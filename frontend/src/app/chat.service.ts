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

  constructor(private http: HttpClient) {}

  sendMessage(message: string, userId = 'frontend-user'): Observable<ChatResponse> {
    const body: ChatRequest = { message, user_id: userId };
    return this.http.post<ChatResponse>(`${this.baseUrl}/chat`, body);
  }
}
