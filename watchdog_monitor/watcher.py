# watchdog_monitor/watcher.py
# Watches a folder and auto-encrypts any new file that appears inside it.
# Uses the folder-level password set when the watch starts.

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.crypto import encrypt_file
from storage.db import register_file
from storage.logger import log


class _DemEventHandler(FileSystemEventHandler):
    """Handles new file events in the watched folder."""

    def __init__(self, output_folder: str, password: str, owner: str, status_callback=None):
        self.output_folder = output_folder
        self.password = password
        self.owner = owner
        self.status_callback = status_callback
        self._processing = set()  # avoid double-processing the same file

    def _notify(self, message: str):
        print(message)
        if self.status_callback:
            self.status_callback(message)

    def on_created(self, event):
        if event.is_directory:
            return

        path = event.src_path

        # Skip .dem files and files already being processed
        if path.endswith('.dem') or path in self._processing:
            return

        self._processing.add(path)
        try:
            # Wait briefly so the file is fully written before we read it
            time.sleep(1.5)

            if not os.path.exists(path):
                return

            filename = os.path.basename(path)
            output_path = os.path.join(self.output_folder, filename + '.dem')

            self._notify(f"New file detected: {filename}")
            self._notify(f"Auto-encrypting...")

            success = encrypt_file(path, output_path, self.password, self.owner)

            if success:
                file_size = os.path.getsize(path)
                register_file(self.owner, filename, path, output_path, file_size)
                log(self.owner, 'WATCHDOG_ENCRYPT', path, 'SUCCESS')
                self._notify(f"✅ Encrypted: {filename}  →  {output_path}")
            else:
                log(self.owner, 'WATCHDOG_ENCRYPT', path, 'FAILED')
                self._notify(f"❌ Failed to encrypt: {filename}")

        finally:
            self._processing.discard(path)


class FolderWatcher:
    """
    Watches a folder and encrypts new files automatically.
    Usage:
        watcher = FolderWatcher(watch_folder, output_folder, password, owner)
        watcher.start()
        ...
        watcher.stop()
    """

    def __init__(
        self,
        watch_folder: str,
        output_folder: str,
        password: str,
        owner: str,
        status_callback=None
    ):
        self.watch_folder = watch_folder
        self.output_folder = output_folder
        self.password = password
        self.owner = owner
        self.status_callback = status_callback
        self._observer = None

    def _notify(self, message: str):
        print(message)
        if self.status_callback:
            self.status_callback(message)

    def start(self):
        os.makedirs(self.output_folder, exist_ok=True)

        handler = _DemEventHandler(
            self.output_folder, self.password, self.owner, self.status_callback
        )
        self._observer = Observer()
        self._observer.schedule(handler, self.watch_folder, recursive=False)
        self._observer.start()
        self._notify(f"● Watching: {self.watch_folder}")
        self._notify(f"  Encrypted files will be saved to: {self.output_folder}")

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self._notify("■ Watchdog stopped.")

    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()
