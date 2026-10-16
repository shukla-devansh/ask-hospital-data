import pytest

from src.sql_guard import check_sql


@pytest.mark.parametrize("sql", [
    "DELETE FROM patients",
    "DROP TABLE patients",
    "UPDATE admissions SET bill_amount = 0",
    "INSERT INTO patients VALUES (999, 30, 'Male', 'Delhi')",
    "ALTER TABLE patients ADD COLUMN x TEXT",
    "PRAGMA table_info(patients)",
    "SELECT * FROM patients; DROP TABLE patients",
    "SELECT * FROM patients -- hidden comment",
    "WITH x AS (SELECT 1) DELETE FROM patients",
    "",
])
def test_dangerous_queries_are_blocked(sql):
    with pytest.raises(ValueError):
        check_sql(sql)


@pytest.mark.parametrize("sql", [
    "SELECT * FROM patients",
    "select city, count(*) from patients group by city",
    "SELECT diagnosis, COUNT(*) AS n FROM admissions GROUP BY diagnosis ORDER BY n DESC LIMIT 5;",
    "WITH t AS (SELECT * FROM admissions) SELECT COUNT(*) FROM t",
])
def test_valid_selects_are_allowed(sql):
    result = check_sql(sql)
    assert result.endswith("LIMIT 200")


def test_column_names_containing_blocked_words_are_fine():
    # "updated_at" should not match the word UPDATE
    check_sql("SELECT updated_at FROM logs")
