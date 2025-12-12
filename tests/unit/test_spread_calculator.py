"""Unit tests for spread calculator."""

import pytest
from datetime import datetime
from src.models import TickData
from src.metrics.spread_calculator import SpreadCalculator


@pytest.fixture
def sample_ticks():
    """Create sample tick data for testing."""
    ticks = []
    for i in range(10):
        tick = TickData(
            timestamp=datetime.now(),
            symbol="EUR/USD",
            bid=1.0850 + (i * 0.0001),
            ask=1.0852 + (i * 0.0001),
            bid_size=10.0,
            ask_size=10.0
        )
        ticks.append(tick)
    return ticks


def test_spread_calculator_initialization():
    """Test spread calculator initialization."""
    calc = SpreadCalculator(window_size=50)
    assert calc.window_size == 50
    assert len(calc.tick_history) == 0


def test_add_tick(sample_ticks):
    """Test adding ticks to calculator."""
    calc = SpreadCalculator()
    
    for tick in sample_ticks:
        calc.add_tick(tick)
    
    assert len(calc.tick_history) == len(sample_ticks)


def test_get_current_spread(sample_ticks):
    """Test getting current spread."""
    calc = SpreadCalculator()
    
    for tick in sample_ticks:
        calc.add_tick(tick)
    
    current_spread = calc.get_current_spread()
    assert current_spread is not None
    assert current_spread == 0.0002  # ask - bid


def test_get_average_spread(sample_ticks):
    """Test calculating average spread."""
    calc = SpreadCalculator()
    
    for tick in sample_ticks:
        calc.add_tick(tick)
    
    avg_spread = calc.get_average_spread()
    assert avg_spread is not None
    assert avg_spread == 0.0002


def test_spread_widening_detection(sample_ticks):
    """Test spread widening detection."""
    calc = SpreadCalculator()
    
    # Add normal ticks
    for tick in sample_ticks:
        calc.add_tick(tick)
    
    # Add tick with wide spread
    wide_tick = TickData(
        timestamp=datetime.now(),
        symbol="EUR/USD",
        bid=1.0850,
        ask=1.0860,  # Very wide spread
        bid_size=10.0,
        ask_size=10.0
    )
    calc.add_tick(wide_tick)
    
    is_widening = calc.detect_spread_widening(threshold_multiplier=2.0)
    assert is_widening is True


def test_spread_metrics(sample_ticks):
    """Test getting comprehensive spread metrics."""
    calc = SpreadCalculator()
    
    for tick in sample_ticks:
        calc.add_tick(tick)
    
    metrics = calc.get_spread_metrics()
    
    assert 'current_spread' in metrics
    assert 'average_spread' in metrics
    assert 'spread_volatility' in metrics
    assert metrics['current_spread'] is not None
