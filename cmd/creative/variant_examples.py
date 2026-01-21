"""
5-Variant Strategy System - Comprehensive Examples & Test Suite
Demonstrates all major features and workflows
"""

from datetime import datetime, timedelta
from variant_strategy import (
    VariantStrategyFramework,
    VariantSelector,
    VariantPortfolio,
    VARIANT_STRATEGY_LIBRARY
)
from variant_testing import (
    ABTestFramework,
    MultiVariantExperiment,
    ExperimentArm,
    VariantLearningSystem,
    VariantLearning
)
from variant_integration import (
    VariantPortfolioBuilder,
    VariantSequencer,
    VariantPerformanceDashboard,
    VariantOptimizationEngine
)


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*100}")
    print(f"  {title}")
    print(f"{'='*100}\n")


# ============================================================================
# EXAMPLE 1: Strategic Recommendations
# ============================================================================

def example_strategic_recommendations():
    """Example: Get variant recommendations by campaign type."""
    print_section("EXAMPLE 1: Strategic Recommendations by Campaign Type")
    
    campaign_scenarios = [
        {
            "name": "E-Commerce Holiday Season",
            "campaign_type": "awareness",
            "target_audience": "consumer",
            "budget_constraint": "premium",
            "optimization_goal": "engagement"
        },
        {
            "name": "B2B SaaS - Enterprise Sales",
            "campaign_type": "consideration",
            "target_audience": "enterprise",
            "budget_constraint": "premium",
            "optimization_goal": "conversion"
        },
        {
            "name": "App Launch - Startup",
            "campaign_type": "awareness",
            "target_audience": "consumer",
            "budget_constraint": "limited",
            "optimization_goal": "ctr"
        },
        {
            "name": "Developer Tools - Q1",
            "campaign_type": "consideration",
            "target_audience": "developer",
            "budget_constraint": "moderate",
            "optimization_goal": "conversion"
        }
    ]
    
    for scenario in campaign_scenarios:
        print(f"📊 {scenario['name']}")
        print(f"   Type: {scenario['campaign_type']} | Audience: {scenario['target_audience']}")
        print(f"   Budget: {scenario['budget_constraint']} | Goal: {scenario['optimization_goal']}\n")
        
        recs = VariantStrategyFramework.get_variant_recommendations(
            campaign_type=scenario['campaign_type'],
            target_audience=scenario['target_audience'],
            budget_constraint=scenario['budget_constraint'],
            optimization_goal=scenario['optimization_goal']
        )
        
        for variant_type, allocation in recs.items():
            char = VARIANT_STRATEGY_LIBRARY[variant_type]
            print(f"   • {char.name:20} {allocation:>5}  ← {char.best_for[0]}")
        print()


# ============================================================================
# EXAMPLE 2: Variant Selection by Audience State
# ============================================================================

def example_variant_selection():
    """Example: Select variants based on audience awareness."""
    print_section("EXAMPLE 2: Intelligent Variant Selection by Audience")
    
    scenarios = [
        ("cold", "awareness", "Need to grab attention"),
        ("cold", "conversion", "First-time conversion needed"),
        ("warm", "awareness", "Deepen relationship"),
        ("warm", "conversion", "Support decision-making"),
        ("hot", "conversion", "Close the sale"),
    ]
    
    for awareness, goal, context in scenarios:
        variant, reasoning = VariantSelector.select_variant_for_audience(
            target_audience="consumer",
            awareness_level=awareness,
            primary_goal=goal
        )
        
        char = VARIANT_STRATEGY_LIBRARY[variant]
        print(f"👤 {awareness.upper()} Audience → {goal.upper()} Goal")
        print(f"   Recommendation: {char.name}")
        print(f"   Reasoning: {reasoning}")
        print(f"   Why: {char.description}\n")


# ============================================================================
# EXAMPLE 3: Statistical Testing
# ============================================================================

def example_statistical_testing():
    """Example: Run A/B tests with statistical significance."""
    print_section("EXAMPLE 3: A/B Testing with Statistical Significance")
    
    # Different test scenarios
    test_scenarios = [
        {
            "name": "Strong Winner",
            "control_conv": 450,
            "control_samples": 10000,
            "variant_conv": 620,
            "variant_samples": 10000,
            "description": "37.8% conversion lift"
        },
        {
            "name": "Moderate Improvement",
            "control_conv": 450,
            "control_samples": 10000,
            "variant_conv": 520,
            "variant_samples": 10000,
            "description": "15.6% conversion lift"
        },
        {
            "name": "Inconclusive Results",
            "control_conv": 450,
            "control_samples": 10000,
            "variant_conv": 465,
            "variant_samples": 10000,
            "description": "3.3% conversion lift"
        },
        {
            "name": "Clear Underperformer",
            "control_conv": 450,
            "control_samples": 10000,
            "variant_conv": 350,
            "variant_samples": 10000,
            "description": "-22.2% conversion lift"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"🧪 {scenario['name']}: {scenario['description']}")
        
        result = ABTestFramework.run_test(
            variant_name=scenario['name'],
            control_conversions=scenario['control_conv'],
            control_samples=scenario['control_samples'],
            variant_conversions=scenario['variant_conv'],
            variant_samples=scenario['variant_samples']
        )
        
        lift = (result.variant_metric - result.control_metric) * 100
        print(f"   Lift: {lift:+.1f}%")
        print(f"   Statistical Significance: {result.statistical_significance.value}")
        print(f"   P-Value: {result.p_value:.4f}")
        print(f"   Recommendation: {result.recommendation}\n")


# ============================================================================
# EXAMPLE 4: Multi-Variant Experiment
# ============================================================================

def example_multi_variant_experiment():
    """Example: Run complete multi-variant experiment."""
    print_section("EXAMPLE 4: Multi-Variant Experiment Analysis")
    
    experiment = MultiVariantExperiment(
        experiment_id="EXP-Q1-2026",
        experiment_name="Q1 2026 Awareness Campaign",
        start_date=datetime.now() - timedelta(days=14),
        end_date=datetime.now(),
        hypothesis="Lifestyle and High-Contrast variants will outperform control"
    )
    
    # Add experimental arms with realistic data
    variants_data = {
        "control": (10000, 450, 50000, 2500),
        "lifestyle": (10000, 580, 50000, 3100),
        "abstract": (9500, 475, 48000, 2400),
        "high_contrast": (11000, 620, 55000, 3500),
        "data_led": (8500, 350, 45000, 2000)
    }
    
    for variant_type, (users, conversions, impressions, clicks) in variants_data.items():
        experiment.add_arm(variant_type, ExperimentArm(
            variant_type=variant_type,
            total_users=users,
            conversions=conversions,
            impressions=impressions,
            clicks=clicks
        ))
    
    # Analyze
    print(experiment.generate_report())
    
    # Show ranking
    print("\n🏆 VARIANT RANKING (Best to Worst)\n")
    ranking = experiment.rank_variants()
    for rank, (variant, rate) in enumerate(ranking, 1):
        print(f"{rank}. {variant.upper():20} {rate:.2%} conversion rate")


# ============================================================================
# EXAMPLE 5: Portfolio Management
# ============================================================================

def example_portfolio_management():
    """Example: Build, track, and optimize portfolio."""
    print_section("EXAMPLE 5: Portfolio Building & Management")
    
    # Build portfolio
    print("📋 Building Portfolio with Recommendations\n")
    
    builder = VariantPortfolioBuilder(
        campaign_id="CAMP-Q1-AWARE",
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
    
    # Simulate performance data
    print("\n📊 Simulating Performance Data\n")
    
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
    
    portfolio.spend = {
        "control": 1200,
        "lifestyle": 1500,
        "abstract": 1400,
        "high_contrast": 1800,
        "data_led": 1600
    }
    
    # Show dashboard
    dashboard = VariantPerformanceDashboard(portfolio)
    print(dashboard.render_dashboard())
    
    # Show optimization
    print("\n💰 Budget Optimization Recommendations\n")
    
    optimizer = VariantOptimizationEngine(portfolio)
    optimized = optimizer.get_budget_optimization(total_budget=50000)
    
    print(f"{'Variant':<20} {'Current':<12} {'Optimized':<12} {'Change':<12}")
    print("-"*56)
    
    current_total = sum(portfolio.spend.values())
    for variant_type, optimized_budget in optimized.items():
        current = (portfolio.spend.get(variant_type, 0) / current_total * 50000) if current_total > 0 else 0
        change = optimized_budget - current
        print(f"{variant_type:<20} ${current:<11,.0f} ${optimized_budget:<11,.0f} {change:+,.0f}")
    
    # Adjustments
    print("\n📈 Variant Adjustments\n")
    
    adjustments = optimizer.get_variant_adjustments()
    for variant, adjustment in adjustments.items():
        print(f"  {variant:20} {adjustment}")


# ============================================================================
# EXAMPLE 6: Phased Rollout Planning
# ============================================================================

def example_phased_rollout():
    """Example: Plan phased rollout with conservative deployment."""
    print_section("EXAMPLE 6: Phased Rollout Planning")
    
    portfolio = VariantPortfolio(
        campaign_id="CAMP-001",
        campaign_name="Q1 Campaign",
        brand_name="TechBrand",
        product_name="Product"
    )
    
    sequencer = VariantSequencer(portfolio)
    rollout = sequencer.get_phased_rollout(total_budget=100000, phases=3)
    
    print("📅 Conservative Phased Deployment\n")
    
    cumulative_budget = 0
    for phase_name in ["phase_1", "phase_2", "phase_3"]:
        phase = rollout[phase_name]
        cumulative_budget += phase["budget"]
        
        print(f"\n{phase_name.upper()}")
        print(f"  Duration: {phase['duration_days']} days")
        print(f"  Budget: ${phase['budget']:,.0f} (${cumulative_budget:,.0f} cumulative)")
        print(f"  Variants: {', '.join(phase['variants'])}")
        print(f"  Status: {phase['status']}")
        print(f"  Rationale: {phase['rationale']}")
        print(f"  Risk Level: {'LOW' if phase_name == 'phase_1' else 'MEDIUM' if phase_name == 'phase_2' else 'HIGH'}")


# ============================================================================
# EXAMPLE 7: Learning System
# ============================================================================

def example_learning_system():
    """Example: Capture and analyze learnings from experiments."""
    print_section("EXAMPLE 7: Learning System & Insights")
    
    learning_system = VariantLearningSystem()
    
    # Add learnings
    learnings = [
        {
            "variant": "lifestyle",
            "insight": "Lifestyle drives 44% higher engagement with warm audiences",
            "audience": "warm_awareness",
            "lift": 0.44,
            "rec": "Prioritize lifestyle content for nurturing sequences",
            "priority": "high"
        },
        {
            "variant": "high_contrast",
            "insight": "Bold design optimal for mobile feed scrolling",
            "audience": "cold_awareness",
            "lift": 0.38,
            "rec": "Use high-contrast primarily for TikTok and Instagram Reels",
            "priority": "high"
        },
        {
            "variant": "data_led",
            "insight": "Data visualization reduces decision friction for B2B",
            "audience": "hot_consideration",
            "lift": 0.28,
            "rec": "Feature data-led creative in enterprise sales sequences",
            "priority": "high"
        },
        {
            "variant": "abstract",
            "insight": "Abstract creative drives 2.5x shares vs control",
            "audience": "warm_awareness",
            "lift": 0.25,
            "rec": "Use abstract for viral/organic reach campaigns",
            "priority": "medium"
        }
    ]
    
    for learning_data in learnings:
        learning_system.add_learning(VariantLearning(
            variant_type=learning_data["variant"],
            learning_date=datetime.now(),
            key_insight=learning_data["insight"],
            audience_segment=learning_data["audience"],
            performance_lift=learning_data["lift"],
            recommendation=learning_data["rec"],
            priority=learning_data["priority"]
        ))
    
    # Show report
    print(learning_system.generate_insights_report())


# ============================================================================
# EXAMPLE 8: Complete Campaign Workflow
# ============================================================================

def example_complete_workflow():
    """Example: End-to-end campaign from planning to optimization."""
    print_section("EXAMPLE 8: Complete Campaign Workflow")
    
    print("STEP 1: Define Campaign Parameters\n")
    
    campaign_params = {
        "name": "Summer Product Launch",
        "type": "awareness",
        "audience": "consumer",
        "budget": 75000,
        "duration_days": 28
    }
    
    print(f"  Campaign: {campaign_params['name']}")
    print(f"  Type: {campaign_params['type']}")
    print(f"  Audience: {campaign_params['audience']}")
    print(f"  Budget: ${campaign_params['budget']:,.0f}")
    print(f"  Duration: {campaign_params['duration_days']} days")
    
    print("\n" + "-"*100)
    print("STEP 2: Build Portfolio with Strategic Recommendations\n")
    
    builder = VariantPortfolioBuilder(
        campaign_id="CAMP-SUMMER",
        campaign_name=campaign_params['name'],
        brand_name="TechBrand",
        product_name="New Product"
    )
    
    portfolio = builder.build_with_recommendations(
        campaign_type=campaign_params['type'],
        target_audience=campaign_params['audience'],
        budget_constraint="premium",
        optimization_goal="engagement"
    )
    
    print("-"*100)
    print("STEP 3: Plan Phased Deployment\n")
    
    sequencer = VariantSequencer(portfolio)
    rollout = sequencer.get_phased_rollout(total_budget=campaign_params['budget'])
    
    for phase_name, phase_data in rollout.items():
        print(f"  {phase_name}: ${phase_data['budget']:>8,.0f} - {phase_data['variants']}")
    
    print("\n" + "-"*100)
    print("STEP 4: Week 1 Performance (Phase 1 Complete)\n")
    
    # Simulate Phase 1 results
    portfolio.impressions = {"control": 25000, "lifestyle": 0, "abstract": 0, "high_contrast": 0, "data_led": 0}
    portfolio.clicks = {"control": 1500, "lifestyle": 0, "abstract": 0, "high_contrast": 0, "data_led": 0}
    portfolio.conversions = {"control": 150, "lifestyle": 0, "abstract": 0, "high_contrast": 0, "data_led": 0}
    
    metrics = portfolio.calculate_metrics()
    print(f"  Control CTR: {metrics['control']['ctr']:.2f}%")
    print(f"  Control Conv Rate: {metrics['control']['conversion_rate']:.2f}%")
    print(f"  Baseline established ✓")
    
    print("\n" + "-"*100)
    print("STEP 5: Week 2-3 Performance (Phase 2 In Progress)\n")
    
    # Simulate Phase 2 results
    portfolio.impressions = {
        "control": 30000,
        "lifestyle": 28000,
        "abstract": 0,
        "high_contrast": 32000,
        "data_led": 0
    }
    portfolio.clicks = {
        "control": 1800,
        "lifestyle": 2100,
        "abstract": 0,
        "high_contrast": 2400,
        "data_led": 0
    }
    portfolio.conversions = {
        "control": 180,
        "lifestyle": 260,
        "abstract": 0,
        "high_contrast": 300,
        "data_led": 0
    }
    
    dashboard = VariantPerformanceDashboard(portfolio)
    snapshot = dashboard.get_snapshot()
    
    print(f"  Best Performer: {snapshot.best_performing_variant}")
    print(f"  Total Conversions: {snapshot.total_conversions}")
    print(f"  Average CTR: {snapshot.average_ctr:.2f}%")
    
    print("\n" + "-"*100)
    print("STEP 6: Budget Optimization for Phase 3\n")
    
    optimizer = VariantOptimizationEngine(portfolio)
    optimized = optimizer.get_budget_optimization(total_budget=campaign_params['budget'])
    
    print("  Recommended Phase 3 Budget Allocation:")
    for variant, budget in optimized.items():
        pct = budget / campaign_params['budget'] * 100
        char = VARIANT_STRATEGY_LIBRARY.get(variant)
        print(f"    {char.name:20} ${budget:>10,.0f} ({pct:>5.1f}%)")
    
    print("\n" + "-"*100)
    print("STEP 7: Record Learning & Plan Next Campaign\n")
    
    sequencer.add_learning(
        variant_type="high_contrast",
        key_insight="High-contrast 67% better CTR than control in mobile feeds",
        audience_segment="cold_awareness",
        performance_lift=0.67,
        recommendation="Make high-contrast primary for mobile-first audiences",
        priority="high"
    )
    
    print("  ✓ Learning recorded: High-Contrast performance insight")
    print("  ✓ Playbook updated for future awareness campaigns")
    print("  ✓ Ready for full Phase 3 rollout")


# ============================================================================
# MAIN - Run All Examples
# ============================================================================

if __name__ == "__main__":
    print("\n" + "█"*100)
    print("█" + " "*98 + "█")
    print("█" + " "*20 + "5-VARIANT STRATEGY SYSTEM - COMPREHENSIVE EXAMPLES".center(58) + " "*20 + "█")
    print("█" + " "*98 + "█")
    print("█"*100)
    
    # Run all examples
    example_strategic_recommendations()
    example_variant_selection()
    example_statistical_testing()
    example_multi_variant_experiment()
    example_portfolio_management()
    example_phased_rollout()
    example_learning_system()
    example_complete_workflow()
    
    print("\n" + "="*100)
    print("✅ All examples completed successfully!")
    print("="*100 + "\n")
