import os
import pytest
import logging
from risk_analytics_agent.risk_analytivs_agent import RiskAnalyticsAgent
from base_agent import AgentContext
from services.watsonx_service import create_watsonx_llm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
async def risk_agent():
    """Create a test instance of RiskAnalyticsAgent."""
    llm = create_watsonx_llm()
    return RiskAnalyticsAgent(llm=llm)

@pytest.mark.asyncio
async def test_risk_analytics_agent_basic(risk_agent):
    """Test basic functionality of RiskAnalyticsAgent."""
    # Sample user assessment data
    test_assessment = {
        "age": 35,
        "income": 100000,
        "net_worth": 250000,
        "dependents": 2,
        "time_horizon": 15,
        "target_amount": 1000000,
        "monthly_contribution": 1000,
        "risk_tolerance": 7
    }
    
    context = AgentContext(user_assessment=test_assessment)
    
    try:
        logger.info("Starting risk analytics agent test")
        result = await risk_agent.execute_agent_logic(context)
        
        # Verify the structure of the response
        assert "content" in result
        assert "structured_data" in result
        assert "risk_blueprint" in result["structured_data"]
        
        # Log the results
        logger.info("Risk assessment completed successfully")
        logger.info("Risk score: %s", result["structured_data"]["risk_score"])
        logger.info("Volatility target: %s", result["structured_data"]["volatility_target"])
        logger.info("Risk level summary: %s", 
                   result["structured_data"]["risk_blueprint"]["risk_level_summary"])
        
        return result
        
    except Exception as e:
        logger.error("Error in risk analytics test: %s", str(e))
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])