"""
Professional SD Prompt Engineering - Complete Demo
Shows all 5 variant types with full prompts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmd.creative.synccreate import *

product = ProductMetadata("KIKI Agent™ Pro", ["AI bidding", "Real-time analytics"], "3x ROAS in 30 days", "Marketing Automation", ["dashboard.png"])
persona = AudiencePersona("high_ltv", "Premium Enterprise", 0.95, 0.68, "data-driven", ["ROI uncertainty"], ["efficiency", "growth"], "High-value win-back")
guidelines = BrandGuidelines("KIKI Agent™", ["#6366f1"], ["#10b981"], ["Inter"], "logo.png", "professional", "minimalist", ["cheap", "free"], ["violence"], "Enterprise B2B", {})

variants = [
    (VariantStrategy.CONTROL, PlatformFormat.META_SQUARE, "Control - Product Hero"),
    (VariantStrategy.LIFESTYLE, PlatformFormat.TIKTOK_VERTICAL, "Lifestyle - In Action"),
    (VariantStrategy.ABSTRACT, PlatformFormat.LINKEDIN_PROFESSIONAL, "Abstract - Concept"),
    (VariantStrategy.HIGH_CONTRAST, PlatformFormat.META_SQUARE, "High-Contrast - Bold"),
    (VariantStrategy.DATA_LED, PlatformFormat.GOOGLE_RESPONSIVE, "Data-Led - Proof"),
]

print("="*120)
print("🎨 PROFESSIONAL SD PROMPT ENGINEERING - FULL DEMO")
print("="*120)

for variant_type, platform, name in variants:
    positive, negative = PromptEngineer.craft_prompt(product, persona, variant_type, platform, guidelines)
    
    # Apply enhancements
    positive = PromptEngineer.add_persona_context(positive, persona)
    positive = PromptEngineer.optimize_for_platform(positive, platform)
    
    print(f"\n{'─'*120}")
    print(f"✨ {name}")
    print(f"   Type: {variant_type.value} | Platform: {platform.value}")
    print(f"{'─'*120}")
    
    print(f"\n📝 POSITIVE PROMPT ({len(positive)} chars):")
    print(f"\n{positive}\n")
    
    print(f"🚫 NEGATIVE PROMPT ({len(negative)} chars):")
    print(f"\n{negative}\n")
    
    # Analysis
    weights = positive.count(":1.")
    print(f"📊 ANALYSIS:")
    print(f"   • Weighted keywords: {weights}")
    print(f"   • Total length: {len(positive)} characters")
    print(f"   • Quality terms: {'masterpiece' in positive}, {'ultra detailed' in positive}")
    print(f"   • Composition: {'rule of thirds' in positive}, {'balanced composition' in positive}")
    print(f"   • Lighting: {'lighting' in positive}")
    print(f"   • Camera angle: {'angle' in positive or 'shot' in positive or 'perspective' in positive}")
    print(f"   • Color theory: {'color' in positive}")
    print(f"   • Materials: {'material' in positive or 'texture' in positive or 'finish' in positive}")

print(f"\n{'='*120}")
print("✅ COMPLETE - Professional SD XL prompts generated with:")
print("   • Weight syntax for emphasis (keyword:1.3)")
print("   • Quality boosters (masterpiece, ultra detailed, 8k)")
print("   • Composition rules (rule of thirds, focal point)")
print("   • Lighting techniques (studio, natural, dramatic)")
print("   • Camera angles (hero, product, lifestyle, dynamic)")
print("   • Color theory (complementary, monochromatic, high-contrast)")
print("   • Material specifications (matte, glossy, premium)")
print("   • Platform optimization (TikTok, Meta, LinkedIn, Google)")
print("   • Persona enhancements (premium, attention-grabbing)")
print("   • Comprehensive negative prompting with weights")
print("="*120)
