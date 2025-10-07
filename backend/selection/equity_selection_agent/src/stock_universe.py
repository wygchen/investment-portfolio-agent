"""
Core Data Provider Classes for Equity Selection Agent (ESA)

This module contains the core classes that are used by the enhanced_data_provider.
These classes handle universe management and data fetching functionality.

Classes:
- TickerManager: Manages US (S&P 500) and HK universe lists
- YFinanceCacheClient: Enhanced client using yfinance-cache for better performance

Note: For new implementations, use enhanced_data_provider.py which includes SQLite storage
and incremental updates.
"""

import pandas as pd
import yfinance_cache as yfc
import requests
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from io import StringIO

# Set up logging
logger = logging.getLogger(__name__)


class TickerManager:
    """
    Manages the US (S&P 500) and HK universe lists with mandatory Region tagging.
    """
    
    def __init__(self, universe_file: str = "data/full_universe_tickers.csv"):
        self.universe_file = universe_file
        self._universe_df: Optional[pd.DataFrame] = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(universe_file), exist_ok=True)
    
    def load_sp500_tickers(self) -> List[Dict[str, str]]:
        """
        Load S&P 500 tickers from Wikipedia using pandas read_html for reliability.
        
        Returns:
            List of dictionaries with ticker, region, and sector information
        """
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
            tables = pd.read_html(StringIO(response.text))
            sp500_df = tables[0]  # First table contains current S&P 500 companies
            
            # Clean up the DataFrame columns
            sp500_df.columns = sp500_df.columns.str.strip()
            
            logger.info(f"Retrieved {len(sp500_df)} companies from Wikipedia")
            
            # Extract ticker symbols and sector information
            tickers_list: List[Dict[str, str]] = []
            
            for idx, row in sp500_df.iterrows():
                try:
                    # Convert idx to int for proper arithmetic
                    row_num = int(idx) if isinstance(idx, (int, float)) else 0
                    
                    # Get ticker symbol (usually in 'Symbol' column)
                    ticker = str(row.get('Symbol', row.iloc[0])).strip()
                    
                    # Basic validation - check if ticker looks valid
                    if not ticker or ticker == 'nan' or len(ticker) > 10:
                        continue
                        
                    # Check for date-like patterns that were causing issues
                    if any(month in ticker.upper() for month in ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 
                                                                'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']):
                        continue
                    
                    # Check for numbers and commas that suggest invalid data
                    if ',' in ticker or any(char.isdigit() for char in ticker.replace('-', '')):
                        if len(ticker) > 5:  # Allow short tickers with numbers (like 3M -> MMM)
                            continue
                    
                    # Get sector and industry information
                    sector = str(row.get('GICS Sector', 'Unknown')).strip()
                    industry = str(row.get('GICS Sub-Industry', 'Unknown')).strip()
                    company_name = str(row.get('Security', row.get('Company', 'Unknown'))).strip()
                    
                    # Clean up ticker symbol (replace dots with dashes for Yahoo Finance)
                    ticker = ticker.replace('.', '-').strip()
                    
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
                        logger.info(f"Processed {row_num + 1}/{len(sp500_df)} tickers")
                        
                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    continue
            
            if len(tickers_list) > 400:  # Should have ~500 companies
                logger.info(f"Successfully loaded {len(tickers_list)} S&P 500 tickers from Wikipedia")
                return tickers_list
            else:
                logger.warning(f"Only got {len(tickers_list)} valid tickers from Wikipedia, trying fallback method")
                
        except Exception as e:
            logger.warning(f"pandas read_html method failed: {e}")
        
        # Fallback to hardcoded list if Wikipedia fails
        return self._get_fallback_sp500_tickers()
    
    def _get_fallback_sp500_tickers(self) -> List[Dict[str, str]]:
        """
        Fallback list of S&P 500 tickers if web scraping fails.
        """
        logger.info("Using fallback S&P 500 ticker list...")
        
        # Sample of major S&P 500 companies
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
        
        # Convert to proper format
        fallback_list = []
        for ticker in fallback_tickers:
            fallback_list.append({
                'ticker': ticker,
                'region': 'US',
                'sector': 'Unknown',
                'industry': 'Unknown',
                'name': 'Unknown'
            })
        
        logger.info(f"Prepared {len(fallback_list)} fallback tickers")
        return fallback_list
    
    def load_hk_tickers(self) -> List[Dict[str, str]]:
        """
        Load HK market tickers. Currently returns placeholder.
        TODO: Implement HK market ticker loading
        
        Returns:
            List of dictionaries with ticker, region, and sector information
        """
        # Major Hong Kong listed companies across key sectors
        hk_tickers = [
            # Financial Services - Banks
            {'ticker': '0005.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Banks', 'name': 'HSBC Holdings'},
            {'ticker': '0939.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Banks', 'name': 'China Construction Bank'},
            {'ticker': '3988.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Banks', 'name': 'Bank of China'},
            {'ticker': '1398.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Banks', 'name': 'Industrial and Commercial Bank of China'},
            {'ticker': '2388.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Banks', 'name': 'BOC Hong Kong Holdings'},
            {'ticker': '0011.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Banks', 'name': 'Hang Seng Bank'},
            {'ticker': '3968.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Banks', 'name': 'China Merchants Bank'},
            
            # Financial Services - Insurance
            {'ticker': '2318.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Insurance', 'name': 'Ping An Insurance'},
            {'ticker': '2628.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Insurance', 'name': 'China Life Insurance'},
            {'ticker': '1299.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Insurance', 'name': 'AIA Group'},
            {'ticker': '1336.HK', 'region': 'HK', 'sector': 'Financial Services', 'industry': 'Insurance', 'name': 'New China Life Insurance'},
            
            # Technology
            {'ticker': '0700.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Internet Content & Information', 'name': 'Tencent Holdings'},
            {'ticker': '9988.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Internet Retail', 'name': 'Alibaba Group'},
            {'ticker': '3690.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Internet Content & Information', 'name': 'Meituan'},
            {'ticker': '1024.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Internet Content & Information', 'name': 'Kuaishou Technology'},
            {'ticker': '9618.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Internet Retail', 'name': 'JD.com'},
            {'ticker': '2382.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Electronic Gaming & Multimedia', 'name': 'Sunny Optical Technology'},
            {'ticker': '0981.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Semiconductors', 'name': 'SMIC'},
            {'ticker': '1810.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Electronics', 'name': 'Xiaomi Corporation'},
            
            # Communication Services
            {'ticker': '0941.HK', 'region': 'HK', 'sector': 'Communication Services', 'industry': 'Telecom Services', 'name': 'China Mobile'},
            {'ticker': '0762.HK', 'region': 'HK', 'sector': 'Communication Services', 'industry': 'Telecom Services', 'name': 'China Unicom'},
            {'ticker': '0728.HK', 'region': 'HK', 'sector': 'Communication Services', 'industry': 'Telecom Services', 'name': 'China Telecom'},
            
            # Energy
            {'ticker': '0857.HK', 'region': 'HK', 'sector': 'Energy', 'industry': 'Oil & Gas Integrated', 'name': 'PetroChina'},
            {'ticker': '0386.HK', 'region': 'HK', 'sector': 'Energy', 'industry': 'Oil & Gas Integrated', 'name': 'Sinopec Corp'},
            {'ticker': '0883.HK', 'region': 'HK', 'sector': 'Energy', 'industry': 'Oil & Gas Integrated', 'name': 'CNOOC'},
            
            # Consumer Discretionary
            {'ticker': '2319.HK', 'region': 'HK', 'sector': 'Consumer Staples', 'industry': 'Food Products', 'name': 'Mengniu Dairy'},
            {'ticker': '0175.HK', 'region': 'HK', 'sector': 'Consumer Discretionary', 'industry': 'Auto Manufacturers', 'name': 'Geely Automobile'},
            {'ticker': '1211.HK', 'region': 'HK', 'sector': 'Consumer Discretionary', 'industry': 'Auto Manufacturers', 'name': 'BYD Company'},
            {'ticker': '2020.HK', 'region': 'HK', 'sector': 'Consumer Discretionary', 'industry': 'Apparel Manufacturing', 'name': 'ANTA Sports Products'},
            {'ticker': '0027.HK', 'region': 'HK', 'sector': 'Consumer Discretionary', 'industry': 'Department Stores', 'name': 'Galaxy Entertainment'},
            {'ticker': '0992.HK', 'region': 'HK', 'sector': 'Technology', 'industry': 'Computer Hardware', 'name': 'Lenovo Group'},
            
            # Consumer Staples
            {'ticker': '0291.HK', 'region': 'HK', 'sector': 'Consumer Staples', 'industry': 'Beverages—Non-Alcoholic', 'name': 'China Resources Beer'},
            {'ticker': '1044.HK', 'region': 'HK', 'sector': 'Consumer Staples', 'industry': 'Food Distribution', 'name': 'Hengan International'},
            {'ticker': '0288.HK', 'region': 'HK', 'sector': 'Consumer Staples', 'industry': 'Specialty Retail', 'name': 'WH Group'},
            
            # Healthcare
            {'ticker': '1093.HK', 'region': 'HK', 'sector': 'Healthcare', 'industry': 'Pharmaceutical Retailers', 'name': 'CSPC Pharmaceutical Group'},
            {'ticker': '6618.HK', 'region': 'HK', 'sector': 'Healthcare', 'industry': 'Biotechnology', 'name': 'JD Health International'},
            {'ticker': '2269.HK', 'region': 'HK', 'sector': 'Healthcare', 'industry': 'Medical Devices', 'name': 'Wuxi Biologics'},
            {'ticker': '1177.HK', 'region': 'HK', 'sector': 'Healthcare', 'industry': 'Drug Manufacturers', 'name': 'Sino Biopharmaceutical'},
            
            # Materials
            {'ticker': '0914.HK', 'region': 'HK', 'sector': 'Materials', 'industry': 'Building Materials', 'name': 'Anhui Conch Cement'},
            {'ticker': '1088.HK', 'region': 'HK', 'sector': 'Materials', 'industry': 'Steel', 'name': 'China Shenhua Energy'},
            
            # Industrials
            {'ticker': '0753.HK', 'region': 'HK', 'sector': 'Industrials', 'industry': 'Airlines', 'name': 'Air China'},
            {'ticker': '1055.HK', 'region': 'HK', 'sector': 'Industrials', 'industry': 'Marine Shipping', 'name': 'China Southern Airlines'},
            {'ticker': '2007.HK', 'region': 'HK', 'sector': 'Industrials', 'industry': 'Farm & Heavy Construction Machinery', 'name': 'Country Garden'},
            {'ticker': '0390.HK', 'region': 'HK', 'sector': 'Industrials', 'industry': 'Railroads', 'name': 'China Railway Group'},
            {'ticker': '1919.HK', 'region': 'HK', 'sector': 'Industrials', 'industry': 'Engineering & Construction', 'name': 'COSCO SHIPPING Holdings'},
            
            # Utilities
            {'ticker': '0002.HK', 'region': 'HK', 'sector': 'Utilities', 'industry': 'Utilities—Regulated Electric', 'name': 'CLP Holdings'},
            {'ticker': '0003.HK', 'region': 'HK', 'sector': 'Utilities', 'industry': 'Utilities—Regulated Gas', 'name': 'Hong Kong and China Gas'},
            {'ticker': '1038.HK', 'region': 'HK', 'sector': 'Utilities', 'industry': 'Utilities—Regulated Electric', 'name': 'Cheung Kong Infrastructure'},
            
        ]
        
        logger.info(f"Loaded {len(hk_tickers)} HK equity tickers")
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
        
        logger.info(f"Created universe with {len(self._universe_df)} total tickers")
        return self._universe_df


class StockDataFetcher:
    """
    Simplified StockDataFetcher that only includes methods used by enhanced_data_provider.py
    """
    
    def __init__(self):
        # Configure yfinance-cache options for optimal performance
        self._configure_cache_settings()
        logger.info("Initialized StockDataFetcher with intelligent caching")
    
    def _configure_cache_settings(self) -> None:
        """Configure yfinance-cache settings for optimal performance."""
        # Set fundamental data aging - less frequent updates
        yfc.options.max_ages.info = "7d"  # Weekly updates for basic info
        yfc.options.max_ages.financials = "30d"  # Monthly for financial statements
        yfc.options.max_ages.balance_sheet = "30d"
        yfc.options.max_ages.cashflow = "30d"
        yfc.options.max_ages.calendar = "14d"  # Bi-weekly for earnings calendar
        
        logger.info("Configured yfinance-cache settings for optimal performance")
    
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
                
                # Get basic info (cached intelligently)
                info = stock.info if hasattr(stock, 'info') else {}
                
                if info:
                    # Get news data (top 10 news items)
                    news_data = []
                    try:
                        if hasattr(stock, 'news') and stock.news:
                            # Get top 10 news items and extract relevant information
                            news_items = stock.news[:10] if len(stock.news) >= 10 else stock.news
                            for news_item in news_items:
                                if isinstance(news_item, dict):
                                    # Handle new yfinance news structure
                                    content = news_item.get('content', {})
                                    if isinstance(content, dict):
                                        news_summary = {
                                            'title': content.get('title', ''),
                                            'summary': content.get('summary', ''),
                                            'description': content.get('description', ''),
                                            'publisher': content.get('provider', {}).get('displayName', ''),
                                            'link': content.get('canonicalUrl', {}).get('url', ''),
                                            'pubDate': content.get('pubDate', ''),
                                            'displayTime': content.get('displayTime', '')
                                        }
                                        news_data.append(news_summary)
                        
                        # Convert to JSON string for storage
                        import json
                        news_json = json.dumps(news_data) if news_data else ''
                        
                    except Exception as e:
                        logger.warning(f"Error fetching news for {ticker}: {e}")
                        news_json = ''
                    
                    # Extract key fundamental metrics
                    fundamental_record = {
                        'ticker': ticker,
                        'market_cap': info.get('marketCap'),
                        'enterprise_value': info.get('enterpriseValue'),
                        'trailing_pe': info.get('trailingPE'),
                        'forward_pe': info.get('forwardPE'),
                        'price_to_book': info.get('priceToBook'),
                        'debt_to_equity': info.get('debtToEquity'),
                        'return_on_equity': info.get('returnOnEquity'),
                        'current_price': info.get('currentPrice'),
                        'trailing_eps': info.get('trailingEps'),
                        'beta': info.get('beta'),
                        'news': news_json,
                    }
                    
                    fundamental_data[ticker] = fundamental_record
                else:
                    fundamental_data[ticker] = {'error': 'No data available'}
                    
            except Exception as e:
                logger.warning(f"Error fetching fundamentals for {ticker}: {e}")
                fundamental_data[ticker] = {'error': str(e)}
            
            # Log progress
            if (i + 1) % 50 == 0:
                logger.info(f"Processed fundamentals for {i + 1}/{len(tickers)} tickers")
        
        successful = len([k for k, v in fundamental_data.items() if 'error' not in v])
        logger.info(f"Successfully fetched fundamental data for {successful}/{len(tickers)} tickers")
        
        return fundamental_data
