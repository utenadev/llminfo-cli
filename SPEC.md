# llminfo-cli - 仕様書

## 概要
OpenRouter.aiおよび関連AIプロバイダー（Groq、Cerebras、Mistral）の利用可能なLLMモデル情報を取得・検索するCLIツール

## ユーザーニーズ

### 必須機能
1. **Freeモデル一覧表示** - OpenRouterの無料モデルを一覧表示
2. **最適Freeモデル選択** - AgentCodingToolでの利用に適した最適なFreeモデルを1つ選択
3. **クレジット残高確認** - OpenRouterの残クレジットを表示
4. **全モデル一覧表示** - 各プロバイダーの全モデル情報を表示

### 利用想定
- 環境変数 `OPENROUTER_API_KEY` にAPIキーを設定済み
- AgentCodingToolからプログラム的に呼び出される想定
- シェルスクリプトとしても利用可能

## 対応プロバイダー

| プロバイダー | ベースURL | APIキー環境変数 | モデル一覧 | クレジット |
|------------|-----------|----------------|---------|--------|
| OpenRouter | https://openrouter.ai/api/v1 | OPENROUTER_API_KEY | o | o |
| Groq | https://api.groq.com/openai/v1 | GROQ_API_KEY | o | x |
| Cerebras | https://api.cerebras.ai/v1 | CEREBRAS_API_KEY | o | x |
| Mistral | https://api.mistral.ai/v1 | MISTRAL_API_KEY | o | x |

## 要件定義

### FR-001: Freeモデル一覧表示
- OpenRouterの無料モデル（`:free`サフィックス付き）を一覧表示する
- モデル名、コンテキスト長、価格を表示

### FR-002: 最適Freeモデル選択
- AgentCodingToolでの利用に適した最適なFreeモデルを1つ選択して返す
- 選択基準：コンテキスト長、価格、パフォーマンス
- 標準出力またはJSON出力でモデルIDを返す

### FR-003: クレジット残高確認
- OpenRouterの残クレジットを表示する
- 総購入額、総使用額、残高を表示

### FR-004: 全モデル一覧表示
- 各プロバイダーの全モデル情報を表示する
- プロバイダー、モデル名、コンテキスト長、価格を表示

### FR-005: プロバイダー指定
- コマンドラインでプロバイダーを指定可能にする
- デフォルト：全プロバイダー

## 非機能要望

| ID | 要望 | 優先度 |
|----|--------|---------|
| NF-001 | 複数プロバイダーの料金比較 | Low |
| NF-002 | モデル詳細情報の表示 | Low |
| NF-003 | モデルフィルタリング（名前、価格など） | Medium |
| NF-004 | モデル検索機能 | Medium |

## 技術制約

- Python 3.11+
- インターネット接続必須
- APIキー認証必須
- レート制限に準拠

## セキュリティ要件

- APIキーは環境変数または設定ファイルに保存
- ログファイルにはAPIキーを含めない
- HTTPS通信のみ使用

## 運用環境

- 開発環境: ローカル開発
- 実行環境: Python 3.11+がインストール済みのマシン

## 配布形式

- PyPIパッケージとして配布
- インストール: `pip install llminfo-cli`
