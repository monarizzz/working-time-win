import threading
import time
from datetime import date

import psutil
import win32gui
import win32process

from . import db, display_names

POLL_INTERVAL_SECONDS = 2
IDLE_PROCESS_NAMES = {"", "explorer.exe", "LockApp.exe", "SearchHost.exe"}

# サンドボックス化された子プロセス(Chromeのレンダラー等)が一時的に
# フォアグラウンドウィンドウの所有者になり、exe()がAccessDeniedになることがある。
# 一度でも解決できたパスはプロセス名単位で覚えておき、失敗時のフォールバックにする。
_last_known_exe_path: dict[str, str] = {}


def get_active_window_info():
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None, None, None, None
    title = win32gui.GetWindowText(hwnd)
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        process_name = proc.name()
        try:
            exe_path = proc.exe()
            _last_known_exe_path[process_name] = exe_path
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            exe_path = _last_known_exe_path.get(process_name)
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return None, None, None, None
    display_name = display_names.get_display_name(process_name, exe_path)
    return process_name, title, display_name, exe_path


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
        last_process, last_title, last_display, last_exe = get_active_window_info()
        last_day = date.today().isoformat()

        while not self._stop_event.is_set():
            self._stop_event.wait(self.poll_interval)
            if self._stop_event.is_set():
                break

            process_name, title, display_name, exe_path = get_active_window_info()
            today = date.today().isoformat()

            if last_process and last_process.lower() not in {n.lower() for n in IDLE_PROCESS_NAMES}:
                day_to_credit = last_day if last_day == today else last_day
                db.add_seconds(
                    last_process, last_title or "", int(self.poll_interval),
                    day=day_to_credit, display_name=last_display, exe_path=last_exe,
                )

            last_process, last_title, last_display, last_exe = process_name, title, display_name, exe_path
            last_day = today
