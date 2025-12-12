"""ClickHouse database client and operations."""

from datetime import datetime
from typing import List, Optional
import clickhouse_connect
from loguru import logger

from config import settings
from src.models import TickData, OrderBook, Trade, MarketMetrics


class ClickHouseClient:
    """Client for interacting with ClickHouse database."""
    
    def __init__(self):
        """Initialize ClickHouse client."""
        self.client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_database
        )
        logger.info(f"Connected to ClickHouse at {settings.clickhouse_host}:{settings.clickhouse_port}")
    
    def initialize_schema(self, schema_file: str = "config/clickhouse/schema.sql"):
        """Initialize database schema from SQL file."""
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Execute each statement separately
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            for statement in statements:
                self.client.command(statement)
            
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            raise
    
    def insert_tick(self, tick: TickData):
        """Insert a single tick into the database."""
        self.client.insert(
            'ticks',
            [[
                tick.timestamp,
                tick.symbol,
                tick.bid,
                tick.ask,
                tick.bid_size,
                tick.ask_size,
                tick.mid_price,
                tick.spread,
                tick.spread_bps
            ]],
            column_names=[
                'timestamp', 'symbol', 'bid', 'ask', 'bid_size', 'ask_size',
                'mid_price', 'spread', 'spread_bps'
            ]
        )
    
    def insert_ticks_batch(self, ticks: List[TickData]):
        """Insert multiple ticks in a batch."""
        if not ticks:
            return
        
        data = [
            [
                tick.timestamp,
                tick.symbol,
                tick.bid,
                tick.ask,
                tick.bid_size,
                tick.ask_size,
                tick.mid_price,
                tick.spread,
                tick.spread_bps
            ]
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
        logger.debug(f"Inserted {len(ticks)} ticks")
    
    def insert_orderbook(self, orderbook: OrderBook):
        """Insert order book snapshot into the database."""
        data = []
        
        # Insert bid levels
        for i, level in enumerate(orderbook.bids):
            data.append([
                orderbook.timestamp,
                orderbook.symbol,
                'bid',
                level.price,
                level.size,
                level.orders,
                i
            ])
        
        # Insert ask levels
        for i, level in enumerate(orderbook.asks):
            data.append([
                orderbook.timestamp,
                orderbook.symbol,
                'ask',
                level.price,
                level.size,
                level.orders,
                i
            ])
        
        if data:
            self.client.insert(
                'orderbook',
                data,
                column_names=['timestamp', 'symbol', 'side', 'price', 'size', 'orders', 'level']
            )
    
    def insert_trade(self, trade: Trade):
        """Insert a trade into the database."""
        self.client.insert(
            'trades',
            [[
                trade.timestamp,
                trade.symbol,
                trade.price,
                trade.size,
                trade.side,
                trade.trade_id or ''
            ]],
            column_names=['timestamp', 'symbol', 'price', 'size', 'side', 'trade_id']
        )
    
    def insert_metrics(self, metrics: MarketMetrics):
        """Insert market metrics into the database."""
        self.client.insert(
            'metrics',
            [[
                metrics.timestamp,
                metrics.symbol,
                metrics.bid_ask_spread,
                metrics.spread_bps,
                metrics.bid_depth,
                metrics.ask_depth,
                metrics.total_depth,
                metrics.order_flow_imbalance,
                metrics.volatility,
                1 if metrics.is_anomaly else 0,
                metrics.anomaly_type,
                metrics.anomaly_score
            ]],
            column_names=[
                'timestamp', 'symbol', 'bid_ask_spread', 'spread_bps',
                'bid_depth', 'ask_depth', 'total_depth', 'order_flow_imbalance',
                'volatility', 'is_anomaly', 'anomaly_type', 'anomaly_score'
            ]
        )
    
    def get_recent_ticks(self, symbol: str, limit: int = 100) -> List[dict]:
        """Get recent ticks for a symbol."""
        query = f"""
            SELECT *
            FROM ticks
            WHERE symbol = '{symbol}'
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        result = self.client.query(query)
        return result.result_rows
    
    def get_recent_metrics(self, symbol: str, limit: int = 100) -> List[dict]:
        """Get recent metrics for a symbol."""
        query = f"""
            SELECT *
            FROM metrics
            WHERE symbol = '{symbol}'
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        result = self.client.query(query)
        return result.result_rows
    
    def close(self):
        """Close the database connection."""
        self.client.close()
        logger.info("ClickHouse connection closed")


# Global client instance
_client: Optional[ClickHouseClient] = None


def get_clickhouse_client() -> ClickHouseClient:
    """Get or create ClickHouse client singleton."""
    global _client
    if _client is None:
        _client = ClickHouseClient()
    return _client
