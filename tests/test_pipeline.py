# The LLM is replaced with a fake function so these tests need no API key.

import pandas as pd
import pytest

from src import llm
from src.charts import make_chart
from src.pipeline import CannotAnswer, answer_question


def fake_llm(*answers):
    # returns the given answers one by one, and remembers the prompts it got
    replies = list(answers)
    prompts = []

    def ask(prompt):
        prompts.append(prompt)
        return replies.pop(0)

    return ask, prompts


def test_question_to_sql_end_to_end(test_db, monkeypatch):
    ask, prompts = fake_llm("```sql\nSELECT d.name, COUNT(*) AS n FROM admissions a "
                            "JOIN departments d ON a.department_id = d.id GROUP BY d.name\n```")
    monkeypatch.setattr(llm, "ask_llm", ask)

    sql, df = answer_question("admissions by department")

    assert sql.startswith("SELECT")
    assert len(df) == 7
    assert "CREATE TABLE admissions" in prompts[0]  # schema is in the prompt


def test_broken_sql_is_retried_once(test_db, monkeypatch):
    ask, prompts = fake_llm("SELECT nme FROM departments", "SELECT name FROM departments")
    monkeypatch.setattr(llm, "ask_llm", ask)

    sql, df = answer_question("list departments")

    assert sql == "SELECT name FROM departments"
    assert len(prompts) == 2
    assert "no such column" in prompts[1]  # the error was sent back to the model


def test_delete_request_is_blocked(test_db, monkeypatch):
    ask, _ = fake_llm("DELETE FROM patients")
    monkeypatch.setattr(llm, "ask_llm", ask)

    with pytest.raises(ValueError):
        answer_question("delete all patients")


def test_model_refusal(test_db, monkeypatch):
    ask, _ = fake_llm("CANNOT_ANSWER")
    monkeypatch.setattr(llm, "ask_llm", ask)

    with pytest.raises(CannotAnswer):
        answer_question("delete all patients")


def test_chart_types():
    by_month = pd.DataFrame({"month": ["2026-01", "2026-02"], "admissions": [10, 20]})
    by_dept = pd.DataFrame({"department": ["Cardiology", "Oncology"], "avg_bill": [1.0, 2.0]})
    single = pd.DataFrame({"total": [5]})

    assert make_chart(by_month).data[0].type == "scatter"  # plotly line charts are scatter traces
    assert make_chart(by_dept).data[0].type == "bar"
    assert make_chart(single) is None
