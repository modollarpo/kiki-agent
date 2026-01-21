#!/usr/bin/env python3
"""
KIKI OaaS Billing Demo Runner
Generates sample OaaS invoice with optional Stripe/Zuora/CRM integration.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

def load_env_file(env_path: str):
    """Load .env file into environment."""
    if Path(env_path).exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        print("✓ Loaded environment from .env")

def generate_demo_invoice():
    """Generate sample OaaS invoice for demo."""
    demo_invoice = {
        "invoice_id": f"INV-{datetime.now().strftime('%Y%m%d')}-DEMO",
        "issue_date": datetime.now().isoformat(),
        "line_items": [
            {
                "client_id": "google_ads_demo",
                "period_start": (datetime.now() - timedelta(days=7)).isoformat(),
                "period_end": datetime.now().isoformat(),
                "baseline_roas": 3.0,
                "kiki_roas": 4.47,
                "margin_improvement_pct": 49.0,
                "additional_revenue": 125.50,
                "kiki_share_pct": 15,
                "kiki_earnings": 18.83,
            },
            {
                "client_id": "meta_demo",
                "period_start": (datetime.now() - timedelta(days=7)).isoformat(),
                "period_end": datetime.now().isoformat(),
                "baseline_roas": 3.0,
                "kiki_roas": 4.23,
                "margin_improvement_pct": 41.0,
                "additional_revenue": 89.75,
                "kiki_share_pct": 15,
                "kiki_earnings": 13.46,
            },
        ],
        "summary": {
            "total_clients": 2,
            "total_margin_improvement": 45.0,
            "total_additional_revenue": 215.25,
            "total_kiki_earnings": 32.29,
            "kiki_share_pct": 15,
        },
        "payment_terms": "Net 30",
        "status": "ISSUED",
    }
    
    return demo_invoice

def main():
    # Load environment
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        load_env_file(str(env_file))
    
    # Get command-line args
    billing_provider = sys.argv[1] if len(sys.argv) > 1 else "none"
    crm_provider = sys.argv[2] if len(sys.argv) > 2 else "none"
    dry_run = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
    
    print("")
    print("🚀 KIKI OaaS Billing Engine - Demo Runner")
    print("=" * 50)
    print("")
    print(f"Configuration:")
    print(f"  Billing Provider: {billing_provider}")
    print(f"  CRM Provider: {crm_provider}")
    print(f"  DRY RUN: {dry_run}")
    print(f"  KIKI Share: {os.getenv('KIKI_SHARE_PCT', '15')}%")
    print(f"  Baseline ROAS: {os.getenv('BASELINE_ROAS', '3.0')}x")
    print("")
    
    # Check for audit trail
    audit_path = Path(__file__).parent.parent.parent / "shield_audit.csv"
    
    if not audit_path.exists():
        print("📝 Audit trail not found; generating demo invoice...")
        print("")
        
        demo_invoice = generate_demo_invoice()
        
        # Display invoice
        print(json.dumps(demo_invoice, indent=2))
        
        # Save to invoices
        invoices_dir = Path(__file__).parent.parent.parent / "invoices"
        invoices_dir.mkdir(exist_ok=True)
        
        inv_path = invoices_dir / f"{demo_invoice['invoice_id']}.json"
        with open(inv_path, "w") as f:
            json.dump(demo_invoice, f, indent=2)
        
        print(f"\n✓ Demo invoice saved to: {inv_path}")
        
        # Show processing
        if billing_provider != "none":
            print(f"\n💳 Billing Processing (DRY RUN: {dry_run}):")
            if billing_provider == "stripe":
                print(f"  - Would create Stripe charge: ${demo_invoice['summary']['total_kiki_earnings']:.2f}")
                print(f"    Charge description: KIKI OaaS {demo_invoice['invoice_id']}")
                print(f"    Metadata: invoice_id, margin_improvement, period dates")
            elif billing_provider == "zuora":
                print(f"  - Would create Zuora invoice: ${demo_invoice['summary']['total_kiki_earnings']:.2f}")
                print(f"    Account: Zuora demo account")
                print(f"    Items: Profit-share charges for 2 clients")
        
        if crm_provider != "none":
            print(f"\n📊 CRM Sync (DRY RUN: {dry_run}):")
            if crm_provider == "salesforce":
                print(f"  - Would create Salesforce Opportunity: {demo_invoice['invoice_id']}")
                print(f"    Amount: ${demo_invoice['summary']['total_kiki_earnings']:.2f}")
                print(f"    Custom Fields: KIKI_Margin_Improvement, KIKI_Invoice_ID")
            elif crm_provider == "hubspot":
                print(f"  - Would create HubSpot Deal: {demo_invoice['invoice_id']}")
                print(f"    Amount: ${demo_invoice['summary']['total_kiki_earnings']:.2f}")
                print(f"  - Would log engagement note with billing details")
        
        print(f"\n✅ Invoice ready for payment/sync")
        print(f"   File: {inv_path}")
        
    else:
        print(f"✓ Found audit trail at {audit_path}")
        print(f"  Run orchestrator to generate real invoices")
        print(f"  from orchestrator import KIKIBillingOrchestrator")

if __name__ == "__main__":
    main()
