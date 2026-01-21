"""
gRPC Server Implementation for Variant Strategy System
Provides gRPC endpoints for portfolio management, testing, and optimization
"""

import grpc
from concurrent import futures
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmd.creative.variant_strategy import (
    VariantPortfolio,
    VariantCharacteristics,
    VARIANT_STRATEGY_LIBRARY,
    get_strategic_recommendations,
)
from cmd.creative.variant_testing import (
    MultiVariantExperiment,
    calculate_sample_size,
    analyze_multi_variant_experiment,
)
from cmd.creative.variant_integration import (
    PortfolioOptimizer,
    VariantSequencer,
)
from cmd.creative.vision_guard import VisionGuardWithVariantOptimization
from cmd.creative.vision_guard_integration import VariantImageValidator, QualityBasedRanking

# Import generated protobuf code
try:
    from api.generated.variant_strategy_pb2 import (
        PortfolioResponse, Portfolio, VariantInPortfolio,
        VariantLibraryResponse, VariantCharacteristics as ProtoVariantCharacteristics,
        VariantRecommendationResponse, VariantRecommendation,
        SampleSizeResponse, ExperimentResponse, ExperimentAnalysisResponse, ExperimentAnalysis,
        OptimizationResponse, OptimizationRecommendation,
        InsightResponse, GetInsightsResponse, Insight, LearningResponse,
        BudgetAllocationResponse, BudgetAllocation,
        DeploymentStrategyResponse, DeploymentPhase,
        ImageValidationResponse, CLIPValidationResult,
        PortfolioValidationResponse, VariantImageQualityResult,
        QualityReportResponse, DeploymentRecommendationResponse, DeploymentRecommendation,
    )
    from api.generated.variant_strategy_pb2_grpc import (
        VariantStrategyServiceServicer, VariantGuardServiceServicer,
        add_VariantStrategyServiceServicer_to_server,
        add_VariantGuardServiceServicer_to_server,
    )
except ImportError as e:
    print(f"Warning: Could not import generated protobuf code: {e}")
    print("Run: python -m grpc_tools.protoc -I proto/ --python_out=api/generated --pyi_out=api/generated --grpc_python_out=api/generated proto/variant_strategy.proto")
    raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# VARIANT STRATEGY SERVICE IMPLEMENTATION
# ============================================================================

class VariantStrategyServiceImpl(VariantStrategyServiceServicer):
    """Implementation of VariantStrategyService"""
    
    def __init__(self):
        self.portfolios: Dict[str, VariantPortfolio] = {}
        self.insights: Dict[str, List[Dict]] = {}
        self.experiments: Dict[str, MultiVariantExperiment] = {}
    
    # Portfolio Management
    def CreatePortfolio(self, request, context):
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
                # Equal allocation if no specific budgets
                per_variant = request.total_budget / len(request.variant_types)
                for variant_type in request.variant_types:
                    portfolio.add_variant(variant_type, per_variant)
            
            self.portfolios[portfolio.portfolio_id] = portfolio
            
            return PortfolioResponse(
                success=True,
                message=f"Portfolio {portfolio.portfolio_id} created successfully",
                portfolio=self._portfolio_to_proto(portfolio)
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return PortfolioResponse(success=False, message=str(e))
    
    def GetPortfolio(self, request, context):
        """Get portfolio by ID"""
        try:
            if request.portfolio_id not in self.portfolios:
                context.set_details(f"Portfolio {request.portfolio_id} not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return PortfolioResponse(success=False, message="Portfolio not found")
            
            portfolio = self.portfolios[request.portfolio_id]
            return PortfolioResponse(
                success=True,
                message="Portfolio retrieved",
                portfolio=self._portfolio_to_proto(portfolio)
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return PortfolioResponse(success=False, message=str(e))
    
    def ListPortfolios(self, request, context):
        """List all portfolios with optional filtering"""
        try:
            portfolios = list(self.portfolios.values())
            
            if request.brand:
                portfolios = [p for p in portfolios if p.brand == request.brand]
            
            # Apply pagination
            offset = request.offset or 0
            limit = request.limit or 100
            paginated = portfolios[offset:offset + limit]
            
            from api.generated.variant_strategy_pb2 import ListPortfoliosResponse
            return ListPortfoliosResponse(
                portfolios=[self._portfolio_to_proto(p) for p in paginated],
                total=len(portfolios)
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            from api.generated.variant_strategy_pb2 import ListPortfoliosResponse
            return ListPortfoliosResponse(total=0)
    
    def UpdatePortfolio(self, request, context):
        """Update portfolio"""
        try:
            if request.portfolio_id not in self.portfolios:
                context.set_details("Portfolio not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return PortfolioResponse(success=False, message="Portfolio not found")
            
            portfolio = self.portfolios[request.portfolio_id]
            
            if request.name:
                portfolio.name = request.name
            if request.total_budget:
                portfolio.total_budget = request.total_budget
            if request.status:
                portfolio.status = request.status
            
            # Update variant budgets if provided
            if request.variant_budgets:
                for variant_id, budget in request.variant_budgets.items():
                    for variant in portfolio.variants:
                        if variant['id'] == variant_id:
                            variant['budget'] = budget
                            break
            
            return PortfolioResponse(
                success=True,
                message="Portfolio updated",
                portfolio=self._portfolio_to_proto(portfolio)
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return PortfolioResponse(success=False, message=str(e))
    
    # Variant Operations
    def GetVariantLibrary(self, request, context):
        """Get variant library"""
        try:
            if request.variant_type:
                if request.variant_type not in VARIANT_STRATEGY_LIBRARY:
                    context.set_details(f"Variant {request.variant_type} not found")
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    return VariantLibraryResponse()
                
                variants = {
                    request.variant_type: self._characteristics_to_proto(
                        VARIANT_STRATEGY_LIBRARY[request.variant_type]
                    )
                }
            else:
                variants = {
                    key: self._characteristics_to_proto(chars)
                    for key, chars in VARIANT_STRATEGY_LIBRARY.items()
                }
            
            return VariantLibraryResponse(variants=variants)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return VariantLibraryResponse()
    
    def GetVariantRecommendation(self, request, context):
        """Get variant recommendations for a campaign"""
        try:
            recommendations = get_strategic_recommendations(
                campaign_type=request.campaign_type,
                target_audience=request.target_audience,
                platform=request.platform,
            )
            
            proto_recs = []
            for variant_type, score, reasoning in recommendations:
                proto_recs.append(VariantRecommendation(
                    variant_type=variant_type,
                    variant_name=VARIANT_STRATEGY_LIBRARY[variant_type].name,
                    recommendation_score=score,
                    reasoning=reasoning,
                    characteristics=self._characteristics_to_proto(
                        VARIANT_STRATEGY_LIBRARY[variant_type]
                    )
                ))
            
            return VariantRecommendationResponse(
                recommendations=proto_recs,
                explanation=f"Recommendations based on campaign type: {request.campaign_type}"
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return VariantRecommendationResponse(
                explanation=str(e)
            )
    
    # Testing & Optimization
    def CalculateSampleSize(self, request, context):
        """Calculate required sample size for experiment"""
        try:
            sample_size = calculate_sample_size(
                baseline_rate=request.baseline_rate,
                mde=request.minimum_detectable_effect,
                alpha=request.alpha or 0.05,
                power=request.power or 0.80,
            )
            
            return SampleSizeResponse(
                sample_size_per_variant=sample_size,
                total_sample_size=sample_size * 5,  # 5 variants
                explanation=f"Required {sample_size} samples per variant for 5-variant test"
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return SampleSizeResponse()
    
    def CreateExperiment(self, request, context):
        """Create a multi-variant experiment"""
        try:
            if request.portfolio_id not in self.portfolios:
                context.set_details("Portfolio not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return ExperimentResponse(success=False, message="Portfolio not found")
            
            variants = [request.variant_control] + list(request.variant_test)
            
            experiment = MultiVariantExperiment(
                name=request.experiment_name,
                variants=variants,
                duration_days=request.duration_days,
                significance_level=request.significance_level or 0.05,
            )
            
            self.experiments[experiment.experiment_id] = experiment
            
            from api.generated.variant_strategy_pb2 import Experiment
            return ExperimentResponse(
                success=True,
                message="Experiment created",
                experiment=Experiment(
                    experiment_id=experiment.experiment_id,
                    portfolio_id=request.portfolio_id,
                    name=experiment.name,
                    control_variant=request.variant_control,
                    test_variants=list(request.variant_test),
                    status="created",
                    created_at=datetime.now().isoformat(),
                )
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return ExperimentResponse(success=False, message=str(e))
    
    def AnalyzeExperiment(self, request, context):
        """Analyze experiment results"""
        try:
            if request.experiment_id not in self.experiments:
                context.set_details("Experiment not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return ExperimentAnalysisResponse()
            
            experiment = self.experiments[request.experiment_id]
            
            # Prepare conversion data
            conversions = dict(request.variant_conversions)
            exposures = dict(request.variant_exposures)
            
            # Analyze
            results = analyze_multi_variant_experiment(
                control=experiment.variants[0],
                test_variants=experiment.variants[1:],
                conversions=conversions,
                exposures=exposures,
            )
            
            analyses = []
            winner = None
            winner_confidence = 0.0
            
            for result in results:
                is_sig = result.get('is_significant', False)
                analyses.append(ExperimentAnalysis(
                    variant=result['variant'],
                    conversion_rate=result['conversion_rate'],
                    lift=result['lift'],
                    confidence_interval_lower=result['ci_lower'],
                    confidence_interval_upper=result['ci_upper'],
                    p_value=result['p_value'],
                    is_significant=is_sig,
                    recommendation=result.get('recommendation', ''),
                ))
                
                if is_sig and result['lift'] > winner_confidence:
                    winner = result['variant']
                    winner_confidence = result['lift']
            
            return ExperimentAnalysisResponse(
                analysis=analyses,
                winner=winner or "inconclusive",
                winner_confidence=winner_confidence,
                summary=f"Analysis complete. {len(results)} variants tested."
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return ExperimentAnalysisResponse()
    
    # Learning & Insights
    def CaptureInsight(self, request, context):
        """Capture a campaign insight"""
        try:
            if request.portfolio_id not in self.insights:
                self.insights[request.portfolio_id] = []
            
            insight = {
                'insight_id': f"insight_{len(self.insights[request.portfolio_id])}",
                'portfolio_id': request.portfolio_id,
                'variant': request.variant,
                'type': request.insight_type,
                'description': request.description,
                'metadata': dict(request.metadata),
                'created_at': datetime.now().isoformat(),
            }
            
            self.insights[request.portfolio_id].append(insight)
            
            return InsightResponse(
                success=True,
                insight_id=insight['insight_id'],
                message="Insight captured"
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return InsightResponse(success=False, message=str(e))
    
    def GetInsights(self, request, context):
        """Get insights for a portfolio"""
        try:
            insights = self.insights.get(request.portfolio_id, [])
            
            if request.variant:
                insights = [i for i in insights if i.get('variant') == request.variant]
            
            limit = request.limit or 100
            insights = insights[:limit]
            
            proto_insights = []
            for insight in insights:
                proto_insights.append(Insight(
                    insight_id=insight['insight_id'],
                    portfolio_id=insight['portfolio_id'],
                    variant=insight.get('variant', ''),
                    type=insight['type'],
                    description=insight['description'],
                    created_at=insight['created_at'],
                    metadata=insight.get('metadata', {}),
                ))
            
            return GetInsightsResponse(insights=proto_insights)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return GetInsightsResponse()
    
    # Helper methods
    def _portfolio_to_proto(self, portfolio: VariantPortfolio) -> Portfolio:
        """Convert VariantPortfolio to protobuf Portfolio"""
        variants = []
        for variant in portfolio.variants:
            variants.append(VariantInPortfolio(
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
        
        return Portfolio(
            portfolio_id=portfolio.portfolio_id,
            name=portfolio.name,
            brand=portfolio.brand,
            product=portfolio.product,
            total_budget=portfolio.total_budget,
            variants=variants,
            status=portfolio.status,
            total_impressions=portfolio.total_impressions,
            total_clicks=portfolio.total_clicks,
            portfolio_ctr=portfolio.total_clicks / max(portfolio.total_impressions, 1),
            total_conversions=portfolio.total_conversions,
            portfolio_conversion_rate=portfolio.total_conversions / max(portfolio.total_clicks, 1),
            created_at=portfolio.created_at.isoformat(),
            updated_at=portfolio.updated_at.isoformat(),
        )
    
    def _characteristics_to_proto(self, chars: VariantCharacteristics) -> ProtoVariantCharacteristics:
        """Convert VariantCharacteristics to protobuf"""
        return ProtoVariantCharacteristics(
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
            optimal_duration_seconds=chars.optimal_duration_seconds or 0,
            color_intensity=chars.color_intensity,
            design_complexity=chars.design_complexity,
        )


# ============================================================================
# VARIANT GUARD SERVICE IMPLEMENTATION
# ============================================================================

class VariantGuardServiceImpl(VariantGuardServiceServicer):
    """Implementation of VariantGuardService"""
    
    def __init__(self):
        self.vision_guard = VisionGuardWithVariantOptimization()
        self.image_validator = VariantImageValidator()
        self.quality_ranker = QualityBasedRanking()
    
    def ValidateImage(self, request, context):
        """Validate a single image"""
        try:
            validation = self.vision_guard.validate_variant(
                image_path=request.image_path,
                variant_type=request.variant_type,
                use_mock=request.use_mock,
            )
            
            result = CLIPValidationResult(
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
            
            return ImageValidationResponse(
                success=True,
                message="Image validated",
                validation=result,
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return ImageValidationResponse(success=False, message=str(e))
    
    def ValidatePortfolioImages(self, request, context):
        """Validate all images in a portfolio"""
        try:
            results = []
            quality_scores = {}
            
            for variant_type, image_path in request.variant_image_paths.items():
                validation = self.vision_guard.validate_variant(
                    image_path=image_path,
                    variant_type=variant_type,
                    use_mock=request.use_mock,
                )
                
                quality_tier = self.quality_ranker.get_quality_tier(validation.overall_score)
                quality_scores[variant_type] = validation.overall_score
                
                result = VariantImageQualityResult(
                    variant=variant_type,
                    validation=CLIPValidationResult(
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
                )
                results.append(result)
            
            return PortfolioValidationResponse(
                success=True,
                message="Portfolio validated",
                variant_results=results,
                quality_scores=quality_scores,
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return PortfolioValidationResponse(success=False, message=str(e))


# ============================================================================
# SERVER STARTUP
# ============================================================================

def serve(port: int = 50051):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add services
    add_VariantStrategyServiceServicer_to_server(VariantStrategyServiceImpl(), server)
    add_VariantGuardServiceServicer_to_server(VariantGuardServiceImpl(), server)
    
    # Bind port
    server.add_insecure_port(f'[::]:{port}')
    
    logger.info(f"Starting gRPC server on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 50051
    serve(port)
