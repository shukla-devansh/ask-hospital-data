# Every call to the LLM goes through this file.
# To switch from Gemini to another provider, only ask_llm() needs to change.

import os

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

RULES = """Rules:
- Write a query for SQLite (use strftime for dates, there is no MONTH() or YEAR()).
- Only write a single SELECT statement. Never change data.
- Always add LIMIT 200 or less.
- Dates are stored as text in YYYY-MM-DD format. Use date('now') for today.
- readmitted is 1 or 0, so the readmission rate is AVG(readmitted).
- Use department names, not ids, in the result.
- If the question asks to change, delete or add data, or has nothing to do with this
  database, reply with exactly: CANNOT_ANSWER
- Reply with only the SQL, no explanation and no markdown."""

# few-shot examples: showing the model a few question -> SQL pairs
# teaches it our table names and style better than rules alone
EXAMPLES = """Question: How many patients are there?
SQL: SELECT COUNT(*) AS total_patients FROM patients LIMIT 1

Question: Which doctors work in Cardiology?
SQL: SELECT doc.name FROM doctors doc JOIN departments d ON doc.department_id = d.id WHERE d.name = 'Cardiology' LIMIT 200

Question: Number of admissions per month
SQL: SELECT strftime('%Y-%m', admit_date) AS month, COUNT(*) AS admissions FROM admissions GROUP BY month ORDER BY month LIMIT 200

Question: Which department had the most readmissions last month?
SQL: SELECT d.name AS department, SUM(a.readmitted) AS readmissions FROM admissions a JOIN departments d ON a.department_id = d.id WHERE strftime('%Y-%m', a.admit_date) = strftime('%Y-%m', 'now', '-1 month') GROUP BY d.name ORDER BY readmissions DESC LIMIT 1"""


def ask_llm(prompt):
    # imported here so the rest of the app (and the tests) work without the package or a key
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()


def clean_sql(text):
    # models sometimes wrap the answer in ```sql ... ``` even when told not to
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("sql"):
            text = text[3:]
    return text.strip()


def build_sql_prompt(question, schema):
    return f"""You are a data analyst for a hospital. Turn the question into a SQL query.

Database schema:
{schema}

{RULES}

Examples:
{EXAMPLES}

Question: {question}
SQL:"""


def question_to_sql(question, schema):
    return clean_sql(ask_llm(build_sql_prompt(question, schema)))


def fix_sql(question, schema, bad_sql, error):
    # self-correction: show the model its own query and the error it caused
    prompt = build_sql_prompt(question, schema)
    prompt += f""" {bad_sql}

That query failed with this error: {error}
Write a corrected query. Reply with only the SQL.
SQL:"""
    return clean_sql(ask_llm(prompt))


def write_insight(question, df):
    prompt = f"""A user asked: "{question}"
Here is the result from the hospital database:
{df.head(30).to_string(index=False)}

Write 1-2 short sentences about the most important thing in this result.
Use plain English and mention actual numbers. Do not mention SQL."""
    return ask_llm(prompt)
