"""SQLite database models for VibeBreaker."""
import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import Optional

# Use the api directory for the database file
API_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(API_DIR, "vibebreaker.db")

def get_db():
    """Get a new SQLite connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            original_code TEXT,
            language TEXT,
            created_at TEXT,
            current_step_index INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS session_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            step_index INTEGER,
            objective TEXT,
            learning_concept TEXT,
            algorithm TEXT,
            starter_hint TEXT,
            reference_code TEXT,
            status TEXT DEFAULT 'pending',
            hint_level_used TEXT,
            created_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    # Dynamic migration for existing databases
    existing_cols = [r[1] for r in c.execute("PRAGMA table_info(session_steps)").fetchall()]
    if "algorithm" not in existing_cols:
        c.execute("ALTER TABLE session_steps ADD COLUMN algorithm TEXT")
    if "starter_hint" not in existing_cols:
        c.execute("ALTER TABLE session_steps ADD COLUMN starter_hint TEXT")
    if "reference_code" not in existing_cols:
        c.execute("ALTER TABLE session_steps ADD COLUMN reference_code TEXT")

    c.execute("""
        CREATE TABLE IF NOT EXISTS session_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            step_id INTEGER,
            student_code TEXT,
            evaluation_status TEXT DEFAULT 'fail',
            feedback TEXT,
            created_at TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            FOREIGN KEY (step_id) REFERENCES session_steps(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS agent_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            agent_name TEXT,
            input_summary TEXT,
            output_summary TEXT,
            model_name TEXT,
            latency_ms INTEGER,
            created_at TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()