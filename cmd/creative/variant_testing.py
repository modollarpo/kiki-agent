"""
5-Variant A/B Testing Framework
Statistical testing and experiment management for variant strategies
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math
from datetime import datetime, timedelta

# ============================================================================
# STATISTICAL TESTING
# ============================================================================

class StatisticalSignificance(Enum):
    """Levels of statistical significance."""
    NOT_SIGNIFICANT = "Not Significant (p > 0.10)"
    MARGINALLY_SIGNIFICANT = "Marginally Significant (0.05 < p ≤ 0.10)"
    SIGNIFICANT = "Significant (p ≤ 0.05)"
    HIGHLY_SIGNIFICANT = "Highly Significant (p ≤ 0.01)"


@dataclass
class ABTestMetrics:
    """Metrics for A/B test results."""
    
    variant_name: str
    control_metric: float
    variant_metric: float
    samples: int
    confidence_interval_95: Tuple[float, float]  # (lower, upper)
    p_value: float
    statistical_significance: StatisticalSignificance
    practical_significance_threshold: float  # e.g., 0.05 for 5% lift
    is_practically_significant: bool
    mde: float  # Minimum Detectable Effect
    recommendation: str


class ABTestFramework:
    """A/B testing framework for variant comparison."""
    
    @staticmethod
    def calculate_sample_size(
        baseline_conversion_rate: float,
        mde_percent: float,  # Minimum Detectable Effect (e.g., 5 for 5% lift)
        alpha: float = 0.05,  # Type I error
        beta: float = 0.20  # Type II error (1 - power)
    ) -> int:
        """
        Calculate sample size needed for A/B test.
        
        Args:
            baseline_conversion_rate: Current conversion rate (0-1)
            mde_percent: Desired minimum detectable effect in percentage
            alpha: Significance level (default 0.05 for 95% confidence)
            beta: Type II error rate (default 0.20 for 80% power)
        
        Returns:
            Sample size needed per variant
        """
        
        # Simplified formula for two-proportions test
        baseline = baseline_conversion_rate
        variant = baseline_conversion_rate * (1 + mde_percent / 100)
        
        z_alpha = 1.96  # For alpha = 0.05 (two-tailed)
        z_beta = 0.84   # For beta = 0.20 (80% power)
        
        p_avg = (baseline + variant) / 2
        
        numerator = ((z_alpha + z_beta) ** 2) * (2 * p_avg * (1 - p_avg))
        denominator = (variant - baseline) ** 2
        
        return int(math.ceil(numerator / denominator))
    
    @staticmethod
    def calculate_p_value(
        control_conversions: int,
        control_samples: int,
        variant_conversions: int,
        variant_samples: int
    ) -> float:
        """
        Calculate p-value for two-sample proportion test.
        Simplified Chi-square approximation.
        """
        
        if control_samples == 0 or variant_samples == 0:
            return 1.0
        
        control_rate = control_conversions / control_samples
        variant_rate = variant_conversions / variant_samples
        
        pooled_rate = (control_conversions + variant_conversions) / (control_samples + variant_samples)
        se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/control_samples + 1/variant_samples))
        
        if se == 0:
            return 1.0
        
        z_score = (variant_rate - control_rate) / se
        
        # Approximate p-value using normal distribution
        # For two-tailed test
        from math import erf
        p_value = 1 - erf(abs(z_score) / math.sqrt(2)) / 2
        
        return min(p_value, 1.0)
    
    @staticmethod
    def assess_statistical_significance(p_value: float) -> StatisticalSignificance:
        """Assess statistical significance level."""
        if p_value <= 0.01:
            return StatisticalSignificance.HIGHLY_SIGNIFICANT
        elif p_value <= 0.05:
            return StatisticalSignificance.SIGNIFICANT
        elif p_value <= 0.10:
            return StatisticalSignificance.MARGINALLY_SIGNIFICANT
        else:
            return StatisticalSignificance.NOT_SIGNIFICANT
    
    @staticmethod
    def run_test(
        variant_name: str,
        control_conversions: int,
        control_samples: int,
        variant_conversions: int,
        variant_samples: int,
        practical_significance_threshold: float = 0.05  # 5% lift
    ) -> ABTestMetrics:
        """
        Run A/B test and return results.
        
        Args:
            variant_name: Name of the variant
            control_conversions: Number of conversions in control
            control_samples: Total samples in control
            variant_conversions: Number of conversions in variant
            variant_samples: Total samples in variant
            practical_significance_threshold: Minimum lift to consider practically significant
        
        Returns:
            ABTestMetrics object with results and recommendation
        """
        
        control_rate = control_conversions / control_samples if control_samples > 0 else 0
        variant_rate = variant_conversions / variant_samples if variant_samples > 0 else 0
        
        lift = (variant_rate - control_rate) / control_rate if control_rate > 0 else 0
        
        # Calculate p-value
        p_value = ABTestFramework.calculate_p_value(
            control_conversions,
            control_samples,
            variant_conversions,
            variant_samples
        )
        
        # Assess significance
        sig_level = ABTestFramework.assess_statistical_significance(p_value)
        
        # Calculate MDE (Minimum Detectable Effect)
        mde_percent = (practical_significance_threshold / control_rate * 100) if control_rate > 0 else 0
        
        # Confidence interval for variant (95% CI)
        se = math.sqrt(variant_rate * (1 - variant_rate) / variant_samples) if variant_samples > 0 else 0
        ci_lower = variant_rate - 1.96 * se
        ci_upper = variant_rate + 1.96 * se
        
        # Practical significance
        is_practically_sig = abs(lift) >= practical_significance_threshold
        
        # Generate recommendation
        if sig_level == StatisticalSignificance.HIGHLY_SIGNIFICANT and is_practically_sig and lift > 0:
            if lift > 0.10:
                recommendation = f"🚀 STRONG WINNER: {lift:.1%} lift. Scale immediately."
            else:
                recommendation = f"✅ WINNER: {lift:.1%} lift. Proceed with deployment."
        elif sig_level in [StatisticalSignificance.SIGNIFICANT, StatisticalSignificance.MARGINALLY_SIGNIFICANT]:
            if lift > 0:
                recommendation = f"⚠️ PROMISING: {lift:.1%} lift detected. Continue testing or deploy with caution."
            else:
                recommendation = f"📉 UNDERPERFORMING: {lift:.1%} change. Consider pausing."
        else:
            recommendation = f"❌ INCONCLUSIVE: {lift:.1%} change detected. Need more samples ({ABTestFramework.calculate_sample_size(control_rate, practical_significance_threshold * 100)} per variant recommended)."
        
        return ABTestMetrics(
            variant_name=variant_name,
            control_metric=control_rate,
            variant_metric=variant_rate,
            samples=variant_samples,
            confidence_interval_95=(ci_lower, ci_upper),
            p_value=p_value,
            statistical_significance=sig_level,
            practical_significance_threshold=practical_significance_threshold,
            is_practically_significant=is_practically_sig,
            mde=mde_percent,
            recommendation=recommendation
        )


# ============================================================================
# MULTI-VARIANT EXPERIMENT FRAMEWORK
# ============================================================================

@dataclass
class ExperimentArm:
    """Single arm of a multi-variant experiment."""
    
    variant_type: str
    total_users: int
    conversions: int
    impressions: int
    clicks: int
    revenue: float = 0.0
    
    def get_metrics(self) -> Dict[str, float]:
        """Calculate metrics for this arm."""
        return {
            "conversion_rate": (self.conversions / self.total_users * 100) if self.total_users > 0 else 0,
            "ctr": (self.clicks / self.impressions * 100) if self.impressions > 0 else 0,
            "cpc": (self.revenue / self.clicks) if self.clicks > 0 else 0,
            "roas": self.revenue,  # Simplified - actual ROAS requires spend data
        }


@dataclass
class MultiVariantExperiment:
    """Framework for multi-variant experiments with 5+ arms."""
    
    experiment_id: str
    experiment_name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    arms: Dict[str, ExperimentArm] = field(default_factory=dict)
    control_variant: str = "control"
    hypothesis: str = ""
    
    def add_arm(self, variant_type: str, arm: ExperimentArm) -> None:
        """Add experimental arm."""
        self.arms[variant_type] = arm
    
    def run_statistical_tests(self) -> Dict[str, ABTestMetrics]:
        """Run A/B tests comparing all variants to control."""
        
        if self.control_variant not in self.arms:
            return {}
        
        control_arm = self.arms[self.control_variant]
        results = {}
        
        for variant_type, arm in self.arms.items():
            if variant_type != self.control_variant:
                test_result = ABTestFramework.run_test(
                    variant_name=variant_type,
                    control_conversions=control_arm.conversions,
                    control_samples=control_arm.total_users,
                    variant_conversions=arm.conversions,
                    variant_samples=arm.total_users
                )
                results[variant_type] = test_result
        
        return results
    
    def rank_variants(self) -> List[Tuple[str, float]]:
        """Rank variants by conversion rate (best to worst)."""
        ranking = []
        
        for variant_type, arm in self.arms.items():
            conv_rate = arm.conversions / arm.total_users if arm.total_users > 0 else 0
            ranking.append((variant_type, conv_rate))
        
        return sorted(ranking, key=lambda x: x[1], reverse=True)
    
    def generate_report(self) -> str:
        """Generate comprehensive experiment report."""
        
        test_results = self.run_statistical_tests()
        ranking = self.rank_variants()
        
        report = f"""
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                    MULTI-VARIANT EXPERIMENT RESULTS REPORT                                       ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝

Experiment:    {self.experiment_name} ({self.experiment_id})
Started:       {self.start_date.strftime('%Y-%m-%d %H:%M:%S')}
{f'Ended:         {self.end_date.strftime("%Y-%m-%d %H:%M:%S")}' if self.end_date else 'Status:        IN PROGRESS'}

Hypothesis:    {self.hypothesis}

{'─'*100}
VARIANT PERFORMANCE RANKING
{'─'*100}

"""
        
        for rank, (variant_type, conv_rate) in enumerate(ranking, 1):
            arm = self.arms[variant_type]
            metrics = arm.get_metrics()
            
            report += f"{rank}. {variant_type.upper():<20}"
            report += f"  Conversions: {arm.conversions:>5}  "
            report += f"Conv Rate: {conv_rate*100:>6.2f}%  "
            report += f"CTR: {metrics['ctr']:>6.2f}%  "
            report += f"Users: {arm.total_users:>7}\n"
        
        if test_results:
            report += f"\n{'─'*100}\nSTATISTICAL TEST RESULTS (vs {self.control_variant.upper()})\n{'─'*100}\n\n"
            
            for variant_type, result in test_results.items():
                report += f"{variant_type.upper()}\n"
                report += f"  Conversion Lift:        {(result.variant_metric - result.control_metric)*100:+.2f}%\n"
                report += f"  P-Value:                {result.p_value:.4f}\n"
                report += f"  Statistical Signif.:   {result.statistical_significance.value}\n"
                report += f"  Practical Signif.:      {'YES' if result.is_practically_significant else 'NO'}\n"
                report += f"  Recommendation:        {result.recommendation}\n\n"
        
        report += f"{'═'*100}\n"
        
        return report


# ============================================================================
# LEARNING & FEEDBACK SYSTEM
# ============================================================================

@dataclass
class VariantLearning:
    """Learning insights from variant performance."""
    
    variant_type: str
    learning_date: datetime
    key_insight: str
    audience_segment: str  # e.g., "cold_awareness", "warm_conversion"
    performance_lift: float  # e.g., 0.15 for 15%
    recommendation: str
    priority: str  # high, medium, low


class VariantLearningSystem:
    """System for capturing and applying learnings from variant testing."""
    
    def __init__(self):
        self.learnings: List[VariantLearning] = []
    
    def add_learning(self, learning: VariantLearning) -> None:
        """Add a learning to the system."""
        self.learnings.append(learning)
    
    def get_learnings_for_variant(self, variant_type: str) -> List[VariantLearning]:
        """Get all learnings for a specific variant."""
        return [l for l in self.learnings if l.variant_type == variant_type]
    
    def get_top_insights(self, limit: int = 5) -> List[VariantLearning]:
        """Get top performing insights."""
        return sorted(
            self.learnings,
            key=lambda x: x.performance_lift,
            reverse=True
        )[:limit]
    
    def generate_insights_report(self) -> str:
        """Generate insights report."""
        
        report = """
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                         VARIANT LEARNING INSIGHTS REPORT                                         ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝

"""
        
        top_insights = self.get_top_insights(10)
        
        for rank, insight in enumerate(top_insights, 1):
            report += f"""
{rank}. {insight.variant_type.upper()} → {insight.performance_lift:+.1%} lift
   Audience: {insight.audience_segment}
   Insight: {insight.key_insight}
   Action: {insight.recommendation}
   Priority: {insight.priority.upper()}
   Discovered: {insight.learning_date.strftime('%Y-%m-%d')}
"""
        
        return report


if __name__ == "__main__":
    # Demo: Calculate sample size
    print("Sample Size Calculator Demo")
    print("="*80)
    
    sample_size = ABTestFramework.calculate_sample_size(
        baseline_conversion_rate=0.05,  # 5% baseline
        mde_percent=5  # Want to detect 5% lift
    )
    print(f"For 5% baseline conversion, to detect 5% lift with 95% confidence and 80% power:")
    print(f"Sample size needed: {sample_size:,} users per variant\n")
    
    # Demo: Run an experiment
    print("\nMulti-Variant Experiment Demo")
    print("="*80 + "\n")
    
    experiment = MultiVariantExperiment(
        experiment_id="EXP-001",
        experiment_name="Brand Awareness Campaign - Jan 2026",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        hypothesis="Abstract variant will have higher engagement for cold audience"
    )
    
    # Add arms
    experiment.add_arm("control", ExperimentArm(
        variant_type="control",
        total_users=10000,
        conversions=450,
        impressions=50000,
        clicks=2500,
        revenue=1200
    ))
    
    experiment.add_arm("lifestyle", ExperimentArm(
        variant_type="lifestyle",
        total_users=10000,
        conversions=580,  # 28.9% lift
        impressions=50000,
        clicks=3100,
        revenue=1600
    ))
    
    experiment.add_arm("abstract", ExperimentArm(
        variant_type="abstract",
        total_users=10000,
        conversions=520,  # 15.6% lift
        impressions=48000,
        clicks=2400,
        revenue=1300
    ))
    
    experiment.add_arm("high_contrast", ExperimentArm(
        variant_type="high_contrast",
        total_users=10000,
        conversions=620,  # 37.8% lift
        impressions=55000,
        clicks=3500,
        revenue=1800
    ))
    
    experiment.add_arm("data_led", ExperimentArm(
        variant_type="data_led",
        total_users=10000,
        conversions=490,  # 8.9% lift
        impressions=45000,
        clicks=2000,
        revenue=1100
    ))
    
    print(experiment.generate_report())


# ============================================================================
# CONVENIENCE FUNCTIONS FOR API
# ============================================================================

def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    alpha: float = 0.05,
    beta: float = 0.20
) -> int:
    """Wrapper for ABTestFramework.calculate_sample_size for API usage."""
    return ABTestFramework.calculate_sample_size(
        baseline_conversion_rate=baseline_rate,
        mde_percent=minimum_detectable_effect,
        alpha=alpha,
        beta=beta
    )


def analyze_multi_variant_experiment(arms_data: Dict[str, Dict]) -> MultiVariantExperiment:
    """
    Create and analyze a multi-variant experiment from dictionary data.
    
    Args:
        arms_data: Dict mapping variant names to arm data dicts with keys:
            - total_users, conversions, impressions, clicks, revenue
    
    Returns:
        MultiVariantExperiment instance with all arms added
    """
    experiment = MultiVariantExperiment()
    
    for variant_type, data in arms_data.items():
        arm = ExperimentArm(
            variant_type=variant_type,
            total_users=data.get('total_users', 0),
            conversions=data.get('conversions', 0),
            impressions=data.get('impressions', 0),
            clicks=data.get('clicks', 0),
            revenue=data.get('revenue', 0.0)
        )
        experiment.add_arm(variant_type, arm)
    
    return experiment
