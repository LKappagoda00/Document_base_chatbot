"""
SaaS LLM Application Backend
A FastAPI application for document upload, processing, and RAG-based Q&A using local or remote LLMs.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from routes import files, query, auth
from config.settings import settings
from models.mongodb import mongodb
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="SaaS LLM Backend",
    description="A scalable backend for document processing and RAG-based Q&A",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,  # Disable docs in production
    redoc_url="/redoc" if settings.is_development else None
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security middleware (optional, for production)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(files.router, prefix="/files", tags=["documents"])
app.include_router(query.router, prefix="/query", tags=["questions"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        await mongodb.init_database()
        print("MongoDB initialized successfully")
    except Exception as e:
        print(f"Failed to initialize MongoDB: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    try:
        await mongodb.close()
        print("MongoDB connection closed")
    except Exception as e:
        print(f"Error closing MongoDB connection: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "llm_api_url": settings.llm_api_url,
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "SaaS LLM Backend API",
        "version": "1.0.0",
        "docs": "/docs" if settings.is_development else "disabled",
        "health": "/health"
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development
    )
