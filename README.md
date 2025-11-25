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
- **マルチテナント (Mock):** テナント間のデータと知識（RAG）を論理的に完全分離。

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
認証には HttpOnly Cookie を採用し、XSS対策を強化しています。

```mermaid
graph TD
    User["User / Browser"] -->|"HTTPS / Cookie Auth"| FE["Angular Frontend (Prism UI)"]
    FE -->|"REST API / Session Cookie"| BE["FastAPI Backend"]
    
    subgraph "Governance Kernel (Backend)"
        BE --> Auth["Auth Manager (Multi-tenant)"]
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

  * **Frontend:** Angular 20+, Angular Material (Enterprise UI), Signals, ngx-markdown
  * **Backend:** Python 3.11+, FastAPI (ASGI/Async), SQLModel
  * **Auth:** Mock Auth (Development) / Ready for OIDC (Production), HttpOnly Cookie
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

## 📦 Installation & Quick Start

### 1\. Default Login Credentials (初期ログイン情報)

本バージョン(v1.1.0)では、開発用として以下の **Mockアカウント** が初期設定されています。
ログイン画面では以下の組み合わせを入力してください。

| Role | Tenant ID | User ID | 権限 |
| :--- | :--- | :--- | :--- |
| **Admin** | `tenant-a` | `user-1` | **管理者** (全ログ閲覧可) |
| User | `tenant-a` | `user-2` | 一般ユーザー (自分のログのみ) |
| User | `tenant-b` | `user-1` | 別テナントの一般ユーザー |

> [\!WARNING]
> **Production Security Alert (商用利用時の注意)**
>
> 上記の `Mock Auth` および初期アカウントは、**開発・テスト専用**です。
> 本番環境（Production）で運用する際は、必ず以下のセキュリティ対策を実施してください。
>
> 1.  **Switch to Real IdP:** `backend/auth.py` のモックロジックを無効化し、**Azure AD (Entra ID)**, **Auth0**, **Google Workspace** 等の OIDC/SAML 認証プロバイダに接続する実装へ差し替えてください。
> 2.  **Disable Mock Login:** `/auth/mock-login` エンドポイントを削除または無効化してください。
> 3.  **Rotate Keys:** `.env` 内の `SECRET_KEY` は、推測不可能な長く複雑な文字列に変更してください。

-----

### 2\. Docker Launch (推奨)

プロジェクトのルートディレクトリで以下のコマンドを実行します。

```bash
# 1. 環境変数の設定
cp .env.example .env
# .env を編集し、GEMINI_API_KEY を設定してください

# 2. 起動
docker-compose up -d --build
```

Access: `http://localhost`

### 3\. Manual Launch (開発用)

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
ng serve
```

Access: `http://localhost:4200`

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

## 📝 License

[MIT](https://www.google.com/search?q=LICENSE)

