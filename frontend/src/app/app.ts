// src/app/app.ts
import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatResponse } from './chat.service';

interface ChatMessage {
  from: 'user' | 'assistant';
  text: string;
  meta?: Partial<ChatResponse>;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly title = signal('Governance Kernel Frontend');

  input = '';
  loading = false;
  error: string | null = null;
  messages: ChatMessage[] = [];

  constructor(private chat: ChatService) {}

  send(): void {
    const content = this.input.trim();
    if (!content || this.loading) return;

    // 自分の発話を追加
    this.messages = [...this.messages, { from: 'user', text: content }];

    this.input = '';
    this.error = null;
    this.loading = true;

    this.chat.sendMessage(content).subscribe({
      next: (res: ChatResponse) => {
        this.messages = [
          ...this.messages,
          { from: 'assistant', text: res.reply, meta: res },
        ];
        this.loading = false;
      },
      error: (err: unknown) => {
        console.error(err);
        this.error =
          'バックエンドとの通信に失敗しました。FastAPI 側のターミナルのエラーも確認してみてください。';
        this.loading = false;
      },
    });
  }
}
