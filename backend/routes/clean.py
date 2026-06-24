"""
Routes: /api/clean/<file_id>  /api/status/<job_id>  /api/result/<job_id>
Uses a simple in-memory job store (replace with Redis for multi-process prod).
"""
import os
import threading
from flask import Blueprint, request, current_app
from utils.helpers import make_file_id, success_response, error_response
from utils.validators import validate_clean_config
from services.cleaner import run_pipeline

clean_bp = Blueprint("clean", __name__)

# job_id → { status, progress, step, result, error }
JOBS: dict = {}


def _run_job(app, job_id: str, file_path: str, cfg: dict):
    def progress_cb(step: str, pct: int, stats: dict):
        JOBS[job_id].update({"step": step, "progress": pct, "stats": stats})

    with app.app_context():
        try:
            JOBS[job_id]["status"] = "running"
            result = run_pipeline(file_path, cfg, progress_cb,
                                  app.config["CLEANED_FOLDER"],
                                  app.config["REPORTS_FOLDER"], job_id)
            JOBS[job_id].update({"status": "done", "progress": 100, "result": result})
        except Exception as exc:
            current_app.logger.exception("Pipeline error job %s", job_id)
            JOBS[job_id].update({"status": "error", "error": str(exc)})


@clean_bp.route("/clean/<file_id>", methods=["POST"])
def start_clean(file_id: str):
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    matches = [f for f in os.listdir(upload_dir) if f.startswith(file_id)]
    if not matches:
        return error_response("Uploaded file not found.", 404)

    body = request.get_json(silent=True) or {}
    cfg = {
        "missing_num_strategy":  body.get("missing_num_strategy", "median"),
        "missing_cat_strategy":  body.get("missing_cat_strategy", "mode"),
        "missing_drop_threshold": float(body.get("missing_drop_threshold", 0.6)),
        "outlier_method":        body.get("outlier_method", "iqr"),
        "outlier_action":        body.get("outlier_action", "cap"),
        "zscore_threshold":      float(body.get("zscore_threshold", 3.0)),
        "clean_text":            bool(body.get("clean_text", True)),
        "standardize_dates":     bool(body.get("standardize_dates", True)),
        "clean_col_names":       bool(body.get("clean_col_names", True)),
    }

    err = validate_clean_config(cfg)
    if err:
        return error_response(err)

    job_id   = make_file_id()
    file_path = os.path.join(upload_dir, matches[0])
    JOBS[job_id] = {"status": "queued", "progress": 0, "step": "Queued", "stats": {}, "result": None}

    t = threading.Thread(target=_run_job,
                         args=(current_app._get_current_object(), job_id, file_path, cfg),
                         daemon=True)
    t.start()

    current_app.logger.info("Job %s started for file %s", job_id, file_id)
    return success_response({"job_id": job_id})


@clean_bp.route("/status/<job_id>", methods=["GET"])
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return error_response("Job not found.", 404)
    return success_response({
        "status":   job["status"],
        "progress": job["progress"],
        "step":     job["step"],
        "stats":    job["stats"],
        "error":    job.get("error"),
    })


@clean_bp.route("/result/<job_id>", methods=["GET"])
def job_result(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return error_response("Job not found.", 404)
    if job["status"] != "done":
        return error_response("Job not complete yet.", 202)
    return success_response({"result": job["result"]})
