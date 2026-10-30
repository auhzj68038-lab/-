#!/usr/bin/env python3
"""ナレーション音声生成（AI社員「声優 コエ」の手足）— ElevenLabs の代わりに Gemini TTS を使う

plan.json の各シーンのセリフを、テンション高めの英語まじり実況ボイスにして
footage/<エピソード>/voice_NN.wav に保存する。render.py が自動で合成する。

  セリフの決め方: シーンの "voice" → 無ければテロップの文言をつなげたもの
  plan.json に "voice": false を書いた回はナレーション無し

必要な環境変数:
  GEMINI_API_KEY   Google AI Studio の APIキー（画像生成と同じキー。無ければ何もしない）
任意:
  TTS_MODEL   既定 gemini-3.1-flash-tts-preview（失敗時は gemini-2.5-flash-preview-tts）
  TTS_VOICE   既定 Puck（明るい）。Fenrir（勢い）/ Zephyr（明るい女性）/ Leda（若い女性）など
  TTS_STYLE   話し方の指示

    python pipeline/tts.py content/2026-11-02_ep001_mini_ramen
"""
import base64
import json
import os
import re
import sys
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from apiutil import http  # noqa: E402

MODELS = [os.environ.get("TTS_MODEL") or "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"]
VOICE = os.environ.get("TTS_VOICE") or "Puck"
STYLE = os.environ.get("TTS_STYLE") or (
    "Say this like a super energetic, slightly hyped Japanese short-video host reacting to a tiny miniature world. "
    "Natural Japanese with casual English exclamations mixed in (like 'Wow!', 'Oh my gosh!', 'Look at this!'). "
    "Fast, bright, smiling voice, no long pauses:"
)
EMOJI_RE = re.compile("[\U0001F000-\U0001FFFF☀-➿️‍]")
SR = 24000  # Gemini TTS の出力は 24kHz / 16bit / mono PCM


def line_for(scene: dict) -> str:
    if "voice" in scene:
        return (scene["voice"] or "").strip()
    tel = scene.get("telop") or []
    tel = [tel] if isinstance(tel, dict) else tel
    return EMOJI_RE.sub("", " ".join(t["text"].replace("\n", "") for t in tel)).strip()


def synth(text: str) -> bytes:
    last = None
    for model in MODELS:
        try:
            res = http(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                       {"contents": [{"parts": [{"text": f"{STYLE}\n\n{text}"}]}],
                        "generationConfig": {"responseModalities": ["AUDIO"],
                                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}},
                       {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=120)
            for part in res["candidates"][0]["content"]["parts"]:
                inline = part.get("inlineData") or part.get("inline_data")
                if inline:
                    return base64.b64decode(inline["data"])
            raise RuntimeError(f"音声が返りませんでした: {json.dumps(res)[:200]}")
        except Exception as e:  # 次のモデルで再挑戦
            last = e
            print(f"   ⚠️  {model}: {e}")
    raise RuntimeError(f"TTS 失敗: {last}")


def main(ep_dir: Path) -> int:
    if not os.environ.get("GEMINI_API_KEY"):
        print("⏭️  GEMINI_API_KEY 未設定 → ナレーション無し")
        return 0
    plan = json.loads((ep_dir / "plan.json").read_text(encoding="utf-8"))
    if plan.get("voice") is False:
        print("⏭️  この回はナレーション無し（plan.json の voice=false）")
        return 0
    out = ROOT / "footage" / ep_dir.name
    out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for i, sc in enumerate(plan["scenes"], 1):
        text = line_for(sc)
        wav, memo = out / f"voice_{i:02d}.wav", out / f"voice_{i:02d}.txt"
        if not text:
            continue
        if wav.exists() and memo.exists() and memo.read_text(encoding="utf-8") == text:
            continue  # 同じセリフは作り直さない（課金を増やさない）
        try:
            pcm = synth(text)
        except Exception as e:
            print(f"❌ シーン{i}: {e}")
            failed += 1
            continue
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm)
        memo.write_text(text, encoding="utf-8")
        print(f"🎙️  シーン{i}: 「{text}」 {len(pcm) / 2 / SR:.1f}秒")
        time.sleep(1)  # 無料枠のレート制限よけ
    return 1 if failed and os.environ.get("STRICT") else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve()))
