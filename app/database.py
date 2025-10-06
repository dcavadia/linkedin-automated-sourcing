import sqlite3
from datetime import datetime
from typing import Dict, Any, List

DB_PATH = "candidates.db"

def init_db():
    """Initialize tables and apply migrations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
        status TEXT DEFAULT 'generated'
    )
    """)

    cursor.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'candidate_name' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN candidate_name TEXT")
    if 'current_company' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN current_company TEXT")
    if 'response_date' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN response_date TIMESTAMP")
    if 'status' not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN status TEXT DEFAULT 'generated'")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        linkedin_id TEXT UNIQUE NOT NULL,
        profile_url TEXT,
        name TEXT NOT NULL,
        skills TEXT,
        relevance_score REAL DEFAULT 0.0,
        search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("PRAGMA table_info(candidates)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'linkedin_id' not in columns:
        cursor.execute("ALTER TABLE candidates ADD COLUMN linkedin_id TEXT UNIQUE NOT NULL DEFAULT 'unknown'")
    if 'relevance_score' not in columns:
        cursor.execute("ALTER TABLE candidates ADD COLUMN relevance_score REAL DEFAULT 0.0")

    conn.commit()
    conn.close()

def save_message(candidate_id: str, candidate_name: str, current_company: str, message: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO messages (candidate_id, candidate_name, current_company, message, status)
        VALUES (?, ?, ?, ?, ?)""",
        (candidate_id, candidate_name, current_company, message, 'generated')
    )
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id

def update_message_status(msg_id: int, status: str = 'sent') -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if status == 'sent':
        cursor.execute(
            "UPDATE messages SET status = ?, sent_date = ? WHERE id = ?",
            (status, datetime.now(), msg_id)
        )
    else:
        cursor.execute("UPDATE messages SET status = ? WHERE id = ?", (status, msg_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def update_response(msg_id: int, response: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE messages SET response = ?, status = ?, response_date = ? WHERE id = ?""",
        (response, 'replied', datetime.now(), msg_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def get_messages_for_candidate(candidate_id: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, candidate_id, candidate_name, current_company, message, sent_date, response,
        response_date, status
        FROM messages WHERE candidate_id = ? ORDER BY id DESC""",
        (candidate_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "candidate_id": row[1],
            "candidate_name": row[2],
            "current_company": row[3],
            "message": row[4],
            "sent_date": row[5],
            "response": row[6],
            "response_date": row[7],
            "status": row[8]
        }
        for row in rows
    ]

def get_all_interactions() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, candidate_id, candidate_name, current_company, message, sent_date, response,
        response_date, status
        FROM messages ORDER BY sent_date DESC, id DESC"""
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "candidate_id": row[1],
            "candidate_name": row[2],
            "current_company": row[3],
            "message": row[4],
            "sent_date": row[5],
            "response": row[6],
            "response_date": row[7],
            "status": row[8]
        }
        for row in rows
    ]

def save_candidates(profiles: List[Dict[str, Any]]) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saved_count = 0
    for profile in profiles:
        linkedin_id = profile.get('id') or profile.get('linkedin_id', 'unknown')
        profile_url = profile.get('profile_url', '')
        name = profile.get('name', 'Unknown')
        skills_str = ','.join(profile.get('skills', [])) if isinstance(profile.get('skills'), list) else str(profile.get('skills', ''))
        relevance_score = float(profile.get('relevance_score', 0.0))
        cursor.execute(
            """INSERT OR IGNORE INTO candidates (linkedin_id, profile_url, name, skills, relevance_score)
            VALUES (?, ?, ?, ?, ?)""",
            (linkedin_id, profile_url, name, skills_str, relevance_score)
        )
        if cursor.rowcount > 0:
            saved_count += 1
    conn.commit()
    conn.close()
    return saved_count

def get_candidates() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, linkedin_id, profile_url, name, skills, relevance_score, search_date FROM candidates ORDER BY search_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "linkedin_id": row[1],
            "profile_url": row[2],
            "name": row[3],
            "skills": row[4],
            "relevance_score": row[5],
            "search_date": row[6]
        }
        for row in rows
    ]

init_db()
