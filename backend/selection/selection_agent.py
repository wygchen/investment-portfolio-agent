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
except ImportError as import_error:
    # Fallback if the import fails
    EQUITY_AGENT_AVAILABLE = False
    
    # Capture the error message at module level
    EQUITY_IMPORT_ERROR = str(import_error)
    
    def run_equity_selection(*args, **kwargs):
        return {
            'success': False,
            'error': f'Equity selection agent not available: {EQUITY_IMPORT_ERROR}',
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
    asset_class_weights: Dict[str, float]  # asset_class -> weight mapping (e.g., {'equity': 0.6, 'bonds': 0.3})
    
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
    summary_metadata: Optional[Dict[str, Any]]


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


def analyze_asset_classes(asset_class_weights: Dict[str, float]) -> Set[str]:
    """
    Analyze which asset classes are present in the asset class weights.
    
    Args:
        asset_class_weights: Dictionary mapping asset class to weight
        
    Returns:
        Set of unique asset classes present
    """
    return set(asset_class_weights.keys())


def bonds_selection_dummy(regions: Optional[List[str]] = None,
                         sectors: Optional[List[str]] = None,
                         weight: float = 0.0) -> Dict[str, Any]:
    """
    Dummy function for bond selection - placeholder implementation.
    
    Args:
        regions: List of allowed regions
        sectors: List of allowed sectors (not applicable for bonds)
        weight: Weight allocation for bonds asset class
        
    Returns:
        Dictionary with dummy bond selection results
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing bonds with weight allocation: {weight:.1%}")
    
    # Simulate some processing time
    time.sleep(0.5)
    
    # Generate dummy bond selections based on weight
    # Higher weight = more bond selections
    num_selections = max(1, int(weight * 10))  # Scale weight to number of selections
    
    dummy_selections = []
    bond_tickers = ['BND', 'AGG', 'TLT', 'IEF', 'SHY']  # Sample bond ETFs
    
    for i in range(min(num_selections, len(bond_tickers))):
        ticker = bond_tickers[i]
        dummy_selections.append({
            'ticker': ticker,
            'asset_class': 'bonds',
            'score': 85.0 - (i * 2),  # Decreasing scores
            'duration': 5.5 + (i * 0.5),
            'yield': 4.2 - (i * 0.1),
            'credit_rating': 'AA' if i < 2 else 'A',
            'recommendation': 'BUY' if i < 3 else 'HOLD',
            'allocation_weight': weight / num_selections  # Distribute weight among selections
        })
    
    return {
        'success': True,
        'selection_count': len(dummy_selections),
        'selections': dummy_selections,
        'processing_time': 0.5,
        'total_weight': weight,
        'message': f'Dummy bond selection completed with {weight:.1%} allocation'
    }


def commodity_selection_dummy(regions: Optional[List[str]] = None,
                             sectors: Optional[List[str]] = None,
                             weight: float = 0.0) -> Dict[str, Any]:
    """
    Dummy function for commodity selection - placeholder implementation.
    
    Args:
        regions: List of allowed regions
        sectors: List of allowed sectors (not applicable for commodities)
        weight: Weight allocation for commodity asset class
        
    Returns:
        Dictionary with dummy commodity selection results
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing commodities with weight allocation: {weight:.1%}")
    
    # Simulate some processing time
    time.sleep(0.3)
    
    # Generate dummy commodity selections based on weight
    num_selections = max(1, int(weight * 8))  # Scale weight to number of selections
    
    dummy_selections = []
    commodity_tickers = ['GLD', 'SLV', 'DBC', 'USO', 'UNG']  # Sample commodity ETFs
    
    for i in range(min(num_selections, len(commodity_tickers))):
        ticker = commodity_tickers[i]
        dummy_selections.append({
            'ticker': ticker,
            'asset_class': 'commodity',
            'score': 80.0 - (i * 3),  # Decreasing scores
            'volatility': 15.0 + (i * 2),
            'correlation_to_stocks': 0.2 + (i * 0.1),
            'recommendation': 'BUY' if i < 2 else 'HOLD',
            'allocation_weight': weight / num_selections  # Distribute weight among selections
        })
    
    return {
        'success': True,
        'selection_count': len(dummy_selections),
        'selections': dummy_selections,
        'processing_time': 0.3,
        'total_weight': weight,
        'message': f'Dummy commodity selection completed with {weight:.1%} allocation'
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
        asset_class_weights = state["asset_class_weights"]
        
        # Validate inputs
        if not asset_class_weights:
            raise ValueError("asset_class_weights cannot be empty")
        
        # Analyze asset classes present
        asset_classes_present = analyze_asset_classes(asset_class_weights)
        
        logger.info(f"Total asset classes to process: {len(asset_class_weights)}")
        logger.info(f"Asset classes present: {sorted(asset_classes_present)}")
        logger.info(f"Regions filter: {state['regions'] or 'All'}")
        logger.info(f"Sectors filter: {state['sectors'] or 'All'}")
        
        # Log weight distribution by asset class
        for asset_class in sorted(asset_classes_present):
            weight = asset_class_weights[asset_class]
            logger.info(f"  {asset_class}: {weight:.1%} allocation")
        
        # Update state
        state.update({
            "asset_classes_present": asset_classes_present,
            "processing_summary": {
                "total_asset_classes": len(asset_class_weights),
                "asset_classes": list(asset_classes_present),
                "weight_distribution": asset_class_weights
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
    
    Calls the equity selection agent for the equity asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("EQUITY SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_class_weights = state["asset_class_weights"]
        asset_classes_present = state["asset_classes_present"]
        regions = state["regions"]
        sectors = state["sectors"]
        
        # Check if equity processing is needed
        if 'equity' not in asset_classes_present:
            logger.info("No equity allocation found - skipping equity selection")
            state["equity_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No equity allocation to process'
            }
            return state
        
        # Get equity weight
        equity_weight = asset_class_weights.get('equity', 0.0)
        
        logger.info(f"Processing equity with {equity_weight:.1%} allocation...")
        
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
            
            # Add weight information to each selection
            if selections_dict and equity_weight > 0:
                individual_weight = equity_weight / len(selections_dict)
                for selection in selections_dict:
                    selection['allocation_weight'] = individual_weight
            
            state["equity_results"] = {
                'success': True,
                'selection_count': equity_results.get('final_selection_count', 0),
                'selections': selections_dict,
                'execution_time': equity_results.get('execution_time', 0),
                'screening_summary': equity_results.get('screening_summary'),
                'total_weight': equity_weight,
                'message': f'Equity selection completed with {equity_weight:.1%} allocation'
            }
        else:
            logger.error(f"Equity selection failed: {equity_results.get('error', 'Unknown error')}")
            state["equity_results"] = {
                'success': False,
                'selection_count': 0,
                'selections': [],
                'error': equity_results.get('error', 'Unknown error'),
                'total_weight': equity_weight,
                'message': 'Equity selection failed'
            }
        
        return state
        
    except Exception as e:
        logger.error(f"Equity selection processing failed: {str(e)}")
        equity_weight = state["asset_class_weights"].get('equity', 0.0)
        state["equity_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'total_weight': equity_weight,
            'message': 'Equity selection processing failed'
        }
        return state


def bonds_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 3: Process bond selections using the dummy bonds function
    
    Calls the dummy bond selection function for the bonds asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("BONDS SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_class_weights = state["asset_class_weights"]
        asset_classes_present = state["asset_classes_present"]
        regions = state["regions"]
        sectors = state["sectors"]
        
        # Check if bonds processing is needed
        if 'bonds' not in asset_classes_present:
            logger.info("No bond allocation found - skipping bonds selection")
            state["bonds_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No bond allocation to process'
            }
            return state
        
        # Get bond weight
        bond_weight = asset_class_weights.get('bonds', 0.0)
        
        logger.info(f"Processing bonds with {bond_weight:.1%} allocation...")
        
        # Call the dummy bonds selection function
        bonds_results = bonds_selection_dummy(
            regions=regions,
            sectors=sectors,
            weight=bond_weight
        )
        
        # Store results
        state["bonds_results"] = bonds_results
        
        logger.info(f"Bonds selection completed: {bonds_results['selection_count']} selections")
        return state
        
    except Exception as e:
        logger.error(f"Bonds selection processing failed: {str(e)}")
        bond_weight = state["asset_class_weights"].get('bonds', 0.0)
        state["bonds_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'total_weight': bond_weight,
            'message': 'Bonds selection processing failed'
        }
        return state


def commodity_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 3.5: Process commodity selections using the dummy commodity function
    
    Calls the dummy commodity selection function for the commodity asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("COMMODITY SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_class_weights = state["asset_class_weights"]
        asset_classes_present = state["asset_classes_present"]
        regions = state["regions"]
        sectors = state["sectors"]
        
        # Check if commodity processing is needed
        if 'commodity' not in asset_classes_present:
            logger.info("No commodity allocation found - skipping commodity selection")
            state["commodity_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No commodity allocation to process'
            }
            return state
        
        # Get commodity weight
        commodity_weight = asset_class_weights.get('commodity', 0.0)
        
        logger.info(f"Processing commodities with {commodity_weight:.1%} allocation...")
        
        # Call the dummy commodity selection function
        commodity_results = commodity_selection_dummy(
            regions=regions,
            sectors=sectors,
            weight=commodity_weight
        )
        
        # Store results
        state["commodity_results"] = commodity_results
        
        logger.info(f"Commodity selection completed: {commodity_results['selection_count']} selections")
        return state
        
    except Exception as e:
        logger.error(f"Commodity selection processing failed: {str(e)}")
        commodity_weight = state["asset_class_weights"].get('commodity', 0.0)
        state["commodity_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'total_weight': commodity_weight,
            'message': 'Commodity selection processing failed'
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
        commodity_results = state.get("commodity_results") or {}
        
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
        
        # Add commodity selections
        if commodity_results.get('success') and commodity_results.get('selections'):
            commodity_selections = commodity_results['selections']
            if commodity_selections:
                all_selections.extend(commodity_selections)
                logger.info(f"Added {len(commodity_selections)} commodity selections")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Create final results summary in the format expected by main_agent.py
        # Structure: { "asset_class": { "selections": [...], "selection_count": N, "success": bool } }
        final_selections = {}
        
        # Add equity results
        if equity_results:
            final_selections['equity'] = {
                'selections': equity_results.get('selections', []),
                'selection_count': equity_results.get('selection_count', 0),
                'success': equity_results.get('success', False),
                'processing_time': equity_results.get('processing_time', 0),
                'message': equity_results.get('message', ''),
                'execution_time': execution_time,
                'total_weight': equity_results.get('total_weight', 0.0)
            }
        
        # Add bond results
        if bonds_results:
            final_selections['bonds'] = {
                'selections': bonds_results.get('selections', []),
                'selection_count': bonds_results.get('selection_count', 0),
                'success': bonds_results.get('success', False),
                'processing_time': bonds_results.get('processing_time', 0),
                'message': bonds_results.get('message', ''),
                'execution_time': execution_time,
                'total_weight': bonds_results.get('total_weight', 0.0)
            }
        
        # Add commodity results
        if commodity_results:
            final_selections['commodity'] = {
                'selections': commodity_results.get('selections', []),
                'selection_count': commodity_results.get('selection_count', 0),
                'success': commodity_results.get('success', False),
                'processing_time': commodity_results.get('processing_time', 0),
                'message': commodity_results.get('message', ''),
                'execution_time': execution_time,
                'total_weight': commodity_results.get('total_weight', 0.0)
            }
        
        # Store summary metadata in the state for debugging/logging purposes
        summary_metadata = {
            'total_selections': len(all_selections),
            'all_selections': all_selections,
            'execution_summary': {
                'total_execution_time': execution_time,
                'equity_success': equity_results.get('success', False),
                'bonds_success': bonds_results.get('success', False),
                'commodity_success': commodity_results.get('success', False),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Update state
        state.update({
            "final_selections": final_selections,
            "execution_time": execution_time,
            "success": True,
            "summary_metadata": summary_metadata
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
    workflow.add_node("commodity_selection", commodity_selection_node)
    workflow.add_node("aggregation", aggregation_node)
    
    # Add edges to define the flow
    workflow.add_edge(START, "initialization")
    workflow.add_edge("initialization", "equity_selection")
    workflow.add_edge("equity_selection", "bonds_selection")
    workflow.add_edge("bonds_selection", "commodity_selection")
    workflow.add_edge("commodity_selection", "aggregation")
    workflow.add_edge("aggregation", END)
    
    # Compile the workflow
    return workflow.compile()


def run_selection_agent(regions: Optional[List[str]] = None,
                       sectors: Optional[List[str]] = None,
                       asset_class_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Run the Selection Agent using LangGraph workflow.
    
    Args:
        regions: List of allowed regions ('US', 'HK', etc.)
        sectors: List of allowed sectors
        asset_class_weights: Dictionary mapping asset class to weight allocation
                           (e.g., {'equity': 0.6, 'bonds': 0.3, 'commodity': 0.1})
        
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
    if not asset_class_weights:
        return {
            'success': False,
            'error': 'asset_class_weights is required and cannot be empty',
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
            "asset_class_weights": asset_class_weights,
            
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
            "processing_summary": {},
            "summary_metadata": None
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
        sample_asset_class_weights = {
            'equity': 0.5,
            'bonds': 0.35,
            'commodity': 0.15
        }
        
        # Run the selection agent
        results = run_selection_agent(
            regions=['US'],
            sectors=['Technology', 'Healthcare'],
            asset_class_weights=sample_asset_class_weights
        )
        
        # Print results summary
        if results['success']:
            print(f"\nExecution successful in {results['execution_time']:.2f} seconds")
            total_selections = sum(
                len(asset_data.get('selections', [])) 
                for asset_data in results.get('final_selections', {}).values()
            )
            print(f"Total selections: {total_selections}")
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
