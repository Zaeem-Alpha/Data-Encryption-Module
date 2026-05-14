# storage/logger.py
# Writes a timestamped audit log for every encrypt/decrypt/admin action.

import os
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(_BASE_DIR, 'dem_audit.log')


def log(user: str, operation: str, target: str, status: str, detail: str = ''):
    """
    Append one line to the audit log.
    Example:
      [2025-01-01 12:00:00] USER=zaeem | OP=ENCRYPT | FILE=photo.jpg | STATUS=SUCCESS
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] USER={user} | OP={operation} | FILE={target} | STATUS={status}"
    if detail:
        line += f" | DETAIL={detail}"
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def get_logs(last_n: int = 200) -> list:
    """Return the last N lines from the audit log."""
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines[-last_n:]
