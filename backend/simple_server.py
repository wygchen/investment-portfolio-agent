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


@app.post("/api/generate-report")
async def generate_investment_report():
    """
    Generate professional investment report using Communication Agent
    
    This endpoint generates a comprehensive investment report with rationales
    and explanations for portfolio decisions, similar to bank house views.
    """
    try:
        # Import communication agent (with fallback if dependencies missing)
        try:
            from communication_agent import generate_investment_report
            report_result = generate_investment_report()
        except ImportError as e:
            logger.warning(f"Communication agent dependencies missing: {e}")
            # Fallback to simple report generation
            report_result = await generate_fallback_report()
        
        return {
            "status": "success",
            "report": report_result.get("report", {}),
            "generated_at": datetime.now().isoformat(),
            "message": "Investment report generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating investment report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@app.post("/api/ask-question")
async def ask_portfolio_question(question_data: Dict[str, Any]):
    """
    Answer questions about portfolio decisions and rationale
    
    This endpoint allows users to ask specific questions about their portfolio
    and get detailed explanations powered by the Communication Agent.
    """
    try:
        question = question_data.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Import communication agent (with fallback if dependencies missing)
        try:
            from communication_agent import answer_question
            answer = answer_question(question)
        except ImportError as e:
            logger.warning(f"Communication agent dependencies missing: {e}")
            # Fallback to simple Q&A
            answer = await generate_fallback_answer(question)
        
        return {
            "status": "success",
            "question": question,
            "answer": answer,
            "answered_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering portfolio question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@app.get("/api/report/latest")
async def get_latest_report():
    """
    Get the most recent investment report
    
    Retrieves the latest generated investment report from the Communication Agent.
    """
    try:
        report = data_manager.get_agent_output("communication_agent")
        
        if not report:
            raise HTTPException(status_code=404, detail="No report found. Generate a report first.")
        
        return {
            "status": "success",
            "report": report,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving latest report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")


async def generate_fallback_report():
    """
    Generate a basic report when Communication Agent is unavailable
    """
    try:
        profile = data_manager.get_latest_profile()
        portfolio_data = data_manager.get_agent_output("portfolio_construction")
        
        if not profile:
            return {"error": "No user profile data available"}
        
        # Create basic report structure
        report = {
            "report_title": "Investment Portfolio Analysis & Recommendations",
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "client_id": profile.get("profile_id", "Unknown"),
            
            "executive_summary": f"""Based on your investment goals and {profile.get('risk_tolerance', 'medium')} risk tolerance, 
            we have constructed a diversified portfolio designed for your {profile.get('time_horizon', 10)}-year investment horizon. 
            The portfolio balances growth potential with risk management to help achieve your financial objectives.""",
            
            "allocation_rationale": f"""The asset allocation reflects your {profile.get('risk_tolerance', 'medium')} risk profile 
            and {profile.get('time_horizon', 10)}-year time horizon. The portfolio emphasizes diversification across asset classes, 
            regions, and sectors to optimize risk-adjusted returns while aligning with your investment preferences.""",
            
            "selection_rationale": """Investment selections focus on high-quality assets with strong fundamentals. 
            The portfolio includes a mix of growth and value opportunities across developed and emerging markets, 
            with attention to your ESG preferences and sector interests.""",
            
            "risk_commentary": f"""The portfolio maintains an appropriate risk level for your {profile.get('risk_tolerance', 'medium')} 
            risk tolerance. Diversification and regular rebalancing help manage downside risk while positioning for long-term growth. 
            Regular monitoring ensures the portfolio remains aligned with your evolving needs.""",
            
            "key_recommendations": [
                "Maintain diversified portfolio allocation",
                "Review portfolio performance quarterly", 
                "Adjust risk exposure as goals approach",
                "Consider tax-efficient investment strategies"
            ],
            
            "next_steps": [
                "Monitor portfolio performance against benchmarks",
                "Schedule quarterly review meetings",
                "Update investment profile if circumstances change"
            ],
            
            "report_metadata": {
                "generated_by": "PortfolioAI Communication Agent (Fallback Mode)",
                "report_type": "Basic Investment Report",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Save fallback report
        data_manager.save_agent_output("communication_agent", report)
        
        return {"status": "success", "report": report}
        
    except Exception as e:
        logger.error(f"Error generating fallback report: {e}")
        return {"error": f"Fallback report generation failed: {str(e)}"}


async def generate_fallback_answer(question: str) -> str:
    """
    Generate basic answers when Communication Agent is unavailable
    """
    try:
        profile = data_manager.get_latest_profile()
        
        # Simple keyword-based responses
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["allocation", "why", "chosen"]):
            risk_level = profile.get("risk_tolerance", "medium") if profile else "medium"
            return f"""The portfolio allocation is designed based on your {risk_level} risk tolerance and investment timeline. 
            We balanced growth potential with risk management by diversifying across different asset classes and regions. 
            This approach helps optimize returns while managing downside risk according to your investment profile."""
        
        elif any(word in question_lower for word in ["risk", "risky", "safe"]):
            return """The portfolio risk level is calibrated to match your risk tolerance and investment goals. 
            We use diversification across asset classes, geographic regions, and sectors to manage risk. 
            Regular monitoring and rebalancing help maintain appropriate risk exposure over time."""
        
        elif any(word in question_lower for word in ["selection", "stocks", "investments", "picked"]):
            return """Investment selections are based on fundamental analysis, quality metrics, and alignment with your preferences. 
            We focus on high-quality assets with strong growth potential and sustainable competitive advantages. 
            Your ESG preferences and sector interests are also considered in the selection process."""
        
        elif any(word in question_lower for word in ["review", "rebalance", "when"]):
            return """We recommend reviewing your portfolio quarterly and rebalancing when allocations drift significantly 
            from targets (typically 5-10% deviation). Market conditions, life changes, and goal updates may also trigger reviews. 
            Regular monitoring ensures your portfolio stays aligned with your objectives."""
        
        else:
            return """Thank you for your question about the portfolio. For detailed explanations about specific investment 
            decisions, allocation strategies, or risk management approaches, please refer to your investment report or 
            contact your financial advisor for personalized guidance."""
            
    except Exception as e:
        logger.error(f"Error generating fallback answer: {e}")
        return "I'm unable to provide a detailed answer at the moment. Please try again or contact support."


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
