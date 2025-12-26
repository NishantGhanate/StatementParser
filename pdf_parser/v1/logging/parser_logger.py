import json
import os
from datetime import datetime
from threading import Lock
from decimal import Decimal

_LOG_FILE = os.getenv("PARSER_LOG_FILE")
_LOCK = Lock()


def _json_safe(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, list):
        return [_json_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    return obj


def _write_to_file(record: dict):
    if not _LOG_FILE:
        return

    try:
        os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
        with _LOCK, open(_LOG_FILE, "a", encoding="utf-8") as f:
            # FILE = vertical / readable JSON
            f.write(json.dumps(record, ensure_ascii=False, indent=2))
            f.write("\n\n")  # separator between records
    except Exception:
        pass  # logging must NEVER break parsing


def _print_pretty(record: dict):
    # STDOUT = vertical / readable JSON
    print(json.dumps(record, ensure_ascii=False, indent=2))


def log_row(stage: str, payload: dict):
    record = {
        "ts": datetime.utcnow().isoformat(),
        "stage": stage,
        **payload,
    }

    safe = _json_safe(record)

    _print_pretty(safe)
    _write_to_file(safe)


def log_output(status: str, transactions: list[dict], meta: dict):
    record = {
        "ts": datetime.utcnow().isoformat(),
        "stage": "output",
        "status": status,
        "meta": meta,
        "transactions": transactions,
    }

    safe = _json_safe(record)

    _print_pretty(safe)
    _write_to_file(safe)
