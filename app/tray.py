import threading

from PIL import Image, ImageDraw
import pystray


def make_icon_image():
    img = Image.new("RGB", (64, 64), "#4a90d9")
    draw = ImageDraw.Draw(img)
    draw.rectangle((16, 16, 48, 48), fill="white")
    return img


class TrayApp:
    def __init__(self, on_show, on_exit):
        self.on_show = on_show
        self.on_exit = on_exit
        self.icon = pystray.Icon(
            "working_time",
            make_icon_image(),
            "使用時間トラッカー",
            menu=pystray.Menu(
                pystray.MenuItem("ダッシュボードを開く", self._show, default=True),
                pystray.MenuItem("終了", self._exit),
            ),
        )

    def _show(self, icon=None, item=None):
        self.on_show()

    def _exit(self, icon=None, item=None):
        self.icon.stop()
        self.on_exit()

    def run_detached(self):
        thread = threading.Thread(target=self.icon.run, daemon=True)
        thread.start()
