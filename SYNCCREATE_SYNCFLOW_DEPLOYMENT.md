# SyncCreate™ & SyncFlow™ Deployment Guide

## Overview

This document covers the deployment of the newly containerized SyncCreate (Creative Engine) and SyncFlow (Campaign Execution) microservices.

## Services Added

### 1. SyncCreate™ (Port 8084)
**Purpose:** AI creative generation engine with brand safety guardrails

**Technology Stack:**
- Python 3.11
- Flask web framework
- Stable Diffusion (via diffusers library)
- Content moderation (detoxify)

**Endpoints:**
- `GET /health` - Health check
- `GET /ready` - Readiness probe
- `POST /api/v1/generate` - Generate creative variants
- `POST /api/v1/validate` - Validate creative compliance
- `GET /metrics` - Prometheus metrics

**Key Features:**
- Multi-variant creative generation (A/B/C testing)
- Brand guideline enforcement
- Content safety checks
- Integration with SyncShield for budget governance

### 2. SyncFlow™ (Already had Dockerfile, now fully integrated)
**Purpose:** Campaign execution and bid management

**Technology Stack:**
- Go 1.25
- gRPC client for SyncValue
- HTTP client for SyncShield

**Features:**
- Multi-platform bid placement
- Circuit breaker resilience
- Budget tracking
- LTV-based decisioning

---

## Local Development

### Start All Services
```bash
# From repository root
docker compose up -d

# Verify all services are running
docker compose ps

# Expected output:
# NAME            STATUS    PORTS
# syncshield      Up        0.0.0.0:8081->8081/tcp
# syncengage      Up        0.0.0.0:8083->8083/tcp
# synccreate      Up        0.0.0.0:8084->8084/tcp
# syncvalue       Up        0.0.0.0:50051->50051/tcp
# syncflow        Up
# kiki-redis      Up        0.0.0.0:6379->6379/tcp
```

### Test SyncCreate
```bash
# Health check
curl http://localhost:8084/health

# Generate creative variants
curl -X POST http://localhost:8084/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "CloudSync Pro",
      "features": ["Real-time sync", "End-to-end encryption"],
      "usp": "10x faster than competitors",
      "category": "software"
    },
    "brand": {
      "name": "TechCorp",
      "primary_colors": ["#3b82f6"],
      "tone_of_voice": "professional"
    },
    "variants": 3,
    "platform": "tiktok_9_16"
  }'

# Validate creative
curl -X POST http://localhost:8084/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/creative.jpg",
    "headline": "CloudSync Pro - 10x Faster",
    "brand": {"name": "TechCorp"}
  }'

# Prometheus metrics
curl http://localhost:8084/metrics
```

### Test SyncFlow
```bash
# SyncFlow runs as a batch process (no HTTP interface)
# Check logs
docker compose logs syncflow

# Manual execution
docker compose exec syncflow ./syncflow --help
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f synccreate
docker compose logs -f syncflow
```

### Stop Services
```bash
docker compose down

# With cleanup
docker compose down -v
```

---

## Kubernetes Deployment

### Prerequisites
```bash
# 1. Create namespace
kubectl create namespace kiki

# 2. Configure secrets (if needed)
kubectl create secret generic synccreate-secrets \
  --from-literal=SHIELD_URL=http://syncshield:8081/check \
  -n kiki
```

### Deploy SyncCreate
```bash
# Apply deployment
kubectl apply -f k8s/synccreate-deployment.yaml

# Verify
kubectl get pods -n kiki -l app=synccreate
kubectl get svc -n kiki synccreate

# Check logs
kubectl logs -n kiki -l app=synccreate --tail=50

# Port forward for testing
kubectl port-forward -n kiki svc/synccreate 8084:8084

# Test
curl http://localhost:8084/health
```

### Deploy SyncFlow
```bash
# Apply deployment
kubectl apply -f k8s/syncflow-deployment.yaml

# Verify
kubectl get pods -n kiki -l app=syncflow
```

### Full Stack Deployment (All Services)
```bash
# Deploy everything
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/syncshield-deployment.yaml
kubectl apply -f k8s/syncengage-deployment.yaml
kubectl apply -f k8s/syncvalue-deployment.yaml
kubectl apply -f k8s/syncflow-deployment.yaml
kubectl apply -f k8s/synccreate-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check all pods
kubectl get pods -n kiki

# Check services
kubectl get svc -n kiki
```

---

## Helm Deployment

### Option 1: Use Existing Helm Chart
```bash
# Update helm/kiki/values.yaml to include SyncCreate
# Then deploy:
helm upgrade --install kiki helm/kiki \
  --namespace kiki \
  --create-namespace \
  --values helm/kiki/values-prod.yaml
```

### Option 2: Standalone SyncCreate Chart
```bash
# Create minimal values file
cat > synccreate-values.yaml <<EOF
image:
  repository: ghcr.io/kiki/synccreate
  tag: latest
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8084

resources:
  requests:
    memory: 512Mi
    cpu: 500m
  limits:
    memory: 2Gi
    cpu: 2000m

env:
  SHIELD_URL: http://syncshield:8081/check
EOF

# Deploy
helm install synccreate ./helm/synccreate -f synccreate-values.yaml
```

---

## CI/CD Integration

The GitHub Actions pipeline (`.github/workflows/ci.yml`) now includes:

1. **Python Setup** - Installs Python 3.11 for SyncCreate validation
2. **Dependency Check** - Validates `cmd/creative/requirements.txt`
3. **Docker Build** - Builds SyncCreate image
4. **Image Push** - Pushes to GHCR (GitHub Container Registry)

### Manual Trigger
```bash
# Build and push manually
docker build -t ghcr.io/YOUR_ORG/synccreate:latest ./cmd/creative
docker push ghcr.io/YOUR_ORG/synccreate:latest
```

---

## Monitoring & Observability

### Prometheus Metrics

**SyncCreate Metrics:**
- `synccreate_requests_total` - Total HTTP requests
- `synccreate_generations_total` - Total creatives generated
- `synccreate_errors_total` - Total errors
- `synccreate_up` - Service availability (1 = up, 0 = down)

**Access Metrics:**
```bash
# Direct
curl http://localhost:8084/metrics

# Via Prometheus
curl http://localhost:9090/api/v1/query?query=synccreate_requests_total
```

### Grafana Dashboard

Add SyncCreate panels to existing dashboard (`grafana/syncshield-dashboard.json`):

```json
{
  "title": "SyncCreate - Generation Rate",
  "targets": [{
    "expr": "rate(synccreate_generations_total[5m])"
  }]
}
```

---

## Resource Requirements

### SyncCreate
- **CPU:** 500m (request), 2 cores (limit)
- **Memory:** 512Mi (request), 2Gi (limit)
- **Storage:** 5Gi cache (emptyDir)
- **Replicas:** 2 (min), 10 (max with HPA)

### SyncFlow
- **CPU:** 250m (request), 1 core (limit)
- **Memory:** 256Mi (request), 512Mi (limit)
- **Replicas:** 2-5 (based on load)

### Cluster Requirements
- **Kubernetes:** 1.24+
- **Total CPU:** ~3-4 cores (all services)
- **Total Memory:** ~4-6Gi (all services)

---

## Troubleshooting

### SyncCreate Not Starting

**Check logs:**
```bash
docker compose logs synccreate
# or
kubectl logs -n kiki -l app=synccreate
```

**Common Issues:**
1. **Python dependencies missing**
   ```bash
   # Rebuild image
   docker compose build synccreate
   ```

2. **Port conflict (8084)**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8085:8084"  # Use 8085 on host
   ```

3. **Shield URL unreachable**
   ```bash
   # Verify SyncShield is running
   curl http://localhost:8081/health
   
   # Check Docker network
   docker network inspect kiki_default
   ```

### SyncFlow Circuit Breaker Open

**Reset circuit:**
```bash
# Restart SyncShield (resets budget)
docker compose restart syncshield

# Or reduce spend
curl "http://localhost:8081/spend?amount=-100"
```

### Image Pull Failures

**Authenticate with GHCR:**
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

**Update image pull secrets in K8s:**
```bash
kubectl create secret docker-registry ghcr-credentials \
  --docker-server=ghcr.io \
  --docker-username=USERNAME \
  --docker-password=$GITHUB_TOKEN \
  -n kiki

# Add to deployment:
# imagePullSecrets:
#   - name: ghcr-credentials
```

---

## Performance Tuning

### SyncCreate Optimization

**1. GPU Acceleration (if available)**
```dockerfile
# Update Dockerfile base image
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
# Install torch with CUDA support
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**2. Increase Cache Size**
```yaml
# docker-compose.yml
volumes:
  - type: tmpfs
    target: /app/cache
    tmpfs:
      size: 10G  # Increase from 5G
```

**3. Preload Models**
```python
# Add to server.py startup
from diffusers import StableDiffusionPipeline
pipeline = StableDiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0")
pipeline.to("cuda")  # or "cpu"
```

### SyncFlow Optimization

**1. Increase gRPC Connection Pool**
```go
// main.go
conn, err := grpc.Dial(
    ltvAddr,
    grpc.WithInsecure(),
    grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(10*1024*1024)),
)
```

**2. Redis Connection Pooling**
```go
redisClient := redis.NewClient(&redis.Options{
    PoolSize: 100,
    MinIdleConns: 10,
})
```

---

## Security Considerations

### SyncCreate Security
1. **Non-root user** - Runs as UID 1000
2. **Read-only filesystem** - Except `/app/output` and `/app/cache`
3. **Content moderation** - All generated content screened
4. **Brand safety** - Prohibited terms/concepts enforced

### Network Policies
```yaml
# k8s/networkpolicies.yaml (already exists, verify includes SyncCreate)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: synccreate-policy
spec:
  podSelector:
    matchLabels:
      app: synccreate
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: syncflow
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: syncshield
```

---

## Next Steps

1. **Database Integration** - Add PostgreSQL for audit trail persistence
2. **Object Storage** - Store generated creatives in S3/GCS
3. **CDN Integration** - Serve creatives via CloudFront/Cloudflare
4. **Variant A/B Testing** - Track performance metrics
5. **Model Fine-tuning** - Custom brand-specific SD models

---

## Support

- **Documentation:** `/docs.html#synccreate`
- **API Reference:** `/api.html#synccreate`
- **Issues:** GitHub Issues
- **Slack:** #kiki-engineering
