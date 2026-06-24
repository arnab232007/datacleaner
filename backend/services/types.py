"""
Data type correction:
- Coerces string columns that look numeric to float/int
- Coerces columns whose name contains date-like keywords to datetime
- Compatible with pandas 2 StringDtype
"""
import pandas as pd
import re

DATE_KEYWORDS = re.compile(r"date|time|dob|birth|created|updated|timestamp", re.I)


def _is_string_col(series: pd.Series) -> bool:
    """True for both old 'object' dtype and new pandas 2 StringDtype."""
    return pd.api.types.is_string_dtype(series) or series.dtype == object


def correct_types(df: pd.DataFrame):
    audit = []

    for col in df.columns:
        if not _is_string_col(df[col]):
            continue

        # Convert to plain Python strings for to_numeric / to_datetime
        str_series = df[col].astype(str).where(df[col].notna(), other=None)
        non_null_orig = df[col].notna().sum()

        # ── Try numeric ──────────────────────────────────────────
        converted_num = pd.to_numeric(str_series, errors="coerce")
        non_null_num  = converted_num.notna().sum()
        if non_null_orig > 0 and (non_null_num / non_null_orig) >= 0.80:
            df[col] = converted_num
            audit.append(f"'{col}': converted str → numeric ({non_null_num} values).")
            continue

        # ── Try date (only if name looks date-like) ──────────────
        if DATE_KEYWORDS.search(col):
            converted_dt = pd.to_datetime(str_series, errors="coerce")
            non_null_dt  = converted_dt.notna().sum()
            if non_null_orig > 0 and (non_null_dt / non_null_orig) >= 0.70:
                df[col] = converted_dt
                audit.append(f"'{col}': converted str → datetime ({non_null_dt} values).")

    return df, audit
