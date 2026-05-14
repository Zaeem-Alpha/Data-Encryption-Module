# auth/login.py
# Manages the logged-in session.
# A session token is written to a temp file when the user logs in.
# It is deleted automatically when the process exits.

import json
import os
import tempfile
import atexit
import secrets
from datetime import datetime


def _session_path() -> str:
    """Each process has its own session file (identified by PID)."""
    return os.path.join(tempfile.gettempdir(), f'dem_session_{os.getpid()}.json')


def login(username: str, role: str) -> str:
    """
    Create a session for the given user.
    Returns the session token.
    The session lasts until the terminal/process is closed.
    """
    token = secrets.token_hex(32)
    session = {
        'username': username,
        'role': role,
        'token': token,
        'created_at': datetime.now().isoformat(),
    }
    path = _session_path()
    with open(path, 'w') as f:
        json.dump(session, f)

    # Auto-cleanup when Python exits
    atexit.register(logout)
    return token


def logout():
    """Delete the session file."""
    path = _session_path()
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def get_session() -> dict | None:
    """Return the current session dict, or None if not logged in."""
    path = _session_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def is_logged_in() -> bool:
    return get_session() is not None


def get_username() -> str | None:
    s = get_session()
    return s['username'] if s else None


def get_role() -> str | None:
    s = get_session()
    return s['role'] if s else None


def is_admin() -> bool:
    return get_role() == 'admin'
