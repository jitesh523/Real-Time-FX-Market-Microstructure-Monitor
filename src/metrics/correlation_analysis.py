"""Correlation analysis between currency pairs."""

from typing import Dict, List
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
from loguru import logger

from src.models import TickData


class PairCorrelationAnalyzer:
    """Analyze correlations between currency pairs."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize correlation analyzer.
        
        Args:
            window_size: Number of ticks for rolling correlation
        """
        self.window_size = window_size
        self.price_history = {}  # symbol -> deque of prices
        
        logger.info(f"Initialized Pair Correlation Analyzer with window={window_size}")
    
    def add_tick(self, tick: TickData):
        """Add a tick for a symbol."""
        if tick.symbol not in self.price_history:
            self.price_history[tick.symbol] = deque(maxlen=self.window_size)
        
        self.price_history[tick.symbol].append({
            'timestamp': tick.timestamp,
            'price': tick.mid_price
        })
    
    def calculate_correlation(self, symbol1: str, symbol2: str) -> Dict:
        """
        Calculate correlation between two symbols.
        
        Args:
            symbol1: First currency pair
            symbol2: Second currency pair
        
        Returns:
            Dictionary with correlation metrics
        """
        if symbol1 not in self.price_history or symbol2 not in self.price_history:
            return {'correlation': None, 'reason': 'Insufficient data'}
        
        prices1 = list(self.price_history[symbol1])
        prices2 = list(self.price_history[symbol2])
        
        if len(prices1) < 10 or len(prices2) < 10:
            return {'correlation': None, 'reason': 'Insufficient data'}
        
        # Align timestamps (use common timestamps)
        timestamps1 = {p['timestamp']: p['price'] for p in prices1}
        timestamps2 = {p['timestamp']: p['price'] for p in prices2}
        
        common_timestamps = set(timestamps1.keys()) & set(timestamps2.keys())
        
        if len(common_timestamps) < 10:
            # Use interpolation for non-aligned data
            return self._calculate_correlation_interpolated(prices1, prices2)
        
        # Get aligned prices
        aligned_prices1 = [timestamps1[t] for t in sorted(common_timestamps)]
        aligned_prices2 = [timestamps2[t] for t in sorted(common_timestamps)]
        
        # Calculate returns
        returns1 = np.diff(np.log(aligned_prices1))
        returns2 = np.diff(np.log(aligned_prices2))
        
        # Calculate correlation
        if len(returns1) < 2:
            return {'correlation': None, 'reason': 'Insufficient aligned data'}
        
        correlation = np.corrcoef(returns1, returns2)[0, 1]
        
        return {
            'correlation': correlation,
            'num_observations': len(returns1),
            'symbol1': symbol1,
            'symbol2': symbol2,
            'strength': self._interpret_correlation(correlation)
        }
    
    def _calculate_correlation_interpolated(self, prices1: List, prices2: List) -> Dict:
        """Calculate correlation with time interpolation."""
        # Simple approach: use most recent N prices
        n = min(len(prices1), len(prices2), 50)
        
        p1 = [p['price'] for p in prices1[-n:]]
        p2 = [p['price'] for p in prices2[-n:]]
        
        if len(p1) < 2 or len(p2) < 2:
            return {'correlation': None, 'reason': 'Insufficient data'}
        
        returns1 = np.diff(np.log(p1))
        returns2 = np.diff(np.log(p2))
        
        correlation = np.corrcoef(returns1, returns2)[0, 1]
        
        return {
            'correlation': correlation,
            'num_observations': len(returns1),
            'method': 'interpolated',
            'strength': self._interpret_correlation(correlation)
        }
    
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(corr)
        
        if abs_corr >= 0.8:
            return 'very_strong'
        elif abs_corr >= 0.6:
            return 'strong'
        elif abs_corr >= 0.4:
            return 'moderate'
        elif abs_corr >= 0.2:
            return 'weak'
        else:
            return 'very_weak'
    
    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """
        Calculate correlation matrix for all pairs.
        
        Returns:
            DataFrame with correlation matrix
        """
        symbols = list(self.price_history.keys())
        
        if len(symbols) < 2:
            return pd.DataFrame()
        
        n = len(symbols)
        corr_matrix = np.zeros((n, n))
        
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if i == j:
                    corr_matrix[i, j] = 1.0
                elif i < j:
                    result = self.calculate_correlation(sym1, sym2)
                    corr = result.get('correlation', 0.0)
                    if corr is not None:
                        corr_matrix[i, j] = corr
                        corr_matrix[j, i] = corr
        
        return pd.DataFrame(corr_matrix, index=symbols, columns=symbols)
    
    def find_highly_correlated_pairs(self, threshold: float = 0.7) -> List[Dict]:
        """
        Find pairs with high correlation.
        
        Args:
            threshold: Minimum correlation threshold
        
        Returns:
            List of highly correlated pairs
        """
        symbols = list(self.price_history.keys())
        highly_correlated = []
        
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols[i+1:], i+1):
                result = self.calculate_correlation(sym1, sym2)
                corr = result.get('correlation')
                
                if corr is not None and abs(corr) >= threshold:
                    highly_correlated.append({
                        'pair': (sym1, sym2),
                        'correlation': corr,
                        'strength': result.get('strength')
                    })
        
        # Sort by absolute correlation
        highly_correlated.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return highly_correlated
