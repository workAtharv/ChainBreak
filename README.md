# ChainBreak 🔗

**ChainBreak** is a prototype forensic tool designed to combat the growing threat of illicit cryptocurrency activity. It provides comprehensive blockchain analysis capabilities including anomaly detection, risk scoring, and network visualization.

## 🚀 Features

- **Data Ingestion**: BlockCypher API integration for blockchain data retrieval
- **Graph Database**: Neo4j for transaction network modeling
- **Anomaly Detection**: Advanced algorithms for detecting suspicious patterns
  - Layering detection
  - Smurfing detection
  - Volume anomaly detection
  - Temporal pattern analysis
- **Risk Scoring**: Comprehensive risk assessment framework
- **Visualization**: Network graphs, charts, and Gephi export
- **API Layer**: RESTful interface for system interaction
- **Performance Optimization**: Batch processing and caching

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   BlockCypher   │    │      Neo4j      │    │   ChainBreak    │
│      API        │───▶│   Graph DB      │◀───│    Engine       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Visualization │    │   Risk Scoring  │
                       │   & Export      │    │   & Analysis    │
                       └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Language**: Python 3.8+
- **Graph Database**: Neo4j Community Edition
- **Blockchain API**: BlockCypher
- **Data Processing**: pandas, numpy
- **Machine Learning**: scikit-learn (Isolation Forest)
- **Visualization**: Matplotlib, NetworkX, Gephi
- **Web Framework**: Flask
- **Containerization**: Docker & Docker Compose

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Neo4j Database (Community Edition)
- BlockCypher API key

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ChainBreak.git
   cd ChainBreak
   ```

2. **Configure BlockCypher API key**
   ```bash
   # Edit config.yaml and add your API key
   nano config.yaml
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the system**
   - API: http://localhost:5001
   - Neo4j Browser: http://localhost:7474

### Manual Installation

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Neo4j database**
   ```bash
   # Download and start Neo4j Community Edition
   # Default credentials: neo4j/password
   ```

3. **Configure the system**
   ```bash
   # Edit config.yaml with your settings
   nano config.yaml
   ```

4. **Run ChainBreak**
   ```bash
   # Standalone mode
   python app.py
   
   # API server mode
   python app.py --api
   
   # Analyze specific address
   python app.py --analyze 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
   ```

## 🔧 Configuration

Edit `config.yaml` to customize your setup:

```yaml
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "password"

blockcypher:
  api_key: "your_api_key_here"
  timeout: 30

analysis:
  time_window_hours: 24
  min_transactions: 5
  volume_threshold: 1000000

risk_scoring:
  volume_weight: 0.3
  frequency_weight: 0.2
  layering_weight: 0.3
  smurfing_weight: 0.2
```

## 📖 Usage

### Command Line Interface

```bash
# Analyze a Bitcoin address
python app.py --analyze 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

# Start API server
python app.py --api

# Run with custom config
python app.py --config custom_config.yaml

# Enable verbose logging
python app.py --verbose
```

### API Usage

#### Analyze Single Address
```bash
curl -X POST http://localhost:5001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "blockchain": "btc",
    "generate_visualizations": true
  }'
```

#### Batch Analysis
```bash
curl -X POST http://localhost:5001/api/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
      "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
    ],
    "blockchain": "btc"
  }'
```

#### Export to Gephi
```bash
curl "http://localhost:5001/api/export/gephi?address=1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
```

### Python API

```python
from src.chainbreak import ChainBreak

# Initialize ChainBreak
chainbreak = ChainBreak()

# Analyze an address
results = chainbreak.analyze_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

# Get risk score
risk_score = chainbreak.risk_scorer.calculate_address_risk_score("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

# Export to Gephi
export_file = chainbreak.export_network_to_gephi("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

# Clean up
chainbreak.close()
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_chainbreak.py

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## 📊 Analysis Capabilities

### Anomaly Detection

1. **Layering Detection**
   - Identifies multiple intermediate addresses in transaction chains
   - Detects complex layering patterns
   - Flags suspicious mixing service usage

2. **Smurfing Detection**
   - Detects rapid transactions to multiple addresses
   - Identifies structured smurfing patterns
   - Analyzes transaction timing anomalies

3. **Volume Anomaly Detection**
   - Uses Isolation Forest algorithm
   - Identifies unusual transaction volumes
   - Statistical pattern analysis

4. **Temporal Analysis**
   - Rapid transaction sequence detection
   - Unusual timing pattern identification
   - Interval analysis

### Risk Scoring

The system calculates comprehensive risk scores based on:

- **Volume Risk** (30%): Transaction volume relative to balance
- **Frequency Risk** (20%): Transaction frequency patterns
- **Layering Risk** (30%): Layering pattern detection
- **Smurfing Risk** (20%): Smurfing pattern detection

Risk levels: `VERY_LOW`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

### Visualization

- **Network Graphs**: Interactive transaction network visualization
- **Risk Heatmaps**: Visual risk score representation
- **Transaction Timelines**: Temporal transaction analysis
- **Gephi Export**: Professional network analysis tool integration

## 🔍 Example Analysis

```python
# Example: Analyzing a suspicious address
address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

results = chainbreak.analyze_address(address)

print(f"Risk Level: {results['risk_score']['risk_level']}")
print(f"Risk Score: {results['risk_score']['total_risk_score']:.3f}")
print(f"Layering Patterns: {len(results['anomalies']['layering_patterns'])}")
print(f"Smurfing Patterns: {len(results['anomalies']['smurfing_patterns'])}")
print(f"Volume Anomalies: {len(results['anomalies']['volume_anomalies'])}")
```

## 🚀 Performance & Scalability

- **Batch Processing**: Efficient handling of large datasets
- **Multi-threading**: Parallel processing capabilities
- **Caching**: In-memory caching for frequently accessed data
- **Database Optimization**: Neo4j query optimization and indexing
- **Memory Management**: Configurable memory limits and cleanup

## 🔒 Security Considerations

- **API Key Management**: Secure storage of BlockCypher API keys
- **Database Security**: Neo4j authentication and access control
- **Input Validation**: Comprehensive data validation and sanitization
- **Error Handling**: Secure error messages without information leakage

## 📈 Monitoring & Logging

- **Comprehensive Logging**: Detailed operation logging
- **Performance Metrics**: Operation timing and resource usage
- **Health Checks**: System status monitoring
- **Error Tracking**: Detailed error logging and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **BlockCypher**: Blockchain data API
- **Neo4j**: Graph database technology
- **Open Source Community**: Various Python libraries and tools

## 📞 Support

For support and questions:

- **Issues**: [GitHub Issues](https://github.com/yourusername/ChainBreak/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/ChainBreak/wiki)
- **Email**: support@chainbreak.com

## 🔮 Future Enhancements

- Multi-blockchain support (Ethereum, Monero)
- Real-time streaming data processing
- Advanced machine learning models
- Web dashboard interface
- Chainalysis API integration
- Performance optimization enhancements

---

**ChainBreak** - Unraveling the blockchain, one transaction at a time. 🔗⚡
