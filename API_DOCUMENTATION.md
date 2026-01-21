# Variant Strategy & Vision Guard API Documentation

**Version:** 1.0.0  
**Last Updated:** January 2026  
**API Type:** gRPC + REST/JSON

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [REST API Reference](#rest-api-reference)
5. [gRPC Reference](#grpc-reference)
6. [Client Libraries](#client-libraries)
7. [Examples](#examples)
8. [Error Handling](#error-handling)

---

## Overview

The Variant Strategy & Vision Guard API provides comprehensive endpoints for:

- **Portfolio Management**: Create, retrieve, and manage creative variant portfolios
- **Variant Operations**: Access variant library and get strategy recommendations
- **Testing & Analysis**: Calculate sample sizes and analyze multi-variant experiments
- **Vision Guard**: Validate images using CLIP embeddings with variant-specific checks
- **Insights**: Capture and retrieve campaign insights
- **Optimization**: Get budget allocation and deployment recommendations

### Key Features

- **Dual Protocol Support**: Both gRPC and REST/JSON for flexibility
- **CLIP Integration**: OpenAI CLIP embeddings for image validation
- **Production-Ready**: Mock mode for testing, real model support for production
- **Comprehensive Validation**: Product detection, safety, quality, composition, brand fit
- **Multi-Variant Testing**: Statistical framework for 5-variant experiments
- **Budget Optimization**: Quality-based budget allocation and deployment strategy

---

## Architecture

```text
┌─────────────────────────────────────────────────────┐
│         Client Applications                          │
│  (Python, JavaScript, Go, Java, C#, etc.)          │
└─────────┬──────────────────────────────┬────────────┘
          │                              │
          │ gRPC (Protobuf)   REST/JSON  │
          │                              │
┌─────────▼──────────────────────────────▼────────────┐
│  API Gateway                                         │
│  ┌────────────────────────────────────────────────┐ │
│  │ gRPC Server (Port 50051)  REST API (8000)    │ │
│  └──────────┬──────────────────────┬─────────────┘ │
└─────────────┼──────────────────────┼────────────────┘
              │                      │
              │                      │
┌─────────────▼──────────────────────▼────────────────┐
│  Service Implementation Layer                       │
│  ┌─────────────────────────────────────────────┐   │
│  │ VariantStrategyService | VariantGuardService│   │
│  └─────────────────────────────────────────────┘   │
└─────────────┬──────────────────────┬────────────────┘
              │                      │
              │                      │
┌─────────────▼──────────────────────▼────────────────┐
│  Business Logic                                      │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │ Variant      │ Variant      │ Vision Guard │    │
│  │ Portfolio    │ Testing      │ Validation   │    │
│  └──────────────┴──────────────┴──────────────┘    │
└──────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- Dependencies: `grpc`, `protobuf`, `fastapi`, `uvicorn`, `requests`

### Installation

```bash
# Install dependencies
pip install grpcio grpcio-tools protobuf fastapi uvicorn requests

# Generate protobuf code (if needed)
python -m grpc_tools.protoc -I proto/ \
  --python_out=api/generated \
  --pyi_out=api/generated \
  --grpc_python_out=api/generated \
  proto/variant_strategy.proto
```

### Starting the Services

#### Start gRPC Server

```bash
python api/grpc_server.py [port]
# Default port: 50051
```

#### Start REST API

```bash
python -m uvicorn api.rest_api:app --host 0.0.0.0 --port 8000
```

#### Interactive API Documentation

Once REST API is running, visit:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## REST API Reference

### Base URL

```text
http://localhost:8000/api
```

### Health & Info

#### Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-19T10:30:00",
  "service": "Variant Strategy API"
}
```

#### Service Info

```http
GET /info
```

**Response:**

```json
{
  "service": "Variant Strategy & Vision Guard API",
  "version": "1.0.0",
  "description": "REST API for creative variant management and CLIP validation",
  "endpoints": {
    "portfolios": "/api/portfolios",
    "variants": "/api/variants",
    "recommendations": "/api/recommendations",
    "validation": "/api/validation",
    "testing": "/api/testing"
  }
}
```

---

### Portfolio Management

#### Create Portfolio

```http
POST /portfolios
Content-Type: application/json

{
  "name": "Q1 2026 Campaign",
  "brand": "TechBrand",
  "product": "AI Assistant Pro",
  "total_budget": 100000,
  "variant_types": ["control", "lifestyle", "abstract", "high_contrast", "data_led"],
  "variant_budgets": {
    "control": 20000,
    "lifestyle": 20000,
    "abstract": 20000,
    "high_contrast": 20000,
    "data_led": 20000
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Portfolio created successfully",
  "portfolio": {
    "portfolio_id": "port_abc123def456",
    "name": "Q1 2026 Campaign",
    "brand": "TechBrand",
    "product": "AI Assistant Pro",
    "total_budget": 100000,
    "variants": [...],
    "status": "active",
    "created_at": "2026-01-19T10:30:00",
    "updated_at": "2026-01-19T10:30:00"
  }
}
```

#### Get Portfolio

```http
GET /portfolios/{portfolio_id}
```

**Response:**

```json
{
  "success": true,
  "message": "Portfolio retrieved",
  "portfolio": { ... }
}
```

#### List Portfolios

```http
GET /portfolios?brand=TechBrand&limit=10&offset=0
```

**Query Parameters:**

- `brand` (optional): Filter by brand
- `limit` (int, default: 100): Maximum results
- `offset` (int, default: 0): Pagination offset

---

### Variant Operations

#### Get Variant Library

```http
GET /variants/library
```

**Optional Query Parameters:**

- `variant_type`: Get specific variant (e.g., "lifestyle")

**Response:**

```json
{
  "success": true,
  "variants": {
    "control": {
      "name": "Control",
      "description": "Product-focused baseline...",
      "ctr_lift_potential": 1.0,
      "conversion_lift": 1.0,
      ...
    },
    "lifestyle": {
      "name": "Lifestyle",
      "description": "Emotional connection...",
      "ctr_lift_potential": 1.15,
      "conversion_lift": 1.25,
      ...
    },
    ...
  }
}
```

#### Get Variant Recommendations

```http
POST /variants/recommendations
Content-Type: application/json

{
  "campaign_type": "awareness",
  "target_audience": "tech professionals",
  "platform": "linkedin",
  "goal": "brand_awareness"
}
```

**Campaign Types:**

- `awareness`: Brand/product awareness
- `consideration`: Driving consideration
- `conversion`: Direct conversions
- `retention`: Customer retention

**Platforms:**

- `meta`: Facebook/Instagram
- `tiktok`: TikTok
- `google`: Google Ads
- `linkedin`: LinkedIn
- `pinterest`: Pinterest
- `youtube`: YouTube

**Response:**

```json
{
  "recommendations": [
    {
      "variant_type": "abstract",
      "variant_name": "Abstract",
      "recommendation_score": 0.92,
      "reasoning": "High engagement for awareness campaigns",
      "characteristics": { ... }
    },
    ...
  ],
  "explanation": "Recommendations for awareness campaign"
}
```

---

### Testing & Analysis

#### Calculate Sample Size

```http
POST /testing/sample-size
Content-Type: application/json

{
  "baseline_rate": 0.05,
  "minimum_detectable_effect": 0.05,
  "alpha": 0.05,
  "power": 0.80
}
```

**Parameters:**

- `baseline_rate`: Current conversion rate (e.g., 5%)
- `minimum_detectable_effect`: Minimum improvement to detect (e.g., 5%)
- `alpha`: Significance level (default: 0.05)
- `power`: Statistical power (default: 0.80)

**Response:**

```json
{
  "sample_size_per_variant": 121987,
  "total_sample_size": 609935,
  "explanation": "Required 121987 samples per variant for 5-variant test"
}
```

#### Analyze Experiment

```http
POST /testing/analyze?control_variant=control&test_variants=lifestyle,abstract,high_contrast,data_led
Content-Type: application/json

{
  "variant_conversions": {
    "control": 500,
    "lifestyle": 625,
    "abstract": 590,
    "high_contrast": 660,
    "data_led": 560
  },
  "variant_exposures": {
    "control": 10000,
    "lifestyle": 10000,
    "abstract": 10000,
    "high_contrast": 10000,
    "data_led": 10000
  }
}
```

**Response:**

```json
{
  "success": true,
  "analysis": [
    {
      "variant": "control",
      "conversion_rate": 0.05,
      "lift": 0.0,
      "p_value": 1.0,
      "is_significant": false
    },
    {
      "variant": "high_contrast",
      "conversion_rate": 0.066,
      "lift": 0.32,
      "p_value": 0.001,
      "is_significant": true,
      "recommendation": "Winner - deploy to 100%"
    },
    ...
  ],
  "winner": "high_contrast",
  "winner_lift": 0.32
}
```

---

### Vision Guard Validation

#### Validate Single Image

```http
POST /validation/image
Content-Type: application/json

{
  "variant_type": "lifestyle",
  "image_path": "/path/to/image.jpg",
  "portfolio_id": "port_abc123",
  "use_mock": true
}
```

**Response:**

```json
{
  "success": true,
  "message": "Image validated successfully",
  "validation": {
    "product_confidence": 0.85,
    "safety_score": 1.0,
    "quality_score": 0.88,
    "brand_fit": 0.75,
    "composition": 0.92,
    "overall_score": 0.86,
    "is_approved": true,
    "recommendations": [
      "Excellent product visibility",
      "Strong composition alignment"
    ],
    "variant_checks": {
      "product_prominence": true,
      "person_visible": true,
      "bold_colors": true,
      "text_visible": false,
      "data_visualization": false
    },
    "detected_objects": ["person", "product", "environment"],
    "detected_concepts": ["professional", "modern", "clean"],
    "safety_flags": []
  }
}
```

#### Validate Portfolio Images

```http
POST /validation/portfolio
Content-Type: application/json

{
  "portfolio_id": "port_abc123",
  "variant_image_paths": {
    "control": "/path/to/control.jpg",
    "lifestyle": "/path/to/lifestyle.jpg",
    "abstract": "/path/to/abstract.jpg",
    "high_contrast": "/path/to/high_contrast.jpg",
    "data_led": "/path/to/data_led.jpg"
  },
  "use_mock": true
}
```

**Response:**

```json
{
  "success": true,
  "message": "Portfolio validated successfully",
  "variant_results": [
    {
      "variant": "lifestyle",
      "validation": { ... },
      "quality_tier": "Production Ready"
    },
    {
      "variant": "high_contrast",
      "validation": { ... },
      "quality_tier": "Approved"
    },
    ...
  ],
  "quality_scores": {
    "lifestyle": 0.92,
    "high_contrast": 0.85,
    "abstract": 0.78,
    "control": 0.82,
    "data_led": 0.75
  }
}
```

**Quality Tiers:**

- `Production Ready` (≥0.90): Ready for immediate deployment
- `Approved` (≥0.80): Ready after minor adjustments
- `Needs Revision` (≥0.70): Requires improvements before use
- `Rejected` (<0.70): Do not use in production

---

### Insights

#### Capture Insight

```http
POST /insights?portfolio_id=port_abc123&insight_type=performance&variant=lifestyle&description=High%20CTR%20observed
```

**Insight Types:**

- `performance`: Performance observations
- `trend`: Trend identification
- `issue`: Problems or blockers
- `opportunity`: Growth opportunities

**Response:**

```json
{
  "success": true,
  "insight_id": "insight_0",
  "message": "Insight captured"
}
```

#### Get Insights

```http
GET /insights/{portfolio_id}?variant=lifestyle&limit=100
```

**Response:**

```json
{
  "success": true,
  "portfolio_id": "port_abc123",
  "insights": [
    {
      "insight_id": "insight_0",
      "portfolio_id": "port_abc123",
      "variant": "lifestyle",
      "type": "performance",
      "description": "High CTR observed",
      "created_at": "2026-01-19T10:30:00"
    },
    ...
  ],
  "total": 5
}
```

---

## gRPC Reference

### Services

#### VariantStrategyService

```protobuf
service VariantStrategyService {
  // Portfolio Management
  rpc CreatePortfolio (CreatePortfolioRequest) returns (PortfolioResponse);
  rpc GetPortfolio (GetPortfolioRequest) returns (PortfolioResponse);
  rpc ListPortfolios (ListPortfoliosRequest) returns (ListPortfoliosResponse);
  rpc UpdatePortfolio (UpdatePortfolioRequest) returns (PortfolioResponse);
  
  // Variant Operations
  rpc GetVariantLibrary (GetVariantLibraryRequest) returns (VariantLibraryResponse);
  rpc GetVariantRecommendation (GetVariantRecommendationRequest) returns (VariantRecommendationResponse);
  
  // Testing & Optimization
  rpc CalculateSampleSize (SampleSizeRequest) returns (SampleSizeResponse);
  rpc CreateExperiment (CreateExperimentRequest) returns (ExperimentResponse);
  rpc AnalyzeExperiment (AnalyzeExperimentRequest) returns (ExperimentAnalysisResponse);
  
  // Learning
  rpc CaptureInsight (CaptureInsightRequest) returns (InsightResponse);
  rpc GetInsights (GetInsightsRequest) returns (GetInsightsResponse);
}
```

#### VariantGuardService

```protobuf
service VariantGuardService {
  rpc ValidateImage (ImageValidationRequest) returns (ImageValidationResponse);
  rpc ValidatePortfolioImages (PortfolioValidationRequest) returns (PortfolioValidationResponse);
  rpc GetQualityReport (QualityReportRequest) returns (QualityReportResponse);
  rpc GetDeploymentRecommendations (DeploymentRecommendationRequest) returns (DeploymentRecommendationResponse);
}
```

### Example gRPC Usage (Python)

```python
import grpc
from variant_strategy_pb2 import CreatePortfolioRequest
from variant_strategy_pb2_grpc import VariantStrategyServiceStub

# Create channel
channel = grpc.aio.insecure_channel('localhost:50051')
stub = VariantStrategyServiceStub(channel)

# Create portfolio
request = CreatePortfolioRequest(
    name="My Campaign",
    brand="MyBrand",
    product="My Product",
    total_budget=50000,
    variant_types=["control", "lifestyle"],
)

response = await stub.CreatePortfolio(request)
print(f"Portfolio ID: {response.portfolio.portfolio_id}")
```

---

## Client Libraries

### Python

#### REST Client

```python
from api.rest_client import RestApiClient

client = RestApiClient()
portfolio = client.create_portfolio(
    name="Q1 Campaign",
    brand="TechBrand",
    product="AI Pro",
    total_budget=100000,
    variant_types=["control", "lifestyle", "abstract", "high_contrast", "data_led"],
)
```

#### gRPC Client

```python
from api.grpc_client import VariantStrategyClientSync

client = VariantStrategyClientSync()
response = client.create_portfolio(
    name="Q1 Campaign",
    brand="TechBrand",
    product="AI Pro",
    total_budget=100000,
    variant_types=["control", "lifestyle", "abstract", "high_contrast", "data_led"],
)
```

### JavaScript/TypeScript

```typescript
// Using fetch API
const response = await fetch('http://localhost:8000/api/portfolios', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Q1 Campaign',
    brand: 'TechBrand',
    product: 'AI Pro',
    total_budget: 100000,
    variant_types: ['control', 'lifestyle', 'abstract', 'high_contrast', 'data_led'],
  }),
});

const portfolio = await response.json();
```

### cURL

```bash
curl -X POST http://localhost:8000/api/portfolios \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 Campaign",
    "brand": "TechBrand",
    "product": "AI Pro",
    "total_budget": 100000,
    "variant_types": ["control", "lifestyle", "abstract", "high_contrast", "data_led"]
  }'
```

---

## Examples

### Complete Workflow: Campaign Setup & Analysis

```python
from api.rest_client import RestApiClient

client = RestApiClient()

# 1. Create portfolio
portfolio = client.create_portfolio(
    name="Q1 2026 Campaign",
    brand="TechBrand",
    product="AI Assistant Pro",
    total_budget=100000,
    variant_types=["control", "lifestyle", "abstract", "high_contrast", "data_led"],
)
portfolio_id = portfolio['portfolio']['portfolio_id']

# 2. Validate images
validation = client.validate_portfolio(
    portfolio_id=portfolio_id,
    variant_image_paths={
        "control": "/images/control.jpg",
        "lifestyle": "/images/lifestyle.jpg",
        "abstract": "/images/abstract.jpg",
        "high_contrast": "/images/high_contrast.jpg",
        "data_led": "/images/data_led.jpg",
    },
    use_mock=True,
)

# 3. Get recommendations
recommendations = client.get_variant_recommendations(
    campaign_type="awareness",
    target_audience="tech professionals",
    platform="linkedin",
)

# 4. Calculate sample size
sample_size = client.calculate_sample_size(
    baseline_rate=0.05,
    minimum_detectable_effect=0.05,
)

# 5. Analyze results after campaign
analysis = client.analyze_experiment(
    control_variant="control",
    test_variants=["lifestyle", "abstract", "high_contrast", "data_led"],
    variant_conversions={
        "control": 500,
        "lifestyle": 625,
        "abstract": 590,
        "high_contrast": 660,
        "data_led": 560,
    },
    variant_exposures={
        "control": 10000,
        "lifestyle": 10000,
        "abstract": 10000,
        "high_contrast": 10000,
        "data_led": 10000,
    },
)

print(f"Winner: {analysis['winner']}")
print(f"Lift: {analysis['winner_lift']:.1%}")
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Portfolio not found"
}
```

### gRPC Status Codes

- `OK` (0): Success
- `INVALID_ARGUMENT` (3): Invalid parameters
- `NOT_FOUND` (5): Resource not found
- `INTERNAL` (13): Server error

---

## Rate Limiting & Performance

- No rate limiting implemented (can be added in production)
- Mock mode for testing: ~10-50ms per request
- Real model mode: ~100-500ms per request (depends on CLIP server)

## Support

For issues, questions, or contributions:

- Create an issue in the repository
- Check documentation at `/docs` (Swagger)
- Review examples in `api/rest_client.py` and `api/grpc_client.py`
