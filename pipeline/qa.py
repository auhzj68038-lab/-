#!/usr/bin/env python3
"""品質チェック（AI社員「品質管理 チェック」の手足）

plan.json と caption.txt を TikTok で伸びる型のルールに照らして自動チェックする。
ERROR が1つでもあれば終了コード 1（GitHub Actions で書き出しを止める）。

    python pipeline/qa.py content/2026-09-27_ep001_mini_ramen
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from render import resolve_source  # noqa: E402
EMOJI_RE = re.compile("[\U0001F000-\U0001FFFF☀-➿]")


def check(ep_dir: Path) -> int:
    errors, warns, infos = [], [], []
    plan = json.loads((ep_dir / "plan.json").read_text(encoding="utf-8"))
    scenes = plan["scenes"]
    total = sum(float(s["duration"]) for s in scenes)

    # 尺: 完走率を取るため 10〜25 秒が勝ち筋
    if not 7 <= total <= 60:
        errors.append(f"総尺 {total:.1f}秒（7〜60秒にすること）")
    elif not 10 <= total <= 25:
        warns.append(f"総尺 {total:.1f}秒（推奨 10〜25秒）")

    # 冒頭 1.5 秒以内のフック
    first = scenes[0]
    t0 = first.get("telop") or []
    t0 = [t0] if isinstance(t0, dict) else t0
    if float(first["duration"]) > 2.0:
        warns.append("1カット目が2秒超。冒頭はテンポ最優先")
    if not any(t.get("style") in ("hook", "punch") and float(t.get("at", 0)) <= 0.3 for t in t0):
        errors.append("冒頭0.3秒以内に hook/punch スタイルのテロップが無い（離脱の最大要因）")

    for i, s in enumerate(scenes, 1):
        if float(s["duration"]) > 3.5:
            warns.append(f"シーン{i}: {s['duration']}秒は長い（3.5秒以内でカット推奨）")
        tel = s.get("telop") or []
        for t in [tel] if isinstance(tel, dict) else tel:
            for line in t["text"].split("\n"):
                if len(line) > 14:
                    warns.append(f"シーン{i}: 1行{len(line)}文字「{line}」（14文字以内推奨・\\nで改行）")
            if EMOJI_RE.search(t["text"]):
                infos.append(f"シーン{i}: テロップの絵文字は自動で除去されます")
        src = s.get("source")
        if src and not resolve_source(src, ep_dir):
            infos.append(f"シーン{i}: 素材未着 footage/{ep_dir.name}/{src} → 仮画面で書き出し")

    last = scenes[-1].get("telop") or []
    last = [last] if isinstance(last, dict) else last
    if not any(t.get("style") in ("cta", "question") for t in last):
        errors.append("最後のシーンに cta/question テロップが無い（コメント・フォロー導線）")

    cap = ep_dir / "caption.txt"
    if not cap.exists():
        errors.append("caption.txt（投稿文）が無い")
    else:
        text = cap.read_text(encoding="utf-8")
        tags = re.findall(r"#\S+", text)
        if not 3 <= len(tags) <= 6:
            warns.append(f"ハッシュタグ {len(tags)}個（3〜6個推奨）")
        if "#ミニチュア" not in tags:
            warns.append("#ミニチュア が入っていない")
        if len(text) > 2200:
            errors.append("投稿文が2200文字超")
        if plan.get("ai_generated") and "#AI" not in text and "AI生成" not in text:
            errors.append("AI生成素材を使う回は投稿時に「AI生成コンテンツ」ラベルON＋本文で明記")

    print(f"=== QA: {ep_dir.name}  総尺 {total:.1f}秒 / {len(scenes)}カット ===")
    for tag, items in (("❌ ERROR", errors), ("⚠️  WARN ", warns), ("ℹ️  INFO ", infos)):
        for m in items:
            print(f"{tag} {m}")
    print("✅ 合格" if not errors else "🚫 不合格：ERROR を直してから書き出し")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(check(Path(sys.argv[1]).resolve()))
