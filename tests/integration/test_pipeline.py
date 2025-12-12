"""Integration tests for the complete data pipeline."""

import pytest
import time
from datetime import datetime
from src.models import TickData, OrderBook, OrderBookLevel
from src.data_ingestion import FXDataSimulator
from src.metrics import MetricsAggregator
from src.anomaly_detection import MultiFeatureAnomalyDetector


class TestDataPipeline:
    """Test the complete data pipeline."""
    
    def test_simulator_generates_valid_ticks(self):
        """Test that simulator generates valid tick data."""
        simulator = FXDataSimulator()
        
        tick = simulator.generate_tick("EUR/USD")
        
        assert tick.symbol == "EUR/USD"
        assert tick.bid > 0
        assert tick.ask > tick.bid
        assert tick.spread > 0
        assert tick.spread_bps > 0
    
    def test_simulator_generates_valid_orderbook(self):
        """Test that simulator generates valid order book."""
        simulator = FXDataSimulator()
        
        orderbook = simulator.generate_orderbook("EUR/USD", levels=5)
        
        assert orderbook.symbol == "EUR/USD"
        assert len(orderbook.bids) == 5
        assert len(orderbook.asks) == 5
        assert orderbook.bids[0].price > orderbook.bids[1].price  # Descending
        assert orderbook.asks[0].price < orderbook.asks[1].price  # Ascending
    
    def test_metrics_aggregator_processes_ticks(self):
        """Test metrics aggregator with tick data."""
        aggregator = MetricsAggregator("EUR/USD")
        simulator = FXDataSimulator()
        
        # Generate and process ticks
        for _ in range(20):
            tick = simulator.generate_tick("EUR/USD")
            aggregator.process_tick(tick)
        
        # Get metrics
        metrics = aggregator.get_current_metrics()
        
        assert metrics is not None
        assert metrics.symbol == "EUR/USD"
        assert metrics.bid_ask_spread > 0
    
    def test_metrics_aggregator_processes_orderbooks(self):
        """Test metrics aggregator with order book data."""
        aggregator = MetricsAggregator("EUR/USD")
        simulator = FXDataSimulator()
        
        # Generate and process order books
        for _ in range(10):
            orderbook = simulator.generate_orderbook("EUR/USD")
            aggregator.process_orderbook(orderbook)
        
        # Get detailed metrics
        all_metrics = aggregator.get_all_metrics()
        
        assert 'depth' in all_metrics
        assert 'flow' in all_metrics
    
    def test_anomaly_detection_integration(self):
        """Test anomaly detection with simulated data."""
        detector = MultiFeatureAnomalyDetector()
        simulator = FXDataSimulator()
        
        # Process normal ticks
        for _ in range(50):
            tick = simulator.generate_tick("EUR/USD")
            result = detector.detect_tick_anomaly(tick)
            
            # Should have detection results
            assert 'is_anomaly' in result
            assert 'price_score' in result
            assert 'volume_score' in result
    
    def test_end_to_end_pipeline(self):
        """Test complete pipeline from data generation to metrics."""
        # Initialize components
        simulator = FXDataSimulator()
        aggregator = MetricsAggregator("EUR/USD")
        detector = MultiFeatureAnomalyDetector()
        
        anomaly_count = 0
        
        # Simulate data flow
        for i in range(100):
            # Generate tick
            tick = simulator.generate_tick("EUR/USD")
            
            # Process through metrics
            aggregator.process_tick(tick)
            
            # Detect anomalies
            anomaly_result = detector.detect_tick_anomaly(tick)
            if anomaly_result['is_anomaly']:
                anomaly_count += 1
            
            # Every 10 ticks, generate order book
            if i % 10 == 0:
                orderbook = simulator.generate_orderbook("EUR/USD")
                aggregator.process_orderbook(orderbook)
        
        # Verify pipeline produced results
        metrics = aggregator.get_current_metrics()
        assert metrics is not None
        
        # Should have detected some metrics
        all_metrics = aggregator.get_all_metrics()
        assert all_metrics['spread']['current_spread'] is not None
        
        print(f"Pipeline processed 100 ticks, detected {anomaly_count} anomalies")


class TestMetricsCalculation:
    """Test metrics calculation accuracy."""
    
    def test_spread_calculation_accuracy(self):
        """Test spread calculation is accurate."""
        tick = TickData(
            timestamp=datetime.now(),
            symbol="EUR/USD",
            bid=1.0850,
            ask=1.0852,
            bid_size=10.0,
            ask_size=10.0
        )
        
        # Verify spread
        assert tick.spread == 0.0002
        
        # Verify mid price
        assert tick.mid_price == 1.0851
        
        # Verify spread in bps
        expected_bps = (0.0002 / 1.0851) * 10000
        assert abs(tick.spread_bps - expected_bps) < 0.01
    
    def test_orderbook_imbalance_calculation(self):
        """Test order book imbalance calculation."""
        orderbook = OrderBook(
            timestamp=datetime.now(),
            symbol="EUR/USD",
            bids=[
                OrderBookLevel(price=1.0850, size=20.0, orders=1),
                OrderBookLevel(price=1.0849, size=15.0, orders=1)
            ],
            asks=[
                OrderBookLevel(price=1.0852, size=10.0, orders=1),
                OrderBookLevel(price=1.0853, size=5.0, orders=1)
            ]
        )
        
        # Total bid depth = 35.0
        # Total ask depth = 15.0
        # Imbalance = (35 - 15) / (35 + 15) = 20 / 50 = 0.4
        
        assert orderbook.bid_depth == 35.0
        assert orderbook.ask_depth == 15.0
        assert orderbook.total_depth == 50.0
        assert abs(orderbook.imbalance - 0.4) < 0.001


class TestAnomalyDetection:
    """Test anomaly detection accuracy."""
    
    def test_zscore_detects_outliers(self):
        """Test Z-score detector identifies outliers."""
        from src.anomaly_detection import ZScoreDetector
        
        detector = ZScoreDetector(window_size=20, threshold=2.0)
        
        # Add normal values
        for i in range(20):
            detector.add_value(10.0)
        
        # Add outlier
        result = detector.detect_and_update(50.0)
        
        assert result['is_anomaly'] is True
        assert abs(result['zscore']) > 2.0
    
    def test_quote_stuffing_detection(self):
        """Test quote stuffing detector."""
        from src.anomaly_detection import QuoteStuffingDetector
        
        detector = QuoteStuffingDetector(window_seconds=1, threshold=10)
        
        # Add many ticks rapidly
        for _ in range(15):
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
        assert result['quote_rate'] > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
