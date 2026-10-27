#!/usr/bin/env python3
"""SNS 自動投稿（AI社員「投稿担当 ポスト」の手足）— YouTube Shorts と TikTok に同時公開

TikTok・YouTube の公式APIは審査を通るまで「非公開」でしか投稿できないため、
審査済みの投稿代行API「Upload-Post」（https://app.upload-post.com）を経由する。

  python pipeline/publish.py content/<エピソード>

必要な環境変数（無ければ投稿せず終了コード0。ドライブ納品だけで止まる）:
  UPLOAD_POST_API_KEY   Upload-Post の APIキー
  UPLOAD_POST_USER      Upload-Post で作ったプロフィール名（TikTok・YouTube を連携したもの）
任意:
  UPLOAD_POST_PLATFORMS 既定 "tiktok,youtube"
  POST_PRIVACY          YouTube の公開範囲 public / unlisted / private（既定 public）
  DRY_RUN=1             送らずに中身だけ表示

安全装置:
  - 投稿済みの回（content/<ep>/posted.json あり）は二度と投稿しない
  - 素材が欠けて「素材待ち」の仮画面が残っている回は投稿しない
  - 同じ回を送り直しても二重投稿にならないよう Idempotency-Key を付ける
"""
import datetime as dt
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from render import resolve_source  # noqa: E402

API = "https://api.upload-post.com/api/upload"


def multipart(fields: list[tuple[str, str]], file_field: str, path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    out = []
    for k, v in fields:
        out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\n'
               f"Content-Type: video/mp4\r\n\r\n".encode() + path.read_bytes() + b"\r\n")
    out.append(f"--{boundary}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def send(body: bytes, ctype: str, key: str, idem: str) -> dict:
    import urllib.error
    import urllib.request
    for attempt in range(3):
        req = urllib.request.Request(API, data=body, method="POST", headers={
            "Authorization": f"Apikey {os.environ['UPLOAD_POST_API_KEY']}", "Content-Type": ctype,
            "Idempotency-Key": idem, "X-Request-Id": idem})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            detail = e.read()[:500].decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503) and attempt < 2:
                print(f"   ⏳ Upload-Post HTTP {e.code} → {90 * (attempt + 1)}秒待って再試行")
                time.sleep(90 * (attempt + 1))
                continue
            raise RuntimeError(f"Upload-Post HTTP {e.code}: {detail}") from None
    return {}


def main(ep_dir: Path) -> int:
    if not (os.environ.get("UPLOAD_POST_API_KEY") and os.environ.get("UPLOAD_POST_USER")):
        print("⏭️  Upload-Post の鍵が未設定 → SNS投稿はスキップ（ドライブ納品のみ）")
        return 0
    marker = ep_dir / "posted.json"
    if marker.exists():
        print(f"⏭️  投稿済み: {marker}")
        return 0
    plan = json.loads((ep_dir / "plan.json").read_text(encoding="utf-8"))
    missing = [i for i, s in enumerate(plan["scenes"], 1) if s.get("source") and not resolve_source(s["source"], ep_dir)]
    if missing:
        print(f"❌ 素材が無いシーン {missing} があるため投稿を中止（仮画面のまま公開しない）")
        return 1
    video = ROOT / "output" / ep_dir.name / f"{plan.get('output_name', ep_dir.name)}.mp4"
    if not video.exists():
        print(f"❌ 動画がありません: {video}")
        return 1
    caption = (ep_dir / "caption.txt").read_text(encoding="utf-8").strip()
    tags = re.findall(r"#(\S+)", caption)
    platforms = [p.strip() for p in os.environ.get("UPLOAD_POST_PLATFORMS", "tiktok,youtube").split(",") if p.strip()]
    yt_title = plan["title"][:90] + (" #shorts" if "#shorts" not in plan["title"] else "")
    fields = [("user", os.environ["UPLOAD_POST_USER"]), ("title", caption[:2200])]
    fields += [("platform[]", p) for p in platforms]
    fields += [("youtube_title", yt_title[:100]), ("youtube_description", caption[:4900]),
               ("privacyStatus", os.environ.get("POST_PRIVACY", "public")), ("categoryId", "24"),
               ("selfDeclaredMadeForKids", "false")]
    fields += [("tags[]", t) for t in tags[:10]]
    if plan.get("ai_generated"):  # AI生成の開示（TikTok の AI ラベル / YouTube の合成コンテンツ申告）
        fields += [("is_aigc", "true"), ("containsSyntheticMedia", "true")]
    idem = f"{ep_dir.name}-{video.stat().st_size}"
    if os.environ.get("DRY_RUN"):
        print("🧪 DRY_RUN:", json.dumps(fields, ensure_ascii=False)[:800], video)
        return 0
    res = send(*multipart(fields, "video", video), os.environ["UPLOAD_POST_API_KEY"], idem)
    print("📮 Upload-Post:", json.dumps(res, ensure_ascii=False)[:800])
    if res.get("success") is False:
        print(f"❌ 投稿失敗: {res.get('error_code')} {res.get('error')}")
        return 1
    marker.write_text(json.dumps({"posted_at": dt.datetime.now(dt.timezone.utc).isoformat(), "platforms": platforms,
                                  "youtube_title": yt_title, "response": res}, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"✅ 投稿しました: {', '.join(platforms)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve()))
