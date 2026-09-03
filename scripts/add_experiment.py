import sqlite3

DB_PATH = "data/tiktok.db"

experiment = {
    "id": "EXP-001",
    "title": "Cabaña bajo la lluvia",
    "duration_seconds": 65,
    "concept": "Vídeo relajante generado con IA: cabaña nocturna, lluvia y ambiente acogedor.",
    "hypothesis": (
        "Un ambiente nocturno con lluvia y movimiento lento "
        "generará buena retención y guardados."
    ),
    "status": "draft",
}

with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        """
        INSERT INTO experiments (
            id,
            title,
            duration_seconds,
            concept,
            hypothesis,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            experiment["id"],
            experiment["title"],
            experiment["duration_seconds"],
            experiment["concept"],
            experiment["hypothesis"],
            experiment["status"],
        ),
    )

print("EXP-001 registrado correctamente.")