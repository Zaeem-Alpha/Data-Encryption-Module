# gui/tabs/decrypt_tab.py
# Tab where users select .dem files, enter a password, and decrypt them.
# Shows owner info from the header before decryption starts.

import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from core.crypto import decrypt_file, read_dem_header
from storage.logger import log
from auth.login import get_username, is_admin


class DecryptTab(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_files = []
        self._build_ui()

    def _build_ui(self):
        # ── Title ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Decrypt Files",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self, text="Select .dem file(s) and enter the correct password to decrypt.",
            text_color="gray"
        ).pack(pady=(0, 10))

        # ── File selection ────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Files to decrypt (.dem):", anchor="w").pack(fill="x", padx=20)

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
        ctk.CTkLabel(self, text="Save decrypted files to:", anchor="w").pack(fill="x", padx=20)

        out_row = ctk.CTkFrame(self, fg_color="transparent")
        out_row.pack(fill="x", padx=20, pady=4)

        self._out_var = ctk.StringVar()
        ctk.CTkEntry(out_row, textvariable=self._out_var,
                     placeholder_text="Choose output folder...").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(out_row, text="Browse", width=85,
                      command=self._browse_output).pack(side="left", padx=(8, 0))

        # ── Password ──────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Decryption password:", anchor="w").pack(fill="x", padx=20)

        pw_row = ctk.CTkFrame(self, fg_color="transparent")
        pw_row.pack(fill="x", padx=20, pady=4)

        self._pw_var = ctk.StringVar()
        self._pw_entry = ctk.CTkEntry(pw_row, textvariable=self._pw_var,
                                      show="*", placeholder_text="Enter the file's password")
        self._pw_entry.pack(side="left", fill="x", expand=True)

        self._show_pw = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(pw_row, text="Show", variable=self._show_pw,
                        command=self._toggle_pw).pack(side="left", padx=(8, 0))

        # ── Progress ──────────────────────────────────────────────────────
        self._progress = ctk.CTkProgressBar(self)
        self._progress.pack(fill="x", padx=20, pady=(10, 2))
        self._progress.set(0)

        self._status = ctk.CTkLabel(self, text="", wraplength=550)
        self._status.pack(pady=4)

        self._dec_btn = ctk.CTkButton(
            self, text="  🔓  Decrypt", width=220,
            font=ctk.CTkFont(size=14),
            command=self._start_decrypt
        )
        self._dec_btn.pack(pady=10)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select .dem files to decrypt",
            filetypes=[("DEM Encrypted Files", "*.dem"), ("All Files", "*.*")]
        )
        if files:
            self._selected_files = list(files)
            self._file_box.configure(state="normal")
            self._file_box.delete("1.0", "end")
            for f in self._selected_files:
                header = read_dem_header(f)
                if header:
                    info = f"  [Owner: {header['owner']}  |  Original: {header['original_filename']}]"
                else:
                    info = "  [⚠ Not a valid .dem file]"
                self._file_box.insert("end", os.path.basename(f) + info + "\n")
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

    # ── Decryption logic ──────────────────────────────────────────────────

    def _start_decrypt(self):
        if not self._selected_files:
            self._set_status("Please select at least one .dem file.", "orange")
            return
        if not self._out_var.get():
            self._set_status("Please select an output folder.", "orange")
            return
        if not self._pw_var.get():
            self._set_status("Please enter the decryption password.", "orange")
            return

        self._dec_btn.configure(state="disabled")
        self._progress.set(0)
        self._set_status("Starting decryption...", "white")

        threading.Thread(target=self._decrypt_worker, daemon=True).start()

    def _decrypt_worker(self):
        files = self._selected_files[:]
        output_folder = self._out_var.get()
        password = self._pw_var.get()
        username = get_username()
        admin = is_admin()
        total = len(files)
        succeeded = 0

        for i, input_path in enumerate(files):
            filename = os.path.basename(input_path)
            self._set_status(f"Decrypting {i + 1}/{total}: {filename}...", "white")

            # Output filename: strip .dem, avoid overwriting
            out_name = filename[:-4] if filename.endswith('.dem') else filename + '_decrypted'
            output_path = os.path.join(output_folder, out_name)

            def progress_cb(p, i=i, total=total):
                overall = (i + p) / total
                self._progress.set(overall)

            success, result = decrypt_file(
                input_path, output_path, password, username,
                is_admin=admin,
                progress_callback=progress_cb
            )

            if success:
                log(username, 'DECRYPT', input_path, 'SUCCESS')
                succeeded += 1
            else:
                log(username, 'DECRYPT', input_path, 'FAILED', result)
                self._set_status(f"❌ {result}", "#FF6B6B")
                self._dec_btn.configure(state="normal")
                return

        self._progress.set(1.0)
        self._set_status(f"✅ Done! {succeeded}/{total} file(s) decrypted successfully.", "#4CAF50")
        self._dec_btn.configure(state="normal")
