"""Google 認証。

- 権限はスプレッドシート読み取り専用（spreadsheets.readonly）のみ。
- OAuth クライアント情報とトークンは macOS キーチェーンに保存し、平文ファイルには残さない。
"""

from __future__ import annotations

import json
from pathlib import Path

from .errors import PrepError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
KEYRING_SERVICE = "shorts_prep"
KEY_CLIENT = "oauth_client"
KEY_TOKEN = "oauth_token"


def _keyring():
    import keyring

    return keyring


def import_client_secret(path: Path) -> None:
    """Google Cloud でダウンロードした client_secret_xxx.json をキーチェーンに取り込む。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise PrepError(f"クライアント情報ファイルを読めませんでした: {path}\n{e}") from e
    if "installed" not in data:
        raise PrepError(
            "このファイルは「デスクトップ アプリ」用の OAuth クライアントではありません。\n"
            "Google Cloud Console で種類「デスクトップ アプリ」を選んで作り直してください。"
        )
    kr = _keyring()
    kr.set_password(KEYRING_SERVICE, KEY_CLIENT, json.dumps(data))
    # クライアントが変わったら古いトークンは無効
    _delete(KEY_TOKEN)


def logout() -> None:
    _delete(KEY_TOKEN)


def _delete(key: str) -> None:
    kr = _keyring()
    try:
        kr.delete_password(KEYRING_SERVICE, key)
    except kr.errors.PasswordDeleteError:
        pass


def get_credentials(interactive: bool = True):
    """有効な認証情報を返す。必要ならトークンを更新し、初回はブラウザで許可を求める。"""
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    kr = _keyring()
    creds = None
    token_json = kr.get_password(KEYRING_SERVICE, KEY_TOKEN)
    if token_json:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        except (ValueError, json.JSONDecodeError):
            creds = None
        if creds and not set(SCOPES).issubset(set(creds.scopes or [])):
            creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except RefreshError:
            creds = None  # 失効・取り消し済み → 再ログイン

    if not interactive:
        raise PrepError("Google へのログインが必要です。`shorts-prep login` を実行してください。")

    client_json = kr.get_password(KEYRING_SERVICE, KEY_CLIENT)
    if not client_json:
        raise PrepError(
            "OAuth クライアント情報が未登録です。\n"
            "`shorts-prep setup --client-secret <ダウンロードしたJSON>` を実行してください。"
        )

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(json.loads(client_json), SCOPES)
    # 127.0.0.1 の空きポートで一時的に受け取り、完了後すぐ閉じる
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        open_browser=True,
        authorization_prompt_message="ブラウザで Google アカウントの許可をしてください: {url}",
        success_message="認証が完了しました。このタブは閉じて構いません。",
    )
    _save_token(creds)
    return creds


def _save_token(creds) -> None:
    _keyring().set_password(KEYRING_SERVICE, KEY_TOKEN, creds.to_json())
