# Yao Meta Skill 日本語紹介

`YAO = Yielding AI Outcomes` は、「AI の結果を実際の成果として届ける」という意味です。単に prompt テキストを増やすのではなく、再利用可能な AI 資産と実運用の成果を作ることを重視します。

`yao-meta-skill` は、再利用可能な agent skill を作成・評価・パッケージ化・運用するための、軽量で厳密なシステムです。

粗い workflow、transcript、prompt、notes、runbook を、再利用可能な skill パッケージに変換し、次の性質を持たせます。

- 明確なトリガー面
- 軽量な `SKILL.md`
- 必要に応じた references、scripts、evals
- 深い authoring の前に、制御された benchmark/reference scan を 1 回行う
- 新しい skill ごとに、白背景の簡潔な HTML overview を自動生成
- 中立的なソースメタデータとクライアント別アダプタ
- ガバナンス、昇格判定、portability チェックを標準フローに内蔵

## アーキテクチャ

Hero 版では、全体の流れは 1 本です。ばらばらの入力を、統制された再利用可能な skill package に変えます。

```mermaid
flowchart LR
    A["入力<br/>workflow / prompt / transcript / docs / notes"] --> B["ルート定義<br/>SKILL.md"]
    B --> C["設計<br/>method + gates"]
    C --> D["実行<br/>create / validate / eval / promote"]
    D --> E["出力<br/>skill package + reports + adapters"]
```

10 秒で読むならこうです。

- **入力**: workflow、prompt、文書、メモなどの粗い素材から始めます。
- **ルート定義**: まず軽量な `SKILL.md` で境界と trigger を決めます。
- **設計**: 適切な archetype、gate、資源の分割を選びます。
- **実行**: 統一 CLI で作成、検証、最適化、昇格を進めます。
- **出力**: 最終的に skill package と、評価・ガバナンス・移植性の証拠が残ります。

## Quick Start

1. skill 化したい workflow、prompt 集合、または反復タスクを説明します。
2. まず短い reference scan を行い、借りるべき pattern だけを抽出します。
3. `yao-meta-skill` を使って scaffold、production、library のいずれかのモードでパッケージを生成または改善します。
4. 新しく作成した skill には `reports/skill-overview.html` と `reports/reference-scan.md` が付き、構造、ロジック、使い方、参考対象をすぐ確認できます。

## Results

- 現在 `make test` は通過
- 現在の回帰セットでは trigger eval が `0` false positives / `0` false negatives
- train / dev / holdout の 3 層評価が通過
- `openai`、`claude`、`generic` の packaging contract が通過

## 現在の強み

最新の加重レビューでは、Yao の強みは production-grade な meta-skill を支える次の領域に集中しています。

- **方法論の完成度 `9.8`**: skill engineering method、gate selection、non-skill decision、governance、resource boundary が正式な体系として揃っています。
- **エンジニアリングツールチェーン `9.8`**: 初期化、検証、最適化、レポート、昇格判定、パッケージ化、CI が一つの運用フローに接続されています。
- **ガバナンス / 保守 / 安全性 `9.8`**: 重要な skill に lifecycle、review cadence、maturity score、trust boundary、promotion evidence を持たせられます。
- **評価ループ `9.7`**: train/dev/holdout、blind holdout、adversarial holdout、judge-backed blind eval、drift history、promotion gate まで備えています。
- **移植性 / パッケージング `9.6`**: ソースは中立のまま保ち、adapter、degradation rule、packaging contract で環境間の再利用性を担保します。
- **トリガーと境界設計 `9.5`**: route confusion、anti-pattern regression、promotion policy により、trigger 品質を監査可能な routing 問題として扱います。
- **コンテキスト効率 `9.4`**: エントリポイントは小さく保たれ、context budget は tier 化され、quality density も追跡されます。

全体の方向性は明確です。入口は軽く、評価は厳しく、ガバナンスは skill 品質の一部として扱います。

## なぜ Yao なのか

- **軽量**: エントリポイントは小さく保たれ、context budget は明示され、追加構造は本当に価値がある場合にだけ導入されます。
- **厳密**: trigger 品質は family regression、blind holdout、adversarial holdout、route confusion、judge-backed blind eval、promotion gate で検証されます。
- **ガバナンス可能**: 重要な skill は lifecycle、maturity expectation、owner、review cadence を持つ保守対象の資産として扱われます。
- **移植可能**: ソースメタデータは中立のまま保たれ、adapter、degradation rule、packaging contract が環境間の再利用意味論を保持します。

## 何をするものか

このプロジェクトは、skill を単発の prompt ではなく、作成・改善・評価・配布できる持続的な能力パッケージとして扱えるようにします。

設計ロジックは次の通りです。

1. ユーザーの依頼の背後にある反復的な仕事を特定する
2. skill の境界を整理し、1 つのパッケージを 1 つの一貫した役割に保つ
3. 本文を長くする前に trigger description を最適化する
4. メインの skill ファイルを小さく保ち、詳細は references や scripts に移す
5. 品質ゲートは必要なときだけ追加する
6. 本当に必要なクライアント向けにだけ互換出力を生成する

## なぜ必要か

多くのチームでは、重要な運用知識が chat、個人 prompt、口頭の習慣、未整理の workflow に散在しています。このプロジェクトは、それらの暗黙知を次の形に変換します。

- 発見可能な skill パッケージ
- 再現可能な実行フロー
- 低コンテキストな指示
- 再利用可能なチーム資産
- 配布しやすい互換パッケージ

## リポジトリ構成

```text
yao-meta-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── .gitignore
├── agents/
│   └── interface.yaml
├── references/
├── scripts/
└── templates/
```

## 主要コンポーネント

### `SKILL.md`

メインの skill エントリです。トリガー面、動作モード、圧縮された workflow、出力契約を定義します。

### `agents/interface.yaml`

中立的なメタデータの単一ソースです。表示情報と互換性情報を保持し、ソースツリーを特定ベンダーのパスに固定しません。

### `references/`

メイン skill ファイルを肥大化させないための長文資料です。設計ルール、評価方法、互換戦略、品質 rubric を含みます。

### `scripts/`

この meta-skill を実用的にする補助スクリプトです。

- `trigger_eval.py`: trigger description が広すぎるか弱すぎるかを確認する
- `context_sizer.py`: コンテキスト量を見積もり、初期ロードが大きすぎる場合に警告する
- `cross_packager.py`: 中立的なソースパッケージからクライアント別出力を生成する

### `templates/`

単純な skill と複雑な skill を始めるためのテンプレートです。

## 使い方

### 1. この skill を直接使う

次のようなときに `yao-meta-skill` を使います。

- 新しい skill を作る
- 既存の skill を改善する
- skill に eval を追加する
- workflow を再利用可能なパッケージにする
- チーム向けに skill を整備する

### 2. 新しい skill パッケージを生成する

一般的な流れは次の通りです。

1. workflow または能力を説明する
2. trigger フレーズと出力を特定する
3. scaffold、production、library のいずれかを選ぶ
4. パッケージを生成する
5. 必要に応じてサイズチェックと trigger チェックを行う
6. 対象クライアント向けの互換出力を生成する

### 3. 互換出力を生成する

例:

```bash
python3 scripts/cross_packager.py ./yao-meta-skill --platform openai --platform claude --zip
python3 scripts/context_sizer.py ./yao-meta-skill
python3 scripts/trigger_eval.py --description "Create and improve agent skills..." --cases ./cases.json
```

## 利点

- **prompt ではなく方法論が中心**: skill creation を正式な engineering workflow として扱います
- **トリガー最適化を前提に設計**: description は route confusion、blind holdout、adversarial family、promotion policy で検証されます
- **入口が軽い**: `SKILL.md` は最小限に保ち、references、scripts、evals は必要なときだけ追加します
- **ツールチェーンが一貫**: 初期化、検証、最適化、レポート、パッケージ化、テストを統一 CLI と CI で回せます
- **資産として運用できる**: owner、lifecycle、maturity expectation、review cadence を持つ skill として管理できます
- **移植前提**: ソースは中立、互換性は adapter と degradation rule で処理します
- **証拠が豊富**: route scorecard、regression history、context budget、portability score、promotion decision が公開アーティファクトとして残ります

## 最適な対象

このプロジェクトは次のような人や組織に向いています。

- agent builder
- 内部ツールチーム
- prompt engineering から skill engineering に移行したい人
- 再利用可能な skill ライブラリを構築したい組織

## ライセンス

MIT。詳細は [LICENSE](../LICENSE) を参照してください。
