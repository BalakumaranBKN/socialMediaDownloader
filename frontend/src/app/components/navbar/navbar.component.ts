import { Component, input, output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Button } from 'primeng/button';
import { BadgeModule } from 'primeng/badge';
import { PlatformInfo } from '../../models/media.model';
import { DownloaderService } from '../../services/downloader.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, Button, BadgeModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})
export class NavbarComponent {
  private downloader = inject(DownloaderService);

  platforms = input<PlatformInfo[]>([]);
  historyCount = input<number>(0);
  toggleHistory = output<void>();

  changeServerUrl(): void {
    const current = this.downloader.apiUrl;
    const newUrl = prompt('Backend Server API URL:', current);
    if (newUrl && newUrl.trim() && newUrl.trim() !== current) {
      this.downloader.setCustomApiUrl(newUrl.trim());
      alert('Backend server updated to: ' + newUrl.trim());
    }
  }
}
