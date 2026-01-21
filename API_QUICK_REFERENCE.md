# API Quick Reference Guide

**Last Updated:** January 2026

## Quick Start (5 minutes)

### 1. Start Services

```bash
# Terminal 1: REST API (recommended for development)
python -m uvicorn api.rest_api:app --port 8000 --reload

# Access interactive docs at:
# http://localhost:8000/docs
```

### 2. Test with cURL

```bash
# Health check
curl http://localhost:8000/health

# Create portfolio
curl -X POST http://localhost:8000/api/portfolios \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Campaign",
    "brand": "MyBrand",
    "product": "MyProduct",
    "total_budget": 100000,
    "variant_types": ["control", "lifestyle", "abstract", "high_contrast", "data_led"]
  }'
```

### 3. Use Python Client

```python
from api.rest_client import RestApiClient

client = RestApiClient()
portfolio = client.create_portfolio(
    name="My Campaign",
    brand="MyBrand",
    product="MyProduct",
    total_budget=100000,
    variant_types=["control", "lifestyle", "abstract", "high_contrast", "data_led"],
)
print(portfolio['portfolio']['portfolio_id'])
```

---

## API Endpoints Cheat Sheet

### Portfolios

```bash
# Create
POST /api/portfolios

# Read
GET /api/portfolios/{id}

# List
GET /api/portfolios?brand=MyBrand&limit=10

# Update
PUT /api/portfolios/{id}
```

### Variants

```bash
# Get library
GET /api/variants/library

# Get specific variant
GET /api/variants/library?variant_type=lifestyle

# Get recommendations
POST /api/variants/recommendations
{
  "campaign_type": "awareness",
  "target_audience": "tech professionals",
  "platform": "linkedin"
}
```

### Testing

```bash
# Calculate sample size
POST /api/testing/sample-size
{
  "baseline_rate": 0.05,
  "minimum_detectable_effect": 0.05
}

# Analyze experiment
POST /api/testing/analyze?control_variant=control&test_variants=lifestyle,abstract
{
  "variant_conversions": {...},
  "variant_exposures": {...}
}
```

### Vision Validation

```bash
# Validate single image
POST /api/validation/image
{
  "variant_type": "lifestyle",
  "image_path": "/path/to/image.jpg",
  "use_mock": true
}

# Validate portfolio images
POST /api/validation/portfolio
{
  "portfolio_id": "port_123",
  "variant_image_paths": {
    "control": "/images/control.jpg",
    "lifestyle": "/images/lifestyle.jpg"
  },
  "use_mock": true
}

# Get quality report
GET /api/validation/quality-report/{portfolio_id}
```

### Insights

```bash
# Capture
POST /api/insights?portfolio_id=port_123&insight_type=performance&variant=lifestyle&description=High%20CTR

# Get
GET /api/insights/{portfolio_id}?limit=10
```

### Utility

```bash
# Health check
GET /health

# API info
GET /info

# Documentation
GET /docs (Swagger)
GET /redoc (ReDoc)
```

---

## Response Examples

### Success Response

```json
{
  "success": true,
  "message": "Operation successful",
  "portfolio": {
    "portfolio_id": "port_abc123",
    "name": "My Campaign",
    "brand": "MyBrand",
    "total_budget": 100000,
    ...
  }
}
```

### Error Response

```json
{
  "detail": "Portfolio not found"
}
```

### Validation Response

```json
{
  "success": true,
  "message": "Image validated successfully",
  "validation": {
    "product_confidence": 0.85,
    "safety_score": 1.0,
    "quality_score": 0.88,
    "overall_score": 0.86,
    "is_approved": true,
    "recommendations": [
      "Excellent product visibility"
    ]
  }
}
```

---

## Python Client Quick Ref

```python
from api.rest_client import RestApiClient

client = RestApiClient()

# Portfolios
client.create_portfolio(name, brand, product, total_budget, variant_types)
client.get_portfolio(portfolio_id)
client.list_portfolios(brand, limit, offset)

# Variants
client.get_variant_library(variant_type)
client.get_variant_recommendations(campaign_type, target_audience, platform)

# Testing
client.calculate_sample_size(baseline_rate, minimum_detectable_effect)
client.analyze_experiment(control, test_variants, conversions, exposures)

# Validation
client.validate_image(variant_type, image_path, use_mock)
client.validate_portfolio(portfolio_id, variant_image_paths, use_mock)

# Insights
client.capture_insight(portfolio_id, insight_type, variant, description)
client.get_insights(portfolio_id, variant, limit)

# Health
client.health_check()
client.get_info()
```

---

## gRPC Quick Ref

```python
from api.grpc_client import VariantStrategyClientSync

client = VariantStrategyClientSync()

# Create portfolio
response = client.create_portfolio(
    name="Campaign",
    brand="Brand",
    product="Product",
    total_budget=100000,
    variant_types=["control", "lifestyle"]
)

# Get recommendations
response = client.get_variant_recommendation(
    campaign_type="awareness",
    target_audience="tech pros",
    platform="linkedin"
)

# Calculate sample size
response = client.calculate_sample_size(
    baseline_rate=0.05,
    mde=0.05
)

client.close()
```

---

## Variant Types

| Variant | Best For | CTR Lift | Conv. Lift | Platforms |
|---------|----------|----------|-----------|-----------|
| **Control** | Baseline | 1.0x | 1.0x | Meta, LinkedIn, Google |
| **Lifestyle** | Engagement | 1.15x | 1.25x | TikTok, Instagram, Shorts |
| **Abstract** | Awareness | 0.95x | 1.18x | LinkedIn, YouTube, Twitter |
| **High-Contrast** | Scrolling | 1.28x | 1.32x | TikTok, Meta, Instagram |
| **Data-Led** | Conversions | 1.05x | 1.15x | LinkedIn, YouTube, Google |

---

## Quality Tiers

| Tier | Score | Status |
|------|-------|--------|
| **Production Ready** | ≥0.90 | Deploy immediately |
| **Approved** | ≥0.80 | Deploy with monitoring |
| **Needs Revision** | ≥0.70 | Improve before deploy |
| **Rejected** | <0.70 | Do not deploy |

---

## Campaign Types

| Type | Use Case | Recommended Variant |
|------|----------|-------------------|
| **Awareness** | Brand discovery | Abstract, Data-Led |
| **Consideration** | Evaluation | Lifestyle, Control |
| **Conversion** | Direct sales | High-Contrast, Data-Led |
| **Retention** | Customer loyalty | Lifestyle, Abstract |

---

## Common Workflows

### Workflow 1: Create & Test Campaign

```python
client = RestApiClient()

# 1. Create portfolio
portfolio = client.create_portfolio(...)
port_id = portfolio['portfolio']['portfolio_id']

# 2. Validate images
validation = client.validate_portfolio(portfolio_id=port_id, ...)

# 3. Get recommendations
recs = client.get_variant_recommendations(...)

# 4. Calculate sample size
sample = client.calculate_sample_size(...)

# 5. Run campaign (external)

# 6. Analyze results
analysis = client.analyze_experiment(...)

print(f"Winner: {analysis['winner']}")
```

### Workflow 2: Quick Image Validation

```python
client = RestApiClient()

result = client.validate_image(
    variant_type="lifestyle",
    image_path="/images/lifestyle.jpg",
    use_mock=True,
)

if result['validation']['is_approved']:
    print("✓ Ready for production")
else:
    print("✗ Needs revision")
    print(result['validation']['recommendations'])
```

### Workflow 3: Get Variant Recommendations

```python
client = RestApiClient()

recs = client.get_variant_recommendations(
    campaign_type="awareness",
    target_audience="tech professionals",
    platform="linkedin",
)

for rec in recs['recommendations']:
    print(f"{rec['variant_name']}: {rec['recommendation_score']:.2f}")
    print(f"  {rec['reasoning']}")
```

---

## Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CLIP Configuration
CLIP_USE_MOCK=true
CLIP_MODEL=ViT-B/32

# Logging
LOG_LEVEL=INFO
```

---

## Deployment Commands

### Docker Compose

```bash
# Build
docker-compose build

# Start
docker-compose up

# Logs
docker-compose logs -f rest-api

# Stop
docker-compose down
```

### Kubernetes

```bash
# Deploy
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods
kubectl get svc

# View logs
kubectl logs -f deployment/variant-api-rest
```

### Cloud Run (Google Cloud)

```bash
gcloud run deploy variant-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 512Mi
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Change port or kill process |
| Module not found | Install dependencies: `pip install -r requirements.txt` |
| Connection refused | Ensure server is running |
| CLIP not downloading | Use mock mode: `CLIP_USE_MOCK=true` |
| High memory usage | Reduce model size or enable caching |

---

## Performance Tips

- ✅ Use gRPC for high-throughput scenarios
- ✅ Use REST for web/mobile clients
- ✅ Enable mock mode for development/testing
- ✅ Use connection pooling for multiple requests
- ✅ Cache variant library (rarely changes)
- ✅ Implement rate limiting in production

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 400 | Bad request |
| 404 | Not found |
| 500 | Server error |

---

## File Locations

- API Server: `api/rest_api.py`
- gRPC Server: `api/grpc_server.py`
- REST Client: `api/rest_client.py`
- gRPC Client: `api/grpc_client.py`
- Protobuf: `proto/variant_strategy.proto`
- Documentation: `API_DOCUMENTATION.md`
- Setup Guide: `API_SETUP_GUIDE.md`

---

## Links

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health
- **API**: http://localhost:8000/api

---

## Contact & Support

- Check documentation at `/docs`
- Review examples in `api/rest_client.py`
- See troubleshooting in `API_SETUP_GUIDE.md`
