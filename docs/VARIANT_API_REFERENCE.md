# 5-Variant Strategy System - API Reference

## Quick Navigation

- [variant_strategy.py](#variant_strategypy)
- [variant_testing.py](#variant_testingpy)
- [variant_integration.py](#variant_integrationpy)

---

## variant_strategy.py

### Classes

#### `VariantCharacteristics`
Metadata for each variant type.

**Attributes:**
```python
name: str                  # Display name
description: str          # Variant description
visual_focus: str        # Visual design focus
messaging_style: str     # Messaging approach
best_for: List[str]      # Use cases
platform_fit: List[str]  # Recommended platforms
ctr_lift_potential: float  # CTR lift vs control
conversion_lift: float     # Conversion lift
engagement_lift: float     # Engagement lift
average_cpv: str          # Cost per view
optimal_duration_seconds: int  # Ideal video length
color_intensity: str      # Color saturation level
design_complexity: str    # simple/moderate/complex
```

#### `VariantPortfolio`
Container for managing campaign variants and performance.

**Constructor:**
```python
VariantPortfolio(
    campaign_id: str,
    campaign_name: str,
    brand_name: str,
    product_name: str,
    created_at: datetime = field(default_factory=datetime.now)
)
```

**Methods:**
```python
add_variant(variant_type: str, variant) -> None
    """Add variant to portfolio"""

calculate_metrics() -> Dict[str, Dict[str, float]]
    """Calculate CTR, conversion rate, CPC, CPA for each variant"""

recommend_variant() -> str
    """Get best performing variant"""

export_summary() -> Dict
    """Export portfolio data as dictionary"""
```

**Attributes:**
```python
impressions: Dict[str, int]     # Impressions per variant
clicks: Dict[str, int]          # Clicks per variant
conversions: Dict[str, int]     # Conversions per variant
spend: Dict[str, float]         # Spend per variant
```

#### `VariantStrategyFramework`
Strategic decision engine for variant recommendations.

**Static Methods:**
```python
get_variant_recommendations(
    campaign_type: str,        # awareness, consideration, conversion, loyalty
    target_audience: str,      # consumer, sme, enterprise, developer
    budget_constraint: str,    # limited, moderate, premium
    optimization_goal: str     # ctr, conversion, engagement, brand_lift
) -> Dict[str, str]
    """Returns budget allocation percentages for 5 variants"""
    # Example: {"abstract": "35%", "lifestyle": "30%", ...}

calculate_portfolio_lift(portfolio: VariantPortfolio) -> Dict
    """Calculate CTR and conversion lift vs control for each variant"""

generate_strategy_report(portfolio: VariantPortfolio) -> str
    """Generate comprehensive text-based performance report"""
```

#### `VariantSelector`
Intelligent variant selection based on audience context.

**Static Methods:**
```python
select_variant_for_audience(
    target_audience: str,      # consumer, enterprise, etc
    awareness_level: str,      # cold, warm, hot
    primary_goal: str          # awareness, consideration, conversion
) -> Tuple[str, str]
    """Returns (variant_type, reasoning)"""

get_variant_characteristics(variant_type: str) -> VariantCharacteristics
    """Get detailed characteristics of a variant"""

print_variant_guide() -> str
    """Print comprehensive variant selection guide"""
```

### Constants

#### `VARIANT_STRATEGY_LIBRARY`
```python
VARIANT_STRATEGY_LIBRARY = {
    "control": VariantCharacteristics(...),
    "lifestyle": VariantCharacteristics(...),
    "abstract": VariantCharacteristics(...),
    "high_contrast": VariantCharacteristics(...),
    "data_led": VariantCharacteristics(...)
}
```

---

## variant_testing.py

### Enums

#### `StatisticalSignificance`
```python
class StatisticalSignificance(Enum):
    NOT_SIGNIFICANT = "Not Significant (p > 0.10)"
    MARGINALLY_SIGNIFICANT = "Marginally Significant (0.05 < p ≤ 0.10)"
    SIGNIFICANT = "Significant (p ≤ 0.05)"
    HIGHLY_SIGNIFICANT = "Highly Significant (p ≤ 0.01)"
```

### Classes

#### `ABTestMetrics`
Results from A/B testing.

**Attributes:**
```python
variant_name: str
control_metric: float
variant_metric: float
samples: int
confidence_interval_95: Tuple[float, float]
p_value: float
statistical_significance: StatisticalSignificance
practical_significance_threshold: float
is_practically_significant: bool
mde: float  # Minimum Detectable Effect
recommendation: str
```

#### `ABTestFramework`
Statistical testing framework.

**Static Methods:**
```python
calculate_sample_size(
    baseline_conversion_rate: float,
    mde_percent: float,
    alpha: float = 0.05,
    beta: float = 0.20
) -> int
    """Calculate required sample size per variant
    
    Args:
        baseline_conversion_rate: e.g., 0.05 for 5%
        mde_percent: e.g., 5 for 5% lift to detect
        alpha: Type I error (0.05 = 95% confidence)
        beta: Type II error (0.20 = 80% power)
    
    Returns:
        Sample size needed per variant
    """

calculate_p_value(
    control_conversions: int,
    control_samples: int,
    variant_conversions: int,
    variant_samples: int
) -> float
    """Calculate p-value for two-sample proportion test"""

assess_statistical_significance(p_value: float) -> StatisticalSignificance
    """Convert p-value to significance level"""

run_test(
    variant_name: str,
    control_conversions: int,
    control_samples: int,
    variant_conversions: int,
    variant_samples: int,
    practical_significance_threshold: float = 0.05
) -> ABTestMetrics
    """Run complete A/B test with statistics and recommendation"""
```

#### `ExperimentArm`
Single arm of multi-variant experiment.

**Constructor:**
```python
ExperimentArm(
    variant_type: str,
    total_users: int,
    conversions: int,
    impressions: int,
    clicks: int,
    revenue: float = 0.0
)
```

**Methods:**
```python
get_metrics() -> Dict[str, float]
    """Returns conversion_rate, ctr, cpc, roas"""
```

#### `MultiVariantExperiment`
Framework for multi-armed experiments.

**Constructor:**
```python
MultiVariantExperiment(
    experiment_id: str,
    experiment_name: str,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    control_variant: str = "control",
    hypothesis: str = ""
)
```

**Methods:**
```python
add_arm(variant_type: str, arm: ExperimentArm) -> None
    """Add experimental arm"""

run_statistical_tests() -> Dict[str, ABTestMetrics]
    """Run A/B tests comparing all variants to control"""

rank_variants() -> List[Tuple[str, float]]
    """Rank variants by conversion rate (best to worst)"""

generate_report() -> str
    """Generate comprehensive experiment results report"""
```

#### `VariantLearning`
Learning insight from variant testing.

**Attributes:**
```python
variant_type: str
learning_date: datetime
key_insight: str
audience_segment: str
performance_lift: float  # e.g., 0.44 for 44%
recommendation: str
priority: str  # high, medium, low
```

#### `VariantLearningSystem`
System for capturing and analyzing learnings.

**Methods:**
```python
add_learning(learning: VariantLearning) -> None
    """Add a learning to the system"""

get_learnings_for_variant(variant_type: str) -> List[VariantLearning]
    """Get all learnings for a specific variant"""

get_top_insights(limit: int = 5) -> List[VariantLearning]
    """Get top performing insights"""

generate_insights_report() -> str
    """Generate insights report"""
```

---

## variant_integration.py

### Classes

#### `VariantPortfolioBuilder`
Builder pattern for portfolio creation.

**Constructor:**
```python
VariantPortfolioBuilder(
    campaign_id: str,
    campaign_name: str,
    brand_name: str,
    product_name: str
)
```

**Methods:**
```python
recommend_strategy(
    campaign_type: str,
    target_audience: str,
    budget_constraint: str,
    optimization_goal: str
) -> Dict[str, str]
    """Get strategic recommendations"""

build_with_recommendations(
    campaign_type: str,
    target_audience: str,
    budget_constraint: str,
    optimization_goal: str
) -> VariantPortfolio
    """Build portfolio and print recommendations"""

get_portfolio() -> VariantPortfolio
    """Get the built portfolio"""
```

#### `VariantSequencer`
Phased rollout planning and learning capture.

**Constructor:**
```python
VariantSequencer(portfolio: VariantPortfolio)
```

**Methods:**
```python
get_phased_rollout(
    total_budget: float,
    phases: int = 3
) -> Dict[str, Dict]
    """Get 3-phase rollout plan
    
    Returns dict with phase_1, phase_2, phase_3:
    {
        "duration_days": int,
        "budget": float,
        "variants": List[str],
        "status": str,
        "rationale": str
    }
    """

add_learning(
    variant_type: str,
    key_insight: str,
    audience_segment: str,
    performance_lift: float,
    recommendation: str,
    priority: str = "medium"
) -> None
    """Record a learning from testing"""

get_insights_report() -> str
    """Get comprehensive insights report"""
```

#### `VariantDashboardSnapshot`
Current state snapshot for dashboard.

**Attributes:**
```python
portfolio_id: str
timestamp: datetime
total_impressions: int
total_clicks: int
total_conversions: int
best_performing_variant: str
worst_performing_variant: str
average_ctr: float
average_conversion_rate: float
estimated_daily_spend: float
recommendations: List[str]
```

#### `VariantPerformanceDashboard`
Real-time performance monitoring.

**Constructor:**
```python
VariantPerformanceDashboard(portfolio: VariantPortfolio)
```

**Methods:**
```python
get_snapshot() -> VariantDashboardSnapshot
    """Get current dashboard snapshot"""

render_dashboard() -> str
    """Render text-based performance dashboard"""
```

#### `VariantOptimizationEngine`
Budget allocation optimization.

**Constructor:**
```python
VariantOptimizationEngine(portfolio: VariantPortfolio)
```

**Methods:**
```python
get_budget_optimization(total_budget: float) -> Dict[str, float]
    """Calculate optimal budget allocation
    
    Returns: {"control": 8525, "lifestyle": 9885, ...}
    """

get_variant_adjustments() -> Dict[str, str]
    """Get adjustment recommendations
    
    Returns recommendations like:
    - "🚀 SCALE UP - Strong performer"
    - "📈 MAINTAIN - Moderate performer"
    - "⚠️ MONITOR - Slight underperformance"
    - "📉 REDUCE - Significant underperformance"
    """
```

---

## Common Workflows

### 1. Build Portfolio with Recommendations

```python
from variant_integration import VariantPortfolioBuilder

builder = VariantPortfolioBuilder(
    campaign_id="CAMP-001",
    campaign_name="Q1 Campaign",
    brand_name="TechBrand",
    product_name="Product"
)

portfolio = builder.build_with_recommendations(
    campaign_type="awareness",
    target_audience="consumer",
    budget_constraint="moderate",
    optimization_goal="engagement"
)
```

### 2. Track Performance

```python
from variant_integration import VariantPerformanceDashboard

portfolio.impressions = {"control": 10000, "lifestyle": 10000, ...}
portfolio.clicks = {"control": 450, "lifestyle": 580, ...}
portfolio.conversions = {"control": 45, "lifestyle": 65, ...}

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
    variant_samples=10000
)

print(f"Lift: {(result.variant_metric - result.control_metric)*100:+.1%}")
print(f"Significance: {result.statistical_significance.value}")
print(f"Action: {result.recommendation}")
```

### 4. Plan Phased Rollout

```python
from variant_integration import VariantSequencer

sequencer = VariantSequencer(portfolio)
rollout = sequencer.get_phased_rollout(total_budget=100000)

for phase, details in rollout.items():
    print(f"{phase}: ${details['budget']:,.0f}")
```

### 5. Capture Learnings

```python
sequencer.add_learning(
    variant_type="lifestyle",
    key_insight="44% higher engagement with warm audiences",
    audience_segment="warm_awareness",
    performance_lift=0.44,
    recommendation="Prioritize for nurturing",
    priority="high"
)

print(sequencer.get_insights_report())
```

---

## Data Structures

### Recommendation Matrix
```python
recs = {
    "control": "5%",
    "lifestyle": "30%",
    "abstract": "35%",
    "high_contrast": "25%",
    "data_led": "5%"
}
```

### Metrics Dictionary
```python
metrics = {
    "control": {
        "ctr": 4.5,
        "conversion_rate": 10.0,
        "cpc": 0.15,
        "cpa": 1.5,
        "roas": 0.0
    },
    "lifestyle": {
        "ctr": 5.8,
        "conversion_rate": 11.21,
        ...
    }
}
```

### Phased Rollout Structure
```python
rollout = {
    "phase_1": {
        "duration_days": 7,
        "budget": 10000.0,
        "variants": ["control"],
        "status": "DEPLOY_NOW",
        "rationale": "Establish baseline..."
    },
    "phase_2": {
        "duration_days": 7,
        "budget": 30000.0,
        "variants": ["control", "lifestyle", "high_contrast"],
        "status": "MONITOR",
        "rationale": "Test high-engagement variants..."
    },
    "phase_3": {
        "duration_days": 14,
        "budget": 60000.0,
        "variants": ["control", "lifestyle", "abstract", "high_contrast", "data_led"],
        "status": "SCALE",
        "rationale": "Deploy full 5-variant strategy..."
    }
}
```

---

## Error Handling

All methods handle edge cases:
- Division by zero prevented (default 1.0 for rates)
- Empty portfolios managed
- Missing data fields handled gracefully
- Statistical calculations bounded (0.0 ≤ p_value ≤ 1.0)

---

## Performance Considerations

- Sample size calculator: O(1) complexity
- Metrics calculation: O(5) complexity (5 variants)
- P-value calculation: O(1) mathematical approximation
- Dashboard rendering: O(5) complexity (5 variants)
- Budget optimization: O(5) complexity

---

## Testing

All modules tested with:
- 15+ pre-configured recommendation scenarios
- Real-world conversion data
- Multi-variant experiments with 5 arms
- Complete workflow scenarios
- Edge case handling

Run tests:
```bash
python cmd/creative/variant_examples.py
```

---

## Version Information

- **Version:** 1.0
- **Release Date:** January 19, 2026
- **Python Version:** 3.8+
- **Dependencies:** None (standard library only)

---

## Support

For detailed documentation:
- Full guide: `docs/VARIANT_STRATEGY_SYSTEM.md`
- Quick reference: `docs/VARIANT_STRATEGY_QUICK_REFERENCE.md`
- Examples: `cmd/creative/variant_examples.py`
- Implementation: `docs/VARIANT_STRATEGY_IMPLEMENTATION.md`
