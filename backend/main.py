#!/usr/bin/env python3
"""
FastAPI Backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import logging
import json
import asyncio
from datetime import datetime
    
# Import our profile processor functions
from backend.profile_processor import generate_user_profile
# Import main agent for workflow execution
from backend.main_agent import MainAgent

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

@app.post("/api/validate-assessment")
async def validate_assessment(assessment_data: FrontendAssessmentData):
    """
    Quick validation of frontend assessment data
    
    This endpoint only validates the assessment data for correctness.
    Returns validation results without generating profile or running workflow.
    """
    try:
        logger.info("Validating assessment data...")
        
        # Convert and validate data
        frontend_data = assessment_data.model_dump()
        
        # Validation checks
        validation_errors = []
        
        if not frontend_data.get("riskTolerance"):
            validation_errors.append("Risk tolerance is required")
        
        if frontend_data.get("annualIncome", 0) <= 0:
            validation_errors.append("Annual income must be greater than 0")
            
        if frontend_data.get("monthlySavings", 0) < 0:
            validation_errors.append("Monthly savings cannot be negative")
            
        if frontend_data.get("totalDebt", 0) < 0:
            validation_errors.append("Total debt cannot be negative")
            
        if frontend_data.get("timeHorizon", 0) <= 0:
            validation_errors.append("Time horizon must be greater than 0")
            
        # Check if goals are provided
        goals = frontend_data.get("goals", [])
        if not goals or len(goals) == 0:
            validation_errors.append("At least one financial goal is required")
            
        if validation_errors:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Validation failed",
                    "errors": validation_errors
                }
            )
            
        logger.info("Assessment data validated successfully")
        return {
            "status": "success", 
            "message": "Assessment data is valid and ready for processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating assessment: {str(e)}")

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


@app.post("/api/generate-report/stream")
async def generate_report_stream(assessment_data: FrontendAssessmentData):
    """
    Generate investment report with real-time streaming updates
    
    This endpoint processes assessment data, generates user profile,
    runs the complete main agent workflow, and streams progress updates.
    """
    
    async def generate_stream():
        try:
            # Step 1: Profile Generation
            yield create_sse_event("profile_generation_started", {
                "progress": 10,
                "message": "Generating user profile..."
            })
            
            frontend_data = assessment_data.model_dump()
            
            # Generate user profile
            profile_result = generate_user_profile(frontend_data)
            user_profile = profile_result["profile_data"]
            
            yield create_sse_event("profile_generated", {
                "progress": 20,
                "profile_id": user_profile["profile_id"],
                "message": "User profile generated successfully"
            })
            
            # Step 2: Stream MainAgent Workflow
            async for event in stream_main_agent_workflow(user_profile):
                yield event
                
        except Exception as e:
            logger.error(f"Stream generation error: {str(e)}")
            yield create_sse_event("error", {
                "message": str(e),
                "type": "server_error"
            })
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.post("/api/generate-report-from-profile")
async def generate_report_from_profile_id(request_data: Dict[str, Any]):
    """
    Generate investment report from an existing user profile
    
    Accepts profile data and generates a comprehensive investment report 
    using the main agent workflow.
    """
    try:
        profile_data = request_data.get("profile_data")
        
        if not profile_data:
            raise HTTPException(
                status_code=400, 
                detail="profile_data is required"
            )
        
        # Convert dict to UserProfile object for main agent
        from backend.profile_processor import UserProfile
        user_profile_obj = UserProfile(
            goals=profile_data.get("goals", []),
            time_horizon=profile_data.get("time_horizon", 10),
            risk_tolerance=profile_data.get("risk_tolerance", "medium"),
            income=profile_data.get("income", 0.0),
            savings_rate=profile_data.get("savings_rate", 0.0),
            liabilities=profile_data.get("liabilities", 0.0),
            liquidity_needs=profile_data.get("liquidity_needs", "medium"),
            personal_values=profile_data.get("personal_values", {}),
            esg_prioritization=profile_data.get("esg_prioritization", False),
            market_selection=profile_data.get("market_selection", ["US"]),
            timestamp=profile_data.get("timestamp", datetime.now().isoformat()),
            profile_id=profile_data.get("profile_id", f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        )
        
        # Run main agent workflow
        agent_result = await run_main_agent_safely(user_profile_obj)
        
        if agent_result["success"]:
            workflow_result = agent_result["result"]
            final_report = workflow_result["results"].get("final_report", {})
            
            return {
                "status": "success",
                "report": final_report,
                "execution_time": workflow_result.get("execution_time", 0)
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Workflow failed: {agent_result['error']}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report from profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


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


def create_sse_event(event_type: str, data: dict) -> str:
    """
    Create a Server-Sent Event formatted string
    """
    event_data = {
        "event": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    return f"data: {json.dumps(event_data)}\n\n"


def create_user_profile_object(user_profile: dict):
    """
    Convert profile dict to UserProfile object for main agent
    """
    from backend.profile_processor import UserProfile
    
    return UserProfile(
        goals=user_profile.get("goals", []),
        time_horizon=user_profile.get("time_horizon", 10),
        risk_tolerance=user_profile.get("risk_tolerance", "medium"),
        income=user_profile.get("income", 0.0),
        savings_rate=user_profile.get("savings_rate", 0.0),
        liabilities=user_profile.get("liabilities", 0.0),
        liquidity_needs=user_profile.get("liquidity_needs", "medium"),
        personal_values=user_profile.get("personal_values", {}),
        esg_prioritization=user_profile.get("esg_prioritization", False),
        market_selection=user_profile.get("market_selection", ["US"]),
        timestamp=user_profile.get("timestamp", datetime.now().isoformat()),
        profile_id=user_profile.get("profile_id", f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    )


async def stream_main_agent_workflow(user_profile):
    """
    Stream the complete MainAgent workflow with real-time updates
    """
    try:
        # Convert to UserProfile object
        user_profile_obj = create_user_profile_object(user_profile)
        
        # Initialize MainAgent with streaming
        main_agent = MainAgent()
        workflow = main_agent.create_workflow()
        
        # Initialize state for streaming
        initial_state = {
            "user_profile": user_profile_obj,
            "risk_analysis_state": None,
            "portfolio_construction_state": None,
            "selection_state": None,
            "communication_state": None,
            "start_time": 0.0,
            "execution_time": 0.0,
            "current_node": "",
            "risk_blueprint": None,
            "portfolio_allocation": None,
            "security_selections": None,
            "final_report": None,
            "success": True,
            "error": None,
            "node_errors": {},
            "config": main_agent.config
        }
        
        # Stream the workflow execution
        current_progress = 20
        
        # Since LangGraph astream might not be available in current version,
        # we'll simulate streaming by running workflow and emitting events
        
        # Risk Analysis
        current_progress = 30
        yield create_sse_event("risk_analysis_started", {
            "progress": current_progress,
            "message": "Analyzing risk profile and generating risk blueprint..."
        })
        
        try:
            # Run the complete workflow (we'll enhance this later for true streaming)
            agent_result = await run_main_agent_safely(user_profile_obj)
            
            if agent_result["success"]:
                workflow_result = agent_result["result"]
                
                # Risk Analysis Complete
                current_progress = 50
                yield create_sse_event("risk_analysis_complete", {
                    "progress": current_progress,
                    "message": "Risk analysis completed successfully",
                    "risk_blueprint": workflow_result.get("results", {}).get("risk_blueprint", {})
                })
                
                # Portfolio Construction
                current_progress = 60
                yield create_sse_event("portfolio_construction_started", {
                    "progress": current_progress,
                    "message": "Optimizing portfolio allocation..."
                })
                
                current_progress = 75
                yield create_sse_event("portfolio_construction_complete", {
                    "progress": current_progress,
                    "message": "Portfolio optimization completed",
                    "portfolio_allocation": workflow_result.get("results", {}).get("portfolio_allocation", {})
                })
                
                # Selection
                current_progress = 80
                yield create_sse_event("selection_started", {
                    "progress": current_progress,
                    "message": "Selecting specific securities..."
                })
                
                current_progress = 90
                yield create_sse_event("selection_complete", {
                    "progress": current_progress,
                    "message": "Security selection completed",
                    "security_selections": workflow_result.get("results", {}).get("security_selections", {})
                })
                
                # Communication
                current_progress = 95
                yield create_sse_event("communication_started", {
                    "progress": current_progress,
                    "message": "Generating final investment report..."
                })
                
                current_progress = 100
                yield create_sse_event("final_report_complete", {
                    "progress": current_progress,
                    "message": "Investment report generated successfully!",
                    "final_report": workflow_result.get("results", {}).get("final_report", {}),
                    "execution_time": workflow_result.get("execution_time", 0),
                    "status": "complete"
                })
                
            else:
                # Workflow failed, provide fallback
                yield create_sse_event("workflow_error", {
                    "progress": 50,
                    "message": f"Workflow error: {agent_result['error']}",
                    "type": "workflow_error"
                })
                
                # Generate fallback report
                yield create_sse_event("communication_started", {
                    "progress": 95,
                    "message": "Generating fallback report..."
                })
                
                fallback_report = await generate_fallback_report()
                yield create_sse_event("final_report_complete", {
                    "progress": 100,
                    "message": "Fallback report generated",
                    "final_report": fallback_report.get("report", {}),
                    "status": "completed_with_fallback"
                })
                
        except Exception as workflow_error:
            logger.error(f"Workflow execution error: {str(workflow_error)}")
            yield create_sse_event("workflow_error", {
                "progress": 50,
                "message": str(workflow_error),
                "type": "workflow_execution_error"
            })
            
            # Always provide fallback report
            fallback_report = await generate_fallback_report()
            yield create_sse_event("final_report_complete", {
                "progress": 100,
                "message": "Fallback report generated due to workflow error",
                "final_report": fallback_report.get("report", {}),
                "status": "completed_with_fallback"
            })
        
    except Exception as e:
        logger.error(f"Stream workflow error: {str(e)}")
        yield create_sse_event("error", {
            "message": str(e),
            "type": "stream_error"
        })


async def run_main_agent_safely(user_profile_obj) -> Dict[str, Any]:
    """
    Safely run the main agent workflow with proper error handling
    
    Args:
        user_profile_obj: UserProfile object
        
    Returns:
        Dictionary with workflow results or error information
    """
    try:
        # Initialize and run main agent
        main_agent = MainAgent()
        workflow_result = main_agent.run_complete_workflow(user_profile_obj)
        
        return {
            "success": workflow_result.get("status") == "success",
            "result": workflow_result,
            "error": None if workflow_result.get("status") == "success" else workflow_result.get("error")
        }
        
    except ImportError as e:
        logger.error(f"Main agent dependencies missing: {str(e)}")
        return {
            "success": False,
            "result": None,
            "error": f"Main agent dependencies missing: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Main agent execution failed: {str(e)}")
        return {
            "success": False,
            "result": None,
            "error": f"Main agent execution failed: {str(e)}"
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
