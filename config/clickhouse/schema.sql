-- ClickHouse schema for FX Market Microstructure Monitor

-- Create database
CREATE DATABASE IF NOT EXISTS fx_market;

-- Tick data table
CREATE TABLE IF NOT EXISTS fx_market.ticks
(
    timestamp DateTime64(3),
    symbol String,
    bid Float64,
    ask Float64,
    bid_size Float64,
    ask_size Float64,
    mid_price Float64,
    spread Float64,
    spread_bps Float64
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
SETTINGS index_granularity = 8192;

-- Order book table
CREATE TABLE IF NOT EXISTS fx_market.orderbook
(
    timestamp DateTime64(3),
    symbol String,
    side Enum8('bid' = 1, 'ask' = 2),
    price Float64,
    size Float64,
    orders UInt32,
    level UInt8
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp, side, level)
SETTINGS index_granularity = 8192;

-- Trades table
CREATE TABLE IF NOT EXISTS fx_market.trades
(
    timestamp DateTime64(3),
    symbol String,
    price Float64,
    size Float64,
    side Enum8('buy' = 1, 'sell' = 2),
    trade_id String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
SETTINGS index_granularity = 8192;

-- Market metrics table
CREATE TABLE IF NOT EXISTS fx_market.metrics
(
    timestamp DateTime64(3),
    symbol String,
    bid_ask_spread Float64,
    spread_bps Float64,
    bid_depth Float64,
    ask_depth Float64,
    total_depth Float64,
    order_flow_imbalance Float64,
    volatility Nullable(Float64),
    is_anomaly UInt8,
    anomaly_type Nullable(String),
    anomaly_score Nullable(Float64)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
SETTINGS index_granularity = 8192;

-- Materialized view for 1-second aggregated metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS fx_market.metrics_1s
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
AS SELECT
    toStartOfSecond(timestamp) as timestamp,
    symbol,
    avg(spread) as avg_spread,
    avg(spread_bps) as avg_spread_bps,
    max(spread) as max_spread,
    min(spread) as min_spread,
    count() as tick_count
FROM fx_market.ticks
GROUP BY symbol, toStartOfSecond(timestamp);

-- Materialized view for 1-minute aggregated metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS fx_market.metrics_1m
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
AS SELECT
    toStartOfMinute(timestamp) as timestamp,
    symbol,
    avg(spread) as avg_spread,
    avg(spread_bps) as avg_spread_bps,
    max(spread) as max_spread,
    min(spread) as min_spread,
    stddevPop(mid_price) as price_volatility,
    count() as tick_count
FROM fx_market.ticks
GROUP BY symbol, toStartOfMinute(timestamp);
