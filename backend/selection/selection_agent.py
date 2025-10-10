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
try:
    import equity_selection_agent.src.equity_selection_agent as esa_module
    run_equity_selection = esa_module.run_agent_workflow
    EQUITY_AGENT_AVAILABLE = True
except ImportError as import_error:
    # Fallback if the import fails - create a mock function
    EQUITY_AGENT_AVAILABLE = False
    
    # Capture the error message at module level
    EQUITY_IMPORT_ERROR = str(import_error)
    
    def run_equity_selection(*args, **kwargs):
        """Mock equity selection function when the real agent is not available"""
        logger = logging.getLogger(__name__)
        logger.warning(f"Using mock equity selection due to import error: {EQUITY_IMPORT_ERROR}")
        
        # Return mock results with exactly 3 selections
        return {
            'success': True,
            'final_selection_count': 3,
            'final_selections': [
                {'ticker': 'AAPL', 'score': 85.0, 'sector': 'Technology', 'recommendation': 'BUY'},
                {'ticker': 'MSFT', 'score': 82.0, 'sector': 'Technology', 'recommendation': 'BUY'},
                {'ticker': 'GOOGL', 'score': 80.0, 'sector': 'Technology', 'recommendation': 'BUY'}
            ],
            'execution_time': 2.0,
            'screening_summary': {'total_screened': 100, 'passed_screening': 25},
            'error': None
        }


# =============================================================================
# STATE DEFINITION
# =============================================================================

class SelectionAgentState(TypedDict):
    """State object that flows through the selection workflow nodes"""
    
    # Input parameters
    regions: Optional[List[str]]
    sectors: Optional[List[str]]
    asset_class_weights: Dict[str, float]  # asset_class -> weight mapping (e.g., {'US_EQUITIES': 0.6, 'BONDS': 0.3})
    
    # Processing metadata
    start_time: float
    execution_time: float
    asset_classes_present: Set[str]
    
    # Results by asset class
    equity_results: Optional[Dict[str, Any]]
    bonds_results: Optional[Dict[str, Any]]
    commodity_results: Optional[Dict[str, Any]]
    reits_results: Optional[Dict[str, Any]]
    crypto_results: Optional[Dict[str, Any]]
    hong_kong_equity_results: Optional[Dict[str, Any]]
    
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


def map_asset_class_to_selection_type(asset_class: str) -> str:
    """
    Map detailed asset class names from portfolio_construction.py to selection types.
    
    Args:
        asset_class: Asset class name from portfolio construction (e.g., 'US_EQUITIES', 'BONDS')
        
    Returns:
        Selection type for the selection agent (e.g., 'equity', 'bonds')
    """
    mapping = {
        'US_EQUITIES': 'equity',
        'HONG_KONG_EQUITIES': 'hong_kong_equity',
        'BONDS': 'bonds',
        'REITS': 'reits',
        'COMMODITIES': 'commodity',
        'CRYPTO': 'crypto'
    }
    return mapping.get(asset_class, 'equity')  # Default to equity


def map_selection_type_to_asset_class(selection_type: str) -> str:
    """
    Map selection types back to detailed asset class names.
    
    Args:
        selection_type: Selection type (e.g., 'equity', 'bonds')
        
    Returns:
        Detailed asset class name (e.g., 'US_EQUITIES', 'BONDS')
    """
    mapping = {
        'equity': 'US_EQUITIES',
        'hong_kong_equity': 'HONG_KONG_EQUITIES',
        'bonds': 'BONDS',
        'reits': 'REITS',
        'commodity': 'COMMODITIES',
        'crypto': 'CRYPTO'
    }
    return mapping.get(selection_type, 'US_EQUITIES')  # Default to US_EQUITIES


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
        Dictionary with dummy bond selection results (exactly 3 selections)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing bonds with weight allocation: {weight:.1%}")
    
    # Simulate some processing time
    time.sleep(0.5)
    
    # Always return exactly 3 bond selections
    num_selections = 3
    
    dummy_selections = []
    bond_tickers = ['BND', 'AGG', 'TLT', 'IEF', 'SHY']  # Sample bond ETFs
    
    for i in range(num_selections):
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
        Dictionary with dummy commodity selection results (exactly 3 selections)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing commodities with weight allocation: {weight:.1%}")
    
    # Simulate some processing time
    time.sleep(0.3)
    
    # Always return exactly 3 commodity selections
    num_selections = 3
    
    dummy_selections = []
    commodity_tickers = ['GLD', 'SLV', 'DBC', 'USO', 'UNG']  # Sample commodity ETFs
    
    for i in range(num_selections):
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


def reits_selection_dummy(regions: Optional[List[str]] = None,
                         sectors: Optional[List[str]] = None,
                         weight: float = 0.0) -> Dict[str, Any]:
    """
    Dummy function for REITs selection - placeholder implementation.
    
    Args:
        regions: List of allowed regions
        sectors: List of allowed sectors (not applicable for REITs)
        weight: Weight allocation for REITs asset class
        
    Returns:
        Dictionary with dummy REITs selection results (exactly 3 selections)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing REITs with weight allocation: {weight:.1%}")
    
    # Simulate some processing time
    time.sleep(0.4)
    
    # Always return exactly 3 REITs selections
    num_selections = 3
    
    dummy_selections = []
    reits_tickers = ['VNQ', 'SCHH', 'IYR', 'RWR', 'VNQI']  # Sample REITs ETFs
    
    for i in range(num_selections):
        ticker = reits_tickers[i]
        dummy_selections.append({
            'ticker': ticker,
            'asset_class': 'reits',
            'score': 82.0 - (i * 2),  # Decreasing scores
            'dividend_yield': 3.5 - (i * 0.2),
            'property_type': ['Office', 'Retail', 'Industrial', 'Residential', 'Healthcare'][i % 5],
            'recommendation': 'BUY' if i < 3 else 'HOLD',
            'allocation_weight': weight / num_selections  # Distribute weight among selections
        })
    
    return {
        'success': True,
        'selection_count': len(dummy_selections),
        'selections': dummy_selections,
        'processing_time': 0.4,
        'total_weight': weight,
        'message': f'Dummy REITs selection completed with {weight:.1%} allocation'
    }


def crypto_selection_dummy(regions: Optional[List[str]] = None,
                          sectors: Optional[List[str]] = None,
                          weight: float = 0.0) -> Dict[str, Any]:
    """
    Dummy function for crypto selection - placeholder implementation.
    
    Args:
        regions: List of allowed regions
        sectors: List of allowed sectors (not applicable for crypto)
        weight: Weight allocation for crypto asset class
        
    Returns:
        Dictionary with dummy crypto selection results (exactly 3 selections)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing crypto with weight allocation: {weight:.1%}")
    
    # Simulate some processing time
    time.sleep(0.2)
    
    # Always return exactly 3 crypto selections
    num_selections = 3
    
    dummy_selections = []
    crypto_tickers = ['BTC-USD', 'GBTC', 'BITO', 'ETHE', 'COIN']  # Sample crypto assets
    
    for i in range(num_selections):
        ticker = crypto_tickers[i]
        dummy_selections.append({
            'ticker': ticker,
            'asset_class': 'crypto',
            'score': 75.0 - (i * 4),  # Decreasing scores
            'volatility': 40.0 + (i * 5),
            'market_cap_rank': i + 1,
            'recommendation': 'BUY' if i < 2 else 'HOLD',
            'allocation_weight': weight / num_selections  # Distribute weight among selections
        })
    
    return {
        'success': True,
        'selection_count': len(dummy_selections),
        'selections': dummy_selections,
        'processing_time': 0.2,
        'total_weight': weight,
        'message': f'Dummy crypto selection completed with {weight:.1%} allocation'
    }


def hong_kong_equity_selection_dummy(regions: Optional[List[str]] = None,
                                    sectors: Optional[List[str]] = None,
                                    weight: float = 0.0) -> Dict[str, Any]:
    """
    Dummy function for Hong Kong equity selection - placeholder implementation.
    
    Args:
        regions: List of allowed regions
        sectors: List of allowed sectors
        weight: Weight allocation for Hong Kong equity asset class
        
    Returns:
        Dictionary with dummy Hong Kong equity selection results (exactly 3 selections)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing Hong Kong equity with weight allocation: {weight:.1%}")
    
    # Simulate some processing time
    time.sleep(0.6)
    
    # Always return exactly 3 Hong Kong equity selections
    num_selections = 3
    
    dummy_selections = []
    hk_tickers = ['0700.HK', '0988.HK', '0939.HK', 'EWH', 'FXI', 'YINN']  # Sample HK tickers
    
    for i in range(num_selections):
        ticker = hk_tickers[i]
        dummy_selections.append({
            'ticker': ticker,
            'asset_class': 'hong_kong_equity',
            'score': 78.0 - (i * 2),  # Decreasing scores
            'sector': ['Technology', 'Financials', 'Real Estate', 'Consumer', 'Healthcare', 'Energy'][i % 6],
            'market_cap': 'Large' if i < 3 else 'Mid',
            'recommendation': 'BUY' if i < 3 else 'HOLD',
            'allocation_weight': weight / num_selections  # Distribute weight among selections
        })
    
    return {
        'success': True,
        'selection_count': len(dummy_selections),
        'selections': dummy_selections,
        'processing_time': 0.6,
        'total_weight': weight,
        'message': f'Dummy Hong Kong equity selection completed with {weight:.1%} allocation'
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
    
    Calls the equity selection agent for the US_EQUITIES asset class.
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
        
        # Check if US_EQUITIES processing is needed
        if 'US_EQUITIES' not in asset_classes_present:
            logger.info("No US equity allocation found - skipping equity selection")
            state["equity_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No US equity allocation to process'
            }
            return state
        
        # Get US equity weight
        equity_weight = asset_class_weights.get('US_EQUITIES', 0.0)
        
        logger.info(f"Processing US equity with {equity_weight:.1%} allocation...")
        
        # Call the equity selection agent
        equity_results = run_equity_selection(
            regions=regions,
            sectors=sectors,
            force_refresh=False
        )
        
        # Process and store results
        if equity_results['success']:
            logger.info(f"US equity selection completed successfully")
            logger.info(f"Selected {equity_results.get('final_selection_count', 0)} equity candidates")
            
            # Convert DataFrame to dictionary format if needed
            final_selections = equity_results.get('final_selections')
            if final_selections is not None and hasattr(final_selections, 'to_dict'):
                selections_dict = final_selections.to_dict('records')
            else:
                selections_dict = final_selections or []
            
            # Limit to exactly 3 selections
            if len(selections_dict) > 3:
                logger.info(f"Limiting equity selections from {len(selections_dict)} to 3")
                selections_dict = selections_dict[:3]
            
            # Add weight information to each selection
            if selections_dict and equity_weight > 0:
                individual_weight = equity_weight / len(selections_dict)
                for selection in selections_dict:
                    selection['allocation_weight'] = individual_weight
            
            state["equity_results"] = {
                'success': True,
                'selection_count': len(selections_dict),
                'selections': selections_dict,
                'execution_time': equity_results.get('execution_time', 0),
                'screening_summary': equity_results.get('screening_summary'),
                'total_weight': equity_weight,
                'message': f'US equity selection completed with {equity_weight:.1%} allocation'
            }
        else:
            logger.error(f"US equity selection failed: {equity_results.get('error', 'Unknown error')}")
            state["equity_results"] = {
                'success': False,
                'selection_count': 0,
                'selections': [],
                'error': equity_results.get('error', 'Unknown error'),
                'total_weight': equity_weight,
                'message': 'US equity selection failed'
            }
        
        return state
        
    except Exception as e:
        logger.error(f"US equity selection processing failed: {str(e)}")
        equity_weight = state["asset_class_weights"].get('US_EQUITIES', 0.0)
        state["equity_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'total_weight': equity_weight,
            'message': 'US equity selection processing failed'
        }
        return state


def bonds_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 3: Process bond selections using the dummy bonds function
    
    Calls the dummy bond selection function for the BONDS asset class.
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
        
        # Check if BONDS processing is needed
        if 'BONDS' not in asset_classes_present:
            logger.info("No bond allocation found - skipping bonds selection")
            state["bonds_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No bond allocation to process'
            }
            return state
        
        # Get bond weight
        bond_weight = asset_class_weights.get('BONDS', 0.0)
        
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
        bond_weight = state["asset_class_weights"].get('BONDS', 0.0)
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
    
    Calls the dummy commodity selection function for the COMMODITIES asset class.
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
        
        # Check if COMMODITIES processing is needed
        if 'COMMODITIES' not in asset_classes_present:
            logger.info("No commodity allocation found - skipping commodity selection")
            state["commodity_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No commodity allocation to process'
            }
            return state
        
        # Get commodity weight
        commodity_weight = asset_class_weights.get('COMMODITIES', 0.0)
        
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
        commodity_weight = state["asset_class_weights"].get('COMMODITIES', 0.0)
        state["commodity_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'total_weight': commodity_weight,
            'message': 'Commodity selection processing failed'
        }
        return state


def reits_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 3.6: Process REITs selections using the dummy REITs function
    
    Calls the dummy REITs selection function for the REITS asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("REITS SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_class_weights = state["asset_class_weights"]
        asset_classes_present = state["asset_classes_present"]
        regions = state["regions"]
        sectors = state["sectors"]
        
        # Check if REITS processing is needed
        if 'REITS' not in asset_classes_present:
            logger.info("No REITs allocation found - skipping REITs selection")
            state["reits_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No REITs allocation to process'
            }
            return state
        
        # Get REITs weight
        reits_weight = asset_class_weights.get('REITS', 0.0)
        
        logger.info(f"Processing REITs with {reits_weight:.1%} allocation...")
        
        # Call the dummy REITs selection function
        reits_results = reits_selection_dummy(
            regions=regions,
            sectors=sectors,
            weight=reits_weight
        )
        
        # Store results
        state["reits_results"] = reits_results
        
        logger.info(f"REITs selection completed: {reits_results['selection_count']} selections")
        return state
        
    except Exception as e:
        logger.error(f"REITs selection processing failed: {str(e)}")
        reits_weight = state["asset_class_weights"].get('REITS', 0.0)
        state["reits_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'total_weight': reits_weight,
            'message': 'REITs selection processing failed'
        }
        return state


def crypto_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 3.7: Process crypto selections using the dummy crypto function
    
    Calls the dummy crypto selection function for the CRYPTO asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("CRYPTO SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_class_weights = state["asset_class_weights"]
        asset_classes_present = state["asset_classes_present"]
        regions = state["regions"]
        sectors = state["sectors"]
        
        # Check if CRYPTO processing is needed
        if 'CRYPTO' not in asset_classes_present:
            logger.info("No crypto allocation found - skipping crypto selection")
            state["crypto_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No crypto allocation to process'
            }
            return state
        
        # Get crypto weight
        crypto_weight = asset_class_weights.get('CRYPTO', 0.0)
        
        logger.info(f"Processing crypto with {crypto_weight:.1%} allocation...")
        
        # Call the dummy crypto selection function
        crypto_results = crypto_selection_dummy(
            regions=regions,
            sectors=sectors,
            weight=crypto_weight
        )
        
        # Store results
        state["crypto_results"] = crypto_results
        
        logger.info(f"Crypto selection completed: {crypto_results['selection_count']} selections")
        return state
        
    except Exception as e:
        logger.error(f"Crypto selection processing failed: {str(e)}")
        crypto_weight = state["asset_class_weights"].get('CRYPTO', 0.0)
        state["crypto_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'total_weight': crypto_weight,
            'message': 'Crypto selection processing failed'
        }
        return state


def hong_kong_equity_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 3.8: Process Hong Kong equity selections using the dummy HK equity function
    
    Calls the dummy Hong Kong equity selection function for the HONG_KONG_EQUITIES asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("HONG KONG EQUITY SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_class_weights = state["asset_class_weights"]
        asset_classes_present = state["asset_classes_present"]
        regions = state["regions"]
        sectors = state["sectors"]
        
        # Check if HONG_KONG_EQUITIES processing is needed
        if 'HONG_KONG_EQUITIES' not in asset_classes_present:
            logger.info("No Hong Kong equity allocation found - skipping HK equity selection")
            state["hong_kong_equity_results"] = {
                'success': True,
                'selection_count': 0,
                'selections': [],
                'message': 'No Hong Kong equity allocation to process'
            }
            return state
        
        # Get Hong Kong equity weight
        hk_equity_weight = asset_class_weights.get('HONG_KONG_EQUITIES', 0.0)
        
        logger.info(f"Processing Hong Kong equity with {hk_equity_weight:.1%} allocation...")
        
        # Call the dummy Hong Kong equity selection function
        hk_equity_results = hong_kong_equity_selection_dummy(
            regions=regions,
            sectors=sectors,
            weight=hk_equity_weight
        )
        
        # Store results
        state["hong_kong_equity_results"] = hk_equity_results
        
        logger.info(f"Hong Kong equity selection completed: {hk_equity_results['selection_count']} selections")
        return state
        
    except Exception as e:
        logger.error(f"Hong Kong equity selection processing failed: {str(e)}")
        hk_equity_weight = state["asset_class_weights"].get('HONG_KONG_EQUITIES', 0.0)
        state["hong_kong_equity_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'total_weight': hk_equity_weight,
            'message': 'Hong Kong equity selection processing failed'
        }
        return state


def aggregation_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 4: Aggregate results from all asset class selections
    
    Combines results from all asset classes into final output.
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
        reits_results = state.get("reits_results") or {}
        crypto_results = state.get("crypto_results") or {}
        hong_kong_equity_results = state.get("hong_kong_equity_results") or {}
        
        # Aggregate all selections
        all_selections = []
        
        # Add equity selections
        if equity_results.get('success') and equity_results.get('selections'):
            equity_selections = equity_results['selections']
            if equity_selections:
                all_selections.extend(equity_selections)
                logger.info(f"Added {len(equity_selections)} US equity selections")
        
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
        
        # Add REITs selections
        if reits_results.get('success') and reits_results.get('selections'):
            reits_selections = reits_results['selections']
            if reits_selections:
                all_selections.extend(reits_selections)
                logger.info(f"Added {len(reits_selections)} REITs selections")
        
        # Add crypto selections
        if crypto_results.get('success') and crypto_results.get('selections'):
            crypto_selections = crypto_results['selections']
            if crypto_selections:
                all_selections.extend(crypto_selections)
                logger.info(f"Added {len(crypto_selections)} crypto selections")
        
        # Add Hong Kong equity selections
        if hong_kong_equity_results.get('success') and hong_kong_equity_results.get('selections'):
            hk_equity_selections = hong_kong_equity_results['selections']
            if hk_equity_selections:
                all_selections.extend(hk_equity_selections)
                logger.info(f"Added {len(hk_equity_selections)} Hong Kong equity selections")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Create final results summary in the format expected by main_agent.py
        # Structure: { "asset_class": { "selections": [...], "selection_count": N, "success": bool } }
        final_selections = {}
        
        # Add equity results
        if equity_results:
            final_selections['US_EQUITIES'] = {
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
            final_selections['BONDS'] = {
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
            final_selections['COMMODITIES'] = {
                'selections': commodity_results.get('selections', []),
                'selection_count': commodity_results.get('selection_count', 0),
                'success': commodity_results.get('success', False),
                'processing_time': commodity_results.get('processing_time', 0),
                'message': commodity_results.get('message', ''),
                'execution_time': execution_time,
                'total_weight': commodity_results.get('total_weight', 0.0)
            }
        
        # Add REITs results
        if reits_results:
            final_selections['REITS'] = {
                'selections': reits_results.get('selections', []),
                'selection_count': reits_results.get('selection_count', 0),
                'success': reits_results.get('success', False),
                'processing_time': reits_results.get('processing_time', 0),
                'message': reits_results.get('message', ''),
                'execution_time': execution_time,
                'total_weight': reits_results.get('total_weight', 0.0)
            }
        
        # Add crypto results
        if crypto_results:
            final_selections['CRYPTO'] = {
                'selections': crypto_results.get('selections', []),
                'selection_count': crypto_results.get('selection_count', 0),
                'success': crypto_results.get('success', False),
                'processing_time': crypto_results.get('processing_time', 0),
                'message': crypto_results.get('message', ''),
                'execution_time': execution_time,
                'total_weight': crypto_results.get('total_weight', 0.0)
            }
        
        # Add Hong Kong equity results
        if hong_kong_equity_results:
            final_selections['HONG_KONG_EQUITIES'] = {
                'selections': hong_kong_equity_results.get('selections', []),
                'selection_count': hong_kong_equity_results.get('selection_count', 0),
                'success': hong_kong_equity_results.get('success', False),
                'processing_time': hong_kong_equity_results.get('processing_time', 0),
                'message': hong_kong_equity_results.get('message', ''),
                'execution_time': execution_time,
                'total_weight': hong_kong_equity_results.get('total_weight', 0.0)
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
                'reits_success': reits_results.get('success', False),
                'crypto_success': crypto_results.get('success', False),
                'hong_kong_equity_success': hong_kong_equity_results.get('success', False),
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
    workflow.add_node("reits_selection", reits_selection_node)
    workflow.add_node("crypto_selection", crypto_selection_node)
    workflow.add_node("hong_kong_equity_selection", hong_kong_equity_selection_node)
    workflow.add_node("aggregation", aggregation_node)
    
    # Add edges to define the flow
    workflow.add_edge(START, "initialization")
    workflow.add_edge("initialization", "equity_selection")
    workflow.add_edge("equity_selection", "bonds_selection")
    workflow.add_edge("bonds_selection", "commodity_selection")
    workflow.add_edge("commodity_selection", "reits_selection")
    workflow.add_edge("reits_selection", "crypto_selection")
    workflow.add_edge("crypto_selection", "hong_kong_equity_selection")
    workflow.add_edge("hong_kong_equity_selection", "aggregation")
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
        # Example usage with sample data using portfolio_construction.py asset class names
        sample_asset_class_weights = {
            'US_EQUITIES': 0.4,
            'BONDS': 0.3,
            'COMMODITIES': 0.15,
            'REITS': 0.1,
            'CRYPTO': 0.05
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
