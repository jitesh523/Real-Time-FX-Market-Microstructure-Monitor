"""Data ingestion package."""

from src.data_ingestion.clickhouse_writer import ClickHouseClient, get_clickhouse_client
from src.data_ingestion.kafka_consumer import KafkaTickConsumer
from src.data_ingestion.kafka_producer import FXDataSimulator, KafkaTickProducer

__all__ = [
    "KafkaTickProducer",
    "FXDataSimulator",
    "KafkaTickConsumer",
    "ClickHouseClient",
    "get_clickhouse_client",
]
