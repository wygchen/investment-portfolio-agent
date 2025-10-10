#!/usr/bin/env python3
"""
Quick test to verify the string format for specificAssets works properly
"""

import json
from pydantic import ValidationError
from main import ValuesData


def test_string_format():
    """Test that the new string format for specificAssets works"""
    
    print("Testing specificAssets as string format...")
    
    # Test 1: Empty string (default)
    try:
        data1 = ValuesData(
            goals=[],
            horizon="",
            riskTolerance="",
            income="",
            liabilities="",
            liquidity="",
            avoidIndustries=[],
            preferIndustries=[],
            specificAssets="",  # Empty string
            customConstraints=""
        )
        print("✅ Test 1 passed: Empty string works")
    except ValidationError as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Natural language input
    try:
        data2 = ValuesData(
            goals=[],
            horizon="",
            riskTolerance="",
            income="",
            liabilities="",
            liquidity="",
            avoidIndustries=[],
            preferIndustries=[],
            specificAssets="AAPL and TESLA",  # Natural language string
            customConstraints=""
        )
        print("✅ Test 2 passed: Natural language string works")
        print(f"   specificAssets value: {data2.specificAssets}")
    except ValidationError as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: More complex string
    try:
        data3 = ValuesData(
            goals=[],
            horizon="",
            riskTolerance="",
            income="",
            liabilities="",
            liquidity="",
            avoidIndustries=[],
            preferIndustries=[],
            specificAssets="I want to invest in Apple, Microsoft, and some Tesla stock",
            customConstraints=""
        )
        print("✅ Test 3 passed: Complex natural language string works")
        print(f"   specificAssets value: {data3.specificAssets}")
    except ValidationError as e:
        print(f"❌ Test 3 failed: {e}")

    # Test 4: JSON serialization works
    try:
        data4 = ValuesData(
            goals=[],
            horizon="",
            riskTolerance="",
            income="",
            liabilities="",
            liquidity="",
            avoidIndustries=["tobacco"],
            preferIndustries=["technology"],
            specificAssets="NVDA, GOOGL",
            customConstraints=""
        )
        json_str = data4.model_dump_json()
        parsed_back = json.loads(json_str)
        print("✅ Test 4 passed: JSON serialization works")
        print(f"   JSON: {json_str}")
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")


if __name__ == "__main__":
    test_string_format()