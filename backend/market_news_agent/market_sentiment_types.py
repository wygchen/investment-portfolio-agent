from dataclasses import dataclass, asdict

@dataclass
class MarketSentiment:
    ticker: str
    watsonx_sentiment: float
    news_sentiment_ddg: float
    fear_greed_index: float
    average_sentiment_score: float

    def to_dict(self):
        return asdict(self)

# class NewsData(BaseModel):
#     """Model for news data"""
#     news: List[Dict[str, Any]] = [] # time as key, heading and source as value
#     hotnews_summary: str = ""