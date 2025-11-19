// src/app/chat.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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
    return this.http.post<ChatResponse>(`${this.baseUrl}/chat`, formData);
  }

  // [LEARN] HttpClient.get: サーバーからデータを取得するためのメソッド。
  // ジェネリクス <any> を指定することで、レスポンスの型を定義できます（ここでは簡易的に any としています）。
  getLogs() {
    return this.http.get<any[]>(`${this.baseUrl}/logs`);
  }

  getPolicies() {
    return this.http.get<any>(`${this.baseUrl}/policies`);
  }
}
