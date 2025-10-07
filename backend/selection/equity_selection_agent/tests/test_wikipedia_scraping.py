"""
Test script for Wikipedia S&P 500 scraping functionality.

This script tests the Wikipedia scraping method in isolation to ensure
it properly extracts ticker symbols without yfinance validation.
"""

import sys
import os
import logging
import pandas as pd
import requests
import bs4 as bs
from typing import List, Dict

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_wikipedia_scraping_beautifulsoup():
    """
    Test the BeautifulSoup method for scraping S&P 500 tickers from Wikipedia.
    """
    logger.info("Testing Wikipedia scraping with BeautifulSoup...")
    
    try:
        # Add proper headers to avoid 403 Forbidden
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Download S&P 500 page from Wikipedia
        logger.info("Fetching Wikipedia page...")
        resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies', 
                          headers=headers, timeout=10)
        resp.raise_for_status()
        logger.info(f"Successfully fetched page. Status: {resp.status_code}")
        
        # Parse with BeautifulSoup
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        table = soup.find('table', {'class': 'wikitable sortable'})
        
        if not table:
            logger.error("Could not find the S&P 500 table on Wikipedia")
            return False
        
        logger.info("Found Wikipedia table")
        
        # Extract data from table rows
        tickers_list: List[Dict[str, str]] = []
        
        # Skip header row and process data rows
        rows = table.find_all('tr')[1:]  # Skip header
        
        logger.info(f"Found {len(rows)} companies in Wikipedia table")
        
        # Analyze first few rows to understand structure
        logger.info("Analyzing table structure...")
        if rows:
            first_row = rows[0]
            cells = first_row.find_all('td')
            logger.info(f"First row has {len(cells)} cells")
            for i, cell in enumerate(cells[:6]):  # Show first 6 cells
                content = cell.get_text(strip=True)
                logger.info(f"  Cell {i}: '{content}'")
        
        # Process all rows
        valid_tickers = []
        invalid_entries = []
        
        for idx, row in enumerate(rows):
            try:
                cells = row.find_all('td')
                if len(cells) < 3:  # Need at least ticker, name, sector
                    logger.debug(f"Row {idx}: insufficient cells ({len(cells)})")
                    continue
                
                # Extract data from cells
                ticker = cells[0].get_text(strip=True)
                company_name = cells[1].get_text(strip=True)
                sector = cells[2].get_text(strip=True) if len(cells) > 2 else 'Unknown'
                industry = cells[3].get_text(strip=True) if len(cells) > 3 else 'Unknown'
                
                # Clean up ticker symbol (remove any extra characters)
                original_ticker = ticker
                ticker = ticker.replace('.', '-').strip()
                
                # Basic validation - check if ticker looks like a valid stock symbol
                if not ticker:
                    invalid_entries.append(f"Empty ticker at row {idx}")
                    continue
                
                # Check for invalid patterns (dates, long strings, special characters)
                if any(char.isdigit() for char in ticker) and len(ticker) > 5:
                    invalid_entries.append(f"Suspicious ticker '{ticker}' (contains digits and long)")
                    continue
                
                if ' ' in ticker or ',' in ticker or len(ticker) > 10:
                    invalid_entries.append(f"Invalid ticker format '{ticker}'")
                    continue
                
                # Check for date-like patterns
                if any(month in ticker.upper() for month in ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 
                                                            'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']):
                    invalid_entries.append(f"Ticker contains month name '{ticker}'")
                    continue
                
                ticker_info = {
                    'ticker': ticker,
                    'original_ticker': original_ticker,
                    'region': 'US',
                    'sector': sector,
                    'industry': industry,
                    'name': company_name,
                    'row_index': idx
                }
                
                valid_tickers.append(ticker_info)
                tickers_list.append(ticker_info)
                
                # Log some examples
                if idx < 10 or idx % 50 == 0:
                    logger.info(f"Row {idx}: {ticker} - {company_name} ({sector})")
                    
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                invalid_entries.append(f"Row {idx}: {str(e)}")
                continue
        
        # Summary results
        logger.info(f"\n=== SCRAPING RESULTS ===")
        logger.info(f"Total rows processed: {len(rows)}")
        logger.info(f"Valid tickers extracted: {len(valid_tickers)}")
        logger.info(f"Invalid entries: {len(invalid_entries)}")
        
        # Show first 10 valid tickers
        logger.info(f"\nFirst 10 valid tickers:")
        for i, ticker_info in enumerate(valid_tickers[:10]):
            logger.info(f"  {i+1}. {ticker_info['ticker']} - {ticker_info['name']}")
        
        # Show invalid entries if any
        if invalid_entries:
            logger.warning(f"\nInvalid entries found:")
            for entry in invalid_entries[:10]:  # Show first 10
                logger.warning(f"  {entry}")
            if len(invalid_entries) > 10:
                logger.warning(f"  ... and {len(invalid_entries) - 10} more")
        
        # Check for suspicious patterns in all tickers
        suspicious_tickers = []
        for ticker_info in valid_tickers:
            ticker = ticker_info['ticker']
            if len(ticker) > 6 or any(char.isdigit() for char in ticker):
                suspicious_tickers.append(ticker_info)
        
        if suspicious_tickers:
            logger.warning(f"\nSuspicious tickers found:")
            for ticker_info in suspicious_tickers[:20]:  # Show first 20
                logger.warning(f"  {ticker_info['ticker']} (original: {ticker_info['original_ticker']}) - {ticker_info['name']}")
        
        # Create a summary DataFrame for analysis
        if valid_tickers:
            df = pd.DataFrame(valid_tickers)
            logger.info(f"\nDataFrame created with shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Show sector distribution
            sector_counts = df['sector'].value_counts()
            logger.info(f"\nSector distribution:")
            for sector, count in sector_counts.head(10).items():
                logger.info(f"  {sector}: {count}")
            
            # Save to CSV for inspection
            output_file = os.path.join(os.path.dirname(__file__), 'wikipedia_scraping_test_results.csv')
            df.to_csv(output_file, index=False)
            logger.info(f"\nResults saved to: {output_file}")
        
        # Success criteria
        success = len(valid_tickers) > 400 and len(invalid_entries) < 50
        
        logger.info(f"\n=== TEST RESULT ===")
        if success:
            logger.info("✅ Wikipedia scraping test PASSED")
            logger.info(f"   - Extracted {len(valid_tickers)} valid tickers")
            logger.info(f"   - {len(invalid_entries)} invalid entries (acceptable)")
        else:
            logger.error("❌ Wikipedia scraping test FAILED")
            logger.error(f"   - Only {len(valid_tickers)} valid tickers (expected > 400)")
            logger.error(f"   - {len(invalid_entries)} invalid entries (expected < 50)")
        
        return success
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def test_pandas_readhtml_method():
    """
    Test the pandas read_html method as comparison.
    """
    logger.info("\nTesting pandas read_html method...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        
        # Use requests with headers first, then pass to pandas
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Read the tables from the response content
        tables = pd.read_html(response.text)
        sp500_df = tables[0]  # First table contains current S&P 500 companies
        
        logger.info(f"pandas read_html found {len(tables)} tables")
        logger.info(f"First table shape: {sp500_df.shape}")
        logger.info(f"Columns: {list(sp500_df.columns)}")
        
        # Show first few rows
        logger.info("\nFirst 5 rows:")
        logger.info(sp500_df.head().to_string())
        
        # Check for valid ticker symbols in first column
        if len(sp500_df.columns) > 0:
            first_col = sp500_df.iloc[:, 0]
            logger.info(f"\nFirst 10 entries in first column:")
            for i, value in enumerate(first_col.head(10)):
                logger.info(f"  {i}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"pandas read_html method failed: {e}")
        return False


def main():
    """
    Run all Wikipedia scraping tests.
    """
    logger.info("Starting Wikipedia S&P 500 scraping tests...")
    
    # Test 1: BeautifulSoup method
    bs_success = test_wikipedia_scraping_beautifulsoup()
    
    # Test 2: pandas read_html method
    pandas_success = test_pandas_readhtml_method()
    
    # Overall results
    logger.info(f"\n=== OVERALL TEST RESULTS ===")
    logger.info(f"BeautifulSoup method: {'✅ PASSED' if bs_success else '❌ FAILED'}")
    logger.info(f"pandas read_html method: {'✅ PASSED' if pandas_success else '❌ FAILED'}")
    
    if bs_success:
        logger.info("\n✅ Wikipedia scraping is working correctly!")
        logger.info("You can now proceed with yfinance integration.")
    else:
        logger.error("\n❌ Wikipedia scraping has issues that need to be fixed.")
        logger.error("Check the invalid entries and adjust the parsing logic.")


if __name__ == "__main__":
    main()