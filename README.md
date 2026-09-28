# ショート動画準備（shorts-prep）

スプレッドシートの**最終行**を読み込んで、次の作業を1クリックで行います。

1. `日付_タイトル` という名前のフォルダを作成
2. 素材URLのファイルを `assets/` にダウンロード
3. Premiere のテンプレート（`.prproj`）を複製し、Finder と Premiere で開く

```
~/Desktop/プレミア/ショート動画自動作成/
├── テンプレート.prproj            ← ここに1つ置いておく
└── 2026-09-28_タイトル/           ← 自動作成
    ├── 2026-09-28_タイトル.prproj
    ├── script.txt                 （台本列を設定した場合のみ）
    └── assets/
        ├── 01_xxx.jpg
        └── 02_xxx.mp4
```

## 安全のための仕様

- **既存のファイルやフォルダは絶対に上書きしません。**
  - 同じ名前のフォルダが既にある場合は、**何も変更せずに中止**し、ダイアログでフォルダの場所を知らせます。
  - どのファイルも「存在しない場合のみ作成する」方式で書き込みます。
  - 素材は一時ファイル（`.xxx.part`）に保存し、完了後に正式な名前へ付け替えます。付け替えには宛先が既にあると必ず失敗する `os.link` を使います。
- Google へのアクセス権限は**スプレッドシートの読み取り専用**だけです。
- 認証情報は **macOS キーチェーン**に保存し、平文ファイルには残しません。
- ダウンロードするのは `https://` のURLだけです。リダイレクト先も同じようにチェックします。ファイルの種類（画像・動画・音声）とサイズの上限も確認します。
- ログは `~/Library/Logs/shorts_prep/` に出力します。URLの `?` 以降（署名トークンなど）は記録しません。

## 初回セットアップ（1回だけ）

### 1. 必要なツールのインストール

```sh
# uv（Python の実行環境の管理ツール）
curl -LsSf https://astral.sh/uv/install.sh | sh

# このリポジトリを好きな場所に置く
git clone <このリポジトリ> ~/shorts-prep
cd ~/shorts-prep
uv sync
```

### 2. Google Cloud の設定（Google Workspace 向け）

1. [Google Cloud Console](https://console.cloud.google.com/) で、**会社の Workspace アカウント**を使ってプロジェクトを作ります。
2. 「API とサービス」→「ライブラリ」で **Google Sheets API** を有効にします。
3. 「OAuth 同意画面」で、ユーザーの種類に **「内部」** を選びます。
   - 「内部」にすると、組織内のアカウントしか使えず、Google の審査も不要です。
   - スコープは `.../auth/spreadsheets.readonly` だけを追加します。
4. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」で、種類を **「デスクトップ アプリ」** にして作成し、JSON ファイルをダウンロードします。
5. 組織のポリシーで外部アプリが制限されている場合は、Workspace の管理者に上記のクライアント ID を許可してもらってください（管理コンソール →「セキュリティ」→「API の制御」）。

### 3. 認証情報の登録と設定

```sh
# ダウンロードした JSON をキーチェーンに取り込み、ブラウザでログインする
uv run shorts-prep setup --client-secret ~/Downloads/client_secret_xxxx.json
rm ~/Downloads/client_secret_xxxx.json   # 取り込み後は不要

# 設定ファイルを作成して編集する
uv run shorts-prep init-config
open -e ~/Library/Application\ Support/shorts_prep/config.toml
```

`config.toml` で最低限設定する項目は次のとおりです。

| 項目 | 内容 |
|---|---|
| `spreadsheet_id` | スプレッドシートURLの `/d/` と `/edit` の間の文字列 |
| `sheet_name` | 読み込むシート（タブ）の名前 |
| `[columns]` | 1行目（見出し行）の列名。初期値は `日付` / `タイトル` / `素材URL` |

素材URLは、1つのセルに改行・カンマ・空白で区切って複数入れられます。複数の列（例: `assets = ["素材1", "素材2"]`）に分けることもできます。

### 4. テンプレートを置く

`~/Desktop/プレミア/ショート動画自動作成/` の直下に、テンプレートの `.prproj` を**1つだけ**置きます。
複数置く場合は、`config.toml` の `[paths] template` で使うものを指定してください。

### 5. 動作確認（何も作らないドライラン）

```sh
uv run shorts-prep run --dry-run
```

## 毎日の使い方（1クリック）

どちらかの方法で起動できます。

- **A. ダブルクリック**：`launcher/ショート動画準備.command` を Dock やデスクトップに置いてダブルクリックします。
  初回だけ `chmod +x launcher/ショート動画準備.command` を実行し、右クリック →「開く」で許可してください。
- **B. ショートカット.app**：新規ショートカットに「シェルスクリプトを実行」を追加し、次の内容を入れます。メニューバーやキーボードショートカットから起動できます。
  ```sh
  export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
  cd ~/shorts-prep && uv run --quiet shorts-prep run
  ```

完了すると通知が出て、フォルダと Premiere プロジェクトが開きます。
エラーや取得に失敗した素材があった場合は、ダイアログで内容を表示します。

## コマンド一覧

| コマンド | 内容 |
|---|---|
| `shorts-prep` / `shorts-prep run` | 最終行から作業フォルダを準備する |
| `shorts-prep run --dry-run` | 何も作らずに、作る予定のものだけを表示する |
| `shorts-prep run --no-open` | 完了後に Finder と Premiere を開かない |
| `shorts-prep init-config` | 設定ファイルのひな形を作る（既存の設定は上書きしない） |
| `shorts-prep setup --client-secret FILE` | OAuth クライアント情報を登録してログインする |
| `shorts-prep login` / `logout` | ログインする / 保存したトークンを削除する |

## 開発

```sh
uv run --extra dev pytest
```
