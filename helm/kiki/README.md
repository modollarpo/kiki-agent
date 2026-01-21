# KIKI Helm Chart

This chart deploys KIKI services: SyncShield, SyncEngage, SyncValue, SyncFlow.

## Install
```bash
helm upgrade --install kiki ./helm/kiki -f ./helm/kiki/values-dev.yaml
```

## Values
- `global.imageRegistry`: base image registry (e.g., ghcr.io/org/kiki)
- `global.namespace`: target namespace (default: kiki)
- `global.domain`: `shield`, `engage` hosts
- `redis.address`: Redis endpoint for SyncShield
- `sync*.*`: per-service enable, image, replicas, resources
- `ingress.*`: enable, rate limits
- `externalSecrets.*`: toggle and provider config (template only)
- `otel.enabled`: toggle OTEL Collector (use k8s/otel-collector.yaml or add a subchart)

## Notes
- Secrets are managed via External Secrets Operator; update `k8s/external-secrets.yaml` or add subchart.
- For production, set image tags to immutable versions and replace domains.
