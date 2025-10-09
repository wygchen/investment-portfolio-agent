#!/usr/bin/env python3
"""
FastAPI Backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any
import uvicorn
import logging
from datetime import datetime
    
# Import our profile processor functions
from backend.profile_processor import generate_user_profile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Investment Portfolio Advisor API",
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

# No initialization needed - using standalone functions

class FrontendAssessmentData(BaseModel):
    """Model for frontend assessment data"""
    goals: List[Dict[str, Any]] = []
    timeHorizon: int = 10
    riskTolerance: str = ""
    annualIncome: float = 0
    monthlySavings: float = 0
    totalDebt: float = 0
    emergencyFundMonths: str = ""
    values: Dict[str, Any] = {}
    esgPrioritization: bool = False
    marketSelection: List[str] = []


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Investment Profile Processor API",
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
    
    This is the main endpoint for the profile processor.
    It takes the frontend assessment data and outputs structured JSON
    that other agents can consume.
    """
    try:
        logger.info("Processing assessment data...")
        
        # Convert Pydantic model to dict for processing
        frontend_data = assessment_data.model_dump()
        
        # Use profile processor function to generate user profile
        result = generate_user_profile(frontend_data)
        
        logger.info(f"User profile generated: {result['profile_data']['profile_id']}")
        
        return {
            "status": "success",
            "message": "Assessment processed successfully",
            "user_profile": result["profile_data"],
            "profile_id": result["profile_data"]["profile_id"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing assessment: {str(e)}")


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
    Get the most recent investment report - Currently not available without data sharing
    """
    return {
        "status": "error",
        "message": "Report retrieval not available without data sharing system",
        "suggestion": "Use /api/generate-report endpoint to generate a new report"
    }


async def generate_fallback_report():
    """
    Generate a basic report when Communication Agent is unavailable
    """
    try:
        # Create basic report structure without requiring profile data
        report = {
            "report_title": "Investment Portfolio Analysis & Recommendations",
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "client_id": "demo_profile",
            
            "executive_summary": """Based on standard investment principles, 
            we have constructed a diversified portfolio designed for long-term investment growth. 
            The portfolio balances growth potential with risk management to help achieve typical financial objectives.""",
            
            "allocation_rationale": """The asset allocation reflects a balanced risk profile 
            and long-term investment horizon. The portfolio emphasizes diversification across asset classes, 
            regions, and sectors to optimize risk-adjusted returns.""",
            
            "selection_rationale": """Investment selections focus on high-quality assets with strong fundamentals. 
            The portfolio includes a mix of growth and value opportunities across developed and emerging markets.""",
            
            "risk_commentary": """The portfolio maintains an appropriate risk level through diversification. 
            Regular rebalancing helps manage downside risk while positioning for long-term growth. 
            Regular monitoring ensures the portfolio remains aligned with evolving market conditions.""",
            
            "key_recommendations": [
                "Maintain diversified portfolio allocation",
                "Review portfolio performance quarterly", 
                "Adjust risk exposure based on market conditions",
                "Consider tax-efficient investment strategies"
            ],
            
            "next_steps": [
                "Monitor portfolio performance against benchmarks",
                "Schedule quarterly review meetings",
                "Update investment strategies based on market changes"
            ],
            
            "report_metadata": {
                "generated_by": "PortfolioAI Communication Agent (Fallback Mode)",
                "report_type": "Basic Investment Report",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return {"status": "success", "report": report}
        
    except Exception as e:
        logger.error(f"Error generating fallback report: {e}")
        return {"error": f"Fallback report generation failed: {str(e)}"}


async def generate_fallback_answer(question: str) -> str:
    """
    Generate basic answers when Communication Agent is unavailable
    """
    try:
        # Simple keyword-based responses without requiring profile data
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["allocation", "why", "chosen"]):
            return """The portfolio allocation is designed based on modern portfolio theory principles. 
            We balance growth potential with risk management by diversifying across different asset classes and regions. 
            This approach helps optimize returns while managing downside risk according to standard investment practices."""
        
        elif any(word in question_lower for word in ["risk", "risky", "safe"]):
            return """Portfolio risk levels are managed through diversification across asset classes, 
            geographic regions, and sectors. We use modern risk management techniques and regular rebalancing 
            to maintain appropriate risk exposure over time."""
        
        elif any(word in question_lower for word in ["selection", "stocks", "investments", "picked"]):
            return """Investment selections are based on fundamental analysis, quality metrics, and diversification principles. 
            We focus on high-quality assets with strong growth potential and sustainable competitive advantages. 
            The selection process considers multiple factors including market conditions and sector allocation."""
        
        elif any(word in question_lower for word in ["review", "rebalance", "when"]):
            return """We recommend reviewing portfolios quarterly and rebalancing when allocations drift significantly 
            from targets (typically 5-10% deviation). Market conditions and major economic changes may also trigger reviews. 
            Regular monitoring ensures portfolios stay aligned with investment objectives."""
        
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
