#!/usr/bin/env python3
"""AI素材生成（AI社員「美術部 アート」の手足）

plan.json の各シーンで、素材（footage/<エピソード>/<source>）がまだ無いものを自動で用意する。

  "gen":   {"image": "画像プロンプト", "motion": "動きのプロンプト(任意)", "seconds": 4}
      → Gemini（Nano Banana）で 9:16 画像を生成
      → motion があれば Seedance（fal.ai）で画像を動画化
  "stock": {"query": "english keywords"}
      → Pexels のフリー素材動画（商用可）を取得

必要な環境変数（無いものはスキップして仮画面で書き出す）:
  GEMINI_API_KEY   Google AI Studio の APIキー
  FAL_KEY          fal.ai の APIキー（Seedance 用）
  PEXELS_API_KEY   Pexels の APIキー（フリー素材用・任意）
  GEMINI_IMAGE_MODEL  既定 gemini-2.5-flash-image
  FAL_VIDEO_ENDPOINT  既定 bytedance/seedance-2.0/fast/image-to-video
  MAX_MOTION_SECONDS  1本あたりの動画生成秒数の上限（既定 10 = 約$2.4）

    python pipeline/generate.py content/2026-09-27_ep001_mini_ramen
"""
import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from render import resolve_source  # noqa: E402

GEMINI_MODEL = os.environ.get("GEMINI_IMAGE_MODEL") or "gemini-2.5-flash-image"
FAL_ENDPOINT = os.environ.get("FAL_VIDEO_ENDPOINT") or "bytedance/seedance-2.0/fast/image-to-video"

# 全カット共通の世界観（ブランドの見た目をそろえる）
BASE_STYLE = (
    "Hyper-detailed handmade miniature diorama, macro photography with tilt-shift shallow depth of field, "
    "warm soft studio lighting, vivid saturated pop colors, tiny hand-crafted props made of clay and resin, "
    "a real human fingertip or a coin nearby for scale when natural, vertical 9:16 composition, "
    "subject centered with empty space at top and bottom for captions, no text, no letters, no logos, no watermark"
)


def http(url, data=None, headers=None, method=None, timeout=300):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw[:1] in (b"{", b"[") else raw


def gemini_image(prompt: str, style: str, ref: Path | None) -> bytes:
    parts = [{"text": f"{prompt}. {style}"}]
    if ref and ref.exists():  # マスコット等の参照画像で見た目を統一
        mime = "image/png" if ref.suffix == ".png" else "image/jpeg"
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(ref.read_bytes()).decode()}})
    res = http(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        {"contents": [{"parts": parts}],
         "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": "9:16"}}},
        {"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    for part in res["candidates"][0]["content"]["parts"]:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline:
            return base64.b64decode(inline["data"])
    raise RuntimeError(f"Gemini が画像を返しませんでした: {json.dumps(res)[:300]}")


def seedance_video(png: bytes, motion: str, seconds: int) -> bytes:
    auth = {"Authorization": f"Key {os.environ['FAL_KEY']}"}
    job = http(f"https://queue.fal.run/{FAL_ENDPOINT}", {
        "prompt": motion + ". Miniature diorama world, smooth macro camera, keep the scene tiny and handmade.",
        "image_url": "data:image/png;base64," + base64.b64encode(png).decode(),
        "duration": str(max(4, seconds)), "aspect_ratio": "9:16", "resolution": "720p",
        "generate_audio": False,
    }, auth)
    for _ in range(120):  # 最大10分待つ
        st = http(job["status_url"], headers=auth)
        if st.get("status") == "COMPLETED":
            break
        time.sleep(5)
    else:
        raise TimeoutError("Seedance がタイムアウトしました")
    result = http(job["response_url"], headers=auth)
    return urllib.request.urlopen(result["video"]["url"], timeout=300).read()


def pexels_video(query: str) -> tuple[bytes, str]:
    q = urllib.parse.quote(query)
    res = http(f"https://api.pexels.com/videos/search?query={q}&orientation=portrait&per_page=5",
               headers={"Authorization": os.environ["PEXELS_API_KEY"]})
    for v in res.get("videos", []):
        files = sorted((f for f in v["video_files"] if f.get("height") and f["height"] <= 1920),
                       key=lambda f: -f["height"])
        if files:
            credit = f"Video by {v['user']['name']} from Pexels ({v['url']})"
            return urllib.request.urlopen(files[0]["link"], timeout=300).read(), credit
    raise RuntimeError(f"Pexels に「{query}」の縦動画がありません")


def main(ep_dir: Path) -> int:
    plan = json.loads((ep_dir / "plan.json").read_text(encoding="utf-8"))
    out = ROOT / "footage" / ep_dir.name
    out.mkdir(parents=True, exist_ok=True)
    style = plan.get("style") or BASE_STYLE
    ref = ROOT / plan["style_ref"] if plan.get("style_ref") else None
    budget = float(os.environ.get("MAX_MOTION_SECONDS", "10"))
    credits = []
    for i, sc in enumerate(plan["scenes"], 1):
        src = sc.get("source")
        if not src or resolve_source(src, ep_dir):
            continue
        stem = Path(src).stem
        try:
            if sc.get("stock") and os.environ.get("PEXELS_API_KEY"):
                data, credit = pexels_video(sc["stock"]["query"])
                (out / f"{stem}.mp4").write_bytes(data)
                credits.append(credit)
                print(f"🎞️  シーン{i}: Pexels「{sc['stock']['query']}」")
            elif sc.get("gen") and os.environ.get("GEMINI_API_KEY"):
                g = sc["gen"]
                png = gemini_image(g["image"], style, ref)
                (out / f"{stem}.png").write_bytes(png)
                print(f"🖼️  シーン{i}: Gemini 画像生成")
                secs = int(g.get("seconds", 4))
                if g.get("motion") and os.environ.get("FAL_KEY") and budget >= max(4, secs):
                    (out / f"{stem}.mp4").write_bytes(seedance_video(png, g["motion"], secs))
                    budget -= max(4, secs)
                    print(f"🎬 シーン{i}: Seedance で動画化（{max(4, secs)}秒）")
            else:
                print(f"⏭️  シーン{i}: 生成設定 or APIキー無し → 仮画面")
        except Exception as e:  # 1カット失敗しても他は続ける（仮画面で書き出される）
            print(f"⚠️  シーン{i}: 生成失敗 {e}")
    if credits:  # Pexels API の利用条件：クレジット表記 → 投稿文の末尾に追記
        cap = ep_dir / "caption.txt"
        text = cap.read_text(encoding="utf-8") if cap.exists() else ""
        if "Pexels" not in text:
            cap.write_text(text.rstrip() + "\n\n素材: " + " / ".join(credits) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve()))
