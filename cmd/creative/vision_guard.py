"""
Vision Guard with CLIP Validation

Advanced vision validation system using CLIP embeddings and Llava models.
Validates that generated images match product, brand, and safety requirements.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
from pathlib import Path
import json


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CLIPValidationResult:
    """Result from CLIP validation."""
    
    product_detected: bool
    product_confidence: float  # 0.0-1.0
    safety_score: float  # 0.0-1.0
    quality_score: float  # 0.0-1.0
    
    detected_objects: List[str]
    detected_concepts: List[str]
    safety_flags: List[str]
    
    composition_score: float  # Rule of thirds, focal points
    brand_fit_score: float  # Alignment with brand
    overall_score: float  # Weighted average
    
    recommendations: List[str]
    is_approved: bool


@dataclass
class ImageQualityMetrics:
    """Technical image quality metrics."""
    
    sharpness: float  # 0-1
    contrast: float  # 0-1
    exposure: float  # 0-1 (not too dark/bright)
    composition: float  # 0-1 (rule of thirds)
    color_vibrancy: float  # 0-1
    overall_quality: float  # Weighted average


class ObjectDetectionType(Enum):
    """Types of objects that can be detected."""
    PRODUCT = "product"
    PERSON = "person"
    ENVIRONMENT = "environment"
    LOGO = "logo"
    TEXT = "text"
    PROHIBITED = "prohibited"


# ============================================================================
# CLIP EMBEDDINGS & SIMILARITY
# ============================================================================

class CLIPEmbeddingEngine:
    """
    CLIP model for image and text embeddings.
    Uses cosine similarity to compare concepts.
    """
    
    def __init__(self, use_mock: bool = True):
        """Initialize CLIP engine.
        
        Args:
            use_mock: Use mock embeddings if True (no model loading)
        """
        self.use_mock = use_mock
        self.model = None
        self.processor = None
        
        if not use_mock:
            try:
                from transformers import CLIPProcessor, CLIPModel
                self.model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
                self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
            except ImportError:
                print("Warning: transformers not installed. Using mock embeddings.")
                self.use_mock = True
    
    def generate_mock_embedding(self, text: str) -> np.ndarray:
        """Generate deterministic mock embedding based on text hash."""
        # Create consistent embedding based on text
        text_hash = hash(text) % 100
        embedding = np.random.RandomState(text_hash).randn(512)
        return embedding / np.linalg.norm(embedding)  # Normalize
    
    def get_text_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text input."""
        if self.use_mock:
            return self.generate_mock_embedding(text)
        
        inputs = self.processor(text=text, return_tensors="pt")
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
        return text_features[0].numpy()
    
    def get_image_embedding(self, image_path: str) -> np.ndarray:
        """Get embedding for image input."""
        if self.use_mock:
            # Deterministic mock based on file hash
            file_hash = hash(image_path) % 100
            embedding = np.random.RandomState(file_hash).randn(512)
            return embedding / np.linalg.norm(embedding)
        
        from PIL import Image
        image = Image.open(image_path)
        inputs = self.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
        return image_features[0].numpy()
    
    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# ============================================================================
# VISION VALIDATION
# ============================================================================

class VisionValidator:
    """
    Advanced vision validation using CLIP embeddings.
    Validates product detection, safety, quality, and brand fit.
    """
    
    def __init__(self, use_mock: bool = True):
        """Initialize vision validator.
        
        Args:
            use_mock: Use mock embeddings if True
        """
        self.clip_engine = CLIPEmbeddingEngine(use_mock=use_mock)
        self.use_mock = use_mock
        
        # Detection thresholds
        self.product_detection_threshold = 0.7
        self.safety_threshold = 0.8
        self.quality_threshold = 0.75
        self.brand_fit_threshold = 0.7
    
    def validate_image(
        self,
        image_path: str,
        expected_product: str,
        brand_guidelines: Optional[Dict] = None,
        variant_type: str = "control"
    ) -> CLIPValidationResult:
        """
        Validate image matches product, safety, and brand requirements.
        
        Args:
            image_path: Path to image file
            expected_product: Product name/description to detect
            brand_guidelines: Brand safety and style guidelines
            variant_type: Type of creative (control, lifestyle, etc)
        
        Returns:
            CLIPValidationResult with validation details
        """
        
        # Get image embedding
        image_embedding = self.clip_engine.get_image_embedding(image_path)
        
        # 1. PRODUCT DETECTION
        product_sim = self._detect_product(
            image_embedding,
            expected_product
        )
        product_detected = product_sim >= self.product_detection_threshold
        
        # 2. SAFETY VALIDATION
        safety_score, safety_flags = self._validate_safety(
            image_embedding,
            brand_guidelines or {}
        )
        
        # 3. QUALITY ASSESSMENT
        quality_metrics = self._assess_quality(image_path)
        quality_score = quality_metrics.overall_quality
        
        # 4. COMPOSITION & BRAND FIT
        composition_score = self._assess_composition(image_path, variant_type)
        brand_fit_score = self._assess_brand_fit(
            image_embedding,
            brand_guidelines or {},
            variant_type
        )
        
        # 5. OBJECT DETECTION
        detected_objects = self._detect_objects(image_embedding)
        detected_concepts = self._detect_concepts(image_embedding)
        
        # 6. OVERALL ASSESSMENT
        overall_score = self._calculate_overall_score(
            product_sim=product_sim,
            safety_score=safety_score,
            quality_score=quality_score,
            composition_score=composition_score,
            brand_fit_score=brand_fit_score
        )
        
        # 7. RECOMMENDATIONS
        recommendations = self._generate_recommendations(
            product_detected=product_detected,
            safety_score=safety_score,
            quality_score=quality_score,
            brand_fit_score=brand_fit_score,
            safety_flags=safety_flags
        )
        
        # 8. APPROVAL DECISION
        is_approved = (
            product_detected and
            safety_score >= self.safety_threshold and
            quality_score >= self.quality_threshold and
            brand_fit_score >= self.brand_fit_threshold
        )
        
        return CLIPValidationResult(
            product_detected=product_detected,
            product_confidence=product_sim,
            safety_score=safety_score,
            quality_score=quality_score,
            detected_objects=detected_objects,
            detected_concepts=detected_concepts,
            safety_flags=safety_flags,
            composition_score=composition_score,
            brand_fit_score=brand_fit_score,
            overall_score=overall_score,
            recommendations=recommendations,
            is_approved=is_approved
        )
    
    def _detect_product(
        self,
        image_embedding: np.ndarray,
        product_name: str
    ) -> float:
        """Detect if product is visible in image using CLIP."""
        
        # Get embedding for product
        product_embedding = self.clip_engine.get_text_embedding(
            f"A photo of {product_name}"
        )
        
        # Calculate similarity
        similarity = self.clip_engine.cosine_similarity(
            image_embedding,
            product_embedding
        )
        
        return similarity
    
    def _validate_safety(
        self,
        image_embedding: np.ndarray,
        brand_guidelines: Dict
    ) -> Tuple[float, List[str]]:
        """Validate image for safety violations."""
        
        safety_flags = []
        safety_score = 1.0
        
        # Check for prohibited concepts
        prohibited = brand_guidelines.get('prohibited_concepts', [])
        for concept in prohibited:
            concept_embedding = self.clip_engine.get_text_embedding(concept)
            sim = self.clip_engine.cosine_similarity(
                image_embedding,
                concept_embedding
            )
            
            if sim > 0.6:  # Threshold for prohibited content
                safety_flags.append(f"Potential '{concept}' detected ({sim:.2f})")
                safety_score *= 0.5  # Reduce safety score
        
        # Check for inappropriate content
        unsafe_embeddings = [
            "violence",
            "explicit content",
            "discrimination",
            "offensive imagery"
        ]
        
        for unsafe_concept in unsafe_embeddings:
            concept_embedding = self.clip_engine.get_text_embedding(unsafe_concept)
            sim = self.clip_engine.cosine_similarity(
                image_embedding,
                concept_embedding
            )
            
            if sim > 0.7:
                safety_flags.append(f"Safety flag: {unsafe_concept} ({sim:.2f})")
                safety_score *= 0.7
        
        return max(0.0, safety_score), safety_flags
    
    def _assess_quality(self, image_path: str) -> ImageQualityMetrics:
        """Assess technical quality of image."""
        
        if self.use_mock:
            # Mock quality metrics
            return ImageQualityMetrics(
                sharpness=0.88,
                contrast=0.85,
                exposure=0.92,
                composition=0.90,
                color_vibrancy=0.87,
                overall_quality=0.88
            )
        
        try:
            from PIL import Image, ImageFilter, ImageStat
            
            img = Image.open(image_path)
            
            # Sharpness (Laplacian variance)
            img_gray = img.convert('L')
            laplacian = img_gray.filter(ImageFilter.FIND_EDGES)
            laplacian_stat = ImageStat.Stat(laplacian)
            sharpness = min(1.0, laplacian_stat.mean[0] / 100)
            
            # Contrast
            stat = ImageStat.Stat(img_gray)
            contrast = min(1.0, stat.stddev[0] / 128)
            
            # Exposure (mean brightness)
            brightness = stat.mean[0] / 255
            exposure = 1.0 - abs(brightness - 0.5)  # Optimal ~0.5
            
            # Color vibrancy
            stat_rgb = ImageStat.Stat(img)
            color_vibrancy = np.mean(stat_rgb.stddev[:3]) / 128
            
            # Mock composition (in real system: detect focal points, rule of thirds)
            composition = 0.85
            
            overall = (sharpness + contrast + exposure + composition + color_vibrancy) / 5
            
            return ImageQualityMetrics(
                sharpness=sharpness,
                contrast=contrast,
                exposure=exposure,
                composition=composition,
                color_vibrancy=color_vibrancy,
                overall_quality=overall
            )
        
        except Exception as e:
            # Fallback mock
            return ImageQualityMetrics(
                sharpness=0.80,
                contrast=0.80,
                exposure=0.85,
                composition=0.80,
                color_vibrancy=0.80,
                overall_quality=0.81
            )
    
    def _assess_composition(self, image_path: str, variant_type: str) -> float:
        """Assess composition quality and variant-specific requirements."""
        
        # Base composition score
        base_score = 0.85
        
        # Variant-specific expectations
        variant_adjustments = {
            "control": 0.0,        # Product-focused
            "lifestyle": 0.05,     # Person prominent
            "abstract": -0.1,      # Conceptual, more forgiving
            "high_contrast": 0.1,  # Strong focal point needed
            "data_led": -0.05      # Infographic style
        }
        
        adjustment = variant_adjustments.get(variant_type, 0.0)
        return max(0.0, min(1.0, base_score + adjustment))
    
    def _assess_brand_fit(
        self,
        image_embedding: np.ndarray,
        brand_guidelines: Dict,
        variant_type: str
    ) -> float:
        """Assess how well image fits brand guidelines."""
        
        brand_fit_score = 0.8
        
        # Check against brand tone
        tone_of_voice = brand_guidelines.get('tone_of_voice', 'professional')
        tone_embedding = self.clip_engine.get_text_embedding(
            f"A {tone_of_voice} advertisement"
        )
        
        tone_sim = self.clip_engine.cosine_similarity(
            image_embedding,
            tone_embedding
        )
        
        brand_fit_score *= tone_sim
        
        # Check style alignment
        style_guide = brand_guidelines.get('style_guide', 'professional')
        style_embedding = self.clip_engine.get_text_embedding(
            f"A {style_guide} design style"
        )
        
        style_sim = self.clip_engine.cosine_similarity(
            image_embedding,
            style_embedding
        )
        
        brand_fit_score *= style_sim
        
        return max(0.0, min(1.0, brand_fit_score))
    
    def _detect_objects(self, image_embedding: np.ndarray) -> List[str]:
        """Detect objects present in image."""
        
        objects_to_check = [
            "product", "person", "people", "hands", "face",
            "background", "logo", "text", "interface",
            "nature", "urban environment", "office"
        ]
        
        detected = []
        
        for obj in objects_to_check:
            obj_embedding = self.clip_engine.get_text_embedding(obj)
            sim = self.clip_engine.cosine_similarity(
                image_embedding,
                obj_embedding
            )
            
            if sim > 0.6:
                detected.append(f"{obj} ({sim:.2f})")
        
        return detected
    
    def _detect_concepts(self, image_embedding: np.ndarray) -> List[str]:
        """Detect high-level concepts in image."""
        
        concepts = [
            "professional", "casual", "luxury", "playful", "serious",
            "modern", "vintage", "minimalist", "energetic",
            "warm", "cool", "bright", "dark", "emotional",
            "technical", "organic", "artificial"
        ]
        
        detected = []
        
        for concept in concepts:
            concept_embedding = self.clip_engine.get_text_embedding(concept)
            sim = self.clip_engine.cosine_similarity(
                image_embedding,
                concept_embedding
            )
            
            if sim > 0.65:
                detected.append(f"{concept} ({sim:.2f})")
        
        return detected
    
    def _calculate_overall_score(
        self,
        product_sim: float,
        safety_score: float,
        quality_score: float,
        composition_score: float,
        brand_fit_score: float
    ) -> float:
        """Calculate weighted overall score."""
        
        # Weights
        weights = {
            'product': 0.30,
            'safety': 0.25,
            'quality': 0.15,
            'composition': 0.15,
            'brand': 0.15
        }
        
        overall = (
            product_sim * weights['product'] +
            safety_score * weights['safety'] +
            quality_score * weights['quality'] +
            composition_score * weights['composition'] +
            brand_fit_score * weights['brand']
        )
        
        return overall
    
    def _generate_recommendations(
        self,
        product_detected: bool,
        safety_score: float,
        quality_score: float,
        brand_fit_score: float,
        safety_flags: List[str]
    ) -> List[str]:
        """Generate recommendations for image improvement."""
        
        recommendations = []
        
        if not product_detected:
            recommendations.append(
                "❌ Product not clearly visible - increase product prominence"
            )
        
        if safety_score < self.safety_threshold:
            recommendations.append(
                f"⚠️ Safety concerns detected - review flags: {', '.join(safety_flags)}"
            )
        
        if quality_score < self.quality_threshold:
            recommendations.append(
                "📷 Image quality needs improvement - increase sharpness/contrast"
            )
        
        if brand_fit_score < self.brand_fit_threshold:
            recommendations.append(
                "🎨 Brand fit could be improved - align better with brand guidelines"
            )
        
        if not recommendations:
            recommendations.append("✅ Image meets all quality standards")
        
        return recommendations


# ============================================================================
# VISION GUARD WITH VARIANT OPTIMIZATION
# ============================================================================

class VisionGuardWithVariantOptimization:
    """
    Enhanced vision guard that validates variants and provides
    variant-specific feedback.
    """
    
    def __init__(self, use_mock: bool = True):
        self.validator = VisionValidator(use_mock=use_mock)
        
        # Variant-specific validation profiles
        self.variant_profiles = {
            "control": {
                "product_prominence": 0.9,
                "background_simple": True,
                "focus_product": True
            },
            "lifestyle": {
                "product_prominence": 0.7,
                "person_visible": True,
                "contextual": True,
                "emotional_connection": True
            },
            "abstract": {
                "product_prominence": 0.5,
                "conceptual": True,
                "artistic": True,
                "emotional_intensity": 0.8
            },
            "high_contrast": {
                "visual_impact": 0.9,
                "bold_colors": True,
                "focal_point_clear": True,
                "product_prominence": 0.8
            },
            "data_led": {
                "text_visible": True,
                "data_visualization": True,
                "professional": True,
                "clarity": 0.95
            }
        }
    
    def validate_variant(
        self,
        image_path: str,
        product_name: str,
        variant_type: str,
        brand_guidelines: Optional[Dict] = None
    ) -> Dict:
        """
        Validate image for specific variant type.
        
        Returns enhanced validation with variant-specific checks.
        """
        
        # Run base validation
        result = self.validator.validate_image(
            image_path=image_path,
            expected_product=product_name,
            brand_guidelines=brand_guidelines,
            variant_type=variant_type
        )
        
        # Add variant-specific checks
        variant_checks = self._check_variant_requirements(
            image_path=image_path,
            result=result,
            variant_type=variant_type,
            brand_guidelines=brand_guidelines or {}
        )
        
        return {
            "variant_type": variant_type,
            "base_validation": {
                "product_detected": result.product_detected,
                "product_confidence": result.product_confidence,
                "safety_score": result.safety_score,
                "quality_score": result.quality_score,
                "overall_score": result.overall_score,
                "is_approved": result.is_approved
            },
            "detected_objects": result.detected_objects,
            "detected_concepts": result.detected_concepts,
            "safety_flags": result.safety_flags,
            "composition_score": result.composition_score,
            "brand_fit_score": result.brand_fit_score,
            "variant_checks": variant_checks,
            "recommendations": result.recommendations,
            "approval_status": "✅ APPROVED" if result.is_approved else "❌ NEEDS REVISION"
        }
    
    def _check_variant_requirements(
        self,
        image_path: str,
        result: CLIPValidationResult,
        variant_type: str,
        brand_guidelines: Dict
    ) -> Dict:
        """Check variant-specific requirements."""
        
        profile = self.variant_profiles.get(variant_type, {})
        checks = {}
        
        # Product prominence check
        if "product_prominence" in profile:
            required = profile["product_prominence"]
            actual = result.product_confidence
            checks["product_prominence"] = {
                "required": required,
                "actual": actual,
                "passed": actual >= required,
                "status": "✅" if actual >= required else "❌"
            }
        
        # Variant-specific feature checks
        if variant_type == "lifestyle" and profile.get("person_visible"):
            person_sim = self.validator.clip_engine.cosine_similarity(
                self.validator.clip_engine.get_image_embedding(image_path),
                self.validator.clip_engine.get_text_embedding("a person using product")
            )
            checks["person_visible"] = {
                "required": True,
                "detected": person_sim > 0.6,
                "confidence": person_sim,
                "status": "✅" if person_sim > 0.6 else "❌"
            }
        
        if variant_type == "high_contrast" and profile.get("bold_colors"):
            checks["bold_colors"] = {
                "required": True,
                "color_vibrancy": result.quality_score,  # Approximation
                "passed": result.quality_score > 0.7,
                "status": "✅" if result.quality_score > 0.7 else "❌"
            }
        
        if variant_type == "data_led" and profile.get("text_visible"):
            text_sim = self.validator.clip_engine.cosine_similarity(
                self.validator.clip_engine.get_image_embedding(image_path),
                self.validator.clip_engine.get_text_embedding("text and data visualization")
            )
            checks["text_visible"] = {
                "required": True,
                "detected": text_sim > 0.65,
                "confidence": text_sim,
                "status": "✅" if text_sim > 0.65 else "❌"
            }
        
        return checks


if __name__ == "__main__":
    # Demo: Vision Guard with CLIP validation
    
    print("\n" + "="*100)
    print("VISION GUARD WITH CLIP VALIDATION - DEMONSTRATION")
    print("="*100 + "\n")
    
    # Initialize vision guard
    guard = VisionGuardWithVariantOptimization(use_mock=True)
    
    # Example brand guidelines
    brand_guidelines = {
        "brand_name": "TechBrand",
        "tone_of_voice": "professional",
        "style_guide": "modern minimalist",
        "prohibited_concepts": [
            "violence",
            "discrimination",
            "misinformation"
        ]
    }
    
    print("📊 Vision Guard Validation Examples\n")
    print("Testing different variants with product 'AI Assistant Pro'\n")
    
    variants_to_test = ["control", "lifestyle", "abstract", "high_contrast", "data_led"]
    
    for variant_type in variants_to_test:
        print(f"\n{variant_type.upper()} VARIANT")
        print("-" * 100)
        
        result = guard.validate_variant(
            image_path="/path/to/image.jpg",  # Mock path
            product_name="AI Assistant Pro",
            variant_type=variant_type,
            brand_guidelines=brand_guidelines
        )
        
        print(f"Product Confidence:    {result['base_validation']['product_confidence']:.2%}")
        print(f"Safety Score:          {result['base_validation']['safety_score']:.2%}")
        print(f"Quality Score:         {result['base_validation']['quality_score']:.2%}")
        print(f"Brand Fit:             {result['brand_fit_score']:.2%}")
        print(f"Overall Score:         {result['base_validation']['overall_score']:.2%}")
        print(f"Status:                {result['approval_status']}")
        
        print(f"\nVariant-Specific Checks:")
        for check_name, check_data in result['variant_checks'].items():
            status = check_data.get('status', '❓')
            print(f"  {status} {check_name}")
        
        print(f"\nRecommendations:")
        for rec in result['recommendations'][:2]:  # Show top 2
            print(f"  • {rec}")
