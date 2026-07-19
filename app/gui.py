import time
import tkinter as tk
from tkinter import ttk

import psutil

from . import db, icons

UPTIME_REFRESH_MS = 60_000
UPTIME_TOOLTIP_TEXT = (
    "高速スタートアップが有効な場合、\n"
    "実際の電源投入時刻より古い値が表示されることがあります。"
)


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("", 9), padx=6, pady=3,
        ).pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


def format_seconds(total: int) -> str:
    d, rem = divmod(int(total), 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}日{h}時間"
    if h:
        return f"{h}時間{m}分"
    if m:
        return f"{m}分{s}秒"
    return f"{s}秒"


class DashboardWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("ソフトウェア使用時間ダッシュボード")
        self.geometry("560x480")
        self.minsize(480, 360)

        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="日付:").pack(side=tk.LEFT)
        self.day_var = tk.StringVar()
        self.day_combo = ttk.Combobox(top, textvariable=self.day_var, state="readonly", width=15)
        self.day_combo.pack(side=tk.LEFT, padx=5)
        self.day_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(top, text="更新", command=self.refresh).pack(side=tk.LEFT, padx=5)

        self.total_label = ttk.Label(top, text="", font=("", 10, "bold"))
        self.total_label.pack(side=tk.RIGHT)

        uptime_row = ttk.Frame(self, padding=(10, 0))
        uptime_row.pack(fill=tk.X)
        self.uptime_label = ttk.Label(uptime_row, text="")
        self.uptime_label.pack(side=tk.LEFT)
        Tooltip(self.uptime_label, UPTIME_TOOLTIP_TEXT)

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        self.load_days()
        self.refresh()
        self.update_uptime()

    def load_days(self):
        days = db.get_available_days()
        from datetime import date

        today = date.today().isoformat()
        if today not in days:
            days.insert(0, today)
        self.day_combo["values"] = days
        if not self.day_var.get():
            self.day_var.set(today)

    def update_uptime(self):
        uptime_seconds = time.time() - psutil.boot_time()
        self.uptime_label.config(text=f"PC起動から: {format_seconds(uptime_seconds)}")
        self.after(UPTIME_REFRESH_MS, self.update_uptime)

    def refresh(self):
        self.load_days()
        day = self.day_var.get()
        rows = db.get_usage_by_process(day)
        self.draw_bars(rows)
        total = sum(r[2] for r in rows)
        self.total_label.config(text=f"合計: {format_seconds(total)}")

    def draw_bars(self, rows):
        self.canvas.delete("all")
        self._icon_refs = []
        if not rows:
            self.canvas.create_text(20, 20, anchor="nw", text="この日のデータはありません")
            return

        max_seconds = max(r[2] for r in rows) or 1
        bar_height = 28
        gap = 12
        icon_size = 20
        icon_x = 14
        text_x = icon_x + icon_size + 8
        left_margin = 200
        right_margin = 90
        canvas_width = self.canvas.winfo_width() or 500
        bar_area_width = max(canvas_width - left_margin - right_margin, 50)

        y = 10
        for process_name, display_name, total, exe_path in rows:
            bar_len = int((total / max_seconds) * bar_area_width)
            photo = icons.get_icon_photo(process_name, exe_path, size=icon_size)
            if photo:
                self._icon_refs.append(photo)
                self.canvas.create_image(icon_x, y + bar_height / 2, anchor="w", image=photo)
            self.canvas.create_text(
                text_x, y + bar_height / 2, anchor="w", text=display_name
            )
            self.canvas.create_rectangle(
                left_margin, y, left_margin + bar_len, y + bar_height,
                fill="#4a90d9", outline=""
            )
            self.canvas.create_text(
                left_margin + bar_len + 8, y + bar_height / 2, anchor="w",
                text=format_seconds(total)
            )
            y += bar_height + gap

        self.canvas.config(scrollregion=(0, 0, canvas_width, y + 10))
