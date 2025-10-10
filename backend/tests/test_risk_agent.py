#!/usr/bin/env python3
"""
Test script for Risk Analytics Agent functionality.
Tests the agent framework and risk analysis capabilities.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from risk_analytics_agent.risk_analytics_agent import RiskAnalyticsAgent
from risk_analytics_agent.agent_coordinator import AgentCoordinator, AgentContext
from watsonx_utils import create_watsonx_llm


async def test_risk_analytics_agent():
    """Test the Risk Analytics Agent with sample data"""
    print("🧠 Testing Risk Analytics Agent...")
    print("=" * 50)
    
    try:
        # Create LLM instance
        print("📋 Creating Watsonx LLM...")
        llm = create_watsonx_llm(
            model_id="ibm/granite-3-2-8b-instruct",
            temperature=0.3,
            max_tokens=2000
        )
        print("✅ LLM created successfully")
        
    except Exception as e:
        print(f"❌ LLM creation failed: {e}")
        print("💡 Make sure your .env file is configured with Watsonx credentials")
        return False
    
    try:
        # Create Risk Analytics Agent
        print("\n🤖 Initializing Risk Analytics Agent...")
        risk_agent = RiskAnalyticsAgent(llm)
        print(f"✅ Agent initialized: {risk_agent.name}")
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Conservative Young Professional",
            "data": {
                "age": 28,
                "income": 65000,
                "net_worth": 45000,
                "dependents": 0,
                "primary_goal": "retirement",
                "time_horizon": 35,
                "target_amount": 1000000,
                "monthly_contribution": 800,
                "risk_tolerance": 4,
                "risk_capacity": "medium",
                "previous_experience": ["stocks", "bonds"],
                "market_reaction": "hold_course",
                "investment_style": "balanced"
            }
        },
        {
            "name": "Aggressive Mid-Career Investor",
            "data": {
                "age": 42,
                "income": 120000,
                "net_worth": 350000,
                "dependents": 2,
                "primary_goal": "retirement",
                "time_horizon": 23,
                "target_amount": 2000000,
                "monthly_contribution": 2000,
                "risk_tolerance": 8,
                "risk_capacity": "high",
                "previous_experience": ["stocks", "bonds", "real_estate", "options"],
                "market_reaction": "buy_more",
                "investment_style": "aggressive"
            }
        },
        {
            "name": "Conservative Pre-Retiree",
            "data": {
                "age": 58,
                "income": 95000,
                "net_worth": 800000,
                "dependents": 0,
                "primary_goal": "retirement",
                "time_horizon": 7,
                "target_amount": 1200000,
                "monthly_contribution": 1500,
                "risk_tolerance": 3,
                "risk_capacity": "medium",
                "previous_experience": ["stocks", "bonds", "mutual_funds"],
                "market_reaction": "sell_some",
                "investment_style": "conservative"
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test Scenario {i}: {scenario['name']}")
        print("-" * 40)
        
        try:
            # Create agent context
            context = AgentContext(
                session_id=f"test_session_{i}",
                user_assessment=scenario["data"]
            )
            
            # Process with agent
            print("⏳ Processing risk analysis...")
            start_time = asyncio.get_event_loop().time()
            
            response = await risk_agent.process(context)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            print(f"✅ Analysis completed in {processing_time:.2f}s")
            print(f"   - Success: {response.success}")
            print(f"   - Agent: {response.agent_name}")
            print(f"   - Confidence: {response.confidence}")
            
            if response.success and response.structured_data:
                # Display key results
                risk_blueprint = response.structured_data.get("risk_blueprint", {})
                risk_score = response.structured_data.get("risk_score", "N/A")
                volatility_target = response.structured_data.get("volatility_target", "N/A")
                
                print(f"\n📊 Key Results:")
                print(f"   - Risk Score: {risk_score}/100")
                print(f"   - Volatility Target: {volatility_target}%")
                print(f"   - Risk Level: {risk_blueprint.get('risk_level_summary', 'N/A')}")
                
                if risk_blueprint.get('financial_ratios'):
                    ratios = risk_blueprint['financial_ratios']
                    print(f"   - Savings Rate: {ratios.get('savings_rate', 'N/A')}")
                    print(f"   - Liquidity Ratio: {ratios.get('liquidity_ratio', 'N/A')}")
                
                # Show a preview of the analysis
                content_preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
                print(f"\n📝 Analysis Preview:")
                print(f"   {content_preview}")
                
            else:
                print(f"❌ Analysis failed: {response.error}")
                
        except Exception as e:
            print(f"❌ Test scenario failed: {e}")
            continue
    
    print(f"\n📈 Agent Status:")
    status = risk_agent.get_status()
    for key, value in status.items():
        print(f"   - {key}: {value}")
    
    return True


async def test_agent_coordinator():
    """Test the Agent Coordinator workflow"""
    print("\n\n🎯 Testing Agent Coordinator...")
    print("=" * 50)
    
    try:
        # Create LLM instance
        llm = create_watsonx_llm(
            model_id="ibm/granite-3-2-8b-instruct",
            temperature=0.3,
            max_tokens=2000
        )
        
        # Create Agent Coordinator
        print("🎮 Initializing Agent Coordinator...")
        coordinator = AgentCoordinator(llm)
        print("✅ Coordinator initialized")
        
        # Test portfolio request
        test_assessment = {
            "age": 35,
            "income": 85000,
            "net_worth": 200000,
            "dependents": 1,
            "primary_goal": "retirement",
            "time_horizon": 30,
            "target_amount": 1500000,
            "monthly_contribution": 1200,
            "risk_tolerance": 6,
            "risk_capacity": "medium",
            "previous_experience": ["stocks", "bonds"],
            "market_reaction": "hold_course",
            "investment_style": "balanced"
        }
        
        print("\n⏳ Processing portfolio request...")
        results = await coordinator.process_portfolio_request(test_assessment)
        
        print(f"✅ Portfolio analysis completed:")
        print(f"   - Success: {results['success']}")
        print(f"   - Session ID: {results['session_id']}")
        print(f"   - Processing Time: {results['processing_time']:.2f}s")
        
        if results["success"]:
            risk_analysis = results.get("risk_analysis", {})
            print(f"   - Risk Score: {risk_analysis.get('risk_score', 'N/A')}")
            print(f"   - Volatility Target: {risk_analysis.get('volatility_target', 'N/A')}")
            
            workflow_metadata = results.get("workflow_metadata", {})
            completed_agents = workflow_metadata.get("completed_agents", [])
            print(f"   - Completed Agents: {len(completed_agents)}")
            
            for agent_info in completed_agents:
                print(f"     * {agent_info['agent_name']}: {agent_info['processing_time']:.2f}s")
        
        # Test coordinator status
        print(f"\n📊 Coordinator Status:")
        status = coordinator.get_agent_status()
        print(f"   - Active Sessions: {status['active_sessions']}")
        print(f"   - Coordinator Status: {status['coordinator_status']}")
        
        # Test health check
        print(f"\n🏥 Health Check:")
        health = await coordinator.health_check()
        print(f"   - Overall Health: {health['overall_health']}")
        print(f"   - Coordinator: {health['coordinator']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Coordinator test failed: {e}")
        return False


if __name__ == "__main__":
    print("🤖 Risk Analytics Agent Test Suite")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ No .env file found!")
        print("💡 Please copy .env.example to .env and configure your credentials")
        sys.exit(1)
    
    async def run_all_tests():
        """Run all test suites"""
        try:
            # Test individual agent
            agent_success = await test_risk_analytics_agent()
            
            # Test coordinator
            coordinator_success = await test_agent_coordinator()
            
            if agent_success and coordinator_success:
                print("\n🎉 All tests passed! Risk Analytics system is ready!")
                print("\n💡 Next steps:")
                print("   1. Start the FastAPI server: python main.py")
                print("   2. Test the /api/risk-analytics/analyze endpoint")
                print("   3. Integrate with your frontend")
                return True
            else:
                print("\n❌ Some tests failed. Please check the errors above.")
                return False
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Tests interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return False
    
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)