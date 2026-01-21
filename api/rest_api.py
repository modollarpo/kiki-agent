"""
JSON REST API Gateway for Variant Strategy System
Provides REST/JSON endpoints that wrap gRPC services
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmd.creative.variant_strategy import (
    VariantPortfolio,
    VARIANT_STRATEGY_LIBRARY,
    get_strategic_recommendations,
)
from cmd.creative.variant_testing import (
    calculate_sample_size,
    analyze_multi_variant_experiment,
)
from cmd.creative.vision_guard import VisionGuardWithVariantOptimization
from cmd.creative.vision_guard_integration import QualityBasedRanking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Variant Strategy API",
    description="REST API for variant strategy management and vision guard validation",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class VariantCharacteristicsModel(BaseModel):
    """Variant characteristics"""
    name: str
    description: str
    visual_focus: str
    messaging_style: str
    best_for: List[str]
    platform_fit: List[str]
    ctr_lift_potential: float
    conversion_lift: float
    engagement_lift: float
    average_cpv: str
    optimal_duration_seconds: Optional[int]
    color_intensity: str
    design_complexity: str


class VariantInPortfolioModel(BaseModel):
    """Variant in portfolio"""
    variant_id: str
    variant_type: str
    name: str
    budget_allocation: float
    current_performance: float
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    conversions: int = 0
    conversion_rate: float = 0.0
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""


class PortfolioModel(BaseModel):
    """Portfolio model"""
    portfolio_id: str
    name: str
    brand: str
    product: str
    total_budget: float
    variants: List[VariantInPortfolioModel] = []
    status: str = "active"
    total_impressions: float = 0.0
    total_clicks: float = 0.0
    portfolio_ctr: float = 0.0
    total_conversions: float = 0.0
    portfolio_conversion_rate: float = 0.0
    created_at: str
    updated_at: str
    performance_metrics: Dict[str, float] = {}


class CreatePortfolioRequest(BaseModel):
    """Request to create portfolio"""
    name: str
    brand: str
    product: str
    total_budget: float
    variant_types: Optional[List[str]] = None
    variant_budgets: Optional[Dict[str, float]] = None


class PortfolioResponseModel(BaseModel):
    """Portfolio response"""
    success: bool
    message: str
    portfolio: Optional[PortfolioModel] = None


class SampleSizeRequest(BaseModel):
    """Sample size calculation request"""
    baseline_rate: float = Field(..., description="Baseline conversion rate")
    minimum_detectable_effect: float = Field(..., description="Minimum detectable effect")
    alpha: float = Field(0.05, description="Significance level")
    power: float = Field(0.80, description="Statistical power")


class SampleSizeResponse(BaseModel):
    """Sample size response"""
    sample_size_per_variant: int
    total_sample_size: int
    explanation: str


class VariantRecommendationModel(BaseModel):
    """Variant recommendation"""
    variant_type: str
    variant_name: str
    recommendation_score: float
    reasoning: str
    characteristics: VariantCharacteristicsModel


class VariantRecommendationRequest(BaseModel):
    """Variant recommendation request"""
    campaign_type: str = Field(..., description="Type of campaign: awareness, consideration, conversion, retention")
    target_audience: str = Field(..., description="Target audience")
    platform: str = Field(..., description="Ad platform: meta, tiktok, google, linkedin, etc")
    goal: Optional[str] = None


class VariantRecommendationResponse(BaseModel):
    """Variant recommendation response"""
    recommendations: List[VariantRecommendationModel]
    explanation: str


class CLIPValidationResultModel(BaseModel):
    """CLIP validation result"""
    product_confidence: float
    safety_score: float
    quality_score: float
    brand_fit: float
    composition: float
    overall_score: float
    is_approved: bool
    recommendations: List[str]
    variant_checks: Dict[str, bool] = {}
    detected_objects: List[str] = []
    detected_concepts: List[str] = []
    safety_flags: List[str] = []


class ImageValidationRequest(BaseModel):
    """Image validation request"""
    portfolio_id: Optional[str] = None
    variant_type: str
    image_path: str
    use_mock: bool = True


class ImageValidationResponse(BaseModel):
    """Image validation response"""
    success: bool
    message: str
    validation: Optional[CLIPValidationResultModel] = None


class PortfolioValidationRequest(BaseModel):
    """Portfolio validation request"""
    portfolio_id: str
    variant_image_paths: Dict[str, str]
    use_mock: bool = True


class VariantImageQualityModel(BaseModel):
    """Variant image quality result"""
    variant: str
    validation: CLIPValidationResultModel
    quality_tier: str


class PortfolioValidationResponse(BaseModel):
    """Portfolio validation response"""
    success: bool
    message: str
    variant_results: List[VariantImageQualityModel] = []
    quality_scores: Dict[str, float] = {}


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

portfolios: Dict[str, VariantPortfolio] = {}
insights: Dict[str, List[Dict]] = {}
vision_guard = VisionGuardWithVariantOptimization()
quality_ranker = QualityBasedRanking()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def portfolio_to_model(portfolio: VariantPortfolio) -> PortfolioModel:
    """Convert VariantPortfolio to Pydantic model"""
    variants_data = []
    for variant in portfolio.variants:
        variants_data.append(VariantInPortfolioModel(
            variant_id=variant.get('id', ''),
            variant_type=variant.get('type', ''),
            name=variant.get('name', ''),
            budget_allocation=variant.get('budget', 0.0),
            current_performance=variant.get('performance', 0.0),
            impressions=int(variant.get('impressions', 0)),
            clicks=int(variant.get('clicks', 0)),
            ctr=variant.get('ctr', 0.0),
            conversions=int(variant.get('conversions', 0)),
            conversion_rate=variant.get('conversion_rate', 0.0),
            status=variant.get('status', 'active'),
            created_at=variant.get('created_at', ''),
            updated_at=variant.get('updated_at', ''),
        ))
    
    return PortfolioModel(
        portfolio_id=portfolio.portfolio_id,
        name=portfolio.name,
        brand=portfolio.brand,
        product=portfolio.product,
        total_budget=portfolio.total_budget,
        variants=variants_data,
        status=portfolio.status,
        total_impressions=portfolio.total_impressions,
        total_clicks=portfolio.total_clicks,
        portfolio_ctr=portfolio.total_clicks / max(portfolio.total_impressions, 1),
        total_conversions=portfolio.total_conversions,
        portfolio_conversion_rate=portfolio.total_conversions / max(portfolio.total_clicks, 1),
        created_at=portfolio.created_at.isoformat(),
        updated_at=portfolio.updated_at.isoformat(),
    )


def characteristics_to_model(chars) -> VariantCharacteristicsModel:
    """Convert VariantCharacteristics to Pydantic model"""
    return VariantCharacteristicsModel(
        name=chars.name,
        description=chars.description,
        visual_focus=chars.visual_focus,
        messaging_style=chars.messaging_style,
        best_for=list(chars.best_for),
        platform_fit=list(chars.platform_fit),
        ctr_lift_potential=chars.ctr_lift_potential,
        conversion_lift=chars.conversion_lift,
        engagement_lift=chars.engagement_lift,
        average_cpv=chars.average_cpv,
        optimal_duration_seconds=chars.optimal_duration_seconds,
        color_intensity=chars.color_intensity,
        design_complexity=chars.design_complexity,
    )


# ============================================================================
# API ENDPOINTS - HEALTH & INFO
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Variant Strategy API"
    }


@app.get("/info")
async def service_info():
    """Service information"""
    return {
        "service": "Variant Strategy & Vision Guard API",
        "version": "1.0.0",
        "description": "REST API for creative variant management and CLIP validation",
        "endpoints": {
            "portfolios": "/api/portfolios",
            "variants": "/api/variants",
            "recommendations": "/api/recommendations",
            "validation": "/api/validation",
            "testing": "/api/testing",
        }
    }


# ============================================================================
# API ENDPOINTS - PORTFOLIO MANAGEMENT
# ============================================================================

@app.post("/api/portfolios", response_model=PortfolioResponseModel)
async def create_portfolio(request: CreatePortfolioRequest):
    """Create a new variant portfolio"""
    try:
        portfolio = VariantPortfolio(
            name=request.name,
            brand=request.brand,
            product=request.product,
            total_budget=request.total_budget,
        )
        
        # Add variants
        if request.variant_budgets:
            for variant_type, budget in request.variant_budgets.items():
                portfolio.add_variant(variant_type, budget)
        elif request.variant_types:
            per_variant = request.total_budget / len(request.variant_types)
            for variant_type in request.variant_types:
                portfolio.add_variant(variant_type, per_variant)
        
        portfolios[portfolio.portfolio_id] = portfolio
        
        logger.info(f"Created portfolio {portfolio.portfolio_id}")
        return PortfolioResponseModel(
            success=True,
            message=f"Portfolio created successfully",
            portfolio=portfolio_to_model(portfolio)
        )
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolios/{portfolio_id}", response_model=PortfolioResponseModel)
async def get_portfolio(portfolio_id: str):
    """Get portfolio by ID"""
    if portfolio_id not in portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = portfolios[portfolio_id]
    return PortfolioResponseModel(
        success=True,
        message="Portfolio retrieved",
        portfolio=portfolio_to_model(portfolio)
    )


@app.get("/api/portfolios")
async def list_portfolios(brand: Optional[str] = None, limit: int = 100, offset: int = 0):
    """List portfolios with optional filtering"""
    portfolio_list = list(portfolios.values())
    
    if brand:
        portfolio_list = [p for p in portfolio_list if p.brand == brand]
    
    paginated = portfolio_list[offset:offset + limit]
    
    return {
        "success": True,
        "portfolios": [portfolio_to_model(p) for p in paginated],
        "total": len(portfolio_list),
        "limit": limit,
        "offset": offset,
    }


# ============================================================================
# API ENDPOINTS - VARIANT OPERATIONS
# ============================================================================

@app.get("/api/variants/library")
async def get_variant_library(variant_type: Optional[str] = None):
    """Get variant library"""
    if variant_type:
        if variant_type not in VARIANT_STRATEGY_LIBRARY:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        return {
            "success": True,
            "variants": {
                variant_type: characteristics_to_model(VARIANT_STRATEGY_LIBRARY[variant_type]).dict()
            }
        }
    
    return {
        "success": True,
        "variants": {
            key: characteristics_to_model(chars).dict()
            for key, chars in VARIANT_STRATEGY_LIBRARY.items()
        }
    }


@app.post("/api/variants/recommendations", response_model=VariantRecommendationResponse)
async def get_variant_recommendations(request: VariantRecommendationRequest):
    """Get variant recommendations for a campaign"""
    try:
        recommendations = get_strategic_recommendations(
            campaign_type=request.campaign_type,
            target_audience=request.target_audience,
            platform=request.platform,
        )
        
        recs = []
        for variant_type, score, reasoning in recommendations:
            recs.append(VariantRecommendationModel(
                variant_type=variant_type,
                variant_name=VARIANT_STRATEGY_LIBRARY[variant_type].name,
                recommendation_score=score,
                reasoning=reasoning,
                characteristics=characteristics_to_model(VARIANT_STRATEGY_LIBRARY[variant_type])
            ))
        
        return VariantRecommendationResponse(
            recommendations=recs,
            explanation=f"Recommendations for {request.campaign_type} campaign"
        )
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# API ENDPOINTS - TESTING & ANALYSIS
# ============================================================================

@app.post("/api/testing/sample-size", response_model=SampleSizeResponse)
async def calculate_sample_size_endpoint(request: SampleSizeRequest):
    """Calculate required sample size for experiment"""
    try:
        sample_size = calculate_sample_size(
            baseline_rate=request.baseline_rate,
            mde=request.minimum_detectable_effect,
            alpha=request.alpha,
            power=request.power,
        )
        
        return SampleSizeResponse(
            sample_size_per_variant=sample_size,
            total_sample_size=sample_size * 5,
            explanation=f"Required {sample_size} samples per variant for statistical significance"
        )
    except Exception as e:
        logger.error(f"Error calculating sample size: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/testing/analyze")
async def analyze_experiment(
    control_variant: str,
    test_variants: List[str],
    variant_conversions: Dict[str, int],
    variant_exposures: Dict[str, int],
):
    """Analyze multi-variant experiment results"""
    try:
        results = analyze_multi_variant_experiment(
            control=control_variant,
            test_variants=test_variants,
            conversions=variant_conversions,
            exposures=variant_exposures,
        )
        
        winner = None
        winner_lift = 0.0
        
        for result in results:
            if result.get('is_significant', False) and result['lift'] > winner_lift:
                winner = result['variant']
                winner_lift = result['lift']
        
        return {
            "success": True,
            "analysis": results,
            "winner": winner or "inconclusive",
            "winner_lift": winner_lift,
        }
    except Exception as e:
        logger.error(f"Error analyzing experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# API ENDPOINTS - VISION GUARD VALIDATION
# ============================================================================

@app.post("/api/validation/image", response_model=ImageValidationResponse)
async def validate_image(request: ImageValidationRequest):
    """Validate a single image"""
    try:
        validation = vision_guard.validate_variant(
            image_path=request.image_path,
            variant_type=request.variant_type,
            use_mock=request.use_mock,
        )
        
        return ImageValidationResponse(
            success=True,
            message="Image validated successfully",
            validation=CLIPValidationResultModel(
                product_confidence=validation.product_confidence,
                safety_score=validation.safety_score,
                quality_score=validation.quality_score,
                brand_fit=validation.brand_fit,
                composition=validation.composition,
                overall_score=validation.overall_score,
                is_approved=validation.is_approved,
                recommendations=validation.recommendations,
                variant_checks=validation.variant_checks,
                detected_objects=validation.detected_objects,
                detected_concepts=validation.detected_concepts,
                safety_flags=validation.safety_flags,
            )
        )
    except Exception as e:
        logger.error(f"Error validating image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validation/portfolio", response_model=PortfolioValidationResponse)
async def validate_portfolio(request: PortfolioValidationRequest):
    """Validate all images in a portfolio"""
    try:
        results = []
        quality_scores = {}
        
        for variant_type, image_path in request.variant_image_paths.items():
            validation = vision_guard.validate_variant(
                image_path=image_path,
                variant_type=variant_type,
                use_mock=request.use_mock,
            )
            
            quality_tier = quality_ranker.get_quality_tier(validation.overall_score)
            quality_scores[variant_type] = validation.overall_score
            
            results.append(VariantImageQualityModel(
                variant=variant_type,
                validation=CLIPValidationResultModel(
                    product_confidence=validation.product_confidence,
                    safety_score=validation.safety_score,
                    quality_score=validation.quality_score,
                    brand_fit=validation.brand_fit,
                    composition=validation.composition,
                    overall_score=validation.overall_score,
                    is_approved=validation.is_approved,
                    recommendations=validation.recommendations,
                    variant_checks=validation.variant_checks,
                    detected_objects=validation.detected_objects,
                    detected_concepts=validation.detected_concepts,
                    safety_flags=validation.safety_flags,
                ),
                quality_tier=quality_tier,
            ))
        
        return PortfolioValidationResponse(
            success=True,
            message="Portfolio validated successfully",
            variant_results=results,
            quality_scores=quality_scores,
        )
    except Exception as e:
        logger.error(f"Error validating portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/validation/quality-report/{portfolio_id}")
async def get_quality_report(portfolio_id: str):
    """Get quality report for portfolio"""
    if portfolio_id not in portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "success": True,
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolios[portfolio_id].name,
        "message": "Quality report generated"
    }


# ============================================================================
# API ENDPOINTS - INSIGHTS & OPTIMIZATION
# ============================================================================

@app.post("/api/insights")
async def capture_insight(portfolio_id: str, insight_type: str, variant: str, description: str):
    """Capture a campaign insight"""
    try:
        if portfolio_id not in insights:
            insights[portfolio_id] = []
        
        insight = {
            'insight_id': f"insight_{len(insights[portfolio_id])}",
            'portfolio_id': portfolio_id,
            'variant': variant,
            'type': insight_type,
            'description': description,
            'created_at': datetime.now().isoformat(),
        }
        
        insights[portfolio_id].append(insight)
        
        return {
            "success": True,
            "insight_id": insight['insight_id'],
            "message": "Insight captured"
        }
    except Exception as e:
        logger.error(f"Error capturing insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/{portfolio_id}")
async def get_insights(portfolio_id: str, variant: Optional[str] = None, limit: int = 100):
    """Get insights for a portfolio"""
    portfolio_insights = insights.get(portfolio_id, [])
    
    if variant:
        portfolio_insights = [i for i in portfolio_insights if i.get('variant') == variant]
    
    return {
        "success": True,
        "portfolio_id": portfolio_id,
        "insights": portfolio_insights[:limit],
        "total": len(portfolio_insights),
    }


# ============================================================================
# OPENAPI SCHEMA
# ============================================================================

@app.get("/api/docs/openapi.json")
async def get_openapi_schema():
    """Get OpenAPI schema"""
    return app.openapi()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
