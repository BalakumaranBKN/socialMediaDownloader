export interface MediaFormat {
  format_id: string;
  ext: string;
  resolution: string;
  filesize?: number | null;
  filesize_formatted?: string | null;
  quality_label: string;
  has_audio: boolean;
  has_video: boolean;
  is_image: boolean;
  is_audio_only: boolean;
  is_mute?: boolean;
  download_mode?: 'normal' | 'mute' | 'music';
  url?: string | null;
}

export interface MediaItem {
  index: number;
  type: 'video' | 'image' | 'gif';
  url: string;
  thumbnail?: string | null;
  title?: string | null;
  resolution?: string | null;
  ext: string;
  resolution_urls?: Record<string, string> | null;
}

export interface MediaInfo {
  id: string;
  platform: 'twitter' | 'instagram' | 'threads' | 'tiktok' | 'reddit' | 'youtube' | 'pinterest' | 'other';
  platform_name: string;
  platform_icon: string;
  title: string;
  description?: string;
  author?: string;
  author_url?: string;
  author_avatar?: string;
  thumbnail?: string;
  duration_string?: string;
  media_type: 'video' | 'image' | 'gif' | 'carousel';
  formats: MediaFormat[];
  items: MediaItem[];
  original_url: string;
}

export interface PlatformInfo {
  id: string;
  name: string;
  icon: string;
  badge_color: string;
  supported_types: string[];
  sample_url: string;
}

export interface HistoryItem {
  id: string;
  url: string;
  platform: string;
  platform_name: string;
  title: string;
  thumbnail?: string;
  timestamp: number;
  media_type: string;
}
