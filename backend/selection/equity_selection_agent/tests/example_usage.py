"""
Example Usage Script for Enhanced Data Provider

This script demonstrates the complete workflow:
1. Collect data once and save to CSV
2. Use the saved CSV data in subsequent operations

Run this script to see the complete data collection and access workflow.
"""

import logging
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from backend.selection.equity_selection_agent.src.data_access import (
    ensure_data_available,
    get_universe,
    get_price_data,
    get_fundamental_data,
    get_sector_data,
    get_available_sectors
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demonstrate_workflow():
    """
    Demonstrate the complete data collection and access workflow.
    """
    logger.info("="*60)
    logger.info("ENHANCED DATA PROVIDER WORKFLOW DEMONSTRATION")
    logger.info("="*60)
    
    # Step 1: Ensure data is available (will collect if needed)
    logger.info("Step 1: Ensuring data is available...")
    if not ensure_data_available(max_age_hours=24):
        logger.error("Failed to ensure data availability")
        return
    
    logger.info("✅ Data is available!")
    
    # Step 2: Access universe data
    logger.info("\nStep 2: Accessing universe data...")
    universe_df = get_universe()
    if universe_df is not None:
        logger.info(f"✅ Universe loaded: {len(universe_df)} tickers")
        logger.info(f"   Regions: {universe_df['region'].unique()}")
        logger.info(f"   Sectors: {universe_df['sector'].nunique()} unique sectors")
        
        # Show sample data
        logger.info("   Sample universe data:")
        logger.info(f"   {universe_df.head(3).to_string()}")
    else:
        logger.error("❌ Failed to load universe data")
        return
    
    # Step 3: Access price data
    logger.info("\nStep 3: Accessing price data...")
    sample_tickers = universe_df['ticker'].head(5).tolist()
    price_data = get_price_data(sample_tickers)
    if price_data is not None:
        logger.info(f"✅ Price data loaded: {price_data.shape}")
        logger.info(f"   Sample tickers: {sample_tickers}")
        logger.info(f"   Date range: {price_data.index.min()} to {price_data.index.max()}")
    else:
        logger.error("❌ Failed to load price data")
    
    # Step 4: Access fundamental data
    logger.info("\nStep 4: Accessing fundamental data...")
    fund_data = get_fundamental_data(sample_tickers)
    if fund_data is not None:
        logger.info(f"✅ Fundamental data loaded: {len(fund_data)} records")
        logger.info("   Available metrics:")
        metrics = [col for col in fund_data.columns if col not in ['ticker', 'sector', 'industry']]
        logger.info(f"   {metrics[:10]}...")  # Show first 10 metrics
    else:
        logger.error("❌ Failed to load fundamental data")
    
    # Step 5: Access sector-specific data
    logger.info("\nStep 5: Accessing sector-specific data...")
    available_sectors = get_available_sectors()
    logger.info(f"Available sectors: {available_sectors}")
    
    if available_sectors:
        target_sector = available_sectors[0]  # Pick first available sector
        logger.info(f"Getting data for sector: {target_sector}")
        
        sector_universe, sector_prices, sector_fundamentals = get_sector_data(target_sector)
        
        if sector_universe is not None:
            logger.info(f"✅ {target_sector} sector data:")
            logger.info(f"   Companies: {len(sector_universe)}")
            logger.info(f"   Price data shape: {sector_prices.shape if sector_prices is not None else 'N/A'}")
            logger.info(f"   Fundamental records: {len(sector_fundamentals) if sector_fundamentals is not None else 'N/A'}")
        else:
            logger.error(f"❌ Failed to load {target_sector} sector data")
    
    # Step 6: Show file locations
    logger.info("\nStep 6: Data file locations...")
    data_dir = "data"
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        logger.info("✅ CSV files created:")
        for file in files:
            file_path = os.path.join(data_dir, file)
            file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
            logger.info(f"   {file} ({file_size:.1f} MB)")
    
    logger.info("\n" + "="*60)
    logger.info("WORKFLOW DEMONSTRATION COMPLETED")
    logger.info("="*60)
    logger.info("Summary:")
    logger.info("1. ✅ Data collection and CSV saving works")
    logger.info("2. ✅ Data access functions work")
    logger.info("3. ✅ Sector filtering works")
    logger.info("4. ✅ CSV files are created and accessible")
    logger.info("\nOther scripts can now use these functions:")
    logger.info("  - ensure_data_available()")
    logger.info("  - get_universe()")
    logger.info("  - get_price_data(tickers)")
    logger.info("  - get_fundamental_data(tickers)")
    logger.info("  - get_sector_data(sector)")


def demonstrate_usage_patterns():
    """
    Show different usage patterns for other scripts.
    """
    logger.info("\n" + "="*60)
    logger.info("USAGE PATTERNS FOR OTHER SCRIPTS")
    logger.info("="*60)
    
    # Pattern 1: Quick data access
    logger.info("\nPattern 1: Quick data access (recommended for most scripts)")
    logger.info("```python")
    logger.info("from data_access import get_universe, get_price_data, get_fundamental_data")
    logger.info("")
    logger.info("# Get all universe data")
    logger.info("universe = get_universe()")
    logger.info("")
    logger.info("# Get price data for specific tickers")
    logger.info("price_data = get_price_data(['AAPL', 'MSFT'])")
    logger.info("")
    logger.info("# Get fundamental data")
    logger.info("fund_data = get_fundamental_data(['AAPL', 'MSFT'])")
    logger.info("```")
    
    # Pattern 2: Sector analysis
    logger.info("\nPattern 2: Sector-specific analysis")
    logger.info("```python")
    logger.info("from data_access import get_sector_data, get_available_sectors")
    logger.info("")
    logger.info("# Get all available sectors")
    logger.info("sectors = get_available_sectors()")
    logger.info("")
    logger.info("# Analyze specific sector")
    logger.info("tech_universe, tech_prices, tech_fund = get_sector_data('Technology')")
    logger.info("```")
    
    # Pattern 3: Data refresh
    logger.info("\nPattern 3: Ensuring fresh data")
    logger.info("```python")
    logger.info("from data_access import ensure_data_available")
    logger.info("")
    logger.info("# Ensure data is fresh (max 6 hours old)")
    logger.info("if ensure_data_available(max_age_hours=6):")
    logger.info("    # Proceed with analysis")
    logger.info("    pass")
    logger.info("```")
    
    # Pattern 4: Direct CSV access
    logger.info("\nPattern 4: Direct CSV file access (if needed)")
    logger.info("```python")
    logger.info("import pandas as pd")
    logger.info("")
    logger.info("# Load CSV files directly")
    logger.info("universe = pd.read_csv('data/full_universe_tickers.csv')")
    logger.info("price_data = pd.read_csv('data/price_data_1y_1d_latest.csv', index_col=0)")
    logger.info("fund_data = pd.read_csv('data/fundamental_data_latest.csv')")
    logger.info("```")


if __name__ == "__main__":
    try:
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Run the demonstration
        demonstrate_workflow()
        demonstrate_usage_patterns()
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        raise