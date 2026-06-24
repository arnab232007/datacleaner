"""
Date standardisation: converts recognised date columns to ISO YYYY-MM-DD strings.
Uses format='mixed' for robust handling of varied date formats (pandas 2+).
"""
import pandas as pd
import re

DATE_KEYWORDS = re.compile(r"date|time|dob|birth|created|updated|timestamp", re.I)


def standardize_dates(df: pd.DataFrame):
    audit = []

    for col in df.columns:
        # Already datetime dtype — just format it
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
            audit.append(f"'{col}': formatted datetime → ISO YYYY-MM-DD.")
            continue

        # String column with a date-like name — try parsing
        is_str = pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object
        if is_str and DATE_KEYWORDS.search(col):
            str_series = df[col].astype(str).where(df[col].notna(), other=None)
            try:
                converted = pd.to_datetime(str_series, errors="coerce", format="mixed")
            except TypeError:
                # Older pandas fallback
                converted = pd.to_datetime(str_series, errors="coerce", infer_datetime_format=True)

            valid_count = converted.notna().sum()
            total_count = df[col].notna().sum()
            if total_count > 0 and (valid_count / total_count) >= 0.60:
                df[col] = converted.dt.strftime("%Y-%m-%d")
                audit.append(f"'{col}': parsed and formatted as ISO YYYY-MM-DD.")

    return df, audit
