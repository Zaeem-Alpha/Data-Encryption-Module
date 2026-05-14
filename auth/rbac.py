# auth/rbac.py
# Simple role-based access checks used by the GUI and CLI.

from auth.login import get_session, is_logged_in, is_admin


def require_login() -> tuple:
    """Returns (True, session_dict) or (False, error_message)."""
    if not is_logged_in():
        return False, "You are not logged in."
    return True, get_session()


def require_admin() -> tuple:
    """Returns (True, session_dict) or (False, error_message)."""
    ok, result = require_login()
    if not ok:
        return False, result
    if result.get('role') != 'admin':
        return False, "Admin access required for this action."
    return True, result


def can_access_file(file_owner: str) -> bool:
    """
    Returns True if the current user may access this file.
    Admins can access everything. Users only their own files.
    """
    s = get_session()
    if not s:
        return False
    return s['role'] == 'admin' or s['username'] == file_owner
