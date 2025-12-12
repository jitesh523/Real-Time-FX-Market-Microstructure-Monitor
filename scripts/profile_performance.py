#!/usr/bin/env python3
"""
Performance profiling script for the FX Market Microstructure Monitor.

Profiles key components and identifies bottlenecks.
"""

import cProfile
import pstats
import io
import time
from datetime import datetime
from loguru import logger

from src.data_ingestion import FXDataSimulator
from src.metrics import MetricsAggregator
from src.anomaly_detection import MultiFeatureAnomalyDetector


def profile_data_generation(num_ticks: int = 1000):
    """Profile data generation."""
    logger.info(f"Profiling data generation ({num_ticks} ticks)...")
    
    simulator = FXDataSimulator()
    
    start_time = time.time()
    
    for _ in range(num_ticks):
        tick = simulator.generate_tick("EUR/USD")
    
    elapsed = time.time() - start_time
    throughput = num_ticks / elapsed
    
    logger.info(f"Data generation: {throughput:.0f} ticks/sec")
    
    return throughput


def profile_metrics_calculation(num_ticks: int = 1000):
    """Profile metrics calculation."""
    logger.info(f"Profiling metrics calculation ({num_ticks} ticks)...")
    
    simulator = FXDataSimulator()
    aggregator = MetricsAggregator("EUR/USD")
    
    # Generate ticks
    ticks = [simulator.generate_tick("EUR/USD") for _ in range(num_ticks)]
    
    start_time = time.time()
    
    for tick in ticks:
        aggregator.process_tick(tick)
    
    elapsed = time.time() - start_time
    throughput = num_ticks / elapsed
    
    logger.info(f"Metrics calculation: {throughput:.0f} ticks/sec")
    
    return throughput


def profile_anomaly_detection(num_ticks: int = 1000):
    """Profile anomaly detection."""
    logger.info(f"Profiling anomaly detection ({num_ticks} ticks)...")
    
    simulator = FXDataSimulator()
    detector = MultiFeatureAnomalyDetector()
    
    # Generate ticks
    ticks = [simulator.generate_tick("EUR/USD") for _ in range(num_ticks)]
    
    start_time = time.time()
    
    for tick in ticks:
        detector.detect_tick_anomaly(tick)
    
    elapsed = time.time() - start_time
    throughput = num_ticks / elapsed
    
    logger.info(f"Anomaly detection: {throughput:.0f} ticks/sec")
    
    return throughput


def profile_end_to_end(num_ticks: int = 1000):
    """Profile complete pipeline."""
    logger.info(f"Profiling end-to-end pipeline ({num_ticks} ticks)...")
    
    simulator = FXDataSimulator()
    aggregator = MetricsAggregator("EUR/USD")
    detector = MultiFeatureAnomalyDetector()
    
    start_time = time.time()
    
    for _ in range(num_ticks):
        # Generate
        tick = simulator.generate_tick("EUR/USD")
        
        # Process metrics
        aggregator.process_tick(tick)
        
        # Detect anomalies
        detector.detect_tick_anomaly(tick)
    
    elapsed = time.time() - start_time
    throughput = num_ticks / elapsed
    
    logger.info(f"End-to-end pipeline: {throughput:.0f} ticks/sec")
    
    return throughput


def detailed_profile():
    """Run detailed profiling with cProfile."""
    logger.info("Running detailed profiling...")
    
    profiler = cProfile.Profile()
    
    simulator = FXDataSimulator()
    aggregator = MetricsAggregator("EUR/USD")
    detector = MultiFeatureAnomalyDetector()
    
    # Profile the pipeline
    profiler.enable()
    
    for _ in range(1000):
        tick = simulator.generate_tick("EUR/USD")
        aggregator.process_tick(tick)
        detector.detect_tick_anomaly(tick)
    
    profiler.disable()
    
    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    logger.info("\nTop 20 functions by cumulative time:")
    print(s.getvalue())


def main():
    """Run all profiling tests."""
    logger.info("=" * 60)
    logger.info("Performance Profiling")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    results = {}
    
    # Run profiling tests
    results['data_generation'] = profile_data_generation(1000)
    results['metrics_calculation'] = profile_metrics_calculation(1000)
    results['anomaly_detection'] = profile_anomaly_detection(1000)
    results['end_to_end'] = profile_end_to_end(1000)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Performance Summary")
    logger.info("=" * 60)
    
    for component, throughput in results.items():
        logger.info(f"{component:25s}: {throughput:8.0f} ticks/sec")
    
    # Detailed profiling
    logger.info("\n" + "=" * 60)
    detailed_profile()
    
    # Recommendations
    logger.info("\n" + "=" * 60)
    logger.info("Recommendations")
    logger.info("=" * 60)
    
    if results['end_to_end'] < 100:
        logger.warning("⚠️ End-to-end throughput below 100 ticks/sec")
        logger.info("  - Consider optimizing metrics calculations")
        logger.info("  - Use batch processing where possible")
        logger.info("  - Implement caching for repeated calculations")
    else:
        logger.success(f"✓ Good performance: {results['end_to_end']:.0f} ticks/sec")


if __name__ == "__main__":
    main()
