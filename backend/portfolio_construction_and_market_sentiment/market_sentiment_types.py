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
