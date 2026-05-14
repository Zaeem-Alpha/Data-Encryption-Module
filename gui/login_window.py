# gui/login_window.py
# The first window shown when DEM starts.
# Asks for username and password, then calls on_success(username, role).

import customtkinter as ctk
from storage.db import verify_user
from auth.login import login


class LoginWindow(ctk.CTk):

    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success  # function to call after successful login

        self.title("DEM – Data Encryption Module")
        self.geometry("420x380")
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 420) // 2
        y = (self.winfo_screenheight() - 380) // 2
        self.geometry(f"420x380+{x}+{y}")

    def _build_ui(self):
        # ── Logo / title area ─────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="🔐  DEM",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(pady=(35, 5))

        ctk.CTkLabel(
            self, text="Data Encryption Module",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack()

        ctk.CTkLabel(
            self, text="──────────────────────────",
            text_color="gray30"
        ).pack(pady=10)

        # ── Username ──────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Username", anchor="w").pack(fill="x", padx=60)
        self._username = ctk.CTkEntry(self, width=300, placeholder_text="Enter username")
        self._username.pack(pady=(2, 10))
        self._username.bind("<Return>", lambda e: self._password_entry.focus())

        # ── Password ──────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Password", anchor="w").pack(fill="x", padx=60)
        self._password_entry = ctk.CTkEntry(self, width=300, show="*", placeholder_text="Enter password")
        self._password_entry.pack(pady=(2, 5))
        self._password_entry.bind("<Return>", lambda e: self._do_login())

        # ── Error message ─────────────────────────────────────────────────
        self._error = ctk.CTkLabel(self, text="", text_color="#FF6B6B")
        self._error.pack(pady=5)

        # ── Login button ──────────────────────────────────────────────────
        ctk.CTkButton(
            self, text="Login", width=300,
            command=self._do_login,
            font=ctk.CTkFont(size=14)
        ).pack(pady=5)

        # Focus username on start
        self._username.focus()

    def _do_login(self):
        username = self._username.get().strip()
        password = self._password_entry.get()

        if not username:
            self._error.configure(text="Please enter your username.")
            return
        if not password:
            self._error.configure(text="Please enter your password.")
            return

        valid, role = verify_user(username, password)
        if valid:
            login(username, role)
            self.destroy()
            self.on_success(username, role)
        else:
            self._error.configure(text="Wrong username or password. Try again.")
            self._password_entry.delete(0, "end")
            self._password_entry.focus()
