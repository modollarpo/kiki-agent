"""
Quick runner for profit-share billing with live Prometheus integration.
Generates invoices and pushes to billing adapters (Stripe/Zuora/PayPal).
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from profit_share_calculator import KIKIProfitShareEngine

def main():
    print("=" * 100)
    print("KIKI OaaS Revenue Engine - Automated Profit-Share Billing")
    print("=" * 100)
    print()
    print("🎯 TRL7 Milestone: Revenue-Generating System")
    print("📊 Data Source: Prometheus metrics + Immutable audit trail")
    print("💰 Model: 10% of margin recovered (vs. 3.0x baseline ROAS)")
    print()
    
    # Initialize profit-share engine
    engine = KIKIProfitShareEngine(
        prometheus_url="http://localhost:9090",
        audit_trail_path="../audit_log.csv",
        profit_share_pct=10.0  # 10% of margin improvement
    )
    
    # Campaigns to bill (matches Prometheus metrics in prometheus_exporter.py)
    campaigns = [
        ("campaign_001", "Acme Corp - Meta Ads"),
        ("campaign_002", "TechStartup Inc - Google Ads"),
        ("campaign_003", "E-commerce Co - TikTok Ads"),
        ("campaign_004", "SaaS Platform - LinkedIn Ads"),
    ]
    
    # Generate invoice for January 2026
    invoice_month = datetime(2026, 1, 1)
    
    print(f"📅 Billing Period: {invoice_month.strftime('%B %Y')}")
    print(f"🏢 Clients: {len(campaigns)}")
    print()
    print("⏳ Calculating margin recovery from Prometheus metrics...")
    print()
    
    # Generate invoice
    invoice = engine.generate_monthly_invoice(campaigns, invoice_month)
    
    # Display results
    print("=" * 100)
    print("✅ INVOICE GENERATED")
    print("=" * 100)
    print()
    print(f"📄 Invoice ID: {invoice['invoice_id']}")
    print(f"📆 Issue Date: {datetime.fromisoformat(invoice['issue_date']).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📆 Due Date: {datetime.fromisoformat(invoice['due_date']).strftime('%Y-%m-%d')} (Net 30)")
    print()
    
    summary = invoice['summary']
    print("💵 FINANCIAL SUMMARY")
    print("-" * 100)
    print(f"  Total Campaigns Billed: {summary['total_campaigns']}")
    print(f"  Total Margin Recovered for Clients: ${summary['total_margin_recovered']:,.2f}")
    print(f"  KIKI Profit Share ({engine.profit_share_pct}%): ${summary['total_invoice_amount']:,.2f}")
    print()
    print(f"📈 PERFORMANCE METRICS")
    print("-" * 100)
    print(f"  Average LTV:CAC Ratio: {summary['average_ltv_cac_ratio']:.2f}x (vs 3.0x baseline)")
    print(f"  Average Prediction Accuracy: {summary['average_accuracy']:.1f}% (TRL6: 94.7%)")
    print()
    
    if invoice['line_items']:
        print("📋 LINE ITEM BREAKDOWN")
        print("-" * 100)
        for i, line in enumerate(invoice['line_items'], 1):
            print(f"\n{i}. {line['client_name']}")
            print(f"   Campaign ID: {line['campaign_id']}")
            print(f"   Period: {line['period_start'][:10]} to {line['period_end'][:10]}")
            print(f"   Baseline ROAS: {line['baseline_roas']:.1f}x → KIKI ROAS: {line['kiki_roas']:.2f}x")
            print(f"   Margin Improvement: +{line['margin_improvement_pct']:.1f}%")
            print(f"   Client Margin Recovered: ${line['margin_recovered']:,.2f}")
            print(f"   KIKI Fee: ${line['kiki_invoice_amount']:,.2f}")
            print(f"   Proof: {line['predictions_count']:,} predictions @ {line['accuracy_rate']:.1f}% accuracy")
    else:
        print("⚠️  WARNING: No line items generated")
        print()
        print("Possible causes:")
        print("  1. Prometheus exporter not running → Start with: python ai-models/prometheus_exporter.py")
        print("  2. No metrics data → Wait 5 seconds for metrics to populate")
        print("  3. Campaign IDs mismatch → Check prometheus_exporter.py line 120-150")
        print()
        sys.exit(1)
    
    # Save invoice files
    invoice_dir = Path("../invoices")
    invoice_dir.mkdir(exist_ok=True)
    
    json_path = invoice_dir / f"{invoice['invoice_id']}.json"
    with open(json_path, "w") as f:
        json.dump(invoice, f, indent=2)
    
    print()
    print("=" * 100)
    print("✅ INVOICE SAVED")
    print("=" * 100)
    print(f"📁 JSON: {json_path.absolute()}")
    
    # Create CSV for QuickBooks/Xero import
    import csv
    csv_path = invoice_dir / f"{invoice['invoice_id']}.csv"
    if invoice['line_items']:
        with open(csv_path, 'w', newline='') as f:
            fieldnames = [
                'campaign_id', 'client_name', 'period_start', 'period_end',
                'baseline_roas', 'kiki_roas', 'margin_improvement_pct',
                'margin_recovered', 'profit_share_percentage', 'kiki_invoice_amount',
                'accuracy_rate', 'predictions_count', 'reliability_score'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(invoice['line_items'])
        print(f"📁 CSV: {csv_path.absolute()}")
    
    # Display proof of value
    print()
    print("=" * 100)
    print("🔐 PROOF OF VALUE (Investor/Auditor Evidence)")
    print("=" * 100)
    proof = invoice['proof_of_value']
    print(f"  Methodology: {proof['methodology']}")
    print(f"  Baseline: {proof['baseline_comparison']}")
    print(f"  Calculation: {proof['margin_calculation']}")
    print(f"  TRL Level: {proof['trl_level']}")
    print(f"  Compliance: {proof['compliance']}")
    print()
    print(f"  Data Sources:")
    for source in proof['data_sources']:
        print(f"    ✓ {source}")
    
    print()
    print("=" * 100)
    print("🚀 NEXT ACTIONS")
    print("=" * 100)
    print()
    print("1. Send invoice to Stripe for auto-collection:")
    print("   python cmd/billing/stripe_adapter.py")
    print()
    print("2. Push to Zuora subscription billing:")
    print("   python cmd/billing/zuora_adapter.py")
    print()
    print("3. Export to QuickBooks/Xero:")
    print("   python cmd/billing/quickbooks_xero_adapter.py")
    print()
    print("4. View in Grafana Command Center:")
    print("   http://localhost:8502")
    print()
    print("5. Track OaaS revenue in Prometheus:")
    print(f"   curl http://localhost:9090/api/v1/query?query=kiki_ooaS_revenue_total")
    print()
    print("=" * 100)
    print(f"✅ TRL7 Revenue Model Activated - ${summary['total_invoice_amount']:,.2f} earned")
    print("=" * 100)

if __name__ == "__main__":
    main()
