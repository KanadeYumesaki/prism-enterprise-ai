import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { ChatService } from './chat.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatCardModule, MatFormFieldModule,
    MatInputModule, MatButtonModule
  ],
  template: `
    <div class="login-container">
      <mat-card>
        <mat-card-header>
          <mat-card-title>Prism Login</mat-card-title>
          <mat-card-subtitle>Mock Auth & Multi-tenancy</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div style="margin-top: 24px; display: flex; flex-direction: column; gap: 16px;">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>User ID</mat-label>
              <input matInput [(ngModel)]="userId" list="userList" placeholder="e.g. user-1">
              <datalist id="userList">
                <option value="user-1">Alice (Admin)</option>
                <option value="user-2">Bob (User)</option>
              </datalist>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Tenant ID</mat-label>
              <input matInput [(ngModel)]="tenantId" list="tenantList" placeholder="e.g. tenant-a">
              <datalist id="tenantList">
                <option value="tenant-a">Acme Corp</option>
                <option value="tenant-b">Beta Inc</option>
              </datalist>
            </mat-form-field>

            <p *ngIf="error" style="color: red;">{{ error }}</p>
          </div>
        </mat-card-content>
        <mat-card-actions align="end">
          <button mat-raised-button color="primary" (click)="login()" [disabled]="loading">
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </mat-card-actions>
      </mat-card>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background-color: #f5f5f5;
    }
    mat-card {
      width: 400px;
      padding: 24px;
    }
    .full-width {
      width: 100%;
    }
  `]
})
export class LoginComponent {
  userId = 'user-1';
  tenantId = 'tenant-a';
  loading = false;
  error = '';

  @Output() loginSuccess = new EventEmitter<{ userId: string, tenantId: string }>();

  constructor(private chatService: ChatService) { }

  login() {
    console.log('[LoginComponent] Login button clicked', { user: this.userId, tenant: this.tenantId });
    this.loading = true;
    this.error = '';
    this.chatService.login(this.userId, this.tenantId).subscribe({
      next: (response) => {
        console.log('[LoginComponent] Login successful', response);
        this.loading = false;
        this.chatService.setTenantId(this.tenantId);
        console.log('[LoginComponent] Emitting loginSuccess event');
        this.loginSuccess.emit({ userId: this.userId, tenantId: this.tenantId });
      },
      error: (err) => {
        console.error('[LoginComponent] Login failed', err);
        this.loading = false;
        this.error = 'Login failed. Please check your credentials.';
        console.error(err);
      }
    });
  }
}
