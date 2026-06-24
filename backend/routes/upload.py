"""
Routes: /api/upload  and  /api/preview/<file_id>
"""
import os
from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file, make_file_id, human_size, success_response, error_response
from utils.validators import validate_upload
import pandas as pd

upload_bp = Blueprint("upload", __name__)


def _read_df(path: str) -> pd.DataFrame:
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        return pd.read_csv(path, low_memory=False)
    return pd.read_excel(path)


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    err = validate_upload(file)
    if err:
        return error_response(err)

    file_id  = make_file_id()
    filename = secure_filename(file.filename)
    ext      = filename.rsplit(".", 1)[-1].lower()
    save_name = f"{file_id}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], save_name)
    file.save(save_path)

    size_bytes = os.path.getsize(save_path)

    try:
        df = _read_df(save_path)
    except Exception as exc:
        os.remove(save_path)
        return error_response(f"Could not parse file: {exc}")

    current_app.logger.info("Uploaded %s → %s (%d rows)", filename, file_id, len(df))

    return success_response({
        "file_id":  file_id,
        "filename": filename,
        "size":     human_size(size_bytes),
        "rows":     len(df),
        "columns":  len(df.columns),
        "col_names": df.columns.tolist(),
        "dtypes":   {col: str(dt) for col, dt in df.dtypes.items()},
    })


@upload_bp.route("/preview/<file_id>", methods=["GET"])
def preview_file(file_id: str):
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    matches = [f for f in os.listdir(upload_dir) if f.startswith(file_id)]
    if not matches:
        return error_response("File not found.", 404)

    path = os.path.join(upload_dir, matches[0])
    try:
        df = _read_df(path)
        preview = df.head(20).fillna("").astype(str)
        return success_response({
            "columns": df.columns.tolist(),
            "rows":    preview.values.tolist(),
            "total_rows": len(df),
        })
    except Exception as exc:
        return error_response(str(exc))
