import pandas as pd
import yfinance as yf
from ddgs import DDGS
from langchain_ibm import WatsonxLLM
from textblob import TextBlob
import os
from dataclasses import asdict
from .market_sentiment_types import MarketSentiment

"""
# Debug flag: set environment variable MARKET_SENTIMENT_DEBUG=1 to print raw LLM responses
DEBUG_LLM = os.getenv("MARKET_SENTIMENT_DEBUG", "0") == "1"
"""

# Get news from yahoofinance and analyze with watsonx LLM
def get_yahoo_news_description(ticker_symbol, max_articles=45):
    """
    Extract news from Yahoo Finance and return as a descriptive news string
    
    Args:
        ticker_symbol: Stock ticker symbol (e.g., "TSLA")
        max_articles: Maximum number of articles to include (default: 3)
    
    Returns:
        String describing the latest news for the ticker
    """
    try:
        # Get ticker data
        ticker = yf.Ticker(ticker_symbol)
        
        # Fetch news articles
        news_articles = ticker.news
        
        if not news_articles:
            return f"No recent news found for {ticker_symbol}"
        
        # Build descriptive news string
        news_description = f"Recent news for {ticker_symbol}: "
        articles_list = []
        
        for i, article in enumerate(news_articles[:max_articles]):
            headline = article.get('title', '').strip()
            summary = article.get('summary', '').strip() or article.get('content', '').strip()
            publisher = article.get('publisher', 'Unknown Source')
            
            if headline:
                article_desc = f"'{headline}'"
                if summary:
                    article_desc += f" - {summary[:100]}..."  # Truncate long summaries
                articles_list.append(article_desc)
        
        if not articles_list:
            return f"No readable news headlines found for {ticker_symbol}"
        
        # Combine all articles into one descriptive string
        news_description += ". ".join(articles_list)
        
        return news_description
        
    except Exception as e:
        return f"Error fetching news for {ticker_symbol}: {str(e)}"

# Setup Watsonx LLM
llm = WatsonxLLM(
    model_id="ibm/granite-3-3-8b-instruct",
    project_id="9fb38a1d-5fae-47c2-a1a1-780e63b953f7",
    apikey="0VrXkis1OeScydFGNiufjJItYgNtxKW7RXbY7ODBzp7j",
    url="https://us-south.ml.cloud.ibm.com",
    params={
        "decoding_method": "greedy",
        "max_new_tokens": 150,
        "temperature": 0.1,
        "repetition_penalty": 1.1
    }
)


def watsonx_sentiment_analysis(text: str, return_label: bool = False):
    """
    Use Watsonx LLM to classify sentiment of a text.

    By default returns a numeric score: 1.0 (Positive), -1.0 (Negative), 0.0 (Neutral)
    If return_label=True it returns a single-word string: 'Positive', 'Negative', or 'Neutral'.
    """
    prompt = f"""
    Analyze the sentiment of the following financial news text.
    Respond with exactly ONE word only: Positive, Negative, or Neutral. Do not include any explanation or extra text.
    Text: {text}
    """

    # Try several call styles to accommodate different LLM wrappers
    response = None
    try:
        # LangChain-style: generate(prompts=[...])
        response = llm.generate(prompts=[prompt])
    except TypeError:
        try:
            # Some wrappers accept a single prompt keyword
            response = llm.generate(prompt=prompt)
        except Exception:
            try:
                # Some LLMs are callable
                response = llm(prompt)
            except Exception:
                response = None

    label = ""

    """
    # Parse different possible response shapes
    if DEBUG_LLM:
        print("[DEBUG] Raw LLM response:", response)
    """
    
    if isinstance(response, dict) and 'results' in response:
        # Original IBM style in this repo
        label = response['results'][0].get('generated_text', '').strip().lower()
    elif hasattr(response, 'generations'):
        # LangChain LLMResult: .generations -> List[List[Generation]] if IBM style failed
        try:
            gens = response.generations
            if gens and gens[0]:
                # Generation object may have .text or .generation_text
                gen0 = gens[0][0]
                label = getattr(gen0, 'text', None) or getattr(gen0, 'generation_text', '')
                label = label.strip().lower()
        except Exception:
            label = ''
    elif isinstance(response, str):
        label = response.strip().lower()
    elif response is None:
        label = ''
    else:
        # Fallback: try to stringify and find keywords
        label = str(response).strip().lower()

    # If label is empty, use a lightweight keyword heuristic as a fallback
    if not label:
        # Very small heuristic-based fallback if LLM unavailable or failed
        low_text = text.lower()
        positive_keywords = ['gain', 'up', 'rise', 'positive', 'beat', 'outperform', 'bull']
        negative_keywords = ['loss', 'down', 'fall', 'drop', 'negative', 'miss', 'bear']
        pos = any(k in low_text for k in positive_keywords)
        neg = any(k in low_text for k in negative_keywords)
        if pos and not neg:
            return 1.0
        elif neg and not pos:
            return -1.0
        else:
            return 0.0

    # Normalize label to single word
    label_word = None
    if "positive" in label:
        label_word = "Positive"
    elif "negative" in label:
        label_word = "Negative"
    elif "neutral" in label:
        label_word = "Neutral"

    # If still not recognized, use heuristic from original fallback
    if label_word is None:
        low_text = text.lower()
        positive_keywords = ['gain', 'up', 'rise', 'positive', 'beat', 'outperform', 'bull']
        negative_keywords = ['loss', 'down', 'fall', 'drop', 'negative', 'miss', 'bear']
        pos = any(k in low_text for k in positive_keywords)
        neg = any(k in low_text for k in negative_keywords)
        if pos and not neg:
            label_word = "Positive"
        elif neg and not pos:
            label_word = "Negative"
        else:
            label_word = "Neutral"

    if return_label:
        return label_word

    # Map to numeric for backward compatibility
    if label_word == "Positive":
        return 1.0
    elif label_word == "Negative":
        return -1.0
    else:
        return 0.0

# 2. News Sentiment (via DuckDuckGo Search + watsonx)
def get_news_sentiment(ticker, num_results=45):
    """Fetch recent news via DuckDuckGo and compute sentiment using TextBlob polarity.

    Returns the average polarity in [-1.0, 1.0].
    """
    ddgs = DDGS()
    query = f"{ticker} stock news"
    results = ddgs.text(query, max_results=num_results)

    scores = []
    for r in results:
        text = f"{r.get('title','')} {r.get('body','')}"
        try:
            tb = TextBlob(text)
            # TextBlob.polarity is in [-1.0, 1.0]
            score = float(tb.sentiment.polarity)
        except Exception:
            # fallback to neutral if TextBlob fails
            score = 0.0
        scores.append(score)

    return sum(scores) / len(scores) if scores else 0.0


# 3. Fear & Greed Index Proxy 
def calculate_fear_greed_index(ticker):
    data = yf.download(ticker, period="6mo", interval="1d")
    data["Change"] = data["Close"].pct_change()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))

    latest_rsi = data["RSI"].iloc[-1]
    latest_vix = get_cboe_vix()

    rsi_score = (latest_rsi - 50) / 50
    vix_score = (20 - latest_vix) / 20

    fear_greed = (rsi_score + vix_score) / 2
    return fear_greed


def get_cboe_vix(default_vix: float = 20.0) -> float:
    """Fetch latest CBOE VIX (^VIX) close value using yfinance.

    Returns a default value if the fetch fails or returns NaN.
    """
    try:
        vix = yf.download('^VIX', period='7d', interval='1d')
        if vix is None or vix.empty:
            return default_vix
        latest = vix['Close'].dropna().iloc[-1]
        if pd.isna(latest):
            return default_vix
        return float(latest)
    except Exception:
        return default_vix


# 4. Master Function
def analyze_market_sentiment(tickers):
    results = []
    for t in tickers:
        # use the defined function get_yahoo_news_description to fetch Yahoo news
        watsonx_sentiment= watsonx_sentiment_analysis(get_yahoo_news_description(t))
        news_sentiment = get_news_sentiment(t)
        fear_greed = calculate_fear_greed_index(t)
        avg_score = (watsonx_sentiment + news_sentiment + fear_greed) / 3

        results.append({
            "Ticker": t,
            "Watsonx Sentiment": watsonx_sentiment,
            "News Sentiment (DDG)": news_sentiment,
            "Fear/Greed Index": fear_greed,
            "Average Sentiment Score": avg_score
        })

    # Ensure numeric types are native Python floats for JSON/printing compatibility
    for r in results:
        for k, v in list(r.items()):
            if isinstance(v, (pd.NA.__class__,)):
                r[k] = None
            try:
                # numpy and pandas numeric types to native float
                if hasattr(v, 'item'):
                    r[k] = float(v.item())
                elif isinstance(v, (int, float)) and not isinstance(v, bool):
                    r[k] = float(v)
            except Exception:
                # leave original value if conversion fails
                pass

    # Build dataclass instances for stronger typing / downstream use
    dataclass_results = []
    for r in results:
        dataclass_results.append(
            MarketSentiment(
                ticker=r.get("Ticker"),
                watsonx_sentiment=float(r.get("Watsonx Sentiment", 0.0) or 0.0),
                news_sentiment_ddg=float(r.get("News Sentiment (DDG)", 0.0) or 0.0),
                fear_greed_index=float(r.get("Fear/Greed Index", 0.0) or 0.0),
                average_sentiment_score=float(r.get("Average Sentiment Score", 0.0) or 0.0),
            )
        )

    return dataclass_results

'''
# test
if __name__ == '__main__':
    # Example run when executed as a script
    analyze_market_sentiment(["AAPL", "TSLA", "MSFT"])
'''