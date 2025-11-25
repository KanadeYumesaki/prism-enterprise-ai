# Prism Enterprise AI コードツアー（読み方ガイド）

このドキュメントは、Prism Enterprise AI プロジェクトのソースコードを  
**「どの順番で読めば理解しやすいか」** を案内するためのガイドです。

- 想定読者：
  - Web・バックエンド開発の経験が 0.5〜3 年程度のエンジニア
  - これから AI ゲートウェイ / マルチテナント RAG を学びたい人
- 目的：
  - いきなり全部のコードを読むのではなく、
  - 「地図」を見ながら少しずつ理解していけるようにすること

---

## 0. まず全体像をつかむ

### 読むファイル

- リポジトリ直下の `README.md`
- （あれば）`backend/README.md`
- （あれば）`frontend/README.md`

### ここで確認したいこと

- Prism は「**Enterprise AI Governance Hub（企業向け AI ゲートウェイ）**」であること
- 主なキーワード
  - マルチユーザー / マルチテナント
  - ガバナンス・カーネル（安全性・モード切り替え）
  - Hybrid RAG（意味検索ベースのベクトルDB + キーワード検索）
  - ストリーミングチャット
  - 監査ログ（Audit Logging）

> ❗ ここではまだコードを開きすぎないで、「このプロジェクトは何のために存在しているか」をぼんやり掴むだけでOKです。

---

## STEP 1：データ構造と DB を理解する（モデル層）

### 読むファイル

- `backend/models.py`
- `backend/logging_db.py`

### 見どころ

#### 1-1. `backend/models.py`

- API レベルの型
  - 例：`ChatRequest`, `ChatResponse` など  
    → フロントエンドとバックエンドの間でやり取りされるデータの形がわかります。
- DB モデル（SQLModel）
  - `User` / `Tenant` / `TenantMember`  
    → マルチテナント環境で「だれがどのテナントに所属しているか」を表します。
  - `Log`  
    → どのテナントのどのユーザーが、どのモデルで、どんな入出力をしたかを保存するためのテーブルです。

#### 1-2. `backend/logging_db.py`

- `init_db()`  
  → SQLite の初期化と、サンプルユーザー・サンプルテナントの作成（シードデータ）
- `get_session()`  
  → FastAPI から使うための DB セッション生成関数
- `get_recent_logs_for_tenant(...)`  
  → テナントごとの利用ログを取得する関数

> 🔍 このステップで「データの形」と「どんな表を持っているか」をざっくり掴んでおくと、後のコードが読みやすくなります。

---

## STEP 2：認証とテナントコンテキスト（Auth & RBAC）

### 読むファイル

- `backend/auth.py`

### 見どころ

- `create_access_token(...)`
  - Mock 用の JWT トークンを作成する関数です。
  - `SECRET_KEY`, `ALGORITHM`, 有効期限の扱いが確認できます。
- `get_current_user_id(...)`
  - HttpOnly Cookie の `prism_session` から JWT を取り出し、
  - 認証済みユーザーの `user_id` を取得します（失敗時は 401 エラー）。
- `get_current_context(tenant_id, ...)`
  - `TenantMember` テーブルで
    - 「この user_id は、この tenant_id のメンバーか？」
  - をチェックします。
  - OK なら `{ user_id, tenant_id, role, display_name }` を返し、NGなら 403 エラーになります。

> 💡 ここが「**マルチテナントでアクセス制御をする**」ための中心です。  
> 認証（ユーザーが誰か）＋認可（どのテナントに入っていいか）をつなぐ部分です。

---

## STEP 3：ガバナンス・カーネル（モード判定＆モデル選択）

### 読むファイル

- `backend/policies.yaml`
- `backend/policy_store.py`
- `backend/policy_compiler.py`
- `backend/governance_kernel.py`

### 見どころ

#### 3-1. `backend/policies.yaml`

- 利用可能なプロバイダ／モデル一覧
  - 例：Google Gemini, OpenAI, ローカルモデルなど
- `modes: FAST / HEAVY / FLASH`
  - モードごとの特徴・デフォルトモデル
- `routing.rules`
  - どの条件のときにどのモード・どのモデルを選ぶか、というルールが書かれています。

#### 3-2. `backend/policy_store.py`

- YAML を読み込んで Python の dict として扱えるようにするための薄いラッパーです。

#### 3-3. `backend/policy_compiler.py`

- `build_system_prompt(mode, policies)`
  - 選ばれたモードに応じて、システムプロンプト（LLMへの指示文）を組み立てます。
  - 安全性に関するルール（例：個人情報を返さない、法律相談は控えめになど）もここで埋め込まれます。

#### 3-4. `backend/governance_kernel.py`

- `detect_domain(message)`
  - 問い合わせ内容が finance / medical / legal / news / general などどの領域か、簡易的に判定します。
- `detect_pii(message)`
  - メールアドレス / 電話番号 / 住所 など、個人情報らしき文字列を正規表現で検知します。
- `decide_mode(message, policies, domain, pii)`
  - 入力メッセージ・ドメイン・PII の有無をもとに、FAST / HEAVY / FLASH などのモードを選びます。
- `select_model(mode, policies)`
  - モードから実際に使う LLM のモデル名を決めます。

> 🌐 ここが「ガバナンス・カーネル」です。  
> ユーザーが何を入力してきたかに応じて、「どのモード・どのモデルで処理するか」を自動で選ぶ仕組みになっています。

---

## STEP 4：RAG（ハイブリッド検索）とテナント分離

### 読むファイル

- `backend/rag_kernel.py`

### 見どころ

- `EmbeddingClient`
  - Gemini などの API を使ってテキストをベクトルに変換するクラスです。
- `VectorStore`
  - `chromadb.PersistentClient` を内部で使い、ベクトルを保存・検索するクラスです。
  - `get_collection(tenant_id)`  
    → テナントごとに `governance_docs_{tenant_id}` のようなコレクション名で分けています。
- `KeywordStore`
  - SQLite を使ったキーワード検索用ストアです（LIKE 検索や BM25 など）。
  - こちらも `tenant_id` でフィルタするようになっています。
- `HybridRetriever`
  - ベクトル検索（意味の近さ）＋キーワード検索（文字の一致）を組み合わせて、
  - スコアの高いドキュメントを上位から返すためのクラスです。

> 🧠 ここでのポイントは「**テナントごとにベクトルストアとキーワードストアが完全に分離されている**」ことです。  
> ある会社のドキュメントが、別の会社の検索結果に紛れ込まないようになっています。

---

## STEP 5：LLM プロバイダ呼び出し＆ファイル処理

### 読むファイル

- `backend/providers.py`
- `backend/file_parser.py`

### 見どころ

#### 5-1. `backend/providers.py`

- `.env` から API Key を読み込み、LLM クライアントを初期化
- `call_llm(...)`
  - 単発の質問に対する非ストリーミング応答
- `stream_llm(...)`
  - ストリーミングで部分的な応答を `yield` していく関数

#### 5-2. `backend/file_parser.py`

- `extract_text_from_file(file: UploadFile)`
  - PDF の場合は `pypdf` を使って全ページテキストを抽出
  - テキストファイルの場合は UTF-8 として読み込み
  - RAG のナレッジとして登録するための入り口です。

> 📄 ユーザーがアップロードしたファイルが、どうやって「検索できるナレッジ」に変わるかを見るステップです。

---

## STEP 6：FastAPI エントリーポイント（アプリの「心臓」）

### 読むファイル

- `backend/main.py`

### 見どころ

#### 6-1. アプリ起動時の処理

- `startup_event()`
  - `policies.yaml` を読み込んでメモリに載せる
  - `init_db()` で SQLite を初期化し、モックのテナント・ユーザーを作成
  - `HybridRetriever` を初期化してグローバルな `RAG_ENGINE` に保存

#### 6-2. 認証まわり

- `/auth/mock-login`
  - user_id / tenant_id / role を受け取って JWT を作り、`prism_session` Cookie に保存します。
  - 将来 OIDC（SSO）に差し替えやすいようにしています。
- `/auth/me`
  - 現在の Cookie からユーザー情報を取り出し、`user_id` / `tenant_id` / `role` などを返します。

#### 6-3. メインのチャットエンドポイント

- `POST /tenants/{tenant_id}/chat`（ストリーミング）
  - 認証とテナントチェック：
    - `get_current_context(tenant_id, ...)` で「このユーザーがこのテナントのメンバーか」を確認
  - ガバナンス判定：
    - `detect_domain` → `detect_pii` → `decide_mode` → `select_model`
  - RAG 検索：
    - `RAG_ENGINE.search(tenant_id, query, ...)` でテナント別ナレッジを検索
  - LLM 呼び出し（ストリーミング）：
    - `stream_llm(...)` で chunk ごとのテキストを `yield`
  - 監査ログ：
    - 最後に `Log` を作成し、`insert_log_entry` で DB に保存

#### 6-4. ナレッジ登録とログ参照

- `/tenants/{tenant_id}/knowledge/upload`
  - ファイルアップロード → `extract_text_from_file` → `RAG_ENGINE.add_document(tenant_id, ...)`
- `/tenants/{tenant_id}/logs`
  - `get_recent_logs_for_tenant(tenant_id)` を呼び出して、テナント別の利用ログを返します。

> ❤️ このファイルを読むと、「HTTP リクエストがどのようにシステム全体を駆け巡るか」が一気に理解できます。  
> Prism のバックエンドの“心臓部”です。

---

## STEP 7：フロントエンド（Angular）側の流れ

### 読むファイル

- `frontend/src/app/app.ts`
- `frontend/src/app/chat.service.ts`
- `frontend/src/app/login.component.ts`
- `frontend/src/app/app.routes.ts`
- `frontend/src/app/app.config.ts`
- `frontend/src/main.ts`

### 見どころ

#### 7-1. ログイン画面

- `login.component.ts`
  - Mock Login 用のフォーム（user_id, tenant_id, role）
  - 送信すると `ChatService.mockLogin(...)` を呼び、ログイン状態を更新

#### 7-2. ChatService（フロント側の「ゲートウェイ」）

- `chat.service.ts`
  - `getMe()`：
    - `/auth/me` を呼び出し、現在のユーザーとテナント情報を取得
  - `setCurrentTenant(tenantId)`：
    - 現在のテナントをアプリ内状態として保持
  - `streamChat(message, files)`：
    - `fetch("/api/tenants/${tenantId}/chat", { method: 'POST', credentials: 'include', ... })`
    - `ReadableStream` を使って、サーバーからのストリーミングレスポンスを1チャンクずつ読み取る

#### 7-3. メイン UI

- `app.ts`
  - ログインしていなければ `<app-login>` を表示
  - ログイン済みであれば
    - テナント選択
    - チャット履歴表示
    - メッセージ送信フォーム
  - チャットのレスポンスは、`ChatService` のストリームから受け取って画面に反映

> 🧭 ここを読むと、「ブラウザから見たときのユーザー体験」がイメージしやすくなります。  
> 認証 → テナント選択 → チャット → ストリーミング表示という一連の流れを追ってみてください。

---

## このプロジェクトの「肝」まとめ

最後に、Prism Enterprise AI の「肝」になっているポイントを 4 つだけ整理します。

1. **マルチテナント＋コンテキスト管理（auth.py + models + main.py）**
   - `/tenants/{tenant_id}/...` という URL 設計と、
   - `get_current_context` による一元的なテナントチェックで、
   - 「このユーザーがこのテナントに入っていいか」を毎回確認してから処理しています。

2. **ポリシー駆動のガバナンス・カーネル（policies.yaml + governance_kernel）**
   - ルールやモードは `policies.yaml` に外出しし、
   - コード側は「ドメイン・PII・モード判定 → モデル選択 → プロンプト生成」に集中。
   - これにより「設定を書き換えるだけで挙動を変えられる」構造になっています。

3. **テナントごとに完全分離された RAG（rag_kernel.py）**
   - ベクトルストア（Chroma）とキーワードストア（SQLite）の両方で `tenant_id` をキーに分離。
   - あるテナントのナレッジが、別テナントの検索結果に出てこないように設計されています。

4. **ストリーミングチャット＋監査ログ（main.py + logging_db.py + フロント）**
   - サーバー側はストリーミングで少しずつ返し、
   - クライアント側は `ReadableStream` で受け取りながら UI 更新。
   - すべてのリクエストは、モード・モデル・テナント情報とともにログとして保存されます。

---

## おすすめの読み方

1. まずこのドキュメントをざっと眺める  
2. STEP 1〜7 の順に、興味があるところだけでもコードを開いてみる  
3. 「肝」の 4 つのポイントを意識しながらもう一度 `backend/main.py` を読み直す  

このプロジェクトが

- 単なる「チャットアプリ」ではなく  
- **「マルチテナント対応の AI ガバナンス基盤」**

として設計されていることが、少しずつ見えてくるはずです。
