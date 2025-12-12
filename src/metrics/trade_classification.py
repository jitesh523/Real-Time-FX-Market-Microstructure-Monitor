"""Lee-Ready algorithm for trade classification."""

from typing import Optional
from datetime import datetime
from loguru import logger

from src.models import Trade, TickData


class LeeReadyClassifier:
    """
    Classify trades as buyer-initiated or seller-initiated using Lee-Ready algorithm.
    
    The algorithm uses:
    1. Quote rule: Compare trade price to mid-quote
    2. Tick test: Compare to previous trade price if at mid-quote
    """
    
    def __init__(self):
        """Initialize Lee-Ready classifier."""
        self.previous_trade_price = None
        self.buy_initiated_count = 0
        self.sell_initiated_count = 0
        
        logger.info("Initialized Lee-Ready Classifier")
    
    def classify_trade(self, trade: Trade, current_tick: TickData) -> dict:
        """
        Classify a trade as buyer or seller initiated.
        
        Args:
            trade: Trade to classify
            current_tick: Current market quote
        
        Returns:
            Dictionary with classification results
        """
        mid_quote = current_tick.mid_price
        trade_price = trade.price
        
        # Quote rule
        if trade_price > mid_quote:
            # Above mid-quote = buyer-initiated
            classification = 'buy'
            self.buy_initiated_count += 1
        elif trade_price < mid_quote:
            # Below mid-quote = seller-initiated
            classification = 'sell'
            self.sell_initiated_count += 1
        else:
            # At mid-quote, use tick test
            classification = self._tick_test(trade_price)
        
        # Update previous price
        self.previous_trade_price = trade_price
        
        return {
            'trade_id': trade.trade_id,
            'classification': classification,
            'method': 'quote_rule' if trade_price != mid_quote else 'tick_test',
            'trade_price': trade_price,
            'mid_quote': mid_quote,
            'distance_from_mid': trade_price - mid_quote
        }
    
    def _tick_test(self, trade_price: float) -> str:
        """
        Apply tick test when trade is at mid-quote.
        
        Args:
            trade_price: Current trade price
        
        Returns:
            'buy' or 'sell'
        """
        if self.previous_trade_price is None:
            # No previous price, default to buy
            self.buy_initiated_count += 1
            return 'buy'
        
        if trade_price > self.previous_trade_price:
            # Uptick = buyer-initiated
            self.buy_initiated_count += 1
            return 'buy'
        elif trade_price < self.previous_trade_price:
            # Downtick = seller-initiated
            self.sell_initiated_count += 1
            return 'sell'
        else:
            # Zero tick, use previous classification
            # Default to buy if no history
            self.buy_initiated_count += 1
            return 'buy'
    
    def get_statistics(self) -> dict:
        """Get classification statistics."""
        total = self.buy_initiated_count + self.sell_initiated_count
        
        if total == 0:
            buy_ratio = 0.5
        else:
            buy_ratio = self.buy_initiated_count / total
        
        return {
            'buy_initiated_count': self.buy_initiated_count,
            'sell_initiated_count': self.sell_initiated_count,
            'total_classified': total,
            'buy_ratio': buy_ratio,
            'sell_ratio': 1 - buy_ratio
        }
    
    def get_order_flow_imbalance(self) -> float:
        """
        Calculate order flow imbalance from classified trades.
        
        Returns:
            Imbalance between -1 and 1
        """
        total = self.buy_initiated_count + self.sell_initiated_count
        
        if total == 0:
            return 0.0
        
        return (self.buy_initiated_count - self.sell_initiated_count) / total


class BulkVolumeClassification:
    """
    Classify trades using Bulk Volume Classification (BVC) method.
    
    Alternative to Lee-Ready that uses volume-weighted approach.
    """
    
    def __init__(self):
        """Initialize BVC classifier."""
        self.buy_volume = 0.0
        self.sell_volume = 0.0
        
        logger.info("Initialized Bulk Volume Classification")
    
    def classify_trade(self, trade: Trade, current_tick: TickData) -> dict:
        """
        Classify trade using BVC method.
        
        Args:
            trade: Trade to classify
            current_tick: Current market quote
        
        Returns:
            Classification results
        """
        mid_quote = current_tick.mid_price
        trade_price = trade.price
        
        # Calculate distance from mid-quote
        distance = trade_price - mid_quote
        
        # Proportional allocation based on distance
        if distance > 0:
            # Closer to ask = more buyer-initiated
            buy_proportion = min(1.0, distance / (current_tick.ask - mid_quote + 1e-10))
        elif distance < 0:
            # Closer to bid = more seller-initiated
            buy_proportion = max(0.0, 1 - abs(distance) / (mid_quote - current_tick.bid + 1e-10))
        else:
            # At mid-quote = 50/50
            buy_proportion = 0.5
        
        sell_proportion = 1 - buy_proportion
        
        # Allocate volume
        buy_vol = trade.size * buy_proportion
        sell_vol = trade.size * sell_proportion
        
        self.buy_volume += buy_vol
        self.sell_volume += sell_vol
        
        # Classify based on majority
        classification = 'buy' if buy_proportion > 0.5 else 'sell'
        
        return {
            'trade_id': trade.trade_id,
            'classification': classification,
            'buy_proportion': buy_proportion,
            'sell_proportion': sell_proportion,
            'buy_volume': buy_vol,
            'sell_volume': sell_vol
        }
    
    def get_statistics(self) -> dict:
        """Get BVC statistics."""
        total_volume = self.buy_volume + self.sell_volume
        
        if total_volume == 0:
            buy_ratio = 0.5
        else:
            buy_ratio = self.buy_volume / total_volume
        
        return {
            'buy_volume': self.buy_volume,
            'sell_volume': self.sell_volume,
            'total_volume': total_volume,
            'buy_ratio': buy_ratio,
            'sell_ratio': 1 - buy_ratio
        }
    
    def get_volume_imbalance(self) -> float:
        """Calculate volume-weighted imbalance."""
        total_volume = self.buy_volume + self.sell_volume
        
        if total_volume == 0:
            return 0.0
        
        return (self.buy_volume - self.sell_volume) / total_volume
