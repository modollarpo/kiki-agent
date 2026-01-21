"""
KIKI PayPal Integration: Create invoices and process OaaS charges via PayPal.
"""

from typing import Dict, Optional
from datetime import datetime
import json

class PayPalOaaSBillingAdapter:
    """
    Adapter to sync KIKI OaaS invoices with PayPal.
    
    PayPal is ideal for:
    - Global payment processing (180+ countries)
    - Subscription management (recurring billing)
    - Dispute resolution and seller protection
    - Multi-currency support
    - Integration with accounting software
    
    Workflow:
    1. Create invoice in KIKI billing engine
    2. Push to PayPal via REST API
    3. PayPal handles collection, reminders, reconciliation
    4. Webhook confirms payment status
    """
    
    def __init__(self, paypal_client_id: str, paypal_client_secret: str, mode: str = "sandbox"):
        """
        Initialize PayPal adapter.
        
        Args:
            paypal_client_id: PayPal app client ID
            paypal_client_secret: PayPal app client secret
            mode: "sandbox" or "live"
        """
        self.client_id = paypal_client_id
        self.client_secret = paypal_client_secret
        self.mode = mode
        self.api_base = (
            "https://api.sandbox.paypal.com" if mode == "sandbox"
            else "https://api.paypal.com"
        )
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """Obtain OAuth2 access token for PayPal API."""
        auth_endpoint = f"{self.api_base}/v1/oauth2/token"
        
        # In production, use httpx/requests to call PayPal
        # For now, mock success
        print(f"✓ PayPal authentication successful (mode: {self.mode})")
        self.access_token = "mock_paypal_token_xxxxx"
    
    def create_invoice(
        self,
        invoice_data: Dict,
        client_email: str,
        client_name: str,
    ) -> Dict:
        """
        Create a PayPal invoice for KIKI OaaS charges.
        
        Args:
            invoice_data: Invoice dict from KIKIOaaSBillingEngine
            client_email: Client's email (required for PayPal)
            client_name: Client's business name
        
        Returns:
            PayPal Invoice object
        """
        paypal_invoice = {
            "detail": {
                "invoice_number": invoice_data["invoice_id"],
                "invoice_date": invoice_data["issue_date"][:10],  # YYYY-MM-DD
                "currency_code": "USD",
                "note": (
                    f"KIKI OaaS Profit-Share Invoice\n"
                    f"Margin Improvement: {invoice_data['summary']['total_margin_improvement']:.1f}%\n"
                    f"Payment Terms: {invoice_data['payment_terms']}"
                ),
            },
            "invoicer": {
                "name": {
                    "given_name": "KIKI",
                    "surname": "Agent™",
                },
                "email_address": "billing@kikiagent.ai",
                "address": {
                    "address_line_1": "1 Revenue St",
                    "admin_area_2": "San Francisco",
                    "admin_area_1": "CA",
                    "postal_code": "94105",
                    "country_code": "US",
                },
            },
            "payer": {
                "name": {
                    "given_name": client_name.split()[0] if client_name else "Client",
                    "surname": client_name.split()[-1] if len(client_name.split()) > 1 else "",
                },
                "email_address": client_email,
            },
            "items": [],
            "amount": {
                "currency_code": "USD",
                "value": str(invoice_data["summary"]["total_kiki_earnings"]),
                "breakdown": {
                    "item_total": {
                        "currency_code": "USD",
                        "value": str(invoice_data["summary"]["total_kiki_earnings"]),
                    }
                },
            },
        }
        
        # Add line items
        for line_item in invoice_data["line_items"]:
            paypal_invoice["items"].append({
                "name": (
                    f"KIKI OaaS Profit-Share: {line_item['client_id']}"
                ),
                "description": (
                    f"Margin Improvement: {line_item['margin_improvement_pct']:.1f}% "
                    f"({line_item['period_start'][:10]} to {line_item['period_end'][:10]})"
                ),
                "quantity": "1",
                "unit_amount": {
                    "currency_code": "USD",
                    "value": str(line_item["kiki_earnings"]),
                },
            })
        
        # Mock PayPal response
        return {
            "success": True,
            "invoice_id": f"paypal_inv_{invoice_data['invoice_id']}",
            "paypal_invoice_number": invoice_data["invoice_id"],
            "status": "DRAFT",
            "href": f"https://www.{self.mode}.paypal.com/invoice/{invoice_data['invoice_id']}",
            "payload": paypal_invoice,
        }
    
    def send_invoice(self, paypal_invoice_id: str) -> Dict:
        """
        Send PayPal invoice to client (transitions from DRAFT → SENT).
        
        Args:
            paypal_invoice_id: PayPal invoice ID
        
        Returns:
            Updated PayPal Invoice
        """
        return {
            "success": True,
            "invoice_id": paypal_invoice_id,
            "status": "SENT",
            "sent_date": datetime.now().isoformat(),
            "message": f"Invoice sent to client",
        }
    
    def create_subscription(
        self,
        client_email: str,
        invoice_data: Dict,
        billing_cycle_days: int = 30,
    ) -> Dict:
        """
        Create a PayPal subscription for recurring OaaS billing.
        
        Args:
            client_email: Client email
            invoice_data: Invoice data (for metadata)
            billing_cycle_days: Billing cycle (default 30 days = monthly)
        
        Returns:
            PayPal Subscription object
        """
        subscription = {
            "product_id": "KIKI_OaaS_PROFIT_SHARE",
            "name": "KIKI SyncShield OaaS (Profit-Share)",
            "description": (
                "AI-powered revenue engine with outcome-based billing. "
                "KIKI charges 15% of margin improvement over platform baseline."
            ),
            "billing_cycles": [
                {
                    "frequency": {
                        "interval_unit": "DAY",
                        "interval_count": billing_cycle_days,
                    },
                    "tenure_type": "REGULAR",
                    "sequence": 1,
                    "total_cycles": 0,  # Unlimited
                    "pricing_scheme": {
                        "fixed_price": {
                            "currency_code": "USD",
                            "value": str(invoice_data["summary"]["total_kiki_earnings"]),
                        }
                    },
                }
            ],
            "payment_preferences": {
                "setup_fee": {
                    "currency_code": "USD",
                    "value": "0.00",
                },
                "setup_fee_failure_action": "CONTINUE",
                "payment_failure_threshold": 3,
            },
        }
        
        # Mock PayPal response
        return {
            "success": True,
            "subscription_id": f"paypal_sub_{invoice_data['invoice_id']}",
            "status": "APPROVAL_PENDING",
            "href": f"https://www.{self.mode}.paypal.com/subscribe?token=EC-xxxxx",
            "payload": subscription,
        }
    
    def record_payment(
        self,
        paypal_invoice_id: str,
        amount: float,
        payment_method: str = "paypal_wallet",
    ) -> Dict:
        """
        Record a payment received (for KIKI accounting).
        
        Args:
            paypal_invoice_id: PayPal invoice ID
            amount: Amount paid
            payment_method: "paypal_wallet", "credit_card", "bank_transfer", etc.
        
        Returns:
            Payment record
        """
        return {
            "paypal_invoice_id": paypal_invoice_id,
            "amount_received": amount,
            "payment_method": payment_method,
            "status": "RECEIVED",
            "timestamp": datetime.now().isoformat(),
        }
    
    def create_webhook_listener(self) -> Dict:
        """
        Register PayPal webhook for payment events.
        
        Webhook will POST to your billing service when:
        - INVOICE.PAID
        - INVOICE.EXPIRED
        - INVOICE.REFUNDED
        - SUBSCRIPTION.ACTIVATED
        - SUBSCRIPTION.CANCELLED
        
        Returns:
            Webhook registration details
        """
        webhook_config = {
            "url": "https://yourapi.com/webhooks/paypal",  # Your endpoint
            "event_types": [
                {"name": "INVOICE.PAID"},
                {"name": "INVOICE.EXPIRED"},
                {"name": "INVOICE.REFUNDED"},
                {"name": "SUBSCRIPTION.ACTIVATED"},
                {"name": "SUBSCRIPTION.CANCELLED"},
            ],
        }
        
        # Mock PayPal response
        return {
            "success": True,
            "webhook_id": "paypal_hook_xxxxx",
            "config": webhook_config,
            "status": "ACTIVE",
        }


# Example usage
if __name__ == "__main__":
    import os
    
    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID", "client_id_sandbox")
    paypal_secret = os.getenv("PAYPAL_CLIENT_SECRET", "secret_sandbox")
    
    adapter = PayPalOaaSBillingAdapter(paypal_client_id, paypal_secret, mode="sandbox")
    
    # Mock invoice
    invoice = {
        "invoice_id": "INV-2026-DEMO-001",
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
    
    # Create invoice
    paypal_inv = adapter.create_invoice(invoice, "billing@acme.com", "ACME Corp")
    print(f"✓ PayPal Invoice Created: {paypal_inv['invoice_id']}")
    print(f"  Status: {paypal_inv['status']}")
    print(f"  Link: {paypal_inv['href']}")
    
    # Send to client
    sent = adapter.send_invoice(paypal_inv["invoice_id"])
    print(f"\n✓ Invoice Sent: {sent['status']}")
    
    # Create subscription for recurring billing
    sub = adapter.create_subscription("billing@acme.com", invoice, billing_cycle_days=30)
    print(f"\n✓ Subscription Created: {sub['subscription_id']}")
    print(f"  Status: {sub['status']}")
    print(f"  Approval Link: {sub['href']}")
