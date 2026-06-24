"""
Routes: /api/download/<job_id>/<fmt>  and  /api/report/<job_id>/<fmt>
"""
import os
from flask import Blueprint, send_file, current_app
from utils.helpers import error_response
from routes.clean import JOBS

download_bp = Blueprint("download", __name__)


def _find_file(folder: str, prefix: str, exts: list[str]) -> str | None:
    for f in os.listdir(folder):
        if f.startswith(prefix):
            if any(f.endswith(e) for e in exts):
                return os.path.join(folder, f)
    return None


@download_bp.route("/download/<job_id>/<fmt>", methods=["GET"])
def download_cleaned(job_id: str, fmt: str):
    if fmt not in ("csv", "xlsx"):
        return error_response("fmt must be csv or xlsx.")

    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        return error_response("Job not ready.", 404)

    folder = current_app.config["CLEANED_FOLDER"]
    path = _find_file(folder, job_id, [f".{fmt}"])
    if not path:
        return error_response("Output file not found.", 404)

    return send_file(path, as_attachment=True,
                     download_name=f"cleaned_{job_id[:8]}.{fmt}")


@download_bp.route("/report/<job_id>/<fmt>", methods=["GET"])
def download_report(job_id: str, fmt: str):
    if fmt not in ("pdf", "html"):
        return error_response("fmt must be pdf or html.")

    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        return error_response("Job not ready.", 404)

    folder = current_app.config["REPORTS_FOLDER"]
    path = _find_file(folder, job_id, [f".{fmt}"])
    if not path:
        return error_response("Report not found.", 404)

    mime = "application/pdf" if fmt == "pdf" else "text/html"
    return send_file(path, mimetype=mime, as_attachment=(fmt == "pdf"),
                     download_name=f"report_{job_id[:8]}.{fmt}")
