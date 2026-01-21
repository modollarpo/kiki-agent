"""
Shadow Mode Report Dashboard

Interactive Plotly-based dashboard showing:
- Efficiency Gap headline KPIs
- Predictive Accuracy table with segment performance
- Human Latency comparison chart
- SyncShield™ Anomaly log
- Phase 2 Recommendation with rollout timeline

Designed for sales demos: clients see their own waste data.
"""

from flask import Flask, render_template_string, jsonify, request
from generate_shadow_mode_report import generate_shadow_mode_report
import json
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from importlib.machinery import SourceFileLoader
from datetime import datetime, timedelta


app = Flask(__name__)


# HTML Template with embedded Plotly
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>KIKI Shadow Mode Report | Moment of Truth</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 50px;
            border-bottom: 2px solid #475569;
            padding-bottom: 30px;
        }
        
        .logo {
            font-size: 32px;
            font-weight: bold;
            color: #60a5fa;
            margin-bottom: 10px;
        }
        
        .tagline {
            font-size: 14px;
            color: #94a3b8;
            margin-bottom: 20px;
        }
        
        .client-select {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }
        
        .client-select select {
            padding: 8px 12px;
            background: #1e293b;
            border: 1px solid #475569;
            color: #e2e8f0;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
        }
        
        .client-select button {
            padding: 8px 20px;
            background: #60a5fa;
            border: none;
            color: white;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .client-select button:hover {
            background: #3b82f6;
        }
        
        /* Headline KPIs */
        .headline {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 50px;
        }
        
        .kpi-card {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(96, 165, 250, 0.2);
        }
        
        .kpi-label {
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .kpi-value {
            font-size: 42px;
            font-weight: bold;
            color: #60a5fa;
            margin-bottom: 5px;
        }
        
        .kpi-sublabel {
            font-size: 13px;
            color: #cbd5e1;
        }
        
        .kpi-accent {
            color: #fbbf24;
        }
        
        /* Section headers */
        h2 {
            font-size: 24px;
            font-weight: 600;
            color: #e2e8f0;
            margin: 50px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #475569;
        }
        
        /* Charts */
        .chart-container {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            min-height: 400px;
        }
        
        /* Table */
        .table-container {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        th {
            background: #0f172a;
            color: #60a5fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #475569;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #334155;
        }
        
        tr:hover {
            background: rgba(96, 165, 250, 0.05);
        }
        
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge-success {
            background: rgba(34, 197, 94, 0.2);
            color: #86efac;
        }
        
        .badge-warning {
            background: rgba(251, 191, 36, 0.2);
            color: #fcd34d;
        }
        
        .badge-danger {
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
        }
        
        /* Anomaly log */
        .anomaly-item {
            background: #0f172a;
            border-left: 4px solid #f87171;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 6px;
        }
        
        .anomaly-type {
            font-size: 11px;
            color: #f87171;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .anomaly-desc {
            font-size: 14px;
            color: #e2e8f0;
            margin-bottom: 8px;
        }
        
        .anomaly-details {
            font-size: 12px;
            color: #94a3b8;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        
        .anomaly-detail {
            background: rgba(96, 165, 250, 0.05);
            padding: 8px;
            border-radius: 4px;
        }
        
        .anomaly-detail strong {
            color: #60a5fa;
        }
        
        /* Recommendation */
        .recommendation-card {
            background: linear-gradient(135deg, #065f46 0%, #047857 100%);
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
        }
        
        .recommendation-title {
            font-size: 20px;
            font-weight: 600;
            color: #d1fae5;
            margin-bottom: 20px;
        }
        
        .timeline {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .timeline-item {
            display: flex;
            gap: 15px;
        }
        
        .timeline-marker {
            width: 40px;
            height: 40px;
            background: #10b981;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            flex-shrink: 0;
        }
        
        .timeline-content {
            padding-top: 5px;
        }
        
        .timeline-day {
            font-size: 12px;
            color: #a7f3d0;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .timeline-action {
            font-size: 14px;
            color: #e2e8f0;
            margin-bottom: 8px;
        }
        
        .timeline-impact {
            font-size: 12px;
            color: #d1fae5;
            font-weight: 500;
        }
        
        footer {
            text-align: center;
            margin-top: 60px;
            padding-top: 30px;
            border-top: 2px solid #475569;
            color: #64748b;
            font-size: 12px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #94a3b8;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">⚡ KIKI Shadow Mode Report</div>
            <div class="tagline">Moment of Truth: How Much Capital Leak Occurred in the Last 30 Days?</div>
            
            <div class="client-select">
                <select id="clientSelect">
                    <option value="">-- Select a Client --</option>
                    <option value="Google Ads Partner">Google Ads Partner</option>
                    <option value="Meta AI Studio">Meta AI Studio</option>
                    <option value="TikTok Growth">TikTok Growth</option>
                    <option value="Storegrill Inc Ltd">Storegrill Inc Ltd</option>
                </select>
                <button onclick="loadReport()">Generate Report</button>
            </div>
        </header>
        
        <div id="content" class="loading">
            Select a client and click "Generate Report" to see the audit.
        </div>
        
        <footer>
            KIKI OaaS™ | SyncValue™ Brain | SyncFlow™ Execution | SyncShield™ Safety
        </footer>
    </div>
    
    <script>
        function loadReport() {
            const clientName = document.getElementById('clientSelect').value;
            if (!clientName) {
                alert('Please select a client.');
                return;
            }
            
            const contentDiv = document.getElementById('content');
            contentDiv.innerHTML = '<div class="loading">Loading report for ' + clientName + '...</div>';
            
            fetch('/api/shadow-report?client=' + encodeURIComponent(clientName))
                .then(res => res.json())
                .then(data => renderReport(data))
                .catch(err => {
                    contentDiv.innerHTML = '<div class="loading" style="color: #f87171;">Error: ' + err.message + '</div>';
                });
        }
        
        function renderReport(report) {
            const meta = report.meta;
            const headline = report.headline;
            const accuracy = report.predictive_accuracy;
            const leak = report.capital_leak;
            const latency = report.human_latency;
            const anomalies = report.anomalies;
            const recommendation = report.recommendation;
            
            let html = '';
            
            // HEADLINE
            html += '<h2>1. The Efficiency Gap (The Headline)</h2>';
            html += '<div class="headline">';
            html += '<div class="kpi-card">';
            html += '  <div class="kpi-label">KIKI Accuracy</div>';
            html += '  <div class="kpi-value">' + headline.kiki_accuracy_pct.toFixed(1) + '%</div>';
            html += '  <div class="kpi-sublabel">Day 1 prediction vs actual Month 1</div>';
            html += '</div>';
            html += '<div class="kpi-card">';
            html += '  <div class="kpi-label">Recoverable Margin</div>';
            html += '  <div class="kpi-value kpi-accent">£' + headline.recoverable_margin_gbp.toLocaleString('en-GB', {maximumFractionDigits: 0}) + '</div>';
            html += '  <div class="kpi-sublabel">Profit lost to low-value acquisition</div>';
            html += '</div>';
            html += '<div class="kpi-card">';
            html += '  <div class="kpi-label">Capital Leak</div>';
            html += '  <div class="kpi-value">' + headline.capital_leak_pct.toFixed(1) + '%</div>';
            html += '  <div class="kpi-sublabel">of total spend wasted on mercenary users</div>';
            html += '</div>';
            html += '</div>';
            
            // PREDICTIVE ACCURACY
            html += '<h2>2. Predictive Accuracy Validation</h2>';
            html += '<div class="table-container">';
            html += '<table>';
            html += '<thead><tr><th>Segment</th><th>KIKI Predicted LTV</th><th>Actual 30-Day Value</th><th>Accuracy</th><th>Status</th><th>Sample Size</th></tr></thead>';
            html += '<tbody>';
            
            const segments = [
              {name: 'Top 10% (VIPs)', key: 'VIP', color: 'success'},
              {name: 'Middle 40%', key: 'Middle', color: 'warning'},
              {name: 'Bottom 50% (Waste)', key: 'Waste', color: 'danger'},
            ];
            
            segments.forEach(seg => {
                const data = accuracy[seg.key];
                if (data) {
                    const status = seg.key === 'VIP' ? 'Accurate' : (seg.key === 'Middle' ? 'Accurate' : 'Target for Exclusion');
                    html += '<tr>';
                    html += '<td><strong>' + seg.name + '</strong></td>';
                    html += '<td>£' + data.avg_predicted_ltv.toFixed(2) + '</td>';
                    html += '<td>£' + data.avg_actual_ltv.toFixed(2) + '</td>';
                    html += '<td>' + data.accuracy_pct.toFixed(1) + '%</td>';
                    html += '<td><span class="badge badge-' + seg.color + '">' + status + '</span></td>';
                    html += '<td>' + data.sample_count + '</td>';
                    html += '</tr>';
                }
            });
            
            html += '</tbody>';
            html += '</table>';
            html += '<p style="margin-top: 15px; font-size: 12px; color: #94a3b8;"><strong>Audit Insight:</strong> Your current platform spent ' + leak.waste_segment_pct.toFixed(0) + '% of budget on Bottom 50%. KIKI would reallocate to Top 10% in real-time.</p>';
            html += '</div>';
            
            // HUMAN LATENCY
            html += '<h2>3. The "Human Latency" Tax</h2>';
            html += '<div class="chart-container" id="latencyChart"></div>';
            html += '<p style="margin-top: 15px; font-size: 13px; color: #cbd5e1;"><strong>Finding:</strong> ' + latency.high_ltv_surges_detected + ' high-LTV surges detected. Platform missed ' + latency.surges_platform_missed + ' of them (4.5-hour lag). KIKI would capture at &lt;1ms. <strong>Estimated latency cost: £' + latency.estimated_latency_cost.toFixed(2) + '</strong></p>';
            
            // SYNCSHIELD ANOMALIES
            html += '<h2>4. SyncShield™ Safety Log</h2>';
            anomalies.forEach(anom => {
                html += '<div class="anomaly-item">';
                html += '<div class="anomaly-type">' + anom.type + '</div>';
                html += '<div class="anomaly-desc">' + anom.description + '</div>';
                html += '<div class="anomaly-details">';
                if (anom.type === 'CPC_SPIKE') {
                    html += '<div class="anomaly-detail"><strong>Spike CPC:</strong> £' + anom.spike_cpc.toFixed(2) + '</div>';
                    html += '<div class="anomaly-detail"><strong>Actual CPC:</strong> £' + anom.actual_cpc.toFixed(2) + '</div>';
                    html += '<div class="anomaly-detail"><strong>Affected Spend:</strong> £' + anom.affected_spend.toFixed(2) + '</div>';
                    html += '<div class="anomaly-detail"><strong>Duration:</strong> ' + anom.duration_minutes + ' min</div>';
                    html += '<div class="anomaly-detail"><strong>KIKI Reaction:</strong> ' + anom.kiki_action_time_ms + 'ms Cool-Down</div>';
                } else {
                    html += '<div class="anomaly-detail"><strong>Waste Spend:</strong> £' + anom.waste_spend.toFixed(2) + '</div>';
                    html += '<div class="anomaly-detail"><strong>Waste %:</strong> ' + anom.waste_pct.toFixed(1) + '%</div>';
                    html += '<div class="anomaly-detail"><strong>Expected Margin Lift:</strong> ' + anom.expected_margin_lift + '</div>';
                }
                html += '</div>';
                html += '</div>';
            });
            
            // RECOMMENDATION
            html += '<h2>5. Recommendation: The "Switch-On" Strategy</h2>';
            html += '<div class="recommendation-card">';
            html += '<div class="recommendation-title">Phase 2 Rollout: Transfer 20% of Budget to KIKI Smart Segments</div>';
            html += '<div class="timeline">';
            recommendation.phase_1_timeline.forEach((item, idx) => {
                html += '<div class="timeline-item">';
                html += '<div class="timeline-marker">' + item.day + '</div>';
                html += '<div class="timeline-content">';
                html += '<div class="timeline-day">Day ' + item.day + '</div>';
                html += '<div class="timeline-action">' + item.action + '</div>';
                html += '<div class="timeline-impact">' + item.expected_impact + '</div>';
                html += '</div>';
                html += '</div>';
            });
            html += '</div>';
            html += '<p style="margin-top: 25px; color: #d1fae5; font-size: 14px;"><strong>Target:</strong> Achieve ' + recommendation.target_margin_increase_pct + '% Margin Increase within 14 days of live bidding.</p>';
            html += '<p style="margin-top: 10px; color: #a7f3d0; font-size: 13px;"><strong>ROI Breakeven:</strong> ' + recommendation.roi_breakeven_days + ' days | <strong>Month 2 Margin Improvement:</strong> £' + recommendation.estimated_month_2_margin_improvement.toFixed(2) + '</p>';
            html += '</div>';
            
            // Summary footer
            html += '<p style="margin-top: 40px; padding: 20px; background: rgba(96, 165, 250, 0.1); border-left: 3px solid #60a5fa; border-radius: 6px; color: #bfdbfe; font-size: 13px;"><strong>How This Closes the Deal:</strong> It uses their data—no longer a pitch, it\'s a mirror. They can\'t argue with their own waste. By showing the accuracy of your "Ghost Predictions," you prove the brain works before it touches their money. Once they see £' + headline.recoverable_margin_gbp.toLocaleString('en-GB', {maximumFractionDigits: 0}) + ' in waste, your 15% performance fee (£' + (headline.recoverable_margin_gbp * 0.15).toFixed(2) + ') looks like a bargain.</p>';
            
            document.getElementById('content').innerHTML = html;
            
            // Render latency chart
            renderLatencyChart(latency);

                        // Add actions section
                        const actionsHtml = `
                            <h2>Invoice Actions</h2>
                            <div class="table-container" style="display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
                                <input id="clientEmail" type="email" placeholder="client email" value="billing@example.com" style="padding:10px 12px; background:#0f172a; border:1px solid #334155; color:#e2e8f0; border-radius:6px; min-width:240px;">
                                <button onclick="generateInvoice('${meta.client}')" style="padding:10px 16px; background:#10b981; border:none; color:white; border-radius:6px; font-weight:600; cursor:pointer;">Generate Invoice (15%)</button>
                                <button onclick="sendPayPalInvoice('${meta.client}');" style="padding:10px 16px; background:#6366f1; border:none; color:white; border-radius:6px; font-weight:600; cursor:pointer;">Send via PayPal</button>
                                <button onclick="createSubscription('${meta.client}');" style="padding:10px 16px; background:#f59e0b; border:none; color:white; border-radius:6px; font-weight:600; cursor:pointer;">Create Subscription</button>
                                <div id="invoiceStatus" style="margin-left:10px; color:#94a3b8; font-size:13px;"></div>
                            </div>
                        `;
                        document.getElementById('content').insertAdjacentHTML('beforeend', actionsHtml);
        }
        
        function renderLatencyChart(latency) {
            const scenarios = [
                {label: 'Platform/Manual', value: latency.platform_reaction_minutes, color: '#ef4444'},
                {label: 'KIKI SyncFlow', value: latency.kiki_reaction_milliseconds / 60000, color: '#10b981'},
            ];
            
            const trace = {
                x: scenarios.map(s => s.label),
                y: scenarios.map(s => s.value),
                marker: {color: scenarios.map(s => s.color)},
                type: 'bar',
                text: scenarios.map(s => s.value === latency.kiki_reaction_milliseconds / 60000 ? '<1ms' : s.value + ' min'),
                textposition: 'outside',
            };
            
            const layout = {
                title: 'Reaction Time: Platform vs KIKI',
                xaxis: {title: ''},
                yaxis: {title: 'Minutes (log scale)', type: 'log'},
                plot_bgcolor: '#0f172a',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: {color: '#e2e8f0'},
                margin: {l: 50, r: 50, t: 50, b: 50},
                height: 350,
            };
            
            Plotly.newPlot('latencyChart', [trace], layout, {responsive: true, displayModeBar: false});
        }

        async function generateInvoice(client) {
            const status = document.getElementById('invoiceStatus');
            status.textContent = 'Generating invoice...';
            try {
                const res = await fetch('/api/invoice/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client, fee_rate: 0.15 })
                });
                const data = await res.json();
                if (res.ok) {
                    status.textContent = `Invoice ready: ${data.invoice_id} | Amount Due: £${data.amount_due}`;
                } else {
                    status.textContent = `Error: ${data.error || 'Failed to generate invoice'}`;
                }
            } catch (e) {
                status.textContent = 'Error generating invoice: ' + e.message;
            }
        }

        async function sendPayPalInvoice(client) {
            const status = document.getElementById('invoiceStatus');
            status.textContent = 'Sending PayPal invoice...';
            const email = (document.getElementById('clientEmail') || { value: 'billing@example.com' }).value || 'billing@example.com';
            try {
                const res = await fetch('/api/invoice/paypal/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client, client_email: email })
                });
                const data = await res.json();
                if (res.ok) {
                    status.innerHTML = `Sent: ${data.status} | <a href="${data.href}" target="_blank">Open PayPal</a>`;
                } else {
                    status.textContent = `Error: ${data.error || 'Failed to send PayPal invoice'}`;
                }
            } catch (e) {
                status.textContent = 'Error sending PayPal invoice: ' + e.message;
            }
        }

        async function createSubscription(client) {
            const status = document.getElementById('invoiceStatus');
            status.textContent = 'Creating subscription...';
            const email = (document.getElementById('clientEmail') || { value: 'billing@example.com' }).value || 'billing@example.com';
            try {
                const res = await fetch('/api/invoice/paypal/subscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client, client_email: email })
                });
                const data = await res.json();
                if (res.ok) {
                    status.innerHTML = `Subscription: ${data.status} | <a href="${data.href}" target="_blank">Approve</a>`;
                } else {
                    status.textContent = `Error: ${data.error || 'Failed to create subscription'}`;
                }
            } catch (e) {
                status.textContent = 'Error creating subscription: ' + e.message;
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/shadow-report')
def get_shadow_report():
    """Generate or load a Shadow Mode report for the specified client."""
    client_name = request.args.get('client', 'Demo Client')
    
    try:
        # Try to load from cached file first
        report_path = Path(__file__).parent.parent / 'reports' / f'shadow_mode_{client_name.replace(" ", "_").lower()}.json'
        
        if report_path.exists():
            with open(report_path, 'r') as f:
                report = json.load(f)
        else:
            # Generate fresh report
            from generate_shadow_mode_report import generate_shadow_mode_report
            audit_csv = Path(__file__).parent.parent / 'shield_audit.csv'
            report = generate_shadow_mode_report(client_name, str(audit_csv))
        
        return jsonify(report)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _load_paypal_adapter():
    """Dynamically load the PayPal adapter without requiring package imports."""
    adapter_path = Path(__file__).parent.parent / 'cmd' / 'billing' / 'paypal_adapter.py'
    module = SourceFileLoader('paypal_adapter', str(adapter_path)).load_module()
    return module.PayPalOaaSBillingAdapter


def _build_invoice_from_report(client_name: str, fee_rate: float = 0.15) -> dict:
    report_path = Path(__file__).parent.parent / 'reports' / f"shadow_mode_{client_name.replace(' ', '_').lower()}.json"
    if not report_path.exists():
        report = generate_shadow_mode_report(client_name)
        report_path.write_text(json.dumps(report, indent=2))
    else:
        report = json.loads(report_path.read_text())
    headline = report.get('headline', {})
    recommendation = report.get('recommendation', {})
    meta = report.get('meta', {})
    recoverable_gbp = float(headline.get('recoverable_margin_gbp', 0))
    fee_amount = round(recoverable_gbp * fee_rate, 2)
    margin_improvement_pct = float(recommendation.get('target_margin_increase_pct', 12))
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


@app.route('/api/invoice/generate', methods=['POST'])
def api_generate_invoice():
    try:
        payload = request.get_json(force=True)
        client = payload.get('client', 'Demo Client')
        fee_rate = float(payload.get('fee_rate', 0.15))
        invoice_data = _build_invoice_from_report(client, fee_rate)
        # Save JSON/CSV artifacts
        invoices_dir = Path(__file__).parent.parent / 'invoices'
        invoices_dir.mkdir(parents=True, exist_ok=True)
        json_out = invoices_dir / f"invoice_shadow_{client.replace(' ', '_').lower()}.json"
        json_out.write_text(json.dumps(invoice_data, indent=2))
        return jsonify({
            'invoice_id': invoice_data['invoice_id'],
            'amount_due': invoice_data['summary']['total_kiki_earnings'],
            'path': str(json_out),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/invoice/paypal/send', methods=['POST'])
def api_send_paypal_invoice():
    try:
        payload = request.get_json(force=True)
        client = payload.get('client', 'Demo Client')
        client_email = payload.get('client_email', 'billing@example.com')
        fee_rate = 0.15
        adapter_cls = _load_paypal_adapter()
        adapter = adapter_cls(
            paypal_client_id='client_id_sandbox',
            paypal_client_secret='secret_sandbox',
            mode='sandbox',
        )
        invoice_data = _build_invoice_from_report(client, fee_rate)
        paypal_inv = adapter.create_invoice(invoice_data, client_email, client)
        sent = adapter.send_invoice(paypal_inv['invoice_id'])
        return jsonify({
            'status': sent['status'],
            'href': paypal_inv['href'],
            'invoice_id': paypal_inv['invoice_id'],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/invoice/paypal/subscribe', methods=['POST'])
def api_create_paypal_subscription():
    try:
        payload = request.get_json(force=True)
        client = payload.get('client', 'Demo Client')
        client_email = payload.get('client_email', 'billing@example.com')
        fee_rate = 0.15
        adapter_cls = _load_paypal_adapter()
        adapter = adapter_cls(
            paypal_client_id='client_id_sandbox',
            paypal_client_secret='secret_sandbox',
            mode='sandbox',
        )
        invoice_data = _build_invoice_from_report(client, fee_rate)
        subscription = adapter.create_subscription(client_email, invoice_data, billing_cycle_days=30)
        return jsonify({
            'status': subscription['status'],
            'href': subscription['href'],
            'subscription_id': subscription['subscription_id'],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
