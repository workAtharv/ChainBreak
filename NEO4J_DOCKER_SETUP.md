# ChainBreak Neo4j Docker Setup

This guide explains how to set up and run ChainBreak with Neo4j using Docker containers.

## Prerequisites

- Docker Desktop installed and running
- Python 3.11+ (for local development)
- At least 4GB RAM available for Docker

## Quick Start

### 1. Start Neo4j Database

```bash
# Start only Neo4j
python start_neo4j_docker.py
# Choose option 1

# Or use docker-compose directly
docker-compose -f docker-compose-neo4j.yml up -d neo4j
```

### 2. Start ChainBreak Application

```bash
# Start Neo4j + ChainBreak App
python start_neo4j_docker.py
# Choose option 2

# Or use docker-compose directly
docker-compose -f docker-compose-neo4j.yml --profile app up -d
```

### 3. Access Services

- **Neo4j Browser**: http://localhost:7474
- **ChainBreak API**: http://localhost:5001
- **ChainBreak Frontend**: http://localhost:3000

**Credentials:**
- Username: `neo4j`
- Password: `password`

## Docker Services

### Neo4j Database
- **Image**: neo4j:5.15-community
- **Ports**: 7474 (HTTP), 7687 (Bolt)
- **Plugins**: APOC, Graph Data Science
- **Memory**: 2GB heap, 1GB page cache

### ChainBreak Application
- **Ports**: 5001 (API), 3000 (Frontend)
- **Environment**: Production-ready with security
- **Dependencies**: Waits for Neo4j to be healthy

### Neo4j Browser (Optional)
- **Port**: 7475
- **Purpose**: Alternative Neo4j web interface

## Configuration

### Environment Variables

```bash
# Neo4j Configuration
NEO4J_AUTH=neo4j/password
NEO4J_PLUGINS=["apoc", "graph-data-science"]

# ChainBreak Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

### Docker Compose Profiles

- **Default**: Only Neo4j database
- **app**: Neo4j + ChainBreak application
- **browser**: Neo4j + Neo4j Browser

## Management Commands

### Using the Management Script

```bash
python start_neo4j_docker.py
```

Options:
1. Start Neo4j only
2. Start Neo4j + ChainBreak App
3. Start Neo4j + ChainBreak App + Browser
4. Stop all services
5. Show status
6. Test Neo4j connection
7. Exit

### Using Docker Compose Directly

```bash
# Start Neo4j only
docker-compose -f docker-compose-neo4j.yml up -d neo4j

# Start with ChainBreak app
docker-compose -f docker-compose-neo4j.yml --profile app up -d

# Start with browser
docker-compose -f docker-compose-neo4j.yml --profile browser up -d

# Stop all services
docker-compose -f docker-compose-neo4j.yml down

# View logs
docker-compose -f docker-compose-neo4j.yml logs -f

# Check status
docker-compose -f docker-compose-neo4j.yml ps
```

## Data Persistence

Data is persisted using Docker volumes:

- `neo4j_data`: Database files
- `neo4j_logs`: Log files
- `neo4j_import`: Import directory
- `neo4j_plugins`: Plugin files
- `neo4j_conf`: Configuration files

## Troubleshooting

### Neo4j Not Starting

1. Check Docker is running:
   ```bash
   docker info
   ```

2. Check available memory:
   ```bash
   docker system df
   ```

3. View Neo4j logs:
   ```bash
   docker-compose -f docker-compose-neo4j.yml logs neo4j
   ```

### Connection Issues

1. Test Neo4j connection:
   ```bash
   python start_neo4j_docker.py
   # Choose option 6
   ```

2. Check if ports are available:
   ```bash
   netstat -an | grep :7474
   netstat -an | grep :7687
   ```

### Performance Issues

1. Increase Docker memory allocation
2. Adjust Neo4j memory settings in docker-compose-neo4j.yml:
   ```yaml
   environment:
     - NEO4J_dbms_memory_heap_max__size=4G
     - NEO4J_dbms_memory_pagecache_size=2G
   ```

## Development

### Building Custom Images

```bash
# Build ChainBreak app image
docker build -t chainbreak-app .

# Build with specific target
docker build --target development -t chainbreak-dev .
docker build --target production -t chainbreak-prod .
```

### Running Tests

```bash
# Run tests in container
docker-compose -f docker-compose-neo4j.yml run --rm chainbreak-app pytest

# Run with coverage
docker-compose -f docker-compose-neo4j.yml run --rm chainbreak-app pytest --cov=src
```

## Security Notes

- Default credentials are for development only
- Change passwords in production
- Use Docker secrets for sensitive data
- Enable SSL/TLS for production deployments

## Monitoring

### Health Checks

- Neo4j: Built-in health check every 30s
- ChainBreak App: HTTP health check on /api/status

### Logs

```bash
# View all logs
docker-compose -f docker-compose-neo4j.yml logs -f

# View specific service logs
docker-compose -f docker-compose-neo4j.yml logs -f neo4j
docker-compose -f docker-compose-neo4j.yml logs -f chainbreak-app
```

## Backup and Restore

### Backup Neo4j Data

```bash
# Create backup
docker-compose -f docker-compose-neo4j.yml exec neo4j neo4j-admin dump --database=neo4j --to=/var/lib/neo4j/import/backup.dump

# Copy backup file
docker cp chainbreak-neo4j:/var/lib/neo4j/import/backup.dump ./backup.dump
```

### Restore Neo4j Data

```bash
# Copy backup file to container
docker cp ./backup.dump chainbreak-neo4j:/var/lib/neo4j/import/backup.dump

# Restore database
docker-compose -f docker-compose-neo4j.yml exec neo4j neo4j-admin load --database=neo4j --from=/var/lib/neo4j/import/backup.dump --force
```

## Production Deployment

For production deployment:

1. Change default passwords
2. Enable SSL/TLS
3. Use Docker secrets
4. Set up monitoring and alerting
5. Configure backup strategies
6. Use external volumes for data persistence

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Docker and Neo4j logs
- Ensure all prerequisites are met
- Verify network connectivity between containers
