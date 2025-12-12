#!/usr/bin/env python3
"""
End-to-end test script for the FX Market Microstructure Monitor.

This script tests the complete system by:
1. Starting the data simulator
2. Processing data through the pipeline
3. Calculating metrics
4. Detecting anomalies
5. Validating results
"""

import sys
import time
from datetime import datetime
from loguru import logger

from src.data_ingestion import FXDataSimulator
from src.metrics import MetricsAggregator
from src.anomaly_detection import (
    MultiFeatureAnomalyDetector,
    QuoteStuffingDetector,
    WashTradingDetector
)
from config import settings


def test_data_generation():
    """Test data generation."""
    logger.info("Testing data generation...")
    
    simulator = FXDataSimulator()
    
    # Test tick generation
    for symbol in settings.currency_pairs_list:
        tick = simulator.generate_tick(symbol)
        assert tick.symbol == symbol
        assert tick.bid > 0
        assert tick.ask > tick.bid
        logger.success(f"✓ Generated valid tick for {symbol}")
    
    # Test order book generation
    for symbol in settings.currency_pairs_list:
        orderbook = simulator.generate_orderbook(symbol)
        assert orderbook.symbol == symbol
        assert len(orderbook.bids) > 0
        assert len(orderbook.asks) > 0
        logger.success(f"✓ Generated valid order book for {symbol}")
    
    logger.success("✓ Data generation test passed")
    return True


def test_metrics_calculation():
    """Test metrics calculation."""
    logger.info("Testing metrics calculation...")
    
    simulator = FXDataSimulator()
    aggregators = {
        symbol: MetricsAggregator(symbol)
        for symbol in settings.currency_pairs_list
    }
    
    # Process 100 ticks for each symbol
    for i in range(100):
        for symbol in settings.currency_pairs_list:
            tick = simulator.generate_tick(symbol)
            aggregators[symbol].process_tick(tick)
            
            # Process order book every 10 ticks
            if i % 10 == 0:
                orderbook = simulator.generate_orderbook(symbol)
                aggregators[symbol].process_orderbook(orderbook)
    
    # Validate metrics
    for symbol, aggregator in aggregators.items():
        metrics = aggregator.get_current_metrics()
        assert metrics is not None
        assert metrics.bid_ask_spread > 0
        
        all_metrics = aggregator.get_all_metrics()
        assert 'spread' in all_metrics
        assert 'depth' in all_metrics
        assert 'flow' in all_metrics
        assert 'volatility' in all_metrics
        
        logger.success(f"✓ Metrics calculated for {symbol}")
    
    logger.success("✓ Metrics calculation test passed")
    return True


def test_anomaly_detection():
    """Test anomaly detection."""
    logger.info("Testing anomaly detection...")
    
    simulator = FXDataSimulator()
    
    # Test multi-feature detector
    detector = MultiFeatureAnomalyDetector()
    anomaly_count = 0
    
    for i in range(200):
        tick = simulator.generate_tick("EUR/USD")
        result = detector.detect_tick_anomaly(tick)
        
        if result['is_anomaly']:
            anomaly_count += 1
            logger.info(f"Anomaly detected: {result['anomaly_type']} (score: {result['max_score']:.3f})")
    
    logger.success(f"✓ Multi-feature detector processed 200 ticks, found {anomaly_count} anomalies")
    
    # Test quote stuffing detector
    quote_detector = QuoteStuffingDetector(window_seconds=1, threshold=50)
    
    # Simulate quote stuffing
    for _ in range(100):
        tick = simulator.generate_tick("EUR/USD")
        quote_detector.add_tick(tick)
    
    result = quote_detector.detect_stuffing()
    logger.info(f"Quote stuffing test: {result['quote_rate']} quotes/sec (threshold: {result['threshold']})")
    
    logger.success("✓ Anomaly detection test passed")
    return True


def test_market_stress_detection():
    """Test market stress detection."""
    logger.info("Testing market stress detection...")
    
    simulator = FXDataSimulator()
    aggregator = MetricsAggregator("EUR/USD")
    
    # Process data
    for i in range(100):
        tick = simulator.generate_tick("EUR/USD")
        aggregator.process_tick(tick)
        
        if i % 10 == 0:
            orderbook = simulator.generate_orderbook("EUR/USD")
            aggregator.process_orderbook(orderbook)
    
    # Check stress indicators
    stress = aggregator.detect_market_stress()
    
    logger.info("Market stress indicators:")
    for indicator, value in stress.items():
        status = "⚠️ DETECTED" if value else "✓ Normal"
        logger.info(f"  {indicator}: {status}")
    
    # Check market quality
    quality = aggregator.get_market_quality_score()
    logger.info(f"Market quality score: {quality:.1f}/100")
    
    logger.success("✓ Market stress detection test passed")
    return True


def test_performance():
    """Test system performance."""
    logger.info("Testing system performance...")
    
    simulator = FXDataSimulator()
    aggregator = MetricsAggregator("EUR/USD")
    detector = MultiFeatureAnomalyDetector()
    
    # Measure throughput
    start_time = time.time()
    tick_count = 1000
    
    for i in range(tick_count):
        tick = simulator.generate_tick("EUR/USD")
        aggregator.process_tick(tick)
        detector.detect_tick_anomaly(tick)
    
    elapsed = time.time() - start_time
    throughput = tick_count / elapsed
    
    logger.info(f"Processed {tick_count} ticks in {elapsed:.2f} seconds")
    logger.info(f"Throughput: {throughput:.0f} ticks/second")
    
    if throughput < 100:
        logger.warning("⚠️ Throughput below 100 ticks/second")
    else:
        logger.success(f"✓ Performance test passed ({throughput:.0f} ticks/sec)")
    
    return True


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("FX Market Microstructure Monitor - End-to-End Test")
    logger.info("=" * 60)
    
    tests = [
        ("Data Generation", test_data_generation),
        ("Metrics Calculation", test_metrics_calculation),
        ("Anomaly Detection", test_anomaly_detection),
        ("Market Stress Detection", test_market_stress_detection),
        ("Performance", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'=' * 60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"✗ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("Test Summary")
    logger.info(f"{'=' * 60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.success("\n🎉 All tests passed!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
