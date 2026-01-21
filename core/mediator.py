import sqlite3
import threading
from datetime import datetime

class SyncHub:
    def __init__(self, db_path='synchub.db'):
        self.db_path = db_path
        self._init_db()
        self.lock = threading.Lock()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent TEXT,
                event_type TEXT,
                payload TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                source_agent TEXT,
                target_agent TEXT,
                signal_type TEXT,
                payload TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS retraining_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                model_name TEXT,
                reason TEXT,
                status TEXT
            )''')
            conn.commit()

    def log_event(self, agent, event_type, payload):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO events (timestamp, agent, event_type, payload) VALUES (?, ?, ?, ?)',
                      (datetime.utcnow().isoformat(), agent, event_type, payload))
            conn.commit()

    def send_signal(self, source_agent, target_agent, signal_type, payload):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO signals (timestamp, source_agent, target_agent, signal_type, payload) VALUES (?, ?, ?, ?, ?)',
                      (datetime.utcnow().isoformat(), source_agent, target_agent, signal_type, payload))
            conn.commit()

    def trigger_retraining(self, model_name, reason):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO retraining_requests (timestamp, model_name, reason, status) VALUES (?, ?, ?, ?)',
                      (datetime.utcnow().isoformat(), model_name, reason, 'pending'))
            conn.commit()
        self.log_event('SyncHub', 'RetrainingEvent', f'{model_name} retraining triggered: {reason}')

    def get_pending_retraining(self):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM retraining_requests WHERE status = ?', ('pending',))
            return c.fetchall()

    def complete_retraining(self, retrain_id):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('UPDATE retraining_requests SET status = ? WHERE id = ?', ('complete', retrain_id))
            conn.commit()

# Example usage:
# hub = SyncHub()
# hub.log_event('SyncValue', 'LTVDrop', '{"ltv": 0.42}')
# hub.send_signal('SyncValue', 'SyncCreate', 'HighPriority', '{"action": "retrain"}')
# hub.trigger_retraining('dRNN', 'LTV accuracy dropped below threshold')
