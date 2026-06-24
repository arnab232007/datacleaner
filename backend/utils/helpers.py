"""
Shared utilities: file helpers, cleanup thread, safe JSON responses.
"""
import os
import time
import uuid
import threading
from pathlib import Path
from flask import jsonify
from config.settings import Config


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


def make_file_id() -> str:
    return uuid.uuid4().hex


def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def success_response(data: dict, status: int = 200):
    return jsonify({"ok": True, **data}), status


def error_response(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _cleanup_old_files(app):
    """Delete files older than FILE_TTL_SECONDS from upload/output folders."""
    folders = [Config.UPLOAD_FOLDER, Config.CLEANED_FOLDER, Config.REPORTS_FOLDER]
    now = time.time()
    removed = 0
    for folder in folders:
        for f in Path(folder).glob("*"):
            if f.is_file() and (now - f.stat().st_mtime) > Config.FILE_TTL_SECONDS:
                try:
                    f.unlink()
                    removed += 1
                except OSError:
                    pass
    if removed:
        app.logger.info("Cleanup: removed %d stale files", removed)


def start_cleanup_thread(app):
    def run():
        while True:
            time.sleep(600)  # run every 10 minutes
            with app.app_context():
                _cleanup_old_files(app)

    t = threading.Thread(target=run, daemon=True)
    t.start()
