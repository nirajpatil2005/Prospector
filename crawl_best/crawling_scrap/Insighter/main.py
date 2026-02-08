#!/usr/bin/env python3
"""
Main script to run the FastAPI backend
"""
import os
import sys
import uvicorn

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )