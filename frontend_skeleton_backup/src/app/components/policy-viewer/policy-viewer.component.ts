import { PolicyService } from '../../services/policy.service';

export class PolicyViewerComponent {
  svc = new PolicyService();
  policies: any = null;

  async load() {
    this.policies = await this.svc.getPolicies();
  }
}
