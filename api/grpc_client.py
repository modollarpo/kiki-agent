"""
gRPC Client Examples
Shows how to use the gRPC API from clients
"""

import grpc
import sys
from pathlib import Path
from typing import Dict, List

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from api.generated.variant_strategy_pb2 import (
        CreatePortfolioRequest, GetPortfolioRequest,
        GetVariantLibraryRequest, GetVariantRecommendationRequest,
        SampleSizeRequest, CreateExperimentRequest, AnalyzeExperimentRequest,
        CaptureInsightRequest, GetInsightsRequest,
        ImageValidationRequest, PortfolioValidationRequest,
    )
    from api.generated.variant_strategy_pb2_grpc import (
        VariantStrategyServiceStub, VariantGuardServiceStub
    )
except ImportError as e:
    print(f"Error: Could not import protobuf modules: {e}")
    print("\nTo generate protobuf code, run:")
    print("  python -m grpc_tools.protoc -I proto/ --python_out=api/generated --pyi_out=api/generated --grpc_python_out=api/generated proto/variant_strategy.proto")
    sys.exit(1)


class VariantStrategyClient:
    """gRPC client for Variant Strategy Service"""
    
    def __init__(self, host: str = 'localhost', port: int = 50051):
        """Initialize client"""
        self.channel = grpc.aio.secure_channel(f'{host}:{port}')
        self.stub = VariantStrategyServiceStub(self.channel)
    
    async def create_portfolio(self, name: str, brand: str, product: str, 
                               total_budget: float, variant_types: List[str]):
        """Create a portfolio"""
        request = CreatePortfolioRequest(
            name=name,
            brand=brand,
            product=product,
            total_budget=total_budget,
            variant_types=variant_types,
        )
        response = await self.stub.CreatePortfolio(request)
        return response
    
    async def get_portfolio(self, portfolio_id: str):
        """Get portfolio by ID"""
        request = GetPortfolioRequest(portfolio_id=portfolio_id)
        response = await self.stub.GetPortfolio(request)
        return response
    
    async def get_variant_library(self, variant_type: str = None):
        """Get variant library"""
        request = GetVariantLibraryRequest(variant_type=variant_type or '')
        response = await self.stub.GetVariantLibrary(request)
        return response
    
    async def get_variant_recommendation(self, campaign_type: str, 
                                        target_audience: str, platform: str):
        """Get variant recommendations"""
        request = GetVariantRecommendationRequest(
            campaign_type=campaign_type,
            target_audience=target_audience,
            platform=platform,
        )
        response = await self.stub.GetVariantRecommendation(request)
        return response
    
    async def calculate_sample_size(self, baseline_rate: float, 
                                   mde: float, alpha: float = 0.05, 
                                   power: float = 0.80):
        """Calculate required sample size"""
        request = SampleSizeRequest(
            baseline_rate=baseline_rate,
            minimum_detectable_effect=mde,
            alpha=alpha,
            power=power,
        )
        response = await self.stub.CalculateSampleSize(request)
        return response
    
    async def close(self):
        """Close connection"""
        await self.channel.close()


class VariantGuardClient:
    """gRPC client for Variant Guard Service"""
    
    def __init__(self, host: str = 'localhost', port: int = 50051):
        """Initialize client"""
        self.channel = grpc.aio.secure_channel(f'{host}:{port}')
        self.stub = VariantGuardServiceStub(self.channel)
    
    async def validate_image(self, variant_type: str, image_path: str, 
                            use_mock: bool = True):
        """Validate a single image"""
        request = ImageValidationRequest(
            variant_type=variant_type,
            image_path=image_path,
            use_mock=use_mock,
        )
        response = await self.stub.ValidateImage(request)
        return response
    
    async def validate_portfolio(self, portfolio_id: str, 
                                variant_image_paths: Dict[str, str],
                                use_mock: bool = True):
        """Validate portfolio images"""
        request = PortfolioValidationRequest(
            portfolio_id=portfolio_id,
            variant_image_paths=variant_image_paths,
            use_mock=use_mock,
        )
        response = await self.stub.ValidatePortfolioImages(request)
        return response
    
    async def close(self):
        """Close connection"""
        await self.channel.close()


# Synchronous wrapper clients
class VariantStrategyClientSync:
    """Synchronous gRPC client for Variant Strategy Service"""
    
    def __init__(self, host: str = 'localhost', port: int = 50051):
        """Initialize client"""
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = VariantStrategyServiceStub(self.channel)
    
    def create_portfolio(self, name: str, brand: str, product: str, 
                        total_budget: float, variant_types: List[str]):
        """Create a portfolio"""
        request = CreatePortfolioRequest(
            name=name,
            brand=brand,
            product=product,
            total_budget=total_budget,
            variant_types=variant_types,
        )
        response = self.stub.CreatePortfolio(request)
        return response
    
    def get_portfolio(self, portfolio_id: str):
        """Get portfolio by ID"""
        request = GetPortfolioRequest(portfolio_id=portfolio_id)
        response = self.stub.GetPortfolio(request)
        return response
    
    def get_variant_library(self, variant_type: str = None):
        """Get variant library"""
        request = GetVariantLibraryRequest(variant_type=variant_type or '')
        response = self.stub.GetVariantLibrary(request)
        return response
    
    def get_variant_recommendation(self, campaign_type: str, 
                                  target_audience: str, platform: str):
        """Get variant recommendations"""
        request = GetVariantRecommendationRequest(
            campaign_type=campaign_type,
            target_audience=target_audience,
            platform=platform,
        )
        response = self.stub.GetVariantRecommendation(request)
        return response
    
    def calculate_sample_size(self, baseline_rate: float, 
                             mde: float, alpha: float = 0.05, 
                             power: float = 0.80):
        """Calculate required sample size"""
        request = SampleSizeRequest(
            baseline_rate=baseline_rate,
            minimum_detectable_effect=mde,
            alpha=alpha,
            power=power,
        )
        response = self.stub.CalculateSampleSize(request)
        return response
    
    def close(self):
        """Close connection"""
        self.channel.close()


class VariantGuardClientSync:
    """Synchronous gRPC client for Variant Guard Service"""
    
    def __init__(self, host: str = 'localhost', port: int = 50051):
        """Initialize client"""
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = VariantGuardServiceStub(self.channel)
    
    def validate_image(self, variant_type: str, image_path: str, 
                      use_mock: bool = True):
        """Validate a single image"""
        request = ImageValidationRequest(
            variant_type=variant_type,
            image_path=image_path,
            use_mock=use_mock,
        )
        response = self.stub.ValidateImage(request)
        return response
    
    def validate_portfolio(self, portfolio_id: str, 
                          variant_image_paths: Dict[str, str],
                          use_mock: bool = True):
        """Validate portfolio images"""
        request = PortfolioValidationRequest(
            portfolio_id=portfolio_id,
            variant_image_paths=variant_image_paths,
            use_mock=use_mock,
        )
        response = self.stub.ValidatePortfolioImages(request)
        return response
    
    def close(self):
        """Close connection"""
        self.channel.close()


# ============================================================================
# EXAMPLES
# ============================================================================

def example_create_portfolio():
    """Example: Create a portfolio via gRPC"""
    print("\n" + "="*80)
    print("EXAMPLE: Create Portfolio via gRPC")
    print("="*80)
    
    client = VariantStrategyClientSync()
    
    try:
        response = client.create_portfolio(
            name="Q1 2026 Campaign",
            brand="TechBrand",
            product="AI Assistant Pro",
            total_budget=100000.0,
            variant_types=["control", "lifestyle", "abstract", "high_contrast", "data_led"],
        )
        
        print(f"\nSuccess: {response.success}")
        print(f"Message: {response.message}")
        if response.portfolio:
            print(f"Portfolio ID: {response.portfolio.portfolio_id}")
            print(f"Brand: {response.portfolio.brand}")
            print(f"Total Budget: ${response.portfolio.total_budget:,.2f}")
            print(f"Variants: {len(response.portfolio.variants)}")
    finally:
        client.close()


def example_get_variant_recommendations():
    """Example: Get variant recommendations via gRPC"""
    print("\n" + "="*80)
    print("EXAMPLE: Get Variant Recommendations via gRPC")
    print("="*80)
    
    client = VariantStrategyClientSync()
    
    try:
        response = client.get_variant_recommendation(
            campaign_type="awareness",
            target_audience="tech professionals",
            platform="linkedin",
        )
        
        print(f"\nExplanation: {response.explanation}")
        print(f"\nRecommendations:")
        for rec in response.recommendations:
            print(f"\n  {rec.variant_name} ({rec.variant_type})")
            print(f"    Score: {rec.recommendation_score:.2f}")
            print(f"    Reasoning: {rec.reasoning}")
            print(f"    Lift Potential: {rec.characteristics.conversion_lift:.0%}")
    finally:
        client.close()


def example_calculate_sample_size():
    """Example: Calculate sample size via gRPC"""
    print("\n" + "="*80)
    print("EXAMPLE: Calculate Sample Size via gRPC")
    print("="*80)
    
    client = VariantStrategyClientSync()
    
    try:
        response = client.calculate_sample_size(
            baseline_rate=0.05,
            mde=0.05,
            alpha=0.05,
            power=0.80,
        )
        
        print(f"\nSample Size per Variant: {response.sample_size_per_variant:,}")
        print(f"Total Sample Size (5 variants): {response.total_sample_size:,}")
        print(f"Explanation: {response.explanation}")
    finally:
        client.close()


def example_validate_image():
    """Example: Validate image via gRPC"""
    print("\n" + "="*80)
    print("EXAMPLE: Validate Image via gRPC")
    print("="*80)
    
    client = VariantGuardClientSync()
    
    try:
        response = client.validate_image(
            variant_type="lifestyle",
            image_path="/path/to/image.jpg",
            use_mock=True,
        )
        
        print(f"\nValidation Success: {response.success}")
        print(f"Message: {response.message}")
        if response.validation:
            val = response.validation
            print(f"\nValidation Results:")
            print(f"  Product Confidence: {val.product_confidence:.2%}")
            print(f"  Safety Score: {val.safety_score:.2%}")
            print(f"  Quality Score: {val.quality_score:.2%}")
            print(f"  Overall Score: {val.overall_score:.2%}")
            print(f"  Approved: {val.is_approved}")
            print(f"\nRecommendations:")
            for rec in val.recommendations:
                print(f"  • {rec}")
    finally:
        client.close()


if __name__ == "__main__":
    print("Variant Strategy gRPC Client Examples")
    print("=" * 80)
    print("\nNote: These examples require the gRPC server to be running.")
    print("Start the server with: python api/grpc_server.py")
    print("\nAvailable examples:")
    print("  1. Create portfolio")
    print("  2. Get variant recommendations")
    print("  3. Calculate sample size")
    print("  4. Validate image")
    
    # Uncomment to run examples (requires server running):
    # example_create_portfolio()
    # example_get_variant_recommendations()
    # example_calculate_sample_size()
    # example_validate_image()
