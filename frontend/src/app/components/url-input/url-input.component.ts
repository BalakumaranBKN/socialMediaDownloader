import { Component, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Button } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { ProgressBar } from 'primeng/progressbar';

@Component({
  selector: 'app-url-input',
  standalone: true,
  imports: [CommonModule, FormsModule, Button, InputText, ProgressBar],
  templateUrl: './url-input.component.html',
  styleUrl: './url-input.component.scss'
})
export class UrlInputComponent {
  loading = input<boolean>(false);
  urlSubmit = output<string>();

  url = '';
  isFocused = false;

  detectedPlatform = signal<{ name: string; icon: string; color: string }>({
    name: 'Link',
    icon: 'pi-link',
    color: '#94a3b8'
  });

  onUrlChange(val: string): void {
    const v = val.toLowerCase();
    if (v.includes('twitter.com') || v.includes('x.com')) {
      this.detectedPlatform.set({ name: 'Twitter / X', icon: 'pi-twitter', color: '#1DA1F2' });
    } else if (v.includes('instagram.com')) {
      this.detectedPlatform.set({ name: 'Instagram', icon: 'pi-instagram', color: '#E1306C' });
    } else if (v.includes('threads.net')) {
      this.detectedPlatform.set({ name: 'Threads', icon: 'pi-at', color: '#ffffff' });
    } else if (v.includes('tiktok.com')) {
      this.detectedPlatform.set({ name: 'TikTok', icon: 'pi-video', color: '#EE1D52' });
    } else if (v.includes('reddit.com') || v.includes('redd.it')) {
      this.detectedPlatform.set({ name: 'Reddit', icon: 'pi-reddit', color: '#FF4500' });
    } else if (v.includes('youtube.com') || v.includes('youtu.be')) {
      this.detectedPlatform.set({ name: 'YouTube', icon: 'pi-youtube', color: '#FF0000' });
    } else if (v.includes('pinterest.com') || v.includes('pin.it')) {
      this.detectedPlatform.set({ name: 'Pinterest', icon: 'pi-image', color: '#BD081C' });
    } else {
      this.detectedPlatform.set({ name: 'Link', icon: 'pi-link', color: '#94a3b8' });
    }
  }

  async pasteClipboard(): Promise<void> {
    try {
      if (navigator.clipboard) {
        const text = await navigator.clipboard.readText();
        if (text) {
          this.url = text.trim();
          this.onUrlChange(this.url);
          this.onSubmit();
        }
      }
    } catch (e) {
      console.warn('Clipboard read access was not granted:', e);
    }
  }

  clearUrl(): void {
    this.url = '';
    this.onUrlChange('');
  }

  setPlatformExample(platform: string): void {
    const examples: Record<string, string> = {
      'twitter': 'https://x.com/SpaceX/status/1768253944684941584',
      'instagram': 'https://www.instagram.com/reel/C321example/',
      'threads': 'https://www.threads.net/@zuck/post/CuU50o1rk3U',
      'tiktok': 'https://www.tiktok.com/@tiktok/video/7106594312292453678',
      'youtube': 'https://youtube.com/shorts/5example123',
      'reddit': 'https://www.reddit.com/r/videos/comments/example/'
    };
    if (examples[platform]) {
      this.url = examples[platform];
      this.onUrlChange(this.url);
    }
  }

  onSubmit(): void {
    if (this.url.trim() && !this.loading()) {
      this.urlSubmit.emit(this.url.trim());
    }
  }
}

