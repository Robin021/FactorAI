# HTTPS 配置指南

## 域名：www.021d.com

### 前置条件
- ✅ 域名 DNS 已指向服务器 IP
- ⚠️ 确保服务器防火墙开放 80 和 443 端口
- ⚠️ 准备一个邮箱地址（用于 Let's Encrypt 通知）

---

## 快速配置步骤

### 1. 修改邮箱地址
编辑 `scripts/setup-ssl.sh`，将第 9 行改为你的邮箱：
```bash
EMAIL="your-email@example.com"  # 改成你的真实邮箱
```

### 2. 给脚本添加执行权限
```bash
chmod +x scripts/setup-ssl.sh
```

### 3. 运行 SSL 设置脚本
```bash
./scripts/setup-ssl.sh
```

脚本会自动：
- 创建必要的目录
- 启动临时 HTTP 服务器
- 向 Let's Encrypt 申请免费 SSL 证书
- 配置 HTTPS 并重启服务
- 启动自动续期服务

### 4. 验证 HTTPS
访问：https://www.021d.com

---

## 手动操作步骤（如果脚本失败）

### 1. 创建目录
```bash
mkdir -p certbot/conf certbot/www certbot/logs
```

### 2. 启动 HTTP 服务（用于域名验证）
```bash
docker-compose up -d frontend
```

### 3. 获取 SSL 证书
```bash
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  -v $(pwd)/certbot/logs:/var/log/letsencrypt \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d www.021d.com \
  -d 021d.com
```

### 4. 启动完整服务（包含 HTTPS）
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 5. 启动证书自动续期
```bash
docker-compose -f docker-compose.certbot.yml up -d
```

---

## 证书续期

证书有效期 90 天，但 certbot 容器会每 12 小时自动检查并续期（剩余 30 天时自动续期）。

### 手动强制续期
```bash
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  certbot/certbot renew --force-renewal

# 重启 nginx 加载新证书
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart frontend
```

---

## 常见问题

### 1. 证书获取失败
**原因：**
- DNS 未生效或指向错误
- 防火墙未开放 80 端口
- 域名已被其他服务占用

**解决：**
```bash
# 检查 DNS
nslookup www.021d.com

# 检查端口
curl http://www.021d.com/.well-known/acme-challenge/test

# 查看日志
cat certbot/logs/letsencrypt.log
```

### 2. HTTPS 访问失败
**检查证书文件：**
```bash
ls -la certbot/conf/live/www.021d.com/
```

应该看到：
- fullchain.pem
- privkey.pem

**重启服务：**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart frontend
```

### 3. 证书过期
如果自动续期失败，手动续期：
```bash
docker-compose -f docker-compose.certbot.yml restart
```

---

## 安全建议

1. **定期检查证书状态**
   ```bash
   docker run --rm \
     -v $(pwd)/certbot/conf:/etc/letsencrypt \
     certbot/certbot certificates
   ```

2. **监控证书过期时间**
   访问：https://www.ssllabs.com/ssltest/analyze.html?d=www.021d.com

3. **备份证书**
   ```bash
   tar -czf ssl-backup-$(date +%Y%m%d).tar.gz certbot/conf/
   ```

---

## 配置文件说明

- `nginx/nginx.conf` - Nginx 主配置，已配置 HTTPS
- `docker-compose.prod.yml` - 生产环境配置，挂载证书目录
- `docker-compose.certbot.yml` - Certbot 自动续期服务
- `certbot/conf/` - 证书存储目录
- `certbot/www/` - Let's Encrypt 验证目录
