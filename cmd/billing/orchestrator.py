"""
KIKI Billing Orchestrator: Unified interface for OaaS invoice generation,
payment processing, and CRM sync.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

from ooaS_billing_engine import KIKIOaaSBillingEngine, ProfitShare


class BillingProvider(Enum):
    """Supported billing providers."""
    STRIPE = "stripe"
    ZUORA = "zuora"
    PAYPAL = "paypal"
    NONE = "none"  # Generate JSON only


class CRMProvider(Enum):
    """Supported CRM platforms."""
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    NONE = "none"  # No CRM sync


class KIKIBillingOrchestrator:
    """
    End-to-end orchestration: audit trail → invoice → payment processing → CRM.
    """
    
    def __init__(
        self,
        audit_csv_path: str,
        kiki_share_pct: float = 15.0,
        billing_provider: BillingProvider = BillingProvider.NONE,
        crm_provider: CRMProvider = CRMProvider.NONE,
    ):
        """
        Initialize orchestrator.
        
        Args:
            audit_csv_path: Path to shield_audit.csv
            kiki_share_pct: KIKI's cut of margin improvement (default 15%)
            billing_provider: Stripe, Zuora, or none
            crm_provider: Salesforce, HubSpot, or none
        """
        self.audit_path = audit_csv_path
        self.billing_engine = KIKIOaaSBillingEngine(kiki_share_pct=kiki_share_pct)
        self.billing_provider = billing_provider
        self.crm_provider = crm_provider
        
        # Load audit trail
        self.audit_df = self.billing_engine.load_audit_trail(audit_csv_path)
        
        # Optional: Initialize payment/CRM adapters
        self.stripe_adapter = None
        self.zuora_adapter = None
        self.paypal_adapter = None
        self.crm_adapter = None
        
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Initialize payment and CRM adapters based on config."""
        import os
        
        if self.billing_provider == BillingProvider.STRIPE:
            from stripe_adapter import StripeOaaSBillingAdapter
            stripe_key = os.getenv("STRIPE_SECRET_KEY")
            if stripe_key:
                self.stripe_adapter = StripeOaaSBillingAdapter(stripe_key)
        
        elif self.billing_provider == BillingProvider.ZUORA:
            from zuora_adapter import ZuoraOaaSBillingAdapter
            zuora_url = os.getenv("ZUORA_API_URL", "https://api.zuora.com")
            zuora_id = os.getenv("ZUORA_CLIENT_ID")
            zuora_secret = os.getenv("ZUORA_CLIENT_SECRET")
            if zuora_id and zuora_secret:
                self.zuora_adapter = ZuoraOaaSBillingAdapter(zuora_url, zuora_id, zuora_secret)
        
        elif self.billing_provider == BillingProvider.PAYPAL:
            from paypal_adapter import PayPalOaaSBillingAdapter
            paypal_id = os.getenv("PAYPAL_CLIENT_ID")
            paypal_secret = os.getenv("PAYPAL_CLIENT_SECRET")
            paypal_mode = os.getenv("PAYPAL_MODE", "sandbox")
            if paypal_id and paypal_secret:
                self.paypal_adapter = PayPalOaaSBillingAdapter(paypal_id, paypal_secret, mode=paypal_mode)
        
        if self.crm_provider == CRMProvider.SALESFORCE:
            from crm_adapter import SalesforceOaaSIntegration
            sf_instance = os.getenv("SALESFORCE_INSTANCE")
            sf_token = os.getenv("SALESFORCE_API_TOKEN")
            if sf_instance and sf_token:
                self.crm_adapter = SalesforceOaaSIntegration(sf_instance, sf_token)
        
        elif self.crm_provider == CRMProvider.HUBSPOT:
            from crm_adapter import HubSpotOaaSIntegration
            hs_key = os.getenv("HUBSPOT_API_KEY")
            if hs_key:
                self.crm_adapter = HubSpotOaaSIntegration(hs_key)
    
    def generate_monthly_invoices(
        self,
        billing_period_start: datetime,
        billing_period_end: datetime,
        baseline_roas: float = 3.0,
        client_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Generate invoices for all (or specified) clients in a period.
        
        Args:
            billing_period_start: Period start
            billing_period_end: Period end
            baseline_roas: Platform baseline ROAS (default 3.0x)
            client_ids: Optional list of client IDs; if None, bill all in audit trail
        
        Returns:
            List of invoice dicts
        """
        if client_ids is None:
            client_ids = list(self.audit_df["client_id"].unique())
        
        invoices = []
        profit_shares = []
        
        for client_id in client_ids:
            try:
                metrics = self.billing_engine.aggregate_client_metrics(
                    self.audit_df,
                    client_id,
                    billing_period_start,
                    billing_period_end,
                )
                ps = self.billing_engine.calculate_profit_share(metrics, baseline_roas)
                profit_shares.append(ps)
            except ValueError as e:
                print(f"⚠ {client_id}: {e}")
        
        if profit_shares:
            invoice = self.billing_engine.generate_invoice(
                profit_shares,
                invoice_id=f"INV-{datetime.now().strftime('%Y%m')}-001",
                issue_date=datetime.now(),
            )
            invoices.append(invoice)
        
        return invoices
    
    def process_invoice(
        self,
        invoice: Dict,
        customer_mappings: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """
        Process invoice through billing and CRM systems.
        
        Args:
            invoice: Invoice dict from generate_monthly_invoices()
            customer_mappings: Map client_id → stripe_customer_id or sf_account_id
        
        Returns:
            Processing result with status and references
        """
        result = {
            "invoice_id": invoice["invoice_id"],
            "status": "PROCESSING",
            "billing_result": None,
            "crm_result": None,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Process payment
        if self.stripe_adapter and customer_mappings:
            try:
                # Use first client's mapping as example
                first_client = invoice["line_items"][0]["client_id"]
                stripe_customer = customer_mappings.get(first_client)
                if stripe_customer:
                    charge = self.stripe_adapter.create_charge_from_invoice(
                        invoice, stripe_customer
                    )
                    result["billing_result"] = {
                        "provider": "stripe",
                        "charge_id": charge.id if hasattr(charge, "id") else "mock_charge",
                        "amount": invoice["summary"]["total_kiki_earnings"],
                    }
            except Exception as e:
                result["billing_result"] = {"provider": "stripe", "error": str(e)}
        
        elif self.zuora_adapter and customer_mappings:
            try:
                first_client = invoice["line_items"][0]["client_id"]
                zuora_account = customer_mappings.get(first_client)
                if zuora_account:
                    zuora_inv = self.zuora_adapter.create_zuora_invoice(
                        invoice, zuora_account
                    )
                    result["billing_result"] = {
                        "provider": "zuora",
                        "invoice_id": zuora_inv["invoiceId"],
                    }
            except Exception as e:
                result["billing_result"] = {"provider": "zuora", "error": str(e)}
        
        elif self.paypal_adapter and customer_mappings:
            try:
                first_client = invoice["line_items"][0]["client_id"]
                client_email = customer_mappings.get(first_client)
                if client_email:
                    paypal_inv = self.paypal_adapter.create_invoice(
                        invoice, client_email, first_client
                    )
                    result["billing_result"] = {
                        "provider": "paypal",
                        "invoice_id": paypal_inv["invoice_id"],
                        "status": paypal_inv["status"],
                        "paypal_url": paypal_inv["href"],
                    }
            except Exception as e:
                result["billing_result"] = {"provider": "paypal", "error": str(e)}
        
        # Sync to CRM
        if self.crm_adapter and customer_mappings:
            try:
                first_client = invoice["line_items"][0]["client_id"]
                crm_account = customer_mappings.get(first_client)
                if crm_account:
                    if self.crm_provider == CRMProvider.SALESFORCE:
                        opp = self.crm_adapter.create_or_update_opportunity(
                            crm_account, invoice
                        )
                        result["crm_result"] = {
                            "provider": "salesforce",
                            "opportunity_id": opp["opportunityId"],
                        }
                    elif self.crm_provider == CRMProvider.HUBSPOT:
                        deal = self.crm_adapter.create_or_update_deal(crm_account, invoice)
                        result["crm_result"] = {
                            "provider": "hubspot",
                            "deal_id": deal["dealId"],
                        }
            except Exception as e:
                result["crm_result"] = {"error": str(e)}
        
        result["status"] = "PROCESSED"
        return result
    
    def save_invoice(self, invoice: Dict, output_dir: str = "invoices") -> str:
        """Save invoice to JSON file."""
        Path(output_dir).mkdir(exist_ok=True)
        filepath = f"{output_dir}/{invoice['invoice_id']}.json"
        with open(filepath, "w") as f:
            json.dump(invoice, f, indent=2)
        return filepath


# Example workflow
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = KIKIBillingOrchestrator(
        audit_csv_path="shield_audit.csv",
        kiki_share_pct=15.0,
        billing_provider=BillingProvider.PAYPAL,  # or STRIPE, ZUORA, or NONE
        crm_provider=CRMProvider.SALESFORCE,  # or HUBSPOT, or NONE
    )
    
    # Generate invoices for last 30 days
    period_end = datetime.now()
    period_start = period_end - timedelta(days=30)
    
    print(f"📋 Generating invoices for {period_start.date()} to {period_end.date()}")
    invoices = orchestrator.generate_monthly_invoices(period_start, period_end)
    
    # Customer/account mappings (in real scenario, load from database)
    mappings = {
        "google_ads_demo": "cus_google_stripe",  # Stripe customer ID or SF account ID
        "meta_demo": "cus_meta_stripe",
    }
    
    # Process each invoice
    for invoice in invoices:
        print(f"\n💳 Processing {invoice['invoice_id']}")
        result = orchestrator.process_invoice(invoice, mappings)
        
        # Save to disk
        saved_path = orchestrator.save_invoice(invoice)
        print(f"  ✓ Saved: {saved_path}")
        
        if result["billing_result"]:
            print(f"  ✓ Billing: {result['billing_result']}")
        if result["crm_result"]:
            print(f"  ✓ CRM: {result['crm_result']}")
