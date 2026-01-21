import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../db/syncmemory.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS creative_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creative_id TEXT,
            style TEXT,
            revenue REAL,
            approved_at TEXT,
            extra JSON
        )
    ''')
    conn.commit()
    conn.close()

# Log a creative's performance

def log_creative_performance(creative_id, style, revenue, approved_at=None, extra=None):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO creative_performance (creative_id, style, revenue, approved_at, extra)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        creative_id,
        style,
        revenue,
        approved_at or datetime.utcnow().isoformat(),
        extra if extra is not None else None
    ))
    conn.commit()
    conn.close()

# Query top styles by revenue in a given period

def get_top_styles(start_date=None, end_date=None, limit=5):
    conn = get_db()
    c = conn.cursor()
    query = '''
        SELECT style, SUM(revenue) as total_revenue, COUNT(*) as count
        FROM creative_performance
        WHERE 1=1
    '''
    params = []
    if start_date:
        query += ' AND approved_at >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND approved_at <= ?'
        params.append(end_date)
    query += ' GROUP BY style ORDER BY total_revenue DESC LIMIT ?'
    params.append(limit)
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    return [dict(row) for row in results]

# Utility: get last week's top styles
def get_last_week_top_styles(limit=5):
    now = datetime.utcnow()
    start = (now - timedelta(days=7)).isoformat()
    end = now.isoformat()
    return get_top_styles(start, end, limit)

init_db()
