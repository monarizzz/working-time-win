import threading
import time
from datetime import date

import psutil
import win32gui
import win32process

from . import db

POLL_INTERVAL_SECONDS = 2
IDLE_PROCESS_NAMES = {"", "explorer.exe", "LockApp.exe", "SearchHost.exe"}


def get_active_window_info():
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None, None
    title = win32gui.GetWindowText(hwnd)
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process_name = psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return None, None
    return process_name, title


class Tracker:
    def __init__(self, poll_interval: float = POLL_INTERVAL_SECONDS):
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        db.init_db()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        last_process, last_title = get_active_window_info()
        last_day = date.today().isoformat()

        while not self._stop_event.is_set():
            self._stop_event.wait(self.poll_interval)
            if self._stop_event.is_set():
                break

            process_name, title = get_active_window_info()
            today = date.today().isoformat()

            if last_process and last_process.lower() not in {n.lower() for n in IDLE_PROCESS_NAMES}:
                day_to_credit = last_day if last_day == today else last_day
                db.add_seconds(last_process, last_title or "", int(self.poll_interval), day=day_to_credit)

            last_process, last_title = process_name, title
            last_day = today
