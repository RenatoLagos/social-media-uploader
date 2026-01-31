"""Servicio de upload a YouTube Shorts"""

import json
from pathlib import Path
from typing import Dict, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from src.config.settings import settings
from src.utils.exceptions import PlatformUploadError, AuthenticationError
from src.utils.logger import get_logger


SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class YouTubeService:
    """Servicio para subir videos a YouTube Shorts"""

    # Categorias de YouTube
    CATEGORIES = {
        'entertainment': '24',
        'people_blogs': '22',
        'comedy': '23',
        'education': '27',
        'howto_style': '26',
        'science_tech': '28',
        'gaming': '20',
        'music': '10',
        'sports': '17',
        'news': '25'
    }

    def __init__(self):
        self.logger = get_logger("youtube")
        self.youtube = None
        self._credentials = None

    def authenticate(self) -> None:
        """
        Autenticar con YouTube usando OAuth2

        Raises:
            AuthenticationError: Si falla la autenticacion
        """
        try:
            creds = None
            token_file = Path(settings.youtube_token_file)
            client_secret_file = Path(settings.youtube_client_secret_file)

            # Verificar archivo de credenciales
            if not client_secret_file.exists():
                raise AuthenticationError(
                    "YouTube",
                    f"Archivo de credenciales no encontrado: {client_secret_file}. "
                    "Descargarlo de Google Cloud Console."
                )

            # Cargar token existente
            if token_file.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
                except Exception as e:
                    self.logger.warning("Token corrupto, sera regenerado", error=str(e))
                    creds = None

            # Renovar o obtener nuevas credenciales
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Renovando token de YouTube")
                    creds.refresh(Request())
                else:
                    self.logger.info("Iniciando flujo OAuth2 de YouTube")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(client_secret_file),
                        SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Guardar token
                token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(token_file, 'w') as f:
                    f.write(creds.to_json())
                self.logger.info("Token guardado", path=str(token_file))

            self._credentials = creds
            self.youtube = build('youtube', 'v3', credentials=creds)
            self.logger.info("Autenticacion YouTube exitosa")

        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError("YouTube", str(e))

    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[list] = None,
        category: str = 'people_blogs',
        privacy: str = 'public'
    ) -> Dict[str, str]:
        """
        Subir video a YouTube Shorts

        Args:
            video_path: Ruta al archivo de video
            title: Titulo del video (max 100 caracteres)
            description: Descripcion del video
            tags: Lista de tags (opcional)
            category: Categoria del video
            privacy: Estado de privacidad (public, private, unlisted)

        Returns:
            Dict con video_id y url

        Raises:
            PlatformUploadError: Si falla el upload
        """
        if not self.youtube:
            self.authenticate()

        # Validar y preparar parametros
        title = self._prepare_title(title)
        tags = self._prepare_tags(tags)
        category_id = self.CATEGORIES.get(category, self.CATEGORIES['people_blogs'])

        try:
            self.logger.info(
                "Iniciando upload a YouTube Shorts",
                title=title,
                privacy=privacy
            )

            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy,
                    'selfDeclaredMadeForKids': False,
                    'madeForKids': False
                }
            }

            # Configurar upload resumible
            media = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                resumable=True,
                chunksize=1024 * 1024  # 1MB chunks
            )

            # Crear request
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            # Ejecutar upload con progreso
            response = self._execute_upload(request)

            video_id = response['id']
            url = f"https://youtube.com/shorts/{video_id}"

            self.logger.info(
                "Upload a YouTube exitoso",
                video_id=video_id,
                url=url
            )

            return {
                'video_id': video_id,
                'url': url,
                'platform': 'YouTube'
            }

        except HttpError as e:
            error_content = json.loads(e.content.decode())
            error_reason = error_content.get('error', {}).get('message', str(e))
            raise PlatformUploadError("YouTube", f"API Error: {error_reason}")

        except Exception as e:
            raise PlatformUploadError("YouTube", str(e))

    def _execute_upload(self, request) -> dict:
        """Ejecutar upload con manejo de progreso"""
        response = None

        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                self.logger.debug(f"Upload progress: {progress}%")

        return response

    def _prepare_title(self, title: str) -> str:
        """Preparar titulo (max 100 caracteres)"""
        title = title.strip()
        if len(title) > 100:
            title = title[:97] + "..."
        return title

    def _prepare_tags(self, tags: Optional[list]) -> list:
        """Preparar lista de tags"""
        default_tags = ['Shorts']

        if not tags:
            return default_tags

        # Asegurar que 'Shorts' este incluido
        if 'Shorts' not in tags and '#Shorts' not in tags:
            tags = ['Shorts'] + tags

        # Limpiar tags
        cleaned_tags = []
        for tag in tags:
            tag = tag.strip().replace('#', '')
            if tag and tag not in cleaned_tags:
                cleaned_tags.append(tag)

        return cleaned_tags[:30]  # YouTube permite max 30 tags

    def is_configured(self) -> bool:
        """Verificar si el servicio esta configurado"""
        client_secret = Path(settings.youtube_client_secret_file)
        return client_secret.exists()
