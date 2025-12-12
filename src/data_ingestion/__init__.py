"""Data ingestion package."""

from src.data_ingestion.kafka_producer import KafkaTickProducer, FXDataSimulator
from src.data_ingestion.kafka_consumer import KafkaTickConsumer
from src.data_ingestion.clickhouse_writer import ClickHouseClient, get_clickhouse_client

__all__ = [
    "KafkaTickProducer",
    "FXDataSimulator",
    "KafkaTickConsumer",
    "ClickHouseClient",
    "get_clickhouse_client"
]
