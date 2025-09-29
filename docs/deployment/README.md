# 部署和运维指南

## 概述

本文档提供股票分析平台的完整部署和运维指南，包括开发环境、测试环境和生产环境的部署方案。

## 系统要求

### 硬件要求

**最低配置:**
- CPU: 4核心
- 内存: 8GB RAM
- 存储: 100GB SSD
- 网络: 100Mbps

**推荐配置:**
- CPU: 8核心
- 内存: 16GB RAM
- 存储: 500GB SSD
- 网络: 1Gbps

### 软件要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS 12+
- **Python**: 3.9+
- **Node.js**: 18+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **PostgreSQL**: 13+
- **Redis**: 6.0+
- **Nginx**: 1.20+

## 快速部署

### 使用 Docker Compose (推荐)

1. **克隆项目**
```bash
git clone https://github.com/your-org/stock-analysis-platform.git
cd stock-analysis-platform
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **初始化数据库**
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

5. **访问应用**
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- 管理界面: http://localhost:8000/admin

## 环境配置

### 环境变量配置

创建 `.env` 文件：

```bash
# 应用配置
APP_NAME=股票分析平台
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/stock_analysis
REDIS_URL=redis://localhost:6379/0

# LLM 配置
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 数据源配置
TUSHARE_TOKEN=your-tushare-token
FINNHUB_API_KEY=your-finnhub-key

# 安全配置
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
JWT_SECRET_KEY=your-jwt-secret
JWT_EXPIRE_MINUTES=60

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/stock-analysis/app.log

# 缓存配置
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Docker Compose 配置

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  # 数据库
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: stock_analysis
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 缓存
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/stock_analysis
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend:/app
      - ./logs:/var/log/stock-analysis
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api/v1
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
```

## 生产环境部署

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx

# 启动 Docker 服务
sudo systemctl enable docker
sudo systemctl start docker

# 添加用户到 docker 组
sudo usermod -aG docker $USER
```

### 2. SSL 证书配置

```bash
# 使用 Let's Encrypt 获取 SSL 证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 设置自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Nginx 配置

`nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # HTTP 重定向到 HTTPS
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS 配置
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        # 前端静态文件
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API 接口
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket 支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # 静态文件缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    }
}
```

### 4. 数据库优化

PostgreSQL 配置优化 (`postgresql.conf`):

```ini
# 内存配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# 连接配置
max_connections = 100
listen_addresses = '*'

# 日志配置
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'all'
log_min_duration_statement = 1000

# 性能配置
checkpoint_completion_target = 0.7
wal_buffers = 16MB
default_statistics_target = 100
```

## 监控和日志

### 1. 应用监控

使用 Prometheus + Grafana 进行监控：

`docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources

  node-exporter:
    image: prom/node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro

volumes:
  prometheus_data:
  grafana_data:
```

### 2. 日志管理

使用 ELK Stack 进行日志管理：

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

## 备份和恢复

### 1. 数据库备份

创建备份脚本 `scripts/backup.sh`:

```bash
#!/bin/bash

# 配置
DB_NAME="stock_analysis"
DB_USER="postgres"
BACKUP_DIR="/var/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/backup_$DATE.sql

# 删除 7 天前的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

### 2. 自动备份

设置 cron 任务：

```bash
# 编辑 crontab
crontab -e

# 添加每日备份任务
0 2 * * * /path/to/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### 3. 数据恢复

```bash
# 恢复数据库
gunzip -c /var/backups/postgres/backup_20240101_020000.sql.gz | psql -h localhost -U postgres -d stock_analysis
```

## 性能优化

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_analysis_stock_code ON analysis_records(stock_code);
CREATE INDEX idx_analysis_created_at ON analysis_records(created_at);
CREATE INDEX idx_analysis_status ON analysis_records(status);

-- 分析表统计信息
ANALYZE analysis_records;

-- 查看慢查询
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### 2. 缓存优化

Redis 配置优化：

```ini
# redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. 应用优化

```python
# 后端性能优化配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# 数据库连接池
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    }
}
```

## 安全配置

### 1. 防火墙配置

```bash
# 配置 UFW 防火墙
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 2. 应用安全

```python
# Django 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 故障排除

### 1. 常见问题

**问题**: 数据库连接失败
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready -U postgres

# 查看数据库日志
docker-compose logs postgres
```

**问题**: 内存不足
```bash
# 检查内存使用
free -h
docker stats

# 清理 Docker 资源
docker system prune -a
```

**问题**: API 响应慢
```bash
# 检查 API 性能
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/health"

# 查看应用日志
docker-compose logs backend
```

### 2. 健康检查

创建健康检查脚本 `scripts/health-check.sh`:

```bash
#!/bin/bash

# 检查服务状态
services=("postgres" "redis" "backend" "frontend" "nginx")

for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "✓ $service is running"
    else
        echo "✗ $service is not running"
        exit 1
    fi
done

# 检查 API 健康状态
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✓ API is healthy"
else
    echo "✗ API is not healthy"
    exit 1
fi

echo "All services are healthy"
```

## 升级和维护

### 1. 应用升级

```bash
# 备份数据
./scripts/backup.sh

# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 滚动更新
docker-compose up -d --no-deps backend
docker-compose up -d --no-deps frontend

# 运行数据库迁移
docker-compose exec backend python manage.py migrate
```

### 2. 系统维护

```bash
# 清理日志文件
find /var/log -name "*.log" -mtime +30 -delete

# 清理 Docker 资源
docker system prune -f

# 更新系统包
sudo apt update && sudo apt upgrade -y
```

## 联系支持

如遇到部署问题，请联系技术支持：

- 邮箱: support@yourcompany.com
- 文档: https://docs.yourcompany.com
- 问题跟踪: https://github.com/your-org/stock-analysis-platform/issues