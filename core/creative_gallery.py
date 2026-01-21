# --- SyncMemory: Agent creative suggestion logic ---
from threading import Lock
_style_suggestion_lock = Lock()
_style_suggestion_idx = 0

def get_next_best_style():
    """Rotate through top 3 styles for agent suggestion."""
    global _style_suggestion_idx
    top_styles = get_last_week_top_styles(limit=3)
    if not top_styles:
        return 'default'
    with _style_suggestion_lock:
        style = top_styles[_style_suggestion_idx % len(top_styles)]['style']
        _style_suggestion_idx += 1
    return style

# Endpoint for agent to fetch next best style
@creative_gallery_bp.route('/creative-gallery/memory/next-style', methods=['GET'])
def get_memory_next_style():
    style = get_next_best_style()
    return jsonify({'next_style': style})
from flask import Blueprint, jsonify, request, render_template
import os
import json
from urllib.request import urlretrieve
from creatives.video_engine import SyncCreateVideo
from ai_models.synccreate_video import create_tiktok_video
from ai_models.ltv_pb2 import LTVRequest
from ai_models.ltv_pb2_grpc import LTVServiceStub
import grpc
from datetime import datetime
import csv
from threading import Timer
import requests
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlencode
from collections import Counter
from glob import glob
from flask_socketio import SocketIO, emit
import time

# Import SyncMemory
from core.syncmemory import log_creative_performance, get_last_week_top_styles

creative_gallery_bp = Blueprint('creative_gallery', __name__)

# Initialize SocketIO (ensure this is only done once in your app)
socketio = SocketIO(app, cors_allowed_origins="*")

def log_to_shield(message, status="INFO"):
    """Helper to stream logs to the dashboard UI"""
    timestamp = time.strftime("%H:%M:%S")
    socketio.emit('new_log', {
        'msg': f"[{timestamp}] {status}: {message}",
        'type': status
    })

# Example: Scan output/videos for MP4s and pair with LTV (stub/demo)
def get_gallery_items():
    video_dir = 'output/videos'
    items = []
    if not os.path.exists(video_dir):
        return items
    for fname in os.listdir(video_dir):
        if fname.endswith('.mp4'):
            # Predict LTV using gRPC AI model
            ltv = 0
            try:
                channel = grpc.insecure_channel('127.0.0.1:50051')
                stub = LTVServiceStub(channel)
                # Example: Use product_id from filename if available
                product_id = fname.split('_')[-1].replace('.mp4','')
                req = LTVRequest(recent_spend=100, engagement_score=0.7)  # Replace with real data
                resp = stub.PredictLTV(req)
                ltv = resp.predicted_ltv
            except Exception as e:
                ltv = 100 + hash(fname) % 100
            items.append({
                'video_url': f'/static/videos/{fname}',
                'ltv': ltv,
                'title': fname
            })
    return items

@creative_gallery_bp.route('/creative-gallery', methods=['GET'])
def get_creative_gallery():
    return jsonify(get_gallery_items())

# In-memory store for approvals (replace with DB in production)
pending_approvals = []
approved_creatives = set()

# In-memory approval history (replace with DB in production)
approval_history = []

# Notification stub (replace with email/SMS/Slack integration)
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_TO = os.environ.get('EMAIL_TO')

# SMS notification (Twilio example)
TWILIO_SID = os.environ.get('TWILIO_SID')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN')
TWILIO_FROM = os.environ.get('TWILIO_FROM')
TWILIO_TO = os.environ.get('TWILIO_TO')

# Email notification

def send_email_notification(subject, body):
    if not (EMAIL_HOST and EMAIL_USER and EMAIL_PASS and EMAIL_TO):
        return
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, [EMAIL_TO], msg.as_string())
    except Exception as e:
        print(f"[NOTIFY ERROR] Email: {e}")

def send_sms_notification(body):
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and TWILIO_TO):
        return
    try:
        url = f'https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json'
        data = urlencode({'From': TWILIO_FROM, 'To': TWILIO_TO, 'Body': body})
        resp = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_TOKEN))
        if resp.status_code >= 400:
            print(f"[NOTIFY ERROR] SMS: {resp.text}")
    except Exception as e:
        print(f"[NOTIFY ERROR] SMS: {e}")

# Webhook notification (generic)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

def send_webhook_notification(payload):
    if not WEBHOOK_URL:
        return
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"[NOTIFY ERROR] Webhook: {e}")

# Update send_notification to use all channels

def send_notification(message):
    print(f"[NOTIFY] {message}")
    if SLACK_WEBHOOK_URL:
        try:
            requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        except Exception as e:
            print(f"[NOTIFY ERROR] Slack: {e}")
    send_email_notification("KIKI Creative Notification", message)
    send_sms_notification(message)
    send_webhook_notification({"event": "creative_notification", "message": message})

@creative_gallery_bp.route('/creative-gallery/submit-for-approval', methods=['POST'])
def submit_for_approval():
    data = request.get_json()
    creative_id = data.get('creative_id')
    video_url = data.get('video_url')
    pending_approvals.append({'creative_id': creative_id, 'video_url': video_url})
    return jsonify({'success': True, 'message': 'Creative submitted for admin approval.'})

@creative_gallery_bp.route('/creative-gallery/pending-approvals', methods=['GET'])
def get_pending_approvals():
    return jsonify(pending_approvals)

@creative_gallery_bp.route('/creative-gallery/approve', methods=['POST'])
def approve_creative():
    data = request.get_json()
    creative_id = data.get('creative_id')
    approved_creatives.add(creative_id)
    global pending_approvals
    pending_approvals = [c for c in pending_approvals if c['creative_id'] != creative_id]
    approval_history.append({'creative_id': creative_id, 'timestamp': datetime.utcnow().isoformat()})
    # --- SyncMemory: Log creative performance ---
    # For demo, extract style and revenue from creative_id or stub
    style = creative_id.split('_')[1] if '_' in creative_id else 'default'
    revenue = 100 + hash(creative_id) % 500  # Stub: random revenue
    log_creative_performance(creative_id, style, revenue, approved_at=datetime.utcnow().isoformat())
    send_notification(f"Creative {creative_id} approved.")
    return jsonify({'success': True, 'message': 'Creative approved.'})
# Endpoint: Get last week's top creative styles (SyncMemory)
@creative_gallery_bp.route('/creative-gallery/memory/top-styles', methods=['GET'])
def get_memory_top_styles():
    limit = int(request.args.get('limit', 5))
    top_styles = get_last_week_top_styles(limit=limit)
    return jsonify({'top_styles': top_styles})

@creative_gallery_bp.route('/creative-gallery/export', methods=['GET'])
def export_creatives_csv():
    video_dir = 'output/videos'
    rows = []
    for fname in os.listdir(video_dir) if os.path.exists(video_dir) else []:
        if fname.endswith('.mp4'):
            rows.append({'creative_id': fname, 'approved': fname in approved_creatives})
    csv_path = 'output/creative_export.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['creative_id', 'approved'])
        writer.writeheader()
        writer.writerows(rows)
    return jsonify({'success': True, 'csv': csv_path})

@creative_gallery_bp.route('/creative-gallery/analytics', methods=['GET'])
def creative_analytics():
    # Example: Return count of approved, pending, and total creatives
    video_dir = 'output/videos'
    total = len([f for f in os.listdir(video_dir) if f.endswith('.mp4')]) if os.path.exists(video_dir) else 0
    return jsonify({
        'total_creatives': total,
        'pending_approval': len(pending_approvals),
        'approved': len(approved_creatives)
    })

@creative_gallery_bp.route('/creative-gallery/analytics/advanced', methods=['GET'])
def advanced_analytics():
    # Example: Approval rate, average approval time, total generated, etc.
    video_dir = 'output/videos'
    total = len([f for f in os.listdir(video_dir) if f.endswith('.mp4')]) if os.path.exists(video_dir) else 0
    approved = len(approved_creatives)
    pending = len(pending_approvals)
    approval_rate = approved / total if total else 0
    # Average approval time (stub: not tracked per creative)
    avg_approval_time = 'N/A'
    return jsonify({
        'total_creatives': total,
        'approved': approved,
        'pending': pending,
        'approval_rate': approval_rate,
        'avg_approval_time': avg_approval_time,
        'approval_history': approval_history
    })

@creative_gallery_bp.route('/creative-gallery/analytics/history', methods=['GET'])
def analytics_history():
    # Trend: count approvals per day
    dates = [h['timestamp'][:10] for h in approval_history]
    counter = Counter(dates)
    history = [{'date': d, 'count': counter[d]} for d in sorted(counter)]
    return jsonify(history)

# Predictive analytics: forecast approvals for next 7 days (simple linear projection)
@creative_gallery_bp.route('/creative-gallery/analytics/forecast', methods=['GET'])
def analytics_forecast():
    from datetime import datetime, timedelta
    # Use approval_history for trend
    dates = [h['timestamp'][:10] for h in approval_history]
    if not dates:
        return jsonify({'forecast': []})
    counter = Counter(dates)
    sorted_dates = sorted(counter)
    counts = [counter[d] for d in sorted_dates]
    # Simple linear forecast
    if len(counts) < 2:
        forecast = [counts[-1]] * 7
    else:
        slope = (counts[-1] - counts[0]) / max(1, len(counts) - 1)
        forecast = [max(0, int(counts[-1] + slope * (i+1))) for i in range(7)]
    forecast_dates = [(datetime.strptime(sorted_dates[-1], '%Y-%m-%d') + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]
    return jsonify({'forecast': list(zip(forecast_dates, forecast))})

# Predictive model: moving average forecast for approvals
@creative_gallery_bp.route('/creative-gallery/analytics/forecast/moving-average', methods=['GET'])
def analytics_moving_average():
    from datetime import datetime, timedelta
    window = 3
    dates = [h['timestamp'][:10] for h in approval_history]
    if not dates:
        return jsonify({'forecast': []})
    counter = Counter(dates)
    sorted_dates = sorted(counter)
    counts = [counter[d] for d in sorted_dates]
    ma_forecast = []
    for i in range(len(counts), len(counts)+7):
        if i < window:
            ma = counts[-1]
        else:
            ma = int(sum(counts[max(0,i-window):i]) / window)
        ma_forecast.append(ma)
    forecast_dates = [(datetime.strptime(sorted_dates[-1], '%Y-%m-%d') + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]
    return jsonify({'forecast': list(zip(forecast_dates, ma_forecast))})

# Predictive model: exponential smoothing forecast for approvals
@creative_gallery_bp.route('/creative-gallery/analytics/forecast/exponential', methods=['GET'])
def analytics_exponential_smoothing():
    from datetime import datetime, timedelta
    alpha = 0.5
    dates = [h['timestamp'][:10] for h in approval_history]
    if not dates:
        return jsonify({'forecast': []})
    counter = Counter(dates)
    sorted_dates = sorted(counter)
    counts = [counter[d] for d in sorted_dates]
    if not counts:
        return jsonify({'forecast': []})
    s = counts[0]
    forecast = []
    for _ in range(7):
        s = alpha * counts[-1] + (1 - alpha) * s
        forecast.append(int(s))
    forecast_dates = [(datetime.strptime(sorted_dates[-1], '%Y-%m-%d') + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]
    return jsonify({'forecast': list(zip(forecast_dates, forecast))})

# Custom escalation: notify if no approvals in last 48h
NO_APPROVALS_HOURS = 48

def check_no_approvals():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    recent = [h for h in approval_history if (now - datetime.fromisoformat(h['timestamp'])).total_seconds() < NO_APPROVALS_HOURS*3600]
    if not recent:
        send_notification(f"Escalation: No creative approvals in the last {NO_APPROVALS_HOURS} hours!")
    Timer(3600, check_no_approvals).start()

check_no_approvals()

# Custom workflow rule: auto-escalate if >3 high-LTV creatives pending for >1 hour
HIGH_LTV_PENDING_THRESHOLD = 3
HIGH_LTV_PENDING_MINUTES = 60

def check_high_ltv_pending():
    now = time.time()
    high_ltv_pending = [c for c in pending_approvals if any(item['creative_id'] == c['creative_id'] and item['ltv'] > LTV_PRIORITY_THRESHOLD for item in get_gallery_items())]
    # In production, track submit time for each creative
    if len(high_ltv_pending) > HIGH_LTV_PENDING_THRESHOLD:
        send_notification(f"Escalation: {len(high_ltv_pending)} high-LTV creatives pending for over {HIGH_LTV_PENDING_MINUTES} minutes!")
    Timer(600, check_high_ltv_pending).start()

check_high_ltv_pending()

# Custom automation: auto-notify if approval rate drops below 50%
def monitor_approval_rate():
    try:
        res = len(approved_creatives) / (len(approved_creatives) + len(pending_approvals))
    except ZeroDivisionError:
        res = 1
    if res < 0.5:
        send_notification(f"Alert: Approval rate dropped below 50% ({res*100:.1f}%)!")
    Timer(600, monitor_approval_rate).start()  # Check every 10 minutes

monitor_approval_rate()

# Custom trigger: auto-generate creatives when new product is added (stub)
def on_new_product(product):
    # --- SyncMemory: Rotate top style suggestion ---
    style = product.get('style', get_next_best_style())
    bg_image = product.get('bg_image', 'assets/default_bg.jpg')
    output_dir = 'output/videos'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"creative_{product.get('id', 'demo')}.mp4")
    # Attach style to product for video engine and memory
    product['style'] = style
    from creatives.video_engine import SyncCreateVideo
    engine = SyncCreateVideo(bg_image, product)
    engine.make_video(output_path)
    creative_id = f"creative_{product.get('id', 'demo')}"
    pending_approvals.append({'creative_id': creative_id, 'video_url': f'/static/videos/{creative_id}.mp4', 'style': style})
    send_notification(f"Auto-generated creative for new product: {creative_id} (style: {style})")
    schedule_auto_approval(creative_id)

# Example endpoint to simulate new product event
@creative_gallery_bp.route('/creative-gallery/simulate-new-product', methods=['POST'])
def simulate_new_product():
    product = request.get_json()
    on_new_product(product)
    return jsonify({'success': True, 'message': 'Creative auto-generated for new product.'})

# More analytics: top creatives by approval speed, most active admin, etc.
@creative_gallery_bp.route('/creative-gallery/analytics/insights', methods=['GET'])
def analytics_insights():
    # Approval speed (stub: all approvals have timestamp, but no submit time)
    # In production, track submit time for each creative
    approval_times = []
    for h in approval_history:
        if 'auto' not in h:
            approval_times.append(0)  # Placeholder for real timing
    avg_approval_speed = sum(approval_times) / len(approval_times) if approval_times else 0
    # Most active admin (stub: not tracked)
    most_active_admin = 'N/A'
    return jsonify({
        'avg_approval_speed': avg_approval_speed,
        'most_active_admin': most_active_admin,
        'total_approvals': len(approval_history)
    })

# Workflow intelligence: escalate if pending > threshold
PENDING_ESCALATION_THRESHOLD = 5

def check_pending_escalation():
    if len(pending_approvals) > PENDING_ESCALATION_THRESHOLD:
        send_notification(f"Escalation: {len(pending_approvals)} creatives pending approval!")
    Timer(60, check_pending_escalation).start()

check_pending_escalation()

# Workflow automation: auto-submit new creatives for approval
AUTO_APPROVE_MINUTES = 10

def schedule_auto_approval(creative_id):
    def auto_approve():
        if creative_id not in approved_creatives:
            approved_creatives.add(creative_id)
            approval_history.append({'creative_id': creative_id, 'timestamp': datetime.utcnow().isoformat(), 'auto': True})
            send_notification(f"Creative {creative_id} auto-approved after {AUTO_APPROVE_MINUTES} minutes.")
    Timer(AUTO_APPROVE_MINUTES * 60, auto_approve).start()

@creative_gallery_bp.route('/creative-gallery/generate', methods=['POST'])
def generate_creative():
    data = request.get_json()
    bg_image = data.get('bg_image')
    product = data.get('product', {})
    # --- SyncMemory: Rotate top style suggestion for agent ---
    style = product.get('style', get_next_best_style())
    product['style'] = style
    output_dir = 'output/videos'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"creative_{product.get('id', 'demo')}.mp4")
    # Download background image if URL
    if bg_image.startswith('http'):
        local_bg = os.path.join('output/temp', os.path.basename(bg_image))
        os.makedirs('output/temp', exist_ok=True)
        urlretrieve(bg_image, local_bg)
        bg_image = local_bg
    engine = SyncCreateVideo(bg_image, product)
    engine.make_video(output_path)
    # Auto-submit for approval
    creative_id = f"creative_{product.get('id', 'demo')}"
    pending_approvals.append({'creative_id': creative_id, 'video_url': f'/static/videos/{creative_id}.mp4', 'style': style})
    send_notification(f"Creative {creative_id} (style: {style}) submitted for approval.")
    schedule_auto_approval(creative_id)
    return jsonify({'success': True, 'video_url': f'/static/videos/{creative_id}.mp4', 'style': style})

# Further automation: notify on export, auto-export daily
from threading import Timer
import time

def schedule_daily_export():
    def export():
        video_dir = 'output/videos'
        rows = []
        for fname in os.listdir(video_dir) if os.path.exists(video_dir) else []:
            if fname.endswith('.mp4'):
                rows.append({'creative_id': fname, 'approved': fname in approved_creatives})
        csv_path = f'output/creative_export_{int(time.time())}.csv'
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['creative_id', 'approved'])
            writer.writeheader()
            writer.writerows(rows)
        send_notification(f"Daily creative export completed: {csv_path}")
        # Schedule next run in 24h
        Timer(24*60*60, export).start()
    Timer(5, export).start()  # Start after 5s for demo

schedule_daily_export()

# Advanced scheduling: weekly summary export

def schedule_weekly_summary():
    def export():
        video_dir = 'output/videos'
        rows = []
        for fname in os.listdir(video_dir) if os.path.exists(video_dir) else []:
            if fname.endswith('.mp4'):
                rows.append({'creative_id': fname, 'approved': fname in approved_creatives})
        csv_path = f'output/creative_weekly_summary_{int(time.time())}.csv'
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['creative_id', 'approved'])
            writer.writeheader()
            writer.writerows(rows)
        send_notification(f"Weekly creative summary exported: {csv_path}")
        # Schedule next run in 7 days
        Timer(7*24*60*60, export).start()
    Timer(15, export).start()  # Start after 15s for demo

schedule_weekly_summary()

# Further automation: auto-cleanup old creatives (e.g., >30 days)
def schedule_auto_cleanup():
    def cleanup():
        video_dir = 'output/videos'
        now = time.time()
        removed = []
        for fname in os.listdir(video_dir) if os.path.exists(video_dir) else []:
            fpath = os.path.join(video_dir, fname)
            if fname.endswith('.mp4') and os.path.isfile(fpath):
                if now - os.path.getmtime(fpath) > 30*24*60*60:
                    os.remove(fpath)
                    removed.append(fname)
        if removed:
            send_notification(f"Auto-cleanup: Removed old creatives: {', '.join(removed)}")
        Timer(24*60*60, cleanup).start()
    Timer(10, cleanup).start()  # Start after 10s for demo

schedule_auto_cleanup()

# Even more intelligent automation: auto-prioritize creatives with high predicted LTV
LTV_PRIORITY_THRESHOLD = 150

def auto_prioritize_high_ltv():
    for item in get_gallery_items():
        if item['ltv'] > LTV_PRIORITY_THRESHOLD and item['creative_id'] not in approved_creatives:
            send_notification(f"Priority: Creative {item['creative_id']} has high LTV (${item['ltv']}) and needs review.")
    Timer(300, auto_prioritize_high_ltv).start()  # Check every 5 minutes

auto_prioritize_high_ltv()

# Advanced automation: auto-archive creatives with low LTV after 60 days
LTV_ARCHIVE_THRESHOLD = 80
ARCHIVE_DAYS = 60

def schedule_auto_archive():
    def archive():
        video_dir = 'output/videos'
        now = time.time()
        archived = []
        for fname in os.listdir(video_dir) if os.path.exists(video_dir) else []:
            fpath = os.path.join(video_dir, fname)
            if fname.endswith('.mp4') and os.path.isfile(fpath):
                ltv = 0
                for item in get_gallery_items():
                    if item['video_url'].endswith(fname):
                        ltv = item['ltv']
                        break
                if ltv < LTV_ARCHIVE_THRESHOLD and now - os.path.getmtime(fpath) > ARCHIVE_DAYS*24*60*60:
                    os.rename(fpath, fpath + '.archived')
                    archived.append(fname)
        if archived:
            send_notification(f"Auto-archived low-LTV creatives: {', '.join(archived)}")
        Timer(24*60*60, archive).start()
    Timer(20, archive).start()  # Start after 20s for demo

schedule_auto_archive()

# Anomaly detection: flag days with approvals >2 std dev above mean
@creative_gallery_bp.route('/creative-gallery/analytics/anomalies', methods=['GET'])
def analytics_anomalies():
    import numpy as np
    dates = [h['timestamp'][:10] for h in approval_history]
    counter = Counter(dates)
    sorted_dates = sorted(counter)
    counts = np.array([counter[d] for d in sorted_dates])
    if len(counts) < 2:
        return jsonify({'anomalies': []})
    mean = counts.mean()
    std = counts.std()
    anomalies = [d for d, c in zip(sorted_dates, counts) if c > mean + 2*std]
    return jsonify({'anomalies': anomalies})

# Anomaly explanations: return context for each anomaly
@creative_gallery_bp.route('/creative-gallery/analytics/anomaly-explanations', methods=['GET'])
def analytics_anomaly_explanations():
    import numpy as np
    dates = [h['timestamp'][:10] for h in approval_history]
    counter = Counter(dates)
    sorted_dates = sorted(counter)
    counts = np.array([counter[d] for d in sorted_dates])
    if len(counts) < 2:
        return jsonify({'explanations': {}})
    mean = counts.mean()
    std = counts.std()
    explanations = {}
    for d, c in zip(sorted_dates, counts):
        if c > mean + 2*std:
            # Example: find top creative(s) approved that day
            top_creatives = [h['creative_id'] for h in approval_history if h['timestamp'].startswith(d)]
            explanations[d] = {
                'count': int(c),
                'mean': float(mean),
                'std': float(std),
                'top_creatives': top_creatives,
                'note': f"Spike likely due to {', '.join(top_creatives[:2])}"
            }
    return jsonify({'explanations': explanations})

# Custom escalation: notify admin group if >2 anomalies in 7 days
ANOMALY_GROUP_ESCALATION_THRESHOLD = 2

def check_anomaly_group_escalation():
    import numpy as np
    from datetime import datetime, timedelta
    dates = [h['timestamp'][:10] for h in approval_history]
    counter = Counter(dates)
    sorted_dates = sorted(counter)
    counts = np.array([counter[d] for d in sorted_dates])
    if len(counts) < 2:
        return
    mean = counts.mean()
    std = counts.std()
    recent = sorted_dates[-7:]
    anomaly_count = sum(1 for d, c in zip(sorted_dates, counts) if d in recent and c > mean + 2*std)
    if anomaly_count > ANOMALY_GROUP_ESCALATION_THRESHOLD:
        send_notification(f"Escalation: {anomaly_count} anomalies detected in last 7 days!")
    Timer(3600, check_anomaly_group_escalation).start()

check_anomaly_group_escalation()

# Anomaly root-cause analysis: correlate with campaign/product events
@creative_gallery_bp.route('/creative-gallery/analytics/anomaly-root-cause', methods=['GET'])
def analytics_anomaly_root_cause():
    # Example: correlate anomaly days with new product/campaign events (stub)
    # In production, pull from real event logs
    import numpy as np
    dates = [h['timestamp'][:10] for h in approval_history]
    counter = Counter(dates)
    sorted_dates = sorted(counter)
    counts = np.array([counter[d] for d in sorted_dates])
    mean = counts.mean() if len(counts) else 0
    std = counts.std() if len(counts) else 0
    anomalies = [d for d, c in zip(sorted_dates, counts) if c > mean + 2*std]
    # Simulate event log
    event_log = {
        d: [f"Campaign launch: {d}", f"New product: SKU{d[-2:]}" if int(d[-2:]) % 2 == 0 else None]
        for d in anomalies
    }
    root_causes = {d: [e for e in event_log[d] if e] for d in anomalies}
    return jsonify({'root_causes': root_causes})

# Admin workflow actions: approve, reject, escalate with reason
@creative_gallery_bp.route('/creative-gallery/reject', methods=['POST'])
def reject_creative():
    data = request.get_json()
    creative_id = data.get('creative_id')
    reason = data.get('reason', 'No reason provided')
    global pending_approvals
    pending_approvals = [c for c in pending_approvals if c['creative_id'] != creative_id]
    approval_history.append({'creative_id': creative_id, 'timestamp': datetime.utcnow().isoformat(), 'rejected': True, 'reason': reason})
    send_notification(f"Creative {creative_id} rejected. Reason: {reason}")
    return jsonify({'success': True, 'message': 'Creative rejected.'})

@creative_gallery_bp.route('/creative-gallery/escalate', methods=['POST'])
def escalate_creative():
    data = request.get_json()
    creative_id = data.get('creative_id')
    reason = data.get('reason', 'No reason provided')
    send_notification(f"Creative {creative_id} escalated for admin review. Reason: {reason}")
    return jsonify({'success': True, 'message': 'Creative escalated.'})

# Deeper analytics: creative performance by campaign/product (stub)
@creative_gallery_bp.route('/creative-gallery/analytics/performance', methods=['GET'])
def analytics_performance():
    # In production, pull real campaign/product mapping and performance
    performance = {}
    for h in approval_history:
        key = h.get('creative_id', 'unknown').split('_')[1] if 'creative_id' in h else 'unknown'
        if key not in performance:
            performance[key] = {'approved': 0, 'rejected': 0}
        if h.get('rejected'):
            performance[key]['rejected'] += 1
        else:
            performance[key]['approved'] += 1
    return jsonify({'performance': performance})

# Custom admin dashboard: summary endpoint
@creative_gallery_bp.route('/creative-gallery/admin-summary', methods=['GET'])
def admin_summary():
    return jsonify({
        'total_creatives': len([f for f in os.listdir('output/videos') if f.endswith('.mp4')]) if os.path.exists('output/videos') else 0,
        'pending': len(pending_approvals),
        'approved': len(approved_creatives),
        'rejected': sum(1 for h in approval_history if h.get('rejected')),
        'escalated': sum(1 for h in approval_history if h.get('escalated')),
        'anomalies': len([h for h in approval_history if 'anomaly' in h]),
        'last_approval': approval_history[-1]['timestamp'] if approval_history else None
    })

# Workflow automation: auto-escalate rejected creatives for review after 24h
REJECTED_ESCALATION_HOURS = 24

def schedule_rejected_escalation():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    for h in approval_history:
        if h.get('rejected') and not h.get('escalated'):
            t = datetime.fromisoformat(h['timestamp'])
            if (now - t).total_seconds() > REJECTED_ESCALATION_HOURS*3600:
                h['escalated'] = True
                send_notification(f"Escalation: Rejected creative {h['creative_id']} needs admin review.")
    Timer(3600, schedule_rejected_escalation).start()

schedule_rejected_escalation()

# Drill-down: get all creatives for a campaign/product
@creative_gallery_bp.route('/creative-gallery/analytics/drilldown/<key>', methods=['GET'])
def analytics_drilldown(key):
    # In production, map key to campaign/product
    creatives = [h for h in approval_history if key in h.get('creative_id', '')]
    return jsonify({'creatives': creatives})

# Granular drill-down: get all actions for a specific creative
@creative_gallery_bp.route('/creative-gallery/analytics/drilldown/creative/<creative_id>', methods=['GET'])
def analytics_drilldown_creative(creative_id):
    actions = [h for h in approval_history if h.get('creative_id') == creative_id]
    return jsonify({'actions': actions})

# Custom export: JSON and Excel formats
@creative_gallery_bp.route('/creative-gallery/analytics/export/json', methods=['GET'])
def export_analytics_json():
    import json
    json_path = 'output/analytics_export.json'
    with open(json_path, 'w') as f:
        json.dump(approval_history, f, indent=2)
    return jsonify({'success': True, 'json': json_path})

@creative_gallery_bp.route('/creative-gallery/analytics/export/xlsx', methods=['GET'])
def export_analytics_xlsx():
    import xlsxwriter
    xlsx_path = 'output/analytics_export.xlsx'
    workbook = xlsxwriter.Workbook(xlsx_path)
    worksheet = workbook.add_worksheet()
    fieldnames = set()
    for h in approval_history:
        fieldnames.update(h.keys())
    fieldnames = list(fieldnames)
    for col, name in enumerate(fieldnames):
        worksheet.write(0, col, name)
    for row, h in enumerate(approval_history, 1):
        for col, name in enumerate(fieldnames):
            worksheet.write(row, col, h.get(name, ''))
    workbook.close()
    return jsonify({'success': True, 'xlsx': xlsx_path})

# Additional export formats: XML and TXT

def export_syncshield_log_xml():
    from xml.etree.ElementTree import Element, SubElement, tostring
    root = Element('SyncShieldLog')
    for e in syncshield_log:
        entry = SubElement(root, 'Event')
        for k, v in e.items():
            SubElement(entry, k).text = str(v)
    xml_str = tostring(root, encoding='utf-8').decode('utf-8')
    xml_path = f'output/syncshield_log_{int(time.time())}.xml'
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    send_notification(f"SyncShield™ log XML exported: {xml_path}")
    return xml_path

def export_syncshield_log_txt():
    txt_path = f'output/syncshield_log_{int(time.time())}.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        for e in syncshield_log:
            line = f"{e.get('timestamp', '')} [{e.get('creative_id', '')}] {e.get('reason', '')}\n"
            f.write(line)
    send_notification(f"SyncShield™ log TXT exported: {txt_path}")
    return txt_path

# Custom scheduling: monthly PDF report
def schedule_monthly_syncshield_pdf_report():
    def export():
        generate_weekly_syncshield_report(custom_title='SyncShield™ Monthly Audit Report')
        Timer(30*24*60*60, export).start()
    Timer(20, export).start()  # Start after 20s for demo

schedule_monthly_syncshield_pdf_report()

# Further reporting automation: send all exports to webhook
def send_export_to_webhook(file_path, export_type):
    if not WEBHOOK_URL:
        return
    try:
        with open(file_path, 'rb') as f:
            requests.post(WEBHOOK_URL, files={'file': (os.path.basename(file_path), f)}, data={'type': export_type})
    except Exception as e:
        print(f"[NOTIFY ERROR] Webhook export: {e}")

# Example: call send_export_to_webhook after each export
def export_and_notify_all_formats():
    pdf_path = generate_weekly_syncshield_report()
    send_export_to_webhook(pdf_path, 'pdf')
    csv_path = f'output/syncshield_log_{int(time.time())}.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        if syncshield_log:
            writer = csv.DictWriter(csvfile, fieldnames=syncshield_log[0].keys())
            writer.writeheader()
            writer.writerows(syncshield_log)
    send_export_to_webhook(csv_path, 'csv')
    xml_path = export_syncshield_log_xml()
    send_export_to_webhook(xml_path, 'xml')
    txt_path = export_syncshield_log_txt()
    send_export_to_webhook(txt_path, 'txt')

# SyncShield™ Log: live unsafe content blocking feed
syncshield_log = []

# Customizable log schema: allow extra fields
SYNC_SHIELD_LOG_FIELDS = ['timestamp', 'creative_id', 'reason', 'platform', 'user', 'severity', 'details']

def log_syncshield_event(event):
    # Accept any extra fields, but only store those in SYNC_SHIELD_LOG_FIELDS
    filtered_event = {k: v for k, v in event.items() if k in SYNC_SHIELD_LOG_FIELDS}
    for field in SYNC_SHIELD_LOG_FIELDS:
        if field not in filtered_event:
            filtered_event[field] = ''
    syncshield_log.append(filtered_event)
    enforce_log_retention()

# API push: POST log events to external endpoint
import requests
SYNC_SHIELD_API_PUSH_URL = None  # Set via endpoint

@creative_gallery_bp.route('/syncshield/log/push', methods=['POST'])
def push_syncshield_log():
    global SYNC_SHIELD_API_PUSH_URL
    data = request.get_json() or {}
    url = data.get('url')
    if url:
        SYNC_SHIELD_API_PUSH_URL = url
        return jsonify({'success': True, 'url': url})
    return jsonify({'success': False, 'error': 'No URL provided'}), 400

def push_log_event_to_api(event):
    if SYNC_SHIELD_API_PUSH_URL:
        try:
            requests.post(SYNC_SHIELD_API_PUSH_URL, json=event, timeout=2)
        except Exception:
            pass

# Call push_log_event_to_api(event) after logging
old_log_syncshield_event = log_syncshield_event
def log_syncshield_event(event):
    old_log_syncshield_event(event)
    push_log_event_to_api(event)

@creative_gallery_bp.route('/syncshield/log', methods=['GET'])
def get_syncshield_log():
    return jsonify({'log': syncshield_log})

# Example: Call this function when unsafe content is blocked
# log_syncshield_event({'timestamp': '2026-01-21T12:00:00Z', 'creative_id': 'abc123', 'reason': 'Brand safety violation'})

@creative_gallery_bp.route('/syncshield/log/test', methods=['POST'])
def trigger_syncshield_test_event():
    from datetime import datetime
    import random
    test_event = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'creative_id': f'test_{random.randint(1000,9999)}',
        'reason': random.choice([
            'Brand safety violation',
            'Copyrighted content',
            'Inappropriate language',
            'Unsafe visual detected',
            'Blocked by custom guardrail'
        ])
    }
    log_syncshield_event(test_event)
    return jsonify({'success': True, 'event': test_event})

from flask import request

@creative_gallery_bp.route('/syncshield/log/filter', methods=['POST'])
def filter_syncshield_log():
    data = request.get_json() or {}
    creative_id = data.get('creative_id')
    reason = data.get('reason')
    filtered = syncshield_log
    if creative_id:
        filtered = [e for e in filtered if creative_id in e['creative_id']]
    if reason:
        filtered = [e for e in filtered if reason.lower() in e['reason'].lower()]
    return jsonify({'log': filtered})

@creative_gallery_bp.route('/syncshield/log/download', methods=['GET'])
def download_syncshield_log():
    import csv
    from io import StringIO
    output = StringIO()
    if syncshield_log:
        writer = csv.DictWriter(output, fieldnames=syncshield_log[0].keys())
        writer.writeheader()
        writer.writerows(syncshield_log)
    return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=syncshield_log.csv'}

@creative_gallery_bp.route('/syncshield/log/filter/advanced', methods=['POST'])
def advanced_filter_syncshield_log():
    data = request.get_json() or {}
    creative_id = data.get('creative_id')
    reason = data.get('reason')
    start = data.get('start')
    end = data.get('end')
    filtered = syncshield_log
    if creative_id:
        filtered = [e for e in filtered if creative_id in e['creative_id']]
    if reason:
        filtered = [e for e in filtered if reason.lower() in e['reason'].lower()]
    if start:
        filtered = [e for e in filtered if e['timestamp'] >= start]
    if end:
        filtered = [e for e in filtered if e['timestamp'] <= end]
    return jsonify({'log': filtered})

@creative_gallery_bp.route('/syncshield/log/filter/granular', methods=['POST'])
def granular_filter_syncshield_log():
    data = request.get_json() or {}
    creative_id = data.get('creative_id')
    reason = data.get('reason')
    start = data.get('start')
    end = data.get('end')
    platform = data.get('platform')
    user = data.get('user')
    severity = data.get('severity')
    filtered = syncshield_log
    if creative_id:
        filtered = [e for e in filtered if creative_id in e.get('creative_id', '')]
    if reason:
        filtered = [e for e in filtered if reason.lower() in e.get('reason', '').lower()]
    if start:
        filtered = [e for e in filtered if e.get('timestamp', '') >= start]
    if end:
        filtered = [e for e in filtered if e.get('timestamp', '') <= end]
    if platform:
        filtered = [e for e in filtered if e.get('platform', '').lower() == platform.lower()]
    if user:
        filtered = [e for e in filtered if e.get('user', '') == user]
    if severity:
        filtered = [e for e in filtered if e.get('severity', '').lower() == severity.lower()]
    return jsonify({'log': filtered})

# Custom retention: configurable days and max entries
LOG_RETENTION_DAYS = 30
LOG_RETENTION_MAX = 500

def set_log_retention(days=None, max_entries=None):
    global LOG_RETENTION_DAYS, LOG_RETENTION_MAX
    if days is not None:
        LOG_RETENTION_DAYS = days
    if max_entries is not None:
        LOG_RETENTION_MAX = max_entries
    enforce_log_retention()

@creative_gallery_bp.route('/syncshield/log/retention', methods=['POST'])
def update_log_retention():
    data = request.get_json() or {}
    days = data.get('days')
    max_entries = data.get('max_entries')
    set_log_retention(days, max_entries)
    return jsonify({'success': True, 'days': LOG_RETENTION_DAYS, 'max_entries': LOG_RETENTION_MAX})

@creative_gallery_bp.route('/syncshield/log/download/pdf', methods=['GET'])
def download_syncshield_log_pdf():
    from fpdf import FPDF
    from flask import Response
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'SyncShield Log', ln=1)
    pdf.set_font('Arial', '', 10)
    for e in syncshield_log:
        line = f"{e.get('timestamp', '')} [{e.get('creative_id', '')}] {e.get('reason', '')}"
        pdf.multi_cell(0, 8, line)
    pdf_output = pdf.output(dest='S').encode('latin1')
    return pdf_output, 200, {'Content-Type': 'application/pdf', 'Content-Disposition': 'attachment; filename=syncshield_log.pdf'}

# Log retention: keep only last N days or M entries
LOG_RETENTION_DAYS = 30
LOG_RETENTION_MAX = 500

def enforce_log_retention():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    cutoff = now - timedelta(days=LOG_RETENTION_DAYS)
    syncshield_log[:] = [e for e in syncshield_log if e.get('timestamp', '') >= cutoff.isoformat()]
    while len(syncshield_log) > LOG_RETENTION_MAX:
        syncshield_log.pop(0)

# Call enforce_log_retention() after each log event
old_log_syncshield_event = log_syncshield_event
def log_syncshield_event(event):
    old_log_syncshield_event(event)
    enforce_log_retention()

@creative_gallery_bp.route('/syncshield/log/download/json', methods=['GET'])
def download_syncshield_log_json():
    from flask import Response
    import json
    return Response(json.dumps(syncshield_log, indent=2), mimetype='application/json', headers={'Content-Disposition': 'attachment; filename=syncshield_log.json'})

@creative_gallery_bp.route('/syncshield/log/download/xlsx', methods=['GET'])
def download_syncshield_log_xlsx():
    import xlsxwriter
    from io import BytesIO
    output = BytesIO()
    if syncshield_log:
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        fieldnames = list(syncshield_log[0].keys())
        for col, name in enumerate(fieldnames):
            worksheet.write(0, col, name)
        for row, e in enumerate(syncshield_log, 1):
            for col, name in enumerate(fieldnames):
                worksheet.write(row, col, e.get(name, ''))
        workbook.close()
        output.seek(0)
        return output.read(), 200, {'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Content-Disposition': 'attachment; filename=syncshield_log.xlsx'}
    return '', 204

# Automated weekly SyncShield™ audit report (PDF) generation and notification
from fpdf import FPDF

def generate_weekly_syncshield_report(custom_title=None, include_details=False, email_to=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    title = custom_title or 'SyncShield™ Weekly Audit Report'
    pdf.cell(0, 10, title, ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}', ln=1)
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Summary', ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f'Total Events: {len(syncshield_log)}', ln=1)
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Recent Events', ln=1)
    pdf.set_font('Arial', '', 9)
    for e in syncshield_log[-50:]:
        line = f"{e.get('timestamp', '')} [{e.get('creative_id', '')}] {e.get('reason', '')}"
        if include_details and e.get('details'):
            line += f" | Details: {e['details']}"
        pdf.multi_cell(0, 6, line)
    pdf_path = f'output/syncshield_audit_{int(time.time())}.pdf'
    pdf.output(pdf_path)
    send_notification(f"Weekly SyncShield™ audit report generated: {pdf_path}")
    if email_to:
        try:
            with open(pdf_path, 'rb') as f:
                msg = MIMEText(f"See attached SyncShield™ audit report.")
                msg['Subject'] = title
                msg['From'] = EMAIL_USER
                msg['To'] = email_to
                from email.mime.application import MIMEApplication
                part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                from email.mime.multipart import MIMEMultipart
                mmsg = MIMEMultipart()
                mmsg.attach(msg)
                mmsg.attach(part)
                with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_USER, EMAIL_PASS)
                    server.sendmail(EMAIL_USER, [email_to], mmsg.as_string())
        except Exception as e:
            print(f"[NOTIFY ERROR] Email PDF: {e}")
    return pdf_path

# Schedule additional automated exports (daily CSV)
def schedule_daily_syncshield_csv_export():
    def export():
        csv_path = f'output/syncshield_log_{int(time.time())}.csv'
        import csv
        with open(csv_path, 'w', newline='') as csvfile:
            if syncshield_log:
                writer = csv.DictWriter(csvfile, fieldnames=syncshield_log[0].keys())
                writer.writeheader()
                writer.writerows(syncshield_log)
        send_notification(f"Daily SyncShield™ log CSV exported: {csv_path}")
        Timer(24*60*60, export).start()
    Timer(10, export).start()  # Start after 10s for demo

schedule_daily_syncshield_csv_export()

# Automated monthly SyncShield™ audit report (PDF) generation and notification
def schedule_monthly_syncshield_pdf_report():
    def export():
        generate_weekly_syncshield_report(custom_title='SyncShield™ Monthly Audit Report')
        Timer(30*24*60*60, export).start()
    Timer(20, export).start()  # Start after 20s for demo

schedule_monthly_syncshield_pdf_report()

# Further reporting automation: send all exports to webhook
def send_export_to_webhook(file_path, export_type):
    if not WEBHOOK_URL:
        return
    try:
        with open(file_path, 'rb') as f:
            requests.post(WEBHOOK_URL, files={'file': (os.path.basename(file_path), f)}, data={'type': export_type})
    except Exception as e:
        print(f"[NOTIFY ERROR] Webhook export: {e}")

# Example: call send_export_to_webhook after each export
def export_and_notify_all_formats():
    pdf_path = generate_weekly_syncshield_report()
    send_export_to_webhook(pdf_path, 'pdf')
    csv_path = f'output/syncshield_log_{int(time.time())}.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        if syncshield_log:
            writer = csv.DictWriter(csvfile, fieldnames=syncshield_log[0].keys())
            writer.writeheader()
            writer.writerows(syncshield_log)
    send_export_to_webhook(csv_path, 'csv')
    xml_path = export_syncshield_log_xml()
    send_export_to_webhook(xml_path, 'xml')
    txt_path = export_syncshield_log_txt()
    send_export_to_webhook(txt_path, 'txt')
