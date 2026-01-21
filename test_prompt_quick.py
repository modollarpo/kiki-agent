"""Quick test of professional SD prompt engineering"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmd.creative.synccreate import PromptEngineer, ProductMetadata, AudiencePersona, BrandGuidelines, VariantStrategy, PlatformFormat

# Test data
product = ProductMetadata("KIKI Agent™ Pro", ["AI bidding"], "3x ROAS in 30 days", "MarTech", [])
persona = AudiencePersona("test", "High-Value", 0.92, 0.73, "urgent", ["ROI"], ["efficiency"], "Win-back")
guidelines = BrandGuidelines("KIKI", ["#6366f1"], ["#10b981"], ["Inter"], None, "pro", "minimalist", ["cheap"], ["violence"], "B2B", {})

print("🎨 Professional SD Prompt Engineering Demo\n")

# Test Control variant for Meta
positive, negative = PromptEngineer.craft_prompt(product, persona, VariantStrategy.CONTROL, PlatformFormat.META_SQUARE, guidelines)

print("📝 POSITIVE PROMPT:")
print(positive[:300])
print("...\n")

print("🚫 NEGATIVE PROMPT:")  
print(negative[:200])
print("...\n")

print("✅ Key Features:")
print(f"   • Uses weights: {':1.' in positive}")
print(f"   • Character count: {len(positive)}")
print(f"   • Has 'masterpiece': {'masterpiece' in positive}")
print(f"   • Has 'rule of thirds': {'rule of thirds' in positive}")
print(f"   • Platform optimized: {'1:1 aspect ratio' in positive}")
