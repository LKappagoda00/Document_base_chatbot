"""
SaaS LLM Application Backend - Simple Test
"""

from fastapi import FastAPI

# Create FastAPI app
app = FastAPI(
    title="SaaS LLM Backend",
    description="Test backend",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Hello from SaaS LLM Backend"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)