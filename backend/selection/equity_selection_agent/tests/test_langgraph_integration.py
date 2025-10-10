#!/usr/bin/env python3
"""
Test script for the new LangGraph-based QualitativeAnalysisAgent.

This script tests the integration of the QualitativeAnalysisAgent with the
existing EquityScreener to ensure proper functionality.
"""

import sys
import os
import pandas as pd
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.selector_logic import EquityScreener
from src.qualitative_agent import QualitativeAnalysisAgent, QualitativeScore

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_qualitative_agent_standalone():
    """Test the QualitativeAnalysisAgent standalone"""
    print("=== Testing QualitativeAnalysisAgent Standalone ===")
    
    config = Config()
    agent = QualitativeAnalysisAgent(config)
    
    # Enable the agent
    agent.enable_qualitative_analysis(True)
    
    # Test single company analysis
    test_ticker = "AAPL"
    test_summary = """Apple Inc. is a leading technology company that designs, develops, 
    and sells consumer electronics, computer software, and online services. The company 
    is known for its innovative products including the iPhone, iPad, Mac computers, and 
    Apple Watch. Apple has a strong competitive advantage through its integrated ecosystem 
    and strong brand loyalty. The company continues to show growth in services revenue 
    and has significant research and development investments."""
    
    test_metrics = {
        'roe': 0.25,
        'debt_to_equity': 0.8,
        'pe_ratio': 28.5
    }
    
    result = agent.analyze_company(test_ticker, test_summary, test_metrics)
    
    if result:
        print(f"✓ Analysis successful for {test_ticker}")
        print(f"  Qualitative Score: {result.qual_score:.2f}/10")
        print(f"  Management Integrity: {result.management_integrity}")
        print(f"  Competitive Advantage: {result.competitive_advantage}")
        print(f"  Growth Potential: {result.growth_potential}")
        print(f"  Assessment: {result.overall_assessment}")
        print(f"  Confidence: {result.confidence:.2f}")
    else:
        print(f"✗ Analysis failed for {test_ticker}")
        return False
    
    # Test batch analysis
    print("\n--- Testing batch analysis ---")
    companies_data = {
        "MSFT": {
            'business_summary': "Microsoft Corporation is a leading technology company that develops and licenses software, hardware, and services. Known for Windows operating system, Office productivity suite, and Azure cloud services. Strong competitive advantages in enterprise software and growing cloud business.",
            'roe': 0.32,
            'debt_to_equity': 0.45,
            'pe_ratio': 24.2
        },
        "GOOGL": {
            'business_summary': "Alphabet Inc. operates Google search engine and advertising platform. Dominant market position in online search and digital advertising. Significant investments in artificial intelligence, cloud computing, and autonomous vehicles.",
            'roe': 0.19,
            'debt_to_equity': 0.15,
            'pe_ratio': 22.8
        }
    }
    
    batch_results = agent.batch_analyze(companies_data)
    
    if len(batch_results) == 2:
        print(f"✓ Batch analysis successful - analyzed {len(batch_results)} companies")
        for ticker, result in batch_results.items():
            print(f"  {ticker}: Score {result.qual_score:.2f}/10")
    else:
        print(f"✗ Batch analysis failed - expected 2 results, got {len(batch_results)}")
        return False
    
    return True


def test_equity_screener_integration():
    """Test the integration with EquityScreener"""
    print("\n=== Testing EquityScreener Integration ===")
    
    config = Config()
    screener = EquityScreener(config)  # No LLM passed, will use mock mode
    
    # Enable qualitative analysis
    screener.enable_qualitative_analysis(True)
    
    # Create mock data for testing
    test_data = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'roe': [0.25, 0.32, 0.19],
        'debt_to_equity': [0.8, 0.45, 0.15],
        'pe_ratio': [28.5, 24.2, 22.8],
        'sector': ['Technology', 'Technology', 'Technology'],
        'region': ['US', 'US', 'US']
    })
    
    # Mock fundamental data with business summaries
    fundamental_data = {
        'AAPL': {
            'business_summary': "Apple Inc. is a leading technology company known for innovative consumer electronics and strong brand loyalty.",
            'roe': 0.25,
            'debt_to_equity': 0.8,
            'pe_ratio': 28.5
        },
        'MSFT': {
            'business_summary': "Microsoft Corporation is a leading technology company with strong competitive advantages in enterprise software.",
            'roe': 0.32,
            'debt_to_equity': 0.45,
            'pe_ratio': 24.2
        },
        'GOOGL': {
            'business_summary': "Alphabet Inc. operates Google with dominant market position in online search and digital advertising.",
            'roe': 0.19,
            'debt_to_equity': 0.15,
            'pe_ratio': 22.8
        }
    }
    
    # Test add_qualitative_scores method
    try:
        enhanced_data = screener.add_qualitative_scores(test_data, fundamental_data)
        
        required_columns = ['qual_score', 'qual_confidence', 'qual_assessment']
        missing_columns = [col for col in required_columns if col not in enhanced_data.columns]
        
        if not missing_columns:
            print("✓ Qualitative scores successfully added to DataFrame")
            print(f"  Added columns: {required_columns}")
            
            # Check if scores are reasonable
            qual_scores = enhanced_data['qual_score'].tolist()
            if all(0 <= score <= 10 for score in qual_scores):
                print(f"✓ All qualitative scores are in valid range (0-10): {qual_scores}")
            else:
                print(f"✗ Some qualitative scores are out of range: {qual_scores}")
                return False
                
        else:
            print(f"✗ Missing expected columns: {missing_columns}")
            return False
            
    except Exception as e:
        print(f"✗ Error in add_qualitative_scores: {e}")
        return False
    
    return True


def test_disabled_mode():
    """Test that the agent works correctly when disabled"""
    print("\n=== Testing Disabled Mode ===")
    
    config = Config()
    agent = QualitativeAnalysisAgent(config)
    
    # Keep agent disabled (default)
    result = agent.analyze_company("TEST", "Some business summary", {'roe': 0.15})
    
    if result is None:
        print("✓ Agent correctly returns None when disabled")
    else:
        print("✗ Agent should return None when disabled")
        return False
    
    batch_results = agent.batch_analyze({"TEST": {'business_summary': "Test", 'roe': 0.15}})
    
    if len(batch_results) == 0:
        print("✓ Batch analysis correctly returns empty dict when disabled")
    else:
        print("✗ Batch analysis should return empty dict when disabled")
        return False
    
    return True


def main():
    """Run all tests"""
    print("Testing LangGraph-based QualitativeAnalysisAgent")
    print("=" * 50)
    
    tests = [
        test_disabled_mode,
        test_qualitative_agent_standalone,
        test_equity_screener_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_func.__name__} PASSED")
            else:
                print(f"✗ {test_func.__name__} FAILED")
        except Exception as e:
            print(f"✗ {test_func.__name__} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The LangGraph integration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)