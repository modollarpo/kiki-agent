# 5-Variant Strategy System - Quick Reference

## The 5 Variants at a Glance

| Variant | Purpose | Best For | Platforms | Lift |
|---------|---------|----------|-----------|------|
| **Control** | Baseline benchmark | New products, baseline | Meta, LinkedIn, Google | 100% |
| **Lifestyle** | Emotional connection | Brand building, engagement | TikTok, Instagram, Pinterest | +33% |
| **Abstract** | Conceptual/emotional | Awareness, innovation | LinkedIn, YouTube, Instagram | +18% |
| **High-Contrast** | Visual impact | Mobile scrolling, conversion | TikTok, Meta, Instagram | +28% |
| **Data-Led** | Proof-driven | B2B, enterprise, trust | LinkedIn, Google, YouTube | +12% |

## Quick Start Examples

### 1. Generate Campaign Recommendations

```python
from variant_strategy import VariantStrategyFramework

recs = VariantStrategyFramework.get_variant_recommendations(
    campaign_type="awareness",          # awareness, consideration, conversion
    target_audience="consumer",         # consumer, sme, enterprise, developer
    budget_constraint="moderate",       # limited, moderate, premium
    optimization_goal="engagement"      # ctr, conversion, engagement, brand_lift
)
# Output: {"abstract": "35%", "lifestyle": "30%", "high_contrast": "25%", ...}
```

### 2. Build and Track Portfolio

```python
from variant_integration import VariantPortfolioBuilder, VariantPerformanceDashboard

builder = VariantPortfolioBuilder(
    campaign_id="CAMP-001",
    campaign_name="Q1 2026 Campaign",
    brand_name="TechBrand",
    product_name="Product Name"
)

portfolio = builder.build_with_recommendations(
    campaign_type="awareness",
    target_audience="consumer",
    budget_constraint="moderate",
    optimization_goal="engagement"
)

# Simulate data (or collect real data)
portfolio.impressions = {"control": 10000, "lifestyle": 10000, ...}
portfolio.clicks = {"control": 450, "lifestyle": 580, ...}
portfolio.conversions = {"control": 45, "lifestyle": 65, ...}

# Monitor performance
dashboard = VariantPerformanceDashboard(portfolio)
print(dashboard.render_dashboard())
```

### 3. Run A/B Test

```python
from variant_testing import ABTestFramework

result = ABTestFramework.run_test(
    variant_name="lifestyle",
    control_conversions=450,
    control_samples=10000,
    variant_conversions=580,
    variant_samples=10000,
    practical_significance_threshold=0.05  # 5% lift threshold
)

print(f"Lift: {(result.variant_metric - result.control_metric)*100:+.1%}")
print(f"Significance: {result.statistical_significance.value}")
print(f"Action: {result.recommendation}")
```

### 4. Get Budget Optimization

```python
from variant_integration import VariantOptimizationEngine

optimizer = VariantOptimizationEngine(portfolio)
optimized_budget = optimizer.get_budget_optimization(total_budget=50000)

for variant, budget in optimized_budget.items():
    print(f"{variant}: ${budget:,.0f}")
```

### 5. Plan Phased Rollout

```python
from variant_integration import VariantSequencer

sequencer = VariantSequencer(portfolio)
rollout = sequencer.get_phased_rollout(total_budget=50000)

for phase, details in rollout.items():
    print(f"{phase}: ${details['budget']:,.0f} - {details['variants']}")
```

## Campaign Strategy Decision Matrix

### Step 1: Identify Campaign Type
- **Awareness**: Build brand recognition
- **Consideration**: Compare options
- **Conversion**: Drive sales/signups
- **Loyalty**: Retain customers

### Step 2: Identify Target Audience
- **Consumer**: B2C audiences
- **SME**: Small/medium businesses
- **Enterprise**: Large organizations
- **Developer**: Technical audiences

### Step 3: Identify Budget Constraint
- **Limited**: < $5,000
- **Moderate**: $5,000 - $50,000
- **Premium**: > $50,000

### Step 4: Identify Optimization Goal
- **CTR**: Click-through rate
- **Conversion**: Conversion rate
- **Engagement**: Social engagement
- **Brand Lift**: Brand awareness increase

### Step 5: Get Recommendations
```python
recs = VariantStrategyFramework.get_variant_recommendations(
    campaign_type="awareness",
    target_audience="consumer",
    budget_constraint="moderate",
    optimization_goal="engagement"
)
```

## Pre-Built Recommendation Sets

### Consumer Awareness + Engagement
```
Abstract:      35%  (Emotion-driven awareness)
Lifestyle:     30%  (Connection-driven)
High-Contrast: 25%  (Attention-grabbing)
Data-Led:       5%
Control:        5%
```

### Enterprise Consideration + Conversion
```
Data-Led:      40%  (Proof-driven)
Control:       30%  (Baseline)
Abstract:      15%
Lifestyle:     10%
High-Contrast:  5%
```

### Consumer Conversion + CTR
```
High-Contrast: 35%  (Maximum impact)
Lifestyle:     30%  (Social proof)
Control:       20%
Data-Led:      10%
Abstract:       5%
```

### Developer Consideration + Conversion
```
Data-Led:      50%  (Technical proof)
Abstract:      25%  (Innovation focus)
Control:       15%
Lifestyle:      5%
High-Contrast:  5%
```

## Statistical Testing Quick Reference

### Sample Size Calculator
```python
sample_size = ABTestFramework.calculate_sample_size(
    baseline_conversion_rate=0.05,  # 5%
    mde_percent=5,                   # Detect 5% lift
    alpha=0.05,                      # 95% confidence
    beta=0.20                        # 80% power
)
# 5% baseline → 121,987 users per variant for 5% lift detection
# 2% baseline → 304,968 users per variant for 5% lift detection
```

### Statistical Significance Levels
- **Highly Significant**: p ≤ 0.01 (99% confident)
- **Significant**: p ≤ 0.05 (95% confident) ✅ Standard
- **Marginally Significant**: 0.05 < p ≤ 0.10 (90% confident)
- **Not Significant**: p > 0.10 (Inconclusive)

### Interpretation Guide
| Lift | p-value | Decision |
|------|---------|----------|
| +20% | 0.03 | ✅ DEPLOY - Statistically significant winner |
| +10% | 0.08 | ⚠️ MONITOR - Continue testing or deploy cautiously |
| +5% | 0.15 | ❌ INCONCLUSIVE - Need more data |
| -5% | 0.12 | 📉 PAUSE - Underperforming |

## Performance Tracking Checklists

### Daily Monitoring
- [ ] CTR trending up or down?
- [ ] Conversion rate stable?
- [ ] Cost per action within budget?
- [ ] Any variants underperforming (<80% control)?

### Weekly Analysis
- [ ] Sufficient sample size for significance?
- [ ] Statistical significance reached?
- [ ] Any platform-specific differences?
- [ ] Should budget be reallocated?

### Phase Transition
- [ ] Phase 1: 7 days baseline data collected
- [ ] Phase 2: Top performers identified
- [ ] Phase 3: Full portfolio deployment approved

## Variant Selection by Audience Awareness

### Cold Audience (Unaware)
**Recommended:** High-Contrast → Lifestyle
- Need immediate attention capture
- High-Contrast for scroll-stopping
- Lifecycle to build connection

### Warm Audience (Aware)
**Recommended:** Lifestyle → Data-Led
- Familiar with brand
- Lifestyle for deeper engagement
- Data-Led for consideration support

### Hot Audience (Decision Stage)
**Recommended:** Data-Led → Control
- Ready to decide
- Data-Led for proof/ROI
- Control for direct product benefit

## Learning Capture Template

```python
sequencer.add_learning(
    variant_type="lifestyle",
    key_insight="44% higher engagement with warm audiences",
    audience_segment="warm_awareness",
    performance_lift=0.44,
    recommendation="Prioritize lifestyle in nurturing sequences",
    priority="high"  # high, medium, low
)
```

## Common Workflows

### Campaign Launch
```
1. Build portfolio with recommendations
2. Deploy Phase 1 (Control only)
3. Collect 7 days baseline
4. Deploy Phase 2 (Top performers)
5. Monitor 7 days
6. Deploy Phase 3 (Full portfolio)
7. Monitor 14 days
```

### Performance Optimization
```
1. Get current metrics
2. Calculate optimized budget allocation
3. Identify scaling opportunities
4. Pause underperformers
5. Test adjustments
6. Monitor new performance
```

### Learning Loop
```
1. Capture performance lift
2. Document key insight
3. Identify audience segment
4. Create recommendation
5. Apply to next campaign
6. Test hypothesis
```

## File Locations

| Module | Purpose | Lines |
|--------|---------|-------|
| `cmd/creative/variant_strategy.py` | Core strategy framework | 800+ |
| `cmd/creative/variant_testing.py` | Statistical testing | 600+ |
| `cmd/creative/variant_integration.py` | Integration & dashboards | 500+ |
| `docs/VARIANT_STRATEGY_SYSTEM.md` | Full documentation | 400+ |

## Key Functions Summary

### variant_strategy.py
- `VariantStrategyFramework.get_variant_recommendations()` - Strategic recommendations
- `VariantStrategyFramework.calculate_portfolio_lift()` - Lift vs control
- `VariantStrategyFramework.generate_strategy_report()` - Comprehensive report
- `VariantSelector.select_variant_for_audience()` - Intelligent selection
- `VariantSelector.print_variant_guide()` - Complete guide

### variant_testing.py
- `ABTestFramework.calculate_sample_size()` - Sample size calculation
- `ABTestFramework.run_test()` - Run A/B test with stats
- `MultiVariantExperiment.run_statistical_tests()` - Multi-arm test
- `VariantLearningSystem.add_learning()` - Capture insights

### variant_integration.py
- `VariantPortfolioBuilder.build_with_recommendations()` - Build portfolio
- `VariantSequencer.get_phased_rollout()` - Rollout plan
- `VariantPerformanceDashboard.render_dashboard()` - Live dashboard
- `VariantOptimizationEngine.get_budget_optimization()` - Budget allocation

## Support

For detailed API documentation, see:
- `docs/VARIANT_STRATEGY_SYSTEM.md` - Complete documentation
- Individual module docstrings - Comprehensive API details
- `demo_*.py` files - Working examples
