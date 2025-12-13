"""Enhanced configuration with validation and production settings."""

from typing import List, Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers"
    )
    kafka_topic_ticks: str = Field(default="fx_ticks", description="Kafka topic for ticks")
    kafka_topic_orderbook: str = Field(default="fx_orderbook", description="Kafka topic for order book")
    kafka_consumer_group: str = Field(default="fx_consumer_group", description="Kafka consumer group")
    
    # ClickHouse Configuration
    clickhouse_host: str = Field(default="localhost", description="ClickHouse host")
    clickhouse_port: int = Field(default=9000, ge=1, le=65535, description="ClickHouse port")
    clickhouse_user: str = Field(default="default", description="ClickHouse user")
    clickhouse_password: str = Field(default="", description="ClickHouse password")
    clickhouse_database: str = Field(default="fx_market", description="ClickHouse database")
    
    # Application Configuration
    currency_pairs: str = Field(
        default="EUR/USD,GBP/USD,USD/JPY,AUD/USD",
        description="Comma-separated currency pairs"
    )
    tick_interval_ms: int = Field(
        default=100,
        ge=10,
        le=10000,
        description="Tick generation interval in milliseconds"
    )
    
    # Dashboard Configuration
    dashboard_port: int = Field(default=8501, ge=1, le=65535, description="Dashboard port")
    refresh_interval_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Dashboard refresh interval"
    )
    
    # Anomaly Detection
    zscore_threshold: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Z-score threshold for anomaly detection"
    )
    quote_stuffing_threshold: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Quote stuffing threshold (quotes/sec)"
    )
    
    # Real Data API
    alphavantage_api_key: Optional[str] = Field(
        default=None,
        description="Alpha Vantage API key"
    )
    use_real_data: bool = Field(
        default=False,
        description="Use real FX data instead of simulator"
    )
    
    # Redis Configuration (for caching)
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    redis_enabled: bool = Field(default=False, description="Enable Redis caching")
    
    # Production Settings
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    @field_validator("currency_pairs")
    @classmethod
    def validate_currency_pairs(cls, v: str) -> str:
        """Validate currency pairs format."""
        pairs = [p.strip() for p in v.split(",")]
        for pair in pairs:
            if "/" not in pair:
                raise ValueError(f"Invalid currency pair format: {pair}. Expected format: EUR/USD")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    @property
    def currency_pairs_list(self) -> List[str]:
        """Get currency pairs as a list."""
        return [p.strip() for p in self.currency_pairs.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    def validate_all(self) -> None:
        """Validate all settings on startup."""
        if self.is_production:
            if self.debug:
                raise ValueError("Debug mode must be disabled in production")
            if self.clickhouse_password == "":
                raise ValueError("ClickHouse password must be set in production")


# Global settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate_all()
except ValueError as e:
    import warnings
    warnings.warn(f"Settings validation warning: {e}")
