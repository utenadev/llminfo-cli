# llminfo-cli

OpenRouter.ai および関連 AI プロバイダー（Groq、Cerebras、Mistral）の利用可能な LLM モデル情報を取得・検索する CLI ツール

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

### Free モデル一覧表示

```bash
# 全プロバイダーの Free モデルを一覧表示
llminfo list free

# 特定プロバイダーの Free モデルのみ
llminfo list free --provider openrouter

# JSON 形式で出力
llminfo list free --json
```

### 最適 Free モデル選択

AgentCodingTool での利用に適した最適な Free モデルを 1 つ選択します。

```bash
llminfo best-free

# 特定プロバイダーから選択
llminfo best-free --provider openrouter

# JSON 形式で出力
llminfo best-free --json
```

### クレジット残高確認

OpenRouter のクレジット残高を表示します。

```bash
llminfo credits openrouter

# JSON 形式で出力
llminfo credits openrouter --json
```

### 全モデル一覧表示

```bash
# 全プロバイダーの全モデルを表示
llminfo list models

# 特定プロバイダーのモデルのみ
llminfo list models --provider groq
```

## 出力形式

### テーブル形式（デフォルト）

```
Provider    Model ID                           Context    Price (Prompt/1M)
--------    --------------------------------        -------    -----------------
OpenRouter  openai/gpt-4o-mini:free           128K       $0.00
OpenRouter  google/gemini-1.5-flash:free       1M         $0.00
```

### JSON 形式

```json
{
  "provider": "openrouter",
  "models": [
    {
      "id": "openai/gpt-4o-mini:free",
      "name": "GPT-4o Mini",
      "context_length": 128000,
      "pricing": {
        "prompt": "0.00015",
        "completion": "0.0006"
      },
      "is_free": true
    }
  ]
}
```

## 対応プロバイダー

| プロバイダー | API キー環境変数 | モデル一覧 | クレジット |
|------------|----------------|---------|--------|
| OpenRouter | `OPENROUTER_API_KEY` | ✓ | ✓ |
| Groq | `GROQ_API_KEY` | ✓ | ✗ |
| Cerebras | `CEREBRAS_API_KEY` | ✓ | ✗ |
| Mistral | `MISTRAL_API_KEY` | ✓ | ✗ |

## 開発

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/llminfo-cli.git
cd llminfo-cli

# 開発依存関係をインストール
pip install -e ".[dev]"

# テスト実行
pytest

# リントチェック
ruff check .

# フォーマット
ruff format .

# 型チェック
mypy llminfo_cli
```

## ライセンス

MIT License
