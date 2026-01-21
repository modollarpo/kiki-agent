"""
KIKI Stripe Integration: Automated charge creation for OaaS profit-share invoices.
"""

import stripe
from typing import Dict, Optional
from datetime import datetime
import json

class StripeOaaSBillingAdapter:
    """
    Adapter to sync KIKI OaaS invoices with Stripe.
    
    Workflow:
    1. Generate ProfitShare invoice via KIKIOaaSBillingEngine
    2. Call create_charge_from_invoice() with Stripe customer_id
    3. Stripe charges the customer; webhook confirms payment
    4. Invoice marked PAID in KIKI system
    """
    
    def __init__(self, stripe_api_key: str):
        """
        Initialize Stripe adapter.
        
        Args:
            stripe_api_key: Stripe secret key (from env or vault).
        """
        stripe.api_key = stripe_api_key
    
    def create_charge_from_invoice(
        self,
        invoice_data: Dict,
        customer_id: str,
        description: Optional[str] = None,
    ) -> Dict:
        """
        Create a Stripe charge for KIKI OaaS invoice.
        
        Args:
            invoice_data: Invoice dict from KIKIOaaSBillingEngine.generate_invoice()
            customer_id: Stripe customer ID (associated with client account)
            description: Optional charge description
        
        Returns:
            Stripe charge object (dict)
        """
        amount_cents = int(invoice_data["summary"]["total_kiki_earnings"] * 100)
        
        charge = stripe.Charge.create(
            amount=amount_cents,
            currency="usd",
            customer=customer_id,
            description=description or f"KIKI OaaS Invoice {invoice_data['invoice_id']}",
            metadata={
                "invoice_id": invoice_data["invoice_id"],
                "billing_period_start": invoice_data["line_items"][0]["period_start"],
                "billing_period_end": invoice_data["line_items"][0]["period_end"],
                "margin_improvement_pct": str(
                    invoice_data["summary"]["total_margin_improvement"]
                ),
            },
        )
        
        return charge
    
    def create_subscription_from_invoice(
        self,
        customer_id: str,
        invoice_data: Dict,
        billing_cycle_anchor: datetime,
    ) -> Dict:
        """
        Create a Stripe subscription for recurring OaaS billing.
        
        Args:
            customer_id: Stripe customer ID
            invoice_data: Invoice dict (used for metadata)
            billing_cycle_anchor: Day-of-month for next bill (e.g., 1st, 15th)
        
        Returns:
            Stripe subscription object
        """
        # Create a product for OaaS service
        product = stripe.Product.create(
            name="KIKI SyncShield OaaS (Profit-Share)",
            description="AI-powered revenue engine with outcome-based billing",
            metadata={"model": "profit_share"},
        )
        
        # Create price (to be used in subscription)
        # Note: For recurring OaaS, you'd typically set this up in Stripe dashboard
        # and reference it here. This is a placeholder for manual billing cycles.
        price = stripe.Price.create(
            product=product.id,
            billing_scheme="per_unit",
            currency="usd",
            recurring={"interval": "month", "interval_count": 1},
            unit_amount=1,  # Placeholder; actual amount set in invoice
        )
        
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price.id, "quantity": 1}],
            billing_cycle_anchor=int(billing_cycle_anchor.timestamp()),
            metadata={"invoice_id": invoice_data["invoice_id"]},
        )
        
        return subscription
    
    def record_payment(self, invoice_id: str, charge_id: str) -> Dict:
        """
        Record a successful payment (for KIKI accounting/reporting).
        
        Args:
            invoice_id: KIKI invoice ID
            charge_id: Stripe charge ID
        
        Returns:
            Payment record
        """
        return {
            "invoice_id": invoice_id,
            "charge_id": charge_id,
            "status": "PAID",
            "timestamp": datetime.now().isoformat(),
        }

# Example usage
if __name__ == "__main__":
    import os
    
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_example")
    adapter = StripeOaaSBillingAdapter(stripe_key)
    
    # Mock invoice
    invoice = {
        "invoice_id": "INV-2026-DEMO-001",
        "summary": {"total_kiki_earnings": 32.29},
        "line_items": [
            {"period_start": "2026-01-11T00:00:00", "period_end": "2026-01-18T00:00:00"}
        ],
    }
    
    print("✓ Stripe adapter initialized")
    print(f"  To charge a customer, call:")
    print(f"  charge = adapter.create_charge_from_invoice(invoice, 'cus_xxxxx')")
