#!/usr/bin/env python3
"""
Script para autenticacion inicial de Instagram con soporte 2FA

Uso:
    python scripts/authenticate_instagram.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired

from src.config.settings import settings


SESSION_FILE = Path("credentials/instagram_session.json")


def main():
    print("\n=== Autenticacion de Instagram ===\n")

    if not settings.instagram_username or not settings.instagram_password:
        print("ERROR: Configura INSTAGRAM_USERNAME y INSTAGRAM_PASSWORD en .env")
        sys.exit(1)

    print(f"Usuario: {settings.instagram_username}")

    client = Client()

    try:
        # Intentar login normal
        client.login(settings.instagram_username, settings.instagram_password)

    except TwoFactorRequired as e:
        print("\n2FA detectado. Revisa tu app de autenticacion o SMS.")
        verification_code = input("Ingresa el codigo de verificacion: ").strip()

        # Login con codigo 2FA
        client.login(
            settings.instagram_username,
            settings.instagram_password,
            verification_code=verification_code
        )

    # Guardar sesion
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    client.dump_settings(SESSION_FILE)

    # Verificar
    user_info = client.account_info()

    print(f"\nLogin exitoso!")
    print(f"  Cuenta: @{user_info.username}")
    print(f"  Nombre: {user_info.full_name}")
    print(f"\nSesion guardada en: {SESSION_FILE}")
    print("Ya puedes usar el sistema para subir Reels!")


if __name__ == '__main__':
    main()
