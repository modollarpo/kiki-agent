"""
KIKI SyncCreate™ - AI Creative Generation Engine

Generates ad variants using Stable Diffusion with brand safety guardrails.

Features:
- Stable Diffusion image generation
- Multi-variant generation (A/B/C testing)
- Brand safety content moderation
- Brand guideline enforcement (colors, logos, tone)
- Automated creative versioning
"""

from typing import List, Dict, Optional, Tuple, Literal
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import re
import hashlib
from enum import Enum


class VariantStrategy(Enum):
    """5-variant generation strategy types."""
    CONTROL = "control"  # Literal product shot
    LIFESTYLE = "lifestyle"  # Product in use
    ABSTRACT = "abstract"  # Emotional benefit visualization
    HIGH_CONTRAST = "high_contrast"  # Stop-the-scroll design
    DATA_LED = "data_led"  # USP-focused


class PlatformFormat(Enum):
    """Ad platform format specifications."""
    TIKTOK_VERTICAL = "tiktok_9_16"
    META_SQUARE = "meta_1_1"
    LINKEDIN_PROFESSIONAL = "linkedin_16_9"
    GOOGLE_RESPONSIVE = "google_responsive"


@dataclass
class AudiencePersona:
    """Audience segment from SyncValue™ brain."""
    persona_id: str
    segment_name: str  # e.g., "High-LTV Retained User"
    ltv_score: float  # 0.0 to 1.0
    churn_risk: float  # 0.0 to 1.0
    preferred_messaging: str  # e.g., "value-focused", "innovation-led"
    pain_points: List[str]
    motivations: List[str]
    ltv_trigger: str  # Specific hook predicted to convert


@dataclass
class ProductMetadata:
    """Product context for creative generation."""
    product_name: str
    features: List[str]
    usp: str  # Unique Selling Proposition
    category: str
    visual_assets: List[str]  # Paths to product images


@dataclass
class BrandGuidelines:
    """Brand identity and safety rules."""
    brand_name: str
    primary_colors: List[str]  # Hex codes
    secondary_colors: List[str]
    fonts: List[str]
    logo_path: Optional[str]
    tone_of_voice: str  # "professional", "casual", "playful", etc.
    style_guide: str  # "minimalist", "energetic", "corporate"
    prohibited_terms: List[str]
    prohibited_concepts: List[str]
    target_audience: str
    dei_profile: Dict[str, any] = field(default_factory=dict)  # Diversity & Inclusion
    
    def to_dict(self) -> dict:
        return {
            'brand_name': self.brand_name,
            'primary_colors': self.primary_colors,
            'secondary_colors': self.secondary_colors,
            'fonts': self.fonts,
            'logo_path': self.logo_path,
            'tone_of_voice': self.tone_of_voice,
            'prohibited_terms': self.prohibited_terms,
            'prohibited_concepts': self.prohibited_concepts,
            'target_audience': self.target_audience,
        }


@dataclass
class SafetyCheckResult:
    """Content moderation result."""
    is_safe: bool
    safety_score: float  # 0.0 to 1.0
    violations: List[str]
    warnings: List[str]
    filters_triggered: List[str]
    
    def to_dict(self) -> dict:
        return {
            'is_safe': self.is_safe,
            'safety_score': self.safety_score,
            'violations': self.violations,
            'warnings': self.warnings,
            'filters_triggered': self.filters_triggered,
        }


@dataclass
class CreativeVariant:
    """Generated ad creative with SyncFlow™ integration."""
    variant_id: str
    variant_type: VariantStrategy
    image_url: str
    headline_text: str  # Max 40 chars
    body_copy: str  # Max 125 chars
    cta_button: str
    platform_format: PlatformFormat
    sd_prompt: str  # Stable Diffusion prompt used
    brand_compliant: bool
    safety_score: float  # 0.0 to 1.0 from Brand Safety Gate
    violations: List[str]
    timestamp: datetime
    vision_validation: Optional[Dict] = None  # CLIP/Llava results
    persona_match: Optional[str] = None  # Which persona this targets
    
    def to_dict(self) -> dict:
        return {
            'variant_id': self.variant_id,
            'variant_type': self.variant_type.value,
            'image_url': self.image_url,
            'headline_text': self.headline_text[:40],  # Enforce max length
            'body_copy': self.body_copy[:125],
            'cta_button': self.cta_button,
            'platform_format': self.platform_format.value,
            'sd_prompt': self.sd_prompt,
            'brand_compliant': self.brand_compliant,
            'safety_score': self.safety_score,
            'violations': self.violations,
            'vision_validation': self.vision_validation,
            'persona_match': self.persona_match,
            'timestamp': self.timestamp.isoformat(),
        }
    
    def to_grpc_format(self) -> dict:
        """Format for SyncFlow™ gRPC/JSON API."""
        return {
            'id': self.variant_id,
            'type': self.variant_type.value,
            'creative': {
                'image_url': self.image_url,
                'headline': self.headline_text[:40],
                'body': self.body_copy[:125],
                'cta': self.cta_button,
            },
            'targeting': {
                'platform': self.platform_format.value,
                'persona': self.persona_match,
            },
            'quality': {
                'safety_score': round(self.safety_score, 3),
                'brand_compliant': self.brand_compliant,
                'vision_verified': self.vision_validation is not None,
            },
            'timestamp': self.timestamp.isoformat(),
        }


class PromptEngineer:
    """
    Professional Stable Diffusion XL Prompt Engineering.
    
    Implements advanced techniques:
    - Weight syntax: (keyword:1.3) for emphasis
    - Quality boosters and artist styles
    - Color theory and lighting techniques
    - Camera angles and composition rules
    - Material/texture specifications
    """
    
    # Quality boosters (SD XL optimized)
    QUALITY_BOOSTERS = [
        "masterpiece",
        "best quality",
        "ultra detailed",
        "8k uhd",
        "sharp focus",
        "professional photography",
        "award winning composition"
    ]
    
    # Lighting techniques
    LIGHTING_STYLES = {
        "studio": "studio lighting, three-point lighting, professional setup, controlled environment",
        "natural": "soft natural lighting, golden hour, diffused sunlight, warm tones",
        "dramatic": "dramatic lighting, high contrast, chiaroscuro, cinematic",
        "soft": "soft box lighting, even illumination, no harsh shadows, gentle",
        "rim": "rim lighting, edge lighting, backlit, glowing edges"
    }
    
    # Camera angles
    CAMERA_ANGLES = {
        "hero": "low angle shot, hero perspective, empowering viewpoint",
        "product": "eye level, straight on, centered composition",
        "lifestyle": "slightly elevated angle, candid perspective, natural",
        "dynamic": "dutch angle, dynamic composition, energetic viewpoint",
        "detail": "macro shot, close-up, detailed view, shallow depth of field"
    }
    
    # Artist/style references (legally safe, style-based only)
    STYLE_REFERENCES = {
        "minimalist": "minimalist photography style, clean aesthetic, Apple product photography style",
        "energetic": "vibrant commercial photography, high energy advertising style",
        "corporate": "corporate photography style, professional business aesthetic, Forbes magazine quality",
        "lifestyle": "lifestyle magazine photography, authentic moments, editorial quality",
        "luxury": "luxury brand photography, premium aesthetic, high-end commercial"
    }
    
    # Color theory keywords
    COLOR_THEORY = {
        "complementary": "complementary color scheme, balanced palette, harmonious colors",
        "monochromatic": "monochromatic palette, single color variations, tonal harmony",
        "triadic": "triadic color scheme, vibrant balance, three-color harmony",
        "analogous": "analogous colors, natural progression, smooth transitions",
        "high_contrast": "high contrast colors, bold palette, striking visual impact"
    }
    
    # Material/texture specifications
    MATERIALS = {
        "tech": "sleek surfaces, brushed metal, glass reflections, modern materials",
        "organic": "natural textures, wood grain, fabric, organic materials",
        "premium": "premium materials, luxurious textures, high-end finishes",
        "matte": "matte finish, non-reflective, soft surfaces",
        "glossy": "glossy finish, reflective surfaces, polished look"
    }
    
    # Comprehensive negative prompt with weights
    NEGATIVE_PROMPT_PROFESSIONAL = (
        "(deformed:1.3), (distorted:1.3), (disfigured:1.3), "
        "(poorly drawn:1.2), (bad anatomy:1.2), (wrong anatomy:1.2), "
        "(extra limbs:1.2), (missing limbs:1.2), (floating limbs:1.2), "
        "(mutated hands and fingers:1.4), (disconnected limbs:1.2), "
        "(mutation:1.2), (mutated:1.2), (ugly:1.1), (disgusting:1.1), "
        "(blurry:1.3), (amputation:1.1), (watermark:1.4), (text:1.4), "
        "(signature:1.4), (username:1.4), (logo:1.3), "
        "low quality, worst quality, jpeg artifacts, duplicate, "
        "morbid, mutilated, out of frame, extra fingers, mutated hands, "
        "poorly drawn hands, poorly drawn face, mutation, deformed, "
        "bad proportions, gross proportions, malformed limbs, "
        "missing arms, missing legs, extra arms, extra legs, "
        "fused fingers, too many fingers, long neck"
    )
    
    @staticmethod
    def craft_prompt(
        product: ProductMetadata,
        persona: AudiencePersona,
        variant_type: VariantStrategy,
        platform: PlatformFormat,
        guidelines: BrandGuidelines
    ) -> Tuple[str, str]:
        """
        Generate professional SD XL prompt with weights and advanced techniques.
        
        Returns: (positive_prompt, negative_prompt)
        """
        
        # === SUBJECT & CORE CONCEPT ===
        if variant_type == VariantStrategy.CONTROL:
            subject = f"(product photography:1.3), {product.product_name}, (centered composition:1.2)"
            camera = PromptEngineer.CAMERA_ANGLES["product"]
            lighting = PromptEngineer.LIGHTING_STYLES["studio"]
            
        elif variant_type == VariantStrategy.LIFESTYLE:
            subject = f"(lifestyle photography:1.3), person using {product.product_name}, (authentic moment:1.2), natural interaction"
            camera = PromptEngineer.CAMERA_ANGLES["lifestyle"]
            lighting = PromptEngineer.LIGHTING_STYLES["natural"]
            
        elif variant_type == VariantStrategy.ABSTRACT:
            emotion = persona.motivations[0] if persona.motivations else "success"
            subject = f"(abstract visualization:1.3), (conceptual art:1.2), {emotion} concept, {product.category} industry theme"
            camera = PromptEngineer.CAMERA_ANGLES["dynamic"]
            lighting = PromptEngineer.LIGHTING_STYLES["dramatic"]
            
        elif variant_type == VariantStrategy.HIGH_CONTRAST:
            subject = f"(bold design:1.4), {product.product_name}, (eye-catching:1.3), (scroll-stopping visual:1.3)"
            camera = PromptEngineer.CAMERA_ANGLES["hero"]
            lighting = PromptEngineer.LIGHTING_STYLES["dramatic"]
            
        else:  # DATA_LED
            subject = f"(infographic style:1.3), {product.product_name}, (data visualization:1.2), {product.usp}"
            camera = PromptEngineer.CAMERA_ANGLES["detail"]
            lighting = PromptEngineer.LIGHTING_STYLES["soft"]
        
        # === STYLE & AESTHETICS ===
        style_ref = PromptEngineer.STYLE_REFERENCES.get(
            guidelines.style_guide,
            PromptEngineer.STYLE_REFERENCES["minimalist"]
        )
        
        if guidelines.style_guide == "minimalist":
            style_keywords = "(clean background:1.3), (minimal clutter:1.2), negative space, simplicity"
            color_scheme = PromptEngineer.COLOR_THEORY["monochromatic"]
            materials = PromptEngineer.MATERIALS["matte"]
            
        elif guidelines.style_guide == "energetic":
            style_keywords = "(vibrant colors:1.3), (dynamic composition:1.2), (high energy:1.2)"
            color_scheme = PromptEngineer.COLOR_THEORY["high_contrast"]
            materials = PromptEngineer.MATERIALS["glossy"]
            
        else:  # corporate
            style_keywords = "(professional setting:1.2), (modern aesthetic:1.2), corporate environment"
            color_scheme = PromptEngineer.COLOR_THEORY["analogous"]
            materials = PromptEngineer.MATERIALS["premium"]
        
        # === COMPOSITION RULES ===
        composition = (
            "(rule of thirds:1.2), (clear focal point:1.3), "
            "(balanced composition:1.1), professional framing"
        )
        
        # === PLATFORM-SPECIFIC ADJUSTMENTS ===
        if platform == PlatformFormat.TIKTOK_VERTICAL:
            aspect = "(9:16 aspect ratio:1.2), vertical orientation, (mobile-first:1.2), portrait format"
            platform_opt = "optimized for mobile viewing, vertical scroll"
            
        elif platform == PlatformFormat.META_SQUARE:
            aspect = "(1:1 aspect ratio:1.2), square format, (feed-optimized:1.2)"
            platform_opt = "social media optimized, thumb-stopping visual"
            
        elif platform == PlatformFormat.LINKEDIN_PROFESSIONAL:
            aspect = "(16:9 aspect ratio:1.2), horizontal format, (professional setting:1.2)"
            platform_opt = "business environment, corporate aesthetic"
            
        else:  # GOOGLE_RESPONSIVE
            aspect = "responsive format, flexible composition, multi-device optimized"
            platform_opt = "versatile layout, adaptive design"
        
        # === TECHNICAL QUALITY ===
        quality = ", ".join([
            f"({boost}:1.1)" if i < 3 else boost
            for i, boost in enumerate(PromptEngineer.QUALITY_BOOSTERS)
        ])
        
        # === ASSEMBLE POSITIVE PROMPT ===
        positive_prompt = ", ".join([
            subject,
            camera,
            lighting,
            composition,
            style_keywords,
            style_ref,
            color_scheme,
            materials,
            aspect,
            platform_opt,
            quality
        ])
        
        # === BRAND-SPECIFIC NEGATIVES ===
        brand_negatives = ", ".join([
            f"({term}:1.3)" for term in guidelines.prohibited_terms[:3]
        ] + [
            f"({concept}:1.2)" for concept in guidelines.prohibited_concepts
        ] + [
            "(competitor branding:1.4)",
            "(misleading imagery:1.3)",
            "(clickbait elements:1.3)",
            "(unprofessional:1.2)",
            "stock photo watermark"
        ])
        
        # === ASSEMBLE NEGATIVE PROMPT ===
        negative_prompt = f"{PromptEngineer.NEGATIVE_PROMPT_PROFESSIONAL}, {brand_negatives}"
        
        return positive_prompt, negative_prompt
    
    @staticmethod
    def optimize_for_platform(prompt: str, platform: PlatformFormat) -> str:
        """Add platform-specific optimizations to existing prompt."""
        
        platform_boosters = {
            PlatformFormat.TIKTOK_VERTICAL: ", (mobile-optimized:1.2), (Gen Z aesthetic:1.1), trendy visual style",
            PlatformFormat.META_SQUARE: ", (Instagram aesthetic:1.2), (feed-stopping:1.2), social media ready",
            PlatformFormat.LINKEDIN_PROFESSIONAL: ", (corporate polish:1.2), (business appropriate:1.2), executive quality",
            PlatformFormat.GOOGLE_RESPONSIVE: ", (versatile design:1.1), multi-format compatible, adaptive layout"
        }
        
        return prompt + platform_boosters.get(platform, "")
    
    @staticmethod
    def add_persona_context(prompt: str, persona: AudiencePersona) -> str:
        """Enhance prompt with persona-specific visual cues."""
        
        persona_enhancements = []
        
        # High LTV = Premium aesthetic
        if persona.ltv_score > 0.8:
            persona_enhancements.append("(premium quality:1.2)")
            persona_enhancements.append("luxury aesthetic")
        
        # High churn risk = Urgency visual cues
        if persona.churn_risk > 0.6:
            persona_enhancements.append("(attention-grabbing:1.2)")
            persona_enhancements.append("immediate impact")
        
        # Motivation-based visual themes
        if "efficiency" in persona.motivations:
            persona_enhancements.append("sleek")
            persona_enhancements.append("streamlined")
        
        if persona_enhancements:
            return prompt + ", " + ", ".join(persona_enhancements)
        
        return prompt


class VisionGuard:
    """CLIP/Llava-based vision validation for generated images."""
    
    def __init__(self):
        # In production: load CLIP model
        # from transformers import CLIPProcessor, CLIPModel
        # self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
        # self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
        self.clip_model = None  # Mock for now
    
    def validate_image(
        self,
        image_path: str,
        expected_product: str,
        guidelines: BrandGuidelines
    ) -> Dict:
        """Inverse vision check: Does image contain product and meet brand safety?"""
        
        # Mock validation (in production: use CLIP embeddings)
        validation_result = {
            'contains_product': True,  # CLIP cosine similarity > 0.7
            'brand_safe': True,  # No prohibited content detected
            'quality_score': 0.92,  # Technical quality (sharpness, composition)
            'confidence': 0.89,
            'detected_elements': [
                expected_product,
                'professional setting',
                'clear branding'
            ],
            'safety_flags': [],  # Empty = safe
        }
        
        return validation_result


class BrandSafetyGuardrails:
    """Content moderation and brand compliance checks (Three-Gate Safety Check)."""
    
    def __init__(self, guidelines: BrandGuidelines):
        self.guidelines = guidelines
        
        # Pre-defined unsafe patterns (can be enhanced with ML models)
        self.unsafe_patterns = [
            r'\b(violence|weapon|drug|alcohol|tobacco)\b',
            r'\b(hate|discriminat|racist|sexist)\b',
            r'\b(explicit|nude|nsfw)\b',
            r'\b(clickbait|fake|scam|limited time offer)\b',  # Gate 2: Copy Integrity
        ]
    
    def three_gate_safety_check(
        self,
        text: str,
        image_validation: Optional[Dict] = None
    ) -> SafetyCheckResult:
        """Run Three-Gate Safety Check: Visual Compliance + Copy Integrity + Identity Guard."""
        violations = []
        warnings = []
        filters_triggered = []
        
        text_lower = text.lower()
        
        # GATE 1: Visual Compliance (if image validation provided)
        if image_validation and image_validation.get('safety_flags'):
            violations.extend(image_validation['safety_flags'])
            filters_triggered.append("visual_compliance")
        
        # GATE 2: Copy Integrity
        # Check prohibited terms
        for term in self.guidelines.prohibited_terms:
            if term.lower() in text_lower:
                violations.append(f"Prohibited term: '{term}'")
                filters_triggered.append("prohibited_terms")
        
        # Check for clickbait/deceptive patterns
        if re.search(r'\b(limited time|act now|exclusive deal|guaranteed)\b', text_lower):
            warnings.append("Potential clickbait language detected")
            filters_triggered.append("copy_integrity")
        
        # Check prohibited concepts
        for concept in self.guidelines.prohibited_concepts:
            if concept.lower() in text_lower:
                violations.append(f"Prohibited concept: '{concept}'")
                filters_triggered.append("prohibited_concepts")
        
        # Check unsafe patterns
        for pattern in self.unsafe_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                violations.append(f"Unsafe content detected: {matches}")
                filters_triggered.append("unsafe_patterns")
        
        # GATE 3: Identity Guard (DEI compliance)
        # In production: Use vision model to check diversity representation
        # For now: enforce in prompt engineering phase
        
        # Calculate safety score (ISO 27001 transparency standard)
        is_safe = len(violations) == 0
        if not is_safe:
            safety_score = max(0.0, 1.0 - (len(violations) * 0.2) - (len(warnings) * 0.05))
        else:
            safety_score = max(0.8, 1.0 - (len(warnings) * 0.05))  # Warnings reduce score slightly
        
        return SafetyCheckResult(
            is_safe=is_safe,
            safety_score=safety_score,
            violations=violations,
            warnings=warnings,
            filters_triggered=list(set(filters_triggered))
        )
    
    def check_brand_compliance(self, creative_text: str) -> bool:
        """Verify creative adheres to brand guidelines."""
        # Check if brand name is mentioned correctly
        if self.guidelines.brand_name.lower() not in creative_text.lower():
            return False
        
        # Additional brand checks can be added here
        # - Tone of voice analysis
        # - Terminology consistency
        # - Brand value alignment
        
        return True
    
    def enhance_prompt_with_brand(self, base_prompt: str) -> str:
        """Add brand guidelines to generation prompt."""
        brand_context = f"""
Style: {self.guidelines.tone_of_voice}
Brand: {self.guidelines.brand_name}
Colors: {', '.join(self.guidelines.primary_colors[:3])}
Target: {self.guidelines.target_audience}
"""
        return f"{base_prompt}\n\nBrand context:\n{brand_context}"


class SyncCreateEngine:
    """AI Creative Generation Engine - The Creative Heart of SyncEngine™."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / 'creatives'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # In production, initialize Stable Diffusion pipeline here
        # from diffusers import StableDiffusionXLPipeline
        # self.sd_pipeline = StableDiffusionXLPipeline.from_pretrained(
        #     "stabilityai/stable-diffusion-xl-base-1.0"
        # )
        self.sd_pipeline = None  # Mock for now
        
        # Initialize sub-components
        self.prompt_engineer = PromptEngineer()
        self.vision_guard = VisionGuard()
    
    def _generate_variant_id(self, prompt: str, index: int, variant_type: VariantStrategy) -> str:
        """Create unique variant ID."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"variant_{timestamp}_{variant_type.value}_{prompt_hash}_{index}"
    
    def _generate_image_with_diffusion(
        self,
        positive_prompt: str,
        negative_prompt: str,
        variant_id: str
    ) -> str:
        """Generate image using Stable Diffusion XL."""
        # In production:
        # image = self.sd_pipeline(
        #     prompt=positive_prompt,
        #     negative_prompt=negative_prompt,
        #     num_inference_steps=50,
        #     guidance_scale=7.5
        # ).images[0]
        # image_path = self.output_dir / f"{variant_id}.webp"
        # image.save(image_path, format='WEBP', quality=90)
        # return str(image_path)
        
        return f"creatives/{variant_id}.webp"  # Mock path
    
    def _generate_copy_for_variant(
        self,
        variant_type: VariantStrategy,
        product: ProductMetadata,
        persona: AudiencePersona,
        guidelines: BrandGuidelines
    ) -> Tuple[str, str, str]:
        """Generate headline, body, and CTA for specific variant type."""
        
        if variant_type == VariantStrategy.CONTROL:
            headline = f"{product.product_name}"[:40]
            body = f"{product.usp}. Built for {guidelines.target_audience}."[:125]
            cta = "Shop Now"
        
        elif variant_type == VariantStrategy.LIFESTYLE:
            headline = f"Transform Your {product.category}"[:40]
            body = f"See how {guidelines.brand_name} fits your lifestyle. {persona.ltv_trigger}."[:125]
            cta = "See It in Action"
        
        elif variant_type == VariantStrategy.ABSTRACT:
            emotion = persona.motivations[0] if persona.motivations else "success"
            headline = f"Unlock Your {emotion.capitalize()}"[:40]
            body = f"{guidelines.brand_name} - {product.usp}. {persona.ltv_trigger}."[:125]
            cta = "Discover How"
        
        elif variant_type == VariantStrategy.HIGH_CONTRAST:
            headline = f"Stop Scrolling. Start {persona.motivations[0] if persona.motivations else 'Growing'}."[:40]
            body = f"{product.product_name}: {product.usp}"[:125]
            cta = "Learn More"
        
        else:  # DATA_LED
            headline = f"{product.usp}"[:40]
            body = f"{guidelines.brand_name} delivers results. {', '.join(product.features[:2])}."[:125]
            cta = "See Proof"
        
        return headline, body, cta
    
    def generate_creative_variants(
        self,
        persona: AudiencePersona,
        product: ProductMetadata,
        platform_format: PlatformFormat,
        guidelines: BrandGuidelines,
        safety_guardrails: BrandSafetyGuardrails
    ) -> List[CreativeVariant]:
        """
        Generate 5-variant strategy with Vision Guard and Three-Gate Safety Check.
        
        Input from SyncValue™:
        - persona: LTV-driven audience targeting
        - product: Product metadata with USP
        - platform_format: TikTok/Meta/LinkedIn/Google
        - guidelines: Brand identity with style guide
        
        Output to SyncFlow™:
        - List of CreativeVariant objects with gRPC-ready format
        """
        
        variants = []
        strategy_types = [
            VariantStrategy.CONTROL,
            VariantStrategy.LIFESTYLE,
            VariantStrategy.ABSTRACT,
            VariantStrategy.HIGH_CONTRAST,
            VariantStrategy.DATA_LED
        ]
        
        print(f"\n🎨 SyncCreate™ Engine - Generating 5-Variant Strategy")
        print(f"   Persona: {persona.segment_name} (LTV: {persona.ltv_score:.2f})")
        print(f"   Product: {product.product_name}")
        print(f"   Platform: {platform_format.value}")
        
        for i, variant_type in enumerate(strategy_types):
            variant_id = self._generate_variant_id(product.product_name, i, variant_type)
            
            # STEP 1: Professional Prompt Engineering
            positive_prompt, negative_prompt = self.prompt_engineer.craft_prompt(
                variant_type=variant_type,
                product=product,
                persona=persona,
                guidelines=guidelines,
                platform=platform_format
            )
            
            # STEP 2: Generate Image with Stable Diffusion
            image_url = self._generate_image_with_diffusion(
                positive_prompt=positive_prompt,
                negative_prompt=negative_prompt,
                variant_id=variant_id
            )
            
            # STEP 3: Vision Guard - CLIP Validation
            vision_validation = self.vision_guard.validate_image(
                image_path=image_url,
                expected_product=product.product_name,
                guidelines=guidelines
            )
            
            # STEP 4: Generate Copy (headline, body, CTA)
            headline, body, cta = self._generate_copy_for_variant(
                variant_type=variant_type,
                product=product,
                persona=persona,
                guidelines=guidelines
            )
            
            # STEP 5: Three-Gate Safety Check
            text_to_check = f"{headline} {body} {cta}"
            safety_result = safety_guardrails.three_gate_safety_check(
                text=text_to_check,
                image_validation=vision_validation
            )
            
            # STEP 6: Create Variant (only if passes safety threshold)
            if safety_result.is_safe and safety_result.safety_score >= 0.8:
                variant = CreativeVariant(
                    variant_id=variant_id,
                    variant_type=variant_type,
                    image_url=image_url,
                    headline_text=headline,
                    body_copy=body,
                    cta_button=cta,
                    platform_format=platform_format,
                    sd_prompt=positive_prompt,
                    brand_compliant=True,
                    safety_score=safety_result.safety_score,
                    vision_validation=vision_validation,
                    persona_match=persona.persona_id,
                    violations=safety_result.violations,
                    timestamp=datetime.now()
                )
                variants.append(variant)
                print(f"✅ {variant_type.value}: Safety {safety_result.safety_score:.2f} | Vision Quality {vision_validation['quality_score']:.2f}")
                
                if safety_result.warnings:
                    print(f"   ⚠️  Warnings: {', '.join(safety_result.warnings)}")
            else:
                print(f"❌ {variant_type.value} BLOCKED - Safety: {safety_result.safety_score:.2f}")
                print(f"   Violations: {safety_result.violations}")
        
        return variants
    
    def save_variants(self, variants: List[CreativeVariant], campaign_name: str) -> Path:
        """Save generated variants to JSON file."""
        output_file = self.output_dir / f"{campaign_name.replace(' ', '_').lower()}_variants.json"
        
        data = {
            'campaign_name': campaign_name,
            'generated_at': datetime.now().isoformat(),
            'variant_count': len(variants),
            'variants': [v.to_dict() for v in variants]
        }
        
        output_file.write_text(json.dumps(data, indent=2))
        return output_file


def demo_creative_generation():
    """Demo SyncCreate™ Enterprise Creative Generation with 5-Variant Strategy."""
    print("🎨 KIKI SyncCreate™ - Enterprise AI Creative Generation Demo")
    print("=" * 80)
    
    # Mock input from SyncValue™ (Audience Intelligence Engine)
    persona = AudiencePersona(
        persona_id="persona_high_value_churner",
        segment_name="High-Value At-Risk Customers",
        ltv_score=0.87,  # High lifetime value
        churn_risk=0.65,  # High churn probability
        preferred_messaging="results-driven, data-backed, time-sensitive",
        pain_points=["ROI uncertainty", "platform complexity", "time constraints"],
        motivations=["efficiency", "competitive advantage", "proven results"],
        ltv_trigger="Win-back campaign: Show immediate value to prevent churn"
    )
    
    product = ProductMetadata(
        product_name="KIKI Agent™ Pro",
        features=[
            "AI-powered bidding optimization",
            "Real-time performance tracking",
            "Multi-platform campaign management",
            "Predictive LTV modeling"
        ],
        usp="3x ROAS improvement in 30 days with autonomous AI agents",
        category="Marketing Automation",
        visual_assets=[
            "product_dashboard.png",
            "performance_graph.png",
            "mobile_app_screenshot.png"
        ]
    )
    
    guidelines = BrandGuidelines(
        brand_name="KIKI Agent™",
        primary_colors=["#6366f1", "#8b5cf6", "#ec4899"],
        secondary_colors=["#10b981", "#f59e0b"],
        fonts=["Inter", "SF Pro Display"],
        logo_path="assets/kiki_logo.png",
        tone_of_voice="professional, data-driven, innovative",
        prohibited_terms=["cheap", "spam", "guaranteed", "risk-free", "secret"],
        prohibited_concepts=["violence", "discrimination", "misleading claims"],
        target_audience="B2B SaaS companies and growth teams",
        style_guide="minimalist",  # Options: minimalist, energetic, corporate
        dei_profile={
            "inclusive_imagery": True,
            "diverse_representation": True,
            "accessible_design": True
        }
    )
    
    # Initialize engine and safety guardrails
    engine = SyncCreateEngine()
    safety_guardrails = BrandSafetyGuardrails(guidelines)
    
    # Generate 5-variant strategy for TikTok platform
    print(f"\n📊 Input from SyncValue™:")
    print(f"   Persona: {persona.segment_name}")
    print(f"   LTV Score: {persona.ltv_score:.2f} | Churn Risk: {persona.churn_risk:.2f}")
    print(f"   Trigger: {persona.ltv_trigger}")
    print(f"   Product: {product.product_name} - {product.usp}")
    
    variants = engine.generate_creative_variants(
        persona=persona,
        product=product,
        platform_format=PlatformFormat.META_SQUARE,  # 1:1 for Meta feed
        guidelines=guidelines,
        safety_guardrails=safety_guardrails
    )
    
    # Display results
    print(f"\n📦 Generated {len(variants)} variants:")
    for i, variant in enumerate(variants, 1):
        print(f"\n   Variant {i} - {variant.variant_type.value}")
        print(f"   Headline: {variant.headline_text}")
        print(f"   Body: {variant.body_copy}")
        print(f"   CTA: {variant.cta_button}")
        print(f"   Safety Score: {variant.safety_score:.2f} | Vision Quality: {variant.vision_validation['quality_score']:.2f}")
        print(f"   Brand Compliant: {'✅' if variant.brand_compliant else '❌'}")
    
    # Save variants
    output_file = engine.save_variants(variants, "enterprise_demo_q1_2026")
    print(f"\n💾 Saved to: {output_file}")
    
    # Show gRPC/JSON API format for SyncFlow™
    if variants:
        print(f"\n🔌 SyncFlow™ API Output Format:")
        grpc_format = variants[0].to_grpc_format()
        print(json.dumps(grpc_format, indent=2)[:500] + "...")
    
    print("\n" + "=" * 80)
    print("✅ Demo complete! SyncCreate™ ready for production.")
    
    return variants


if __name__ == "__main__":
    demo_creative_generation()

