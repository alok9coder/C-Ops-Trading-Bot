import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional

DB_FILENAME = os.path.join(os.path.dirname(__file__), "market_data.sqlite3")

# Lock used to serialize access to the SQLite database across threads.
_db_lock = threading.RLock()


def _get_connection() -> sqlite3.Connection:
    # Open a sqlite connection with row access by column name.
    conn = sqlite3.connect(DB_FILENAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """Create the database and required tables if they do not exist."""
    with _db_lock:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_catalog (
                skin_name TEXT PRIMARY KEY,
                highest_bp INTEGER NOT NULL,
                lowest_sp INTEGER NOT NULL,
                calculated_margin REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bid_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skin_name TEXT NOT NULL,
                action TEXT NOT NULL,
                bid_value INTEGER NOT NULL,
                profit_margin REAL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()


def reset_market_catalog() -> None:
    """Remove stale market data before a fresh scan sweep."""
    with _db_lock:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS market_catalog")
        cursor.execute("DROP TABLE IF EXISTS bid_history")
        conn.commit()
        conn.close()
    initialize_database()


def save_or_update_skin_record(skin_name: str, highest_bp: int, lowest_sp: int, calculated_margin: float) -> None:
    """Insert or update a market record for a skin."""
    timestamp = datetime.utcnow().isoformat()
    with _db_lock:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO market_catalog (skin_name, highest_bp, lowest_sp, calculated_margin, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(skin_name) DO UPDATE SET
              highest_bp=excluded.highest_bp,
              lowest_sp=excluded.lowest_sp,
              calculated_margin=excluded.calculated_margin,
              updated_at=excluded.updated_at
            """,
            (skin_name, highest_bp, lowest_sp, calculated_margin, timestamp),
        )
        conn.commit()
        conn.close()


def query_skin_record(skin_name: str) -> Optional[sqlite3.Row]:
    # Return the most recent record for a specific skin from the market catalog.
    with _db_lock:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM market_catalog WHERE skin_name = ?",
            (skin_name,),
        )
        row = cursor.fetchone()
        conn.close()
        return row


def query_recent_history(limit: int = 50) -> list[sqlite3.Row]:
    # Retrieve the newest bid history entries up to the specified limit.
    with _db_lock:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM bid_history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return list(rows)


def record_bid_history(skin_name: str, action: str, bid_value: int, profit_margin: float | None = None) -> None:
    # Append an action record to the bid history table for auditing.
    timestamp = datetime.utcnow().isoformat()
    with _db_lock:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bid_history (skin_name, action, bid_value, profit_margin, created_at) VALUES (?, ?, ?, ?, ?)",
            (skin_name, action, bid_value, profit_margin, timestamp),
        )
        conn.commit()
        conn.close()
