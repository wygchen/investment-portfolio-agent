#!/usr/bin/env python3
"""
Simple FastAPI Backend for Discovery Agent

This is a minimal API that uses the discovery agent to process user assessment data
and outputs raw JSON for other agents to consume.
"""

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Dict, List, Any, Optional
    import uvicorn
    import logging
    from datetime import datetime
    print("✅ FastAPI imported successfully")
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Installing dependencies...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "fastapi", "uvicorn", "python-dotenv", "pydantic"])
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Dict, List, Any, Optional
    import uvicorn
    import logging
    from datetime import datetime

# Import our discovery agent and data sharing components
from discovery_agent import DiscoveryAgent, UserProfileJSON
from data_sharing import DataSharingManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Investment Discovery Agent API",
    description="API for processing user assessment data and generating User Profile JSON",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
discovery_agent = DiscoveryAgent()
data_manager = DataSharingManager()


class FrontendAssessmentData(BaseModel):
    """Model for frontend assessment data"""
    goals: List[Dict[str, Any]] = []
    timeHorizon: int = 10
    milestones: List[Dict[str, Any]] = []
    riskTolerance: str = ""
    experienceLevel: str = ""
    annualIncome: float = 0
    monthlySavings: float = 0
    totalDebt: float = 0
    dependents: int = 0
    emergencyFundMonths: str = ""
    values: Dict[str, Any] = {}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Investment Discovery Agent API",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend server is running"}


@app.post("/api/process-assessment")
async def process_assessment(assessment_data: FrontendAssessmentData):
    """
    Process user assessment data and generate User Profile JSON
    
    This is the main endpoint for the discovery agent.
    It takes the frontend assessment data and outputs structured JSON
    that other agents can consume.
    """
    try:
        logger.info("Processing assessment data...")
        
        # Convert Pydantic model to dict for processing
        frontend_data = assessment_data.dict()
        
        # Use discovery agent to generate user profile
        result = discovery_agent.generate_user_profile(frontend_data)
        
        logger.info(f"User profile generated: {result['profile_data']['profile_id']}")
        
        return {
            "status": "success",
            "message": "Assessment processed successfully",
            "user_profile": result["profile_data"],
            "profile_id": result["profile_data"]["profile_id"],
            "file_path": result["file_path"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing assessment: {str(e)}")


@app.post("/api/profile")
async def save_profile(profile: dict):
    """Legacy endpoint - redirects to new discovery agent processing"""
    try:
        # Convert old format to new format if needed
        assessment_data = FrontendAssessmentData(**profile)
        return await process_assessment(assessment_data)
    except Exception as e:
        logger.error(f"Error in legacy profile endpoint: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/profile/latest")
async def get_latest_profile():
    """
    Get the latest user profile JSON
    
    This endpoint allows other agents/teammates to retrieve
    the most recent user profile data.
    """
    try:
        profile = data_manager.get_latest_profile()
        
        if not profile:
            raise HTTPException(status_code=404, detail="No profile data found")
        
        return {
            "status": "success",
            "profile": profile,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")


@app.get("/api/profiles/list")
async def list_profiles():
    """
    List all available profile IDs
    
    Useful for teammates to see what profile data is available.
    """
    try:
        profiles = data_manager.list_all_profiles()
        
        return {
            "status": "success",
            "profiles": profiles,
            "count": len(profiles),
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing profiles: {str(e)}")

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
