#python/scrapper/base_scrapper.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import asyncio
from datetime import datetime

class BaseScraper(ABC):
    """Abstract base class for social media scrapers"""
    
    @abstractmethod
    async def initialize(self):
        """Initialize the scraper with necessary credentials"""
        pass
    
    @abstractmethod
    async def get_trends(self) -> List[Dict]:
        """Get current trending topics"""
        pass
    
    @abstractmethod
    async def search_mentions(self, query: str, limit: int = 100) -> List[Dict]:
        """Search for mentions of a specific term"""
        pass