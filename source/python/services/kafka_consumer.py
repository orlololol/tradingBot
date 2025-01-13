from kafka import KafkaConsumer
import json
import logging

logger = logging.getLogger(__name__)

class KafkaMessageConsumer:
    def __init__(self, broker_url: str, topic: str, group_id: str):
        """Initialize Kafka consumer"""
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=broker_url,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )

    def consume_messages(self, handler):
        """Consume messages and process with the provided handler"""
        try:
            for message in self.consumer:
                logger.info(f"Received message: {message.value}")
                handler(message.value)
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
