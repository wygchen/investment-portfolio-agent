#!/usr/bin/env python3
"""
Test script to verify compatibility between main_agent.py and selection_agent.py

This script tests the interface compatibility without running the full workflow.
"""

import sys
import os

# Add the backend directory to Python path (parent of current directory)
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

# Also add the selection directory to path
selection_dir = os.path.dirname(__file__)
sys.path.insert(0, selection_dir)

def test_selection_agent_compatibility():
    """Test that selection_agent.py returns data in format expected by main_agent.py"""
    
    print("Testing selection agent compatibility...")
    print(f"Backend directory: {backend_dir}")
    print(f"Selection directory: {selection_dir}")
    
    # Import the selection agent
    try:
        from selection_agent import run_selection_agent
        print("✅ Successfully imported run_selection_agent")
    except ImportError as e:
        print(f"❌ Failed to import run_selection_agent: {e}")
        print(f"Current Python path: {sys.path}")
        return False
    
    # Test data that mimics what main_agent.py would pass
    test_regions = ["US"]
    test_sectors = ["technology", "healthcare"]
    
    # New approach: work with asset classes and weights directly
    test_asset_class_weights = {
        "equity": 0.6,
        "bonds": 0.3,
        "commodity": 0.1
    }
    
    print(f"Test input:")
    print(f"  regions: {test_regions}")
    print(f"  sectors: {test_sectors}")
    print(f"  asset_class_weights: {test_asset_class_weights}")
    
    # Call the selection agent
    try:
        result = run_selection_agent(
            regions=test_regions,
            sectors=test_sectors,
            asset_class_weights=test_asset_class_weights
        )
        print("✅ Successfully called run_selection_agent")
    except Exception as e:
        print(f"❌ Failed to call run_selection_agent: {e}")
        return False
    
    # Verify the result structure matches what main_agent.py expects
    required_fields = ["success", "final_selections"]
    
    for field in required_fields:
        if field not in result:
            print(f"❌ Missing required field '{field}' in result")
            return False
        print(f"✅ Found required field '{field}'")
    
    # Check success field
    if not isinstance(result["success"], bool):
        print(f"❌ 'success' field should be boolean, got {type(result['success'])}")
        return False
    print(f"✅ 'success' field is boolean: {result['success']}")
    
    # Check final_selections structure
    final_selections = result["final_selections"]
    if not isinstance(final_selections, dict):
        print(f"❌ 'final_selections' should be dict, got {type(final_selections)}")
        return False
    print(f"✅ 'final_selections' is dict with keys: {list(final_selections.keys())}")
    
    # Test the main_agent.py calculation logic
    try:
        # This is the exact calculation from main_agent.py lines 529-532
        total_selections = sum(
            len(selections.get("selections", [])) 
            for selections in result.get("final_selections", {}).values()
        )
        print(f"✅ Successfully calculated total_selections: {total_selections}")
    except Exception as e:
        print(f"❌ Failed to calculate total_selections (main_agent.py logic): {e}")
        return False
    
    # Test individual asset class structure
    for asset_class, data in final_selections.items():
        if not isinstance(data, dict):
            print(f"❌ Asset class '{asset_class}' data should be dict, got {type(data)}")
            return False
        
        if "selections" not in data:
            print(f"❌ Asset class '{asset_class}' missing 'selections' field")
            return False
        
        if not isinstance(data["selections"], list):
            print(f"❌ Asset class '{asset_class}' 'selections' should be list, got {type(data['selections'])}")
            return False
        
        print(f"✅ Asset class '{asset_class}' has proper structure with {len(data['selections'])} selections")
    
    print("🎉 All compatibility tests passed!")
    return True

def main():
    """Main test runner"""
    print("="*60)
    print("SELECTION AGENT COMPATIBILITY TEST")
    print("="*60)
    
    success = test_selection_agent_compatibility()
    
    print("\n" + "="*60)
    if success:
        print("✅ COMPATIBILITY TEST PASSED")
        print("selection_agent.py is compatible with main_agent.py")
    else:
        print("❌ COMPATIBILITY TEST FAILED")
        print("selection_agent.py needs further modifications")
    print("="*60)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)