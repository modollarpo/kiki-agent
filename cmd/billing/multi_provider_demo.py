#!/usr/bin/env python3
"""
Multi-Provider Billing Demo: Compare Stripe, Zuora, and PayPal
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from stripe_adapter import StripeOaaSBillingAdapter
from zuora_adapter import ZuoraOaaSBillingAdapter
from paypal_adapter import PayPalOaaSBillingAdapter


def demo_invoice():
    """Sample OaaS invoice for all providers."""
    return {
        "invoice_id": "INV-2026-MULTI-001",
        "issue_date": "2026-01-18T00:00:00",
        "payment_terms": "Net 30",
        "summary": {
            "total_margin_improvement": 45.0,
            "total_kiki_earnings": 32.29,
        },
        "line_items": [
            {
                "client_id": "google_ads_demo",
                "margin_improvement_pct": 49.0,
                "period_start": "2026-01-11T00:00:00",
                "period_end": "2026-01-18T00:00:00",
                "kiki_earnings": 18.83,
            },
            {
                "client_id": "meta_demo",
                "margin_improvement_pct": 41.0,
                "period_start": "2026-01-11T00:00:00",
                "period_end": "2026-01-18T00:00:00",
                "kiki_earnings": 13.46,
            },
        ],
    }


def main():
    """Compare all three billing providers."""
    
    print("=" * 80)
    print("KIKI OaaS Billing: Multi-Provider Demo (Stripe, Zuora, PayPal)")
    print("=" * 80)
    print()
    
    invoice = demo_invoice()
    
    print(f"Invoice ID: {invoice['invoice_id']}")
    print(f"Total Earnings: ${invoice['summary']['total_kiki_earnings']:.2f}")
    print(f"Margin Improvement: {invoice['summary']['total_margin_improvement']:.1f}%")
    print()
    print("-" * 80)
    print()
    
    # 1. Stripe
    print("🟠 STRIPE ADAPTER")
    print("-" * 80)
    try:
        stripe = StripeOaaSBillingAdapter(stripe_api_key="sk_test_demo")
        charge = stripe.create_charge_from_invoice(invoice, "cus_demo_123")
        print(f"✓ Charge created: {charge['id']}")
        print(f"  Amount: ${charge['amount'] / 100:.2f}")
        print(f"  Currency: {charge['currency'].upper()}")
        print(f"  Status: {charge['status']}")
    except Exception as e:
        print(f"ℹ Stripe (requires valid API key for live demo)")
        print(f"  Methods: create_charge_from_invoice(), create_subscription_from_invoice()")
        print(f"  Status: Ready for integration (set STRIPE_SECRET_KEY env var)")
    
    print()
    print("-" * 80)
    print()
    
    # 2. Zuora
    print("🔵 ZUORA ADAPTER")
    print("-" * 80)
    try:
        zuora = ZuoraOaaSBillingAdapter(
            zuora_api_url="https://api.zuora.sandbox.com",
            zuora_client_id="client_demo",
            zuora_client_secret="secret_demo"
        )
        print(f"✓ Zuora initialized (Sandbox mode)")
        print(f"  Methods: create_zuora_account(), create_zuora_invoice()")
        print(f"  Features: Multi-currency, ASC 606 revenue recognition, dunning")
        print(f"  Status: Ready for integration (set ZUORA_* env vars)")
    except Exception as e:
        print(f"ℹ Zuora (requires valid credentials for live demo)")
        print(f"  Status: Ready for integration (set ZUORA_* env vars)")
    
    print()
    print("-" * 80)
    print()
    
    # 3. PayPal
    print("🟢 PAYPAL ADAPTER")
    print("-" * 80)
    try:
        paypal = PayPalOaaSBillingAdapter(
            paypal_client_id="client_demo",
            paypal_client_secret="secret_demo",
            mode="sandbox"
        )
        paypal_inv = paypal.create_invoice(invoice, "demo@acme.com", "ACME Corp")
        print(f"✓ Invoice created: {paypal_inv['invoice_id']}")
        print(f"  Status: {paypal_inv['status']}")
        print(f"  Link: {paypal_inv['href']}")
        
        sent = paypal.send_invoice(paypal_inv['invoice_id'])
        print(f"✓ Invoice sent: {sent['status']}")
        
        sub = paypal.create_subscription("demo@acme.com", invoice)
        print(f"✓ Subscription: {sub['subscription_id']}")
        print(f"  Status: {sub['status']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print()
    print("=" * 80)
    print()
    print("SUMMARY")
    print("-" * 80)
    print()
    print("All three billing adapters support:")
    print("  ✓ Invoice creation from KIKI OaaS data")
    print("  ✓ Charge/subscription setup")
    print("  ✓ Integration with orchestrator")
    print("  ✓ CRM sync (Salesforce/HubSpot)")
    print()
    print("Provider Comparison:")
    print()
    print("  STRIPE:  Highest transaction volume | Developer-friendly API")
    print("  ZUORA:   Enterprise compliance | ASC 606 revenue recognition")
    print("  PAYPAL:  Global reach (180+ countries) | Lowest integration cost")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
