"""Order book depth analyzer for market microstructure analysis."""

from typing import List, Optional, Tuple
import numpy as np
from loguru import logger

from src.models import OrderBook, OrderBookLevel


class DepthAnalyzer:
    """Analyze order book depth and liquidity."""
    
    def __init__(self, max_levels: int = 10):
        """
        Initialize depth analyzer.
        
        Args:
            max_levels: Maximum number of order book levels to analyze
        """
        self.max_levels = max_levels
        self.orderbook_history: List[OrderBook] = []
    
    def add_orderbook(self, orderbook: OrderBook):
        """Add a new order book snapshot to the history."""
        self.orderbook_history.append(orderbook)
        
        # Keep only recent snapshots (last 100)
        if len(self.orderbook_history) > 100:
            self.orderbook_history.pop(0)
    
    def get_current_depth(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current order book depth.
        
        Returns:
            Tuple of (bid_depth, ask_depth, total_depth)
        """
        if not self.orderbook_history:
            return None
        
        ob = self.orderbook_history[-1]
        return (ob.bid_depth, ob.ask_depth, ob.total_depth)
    
    def get_depth_at_level(self, level: int = 0) -> Optional[Tuple[float, float]]:
        """
        Get depth at a specific level.
        
        Args:
            level: Order book level (0 = best bid/ask)
        
        Returns:
            Tuple of (bid_size, ask_size) at the level
        """
        if not self.orderbook_history:
            return None
        
        ob = self.orderbook_history[-1]
        
        if level >= len(ob.bids) or level >= len(ob.asks):
            return None
        
        return (ob.bids[level].size, ob.asks[level].size)
    
    def get_cumulative_depth(self, num_levels: int = 5) -> Optional[Tuple[float, float]]:
        """
        Get cumulative depth for top N levels.
        
        Args:
            num_levels: Number of levels to sum
        
        Returns:
            Tuple of (cumulative_bid_depth, cumulative_ask_depth)
        """
        if not self.orderbook_history:
            return None
        
        ob = self.orderbook_history[-1]
        
        bid_depth = sum(level.size for level in ob.bids[:num_levels])
        ask_depth = sum(level.size for level in ob.asks[:num_levels])
        
        return (bid_depth, ask_depth)
    
    def get_depth_imbalance(self, num_levels: int = 5) -> Optional[float]:
        """
        Calculate order book imbalance.
        
        Imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)
        
        Args:
            num_levels: Number of levels to consider
        
        Returns:
            Imbalance ratio between -1 and 1
        """
        depths = self.get_cumulative_depth(num_levels)
        if depths is None:
            return None
        
        bid_depth, ask_depth = depths
        total = bid_depth + ask_depth
        
        if total == 0:
            return 0.0
        
        return (bid_depth - ask_depth) / total
    
    def get_weighted_mid_price(self, num_levels: int = 5) -> Optional[float]:
        """
        Calculate volume-weighted mid price.
        
        Args:
            num_levels: Number of levels to consider
        
        Returns:
            Volume-weighted mid price
        """
        if not self.orderbook_history:
            return None
        
        ob = self.orderbook_history[-1]
        
        bid_levels = ob.bids[:num_levels]
        ask_levels = ob.asks[:num_levels]
        
        if not bid_levels or not ask_levels:
            return None
        
        bid_value = sum(level.price * level.size for level in bid_levels)
        ask_value = sum(level.price * level.size for level in ask_levels)
        
        bid_volume = sum(level.size for level in bid_levels)
        ask_volume = sum(level.size for level in ask_levels)
        
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return None
        
        return (bid_value + ask_value) / total_volume
    
    def get_price_impact(self, volume: float, side: str) -> Optional[float]:
        """
        Estimate price impact for a market order of given volume.
        
        Args:
            volume: Order volume
            side: 'buy' or 'sell'
        
        Returns:
            Estimated price impact (difference from mid price)
        """
        if not self.orderbook_history:
            return None
        
        ob = self.orderbook_history[-1]
        levels = ob.asks if side == 'buy' else ob.bids
        
        if not levels:
            return None
        
        remaining_volume = volume
        total_cost = 0.0
        
        for level in levels:
            if remaining_volume <= 0:
                break
            
            volume_at_level = min(remaining_volume, level.size)
            total_cost += volume_at_level * level.price
            remaining_volume -= volume_at_level
        
        if remaining_volume > 0:
            # Not enough liquidity
            return None
        
        avg_price = total_cost / volume
        
        # Calculate mid price
        mid_price = (ob.bids[0].price + ob.asks[0].price) / 2
        
        return abs(avg_price - mid_price)
    
    def get_liquidity_score(self, num_levels: int = 5) -> Optional[float]:
        """
        Calculate a liquidity score based on depth and spread.
        
        Higher score = better liquidity
        
        Args:
            num_levels: Number of levels to consider
        
        Returns:
            Liquidity score
        """
        if not self.orderbook_history:
            return None
        
        ob = self.orderbook_history[-1]
        
        # Get cumulative depth
        depths = self.get_cumulative_depth(num_levels)
        if depths is None:
            return None
        
        bid_depth, ask_depth = depths
        total_depth = bid_depth + ask_depth
        
        # Get spread
        if not ob.bids or not ob.asks:
            return None
        
        spread = ob.asks[0].price - ob.bids[0].price
        mid_price = (ob.bids[0].price + ob.asks[0].price) / 2
        
        if spread == 0:
            return None
        
        # Liquidity score = depth / spread (normalized by mid price)
        liquidity_score = (total_depth * mid_price) / spread
        
        return liquidity_score
    
    def detect_depth_depletion(self, threshold_percentile: float = 25) -> bool:
        """
        Detect if current depth is abnormally low.
        
        Args:
            threshold_percentile: Percentile threshold for detection
        
        Returns:
            True if depth is depleted
        """
        if len(self.orderbook_history) < 10:
            return False
        
        current_depth = self.get_current_depth()
        if current_depth is None:
            return False
        
        _, _, current_total = current_depth
        
        # Calculate historical depth percentile
        historical_depths = [ob.total_depth for ob in self.orderbook_history[:-1]]
        threshold = np.percentile(historical_depths, threshold_percentile)
        
        return current_total < threshold
    
    def get_depth_metrics(self) -> dict:
        """
        Get comprehensive depth metrics.
        
        Returns:
            Dictionary of depth metrics
        """
        current_depth = self.get_current_depth()
        
        if current_depth is None:
            return {}
        
        bid_depth, ask_depth, total_depth = current_depth
        
        return {
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'total_depth': total_depth,
            'depth_imbalance': self.get_depth_imbalance(),
            'weighted_mid_price': self.get_weighted_mid_price(),
            'liquidity_score': self.get_liquidity_score(),
            'is_depth_depleted': self.detect_depth_depletion(),
            'price_impact_buy_1lot': self.get_price_impact(1.0, 'buy'),
            'price_impact_sell_1lot': self.get_price_impact(1.0, 'sell')
        }
