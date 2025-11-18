export class LogService {
  baseUrl = 'http://localhost:8000';

  async getLogs(limit = 50): Promise<any> {
    const res = await fetch(`${this.baseUrl}/logs?limit=${limit}`);
    if (!res.ok) throw new Error('failed to fetch logs');
    return await res.json();
  }
}
