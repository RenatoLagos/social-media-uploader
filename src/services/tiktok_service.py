"""Servicio de upload a TikTok"""

from pathlib import Path
from typing import Dict, Optional

import requests

from src.config.settings import settings
from src.utils.exceptions import PlatformUploadError, AuthenticationError
from src.utils.logger import get_logger


class TikTokService:
    """
    Servicio para subir videos a TikTok

    NOTA IMPORTANTE: La API de TikTok requiere aprobacion de app que
    puede tomar varias semanas. Este servicio esta preparado para
    cuando la app sea aprobada.

    Documentacion: https://developers.tiktok.com/doc/content-posting-api-get-started
    """

    # URLs de la API
    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"

    # Niveles de privacidad
    PRIVACY_LEVELS = {
        'public': 'PUBLIC_TO_EVERYONE',
        'friends': 'MUTUAL_FOLLOW_FRIENDS',
        'private': 'SELF_ONLY'
    }

    def __init__(self):
        self.logger = get_logger("tiktok")
        self.client_key = settings.tiktok_client_key
        self.client_secret = settings.tiktok_client_secret
        self.access_token = settings.tiktok_access_token

    def _validate_config(self) -> None:
        """Validar que TikTok esta habilitado y configurado"""
        if not settings.enable_tiktok:
            raise PlatformUploadError(
                "TikTok",
                "TikTok esta deshabilitado. Configurar ENABLE_TIKTOK=true en .env"
            )

        if not self.access_token:
            raise AuthenticationError(
                "TikTok",
                "TIKTOK_ACCESS_TOKEN no configurado. "
                "Requiere app aprobada por TikTok. "
                "Ver: https://developers.tiktok.com/doc/login-kit-web"
            )

    def upload(
        self,
        video_path: str,
        description: str,
        privacy: str = 'public',
        disable_duet: bool = False,
        disable_stitch: bool = False,
        disable_comment: bool = False
    ) -> Dict[str, str]:
        """
        Subir video a TikTok

        Args:
            video_path: Ruta al archivo de video
            description: Descripcion del video (max 2200 chars)
            privacy: Nivel de privacidad (public, friends, private)
            disable_duet: Deshabilitar duets
            disable_stitch: Deshabilitar stitch
            disable_comment: Deshabilitar comentarios

        Returns:
            Dict con video_id y url

        Raises:
            PlatformUploadError: Si falla el upload
        """
        self._validate_config()

        # Validar archivo
        path = Path(video_path)
        if not path.exists():
            raise PlatformUploadError("TikTok", f"Archivo no existe: {video_path}")

        try:
            self.logger.info(
                "Iniciando upload a TikTok",
                privacy=privacy
            )

            # Paso 1: Inicializar upload
            upload_url = self._initialize_upload(
                description=description,
                privacy=privacy,
                disable_duet=disable_duet,
                disable_stitch=disable_stitch,
                disable_comment=disable_comment
            )

            # Paso 2: Subir el video
            self._upload_video(upload_url, video_path)

            # Paso 3: Verificar publicacion
            result = self._verify_publish()

            self.logger.info(
                "Upload a TikTok exitoso",
                video_id=result.get('video_id')
            )

            return result

        except (PlatformUploadError, AuthenticationError):
            raise
        except Exception as e:
            raise PlatformUploadError("TikTok", str(e))

    def _initialize_upload(
        self,
        description: str,
        privacy: str,
        disable_duet: bool,
        disable_stitch: bool,
        disable_comment: bool
    ) -> str:
        """
        Inicializar sesion de upload

        Returns:
            URL para subir el video
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        privacy_level = self.PRIVACY_LEVELS.get(privacy, self.PRIVACY_LEVELS['public'])

        data = {
            'post_info': {
                'title': description[:150],  # TikTok prefiere titulos cortos
                'privacy_level': privacy_level,
                'disable_duet': disable_duet,
                'disable_stitch': disable_stitch,
                'disable_comment': disable_comment
            },
            'source_info': {
                'source': 'FILE_UPLOAD'
            }
        }

        response = requests.post(
            self.UPLOAD_URL,
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            error = response.json().get('error', {})
            raise PlatformUploadError(
                "TikTok",
                f"Error inicializando upload: {error.get('message', response.text)}"
            )

        result = response.json().get('data', {})
        upload_url = result.get('upload_url')

        if not upload_url:
            raise PlatformUploadError("TikTok", "No se obtuvo URL de upload")

        return upload_url

    def _upload_video(self, upload_url: str, video_path: str) -> None:
        """Subir el archivo de video"""
        headers = {
            'Content-Type': 'video/mp4'
        }

        with open(video_path, 'rb') as video_file:
            response = requests.put(
                upload_url,
                headers=headers,
                data=video_file
            )

        if response.status_code not in [200, 201]:
            raise PlatformUploadError(
                "TikTok",
                f"Error subiendo video: {response.text}"
            )

    def _verify_publish(self) -> Dict[str, str]:
        """
        Verificar que el video fue publicado

        NOTA: La API real requiere polling del estado.
        Esta es una implementacion simplificada.
        """
        # En implementacion real, usar endpoint de status
        return {
            'video_id': 'pending',
            'url': 'https://tiktok.com',
            'platform': 'TikTok',
            'status': 'Video en procesamiento por TikTok'
        }

    def is_configured(self) -> bool:
        """Verificar si el servicio esta configurado"""
        return bool(
            settings.enable_tiktok and
            self.client_key and
            self.access_token
        )

    def get_auth_url(self, redirect_uri: str, state: str = "state") -> str:
        """
        Obtener URL de autorizacion para OAuth2

        Args:
            redirect_uri: URI de redireccion configurada en TikTok Developer
            state: Estado para CSRF protection

        Returns:
            URL de autorizacion
        """
        if not self.client_key:
            raise AuthenticationError(
                "TikTok",
                "TIKTOK_CLIENT_KEY no configurado"
            )

        params = {
            'client_key': self.client_key,
            'scope': 'user.info.basic,video.upload',
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'state': state
        }

        query = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"
