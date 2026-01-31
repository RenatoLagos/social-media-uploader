"""Orchestrador principal del sistema de upload de videos"""

from pathlib import Path
from typing import List, Optional

from src.config.settings import settings
from src.models.video_metadata import (
    VideoMetadata,
    PlatformDescriptions,
    UploadResult,
    ProcessingResult
)
from src.services.transcription_service import TranscriptionService
from src.services.description_service import DescriptionService
from src.services.youtube_service import YouTubeService
from src.services.instagram_service import InstagramService
from src.services.tiktok_service import TikTokService
from src.utils.video_validator import VideoValidator
from src.utils.logger import get_logger
from src.utils.exceptions import (
    VideoValidationError,
    TranscriptionError,
    DescriptionGenerationError,
    PlatformUploadError
)


class VideoUploadOrchestrator:
    """
    Orchestrador que coordina todo el proceso de upload de videos:
    1. Validacion del video
    2. Transcripcion del audio
    3. Generacion de descripciones
    4. Upload a plataformas
    """

    def __init__(
        self,
        enable_youtube: Optional[bool] = None,
        enable_instagram: Optional[bool] = None,
        enable_tiktok: Optional[bool] = None
    ):
        """
        Inicializar orchestrador

        Args:
            enable_youtube: Override para habilitar/deshabilitar YouTube
            enable_instagram: Override para habilitar/deshabilitar Instagram
            enable_tiktok: Override para habilitar/deshabilitar TikTok
        """
        self.logger = get_logger("orchestrator")

        # Usar settings si no se proporciona override
        self._enable_youtube = enable_youtube if enable_youtube is not None else settings.enable_youtube
        self._enable_instagram = enable_instagram if enable_instagram is not None else settings.enable_instagram
        self._enable_tiktok = enable_tiktok if enable_tiktok is not None else settings.enable_tiktok

        # Inicializar servicios
        self.validator = VideoValidator()
        self.transcription_service = TranscriptionService()
        self.description_service = DescriptionService()

        # Inicializar servicios de plataforma solo si estan habilitados
        self.youtube_service = YouTubeService() if self._enable_youtube else None
        self.instagram_service = InstagramService() if self._enable_instagram else None
        self.tiktok_service = TikTokService() if self._enable_tiktok else None

    def process(
        self,
        video_path: str,
        custom_title: Optional[str] = None
    ) -> ProcessingResult:
        """
        Procesar y subir video a todas las plataformas habilitadas

        Args:
            video_path: Ruta al archivo de video
            custom_title: Titulo personalizado (opcional)

        Returns:
            ProcessingResult con resultados de todo el proceso
        """
        result = ProcessingResult(video_path=video_path)

        try:
            # 1. Validar video
            self.logger.info("Paso 1/4: Validando video", path=video_path)
            metadata = self._validate_video(video_path)
            result.metadata = metadata

            # 2. Transcribir audio
            self.logger.info("Paso 2/4: Transcribiendo audio")
            transcription = self._transcribe(video_path)
            result.transcription = transcription

            # 3. Generar descripciones
            self.logger.info("Paso 3/4: Generando descripciones optimizadas")
            descriptions = self._generate_descriptions(transcription)
            result.descriptions = descriptions

            # 4. Subir a plataformas
            self.logger.info("Paso 4/4: Subiendo a plataformas")
            upload_results = self._upload_to_platforms(
                video_path=video_path,
                descriptions=descriptions,
                title=custom_title or Path(video_path).stem
            )
            result.upload_results = upload_results

            # Log resumen
            self.logger.info(
                "Procesamiento completado",
                successful=result.successful_uploads,
                total=result.total_uploads
            )

            return result

        except Exception as e:
            self.logger.error("Error en procesamiento", error=str(e))
            raise

    def _validate_video(self, video_path: str) -> VideoMetadata:
        """Validar video y retornar metadata"""
        try:
            return self.validator.validate(video_path)
        except VideoValidationError as e:
            self.logger.error("Validacion fallida", error=str(e))
            raise

    def _transcribe(self, video_path: str) -> str:
        """
        Transcribir audio del video.

        Primero busca archivos .txt o .srt con el mismo nombre del video.
        Si existe, usa su contenido y se salta la transcripcion con Whisper.
        """
        video_file = Path(video_path)

        # Buscar archivo de transcripcion existente (.txt o .srt)
        txt_file = video_file.with_suffix('.txt')
        srt_file = video_file.with_suffix('.srt')

        # Prioridad: .txt > .srt
        if txt_file.exists():
            self.logger.info("Archivo .txt encontrado, usando como transcripcion", path=str(txt_file))
            transcription = txt_file.read_text(encoding='utf-8').strip()
            if transcription:
                return transcription
            self.logger.warning("Archivo .txt vacio, continuando con Whisper")

        if srt_file.exists():
            self.logger.info("Archivo .srt encontrado, usando como transcripcion", path=str(srt_file))
            transcription = self._parse_srt(srt_file)
            if transcription:
                return transcription
            self.logger.warning("Archivo .srt vacio, continuando con Whisper")

        # No hay archivo de transcripcion, usar Whisper
        try:
            transcription = self.transcription_service.transcribe(video_path)

            if not transcription.strip():
                self.logger.warning("Transcripcion vacia, usando fallback")
                return "Video sin audio o sin voz detectada."

            return transcription

        except TranscriptionError as e:
            self.logger.error("Transcripcion fallida", error=str(e))
            raise

    def _parse_srt(self, srt_path: Path) -> str:
        """
        Parsear archivo SRT y extraer solo el texto (sin timestamps).

        Args:
            srt_path: Ruta al archivo .srt

        Returns:
            Texto extraido del SRT
        """
        import re

        content = srt_path.read_text(encoding='utf-8')

        # Remover numeros de secuencia (lineas que solo tienen digitos)
        # Remover timestamps (formato: 00:00:00,000 --> 00:00:00,000)
        lines = content.split('\n')
        text_lines = []

        timestamp_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}')

        for line in lines:
            line = line.strip()
            # Saltar lineas vacias
            if not line:
                continue
            # Saltar numeros de secuencia
            if line.isdigit():
                continue
            # Saltar timestamps
            if timestamp_pattern.match(line):
                continue
            # Es texto del subtitulo
            text_lines.append(line)

        return ' '.join(text_lines)

    def _generate_descriptions(self, transcription: str) -> PlatformDescriptions:
        """Generar descripciones para todas las plataformas"""
        try:
            return self.description_service.generate_all(transcription)
        except DescriptionGenerationError as e:
            self.logger.error("Generacion de descripciones fallida", error=str(e))
            raise

    def _upload_to_platforms(
        self,
        video_path: str,
        descriptions: PlatformDescriptions,
        title: str
    ) -> List[UploadResult]:
        """Subir video a todas las plataformas habilitadas"""
        results = []

        # YouTube
        if self.youtube_service:
            result = self._upload_youtube(video_path, title, descriptions.youtube)
            results.append(result)

        # Instagram
        if self.instagram_service:
            result = self._upload_instagram(
                video_path,
                descriptions.instagram
            )
            results.append(result)

        # TikTok
        if self.tiktok_service:
            result = self._upload_tiktok(video_path, descriptions.tiktok)
            results.append(result)

        return results

    def _upload_youtube(
        self,
        video_path: str,
        title: str,
        description: str
    ) -> UploadResult:
        """Subir a YouTube Shorts"""
        try:
            result = self.youtube_service.upload(
                video_path=video_path,
                title=title,
                description=description
            )
            return UploadResult(
                platform="YouTube",
                success=True,
                video_id=result['video_id'],
                url=result['url']
            )
        except (PlatformUploadError, Exception) as e:
            self.logger.error("Upload a YouTube fallido", error=str(e))
            return UploadResult(
                platform="YouTube",
                success=False,
                error=str(e)
            )

    def _upload_instagram(
        self,
        video_path: str,
        caption: str
    ) -> UploadResult:
        """Subir a Instagram Reels (usando instagrapi con archivo local)"""
        try:
            result = self.instagram_service.upload(
                video_path=video_path,
                caption=caption
            )
            return UploadResult(
                platform="Instagram",
                success=True,
                video_id=result['media_id'],
                url=result['url']
            )
        except (PlatformUploadError, Exception) as e:
            self.logger.error("Upload a Instagram fallido", error=str(e))
            return UploadResult(
                platform="Instagram",
                success=False,
                error=str(e)
            )

    def _upload_tiktok(
        self,
        video_path: str,
        description: str
    ) -> UploadResult:
        """Subir a TikTok"""
        try:
            result = self.tiktok_service.upload(
                video_path=video_path,
                description=description
            )
            return UploadResult(
                platform="TikTok",
                success=True,
                video_id=result.get('video_id'),
                url=result.get('url')
            )
        except (PlatformUploadError, Exception) as e:
            self.logger.error("Upload a TikTok fallido", error=str(e))
            return UploadResult(
                platform="TikTok",
                success=False,
                error=str(e)
            )

    def get_enabled_platforms(self) -> List[str]:
        """Obtener lista de plataformas habilitadas"""
        platforms = []
        if self._enable_youtube:
            platforms.append("YouTube")
        if self._enable_instagram:
            platforms.append("Instagram")
        if self._enable_tiktok:
            platforms.append("TikTok")
        return platforms

    def check_configuration(self) -> dict:
        """
        Verificar configuracion de todas las plataformas

        Returns:
            Dict con estado de configuracion por plataforma
        """
        status = {}

        # OpenAI
        status['openai'] = bool(settings.openai_api_key)

        # YouTube
        if self.youtube_service:
            status['youtube'] = self.youtube_service.is_configured()
        else:
            status['youtube'] = False

        # Instagram
        if self.instagram_service:
            status['instagram'] = self.instagram_service.is_configured()
        else:
            status['instagram'] = False

        # TikTok
        if self.tiktok_service:
            status['tiktok'] = self.tiktok_service.is_configured()
        else:
            status['tiktok'] = False

        return status
