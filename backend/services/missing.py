"""
Missing value handling:
- Drops columns with > threshold null ratio
- Imputes numeric columns with mean / median / mode
- Imputes categorical columns with mode
"""
import pandas as pd
import numpy as np


def handle_missing(df: pd.DataFrame, num_strategy: str,
                   cat_strategy: str, drop_threshold: float):
    audit = []
    stats = {"total_filled": 0, "cols_dropped": 0, "by_column": {}}

    # 1. Drop columns with excessive nulls
    null_ratio = df.isnull().mean()
    cols_to_drop = null_ratio[null_ratio > drop_threshold].index.tolist()
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        stats["cols_dropped"] = len(cols_to_drop)
        audit.append(f"Dropped {len(cols_to_drop)} column(s) with >{drop_threshold*100:.0f}% nulls: {cols_to_drop}")

    # 2. Impute remaining columns
    for col in df.columns:
        null_count = df[col].isnull().sum()
        if null_count == 0:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            if num_strategy == "mean":
                fill_val = df[col].mean()
            elif num_strategy == "median":
                fill_val = df[col].median()
            elif num_strategy == "mode":
                mode = df[col].mode()
                fill_val = mode.iloc[0] if not mode.empty else 0
            else:  # "drop"
                df = df.dropna(subset=[col])
                audit.append(f"'{col}': dropped {null_count} rows with null values")
                continue

            df[col] = df[col].fillna(fill_val)
            audit.append(f"'{col}': filled {null_count} nulls with {num_strategy} ({fill_val:.4g})")

        else:  # categorical / object
            mode = df[col].mode()
            if not mode.empty:
                fill_val = mode.iloc[0]
                df[col] = df[col].fillna(fill_val)
                audit.append(f"'{col}': filled {null_count} nulls with mode ('{fill_val}')")
            else:
                df[col] = df[col].fillna("unknown")
                audit.append(f"'{col}': filled {null_count} nulls with 'unknown'")

        stats["total_filled"] += null_count
        stats["by_column"][col] = int(null_count)

    return df, audit, stats
