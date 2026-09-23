import os
import re
import tempfile
import subprocess
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
import requests
import yt_dlp

import io
import zipfile
from PIL import Image

from ..models.schemas import UrlRequest, MediaInfoResponse, PlatformInfo, BatchDownloadRequest
from ..services.downloader import extract_media_info, PLATFORMS_META, FFMPEG_PATH

router = APIRouter(prefix="/api", tags=["Media"])


@router.get("/platforms", response_model=list[PlatformInfo])
def get_supported_platforms():
    platforms = []
    for key, data in PLATFORMS_META.items():
        if key == "other":
            continue
        platforms.append(PlatformInfo(
            id=data["id"],
            name=data["name"],
            icon=data["icon"],
            badge_color=data["badge_color"],
            supported_types=data["supported_types"],
            sample_url=data["sample_url"]
        ))
    return platforms


@router.post("/info", response_model=MediaInfoResponse)
def get_media_info(payload: UrlRequest):
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        media_info = extract_media_info(url)
        return media_info
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract media: {str(e)}")


@router.get("/download")
def download_stream(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="Direct media URL"),
    filename: str = Query("media", description="Target filename"),
    ext: str = Query("mp4", description="File extension"),
    mode: str = Query("normal", description="'normal', 'mute', or 'music'")
):
    """
    Streams media content directly to the browser with Content-Disposition attachment.
    Supports mode='normal' (lossless stream proxy), mode='mute' (silent video without audio),
    and mode='music' (extracted MP3 audio track).
    """
    # Sanitize base filename
    raw_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', filename).strip('_') or "media"

    url_lower = url.lower()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    if any(k in url_lower for k in ['instagram', 'cdninstagram', 'fbcdn']):
        headers['Referer'] = 'https://www.instagram.com/'
    elif any(k in url_lower for k in ['twimg', 'twitter', 'x.com']):
        headers['Referer'] = 'https://twitter.com/'

    def cleanup_temp_dir(dir_path: str):
        try:
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    try:
                        os.remove(os.path.join(dir_path, f))
                    except Exception:
                        pass
                os.rmdir(dir_path)
        except Exception:
            pass

    # Processing with FFmpeg if mute or music is requested
    if mode in ["mute", "music"]:
        if not FFMPEG_PATH:
            raise HTTPException(status_code=500, detail="FFmpeg is not available on this server.")

        temp_dir = tempfile.mkdtemp(prefix=f"bkn_{mode}_")
        temp_input = os.path.join(temp_dir, f"source_input.{ext}")

        try:
            with requests.get(url, headers=headers, stream=True, timeout=40) as req:
                req.raise_for_status()
                with open(temp_input, "wb") as f_out:
                    for chunk in req.iter_content(chunk_size=1024 * 128):
                        if chunk:
                            f_out.write(chunk)
        except Exception as e:
            cleanup_temp_dir(temp_dir)
            raise HTTPException(status_code=502, detail=f"Failed to fetch source stream: {str(e)}")

        if mode == "mute":
            out_filename = f"{raw_name}_mute.mp4"
            out_path = os.path.join(temp_dir, out_filename)
            # Remove audio: -an -c:v copy
            cmd = [FFMPEG_PATH, "-y", "-i", temp_input, "-an", "-c:v", "copy", out_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0 or not os.path.exists(out_path):
                cleanup_temp_dir(temp_dir)
                raise HTTPException(status_code=500, detail=f"Failed to mute video: {res.stderr[:200]}")

            background_tasks.add_task(cleanup_temp_dir, temp_dir)
            return FileResponse(
                path=out_path,
                filename=out_filename,
                media_type="video/mp4"
            )

        elif mode == "music":
            out_filename = f"{raw_name}_music.mp3"
            out_path = os.path.join(temp_dir, out_filename)
            # Extract audio to MP3: -vn -c:a libmp3lame -b:a 192k
            cmd = [FFMPEG_PATH, "-y", "-i", temp_input, "-vn", "-c:a", "libmp3lame", "-b:a", "192k", out_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0 or not os.path.exists(out_path):
                cleanup_temp_dir(temp_dir)
                err_text = res.stderr or ""
                if "does not contain any stream" in err_text or "matches no streams" in err_text:
                    raise HTTPException(status_code=400, detail="This video does not contain an audio track to extract.")
                raise HTTPException(status_code=500, detail=f"Failed to extract music: {err_text[:200]}")

            background_tasks.add_task(cleanup_temp_dir, temp_dir)
            return FileResponse(
                path=out_path,
                filename=out_filename,
                media_type="audio/mpeg"
            )

    # Standard stream proxy (mode == 'normal')
    safe_name = f"{raw_name}.{ext}"
    try:
        req = requests.get(url, headers=headers, stream=True, timeout=30)
        req.raise_for_status()

        content_type = req.headers.get("Content-Type", "application/octet-stream")
        content_length = req.headers.get("Content-Length")

        response_headers = {
            "Content-Disposition": f'attachment; filename="{safe_name}"; filename*=UTF-8\'\'{quote(safe_name)}'
        }
        if content_length:
            response_headers["Content-Length"] = content_length

        def iterfile():
            for chunk in req.iter_content(chunk_size=1024 * 64):
                if chunk:
                    yield chunk

        return StreamingResponse(
            iterfile(),
            media_type=content_type,
            headers=response_headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream download: {str(e)}")


def process_image_resolution(image_bytes: bytes, resolution: str) -> bytes:
    if resolution == "original":
        return image_bytes
    try:
        max_dim = 1080
        if resolution == "720p":
            max_dim = 720
        elif resolution == "360p":
            max_dim = 360

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
        return buf.getvalue()
    except Exception as e:
        print(f"Image resize error: {e}")
        return image_bytes


@router.get("/download-image")
def download_image_stream(
    url: str = Query(..., description="Direct media URL"),
    filename: str = Query("photo", description="Target filename"),
    resolution: str = Query("1080p", description="Image resolution: 1080p, 720p, 360p, original"),
    ext: str = Query("jpg", description="File extension")
):
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    target_name = f"{safe_name}_{resolution}.{ext}" if resolution != "original" else f"{safe_name}.{ext}"

    url_lower = url.lower()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    if any(k in url_lower for k in ['instagram', 'cdninstagram', 'fbcdn']):
        headers['Referer'] = 'https://www.instagram.com/'
    elif any(k in url_lower for k in ['twimg', 'twitter', 'x.com']):
        headers['Referer'] = 'https://twitter.com/'

    try:
        req = requests.get(url, headers=headers, timeout=30)
        req.raise_for_status()

        img_bytes = process_image_resolution(req.content, resolution)
        response_headers = {
            "Content-Disposition": f'attachment; filename="{target_name}"; filename*=UTF-8\'\'{quote(target_name)}',
            "Content-Length": str(len(img_bytes))
        }

        return StreamingResponse(
            io.BytesIO(img_bytes),
            media_type="image/jpeg" if ext in ["jpg", "jpeg"] else "application/octet-stream",
            headers=response_headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream image: {str(e)}")


@router.post("/download-zip")
def download_images_zip(payload: BatchDownloadRequest):
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items selected for download")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(payload.items):
            url_lower = item.url.lower()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            }
            if any(k in url_lower for k in ['instagram', 'cdninstagram', 'fbcdn']):
                headers['Referer'] = 'https://www.instagram.com/'
            elif any(k in url_lower for k in ['twimg', 'twitter', 'x.com']):
                headers['Referer'] = 'https://twitter.com/'

            try:
                resp = requests.get(item.url, headers=headers, timeout=20)
                if resp.status_code == 200:
                    processed_bytes = process_image_resolution(resp.content, payload.resolution)
                    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', item.filename)
                    entry_name = f"{safe_name}_{payload.resolution}.{item.ext}"
                    zf.writestr(entry_name, processed_bytes)
            except Exception as e:
                print(f"Failed to download item {item.url}: {e}")

    zip_bytes = zip_buffer.getvalue()
    zip_name = payload.zip_name or "downloaded_album.zip"
    if not zip_name.endswith(".zip"):
        zip_name += ".zip"

    response_headers = {
        "Content-Disposition": f'attachment; filename="{zip_name}"; filename*=UTF-8\'\'{quote(zip_name)}',
        "Content-Length": str(len(zip_bytes))
    }

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers=response_headers
    )


@router.get("/download-ytdl")
def download_via_ytdl(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="Post/video URL"),
    format_id: str = Query("best", description="yt-dlp format id or best"),
    filename: str = Query("video", description="Filename")
):
    """
    Uses yt-dlp to download and merge streams (audio+video) if needed,
    then delivers the completed file and cleans up afterwards.
    """
    temp_dir = tempfile.mkdtemp(prefix="social_dl_")
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    output_template = os.path.join(temp_dir, f"{safe_name}.%(ext)s")

    ydl_opts = {
        'format': f'{format_id}+bestaudio/best' if format_id != "best" else 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }
    }

    def cleanup(dir_path: str):
        try:
            for f in os.listdir(dir_path):
                os.remove(os.path.join(dir_path, f))
            os.rmdir(dir_path)
        except Exception:
            pass

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        downloaded_files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)]
        if not downloaded_files:
            cleanup(temp_dir)
            raise HTTPException(status_code=500, detail="Downloaded file not found")

        target_file = downloaded_files[0]
        actual_name = os.path.basename(target_file)

        background_tasks.add_task(cleanup, temp_dir)
        return FileResponse(
            path=target_file,
            filename=actual_name,
            media_type="application/octet-stream"
        )
    except Exception as e:
        cleanup(temp_dir)
        raise HTTPException(status_code=500, detail=f"yt-dlp download failed: {str(e)}")
