"""
Logging setup — writes to logs/app.log and stderr.
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(app):
    log_path = os.path.join(app.config["LOGS_FOLDER"], "app.log")
    os.makedirs(app.config["LOGS_FOLDER"], exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Also configure root logger so service modules can use logging.getLogger(__name__)
    logging.basicConfig(handlers=[file_handler], level=logging.INFO)
    app.logger.info("Logger initialised -> %s", log_path)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
