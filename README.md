# マルチ LLM Governance Kernel

マルチ LLM を「ポリシー駆動」で安全に使うための実験用プラットフォームです。
バックエンドは **Python / FastAPI**、フロントエンドは **Angular** で実装されており、

* **Governance Kernel**：

  * ユーザーの入力を解析して「モード（FAST / MEDIUM / HEAVY / FLASH）」を判定
  * ポリシーに基づいて LLM モデルを選択（例：Gemini 2.5 Flash / Pro）
  * すべてのリクエストを SQLite にログ保存
* **Policy Compiler**：

  * YAML で記述した独自 DSL（Policy DSL）から System Prompt を生成
  * ドメイン別のガバナンスルールを一元管理

現在は主に **Gemini 2.5 (Flash / Pro)** を使ったマルチモード・ルーティングが動作しており、
将来的には GPT / ローカル LLM / AWS Bedrock なども追加可能な構造になっています。

---

## アーキテクチャ概要

```text
┌────────────┐        ┌────────────────────┐       ┌────────────────────────┐
│ Angular UI │──HTTP→│ FastAPI Backend     │──→   │ LLM Providers           │
│ (frontend) │      │  - /chat             │      │  - Google Gemini 2.5    │
└────────────┘      │  - /policies         │      │  - OpenAI (将来/実験)   │
                    │  - /logs             │      │  - Local / others (予定)│
                    └──────────┬───────────┘       └────────────────────────┘
                               │
                               │ Policy DSL (policies.yaml)
                               │
                     ┌─────────▼─────────┐
                     │ Governance Kernel  │
                     │  - モード判定      │
                     │  - モデル選択      │
                     │  - PII/ドメイン検知│
                     └─────────▲─────────┘
                               │
                     ┌─────────┴─────────┐
                     │ Policy Compiler    │
                     │  - System Prompt   │
                     │    自動生成        │
                     └────────────────────┘
```

---

## 主な機能

### バックエンド（`backend/`）

* `/chat`

  * リクエスト：`{ user_id, message, metadata? }`
  * 処理フロー：

    1. `governance_kernel.py` でモード判定（FAST / HEAVY など）
    2. `policies.yaml` の `routing` ルールからモデルを選択
       （例：FAST → `google:gemini-2.5-flash`、HEAVY → `google:gemini-2.5-pro`）
    3. `policy_compiler.py` で System Prompt を構築
    4. `providers.py` 経由で LLM を呼び出し
    5. 結果を `logging_db.py` で SQLite に保存
  * レスポンス：

    ```json
    {
      "reply": "...",
      "mode": "FAST",
      "model": "google:gemini-2.5-flash",
      "policy_version": "0.1",
      "safety_flags": [],
      "tools_used": [],
      "latency_ms": 1234
    }
    ```

* `/policies`

  * 現在適用中の `policies.yaml` を返す（ポリシー可視化・デバッグ用）

* `/logs`

  * SQLite (`governance_logs.db`) に溜めたガバナンスログを返却
  * 後続で Angular のログビューアと接続予定

### フロントエンド（`frontend/`）

* Angular 20 ベースの SPA
* 現状のメイン画面：

  * **チャット UI**

    * メッセージ入力欄＋「送信」ボタン
    * 会話履歴を表示
    * 各 AI 応答の下に `model / mode / latency_ms` をバッジ表示

      * 例：`モデル: google:gemini-2.5-pro / モード: HEAVY / レイテンシ: xxxx ms`
* `frontend_skeleton_backup/` には今後追加予定のコンポーネントのスケルトンを保存

  * `policy-viewer`（ポリシー一覧 UI）
  * `log-viewer`（ログ一覧 UI） など

---

## 動作環境

* Python 3.11 付近を想定
* Node.js 20 系以上
* Angular CLI 20.x
* OS: Windows 11 で動作確認（他 OS でも動く想定）

---

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://gitlab.com/masahiro_suzuki/governance_kernel.git
cd governance_kernel
```

### 2. バックエンド（FastAPI）セットアップ

```bash
cd backend

# 仮想環境作成（任意のパスでOK）
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Git Bash / WSL の場合
# source .venv/Scripts/activate or .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

#### `.env` の設定

`backend/.env.example` をコピーして `.env` を作成し、API キーを設定します。

```bash
cp .env.example .env
```

`.env` の例：

```env
GEMINI_API_KEY=your_google_gemini_api_key_here

# 将来 OpenAI などを繋ぐとき
# OPENAI_API_KEY=sk-xxxx
```

> `.env` と `.venv` は `.gitignore` に入れてあり、Git にコミットされないようになっています。

#### バックエンド起動

```bash
cd backend
uvicorn main:app --reload --port 8000
```

* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* `POST /chat` から単体で動作確認もできます。

---

### 3. フロントエンド（Angular）セットアップ

別ターミナルを開いて：

```bash
cd governance_kernel/frontend

npm install
ng serve --open
```

* ブラウザで自動的に `http://localhost:4200` が開きます。
* 画面からメッセージを送ると、FastAPI の `/chat` → Gemini までの一連の流れが動作します。

---

## ポリシー DSL（`policies.yaml`）について

`backend/policies.yaml` に、ガバナンスルールを YAML ベースの DSL で定義しています。

主なセクション：

* `modes`

  * FAST / MEDIUM / HEAVY / FLASH などのモード定義
  * どのようなときにどのモードを使うかの抽象ルール

* `routing`

  * `when_mode_in` に応じて `primary_model` / `backup_models` を指定
  * 例：

    ```yaml
    - name: "heavy_sensitive_domains"
      when_mode_in: ["HEAVY"]
      primary_model: "google:gemini-2.5-pro"
      backup_models:
        - "openai:gpt5_1_thinking"  # 将来用スロット
    ```

* `safety`

  * PII 検知やドメインごとの禁止事項など（v0.1 では簡易）

この DSL を `policy_compiler.py` が解釈し、LLM に渡す System Prompt を自動生成します。

---

## ログ・監査

* `backend/logging_db.py` で簡易な SQLite ログを管理

  * テーブルには

    * `timestamp`
    * `user_id`
    * `mode`
    * `model`
    * `latency_ms`
    * `input_text` / `output_text`（必要に応じて）
  * 将来的に

    * ドメイン別集計
    * モード別利用率
    * コスト推定
      などをダッシュボード化する想定

* Angular 側では今後、`log-viewer` コンポーネントから `/logs` API を叩いてテーブル表示する予定

---

## 想定ユースケース

* 社内向け「AI ポータル」のベース

  * 1つの UI から複数 LLM（Gemini / GPT / ローカル）を使い分けたい
  * 利用ログ・モード・モデルを監査したい
* ガバナンスルールの A/B テスト

  * `policies.yaml` を書き換えて、どのルーティングが安定するか検証
* LLM ガバナンス / 安全性に関する PoC / 論文・ブログ用サンプル

---

## ロードマップ / TODO

* [ ] Angular ログビューア (`/logs` コンポーネント)
* [ ] ポリシービューア（`/policies` を UI で可視化）
* [ ] OpenAI / 他プロバイダを providers.py に正式対応
* [ ] PII / ドメイン分類を本格的なモデルに差し替え
* [ ] 部署・ユーザーごとの利用統計ダッシュボード
* [ ] Docker 化・クラウド環境へのデプロイ手順

---

## ライセンス / 注意事項

* 現時点では個人開発・実験用途を前提としたリポジトリです。
* 商用利用や社内展開を行う場合は、利用する LLM プロバイダ（Google, OpenAI, AWS 等）の
  利用規約・料金・データ取り扱いポリシーを必ず確認してください。
* `.env` や API キーは決して Git にコミットしないでください。
