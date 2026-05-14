# main.py
# ─────────────────────────────────────────────
#  DEM – Data Encryption Module
#  Entry point. Run this file to start DEM.
#  Command:  python main.py
# ─────────────────────────────────────────────

import sys
import os

# Make sure Python can find all our packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.db import initialize_db
from gui.login_window import LoginWindow
from gui.main_window import MainWindow


def on_login_success(username: str, role: str):
    """Called by the login window after a successful login."""
    MainWindow().mainloop()


def main():
    # Step 1: Set up the database (creates tables + default admin on first run)
    initialize_db()

    # Step 2: Show login window
    LoginWindow(on_login_success).mainloop()


if __name__ == "__main__":
    main()
