"""
5-Variant Strategy Integration
Integration layer connecting variant strategy system with SyncCreate engine
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from variant_strategy import (
    VariantPortfolio,
    VariantStrategyFramework,
    VariantSelector,
    VARIANT_STRATEGY_LIBRARY
)
from variant_testing import (
    ABTestFramework,
    MultiVariantExperiment,
    ExperimentArm,
    VariantLearningSystem,
    VariantLearning
)


# ============================================================================
# VARIANT PORTFOLIO BUILDER
# ============================================================================

class VariantPortfolioBuilder:
    """Builder for creating complete 5-variant portfolios."""
    
    def __init__(self, campaign_id: str, campaign_name: str, brand_name: str, product_name: str):
        self.portfolio = VariantPortfolio(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            brand_name=brand_name,
            product_name=product_name
        )
    
    def recommend_strategy(
        self,
        campaign_type: str,
        target_audience: str,
        budget_constraint: str,
        optimization_goal: str
    ) -> Dict[str, str]:
        """Get strategic recommendations for this portfolio."""
        return VariantStrategyFramework.get_variant_recommendations(
            campaign_type=campaign_type,
            target_audience=target_audience,
            budget_constraint=budget_constraint,
            optimization_goal=optimization_goal
        )
    
    def build_with_recommendations(
        self,
        campaign_type: str,
        target_audience: str,
        budget_constraint: str,
        optimization_goal: str
    ) -> 'VariantPortfolio':
        """Build portfolio with automated recommendations."""
        
        recs = self.recommend_strategy(
            campaign_type=campaign_type,
            target_audience=target_audience,
            budget_constraint=budget_constraint,
            optimization_goal=optimization_goal
        )
        
        print(f"\n📋 Strategy Recommendations for {self.portfolio.campaign_name}")
        print("="*80)
        print(f"Campaign Type: {campaign_type}")
        print(f"Target Audience: {target_audience}")
        print(f"Budget: {budget_constraint}")
        print(f"Goal: {optimization_goal}\n")
        
        print("Recommended Budget Allocation:")
        print("-"*80)
        
        for variant_type, allocation in recs.items():
            char = VARIANT_STRATEGY_LIBRARY.get(variant_type)
            print(f"  {char.name:20} {allocation:>8}  → {char.best_for[0]}")
        
        return self.portfolio
    
    def get_portfolio(self) -> VariantPortfolio:
        """Get the built portfolio."""
        return self.portfolio


# ============================================================================
# SMART VARIANT SEQUENCING
# ============================================================================

class VariantSequencer:
    """Intelligently sequence variant rollout based on learnings."""
    
    def __init__(self, portfolio: VariantPortfolio):
        self.portfolio = portfolio
        self.learning_system = VariantLearningSystem()
    
    def get_phased_rollout(self, total_budget: float, phases: int = 3) -> Dict[str, Dict]:
        """
        Get phased rollout plan with conservative deployment.
        
        Phase 1 (10%): Control + Winner from previous test
        Phase 2 (30%): Top 3 performers
        Phase 3 (60%): Full portfolio
        """
        
        budget_per_phase = [0.10, 0.30, 0.60]
        variant_names = list(self.portfolio.variants.keys())
        
        rollout_plan = {}
        
        # Phase 1: Conservative
        rollout_plan["phase_1"] = {
            "duration_days": 7,
            "budget": total_budget * budget_per_phase[0],
            "variants": ["control"],  # Start with just control
            "status": "DEPLOY_NOW",
            "rationale": "Establish baseline with control variant"
        }
        
        # Phase 2: Expand
        rollout_plan["phase_2"] = {
            "duration_days": 7,
            "budget": total_budget * budget_per_phase[1],
            "variants": ["control", "lifestyle", "high_contrast"],
            "status": "MONITOR",
            "rationale": "Test high-engagement variants (Lifestyle, High-Contrast)"
        }
        
        # Phase 3: Full portfolio
        rollout_plan["phase_3"] = {
            "duration_days": 14,
            "budget": total_budget * budget_per_phase[2],
            "variants": ["control", "lifestyle", "abstract", "high_contrast", "data_led"],
            "status": "SCALE",
            "rationale": "Deploy full 5-variant strategy with optimal distribution"
        }
        
        return rollout_plan
    
    def add_learning(
        self,
        variant_type: str,
        key_insight: str,
        audience_segment: str,
        performance_lift: float,
        recommendation: str,
        priority: str = "medium"
    ) -> None:
        """Record a learning from testing."""
        
        learning = VariantLearning(
            variant_type=variant_type,
            learning_date=datetime.now(),
            key_insight=key_insight,
            audience_segment=audience_segment,
            performance_lift=performance_lift,
            recommendation=recommendation,
            priority=priority
        )
        
        self.learning_system.add_learning(learning)
    
    def get_insights_report(self) -> str:
        """Get comprehensive insights report."""
        return self.learning_system.generate_insights_report()


# ============================================================================
# VARIANT PERFORMANCE DASHBOARD
# ============================================================================

@dataclass
class VariantDashboardSnapshot:
    """Current state snapshot for dashboard."""
    
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


class VariantPerformanceDashboard:
    """Real-time performance dashboard for variant portfolios."""
    
    def __init__(self, portfolio: VariantPortfolio):
        self.portfolio = portfolio
    
    def get_snapshot(self) -> VariantDashboardSnapshot:
        """Get current dashboard snapshot."""
        
        metrics = self.portfolio.calculate_metrics()
        
        # Find best and worst
        variant_scores = {}
        for vtype, metric in metrics.items():
            # Combined score: CTR (40%) + Conv Rate (60%)
            score = (metric["ctr"] * 0.4) + (metric["conversion_rate"] * 0.6)
            variant_scores[vtype] = score
        
        best = max(variant_scores, key=variant_scores.get) if variant_scores else "unknown"
        worst = min(variant_scores, key=variant_scores.get) if variant_scores else "unknown"
        
        # Calculate averages
        total_impr = sum(self.portfolio.impressions.values())
        total_clicks = sum(self.portfolio.clicks.values())
        total_convs = sum(self.portfolio.conversions.values())
        
        avg_ctr = (total_clicks / total_impr * 100) if total_impr > 0 else 0
        avg_conv = (total_convs / total_clicks * 100) if total_clicks > 0 else 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, best, worst)
        
        # Estimate daily spend
        total_spend = sum(self.portfolio.spend.values())
        days_active = max(1, (datetime.now() - self.portfolio.created_at).days)
        daily_spend = total_spend / days_active if days_active > 0 else 0
        
        return VariantDashboardSnapshot(
            portfolio_id=self.portfolio.campaign_id,
            timestamp=datetime.now(),
            total_impressions=total_impr,
            total_clicks=total_clicks,
            total_conversions=total_convs,
            best_performing_variant=best,
            worst_performing_variant=worst,
            average_ctr=avg_ctr,
            average_conversion_rate=avg_conv,
            estimated_daily_spend=daily_spend,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, metrics: Dict, best: str, worst: str) -> List[str]:
        """Generate action recommendations."""
        recommendations = []
        
        best_char = VARIANT_STRATEGY_LIBRARY.get(best)
        worst_char = VARIANT_STRATEGY_LIBRARY.get(worst)
        
        recommendations.append(f"🏆 {best_char.name} is performing best - consider increasing its budget allocation")
        
        if worst_char:
            worst_lift = metrics.get(worst, {}).get("ctr", 0)
            if worst_lift < 1.0:
                recommendations.append(f"📉 {worst_char.name} underperforming - test optimization or pause")
        
        recommendations.append("📊 Continue monitoring for statistical significance (7-14 days recommended)")
        recommendations.append("🎯 Use learnings to inform next campaign iteration")
        
        return recommendations
    
    def render_dashboard(self) -> str:
        """Render text-based dashboard."""
        
        snapshot = self.get_snapshot()
        metrics = self.portfolio.calculate_metrics()
        
        dashboard = f"""
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                          5-VARIANT PERFORMANCE DASHBOARD                                         ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝

Portfolio: {self.portfolio.campaign_name}
Campaign ID: {snapshot.portfolio_id}
Updated: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{'─'*100}
KEY METRICS
{'─'*100}

Total Impressions:     {snapshot.total_impressions:>12,}
Total Clicks:          {snapshot.total_clicks:>12,}
Total Conversions:     {snapshot.total_conversions:>12,}
Average CTR:           {snapshot.average_ctr:>12.2f}%
Average Conversion:    {snapshot.average_conversion_rate:>12.2f}%
Daily Spend:           ${snapshot.estimated_daily_spend:>11.2f}

{'─'*100}
VARIANT PERFORMANCE
{'─'*100}

{f'{'Variant':<20} {'Impressions':<15} {'CTR':<12} {'Conv Rate':<12} {'Status':<15}'}
{'-'*74}
"""
        
        for variant_type in ["control", "lifestyle", "abstract", "high_contrast", "data_led"]:
            char = VARIANT_STRATEGY_LIBRARY.get(variant_type)
            impr = self.portfolio.impressions.get(variant_type, 0)
            metric = metrics.get(variant_type, {})
            ctr = metric.get("ctr", 0)
            conv_rate = metric.get("conversion_rate", 0)
            
            # Determine status
            if variant_type == snapshot.best_performing_variant:
                status = "🏆 WINNING"
            elif variant_type == snapshot.worst_performing_variant:
                status = "📉 NEEDS WORK"
            else:
                status = "✅ ACTIVE"
            
            dashboard += f"{char.name:<20} {impr:<15} {ctr:<12.2f}% {conv_rate:<12.2f}% {status:<15}\n"
        
        dashboard += f"\n{'─'*100}\nRECOMMENDATIONS\n{'─'*100}\n\n"
        
        for i, rec in enumerate(snapshot.recommendations, 1):
            dashboard += f"{i}. {rec}\n"
        
        dashboard += f"\n{'═'*100}\n"
        
        return dashboard


# ============================================================================
# VARIANT OPTIMIZATION ENGINE
# ============================================================================

class VariantOptimizationEngine:
    """Engine for continuous optimization of variant performance."""
    
    def __init__(self, portfolio: VariantPortfolio):
        self.portfolio = portfolio
    
    def get_budget_optimization(self, total_budget: float) -> Dict[str, float]:
        """
        Calculate optimal budget distribution based on current performance.
        Uses proportional allocation: higher performing variants get more budget.
        """
        
        metrics = self.portfolio.calculate_metrics()
        
        # Calculate performance scores (weighted CTR + Conv Rate)
        scores = {}
        for variant_type, metric in metrics.items():
            score = (metric["ctr"] * 0.4) + (metric["conversion_rate"] * 0.6)
            scores[variant_type] = max(0.1, score)  # Minimum score of 0.1
        
        # Normalize scores
        total_score = sum(scores.values())
        
        allocation = {}
        for variant_type, score in scores.items():
            allocation[variant_type] = total_budget * (score / total_score)
        
        return allocation
    
    def get_variant_adjustments(self) -> Dict[str, str]:
        """Get recommended adjustments for each variant."""
        
        metrics = self.portfolio.calculate_metrics()
        adjustments = {}
        
        control_conv = metrics.get("control", {}).get("conversion_rate", 1)
        
        for variant_type, metric in metrics.items():
            if variant_type != "control":
                lift = (metric["conversion_rate"] - control_conv) / control_conv if control_conv > 0 else 0
                
                if lift > 0.20:
                    adjustments[variant_type] = "🚀 SCALE UP - Strong performer, increase budget"
                elif lift > 0.05:
                    adjustments[variant_type] = "📈 MAINTAIN - Moderate performer, hold budget"
                elif lift > -0.10:
                    adjustments[variant_type] = "⚠️ MONITOR - Slight underperformance, watch closely"
                else:
                    adjustments[variant_type] = "📉 REDUCE - Significant underperformance, consider pausing"
        
        return adjustments


# ============================================================================
# COMPLETE VARIANT STRATEGY WORKFLOW
# ============================================================================

def demo_complete_workflow():
    """Demonstrate complete 5-variant strategy workflow."""
    
    print("\n" + "="*100)
    print("COMPLETE 5-VARIANT STRATEGY WORKFLOW DEMONSTRATION")
    print("="*100 + "\n")
    
    # Step 1: Build Portfolio
    print("STEP 1: Building Portfolio")
    print("-"*100)
    
    builder = VariantPortfolioBuilder(
        campaign_id="CAMPAIGN-001",
        campaign_name="Q1 2026 Awareness Campaign",
        brand_name="TechBrand",
        product_name="AI Assistant Pro"
    )
    
    portfolio = builder.build_with_recommendations(
        campaign_type="awareness",
        target_audience="consumer",
        budget_constraint="moderate",
        optimization_goal="engagement"
    )
    
    # Step 2: Get Sequencer
    print("\n\nSTEP 2: Phased Rollout Plan")
    print("-"*100)
    
    sequencer = VariantSequencer(portfolio)
    rollout = sequencer.get_phased_rollout(total_budget=50000)
    
    for phase, details in rollout.items():
        print(f"\n{phase.upper()}")
        print(f"  Duration: {details['duration_days']} days")
        print(f"  Budget: ${details['budget']:,.0f}")
        print(f"  Variants: {', '.join(details['variants'])}")
        print(f"  Status: {details['status']}")
        print(f"  Rationale: {details['rationale']}")
    
    # Step 3: Simulate Performance Data
    print("\n\nSTEP 3: Simulating Performance Data")
    print("-"*100)
    
    portfolio.impressions = {
        "control": 10000,
        "lifestyle": 10000,
        "abstract": 9500,
        "high_contrast": 11000,
        "data_led": 8500
    }
    
    portfolio.clicks = {
        "control": 450,
        "lifestyle": 580,
        "abstract": 475,
        "high_contrast": 620,
        "data_led": 350
    }
    
    portfolio.conversions = {
        "control": 45,
        "lifestyle": 65,
        "abstract": 50,
        "high_contrast": 75,
        "data_led": 55
    }
    
    print("Performance data loaded into portfolio")
    
    # Step 4: Dashboard
    print("\n\nSTEP 4: Performance Dashboard")
    print("-"*100)
    
    dashboard = VariantPerformanceDashboard(portfolio)
    print(dashboard.render_dashboard())
    
    # Step 5: Optimization
    print("\nSTEP 5: Budget Optimization")
    print("-"*100)
    
    optimizer = VariantOptimizationEngine(portfolio)
    optimized_budget = optimizer.get_budget_optimization(total_budget=50000)
    
    print("\nOptimized Budget Allocation:")
    for variant_type, budget in optimized_budget.items():
        char = VARIANT_STRATEGY_LIBRARY.get(variant_type)
        print(f"  {char.name:20} ${budget:>10,.0f}  ({budget/50000*100:>5.1f}%)")
    
    print("\nVariant Adjustment Recommendations:")
    adjustments = optimizer.get_variant_adjustments()
    for variant_type, recommendation in adjustments.items():
        print(f"  {variant_type:20} {recommendation}")
    
    # Step 6: Learning System
    print("\n\nSTEP 6: Recording Learnings")
    print("-"*100)
    
    sequencer.add_learning(
        variant_type="lifestyle",
        key_insight="Lifestyle variant drives 44% higher engagement with warm audiences",
        audience_segment="warm_awareness",
        performance_lift=0.44,
        recommendation="Prioritize lifestyle content for audience nurturing sequences",
        priority="high"
    )
    
    sequencer.add_learning(
        variant_type="high_contrast",
        key_insight="High-contrast design optimal for mobile feed scrolling",
        audience_segment="cold_awareness",
        performance_lift=0.38,
        recommendation="Use high-contrast primarily for TikTok and Instagram Reels",
        priority="high"
    )
    
    print("\n" + sequencer.get_insights_report())


if __name__ == "__main__":
    demo_complete_workflow()
