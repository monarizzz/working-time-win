import sqlite3
from datetime import date
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent.parent / "usage.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS usage (
    day TEXT NOT NULL,
    process_name TEXT NOT NULL,
    window_title TEXT NOT NULL DEFAULT '',
    seconds INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (day, process_name, window_title)
);
CREATE INDEX IF NOT EXISTS idx_usage_day ON usage(day);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def add_seconds(process_name: str, window_title: str, seconds: int, day: str = None):
    if seconds <= 0:
        return
    day = day or date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO usage (day, process_name, window_title, seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(day, process_name, window_title)
            DO UPDATE SET seconds = seconds + excluded.seconds
            """,
            (day, process_name, window_title, seconds),
        )
        conn.commit()


def get_usage_by_process(day: str = None):
    day = day or date.today().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT process_name, SUM(seconds) AS total
            FROM usage
            WHERE day = ?
            GROUP BY process_name
            ORDER BY total DESC
            """,
            (day,),
        )
        return cur.fetchall()


def get_available_days():
    with get_conn() as conn:
        cur = conn.execute("SELECT DISTINCT day FROM usage ORDER BY day DESC")
        return [row[0] for row in cur.fetchall()]
