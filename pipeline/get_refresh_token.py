#!/usr/bin/env python3
"""初回だけ自分のPCで実行し、Googleドライブ用のリフレッシュトークンを取得する。

    pip install google-auth-oauthlib
    python pipeline/get_refresh_token.py client_secret.json

表示された3つの値を GitHub の Settings → Secrets and variables → Actions に登録する。
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

if len(sys.argv) != 2:
    sys.exit(__doc__)
flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], ["https://www.googleapis.com/auth/drive"])
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
info = json.load(open(sys.argv[1]))["installed"]
print("\n以下を GitHub Secrets に登録してください:\n")
print(f"GDRIVE_CLIENT_ID     = {info['client_id']}")
print(f"GDRIVE_CLIENT_SECRET = {info['client_secret']}")
print(f"GDRIVE_REFRESH_TOKEN = {creds.refresh_token}")
