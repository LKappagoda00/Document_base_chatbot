"""
Embeddings service for generating text embeddings using sentence-transformers.
Supports chunking strategies and batch processing for efficient embedding generation.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np
from config.settings import settings


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        # Load embedding model (cached after first load)
        self.model_name = settings.embedding_model
        self.embedding_model = SentenceTransformer(self.model_name)
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batch processing)."""
        embeddings = self.embedding_model.encode(texts)
        return [emb.tolist() for emb in embeddings]
    
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = None, 
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Input text to chunk
            chunk_size: Size of each chunk (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
        
        Returns:
            List of chunks with metadata
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        # Simple character-based chunking
        # TODO: Implement smarter chunking (sentence-based, paragraph-based)
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to break at word boundaries
            if end < len(text) and not text[end].isspace():
                # Find the last space within the chunk
                last_space = chunk_text.rfind(' ')
                if last_space > chunk_size * 0.8:  # Only if we don't lose too much
                    end = start + last_space
                    chunk_text = text[start:end]
            
            chunks.append({
                "text": chunk_text.strip(),
                "chunk_index": chunk_index,
                "start_char": start,
                "end_char": end,
                "length": len(chunk_text.strip())
            })
            
            chunk_index += 1
            start = end - chunk_overlap
            
            # Prevent infinite loop
            if start >= end:
                start = end
        
        return chunks
    
    def process_document_for_embeddings(
        self, 
        text: str, 
        document_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Process a document: chunk text and generate embeddings.
        
        Args:
            text: Document text
            document_id: Optional document identifier
        
        Returns:
            List of chunks with embeddings and metadata
        """
        # Split into chunks
        chunks = self.chunk_text(text)
        
        # Extract text for embedding
        chunk_texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings for all chunks
        embeddings = self.embed_texts(chunk_texts)
        
        # Combine chunks with embeddings
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                **chunk,
                "embedding": embeddings[i],
                "document_id": document_id,
                "embedding_model": self.model_name
            })
        
        return processed_chunks
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_model.get_sentence_embedding_dimension(),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }


# Global embedding service instance
embedding_service = EmbeddingService()


# Backward compatibility function
def embed_text(text: str) -> List[float]:
    """Backward compatible function for embedding text."""
    return embedding_service.embed_text(text)
