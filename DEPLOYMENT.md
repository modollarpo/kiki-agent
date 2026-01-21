# KIKI Platform Deployment Guide

## Overview

KIKI is a production-grade agent platform with four core services:
- **SyncShield™** (Port 8081): Regulatory guardrail & budget governance
- **SyncEngage™** (Port 8083): Post-acquisition loyalty & retention engine
- **SyncValue™** (gRPC 50051): LTV prediction AI service
- **SyncFlow™**: Execution engine for multi-platform campaigns

This guide covers local development, Docker Compose staging, and Kubernetes production deployment.

---

## Quick Start (Local Development)

### Prerequisites
- Go 1.24.0+
- Redis (optional; in-memory fallback available)
- gRPC tools

### Run SyncShield + SyncEngage Locally

```bash
# Terminal 1: SyncShield (port 8081)
cd cmd/syncshield
PORT=8081 REDIS_ADDR=localhost:6379 go run .

# Terminal 2: SyncEngage (port 8083)
cd cmd/syncengage
SHIELD_URL=http://localhost:8081/check go run .

# Terminal 3: Test budget enforcement
for i in {1..6}; do 
  curl "http://localhost:8081/spend?amount=100" 
done
curl "http://localhost:8081/check?ltv=600"  # Expect 403
```

### With Docker Compose (Local)

```bash
docker compose up -d redis syncshield syncengage

# Test
curl "http://localhost:8081/health"
curl "http://localhost:8083/health"

# Cleanup
docker compose down
```

---

## Kubernetes Deployment (Production)

### Prerequisites
- Kubernetes 1.29+ cluster (EKS, AKS, GKE)
- Helm 3.14+
- kubectl configured
- External Secrets Operator (ESO) installed
- cert-manager for TLS

### Install Required Operators

```bash
# Install External Secrets Operator (ESO)
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets-system --create-namespace

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  -n cert-manager --create-namespace \
  --set installCRDs=true

# Create Let's Encrypt ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@kiki.io
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Configure Secrets (AWS Example)

#### 1. Create IAM Role for KIKI Service Account

```bash
# Create OIDC identity provider
eksctl utils associate-iam-oidc-provider --cluster=kiki-prod --region=us-east-1

# Create IAM policy
cat > kiki-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:kiki/prod/*"
    }
  ]
}
EOF

aws iam create-policy --policy-name kiki-sa-policy --policy-document file://kiki-policy.json

# Create IAM role and bind to K8s service account
eksctl create iamserviceaccount \
  --cluster=kiki-prod \
  --name=kiki-sa \
  --namespace=kiki \
  --attach-policy-arn=arn:aws:iam::ACCOUNT_ID:policy/kiki-sa-policy \
  --approve
```

#### 2. Populate Secrets in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name kiki/prod/sendgrid_api_key \
  --secret-string "SG.xxxxx"

aws secretsmanager create-secret \
  --name kiki/prod/redis_password \
  --secret-string "your-redis-password"

aws secretsmanager create-secret \
  --name kiki/prod/postgres_password \
  --secret-string "your-postgres-password"

aws secretsmanager create-secret \
  --name kiki/prod/salesforce_client_id \
  --secret-string "your-salesforce-id"

# ... (repeat for TWILIO, HUBSPOT, SHOPIFY, etc.)
```

### Deploy KIKI via Helm

#### Option 1: Manual Helm Deploy

```bash
# Add values overrides
cat > overrides.yaml <<EOF
global:
  imageRegistry: "ghcr.io/your-org/kiki"
  domain:
    shield: shield.kiki.io
    engage: engage.kiki.io

redis:
  address: "kiki-prod-redis.xxxxx.ng.0001.use1.cache.amazonaws.com:6379"

externalSecrets:
  enabled: true
  provider: aws
  region: us-east-1
EOF

# Deploy with Helm
helm upgrade --install kiki ./helm/kiki \
  --namespace kiki --create-namespace \
  --set global.imageRegistry=ghcr.io/your-org/kiki \
  --set syncshield.image=syncshield:v1.0.0 \
  --set syncengage.image=syncengage:v1.0.0 \
  --set syncvalue.image=syncvalue:v1.0.0 \
  --set syncflow.image=syncflow:v1.0.0 \
  -f helm/kiki/values-prod.yaml \
  -f overrides.yaml \
  --timeout 10m --wait

# Verify
kubectl -n kiki get pods
kubectl -n kiki get svc
kubectl -n kiki get ing
```

#### Option 2: GitHub Actions CD Pipeline (Recommended)

1. **Create GitHub secrets** in your repository:
   - `KUBECONFIG_BASE64`: Base64-encoded kubeconfig for your cluster
   - `GITHUB_TOKEN`: Automatically available (for GHCR push)

2. **Tag a release** to trigger CD:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. **Monitor deployment**:
   ```bash
   # Watch GitHub Actions
   gh workflow view CD --web
   
   # Or check cluster
   kubectl -n kiki rollout status deployment/syncshield
   kubectl -n kiki rollout status deployment/syncengage
   ```

---

## Configuration Reference

### Environment Variables

#### SyncShield

| Variable | Default | Example | Notes |
|----------|---------|---------|-------|
| `PORT` | 8081 | 8081 | HTTP server port |
| `REDIS_ADDR` | localhost:6379 | redis:6379 | Redis address (Docker/K8s) |
| `MAX_BURST_BUDGET` | 500.0 | 1000.0 | Max spend in window (dollars) |
| `WINDOW_SECONDS` | 60.0 | 3600.0 | Sliding window duration (seconds) |
| `RETENTION_DAYS` | 2555 | 2555 | GDPR audit log retention |

#### SyncEngage

| Variable | Default | Example | Notes |
|----------|---------|---------|-------|
| `SHIELD_URL` | http://localhost:8081/check | http://syncshield:80/check | SyncShield compliance endpoint |
| `LTV_GRPC_ADDR` | localhost:50051 | syncvalue:50051 | SyncValue LTV service address |

### Helm Values Overrides

```yaml
# Production resource allocation
syncshield:
  replicaCount: 3
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

# High availability
pdb:
  enabled: true
  minAvailable: 2

# Network security
networkPolicy:
  enabled: true
  allowExternal: false

# Observability
otel:
  enabled: true
  collector:
    endpoint: "otel-collector.monitoring.svc.cluster.local:4317"
  samplingRate: 0.1
```

---

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl -n kiki describe pod syncshield-0

# View logs
kubectl -n kiki logs deployment/syncshield
kubectl -n kiki logs deployment/syncshield --previous  # if crashed
```

### External Secrets not syncing

```bash
# Check ExternalSecret status
kubectl -n kiki describe externalsecret kiki-secrets-aws

# Verify AWS credentials
kubectl -n kiki describe sa kiki-sa

# Check ESO controller logs
kubectl -n external-secrets-system logs deployment/external-secrets
```

### Budget enforcement not working

```bash
# Test /spend endpoint
curl -v "http://syncshield.kiki.svc.cluster.local/spend?amount=100"

# Test /check with high spend
curl -v "http://syncshield.kiki.svc.cluster.local/check?ltv=100"
# Should return 403 if budget exceeded

# Check audit logs
kubectl -n kiki exec deployment/syncshield -it -- cat shield_audit_gdpr.csv
```

### Compliance/consent endpoints

```bash
# Grant consent (JSON body)
curl -X POST http://syncshield.kiki.svc.cluster.local/consent/grant \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust_123","consent_type":"marketing"}'

# Check status
curl http://syncshield.kiki.svc.cluster.local/consent/status?customer_id=cust_123

# Create DSR
curl -X POST http://syncshield.kiki.svc.cluster.local/dsr/create \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust_123","request_type":"ACCESS"}'
```

---

## Monitoring & Observability

### Prometheus Metrics

SyncShield exposes metrics via OpenTelemetry:
```bash
# Port-forward OTEL collector
kubectl -n kiki port-forward svc/otel-collector 8888:8888

# Query metrics (Prometheus endpoint)
curl http://localhost:8888/metrics
```

### Jaeger Tracing

Enable distributed tracing for request flow visibility:
```bash
# Port-forward Jaeger
kubectl -n kiki port-forward svc/jaeger-query 16686:16686

# Access UI at http://localhost:16686
```

### Logs

All services log to stdout; aggregate with your logging solution:
```bash
# Real-time logs
kubectl -n kiki logs -f deployment/syncshield

# Search audit logs
kubectl -n kiki exec deployment/syncshield -it -- \
  grep "DENIED" shield_audit_gdpr.csv
```

---

## Backup & Disaster Recovery

### Redis Snapshots (AWS ElastiCache)

```bash
# Enable automatic backups (via AWS Console or CLI)
aws elasticache modify-replication-group \
  --replication-group-id kiki-prod \
  --automatic-failover-enabled \
  --apply-immediately
```

### Compliance Audit Logs

Store audit logs in S3 for long-term retention:
```bash
# Mount S3 bucket as volume
kubectl -n kiki patch deployment syncshield --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/volumes/-", 
       "value": {"name": "audit-logs", 
       "emptyDir": {"medium": "Memory"}}}]'

# Periodically sync to S3
kubectl -n kiki create cronjob sync-audits --image=amazon/aws-cli \
  --schedule="*/1 * * * *" \
  -- aws s3 sync /var/audit-logs s3://kiki-audits/
```

---

## Upgrade & Rollback

### Rolling Update

```bash
# Helm upgrade (zero-downtime with PDB)
helm upgrade kiki ./helm/kiki \
  --namespace kiki \
  --set syncshield.image=syncshield:v1.1.0 \
  -f helm/kiki/values-prod.yaml \
  --timeout 10m --wait

# Monitor rollout
kubectl -n kiki rollout status deployment/syncshield
```

### Rollback

```bash
# Revert to previous Helm release
helm rollback kiki -n kiki

# Or revert deployment
kubectl -n kiki rollout undo deployment/syncshield
```

---

## Security Checklist

- [ ] Network policies enforce pod-to-pod communication
- [ ] External Secrets operator has least-privilege IAM role
- [ ] TLS enabled for all external ingress (Let's Encrypt)
- [ ] Pod Security Policy set to "restricted"
- [ ] ReadOnlyRootFilesystem enabled
- [ ] Non-root containers (uid 10001)
- [ ] All secrets stored in AWS Secrets Manager (not ConfigMaps)
- [ ] Audit logs encrypted and retained for 7 years (GDPR)
- [ ] Resource requests/limits enforced
- [ ] HPA enabled to prevent resource exhaustion

---

## Support & References

- **Helm Chart**: [helm/kiki](helm/kiki)
- **K8s Manifests**: [k8s/](k8s/)
- **API Docs**: [cmd/syncshield/README_COMPLIANCE.md](cmd/syncshield/README_COMPLIANCE.md)
- **GitHub Actions**: [.github/workflows/cd.yml](.github/workflows/cd.yml)

