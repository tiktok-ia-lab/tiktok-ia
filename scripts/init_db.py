import sqlite3
from pathlib import Path

DB_PATH = Path("data/tiktok.db")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

with sqlite3.connect(DB_PATH) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            published_at TEXT,
            duration_seconds INTEGER,
            concept TEXT,
            hypothesis TEXT,
            status TEXT NOT NULL DEFAULT 'draft'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            collected_at TEXT NOT NULL,
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            shares INTEGER,
            saves INTEGER,
            followers_gained INTEGER,
            avg_watch_time_seconds REAL,
            completion_rate REAL,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        )
    """)

print(f"Base de datos creada en {DB_PATH}")