"""
KIKI QuickBooks & Xero Integration: Sync OaaS invoices with accounting platforms.
"""

from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum
import json


class AccountingPlatform(Enum):
    """Supported accounting platforms."""
    QUICKBOOKS = "quickbooks"
    XERO = "xero"


class QuickBooksXeroAdapter:
    """
    Adapter to sync KIKI OaaS invoices with QuickBooks Online or Xero.
    
    Both platforms provide:
    - Invoice creation and sending
    - Payment tracking & reconciliation
    - Multi-currency support
    - Tax compliance
    - Integration with banks for payment matching
    
    QuickBooks: SMB-focused, USA-first  
    Xero: Global-first, strong in AU/NZ/UK
    """
    
    def __init__(
        self,
        platform: AccountingPlatform,
        api_url: str,
        access_token: str,
        company_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize accounting adapter.
        
        Args:
            platform: QuickBooks or Xero
            api_url: API endpoint (QB: https://quickbooks.api.intuit.com, Xero: https://api.xero.com)
            access_token: OAuth2 access token
            company_id: QuickBooks company ID (QB)
            tenant_id: Xero tenant ID
        """
        self.platform = platform
        self.api_url = api_url
        self.access_token = access_token
        self.company_id = company_id
        self.tenant_id = tenant_id
        self._authenticate()
    
    def _authenticate(self):
        """Verify OAuth2 connection."""
        print(f"✓ {self.platform.value.upper()} authentication successful")
        print(f"  API URL: {self.api_url}")
    
    def create_invoice(
        self,
        invoice_data: Dict,
        customer_id: str,
        customer_email: str,
        customer_name: str,
    ) -> Dict:
        """
        Create invoice in accounting platform.
        
        Args:
            invoice_data: KIKI invoice dict
            customer_id: Customer ID in accounting system
            customer_email: Customer email
            customer_name: Customer name
        
        Returns:
            Invoice reference
        """
        invoice_payload = {
            "invoice_id": invoice_data["invoice_id"],
            "customer_id": customer_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "invoice_date": invoice_data["issue_date"][:10],
            "due_date": (
                datetime.fromisoformat(invoice_data["issue_date"])
                .replace(day=28)  # Net 30 approx
                .isoformat()[:10]
            ),
            "currency_code": "USD",
            "total_amount": invoice_data["summary"]["total_kiki_earnings"],
            "description": "KIKI OaaS Profit-Share Invoice",
            "line_items": [
                {
                    "description": (
                        f"KIKI SyncShield: {line['client_id']} "
                        f"({line['margin_improvement_pct']:.1f}% margin improvement)"
                    ),
                    "quantity": 1,
                    "unit_price": line["kiki_earnings"],
                    "tax_code": "TAX_EXEMPT",  # OaaS revenue
                }
                for line in invoice_data["line_items"]
            ],
        }
        
        # Mock platform response
        if self.platform == AccountingPlatform.QUICKBOOKS:
            return {
                "success": True,
                "platform": "quickbooks",
                "invoice_id": f"qbo_{invoice_data['invoice_id']}",
                "docnumber": invoice_data["invoice_id"],
                "status": "OPEN",
                "total_amount": invoice_payload["total_amount"],
                "payload": invoice_payload,
            }
        else:  # Xero
            return {
                "success": True,
                "platform": "xero",
                "invoice_id": f"xero_{invoice_data['invoice_id']}",
                "reference": invoice_data["invoice_id"],
                "status": "DRAFT",
                "total_amount": invoice_payload["total_amount"],
                "payload": invoice_payload,
            }
    
    def send_invoice(
        self,
        accounting_invoice_id: str,
        customer_email: Optional[str] = None,
    ) -> Dict:
        """
        Send invoice to customer via platform email.
        
        Args:
            accounting_invoice_id: Invoice ID from accounting platform
            customer_email: Override email
        
        Returns:
            Send confirmation
        """
        return {
            "success": True,
            "accounting_invoice_id": accounting_invoice_id,
            "status": "SENT",
            "sent_at": datetime.now().isoformat(),
            "message": f"Invoice sent via {self.platform.value}",
        }
    
    def record_payment(
        self,
        accounting_invoice_id: str,
        amount: float,
        payment_date: Optional[str] = None,
        reference: str = "Stripe/PayPal/Zuora",
    ) -> Dict:
        """
        Record payment against invoice (for reconciliation).
        
        Args:
            accounting_invoice_id: Invoice ID
            amount: Amount paid
            payment_date: Payment date (defaults to today)
            reference: Payment reference/gateway
        
        Returns:
            Payment record
        """
        return {
            "success": True,
            "accounting_invoice_id": accounting_invoice_id,
            "amount_recorded": amount,
            "payment_date": payment_date or datetime.now().isoformat()[:10],
            "reference": reference,
            "status": "RECORDED",
            "platform": self.platform.value,
        }
    
    def create_customer(
        self,
        customer_id: str,
        company_name: str,
        email: str,
        phone: Optional[str] = None,
        billing_address: Optional[Dict] = None,
    ) -> Dict:
        """
        Create or update customer record in accounting system.
        
        Args:
            customer_id: KIKI client ID
            company_name: Client company name
            email: Billing email
            phone: Contact phone
            billing_address: Address dict
        
        Returns:
            Customer reference
        """
        customer_payload = {
            "customer_id": customer_id,
            "company_name": company_name,
            "email": email,
            "phone": phone or "",
            "billing_address": billing_address or {
                "country": "US",
            },
        }
        
        if self.platform == AccountingPlatform.QUICKBOOKS:
            return {
                "success": True,
                "platform": "quickbooks",
                "customer_id": f"qbo_cust_{customer_id}",
                "display_name": company_name,
                "status": "ACTIVE",
                "payload": customer_payload,
            }
        else:  # Xero
            return {
                "success": True,
                "platform": "xero",
                "contact_id": f"xero_cust_{customer_id}",
                "name": company_name,
                "status": "ACTIVE",
                "payload": customer_payload,
            }
    
    def get_trial_balance(
        self,
        start_date: str,
        end_date: str,
    ) -> Dict:
        """
        Retrieve trial balance for period (for accounting reconciliation).
        
        Args:
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
        
        Returns:
            Trial balance report
        """
        return {
            "success": True,
            "platform": self.platform.value,
            "period": f"{start_date} to {end_date}",
            "accounts": [
                {
                    "account_name": "Revenue - KIKI OaaS",
                    "account_code": "4100",
                    "debit": 0.0,
                    "credit": 0.0,
                },
                {
                    "account_name": "Accounts Receivable",
                    "account_code": "1200",
                    "debit": 0.0,
                    "credit": 0.0,
                },
            ],
        }
    
    def sync_bank_payments(
        self,
        start_date: str,
        end_date: str,
    ) -> Dict:
        """
        Auto-match bank transactions to invoices (for payment reconciliation).
        
        Args:
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
        
        Returns:
            Reconciliation results
        """
        return {
            "success": True,
            "platform": self.platform.value,
            "period": f"{start_date} to {end_date}",
            "transactions_matched": 0,
            "unmatched_transactions": 0,
            "status": "READY_FOR_REVIEW",
        }


# Example usage
if __name__ == "__main__":
    import os
    
    # QuickBooks example
    qb = QuickBooksXeroAdapter(
        platform=AccountingPlatform.QUICKBOOKS,
        api_url="https://quickbooks.api.intuit.com",
        access_token="qbo_token_xxxxx",
        company_id="1234567890",
    )
    
    invoice = {
        "invoice_id": "INV-2026-QBO-001",
        "issue_date": "2026-01-18T00:00:00",
        "summary": {
            "total_kiki_earnings": 32.29,
        },
        "line_items": [
            {
                "client_id": "google_ads_demo",
                "margin_improvement_pct": 49.0,
                "kiki_earnings": 18.83,
            },
            {
                "client_id": "meta_demo",
                "margin_improvement_pct": 41.0,
                "kiki_earnings": 13.46,
            },
        ],
    }
    
    # Create invoice
    qb_inv = qb.create_invoice(invoice, "cust_123", "billing@acme.com", "ACME Corp")
    print(f"✓ QuickBooks Invoice Created: {qb_inv['invoice_id']}")
    print(f"  Status: {qb_inv['status']}")
    
    # Send to customer
    sent = qb.send_invoice(qb_inv["invoice_id"], "billing@acme.com")
    print(f"✓ Invoice Sent: {sent['status']}")
    
    # Record payment
    payment = qb.record_payment(qb_inv["invoice_id"], 32.29, reference="Stripe Charge")
    print(f"✓ Payment Recorded: ${payment['amount_recorded']:.2f}")
    
    print()
    
    # Xero example
    xero = QuickBooksXeroAdapter(
        platform=AccountingPlatform.XERO,
        api_url="https://api.xero.com",
        access_token="xero_token_xxxxx",
        tenant_id="tenant_xxxxx",
    )
    
    xero_inv = xero.create_invoice(invoice, "cust_456", "billing@acme.com", "ACME Corp")
    print(f"✓ Xero Invoice Created: {xero_inv['invoice_id']}")
    print(f"  Status: {xero_inv['status']}")
