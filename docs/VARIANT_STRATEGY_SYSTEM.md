# 5-Variant Strategy System Documentation

## Overview

The **5-Variant Strategy System** is a comprehensive framework for managing creative variations across campaigns. It provides structured approaches to variant selection, testing, optimization, and learning.

## Architecture

### Three-Layer System

```
┌─────────────────────────────────────────────────┐
│   Integration Layer (variant_integration.py)    │
│   Portfolio builder, dashboard, optimizer       │
└─────────────────────────────────────────────────┘
                        ↓
    ┌─────────────────────────────────────────────┐
    │  Core Systems (strategy + testing modules)  │
    │  - Variant Strategy Framework               │
    │  - A/B Testing Framework                    │
    │  - Learning System                          │
    └─────────────────────────────────────────────┘
                        ↓
    ┌─────────────────────────────────────────────┐
    │        5 Creative Variants (Enums)          │
    │  - Control                                  │
    │  - Lifestyle                                │
    │  - Abstract                                 │
    │  - High-Contrast                            │
    │  - Data-Led                                 │
    └─────────────────────────────────────────────┘
```

## The 5 Variants

### 1. Control
**Purpose:** Baseline performance benchmark

- **Visual Focus:** Product hero shot, clean presentation, professional setting
- **Messaging:** Direct, clear value proposition, USP-focused
- **Best For:** New products, professional audiences, baseline measurements
- **Platforms:** Meta, LinkedIn, Google, YouTube
- **Performance Lift:** 100% (baseline)
  - CTR: 100%
  - Conversion: 100%
  - Engagement: 100%
- **Est. CPV:** $0.08-0.12
- **Design:** Simple, moderate colors, 6s optimal

### 2. Lifestyle
**Purpose:** Emotional connection through real-world usage

- **Visual Focus:** Person using product, authentic moments, natural environments
- **Messaging:** Narrative-driven, benefit-focused, aspirational
- **Best For:** Brand building, lifestyle products, consumer engagement
- **Platforms:** TikTok, Instagram, Pinterest, YouTube Shorts
- **Performance Lift:** +33% average
  - CTR: +15%
  - Conversion: +25%
  - Engagement: +35%
- **Est. CPV:** $0.06-0.10
- **Design:** Moderate complexity, warm colors, 15s optimal

### 3. Abstract
**Purpose:** Conceptual visualization of emotions and aspirations

- **Visual Focus:** Abstract concept art, metaphorical imagery, emotional themes
- **Messaging:** Inspirational, motivational, pain-point-focused
- **Best For:** Awareness campaigns, emotional branding, innovation messaging
- **Platforms:** LinkedIn, YouTube, Instagram, Twitter/X
- **Performance Lift:** +18% average
  - CTR: -5% (lower but shares drive engagement)
  - Conversion: +18%
  - Engagement: +42% (highly shareable)
- **Est. CPV:** $0.05-0.09
- **Design:** Complex, high colors, 20s optimal

### 4. High-Contrast
**Purpose:** Bold, scroll-stopping design with maximum visual impact

- **Visual Focus:** Vibrant colors, striking composition, eye-catching elements
- **Messaging:** Urgent, action-oriented, FOMO-driven
- **Best For:** Feed optimization, mobile scrolling, lower-funnel conversion
- **Platforms:** TikTok, Meta, Instagram, Snapchat
- **Performance Lift:** +28% average
  - CTR: +28% (highest CTR)
  - Conversion: +32%
  - Engagement: +25%
- **Est. CPV:** $0.07-0.11
- **Design:** Very high intensity, moderate complexity, 8s optimal

### 5. Data-Led
**Purpose:** Proof-driven creative highlighting USP, metrics, social proof

- **Visual Focus:** Infographic style, data visualization, proof elements
- **Messaging:** Evidence-based, trust-building, ROI-focused
- **Best For:** B2B marketing, enterprise sales, performance marketing
- **Platforms:** LinkedIn, Google Ads, YouTube, industry publications
- **Performance Lift:** +12% average
  - CTR: -8% (less eye-catching)
  - Conversion: +38% (highest conversion for aware audiences)
  - Engagement: -12% (less shareable)
- **Est. CPV:** $0.12-0.18 (higher CPV but better ROI for qualified leads)
- **Design:** Complex, low intensity, 12s optimal

## Module: variant_strategy.py

### Core Classes

#### VariantCharacteristics
Metadata for each variant type including performance metrics, use cases, and design profile.

```python
from variant_strategy import VARIANT_STRATEGY_LIBRARY

# Access characteristics
lifestyle_char = VARIANT_STRATEGY_LIBRARY["lifestyle"]
print(f"Best for: {lifestyle_char.best_for}")
print(f"Platforms: {lifestyle_char.platform_fit}")
print(f"Conversion lift: {lifestyle_char.conversion_lift:.0%}")
```

#### VariantPortfolio
Container for managing 5 variants and their performance metrics.

```python
from variant_strategy import VariantPortfolio

portfolio = VariantPortfolio(
    campaign_id="CAMP-001",
    campaign_name="Q1 2026 Awareness",
    brand_name="TechBrand",
    product_name="AI Assistant Pro"
)

# Track performance
portfolio.impressions = {"control": 10000, "lifestyle": 10000, ...}
portfolio.clicks = {"control": 450, "lifestyle": 580, ...}
portfolio.conversions = {"control": 45, "lifestyle": 65, ...}

# Get metrics
metrics = portfolio.calculate_metrics()
print(metrics["lifestyle"]["ctr"])  # CTR for lifestyle variant

# Get recommendation
best = portfolio.recommend_variant()
```

#### VariantStrategyFramework
Strategic decision engine for variant selection and allocation.

```python
from variant_strategy import VariantStrategyFramework

# Get recommendations
recs = VariantStrategyFramework.get_variant_recommendations(
    campaign_type="awareness",
    target_audience="consumer",
    budget_constraint="moderate",
    optimization_goal="engagement"
)
# Returns: {"abstract": "35%", "lifestyle": "30%", ...}

# Calculate lift
lift = VariantStrategyFramework.calculate_portfolio_lift(portfolio)
# Returns per-variant lift vs control

# Generate report
report = VariantStrategyFramework.generate_strategy_report(portfolio)
print(report)
```

#### VariantSelector
Intelligent variant selection based on audience context.

```python
from variant_strategy import VariantSelector

# Select best variant for context
variant, reasoning = VariantSelector.select_variant_for_audience(
    target_audience="cold",
    awareness_level="awareness"
)
# Returns: ("high_contrast", "Needs immediate attention capture")

# Get detailed characteristics
char = VariantSelector.get_variant_characteristics(variant)

# Print selection guide
guide = VariantSelector.print_variant_guide()
```

## Module: variant_testing.py

### Statistical Testing Framework

#### ABTestFramework
Statistical testing with Chi-square approximation and p-value calculation.

```python
from variant_testing import ABTestFramework, StatisticalSignificance

# Calculate sample size
sample_size = ABTestFramework.calculate_sample_size(
    baseline_conversion_rate=0.05,  # 5%
    mde_percent=5,                   # Detect 5% lift
    alpha=0.05,                      # 95% confidence
    beta=0.20                        # 80% power
)
# Returns: 121,987 users per variant

# Run A/B test
result = ABTestFramework.run_test(
    variant_name="lifestyle",
    control_conversions=450,
    control_samples=10000,
    variant_conversions=580,
    variant_samples=10000
)

print(f"Lift: {(result.variant_metric - result.control_metric)*100:+.1%}")
print(f"Statistical Significance: {result.statistical_significance.value}")
print(f"Recommendation: {result.recommendation}")
```

#### MultiVariantExperiment
Framework for running multi-armed experiments.

```python
from variant_testing import MultiVariantExperiment, ExperimentArm

experiment = MultiVariantExperiment(
    experiment_id="EXP-001",
    experiment_name="Brand Awareness Campaign",
    start_date=datetime.now() - timedelta(days=7),
    hypothesis="Abstract variant will have higher engagement"
)

# Add arms
experiment.add_arm("control", ExperimentArm(
    variant_type="control",
    total_users=10000,
    conversions=450,
    impressions=50000,
    clicks=2500
))

experiment.add_arm("lifestyle", ExperimentArm(
    variant_type="lifestyle",
    total_users=10000,
    conversions=580,
    impressions=50000,
    clicks=3100
))

# Run statistical tests
results = experiment.run_statistical_tests()

# Rank variants
ranking = experiment.rank_variants()
for variant, conv_rate in ranking:
    print(f"{variant}: {conv_rate:.2%}")

# Generate report
print(experiment.generate_report())
```

#### VariantLearningSystem
System for capturing and applying learnings from testing.

```python
from variant_testing import VariantLearningSystem, VariantLearning
from datetime import datetime

learning_system = VariantLearningSystem()

learning_system.add_learning(VariantLearning(
    variant_type="lifestyle",
    learning_date=datetime.now(),
    key_insight="Lifestyle drives 44% higher engagement with warm audiences",
    audience_segment="warm_awareness",
    performance_lift=0.44,
    recommendation="Prioritize lifestyle for nurturing sequences",
    priority="high"
))

# Get insights
top_insights = learning_system.get_top_insights(limit=5)
report = learning_system.generate_insights_report()
```

## Module: variant_integration.py

### Complete Workflow Components

#### VariantPortfolioBuilder
Builder pattern for creating and configuring portfolios.

```python
from variant_integration import VariantPortfolioBuilder

builder = VariantPortfolioBuilder(
    campaign_id="CAMP-001",
    campaign_name="Q1 Awareness",
    brand_name="TechBrand",
    product_name="AI Assistant"
)

# Get recommendations
recs = builder.recommend_strategy(
    campaign_type="awareness",
    target_audience="consumer",
    budget_constraint="moderate",
    optimization_goal="engagement"
)

# Build portfolio
portfolio = builder.build_with_recommendations(
    campaign_type="awareness",
    target_audience="consumer",
    budget_constraint="moderate",
    optimization_goal="engagement"
)
```

#### VariantSequencer
Phased rollout planning with learning capture.

```python
from variant_integration import VariantSequencer

sequencer = VariantSequencer(portfolio)

# Get phased rollout
rollout = sequencer.get_phased_rollout(
    total_budget=50000,
    phases=3
)

# Phase 1: Control only ($5,000)
# Phase 2: Top performers ($15,000)
# Phase 3: Full portfolio ($30,000)

# Record learnings
sequencer.add_learning(
    variant_type="lifestyle",
    key_insight="44% higher engagement with warm audiences",
    audience_segment="warm_awareness",
    performance_lift=0.44,
    recommendation="Prioritize for nurturing",
    priority="high"
)

# Get insights
insights = sequencer.get_insights_report()
```

#### VariantPerformanceDashboard
Real-time performance monitoring and recommendations.

```python
from variant_integration import VariantPerformanceDashboard

dashboard = VariantPerformanceDashboard(portfolio)

# Get snapshot
snapshot = dashboard.get_snapshot()
print(f"Best variant: {snapshot.best_performing_variant}")
print(f"Total conversions: {snapshot.total_conversions}")

# Render dashboard
dashboard_text = dashboard.render_dashboard()
print(dashboard_text)
```

#### VariantOptimizationEngine
Budget allocation optimization based on performance.

```python
from variant_integration import VariantOptimizationEngine

optimizer = VariantOptimizationEngine(portfolio)

# Get optimized budget
optimized = optimizer.get_budget_optimization(total_budget=50000)
# Allocates higher budget to better performers

# Get adjustment recommendations
adjustments = optimizer.get_variant_adjustments()
for variant, recommendation in adjustments.items():
    print(f"{variant}: {recommendation}")
```

## Campaign Strategy Recommendations Matrix

### By Campaign Type × Audience × Budget × Goal

**Awareness + Consumer + Moderate + Engagement:**
```
Abstract:      35%  (Build awareness through emotion)
Lifestyle:     30%  (Connect with aspirational content)
High-Contrast: 25%  (Stop scrolls on mobile)
Data-Led:       5%  (Not relevant for awareness)
Control:        5%  (Benchmark)
```

**Consideration + Enterprise + Premium + Conversion:**
```
Data-Led:      40%  (Build trust with proof)
Control:       30%  (Professional baseline)
Abstract:      15%  (Conceptual value)
Lifestyle:     10%  (Executive persona)
High-Contrast:  5%  (Not suitable for B2B)
```

**Conversion + Consumer + Moderate + Conversion:**
```
High-Contrast: 35%  (Maximum impact)
Lifestyle:     30%  (Social proof via usage)
Control:       20%  (Direct product benefit)
Data-Led:      10%  (ROI focus)
Abstract:       5%  (Lower conversion)
```

## Complete Workflow Example

```python
from datetime import datetime, timedelta
from variant_integration import (
    VariantPortfolioBuilder,
    VariantSequencer,
    VariantPerformanceDashboard,
    VariantOptimizationEngine
)

# Step 1: Build Portfolio with Recommendations
builder = VariantPortfolioBuilder(
    campaign_id="CAMP-001",
    campaign_name="Q1 Awareness",
    brand_name="TechBrand",
    product_name="AI Assistant"
)

portfolio = builder.build_with_recommendations(
    campaign_type="awareness",
    target_audience="consumer",
    budget_constraint="moderate",
    optimization_goal="engagement"
)

# Step 2: Plan Phased Rollout
sequencer = VariantSequencer(portfolio)
rollout = sequencer.get_phased_rollout(total_budget=50000)

# Step 3: Deploy Phase 1, collect data...
# (Simulate performance data)
portfolio.impressions = {"control": 10000, "lifestyle": 10000, ...}
portfolio.clicks = {"control": 450, "lifestyle": 580, ...}
portfolio.conversions = {"control": 45, "lifestyle": 65, ...}

# Step 4: Monitor Performance
dashboard = VariantPerformanceDashboard(portfolio)
dashboard_snapshot = dashboard.get_snapshot()
print(dashboard.render_dashboard())

# Step 5: Optimize Budget
optimizer = VariantOptimizationEngine(portfolio)
optimized_budget = optimizer.get_budget_optimization(total_budget=50000)
adjustments = optimizer.get_variant_adjustments()

# Step 6: Record Learnings
sequencer.add_learning(
    variant_type="lifestyle",
    key_insight="44% higher engagement with warm audiences",
    audience_segment="warm_awareness",
    performance_lift=0.44,
    recommendation="Prioritize for nurturing sequences",
    priority="high"
)

print(sequencer.get_insights_report())
```

## Best Practices

### Selection
1. **Start with Control** - Always include control for benchmarking
2. **Match Campaign Type** - Use recommended allocations by campaign type
3. **Audience Awareness** - Cold audiences need High-Contrast; warm audiences benefit from Lifestyle
4. **Platform Fit** - Respect platform recommendations for each variant

### Testing
1. **Statistical Significance** - Run until p ≤ 0.05 for reliability
2. **Minimum Sample Size** - Calculate needed sample size upfront
3. **Multi-Variant Tests** - Use ANOVA/Chi-square for 5-arm experiments
4. **Practical Significance** - Set minimum detectable effect (MDE) threshold

### Optimization
1. **Phased Rollout** - Deploy conservatively (10% → 30% → 60%)
2. **Performance Monitoring** - Check daily CTR and conversion trends
3. **Budget Reallocation** - Shift budget toward higher performers
4. **Pause Underperformers** - Stop variants with <10% control performance

### Learning
1. **Document Insights** - Capture learning with performance lift and audience
2. **Build Playbooks** - Consolidate learnings into repeatable patterns
3. **Cross-Campaign** - Share learnings across similar campaigns
4. **Test Hypotheses** - Build learning system gradually

## Integration with SyncCreate™

The 5-Variant Strategy System integrates seamlessly with SyncCreate™:

```python
from cmd.creative.synccreate import SyncCreateEngine
from variant_integration import VariantPortfolioBuilder

# Build portfolio
builder = VariantPortfolioBuilder(...)
portfolio = builder.build_with_recommendations(...)

# Generate variants using SyncCreate
engine = SyncCreateEngine()
variants = engine.generate_creative_variants(
    product_metadata={...},
    audience_persona={...},
    num_variants=5
)

# Add to portfolio
for variant in variants:
    portfolio.add_variant(variant.strategy.value.lower(), variant)

# Track performance
dashboard = VariantPerformanceDashboard(portfolio)
```

## Output Formats

### Portfolio Export
```json
{
  "campaign_id": "CAMP-001",
  "campaign_name": "Q1 Awareness",
  "variants": {
    "control": {"headline": "...", "metrics": {...}},
    "lifestyle": {"headline": "...", "metrics": {...}}
  }
}
```

### Dashboard JSON
```json
{
  "portfolio_id": "CAMP-001",
  "best_variant": "lifestyle",
  "average_ctr": 5.05,
  "total_conversions": 290,
  "recommendations": [...]
}
```

## API Reference

See individual module docstrings for complete API documentation:
- `variant_strategy.py` - 800+ lines of strategy framework
- `variant_testing.py` - 600+ lines of statistical testing
- `variant_integration.py` - 500+ lines of integration layer

All modules include comprehensive docstrings and type hints.
