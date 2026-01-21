"""
KIKI OaaS Billing Engine: Profit-Share Model
Reads from Immutable Audit Trail (shield_audit.csv / SQL) and calculates margin recovery.
Enables transition from SaaS (fixed fee) → OaaS (outcome-based, revenue share).
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class ClientMetrics:
    """Per-client performance snapshot from audit trail."""
    client_id: str
    period_start: datetime
    period_end: datetime
    total_spend: float  # Micros (1M = $1)
    predicted_ltv_total: float
    actual_ltv_total: float
    accuracy_pct: float
    requests_count: int
    fallback_activations: int
    circuit_trips: int
    
    def to_dict(self) -> Dict:
        return {
            "client_id": self.client_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_spend": self.total_spend,
            "predicted_ltv_total": self.predicted_ltv_total,
            "actual_ltv_total": self.actual_ltv_total,
            "accuracy_pct": self.accuracy_pct,
            "requests_count": self.requests_count,
            "fallback_activations": self.fallback_activations,
            "circuit_trips": self.circuit_trips,
        }

@dataclass
class ProfitShare:
    """Calculated profit share for a client in a billing period."""
    client_id: str
    period_start: datetime
    period_end: datetime
    baseline_roas: float  # Platform default (e.g., 3.0x)
    kiki_roas: float  # Actual LTV / Spend
    margin_improvement: float  # (kiki_roas - baseline_roas) / baseline_roas * 100
    additional_revenue: float  # Extra margin in dollars
    kiki_share_pct: float  # KIKI's cut (e.g., 15%)
    kiki_earnings: float  # Amount owed to KIKI
    
    def to_dict(self) -> Dict:
        return {
            "client_id": self.client_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "baseline_roas": self.baseline_roas,
            "kiki_roas": self.kiki_roas,
            "margin_improvement_pct": round(self.margin_improvement, 2),
            "additional_revenue": round(self.additional_revenue, 2),
            "kiki_share_pct": self.kiki_share_pct,
            "kiki_earnings": round(self.kiki_earnings, 2),
        }

class KIKIOaaSBillingEngine:
    """
    Profit-Share Billing for KIKI Agent™.
    
    Model:
    - Baseline ROAS: Platform's default (e.g., Google's native algo → 3.0x)
    - KIKI ROAS: Actual LTV / Spend from audit trail
    - Margin Improvement: (KIKI ROAS - Baseline) / Baseline
    - Additional Revenue: Margin Improvement * Client Spend
    - KIKI Cut: kiki_share_pct * Additional Revenue
    
    This incentivizes KIKI to maximize client ROI.
    """
    
    def __init__(self, kiki_share_pct: float = 15.0):
        """
        Initialize billing engine.
        
        Args:
            kiki_share_pct: KIKI's percentage cut of margin improvement (e.g., 15%).
        """
        self.kiki_share_pct = kiki_share_pct
    
    def load_audit_trail(self, audit_csv_path: str) -> pd.DataFrame:
        """Load shield_audit.csv into a DataFrame."""
        return pd.read_csv(audit_csv_path)
    
    def aggregate_client_metrics(
        self,
        audit_df: pd.DataFrame,
        client_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> ClientMetrics:
        """
        Aggregate audit trail data for a single client in a time period.
        
        Args:
            audit_df: Loaded audit trail DataFrame.
            client_id: Client identifier (campaign_id or account_id).
            period_start: Billing period start.
            period_end: Billing period end.
        
        Returns:
            ClientMetrics summarizing that client's performance.
        """
        # Filter by client and time range
        mask = (
            (audit_df["client_id"] == client_id) &
            (pd.to_datetime(audit_df["timestamp"]) >= period_start) &
            (pd.to_datetime(audit_df["timestamp"]) <= period_end)
        )
        client_data = audit_df[mask]
        
        if client_data.empty:
            raise ValueError(f"No audit records for {client_id} in {period_start}–{period_end}")
        
        # Sum totals
        total_spend = client_data["spend_micros"].sum()
        predicted_ltv_total = client_data["predicted_ltv"].sum()
        actual_ltv_total = client_data["actual_ltv"].sum()
        accuracy_pct = (
            (client_data["prediction_correct"].sum() / len(client_data) * 100)
            if len(client_data) > 0 else 0.0
        )
        
        return ClientMetrics(
            client_id=client_id,
            period_start=period_start,
            period_end=period_end,
            total_spend=total_spend,
            predicted_ltv_total=predicted_ltv_total,
            actual_ltv_total=actual_ltv_total,
            accuracy_pct=accuracy_pct,
            requests_count=len(client_data),
            fallback_activations=client_data["fallback_used"].sum(),
            circuit_trips=client_data["circuit_open"].sum(),
        )
    
    def calculate_profit_share(
        self,
        client_metrics: ClientMetrics,
        baseline_roas: float,
    ) -> ProfitShare:
        """
        Calculate KIKI's earnings for this client in this period.
        
        Args:
            client_metrics: Aggregated client performance.
            baseline_roas: Platform default (e.g., 3.0 = 3x return).
        
        Returns:
            ProfitShare with KIKI's earnings breakdown.
        """
        # Convert micros to dollars
        spend_dollars = client_metrics.total_spend / 1_000_000
        actual_ltv_dollars = client_metrics.actual_ltv_total / 1_000_000
        
        # Calculate actual ROAS
        kiki_roas = actual_ltv_dollars / spend_dollars if spend_dollars > 0 else 0.0
        
        # Margin improvement vs baseline
        margin_improvement = (
            ((kiki_roas - baseline_roas) / baseline_roas * 100)
            if baseline_roas > 0 else 0.0
        )
        
        # Additional revenue captured
        additional_revenue = (
            spend_dollars * ((kiki_roas - baseline_roas) / baseline_roas)
            if kiki_roas > baseline_roas else 0.0
        )
        
        # KIKI's share of additional revenue
        kiki_earnings = additional_revenue * (self.kiki_share_pct / 100)
        
        return ProfitShare(
            client_id=client_metrics.client_id,
            period_start=client_metrics.period_start,
            period_end=client_metrics.period_end,
            baseline_roas=baseline_roas,
            kiki_roas=kiki_roas,
            margin_improvement=margin_improvement,
            additional_revenue=additional_revenue,
            kiki_share_pct=self.kiki_share_pct,
            kiki_earnings=kiki_earnings,
        )
    
    def generate_invoice(
        self,
        profit_shares: List[ProfitShare],
        invoice_id: str,
        issue_date: datetime,
    ) -> Dict:
        """
        Generate an OaaS invoice summarizing all profit shares.
        
        Args:
            profit_shares: List of ProfitShare objects (one per client/period).
            invoice_id: Unique invoice identifier.
            issue_date: Invoice issue date.
        
        Returns:
            Invoice dict ready for JSON or database storage.
        """
        total_kiki_earnings = sum(ps.kiki_earnings for ps in profit_shares)
        
        invoice = {
            "invoice_id": invoice_id,
            "issue_date": issue_date.isoformat(),
            "line_items": [ps.to_dict() for ps in profit_shares],
            "summary": {
                "total_clients": len(profit_shares),
                "total_margin_improvement": round(
                    sum(ps.margin_improvement for ps in profit_shares) / len(profit_shares),
                    2
                ) if profit_shares else 0,
                "total_additional_revenue": round(
                    sum(ps.additional_revenue for ps in profit_shares), 2
                ),
                "total_kiki_earnings": round(total_kiki_earnings, 2),
                "kiki_share_pct": self.kiki_share_pct,
            },
            "payment_terms": "Net 30",
            "status": "ISSUED",
        }
        
        return invoice

# Example usage
if __name__ == "__main__":
    # Create billing engine (KIKI takes 15% of margin improvement)
    engine = KIKIOaaSBillingEngine(kiki_share_pct=15.0)
    
    # Load audit trail
    audit_path = "shield_audit.csv"
    if Path(audit_path).exists():
        audit_df = engine.load_audit_trail(audit_path)
        print(f"✓ Loaded {len(audit_df)} audit records")
        
        # Example: Bill for the last 7 days
        period_end = datetime.now()
        period_start = period_end - timedelta(days=7)
        
        # Unique clients in the audit trail
        clients = audit_df["client_id"].unique()[:3]  # First 3 clients as example
        
        profit_shares = []
        for client_id in clients:
            try:
                metrics = engine.aggregate_client_metrics(
                    audit_df, client_id, period_start, period_end
                )
                # Assume baseline ROAS = 3.0x (platform default)
                ps = engine.calculate_profit_share(metrics, baseline_roas=3.0)
                profit_shares.append(ps)
                print(f"\n📊 {client_id}:")
                print(f"   Baseline ROAS: {ps.baseline_roas}x")
                print(f"   KIKI ROAS: {ps.kiki_roas:.2f}x")
                print(f"   Margin Improvement: {ps.margin_improvement:.2f}%")
                print(f"   KIKI Earnings: ${ps.kiki_earnings:.2f}")
            except ValueError as e:
                print(f"⚠ {client_id}: {e}")
        
        # Generate invoice
        if profit_shares:
            invoice = engine.generate_invoice(
                profit_shares,
                invoice_id="INV-2026-001",
                issue_date=datetime.now(),
            )
            print("\n💰 OaaS Invoice Summary:")
            print(json.dumps(invoice["summary"], indent=2))
            
            # Save to file
            with open("invoices/ooaS_invoice_2026_001.json", "w") as f:
                json.dump(invoice, f, indent=2)
            print("\n✓ Invoice saved to invoices/ooaS_invoice_2026_001.json")
    else:
        print(f"⚠ Audit trail not found at {audit_path}")
        print("  Run the demo to generate audit_log.csv first.")
