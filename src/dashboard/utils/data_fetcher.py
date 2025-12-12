"""Data fetcher utility for dashboard."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.data_ingestion.clickhouse_writer import get_clickhouse_client


class DataFetcher:
    """Fetch data from ClickHouse for dashboard."""
    
    def __init__(self):
        """Initialize data fetcher."""
        try:
            self.client = get_clickhouse_client()
            self.connected = True
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self.connected
    
    def get_recent_ticks(self, symbol: str, minutes: int = 5, limit: int = 1000) -> List[Dict]:
        """
        Get recent ticks for a symbol.
        
        Args:
            symbol: Currency pair
            minutes: Number of minutes of history
            limit: Maximum number of ticks
        
        Returns:
            List of tick dictionaries
        """
        if not self.connected:
            return []
        
        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
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
                WHERE symbol = '{symbol}'
                  AND timestamp >= '{cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}'
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
            
            result = self.client.client.query(query)
            
            # Convert to list of dicts
            columns = ['timestamp', 'symbol', 'bid', 'ask', 'mid_price', 
                      'spread', 'spread_bps', 'bid_size', 'ask_size']
            
            ticks = []
            for row in result.result_rows:
                tick = dict(zip(columns, row))
                ticks.append(tick)
            
            return list(reversed(ticks))  # Return in chronological order
        
        except Exception as e:
            logger.error(f"Error fetching ticks: {e}")
            return []
    
    def get_recent_orderbook(self, symbol: str, limit: int = 1) -> Optional[Dict]:
        """
        Get most recent order book snapshot.
        
        Args:
            symbol: Currency pair
            limit: Number of snapshots (default 1 for latest)
        
        Returns:
            Order book dictionary
        """
        if not self.connected:
            return None
        
        try:
            query = f"""
                SELECT
                    timestamp,
                    symbol,
                    side,
                    price,
                    size,
                    level
                FROM orderbook
                WHERE symbol = '{symbol}'
                ORDER BY timestamp DESC, level ASC
                LIMIT 20
            """
            
            result = self.client.client.query(query)
            
            if not result.result_rows:
                return None
            
            # Group by side
            bids = []
            asks = []
            timestamp = None
            
            for row in result.result_rows:
                ts, sym, side, price, size, level = row
                if timestamp is None:
                    timestamp = ts
                
                level_data = {
                    'price': price,
                    'size': size,
                    'level': level
                }
                
                if side == 'bid':
                    bids.append(level_data)
                else:
                    asks.append(level_data)
            
            return {
                'timestamp': timestamp,
                'symbol': symbol,
                'bids': sorted(bids, key=lambda x: x['price'], reverse=True),
                'asks': sorted(asks, key=lambda x: x['price'])
            }
        
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            return None
    
    def get_recent_metrics(self, symbol: str, minutes: int = 5, limit: int = 1000) -> List[Dict]:
        """
        Get recent metrics for a symbol.
        
        Args:
            symbol: Currency pair
            minutes: Number of minutes of history
            limit: Maximum number of records
        
        Returns:
            List of metrics dictionaries
        """
        if not self.connected:
            return []
        
        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            query = f"""
                SELECT
                    timestamp,
                    symbol,
                    bid_ask_spread,
                    spread_bps,
                    bid_depth,
                    ask_depth,
                    total_depth,
                    order_flow_imbalance,
                    volatility,
                    is_anomaly,
                    anomaly_type,
                    anomaly_score
                FROM metrics
                WHERE symbol = '{symbol}'
                  AND timestamp >= '{cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}'
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
            
            result = self.client.client.query(query)
            
            columns = ['timestamp', 'symbol', 'bid_ask_spread', 'spread_bps',
                      'bid_depth', 'ask_depth', 'total_depth', 'order_flow_imbalance',
                      'volatility', 'is_anomaly', 'anomaly_type', 'anomaly_score']
            
            metrics = []
            for row in result.result_rows:
                metric = dict(zip(columns, row))
                metrics.append(metric)
            
            return list(reversed(metrics))
        
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            return []
    
    def get_anomaly_summary(self, symbol: str, hours: int = 24) -> Dict:
        """
        Get anomaly summary statistics.
        
        Args:
            symbol: Currency pair
            hours: Number of hours to analyze
        
        Returns:
            Dictionary with anomaly statistics
        """
        if not self.connected:
            return {}
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = f"""
                SELECT
                    count(*) as total_records,
                    sum(is_anomaly) as anomaly_count,
                    avg(anomaly_score) as avg_anomaly_score,
                    groupArray(anomaly_type) as anomaly_types
                FROM metrics
                WHERE symbol = '{symbol}'
                  AND timestamp >= '{cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}'
                  AND is_anomaly = 1
            """
            
            result = self.client.client.query(query)
            
            if result.result_rows:
                row = result.result_rows[0]
                return {
                    'total_records': row[0],
                    'anomaly_count': row[1],
                    'avg_anomaly_score': row[2],
                    'anomaly_types': row[3]
                }
            
            return {}
        
        except Exception as e:
            logger.error(f"Error fetching anomaly summary: {e}")
            return {}
