"""
Vision Guard Validation Demo

Complete demonstration of CLIP vision validation for 5-variant strategy.
"""

from vision_guard import VisionGuardWithVariantOptimization
from variant_strategy import VARIANT_STRATEGY_LIBRARY


def demo_vision_guard():
    """Run complete vision guard demonstration."""
    
    print("\n" + "="*100)
    print("VISION GUARD WITH CLIP VALIDATION - COMPLETE DEMO")
    print("="*100 + "\n")
    
    # Initialize vision guard
    guard = VisionGuardWithVariantOptimization(use_mock=True)
    
    # Brand guidelines
    brand_guidelines = {
        "brand_name": "TechBrand",
        "tone_of_voice": "professional",
        "style_guide": "modern minimalist",
        "primary_colors": ["#2563EB", "#1E40AF"],
        "prohibited_concepts": ["violence", "discrimination", "deceptive"]
    }
    
    # Variants to validate
    variants = ["control", "lifestyle", "abstract", "high_contrast", "data_led"]
    
    print("📊 CLIP-BASED VISION VALIDATION FOR 5 VARIANTS\n")
    print("Product: AI Assistant Pro")
    print("Brand: TechBrand")
    print("Validation Method: CLIP embeddings with variant-specific checks\n")
    
    all_results = {}
    
    for variant_type in variants:
        print(f"\n{'='*100}")
        print(f"{variant_type.upper()} VARIANT")
        print(f"{'='*100}\n")
        
        # Validate (using mock path)
        result = guard.validate_variant(
            image_path=f"/mock/{variant_type}.jpg",
            product_name="AI Assistant Pro",
            variant_type=variant_type,
            brand_guidelines=brand_guidelines
        )
        
        all_results[variant_type] = result
        
        # Base validation
        print("📈 BASE VALIDATION SCORES")
        print("-" * 50)
        print(f"  Product Confidence:      {result['base_validation']['product_confidence']:>7.1%}")
        print(f"  Safety Score:            {result['base_validation']['safety_score']:>7.1%}")
        print(f"  Quality Score:           {result['base_validation']['quality_score']:>7.1%}")
        print(f"  Brand Fit:               {result['brand_fit_score']:>7.1%}")
        print(f"  Composition:             {result['composition_score']:>7.1%}")
        print(f"  Overall Score:           {result['base_validation']['overall_score']:>7.1%}")
        
        # Approval status
        print(f"\n📋 APPROVAL STATUS: {result['approval_status']}")
        
        # Detected elements
        if result['detected_objects']:
            print(f"\n🔍 DETECTED OBJECTS")
            print("-" * 50)
            for obj in result['detected_objects'][:5]:
                print(f"  • {obj}")
        
        if result['detected_concepts']:
            print(f"\n💡 DETECTED CONCEPTS")
            print("-" * 50)
            for concept in result['detected_concepts'][:5]:
                print(f"  • {concept}")
        
        # Safety flags
        if result['safety_flags']:
            print(f"\n⚠️ SAFETY FLAGS")
            print("-" * 50)
            for flag in result['safety_flags']:
                print(f"  • {flag}")
        
        # Variant-specific checks
        print(f"\n✓ VARIANT-SPECIFIC CHECKS ({variant_type.upper()})")
        print("-" * 50)
        
        char = VARIANT_STRATEGY_LIBRARY[variant_type]
        print(f"Expected Focus: {char.visual_focus}")
        print(f"Messaging Style: {char.messaging_style}\n")
        
        for check_name, check_data in result['variant_checks'].items():
            status = check_data.get('status', '❓')
            
            if isinstance(check_data, dict):
                if 'confidence' in check_data:
                    conf = f" ({check_data['confidence']:.1%})"
                elif 'actual' in check_data and 'required' in check_data:
                    conf = f" (needed {check_data['required']:.1%}, got {check_data['actual']:.1%})"
                else:
                    conf = ""
                
                print(f"  {status} {check_name}{conf}")
            else:
                print(f"  {status} {check_name}")
        
        # Recommendations
        if result['recommendations']:
            print(f"\n💬 RECOMMENDATIONS")
            print("-" * 50)
            for rec in result['recommendations']:
                print(f"  {rec}")
    
    # SUMMARY ANALYSIS
    print(f"\n\n{'='*100}")
    print("PORTFOLIO SUMMARY & RECOMMENDATIONS")
    print(f"{'='*100}\n")
    
    # Rank by overall score
    print("📊 VARIANT RANKING BY QUALITY\n")
    
    ranked = sorted(
        all_results.items(),
        key=lambda x: x[1]['base_validation']['overall_score'],
        reverse=True
    )
    
    for rank, (variant_type, result) in enumerate(ranked, 1):
        overall = result['base_validation']['overall_score']
        char = VARIANT_STRATEGY_LIBRARY[variant_type]
        
        if overall >= 0.85:
            tier = "🏆 EXCELLENT"
        elif overall >= 0.75:
            tier = "✅ GOOD"
        elif overall >= 0.65:
            tier = "⚠️ FAIR"
        else:
            tier = "❌ NEEDS WORK"
        
        print(f"{rank}. {char.name:<20} {overall:>6.1%}  {tier}")
    
    # Budget allocation based on quality
    print("\n\n💰 BUDGET ALLOCATION (Based on Quality Scores)\n")
    
    total_score = sum(
        result['base_validation']['overall_score']
        for result in all_results.values()
    )
    
    budget = 100000
    allocations = {}
    
    for variant_type, result in all_results.items():
        overall = result['base_validation']['overall_score']
        allocation = budget * (overall / total_score) if total_score > 0 else budget / 5
        allocations[variant_type] = allocation
        
        char = VARIANT_STRATEGY_LIBRARY[variant_type]
        pct = allocation / budget * 100
        print(f"  {char.name:<20} ${allocation:>10,.0f} ({pct:>5.1f}%)")
    
    # Deployment strategy
    print("\n\n🚀 DEPLOYMENT STRATEGY\n")
    
    print("PHASE 1 (Week 1): Conservative Test")
    print("  Deploy top 2 performers only")
    top_2 = sorted(
        allocations.items(),
        key=lambda x: x[1],
        reverse=True
    )[:2]
    phase1_budget = sum(x[1] for x in top_2) * 0.5  # 50% of budget
    for variant_type, _ in top_2:
        char = VARIANT_STRATEGY_LIBRARY[variant_type]
        print(f"    • {char.name}: ${phase1_budget / 2:,.0f}")
    
    print(f"\nPHASE 2 (Week 2-3): Expanded Test")
    print("  Deploy top 3 performers")
    top_3 = sorted(
        allocations.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    phase2_budget = sum(x[1] for x in top_3) * 0.8
    for variant_type, _ in top_3:
        char = VARIANT_STRATEGY_LIBRARY[variant_type]
        print(f"    • {char.name}: ${phase2_budget / 3:,.0f}")
    
    print(f"\nPHASE 3 (Week 4+): Full Rollout")
    print("  Deploy all variants with optimized allocation")
    for variant_type, allocation in sorted(
        allocations.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        char = VARIANT_STRATEGY_LIBRARY[variant_type]
        pct = allocation / budget * 100
        status = "✅" if result['base_validation']['overall_score'] > 0.75 else "⚠️"
        print(f"    {status} {char.name:<20} ${allocation:>10,.0f} ({pct:>5.1f}%)")
    
    # Key insights
    print(f"\n\n💡 KEY INSIGHTS\n")
    
    print("Vision Validation Findings:")
    best_variant = max(
        all_results.items(),
        key=lambda x: x[1]['base_validation']['overall_score']
    )
    best_char = VARIANT_STRATEGY_LIBRARY[best_variant[0]]
    print(f"  • {best_char.name} is highest quality - {best_variant[1]['base_validation']['overall_score']:.1%}")
    
    print("\nCommon Issues:")
    all_flags = []
    for result in all_results.values():
        all_flags.extend(result['safety_flags'])
    
    if all_flags:
        print(f"  • Safety concerns detected across {len(set(all_flags))} variants")
    else:
        print("  • No safety concerns detected ✅")
    
    print("\nRecommendations:")
    print("  • Prioritize quality over quantity - focus on fewer, high-quality variants")
    print("  • Use CLIP validation to catch issues early before deployment")
    print("  • Align variants with brand guidelines for maximum performance")
    print("  • Test variants that meet safety thresholds (≥0.80)")
    
    print(f"\n{'='*100}\n")


if __name__ == "__main__":
    demo_vision_guard()
