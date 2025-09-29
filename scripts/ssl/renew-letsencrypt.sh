#!/bin/bash

# Let's Encrypt SSL Certificate Renewal Script
set -e

DOMAIN=${1}

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    echo "Example: $0 example.com"
    exit 1
fi

echo "Renewing Let's Encrypt SSL certificate for domain: $DOMAIN"

# Renew certificate
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot \
    renew --webroot \
    --webroot-path=/var/www/certbot \
    --quiet

# Check if renewal was successful
if [ $? -eq 0 ]; then
    echo "Certificate renewed successfully"
    
    # Copy new certificates
    cp ./certbot/conf/live/$DOMAIN/fullchain.pem ./nginx/ssl/cert.pem
    cp ./certbot/conf/live/$DOMAIN/privkey.pem ./nginx/ssl/key.pem
    
    # Set proper permissions
    chmod 600 ./nginx/ssl/key.pem
    chmod 644 ./nginx/ssl/cert.pem
    
    # Reload nginx
    docker-compose exec frontend nginx -s reload
    
    echo "✅ SSL certificate renewed and nginx reloaded!"
else
    echo "❌ Certificate renewal failed"
    exit 1
fi