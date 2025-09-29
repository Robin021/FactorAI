# Production Deployment Guide

This guide covers the complete production deployment setup for the TradingAgents platform.

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured (for SSL certificates)
- Minimum 4GB RAM, 2 CPU cores
- 50GB+ disk space
- Ubuntu 20.04+ or similar Linux distribution

## Quick Production Setup

### 1. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd TradingAgents-CN

# Copy production environment template
cp .env.production .env

# Edit configuration (IMPORTANT!)
nano .env
```

### 2. Configure Environment Variables

Edit `.env` file and update these critical values:

```bash
# Security (CHANGE THESE!)
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production

# Database passwords
MONGODB_PASSWORD=your-secure-mongodb-password
REDIS_PASSWORD=your-secure-redis-password

# API Keys
OPENAI_API_KEY=your-openai-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
# ... other API keys
```

### 3. SSL Certificate Setup

#### Option A: Self-Signed Certificate (Development/Testing)

```bash
./scripts/ssl/generate-ssl-cert.sh yourdomain.com
```

#### Option B: Let's Encrypt Certificate (Production)

```bash
./scripts/ssl/setup-letsencrypt.sh yourdomain.com admin@yourdomain.com
```

### 4. Deploy to Production

```bash
# Build and deploy
./scripts/docker/deploy-production.sh

# Or manually
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Verify Deployment

```bash
# Check service health
./scripts/docker/health-check.sh

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Advanced Configuration

### SSL Certificate Management

#### Automatic Renewal Setup

Add to crontab for automatic certificate renewal:

```bash
# Edit crontab
crontab -e

# Add this line for daily renewal check
0 2 * * * /path/to/TradingAgents-CN/scripts/ssl/renew-letsencrypt.sh yourdomain.com
```

#### Manual Certificate Renewal

```bash
./scripts/ssl/renew-letsencrypt.sh yourdomain.com
```

### Monitoring Setup

Enable monitoring services:

```bash
# Start with monitoring
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Access monitoring dashboards
# Prometheus: http://yourdomain.com:9090
# Grafana: http://yourdomain.com:3001 (admin/admin)
```

### Log Aggregation

Enable centralized logging:

```bash
# Start with logging
docker-compose -f docker-compose.prod.yml --profile logging up -d
```

### Database Backup Setup

#### Automated Backups

Add to crontab for daily backups:

```bash
# Edit crontab
crontab -e

# Add these lines
0 1 * * * /path/to/TradingAgents-CN/scripts/backup/backup-mongodb.sh
0 1 * * * /path/to/TradingAgents-CN/scripts/backup/backup-redis.sh
```

#### Manual Backups

```bash
# Backup MongoDB
./scripts/backup/backup-mongodb.sh

# Backup Redis
./scripts/backup/backup-redis.sh
```

#### Restore from Backup

```bash
# List available backups
ls -la backups/mongodb/
ls -la backups/redis/

# Restore MongoDB
./scripts/backup/restore-mongodb.sh mongodb_backup_20240101_120000.tar.gz

# Restore Redis
./scripts/backup/restore-redis.sh redis_backup_20240101_120000.rdb
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Install UFW (Ubuntu)
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow monitoring (optional, restrict to specific IPs)
sudo ufw allow from YOUR_MONITORING_IP to any port 9090
sudo ufw allow from YOUR_MONITORING_IP to any port 3001

# Enable firewall
sudo ufw enable
```

### 2. Docker Security

```bash
# Create docker group and add user
sudo groupadd docker
sudo usermod -aG docker $USER

# Restart Docker daemon with security options
sudo systemctl edit docker

# Add these lines:
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --userland-proxy=false --iptables=false
```

### 3. System Updates

```bash
# Regular system updates
sudo apt update && sudo apt upgrade -y

# Docker updates
sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io
```

## Performance Optimization

### 1. System Tuning

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize kernel parameters
echo "net.core.somaxconn = 65536" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 2. Docker Resource Limits

Edit `docker-compose.prod.yml` to add resource limits:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### 3. Database Optimization

#### MongoDB Configuration

Create `config/mongodb/mongod.conf`:

```yaml
storage:
  dbPath: /data/db
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 0.0.0.0

processManagement:
  timeZoneInfo: /usr/share/zoneinfo
```

#### Redis Optimization

Optimize Redis configuration in docker-compose:

```yaml
redis:
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} --maxmemory 1gb --maxmemory-policy allkeys-lru --tcp-keepalive 60
```

## Troubleshooting

### Common Issues

#### 1. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Test SSL configuration
curl -I https://yourdomain.com

# Check nginx configuration
docker-compose exec frontend nginx -t
```

#### 2. Database Connection Issues

```bash
# Check MongoDB connection
docker-compose exec mongodb mongo --eval "db.adminCommand('ping')"

# Check Redis connection
docker-compose exec redis redis-cli ping

# View database logs
docker-compose logs mongodb
docker-compose logs redis
```

#### 3. Performance Issues

```bash
# Check resource usage
docker stats

# Check system resources
htop
df -h
free -h

# Check application logs
docker-compose logs backend | grep ERROR
```

#### 4. Network Issues

```bash
# Check port availability
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# Test internal connectivity
docker-compose exec frontend ping backend
docker-compose exec backend ping mongodb
```

### Log Analysis

#### Application Logs

```bash
# Backend logs
docker-compose logs -f backend

# Frontend/Nginx logs
docker-compose logs -f frontend

# Database logs
docker-compose logs -f mongodb redis
```

#### System Logs

```bash
# Docker daemon logs
sudo journalctl -u docker.service -f

# System logs
sudo journalctl -f
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Check service health
- Monitor disk usage
- Review error logs

#### Weekly
- Update system packages
- Clean up old Docker images
- Review security logs

#### Monthly
- Update Docker images
- Review and rotate logs
- Performance analysis
- Security audit

### Maintenance Scripts

```bash
# System cleanup
docker system prune -f
docker volume prune -f

# Log rotation
sudo logrotate -f /etc/logrotate.conf

# Update containers
docker-compose pull
docker-compose up -d
```

## Scaling

### Horizontal Scaling

#### Load Balancer Setup

Use nginx upstream for multiple backend instances:

```nginx
upstream backend {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
}
```

#### Database Scaling

##### MongoDB Replica Set

```yaml
mongodb-primary:
  image: mongo:7.0
  command: mongod --replSet rs0 --bind_ip_all

mongodb-secondary:
  image: mongo:7.0
  command: mongod --replSet rs0 --bind_ip_all

mongodb-arbiter:
  image: mongo:7.0
  command: mongod --replSet rs0 --bind_ip_all
```

##### Redis Cluster

```yaml
redis-master:
  image: redis:7.2-alpine
  command: redis-server --appendonly yes

redis-slave:
  image: redis:7.2-alpine
  command: redis-server --slaveof redis-master 6379 --appendonly yes
```

### Vertical Scaling

Increase resource limits in docker-compose:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

## Disaster Recovery

### Backup Strategy

1. **Database Backups**: Daily automated backups
2. **Configuration Backups**: Version controlled
3. **SSL Certificates**: Backed up with renewal scripts
4. **Application Data**: Regular snapshots

### Recovery Procedures

#### Complete System Recovery

```bash
# 1. Restore from backups
./scripts/backup/restore-mongodb.sh latest_backup.tar.gz
./scripts/backup/restore-redis.sh latest_backup.rdb

# 2. Restore SSL certificates
cp backup/ssl/* nginx/ssl/

# 3. Restore configuration
cp backup/.env .env

# 4. Restart services
docker-compose -f docker-compose.prod.yml up -d
```

#### Partial Recovery

```bash
# Database only
./scripts/backup/restore-mongodb.sh specific_backup.tar.gz

# Configuration only
cp backup/.env .env
docker-compose restart backend
```

## Support and Monitoring

### Health Monitoring

- **Application Health**: `/health` endpoints
- **Database Health**: Connection tests
- **SSL Health**: Certificate expiration monitoring
- **System Health**: Resource usage monitoring

### Alerting

Configure alerts for:
- Service downtime
- High resource usage
- SSL certificate expiration
- Database connection failures
- High error rates

### Contact Information

For production issues:
- Check logs first
- Review monitoring dashboards
- Contact system administrator
- Escalate to development team if needed