"""
KIKI Zuora Integration: Enterprise billing for OaaS profit-share invoices.
"""

from typing import Dict, Optional
from datetime import datetime
import json
import httpx

class ZuoraOaaSBillingAdapter:
    """
    Adapter to sync KIKI OaaS invoices with Zuora.
    
    Zuora is ideal for:
    - Multi-currency, multi-country billing
    - Complex revenue recognition (ASC 606)
    - Dunning management and retry logic
    - Automated invoice generation and tax handling
    
    Workflow:
    1. Create Account in Zuora for each client
    2. Generate Invoice via KIKI engine
    3. Call create_zuora_invoice() to push invoice to Zuora
    4. Zuora handles payment collection, reconciliation, revenue rec.
    """
    
    def __init__(self, zuora_api_url: str, zuora_client_id: str, zuora_client_secret: str):
        """
        Initialize Zuora adapter.
        
        Args:
            zuora_api_url: Zuora REST API endpoint (e.g., https://api.zuora.com)
            zuora_client_id: OAuth2 client ID
            zuora_client_secret: OAuth2 client secret
        """
        self.api_url = zuora_api_url
        self.client_id = zuora_client_id
        self.client_secret = zuora_client_secret
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """Obtain OAuth2 access token for Zuora API."""
        auth_endpoint = f"{self.api_url}/oauth/token"
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        
        # In production, use httpx or requests to call Zuora
        # For now, mock success
        print("✓ Zuora authentication successful (mock)")
        self.access_token = "mock_token_xxxxx"
    
    def create_zuora_account(self, client_id: str, client_email: str) -> Dict:
        """
        Create a Zuora Account for a KIKI client.
        
        Args:
            client_id: KIKI client identifier
            client_email: Client contact email
        
        Returns:
            Zuora Account object
        """
        account_payload = {
            "name": f"KIKI Client - {client_id}",
            "currency": "USD",
            "status": "Active",
            "billCycleDay": 1,  # Bill on 1st of month
            "contactInfo": {
                "email": client_email,
                "zipCode": "00000",  # Placeholder
            },
            "invoiceDeliveryPrefs": {
                "invoiceDeliveryFormat": ["PDF"],
                "invoiceDeliveryFrequency": "Monthly",
            },
        }
        
        # Mock Zuora response
        return {
            "success": True,
            "accountId": f"zuora_acct_{client_id}",
            "payload": account_payload,
        }
    
    def create_zuora_invoice(
        self,
        invoice_data: Dict,
        zuora_account_id: str,
    ) -> Dict:
        """
        Push KIKI OaaS invoice to Zuora for management.
        
        Args:
            invoice_data: Invoice from KIKIOaaSBillingEngine.generate_invoice()
            zuora_account_id: Zuora Account ID (from create_zuora_account)
        
        Returns:
            Zuora Invoice object
        """
        invoice_items = []
        for line_item in invoice_data["line_items"]:
            invoice_items.append({
                "chargeAmount": line_item["kiki_earnings"],
                "description": (
                    f"KIKI OaaS Profit-Share: {line_item['margin_improvement_pct']:.1f}% "
                    f"margin improvement ({line_item['client_id']})"
                ),
                "serviceStartDate": line_item["period_start"],
                "serviceEndDate": line_item["period_end"],
            })
        
        zuora_invoice_payload = {
            "accountId": zuora_account_id,
            "invoiceDate": invoice_data["issue_date"],
            "dueDate": (
                datetime.fromisoformat(invoice_data["issue_date"]) + 
                datetime.timedelta(days=30)
            ).isoformat(),
            "invoiceItems": invoice_items,
            "status": "Draft",  # Will be sent for approval/payment
            "comments": (
                f"KIKI OaaS Invoice: {invoice_data['summary']['total_margin_improvement']:.1f}% "
                f"avg margin improvement"
            ),
        }
        
        # Mock Zuora response
        return {
            "success": True,
            "invoiceId": f"zuora_inv_{invoice_data['invoice_id']}",
            "payload": zuora_invoice_payload,
            "status": "POSTED",
        }
    
    def publish_invoice_for_collection(self, zuora_invoice_id: str) -> Dict:
        """
        Publish invoice in Zuora (moves from draft → posted → sent for payment).
        
        Args:
            zuora_invoice_id: Zuora Invoice ID
        
        Returns:
            Updated Zuora Invoice
        """
        return {
            "success": True,
            "invoiceId": zuora_invoice_id,
            "status": "POSTED",
            "paymentStatus": "Not Yet Due",
            "timestamp": datetime.now().isoformat(),
        }
    
    def sync_payment(self, zuora_invoice_id: str, amount: float) -> Dict:
        """
        Record payment received (Zuora → KIKI accounting).
        
        Args:
            zuora_invoice_id: Zuora Invoice ID
            amount: Amount paid
        
        Returns:
            Payment record
        """
        return {
            "zuora_invoice_id": zuora_invoice_id,
            "amount_received": amount,
            "status": "RECEIVED",
            "timestamp": datetime.now().isoformat(),
        }

# Example usage
if __name__ == "__main__":
    import os
    
    zuora_url = os.getenv("ZUORA_API_URL", "https://api.zuora.sandbox.com")
    zuora_client_id = os.getenv("ZUORA_CLIENT_ID", "client_id_example")
    zuora_secret = os.getenv("ZUORA_CLIENT_SECRET", "secret_example")
    
    adapter = ZuoraOaaSBillingAdapter(zuora_url, zuora_client_id, zuora_secret)
    
    # Create account for a new client
    account = adapter.create_zuora_account("acme_corp_123", "billing@acme.com")
    print(f"✓ Zuora Account Created: {account['accountId']}")
    
    # Mock invoice
    invoice = {
        "invoice_id": "INV-2026-DEMO-001",
        "issue_date": "2026-01-18T00:00:00",
        "summary": {"total_margin_improvement": 45.0},
        "line_items": [
            {
                "client_id": "acme_corp_123",
                "kiki_earnings": 32.29,
                "margin_improvement_pct": 45.0,
                "period_start": "2026-01-11T00:00:00",
                "period_end": "2026-01-18T00:00:00",
            }
        ],
    }
    
    # Create and publish invoice
    zuora_inv = adapter.create_zuora_invoice(invoice, account["accountId"])
    print(f"✓ Zuora Invoice Created: {zuora_inv['invoiceId']}")
    
    published = adapter.publish_invoice_for_collection(zuora_inv["invoiceId"])
    print(f"✓ Invoice Published: {published['status']}")
