#!/usr/bin/env python3
"""
Script para validar que todas las APIs estan configuradas correctamente

Uso:
    python scripts/test_apis.py
"""

import sys
from pathlib import Path

# Agregar directorio raiz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings


def test_openai():
    """Test OpenAI API (Whisper + GPT-4)"""
    print("\n[OpenAI API]")

    if not settings.openai_api_key:
        print("  OPENAI_API_KEY: No configurada")
        return False

    print(f"  OPENAI_API_KEY: Configurada ({settings.openai_api_key[:10]}...)")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)

        # Test simple
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Responde solo 'OK'"}],
            max_tokens=5
        )

        result = response.choices[0].message.content.strip()
        print(f"  Test GPT-4: OK (respuesta: {result})")
        return True

    except Exception as e:
        print(f"  Test GPT-4: FALLO - {e}")
        return False


def test_youtube():
    """Test configuracion de YouTube"""
    print("\n[YouTube API]")

    client_secret = Path(settings.youtube_client_secret_file)
    token_file = Path(settings.youtube_token_file)

    if not client_secret.exists():
        print(f"  Client Secret: No encontrado ({client_secret})")
        print("  -> Descargar de Google Cloud Console")
        return False

    print(f"  Client Secret: OK ({client_secret})")

    if not token_file.exists():
        print(f"  Token: No encontrado ({token_file})")
        print("  -> Ejecutar: python scripts/authenticate_youtube.py")
        return False

    print(f"  Token: OK ({token_file})")

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            str(token_file),
            ['https://www.googleapis.com/auth/youtube.upload']
        )

        youtube = build('youtube', 'v3', credentials=creds)
        # Test: obtener info del canal
        response = youtube.channels().list(
            part='snippet',
            mine=True
        ).execute()

        if response.get('items'):
            channel = response['items'][0]['snippet']['title']
            print(f"  Canal conectado: {channel}")

        return True

    except Exception as e:
        print(f"  Test conexion: FALLO - {e}")
        return False


def test_instagram():
    """Test configuracion de Instagram (instagrapi)"""
    print("\n[Instagram API]")

    if not settings.instagram_username:
        print("  Username: No configurado")
        return False

    print(f"  Username: {settings.instagram_username}")

    if not settings.instagram_password:
        print("  Password: No configurado")
        return False

    print("  Password: Configurado (********)")

    try:
        from src.services.instagram_service import InstagramService

        service = InstagramService()
        info = service.test_connection()

        print(f"  Cuenta conectada: @{info['username']}")
        print(f"  Nombre: {info['full_name']}")
        return True

    except Exception as e:
        print(f"  Test conexion: FALLO - {e}")
        return False


def test_tiktok():
    """Test configuracion de TikTok"""
    print("\n[TikTok API]")

    if not settings.enable_tiktok:
        print("  Estado: Deshabilitado (ENABLE_TIKTOK=false)")
        return None  # No es un fallo, solo no habilitado

    if not settings.tiktok_client_key:
        print("  Client Key: No configurado")
        return False

    print(f"  Client Key: Configurado ({settings.tiktok_client_key[:10]}...)")

    if not settings.tiktok_access_token:
        print("  Access Token: No configurado")
        print("  -> Requiere app aprobada por TikTok")
        return False

    print(f"  Access Token: Configurado ({settings.tiktok_access_token[:15]}...)")
    print("  NOTA: Verificacion completa requiere app aprobada")

    return True


def print_summary(results):
    """Imprimir resumen de resultados"""
    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)

    for service, status in results.items():
        if status is True:
            icon = "OK"
        elif status is False:
            icon = "FALLO"
        else:
            icon = "DESHABILITADO"

        print(f"  {service}: {icon}")

    # Contar exitosos
    success = sum(1 for s in results.values() if s is True)
    total = sum(1 for s in results.values() if s is not None)

    print(f"\n{success}/{total} servicios configurados correctamente")

    if success < total:
        print("\nPara completar la configuracion, revisa el README.md")


def main():
    """Ejecutar todos los tests"""
    print("\n" + "=" * 50)
    print("VERIFICACION DE CONFIGURACION DE APIs")
    print("=" * 50)

    results = {}

    results['OpenAI'] = test_openai()
    results['YouTube'] = test_youtube()
    results['Instagram'] = test_instagram()
    results['TikTok'] = test_tiktok()

    print_summary(results)


if __name__ == '__main__':
    main()
