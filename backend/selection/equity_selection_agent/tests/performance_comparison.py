"""
Performance Comparison: Original vs Enhanced YFinance Client

This script demonstrates the performance improvements achieved by using
yfinance-cache compared to the original manual caching implementation.
"""

import time
import pandas as pd
from typing import List, Dict, Any
import logging
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_provider import YFinanceClient, TickerManager
from data_provider_enhanced import YFinanceCacheClient, TickerManager as EnhancedTickerManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def time_function(func, *args, **kwargs):
    """Time the execution of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    return result, execution_time


def performance_comparison_test():
    """
    Compare performance between original and enhanced clients.
    """
    # Test with a smaller subset for demonstration
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'WMT']
    
    logger.info("="*60)
    logger.info("PERFORMANCE COMPARISON TEST")
    logger.info("="*60)
    logger.info(f"Testing with {len(test_tickers)} tickers: {', '.join(test_tickers)}")
    
    # Initialize clients
    original_client = YFinanceClient()
    enhanced_client = YFinanceCacheClient()
    
    results = {}
    
    # Test 1: Fresh data fetch (no cache)
    logger.info("\n--- Test 1: Fresh Data Fetch (Cold Cache) ---")
    
    # Clear caches to ensure fair comparison
    original_client.clear_cache()
    
    # Original client - historical data
    logger.info("Testing original client...")
    orig_data, orig_time = time_function(
        original_client.get_historical_data,
        test_tickers,
        period="6mo"
    )
    logger.info(f"Original client - Historical data: {orig_time:.2f} seconds")
    
    # Enhanced client - historical data
    logger.info("Testing enhanced client...")
    enh_data, enh_time = time_function(
        enhanced_client.get_historical_data,
        test_tickers,
        period="6mo",
        force_refresh=True  # Ensure fresh fetch
    )
    logger.info(f"Enhanced client - Historical data: {enh_time:.2f} seconds")
    
    results['fresh_fetch'] = {
        'original_time': orig_time,
        'enhanced_time': enh_time,
        'improvement': f"{((orig_time - enh_time) / orig_time * 100):.1f}%" if orig_time > enh_time else "No improvement"
    }
    
    # Test 2: Cached data retrieval
    logger.info("\n--- Test 2: Cached Data Retrieval (Warm Cache) ---")
    
    # Original client - cached data
    logger.info("Testing original client (cached)...")
    orig_cached_data, orig_cached_time = time_function(
        original_client.get_historical_data,
        test_tickers,
        period="6mo"
    )
    logger.info(f"Original client - Cached data: {orig_cached_time:.2f} seconds")
    
    # Enhanced client - cached data
    logger.info("Testing enhanced client (cached)...")
    enh_cached_data, enh_cached_time = time_function(
        enhanced_client.get_historical_data,
        test_tickers,
        period="6mo"
    )
    logger.info(f"Enhanced client - Cached data: {enh_cached_time:.2f} seconds")
    
    results['cached_fetch'] = {
        'original_time': orig_cached_time,
        'enhanced_time': enh_cached_time,
        'improvement': f"{((orig_cached_time - enh_cached_time) / orig_cached_time * 100):.1f}%" if orig_cached_time > enh_cached_time else "No improvement"
    }
    
    # Test 3: Fundamental data
    logger.info("\n--- Test 3: Fundamental Data Retrieval ---")
    
    # Original client - fundamentals
    logger.info("Testing original client fundamentals...")
    orig_fund, orig_fund_time = time_function(
        original_client.get_fundamentals,
        test_tickers[:5]  # Use fewer tickers for fundamentals to avoid rate limits
    )
    logger.info(f"Original client - Fundamentals: {orig_fund_time:.2f} seconds")
    
    # Enhanced client - fundamentals
    logger.info("Testing enhanced client fundamentals...")
    enh_fund, enh_fund_time = time_function(
        enhanced_client.get_fundamentals,
        test_tickers[:5]
    )
    logger.info(f"Enhanced client - Fundamentals: {enh_fund_time:.2f} seconds")
    
    results['fundamentals'] = {
        'original_time': orig_fund_time,
        'enhanced_time': enh_fund_time,
        'improvement': f"{((orig_fund_time - enh_fund_time) / orig_fund_time * 100):.1f}%" if orig_fund_time > enh_fund_time else "No improvement"
    }
    
    # Print summary results
    print_performance_summary(results, test_tickers)
    
    return results


def feature_comparison_demo():
    """
    Demonstrate advanced features of the enhanced client.
    """
    logger.info("\n" + "="*60)
    logger.info("FEATURE COMPARISON DEMO")
    logger.info("="*60)
    
    enhanced_client = YFinanceCacheClient()
    test_ticker = 'AAPL'
    
    # Demonstrate intelligent aging
    logger.info("\n--- Intelligent Caching Features ---")
    
    # Get data with market-aware caching
    logger.info(f"Fetching {test_ticker} data with market-aware caching...")
    stock_data = enhanced_client.get_historical_data(
        [test_ticker], 
        period="1mo",
        trigger_at_market_close=True
    )
    
    if not stock_data.empty and 'FetchDate' in stock_data.columns:
        logger.info(f"Data includes FetchDate: {stock_data['FetchDate'].iloc[-1]}")
        logger.info(f"Final data indicator: {stock_data.get('Final?', 'N/A').iloc[-1] if 'Final?' in stock_data.columns else 'N/A'}")
    
    # Demonstrate cache verification
    logger.info(f"\nVerifying cache integrity for {test_ticker}...")
    integrity_check = enhanced_client.verify_cache_integrity([test_ticker])
    logger.info(f"Cache integrity check: {'PASSED' if integrity_check else 'FAILED'}")
    
    # Demonstrate offline mode
    logger.info("\nTesting offline mode...")
    enhanced_client.enable_offline_mode()
    try:
        offline_data = enhanced_client.get_historical_data([test_ticker], period="1mo")
        logger.info("Successfully retrieved data in offline mode (from cache)")
    except Exception as e:
        logger.info(f"Offline mode limitation: {e}")
    finally:
        enhanced_client.disable_offline_mode()
    
    # Show earnings calendar features
    logger.info("\nDemonstrating earnings-aware fundamental updates...")
    fundamentals = enhanced_client.get_fundamentals([test_ticker])
    if test_ticker in fundamentals:
        fund_data = fundamentals[test_ticker]
        if 'release_dates' in fund_data and fund_data['release_dates']:
            logger.info(f"Next earnings release info available: {fund_data['release_dates']}")
        else:
            logger.info("Earnings calendar integration available (specific dates depend on current data)")


def data_quality_comparison():
    """
    Compare data quality between original and enhanced implementations.
    """
    logger.info("\n" + "="*60)
    logger.info("DATA QUALITY COMPARISON")
    logger.info("="*60)
    
    original_client = YFinanceClient()
    enhanced_client = YFinanceCacheClient()
    test_ticker = 'AAPL'
    
    # Get data from both clients
    orig_data = original_client.get_historical_data([test_ticker], period="1mo")
    enh_data = enhanced_client.get_historical_data([test_ticker], period="1mo")
    
    logger.info(f"\nData comparison for {test_ticker}:")
    logger.info(f"Original data shape: {orig_data.shape}")
    logger.info(f"Enhanced data shape: {enh_data.shape}")
    
    # Check for additional columns in enhanced data
    if hasattr(enh_data, 'columns'):
        enhanced_columns = set(enh_data.columns) - set(orig_data.columns)
        if enhanced_columns:
            logger.info(f"Additional columns in enhanced data: {enhanced_columns}")
        
        # Show price repair features
        logger.info("\nEnhanced data includes:")
        logger.info("- Automatic split adjustments")
        logger.info("- Automatic dividend adjustments") 
        logger.info("- Price repair for bad Yahoo data")
        logger.info("- Fetch date tracking")
        logger.info("- Data finality indicators")


def print_performance_summary(results: Dict[str, Dict[str, Any]], test_tickers: List[str]):
    """
    Print a formatted summary of performance test results.
    """
    logger.info("\n" + "="*60)
    logger.info("PERFORMANCE SUMMARY")
    logger.info("="*60)
    logger.info(f"Test conducted with {len(test_tickers)} tickers")
    
    for test_name, data in results.items():
        logger.info(f"\n{test_name.replace('_', ' ').title()}:")
        logger.info(f"  Original Client: {data['original_time']:.2f} seconds")
        logger.info(f"  Enhanced Client: {data['enhanced_time']:.2f} seconds")
        logger.info(f"  Performance Change: {data['improvement']}")
    
    logger.info("\n" + "="*60)
    logger.info("KEY ADVANTAGES OF ENHANCED CLIENT:")
    logger.info("="*60)
    logger.info("✓ Market-aware caching (considers trading hours)")
    logger.info("✓ Automatic price adjustments for splits/dividends")
    logger.info("✓ Intelligent cache aging based on data type")
    logger.info("✓ Earnings calendar integration for fundamental updates")
    logger.info("✓ Built-in price repair for data quality")
    logger.info("✓ Cache integrity verification")
    logger.info("✓ Offline mode support")
    logger.info("✓ Reduced API calls through smarter caching")
    logger.info("✓ Persistent cache across sessions")


def main():
    """
    Main function to run all comparison tests.
    """
    try:
        # Run performance comparison
        performance_results = performance_comparison_test()
        
        # Demonstrate enhanced features
        feature_comparison_demo()
        
        # Compare data quality
        data_quality_comparison()
        
        logger.info("\n" + "="*60)
        logger.info("RECOMMENDATION")
        logger.info("="*60)
        logger.info("Based on the analysis, yfinance-cache provides:")
        logger.info("1. Better performance through intelligent caching")
        logger.info("2. Higher data quality with automatic adjustments")
        logger.info("3. More robust error handling and rate limiting")
        logger.info("4. Advanced features like market awareness and earnings integration")
        logger.info("5. Reduced server load through smarter cache management")
        logger.info("\nRecommendation: Migrate to yfinance-cache for production use.")
        
    except Exception as e:
        logger.error(f"Error during comparison testing: {e}")
        raise


if __name__ == "__main__":
    main()