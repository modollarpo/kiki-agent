# KIKI OaaS Billing: Demo Runner
# Generates sample invoice and optionally syncs to Stripe/Zuora/CRM

param(
    [string]$Provider = "none",      # none, stripe, zuora
    [string]$CRMProvider = "none",   # none, salesforce, hubspot
    [switch]$DryRun = $false         # Show what would happen, don't charge
)

# Navigate to billing directory
$BillingDir = "C:\Users\USER\Documents\KIKI\cmd\billing"
Set-Location $BillingDir

# Load .env if present (PowerShell doesn't auto-load .env like bash)
$EnvFile = "C:\Users\USER\Documents\KIKI\.env"
if (Test-Path $EnvFile) {
    Write-Host "✓ Loading environment from .env"
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#][^=]*?)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

# Set defaults for demo (test/mock credentials)
if (-not $env:STRIPE_SECRET_KEY) {
    $env:STRIPE_SECRET_KEY = "sk_test_example_for_demo"
}
if (-not $env:ZUORA_API_URL) {
    $env:ZUORA_API_URL = "https://api.zuora.sandbox.com"
}
if (-not $env:SALESFORCE_INSTANCE) {
    $env:SALESFORCE_INSTANCE = "https://myorg.sandbox.salesforce.com"
}
if (-not $env:HUBSPOT_API_KEY) {
    $env:HUBSPOT_API_KEY = "pat-demo-key"
}
if (-not $env:KIKI_SHARE_PCT) {
    $env:KIKI_SHARE_PCT = "15"
}
if (-not $env:BASELINE_ROAS) {
    $env:BASELINE_ROAS = "3.0"
}

Write-Host ""
Write-Host "🚀 KIKI OaaS Billing Engine - Demo Runner"
Write-Host "==========================================="
Write-Host ""
Write-Host "Configuration:"
Write-Host "  Billing Provider: $Provider"
Write-Host "  CRM Provider: $CRMProvider"
Write-Host "  DRY RUN: $DryRun"
Write-Host "  KIKI Share: $($env:KIKI_SHARE_PCT)%"
Write-Host "  Baseline ROAS: $($env:BASELINE_ROAS)x"
Write-Host ""

# Check if audit trail exists
if (-not (Test-Path "C:\Users\USER\Documents\KIKI\shield_audit.csv")) {
    Write-Host "⚠️  Audit trail not found at C:\Users\USER\Documents\KIKI\shield_audit.csv"
    Write-Host "   Generate by running: go run cmd/syncflow/main.go"
    Write-Host ""
    Write-Host "   For demo purposes, we'll generate a sample invoice JSON..."
    Write-Host ""
}

# Create Python script to run orchestrator
$PythonScript = @'
import sys
import os
from datetime import datetime, timedelta
import json

# Parse environment
billing_provider = sys.argv[1] if len(sys.argv) > 1 else "none"
crm_provider = sys.argv[2] if len(sys.argv) > 2 else "none"
dry_run = sys.argv[3] == "true" if len(sys.argv) > 3 else False

try:
    # Try to load orchestrator; if audit trail missing, use demo invoice
    audit_path = "C:\\Users\\USER\\Documents\\KIKI\\shield_audit.csv"
    
    if not os.path.exists(audit_path):
        print("📝 Audit trail not found; generating demo invoice...")
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
        
        print(json.dumps(demo_invoice, indent=2))
        
        # Save to invoices
        os.makedirs("C:\\Users\\USER\\Documents\\KIKI\\invoices", exist_ok=True)
        inv_path = f"C:\\Users\\USER\\Documents\\KIKI\\invoices\\{demo_invoice['invoice_id']}.json"
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
        # Load orchestrator and generate real invoices
        from orchestrator import KIKIBillingOrchestrator, BillingProvider, CRMProvider
        
        print("✓ Loading audit trail...")
        
        # Map string to enum
        bill_prov = {
            "stripe": BillingProvider.STRIPE,
            "zuora": BillingProvider.ZUORA,
            "none": BillingProvider.NONE,
        }.get(billing_provider, BillingProvider.NONE)
        
        crm_prov = {
            "salesforce": CRMProvider.SALESFORCE,
            "hubspot": CRMProvider.HUBSPOT,
            "none": CRMProvider.NONE,
        }.get(crm_provider, CRMProvider.NONE)
        
        orchestrator = KIKIOaaSBillingEngine(
            audit_csv_path=audit_path,
            billing_provider=bill_prov,
            crm_provider=crm_prov,
        )
        
        # Generate invoices
        period_end = datetime.now()
        period_start = period_end - timedelta(days=30)
        
        print(f"\n📋 Generating invoices for {period_start.date()} to {period_end.date()}")
        invoices = orchestrator.generate_monthly_invoices(period_start, period_end)
        
        for invoice in invoices:
            print(f"\n✓ Invoice: {invoice['invoice_id']}")
            print(f"  Total Earnings: ${invoice['summary']['total_kiki_earnings']:.2f}")
            print(f"  Margin Improvement: {invoice['summary']['total_margin_improvement']:.1f}%")
            
            # Save
            path = orchestrator.save_invoice(invoice)
            print(f"  Saved: {path}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
'@

# Write and run Python script
$ScriptPath = "$BillingDir\demo_runner.py"
$PythonScript | Out-File -FilePath $ScriptPath -Encoding UTF8

Write-Host "Running orchestrator..."
Write-Host ""

# Run with Python
$env:PYTHONPATH = "C:\Users\USER\Documents\KIKI\cmd\billing"
python $ScriptPath $Provider $CRMProvider $($DryRun.ToString().ToLower())

Write-Host ""
Write-Host "✅ Demo complete!"
