#!/usr/bin/env python3
"""
Test script for WatsonX browser agent integration.

This script tests the browser agent with the deployed WatsonX model.
Make sure to set WATSONX_API_KEY environment variable before running.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser_agent import BrowserAgent

def test_watsonx_browser_agent():
    """Test the WatsonX browser agent integration."""
    
    # Check if API key is set
    api_key = os.getenv('WATSONX_API_KEY')
    if not api_key:
        print("❌ WATSONX_API_KEY environment variable not set!")
        print("Please set it in your .env file or environment.")
        return False
    
    print("✅ WATSONX_API_KEY found")
    
    # Initialize browser agent
    try:
        agent = BrowserAgent()
        print("✅ Browser agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize browser agent: {e}")
        return False
    
    # Test search queries
    test_queries = [
        "current stock market trends 2024",
        "Federal Reserve interest rate policy",
        "technology sector investment outlook"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing search query: '{query}'")
        try:
            result = agent.search_web(query, "google", max_results=3)
            
            if result.get("total_results", 0) > 0:
                print(f"✅ Found {result['total_results']} results")
                print(f"   Search type: {result.get('search_type', 'unknown')}")
                print(f"   WatsonX used: {result.get('search_metadata', {}).get('watsonx_used', False)}")
                
                # Show first result
                if result.get("results"):
                    first_result = result["results"][0]
                    print(f"   First result: {first_result.get('title', 'No title')}")
                    print(f"   URL: {first_result.get('url', 'No URL')}")
                    print(f"   Score: {first_result.get('relevance_score', 'No score')}")
            else:
                print("⚠️  No results found")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    # Test capabilities
    print("\n📋 Browser agent capabilities:")
    capabilities = agent.get_search_capabilities()
    for key, value in capabilities.items():
        print(f"   {key}: {value}")
    
    return True

if __name__ == "__main__":
    print("🚀 Testing WatsonX Browser Agent Integration")
    print("=" * 50)
    
    success = test_watsonx_browser_agent()
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        sys.exit(1)
