"""Bid-ask spread calculator for FX market analysis."""

from typing import List, Optional
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

from src.models import TickData


class SpreadCalculator:
    """Calculate various spread metrics for FX market analysis."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize spread calculator.
        
        Args:
            window_size: Number of ticks to use for rolling calculations
        """
        self.window_size = window_size
        self.tick_history: List[TickData] = []
    
    def add_tick(self, tick: TickData):
        """Add a new tick to the history."""
        self.tick_history.append(tick)
        
        # Keep only the most recent ticks
        if len(self.tick_history) > self.window_size:
            self.tick_history.pop(0)
    
    def get_current_spread(self) -> Optional[float]:
        """Get the current bid-ask spread."""
        if not self.tick_history:
            return None
        return self.tick_history[-1].spread
    
    def get_current_spread_bps(self) -> Optional[float]:
        """Get the current spread in basis points."""
        if not self.tick_history:
            return None
        return self.tick_history[-1].spread_bps
    
    def get_average_spread(self) -> Optional[float]:
        """Calculate average spread over the window."""
        if not self.tick_history:
            return None
        
        spreads = [tick.spread for tick in self.tick_history]
        return np.mean(spreads)
    
    def get_average_spread_bps(self) -> Optional[float]:
        """Calculate average spread in basis points over the window."""
        if not self.tick_history:
            return None
        
        spread_bps = [tick.spread_bps for tick in self.tick_history]
        return np.mean(spread_bps)
    
    def get_spread_volatility(self) -> Optional[float]:
        """Calculate spread volatility (standard deviation)."""
        if len(self.tick_history) < 2:
            return None
        
        spreads = [tick.spread for tick in self.tick_history]
        return np.std(spreads)
    
    def get_relative_spread(self) -> Optional[float]:
        """
        Calculate relative spread: (ask - bid) / mid_price.
        This is essentially spread_bps / 10000.
        """
        if not self.tick_history:
            return None
        
        tick = self.tick_history[-1]
        return tick.spread / tick.mid_price
    
    def get_effective_spread(self, trade_price: float, trade_side: str) -> Optional[float]:
        """
        Calculate effective spread for a trade.
        
        Effective spread = 2 * |trade_price - mid_price|
        
        Args:
            trade_price: Price at which the trade was executed
            trade_side: 'buy' or 'sell'
        
        Returns:
            Effective spread
        """
        if not self.tick_history:
            return None
        
        mid_price = self.tick_history[-1].mid_price
        return 2 * abs(trade_price - mid_price)
    
    def get_realized_spread(self, trade_price: float, trade_side: str, 
                           future_mid_price: float) -> float:
        """
        Calculate realized spread for a trade.
        
        Realized spread = 2 * (trade_price - future_mid_price) * direction
        where direction = +1 for buy, -1 for sell
        
        Args:
            trade_price: Price at which the trade was executed
            trade_side: 'buy' or 'sell'
            future_mid_price: Mid price at a future time point
        
        Returns:
            Realized spread
        """
        direction = 1 if trade_side == 'buy' else -1
        return 2 * direction * (trade_price - future_mid_price)
    
    def get_quoted_spread_percentile(self, percentile: float = 95) -> Optional[float]:
        """
        Calculate percentile of quoted spreads.
        
        Args:
            percentile: Percentile to calculate (0-100)
        
        Returns:
            Spread at the specified percentile
        """
        if not self.tick_history:
            return None
        
        spreads = [tick.spread for tick in self.tick_history]
        return np.percentile(spreads, percentile)
    
    def detect_spread_widening(self, threshold_multiplier: float = 2.0) -> bool:
        """
        Detect if current spread is abnormally wide.
        
        Args:
            threshold_multiplier: Number of standard deviations above mean
        
        Returns:
            True if spread is abnormally wide
        """
        if len(self.tick_history) < 10:
            return False
        
        current_spread = self.get_current_spread()
        avg_spread = self.get_average_spread()
        spread_vol = self.get_spread_volatility()
        
        if current_spread is None or avg_spread is None or spread_vol is None:
            return False
        
        threshold = avg_spread + (threshold_multiplier * spread_vol)
        return current_spread > threshold
    
    def get_spread_metrics(self) -> dict:
        """
        Get comprehensive spread metrics.
        
        Returns:
            Dictionary of spread metrics
        """
        return {
            'current_spread': self.get_current_spread(),
            'current_spread_bps': self.get_current_spread_bps(),
            'average_spread': self.get_average_spread(),
            'average_spread_bps': self.get_average_spread_bps(),
            'spread_volatility': self.get_spread_volatility(),
            'relative_spread': self.get_relative_spread(),
            'spread_95th_percentile': self.get_quoted_spread_percentile(95),
            'is_spread_widening': self.detect_spread_widening(),
            'window_size': len(self.tick_history)
        }
