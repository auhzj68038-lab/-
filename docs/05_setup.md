# 初期設定ガイド（最初の1回だけ・PCで約40分）

やることは「**5つの合鍵を作って、GitHub の金庫に入れる**」だけです。
合鍵を入れておけば、左腕（毎週の自動ルーチン）とロボット（GitHub Actions）が
**AI素材生成 → 動画書き出し → ドライブ納品** まで勝手にやってくれます。

| # | 合鍵 | 何に使う | 費用 | 所要 |
|---|---|---|---|---|
| 1 | GEMINI_API_KEY | Gemini（Nano Banana）でミニチュア画像を作る | 1枚 約6円 | 5分 |
| 2 | FAL_KEY | Seedance で画像を動画にする | 1秒 約36円（1本2カットまでに制限済み） | 5分 |
| 3 | PEXELS_API_KEY | フリー素材動画（任意） | 無料 | 3分 |
| 4 | GDRIVE_CLIENT_ID / SECRET / REFRESH_TOKEN | ドライブに自動納品 | 無料 | 20分 |
| 5 | — | GitHub に登録して試運転 | 無料 | 5分 |

> 1本あたりの目安：画像6枚（約36円）＋動画8秒（約290円）＝**約330円**。週4本で月 約5,500円。
> 上限は GitHub の Variables `MAX_MOTION_SECONDS`（既定10秒）で調整できます。0 にすると動画化なし＝1本 約36円。

---

## 0. GitHub の「金庫」を開いておく
1. PCのブラウザで https://github.com/auhzj68038-lab/- を開く
2. 上のタブ **Settings**（歯車）→ 左メニュー **Secrets and variables** → **Actions**
3. このページを開いたままにしておく。以下で作った鍵は、ここの緑のボタン **New repository secret** から
   「Name」に鍵の名前、「Secret」に値を貼って **Add secret**。

---

## 1. Gemini の鍵（GEMINI_API_KEY）
1. https://aistudio.google.com/ を開き、ドライブと同じGoogleアカウントでログイン
2. 左下（またはメニュー）の **Get API key** → **Create API key** → プロジェクトは「新規作成」でOK
3. 表示された `AIza…` で始まる文字列をコピー
4. 画像生成は無料枠の対象外のことが多いので、同じ画面の **Set up billing（お支払い設定）** でクレジットカードを登録
   - 使いすぎ防止に Google Cloud の「予算とアラート」で月3,000円のアラートを付けると安心
5. GitHub の金庫に **Name: `GEMINI_API_KEY`** で登録

## 2. Seedance の鍵（FAL_KEY）
Seedance（ByteDance の動画AI）は fal.ai 経由で使います。
1. https://fal.ai/ → 右上 **Sign in**（GitHub アカウントでログインが一番かんたん）
2. 右上メニュー → **Billing** → **Add credits** で $10（約1,500円）チャージ
   - 自動チャージはOFFのままにしておけば、チャージ額以上は絶対に使われません
3. メニュー → **API Keys** → **Add key** → 名前 `tiktok` → 表示された鍵をコピー（**一度しか表示されない**）
4. GitHub の金庫に **Name: `FAL_KEY`** で登録

## 3. Pexels の鍵（PEXELS_API_KEY・任意）
「手元」「作業机」などのリアル映像が欲しい時のフリー素材（商用OK）。
1. https://www.pexels.com/ja-jp/api/ → 無料登録 → **Your API Key** をコピー
2. GitHub の金庫に **Name: `PEXELS_API_KEY`** で登録
（使った場合、投稿文の末尾にクレジットが自動で入ります）

## 4. ドライブの鍵（3つ）
ロボットがあなたのドライブ「ミニチュアの世界」に動画を置くための許可証です。
### 4-1. Google Cloud で許可証の発行元を作る
1. https://console.cloud.google.com/ を開く（手順1で作られたプロジェクトが選ばれていればそのままでOK）
2. 上の検索窓に「Google Drive API」→ 出てきた **Google Drive API** → **有効にする**
3. 左メニュー **APIとサービス → OAuth 同意画面**（または「Google Auth Platform」→「概要」→「開始」）
   - アプリ名: `mini-tiktok`／サポートメール: 自分のGmail
   - 対象: **外部**
   - 連絡先メール: 自分のGmail → 同意して **作成**
4. 「対象（Audience）」画面で **アプリを公開 → 本番環境に push** を押す
   - ⚠️ これを忘れると7日ごとに鍵が切れます
5. 左メニュー **クライアント（認証情報）→ クライアントを作成（OAuth クライアント ID）**
   - アプリケーションの種類: **デスクトップ アプリ** → 名前 `mini-tiktok` → 作成
   - **JSON をダウンロード** → ファイル名を `client_secret.json` に変更してデスクトップに置く

### 4-2. 自分のPCで鍵を取り出す
Python が入っていない場合は https://www.python.org/downloads/ から入れる（Windowsは「Add python.exe to PATH」にチェック）。
1. https://github.com/auhzj68038-lab/- の緑の **Code → Download ZIP** → 解凍
2. 解凍したフォルダに `client_secret.json` を入れる
3. そのフォルダでターミナル（Windows: フォルダのアドレス欄に `cmd` と打って Enter／Mac: 右クリック→「フォルダに新規ターミナル」）を開き、
   ```
   pip install google-auth-oauthlib
   python pipeline/get_refresh_token.py client_secret.json
   ```
4. ブラウザが開く → 自分のアカウントを選ぶ → 「このアプリは Google で確認されていません」→ **詳細 → mini-tiktok（安全ではないページ）に移動** → **続行**
   （自分で作った自分専用アプリなので問題ありません）
5. ターミナルに3行表示されるので、それぞれ GitHub の金庫に登録
   - `GDRIVE_CLIENT_ID` / `GDRIVE_CLIENT_SECRET` / `GDRIVE_REFRESH_TOKEN`
6. 終わったら `client_secret.json` は削除してOK（**絶対に人に送ったりアップしない**）

## 5. 試運転
1. GitHub のリポジトリ → 上のタブ **Actions** → 左の **render-and-deliver** → 右の **Run workflow**
2. episode 欄に `2026-09-27_ep001_mini_ramen` → **Run workflow**
3. 5〜10分で緑のチェック ✅ → ドライブ「ミニチュアの世界 / 完成動画 / 2026-09-27_ep001_mini_ramen」に
   動画・カバー画像・確認シート・投稿文.txt が届けば完成！
   - ❌ 赤くなったら、そのままClaudeに「Actionsが赤い」と送ってください。左腕が直します。

---

## 左腕（毎週の自動ルーチン）について
Claude のルーチンとして **毎週土曜の朝** に起動し、`/autopilot` で今週4本分の企画〜構成を作って push します。
push されると上のロボットが動画化してドライブに納品します。
- 確認・停止: https://claude.ai/code の **Routines**（ルーチン）画面
- 本数やテーマを変えたい時: Claude に「来週はハロウィンで5本」と送るだけ

## ドライブのフォルダ構成
```
ミニチュアの世界/
├ 📘 運用マニュアル
├ 素材/       ← 自分で撮った動画を使いたい時だけ（01_hook.mp4 など plan.json の名前で）
└ 完成動画/   ← 毎週ここに届く（mp4・カバー画像・確認シート・投稿文.txt）
```
