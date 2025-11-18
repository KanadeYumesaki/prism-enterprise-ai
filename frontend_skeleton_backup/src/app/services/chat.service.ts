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

export class ChatService {
  baseUrl = 'http://localhost:8000';

  async sendMessage(req: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('chat request failed');
    return await res.json();
  }
}
