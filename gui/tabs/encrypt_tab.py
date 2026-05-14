# gui/tabs/encrypt_tab.py
# Tab where users select files, enter a password, and encrypt them.
# Supports multiple files at once. Shows a progress bar for large files.

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.crypto import encrypt_file
from storage.db import register_file
from storage.logger import log
from auth.login import get_username


class EncryptTab(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_files = []
        self._build_ui()

    def _build_ui(self):
        # ── Title ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Encrypt Files",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self, text="Select one or more files of any type and format to encrypt.",
            text_color="gray"
        ).pack(pady=(0, 10))

        # ── File selection ────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Files to encrypt:", anchor="w").pack(fill="x", padx=20)

        file_row = ctk.CTkFrame(self, fg_color="transparent")
        file_row.pack(fill="x", padx=20, pady=4)

        self._file_box = ctk.CTkTextbox(file_row, height=90, state="disabled")
        self._file_box.pack(side="left", fill="x", expand=True)

        btn_col = ctk.CTkFrame(file_row, fg_color="transparent")
        btn_col.pack(side="left", padx=(8, 0))
        ctk.CTkButton(btn_col, text="Browse", width=85, command=self._browse_files).pack(pady=2)
        ctk.CTkButton(btn_col, text="Clear",  width=85, command=self._clear_files,
                      fg_color="gray30", hover_color="gray20").pack(pady=2)

        # ── Output folder ─────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Save encrypted files to:", anchor="w").pack(fill="x", padx=20)

        out_row = ctk.CTkFrame(self, fg_color="transparent")
        out_row.pack(fill="x", padx=20, pady=4)

        self._out_var = ctk.StringVar()
        ctk.CTkEntry(out_row, textvariable=self._out_var,
                     placeholder_text="Choose output folder...").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(out_row, text="Browse", width=85,
                      command=self._browse_output).pack(side="left", padx=(8, 0))

        # ── Password ──────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Encryption password:", anchor="w").pack(fill="x", padx=20)

        pw_row = ctk.CTkFrame(self, fg_color="transparent")
        pw_row.pack(fill="x", padx=20, pady=4)

        self._pw_var = ctk.StringVar()
        self._pw_entry = ctk.CTkEntry(pw_row, textvariable=self._pw_var,
                                      show="*", placeholder_text="Enter a strong password")
        self._pw_entry.pack(side="left", fill="x", expand=True)

        self._show_pw = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(pw_row, text="Show", variable=self._show_pw,
                        command=self._toggle_pw).pack(side="left", padx=(8, 0))

        # ── Progress bar ──────────────────────────────────────────────────
        self._progress = ctk.CTkProgressBar(self)
        self._progress.pack(fill="x", padx=20, pady=(10, 2))
        self._progress.set(0)

        # ── Status label ──────────────────────────────────────────────────
        self._status = ctk.CTkLabel(self, text="", wraplength=550)
        self._status.pack(pady=4)

        # ── Encrypt button ────────────────────────────────────────────────
        self._enc_btn = ctk.CTkButton(
            self, text="  🔒  Encrypt", width=220,
            font=ctk.CTkFont(size=14),
            command=self._start_encrypt
        )
        self._enc_btn.pack(pady=10)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _browse_files(self):
        files = filedialog.askopenfilenames(title="Select files to encrypt")
        if files:
            self._selected_files = list(files)
            self._file_box.configure(state="normal")
            self._file_box.delete("1.0", "end")
            for f in self._selected_files:
                size_mb = os.path.getsize(f) / (1024 * 1024)
                self._file_box.insert("end", f"{os.path.basename(f)}  ({size_mb:.2f} MB)\n")
            self._file_box.configure(state="disabled")

    def _clear_files(self):
        self._selected_files = []
        self._file_box.configure(state="normal")
        self._file_box.delete("1.0", "end")
        self._file_box.configure(state="disabled")

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self._out_var.set(folder)

    def _toggle_pw(self):
        self._pw_entry.configure(show="" if self._show_pw.get() else "*")

    def _set_status(self, text: str, color: str = "white"):
        self._status.configure(text=text, text_color=color)

    # ── Encryption logic ──────────────────────────────────────────────────

    def _start_encrypt(self):
        if not self._selected_files:
            self._set_status("Please select at least one file.", "orange")
            return
        if not self._out_var.get():
            self._set_status("Please select an output folder.", "orange")
            return
        if not self._pw_var.get():
            self._set_status("Please enter a password.", "orange")
            return

        self._enc_btn.configure(state="disabled")
        self._progress.set(0)
        self._set_status("Starting encryption...", "white")

        threading.Thread(target=self._encrypt_worker, daemon=True).start()

    def _encrypt_worker(self):
        files = self._selected_files[:]
        output_folder = self._out_var.get()
        password = self._pw_var.get()
        owner = get_username()
        total = len(files)
        succeeded = 0

        for i, input_path in enumerate(files):
            filename = os.path.basename(input_path)
            self._set_status(f"Encrypting {i + 1}/{total}: {filename}...", "white")

            output_path = os.path.join(output_folder, filename + '.dem')

            def progress_cb(p, i=i, total=total):
                overall = (i + p) / total
                self._progress.set(overall)

            success = encrypt_file(input_path, output_path, password, owner, progress_cb)

            if success:
                register_file(owner, filename, input_path, output_path, os.path.getsize(input_path))
                log(owner, 'ENCRYPT', input_path, 'SUCCESS')
                succeeded += 1
            else:
                log(owner, 'ENCRYPT', input_path, 'FAILED')
                self._set_status(f"❌ Failed to encrypt: {filename}", "#FF6B6B")
                self._enc_btn.configure(state="normal")
                return

        self._progress.set(1.0)
        self._set_status(f"✅ Done! {succeeded}/{total} file(s) encrypted successfully.", "#4CAF50")
        self._enc_btn.configure(state="normal")
