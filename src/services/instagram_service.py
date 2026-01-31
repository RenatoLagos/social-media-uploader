"""Servicio de upload a Instagram Reels usando instagrapi"""

from pathlib import Path
from typing import Dict, Optional

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError

from src.config.settings import settings
from src.utils.exceptions import PlatformUploadError, AuthenticationError
from src.utils.logger import get_logger


class InstagramService:
    """
    Servicio para subir videos a Instagram Reels usando instagrapi

    Ventajas sobre Graph API:
    - Sube archivos locales directamente (sin necesidad de URL publica)
    - Configuracion simple (solo usuario y contraseña)
    - Soporte para thumbnail personalizado y ubicacion
    """

    SESSION_FILE = Path("credentials/instagram_session.json")

    def __init__(self):
        self.logger = get_logger("instagram")
        self.client: Optional[Client] = None
        self.username = settings.instagram_username
        self.password = settings.instagram_password

    def _validate_config(self) -> None:
        """Validar configuracion necesaria"""
        if not self.username:
            raise AuthenticationError(
                "Instagram",
                "INSTAGRAM_USERNAME no configurado en .env"
            )

        if not self.password:
            raise AuthenticationError(
                "Instagram",
                "INSTAGRAM_PASSWORD no configurado en .env"
            )

    def _login(self) -> Client:
        """
        Iniciar sesion en Instagram

        Intenta reusar sesion guardada, si no existe o expiro, hace login nuevo.
        """
        self._validate_config()

        client = Client()

        # Intentar cargar sesion existente
        if self.SESSION_FILE.exists():
            try:
                client.load_settings(self.SESSION_FILE)
                client.login(self.username, self.password)
                self.logger.debug("Sesion de Instagram restaurada")
                return client
            except LoginRequired:
                self.logger.debug("Sesion expirada, haciendo login nuevo")
            except Exception as e:
                self.logger.debug(f"Error cargando sesion: {e}")

        # Login nuevo
        try:
            client.login(self.username, self.password)

            # Guardar sesion para futuros usos
            self.SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            client.dump_settings(self.SESSION_FILE)

            self.logger.info("Login exitoso en Instagram")
            return client

        except Exception as e:
            raise AuthenticationError("Instagram", f"Error de login: {e}")

    def upload(
        self,
        video_path: str,
        caption: str,
        thumbnail_path: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Subir video a Instagram Reels

        Args:
            video_path: Ruta al archivo de video local
            caption: Descripcion/caption del reel (soporta hashtags, menciones, emojis)
            thumbnail_path: Ruta opcional a imagen de portada
            location: Ubicacion opcional (nombre del lugar)

        Returns:
            Dict con media_id, code y url

        Raises:
            PlatformUploadError: Si falla el upload
        """
        video_file = Path(video_path)

        if not video_file.exists():
            raise PlatformUploadError("Instagram", f"Video no encontrado: {video_path}")

        try:
            self.logger.info(
                "Iniciando upload a Instagram Reels",
                video=video_file.name
            )

            client = self._login()

            # Preparar thumbnail si se proporciono
            thumbnail = None
            if thumbnail_path:
                thumb_file = Path(thumbnail_path)
                if thumb_file.exists():
                    thumbnail = str(thumb_file)

            # Subir reel
            media = client.clip_upload(
                path=str(video_file),
                caption=caption,
                thumbnail=thumbnail
            )

            url = f"https://instagram.com/reel/{media.code}"

            self.logger.info(
                "Upload a Instagram exitoso",
                media_id=media.id,
                code=media.code,
                url=url
            )

            return {
                'media_id': media.id,
                'code': media.code,
                'url': url,
                'platform': 'Instagram'
            }

        except (AuthenticationError, PlatformUploadError):
            raise
        except ClientError as e:
            raise PlatformUploadError("Instagram", f"Error de cliente: {e}")
        except Exception as e:
            raise PlatformUploadError("Instagram", str(e))

    def is_configured(self) -> bool:
        """Verificar si el servicio esta configurado"""
        return bool(self.username and self.password)

    def test_connection(self) -> Dict[str, str]:
        """
        Probar conexion a Instagram

        Returns:
            Dict con info del usuario autenticado
        """
        client = self._login()
        user_info = client.account_info()

        return {
            'username': user_info.username,
            'full_name': user_info.full_name
        }
