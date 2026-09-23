from typing import List, Optional
from pydantic import BaseModel, Field


class UrlRequest(BaseModel):
    url: str = Field(..., description="The social media URL to extract or download")


class MediaFormat(BaseModel):
    format_id: str
    ext: str
    resolution: str
    filesize: Optional[int] = None
    filesize_formatted: Optional[str] = None
    quality_label: str
    has_audio: bool = True
    has_video: bool = True
    is_image: bool = False
    is_audio_only: bool = False
    is_mute: bool = False
    download_mode: str = "normal"  # "normal", "mute", "music"
    url: Optional[str] = None


class MediaItem(BaseModel):
    index: int = 0
    type: str = "image"  # "video", "image", "gif"
    url: str
    thumbnail: Optional[str] = None
    title: Optional[str] = None
    resolution: Optional[str] = None
    ext: str = "jpg"
    resolution_urls: Optional[dict[str, str]] = {}


class BatchDownloadItem(BaseModel):
    url: str
    filename: str
    ext: str = "jpg"


class BatchDownloadRequest(BaseModel):
    items: List[BatchDownloadItem]
    resolution: str = "1080p"  # "1080p", "720p", "360p", "original"
    zip_name: Optional[str] = "social_media_album.zip"


class MediaInfoResponse(BaseModel):
    id: str
    platform: str
    platform_name: str
    platform_icon: str
    title: str
    description: Optional[str] = ""
    author: Optional[str] = "Unknown"
    author_url: Optional[str] = None
    author_avatar: Optional[str] = None
    thumbnail: Optional[str] = None
    duration_string: Optional[str] = None
    media_type: str  # "video", "image", "gif", "carousel"
    formats: List[MediaFormat] = []
    items: List[MediaItem] = []
    original_url: str


class PlatformInfo(BaseModel):
    id: str
    name: str
    icon: str
    badge_color: str
    supported_types: List[str]
    sample_url: str
