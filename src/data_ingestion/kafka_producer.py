"""Kafka producer for simulating FX market data."""

import json
import random
import time
from datetime import datetime
from typing import Dict
from kafka import KafkaProducer
from loguru import logger

from config import settings
from src.models import TickData, OrderBook, OrderBookLevel


class FXDataSimulator:
    """Simulates realistic FX market tick data."""
    
    def __init__(self):
        """Initialize the simulator with base prices."""
        self.base_prices = {
            "EUR/USD": 1.0850,
            "GBP/USD": 1.2650,
            "USD/JPY": 149.50,
            "AUD/USD": 0.6550
        }
        self.current_prices = self.base_prices.copy()
    
    def generate_tick(self, symbol: str) -> TickData:
        """Generate a realistic tick for a currency pair."""
        # Simulate price movement with random walk
        price_change = random.gauss(0, 0.0001)  # Small random changes
        self.current_prices[symbol] += price_change
        
        mid_price = self.current_prices[symbol]
        
        # Typical spread in basis points (0.5-2 bps for major pairs)
        spread_bps = random.uniform(0.5, 2.0)
        spread = (spread_bps / 10000) * mid_price
        
        bid = mid_price - spread / 2
        ask = mid_price + spread / 2
        
        # Random sizes
        bid_size = random.uniform(1.0, 10.0)
        ask_size = random.uniform(1.0, 10.0)
        
        return TickData(
            timestamp=datetime.now(),
            symbol=symbol,
            bid=round(bid, 5),
            ask=round(ask, 5),
            bid_size=round(bid_size, 2),
            ask_size=round(ask_size, 2)
        )
    
    def generate_orderbook(self, symbol: str, levels: int = 5) -> OrderBook:
        """Generate a realistic order book snapshot."""
        tick = self.generate_tick(symbol)
        
        bids = []
        asks = []
        
        # Generate bid levels (decreasing prices)
        for i in range(levels):
            price = tick.bid - (i * 0.0001)
            size = random.uniform(1.0, 20.0) * (1 + i * 0.5)  # More size at worse prices
            bids.append(OrderBookLevel(
                price=round(price, 5),
                size=round(size, 2),
                orders=random.randint(1, 5)
            ))
        
        # Generate ask levels (increasing prices)
        for i in range(levels):
            price = tick.ask + (i * 0.0001)
            size = random.uniform(1.0, 20.0) * (1 + i * 0.5)
            asks.append(OrderBookLevel(
                price=round(price, 5),
                size=round(size, 2),
                orders=random.randint(1, 5)
            ))
        
        return OrderBook(
            timestamp=datetime.now(),
            symbol=symbol,
            bids=bids,
            asks=asks
        )


class KafkaTickProducer:
    """Kafka producer for FX tick data."""
    
    def __init__(self):
        """Initialize Kafka producer."""
        self.producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        self.simulator = FXDataSimulator()
        logger.info(f"Kafka producer connected to {settings.kafka_bootstrap_servers}")
    
    def send_tick(self, tick: TickData):
        """Send a tick to Kafka."""
        message = tick.model_dump()
        self.producer.send(settings.kafka_topic_ticks, value=message)
    
    def send_orderbook(self, orderbook: OrderBook):
        """Send an order book snapshot to Kafka."""
        message = orderbook.model_dump()
        self.producer.send(settings.kafka_topic_orderbook, value=message)
    
    def run_simulation(self, duration_seconds: int = 3600):
        """Run the simulation for a specified duration."""
        logger.info(f"Starting FX data simulation for {duration_seconds} seconds")
        start_time = time.time()
        tick_count = 0
        
        try:
            while time.time() - start_time < duration_seconds:
                # Generate ticks for all currency pairs
                for symbol in settings.currency_pairs_list:
                    tick = self.simulator.generate_tick(symbol)
                    self.send_tick(tick)
                    tick_count += 1
                    
                    # Occasionally send order book updates
                    if random.random() < 0.1:  # 10% chance
                        orderbook = self.simulator.generate_orderbook(symbol)
                        self.send_orderbook(orderbook)
                
                # Sleep to control tick rate
                time.sleep(settings.tick_interval_ms / 1000.0)
                
                if tick_count % 100 == 0:
                    logger.info(f"Sent {tick_count} ticks")
        
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")
        finally:
            self.producer.flush()
            self.producer.close()
            logger.info(f"Simulation completed. Total ticks sent: {tick_count}")


if __name__ == "__main__":
    producer = KafkaTickProducer()
    producer.run_simulation()
