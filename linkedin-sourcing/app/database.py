import sqlite3
from datetime import datetime
from typing import Dict, Any

DB_PATH = "candidates.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table with all columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT NOT NULL,
            candidate_name TEXT,
            current_company TEXT,
            message TEXT NOT NULL,
            sent_date TIMESTAMP,
            response TEXT,
            response_date TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    # Safe migration for new columns
    cursor.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'candidate_name' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN candidate_name TEXT")
    if 'current_company' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN current_company TEXT")
    if 'response_date' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN response_date TIMESTAMP")
    if 'status' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN status TEXT DEFAULT 'pending'")
    
    conn.commit()
    conn.close()

def save_message(candidate_id: str, candidate_name: str, current_company: str, message: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (candidate_id, candidate_name, current_company, message, sent_date, status) VALUES (?, ?, ?, ?, ?, ?)",
        (candidate_id, candidate_name, current_company, message, datetime.now(), 'sent')
    )
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id

def update_response(msg_id: int, response: str, status: str = 'replied'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE messages SET response = ?, status = ?, response_date = ? WHERE id = ?",
        (response, status, datetime.now(), msg_id)
    )
    conn.commit()
    conn.close()

def get_messages_for_candidate(candidate_id: str) -> list[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Explicit columns to avoid order issues
    cursor.execute("""
        SELECT id, candidate_id, candidate_name, current_company, message, sent_date, response, response_date, status 
        FROM messages WHERE candidate_id = ?
    """, (candidate_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0], 
            "candidate_id": r[1], 
            "candidate_name": r[2], 
            "current_company": r[3],
            "message": r[4], 
            "sent_date": r[5], 
            "response": r[6], 
            "response_date": r[7], 
            "status": r[8]
        } for r in rows
    ]

def get_all_interactions() -> list[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Explicit columns
    cursor.execute("""
        SELECT id, candidate_id, candidate_name, current_company, message, sent_date, response, response_date, status 
        FROM messages ORDER BY sent_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0], 
            "candidate_id": r[1], 
            "candidate_name": r[2], 
            "current_company": r[3],
            "message": r[4], 
            "sent_date": r[5], 
            "response": r[6], 
            "response_date": r[7], 
            "status": r[8]
        } for r in rows
    ]

init_db()
