# Picks a chart based on what the result looks like.

import pandas as pd
import plotly.express as px


def make_chart(df):
    """Line chart for dates, bar chart for categories, None if it doesn't fit."""
    if len(df) < 2 or len(df.columns) < 2:
        return None

    x = df.columns[0]
    numeric_cols = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        return None
    y = numeric_cols[0]

    # if the first column can be read as dates (like 2026-03), draw a line over time
    if not pd.api.types.is_numeric_dtype(df[x]):
        dates = pd.to_datetime(df[x], errors="coerce", format="mixed")
        if dates.notna().all():
            return px.line(df, x=x, y=y, markers=True)
        return px.bar(df, x=x, y=y)

    return None
