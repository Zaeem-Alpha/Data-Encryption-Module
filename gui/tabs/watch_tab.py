# gui/tabs/watch_tab.py
# Tab for the folder watchdog.
# User sets a watch folder, output folder, and one folder-level password.
# Any file dropped into the watch folder is auto-encrypted.

import os
import customtkinter as ctk
from tkinter import filedialog
from watchdog_monitor.watcher import FolderWatcher
from auth.login import get_username


class WatchTab(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._watcher = None
        self._build_ui()

    def _build_ui(self):
        # ── Title ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Folder Watchdog",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="Drop any file into the watched folder and it will be encrypted automatically.",
            text_color="gray", wraplength=550
        ).pack(pady=(0, 10))

        # ── Watch folder ──────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Watch this folder:", anchor="w").pack(fill="x", padx=20)

        wf_row = ctk.CTkFrame(self, fg_color="transparent")
        wf_row.pack(fill="x", padx=20, pady=4)

        self._watch_var = ctk.StringVar()
        ctk.CTkEntry(wf_row, textvariable=self._watch_var,
                     placeholder_text="Folder to monitor for new files").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(wf_row, text="Browse", width=85,
                      command=self._browse_watch).pack(side="left", padx=(8, 0))

        # ── Output folder ─────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Save encrypted files to:", anchor="w").pack(fill="x", padx=20)

        of_row = ctk.CTkFrame(self, fg_color="transparent")
        of_row.pack(fill="x", padx=20, pady=4)

        self._out_var = ctk.StringVar()
        ctk.CTkEntry(of_row, textvariable=self._out_var,
                     placeholder_text="Output folder for .dem files").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(of_row, text="Browse", width=85,
                      command=self._browse_out).pack(side="left", padx=(8, 0))

        # ── Folder password ───────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Folder password (used for all files auto-encrypted by watchdog):",
            anchor="w"
        ).pack(fill="x", padx=20)

        pw_row = ctk.CTkFrame(self, fg_color="transparent")
        pw_row.pack(fill="x", padx=20, pady=4)

        self._pw_var = ctk.StringVar()
        self._pw_entry = ctk.CTkEntry(pw_row, textvariable=self._pw_var,
                                      show="*", placeholder_text="Enter folder-level password")
        self._pw_entry.pack(side="left", fill="x", expand=True)

        self._show_pw = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(pw_row, text="Show", variable=self._show_pw,
                        command=self._toggle_pw).pack(side="left", padx=(8, 0))

        # ── Status indicator + toggle button ──────────────────────────────
        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.pack(pady=10)

        self._indicator = ctk.CTkLabel(
            status_row, text="■  Stopped",
            text_color="#FF6B6B",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self._indicator.pack(side="left", padx=(0, 20))

        self._toggle_btn = ctk.CTkButton(
            status_row, text="▶  Start Watching", width=180,
            font=ctk.CTkFont(size=13),
            command=self._toggle
        )
        self._toggle_btn.pack(side="left")

        # ── Activity log ──────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Activity log:", anchor="w").pack(fill="x", padx=20)

        self._log_box = ctk.CTkTextbox(self, height=160, state="disabled")
        self._log_box.pack(fill="x", padx=20, pady=(4, 15))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _browse_watch(self):
        folder = filedialog.askdirectory(title="Select folder to watch")
        if folder:
            self._watch_var.set(folder)

    def _browse_out(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self._out_var.set(folder)

    def _toggle_pw(self):
        self._pw_entry.configure(show="" if self._show_pw.get() else "*")

    def _append_log(self, message: str):
        """Thread-safe log append (called from watchdog thread via callback)."""
        self._log_box.configure(state="normal")
        self._log_box.insert("end", message + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    # ── Watchdog control ──────────────────────────────────────────────────

    def _toggle(self):
        if self._watcher and self._watcher.is_running():
            self._stop()
        else:
            self._start()

    def _start(self):
        watch_folder = self._watch_var.get().strip()
        out_folder   = self._out_var.get().strip()
        password     = self._pw_var.get()

        if not watch_folder:
            self._append_log("❌ Please choose a folder to watch.")
            return
        if not out_folder:
            self._append_log("❌ Please choose an output folder.")
            return
        if not password:
            self._append_log("❌ Please enter a folder password.")
            return
        if not os.path.isdir(watch_folder):
            self._append_log(f"❌ Folder not found: {watch_folder}")
            return

        self._watcher = FolderWatcher(
            watch_folder, out_folder, password,
            get_username(),
            status_callback=self._append_log
        )
        self._watcher.start()

        self._indicator.configure(text="●  Watching", text_color="#4CAF50")
        self._toggle_btn.configure(text="■  Stop Watching")

    def _stop(self):
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

        self._indicator.configure(text="■  Stopped", text_color="#FF6B6B")
        self._toggle_btn.configure(text="▶  Start Watching")
