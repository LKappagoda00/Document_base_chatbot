#!/usr/bin/env python3
import uvicorn
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting SaaS LLM Backend Server...")
    print("Server will be available at: http://localhost:8000")
    
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            reload_dirs=["./"]
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        print("Trying alternative startup method...")
        
        # Fallback method
        uvicorn.run(
            app="main:app",
            host="127.0.0.1",
            port=8000,
            reload=False
        )