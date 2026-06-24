"""
Validation layer — file and cleaning-config checks.
"""
from config.settings import Config


def validate_upload(file) -> str | None:
    """Returns an error string or None if valid."""
    if not file or file.filename == "":
        return "No file selected."
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in Config.ALLOWED_EXTENSIONS:
        return f"Unsupported file type '.{ext}'. Allowed: csv, xls, xlsx."
    return None


def validate_clean_config(cfg: dict) -> str | None:
    valid_num   = {"mean", "median", "mode", "drop"}
    valid_out   = {"iqr", "zscore"}
    valid_act   = {"cap", "remove", "keep"}

    if cfg.get("missing_num_strategy") not in valid_num:
        return f"Invalid missing_num_strategy. Choose from {valid_num}."
    if cfg.get("outlier_method") not in valid_out:
        return f"Invalid outlier_method. Choose from {valid_out}."
    if cfg.get("outlier_action") not in valid_act:
        return f"Invalid outlier_action. Choose from {valid_act}."
    return None
