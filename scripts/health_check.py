#!/usr/bin/env python3
"""
System health check script.

Checks the health of all system components:
- Kafka connectivity
- ClickHouse connectivity
- Data pipeline status
- Dashboard availability
"""

import sys
import socket
from datetime import datetime
from loguru import logger

from config import settings


def check_port(host: str, port: int, service_name: str) -> bool:
    """Check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.success(f"✓ {service_name} is reachable at {host}:{port}")
            return True
        else:
            logger.error(f"✗ {service_name} is not reachable at {host}:{port}")
            return False
    except Exception as e:
        logger.error(f"✗ Error checking {service_name}: {e}")
        return False


def check_kafka() -> bool:
    """Check Kafka connectivity."""
    logger.info("Checking Kafka...")
    
    try:
        from kafka import KafkaProducer
        from kafka.errors import NoBrokersAvailable
        
        try:
            producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                request_timeout_ms=5000
            )
            producer.close()
            logger.success("✓ Kafka is accessible")
            return True
        except NoBrokersAvailable:
            logger.error("✗ Kafka brokers not available")
            return False
    except Exception as e:
        logger.error(f"✗ Kafka check failed: {e}")
        return False


def check_clickhouse() -> bool:
    """Check ClickHouse connectivity."""
    logger.info("Checking ClickHouse...")
    
    try:
        from src.data_ingestion import get_clickhouse_client
        
        client = get_clickhouse_client()
        
        # Try a simple query
        result = client.client.query("SELECT 1")
        
        if result.result_rows:
            logger.success("✓ ClickHouse is accessible")
            
            # Check if tables exist
            tables_query = """
                SELECT name FROM system.tables 
                WHERE database = 'fx_market'
            """
            tables_result = client.client.query(tables_query)
            tables = [row[0] for row in tables_result.result_rows]
            
            expected_tables = ['ticks', 'orderbook', 'trades', 'metrics']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                logger.warning(f"⚠️ Missing tables: {', '.join(missing_tables)}")
                logger.info("Run: docker exec -i clickhouse clickhouse-client < config/clickhouse/schema.sql")
                return False
            else:
                logger.success("✓ All required tables exist")
                return True
        else:
            logger.error("✗ ClickHouse query failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ ClickHouse check failed: {e}")
        return False


def check_data_pipeline() -> bool:
    """Check if data is flowing through the pipeline."""
    logger.info("Checking data pipeline...")
    
    try:
        from src.data_ingestion import get_clickhouse_client
        
        client = get_clickhouse_client()
        
        # Check recent ticks
        query = """
            SELECT count(*) as count, max(timestamp) as latest
            FROM fx_market.ticks
            WHERE timestamp >= now() - INTERVAL 5 MINUTE
        """
        
        result = client.client.query(query)
        
        if result.result_rows:
            count, latest = result.result_rows[0]
            
            if count > 0:
                logger.success(f"✓ Data pipeline is active ({count} ticks in last 5 minutes)")
                logger.info(f"  Latest tick: {latest}")
                return True
            else:
                logger.warning("⚠️ No recent data in pipeline")
                logger.info("  Start producer: python -m src.data_ingestion.kafka_producer")
                logger.info("  Start consumer: python -m src.data_ingestion.kafka_consumer")
                return False
        else:
            logger.warning("⚠️ Unable to query tick data")
            return False
            
    except Exception as e:
        logger.error(f"✗ Data pipeline check failed: {e}")
        return False


def check_dashboard() -> bool:
    """Check if dashboard is accessible."""
    logger.info("Checking dashboard...")
    
    return check_port('localhost', settings.dashboard_port, 'Dashboard')


def main():
    """Run all health checks."""
    logger.info("=" * 60)
    logger.info("FX Market Microstructure Monitor - Health Check")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    checks = [
        ("Kafka", check_kafka),
        ("ClickHouse", check_clickhouse),
        ("Data Pipeline", check_data_pipeline),
        ("Dashboard", check_dashboard)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        logger.info(f"\n{'=' * 60}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"✗ {check_name} check failed with exception: {e}")
            results.append((check_name, False))
    
    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("Health Check Summary")
    logger.info(f"{'=' * 60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓ HEALTHY" if result else "✗ UNHEALTHY"
        logger.info(f"{check_name}: {status}")
    
    logger.info(f"\nStatus: {passed}/{total} checks passed")
    
    if passed == total:
        logger.success("\n✓ System is healthy")
        return 0
    else:
        logger.warning(f"\n⚠️ {total - passed} component(s) need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
