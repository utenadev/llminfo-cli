# コーディングとテストルール

## 1. Pythonパッケージ構造と依存関係

### 1.1 コア依存関係
- **CLIフレームワーク (typer)**: 型安全なCLI定義、自動ヘルプ生成、サブコマンドサポート
- **HTTPクライアント (httpx)**: 非同期HTTPリクエスト、自動再試行、タイムアウト管理
- **データバリデーション (pydantic)**: APIレスポンスのバリデーション、型安全なデータモデル
- **リッチテキスト (rich)**: テーブルフォーマット、カラフルな出力
- **設定管理 (pyyaml)**: YAML形式の設定ファイルパース
- **非同期ファイル操作 (aiofiles)**: 非同期でのファイル読み書き

### 1.2 開発依存関係
- **タスクランナー (go-task)**: セットアップ、テスト、リンター等のタスク自動化
- **テストフレームワーク (pytest)**: 単体テストと統合テスト
- **非同期テスト (pytest-asyncio)**: 非同期関数のテストサポート
- **モッキング (pytest-mock)**: 外部依存のモック化
- **リンター (ruff)**: コードスタイルの一貫性、インポートの整理
- **型チェッカー (mypy)**: 静的型解析、型安全性の確保

### 1.3 パッケージ構造
```
llminfo_cli/
├── ... (ソースコード)
├── Taskfile.yml         # タスク定義ファイル
├── pyproject.toml       # プロジェクト設定・依存関係
├── providers.yml        # プロバイダー設定
└── tests/               # テストコード
```

## 2. コーディング標準

### 2.1 型アノテーション
- **厳格な型付け**: すべての関数に完全な型アノテーション
- **データモデル**: Pydanticモデルを積極的に使用
- **オプショナル型**: `Optional[T]` または `T | None` を使用
- **型エイリアス**: 複雑な型定義には型エイリアスを使用

### 2.2 エラーハンドリング
- **階層化された例外**: `errors.py` で定義された `APIError`, `NetworkError` 等を使用
- **ユーザーへの通知**: スタックトレースではなく、理解しやすいエラーメッセージを表示
- **終了コード**: 正常終了は0、エラー時は1

### 2.3 非同期処理
- **完全非同期**: `asyncio` と `httpx.AsyncClient` を使用
- **メインループ**: `asyncio.run()` で実行
- **タイムアウト**: 全てのリクエストにタイムアウトを設定 (デフォルト30秒)

## 3. テスト戦略

### 3.1 単体テスト
- **モッキング**: `unittest.mock` と `pytest-mock` を使用して外部API呼び出しをモック
- **フィクスチャ**: 共通のセットアップを再利用

#### 単体テスト例 (`tests/test_providers.py` より)
```python
@pytest.mark.asyncio
async def test_openrouter_get_models():
    """Test fetching models from OpenRouter"""
    provider = OpenRouterProvider(api_key="test_key")

    mock_response_data = {
        "data": [
            {
                "id": "openai/gpt-4o-mini:free",
                "name": "GPT-4o Mini (Free)",
                "context_length": 128000,
                "pricing": {"prompt": "0.0", "completion": "0.0"},
            },
        ]
    }

    # モックの作成
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    # httpx.AsyncClientをパッチ
    with patch("httpx.AsyncClient", return_value=mock_client):
        models = await provider.get_models()

        assert len(models) == 1
        assert models[0].id == "openai/gpt-4o-mini:free"
```

### 3.2 統合テスト
- **実際のAPI**: 環境変数 (`.env.test`) を使用して実際のAPIをテスト
- **マーカー**: `@pytest.mark.integration` を付与して区別

#### 統合テスト例
```python
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

## 4. 実装パターン

### 4.1 汎用実装パターン (`GenericProvider`)
設定ファイルベースのプロバイダーに対応するための汎用クラス。

```python
class GenericProvider(Provider):
    """Generic provider implementation for configuration-based providers"""

    def __init__(
        self,
        provider_name: str,
        base_url: str,
        api_key_env: str,
        models_endpoint: str,
        parser: ResponseParser,
        api_key: Optional[str] = None,
        credits_endpoint: Optional[str] = None,
        cache_ttl_hours: int = 1,
    ):
        self.provider_name_value = provider_name
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.api_key = api_key or os.environ.get(api_key_env)
        # ... (省略)
```

### 4.2 レスポンスパーサーパターン (Strategy)
APIごとのレスポンス形式の違いを吸収するためのStrategyパターン。

```python
class ResponseParser(ABC):
    @abstractmethod
    def parse_models(self, response: dict) -> List[ModelInfo]:
        """Parse models from API response"""
        pass

class OpenAICompatibleParser(ResponseParser):
    def parse_models(self, response: dict) -> List[ModelInfo]:
        data = response.get("data", [])
        # ... (パース処理)
        return [ModelInfo(...) for m in data]
```

## 5. CLIコマンド実装

### 5.1 コマンド定義 (`main.py` より)
Typerを使用したコマンド定義とエラーハンドリング。

```python
@app.command()
def credits(
    provider: str = typer.Option("openrouter", "--provider", help="Provider name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display credit balance for the specified provider"""

    async def run():
        try:
            provider_instance = get_provider(provider)
            credits_info = await provider_instance.get_credits()

            if json_output:
                typer.echo(json.dumps(credits_info.model_dump(), indent=2))
            else:
                typer.echo(f"Total Credits: ${credits_info.total_credits:.2f}")
                # ...
        except ValueError as e:
            typer.echo(str(e), err=True)
            sys.exit(1)
        # ... (その他の例外処理)

    asyncio.run(run())
```

## 6. 設定とバリデーション

### 6.1 設定ファイル (`providers.yml`)
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

## 7. キャッシュ戦略
- **場所**: `~/.cache/llminfo/` (OS依存)
- **TTL**: デフォルト1時間
- **形式**: JSONファイルとして保存
- **制御**: `--force` フラグでキャッシュを無視して再取得

## 8. 互換性ルール

### 8.1 Pythonバージョン
- **サポートバージョン**: Python 3.11+
- **非推奨**: 3.10以下はサポート対象外

### 8.2 新機能の利用
Python 3.11以降の機能（`Self`型、例外グループなど）は、`typing_extensions` バックポートを利用するか、バージョンチェックを行った上で使用する。

## 9. 開発フロー



### 9.1 タスク自動化 (Taskfile)

プロジェクトのセットアップ、テスト、静的解析などはすべて `task` コマンドを通じて実行することを原則とします。



#### 主要なタスク

- **セットアップ**: `task setup` (仮想環境の作成と依存関係のインストール)

- **テスト実行**: 

  - 全テスト: `task test`

  - 単体テストのみ: `task test-unit`

  - 統合テスト: `task test-integration` (要 `dotenvx`)

- **静的解析**:

  - リンター確認: `task lint`

  - 自動修正: `task lint-fix`

  - 型チェック: `task type-check`

- **一括チェック**: `task check` (lint, type-check, testを順に実行)

- **クリーンアップ**: `task clean` (一時ファイルやキャッシュの削除)



### 9.2 推奨される開発サイクル

1. **初期化**: `task setup`

2. **実装**: `llminfo_cli/` 以下のコードを変更

3. **検証**: `task check` で静的解析とテストが通過することを確認

4. **提出**: 全てのチェックが通過した状態でコミット/プッシュ
