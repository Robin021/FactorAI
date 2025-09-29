#!/bin/bash

# Production Deployment Script
set -e

echo "Deploying TradingAgents to production..."

# Check if .env file exists and is configured
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please copy .env.production to .env and configure it."
    exit 1
fi

# Check for required environment variables
required_vars=("SECRET_KEY" "JWT_SECRET_KEY" "MONGODB_PASSWORD" "REDIS_PASSWORD")
for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=.*change.*" .env; then
        echo "Error: Please configure ${var} in .env file"
        exit 1
    fi
done

# Create necessary directories
mkdir -p logs data

# Pull latest images (if using registry)
# docker-compose pull

# Build images
echo "Building production images..."
docker-compose build

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Start services
echo "Starting production services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Check service health
echo "Checking service health..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running successfully!"
    echo ""
    echo "Application URLs:"
    echo "  Frontend: http://localhost"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop services: docker-compose down"
else
    echo "❌ Some services failed to start. Check logs:"
    docker-compose logs
    exit 1
fi