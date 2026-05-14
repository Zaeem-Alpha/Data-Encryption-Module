# gui/tabs/account_tab.py
# Lets the currently logged-in user change their own password.
# Requires them to enter their current password first for verification.

import customtkinter as ctk
from storage.db import verify_user, change_password
from auth.login import get_username


class AccountTab(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="My Account",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="Change your login password here.\nYou must enter your current password to confirm.",
            text_color="gray",
            justify="center"
        ).pack(pady=(0, 20))

        frame = ctk.CTkFrame(self)
        frame.pack(padx=60, pady=10, fill="x")

        # Logged-in user display
        r0 = ctk.CTkFrame(frame, fg_color="transparent")
        r0.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(r0, text="Logged in as:", width=140, anchor="w").pack(side="left")
        ctk.CTkLabel(
            r0,
            text=get_username(),
            font=ctk.CTkFont(weight="bold"),
            text_color="#90CAF9"
        ).pack(side="left")

        # Separator
        ctk.CTkLabel(frame, text="", height=2).pack()

        # Current password
        r1 = ctk.CTkFrame(frame, fg_color="transparent")
        r1.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(r1, text="Current password:", width=140, anchor="w").pack(side="left")
        self._current_pw = ctk.CTkEntry(r1, show="*", placeholder_text="enter your current password")
        self._current_pw.pack(side="left", fill="x", expand=True)

        # New password
        r2 = ctk.CTkFrame(frame, fg_color="transparent")
        r2.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(r2, text="New password:", width=140, anchor="w").pack(side="left")
        self._new_pw = ctk.CTkEntry(r2, show="*", placeholder_text="new password (min 4 chars)")
        self._new_pw.pack(side="left", fill="x", expand=True)

        # Confirm new password
        r3 = ctk.CTkFrame(frame, fg_color="transparent")
        r3.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(r3, text="Confirm new:", width=140, anchor="w").pack(side="left")
        self._confirm_pw = ctk.CTkEntry(r3, show="*", placeholder_text="repeat new password")
        self._confirm_pw.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            frame, text="Change My Password",
            font=ctk.CTkFont(size=13),
            command=self._change_password
        ).pack(pady=16)

        self._status = ctk.CTkLabel(self, text="", wraplength=500)
        self._status.pack(pady=6)

    def _set_status(self, text, color="white"):
        self._status.configure(text=text, text_color=color)

    def _change_password(self):
        username   = get_username()
        current_pw = self._current_pw.get()
        new_pw     = self._new_pw.get()
        confirm_pw = self._confirm_pw.get()

        # All fields must be filled
        if not current_pw:
            self._set_status("Please enter your current password.", "orange")
            return
        if not new_pw:
            self._set_status("Please enter a new password.", "orange")
            return
        if not confirm_pw:
            self._set_status("Please confirm your new password.", "orange")
            return

        # Verify current password is correct
        valid, _ = verify_user(username, current_pw)
        if not valid:
            self._set_status("Current password is incorrect.", "#FF6B6B")
            self._current_pw.delete(0, "end")
            return

        # New passwords must match
        if new_pw != confirm_pw:
            self._set_status("New passwords do not match. Please try again.", "#FF6B6B")
            self._confirm_pw.delete(0, "end")
            return

        # Cannot reuse same password
        if current_pw == new_pw:
            self._set_status("New password must be different from your current password.", "orange")
            return

        ok, error = change_password(username, new_pw)
        if ok:
            self._set_status("Password changed successfully!", "#4CAF50")
            self._current_pw.delete(0, "end")
            self._new_pw.delete(0, "end")
            self._confirm_pw.delete(0, "end")
        else:
            self._set_status(f"Error: {error}", "#FF6B6B")
