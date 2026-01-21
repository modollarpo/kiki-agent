"""
Vision Guard Integration with 5-Variant Strategy System

Integrates CLIP-based vision validation with variant portfolio management
and performance tracking.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from cmd.creative.vision_guard import VisionGuardWithVariantOptimization, CLIPValidationResult
from cmd.creative.variant_strategy import VariantPortfolio, VARIANT_STRATEGY_LIBRARY


# ============================================================================
# VISION VALIDATION FOR PORTFOLIO
# ============================================================================

@dataclass
class VariantImageQuality:
    """Quality metrics for variant image."""
    
    variant_type: str
    image_path: str
    product_confidence: float
    safety_score: float
    quality_score: float
    brand_fit: float
    composition: float
    overall_score: float
    is_approved: bool
    variant_requirements_met: bool
    validation_date: datetime = field(default_factory=datetime.now)
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    variant_checks: Dict = field(default_factory=dict)


class VariantImageValidator:
    """Validates all images in a portfolio using vision guard."""
    
    def __init__(self, use_mock: bool = True):
        self.vision_guard = VisionGuardWithVariantOptimization(use_mock=use_mock)
        self.validation_cache: Dict[str, VariantImageQuality] = {}
    
    def validate_portfolio_images(
        self,
        portfolio: VariantPortfolio,
        image_paths: Dict[str, str],  # variant_type -> image_path
        brand_guidelines: Optional[Dict] = None
    ) -> Dict[str, VariantImageQuality]:
        """
        Validate all images in portfolio.
        
        Args:
            portfolio: VariantPortfolio instance
            image_paths: Mapping of variant types to image file paths
            brand_guidelines: Brand safety guidelines
        
        Returns:
            Dict mapping variant types to VariantImageQuality
        """
        
        results = {}
        
        for variant_type, image_path in image_paths.items():
            if not Path(image_path).exists():
                print(f"Warning: Image not found for {variant_type}: {image_path}")
                continue
            
            quality = self.validate_variant_image(
                image_path=image_path,
                variant_type=variant_type,
                product_name=portfolio.product_name,
                brand_guidelines=brand_guidelines
            )
            
            results[variant_type] = quality
        
        return results
    
    def validate_variant_image(
        self,
        image_path: str,
        variant_type: str,
        product_name: str,
        brand_guidelines: Optional[Dict] = None
    ) -> VariantImageQuality:
        """
        Validate single variant image.
        
        Returns:
            VariantImageQuality with detailed validation
        """
        
        # Check cache
        cache_key = f"{image_path}:{variant_type}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
        
        # Run validation
        validation = self.vision_guard.validate_variant(
            image_path=image_path,
            product_name=product_name,
            variant_type=variant_type,
            brand_guidelines=brand_guidelines or {}
        )
        
        # Extract results
        base = validation['base_validation']
        violations = validation['safety_flags']
        
        # Check variant requirements
        variant_reqs = validation['variant_checks']
        all_passed = all(
            check.get('passed', check.get('status') == '✅')
            for check in variant_reqs.values()
        )
        
        quality = VariantImageQuality(
            variant_type=variant_type,
            image_path=image_path,
            product_confidence=base['product_confidence'],
            safety_score=base['safety_score'],
            quality_score=base['quality_score'],
            brand_fit=validation.get('brand_fit_score', 0.8),
            composition=validation.get('composition_score', 0.85),
            overall_score=base['overall_score'],
            is_approved=base['is_approved'] and all_passed,
            violations=violations,
            warnings=[],
            recommendations=validation['recommendations'],
            variant_requirements_met=all_passed,
            variant_checks=variant_reqs
        )
        
        # Cache
        self.validation_cache[cache_key] = quality
        
        return quality


# ============================================================================
# QUALITY-BASED PORTFOLIO RANKING
# ============================================================================

class QualityBasedRanking:
    """Rank variants by vision quality scores."""
    
    @staticmethod
    def rank_by_quality(
        quality_results: Dict[str, VariantImageQuality]
    ) -> List[tuple]:
        """
        Rank variants by overall quality score.
        
        Returns:
            List of (variant_type, quality) tuples sorted by quality (best first)
        """
        
        ranking = []
        for variant_type, quality in quality_results.items():
            ranking.append((
                variant_type,
                quality.overall_score,
                quality
            ))
        
        return sorted(ranking, key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def get_quality_tier(score: float) -> str:
        """Classify quality score into tier."""
        
        if score >= 0.90:
            return "🏆 PRODUCTION READY"
        elif score >= 0.80:
            return "✅ APPROVED"
        elif score >= 0.70:
            return "⚠️ NEEDS REVISION"
        else:
            return "❌ REJECTED"
    
    @staticmethod
    def generate_quality_report(
        quality_results: Dict[str, VariantImageQuality]
    ) -> str:
        """Generate comprehensive quality report."""
        
        report = """
╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                             VARIANT IMAGE QUALITY REPORT                                          ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════╝

"""
        
        # Rank variants
        ranking = QualityBasedRanking.rank_by_quality(quality_results)
        
        report += f"{'Variant':<20} {'Overall':<10} {'Product':<10} {'Safety':<10} {'Quality':<10} {'Brand':<10} {'Status':<25}\n"
        report += "-"*95 + "\n"
        
        for variant_type, overall_score, quality in ranking:
            tier = QualityBasedRanking.get_quality_tier(overall_score)
            
            report += (
                f"{variant_type:<20} "
                f"{overall_score:>8.1%}  "
                f"{quality.product_confidence:>8.1%}  "
                f"{quality.safety_score:>8.1%}  "
                f"{quality.quality_score:>8.1%}  "
                f"{quality.brand_fit:>8.1%}  "
                f"{tier:<25}\n"
            )
        
        report += "\n" + "-"*95 + "\n\n"
        
        # Detailed findings
        report += "DETAILED FINDINGS\n\n"
        
        for variant_type, overall_score, quality in ranking:
            char = VARIANT_STRATEGY_LIBRARY.get(variant_type)
            report += f"\n{char.name.upper()}\n"
            report += f"  Overall Score: {overall_score:.1%}\n"
            report += f"  Product Detection: {quality.product_confidence:.1%}\n"
            report += f"  Safety Score: {quality.safety_score:.1%}\n"
            report += f"  Quality Score: {quality.quality_score:.1%}\n"
            report += f"  Brand Fit: {quality.brand_fit:.1%}\n"
            report += f"  Composition: {quality.composition:.1%}\n"
            report += f"  Variant Requirements: {'✅ MET' if quality.variant_requirements_met else '❌ NOT MET'}\n"
            
            if quality.violations:
                report += f"  Violations:\n"
                for v in quality.violations:
                    report += f"    • {v}\n"
            
            if quality.recommendations:
                report += f"  Recommendations:\n"
                for r in quality.recommendations[:3]:
                    report += f"    • {r}\n"
        
        report += f"\n{'='*95}\n"
        
        return report


# ============================================================================
# VISION-BASED PORTFOLIO OPTIMIZATION
# ============================================================================

class VisionBasedOptimizer:
    """Optimize portfolio based on vision quality validation."""
    
    def __init__(self, validator: VariantImageValidator):
        self.validator = validator
    
    def get_deployment_recommendations(
        self,
        quality_results: Dict[str, VariantImageQuality]
    ) -> Dict[str, str]:
        """
        Get deployment recommendations based on quality.
        
        Returns:
            Dict mapping variant_type to recommendation
        """
        
        recommendations = {}
        
        for variant_type, quality in quality_results.items():
            if quality.overall_score >= 0.90:
                recommendations[variant_type] = (
                    "🚀 DEPLOY - Production ready, full budget allocation"
                )
            elif quality.overall_score >= 0.80:
                recommendations[variant_type] = (
                    "✅ DEPLOY - Approved, standard allocation"
                )
            elif quality.overall_score >= 0.70:
                recommendations[variant_type] = (
                    "⚠️ CONDITIONAL - Address recommendations, reduced allocation"
                )
            else:
                recommendations[variant_type] = (
                    "❌ HOLD - Revise image, requires revalidation"
                )
        
        return recommendations
    
    def get_budget_adjustment(
        self,
        quality_results: Dict[str, VariantImageQuality],
        total_budget: float
    ) -> Dict[str, float]:
        """
        Adjust budget allocation based on quality scores.
        
        Higher quality images get more budget.
        """
        
        # Calculate scores
        scores = {}
        for variant_type, quality in quality_results.items():
            scores[variant_type] = quality.overall_score
        
        # Normalize
        total_score = sum(scores.values())
        if total_score == 0:
            return {vt: total_budget / len(scores) for vt in scores}
        
        # Allocate budget proportionally
        allocation = {}
        for variant_type, score in scores.items():
            allocation[variant_type] = total_budget * (score / total_score)
        
        return allocation
    
    def get_reoptimization_path(
        self,
        quality_results: Dict[str, VariantImageQuality]
    ) -> Dict[str, List[str]]:
        """
        Get specific steps to improve each variant.
        
        Returns:
            Dict with improvement steps for each variant
        """
        
        paths = {}
        
        for variant_type, quality in quality_results.items():
            steps = []
            
            # Product confidence
            if quality.product_confidence < 0.7:
                steps.append("Increase product prominence/visibility in frame")
            
            # Safety
            if quality.safety_score < 0.8:
                steps.append("Review and address safety concerns")
                for violation in quality.violations:
                    steps.append(f"  - Fix: {violation}")
            
            # Quality
            if quality.quality_score < 0.75:
                steps.append("Improve image technical quality (sharpness, exposure)")
            
            # Brand fit
            if quality.brand_fit < 0.7:
                steps.append("Better align with brand guidelines and tone")
            
            # Composition
            if quality.composition < 0.8:
                steps.append("Improve composition (rule of thirds, focal point)")
            
            # Variant-specific
            if not quality.variant_requirements_met:
                char = VARIANT_STRATEGY_LIBRARY.get(variant_type)
                steps.append(f"Address {char.name}-specific requirements:")
                for check_name, check_data in quality.variant_checks.items():
                    if check_data.get('status') == '❌':
                        steps.append(f"  - {check_name}")
            
            paths[variant_type] = steps if steps else ["✅ No improvements needed"]
        
        return paths


# ============================================================================
# COMPLETE VALIDATION WORKFLOW
# ============================================================================

def demo_vision_validation_workflow():
    """Demonstrate complete vision validation workflow."""
    
    print("\n" + "="*100)
    print("VISION GUARD INTEGRATION WITH 5-VARIANT STRATEGY")
    print("="*100 + "\n")
    
    # Initialize
    validator = VariantImageValidator(use_mock=True)
    
    # Example portfolio
    portfolio = VariantPortfolio(
        campaign_id="CAMP-VG-001",
        campaign_name="Vision Guard Test",
        brand_name="TechBrand",
        product_name="AI Assistant Pro"
    )
    
    # Brand guidelines
    brand_guidelines = {
        "brand_name": "TechBrand",
        "tone_of_voice": "professional",
        "style_guide": "modern minimalist",
        "primary_colors": ["#2563EB", "#1E40AF"],
        "prohibited_concepts": ["violence", "discrimination"]
    }
    
    # Mock image paths
    image_paths = {
        "control": "/path/to/control.jpg",
        "lifestyle": "/path/to/lifestyle.jpg",
        "abstract": "/path/to/abstract.jpg",
        "high_contrast": "/path/to/high_contrast.jpg",
        "data_led": "/path/to/data_led.jpg"
    }
    
    # Validate all images
    print("📊 Validating Portfolio Images\n")
    quality_results = validator.validate_portfolio_images(
        portfolio=portfolio,
        image_paths=image_paths,
        brand_guidelines=brand_guidelines
    )
    
    # Generate quality report
    report = QualityBasedRanking.generate_quality_report(quality_results)
    print(report)
    
    # Get deployment recommendations
    print("\n📈 DEPLOYMENT RECOMMENDATIONS\n")
    optimizer = VisionBasedOptimizer(validator)
    deployments = optimizer.get_deployment_recommendations(quality_results)
    
    for variant_type, recommendation in deployments.items():
        print(f"  {variant_type:20} {recommendation}")
    
    # Get budget adjustments
    print("\n💰 ADJUSTED BUDGET ALLOCATION\n")
    adjusted_budget = optimizer.get_budget_adjustment(
        quality_results,
        total_budget=100000
    )
    
    for variant_type, budget in sorted(
        adjusted_budget.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        pct = budget / 100000 * 100
        print(f"  {variant_type:20} ${budget:>10,.0f} ({pct:>5.1f}%)")
    
    # Get improvement paths
    print("\n🔧 IMPROVEMENT PATHS\n")
    paths = optimizer.get_reoptimization_path(quality_results)
    
    for variant_type, steps in paths.items():
        print(f"\n  {variant_type.upper()}")
        for step in steps:
            print(f"    {step}")


if __name__ == "__main__":
    demo_vision_validation_workflow()
