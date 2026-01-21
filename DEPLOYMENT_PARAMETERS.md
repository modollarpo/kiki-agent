# KIKI Deployment Parameters Template

Use this template to fill in your deployment-specific values before running Helm.

## Cloud Provider Selection

```bash
# Choose one:
CLOUD_PROVIDER="aws"      # Amazon EKS + ElastiCache + Secrets Manager
# CLOUD_PROVIDER="azure"  # Azure AKS + Azure Cache + Key Vault
# CLOUD_PROVIDER="gcp"    # Google GKE + Memorystore + Secret Manager
```

## Domain Configuration

```yaml
# Update these in helm/kiki/values-prod.yaml
global:
  domain:
    shield: "shield.YOUR_DOMAIN.com"     # e.g., shield.kiki.io
    engage: "engage.YOUR_DOMAIN.com"     # e.g., engage.kiki.io
    api: "api.YOUR_DOMAIN.com"           # Optional: central API endpoint
```

## Container Registry

```yaml
# Update these in helm/kiki/values-prod.yaml
global:
  imageRegistry: "ghcr.io/YOUR_ORG/kiki"  # GitHub Container Registry
  # OR
  imageRegistry: "YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/kiki"  # ECR
  # OR
  imageRegistry: "your-acr-name.azurecr.io/kiki"  # ACR
```

## Redis Configuration

### AWS ElastiCache
```yaml
redis:
  address: "kiki-prod-redis.xxxxx.ng.0001.use1.cache.amazonaws.com:6379"
  passwordSecret:
    name: kiki-runtime-secrets
    key: REDIS_PASSWORD
```

**Create via AWS CLI:**
```bash
aws elasticache create-replication-group \
  --replication-group-description "KIKI Production Redis" \
  --engine redis \
  --cache-node-type cache.r7g.large \
  --num-cache-clusters 3 \
  --automatic-failover-enabled \
  --engine-version 7.0
```

### Azure Cache for Redis
```yaml
redis:
  address: "kiki-prod.redis.cache.windows.net:6380"
  passwordSecret:
    name: kiki-runtime-secrets
    key: REDIS_PASSWORD
```

### GCP Cloud Memorystore
```yaml
redis:
  address: "10.0.0.3:6379"  # Private IP in VPC
```

## Kubernetes Cluster Details

```bash
# EKS Example
CLUSTER_NAME="kiki-prod"
CLUSTER_REGION="us-east-1"
CLUSTER_VERSION="1.29"
ACCOUNT_ID="123456789012"

# AKS Example
RESOURCE_GROUP="kiki-prod-rg"
CLUSTER_NAME="kiki-prod-aks"
LOCATION="East US"

# GKE Example
PROJECT_ID="kiki-prod-12345"
CLUSTER_NAME="kiki-prod-gke"
ZONE="us-central1-a"
```

## Secrets to Populate

### AWS Secrets Manager

```bash
# Create secret in AWS Secrets Manager
aws secretsmanager create-secret \
  --name kiki/prod/sendgrid_api_key \
  --description "SendGrid API key for KIKI production" \
  --secret-string "SG.YOUR_API_KEY_HERE"

# Repeat for each secret:
aws secretsmanager create-secret --name kiki/prod/twilio_account_sid --secret-string "ACxxxxx"
aws secretsmanager create-secret --name kiki/prod/twilio_auth_token --secret-string "xxxxx"
aws secretsmanager create-secret --name kiki/prod/salesforce_client_id --secret-string "xxxxx"
aws secretsmanager create-secret --name kiki/prod/salesforce_client_secret --secret-string "xxxxx"
aws secretsmanager create-secret --name kiki/prod/hubspot_token --secret-string "pat-na1-xxxxx"
aws secretsmanager create-secret --name kiki/prod/shopify_api_key --secret-string "xxxxx"
aws secretsmanager create-secret --name kiki/prod/shopify_api_secret --secret-string "xxxxx"
aws secretsmanager create-secret --name kiki/prod/postgres_password --secret-string "xxxxx"
aws secretsmanager create-secret --name kiki/prod/redis_password --secret-string "xxxxx"
```

### Azure Key Vault

```bash
az keyvault secret set --vault-name kiki-prod-kv --name sendgrid-api-key --value "SG.xxxxx"
az keyvault secret set --vault-name kiki-prod-kv --name twilio-account-sid --value "ACxxxxx"
# ... repeat for others
```

### GCP Secret Manager

```bash
echo "SG.xxxxx" | gcloud secrets create sendgrid-api-key --data-file=-
echo "ACxxxxx" | gcloud secrets create twilio-account-sid --data-file=-
# ... repeat for others
```

## Email & Messaging

```bash
# SendGrid
SENDGRID_API_KEY="SG.YOUR_KEY_HERE"

# Twilio (SMS)
TWILIO_ACCOUNT_SID="ACxxxxx"
TWILIO_AUTH_TOKEN="xxxxx"
TWILIO_PHONE_NUMBER="+1234567890"
```

## CRM Integrations

```bash
# Salesforce
SALESFORCE_CLIENT_ID="3MVGxxxxxxxxxxxxx"
SALESFORCE_CLIENT_SECRET="xxxxx"
SALESFORCE_ORG_ID="00Dxxxxxxxxxxxxx"

# HubSpot
HUBSPOT_PRIVATE_APP_TOKEN="pat-na1-xxxxx"

# Shopify
SHOPIFY_SHOP_NAME="your-store.myshopify.com"
SHOPIFY_API_KEY="xxxxx"
SHOPIFY_API_SECRET="xxxxx"
```

## Database (Optional)

```bash
# PostgreSQL for persistent consent/DSR storage
POSTGRES_HOST="kiki-prod-db.xxxxx.rds.amazonaws.com"
POSTGRES_PORT="5432"
POSTGRES_DATABASE="kiki_prod"
POSTGRES_USER="kiki_admin"
POSTGRES_PASSWORD="xxxxx"
```

## GitHub Actions Secrets

```bash
# Encode kubeconfig in base64
cat ~/.kube/config | base64 -w 0

# Add to GitHub Secrets:
# - Name: KUBECONFIG_BASE64
# - Value: (paste base64 output)
```

**Command by OS:**
```bash
# macOS
cat ~/.kube/config | base64 | pbcopy

# Linux
cat ~/.kube/config | base64 -w 0 | xclip -selection clipboard

# Windows PowerShell
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content ~/.kube/config -Raw))) | Set-Clipboard
```

## TLS/SSL Configuration

```bash
# Let's Encrypt (free)
CERT_ISSUER="letsencrypt-prod"
CERT_EMAIL="ops@YOUR_DOMAIN.com"

# Or custom certificate
CERT_SECRET_NAME="kiki-tls-prod"
CERT_CRT_PATH="/path/to/certificate.crt"
CERT_KEY_PATH="/path/to/private.key"
```

## Scaling & Resource Limits

```yaml
# High-traffic production defaults
syncshield:
  replicaCount: 3
  autoscaling:
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

syncengage:
  replicaCount: 3
  autoscaling:
    minReplicas: 3
    maxReplicas: 10
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

syncvalue:  # LTV model (heavier)
  replicaCount: 2
  autoscaling:
    minReplicas: 2
    maxReplicas: 8
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 2Gi
```

## Observability

```bash
# OTEL Collector endpoint
OTEL_COLLECTOR_ENDPOINT="otel-collector.monitoring.svc.cluster.local:4317"

# Jaeger UI
JAEGER_QUERY_HOST="jaeger-query.monitoring.svc.cluster.local"
JAEGER_QUERY_PORT="16686"

# Prometheus
PROMETHEUS_HOST="prometheus.monitoring.svc.cluster.local"
PROMETHEUS_PORT="9090"

# Sampling rate (0.0 = none, 1.0 = all)
OTEL_TRACE_SAMPLER_ARG="0.1"  # 10% sampling for production
```

## Network & Security

```yaml
# Ingress rate limiting
ingress:
  annotations:
    nginx.ingress.kubernetes.io/limit-rps: "50"      # 50 requests/sec
    nginx.ingress.kubernetes.io/limit-connections: "10"  # 10 concurrent

# Network policies: Allow only specific namespaces
networkPolicy:
  allowExternal: false          # Reject traffic from outside cluster
  allowDNS: true               # Allow DNS (53)
  ingressFromNamespaces:
    - "monitoring"
    - "ingress-nginx"
```

## Compliance & Audit

```yaml
# GDPR audit log retention (in days)
RETENTION_DAYS: 2555  # 7 years

# Budget enforcement
MAX_BURST_BUDGET: 500    # Max spend in sliding window ($)
WINDOW_SECONDS: 3600     # 1 hour window
```

---

## Deployment Checklist

- [ ] Domain names resolved (shield.YOUR_DOMAIN, engage.YOUR_DOMAIN)
- [ ] Container registry available and credentials configured
- [ ] Redis endpoint ready (managed service with password)
- [ ] All secrets created in cloud secret manager
- [ ] IAM/RBAC roles created for service accounts
- [ ] External Secrets Operator installed in cluster
- [ ] cert-manager installed (for TLS)
- [ ] GitHub secrets configured (KUBECONFIG_BASE64)
- [ ] Helm chart values-prod.yaml updated
- [ ] First release tagged: `git tag v1.0.0 && git push origin v1.0.0`

