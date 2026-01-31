#!/usr/bin/env python3
"""
Script para autenticacion inicial de YouTube OAuth2

Este script debe ejecutarse una vez para obtener el token de acceso
que permite subir videos a YouTube.

Requisitos previos:
1. Crear proyecto en Google Cloud Console
2. Habilitar YouTube Data API v3
3. Crear credenciales OAuth 2.0 (tipo: Desktop app)
4. Descargar JSON y guardarlo en credentials/youtube_client_secret.json

Uso:
    python scripts/authenticate_youtube.py
"""

import sys
from pathlib import Path

# Agregar directorio raiz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow

from src.config.settings import settings


SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]


def main():
    """Realizar flujo OAuth2 y guardar token"""
    print("\n=== Autenticacion de YouTube ===\n")

    client_secret_file = Path(settings.youtube_client_secret_file)
    token_file = Path(settings.youtube_token_file)

    # Verificar archivo de credenciales
    if not client_secret_file.exists():
        print(f"ERROR: Archivo de credenciales no encontrado: {client_secret_file}")
        print("\nPasos para obtener credenciales:")
        print("1. Ir a https://console.cloud.google.com/")
        print("2. Crear proyecto o seleccionar existente")
        print("3. Ir a APIs & Services > Library")
        print("4. Buscar y habilitar 'YouTube Data API v3'")
        print("5. Ir a APIs & Services > Credentials")
        print("6. Click 'Create Credentials' > 'OAuth client ID'")
        print("7. Application type: 'Desktop app'")
        print("8. Descargar JSON y guardarlo como:")
        print(f"   {client_secret_file}")
        sys.exit(1)

    print(f"Usando credenciales: {client_secret_file}")
    print("\nSe abrira una ventana del navegador para autorizar la aplicacion.")
    print("Por favor, inicia sesion con tu cuenta de YouTube.\n")

    try:
        # Iniciar flujo OAuth
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_file),
            SCOPES
        )

        # Abrir navegador para autorizacion
        credentials = flow.run_local_server(
            port=0,
            prompt='consent',
            success_message='Autorizacion completada! Puedes cerrar esta ventana.'
        )

        # Crear directorio si no existe
        token_file.parent.mkdir(parents=True, exist_ok=True)

        # Guardar token
        with open(token_file, 'w') as f:
            f.write(credentials.to_json())

        print(f"\nToken guardado exitosamente en: {token_file}")
        print("\nYa puedes usar el sistema para subir videos a YouTube!")

    except Exception as e:
        print(f"\nERROR durante autenticacion: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
