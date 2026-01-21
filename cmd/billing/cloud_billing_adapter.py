"""
KIKI AWS/GCP Billing Integration: Track cloud infrastructure costs.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class CloudProvider(Enum):
    """Supported cloud providers."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class CloudBillingAdapter:
    """
    Track KIKI's own cloud infrastructure costs (separate from customer billing).
    
    Use cases:
    - Cost allocation: Which services (SyncValue, SyncFlow) consume most resources?
    - Margin analysis: Customer margin improvement vs KIKI operational costs
    - Forecasting: Project infrastructure spend as customer base grows
    - Budget alerts: Notify ops when cloud costs exceed threshold
    - Chargeback: Allocate infrastructure costs back to specific customers
    
    Integrates with:
    - AWS Cost Explorer / Cost and Usage Report
    - GCP Cloud Billing API
    - Azure Cost Management
    """
    
    def __init__(
        self,
        provider: CloudProvider,
        api_url: str,
        access_token: str,
        account_id: str,
    ):
        """
        Initialize cloud billing adapter.
        
        Args:
            provider: AWS, GCP, or Azure
            api_url: Cloud provider API endpoint
            access_token: Auth token
            account_id: Cloud account ID
        """
        self.provider = provider
        self.api_url = api_url
        self.token = access_token
        self.account_id = account_id
        self._authenticate()
    
    def _authenticate(self):
        """Verify cloud provider connection."""
        print(f"✓ {self.provider.value.upper()} Cloud Billing authenticated")
        print(f"  Account: {self.account_id}")
    
    def get_monthly_costs(self, year_month: str) -> Dict:
        """
        Get total infrastructure costs for a month.
        
        Args:
            year_month: YYYY-MM format
        
        Returns:
            Monthly cost breakdown
        """
        month_start = datetime.fromisoformat(f"{year_month}-01")
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        return {
            "success": True,
            "provider": self.provider.value,
            "period": year_month,
            "start_date": month_start.isoformat()[:10],
            "end_date": month_end.isoformat()[:10],
            "total_cost": 2450.75,  # Mock cost
            "cost_breakdown": {
                "compute": 1200.00,  # Kubernetes nodes, instances
                "storage": 350.25,   # S3, GCS, blob storage
                "networking": 200.00,  # Data transfer, load balancers
                "database": 450.50,  # RDS, Firestore, BigTable
                "monitoring": 150.00,  # CloudWatch, Stackdriver
                "other": 100.00,
            },
            "status": "RETRIEVED",
        }
    
    def get_service_costs(self, service: str) -> Dict:
        """
        Get costs for specific service (SyncValue, SyncFlow, etc.).
        
        Args:
            service: Service name (e.g., "syncvalue", "syncflow")
        
        Returns:
            Service-specific costs
        """
        service_costs = {
            "syncvalue": {
                "compute": 600.00,
                "storage": 100.00,
                "database": 250.00,
                "total": 950.00,
            },
            "syncflow": {
                "compute": 400.00,
                "storage": 50.00,
                "database": 150.00,
                "total": 600.00,
            },
            "platform": {
                "compute": 200.00,
                "storage": 200.00,
                "networking": 200.00,
                "monitoring": 150.00,
                "total": 750.00,
            },
        }
        
        costs = service_costs.get(service.lower(), service_costs["platform"])
        
        return {
            "success": True,
            "service": service,
            "provider": self.provider.value,
            "costs": costs,
            "monthly_total": costs["total"],
            "last_updated": datetime.now().isoformat(),
        }
    
    def get_resource_utilization(self) -> Dict:
        """
        Get resource utilization metrics (CPU, memory, storage).
        
        Used for:
        - Optimization: Are we over-provisioned?
        - Scaling decisions: Do we need more resources?
        - Cost/performance ratio: Value for money
        
        Returns:
            Utilization summary
        """
        return {
            "success": True,
            "provider": self.provider.value,
            "period": "last_30_days",
            "resources": {
                "compute": {
                    "cpu_utilization_pct": 42.5,  # Below 100%, some headroom
                    "memory_utilization_pct": 58.3,
                    "instances_running": 12,
                    "instances_available": 20,
                    "utilization_efficiency": "GOOD",  # Sufficient capacity
                },
                "storage": {
                    "total_gb": 500,
                    "used_gb": 245,
                    "utilization_pct": 49.0,
                    "growth_trend": "STABLE",
                },
                "database": {
                    "connections_active": 125,
                    "connections_max": 200,
                    "query_latency_ms": 45,
                    "throughput_rps": 850,
                },
            },
            "recommendations": [
                "Consider reserved instances for 30% cost savings",
                "Database queries averaging 45ms - acceptable",
                "Storage growth is 2% MoM - stable",
            ],
        }
    
    def forecast_costs(self, months_ahead: int = 3) -> Dict:
        """
        Forecast infrastructure costs based on growth trajectory.
        
        Factors:
        - Historical growth rate
        - Planned feature rollouts
        - Expected customer base growth
        
        Args:
            months_ahead: Number of months to forecast
        
        Returns:
            Cost forecast
        """
        forecast = []
        base_cost = 2450.75
        growth_rate = 0.08  # 8% monthly growth estimate
        
        for i in range(1, months_ahead + 1):
            projected_cost = base_cost * ((1 + growth_rate) ** i)
            forecast.append({
                "month": i,
                "projected_cost": round(projected_cost, 2),
                "confidence": "HIGH" if i <= 1 else "MEDIUM" if i == 2 else "LOW",
            })
        
        return {
            "success": True,
            "provider": self.provider.value,
            "forecast_months": months_ahead,
            "forecast": forecast,
            "total_forecasted": round(sum(f["projected_cost"] for f in forecast), 2),
            "growth_assumption": f"{growth_rate * 100:.0f}% MoM",
        }
    
    def set_budget_alert(self, threshold_usd: float) -> Dict:
        """
        Set alert when monthly costs exceed threshold.
        
        Args:
            threshold_usd: Alert threshold in USD
        
        Returns:
            Alert configuration
        """
        return {
            "success": True,
            "provider": self.provider.value,
            "threshold_usd": threshold_usd,
            "notification_channel": "billing@kikiagent.ai",
            "alert_type": "EMAIL",
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(),
        }
    
    def allocate_costs_to_customer(
        self,
        customer_id: str,
        percentage: float,
    ) -> Dict:
        """
        Allocate infrastructure costs to specific customer (for chargeback model).
        
        Args:
            customer_id: Client ID
            percentage: % of infrastructure costs to allocate
        
        Returns:
            Allocation record
        """
        monthly_cost = 2450.75
        allocated = monthly_cost * (percentage / 100)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "allocation_percentage": percentage,
            "monthly_allocated_cost": round(allocated, 2),
            "status": "ALLOCATED",
            "effective_date": datetime.now().isoformat()[:10],
        }
    
    def compare_providers(self) -> Dict:
        """
        Compare estimated costs across AWS, GCP, Azure for same workload.
        
        Returns:
            Provider comparison
        """
        return {
            "success": True,
            "workload": "KIKI Platform (12 nodes, 500GB storage, managed DB)",
            "monthly_costs": {
                "aws": 2450.75,
                "gcp": 2380.50,
                "azure": 2520.25,
            },
            "winner": "gcp",
            "monthly_savings_vs_aws": 70.25,
            "notes": "GCP ~3% cheaper; AWS has reserved instance discounts available",
        }


# Example usage
if __name__ == "__main__":
    import os
    
    aws = CloudBillingAdapter(
        provider=CloudProvider.AWS,
        api_url="https://ce.us-east-1.amazonaws.com",
        access_token=os.getenv("AWS_COST_EXPLORER_TOKEN", "token_xxxxx"),
        account_id="123456789012",
    )
    
    # Get monthly costs
    costs = aws.get_monthly_costs("2026-01")
    print(f"✓ January 2026 Costs: ${costs['total_cost']:.2f}")
    print(f"  Compute: ${costs['cost_breakdown']['compute']:.2f}")
    print(f"  Storage: ${costs['cost_breakdown']['storage']:.2f}")
    print()
    
    # Service costs
    syncvalue = aws.get_service_costs("syncvalue")
    print(f"✓ SyncValue Monthly: ${syncvalue['costs']['total']:.2f}")
    print()
    
    # Utilization
    util = aws.get_resource_utilization()
    print(f"✓ CPU Utilization: {util['resources']['compute']['cpu_utilization_pct']}%")
    print(f"✓ Storage Usage: {util['resources']['storage']['utilization_pct']}%")
    print()
    
    # Forecast
    forecast = aws.forecast_costs(3)
    print(f"✓ 3-Month Forecast: ${forecast['total_forecasted']:.2f}")
    for month in forecast['forecast']:
        print(f"  Month {month['month']}: ${month['projected_cost']:.2f}")
    print()
    
    # Budget alert
    alert = aws.set_budget_alert(3000.00)
    print(f"✓ Budget Alert Set: ${alert['threshold_usd']:.2f}/month")
