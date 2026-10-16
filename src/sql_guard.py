# Checks the SQL from the LLM before we run it.
# We never trust model output blindly, it could be wrong or even harmful.

import re

MAX_ROWS = 200

BLOCKED_WORDS = ["drop", "delete", "update", "insert", "alter", "pragma",
                 "create", "attach", "detach", "vacuum"]


def check_sql(sql):
    """Returns a safe version of the query, or raises ValueError."""
    sql = sql.strip().rstrip(";").strip()

    if sql == "":
        raise ValueError("The query is empty.")

    # a ; in the middle means more than one statement, e.g. "SELECT 1; DROP TABLE x"
    if ";" in sql:
        raise ValueError("Only one SQL statement is allowed.")

    # comments can be used to hide things, so just don't allow them
    if "--" in sql or "/*" in sql:
        raise ValueError("SQL comments are not allowed.")

    first_word = sql.split()[0].lower()
    if first_word not in ("select", "with"):
        raise ValueError("Only SELECT queries are allowed.")

    for word in BLOCKED_WORDS:
        if re.search(r"\b" + word + r"\b", sql, re.IGNORECASE):
            raise ValueError(f"Blocked keyword found: {word.upper()}")

    # wrap the query so it can never return more than MAX_ROWS rows
    return f"SELECT * FROM ({sql}) LIMIT {MAX_ROWS}"
