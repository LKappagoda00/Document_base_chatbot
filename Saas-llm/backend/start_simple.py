"""
Simple FastAPI server without embeddings for testing frontend integration.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from models.mongodb import MongoUser
from config.settings import settings


# Create global MongoDB connection
mongodb_client = None
database = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB connection
    global mongodb_client, database
    try:
        mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
        database = mongodb_client[settings.mongodb_database]
        
        # Test connection
        await mongodb_client.admin.command('ping')
        print(f"✅ Connected to MongoDB at {settings.mongodb_url}")
        print(f"📦 Using database: {settings.mongodb_database}")
        
        print("✅ MongoDB collections initialized")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise e
    
    yield
    
    # Shutdown: Close MongoDB connection
    if mongodb_client:
        mongodb_client.close()
        print("✅ MongoDB connection closed")

# Create FastAPI app
app = FastAPI(
    title="SaaS LLM API (Simple Mode)",
    description="Document-based Q&A API with MongoDB backend - Testing Mode",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple auth routes
from routes.auth import router as auth_router
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "SaaS LLM API is running (Simple Mode)",
        "mongodb_connected": database is not None
    }

# Simple files endpoints
@app.get("/files/documents")
async def get_documents():
    """Get user documents (mock response)."""
    return {
        "documents": [
            {
                "id": "507f1f77bcf86cd799439011",  # Mock MongoDB ObjectId
                "filename": "sample_document.pdf",
                "file_size": 1024000,
                "created_at": "2025-01-01T10:00:00Z",
                "processed_at": "2025-01-01T10:01:00Z",
                "status": "completed",
                "content_preview": "This is a sample document for testing..."
            }
        ],
        "total": 1,
        "message": "Sample data from simple mode"
    }

@app.get("/files/stats")
async def get_upload_stats():
    """Get file upload statistics."""
    return {
        "total_documents": 1,
        "total_size_bytes": 1024000,
        "total_chunks": 10,
        "average_processing_time": 5.2
    }

@app.post("/files/upload")
async def upload_file():
    """Mock file upload endpoint."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="File upload disabled in simple mode. Please enable embeddings service to use this feature."
    )

@app.delete("/files/documents/{document_id}")
async def delete_document(document_id: str):
    """Mock document deletion."""
    return {"message": f"Document {document_id} deletion disabled in simple mode"}

# Simple query endpoints
@app.post("/query/ask")
async def ask_question():
    """Mock query endpoint."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Query operations disabled in simple mode. Please enable embeddings service to use this feature."
    )

@app.post("/query/search")
async def search_documents():
    """Mock search endpoint."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Search operations disabled in simple mode. Please enable embeddings service to use this feature."
    )

@app.get("/query/health")
async def query_health():
    """Query service health check."""
    return {
        "status": "disabled",
        "message": "Query service disabled in simple mode",
        "embedding_model": "not_loaded"
    }

if __name__ == "__main__":
    uvicorn.run(
        "start_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )