#!/bin/bash

# Production Docker Build Script
set -e

echo "Building TradingAgents for production..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please copy .env.production to .env and configure it."
    echo "Using .env.production as template..."
    cp .env.production .env
fi

# Build backend image
echo "Building backend image..."
docker build -t tradingagents-backend:latest ./backend

# Build frontend image
echo "Building frontend image..."
docker build -t tradingagents-frontend:latest ./frontend

# Build complete stack
echo "Building complete stack with docker-compose..."
docker-compose build

echo "Production build completed successfully!"
echo ""
echo "To start the production environment:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the environment:"
echo "  docker-compose down"