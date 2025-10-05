import sqlite3
from datetime import datetime
from typing import Dict, Any, List

DB_PATH = "candidates.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Existing messages table (from Modules 2-3, unchanged)
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
    
    # New: Candidates table (stores search results; candidate_id = id or linkedin_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            linkedin_id TEXT UNIQUE,
            profile_url TEXT,
            name TEXT,
            skills TEXT,  -- JSON-like or comma-separated from search
            experience_years INTEGER,
            location TEXT,
            current_company TEXT,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Existing messages functions (unchanged: save_message, update_response, get_messages_for_candidate, get_all_interactions)
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

# New: Candidates functions
def save_candidates(profiles: List[Dict[str, Any]]) -> int:
    """Save list of profiles; returns count saved (deduped by linkedin_id)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saved_count = 0
    for profile in profiles:
        # Use linkedin_id if present, else profile_url as fallback
        linkedin_id = profile.get('id') or profile.get('linkedin_id', 'unknown')
        profile_url = profile.get('profile_url') or profile.get('profile_url', '')
        skills = ','.join(profile.get('skills', []))  # Comma-separated
        cursor.execute("""
            INSERT OR IGNORE INTO candidates (linkedin_id, profile_url, name, skills, experience_years, location, current_company, search_date) 
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (linkedin_id, profile_url, profile.get('name'), skills, profile.get('experience_years'), 
              profile.get('location'), profile.get('current_company')))
        if cursor.rowcount > 0:  # New insert
            saved_count += 1
    conn.commit()
    conn.close()
    return saved_count

def get_candidates() -> List[Dict[str, Any]]:
    """Fetch all saved candidates."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates ORDER BY search_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "linkedin_id": r[1], "profile_url": r[2], "name": r[3], "skills": r[4],
            "experience_years": r[5], "location": r[6], "current_company": r[7], "search_date": r[8]
        } for r in rows
    ]

init_db()  # Runs on import
