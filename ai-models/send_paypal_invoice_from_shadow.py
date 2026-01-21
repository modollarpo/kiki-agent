import os
import json
from pathlib import Path
from datetime import datetime, timedelta

from importlib.machinery import SourceFileLoader
_adapter_path = Path(__file__).parent.parent / 'cmd' / 'billing' / 'paypal_adapter.py'
paypal_adapter_mod = SourceFileLoader('paypal_adapter', str(_adapter_path)).load_module()
PayPalOaaSBillingAdapter = paypal_adapter_mod.PayPalOaaSBillingAdapter

FEE_RATE = 0.15
CURRENCY = "USD"


def build_invoice_from_report(client_name: str) -> dict:
    report_path = Path(__file__).parent.parent / 'reports' / f'shadow_mode_{client_name.replace(' ', '_').lower()}.json'
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")
    report = json.loads(report_path.read_text())

    headline = report.get('headline', {})
    recommendation = report.get('recommendation', {})
    meta = report.get('meta', {})

    recoverable_gbp = float(headline.get('recoverable_margin_gbp', 0))
    fee_amount = round(recoverable_gbp * FEE_RATE, 2)
    margin_improvement_pct = float(recommendation.get('target_margin_increase_pct', 12))

    # period
    period_days = int(meta.get('period_days', 30))
    report_date = datetime.fromisoformat(meta.get('report_date')) if meta.get('report_date') else datetime.now()
    period_end = report_date
    period_start = report_date - timedelta(days=period_days)

    invoice_id = f"INV-{datetime.now().strftime('%Y%m%d')}-{client_name.replace(' ', '-').upper()}"

    invoice_data = {
        "invoice_id": invoice_id,
        "issue_date": datetime.now().isoformat(),
        "payment_terms": "Net 30",
        "summary": {
            "total_margin_improvement": margin_improvement_pct,
            "total_kiki_earnings": fee_amount,
        },
        "line_items": [
            {
                "client_id": client_name.replace(' ', '_').lower(),
                "margin_improvement_pct": margin_improvement_pct,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "kiki_earnings": fee_amount,
            }
        ],
    }

    return invoice_data


def main():
    client = os.environ.get("CLIENT_NAME", "Storegrill Inc Ltd")
    client_email = os.environ.get("CLIENT_EMAIL", "billing@storegrill.com")

    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID", "client_id_sandbox")
    paypal_secret = os.getenv("PAYPAL_CLIENT_SECRET", "secret_sandbox")
    mode = os.getenv("PAYPAL_MODE", "sandbox")

    adapter = PayPalOaaSBillingAdapter(paypal_client_id, paypal_secret, mode=mode)

    invoice_data = build_invoice_from_report(client)
    paypal_inv = adapter.create_invoice(invoice_data, client_email, client)

    print(f"\n✓ PayPal Invoice Created: {paypal_inv['invoice_id']}")
    print(f"  Status: {paypal_inv['status']}")
    print(f"  Link: {paypal_inv['href']}")

    sent = adapter.send_invoice(paypal_inv["invoice_id"])
    print(f"\n✓ Invoice Sent: {sent['status']} at {sent['sent_date']}")

    sub = adapter.create_subscription(client_email, invoice_data, billing_cycle_days=30)
    print(f"\n✓ Subscription Created: {sub['subscription_id']}")
    print(f"  Status: {sub['status']}")
    print(f"  Approval Link: {sub['href']}")


if __name__ == "__main__":
    main()
