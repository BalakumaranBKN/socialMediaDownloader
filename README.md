# OmniGrab - Social Media Media Downloader

A full-stack web application for downloading videos, images, carousels, and GIFs from **Twitter / X**, **Instagram**, **Threads**, **TikTok**, **Reddit**, **YouTube Shorts**, and **Pinterest**.

Built with **Angular 22**, **PrimeNG 22**, and **Python (FastAPI + yt-dlp)**.

---

## 🌟 Features

- **Multi-Platform Support**:
  - **Twitter / X**: Videos, single images, multi-image tweets, and GIFs.
  - **Instagram**: Reels, single posts, multi-photo carousels.
  - **Threads**: Posts with video and high-resolution photos.
  - **TikTok**: HD videos and audio tracks.
  - **Reddit & YouTube Shorts**: Video clips with audio.
  - **Pinterest**: Images and video pins.
- **Smart Link Detection**: Detects the platform in real time as soon as you type or paste a link.
- **Clipboard 1-Click Paste**: Dedicated button to read and fetch straight from your clipboard.
- **Media Preview Player**: Watch videos or browse multi-photo carousels right inside the app before downloading.
- **Multiple Resolutions & Formats**: Select 1080p Full HD, 720p HD, 480p, MP3 Audio, or original image resolution.
- **Direct Stream Downloads**: Bypasses browser inline playback and CORS restrictions using a backend stream proxy.
- **Download History**: Stores your recent downloads in local storage for instant re-access.
- **Modern Dark UI**: Glassmorphism aesthetic built with PrimeNG Aura theme and PrimeIcons.

---

## 🚀 Quick Start

### 1. Launch with One Click
Double-click `start.bat` in the root folder. It will start both the FastAPI backend and the Angular frontend.

### 2. Or Start Manually

#### Backend (Python FastAPI):
```powershell
cd d:\Study\downloader\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Frontend (Angular + PrimeNG):
```powershell
cd d:\Study\downloader\frontend
npm start
```
Frontend Web UI: [http://localhost:4200](http://localhost:4200)

---

## 📁 Project Structure

```
d:\Study\downloader\
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI setup & CORS
│   │   ├── models/schemas.py        # Pydantic schemas
│   │   ├── routers/media.py         # /api/info, /api/download, /api/platforms
│   │   └── services/downloader.py   # yt-dlp & FxTwitter fallback
│   ├── requirements.txt
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── navbar/          # Header with branding & platform pills
│   │   │   │   ├── url-input/       # Hero input bar & clipboard paste
│   │   │   │   ├── media-preview/   # Video player, carousel & format picker
│   │   │   │   ├── history/         # History drawer
│   │   │   │   └── faq/             # Guide on how to copy links
│   │   │   ├── services/            # DownloaderService
│   │   │   ├── models/              # TypeScript interfaces
│   │   │   ├── app.ts / app.html
│   │   │   └── app.config.ts        # PrimeNG 22 Aura setup
│   │   └── styles.scss
│   └── package.json
│
├── start.bat                        # One-click start script
└── README.md
```
