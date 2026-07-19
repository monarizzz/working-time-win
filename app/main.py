import ctypes
import tkinter as tk

import sv_ttk

from .theme import is_dark_mode
from .tracker import Tracker
from .gui import DashboardWindow
from .tray import TrayApp


def _enable_dpi_awareness():
    """高DPIモニターでウィンドウがぼやけて表示されるのを防ぐ。

    宣言しないとWindowsが96DPI前提でレンダリングした結果を
    ビットマップ拡大するため、文字やアイコンがにじんで見える。
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def main():
    _enable_dpi_awareness()

    tracker = Tracker()
    tracker.start()

    root = tk.Tk()
    root.withdraw()
    sv_ttk.set_theme("dark" if is_dark_mode() else "light")

    dashboard = DashboardWindow(root)

    def show_dashboard():
        root.after(0, lambda: (dashboard.deiconify(), dashboard.refresh(), dashboard.lift()))

    def on_exit():
        tracker.stop()
        root.after(0, root.quit)

    tray = TrayApp(on_show=show_dashboard, on_exit=on_exit)
    tray.run_detached()

    root.mainloop()


if __name__ == "__main__":
    main()
