"""
Configuration settings — loaded from .env in production.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY         = os.getenv("SECRET_KEY", "dev-secret-change-me")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024          # 50 MB upload limit

    UPLOAD_FOLDER      = str(BASE_DIR / "uploads")
    CLEANED_FOLDER     = str(BASE_DIR / "cleaned_files")
    REPORTS_FOLDER     = str(BASE_DIR / "reports")
    LOGS_FOLDER        = str(BASE_DIR / "logs")

    ALLOWED_EXTENSIONS = {"csv", "xls", "xlsx"}
    FILE_TTL_SECONDS   = 3600                       # auto-delete after 1 hour

    # Cleaning defaults
    MISSING_NUM_STRATEGY  = "median"                # mean | median | mode
    MISSING_CAT_STRATEGY  = "mode"
    MISSING_DROP_THRESHOLD = 0.6                    # drop col if >60 % null
    OUTLIER_METHOD        = "iqr"                   # iqr | zscore
    OUTLIER_ACTION        = "cap"                   # cap | remove | keep
    ZSCORE_THRESHOLD      = 3.0
