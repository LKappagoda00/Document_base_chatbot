#!/usr/bin/env python3
"""
Simple startup script to run the SaaS LLM backend server
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set working directory
os.chdir(current_dir)

if __name__ == "__main__":
    try:
        import uvicorn
        print("Starting SaaS LLM Backend Server...")
        print(f"Working directory: {os.getcwd()}")
        
        # Import main app
        from main import app
        
        # Run the server
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=True
        )
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)