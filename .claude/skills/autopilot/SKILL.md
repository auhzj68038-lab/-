---
name: autopilot
description: 左腕（毎週の自動ルーチン）用。社長の手を借りずに、今週分のミニチュア動画を企画〜AI素材指定〜構成まで作り、push してGitHub Actionsで動画化・ドライブ納品させる。「/autopilot」「今週分おまかせ」で使う。引数に本数（既定4）。
---
# 左腕の週次業務（社長の作業ゼロで今週分を納品する）

本数: $ARGUMENTS（数字が無ければ 4 本）

1. `git pull` で最新を取り込み、`docs/analytics_log.md` に先週分の数値があれば先に `weekly-review` スキルの手順で振り返り、勝ちパターンを更新する。
2. `researcher` に、今週の季節ネタ・トレンドを踏まえて本数分の企画を出させる（既出ネタと被らせない）。エピソードフォルダは投稿予定日で命名（月・水・金・日の 19:30 投稿想定）。
3. 各エピソードで `scriptwriter` → `director` を実行。**全カットAI素材（gen）で指定**し、`gen.motion` は1本2カットまで。
4. `python pipeline/qa.py content/<ep>` を全エピソードで ERROR 0 にする。
5. `publisher` の手順で各エピソードの post_checklist.md を作る（予約日時入り）。
6. コミットして **既定ブランチ `claude/wonderful-dijkstra-n8c69e` に push**（社長承認済みの運用。他のブランチは使わない。push が拒否されたら fetch→merge してから再push）。GitHub Actions が AI素材生成→書き出し→ドライブ「完成動画」への納品を行う。
7. 最後に社長へ3行で報告：今週の企画タイトル一覧／ドライブ「完成動画」フォルダのURL https://drive.google.com/drive/folders/1UN9JJXcIMvMWbEm66MK7iEOxNk_NrhHQ ／日曜にやること（確認→予約投稿）。
