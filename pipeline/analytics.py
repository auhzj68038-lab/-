#!/usr/bin/env python3
"""アナリティクス自動フィードバック（AI社員「分析官 カズ」の手足）

YouTube Analytics API から直近28日の Shorts の成績（再生数・平均視聴率・いいね）を取得し、
docs/analytics_auto.json に保存する。autoplan.py がこれを読んで、伸びた型を次の企画に反映する。

  python pipeline/analytics.py          取得して保存（トップ3を表示）

ドライブと同じ鍵（GDRIVE_CLIENT_ID / GDRIVE_CLIENT_SECRET / GDRIVE_REFRESH_TOKEN）を使う。
鍵に YouTube の閲覧権限が無い場合は何もせず終了（get_refresh_token.py を実行し直すと有効になる）。
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "analytics_auto.json"


def creds():
    from google.oauth2.credentials import Credentials
    return Credentials(None, refresh_token=os.environ["GDRIVE_REFRESH_TOKEN"],
                       client_id=os.environ["GDRIVE_CLIENT_ID"], client_secret=os.environ["GDRIVE_CLIENT_SECRET"],
                       token_uri="https://oauth2.googleapis.com/token")


def fetch(days: int = 28, n: int = 25) -> list[dict]:
    from googleapiclient.discovery import build
    c = creds()
    yta = build("youtubeAnalytics", "v2", credentials=c, cache_discovery=False)
    yt = build("youtube", "v3", credentials=c, cache_discovery=False)
    end = dt.date.today()
    res = yta.reports().query(ids="channel==MINE", startDate=str(end - dt.timedelta(days=days)), endDate=str(end),
                              metrics="views,averageViewPercentage,likes,subscribersGained",
                              dimensions="video", sort="-views", maxResults=n).execute()
    rows = res.get("rows", [])
    if not rows:
        return []
    meta = yt.videos().list(part="snippet", id=",".join(r[0] for r in rows)).execute().get("items", [])
    titles = {m["id"]: m["snippet"]["title"] for m in meta}
    return [{"title": titles.get(r[0], r[0]), "views": int(r[1]), "avg_view_pct": round(float(r[2]), 1),
             "likes": int(r[3]), "subs": int(r[4]), "url": f"https://youtube.com/shorts/{r[0]}"} for r in rows]


def main() -> int:
    if not os.environ.get("GDRIVE_REFRESH_TOKEN"):
        print("⏭️  鍵が未設定 → アナリティクス取得はスキップ")
        return 0
    try:
        videos = fetch()
    except Exception as e:  # 権限不足・API未有効など。企画は前回のデータで続行する
        msg = str(e)
        hint = "（get_refresh_token.py を実行し直して YouTube の権限付きの鍵に更新してください）" \
            if "insufficient" in msg.lower() or "403" in msg else ""
        print(f"⚠️  YouTube アナリティクス取得失敗: {msg[:300]}{hint}")
        return 0
    OUT.write_text(json.dumps({"updated": dt.date.today().isoformat(), "period_days": 28,
                               "note": "views 降順。avg_view_pct = 平均視聴率(%)", "videos": videos},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"📊 {len(videos)}本の成績を保存: {OUT.relative_to(ROOT)}")
    for v in videos[:3]:
        print(f"   {v['views']:>7,}回  視聴率{v['avg_view_pct']}%  {v['title']}")
    return 0


def top(n: int = 3) -> list[dict]:
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))["videos"][:n]
    except Exception:
        return []


if __name__ == "__main__":
    sys.exit(main())
