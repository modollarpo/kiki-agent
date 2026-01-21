# Example: SyncValue agent integration
from core.mediator import SyncHub
import threading
import time

hub = SyncHub()

def monitor_ltv_accuracy():
    while True:
        # Simulate LTV accuracy check
        ltv_accuracy = 0.45  # Replace with real metric
        if ltv_accuracy < 0.5:
            hub.log_event('SyncValue', 'LTVDrop', f'{{"ltv_accuracy": {ltv_accuracy}}}')
            hub.send_signal('SyncValue', 'SyncCreate', 'HighPriority', '{"action": "retrain"}')
            hub.trigger_retraining('dRNN', 'LTV accuracy dropped below 0.5')
        time.sleep(3600)  # Check every hour

# Run in background
t = threading.Thread(target=monitor_ltv_accuracy, daemon=True)
t.start()

# Example: SyncCreate agent integration
from core.mediator import SyncHub
import time

hub = SyncHub()

def listen_for_signals():
    while True:
        # Poll for signals
        with hub.lock, hub._init_db(), sqlite3.connect(hub.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM signals WHERE target_agent = ? AND signal_type = ? ORDER BY id DESC LIMIT 1', ('SyncCreate', 'HighPriority'))
            row = c.fetchone()
            if row:
                # Take action (e.g., retrain model)
                print(f"[SyncCreate] Received signal: {row}")
                # Mark signal as processed or delete if needed
        time.sleep(10)

t2 = threading.Thread(target=listen_for_signals, daemon=True)
t2.start()

# Example: Async/Cloud extension (using Celery)
# In your Celery worker:
# from core.mediator import SyncHub
# hub = SyncHub()
# @celery.task
def retrain_model_task(model_name, reason):
    # ... retrain logic ...
    hub.complete_retraining(retrain_id)
    hub.log_event('SyncCreate', 'RetrainingComplete', f'{model_name} retrained for {reason}')

# Example: Feedback loop (revenue outcome updates confidence)
def update_confidence_from_revenue(creative_id, revenue):
    # ... update logic ...
    hub.log_event('SyncValue', 'ConfidenceUpdate', f'{{"creative_id": "{creative_id}", "revenue": {revenue}}}')

# Example: Cloud integration (push to external API)
import requests
def push_event_to_cloud(event):
    url = 'https://your-cloud-endpoint/api/events'
    try:
        requests.post(url, json=event, timeout=2)
    except Exception:
        pass

# Call push_event_to_cloud(event) after hub.log_event(...)
