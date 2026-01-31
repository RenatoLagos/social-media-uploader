"""Validador de videos para redes sociales"""

from pathlib import Path
from typing import Optional

from moviepy.editor import VideoFileClip

from src.config.settings import settings
from src.models.video_metadata import VideoMetadata
from src.utils.exceptions import VideoValidationError


class VideoValidator:
    """Validador de videos para subida a redes sociales"""

    SUPPORTED_FORMATS = ['.mp4', '.mov', '.avi', '.webm']
    RECOMMENDED_ASPECT_RATIO = (9, 16)  # Vertical para Shorts/Reels

    def __init__(self):
        self.max_duration = settings.max_video_duration
        self.max_file_size_mb = settings.max_file_size_mb

    def validate(self, video_path: str) -> VideoMetadata:
        """
        Validar video y retornar metadata

        Args:
            video_path: Ruta al archivo de video

        Returns:
            VideoMetadata con informacion del video

        Raises:
            VideoValidationError: Si el video no cumple los requisitos
        """
        path = Path(video_path)

        # Verificar existencia
        if not path.exists():
            raise VideoValidationError(f"El archivo no existe: {video_path}")

        # Verificar formato
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise VideoValidationError(
                f"Formato no soportado: {path.suffix}. "
                f"Formatos validos: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Verificar tamano antes de abrir
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise VideoValidationError(
                f"Tamano de archivo ({file_size_mb:.1f} MB) excede "
                f"el maximo permitido ({self.max_file_size_mb} MB)"
            )

        # Analizar video con moviepy
        try:
            clip = VideoFileClip(str(path))
            duration = clip.duration
            resolution = (clip.w, clip.h)
            clip.close()
        except Exception as e:
            raise VideoValidationError(f"Error al analizar video: {e}")

        # Validar duracion
        if duration > self.max_duration:
            raise VideoValidationError(
                f"Duracion ({duration:.1f}s) excede el maximo "
                f"permitido ({self.max_duration}s) para videos cortos"
            )

        # Crear metadata
        metadata = VideoMetadata(
            path=str(path.absolute()),
            duration=duration,
            resolution=resolution,
            file_size=int(file_size_mb),
            format=path.suffix.lower().replace('.', '')
        )

        # Warnings (no detienen el proceso)
        self._check_warnings(metadata)

        return metadata

    def _check_warnings(self, metadata: VideoMetadata) -> None:
        """Verificar condiciones que generan warnings pero no errores"""
        from src.utils.logger import get_logger
        logger = get_logger()

        # Warning si no es vertical
        if not metadata.is_vertical:
            logger.warning(
                "Video no es vertical",
                resolution=metadata.resolution,
                recommended="9:16 (vertical) para mejor rendimiento en Shorts/Reels"
            )

        # Warning si duracion muy corta
        if metadata.duration < 3:
            logger.warning(
                "Video muy corto",
                duration=metadata.duration,
                recommendation="Videos de al menos 3 segundos tienen mejor engagement"
            )

    @staticmethod
    def validate_quick(video_path: str) -> bool:
        """
        Validacion rapida sin analizar contenido del video

        Args:
            video_path: Ruta al archivo

        Returns:
            True si el archivo parece valido, False si no
        """
        path = Path(video_path)

        if not path.exists():
            return False

        if path.suffix.lower() not in VideoValidator.SUPPORTED_FORMATS:
            return False

        if path.stat().st_size == 0:
            return False

        return True
