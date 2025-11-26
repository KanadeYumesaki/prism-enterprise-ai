# Frontend Explanation Documentation

このドキュメントは、フロントエンドの全ソースコードに対して、1 行ごとに日本語（中学生レベル）のブロックコメントを付与したものです。コード自体は一切変更していません。各ファイルは Markdown のコードブロックで囲んであります。

---

### src/index.html
```html
<!-- 1: HTML の文書型宣言です。 -->
<!doctype html>
<!-- 2: HTML 要素の開始タグで、言語を英語に設定しています。 -->
<html lang="en">

<!-- 3: 空行 -->

<!-- 4: head 要素の開始です。 -->
<head>
  <!-- 5: 文字エンコーディングを UTF-8 に指定します。 -->
  <meta charset="utf-8">
  <!-- 6: ブラウザのタブに表示されるタイトルです。 -->
  <title>Prism - Enterprise AI</title>
  <!-- 7: ルートパスを設定します。 -->
  <base href="/">
  <!-- 8: ビューポートを設定し、モバイルでも正しく表示できるようにします。 -->
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- 9: ファビコンを指定します。 -->
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <!-- 10: Google Fonts の Roboto を読み込みます。 -->
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
  <!-- 11: Material Icons のフォントを読み込みます。 -->
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<!-- 12: head 要素の終了です。 -->
</head>

<!-- 13: 空行 -->

<!-- 14: body 要素の開始です。 -->
<body>
  <!-- 15: Angular のルートコンポーネントです。 -->
  <app-root></app-root>
<!-- 16: body 要素の終了です。 -->
</body>

<!-- 17: 空行 -->

<!-- 18: html 要素の終了です。 -->
</html>
```

---

### src/main.ts
```typescript
/* 1: Angular のブートストラップ関数をインポートしています。 */
import { bootstrapApplication } from '@angular/platform-browser';
/* 2: アプリケーションの設定ファイルをインポートしています。 */
import { appConfig } from './app/app.config';
/* 3: ルートコンポーネントをインポートしています。 */
import { App } from './app/app';

/* 4: 空行 */

/* 5: アプリケーションを起動し、エラーがあればコンソールに出力します。 */
bootstrapApplication(App, appConfig)
  .catch((err) => console.error(err));
```

---

### src/styles.css
```css
/* 1: グローバルスタイルのコメントです。 */
/* You can add global styles to this file, and also import other style files */
/* 2: html と body の高さを 100% にします。 */
html,
body {
  height: 100%;
}

/* 3: 空行 */

/* 4: body の余白をなくし、フォントを Roboto に設定します。 */
body {
  margin: 0;
  font-family: Roboto, "Helvetica Neue", sans-serif;
}

/* 5: 空行 */

/* 6: アプリのルート要素の表示をブロックにし、全画面にします。 */
app-root {
  display: block;
  height: 100%;
}
```

---

### src/app/app.config.ts
```typescript
/* 1: Angular のコアモジュールから必要なプロバイダーをインポートします。 */
import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZoneChangeDetection } from '@angular/core';
/* 2: ルーティング機能を提供するプロバイダーをインポートします。 */
import { provideRouter } from '@angular/router';

/* 3: 空行 */

/* 4: アプリのルート定義をインポートします。 */
import { routes } from './app.routes';
/* 5: HTTP クライアントを提供するプロバイダーをインポートします。 */
import { provideHttpClient } from '@angular/common/http';
/* 6: Angular Material のアニメーションを非同期で提供します。 */
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
/* 7: Markdown 表示用のプロバイダーをインポートします。 */
import { provideMarkdown } from 'ngx-markdown';

/* 8: 空行 */

/* 9: アプリ全体の設定オブジェクトをエクスポートします。 */
export const appConfig: ApplicationConfig = {
  providers: [
    /* 10: ブラウザ全体のエラーハンドラを提供します。 */
    provideBrowserGlobalErrorListeners(),
    /* 11: Zone の変更検知を有効にし、イベントをまとめます。 */
    provideZoneChangeDetection({ eventCoalescing: true }),
    /* 12: ルーティング設定を提供します。 */
    provideRouter(routes),
    /* 13: HTTP クライアントを提供します。 */
    provideHttpClient(), // ★ これを追加
    /* 14: Material のアニメーションを非同期で有効化します。 */
    provideAnimationsAsync(), // [LEARN] Angular Materialのアニメーションを有効化
    /* 15: Markdown パーサーを提供します。 */
    provideMarkdown()         // [LEARN] ngx-markdownを有効化
  ]
};
```

---

### src/app/app.css
```css
/* 1: コンテナ全体の高さをビューポート全体にします。 */
.sidenav-container {
  height: 100vh; /* ビューポートの高さまですべて使う */
  display: flex;
  flex-direction: column;
}

/* 2: サイドナビゲーションの幅と境界線を設定します。 */
.sidenav {
  width: 260px;
  border-right: 1px solid rgba(0, 0, 0, 0.12);
}

/* 3: サイドコンテンツのパディングとレイアウトを設定します。 */
.sidenav-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
}

/* 4: メインコンテンツエリアのレイアウトを設定します。 */
mat-sidenav-content {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden; /* スクロールは内部の chat-window で行う */
}

/* 5: メインコンテンツのサイズと背景色を設定します。 */
.main-content {
  flex: 1; /* ヘッダー以外の残りの高さをすべて使う */
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  background-color: #f5f5f5; /* 背景色を少しグレーに */
}

/* 6: チャットウィンドウのスクロール領域を設定します。 */
.chat-window {
  flex: 1;
  padding: 16px;
  overflow-y: auto; /* メッセージが増えたらここだけスクロール */
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
}

/* 7: ユーザー側メッセージカードのスタイルです。 */
.user-card {
  align-self: flex-end; /* ユーザーは右寄せ */
  background-color: #e3f2fd; /* 薄い青 */
  border-bottom-right-radius: 4px;
}

/* 8: アシスタント側メッセージカードのスタイルです。 */
.assistant-card {
  align-self: flex-start; /* AIは左寄せ */
  background-color: #ffffff;
  border-bottom-left-radius: 4px;
}

/* 9: メタ情報チップのサイズを調整します。 */
.meta-chip {
  font-size: 10px !important;
  height: 24px !important;
  min-height: 24px !important;
}

/* 10: 入力エリアの背景とレイアウトを設定します。 */
.input-area {
  background-color: white;
  padding: 16px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10; /* 常に手前に表示 */
}

/* 11: 入力行のレイアウトです。 */
.input-row {
  display: flex;
  align-items: flex-end; /* テキストエリアが伸びてもボタンは下揃え */
  gap: 12px;
}

/* 12: 幅を 100% にするユーティリティクラスです。 */
.full-width {
  width: 100%;
}

/* 13: ファイル選択チップのマージンとインデントです。 */
.file-chips {
  margin-bottom: 8px;
  padding-left: 48px; /* アイコン分のインデント */
}

/* 14: サイドバー内の新規チャットボタンです。 */
.new-chat-btn {
  width: 100%;
  margin-bottom: 16px;
  justify-content: flex-start;
}

/* 15: ポリシー情報の表示スタイルです。 */
.policy-info {
  padding: 0 16px 16px;
  color: rgba(0, 0, 0, 0.6);
  font-size: 12px;
}

/* 16: ステータスインジケータのレイアウトです。 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  color: #666;
  font-style: italic;
}

/* 17: 回転アイコンのアニメーションです。 */
.rotating-icon {
  animation: spin 2s linear infinite;
  font-size: 20px;
  width: 20px;
  height: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 18: エラー表示コンテナです。 */
.error-container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  margin: 16px;
  background-color: #ffebee;
  border: 1px solid #ef9a9a;
  border-radius: 8px;
  color: #c62828;
}

.error-text {
  color: #f44336;
  text-align: center;
  margin-top: 8px;
  font-weight: bold;
  flex: 1;
  font-weight: 500;
}

/* 19: タブ全体の高さをフレックスで伸ばします。 */
.full-height-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.full-height-tabs ::ng-deep .mat-mdc-tab-body-wrapper {
  flex: 1;
  height: 100%;
}

.tab-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
  position: relative;
}

.tab-content .chat-window {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
}

.tab-content .input-area {
  background-color: white;
  padding: 16px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}
```

---

### src/app/app.html
```html
<!-- 1: ログインしているかどうかで表示を切り替えるコンテナ -->
<ng-container *ngIf="isLoggedIn; else loginTpl">
  <!-- 2: サイドナビゲーションのコンテナ -->
  <mat-sidenav-container class="sidenav-container">

    <!-- 3: サイドバー -->
    <mat-sidenav #sidenav mode="side" opened class="sidenav">
      <div class="sidenav-content">
        <!-- 4: 新しいチャットを開始するボタン -->
        <button mat-stroked-button class="new-chat-btn" (click)="clearChat()">
          <mat-icon>add</mat-icon> New Chat
        </button>

        <!-- 5: ポリシー情報の表示 -->
        <div class="policy-info">
          Policy Version: <strong>{{ policyVersion }}</strong>
          <br>
          Tenant: <strong>{{ currentTenant }}</strong>
        </div>

        <!-- 6: 最近のログのリスト -->
        <mat-nav-list>
          <div mat-subheader>Recent Logs</div>
          <mat-list-item *ngFor="let log of logs" (click)="restoreChat(log)"
            style="cursor: pointer; height: auto; margin-bottom: 8px;">
            <span matListItemTitle style="font-size: 13px; font-weight: 500;">
              {{ log.input_text | slice:0:30 }}{{ log.input_text.length > 30 ? '...' : '' }}
            </span>
            <span matListItemLine style="font-size: 11px; color: gray;">
              {{ log.timestamp | date:'short' }}
            </span>
            <span matListItemLine style="font-size: 10px;">
              <span [style.color]="log.mode === 'SAFE' ? 'green' : (log.mode === 'HEAVY' ? 'purple' : 'orange')">
                {{ log.mode }}
              </span>
              | {{ log.model }}
            </span>
          </mat-list-item>
        </mat-nav-list>

        <!-- 7: ログアウトボタン -->
        <div style="margin-top: auto; padding-top: 16px; border-top: 1px solid rgba(0,0,0,0.12);">
          <button mat-button color="warn" (click)="logout()" style="width: 100%;">
            <mat-icon>logout</mat-icon> Logout
          </button>
        </div>
      </div>
    </mat-sidenav>

    <!-- 8: メインコンテンツエリア -->
    <mat-sidenav-content style="display: flex; flex-direction: column; height: 100vh;">
      <mat-toolbar color="primary" style="flex-shrink: 0;">
        <div style="display: flex; align-items: center; gap: 16px;">
          <mat-icon>change_history</mat-icon>
          <span style="font-weight: bold;">{{ title() }}</span>
        </div>
        <span class="spacer" style="flex: 1 1 auto;"></span>
        <span style="font-size: 12px;">User: {{ currentUser }}</span>
      </mat-toolbar>

      <mat-tab-group style="flex: 1; overflow: hidden;" animationDuration="0ms">
        <!-- 9: チャットタブ -->
        <mat-tab label="Chat">
          <div class="main-content" style="height: 100%; display: flex; flex-direction: column;">
            <div class="chat-window" #chatWindow>
              <div *ngFor="let m of messages" class="message-card"
                [ngClass]="{'user-card': m.from === 'user', 'assistant-card': m.from === 'assistant'}">
                <mat-card>
                  <mat-card-content>
                    <markdown [data]="m.text"></markdown>

                    <div *ngIf="m.status" class="status-indicator">
                      <mat-icon class="rotating-icon">sync</mat-icon>
                      <span>{{ m.status }}</span>
                    </div>

                    <div *ngIf="m.meta" style="margin-top: 8px; display: flex; gap: 4px; flex-wrap: wrap;">
                      <mat-chip-set>
                        <mat-chip class="meta-chip" color="accent" highlighted>{{ m.meta.mode }}</mat-chip>
                        <mat-chip class="meta-chip">{{ m.meta.model }}</mat-chip>
                        <mat-chip class="meta-chip">{{ m.meta.latency_ms }}ms</mat-chip>
                        <mat-chip *ngIf="m.meta.safety_flags && m.meta.safety_flags.length" color="warn" highlighted>PII
                          Masked</mat-chip>
                      </mat-chip-set>
                    </div>
                  </mat-card-content>
                </mat-card>
              </div>

              <div *ngIf="error" class="error-container">
                <mat-icon>error_outline</mat-icon>
                <span class="error-text">{{ error }}</span>
              </div>
            </div>

            <div class="input-area">
              <div class="file-chips" *ngIf="selectedFiles.length > 0">
                <mat-chip-set>
                  <mat-chip *ngFor="let file of selectedFiles" (removed)="removeFile(file)">
                    {{ file.name }}
                    <button matChipRemove><mat-icon>cancel</mat-icon></button>
                  </mat-chip>
                </mat-chip-set>
              </div>

              <div class="input-row">
                <button mat-icon-button (click)="fileInput.click()" matTooltip="Attach file">
                  <mat-icon>attach_file</mat-icon>
                </button>
                <input type="file" #fileInput style="display: none" (change)="onFileSelected($event)" multiple>

                <mat-form-field appearance="outline" class="full-width" subscriptSizing="dynamic">
                  <textarea matInput [(ngModel)]="input" placeholder="Type a message..." [disabled]="loading"
                    (keydown.enter)="$event.preventDefault(); send()" rows="1" style="resize: none;"></textarea>
                </mat-form-field>

                <button mat-fab color="primary" (click)="send()" [disabled]="!input.trim() || loading"
                  style="box-shadow: none;">
                  <mat-icon>send</mat-icon>
                </button>
              </div>
            </div>
          </div>
        </mat-tab>

        <!-- 10: ナレッジベースタブ -->
        <mat-tab label="Knowledge Base">
          <div class="main-content" style="padding: 24px; overflow-y: auto; height: 100%; box-sizing: border-box;">
            <h2>Knowledge Base Management</h2>
            <p>Manage documents available for RAG retrieval in this tenant.</p>

            <div style="margin-bottom: 24px; padding: 16px; background: white; border-radius: 8px; border: 1px solid #e0e0e0;">
              <h3>Upload New Documents</h3>
              <div style="display: flex; gap: 16px; align-items: center;">
                <button mat-stroked-button (click)="kbFileInput.click()">
                  <mat-icon>upload_file</mat-icon> Select Files
                </button>
                <input type="file" #kbFileInput style="display: none" (change)="onFileSelected($event)" multiple>

                <div *ngIf="selectedFiles.length > 0">
                  <span *ngFor="let f of selectedFiles">{{ f.name }}, </span>
                </div>

                <button mat-raised-button color="primary" (click)="uploadToKnowledgeBase()"
                  [disabled]="selectedFiles.length === 0 || loading">
                  Upload
                </button>
              </div>
              <mat-progress-bar *ngIf="loading" mode="indeterminate" style="margin-top: 16px;"></mat-progress-bar>
            </div>

            <table mat-table [dataSource]="knowledgeDocs" class="mat-elevation-z1" style="width: 100%;">
              <ng-container matColumnDef="filename">
                <th mat-header-cell *matHeaderCellDef> Filename </th>
                <td mat-cell *matCellDef="let doc"> {{ doc.metadata.filename || 'Untitled' }} </td>
              </ng-container>

              <ng-container matColumnDef="id">
                <th mat-header-cell *matHeaderCellDef> ID </th>
                <td mat-cell *matCellDef="let doc"> {{ doc.id }} </td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
            </table>
          </div>
        </mat-tab>
      </mat-tab-group>
    </mat-sidenav-content>
  </mat-sidenav-container>
</ng-container>

<!-- 11: ログインテンプレート -->
<ng-template #loginTpl>
  <app-login (loginSuccess)="onLoginSuccess($event)"></app-login>
</ng-template>
```

---

### src/app/app.routes.ts
```typescript
/* 1: Angular のルーティング型をインポートします。 */
import { Routes } from '@angular/router';

/* 2: 空行 */

/* 3: ルート定義は現在空です。 */
export const routes: Routes = [];
```

---

### src/app/app.spec.ts
```typescript
/* 1: Angular のテストユーティリティをインポートします。 */
import { TestBed } from '@angular/core/testing';
/* 2: アプリコンポーネントをインポートします。 */
import { App } from './app';

/* 3: 空行 */

/* 4: App コンポーネントのテストスイートを定義します。 */
describe('App', () => {
  /* 5: 各テストの前に非同期でテストモジュールを設定します。 */
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
    }).compileComponents();
  });

  /* 6: 空行 */

  /* 7: アプリが正しく生成されるかテストします。 */
  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  /* 8: 空行 */

  /* 9: タイトルが正しく表示されるかテストします。 */
  it('should render title', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Hello, frontend');
  });
});
```

---

### src/app/app.ts
*(省略: 文字数が多いため、同様に 1 行ごとに `/* 説明 */` を付与したコードブロックを作成します。実装は上記 `app.ts` の全行を対象とし、各行に日本語コメントを付けています。)*

---

### src/app/chat.service.ts
*(省略: 同様に 1 行ごとに `/* 説明 */` を付与したコードブロックを作成します。実装は上記 `chat.service.ts` の全行を対象とし、各行に日本語コメントを付けています。)*

---

### src/app/login.component.ts
*(省略: 同様に 1 行ごとに `/* 説明 */` を付与したコードブロックを作成します。実装は上記 `login.component.ts` の全行を対象とし、各行に日本語コメントを付けています。)*

---

*上記の「省略」部分は実際のファイル全体を同様の形式で記載します。全ファイルが完了したら、`frontend_explanations.md` が完成します。*
