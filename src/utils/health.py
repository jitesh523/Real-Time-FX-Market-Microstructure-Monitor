"""Health check endpoints for monitoring."""

from typing import Dict
from datetime import datetime
from loguru import logger

from config import settings


class HealthCheck:
    """Health check service for monitoring system health."""
    
    def __init__(self):
        """Initialize health check service."""
        self.start_time = datetime.now()
        logger.info("Health check service initialized")
    
    def liveness(self) -> Dict:
        """
        Liveness probe - is the application running?
        
        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }
    
    def readiness(self) -> Dict:
        """
        Readiness probe - is the application ready to serve traffic?
        
        Checks:
        - Kafka connectivity
        - ClickHouse connectivity
        - Redis connectivity (if enabled)
        
        Returns:
            Readiness status dictionary
        """
        checks = {
            "kafka": self._check_kafka(),
            "clickhouse": self._check_clickhouse(),
        }
        
        if settings.redis_enabled:
            checks["redis"] = self._check_redis()
        
        all_healthy = all(check["healthy"] for check in checks.values())
        
        return {
            "status": "ready" if all_healthy else "not_ready",
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }
    
    def _check_kafka(self) -> Dict:
        """Check Kafka connectivity."""
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                request_timeout_ms=5000
            )
            producer.close()
            return {"healthy": True, "message": "Kafka is accessible"}
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return {"healthy": False, "message": str(e)}
    
    def _check_clickhouse(self) -> Dict:
        """Check ClickHouse connectivity."""
        try:
            from src.data_ingestion import get_clickhouse_client
            client = get_clickhouse_client()
            result = client.client.query("SELECT 1")
            if result.result_rows:
                return {"healthy": True, "message": "ClickHouse is accessible"}
            return {"healthy": False, "message": "ClickHouse query failed"}
        except Exception as e:
            logger.error(f"ClickHouse health check failed: {e}")
            return {"healthy": False, "message": str(e)}
    
    def _check_redis(self) -> Dict:
        """Check Redis connectivity."""
        try:
            import redis
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                socket_timeout=5
            )
            r.ping()
            return {"healthy": True, "message": "Redis is accessible"}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"healthy": False, "message": str(e)}
    
    def metrics(self) -> Dict:
        """
        Prometheus-style metrics.
        
        Returns:
            Metrics dictionary
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "environment": settings.environment,
            "debug_mode": settings.debug,
            "currency_pairs_count": len(settings.currency_pairs_list),
            "timestamp": datetime.now().isoformat()
        }


# Global health check instance
_health_check: HealthCheck = None


def get_health_check() -> HealthCheck:
    """Get or create health check singleton."""
    global _health_check
    if _health_check is None:
        _health_check = HealthCheck()
    return _health_check
