#!/bin/bash

# Docker Health Check Script
set -e

echo "Checking TradingAgents services health..."

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if curl -f -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo "✅ Healthy"
        return 0
    else
        echo "❌ Unhealthy"
        return 1
    fi
}

# Check if containers are running
echo "Checking container status..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Some containers are not running"
    docker-compose ps
    exit 1
fi

# Check service endpoints
failed=0

# Check frontend
if ! check_service "Frontend" "http://localhost:80/health"; then
    failed=1
fi

# Check backend
if ! check_service "Backend API" "http://localhost:8000/health"; then
    failed=1
fi

# Check backend docs
if ! check_service "Backend Docs" "http://localhost:8000/docs"; then
    failed=1
fi

# Check database connections
echo -n "Checking MongoDB... "
if docker-compose exec -T mongodb mongo --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "❌ Connection failed"
    failed=1
fi

echo -n "Checking Redis... "
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Connected"
else
    echo "❌ Connection failed"
    failed=1
fi

if [ $failed -eq 0 ]; then
    echo ""
    echo "🎉 All services are healthy!"
    exit 0
else
    echo ""
    echo "❌ Some services are unhealthy. Check logs with: docker-compose logs"
    exit 1
fi