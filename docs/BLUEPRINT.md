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
- **pyyaml** - 設定ファイル管理
  - プロバイダー設定の読み込み
  - プラグインファイルのパース

### 開発ライブラリ
- **pytest** - テストフレームワーク
- **pytest-asyncio** - 非同期テスト用
- **pytest-mock** - モックサポート
- **ruff** - リンター・フォーマッター
- **mypy** - 静的型チェッカー
- **types-PyYAML** - PyYAMLの型スタブ

## プロジェクト構成

```
llminfo-cli/
├── llminfo_cli/
│   ├── __init__.py
│   ├── main.py              # CLIエントリーポイント
│   ├── providers/
│   │   ├── __init__.py      # プロバイダーファクトリー
│   │   ├── base.py          # プロバイダーベースクラス
│   │   ├── generic.py       # 汎用プロバイダー
│   │   ├── parsers.py       # レスポンスパーサー（Strategy Pattern）
│   │   └── openrouter.py    # OpenRouter実装
│   ├── cache.py             # キャッシュ管理
│   ├── validators.py       # プロバイダー設定バリデーション
│   └── schemas.py          # データモデル定義
├── tests/
│   ├── __init__.py
│   ├── test_providers.py
│   ├── test_integration.py
│   ├── test_list_models.py
│   ├── test_cache.py
│   └── test_cli_commands.py
├── providers.yml           # プロバイダー設定
├── plugin/                 # プロバイダープラグイン（.gitignore）
├── pyproject.toml
├── README.md
├── README.ja.md
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

class CreditInfo(BaseModel):
    total_credits: float
    usage: float
    remaining: float

class Provider(ABC):
    @abstractmethod
    async def get_models(self) -> List[ModelInfo]:
        """モデル一覧を取得"""
        pass

    @abstractmethod
    async def get_credits(self) -> Optional[CreditInfo]:
        """クレジット情報を取得（存在する場合）"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """プロバイダー名"""
        pass
```

#### ResponseParser Strategy Pattern
```python
# providers/parsers.py

from abc import ABC, abstractmethod
from typing import List, Optional

class ResponseParser(ABC):
    @abstractmethod
    def parse_models(self, response: dict) -> List[ModelInfo]:
        pass

    @abstractmethod
    def parse_credits(self, response: dict) -> Optional[CreditInfo]:
        pass

class OpenAICompatibleParser(ResponseParser):
    """OpenAI互換API用パーサー"""
    def parse_models(self, response: dict) -> List[ModelInfo]:
        data = response.get("data", [])
        return [
            ModelInfo(
                id=m.get("id", ""),
                name=m.get("id", ""),
                context_length=m.get("context_length"),
                pricing=m.get("pricing"),
            )
            for m in data
        ]

class OpenRouterParser(ResponseParser):
    """OpenRouter専用パーサー"""
    def parse_models(self, response: dict) -> List[ModelInfo]:
        data = response.get("data", [])
        return [
            ModelInfo(
                id=m["id"],
                name=m["name"],
                context_length=m.get("context_length"),
                pricing=m.get("pricing"),
            )
            for m in data
        ]

    def parse_credits(self, response: dict) -> Optional[CreditInfo]:
        data = response.get("data", {})
        total_credits = data.get("total_credits", 0.0)
        total_usage = data.get("total_usage", 0.0)

        return CreditInfo(
            total_credits=total_credits,
            usage=total_usage,
            remaining=total_credits - total_usage,
        )
```

#### 汎用プロバイダー
```python
# providers/generic.py

class GenericProvider(Provider):
    """設定ファイルベースの汎用プロバイダー"""

    def __init__(
        self,
        provider_name: str,
        base_url: str,
        api_key_env: str,
        models_endpoint: str,
        parser: ResponseParser,
        api_key: Optional[str] = None,
        credits_endpoint: Optional[str] = None,
    ):
        self.provider_name_value = provider_name
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.api_key = api_key or os.environ.get(api_key_env)
        self.models_endpoint = models_endpoint
        self.parser = parser
        self.credits_endpoint = credits_endpoint

    async def get_models(self) -> List[ModelInfo]:
        if not self.api_key:
            raise ValueError(f"{self.api_key_env} environment variable not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{self.models_endpoint}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return self.parser.parse_models(data)

    async def get_credits(self) -> Optional[CreditInfo]:
        if not self.api_key:
            raise ValueError(f"{self.api_key_env} environment variable not set")

        if not self.credits_endpoint:
            return None

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{self.credits_endpoint}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return self.parser.parse_credits(data)

    @property
    def provider_name(self) -> str:
        return self.provider_name_value
```

#### OpenRouter実装（GenericProvider使用）
```python
# providers/openrouter.py

class OpenRouterProvider(Provider):
    """OpenRouter.ai プロバイダー実装"""

    BASE_URL = "https://openrouter.ai/api/v1"
    API_KEY_ENV = "OPENROUTER_API_KEY"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(self.API_KEY_ENV)

    async def get_models(self) -> List[ModelInfo]:
        if not self.api_key:
            raise ValueError(f"{self.API_KEY_ENV} environment variable not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]

            return [
                ModelInfo(
                    id=m["id"],
                    name=m["name"],
                    context_length=m.get("context_length"),
                    pricing=m.get("pricing"),
                )
                for m in data
            ]

    async def get_credits(self) -> Optional[CreditInfo]:
        if not self.api_key:
            raise ValueError(f"{self.API_KEY_ENV} environment variable not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/credits",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]

            total_credits = data.get("total_credits", 0.0)
            total_usage = data.get("total_usage", 0.0)

            return CreditInfo(
                total_credits=total_credits,
                usage=total_usage,
                remaining=total_credits - total_usage,
            )

    @property
    def provider_name(self) -> str:
        return "openrouter"
```

#### プロバイダー設定ファイル
```yaml
# providers.yml

providers:
  groq:
    name: "groq"
    base_url: "https://api.groq.com/openai/v1"
    api_key_env: "GROQ_API_KEY"
    models_endpoint: "/models"
    parser: "openai_compatible"
    credits_endpoint: null

  openrouter:
    name: "openrouter"
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"
    models_endpoint: "/models"
    parser: "openrouter"
    credits_endpoint: "/credits"
```

### 2. CLIコマンド構成

#### メインコマンド階層
```bash
# ルートコマンド
llminfo                    # ヘルプ表示
llminfo credits              # クレジット確認
llminfo test-provider        # プロバイダーテスト
llminfo import-provider      # プロバイダーインポート

# グローバルオプション
--json                      # JSON出力
--provider <provider>       # プロバイダー指定
```

#### creditsサブコマンド
```bash
llminfo credits --provider openrouter  # OpenRouterのクレジット
llminfo credits --json               # JSON形式で出力
```

#### test-providerサブコマンド
```bash
llminfo test-provider plugin/new-provider.yml  # プラグイン設定をテスト
llminfo test-provider plugin/new-provider.yml --api-key key  # APIキー指定
```

#### import-providerサブコマンド
```bash
llminfo import-provider plugin/new-provider.yml  # テスト成功後にproviders.ymlへ追加
```

### 3. 出力形式

#### テーブル形式（デフォルト）
```
Total Credits: $15.00
Usage: $2.67
Remaining: $12.33
```

#### JSON形式
```json
{
  "total_credits": 15.0,
  "usage": 2.66625653,
  "remaining": 12.33374347
}
```

### 4. エラーハンドリング

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

### 5. テスト戦略

#### 単体テスト
```python
# tests/test_providers.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from llminfo_cli.providers import get_provider

@pytest.mark.asyncio
async def test_openrouter_get_models():
    provider = OpenRouterProvider(api_key="test_key")

    mock_response_data = {
        "data": [
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o Mini",
                "context_length": 128000,
                "pricing": {"prompt": "0.00015"},
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        models = await provider.get_models()

        assert len(models) == 1
        assert models[0].id == "openai/gpt-4o-mini"
```

#### 統合テスト
```python
# tests/test_integration.py

import pytest
import os

@pytest.mark.integration
@pytest.mark.asyncio
async def test_openrouter_get_models_real():
    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set in environment")

    provider = OpenRouterProvider(api_key=api_key)
    models = await provider.get_models()

    assert len(models) > 0
```

### 6. 配布設定

#### pyproject.toml
```toml
[project]
name = "llminfo-cli"
version = "0.1.0"
description = "CLI tool for LLM model information"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "types-PyYAML>=6.0.0",
]

[project.scripts]
llminfo = "llminfo_cli.main:app"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true

[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests (requires API keys)"
]
```

### 7. 実装フェーズ

#### Phase 1: 基盤整備（完了）
1. プロジェクト構成の作成
2. 基礎データモデルの実装
3. 設定ファイルの作成（.env.example）

#### Phase 2: プロバイダー実装（完了）
1. GenericProviderの実装
2. ResponseParser Strategy Patternの実装
3. OpenRouterプロバイダーの実装
4. プロバイダー設定ファイル（providers.yml）の作成

#### Phase 3: プラグインシステム実装（完了）
1. test-providerコマンドの実装
2. import-providerコマンドの実装
3. プラグインディレクトリの作成

#### Phase 4: テスト（完了）
1. 単体テストの作成
2. 統合テストの作成
3. カバレッジの設定

#### Phase 5: ドキュメンテーション（完了）
1. README.mdの作成
2. SPEC.mdの作成
3. BLUEPRINT.mdの作成
4. 使用例の追加

#### Phase 6: 配布準備（完了）
1. PyPIへの配布設定
2. GitHubリポジトリの作成
3. MIT Licenseの追加

## 将来の拡張

### マイルストーン v1.1
- [ ] 複数プロバイダーの料金比較機能
- [ ] モデル詳細情報の表示（`llminfo info <model_id>`）
- [ ] モデルフィルタリング機能（`--filter "price<0.01"`）
- [ ] 履歴管理（最近使用したモデルを保存）

### マイルストーン v1.2
- [ ] インタラクティブモード（TUI）
- [ ] モデル評価機能
- [ ] カスタムパーサーのプラグイン対応
