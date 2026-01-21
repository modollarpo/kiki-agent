# Live demo hooks for SyncHub integration
from core.mediator import SyncHub
import time
import threading
import requests

hub = SyncHub()

# Live demo: trigger a retraining event from the dashboard
from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/demo/trigger_retraining', methods=['POST'])
def demo_trigger_retraining():
    model = request.json.get('model', 'dRNN')
    reason = request.json.get('reason', 'Manual demo trigger')
    hub.trigger_retraining(model, reason)
    return jsonify({'success': True, 'model': model, 'reason': reason})

# Live demo: push a custom event to the audit log
@app.route('/demo/log_event', methods=['POST'])
def demo_log_event():
    agent = request.json.get('agent', 'DemoAgent')
    event_type = request.json.get('event_type', 'DemoEvent')
    payload = request.json.get('payload', '{}')
    hub.log_event(agent, event_type, payload)
    return jsonify({'success': True})

# Observability: OpenTelemetry tracing example
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

@app.route('/demo/observability', methods=['POST'])
def demo_observability():
    with tracer.start_as_current_span("demo-span"):
        # Simulate a cross-agent operation
        hub.log_event('ObservabilityDemo', 'Trace', '{"msg": "Tracing demo event"}')
        time.sleep(0.1)
    return jsonify({'success': True})

# Cloud integration: push all new events to a cloud endpoint
CLOUD_ENDPOINT = 'https://your-cloud-endpoint/api/events'

def push_all_events_to_cloud():
    last_id = 0
    while True:
        with hub.lock, sqlite3.connect(hub.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT id, timestamp, agent, event_type, payload FROM events WHERE id > ? ORDER BY id ASC', (last_id,))
            rows = c.fetchall()
            for row in rows:
                event = {'id': row[0], 'timestamp': row[1], 'agent': row[2], 'event_type': row[3], 'payload': row[4]}
                try:
                    requests.post(CLOUD_ENDPOINT, json=event, timeout=2)
                except Exception:
                    pass
                last_id = row[0]
        time.sleep(5)

# To start cloud push in background:
# t = threading.Thread(target=push_all_events_to_cloud, daemon=True)
# t.start()

if __name__ == "__main__":
    app.run(port=5050, debug=True)
