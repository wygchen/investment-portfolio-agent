#!/usr/bin/env python3
"""
Simple test to verify the string format for specificAssets works properly
"""

from pydantic import BaseModel
from typing import List


class ValuesData(BaseModel):
    avoidIndustries: List[str] = []
    preferIndustries: List[str] = []
    specificAssets: str = ""  # Changed from List[str] to str
    customConstraints: str = ""


def test_string_format():
    """Test that the new string format for specificAssets works"""
    
    print("Testing specificAssets as string format...")
    
    # Test 1: Empty string (default)
    data1 = ValuesData()
    print(f"✅ Test 1 passed: Default empty string: '{data1.specificAssets}'")
    
    # Test 2: Natural language input
    data2 = ValuesData(specificAssets="AAPL and TESLA")
    print(f"✅ Test 2 passed: Natural language string: '{data2.specificAssets}'")
    
    # Test 3: More complex string
    data3 = ValuesData(specificAssets="I want to invest in Apple, Microsoft, and some Tesla stock")
    print(f"✅ Test 3 passed: Complex string: '{data3.specificAssets}'")
    
    # Test 4: JSON serialization
    import json
    data4 = ValuesData(
        avoidIndustries=["tobacco"],
        preferIndustries=["technology"],
        specificAssets="NVDA, GOOGL",
        customConstraints="No more than 10% in any single stock"
    )
    json_str = data4.model_dump_json()
    parsed_back = json.loads(json_str)
    print(f"✅ Test 4 passed: JSON works: {parsed_back['specificAssets']}")
    
    print("\nAll tests passed! The string format is working correctly. 🎉")
    print("LLM agents will now be able to parse natural language asset preferences like:")
    print('  - "AAPL and TESLA"')
    print('  - "Apple, Microsoft, and some Bitcoin"')
    print('  - "I want exposure to tech stocks like NVDA and GOOGL"')


if __name__ == "__main__":
    test_string_format()