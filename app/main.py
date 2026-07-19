import tkinter as tk

from .tracker import Tracker
from .gui import DashboardWindow
from .tray import TrayApp


def main():
    tracker = Tracker()
    tracker.start()

    root = tk.Tk()
    root.withdraw()

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
