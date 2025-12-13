# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Redis caching support for improved performance
- Health check endpoints (liveness, readiness, metrics)
- Pre-commit hooks for code quality
- CONTRIBUTING.md with development guidelines
- Comprehensive settings validation

### Changed
- Upgraded Docker images: Kafka 7.7.0, ClickHouse 24.11, Redis 7.4
- Upgraded Python from 3.11 to 3.12
- Consolidated requirements files into single requirements.txt
- Updated dependencies to latest stable versions
- Enhanced configuration with production mode support

### Fixed
- Improved error handling across all modules
- Better logging configuration

## [1.0.0] - 2024-12-13

### Added
- Initial release
- Real-time FX data ingestion with Kafka
- ClickHouse time-series storage
- Microstructure metrics (spread, depth, flow, volatility)
- Anomaly detection (Half-Space Trees, Z-score, quote stuffing, wash trading, spoofing)
- Isolation Forest anomaly detector
- Kyle's Lambda and Amihud Illiquidity metrics
- Lee-Ready trade classification
- Correlation analysis between currency pairs
- Alert notification system
- Real-time Streamlit dashboard
- Alpha Vantage API integration
- Performance optimizations (caching, connection pooling)
- Comprehensive testing suite
- Kubernetes deployment manifests
- CI/CD pipeline with GitHub Actions
- Documentation (README, API docs, deployment guide)

[Unreleased]: https://github.com/jitesh523/Real-Time-FX-Market-Microstructure-Monitor/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/jitesh523/Real-Time-FX-Market-Microstructure-Monitor/releases/tag/v1.0.0
