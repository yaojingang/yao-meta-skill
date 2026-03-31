# Yao Meta Skill 日本語紹介

`yao-meta-skill` は、他の agent skill を構築するための meta-skill です。

粗い workflow、transcript、prompt、notes、runbook を、再利用可能な skill パッケージに変換し、次の性質を持たせます。

- 明確なトリガー面
- 軽量な `SKILL.md`
- 必要に応じた references、scripts、evals
- 中立的なソースメタデータとクライアント別アダプタ

## Quick Start

1. skill 化したい workflow、prompt 集合、または反復タスクを説明します。
2. `yao-meta-skill` を使って scaffold、production、library のいずれかのモードでパッケージを生成または改善します。
3. 必要に応じて `context_sizer.py`、`trigger_eval.py`、`cross_packager.py` を実行し、検証と出力を行います。

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

- **中立設計**: ソースはベンダー中立で、アダプタは必要時のみ生成
- **コンテキスト効率**: 詳細をメイン skill ファイルの外へ明示的に押し出す
- **評価前提**: trigger とサイズのチェックが workflow に組み込まれている
- **再利用しやすい**: 出力が単発の prompt ではなくパッケージになる
- **移植しやすい**: 互換性はソース複製ではなくパッケージ処理で扱う

## 最適な対象

このプロジェクトは次のような人や組織に向いています。

- agent builder
- 内部ツールチーム
- prompt engineering から skill engineering に移行したい人
- 再利用可能な skill ライブラリを構築したい組織

## ライセンス

MIT。詳細は [LICENSE](../LICENSE) を参照してください。
