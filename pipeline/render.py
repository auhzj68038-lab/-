#!/usr/bin/env python3
"""ミニチュア動画 自動編集エンジン（AI社員「編集部 カット」の手足）

plan.json（構成表）を読み込み、縦型 1080x1920 の TikTok 用 mp4 を書き出す。
- 素材: 動画 / 画像（ズーム・パン付き）/ 素材が無い場合はプレースホルダー
- テロップ: 縁取り＋ポップイン演出、スタイル別の色
- 効果音: pop / whoosh / ding / boom をコードで合成（著作権フリー）
- 出力: 動画 mp4、サムネ png、確認用コンタクトシート png

使い方:
    python pipeline/render.py content/2026-09-26_sample/plan.json
    python pipeline/render.py content/.../plan.json --preview   # 低画質で高速確認
"""
from __future__ import annotations

import argparse
import json
import math
import re
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SR = 44100

# ---------------------------------------------------------------- フォント
FONT_CANDIDATES = [
    ROOT / "pipeline/fonts/DelaGothicOne-Regular.ttf",
    ROOT / "pipeline/fonts/MPLUSRounded1c-ExtraBold.ttf",
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"),
    Path("/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"),
    Path("C:/Windows/Fonts/meiryob.ttc"),
    Path("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"),
    Path("/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"),
]


def find_font() -> str:
    env = os.environ.get("TELOP_FONT")
    if env and Path(env).exists():
        return env
    for p in FONT_CANDIDATES:
        if p.exists():
            return str(p)
    sys.exit("日本語フォントが見つかりません。pipeline/setup.sh を実行するか TELOP_FONT を指定してください")


# ---------------------------------------------------------------- テロップのスタイル
STYLES = {
    # 文字色, 縁色, 背景帯色(None=帯なし), サイズ倍率
    "hook":     dict(fill="#FFE600", stroke="#000000", band=None,       scale=1.25),
    "normal":   dict(fill="#FFFFFF", stroke="#000000", band=None,       scale=1.0),
    "punch":    dict(fill="#FF2D55", stroke="#FFFFFF", band=None,       scale=1.35),
    "question": dict(fill="#FFFFFF", stroke="#0066FF", band="#0066FFCC", scale=1.0),
    "info":     dict(fill="#000000", stroke="#FFFFFF", band="#FFFFFFE6", scale=0.8),
    "cta":      dict(fill="#FFFFFF", stroke="#FF0050", band="#FF0050E6", scale=0.95),
}
# TikTok の UI に被らない安全領域（上 150px / 下 380px / 右 140px を避ける）
POSITIONS = {"top": 0.20, "center": 0.46, "bottom": 0.68}


def hex_rgba(h: str) -> tuple[int, ...]:
    h = h.lstrip("#")
    if len(h) == 6:
        h += "FF"
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))


@dataclass
class Telop:
    text: str
    style: str = "normal"
    position: str = "center"


EMOJI_RE = re.compile("[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F\u200D]")


def strip_emoji(text: str) -> str:
    """テロップ用フォントは絵文字を描けないので除去（絵文字は投稿文で使う）"""
    return EMOJI_RE.sub("", text).strip()


def render_telop(t: Telop, W: int, font_path: str) -> Image.Image:
    """テロップ1枚を RGBA 画像で返す（改行 \\n 対応）"""
    st = STYLES.get(t.style, STYLES["normal"])
    t = Telop(strip_emoji(t.text), t.style, t.position)
    size = int(W * 0.085 * st["scale"])
    font = ImageFont.truetype(font_path, size)
    lines = t.text.split("\n")
    # 横幅に収まるまで縮小
    max_w = W * 0.86
    while True:
        widths = [font.getbbox(l, stroke_width=size // 7)[2] for l in lines]
        if max(widths) <= max_w or size < 30:
            break
        size = int(size * 0.92)
        font = ImageFont.truetype(font_path, size)
    stroke = max(4, size // 7)
    line_h = int(size * 1.25)
    pad = int(size * 0.45)
    w = int(max(widths)) + pad * 2
    h = line_h * len(lines) + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if st["band"]:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(size * 0.35), fill=hex_rgba(st["band"]))
    else:  # 帯なしの時は影で視認性を上げる
        shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        for i, l in enumerate(lines):
            lw = font.getbbox(l, stroke_width=stroke)[2]
            sd.text(((w - lw) / 2 + 6, pad + i * line_h + 8), l, font=font, fill=(0, 0, 0, 160),
                    stroke_width=stroke, stroke_fill=(0, 0, 0, 160))
        img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        lw = font.getbbox(l, stroke_width=stroke)[2]
        d.text(((w - lw) / 2, pad + i * line_h), l, font=font, fill=hex_rgba(st["fill"]),
               stroke_width=stroke, stroke_fill=hex_rgba(st["stroke"]))
    return img


# ---------------------------------------------------------------- 素材
def resolve_source(src, base: Path):
    """素材の場所: footage/<エピソード名>/ → エピソードフォルダ → リポジトリ直下 の順に探す"""
    if not src:
        return None
    for p in (ROOT / "footage" / base.name / src, base / src, ROOT / src, Path(src)):
        if p.exists():
            return p
    # AI生成で拡張子が変わった素材（01_hook.mp4 の代わりに 01_hook.png 等）も拾う
    stem = ROOT / "footage" / base.name / Path(src).stem
    for ext in (".mp4", ".mov", ".png", ".jpg", ".jpeg", ".webp"):
        if stem.with_suffix(ext).exists():
            return stem.with_suffix(ext)
    return None


class Source:
    """シーンの背景映像。frame(t) で RGB ndarray (H,W,3) を返す"""

    def __init__(self, scene: dict, W: int, H: int, base: Path):
        self.W, self.H = W, H
        self.effect = scene.get("effect", "none")
        self.duration = float(scene["duration"])
        self.speed = float(scene.get("speed", 1.0))
        self.start = float(scene.get("start", 0))
        self.clip = None
        self.still = None
        src = scene.get("source")
        path = resolve_source(src, base)
        if path and path.suffix.lower() in (".mp4", ".mov", ".m4v", ".webm", ".avi"):
            from moviepy import VideoFileClip
            self.clip = VideoFileClip(str(path), audio=False)
        elif path and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            self.still = self._cover(Image.open(path).convert("RGB"), 1.25)
        else:
            self.still = self._placeholder(scene.get("placeholder", {}), scene.get("source"))

    def _cover(self, img: Image.Image, extra: float = 1.0) -> Image.Image:
        """9:16 に中央クロップ（ズーム用に extra 倍の余白を持つ）"""
        W, H = int(self.W * extra), int(self.H * extra)
        r = max(W / img.width, H / img.height)
        img = img.resize((math.ceil(img.width * r), math.ceil(img.height * r)), Image.LANCZOS)
        l, t = (img.width - W) // 2, (img.height - H) // 2
        return img.crop((l, t, l + W, t + H))

    def _placeholder(self, ph: dict, src) -> Image.Image:
        """素材未撮影時の仮画面（撮影指示を表示）"""
        W, H = int(self.W * 1.25), int(self.H * 1.25)
        c1 = np.array(hex_rgba(ph.get("color", "#2B2D6E"))[:3], dtype=np.float32)
        c2 = np.array(hex_rgba(ph.get("color2", "#FF7AB6"))[:3], dtype=np.float32)
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        x = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
        g = np.clip(y * 0.8 + x * 0.2, 0, 1)
        arr = (c1 * (1 - g) + c2 * g).astype(np.uint8)
        img = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).copy()).convert("RGBA")
        # ミニチュア撮影っぽい玉ボケ
        bokeh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(bokeh)
        rng = np.random.default_rng(sum(map(ord, ph.get("label", "x"))))
        for _ in range(22):
            cx, cy, r = rng.integers(0, W), rng.integers(0, H), rng.integers(20, 110)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, int(rng.integers(25, 70))))
        img = Image.alpha_composite(img, bokeh.filter(ImageFilter.GaussianBlur(10)))
        label = ph.get("label") or (f"素材待ち: {src}" if src else "")
        if label:  # 撮影指示を画面下部の安全領域に表示
            font = ImageFont.truetype(find_font(), int(self.W * 0.04))
            d = ImageDraw.Draw(img)
            text = "撮影: " + label
            tw = font.getbbox(text)[2]
            x, y = (W - tw) / 2, H / 2 + self.H * 0.30
            pad = self.W * 0.02
            d.rounded_rectangle([x - pad, y - pad, x + tw + pad, y + self.W * 0.04 + pad * 1.3],
                                radius=int(pad), fill=(0, 0, 0, 140))
            d.text((x, y), text, font=font, fill=(255, 255, 255))
        return img.convert("RGB")

    def frame(self, t: float) -> np.ndarray:
        p = t / max(self.duration, 1e-6)  # 0→1 進行度
        if self.clip is not None:
            ct = min(self.start + t * self.speed, self.clip.duration - 0.05)
            img = self._cover(Image.fromarray(self.clip.get_frame(ct)), 1.12)
        else:
            img = self.still
        zoom = {"zoom_in": 1.0 + 0.10 * p, "zoom_out": 1.10 - 0.10 * p,
                "punch": 1.0 + 0.12 * max(0.0, 1 - p * 6)}.get(self.effect, 1.0)
        big_w, big_h = img.size
        # 表示範囲（元画像サイズに対する割合で計算）
        vw = big_w / (1.25 if self.clip is None else 1.12) / zoom
        vh = vw * self.H / self.W
        cx, cy = big_w / 2, big_h / 2
        if self.effect == "pan_right":
            cx = big_w / 2 - (big_w - vw) / 2 * (1 - 2 * p) * 0.9
        elif self.effect == "pan_up":
            cy = big_h / 2 + (big_h - vh) / 2 * (1 - 2 * p) * 0.9
        if self.effect == "shake":
            cx += math.sin(t * 55) * big_w * 0.012
            cy += math.cos(t * 47) * big_h * 0.012
        box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
        out = img.resize((self.W, self.H), Image.BILINEAR, box=box)
        return np.asarray(out)

    def close(self):
        if self.clip is not None:
            self.clip.close()


# ---------------------------------------------------------------- 効果音（合成）
def sfx(kind: str) -> np.ndarray:
    def env(n, a=0.005, d=0.15):
        t = np.arange(n) / SR
        return np.minimum(t / a, 1) * np.exp(-t / d)

    if kind == "pop":
        n = int(SR * 0.12); t = np.arange(n) / SR
        f = 900 * np.exp(-t * 25) + 300
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.04)
    elif kind == "whoosh":
        n = int(SR * 0.35); t = np.arange(n) / SR
        noise = np.random.default_rng(1).standard_normal(n)
        k = np.convolve(noise, np.ones(30) / 30, "same")
        s = k * np.sin(np.pi * t / t[-1]) * 1.8
    elif kind == "ding":
        n = int(SR * 0.6); t = np.arange(n) / SR
        s = (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 2637 * t)) * env(n, 0.002, 0.25) * 0.5
    elif kind == "boom":
        n = int(SR * 0.5); t = np.arange(n) / SR
        f = 120 * np.exp(-t * 6) + 40
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.2)
    else:
        return np.zeros(1)
    return (s * 0.6).astype(np.float32)


def build_audio(plan: dict, scenes: list[dict], total: float, base: Path) -> np.ndarray:
    audio = np.zeros(int(total * SR) + SR, dtype=np.float32)
    t0 = 0.0
    for sc in scenes:
        for kind in ([sc["sfx"]] if isinstance(sc.get("sfx"), str) else sc.get("sfx", [])):
            s = sfx(kind)
            i = int(t0 * SR)
            audio[i:i + len(s)] += s[: len(audio) - i]
        t0 += float(sc["duration"])
    bgm = plan.get("bgm")
    if bgm:
        from moviepy import AudioFileClip
        p = base / bgm if (base / bgm).exists() else ROOT / bgm
        a = AudioFileClip(str(p)).with_fps(SR).to_soundarray(fps=SR)
        a = a.mean(axis=1) if a.ndim == 2 else a
        a = np.resize(a, len(audio)).astype(np.float32) * float(plan.get("bgm_volume", 0.35))
        audio += a
    peak = np.abs(audio).max() or 1
    audio = audio / max(peak, 1.0) * 0.95
    return np.stack([audio, audio], axis=1)


# ---------------------------------------------------------------- 合成
def pop_scale(t: float) -> float:
    """テロップのポップイン（0.18秒でオーバーシュートして着地）"""
    if t >= 0.18:
        return 1.0
    p = t / 0.18 - 1  # easeOutBack
    return 0.5 + 0.5 * (1 + 2.70158 * p ** 3 + 1.70158 * p ** 2)


def compose(plan_path: Path, preview: bool = False) -> Path:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    base = plan_path.parent
    W, H = plan.get("size", [1080, 1920])
    fps = plan.get("fps", 30)
    if preview:
        W, H, fps = W // 2, H // 2, 15
    font = find_font()
    scenes = plan["scenes"]
    sources = [Source(sc, W, H, base) for sc in scenes]
    telops = []
    for sc in scenes:
        items = sc.get("telop") or []
        items = [items] if isinstance(items, dict) else items
        telops.append([(render_telop(Telop(**{k: v for k, v in it.items() if k in ("text", "style", "position")}), W, font),
                        it.get("position", "center"), float(it.get("at", 0))) for it in items])
    starts = np.cumsum([0] + [float(s["duration"]) for s in scenes])
    total = float(starts[-1])
    flash_at = [starts[i] for i, s in enumerate(scenes) if s.get("transition") == "flash"]

    def frame_at(t: float) -> np.ndarray:
        i = min(int(np.searchsorted(starts, t, side="right") - 1), len(scenes) - 1)
        lt = t - starts[i]
        img = Image.fromarray(sources[i].frame(lt)).convert("RGBA")
        for tel, pos, at in telops[i]:
            if lt < at:
                continue
            s = pop_scale(lt - at)
            tw, th = int(tel.width * s), int(tel.height * s)
            if tw < 2 or th < 2:
                continue
            ti = tel.resize((tw, th), Image.BILINEAR) if s != 1.0 else tel
            y = int(H * POSITIONS.get(pos, 0.46) - th / 2)
            x = int((W - tw) / 2 - min(W * 0.03, (W - tw) / 2))  # 右側のボタン列を避けて少し左へ
            img.alpha_composite(ti, (max(0, x), max(0, y)))
        arr = np.asarray(img.convert("RGB")).astype(np.float32)
        for fa in flash_at:
            if 0 <= t - fa < 0.12:
                a = 1 - (t - fa) / 0.12
                arr = arr * (1 - a) + 255 * a
        return arr.astype(np.uint8)

    from moviepy import VideoClip
    from moviepy.audio.AudioClip import AudioArrayClip

    out_dir = ROOT / "output" / base.name
    out_dir.mkdir(parents=True, exist_ok=True)
    name = plan.get("output_name", base.name) + ("_preview" if preview else "")
    out = out_dir / f"{name}.mp4"
    video = VideoClip(frame_at, duration=total).with_fps(fps)
    audio = AudioArrayClip(build_audio(plan, scenes, total, base), fps=SR).with_duration(total)
    video = video.with_audio(audio)
    video.write_videofile(str(out), codec="libx264", audio_codec="aac", fps=fps,
                          preset="ultrafast" if preview else "medium",
                          ffmpeg_params=["-crf", "30" if preview else "20", "-pix_fmt", "yuv420p"],
                          logger=None)

    # サムネ（カバー画像）と確認用コンタクトシート
    cover_t = float(plan.get("cover_time", 0.3))
    Image.fromarray(frame_at(min(cover_t, total - 0.01))).save(out_dir / f"{name}_cover.png")
    n = len(scenes)
    tw, th = W // 4, H // 4
    sheet = Image.new("RGB", (tw * min(n, 5), th * math.ceil(n / 5)), "white")
    for k in range(n):
        f = Image.fromarray(frame_at(min(starts[k] + float(scenes[k]["duration"]) * 0.8, total - 0.01))).resize((tw, th))
        sheet.paste(f, ((k % 5) * tw, (k // 5) * th))
    sheet.save(out_dir / f"{name}_sheet.png")
    for s in sources:
        s.close()
    print(f"✅ 書き出し完了: {out}  ({total:.1f}秒)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", type=Path)
    ap.add_argument("--preview", action="store_true", help="半分の解像度で高速書き出し")
    a = ap.parse_args()
    compose(a.plan.resolve(), a.preview)
