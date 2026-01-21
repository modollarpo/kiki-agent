"""
REST API Client Examples
Shows how to use the REST API from clients using requests and curl
"""

import requests
import json
from typing import Dict, Optional
from dataclasses import dataclass

# API Configuration
API_BASE_URL = "http://localhost:8000/api"


class RestApiClient:
    """REST API client for Variant Strategy"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    # ========================================================================
    # Portfolio Operations
    # ========================================================================
    
    def create_portfolio(self, name: str, brand: str, product: str, 
                        total_budget: float, variant_types: list = None,
                        variant_budgets: dict = None) -> Dict:
        """Create a new portfolio"""
        url = f"{self.base_url}/portfolios"
        data = {
            "name": name,
            "brand": brand,
            "product": product,
            "total_budget": total_budget,
            "variant_types": variant_types,
            "variant_budgets": variant_budgets,
        }
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_portfolio(self, portfolio_id: str) -> Dict:
        """Get portfolio by ID"""
        url = f"{self.base_url}/portfolios/{portfolio_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def list_portfolios(self, brand: str = None, limit: int = 100, 
                       offset: int = 0) -> Dict:
        """List portfolios"""
        url = f"{self.base_url}/portfolios"
        params = {
            "brand": brand,
            "limit": limit,
            "offset": offset,
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # Variant Operations
    # ========================================================================
    
    def get_variant_library(self, variant_type: str = None) -> Dict:
        """Get variant library"""
        url = f"{self.base_url}/variants/library"
        params = {}
        if variant_type:
            params["variant_type"] = variant_type
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_variant_recommendations(self, campaign_type: str, 
                                   target_audience: str, platform: str,
                                   goal: str = None) -> Dict:
        """Get variant recommendations"""
        url = f"{self.base_url}/variants/recommendations"
        data = {
            "campaign_type": campaign_type,
            "target_audience": target_audience,
            "platform": platform,
            "goal": goal,
        }
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # Testing & Analysis
    # ========================================================================
    
    def calculate_sample_size(self, baseline_rate: float, 
                             minimum_detectable_effect: float,
                             alpha: float = 0.05, power: float = 0.80) -> Dict:
        """Calculate required sample size"""
        url = f"{self.base_url}/testing/sample-size"
        data = {
            "baseline_rate": baseline_rate,
            "minimum_detectable_effect": minimum_detectable_effect,
            "alpha": alpha,
            "power": power,
        }
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def analyze_experiment(self, control_variant: str, test_variants: list,
                          variant_conversions: dict, 
                          variant_exposures: dict) -> Dict:
        """Analyze experiment results"""
        url = f"{self.base_url}/testing/analyze"
        params = {
            "control_variant": control_variant,
            "test_variants": ",".join(test_variants),
        }
        data = {
            "variant_conversions": variant_conversions,
            "variant_exposures": variant_exposures,
        }
        response = self.session.post(url, params=params, json=data)
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # Vision Guard Validation
    # ========================================================================
    
    def validate_image(self, variant_type: str, image_path: str,
                      portfolio_id: str = None, use_mock: bool = True) -> Dict:
        """Validate a single image"""
        url = f"{self.base_url}/validation/image"
        data = {
            "variant_type": variant_type,
            "image_path": image_path,
            "portfolio_id": portfolio_id,
            "use_mock": use_mock,
        }
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def validate_portfolio(self, portfolio_id: str, 
                          variant_image_paths: dict,
                          use_mock: bool = True) -> Dict:
        """Validate all images in portfolio"""
        url = f"{self.base_url}/validation/portfolio"
        data = {
            "portfolio_id": portfolio_id,
            "variant_image_paths": variant_image_paths,
            "use_mock": use_mock,
        }
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_quality_report(self, portfolio_id: str) -> Dict:
        """Get quality report"""
        url = f"{self.base_url}/validation/quality-report/{portfolio_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # Insights
    # ========================================================================
    
    def capture_insight(self, portfolio_id: str, insight_type: str,
                       variant: str, description: str) -> Dict:
        """Capture an insight"""
        url = f"{self.base_url}/insights"
        params = {
            "portfolio_id": portfolio_id,
            "insight_type": insight_type,
            "variant": variant,
            "description": description,
        }
        response = self.session.post(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_insights(self, portfolio_id: str, variant: str = None,
                    limit: int = 100) -> Dict:
        """Get insights"""
        url = f"{self.base_url}/insights/{portfolio_id}"
        params = {
            "variant": variant,
            "limit": limit,
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # Health & Info
    # ========================================================================
    
    def health_check(self) -> Dict:
        """Check API health"""
        url = f"{self.base_url.rsplit('/api', 1)[0]}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_info(self) -> Dict:
        """Get API info"""
        url = f"{self.base_url.rsplit('/api', 1)[0]}/info"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


# ============================================================================
# EXAMPLES
# ============================================================================

def example_health_check():
    """Example: Check API health"""
    print("\n" + "="*80)
    print("EXAMPLE: Health Check")
    print("="*80)
    
    client = RestApiClient()
    
    try:
        result = client.health_check()
        print(f"\n✓ API is healthy")
        print(f"  Status: {result['status']}")
        print(f"  Service: {result['service']}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_create_portfolio():
    """Example: Create portfolio"""
    print("\n" + "="*80)
    print("EXAMPLE: Create Portfolio")
    print("="*80)
    
    client = RestApiClient()
    
    try:
        result = client.create_portfolio(
            name="Q1 2026 Campaign",
            brand="TechBrand",
            product="AI Assistant Pro",
            total_budget=100000.0,
            variant_types=["control", "lifestyle", "abstract", "high_contrast", "data_led"],
        )
        
        print(f"\n✓ Portfolio created successfully")
        print(f"  ID: {result['portfolio']['portfolio_id']}")
        print(f"  Name: {result['portfolio']['name']}")
        print(f"  Budget: ${result['portfolio']['total_budget']:,.2f}")
        print(f"  Variants: {len(result['portfolio']['variants'])}")
        
        return result['portfolio']['portfolio_id']
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def example_get_variant_library():
    """Example: Get variant library"""
    print("\n" + "="*80)
    print("EXAMPLE: Get Variant Library")
    print("="*80)
    
    client = RestApiClient()
    
    try:
        result = client.get_variant_library()
        
        print(f"\n✓ Variant library retrieved")
        print(f"  Total variants: {len(result['variants'])}")
        
        for variant_type, characteristics in result['variants'].items():
            print(f"\n  {variant_type.upper()}")
            print(f"    Name: {characteristics['name']}")
            print(f"    CTR Lift: {characteristics['ctr_lift_potential']:.0%}")
            print(f"    Conversion Lift: {characteristics['conversion_lift']:.0%}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_get_recommendations():
    """Example: Get variant recommendations"""
    print("\n" + "="*80)
    print("EXAMPLE: Get Variant Recommendations")
    print("="*80)
    
    client = RestApiClient()
    
    try:
        result = client.get_variant_recommendations(
            campaign_type="awareness",
            target_audience="tech professionals",
            platform="linkedin",
        )
        
        print(f"\n✓ Recommendations retrieved")
        print(f"  Explanation: {result['explanation']}")
        print(f"\n  Recommendations:")
        
        for rec in result['recommendations']:
            print(f"\n    {rec['variant_name']} ({rec['variant_type']})")
            print(f"      Score: {rec['recommendation_score']:.2f}")
            print(f"      Reasoning: {rec['reasoning']}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_sample_size():
    """Example: Calculate sample size"""
    print("\n" + "="*80)
    print("EXAMPLE: Calculate Sample Size")
    print("="*80)
    
    client = RestApiClient()
    
    try:
        result = client.calculate_sample_size(
            baseline_rate=0.05,
            minimum_detectable_effect=0.05,
        )
        
        print(f"\n✓ Sample size calculated")
        print(f"  Per Variant: {result['sample_size_per_variant']:,}")
        print(f"  Total (5 variants): {result['total_sample_size']:,}")
        print(f"  Explanation: {result['explanation']}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_validate_image():
    """Example: Validate image"""
    print("\n" + "="*80)
    print("EXAMPLE: Validate Image")
    print("="*80)
    
    client = RestApiClient()
    
    try:
        result = client.validate_image(
            variant_type="lifestyle",
            image_path="/path/to/image.jpg",
            use_mock=True,
        )
        
        if result['success']:
            val = result['validation']
            print(f"\n✓ Image validated")
            print(f"  Product Confidence: {val['product_confidence']:.2%}")
            print(f"  Safety Score: {val['safety_score']:.2%}")
            print(f"  Quality Score: {val['quality_score']:.2%}")
            print(f"  Overall Score: {val['overall_score']:.2%}")
            print(f"  Approved: {val['is_approved']}")
            
            if val['recommendations']:
                print(f"\n  Recommendations:")
                for rec in val['recommendations']:
                    print(f"    • {rec}")
        else:
            print(f"\n✗ Validation failed: {result['message']}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


# ============================================================================
# CURL EXAMPLES
# ============================================================================

CURL_EXAMPLES = """
# REST API CURL Examples
# Base URL: http://localhost:8000/api

# 1. Health Check
curl -X GET http://localhost:8000/health

# 2. Create Portfolio
curl -X POST http://localhost:8000/api/portfolios \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Q1 2026 Campaign",
    "brand": "TechBrand",
    "product": "AI Assistant Pro",
    "total_budget": 100000,
    "variant_types": ["control", "lifestyle", "abstract", "high_contrast", "data_led"]
  }'

# 3. Get Portfolio
curl -X GET http://localhost:8000/api/portfolios/{portfolio_id}

# 4. List Portfolios
curl -X GET "http://localhost:8000/api/portfolios?brand=TechBrand&limit=10"

# 5. Get Variant Library
curl -X GET http://localhost:8000/api/variants/library

# 6. Get Specific Variant
curl -X GET "http://localhost:8000/api/variants/library?variant_type=lifestyle"

# 7. Get Variant Recommendations
curl -X POST http://localhost:8000/api/variants/recommendations \\
  -H "Content-Type: application/json" \\
  -d '{
    "campaign_type": "awareness",
    "target_audience": "tech professionals",
    "platform": "linkedin",
    "goal": "brand_awareness"
  }'

# 8. Calculate Sample Size
curl -X POST http://localhost:8000/api/testing/sample-size \\
  -H "Content-Type: application/json" \\
  -d '{
    "baseline_rate": 0.05,
    "minimum_detectable_effect": 0.05,
    "alpha": 0.05,
    "power": 0.80
  }'

# 9. Validate Image
curl -X POST http://localhost:8000/api/validation/image \\
  -H "Content-Type: application/json" \\
  -d '{
    "variant_type": "lifestyle",
    "image_path": "/path/to/image.jpg",
    "use_mock": true
  }'

# 10. Validate Portfolio
curl -X POST http://localhost:8000/api/validation/portfolio \\
  -H "Content-Type: application/json" \\
  -d '{
    "portfolio_id": "portfolio_123",
    "variant_image_paths": {
      "control": "/path/to/control.jpg",
      "lifestyle": "/path/to/lifestyle.jpg",
      "abstract": "/path/to/abstract.jpg",
      "high_contrast": "/path/to/high_contrast.jpg",
      "data_led": "/path/to/data_led.jpg"
    },
    "use_mock": true
  }'

# 11. Capture Insight
curl -X POST "http://localhost:8000/api/insights?portfolio_id=p123&insight_type=performance&variant=lifestyle&description=High%20CTR%20observed"

# 12. Get Insights
curl -X GET "http://localhost:8000/api/insights/portfolio_123?limit=10"

# 13. Get API Info
curl -X GET http://localhost:8000/info
"""


if __name__ == "__main__":
    print("Variant Strategy REST API Client Examples")
    print("=" * 80)
    print("\nNote: These examples require the REST API to be running.")
    print("Start the API with: python -m uvicorn api.rest_api:app --host 0.0.0.0 --port 8000")
    
    # Run examples
    print("\n" + "="*80)
    print("Running REST API Examples")
    print("="*80)
    
    example_health_check()
    example_get_variant_library()
    example_get_recommendations()
    example_sample_size()
    portfolio_id = example_create_portfolio()
    if portfolio_id:
        example_validate_image()
    
    # Print curl examples
    print("\n" + "="*80)
    print("CURL Examples")
    print("="*80)
    print(CURL_EXAMPLES)
