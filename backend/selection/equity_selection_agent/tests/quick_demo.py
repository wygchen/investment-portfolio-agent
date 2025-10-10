#!/usr/bin/env python3
"""
Quick Demo Script for Enhanced Data Provider

This script demonstrates the complete workflow in a single run.
Run this to see how the enhanced data provider works.

Usage:
    python quick_demo.py
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the complete demonstration."""
    
    logger.info("🚀 ENHANCED DATA PROVIDER QUICK DEMO")
    logger.info("="*50)
    
    try:
        # Import the enhanced data provider function
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from data_provider_enhanced import run_full_data_collection
        
        logger.info("📊 Step 1: Running full data collection...")
        logger.info("   This will collect S&P 500 data and save to CSV files")
        
        # Run the data collection
        universe_df, price_data_df, fund_data_df = run_full_data_collection(
            save_to_csv=True,
            period="1y",
            interval="1d",
            include_us=True,
            include_hk=False,
            output_dir="data"
        )
        
        logger.info("✅ Step 1 Complete!")
        logger.info(f"   - Universe: {len(universe_df)} tickers")
        logger.info(f"   - Price data: {price_data_df.shape if price_data_df is not None else 'N/A'}")
        logger.info(f"   - Fundamental data: {len(fund_data_df) if fund_data_df is not None else 'N/A'} records")
        
        # Show what files were created
        logger.info("\n📁 Step 2: Checking created files...")
        data_dir = "data"
        if os.path.exists(data_dir):
            csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            logger.info(f"   Created {len(csv_files)} CSV files:")
            for file in sorted(csv_files):
                file_path = os.path.join(data_dir, file)
                file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                logger.info(f"   - {file} ({file_size:.1f} MB)")
        
        # Demonstrate the data access functions
        logger.info("\n🔍 Step 3: Demonstrating data access functions...")
        
        try:
            from backend.selection.equity_selection_agent.src.data_access import (
                get_universe, get_price_data, get_fundamental_data, 
                get_available_sectors, get_sector_data
            )
            
            # Test universe access
            universe = get_universe()
            if universe is not None:
                logger.info(f"   ✅ Universe access: {len(universe)} tickers")
                logger.info(f"      Sectors: {list(universe['sector'].value_counts().head(3).index)}")
            
            # Test price data access
            sample_tickers = ['AAPL', 'MSFT', 'GOOGL']
            prices = get_price_data(sample_tickers)
            if prices is not None:
                logger.info(f"   ✅ Price data access: {prices.shape}")
            
            # Test fundamental data access
            fundamentals = get_fundamental_data(sample_tickers)
            if fundamentals is not None:
                logger.info(f"   ✅ Fundamental data access: {len(fundamentals)} records")
            
            # Test sector access
            sectors = get_available_sectors()
            if sectors:
                target_sector = sectors[0]
                sector_data = get_sector_data(target_sector)
                logger.info(f"   ✅ Sector data access: {target_sector} sector")
                
        except ImportError:
            logger.warning("   ⚠️  data_access module not available, skipping function tests")
        
        logger.info("\n🎉 SUCCESS! Enhanced data provider is working correctly!")
        logger.info("\n📝 Next steps:")
        logger.info("   1. Other scripts can now use: from data_access import get_universe, get_price_data")
        logger.info("   2. CSV files are saved in data/ directory for persistence")
        logger.info("   3. Data will auto-refresh when it gets old (>24 hours by default)")
        logger.info("   4. Use collect_data.py for more control over data collection")
        
        # Show usage example
        logger.info("\n💡 Example usage in other scripts:")
        logger.info("```python")
        logger.info("from data_access import get_universe, get_price_data")
        logger.info("")
        logger.info("# Get all universe data")
        logger.info("universe = get_universe()")
        logger.info("")
        logger.info("# Get price data for specific tickers")
        logger.info("tech_tickers = universe[universe['sector'] == 'Technology']['ticker'].tolist()")
        logger.info("tech_prices = get_price_data(tech_tickers)")
        logger.info("```")
        
    except Exception as e:
        logger.error(f"❌ Error during demo: {e}")
        logger.error("   This might be due to:")
        logger.error("   - Missing yfinance-cache package (pip install yfinance-cache)")
        logger.error("   - Network connectivity issues")
        logger.error("   - Yahoo Finance API rate limiting")
        raise
    
    logger.info("\n" + "="*50)
    logger.info("🎯 DEMO COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()