// --- SyncMemory: Top Styles ---
async function loadSyncMemoryTopStyles() {
    const res = await fetch(`${API_BASE}/creative-gallery/memory/top-styles`);
    let topStyles = [];
    if (res.ok) {
        topStyles = (await res.json()).top_styles;
    }
    renderSyncMemoryTopStyles(topStyles);
}

function renderSyncMemoryTopStyles(topStyles) {
    const container = document.getElementById('syncmemory-top-styles');
    if (!container) return;
    if (!topStyles.length) {
        container.innerHTML = '<p class="text-muted">No memory insights yet.</p>';
        return;
    }
    let html = '<h6>Top Creative Styles (Last 7 Days)</h6><ul class="list-group">';
    topStyles.forEach(style => {
        html += `<li class="list-group-item bg-dark text-light d-flex justify-content-between align-items-center">
            <span><b>${style.style}</b></span>
            <span class="badge bg-success">$${style.total_revenue.toFixed(2)} / ${style.count} uses</span>
        </li>`;
    });
    html += '</ul>';
    container.innerHTML = html;
}
// KIKI Super-Admin Dashboard - Client Application

const API_BASE = 'http://localhost:8085';
const WS_URL = 'ws://localhost:8085/live/metrics';

let ws = null;
let currentMetrics = {};
let alerts = [];
let actions = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('KIKI Super-Admin Dashboard loaded');
    initWebSocket();
    updateClock();
    loadInitialData();
    setInterval(updateClock, 1000);
});

// Update clock in header
function updateClock() {
    const now = new Date();
    const formatted = now.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
    document.getElementById('current-time').textContent = formatted;
}

// Initialize WebSocket connection
function initWebSocket() {
    try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log('✅ WebSocket connected to Admin API');
            updateStatusBadge('online');
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                
                if (message.type === 'metrics') {
                    currentMetrics = message.data;
                    updateDashboard(message.data);
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatusBadge('offline');
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateStatusBadge('offline');
            // Reconnect after 5 seconds
            setTimeout(initWebSocket, 5000);
        };
    } catch (e) {
        console.error('Failed to connect to WebSocket:', e);
    }
}

// Load initial data via REST API
async function loadInitialData() {
    try {
        // Load metrics
        const metricsRes = await fetch(`${API_BASE}/api/admin/metrics`);
        if (metricsRes.ok) {
            const metrics = await metricsRes.json();
            updateDashboard(metrics);
        }

        // Load alerts
        const alertsRes = await fetch(`${API_BASE}/api/admin/alerts`);
        if (alertsRes.ok) {
            alerts = await alertsRes.json();
            displayAlerts();
        }

        // Load audit log
        const auditRes = await fetch(`${API_BASE}/api/admin/audit-log`);
        if (auditRes.ok) {
            actions = await auditRes.json();
            displayActions();
        }
    } catch (e) {
        console.error('Error loading initial data:', e);
    }
}

// Update dashboard with metrics
function updateDashboard(metrics) {
    if (!metrics || !metrics.services) return;

    // Update status badge
    const upCount = Object.values(metrics.services).filter(s => s.status === 'up').length;
    const totalCount = Object.values(metrics.services).length;
    
    if (upCount === totalCount) {
        updateStatusBadge('all-systems');
    } else if (upCount === 0) {
        updateStatusBadge('critical');
    } else {
        updateStatusBadge('degraded');
    }

    // Update KPIs
    document.getElementById('services-up').textContent = `${upCount}/${totalCount}`;
    document.getElementById('campaigns').textContent = metrics.active_campaigns || '847';
    document.getElementById('revenue').textContent = formatCurrency(metrics.daily_revenue || 45320);
    document.getElementById('uptime').textContent = formatUptime(metrics.timestamp);

    // Capital Leak metric
    const capitalLeak = metrics.capital_leak ?? 0;
    const capitalLeakElem = document.getElementById('capital-leak');
    capitalLeakElem.textContent = `${capitalLeak.toFixed(2)}%`;
    if (capitalLeak > 10) {
        capitalLeakElem.classList.add('pulse', 'text-neon-green');
    } else {
        capitalLeakElem.classList.remove('pulse', 'text-neon-green');
    }

    // Update service health table
    updateServiceHealth(metrics.services);

    // Update service detail cards
    updateServiceCards(metrics.services);
}

// Update service health table
function updateServiceHealth(services) {
    const tbody = document.getElementById('service-rows');
    tbody.innerHTML = '';

    const serviceOrder = ['syncshield', 'syncengage', 'syncflow', 'synccreate', 'syncvalue'];
    
    Object.entries(services)
        .sort((a, b) => serviceOrder.indexOf(a[0]) - serviceOrder.indexOf(b[0]))
        .forEach(([name, service]) => {
            const row = document.createElement('tr');
            const statusIcon = getStatusIcon(service.status);
            const latencyP95 = (service.latency?.p95 || service.latency?.current || 0).toFixed(0);
            
            row.innerHTML = `
                <td><strong>${formatServiceName(name)}</strong></td>
                <td>${statusIcon}</td>
                <td><span class="status-${service.status}">${(service.uptime || 99).toFixed(2)}%</span></td>
                <td>${(service.requests_per_sec || 0).toFixed(0)}</td>
                <td>${(service.error_rate || 0).toFixed(2)}%</td>
                <td>${latencyP95}ms</td>
                <td>
                    <button class="btn btn-sm btn-link text-info" onclick="restartService('${name}')" title="Restart">
                        <i class="fas fa-sync"></i>
                    </button>
                    <button class="btn btn-sm btn-link text-warning" onclick="viewServiceLogs('${name}')" title="View Logs">
                        <i class="fas fa-file-alt"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
}

// Update service detail cards
function updateServiceCards(services) {
    const container = document.getElementById('services-detail');
    container.innerHTML = '';

    Object.entries(services).forEach(([name, service]) => {
        const statusIcon = getStatusIcon(service.status);
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-3';
        card.innerHTML = `
            <div class="service-card">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <div class="service-name">${formatServiceName(name)}</div>
                        <span class="badge ${service.status === 'up' ? 'bg-success' : 'bg-danger'}">${statusIcon}</span>
                    </div>
                    <div class="dropdown">
                        <button class="btn btn-sm btn-link text-light" type="button" data-bs-toggle="dropdown">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-dark">
                            <li><a class="dropdown-item" onclick="restartService('${name}')">Restart</a></li>
                            <li><a class="dropdown-item" onclick="pauseService('${name}')">Pause</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" onclick="viewServiceLogs('${name}')">View Logs</a></li>
                        </ul>
                    </div>
                </div>
                <div class="service-stats">
                    <div class="service-stat">
                        <div class="service-stat-label">Uptime</div>
                        <div class="service-stat-value">${(service.uptime || 99).toFixed(2)}%</div>
                    </div>
                    <div class="service-stat">
                        <div class="service-stat-label">Req/s</div>
                        <div class="service-stat-value">${(service.requests_per_sec || 0).toFixed(0)}</div>
                    </div>
                    <div class="service-stat">
                        <div class="service-stat-label">Error Rate</div>
                        <div class="service-stat-value">${(service.error_rate || 0).toFixed(2)}%</div>
                    </div>
                    <div class="service-stat">
                        <div class="service-stat-label">Latency (ms)</div>
                        <div class="service-stat-value">${((service.latency?.current) || 0).toFixed(0)}</div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

// Display alerts
function displayAlerts() {
    const container = document.getElementById('alerts-list');
    container.innerHTML = '';

    if (alerts.length === 0) {
        container.innerHTML = '<p class="text-muted">No active alerts</p>';
        return;
    }

    alerts.forEach(alert => {
        const icon = getSeverityIcon(alert.severity);
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${getSeverityCSSClass(alert.severity)}`;
        alertDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="fw-bold">${icon} ${alert.message}</div>
                    <small class="text-muted">${new Date(alert.timestamp).toLocaleTimeString()}</small>
                </div>
                <button class="btn btn-sm btn-link text-light" onclick="dismissAlert('${alert.id}')" title="Dismiss">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        container.appendChild(alertDiv);
    });
}

// Display admin actions
function displayActions() {
    const container = document.getElementById('actions-list');
    container.innerHTML = '';

    if (actions.length === 0) {
        container.innerHTML = '<p class="text-muted">No recent actions</p>';
        return;
    }

    actions.slice(-10).reverse().forEach(action => {
        const statusIcon = action.status === 'completed' ? '✅' : '⏳';
        const actionDiv = document.createElement('div');
        actionDiv.className = 'mb-2 pb-2 border-bottom border-secondary';
        actionDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="fw-bold">${statusIcon} ${action.action}</div>
                    <small class="text-muted">${action.resource}</small>
                </div>
                <small class="text-muted">${new Date(action.timestamp).toLocaleTimeString()}</small>
            </div>
        `;
        container.appendChild(actionDiv);
    });
}

// --- Creative Gallery ---
async function loadCreativeGallery() {
    // Example: Fetch gallery data from API (replace with real endpoint)
    const res = await fetch(`${API_BASE}/api/creative-gallery`);
    let gallery = [];
    if (res.ok) {
        gallery = await res.json();
    } else {
        // Fallback: demo data
        gallery = [
            {
                video_url: 'https://www.w3schools.com/html/mov_bbb.mp4',
                ltv: 142.50,
                title: 'Demo Creative 1'
            },
            {
                video_url: 'https://www.w3schools.com/html/movie.mp4',
                ltv: 98.75,
                title: 'Demo Creative 2'
            }
        ];
    }
    renderCreativeGallery(gallery);
}

function renderCreativeGallery(gallery) {
    const grid = document.getElementById('gallery-grid');
    grid.innerHTML = '';
    gallery.forEach(item => {
        const col = document.createElement('div');
        col.className = 'col-md-4';
        col.innerHTML = `
            <div class="card bg-dark border-neon-pink h-100">
                <video src="${item.video_url}" controls class="w-100 rounded mb-2" style="max-height:340px;background:#000;"></video>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="fw-bold text-neon-green">LTV: $${item.ltv.toFixed(2)}</span>
                    <span class="text-muted small">${item.title || ''}</span>
                </div>
            </div>
        `;
        grid.appendChild(col);
    });
}

// Load gallery when tab is shown
const creativeGalleryTab = document.querySelector('a[href="#creative-gallery"]');
if (creativeGalleryTab) {
    creativeGalleryTab.addEventListener('shown.bs.tab', loadCreativeGallery);
}

// --- Creative Gallery: Generate Button ---
function showGenerateCreativeModal() {
    const modalHtml = `
    <div class="modal fade" id="generateCreativeModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content bg-darker border-secondary">
          <div class="modal-header border-secondary">
            <h5 class="modal-title">Generate New Creative</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Background Image URL</label>
              <input type="text" class="form-control bg-secondary border-secondary text-light" id="creative-bg-url" placeholder="https://...">
            </div>
            <div class="mb-3">
              <label class="form-label">Product Hook Text</label>
              <input type="text" class="form-control bg-secondary border-secondary text-light" id="creative-hook" placeholder="Your Next Best Seller">
            </div>
            <div class="mb-3">
              <label class="form-label">Product ID</label>
              <input type="text" class="form-control bg-secondary border-secondary text-light" id="creative-product-id" placeholder="sku1234">
            </div>
          </div>
          <div class="modal-footer border-secondary">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="generateCreativeBtn">Generate</button>
          </div>
        </div>
      </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('generateCreativeModal'));
    modal.show();
    document.getElementById('generateCreativeBtn').onclick = async function() {
        const bg_image = document.getElementById('creative-bg-url').value;
        const hook = document.getElementById('creative-hook').value;
        const product_id = document.getElementById('creative-product-id').value;
        if (!bg_image || !hook || !product_id) return alert('All fields required.');
        const res = await fetch(`${API_BASE}/api/creative-gallery/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bg_image, product: { id: product_id, hook } })
        });
        if (res.ok) {
            showNotification('Creative generated!');
            loadCreativeGallery();
            modal.hide();
        } else {
            showNotification('Failed to generate creative', 'error');
        }
    };
    document.getElementById('generateCreativeModal').addEventListener('hidden.bs.modal', function() {
        document.getElementById('generateCreativeModal').remove();
    });
}

// Add button to Creative Gallery tab
const creativeGalleryTabContent = document.getElementById('creative-gallery');
if (creativeGalleryTabContent) {
    const btn = document.createElement('button');
    btn.className = 'btn btn-neon mb-3';
    btn.innerHTML = '<i class="fas fa-plus"></i> Generate Creative';
    btn.onclick = showGenerateCreativeModal;
    creativeGalleryTabContent.querySelector('.card-body').prepend(btn);
}

// --- Admin Approval UI ---
async function loadAdminApprovals() {
    const res = await fetch(`${API_BASE}/api/creative-gallery/pending-approvals`);
    let approvals = [];
    if (res.ok) {
        approvals = await res.json();
    }
    renderAdminApprovals(approvals);
}

function renderAdminApprovals(approvals) {
    const grid = document.getElementById('approvals-list');
    grid.innerHTML = '';
    if (!approvals.length) {
        grid.innerHTML = '<p class="text-muted">No pending approvals</p>';
        return;
    }
    approvals.forEach(item => {
        const col = document.createElement('div');
        col.className = 'col-md-6';
        col.innerHTML = `
            <div class="card bg-dark border-neon-pink h-100">
                <video src="${item.video_url}" controls class="w-100 rounded mb-2" style="max-height:340px;background:#000;"></video>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="fw-bold">${item.creative_id}</span>
                    <div>
                        <button class="btn btn-success btn-sm me-1" onclick="approveCreative('${item.creative_id}')"><i class="fas fa-check"></i> Approve</button>
                        <button class="btn btn-danger btn-sm me-1" onclick="rejectCreative('${item.creative_id}')"><i class="fas fa-times"></i> Reject</button>
                        <button class="btn btn-warning btn-sm" onclick="escalateCreative('${item.creative_id}')"><i class="fas fa-exclamation-triangle"></i> Escalate</button>
                    </div>
                </div>
            </div>
        `;
        grid.appendChild(col);
    });
}

async function approveCreative(creative_id) {
    const res = await fetch(`${API_BASE}/api/creative-gallery/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ creative_id })
    });
    if (res.ok) {
        showNotification('Creative approved!');
        loadAdminApprovals();
        loadCreativeGallery();
    } else {
        showNotification('Approval failed', 'error');
    }
}

// --- Anomaly Detection Visualization ---
async function loadAnomalies() {
    const res = await fetch(`${API_BASE}/api/creative-gallery/analytics/anomalies`);
    let anomalies = [];
    if (res.ok) {
        anomalies = (await res.json()).anomalies;
    }
    renderAnomaliesOnTrendChart(anomalies);
}

function renderAnomaliesOnTrendChart(anomalies) {
    if (!window.creativeTrendChart || !anomalies.length) return;
    const chart = window.creativeTrendChart;
    // Highlight anomaly points
    chart.data.datasets.forEach(ds => {
        if (!ds.pointBackgroundColor) ds.pointBackgroundColor = Array(ds.data.length).fill('#00ff88');
    });
    chart.data.labels.forEach((label, i) => {
        if (anomalies.includes(label)) {
            chart.data.datasets[0].pointBackgroundColor[i] = '#ff0000';
        }
    });
    chart.update();
}

// --- Anomaly Explanations & Interactivity ---
async function loadAnomalyExplanations() {
    const res = await fetch(`${API_BASE}/api/creative-gallery/analytics/anomaly-explanations`);
    let explanations = {};
    if (res.ok) {
        explanations = (await res.json()).explanations;
    }
    window.anomalyExplanations = explanations;
}

// Show explanation on anomaly click
if (document.getElementById('creative-trend-chart')) {
    document.getElementById('creative-trend-chart').onclick = function(evt) {
        if (!window.creativeTrendChart) return;
        const points = window.creativeTrendChart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
        if (points.length) {
            const idx = points[0].index;
            const label = window.creativeTrendChart.data.labels[idx];
            if (window.anomalyExplanations && window.anomalyExplanations[label]) {
                const exp = window.anomalyExplanations[label];
                showNotification(`Anomaly: ${label}\nCount: ${exp.count}\nTop Creatives: ${exp.top_creatives.join(', ')}\nNote: ${exp.note}`);
            } else {
                showNotification('Date: ' + label + ', Approvals: ' + window.creativeTrendChart.data.datasets[0].data[idx]);
            }
        }
    };
}

// Load anomaly explanations after anomalies
if (creativeAnalyticsTab) {
    creativeAnalyticsTab.addEventListener('shown.bs.tab', () => {
        setTimeout(loadAnomalyExplanations, 1300);
        setTimeout(loadSyncMemoryTopStyles, 800);
    });
}

// --- Anomaly Root-Cause Analysis ---
async function loadAnomalyRootCauses() {
    const res = await fetch(`${API_BASE}/api/creative-gallery/analytics/anomaly-root-cause`);
    let rootCauses = {};
    if (res.ok) {
        rootCauses = (await res.json()).root_causes;
    }
    window.anomalyRootCauses = rootCauses;
}

// Show root cause on anomaly click
if (document.getElementById('creative-trend-chart')) {
    document.getElementById('creative-trend-chart').onclick = function(evt) {
        if (!window.creativeTrendChart) return;
        const points = window.creativeTrendChart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
        if (points.length) {
            const idx = points[0].index;
            const label = window.creativeTrendChart.data.labels[idx];
            if (window.anomalyRootCauses && window.anomalyRootCauses[label]) {
                showNotification('Root Cause(s): ' + window.anomalyRootCauses[label].join('; '));
            }
        }
    };
}

// Load root causes after anomaly explanations
if (creativeAnalyticsTab) {
    creativeAnalyticsTab.addEventListener('shown.bs.tab', () => {
        setTimeout(loadAnomalyRootCauses, 1400);
    });
}

// --- Admin Workflow Actions ---
async function rejectCreative(creative_id) {
    const reason = prompt('Reason for rejection?');
    if (!reason) return;
    const res = await fetch(`${API_BASE}/api/creative-gallery/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ creative_id, reason })
    });
    if (res.ok) {
        showNotification('Creative rejected.');
        loadAdminApprovals();
        loadCreativeGallery();
    } else {
        showNotification('Rejection failed', 'error');
    }
}

async function escalateCreative(creative_id) {
    const reason = prompt('Reason for escalation?');
    if (!reason) return;
    const res = await fetch(`${API_BASE}/api/creative-gallery/escalate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ creative_id, reason })
    });
    if (res.ok) {
        showNotification('Creative escalated.');
    } else {
        showNotification('Escalation failed', 'error');
    }
}

// API Calls

async function restartService(serviceName) {
    if (!confirm(`Restart ${serviceName}?`)) return;

    try {
        const res = await fetch(`${API_BASE}/api/admin/services/${serviceName}/restart`, {
            method: 'POST'
        });

        if (res.ok) {
            showNotification(`${serviceName} restart initiated`, 'success');
        } else {
            showNotification(`Failed to restart ${serviceName}`, 'error');
        }
    } catch (e) {
        console.error('Error restarting service:', e);
        showNotification('Error restarting service', 'error');
    }
}

function pauseService(serviceName) {
    console.log('Pause service:', serviceName);
}

function viewServiceLogs(serviceName) {
    console.log('View logs for:', serviceName);
}

function refreshServices() {
    loadInitialData();
    showNotification('Services refreshed', 'info');
}

function exportAuditLog() {
    const csv = convertToCSV(actions);
    downloadCSV(csv, 'audit-log.csv');
    showNotification('Audit log exported', 'success');
}

function dismissAlert(alertId) {
    alerts = alerts.filter(a => a.id !== alertId);
    displayAlerts();
}

function logout() {
    if (confirm('Logout from Super-Admin?')) {
        // In production, clear session/token
        window.location.href = '/';
    }
}

// Utility Functions

function getStatusIcon(status) {
    const icons = {
        'up': '🟢 Up',
        'down': '🔴 Down',
        'degraded': '🟡 Degraded'
    };
    return icons[status] || '❓ Unknown';
}

function getSeverityIcon(severity) {
    const icons = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'critical': '🔴'
    };
    return icons[severity] || '❓';
}

function getSeverityCSSClass(severity) {
    const classes = {
        'info': 'info',
        'warning': 'warning',
        'critical': 'danger'
    };
    return classes[severity] || 'info';
}

function formatServiceName(name) {
    const names = {
        'syncshield': 'SyncShield',
        'syncengage': 'SyncEngage',
        'syncflow': 'SyncFlow',
        'synccreate': 'SyncCreate',
        'syncvalue': 'SyncValue'
    };
    return names[name] || name;
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0
    }).format(value);
}

function formatUptime(timestamp) {
    // Calculate uptime from timestamp
    const now = new Date();
    const uptime = new Date(now - new Date(timestamp));
    const days = uptime.getUTCDate() - 1;
    const hours = uptime.getUTCHours();
    const minutes = uptime.getUTCMinutes();
    
    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    }
    return `${hours}h ${minutes}m`;
}

function updateStatusBadge(status) {
    const badge = document.getElementById('status-badge');
    const statusMap = {
        'online': { class: 'bg-success', text: '🟢 All Systems' },
        'offline': { class: 'bg-danger', text: '🔴 Offline' },
        'degraded': { class: 'bg-warning text-dark', text: '🟡 Degraded' },
        'all-systems': { class: 'bg-success', text: '🟢 All Systems' },
        'critical': { class: 'bg-danger', text: '🔴 Critical' }
    };
    
    const mapping = statusMap[status] || statusMap['online'];
    badge.className = `badge ${mapping.class}`;
    badge.textContent = mapping.text;
}

function showNotification(message, type = 'info') {
    // Create toast notification
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} position-fixed`;
    alertDiv.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.textContent = message;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// CSV Export
function convertToCSV(data) {
    const headers = ['ID', 'Timestamp', 'Admin', 'Action', 'Resource', 'Status'];
    const rows = data.map(action => [
        action.id,
        new Date(action.timestamp).toISOString(),
        action.admin_id,
        action.action,
        action.resource,
        action.status
    ]);
    
    const csv = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    return csv;
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// --- Performance by Campaign/Product Chart ---
async function loadPerformanceChart() {
    const res = await fetch(`${API_BASE}/api/creative-gallery/analytics/performance`);
    let perf = {};
    if (res.ok) {
        perf = (await res.json()).performance;
    }
    renderPerformanceChart(perf);
}

function renderPerformanceChart(perf) {
    const ctx = document.createElement('canvas');
    ctx.height = 120;
    ctx.className = 'mb-4';
    document.getElementById('creative-analytics').querySelector('.card-body').appendChild(ctx);
    const labels = Object.keys(perf);
    const approved = labels.map(k => perf[k].approved);
    const rejected = labels.map(k => perf[k].rejected);
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: 'Approved', data: approved, backgroundColor: '#00ff88' },
                { label: 'Rejected', data: rejected, backgroundColor: '#ff00cc' }
            ]
        },
        options: {
            plugins: { legend: { display: true } },
            scales: { x: { title: { display: true, text: 'Campaign/Product' } }, y: { beginAtZero: true } },
            onClick: async function(evt, elements) {
                if (elements.length) {
                    const idx = elements[0].index;
                    const key = labels[idx];
                    const res = await fetch(`${API_BASE}/api/creative-gallery/analytics/drilldown/${key}`);
                    let data = [];
                    if (res.ok) data = (await res.json()).creatives;
                    showNotification('Drill-down: ' + data.map(c => c.creative_id).join(', '));
                }
            }
        }
    });
}

// --- Export All Analytics Button ---
async function exportAllAnalyticsCSV() {
    const res = await fetch(`${API_BASE}/api/creative-gallery/analytics/export`);
    if (res.ok) {
        const data = await res.json();
        showNotification('Analytics exported: ' + data.csv, 'success');
        window.open('/' + data.csv, '_blank');
    } else {
        showNotification('Export failed', 'error');
    }
}

// Add export button to analytics tab
if (analyticsTabContent) {
    const btn = document.createElement('button');
    btn.className = 'btn btn-neon mb-3';
    btn.innerHTML = '<i class="fas fa-download"></i> Export All Analytics';
    btn.onclick = exportAllAnalyticsCSV;
    analyticsTabContent.querySelector('.card-body').prepend(btn);
}

// --- Admin Summary Panel ---
async function loadAdminSummary() {
    const res = await fetch(`${API_BASE}/api/creative-gallery/admin-summary`);
    let summary = {};
    if (res.ok) {
        summary = await res.json();
    }
    renderAdminSummary(summary);
}

function renderAdminSummary(summary) {
    const div = document.createElement('div');
    div.className = 'alert alert-info';
    div.innerHTML = `
        <strong>Admin Summary:</strong> Total: ${summary.total_creatives}, Pending: ${summary.pending}, Approved: ${summary.approved}, Rejected: ${summary.rejected}, Escalated: ${summary.escalated}, Last Approval: ${summary.last_approval}
    `;
    document.getElementById('creative-analytics').querySelector('.card-body').prepend(div);
}

// Load deeper analytics and admin summary when analytics tab is shown
if (creativeAnalyticsTab) {
    creativeAnalyticsTab.addEventListener('shown.bs.tab', () => {
        loadPerformanceChart();
        loadAdminSummary();
    });
}

// Add granular drill-down for creative actions
function showCreativeActions(creativeId) {
  fetch(`/creative-gallery/analytics/drilldown/creative/${creativeId}`)
    .then(r => r.json())
    .then(data => {
      let html = '<h4>Action History</h4><ul>';
      data.actions.forEach(a => {
        html += `<li>${a.timestamp || ''}: ${a.auto_rejected ? 'Auto-Rejected' : (a.auto_approved ? 'Auto-Approved' : a.action || 'Unknown')}</li>`;
      });
      html += '</ul>';
      showModal(html);
    });
}

// Add export as JSON and Excel
$('#export-json-btn').on('click', function() {
  fetch('/creative-gallery/analytics/export/json')
    .then(r => r.json())
    .then(data => {
      window.open('/' + data.json, '_blank');
    });
});
$('#export-xlsx-btn').on('click', function() {
  fetch('/creative-gallery/analytics/export/xlsx')
    .then(r => r.json())
    .then(data => {
      window.open('/' + data.xlsx, '_blank');
    });
});
$('#creative-analytics').on('click', '.creative-drilldown', function() {
  const creativeId = $(this).data('creative-id');
  showCreativeActions(creativeId);
});

// Anomaly detection and trend analytics
$('#anomaly-btn').on('click', function() {
  fetch('/creative-gallery/analytics/anomaly')
    .then(r => r.json())
    .then(data => {
      let html = `<h4>Anomalies (mean: ${data.mean.toFixed(2)}, std: ${data.std.toFixed(2)})</h4><ul>`;
      data.anomalies.forEach(c => {
        html += `<li>${c.creative_id}: LTV ${c.ltv}</li>`;
      });
      html += '</ul>';
      showModal(html);
    });
});
$('#trend-btn').on('click', function() {
  fetch('/creative-gallery/analytics/trend')
    .then(r => r.json())
    .then(data => {
      showModal(`<h4>LTV Trend: ${data.trend} (slope: ${data.slope})</h4>`);
    });
});
// Filtered export
$('#export-csv-filtered-btn').on('click', function() {
  const start = $('#filter-start').val();
  const end = $('#filter-end').val();
  const status = $('#filter-status').val();
  fetch('/creative-gallery/analytics/export/csv', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({start, end, status})
  })
    .then(r => r.text())
    .then(csv => {
      const blob = new Blob([csv], {type: 'text/csv'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'analytics_filtered.csv';
      a.click();
      URL.revokeObjectURL(url);
    });
});
// Escalate workflow
$('#escalate-btn').on('click', function() {
  fetch('/creative-gallery/workflow/escalate', {method: 'POST'})
    .then(r => r.json())
    .then(data => {
      showModal(`<h4>Escalated Creatives</h4><ul>${data.escalated.map(cid => `<li>${cid}</li>`).join('')}</ul>`);
    });
});

// Live SyncShield™ log feed
function refreshSyncShieldLog() {
  fetch('/syncshield/log')
    .then(r => r.json())
    .then(data => {
      let html = '<ul>';
      data.log.slice().reverse().forEach(e => {
        html += `<li><b>${e.timestamp}</b> [${e.creative_id}]: ${e.reason}</li>`;
      });
      html += '</ul>';
      $('#syncshield-log').html(html);
    });
}
setInterval(refreshSyncShieldLog, 5000);
$('#trigger-syncshield-test-btn').on('click', function() {
  fetch('/syncshield/log/test', {method: 'POST'})
    .then(r => r.json())
    .then(data => {
      refreshSyncShieldLog();
      showModal(`<b>Test event triggered:</b><br>${JSON.stringify(data.event)}`);
    });
});
$('#filter-syncshield-btn').on('click', function() {
  const creativeId = $('#filter-syncshield-id').val();
  const reason = $('#filter-syncshield-reason').val();
  fetch('/syncshield/log/filter', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({creative_id: creativeId, reason})
  })
    .then(r => r.json())
    .then(data => {
      let html = '<ul>';
      data.log.slice().reverse().forEach(e => {
        html += `<li><b>${e.timestamp}</b> [${e.creative_id}]: ${e.reason}</li>`;
      });
      html += '</ul>';
      $('#syncshield-log').html(html);
    });
});
$('#advanced-filter-syncshield-btn').on('click', function() {
  const creativeId = $('#filter-syncshield-id').val();
  const reason = $('#filter-syncshield-reason').val();
  const start = $('#filter-syncshield-start').val();
  const end = $('#filter-syncshield-end').val();
  fetch('/syncshield/log/filter/advanced', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({creative_id: creativeId, reason, start, end})
  })
    .then(r => r.json())
    .then(data => {
      let html = '<ul>';
      data.log.slice().reverse().forEach(e => {
        html += `<li><b>${e.timestamp}</b> [${e.creative_id}]: ${e.reason}</li>`;
      });
      html += '</ul>';
      $('#syncshield-log').html(html);
    });
});
$('#download-syncshield-log-json-btn').on('click', function() {
  window.open('/syncshield/log/download/json', '_blank');
});
$('#download-syncshield-log-xlsx-btn').on('click', function() {
  window.open('/syncshield/log/download/xlsx', '_blank');
});
$('#granular-filter-syncshield-btn').on('click', function() {
  const creativeId = $('#filter-syncshield-id').val();
  const reason = $('#filter-syncshield-reason').val();
  const start = $('#filter-syncshield-start').val();
  const end = $('#filter-syncshield-end').val();
  const platform = $('#filter-syncshield-platform').val();
  const user = $('#filter-syncshield-user').val();
  const severity = $('#filter-syncshield-severity').val();
  fetch('/syncshield/log/filter/granular', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({creative_id: creativeId, reason, start, end, platform, user, severity})
  })
    .then(r => r.json())
    .then(data => {
      let html = '<ul>';
      data.log.slice().reverse().forEach(e => {
        html += `<li><b>${e.timestamp}</b> [${e.creative_id}] (${e.platform || ''}, ${e.user || ''}, ${e.severity || ''}): ${e.reason}</li>`;
      });
      html += '</ul>';
      $('#syncshield-log').html(html);
    });
});
$('#update-log-retention-btn').on('click', function() {
  const days = parseInt($('#log-retention-days').val(), 10);
  const maxEntries = parseInt($('#log-retention-max').val(), 10);
  fetch('/syncshield/log/retention', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({days, max_entries: maxEntries})
  })
    .then(r => r.json())
    .then(data => {
      showModal(`<b>Retention updated:</b> ${data.days} days, ${data.max_entries} entries`);
    });
});
$('#download-syncshield-log-pdf-btn').on('click', function() {
  window.open('/syncshield/log/download/pdf', '_blank');
});
$('#set-syncshield-api-push-btn').on('click', function() {
  const url = $('#syncshield-api-push-url').val();
  fetch('/syncshield/log/push', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url})
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        showModal(`<b>API push URL set:</b> ${data.url}`);
      } else {
        showModal(`<b>Error:</b> ${data.error}`);
      }
    });
});

// Demo buttons
$('#trigger-retraining-demo-btn').on('click', function() {
  fetch('/demo/trigger_retraining', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({model: 'dRNN', reason: 'Manual dashboard demo'})
  })
    .then(r => r.json())
    .then(data => {
      showModal(`<b>Retraining triggered:</b> ${data.model} (${data.reason})`);
    });
});
$('#log-event-demo-btn').on('click', function() {
  fetch('/demo/log_event', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({agent: 'DemoAgent', event_type: 'DemoEvent', payload: '{"msg": "Demo event from dashboard"}'})
  })
    .then(r => r.json())
    .then(data => {
      showModal(`<b>Demo event logged!</b>`);
    });
});
$('#observability-demo-btn').on('click', function() {
  fetch('/demo/observability', {method: 'POST'})
    .then(r => r.json())
    .then(data => {
      showModal(`<b>Observability trace sent!</b>`);
    });
});

console.log('✅ Dashboard client loaded');
