# Real-Time FX Market Microstructure Monitor

A real-time monitoring system for FX market microstructure, detecting anomalies and providing insights into market behavior.

## Features

- **Real-time Data Ingestion**: Kafka-based streaming pipeline for FX tick data
- **Time-Series Storage**: ClickHouse database optimized for high-frequency data
- **Microstructure Metrics**: 
  - Bid-ask spread analysis
  - Order book depth monitoring
  - Order flow imbalance calculation
  - Volatility clustering detection
- **Anomaly Detection**:
  - Quote stuffing detection
  - Wash trading detection
  - Spoofing detection
  - Statistical anomaly detection (Z-score, Half-Space Trees)
- **Interactive Dashboard**: Real-time Streamlit dashboard with visualizations

## Architecture

```
┌─────────────┐     ┌─────────┐     ┌──────────────┐     ┌────────────┐
│ FX Data API │────▶│  Kafka  │────▶│   Consumer   │────▶│ ClickHouse │
└─────────────┘     └─────────┘     └──────────────┘     └────────────┘
                                            │                     │
                                            ▼                     ▼
                                    ┌──────────────┐     ┌────────────┐
                                    │   Metrics    │────▶│ Dashboard  │
                                    │  Calculator  │     │ (Streamlit)│
                                    └──────────────┘     └────────────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │   Anomaly    │
                                    │  Detection   │
                                    └──────────────┘
```

## Technology Stack

- **Data Streaming**: Apache Kafka
- **Database**: ClickHouse
- **Processing**: Python (pandas, numpy, river)
- **Dashboard**: Streamlit
- **Containerization**: Docker

## Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.11+

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jitesh523/Real-Time-FX-Market-Microstructure-Monitor.git
cd Real-Time-FX-Market-Microstructure-Monitor
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Start infrastructure services:
```bash
docker-compose up -d zookeeper kafka clickhouse
```

4. Initialize ClickHouse schema:
```bash
python -c "from src.data_ingestion import get_clickhouse_client; get_clickhouse_client().initialize_schema()"
```

5. Install Python dependencies (for local development):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Running the Data Pipeline

1. Start the Kafka producer (data simulator):
```bash
python -m src.data_ingestion.kafka_producer
```

2. Start the Kafka consumer (in a new terminal):
```bash
python -m src.data_ingestion.kafka_consumer
```

3. Launch the dashboard (in a new terminal):
```bash
streamlit run src/dashboard/app.py
```

### Using Docker

Run the entire stack with Docker Compose:
```bash
docker-compose up
```

Access the dashboard at: http://localhost:8501

## Project Structure

```
.
├── config/
│   ├── clickhouse/
│   │   └── schema.sql          # Database schema
│   └── settings.py             # Configuration management
├── src/
│   ├── data_ingestion/
│   │   ├── kafka_producer.py   # Data simulator and producer
│   │   ├── kafka_consumer.py   # Kafka consumer
│   │   └── clickhouse_writer.py # Database client
│   ├── models/
│   │   └── tick_data.py        # Data models
│   ├── metrics/                # Microstructure metrics
│   ├── anomaly_detection/      # Anomaly detection algorithms
│   └── dashboard/              # Streamlit dashboard
├── tests/                      # Unit and integration tests
├── docs/                       # Documentation
├── docker-compose.yml          # Docker services configuration
├── Dockerfile                  # Application container
└── requirements.txt            # Python dependencies
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint code
pylint src/

# Type checking
mypy src/
```

## Configuration

Key configuration options in `.env`:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address
- `CLICKHOUSE_HOST`: ClickHouse server address
- `CURRENCY_PAIRS`: Comma-separated list of currency pairs to monitor
- `TICK_INTERVAL_MS`: Tick generation interval in milliseconds
- `ZSCORE_THRESHOLD`: Z-score threshold for anomaly detection

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Built following best practices in market microstructure analysis and real-time data processing.
