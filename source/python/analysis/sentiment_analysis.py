# kafka/analysis/sentiment_analysis_kafka.py

from typing import List, Dict, Union
import logging
from kafka import KafkaProducer, KafkaConsumer
from transformers import (
    TextClassificationPipeline,
    AutoModelForSequenceClassification,
    AutoTokenizer
)
from functools import lru_cache
import json

logger = logging.getLogger(__name__)

class CryptoSentimentAnalyzer:
    def __init__(self, 
                 model_name: str = "ElKulako/cryptobert", 
                 priority_accounts: List[str] = None,
                 kafka_broker: str = "localhost:9092",
                 topic_name: str = "crypto-sentiment"):
        """
        Initialize the crypto-specific sentiment analyzer with Kafka
        
        Args:
            model_name: Name of the CryptoBERT model to use
            priority_accounts: List of X usernames whose signals take priority
            kafka_broker: Address of the Kafka broker
            topic_name: Kafka topic for publishing sentiment analysis
        """
        try:
            self.model_name = model_name
            self.sentiment_pipeline = self._load_model()
            self.priority_accounts = set(priority_accounts or [])
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=kafka_broker,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.kafka_topic = topic_name
            logger.info(f"Loaded CryptoBERT model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load CryptoBERT model: {e}")
            raise

    @lru_cache(maxsize=1)
    def _load_model(self):
        """Load and cache the CryptoBERT model"""
        tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(self.model_name, num_labels=3)
        return TextClassificationPipeline(
            model=model,
            tokenizer=tokenizer,
            max_length=64,
            truncation=True,
            padding='max_length'
        )

    async def analyze_sentiment(self, posts: List[Dict[str, str]]) -> Dict[str, Union[str, float, List]]:
        """
        Analyze sentiment from posts, prioritizing certain accounts, and publish results to Kafka
        
        Args:
            posts: List of dicts containing:
                - text: The post text
                - username: X username
                - wallet_address: Optional wallet address for tracking
        
        Returns:
            Dict containing:
                - overall_sentiment: dominant sentiment
                - confidence: confidence score
                - priority_signals: list of signals from priority accounts
                - general_signals: list of other analyzed posts
        """
        try:
            priority_signals = []
            general_signals = []
            
            for post in posts:
                # Analyze sentiment
                result = self.sentiment_pipeline(post['text'])[0]
                sentiment_map = {
                    'LABEL_0': 'neutral',
                    'LABEL_1': 'bullish',
                    'LABEL_2': 'bearish'
                }
                
                analysis = {
                    'text': post['text'],
                    'username': post['username'],
                    'wallet_address': post.get('wallet_address'),
                    'sentiment': sentiment_map.get(result['label'], result['label']),
                    'confidence': result['score']
                }
                
                # Sort into priority or general signals
                if post['username'] in self.priority_accounts:
                    priority_signals.append(analysis)
                else:
                    general_signals.append(analysis)
            
            # Calculate overall sentiment from all signals
            all_signals = priority_signals + general_signals
            if not all_signals:
                return {}
            
            sentiment_counts = {
                'bullish': sum(1 for s in all_signals if s['sentiment'] == 'bullish'),
                'bearish': sum(1 for s in all_signals if s['sentiment'] == 'bearish'),
                'neutral': sum(1 for s in all_signals if s['sentiment'] == 'neutral')
            }
            
            overall_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
            avg_confidence = sum(s['confidence'] for s in all_signals) / len(all_signals)
            
            result = {
                'overall_sentiment': overall_sentiment,
                'confidence': avg_confidence,
                'priority_signals': priority_signals,
                'general_signals': general_signals,
                'sentiment_counts': sentiment_counts
            }
            
            # Publish the result to Kafka
            self.kafka_producer.send(self.kafka_topic, result)
            return result
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {}