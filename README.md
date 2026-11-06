# 🌍✨ ミニチュアTikTok 自動運用システム（AI社員チーム）

TikTok [@sho1249003](https://www.tiktok.com/@sho1249003)
「小さな世界で大きなエネルギーを！ミニチュアの向こうをハイテンションにお届け！」を
**副業の短い時間でも毎週回せる**ようにした仕組みです。

```
市場調査 → 台本 → 構成 → 素材オーダー表 → [社長: Geminiアプリで画像3枚] → 動画作成(テロップ・効果音・演出) → 品質チェック → ドライブ納品
 リサ     ツムギ   カット   自動                                                ヘンシュ(自動)                     チェック       ポスト
```
**追加課金ゼロ**（Claudeの月額プラン＋無料ツールだけ）で回る設計です。

## 社長（あなた）がやること：週30分
1. 土曜：Claudeに「今週分つくって」（1分）
2. 土曜：素材オーダー表のコピペ文を Gemini アプリに貼って画像を作り、ドライブへ（12分）
3. 日曜：完成動画を確認 → TikTok Studio で予約投稿（15分）
4. 日曜：数値のスクショを Claude に送る（3分）

最初の1回だけ [docs/05_setup.md](docs/05_setup.md) の初期設定（約25分・カード登録なし）が必要です。詳細は [docs/02_workflow.md](docs/02_workflow.md)。

### 全自動モード（任意・月3,000円前後）
毎日19:00に「企画→画像→ナレーション→動画→ドライブ→YouTube Shorts / TikTok 投稿→Discord通知」まで無人で回します。設定は [docs/05_setup.md](docs/05_setup.md) 後半の「全自動モード」。

## 中身
| パス | 内容 |
|---|---|
| `.claude/agents/` | AI社員6名（調査・台本・構成/AI素材指定・編集・品質管理・投稿） |
| `.claude/skills/make-video` | 全工程を1コマンドで回す進行役 |
| `.claude/skills/weekly-review` | 週次の数値振り返り→勝ちパターン更新 |
| `pipeline/render.py` | 構成表(plan.json)→縦型動画。テロップ6種・ズーム/パン/揺れ・フラッシュ・効果音合成・カバー画像 |
| `pipeline/order_sheet.py` | 素材オーダー表：Geminiアプリにコピペするだけのプロンプト集 |
| `pipeline/generate.py` | （将来用・有料API）Gemini API / Seedance API で素材も全自動化。鍵を入れない限り動かない |
| `.claude/skills/autopilot` | 「今週分つくって」の業務手順 |
| `pipeline/qa.py` | 伸びる型のルールで自動チェック（冒頭フック・尺・文字数・CTA・ハッシュタグ） |
| `pipeline/autoplan.py` | 全自動：今日の回を決め、無ければ Gemini で次の番号の回を企画（成績を反映・品質チェックまで自動） |
| `pipeline/tts.py` | 全自動：テンション高め・英語まじりのナレーションを Gemini TTS で生成 |
| `pipeline/publish.py` | 全自動：Upload-Post 経由で YouTube Shorts / TikTok に投稿（二重投稿・仮画面の投稿を防止） |
| `pipeline/analytics.py` | 全自動：YouTube の成績を取得し docs/analytics_auto.json に保存 → 次の企画に反映 |
| `pipeline/notify.py` | 全自動：成功・失敗と再生数トップ3を Discord（または LINE）に通知 |
| `.github/workflows/daily-auto.yml` | 全自動：毎日19:00に上をすべて実行（429等は最大2回リトライ）。Variables の AUTO_MODE=on で開始 |
| `pipeline/drive.py` | Googleドライブから素材取得 / 完成動画を納品 |
| `.github/workflows/render.yml` | push と2時間ごとに 品質チェック→素材取得→書き出し→納品 を自動実行（無料） |
| `content/<日付>_epNNN_*/` | 1本ごとの research / script / plan.json / caption / 投稿チェックリスト |
| `livestream/` | AIキャラの全自動ライブ配信（毎日22〜23時・わんコメ→OpenAI→VOICEVOX→VTube Studio/OBS） |
| `docs/` | 市場調査・業務フロー・ツール一覧・ブランドガイド・初期設定・数値ログ |

## ローカルで動かす場合
```bash
bash pipeline/setup.sh
python pipeline/qa.py content/2026-11-02_ep001_mini_ramen
python pipeline/render.py content/2026-11-02_ep001_mini_ramen/plan.json   # → output/ に mp4
```
素材が無いカットは「撮影指示付きの仮画面」で書き出されるので、構成の確認にもそのまま使えます。

