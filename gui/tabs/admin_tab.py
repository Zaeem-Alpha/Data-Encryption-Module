# gui/tabs/admin_tab.py
# Admin-only panel.
# Fixed: delete users, change any user's password, list users with refresh.

import customtkinter as ctk
from storage.db import list_users, add_user, delete_user, change_password, get_all_files, user_exists
from storage.logger import get_logs


class AdminTab(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()
        self._refresh_users()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="Admin Panel",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 5))

        inner_tabs = ctk.CTkTabview(self)
        inner_tabs.pack(fill="both", expand=True, padx=10, pady=5)

        inner_tabs.add("Users")
        inner_tabs.add("Change Password")
        inner_tabs.add("All Files")
        inner_tabs.add("Audit Log")

        self._build_users_tab(inner_tabs.tab("Users"))
        self._build_change_pw_tab(inner_tabs.tab("Change Password"))
        self._build_files_tab(inner_tabs.tab("All Files"))
        self._build_logs_tab(inner_tabs.tab("Audit Log"))

    def _build_users_tab(self, parent):
        ctk.CTkLabel(parent, text="Registered users:", anchor="w").pack(fill="x", padx=10, pady=(10, 2))

        self._user_box = ctk.CTkTextbox(
            parent, height=130, state="disabled",
            font=ctk.CTkFont(family="Courier New", size=12)
        )
        self._user_box.pack(fill="x", padx=10, pady=2)

        ctk.CTkButton(parent, text="Refresh", width=110, command=self._refresh_users).pack(pady=4)

        ctk.CTkLabel(parent, text="-- Add new user --", text_color="gray").pack(pady=(8, 4))

        add_frame = ctk.CTkFrame(parent)
        add_frame.pack(fill="x", padx=10, pady=4)

        r1 = ctk.CTkFrame(add_frame, fg_color="transparent")
        r1.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r1, text="Username:", width=90, anchor="w").pack(side="left")
        self._new_user = ctk.CTkEntry(r1, placeholder_text="new username")
        self._new_user.pack(side="left", fill="x", expand=True)

        r2 = ctk.CTkFrame(add_frame, fg_color="transparent")
        r2.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r2, text="Password:", width=90, anchor="w").pack(side="left")
        self._new_pw = ctk.CTkEntry(r2, show="*", placeholder_text="password (min 4 chars)")
        self._new_pw.pack(side="left", fill="x", expand=True)

        r3 = ctk.CTkFrame(add_frame, fg_color="transparent")
        r3.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r3, text="Role:", width=90, anchor="w").pack(side="left")
        self._role_var = ctk.StringVar(value="user")
        ctk.CTkOptionMenu(r3, variable=self._role_var, values=["user", "admin"]).pack(side="left")

        ctk.CTkButton(add_frame, text="Add User", command=self._add_user).pack(pady=8)

        ctk.CTkLabel(parent, text="-- Delete user --", text_color="gray").pack(pady=(8, 4))

        del_row = ctk.CTkFrame(parent, fg_color="transparent")
        del_row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(del_row, text="Username:", anchor="w", width=90).pack(side="left")
        self._del_user_entry = ctk.CTkEntry(del_row, placeholder_text="username to delete")
        self._del_user_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            del_row, text="Delete", width=90,
            fg_color="#B71C1C", hover_color="#7F0000",
            command=self._delete_user
        ).pack(side="left")

        self._user_status = ctk.CTkLabel(parent, text="", wraplength=450)
        self._user_status.pack(pady=6)

    def _build_change_pw_tab(self, parent):
        ctk.CTkLabel(
            parent,
            text="Change the password of any user account.",
            text_color="gray"
        ).pack(pady=(15, 10))

        frame = ctk.CTkFrame(parent)
        frame.pack(padx=20, pady=10, fill="x")

        r1 = ctk.CTkFrame(frame, fg_color="transparent")
        r1.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(r1, text="Username:", width=120, anchor="w").pack(side="left")
        self._cpw_user = ctk.CTkEntry(r1, placeholder_text="whose password to change")
        self._cpw_user.pack(side="left", fill="x", expand=True)

        r2 = ctk.CTkFrame(frame, fg_color="transparent")
        r2.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(r2, text="New password:", width=120, anchor="w").pack(side="left")
        self._cpw_new = ctk.CTkEntry(r2, show="*", placeholder_text="new password (min 4 chars)")
        self._cpw_new.pack(side="left", fill="x", expand=True)

        r3 = ctk.CTkFrame(frame, fg_color="transparent")
        r3.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(r3, text="Confirm:", width=120, anchor="w").pack(side="left")
        self._cpw_confirm = ctk.CTkEntry(r3, show="*", placeholder_text="repeat new password")
        self._cpw_confirm.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(frame, text="Change Password", command=self._admin_change_password).pack(pady=12)

        self._cpw_status = ctk.CTkLabel(parent, text="", wraplength=450)
        self._cpw_status.pack(pady=6)

    def _build_files_tab(self, parent):
        ctk.CTkLabel(parent, text="All encrypted files in the registry:", anchor="w").pack(fill="x", padx=10, pady=(10, 2))
        self._files_box = ctk.CTkTextbox(parent, state="disabled", font=ctk.CTkFont(family="Courier New", size=11))
        self._files_box.pack(fill="both", expand=True, padx=10, pady=4)
        ctk.CTkButton(parent, text="Refresh", width=110, command=self._refresh_files).pack(pady=6)
        self._refresh_files()

    def _build_logs_tab(self, parent):
        ctk.CTkLabel(parent, text="Recent audit log entries:", anchor="w").pack(fill="x", padx=10, pady=(10, 2))
        self._log_box = ctk.CTkTextbox(parent, state="disabled", font=ctk.CTkFont(family="Courier New", size=11))
        self._log_box.pack(fill="both", expand=True, padx=10, pady=4)
        ctk.CTkButton(parent, text="Refresh", width=110, command=self._refresh_logs).pack(pady=6)
        self._refresh_logs()

    def _refresh_users(self):
        users = list_users()
        self._user_box.configure(state="normal")
        self._user_box.delete("1.0", "end")
        self._user_box.insert("end", f"{'USERNAME':<20} {'ROLE':<10} CREATED\n")
        self._user_box.insert("end", "-" * 55 + "\n")
        for username, role, created_at in users:
            self._user_box.insert("end", f"{username:<20} {role:<10} {created_at[:19]}\n")
        self._user_box.configure(state="disabled")

    def _refresh_files(self):
        files = get_all_files()
        self._files_box.configure(state="normal")
        self._files_box.delete("1.0", "end")
        if not files:
            self._files_box.insert("end", "No encrypted files registered yet.\n")
        else:
            self._files_box.insert("end", f"{'OWNER':<15} {'FILENAME':<30} {'SIZE':>10}  ENCRYPTED AT\n")
            self._files_box.insert("end", "-" * 75 + "\n")
            for owner, filename, enc_path, size, created_at in files:
                size_str = f"{size / 1024:.1f} KB" if size else "?"
                self._files_box.insert("end", f"{owner:<15} {filename:<30} {size_str:>10}  {created_at[:19]}\n")
        self._files_box.configure(state="disabled")

    def _refresh_logs(self):
        lines = get_logs(200)
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        if not lines:
            self._log_box.insert("end", "No log entries yet.\n")
        else:
            for line in reversed(lines):
                self._log_box.insert("end", line)
        self._log_box.configure(state="disabled")

    def _set_user_status(self, text, color="white"):
        self._user_status.configure(text=text, text_color=color)

    def _set_cpw_status(self, text, color="white"):
        self._cpw_status.configure(text=text, text_color=color)

    def _add_user(self):
        username = self._new_user.get().strip()
        password = self._new_pw.get()
        role     = self._role_var.get()
        if not username or not password:
            self._set_user_status("Please fill in both username and password.", "orange")
            return
        ok, error = add_user(username, password, role)
        if ok:
            self._set_user_status(f"User '{username}' ({role}) created successfully.", "#4CAF50")
            self._new_user.delete(0, "end")
            self._new_pw.delete(0, "end")
            self._refresh_users()
        else:
            self._set_user_status(f"Error: {error}", "#FF6B6B")

    def _delete_user(self):
        username = self._del_user_entry.get().strip()
        if not username:
            self._set_user_status("Please enter a username to delete.", "orange")
            return
        if not user_exists(username):
            self._set_user_status(f"User '{username}' does not exist.", "#FF6B6B")
            return
        ok, error = delete_user(username)
        if ok:
            self._set_user_status(f"User '{username}' has been deleted.", "#4CAF50")
            self._del_user_entry.delete(0, "end")
            self._refresh_users()
        else:
            self._set_user_status(f"Error: {error}", "#FF6B6B")

    def _admin_change_password(self):
        username   = self._cpw_user.get().strip()
        new_pw     = self._cpw_new.get()
        confirm_pw = self._cpw_confirm.get()
        if not username:
            self._set_cpw_status("Please enter a username.", "orange")
            return
        if not new_pw:
            self._set_cpw_status("Please enter a new password.", "orange")
            return
        if new_pw != confirm_pw:
            self._set_cpw_status("Passwords do not match. Please try again.", "#FF6B6B")
            self._cpw_confirm.delete(0, "end")
            return
        if not user_exists(username):
            self._set_cpw_status(f"User '{username}' does not exist.", "#FF6B6B")
            return
        ok, error = change_password(username, new_pw)
        if ok:
            self._set_cpw_status(f"Password for '{username}' changed successfully.", "#4CAF50")
            self._cpw_user.delete(0, "end")
            self._cpw_new.delete(0, "end")
            self._cpw_confirm.delete(0, "end")
        else:
            self._set_cpw_status(f"Error: {error}", "#FF6B6B")
