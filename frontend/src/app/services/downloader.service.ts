import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { MediaInfo, PlatformInfo, HistoryItem } from '../models/media.model';
import { Capacitor } from '@capacitor/core';

@Injectable({
  providedIn: 'root'
})
export class DownloaderService {
  private readonly API_STORAGE_KEY = 'omnigrab_api_url';
  private readonly HISTORY_KEY = 'social_dl_history';

  get apiUrl(): string {
    if (typeof window !== 'undefined') {
      const customUrl = localStorage.getItem(this.API_STORAGE_KEY);
      if (customUrl) return customUrl.replace(/\/+$/, '');

      if (Capacitor.isNativePlatform()) {
        return 'http://192.168.1.5:8000/api';
      }

      if (window.location.port === '4200') {
        return 'http://localhost:8000/api';
      }
    }
    return '/api';
  }

  setCustomApiUrl(url: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.API_STORAGE_KEY, url);
      this.fetchPlatforms();
    }
  }

  // Signals for reactive state management
  mediaInfo = signal<MediaInfo | null>(null);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);
  platforms = signal<PlatformInfo[]>([]);
  history = signal<HistoryItem[]>([]);

  constructor(private http: HttpClient) {
    this.loadHistory();
    this.fetchPlatforms();
  }

  fetchPlatforms(): void {
    this.http.get<PlatformInfo[]>(`${this.apiUrl}/platforms`).subscribe({
      next: (data) => this.platforms.set(data),
      error: (err) => console.error('Failed to load platforms', err)
    });
  }

  fetchMediaInfo(url: string): Observable<MediaInfo> {
    this.loading.set(true);
    this.error.set(null);
    this.mediaInfo.set(null);

    return this.http.post<MediaInfo>(`${this.apiUrl}/info`, { url }).pipe(
      tap({
        next: (info) => {
          this.mediaInfo.set(info);
          this.loading.set(false);
          this.addToHistory(info);
        },
        error: (err) => {
          this.loading.set(false);
          const msg = err.error?.detail || err.message || 'Failed to extract media. Please verify the URL.';
          this.error.set(msg);
        }
      })
    );
  }

  getDownloadUrl(directUrl: string, filename: string, ext: string, mode: 'normal' | 'mute' | 'music' = 'normal'): string {
    const encodedUrl = encodeURIComponent(directUrl);
    const encodedName = encodeURIComponent(filename);
    const encodedMode = encodeURIComponent(mode);
    return `${this.apiUrl}/download?url=${encodedUrl}&filename=${encodedName}&ext=${ext}&mode=${encodedMode}`;
  }

  getYtdlDownloadUrl(pageUrl: string, formatId: string, filename: string): string {
    const encodedUrl = encodeURIComponent(pageUrl);
    const encodedFormat = encodeURIComponent(formatId);
    const encodedName = encodeURIComponent(filename);
    return `${this.apiUrl}/download-ytdl?url=${encodedUrl}&format_id=${encodedFormat}&filename=${encodedName}`;
  }

  triggerDownload(downloadUrl: string): void {
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.setAttribute('download', '');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  // History management
  private loadHistory(): void {
    try {
      const data = localStorage.getItem(this.HISTORY_KEY);
      if (data) {
        this.history.set(JSON.parse(data));
      }
    } catch (e) {
      console.error('Error loading history', e);
    }
  }

  private addToHistory(info: MediaInfo): void {
    try {
      const item: HistoryItem = {
        id: info.id,
        url: info.original_url,
        platform: info.platform,
        platform_name: info.platform_name,
        title: info.title,
        thumbnail: info.thumbnail,
        timestamp: Date.now(),
        media_type: info.media_type
      };

      const existing = this.history().filter(h => h.url !== info.original_url);
      const updated = [item, ...existing].slice(0, 15); // keep last 15
      this.history.set(updated);
      localStorage.setItem(this.HISTORY_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error('Error saving history', e);
    }
  }

  clearHistory(): void {
    this.history.set([]);
    localStorage.removeItem(this.HISTORY_KEY);
  }

  clearCurrentMedia(): void {
    this.mediaInfo.set(null);
    this.error.set(null);
  }
}
