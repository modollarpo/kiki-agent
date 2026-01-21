# KIKI Production Infrastructure

## Overview
KIKI comprises two core agents:
- SyncShield: Regulatory guardrail and budget governor (port 8081)
- SyncEngage: Post-acquisition loyalty automation (port 8083)

This document defines a production-ready, secure, observable, and scalable architecture spanning environments: dev, staging, prod.

## Architecture (Cloud-agnostic)
- Ingress: Managed Load Balancer + NGINX Ingress Controller (TLS 1.3) with rate limiting and security headers
- Runtime: Kubernetes (EKS/GKE/AKS)
- Images: OCI registry (GHCR/ECR/GCR)
- Data: Redis (managed: ElastiCache/Memorystore) for sliding-window budget; Postgres (managed) for analytics/DSR state (future)
- Messaging: SendGrid/Twilio (outbound only from SyncEngage)
- Observability: Prometheus + Grafana, Loki (logs), Tempo (traces) via OpenTelemetry
- Secrets: External Secrets Operator backed by cloud secret manager
- CI/CD: GitHub Actions → Registry → Helm deploy (progressive rollout)
- Security: mTLS in cluster (optional), network policies, OPA Gatekeeper/Conftest, image signing (cosign), SBOMs

## Environments
- Dev: Shared cluster, feature namespaces, permissive budgets
- Staging: Prod parity, synthetic traffic, canary testing
- Prod: HA, HPA tuned, PDBs, multi-AZ nodes, backups and DR

## Networking
- Ingress rules:
  - shield.example.com → SyncShield Service:8081
  - engage.example.com → SyncEngage Service:8083
- Private egress to Redis/Datastores via VPC endpoints when possible
- NetworkPolicies isolate namespaces and deny-all by default

## Workloads
- SyncShield: HTTP 8081, budget governor + compliance endpoints
- SyncEngage: HTTP 8083, retention triggers; calls SyncShield `/check`
- SyncValue: gRPC 50051, LTV predictions
- SyncFlow: HTTP 8082, execution/bidding; depends on SyncShield + SyncValue

## Scalability
- HPA for CPU 60% target and RPS signals via custom metrics
- PDB minAvailable=1, TopologySpread across zones
- Request/limit defaults: 100m/300Mi requests → 500m/512Mi limits (tune via SLOs)

## Reliability
- Readiness/liveness probes; startup probes for cold start
- Retry policies and circuit breakers for outbound calls
- Budget governor relies on managed Redis; if unavailable, allow or deny based on policy (prod: deny)

## Security
- TLS everywhere (ingress and service-to-service via mTLS if enabled)
- JWT-based service auth or NetworkPolicy-based service isolation
- Audit logs: CSV+JSON dual logs retained 7 years; PII hashed (SHA-256)
- Secrets: mounted via External Secrets; no secrets in images/manifests
- Container: non-root user, drop capabilities, readOnlyRootFilesystem
- Supply chain: SLSA level targets with SBOM and cosign signatures
 - Pod Security Admission: `restricted` level enforced via namespace labels

## Observability
- Structured logs (JSON), request IDs, correlation with traceparent
- Metrics: request_rate, error_rate, latency (RED), budget window metrics
- Traces: HTTP client calls from SyncEngage → SyncShield
 - OpenTelemetry Collector: receives OTLP and exports to logging/Prometheus

## CI/CD
- CI: lint, test, build, SBOM (syft), image scan (trivy)
- CD: helm upgrade --install with progressive rollout (25/50/100), auto-rollback on SLO breach
 - Pages: static landing auto-deploys from `web/landing/`

## SRE Runbook (abridged)
- Incident triage based on SLO dashboards (latency, errors, budgets)
- Budget breach: check Redis health, recent deploys, traffic spikes
- Compliance: verify audit logs existence and rotation; consent endpoints
- Rollback: helm rollback kiki <REVISION>

## Data Protection
- Retention: audit logs 2555 days; marketing data 730 days; session 90 days
- Encryption: AES-256-GCM at rest; TLS 1.3 in transit; keys via KMS

## Backups & DR
- Logs: shipped to object storage with lifecycle rules
- Redis: managed snapshots; RPO < 15 min
- Terraform state: remote backend with locking

## Domain/Certificates
- DNS: shield.example.com, engage.example.com
- Certificates: cert-manager + ACME/Let’s Encrypt (prod: DNS01)

---
For implementation, see k8s/, infra/terraform/, and .github/ workflows in this repo.
