#!/usr/bin/env python3
"""
Main Orchestrator for Equity Selection Agent (ESA) V1.0

This script manages the entire ESA workflow:
1. Initialize configuration
2. Data acquisition  
3. Feature engineering
4. Screening
5. Ranking
6. Reporting

Usage:
    python main.py [--config config.json] [--regions US HK] [--sectors Technology Financial]
"""

import sys
import os
import argparse
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config, load_config_from_env
from src.data_provider import TickerManager, YFinanceClient
from src.feature_engine import FundamentalCalculator, TechnicalAnalyzer, calculate_composite_features
from src.selector_logic import EquityScreener
from src.agent_output import RankingEngine, Reporter


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


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Equity Selection Agent (ESA) V1.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Run with default settings
  python main.py --regions US                      # US stocks only
  python main.py --sectors Technology Financial    # Specific sectors only
  python main.py --target-count 50                 # Select top 50 stocks
  python main.py --enable-qualitative              # Enable LLM analysis
        """
    )
    
    parser.add_argument(
        '--config', type=str, default=None,
        help='Path to custom configuration file (JSON)'
    )
    
    parser.add_argument(
        '--regions', nargs='+', choices=['US', 'HK'], default=None,
        help='Allowed regions for stock selection'
    )
    
    parser.add_argument(
        '--sectors', nargs='+', default=None,
        help='Allowed sectors for stock selection'
    )
    
    parser.add_argument(
        '--target-count', type=int, default=None,
        help='Number of stocks to select'
    )
    
    parser.add_argument(
        '--enable-qualitative', action='store_true',
        help='Enable qualitative analysis (LLM-based)'
    )
    
    parser.add_argument(
        '--force-refresh', action='store_true',
        help='Force refresh of all cached data'
    )
    
    parser.add_argument(
        '--output-dir', type=str, default=None,
        help='Custom output directory for results'
    )
    
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def load_configuration(args: argparse.Namespace) -> Config:
    """Load and customize configuration based on arguments"""
    
    # Start with environment-based config
    config = load_config_from_env()
    
    # Apply command line overrides
    if args.target_count:
        config.output.target_stock_count = args.target_count
    
    if args.output_dir:
        config.output.log_directory = args.output_dir
        os.makedirs(args.output_dir, exist_ok=True)
    
    if args.verbose:
        config.output.log_level = "DEBUG"
    
    # TODO: Load custom config file if provided
    if args.config:
        logging.warning(f"Custom config file loading not yet implemented: {args.config}")
    
    return config


def run_agent(regions: Optional[List[str]] = None,
              sectors: Optional[List[str]] = None,
              enable_qualitative: bool = False,
              force_refresh: bool = False,
              config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Main agent execution function.
    
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
    logger.info("EQUITY SELECTION AGENT (ESA) V1.0 - STARTING EXECUTION")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Target stock count: {config.output.target_stock_count}")
    logger.info(f"Allowed regions: {regions or 'All'}")
    logger.info(f"Allowed sectors: {sectors or 'All'}")
    logger.info(f"Qualitative analysis: {'Enabled' if enable_qualitative else 'Disabled'}")
    
    try:
        # Step 1: Data Acquisition
        logger.info("\n" + "="*50)
        logger.info("STEP 1: DATA ACQUISITION")
        logger.info("="*50)
        
        # Initialize data providers
        ticker_manager = TickerManager(config.universe.universe_file)
        yfinance_client = YFinanceClient()
        
        # Get universe
        include_us = regions is None or 'US' in regions
        include_hk = regions is None or 'HK' in regions
        
        universe_df = ticker_manager.create_full_universe(
            include_us=include_us, 
            include_hk=include_hk
        )
        
        initial_universe_size = len(universe_df)
        logger.info(f"Loaded universe: {initial_universe_size} stocks")
        
        # Get ticker list
        tickers = universe_df['ticker'].tolist()
        
        # Fetch price data
        logger.info("Fetching historical price data...")
        price_data = yfinance_client.get_historical_data(
            tickers, 
            period=config.technical.lookback_period,
            force_refresh=force_refresh
        )
        
        # Fetch fundamental data
        logger.info("Fetching fundamental data...")
        fundamental_data = yfinance_client.get_fundamentals(
            tickers,
            force_refresh=force_refresh
        )
        
        # Step 2: Feature Engineering
        logger.info("\n" + "="*50)
        logger.info("STEP 2: FEATURE ENGINEERING")
        logger.info("="*50)
        
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
        
        # Step 3: Screening
        logger.info("\n" + "="*50)
        logger.info("STEP 3: SCREENING")
        logger.info("="*50)
        
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
        
        # Step 4: Ranking and Selection
        logger.info("\n" + "="*50)
        logger.info("STEP 4: RANKING AND SELECTION")
        logger.info("="*50)
        
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
        
        # Step 5: Reporting
        logger.info("\n" + "="*50)
        logger.info("STEP 5: REPORTING")
        logger.info("="*50)
        
        # Initialize reporter
        reporter = Reporter(config)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Generate complete report
        file_paths = reporter.generate_complete_report(
            final_selections,
            initial_universe_size,
            screening_summary,
            execution_time
        )
        
        # Step 6: Summary
        logger.info("\n" + "="*50)
        logger.info("EXECUTION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total execution time: {execution_time:.2f} seconds")
        logger.info(f"Initial universe: {initial_universe_size} stocks")
        logger.info(f"Final selection: {len(final_selections)} stocks")
        logger.info(f"Success rate: {len(final_selections)/initial_universe_size*100:.1f}%")
        logger.info("Generated output files:")
        for file_type, path in file_paths.items():
            logger.info(f"  {file_type.upper()}: {path}")
        
        # Top 5 selections preview
        if not final_selections.empty:
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
        
        return {
            'success': True,
            'execution_time': execution_time,
            'initial_universe_size': initial_universe_size,
            'final_selection_count': len(final_selections),
            'file_paths': file_paths,
            'final_selections': final_selections,
            'screening_summary': screening_summary
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"EXECUTION FAILED after {execution_time:.2f} seconds: {str(e)}")
        logger.exception("Full error details:")
        
        return {
            'success': False,
            'execution_time': execution_time,
            'error': str(e),
            'file_paths': {}
        }


def main() -> int:
    """Main entry point"""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Load configuration
        config = load_configuration(args)
        
        # Set up logging
        setup_logging(config)
        
        # Run the agent
        results = run_agent(
            regions=args.regions,
            sectors=args.sectors,
            enable_qualitative=args.enable_qualitative,
            force_refresh=args.force_refresh,
            config=config
        )
        
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