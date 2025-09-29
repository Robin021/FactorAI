#!/bin/bash

# Let's Encrypt SSL Certificate Setup Script
set -e

DOMAIN=${1}
EMAIL=${2}

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 example.com admin@example.com"
    exit 1
fi

echo "Setting up Let's Encrypt SSL certificate for domain: $DOMAIN"

# Create directories
mkdir -p ./nginx/ssl
mkdir -p ./certbot/www
mkdir -p ./certbot/conf

# Create initial nginx config for HTTP challenge
cat > ./nginx/nginx-letsencrypt.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

echo "Starting nginx for HTTP challenge..."
docker run -d --name nginx-letsencrypt \
    -p 80:80 \
    -v $(pwd)/nginx/nginx-letsencrypt.conf:/etc/nginx/conf.d/default.conf \
    -v $(pwd)/certbot/www:/var/www/certbot \
    nginx:alpine

# Wait for nginx to start
sleep 5

echo "Obtaining SSL certificate from Let's Encrypt..."
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Stop temporary nginx
docker stop nginx-letsencrypt
docker rm nginx-letsencrypt

# Copy certificates to nginx ssl directory
cp ./certbot/conf/live/$DOMAIN/fullchain.pem ./nginx/ssl/cert.pem
cp ./certbot/conf/live/$DOMAIN/privkey.pem ./nginx/ssl/key.pem

# Set proper permissions
chmod 600 ./nginx/ssl/key.pem
chmod 644 ./nginx/ssl/cert.pem

echo "✅ Let's Encrypt SSL certificate obtained successfully!"
echo "Certificate: ./nginx/ssl/cert.pem"
echo "Private key: ./nginx/ssl/key.pem"
echo ""
echo "Certificate will expire in 90 days. Set up auto-renewal with:"
echo "./scripts/ssl/renew-letsencrypt.sh $DOMAIN"