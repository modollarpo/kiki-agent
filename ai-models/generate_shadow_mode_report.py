"""
Shadow Mode Report Generator

Generates realistic "Moment of Truth" audits showing capital leak and LTV waste
for new prospects. Uses client profile and event data to compute:
- Predictive accuracy gaps
- Human latency costs
- Budget anomalies (SyncShield™ scenarios)
- Recoverable margin recommendations

Output: JSON report suitable for interactive dashboard visualization.
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
import random


def load_audit_data(audit_csv_path: str) -> list:
    """
    Load shadow mode simulation data. For now, generate synthetic data
    since the audit_log.csv doesn't contain LTV/spend columns needed for
    Shadow Mode analysis. In production, this would read from a dedicated
    shadow_mode_events table with predicted_ltv, actual_ltv, spend, etc.
    """
    print(f"Generating synthetic Shadow Mode data (audit file has no LTV/spend data).")
    return generate_synthetic_audit()


def generate_synthetic_audit() -> list:
    """Generate 500 synthetic events mimicking audit_log.csv structure with realistic LTV data."""
    events = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(500):
        event_date = base_date + timedelta(hours=i % 720)  # Spread over 30 days
        
        # Realistic LTV distribution: Pareto-style (80/20)
        if i % 100 < 10:  # Top 10%
            ltv_score = round(random.gauss(450, 50), 2)
            segment = 'VIP'
            spend = round(random.uniform(50, 150), 2)
        elif i % 100 < 50:  # Middle 40%
            ltv_score = round(random.gauss(85, 15), 2)
            segment = 'Middle'
            spend = round(random.uniform(20, 80), 2)
        else:  # Bottom 50%
            ltv_score = round(random.gauss(12, 8), 2)
            segment = 'Waste'
            spend = round(random.uniform(5, 40), 2)
        
        # Actual 30-day value: correlated to prediction (±10%)
        actual_value = round(ltv_score * random.uniform(0.85, 1.05), 2)
        platform_cpc = round(random.uniform(0.50, 3.00), 2)
        
        events.append({
            'timestamp': event_date.isoformat(),
            'client': random.choice(['google_ads', 'meta', 'tiktok']),
            'user_id': f"user_{i:05d}",
            'predicted_ltv': str(max(5, ltv_score)),
            'actual_30d_value': str(max(0, actual_value)),
            'spend': str(spend),
            'platform_cpc': str(platform_cpc),
            'segment': segment,
        })
    
    return events


def analyze_predictive_accuracy(events: list) -> dict:
    """
    Compare Day 1 predicted LTV to actual 30-day value.
    Returns accuracy metrics by segment.
    """
    segments = {'VIP': [], 'Middle': [], 'Waste': []}
    
    for event in events:
        try:
            pred = float(event.get('predicted_ltv', 0))
            actual = float(event.get('actual_30d_value', 0))
            segment = event.get('segment', 'Waste')
            
            if segment in segments:
                if actual > 0:
                    accuracy = min(100, (min(pred, actual) / max(pred, actual)) * 100)
                else:
                    accuracy = 0
                segments[segment].append({
                    'predicted': pred,
                    'actual': actual,
                    'accuracy': round(accuracy, 1)
                })
        except (ValueError, KeyError):
            pass
    
    # Compute aggregates
    accuracy_by_segment = {}
    for seg, data in segments.items():
        if data:
            avg_accuracy = sum(d['accuracy'] for d in data) / len(data)
            avg_predicted = sum(d['predicted'] for d in data) / len(data)
            avg_actual = sum(d['actual'] for d in data) / len(data)
            accuracy_by_segment[seg] = {
                'accuracy_pct': round(avg_accuracy, 1),
                'avg_predicted_ltv': round(avg_predicted, 2),
                'avg_actual_ltv': round(avg_actual, 2),
                'sample_count': len(data),
            }
    
    return accuracy_by_segment


def calculate_capital_leak(events: list, accuracy_by_segment: dict) -> dict:
    """
    Estimate wasted spend on low-LTV segments.
    Capital Leak = spend on Waste segment * (1 - segment accuracy).
    """
    total_spend = sum(float(e.get('spend', 0)) for e in events)
    waste_spend = sum(float(e.get('spend', 0)) for e in events if e.get('segment') == 'Waste')
    
    waste_accuracy = accuracy_by_segment.get('Waste', {}).get('accuracy_pct', 50) / 100
    recoverable = waste_spend * (1 - waste_accuracy)
    
    return {
        'total_spend_30d': round(total_spend, 2),
        'waste_segment_spend': round(waste_spend, 2),
        'waste_segment_pct': round((waste_spend / total_spend * 100) if total_spend > 0 else 0, 1),
        'recoverable_margin': round(recoverable, 2),
        'capital_leak_pct': round((recoverable / total_spend * 100) if total_spend > 0 else 0, 1),
    }


def calculate_human_latency_cost(events: list) -> dict:
    """
    Simulate surge detection scenarios.
    KIKI would react in <1ms; typical platform/manual reaction is 4.5 hours.
    Estimate cost of missed surges.
    """
    # Identify high-LTV surges (e.g., top 10% of events)
    sorted_events = sorted(
        events,
        key=lambda e: float(e.get('actual_30d_value', 0)),
        reverse=True
    )
    top_10_pct = sorted_events[:max(1, len(sorted_events) // 10)]
    
    surge_spend = sum(float(e.get('spend', 0)) for e in top_10_pct)
    surge_cpc = sum(float(e.get('platform_cpc', 1)) for e in top_10_pct) / len(top_10_pct) if top_10_pct else 1
    
    # Manual/platform latency cost: 45 minutes of suboptimal bidding on surge events
    missed_surge_count = len(top_10_pct) // 4  # Assume platform misses 25%
    latency_cost = missed_surge_count * surge_cpc * 2  # 2x CPC for late reaction
    
    return {
        'high_ltv_surges_detected': len(top_10_pct),
        'surge_avg_ltv': round(sum(float(e.get('actual_30d_value', 0)) for e in top_10_pct) / len(top_10_pct), 2) if top_10_pct else 0,
        'platform_reaction_minutes': 270,  # 4.5 hours
        'kiki_reaction_milliseconds': 1,
        'surges_platform_missed': missed_surge_count,
        'estimated_latency_cost': round(latency_cost, 2),
    }


def detect_budget_anomalies(events: list) -> list:
    """
    Identify sudden CPC spikes, unusual spend patterns, or budget waste.
    Return list of anomalies suitable for SyncShield log.
    """
    anomalies = []
    
    # Anomaly 1: CPC spike detection
    cpcs = [float(e.get('platform_cpc', 1)) for e in events if e.get('platform_cpc')]
    if cpcs:
        avg_cpc = sum(cpcs) / len(cpcs)
        std_cpc = (sum((c - avg_cpc) ** 2 for c in cpcs) / len(cpcs)) ** 0.5
        spike_threshold = avg_cpc + (2 * std_cpc)
        
        spike_events = [e for e in events if float(e.get('platform_cpc', 0)) > spike_threshold]
        if spike_events:
            spike_spend = sum(float(e.get('spend', 0)) for e in spike_events)
            anomalies.append({
                'type': 'CPC_SPIKE',
                'timestamp': spike_events[0].get('timestamp', 'unknown'),
                'platform': spike_events[0].get('client', 'unknown'),
                'description': f"Sudden CPC spike detected on {spike_events[0].get('client', 'unknown')}",
                'spike_cpc': round(spike_threshold, 2),
                'actual_cpc': round(float(spike_events[0].get('platform_cpc', 0)), 2),
                'affected_spend': round(spike_spend, 2),
                'duration_minutes': 45,
                'kiki_action': 'Cool-Down triggered',
                'kiki_action_time_ms': 0.03,
            })
    
    # Anomaly 2: Waste segment overspend
    waste_events = [e for e in events if e.get('segment') == 'Waste']
    if waste_events:
        waste_spend = sum(float(e.get('spend', 0)) for e in waste_events)
        anomalies.append({
            'type': 'WASTE_OVERSPEND',
            'timestamp': waste_events[0].get('timestamp', 'unknown'),
            'platform': waste_events[0].get('client', 'unknown'),
            'description': f"Budget misallocated to low-LTV segment (Bottom 50%)",
            'waste_spend': round(waste_spend, 2),
            'waste_pct': round((waste_spend / sum(float(e.get('spend', 0)) for e in events)) * 100, 1),
            'kiki_action': 'Reallocate to VIP segment',
            'expected_margin_lift': '12-18%',
        })
    
    return anomalies


def generate_recommendation(capital_leak: dict, anomalies: list, accuracy: dict) -> dict:
    """
    Produce the "Switch-On" strategy: phased rollout with margin targets.
    """
    recoverable = capital_leak.get('recoverable_margin', 0)
    phase_1_budget = capital_leak.get('total_spend_30d', 1000) * 0.20  # 20% transfer
    
    # Safe anomaly cost lookup
    anomaly_cost = round(anomalies[0].get("affected_spend", 0) * 0.7, 2) if anomalies else 500
    
    return {
        'strategy': 'PHASED_SWITCH_ON',
        'phase_1_budget_transfer': round(phase_1_budget, 2),
        'phase_1_duration_days': 14,
        'target_margin_increase_pct': 12,
        'phase_1_timeline': [
            {
                'day': 1,
                'action': 'Transfer 20% budget to Smart Segments (VIP + Middle)',
                'expected_impact': 'Baseline established',
            },
            {
                'day': 7,
                'action': 'Apply MaxBurstLimit protection',
                'expected_impact': f'Anomaly costs reduced by ~£{anomaly_cost} if spike recurs',
            },
            {
                'day': 14,
                'action': 'Full reallocation based on VIP/Middle accuracy',
                'expected_impact': f'Margin increase of 12-15% (£{round(recoverable * 0.12, 2)} in recovered spend)',
            },
        ],
        'max_burst_limit': round(phase_1_budget / 10, 2),
        'estimated_month_2_margin_improvement': round(recoverable * 0.15, 2),
        'ooaS_fee_15pct_savings': round(recoverable * 0.15, 2),
        'roi_breakeven_days': 30,
    }


def generate_shadow_mode_report(client_name: str, audit_csv_path: str = None) -> dict:
    """
    Main report generator. Orchestrates all analyses and returns unified JSON.
    """
    if audit_csv_path is None:
        audit_csv_path = Path(__file__).parent.parent / 'shield_audit.csv'
    
    # Load or generate audit data
    events = load_audit_data(str(audit_csv_path))
    
    # Run analyses
    accuracy = analyze_predictive_accuracy(events)
    capital_leak = calculate_capital_leak(events, accuracy)
    latency = calculate_human_latency_cost(events)
    anomalies = detect_budget_anomalies(events)
    recommendation = generate_recommendation(capital_leak, anomalies, accuracy)
    
    # Overall accuracy (weighted average)
    total_samples = sum(seg.get('sample_count', 1) for seg in accuracy.values())
    overall_accuracy = (
        sum(seg.get('accuracy_pct', 0) * seg.get('sample_count', 1) for seg in accuracy.values())
        / total_samples
    ) if total_samples > 0 else 85
    
    report = {
        'meta': {
            'client': client_name,
            'report_date': datetime.now().isoformat(),
            'period_days': 30,
            'audit_events_analyzed': len(events),
        },
        'headline': {
            'kiki_accuracy_pct': round(overall_accuracy, 1),
            'recoverable_margin_gbp': capital_leak['recoverable_margin'],
            'capital_leak_pct': capital_leak['capital_leak_pct'],
        },
        'predictive_accuracy': accuracy,
        'capital_leak': capital_leak,
        'human_latency': latency,
        'anomalies': anomalies,
        'recommendation': recommendation,
    }
    
    return report


if __name__ == '__main__':
    # Generate sample reports for demo
    clients = ['Google Ads Partner', 'Meta AI Studio', 'TikTok Growth']
    
    for client_name in clients:
        report = generate_shadow_mode_report(client_name)
        
        # Save to JSON
        output_path = Path(__file__).parent.parent / 'reports' / f'shadow_mode_{client_name.replace(" ", "_").lower()}.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Report saved: {output_path}")
        print(f"  Recoverable Margin: £{report['headline']['recoverable_margin_gbp']:,.2f}")
        print(f"  KIKI Accuracy: {report['headline']['kiki_accuracy_pct']}%\n")
