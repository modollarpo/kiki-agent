#!/usr/bin/env pwsh
# KIKI Platform - Quick Start Script for Windows
# Builds and starts all 5 microservices

Write-Host "🚀 KIKI Platform - Quick Start" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "❌ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

$dockerComposeInstalled = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerComposeInstalled) {
    Write-Host "❌ Docker Compose not found. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker found: $(docker --version)" -ForegroundColor Green
Write-Host "✅ Docker Compose found" -ForegroundColor Green
Write-Host ""

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null

# Build images
Write-Host "🔨 Building Docker images..." -ForegroundColor Yellow
Write-Host "   This may take 5-10 minutes on first run..." -ForegroundColor Gray
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed. Check logs above." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All images built successfully" -ForegroundColor Green
Write-Host ""

# Start services
Write-Host "🚀 Starting all services..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services." -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Health checks
Write-Host ""
Write-Host "🏥 Running health checks..." -ForegroundColor Yellow
Write-Host ""

$services = @(
    @{ Name = "SyncShield"; URL = "http://localhost:8081/health"; Port = 8081 },
    @{ Name = "SyncEngage"; URL = "http://localhost:8083/health"; Port = 8083 },
    @{ Name = "SyncCreate"; URL = "http://localhost:8084/health"; Port = 8084 }
)

$allHealthy = $true

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.URL -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Name) (port $($service.Port)): Healthy" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($service.Name) (port $($service.Port)): Unhealthy (HTTP $($response.StatusCode))" -ForegroundColor Yellow
            $allHealthy = $false
        }
    } catch {
        Write-Host "❌ $($service.Name) (port $($service.Port)): Not responding" -ForegroundColor Red
        $allHealthy = $false
    }
}

# Check SyncValue (gRPC)
$syncValueRunning = docker ps --filter "name=syncvalue" --filter "status=running" --quiet
if ($syncValueRunning) {
    Write-Host "✅ SyncValue (port 50051): Running" -ForegroundColor Green
} else {
    Write-Host "❌ SyncValue (port 50051): Not running" -ForegroundColor Red
    $allHealthy = $false
}

# Check SyncFlow
$syncFlowRunning = docker ps --filter "name=syncflow" --filter "status=running" --quiet
if ($syncFlowRunning) {
    Write-Host "✅ SyncFlow: Running" -ForegroundColor Green
} else {
    Write-Host "❌ SyncFlow: Not running" -ForegroundColor Red
    $allHealthy = $false
}

# Check Redis
$redisRunning = docker ps --filter "name=kiki-redis" --filter "status=running" --quiet
if ($redisRunning) {
    Write-Host "✅ Redis (port 6379): Running" -ForegroundColor Green
} else {
    Write-Host "❌ Redis (port 6379): Not running" -ForegroundColor Red
    $allHealthy = $false
}

Write-Host ""

if ($allHealthy) {
    Write-Host "🎉 All services started successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some services failed to start. Check logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs <service-name>" -ForegroundColor Gray
}

# Display useful information
Write-Host ""
Write-Host "📚 Service Endpoints:" -ForegroundColor Cyan
Write-Host "   SyncShield:  http://localhost:8081/health" -ForegroundColor White
Write-Host "   SyncEngage:  http://localhost:8083/health" -ForegroundColor White
Write-Host "   SyncCreate:  http://localhost:8084/health" -ForegroundColor White
Write-Host "   SyncValue:   grpc://localhost:50051" -ForegroundColor White
Write-Host "   Redis:       redis://localhost:6379" -ForegroundColor White
Write-Host ""

Write-Host "📖 Useful Commands:" -ForegroundColor Cyan
Write-Host "   View logs:        docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop services:    docker-compose down" -ForegroundColor White
Write-Host "   Restart service:  docker-compose restart <name>" -ForegroundColor White
Write-Host "   View containers:  docker-compose ps" -ForegroundColor White
Write-Host ""

Write-Host "🧪 Quick Test:" -ForegroundColor Cyan
Write-Host "   curl http://localhost:8084/api/v1/generate -Method POST ``" -ForegroundColor White
Write-Host "     -ContentType 'application/json' ``" -ForegroundColor White
Write-Host "     -Body '{\"product\":{\"name\":\"Test\"},\"brand\":{\"name\":\"KIKI\"},\"variants\":2}'" -ForegroundColor White
Write-Host ""

Write-Host "✨ Ready to build with KIKI!" -ForegroundColor Green
