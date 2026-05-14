import sqlite3
import json
from typing import Dict, Any, List
from datetime import datetime

DB_PATH = "tickets.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            user_email TEXT,
            issue_text TEXT,
            category TEXT,
            status TEXT,
            resolution TEXT,
            investigation_log TEXT,
            cache_hit BOOLEAN,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_ticket(ticket_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ensure cache_hit is boolean
    cache_hit = ticket_data.get("cache_hit", False)
    # Convert investigation log to JSON string
    investigation_log = json.dumps(ticket_data.get("investigation_log", {}))
    
    cursor.execute('''
        INSERT INTO tickets (id, user_email, issue_text, category, status, resolution, investigation_log, cache_hit, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ticket_data["ticket_id"],
        ticket_data["user_email"],
        ticket_data["issue_text"],
        ticket_data.get("category", "Uncategorized"),
        ticket_data.get("status", "Requires Review"),
        ticket_data.get("resolution", ""),
        investigation_log,
        cache_hit,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_all_tickets() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        d = dict(row)
        if d["investigation_log"]:
            try:
                d["investigation_log"] = json.loads(d["investigation_log"])
            except json.JSONDecodeError:
                d["investigation_log"] = {}
        # Convert 1/0 to True/False for cache_hit
        d["cache_hit"] = bool(d["cache_hit"])
        result.append(d)
        
    return result

def get_ticket_by_id(ticket_id: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    d = dict(row)
    if d["investigation_log"]:
        try:
            d["investigation_log"] = json.loads(d["investigation_log"])
        except json.JSONDecodeError:
            d["investigation_log"] = {}
    d["cache_hit"] = bool(d["cache_hit"])
    return d
