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
