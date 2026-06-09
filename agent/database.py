# agent/database.py

import sqlite3
import datetime
import json


def init_database():
    """
    Creates the database and table if they don't exist
    Run once on startup
    """
    conn = sqlite3.connect("intelligence.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS run_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT,
            domain TEXT,
            gaps TEXT,
            severity TEXT,
            approved INTEGER,
            recommendation TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Database initialised")


def load_history(domain: str) -> list:
    """
    Loads previous runs for the same domain
    Returns last 3 runs
    """
    conn = sqlite3.connect("intelligence.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT run_date, domain, gaps, severity, approved, recommendation
        FROM run_history
        WHERE domain = ?
        ORDER BY run_date DESC
        LIMIT 3
    """, (domain,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "date": row[0],
            "domain": row[1],
            "gaps": json.loads(row[2]),
            "severity": row[3],
            "approved": bool(row[4]),
            "recommendation": row[5]
        })
    
    return history


def save_run(state: dict):
    """
    Saves the current run to SQLite
    """
    conn = sqlite3.connect("intelligence.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO run_history 
        (run_date, domain, gaps, severity, approved, recommendation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.datetime.now().isoformat(),
        state['domain'],
        json.dumps(state['gaps']),
        state['severity'],
        1 if state['approved'] else 0,
        state['recommendation']
    ))
    
    conn.commit()
    conn.close()
    print("✓ Run saved to history")