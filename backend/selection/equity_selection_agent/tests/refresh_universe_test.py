"""
Test and refresh the S&P 500 universe with the fixed Wikipedia scraping.
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_provider_enhanced import TickerManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def refresh_universe():
    """Refresh the universe with the fixed Wikipedia scraping."""
    logger.info("Refreshing S&P 500 universe with fixed scraping...")
    
    try:
        # Create ticker manager
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        ticker_manager = TickerManager(universe_file=os.path.join(data_dir, "full_universe_tickers.csv"))
        
        # Force refresh the universe (this will use the fixed scraping method)
        universe_df = ticker_manager.get_universe(refresh=True)
        
        logger.info(f"Successfully refreshed universe with {len(universe_df)} tickers")
        
        # Show summary by sector
        if 'sector' in universe_df.columns:
            sector_counts = universe_df['sector'].value_counts()
            logger.info(f"\nSector distribution:")
            for sector, count in sector_counts.head(10).items():
                logger.info(f"  {sector}: {count}")
        
        # Show first 10 tickers
        logger.info("\nFirst 10 tickers:")
        for i, row in universe_df.head(10).iterrows():
            logger.info(f"  {i+1}. {row['ticker']} - {row['name']} ({row['sector']})")
        
        # Check for any suspicious tickers
        suspicious = []
        for _, row in universe_df.iterrows():
            ticker = row['ticker']
            if any(month in ticker.upper() for month in ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 
                                                        'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']):
                suspicious.append(ticker)
            elif ',' in ticker or ' ' in ticker:
                suspicious.append(ticker)
        
        if suspicious:
            logger.warning(f"Found {len(suspicious)} suspicious tickers: {suspicious}")
        else:
            logger.info("✅ No suspicious tickers found - fix successful!")
        
        # Test success criteria
        if len(universe_df) > 400 and len(suspicious) == 0:
            logger.info("✅ Universe refresh test PASSED!")
            return True
        else:
            logger.error("❌ Universe refresh test FAILED!")
            return False
            
    except Exception as e:
        logger.error(f"Universe refresh failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    refresh_universe()