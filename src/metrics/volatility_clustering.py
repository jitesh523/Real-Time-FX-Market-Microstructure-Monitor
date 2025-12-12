"""Volatility clustering detection and analysis."""

from typing import List, Optional
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from loguru import logger

from src.models import TickData


class VolatilityAnalyzer:
    """Analyze volatility clustering in FX markets."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize volatility analyzer.
        
        Args:
            window_size: Number of ticks for rolling calculations
        """
        self.window_size = window_size
        self.tick_history: List[TickData] = []
        self.returns: List[float] = []
    
    def add_tick(self, tick: TickData):
        """Add a new tick and calculate returns."""
        if self.tick_history:
            # Calculate log return
            prev_price = self.tick_history[-1].mid_price
            current_price = tick.mid_price
            
            if prev_price > 0 and current_price > 0:
                log_return = np.log(current_price / prev_price)
                self.returns.append(log_return)
        
        self.tick_history.append(tick)
        
        # Keep only recent data
        if len(self.tick_history) > self.window_size:
            self.tick_history.pop(0)
        
        if len(self.returns) > self.window_size:
            self.returns.pop(0)
    
    def get_realized_volatility(self, annualize: bool = True) -> Optional[float]:
        """
        Calculate realized volatility from returns.
        
        Args:
            annualize: Whether to annualize the volatility
        
        Returns:
            Realized volatility
        """
        if len(self.returns) < 2:
            return None
        
        volatility = np.std(self.returns)
        
        if annualize:
            # Assuming 252 trading days, 24 hours, 60 minutes, 60 seconds
            # and tick_interval_ms determines ticks per second
            # For simplicity, use sqrt(number of periods in a year)
            periods_per_year = 252 * 24 * 60 * 60 * 10  # Assuming ~10 ticks per second
            volatility *= np.sqrt(periods_per_year)
        
        return volatility
    
    def get_ewma_volatility(self, lambda_param: float = 0.94) -> Optional[float]:
        """
        Calculate Exponentially Weighted Moving Average (EWMA) volatility.
        
        Args:
            lambda_param: Decay parameter (typically 0.94 for daily data)
        
        Returns:
            EWMA volatility
        """
        if len(self.returns) < 2:
            return None
        
        # Initialize with first squared return
        ewma_var = self.returns[0] ** 2
        
        # Update with subsequent returns
        for ret in self.returns[1:]:
            ewma_var = lambda_param * ewma_var + (1 - lambda_param) * (ret ** 2)
        
        return np.sqrt(ewma_var)
    
    def get_parkinson_volatility(self) -> Optional[float]:
        """
        Calculate Parkinson volatility using high-low range.
        
        Parkinson volatility = sqrt(1/(4*ln(2)) * mean((ln(high/low))^2))
        
        Returns:
            Parkinson volatility estimate
        """
        if len(self.tick_history) < 2:
            return None
        
        hl_ratios = []
        for tick in self.tick_history:
            if tick.ask > 0 and tick.bid > 0:
                hl_ratio = np.log(tick.ask / tick.bid)
                hl_ratios.append(hl_ratio ** 2)
        
        if not hl_ratios:
            return None
        
        parkinson_var = np.mean(hl_ratios) / (4 * np.log(2))
        return np.sqrt(parkinson_var)
    
    def detect_volatility_clustering(self, threshold: float = 1.5) -> bool:
        """
        Detect volatility clustering using ARCH effects.
        
        Args:
            threshold: Threshold for detection (in standard deviations)
        
        Returns:
            True if volatility clustering detected
        """
        if len(self.returns) < 20:
            return False
        
        # Calculate squared returns (proxy for volatility)
        squared_returns = [r ** 2 for r in self.returns]
        
        # Check if recent volatility is higher than average
        recent_vol = np.mean(squared_returns[-10:])
        avg_vol = np.mean(squared_returns[:-10])
        std_vol = np.std(squared_returns[:-10])
        
        if std_vol == 0:
            return False
        
        z_score = (recent_vol - avg_vol) / std_vol
        
        return z_score > threshold
    
    def get_volatility_regime(self) -> Optional[str]:
        """
        Classify current volatility regime.
        
        Returns:
            'low', 'normal', or 'high'
        """
        if len(self.returns) < 20:
            return None
        
        current_vol = np.std(self.returns[-10:])
        historical_vol = np.std(self.returns[:-10])
        
        if current_vol < 0.7 * historical_vol:
            return 'low'
        elif current_vol > 1.3 * historical_vol:
            return 'high'
        else:
            return 'normal'
    
    def get_volatility_percentile(self) -> Optional[float]:
        """
        Calculate current volatility percentile relative to history.
        
        Returns:
            Percentile (0-100)
        """
        if len(self.returns) < 20:
            return None
        
        # Calculate rolling volatilities
        window = 10
        rolling_vols = []
        
        for i in range(len(self.returns) - window + 1):
            vol = np.std(self.returns[i:i+window])
            rolling_vols.append(vol)
        
        if not rolling_vols:
            return None
        
        current_vol = rolling_vols[-1]
        
        # Calculate percentile
        percentile = stats.percentileofscore(rolling_vols, current_vol)
        
        return percentile
    
    def get_intraday_volatility_pattern(self) -> Optional[dict]:
        """
        Analyze intraday volatility patterns.
        
        Returns:
            Dictionary with volatility by hour
        """
        if len(self.tick_history) < 24:
            return None
        
        hourly_vols = {}
        
        for tick in self.tick_history:
            hour = tick.timestamp.hour
            if hour not in hourly_vols:
                hourly_vols[hour] = []
        
        # Calculate returns by hour
        for i in range(1, len(self.tick_history)):
            prev_price = self.tick_history[i-1].mid_price
            curr_price = self.tick_history[i].mid_price
            hour = self.tick_history[i].timestamp.hour
            
            if prev_price > 0 and curr_price > 0:
                ret = np.log(curr_price / prev_price)
                hourly_vols[hour].append(ret)
        
        # Calculate volatility for each hour
        result = {}
        for hour, returns in hourly_vols.items():
            if len(returns) > 1:
                result[hour] = np.std(returns)
        
        return result
    
    def get_volatility_metrics(self) -> dict:
        """
        Get comprehensive volatility metrics.
        
        Returns:
            Dictionary of volatility metrics
        """
        return {
            'realized_volatility': self.get_realized_volatility(annualize=False),
            'annualized_volatility': self.get_realized_volatility(annualize=True),
            'ewma_volatility': self.get_ewma_volatility(),
            'parkinson_volatility': self.get_parkinson_volatility(),
            'is_clustering': self.detect_volatility_clustering(),
            'volatility_regime': self.get_volatility_regime(),
            'volatility_percentile': self.get_volatility_percentile(),
            'num_returns': len(self.returns)
        }
