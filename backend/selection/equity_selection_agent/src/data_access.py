"""
Data Access Utility for Equity Selection Agent

This module provides easy access to the collected data stored in CSV files.
Other modules should use these functions instead of calling the data fetching functions directly.

Usage:
    from data_access import get_universe, get_price_data, get_fundamental_data, ensure_data_available
"""

import os
import pandas as pd
import logging
from typing import Optional, Tuple, List

from .stock_database import StockDatabase

# Set up logging
logger = logging.getLogger(__name__)


class DataAccess:
    """
    Centralized data access class for the equity selection agent.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Default to data directory relative to this file's parent directory
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.data_dir = data_dir
        
        # Initialize StockDatabase with SQLite database in the data directory
        db_path = os.path.join(data_dir, "stock_data.db")
        self.stock_db = StockDatabase(db_path)
        
        self._universe_df = None
        self._price_data_df = None
        self._fundamental_data_df = None
        self._data_loaded = False
    
    def _load_data(self, force_reload: bool = False) -> None:
        """Load data from the StockDatabase if not already loaded."""
        if not self._data_loaded or force_reload:
            logger.info("Loading data from StockDatabase...")
            self._universe_df = self.stock_db.get_universe()
            self._price_data_df = self.stock_db.get_price_data()
            self._fundamental_data_df = self.stock_db.get_fundamental_data()
            self._data_loaded = True
    
    def get_universe(self, force_reload: bool = False) -> Optional[pd.DataFrame]:
        """
        Get the investment universe data.
        
        Args:
            force_reload: Force reload from CSV files
            
        Returns:
            DataFrame with universe data or None if not available
        """
        self._load_data(force_reload)
        return self._universe_df
    
    def get_price_data(self, 
                      tickers: Optional[List[str]] = None, 
                      force_reload: bool = False) -> Optional[pd.DataFrame]:
        """
        Get historical price data.
        
        Args:
            tickers: List of specific tickers to get (None = all)
            force_reload: Force reload from database
            
        Returns:
            DataFrame with price data or None if not available
        """
        if force_reload:
            self._load_data(force_reload=True)
        else:
            self._load_data()
        
        # Use the StockDatabase method directly for specific tickers
        if tickers is not None:
            return self.stock_db.get_price_data(tickers=tickers)
        else:
            return self._price_data_df
    
    def get_fundamental_data(self, 
                           tickers: Optional[List[str]] = None, 
                           force_reload: bool = False) -> Optional[pd.DataFrame]:
        """
        Get fundamental data.
        
        Args:
            tickers: List of specific tickers to get (None = all)
            force_reload: Force reload from database
            
        Returns:
            DataFrame with fundamental data or None if not available
        """
        if force_reload:
            self._load_data(force_reload=True)
        else:
            self._load_data()
        
        # Use the StockDatabase method directly for specific tickers
        return self.stock_db.get_fundamental_data(tickers=tickers)
    
    def get_sector_data(self, sector: str, force_reload: bool = False) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Get all data for a specific sector.
        
        Args:
            sector: Sector name to filter by
            force_reload: Force reload from CSV files
            
        Returns:
            Tuple of (universe_df, price_data_df, fundamental_data_df) for the sector
        """
        universe_df = self.get_universe(force_reload)
        if universe_df is None:
            return None, None, None
        
        # Get tickers for the sector
        sector_tickers = universe_df[universe_df['sector'] == sector]['ticker'].tolist()
        if not sector_tickers:
            logger.warning(f"No tickers found for sector: {sector}")
            return None, None, None
        
        # Get data for sector tickers
        sector_universe = universe_df[universe_df['sector'] == sector]
        sector_price_data = self.get_price_data(sector_tickers)
        sector_fundamental_data = self.get_fundamental_data(sector_tickers)
        
        return sector_universe, sector_price_data, sector_fundamental_data
    
    def is_data_available(self) -> bool:
        """Check if data is available and loaded."""
        self._load_data()
        return all([
            self._universe_df is not None,
            self._price_data_df is not None,
            self._fundamental_data_df is not None
        ])
    
    def get_available_sectors(self, force_reload: bool = False) -> List[str]:
        """Get list of available sectors."""
        universe_df = self.get_universe(force_reload)
        if universe_df is None:
            return []
        return universe_df['sector'].unique().tolist()
    
    def get_available_tickers(self, force_reload: bool = False) -> List[str]:
        """Get list of available tickers."""
        universe_df = self.get_universe(force_reload)
        if universe_df is None:
            return []
        return universe_df['ticker'].unique().tolist()
    
    def refresh_data_if_needed(self, max_age_hours: int = 24) -> bool:
        """
        Check if data needs refreshing and refresh if necessary.
        
        Args:
            max_age_hours: Maximum age in hours before refresh
            
        Returns:
            True if data was refreshed, False if no refresh was needed
        """
        try:
            # Check if database has recent data using data summary
            summary = self.stock_db.get_data_summary()
            
            # If we have no data, we need to refresh
            if (summary['universe']['active_tickers'] == 0 or 
                summary['price_data']['total_records'] == 0):
                logger.info("No data available, performing refresh...")
                self.stock_db.refresh_universe(include_us=True, include_hk=True)
                self.stock_db.update_data(update_fundamentals=True)
                self._load_data(force_reload=True)
                logger.info("Data successfully refreshed")
                return True
            else:
                # Update data (incremental update)
                logger.info("Performing incremental data update...")
                update_results = self.stock_db.update_data()
                self._load_data(force_reload=True)
                logger.info(f"Data updated: {update_results}")
                return True
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            return False


# Global instance for easy access
# Use the correct path relative to the src directory
_data_access = DataAccess(data_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))


# Convenience functions for easy import and use
def ensure_data_available(max_age_hours: int = 24) -> bool:
    """
    Ensure that data is available, refreshing if necessary.
    
    Args:
        max_age_hours: Maximum age in hours before refresh
        
    Returns:
        True if data is available, False if there was an error
    """
    if not _data_access.is_data_available():
        logger.info("No data available, collecting fresh data...")
        try:
            # Use the new database approach
            _data_access.stock_db.refresh_universe(include_us=True, include_hk=True)
            _data_access.stock_db.update_data(update_fundamentals=True)
            _data_access._load_data(force_reload=True)
        except Exception as e:
            logger.error(f"Error collecting initial data: {e}")
            return False
    else:
        _data_access.refresh_data_if_needed(max_age_hours)
    
    return _data_access.is_data_available()


def get_universe() -> Optional[pd.DataFrame]:
    """Get the investment universe data."""
    ensure_data_available()
    return _data_access.get_universe()


def get_price_data(tickers: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    """Get historical price data."""
    ensure_data_available()
    return _data_access.get_price_data(tickers)


def get_fundamental_data(tickers: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    """Get fundamental data."""
    ensure_data_available()
    return _data_access.get_fundamental_data(tickers)


def get_sector_data(sector: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Get all data for a specific sector."""
    ensure_data_available()
    return _data_access.get_sector_data(sector)


def get_available_sectors() -> List[str]:
    """Get list of available sectors."""
    ensure_data_available()
    return _data_access.get_available_sectors()


def get_available_tickers() -> List[str]:
    """Get list of available tickers."""
    ensure_data_available()
    return _data_access.get_available_tickers()


# Example usage function
def example_usage():
    """
    Example of how to use the data access functions.
    """
    logger.info("Data Access Example Usage")
    logger.info("="*40)
    
    # Ensure data is available
    if not ensure_data_available():
        logger.error("Failed to get data")
        return
    
    # Get universe
    universe = get_universe()
    if universe is not None:
        logger.info(f"Universe: {len(universe)} tickers")
        logger.info(f"Sectors: {universe['sector'].nunique()}")
    
    # Get price data for specific tickers
    price_data = get_price_data(['AAPL', 'MSFT', 'GOOGL'])
    if price_data is not None:
        logger.info(f"Price data shape: {price_data.shape}")
    
    # Get fundamental data
    fund_data = get_fundamental_data()
    if fund_data is not None:
        logger.info(f"Fundamental data: {len(fund_data)} records")
    
    # Get sector-specific data
    tech_universe, tech_prices, tech_fundamentals = get_sector_data('Technology')
    if tech_universe is not None:
        logger.info(f"Technology sector: {len(tech_universe)} companies")
    
    # List available sectors
    sectors = get_available_sectors()
    logger.info(f"Available sectors: {sectors}")


if __name__ == "__main__":
    # Run example when script is executed directly
    example_usage()