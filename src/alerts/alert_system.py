"""Alert notification system for anomalies and market events."""

import json
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
from loguru import logger


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    ANOMALY = "anomaly"
    SPREAD_WIDENING = "spread_widening"
    DEPTH_DEPLETION = "depth_depletion"
    QUOTE_STUFFING = "quote_stuffing"
    WASH_TRADING = "wash_trading"
    SPOOFING = "spoofing"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAK = "correlation_break"


class Alert:
    """Represents a single alert."""
    
    def __init__(self, alert_type: AlertType, severity: AlertSeverity,
                 symbol: str, message: str, data: Optional[Dict] = None):
        """
        Create an alert.
        
        Args:
            alert_type: Type of alert
            severity: Severity level
            symbol: Currency pair
            message: Alert message
            data: Additional data
        """
        self.alert_id = f"{datetime.now().timestamp()}_{symbol}_{alert_type.value}"
        self.timestamp = datetime.now()
        self.alert_type = alert_type
        self.severity = severity
        self.symbol = symbol
        self.message = message
        self.data = data or {}
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary."""
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'symbol': self.symbol,
            'message': self.message,
            'data': self.data
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"[{self.severity.value.upper()}] {self.symbol} - {self.message}"


class AlertManager:
    """Manage and dispatch alerts."""
    
    def __init__(self, max_alerts: int = 1000):
        """
        Initialize alert manager.
        
        Args:
            max_alerts: Maximum number of alerts to keep in memory
        """
        self.max_alerts = max_alerts
        self.alerts = []
        self.alert_count_by_type = {}
        self.alert_count_by_severity = {}
        
        logger.info(f"Initialized Alert Manager (max_alerts={max_alerts})")
    
    def create_alert(self, alert_type: AlertType, severity: AlertSeverity,
                    symbol: str, message: str, data: Optional[Dict] = None) -> Alert:
        """
        Create and register an alert.
        
        Args:
            alert_type: Type of alert
            severity: Severity level
            symbol: Currency pair
            message: Alert message
            data: Additional data
        
        Returns:
            Created alert
        """
        alert = Alert(alert_type, severity, symbol, message, data)
        
        # Add to alerts list
        self.alerts.append(alert)
        
        # Update counts
        self.alert_count_by_type[alert_type.value] = \
            self.alert_count_by_type.get(alert_type.value, 0) + 1
        self.alert_count_by_severity[severity.value] = \
            self.alert_count_by_severity.get(severity.value, 0) + 1
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts.pop(0)
        
        # Log alert
        log_func = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.CRITICAL: logger.error
        }[severity]
        
        log_func(f"Alert: {alert}")
        
        return alert
    
    def get_recent_alerts(self, limit: int = 100, 
                         severity: Optional[AlertSeverity] = None,
                         alert_type: Optional[AlertType] = None,
                         symbol: Optional[str] = None) -> List[Alert]:
        """
        Get recent alerts with optional filtering.
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity
            alert_type: Filter by type
            symbol: Filter by symbol
        
        Returns:
            List of alerts
        """
        filtered_alerts = self.alerts
        
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
        
        if alert_type:
            filtered_alerts = [a for a in filtered_alerts if a.alert_type == alert_type]
        
        if symbol:
            filtered_alerts = [a for a in filtered_alerts if a.symbol == symbol]
        
        return filtered_alerts[-limit:]
    
    def get_statistics(self) -> Dict:
        """Get alert statistics."""
        return {
            'total_alerts': len(self.alerts),
            'by_type': self.alert_count_by_type.copy(),
            'by_severity': self.alert_count_by_severity.copy(),
            'recent_critical': len([a for a in self.alerts[-100:] 
                                   if a.severity == AlertSeverity.CRITICAL])
        }
    
    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts.clear()
        logger.info("Cleared all alerts")
    
    def export_alerts(self, filepath: str, format: str = 'json'):
        """
        Export alerts to file.
        
        Args:
            filepath: Output file path
            format: Export format ('json' or 'csv')
        """
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump([a.to_dict() for a in self.alerts], f, indent=2)
        elif format == 'csv':
            import csv
            with open(filepath, 'w', newline='') as f:
                if self.alerts:
                    writer = csv.DictWriter(f, fieldnames=self.alerts[0].to_dict().keys())
                    writer.writeheader()
                    for alert in self.alerts:
                        writer.writerow(alert.to_dict())
        
        logger.info(f"Exported {len(self.alerts)} alerts to {filepath}")


class AlertRuleEngine:
    """Rule engine for automatic alert generation."""
    
    def __init__(self, alert_manager: AlertManager):
        """
        Initialize rule engine.
        
        Args:
            alert_manager: Alert manager instance
        """
        self.alert_manager = alert_manager
        self.rules = {}
        
        # Default rules
        self._setup_default_rules()
        
        logger.info("Initialized Alert Rule Engine")
    
    def _setup_default_rules(self):
        """Set up default alert rules."""
        self.rules = {
            'spread_widening': {
                'threshold': 2.0,  # 2x normal spread
                'severity': AlertSeverity.WARNING
            },
            'depth_depletion': {
                'threshold': 0.25,  # 25th percentile
                'severity': AlertSeverity.WARNING
            },
            'quote_stuffing': {
                'threshold': 100,  # quotes per second
                'severity': AlertSeverity.CRITICAL
            },
            'volatility_spike': {
                'threshold': 3.0,  # 3 standard deviations
                'severity': AlertSeverity.WARNING
            }
        }
    
    def check_spread_widening(self, symbol: str, current_spread: float, 
                             avg_spread: float) -> Optional[Alert]:
        """Check for spread widening."""
        rule = self.rules['spread_widening']
        
        if current_spread > avg_spread * rule['threshold']:
            return self.alert_manager.create_alert(
                AlertType.SPREAD_WIDENING,
                rule['severity'],
                symbol,
                f"Spread widened to {current_spread:.5f} ({current_spread/avg_spread:.1f}x normal)",
                {'current_spread': current_spread, 'avg_spread': avg_spread}
            )
        
        return None
    
    def check_quote_stuffing(self, symbol: str, quote_rate: int) -> Optional[Alert]:
        """Check for quote stuffing."""
        rule = self.rules['quote_stuffing']
        
        if quote_rate > rule['threshold']:
            return self.alert_manager.create_alert(
                AlertType.QUOTE_STUFFING,
                rule['severity'],
                symbol,
                f"Quote stuffing detected: {quote_rate} quotes/sec",
                {'quote_rate': quote_rate, 'threshold': rule['threshold']}
            )
        
        return None
    
    def check_anomaly(self, symbol: str, anomaly_type: str, 
                     anomaly_score: float) -> Optional[Alert]:
        """Check for general anomaly."""
        severity = AlertSeverity.CRITICAL if anomaly_score > 0.9 else AlertSeverity.WARNING
        
        return self.alert_manager.create_alert(
            AlertType.ANOMALY,
            severity,
            symbol,
            f"Anomaly detected: {anomaly_type} (score: {anomaly_score:.3f})",
            {'anomaly_type': anomaly_type, 'anomaly_score': anomaly_score}
        )


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
