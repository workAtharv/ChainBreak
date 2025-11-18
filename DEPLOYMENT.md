# ChainBreak Deployment Guide

Complete guide for deploying ChainBreak in production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Application Deployment](#application-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Health Checks](#health-checks)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **Docker**: 20.10+ (for Neo4j)
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Disk Space**: 10GB+ free space

### Required Software

```bash
# Install Python 3.8+
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Install Node.js 16+
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/ChainBreak.git
cd ChainBreak
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Critical Environment Variables:**

```env
# Production settings
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<generate-random-secret-key>

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secure-password>

# Security
CORS_ORIGINS=https://yourdomain.com
```

## Database Configuration

### Start Neo4j with Docker

```bash
# Start Neo4j container
docker-compose up -d neo4j

# Wait for Neo4j to initialize (30-60 seconds)
docker-compose logs -f neo4j

# Test connection
python health_check.py
```

### Initialize Database Schema

The schema is automatically created on first run, but you can manually initialize:

```bash
python -c "from src.chainbreak import ChainBreak; cb = ChainBreak(); print('Database initialized')"
```

### Backup and Restore

```bash
# Backup Neo4j data
docker exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j.dump

# Restore from backup
docker exec neo4j neo4j-admin load --from=/backups/neo4j.dump --database=neo4j --force
```

## Application Deployment

### Development Mode

```bash
# Start backend
python app.py --api

# In another terminal, start frontend
cd frontend
npm install
npm start
```

### Production Mode

#### Backend Deployment

```bash
# Install production server (gunicorn)
pip install gunicorn eventlet

# Start with gunicorn
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --worker-class eventlet \
         --timeout 120 \
         --access-logfile logs/access.log \
         --error-logfile logs/error.log \
         'src.api:app'
```

#### Using Systemd Service

Create `/etc/systemd/system/chainbreak.service`:

```ini
[Unit]
Description=ChainBreak API Server
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=chainbreak
WorkingDirectory=/opt/chainbreak
Environment="PATH=/opt/chainbreak/venv/bin"
ExecStart=/opt/chainbreak/venv/bin/gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --worker-class eventlet \
    --timeout 120 \
    'src.api:app'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable chainbreak
sudo systemctl start chainbreak
sudo systemctl status chainbreak
```

## Frontend Deployment

### Build for Production

```bash
cd frontend
npm install
npm run build
```

### Deploy with Nginx

Install Nginx:

```bash
sudo apt install nginx
```

Configure Nginx (`/etc/nginx/sites-available/chainbreak`):

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /opt/chainbreak/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/chainbreak /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

## Health Checks

### Run Comprehensive Health Check

```bash
# Test all endpoints
python test_endpoints.py

# Check specific URL
python test_endpoints.py --url https://yourdomain.com

# With custom output
python test_endpoints.py --output production_health_check.json
```

### Automated Monitoring

Add to cron for regular checks:

```bash
# Edit crontab
crontab -e

# Add health check every 5 minutes
*/5 * * * * cd /opt/chainbreak && /opt/chainbreak/venv/bin/python test_endpoints.py >> /var/log/chainbreak_health.log 2>&1
```

### Monitoring Endpoints

- **System Status**: `GET /api/status`
- **Backend Mode**: `GET /api/mode`
- **Statistics**: `GET /api/statistics`
- **Threat Intel Status**: `GET /api/threat-intelligence/status`

## Monitoring

### Application Logs

```bash
# View application logs
tail -f logs/chainbreak.log

# View access logs
tail -f logs/access.log

# View error logs
tail -f logs/error.log

# Neo4j logs
docker logs -f neo4j
```

### Performance Monitoring

#### Using Prometheus (Optional)

Install Prometheus:

```bash
# Add prometheus endpoint in your code
pip install prometheus-flask-exporter

# Start Prometheus
docker run -d \
    --name prometheus \
    -p 9090:9090 \
    -v /opt/chainbreak/prometheus.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus
```

Example `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'chainbreak'
    static_configs:
      - targets: ['localhost:5000']
```

## Troubleshooting

### Common Issues

#### Backend won't start

```bash
# Check if port is already in use
sudo lsof -i :5000

# Check logs
tail -f logs/error.log

# Verify dependencies
pip list | grep -E "flask|neo4j"
```

#### Neo4j connection fails

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs neo4j

# Test connection
cypher-shell -u neo4j -p <password> "RETURN 1;"
```

#### Frontend build fails

```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+

# Build with verbose output
npm run build --verbose
```

#### WebSocket not connecting

```bash
# Check if WebSocket endpoint is accessible
curl -i -N \
    -H "Connection: Upgrade" \
    -H "Upgrade: websocket" \
    http://localhost:5000/socket.io/

# Check firewall rules
sudo ufw status
```

### Debug Mode

Enable detailed logging:

```bash
# Set in .env
FLASK_DEBUG=True
LOG_LEVEL=DEBUG

# Restart service
sudo systemctl restart chainbreak
```

### Performance Issues

```bash
# Check system resources
htop

# Check database performance
docker exec neo4j cypher-shell -u neo4j -p <password> "CALL dbms.listQueries();"

# Optimize Neo4j memory
docker exec neo4j cat /var/lib/neo4j/conf/neo4j.conf | grep heap
```

## Security Checklist

- [ ] Change default Neo4j password
- [ ] Set strong SECRET_KEY in .env
- [ ] Enable HTTPS with SSL certificate
- [ ] Configure firewall (ufw/iptables)
- [ ] Set up rate limiting
- [ ] Enable security headers in Nginx
- [ ] Regular security updates
- [ ] Backup database regularly
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables (never commit .env)

## Scaling

### Horizontal Scaling

Use load balancer (e.g., HAProxy):

```bash
frontend http_front
    bind *:80
    default_backend http_back

backend http_back
    balance roundrobin
    server server1 127.0.0.1:5000 check
    server server2 127.0.0.1:5001 check
    server server3 127.0.0.1:5002 check
```

### Database Scaling

- Use Neo4j Enterprise for clustering
- Set up read replicas
- Implement caching layer (Redis)

## Backup Strategy

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/chainbreak"

# Backup Neo4j
docker exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j_${DATE}.dump

# Backup data directory
tar -czf ${BACKUP_DIR}/data_${DATE}.tar.gz data/

# Backup configuration
tar -czf ${BACKUP_DIR}/config_${DATE}.tar.gz config.yaml .env

# Keep last 7 days
find ${BACKUP_DIR} -name "*.dump" -mtime +7 -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +7 -delete
```

## Support

For issues and support:
- GitHub Issues: https://github.com/yourorg/ChainBreak/issues
- Documentation: https://docs.chainbreak.io
- Email: support@chainbreak.io
