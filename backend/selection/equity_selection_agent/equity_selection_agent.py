#!/usr/bin/env python3
"""
Equity Selection Agent (ESA) V2.0 - LangGraph Workflow Implementation

This script manages the entire ESA workflow using LangGraph:
1. Data loading from database
2. Feature engineering
3. Screening
4. Ranking and selection
5. Agent output

Usage:
    python main.py [--config config.json] [--regions US HK] [--sectors Technology Financial]
"""

import sys
import os
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config, load_config_from_env
from src.data_access import ensure_data_available, get_universe, get_price_data, get_fundamental_data
from src.feature_engine import FundamentalCalculator, TechnicalAnalyzer, calculate_composite_features
from src.selector_logic import EquityScreener
from src.ranking_engine import RankingEngine


# State definition for the workflow
class EquitySelectionAgentState(TypedDict):
    """State object that flows through the workflow nodes"""
    # Configuration and parameters
    config: Config
    regions: Optional[List[str]]
    sectors: Optional[List[str]]
    enable_qualitative: bool
    force_refresh: bool
    start_time: float
    
    # Data objects - using Any to accommodate pandas DataFrames and Dicts
    universe_df: Optional[Any]  # pandas DataFrame
    price_data: Optional[Any]   # pandas DataFrame
    fundamental_data: Optional[Any]  # Dict[str, Dict[str, Any]]
    
    # Processing results - using Any for pandas DataFrames
    fundamental_features: Optional[Any]  # pandas DataFrame
    technical_features: Optional[Any]    # pandas DataFrame
    combined_features: Optional[Any]     # pandas DataFrame
    screened_data: Optional[Any]         # pandas DataFrame
    scored_data: Optional[Any]           # pandas DataFrame
    ranked_data: Optional[Any]           # pandas DataFrame
    final_selections: Optional[Any]      # pandas DataFrame
    
    # Metadata and results
    initial_universe_size: int
    screening_summary: Optional[Any]  # Dict[str, Any]
    execution_time: float
    
    # Status tracking
    success: bool
    error: Optional[str]


def setup_logging(config: Config) -> None:
    """Set up logging configuration"""
    log_level = getattr(logging, config.output.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format=config.output.log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(config.output.log_directory, 'esa_execution.log')
            )
        ]
    )


# =============================================================================
# WORKFLOW NODE FUNCTIONS
# =============================================================================

def data_loading_node(state: EquitySelectionAgentState) -> EquitySelectionAgentState:
    """
    Node 1: Data Loading from Database
    
    Loads stock universe and fetches price/fundamental data from database or CSV files.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("NODE 1: DATA LOADING")
    logger.info("="*50)
    
    try:
        config = state["config"]
        regions = state["regions"]
        force_refresh = state["force_refresh"]
        
        # Ensure data is available and fresh
        logger.info("Ensuring data availability...")
        max_age_hours = 1 if force_refresh else 24  # Force refresh if requested
        data_available = ensure_data_available(max_age_hours=max_age_hours)
        
        if not data_available:
            raise Exception("Failed to ensure data availability")
        
        # Load universe data
        logger.info("Loading universe data...")
        universe_df = get_universe()
        
        if universe_df is None or universe_df.empty:
            raise Exception("Failed to load universe data")
        
        # Filter by regions if specified
        if regions:
            logger.info(f"Filtering universe by regions: {regions}")
            universe_df = universe_df[universe_df['region'].isin(regions)]
        
        initial_universe_size = len(universe_df)
        logger.info(f"Loaded universe: {initial_universe_size} stocks")
        
        # Get ticker list
        tickers = universe_df['ticker'].tolist()
        
        # Load price data
        logger.info("Loading historical price data...")
        price_data = get_price_data(tickers)
        
        if price_data is None or price_data.empty:
            raise Exception("Failed to load price data")
        
        # Load fundamental data
        logger.info("Loading fundamental data...")
        fundamental_data = get_fundamental_data(tickers)
        
        if fundamental_data is None or fundamental_data.empty:
            raise Exception("Failed to load fundamental data")
        
        # Convert fundamental data to dictionary format expected by feature engine
        fundamental_data_dict = {}
        for _, row in fundamental_data.iterrows():
            ticker = row['ticker']
            fundamental_data_dict[ticker] = row.to_dict()
        
        # Update state
        state.update({
            "universe_df": universe_df,
            "price_data": price_data,
            "fundamental_data": fundamental_data_dict,
            "initial_universe_size": initial_universe_size
        })
        
        logger.info(f"Data loading completed successfully for {initial_universe_size} stocks")
        return state
        
    except Exception as e:
        logger.error(f"Data loading failed: {str(e)}")
        state.update({
            "success": False,
            "error": f"Data loading failed: {str(e)}"
        })
        return state


def feature_engineering_node(state: EquitySelectionAgentState) -> EquitySelectionAgentState:
    """
    Node 2: Feature Engineering
    
    Calculates fundamental and technical features for all stocks.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("NODE 2: FEATURE ENGINEERING")
    logger.info("="*50)
    
    try:
        config = state["config"]
        universe_df = state["universe_df"]
        price_data = state["price_data"]
        fundamental_data = state["fundamental_data"]
        
        # Validate inputs
        if universe_df is None:
            raise Exception("Universe data is None")
        if price_data is None:
            raise Exception("Price data is None")
        if fundamental_data is None:
            raise Exception("Fundamental data is None")
        
        # Initialize calculators
        fundamental_calculator = FundamentalCalculator(config)
        technical_analyzer = TechnicalAnalyzer(config)
        
        # Calculate fundamental features
        logger.info("Calculating fundamental metrics...")
        fundamental_features = fundamental_calculator.process_fundamental_data(
            fundamental_data, universe_df
        )
        
        # Calculate technical features
        logger.info("Calculating technical indicators...")
        technical_features = technical_analyzer.process_technical_data(price_data)
        
        # Combine features
        combined_features = calculate_composite_features(
            fundamental_features, technical_features
        )
        
        logger.info(f"Combined features calculated for {len(combined_features)} stocks")
        
        # Update state
        state.update({
            "fundamental_features": fundamental_features,
            "technical_features": technical_features,
            "combined_features": combined_features
        })
        
        logger.info("Feature engineering completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Feature engineering failed: {str(e)}")
        state.update({
            "success": False,
            "error": f"Feature engineering failed: {str(e)}"
        })
        return state


def screening_node(state: EquitySelectionAgentState) -> EquitySelectionAgentState:
    """
    Node 3: Screening
    
    Applies screening filters and qualitative analysis to narrow down candidates.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("NODE 3: SCREENING")
    logger.info("="*50)
    
    try:
        config = state["config"]
        combined_features = state["combined_features"]
        fundamental_data = state["fundamental_data"]
        regions = state["regions"]
        sectors = state["sectors"]
        enable_qualitative = state["enable_qualitative"]
        
        # Validate inputs
        if combined_features is None:
            raise Exception("Combined features data is None")
        if fundamental_data is None:
            raise Exception("Fundamental data is None")
        
        # Initialize screener
        screener = EquityScreener(config)
        
        # Enable qualitative analysis if requested
        if enable_qualitative:
            screener.enable_qualitative_analysis(True)
        
        # Apply screening pipeline
        screened_data = screener.apply_full_screening_pipeline(
            combined_features,
            allowed_regions=regions,
            allowed_sectors=sectors
        )
        
        # Add qualitative scores
        if enable_qualitative:
            logger.info("Adding qualitative analysis...")
            screened_data = screener.add_qualitative_scores(
                screened_data, fundamental_data
            )
        
        logger.info(f"Screening completed: {len(screened_data)} stocks survived")
        
        # Get screening summary
        screening_summary = screener.get_screening_summary()
        
        # Update state
        state.update({
            "screened_data": screened_data,
            "screening_summary": screening_summary
        })
        
        logger.info("Screening completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Screening failed: {str(e)}")
        state.update({
            "success": False,
            "error": f"Screening failed: {str(e)}"
        })
        return state


def ranking_selection_node(state: EquitySelectionAgentState) -> EquitySelectionAgentState:
    """
    Node 4: Ranking and Selection (Final Node)
    
    Calculates composite scores, ranks candidates, and selects top stocks.
    """
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*50)
    logger.info("NODE 4: RANKING AND SELECTION")
    logger.info("="*50)
    
    try:
        config = state["config"]
        screened_data = state["screened_data"]
        start_time = state["start_time"]
        initial_universe_size = state["initial_universe_size"]
        
        # Validate inputs
        if screened_data is None:
            raise Exception("Screened data is None")
        
        # Initialize ranking engine
        ranking_engine = RankingEngine(config)
        
        # Calculate composite scores
        logger.info("Calculating composite scores...")
        scored_data = ranking_engine.calculate_composite_score(screened_data)
        
        # Rank candidates
        ranked_data = ranking_engine.rank_candidates(scored_data)
        
        # Select top candidates
        final_selections = ranking_engine.select_top_candidates(ranked_data)
        
        logger.info(f"Selected top {len(final_selections)} candidates")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Update state with final results
        state.update({
            "scored_data": scored_data,
            "ranked_data": ranked_data,
            "final_selections": final_selections,
            "execution_time": execution_time,
            "success": True
        })
        
        # Generate summary
        logger.info("\n" + "="*50)
        logger.info("EXECUTION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total execution time: {execution_time:.2f} seconds")
        logger.info(f"Initial universe: {initial_universe_size} stocks")
        logger.info(f"Final selection: {len(final_selections)} stocks")
        logger.info(f"Success rate: {len(final_selections)/initial_universe_size*100:.1f}%")
        
        # Top 5 selections preview
        if hasattr(final_selections, 'empty') and not final_selections.empty:
            logger.info("\nTOP 5 SELECTIONS:")
            logger.info("-" * 40)
            for i, (_, row) in enumerate(final_selections.head(5).iterrows(), 1):
                score = row.get('final_score', 0)
                ticker = row.get('ticker', 'Unknown')
                sector = row.get('sector', 'Unknown')
                logger.info(f"{i}. {ticker} ({sector}) - Score: {score:.2f}")
        
        logger.info("\n" + "="*60)
        logger.info("EQUITY SELECTION AGENT - EXECUTION COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        return state
        
    except Exception as e:
        execution_time = time.time() - state["start_time"]
        logger.error(f"Ranking and selection failed: {str(e)}")
        state.update({
            "success": False,
            "error": f"Ranking and selection failed: {str(e)}",
            "execution_time": execution_time
        })
        return state


# =============================================================================
# WORKFLOW CREATION AND EXECUTION
# =============================================================================

def create_workflow() -> CompiledStateGraph:
    """
    Create and compile the LangGraph workflow for the Equity Selection Agent.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the state graph
    workflow = StateGraph(EquitySelectionAgentState)
    
    # Add nodes
    workflow.add_node("data_loading", data_loading_node)
    workflow.add_node("feature_engineering", feature_engineering_node)
    workflow.add_node("screening", screening_node)
    workflow.add_node("ranking_selection", ranking_selection_node)
    
    # Add edges to define the flow
    workflow.add_edge(START, "data_loading")
    workflow.add_edge("data_loading", "feature_engineering")
    workflow.add_edge("feature_engineering", "screening")
    workflow.add_edge("screening", "ranking_selection")
    workflow.add_edge("ranking_selection", END)
    
    # Compile the workflow
    return workflow.compile()


def run_agent_workflow(regions: Optional[List[str]] = None,
                      sectors: Optional[List[str]] = None,
                      enable_qualitative: bool = False,
                      force_refresh: bool = False,
                      config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Run the Equity Selection Agent using LangGraph workflow.
    
    Args:
        regions: List of allowed regions ('US', 'HK', etc.)
        sectors: List of allowed sectors
        enable_qualitative: Whether to enable qualitative analysis
        force_refresh: Force refresh of cached data
        config: Configuration object (uses default if None)
        
    Returns:
        Dictionary with execution results and file paths
    """
    start_time = time.time()
    
    if config is None:
        config = Config()
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("EQUITY SELECTION AGENT (ESA) - LANGGRAPH WORKFLOW")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Target stock count: {config.output.target_stock_count}")
    logger.info(f"Allowed regions: {regions or 'All'}")
    logger.info(f"Allowed sectors: {sectors or 'All'}")
    logger.info(f"Qualitative analysis: {'Enabled' if enable_qualitative else 'Disabled'}")
    
    try:
        # Create the workflow
        workflow = create_workflow()
        
        # Initialize the state
        initial_state: EquitySelectionAgentState = {
            # Configuration and parameters
            "config": config,
            "regions": regions,
            "sectors": sectors,
            "enable_qualitative": enable_qualitative,
            "force_refresh": force_refresh,
            "start_time": start_time,
            
            # Data objects (initialized to None)
            "universe_df": None,
            "price_data": None,
            "fundamental_data": None,
            
            # Processing results (initialized to None)
            "fundamental_features": None,
            "technical_features": None,
            "combined_features": None,
            "screened_data": None,
            "scored_data": None,
            "ranked_data": None,
            "final_selections": None,
            
            # Metadata and results
            "initial_universe_size": 0,
            "screening_summary": None,
            "execution_time": 0.0,
            
            # Status tracking
            "success": True,
            "error": None
        }
        
        # Execute the workflow
        logger.info("Starting LangGraph workflow execution...")
        final_state = workflow.invoke(initial_state)
        
        # Extract results
        if final_state["success"]:
            return {
                'success': True,
                'execution_time': final_state["execution_time"],
                'initial_universe_size': final_state["initial_universe_size"],
                'final_selection_count': len(final_state["final_selections"]) if final_state["final_selections"] is not None else 0,
                'final_selections': final_state["final_selections"],
                'screening_summary': final_state["screening_summary"],
                'scored_data': final_state["scored_data"],
                'ranked_data': final_state["ranked_data"]
            }
        else:
            return {
                'success': False,
                'execution_time': final_state["execution_time"],
                'error': final_state["error"]
            }
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"WORKFLOW EXECUTION FAILED after {execution_time:.2f} seconds: {str(e)}")
        logger.exception("Full error details:")
        
        return {
            'success': False,
            'execution_time': execution_time,
            'error': str(e)
        }


def main() -> int:
    """Main entry point for standalone execution"""
    try:
        # Use default configuration for standalone execution
        config = load_config_from_env()
        
        # Set up logging
        setup_logging(config)
        
        # Run the agent workflow with default settings
        results = run_agent_workflow(config=config)
        
        # Return appropriate exit code
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