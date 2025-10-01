"""
File upload and management routes for PDF documents.
Handles file upload, text extraction, chunking, and embedding generation.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List
import fitz  # PyMuPDF
import os
import uuid
from datetime import datetime

from services.embeddings import embedding_service
from services.vector_store import vector_store_service
from models.database import Document
from routes.auth import get_current_user
from config.settings import settings

router = APIRouter()


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a PDF file, extract text, generate embeddings, and store in vector DB.
    """
    # Validate file type
    if file.content_type not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {settings.allowed_file_types}"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(settings.upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Extract text from PDF
        text = ""
        pdf = fitz.open(file_path)
        for page in pdf:
            text += page.get_text()
        pdf.close()
        
        if not text.strip():
            os.remove(file_path)  # Clean up
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text could be extracted from the PDF"
            )
        
        # Create document record in database
        doc_model = Document()
        doc_id = doc_model.create_document(
            user_id=current_user["id"],
            filename=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            content_preview=text[:500]  # First 500 characters as preview
        )
        
        # Process document for embeddings
        processed_chunks = embedding_service.process_document_for_embeddings(
            text=text,
            document_id=str(doc_id)
        )
        
        # Store chunks in database
        for chunk in processed_chunks:
            doc_model.add_document_chunk(
                doc_id=doc_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["text"]
            )
        
        # Store in vector database
        chunk_ids = vector_store_service.add_document_chunks(
            doc_id=str(doc_id),
            chunks=processed_chunks,
            user_id=current_user["id"]
        )
        
        # Update document status
        doc_model.update_document_status(doc_id, "completed")
        
        return {
            "message": "File uploaded and processed successfully",
            "document_id": doc_id,
            "filename": file.filename,
            "file_size": len(file_content),
            "chunks_created": len(processed_chunks),
            "text_length": len(text),
            "content_preview": text[:200] + "..." if len(text) > 200 else text
        }
        
    except Exception as e:
        # Clean up file if processing failed
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )


@router.get("/documents")
async def get_user_documents(current_user: dict = Depends(get_current_user)):
    """Get all documents uploaded by the current user."""
    try:
        doc_model = Document()
        documents = doc_model.get_user_documents(current_user["id"])
        
        return {
            "documents": documents,
            "total_count": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document and its associated data."""
    try:
        doc_model = Document()
        
        # Check if document exists and belongs to user
        document = doc_model.get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if document["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this document"
            )
        
        # Delete from vector store
        await vector_store_service.delete_document(str(document_id), current_user["id"])
        
        # Delete physical file if it exists
        if document.get("file_path") and os.path.exists(document["file_path"]):
            try:
                os.remove(document["file_path"])
            except OSError:
                pass  # File might already be deleted
        
        # Delete from database
        doc_model.delete_document(document_id)
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )