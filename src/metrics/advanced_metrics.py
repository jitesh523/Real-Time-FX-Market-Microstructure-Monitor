"""Advanced microstructure metrics: Kyle's Lambda and Amihud Illiquidity."""

from typing import List, Optional
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

from src.models import Trade, TickData


class KylesLambda:
    """
    Calculate Kyle's Lambda - a measure of price impact.
    
    Lambda measures how much prices move in response to order flow.
    Higher lambda = higher price impact = lower liquidity.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize Kyle's Lambda calculator.
        
        Args:
            window_size: Number of trades to use for calculation
        """
        self.window_size = window_size
        self.trades = []
        self.price_changes = []
        self.signed_volumes = []
        
        logger.info(f"Initialized Kyle's Lambda with window={window_size}")
    
    def add_trade(self, trade: Trade, previous_price: float):
        """
        Add a trade and calculate price change.
        
        Args:
            trade: Trade object
            previous_price: Price before this trade
        """
        self.trades.append(trade)
        
        # Calculate price change
        price_change = trade.price - previous_price
        self.price_changes.append(price_change)
        
        # Calculate signed volume (positive for buy, negative for sell)
        signed_volume = trade.size if trade.side == 'buy' else -trade.size
        self.signed_volumes.append(signed_volume)
        
        # Keep window size
        if len(self.trades) > self.window_size:
            self.trades.pop(0)
            self.price_changes.pop(0)
            self.signed_volumes.pop(0)
    
    def calculate_lambda(self) -> Optional[float]:
        """
        Calculate Kyle's Lambda.
        
        Lambda = Cov(ΔP, Q) / Var(Q)
        where ΔP is price change and Q is signed volume
        
        Returns:
            Kyle's Lambda value
        """
        if len(self.price_changes) < 10:
            return None
        
        # Calculate covariance and variance
        price_changes = np.array(self.price_changes)
        signed_volumes = np.array(self.signed_volumes)
        
        if np.var(signed_volumes) == 0:
            return None
        
        covariance = np.cov(price_changes, signed_volumes)[0, 1]
        variance = np.var(signed_volumes)
        
        lambda_value = covariance / variance
        
        return lambda_value
    
    def get_metrics(self) -> dict:
        """Get Kyle's Lambda metrics."""
        lambda_value = self.calculate_lambda()
        
        return {
            'kyles_lambda': lambda_value,
            'num_trades': len(self.trades),
            'avg_price_change': np.mean(self.price_changes) if self.price_changes else None,
            'avg_signed_volume': np.mean(self.signed_volumes) if self.signed_volumes else None
        }


class AmihudIlliquidity:
    """
    Calculate Amihud Illiquidity Ratio.
    
    Measures price impact per unit of volume.
    Higher ratio = more illiquid market.
    
    ILLIQ = (1/N) * Σ(|R_t| / Volume_t)
    where R_t is return and Volume_t is dollar volume
    """
    
    def __init__(self, window_minutes: int = 60):
        """
        Initialize Amihud Illiquidity calculator.
        
        Args:
            window_minutes: Time window for calculation
        """
        self.window_minutes = window_minutes
        self.data_points = []
        
        logger.info(f"Initialized Amihud Illiquidity with window={window_minutes}min")
    
    def add_data_point(self, timestamp: datetime, price: float, volume: float):
        """
        Add a data point.
        
        Args:
            timestamp: Time of observation
            price: Price at this time
            volume: Trading volume
        """
        self.data_points.append({
            'timestamp': timestamp,
            'price': price,
            'volume': volume
        })
        
        # Remove old data points
        cutoff_time = timestamp - timedelta(minutes=self.window_minutes)
        self.data_points = [
            dp for dp in self.data_points
            if dp['timestamp'] >= cutoff_time
        ]
    
    def calculate_illiquidity(self) -> Optional[float]:
        """
        Calculate Amihud Illiquidity Ratio.
        
        Returns:
            Illiquidity ratio
        """
        if len(self.data_points) < 2:
            return None
        
        illiquidity_values = []
        
        for i in range(1, len(self.data_points)):
            prev = self.data_points[i-1]
            curr = self.data_points[i]
            
            # Calculate return
            if prev['price'] == 0:
                continue
            
            return_pct = abs((curr['price'] - prev['price']) / prev['price'])
            
            # Calculate dollar volume
            dollar_volume = curr['volume'] * curr['price']
            
            if dollar_volume == 0:
                continue
            
            # Illiquidity for this period
            illiq = return_pct / dollar_volume
            illiquidity_values.append(illiq)
        
        if not illiquidity_values:
            return None
        
        # Average illiquidity
        return np.mean(illiquidity_values)
    
    def get_metrics(self) -> dict:
        """Get Amihud Illiquidity metrics."""
        illiquidity = self.calculate_illiquidity()
        
        return {
            'amihud_illiquidity': illiquidity,
            'num_data_points': len(self.data_points),
            'time_span_minutes': (
                (self.data_points[-1]['timestamp'] - self.data_points[0]['timestamp']).total_seconds() / 60
                if len(self.data_points) > 1 else 0
            )
        }


class AdvancedMetricsCalculator:
    """Combined calculator for advanced microstructure metrics."""
    
    def __init__(self):
        """Initialize all advanced metrics calculators."""
        self.kyles_lambda = KylesLambda()
        self.amihud_illiquidity = AmihudIlliquidity()
        self.previous_price = None
        
        logger.info("Initialized Advanced Metrics Calculator")
    
    def process_trade(self, trade: Trade):
        """Process a trade for Kyle's Lambda."""
        if self.previous_price is not None:
            self.kyles_lambda.add_trade(trade, self.previous_price)
        
        self.previous_price = trade.price
    
    def process_tick(self, tick: TickData):
        """Process a tick for Amihud Illiquidity."""
        total_volume = tick.bid_size + tick.ask_size
        self.amihud_illiquidity.add_data_point(
            tick.timestamp,
            tick.mid_price,
            total_volume
        )
    
    def get_all_metrics(self) -> dict:
        """Get all advanced metrics."""
        kyles_metrics = self.kyles_lambda.get_metrics()
        amihud_metrics = self.amihud_illiquidity.get_metrics()
        
        return {
            **kyles_metrics,
            **amihud_metrics,
            'liquidity_score': self._calculate_liquidity_score(
                kyles_metrics.get('kyles_lambda'),
                amihud_metrics.get('amihud_illiquidity')
            )
        }
    
    def _calculate_liquidity_score(self, lambda_val: Optional[float],
                                   illiquidity: Optional[float]) -> Optional[float]:
        """
        Calculate overall liquidity score (0-100).
        
        Higher score = better liquidity
        """
        if lambda_val is None and illiquidity is None:
            return None
        
        score = 50.0  # Start at neutral
        
        # Lower lambda is better (less price impact)
        if lambda_val is not None:
            if lambda_val < 0.0001:
                score += 25
            elif lambda_val < 0.001:
                score += 15
            elif lambda_val > 0.01:
                score -= 25
        
        # Lower illiquidity is better
        if illiquidity is not None:
            if illiquidity < 0.00001:
                score += 25
            elif illiquidity < 0.0001:
                score += 15
            elif illiquidity > 0.001:
                score -= 25
        
        return max(0.0, min(100.0, score))
