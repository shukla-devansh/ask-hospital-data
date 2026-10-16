# Small helpers to talk to the SQLite database.

import os
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hospital.db")
MAX_ROWS = 200


def connect():
    # mode=ro opens the file read-only, so even if a bad query gets through
    # the guard, SQLite itself will refuse to change anything
    uri = Path(DB_PATH).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def get_schema():
    # the CREATE TABLE statements, which we paste into the LLM prompt
    conn = connect()
    rows = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table'").fetchall()
    conn.close()
    return "\n\n".join(row[0] for row in rows)


def run_query(sql):
    conn = connect()
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchmany(MAX_ROWS)  # never pull more than MAX_ROWS
        columns = [col[0] for col in cursor.description]
    finally:
        conn.close()
    return pd.DataFrame(rows, columns=columns)
