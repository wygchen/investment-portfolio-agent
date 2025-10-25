#!/usr/bin/env python3
"""
Test script to verify API keys and news integration are working properly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test that all required environment variables are loaded"""
    print("🔍 Testing Environment Variables...")
    
    # WatsonX API Keys
    watsonx_apikey = os.getenv('WATSONX_APIKEY')
    watsonx_url = os.getenv('WATSONX_URL')
    proj_id = os.getenv('WATSONX_PROJECT_ID')
    
    print(f"WATSONX_APIKEY: {'✅ Set' if watsonx_apikey else '❌ Missing'}")
    print(f"WATSONX_URL: {'✅ Set' if watsonx_url else '❌ Missing'}")
    print(f"WATSONX_PROJECT_ID: {'✅ Set' if proj_id else '❌ Missing'}")
    
    # News API Keys
    newsapi_key = os.getenv('NEWSAPI_KEY')
    alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    
    print(f"NEWSAPI_KEY: {'✅ Set' if newsapi_key else '❌ Missing'}")
    print(f"ALPHA_VANTAGE_API_KEY: {'✅ Set' if alpha_vantage_key else '❌ Missing'}")
    print(f"FINNHUB_API_KEY: {'✅ Set' if finnhub_key else '❌ Missing'}")
    
    return {
        'watsonx_ready': all([watsonx_apikey, watsonx_url, proj_id]),
        'news_apis_available': any([newsapi_key, alpha_vantage_key, finnhub_key])
    }

def test_yfinance():
    """Test YFinance functionality"""
    print("\n📊 Testing YFinance...")
    
    try:
        import yfinance as yf
        
        # Test basic stock data fetch
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        news = ticker.news
        
        print(f"✅ YFinance working - AAPL price: ${info.get('currentPrice', 'N/A')}")
        print(f"✅ YFinance news - Found {len(news)} articles for AAPL")
        return True
        
    except Exception as e:
        print(f"❌ YFinance error: {e}")
        return False

def test_enhanced_market_analysis():
    """Test enhanced market analysis news functions"""
    print("\n📰 Testing Enhanced Market Analysis...")
    
    try:
        from enhanced_market_analysis import NewsSourceManager
        
        news_manager = NewsSourceManager()
        
        # Test Yahoo Finance news
        print("🔄 Testing Yahoo Finance news...")
        yahoo_news = news_manager.get_yahoo_finance_news("AAPL", 5)
        print(f"✅ Yahoo Finance: {len(yahoo_news)} articles")
        
        # Test NewsAPI if available (Priority 1)
        if os.getenv('NEWSAPI_KEY'):
            print("🔄 Testing NewsAPI (Priority 1)...")
            newsapi_news = news_manager.get_newsapi_news("AAPL", 3)
            print(f"✅ NewsAPI: {len(newsapi_news)} articles")
        else:
            print("⚠️ NewsAPI key not available")
        
        # Test Finnhub if available (Priority 2)
        if os.getenv('FINNHUB_API_KEY'):
            print("🔄 Testing Finnhub (Priority 2)...")
            finnhub_news = news_manager.get_finnhub_news("AAPL", 3)
            print(f"✅ Finnhub: {len(finnhub_news)} articles")
        else:
            print("⚠️ Finnhub key not available")
        
        # Test Alpha Vantage if available (Priority 4)
        if os.getenv('ALPHA_VANTAGE_API_KEY'):
            print("🔄 Testing Alpha Vantage (Priority 4)...")
            av_news = news_manager.get_alpha_vantage_news("AAPL", 3)
            print(f"✅ Alpha Vantage: {len(av_news)} articles")
        else:
            print("⚠️ Alpha Vantage key not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced market analysis error: {e}")
        return False



async def test_complete_pipeline():
    """Test the complete enhanced market analysis pipeline"""
    print("\n🔄 Testing Enhanced Market Analysis Pipeline...")
    
    try:
        from enhanced_market_analysis import get_enhanced_market_analysis
        
        # Test enhanced market analysis only
        print("🔄 Testing enhanced market analysis for AAPL...")
        result = await get_enhanced_market_analysis("AAPL")
        
        print(f"✅ Enhanced market analysis complete for AAPL")
        print(f"   Company: {result['stock_metrics'].get('company_name', 'N/A')}")
        print(f"   Price: ${result['stock_metrics'].get('current_price', 0):.2f}")
        print(f"   News articles: {len(result.get('related_news', []))}")
        print(f"   Event Summary: {result['ai_analysis'].get('event_summary', 'N/A')[:100]}...")
        print(f"   Market Sentiment: {result['ai_analysis'].get('market_sentiment', 'N/A')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced market analysis pipeline error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting API Key and Integration Tests\n")
    
    # Test environment variables
    env_status = test_environment_variables()
    
    # Test YFinance
    yfinance_ok = test_yfinance()
    
    # Test enhanced market analysis
    news_ok = test_enhanced_market_analysis()
    
    # Test complete pipeline (includes WatsonX LLM testing)
    pipeline_ok = await test_complete_pipeline()
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    print(f"Environment Variables: {'✅' if env_status['watsonx_ready'] else '❌'}")
    print(f"YFinance: {'✅' if yfinance_ok else '❌'}")
    print(f"News APIs: {'✅' if news_ok else '❌'}")
    print(f"Enhanced Market Analysis Pipeline: {'✅' if pipeline_ok else '❌'}")
    
    if all([yfinance_ok, news_ok, pipeline_ok]):
        print("\n🎉 All tests passed! The system is ready to use.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        
        if not env_status['watsonx_ready']:
            print("\n💡 To fix WatsonX issues:")
            print("   1. Add WATSONX_APIKEY to your .env file")
            print("   2. Add WATSONX_PROJECT_ID to your .env file")
            print("   3. Optionally add WATSONX_URL (defaults to us-south)")
        
        if not env_status['news_apis_available']:
            print("\n💡 To enable more news sources:")
            print("   1. Add NEWSAPI_KEY for NewsAPI")
            print("   2. Add ALPHA_VANTAGE_API_KEY for Alpha Vantage")
            print("   3. Add FINNHUB_API_KEY for Finnhub")
            print("   Note: Yahoo Finance works without API keys")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())