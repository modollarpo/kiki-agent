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

console.log('✅ Dashboard client loaded');
