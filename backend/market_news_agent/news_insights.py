"""
AI News and Insights Module
Provides stock price data and news analysis with market summaries using Finnhub and WatsonX AI
"""

import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv
from langchain_ibm import ChatWatsonx

# Load environment variables
load_dotenv()

class NewsInsightsAnalyzer:
    """Handles stock price data and news analysis"""
    
    def __init__(self):
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.watsonx_api_key = os.getenv('WATSONX_APIKEY')
        self.watsonx_project_id = os.getenv('PROJ_ID')
        
        # Initialize WatsonX LLM if credentials are available
        self.llm = None
        if self.watsonx_api_key and self.watsonx_project_id:
            try:
                self.llm = ChatWatsonx(
                    model_id="ibm/granite-3-3-8b-instruct",
                    url="https://us-south.ml.cloud.ibm.com",
                    apikey=self.watsonx_api_key,
                    project_id=self.watsonx_project_id,
                    params={
                        "decoding_method": "greedy",
                        "max_new_tokens": 100,
                        "temperature": 0.3
                    }
                )
            except Exception as e:
                print(f"Failed to initialize WatsonX: {e}")
                self.llm = None
    
    def get_stock_price_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock price and change data from yfinance
        
        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            
        Returns:
            Dict with price, change, and changePercent
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            # Get current price
            current_price = (
                info.get('currentPrice') or 
                info.get('regularMarketPrice') or 
                (hist['Close'].iloc[-1] if not hist.empty else 0)
            )
            
            # Get previous close
            previous_close = (
                info.get('previousClose') or 
                info.get('regularMarketPreviousClose') or
                (hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
            )
            
            # Calculate change
            change = float(current_price) - float(previous_close)
            change_percent = (change / float(previous_close) * 100) if previous_close > 0 else 0
            
            return {
                "price": round(float(current_price), 2),
                "change": round(change, 2),
                "changePercent": round(change_percent, 2)
            }
            
        except Exception as e:
            print(f"Error fetching price data for {symbol}: {e}")
            return {
                "price": 0.0,
                "change": 0.0,
                "changePercent": 0.0
            }
    
    def get_finnhub_news(self, symbol: str, max_articles: int = 5) -> List[Dict]:
        """Get news from Finnhub API"""
        if not self.finnhub_key:
            print(f"Finnhub API key not found for {symbol}")
            return []
            
        try:
            # Get news from last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            url = f"https://finnhub.io/api/v1/company-news"
            params = {
                'symbol': symbol,
                'from': from_date,
                'to': to_date,
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            formatted_news = []
            for article in data[:max_articles]:
                try:
                    formatted_news.append({
                        'title': article.get('headline', ''),
                        'summary': article.get('summary', ''),
                        'publisher': article.get('source', 'Finnhub'),
                        'published_date': datetime.fromtimestamp(article.get('datetime', 0)),
                        'url': article.get('url', ''),
                        'source': 'finnhub'
                    })
                except Exception as article_error:
                    print(f"Error parsing article for {symbol}: {article_error}")
                    continue
            
            print(f"Fetched {len(formatted_news)} news articles for {symbol}")
            return formatted_news
            
        except Exception as e:
            print(f"Error fetching Finnhub news for {symbol}: {e}")
            return []
    
    def analyze_news_with_watsonx(self, symbol: str, news_articles: List[Dict]) -> str:
        """
        Use WatsonX AI to analyze news articles and provide market summary
        
        Args:
            symbol: Stock ticker symbol
            news_articles: List of news articles from Finnhub
            
        Returns:
            20-word market summary from WatsonX AI. Do not include the phrase "20-word:"
        """
        if not self.llm or not news_articles:
            return f"No AI analysis available for {symbol}."
        
        try:
            # Prepare news content for analysis
            news_content = ""
            for article in news_articles[:3]:  # Use top 3 articles
                news_content += f"Title: {article.get('title', '')}\n"
                if article.get('summary'):
                    news_content += f"Summary: {article.get('summary', '')}\n"
                news_content += "\n"
            
            # Create prompt for WatsonX
            prompt = f"""Analyze the following news about {symbol} and provide a 20-word market summary with investment recommendation:

{news_content}

Provide exactly 20 words summarizing the market outlook and whether to buy, hold, or sell {symbol}."""

            # Call WatsonX AI
            response = self.llm.invoke(prompt)
            
            # Extract and clean the response
            summary = response.content.strip()
            
            # Ensure it's roughly 20 words
            words = summary.split()
            if len(words) > 25:
                summary = ' '.join(words[:20]) + "..."
            elif len(words) < 15:
                summary += f" Monitor {symbol} closely for investment opportunities."
            
            return summary
            
        except Exception as e:
            print(f"Error in WatsonX analysis for {symbol}: {e}")
            return f"AI analysis unavailable for {symbol}. Monitor market conditions carefully."

    def analyze_market_summary(self, symbol: str, news_articles: List[Dict]) -> str:
        """
        Analyze news articles and provide market summary with recommendation
        
        Args:
            symbol: Stock ticker symbol
            news_articles: List of news articles from Finnhub
            
        Returns:
            Market summary string (20 words from WatsonX AI)
        """
        if not news_articles:
            return f"No recent news available for {symbol}. Monitor for updates before making investment decisions."
        
        # Try WatsonX AI analysis first
        if self.llm:
            return self.analyze_news_with_watsonx(symbol, news_articles)
        


    def get_complete_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get complete analysis for a stock symbol
        
        Returns:
            Dict with price data, news articles, market summary, and news URLs
        """
        try:
            # Get price data
            price_data = self.get_stock_price_data(symbol)
            
            # Get news articles
            news_articles = self.get_finnhub_news(symbol)
            
            # Extract URLs from news articles
            news_urls = [article.get('url', '') for article in news_articles if article.get('url')]
            
            # Generate market summary
            market_summary = self.analyze_market_summary(symbol, news_articles)
            
            return {
                "symbol": symbol,
                "priceData": price_data,
                "newsArticles": news_articles,
                "newsUrls": news_urls,
                "marketSummary": market_summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in complete analysis for {symbol}: {e}")
            return {
                "symbol": symbol,
                "priceData": {"price": 0.0, "change": 0.0, "changePercent": 0.0},
                "newsArticles": [],
                "newsUrls": [],
                "marketSummary": f"Analysis for {symbol} is currently unavailable.",
                "timestamp": datetime.now().isoformat()
            }

# Main function for API integration
def get_news_insights_analysis(symbol: str) -> Dict[str, Any]:
    """Main function to get complete news insights analysis"""
    analyzer = NewsInsightsAnalyzer()
    return analyzer.get_complete_analysis(symbol)

if __name__ == "__main__":
    # Test the functions
    analyzer = NewsInsightsAnalyzer()
    
    # Test with AAPL
    print("Testing with AAPL...")
    result = analyzer.get_complete_analysis("AAPL")
    print(f"Price: ${result['priceData']['price']:.2f}")
    print(f"Change: {result['priceData']['changePercent']:+.2f}%")
    print(f"News articles: {len(result['newsArticles'])}")
    print(f"News URLs: {result['newsUrls']}")

    print(f"Market summary: {result['marketSummary']}")