import json
import csv
import sys
from pathlib import Path
from datetime import datetime

from generate_shadow_mode_report import generate_shadow_mode_report

DEFAULT_FEE_RATE = 0.15
DEFAULT_CURRENCY = "GBP"


def generate_invoice(client_name: str, fee_rate: float = DEFAULT_FEE_RATE):
    reports_dir = Path(__file__).parent.parent / 'reports'
    invoices_dir = Path(__file__).parent.parent / 'invoices'
    reports_dir.mkdir(parents=True, exist_ok=True)
    invoices_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / f"shadow_mode_{client_name.replace(' ', '_').lower()}.json"
    if not json_path.exists():
        report = generate_shadow_mode_report(client_name)
        json_path.write_text(json.dumps(report, indent=2))
    else:
        report = json.loads(json_path.read_text())

    headline = report.get('headline', {})
    recoverable = float(headline.get('recoverable_margin_gbp', 0))
    fee_amount = round(recoverable * fee_rate, 2)

    invoice = {
        'invoice_id': f"shadow-{client_name.replace(' ', '-').lower()}-{datetime.now().strftime('%Y%m%d')}",
        'client': client_name,
        'date': datetime.now().date().isoformat(),
        'currency': DEFAULT_CURRENCY,
        'recoverable_margin_gbp': recoverable,
        'fee_rate': fee_rate,
        'amount_due': fee_amount,
        'description': f"Performance fee ({int(fee_rate*100)}%) from Shadow Mode Report recoverable margin",
        'source_report': str(json_path),
    }

    # Save JSON
    json_out = invoices_dir / f"invoice_shadow_{client_name.replace(' ', '_').lower()}.json"
    json_out.write_text(json.dumps(invoice, indent=2))

    # Save CSV
    csv_out = invoices_dir / f"invoice_shadow_{client_name.replace(' ', '_').lower()}.csv"
    with csv_out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(invoice.keys()))
        writer.writeheader()
        writer.writerow(invoice)

    print(f"✓ Invoice generated: {json_out}")
    print(f"✓ Invoice CSV: {csv_out}")
    print(f"  Amount Due: {DEFAULT_CURRENCY} {fee_amount:,.2f} (rate {fee_rate*100:.0f}%)")


if __name__ == '__main__':
    client = 'Demo Client'
    rate = DEFAULT_FEE_RATE
    if len(sys.argv) > 1:
        client = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            rate = float(sys.argv[2])
        except Exception:
            pass
    generate_invoice(client, rate)
