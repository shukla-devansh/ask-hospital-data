import os
import sqlite3

import streamlit as st

from src import db, llm
from src.charts import make_chart
from src.pipeline import CannotAnswer, answer_question

EXAMPLE_QUESTIONS = [
    "Top 5 diagnoses by count",
    "Monthly admissions trend",
    "Average bill by department",
    "Readmission rate by department",
]


# cache results so clicking around the page doesn't call the API again
@st.cache_data
def get_answer(question):
    return answer_question(question)


@st.cache_data
def get_insight(question, df):
    return llm.write_insight(question, df)


st.set_page_config(page_title="Ask Your Hospital Data", layout="wide")
st.title("Ask Your Hospital Data")
st.write("Ask a question in plain English and get a table, a chart and a short insight.")

if not os.path.exists(db.DB_PATH):
    st.error("Database not found. Run `python src/generate_data.py` first.")
    st.stop()

# example buttons just fill in the question box
if "question" not in st.session_state:
    st.session_state.question = ""

cols = st.columns(len(EXAMPLE_QUESTIONS))
for col, example in zip(cols, EXAMPLE_QUESTIONS):
    if col.button(example, width="stretch"):
        st.session_state.question = example

question = st.text_input("Your question", key="question",
                         placeholder="e.g. Which department had the most readmissions last month?")

if question:
    try:
        with st.spinner("Thinking..."):
            sql, df = get_answer(question)
    except CannotAnswer as e:
        st.warning(str(e))
        st.stop()
    except ValueError as e:
        st.error(f"Blocked for safety: {e}")
        st.stop()
    except sqlite3.Error:
        st.error("Sorry, I couldn't answer that one. Try asking it a different way.")
        st.stop()
    except Exception as e:
        if "429" in str(e):
            st.error("Gemini free tier limit reached. Wait a minute and try again.")
        else:
            st.error(f"Something went wrong: {e}")
        st.stop()

    with st.expander("Generated SQL"):
        st.code(sql, language="sql")

    if df.empty:
        st.info("The query ran but returned no rows.")
        st.stop()

    st.dataframe(df, width="stretch", hide_index=True)

    chart = make_chart(df)
    if chart is not None:
        st.plotly_chart(chart, width="stretch")

    try:
        st.success(get_insight(question, df))
    except Exception:
        st.caption("Could not generate an insight for this result.")
