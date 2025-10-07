#!/usr/bin/env python3
"""
Test script for the Selection Agent

This script tests the selection_agent.py functionality with sample data.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from selection_agent import run_selection_agent

def test_selection_agent():
    """Test the selection agent with sample data"""
    
    print("Testing Selection Agent...")
    print("=" * 50)
    
    # Sample data for testing
    sample_filtered_tickers = {
        'SPY': 'equity',     # S&P 500 ETF
        'QQQ': 'equity',     # NASDAQ ETF
        'AAPL': 'equity',    # Apple stock
        'BND': 'bonds',      # Bond ETF
        'AGG': 'bonds',      # Another bond ETF
        'GLD': 'commodity'   # Gold ETF
    }
    
    sample_filtered_weights = {
        'SPY': 0.25,
        'QQQ': 0.15,
        'AAPL': 0.10,
        'BND': 0.25,
        'AGG': 0.15,
        'GLD': 0.10
    }
    
    try:
        # Run the selection agent
        results = run_selection_agent(
            regions=['US'],
            sectors=['Technology', 'Healthcare', 'Financial'],
            filtered_tickers=sample_filtered_tickers,
            filtered_weights=sample_filtered_weights
        )
        
        # Print results
        print(f"\nExecution Status: {'SUCCESS' if results['success'] else 'FAILED'}")
        print(f"Execution Time: {results['execution_time']:.2f} seconds")
        
        if results['success']:
            final_selections = results['final_selections']
            print(f"\nTotal Selections: {final_selections['total_selections']}")
            print(f"Equity Selections: {final_selections['selections_by_asset_class']['equity']}")
            print(f"Bond Selections: {final_selections['selections_by_asset_class']['bonds']}")
            
            # Show some sample selections
            if final_selections['all_selections']:
                print(f"\nSample Selections:")
                for i, selection in enumerate(final_selections['all_selections'][:3]):
                    print(f"  {i+1}. {selection.get('ticker', 'N/A')} - {selection.get('asset_class', 'N/A')}")
        else:
            print(f"Error: {results['error']}")
        
        return results['success']
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_selection_agent()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)