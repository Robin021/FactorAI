# TradingAgents Development Makefile

.PHONY: help setup dev-up dev-down backend frontend test clean

# Default target
help:
	@echo "TradingAgents Development Commands:"
	@echo "  setup      - Set up development environment"
	@echo "  dev-up     - Start all development services"
	@echo "  dev-down   - Stop all development services"
	@echo "  backend    - Start backend development server"
	@echo "  frontend   - Start frontend development server"
	@echo "  test       - Run all tests"
	@echo "  clean      - Clean up containers and volumes"

# Set up development environment
setup:
	@echo "Setting up development environment..."
	@echo "Please install dependencies manually:"
	@echo "  Backend: cd backend && pip install -r requirements.txt"
	@echo "  Frontend: cd frontend && npm install"

# Start all development services
dev-up:
	@echo "Starting development services..."
	@docker-compose -f docker-compose.dev.yml up -d

# Stop all development services
dev-down:
	@echo "Stopping development services..."
	@docker-compose -f docker-compose.dev.yml down

# Start backend development server
backend:
	@echo "Starting backend development server..."
	@cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend development server
frontend:
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev

# Run all tests
test:
	@echo "Running backend tests..."
	@cd backend && python -m pytest
	@echo "Running frontend tests..."
	@cd frontend && npm run test

# Clean up containers and volumes
clean:
	@echo "Cleaning up containers and volumes..."
	@docker-compose -f docker-compose.dev.yml down -v
	@docker system prune -f