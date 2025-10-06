"""
Enhanced Data Provider Module for Equity Selection Agent (ESA) V1.0

This module houses the enhanced classes for defining the investment universe 
and retrieving both historical and fundamental raw data using yfinance-cache
for improved performance and intelligent caching.

Classes:
- TickerManager: Manages US (S&P 500) and HK universe lists (unchanged)
- YFinanceCacheClient: Enhanced client using yfinance-cache for better performance
"""

import pandas as pd
import yfinance_cache as yfc
import requests
import bs4 as bs
import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Set up logging
logger = logging.getLogger(__name__)


class TickerManager:
    """
    Manages the US (S&P 500) and HK universe lists with mandatory Region tagging.
    Handles persistence in full_universe_tickers.csv.
    
    This class remains unchanged from the original implementation.
    """
    
    def __init__(self, universe_file: str = "data/full_universe_tickers.csv"):
        self.universe_file = universe_file
        self._universe_df: Optional[pd.DataFrame] = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(universe_file), exist_ok=True)
    
    def _validate_ticker_with_yfinance(self, ticker: str, timeout_seconds: int = 5) -> bool:
        """
        Validate that a ticker works with yfinance_cache.
        
        Args:
            ticker: The ticker symbol to validate
            timeout_seconds: Timeout for the validation check
            
        Returns:
            True if ticker is valid, False otherwise
        """
        try:
            import yfinance_cache as yfc
            stock = yfc.Ticker(ticker)
            # Try to get just 2 days of data as a quick test
            data = stock.history(period="2d", max_age="1d")
            return not data.empty
        except Exception as e:
            logger.debug(f"Ticker {ticker} validation failed: {e}")
            return False
    
    def load_sp500_tickers(self) -> List[Dict[str, str]]:
        """
        Load S&P 500 tickers from Wikipedia using pandas read_html for reliability.
        
        Returns:
            List of dictionaries with ticker, region, and sector information
        """
        # Method 1: Try pandas read_html (most reliable method)
        try:
            logger.info("Loading S&P 500 tickers from Wikipedia using pandas read_html...")
            
            # Add proper headers to avoid 403 Forbidden
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            
            # Use requests with headers first, then pass to pandas
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Read the tables from the response content using StringIO to avoid FutureWarning
            from io import StringIO
            tables = pd.read_html(StringIO(response.text))
            sp500_df = tables[0]  # First table contains current S&P 500 companies
            
            # Clean up the DataFrame columns
            sp500_df.columns = sp500_df.columns.str.strip()
            
            logger.info(f"Retrieved {len(sp500_df)} companies from Wikipedia")
            
            # Extract ticker symbols and sector information
            tickers_list: List[Dict[str, str]] = []
            validated_count = 0
            failed_validation = []
            
            for idx, row in sp500_df.iterrows():
                try:
                    # Convert idx to int for proper arithmetic
                    row_num = int(idx) if isinstance(idx, (int, float)) else 0
                    
                    # Get ticker symbol (usually in 'Symbol' column)
                    ticker = str(row.get('Symbol', row.iloc[0])).strip()
                    
                    # Basic validation - check if ticker looks valid before yfinance validation
                    if not ticker or ticker == 'nan' or len(ticker) > 10:
                        logger.debug(f"Skipping invalid ticker format: {ticker}")
                        continue
                        
                    # Check for date-like patterns that were causing issues
                    if any(month in ticker.upper() for month in ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 
                                                                'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']):
                        logger.debug(f"Skipping ticker with month name: {ticker}")
                        continue
                    
                    # Check for numbers and commas that suggest invalid data
                    if ',' in ticker or any(char.isdigit() for char in ticker.replace('-', '')):
                        if len(ticker) > 5:  # Allow short tickers with numbers (like 3M -> MMM)
                            logger.debug(f"Skipping suspicious ticker: {ticker}")
                            continue
                    
                    # Get sector and industry information
                    sector = str(row.get('GICS Sector', 'Unknown')).strip()
                    industry = str(row.get('GICS Sub-Industry', 'Unknown')).strip()
                    company_name = str(row.get('Security', row.get('Company', 'Unknown'))).strip()
                    
                    # Clean up ticker symbol (replace dots with dashes for Yahoo Finance)
                    ticker = ticker.replace('.', '-').strip()
                    
                    # Validate ticker with yfinance (but don't fail the whole process if some fail)
                    if not self._validate_ticker_with_yfinance(ticker):
                        failed_validation.append(ticker)
                        logger.debug(f"Skipping invalid ticker: {ticker}")
                        continue
                    
                    validated_count += 1
                    
                    ticker_info: Dict[str, str] = {
                        'ticker': ticker,
                        'region': 'US',
                        'sector': sector,
                        'industry': industry,
                        'name': company_name
                    }
                    tickers_list.append(ticker_info)
                    
                    # Log progress every 50 tickers
                    if (row_num + 1) % 50 == 0:
                        logger.info(f"Processed {row_num + 1}/{len(sp500_df)} tickers, {validated_count} validated")
                        
                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    continue
            
            if len(tickers_list) > 400:  # Should have ~500 companies
                logger.info(f"Successfully loaded {len(tickers_list)} validated S&P 500 tickers from Wikipedia")
                if failed_validation:
                    logger.info(f"Failed validation for {len(failed_validation)} tickers: {failed_validation[:10]}{'...' if len(failed_validation) > 10 else ''}")
                return tickers_list
            else:
                logger.warning(f"Only got {len(tickers_list)} valid tickers from Wikipedia, trying alternative method")
                
        except Exception as e:
            logger.warning(f"pandas read_html method failed: {e}")
        
        # Method 2: Try BeautifulSoup as backup with correct table parsing
        try:
            logger.info("Trying BeautifulSoup as backup method...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Download stocks names from S&P500 page on wikipedia
            resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies', 
                              headers=headers, timeout=10)
            resp.raise_for_status()
            
            soup = bs.BeautifulSoup(resp.text, 'lxml')
            
            # Try to find the correct table - look for tables with S&P 500 data
            tables = soup.find_all('table', {'class': 'wikitable'})
            
            sp500_table = None
            for table in tables:
                # Look for table headers that indicate S&P 500 constituents
                headers_row = table.find('tr')
                if headers_row:
                    headers_text = headers_row.get_text().lower()
                    if 'symbol' in headers_text and 'security' in headers_text:
                        sp500_table = table
                        break
            
            if not sp500_table:
                raise ValueError("Could not find the S&P 500 table with BeautifulSoup")
            
            # Extract data from table rows
            tickers_list: List[Dict[str, str]] = []
            validated_count = 0
            failed_validation = []
            
            # Skip header row and process data rows
            rows = sp500_table.find_all('tr')[1:]  # Skip header
            
            logger.info(f"Found {len(rows)} companies in BeautifulSoup table")
            
            for idx, row in enumerate(rows):
                try:
                    cells = row.find_all('td')
                    if len(cells) < 3:  # Need at least ticker, name, sector
                        continue
                    
                    # Extract data from cells (typical order: Symbol, Security, GICS Sector, GICS Sub-Industry)
                    ticker = cells[0].get_text(strip=True)
                    company_name = cells[1].get_text(strip=True)
                    sector = cells[2].get_text(strip=True) if len(cells) > 2 else 'Unknown'
                    industry = cells[3].get_text(strip=True) if len(cells) > 3 else 'Unknown'
                    
                    # Basic validation before yfinance check
                    if not ticker or ticker == 'nan' or len(ticker) > 10:
                        continue
                        
                    # Check for date-like patterns
                    if any(month in ticker.upper() for month in ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 
                                                                'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']):
                        continue
                    
                    # Clean up ticker symbol (remove any extra characters)
                    ticker = ticker.replace('.', '-').strip()
                    
                    # Validate ticker with yfinance
                    if not self._validate_ticker_with_yfinance(ticker):
                        failed_validation.append(ticker)
                        logger.debug(f"Skipping invalid ticker: {ticker}")
                        continue
                    
                    validated_count += 1
                    
                    ticker_info: Dict[str, str] = {
                        'ticker': ticker,
                        'region': 'US',
                        'sector': sector,
                        'industry': industry,
                        'name': company_name
                    }
                    tickers_list.append(ticker_info)
                    
                    # Log progress every 50 tickers
                    if (idx + 1) % 50 == 0:
                        logger.info(f"Processed {idx + 1}/{len(rows)} tickers, {validated_count} validated")
                        
                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    continue
            
            if len(tickers_list) > 400:  # Should have ~500 companies
                logger.info(f"Successfully loaded {len(tickers_list)} validated S&P 500 tickers from BeautifulSoup backup")
                if failed_validation:
                    logger.info(f"Failed validation for {len(failed_validation)} tickers: {failed_validation[:10]}{'...' if len(failed_validation) > 10 else ''}")
                return tickers_list
            else:
                logger.warning(f"Only got {len(tickers_list)} valid tickers from BeautifulSoup backup")
                
        except Exception as e:
            logger.warning(f"BeautifulSoup backup method failed: {e}")
        
        # Method 3: Use updated fallback list
        logger.info("Using updated fallback ticker list...")
        return self._get_fallback_sp500_tickers()
    
    def _get_fallback_sp500_tickers(self) -> List[Dict[str, str]]:
        """
        Updated fallback method with current S&P 500 tickers (as of Oct 2024).
        These tickers are verified to be currently trading and active.
        """
        # Updated list of major S&P 500 companies (verified active as of Oct 2024)
        fallback_tickers = [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
            'AVGO', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'ACN', 'TXN', 'QCOM',
            'AMD', 'INTC', 'IBM', 'INTU', 'NOW', 'AMAT', 'MU', 'ADI',
            
            # Financial Services
            'BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'AXP',
            'SPGI', 'BLK', 'C', 'SCHW', 'CB', 'MMC', 'ICE', 'PGR',
            
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR',
            'BMY', 'CVS', 'MDT', 'CI', 'GILD', 'BSX', 'ISRG', 'VRTX',
            
            # Consumer Discretionary
            'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'F', 'GM',
            'MAR', 'HLT', 'ABNB', 'BKNG', 'CMG', 'ORLY', 'AZO',
            
            # Consumer Staples
            'WMT', 'PG', 'KO', 'PEP', 'COST', 'WBA', 'EL', 'CL', 'KMB',
            'GIS', 'HSY', 'K', 'CPB', 'CAG', 'SJM', 'CHD',
            
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'MPC', 'VLO',
            'PSX', 'OXY', 'BKR', 'HAL', 'DVN', 'FANG', 'EQT',
            
            # Industrials
            'LIN', 'CAT', 'BA', 'RTX', 'HON', 'UPS', 'DE', 'LMT',
            'MMM', 'GE', 'UNP', 'ADP', 'TT', 'ETN', 'ITW', 'CSX',
            
            # Communication Services
            'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'NFLX',
            'CHTR', 'PARA', 'WBD', 'FOXA', 'FOX', 'MTCH', 'PINS',
            
            # Utilities
            'NEE', 'SO', 'DUK', 'AEP', 'SRE', 'D', 'PEG', 'EXC',
            'XEL', 'ED', 'ETR', 'WEC', 'ES', 'FE', 'EIX', 'PPL',
            
            # Real Estate
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'WELL', 'SPG', 'O',
            'SBAC', 'DLR', 'REG', 'ARE', 'MAA', 'EQR', 'VTR', 'ESS',
            
            # Materials
            'APD', 'SHW', 'FCX', 'NEM', 'DOW', 'DD', 'VMC',
            'MLM', 'ECL', 'PPG', 'RPM', 'FMC', 'ALB', 'CF', 'EMN'
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tickers = []
        for ticker in fallback_tickers:
            if ticker not in seen:
                seen.add(ticker)
                unique_tickers.append(ticker)
        
        logger.info(f"Using fallback ticker list with {len(unique_tickers)} tickers")
        
        # Validate fallback tickers too
        validated_fallback = []
        for ticker in unique_tickers:
            if self._validate_ticker_with_yfinance(ticker):
                validated_fallback.append({
                    'ticker': ticker,
                    'region': 'US',
                    'sector': 'Unknown',  # Will be updated when fetching fundamentals
                    'industry': 'Unknown',
                    'name': 'Unknown'
                })
            else:
                logger.warning(f"Fallback ticker {ticker} failed validation")
        
        logger.info(f"Validated {len(validated_fallback)} fallback tickers")
        return validated_fallback
    
    def load_hk_tickers(self) -> List[Dict[str, str]]:
        """
        Load HK market tickers. Currently returns placeholder.
        TODO: Implement HK market ticker loading (e.g., from Hang Seng Index)
        
        Returns:
            List of dictionaries with ticker, region, and sector information
        """
        # Placeholder for HK tickers - to be implemented based on requirements
        hk_tickers = [
            {'ticker': '0005.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Banks', 'name': 'HSBC Holdings'},
            {'ticker': '0700.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Internet Content & Information', 'name': 'Tencent Holdings'},
            {'ticker': '0941.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Semiconductors', 'name': 'China Mobile'},
        ]
        
        logger.info(f"Loaded {len(hk_tickers)} HK tickers (placeholder)")
        return hk_tickers
    
    def create_full_universe(self, include_us: bool = True, include_hk: bool = False) -> pd.DataFrame:
        """
        Create the complete investment universe with Region tagging.
        
        Args:
            include_us: Whether to include US stocks
            include_hk: Whether to include HK stocks
            
        Returns:
            DataFrame with columns: ticker, region, sector, industry, name
        """
        all_tickers: List[Dict[str, str]] = []
        
        if include_us:
            us_tickers = self.load_sp500_tickers()
            all_tickers.extend(us_tickers)
        
        if include_hk:
            hk_tickers = self.load_hk_tickers()
            all_tickers.extend(hk_tickers)
        
        if not all_tickers:
            raise ValueError("No tickers loaded. Please enable at least one region.")
        
        self._universe_df = pd.DataFrame(all_tickers)
        
        # Save to file for persistence
        self.save_universe()
        
        logger.info(f"Created universe with {len(self._universe_df)} total tickers")
        return self._universe_df
    
    def load_universe(self) -> Optional[pd.DataFrame]:
        """
        Load universe from saved file if it exists.
        
        Returns:
            DataFrame or None if file doesn't exist
        """
        if os.path.exists(self.universe_file):
            try:
                self._universe_df = pd.read_csv(self.universe_file)
                logger.info(f"Loaded universe from {self.universe_file} with {len(self._universe_df)} tickers")
                return self._universe_df
            except Exception as e:
                logger.error(f"Error loading universe file: {e}")
                return None
        return None
    
    def save_universe(self) -> None:
        """Save current universe to file."""
        if self._universe_df is not None:
            self._universe_df.to_csv(self.universe_file, index=False)
            logger.info(f"Saved universe to {self.universe_file}")
    
    def get_universe(self, refresh: bool = False) -> pd.DataFrame:
        """
        Get the investment universe, loading from file or creating new.
        
        Args:
            refresh: Force refresh of the universe
            
        Returns:
            DataFrame with universe data
        """
        if refresh or self._universe_df is None:
            # Try to load from file first
            if not refresh:
                loaded_df = self.load_universe()
                if loaded_df is not None:
                    self._universe_df = loaded_df
                    return self._universe_df
            
            # Create new universe
            self._universe_df = self.create_full_universe()
        
        return self._universe_df


class YFinanceCacheClient:
    """
    Enhanced client using yfinance-cache for intelligent caching and better performance.
    
    Key improvements over manual caching:
    - Market-aware caching (considers market hours)
    - Automatic price adjustments for splits/dividends
    - Smart aging based on data type
    - Earnings-calendar aware fundamental updates
    - Built-in rate limiting and error handling
    """
    
    def __init__(self):
        """
        Initialize the enhanced yfinance client with optimal settings.
        """
        # Configure yfinance-cache options for optimal performance
        self._configure_cache_settings()
        
        logger.info("Initialized YFinanceCacheClient with intelligent caching")
    
    def _configure_cache_settings(self) -> None:
        """
        Configure yfinance-cache settings for optimal performance.
        """
        # Set price data aging - more frequent updates during market hours
        yfc.options.max_ages.history_1d = "1h"  # Update hourly for daily data
        yfc.options.max_ages.history_1wk = "4h"  # Update every 4 hours for weekly
        yfc.options.max_ages.history_1mo = "1d"  # Daily updates for monthly
        
        # Set fundamental data aging - less frequent updates
        yfc.options.max_ages.info = "7d"  # Weekly updates for basic info
        yfc.options.max_ages.financials = "30d"  # Monthly for financial statements
        yfc.options.max_ages.balance_sheet = "30d"
        yfc.options.max_ages.cashflow = "30d"
        yfc.options.max_ages.calendar = "14d"  # Bi-weekly for earnings calendar
        
        logger.info("Configured yfinance-cache settings for optimal performance")
    
    def validate_tickers(self, tickers: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a list of tickers with yfinance_cache.
        
        Args:
            tickers: List of ticker symbols to validate
            
        Returns:
            Tuple of (valid_tickers, invalid_tickers)
        """
        valid_tickers = []
        invalid_tickers = []
        
        logger.info(f"Validating {len(tickers)} tickers...")
        
        for i, ticker in enumerate(tickers):
            try:
                stock = yfc.Ticker(ticker)
                # Quick test with minimal data
                data = stock.history(period="2d", max_age="1d")
                if not data.empty:
                    valid_tickers.append(ticker)
                else:
                    invalid_tickers.append(ticker)
                    logger.debug(f"Ticker {ticker} returned empty data")
            except Exception as e:
                invalid_tickers.append(ticker)
                logger.debug(f"Ticker {ticker} validation failed: {e}")
            
            # Log progress for large lists
            if (i + 1) % 50 == 0:
                logger.info(f"Validated {i + 1}/{len(tickers)} tickers")
        
        logger.info(f"Validation complete: {len(valid_tickers)} valid, {len(invalid_tickers)} invalid")
        return valid_tickers, invalid_tickers
    
    def get_historical_data(self, 
                          tickers: List[str], 
                          period: str = "1y",
                          interval: str = "1d",
                          force_refresh: bool = False,
                          trigger_at_market_close: bool = True,
                          validate_tickers_first: bool = False) -> pd.DataFrame:
        """
        Get historical price data using intelligent caching.
        
        Args:
            tickers: List of ticker symbols
            period: Data period (e.g., "1y", "2y", "5y")
            interval: Data interval (e.g., "1d", "1wk", "1mo")
            force_refresh: Force refresh regardless of cache age
            trigger_at_market_close: Update cache when market closes
            validate_tickers_first: Validate tickers before fetching data
            
        Returns:
            DataFrame with historical price data including FetchDate and Final? columns
        """
        logger.info(f"Fetching historical data for {len(tickers)} tickers (period={period}, interval={interval})")
        
        # Validate tickers first if requested
        if validate_tickers_first:
            valid_tickers, invalid_tickers = self.validate_tickers(tickers)
            if invalid_tickers:
                logger.warning(f"Skipping {len(invalid_tickers)} invalid tickers: {invalid_tickers[:5]}{'...' if len(invalid_tickers) > 5 else ''}")
            tickers = valid_tickers
            if not tickers:
                raise ValueError("No valid tickers found after validation")
        
        try:
            all_data = []
            
            for ticker in tickers:
                try:
                    # Create ticker object
                    stock = yfc.Ticker(ticker)
                    
                    # Determine max_age based on interval and force_refresh
                    if force_refresh:
                        max_age = "0s"  # Force immediate refresh
                    else:
                        # Use default smart aging
                        max_age = None
                    
                    # Fetch historical data with intelligent caching
                    data = stock.history(
                        period=period,
                        interval=interval,
                        max_age=max_age,
                        trigger_at_market_close=trigger_at_market_close,
                        adjust_splits=True,  # Automatically adjust for splits
                        adjust_divs=True     # Automatically adjust for dividends
                    )
                    
                    if data is not None and not data.empty:
                        # Add ticker column for identification
                        data_copy = data.copy()
                        data_copy['Ticker'] = ticker
                        all_data.append(data_copy)
                        
                except Exception as e:
                    logger.error(f"Error fetching data for {ticker}: {e}")
                    continue
            
            if not all_data:
                raise ValueError("No valid data retrieved for any ticker")
            
            # Combine all data
            combined_data = pd.concat(all_data, keys=[df['Ticker'].iloc[0] for df in all_data])
            
            logger.info(f"Successfully fetched historical data for {len(all_data)} tickers")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error in get_historical_data: {e}")
            raise
    
    def get_fundamentals(self, 
                        tickers: List[str], 
                        force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get fundamental data using earnings-aware caching.
        
        Args:
            tickers: List of ticker symbols
            force_refresh: Force refresh regardless of cache age
            
        Returns:
            Dictionary with ticker as key and fundamental data as value
        """
        logger.info(f"Fetching fundamental data for {len(tickers)} tickers")
        
        fundamental_data = {}
        
        for i, ticker in enumerate(tickers):
            try:
                # Create ticker object
                stock = yfc.Ticker(ticker)
                
                # Determine max_age for different data types
                max_age = "0s" if force_refresh else None
                
                # Get basic info (cached intelligently)
                info = stock.info if hasattr(stock, 'info') else {}
                
                # Get financial statements with caching
                try:
                    # These are cached based on earnings calendar
                    balance_sheet = stock.balance_sheet if hasattr(stock, 'balance_sheet') else pd.DataFrame()
                    income_stmt = stock.financials if hasattr(stock, 'financials') else pd.DataFrame()
                    cashflow = stock.cashflow if hasattr(stock, 'cashflow') else pd.DataFrame()
                    
                    # Get earnings calendar information
                    calendar_data = stock.calendar if hasattr(stock, 'calendar') else pd.DataFrame()
                    
                    # Get release dates for intelligent fundamental updates
                    try:
                        release_dates = stock.get_release_dates() if hasattr(stock, 'get_release_dates') else None
                    except:
                        release_dates = None
                    
                    # Extract key financial metrics with safe type casting
                    fundamental_info: Dict[str, Any] = {
                        'info': info,
                        'sector': str(info.get('sector', 'Unknown')) if info else 'Unknown',
                        'industry': str(info.get('industry', 'Unknown')) if info else 'Unknown',
                        'market_cap': info.get('marketCap', None) if info else None,
                        'enterprise_value': info.get('enterpriseValue', None) if info else None,
                        'trailing_pe': info.get('trailingPE', None) if info else None,
                        'forward_pe': info.get('forwardPE', None) if info else None,
                        'price_to_book': info.get('priceToBook', None) if info else None,
                        'debt_to_equity': info.get('debtToEquity', None) if info else None,
                        'return_on_equity': info.get('returnOnEquity', None) if info else None,
                        'current_price': info.get('regularMarketPrice', info.get('currentPrice', None)) if info else None,
                        'trailing_eps': info.get('trailingEps', None) if info else None,
                        'beta': info.get('beta', None) if info else None,
                        'business_summary': str(info.get('longBusinessSummary', '')) if info else '',
                        'balance_sheet': balance_sheet.iloc[:, 0].to_dict() if not balance_sheet.empty else {},
                        'income_statement': income_stmt.iloc[:, 0].to_dict() if not income_stmt.empty else {},
                        'cashflow': cashflow.iloc[:, 0].to_dict() if not cashflow.empty else {},
                        'calendar': calendar_data.to_dict() if not calendar_data.empty else {},
                        'release_dates': release_dates
                    }
                    
                except Exception as e:
                    logger.warning(f"Could not fetch financial statements for {ticker}: {e}")
                    fundamental_info = {
                        'info': info,
                        'sector': str(info.get('sector', 'Unknown')) if info else 'Unknown',
                        'industry': str(info.get('industry', 'Unknown')) if info else 'Unknown',
                        'current_price': info.get('regularMarketPrice', info.get('currentPrice', None)) if info else None,
                        'business_summary': str(info.get('longBusinessSummary', '')) if info else '',
                    }
                
                fundamental_data[ticker] = fundamental_info
                
                if (i + 1) % 20 == 0:
                    logger.info(f"Processed {i + 1}/{len(tickers)} tickers")
                    
            except Exception as e:
                logger.error(f"Error fetching fundamental data for {ticker}: {e}")
                fundamental_data[ticker] = {'error': str(e)}
        
        logger.info(f"Successfully fetched fundamental data for {len(fundamental_data)} tickers")
        return fundamental_data
    
    def get_sector_mapping(self, tickers: List[str]) -> Dict[str, str]:
        """
        Get sector mapping for tickers using cached fundamental data.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to sector
        """
        fundamental_data = self.get_fundamentals(tickers)
        
        sector_mapping = {}
        for ticker, data in fundamental_data.items():
            if 'sector' in data:
                sector_mapping[ticker] = data['sector']
            else:
                sector_mapping[ticker] = 'Unknown'
        
        return sector_mapping
    
    def verify_cache_integrity(self, 
                             tickers: Optional[List[str]] = None, 
                             correct_errors: bool = False,
                             rtol: float = 0.0001,
                             vol_rtol: float = 0.005) -> bool:
        """
        Verify cached data integrity against latest Yahoo Finance data.
        
        Args:
            tickers: List of tickers to verify (None = verify all cached)
            correct_errors: Whether to automatically correct found errors
            rtol: Relative tolerance for price differences (0.0001 = 0.01%)
            vol_rtol: Relative tolerance for volume differences (0.005 = 0.5%)
            
        Returns:
            True if cache is valid, False if discrepancies found
        """
        try:
            # Determine correct parameter based on user preference
            correct_param = 'all' if correct_errors else False
            
            if tickers:
                # Verify specific tickers
                for ticker in tickers:
                    stock = yfc.Ticker(ticker)
                    # Use type: ignore to handle the union type issue
                    result = stock.verify_cached_prices(
                        rtol=rtol,
                        vol_rtol=vol_rtol,
                        correct=correct_param,  # type: ignore
                        quiet=True  # Suppress detailed output for batch verification
                    )
                    if not result:
                        logger.warning(f"Cache integrity issue detected for {ticker}")
                        return False
                    logger.debug(f"Cache verification passed for {ticker}")
            else:
                # Verify entire cache
                # Use type: ignore to handle the union type issue
                result = yfc.verify_cached_tickers_prices(
                    rtol=rtol,
                    vol_rtol=vol_rtol,
                    correct=correct_param,  # type: ignore
                    halt_on_fail=not correct_errors  # If correcting, don't halt on first failure
                )
                if not result:
                    logger.warning("Cache integrity issues detected")
                    return False
            
            logger.info("Cache integrity verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Error during cache verification: {e}")
            return False
    
    def correct_cache_errors(self, 
                           tickers: Optional[List[str]] = None,
                           correction_mode: str = 'all') -> bool:
        """
        Correct cache errors by comparing against latest Yahoo Finance data.
        
        Args:
            tickers: List of tickers to correct (None = correct all cached)
            correction_mode: 'one' to stop after first correction, 'all' to correct everything
            
        Returns:
            True if corrections completed successfully
        """
        try:
            # Convert correction_mode to appropriate parameter value
            correct_param = correction_mode if correction_mode in ['one', 'all'] else 'all'
            
            if tickers:
                # Correct specific tickers
                all_corrected = True
                for ticker in tickers:
                    stock = yfc.Ticker(ticker)
                    # Use type: ignore to handle the union type issue
                    result = stock.verify_cached_prices(
                        rtol=0.0001,
                        vol_rtol=0.005,
                        correct=correct_param,  # type: ignore
                        quiet=False  # Show correction details
                    )
                    if not result:
                        logger.info(f"Corrected cache issues for {ticker}")
                    else:
                        logger.debug(f"No corrections needed for {ticker}")
                        
                    if correction_mode == 'one' and not result:
                        break  # Stop after first correction
                        
                return True
            else:
                # Correct entire cache
                # Use type: ignore to handle the union type issue
                result = yfc.verify_cached_tickers_prices(
                    rtol=0.0001,
                    vol_rtol=0.005,
                    correct=correct_param,  # type: ignore
                    halt_on_fail=False  # Don't stop on failures when correcting
                )
                logger.info(f"Cache correction completed: {result}")
                return True
                
        except Exception as e:
            logger.error(f"Error during cache correction: {e}")
            return False
    
    def clear_cache(self, tickers: Optional[List[str]] = None) -> None:
        """
        Clear cache for specific tickers or entire cache.
        
        Args:
            tickers: List of tickers to clear (None = clear all)
        """
        try:
            if tickers:
                for ticker in tickers:
                    # yfinance-cache doesn't have per-ticker clear, but we can force refresh
                    stock = yfc.Ticker(ticker)
                    # Force refresh by getting data with max_age=0
                    stock.history(period="1d", max_age="0s")
                    logger.info(f"Forced refresh for {ticker}")
            else:
                # For clearing entire cache, user would need to manually delete cache directory
                # or we can provide instructions
                cache_dir = yfc.options.cache_dir if hasattr(yfc.options, 'cache_dir') else None
                logger.info(f"To clear entire cache, delete directory: {cache_dir}")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def enable_offline_mode(self) -> None:
        """Enable offline mode - use only cached data."""
        yfc.options.session.offline = True
        logger.info("Enabled offline mode - using only cached data")
    
    def disable_offline_mode(self) -> None:
        """Disable offline mode - allow web fetches."""
        yfc.options.session.offline = False
        logger.info("Disabled offline mode - allowing web fetches")
    
    def save_data_to_csv(self, 
                        tickers: List[str],
                        period: str = "1y",
                        interval: str = "1d",
                        output_dir: str = "data",
                        include_fundamentals: bool = True) -> Dict[str, str]:
        """
        Fetch data and save to CSV files for persistent storage.
        
        Args:
            tickers: List of ticker symbols
            period: Historical data period
            interval: Data interval
            output_dir: Directory to save CSV files
            include_fundamentals: Whether to fetch and save fundamental data
            
        Returns:
            Dictionary with file paths of saved CSV files
        """
        os.makedirs(output_dir, exist_ok=True)
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get historical data
        try:
            logger.info(f"Fetching and saving price data for {len(tickers)} tickers...")
            price_data = self.get_historical_data(tickers, period, interval)
            
            if not price_data.empty:
                # Save price data with timestamp
                price_file = os.path.join(output_dir, f"price_data_{period}_{interval}_{timestamp}.csv")
                price_data.to_csv(price_file)
                saved_files['price_data'] = price_file
                logger.info(f"Saved price data to {price_file}")
                
                # Also save a 'latest' version for easy access
                latest_price_file = os.path.join(output_dir, f"price_data_{period}_{interval}_latest.csv")
                price_data.to_csv(latest_price_file)
                saved_files['price_data_latest'] = latest_price_file
                logger.info(f"Saved latest price data to {latest_price_file}")
            else:
                logger.warning("No price data to save")
                
        except Exception as e:
            logger.error(f"Error saving price data: {e}")
        
        # Get and save fundamental data
        if include_fundamentals:
            try:
                logger.info(f"Fetching and saving fundamental data for {len(tickers)} tickers...")
                fundamental_data = self.get_fundamentals(tickers)
                
                # Convert fundamental data to DataFrame for CSV saving
                fund_records = []
                for ticker, data in fundamental_data.items():
                    if 'error' not in data and isinstance(data, dict):
                        record = {'ticker': ticker}
                        # Add scalar values only (skip complex objects)
                        for key, value in data.items():
                            if not isinstance(value, (dict, pd.DataFrame, list)) and key != 'info':
                                record[key] = value
                            elif key == 'info' and isinstance(value, dict):
                                # Add key info fields
                                for info_key in ['marketCap', 'enterpriseValue', 'trailingPE', 'forwardPE', 
                                               'priceToBook', 'debtToEquity', 'returnOnEquity', 'beta',
                                               'dividendYield', 'payoutRatio', 'profitMargins']:
                                    if info_key in value:
                                        record[f'info_{info_key}'] = value[info_key]
                        fund_records.append(record)
                
                if fund_records:
                    fund_df = pd.DataFrame(fund_records)
                    
                    # Save fundamental data with timestamp
                    fund_file = os.path.join(output_dir, f"fundamental_data_{timestamp}.csv")
                    fund_df.to_csv(fund_file, index=False)
                    saved_files['fundamental_data'] = fund_file
                    logger.info(f"Saved fundamental data to {fund_file}")
                    
                    # Also save a 'latest' version
                    latest_fund_file = os.path.join(output_dir, "fundamental_data_latest.csv")
                    fund_df.to_csv(latest_fund_file, index=False)
                    saved_files['fundamental_data_latest'] = latest_fund_file
                    logger.info(f"Saved latest fundamental data to {latest_fund_file}")
                else:
                    logger.warning("No fundamental data to save")
                    
            except Exception as e:
                logger.error(f"Error saving fundamental data: {e}")
        
        return saved_files


# Convenience functions for easy usage with enhanced client
def get_sp500_universe() -> pd.DataFrame:
    """Get S&P 500 universe data."""
    manager = TickerManager()
    return manager.get_universe()


def fetch_stock_data_enhanced(tickers: List[str], 
                             period: str = "1y",
                             interval: str = "1d", 
                             include_fundamentals: bool = True,
                             force_refresh: bool = False,
                             validate_tickers: bool = True) -> Tuple[pd.DataFrame, Optional[Dict]]:
    """
    Enhanced convenience function to fetch both price and fundamental data.
    
    Args:
        tickers: List of ticker symbols
        period: Historical data period
        interval: Data interval
        include_fundamentals: Whether to fetch fundamental data
        force_refresh: Force refresh regardless of cache
        validate_tickers: Validate tickers before fetching data
        
    Returns:
        Tuple of (price_data, fundamental_data)
    """
    client = YFinanceCacheClient()
    
    # Validate tickers first if requested
    working_tickers = tickers
    if validate_tickers:
        valid_tickers, invalid_tickers = client.validate_tickers(tickers)
        if invalid_tickers:
            logger.warning(f"Skipping {len(invalid_tickers)} invalid tickers: {invalid_tickers[:5]}{'...' if len(invalid_tickers) > 5 else ''}")
        working_tickers = valid_tickers
        if not working_tickers:
            raise ValueError("No valid tickers found after validation")
    
    price_data = client.get_historical_data(
        working_tickers, 
        period=period, 
        interval=interval,
        force_refresh=force_refresh,
        validate_tickers_first=False  # Already validated above if requested
    )
    
    fundamental_data = None
    if include_fundamentals:
        fundamental_data = client.get_fundamentals(working_tickers, force_refresh=force_refresh)
    
    return price_data, fundamental_data


def run_full_data_collection(save_to_csv: bool = True, 
                           period: str = "1y",
                           interval: str = "1d",
                           include_us: bool = True,
                           include_hk: bool = False,
                           output_dir: str = "data") -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Complete data collection workflow - run once to get all data and optionally save to CSV.
    
    Args:
        save_to_csv: Whether to save data to CSV files
        period: Historical data period
        interval: Data interval
        include_us: Whether to include US stocks
        include_hk: Whether to include HK stocks
        output_dir: Directory to save CSV files
        
    Returns:
        Tuple of (universe_df, price_data_df, fundamental_data_df)
    """
    logger.info("Starting full data collection workflow...")
    
    # Step 1: Get universe
    ticker_manager = TickerManager(universe_file=os.path.join(output_dir, "full_universe_tickers.csv"))
    universe_df = ticker_manager.get_universe()
    
    if universe_df.empty:
        logger.info("Creating new universe...")
        universe_df = ticker_manager.create_full_universe(include_us=include_us, include_hk=include_hk)
    
    tickers = universe_df['ticker'].tolist()
    logger.info(f"Loaded {len(tickers)} tickers from universe")
    
    # Step 2: Get stock data
    client = YFinanceCacheClient()
    
    # Initialize return variables
    price_data_df = None
    fundamental_data_df = None
    
    if save_to_csv:
        # Save data to CSV and also return DataFrames
        saved_files = client.save_data_to_csv(
            tickers, 
            period=period, 
            interval=interval,
            output_dir=output_dir,
            include_fundamentals=True
        )
        
        # Load the saved CSV files as DataFrames
        if 'price_data_latest' in saved_files:
            try:
                price_data_df = pd.read_csv(saved_files['price_data_latest'], index_col=0)
                logger.info(f"Loaded price data CSV: {price_data_df.shape}")
            except Exception as e:
                logger.error(f"Error loading price data CSV: {e}")
        
        if 'fundamental_data_latest' in saved_files:
            try:
                fundamental_data_df = pd.read_csv(saved_files['fundamental_data_latest'])
                logger.info(f"Loaded fundamental data CSV: {fundamental_data_df.shape}")
            except Exception as e:
                logger.error(f"Error loading fundamental data CSV: {e}")
        
        logger.info(f"Data saved to files: {saved_files}")
    else:
        # Just fetch data without saving
        price_data, fundamental_data = fetch_stock_data_enhanced(
            tickers, 
            period=period, 
            interval=interval,
            include_fundamentals=True
        )
        price_data_df = price_data
        
        # Convert fundamental_data dict to DataFrame if needed
        if fundamental_data:
            fund_records = []
            for ticker, data in fundamental_data.items():
                if 'error' not in data and isinstance(data, dict):
                    record = {'ticker': ticker}
                    for key, value in data.items():
                        if not isinstance(value, (dict, pd.DataFrame, list)) and key != 'info':
                            record[key] = value
                    fund_records.append(record)
            if fund_records:
                fundamental_data_df = pd.DataFrame(fund_records)
    
    logger.info("Full data collection completed!")
    return universe_df, price_data_df, fundamental_data_df


def load_latest_data(data_dir: str = "data") -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load the latest saved data from CSV files.
    
    Args:
        data_dir: Directory containing the CSV files
        
    Returns:
        Tuple of (universe_df, price_data_df, fundamental_data_df)
    """
    universe_df = None
    price_data_df = None
    fundamental_data_df = None
    
    # Load universe
    universe_file = os.path.join(data_dir, "full_universe_tickers.csv")
    if os.path.exists(universe_file):
        try:
            universe_df = pd.read_csv(universe_file)
            logger.info(f"Loaded universe data: {len(universe_df)} tickers")
        except Exception as e:
            logger.error(f"Error loading universe data: {e}")
    
    # Load latest price data
    price_files = [f for f in os.listdir(data_dir) if f.startswith("price_data_") and f.endswith("_latest.csv")]
    if price_files:
        latest_price_file = os.path.join(data_dir, price_files[0])  # Should only be one 'latest' file
        try:
            price_data_df = pd.read_csv(latest_price_file, index_col=0)
            logger.info(f"Loaded price data: {price_data_df.shape}")
        except Exception as e:
            logger.error(f"Error loading price data: {e}")
    
    # Load latest fundamental data
    fund_file = os.path.join(data_dir, "fundamental_data_latest.csv")
    if os.path.exists(fund_file):
        try:
            fundamental_data_df = pd.read_csv(fund_file)
            logger.info(f"Loaded fundamental data: {len(fundamental_data_df)} records")
        except Exception as e:
            logger.error(f"Error loading fundamental data: {e}")
    
    return universe_df, price_data_df, fundamental_data_df


def should_refresh_data(data_dir: str = "data", max_age_hours: int = 24) -> bool:
    """
    Check if saved data is older than max_age_hours and should be refreshed.
    
    Args:
        data_dir: Directory containing the CSV files
        max_age_hours: Maximum age in hours before refresh is needed
        
    Returns:
        True if data should be refreshed, False otherwise
    """
    latest_files = [
        os.path.join(data_dir, "price_data_1y_1d_latest.csv"),
        os.path.join(data_dir, "fundamental_data_latest.csv")
    ]
    
    for file_path in latest_files:
        if not os.path.exists(file_path):
            logger.info(f"File {file_path} doesn't exist, refresh needed")
            return True
        
        # Check file age
        file_age = time.time() - os.path.getmtime(file_path)
        age_hours = file_age / 3600
        
        if age_hours > max_age_hours:
            logger.info(f"File {file_path} is {age_hours:.1f} hours old, refresh needed")
            return True
    
    logger.info("Data is fresh, no refresh needed")
    return False