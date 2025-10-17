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

# LangGraph imports (lazy-guarded)
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.state import CompiledStateGraph
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    StateGraph = None  # type: ignore
    START = None  # type: ignore
    END = None  # type: ignore
    CompiledStateGraph = None  # type: ignore
    _LANGGRAPH_AVAILABLE = False

# Import equity selection agent
try:
    # Prefer absolute import relative to backend folder execution
    from selection.equity_selection_agent.src import equity_selection_agent as esa_module
    run_equity_selection = esa_module.run_agent_workflow
    EQUITY_AGENT_AVAILABLE = True
    try:
        logging.getLogger(__name__).info("selection_agent: using absolute import 'selection.equity_selection_agent.src'")
    except Exception:
        pass
except ImportError:
    try:
        # Fallback to package-relative import when imported as part of selection package
        from .equity_selection_agent.src import equity_selection_agent as esa_module
        run_equity_selection = esa_module.run_agent_workflow
        EQUITY_AGENT_AVAILABLE = True
        try:
            logging.getLogger(__name__).info("selection_agent: using relative import '.equity_selection_agent.src'")
        except Exception:
            pass
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
    selected_tickers: Dict[str, List[str]]  # asset_class -> list of tickers mapping (e.g., {'equities': ['AAPL', 'MSFT'], 'bonds': ['BND']})
    
    # Processing metadata
    start_time: float
    execution_time: float
    asset_classes_present: Set[str]
    asset_classes_missing: Set[str]  # Asset classes not in selected_tickers that need processing
    
    # Results by asset class
    equity_results: Optional[Dict[str, Any]]
    bonds_results: Optional[Dict[str, Any]]
    commodity_results: Optional[Dict[str, Any]]
    gold_results: Optional[Dict[str, Any]]  # Updated to match new asset classes
    
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


def analyze_asset_classes(selected_tickers: Dict[str, List[str]]) -> tuple[Set[str], Set[str]]:
    """
    Analyze which asset classes are present in selected_tickers and which are missing.
    
    Args:
        selected_tickers: Dictionary mapping asset class to list of tickers
        
    Returns:
        Tuple of (present_asset_classes, missing_asset_classes)
    """
    # Supported asset classes as defined in profile_processor_agent.py
    supported_asset_classes = {"equities", "bonds", "commodities", "gold"}
    
    present_classes = set(selected_tickers.keys()) & supported_asset_classes
    missing_classes = supported_asset_classes - present_classes
    
    return present_classes, missing_classes


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


def gold_selection_dummy(regions: Optional[List[str]] = None,
                        sectors: Optional[List[str]] = None,
                        weight: float = 0.0) -> Dict[str, Any]:
    """
    Dummy function for gold selection - placeholder implementation.
    
    Args:
        regions: List of allowed regions
        sectors: List of allowed sectors (not applicable for gold)
        weight: Weight allocation for gold asset class
        
    Returns:
        Dictionary with dummy gold selection results (exactly 3 selections)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing gold with weight allocation: {weight:.1%}")
    
    # Simulate some processing time
    time.sleep(0.3)
    
    # Always return exactly 3 gold selections
    num_selections = 3
    
    dummy_selections = []
    gold_tickers = ['GLD', 'IAU', 'SGOL', 'BAR', 'OUNZ']  # Sample gold ETFs
    
    for i in range(num_selections):
        ticker = gold_tickers[i]
        dummy_selections.append({
            'ticker': ticker,
            'asset_class': 'gold',
            'score': 85.0 - (i * 2),  # Decreasing scores
            'expense_ratio': 0.25 + (i * 0.05),
            'metal_type': 'Physical Gold ETF',
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
        start_time = time.time()
        state["start_time"] = start_time
        
        # Get selected_tickers from state
        selected_tickers = state.get("selected_tickers", {})
        
        # Analyze which asset classes are present and missing
        asset_classes_present, asset_classes_missing = analyze_asset_classes(selected_tickers)
        
        logger.info(f"Selected tickers provided: {selected_tickers}")
        logger.info(f"Asset classes present: {asset_classes_present}")
        logger.info(f"Asset classes missing (need selection): {asset_classes_missing}")
        
        # Update state
        state["asset_classes_present"] = asset_classes_present
        state["asset_classes_missing"] = asset_classes_missing
        state["processing_summary"] = {
            "total_supported_classes": 4,  # equities, bonds, commodities, gold
            "classes_with_tickers": len(asset_classes_present),
            "classes_needing_selection": len(asset_classes_missing),
            "regions_filter": state.get("regions", ["US"]),
            "sectors_filter": state.get("sectors", None)
        }
        
        # Initialize all result fields to None
        state["equity_results"] = None
        state["bonds_results"] = None
        state["commodity_results"] = None
        state["gold_results"] = None
        state["final_selections"] = {}
        state["success"] = False
        state["error"] = None
        
        logger.info("✅ Initialization completed successfully")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {str(e)}")
        state["error"] = f"Initialization error: {str(e)}"
        state["success"] = False
        return state


def equity_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 2: Process equity selections using the equity_selection_agent
    
    Calls the equity selection agent for the equities asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("EQUITY SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_classes_missing = state.get("asset_classes_missing", set())
        regions = state.get("regions", ["US"])
        sectors = state.get("sectors", None)
        
        # Check if equities processing is needed
        if "equities" not in asset_classes_missing:
            logger.info("Equities already provided by user - skipping equity selection")
            return state
        
        logger.info(f"Processing equities for regions: {regions}")
        if sectors:
            logger.info(f"Sectors filter: {sectors}")
        
        # Call the equity selection agent with regions parameter
        equity_results = run_equity_selection(
            regions=regions,
            sectors=sectors,
            force_refresh=False
        )
        
        # Process and store results
        if equity_results.get('success', False):
            logger.info(f"Equity selection completed successfully")
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
            
            # Format selections for consistency
            formatted_selections = []
            for i, selection in enumerate(selections_dict):
                formatted_selection = {
                    "ticker": selection.get("ticker", f"EQUITY_{i+1}"),
                    "score": selection.get("score", 85.0 - (i * 2)),
                    "reasoning": f"Equity selection {i+1}: {selection.get('reasoning', 'AI-selected equity')}",
                    "asset_class": "equities",
                    "sector": selection.get("sector", "Unknown"),
                    "recommendation": selection.get("recommendation", "BUY")
                }
                formatted_selections.append(formatted_selection)
            
            state["equity_results"] = {
                'success': True,
                'selection_count': len(formatted_selections),
                'selections': formatted_selections,
                'execution_time': equity_results.get('execution_time', 0),
                'screening_summary': equity_results.get('screening_summary'),
                'message': f'Equity selection completed with {len(formatted_selections)} selections'
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
    
    Calls the dummy bond selection function for the bonds asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("BONDS SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_classes_missing = state.get("asset_classes_missing", set())
        regions = state.get("regions", ["US"])
        sectors = state.get("sectors", None)
        
        # Check if bonds processing is needed
        if "bonds" not in asset_classes_missing:
            logger.info("Bonds already provided by user - skipping bonds selection")
            return state
        
        logger.info(f"Processing bonds for regions: {regions}")
        
        # Call the dummy bonds selection function
        bonds_results = bonds_selection_dummy(
            regions=regions,
            sectors=sectors,
            weight=0.1  # Default weight for bonds
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


def commodity_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 4: Process commodity selections using the dummy commodity function
    
    Calls the dummy commodity selection function for the commodities asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("COMMODITY SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_classes_missing = state.get("asset_classes_missing", set())
        regions = state.get("regions", ["US"])
        sectors = state.get("sectors", None)
        
        # Check if commodities processing is needed
        if "commodities" not in asset_classes_missing:
            logger.info("Commodities already provided by user - skipping commodity selection")
            return state
        
        logger.info(f"Processing commodities for regions: {regions}")
        
        # Call the dummy commodity selection function
        commodity_results = commodity_selection_dummy(
            regions=regions,
            sectors=sectors,
            weight=0.1  # Default weight for commodities
        )
        
        # Store results
        state["commodity_results"] = commodity_results
        
        logger.info(f"Commodity selection completed: {commodity_results['selection_count']} selections")
        return state
        
    except Exception as e:
        logger.error(f"Commodity selection processing failed: {str(e)}")
        state["commodity_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'message': 'Commodity selection processing failed'
        }
        return state


def gold_selection_node(state: SelectionAgentState) -> SelectionAgentState:
    """
    Node 5: Process gold selections using the dummy gold function
    
    Calls the dummy gold selection function for the gold asset class.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("GOLD SELECTION PROCESSING")
    logger.info("="*50)
    
    try:
        asset_classes_missing = state.get("asset_classes_missing", set())
        regions = state.get("regions", ["US"])
        sectors = state.get("sectors", None)
        
        # Check if gold processing is needed
        if "gold" not in asset_classes_missing:
            logger.info("Gold already provided by user - skipping gold selection")
            return state
        
        logger.info(f"Processing gold for regions: {regions}")
        
        # Call the dummy gold selection function
        gold_results = gold_selection_dummy(
            regions=regions,
            sectors=sectors,
            weight=0.1  # Default weight for gold
        )
        
        # Store results
        state["gold_results"] = gold_results
        
        logger.info(f"Gold selection completed: {gold_results['selection_count']} selections")
        return state
        
    except Exception as e:
        logger.error(f"Gold selection processing failed: {str(e)}")
        state["gold_results"] = {
            'success': False,
            'selection_count': 0,
            'selections': [],
            'error': str(e),
            'message': 'Gold selection processing failed'
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
    Node 6: Aggregate results from selected_tickers and new selections
    
    Combines existing tickers from user profile with new selections from agents.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("RESULTS AGGREGATION")
    logger.info("="*50)
    
    try:
        # Get selected_tickers from state
        selected_tickers = state.get("selected_tickers", {})
        asset_classes_present = state.get("asset_classes_present", set())
        asset_classes_missing = state.get("asset_classes_missing", set())
        
        final_selections = {}
        
        # Add existing tickers from user profile
        for asset_class in asset_classes_present:
            tickers = selected_tickers.get(asset_class, [])
            if tickers:
                final_selections[asset_class] = {
                    "success": True,
                    "selection_count": len(tickers),
                    "selections": [
                        {
                            "ticker": ticker,
                            "score": 90.0,  # High score for user-selected
                            "reasoning": "User-selected asset",
                            "asset_class": asset_class,
                            "recommendation": "USER_SELECTED"
                        }
                        for ticker in tickers
                    ],
                    "source": "user_profile"
                }
                logger.info(f"Added {len(tickers)} user-selected tickers for {asset_class}: {tickers}")
        
        # Add selections from agents for missing asset classes
        key_map = {
            "equities": "equity_results",
            "bonds": "bonds_results",
            "commodities": "commodity_results",
            "gold": "gold_results",
        }
        for asset_class in asset_classes_missing:
            result_key = key_map.get(asset_class, f"{asset_class}_results")
            results = state.get(result_key)
            
            if results and results.get("success", False):
                final_selections[asset_class] = results
                selections_count = len(results.get("selections", []))
                logger.info(f"Added {selections_count} agent selections for {asset_class}")
            else:
                logger.warning(f"No valid results for missing asset class: {asset_class}")
        
        # Update state
        state["final_selections"] = final_selections
        
        # Calculate execution time
        start_time = state.get("start_time", time.time())
        state["execution_time"] = time.time() - start_time
        
        # Generate processing summary
        total_selections = sum(
            len(selection_data.get("selections", [])) 
            for selection_data in final_selections.values()
        )
        
        state["processing_summary"].update({
            "final_asset_classes": list(final_selections.keys()),
            "total_final_selections": total_selections,
            "user_selected_classes": list(asset_classes_present),
            "agent_selected_classes": list(asset_classes_missing),
            "execution_completed": True
        })
        
        state["success"] = True
        
        logger.info("✅ Results aggregation completed successfully")
        logger.info(f"Final portfolio: {len(final_selections)} asset classes")
        logger.info(f"Total securities: {total_selections}")
        
        for asset_class, data in final_selections.items():
            count = len(data.get("selections", []))
            source = data.get("source", "agent")
            logger.info(f"  {asset_class}: {count} selections ({source})")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Results aggregation failed: {str(e)}")
        state["error"] = f"Aggregation error: {str(e)}"
        state["success"] = False
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
    if not _LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph is required to create the selection workflow. Please install 'langgraph'.")
    # Create the state graph
    workflow = StateGraph(SelectionAgentState)
    
    # Add nodes for the four asset classes only
    workflow.add_node("initialization", initialization_node)
    workflow.add_node("equity_selection", equity_selection_node)
    workflow.add_node("bonds_selection", bonds_selection_node)
    workflow.add_node("commodity_selection", commodity_selection_node)
    workflow.add_node("gold_selection", gold_selection_node)
    workflow.add_node("aggregation", aggregation_node)
    
    # Add edges to define the sequential flow
    workflow.add_edge(START, "initialization")
    workflow.add_edge("initialization", "equity_selection")
    workflow.add_edge("equity_selection", "bonds_selection")
    workflow.add_edge("bonds_selection", "commodity_selection")
    workflow.add_edge("commodity_selection", "gold_selection")
    workflow.add_edge("gold_selection", "aggregation")
    workflow.add_edge("aggregation", END)
    
    # Compile the workflow
    return workflow.compile()


def run_selection_agent(regions: Optional[List[str]] = None,
                       sectors: Optional[List[str]] = None,
                       selected_tickers: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """
    Run the Selection Agent using LangGraph workflow.
    
    Args:
        regions: List of allowed regions ('US', 'HK', etc.)
        sectors: List of allowed sectors
        selected_tickers: Dictionary mapping asset class to list of tickers
                         (e.g., {'equities': ['AAPL', 'MSFT'], 'bonds': ['BND']})
        
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
    if not selected_tickers:
        selected_tickers = {}
    
    # Create initial state
    initial_state: SelectionAgentState = {
        "regions": regions or ["US"],
        "sectors": sectors,
        "selected_tickers": selected_tickers,
        "start_time": start_time,
        "execution_time": 0.0,
        "asset_classes_present": set(),
        "asset_classes_missing": set(),
        "equity_results": None,
        "bonds_results": None,
        "commodity_results": None,
        "gold_results": None,
        "final_selections": {},
        "success": False,
        "error": None,
        "processing_summary": {},
        "summary_metadata": None
    }
    
    try:
        # Create and run workflow
        workflow = create_selection_workflow()
        result = workflow.invoke(initial_state)
        
        # Ensure JSON-serializable fields
        if isinstance(result.get("asset_classes_present"), set):
            result["asset_classes_present"] = list(result["asset_classes_present"])
        if isinstance(result.get("asset_classes_missing"), set):
            result["asset_classes_missing"] = list(result["asset_classes_missing"])
        if isinstance(result.get("processing_summary"), dict):
            if isinstance(result["processing_summary"].get("user_selected_classes"), set):
                result["processing_summary"]["user_selected_classes"] = list(result["processing_summary"]["user_selected_classes"])
            if isinstance(result["processing_summary"].get("agent_selected_classes"), set):
                result["processing_summary"]["agent_selected_classes"] = list(result["processing_summary"]["agent_selected_classes"])
        
        # Calculate final execution time
        result["execution_time"] = time.time() - start_time
        
        logger.info(f"Selection Agent completed in {result['execution_time']:.2f} seconds")
        
        if result.get("success", False):
            logger.info("✅ Selection Agent completed successfully")
        else:
            logger.error(f"❌ Selection Agent failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        error_msg = f"Selection Agent workflow failed: {str(e)}"
        logger.error(error_msg)
        resp = {
            'success': False,
            'error': error_msg,
            'execution_time': time.time() - start_time,
            'final_selections': {},
            'processing_summary': {}
        }
        return resp
    
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
        # Example usage with sample selected_tickers for testing
        sample_selected_tickers = {
            'equities': ['AAPL', 'MSFT'],  # User provided these
            'bonds': ['BND']               # User provided this
            # commodities and gold missing - will be selected by agents
        }
        
        # Run the selection agent
        results = run_selection_agent(
            regions=['US'],
            sectors=['Technology', 'Healthcare'],
            selected_tickers=sample_selected_tickers
        )
        
        # Print results summary
        if results['success']:
            print(f"\nExecution successful in {results['execution_time']:.2f} seconds")
            total_selections = sum(
                len(asset_data.get('selections', [])) 
                for asset_data in results.get('final_selections', {}).values()
            )
            print(f"Total selections: {total_selections}")
            
            # Print breakdown by asset class
            for asset_class, data in results.get('final_selections', {}).items():
                count = len(data.get('selections', []))
                source = data.get('source', 'agent')
                print(f"  {asset_class}: {count} selections ({source})")
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
