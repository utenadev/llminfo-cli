# llminfo-cli リポジトリ分析レポート

**日付:** 2026年1月3日
**分析対象:** llminfo-cli リポジトリ

## 1. 全体評価

*   **品質**: 非常に高い。`Typer`, `Rich`, `Pydantic`, `Httpx` などのモダンなスタック選定、`Ruff`/`Mypy`による静的解析、Strategyパターンを用いた設計など、プロフェッショナルな品質です。
*   **ドキュメント**: `README.md`、`GEMINI.md`、`SPEC.md` が整備されており、開発者・ユーザー双方にとって分かりやすい状態です。
*   **CI**: GitHub Actionsでテスト、Lint、型チェック、カバレッジ計測（80%以上）が自動化されており理想的です。

## 2. 重要・致命的な指摘（Critical）

### 🚨 `providers.yml` の配置と読み込み・書き込み権限
現在、`providers.yml` はプロジェクトルートに配置されていますが、配布時および実行時の挙動において重大な問題があります。

*   **問題A: 配布パッケージに含まれない可能性**
    `pyproject.toml` の設定では、デフォルトで `llminfo_cli` パッケージ内のファイルは含まれますが、ルートにある `providers.yml` は明示的に含める設定をしない限りパッケージに含まれません。`pip install` したユーザーの手元にはこのファイルが存在せず、実行時エラーになります。

*   **問題B: 読み込みパスの脆弱性**
    `llminfo_cli/providers/__init__.py` 内で以下のようにパスを指定しています：
    ```python
    Path(__file__).parent.parent.parent / "providers.yml"
    ```
    パッケージとしてインストールされた場合、この相対パスは `site-packages` ディレクトリのルートなどを指してしまい、意図したファイルを読み込めません。

*   **問題C: `import-provider` の権限エラー**
    `import-provider` コマンドは `providers.yml` に追記しようとします。しかし、通常のユーザー権限で `pip install` した場合、インストール先（システムの `site-packages` 等）への書き込み権限がないため、このコマンドは `PermissionError` で失敗します。

#### 改善提案
1.  **内蔵設定の移動**: `providers.yml` を `llminfo_cli/data/providers.yml` など、パッケージ内部に移動し、`importlib.resources` または `pkgutil` を使って読み込むように変更する。
2.  **ユーザー設定のサポート**: `~/.config/llminfo/providers.yml` (XDG Base Directory準拠) などのユーザー固有の設定ファイルをサポートし、`import-provider` はこちらに書き込むようにする。読み込み時は「内蔵設定 + ユーザー設定」をマージする設計にする。

## 3. アーキテクチャ・コードへの指摘

### エラーハンドリングの一貫性
`llminfo_cli/errors.py` で `APIError`, `NetworkError` 等の例外階層が定義されていますが、活用が不十分です。
*   **現状**: `main.py` で `httpx.HTTPStatusError` などを直接 catch している箇所があります。
*   **提案**: Provider層で `httpx` の例外を `APIError` や `NetworkError` にラップして再送出し、CLI層（main.py）は `LLMInfoError` 系のみをハンドリングするように変更することで、責務の分離と保守性が向上します。

### キャッシュの非同期対応
`cache.py` で標準の `open()` を使用していますが、これはブロッキングI/Oです。
*   **現状**: CLIツールでありファイルサイズも小さいため実害は少ないですが、全体が非同期設計であるため一貫性に欠けます。
*   **提案**: `aiofiles` を導入して非同期ファイルI/Oにすることを検討してください。

### CIのPythonバージョン
`.github/workflows/ci.yml` で `python-version: "3.14"` が指定されています。
*   **指摘**: Python 3.14 は現時点でまだ一般的ではない（開発版の）可能性があります。
*   **提案**: 実際のターゲット環境に合わせて、`["3.11", "3.12", "3.13"]` のマトリックスビルドを行うことを推奨します。

## 4. 推奨アクションプラン

まず最初に着手すべきは **「`providers.yml` 問題」の修正** です。これを行わないと、PyPI等で配布しても正常に動作しません。

1.  **設定ファイルの分離**:
    *   デフォルト設定をパッケージ内部（`llminfo_cli/` 下）へ移動。
    *   ユーザー設定（`~/.config/...`）の読み込みロジックを追加。
2.  **ビルド設定の修正**: `pyproject.toml` にデータファイルを含める設定を追加。
3.  **CI設定の修正**: Pythonバージョンマトリックスの修正。
