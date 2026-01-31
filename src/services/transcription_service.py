"""Servicio de transcripcion de audio usando OpenAI Whisper"""

import tempfile
from pathlib import Path
from typing import Optional

from moviepy.editor import VideoFileClip
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import settings
from src.utils.exceptions import TranscriptionError
from src.utils.logger import get_logger


class TranscriptionService:
    """Servicio para transcribir audio de videos usando OpenAI Whisper"""

    SUPPORTED_LANGUAGES = ['es', 'en', 'pt', 'fr', 'de', 'it']

    def __init__(self, language: str = "es"):
        """
        Inicializar servicio de transcripcion

        Args:
            language: Codigo de idioma para la transcripcion (default: espanol)
        """
        self.logger = get_logger("transcription")
        self.language = language

        if not settings.openai_api_key:
            raise TranscriptionError(
                "OPENAI_API_KEY no configurada. Agregar a archivo .env"
            )

        self.client = OpenAI(api_key=settings.openai_api_key)

    def transcribe(self, video_path: str) -> str:
        """
        Extraer audio y transcribir con Whisper

        Args:
            video_path: Ruta al archivo de video

        Returns:
            Transcripcion en texto

        Raises:
            TranscriptionError: Si hay error en el proceso
        """
        audio_path = None

        try:
            # Extraer audio
            self.logger.info("Extrayendo audio del video", video_path=video_path)
            audio_path = self._extract_audio(video_path)

            # Transcribir con Whisper
            self.logger.info("Enviando audio a Whisper API")
            transcription = self._transcribe_with_whisper(audio_path)

            self.logger.info(
                "Transcripcion completada",
                length=len(transcription),
                preview=transcription[:100] + "..." if len(transcription) > 100 else transcription
            )

            return transcription

        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"Error inesperado en transcripcion: {e}")

        finally:
            # Limpiar archivo temporal
            if audio_path:
                self._cleanup_temp_file(audio_path)

    def _extract_audio(self, video_path: str) -> str:
        """
        Extraer audio del video como archivo temporal

        Args:
            video_path: Ruta al video

        Returns:
            Ruta al archivo de audio temporal
        """
        try:
            clip = VideoFileClip(video_path)

            if clip.audio is None:
                clip.close()
                raise TranscriptionError("El video no tiene audio")

            # Crear archivo temporal
            temp_audio = tempfile.NamedTemporaryFile(
                suffix='.mp3',
                delete=False
            )
            temp_audio.close()

            # Extraer audio
            clip.audio.write_audiofile(
                temp_audio.name,
                logger=None,  # Silenciar logs de moviepy
                verbose=False
            )
            clip.close()

            return temp_audio.name

        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"Error extrayendo audio: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _transcribe_with_whisper(self, audio_path: str) -> str:
        """
        Transcribir audio usando Whisper API con reintentos

        Args:
            audio_path: Ruta al archivo de audio

        Returns:
            Texto transcrito
        """
        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=self.language,
                    response_format="text"
                )

            if not transcript or not transcript.strip():
                raise TranscriptionError("Transcripcion vacia - el audio puede no tener voz")

            return transcript.strip()

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                self.logger.warning("Rate limit alcanzado, reintentando...")
                raise  # Permitir reintento
            raise TranscriptionError(f"Error en Whisper API: {e}")

    def _cleanup_temp_file(self, file_path: str) -> None:
        """Eliminar archivo temporal de forma segura"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                self.logger.debug("Archivo temporal eliminado", path=file_path)
        except Exception as e:
            self.logger.warning("No se pudo eliminar archivo temporal", path=file_path, error=str(e))
