import sqlite3
from datetime import datetime
from typing import Dict, Any, List

DB_PATH = "candidates.db"

def get_db_connection():
    """Get SQLite connection (direct connect for consistency)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Optional: Dict-like rows if needed
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Existing messages table (unchanged)
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
            status TEXT DEFAULT 'sent'
        )
    """)
    
    # Migrations for messages (unchanged)
    cursor.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'candidate_name' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN candidate_name TEXT")
    if 'current_company' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN current_company TEXT")
    if 'response_date' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN response_date TIMESTAMP")
    if 'status' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN status TEXT DEFAULT 'sent'")
    
    # Simplified: Candidates table (only requested fields)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            linkedin_id TEXT UNIQUE,
            profile_url TEXT,
            name TEXT,
            skills TEXT,
            relevance_score REAL,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Existing messages functions (unchanged)
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

def get_messages_for_candidate(candidate_id: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, candidate_id, candidate_name, current_company, message, sent_date, response, response_date, status 
        FROM messages WHERE candidate_id = ?
    """, (candidate_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "candidate_id": r[1], "candidate_name": r[2], "current_company": r[3],
            "message": r[4], "sent_date": r[5], "response": r[6], "response_date": r[7], "status": r[8]
        } for r in rows
    ]

def get_all_interactions() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, candidate_id, candidate_name, current_company, message, sent_date, response, response_date, status 
        FROM messages ORDER BY sent_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "candidate_id": r[1], "candidate_name": r[2], "current_company": r[3],
            "message": r[4], "sent_date": r[5], "response": r[6], "response_date": r[7], "status": r[8]
        } for r in rows
    ]

# Updated: Candidates functions (simplified fields)
def save_candidates(profiles: List[Dict[str, Any]]) -> int:
    """Save list of profiles (subset: linkedin_id, profile_url, name, skills, relevance_score); deduped by linkedin_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saved_count = 0
    for profile in profiles:
        linkedin_id = profile.get('id') or profile.get('linkedin_id', 'unknown')  # Cleaned username
        profile_url = profile.get('profile_url') or ''
        skills = ','.join(profile.get('skills', []))  # Comma-separated
        name = profile.get('name') or ''
        relevance_score = profile.get('relevance_score', 0.0)
        cursor.execute("""
            INSERT OR IGNORE INTO candidates (linkedin_id, profile_url, name, skills, relevance_score, search_date) 
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (linkedin_id, profile_url, name, skills, relevance_score))
        if cursor.rowcount > 0:  # New insert
            saved_count += 1
    conn.commit()
    conn.close()
    return saved_count

def get_candidates() -> List[Dict[str, Any]]:
    """Fetch all saved candidates (simplified)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates ORDER BY search_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "linkedin_id": r[1], "profile_url": r[2], "name": r[3], "skills": r[4],
            "relevance_score": r[5], "search_date": r[6]
        } for r in rows
    ]

def update_message_status(msg_id: int, status: str = 'sent'):
    """Update message status and sent_date if 'sent'."""
    conn = get_db_connection()  # Now defined
    cursor = conn.cursor()
    if status == 'sent':
        cursor.execute("UPDATE messages SET status = ?, sent_date = ? WHERE id = ?", (status, datetime.now(), msg_id))
    else:
        cursor.execute("UPDATE messages SET status = ? WHERE id = ?", (status, msg_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

init_db()  # Runs on import
