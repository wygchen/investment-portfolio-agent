"""Integration test for RiskAnalyticsAgent with WatsonX LLM."""

import asyncio
import pytest
from backend.risk_analytics_agent.risk_analytivs_agent import RiskAnalyticsAgent
from backend.watsonx_utils import create_watsonx_llm


@pytest.mark.asyncio
async def test_risk_analytics_agent_integration():
    """Test RiskAnalyticsAgent with real WatsonX LLM."""
    
    # Create WatsonX LLM instance
    llm = create_watsonx_llm(
        model_id="ibm/granite-3-2-8b-instruct",
        max_tokens=1000,
        temperature=0.7
    )
    
    # Create RiskAnalyticsAgent instance
    agent = RiskAnalyticsAgent(llm=llm)
    
    # Test data
    test_context = type('AgentContext', (), {
        'user_assessment': {
            'age': 35,
            'income': 100000,
            'net_worth': 500000,
            'dependents': 2,
            'time_horizon': 15,
            'risk_tolerance': 7,
            'target_amount': 1000000,
            'monthly_contribution': 2000,
        }
    })()
    
    # Execute agent logic
    result = await agent.execute_agent_logic(test_context)
    
    # Validate response structure
    assert 'content' in result
    assert 'structured_data' in result
    assert 'risk_blueprint' in result['structured_data']
    
    # Validate risk components
    blueprint = result['structured_data']['risk_blueprint']
    assert 'risk_capacity' in blueprint
    assert 'risk_tolerance' in blueprint
    assert 'risk_requirement' in blueprint
    assert 'volatility_target' in blueprint
    
    print("Test Results:")
    print(f"Risk Level Summary: {blueprint['risk_level_summary']}")
    print(f"Volatility Target: {blueprint['volatility_target']}")
    print(f"Risk Score: {blueprint['risk_score']}")
    

if __name__ == '__main__':
    asyncio.run(test_risk_analytics_agent_integration())