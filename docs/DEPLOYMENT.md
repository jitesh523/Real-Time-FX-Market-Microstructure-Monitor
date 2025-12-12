# Deployment Guide

This guide provides step-by-step instructions for deploying the Real-Time FX Market Microstructure Monitor.

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- At least 4GB RAM available
- Ports 8501, 9092, 9000, 8123 available

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/jitesh523/Real-Time-FX-Market-Microstructure-Monitor.git
cd Real-Time-FX-Market-Microstructure-Monitor
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed
```

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- Zookeeper (port 2181)
- Kafka (port 9092)
- ClickHouse (ports 8123, 9000)
- Dashboard (port 8501)

### 4. Initialize Database Schema

```bash
# Wait for ClickHouse to be ready (about 10 seconds)
sleep 10

# Initialize schema
docker exec -i clickhouse clickhouse-client < config/clickhouse/schema.sql
```

### 5. Start Data Pipeline

In separate terminals:

```bash
# Terminal 1: Start data producer (simulator)
python -m src.data_ingestion.kafka_producer

# Terminal 2: Start data consumer
python -m src.data_ingestion.kafka_consumer
```

### 6. Access Dashboard

Open your browser and navigate to:
```
http://localhost:8501
```

## Manual Setup (Without Docker)

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install and Configure Kafka

Download and start Kafka:
```bash
# Download Kafka
wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz
tar -xzf kafka_2.13-3.6.0.tgz
cd kafka_2.13-3.6.0

# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties &

# Start Kafka
bin/kafka-server-start.sh config/server.properties &
```

### 3. Install and Configure ClickHouse

```bash
# On macOS
brew install clickhouse

# On Ubuntu
sudo apt-get install clickhouse-server clickhouse-client

# Start ClickHouse
sudo service clickhouse-server start
```

### 4. Initialize Database

```bash
clickhouse-client < config/clickhouse/schema.sql
```

### 5. Run Application

```bash
# Terminal 1: Producer
python -m src.data_ingestion.kafka_producer

# Terminal 2: Consumer
python -m src.data_ingestion.kafka_consumer

# Terminal 3: Dashboard
streamlit run src/dashboard/app.py
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_TICKS=fx_ticks
KAFKA_TOPIC_ORDERBOOK=fx_orderbook

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_DATABASE=fx_market

# Application
CURRENCY_PAIRS=EUR/USD,GBP/USD,USD/JPY,AUD/USD
TICK_INTERVAL_MS=100

# Anomaly Detection
ZSCORE_THRESHOLD=3.0
QUOTE_STUFFING_THRESHOLD=100
```

## Monitoring

### Check Service Status

```bash
# Check Docker containers
docker-compose ps

# Check Kafka topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check ClickHouse
docker exec clickhouse clickhouse-client --query "SELECT count(*) FROM fx_market.ticks"
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f clickhouse
docker-compose logs -f kafka
```

## Troubleshooting

### Dashboard Not Loading

1. Check if ClickHouse is running:
   ```bash
   docker-compose ps clickhouse
   ```

2. Verify database connection:
   ```bash
   docker exec clickhouse clickhouse-client --query "SELECT 1"
   ```

### No Data Appearing

1. Check if producer is running:
   ```bash
   ps aux | grep kafka_producer
   ```

2. Check Kafka topics:
   ```bash
   docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic fx_ticks --from-beginning --max-messages 5
   ```

3. Check consumer logs for errors

### High Memory Usage

- Reduce `TICK_INTERVAL_MS` to generate fewer ticks
- Reduce number of `CURRENCY_PAIRS`
- Adjust ClickHouse memory settings in `docker-compose.yml`

## Production Deployment

### Security Considerations

1. **Enable Authentication**:
   - Configure Kafka SASL/SSL
   - Set ClickHouse password
   - Add API authentication to dashboard

2. **Network Security**:
   - Use firewall rules
   - Enable TLS/SSL for all connections
   - Restrict port access

3. **Data Retention**:
   - Configure ClickHouse TTL policies
   - Set up automated backups

### Scaling

1. **Horizontal Scaling**:
   - Add more Kafka brokers
   - Use Kafka partitioning
   - Deploy multiple consumer instances

2. **Vertical Scaling**:
   - Increase ClickHouse memory
   - Use SSD storage
   - Optimize queries with indexes

### Monitoring in Production

- Set up Prometheus + Grafana for metrics
- Configure alerting for anomalies
- Monitor resource usage
- Track data pipeline latency

## Backup and Recovery

### Backup ClickHouse Data

```bash
# Create backup
docker exec clickhouse clickhouse-client --query "BACKUP DATABASE fx_market TO Disk('backups', 'backup_$(date +%Y%m%d).zip')"
```

### Restore from Backup

```bash
# Restore
docker exec clickhouse clickhouse-client --query "RESTORE DATABASE fx_market FROM Disk('backups', 'backup_20240101.zip')"
```

## Updating

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations if needed
docker exec clickhouse clickhouse-client < config/clickhouse/migrations/001_update.sql
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/jitesh523/Real-Time-FX-Market-Microstructure-Monitor/issues
- Documentation: See `docs/` directory
