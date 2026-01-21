#!/usr/bin/env python3
"""
Lightweight Grafana Alternative - Pure Python Dashboard
No Docker required - visualizes Prometheus metrics in the browser
"""

from flask import Flask, render_template_string, jsonify, request
import requests
from datetime import datetime, timedelta
import json
from pathlib import Path
from importlib.machinery import SourceFileLoader
import threading
import time

app = Flask(__name__)

# HTML Template with enterprise-grade design
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIKI SyncBrain™ Enterprise Metrics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-primary: #0a0e1a;
            --bg-secondary: #111827;
            --bg-tertiary: #1f2937;
            --bg-card: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            --glow: rgba(99, 102, 241, 0.3);
        }
        
        body {
            background: linear-gradient(135deg, var(--bg-primary) 0%, #0f172a 100%);
            background-attachment: fixed;
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        /* Animated background gradient */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        
        .container {
            max-width: 1920px;
            margin: 0 auto;
            padding: 24px;
            position: relative;
            z-index: 1;
        }
        
        /* Header Section */
        .header {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
            border-radius: 16px;
            padding: 48px;
            margin-bottom: 32px;
            box-shadow: 0 20px 60px rgba(99, 102, 241, 0.3),
                        0 0 0 1px rgba(255, 255, 255, 0.1) inset;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/></pattern></defs><rect width="100%" height="100%" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        .header h1 {
            font-size: 3em;
            font-weight: 800;
            margin-bottom: 12px;
            background: linear-gradient(to right, #ffffff, #e0e7ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }
        
        .header-subtitle {
            font-size: 1.1em;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 400;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Navigation Tabs */
        .nav-tabs {
            display: flex;
            gap: 12px;
            margin-bottom: 32px;
            background: var(--bg-secondary);
            padding: 8px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .nav-tab {
            flex: 1;
            padding: 14px 24px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.95em;
        }
        
        .nav-tab:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        .nav-tab.active {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            box-shadow: 0 4px 12px var(--glow);
        }
        
        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 28px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(99, 102, 241, 0.2);
            border-color: var(--accent-primary);
        }
        
        .metric-card:hover::before {
            opacity: 1;
        }
        
        .metric-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 16px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            box-shadow: 0 4px 12px var(--glow);
        }
        
        .metric-label {
            font-size: 0.85em;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.2;
            margin-bottom: 8px;
        }
        
        .metric-change {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 0.85em;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
        }
        
        .metric-change.positive {
            color: var(--success);
            background: rgba(16, 185, 129, 0.1);
        }
        
        .metric-change.negative {
            color: var(--danger);
            background: rgba(239, 68, 68, 0.1);
        }
        
        /* Chart Containers */
        .chart-container {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        
        .chart-container:hover {
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }

        .billing-row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
            margin-top: 12px;
        }
        .billing-row select, .billing-row input {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 10px 12px;
            border-radius: 8px;
            min-width: 220px;
        }
        .action-btn {
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            transition: transform 0.15s ease, box-shadow 0.2s ease;
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 20px rgba(0,0,0,0.35);
        }
        .btn-generate { background: linear-gradient(135deg, #10b981, #059669); color: #fff; }
        .btn-send { background: linear-gradient(135deg, #6366f1, #4f46e5); color: #fff; }
        .btn-subscribe { background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; }
        .billing-status { color: var(--text-muted); margin-top: 8px; font-size: 0.9em; }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        
        .chart-title {
            font-size: 1.25em;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .chart-subtitle {
            font-size: 0.9em;
            color: var(--text-muted);
            margin-top: 4px;
        }
        
        .time-selector {
            display: flex;
            gap: 8px;
            background: var(--bg-tertiary);
            padding: 4px;
            border-radius: 8px;
        }
        
        .time-btn {
            padding: 8px 16px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 0.85em;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .time-btn:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }
        
        .time-btn.active {
            background: var(--accent-primary);
            color: white;
        }
        
        /* Alerts Section */
        .alerts-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }
        
        .alert-item {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px;
            background: var(--bg-tertiary);
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 4px solid;
            transition: all 0.2s ease;
        }
        
        .alert-item:hover {
            transform: translateX(4px);
        }
        
        .alert-item.success {
            border-color: var(--success);
            background: rgba(16, 185, 129, 0.05);
        }
        
        .alert-item.warning {
            border-color: var(--warning);
            background: rgba(245, 158, 11, 0.05);
        }
        
        .alert-item.danger {
            border-color: var(--danger);
            background: rgba(239, 68, 68, 0.05);
        }
        
        .alert-icon {
            font-size: 24px;
        }
        
        .alert-content {
            flex: 1;
        }
        
        .alert-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .alert-desc {
            font-size: 0.9em;
            color: var(--text-muted);
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 32px;
            margin-top: 48px;
            border-top: 1px solid var(--border-color);
        }
        
        .refresh-indicator {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: var(--bg-secondary);
            padding: 12px 24px;
            border-radius: 24px;
            font-size: 0.9em;
            color: var(--text-secondary);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid var(--border-color);
            border-top-color: var(--accent-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            
            .header {
                padding: 32px 24px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .nav-tabs {
                flex-direction: column;
            }
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 12px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 6px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-primary);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-content">
                <h1>🚀 KIKI SyncBrain™</h1>
                <div class="header-subtitle">
                    Enterprise Metrics Dashboard
                    <span class="status-badge">
                        <span class="status-dot"></span>
                        All Systems Operational
                    </span>
                </div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="nav-tab" onclick="showTab('integrations')">🔗 Integrations</button>
            <button class="nav-tab" onclick="showTab('performance')">⚡ Performance</button>
            <button class="nav-tab" onclick="showTab('alerts')">🔔 Alerts</button>
        </div>

        <!-- Billing Actions -->
        <div class="chart-container" style="border:1px solid var(--accent-primary);">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Shadow Mode Billing Actions</div>
                    <div class="chart-subtitle">Generate invoices, send via PayPal, and spin up subscriptions directly from the Command Center</div>
                </div>
            </div>
            <div class="billing-row">
                <select id="billing-client"></select>
                <input id="billing-email" type="email" placeholder="billing contact" value="billing@example.com" />
                <button class="action-btn btn-generate" onclick="generateInvoice()">Generate Invoice (15%)</button>
                <button class="action-btn btn-send" onclick="sendPayPalInvoice()">Send via PayPal</button>
                <button class="action-btn btn-subscribe" onclick="createSubscription()">Create Subscription</button>
            </div>
            <div id="billing-status" class="billing-status"></div>
        </div>

        <!-- Metrics Grid -->
        <div class="metrics-grid" id="metrics-grid"></div>

        <!-- Charts Section -->
        <div class="chart-container">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Integration Health Status</div>
                    <div class="chart-subtitle">Real-time status of all 13 billing adapters</div>
                </div>
                <div class="time-selector">
                    <button class="time-btn">1H</button>
                    <button class="time-btn active">6H</button>
                    <button class="time-btn">24H</button>
                    <button class="time-btn">7D</button>
                </div>
            </div>
            <div id="integration-health-chart"></div>
        </div>

        <div class="chart-container">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Payment Success Rates</div>
                    <div class="chart-subtitle">By provider (Stripe, Zuora, PayPal)</div>
                </div>
            </div>
            <div id="payment-success-chart"></div>
        </div>

        <div class="chart-container">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Customer Margin Improvement</div>
                    <div class="chart-subtitle">AI-driven optimization impact by client</div>
                </div>
            </div>
            <div id="margin-improvement-chart"></div>
        </div>

        <div class="chart-container">
            <div class="chart-header">
                <div>
                    <div class="chart-title">API Latency Distribution</div>
                    <div class="chart-subtitle">Response times across all endpoints</div>
                </div>
            </div>
            <div id="latency-chart"></div>
        </div>

        <!-- Alerts Section -->
        <div class="alerts-section" id="alerts-section">
            <h2 style="margin-bottom: 20px;">🔔 System Alerts</h2>
            <div id="alerts-container"></div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="refresh-indicator">
                <div class="spinner"></div>
                Last updated: <span id="last-update"></span>
            </div>
            <p style="margin-top: 16px; color: var(--text-muted); font-size: 0.9em;">
                KIKI SyncBrain™ v2.0 | Enterprise Metrics Platform | Built with ❤️ for OaaS
            </p>
        </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    // Update metric cards
                    const metricsGrid = document.getElementById('metrics-grid');
                    metricsGrid.innerHTML = '';
                    
                    // Key metrics
                    const keyMetrics = [
                        { label: 'LTV Predictions', value: data.ltv_predictions || 0, suffix: '' },
                        { label: 'Active Customers', value: data.active_customers || 0, suffix: '' },
                        { label: 'Total Revenue', value: (data.total_revenue_micros / 1000000).toFixed(2), suffix: 'k' },
                        { label: 'Prediction Confidence', value: (data.prediction_confidence * 100).toFixed(1), suffix: '%' },
                        { label: 'Integration Health', value: (data.integration_health * 100).toFixed(0), suffix: '%' },
                        { label: 'Audit Records', value: data.audit_trail_records || 0, suffix: '' }
                    ];
                    
                    keyMetrics.forEach(metric => {
                        const card = document.createElement('div');
                        card.className = 'metric-card';
                        card.innerHTML = `
                            <div class="metric-value">${metric.value}${metric.suffix}</div>
                            <div class="metric-label">${metric.label}</div>
                        `;
                        metricsGrid.appendChild(card);
                    });

                    // Update charts
                    updateIntegrationHealthChart(data.integration_details || {});
                    updatePaymentSuccessChart(data.payment_success || {});
                    updateMarginImprovementChart(data.margin_improvement || {});

                    // Update timestamp
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                })
                .catch(error => console.error('Error fetching metrics:', error));
        }

        function updateIntegrationHealthChart(details) {
            const adapters = Object.keys(details);
            const values = Object.values(details);
            
            const data = [{
                type: 'bar',
                x: adapters,
                y: values,

                marker: {
                    color: values.map(v => v > 0.5 ? '#3fb950' : '#f85149')
                }
            }];
            
            const layout = {
                title: 'Integration Health Status (13 Adapters)',
                paper_bgcolor: '#161b22',
                plot_bgcolor: '#161b22',
                font: { color: '#ffffff' },
                xaxis: { tickangle: -45 },
                yaxis: { title: 'Health (0=Down, 1=Up)' }
            };
            
            Plotly.newPlot('integration-health-chart', data, layout);
        }

        function updatePaymentSuccessChart(success) {
            const providers = Object.keys(success);
            const rates = Object.values(success);
            
            const data = [{
                type: 'bar',

                x: providers,
                y: rates.map(r => r * 100),
                marker: { color: '#58a6ff' }
            }];
            
            const layout = {
                title: 'Payment Success Rate by Provider',
                paper_bgcolor: '#161b22',
                plot_bgcolor: '#161b22',
                font: { color: '#ffffff' },
                yaxis: { title: 'Success Rate (%)' }
            };
            
            Plotly.newPlot('payment-success-chart', data, layout);
        }

        function updateMarginImprovementChart(margins) {
            const clients = Object.keys(margins);
            const improvements = Object.values(margins);
            
            const data = [{
                type: 'bar',
                x: clients,
                y: improvements,
                marker: { color: '#3fb950' }
            }];
            
            const layout = {
                title: 'Customer Margin Improvement (%)',
                paper_bgcolor: '#161b22',
                plot_bgcolor: '#161b22',
                font: { color: '#ffffff' },
                yaxis: { title: 'Improvement (%)' }
            };
            
            Plotly.newPlot('margin-improvement-chart', data, layout);
        }

        function populateBillingClients() {
            const select = document.getElementById('billing-client');
            const clients = [
                'Google Ads Partner',
                'Meta AI Studio',
                'TikTok Growth',
                'Storegrill Inc Ltd'
            ];
            select.innerHTML = clients.map(c => `<option value="${c}">${c}</option>`).join('');
        }

        function setBillingStatus(message, asHtml = false) {
            const el = document.getElementById('billing-status');
            if (asHtml) {
                el.innerHTML = message;
            } else {
                el.textContent = message;
            }
        }

        function billingPayload() {
            const client = (document.getElementById('billing-client') || { value: 'Demo Client' }).value || 'Demo Client';
            const client_email = (document.getElementById('billing-email') || { value: 'billing@example.com' }).value || 'billing@example.com';
            return { client, client_email };
        }

        async function generateInvoice() {
            const { client } = billingPayload();
            setBillingStatus('Generating invoice...');
            try {
                const res = await fetch('/api/invoice/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client, fee_rate: 0.15 })
                });
                const data = await res.json();
                if (res.ok) {
                    setBillingStatus(`Invoice ready: ${data.invoice_id} | Amount Due: £${data.amount_due}`);
                } else {
                    setBillingStatus(`Error: ${data.error || 'Failed to generate invoice'}`);
                }
            } catch (e) {
                setBillingStatus('Error generating invoice: ' + e.message);
            }
        }

        async function sendPayPalInvoice() {
            const { client, client_email } = billingPayload();
            setBillingStatus('Sending PayPal invoice...');
            try {
                const res = await fetch('/api/invoice/paypal/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client, client_email })
                });
                const data = await res.json();
                if (res.ok) {
                    setBillingStatus(`Sent: ${data.status} | <a href="${data.href}" target="_blank">Open PayPal</a>`, true);
                } else {
                    setBillingStatus(`Error: ${data.error || 'Failed to send PayPal invoice'}`);
                }
            } catch (e) {
                setBillingStatus('Error sending PayPal invoice: ' + e.message);
            }
        }

        async function createSubscription() {
            const { client, client_email } = billingPayload();
            setBillingStatus('Creating subscription...');
            try {
                const res = await fetch('/api/invoice/paypal/subscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client, client_email })
                });
                const data = await res.json();
                if (res.ok) {
                    setBillingStatus(`Subscription: ${data.status} | <a href="${data.href}" target="_blank">Approve</a>`, true);
                } else {
                    setBillingStatus(`Error: ${data.error || 'Failed to create subscription'}`);
                }
            } catch (e) {
                setBillingStatus('Error creating subscription: ' + e.message);
            }
        }

        // Initial load
        populateBillingClients();
        updateDashboard();
        
        // Auto-refresh every 5 seconds
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
"""

def parse_prometheus_metrics():
    """Parse metrics from Prometheus exporter"""
    try:
        response = requests.get("http://localhost:9090/metrics", timeout=2)
        if response.status_code == 200:
            metrics = {}
            lines = response.text.split('\n')
            
            for line in lines:
                if line and not line.startswith('#'):
                    try:
                        parts = line.split(' ')
                        if len(parts) >= 2:
                            # Parse metric name and labels
                            metric_full = parts[0]
                            metric_value = float(parts[-1])
                            
                            # Extract metric name (before {)
                            if '{' in metric_full:
                                metric_name = metric_full.split('{')[0]
                                labels = metric_full.split('{')[1].split('}')[0]
                            else:
                                metric_name = metric_full
                                labels = ''
                            
                            # Store metric
                            if metric_name not in metrics:
                                metrics[metric_name] = []
                            metrics[metric_name].append({
                                'value': metric_value,
                                'labels': labels
                            })
                    except:
                        pass
            
            return metrics
        return {}
    except:
        return {}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/metrics')
def get_metrics():
    """API endpoint to fetch current metrics"""
    raw_metrics = parse_prometheus_metrics()
    
    # Aggregate metrics for dashboard
    result = {
        'ltv_predictions': 0,
        'active_customers': 0,
        'total_revenue_micros': 0,
        'prediction_confidence': 0,
        'integration_health': 1.0,
        'audit_trail_records': 0,
        'integration_details': {},
        'payment_success': {},
        'margin_improvement': {}
    }
    
    # Extract specific metrics
    if 'ltv_predictions_total' in raw_metrics:
        result['ltv_predictions'] = sum(m['value'] for m in raw_metrics['ltv_predictions_total'])
    
    if 'active_customers' in raw_metrics:
        result['active_customers'] = int(raw_metrics['active_customers'][0]['value'])
    
    if 'total_revenue_micros' in raw_metrics:
        result['total_revenue_micros'] = raw_metrics['total_revenue_micros'][0]['value']
    
    if 'ltv_prediction_confidence_score' in raw_metrics:
        result['prediction_confidence'] = raw_metrics['ltv_prediction_confidence_score'][0]['value']
    
    if 'audit_trail_records_total' in raw_metrics:
        result['audit_trail_records'] = int(raw_metrics['audit_trail_records_total'][0]['value'])
    
    # Integration health details
    if 'integration_health_status' in raw_metrics:
        for metric in raw_metrics['integration_health_status']:
            adapter_name = metric['labels'].split('adapter_name="')[1].split('"')[0] if 'adapter_name=' in metric['labels'] else 'unknown'
            result['integration_details'][adapter_name] = metric['value']
    
    # Payment success rates
    if 'payment_success_rate' in raw_metrics:
        for metric in raw_metrics['payment_success_rate']:
            provider = metric['labels'].split('provider="')[1].split('"')[0] if 'provider=' in metric['labels'] else 'unknown'
            result['payment_success'][provider] = metric['value']
    
    # Margin improvements
    if 'margin_improvement_percentage' in raw_metrics:
        for metric in raw_metrics['margin_improvement_percentage']:
            client_id = metric['labels'].split('client_id="')[1].split('"')[0] if 'client_id=' in metric['labels'] else 'unknown'
            result['margin_improvement'][client_id] = metric['value']
    
    return jsonify(result)


def _load_paypal_adapter():
    adapter_path = Path(__file__).parent.parent / 'cmd' / 'billing' / 'paypal_adapter.py'
    module = SourceFileLoader('paypal_adapter', str(adapter_path)).load_module()
    return module.PayPalOaaSBillingAdapter


def _build_invoice_from_report(client_name: str, fee_rate: float = 0.15) -> dict:
    from generate_shadow_mode_report import generate_shadow_mode_report
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
        adapter_cls = _load_paypal_adapter()
        adapter = adapter_cls(
            paypal_client_id='client_id_sandbox',
            paypal_client_secret='secret_sandbox',
            mode='sandbox',
        )
        invoice_data = _build_invoice_from_report(client, 0.15)
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
        adapter_cls = _load_paypal_adapter()
        adapter = adapter_cls(
            paypal_client_id='client_id_sandbox',
            paypal_client_secret='secret_sandbox',
            mode='sandbox',
        )
        invoice_data = _build_invoice_from_report(client, 0.15)
        subscription = adapter.create_subscription(client_email, invoice_data, billing_cycle_days=30)
        return jsonify({
            'status': subscription['status'],
            'href': subscription['href'],
            'subscription_id': subscription['subscription_id'],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/shadow-mode')
def shadow_mode():
    """Redirect to Shadow Mode Report dashboard on port 5001"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecting to Shadow Mode Report...</title>
        <meta charset="utf-8">
        <script>
            // Redirect to Shadow Mode dashboard
            window.location.href = 'http://localhost:5001';
        </script>
    </head>
    <body>
        <p>Redirecting to Shadow Mode Report dashboard...</p>
        <p>If you are not redirected, <a href="http://localhost:5001">click here</a>.</p>
    </body>
    </html>
    """)

if __name__ == '__main__':
    print("🎯 Starting KIKI Grafana Alternative Dashboard...")
    print("📊 Dashboard URL: http://localhost:8502")
    print("✅ No Docker required!")
    print("\nFeatures:")
    print("  • Real-time Prometheus metrics")
    print("  • Interactive charts (Plotly)")
    print("  • Auto-refresh every 5 seconds")
    print("  • Dark theme UI")
    print("\n" + "="*60)
    
    app.run(host='0.0.0.0', port=8502, debug=False)
