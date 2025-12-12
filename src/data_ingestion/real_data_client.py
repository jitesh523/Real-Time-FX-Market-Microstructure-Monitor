"""Real FX data client with Alpha Vantage integration."""

import requests
import time
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

from config import settings
from src.models import TickData


class AlphaVantageClient:
    """Client for Alpha Vantage FX data API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Alpha Vantage client.
        
        Args:
            api_key: Alpha Vantage API key
        """
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.last_request_time = 0
        self.min_request_interval = 12  # 5 requests/min = 12 seconds between requests
        
        logger.info("Initialized Alpha Vantage client")
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Dict]:
        """
        Get current exchange rate.
        
        Args:
            from_currency: Source currency (e.g., 'EUR')
            to_currency: Target currency (e.g., 'USD')
        
        Returns:
            Exchange rate data or None if error
        """
        self._rate_limit()
        
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_currency,
            'to_currency': to_currency,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Realtime Currency Exchange Rate' in data:
                return data['Realtime Currency Exchange Rate']
            elif 'Note' in data:
                logger.warning(f"API limit reached: {data['Note']}")
                return None
            else:
                logger.error(f"Unexpected response: {data}")
                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_tick(self, symbol: str) -> Optional[TickData]:
        """
        Get tick data for a currency pair.
        
        Args:
            symbol: Currency pair (e.g., 'EUR/USD')
        
        Returns:
            TickData or None if error
        """
        # Parse symbol
        parts = symbol.split('/')
        if len(parts) != 2:
            logger.error(f"Invalid symbol format: {symbol}")
            return None
        
        from_currency, to_currency = parts
        
        # Get exchange rate
        rate_data = self.get_exchange_rate(from_currency, to_currency)
        
        if not rate_data:
            return None
        
        try:
            # Parse response
            bid = float(rate_data['8. Bid Price'])
            ask = float(rate_data['9. Ask Price'])
            timestamp_str = rate_data['6. Last Refreshed']
            
            # Parse timestamp
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Create TickData
            tick = TickData(
                timestamp=timestamp,
                symbol=symbol,
                bid=bid,
                ask=ask,
                bid_size=1.0,  # Alpha Vantage doesn't provide size
                ask_size=1.0
            )
            
            logger.info(f"Fetched real data for {symbol}: {tick.mid_price:.5f}")
            
            return tick
        
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse rate data: {e}")
            return None


class RealDataClient:
    """
    Unified client for real FX data with fallback to simulator.
    """
    
    def __init__(self, use_real_data: bool = True):
        """
        Initialize real data client.
        
        Args:
            use_real_data: Whether to use real data or simulator
        """
        self.use_real_data = use_real_data
        self.alpha_vantage = None
        self.simulator = None
        
        if use_real_data:
            api_key = getattr(settings, 'alphavantage_api_key', None)
            if api_key:
                self.alpha_vantage = AlphaVantageClient(api_key)
                logger.info("Using real FX data from Alpha Vantage")
            else:
                logger.warning("No Alpha Vantage API key found, falling back to simulator")
                self.use_real_data = False
        
        if not self.use_real_data:
            from src.data_ingestion import FXDataSimulator
            self.simulator = FXDataSimulator()
            logger.info("Using simulated FX data")
    
    def get_tick(self, symbol: str) -> Optional[TickData]:
        """
        Get tick data with automatic fallback.
        
        Args:
            symbol: Currency pair
        
        Returns:
            TickData
        """
        if self.use_real_data and self.alpha_vantage:
            tick = self.alpha_vantage.get_tick(symbol)
            
            if tick:
                return tick
            
            # Fallback to simulator on error
            logger.warning(f"Real data failed for {symbol}, using simulator")
            if not self.simulator:
                from src.data_ingestion import FXDataSimulator
                self.simulator = FXDataSimulator()
        
        # Use simulator
        return self.simulator.generate_tick(symbol)
    
    def is_using_real_data(self) -> bool:
        """Check if using real data."""
        return self.use_real_data and self.alpha_vantage is not None


# Global client instance
_real_data_client: Optional[RealDataClient] = None


def get_real_data_client(use_real_data: bool = True) -> RealDataClient:
    """Get or create real data client singleton."""
    global _real_data_client
    if _real_data_client is None:
        _real_data_client = RealDataClient(use_real_data=use_real_data)
    return _real_data_client
