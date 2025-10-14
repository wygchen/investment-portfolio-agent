from dataclasses import dataclass, asdict
from typing import List, Dict, Any, TypedDict, Optional


class ArticleContent(TypedDict):
    """Shape of the inner article content used in news_list.

    Example:
    {
      "2024-01-15T10:30:00Z": {
          "heading": "...",
          "subheading": "...",
          "source": "...",
          "link": "..."
      }
    }
    """
    heading: str
    content_summary: str
    source: str
    link: str


NewsList = List[Dict[str, ArticleContent]]


@dataclass
class NewsReport:
    """Represents the nested news report returned by the model.

    The model returns a structure with a `news_list` (list of timestamp-keyed
    article entries) and a `hotnews_summary` string.
    """
    news_list: NewsList
    hotnews_summary: str
    news_source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "news_list": self.news_list,
            "hotnews_summary": self.hotnews_summary,
            "news_source": self.news_source,
        }


@dataclass
class NewsData:
    """Model for news data matching expected output format used by the API.

    - news_list: List of dicts where the key is a timestamp string and the value
      is an ArticleContent dict.
    - hotnews_summary: AI-generated summary string.
    """
    news_list: NewsList
    hotnews_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "news_list": self.news_list,
            "hotnews_summary": self.hotnews_summary,
        }



__all__ = [
    "ArticleContent",
    "NewsList",
    "NewsReport",
    "NewsData",
]