#!/bin/bash

# Development Docker Build Script
set -e

echo "Building TradingAgents for development..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please copy .env.development to .env and configure it."
    echo "Using .env.development as template..."
    cp .env.development .env
fi

# Build development images
echo "Building development images..."
docker-compose -f docker-compose.dev.yml build

echo "Development build completed successfully!"
echo ""
echo "To start the development environment:"
echo "  docker-compose -f docker-compose.dev.yml up -d"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "To stop the environment:"
echo "  docker-compose -f docker-compose.dev.yml down"
echo ""
echo "Development URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"