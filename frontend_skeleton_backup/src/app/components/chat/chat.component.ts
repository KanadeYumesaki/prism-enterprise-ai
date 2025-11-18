import { ChatService } from '../../services/chat.service';

export class ChatComponent {
  chat = new ChatService();
  history: Array<{ from: string; text: string; meta?: any }> = [];
  userId = 'user_local';

  async send(message: string) {
    this.history.push({ from: 'user', text: message });
    const resp = await this.chat.sendMessage({ user_id: this.userId, message });
    this.history.push({ from: 'ai', text: resp.reply, meta: { mode: resp.mode, model: resp.model, latency_ms: resp.latency_ms } });
  }
}
