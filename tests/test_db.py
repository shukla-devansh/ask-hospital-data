import sqlite3

import pytest

from src import db


def test_tables_have_data(test_db):
    assert db.run_query("SELECT COUNT(*) AS n FROM patients")["n"][0] == 500
    assert db.run_query("SELECT COUNT(*) AS n FROM admissions")["n"][0] == 2000


def test_schema_has_all_tables(test_db):
    schema = db.get_schema()
    for table in ["patients", "departments", "doctors", "admissions"]:
        assert f"CREATE TABLE {table}" in schema


def test_database_is_read_only(test_db):
    # even without the guard, SQLite should refuse to write
    with pytest.raises(sqlite3.OperationalError):
        db.run_query("DELETE FROM patients")


def test_row_limit(test_db):
    df = db.run_query("SELECT * FROM admissions")
    assert len(df) == db.MAX_ROWS
