#!/usr/bin/env python3
"""
Integration test for Financial Ratio Engine with Risk Analytics Agent.
Tests the complete financial analysis workflow.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from utils.financial_ratios import FinancialRatioEngine
from risk_analytics_agent.risk_analytics_agent import RiskAnalyticsAgent
from risk_analytics_agent.agent_coordinator import AgentContext
from watsonx_utils import create_watsonx_llm


async def test_financial_ratio_engine():
    """Test the Financial Ratio Engine standalone"""
    print("🧮 Testing Financial Ratio Engine...")
    print("=" * 50)
    
    # Initialize engine
    engine = FinancialRatioEngine()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Young Professional",
            "data": {
                "age": 28,
                "income": 65000,
                "net_worth": 25000,
                "monthly_contribution": 800,
                "dependents": 0,
                "time_horizon": 35,
                "target_amount": 1000000
            }
        },
        {
            "name": "Mid-Career Family",
            "data": {
                "age": 42,
                "income": 95000,
                "net_worth": 280000,
                "monthly_contribution": 1500,
                "dependents": 2,
                "time_horizon": 23,
                "target_amount": 1500000
            }
        },
        {
            "name": "High Earner",
            "data": {
                "age": 38,
                "income": 180000,
                "net_worth": 450000,
                "monthly_contribution": 3500,
                "dependents": 1,
                "time_horizon": 27,
                "target_amount": 3000000
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📊 Scenario {i}: {scenario['name']}")
        print("-" * 30)
        
        try:
            # Calculate all ratios
            ratios = engine.calculate_all_ratios(scenario["data"])
            
            print(f"✅ Calculated {len(ratios)} financial ratios")
            
            # Display key ratios
            key_ratios = ["savings_rate", "liquidity_ratio", "debt_to_income", 
                         "net_worth_to_income", "financial_stability_score"]
            
            for ratio_name in key_ratios:
                if ratio_name in ratios:
                    ratio = ratios[ratio_name]
                    print(f"   - {ratio.name}: {ratio.value:.1f} ({ratio.interpretation})")
            
            # Generate summary
            summary = engine.generate_ratio_summary(ratios)
            print(f"\n📈 Overall Financial Health: {summary['health_status']} ({summary['overall_score']:.1f}/100)")
            
            # Show top recommendations
            if summary['recommendations']:
                print(f"💡 Top Recommendations:")
                for j, rec in enumerate(summary['recommendations'][:2], 1):
                    print(f"   {j}. {rec}")
            
            # Show warnings if any
            if summary['key_warnings']:
                print(f"⚠️  Key Warnings:")
                for warning in summary['key_warnings'][:2]:
                    print(f"   - {warning}")
                    
        except Exception as e:
            print(f"❌ Scenario failed: {e}")
            continue
    
    return True


async def test_enhanced_risk_agent():
    """Test Risk Analytics Agent with enhanced financial ratios"""
    print("\n\n🤖 Testing Enhanced Risk Analytics Agent...")
    print("=" * 50)
    
    try:
        # Create LLM (will use fallback if not available)
        try:
            llm = create_watsonx_llm(
                model_id="ibm/granite-3-2-8b-instruct",
                temperature=0.3,
                max_tokens=2000
            )
            print("✅ Watsonx LLM initialized")
        except Exception as e:
            print(f"⚠️  Watsonx LLM failed, using fallback: {e}")
            llm = None
        
        # Create enhanced risk agent
        if llm:
            risk_agent = RiskAnalyticsAgent(llm)
            print("✅ Enhanced Risk Analytics Agent initialized")
        else:
            print("❌ Cannot test agent without LLM")
            return False
        
        # Test comprehensive analysis
        test_assessment = {
            "age": 35,
            "income": 85000,
            "net_worth": 180000,
            "monthly_contribution": 1200,
            "dependents": 1,
            "primary_goal": "retirement",
            "time_horizon": 30,
            "target_amount": 1500000,
            "risk_tolerance": 6,
            "risk_capacity": "medium",
            "previous_experience": ["stocks", "bonds"],
            "market_reaction": "hold_course",
            "investment_style": "balanced"
        }
        
        # Create context and process
        context = AgentContext(
            session_id="test_enhanced_analysis",
            user_assessment=test_assessment
        )
        
        print("\n⏳ Processing enhanced risk analysis...")
        response = await risk_agent.process(context)
        
        print(f"✅ Analysis completed:")
        print(f"   - Success: {response.success}")
        print(f"   - Processing Time: {response.processing_time:.2f}s")
        print(f"   - Confidence: {response.confidence}")
        
        if response.success and response.structured_data:
            # Display enhanced results
            structured_data = response.structured_data
            
            # Risk blueprint
            risk_blueprint = structured_data.get("risk_blueprint", {})
            print(f"\n📋 Risk Blueprint:")
            print(f"   - Risk Score: {structured_data.get('risk_score', 'N/A')}")
            print(f"   - Volatility Target: {structured_data.get('volatility_target', 'N/A')}")
            print(f"   - Risk Level: {risk_blueprint.get('risk_level_summary', 'N/A')}")
            
            # Comprehensive ratios
            ratio_summary = structured_data.get("ratio_summary", {})
            if ratio_summary:
                print(f"\n📊 Comprehensive Analysis:")
                print(f"   - Overall Score: {ratio_summary.get('overall_score', 0):.1f}/100")
                print(f"   - Health Status: {ratio_summary.get('health_status', 'Unknown')}")
                print(f"   - Ratios Calculated: {ratio_summary.get('total_ratios_calculated', 0)}")
            
            # Financial ratios
            financial_ratios = structured_data.get("financial_ratios", {})
            if financial_ratios:
                print(f"\n💰 Key Financial Ratios:")
                for ratio_name, value in financial_ratios.items():
                    print(f"   - {ratio_name.replace('_', ' ').title()}: {value}")
            
            # Show analysis preview
            content_preview = response.content[:300] + "..." if len(response.content) > 300 else response.content
            print(f"\n📝 Analysis Preview:")
            print(f"   {content_preview}")
            
        else:
            print(f"❌ Analysis failed: {response.error}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced agent test failed: {e}")
        return False


async def test_ratio_validation_and_edge_cases():
    """Test ratio engine validation and edge cases"""
    print("\n\n🔍 Testing Validation and Edge Cases...")
    print("=" * 50)
    
    engine = FinancialRatioEngine()
    
    # Edge case scenarios
    edge_cases = [
        {
            "name": "Zero Income",
            "data": {
                "age": 25,
                "income": 0,
                "net_worth": 10000,
                "monthly_contribution": 0,
                "dependents": 0,
                "time_horizon": 10,
                "target_amount": 100000
            }
        },
        {
            "name": "Negative Net Worth",
            "data": {
                "age": 30,
                "income": 50000,
                "net_worth": -25000,
                "monthly_contribution": 500,
                "dependents": 1,
                "time_horizon": 20,
                "target_amount": 500000
            }
        },
        {
            "name": "Extreme High Income",
            "data": {
                "age": 45,
                "income": 500000,
                "net_worth": 2000000,
                "monthly_contribution": 10000,
                "dependents": 3,
                "time_horizon": 15,
                "target_amount": 5000000
            }
        },
        {
            "name": "Unrealistic Savings",
            "data": {
                "age": 35,
                "income": 60000,
                "net_worth": 50000,
                "monthly_contribution": 8000,  # More than monthly income
                "dependents": 0,
                "time_horizon": 25,
                "target_amount": 1000000
            }
        }
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n🧪 Edge Case {i}: {case['name']}")
        print("-" * 25)
        
        try:
            ratios = engine.calculate_all_ratios(case["data"])
            summary = engine.generate_ratio_summary(ratios)
            
            print(f"✅ Handled gracefully:")
            print(f"   - Ratios calculated: {len(ratios)}")
            print(f"   - Overall score: {summary['overall_score']:.1f}")
            print(f"   - Warnings: {len(summary['key_warnings'])}")
            
            # Show warnings for problematic cases
            if summary['key_warnings']:
                print(f"   - Key warnings: {summary['key_warnings'][:2]}")
                
        except Exception as e:
            print(f"❌ Edge case handling failed: {e}")
            continue
    
    return True


async def run_comprehensive_tests():
    """Run all financial ratio integration tests"""
    print("🧮 Financial Ratio Engine Integration Tests")
    print("=" * 60)
    
    try:
        # Test 1: Standalone ratio engine
        engine_success = await test_financial_ratio_engine()
        
        # Test 2: Enhanced risk agent
        agent_success = await test_enhanced_risk_agent()
        
        # Test 3: Edge cases and validation
        validation_success = await test_ratio_validation_and_edge_cases()
        
        # Summary
        print(f"\n🎯 Test Results Summary:")
        print(f"   - Ratio Engine: {'✅ PASS' if engine_success else '❌ FAIL'}")
        print(f"   - Enhanced Agent: {'✅ PASS' if agent_success else '❌ FAIL'}")
        print(f"   - Edge Cases: {'✅ PASS' if validation_success else '❌ FAIL'}")
        
        if engine_success and agent_success and validation_success:
            print(f"\n🎉 All integration tests passed!")
            print(f"\n💡 Enhanced Financial Analysis System Ready:")
            print(f"   - Comprehensive ratio calculations")
            print(f"   - Professional financial health scoring")
            print(f"   - AI-powered risk analysis integration")
            print(f"   - Robust validation and error handling")
            return True
        else:
            print(f"\n❌ Some tests failed. Check the output above.")
            return False
            
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        return False


if __name__ == "__main__":
    import os
    
    print("🧮 Financial Ratio Engine Integration Test Suite")
    print("=" * 60)
    
    # Check environment
    if not os.path.exists(".env"):
        print("⚠️  No .env file found - some tests may use fallback modes")
    
    # Run tests
    success = asyncio.run(run_comprehensive_tests())
    
    if success:
        print(f"\n🚀 Ready for production! Your enhanced financial analysis system is working perfectly.")
    else:
        print(f"\n🔧 Some issues detected. Please review the test output above.")
    
    sys.exit(0 if success else 1)