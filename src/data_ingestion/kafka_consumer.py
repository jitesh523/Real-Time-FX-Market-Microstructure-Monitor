"""Kafka consumer for processing FX market data."""

import json
from datetime import datetime
from kafka import KafkaConsumer
from loguru import logger

from config import settings
from src.models import TickData, OrderBook, OrderBookLevel
from src.data_ingestion.clickhouse_writer import get_clickhouse_client


class KafkaTickConsumer:
    """Kafka consumer for FX tick data."""
    
    def __init__(self):
        """Initialize Kafka consumer."""
        self.consumer = KafkaConsumer(
            settings.kafka_topic_ticks,
            settings.kafka_topic_orderbook,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        self.db_client = get_clickhouse_client()
        self.tick_buffer = []
        self.buffer_size = 100  # Batch insert every 100 ticks
        logger.info(f"Kafka consumer started, subscribed to topics: {settings.kafka_topic_ticks}, {settings.kafka_topic_orderbook}")
    
    def process_tick(self, message: dict):
        """Process a tick message."""
        try:
            # Parse timestamp
            if isinstance(message['timestamp'], str):
                message['timestamp'] = datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
            
            tick = TickData(**message)
            self.tick_buffer.append(tick)
            
            # Batch insert when buffer is full
            if len(self.tick_buffer) >= self.buffer_size:
                self.db_client.insert_ticks_batch(self.tick_buffer)
                self.tick_buffer.clear()
        
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
    
    def process_orderbook(self, message: dict):
        """Process an order book message."""
        try:
            # Parse timestamp
            if isinstance(message['timestamp'], str):
                message['timestamp'] = datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
            
            # Parse order book levels
            message['bids'] = [OrderBookLevel(**level) for level in message['bids']]
            message['asks'] = [OrderBookLevel(**level) for level in message['asks']]
            
            orderbook = OrderBook(**message)
            self.db_client.insert_orderbook(orderbook)
        
        except Exception as e:
            logger.error(f"Error processing order book: {e}")
    
    def run(self):
        """Run the consumer loop."""
        logger.info("Starting consumer loop...")
        
        try:
            for message in self.consumer:
                topic = message.topic
                value = message.value
                
                if topic == settings.kafka_topic_ticks:
                    self.process_tick(value)
                elif topic == settings.kafka_topic_orderbook:
                    self.process_orderbook(value)
        
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        finally:
            # Flush remaining ticks
            if self.tick_buffer:
                self.db_client.insert_ticks_batch(self.tick_buffer)
                self.tick_buffer.clear()
            
            self.consumer.close()
            logger.info("Consumer closed")


if __name__ == "__main__":
    consumer = KafkaTickConsumer()
    consumer.run()
