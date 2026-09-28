# 業務フローとAI社員

## 組織図
```
社長（あなた）……週30分：確認して予約投稿するだけ
 └ 左腕（Claude の週次ルーチン）… 毎週土曜の朝に自動起動 → /autopilot
    ├ リサ     市場調査部長     .claude/agents/researcher.md
    ├ ツムギ   台本作家         .claude/agents/scriptwriter.md
    ├ カット   構成・AI素材指定 .claude/agents/director.md
    ├ アート   AI素材生成       pipeline/generate.py（Gemini画像 → Seedance動画 / Pexels）
    ├ ヘンシュ 動画編集         .claude/agents/editor.md    ＋ pipeline/render.py
    ├ チェック 品質管理         .claude/agents/qa.md        ＋ pipeline/qa.py
    └ ポスト   納品・投稿準備   .claude/agents/publisher.md ＋ pipeline/drive.py ＋ GitHub Actions
```

## 1週間の流れ
| いつ | 誰が | 何が起きる |
|---|---|---|
| 土 朝（自動） | 左腕 | 先週の数値を振り返り → 今週4本の企画・台本・構成・AI素材プロンプトを作って push |
| 土 午前（自動） | ロボット | Gemini で画像 → Seedance で見せ場を動画化 → テロップ・効果音・演出入りで書き出し → 品質チェック → ドライブ「完成動画」へ納品 |
| **日（30分）** | **社長** | ↓の3つだけ |

## 社長の作業（週30分）
1. **確認（10分）** ドライブ「完成動画」で今週の4本をスマホで流し見。気になる所は Claude に「ep003の2カット目、もっと派手に」と送るだけ（左腕が直して再納品）
2. **予約投稿（15分）** PCで TikTok Studio → 4本を予約投稿（動画・カバー・投稿文.txt をコピペ・AI生成ラベルON）
3. **数値報告（5分）** TikTok Studio の数値をスクショして Claude に送る → 翌週の企画に反映

コメント返信は余裕がある日だけでOK（やると伸びやすい）。

## 自分で撮りたい回
Claude に「次の回は自分で撮る」と送れば、撮影リストが届きます。撮った動画をドライブ「素材/<エピソード>」に入れれば、AI生成の代わりにその素材が使われます。

## AI素材のルール
- 投稿時は TikTok の「AI生成コンテンツ」ラベルを必ずON（投稿文にも「※AI生成映像です」が自動で入る）
- AI映像で「手作り」「制作〇時間」とは言わない（誤解を招く＝信用を失う）
- 他人の動画・画像の転載は禁止。著作権侵害になるうえ、TikTok は転載・無加工の再投稿を「オリジナルでない」としておすすめに載せない
