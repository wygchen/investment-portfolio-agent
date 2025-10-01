#!/usr/bin/env python3
"""
Simple FastAPI server for testing
"""

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    print("✅ FastAPI imported successfully")
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Installing dependencies...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "fastapi", "uvicorn", "python-dotenv"])
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn

# Create FastAPI app
app = FastAPI(
    title="PortfolioAI API",
    description="AI-powered investment portfolio management API", 
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "PortfolioAI Backend is running!", "status": "healthy"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend server is running"}

@app.post("/api/profile")
async def save_profile(profile: dict):
    """Save user investment profile"""
    print(f"📝 Received profile: {profile}")
    return {"success": True, "message": "Profile saved successfully"}

@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio recommendations"""
    return {
        "portfolio": {
            "total_value": 487650,
            "change": 23450,
            "change_percent": 5.06,
            "allocations": [
                {"name": "US Equities", "percentage": 35, "value": 170778},
                {"name": "International Equities", "percentage": 25, "value": 121913}, 
                {"name": "Bonds", "percentage": 20, "value": 97530},
                {"name": "REITs", "percentage": 10, "value": 48765},
                {"name": "Commodities", "percentage": 7, "value": 34136},
                {"name": "Crypto", "percentage": 3, "value": 14630}
            ]
        }
    }

if __name__ == "__main__":
    print("🚀 Starting PortfolioAI Backend Server...")
    print("📍 Server will be available at: http://localhost:8003")
    print("🔗 Frontend should connect from: http://localhost:3000")
    
    uvicorn.run(
        app, 
        host="127.0.0.1",
        port=8003,
        log_level="info"
    )