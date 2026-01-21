# llminfo-cli

OpenRouter.ai および関連 AI プロバイダー（Groq、Cerebras、Mistral）の利用可能な LLM モデル情報を取得・検索する CLI ツール

## リポジトリ

https://github.com/utenadev/llminfo-cli

## インストール

```bash
pip install llminfo-cli
```

## 環境設定

以下の環境変数を設定してください：

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
export GROQ_API_KEY="your-groq-api-key"          # 任意
export CEREBRAS_API_KEY="your-cerebras-api-key"  # 任意
export MISTRAL_API_KEY="your-mistral-api-key"    # 任意
```

## 使用方法

### はじめに

引数なしで `llminfo` を実行すると、利用可能なコマンドが表示されます：

```bash
llminfo

# 出力:
# Usage: llminfo [COMMAND] [OPTIONS]
#
# Available commands:
#   credits         Display credit balance for the specified provider
#   list            List models from providers
#   test-provider   Test a provider configuration
#   import-provider Test and import a provider configuration
#
# Run 'llminfo [COMMAND] --help' for command-specific help.
#
# Examples:
#   llminfo list models                    # List all models
#   llminfo credits --provider openrouter  # Check credits
```

### モデル一覧表示

全プロバイダーまたは指定されたプロバイダーからモデルを一覧表示します。

```bash
# 全プロバイダーのモデルを一覧表示
llminfo list models

# 特定プロバイダーのモデルを一覧表示
llminfo list models --provider openrouter

# JSON 形式で出力
llminfo list models --json

# API から強制的に最新データを取得（キャッシュを無視）
llminfo list models --force
```

### クレジット残高確認

指定されたプロバイダーのクレジット残高を表示します。

```bash
# OpenRouter のクレジットを確認
llminfo credits --provider openrouter

# Groq のクレジットを確認（未対応、エラーが返されます）
llminfo credits --provider groq

# JSON 形式で出力
llminfo credits --provider openrouter --json
```

### プロバイダーのテストとインポート

新しいプロバイダー設定をテストし、`providers.yml` にインポートします。

```bash
# プロバイダー設定をテスト
llminfo test-provider plugin/new-provider.yml --api-key your-api-key

# テストしてインポート（providers.yml に追加）
llminfo import-provider plugin/new-provider.yml --api-key your-api-key
```

### プロバイダー設定

プロバイダーは `providers.yml` で設定されます。OpenAI 互換のプロバイダーは YAML 設定のみで追加できます：

```yaml
providers:
  groq:
    name: "groq"
    base_url: "https://api.groq.com/openai/v1"
    api_key_env: "GROQ_API_KEY"
    models_endpoint: "/models"
    parser: "openai_compatible"
    credits_endpoint: null
```

詳細なプロバイダー追加基準については `docs/SPEC.md` を参照してください。

### ログ

llminfo-cli にはデバッグと監視のための包括的なログ機能があります。ログはコンソールと `llminfo.log` ファイルの両方に書き込まれます。

### 高度な使用方法

#### カスタムキャッシュTTL

プロバイダー実装を変更してキャッシュTTLを設定できます：

```python
# 例: 2時間のキャッシュTTLを設定
from llminfo_cli.providers.generic import GenericProvider

provider = GenericProvider(
    provider_name="custom",
    base_url="https://api.example.com",
    api_key_env="CUSTOM_API_KEY",
    models_endpoint="/models",
    parser=OpenAICompatibleParser(),
    cache_ttl_hours=2  # デフォルトの1時間ではなく2時間
)
```

#### トラブルシューティング

**一般的な問題:**

- **API キー未設定**: 環境変数が正しく設定されているか確認してください
- **ネットワークエラー**: インターネット接続と API エンドポイントを確認してください
- **レート制限**: 再試行する前に待つか、API 制限を確認してください
- **キャッシュの問題**: `--force` フラグを使用してキャッシュをバイパスしてください

**デバッグ:**

詳細なエラー情報と API 呼び出しログについては `llminfo.log` を確認してください。

## キャッシュ

モデルリストはデフォルトで1時間キャッシュされます。キャッシュは `~/.cache/llminfo/` に保存されます。

APIから強制的に最新データを取得してキャッシュを無視するには：
```bash
llminfo list models --force
```

## 出力形式

### テーブル形式（デフォルト）

```
Total Credits: $15.00
Usage: $2.67
Remaining: $12.33
```

### JSON 形式

```json
{
  "total_credits": 15.0,
  "usage": 2.66625653,
  "remaining": 12.33374347
}
```

## 利用可能なコマンド

### Credits

指定されたプロバイダーのクレジット残高を表示します。現時点では OpenRouter のみがクレジット API をサポートしています。

```bash
llminfo credits --provider openrouter
```

### Test Provider

永続的な設定に追加せず、プロバイダー設定をテストします。

```bash
llminfo test-provider plugin/new-provider.yml --api-key your-api-key
```

### Import Provider

プロバイダー設定をテストし、`providers.yml` にインポートします。

```bash
llminfo import-provider plugin/new-provider.yml --api-key your-api-key
```

## 対応プロバイダー

| プロバイダー | API キー環境変数 | モデル一覧 | クレジット |
|------------|----------------|---------|--------|
| OpenRouter | `OPENROUTER_API_KEY` | ✓ | ✓ |
| Groq | `GROQ_API_KEY` | ✓ | ✗ |
| Cerebras | `CEREBRAS_API_KEY` | ✓ | ✗ |
| Mistral | `MISTRAL_API_KEY` | ✓ | ✗ |

## 開発

### Task Runnerの使用（推奨）

より簡単なプロジェクト管理のために、Task runnerを使用できます：

```bash
# Taskのインストール (https://taskfile.dev/installation/)
# miseを使用する場合（miseがインストールされている場合）:
mise install task=latest

# または https://taskfile.dev/installation/ から直接インストール

# プロジェクトのセットアップ
task setup

# すべてのテストを実行
task test

# カバレッジレポートを生成
task coverage

# リンターを実行
task lint

# 型チェックを実行
task type-check

# すべてのチェックを実行（リンター、型チェック、テスト、カバレッジ）
task check

# セキュリティ監査を実行
task audit

# 開発セットアップを実行（セットアップ＋テスト）
task dev

# 利用可能なタスクを表示
task help
```

### 直接コマンドを使用

```bash
# リポジトリをクローン
git clone https://github.com/utenadev/llminfo-cli.git
cd llminfo-cli

# uv を使用して仮想環境と依存関係をセットアップ
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 全テスト実行
pytest

# カバレッジ付きでテスト実行
pytest --cov=llminfo_cli --cov-report=html

# インテグレーションテスト実行（API キーが必要）
# dotenvx をインストール: curl -fsSL https://dotenvx.sh | sh
# .env.test を暗号化: dotenvx encrypt -f .env.test
# 以下で実行: dotenvx run -f .env.test -- pytest -m integration

# 新しいプロバイダープラグインをテスト
llminfo test-provider plugin/new-provider.yml --api-key your-key

# リントチェック
ruff check .

# フォーマット
ruff format .

# 型チェック
mypy llminfo_cli tests
```

## テスト

- **単体テスト**: モックされた API レスポンスを使用、API キー不要
- **インテグレーションテスト**: 実際の API を呼び出し、有効な API キーが必要（OPENROUTER_API_KEY、GROQ_API_KEY など）

インテグレーションテストのセットアップ手順は `tests/INTEGRATION.md` を参照してください。

現在のカバレッジ: **70%** (99テスト)

## 機能

- **設定ベースのプロバイダー**: OpenAI 互換のプロバイダーを YAML 設定のみで追加
- **プラグインシステム**: 新しいプロバイダーを安全にテストしてインポート
- **型安全**: Python 型ヒントと Pydantic モデルで構築
- **非同期 API 呼び出し**: より良いパフォーマンスのためのノンブロッキングリクエスト
- **複数プロバイダー**: OpenRouter、Groq、Cerebras、Mistral をサポート
- **キャッシング**: モデルリストを 1 時間キャッシュして API 呼び出しを削減
- **キャッシュ無効化**: `--force` フラグを使用してキャッシュをバイパスし最新データを取得

## ライセンス

MIT License
