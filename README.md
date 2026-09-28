# 🌍✨ ミニチュアTikTok 自動運用システム（AI社員チーム）

TikTok [@sho1249003](https://www.tiktok.com/@sho1249003)
「小さな世界で大きなエネルギーを！ミニチュアの向こうをハイテンションにお届け！」を
**副業の短い時間でも毎週回せる**ようにした仕組みです。

```
[左腕が毎週土曜に自動実行]
市場調査 → 台本 → 構成 → AI素材生成 → 動画作成(テロップ・効果音・演出) → 品質チェック → ドライブ納品
 リサ     ツムギ   カット   Gemini+Seedance   ヘンシュ                          チェック       ポスト
                                                                              ↓
                                                        [社長 週30分] 確認 → 予約投稿 → 数値を送る
```

## 社長（あなた）がやること：週30分
1. 日曜にドライブ「完成動画」で4本を確認（10分）
2. TikTok Studio で予約投稿（15分）
3. 数値のスクショを Claude に送る（5分）

最初の1回だけ [docs/05_setup.md](docs/05_setup.md) の初期設定（約40分）が必要です。詳細は [docs/02_workflow.md](docs/02_workflow.md)。

## 中身
| パス | 内容 |
|---|---|
| `.claude/agents/` | AI社員6名（調査・台本・構成/AI素材指定・編集・品質管理・投稿） |
| `.claude/skills/make-video` | 全工程を1コマンドで回す進行役 |
| `.claude/skills/weekly-review` | 週次の数値振り返り→勝ちパターン更新 |
| `pipeline/render.py` | 構成表(plan.json)→縦型動画。テロップ6種・ズーム/パン/揺れ・フラッシュ・効果音合成・カバー画像 |
| `pipeline/generate.py` | AI素材生成：Gemini（Nano Banana）画像 → Seedance 動画化 / Pexels フリー素材 |
| `.claude/skills/autopilot` | 左腕（毎週の自動ルーチン）の業務手順 |
| `pipeline/qa.py` | 伸びる型のルールで自動チェック（冒頭フック・尺・文字数・CTA・ハッシュタグ） |
| `pipeline/drive.py` | Googleドライブから素材取得 / 完成動画を納品 |
| `.github/workflows/render.yml` | push で 品質チェック→書き出し→納品 を自動実行 |
| `content/<日付>_epNNN_*/` | 1本ごとの research / script / plan.json / caption / 投稿チェックリスト |
| `docs/` | 市場調査・業務フロー・ツール一覧・ブランドガイド・初期設定・数値ログ |

## ローカルで動かす場合
```bash
bash pipeline/setup.sh
python pipeline/qa.py content/2026-09-27_ep001_mini_ramen
python pipeline/render.py content/2026-09-27_ep001_mini_ramen/plan.json   # → output/ に mp4
```
素材が無いカットは「撮影指示付きの仮画面」で書き出されるので、構成の確認にもそのまま使えます。

