"""Half-Space Trees for streaming anomaly detection using River."""

from typing import Optional, Dict
from datetime import datetime
from river import anomaly
from loguru import logger

from src.models import TickData, MarketMetrics


class HalfSpaceTreeDetector:
    """Streaming anomaly detection using Half-Space Trees from River."""
    
    def __init__(self, n_trees: int = 10, height: int = 8, window_size: int = 250,
                 seed: int = 42):
        """
        Initialize Half-Space Trees detector.
        
        Args:
            n_trees: Number of trees in the ensemble
            height: Height of each tree
            window_size: Window size for the detector
            seed: Random seed for reproducibility
        """
        self.detector = anomaly.HalfSpaceTrees(
            n_trees=n_trees,
            height=height,
            window_size=window_size,
            seed=seed
        )
        self.anomaly_count = 0
        self.total_samples = 0
        logger.info(f"Initialized Half-Space Trees detector with {n_trees} trees")
    
    def _tick_to_features(self, tick: TickData) -> Dict[str, float]:
        """
        Convert tick data to feature dictionary.
        
        Args:
            tick: Tick data
        
        Returns:
            Feature dictionary
        """
        return {
            'mid_price': tick.mid_price,
            'spread': tick.spread,
            'spread_bps': tick.spread_bps,
            'bid_size': tick.bid_size,
            'ask_size': tick.ask_size,
            'size_imbalance': (tick.bid_size - tick.ask_size) / (tick.bid_size + tick.ask_size + 1e-10)
        }
    
    def _metrics_to_features(self, metrics: MarketMetrics) -> Dict[str, float]:
        """
        Convert market metrics to feature dictionary.
        
        Args:
            metrics: Market metrics
        
        Returns:
            Feature dictionary
        """
        features = {
            'spread': metrics.bid_ask_spread,
            'spread_bps': metrics.spread_bps,
            'bid_depth': metrics.bid_depth,
            'ask_depth': metrics.ask_depth,
            'total_depth': metrics.total_depth,
            'flow_imbalance': metrics.order_flow_imbalance
        }
        
        if metrics.volatility is not None:
            features['volatility'] = metrics.volatility
        
        return features
    
    def score_tick(self, tick: TickData) -> float:
        """
        Score a tick for anomaly.
        
        Args:
            tick: Tick data
        
        Returns:
            Anomaly score (higher = more anomalous)
        """
        features = self._tick_to_features(tick)
        score = self.detector.score_one(features)
        self.detector.learn_one(features)
        
        self.total_samples += 1
        
        return score
    
    def score_metrics(self, metrics: MarketMetrics) -> float:
        """
        Score market metrics for anomaly.
        
        Args:
            metrics: Market metrics
        
        Returns:
            Anomaly score
        """
        features = self._metrics_to_features(metrics)
        score = self.detector.score_one(features)
        self.detector.learn_one(features)
        
        self.total_samples += 1
        
        return score
    
    def is_anomaly(self, score: float, threshold: float = 0.7) -> bool:
        """
        Determine if a score indicates an anomaly.
        
        Args:
            score: Anomaly score
            threshold: Threshold for anomaly detection
        
        Returns:
            True if anomaly detected
        """
        is_anom = score > threshold
        if is_anom:
            self.anomaly_count += 1
        return is_anom
    
    def get_statistics(self) -> Dict:
        """
        Get detector statistics.
        
        Returns:
            Dictionary of statistics
        """
        anomaly_rate = (self.anomaly_count / self.total_samples * 100) if self.total_samples > 0 else 0
        
        return {
            'total_samples': self.total_samples,
            'anomaly_count': self.anomaly_count,
            'anomaly_rate_pct': anomaly_rate
        }


class MultiFeatureAnomalyDetector:
    """Ensemble anomaly detector using multiple feature sets."""
    
    def __init__(self):
        """Initialize multiple detectors for different feature sets."""
        # Detector for price-based features
        self.price_detector = HalfSpaceTreeDetector(n_trees=10, height=8)
        
        # Detector for volume-based features
        self.volume_detector = HalfSpaceTreeDetector(n_trees=10, height=8)
        
        # Detector for combined features
        self.combined_detector = HalfSpaceTreeDetector(n_trees=15, height=10)
        
        logger.info("Initialized multi-feature anomaly detector")
    
    def detect_tick_anomaly(self, tick: TickData, threshold: float = 0.7) -> Dict:
        """
        Detect anomalies in tick data using multiple detectors.
        
        Args:
            tick: Tick data
            threshold: Anomaly threshold
        
        Returns:
            Dictionary with anomaly detection results
        """
        # Price features
        price_features = {
            'mid_price': tick.mid_price,
            'spread': tick.spread,
            'spread_bps': tick.spread_bps
        }
        price_score = self.price_detector.detector.score_one(price_features)
        self.price_detector.detector.learn_one(price_features)
        
        # Volume features
        volume_features = {
            'bid_size': tick.bid_size,
            'ask_size': tick.ask_size,
            'total_size': tick.bid_size + tick.ask_size,
            'size_imbalance': (tick.bid_size - tick.ask_size) / (tick.bid_size + tick.ask_size + 1e-10)
        }
        volume_score = self.volume_detector.detector.score_one(volume_features)
        self.volume_detector.detector.learn_one(volume_features)
        
        # Combined features
        combined_features = {**price_features, **volume_features}
        combined_score = self.combined_detector.detector.score_one(combined_features)
        self.combined_detector.detector.learn_one(combined_features)
        
        # Determine if anomaly
        is_price_anomaly = price_score > threshold
        is_volume_anomaly = volume_score > threshold
        is_combined_anomaly = combined_score > threshold
        
        # Overall anomaly if any detector flags it
        is_anomaly = is_price_anomaly or is_volume_anomaly or is_combined_anomaly
        
        # Determine anomaly type
        anomaly_type = None
        if is_price_anomaly and is_volume_anomaly:
            anomaly_type = "price_volume_anomaly"
        elif is_price_anomaly:
            anomaly_type = "price_anomaly"
        elif is_volume_anomaly:
            anomaly_type = "volume_anomaly"
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_type': anomaly_type,
            'price_score': price_score,
            'volume_score': volume_score,
            'combined_score': combined_score,
            'max_score': max(price_score, volume_score, combined_score)
        }
