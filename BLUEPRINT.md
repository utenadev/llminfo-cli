# llminfo-cli - 詳細設計書

## 技術スタック

### コアフレームワーク
- **Python 3.11+** - 実行環境
- **typer** - CLIフレームワーク
  - 型安全なCLI定義
  - 自動的なhelp生成
  - サブコマンドの自然な階層化
  - リッチなオプションサポート
- **httpx** - 非同期HTTPクライアント
  - 高速なリクエスト
  - 自動的な再試行（retry）
  - 非同期処理対応
- **pydantic** - データバリデーション
  - APIレスポンスのバリデーション
  - 型安全なデータモデル

### 開発ライブラリ
- **pytest** - テストフレームワーク
- **pytest-asyncio** - 非同期テスト用
- **ruff** - リンター・フォーマッター
- **mypy** - 静的型チェッカー

## プロジェクト構成

```
llminfo-cli/
├── llminfo_cli/
│   ├── __init__.py
│   ├── main.py              # CLIエントリーポイント
│   ├── models.py             # モデル情報管理
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py          # プロバイダーベースクラス
│   │   ├── openrouter.py    # OpenRouter実装
│   │   ├── groq.py          # Groq実装
│   │   ├── cerebras.py      # Cerebras実装
│   │   └── mistral.py      # Mistral実装
│   └── schemas.py            # データモデル定義
├── tests/
│   ├── __init__.py
│   ├── test_providers.py
│   └── test_models.py
├── pyproject.toml
├── README.md
└── .env.example
```

## 詳細設計

### 1. プロバイダーアーキテクチャ

#### 抽象ベースクラス
```python
# providers/base.py

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class ModelInfo(BaseModel):
    id: str
    name: str
    context_length: Optional[int] = None
    pricing: Optional[dict] = None
    is_free: bool = False

class Provider(ABC):
    @abstractmethod
    async def get_models(self) -> List[ModelInfo]:
        """モデル一覧を取得"""
        pass

    @abstractmethod
    async def get_credits(self) -> Optional[dict]:
        """クレジット情報を取得（存在する場合）"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """プロバイダー名"""
        pass
```

#### OpenRouter実装
```python
# providers/openrouter.py

import httpx
from .base import Provider, ModelInfo

class OpenRouterProvider(Provider):
    BASE_URL = "https://openrouter.ai/api/v1"
    API_KEY_ENV = "OPENROUTER_API_KEY"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(self.API_KEY_ENV)

    async def get_models(self) -> List[ModelInfo]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            data = response.json()["data"]

            return [
                ModelInfo(
                    id=m["id"],
                    name=m["name"],
                    context_length=m.get("context_length"),
                    pricing=m.get("pricing"),
                    is_free=":free" in m["id"]
                )
                for m in data
            ]

    async def get_credits(self) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/credits",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()["data"]

    @property
    def provider_name(self) -> str:
        return "openrouter"
```

#### Groq/Cerebras/Mistral実装
```python
# providers/groq.py, cerebras.py, mistral.py

import httpx
from .base import Provider, ModelInfo

class GroqProvider(Provider):
    BASE_URL = "https://api.groq.com/openai/v1"
    API_KEY_ENV = "GROQ_API_KEY"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(self.API_KEY_ENV)

    async def get_models(self) -> List[ModelInfo]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            data = response.json()["data"]

            return [
                ModelInfo(
                    id=m["id"],
                    name=m["id"],  # Groqはnameフィールドがない
                    context_length=m.get("context_window"),
                    is_free=False  # Groqは有料のみ
                )
                for m in data
            ]

    async def get_credits(self) -> Optional[dict]:
        # Groq/Cerebras/MistralはクレジットAPIがない
        return None

    @property
    def provider_name(self) -> str:
        return "groq"
```

### 2. CLIコマンド構成

#### メインコマンド階層
```bash
# ルートコマンド
llminfo                    # ヘルプ表示
llminfo list                # listサブコマンド
llminfo list free            # Freeモデル一覧
llminfo list models          # 全モデル一覧
llminfo best-free            # 最適Freeモデル選択
llminfo credits              # クレジット確認

# グローバルオプション
--provider <provider>    # プロバイダー指定
--json                  # JSON出力
--table                 # テーブル出力（デフォルト）
--output <file>         # ファイルへ出力
```

#### listサブコマンド
```bash
llminfo list free                    # 全プロバイダーのfreeモデル
llminfo list free --provider openrouter  # 特定プロバイダーのみ
llminfo list free --json            # JSON形式で出力
llminfo list free --output models.json  # ファイルへ保存
```

#### best-freeサブコマンド
```bash
llminfo best-free                    # 最適freeモデルを1つ選択
llminfo best-free --provider openrouter  # 特定プロバイダー
llminfo best-free --json              # JSON形式で出力（モデルIDのみ）
```

#### creditsサブコマンド
```bash
llminfo credits openrouter          # OpenRouterのクレジット
llminfo credits --json              # JSON形式で出力
```

### 3. モデル選択ロジック

#### AgentCodingTool用最適モデル選択
```python
# 選択基準（重要度順）
1. コンテキスト長（context_length） - 大きいを優先
2. 価格（pricing.prompt/completion） - 安いを優先
3. サポートするパラメーター（supported_parameters）- function_calling, tools等
4. 推論能力（reasoning_tokensサポート）

def select_best_free_model(models: List[ModelInfo]) -> ModelInfo:
    """
    AgentCodingToolでの利用に適した最適なFreeモデルを選択

    優先順位：
    1. context_length > 32,000（長いコード生成）
    2. function_calling, toolsをサポート
    3. 低価格
    """
    candidates = [m for m in models if m.is_free]

    # 基準1: コンテキスト長
    candidates = [m for m in candidates if (m.context_length or 0) > 32000]

    # 基準2: 低価格
    if candidates:
        candidates.sort(key=lambda m: float(m.pricing.get("prompt", "999999")) if m.pricing else 999999)

    return candidates[0] if candidates else models[0]
```

### 4. 出力形式

#### テーブル形式（デフォルト）
```
Provider    Model ID                           Context    Price (Prompt/1M)
--------    --------------------------------        -------    -----------------
OpenRouter  openai/gpt-4o-mini:free           128K       $0.00
OpenRouter  google/gemini-1.5-flash:free       1M         $0.00
Groq       llama-3.1-8b-instant              131K       $0.05
```

#### JSON形式
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

### 5. エラーハンドリング

#### APIリクエストエラー
```python
try:
    models = await provider.get_models()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        echo_error("APIキーが無効です。環境変数を確認してください。")
    elif e.response.status_code == 429:
        echo_error("レート制限を超えました。時間を置いて再試行してください。")
    else:
        echo_error(f"APIリクエストエラー: {e.response.status_code}")
except httpx.RequestError as e:
    echo_error("ネットワークエラー: インターネット接続を確認してください。")
```

#### APIキー未設定
```python
if not api_key:
    echo_error(f"{provider_name}のAPIキーが設定されていません。")
    echo_info(f"環境変数 {API_KEY_ENV} を設定してください。")
    sys.exit(1)
```

### 6. テスト戦略

#### 単体テスト
```python
# tests/test_providers.py

import pytest
from openrouter_cli.providers import OpenRouterProvider, GroqProvider

@pytest.mark.asyncio
async def test_openrouter_get_models():
    provider = OpenRouterProvider(api_key="test_key")
    # モックAPIレスポンスを使用
    models = await provider.get_models()
    assert len(models) > 0
    assert any(m.is_free for m in models)

@pytest.mark.asyncio
async def test_select_best_model():
    from openrouter_cli.models import select_best_free_model
    # モックモデルデータ
    models = [
        ModelInfo(id="model1", name="Model 1", context_length=32000, is_free=True, pricing={"prompt": "0.01"}),
        ModelInfo(id="model2", name="Model 2", context_length=131072, is_free=True, pricing={"prompt": "0.00"}),
    ]
    selected = select_best_free_model(models)
    assert selected.id == "model2"  # context_lengthと価格で選択
```

#### 統合テスト
```python
# tests/test_integration.py

import pytest
from openrouter_cli.main import app

def test_list_free_command():
    from typer.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(app, ["list", "free"])
    assert result.exit_code == 0
    assert "free" in result.stdout.lower()
```

### 7. 配布設定

#### pyproject.toml
```toml
[project]
name = "llminfo-cli"
version = "0.1.0"
description = "OpenRouter.aiおよび関連AIプロバイダーのモデル情報取得CLIツール"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",  # 美しいテーブル出力
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
llminfo = "llminfo_cli.main:app"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
```

### 8. 実装フェーズ

#### Phase 1: 基盤整備
1. プロジェクト構成の作成
2. 基礎データモデルの実装
3. 設定ファイルの作成（.env.example）

#### Phase 2: プロバイダー実装
1. OpenRouterプロバイダーの実装
2. Groqプロバイダーの実装
3. Cerebrasプロバイダーの実装
4. Mistralプロバイダーの実装

#### Phase 3: CLIコマンド実装
1. listサブコマンドの実装
2. best-freeコマンドの実装
3. creditsコマンドの実装
4. 出力フォーマットの整備

#### Phase 4: テスト
1. 単体テストの作成
2. 統合テストの作成
3. カバレッジの設定

#### Phase 5: ドキュメンテーション
1. README.mdの作成
2. .env.exampleの作成
3. 使用例の追加

#### Phase 6: 配布準備
1. PyPIへの配布設定
2. GitHub Actions CI/CDの設定

## 将来の拡張

### マイルストーン v1.1
- [ ] 複数プロバイダーの料金比較機能
- [ ] モデル詳細情報の表示（`ai-cli info <model_id>`）
- [ ] モデルフィルタリング機能（`--filter "price<0.01"`）
- [ ] 履歴管理（最近使用したモデルを保存）

### マイルストーン v1.2
- [ ] インタラクティブモード（TUI）
- [ ] モデル評価機能
- [ ] カスタムプロバイダーの追加
