# gui/main_window.py
# Main application window shown after a successful login.
# Admin gets 6 tabs. Regular users get 5 tabs (no Admin Panel).

import customtkinter as ctk
from auth.login import get_username, get_role, logout
from gui.tabs.encrypt_tab import EncryptTab
from gui.tabs.decrypt_tab import DecryptTab
from gui.tabs.watch_tab import WatchTab
from gui.tabs.files_tab import FilesTab
from gui.tabs.account_tab import AccountTab
from gui.tabs.admin_tab import AdminTab


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        username = get_username()
        role = get_role()

        self.title(f"DEM – Data Encryption Module   |   {username}  ({role})")
        self.geometry("750x640")
        self.minsize(700, 580)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_ui(username, role)
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 750) // 2
        y = (self.winfo_screenheight() - 640) // 2
        self.geometry(f"750x640+{x}+{y}")

    def _build_ui(self, username: str, role: str):
        # ── Top bar ───────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, height=44, corner_radius=0)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        ctk.CTkLabel(
            top,
            text="DEM - Data Encryption Module",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=16)

        ctk.CTkButton(
            top, text="Logout", width=80, height=28,
            fg_color="gray30", hover_color="gray20",
            command=self._logout
        ).pack(side="right", padx=12, pady=7)

        role_color = "#FFD700" if role == "admin" else "#90CAF9"
        ctk.CTkLabel(
            top,
            text=f"  {username}  [{role}]",
            text_color=role_color,
            font=ctk.CTkFont(size=13)
        ).pack(side="right", padx=6)

        # ── Tab view ──────────────────────────────────────────────────────
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=8)

        tabs.add("Encrypt")
        tabs.add("Decrypt")
        tabs.add("My Files")
        tabs.add("Watchdog")
        tabs.add("My Account")   # <-- new tab for all users

        EncryptTab(tabs.tab("Encrypt")).pack(fill="both", expand=True)
        DecryptTab(tabs.tab("Decrypt")).pack(fill="both", expand=True)
        FilesTab(tabs.tab("My Files")).pack(fill="both", expand=True)
        WatchTab(tabs.tab("Watchdog")).pack(fill="both", expand=True)
        AccountTab(tabs.tab("My Account")).pack(fill="both", expand=True)

        # Admin Panel — only for admins
        if role == "admin":
            tabs.add("Admin")
            AdminTab(tabs.tab("Admin")).pack(fill="both", expand=True)

    def _logout(self):
        logout()
        self.destroy()
        from gui.login_window import LoginWindow

        def on_login(username, role):
            MainWindow().mainloop()

        LoginWindow(on_login).mainloop()
