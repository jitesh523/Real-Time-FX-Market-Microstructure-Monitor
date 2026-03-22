"""Data ingestion package."""

from src.data_ingestion.kafka_producer import FXDataSimulator

try:
    from src.data_ingestion.kafka_producer import KafkaTickProducer
    from src.data_ingestion.kafka_consumer import KafkaTickConsumer
    from src.data_ingestion.clickhouse_writer import ClickHouseClient, get_clickhouse_client
except ImportError:
    KafkaTickProducer = None  # type: ignore[assignment, misc]
    KafkaTickConsumer = None  # type: ignore[assignment, misc]
    ClickHouseClient = None  # type: ignore[assignment, misc]
    get_clickhouse_client = None  # type: ignore[assignment, misc]

__all__ = [
    "KafkaTickProducer",
    "FXDataSimulator",
    "KafkaTickConsumer",
    "ClickHouseClient",
    "get_clickhouse_client",
]
