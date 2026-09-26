# 業務フローとAI社員

## 組織図
```
社長（あなた）……最終確認・撮影・投稿ボタンだけ
 └ Claude（AI秘書・進行管理）  … /make-video で全員を順番に動かす
    ├ リサ   市場調査部長     .claude/agents/researcher.md
    ├ ツムギ 台本作家         .claude/agents/scriptwriter.md
    ├ カット 構成ディレクター .claude/agents/director.md
    ├ ヘンシュ 動画編集       .claude/agents/editor.md   ＋ pipeline/render.py
    ├ チェック 品質管理       .claude/agents/qa.md       ＋ pipeline/qa.py
    └ ポスト 投稿担当         .claude/agents/publisher.md ＋ pipeline/drive.py ＋ GitHub Actions
```

## 1本ができるまで
| 工程 | 担当 | 成果物 | 社長の作業 |
|---|---|---|---|
| ① 市場調査 | リサ | content/<ep>/research.md | なし |
| ② 台本 | ツムギ | script.md / caption.txt | なし |
| ③ 構成 | カット | plan.json（撮影リスト付き） | なし |
| ④ 撮影 | **社長** or AI動画生成 | ドライブ「素材/<ep>/01_xxx.mp4」 | スマホで5〜7カット（15分） |
| ⑤ 動画作成 | ヘンシュ＋GitHub Actions | 完成mp4・カバー画像（テロップ・効果音・ズーム・フラッシュ全部入り） | なし |
| ⑥ 確認 | チェック | qa_report.md | ドライブで完成動画を見て OK/NG（2分） |
| ⑦ 投稿 | ポスト | post_checklist.md | TikTok Studioで予約投稿（3分） |

## 副業向け 週間スケジュール（社長の作業 合計 約2時間/週）
| 曜日 | やること | 時間 |
|---|---|---|
| 土 朝 | Claudeアプリで「/make-video 今週分4本」→ 撮影リストが届く | 5分 |
| 土 昼 | 撮影リストどおりスマホで撮影 → ドライブの「素材/<ep>」に入れる | 60分 |
| 土 夜 | Claudeに「素材入れた」と送る → 自動で書き出し・納品 | 1分 |
| 日 | ドライブで4本チェック → TikTok Studio で1週間分を予約投稿 | 30分 |
| 平日 | コメント返信（伸びるための最重要アクション） | 5分/日 |
| 日 夜 | 数値を送る → 「/weekly-review」 | 10分 |

## 撮影しない日の選択肢（AIモード）
素材が撮れない週は、AI画像/動画生成でミニチュア素材を作ることも可能（docs/03_tools.md）。
その回は plan.json に `"ai_generated": true` を入れ、投稿時に TikTok の「AI生成コンテンツ」ラベルをONにする（qa.py が確認）。
実写の手作りミニチュアの方がファン化しやすいので、**基本は実写・AIは補助**がおすすめ。
