#!/usr/bin/env bash
# 依存ライブラリとテロップ用フォント（Dela Gothic One / M PLUS Rounded 1c・どちらもOFL）を入れる
set -e
cd "$(dirname "$0")"
pip install -q -r requirements.txt
mkdir -p fonts
base=https://github.com/google/fonts/raw/main/ofl
[ -f fonts/DelaGothicOne-Regular.ttf ] || curl -fsSL -o fonts/DelaGothicOne-Regular.ttf $base/delagothicone/DelaGothicOne-Regular.ttf || echo "フォント取得失敗（標準フォントで続行）"
[ -f fonts/MPLUSRounded1c-ExtraBold.ttf ] || curl -fsSL -o fonts/MPLUSRounded1c-ExtraBold.ttf $base/mplusrounded1c/MPLUSRounded1c-ExtraBold.ttf || true
echo "✅ セットアップ完了"
