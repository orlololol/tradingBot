# kafka/analysis/wallet_tracker_kafka.py

from typing import List, Dict, Optional
import logging
from kafka import KafkaProducer, KafkaConsumer
import json

logger = logging.getLogger(__name__)

class WalletTracker:
    def __init__(self, 
                 priority_wallets: List[str] = None,
                 kafka_broker: str = "localhost:9092",
                 topic_name: str = "wallet-transactions"):
        """
        Initialize wallet tracker with Kafka
        
        Args:
            priority_wallets: List of wallet addresses to track closely
            kafka_broker: Address of the Kafka broker
            topic_name: Kafka topic for publishing transaction analysis
        """
        self.priority_wallets = set(priority_wallets or [])
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.kafka_topic = topic_name

    async def analyze_transactions(self, 
                                   transactions: List[Dict], 
                                   token_address: str) -> Dict[str, List[Dict]]:
        """
        Analyze transactions for a specific token and publish results to Kafka
        
        Args:
            transactions: List of transaction data
            token_address: Address of the token to analyze
            
        Returns:
            Dict containing:
                - priority_trades: List of trades from priority wallets
                - whale_trades: List of large trades from other wallets
                - recent_trades: List of other relevant trades
        """
        try:
            priority_trades = []
            whale_trades = []
            recent_trades = []
            
            for tx in transactions:
                trade = {
                    'wallet': tx['from_address'],
                    'type': 'buy' if tx.get('is_buy') else 'sell',
                    'amount': tx.get('amount'),
                    'value_usd': tx.get('value_usd')
                }
                
                # Categorize the trade
                if tx['from_address'] in self.priority_wallets:
                    priority_trades.append(trade)
                elif tx.get('value_usd', 0) > 10000:  # Consider trades over $10k as whale trades
                    whale_trades.append(trade)
                else:
                    recent_trades.append(trade)
            
            result = {
                'priority_trades': priority_trades,
                'whale_trades': whale_trades,
                'recent_trades': recent_trades[:10]  # Limit recent trades to last 10
            }
            
            # Publish the result to Kafka
            self.kafka_producer.send(self.kafka_topic, result)
            return result
            
        except Exception as e:
            logger.error(f"Transaction analysis failed: {e}")
            return {
                'priority_trades': [],
                'whale_trades': [],
                'recent_trades': []
            }