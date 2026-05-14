# gui/tabs/files_tab.py
# Shows the current user's encrypted file registry.
# Users can only see their own files, never other people's.

import os
import customtkinter as ctk
from storage.db import get_user_files
from auth.login import get_username


class FilesTab(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="My Encrypted Files",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="These are the files you have encrypted. Only you can see this list.",
            text_color="gray"
        ).pack(pady=(0, 10))

        self._box = ctk.CTkTextbox(
            self, state="disabled",
            font=ctk.CTkFont(family="Courier New", size=12)
        )
        self._box.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        ctk.CTkButton(self, text="↻  Refresh", width=120, command=self._refresh).pack(pady=6)

        self._status = ctk.CTkLabel(self, text="", text_color="gray")
        self._status.pack()

    def _refresh(self):
        username = get_username()
        files = get_user_files(username)

        self._box.configure(state="normal")
        self._box.delete("1.0", "end")

        if not files:
            self._box.insert("end", "You have no encrypted files yet.\n\n")
            self._box.insert("end", "Go to the  Encrypt  tab to encrypt your first file.")
        else:
            self._box.insert("end", f"{'FILENAME':<35} {'SIZE':>10}  ENCRYPTED AT\n")
            self._box.insert("end", "─" * 65 + "\n")
            for filename, enc_path, size, created_at in files:
                size_str = f"{size / 1024:.1f} KB" if size else "?"
                exists = "✅" if os.path.exists(enc_path) else "⚠ missing"
                self._box.insert(
                    "end",
                    f"{filename:<35} {size_str:>10}  {created_at[:19]}  {exists}\n"
                )

        self._box.configure(state="disabled")
        total = len(files)
        self._status.configure(text=f"{total} file(s) registered." if total else "")
