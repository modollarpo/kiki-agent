# API Setup & Deployment Guide

**Last Updated:** January 2026

## Table of Contents

1. [Development Setup](#development-setup)
2. [Running Locally](#running-locally)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Configuration](#configuration)
6. [Monitoring & Logging](#monitoring--logging)
7. [Troubleshooting](#troubleshooting)

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Step 1: Create Virtual Environment

```bash
# Navigate to project root
cd C:\Users\USER\Documents\KIKI

# Create virtual environment
python -m venv api_env

# Activate virtual environment
# On Windows:
api_env\Scripts\activate
# On Linux/macOS:
source api_env/bin/activate
```

### Step 2: Install Dependencies

```bash
# Install required packages
pip install --upgrade pip
pip install grpcio grpcio-tools protobuf fastapi uvicorn pydantic requests
```

### Step 3: Generate Protobuf Code

```bash
# Create directory for generated code
mkdir -p api/generated

# Generate protobuf Python code
python -m grpc_tools.protoc \
  -I proto/ \
  --python_out=api/generated \
  --pyi_out=api/generated \
  --grpc_python_out=api/generated \
  proto/variant_strategy.proto
```

### Step 4: Update Python Path

Add `api/generated` to your Python path in `api/grpc_server.py` and `api/grpc_client.py`:

```python
sys.path.insert(0, str(Path(__file__).parent / "generated"))
```

---

## Running Locally

### Option 1: Run Both Services

#### Terminal 1 - gRPC Server

```bash
cd C:\Users\USER\Documents\KIKI
python api/grpc_server.py 50051
```

Output:
```
INFO:__main__:Starting gRPC server on port 50051
```

#### Terminal 2 - REST API

```bash
cd C:\Users\USER\Documents\KIKI
python -m uvicorn api.rest_api:app --host 0.0.0.0 --port 8000 --reload
```

Output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Terminal 3 - Test Clients

```bash
cd C:\Users\USER\Documents\KIKI

# Test REST API
python api/rest_client.py

# Test gRPC Client (requires server running)
# python api/grpc_client.py
```

### Option 2: Run REST API Only (Recommended for Development)

The REST API can work without the gRPC server (it calls the Python modules directly):

```bash
cd C:\Users\USER\Documents\KIKI
python -m uvicorn api.rest_api:app --host 0.0.0.0 --port 8000 --reload
```

Then visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Health**: http://localhost:8000/health

---

## Docker Deployment

### Step 1: Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 50051 8000

# Default: run REST API
CMD ["python", "-m", "uvicorn", "api.rest_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  grpc-server:
    build: .
    ports:
      - "50051:50051"
    command: python api/grpc_server.py 50051
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./cmd/creative:/app/cmd/creative
      - ./api:/app/api

  rest-api:
    build: .
    ports:
      - "8000:8000"
    command: python -m uvicorn api.rest_api:app --host 0.0.0.0 --port 8000
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./cmd/creative:/app/cmd/creative
      - ./api:/app/api
    depends_on:
      - grpc-server

  # Optional: Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### Step 3: Build and Run with Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up

# View logs
docker-compose logs -f rest-api

# Stop services
docker-compose down
```

---

## Production Deployment

### Option 1: Deploy to Kubernetes

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: variant-api-rest
spec:
  replicas: 3
  selector:
    matchLabels:
      app: variant-api-rest
  template:
    metadata:
      labels:
        app: variant-api-rest
    spec:
      containers:
      - name: variant-api-rest
        image: variant-api:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: variant-api-service
spec:
  selector:
    app: variant-api-rest
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:

```bash
kubectl apply -f k8s-deployment.yaml
kubectl get service variant-api-service
```

### Option 2: Deploy to Cloud Platforms

#### AWS Lambda + API Gateway

```bash
# Create Lambda function from Docker image
aws lambda create-function \
  --function-name variant-strategy-api \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --code ImageUri=123456789.dkr.ecr.us-east-1.amazonaws.com/variant-api:latest \
  --timeout 30 \
  --memory-size 512
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy variant-strategy-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1
```

#### Azure Container Instances

```bash
# Create container
az container create \
  --resource-group myResourceGroup \
  --name variant-api \
  --image myregistry.azurecr.io/variant-api:latest \
  --cpu 1 \
  --memory 0.5 \
  --ports 8000 \
  --environment-variables PYTHONUNBUFFERED=1
```

---

## Configuration

### Environment Variables

Create `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
GRPC_PORT=50051

# CLIP Configuration
CLIP_MODEL=ViT-B/32
CLIP_USE_MOCK=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Database (if needed)
DATABASE_URL=sqlite:///./portfolio.db
```

### Configuration File

Create `config.yaml`:

```yaml
api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: false

grpc:
  host: 0.0.0.0
  port: 50051
  max_workers: 10

clip:
  model: ViT-B/32
  use_mock: true
  device: cpu

logging:
  level: INFO
  format: json
  file: logs/api.log

security:
  enable_cors: true
  cors_origins: ['*']
```

### Load Configuration

```python
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

API_PORT = config['api']['port']
GRPC_PORT = config['grpc']['port']
```

---

## Monitoring & Logging

### Structured Logging

```python
import logging
import json
from logging.handlers import RotatingFileHandler

# Configure JSON logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        return json.dumps(log_data)

handler = RotatingFileHandler(
    'logs/api.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
handler.setFormatter(JsonFormatter())

logger = logging.getLogger(__name__)
logger.addHandler(handler)
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
request_count = Counter('api_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('api_request_duration_seconds', 'Request duration')

# Export metrics
@app.get("/metrics")
async def metrics():
    return generate_latest()
```

### Health Monitoring

```python
# Health check with dependencies
@app.get("/health/detailed")
async def detailed_health():
    return {
        "status": "healthy",
        "components": {
            "api": "operational",
            "grpc": check_grpc_connection(),
            "storage": check_storage(),
        }
    }
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'variant_strategy_pb2'"

**Solution:** Generate protobuf code:

```bash
python -m grpc_tools.protoc -I proto/ --python_out=api/generated --grpc_python_out=api/generated proto/variant_strategy.proto
```

### Issue: "Port already in use"

**Solution:** Use different port or kill existing process:

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :8000
kill -9 <PID>
```

### Issue: "Connection refused" when calling gRPC

**Solution:** Ensure gRPC server is running:

```bash
python api/grpc_server.py 50051
```

### Issue: "No module named 'cmd.creative'"

**Solution:** Ensure project structure and PYTHONPATH:

```bash
# In api/grpc_server.py or rest_api.py, ensure path is correct:
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Issue: CLIP Model Download Fails

**Solution:** Pre-download model or use mock mode:

```python
# Set CLIP_USE_MOCK=true in environment
os.environ['CLIP_USE_MOCK'] = 'true'

# Or manually download:
import clip
clip.load("ViT-B/32")
```

### Issue: High Memory Usage

**Solution:** Optimize for production:

```python
# Use smaller CLIP model
clip.load("ViT-B/32")  # ~350MB

# Or use CLIP-lite variants for mobile/edge
```

---

## Performance Optimization

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def get_variant_library():
    return VARIANT_STRATEGY_LIBRARY
```

### Connection Pooling

```python
from grpc._cython import cygrpc

options = [
    (cygrpc.ChannelArgKey.max_connection_idle_ms, 60000),
    (cygrpc.ChannelArgKey.max_connection_age_ms, 600000),
]
channel = grpc.secure_channel('localhost:50051', creds, options=options)
```

### Database Connection Pool

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
)
```

---

## Deployment Checklist

- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Protobuf code generated (`python -m grpc_tools.protoc ...`)
- [ ] Environment variables configured (`.env` file)
- [ ] CLIP model downloaded or mock mode enabled
- [ ] Logging configured and tested
- [ ] Health checks passing
- [ ] gRPC and REST API responding
- [ ] CORS configured if needed
- [ ] SSL/TLS certificates installed (production)
- [ ] Monitoring and alerting configured
- [ ] Database backups configured
- [ ] Rate limiting configured (optional)
- [ ] API documentation updated
- [ ] Client libraries tested
- [ ] Load testing completed

---

## Next Steps

1. **Monitoring**: Set up Prometheus + Grafana for metrics
2. **CI/CD**: Configure GitHub Actions or GitLab CI for automated deployment
3. **API Versioning**: Implement versioning for backward compatibility
4. **Authentication**: Add API key or OAuth 2.0 authentication
5. **Rate Limiting**: Implement rate limiting and quota management
6. **Caching Layer**: Add Redis for distributed caching
7. **APM**: Integrate Application Performance Monitoring (DataDog, NewRelic)

---

## Support

For deployment assistance:
- Check Docker documentation: https://docs.docker.com
- Kubernetes: https://kubernetes.io/docs
- gRPC: https://grpc.io/docs
- FastAPI: https://fastapi.tiangolo.com
