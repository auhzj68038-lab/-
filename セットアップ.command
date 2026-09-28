#!/bin/zsh
# 初回セットアップ。ターミナルで `zsh ` と入力し、このファイルをドラッグして Enter で実行します。
# 既存のファイルは上書きしません。
set -eu

SRC="${0:A:h}"
DEST="$HOME/shorts-prep"
LINK="$HOME/Desktop/ショート動画準備.command"

echo "=== ショート動画準備 セットアップ ==="

# 1. ツール一式を ~/shorts-prep に配置（ダウンロードフォルダを整理しても動くように）
if [[ "$SRC" != "$DEST" ]]; then
  if [[ -e "$DEST" ]]; then
    echo "既に $DEST があるので、そちらを使います（上書きしません）。"
  else
    cp -R "$SRC" "$DEST"
    echo "ツールを $DEST にコピーしました。"
  fi
fi
cd "$DEST"

# ダウンロード由来の「開けません」警告を、このツールのフォルダに限って解除
xattr -dr com.apple.quarantine "$DEST" 2>/dev/null || true
chmod +x launcher/*.command

# 2. uv（Python 実行環境）
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv をインストールします…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "必要なライブラリを準備しています…（初回は1〜2分かかります）"
uv sync --quiet

# 3. デスクトップに起動用アイコン
if [[ -e "$LINK" || -L "$LINK" ]]; then
  echo "デスクトップの起動ファイルは既にあります（上書きしません）。"
else
  ln -s "$DEST/launcher/ショート動画準備.command" "$LINK"
  echo "デスクトップに「ショート動画準備」を作成しました。"
fi

# 4. 対話形式の設定（スプレッドシート・Google ログイン・テンプレート確認）
echo
uv run --quiet shorts-prep wizard
