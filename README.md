# 🌍✨ ミニチュアTikTok 自動運用システム（AI社員チーム）

TikTok [@sho1249003](https://www.tiktok.com/@sho1249003)
「小さな世界で大きなエネルギーを！ミニチュアの向こうをハイテンションにお届け！」を
**副業の短い時間でも毎週回せる**ようにした仕組みです。

```
市場調査 → 台本 → 構成 → [撮影] → 動画作成（テロップ・効果音・演出） → 確認 → ドライブ納品 → 予約投稿
  リサ     ツムギ   カット   社長      ヘンシュ＋自動書き出し            チェック   ポスト       社長
```

## 社長（あなた）がやること
1. Claude（アプリ or Claude Code）でこのリポジトリを開き **`/make-video`** と送る
2. 届いた撮影リストどおりスマホで撮り、ドライブ「ミニチュアの世界/素材/<エピソード>」に入れて「素材入れた」と送る
3. ドライブ「完成動画」で確認 → TikTok Studio で予約投稿
4. 週1回 数値を送って **`/weekly-review`**

→ 週の作業は約2時間。詳細は [docs/02_workflow.md](docs/02_workflow.md)。

## 中身
| パス | 内容 |
|---|---|
| `.claude/agents/` | AI社員6名（調査・台本・構成・編集・品質管理・投稿） |
| `.claude/skills/make-video` | 全工程を1コマンドで回す進行役 |
| `.claude/skills/weekly-review` | 週次の数値振り返り→勝ちパターン更新 |
| `pipeline/render.py` | 構成表(plan.json)→縦型動画。テロップ6種・ズーム/パン/揺れ・フラッシュ・効果音合成・カバー画像 |
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

## 初期設定
ドライブ自動納品を使うには [docs/05_setup.md](docs/05_setup.md)（1回だけ・約20分）。
