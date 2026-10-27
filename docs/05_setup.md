# 初期設定ガイド（追加課金ゼロ版・PCで約25分・最初の1回だけ）

## お金について（最初に）
- **使うものは全部無料枠**：Claude（今の月額プラン内）／GitHub Actions（公開リポジトリは無料・無制限）／Google ドライブ（無料15GB）／Google Cloud の Drive API（無料）／Gemini アプリ（無料）／Dreamina（毎日の無料クレジット）
- **クレジットカードはどこにも登録しません。** カードを登録していなければ、どのサービスも課金のしようがありません。
- Google Cloud で「お支払いアカウントを設定しますか？」「無料トライアルを開始」と出ても **すべて無視（閉じる）** でOK。

やることは「ドライブの合鍵3つを作って、GitHub の金庫に入れる」だけです。

---

## ステップ1：GitHub の金庫を開く（2分）
1. PCのブラウザで https://github.com/auhzj68038-lab/- を開く（GitHubにログイン）
2. 上のタブ **Settings**（歯車）→ 左メニュー **Secrets and variables** → **Actions**
3. このタブは開いたままにしておく（ステップ4で使う）

## ステップ2：Google Cloud で「ドライブの合鍵の発行元」を作る（10分）
1. 別タブで https://console.cloud.google.com/ を開き、ドライブと同じGoogleアカウントでログイン
   - 初回は利用規約に同意（国：日本）。**無料トライアルの案内は閉じる**
2. 画面上部の「プロジェクトを選択」→ **新しいプロジェクト** → 名前 `mini-tiktok` → **作成** → 作ったプロジェクトを選択
3. 上の検索窓に `Google Drive API` → 出てきた **Google Drive API** → **有効にする**
4. 左上 ≡ メニュー → **APIとサービス** → **OAuth 同意画面**（「Google Auth Platform」と表示されたら **開始**）
   - アプリ名：`mini-tiktok`／ユーザーサポートメール：自分のGmail → 次へ
   - 対象：**外部** → 次へ
   - 連絡先：自分のGmail → 次へ → 同意にチェック → **作成**
5. 左メニュー **対象**（Audience）→ 公開ステータスの **アプリを公開** → **確認**
   - ⚠️ これをしないと7日で合鍵が切れます（「確認が必要」と出ても自分専用なのでそのままでOK）
6. 左メニュー **クライアント** → **クライアントを作成**
   - アプリケーションの種類：**デスクトップ アプリ**／名前：`mini-tiktok` → **作成**
   - 出てきた画面の **JSON をダウンロード** → ファイル名を `client_secret.json` に変える

## ステップ3：自分のPCで合鍵を取り出す（10分）
1. Python が無ければ https://www.python.org/downloads/ からインストール
   - Windows は最初の画面で **「Add python.exe to PATH」にチェック** を忘れずに
2. https://github.com/auhzj68038-lab/- の緑の **Code → Download ZIP** → 解凍
3. 解凍したフォルダに `client_secret.json` を入れる
4. そのフォルダでコマンド画面を開く
   - Windows：フォルダ上部のアドレス欄に `cmd` と入力して Enter
   - Mac：フォルダを右クリック →「フォルダに新規ターミナル」
5. 次の2行を1行ずつ貼って Enter
   ```
   pip install google-auth-oauthlib
   python pipeline/get_refresh_token.py client_secret.json
   ```
6. ブラウザが開く → 自分のアカウント →「このアプリは Google で確認されていません」→ **詳細** → **mini-tiktok（安全ではないページ）に移動** → **続行**
   （自分で作った自分専用アプリなので問題ありません）
7. コマンド画面に3行表示される（GDRIVE_CLIENT_ID / GDRIVE_CLIENT_SECRET / GDRIVE_REFRESH_TOKEN）

## ステップ4：GitHub の金庫に入れる（3分）
ステップ1のタブで **New repository secret** を3回：
| Name | Secret |
|---|---|
| `GDRIVE_CLIENT_ID` | 表示された値 |
| `GDRIVE_CLIENT_SECRET` | 表示された値 |
| `GDRIVE_REFRESH_TOKEN` | 表示された値 |

終わったら `client_secret.json` は削除してOK（**人に送らない・アップしない**）。

## ステップ5：試運転（3分）
1. GitHub の上のタブ **Actions** → 左の **render-and-deliver** → 右の **Run workflow**
2. episode 欄に `2026-09-27_ep001_mini_ramen` → 緑の **Run workflow**
3. 5分ほどで ✅ になり、ドライブに次の2つが届けば成功：
   - 「素材 / 2026-09-27_ep001_mini_ramen / 素材オーダー表.txt」
   - 「完成動画 / 2026-09-27_ep001_mini_ramen / 動画（仮画面）」
4. あとは素材オーダー表どおり Gemini アプリで画像を3枚作って「素材」フォルダに入れるだけ → 2時間以内に本番の動画が届きます

❌ 赤くなったら、その画面のスクショを Claude に送ってください。

---

## 有料APIを使いたくなったら（今はやらない）
将来「画像作りも全部自動にしたい」となったら、Gemini API（画像1枚 約6円）や Seedance API（1秒 約36円）の鍵を
GitHub の金庫に `GEMINI_API_KEY` / `FAL_KEY` で入れるだけで、全自動モードに切り替わります。鍵を入れない限り一切呼ばれません。

---

# 全自動モード（毎日19:00に 企画→画像→ナレーション→動画→ドライブ→YouTube Shorts / TikTok 投稿→Discord通知）

`.github/workflows/daily-auto.yml` が担当します。**Variables に `AUTO_MODE = on` を入れるまで定期実行は始まりません。**
ElevenLabs は使わず、ナレーションも Gemini（同じ APIキー）で作ります。

## お金（1日1本・月30本の目安）
| 項目 | 月額 |
|---|---|
| Gemini（企画・画像3枚/本・ナレーション） | 約500〜1,300円 |
| Upload-Post（YouTube＋TikTok 投稿代行・TikTokは有料プランのみ） | 約2,300円〜（契約前に公式サイトで最新料金を確認） |
| GitHub Actions / Google ドライブ / Discord | 0円 |

Google AI Studio の「お支払い」で **月の予算アラート（例：1,500円）** を必ず設定してください。

## ステップA：Gemini の APIキー（5分）
1. https://aistudio.google.com/apikey → **APIキーを作成**（ステップ2と同じプロジェクト `mini-tiktok` を選ぶ）
2. 画像生成は有料枠が必要なため、AI Studio の「お支払い」でカードを登録し、予算アラートを設定
3. GitHub の **New repository secret**：`GEMINI_API_KEY`

## ステップB：ドライブの鍵を YouTube 分析対応に作り直す（10分・任意だが推奨）
伸びた動画の傾向を次の企画に自動反映するために必要です。
1. Google Cloud（プロジェクト `mini-tiktok`）で **YouTube Data API v3** と **YouTube Analytics API** を「有効にする」
2. ステップ3と同じ手順で `python pipeline/get_refresh_token.py client_secret.json` を実行し、
   ブラウザでは **YouTube チャンネルを持つアカウント** を選ぶ（チャンネル選択が出たら投稿先のチャンネル）
3. 表示された `GDRIVE_REFRESH_TOKEN` で GitHub の Secret を **上書き**（Update）
   - 「リフレッシュトークンが空」と出たら https://myaccount.google.com/permissions で `mini-tiktok` を削除して再実行
   - OAuth 同意画面が「テスト」のままだと7日で切れます（ステップ2-5の「アプリを公開」を必ず）

## ステップC：Upload-Post で YouTube と TikTok をつなぐ（20分）
YouTube・TikTok の公式APIは審査に通るまで「非公開」でしか投稿できないため、審査済みの投稿代行を使います。
1. https://app.upload-post.com でアカウント作成 → TikTok 投稿ができるプランを契約
2. プロフィールを1つ作る（名前の例：`miniature`）→ そこに **TikTok（@sho1249003）** と **YouTube チャンネル** を連携
3. APIキーを発行
4. GitHub の Secret を2つ：`UPLOAD_POST_API_KEY`（APIキー）／`UPLOAD_POST_USER`（プロフィール名 例 `miniature`）
- TikTok アカウントは **公開アカウント** にしておく
- YouTube だけにしたい時は Variables に `UPLOAD_POST_PLATFORMS = youtube`

## ステップD：Discord 通知（5分）
1. Discord で「＋」→ サーバーを作成 →「自分と友達のため」
2. 通知用チャンネルの歯車 → **連携サービス** → **ウェブフック** → 新しいウェブフック → **URLをコピー**
3. GitHub の Secret：`DISCORD_WEBHOOK_URL`
（LINE Notify は2025年3月で終了。LINE で受けたい場合は LINE公式アカウントの Messaging API の
 長期トークンを `LINE_CHANNEL_TOKEN`、自分のユーザーIDを `LINE_USER_ID` に）

## ステップE：テスト実行 → 本番オン（10分）
1. GitHub **Actions** → 左の **daily-auto** → **Run workflow**（「テスト実行」にチェックが入ったまま）→ 緑のボタン
2. 10〜15分で ✅。ドライブ「完成動画」に動画が届き、Discord に「テスト実行のため SNS には投稿していません」と来れば成功
   - 動画は Actions の実行画面下の **Artifacts** からもダウンロードできます
3. 中身に問題なければ **Settings → Secrets and variables → Actions → Variables タブ → New repository variable**
   - Name：`AUTO_MODE`　Value：`on`
4. 以後、毎日19:00（GitHub の混雑で数分〜数十分遅れることあり）に自動で企画〜投稿されます。止めたい時は `AUTO_MODE` を `off` に

## 全自動モードの動き方
- その日の日付のフォルダ（`content/<今日>_epNNN_*`）が既にあり、写真不要の回ならそれを使う
- 無ければ（または実物写真が必要な回なら）Gemini が次の番号で新しい回を企画。品質チェックに通るまで最大3回作り直す
- 画像・ナレーション・投稿は一時エラー（429など）で最大2回まで待ってから自動リトライ
- 素材が欠けた回・投稿済みの回は投稿しない（`content/<ep>/posted.json` が投稿済みの印）
- 企画と投稿記録は自動でリポジトリに保存される。社長の指定は `docs/next_week.md` に書けば最優先で反映
- **実物写真を使う回（`gen.photo` あり）は自動投稿しません。** これまで通りドライブに写真入りの素材を入れ、TikTok Studio で投稿してください

## エラーが出たら
| 表示 | 原因 | 直し方 |
|---|---|---|
| `GEMINI_API_KEY が未登録` | Secret 名の打ち間違い | 名前を完全一致で登録し直す |
| `HTTP 429` が3回続いて失敗 | Gemini の無料枠・上限 | AI Studio で課金を有効化、または翌日に自動で再挑戦 |
| `invalid_grant` | ドライブの鍵が失効（同意画面がテストのまま等） | ステップ2-5で公開 → ステップBをやり直す |
| `YouTube アナリティクス取得失敗 403` | 鍵に YouTube 権限が無い | ステップBをやり直す（投稿は止まりません） |
| `Upload-Post HTTP 401` | APIキー違い | `UPLOAD_POST_API_KEY` を貼り直す |
| `tiktok_privacy_unavailable` | TikTok が非公開アカウント | TikTok を公開アカウントに |
| `素材が無いシーン … 投稿を中止` | 画像生成の失敗が続いた | Actions の該当ステップのログを Claude に送る |
