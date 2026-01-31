"""Modelos de datos para el sistema de upload de videos"""

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class VideoMetadata:
    """Metadata de un video procesado"""
    path: str
    duration: float  # segundos
    resolution: Tuple[int, int]  # (width, height)
    file_size: int  # MB
    format: str = "mp4"

    @property
    def is_vertical(self) -> bool:
        """Verificar si el video es vertical (ideal para Shorts/Reels)"""
        width, height = self.resolution
        return height > width

    @property
    def aspect_ratio(self) -> str:
        """Obtener aspect ratio aproximado"""
        width, height = self.resolution
        if height > width:
            return "9:16"  # Vertical
        elif width > height:
            return "16:9"  # Horizontal
        else:
            return "1:1"  # Cuadrado


@dataclass
class PlatformDescriptions:
    """Descripciones optimizadas para cada plataforma"""
    youtube_title: str
    youtube: str
    instagram: str
    tiktok: str


@dataclass
class UploadResult:
    """Resultado de upload a una plataforma"""
    platform: str
    success: bool
    video_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            return f"[{self.platform}] Exito - {self.url}"
        return f"[{self.platform}] Fallo - {self.error}"


@dataclass
class ProcessingResult:
    """Resultado completo del procesamiento de un video"""
    video_path: str
    metadata: Optional[VideoMetadata] = None
    transcription: Optional[str] = None
    descriptions: Optional[PlatformDescriptions] = None
    upload_results: list = field(default_factory=list)

    @property
    def successful_uploads(self) -> int:
        """Numero de uploads exitosos"""
        return sum(1 for r in self.upload_results if r.success)

    @property
    def total_uploads(self) -> int:
        """Total de intentos de upload"""
        return len(self.upload_results)
