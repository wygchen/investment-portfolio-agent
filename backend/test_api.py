#!/usr/bin/env python3
"""
Test script for PortfolioAI API Assessment Endpoint
This script tests the /api/assessment endpoint to ensure it can receive data properly.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
ASSESSMENT_ENDPOINT = f"{API_BASE_URL}/api/assessment"

# Sample assessment data that matches the frontend format
sample_assessment: Dict[str, Any] = {
    "age": 35,
    "income": 75000,
    "net_worth": 150000,
    "dependents": 2,
    "primary_goal": "retirement",
    "time_horizon": 25,
    "target_amount": 1000000,
    "monthly_contribution": 2000,
    "risk_tolerance": 6,
    "risk_capacity": "moderate",
    "previous_experience": ["stocks", "bonds", "mutual_funds"],
    "market_reaction": "hold_steady",
    "investment_style": "long_term",
    "rebalancing_frequency": "quarterly",
    "esg_preferences": True,
    "special_circumstances": "Planning for children's education"
}

def test_health_endpoint():
    """Test the health endpoint to ensure API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed:")
            print(f"   Status: {data.get('status')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the FastAPI server is running.")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_assessment_submission():
    """Test submitting assessment data to the API"""
    try:
        print("\n📤 Testing assessment submission...")
        print(f"   Endpoint: {ASSESSMENT_ENDPOINT}")
        print(f"   Data: {json.dumps(sample_assessment, indent=2)}")
        
        response = requests.post(
            ASSESSMENT_ENDPOINT,
            json=sample_assessment,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Assessment submission successful:")
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Assessment ID: {data.get('assessment_id')}")
            return data.get('user_id')
        else:
            print(f"❌ Assessment submission failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Assessment submission error: {e}")
        return None

def test_assessment_retrieval(user_id: Optional[str]) -> bool:
    """Test retrieving assessment data from the API"""
    if not user_id:
        print("⏭️  Skipping assessment retrieval (no user ID)")
        return False
        
    try:
        print(f"\n📥 Testing assessment retrieval for user: {user_id}")
        response = requests.get(f"{API_BASE_URL}/api/assessment/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Assessment retrieval successful:")
            print(f"   Age: {data.get('age')}")
            print(f"   Income: ${data.get('income'):,}")
            print(f"   Risk Tolerance: {data.get('risk_tolerance')}/10")
            print(f"   Primary Goal: {data.get('primary_goal')}")
            return True
        else:
            print(f"❌ Assessment retrieval failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Assessment retrieval error: {e}")
        return False

def test_portfolio_generation():
    """Test portfolio generation with the sample assessment data"""
    try:
        print("\n🤖 Testing portfolio generation...")
        response = requests.post(
            f"{API_BASE_URL}/api/portfolio/generate",
            json=sample_assessment,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Portfolio generation successful:")
            print(f"   Expected Return: {data.get('expected_return')}%")
            print(f"   Volatility: {data.get('volatility')}%")
            print(f"   Sharpe Ratio: {data.get('sharpe_ratio')}")
            print(f"   Confidence: {data.get('confidence')}%")
            print(f"   Allocations: {len(data.get('allocation', []))} assets")
            
            # Show top 3 allocations
            allocations = data.get('allocation', [])
            if allocations:
                print("   Top allocations:")
                for i, allocation in enumerate(sorted(allocations, key=lambda x: x['percentage'], reverse=True)[:3]):
                    print(f"     {i+1}. {allocation['name']}: {allocation['percentage']}%")
            
            return True
        else:
            print(f"❌ Portfolio generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Portfolio generation error: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 PortfolioAI API Test Suite")
    print("=" * 50)
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Health check
    if not test_health_endpoint():
        print("\n❌ API is not accessible. Please ensure:")
        print("   1. FastAPI server is running: python start_server.py")
        print("   2. Server is running on http://127.0.0.1:8000")
        print("   3. No firewall blocking the connection")
        sys.exit(1)
    
    # Test 2: Assessment submission
    user_id = test_assessment_submission()
    
    # Test 3: Assessment retrieval
    test_assessment_retrieval(user_id)
    
    # Test 4: Portfolio generation
    test_portfolio_generation()
    
    print("\n" + "=" * 50)
    print("✅ API testing completed!")
    print("\nTo test the frontend integration:")
    print("1. Start the Next.js frontend: npm run dev")
    print("2. Navigate to http://localhost:3000/assessment")
    print("3. Complete the assessment form")
    print("4. Check if data is submitted to the backend")

if __name__ == "__main__":
    main()