"""Data models for FX market data."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class TickData(BaseModel):
    """Represents a single tick (price update) in the FX market."""
    
    timestamp: datetime = Field(description="Time of the tick")
    symbol: str = Field(description="Currency pair (e.g., EUR/USD)")
    bid: float = Field(description="Bid price")
    ask: float = Field(description="Ask price")
    bid_size: float = Field(default=0.0, description="Bid volume")
    ask_size: float = Field(default=0.0, description="Ask volume")
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price."""
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        return self.ask - self.bid
    
    @property
    def spread_bps(self) -> float:
        """Calculate spread in basis points."""
        return (self.spread / self.mid_price) * 10000


class OrderBookLevel(BaseModel):
    """Represents a single level in the order book."""
    
    price: float = Field(description="Price level")
    size: float = Field(description="Volume at this price level")
    orders: int = Field(default=1, description="Number of orders at this level")


class OrderBook(BaseModel):
    """Represents the full order book for a currency pair."""
    
    timestamp: datetime = Field(description="Time of the order book snapshot")
    symbol: str = Field(description="Currency pair")
    bids: list[OrderBookLevel] = Field(description="Bid side of the order book")
    asks: list[OrderBookLevel] = Field(description="Ask side of the order book")
    
    @property
    def bid_depth(self) -> float:
        """Total volume on bid side."""
        return sum(level.size for level in self.bids)
    
    @property
    def ask_depth(self) -> float:
        """Total volume on ask side."""
        return sum(level.size for level in self.asks)
    
    @property
    def total_depth(self) -> float:
        """Total volume on both sides."""
        return self.bid_depth + self.ask_depth
    
    @property
    def imbalance(self) -> float:
        """Order flow imbalance: (bid_depth - ask_depth) / total_depth."""
        total = self.total_depth
        if total == 0:
            return 0.0
        return (self.bid_depth - self.ask_depth) / total


class Trade(BaseModel):
    """Represents a completed trade."""
    
    timestamp: datetime = Field(description="Time of the trade")
    symbol: str = Field(description="Currency pair")
    price: float = Field(description="Trade price")
    size: float = Field(description="Trade volume")
    side: str = Field(description="Trade side: 'buy' or 'sell'")
    trade_id: Optional[str] = Field(default=None, description="Unique trade identifier")


class MarketMetrics(BaseModel):
    """Aggregated market microstructure metrics."""
    
    timestamp: datetime = Field(description="Time of the metrics")
    symbol: str = Field(description="Currency pair")
    
    # Spread metrics
    bid_ask_spread: float = Field(description="Current bid-ask spread")
    spread_bps: float = Field(description="Spread in basis points")
    
    # Depth metrics
    bid_depth: float = Field(description="Total bid volume")
    ask_depth: float = Field(description="Total ask volume")
    total_depth: float = Field(description="Total market depth")
    
    # Flow metrics
    order_flow_imbalance: float = Field(description="Order flow imbalance")
    
    # Volatility metrics
    volatility: Optional[float] = Field(default=None, description="Realized volatility")
    
    # Anomaly flags
    is_anomaly: bool = Field(default=False, description="Anomaly detected")
    anomaly_type: Optional[str] = Field(default=None, description="Type of anomaly")
    anomaly_score: Optional[float] = Field(default=None, description="Anomaly score")
