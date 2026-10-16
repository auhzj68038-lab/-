#!/usr/bin/env python3
"""Google ドライブ連携（AI社員「投稿担当 ポスト」の手足）

  pull <episode>  : ドライブ「素材/<episode>」の撮影素材を footage/<episode>/ にダウンロード
  push <episode>  : output/<episode>/ の完成動画・サムネ・投稿文を「完成動画/<episode>」へアップロード
  order <episode> : 素材オーダー表を「素材/<episode>」に置く（社長はこれを見てGeminiアプリで画像を作る）
  changed         : 素材が新しく入った（＝書き出しが必要な）エピソード名を1行ずつ出力

必要な環境変数（初回のみ docs/05_setup.md の手順で取得）:
  GDRIVE_CLIENT_ID / GDRIVE_CLIENT_SECRET / GDRIVE_REFRESH_TOKEN
  GDRIVE_FOLDER_ID（省略時は「ミニチュアの世界」フォルダ）
"""
import io
import os
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FOLDER = "16K7ULSixWnJT8FR8Qc91tJ4MdgzpNWjm"  # ミニチュアの世界
FOLDER_MIME = "application/vnd.google-apps.folder"
ORDER_NAME = "素材オーダー表.txt"
MIMES = {".mp4": "video/mp4", ".png": "image/png", ".txt": "text/plain"}


def service():
    creds = Credentials(
        None,
        refresh_token=os.environ["GDRIVE_REFRESH_TOKEN"],
        client_id=os.environ["GDRIVE_CLIENT_ID"],
        client_secret=os.environ["GDRIVE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_or_create(svc, name: str, parent: str, create: bool = True):
    q = f"name = '{name}' and '{parent}' in parents and mimeType = '{FOLDER_MIME}' and trashed = false"
    hit = svc.files().list(q=q, fields="files(id)").execute()["files"]
    if hit:
        return hit[0]["id"]
    if not create:
        return None
    return svc.files().create(body={"name": name, "mimeType": FOLDER_MIME, "parents": [parent]},
                              fields="id").execute()["id"]


def pull(svc, root: str, episode: str):
    src = find_or_create(svc, "素材", root, create=False)
    ep = src and find_or_create(svc, episode, src, create=False)
    if not ep:
        print(f"ドライブに 素材/{episode} がありません（仮画面で書き出します）")
        return
    dest = ROOT / "footage" / episode
    dest.mkdir(parents=True, exist_ok=True)
    files = svc.files().list(q=f"'{ep}' in parents and trashed = false", fields="files(id,name)").execute()["files"]
    for f in files:
        if f["name"] == ORDER_NAME:
            continue
        with open(dest / f["name"], "wb") as fh:
            dl = MediaIoBaseDownload(fh, svc.files().get_media(fileId=f["id"]))
            done = False
            while not done:
                _, done = dl.next_chunk()
        print(f"⬇️  {f['name']}")


def upload(svc, path: Path, folder: str, name: str):
    """同名ファイルがあれば上書き（版を増やさない）"""
    q = f"name = '{name}' and '{folder}' in parents and trashed = false"
    old = svc.files().list(q=q, fields="files(id)").execute()["files"]
    media = MediaFileUpload(str(path), mimetype=MIMES[path.suffix], resumable=True)
    if old:
        svc.files().update(fileId=old[0]["id"], media_body=media).execute()
    else:
        svc.files().create(body={"name": name, "parents": [folder]}, media_body=media).execute()
    print(f"⬆️  {name}")


def push(svc, root: str, episode: str):
    out = ROOT / "output" / episode
    ep_dir = ROOT / "content" / episode
    targets = sorted(p for p in out.glob("*") if p.suffix in (".mp4", ".png") and "_preview" not in p.name)
    if (ep_dir / "caption.txt").exists():
        targets.append(ep_dir / "caption.txt")
    folder = find_or_create(svc, episode, find_or_create(svc, "完成動画", root))
    for p in targets:
        upload(svc, p, folder, "投稿文.txt" if p.name == "caption.txt" else p.name)
    print(f"https://drive.google.com/drive/folders/{folder}")


def order(svc, root: str, episode: str):
    sheet = ROOT / "output" / episode / ORDER_NAME
    folder = find_or_create(svc, episode, find_or_create(svc, "素材", root))
    upload(svc, sheet, folder, ORDER_NAME)
    print(f"https://drive.google.com/drive/folders/{folder}")


def changed(svc, root: str, _=None):
    """素材フォルダの最終更新 > 完成動画の mp4 の更新日時 なら書き出し対象"""
    src_root = find_or_create(svc, "素材", root, create=False)
    done_root = find_or_create(svc, "完成動画", root, create=False)
    if not src_root:
        return
    q = f"'{src_root}' in parents and mimeType = '{FOLDER_MIME}' and trashed = false"
    for ep in svc.files().list(q=q, fields="files(id,name)", pageSize=200).execute()["files"]:
        if not (ROOT / "content" / ep["name"] / "plan.json").exists():
            continue
        files = svc.files().list(q=f"'{ep['id']}' in parents and trashed = false",
                                 fields="files(name,modifiedTime)").execute()["files"]
        stamps = [f["modifiedTime"] for f in files if f["name"] != ORDER_NAME]
        if not stamps:
            continue
        done = done_root and find_or_create(svc, ep["name"], done_root, create=False)
        mp4 = []
        if done:
            mp4 = [f["modifiedTime"] for f in svc.files().list(
                q=f"'{done}' in parents and mimeType = 'video/mp4' and trashed = false",
                fields="files(modifiedTime)").execute()["files"]]
        if not mp4 or max(stamps) > max(mp4):
            print(ep["name"])


if __name__ == "__main__":
    cmds = {"pull": pull, "push": push, "order": order, "changed": changed}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds or (sys.argv[1] != "changed" and len(sys.argv) != 3):
        sys.exit(__doc__)
    svc = service()
    root = os.environ.get("GDRIVE_FOLDER_ID") or DEFAULT_FOLDER
    cmds[sys.argv[1]](svc, root, sys.argv[2] if len(sys.argv) > 2 else None)
