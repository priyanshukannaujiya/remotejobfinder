import requests
from typing import List, Dict
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class NewsFetcher:
    @staticmethod
    def get_latest_news(limit: int = 3) -> List[Dict]:
        """
        Fetches the latest trending articles for Data Engineering from dev.to API.
        """
        url = f"https://dev.to/api/articles?tag=dataengineering&top=1&per_page={limit}"
        news = []
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data:
                news.append({
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "url": item.get("url", ""),
                    "cover_image": item.get("cover_image", ""),
                    "published_at": item.get("published_at", "")
                })
            logger.info(f"Successfully fetched {len(news)} news articles.")
        except Exception as e:
            logger.error(f"Failed to fetch news from dev.to API: {e}")
            
        return news
