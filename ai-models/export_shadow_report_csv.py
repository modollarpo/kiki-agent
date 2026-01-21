import json
import csv
import sys
from pathlib import Path
from datetime import datetime

from generate_shadow_mode_report import generate_shadow_mode_report


def export_csv(client_name: str):
    reports_dir = Path(__file__).parent.parent / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / f"shadow_mode_{client_name.replace(' ', '_').lower()}.json"

    if not json_path.exists():
        report = generate_shadow_mode_report(client_name)
        json_path.write_text(json.dumps(report, indent=2))
    else:
        report = json.loads(json_path.read_text())

    # Build a flat CSV structure
    csv_rows = []
    meta = report.get('meta', {})
    headline = report.get('headline', {})
    acc = report.get('predictive_accuracy', {})
    leak = report.get('capital_leak', {})
    latency = report.get('human_latency', {})
    anomalies = report.get('anomalies', [])

    row = {
        'client': meta.get('client', client_name),
        'report_date': meta.get('report_date', datetime.now().isoformat()),
        'period_days': meta.get('period_days', 30),
        'events_analyzed': meta.get('audit_events_analyzed', 0),
        # Headline
        'kiki_accuracy_pct': headline.get('kiki_accuracy_pct', 0),
        'recoverable_margin_gbp': headline.get('recoverable_margin_gbp', 0),
        'capital_leak_pct': headline.get('capital_leak_pct', 0),
        # Segment accuracy (averages)
        'vip_predicted_ltv': acc.get('VIP', {}).get('avg_predicted_ltv', 0),
        'vip_actual_ltv': acc.get('VIP', {}).get('avg_actual_ltv', 0),
        'vip_accuracy_pct': acc.get('VIP', {}).get('accuracy_pct', 0),
        'vip_sample_count': acc.get('VIP', {}).get('sample_count', 0),
        'middle_predicted_ltv': acc.get('Middle', {}).get('avg_predicted_ltv', 0),
        'middle_actual_ltv': acc.get('Middle', {}).get('avg_actual_ltv', 0),
        'middle_accuracy_pct': acc.get('Middle', {}).get('accuracy_pct', 0),
        'middle_sample_count': acc.get('Middle', {}).get('sample_count', 0),
        'waste_predicted_ltv': acc.get('Waste', {}).get('avg_predicted_ltv', 0),
        'waste_actual_ltv': acc.get('Waste', {}).get('avg_actual_ltv', 0),
        'waste_accuracy_pct': acc.get('Waste', {}).get('accuracy_pct', 0),
        'waste_sample_count': acc.get('Waste', {}).get('sample_count', 0),
        # Capital leak details
        'total_spend_30d': leak.get('total_spend_30d', 0),
        'waste_segment_spend': leak.get('waste_segment_spend', 0),
        'waste_segment_pct': leak.get('waste_segment_pct', 0),
        # Latency
        'surges_detected': latency.get('high_ltv_surges_detected', 0),
        'surges_missed': latency.get('surges_platform_missed', 0),
        'platform_reaction_minutes': latency.get('platform_reaction_minutes', 0),
        'kiki_reaction_ms': latency.get('kiki_reaction_milliseconds', 0),
        'estimated_latency_cost': latency.get('estimated_latency_cost', 0),
        # Anomaly summary
        'anomalies_count': len(anomalies),
        'first_anomaly_type': anomalies[0]['type'] if anomalies else '',
        'first_anomaly_desc': anomalies[0]['description'] if anomalies else '',
    }
    csv_rows.append(row)

    out_path = reports_dir / f"shadow_mode_{client_name.replace(' ', '_').lower()}.csv"
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"✓ CSV exported: {out_path}")


if __name__ == '__main__':
    client = 'Demo Client'
    if len(sys.argv) > 1:
        client = sys.argv[1]
    export_csv(client)
