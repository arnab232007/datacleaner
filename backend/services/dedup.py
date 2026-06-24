"""
Deduplication: removes exact duplicate rows, reports count.
"""
import pandas as pd


def remove_duplicates(df: pd.DataFrame):
    audit = []
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed:
        audit.append(f"Removed {removed} exact duplicate row(s).")
    else:
        audit.append("No duplicate rows found.")
    return df, audit, removed
