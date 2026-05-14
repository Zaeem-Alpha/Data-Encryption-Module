# storage/db.py
# Handles all database operations: users, roles, and file registry.
# We store only the PATH of encrypted files, never a copy of the data.

import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

# Database lives in the project root folder
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BASE_DIR, 'dem_database.db')


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def initialize_db():
    """
    Create all tables on first run.
    Also creates the default admin account if no users exist yet.
    """
    conn = _connect()
    cur = conn.cursor()

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT    UNIQUE NOT NULL,
            password_hash TEXT   NOT NULL,
            salt         TEXT    NOT NULL,
            role         TEXT    NOT NULL DEFAULT 'user',
            created_at   TEXT    NOT NULL
        )
    ''')

    # File registry table - stores path only, never the encrypted data itself
    cur.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            owner             TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            original_path     TEXT,
            encrypted_path    TEXT NOT NULL,
            file_size         INTEGER,
            created_at        TEXT NOT NULL
        )
    ''')

    conn.commit()

    # Create default admin if the users table is empty
    cur.execute('SELECT COUNT(*) FROM users')
    if cur.fetchone()[0] == 0:
        _create_user_internal(conn, 'admin', 'admin123', 'admin')
        print("=" * 50)
        print("[DEM] First run detected.")
        print("[DEM] Default admin account created.")
        print("[DEM]   Username : admin")
        print("[DEM]   Password : admin123")
        print("[DEM] Please change this password after logging in!")
        print("=" * 50)

    conn.close()


# ── Password hashing ──────────────────────────────────────────────────────────

def _hash_password(password: str, salt: str) -> str:
    """Hash a password with a salt using PBKDF2-SHA256."""
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        260_000
    ).hex()


# ── User management ───────────────────────────────────────────────────────────

def _create_user_internal(conn: sqlite3.Connection, username: str, password: str, role: str) -> bool:
    """Internal helper - create user with given connection."""
    salt = secrets.token_hex(32)
    pw_hash = _hash_password(password, salt)
    try:
        conn.execute(
            'INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?)',
            (username, pw_hash, salt, role, datetime.now().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def verify_user(username: str, password: str) -> tuple:
    """
    Check login credentials.
    Returns (True, role) if correct, (False, None) if wrong.
    """
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT password_hash, salt, role FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False, None

    pw_hash, salt, role = row
    if _hash_password(password, salt) == pw_hash:
        return True, role
    return False, None


def add_user(username: str, password: str, role: str = 'user') -> tuple:
    """
    Admin action: add a new user.
    Returns (True, '') on success or (False, error_message) on failure.
    """
    if not username.strip():
        return False, "Username cannot be empty."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if role not in ('user', 'admin'):
        return False, "Role must be 'user' or 'admin'."

    conn = _connect()
    ok = _create_user_internal(conn, username.strip(), password, role)
    conn.close()

    if ok:
        return True, ''
    return False, f"Username '{username}' already exists."


def delete_user(username: str) -> tuple:
    """
    Admin action: delete a user.
    Returns (True, '') or (False, error_message).
    """
    if username == 'admin':
        return False, "The default 'admin' account cannot be deleted."

    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE username = ?', (username,))
    if not cur.fetchone():
        conn.close()
        return False, f"User '{username}' does not exist."

    conn.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()
    return True, ''


def change_password(username: str, new_password: str) -> tuple:
    """Change a user's password. Returns (True, '') or (False, error)."""
    if len(new_password) < 4:
        return False, "Password must be at least 4 characters."
    salt = secrets.token_hex(32)
    pw_hash = _hash_password(new_password, salt)
    conn = _connect()
    conn.execute(
        'UPDATE users SET password_hash = ?, salt = ? WHERE username = ?',
        (pw_hash, salt, username)
    )
    conn.commit()
    conn.close()
    return True, ''


def list_users() -> list:
    """Return list of (username, role, created_at) for all users."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT username, role, created_at FROM users ORDER BY created_at')
    rows = cur.fetchall()
    conn.close()
    return rows


def user_exists(username: str) -> bool:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE username = ?', (username,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


# ── File registry ─────────────────────────────────────────────────────────────

def register_file(
    owner: str,
    original_filename: str,
    original_path: str,
    encrypted_path: str,
    file_size: int
):
    """
    Record a newly encrypted file in the registry.
    We store only the path, never the file content itself.
    """
    conn = _connect()
    conn.execute(
        '''INSERT INTO files
           (owner, original_filename, original_path, encrypted_path, file_size, created_at)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (owner, original_filename, original_path, encrypted_path, file_size,
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_user_files(username: str) -> list:
    """Return all files owned by a specific user."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        'SELECT original_filename, encrypted_path, file_size, created_at FROM files WHERE owner = ? ORDER BY created_at DESC',
        (username,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_files() -> list:
    """Admin only: return all files from all users."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        'SELECT owner, original_filename, encrypted_path, file_size, created_at FROM files ORDER BY created_at DESC'
    )
    rows = cur.fetchall()
    conn.close()
    return rows
