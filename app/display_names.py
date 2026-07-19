import win32api

_cache: dict[str, str] = {}


def _strip_exe(process_name: str) -> str:
    if process_name.lower().endswith(".exe"):
        return process_name[:-4]
    return process_name


def get_display_name(process_name: str, exe_path: str | None = None) -> str:
    """プロセス名から分かりやすいアプリ名(例:「Google Chrome」)を取得する。

    実行ファイルにバージョン情報(FileDescription)がない場合は、
    ".exe"を除いたプロセス名にフォールバックする。
    """
    if process_name in _cache:
        return _cache[process_name]

    display = _strip_exe(process_name)
    if exe_path:
        try:
            lang, codepage = win32api.GetFileVersionInfo(
                exe_path, "\\VarFileInfo\\Translation"
            )[0]
            description = win32api.GetFileVersionInfo(
                exe_path, f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\FileDescription"
            )
            if description and description.strip():
                display = description.strip()
        except Exception:
            pass

    _cache[process_name] = display
    return display
