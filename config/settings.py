"""Configuration settings for FX Market Microstructure Monitor."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_ticks: str = "fx_ticks"
    kafka_topic_trades: str = "fx_trades"
    kafka_topic_orderbook: str = "fx_orderbook"
    kafka_consumer_group: str = "fx_monitor"
    
    # ClickHouse Configuration
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 9000
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "fx_market"
    
    # Application Configuration
    log_level: str = "INFO"
    currency_pairs: str = "EUR/USD,GBP/USD,USD/JPY,AUD/USD"
    tick_interval_ms: int = 100
    
    # Anomaly Detection Thresholds
    zscore_threshold: float = 3.0
    quote_stuffing_threshold: int = 100
    wash_trade_window_seconds: int = 60
    spoofing_depth_threshold: int = 5
    
    # Dashboard Configuration
    dashboard_port: int = 8501
    refresh_interval_seconds: int = 1
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def currency_pairs_list(self) -> List[str]:
        """Get currency pairs as a list."""
        return [pair.strip() for pair in self.currency_pairs.split(",")]


# Global settings instance
settings = Settings()
