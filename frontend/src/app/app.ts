import { Component, signal, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatResponse } from './chat.service';

interface ChatMessage {
  from: 'user' | 'assistant';
  text: string;
  status?: string; // [NEW] ステータス表示用 (Thinking, Searching...)
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
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar'; // [NEW]
import { MarkdownComponent } from 'ngx-markdown';

import { LoginComponent } from './login.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatTableModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatSnackBarModule,
    MarkdownComponent,
    LoginComponent // [NEW]
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  @ViewChild('chatWindow') private chatWindow!: ElementRef;
  protected readonly title = signal('Prism');

  // [NEW] Login State
  isLoggedIn = false;
  currentUser = '';
  currentTenant = '';

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

  logs: any[] = [];
  policyVersion = 'Loading...';

  constructor(private chat: ChatService, private snackBar: MatSnackBar) { }

  ngOnInit() {
    // [REFAC] Wait for login
  }

  // [NEW] Login Handler
  onLoginSuccess(event: { userId: string, tenantId: string }) {
    this.isLoggedIn = true;
    this.currentUser = event.userId;
    this.currentTenant = event.tenantId;
    this.fetchSidebarData();
  }

  // [NEW] Logout
  logout() {
    this.chat.logout().subscribe(() => {
      this.isLoggedIn = false;
      this.currentUser = '';
      this.currentTenant = '';
      this.messages = [];
      this.logs = [];
      this.chat.setTenantId('');
    });
  }

  fetchSidebarData() {
    this.chat.getLogs().subscribe({
      next: (data) => {
        this.logs = data;
      },
      error: (e) => console.error('Failed to fetch logs', e)
    });

    this.chat.getPolicies().subscribe({
      next: (data) => {
        this.policyVersion = data.version || 'Unknown';
      },
      error: (e) => console.error('Failed to fetch policies', e)
    });
  }

  clearChat() {
    this.messages = [];
    this.error = null;
    this.input = '';
    this.selectedFiles = [];
  }

  // [NEW] ファイルバリデーション
  validateFile(file: File): boolean {
    const MAX_SIZE = 10 * 1024 * 1024; // 10MB
    const ALLOWED_EXTENSIONS = ['.txt', '.pdf', '.csv', '.md', '.json', '.py', '.js', '.ts', '.html', '.css'];

    if (file.size > MAX_SIZE) {
      this.showError(`File ${file.name} is too large. Max size is 10MB.`);
      return false;
    }

    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    // 拡張子チェック（必要に応じて緩和）
    // if (!ALLOWED_EXTENSIONS.includes(ext)) {
    //   this.showError(`File type ${ext} is not supported.`);
    //   return false;
    // }
    return true;
  }

  showError(message: string) {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
    this.error = message;
  }

  showSuccess(message: string) {
    this.snackBar.open(message, 'OK', {
      duration: 3000,
      panelClass: ['success-snackbar']
    });
  }

  onFileSelected(event: Event): void {
    const element = event.currentTarget as HTMLInputElement;
    const fileList: FileList | null = element.files;
    if (fileList && fileList.length > 0) {
      const newFiles = Array.from(fileList);

      newFiles.forEach(file => {
        if (this.selectedFiles.length >= 10) {
          this.showError('Max 10 files allowed.');
          return;
        }
        if (!this.validateFile(file)) return; // [NEW] Validation

        if (!this.selectedFiles.some(f => f.name === file.name)) {
          this.selectedFiles.push(file);
        }
      });
    }
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
      error: (e) => this.showError('Failed to fetch knowledge base')
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
            this.showSuccess('All files uploaded successfully!');
          }
        },
        error: (e) => {
          console.error(e);
          completed++;
          this.showError(`Failed to upload ${file.name}`);
          if (completed === total) {
            this.loading = false;
            this.fetchKnowledgeBase();
          }
        }
      });
    });
  }

  send(): void {
    const content = this.input.trim();
    if (!content || this.loading) return;

    this.messages = [...this.messages, { from: 'user', text: content }];

    const assistantMsg: ChatMessage = { from: 'assistant', text: '', status: 'Thinking...' }; // [NEW] Initial status
    this.messages = [...this.messages, assistantMsg];

    this.input = '';
    this.error = null;
    this.loading = true;
    this.scrollToBottom();

    this.chat.sendMessageStream(content, 'frontend-user', this.selectedFiles).subscribe({
      next: (data) => {
        if (data.type === 'status') {
          // [NEW] ステータス更新
          assistantMsg.status = data.content;
          this.scrollToBottom();
        } else if (data.type === 'chunk') {
          // [NEW] 回答開始でステータス消去
          assistantMsg.status = undefined;
          assistantMsg.text += data.content;
          this.scrollToBottom();
        } else if (data.type === 'complete') {
          assistantMsg.meta = data.meta;
          this.loading = false;
          this.selectedFiles = [];
          this.fetchSidebarData();
          this.scrollToBottom();
        }
      },
      error: (err: Error) => {
        console.error(err);
        this.showError(err.message || 'Communication failed');
        this.loading = false;
        // エラー時はステータスを消してエラー表示
        assistantMsg.status = undefined;
        assistantMsg.text += '\n\n**Error:** ' + (err.message || 'Communication failed');
      }
    });
  }

  restoreChat(log: any) {
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
