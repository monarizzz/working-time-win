# working_time

Windows用ソフトウェア使用時間トラッカー。アクティブウィンドウのプロセス単位で使用時間を計測し、タスクトレイに常駐しつつダッシュボードで確認できます。

## セットアップ (Windows)

```
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 実行

```
python run.py
```

- 起動するとタスクトレイにアイコンが常駐し、バックグラウンドでアクティブウィンドウのプロセスを2秒間隔でポーリングして計測します。
- トレイアイコンをクリック(またはダブルクリック)すると使用時間ダッシュボードが開きます。
- データは `usage.db` (SQLite) に保存され、日付ごと・プロセスごとに集計されます。

## exe化 (任意)

```
pip install pyinstaller
pyinstaller --onefile --noconsole --name WorkingTime run.py
```

生成された `dist/WorkingTime.exe` をスタートアップフォルダに登録すると、ログイン時に自動起動できます。

## 構成

- `app/tracker.py` — `win32gui`/`win32process`/`psutil` でアクティブウィンドウのプロセス名を取得し、SQLiteに秒数を積算するバックグラウンドスレッド。
- `app/db.py` — SQLiteアクセス層(`usage`テーブル: day, process_name, window_title, seconds)。
- `app/gui.py` — tkinter製のダッシュボード。日付選択とプロセス別使用時間の棒グラフ表示。
- `app/tray.py` — `pystray` によるタスクトレイ常駐・メニュー。
- `app/main.py` — 上記を束ねるエントリポイント。
# working-time-win
