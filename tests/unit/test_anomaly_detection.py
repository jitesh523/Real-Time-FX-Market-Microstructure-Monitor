"""Unit tests for anomaly detectors."""

import pytest
from datetime import datetime
from src.models import TickData
from src.anomaly_detection.zscore_detector import ZScoreDetector, MultiVariateZScoreDetector
from src.anomaly_detection.quote_stuffing import QuoteStuffingDetector


def test_zscore_detector_initialization():
    """Test Z-score detector initialization."""
    detector = ZScoreDetector(window_size=100, threshold=3.0)
    assert detector.window_size == 100
    assert detector.threshold == 3.0
    assert len(detector.values) == 0


def test_zscore_detection():
    """Test Z-score anomaly detection."""
    detector = ZScoreDetector(window_size=10, threshold=2.0)
    
    # Add normal values
    for i in range(10):
        detector.add_value(10.0 + i * 0.1)
    
    # Add anomalous value
    result = detector.detect_and_update(50.0)
    
    assert result['is_anomaly'] is True
    assert result['zscore'] is not None


def test_multivariate_zscore_detector():
    """Test multi-variate Z-score detector."""
    detector = MultiVariateZScoreDetector(window_size=10, threshold=2.0)
    
    # Create sample ticks
    for i in range(15):
        tick = TickData(
            timestamp=datetime.now(),
            symbol="EUR/USD",
            bid=1.0850,
            ask=1.0852,
            bid_size=10.0,
            ask_size=10.0
        )
        result = detector.detect_tick_anomaly(tick)
        
        if i < 10:
            # Should not detect anomaly in first 10 ticks
            assert result['is_anomaly'] is False


def test_quote_stuffing_detector():
    """Test quote stuffing detector."""
    detector = QuoteStuffingDetector(window_seconds=1, threshold=5)
    
    # Add a few ticks
    for i in range(3):
        tick = TickData(
            timestamp=datetime.now(),
            symbol="EUR/USD",
            bid=1.0850,
            ask=1.0852,
            bid_size=10.0,
            ask_size=10.0
        )
        detector.add_tick(tick)
    
    result = detector.detect_stuffing()
    assert result['is_stuffing'] is False
    
    # Add many ticks to trigger stuffing
    for i in range(10):
        tick = TickData(
            timestamp=datetime.now(),
            symbol="EUR/USD",
            bid=1.0850,
            ask=1.0852,
            bid_size=10.0,
            ask_size=10.0
        )
        detector.add_tick(tick)
    
    result = detector.detect_stuffing()
    assert result['is_stuffing'] is True
