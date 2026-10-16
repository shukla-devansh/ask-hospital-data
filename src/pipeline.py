# Question -> SQL -> safety check -> run, with one retry if the SQL fails.

import sqlite3

from src import db, llm, sql_guard


class CannotAnswer(Exception):
    pass


def answer_question(question):
    """Returns (sql, dataframe). Raises ValueError, CannotAnswer or sqlite3.Error."""
    schema = db.get_schema()
    sql = llm.question_to_sql(question, schema)

    if "CANNOT_ANSWER" in sql:
        raise CannotAnswer("I can only answer read-only questions about the hospital data.")

    # unsafe SQL is never retried, it is just rejected
    safe_sql = sql_guard.check_sql(sql)

    try:
        df = db.run_query(safe_sql)
    except sqlite3.Error as error:
        # give the LLM one chance to fix its own mistake
        sql = llm.fix_sql(question, schema, sql, str(error))
        safe_sql = sql_guard.check_sql(sql)
        df = db.run_query(safe_sql)  # if this fails too, the error goes to the app

    return sql, df
