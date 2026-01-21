import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
import requests
import re

# Page Configuration for an Enterprise Look
st.set_page_config(page_title="KIKI Command Center - SyncBrain™", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for the "Cyberpunk/Fintech" Aesthetic
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Health check function
def check_health(url):
    try:
        start = time.time()
        resp = requests.get(url, timeout=2)
        elapsed = time.time() - start
        return resp.status_code == 200, elapsed
    except:
        return False, 0

# Prometheus metrics fetcher
@st.cache_data(ttl=5)
def fetch_prometheus_metrics():
    """Fetch metrics from Prometheus exporter"""
    try:
        response = requests.get("http://localhost:9090/metrics", timeout=3)
        if response.status_code == 200:
            metrics = {}
            for line in response.text.split('\n'):
                if line and not line.startswith('#'):
                    try:
                        parts = line.split(' ')
                        if len(parts) >= 2:
                            metric_name = parts[0]
                            metric_value = float(parts[-1])
                            if metric_name not in metrics:
                                metrics[metric_name] = metric_value
                    except:
                        pass
            return metrics
        return {}
    except:
        return {}

# Path to audit log
audit_log_path = "../../audit_log.csv"

# Sidebar for controls
st.sidebar.header("Dashboard Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 1, 10, 2)

# Simulation Control
st.sidebar.header("Simulation Control")
if st.sidebar.button("Simulate High-Value Customer"):
    # Simulate a high-value customer decision
    import csv
    with open(audit_log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), "simulated_cust", 150.0, 15.0, "Placed"])
    st.sidebar.success("Simulated high-value bid placed!")

# Main content
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("System Status", "🟢 Online", "All systems operational")

with col2:
    st.metric("Active Agents", "2/2", "SyncFlow & SyncValue")

with col3:
    st.metric("Uptime", "00:15:30", "+2s")

with col4:
    st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))

st.header("🔍 System Health & Performance")

health_col1, health_col2, health_col3 = st.columns(3)

with health_col1:
    syncvalue_ok, syncvalue_time = check_health("http://localhost:50051/health")
    syncvalue_status = "🟢 Online" if syncvalue_ok else "🔴 Offline"
    st.metric("SyncValue (AI)", syncvalue_status, f"{syncvalue_time:.2f}s" if syncvalue_ok else "N/A")

with health_col2:
    syncshield_ok, syncshield_time = check_health("http://localhost:8081/check")
    syncshield_status = "🟢 Online" if syncshield_ok else "🔴 Offline"
    st.metric("SyncShield (Compliance)", syncshield_status, f"{syncshield_time:.2f}s" if syncshield_ok else "N/A")

with health_col3:
    syncflow_ok, syncflow_time = check_health("http://localhost:8082/health")
    syncflow_status = "🟢 Online" if syncflow_ok else "🔴 Offline"
    st.metric("SyncFlow (Bidding)", syncflow_status, f"{syncflow_time:.2f}s" if syncflow_ok else "N/A")

# Prometheus Metrics Section
st.header("📊 Prometheus Metrics")

prom_metrics = fetch_prometheus_metrics()

if prom_metrics:
    prom_col1, prom_col2, prom_col3, prom_col4 = st.columns(4)
    
    # Extract key metrics
    with prom_col1:
        # LTV metrics
        ltv_predictions = prom_metrics.get('ltv_predictions_total', 0)
        st.metric("LTV Predictions", int(ltv_predictions), "📈")
    
    with prom_col2:
        # Integration health
        integration_health = prom_metrics.get('integration_health_status', 1)
        health_pct = int(integration_health * 100)
        st.metric("Integration Health", f"{health_pct}%", "🔗")
    
    with prom_col3:
        # Active customers
        active_cust = prom_metrics.get('active_customers', 0)
        st.metric("Active Customers", int(active_cust), "👥")
    
    with prom_col4:
        # Total revenue
        revenue = prom_metrics.get('total_revenue_micros', 0) / 1_000_000
        st.metric("Revenue", f"${revenue:.2f}k", "💰")
    
    # Detailed metrics display
    with st.expander("View All Prometheus Metrics"):
        metrics_df = pd.DataFrame([
            {"Metric": k, "Value": v} 
            for k, v in sorted(prom_metrics.items())
        ])
        st.dataframe(metrics_df, use_container_width=True)
else:
    st.warning("⚠️ Prometheus metrics not available. Ensure prometheus_exporter.py is running on :9090")

st.header("📊 Live Decision Stream")

# Initialize session state for data
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

current_time = datetime.now()
if os.path.exists(audit_log_path):
    try:
        df = pd.read_csv(audit_log_path, names=["Timestamp", "CustomerID", "PredictedLTV", "BidAmount", "Decision", "Mode"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        
        # Filter last 24 hours
        cutoff = current_time - timedelta(hours=24)
        df = df[df["Timestamp"] > cutoff]
        
        if not df.empty:
            # Metrics
            total_bids = len(df[df["Decision"] == "Placed"])
            high_value = len(df[df["PredictedLTV"] > 100])
            total_spend = df[df["Decision"] == "Placed"]["BidAmount"].sum()
            avg_ltv = df["PredictedLTV"].mean()
            
            # Update metrics
            col1.metric("Total Bids Placed", f"{total_bids}")
            col2.metric("High-Value Customers", f"{high_value}")
            col3.metric("Total Spend", f"${total_spend:.2f}")
            col4.metric("Avg LTV", f"${avg_ltv:.2f}")
            
            # Recent decisions
            st.subheader("Recent Decisions")
            recent_df = df.tail(5)[["Timestamp", "CustomerID", "PredictedLTV", "Decision", "Mode"]]
            recent_df["Timestamp"] = recent_df["Timestamp"].dt.strftime("%H:%M:%S")
            st.dataframe(recent_df, use_container_width=True)
            
            # Charts
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("LTV Distribution")
                st.bar_chart(df["PredictedLTV"])
            
            with col_chart2:
                st.subheader("Decision Timeline")
                timeline_df = df.groupby(df["Timestamp"].dt.hour)["Decision"].value_counts().unstack().fillna(0)
                st.line_chart(timeline_df)
            
            # Budget monitoring
            st.subheader("Budget Monitoring")
            budget_limit = 500.0
            current_spend = total_spend
            progress = min(current_spend / budget_limit, 1.0)
            
            if progress > 0.8:
                st.error(f"⚠️ Budget Alert: ${current_spend:.2f} / ${budget_limit:.2f}")
            elif progress > 0.6:
                st.warning(f"Budget Warning: ${current_spend:.2f} / ${budget_limit:.2f}")
            else:
                st.success(f"Budget OK: ${current_spend:.2f} / ${budget_limit:.2f}")
            
            st.progress(progress)
            
            # Financial Impact Chart
            st.subheader("💰 Financial Impact: LTV Captured vs Ad Spend")
            captured_ltv = df[df["Decision"] == "Placed"]["PredictedLTV"].sum()
            ad_spend = total_spend
            
            # Enhanced chart with more details
            impact_data = {
                "LTV Captured": captured_ltv,
                "Ad Spend": ad_spend,
                "Net Profit": captured_ltv - ad_spend
            }
            
            impact_df = pd.DataFrame(list(impact_data.items()), columns=["Metric", "Amount"])
            st.bar_chart(impact_df.set_index("Metric"), height=300)
            
            # ROI and efficiency metrics
            roi = (captured_ltv - ad_spend) / ad_spend * 100 if ad_spend > 0 else 0
            efficiency = captured_ltv / ad_spend if ad_spend > 0 else 0
            
            roi_col, profit_col, efficiency_col = st.columns(3)
            with roi_col:
                st.metric("ROI", f"{roi:.1f}%", delta=f"${captured_ltv - ad_spend:.2f} profit")
            with profit_col:
                st.metric("Net Profit", f"${captured_ltv - ad_spend:.2f}")
            with efficiency_col:
                st.metric("LTV/Spend Ratio", f"{efficiency:.2f}x")
            
            # System Alerts
            st.subheader("🚨 System Alerts")
            alerts = []
            if not syncvalue_ok:
                alerts.append("⚠️ AI Prediction Service Offline")
            if not syncshield_ok:
                alerts.append("⚠️ Compliance Service Offline") 
            if not syncflow_ok:
                alerts.append("⚠️ Bidding Agent Offline")
            if progress > 0.9:
                alerts.append("🚨 Budget Critical: Over 90% spent")
            if roi < 0:
                alerts.append("📉 Negative ROI Detected")
            
            if alerts:
                for alert in alerts:
                    st.error(alert)
            else:
                st.success("✅ All Systems Operational - No Alerts")
            
            # Performance Summary
            st.subheader("📈 Performance Summary")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.metric("Decisions/Min", f"{len(df[df['Timestamp'] > current_time - timedelta(minutes=1)]):.1f}")
            with summary_col2:
                st.metric("Avg Response Time", f"{(syncvalue_time + syncshield_time + syncflow_time)/3:.2f}s")
            with summary_col3:
                st.metric("Uptime", "99.9%")  # Mock
            
            # Raw data
            with st.expander("View Raw Audit Data"):
                st.dataframe(df, use_container_width=True)
                
        else:
            st.info("Waiting for decision data...")
            
    except Exception as e:
        st.error(f"Error reading audit log: {e}")
else:
    st.warning("Audit log not found. Start the SyncFlow agent to generate data.")

st.session_state.last_update = current_time

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("**KIKI Agent™ v1.0** | Autonomous Advertising Optimization | Built for Activate Studio Demo")
st.markdown("*Real-time LTV optimization with AI-driven bidding decisions*")