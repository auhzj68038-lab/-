#!/usr/bin/env python3
"""運用結果の通知（Discord / LINE）— LINE Notify は2025年3月で終了したため Discord を推奨

  python pipeline/notify.py success <エピソード>
  python pipeline/notify.py failure <エピソード or ->

必要な環境変数（どちらか。無ければ何もしない）:
  DISCORD_WEBHOOK_URL                     Discord のチャンネル → 連携サービス → ウェブフック の URL
  LINE_CHANNEL_TOKEN + LINE_USER_ID       LINE公式アカウント（Messaging API）の長期トークンと自分のユーザーID
GitHub Actions が自動で入れる: GITHUB_SERVER_URL / GITHUB_REPOSITORY / GITHUB_RUN_ID（ログへのリンク用）
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from analytics import top  # noqa: E402
from apiutil import http  # noqa: E402


def message(status: str, ep: str) -> str:
    lines = []
    ep_dir = ROOT / "content" / ep
    title = ""
    if (ep_dir / "plan.json").exists():
        title = json.loads((ep_dir / "plan.json").read_text(encoding="utf-8"))["title"]
    if status == "success":
        posted = (ep_dir / "posted.json").exists()
        lines.append(f"✅ 本日の自動運用 成功：{title or ep}")
        if posted:
            lines.append("📮 YouTube Shorts / TikTok に投稿済み")
        elif os.environ.get("DRY_RUN"):
            lines.append("🧪 テスト実行のため SNS には投稿していません")
        else:
            lines.append("📁 ドライブ納品のみ（SNS投稿の鍵が未設定）")
        url_file = ROOT / "output" / ep / "drive_url.txt"
        if url_file.exists():
            lines.append(f"📁 {url_file.read_text().strip()}")
    else:
        lines.append(f"❌ 本日の自動運用 失敗：{title or ep}")
        lines.append("ログを確認してください（2回まで自動リトライ済み）")
    if os.environ.get("GITHUB_RUN_ID"):
        lines.append(f"🔎 {os.environ.get('GITHUB_SERVER_URL')}/{os.environ.get('GITHUB_REPOSITORY')}"
                     f"/actions/runs/{os.environ['GITHUB_RUN_ID']}")
    best = top(3)
    if best:
        lines.append("\n🏆 YouTube Shorts 再生数トップ3（直近28日）")
        for i, v in enumerate(best, 1):
            lines.append(f"{i}. {v['views']:,}回（視聴率{v['avg_view_pct']}%）{v['title']}\n   {v['url']}")
    return "\n".join(lines)


def main(status: str, ep: str) -> int:
    text = message(status, ep)
    print(text)
    sent = False
    if os.environ.get("DISCORD_WEBHOOK_URL"):
        try:
            http(os.environ["DISCORD_WEBHOOK_URL"], {"content": text[:1990]}, retries=2)  # 2000文字制限
            sent = True
        except Exception as e:
            print(f"⚠️  Discord 通知失敗: {e}")
    if os.environ.get("LINE_CHANNEL_TOKEN") and os.environ.get("LINE_USER_ID"):
        try:
            http("https://api.line.me/v2/bot/message/push",
                 {"to": os.environ["LINE_USER_ID"], "messages": [{"type": "text", "text": text[:4900]}]},
                 {"Authorization": f"Bearer {os.environ['LINE_CHANNEL_TOKEN']}"}, retries=2)
            sent = True
        except Exception as e:
            print(f"⚠️  LINE 通知失敗: {e}")
    if not sent:
        print("⏭️  通知先が未設定（DISCORD_WEBHOOK_URL など）")
    return 0  # 通知の失敗で運用全体を失敗扱いにしない


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("success", "failure"):
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
