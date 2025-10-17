"""
Enhanced Data Collection Script for Equity Selection Agent

This script uses the new EnhancedDataProvider with SQLite storage and incremental updates.
It supports three main operations:
- refresh: Complete universe rebuild (when S&P 500 composition changes)
- update: Incremental price + conditional fundamental updates
- load: Use existing cached data

Usage:
    python collect_data.py [--operation refresh|update|load] [--db-path data/stock_data.db]

Examples:
    python src/collect_data.py --operation refresh     # Full refresh
    python src/collect_data.py --operation update      # Incremental update (daily)
    python src/collect_data.py --operation load        # Just load existing data
"""

import os
import argparse
import logging

from .stock_database import StockDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """
    Main data collection workflow using enhanced provider.
    """
    parser = argparse.ArgumentParser(description='Enhanced stock data collection with SQLite storage')
    parser.add_argument('--operation', choices=['refresh', 'update', 'load'], default='update',
                       help='Operation to perform: refresh (full rebuild), update (incremental), load (use cached)')
    parser.add_argument('--db-path', default='data/stock_data.db', 
                       help='SQLite database path (default: data/stock_data.db)')
    parser.add_argument('--include-us', action='store_true', default=True,
                       help='Include US tickers (default: True)')
    parser.add_argument('--include-hk', action='store_true', default=True,
                       help='Include Hong Kong tickers (default: True)')
    parser.add_argument('--fundamental-days', type=int, default=7,
                       help='Days threshold for fundamental updates (default: 7)')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    os.makedirs(os.path.dirname(args.db_path), exist_ok=True)
    
    logger.info("="*60)
    logger.info("STARTING ENHANCED DATA COLLECTION")
    logger.info("="*60)
    logger.info(f"Operation: {args.operation}")
    logger.info(f"Database: {args.db_path}")
    logger.info(f"Include US: {args.include_us}, Include HK: {args.include_hk}")
    
    try:
        provider = StockDatabase(args.db_path)
        
        # Get data summary before operation
        summary_before = provider.get_data_summary()
        logger.info("Database state before operation:")
        logger.info(f"  Universe: {summary_before['universe']['active_tickers']} active tickers")
        logger.info(f"  Price data: {summary_before['price_data']['total_records']} records")
        logger.info(f"  Fundamental data: {summary_before['fundamental_data']['total_records']} records")
        
        # Perform the requested operation
        if args.operation == "refresh":
            logger.info("Performing complete universe refresh...")
            universe_df = provider.refresh_universe(
                include_us=args.include_us,
                include_hk=args.include_hk
            )
            # After refresh, update all data
            update_results = provider.update_data(update_fundamentals=True)
            logger.info(f"Post-refresh update results: {update_results}")
            
        elif args.operation == "update":
            logger.info("Performing incremental data update...")
            update_results = provider.update_data()
            # Auto-decides on fundamentals based on 7-day threshold
            logger.info(f"Update results: {update_results}")
            
        elif args.operation == "load":
            logger.info("Loading existing data from database...")
            # No updates, just load existing data
            
        # Get final data for reporting
        universe_df = provider.get_universe()
        price_data_df = provider.get_price_data()
        fundamental_data_df = provider.get_fundamental_data()
        
        # Get data summary after operation
        summary_after = provider.get_data_summary()
        
        # Log final results
        logger.info("="*60)
        logger.info("ENHANCED DATA COLLECTION COMPLETED")
        logger.info("="*60)
        
        if not universe_df.empty:
            logger.info(f"Universe: {len(universe_df)} active tickers")
            if 'sector' in universe_df.columns:
                logger.info(f"  Sectors: {universe_df['sector'].nunique()} unique sectors")
            if 'region' in universe_df.columns:
                logger.info(f"  Regions: {universe_df['region'].nunique()} regions")
        
        if not price_data_df.empty:
            logger.info(f"Price data: {len(price_data_df)} total records")
            logger.info(f"  Tickers with data: {price_data_df['ticker'].nunique()}")
            if 'date' in price_data_df.columns:
                logger.info(f"  Date range: {price_data_df['date'].min()} to {price_data_df['date'].max()}")
        
        if not fundamental_data_df.empty:
            logger.info(f"Fundamental data: {len(fundamental_data_df)} records")
            logger.info(f"  Companies with market cap: {fundamental_data_df['market_cap'].notna().sum()}")
        
        logger.info(f"SQLite database saved: {args.db_path}")
        logger.info("Use EnhancedDataProvider to access this data in other scripts")
        
        # Show what changed
        if args.operation in ["refresh", "update"]:
            price_diff = summary_after['price_data']['total_records'] - summary_before['price_data']['total_records']
            fund_diff = summary_after['fundamental_data']['total_records'] - summary_before['fundamental_data']['total_records']
            logger.info(f"Changes: +{price_diff} price records, +{fund_diff} fundamental records")
        
    except Exception as e:
        logger.error(f"Error during enhanced data collection: {e}")
        raise


if __name__ == "__main__":
    main()