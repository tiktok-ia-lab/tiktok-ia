import sqlite3
from datetime import datetime

DB_PATH = "data/tiktok.db"

experiment_id = input("Vídeo [EXP-001]: ").strip() or "EXP-001"

views = int(input("Visualizaciones: ") or 0)
likes = int(input("Likes: ") or 0)
comments = int(input("Comentarios: ") or 0)
shares = int(input("Compartidos: ") or 0)
saves = int(input("Guardados: ") or 0)
followers_gained = int(input("Seguidores ganados: ") or 0)
avg_watch_time_seconds = float(input("Tiempo medio de reproducción (segundos): ") or 0)
completion_rate = float(input("Porcentaje completado: ") or 0)

with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        """
        INSERT INTO metrics (
            experiment_id,
            collected_at,
            views,
            likes,
            comments,
            shares,
            saves,
            followers_gained,
            avg_watch_time_seconds,
            completion_rate
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            experiment_id,
            datetime.now().isoformat(timespec="seconds"),
            views,
            likes,
            comments,
            shares,
            saves,
            followers_gained,
            avg_watch_time_seconds,
            completion_rate,
        ),
    )

print("Métricas registradas correctamente.")