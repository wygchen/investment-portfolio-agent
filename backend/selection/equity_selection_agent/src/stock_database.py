"""
Enhanced Data Provider with SQLite Storage and Incremental Updates

This module provides an enhanced data provider that uses SQLite for efficient storage
and supports incremental updates instead of full refreshes.

Key features:
- SQLite database for efficient storage and querying
- Three operations: refresh (full rebuild), update (incremental), load (cached)
- Incremental price data updates from last recorded date
- Smart fundamental data updates based on age
- Data migration utilities from existing CSV files

Usage:
    provider = EnhancedDataProvider("data/stock_data.db")
    
    # First time setup or when S&P 500 composition changes
    provider.refresh_universe()
    
    # Daily updates (recommended in cron job)
    provider.update_data()
    
    # Load data for analysis
    price_data = provider.get_price_data(tickers=['AAPL', 'MSFT'])
    fundamental_data = provider.get_fundamental_data()
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Any
import logging
import os
from pathlib import Path
import yfinance as yfc

# Import from same package
try:
    from .stock_universe import TickerManager, StockDataFetcher
except ImportError:
    # Fallback for direct script execution
    from stock_universe import TickerManager, StockDataFetcher

logger = logging.getLogger(__name__)


class StockDatabase:
    """
    Enhanced data provider with incremental updates and SQLite storage.
    
    Operations:
    - refresh(): Complete universe rebuild (when S&P 500 composition changes)
    - update(): Incremental price + conditional fundamental updates  
    - load(): Use cached data from database
    """
    
    def __init__(self, db_path: str = "data/stock_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_database_setup()
        
    def ensure_database_setup(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            # Universe table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS universe (
                    ticker TEXT PRIMARY KEY,
                    region TEXT NOT NULL,
                    sector TEXT,
                    industry TEXT,
                    name TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Price data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    ticker TEXT,
                    date DATE,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    dividends REAL DEFAULT 0,
                    stock_splits REAL DEFAULT 0,
                    fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (ticker, date),
                    FOREIGN KEY (ticker) REFERENCES universe(ticker)
                )
            """)
            
            # Fundamental data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fundamental_data (
                    ticker TEXT PRIMARY KEY,
                    market_cap REAL,
                    enterprise_value REAL,
                    trailing_pe REAL,
                    forward_pe REAL,
                    price_to_book REAL,
                    debt_to_equity REAL,
                    return_on_equity REAL,
                    current_price REAL,
                    trailing_eps REAL,
                    beta REAL,
                    news TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticker) REFERENCES universe(ticker)
                )
            """)
            
            # Metadata table for tracking updates
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_date ON price_data(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_ticker ON price_data(ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_universe_active ON universe(is_active)")
            
    def refresh_universe(self, include_us: bool = True, include_hk: bool = False) -> pd.DataFrame:
        """
        Complete universe refresh - rebuild everything.
        Use when S&P 500 composition changes.
        
        Args:
            include_us: Include US tickers
            include_hk: Include Hong Kong tickers
            
        Returns:
            DataFrame with universe data
        """
        logger.info("Starting complete universe refresh...")
        
        # Get fresh universe
        ticker_manager = TickerManager()
        universe_df = ticker_manager.create_full_universe(
            include_us=include_us,
            include_hk=include_hk
        )
        
        with sqlite3.connect(self.db_path) as conn:
            # Mark all existing tickers as inactive
            conn.execute("UPDATE universe SET is_active = 0")
            
            # Insert/update universe
            for _, row in universe_df.iterrows():
                conn.execute("""
                    INSERT OR REPLACE INTO universe 
                    (ticker, region, sector, industry, name, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (
                    row['ticker'], 
                    row['region'], 
                    row.get('sector', ''), 
                    row.get('industry', ''), 
                    row.get('name', '')
                ))
            
            # Update metadata
            conn.execute("""
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES ('last_universe_refresh', ?)
            """, (datetime.now().isoformat(),))
            
        logger.info(f"Universe refresh completed: {len(universe_df)} tickers")
        return universe_df
    
    def update_data(self, 
                   update_fundamentals: Optional[bool] = None,
                   fundamental_update_days: int = 7) -> Dict[str, int]:
        """
        Incremental data update.
        
        Args:
            update_fundamentals: None = auto-decide based on last update,
                                True = force update, False = skip
            fundamental_update_days: Days threshold for automatic fundamental updates
        
        Returns:
            Dict with counts of updated records
        """
        logger.info("Starting incremental data update...")
        
        # Get active tickers
        active_tickers = self.get_active_tickers()
        if not active_tickers:
            raise ValueError("No active tickers found. Run refresh_universe() first.")
        
        results = {'price_updates': 0, 'fundamental_updates': 0}
        
        # 1. Update price data (always)
        results['price_updates'] = self._update_price_data(active_tickers)
        
        # 2. Update fundamental data (conditionally)
        if update_fundamentals is None:
            # Auto-decide: update if >N days since last fundamental update
            last_fund_update = self._get_last_fundamental_update()
            should_update = (
                last_fund_update is None or 
                (datetime.now() - last_fund_update).days >= fundamental_update_days
            )
        else:
            should_update = update_fundamentals
            
        if should_update:
            results['fundamental_updates'] = self._update_fundamental_data(active_tickers)
        else:
            logger.info("Skipping fundamental data update (still fresh)")
        
        logger.info(f"Update completed: {results}")
        return results
    
    def _update_price_data(self, tickers: List[str]) -> int:
        """Update price data incrementally."""
        logger.info(f"Updating price data for {len(tickers)} tickers...")
        
        # Get last price date for each ticker
        with sqlite3.connect(self.db_path) as conn:
            last_dates_df = pd.read_sql("""
                SELECT ticker, MAX(date) as last_date
                FROM price_data
                GROUP BY ticker
            """, conn)
        
        last_dates = dict(zip(last_dates_df['ticker'], last_dates_df['last_date']))
        
        client = StockDataFetcher()
        total_updates = 0
        
        for ticker in tickers:
            try:
                # Determine start date
                last_date = last_dates.get(ticker)
                if last_date:
                    # Convert to datetime and add 1 day
                    last_dt = pd.to_datetime(last_date)
                    start_date = (last_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                    
                    # Skip if already up to date
                    if start_date > datetime.now().strftime('%Y-%m-%d'):
                        continue
                        
                    period = None
                    start = start_date
                else:
                    # No existing data, get full year
                    period = "1y"
                    start = None
                
                # Fetch new data using yfinance directly
                import yfinance as yf
                stock = yf.Ticker(ticker)
                
                if period:
                    data = stock.history(period=period, interval="1d")
                else:
                    data = stock.history(start=start, interval="1d")
                
                if not data.empty:
                    # Prepare data for database
                    data_records = []
                    for date, row in data.iterrows():
                        # Skip if we already have this date - convert index to string format YYYY-MM-DD
                        date_str = str(date)[:10]  # Extract YYYY-MM-DD from datetime string
                        if ticker in last_dates and date_str <= last_dates[ticker]:
                            continue
                            
                        data_records.append((
                            ticker, date_str,
                            float(row['Open']) if not pd.isna(row['Open']) else None,
                            float(row['High']) if not pd.isna(row['High']) else None,
                            float(row['Low']) if not pd.isna(row['Low']) else None,
                            float(row['Close']) if not pd.isna(row['Close']) else None,
                            int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                            float(row.get('Dividends', 0)) if not pd.isna(row.get('Dividends', 0)) else 0,
                            float(row.get('Stock Splits', 0)) if not pd.isna(row.get('Stock Splits', 0)) else 0
                        ))
                    
                    # Insert into database
                    if data_records:
                        with sqlite3.connect(self.db_path) as conn:
                            conn.executemany("""
                                INSERT OR REPLACE INTO price_data
                                (ticker, date, open, high, low, close, volume, dividends, stock_splits)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, data_records)
                        
                        total_updates += len(data_records)
                        logger.debug(f"Added {len(data_records)} price records for {ticker}")
                        
            except Exception as e:
                logger.warning(f"Error updating price data for {ticker}: {e}")
        
        # Update metadata
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES ('last_price_update', ?)
            """, (datetime.now().isoformat(),))
        
        logger.info(f"Price data update completed: {total_updates} records")
        return total_updates
    
    def _update_fundamental_data(self, tickers: List[str]) -> int:
        """Update fundamental data."""
        logger.info(f"Updating fundamental data for {len(tickers)} tickers...")
        
        try:
            client = StockDataFetcher()
            fundamental_data = client.get_fundamentals(tickers, force_refresh=True)
        except Exception as e:
            logger.error(f"Error fetching fundamental data: {e}")
            return 0
        
        total_updates = 0
        with sqlite3.connect(self.db_path) as conn:
            for ticker, data in fundamental_data.items():
                if 'error' not in data and isinstance(data, dict):
                    try:
                        conn.execute("""
                            INSERT OR REPLACE INTO fundamental_data
                            (ticker, market_cap, enterprise_value, trailing_pe, forward_pe,
                             price_to_book, debt_to_equity, return_on_equity, current_price,
                             trailing_eps, beta, news)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            ticker,
                            data.get('market_cap'),
                            data.get('enterprise_value'),
                            data.get('trailing_pe'),
                            data.get('forward_pe'),
                            data.get('price_to_book'),
                            data.get('debt_to_equity'),
                            data.get('return_on_equity'),
                            data.get('current_price'),
                            data.get('trailing_eps'),
                            data.get('beta'),
                            data.get('news', '')
                        ))
                        total_updates += 1
                    except Exception as e:
                        logger.warning(f"Error inserting fundamental data for {ticker}: {e}")
            
            # Update metadata
            conn.execute("""
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES ('last_fundamental_update', ?)
            """, (datetime.now().isoformat(),))
        
        logger.info(f"Fundamental data update completed: {total_updates} records")
        return total_updates
    
    def get_active_tickers(self) -> List[str]:
        """Get list of active tickers."""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql("SELECT ticker FROM universe WHERE is_active = 1 ORDER BY ticker", conn)
        return df['ticker'].tolist()
    
    def get_price_data(self, 
                      tickers: Optional[List[str]] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get price data with optional filtering.
        
        Args:
            tickers: List of tickers to filter by
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with price data
        """
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM price_data WHERE 1=1"
            params = []
            
            if tickers:
                placeholders = ','.join(['?' for _ in tickers])
                query += f" AND ticker IN ({placeholders})"
                params.extend(tickers)
                
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += " ORDER BY ticker, date"
            
            df = pd.read_sql(query, conn, params=params)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                
            return df
    
    def get_fundamental_data(self, tickers: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get fundamental data.
        
        Args:
            tickers: List of tickers to filter by
            
        Returns:
            DataFrame with fundamental data
        """
        with sqlite3.connect(self.db_path) as conn:
            if tickers:
                placeholders = ','.join(['?' for _ in tickers])
                query = f"SELECT * FROM fundamental_data WHERE ticker IN ({placeholders}) ORDER BY ticker"
                return pd.read_sql(query, conn, params=tuple(tickers))
            else:
                return pd.read_sql("SELECT * FROM fundamental_data ORDER BY ticker", conn)
    
    def get_universe(self) -> pd.DataFrame:
        """Get universe data."""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql("SELECT * FROM universe WHERE is_active = 1 ORDER BY ticker", conn)
    
    def _get_last_fundamental_update(self) -> Optional[datetime]:
        """Get timestamp of last fundamental update."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT value FROM metadata WHERE key = 'last_fundamental_update'
            """).fetchone()
            
            if result:
                try:
                    return datetime.fromisoformat(result[0])
                except ValueError:
                    return None
            return None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of data in database."""
        with sqlite3.connect(self.db_path) as conn:
            summary = {}
            
            # Universe stats
            summary['universe'] = pd.read_sql("""
                SELECT 
                    COUNT(*) as total_tickers,
                    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_tickers,
                    COUNT(DISTINCT sector) as sectors,
                    COUNT(DISTINCT region) as regions
                FROM universe
            """, conn).iloc[0].to_dict()
            
            # Price data stats
            try:
                summary['price_data'] = pd.read_sql("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT ticker) as tickers_with_data,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date
                    FROM price_data
                """, conn).iloc[0].to_dict()
            except:
                summary['price_data'] = {'total_records': 0, 'tickers_with_data': 0, 
                                       'earliest_date': None, 'latest_date': None}
            
            # Fundamental data stats
            try:
                summary['fundamental_data'] = pd.read_sql("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN market_cap IS NOT NULL THEN 1 END) as with_market_cap,
                        MIN(last_updated) as earliest_update,
                        MAX(last_updated) as latest_update
                    FROM fundamental_data
                """, conn).iloc[0].to_dict()
            except:
                summary['fundamental_data'] = {'total_records': 0, 'with_market_cap': 0,
                                             'earliest_update': None, 'latest_update': None}
            
            # Last update times
            try:
                metadata_df = pd.read_sql("SELECT * FROM metadata", conn)
                summary['last_updates'] = dict(zip(metadata_df['key'], metadata_df['value']))
            except:
                summary['last_updates'] = {}
            
        return summary