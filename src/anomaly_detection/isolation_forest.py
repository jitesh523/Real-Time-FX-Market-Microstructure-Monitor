"""Isolation Forest anomaly detector for batch anomaly detection."""

from typing import List, Dict, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
from loguru import logger

from src.models import TickData, MarketMetrics


class IsolationForestDetector:
    """Anomaly detection using Isolation Forest algorithm."""
    
    def __init__(self, contamination: float = 0.1, n_estimators: int = 100,
                 window_size: int = 1000):
        """
        Initialize Isolation Forest detector.
        
        Args:
            contamination: Expected proportion of outliers (0.0 to 0.5)
            n_estimators: Number of trees in the forest
            window_size: Number of samples to keep for retraining
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.window_size = window_size
        
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42,
            n_jobs=-1
        )
        
        self.feature_buffer = []
        self.is_fitted = False
        self.anomaly_count = 0
        
        logger.info(f"Initialized Isolation Forest with contamination={contamination}")
    
    def _tick_to_features(self, tick: TickData) -> np.ndarray:
        """Convert tick to feature vector."""
        return np.array([
            tick.mid_price,
            tick.spread,
            tick.spread_bps,
            tick.bid_size,
            tick.ask_size,
            tick.bid_size + tick.ask_size,  # total size
            (tick.bid_size - tick.ask_size) / (tick.bid_size + tick.ask_size + 1e-10)  # imbalance
        ])
    
    def _metrics_to_features(self, metrics: MarketMetrics) -> np.ndarray:
        """Convert metrics to feature vector."""
        features = [
            metrics.bid_ask_spread,
            metrics.spread_bps,
            metrics.bid_depth,
            metrics.ask_depth,
            metrics.total_depth,
            metrics.order_flow_imbalance
        ]
        
        if metrics.volatility is not None:
            features.append(metrics.volatility)
        else:
            features.append(0.0)
        
        return np.array(features)
    
    def add_tick(self, tick: TickData):
        """Add tick to feature buffer."""
        features = self._tick_to_features(tick)
        self.feature_buffer.append(features)
        
        # Keep buffer size limited
        if len(self.feature_buffer) > self.window_size:
            self.feature_buffer.pop(0)
        
        # Retrain if we have enough samples
        if len(self.feature_buffer) >= 100 and len(self.feature_buffer) % 100 == 0:
            self._retrain()
    
    def add_metrics(self, metrics: MarketMetrics):
        """Add metrics to feature buffer."""
        features = self._metrics_to_features(metrics)
        self.feature_buffer.append(features)
        
        if len(self.feature_buffer) > self.window_size:
            self.feature_buffer.pop(0)
        
        if len(self.feature_buffer) >= 100 and len(self.feature_buffer) % 100 == 0:
            self._retrain()
    
    def _retrain(self):
        """Retrain the model with buffered data."""
        if len(self.feature_buffer) < 50:
            return
        
        X = np.array(self.feature_buffer)
        self.model.fit(X)
        self.is_fitted = True
        logger.debug(f"Retrained Isolation Forest with {len(self.feature_buffer)} samples")
    
    def predict_tick(self, tick: TickData) -> Dict:
        """
        Predict if tick is anomalous.
        
        Returns:
            Dictionary with prediction results
        """
        if not self.is_fitted:
            # Not enough data yet
            self.add_tick(tick)
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'reason': 'Model not yet fitted'
            }
        
        features = self._tick_to_features(tick).reshape(1, -1)
        
        # Predict (-1 for anomaly, 1 for normal)
        prediction = self.model.predict(features)[0]
        
        # Get anomaly score (lower = more anomalous)
        score = self.model.score_samples(features)[0]
        
        is_anomaly = prediction == -1
        
        if is_anomaly:
            self.anomaly_count += 1
        
        # Add to buffer for future retraining
        self.add_tick(tick)
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': abs(score),  # Convert to positive score
            'reason': 'Isolation Forest detection' if is_anomaly else None
        }
    
    def predict_metrics(self, metrics: MarketMetrics) -> Dict:
        """
        Predict if metrics are anomalous.
        
        Returns:
            Dictionary with prediction results
        """
        if not self.is_fitted:
            self.add_metrics(metrics)
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'reason': 'Model not yet fitted'
            }
        
        features = self._metrics_to_features(metrics).reshape(1, -1)
        
        prediction = self.model.predict(features)[0]
        score = self.model.score_samples(features)[0]
        
        is_anomaly = prediction == -1
        
        if is_anomaly:
            self.anomaly_count += 1
        
        self.add_metrics(metrics)
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': abs(score),
            'reason': 'Isolation Forest detection' if is_anomaly else None
        }
    
    def get_statistics(self) -> Dict:
        """Get detector statistics."""
        return {
            'is_fitted': self.is_fitted,
            'buffer_size': len(self.feature_buffer),
            'anomaly_count': self.anomaly_count,
            'contamination': self.contamination
        }


class AdaptiveIsolationForest:
    """Adaptive Isolation Forest with automatic contamination adjustment."""
    
    def __init__(self, initial_contamination: float = 0.1):
        """Initialize adaptive detector."""
        self.contamination = initial_contamination
        self.detector = IsolationForestDetector(contamination=initial_contamination)
        self.recent_anomaly_rate = []
        
        logger.info("Initialized Adaptive Isolation Forest")
    
    def predict_tick(self, tick: TickData) -> Dict:
        """Predict with adaptive contamination."""
        result = self.detector.predict_tick(tick)
        
        # Track anomaly rate
        self.recent_anomaly_rate.append(1 if result['is_anomaly'] else 0)
        
        # Keep last 100 predictions
        if len(self.recent_anomaly_rate) > 100:
            self.recent_anomaly_rate.pop(0)
        
        # Adjust contamination if needed
        if len(self.recent_anomaly_rate) >= 100:
            current_rate = np.mean(self.recent_anomaly_rate)
            
            # If anomaly rate deviates significantly from contamination, adjust
            if abs(current_rate - self.contamination) > 0.05:
                new_contamination = np.clip(current_rate, 0.01, 0.5)
                logger.info(f"Adjusting contamination: {self.contamination:.3f} -> {new_contamination:.3f}")
                
                self.contamination = new_contamination
                self.detector = IsolationForestDetector(
                    contamination=new_contamination,
                    n_estimators=self.detector.n_estimators,
                    window_size=self.detector.window_size
                )
                # Transfer buffer
                self.detector.feature_buffer = self.detector.feature_buffer.copy()
        
        return result
