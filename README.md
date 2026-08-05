# キム・ミンソプ（김민섭）— Product / UX Research

[한국어](README.ko.md) · **日本語**

ユーザーの「なぜ」を掘り下げ、仮説を立て、データで検証しながらプロダクトを前に進めます。
韓国のデザインSaaS企業で、日本市場向けAIプロダクトの企画（Assistant PdM）をしています。

📄 **ケーススタディ** → [ポートフォリオ](outputs/vibe-coding/portfolio-aisaac)
🖱 **触ってみる** → [デザイン評価ビューアのデモ](https://ricky111529-cmyk.github.io/pm-ai-toolkit/outputs/vibe-coding/design-eval-viewer/) — `サンプル読み込み` を押すとデータなしで動きます（日本語 / 한국어 切り替え可）

---

## このリポジトリは何か

**企画者が自分の作業環境を設計した記録です。**

AIとペアで働くうえで一番無駄だったのは、毎回コンテキストを説明し直すことでした。そこでルールをファイルに固定しました — どの文書をどこに保存するか、どの類型ならどの骨格を使うか、何を聞き返すべきか。

| | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | 起動時に必ず読むルール。保存先の決定木 · 文書類型ごとの構造 · ルーティング |
| [`.claude/prompts/templates/`](.claude/prompts/templates) | 文書類型8種の骨格 — PRD · 機能仕様 · VoC分析 · 競合リサーチ · データ分析 · アンケート · 実験 · 評価ルーブリック |
| [`.claude/prompts/ux-research-guideline.md`](.claude/prompts/ux-research-guideline.md) | リサーチクエスチョン・仮説・インタビュー設計のフレームワーク |
| [`.claude/skills/`](.claude/skills) | Databricks SQL · Unity Catalog · Genie |

設計原則は一つです。**「この行がなければAIは間違えるか？ Noなら削除」**。コードやファイル構造から読み取れる情報は書きません。だから `CLAUDE.md` は200行を超えません。

---

## どう働くか

**仮説と検証** — 何が・なぜ起きているのかを突き止め、データで確かめる。
AIスライド生成の初回失敗を3万件分析し、3つのroute（聞き返し / 不適切な拒否 / 空応答）に分類して、13.4% → 5.1% に下げました。発見から検証まで一人で閉じた経験です。

**オーナーシップ** — 指示を待たず、自分で課題を定義する。
企画が通らない理由を掘ると、チームがユーザーを深く理解できていないことが根本でした。1on1で問題を提起し、UXリサーチを自ら立ち上げました。現在進行中です。

**自分でつくる** — 企画だけでなく検証ツールを自作する。
LLM品質評価パイプラインをAIとペアで自作しました（コードはAI、設計・検証は自分）（[コードと振り返り](outputs/vibe-coding/llm-qa-pipeline)）。自社APIでスライドを自動生成し、外部LLMがPASS/FAILを判定する2層構造（Rule-based + LLM-based）です。**実運用までは至りませんでした** — 「LLMでLLMを評価する」判定精度を担保できなかったのが壁でした。この振り返りが次のツールの設計になりました → [`design-eval-viewer`](outputs/vibe-coding/design-eval-viewer)：自動判定を先につくらず、**人が実物を見て判断を残す環境**を先につくりました。

---

## つくったもの

| | |
|---|---|
| [`design-eval-viewer`](outputs/vibe-coding/design-eval-viewer) | AIの生成物を全ページのサムネイル + 文脈と一緒に見て、**ページ単位で**評価を残す単一HTMLアプリ。大きなgzをブラウザでストリーミング解凍 · 逐次レンダリング · カラム自動分類。[**デモを開く ↗**](https://ricky111529-cmyk.github.io/pm-ai-toolkit/outputs/vibe-coding/design-eval-viewer/) |
| [`llm-qa-pipeline`](outputs/vibe-coding/llm-qa-pipeline) | AIチャット応答の品質を自動検証するパイプライン。2層判定 · マルチターン自動化 · Flask UI。**実運用には至りませんでした** — [振り返り](outputs/vibe-coding/llm-qa-pipeline/PORTFOLIO.md) |
| [`portfolio-aisaac`](outputs/vibe-coding/portfolio-aisaac) | ポートフォリオサイト |

---

## できること

誇張せずに書きます。

| | |
|---|---|
| 企画・リサーチ | PRD・機能仕様の作成、インタビュー設計、定性分析、VoC分類体系 |
| データ | SQL（Databricks）。記述統計・ファネル・コホート・A/B結果の解釈は自分で / **仮説検定・回帰は概念レベルで、AIの補助を使います** / モデリングはまだできません |
| つくる | **自分ではコードを書けません。** ツールはすべてAIとのペア（vibe coding）でつくりました — 問題定義・要件・検証（QA・実測）は自分、コードはAI。このリポジトリのビューアやパイプラインがその成果物です |
| 言語 | 韓国語（母語）· 日本語（JLPT N1） |

---

## 入れていないもの

会社の業務成果物（企画書・リサーチレポート・顧客データ・社内インフラ設定）は入っていません。再利用できる**方法**だけを移し、社内スキーマ・ホスト・パスはプレースホルダに置き換えています。

ただし仕事の全体像が分かるよう、社内成果物は**フォルダ名と概要（README）だけ**残しています — 中身は空です。
[`outputs/research/`](outputs/research)（VoC分析 · NPS分析 · ユーザーインタビュー · 入力ログ分析 · 競合リサーチ · プロンプト実験）· [`outputs/specs/`](outputs/specs)（企画書・スペック）· [`projects/ux-research/`](projects/ux-research)（進行中のUXリサーチ）

## 連絡先

ricky111529@gmail.com
