"""Regression coverage for unchanged-price Lee-Ready classifications."""

from datetime import datetime

import pytest

from src.metrics.trade_classification import LeeReadyClassifier
from src.models import TickData, Trade


def classify(classifier, price, midpoint):
    timestamp = datetime(2026, 11, 1)
    trade = Trade(
        timestamp=timestamp,
        symbol="EUR/USD",
        price=price,
        size=1.0,
        side="buy",
    )
    tick = TickData(
        timestamp=timestamp,
        symbol="EUR/USD",
        bid=midpoint - 1,
        ask=midpoint + 1,
    )
    return classifier.classify_trade(trade, tick)


@pytest.mark.parametrize("side, price", [("sell", 99.0), ("buy", 101.0)])
def test_zero_ticks_retain_quote_rule_classification(side, price):
    classifier = LeeReadyClassifier()
    initial = classify(classifier, price, 100.0)
    assert initial["classification"] == side
    assert initial["method"] == "quote_rule"

    for _ in range(3):
        result = classify(classifier, price, price)
        assert result["classification"] == side
        assert result["method"] == "tick_test"

    stats = classifier.get_statistics()
    assert stats[f"{side}_initiated_count"] == 4
    assert stats["total_classified"] == 4
    assert classifier.get_order_flow_imbalance() == (-1.0 if side == "sell" else 1.0)


@pytest.mark.parametrize("side, price", [("sell", 99.0), ("buy", 101.0)])
def test_zero_ticks_retain_nonzero_tick_direction(side, price):
    classifier = LeeReadyClassifier()
    classify(classifier, 100.0, 100.0)
    assert classify(classifier, price, price)["classification"] == side
    assert classify(classifier, price, price)["classification"] == side


@pytest.mark.parametrize(
    "initial_price, next_midpoint, expected",
    [(99.0, 98.0, "buy"), (101.0, 102.0, "sell")],
)
def test_quote_rule_can_change_direction_before_zero_tick(
    initial_price, next_midpoint, expected
):
    classifier = LeeReadyClassifier()
    classify(classifier, initial_price, 100.0)
    changed = classify(classifier, initial_price, next_midpoint)
    assert changed["classification"] == expected
    assert changed["method"] == "quote_rule"
    assert (
        classify(classifier, initial_price, initial_price)["classification"] == expected
    )


def test_first_midpoint_trade_keeps_default_buy_classification():
    classifier = LeeReadyClassifier()
    for _ in range(3):
        assert classify(classifier, 100.0, 100.0)["classification"] == "buy"
    assert classifier.get_statistics()["buy_initiated_count"] == 3


def test_mixed_sequence_counts_each_trade_once():
    classifier = LeeReadyClassifier()
    observed = [
        classify(classifier, price, midpoint)["classification"]
        for price, midpoint in [
            (99.0, 100.0),
            (99.0, 99.0),
            (99.0, 99.0),
            (100.0, 100.0),
            (100.0, 100.0),
        ]
    ]
    assert observed == ["sell", "sell", "sell", "buy", "buy"]
    stats = classifier.get_statistics()
    assert stats["buy_initiated_count"] == 2
    assert stats["sell_initiated_count"] == 3
    assert stats["total_classified"] == 5
    assert stats["buy_ratio"] == pytest.approx(0.4)
    assert classifier.get_order_flow_imbalance() == pytest.approx(-0.2)


def test_classification_history_is_per_instance():
    seller = LeeReadyClassifier()
    classify(seller, 99.0, 100.0)
    fresh = LeeReadyClassifier()
    assert classify(fresh, 99.0, 99.0)["classification"] == "buy"
    assert classify(seller, 99.0, 99.0)["classification"] == "sell"
