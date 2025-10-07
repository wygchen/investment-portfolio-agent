#!/usr/bin/env python3
"""
Selection Agent - LangGraph Workflow Implementation

This agent orchestrates the selection process for different asset classes:
- Equity: Calls the equity_selection_agent for stock selection
- Bonds: Calls a dummy function for bond selection
- Routes based on asset classes present in filtered_tickers

Usage:
    from selection_agent import run_selection_agent
    
    result = run_selection_agent(
        regions=['US', 'HK'],
        sectors=['Technology', 'Healthcare'], 
        filtered_tickers={'SPY': 'equity', 'BND': 'bonds', 'GLD': 'commodity'},
        filtered_weights={'SPY': 0.4, 'BND': 0.3, 'GLD': 0.3}
    )
"""

import sys
import os
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict, Set

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

# Import equity selection agent
equity_agent_path = os.path.join(os.path.dirname(__file__), 'equity_selection_agent')
sys.path.insert(0, equity_agent_path)

try:
    from equity_selection_agent import run_agent_workflow as run_equity_selection  # type: ignore
    EQUITY_AGENT_AVAILABLE = True
except ImportError as e:
    # Fallback if the import fails
    EQUITY_AGENT_AVAILABLE = False
    def run_equity_selection(*args, **kwargs):
        return {
            'success': False,
            'error': f'Equity selection agent not available: {str(e)}',
            'final_selection_count': 0,
            'final_selections': [],
            'execution_time': 0
        }


# =============================================================================
# STATE DEFINITION
# =============================================================================

class SelectionAgentState(TypedDict):
    """State object that flows through the selection workflow nodes"""
    
    # Input parameters
    regions: Optional[List[str]]
    sectors: Optional[List[str]]
    filtered_tickers: Dict[str, str]  # ticker -> asset_class mapping
    filtered_weights: Dict[str, float]  # ticker -> weight mapping
    
    # Processing metadata
    start_time: float
    execution_time: float
    asset_classes_present: Set[str]
    
    # Results by asset class
    equity_results: Optional[Dict[str, Any]]
    bonds_results: Optional[Dict[str, Any]]
    commodity_results: Optional[Dict[str, Any]]
    
    # Combined results
    final_selections: Dict[str, Any]
    
    # Status tracking
    success: bool
    error: Optional[str]
    processing_summary: Dict[str, Any]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def setup_logging() -> None:
    """Set up logging configuration for the selection agent"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def analyze_asset_classes(filtered_tickers: Dict[str, str]) -> Set[str]:
    """
    Analyze which asset classes are present in the filtered tickers.
    
    Args:
        filtered_tickers: Dictionary mapping ticker to asset class
        
    Returns:
        Set of unique asset classes present
    """
    return set(filtered_tickers.values())


def bonds_selection_dummy(regions: Optional[List[str]] = None,
                         sectors: Optional[List[str]] = None,
                         bond_tickers: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Dummy function for bond selection - placeholder implementation.
    
    Args:
        regions: List of allowed regions
        sectors: List of allowed sectors (not applicable for bonds)
        bond_tickers: List of bond tickers to analyze
        
    Returns:
        Dictionary with dummy bond selection results
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing {len(bond_tickers) if bond_tickers else 0} bond tickers...")
    
    # Simulate some processing time
    time.sleep(0.5)
    
    # Return dummy results
    dummy_selections = []
    if bond_tickers:
        for i, ticker in enumerate(bond_tickers[:5]):  # Limit to top 5
            dummy_selections.append({
                'ticker': ticker,
                'asset_class': 'bonds',
                'score': 85.0 - (i * 2),  # Decreasing scores
                'duration': 5.5 + (i * 0.5),
                'yield': 4.2 - (i * 0.1),
                'credit_rating': 'AA' if i < 2 else 'A',
                'recommendation': 'BUY' if i < 3 else 'HOLD'
            })
    
    return {
        'success': True,
        'selection_count': len(dummy_selections),
        'selections': dummy_selections,
        'processing_time': 0.5,
        'message': 'Dummy bond selection completed'
    }


# =============================================================================
# WORKFLOW NODE FUNCTIONS
# =============================================================================

def initialization_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 1: Initialize the selection workflow
    
    Analyzes input parameters and determines which asset classes need processing.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("SELECTION AGENT - INITIALIZATION")
    logger.info("="*60)
    
    try:
        filtered_tickers = state["filtered_tickers"]
        filtered_weights = state["filtered_weights"]
        
        # Validate inputs
        if not filtered_tickers:
            raise ValueError("filtered_tickers cannot be empty")
        
        if not filtered_weights:
            raise ValueError("filtered_weights cannot be empty")
        
        # Analyze asset classes present
        asset_classes_present = analyze_asset_classes(filtered_tickers)
        
        logger.info(f"Total tickers to process: {len(filtered_tickers)}")
        logger.info(f"Asset classes present: {sorted(asset_classes_present)}")
        logger.info(f"Regions filter: {state['regions'] or 'All'}")
        logger.info(f"Sectors filter: {state['sectors'] or 'All'}")
        
        # Log ticker distribution by asset class
        for asset_class in sorted(asset_classes_present):
            tickers_in_class = [t for t, ac in filtered_tickers.items() if ac == asset_class]
            logger.info(f"  {asset_class}: {len(tickers_in_class)} tickers")
        
        # Update state
        state.update({
            "asset_classes_present": asset_classes_present,
            "processing_summary": {
                "total_tickers": len(filtered_tickers),
                "asset_classes": list(asset_classes_present),
                "ticker_distribution": {
                    ac: len([t for t, c in filtered_tickers.items() if c == ac])
                    for ac in asset_classes_present
                }
            }
        })
        
        logger.info("Initialization completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        state.update({
            "success": False,
            "error": f"Initialization failed: {str(e)}"
        })
        return state


def equity_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 2: Process equity selections using the equity_selection_agent
    
    Calls the equity selection agent for stocks in the equity asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("EQUITY SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        filtered_tickers = state["filtered_tickers"]
        asset_classes_present = state["asset_classes_present"]
        regions = state["regions"]
        sectors = state["sectors"]
        
        # Check if equity processing is needed
        if 'equity' not in asset_classes_present:
            logger.info("No equity tickers found - skipping equity selection")
            state["equity_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No equity tickers to process'
            }
            return state
        
        # Get equity tickers
        equity_tickers = [ticker for ticker, asset_class in filtered_tickers.items() 
                         if asset_class == 'equity']
        
        logger.info(f"Processing {len(equity_tickers)} equity tickers...")
        logger.info(f"Equity tickers: {equity_tickers}")
        
        # Call the equity selection agent
        equity_results = run_equity_selection(
            regions=regions,
            sectors=sectors,
            enable_qualitative=False,  # Can be made configurable
            force_refresh=False
        )
        
        # Process and store results
        if equity_results['success']:
            logger.info(f"Equity selection completed successfully")
            logger.info(f"Selected {equity_results.get('final_selection_count', 0)} equity candidates")
            
            # Convert DataFrame to dictionary format if needed
            final_selections = equity_results.get('final_selections')
            if final_selections is not None and hasattr(final_selections, 'to_dict'):
                selections_dict = final_selections.to_dict('records')
            else:
                selections_dict = final_selections or []
            
            state["equity_results"] = {
                'success': True,
                'selection_count': equity_results.get('final_selection_count', 0),
                'selections': selections_dict,
                'execution_time': equity_results.get('execution_time', 0),
                'screening_summary': equity_results.get('screening_summary'),
                'message': 'Equity selection completed successfully'
            }
        else:
            logger.error(f"Equity selection failed: {equity_results.get('error', 'Unknown error')}")
            state["equity_results"] = {
                'success': False,
                'selection_count': 0,
                'selections': [],
                'error': equity_results.get('error', 'Unknown error'),
                'message': 'Equity selection failed'
            }
        
        return state
        
    except Exception as e:
        logger.error(f"Equity selection processing failed: {str(e)}")
        state["equity_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'message': 'Equity selection processing failed'
        }
        return state


def bonds_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 3: Process bond selections using the dummy bonds function
    
    Calls the dummy bond selection function for tickers in the bonds asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("BONDS SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        filtered_tickers = state["filtered_tickers"]
        asset_classes_present = state["asset_classes_present"]
        regions = state["regions"]
        sectors = state["sectors"]
        
        # Check if bonds processing is needed
        if 'bonds' not in asset_classes_present:
            logger.info("No bond tickers found - skipping bonds selection")
            state["bonds_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No bond tickers to process'
            }
            return state
        
        # Get bond tickers
        bond_tickers = [ticker for ticker, asset_class in filtered_tickers.items() 
                       if asset_class == 'bonds']
        
        logger.info(f"Processing {len(bond_tickers)} bond tickers...")
        logger.info(f"Bond tickers: {bond_tickers}")
        
        # Call the dummy bonds selection function
        bonds_results = bonds_selection_dummy(
            regions=regions,
            sectors=sectors,
            bond_tickers=bond_tickers
        )
        
        # Store results
        state["bonds_results"] = bonds_results
        
        logger.info(f"Bonds selection completed: {bonds_results['selection_count']} selections")
        return state
        
    except Exception as e:
        logger.error(f"Bonds selection processing failed: {str(e)}")
        state["bonds_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'message': 'Bonds selection processing failed'
        }
        return state


def aggregation_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 4: Aggregate results from all asset class selections
    
    Combines results from equity, bonds, and other asset classes into final output.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("RESULTS AGGREGATION")
    logger.info("="*50)
    
    try:
        start_time = state["start_time"]
        equity_results = state.get("equity_results") or {}
        bonds_results = state.get("bonds_results") or {}
        
        # Aggregate all selections
        all_selections = []
        
        # Add equity selections
        if equity_results.get('success') and equity_results.get('selections'):
            equity_selections = equity_results['selections']
            if equity_selections:
                all_selections.extend(equity_selections)
                logger.info(f"Added {len(equity_selections)} equity selections")
        
        # Add bond selections
        if bonds_results.get('success') and bonds_results.get('selections'):
            bond_selections = bonds_results['selections']
            if bond_selections:
                all_selections.extend(bond_selections)
                logger.info(f"Added {len(bond_selections)} bond selections")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Create final results summary
        final_selections = {
            'total_selections': len(all_selections),
            'selections_by_asset_class': {
                'equity': equity_results.get('selection_count', 0),
                'bonds': bonds_results.get('selection_count', 0)
            },
            'all_selections': all_selections,
            'execution_summary': {
                'total_execution_time': execution_time,
                'equity_success': equity_results.get('success', False),
                'bonds_success': bonds_results.get('success', False),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Update state
        state.update({
            "final_selections": final_selections,
            "execution_time": execution_time,
            "success": True
        })
        
        # Log summary
        logger.info(f"Total selections: {len(all_selections)}")
        logger.info(f"Execution time: {execution_time:.2f} seconds")
        logger.info("Results aggregation completed successfully")
        
        return state
        
    except Exception as e:
        execution_time = time.time() - state["start_time"]
        logger.error(f"Results aggregation failed: {str(e)}")
        state.update({
            "success": False,
            "error": f"Results aggregation failed: {str(e)}",
            "execution_time": execution_time
        })
        return state


# =============================================================================
# WORKFLOW CREATION AND EXECUTION
# =============================================================================

def create_selection_workflow() -> CompiledStateGraph:
    """
    Create and compile the LangGraph workflow for the Selection Agent.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the state graph
    workflow = StateGraph(SelectionAgentState)
    
    # Add nodes
    workflow.add_node("initialization", initialization_node)
    workflow.add_node("equity_selection", equity_selection_node)
    workflow.add_node("bonds_selection", bonds_selection_node)
    workflow.add_node("aggregation", aggregation_node)
    
    # Add edges to define the flow
    workflow.add_edge(START, "initialization")
    workflow.add_edge("initialization", "equity_selection")
    workflow.add_edge("equity_selection", "bonds_selection")
    workflow.add_edge("bonds_selection", "aggregation")
    workflow.add_edge("aggregation", END)
    
    # Compile the workflow
    return workflow.compile()


def run_selection_agent(regions: Optional[List[str]] = None,
                       sectors: Optional[List[str]] = None,
                       filtered_tickers: Optional[Dict[str, str]] = None,
                       filtered_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Run the Selection Agent using LangGraph workflow.
    
    Args:
        regions: List of allowed regions ('US', 'HK', etc.)
        sectors: List of allowed sectors
        filtered_tickers: Dictionary mapping ticker to asset class 
                         (e.g., {'SPY': 'equity', 'BND': 'bonds'})
        filtered_weights: Dictionary mapping ticker to weight
                         (e.g., {'SPY': 0.6, 'BND': 0.4})
        
    Returns:
        Dictionary with execution results and selections by asset class
    """
    start_time = time.time()
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("SELECTION AGENT - LANGGRAPH WORKFLOW")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Validate inputs
    if not filtered_tickers:
        return {
            'success': False,
            'error': 'filtered_tickers is required and cannot be empty',
            'execution_time': time.time() - start_time
        }
    
    if not filtered_weights:
        return {
            'success': False,
            'error': 'filtered_weights is required and cannot be empty',
            'execution_time': time.time() - start_time
        }
    
    try:
        # Create the workflow
        workflow = create_selection_workflow()
        
        # Initialize the state
        initial_state: SelectionAgentState = {
            # Input parameters
            "regions": regions,
            "sectors": sectors,
            "filtered_tickers": filtered_tickers,
            "filtered_weights": filtered_weights,
            
            # Processing metadata
            "start_time": start_time,
            "execution_time": 0.0,
            "asset_classes_present": set(),
            
            # Results by asset class (initialized to None)
            "equity_results": None,
            "bonds_results": None,
            "commodity_results": None,
            
            # Combined results
            "final_selections": {},
            
            # Status tracking
            "success": True,
            "error": None,
            "processing_summary": {}
        }
        
        # Execute the workflow
        logger.info("Starting Selection Agent workflow execution...")
        final_state = workflow.invoke(initial_state)
        
        # Return results
        if final_state["success"]:
            logger.info("\n" + "="*60)
            logger.info("SELECTION AGENT - EXECUTION COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            
            return {
                'success': True,
                'execution_time': final_state["execution_time"],
                'processing_summary': final_state["processing_summary"],
                'final_selections': final_state["final_selections"],
                'equity_results': final_state["equity_results"],
                'bonds_results': final_state["bonds_results"]
            }
        else:
            logger.error("Selection Agent execution failed")
            return {
                'success': False,
                'execution_time': final_state["execution_time"],
                'error': final_state["error"]
            }
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"SELECTION AGENT EXECUTION FAILED after {execution_time:.2f} seconds: {str(e)}")
        logger.exception("Full error details:")
        
        return {
            'success': False,
            'execution_time': execution_time,
            'error': str(e)
        }


def main() -> int:
    """Main entry point for standalone testing"""
    try:
        # Example usage with sample data
        sample_filtered_tickers = {
            'SPY': 'equity',
            'QQQ': 'equity', 
            'BND': 'bonds',
            'AGG': 'bonds',
            'GLD': 'commodity'
        }
        
        sample_filtered_weights = {
            'SPY': 0.3,
            'QQQ': 0.2,
            'BND': 0.25,
            'AGG': 0.15,
            'GLD': 0.1
        }
        
        # Run the selection agent
        results = run_selection_agent(
            regions=['US'],
            sectors=['Technology', 'Healthcare'],
            filtered_tickers=sample_filtered_tickers,
            filtered_weights=sample_filtered_weights
        )
        
        # Print results summary
        if results['success']:
            print(f"\nExecution successful in {results['execution_time']:.2f} seconds")
            print(f"Total selections: {results['final_selections']['total_selections']}")
        else:
            print(f"Execution failed: {results['error']}")
        
        return 0 if results['success'] else 1
        
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
