from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuracion centralizada de la aplicacion"""

    # OpenAI
    openai_api_key: str = ""

    # YouTube
    youtube_client_secret_file: str = "credentials/youtube_client_secret.json"
    youtube_token_file: str = "credentials/tokens/youtube_token.json"

    # Instagram (instagrapi)
    instagram_username: Optional[str] = None
    instagram_password: Optional[str] = None

    # TikTok
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    tiktok_access_token: Optional[str] = None

    # App config
    log_level: str = "INFO"
    log_file: str = "logs/upload.log"
    max_video_duration: int = 120
    max_file_size_mb: int = 500

    # Feature flags
    enable_youtube: bool = True
    enable_instagram: bool = True
    enable_tiktok: bool = False

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


def get_settings() -> Settings:
    """Obtener instancia de configuracion"""
    return Settings()


settings = get_settings()
