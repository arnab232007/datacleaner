"""
Cleaning pipeline orchestrator.
Calls each service in sequence, tracks progress, returns a full summary dict.
"""
import os
import pandas as pd
from services.missing   import handle_missing
from services.dedup     import remove_duplicates
from services.types     import correct_types
from services.outliers  import handle_outliers
from services.text      import standardize_text
from services.dates     import standardize_dates
from services.colnames  import clean_column_names
from services.report    import generate_reports


def run_pipeline(file_path: str, cfg: dict,
                 progress_cb, cleaned_dir: str, reports_dir: str,
                 job_id: str) -> dict:
    """
    Runs all cleaning stages and writes output files.
    Returns a summary dict consumed by /api/result.
    """
    # ── 1. Load ──────────────────────────────────────────────────────────────
    progress_cb("Loading file", 5, {})
    ext = file_path.rsplit(".", 1)[-1].lower()
    df_raw = pd.read_csv(file_path, low_memory=False) if ext == "csv" \
             else pd.read_excel(file_path)
    original_shape = df_raw.shape
    df = df_raw.copy()
    audit = []

    # ── 2. Column name cleaning ──────────────────────────────────────────────
    progress_cb("Cleaning column names", 12, {})
    if cfg["clean_col_names"]:
        df, col_audit = clean_column_names(df)
        audit.extend(col_audit)

    # ── 3. Type correction ───────────────────────────────────────────────────
    progress_cb("Correcting data types", 22, {})
    df, type_audit = correct_types(df)
    audit.extend(type_audit)

    # ── 4. Missing value handling ────────────────────────────────────────────
    progress_cb("Handling missing values", 35, {})
    df, missing_audit, missing_stats = handle_missing(
        df, cfg["missing_num_strategy"], cfg["missing_cat_strategy"],
        cfg["missing_drop_threshold"]
    )
    audit.extend(missing_audit)

    # ── 5. Deduplication ────────────────────────────────────────────────────
    progress_cb("Removing duplicates", 48, {})
    df, dup_audit, dup_count = remove_duplicates(df)
    audit.extend(dup_audit)

    # ── 6. Outlier handling ──────────────────────────────────────────────────
    progress_cb("Detecting outliers", 60, {})
    df, outlier_audit, outlier_stats = handle_outliers(
        df, cfg["outlier_method"], cfg["outlier_action"],
        cfg.get("zscore_threshold", 3.0)
    )
    audit.extend(outlier_audit)

    # ── 7. Text standardisation ──────────────────────────────────────────────
    progress_cb("Standardising text", 72, {})
    if cfg["clean_text"]:
        df, text_audit = standardize_text(df)
        audit.extend(text_audit)

    # ── 8. Date standardisation ──────────────────────────────────────────────
    progress_cb("Standardising dates", 83, {})
    if cfg["standardize_dates"]:
        df, date_audit = standardize_dates(df)
        audit.extend(date_audit)

    # ── 9. Write output files ────────────────────────────────────────────────
    progress_cb("Writing output files", 90, {})
    csv_path  = os.path.join(cleaned_dir,  f"{job_id}.csv")
    xlsx_path = os.path.join(cleaned_dir,  f"{job_id}.xlsx")
    df.to_csv(csv_path,    index=False)
    df.to_excel(xlsx_path, index=False)

    # ── 10. Generate reports ─────────────────────────────────────────────────
    progress_cb("Generating reports", 95, {})
    summary = {
        "original_rows":      int(original_shape[0]),
        "original_cols":      int(original_shape[1]),
        "cleaned_rows":       int(len(df)),
        "cleaned_cols":       int(len(df.columns)),
        "removed_rows":       int(original_shape[0] - len(df)),
        "nulls_fixed":        int(missing_stats.get("total_filled", 0)),
        "cols_dropped":       int(missing_stats.get("cols_dropped", 0)),
        "duplicates_removed": int(dup_count),
        "outliers_handled":   int(outlier_stats.get("total", 0)),
        "audit_log":          audit,
        "missing_stats":      {k: int(v) if hasattr(v, 'item') else v
                               for k, v in missing_stats.items()},
        "outlier_stats":      {k: int(v) if hasattr(v, 'item') else v
                               for k, v in outlier_stats.items()},
    }
    generate_reports(df_raw, df, summary, job_id, reports_dir)

    progress_cb("Complete", 100, summary)
    return summary
