#!/bin/bash

# SSL Certificate Generation Script
set -e

DOMAIN=${1:-localhost}
SSL_DIR="./nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"

echo "Generating SSL certificate for domain: $DOMAIN"

# Create SSL directory
mkdir -p "$SSL_DIR"

# Generate private key
echo "Generating private key..."
openssl genrsa -out "$KEY_FILE" 2048

# Generate certificate signing request
echo "Generating certificate signing request..."
openssl req -new -key "$KEY_FILE" -out "$SSL_DIR/cert.csr" -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

# Generate self-signed certificate
echo "Generating self-signed certificate..."
openssl x509 -req -in "$SSL_DIR/cert.csr" -signkey "$KEY_FILE" -out "$CERT_FILE" -days 365 \
    -extensions v3_req -extfile <(cat <<EOF
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = localhost
DNS.3 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
)

# Set proper permissions
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

# Clean up CSR
rm "$SSL_DIR/cert.csr"

echo "✅ SSL certificate generated successfully!"
echo "Certificate: $CERT_FILE"
echo "Private key: $KEY_FILE"
echo ""
echo "Note: This is a self-signed certificate for development/testing."
echo "For production, use a certificate from a trusted CA or Let's Encrypt."