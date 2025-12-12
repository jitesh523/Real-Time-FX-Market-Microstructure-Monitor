"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime

from src.models import TickData, OrderBook, OrderBookLevel, Trade
from src.data_ingestion import FXDataSimulator


@pytest.fixture
def sample_tick():
    """Create a sample tick."""
    return TickData(
        timestamp=datetime.now(),
        symbol="EUR/USD",
        bid=1.0850,
        ask=1.0852,
        bid_size=10.0,
        ask_size=10.0
    )


@pytest.fixture
def sample_orderbook():
    """Create a sample order book."""
    return OrderBook(
        timestamp=datetime.now(),
        symbol="EUR/USD",
        bids=[
            OrderBookLevel(price=1.0850, size=10.0, orders=1),
            OrderBookLevel(price=1.0849, size=15.0, orders=2)
        ],
        asks=[
            OrderBookLevel(price=1.0852, size=10.0, orders=1),
            OrderBookLevel(price=1.0853, size=12.0, orders=1)
        ]
    )


@pytest.fixture
def sample_trade():
    """Create a sample trade."""
    return Trade(
        timestamp=datetime.now(),
        symbol="EUR/USD",
        trade_id="12345",
        price=1.0851,
        size=5.0,
        side="buy"
    )


@pytest.fixture
def fx_simulator():
    """Create FX data simulator."""
    return FXDataSimulator()


@pytest.fixture
def sample_ticks(fx_simulator):
    """Generate sample ticks."""
    return [fx_simulator.generate_tick("EUR/USD") for _ in range(100)]
