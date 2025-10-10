#!/usr/bin/env python3
"""
Test script for the new streaming API endpoints
"""

import requests
import json
import time
from datetime import datetime

# Test data matching frontend UserProfile structure
test_assessment_data = {
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

def test_validate_assessment():
    """Test the validation endpoint"""
    print("="*60)
    print("TESTING VALIDATE ASSESSMENT ENDPOINT")
    print("="*60)
    
    try:
        # Make API call to validate assessment
        response = requests.post(
            "http://localhost:8000/api/validate-assessment",
            json=test_assessment_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Validation passed successfully!")
        else:
            print("❌ Validation failed!")
            
    except Exception as e:
        print(f"❌ Error testing validation: {str(e)}")

def test_streaming_report():
    """Test the streaming report endpoint"""
    print("\n" + "="*60)
    print("TESTING STREAMING REPORT ENDPOINT")
    print("="*60)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/generate-report/stream",
            json=test_assessment_data,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        print(f"Status Code: {response.status_code}")
        print("Streaming events:")
        print("-" * 40)
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            event_data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            event = event_data.get('event', 'unknown')
                            progress = event_data.get('data', {}).get('progress', 0)
                            message = event_data.get('data', {}).get('message', '')
                            timestamp = event_data.get('timestamp', '')
                            
                            print(f"[{timestamp}] {event} ({progress}%): {message}")
                            
                            # If final report is complete, show summary
                            if event == 'final_report_complete':
                                final_report = event_data.get('data', {}).get('final_report', {})
                                print(f"\n📊 FINAL REPORT SUMMARY:")
                                print(f"Title: {final_report.get('report_title', 'N/A')}")
                                print(f"Status: {event_data.get('data', {}).get('status', 'N/A')}")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON: {line_str}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error testing streaming: {str(e)}")

def test_invalid_data():
    """Test validation with invalid data"""
    print("\n" + "="*60)
    print("TESTING VALIDATION WITH INVALID DATA")
    print("="*60)
    
    invalid_data = {
        "goals": [],  # Empty goals
        "timeHorizon": -5,  # Invalid time horizon
        "riskTolerance": "",  # Empty risk tolerance
        "annualIncome": -1000,  # Negative income
        "monthlySavings": -500,  # Negative savings
        "totalDebt": -1000,  # Negative debt
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/validate-assessment",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print("✅ Validation correctly rejected invalid data!")
        else:
            print("❌ Validation should have failed!")
            
    except Exception as e:
        print(f"❌ Error testing invalid data: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing Streaming API Endpoints")
    print("🔗 Make sure backend server is running on http://localhost:8000")
    print(f"🕐 Test started at: {datetime.now().isoformat()}")
    
    # Test 1: Validate good data
    test_validate_assessment()
    
    # Test 2: Test streaming
    test_streaming_report()
    
    # Test 3: Validate bad data
    test_invalid_data()
    
    print(f"\n🏁 Testing completed at: {datetime.now().isoformat()}")