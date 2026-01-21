#!/usr/bin/env python3
"""
Quick invoice generator from shield_audit.csv
"""

import sys
from pathlib import Path
import os

# Add billing dir to path
sys.path.insert(0, str(Path(__file__).parent))

from ooaS_billing_engine import KIKIOaaSBillingEngine
from datetime import datetime, timedelta

def main():
    audit_path = Path(__file__).parent.parent.parent / "shield_audit.csv"
    
    if not audit_path.exists():
        print(f"❌ Audit trail not found at {audit_path}")
        return
    
    print(f"✓ Loading audit trail from {audit_path}")
    
    # Initialize engine
    engine = KIKIOaaSBillingEngine(kiki_share_pct=15.0)
    audit_df = engine.load_audit_trail(str(audit_path))
    
    print(f"✓ Loaded {len(audit_df)} audit records")
    
    # Billing period: last 7 days
    period_end = datetime.now()
    period_start = period_end - timedelta(days=7)
    
    print(f"\n📋 Billing Period: {period_start.date()} to {period_end.date()}")
    
    # Get unique clients
    clients = list(audit_df["client_id"].unique())
    print(f"✓ Found {len(clients)} unique clients")
    
    # Generate invoices
    profit_shares = []
    baseline_roas = 3.0
    
    for client_id in clients[:5]:  # First 5 for demo
        try:
            metrics = engine.aggregate_client_metrics(
                audit_df, client_id, period_start, period_end
            )
            ps = engine.calculate_profit_share(metrics, baseline_roas)
            profit_shares.append(ps)
            
            print(f"\n✓ {client_id}:")
            print(f"    Baseline ROAS: {ps.baseline_roas:.1f}x")
            print(f"    KIKI ROAS: {ps.kiki_roas:.2f}x")
            print(f"    Margin Improvement: {ps.margin_improvement:.1f}%")
            print(f"    KIKI Earnings: ${ps.kiki_earnings:.2f}")
            
        except ValueError as e:
            print(f"⚠ {client_id}: {e}")
    
    # Generate consolidated invoice
    if profit_shares:
        invoice = engine.generate_invoice(
            profit_shares,
            invoice_id=f"INV-{datetime.now().strftime('%Y%m%d')}-OaaS",
            issue_date=datetime.now(),
        )
        
        # Save invoice
        invoices_dir = Path(__file__).parent.parent.parent / "invoices"
        invoices_dir.mkdir(exist_ok=True)
        
        inv_file = invoices_dir / f"{invoice['invoice_id']}.json"
        import json
        with open(inv_file, "w") as f:
            json.dump(invoice, f, indent=2)
        
        print(f"\n💰 OaaS Invoice Summary:")
        print(f"    Total Clients: {invoice['summary']['total_clients']}")
        print(f"    Total Margin Improvement: {invoice['summary']['total_margin_improvement']:.1f}%")
        print(f"    Total Additional Revenue: ${invoice['summary']['total_additional_revenue']:.2f}")
        print(f"    Total KIKI Earnings: ${invoice['summary']['total_kiki_earnings']:.2f}")
        
        print(f"\n✓ Invoice saved: {inv_file}")
        print(f"\nNext steps:")
        print(f"  1. Set Stripe/Zuora credentials in .env")
        print(f"  2. Run: python orchestrator.py stripe/zuora salesforce/hubspot")
        print(f"  3. Invoices will be synced to payment & CRM systems")

if __name__ == "__main__":
    main()
