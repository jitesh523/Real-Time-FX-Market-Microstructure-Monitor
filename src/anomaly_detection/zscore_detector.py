"""Z-score based anomaly detection for market data."""

from typing import List, Optional, Dict
from collections import deque
import numpy as np
from loguru import logger

from src.models import TickData, MarketMetrics


class ZScoreDetector:
    """Z-score based anomaly detection."""
    
    def __init__(self, window_size: int = 100, threshold: float = 3.0):
        """
        Initialize Z-score detector.
        
        Args:
            window_size: Number of samples for rolling statistics
            threshold: Z-score threshold for anomaly detection
        """
        self.window_size = window_size
        self.threshold = threshold
        self.values = deque(maxlen=window_size)
        self.anomaly_count = 0
        logger.info(f"Initialized Z-score detector with window={window_size}, threshold={threshold}")
    
    def add_value(self, value: float):
        """Add a new value to the window."""
        self.values.append(value)
    
    def get_zscore(self, value: float) -> Optional[float]:
        """
        Calculate Z-score for a value.
        
        Args:
            value: Value to score
        
        Returns:
            Z-score
        """
        if len(self.values) < 2:
            return None
        
        mean = np.mean(self.values)
        std = np.std(self.values)
        
        if std == 0:
            return 0.0
        
        zscore = (value - mean) / std
        return zscore
    
    def is_anomaly(self, zscore: Optional[float]) -> bool:
        """
        Determine if Z-score indicates an anomaly.
        
        Args:
            zscore: Z-score value
        
        Returns:
            True if anomaly detected
        """
        if zscore is None:
            return False
        
        is_anom = abs(zscore) > self.threshold
        if is_anom:
            self.anomaly_count += 1
        return is_anom
    
    def detect_and_update(self, value: float) -> Dict:
        """
        Detect anomaly and update the detector.
        
        Args:
            value: New value
        
        Returns:
            Dictionary with detection results
        """
        zscore = self.get_zscore(value)
        is_anom = self.is_anomaly(zscore)
        self.add_value(value)
        
        return {
            'value': value,
            'zscore': zscore,
            'is_anomaly': is_anom,
            'threshold': self.threshold
        }


class MultiVariateZScoreDetector:
    """Multi-variate Z-score anomaly detection for market metrics."""
    
    def __init__(self, window_size: int = 100, threshold: float = 3.0):
        """
        Initialize multi-variate Z-score detector.
        
        Args:
            window_size: Window size for statistics
            threshold: Z-score threshold
        """
        self.window_size = window_size
        self.threshold = threshold
        
        # Individual detectors for different metrics
        self.spread_detector = ZScoreDetector(window_size, threshold)
        self.depth_detector = ZScoreDetector(window_size, threshold)
        self.imbalance_detector = ZScoreDetector(window_size, threshold)
        self.volatility_detector = ZScoreDetector(window_size, threshold)
        
        logger.info("Initialized multi-variate Z-score detector")
    
    def detect_tick_anomaly(self, tick: TickData) -> Dict:
        """
        Detect anomalies in tick data.
        
        Args:
            tick: Tick data
        
        Returns:
            Dictionary with detection results
        """
        # Detect spread anomaly
        spread_result = self.spread_detector.detect_and_update(tick.spread_bps)
        
        # Detect size anomaly
        total_size = tick.bid_size + tick.ask_size
        depth_result = self.depth_detector.detect_and_update(total_size)
        
        # Detect imbalance anomaly
        size_imbalance = (tick.bid_size - tick.ask_size) / (tick.bid_size + tick.ask_size + 1e-10)
        imbalance_result = self.imbalance_detector.detect_and_update(size_imbalance)
        
        # Overall anomaly if any metric is anomalous
        is_anomaly = (spread_result['is_anomaly'] or 
                     depth_result['is_anomaly'] or 
                     imbalance_result['is_anomaly'])
        
        # Determine anomaly type
        anomaly_types = []
        if spread_result['is_anomaly']:
            anomaly_types.append('spread')
        if depth_result['is_anomaly']:
            anomaly_types.append('depth')
        if imbalance_result['is_anomaly']:
            anomaly_types.append('imbalance')
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_types': anomaly_types,
            'spread': spread_result,
            'depth': depth_result,
            'imbalance': imbalance_result
        }
    
    def detect_metrics_anomaly(self, metrics: MarketMetrics) -> Dict:
        """
        Detect anomalies in market metrics.
        
        Args:
            metrics: Market metrics
        
        Returns:
            Dictionary with detection results
        """
        # Detect spread anomaly
        spread_result = self.spread_detector.detect_and_update(metrics.spread_bps)
        
        # Detect depth anomaly
        depth_result = self.depth_detector.detect_and_update(metrics.total_depth)
        
        # Detect imbalance anomaly
        imbalance_result = self.imbalance_detector.detect_and_update(metrics.order_flow_imbalance)
        
        # Detect volatility anomaly (if available)
        volatility_result = None
        if metrics.volatility is not None:
            volatility_result = self.volatility_detector.detect_and_update(metrics.volatility)
        
        # Overall anomaly
        is_anomaly = (spread_result['is_anomaly'] or 
                     depth_result['is_anomaly'] or 
                     imbalance_result['is_anomaly'] or
                     (volatility_result and volatility_result['is_anomaly']))
        
        # Determine anomaly types
        anomaly_types = []
        if spread_result['is_anomaly']:
            anomaly_types.append('spread')
        if depth_result['is_anomaly']:
            anomaly_types.append('depth')
        if imbalance_result['is_anomaly']:
            anomaly_types.append('imbalance')
        if volatility_result and volatility_result['is_anomaly']:
            anomaly_types.append('volatility')
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_types': anomaly_types,
            'spread': spread_result,
            'depth': depth_result,
            'imbalance': imbalance_result,
            'volatility': volatility_result
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics from all detectors."""
        return {
            'spread_anomalies': self.spread_detector.anomaly_count,
            'depth_anomalies': self.depth_detector.anomaly_count,
            'imbalance_anomalies': self.imbalance_detector.anomaly_count,
            'volatility_anomalies': self.volatility_detector.anomaly_count
        }
