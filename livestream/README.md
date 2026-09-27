# livestream — AIキャラ全自動配信

使い方・初期設定・収益化の目安は [docs/06_livestream.md](../docs/06_livestream.md)。

| ファイル | 役割 |
|---|---|
| `server.py` | 22:00〜23:00 の番組進行（OBS開始/停止・返答・雑談・締め・ログ） |
| `onecomme-plugin/index.js` | わんコメ → server.py へコメント転送 |
| `topics.txt` | コメントが無い時の雑談ネタ |
| `ng_words.txt` | 反応しない言葉 |
| `run_daily.bat` / `setup_task.ps1` | 毎日21:50に全アプリを起動するWindowsタスク |
| `.env.example` | APIキー・デバイス名・配信時間の設定 |
