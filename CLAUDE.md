# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Social Media Video Uploader - Automates uploading short-form videos to YouTube Shorts, Instagram Reels, and TikTok with AI-powered transcription (OpenAI Whisper) and platform-optimized descriptions (GPT-4).

## Commands

### Run the uploader
```bash
# Activate virtual environment first
.\venv\Scripts\activate

# Basic usage
python upload.py VIDEO_PATH

# With options
python upload.py video.mp4 --title "Custom Title" --only-youtube
python upload.py video.mp4 --skip-instagram --verbose
```

### Setup & Configuration
```bash
# Install dependencies
pip install -r requirements.txt

# Authenticate YouTube (runs OAuth flow)
python scripts/authenticate_youtube.py

# Verify API configuration
python scripts/test_apis.py
```

### Run tests
```bash
pytest
pytest tests/ -v
```

## Architecture

### Processing Pipeline
The `VideoUploadOrchestrator` (src/main.py) coordinates a 4-step pipeline:
1. **Validation** - VideoValidator checks format (MP4), duration (max 60s), and file size (max 500MB)
2. **Transcription** - TranscriptionService extracts audio via moviepy, sends to Whisper API
3. **Description Generation** - DescriptionService calls GPT-4 with platform-specific prompts
4. **Upload** - Platform services upload with generated descriptions; failures don't block other platforms

### Service Pattern
Each platform has a dedicated service class in `src/services/`:
- `YouTubeService` - Google OAuth 2.0, YouTube Data API v3
- `InstagramService` - Meta Graph API (requires video at public URL)
- `TikTokService` - TikTok Content Posting API (requires approved app)

Services implement `upload()` and `is_configured()` methods. All API calls use `tenacity` for retry with exponential backoff.

### Configuration
- Settings loaded via pydantic-settings from `.env` file (src/config/settings.py)
- Credentials stored in `credentials/` directory (gitignored)
- YouTube OAuth tokens stored in `credentials/tokens/`

## Key Constraints

- **Instagram**: Uses instagrapi (unofficial library) - uploads local files directly with username/password
- **TikTok**: Requires approved developer app which may take weeks
- **Video format**: MP4 only, max 120 seconds, max 500MB (configurable in .env)
- **Language**: Transcription defaults to Spanish ("es"); descriptions generated in Spanish

## Claude Code Execution Notes

**IMPORTANTE:** Al ejecutar comandos en Windows desde Claude Code (que usa bash internamente):

1. **NO usar** `.\venv\Scripts\activate` - no funciona en bash
2. **NO usar** `cmd /c` - causa problemas de encoding
3. **USAR** la ruta completa al Python del venv con forward slashes:
   ```bash
   PYTHONIOENCODING=utf-8 C:/Users/Admin/Projects/upload_to_socialmedia/venv/Scripts/python.exe upload.py "VIDEO_PATH"
   ```

4. **SIEMPRE** incluir `PYTHONIOENCODING=utf-8` para evitar errores de Unicode con la librería Rich en Windows
