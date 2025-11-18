# Multi-LLM Governance Kernel & Policy Compiler v0.1 – コード生成用 指示書

> このドキュメントは、コード生成モデル（例: "codex" / GPT の code モデル）にそのまま渡して、**Python + FastAPI バックエンド**と**Angular フロントエンド**を一式生成させるための指示書です。
>
> コード生成モデルに渡すときは、可能であれば **この全文をプロンプトとして入力** してください。

---

## 1. あなた（コードモデル）の役割

あなたは、Python 3.11・FastAPI・Angular 17・TypeScript に精通したフルスタックエンジニアです。
この指示書に従い、**Multi-LLM Governance Kernel & Policy Compiler v0.1** を実装します。

- バックエンド:
  - 言語: Python 3.11
  - フレームワーク: FastAPI
  - ORM/DB: SQLite（v0.1はシンプルな手書きSQLか SQLModel のどちらでもよい）
  - HTTPクライアント: httpx

- フロントエンド:
  - Angular 17
  - TypeScript
  - シンプルな SPA 構成

生成するコードは **ローカル環境で動作可能** であることを目標とします。

---

## 2. システム概要

### 2.1 目的

- 複数の LLM（OpenAI / Google / ローカルモデルなど）を、**単一のポリシー（YAML）** で一括制御する基盤を作る。
- モード判定（FAST / MEDIUM / HEAVY / FLASH）、PII ガード、セーフティ、モデル選択、ログ・監査を **バックエンドの "Governance Kernel"** に集約する。
- フロントエンドのチャット UI は Kernel に対して `/chat` API を呼ぶだけでよい構造にする。

### 2.2 ユースケース（v0.1）

- 社内ユーザーが Web からチャットで質問する。
- バックエンドは `policies.yaml` に基づいて:
  1. モード判定
  2. PII 検出（簡易）
  3. モードエスカレーション
  4. ルーティングルールに従うモデル選択
  5. Policy Compiler による system prompt 生成
  6. LLM API 呼び出し（v0.1では実装はダミー or OpenAI のみでOK）
  7. ログ保存
- フロントエンドは、チャット画面に
  - AI の応答
  - `mode` / `model` / `policy_version`
  を表示する。

---

## 3. Policy DSL (policies.yaml) v0.1

プロジェクトルートに `policies.yaml` を作成し、以下の内容を配置してください。

```yaml
version: "0.1"
policy_name: "COUNCIL_FOUR_GOV_KERNEL"
updated_at: "2025-11-17T00:00:00+09:00"

providers:
  openai:
    models:
      gpt5_1_thinking:
        role: "primary_heavy_reasoner"
        cost_tier: "high"
      gpt4_mini:
        role: "fast_light"
        cost_tier: "low"
  google:
    models:
      gemini_2_5_pro:
        role: "primary_heavy_reasoner"
        cost_tier: "high"
      gemini_2_5_flash:
        role: "fast_light"
        cost_tier: "low"
  local:
    models:
      local_safe_model:
        role: "fallback_sensitive"
        cost_tier: "local"

safety:
  precedence:
    - "legal_pii"
    - "injection_guard"
    - "safety"
    - "host_escalation"
    - "council_logic"
    - "persona"

  pii_shield:
    echo_pii_back: false
    direct_ids:
      mask_strategy: "full_mask"
      mask_token: "[REDACTED_DIRECT_ID]"
      examples:
        - "email"
        - "phone_number"
        - "credit_card"
    quasi_ids:
      mask_strategy: "head1_mask"
      visible_chars: 1
      mask_char: "*"
      examples:
        - "person_name"
        - "partial_address"
    code_names:
      mask_strategy: "category_replace"
      categories:
        project: "[PROJECT_NAME]"
        internal_code: "[INTERNAL_CODE]"
        secret_term: "[SENSITIVE_TERM]"

  blocked_categories:
    - "self_harm"
    - "violence"
    - "terrorism"
    - "child_exploitation"

modes:
  - id: "FAST"
    description: "一般的な質問・軽いタスク向け。Web検索は原則禁止。"
    safety_level: "normal"
    allow_web_search: false
    allow_code_execution: false
    default_models:
      - "openai:gpt4_mini"
      - "google:gemini_2_5_flash"
    triggers:
      fallback: true

  - id: "MEDIUM"
    description: "比較・設計・レビュー・仕様・計画・実験など、少し重い推論向け。"
    safety_level: "elevated"
    allow_web_search: false
    allow_code_execution: true
    default_models:
      - "openai:gpt5_1_thinking"
      - "google:gemini_2_5_pro"
    triggers:
      keywords_any:
        - "比較"
        - "設計"
        - "レビュー"
        - "仕様"
        - "計画"
        - "実験"

  - id: "HEAVY"
    description: "医療・法務・金融・安全・プライバシー・規制などの高リスク領域。"
    safety_level: "high"
    require_web_search_for_fresh: true
    allow_code_execution: true
    default_models:
      - "openai:gpt5_1_thinking"
      - "google:gemini_2_5_pro"
      - "local:local_safe_model"
    triggers:
      domains_any:
        - "medical"
        - "legal"
        - "finance"
        - "safety"
        - "privacy"
        - "regulation"
      keywords_any:
        - "個人情報"
        - "PII"
        - "規制"
        - "コンプライアンス"
        - "法改正"
        - "契約"
        - "SLO"
        - "脆弱性"

  - id: "FLASH"
    description: "ニュース・株価・天候など、24h以内の速報性が重要な要約専用モード。"
    safety_level: "strict"
    require_web_search: true
    response_style:
      skeleton: ["Decision", "Why"]
      disable_long_explanation: true
      disable_advice: true
    default_models:
      - "openai:gpt5_1_thinking"
      - "google:gemini_2_5_pro"
    triggers:
      domains_any:
        - "news"
        - "finance"
        - "weather"
      keywords_any:
        - "速報"
        - "最新ニュース"
        - "株価"
        - "今の天気"
      recency_hours_max: 24

escalation_rules:
  - name: "pii_always_heavy"
    if_flags:
      pii_detected: true
    escalate_to_min_mode: "HEAVY"

  - name: "user_forced_web_search"
    if_flags:
      user_requested_web_search: true
    min_mode: "HEAVY"

  - name: "ambiguity_score_raise"
    if_score_gte:
      ambiguity_score: 1
    step_up: 1

routing:
  rules:
    - name: "heavy_sensitive_domains"
      when_mode_in: ["HEAVY"]
      primary_model: "openai:gpt5_1_thinking"
      backup_models:
        - "google:gemini_2_5_pro"
        - "local:local_safe_model"

    - name: "flash_news"
      when_mode_in: ["FLASH"]
      primary_model: "openai:gpt5_1_thinking"
      require_web_search: true

    - name: "medium_default"
      when_mode_in: ["MEDIUM"]
      primary_model: "openai:gpt5_1_thinking"

    - name: "fast_default"
      when_mode_in: ["FAST"]
      primary_model: "google:gemini_2_5_flash"

logging:
  enabled: true
  fields:
    - "timestamp"
    - "user_id"
    - "mode"
    - "selected_model"
    - "policy_version"
    - "pii_mask_applied"
    - "safety_flags"
    - "tools_used"
    - "latency_ms"

experimental:
  triage_sigma:
    enabled: false
```

---

## 4. バックエンド設計（Python + FastAPI）

以下のファイル構成を想定して実装してください。

```text
backend/
  main.py
  policy_store.py
  governance_kernel.py
  policy_compiler.py
  providers.py
  logging_db.py
  models.py        # pydanticモデル
  requirements.txt
  policies.yaml    # 上記のDSL
```

### 4.1 requirements.txt

最低限、以下を含めてください（必要に応じて追加可）。

```text
fastapi
uvicorn[standard]
httpx
pydantic
pyyaml
sqlmodel
python-dotenv
```

### 4.2 policy_store.py

- 役割: `policies.yaml` を読み込み、Python の dict として提供する。
- 要件:
  - 関数 `load_policies(path: str) -> dict`
  - アプリ起動時に1回読み込めばよい（ホットリロードは v0.1 では不要）。
  - 読み込み失敗時は例外を投げ、起動時に気付けるようにする。

### 4.3 governance_kernel.py

- 役割: メインのガバナンスロジック。
- 実装する関数（最低限）:
  - `detect_domain(message: str) -> str`
    - v0.1 では単純なキーワードベースでよい。
    - 例: 「株」「株価」が含まれていたら `"finance"` など。
  - `detect_pii(message: str) -> dict`
    - メールアドレス・電話番号を正規表現で検出。
    - 戻り値例: `{ "pii_detected": bool, "detected_types": ["email", ...] }`
  - `decide_mode(message: str, policies: dict, domain: str, pii_flags: dict) -> str`
    - `modes` と `escalation_rules` を参照して `"FAST"|"MEDIUM"|"HEAVY"|"FLASH"` を返す。
    - ロジックはシンプルで構わない（厳密でなくてよい）。
  - `select_model(mode: str, policies: dict) -> str`
    - `routing.rules` から `primary_model` を返す。

### 4.4 policy_compiler.py

- 役割: mode / safety / PII 情報から、LLM に渡す system prompt を組み立てる。
- 関数:
  - `build_system_prompt(mode: str, policies: dict) -> str`
- 実装方針（例）:
  - 共通ベースメッセージ:
    - "You are an AI assistant governed by a central policy kernel."
    - "Follow the safety precedence: ..."
  - mode による差分:
    - HEAVY の場合: "Be extremely cautious, especially for medical/legal/finance queries."
    - FLASH の場合: "Focus on most recent facts and keep the answer short."

### 4.5 providers.py

- 役割: `provider:model` 形式の ID に応じて LLM を呼び出す。
- v0.1 では、実際の LLM 呼び出しは **ダミー実装** でも構いません。
  - 例: "モデル: openai:gpt5_1_thinking / モード: HEAVY" といった文字列を返す。
- 実際に OpenAI API を呼ぶ場合の雛形も入れてください（コメント付き）。

```python
# 擬似コードイメージ
async def call_llm(model_id: str, system_prompt: str, user_message: str) -> str:
    provider, name = model_id.split(":", 1)
    if provider == "openai":
        # TODO: OpenAI API 呼び出し実装
        return f"[DUMMY OPENAI:{name}] {user_message}"
    elif provider == "google":
        return f"[DUMMY GEMINI:{name}] {user_message}"
    else:
        return f"[DUMMY LOCAL:{name}] {user_message}"
```

### 4.6 logging_db.py

- 役割: SQLite にログを保存・取得する。
- 要件:
  - `logs` テーブルスキーマ:
    - id (int, PK, auto increment)
    - timestamp (datetime)
    - user_id (text)
    - mode (text)
    - model (text)
    - policy_version (text)
    - pii_mask_applied (boolean/int)
    - safety_flags (text; JSON文字列)
    - tools_used (text; JSON文字列)
    - latency_ms (int)
  - 関数:
    - `init_db()` : テーブルがなければ作成。
    - `insert_log(...)` : 1件挿入。
    - `get_recent_logs(limit: int) -> List[dict]` : 最新 N 件取得。

### 4.7 models.py (pydantic)

- リクエスト/レスポンス用のモデルを定義:

```python
from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    user_id: str
    message: str
    metadata: Optional[dict] = None

class ChatResponse(BaseModel):
    reply: str
    mode: str
    model: str
    policy_version: str
    safety_flags: List[str]
    tools_used: List[str]
    latency_ms: int

class LogRecord(BaseModel):
    id: int
    timestamp: str
    user_id: str
    mode: str
    model: str
    policy_version: str
    pii_mask_applied: bool
    safety_flags: List[str]
    tools_used: List[str]
    latency_ms: int
```

### 4.8 main.py (FastAPI アプリ本体)

- 起動時に:
  - `policies.yaml` を読み込む。
  - DB 初期化 (`init_db`) を呼ぶ。

- エンドポイント:

1. `POST /chat`
   - Request: `ChatRequest`
   - フロー:
     1. `detect_domain` / `detect_pii` / `decide_mode` / `select_model`
     2. `build_system_prompt`
     3. `call_llm`
     4. レイテンシ計測
     5. `insert_log`
   - Response: `ChatResponse`

2. `GET /policies`
   - 現在メモリにロードしている policies を JSON として返す。

3. `GET /logs?limit=50`
   - `get_recent_logs(limit)` を呼び出し、その結果を返す。

- `uvicorn main:app --reload` で起動可能にする。

---

## 5. フロントエンド設計（Angular 17）

### 5.1 プロジェクト構成（例）

```text
frontend/
  src/
    app/
      services/
        chat.service.ts
        policy.service.ts
        log.service.ts
      components/
        chat/
          chat.component.ts
          chat.component.html
          chat.component.css
        policy-viewer/
          policy-viewer.component.ts
          policy-viewer.component.html
        log-viewer/
          log-viewer.component.ts
          log-viewer.component.html
      app-routing.module.ts
      app.component.ts
      app.component.html
```

### 5.2 ChatService

- `POST /chat` を叩くサービス。

```ts
export interface ChatRequest {
  user_id: string;
  message: string;
  metadata?: any;
}

export interface ChatResponse {
  reply: string;
  mode: string;
  model: string;
  policy_version: string;
  safety_flags: string[];
  tools_used: string[];
  latency_ms: number;
}
```

- `sendMessage(req: ChatRequest): Observable<ChatResponse>` を実装。

### 5.3 ChatComponent

- ユーザーが AI と対話する画面。
- 機能:
  - 入力欄 + 送信ボタン
  - メッセージ履歴の表示
  - AI 側メッセージに `mode` / `model` / `latency_ms` をバッジ表示

### 5.4 PolicyViewerComponent

- `GET /policies` の結果を JSON 表示するだけの画面（v0.1は read-only でよい）。

### 5.5 LogViewerComponent

- `GET /logs?limit=50` を叩き、テーブルで表示。
- カラム例: timestamp, user_id, mode, model, latency_ms

### 5.6 ルーティング

- `app-routing.module.ts`:
  - `/chat` → ChatComponent
  - `/policies` → PolicyViewerComponent
  - `/logs` → LogViewerComponent

### 5.7 接続先 URL

- 開発中は、バックエンドを `http://localhost:8000` で起動する前提。
- 各サービスの baseUrl を `http://localhost:8000` に設定。

---

## 6. 動作確認手順（想定）

1. バックエンド:
   - `cd backend`
   - `pip install -r requirements.txt`
   - `uvicorn main:app --reload`

2. フロントエンド:
   - `cd frontend`
   - `npm install`
   - `ng serve`
   - ブラウザで `http://localhost:4200` を開く。

3. ブラウザ上で:
   - Chat 画面でメッセージを送信 → AIの返答と mode / model が表示される。
   - Policies 画面で `policies.yaml` の内容が JSON として見える。
   - Logs 画面で、最新のチャット履歴（メタ情報付き）が見える。

---

## 7. 実装ポリシー

- 型ヒント・docstring を適切に書くこと。
- 関数やクラスは、読みやすく小さく分割すること。
- v0.1 では LLM 呼び出しはダミーでも構わないが、実際の API 呼び出しに差し替えやすい構造にすること（provider / model の抽象化）。
- セキュリティ上の観点から、APIキーやシークレットは `.env` から読む形の雛形をコメントで示すこと。

---

## 8. 出力形式の指定（重要）

コード生成モデルとしてのあなたは、**以下の順番で出力**してください。

1. `backend/` 以下のファイル構成と、それぞれの Python コード全文。
2. `frontend/` 以下の主要ファイル構成と、TypeScript / HTML / CSS のコード全文。

ファイルごとに、`
```filename
...code...
```
の形式で示してもらえると助かります。

以上の指示に従って、Multi-LLM Governance Kernel & Policy Compiler v0.1 の実装コードを生成してください。

