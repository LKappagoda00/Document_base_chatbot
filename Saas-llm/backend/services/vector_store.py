"""
Vector Store service using ChromaDB for storing and retrieving document embeddings.
Supports multi-tenant architecture with user isolation and easy migration to cloud vector DBs.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json
from config.settings import settings


class VectorStoreService:
    """Service for managing document embeddings in ChromaDB."""
    
    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.Client(
            Settings(
                persist_directory=settings.chroma_db_path,
                anonymized_telemetry=False
            )
        )
        
        # Create or get the main collection
        # In production, you might want separate collections per user/tenant
        self.collection = self.client.get_or_create_collection(
            name="document_chunks",
            metadata={"description": "PDF document chunks with embeddings"}
        )
    
    def add_document_chunks(
        self, 
        doc_id: str, 
        chunks: List[Dict[str, Any]], 
        user_id: int = None
    ) -> List[str]:
        """
        Add document chunks with embeddings to the vector store.
        
        Args:
            doc_id: Document identifier
            chunks: List of chunks with embeddings and metadata
            user_id: User ID for multi-tenant isolation
        
        Returns:
            List of chunk IDs that were added
        """
        documents = []
        embeddings = []
        ids = []
        metadatas = []
        
        for chunk in chunks:
            chunk_id = f"{doc_id}_{chunk['chunk_index']}"
            
            documents.append(chunk['text'])
            embeddings.append(chunk['embedding'])
            ids.append(chunk_id)
            
            # Metadata for filtering and source attribution
            metadata = {
                "document_id": doc_id,
                "chunk_index": chunk['chunk_index'],
                "start_char": chunk['start_char'],
                "end_char": chunk['end_char'],
                "length": chunk['length'],
                "embedding_model": chunk.get('embedding_model', 'unknown')
            }
            
            # Add user_id for multi-tenant filtering
            if user_id:
                metadata["user_id"] = user_id
            
            metadatas.append(metadata)
        
        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        return ids
    
    def query_similar_chunks(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        user_id: int = None,
        document_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Query for similar chunks based on embedding similarity.
        
        Args:
            query_embedding: Query text embedding
            top_k: Number of similar chunks to return
            user_id: Filter by user ID for multi-tenant isolation
            document_ids: Filter by specific document IDs
        
        Returns:
            Dictionary with similar chunks and metadata
        """
        # Build where clause for filtering
        where_clause = {}
        
        if user_id:
            where_clause["user_id"] = user_id
        
        if document_ids:
            where_clause["document_id"] = {"$in": document_ids}
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = {
            "chunks": [],
            "total_results": len(results["ids"][0]) if results["ids"] else 0
        }
        
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                chunk_data = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "distance": results["distances"][0][i]
                }
                formatted_results["chunks"].append(chunk_data)
        
        return formatted_results
    
    def delete_document_chunks(self, doc_id: str, user_id: int = None) -> bool:
        """
        Delete all chunks for a specific document.
        
        Args:
            doc_id: Document identifier
            user_id: User ID for additional security
        
        Returns:
            True if deletion was successful
        """
        try:
            where_clause = {"document_id": doc_id}
            if user_id:
                where_clause["user_id"] = user_id
            
            # Get all chunk IDs for this document
            results = self.collection.get(
                where=where_clause,
                include=["ids"]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
            
            return True
        except Exception as e:
            print(f"Error deleting document chunks: {e}")
            return False
    
    async def delete_document(self, doc_id: str, user_id: int = None) -> bool:
        """
        Async alias for delete_document_chunks to match API expectations.
        
        Args:
            doc_id: Document identifier
            user_id: User ID for additional security
        
        Returns:
            True if deletion was successful
        """
        return self.delete_document_chunks(doc_id, user_id)
    
    def get_user_documents(self, user_id: int) -> List[Dict[str, Any]]:
        """Get summary of all documents for a user."""
        try:
            results = self.collection.get(
                where={"user_id": user_id},
                include=["metadatas"]
            )
            
            # Group by document_id
            doc_summary = {}
            for metadata in results["metadatas"]:
                doc_id = metadata["document_id"]
                if doc_id not in doc_summary:
                    doc_summary[doc_id] = {
                        "document_id": doc_id,
                        "chunk_count": 0,
                        "embedding_model": metadata.get("embedding_model", "unknown")
                    }
                doc_summary[doc_id]["chunk_count"] += 1
            
            return list(doc_summary.values())
        except Exception as e:
            print(f"Error getting user documents: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        try:
            collection_data = self.collection.get(include=["metadatas"])
            total_chunks = len(collection_data["metadatas"])
            
            # Count unique documents and users
            unique_docs = set()
            unique_users = set()
            
            for metadata in collection_data["metadatas"]:
                unique_docs.add(metadata["document_id"])
                if "user_id" in metadata:
                    unique_users.add(metadata["user_id"])
            
            return {
                "total_chunks": total_chunks,
                "unique_documents": len(unique_docs),
                "unique_users": len(unique_users),
                "collection_name": self.collection.name
            }
        except Exception as e:
            return {"error": str(e)}


# Global vector store service instance
vector_store_service = VectorStoreService()


# Backward compatibility functions
def add_document(doc_id: str, chunks: List[str], embeddings: List[List[float]], user_id: int = None):
    """Backward compatible function for adding documents."""
    chunk_data = []
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_data.append({
            "text": chunk_text,
            "embedding": embedding,
            "chunk_index": i,
            "start_char": i * 500,  # Approximate
            "end_char": (i + 1) * 500,
            "length": len(chunk_text)
        })
    
    return vector_store_service.add_document_chunks(doc_id, chunk_data, user_id)


def query_similar(text_embedding: List[float], top_k: int = 3, user_id: int = None):
    """Backward compatible function for querying similar chunks."""
    results = vector_store_service.query_similar_chunks(text_embedding, top_k, user_id)
    
    # Convert to old format for backward compatibility
    return {
        "documents": [[chunk["text"] for chunk in results["chunks"]]],
        "metadatas": [[chunk["metadata"] for chunk in results["chunks"]]],
        "distances": [[chunk["distance"] for chunk in results["chunks"]]]
    }
