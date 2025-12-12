"""Quote stuffing detection for market manipulation."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import deque
from loguru import logger

from src.models import TickData, OrderBook


class QuoteStuffingDetector:
    """Detect quote stuffing - rapid submission and cancellation of orders."""
    
    def __init__(self, window_seconds: int = 1, threshold: int = 100):
        """
        Initialize quote stuffing detector.
        
        Args:
            window_seconds: Time window for detection
            threshold: Number of quote updates to trigger detection
        """
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.quote_timestamps = deque()
        self.orderbook_updates = deque()
        self.stuffing_events = 0
        logger.info(f"Initialized quote stuffing detector with threshold={threshold} updates/{window_seconds}s")
    
    def add_tick(self, tick: TickData):
        """Add a tick (quote update)."""
        self.quote_timestamps.append(tick.timestamp)
        self._cleanup_old_quotes(tick.timestamp)
    
    def add_orderbook(self, orderbook: OrderBook):
        """Add an order book update."""
        self.orderbook_updates.append(orderbook.timestamp)
        self._cleanup_old_orderbook_updates(orderbook.timestamp)
    
    def _cleanup_old_quotes(self, current_time: datetime):
        """Remove quotes outside the time window."""
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        while self.quote_timestamps and self.quote_timestamps[0] < cutoff_time:
            self.quote_timestamps.popleft()
    
    def _cleanup_old_orderbook_updates(self, current_time: datetime):
        """Remove old order book updates."""
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        while self.orderbook_updates and self.orderbook_updates[0] < cutoff_time:
            self.orderbook_updates.popleft()
    
    def get_quote_rate(self) -> int:
        """Get current quote update rate."""
        return len(self.quote_timestamps)
    
    def get_orderbook_update_rate(self) -> int:
        """Get current order book update rate."""
        return len(self.orderbook_updates)
    
    def detect_stuffing(self) -> Dict:
        """
        Detect quote stuffing.
        
        Returns:
            Dictionary with detection results
        """
        quote_rate = self.get_quote_rate()
        orderbook_rate = self.get_orderbook_update_rate()
        
        # Quote stuffing if update rate exceeds threshold
        is_stuffing = quote_rate > self.threshold or orderbook_rate > self.threshold
        
        if is_stuffing:
            self.stuffing_events += 1
            logger.warning(f"Quote stuffing detected: {quote_rate} quotes, {orderbook_rate} OB updates in {self.window_seconds}s")
        
        return {
            'is_stuffing': is_stuffing,
            'quote_rate': quote_rate,
            'orderbook_update_rate': orderbook_rate,
            'threshold': self.threshold,
            'window_seconds': self.window_seconds,
            'total_stuffing_events': self.stuffing_events
        }
    
    def get_statistics(self) -> Dict:
        """Get detector statistics."""
        return {
            'total_stuffing_events': self.stuffing_events,
            'current_quote_rate': self.get_quote_rate(),
            'current_orderbook_rate': self.get_orderbook_update_rate()
        }


class AdaptiveQuoteStuffingDetector:
    """Adaptive quote stuffing detector with dynamic thresholds."""
    
    def __init__(self, window_seconds: int = 1, initial_threshold: int = 100,
                 adaptation_window: int = 300):
        """
        Initialize adaptive detector.
        
        Args:
            window_seconds: Detection window
            initial_threshold: Initial threshold
            adaptation_window: Window for calculating adaptive threshold (seconds)
        """
        self.window_seconds = window_seconds
        self.threshold = initial_threshold
        self.adaptation_window = adaptation_window
        
        self.quote_timestamps = deque()
        self.historical_rates = deque(maxlen=adaptation_window)
        self.stuffing_events = 0
        
        logger.info(f"Initialized adaptive quote stuffing detector")
    
    def add_tick(self, tick: TickData):
        """Add a tick and update adaptive threshold."""
        self.quote_timestamps.append(tick.timestamp)
        self._cleanup_old_quotes(tick.timestamp)
        
        # Update historical rates
        current_rate = len(self.quote_timestamps)
        self.historical_rates.append(current_rate)
        
        # Update adaptive threshold (mean + 3 * std)
        if len(self.historical_rates) >= 30:
            import numpy as np
            mean_rate = np.mean(self.historical_rates)
            std_rate = np.std(self.historical_rates)
            self.threshold = mean_rate + (3 * std_rate)
    
    def _cleanup_old_quotes(self, current_time: datetime):
        """Remove quotes outside the time window."""
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        while self.quote_timestamps and self.quote_timestamps[0] < cutoff_time:
            self.quote_timestamps.popleft()
    
    def detect_stuffing(self) -> Dict:
        """Detect quote stuffing with adaptive threshold."""
        quote_rate = len(self.quote_timestamps)
        is_stuffing = quote_rate > self.threshold
        
        if is_stuffing:
            self.stuffing_events += 1
            logger.warning(f"Adaptive quote stuffing detected: {quote_rate} quotes (threshold: {self.threshold:.1f})")
        
        return {
            'is_stuffing': is_stuffing,
            'quote_rate': quote_rate,
            'adaptive_threshold': self.threshold,
            'window_seconds': self.window_seconds,
            'total_stuffing_events': self.stuffing_events
        }
