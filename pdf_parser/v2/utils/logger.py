import logging
import sys
import json
from pathlib import Path
from datetime import datetime


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }

        if hasattr(record, "payload"):
            log["payload"] = record.payload
        else:
            log["message"] = record.getMessage()

        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)

        return json.dumps(log, indent=2, default=str)



def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # ---------------------------
    # Console (human-readable)
    # ---------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(name)s :: %(message)s")
    )

    # ---------------------------
    # File (JSON)
    # ---------------------------
    file_handler = logging.FileHandler(
        LOG_DIR / "statement_parser.jsonl",
        mode="a",
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
