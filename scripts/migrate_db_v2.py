import sqlite3
from pathlib import Path

DB_PATH = Path("data/tiktok.db")


def column_exists(conn, table, column):
    rows = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return any(
        row[1] == column
        for row in rows
    )


with sqlite3.connect(DB_PATH) as conn:

    if not column_exists(
        conn,
        "experiments",
        "tiktok_video_id"
    ):
        conn.execute("""
            ALTER TABLE experiments
            ADD COLUMN tiktok_video_id TEXT
        """)

        print("Añadida columna: tiktok_video_id")

    else:
        print("Ya existe: tiktok_video_id")

    if not column_exists(
        conn,
        "experiments",
        "tiktok_url"
    ):
        conn.execute("""
            ALTER TABLE experiments
            ADD COLUMN tiktok_url TEXT
        """)

        print("Añadida columna: tiktok_url")

    else:
        print("Ya existe: tiktok_url")


print("Migración v2 completada.")