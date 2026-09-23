import os
import re
import tempfile
import urllib.parse
from typing import Dict, Any, List, Optional
import yt_dlp
import requests
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_PATH = None

from ..models.schemas import MediaInfoResponse, MediaFormat, MediaItem, PlatformInfo

PLATFORMS_META = {
    "twitter": {
        "id": "twitter",
        "name": "Twitter / X",
        "icon": "pi-twitter",
        "badge_color": "#1DA1F2",
        "patterns": [r"(?:twitter\.com|x\.com)"],
        "supported_types": ["Video", "Image", "GIF", "Carousel"],
        "sample_url": "https://x.com/username/status/1234567890"
    },
    "instagram": {
        "id": "instagram",
        "name": "Instagram",
        "icon": "pi-instagram",
        "badge_color": "#E1306C",
        "patterns": [r"instagram\.com"],
        "supported_types": ["Reel", "Post", "Photo", "Carousel"],
        "sample_url": "https://www.instagram.com/reel/C8..."
    },
    "threads": {
        "id": "threads",
        "name": "Threads",
        "icon": "pi-at",
        "badge_color": "#000000",
        "patterns": [r"threads\.net"],
        "supported_types": ["Post", "Video", "Image"],
        "sample_url": "https://www.threads.net/@user/post/..."
    },
    "tiktok": {
        "id": "tiktok",
        "name": "TikTok",
        "icon": "pi-video",
        "badge_color": "#EE1D52",
        "patterns": [r"tiktok\.com"],
        "supported_types": ["Video", "Audio"],
        "sample_url": "https://www.tiktok.com/@user/video/..."
    },
    "reddit": {
        "id": "reddit",
        "name": "Reddit",
        "icon": "pi-reddit",
        "badge_color": "#FF4500",
        "patterns": [r"reddit\.com", r"redd\.it"],
        "supported_types": ["Video", "GIF", "Gallery"],
        "sample_url": "https://www.reddit.com/r/videos/comments/..."
    },
    "youtube": {
        "id": "youtube",
        "name": "YouTube Shorts",
        "icon": "pi-youtube",
        "badge_color": "#FF0000",
        "patterns": [r"(?:youtube\.com|youtu\.be)"],
        "supported_types": ["Shorts", "Video", "Audio"],
        "sample_url": "https://youtube.com/shorts/..."
    },
    "pinterest": {
        "id": "pinterest",
        "name": "Pinterest",
        "icon": "pi-image",
        "badge_color": "#BD081C",
        "patterns": [r"pinterest\.com", r"pin\.it"],
        "supported_types": ["Video", "Image"],
        "sample_url": "https://www.pinterest.com/pin/..."
    },
    "other": {
        "id": "other",
        "name": "Web Media",
        "icon": "pi-globe",
        "badge_color": "#6366F1",
        "patterns": [],
        "supported_types": ["Media"],
        "sample_url": "https://..."
    }
}


def detect_platform(url: str) -> Dict[str, Any]:
    url_lower = url.lower()
    for key, data in PLATFORMS_META.items():
        if key == "other":
            continue
        for pattern in data["patterns"]:
            if re.search(pattern, url_lower):
                return data
    return PLATFORMS_META["other"]


def format_filesize(size_bytes: Optional[int]) -> Optional[str]:
    if not size_bytes:
        return None
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_default_ydl_opts() -> Dict[str, Any]:
    opts = {
        'skip_download': True,
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    }
    if FFMPEG_PATH:
        opts['ffmpeg_location'] = FFMPEG_PATH
    return opts


def append_mute_and_music_formats(formats: List[MediaFormat], primary_video_url: Optional[str]):
    if not primary_video_url:
        return
    has_mute = any(f.download_mode == "mute" for f in formats)
    has_music = any(f.download_mode == "music" for f in formats)

    if not has_mute:
        formats.append(MediaFormat(
            format_id="mute_video",
            ext="mp4",
            resolution="Mute (No Audio)",
            quality_label="Mute Video (No Audio - MP4)",
            has_audio=False,
            has_video=True,
            is_mute=True,
            download_mode="mute",
            url=primary_video_url
        ))

    if not has_music:
        formats.append(MediaFormat(
            format_id="music_audio",
            ext="mp3",
            resolution="Music (MP3)",
            quality_label="Music Track (High Quality MP3)",
            has_audio=True,
            has_video=False,
            is_audio_only=True,
            download_mode="music",
            url=primary_video_url
        ))


def try_fxtwitter_fallback(url: str) -> Optional[MediaInfoResponse]:
    """
    Fallback for Twitter/X posts: FxTwitter API returns reliable JSON
    for videos, images, gifs, carousels without login blocks.
    """
    match = re.search(r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)", url)
    if not match:
        return None
    screen_name, status_id = match.groups()
    api_url = f"https://api.fxtwitter.com/{screen_name}/status/{status_id}"
    try:
        resp = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json().get("tweet")
        if not data:
            return None

        media = data.get("media", {})
        photos = media.get("photos", [])
        videos = media.get("videos", [])
        all_items: List[MediaItem] = []
        formats: List[MediaFormat] = []

        # Process videos/gifs
        media_type = "video" if videos else ("image" if photos else "other")
        thumb = None

        if photos:
            for idx, photo in enumerate(photos):
                photo_url = photo.get("url")
                if photo_url:
                    all_items.append(MediaItem(
                        index=idx + 1,
                        type="image",
                        url=photo_url,
                        thumbnail=photo_url,
                        resolution=f"{photo.get('width', 'HD')}x{photo.get('height', '')}".strip('x'),
                        ext="jpg"
                    ))
            if not videos and len(photos) > 1:
                media_type = "carousel"
            if photos:
                thumb = photos[0].get("url")

        if videos:
            for idx, vid in enumerate(videos):
                vid_url = vid.get("url")
                vid_thumb = vid.get("thumbnail_url")
                if not thumb:
                    thumb = vid_thumb
                if vid_url:
                    formats.append(MediaFormat(
                        format_id=f"fxtwitter_vid_{idx}",
                        ext="mp4",
                        resolution=f"{vid.get('width', '')}x{vid.get('height', '')}".strip('x') or "HD",
                        quality_label=f"Video ({vid.get('format', 'MP4')})",
                        has_audio=True,
                        has_video=True,
                        url=vid_url
                    ))
                    all_items.append(MediaItem(
                        index=idx + 1,
                        type="video",
                        url=vid_url,
                        thumbnail=vid_thumb,
                        ext="mp4"
                    ))

        # Add image formats
        for idx, item in enumerate(all_items):
            if item.type == "image":
                formats.append(MediaFormat(
                    format_id=f"image_{idx}",
                    ext=item.ext,
                    resolution=item.resolution or "Original",
                    quality_label=f"Photo #{item.index} (High Res)",
                    is_image=True,
                    has_video=False,
                    has_audio=False,
                    url=item.url
                ))

        if videos and formats:
            first_vid_url = next((v.get("url") for v in videos if v.get("url")), None)
            append_mute_and_music_formats(formats, first_vid_url)

        return MediaInfoResponse(
            id=str(status_id),
            platform="twitter",
            platform_name="Twitter / X",
            platform_icon="pi-twitter",
            title=data.get("text") or f"Post by @{screen_name}",
            description=data.get("text", ""),
            author=f"@{screen_name} ({data.get('author', {}).get('name', '')})",
            author_url=f"https://x.com/{screen_name}",
            author_avatar=data.get('author', {}).get('avatar_url'),
            thumbnail=thumb,
            duration_string=None,
            media_type=media_type,
            formats=formats,
            items=all_items,
            original_url=url
        )
    except Exception as e:
        print(f"FxTwitter fallback failed: {e}")
        return None


def extract_instagram_media(url: str) -> Optional[MediaInfoResponse]:
    """
    Direct Instagram extractor leveraging InstagramIE to extract single photos,
    multi-photo carousels, reels, and video clips without yt-dlp's 'no video formats found' crash.
    """
    try:
        from yt_dlp.extractor.instagram import InstagramIE
        ydl_opts = get_default_ydl_opts()
        ydl = yt_dlp.YoutubeDL(ydl_opts)
        ie = InstagramIE(ydl)
        res = ie._real_extract(url)
        if not res:
            return None

        post_id = str(res.get("id") or "instagram_media")
        title = res.get("title") or res.get("description") or "Instagram Post"
        if len(title) > 120:
            title = title[:117] + "..."
        author = res.get("uploader") or res.get("channel") or "Instagram Creator"
        author_url = res.get("uploader_url")

        items: List[MediaItem] = []
        formats: List[MediaFormat] = []

        # If it's a carousel / playlist of entries
        entries = list(res.get("entries", [])) if res.get("entries") else [res]
        main_thumbnail = None

        for idx, entry in enumerate(entries):
            if not entry:
                continue

            vcodec = entry.get("vcodec")
            is_video = (vcodec and vcodec != "none") or bool(entry.get("formats"))
            thumbs = entry.get("thumbnails") or []
            best_img = thumbs[-1]["url"] if thumbs else entry.get("thumbnail")
            thumb_img = thumbs[0]["url"] if thumbs else best_img

            if not main_thumbnail and (best_img or thumb_img):
                main_thumbnail = best_img or thumb_img

            if is_video:
                vid_url = None
                raw_fmts = entry.get("formats") or []
                if raw_fmts:
                    raw_fmts_sorted = sorted(
                        [f for f in raw_fmts if f.get("url") and f.get("vcodec") != "none"],
                        key=lambda f: f.get("height") or 0,
                        reverse=True
                    )
                    if raw_fmts_sorted:
                        vid_url = raw_fmts_sorted[0].get("url")
                if not vid_url:
                    vid_url = entry.get("url")

                if vid_url:
                    res_label = f"{entry.get('height', 'HD')}p" if entry.get("height") else "HD"
                    formats.append(MediaFormat(
                        format_id=f"ig_vid_{idx}",
                        ext="mp4",
                        resolution=res_label,
                        quality_label=f"Video #{idx + 1} ({res_label} MP4)",
                        has_video=True,
                        has_audio=True,
                        url=vid_url
                    ))
                    items.append(MediaItem(
                        index=idx + 1,
                        type="video",
                        url=vid_url,
                        thumbnail=thumb_img or best_img,
                        ext="mp4"
                    ))
            else:
                if best_img:
                    res_map = {"original": best_img, "1080p": best_img}
                    for t in thumbs:
                        t_url = t.get("url")
                        t_width = t.get("width") or 0
                        t_str = str(t_url)
                        if t_width in [320, 360, 480] or "320x320" in t_str or "360x360" in t_str:
                            res_map["360p"] = t_url
                        elif t_width in [640, 720, 750] or "640x640" in t_str or "720x720" in t_str:
                            res_map["720p"] = t_url
                        elif t_width >= 1080 or "1080x1080" in t_str:
                            res_map["1080p"] = t_url

                    if "720p" not in res_map:
                        res_map["720p"] = best_img
                    if "360p" not in res_map:
                        res_map["360p"] = thumb_img or best_img

                    formats.append(MediaFormat(
                        format_id=f"ig_photo_{idx}",
                        ext="jpg",
                        resolution="1080p",
                        quality_label=f"Photo #{idx + 1} (1080p Full HD)",
                        is_image=True,
                        has_video=False,
                        has_audio=False,
                        url=best_img
                    ))
                    items.append(MediaItem(
                        index=idx + 1,
                        type="image",
                        url=best_img,
                        thumbnail=thumb_img or best_img,
                        ext="jpg",
                        resolution_urls=res_map
                    ))

        if not items and not formats:
            return None

        first_vid_url = next((it.url for it in items if it.type == "video"), next((f.url for f in formats if f.has_video and f.url), None))
        if first_vid_url:
            append_mute_and_music_formats(formats, first_vid_url)

        media_type = "carousel" if len(items) > 1 else (items[0].type if items else "image")

        return MediaInfoResponse(
            id=post_id,
            platform="instagram",
            platform_name="Instagram",
            platform_icon="pi-instagram",
            title=title,
            description=res.get("description", "") or "",
            author=author,
            author_url=author_url,
            author_avatar=None,
            thumbnail=main_thumbnail or (items[0].thumbnail if items else None),
            duration_string=res.get("duration_string"),
            media_type=media_type,
            formats=formats,
            items=items,
            original_url=url
        )
    except Exception as e:
        print(f"Direct Instagram extraction failed: {e}")
        return None


def extract_media_info(url: str) -> MediaInfoResponse:
    platform_data = detect_platform(url)

    # For Twitter, try the FxTwitter API first for speed & resilience
    if platform_data["id"] == "twitter":
        fx_result = try_fxtwitter_fallback(url)
        if fx_result and (fx_result.formats or fx_result.items):
            return fx_result

    # For Instagram, use direct InstagramIE to properly extract photos & carousels
    if platform_data["id"] == "instagram":
        ig_result = extract_instagram_media(url)
        if ig_result and (ig_result.formats or ig_result.items):
            return ig_result

    ydl_opts = get_default_ydl_opts()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Could not extract any media information.")

            # Handle playlist / multi-entry (e.g. carousels)
            entries = info.get("entries")
            items: List[MediaItem] = []
            formats: List[MediaFormat] = []
            
            title = info.get("title") or info.get("description") or f"Media from {platform_data['name']}"
            if len(title) > 120:
                title = title[:117] + "..."

            author = info.get("uploader") or info.get("channel") or info.get("creator") or "Social Media Creator"
            thumbnail = info.get("thumbnail")
            duration = info.get("duration_string")

            # Check if multi-item carousel/playlist
            if entries:
                for idx, entry in enumerate(entries):
                    if not entry:
                        continue
                    e_url = entry.get("url") or (entry.get("formats")[-1]["url"] if entry.get("formats") else None)
                    e_thumb = entry.get("thumbnail")
                    e_type = "video" if entry.get("vcodec") != "none" else "image"
                    if e_url:
                        items.append(MediaItem(
                            index=idx + 1,
                            type=e_type,
                            url=e_url,
                            thumbnail=e_thumb or thumbnail,
                            title=entry.get("title"),
                            ext=entry.get("ext", "mp4" if e_type == "video" else "jpg")
                        ))

            # Process formats for single video or primary entry
            raw_formats = info.get("formats") or []
            # Deduplicate by resolution / format
            seen_res = set()
            
            # If video has formats
            for f in raw_formats:
                url_direct = f.get("url")
                if not url_direct:
                    continue
                vcodec = f.get("vcodec", "none")
                acodec = f.get("acodec", "none")
                ext = f.get("ext", "mp4")
                height = f.get("height")
                filesize = f.get("filesize") or f.get("filesize_approx")
                
                is_video = vcodec != "none"
                is_audio = acodec != "none"

                res_label = f"{height}p" if height else (f.get("format_note") or f.get("resolution") or "Standard")
                
                # Check for audio only
                if is_audio and not is_video:
                    formats.append(MediaFormat(
                        format_id=f.get("format_id", "audio"),
                        ext=ext if ext in ["mp3", "m4a", "aac"] else "m4a",
                        resolution="Audio Only",
                        filesize=filesize,
                        filesize_formatted=format_filesize(filesize),
                        quality_label=f"Audio ({ext.upper()})",
                        has_audio=True,
                        has_video=False,
                        is_audio_only=True,
                        url=url_direct
                    ))
                    continue

                if is_video:
                    key = f"{res_label}_{ext}"
                    if key in seen_res:
                        continue
                    seen_res.add(key)

                    label = f"{res_label} HD" if height and height >= 720 else res_label
                    formats.append(MediaFormat(
                        format_id=f.get("format_id", "video"),
                        ext=ext,
                        resolution=res_label,
                        filesize=filesize,
                        filesize_formatted=format_filesize(filesize),
                        quality_label=f"Video - {label} ({ext.upper()})",
                        has_audio=is_audio,
                        has_video=True,
                        url=url_direct
                    ))

            # If no formats extracted, but direct URL exists
            if not formats and info.get("url"):
                ext = info.get("ext", "mp4")
                formats.append(MediaFormat(
                    format_id="best",
                    ext=ext,
                    resolution="Best Quality",
                    quality_label=f"Standard Download ({ext.upper()})",
                    has_audio=True,
                    has_video=True,
                    url=info.get("url")
                ))

            # Determine media type
            if items and len(items) > 1:
                media_type = "carousel"
            elif any(f.is_image for f in formats) or info.get("ext") in ["jpg", "jpeg", "png", "webp"]:
                media_type = "image"
            elif info.get("ext") == "gif":
                media_type = "gif"
            else:
                media_type = "video"

            # Fallback item if items list is empty
            if not items and formats:
                primary_url = formats[0].url or info.get("url")
                if primary_url:
                    items.append(MediaItem(
                        index=1,
                        type=media_type,
                        url=primary_url,
                        thumbnail=thumbnail,
                        ext=formats[0].ext
                    ))

            if media_type == "video" or any(f.has_video for f in formats):
                first_vid_url = next((it.url for it in items if it.type == "video"), next((f.url for f in formats if f.has_video and f.url), info.get("url")))
                if first_vid_url:
                    append_mute_and_music_formats(formats, first_vid_url)

            return MediaInfoResponse(
                id=str(info.get("id", "media")),
                platform=platform_data["id"],
                platform_name=platform_data["name"],
                platform_icon=platform_data["icon"],
                title=title,
                description=info.get("description", "") or "",
                author=author,
                author_url=info.get("uploader_url"),
                author_avatar=None,
                thumbnail=thumbnail,
                duration_string=duration,
                media_type=media_type,
                formats=formats,
                items=items,
                original_url=url
            )
    except Exception as e:
        # If yt-dlp failed, try fallback
        if platform_data["id"] == "twitter":
            fx_result = try_fxtwitter_fallback(url)
            if fx_result:
                return fx_result
        raise RuntimeError(f"Error fetching media: {str(e)}")
