#!/usr/bin/env python3
"""完全自動の企画エンジン（AI社員「リサ・ツムギ・カット」を Gemini で代行）

  python pipeline/autoplan.py pick   今日（日本時間）の回のフォルダ名を1行で出力する
      1. content/<今日の日付>_epNNN_* があり、まだ投稿していなければそれを使う（社長が作った回を優先）
      2. 無ければ Gemini で次の回（epNNN を自動採番）を企画し、research/script/plan.json/caption を作る
         品質チェック（qa.py）の ERROR が 0 になるまで最大3回、指摘を渡して作り直させる

企画には次を自動で反映する（勝ちパターンの自動フィードバック）:
  docs/01_market_research.md の勝ちパターン / docs/analytics_auto.json（YouTube の成績・analytics.py が更新）
  docs/analytics_log.md（TikTok の手入力の数値）/ docs/next_week.md（社長の指定・任意）/ 過去の回のタイトル

必要な環境変数: GEMINI_API_KEY
任意: GEMINI_TEXT_MODEL（既定 gemini-flash-latest → 失敗時 gemini-2.5-flash）
"""
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from apiutil import http  # noqa: E402
import qa  # noqa: E402

CONTENT = ROOT / "content"
MODELS = [m for m in (os.environ.get("GEMINI_TEXT_MODEL"), "gemini-flash-latest", "gemini-2.5-flash") if m]
EFFECTS = {"none", "zoom_in", "zoom_out", "punch", "shake", "pan_right", "pan_up"}
SFX = {"pop", "whoosh", "ding", "boom"}
STYLES = {"hook", "punch", "normal", "question", "info", "cta"}
POSITIONS = {"top", "center", "bottom"}


def today() -> dt.date:
    return dt.datetime.now(ZoneInfo("Asia/Tokyo")).date()


def episodes() -> list[Path]:
    return sorted(p for p in CONTENT.iterdir() if p.is_dir() and (p / "plan.json").exists())


def next_number() -> int:
    nums = [int(m.group(1)) for p in CONTENT.iterdir() if (m := re.search(r"_ep(\d{3,})", p.name))]
    return max(nums, default=0) + 1


def read(path: str, limit: int = 6000) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8")[:limit] if p.exists() else ""


def context() -> str:
    past = []
    for p in episodes()[-30:]:
        try:
            past.append(f"- {p.name}: {json.loads((p / 'plan.json').read_text(encoding='utf-8'))['title']}")
        except Exception:
            pass
    perf = read("docs/analytics_auto.json", 4000)
    return "\n\n".join(x for x in [
        f"# 今日の日付（日本時間）\n{today():%Y年%m月%d日（%a）}。季節・行事・曜日に合ったネタにする。",
        "# 社長からの指定（最優先）\n" + read("docs/next_week.md", 2000) if read("docs/next_week.md") else "",
        "# 市場調査と勝ちパターン\n" + read("docs/01_market_research.md"),
        "# YouTube Shorts の成績（再生数順。上位の型・テーマを優先し、下位の型は避ける）\n" + perf if perf else "",
        "# TikTok の手入力の数値\n" + read("docs/analytics_log.md", 3000),
        "# 過去の回（同じネタは禁止。シリーズ物として発展させるのは可）\n" + "\n".join(past),
    ] if x)


RULES = """
# 全自動モードの追加ルール（上の台本・構成ルールより優先）
- 素材は Gemini 画像生成で全自動で作る。人が写真を撮る前提の "photo" は使わない。
- 画像は1本3枚まで（source は 01_xxx.png / 02_xxx.png / 03_xxx.png）。同じ画像を crop で使い回して5〜7カットにする。
  gen はその画像が最初に出るシーンにだけ書き、gen.image は英語で具体的に（被写体・大きさ比べの小物・アングル・光）。
- 大きさ比べは「指先」「米粒」「マッチ棒」「鉛筆の先」など AI が崩しにくいもので。硬貨・紙幣・文字・ロゴ・実在の商品やキャラ・人の顔は描かせない。
- 各シーンに "voice"（ナレーションのセリフ）を付ける。キャラは「テンション高めの小人の世界の実況者」。
  日本語に "Wow!" "Oh my gosh!" "Look at this!" などの英語の感嘆を少し混ぜる。長さはカットの秒数×6文字以内。
- 総尺 12〜20秒、5〜7カット。1カット目は effect=punch・sfx=boom・hook テロップ（at=0）。最後は question + cta。
- caption に「※AI生成映像です」と #ミニチュア を含め、ハッシュタグは合計3〜6個。
- 「手作り」「制作〇時間」など実物を作ったと誤解させる表現は禁止。

# 出力（この JSON だけを返す）
{"slug": "mini_英小文字とアンダースコア", "title": "動画タイトル（30文字以内）", "pattern": "使った勝ちパターンの型",
 "research": "企画メモ（狙い・型・季節性を3〜5行）", "caption": "投稿文（改行は\\n）",
 "scenes": [{"source": "01_xxx.png", "duration": 1.5, "effect": "punch", "sfx": "boom", "transition": "flash（任意）",
   "crop": [0.1, 0.0, 0.8, 0.55], "voice": "セリフ",
   "placeholder": {"label": "何が映るか", "color": "#RRGGBB", "color2": "#RRGGBB"},
   "telop": [{"text": "1行14文字以内\\n改行可", "style": "hook", "position": "bottom", "at": 0}],
   "gen": {"image": "English prompt"}}]}
"""


def ask_gemini(prompt: str) -> dict:
    last = None
    for model in MODELS:
        try:
            res = http(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                       {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}},
                       {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=180)
            text = "".join(p.get("text", "") for p in res["candidates"][0]["content"]["parts"])
            return json.loads(text[text.index("{"):text.rindex("}") + 1])
        except Exception as e:
            last = e
            print(f"   ⚠️  {model}: {e}")
    raise RuntimeError(f"Gemini で企画できませんでした: {last}")


def clean(idea: dict) -> dict:
    """モデルの出力を render.py が読める形にそろえる（値の揺れはここで吸収）"""
    scenes = []
    for sc in idea["scenes"][:8]:
        tel = sc.get("telop") or []
        tel = [tel] if isinstance(tel, dict) else tel
        s = {"source": re.sub(r"[^\w.\-]", "_", str(sc["source"])),
             "duration": round(min(max(float(sc.get("duration", 2)), 1.0), 3.5), 2),
             "effect": sc.get("effect") if sc.get("effect") in EFFECTS else "zoom_in",
             "sfx": sc.get("sfx") if sc.get("sfx") in SFX else "pop",
             "placeholder": sc.get("placeholder") or {"label": "AI画像", "color": "#2B2D6E", "color2": "#FF7AB6"},
             "telop": [{"text": str(t["text"]), "style": t.get("style") if t.get("style") in STYLES else "normal",
                        "position": t.get("position") if t.get("position") in POSITIONS else "center",
                        "at": float(t.get("at", 0))} for t in tel if t.get("text")],
             "voice": str(sc.get("voice", ""))}
        if sc.get("transition") == "flash":
            s["transition"] = "flash"
        if isinstance(sc.get("crop"), list) and len(sc["crop"]) == 4:
            s["crop"] = [min(max(float(v), 0.0), 1.0) for v in sc["crop"]]
        if isinstance(sc.get("gen"), dict) and sc["gen"].get("image"):
            s["gen"] = {"image": str(sc["gen"]["image"])}
        scenes.append(s)
    return {**idea, "scenes": scenes}


def write(ep_dir: Path, idea: dict, num: int):
    ep_dir.mkdir(parents=True, exist_ok=True)
    plan = {"title": idea["title"], "output_name": f"ep{num:03d}_{idea['slug']}", "size": [1080, 1920],
            "fps": 30, "bgm": None, "cover_time": 0.4, "ai_generated": True, "auto": True, "voice": True,
            "look": {"handheld": True, "grain": 0.025, "vignette": 0.3}, "scenes": idea["scenes"]}
    (ep_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ep_dir / "caption.txt").write_text(idea["caption"].strip() + "\n", encoding="utf-8")
    (ep_dir / "research.md").write_text(
        f"# ep{num:03d} 企画メモ（自動企画エンジン）\n\n## {idea['title']}\n- 型: {idea.get('pattern', '')}\n\n"
        f"{idea.get('research', '')}\n", encoding="utf-8")
    rows = ["| # | 秒 | 素材 | テロップ | ナレーション | 効果音 |", "|---|---|---|---|---|---|"]
    for i, s in enumerate(idea["scenes"], 1):
        tel = " → ".join(t["text"].replace("\n", " ") for t in s["telop"])
        rows.append(f"| {i} | {s['duration']} | {s['source']} | {tel} | {s['voice']} | {s['sfx']} |")
    (ep_dir / "script.md").write_text(f"# ep{num:03d} 台本（自動）「{idea['title']}」\n\n" + "\n".join(rows) + "\n",
                                      encoding="utf-8")


def create() -> str:
    num = next_number()
    prompt = "\n\n".join([
        "あなたはミニチュア動画（TikTok / YouTube Shorts）の企画・台本・構成を1人でこなすAIチームです。今日投稿する1本を作ってください。",
        context(), read(".claude/agents/scriptwriter.md"), read(".claude/agents/director.md"), RULES])
    feedback, ep_dir = "", None
    for attempt in range(1, 4):
        idea = clean(ask_gemini(prompt + feedback))
        slug = re.sub(r"[^a-z0-9_]", "", str(idea.get("slug", "")).lower()) or "mini_auto"
        idea["slug"] = slug if slug.startswith("mini") else f"mini_{slug}"
        new_dir = CONTENT / f"{today():%Y-%m-%d}_ep{num:03d}_{idea['slug']}"
        if ep_dir and ep_dir != new_dir and ep_dir.exists():
            for f in ep_dir.iterdir():
                f.unlink()
            ep_dir.rmdir()
        ep_dir = new_dir
        write(ep_dir, idea, num)
        errors, warns, *_ = qa.collect(ep_dir)
        print(f"📝 企画案{attempt}: {idea['title']}（ERROR {len(errors)} / WARN {len(warns)}）")
        if not errors:
            return ep_dir.name
        feedback = "\n\n# 前回案の品質チェック結果（これを直した完全な JSON を出し直す）\n" + "\n".join(errors + warns)
    raise SystemExit(f"❌ 3回作り直しても品質チェックに通りませんでした: {errors}")


def needs_photo(ep_dir: Path) -> bool:
    """社長が撮る実物写真が前提の回（gen.photo あり）は、AIで描くと「実物」の表記が嘘になるので自動では扱わない"""
    plan = json.loads((ep_dir / "plan.json").read_text(encoding="utf-8"))
    return any((sc.get("gen") or {}).get("photo") for sc in plan["scenes"])


def pick() -> str:
    for p in episodes():
        if p.name.startswith(f"{today():%Y-%m-%d}_") and not (p / "posted.json").exists():
            if needs_photo(p):
                print(f"📷 {p.name} は実物写真が必要な回 → これまで通り手動運用。自動では別の回を企画します", file=sys.stderr)
                continue
            print(f"📅 今日の回が既にあります: {p.name}", file=sys.stderr)
            return p.name
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("❌ GEMINI_API_KEY が未設定のため自動企画できません")
    return create()


if __name__ == "__main__":
    if sys.argv[1:] != ["pick"]:
        sys.exit(__doc__)
    print(pick())
