# KIKI SyncShield Platform

A TRL6/7-ready AI revenue engine that combines SyncValue (AI brain),
SyncFlow (execution), and SyncShield (governance) with observability via
Prometheus and Grafana.

## Components

- SyncValue (AI): gRPC service for dRNN LTV predictions (<1ms target).
- SyncFlow (Execution): Multi-platform bidder/circuit-breaker client with
  resilience logic.
- SyncShield (Governance): Policy/check endpoint and budget guardrails.
- Observability: Prometheus metrics (port 9090), Grafana Command Center
  dashboard.

## Getting Started

### Prereqs

- Go 1.21+
- Python 3.10+ (for AI server)
- Docker / Docker Compose
- Node 18+ (for markdownlint) optional

### Local (Docker Compose)

```bash
cd c:/Users/USER/Documents/KIKI
docker compose up --build
```

Services:

- SyncValue gRPC: :50051
- SyncShield HTTP: :8081
- SyncFlow client: depends on SyncValue/Shield
- Redis: :6379

### Helm (Kubernetes)

Helm chart lives in [helm/syncshield](helm/syncshield).

- Images: set in [helm/syncshield/values.yaml](helm/syncshield/values.yaml)
  (placeholders `ghcr.io/kiki/syncvalue:1.0.0` and `ghcr.io/kiki/syncflow:1.0.0`).
- Deployments: [deployment-syncvalue.yaml](helm/syncshield/templates/deployment-syncvalue.yaml),
  [deployment-syncflow.yaml](helm/syncshield/templates/deployment-syncflow.yaml).
- HA: HPAs, PDBs, topology spread; enable via values.
- Observability: ServiceMonitor toggles for Prometheus Operator.

Install:

```bash
helm upgrade --install syncshield helm/syncshield -n syncshield --create-namespace
```

### Observability (Grafana + Prometheus)

- Dashboard JSON: [grafana/syncshield-dashboard.json](grafana/syncshield-dashboard.json)
- Provisioning: [grafana/provisioning/dashboards/syncshield.yaml](grafana/provisioning/dashboards/syncshield.yaml)
- Default mounts (for Docker Grafana):
  - `/etc/grafana/provisioning/dashboards` ← c:/Users/USER/Documents/KIKI/etc/grafana/provisioning/dashboards
  - `/var/lib/grafana/dashboards/syncshield` ← c:/Users/USER/Documents/KIKI/var/lib/grafana/dashboards/syncshield

Key panels:

- Resilience (circuit state): `syncflow_circuit_breaker_state_count`
- Financial Guardrail gauge: `sum(syncflow_budget_spent_micros) / max(syncflow_budget_limit_micros)`
- LTV Momentum: `sum(syncvalue_predicted_ltv_total) / sum(syncflow_spend_total)`

### Prometheus Targets

- Metrics ports: SyncValue :9090, SyncFlow :9090
- ServiceMonitor templates: [servicemonitor-syncshield.yaml](helm/syncshield/templates/servicemonitor-syncshield.yaml)

## Development

### Generate Protos

```bash
protoc --go_out=. --go-grpc_out=. \
  --go_opt=paths=source_relative --go-grpc_opt=paths=source_relative \
  api/proto/syncvalue.proto

protoc --go_out=. --go-grpc_out=. \
  --go_opt=paths=source_relative --go-grpc_opt=paths=source_relative \
  api/proto/syncflow.proto
```

Python stubs:

```bash
python -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. api/proto/syncvalue.proto
```

### Run AI server (dev)

```bash
python cmd/syncvalue/server.py
```

### Run client (dev)

```bash
go run cmd/syncflow/main.go
```

## Testing

Run all tests:

```bash

```

## Linting

Markdown:

```bash
npx -y -p markdownlint-cli markdownlint "docs/**/*.md" "cmd/**/*.md" "README.md"
```

## Useful Paths

- Docs: [docs](docs)
- Examples (heartbeat demo): [cmd/syncshield/examples](cmd/syncshield/examples)
- Helm chart: [helm/syncshield](helm/syncshield)
- Grafana assets: [grafana](grafana)

## Deployment Notes

- Set real image tags in values before deploy.
- Enable mTLS annotations via `global.mtlsAnnotations` if running under a mesh.
- Tune HPAs (CPU/custom metric) and PDB minAvailable per SLOs.

## Roadmap (excerpt)

- TRL7 hardening: Kubernetes service mesh, canary rollouts.
- Profit-based billing (SyncShield audit logs).
- Additional platform connectors (beyond current 14 verified sandboxes).

## OaaS Billing Engine (Profit-Share Model)

Transition from SaaS (fixed fee) → OaaS (outcome-based revenue share).

The billing engine ([cmd/billing/ooaS_billing_engine.py](cmd/billing/ooaS_billing_engine.py))
reads the immutable audit trail and calculates KIKI's earnings based on
margin improvement.

### Model

**Baseline ROAS**: Platform default (e.g., Google Ads native = 3.0x).  
**KIKI ROAS**: Actual LTV / Spend from audit trail.  
**Margin Improvement**: (KIKI ROAS - Baseline) / Baseline * 100%.  
**Additional Revenue**: Margin Improvement * Client Spend.  
**KIKI Earnings**: kiki_share_pct * Additional Revenue (default: 15%).

### Example

Client spends $1,000:
- Baseline ROAS: 3.0x → expected return $3,000
- KIKI ROAS: 4.47x → actual return $4,470
- Margin Improvement: 49%
- Additional Revenue: $1,470
- KIKI Earnings: 15% * $1,470 = **$220.50**

### Usage

```bash
python cmd/billing/ooaS_billing_engine.py
```

Outputs invoice JSON to [invoices/](invoices/) directory. Integrate with
accounting system or subscription platform (Stripe, Zuora, etc.).

### Payment & CRM Integration

**Billing Adapters**:
- [cmd/billing/stripe_adapter.py](cmd/billing/stripe_adapter.py): Create charges
  and subscriptions via Stripe API.
- [cmd/billing/zuora_adapter.py](cmd/billing/zuora_adapter.py): Enterprise billing
  with multi-currency, revenue recognition (ASC 606), dunning.
- [cmd/billing/paypal_adapter.py](cmd/billing/paypal_adapter.py): Global payments
  via PayPal (180+ countries, subscriptions, webhooks).

**CRM Integrations**:
- [cmd/billing/crm_adapter.py](cmd/billing/crm_adapter.py): Sync to Salesforce
  (opportunities, account metrics, revenue records) or HubSpot (deals, engagement notes).

**Unified Orchestrator**:
- [cmd/billing/orchestrator.py](cmd/billing/orchestrator.py): End-to-end workflow:
  audit trail → invoice → payment → CRM.

### Setup (Environment Variables)

```bash
# Stripe
export STRIPE_SECRET_KEY=sk_live_xxxxx

# Zuora
export ZUORA_API_URL=https://api.zuora.com
export ZUORA_CLIENT_ID=client_id_xxxxx
export ZUORA_CLIENT_SECRET=secret_xxxxx

# PayPal
export PAYPAL_CLIENT_ID=client_id_xxxxx
export PAYPAL_CLIENT_SECRET=secret_xxxxx
export PAYPAL_MODE=sandbox  # or "live"

# Salesforce
export SALESFORCE_INSTANCE=https://myorg.salesforce.com
export SALESFORCE_API_TOKEN=token_xxxxx

# HubSpot
export HUBSPOT_API_KEY=pat-xxxxx
```

### Example Workflow

```python
from orchestrator import KIKIBillingOrchestrator, BillingProvider, CRMProvider

# Initialize with Stripe + Salesforce
orchestrator = KIKIBillingOrchestrator(
    audit_csv_path="shield_audit.csv",
    billing_provider=BillingProvider.STRIPE,
    crm_provider=CRMProvider.SALESFORCE,
)

# Generate monthly invoices
invoices = orchestrator.generate_monthly_invoices(
    period_start, period_end, baseline_roas=3.0
)

# Process and sync to payment + CRM
for invoice in invoices:
    result = orchestrator.process_invoice(invoice, customer_mappings)
    orchestrator.save_invoice(invoice)
```
