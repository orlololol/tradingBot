#python/data/database.py

from typing import Dict, List, Optional
import logging
import asyncio
import aiosqlite
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        """Initialize database connection"""
        self.db_path = db_path
        
    async def initialize(self):
        """Create necessary tables"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS tokens (
                        address TEXT PRIMARY KEY,
                        symbol TEXT,
                        name TEXT,
                        created_at TIMESTAMP
                    )
                ''')
                
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS sentiment_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_address TEXT,
                        sentiment TEXT,
                        confidence REAL,
                        created_at TIMESTAMP,
                        FOREIGN KEY (token_address) REFERENCES tokens (address)
                    )
                ''')
                
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_address TEXT,
                        wallet_address TEXT,
                        type TEXT,
                        amount REAL,
                        price REAL,
                        created_at TIMESTAMP,
                        FOREIGN KEY (token_address) REFERENCES tokens (address)
                    )
                ''')
                
                await db.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def add_token(self, token_data: Dict) -> bool:
        """Add new token to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO tokens (address, symbol, name, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    token_data['address'],
                    token_data['symbol'],
                    token_data['name'],
                    datetime.now().isoformat()
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add token: {e}")
            return False

    async def add_sentiment(self, sentiment_data: Dict) -> bool:
        """Add sentiment analysis result"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO sentiment_analysis 
                    (token_address, sentiment, confidence, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    sentiment_data['token_address'],
                    sentiment_data['sentiment'],
                    sentiment_data['confidence'],
                    datetime.now().isoformat()
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add sentiment: {e}")
            return False

    async def add_trade(self, trade_data: Dict) -> bool:
        """Add trade information"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO trades 
                    (token_address, wallet_address, type, amount, price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data['token_address'],
                    trade_data['wallet_address'],
                    trade_data['type'],
                    trade_data['amount'],
                    trade_data['price'],
                    datetime.now().isoformat()
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add trade: {e}")
            return False