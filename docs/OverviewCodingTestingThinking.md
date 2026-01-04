# 概要: LLM協働開発のためのコーディング・テストガイド

このドキュメントは、人間とLLMがソフトウェアを共同開発するためのコーディングおよびテストの標準指針です。
目標は、PythonであれGolangであれ、**「AIエージェントが理解しやすく、かつ自律的に検証可能なコード」**を書くことです。

## 1. コーディング標準: "Guardrails for AI"

LLMは確率的にコードを生成するため、厳格な制約（ガードレール）が必要です。言語機能を用いて、AIの「幻覚」を防ぎます。

### 1.1 強い型付け (Strong Typing)
**言語を問わず、型定義は「LLMへの最強のドキュメント」です。**

- **Pythonの場合**:
    - `Any` は禁止（AIに「何でもいい」と伝えるとバグります）。
    - `Pydantic` モデルを使用して、データ構造を強制する。
- **Golangの場合 (将来)**:
    - `interface` を小さく定義し、構造体の役割を明確にする。
    - `struct` タグを活用し、JSON等の入出力形式を明示する。
- **TypeScriptの場合 (将来)**:
    - `Zod` 等で実行時バリデーションを行う。

### 1.2 自己文書化コード (Self-Documenting Code)
- **Docstrings/Comments**:
    - 関数の中身を書く**前**に、Docstring（プロンプト）を書くフローを推奨します。
    - LLMは関数名とDocstringを見て、実装を補完します。

## 2. テスト戦略: "Test-Driven Generation (TDG) with Interactive Hearing"

人間が全てのテストコードを書く必要はありません。
重要なのは、**「何が正解か（テストケース）」をAIと合意すること**です。

### 2.1 TDGの実践フロー
このプロジェクトでは、以下のサイクルで開発を進めることを推奨します。

1. **Scaffold (足場作り)**:
    - AI: `SPEC.md` を元に、「テストシナリオのリスト（日本語）」を提示する。
    - Human: シナリオを確認し、不足があれば指摘する（例: 「ネットワークエラー時のテストが足りないよ」）。

2. **Test Generation (テスト生成)**:
    - AI: 合意されたシナリオを元に、失敗するテストコード（Red）を実装する。
    - **重要**: 実装（本体コード）を書く前に、テストだけをコミットまたは提示し、期待値が合っているか確認する。

3. **Implementation (実装)**:
    - AI: テストをパスする最小限の実装（Green）を行う。

4. **Refactoring**:
    - AI & Human: コードを整理し、可読性を高める。テストがガードレールとなり、安全にリファクタリングできる。

### 2.2 テスト生成ツールの可能性
将来的に、この「ヒアリング → テスト生成」のプロセス自体を自動化ツール（CLI/Web）として切り出すことも検討しています。
AIエージェントは、常に**「テストを書くための情報は揃っているか？」**を自問し、不足があれば人間にヒアリングを行う姿勢を持ってください。

### 2.3 外部依存のモック化
AIエージェントが試行錯誤する際、実際のAPIを叩くとレート制限にかかったり、データが汚染されたりします。
- **原則**: 開発・テスト時の外部I/O（HTTP, DB）はすべてモック可能にする。
- **Dependency Injection**: コンストラクタでAPIクライアント等を注入する設計にする（PythonでもGoでも共通のベストプラクティス）。

## 3. 自動化インターフェース: "Taskfile"

言語やフレームワークが増えても（Python, Go, Node.js）、**「AIエージェントへの命令」は統一**します。
私たちは `go-task` (Taskfile) を標準インターフェースとして採用します。

### 3.1 標準タスク定義
言語に関わらず、以下のコマンドが動作するように `Taskfile.yml` を維持してください。

- `task setup`: 依存関係のインストール、環境構築。
- `task test`: テストの実行。
- `task lint`: コードスタイルのチェック。
- `task check`: **品質保証の決定版**。Lint, Type-Check, Testを一括実行。
    - **ルール**: AIエージェントは、作業完了宣言の前に必ず `task check` をパスさせなければならない。

## 4. 技術スタック別ガイドライン

プロジェクトのフェーズや要件に応じて、適切なスタックを選択します。

### A. Python CLI (Current Default)
現在の `llminfo-cli` などの開発標準です。
- **Core**: Typer, Pydantic, HTTPX
- **Testing**: Pytest, Pytest-Asyncio, Pytest-Mock
- **Lint/Format**: Ruff, Mypy

### B. Python Web/Server (Future)
データ処理やAPIサーバー向け。
- **Core**: FastAPI
- **Interface**: OpenAPI (schema-first development)

### C. Golang / High Performance (Future)
バイナリ配布や高並行処理が必要な場合。
- **Project Layout**: `Standard Go Project Layout` (cmd/, internal/, pkg/)
- **Core**: Cobra (CLI), Echo/Gin (Web)
- **Lint**: golangci-lint
