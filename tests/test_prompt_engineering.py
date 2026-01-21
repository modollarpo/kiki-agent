"""
Test Professional SD Prompt Engineering
Demonstrates advanced prompt generation with weights and techniques
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmd.creative.synccreate import (
    PromptEngineer,
    ProductMetadata,
    AudiencePersona,
    BrandGuidelines,
    VariantStrategy,
    PlatformFormat
)


def test_prompt_engineering():
    """Test all 5 variant types with professional prompt engineering."""
    
    print("🎨 Professional SD Prompt Engineering Test")
    print("=" * 100)
    
    # Setup test data
    product = ProductMetadata(
        product_name="KIKI Agent™ Pro",
        features=["AI bidding", "Real-time analytics", "Multi-platform"],
        usp="3x ROAS in 30 days",
        category="Marketing Automation",
        visual_assets=["dashboard.png"]
    )
    
    persona = AudiencePersona(
        persona_id="high_value_churner",
        segment_name="High-Value At-Risk",
        ltv_score=0.92,  # Very high LTV
        churn_risk=0.73,  # High churn risk
        preferred_messaging="urgent, data-driven",
        pain_points=["ROI uncertainty"],
        motivations=["efficiency", "competitive advantage"],
        ltv_trigger="Win-back campaign"
    )
    
    guidelines = BrandGuidelines(
        brand_name="KIKI Agent™",
        primary_colors=["#6366f1", "#8b5cf6"],
        secondary_colors=["#10b981"],
        fonts=["Inter"],
        logo_path="assets/logo.png",
        tone_of_voice="professional",
        prohibited_terms=["cheap", "free", "guaranteed"],
        prohibited_concepts=["violence", "discrimination"],
        target_audience="B2B SaaS",
        style_guide="minimalist",
        dei_profile={"inclusive_imagery": True}
    )
    
    # Test each variant type
    variants = [
        (VariantStrategy.CONTROL, PlatformFormat.META_SQUARE, "Meta Feed - Control Product Shot"),
        (VariantStrategy.LIFESTYLE, PlatformFormat.TIKTOK_VERTICAL, "TikTok - Lifestyle Moment"),
        (VariantStrategy.ABSTRACT, PlatformFormat.LINKEDIN_PROFESSIONAL, "LinkedIn - Abstract Concept"),
        (VariantStrategy.HIGH_CONTRAST, PlatformFormat.META_SQUARE, "Meta - High-Contrast Bold"),
        (VariantStrategy.DATA_LED, PlatformFormat.GOOGLE_RESPONSIVE, "Google - Data-Driven USP"),
    ]
    
    for variant_type, platform, description in variants:
        print(f"\n{'='*100}")
        print(f"🎯 {description}")
        print(f"   Type: {variant_type.value} | Platform: {platform.value}")
        print(f"{'='*100}")
        
        # Generate prompts
        positive, negative = PromptEngineer.craft_prompt(
            product=product,
            persona=persona,
            variant_type=variant_type,
            platform=platform,
            guidelines=guidelines
        )
        
        # Apply persona enhancements
        positive_enhanced = PromptEngineer.add_persona_context(positive, persona)
        
        # Apply platform optimization
        positive_final = PromptEngineer.optimize_for_platform(positive_enhanced, platform)
        
        print(f"\n📝 POSITIVE PROMPT ({len(positive_final)} chars):")
        print(f"   {positive_final[:200]}...")
        print(f"   ...{positive_final[-100:]}")
        
        print(f"\n🚫 NEGATIVE PROMPT ({len(negative)} chars):")
        print(f"   {negative[:150]}...")
        
        # Highlight key features
        print(f"\n✨ KEY FEATURES:")
        weight_count = positive_final.count(":")
        print(f"   • Weighted keywords: {weight_count}")
        print(f"   • Has quality boosters: {'masterpiece' in positive_final}")
        print(f"   • Has composition rules: {'rule of thirds' in positive_final}")
        print(f"   • Platform-optimized: {platform.value in positive_final}")
        print(f"   • Persona-enhanced: {'premium quality' in positive_final or 'attention-grabbing' in positive_final}")
    
    print(f"\n{'='*100}")
    print("✅ Professional prompt engineering test complete!")
    print("\nKey Capabilities Demonstrated:")
    print("  • Weight syntax (keyword:1.3) for emphasis")
    print("  • Quality boosters and technical specifications")
    print("  • Camera angles and lighting techniques")
    print("  • Color theory and material specifications")
    print("  • Platform-specific optimizations")
    print("  • Persona-driven visual enhancements")
    print("  • Comprehensive negative prompting")
    print("=" * 100)


if __name__ == "__main__":
    test_prompt_engineering()
