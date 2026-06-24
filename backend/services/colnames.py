"""
Column name cleaning:
- Strip whitespace
- Lowercase
- Replace spaces and hyphens with underscores
- Remove non-alphanumeric characters (except underscores)
"""
import re
import pandas as pd


def clean_column_names(df: pd.DataFrame):
    audit = []
    rename_map = {}

    for col in df.columns:
        new_col = col.strip().lower()
        new_col = re.sub(r"[\s\-]+", "_", new_col)           # spaces/hyphens → _
        new_col = re.sub(r"[^\w]", "", new_col)               # remove non-word chars
        new_col = re.sub(r"_+", "_", new_col).strip("_")      # collapse underscores
        if new_col != col:
            rename_map[col] = new_col

    if rename_map:
        df = df.rename(columns=rename_map)
        audit.append(f"Renamed {len(rename_map)} column(s): {rename_map}")
    else:
        audit.append("All column names already clean.")

    return df, audit
