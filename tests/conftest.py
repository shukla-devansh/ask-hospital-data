import pytest

from src import db
from src.generate_data import create_database


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    # build a fresh fake database in a temp folder and point db.py at it
    path = str(tmp_path / "test.db")
    create_database(path)
    monkeypatch.setattr(db, "DB_PATH", path)
    return path
