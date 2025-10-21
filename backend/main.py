#!/usr/bin/env python3
"""
FastAPI Backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import logging
import json
import asyncio
from datetime import datetime

# Import our profile processor functions
from profile_processor_agent import generate_user_profile
# Import main agent for workflow execution
from main_agent import MainAgent
from market_news_agent.news_insights import get_news_insights_analysis
from market_news_agent.market_sentiment import get_yahoo_news_description

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
    allow_origins=["*"],  # Allow all origins for production deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No initialization needed - using standalone functions

class ValuesData(BaseModel):
    """Model for user values and preferences"""
    avoidIndustries: List[str] = []
    preferIndustries: List[str] = []
    specificAssets: str = ""  # NEW: User-specified assets
    customConstraints: str = ""

class FrontendAssessmentData(BaseModel):
    """Model for frontend assessment data"""
    goals: List[Dict[str, Any]] = []
    timeHorizon: int = 10
    riskTolerance: str = ""
    annualIncome: float = 0
    monthlySavings: float = 0
    totalDebt: float = 0
    emergencyFundMonths: str = ""
    values: ValuesData = ValuesData()  # Updated to use structured model
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

@app.post("/api/process-assessment")
async def process_assessment(assessment_data: FrontendAssessmentData):
    """
    Process assessment data and generate investment report
    
    This endpoint processes the assessment data, generates user profile,
    and returns a complete investment report with portfolio recommendations.
    """
    try:
        logger.info("🚀 Processing assessment data...")
        
        # Convert frontend data to backend format
        frontend_data = assessment_data.model_dump()
        
        # Generate user profile
        logger.info("📊 Generating user profile...")
        profile_result = generate_user_profile(frontend_data)
        
        if not profile_result.get("success"):
            raise HTTPException(
                status_code=400, 
                detail=f"Profile generation failed: {profile_result.get('error', 'Unknown error')}"
            )
        
        user_profile = profile_result["profile"]
        logger.info("✅ User profile generated successfully")
        
        # Run main agent workflow
        logger.info("🤖 Running AI agent workflow...")
        main_agent = MainAgent()
        agent_result = await main_agent.execute_workflow(user_profile)
        
        if not agent_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Agent workflow failed: {agent_result.get('error', 'Unknown error')}"
            )
        
        workflow_result = agent_result["result"]
        final_report = workflow_result["results"].get("final_report", {})
        
        logger.info("✅ Assessment processing complete")
        
        return {
            "status": "success",
            "report": final_report,
            "profile": user_profile,
            "execution_time": workflow_result.get("execution_time", 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing assessment: {str(e)}")

@app.post("/api/get-news")
async def get_news(ticker: str):
    """
    Get news data for a given ticker
    """
    news_data = get_yahoo_news_description(ticker, max_articles=5)
    return {"news": news_data}
    # Example JSON response structure for frontend reference:
    # {
    #   "news": {
    #     "news_list": [
    #       {
    #         "2024-01-15T10:30:00Z": {
    #           "heading": "Company reports strong Q4 earnings",
    #           "source": "Reuters"
    #         }
    #       },
    #       {
    #         "2024-01-15T09:15:00Z": {
    #           "heading": "Analyst upgrades stock to buy rating",
    #           "source": "Bloomberg"
    #         }
    #       }
    #     ],
    #     "hotnews_summary": "Recent news shows positive sentiment with strong earnings and analyst upgrades driving investor confidence."
    #   }
    # }

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
        from profile_processor_agent import UserProfile
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


@app.post("/api/generate-report")
async def generate_investment_report():
    """
    Generate comprehensive investment report using realistic preset data
    
    This endpoint generates a professional investment report with portfolio
    allocation, rationale, and recommendations based on preset user data.
    """
    try:
        # Use realistic preset data that matches our streaming data
        preset_report_data = {
            "report_title": "Investment Portfolio Analysis Report",
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "client_id": "demo_profile_12345",
            "executive_summary": "This comprehensive investment strategy is designed to meet your long-term financial objectives through a carefully balanced portfolio approach. The recommended $125,000 portfolio emphasizes growth potential while maintaining appropriate risk management, targeting a 7.6% annual return aligned with your ESG preferences and moderate risk tolerance.",
            "allocation_rationale": """The portfolio allocation is strategically designed for long-term wealth building with ESG integration:

• Equity Allocation (70%): Provides growth potential through high-quality individual stocks including Microsoft (8%), Google (6%), Apple (5%), and NVIDIA (4%)
• Technology Focus (29%): Leverages digital transformation trends through leading companies
• Fixed Income (30%): Offers stability through bond ETFs and government securities
• ESG Integration: All investments are screened to avoid tobacco and weapons sectors
• Geographic Focus: Primarily US-focused with some international ETF exposure""",
            "selection_rationale": """Individual stock selections focus on industry-leading companies with strong ESG characteristics:

• Microsoft (MSFT): Cloud computing and AI leadership with carbon negative commitments
• Google/Alphabet (GOOGL): Dominant search and cloud platforms with renewable energy focus
• Apple (AAPL): Premium consumer technology with supply chain sustainability initiatives
• NVIDIA (NVDA): AI and semiconductor leadership driving technological transformation
• NextEra Energy (NEE): Largest renewable energy developer in North America
• Tesla (TSLA): Electric vehicle and energy storage innovation leadership

ETF selections provide diversified exposure while maintaining ESG alignment and cost efficiency.""",
            "risk_commentary": """Portfolio risk characteristics are well-managed through diversification and quality selection:

• Volatility Management: 70/30 equity/bond allocation appropriate for moderate risk tolerance
• Concentration Risk: Individual positions limited to 8% maximum allocation
• ESG Risk Mitigation: Exclusion of controversial sectors reduces regulatory risks
• Market Risk: Diversification across technology, energy, and healthcare sectors
• Debt Management: Portfolio considers 33% debt ratio in overall financial planning

Expected annual return of 7.6% with moderate volatility through systematic diversification.""",
            "key_recommendations": [
                "Implement systematic monthly investing of $1,500 to benefit from dollar-cost averaging",
                "Maintain current ESG-focused allocation targeting tobacco/weapons avoidance",
                "Review portfolio performance and rebalance quarterly to maintain target weights",
                "Consider tax-loss harvesting opportunities in taxable accounts",
                "Monitor individual stock positions for concentration risk management"
            ],
            "next_steps": [
                "Set up automatic monthly investment transfers of $1,500",
                "Schedule quarterly portfolio performance review meetings",
                "Ensure 6-month emergency fund is established separate from investments",
                "Review beneficiary designations on all investment accounts",
                "Plan for future contribution increases aligned with income growth"
            ],
            "portfolio_allocation": {
                "Technology Stocks": 29.0,
                "Bonds": 30.0,
                "Renewable Energy": 12.0,
                "International": 17.0,
                "Broad Market ETFs": 8.0,
                "Real Estate": 4.0
            },
            "individual_holdings": [
                {"name": "Microsoft Corporation", "symbol": "MSFT", "allocation_percent": 8.0, "value": 10000},
                {"name": "Alphabet Inc", "symbol": "GOOGL", "allocation_percent": 6.0, "value": 7500},
                {"name": "Apple Inc", "symbol": "AAPL", "allocation_percent": 5.0, "value": 6250},
                {"name": "NVIDIA Corporation", "symbol": "NVDA", "allocation_percent": 4.0, "value": 5000},
                {"name": "Amazon.com Inc", "symbol": "AMZN", "allocation_percent": 3.0, "value": 3750},
                {"name": "Meta Platforms Inc", "symbol": "META", "allocation_percent": 3.0, "value": 3750},
                {"name": "Vanguard Total Bond Market ETF", "symbol": "BND", "allocation_percent": 15.0, "value": 18750},
                {"name": "Vanguard Tax-Exempt Bond ETF", "symbol": "VTEB", "allocation_percent": 8.0, "value": 10000},
                {"name": "iShares TIPS Bond ETF", "symbol": "TIP", "allocation_percent": 7.0, "value": 8750},
                {"name": "Vanguard Total Stock Market ETF", "symbol": "VTI", "allocation_percent": 8.0, "value": 10000},
                {"name": "Vanguard Total International Stock ETF", "symbol": "VXUS", "allocation_percent": 10.0, "value": 12500},
                {"name": "Vanguard FTSE Europe ETF", "symbol": "VEA", "allocation_percent": 7.0, "value": 8750},
                {"name": "NextEra Energy Inc", "symbol": "NEE", "allocation_percent": 4.0, "value": 5000},
                {"name": "Tesla Inc", "symbol": "TSLA", "allocation_percent": 3.0, "value": 3750},
                {"name": "First Solar Inc", "symbol": "FSLR", "allocation_percent": 2.0, "value": 2500},
                {"name": "Brookfield Renewable Corp", "symbol": "BEPC", "allocation_percent": 2.0, "value": 2500},
                {"name": "Vanguard Real Estate ETF", "symbol": "VNQ", "allocation_percent": 4.0, "value": 5000}
            ]
        }
        
        # Generate PDF report
        try:
            from communication_agent import generate_pdf_report
            import os
            pdf_path = generate_pdf_report(preset_report_data)
            preset_report_data["pdf_available"] = True
            preset_report_data["pdf_filename"] = os.path.basename(pdf_path)
        except ImportError as e:
            logger.warning(f"PDF generation unavailable: {e}")
            preset_report_data["pdf_available"] = False
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            preset_report_data["pdf_available"] = False
        
        return {
            "status": "success",
            "report": preset_report_data,
            "message": "Investment report generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating investment report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@app.get("/api/download-report/{filename}")
async def download_pdf_report(filename: str):
    """
    Download generated PDF report
    
    Serves the PDF file for download with proper content headers.
    """
    try:
        import os
        
        # Security check - only allow PDF files and prevent directory traversal
        if not filename.endswith('.pdf') or '..' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Check if file exists in current directory (where PDFs are generated)
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        return FileResponse(
            path=file_path,
            filename=f"investment_report_{datetime.now().strftime('%Y%m%d')}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving PDF file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")


@app.get("/api/report/latest")
async def get_latest_report():
    """
    Get the most recent investment report using preset data
    """
    try:
        import os
        import glob
        
        # Return the same preset report data that generate_report creates
        latest_report_data = {
            "report_title": "Investment Portfolio Analysis Report", 
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "client_id": "demo_profile_12345",
            "executive_summary": "This comprehensive investment strategy is designed to meet your long-term financial objectives through a carefully balanced portfolio approach. The recommended $125,000 portfolio emphasizes growth potential while maintaining appropriate risk management, targeting a 7.6% annual return aligned with your ESG preferences and moderate risk tolerance.",
            "allocation_rationale": "The portfolio allocation is strategically designed for long-term wealth building with ESG integration. The 70% equity allocation provides growth through quality individual stocks while 30% fixed income offers stability.",
            "selection_rationale": "Individual stock selections focus on industry-leading companies with strong ESG characteristics including Microsoft, Google, Apple, NVIDIA, NextEra Energy, and Tesla.",
            "risk_commentary": "Portfolio risk is well-managed through diversification, quality selection, and appropriate asset allocation for moderate risk tolerance.",
            "key_recommendations": [
                "Implement systematic monthly investing of $1,500",
                "Maintain ESG-focused allocation", 
                "Review portfolio quarterly",
                "Consider tax-loss harvesting",
                "Monitor concentration risk"
            ],
            "next_steps": [
                "Set up automatic monthly investments",
                "Schedule quarterly reviews", 
                "Establish emergency fund",
                "Review beneficiaries",
                "Plan contribution increases"
            ],
            "portfolio_allocation": {
                "Technology Stocks": 29.0,
                "Bonds": 30.0,
                "Renewable Energy": 12.0,
                "International": 17.0,
                "Broad Market ETFs": 8.0,
                "Real Estate": 4.0
            },
            "individual_holdings": [
                {"name": "Microsoft Corporation", "symbol": "MSFT", "allocation_percent": 8.0, "value": 10000},
                {"name": "Alphabet Inc", "symbol": "GOOGL", "allocation_percent": 6.0, "value": 7500},
                {"name": "Apple Inc", "symbol": "AAPL", "allocation_percent": 5.0, "value": 6250},
                {"name": "NVIDIA Corporation", "symbol": "NVDA", "allocation_percent": 4.0, "value": 5000},
                {"name": "Vanguard Total Bond Market ETF", "symbol": "BND", "allocation_percent": 15.0, "value": 18750},
                {"name": "NextEra Energy Inc", "symbol": "NEE", "allocation_percent": 4.0, "value": 5000},
                {"name": "Tesla Inc", "symbol": "TSLA", "allocation_percent": 3.0, "value": 3750}
            ]
        }
        
        # Check for existing PDF files and add the most recent one
        pdf_files = glob.glob("investment_report_*.pdf")
        if pdf_files:
            # Sort by modification time and get the most recent
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            latest_report_data["pdf_available"] = True
            latest_report_data["pdf_filename"] = os.path.basename(latest_pdf)
        else:
            latest_report_data["pdf_available"] = False
            latest_report_data["pdf_filename"] = None
        
        return {
            "status": "success",
            "report": latest_report_data
        }
        
    except Exception as e:
        logger.error(f"Error retrieving latest report: {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving report: {str(e)}"
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
    from profile_processor_agent import UserProfile
    
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
    REAL AGENT VERSION - Using actual agent execution with streaming callbacks
    """
    try:
        # Convert to UserProfile object
        user_profile_obj = create_user_profile_object(user_profile)
        
        # Log user preferences including specific assets
        personal_values = user_profile.get("personal_values", {})
        esg_preferences = personal_values.get("esg_preferences", {})
        specific_assets = esg_preferences.get("specific_assets", [])
        avoid_industries = esg_preferences.get("avoid_industries", [])
        prefer_industries = esg_preferences.get("prefer_industries", [])
        
        logger.info("=== USER PREFERENCES DETECTED ===")
        logger.info(f"User-specified specific assets: {specific_assets}")
        logger.info(f"Industries to avoid: {avoid_industries}")
        logger.info(f"Preferred industries: {prefer_industries}")
        logger.info(f"ESG prioritization: {user_profile.get('esg_prioritization', False)}")
        logger.info("=====================================")
        
        # Initialize MainAgent with streaming
        logger.info("REAL AGENT MODE: Using actual agent execution")
        main_agent = MainAgent()
        
        # Create a queue to collect streaming events
        import asyncio
        event_queue = asyncio.Queue()
        
        # Define progress callback that adds events to queue
        async def progress_callback(event_type, data):
            await event_queue.put((event_type, data))
        
        # Start the workflow in a separate task
        async def run_workflow():
            try:
                result = main_agent.run_complete_workflow(user_profile_obj, progress_callback)
                await event_queue.put(("workflow_complete", {"result": result}))
            except Exception as e:
                await event_queue.put(("workflow_error", {"error": str(e)}))
        
        # Start workflow task
        workflow_task = asyncio.create_task(run_workflow())
        
        # Stream events as they come
        while True:
            try:
                # Wait for next event with timeout
                event_type, data = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                
                if event_type == "workflow_complete":
                    # Workflow finished successfully
                    result = data["result"]
                    yield create_sse_event("workflow_complete", {
                        "progress": 100,
                        "message": "Workflow completed successfully",
                        "result": result
                    })
                    break
                elif event_type == "workflow_error":
                    # Workflow failed
                    yield create_sse_event("workflow_error", {
                        "message": f"Workflow failed: {data['error']}",
                        "type": "workflow_error"
                    })
                    break
                else:
                    # Regular progress event
                    yield create_sse_event(event_type, data)
                    
            except asyncio.TimeoutError:
                # No event received within timeout, check if workflow is still running
                if workflow_task.done():
                    # Workflow finished but no completion event was sent
                    try:
                        result = workflow_task.result()
                        yield create_sse_event("workflow_complete", {
                            "progress": 100,
                            "message": "Workflow completed successfully",
                            "result": result
                        })
                    except Exception as e:
                        yield create_sse_event("workflow_error", {
                            "message": f"Workflow failed: {str(e)}",
                            "type": "workflow_error"
                        })
                    break
                else:
                    # Still running, send keepalive
                    yield create_sse_event("keepalive", {
                        "message": "Workflow in progress...",
                        "progress": 50
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
    Generate detailed answers about our realistic portfolio when Communication Agent is unavailable
    """
    try:
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["allocation", "why", "chosen"]):
            return """The 70% equity / 30% bond allocation is specifically designed for your profile with a 10+ year investment horizon and moderate risk tolerance.

**Equity Holdings (70%):** Focus on high-quality individual stocks including Microsoft (8%), Google (6%), Apple (5%), and NVIDIA (4%), plus diversified ETFs. This provides growth potential while the technology focus aligns with your ESG preferences.

**Fixed Income (30%):** Bond ETFs and government securities provide portfolio stability and help manage the overall volatility of your $125,000 portfolio.

**ESG Integration:** All selections avoid tobacco and weapons sectors while emphasizing companies with strong environmental and social practices like NextEra Energy and Tesla."""
        
        elif any(word in question_lower for word in ["risk", "risky", "safe"]):
            return """Your portfolio risk is carefully managed for your moderate risk tolerance:

**Expected Annual Return:** 7.6% - realistic and achievable over your time horizon
**Volatility Management:** 70/30 equity/bond split reduces volatility compared to 100% stock allocation
**Concentration Risk:** No single stock exceeds 8% (Microsoft is largest holding)
**ESG Risk Mitigation:** Avoiding controversial sectors reduces regulatory and reputational risks
**Debt Consideration:** Portfolio planning accounts for your 33% debt-to-income ratio

The portfolio targets steady growth while avoiding excessive risk that could jeopardize your financial goals."""
        
        elif any(word in question_lower for word in ["selection", "stocks", "investments", "picked", "microsoft", "google", "apple", "tesla"]):
            return """Individual stock selections focus on industry leaders with strong ESG characteristics:

**Technology Leaders:**
• Microsoft (8%) - Cloud computing dominance and carbon negative commitments
• Google (6%) - AI leadership and renewable energy investments  
• Apple (5%) - Premium brand strength and supply chain sustainability
• NVIDIA (4%) - AI/semiconductor leadership driving digital transformation

**Clean Energy:**
• NextEra Energy (4%) - Largest US renewable energy developer
• Tesla (3%) - Electric vehicle and energy storage innovation

**ETF Core Holdings:** Provide diversified market exposure with low fees

All selections combine growth potential with your ESG values, avoiding tobacco and weapons while emphasizing sustainable business practices."""
        
        elif any(word in question_lower for word in ["esg", "values", "environmental", "social"]):
            return """ESG integration is central to your portfolio strategy:

**Environmental Focus:** Holdings include NextEra Energy (renewable energy leader) and Tesla (electric vehicles), while tech companies like Microsoft and Google have committed to carbon neutrality.

**Social Responsibility:** All selected companies demonstrate strong labor practices, diversity initiatives, and positive community impact.

**Exclusionary Screening:** The portfolio specifically avoids tobacco, weapons, and other sectors that conflict with your values.

This approach allows you to generate competitive returns (targeting 7.6% annually) while supporting companies aligned with your environmental and social beliefs."""
        
        elif any(word in question_lower for word in ["review", "rebalance", "when", "monthly", "1500"]):
            return """Portfolio management includes systematic investing and regular rebalancing:

**Monthly Investing:** Your $1,500 monthly contributions benefit from dollar-cost averaging, reducing timing risk over your investment horizon.

**Quarterly Reviews:** Portfolio allocations are monitored quarterly, with rebalancing when positions drift more than 5% from targets.

**Contribution Strategy:** Monthly investments are directed toward underweight positions, providing natural rebalancing.

**Performance Monitoring:** Expected 7.6% annual returns are tracked against benchmarks with adjustments as needed.

This disciplined approach helps maintain your target allocation while building wealth systematically over time."""
        
        elif any(word in question_lower for word in ["return", "performance", "7.6", "growth"]):
            return """Your portfolio targets a 7.6% annual return based on realistic long-term expectations:

**Historical Context:** This return target is conservative compared to long-term stock market averages while accounting for current market conditions.

**Asset Mix Impact:** The 70/30 equity/bond allocation balances growth potential with stability.

**Individual Stock Alpha:** Quality selections like Microsoft, Google, and Apple may outperform market averages over time.

**ESG Performance:** Studies show ESG-focused portfolios can match or exceed traditional returns while reducing certain risks.

With systematic $1,500 monthly contributions and 7.6% growth, your $125,000 portfolio is positioned for substantial long-term wealth building."""
        
        else:
            return f"""Thank you for your question about "{question}".

Your $125,000 portfolio is designed as a comprehensive strategy balancing growth and ESG values:

**Key Features:**
• 70% equity allocation with individual stocks (MSFT, GOOGL, AAPL, NVDA, NEE, TSLA) plus ETFs
• 30% fixed income for stability and risk management  
• 7.6% expected annual return over your investment timeline
• $1,500 monthly contributions for systematic wealth building
• ESG integration avoiding tobacco/weapons sectors

For specific questions about allocation decisions, individual stock rationale, or risk management, I can provide detailed explanations tailored to your investment strategy."""
            
    except Exception as e:
        logger.error(f"Error generating fallback answer: {e}")
        return "I'm unable to provide a detailed answer at the moment. Please try again or contact support."


@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio recommendations"""
    return {
        "portfolio": {
            "total_value": 125000,  # Realistic current portfolio value for someone starting out
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

@app.post("/api/news-insights")
async def get_news_insights_endpoint(request_data: Dict[str, Any]):
    """
    Get AI news insights for a stock symbol
    Returns price data, news articles, and market summary
    """
    symbol = request_data.get("symbol")
    
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    try:
        logger.info(f"🔄 Getting news insights for {symbol}")
        
        # Get complete analysis
        analysis_data = get_news_insights_analysis(symbol)
        
        logger.info(f"✅ News insights complete for {symbol}")
        
        return {
            "status": "success",
            "data": analysis_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting news insights for {symbol}: {str(e)}")
        return {
            "status": "error",
            "symbol": symbol,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    print("🚀 Starting PortfolioAI Backend Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🔗 Frontend should connect from: http://localhost:3000")
    
    uvicorn.run(
        app, 
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
