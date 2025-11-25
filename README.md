# 🔺 Prism - Enterprise AI Governance Hub

> **Intelligent Gateway for Secure, Cost-Optimized, and RAG-Enhanced LLM Orchestration.**

![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/version-1.1.0-green)
![Status](https://img.shields.io/badge/status-Production_Ready-success)

**Prism (プリズム)** は、企業利用を想定し、セキュリティとコスト管理を両立させた次世代の AI ガバナンス・プラットフォームです。
ユーザーとLLMの間に「ガバナンス・カーネル」を配置することで、安全に社内情報（RAG）を活用し、業務特化型の推論を実現します。

---

## 🚀 Key Features (主な機能)

### 1. 🔐 Multi-User & Secure Login [NEW]
**複数ユーザーによる同時ログインとセッション分離に対応しました。**
- **個別認証:** ユーザーごとのID管理により、セキュアなアクセス制御を実現。
- **履歴の分離:** チャット履歴や監査ログはユーザーID（`user_id`）に紐づいて管理され、他者のデータと混在することはありません。
- **パーソナライズ:** ユーザーごとの利用状況に応じたコンテキスト維持が可能。

### 2. 🛡️ Governance & Dynamic Routing
入力内容をリアルタイムで解析し、最適な「モード」へ自動ルーティングします。
- **FLASH Mode:** ニュースや株価などの速報（Web検索利用）。
- **HEAVY Mode:** 契約書や医療情報の精密分析（PII検知・高精度モデル）。
- **PII Shield:** 機密情報（個人情報など）を検知し、外部流出を未然に防ぐマスキング機能。

### 3. 🧠 Hybrid RAG (Retrieval-Augmented Generation)
**ChromaDB (ベクトル検索)** と **SQLite (キーワード検索)** を組み合わせたハイブリッド検索エンジンを搭載。
- **ナレッジベース:** 社内規定やマニュアルを登録し、AIに「長期記憶」を持たせることが可能。
- **高精度な検索:** 「概念（ゼロトラスト）」と「品番（PROJ-A77）」の両方を正確に検索し、ハルシネーション（嘘）を抑制。

### 4. 📊 Multi-modal Analysis
複数のファイル（PDF, CSV, Excel）を同時にアップロードし、LLM のコンテキストウィンドウに統合。
- **比較分析:** 複数の決算書PDFを読み込み、差異や数値を比較してMarkdownの表形式で出力。

### 5. ✨ Real-time UX & Audit
- **ストリーミング応答 (NDJSON):** AIの回答をリアルタイムで画面に逐次表示し、応答待ちのストレスを解消。
- **監査ログ:** 全ての会話、使われたモデル、推論プロセスをデータベースに記録。サイドバーからログを復元し、利用状況を監査可能。

---

## 🛠 Architecture

Frontend (Angular) と Backend (FastAPI) によるモダンな疎結合アーキテクチャを採用しています。

```mermaid
graph TD
    User["User / Browser"] -->|"HTTPS / Auth"| FE["Angular Frontend (Prism UI)"]
    FE -->|"REST API / Bearer Token"| BE["FastAPI Backend"]
    
    subgraph "Governance Kernel (Backend)"
        BE --> Auth["Auth Manager (User Session)"]
        BE --> Router["Mode Router"]
        BE --> PII["PII Shield"]
        Router -->|"Routing"| Model["LLM Orchestrator"]
        
        subgraph "Hybrid RAG Engine"
            BE --> Vector["Vector Store (ChromaDB)"]
            BE --> Keyword["Keyword Store (SQLite)"]
        end
    end
    
    Model -->|"API Call"| Google["Google Gemini 2.5 Pro/Flash"]
    BE -->|"User Log & Audit"| DB[("SQLite / Audit DB")]
````

### Tech Stack

  * **Frontend:** Angular 18+, Angular Material (Enterprise UI), Signals, ngx-markdown
  * **Backend:** Python 3.11+, FastAPI (ASGI/Async), Pydantic
  * **Auth:** Session / Token Based Authentication
  * **AI Engine:** Google Gemini 2.5 Pro / Flash (Dynamic Model Routing)
  * **Data:** **ChromaDB** (Vector Search), **SQLite** (Audit Logs & Keyword Search)

-----

## 🤝 Contribution & Contact (利用上の注意)

**⚠️ IMPORTANT: ご利用の前に**

本プロジェクトは、筆者のポートフォリオおよび技術検証用として、AI駆動開発（AI-Driven Development）によって作成されました。

**本コードをフォーク、または商用利用・大規模展開のためにご活用される場合は、必ず事前に筆者までご連絡をお願いいたします。**
（学習用・個人利用の範囲であればご自由に参照ください）

これは、筆者がこのプロジェクトの貢献者として、また今後の開発ロードマップを把握するためのお願いです。

| 項目 | 詳細 |
| :--- | :--- |
| **連絡先** | GitHub Issue または kanade.yumesaki.mail@gmail.com |
| **ライセンス** | MIT (商用利用可能ですが、上記連絡をお願いします) |

-----

## 📦 Installation

この方法は、PythonやNode.jsの環境構築を一切スキップし、Prismを最も確実かつ迅速に起動できます。

### Prerequisites (必要なもの)

  * **Docker Desktop** (または Docker Engine)
  * Google Gemini API Key
  * Git Clone済みのPrismプロジェクト一式

-----

### 1\. 📂 依存関係の確認とDockerファイルの配置

以下の3つのファイルがプロジェクトの**ルートディレクトリ**にあり、内容が最新であることを確認してください。

  * `docker-compose.yml`
  * `Dockerfile.backend`
  * `Dockerfile.frontend`

#### ⚠️ 重要：Backend 依存関係の修正

エラーの再発を防ぐため、`backend/requirements.txt` に以下のライブラリが含まれていることを確認してください。

```text
# backend/requirements.txt (追記確認)
pypdf            # PDFパース機能
pydantic-settings # 環境変数処理
python-multipart # 認証フォームデータ処理用
passlib[bcrypt]  # パスワードハッシュ化 (認証用)
python-jose      # JWTトークン生成 (認証用)
```

-----

### 2\. 🔑 環境設定ファイル (.env) の作成

FastAPIコンテナにAPIキーを安全に渡すため、プロジェクトの**ルートディレクトリ**で設定ファイルを準備します。

```bash
# ルートディレクトリで実行
cp .env.example .env
```

`**.env**` ファイルを開き、`GEMINI_API_KEY` を入力して保存してください。

```text
# .env ファイル (ルートディレクトリ)
GEMINI_API_KEY="ここにあなたのGemini APIキーを記述します"
SECRET_KEY="認証用のランダムな文字列を設定してください"
```

-----

### 3\. ✨ Prismの起動 (One Command Launch)

プロジェクトのルートディレクトリで、以下のコマンドを一度だけ実行します。フロントとバックエンドが同時にビルド・起動し、バックグラウンドで動作します。

```bash
docker-compose up -d --build
```

### 4\. アクセスと利用

サーバーが立ち上がったら、ブラウザで以下のURLにアクセスしてください。

  * Access `http://localhost` to launch Prism.
  * ログイン画面が表示されます。初期ユーザー情報を入力してログインしてください。

起動中のサービスを停止・削除する場合は、同じディレクトリで `docker-compose down` を実行してください。

-----

## 📖 Usage Guide

### 1\. ログインと知識の登録

1.  ログイン画面でユーザー認証を行います。
2.  サイドバーの **「Knowledge Base」** をクリック。
3.  「Select Documents」から社内規定（PDF）やマニュアル（TXT）を選択し、**「Register to RAG」** をクリック。

### 2\. ハイブリッド検索とチャット

1.  「New Chat」に戻る。
2.  質問を入力（例：「プロジェクトA77の経費上限は？」）。
3.  Prismは **RAG（知識）** と **ガバナンス（モード判定）** を組み合わせ、最適なモデルで正確な回答をストリーミング生成します。

-----

## ⚙️ Configuration (Policies)

`backend/policies.yaml` を編集することで、ガバナンスルールをノーコードで調整可能です。

```yaml
modes:
  - id: "HEAVY"
    safety_level: "high"
    allow_web_search: false # 社内秘情報の流出防止
    triggers:
      keywords_any: ["契約", "法務", "PII"]
```

-----

## 🛡 Security Note

  * 本システムは **PII（個人識別情報）** の簡易検知機能を備えていますが、完全な保護を保証するものではありません。
  * 実際の機密データを扱う際は、法人契約の API（Vertex AIなど）を利用し、インフラのセキュリティ設定を厳格に行ってください。

-----

## 📝 License

[MIT](https://www.google.com/search?q=LICENSE)
