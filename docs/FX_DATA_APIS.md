# Real FX Data API Options

## Free/Open Source APIs

### 1. **Alpha Vantage** ⭐ Recommended
- **URL**: https://www.alphavantage.co/
- **Free Tier**: 5 API calls/minute, 500 calls/day
- **Data**: Real-time and historical FX rates
- **Format**: JSON
- **Coverage**: 150+ currencies
- **Pros**: Reliable, good documentation, free tier available
- **Cons**: Rate limits on free tier

### 2. **Twelve Data**
- **URL**: https://twelvedata.com/
- **Free Tier**: 800 API calls/day
- **Data**: Real-time FX, stocks, crypto
- **Format**: JSON
- **Pros**: WebSocket support, good free tier
- **Cons**: Limited historical data on free tier

### 3. **Fixer.io**
- **URL**: https://fixer.io/
- **Free Tier**: 100 requests/month
- **Data**: FX rates (updated hourly)
- **Pros**: Simple API, reliable
- **Cons**: Very limited free tier, no real-time

### 4. **ExchangeRate-API**
- **URL**: https://www.exchangerate-api.com/
- **Free Tier**: 1,500 requests/month
- **Data**: FX rates (updated daily)
- **Pros**: Simple, no signup required
- **Cons**: Daily updates only, not real-time

### 5. **OANDA** (Professional)
- **URL**: https://www.oanda.com/
- **Pricing**: Paid (professional grade)
- **Data**: Real-time streaming FX data
- **Pros**: Institutional quality, streaming
- **Cons**: Expensive, requires account

## Recommended Approach

For this project, we'll implement:

1. **Primary**: Alpha Vantage (free tier)
2. **Fallback**: Simulator (for development/testing)
3. **Future**: OANDA or similar for production

## Implementation Plan

```python
# Priority order for data sources
DATA_SOURCES = [
    'alphavantage',  # Try real data first
    'simulator'      # Fallback to simulator
]
```

## Alpha Vantage API Details

### Endpoint for FX
```
https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey=YOUR_API_KEY
```

### Response Format
```json
{
    "Realtime Currency Exchange Rate": {
        "1. From_Currency Code": "EUR",
        "2. From_Currency Name": "Euro",
        "3. To_Currency Code": "USD",
        "4. To_Currency Name": "United States Dollar",
        "5. Exchange Rate": "1.08500000",
        "6. Last Refreshed": "2024-01-01 12:00:00",
        "7. Time Zone": "UTC",
        "8. Bid Price": "1.08490000",
        "9. Ask Price": "1.08510000"
    }
}
```

### Rate Limits
- 5 API requests per minute
- 500 API requests per day

## Getting Started

1. Sign up at https://www.alphavantage.co/support/#api-key
2. Get free API key
3. Add to `.env`:
   ```
   ALPHAVANTAGE_API_KEY=your_key_here
   ```
