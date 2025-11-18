import { LogService } from '../../services/log.service';

export class LogViewerComponent {
  svc = new LogService();
  logs: any[] = [];

  async load() {
    this.logs = await this.svc.getLogs(50);
  }
}
