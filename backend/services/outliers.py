"""
Outlier handling: IQR method or Z-score method.
Actions: cap (winsorise) | remove | keep
"""
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats


def _iqr_bounds(series: pd.Series):
    Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
    IQR = Q3 - Q1
    return Q1 - 1.5 * IQR, Q3 + 1.5 * IQR


def handle_outliers(df: pd.DataFrame, method: str, action: str, zscore_thresh: float):
    audit = []
    stats = {"total": 0, "by_column": {}}

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    for col in num_cols:
        series = df[col].dropna().astype(float)
        if len(series) < 4:
            continue

        if method == "iqr":
            lo, hi = _iqr_bounds(series)
        else:  # zscore
            z = np.abs(scipy_stats.zscore(series))
            lo = series[z <= zscore_thresh].min()
            hi = series[z <= zscore_thresh].max()

        outlier_mask = (df[col] < lo) | (df[col] > hi)
        count = int(outlier_mask.sum())
        if count == 0:
            continue

        stats["total"] += count
        stats["by_column"][col] = count

        if action == "cap":
            df[col] = df[col].clip(lower=lo, upper=hi)
            audit.append(f"'{col}': capped {count} outlier(s) to [{lo:.4g}, {hi:.4g}].")
        elif action == "remove":
            df = df[~outlier_mask]
            audit.append(f"'{col}': removed {count} row(s) with outliers.")
        else:
            audit.append(f"'{col}': {count} outlier(s) detected but kept (action=keep).")

    if not audit:
        audit.append("No significant outliers detected.")

    return df, audit, stats
