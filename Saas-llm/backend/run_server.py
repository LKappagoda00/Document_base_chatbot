#!/usr/bin/env python3
"""
Alternative simple server runner for the SaaS LLM backend
"""

import sys
import os
import subprocess

# Set up the environment
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

# Add current directory to Python path
sys.path.insert(0, current_dir)

print(f"Starting server from: {current_dir}")
print(f"Python executable: {sys.executable}")

# Use subprocess to run uvicorn with proper module path
try:
    cmd = [
        sys.executable, 
        "-m", "uvicorn", 
        "main:app", 
        "--reload", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=current_dir)
    
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Error starting server: {e}")
    print("\nTrying alternative method...")
    
    # Alternative: direct import and run
    try:
        import uvicorn
        from main import app
        
        print("Starting server with direct import...")
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
        
    except Exception as e2:
        print(f"Alternative method also failed: {e2}")
        print("Please check your Python environment and dependencies.")