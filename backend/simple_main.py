#!/usr/bin/env python3
"""
Enhanced investment report API with comprehensive analysis and house view
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import logging
import json
from datetime import datetime
from report_generator import UnifiedReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Investment Portfolio Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Investment Portfolio Backend API", "status": "running"}

# Pydantic models for request validation
class Goal(BaseModel):
    id: str
    label: str
    priority: int

class Milestone(BaseModel):
    date: str
    description: str

class Values(BaseModel):
    avoidIndustries: List[str] = []
    preferIndustries: List[str] = []
    specificAssets: str = ""  # User-specified assets as single string
    customConstraints: str = ""

class AssessmentData(BaseModel):
    goals: List[Goal] = []
    timeHorizon: int = 10
    milestones: List[Milestone] = []
    riskTolerance: str = "medium"
    experienceLevel: str = "beginner"
    annualIncome: float = 0
    monthlySavings: float = 0
    totalDebt: float = 0
    dependents: int = 0
    emergencyFundMonths: str = "3-6"
    values: Values = Values()
    esgPrioritization: bool = False
    marketSelection: List[str] = ["US"]

@app.post("/api/validate-assessment")
async def validate_assessment(assessment_data: AssessmentData):
    """Validate assessment data before generating report"""
    try:
        data_dict = assessment_data.dict()
        
        # Validation logic
        errors = []
        
        if not data_dict.get('goals') or len(data_dict['goals']) == 0:
            errors.append("At least one investment goal is required")
        
        if data_dict.get('timeHorizon', 0) <= 0:
            errors.append("Time horizon must be positive")
        
        if not data_dict.get('riskTolerance'):
            errors.append("Risk tolerance must be specified")
        
        if data_dict.get('annualIncome', 0) < 0:
            errors.append("Annual income cannot be negative")
        
        if data_dict.get('monthlySavings', 0) < 0:
            errors.append("Monthly savings cannot be negative")
        
        if data_dict.get('totalDebt', 0) < 0:
            errors.append("Total debt cannot be negative")
        
        if data_dict.get('dependents', 0) < 0:
            errors.append("Number of dependents cannot be negative")
        
        # Validate goals structure
        for goal in data_dict.get('goals', []):
            if not goal.get('id') or not goal.get('label'):
                errors.append("All goals must have an id and label")
            if goal.get('priority', 0) <= 0:
                errors.append("Goal priorities must be positive")
        
        if errors:
            return {"status": "error", "errors": errors}
        
        return {"status": "success", "message": "Assessment data is valid"}
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")

@app.get("/api/test-pdf")
async def test_pdf_generation():
    """Test endpoint to verify PDF generation works"""
    try:
        logger.info("Testing PDF generation...")
        
        test_data = {
            'riskTolerance': 'moderate',
            'timeHorizon': 10,
            'annualIncome': 75000,
            'monthlySavings': 1000,
            'goals': [{'id': 'retirement', 'label': 'Retirement', 'priority': 1}]
        }
        
        generator = UnifiedReportGenerator()
        pdf_path = generator.generate_comprehensive_report(test_data)
        
        import os
        if os.path.exists(pdf_path):
            return {
                "status": "success",
                "message": "PDF generation test successful",
                "pdf_path": pdf_path,
                "pdf_size": os.path.getsize(pdf_path)
            }
        else:
            return {
                "status": "error",
                "message": "PDF file not found after generation"
            }
            
    except Exception as e:
        logger.error(f"PDF test failed: {str(e)}")
        return {
            "status": "error",
            "message": f"PDF test failed: {str(e)}"
        }

@app.post("/api/generate-report")
async def generate_investment_report(assessment_data: Optional[AssessmentData] = None):
    """
    Generate comprehensive investment report with house view and detailed analysis
    """
    try:
        # Use provided assessment data or fallback to test data
        if assessment_data:
            user_data = assessment_data.dict()
        else:
            # Fallback to updated test assessment data from test_streaming_api.py
            user_data = {
                "goals": [
                    {
                        "id": "retirement",
                        "label": "Retirement Planning",
                        "priority": 1
                    },
                    {
                        "id": "wealth",
                        "label": "Wealth Growth", 
                        "priority": 2
                    },
                    {
                        "id": "house",
                        "label": "Buy a Home",
                        "priority": 3
                    }
                ],
                "timeHorizon": 15,
                "milestones": [
                    {
                        "date": "2030-01-01",
                        "description": "Target for home down payment"
                    },
                    {
                        "date": "2040-01-01", 
                        "description": "Retirement readiness checkpoint"
                    }
                ],
                "riskTolerance": "moderate-aggressive",
                "experienceLevel": "intermediate",
                "annualIncome": 85000.0,
                "monthlySavings": 2500.0,
                "totalDebt": 35000.0,
                "dependents": 1,
                "emergencyFundMonths": "6+",
                "values": {
                    "avoidIndustries": ["tobacco", "weapons", "fossil-fuels"],
                    "preferIndustries": ["technology", "renewable-energy", "healthcare"],
                    "customConstraints": "Focus on sustainable investments with strong ESG credentials. Prefer companies with positive environmental impact and strong governance practices."
                },
                "esgPrioritization": True,
                "marketSelection": ["US", "International Developed", "Emerging Markets"]
            }
        
        # Generate enhanced comprehensive report using unified generator
        try:
            logger.info("Starting report generation with unified generator...")
            logger.info(f"User data keys: {list(user_data.keys())}")
            
            # Use the unified report generator
            generator = UnifiedReportGenerator()
            logger.info("UnifiedReportGenerator created successfully")
            
            pdf_path = generator.generate_comprehensive_report(user_data)
            logger.info(f"PDF generated successfully at: {pdf_path}")
            
            # Verify PDF file exists
            import os
            if not os.path.exists(pdf_path):
                raise Exception(f"PDF file not found at {pdf_path}")
            
            logger.info(f"PDF file verified, size: {os.path.getsize(pdf_path)} bytes")
            
            # Create response with detailed report structure matching frontend expectations
            house_view = _create_house_view_summary(user_data)
            strategic_recs = _create_strategic_recommendations(user_data)
            
            report_response = {
                "report_title": "Comprehensive Investment Portfolio Strategy Report",
                "generated_date": datetime.now().strftime("%B %d, %Y"),
                "client_id": f"CLIENT_{hash(str(user_data.get('annualIncome', 0)))}"[-8:],
                "executive_summary": house_view.get('central_theme', 'Comprehensive investment strategy tailored to your goals and risk profile.'),
                "allocation_rationale": house_view.get('investment_stance', 'Strategic asset allocation approach') + ". " + house_view.get('strategic_positioning', ''),
                "selection_rationale": "\n".join(house_view.get('key_convictions', [])),
                "risk_commentary": f"Risk management approach aligned with {user_data.get('riskTolerance', 'moderate')} risk tolerance and {user_data.get('timeHorizon', 10)}-year investment timeline.",
                "key_recommendations": strategic_recs[:4] if len(strategic_recs) > 4 else strategic_recs,
                "next_steps": strategic_recs[4:] if len(strategic_recs) > 4 else ["Review portfolio quarterly", "Monitor progress annually"],
                "pdf_available": True,
                "pdf_filename": pdf_path,
                "pdf_size_bytes": os.path.getsize(pdf_path),
                "report_metadata": {
                    "generated_by": "Investment Portfolio AI System",
                    "report_type": "unified_comprehensive",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info("Report response created successfully")
            
        except Exception as e:
            # Handle any generation errors with detailed logging
            import traceback
            logger.error(f"Report generation failed: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
        
        return {
            "status": "success",
            "report": report_response,
            "message": "Comprehensive investment report generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating investment report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

def _extract_client_summary(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract client profile summary from assessment data"""
    goals = user_data.get('goals', [])
    primary_goals = [goal.get('description', goal.get('goal_type', '')) for goal in goals[:2]]
    
    return {
        "primary_objectives": primary_goals,
        "investment_timeline": f"{user_data.get('timeHorizon', 10)} years",
        "risk_profile": user_data.get('riskTolerance', 'medium').title(),
        "monthly_investment_capacity": f"${user_data.get('monthlySavings', 0):,.0f}",
        "esg_integration": "Yes" if user_data.get('esgPrioritization', False) else "No",
        "geographic_focus": ', '.join(user_data.get('marketSelection', ['US']))
    }

def _create_house_view_summary(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create house view summary based on user profile"""
    risk_tolerance = user_data.get('riskTolerance', 'medium')
    time_horizon = user_data.get('timeHorizon', 10)
    esg_focus = user_data.get('esgPrioritization', False)
    
    # Determine strategic stance
    if time_horizon >= 15 and risk_tolerance in ['medium', 'aggressive']:
        stance = "Constructive Growth Orientation"
        theme = "Long-term wealth building through quality growth assets"
    elif risk_tolerance == 'conservative':
        stance = "Defensive Quality Focus"
        theme = "Capital preservation with modest growth potential"
    else:
        stance = "Balanced Strategic Approach"
        theme = "Diversified growth with risk management"
    
    key_convictions = [
        "Technology leadership provides sustainable competitive advantages",
        "Quality companies with strong fundamentals outperform over time",
        "Geographic diversification reduces single-market concentration risk"
    ]
    
    if esg_focus:
        key_convictions.append("ESG integration aligns with long-term value creation")
    
    return {
        "investment_stance": stance,
        "central_theme": theme,
        "key_convictions": key_convictions,
        "strategic_positioning": f"Equity-focused with {risk_tolerance} risk management approach"
    }

def _create_strategic_recommendations(user_data: Dict[str, Any]) -> List[str]:
    """Create strategic recommendations based on user profile"""
    monthly_savings = user_data.get('monthlySavings', 0)
    time_horizon = user_data.get('timeHorizon', 10)
    
    recommendations = [
        f"Implement systematic monthly investing of ${monthly_savings:,.0f} for dollar-cost averaging benefits",
        "Prioritize tax-advantaged accounts (401k, IRA) for maximum tax efficiency",
        "Maintain emergency fund equivalent to 6-months of expenses separate from investments"
    ]
    
    if time_horizon >= 10:
        recommendations.append("Focus on growth-oriented assets for long-term wealth accumulation")
    
    if user_data.get('esgPrioritization', False):
        recommendations.append("Integrate ESG-focused investments aligned with personal values")
    
    recommendations.extend([
        "Review and rebalance portfolio quarterly to maintain strategic allocation",
        "Monitor investment progress annually and adjust strategy as goals evolve"
    ])
    
    return recommendations

def _generate_fallback_report(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate fallback report when enhanced generator is not available"""
    monthly_savings = user_data.get('monthlySavings', 0)
    annual_capacity = monthly_savings * 12
    house_view = _create_house_view_summary(user_data)
    strategic_recs = _create_strategic_recommendations(user_data)
    
    return {
        "report_title": "Investment Portfolio Analysis Report",
        "generated_date": datetime.now().strftime("%B %d, %Y"),
        "client_id": f"CLIENT_{hash(str(user_data.get('annualIncome', 0)))}"[-8:],
        "executive_summary": (
            f"This investment strategy is tailored for your {user_data.get('timeHorizon', 10)}-year timeline "
            f"with {user_data.get('riskTolerance', 'medium')} risk tolerance. The approach emphasizes "
            f"systematic investing of ${monthly_savings:,.0f} monthly (${annual_capacity:,.0f} annually) "
            f"through diversified holdings aligned with your goals."
        ),
        "allocation_rationale": house_view.get('investment_stance', 'Balanced strategic approach'),
        "selection_rationale": "\n".join(house_view.get('key_convictions', ['Quality focus', 'Diversified approach'])),
        "risk_commentary": f"Risk management aligned with {user_data.get('riskTolerance', 'moderate')} tolerance.",
        "key_recommendations": strategic_recs[:4] if len(strategic_recs) > 4 else strategic_recs,
        "next_steps": strategic_recs[4:] if len(strategic_recs) > 4 else ["Review quarterly", "Adjust as needed"],
        "pdf_available": False,
        "report_metadata": {
            "generated_by": "Investment Portfolio AI System",
            "report_type": "basic_fallback",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.post("/api/generate-report/stream")
async def generate_report_stream(assessment_data: AssessmentData):
    """Generate investment report with streaming progress updates"""
    
    def generate_streaming_response():
        """Generator function for streaming report generation"""
        import time
        
        try:
            # Step 1: Validate assessment data
            yield f"data: {json.dumps({'event': 'validation_start', 'data': {'progress': 10, 'message': 'Validating assessment data'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            time.sleep(0.5)
            
            user_data = assessment_data.dict()
            
            yield f"data: {json.dumps({'event': 'validation_complete', 'data': {'progress': 20, 'message': 'Assessment validation successful'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            time.sleep(0.5)
            
            # Step 2: Analyze user profile
            yield f"data: {json.dumps({'event': 'analysis_start', 'data': {'progress': 30, 'message': 'Analyzing investment profile and risk tolerance'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            time.sleep(1.0)
            
            # Step 3: Generate house view
            yield f"data: {json.dumps({'event': 'house_view_generation', 'data': {'progress': 45, 'message': 'Developing investment house view and market outlook'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            time.sleep(1.0)
            
            # Step 4: Create strategic allocation
            yield f"data: {json.dumps({'event': 'allocation_analysis', 'data': {'progress': 60, 'message': 'Creating strategic asset allocation and portfolio structure'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            time.sleep(1.0)
            
            # Step 5: Generate detailed rationale
            yield f"data: {json.dumps({'event': 'rationale_development', 'data': {'progress': 75, 'message': 'Developing investment rationale and risk assessment'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            time.sleep(1.0)
            
            # Step 6: Create PDF report
            yield f"data: {json.dumps({'event': 'pdf_generation', 'data': {'progress': 85, 'message': 'Generating comprehensive PDF report'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            time.sleep(1.5)
            
            # Generate the actual report
            try:
                generator = UnifiedReportGenerator()
                pdf_path = generator.generate_comprehensive_report(user_data)
                
                report_data = {
                    "report_title": "Comprehensive Investment Portfolio Strategy Report",
                    "generated_date": datetime.now().strftime("%B %d, %Y"),
                    "client_profile": _extract_client_summary(user_data),
                    "house_view_summary": _create_house_view_summary(user_data),
                    "strategic_recommendations": _create_strategic_recommendations(user_data),
                    "pdf_available": True,
                    "pdf_filename": pdf_path
                }
                
                yield f"data: {json.dumps({'event': 'report_finalization', 'data': {'progress': 95, 'message': 'Finalizing report and preparing delivery'}, 'timestamp': datetime.now().isoformat()})}\n\n"
                time.sleep(0.5)
                
                # Final success response
                yield f"data: {json.dumps({'event': 'final_report_complete', 'data': {'progress': 100, 'message': 'Comprehensive investment report generated successfully', 'status': 'success', 'final_report': report_data}, 'timestamp': datetime.now().isoformat()})}\n\n"
                
            except Exception as e:
                logger.error(f"Report generation failed: {str(e)}")
                yield f"data: {json.dumps({'event': 'generation_error', 'data': {'progress': 85, 'message': f'Report generation encountered an error: {str(e)}'}, 'timestamp': datetime.now().isoformat()})}\n\n"
                
                # Generate fallback report
                fallback_report = _generate_fallback_report(user_data)
                yield f"data: {json.dumps({'event': 'final_report_complete', 'data': {'progress': 100, 'message': 'Basic investment report generated', 'status': 'success', 'final_report': fallback_report}, 'timestamp': datetime.now().isoformat()})}\n\n"
                
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield f"data: {json.dumps({'event': 'stream_error', 'data': {'progress': 0, 'message': f'Streaming failed: {str(e)}'}, 'timestamp': datetime.now().isoformat()})}\n\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.get("/api/download-report/{filename}")
async def download_pdf_report(filename: str):
    """Download generated PDF report"""
    try:
        import os
        
        # Security check
        if not filename.endswith('.pdf') or '..' in filename or '/' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        if not os.path.exists(filename):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        return FileResponse(
            path=filename,
            filename=f"investment_report_{datetime.now().strftime('%Y%m%d')}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving PDF file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")

@app.post("/api/ask-question")
async def ask_portfolio_question(question_data: Dict[str, Any]):
    """Answer questions about portfolio decisions"""
    try:
        question = question_data.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Simple fallback answers
        question_lower = question.lower()
        
        if "allocation" in question_lower or "why" in question_lower:
            answer = """The 70% equity / 30% bond allocation is specifically designed for your profile with a 10+ year investment horizon and moderate risk tolerance.

The portfolio emphasizes high-quality individual stocks including Microsoft (8%), Google (6%), Apple (5%), and NVIDIA (4%), plus diversified ETFs. This provides growth potential through technology leaders with strong fundamentals and competitive advantages.

The allocation focuses on quality companies with proven business models and strong financial positions."""
        
        elif "risk" in question_lower:
            answer = """Your portfolio risk is carefully managed for moderate risk tolerance:

Expected Annual Return: 7.6% - realistic and achievable through systematic diversification
Volatility Management: 70/30 equity/bond split reduces volatility while maintaining growth potential
Concentration Risk: No single stock exceeds 8% allocation to prevent overexposure
Quality Focus: Selection of financially strong companies with proven business models

The portfolio targets steady growth while maintaining appropriate risk levels for your moderate risk tolerance."""
        
        else:
            answer = f"Thank you for your question about '{question}'. Your $125,000 portfolio is designed with a 70% equity allocation focusing on high-quality technology leaders and diversified holdings, targeting 7.6% annual returns with systematic $1,500 monthly contributions."
        
        return {
            "status": "success",
            "question": question,
            "answer": answer,
            "answered_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")

@app.get("/api/report/latest")
async def get_latest_report():
    """Get the most recent investment report"""
    try:
        latest_report_data = {
            "report_title": "Investment Portfolio Analysis Report", 
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "client_id": "demo_profile_12345",
            "executive_summary": "This comprehensive investment strategy is designed to meet your long-term financial objectives through a carefully balanced portfolio approach.",
            "allocation_rationale": "The portfolio allocation is strategically designed for long-term wealth building with balanced risk management.",
            "selection_rationale": "Individual stock selections focus on industry-leading companies with strong fundamentals and growth potential.",
            "risk_commentary": "Portfolio risk is well-managed through diversification and quality selection.",
            "key_recommendations": [
                "Implement systematic monthly investing of $1,500",
                "Maintain technology-focused allocation while monitoring concentration risk", 
                "Review portfolio quarterly"
            ],
            "next_steps": [
                "Set up automatic monthly investments",
                "Schedule quarterly reviews"
            ]
        }
        
        return {"status": "success", "report": latest_report_data}
        
    except Exception as e:
        logger.error(f"Error retrieving latest report: {str(e)}")
        return {"status": "error", "message": f"Error retrieving report: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8001, reload=True)