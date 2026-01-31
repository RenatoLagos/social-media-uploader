"""Excepciones personalizadas para el sistema de upload de videos"""


class VideoValidationError(Exception):
    """Error en validacion de video (formato, duracion, tamano, etc.)"""
    pass


class TranscriptionError(Exception):
    """Error en transcripcion de audio con Whisper"""
    pass


class DescriptionGenerationError(Exception):
    """Error generando descripciones con GPT-4"""
    pass


class PlatformUploadError(Exception):
    """Error subiendo video a una plataforma (YouTube, Instagram, TikTok)"""

    def __init__(self, platform: str, message: str):
        self.platform = platform
        self.message = message
        super().__init__(f"[{platform}] {message}")


class AuthenticationError(Exception):
    """Error de autenticacion con API externa"""

    def __init__(self, platform: str, message: str):
        self.platform = platform
        self.message = message
        super().__init__(f"[{platform}] Error de autenticacion: {message}")
