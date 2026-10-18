import sqlite3
from pathlib import Path


DB_PATH = Path("data/bot.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def init_db() -> None:
    with get_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_notification_at TIMESTAMP
            )
            """
        )

        connection.execute("""
                    CREATE TABLE IF NOT EXISTS check_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TEXT NOT NULL DEFAULT (
                            strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                        ),
                        result TEXT NOT NULL,
                        days_count INTEGER,
                        status_code INTEGER
                    )
                """)

        connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_check_events_created_at
                    ON check_events(created_at)
                """)

        connection.commit()