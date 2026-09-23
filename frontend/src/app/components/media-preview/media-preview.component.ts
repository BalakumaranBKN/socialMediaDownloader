import { Component, input, output, signal, computed, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Button } from 'primeng/button';
import { Tag } from 'primeng/tag';
import { Select } from 'primeng/select';
import { Tooltip } from 'primeng/tooltip';
import { MediaInfo, MediaFormat, MediaItem } from '../../models/media.model';

@Component({
  selector: 'app-media-preview',
  standalone: true,
  imports: [CommonModule, FormsModule, Button, Tag, Select, Tooltip],
  templateUrl: './media-preview.component.html',
  styleUrl: './media-preview.component.scss'
})
export class MediaPreviewComponent implements OnChanges {
  media = input<MediaInfo | null>(null);
  downloadTrigger = output<{ url: string; filename: string; ext: string; mode?: 'normal' | 'mute' | 'music' }>();
  close = output<void>();

  selectedFormat: MediaFormat | null = null;
  selectedItemIndex = signal<number>(0);
  selectedIndices = signal<number[]>([]);

  ngOnChanges(): void {
    const info = this.media();
    if (info && info.formats && info.formats.length > 0) {
      // Default to first video format if available, otherwise first format
      const firstVid = info.formats.find(f => f.has_video && !f.is_mute && !f.is_image);
      this.selectedFormat = firstVid || info.formats[0];
    }
    this.selectedItemIndex.set(0);
    // Select all items by default for easy batch or selective download
    if (info?.items && info.items.length > 0) {
      this.selectedIndices.set(info.items.map((_, i) => i));
    } else {
      this.selectedIndices.set([]);
    }
  }

  isVideoMedia = computed<boolean>(() => {
    const info = this.media();
    if (!info) return false;
    if (info.media_type === 'video') return true;
    const item = this.currentItem();
    if (item && item.type === 'video') return true;
    return !!(info.formats && info.formats.some(f => f.has_video && !f.is_image));
  });

  videoFormats = computed<MediaFormat[]>(() => {
    const info = this.media();
    if (!info?.formats) return [];
    return info.formats.filter(f => f.has_video && !f.is_mute && !f.is_image);
  });

  muteFormat = computed<MediaFormat | null>(() => {
    const info = this.media();
    if (!info?.formats) return null;
    return info.formats.find(f => f.is_mute || f.download_mode === 'mute') || null;
  });

  musicFormat = computed<MediaFormat | null>(() => {
    const info = this.media();
    if (!info?.formats) return null;
    return info.formats.find(f => f.is_audio_only || f.download_mode === 'music') || null;
  });

  currentItem = computed<MediaItem | null>(() => {
    const info = this.media();
    if (!info || !info.items || info.items.length === 0) return null;
    return info.items[this.selectedItemIndex()] || info.items[0];
  });

  activeCarouselItem = computed<MediaItem | null>(() => {
    return this.currentItem();
  });

  activeVideoUrl(): string {
    const item = this.currentItem();
    if (item && item.type === 'video') {
      return item.url;
    }
    if (this.selectedFormat && this.selectedFormat.url) {
      return this.selectedFormat.url;
    }
    const info = this.media();
    if (info?.formats && info.formats.length > 0 && info.formats[0].url) {
      return info.formats[0].url;
    }
    return '';
  }

  activeImageUrl(): string {
    const item = this.currentItem();
    if (item && item.url) return item.url;
    const info = this.media();
    return info?.thumbnail || '';
  }

  selectItem(index: number): void {
    this.selectedItemIndex.set(index);
  }

  prevItem(): void {
    const info = this.media();
    if (!info?.items?.length) return;
    const count = info.items.length;
    this.selectedItemIndex.update(i => (i - 1 + count) % count);
  }

  nextItem(): void {
    const info = this.media();
    if (!info?.items?.length) return;
    const count = info.items.length;
    this.selectedItemIndex.update(i => (i + 1) % count);
  }

  toggleSelect(index: number, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    const current = this.selectedIndices();
    if (current.includes(index)) {
      this.selectedIndices.set(current.filter(i => i !== index));
    } else {
      this.selectedIndices.set([...current, index].sort((a, b) => a - b));
    }
  }

  isItemSelected(index: number): boolean {
    return this.selectedIndices().includes(index);
  }

  selectAll(): void {
    const info = this.media();
    if (info?.items) {
      this.selectedIndices.set(info.items.map((_, i) => i));
    }
  }

  clearSelection(): void {
    this.selectedIndices.set([]);
  }

  selectOnly(index: number, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.selectedItemIndex.set(index);
    this.selectedIndices.set([index]);
  }

  platformColor(platform: string): string {
    switch (platform) {
      case 'twitter': return '#1DA1F2';
      case 'instagram': return '#E1306C';
      case 'threads': return '#1e293b';
      case 'tiktok': return '#EE1D52';
      case 'reddit': return '#FF4500';
      case 'youtube': return '#FF0000';
      case 'pinterest': return '#BD081C';
      default: return '#6366F1';
    }
  }

  getMediaTypeSeverity(type: string): 'info' | 'success' | 'warn' | 'danger' | 'secondary' {
    switch (type) {
      case 'video': return 'danger';
      case 'carousel': return 'info';
      case 'image': return 'success';
      case 'gif': return 'warn';
      default: return 'secondary';
    }
  }

  onDownloadChosen(): void {
    const info = this.media();
    if (!info) return;

    const fmt = this.selectedFormat || (info.formats && info.formats[0]);
    const targetUrl = fmt?.url || this.activeVideoUrl() || info.original_url;
    const ext = fmt?.ext || 'mp4';
    const mode = (fmt?.download_mode || (fmt?.is_mute ? 'mute' : (fmt?.is_audio_only ? 'music' : 'normal'))) as 'normal' | 'mute' | 'music';
    const filename = `${info.platform}_${info.id}_${fmt?.resolution || 'media'}`.replace(/\s+/g, '_');

    this.downloadTrigger.emit({
      url: targetUrl,
      filename,
      ext,
      mode
    });
  }

  downloadVideoNormal(): void {
    const info = this.media();
    if (!info) return;

    const fmt = (this.selectedFormat && this.selectedFormat.has_video && !this.selectedFormat.is_mute)
      ? this.selectedFormat
      : (this.videoFormats()[0] || info.formats?.[0]);

    const targetUrl = fmt?.url || this.activeVideoUrl() || info.original_url;
    const ext = fmt?.ext || 'mp4';
    const filename = `${info.platform}_${info.id}_${fmt?.resolution || 'video'}`.replace(/\s+/g, '_');

    this.downloadTrigger.emit({
      url: targetUrl,
      filename,
      ext,
      mode: 'normal'
    });
  }

  downloadVideoMute(): void {
    const info = this.media();
    if (!info) return;

    const fmt = this.muteFormat();
    const targetUrl = fmt?.url || this.activeVideoUrl() || info.original_url;
    const filename = `${info.platform}_${info.id}_mute`.replace(/\s+/g, '_');

    this.downloadTrigger.emit({
      url: targetUrl,
      filename,
      ext: 'mp4',
      mode: 'mute'
    });
  }

  downloadVideoMusic(): void {
    const info = this.media();
    if (!info) return;

    const fmt = this.musicFormat();
    const targetUrl = fmt?.url || this.activeVideoUrl() || info.original_url;
    const filename = `${info.platform}_${info.id}_music`.replace(/\s+/g, '_');

    this.downloadTrigger.emit({
      url: targetUrl,
      filename,
      ext: 'mp3',
      mode: 'music'
    });
  }

  downloadParticularItem(item: MediaItem, event?: Event, mode: 'normal' | 'mute' | 'music' = 'normal'): void {
    if (event) {
      event.stopPropagation();
    }
    const info = this.media();
    if (!info || !item) return;

    const ext = mode === 'music' ? 'mp3' : (item.ext || (item.type === 'video' ? 'mp4' : 'jpg'));
    const suffix = mode === 'mute' ? '_mute' : (mode === 'music' ? '_music' : '');
    const filename = `${info.platform}_${info.id}_${item.type}_${item.index}${suffix}`.replace(/\s+/g, '_');
    this.downloadTrigger.emit({
      url: item.url,
      filename,
      ext,
      mode
    });
  }

  downloadCurrentCarouselItem(): void {
    const item = this.currentItem();
    if (item) {
      this.downloadParticularItem(item);
    }
  }

  downloadSelectedItems(): void {
    const info = this.media();
    if (!info || !info.items) return;

    const indices = this.selectedIndices();
    const itemsToDownload = indices.length > 0
      ? info.items.filter((_, idx) => indices.includes(idx))
      : [this.currentItem() || info.items[0]];

    itemsToDownload.forEach((item, i) => {
      setTimeout(() => {
        this.downloadParticularItem(item);
      }, i * 400);
    });
  }

  downloadAllItems(): void {
    const info = this.media();
    if (!info || !info.items) return;

    info.items.forEach((item, index) => {
      setTimeout(() => {
        this.downloadParticularItem(item);
      }, index * 400);
    });
  }

  copyMediaLink(): void {
    const fmt = this.selectedFormat;
    const url = fmt?.url || this.currentItem()?.url || this.media()?.original_url;
    if (url && navigator.clipboard) {
      navigator.clipboard.writeText(url);
    }
  }
}
