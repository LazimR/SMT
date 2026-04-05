import sqlite3
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "leituras.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leituras (
                id TEXT PRIMARY KEY,
                sensor_id TEXT NOT NULL,
                temperatura REAL NOT NULL,
                status_logico TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.commit()


def get_leitura_by_id(leitura_id: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, sensor_id, temperatura, status_logico, timestamp FROM leituras WHERE id = ?",
            (leitura_id,),
        ).fetchone()
    return row


def insert_leitura(
    leitura_id: str,
    sensor_id: str,
    temperatura: float,
    status_logico: str,
    timestamp: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO leituras (id, sensor_id, temperatura, status_logico, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (leitura_id, sensor_id, temperatura, status_logico, timestamp),
        )
        conn.commit()
