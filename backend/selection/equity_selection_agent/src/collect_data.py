"""
Data Collection Script for Equity Selection Agent

This script demonstrates how to use the enhanced data provider to collect
all necessary data and save it to CSV files for use by other components.

Usage:
    python collect_data.py [--refresh] [--period 1y] [--interval 1d]
"""

import sys
import os
import argparse
import logging

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_provider_enhanced import (
    run_full_data_collection, 
    load_latest_data, 
    should_refresh_data
)

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
    Main data collection workflow.
    """
    parser = argparse.ArgumentParser(description='Collect stock data for equity selection')
    parser.add_argument('--refresh', action='store_true', help='Force refresh of data')
    parser.add_argument('--period', default='1y', help='Data period (default: 1y)')
    parser.add_argument('--interval', default='1d', help='Data interval (default: 1d)')
    parser.add_argument('--output-dir', default='data', help='Output directory (default: data)')
    parser.add_argument('--max-age-hours', type=int, default=24, help='Max age in hours before refresh (default: 24)')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info("="*60)
    logger.info("STARTING DATA COLLECTION")
    logger.info("="*60)
    logger.info(f"Period: {args.period}, Interval: {args.interval}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Force refresh: {args.refresh}")
    
    try:
        # Check if we need to refresh data
        if not args.refresh:
            if not should_refresh_data(args.output_dir, args.max_age_hours):
                logger.info("Data is fresh, loading existing CSV files...")
                universe_df, price_data_df, fundamental_data_df = load_latest_data(args.output_dir)
                
                if universe_df is not None and price_data_df is not None and fundamental_data_df is not None:
                    logger.info("Successfully loaded existing data:")
                    logger.info(f"  Universe: {len(universe_df)} tickers")
                    logger.info(f"  Price data: {price_data_df.shape}")
                    logger.info(f"  Fundamental data: {len(fundamental_data_df)} records")
                    logger.info("="*60)
                    logger.info("DATA COLLECTION COMPLETED (using existing data)")
                    logger.info("="*60)
                    return
        
        # Collect fresh data
        logger.info("Collecting fresh data...")
        universe_df, price_data_df, fundamental_data_df = run_full_data_collection(
            save_to_csv=True,
            period=args.period,
            interval=args.interval,
            include_us=True,
            include_hk=False,  # Can be enabled later
            output_dir=args.output_dir
        )
        
        # Log results
        logger.info("="*60)
        logger.info("DATA COLLECTION COMPLETED")
        logger.info("="*60)
        
        if universe_df is not None:
            logger.info(f"Universe: {len(universe_df)} tickers")
            logger.info(f"  Sectors: {universe_df['sector'].nunique()} unique sectors")
            logger.info(f"  Regions: {universe_df['region'].nunique()} regions")
        
        if price_data_df is not None:
            logger.info(f"Price data: {price_data_df.shape}")
            logger.info(f"  Date range: {price_data_df.index.min()} to {price_data_df.index.max()}")
        
        if fundamental_data_df is not None:
            logger.info(f"Fundamental data: {len(fundamental_data_df)} records")
            logger.info(f"  Companies with data: {fundamental_data_df['ticker'].nunique()}")
        
        logger.info("CSV files saved in '{}' directory".format(args.output_dir))
        logger.info("Other scripts can now use load_latest_data() to access this data")
        
    except Exception as e:
        logger.error(f"Error during data collection: {e}")
        raise


if __name__ == "__main__":
    main()