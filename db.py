"""
Database helper functions for the Massage Shop system.
Uses SQLite and provides simple CRUD and aggregate queries.
"""
import sqlite3
from sqlite3 import Connection
from typing import List, Dict, Optional


def get_conn(db_path: str) -> Connection:
    """Get a SQLite connection with row factory to return dict-like rows."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str):
    """Initialize the database and create table if not exists."""
    conn = get_conn(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            card_amount REAL DEFAULT 0,
            cash_amount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            customer_count INTEGER DEFAULT 0,
            note TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def upsert_record(db_path: str, date_str: str, card_amount: float, cash_amount: float,
                  total_amount: float, customer_count: int, note: Optional[str]):
    """
    Insert or update a record for given date (date field is unique).
    """
    conn = get_conn(db_path)
    c = conn.cursor()
    # try update first
    c.execute(
        """
        INSERT INTO records (date, card_amount, cash_amount, total_amount, customer_count, note)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
          card_amount=excluded.card_amount,
          cash_amount=excluded.cash_amount,
          total_amount=excluded.total_amount,
          customer_count=excluded.customer_count,
          note=excluded.note
        """,
        (date_str, card_amount, cash_amount, total_amount, customer_count, note)
    )
    conn.commit()
    conn.close()


def get_record_by_date(db_path: str, date_str: str) -> Optional[Dict]:
    """Return a single record by date or None."""
    conn = get_conn(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM records WHERE date = ?", (date_str,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_records(db_path: str, start: str = None, end: str = None, order: str = "desc") -> List[Dict]:
    """
    Get records optionally filtered by start/end date (inclusive).
    order: 'asc' or 'desc' by date.
    """
    conn = get_conn(db_path)
    c = conn.cursor()
    query = "SELECT * FROM records"
    params = []
    if start and end:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([start, end])
    elif start:
        query += " WHERE date >= ?"
        params.append(start)
    elif end:
        query += " WHERE date <= ?"
        params.append(end)

    query += " ORDER BY date " + ("ASC" if order == "asc" else "DESC")
    c.execute(query, tuple(params))
    rows = c.fetchall()
    conn.close()
    # convert to list of dicts and ensure numeric types
    result = []
    for r in rows:
        row = dict(r)
        # round floats to two decimals for display convenience (store raw as well)
        row["card_amount"] = float(row.get("card_amount") or 0.0)
        row["cash_amount"] = float(row.get("cash_amount") or 0.0)
        row["total_amount"] = float(row.get("total_amount") or 0.0)
        row["customer_count"] = int(row.get("customer_count") or 0)
        row["note"] = row.get("note") or ""
        result.append(row)
    return result