#!/usr/bin/env python3
"""
Script para autenticacion de TikTok OAuth2

Este script realiza el flujo OAuth2 para obtener el access token
que permite subir videos a TikTok.

Requisitos previos:
1. Crear app en TikTok for Developers (https://developers.tiktok.com/)
2. Configurar Redirect URI como: http://localhost:8080/callback
3. Agregar TIKTOK_CLIENT_KEY y TIKTOK_CLIENT_SECRET en .env

Uso:
    python scripts/authenticate_tiktok.py
"""

import sys
import webbrowser
import json
import secrets
import hashlib
import base64
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests

# Agregar directorio raiz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings


# Configuracion
REDIRECT_URI = "http://localhost:8080/callback"
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
SCOPES = "user.info.basic,user.info.profile,video.upload"
TOKEN_FILE = Path("credentials/tiktok_token.json")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handler para recibir el callback de OAuth"""

    auth_code = None
    state_received = None
    error = None

    def do_GET(self):
        """Manejar GET request del callback"""
        parsed = urlparse(self.path)

        if parsed.path == "/callback":
            params = parse_qs(parsed.query)

            if "error" in params:
                OAuthCallbackHandler.error = params.get("error_description", ["Unknown error"])[0]
                self._send_response("Error de autorizacion. Puedes cerrar esta ventana.", error=True)
            elif "code" in params:
                OAuthCallbackHandler.auth_code = params["code"][0]
                OAuthCallbackHandler.state_received = params.get("state", [None])[0]
                self._send_response("Autorizacion exitosa! Puedes cerrar esta ventana.")
            else:
                self._send_response("Respuesta inesperada. Puedes cerrar esta ventana.", error=True)
        else:
            self.send_error(404)

    def _send_response(self, message: str, error: bool = False):
        """Enviar respuesta HTML"""
        color = "#e74c3c" if error else "#27ae60"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TikTok Auth - FerRealSpanish Uploader</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px 60px;
                    border-radius: 16px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    text-align: center;
                }}
                h1 {{
                    color: {color};
                    margin-bottom: 10px;
                }}
                p {{
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{"Error" if error else "Exito!"}</h1>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Silenciar logs del servidor"""
        pass


def generate_pkce():
    """Generar code_verifier y code_challenge para PKCE"""
    # Code verifier: random string de 43-128 caracteres (solo alfanumericos)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    code_verifier = ''.join(secrets.choice(alphabet) for _ in range(43))

    # Code challenge: SHA256 hash del verifier, codificado en HEX (no base64!)
    # TikTok requiere HEX encoding, no base64url como el estandar PKCE
    sha256_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = sha256_hash.hex()

    return code_verifier, code_challenge


def get_auth_url(client_key: str, state: str, code_challenge: str) -> str:
    """Generar URL de autorizacion con PKCE"""
    params = {
        "client_key": client_key,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def verify_pkce(code_verifier: str, expected_challenge: str) -> bool:
    """Verificar que el code_verifier genera el code_challenge esperado"""
    sha256_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
    calculated_challenge = sha256_hash.hex()  # TikTok usa HEX, no base64url
    return calculated_challenge == expected_challenge


def exchange_code_for_token(code: str, client_key: str, client_secret: str, code_verifier: str, code_challenge: str) -> dict:
    """Intercambiar codigo por access token con PKCE"""
    # Debug
    print(f"  Code verifier: {code_verifier}")
    print(f"  Code verifier length: {len(code_verifier)}")

    # Verificar PKCE localmente
    if verify_pkce(code_verifier, code_challenge):
        print(f"  PKCE verification: OK (local check passed)")
    else:
        print(f"  PKCE verification: FAILED!")
        print(f"  Expected challenge: {code_challenge}")
        sha256_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
        calc = base64.urlsafe_b64encode(sha256_hash).decode('ascii').rstrip('=')
        print(f"  Calculated challenge: {calc}")

    # Usar params dict directamente (requests lo encodea)
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print(f"  Sending to: {TOKEN_URL}")
    response = requests.post(TOKEN_URL, data=data, headers=headers)

    print(f"  Response status: {response.status_code}")
    print(f"  Response: {response.text}")

    # Si falla con form-urlencoded, intentar con JSON
    if "invalid" in response.text.lower():
        print("\n  Intentando con JSON...")
        headers_json = {"Content-Type": "application/json"}
        response = requests.post(TOKEN_URL, json=data, headers=headers_json)
        print(f"  Response JSON: {response.text}")

    return response.json()


def save_token(token_data: dict):
    """Guardar token en archivo"""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)

    print(f"\nToken guardado en: {TOKEN_FILE}")


def main():
    """Realizar flujo OAuth2 de TikTok"""
    print("\n" + "=" * 50)
    print("   TikTok Authentication - FerRealSpanish Uploader")
    print("=" * 50 + "\n")

    # Verificar configuracion
    client_key = settings.tiktok_client_key
    client_secret = settings.tiktok_client_secret

    if not client_key:
        print("ERROR: TIKTOK_CLIENT_KEY no configurado en .env")
        print("\nAgrega estas lineas a tu archivo .env:")
        print("  TIKTOK_CLIENT_KEY=tu_client_key")
        print("  TIKTOK_CLIENT_SECRET=tu_client_secret")
        sys.exit(1)

    if not client_secret:
        print("ERROR: TIKTOK_CLIENT_SECRET no configurado en .env")
        sys.exit(1)

    print(f"Client Key: {client_key[:10]}...")
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Scopes: {SCOPES}")

    # Generar state para CSRF protection
    state = secrets.token_urlsafe(16)

    # Generar PKCE code_verifier y code_challenge
    code_verifier, code_challenge = generate_pkce()
    print(f"PKCE habilitado:")
    print(f"  Verifier (primeros 20): {code_verifier[:20]}...")
    print(f"  Challenge: {code_challenge}")

    # Iniciar servidor local
    print("\nIniciando servidor local para callback...")
    server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)

    # Generar URL de autorizacion con PKCE
    auth_url = get_auth_url(client_key, state, code_challenge)

    print("\nAbriendo navegador para autorizacion...")
    print("Si no se abre automaticamente, visita:")
    print(f"\n{auth_url}\n")

    # Debug: verificar que el challenge está en la URL
    if code_challenge in auth_url:
        print("(code_challenge encontrado en URL: OK)")
    else:
        print("(ADVERTENCIA: code_challenge NO encontrado en URL exactamente)")
        print(f"  Challenge buscado: {code_challenge}")

    # Abrir navegador
    webbrowser.open(auth_url)

    # Esperar callback
    print("Esperando autorizacion...")
    while OAuthCallbackHandler.auth_code is None and OAuthCallbackHandler.error is None:
        server.handle_request()

    server.server_close()

    # Verificar error
    if OAuthCallbackHandler.error:
        print(f"\nERROR: {OAuthCallbackHandler.error}")
        sys.exit(1)

    # Verificar state (CSRF protection)
    if OAuthCallbackHandler.state_received != state:
        print("\nERROR: State mismatch - posible ataque CSRF")
        sys.exit(1)

    code = OAuthCallbackHandler.auth_code
    print(f"\nCodigo de autorizacion recibido: {code[:20]}...")

    # Intercambiar codigo por token
    print("\nIntercambiando codigo por access token...")
    try:
        token_response = exchange_code_for_token(code, client_key, client_secret, code_verifier, code_challenge)

        if "error" in token_response:
            print(f"\nERROR: {token_response.get('error_description', token_response['error'])}")
            sys.exit(1)

        # Extraer datos del token
        access_token = token_response.get("access_token")
        open_id = token_response.get("open_id")
        expires_in = token_response.get("expires_in")
        refresh_token = token_response.get("refresh_token")

        print("\n" + "=" * 50)
        print("   AUTENTICACION EXITOSA!")
        print("=" * 50)
        print(f"\nOpen ID: {open_id}")
        print(f"Access Token: {access_token[:30]}...")
        print(f"Expira en: {expires_in} segundos ({expires_in // 86400} dias)")

        # Guardar token
        save_token(token_response)

        # Mostrar instrucciones
        print("\n" + "-" * 50)
        print("SIGUIENTE PASO:")
        print("-" * 50)
        print("\nAgrega esta linea a tu archivo .env:")
        print(f"\n  TIKTOK_ACCESS_TOKEN={access_token}")
        print("\nY habilita TikTok:")
        print("  ENABLE_TIKTOK=true")
        print("\nYa puedes subir videos a TikTok!")

    except Exception as e:
        print(f"\nERROR intercambiando token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
