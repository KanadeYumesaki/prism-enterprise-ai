// src/app/chat.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { retry, timeout, catchError } from 'rxjs/operators';

export interface ChatRequest {
  message: string;
  user_id: string;
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

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  // FastAPI を 8000 番ポートで動かしている前提
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) { }

  sendMessage(message: string, userId = 'frontend-user', files: File[] = []): Observable<ChatResponse> {
    /* [OLD] JSON送信
       以前は単純なオブジェクトをJSONとして送っていました。
       const body: ChatRequest = { message, user_id: userId };
       return this.http.post<ChatResponse>(`${this.baseUrl}/chat`, body);
    */

    // [LEARN] ここでFormDataを使う理由は、テキストとバイナリファイル(画像やPDFなど)を
    // 一度のHTTPリクエストでまとめて送信するためです。
    // JSONはテキストデータの構造化には向いていますが、バイナリデータの扱いは苦手です。
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('message', message);

    // [LEARN] 配列操作（複数ファイル）
    // 複数のファイルを送信する場合、同じキー名（'files'）で何度も append します。
    // バックエンド側（FastAPIなど）はこれをリストとして受け取ることができます。
    if (files && files.length > 0) {
      files.forEach(file => {
        formData.append('files', file);
      });
    }

    // [LEARN] HttpClient は FormData を渡すと、自動的に
    // 'Content-Type': 'multipart/form-data; boundary=...'
    // というヘッダーを設定してくれます。自分でヘッダーを設定する必要はありません。
    // 'Content-Type': 'multipart/form-data; boundary=...'
    // というヘッダーを設定してくれます。自分でヘッダーを設定する必要はありません。
    return this.http.post<ChatResponse>(`${this.baseUrl}/chat`, formData);
  }

  // [NEW CODE] ストリーミング対応 (Refactored for Production)
  sendMessageStream(message: string, userId = 'frontend-user', files: File[] = []): Observable<any> {
    return new Observable<any>(observer => {
      const controller = new AbortController();
      const signal = controller.signal;

      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('message', message);
      if (files && files.length > 0) {
        files.forEach(file => formData.append('files', file));
      }

      fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        body: formData,
        signal
      }).then(async response => {
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Server Error (${response.status}): ${errorText || response.statusText}`);
        }
        if (!response.body) {
          throw new Error('No response body received from server.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.trim()) {
                try {
                  const data = JSON.parse(line);
                  observer.next(data);
                } catch (e) {
                  console.warn('Stream Parse Warning:', e, line);
                }
              }
            }
          }
          // Process remaining buffer
          if (buffer.trim()) {
            try {
              const data = JSON.parse(buffer);
              observer.next(data);
            } catch (e) { console.warn('Final Stream Parse Warning:', e, buffer); }
          }
          observer.complete();
        } catch (err) {
          observer.error(err);
        }
      }).catch(err => {
        if (err.name === 'AbortError') {
          observer.complete(); // Cancelled by user
        } else {
          observer.error(err);
        }
      });

      return () => controller.abort();
    }).pipe(
      // ネットワークエラーなどで即死した場合のリトライ
      retry({ count: 2, delay: 1000 }),
      // 30秒間何もレスポンスがない場合はタイムアウト
      timeout(30000),
      catchError(err => {
        // ユーザー向けのエラーメッセージに変換
        let userMessage = 'An unexpected error occurred.';
        if (err.name === 'TimeoutError') {
          userMessage = 'Connection timed out. The server is taking too long to respond.';
        } else if (err.message && err.message.includes('Server Error')) {
          userMessage = err.message;
        } else if (err.status === 0) {
          userMessage = 'Network error. Please check your connection.';
        } else {
          userMessage = `Error: ${err.message || 'Unknown error'}`;
        }
        return throwError(() => new Error(userMessage));
      })
    );
  }

  // [LEARN] HttpClient.get: サーバーからデータを取得するためのメソッド。
  // ジェネリクス <any> を指定することで、レスポンスの型を定義できます（ここでは簡易的に any としています）。
  getLogs() {
    return this.http.get<any[]>(`${this.baseUrl}/logs`);
  }

  getPolicies() {
    return this.http.get<any>(`${this.baseUrl}/policies`);
  }

  getKnowledgeList() {
    return this.http.get<any[]>(`${this.baseUrl}/knowledge`);
  }

  ingestFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.baseUrl}/ingest`, formData);
  }
}
