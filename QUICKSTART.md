# ChainBreak Quick Start Guide 🚀

Get ChainBreak up and running in minutes with this quick start guide.

## ⚡ Quick Start (5 minutes)

### 1. Prerequisites Check

Make sure you have:
- Python 3.8+ installed
- Docker and Docker Compose (for containerized setup)
- BlockCypher API key (free at [blockcypher.com](https://www.blockcypher.com/))

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ChainBreak.git
cd ChainBreak

# Copy and edit configuration
cp config.yaml.example config.yaml
# Edit config.yaml with your BlockCypher API key
```

### 3. Start with Docker (Recommended)

```bash
# Start Neo4j and ChainBreak
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chainbreak
```

### 4. Test the System

```bash
# Check API status
curl http://localhost:5001/api/status

# Analyze a test address
curl -X POST http://localhost:5001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"}'
```

## 🔧 Manual Setup

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Start Neo4j (download from neo4j.com)
# Default credentials: neo4j/password
```

### 2. Configure

Edit `config.yaml`:
```yaml
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "password"

blockcypher:
  api_key: "your_actual_api_key_here"
```

### 3. Run

```bash
# Standalone mode
python app.py

# API server mode
python app.py --api

# Analyze specific address
python app.py --analyze 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
```

## 📱 Access Points

- **API**: http://localhost:5001
- **API Docs**: http://localhost:5001/ (built-in documentation)
- **Neo4j Browser**: http://localhost:7474 (username: neo4j, password: password)

## 🧪 First Analysis

### Using the API

```bash
# Analyze a Bitcoin address
curl -X POST http://localhost:5001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "blockchain": "btc",
    "generate_visualizations": true
  }'
```

### Using Python

```python
from src.chainbreak import ChainBreak

# Initialize
chainbreak = ChainBreak()

# Analyze
results = chainbreak.analyze_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

# View results
print(f"Risk Level: {results['risk_score']['risk_level']}")
print(f"Risk Score: {results['risk_score']['total_risk_score']:.3f}")

# Clean up
chainbreak.close()
```

### Using Command Line

```bash
# Analyze with CLI
python app.py --analyze 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

# Run example
python examples/basic_analysis.py
```

## 📊 Understanding Results

### Risk Levels
- **VERY_LOW** (0.0-0.2): Normal activity
- **LOW** (0.2-0.4): Minor concerns
- **MEDIUM** (0.4-0.6): Moderate risk
- **HIGH** (0.6-0.8): High risk
- **CRITICAL** (0.8-1.0): Immediate attention required

### Anomaly Types
- **Layering**: Multiple intermediate addresses
- **Smurfing**: Rapid transactions to many addresses
- **Volume**: Unusual transaction amounts
- **Temporal**: Suspicious timing patterns

## 🚨 Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   ```bash
   # Check if Neo4j is running
   docker-compose ps neo4j
   
   # Check Neo4j logs
   docker-compose logs neo4j
   ```

2. **BlockCypher API Errors**
   - Verify API key in `config.yaml`
   - Check API rate limits
   - Ensure internet connectivity

3. **Port Already in Use**
   ```bash
   # Change ports in docker-compose.yml
   ports:
     - "5001:5001"  # Use port 5001 instead
   ```

4. **Memory Issues**
   ```bash
   # Increase Neo4j memory in docker-compose.yml
   environment:
     - NEO4J_dbms_memory_heap_max__size=4G
   ```

### Debug Mode

```bash
# Enable verbose logging
python app.py --verbose

# Check logs
tail -f chainbreak.log

# Docker logs
docker-compose logs -f chainbreak
```

## 📈 Next Steps

1. **Explore the API**: Visit http://localhost:5001 for interactive documentation
2. **Run Examples**: Try `python examples/basic_analysis.py`
3. **Custom Analysis**: Modify `config.yaml` for your use case
4. **Scale Up**: Adjust Neo4j memory and ChainBreak batch sizes
5. **Integration**: Use the API in your own applications

## 🆘 Need Help?

- **Documentation**: [README.md](README.md)
- **Examples**: [examples/](examples/) directory
- **Tests**: [tests/](tests/) directory
- **Issues**: GitHub Issues page

## 🎯 Success Criteria

You've successfully set up ChainBreak when you can:

✅ Start the system with `docker-compose up -d`  
✅ Access the API at http://localhost:5001  
✅ Run a basic analysis on a Bitcoin address  
✅ View results with risk scores and anomaly detection  
✅ Export networks to Gephi format  

---

**Happy analyzing! 🔗⚡**

For detailed information, see the full [README.md](README.md).
