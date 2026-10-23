#!/usr/bin/env python3
"""素材オーダー表（無料モードの要）

plan.json から「Geminiアプリ（無料）にコピペするだけ」のプロンプト集を作る。
社長はこれを見て画像を作り、ドライブ「素材/<エピソード>/」に指定のファイル名で保存するだけ。

    python pipeline/order_sheet.py content/2026-09-27_ep001_mini_ramen
      → output/<ep>/素材オーダー表.txt
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from generate import BASE_STYLE  # noqa: E402


def build(ep_dir: Path) -> Path:
    plan = json.loads((ep_dir / "plan.json").read_text(encoding="utf-8"))
    style = plan.get("style") or BASE_STYLE
    orders, seen = [], set()
    for sc in plan["scenes"]:
        src, gen = sc.get("source"), sc.get("gen")
        if not src or not gen or Path(src).stem in seen:
            continue
        seen.add(Path(src).stem)
        label = sc.get("placeholder", {}).get("label", "")
        if "切り抜き" in label:
            label = "全体の画像（あとで自動で切り抜いて複数カットに使います）"
        orders.append((Path(src).stem, gen, label))
    orders.sort(key=lambda o: o[0])

    lines = [
        f"【素材オーダー表】{plan.get('title', ep_dir.name)}",
        "",
        "■ やること（1枚1分 × %d枚）" % len(orders),
        "1. Geminiアプリ（無料）を開く → 下の「コピペ文」を1つずつ貼って送信",
        "2. できた画像を Claude のチャットに「%s の 01」のように番号を添えて送る → その場で動画にして返します" % ep_dir.name.split("_")[1],
        "   （ドライブ連携を設定済みなら、ドライブのこのフォルダに番号の名前で入れるだけでもOK）",
        "",
        "※ 気に入らない画像は、同じ会話で「もっと明るく」「もっと寄りで」と言えば作り直せます",
        "※ 人物の顔・実在のキャラクター・ブランドのロゴが入った画像は使わない",
        "",
    ]
    for i, (stem, gen, label) in enumerate(orders, 1):
        lines += [
            "=" * 40,
            f"#{i}  ファイル名: {stem.split('_')[0]}    （{label}）",
            "-" * 40,
        ]
        if gen.get("photo"):  # 本物を撮る＋Geminiで足す（AI感を消す・サイズ比較の説得力）
            lines += [
                f"① スマホで撮る：{gen['photo']}（縦向き・明るい窓際で）",
                "② Geminiアプリにその写真を添付して、次の文を送信:",
                f"この写真はそのまま使って、{gen['image']} 光と影の向きを写真に合わせて、写真に写っている本物の物は変えないで。文字は入れないで。",
                "",
            ]
        else:
            lines += [
                "コピペ文:",
                f"縦長（9:16）の画像を生成して。文字は入れないで。{gen['image']}. {style}",
                "",
            ]
        if gen.get("motion"):
            lines += [
                "（任意・余裕がある日だけ）動画にする場合：Dreamina（無料枠）の「画像から動画」に",
                f"  この画像と次の文を入れる → {gen['motion']}",
                f"  できた動画も「{stem.split('_')[0]}」の名前で入れると、画像の代わりに動画が使われます",
                "",
            ]
    out = ROOT / "output" / ep_dir.name
    out.mkdir(parents=True, exist_ok=True)
    path = out / "素材オーダー表.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📝 {path}（{len(orders)}枚）")
    return path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(Path(sys.argv[1]).resolve())
