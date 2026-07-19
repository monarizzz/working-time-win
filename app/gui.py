import time
import tkinter as tk
from tkinter import ttk

import psutil

from . import db, icons
from .theme import is_dark_mode

UPTIME_REFRESH_MS = 60_000
UPTIME_TOOLTIP_TEXT = (
    "高速スタートアップが有効な場合、\n"
    "実際の電源投入時刻より古い値が表示されることがあります。"
)


class Tooltip:
    def __init__(self, widget, text, bg="#ffffe0", fg="black"):
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
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
            background=self.bg, foreground=self.fg, relief=tk.SOLID, borderwidth=1,
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
        self.geometry("680x560")
        self.minsize(560, 420)

        dark = is_dark_mode()
        if dark:
            self.canvas_bg = "#1e1e1e"
            self.canvas_fg = "#e8e8e8"
            widget_bg = "#252525"
            field_bg = "#2d2d2d"
            border = "#3a3a3a"
            active_bg = "#3a3a3a"
        else:
            self.canvas_bg = "white"
            self.canvas_fg = "black"
            widget_bg = "#f0f0f0"
            field_bg = "white"
            border = "#c0c0c0"
            active_bg = "#e0e0e0"

        self.configure(bg=self.canvas_bg)

        style = ttk.Style(self)
        style.configure("Dash.TFrame", background=self.canvas_bg)
        style.configure("Dash.TLabel", background=self.canvas_bg, foreground=self.canvas_fg)
        style.configure(
            "Dash.TButton", background=widget_bg, foreground=self.canvas_fg,
            bordercolor=border, focuscolor=border,
        )
        style.map("Dash.TButton", background=[("active", active_bg)])
        style.configure(
            "Dash.TCombobox", fieldbackground=field_bg, background=widget_bg,
            foreground=self.canvas_fg, arrowcolor=self.canvas_fg, bordercolor=border,
        )
        style.map(
            "Dash.TCombobox",
            fieldbackground=[("readonly", field_bg)],
            foreground=[("readonly", self.canvas_fg)],
            background=[("readonly", widget_bg)],
        )
        self.option_add("*TCombobox*Listbox.background", field_bg)
        self.option_add("*TCombobox*Listbox.foreground", self.canvas_fg)
        self.option_add("*TCombobox*Listbox.selectBackground", active_bg)

        top = ttk.Frame(self, padding=(18, 16), style="Dash.TFrame")
        top.pack(fill=tk.X)

        ttk.Label(top, text="日付:", style="Dash.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        self.day_var = tk.StringVar()
        self.day_combo = ttk.Combobox(
            top, textvariable=self.day_var, state="readonly", width=15, style="Dash.TCombobox",
        )
        self.day_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.day_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(top, text="更新", command=self.refresh, style="Dash.TButton").pack(side=tk.LEFT)

        self.total_label = ttk.Label(top, text="", font=("", 11, "bold"), style="Dash.TLabel")
        self.total_label.pack(side=tk.RIGHT)

        uptime_row = ttk.Frame(self, padding=(18, 0, 18, 12), style="Dash.TFrame")
        uptime_row.pack(fill=tk.X)
        self.uptime_label = ttk.Label(uptime_row, text="", style="Dash.TLabel")
        self.uptime_label.pack(side=tk.LEFT)
        Tooltip(self.uptime_label, UPTIME_TOOLTIP_TEXT, bg=field_bg, fg=self.canvas_fg)

        self.canvas = tk.Canvas(self, bg=self.canvas_bg, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 18))

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
            self.canvas.create_text(
                20, 20, anchor="nw", text="この日のデータはありません", fill=self.canvas_fg
            )
            return

        max_seconds = max(r[2] for r in rows) or 1
        bar_height = 34
        gap = 18
        icon_size = 22
        icon_x = 18
        text_x = icon_x + icon_size + 12
        left_margin = 230
        right_margin = 110
        canvas_width = self.canvas.winfo_width() or 500
        bar_area_width = max(canvas_width - left_margin - right_margin, 50)

        y = 16
        for process_name, display_name, total, exe_path in rows:
            bar_len = int((total / max_seconds) * bar_area_width)
            photo = icons.get_icon_photo(process_name, exe_path, size=icon_size)
            if photo:
                self._icon_refs.append(photo)
                self.canvas.create_image(icon_x, y + bar_height / 2, anchor="w", image=photo)
            self.canvas.create_text(
                text_x, y + bar_height / 2, anchor="w", text=display_name, fill=self.canvas_fg
            )
            self.canvas.create_rectangle(
                left_margin, y, left_margin + bar_len, y + bar_height,
                fill="#4a90d9", outline=""
            )
            self.canvas.create_text(
                left_margin + bar_len + 12, y + bar_height / 2, anchor="w",
                text=format_seconds(total), fill=self.canvas_fg
            )
            y += bar_height + gap

        self.canvas.config(scrollregion=(0, 0, canvas_width, y + 10))
