# working_time

Windows用ソフトウェア使用時間トラッカー。アクティブウィンドウのプロセス単位で使用時間を計測し、タスクトレイに常駐しつつダッシュボードで確認できます。
<img width="606" height="539" alt="image" src="https://github.com/user-attachments/assets/be339fb4-514e-451d-825d-6ff71458fb19" />


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

生成された `dist/WorkingTime.exe` をスタートアップフォルダ(`shell:startup`)にショートカットとして登録すると、ログイン時に自動起動できます。

### 開発運用フロー(重要)

`WorkingTime.exe` は **ビルド時点のコードを固めたスナップショット** です。`app/` 以下のソースコードを後から変更しても、既存の exe には反映されません。

- コードを頻繁に触っている間は `python run.py` で直接動作確認する
- ある程度変更がまとまったら、上記コマンドで **再ビルド** して exe を作り直す
- 配布・常駐用の exe は Downloads やスタートアップフォルダなど、リポジトリ外のコピーを使う運用でもよい

### exe配布のベストプラクティス(参考)

- `--onefile` は実行時に一時フォルダへ自己展開するため、起動が数秒遅くなり、その展開動作がアンチウイルスの誤検知(false positive)を招きやすい。個人PCでの常駐用途なら実用上問題ないが、Windows Defender等で警告が出る場合は `--onedir`(展開不要でAV誤検知が少なく、2回目以降の起動も高速)への切り替えを検討する
- UPX圧縮(デフォルトで有効)も誤検知の一因になり得るため、警告が出る場合は `--noupx` を試す
- 他人のPCへ広く配布する場合は、コード署名証明書(.pfx)で `signtool` を使い署名すると、AV警告の減少と信頼度(reputation)の蓄積につながる。誤検知が出た場合は各AVベンダーへ報告すれば通常数日でホワイトリスト化される
- 参考: [PyInstaller Antivirus False Positives](https://www.pythonguis.com/faq/problems-with-antivirus-software-and-pyinstaller/) / [Code Signing Recipe](https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Win-Code-Signing) / [onefile vs onedir 起動速度の議論](https://discuss.python.org/t/opinion-pyinstaller-onefile-or-onedir-for-program-distribution/106137)

## 構成

- `app/tracker.py` — `win32gui`/`win32process`/`psutil` でアクティブウィンドウのプロセス名を取得し、SQLiteに秒数を積算するバックグラウンドスレッド。
- `app/db.py` — SQLiteアクセス層(`usage`テーブル: day, process_name, window_title, seconds)。
- `app/gui.py` — tkinter製のダッシュボード。日付選択とプロセス別使用時間の棒グラフ表示。
- `app/tray.py` — `pystray` によるタスクトレイ常駐・メニュー。
- `app/main.py` — 上記を束ねるエントリポイント。
# working-time-win
