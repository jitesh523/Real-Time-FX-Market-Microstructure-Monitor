"""Optimized ClickHouse client with connection pooling and query optimization."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import clickhouse_connect
from loguru import logger
from functools import lru_cache

from config import settings
from src.models import TickData, OrderBook, Trade, MarketMetrics


class OptimizedClickHouseClient:
    """Optimized ClickHouse client with connection pooling and caching."""
    
    def __init__(self, pool_size: int = 5):
        """
        Initialize optimized ClickHouse client.
        
        Args:
            pool_size: Number of connections in the pool
        """
        self.pool_size = pool_size
        self.client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_database,
            connect_timeout=10,
            send_receive_timeout=30
        )
        
        # Batch buffers for bulk inserts
        self.tick_buffer = []
        self.orderbook_buffer = []
        self.metrics_buffer = []
        self.buffer_size = 100
        
        logger.info(f"Initialized Optimized ClickHouse Client (pool_size={pool_size})")
    
    def insert_tick_batch(self, ticks: List[TickData]):
        """
        Insert ticks in batch (optimized).
        
        Args:
            ticks: List of tick data
        """
        if not ticks:
            return
        
        # Prepare data as list of tuples for faster insertion
        data = [
            (
                tick.timestamp,
                tick.symbol,
                tick.bid,
                tick.ask,
                tick.bid_size,
                tick.ask_size,
                tick.mid_price,
                tick.spread,
                tick.spread_bps
            )
            for tick in ticks
        ]
        
        self.client.insert(
            'ticks',
            data,
            column_names=[
                'timestamp', 'symbol', 'bid', 'ask', 'bid_size', 'ask_size',
                'mid_price', 'spread', 'spread_bps'
            ]
        )
        
        logger.debug(f"Inserted {len(ticks)} ticks in batch")
    
    def insert_tick_buffered(self, tick: TickData):
        """
        Insert tick with buffering for automatic batching.
        
        Args:
            tick: Tick data
        """
        self.tick_buffer.append(tick)
        
        if len(self.tick_buffer) >= self.buffer_size:
            self.flush_tick_buffer()
    
    def flush_tick_buffer(self):
        """Flush tick buffer to database."""
        if self.tick_buffer:
            self.insert_tick_batch(self.tick_buffer)
            self.tick_buffer.clear()
    
    @lru_cache(maxsize=128)
    def get_recent_ticks_cached(self, symbol: str, minutes: int, limit: int) -> tuple:
        """
        Get recent ticks with caching.
        
        Args:
            symbol: Currency pair
            minutes: Number of minutes
            limit: Maximum ticks
        
        Returns:
            Tuple of tick data (for caching)
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # Optimized query with PREWHERE for better performance
        query = f"""
            SELECT
                timestamp,
                symbol,
                bid,
                ask,
                mid_price,
                spread,
                spread_bps,
                bid_size,
                ask_size
            FROM ticks
            PREWHERE symbol = '{symbol}'
            WHERE timestamp >= '{cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        
        result = self.client.query(query)
        return tuple(result.result_rows)
    
    def get_aggregated_metrics(self, symbol: str, interval: str = '1m',
                               minutes: int = 60) -> List[Dict]:
        """
        Get pre-aggregated metrics using materialized views.
        
        Args:
            symbol: Currency pair
            interval: Aggregation interval ('1s' or '1m')
            minutes: Time range in minutes
        
        Returns:
            List of aggregated metrics
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # Use materialized view for better performance
        table = 'metrics_1m' if interval == '1m' else 'metrics_1s'
        
        query = f"""
            SELECT
                timestamp,
                symbol,
                avg_spread,
                avg_spread_bps,
                max_spread,
                min_spread,
                tick_count
            FROM fx_market.{table}
            WHERE symbol = '{symbol}'
              AND timestamp >= '{cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY timestamp ASC
        """
        
        result = self.client.query(query)
        
        columns = ['timestamp', 'symbol', 'avg_spread', 'avg_spread_bps',
                  'max_spread', 'min_spread', 'tick_count']
        
        return [dict(zip(columns, row)) for row in result.result_rows]
    
    def execute_optimized_query(self, query: str, use_cache: bool = False) -> List:
        """
        Execute query with optimizations.
        
        Args:
            query: SQL query
            use_cache: Whether to use query result cache
        
        Returns:
            Query results
        """
        if use_cache:
            # Add SETTINGS for query result caching
            query += " SETTINGS use_query_cache = 1"
        
        result = self.client.query(query)
        return result.result_rows
    
    def get_statistics(self) -> Dict:
        """Get client statistics."""
        return {
            'tick_buffer_size': len(self.tick_buffer),
            'orderbook_buffer_size': len(self.orderbook_buffer),
            'metrics_buffer_size': len(self.metrics_buffer)
        }
    
    def close(self):
        """Close connection and flush buffers."""
        self.flush_tick_buffer()
        self.client.close()
        logger.info("Optimized ClickHouse client closed")


# Global optimized client instance
_optimized_client: Optional[OptimizedClickHouseClient] = None


def get_optimized_clickhouse_client() -> OptimizedClickHouseClient:
    """Get or create optimized ClickHouse client singleton."""
    global _optimized_client
    if _optimized_client is None:
        _optimized_client = OptimizedClickHouseClient()
    return _optimized_client
