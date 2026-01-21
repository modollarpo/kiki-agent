"""
Quick demo: Generate and process an OaaS invoice via PayPal.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from paypal_adapter import PayPalOaaSBillingAdapter


def main():
    """Generate and process OaaS invoice via PayPal."""
    
    print("=" * 70)
    print("KIKI OaaS Billing Demo: PayPal Integration")
    print("=" * 70)
    print()
    
    # Initialize PayPal adapter
    adapter = PayPalOaaSBillingAdapter(
        paypal_client_id="demo_client_id",
        paypal_client_secret="demo_secret",
        mode="sandbox"
    )
    print("✓ PayPal Adapter Initialized (Sandbox Mode)")
    print()
    
    # Mock OaaS invoice
    invoice = {
        "invoice_id": "INV-2026-PAYPAL-001",
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
    
    print(f"📋 Invoice ID: {invoice['invoice_id']}")
    print(f"   Total Earnings: ${invoice['summary']['total_kiki_earnings']:.2f}")
    print(f"   Avg Margin Improvement: {invoice['summary']['total_margin_improvement']:.1f}%")
    print()
    
    # Create PayPal invoice
    print("Creating PayPal invoice...")
    paypal_inv = adapter.create_invoice(invoice, "billing@acme.com", "ACME Corp")
    print(f"✓ Invoice Created: {paypal_inv['invoice_id']}")
    print(f"  Status: {paypal_inv['status']}")
    print(f"  PayPal Link: {paypal_inv['href']}")
    print()
    
    # Send to client
    print("Sending to client...")
    sent = adapter.send_invoice(paypal_inv["invoice_id"])
    print(f"✓ Invoice Status: {sent['status']}")
    print(f"  Sent at: {sent['sent_date']}")
    print()
    
    # Create subscription
    print("Creating recurring subscription...")
    sub = adapter.create_subscription("billing@acme.com", invoice, billing_cycle_days=30)
    print(f"✓ Subscription Created: {sub['subscription_id']}")
    print(f"  Status: {sub['status']}")
    print(f"  Approval URL: {sub['href']}")
    print()
    
    # Setup webhook
    print("Registering webhook for payment events...")
    webhook = adapter.create_webhook_listener()
    print(f"✓ Webhook Registered: {webhook['webhook_id']}")
    print(f"  Events: INVOICE.PAID, INVOICE.EXPIRED, SUBSCRIPTION.ACTIVATED")
    print()
    
    print("=" * 70)
    print("✓ PayPal integration ready!")
    print("=" * 70)


if __name__ == "__main__":
    main()
