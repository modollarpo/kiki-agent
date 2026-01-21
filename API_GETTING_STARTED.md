# API Getting Started - Copy & Paste Commands

Quick commands to get the API running in under 5 minutes.

---

## 🚀 Start REST API (Recommended)

```bash
cd C:\Users\USER\Documents\KIKI
python -m uvicorn api.rest_api:app --port 8000 --reload
```

Then visit: **http://localhost:8000/docs**

---

## 📝 First Test - Create Portfolio

### Option 1: Browser (Easiest)

1. Go to http://localhost:8000/docs
2. Find "POST /api/portfolios"
3. Click "Try it out"
4. Click "Execute"

### Option 2: cURL

```bash
curl -X POST http://localhost:8000/api/portfolios \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Campaign",
    "brand": "TestBrand",
    "product": "TestProduct",
    "total_budget": 50000,
    "variant_types": ["control", "lifestyle", "abstract", "high_contrast", "data_led"]
  }'
```

### Option 3: Python

```bash
cd C:\Users\USER\Documents\KIKI
python
```

Then in Python:
```python
from api.rest_client import RestApiClient

client = RestApiClient()
result = client.create_portfolio(
    name="My First Campaign",
    brand="TestBrand",
    product="TestProduct",
    total_budget=50000,
    variant_types=["control", "lifestyle", "abstract", "high_contrast", "data_led"],
)
print(f"Portfolio ID: {result['portfolio']['portfolio_id']}")
```

---

## 🎨 Test Image Validation

```bash
curl -X POST http://localhost:8000/api/validation/image \
  -H "Content-Type: application/json" \
  -d '{
    "variant_type": "lifestyle",
    "image_path": "/images/lifestyle.jpg",
    "use_mock": true
  }'
```

---

## 📊 Test Sample Size Calculation

```bash
curl -X POST http://localhost:8000/api/testing/sample-size \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_rate": 0.05,
    "minimum_detectable_effect": 0.05
  }'
```

---

## 📚 Get Variant Recommendations

```bash
curl -X POST http://localhost:8000/api/variants/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_type": "awareness",
    "target_audience": "tech professionals",
    "platform": "linkedin"
  }'
```

---

## 🐳 Start with Docker Compose

```bash
cd C:\Users\USER\Documents\KIKI

# Build images
docker-compose build

# Start services
docker-compose up

# View logs
docker-compose logs -f rest-api

# Stop
docker-compose down
```

---

## 🔧 Start gRPC Server (Optional)

In a separate terminal:

```bash
cd C:\Users\USER\Documents\KIKI
python api/grpc_server.py 50051
```

Then use gRPC client:

```python
from api.grpc_client import VariantStrategyClientSync

client = VariantStrategyClientSync()
response = client.create_portfolio(
    name="My Campaign",
    brand="TestBrand",
    product="TestProduct",
    total_budget=50000,
    variant_types=["control", "lifestyle"],
)
print(f"Portfolio: {response.portfolio.portfolio_id}")
client.close()
```

---

## 📖 Documentation Links

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **API Info**: http://localhost:8000/info

---

## ✅ Verify Installation

```bash
# Check if API is running
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2026-01-19T...","service":"Variant Strategy API"}
```

---

## 🆘 Troubleshooting

### Port Already in Use

```bash
# Windows - Find process on port 8000
netstat -ano | findstr :8000

# Kill it
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Module Not Found

```bash
pip install grpcio grpcio-tools protobuf fastapi uvicorn pydantic requests
```

### PYTHONPATH Issues

```bash
# Add to your terminal session
set PYTHONPATH=C:\Users\USER\Documents\KIKI;%PYTHONPATH%
```

---

## 🎯 Common Operations

### List all portfolios

```bash
curl http://localhost:8000/api/portfolios
```

### Get specific portfolio

```bash
curl http://localhost:8000/api/portfolios/{portfolio_id}
```

### Get variant library

```bash
curl http://localhost:8000/api/variants/library
```

### Get variant library for specific variant

```bash
curl "http://localhost:8000/api/variants/library?variant_type=lifestyle"
```

### Capture insight

```bash
curl -X POST "http://localhost:8000/api/insights?portfolio_id=port_123&insight_type=performance&variant=lifestyle&description=High%20CTR%20observed"
```

### Get insights

```bash
curl "http://localhost:8000/api/insights/port_123?limit=10"
```

---

## 📊 Full Workflow Example

```bash
# 1. Create portfolio
PORTFOLIO=$(curl -s -X POST http://localhost:8000/api/portfolios \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Campaign 1",
    "brand": "MyBrand",
    "product": "Product",
    "total_budget": 100000,
    "variant_types": ["control", "lifestyle", "abstract", "high_contrast", "data_led"]
  }')

PORTFOLIO_ID=$(echo $PORTFOLIO | grep -o '"portfolio_id":"[^"]*' | head -1 | cut -d'"' -f4)

echo "Created portfolio: $PORTFOLIO_ID"

# 2. Get recommendations
curl -X POST http://localhost:8000/api/variants/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_type": "awareness",
    "target_audience": "tech professionals",
    "platform": "linkedin"
  }'

# 3. Calculate sample size
curl -X POST http://localhost:8000/api/testing/sample-size \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_rate": 0.05,
    "minimum_detectable_effect": 0.05
  }'

# 4. Validate portfolio images
curl -X POST http://localhost:8000/api/validation/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "'$PORTFOLIO_ID'",
    "variant_image_paths": {
      "control": "/images/control.jpg",
      "lifestyle": "/images/lifestyle.jpg",
      "abstract": "/images/abstract.jpg",
      "high_contrast": "/images/high_contrast.jpg",
      "data_led": "/images/data_led.jpg"
    },
    "use_mock": true
  }'
```

---

## 🚀 Production Deployment

### AWS Lambda

```bash
# Build and push to ECR
docker build -t variant-api .
docker tag variant-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/variant-api:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/variant-api:latest

# Create Lambda function
aws lambda create-function \
  --function-name variant-strategy-api \
  --role arn:aws:iam::123456789:role/lambda-role \
  --code ImageUri=123456789.dkr.ecr.us-east-1.amazonaws.com/variant-api:latest \
  --timeout 30 \
  --memory-size 512
```

### Google Cloud Run

```bash
gcloud run deploy variant-strategy-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 512Mi
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name variant-api \
  --image myregistry.azurecr.io/variant-api:latest \
  --cpu 1 \
  --memory 0.5 \
  --ports 8000
```

### Kubernetes

```bash
kubectl apply -f k8s-deployment.yaml
kubectl get service variant-api-service
```

---

## 📚 Next Steps After Starting

1. **Read Quick Reference**: Open `API_QUICK_REFERENCE.md`
2. **Read Full Documentation**: Open `API_DOCUMENTATION.md`
3. **Review Examples**: Check `api/rest_client.py` and `api/grpc_client.py`
4. **Deploy**: Follow `API_SETUP_GUIDE.md`

---

## 💡 Pro Tips

- Use `/docs` for interactive testing
- Use `?limit=10` to paginate results
- Use `use_mock=true` for image validation testing
- Check `variant_checks` in validation results for variant-specific issues
- Campaign types: `awareness`, `consideration`, `conversion`, `retention`

---

## 🔗 Quick Links

| Link | Purpose |
|------|---------|
| http://localhost:8000/docs | API Documentation |
| http://localhost:8000/redoc | Alternative Docs |
| http://localhost:8000/health | Health Check |
| http://localhost:8000/api/portfolios | List Portfolios |
| http://localhost:8000/api/variants/library | Variant Library |

---

**That's it! You're ready to use the API. Start with the REST API and visit /docs for interactive testing.**
