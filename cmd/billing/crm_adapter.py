"""
KIKI CRM Integration: Push billing data to Salesforce/HubSpot for sales/customer success reporting.
"""

from typing import Dict, Optional
from datetime import datetime
import json

class SalesforceOaaSIntegration:
    """
    Sync KIKI OaaS billing and performance metrics to Salesforce.
    
    Use cases:
    - Sales can see realized margin improvement per account
    - CS team tracks KIKI ROI and performance trends
    - Forecasting: project KIKI earnings over contract lifetime
    - Churn prevention: flag accounts with declining ROAS
    """
    
    def __init__(self, salesforce_instance: str, salesforce_api_token: str):
        """
        Initialize Salesforce adapter.
        
        Args:
            salesforce_instance: Salesforce instance URL (e.g., https://myorg.salesforce.com)
            salesforce_api_token: OAuth2 token or session ID
        """
        self.instance = salesforce_instance
        self.token = salesforce_api_token
    
    def create_or_update_opportunity(
        self,
        salesforce_account_id: str,
        invoice_data: Dict,
    ) -> Dict:
        """
        Create/update Salesforce Opportunity with KIKI OaaS deal.
        
        Args:
            salesforce_account_id: Salesforce Account ID
            invoice_data: Invoice from KIKI billing engine
        
        Returns:
            Salesforce Opportunity record
        """
        opportunity = {
            "Name": f"KIKI OaaS - {invoice_data['invoice_id']}",
            "AccountId": salesforce_account_id,
            "Amount": invoice_data["summary"]["total_kiki_earnings"],
            "StageName": "Closed Won",
            "CloseDate": datetime.now().strftime("%Y-%m-%d"),
            "Description": (
                f"KIKI OaaS Profit-Share Invoice\n"
                f"Period: {invoice_data['line_items'][0]['period_start']} to "
                f"{invoice_data['line_items'][0]['period_end']}\n"
                f"Avg Margin Improvement: {invoice_data['summary']['total_margin_improvement']:.1f}%"
            ),
            # Custom fields
            "KIKI_Margin_Improvement__c": invoice_data["summary"]["total_margin_improvement"],
            "KIKI_Invoice_ID__c": invoice_data["invoice_id"],
        }
        
        # Mock Salesforce response
        return {
            "success": True,
            "opportunityId": f"006xx000003DHk_KIKI_{invoice_data['invoice_id']}",
            "opportunity": opportunity,
        }
    
    def update_account_metrics(
        self,
        salesforce_account_id: str,
        client_metrics: Dict,
    ) -> Dict:
        """
        Update Account record with latest KIKI performance metrics.
        
        Args:
            salesforce_account_id: Salesforce Account ID
            client_metrics: Client metrics dict (from audit trail aggregation)
        
        Returns:
            Updated Salesforce Account
        """
        account_update = {
            "Id": salesforce_account_id,
            # Standard fields
            "Description": f"KIKI OaaS enabled | Accuracy: {client_metrics['accuracy_pct']:.1f}%",
            # Custom fields
            "KIKI_Status__c": "Active",
            "KIKI_Accuracy_Pct__c": client_metrics["accuracy_pct"],
            "KIKI_Total_Spend__c": client_metrics["total_spend"] / 1_000_000,  # Convert micros to $
            "KIKI_Requests_Count__c": client_metrics["requests_count"],
            "KIKI_Circuit_Trips__c": client_metrics["circuit_trips"],
            "KIKI_Fallback_Activations__c": client_metrics["fallback_activations"],
        }
        
        # Mock Salesforce response
        return {
            "success": True,
            "accountId": salesforce_account_id,
            "account": account_update,
        }
    
    def create_revenue_record(
        self,
        salesforce_account_id: str,
        invoice_data: Dict,
    ) -> Dict:
        """
        Create Revenue Recognition record for ASC 606 compliance.
        
        Args:
            salesforce_account_id: Salesforce Account ID
            invoice_data: Invoice data
        
        Returns:
            Revenue record
        """
        revenue_record = {
            "AccountId": salesforce_account_id,
            "Amount": invoice_data["summary"]["total_kiki_earnings"],
            "RecognitionDate": datetime.now().strftime("%Y-%m-%d"),
            "RevenueType": "KIKI_OaaS_ProfitShare",
            "InvoiceId": invoice_data["invoice_id"],
            "Status": "Recognized",
        }
        
        return {
            "success": True,
            "revenueRecordId": f"revrecord_{invoice_data['invoice_id']}",
            "record": revenue_record,
        }


class HubSpotOaaSIntegration:
    """
    Sync KIKI OaaS billing to HubSpot for CSM and community reporting.
    
    HubSpot excels at:
    - Deal tracking and forecasting
    - Custom properties for KIKI metrics
    - Reporting/dashboards for sales/CS teams
    - Automated workflows based on KIKI performance
    """
    
    def __init__(self, hubspot_api_key: str):
        """
        Initialize HubSpot adapter.
        
        Args:
            hubspot_api_key: HubSpot private app token
        """
        self.api_key = hubspot_api_key
    
    def create_or_update_deal(
        self,
        hubspot_contact_id: str,
        invoice_data: Dict,
    ) -> Dict:
        """
        Create/update HubSpot Deal for KIKI OaaS engagement.
        
        Args:
            hubspot_contact_id: HubSpot Contact ID
            invoice_data: Invoice from KIKI billing
        
        Returns:
            HubSpot Deal record
        """
        deal = {
            "properties": {
                "dealname": f"KIKI OaaS Revenue Share - {invoice_data['invoice_id']}",
                "dealstage": "closedwon",
                "amount": str(invoice_data["summary"]["total_kiki_earnings"]),
                "closedate": int(datetime.now().timestamp() * 1000),
                # Custom properties
                "kiki_margin_improvement": str(
                    invoice_data["summary"]["total_margin_improvement"]
                ),
                "kiki_invoice_id": invoice_data["invoice_id"],
                "kiki_period_start": invoice_data["line_items"][0]["period_start"],
                "kiki_period_end": invoice_data["line_items"][0]["period_end"],
            }
        }
        
        # Mock HubSpot response
        return {
            "success": True,
            "dealId": f"hubspot_deal_{invoice_data['invoice_id']}",
            "deal": deal,
        }
    
    def log_engagement_note(
        self,
        hubspot_contact_id: str,
        invoice_data: Dict,
    ) -> Dict:
        """
        Log engagement note for sales/CS teams.
        
        Args:
            hubspot_contact_id: HubSpot Contact ID
            invoice_data: Invoice data
        
        Returns:
            HubSpot Engagement (note) record
        """
        note = {
            "engagement": {
                "type": "NOTE",
                "timestamp": int(datetime.now().timestamp() * 1000),
            },
            "associations": {
                "contactIds": [hubspot_contact_id],
            },
            "metadata": {
                "body": (
                    f"KIKI OaaS Invoice {invoice_data['invoice_id']}\n"
                    f"Margin Improvement: {invoice_data['summary']['total_margin_improvement']:.1f}%\n"
                    f"KIKI Earnings: ${invoice_data['summary']['total_kiki_earnings']:.2f}\n"
                    f"Billing Period: {invoice_data['line_items'][0]['period_start']} to "
                    f"{invoice_data['line_items'][0]['period_end']}"
                ),
            },
        }
        
        # Mock HubSpot response
        return {
            "success": True,
            "engagementId": f"hubspot_note_{invoice_data['invoice_id']}",
            "engagement": note,
        }


# Example usage
if __name__ == "__main__":
    import os
    
    # Salesforce example
    sf_instance = os.getenv("SALESFORCE_INSTANCE", "https://myorg.salesforce.com")
    sf_token = os.getenv("SALESFORCE_API_TOKEN", "token_xxxxx")
    
    sf_adapter = SalesforceOaaSIntegration(sf_instance, sf_token)
    
    invoice = {
        "invoice_id": "INV-2026-DEMO-001",
        "summary": {
            "total_margin_improvement": 45.0,
            "total_kiki_earnings": 32.29,
        },
        "line_items": [
            {
                "period_start": "2026-01-11T00:00:00",
                "period_end": "2026-01-18T00:00:00",
            }
        ],
    }
    
    opp = sf_adapter.create_or_update_opportunity("001xx000003DLHAA2", invoice)
    print(f"✓ Salesforce Opportunity: {opp['opportunityId']}")
    
    # HubSpot example
    hs_api_key = os.getenv("HUBSPOT_API_KEY", "pat-xxxxx")
    hs_adapter = HubSpotOaaSIntegration(hs_api_key)
    
    deal = hs_adapter.create_or_update_deal("1001", invoice)
    print(f"✓ HubSpot Deal: {deal['dealId']}")
    
    note = hs_adapter.log_engagement_note("1001", invoice)
    print(f"✓ HubSpot Engagement: {note['engagementId']}")
