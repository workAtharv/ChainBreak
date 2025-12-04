# ChainBreak Troubleshooting Guide

This guide helps you resolve common issues with ChainBreak, especially when Neo4j is not working.

## 🚨 Frontend Not Working When Neo4j is Down

### Problem
Your frontend stops working when Neo4j database is unavailable.

### Solution
The system has been updated to handle Neo4j unavailability gracefully. Here are your options:

#### Option 1: Start in Limited Mode (Recommended)
```bash
# Start the API server without Neo4j dependency
python start_system.py --mode api-only
```

This will:
- ✅ Start the API server successfully
- ✅ Allow frontend to work for basic features
- ✅ Enable blockchain data fetching and visualization
- ⚠️ Disable advanced analysis features that require Neo4j

#### Option 2: Check System Status
```bash
# Check what's working and what's not
python health_check.py
```

This will show you:
- API server status
- Neo4j database status  
- Frontend accessibility
- Specific recommendations for fixing issues

#### Option 3: Use Docker (Full System)
```bash
# Start everything with Docker (requires Neo4j to be working)
python start_system.py --mode docker
```

## 🔧 Quick Fixes

### 1. Neo4j Connection Issues

**Symptoms:**
- Frontend shows "Offline" status
- API returns 503 errors
- Error messages about Neo4j connection

**Solutions:**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Start Neo4j if using Docker
docker-compose up -d neo4j

# Or start Neo4j manually
# Download from neo4j.com and start the service
```

### 2. API Server Won't Start

**Symptoms:**
- `python app.py` fails with Neo4j errors
- Import errors for Neo4j modules

**Solutions:**
```bash
# Install dependencies
pip install -r requirements.txt

# Start in limited mode (no Neo4j required)
python start_system.py --mode api-only

# Or set environment variable
export CHAINBREAK_NO_NEO4J=1
python app.py
```

### 3. Frontend Shows Errors

**Symptoms:**
- Frontend loads but shows connection errors
- API calls fail

**Solutions:**
```bash
# Check if API is running
curl http://localhost:5001/api/status

# Start API server
python start_system.py --mode api-only

# Check frontend accessibility
curl http://localhost:5001/frontend/index.html
```

## 📊 Understanding System Status

The frontend now shows different status indicators:

### 🟢 Online (Green)
- All systems working
- Neo4j available
- Full functionality

### 🟡 Limited (Yellow)  
- API working
- Neo4j unavailable
- Basic features only

### 🔴 Offline (Red)
- API server not responding
- Check if server is running

## 🛠️ Advanced Troubleshooting

### Check Logs
```bash
# View application logs
tail -f chainbreak.log

# View Docker logs
docker-compose logs -f chainbreak
docker-compose logs -f neo4j
```

### Test Individual Components
```bash
# Test API directly
curl -X POST http://localhost:5001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"}'

# Test Neo4j connection
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with driver.session() as session:
    result = session.run('RETURN 1 as test')
    print('Neo4j OK:', result.single())
driver.close()
"
```

### Configuration Issues
Check your `config.yaml`:
```yaml
neo4j:
  uri: "bolt://localhost:7687"  # Make sure this matches your Neo4j setup
  username: "neo4j"
  password: "password"          # Use your actual password
```

## 🎯 What Works Without Neo4j

When Neo4j is unavailable, these features still work:

✅ **Blockchain Data Fetching**
- Fetch transaction data from blockchain.info
- Save graphs as JSON files
- View transaction networks

✅ **Basic Visualization**
- Display transaction graphs
- Show address relationships
- Basic graph analysis

✅ **Frontend Interface**
- All UI components work
- Graph rendering
- File management

❌ **Advanced Features (Require Neo4j)**
- Anomaly detection
- Risk scoring
- Complex pattern analysis
- Database storage

## 🚀 Getting Started

1. **Quick Start (No Neo4j):**
   ```bash
   python start_system.py --mode api-only
   # Open http://localhost:5001/frontend/index.html
   ```

2. **Full System (With Neo4j):**
   ```bash
   # Start Neo4j first
   docker-compose up -d neo4j
   
   # Then start the full system
   python start_system.py --mode full
   ```

3. **Docker (Everything):**
   ```bash
   python start_system.py --mode docker
   ```

## 📞 Need Help?

1. Run the health check: `python health_check.py`
2. Check the logs: `tail -f chainbreak.log`
3. Verify Neo4j is running: `docker ps | grep neo4j`
4. Test API: `curl http://localhost:5001/api/status`

The system is now designed to be resilient to Neo4j failures while maintaining core functionality!
