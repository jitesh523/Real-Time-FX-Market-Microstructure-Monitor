# API Reference

This document provides detailed API reference for the FX Market Microstructure Monitor.

## Data Models

### TickData

Represents a single price update in the FX market.

```python
from src.models import TickData

tick = TickData(
    timestamp=datetime.now(),
    symbol="EUR/USD",
    bid=1.0850,
    ask=1.0852,
    bid_size=10.0,
    ask_size=10.0
)
```

**Properties:**
- `mid_price`: Calculated mid price (bid + ask) / 2
- `spread`: Bid-ask spread
- `spread_bps`: Spread in basis points

### OrderBook

Represents the order book for a currency pair.

```python
from src.models import OrderBook, OrderBookLevel

orderbook = OrderBook(
    timestamp=datetime.now(),
    symbol="EUR/USD",
    bids=[OrderBookLevel(price=1.0850, size=10.0, orders=1)],
    asks=[OrderBookLevel(price=1.0852, size=10.0, orders=1)]
)
```

**Properties:**
- `bid_depth`: Total volume on bid side
- `ask_depth`: Total volume on ask side
- `total_depth`: Total volume on both sides
- `imbalance`: Order flow imbalance

## Metrics Calculators

### SpreadCalculator

Calculate various spread metrics.

```python
from src.metrics import SpreadCalculator

calc = SpreadCalculator(window_size=100)
calc.add_tick(tick)

# Get metrics
current_spread = calc.get_current_spread()
avg_spread = calc.get_average_spread()
is_widening = calc.detect_spread_widening()
```

**Methods:**
- `add_tick(tick)`: Add a tick to the calculator
- `get_current_spread()`: Get current spread
- `get_average_spread()`: Get average spread over window
- `get_spread_volatility()`: Get spread volatility
- `detect_spread_widening(threshold_multiplier)`: Detect abnormal spread widening

### DepthAnalyzer

Analyze order book depth and liquidity.

```python
from src.metrics import DepthAnalyzer

analyzer = DepthAnalyzer(max_levels=10)
analyzer.add_orderbook(orderbook)

# Get metrics
depth = analyzer.get_current_depth()
imbalance = analyzer.get_depth_imbalance()
liquidity_score = analyzer.get_liquidity_score()
```

**Methods:**
- `add_orderbook(orderbook)`: Add order book snapshot
- `get_current_depth()`: Get current bid/ask/total depth
- `get_depth_imbalance(num_levels)`: Calculate depth imbalance
- `get_price_impact(volume, side)`: Estimate price impact
- `get_liquidity_score(num_levels)`: Calculate liquidity score

### VolatilityAnalyzer

Analyze volatility and detect clustering.

```python
from src.metrics import VolatilityAnalyzer

analyzer = VolatilityAnalyzer(window_size=100)
analyzer.add_tick(tick)

# Get metrics
realized_vol = analyzer.get_realized_volatility()
is_clustering = analyzer.detect_volatility_clustering()
regime = analyzer.get_volatility_regime()
```

**Methods:**
- `add_tick(tick)`: Add a tick
- `get_realized_volatility(annualize)`: Calculate realized volatility
- `get_ewma_volatility(lambda_param)`: Calculate EWMA volatility
- `detect_volatility_clustering(threshold)`: Detect clustering
- `get_volatility_regime()`: Get current regime (low/normal/high)

## Anomaly Detectors

### HalfSpaceTreeDetector

Streaming anomaly detection using Half-Space Trees.

```python
from src.anomaly_detection import HalfSpaceTreeDetector

detector = HalfSpaceTreeDetector(n_trees=10, height=8)

# Score a tick
score = detector.score_tick(tick)
is_anomaly = detector.is_anomaly(score, threshold=0.7)
```

**Methods:**
- `score_tick(tick)`: Score a tick for anomaly
- `score_metrics(metrics)`: Score market metrics
- `is_anomaly(score, threshold)`: Determine if anomaly
- `get_statistics()`: Get detector statistics

### ZScoreDetector

Z-score based anomaly detection.

```python
from src.anomaly_detection import ZScoreDetector

detector = ZScoreDetector(window_size=100, threshold=3.0)

# Detect anomaly
result = detector.detect_and_update(value)
# result = {'value': ..., 'zscore': ..., 'is_anomaly': ...}
```

### QuoteStuffingDetector

Detect quote stuffing patterns.

```python
from src.anomaly_detection import QuoteStuffingDetector

detector = QuoteStuffingDetector(window_seconds=1, threshold=100)
detector.add_tick(tick)

result = detector.detect_stuffing()
# result = {'is_stuffing': ..., 'quote_rate': ..., ...}
```

### WashTradingDetector

Detect wash trading patterns.

```python
from src.anomaly_detection import WashTradingDetector

detector = WashTradingDetector(window_seconds=60)
detector.add_trade(trade)

result = detector.detect_wash_trading()
# result = {'is_wash_trading': ..., 'matched_pairs': ..., ...}
```

### SpoofingDetector

Detect spoofing (fake orders).

```python
from src.anomaly_detection import SpoofingDetector

detector = SpoofingDetector(depth_threshold=5, size_multiplier=3.0)
detector.add_orderbook(orderbook)

result = detector.detect_spoofing()
# result = {'is_spoofing': ..., 'large_orders_detected': ..., ...}
```

## Data Ingestion

### KafkaTickProducer

Produce simulated FX tick data to Kafka.

```python
from src.data_ingestion import KafkaTickProducer

producer = KafkaTickProducer()
producer.run_simulation(duration_seconds=3600)
```

### KafkaTickConsumer

Consume tick data from Kafka and store in ClickHouse.

```python
from src.data_ingestion import KafkaTickConsumer

consumer = KafkaTickConsumer()
consumer.run()
```

### ClickHouseClient

Interact with ClickHouse database.

```python
from src.data_ingestion import get_clickhouse_client

client = get_clickhouse_client()

# Initialize schema
client.initialize_schema()

# Insert data
client.insert_tick(tick)
client.insert_orderbook(orderbook)
client.insert_metrics(metrics)

# Query data
ticks = client.get_recent_ticks("EUR/USD", limit=100)
metrics = client.get_recent_metrics("EUR/USD", limit=100)
```

## Configuration

### Settings

Access configuration settings:

```python
from config import settings

# Kafka settings
bootstrap_servers = settings.kafka_bootstrap_servers
topic_ticks = settings.kafka_topic_ticks

# ClickHouse settings
ch_host = settings.clickhouse_host
ch_port = settings.clickhouse_port

# Application settings
currency_pairs = settings.currency_pairs_list
tick_interval = settings.tick_interval_ms

# Anomaly thresholds
zscore_threshold = settings.zscore_threshold
```

## Dashboard Components

### DataFetcher

Fetch data from ClickHouse for dashboard.

```python
from src.dashboard.utils import DataFetcher

fetcher = DataFetcher()

# Check connection
if fetcher.is_connected():
    # Fetch data
    ticks = fetcher.get_recent_ticks("EUR/USD", minutes=5)
    orderbook = fetcher.get_recent_orderbook("EUR/USD")
    metrics = fetcher.get_recent_metrics("EUR/USD", minutes=5)
```

## Examples

### Complete Pipeline Example

```python
from datetime import datetime
from src.models import TickData
from src.metrics import MetricsAggregator
from src.anomaly_detection import MultiFeatureAnomalyDetector

# Create aggregator
aggregator = MetricsAggregator("EUR/USD")

# Create anomaly detector
detector = MultiFeatureAnomalyDetector()

# Process tick
tick = TickData(
    timestamp=datetime.now(),
    symbol="EUR/USD",
    bid=1.0850,
    ask=1.0852,
    bid_size=10.0,
    ask_size=10.0
)

# Update metrics
aggregator.process_tick(tick)

# Get current metrics
metrics = aggregator.get_current_metrics()

# Detect anomalies
anomaly_result = detector.detect_tick_anomaly(tick)

if anomaly_result['is_anomaly']:
    print(f"Anomaly detected: {anomaly_result['anomaly_type']}")
    print(f"Score: {anomaly_result['max_score']}")
```
