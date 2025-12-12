"""Order flow imbalance calculator."""

from typing import List, Optional
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

from src.models import Trade, OrderBook


class FlowImbalanceCalculator:
    """Calculate order flow imbalance metrics."""
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize flow imbalance calculator.
        
        Args:
            window_seconds: Time window for flow calculations
        """
        self.window_seconds = window_seconds
        self.trade_history: List[Trade] = []
        self.orderbook_history: List[OrderBook] = []
    
    def add_trade(self, trade: Trade):
        """Add a new trade to the history."""
        self.trade_history.append(trade)
        self._cleanup_old_trades()
    
    def add_orderbook(self, orderbook: OrderBook):
        """Add a new order book snapshot."""
        self.orderbook_history.append(orderbook)
        self._cleanup_old_orderbooks()
    
    def _cleanup_old_trades(self):
        """Remove trades outside the time window."""
        if not self.trade_history:
            return
        
        cutoff_time = self.trade_history[-1].timestamp - timedelta(seconds=self.window_seconds)
        self.trade_history = [t for t in self.trade_history if t.timestamp >= cutoff_time]
    
    def _cleanup_old_orderbooks(self):
        """Remove old order book snapshots."""
        if len(self.orderbook_history) > 100:
            self.orderbook_history = self.orderbook_history[-100:]
    
    def get_trade_flow_imbalance(self) -> Optional[float]:
        """
        Calculate trade flow imbalance.
        
        Flow Imbalance = (buy_volume - sell_volume) / (buy_volume + sell_volume)
        
        Returns:
            Flow imbalance between -1 and 1
        """
        if not self.trade_history:
            return None
        
        buy_volume = sum(t.size for t in self.trade_history if t.side == 'buy')
        sell_volume = sum(t.size for t in self.trade_history if t.side == 'sell')
        
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return 0.0
        
        return (buy_volume - sell_volume) / total_volume
    
    def get_order_book_imbalance(self) -> Optional[float]:
        """
        Calculate current order book imbalance.
        
        Returns:
            Order book imbalance between -1 and 1
        """
        if not self.orderbook_history:
            return None
        
        ob = self.orderbook_history[-1]
        return ob.imbalance
    
    def get_volume_weighted_imbalance(self, num_levels: int = 5) -> Optional[float]:
        """
        Calculate volume-weighted order book imbalance.
        
        Args:
            num_levels: Number of order book levels to consider
        
        Returns:
            Volume-weighted imbalance
        """
        if not self.orderbook_history:
            return None
        
        ob = self.orderbook_history[-1]
        
        bid_levels = ob.bids[:num_levels]
        ask_levels = ob.asks[:num_levels]
        
        if not bid_levels or not ask_levels:
            return None
        
        bid_volume = sum(level.size for level in bid_levels)
        ask_volume = sum(level.size for level in ask_levels)
        
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return 0.0
        
        return (bid_volume - ask_volume) / total_volume
    
    def get_trade_intensity(self) -> Optional[float]:
        """
        Calculate trade intensity (trades per second).
        
        Returns:
            Number of trades per second
        """
        if not self.trade_history:
            return None
        
        return len(self.trade_history) / self.window_seconds
    
    def get_volume_intensity(self) -> Optional[float]:
        """
        Calculate volume intensity (volume per second).
        
        Returns:
            Total volume per second
        """
        if not self.trade_history:
            return None
        
        total_volume = sum(t.size for t in self.trade_history)
        return total_volume / self.window_seconds
    
    def get_buy_sell_ratio(self) -> Optional[float]:
        """
        Calculate buy/sell volume ratio.
        
        Returns:
            Ratio of buy volume to sell volume
        """
        if not self.trade_history:
            return None
        
        buy_volume = sum(t.size for t in self.trade_history if t.side == 'buy')
        sell_volume = sum(t.size for t in self.trade_history if t.side == 'sell')
        
        if sell_volume == 0:
            return None
        
        return buy_volume / sell_volume
    
    def get_vpin(self, num_buckets: int = 50) -> Optional[float]:
        """
        Calculate Volume-Synchronized Probability of Informed Trading (VPIN).
        
        VPIN measures the probability of informed trading based on order flow imbalance.
        
        Args:
            num_buckets: Number of volume buckets to use
        
        Returns:
            VPIN estimate
        """
        if len(self.trade_history) < num_buckets:
            return None
        
        # Calculate total volume
        total_volume = sum(t.size for t in self.trade_history)
        
        if total_volume == 0:
            return None
        
        # Volume per bucket
        volume_per_bucket = total_volume / num_buckets
        
        # Create volume buckets and calculate imbalances
        imbalances = []
        current_bucket_volume = 0
        current_buy_volume = 0
        current_sell_volume = 0
        
        for trade in self.trade_history:
            if trade.side == 'buy':
                current_buy_volume += trade.size
            else:
                current_sell_volume += trade.size
            
            current_bucket_volume += trade.size
            
            if current_bucket_volume >= volume_per_bucket:
                # Bucket is full, calculate imbalance
                imbalance = abs(current_buy_volume - current_sell_volume)
                imbalances.append(imbalance)
                
                # Reset bucket
                current_bucket_volume = 0
                current_buy_volume = 0
                current_sell_volume = 0
        
        if not imbalances:
            return None
        
        # VPIN is the average absolute imbalance divided by volume per bucket
        vpin = np.mean(imbalances) / volume_per_bucket
        
        return vpin
    
    def detect_aggressive_buying(self, threshold: float = 0.3) -> bool:
        """
        Detect aggressive buying pressure.
        
        Args:
            threshold: Imbalance threshold for detection
        
        Returns:
            True if aggressive buying detected
        """
        imbalance = self.get_trade_flow_imbalance()
        if imbalance is None:
            return False
        
        return imbalance > threshold
    
    def detect_aggressive_selling(self, threshold: float = -0.3) -> bool:
        """
        Detect aggressive selling pressure.
        
        Args:
            threshold: Imbalance threshold for detection
        
        Returns:
            True if aggressive selling detected
        """
        imbalance = self.get_trade_flow_imbalance()
        if imbalance is None:
            return False
        
        return imbalance < threshold
    
    def get_flow_metrics(self) -> dict:
        """
        Get comprehensive flow metrics.
        
        Returns:
            Dictionary of flow metrics
        """
        return {
            'trade_flow_imbalance': self.get_trade_flow_imbalance(),
            'orderbook_imbalance': self.get_order_book_imbalance(),
            'volume_weighted_imbalance': self.get_volume_weighted_imbalance(),
            'trade_intensity': self.get_trade_intensity(),
            'volume_intensity': self.get_volume_intensity(),
            'buy_sell_ratio': self.get_buy_sell_ratio(),
            'vpin': self.get_vpin(),
            'is_aggressive_buying': self.detect_aggressive_buying(),
            'is_aggressive_selling': self.detect_aggressive_selling(),
            'num_trades': len(self.trade_history)
        }
