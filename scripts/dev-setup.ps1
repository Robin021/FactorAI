# Development environment setup script for Windows

Write-Host "🚀 Setting up TradingAgents development environment..." -ForegroundColor Green

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create environment files if they don't exist
if (-not (Test-Path "backend\.env")) {
    Write-Host "📝 Creating backend environment file..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "✅ Created backend\.env from example" -ForegroundColor Green
}

# Create data directories
Write-Host "📁 Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\mongodb" | Out-Null
New-Item -ItemType Directory -Force -Path "data\redis" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

# Start development services
Write-Host "🐳 Starting development services..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml up -d mongodb redis

Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if services are running
$services = docker-compose -f docker-compose.dev.yml ps
if ($services -match "Up") {
    Write-Host "✅ Development services are running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Service URLs:" -ForegroundColor Cyan
    Write-Host "   - MongoDB: mongodb://localhost:27017"
    Write-Host "   - Redis: redis://localhost:6379"
    Write-Host ""
    Write-Host "🔧 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Backend: cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload"
    Write-Host "   2. Frontend: cd frontend && npm install && npm run dev"
    Write-Host ""
    Write-Host "   Or use Docker:"
    Write-Host "   - docker-compose -f docker-compose.dev.yml up backend frontend"
} else {
    Write-Host "❌ Failed to start development services" -ForegroundColor Red
    exit 1
}