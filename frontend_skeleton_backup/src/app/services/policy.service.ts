export class PolicyService {
  baseUrl = 'http://localhost:8000';

  async getPolicies(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/policies`);
    if (!res.ok) throw new Error('failed to fetch policies');
    return await res.json();
  }
}
