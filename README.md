# 🔺 Prism - Enterprise AI Governance Hub

> **Intelligent Gateway for Secure & Optimized LLM Orchestration**

![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/version-1.0.0-green)
![Status](https://img.shields.io/badge/status-Active-success)

**Prism (プリズム)** は、企業利用を想定した次世代の AI ガバナンス・プラットフォームです。
ユーザーと複数の LLM（Gemini, GPT 等）の間に「ガバナンス・カーネル」を配置することで、セキュリティ、コスト最適化、そして業務特化型の推論能力を同時に提供します。

---

## 🚀 Key Features (主な機能)

### 1. Dynamic Governance Kernel
入力内容をリアルタイムで解析し、最適な「モード」へ自動ルーティングします。
- **FLASH Mode:** ニュースや株価などの速報（Web検索）
- **HEAVY Mode:** 契約書や医療情報の精密分析（PII検知・高精度モデル）
- **FAST Mode:** 日常的な雑談や軽量タスク

### 2. Multi-modal Analysis
複数のファイル（PDF, CSV, Excel）を同時にアップロードし、LLM のコンテキストウィンドウに統合。
- **比較分析:** A社とB社の決算書PDFを比較し、差異を表形式で出力。
- **データ抽出:** 非構造化データからのインサイト抽出。

### 3. Audit Logging & Transparency
全てのインタラクションは SQLite ベースの監査ログに記録されます。
- **UI統合:** サイドバーから過去のログ（使用モデル、レイテンシ、モード）を即座に確認・復元可能。
- **透明性:** AI が「なぜその回答をしたか」のプロセスが可視化されます。

---

## 🛠 Architecture

Frontend (Angular) と Backend (FastAPI) によるモダンな疎結合アーキテクチャを採用しています。

```mermaid
graph TD
    User[User / Browser] -->|HTTPS / Multipart| FE["Angular Frontend (Prism UI)"]
    FE -->|REST API / FormData| BE[FastAPI Backend]
    
    subgraph "Governance Kernel (Backend)"
        BE --> Parser[File Parser (PDF/CSV)]
        BE --> Router[Mode Router]
        BE --> PII[PII Shield]
        Router -->|Routing| Model[LLM Orchestrator]
    end
    
    Model -->|API Call| Google[Google Gemini 1.5 Pro/Flash]
    BE -->|Audit Log| DB[(SQLite / Audit DB)]
````

### Tech Stack

  * **Frontend:** Angular 18+, Angular Material, Signals, ngx-markdown
  * **Backend:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy
  * **AI Engine:** Google Gemini 1.5 Pro / Flash (via Google Gen AI SDK)
  * **Data:** SQLite (Audit Logs), ChromaDB (Future plan for RAG)

-----

## 📦 Installation

### Prerequisites

  * Python 3.10+
  * Node.js 20+
  * Google Gemini API Key

### 1\. Backend Setup (FastAPI)

```bash
cd backend

# 仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1

# 依存ライブラリのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .env ファイルを開き、GEMINI_API_KEY を入力してください
```

### 2\. Frontend Setup (Angular)

```bash
cd frontend

# 依存ライブラリのインストール
npm install

# 開発サーバーの起動
ng serve
```

Access `http://localhost:4200` to launch Prism.

-----

## 📖 Usage Guide

### 決算書の比較分析（例）

1.  サイドバーの「New Chat」をクリック。
2.  画面下部のクリップアイコン📎から、比較したい複数のPDF（例：決算短信）を選択。
3.  メッセージ欄に\*\*「アップロードした2社の営業利益率を比較し、表にまとめて」\*\*と入力して送信。
4.  Prism がファイルを解析し、Markdown 形式でレポートを出力します。

### 監査ログの確認

1.  サイドバーの「Audit Logs」リストを確認。
2.  過去の履歴をクリックすると、その時点の会話コンテキストがメイン画面に復元されます。

-----

## ⚙️ Configuration (Policies)

`backend/policies.yaml` を編集することで、ガバナンスルールをノーコードで調整可能です。

```yaml
modes:
  - id: "HEAVY"
    safety_level: "high"
    allow_web_search: true
    triggers:
      keywords_any: ["契約", "法務", "PII"]
```

-----

## 🛡 Security Note

  * 本システムは **PII（個人識別情報）** の簡易検知機能を備えていますが、完全な保護を保証するものではありません。
  * 実際の機密データを扱う際は、オンプレミス LLM への切り替えや、エンタープライズ契約済みの API 利用を推奨します。

-----

## 📝 License

[MIT](https://www.google.com/search?q=LICENSE)

````
