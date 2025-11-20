# Prism RAG ハイブリッド検索テスト一式 README

このディレクトリは、Prism / Governance Kernel の **RAG（HybridRetriever）検証用テスト仕様**をまとめたものです。
自分用ログとして Git 管理しやすいよう、内容を複数ファイルに分割しています。

## ファイル一覧

- `rag_test_README.md` …… このファイル。テスト一式の概要。
- `rag_test_documents.md` …… RAG に登録するテストドキュメント（D1〜D4）の内容定義。
- `rag_test_cases.md` …… テストケース（T-FTS / T-VEC / T-HYB 系）の定義。
- `rag_test_execution.md` …… 実行手順・合否判定の基準。

## 想定フォルダ構成（例）

```text
backend/
  tests/
    rag_hybrid/
      rag_test_README.md
      rag_test_documents.md
      rag_test_cases.md
      rag_test_execution.md
```

## PDF 化について

この環境で自動生成した PDF は、日本語フォントが埋め込めず「■」になってしまうため、
**Markdown をローカル環境で PDF に変換して使うことを推奨**します。

例（VS Code の場合）:

1. いずれかの `rag_test_*.md` を開く
2. 「印刷」→ プリンタに「Microsoft Print to PDF」などを選択
3. PDF として保存

または `pandoc` 等を使っても構いません。

