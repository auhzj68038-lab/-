---
name: autopilot
description: 毎週の「今週分つくって」。今週分のミニチュア動画の企画〜台本〜構成〜素材オーダー表までを作り、push してGitHub Actionsで仮動画化・ドライブ納品させる。追加課金ゼロ運用。「/autopilot」「今週分つくって」「今週分おまかせ」で使う。引数に本数（既定4）。
---
# 週次業務（追加課金ゼロ運用）

本数: $ARGUMENTS（数字が無ければ 4 本）

1. `git pull` で最新を取り込む。`docs/analytics_log.md` に先週分の数値があれば先に `weekly-review` スキルの手順で振り返り、勝ちパターンを更新する。`docs/next_week.md` に社長の指定（テーマ・本数）があれば優先する。
2. `researcher` に、今週の季節ネタ・トレンドを踏まえて本数分の企画を出させる（既出ネタと被らせない）。エピソードフォルダは投稿予定日で命名（月・水・金・日 19:30 投稿想定）。
3. 各エピソードで `scriptwriter` → `director` を実行。**画像は1本3枚まで・crop で使い回し**（director.md の「素材の指定」に従う）。
4. `python pipeline/qa.py content/<ep>` を全エピソードで ERROR 0 にし、`python pipeline/order_sheet.py content/<ep>` でオーダー表が作れることを確認する。
5. `publisher` の手順で各エピソードの post_checklist.md を作る（予約日時入り）。
6. コミットして既定ブランチ `claude/wonderful-dijkstra-n8c69e` に push（社長承認済み。push を拒否されたら fetch→merge して再push）。
   GitHub Actions が素材オーダー表をドライブ「素材/<ep>」に置き、仮動画を「完成動画/<ep>」に納品する。社長が画像を入れると2時間以内に本番動画へ差し替わる。
7. 社長へ短く報告：
   - 今週の企画タイトル一覧（投稿予定日つき）
   - 「ドライブ『素材』の各フォルダにある素材オーダー表どおり、Geminiアプリで画像を作って番号の名前で入れてください（計N枚・約N分）」
   - ドライブの鍵が未設定（GitHub Secrets に GDRIVE_REFRESH_TOKEN が無い）なら、オーダー表のコピペ文をこのチャットに直接書く
