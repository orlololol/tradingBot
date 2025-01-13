#python/scrapper/twitter_scrapper.py

"""TODO implementations:
- use cookies to authenticate, if no cookies, login with username and password
    https://twikit.readthedocs.io/en/latest/twikit.html#twikit.client.client.Client.get_cookies
- search for token mentions
    https://twikit.readthedocs.io/en/latest/twikit.html#twikit.client.client.Client.search_tweet
- search for latest tweets for a cherry picked list of user
    https://twikit.readthedocs.io/en/latest/twikit.html#twikit.client.client.Client.search_user
"""

from typing import List, Dict
import logging
from datetime import datetime
from twikit import Client
from ..utils.rate_limiter import RateLimiter
from ..services.kafka_producer import TradeRequestProducer
from .base_scrapper import BaseScraper

logger = logging.getLogger(__name__)

class TwitterScraper(BaseScraper):
    def __init__(self, config: Dict, kafka_config: Dict):
        """Initialize Twitter scraper with configuration"""
        self.config = config
        self.client = Client("en-US")
        self.rate_limiter = RateLimiter(
            max_requests=config.get('max_requests', 100),
            time_window=config.get('time_window', 60)
        )
        self.kafka_producer = TradeRequestProducer(
            broker_url=kafka_config.get('broker_url'),
            topic=kafka_config.get('topic')
        )

    async def initialize(self):
        """Set up Twitter client with credentials"""
        try:
            self.client.set_cookies({
                'auth_token': self.config['auth_token'],
                'ct0': self.config['ct0']
            })
            logger.info("Twitter scraper initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter scraper: {e}")
            raise

    async def get_trends(self, category: str = "news") -> List[Dict]:
        """
        Get current Twitter trends
        https://twikit.readthedocs.io/en/latest/twikit.html#twikit.client.client.Client.get_trends
        """
        async with self.rate_limiter:
            try:
                trends = await self.client.get_trends(category)
                trend_data = [
                    {
                        'trend': trend,
                        'category': category,
                        'timestamp': datetime.now().isoformat()
                    }
                    for trend in trends
                ]
                self.kafka_producer.send_trade_request({'type': 'trends', 'data': trend_data})
                return trend_data
            except Exception as e:
                logger.error(f"Failed to fetch trends: {e}")
                return []

    async def search_mentions(self, query: str, limit: int = 100) -> List[Dict]:
        """Search for token mentions"""
        async with self.rate_limiter:
            try:
                mentions = await self.client.search_mentions(query, limit)
                mention_data = [
                    {
                        'mention': mention,
                        'query': query,
                        'timestamp': datetime.now().isoformat()
                    }
                    for mention in mentions
                ]
                self.kafka_producer.send_trade_request({'type': 'mentions', 'data': mention_data})
                return mention_data
            except Exception as e:
                logger.error(f"Failed to search mentions: {e}")
                return []