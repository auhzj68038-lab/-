# 初期設定（最初の1回だけ・約20分）

GitHub Actions がドライブから素材を取り、完成動画をドライブに置けるようにする設定です。
これをやらなくても、完成動画は GitHub の Actions 画面（Artifacts「videos」）から毎回ダウンロードできます。

## 1. Google Cloud で鍵を作る
1. https://console.cloud.google.com/ で新規プロジェクト（名前は何でもOK、例: mini-tiktok）
2. 「APIとサービス」→「ライブラリ」→ **Google Drive API** を有効化
3. 「OAuth 同意画面」→ 外部 → アプリ名・メールを入力 → テストユーザーに自分のGmailを追加
   → **「アプリを公開」を押して本番にする**（テストのままだと7日で鍵が切れる。未確認アプリの警告は自分用なので「続行」でOK）
4. 「認証情報」→「OAuth クライアントID」→ 種類 **デスクトップアプリ** → JSONをダウンロード（client_secret.json）

## 2. 自分のPCでトークンを取る
```bash
pip install google-auth-oauthlib
python pipeline/get_refresh_token.py client_secret.json
```
ブラウザが開くのでGoogleアカウントで許可 → 3つの値が表示される。
（client_secret.json は絶対に GitHub に上げない。.gitignore 済み）

## 3. GitHub に登録
リポジトリの Settings → Secrets and variables → Actions → New repository secret
- `GDRIVE_CLIENT_ID`
- `GDRIVE_CLIENT_SECRET`
- `GDRIVE_REFRESH_TOKEN`

（別フォルダに納品したい時だけ Variables に `GDRIVE_FOLDER_ID` を追加）

## 4. 動作確認
GitHub の Actions → render-and-deliver → Run workflow → `2026-09-27_ep001_mini_ramen`
→ ドライブ「ミニチュアの世界 / 完成動画 / 2026-09-27_ep001_mini_ramen」に動画が入れば完了。

## ドライブのフォルダ構成
```
ミニチュアの世界/
├ 素材/
│  └ 2026-09-27_ep001_mini_ramen/   ← 撮った動画を 01_hook.mp4 のように plan.json の名前で入れる
└ 完成動画/
   └ 2026-09-27_ep001_mini_ramen/   ← 自動で納品（mp4・カバー画像・投稿文.txt・確認シート）
```
