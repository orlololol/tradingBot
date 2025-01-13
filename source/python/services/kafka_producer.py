from kafka import KafkaProducer
import json
from utils.kafka_config import KAFKA_BROKER_URL, TRADE_REQUEST_TOPIC

class TradeRequestProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER_URL,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def send_trade_request(self, trade_request):
        self.producer.send(TRADE_REQUEST_TOPIC, trade_request)
        self.producer.flush()

# Usage
if __name__ == "__main__":
    producer = TradeRequestProducer()
    trade_request = {"coin": "SOL", "action": "BUY", "amount": 10}
    producer.send_trade_request(trade_request)
