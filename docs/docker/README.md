# Docker Deployment Guide

This guide covers the Docker containerization setup for the TradingAgents platform.

## Overview

The TradingAgents platform uses a microservices architecture with the following components:

- **Frontend**: React application served by Nginx
- **Backend**: FastAPI application with Uvicorn
- **Database**: MongoDB for data persistence
- **Cache**: Redis for caching and session storage

## Quick Start

### Development Environment

1. **Setup environment**:
   ```bash
   cp .env.development .env
   # Edit .env with your configuration
   ```

2. **Build and start services**:
   ```bash
   ./scripts/docker/build-development.sh
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Production Environment

1. **Setup environment**:
   ```bash
   cp .env.production .env
   # Edit .env with your production configuration
   ```

2. **Deploy to production**:
   ```bash
   ./scripts/docker/deploy-production.sh
   ```

3. **Access the application**:
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key | `your-secret-key` |
| `JWT_SECRET_KEY` | JWT signing key | `your-jwt-secret` |
| `MONGODB_PASSWORD` | MongoDB password | `secure-password` |
| `REDIS_PASSWORD` | Redis password | `secure-password` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_CONCURRENT_ANALYSES` | Max concurrent analyses | `5` |
| `ANALYSIS_TIMEOUT_MINUTES` | Analysis timeout | `30` |

## Docker Commands

### Build Commands

```bash
# Build development images
docker-compose -f docker-compose.dev.yml build

# Build production images
docker-compose build

# Build specific service
docker-compose build backend
```

### Run Commands

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Start production environment
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up -d backend
```

### Management Commands

```bash
# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart service
docker-compose restart backend
```

### Maintenance Commands

```bash
# Check service health
./scripts/docker/health-check.sh

# View container status
docker-compose ps

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

# View resource usage
docker stats
```

## Service Configuration

### Frontend (Nginx)

- **Port**: 80 (production), 3000 (development)
- **Configuration**: `frontend/nginx.conf`
- **Features**:
  - Static file serving
  - API proxy to backend
  - WebSocket proxy
  - Gzip compression
  - Security headers

### Backend (FastAPI)

- **Port**: 8000
- **Workers**: 4 (production), 1 (development)
- **Features**:
  - Auto-reload (development)
  - Health checks
  - Structured logging
  - Security middleware

### Database Services

#### MongoDB
- **Port**: 27017
- **Authentication**: Username/password
- **Persistence**: Docker volume
- **Initialization**: `scripts/mongo-init.js`

#### Redis
- **Port**: 6379
- **Authentication**: Password (production)
- **Persistence**: Docker volume
- **Configuration**: Append-only file enabled

## Security Considerations

### Production Security

1. **Change default passwords**:
   - Update `MONGODB_PASSWORD`
   - Update `REDIS_PASSWORD`
   - Update `SECRET_KEY` and `JWT_SECRET_KEY`

2. **Network security**:
   - Use internal Docker networks
   - Expose only necessary ports
   - Configure firewall rules

3. **Container security**:
   - Run as non-root user
   - Use multi-stage builds
   - Minimal base images
   - Regular security updates

### Development Security

- Use separate credentials for development
- Don't use production secrets in development
- Regularly update dependencies

## Monitoring and Logging

### Health Checks

All services include health checks:

```bash
# Check all services
./scripts/docker/health-check.sh

# Manual health checks
curl http://localhost/health          # Frontend
curl http://localhost:8000/health     # Backend
```

### Logging

Logs are configured with rotation:

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# View logs with timestamps
docker-compose logs -f -t
```

### Monitoring

Monitor resource usage:

```bash
# Container stats
docker stats

# System resource usage
docker system df

# Container processes
docker-compose top
```

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check port usage
   netstat -tulpn | grep :80
   netstat -tulpn | grep :8000
   ```

2. **Permission issues**:
   ```bash
   # Fix log directory permissions
   sudo chown -R $USER:$USER logs/
   ```

3. **Database connection issues**:
   ```bash
   # Check MongoDB logs
   docker-compose logs mongodb
   
   # Test MongoDB connection
   docker-compose exec mongodb mongo --eval "db.adminCommand('ping')"
   ```

4. **Memory issues**:
   ```bash
   # Check memory usage
   docker stats --no-stream
   
   # Increase Docker memory limit
   # Docker Desktop: Settings > Resources > Memory
   ```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart with debug logs
docker-compose restart backend
docker-compose logs -f backend
```

## Backup and Recovery

### Database Backup

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /data/backup

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v tradingagents_mongodb_data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz /data
docker run --rm -v tradingagents_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz /data
```

## Performance Tuning

### Production Optimizations

1. **Backend scaling**:
   ```yaml
   # In docker-compose.yml
   backend:
     deploy:
       replicas: 3
   ```

2. **Database optimization**:
   - Configure MongoDB indexes
   - Tune Redis memory settings
   - Use connection pooling

3. **Frontend optimization**:
   - Enable Nginx caching
   - Configure CDN
   - Optimize bundle size

### Resource Limits

```yaml
# Example resource limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

## Updates and Maintenance

### Updating Services

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Rolling update (zero downtime)
docker-compose up -d --no-deps backend
```

### Cleanup

```bash
# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Complete cleanup
docker system prune -af
```