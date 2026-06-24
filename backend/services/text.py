"""
Text standardisation for object/string columns:
- Strip leading/trailing whitespace
- Collapse internal whitespace
- Lowercase conversion
- Remove non-printable / control characters
"""
import pandas as pd
import re


def standardize_text(df: pd.DataFrame):
    audit = []
    str_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

    for col in str_cols:
        before = df[col].copy()

        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)          # collapse whitespace
            .str.replace(r"[^\x20-\x7E]", "", regex=True)  # remove non-ASCII printable
            .str.lower()
        )
        # Restore NaN-like "nan" strings to actual NaN
        df[col] = df[col].replace("nan", pd.NA)

        changed = int((before.astype(str) != df[col].astype(str)).sum())
        if changed:
            audit.append(f"'{col}': standardised text in {changed} cell(s).")

    return df, audit
