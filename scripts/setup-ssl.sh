#!/bin/bash

# SSL 证书设置脚本
# 用于首次获取 Let's Encrypt SSL 证书

set -e

DOMAIN="www.021d.com"
EMAIL="your-email@example.com"  # 请修改为你的邮箱

echo "=== SSL 证书设置向导 ==="
echo "域名: $DOMAIN"
echo ""

# 停止所有服务
echo "1. 停止现有服务..."
docker-compose down 2>/dev/null || true

# 创建必要的目录
echo "2. 创建必要的目录..."
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p certbot/logs

# 重新构建前端镜像（包含 Let's Encrypt 验证路径配置）
echo "3. 重新构建前端镜像..."
docker-compose build frontend

# 启动服务
echo "4. 启动服务..."
docker-compose up -d

# 等待服务启动
echo "5. 等待服务启动..."
sleep 10

# 测试验证路径
echo "6. 测试验证路径..."
echo "test" > certbot/www/test.txt
sleep 2
echo "访问测试: http://$DOMAIN/.well-known/acme-challenge/test.txt"
curl -s "http://$DOMAIN/.well-known/acme-challenge/test.txt" && echo " ✓ 验证路径正常" || echo " ✗ 验证路径异常"

# 获取证书
echo ""
echo "7. 获取 SSL 证书..."
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  -v $(pwd)/certbot/logs:/var/log/letsencrypt \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email $EMAIL \
  --agree-tos \
  --no-eff-email \
  -d $DOMAIN \
  -d 021d.com

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL 证书获取成功！"
    echo ""
    echo "8. 切换到生产环境配置（启用 HTTPS）..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    echo ""
    echo "9. 启动证书自动续期服务..."
    docker-compose -f docker-compose.certbot.yml up -d
    
    echo ""
    echo "✅ 完成！你的网站现在可以通过 HTTPS 访问了："
    echo "   https://www.021d.com"
    echo "   https://021d.com"
    echo ""
    echo "证书将自动续期，无需手动操作。"
else
    echo ""
    echo "❌ 证书获取失败"
    echo ""
    echo "查看详细日志："
    echo "   cat certbot/logs/letsencrypt.log"
    echo ""
    echo "查看 Nginx 日志："
    echo "   docker logs tradingagents-frontend"
fi
