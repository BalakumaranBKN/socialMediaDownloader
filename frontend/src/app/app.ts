import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Toast } from 'primeng/toast';
import { MessageService } from 'primeng/api';

import { DownloaderService } from './services/downloader.service';
import { NavbarComponent } from './components/navbar/navbar.component';
import { UrlInputComponent } from './components/url-input/url-input.component';
import { MediaPreviewComponent } from './components/media-preview/media-preview.component';
import { HistoryComponent } from './components/history/history.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    Toast,
    NavbarComponent,
    UrlInputComponent,
    MediaPreviewComponent,
    HistoryComponent
  ],
  providers: [MessageService],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  downloader = inject(DownloaderService);
  messageService = inject(MessageService);

  historyDrawerVisible = signal<boolean>(false);

  handleUrlSubmit(url: string): void {
    this.downloader.fetchMediaInfo(url).subscribe({
      next: (info) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Media Found!',
          detail: `Loaded ${info.platform_name} ${info.media_type}: "${info.title.substring(0, 45)}..."`,
          life: 4000
        });
      },
      error: (err) => {
        const errorMsg = err.error?.detail || 'Could not fetch media from this link. Please check if the post is public.';
        this.messageService.add({
          severity: 'error',
          summary: 'Fetch Error',
          detail: errorMsg,
          life: 6000
        });
      }
    });
  }

  handleDownloadTrigger(event: { url: string; filename: string; ext: string; mode?: 'normal' | 'mute' | 'music' }): void {
    const mode = event.mode || 'normal';
    const downloadUrl = this.downloader.getDownloadUrl(event.url, event.filename, event.ext, mode);
    this.downloader.triggerDownload(downloadUrl);

    let summary = 'Download Started';
    let detail = `Downloading ${event.filename}.${event.ext}...`;
    let severity: 'info' | 'warn' | 'success' = 'info';

    if (mode === 'mute') {
      summary = 'Muted Video Download';
      detail = `Downloading silent video (no audio): ${event.filename}.${event.ext}`;
      severity = 'warn';
    } else if (mode === 'music') {
      summary = 'Music Track Download';
      detail = `Extracting & downloading MP3 music track: ${event.filename}.${event.ext}`;
      severity = 'success';
    }

    this.messageService.add({
      severity,
      summary,
      detail,
      life: 3500
    });
  }

  handleHistorySelect(url: string): void {
    this.historyDrawerVisible.set(false);
    this.handleUrlSubmit(url);
  }

  handleClearHistory(): void {
    this.downloader.clearHistory();
    this.messageService.add({
      severity: 'info',
      summary: 'History Cleared',
      detail: 'Recent downloads history has been reset.',
      life: 2500
    });
  }

  toggleHistoryDrawer(): void {
    this.historyDrawerVisible.update(v => !v);
  }

  clearMedia(): void {
    this.downloader.clearCurrentMedia();
  }
}
