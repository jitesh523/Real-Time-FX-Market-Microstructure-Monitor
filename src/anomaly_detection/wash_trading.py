"""Wash trading detection - detecting self-trading patterns."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from loguru import logger

from src.models import Trade


class WashTradingDetector:
    """Detect wash trading - simultaneous buy and sell orders."""
    
    def __init__(self, window_seconds: int = 60, price_tolerance: float = 0.0001,
                 size_tolerance: float = 0.1):
        """
        Initialize wash trading detector.
        
        Args:
            window_seconds: Time window for matching trades
            price_tolerance: Price tolerance for matching trades
            size_tolerance: Size tolerance for matching trades (as fraction)
        """
        self.window_seconds = window_seconds
        self.price_tolerance = price_tolerance
        self.size_tolerance = size_tolerance
        
        self.trade_history = deque()
        self.wash_trade_count = 0
        self.suspicious_patterns = []
        
        logger.info(f"Initialized wash trading detector with window={window_seconds}s")
    
    def add_trade(self, trade: Trade):
        """Add a trade to the history."""
        self.trade_history.append(trade)
        self._cleanup_old_trades(trade.timestamp)
    
    def _cleanup_old_trades(self, current_time: datetime):
        """Remove trades outside the time window."""
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        while self.trade_history and self.trade_history[0].timestamp < cutoff_time:
            self.trade_history.popleft()
    
    def detect_wash_trading(self) -> Dict:
        """
        Detect wash trading patterns.
        
        Looks for:
        1. Simultaneous buy and sell at same price
        2. Similar sizes
        3. Within short time window
        
        Returns:
            Dictionary with detection results
        """
        if len(self.trade_history) < 2:
            return {
                'is_wash_trading': False,
                'matched_pairs': 0,
                'total_trades': len(self.trade_history)
            }
        
        # Group trades by symbol
        trades_by_symbol = defaultdict(list)
        for trade in self.trade_history:
            trades_by_symbol[trade.symbol].append(trade)
        
        matched_pairs = 0
        suspicious_pairs = []
        
        # Check each symbol
        for symbol, trades in trades_by_symbol.items():
            # Separate buy and sell trades
            buy_trades = [t for t in trades if t.side == 'buy']
            sell_trades = [t for t in trades if t.side == 'sell']
            
            # Look for matching pairs
            for buy_trade in buy_trades:
                for sell_trade in sell_trades:
                    if self._is_matching_pair(buy_trade, sell_trade):
                        matched_pairs += 1
                        suspicious_pairs.append({
                            'buy_trade': buy_trade,
                            'sell_trade': sell_trade,
                            'price_diff': abs(buy_trade.price - sell_trade.price),
                            'size_diff': abs(buy_trade.size - sell_trade.size),
                            'time_diff': abs((buy_trade.timestamp - sell_trade.timestamp).total_seconds())
                        })
        
        is_wash_trading = matched_pairs > 0
        
        if is_wash_trading:
            self.wash_trade_count += matched_pairs
            self.suspicious_patterns.extend(suspicious_pairs)
            logger.warning(f"Wash trading detected: {matched_pairs} matched pairs")
        
        return {
            'is_wash_trading': is_wash_trading,
            'matched_pairs': matched_pairs,
            'total_trades': len(self.trade_history),
            'total_wash_trades': self.wash_trade_count,
            'suspicious_pairs': suspicious_pairs[:5]  # Return top 5
        }
    
    def _is_matching_pair(self, buy_trade: Trade, sell_trade: Trade) -> bool:
        """
        Check if buy and sell trades form a wash trading pair.
        
        Args:
            buy_trade: Buy trade
            sell_trade: Sell trade
        
        Returns:
            True if trades match wash trading pattern
        """
        # Check price similarity
        price_diff = abs(buy_trade.price - sell_trade.price)
        if price_diff > self.price_tolerance:
            return False
        
        # Check size similarity
        size_diff = abs(buy_trade.size - sell_trade.size)
        avg_size = (buy_trade.size + sell_trade.size) / 2
        if avg_size > 0 and (size_diff / avg_size) > self.size_tolerance:
            return False
        
        # Check time proximity (within window)
        time_diff = abs((buy_trade.timestamp - sell_trade.timestamp).total_seconds())
        if time_diff > self.window_seconds:
            return False
        
        return True
    
    def get_statistics(self) -> Dict:
        """Get detector statistics."""
        return {
            'total_wash_trades': self.wash_trade_count,
            'suspicious_patterns_count': len(self.suspicious_patterns),
            'current_trades_in_window': len(self.trade_history)
        }


class VolumeBasedWashDetector:
    """Detect wash trading based on volume patterns."""
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize volume-based wash detector.
        
        Args:
            window_seconds: Time window for analysis
        """
        self.window_seconds = window_seconds
        self.trade_history = deque()
        self.wash_events = 0
        
        logger.info("Initialized volume-based wash trading detector")
    
    def add_trade(self, trade: Trade):
        """Add a trade."""
        self.trade_history.append(trade)
        self._cleanup_old_trades(trade.timestamp)
    
    def _cleanup_old_trades(self, current_time: datetime):
        """Remove old trades."""
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        while self.trade_history and self.trade_history[0].timestamp < cutoff_time:
            self.trade_history.popleft()
    
    def detect_wash_trading(self) -> Dict:
        """
        Detect wash trading based on volume patterns.
        
        Looks for:
        1. Balanced buy/sell volumes
        2. No net position change
        3. High trading activity
        
        Returns:
            Detection results
        """
        if len(self.trade_history) < 4:
            return {'is_wash_trading': False}
        
        # Calculate buy and sell volumes
        buy_volume = sum(t.size for t in self.trade_history if t.side == 'buy')
        sell_volume = sum(t.size for t in self.trade_history if t.side == 'sell')
        
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return {'is_wash_trading': False}
        
        # Calculate volume imbalance
        volume_imbalance = abs(buy_volume - sell_volume) / total_volume
        
        # Wash trading if volumes are very balanced (low imbalance)
        # and there's significant trading activity
        is_wash = (volume_imbalance < 0.1 and  # Less than 10% imbalance
                  len(self.trade_history) > 10)  # At least 10 trades
        
        if is_wash:
            self.wash_events += 1
            logger.warning(f"Volume-based wash trading detected: imbalance={volume_imbalance:.3f}")
        
        return {
            'is_wash_trading': is_wash,
            'volume_imbalance': volume_imbalance,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'trade_count': len(self.trade_history),
            'total_wash_events': self.wash_events
        }
