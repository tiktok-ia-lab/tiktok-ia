import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/tiktok.db")


def optional_int(prompt):
    value = input(prompt).strip()

    if value == "":
        return None

    return int(value)


def optional_float(prompt):
    value = input(prompt).strip()

    if value == "":
        return None

    return float(value)


experiment_id = (
    input("Vídeo [EXP-001]: ").strip()
    or "EXP-001"
)

views = optional_int("Visualizaciones: ")
likes = optional_int("Likes: ")
comments = optional_int("Comentarios: ")
shares = optional_int("Compartidos: ")
saves = optional_int("Guardados: ")
followers_gained = optional_int(
    "Seguidores ganados: "
)
avg_watch_time_seconds = optional_float(
    "Tiempo medio de reproducción (segundos): "
)
completion_rate = optional_float(
    "Porcentaje completado: "
)


with sqlite3.connect(DB_PATH) as conn:

    exists = conn.execute(
        """
        SELECT 1
        FROM experiments
        WHERE id = ?
        """,
        (experiment_id,),
    ).fetchone()

    if not exists:
        raise SystemExit(
            f"ERROR: no existe {experiment_id}"
        )

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
            datetime.now().isoformat(
                timespec="seconds"
            ),
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