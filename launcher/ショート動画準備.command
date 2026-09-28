#!/bin/zsh
# ダブルクリックで実行する起動ファイル（Finder / Dock / ショートカット.app から使えます）
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "${0:A:h}/.." || exit 1
uv run --quiet shorts-prep run
status=$?
# ターミナルで開いた場合に結果を読めるよう少し待つ
[[ -t 1 ]] && { echo; read -k 1 "?何かキーを押すと閉じます"; }
exit $status
