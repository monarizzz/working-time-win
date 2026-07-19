from PIL import Image, ImageTk
import win32con
import win32gui
import win32ui

_cache: dict[str, "ImageTk.PhotoImage | None"] = {}


def _hicon_to_image(hicon, size: int) -> Image.Image:
    """アイコンを指定サイズちょうどに引き伸ばして描画する。

    DrawIcon(ネイティブサイズ描画)だと元アイコンの解像度によって
    見た目のサイズがバラつくため、DrawIconExで明示的にsize x sizeへ
    ストレッチし、どのアイコンも同じ大きさに揃える。
    """
    screen_dc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
    mem_dc = screen_dc.CreateCompatibleDC()
    hbmp = win32ui.CreateBitmap()
    hbmp.CreateCompatibleBitmap(screen_dc, size, size)
    mem_dc.SelectObject(hbmp)
    win32gui.DrawIconEx(mem_dc.GetSafeHdc(), 0, 0, hicon, size, size, 0, None, win32con.DI_NORMAL)

    bmpinfo = hbmp.GetInfo()
    bmpstr = hbmp.GetBitmapBits(True)
    image = Image.frombuffer(
        "RGBA", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRA", 0, 1
    )

    win32gui.DeleteObject(hbmp.GetHandle())
    mem_dc.DeleteDC()
    screen_dc.DeleteDC()
    return image


def get_icon_photo(process_name: str, exe_path: str | None, size: int = 20):
    """exeからアイコンを抽出してPhotoImageを返す(プロセス名単位でキャッシュ)。

    取得できない場合はNoneを返す。呼び出し側でTkinterのImageオブジェクトへの
    参照を保持しないとガベージコレクトされて表示が消えるので注意。
    """
    if process_name in _cache:
        return _cache[process_name]

    photo = None
    if exe_path:
        large_icons, small_icons = [], []
        try:
            large_icons, small_icons = win32gui.ExtractIconEx(exe_path, 0)
            hicon = (large_icons or small_icons)[0]
            render_size = max(size, 32)
            image = _hicon_to_image(hicon, render_size)
            if render_size != size:
                image = image.resize((size, size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
        except Exception:
            photo = None
        finally:
            for handle in list(large_icons) + list(small_icons):
                win32gui.DestroyIcon(handle)

    _cache[process_name] = photo
    return photo
