#!/usr/bin/env python3
"""初回だけ自分のPCで実行し、Googleドライブ＋YouTube分析用のリフレッシュトークンを取得する。

（全自動モードで YouTube の成績を企画に反映するため、YouTube の「閲覧のみ」権限も一緒にもらう。
  以前ドライブだけの鍵を作った人も、もう一度実行して GDRIVE_REFRESH_TOKEN を上書きすればOK）

    pip install google-auth-oauthlib
    python pipeline/get_refresh_token.py client_secret.json

表示された3つの値を GitHub の Settings → Secrets and variables → Actions に登録する。
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

if len(sys.argv) != 2:
    sys.exit(__doc__)
SCOPES = [
    "https://www.googleapis.com/auth/drive",                  # 素材の取得・完成動画の納品
    "https://www.googleapis.com/auth/youtube.readonly",       # 動画タイトルの取得（閲覧のみ）
    "https://www.googleapis.com/auth/yt-analytics.readonly",  # 再生数・視聴率（閲覧のみ）
]
flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
info = json.load(open(sys.argv[1]))["installed"]
print("\n以下を GitHub Secrets に登録してください:\n")
print(f"GDRIVE_CLIENT_ID     = {info['client_id']}")
print(f"GDRIVE_CLIENT_SECRET = {info['client_secret']}")
print(f"GDRIVE_REFRESH_TOKEN = {creds.refresh_token}")
if not creds.refresh_token:
    print("\n※ REFRESH_TOKEN が空です。https://myaccount.google.com/permissions でこのアプリを削除してから再実行してください")
