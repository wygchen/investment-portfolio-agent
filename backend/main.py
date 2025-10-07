from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uvicorn
import logging
from datetime import datetime, timedelta
import random
import asyncio

# Import watsonx service and agents
from services.watsonx_service import get_watsonx_service, initialize_watsonx_service
from agents.agent_coordinator import get_agent_coordinator, initialize_agent_coordinator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PortfolioAI API",
    description="AI-powered investment portfolio management API with Watsonx.ai integration",
    version="1.0.0"
)

# Global service instances
watsonx_service = None
agent_coordinator = None

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class AssessmentData(BaseModel):
    age: int = Field(..., ge=18, le=100)
    income: int = Field(..., ge=0)
    net_worth: int = Field(..., ge=0)
    dependents: int = Field(..., ge=0)
    primary_goal: str
    time_horizon: int = Field(..., ge=1, le=50)
    target_amount: int = Field(..., ge=0)
    monthly_contribution: int = Field(..., ge=0)
    risk_tolerance: int = Field(..., ge=1, le=10)
    risk_capacity: str
    previous_experience: List[str]
    market_reaction: str
    investment_style: str
    rebalancing_frequency: str
    esg_preferences: bool
    special_circumstances: Optional[str] = None
    # New fields for equity selection
    sector_preferences: Optional[List[str]] = Field(default=[], description="Preferred investment sectors")
    region_preferences: Optional[List[str]] = Field(default=[], description="Preferred investment regions")

class PortfolioAllocation(BaseModel):
    name: str
    percentage: float = Field(..., ge=0, le=100)
    amount: float = Field(..., ge=0)
    color: Optional[str] = None
    rationale: Optional[str] = None

class PortfolioRecommendation(BaseModel):
    allocation: List[PortfolioAllocation]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    risk_score: float
    confidence: int = Field(..., ge=0, le=100)

class MarketDataPoint(BaseModel):
    timestamp: datetime
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: Optional[int] = None

class RiskMetrics(BaseModel):
    var_95: float
    cvar_95: float
    maximum_drawdown: float
    beta: float
    correlation_matrix: Dict[str, Dict[str, float]]

# In-memory storage for demo purposes
assessments_db: Dict[str, Dict[str, Any]] = {}
portfolios_db: Dict[str, Dict[str, Any]] = {}

# Startup event to initialize services
@app.on_event("startup")
async def startup_event():
    """Initialize watsonx service and agent coordinator on startup"""
    global watsonx_service, agent_coordinator
    try:
        logger.info("Initializing Watsonx.ai service...")
        watsonx_service = await initialize_watsonx_service()
        logger.info("Watsonx.ai service initialized successfully")
        
        # Initialize agent coordinator with the LLM
        if watsonx_service and watsonx_service.llm:
            logger.info("Initializing Agent Coordinator...")
            agent_coordinator = await initialize_agent_coordinator(watsonx_service.llm)
            logger.info("Agent Coordinator initialized successfully")
        else:
            logger.warning("Cannot initialize Agent Coordinator - Watsonx LLM not available")
            
    except Exception as e:
        logger.warning(f"Service initialization failed: {e}")
        logger.info("Application will continue with fallback responses")

# Root endpoint
@app.get("/")
async def root():
    service_status = "unknown"
    if watsonx_service:
        status_info = watsonx_service.get_service_status()
        service_status = status_info["status"]
    
    return {
        "message": "PortfolioAI API with Watsonx.ai", 
        "status": "running", 
        "version": "1.0.0",
        "watsonx_status": service_status
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    health_status = {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    # Add watsonx service health if available
    if watsonx_service:
        watsonx_status = watsonx_service.get_service_status()
        health_status["watsonx"] = watsonx_status
        
        # Perform actual health check
        try:
            is_healthy = await watsonx_service.health_check()
            health_status["watsonx"]["health_check"] = "passed" if is_healthy else "failed"
        except Exception as e:
            health_status["watsonx"]["health_check"] = f"error: {str(e)}"
    
    return health_status

# Service status endpoints
@app.get("/api/watsonx/status")
async def get_watsonx_status():
    """Get detailed Watsonx service status"""
    if not watsonx_service:
        return {"status": "not_initialized", "message": "Watsonx service not initialized"}
    
    return watsonx_service.get_service_status()

@app.get("/api/agents/status")
async def get_agents_status():
    """Get agent coordinator and individual agent status"""
    if not agent_coordinator:
        return {"status": "not_initialized", "message": "Agent coordinator not initialized"}
    
    return agent_coordinator.get_agent_status()

@app.get("/api/agents/health")
async def get_agents_health():
    """Perform health check on all agents"""
    if not agent_coordinator:
        return {"status": "not_initialized", "message": "Agent coordinator not initialized"}
    
    return await agent_coordinator.health_check()

@app.get("/api/agents/session/{session_id}")
async def get_session_status(session_id: str):
    """Get status of a specific analysis session"""
    if not agent_coordinator:
        raise HTTPException(status_code=404, detail="Agent coordinator not available")
    
    session_status = await agent_coordinator.get_session_status(session_id)
    if not session_status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_status

# Assessment endpoints
@app.post("/api/assessment", response_model=Dict[str, Any])
async def submit_assessment(assessment: AssessmentData) -> Dict[str, Any]:
    """Submit user assessment data for AI portfolio generation"""
    try:
        user_id = f"user_{len(assessments_db) + 1}"
        assessments_db[user_id] = assessment.model_dump()
        
        logger.info(f"Assessment submitted for user {user_id}")
        
        return {
            "user_id": user_id,
            "status": "success",
            "message": "Assessment data received successfully",
            "assessment_id": user_id
        }
    except Exception as e:
        logger.error(f"Error submitting assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit assessment")

@app.get("/api/assessment/{user_id}", response_model=AssessmentData)
async def get_assessment(user_id: str) -> AssessmentData:
    """Retrieve user assessment data"""
    if user_id not in assessments_db:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    return AssessmentData(**assessments_db[user_id])

# Portfolio generation endpoints
@app.post("/api/portfolio/generate", response_model=PortfolioRecommendation)
async def generate_portfolio(assessment: AssessmentData) -> PortfolioRecommendation:
    """Generate AI-powered portfolio recommendation based on assessment"""
    try:
        # Mock AI portfolio generation logic
        portfolio = _generate_mock_portfolio(assessment)
        
        user_id = f"user_{len(portfolios_db) + 1}"
        portfolios_db[user_id] = portfolio.model_dump()
        
        logger.info(f"Portfolio generated for assessment with risk tolerance {assessment.risk_tolerance}")
        
        return portfolio
    except Exception as e:
        logger.error(f"Error generating portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate portfolio")

@app.get("/api/portfolio/{user_id}", response_model=PortfolioRecommendation)
async def get_portfolio(user_id: str) -> PortfolioRecommendation:
    """Retrieve user portfolio recommendation"""
    if user_id not in portfolios_db:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return PortfolioRecommendation(**portfolios_db[user_id])

# Market data endpoints
@app.get("/api/market-data/overview")
async def get_market_overview() -> Dict[str, Any]:
    """Get current market overview and key indicators"""
    return {
        "market_indices": [
            {"name": "S&P 500", "value": 4890.25, "change": 1.2, "change_percent": 2.45},
            {"name": "NASDAQ", "value": 15420.87, "change": -0.8, "change_percent": -1.15},
            {"name": "DOW", "value": 38250.14, "change": 0.5, "change_percent": 0.85},
            {"name": "Russell 2000", "value": 2150.63, "change": 2.1, "change_percent": 1.95}
        ],
        "sector_performance": [
            {"sector": "Technology", "change_percent": 1.8},
            {"sector": "Healthcare", "change_percent": 0.6},
            {"sector": "Financials", "change_percent": -0.3},
            {"sector": "Energy", "change_percent": 2.4},
            {"sector": "Consumer Discretionary", "change_percent": 1.2}
        ],
        "economic_indicators": {
            "vix": 18.45,
            "10y_treasury": 4.25,
            "dollar_index": 103.82,
            "oil_price": 82.45
        },
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/market-data/assets/{asset_class}")
async def get_asset_performance(asset_class: str) -> Dict[str, Any]:
    """Get performance data for specific asset class"""
    # Mock data generation based on asset class
    performance_data: List[Dict[str, Any]] = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        price = 100 + random.uniform(-10, 15) + (i * 0.5)
        performance_data.append({
            "date": date.isoformat(),
            "price": round(price, 2),
            "volume": random.randint(1000000, 5000000)
        })
    
    return {
        "asset_class": asset_class,
        "current_price": performance_data[-1]["price"],
        "change_24h": round(random.uniform(-3, 3), 2),
        "change_percent_24h": round(random.uniform(-5, 5), 2),
        "historical_data": performance_data,
        "volatility": round(random.uniform(10, 25), 2)
    }

# Risk analytics endpoints
@app.post("/api/risk-analytics/analyze", response_model=Dict[str, Any])
async def analyze_risk_profile(assessment: AssessmentData) -> Dict[str, Any]:
    """Generate AI-powered risk analysis using the agent coordinator"""
    try:
        global agent_coordinator
        if not agent_coordinator:
            # Fallback to direct watsonx service
            return await analyze_risk_profile_fallback(assessment)
        
        logger.info(f"Processing risk analysis via agent coordinator for user with risk tolerance {assessment.risk_tolerance}")
        
        # Convert assessment to dict for processing
        assessment_data = assessment.model_dump()
        
        # Use agent coordinator for comprehensive analysis
        results = await agent_coordinator.process_portfolio_request(assessment_data)
        
        if not results["success"]:
            logger.error(f"Agent coordinator analysis failed: {results.get('error')}")
            raise HTTPException(status_code=500, detail="Risk analysis service unavailable")
        
        # Extract risk analysis results
        risk_analysis = results.get("risk_analysis", {})
        
        return {
            "success": True,
            "analysis": risk_analysis.get("content", ""),
            "risk_blueprint": risk_analysis.get("risk_blueprint"),
            "financial_ratios": risk_analysis.get("financial_ratios"),
            "risk_score": risk_analysis.get("risk_score"),
            "volatility_target": risk_analysis.get("volatility_target"),
            "metadata": {
                "source": "agent_coordinator",
                "processing_time": results.get("processing_time", 0),
                "session_id": results.get("session_id"),
                "agent_metadata": risk_analysis.get("agent_metadata", {}),
                "workflow_metadata": results.get("workflow_metadata", {}),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent coordinator risk analysis: {str(e)}")
        # Fallback to direct service
        return await analyze_risk_profile_fallback(assessment)

async def analyze_risk_profile_fallback(assessment: AssessmentData) -> Dict[str, Any]:
    """Fallback risk analysis using direct watsonx service"""
    try:
        global watsonx_service
        if not watsonx_service:
            watsonx_service = get_watsonx_service()
        
        logger.info("Using fallback risk analysis method")
        
        # Convert assessment to dict for processing
        assessment_data = assessment.model_dump()
        
        # Generate comprehensive risk analysis using AI
        response = await watsonx_service.generate_risk_analysis(
            assessment_data, 
            analysis_type="comprehensive"
        )
        
        if not response.success:
            logger.error(f"Fallback risk analysis failed: {response.error}")
            raise HTTPException(status_code=500, detail="Risk analysis service unavailable")
        
        # Extract JSON from AI response if present
        risk_blueprint = None
        try:
            content = response.content
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end > json_start:
                    import json
                    json_content = content[json_start:json_end].strip()
                    risk_blueprint = json.loads(json_content)
        except Exception as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
        
        # Return comprehensive response
        return {
            "success": True,
            "analysis": response.content,
            "risk_blueprint": risk_blueprint,
            "metadata": {
                "source": response.source,
                "processing_time": response.processing_time,
                "model_version": response.model_version,
                "confidence": response.confidence,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fallback risk analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze risk profile")

@app.get("/api/risk-analytics/portfolio/{user_id}")
async def get_portfolio_risk_metrics(user_id: str) -> Dict[str, Any]:
    """Get comprehensive risk analytics for user portfolio"""
    if user_id not in portfolios_db:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "risk_metrics": {
            "var_95": -0.0485,
            "cvar_95": -0.0672,
            "maximum_drawdown": -0.156,
            "beta": 0.92,
            "sharpe_ratio": 1.35,
            "sortino_ratio": 1.82
        },
        "stress_test_scenarios": [
            {"scenario": "2008 Financial Crisis", "portfolio_loss": -32.4, "benchmark_loss": -37.8},
            {"scenario": "COVID-19 Pandemic", "portfolio_loss": -28.1, "benchmark_loss": -33.9},
            {"scenario": "Interest Rate Shock", "portfolio_loss": -15.2, "benchmark_loss": -18.7},
            {"scenario": "Inflation Surge", "portfolio_loss": -12.8, "benchmark_loss": -16.3}
        ],
        "monte_carlo_projections": [
            {"percentile": "5th", "value": 420000, "probability": 5},
            {"percentile": "25th", "value": 550000, "probability": 25},
            {"percentile": "50th", "value": 680000, "probability": 50},
            {"percentile": "75th", "value": 780000, "probability": 75},
            {"percentile": "95th", "value": 1200000, "probability": 95}
        ],
        "risk_alerts": [
            {
                "type": "warning",
                "title": "Increased Correlation Risk",
                "description": "US and International equity correlation has increased to 0.85",
                "severity": "Medium"
            }
        ]
    }

@app.get("/api/risk-analytics/market-conditions")
async def get_market_risk_conditions() -> Dict[str, Any]:
    """Get current market risk conditions and alerts"""
    return {
        "volatility_regime": "Normal",
        "market_stress_level": 3.2,
        "correlation_environment": "Elevated",
        "liquidity_conditions": "Good",
        "risk_indicators": {
            "vix_level": 18.45,
            "credit_spreads": 125,
            "currency_volatility": 12.8,
            "commodity_volatility": 22.1
        },
        "regime_probabilities": {
            "low_volatility": 0.25,
            "normal_volatility": 0.55,
            "high_volatility": 0.20
        }
    }

# Dashboard endpoints
@app.get("/api/dashboard/overview/{user_id}")
async def get_dashboard_overview(user_id: str) -> Dict[str, Any]:
    """Get comprehensive dashboard data for user"""
    if user_id not in portfolios_db:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = portfolios_db[user_id]
    
    return {
        "portfolio_value": 487650,
        "total_return": 8.4,
        "total_return_amount": 37650,
        "performance_data": [
            {"month": "Jan", "portfolio": 6.2, "benchmark": 4.8, "market": 5.1},
            {"month": "Feb", "portfolio": 3.1, "benchmark": 2.7, "market": 3.2},
            {"month": "Mar", "portfolio": 8.9, "benchmark": 6.4, "market": 7.1},
            {"month": "Apr", "portfolio": 2.8, "benchmark": 3.1, "market": 2.9},
            {"month": "May", "portfolio": 5.8, "benchmark": 4.1, "market": 4.5},
            {"month": "Jun", "portfolio": 4.9, "benchmark": 3.6, "market": 3.9}
        ],
        "allocation": portfolio["allocation"],
        "rebalancing_recommendations": [
            {"asset": "International Equities", "current": 18, "target": 20, "action": "Buy"},
            {"asset": "Bonds", "current": 23, "target": 20, "action": "Sell"}
        ],
        "recent_trades": [
            {"date": "2024-01-15", "action": "Buy", "asset": "VTI", "shares": 25, "price": 245.30},
            {"date": "2024-01-12", "action": "Sell", "asset": "BND", "shares": 15, "price": 78.45}
        ]
    }

@app.get("/api/dashboard/performance/{user_id}")
async def get_performance_analytics(user_id: str, period: str = "1y") -> Dict[str, Any]:
    """Get detailed performance analytics for specified period"""
    if user_id not in portfolios_db:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "period": period,
        "total_return": 8.4,
        "annualized_return": 9.2,
        "volatility": 12.8,
        "sharpe_ratio": 1.35,
        "max_drawdown": -15.6,
        "benchmark_comparison": {
            "portfolio_return": 8.4,
            "benchmark_return": 6.8,
            "alpha": 1.6,
            "beta": 0.92,
            "tracking_error": 4.2
        },
        "attribution_analysis": [
            {"factor": "Asset Allocation", "contribution": 2.1},
            {"factor": "Security Selection", "contribution": 1.8},
            {"factor": "Timing", "contribution": -0.3},
            {"factor": "Fees", "contribution": -0.2}
        ]
    }

# Utility functions
def _generate_mock_portfolio(assessment: AssessmentData) -> PortfolioRecommendation:
    """Generate a mock portfolio based on assessment data"""
    risk_level = assessment.risk_tolerance
    
    # Adjust allocations based on risk tolerance
    if risk_level <= 3:  # Conservative
        allocations = [
            PortfolioAllocation(name="US Large Cap Equities", percentage=25, amount=25000, color="#3B82F6", rationale="Stable growth"),
            PortfolioAllocation(name="International Equities", percentage=15, amount=15000, color="#10B981", rationale="Geographic diversification"),
            PortfolioAllocation(name="Bonds", percentage=40, amount=40000, color="#F59E0B", rationale="Capital preservation"),
            PortfolioAllocation(name="REITs", percentage=10, amount=10000, color="#EF4444", rationale="Income generation"),
            PortfolioAllocation(name="Cash", percentage=10, amount=10000, color="#6B7280", rationale="Liquidity buffer")
        ]
        expected_return = 6.2
        volatility = 8.5
    elif risk_level <= 6:  # Moderate
        allocations = [
            PortfolioAllocation(name="US Large Cap Equities", percentage=32, amount=32000, color="#3B82F6", rationale="Growth engine"),
            PortfolioAllocation(name="International Equities", percentage=18, amount=18000, color="#10B981", rationale="Global diversification"),
            PortfolioAllocation(name="Bonds", percentage=25, amount=25000, color="#F59E0B", rationale="Stability"),
            PortfolioAllocation(name="Small Cap Equities", percentage=8, amount=8000, color="#8B5CF6", rationale="Growth potential"),
            PortfolioAllocation(name="REITs", percentage=12, amount=12000, color="#EF4444", rationale="Real estate exposure"),
            PortfolioAllocation(name="Commodities", percentage=5, amount=5000, color="#F97316", rationale="Inflation protection")
        ]
        expected_return = 8.4
        volatility = 12.8
    else:  # Aggressive
        allocations = [
            PortfolioAllocation(name="US Large Cap Equities", percentage=40, amount=40000, color="#3B82F6", rationale="Primary growth driver"),
            PortfolioAllocation(name="International Equities", percentage=25, amount=25000, color="#10B981", rationale="Global opportunities"),
            PortfolioAllocation(name="Small Cap Equities", percentage=15, amount=15000, color="#8B5CF6", rationale="High growth potential"),
            PortfolioAllocation(name="Bonds", percentage=10, amount=10000, color="#F59E0B", rationale="Minimal stability"),
            PortfolioAllocation(name="REITs", percentage=5, amount=5000, color="#EF4444", rationale="Alternative exposure"),
            PortfolioAllocation(name="Cryptocurrency", percentage=5, amount=5000, color="#06B6D4", rationale="Emerging assets")
        ]
        expected_return = 11.2
        volatility = 18.5
    
    return PortfolioRecommendation(
        allocation=allocations,
        expected_return=expected_return,
        volatility=volatility,
        sharpe_ratio=round(expected_return / volatility, 2),
        risk_score=risk_level,
        confidence=random.randint(88, 96)
    )

# Exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

# Main execution
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )