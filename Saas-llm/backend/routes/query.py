"""
Query routes for RAG-based question answering.
Handles user questions, context retrieval, and LLM interaction.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from services.embeddings import embedding_service
from services.vector_store import vector_store_service
from services.llm import llm_service
from routes.auth import get_current_user

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None  # Optionally filter by specific documents
    max_chunks: Optional[int] = 5  # Number of relevant chunks to retrieve
    temperature: Optional[float] = 0.7  # LLM temperature


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    question: str
    model_info: dict
    processing_time_ms: int


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    req: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ask a question and get an answer using RAG (Retrieval-Augmented Generation).
    """
    import time
    start_time = time.time()
    
    try:
        # Generate embedding for the question
        question_embedding = embedding_service.embed_text(req.question)
        
        # Retrieve relevant chunks from vector store
        search_results = vector_store_service.query_similar_chunks(
            query_embedding=question_embedding,
            top_k=req.max_chunks or 5,
            user_id=current_user["id"],
            document_ids=req.document_ids
        )
        
        if not search_results["chunks"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant documents found. Please upload some documents first."
            )
        
        # Prepare context from retrieved chunks
        context_chunks = []
        sources = []
        
        for chunk in search_results["chunks"]:
            context_chunks.append(chunk["text"])
            sources.append({
                "chunk_id": chunk["id"],
                "document_id": chunk["metadata"]["document_id"],
                "similarity_score": chunk["similarity_score"],
                "snippet": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            })
        
        context = "\n\n".join(context_chunks)
        
        # Query the LLM with context
        llm_response = await llm_service.query_llm(
            prompt=req.question,
            context=context,
            temperature=req.temperature or 0.7
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return QueryResponse(
            answer=llm_response["response"],
            sources=sources,
            question=req.question,
            model_info={
                "llm_model": llm_response.get("model", "unknown"),
                "embedding_model": embedding_service.model_name,
                "chunks_used": len(context_chunks),
                "total_context_length": len(context)
            },
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@router.get("/health")
async def query_health_check(current_user: dict = Depends(get_current_user)):
    """Check if all query services are working properly."""
    try:
        # Test embedding service
        test_embedding = embedding_service.embed_text("test")
        embedding_working = len(test_embedding) > 0
        
        # Test LLM service
        llm_status = await llm_service.check_model_availability()
        
        # Test vector store
        vector_stats = vector_store_service.get_collection_stats()
        
        return {
            "embedding_service": {
                "working": embedding_working,
                "model": embedding_service.model_name,
                "dimension": len(test_embedding)
            },
            "llm_service": llm_status,
            "vector_store": vector_stats,
            "user_documents": len(vector_store_service.get_user_documents(current_user["id"]))
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.post("/search")
async def search_documents(
    req: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Search documents without generating an LLM response.
    Useful for finding relevant documents or chunks.
    """
    try:
        # Generate embedding for the search query
        query_embedding = embedding_service.embed_text(req.question)
        
        # Search vector store
        search_results = vector_store_service.query_similar_chunks(
            query_embedding=query_embedding,
            top_k=req.max_chunks or 10,
            user_id=current_user["id"],
            document_ids=req.document_ids
        )
        
        # Format results
        formatted_results = []
        for chunk in search_results["chunks"]:
            formatted_results.append({
                "chunk_id": chunk["id"],
                "document_id": chunk["metadata"]["document_id"],
                "similarity_score": chunk["similarity_score"],
                "text_snippet": chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
                "chunk_index": chunk["metadata"]["chunk_index"]
            })
        
        return {
            "query": req.question,
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
