# Social Media Video Uploader

Automation system for uploading short videos to **YouTube Shorts**, **Instagram Reels**, and **TikTok** with AI-powered transcription and descriptions.

## Features

- Automatic audio transcription with **OpenAI Whisper**
- Platform-optimized description generation with **GPT-4**
- Automatic upload to multiple platforms
- Intuitive CLI with progress indicators
- Structured logging for debugging
- Robust error handling (if one platform fails, continues with others)

## Requirements

- Python 3.11+
- OpenAI account with API key
- YouTube credentials (Google Cloud)
- Instagram professional account (optional)
- Approved TikTok app (optional)

## Installation

### 1. Clone and setup environment

```bash
git clone https://github.com/RenatoLagos/social-media-uploader.git
cd social-media-uploader

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
```

## API Configuration

### OpenAI (Required)

1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env`:
   ```
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
   ```

### YouTube (Required for YouTube Shorts)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services > Credentials
   - Create Credentials > OAuth client ID
   - Application type: **Desktop app**
   - Download JSON
5. Save the file as `credentials/youtube_client_secret.json`
6. Run initial authentication:
   ```bash
   python scripts/authenticate_youtube.py
   ```
   A browser window will open for authorization.

### Instagram (Optional)

Uses `instagrapi` library for direct uploads with username/password.

1. Add to `.env`:
   ```
   INSTAGRAM_USERNAME=your_username
   INSTAGRAM_PASSWORD=your_password
   ENABLE_INSTAGRAM=true
   ```

**Note**: This uses an unofficial library. Use at your own risk.

### TikTok (Optional - Requires Approval)

TikTok API requires app approval which can take weeks.

1. Register at [TikTok for Developers](https://developers.tiktok.com/)
2. Create app with Content Posting API
3. Wait for approval
4. Once approved, add to `.env`:
   ```
   TIKTOK_CLIENT_KEY=awxxxxxxxxxx
   TIKTOK_CLIENT_SECRET=xxxxxxxxxxxx
   TIKTOK_ACCESS_TOKEN=act.xxxxxxxxxx
   ENABLE_TIKTOK=true
   ```

## Usage

### Basic usage

```bash
python upload.py /path/to/video.mp4
```

### With options

```bash
# With custom title
python upload.py video.mp4 --title "My awesome video"

# YouTube only
python upload.py video.mp4 --only-youtube

# Skip Instagram
python upload.py video.mp4 --skip-instagram

# Check configuration
python upload.py video.mp4 --check-config

# Verbose mode
python upload.py video.mp4 --verbose
```

### Available options

| Option | Description |
|--------|-------------|
| `--title, -t` | Custom title for the video |
| `--only-youtube` | Upload to YouTube only |
| `--only-instagram` | Upload to Instagram only |
| `--only-tiktok` | Upload to TikTok only |
| `--skip-youtube` | Skip YouTube |
| `--skip-instagram` | Skip Instagram |
| `--skip-tiktok` | Skip TikTok |
| `--check-config` | Verify configuration without uploading |
| `--verbose, -v` | Show detailed logs |

## Verify Configuration

```bash
python scripts/test_apis.py
```

This will verify all APIs are correctly configured.

## Project Structure

```
social-media-uploader/
├── src/
│   ├── main.py                 # Main orchestrator
│   ├── config/
│   │   └── settings.py         # Configuration
│   ├── services/
│   │   ├── transcription_service.py   # OpenAI Whisper
│   │   ├── description_service.py     # GPT-4
│   │   ├── youtube_service.py         # YouTube API
│   │   ├── instagram_service.py       # Instagram API
│   │   └── tiktok_service.py          # TikTok API
│   ├── utils/
│   │   ├── video_validator.py   # Video validation
│   │   ├── logger.py            # Logging
│   │   └── exceptions.py        # Exceptions
│   └── models/
│       └── video_metadata.py    # Data models
├── scripts/
│   ├── authenticate_youtube.py  # YouTube OAuth setup
│   └── test_apis.py             # Verify configuration
├── credentials/                  # Credentials (not in git)
├── logs/                         # Execution logs
├── upload.py                     # Main CLI
├── requirements.txt
├── .env                          # Environment variables (not in git)
└── .env.example
```

## Limitations

- **Format**: MP4 videos only
- **Duration**: Maximum 120 seconds (configurable)
- **Size**: Maximum 500 MB (configurable)
- **TikTok**: Requires approved app

## Processing Flow

1. **Validation**: Checks video format, duration, and size
2. **Transcription**: Extracts audio and transcribes with Whisper
3. **Descriptions**: GPT-4 generates optimized descriptions for each platform
4. **Upload**: Uploads video to each enabled platform

If one platform fails, the process continues with the others.

## Troubleshooting

### "OPENAI_API_KEY not configured"
Make sure you have the `.env` file with the correct API key.

### "Credentials file not found" (YouTube)
Download the OAuth JSON file from Google Cloud Console and save it to `credentials/youtube_client_secret.json`.

### "Corrupt token" (YouTube)
Delete `credentials/tokens/youtube_token.json` and run `python scripts/authenticate_youtube.py` again.

### Rate limits
The system has automatic retries with exponential backoff. If it persists, wait a few minutes before retrying.

## Estimated Costs

- **OpenAI Whisper**: ~$0.006 per minute of audio
- **GPT-4**: ~$0.03 per 1K tokens (approx. $0.02-0.05 per video)
- **YouTube/Instagram/TikTok**: Free

For a 60-second video, the approximate cost is **$0.03-0.08 USD**.

## License

MIT

## Contributing

Pull requests are welcome. For major changes, please open an issue first.
