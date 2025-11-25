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
  private baseUrl = 'http://localhost:8000';
  private currentTenantId = '';

  constructor(private http: HttpClient) { }

  setTenantId(tenantId: string) {
    this.currentTenantId = tenantId;
  }

  login(userId: string, tenantId: string) {
    // [NEW] Mock Login
    return this.http.post(`${this.baseUrl}/auth/mock-login`, { user_id: userId, tenant_id: tenantId }, { withCredentials: true });
  }

  logout() {
    return this.http.post(`${this.baseUrl}/auth/logout`, {}, { withCredentials: true });
  }

  // [NEW] ストリーミング対応 (Refactored for Production)
  sendMessageStream(message: string, userId = 'frontend-user', files: File[] = []): Observable<any> {
    if (!this.currentTenantId) {
      return throwError(() => new Error('No tenant selected. Please login first.'));
    }

    return new Observable<any>(observer => {
      const controller = new AbortController();
      const signal = controller.signal;

      const formData = new FormData();
      // user_id is now inferred from cookie, but we might still send it for logging consistency if needed,
      // but the backend uses the cookie context. We'll keep sending it just in case logic depends on it,
      // but backend relies on cookie.
      formData.append('user_id', userId);
      formData.append('message', message);
      if (files && files.length > 0) {
        files.forEach(file => formData.append('files', file));
      }

      // [REFAC] Tenant-scoped URL & Credentials
      fetch(`${this.baseUrl}/tenants/${this.currentTenantId}/chat`, {
        method: 'POST',
        body: formData,
        signal,
        credentials: 'include' // [IMPORTANT] Send Cookies
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
      retry({ count: 2, delay: 1000 }),
      timeout(30000),
      catchError(err => {
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

  getLogs() {
    if (!this.currentTenantId) return throwError(() => new Error('Not logged in'));
    return this.http.get<any[]>(`${this.baseUrl}/tenants/${this.currentTenantId}/logs`, { withCredentials: true });
  }

  getPolicies() {
    if (!this.currentTenantId) return throwError(() => new Error('Not logged in'));
    return this.http.get<any>(`${this.baseUrl}/tenants/${this.currentTenantId}/policies`, { withCredentials: true });
  }

  getKnowledgeList() {
    if (!this.currentTenantId) return throwError(() => new Error('Not logged in'));
    return this.http.get<any[]>(`${this.baseUrl}/tenants/${this.currentTenantId}/knowledge`, { withCredentials: true });
  }

  ingestFile(file: File) {
    if (!this.currentTenantId) return throwError(() => new Error('Not logged in'));
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.baseUrl}/tenants/${this.currentTenantId}/ingest`, formData, { withCredentials: true });
  }
}
