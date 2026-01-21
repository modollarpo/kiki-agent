"""
5-Variant Strategy System
Complete framework for managing, analyzing, and optimizing creative variants
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import json
from pathlib import Path

# ============================================================================
# VARIANT CHARACTERISTICS & METADATA
# ============================================================================

@dataclass
class VariantCharacteristics:
    """Core characteristics of each variant type."""
    
    name: str
    description: str
    visual_focus: str
    messaging_style: str
    best_for: List[str]  # Use cases
    platform_fit: List[str]  # Best platforms
    ctr_lift_potential: float  # Expected CTR improvement vs control
    conversion_lift: float  # Expected conversion improvement
    engagement_lift: float  # Expected engagement improvement
    average_cpv: str  # Cost per view expectation
    optimal_duration_seconds: Optional[int]  # For video
    color_intensity: str  # visual intensity level
    design_complexity: str  # simple, moderate, complex
    

VARIANT_STRATEGY_LIBRARY = {
    "control": VariantCharacteristics(
        name="Control",
        description="Product-focused baseline for performance benchmarking",
        visual_focus="Product hero shot, clean presentation, professional setting",
        messaging_style="Direct, clear value proposition, USP-focused",
        best_for=["Baseline benchmarking", "New products", "Direct response", "Professional audiences"],
        platform_fit=["Meta", "LinkedIn", "Google", "YouTube"],
        ctr_lift_potential=1.0,  # Baseline
        conversion_lift=1.0,  # Baseline
        engagement_lift=1.0,  # Baseline
        average_cpv="$0.08-0.12",
        optimal_duration_seconds=6,
        color_intensity="moderate",
        design_complexity="simple"
    ),
    
    "lifestyle": VariantCharacteristics(
        name="Lifestyle",
        description="Emotional connection through real-world usage scenarios",
        visual_focus="Person using product, authentic moments, natural environments",
        messaging_style="Narrative-driven, benefit-focused, aspirational",
        best_for=["Brand building", "Lifestyle products", "Emotional resonance", "Consumer engagement"],
        platform_fit=["TikTok", "Instagram", "Pinterest", "YouTube Shorts"],
        ctr_lift_potential=1.15,  # 15% improvement
        conversion_lift=1.25,  # 25% improvement
        engagement_lift=1.35,  # 35% improvement
        average_cpv="$0.06-0.10",
        optimal_duration_seconds=15,
        color_intensity="warm",
        design_complexity="moderate"
    ),
    
    "abstract": VariantCharacteristics(
        name="Abstract",
        description="Conceptual visualization of emotions, motivations, and aspirations",
        visual_focus="Abstract concept art, metaphorical imagery, emotional themes",
        messaging_style="Inspirational, motivational, pain-point-focused",
        best_for=["Awareness campaigns", "Emotional branding", "Innovation messaging", "High-level concepts"],
        platform_fit=["LinkedIn", "YouTube", "Instagram", "Twitter/X"],
        ctr_lift_potential=0.95,  # Slightly lower CTR
        conversion_lift=1.18,  # 18% improvement (strong for aware audience)
        engagement_lift=1.42,  # 42% engagement lift (shares, reactions)
        average_cpv="$0.05-0.09",
        optimal_duration_seconds=20,
        color_intensity="high",
        design_complexity="complex"
    ),
    
    "high_contrast": VariantCharacteristics(
        name="High-Contrast",
        description="Bold, scroll-stopping design with maximum visual impact",
        visual_focus="Vibrant colors, striking composition, eye-catching elements",
        messaging_style="Urgent, action-oriented, FOMO-driven",
        best_for=["Feed optimization", "Mobile scrolling", "Quick captures", "Lower-funnel conversion"],
        platform_fit=["TikTok", "Meta", "Instagram", "Snapchat"],
        ctr_lift_potential=1.28,  # 28% improvement
        conversion_lift=1.32,  # 32% improvement
        engagement_lift=1.25,  # 25% engagement
        average_cpv="$0.07-0.11",
        optimal_duration_seconds=8,
        color_intensity="very_high",
        design_complexity="moderate"
    ),
    
    "data_led": VariantCharacteristics(
        name="Data-Led",
        description="Proof-driven creative highlighting USP, metrics, and social proof",
        visual_focus="Infographic style, data visualization, proof elements",
        messaging_style="Evidence-based, trust-building, ROI-focused",
        best_for=["B2B marketing", "Enterprise sales", "Performance marketing", "Trust building"],
        platform_fit=["LinkedIn", "Google Ads", "YouTube", "Industry publications"],
        ctr_lift_potential=0.92,  # Lower CTR (not as eye-catching)
        conversion_lift=1.38,  # 38% improvement (highest conversion for aware)
        engagement_lift=0.88,  # Lower engagement (less shareable)
        average_cpv="$0.12-0.18",
        optimal_duration_seconds=12,
        color_intensity="low",
        design_complexity="complex"
    )
}


# ============================================================================
# VARIANT PORTFOLIO & STRATEGY
# ============================================================================

@dataclass
class CreativeVariant:
    """Individual creative variant with metadata and assets."""
    
    variant_type: str  # control, lifestyle, abstract, high_contrast, data_led
    variant_id: str
    characteristics: VariantCharacteristics
    asset_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_mb: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "draft"  # draft, active, paused, archived
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class VariantPortfolio:
    """A portfolio of 5 variants for a specific campaign."""
    
    campaign_id: str
    campaign_name: str
    brand_name: str
    product_name: str
    created_at: datetime = field(default_factory=datetime.now)
    variants: Dict[str, 'CreativeVariant'] = field(default_factory=dict)
    
    # Performance tracking
    impressions: Dict[str, int] = field(default_factory=lambda: {
        "control": 0, "lifestyle": 0, "abstract": 0, "high_contrast": 0, "data_led": 0
    })
    clicks: Dict[str, int] = field(default_factory=lambda: {
        "control": 0, "lifestyle": 0, "abstract": 0, "high_contrast": 0, "data_led": 0
    })
    conversions: Dict[str, int] = field(default_factory=lambda: {
        "control": 0, "lifestyle": 0, "abstract": 0, "high_contrast": 0, "data_led": 0
    })
    spend: Dict[str, float] = field(default_factory=lambda: {
        "control": 0.0, "lifestyle": 0.0, "abstract": 0.0, "high_contrast": 0.0, "data_led": 0.0
    })
    
    def add_variant(self, variant_type: str, variant: 'CreativeVariant') -> None:
        """Add variant to portfolio."""
        self.variants[variant_type] = variant
    
    def calculate_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics for each variant."""
        metrics = {}
        
        for variant_type in ["control", "lifestyle", "abstract", "high_contrast", "data_led"]:
            impr = self.impressions.get(variant_type, 1)  # Avoid division by zero
            clicks = self.clicks.get(variant_type, 0)
            convs = self.conversions.get(variant_type, 0)
            spend = self.spend.get(variant_type, 0.01)
            
            metrics[variant_type] = {
                "ctr": (clicks / impr * 100) if impr > 0 else 0.0,
                "conversion_rate": (convs / clicks * 100) if clicks > 0 else 0.0,
                "cpc": (spend / clicks) if clicks > 0 else 0.0,
                "cpa": (spend / convs) if convs > 0 else 0.0,
                "roas": 0.0,  # To be calculated with revenue data
            }
        
        return metrics
    
    def recommend_variant(self) -> str:
        """Recommend best performing variant based on current metrics."""
        metrics = self.calculate_metrics()
        
        # Score variants on CTR + Conversion Rate
        scores = {}
        for variant_type, metric in metrics.items():
            ctr = metric["ctr"]
            conv_rate = metric["conversion_rate"]
            # Weighted score: 40% CTR, 60% conversion
            scores[variant_type] = (ctr * 0.4) + (conv_rate * 0.6)
        
        return max(scores, key=scores.get)
    
    def export_summary(self) -> Dict:
        """Export portfolio summary for reporting."""
        metrics = self.calculate_metrics()
        
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "brand": self.brand_name,
            "product": self.product_name,
            "created_at": self.created_at.isoformat(),
            "variants": {
                vtype: {
                    "headline": v.headline_text,
                    "platform": v.platform_format.value if hasattr(v, 'platform_format') else "unknown",
                    "impressions": self.impressions.get(vtype, 0),
                    "clicks": self.clicks.get(vtype, 0),
                    "conversions": self.conversions.get(vtype, 0),
                    "metrics": metrics.get(vtype, {})
                }
                for vtype, v in self.variants.items()
            }
        }


# ============================================================================
# STRATEGY FRAMEWORK
# ============================================================================

class VariantStrategyFramework:
    """Framework for building and managing 5-variant strategies."""
    
    @staticmethod
    def get_variant_recommendations(
        campaign_type: str,
        target_audience: str,
        budget_constraint: str,
        optimization_goal: str
    ) -> Dict[str, str]:
        """
        Get variant recommendations based on campaign parameters.
        
        Args:
            campaign_type: awareness, consideration, conversion, loyalty
            target_audience: enterprise, sme, consumer, developer
            budget_constraint: limited, moderate, premium
            optimization_goal: ctr, conversion, engagement, brand_lift
            
        Returns:
            Dictionary mapping variant types to investment allocation percentages
        """
        
        recommendations = {
            # Awareness campaigns
            ("awareness", "consumer", "moderate", "engagement"): {
                "abstract": "35%",
                "lifestyle": "30%",
                "high_contrast": "25%",
                "data_led": "5%",
                "control": "5%"
            },
            
            # Enterprise B2B consideration
            ("consideration", "enterprise", "premium", "conversion"): {
                "data_led": "40%",
                "control": "30%",
                "abstract": "15%",
                "lifestyle": "10%",
                "high_contrast": "5%"
            },
            
            # Lower-funnel conversion
            ("conversion", "consumer", "moderate", "conversion"): {
                "high_contrast": "35%",
                "lifestyle": "30%",
                "control": "20%",
                "data_led": "10%",
                "abstract": "5%"
            },
            
            # SME product launch
            ("awareness", "sme", "limited", "ctr"): {
                "high_contrast": "30%",
                "lifestyle": "25%",
                "control": "20%",
                "abstract": "15%",
                "data_led": "10%"
            },
            
            # Developer/technical audience
            ("consideration", "developer", "moderate", "conversion"): {
                "data_led": "50%",
                "abstract": "25%",
                "control": "15%",
                "lifestyle": "5%",
                "high_contrast": "5%"
            }
        }
        
        key = (campaign_type, target_audience, budget_constraint, optimization_goal)
        return recommendations.get(
            key,
            {  # Default balanced approach
                "control": "20%",
                "lifestyle": "20%",
                "abstract": "20%",
                "high_contrast": "20%",
                "data_led": "20%"
            }
        )
    
    @staticmethod
    def calculate_portfolio_lift(portfolio: VariantPortfolio) -> Dict:
        """Calculate overall portfolio lift vs control."""
        metrics = portfolio.calculate_metrics()
        control_metrics = metrics.get("control", {})
        
        lift_analysis = {}
        for variant_type, metric in metrics.items():
            if variant_type == "control":
                lift_analysis[variant_type] = {
                    "ctr_lift": "0%",
                    "conv_lift": "0%",
                    "avg_lift": "0%"
                }
            else:
                ctr_control = control_metrics.get("ctr", 1)
                conv_control = control_metrics.get("conversion_rate", 1)
                
                ctr_lift = ((metric["ctr"] - ctr_control) / ctr_control * 100) if ctr_control > 0 else 0
                conv_lift = ((metric["conversion_rate"] - conv_control) / conv_control * 100) if conv_control > 0 else 0
                avg_lift = (ctr_lift + conv_lift) / 2
                
                lift_analysis[variant_type] = {
                    "ctr_lift": f"{ctr_lift:+.1f}%",
                    "conv_lift": f"{conv_lift:+.1f}%",
                    "avg_lift": f"{avg_lift:+.1f}%"
                }
        
        return lift_analysis
    
    @staticmethod
    def generate_strategy_report(portfolio: VariantPortfolio) -> str:
        """Generate a comprehensive strategy report."""
        metrics = portfolio.calculate_metrics()
        lift = VariantStrategyFramework.calculate_portfolio_lift(portfolio)
        
        report = f"""
{'='*100}
5-VARIANT STRATEGY PERFORMANCE REPORT
{'='*100}

Campaign: {portfolio.campaign_name}
Brand: {portfolio.brand_name}
Product: {portfolio.product_name}
Created: {portfolio.created_at.strftime('%Y-%m-%d %H:%M:%S')}

{'─'*100}
VARIANT PERFORMANCE COMPARISON
{'─'*100}

{f'{'Variant':<20} {'Impressions':<15} {'Clicks':<15} {'CTR':<12} {'Conversions':<15} {'Conv Rate':<12}'}
{'-'*89}
"""
        
        for variant_type in ["control", "lifestyle", "abstract", "high_contrast", "data_led"]:
            char = VARIANT_STRATEGY_LIBRARY.get(variant_type)
            impr = portfolio.impressions.get(variant_type, 0)
            clicks = portfolio.clicks.get(variant_type, 0)
            convs = portfolio.conversions.get(variant_type, 0)
            metric = metrics.get(variant_type, {})
            
            report += f"{char.name:<20} {impr:<15} {clicks:<15} {metric.get('ctr', 0):.2f}%    {convs:<15} {metric.get('conversion_rate', 0):.2f}%\n"
        
        report += f"\n{'─'*100}\nVARIANT LIFT vs CONTROL\n{'─'*100}\n\n"
        
        for variant_type, lift_data in lift.items():
            if variant_type != "control":
                char = VARIANT_STRATEGY_LIBRARY.get(variant_type)
                report += f"{char.name:20} | CTR Lift: {lift_data['ctr_lift']:>8} | Conv Lift: {lift_data['conv_lift']:>8} | Avg Lift: {lift_data['avg_lift']:>8}\n"
        
        report += f"\n{'─'*100}\nRECOMMENDATIONS\n{'─'*100}\n\n"
        
        best_variant = portfolio.recommend_variant()
        best_char = VARIANT_STRATEGY_LIBRARY.get(best_variant)
        
        report += f"🏆 Best Performer: {best_char.name}\n"
        report += f"   • Recommended for: {', '.join(best_char.best_for[:2])}\n"
        report += f"   • Best platforms: {', '.join(best_char.platform_fit[:2])}\n"
        
        report += f"\n{'='*100}\n"
        
        return report


# ============================================================================
# VARIANT SELECTOR & OPTIMIZER
# ============================================================================

class VariantSelector:
    """Intelligent variant selection based on context."""
    
    @staticmethod
    def select_variant_for_audience(
        target_audience: str,
        awareness_level: str,  # cold, warm, hot
        primary_goal: str  # awareness, consideration, conversion
    ) -> Tuple[str, str]:
        """
        Select best variant for specific audience + context.
        
        Returns: (variant_type, reasoning)
        """
        
        selection_matrix = {
            # Cold awareness campaigns
            ("cold", "awareness"): ("high_contrast", "Needs immediate attention capture"),
            ("cold", "consideration"): ("abstract", "Build emotional connection first"),
            ("cold", "conversion"): ("high_contrast", "Maximum visual impact"),
            
            # Warm audience (aware of brand)
            ("warm", "awareness"): ("lifestyle", "Deepen brand relationship"),
            ("warm", "consideration"): ("data_led", "Support decision making"),
            ("warm", "conversion"): ("lifestyle", "Personal connection drives action"),
            
            # Hot audience (decision stage)
            ("hot", "awareness"): ("control", "Direct product focus"),
            ("hot", "consideration"): ("data_led", "Prove ROI and value"),
            ("hot", "conversion"): ("data_led", "Close with proof"),
        }
        
        key = (awareness_level, primary_goal)
        variant, reasoning = selection_matrix.get(
            key,
            ("control", "Balanced approach for unknown context")
        )
        
        return variant, reasoning
    
    @staticmethod
    def get_variant_characteristics(variant_type: str) -> VariantCharacteristics:
        """Get detailed characteristics of a variant."""
        return VARIANT_STRATEGY_LIBRARY.get(variant_type)
    
    @staticmethod
    def print_variant_guide() -> str:
        """Print comprehensive variant selection guide."""
        guide = """
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                         5-VARIANT STRATEGY SELECTION GUIDE                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝

"""
        
        for vtype, char in VARIANT_STRATEGY_LIBRARY.items():
            guide += f"""
┌─ {char.name.upper()} ─────────────────────────────────────────────────────────────────────────────┐
│
│ Description: {char.description}
│
│ Visual Focus:  {char.visual_focus}
│ Messaging:     {char.messaging_style}
│
│ Best For:  {', '.join(char.best_for)}
│ Platforms: {', '.join(char.platform_fit)}
│
│ Performance Lift (vs Control):
│   • CTR:        {char.ctr_lift_potential:.0%}
│   • Conversion: {char.conversion_lift:.0%}
│   • Engagement: {char.engagement_lift:.0%}
│   • Est. CPV:   {char.average_cpv}
│
│ Design Profile:
│   • Color Intensity: {char.color_intensity}
│   • Complexity:      {char.design_complexity}
│   • Video Duration:  {char.optimal_duration_seconds}s optimal
│
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
        
        return guide


def get_strategic_recommendations(
    campaign_type: str,
    target_audience: str,
    platform: str
) -> List[Tuple[str, float, str]]:
    """
    Get strategic variant recommendations for a campaign.
    
    Returns:
        List of tuples: (variant_type, score, reasoning)
    """
    recommendations = []
    
    # Score each variant based on campaign requirements
    for variant_key, characteristics in VARIANT_STRATEGY_LIBRARY.items():
        score = 0.5  # Base score
        reasoning_parts = []
        
        # Platform fit
        if platform.lower() in [p.lower() for p in characteristics.platform_fit]:
            score += 0.2
            reasoning_parts.append(f"Strong {platform} fit")
        
        # Campaign type alignment
        campaign_keywords = {
            "awareness": ["awareness", "brand", "engagement"],
            "consideration": ["consideration", "education", "lifestyle"],
            "conversion": ["conversion", "direct response", "data"],
            "retention": ["retention", "loyalty", "relationship"]
        }
        
        if campaign_type.lower() in campaign_keywords:
            for keyword in campaign_keywords[campaign_type.lower()]:
                if any(keyword in use_case.lower() for use_case in characteristics.best_for):
                    score += 0.15
                    reasoning_parts.append(f"Aligned with {campaign_type}")
                    break
        
        # Audience fit
        audience_keywords = {
            "tech": ["professional", "b2b", "tech"],
            "consumer": ["consumer", "lifestyle", "general"],
            "professional": ["professional", "b2b", "corporate"],
            "creative": ["creative", "artistic", "visual"]
        }
        
        if target_audience.lower() in audience_keywords:
            for keyword in audience_keywords[target_audience.lower()]:
                if any(keyword in use_case.lower() for use_case in characteristics.best_for):
                    score += 0.1
                    reasoning_parts.append(f"Fits {target_audience} audience")
                    break
        
        # Add performance metrics
        if characteristics.ctr_lift_potential > 1.1:
            score += 0.05
            reasoning_parts.append("High CTR potential")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Standard recommendation"
        recommendations.append((variant_key, min(score, 1.0), reasoning))
    
    # Sort by score descending
    recommendations.sort(key=lambda x: x[1], reverse=True)
    
    return recommendations


if __name__ == "__main__":
    # Demo the system
    print(VariantSelector.print_variant_guide())
    
    # Example: Get recommendations
    print("\n" + "="*100)
    print("EXAMPLE: Campaign Strategy Recommendations")
    print("="*100 + "\n")
    
    recs = VariantStrategyFramework.get_variant_recommendations(
        campaign_type="awareness",
        target_audience="consumer",
        budget_constraint="moderate",
        optimization_goal="engagement"
    )
    
    print("Recommended budget allocation for consumer awareness campaign:")
    for variant, allocation in recs.items():
        char = VARIANT_STRATEGY_LIBRARY[variant]
        print(f"  {char.name:20} {allocation:>8}  → {char.best_for[0]}")
