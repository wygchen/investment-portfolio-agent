#!/usr/bin/env python3
"""
Integration example showing how to use selection_agent.py in the AI investment portfolio system.

This example demonstrates how to integrate the selection agent with the portfolio construction
workflow from the main backend system.
"""

import sys
import os

# Add paths for imports
backend_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(backend_path, 'selection'))
sys.path.insert(0, os.path.join(backend_path, 'portfolio_construction'))

from selection_agent import run_selection_agent

def integrate_with_portfolio_construction():
    """
    Example integration with portfolio construction system
    
    This simulates how the selection agent would be called from the main
    portfolio construction workflow.
    """
    
    print("AI Investment Portfolio - Selection Agent Integration Example")
    print("=" * 70)
    
    # Example: These would come from the portfolio construction optimization
    # This simulates the output from portfolio_construction.py filtered results
    optimized_portfolio = {
        'filtered_tickers': {
            'SPY': 'equity',      # S&P 500 - Large Cap US Equity
            'QQQ': 'equity',      # NASDAQ - Tech Heavy Equity  
            'VTI': 'equity',      # Total Stock Market
            'BND': 'bonds',       # Aggregate Bond Index
            'VGIT': 'bonds',      # Intermediate Treasury Bonds
            'GLD': 'commodity',   # Gold
            'VNQ': 'equity'       # REITs (Real Estate)
        },
        'filtered_weights': {
            'SPY': 0.25,
            'QQQ': 0.20,
            'VTI': 0.15, 
            'BND': 0.20,
            'VGIT': 0.10,
            'GLD': 0.05,
            'VNQ': 0.05
        }
    }
    
    # User preferences (these would come from user input/discovery agent)
    user_preferences = {
        'regions': ['US'],  # Geographic preference
        'sectors': ['Technology', 'Healthcare', 'Financial', 'Consumer Discretionary'],
        'risk_tolerance': 'moderate'
    }
    
    print("Portfolio Optimization Results:")
    print(f"  Total Assets: {len(optimized_portfolio['filtered_tickers'])}")
    print(f"  Asset Classes: {set(optimized_portfolio['filtered_tickers'].values())}")
    print(f"  Geographic Focus: {user_preferences['regions']}")
    print(f"  Preferred Sectors: {user_preferences['sectors']}")
    
    print("\nCalling Selection Agent...")
    print("-" * 30)
    
    try:
        # Call the selection agent with the optimized portfolio results
        selection_results = run_selection_agent(
            regions=user_preferences['regions'],
            sectors=user_preferences['sectors'],
            filtered_tickers=optimized_portfolio['filtered_tickers'],
            filtered_weights=optimized_portfolio['filtered_weights']
        )
        
        if selection_results['success']:
            print("✅ Selection Agent completed successfully!")
            
            final_selections = selection_results['final_selections']
            execution_summary = final_selections['execution_summary']
            
            print(f"\nExecution Summary:")
            print(f"  Total execution time: {execution_summary['total_execution_time']:.2f}s")
            print(f"  Equity processing: {'✅' if execution_summary['equity_success'] else '❌'}")
            print(f"  Bonds processing: {'✅' if execution_summary['bonds_success'] else '❌'}")
            
            print(f"\nSelection Results:")
            print(f"  Total selections: {final_selections['total_selections']}")
            print(f"  Equity selections: {final_selections['selections_by_asset_class']['equity']}")
            print(f"  Bond selections: {final_selections['selections_by_asset_class']['bonds']}")
            
            # Show detailed selections by asset class
            if final_selections['all_selections']:
                print(f"\nDetailed Selections:")
                
                equity_selections = [s for s in final_selections['all_selections'] 
                                   if s.get('asset_class') == 'equity']
                bond_selections = [s for s in final_selections['all_selections'] 
                                 if s.get('asset_class') == 'bonds']
                
                if equity_selections:
                    print(f"  📈 Equity Selections ({len(equity_selections)}):")
                    for i, selection in enumerate(equity_selections[:3], 1):
                        score = selection.get('final_score', selection.get('score', 'N/A'))
                        ticker = selection.get('ticker', 'N/A')
                        sector = selection.get('sector', 'N/A')
                        print(f"    {i}. {ticker} ({sector}) - Score: {score}")
                
                if bond_selections:
                    print(f"  🏦 Bond Selections ({len(bond_selections)}):")
                    for i, selection in enumerate(bond_selections[:3], 1):
                        score = selection.get('score', 'N/A')
                        ticker = selection.get('ticker', 'N/A')
                        yield_val = selection.get('yield', 'N/A')
                        rating = selection.get('credit_rating', 'N/A')
                        print(f"    {i}. {ticker} (Rating: {rating}) - Yield: {yield_val}% Score: {score}")
            
            print(f"\n🎯 Next Steps:")
            print(f"  - Review selected securities for final portfolio construction")
            print(f"  - Apply position sizing based on optimized weights")
            print(f"  - Consider any additional risk management overlays")
            
            return True
            
        else:
            print(f"❌ Selection Agent failed: {selection_results['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return False

def main():
    """Main entry point"""
    try:
        success = integrate_with_portfolio_construction()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)