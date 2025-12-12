"""Metrics aggregation module for combining all microstructure metrics."""

from typing import Dict, Optional
from datetime import datetime
from loguru import logger

from src.models import TickData, OrderBook, Trade, MarketMetrics
from src.metrics.spread_calculator import SpreadCalculator
from src.metrics.depth_analyzer import DepthAnalyzer
from src.metrics.flow_imbalance import FlowImbalanceCalculator
from src.metrics.volatility_clustering import VolatilityAnalyzer


class MetricsAggregator:
    """Aggregate all microstructure metrics for a currency pair."""
    
    def __init__(self, symbol: str):
        """
        Initialize metrics aggregator.
        
        Args:
            symbol: Currency pair symbol
        """
        self.symbol = symbol
        self.spread_calc = SpreadCalculator()
        self.depth_analyzer = DepthAnalyzer()
        self.flow_calc = FlowImbalanceCalculator()
        self.volatility_analyzer = VolatilityAnalyzer()
        
        logger.info(f"Initialized metrics aggregator for {symbol}")
    
    def process_tick(self, tick: TickData):
        """Process a new tick."""
        self.spread_calc.add_tick(tick)
        self.volatility_analyzer.add_tick(tick)
    
    def process_orderbook(self, orderbook: OrderBook):
        """Process a new order book snapshot."""
        self.depth_analyzer.add_orderbook(orderbook)
        self.flow_calc.add_orderbook(orderbook)
    
    def process_trade(self, trade: Trade):
        """Process a new trade."""
        self.flow_calc.add_trade(trade)
    
    def get_current_metrics(self) -> Optional[MarketMetrics]:
        """
        Get current aggregated metrics.
        
        Returns:
            MarketMetrics object with all current metrics
        """
        # Get spread metrics
        spread_metrics = self.spread_calc.get_spread_metrics()
        if not spread_metrics or spread_metrics['current_spread'] is None:
            return None
        
        # Get depth metrics
        depth_metrics = self.depth_analyzer.get_depth_metrics()
        
        # Get flow metrics
        flow_metrics = self.flow_calc.get_flow_metrics()
        
        # Get volatility metrics
        volatility_metrics = self.volatility_analyzer.get_volatility_metrics()
        
        # Create MarketMetrics object
        metrics = MarketMetrics(
            timestamp=datetime.now(),
            symbol=self.symbol,
            bid_ask_spread=spread_metrics['current_spread'],
            spread_bps=spread_metrics['current_spread_bps'],
            bid_depth=depth_metrics.get('bid_depth', 0.0),
            ask_depth=depth_metrics.get('ask_depth', 0.0),
            total_depth=depth_metrics.get('total_depth', 0.0),
            order_flow_imbalance=flow_metrics.get('trade_flow_imbalance', 0.0),
            volatility=volatility_metrics.get('realized_volatility')
        )
        
        return metrics
    
    def get_all_metrics(self) -> Dict:
        """
        Get all detailed metrics.
        
        Returns:
            Dictionary containing all metrics from all calculators
        """
        return {
            'symbol': self.symbol,
            'timestamp': datetime.now().isoformat(),
            'spread': self.spread_calc.get_spread_metrics(),
            'depth': self.depth_analyzer.get_depth_metrics(),
            'flow': self.flow_calc.get_flow_metrics(),
            'volatility': self.volatility_analyzer.get_volatility_metrics()
        }
    
    def detect_market_stress(self) -> Dict[str, bool]:
        """
        Detect various market stress indicators.
        
        Returns:
            Dictionary of stress indicators
        """
        spread_metrics = self.spread_calc.get_spread_metrics()
        depth_metrics = self.depth_analyzer.get_depth_metrics()
        flow_metrics = self.flow_calc.get_flow_metrics()
        volatility_metrics = self.volatility_analyzer.get_volatility_metrics()
        
        return {
            'spread_widening': spread_metrics.get('is_spread_widening', False),
            'depth_depletion': depth_metrics.get('is_depth_depleted', False),
            'aggressive_buying': flow_metrics.get('is_aggressive_buying', False),
            'aggressive_selling': flow_metrics.get('is_aggressive_selling', False),
            'volatility_clustering': volatility_metrics.get('is_clustering', False),
            'high_volatility_regime': volatility_metrics.get('volatility_regime') == 'high'
        }
    
    def get_market_quality_score(self) -> Optional[float]:
        """
        Calculate an overall market quality score (0-100).
        
        Higher score = better market quality (tight spreads, good depth, low volatility)
        
        Returns:
            Market quality score
        """
        spread_metrics = self.spread_calc.get_spread_metrics()
        depth_metrics = self.depth_analyzer.get_depth_metrics()
        volatility_metrics = self.volatility_analyzer.get_volatility_metrics()
        
        if not spread_metrics or not depth_metrics:
            return None
        
        score = 100.0
        
        # Penalize for wide spreads
        if spread_metrics.get('is_spread_widening'):
            score -= 20
        
        # Penalize for low depth
        if depth_metrics.get('is_depth_depleted'):
            score -= 20
        
        # Penalize for high volatility
        if volatility_metrics.get('volatility_regime') == 'high':
            score -= 15
        elif volatility_metrics.get('volatility_regime') == 'low':
            score += 5
        
        # Penalize for volatility clustering
        if volatility_metrics.get('is_clustering'):
            score -= 10
        
        # Reward for good liquidity
        liquidity_score = depth_metrics.get('liquidity_score')
        if liquidity_score and liquidity_score > 1000:
            score += 10
        
        return max(0.0, min(100.0, score))


class MultiSymbolMetricsManager:
    """Manage metrics for multiple currency pairs."""
    
    def __init__(self, symbols: list):
        """
        Initialize multi-symbol metrics manager.
        
        Args:
            symbols: List of currency pair symbols
        """
        self.aggregators = {symbol: MetricsAggregator(symbol) for symbol in symbols}
        logger.info(f"Initialized metrics manager for {len(symbols)} symbols")
    
    def process_tick(self, tick: TickData):
        """Process a tick for the appropriate symbol."""
        if tick.symbol in self.aggregators:
            self.aggregators[tick.symbol].process_tick(tick)
    
    def process_orderbook(self, orderbook: OrderBook):
        """Process an order book for the appropriate symbol."""
        if orderbook.symbol in self.aggregators:
            self.aggregators[orderbook.symbol].process_orderbook(orderbook)
    
    def process_trade(self, trade: Trade):
        """Process a trade for the appropriate symbol."""
        if trade.symbol in self.aggregators:
            self.aggregators[trade.symbol].process_trade(trade)
    
    def get_all_current_metrics(self) -> Dict[str, Optional[MarketMetrics]]:
        """Get current metrics for all symbols."""
        return {
            symbol: aggregator.get_current_metrics()
            for symbol, aggregator in self.aggregators.items()
        }
    
    def get_all_detailed_metrics(self) -> Dict[str, Dict]:
        """Get detailed metrics for all symbols."""
        return {
            symbol: aggregator.get_all_metrics()
            for symbol, aggregator in self.aggregators.items()
        }
    
    def get_market_stress_summary(self) -> Dict[str, Dict[str, bool]]:
        """Get market stress indicators for all symbols."""
        return {
            symbol: aggregator.detect_market_stress()
            for symbol, aggregator in self.aggregators.items()
        }
