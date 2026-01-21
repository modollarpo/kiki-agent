# 🚀 SyncCreate™ - Quick Start Guide

> **AI-powered creative generation with brand safety guardrails**

## ⚡ 5-Minute Demo

```bash
# Run the demo
cd c:\Users\USER\Documents\KIKI
python cmd/creative/synccreate.py
```

**What you'll see:**
- ✅ 5 creative variants generated (Control, Lifestyle, Abstract, High-Contrast, Data-Led)
- ✅ 100% safety scores (Three-Gate Safety Check)
- ✅ Platform-optimized outputs (Meta 1:1 in demo)
- ✅ gRPC/JSON API format for SyncFlow™

## 🎯 Core Concepts

### 1. LTV-Driven Personas (from SyncValue™)

```python
persona = AudiencePersona(
    persona_id="high_value_churner",
    segment_name="High-Value At-Risk Customers",
    ltv_score=0.87,  # Predicted lifetime value
    churn_risk=0.65,  # Probability of churning
    ltv_trigger="Win-back campaign"  # Why we're targeting now
)
```

### 2. 5-Variant Strategy

| Variant | Purpose | Example |
|---------|---------|---------|
| Control | Baseline product shot | "Product Pro" + USP |
| Lifestyle | Emotional connection | Person using product |
| Abstract | Aspirational | Visualize their success |
| High-Contrast | Scroll-stopping | Bold colors + attention hook |
| Data-Led | Proof-driven | USP + feature highlights |

### 3. Three-Gate Safety Check

- **GATE 1:** Visual Compliance (CLIP validation)
- **GATE 2:** Copy Integrity (prohibited terms, clickbait)
- **GATE 3:** Identity Guard (DEI compliance)

**Safety Threshold:** 0.8/1.0 (violations: -0.2 each, warnings: -0.05 each)

## 🧪 Test Safety Filters

```bash
python tests/test_synccreate_safety.py
```

**Example results:**
```
✅ "Professional copy" → Score: 1.00 (PASSED)
❌ "Cheap guaranteed!" → Score: 0.40 (BLOCKED)
```

## 📊 Sample Output

**Generated Variant:**
```json
{
  "id": "variant_20260119172529_control_94326446_0",
  "type": "control",
  "creative": {
    "image_url": "creatives/variant_xxx.webp",
    "headline": "KIKI Agent™ Pro",
    "body": "3x ROAS improvement in 30 days",
    "cta": "Shop Now"
  },
  "quality": {
    "safety_score": 1.0,
    "brand_compliant": true,
    "vision_verified": true
  }
}
```

## 🔧 Integration Points

**Input:** SyncValue™ provides personas + LTV triggers  
**Processing:** SyncCreate™ generates brand-safe creatives  
**Output:** SyncFlow™ receives variants for bidding optimization

## 📚 Full Documentation

- **Architecture:** [`SYNCCREATE_ARCHITECTURE.md`](./SYNCCREATE_ARCHITECTURE.md)
- **Code:** [`cmd/creative/synccreate.py`](../cmd/creative/synccreate.py)
- **Output:** [`creatives/enterprise_demo_q1_2026_variants.json`](../creatives/enterprise_demo_q1_2026_variants.json)

## 🚦 Status

✅ **Production-Ready** (mocked SD/CLIP integrations, real API framework in place)

**Version:** 2.0.0  
**Last Updated:** 2026-01-19
