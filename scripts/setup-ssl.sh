#!/bin/bash

# SSL 证书设置脚本
# 用于首次获取 Let's Encrypt SSL 证书

set -e

DOMAIN="www.021d.com"
EMAIL="your-email@example.com"  # 请修改为你的邮箱

echo "=== SSL 证书设置向导 ==="
echo "域名: $DOMAIN"
echo ""

# 创建必要的目录
echo "1. 创建必要的目录..."
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p certbot/logs

# 启动 nginx (仅 HTTP，用于验证域名)
echo "2. 启动临时 HTTP 服务器..."
docker-compose -f docker-compose.yml up -d frontend

# 等待 nginx 启动
echo "3. 等待服务启动..."
sleep 5

# 获取证书
echo "4. 获取 SSL 证书..."
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
    echo "5. 重启服务以启用 HTTPS..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    echo ""
    echo "6. 启动证书自动续期服务..."
    docker-compose -f docker-compose.certbot.yml up -d
    
    echo ""
    echo "✅ 完成！你的网站现在可以通过 HTTPS 访问了："
    echo "   https://www.021d.com"
    echo "   https://021d.com"
    echo ""
    echo "证书将自动续期，无需手动操作。"
else
    echo ""
    echo "❌ 证书获取失败，请检查："
    echo "   1. 域名 DNS 是否正确指向服务器"
    echo "   2. 服务器防火墙是否开放 80 端口"
    echo "   3. 邮箱地址是否正确"
    echo ""
    echo "查看详细日志："
    echo "   cat certbot/logs/letsencrypt.log"
fi
