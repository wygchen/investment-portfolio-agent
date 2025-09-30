#!/usr/bin/env python3
"""
PortfolioAI FastAPI Server Startup Script
Starts the FastAPI server with environment-based configuration
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def start_server():
    """Start the FastAPI server with configuration from environment variables"""
    
    # Server configuration from environment variables
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"🚀 Starting PortfolioAI API server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"📝 Log Level: {log_level}")
    print(f"🌐 Frontend URL: http://localhost:3000")
    print(f"📊 API Docs: http://{host}:{port}/docs")
    print(f"💡 ReDoc: http://{host}:{port}/redoc")
    print("-" * 50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    start_server()