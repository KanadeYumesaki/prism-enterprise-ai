// src/app/app.ts
import { Component, signal, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatResponse } from './chat.service';

interface ChatMessage {
  from: 'user' | 'assistant';
  text: string;
  meta?: Partial<ChatResponse>;
}

import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatTableModule } from '@angular/material/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MarkdownComponent } from 'ngx-markdown';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    // [LEARN] Material Designのコンポーネントを利用可能にします
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatCardModule,
    MatChipsModule,
    MatTableModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    MatTooltipModule,
    MarkdownComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  @ViewChild('chatWindow') private chatWindow!: ElementRef;
  protected readonly title = signal('Prism');

  input = '';
  loading = false;
  error: string | null = null;
  messages: ChatMessage[] = [];
  selectedFiles: File[] = [];
  viewMode: 'chat' | 'knowledge' = 'chat';
  knowledgeDocs: any[] = [];
  displayedColumns: string[] = ['filename', 'id'];

  removeFile(fileToRemove: File): void {
    this.selectedFiles = this.selectedFiles.filter(file => file !== fileToRemove);
  }

  // サイドバー用データ
  logs: any[] = [];
  policyVersion = 'Loading...';

  constructor(private chat: ChatService) { }

  ngOnInit() {
    this.fetchSidebarData();
  }

  fetchSidebarData() {
    // ログ取得
    this.chat.getLogs().subscribe({
      next: (data) => {
        this.logs = data;
      },
      error: (e) => console.error('Failed to fetch logs', e)
    });

    // ポリシー取得
    this.chat.getPolicies().subscribe({
      next: (data) => {
        this.policyVersion = data.version || 'Unknown';
      },
      error: (e) => console.error('Failed to fetch policies', e)
    });
  }

  // 新規チャット（画面クリア）
  clearChat() {
    this.messages = [];
    this.error = null;
    this.input = '';
    this.input = '';
    this.selectedFiles = [];
  }

  // [LEARN] ファイル選択時のイベントハンドラ
  // HTMLの <input type="file" multiple (change)="onFileSelected($event)"> から呼ばれます。
  onFileSelected(event: Event): void {
    const element = event.currentTarget as HTMLInputElement;
    const fileList: FileList | null = element.files;
    if (fileList && fileList.length > 0) {
      const newFiles = Array.from(fileList);

      // 重複排除と上限チェック
      newFiles.forEach(file => {
        if (this.selectedFiles.length >= 10) return;
        if (!this.selectedFiles.some(f => f.name === file.name)) {
          this.selectedFiles.push(file);
        }
      });
    }
    // [IMPORTANT] 同じファイルを再選択できるように値をクリア
    element.value = '';
  }

  setViewMode(mode: 'chat' | 'knowledge') {
    this.viewMode = mode;
    if (mode === 'knowledge') {
      this.fetchKnowledgeBase();
    }
  }

  fetchKnowledgeBase() {
    this.chat.getKnowledgeList().subscribe({
      next: (data) => {
        this.knowledgeDocs = data;
      },
      error: (e) => console.error('Failed to fetch knowledge base', e)
    });
  }

  uploadToKnowledgeBase() {
    if (this.selectedFiles.length === 0) return;

    this.loading = true;
    let completed = 0;
    const total = this.selectedFiles.length;

    this.selectedFiles.forEach(file => {
      this.chat.ingestFile(file).subscribe({
        next: () => {
          completed++;
          if (completed === total) {
            this.loading = false;
            this.selectedFiles = [];
            this.fetchKnowledgeBase();
            alert('All files uploaded successfully!');
          }
        },
        error: (e) => {
          console.error(e);
          completed++;
          if (completed === total) {
            this.loading = false;
            this.fetchKnowledgeBase(); // Refresh anyway
          }
        }
      });
    });
  }

  send(): void {
    const content = this.input.trim();
    if (!content || this.loading) return;

    // 自分の発話を追加
    this.messages = [...this.messages, { from: 'user', text: content }];

    // Assistantのプレースホルダーを追加
    const assistantMsg: ChatMessage = { from: 'assistant', text: '' };
    this.messages = [...this.messages, assistantMsg];

    this.input = '';
    this.error = null;
    this.loading = true;
    this.scrollToBottom();

    this.chat.sendMessageStream(content, 'frontend-user', this.selectedFiles).subscribe({
      next: (data) => {
        if (data.type === 'status') {
          // ステータス表示（検索中...など）
          // まだ回答が始まっていないので、テキストを上書きして表示
          assistantMsg.text = `<i style="color:gray">${data.content}</i>`;
          this.scrollToBottom();
        } else if (data.type === 'chunk') {
          // 最初のチャンクが来たら、ステータス表示を消して回答追記モードへ
          if (assistantMsg.text.startsWith('<i style="color:gray">')) {
            assistantMsg.text = '';
          }
          assistantMsg.text += data.content;
          this.scrollToBottom();
        } else if (data.type === 'complete') {
          // 完了時のメタデータ更新
          assistantMsg.meta = data.meta;
          this.loading = false;
          this.selectedFiles = [];
          this.fetchSidebarData();
          this.scrollToBottom();
        }
      },
      error: (err: unknown) => {
        console.error(err);
        this.error =
          'バックエンドとの通信に失敗しました。FastAPI 側のターミナルのエラーも確認してみてください。';
        this.loading = false;
      }
    });
  }

  // [LEARN] 履歴復元（データバインディング）
  // サイドバーのログをクリックしたときに呼び出されます。
  // 過去の会話データを messages 配列にセットすることで、Angularのデータバインディング機能により
  // 自動的に画面上の表示が更新されます。これが「データ駆動」のUI構築です。
  restoreChat(log: any) {
    // 既存のメッセージをクリアして、ログの内容で上書き
    // 必要に応じて [...this.messages, ...] のように追記することも可能です
    this.messages = [
      { from: 'user', text: log.input_text },
      {
        from: 'assistant',
        text: log.output_text,
        meta: {
          mode: log.mode,
          model: log.model,
          policy_version: log.policy_version,
          safety_flags: log.safety_flags,
          tools_used: log.tools_used,
          latency_ms: log.latency_ms
        }
      }
    ];
    setTimeout(() => this.scrollToBottom(), 100);
  }

  scrollToBottom(): void {
    setTimeout(() => {
      try {
        this.chatWindow.nativeElement.scrollTop = this.chatWindow.nativeElement.scrollHeight;
      } catch (err) { }
    }, 0);
  }
}
