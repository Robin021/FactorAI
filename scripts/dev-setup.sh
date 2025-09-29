#!/bin/bash

# Development environment setup script

set -e

echo "🚀 Setting up TradingAgents development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend environment file..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env from example"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/mongodb
mkdir -p data/redis
mkdir -p logs

# Start development services
echo "🐳 Starting development services..."
docker-compose -f docker-compose.dev.yml up -d mongodb redis

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo "✅ Development services are running!"
    echo ""
    echo "📋 Service URLs:"
    echo "   - MongoDB: mongodb://localhost:27017"
    echo "   - Redis: redis://localhost:6379"
    echo ""
    echo "🔧 Next steps:"
    echo "   1. Backend: cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload"
    echo "   2. Frontend: cd frontend && npm install && npm run dev"
    echo ""
    echo "   Or use Docker:"
    echo "   - docker-compose -f docker-compose.dev.yml up backend frontend"
else
    echo "❌ Failed to start development services"
    exit 1
fi