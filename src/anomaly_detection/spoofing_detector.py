"""Spoofing detection - detecting fake orders to manipulate prices."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from loguru import logger

from src.models import OrderBook, Trade


class SpoofingDetector:
    """Detect spoofing - placing large orders with intent to cancel."""
    
    def __init__(self, depth_threshold: int = 5, size_multiplier: float = 3.0,
                 cancellation_window_seconds: int = 10):
        """
        Initialize spoofing detector.
        
        Args:
            depth_threshold: Minimum depth level to monitor
            size_multiplier: Multiplier for detecting abnormally large orders
            cancellation_window_seconds: Time window to detect cancellations
        """
        self.depth_threshold = depth_threshold
        self.size_multiplier = size_multiplier
        self.cancellation_window = cancellation_window_seconds
        
        self.orderbook_history = deque(maxlen=100)
        self.large_order_events = deque()
        self.spoofing_events = 0
        
        logger.info(f"Initialized spoofing detector with depth_threshold={depth_threshold}")
    
    def add_orderbook(self, orderbook: OrderBook):
        """Add an order book snapshot."""
        self.orderbook_history.append(orderbook)
        self._cleanup_old_events(orderbook.timestamp)
    
    def add_trade(self, trade: Trade):
        """Add a trade (to detect if spoofed orders led to trades)."""
        pass  # Can be extended to correlate trades with spoofing
    
    def _cleanup_old_events(self, current_time: datetime):
        """Remove old large order events."""
        cutoff_time = current_time - timedelta(seconds=self.cancellation_window)
        while self.large_order_events and self.large_order_events[0]['timestamp'] < cutoff_time:
            self.large_order_events.popleft()
    
    def detect_spoofing(self) -> Dict:
        """
        Detect spoofing patterns.
        
        Looks for:
        1. Abnormally large orders deep in the book
        2. Rapid cancellation of large orders
        3. Order book imbalance created by large orders
        
        Returns:
            Dictionary with detection results
        """
        if len(self.orderbook_history) < 2:
            return {
                'is_spoofing': False,
                'large_orders_detected': 0
            }
        
        current_ob = self.orderbook_history[-1]
        
        # Detect abnormally large orders
        large_bid_orders = self._detect_large_orders(current_ob.bids, 'bid')
        large_ask_orders = self._detect_large_orders(current_ob.asks, 'ask')
        
        total_large_orders = len(large_bid_orders) + len(large_ask_orders)
        
        # Record large order events
        if total_large_orders > 0:
            self.large_order_events.append({
                'timestamp': current_ob.timestamp,
                'bid_orders': large_bid_orders,
                'ask_orders': large_ask_orders
            })
        
        # Detect rapid cancellations (large orders that disappeared)
        cancellations = self._detect_cancellations()
        
        # Detect order book imbalance from spoofing
        imbalance_spoofing = self._detect_imbalance_spoofing(current_ob)
        
        is_spoofing = (len(cancellations) > 0 or 
                      imbalance_spoofing or 
                      total_large_orders > 3)
        
        if is_spoofing:
            self.spoofing_events += 1
            logger.warning(f"Spoofing detected: {total_large_orders} large orders, {len(cancellations)} cancellations")
        
        return {
            'is_spoofing': is_spoofing,
            'large_orders_detected': total_large_orders,
            'large_bid_orders': large_bid_orders,
            'large_ask_orders': large_ask_orders,
            'rapid_cancellations': len(cancellations),
            'imbalance_spoofing': imbalance_spoofing,
            'total_spoofing_events': self.spoofing_events
        }
    
    def _detect_large_orders(self, levels: List, side: str) -> List[Dict]:
        """
        Detect abnormally large orders in the order book.
        
        Args:
            levels: Order book levels
            side: 'bid' or 'ask'
        
        Returns:
            List of large order details
        """
        if len(levels) < self.depth_threshold:
            return []
        
        # Calculate average size across all levels
        sizes = [level.size for level in levels]
        if not sizes:
            return []
        
        avg_size = sum(sizes) / len(sizes)
        
        # Detect orders significantly larger than average
        large_orders = []
        for i, level in enumerate(levels):
            if level.size > (avg_size * self.size_multiplier):
                large_orders.append({
                    'level': i,
                    'price': level.price,
                    'size': level.size,
                    'avg_size': avg_size,
                    'multiplier': level.size / avg_size if avg_size > 0 else 0,
                    'side': side
                })
        
        return large_orders
    
    def _detect_cancellations(self) -> List[Dict]:
        """
        Detect rapid cancellations of large orders.
        
        Returns:
            List of detected cancellations
        """
        if len(self.orderbook_history) < 2 or len(self.large_order_events) < 2:
            return []
        
        cancellations = []
        
        # Compare recent large orders with current order book
        current_ob = self.orderbook_history[-1]
        
        for event in list(self.large_order_events)[:-1]:  # Exclude current event
            # Check if large orders from this event are still present
            for order in event['bid_orders'] + event['ask_orders']:
                if not self._is_order_still_present(order, current_ob):
                    cancellations.append({
                        'timestamp': event['timestamp'],
                        'order': order,
                        'time_to_cancel': (current_ob.timestamp - event['timestamp']).total_seconds()
                    })
        
        return cancellations
    
    def _is_order_still_present(self, order: Dict, orderbook: OrderBook) -> bool:
        """Check if an order is still present in the order book."""
        levels = orderbook.bids if order['side'] == 'bid' else orderbook.asks
        
        if order['level'] >= len(levels):
            return False
        
        level = levels[order['level']]
        
        # Check if price and size are similar
        price_match = abs(level.price - order['price']) < 0.00001
        size_match = abs(level.size - order['size']) / order['size'] < 0.2  # 20% tolerance
        
        return price_match and size_match
    
    def _detect_imbalance_spoofing(self, orderbook: OrderBook) -> bool:
        """
        Detect if large orders are creating artificial imbalance.
        
        Args:
            orderbook: Current order book
        
        Returns:
            True if imbalance spoofing detected
        """
        if len(orderbook.bids) < 3 or len(orderbook.asks) < 3:
            return False
        
        # Calculate top-level imbalance
        top_bid_size = sum(level.size for level in orderbook.bids[:3])
        top_ask_size = sum(level.size for level in orderbook.asks[:3])
        
        total_top_size = top_bid_size + top_ask_size
        
        if total_top_size == 0:
            return False
        
        imbalance = abs(top_bid_size - top_ask_size) / total_top_size
        
        # Spoofing if extreme imbalance (>70%)
        return imbalance > 0.7
    
    def get_statistics(self) -> Dict:
        """Get detector statistics."""
        return {
            'total_spoofing_events': self.spoofing_events,
            'current_large_orders': len(self.large_order_events)
        }
