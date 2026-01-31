# Social Media Video Uploader

Sistema de automatizacion para subir videos cortos a **YouTube Shorts**, **Instagram Reels** y **TikTok** con transcripcion y descripciones generadas por IA.

## Caracteristicas

- Transcripcion automatica del audio con **OpenAI Whisper**
- Generacion de descripciones optimizadas por plataforma con **GPT-4**
- Upload automatico a multiples plataformas
- CLI intuitivo con indicadores de progreso
- Logging estructurado para debugging
- Manejo robusto de errores (si una plataforma falla, continua con las otras)

## Requisitos

- Python 3.11+
- Cuenta de OpenAI con API key
- Credenciales de YouTube (Google Cloud)
- Cuenta profesional de Instagram con Graph API (opcional)
- App aprobada de TikTok (opcional)

## Instalacion

### 1. Clonar y preparar entorno

```bash
cd C:\Users\Admin\Projects\upload_to_socialmedia

# Activar entorno virtual
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
# Copiar plantilla
copy .env.example .env

# Editar .env con tus credenciales
notepad .env
```

## Configuracion de APIs

### OpenAI (Requerido)

1. Ir a https://platform.openai.com/api-keys
2. Crear nueva API key
3. Agregar a `.env`:
   ```
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
   ```

### YouTube (Requerido para YouTube Shorts)

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear nuevo proyecto
3. Habilitar **YouTube Data API v3**
4. Crear credenciales OAuth 2.0:
   - Ir a APIs & Services > Credentials
   - Create Credentials > OAuth client ID
   - Application type: **Desktop app**
   - Descargar JSON
5. Guardar el archivo como `credentials/youtube_client_secret.json`
6. Ejecutar autenticacion inicial:
   ```bash
   python scripts/authenticate_youtube.py
   ```
   Se abrira el navegador para autorizar la aplicacion.

### Instagram (Opcional)

Instagram Graph API requiere una cuenta profesional y video en URL publica.

1. Convertir cuenta a Professional/Creator
2. Crear app en [Meta for Developers](https://developers.facebook.com/)
3. Agregar producto "Instagram Graph API"
4. Obtener Page Access Token de larga duracion
5. Obtener Instagram Business Account ID
6. Agregar a `.env`:
   ```
   INSTAGRAM_ACCESS_TOKEN=EAAxxxxxxxxxx
   INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000
   ```

**Nota**: Para subir a Instagram, el video debe estar en una URL publica (Cloudinary, S3, etc.)

### TikTok (Opcional - Requiere aprobacion)

La API de TikTok requiere aprobacion que puede tomar semanas.

1. Registrarse en [TikTok for Developers](https://developers.tiktok.com/)
2. Crear app con Content Posting API
3. Esperar aprobacion
4. Una vez aprobada, agregar a `.env`:
   ```
   TIKTOK_CLIENT_KEY=awxxxxxxxxxx
   TIKTOK_CLIENT_SECRET=xxxxxxxxxxxx
   TIKTOK_ACCESS_TOKEN=act.xxxxxxxxxx
   ENABLE_TIKTOK=true
   ```

## Uso

### Uso basico

```bash
python upload.py C:\videos\mi_video.mp4
```

### Con opciones

```bash
# Con titulo personalizado
python upload.py video.mp4 --title "Mi video genial"

# Solo YouTube
python upload.py video.mp4 --only-youtube

# Saltar Instagram
python upload.py video.mp4 --skip-instagram

# Con URL de Instagram (si el video esta hosteado)
python upload.py video.mp4 --instagram-url "https://cloudinary.com/mi_video.mp4"

# Verificar configuracion
python upload.py video.mp4 --check-config

# Modo verbose
python upload.py video.mp4 --verbose
```

### Opciones disponibles

| Opcion | Descripcion |
|--------|-------------|
| `--title, -t` | Titulo personalizado para el video |
| `--instagram-url` | URL publica del video para Instagram |
| `--only-youtube` | Solo subir a YouTube |
| `--only-instagram` | Solo subir a Instagram |
| `--only-tiktok` | Solo subir a TikTok |
| `--skip-youtube` | Saltar YouTube |
| `--skip-instagram` | Saltar Instagram |
| `--skip-tiktok` | Saltar TikTok |
| `--check-config` | Verificar configuracion sin subir |
| `--verbose, -v` | Mostrar logs detallados |

## Verificar Configuracion

```bash
python scripts/test_apis.py
```

Esto verificara que todas las APIs esten correctamente configuradas.

## Estructura del Proyecto

```
upload_to_socialmedia/
├── src/
│   ├── main.py                 # Orchestrador principal
│   ├── config/
│   │   └── settings.py         # Configuracion
│   ├── services/
│   │   ├── transcription_service.py   # OpenAI Whisper
│   │   ├── description_service.py     # GPT-4
│   │   ├── youtube_service.py         # YouTube API
│   │   ├── instagram_service.py       # Instagram API
│   │   └── tiktok_service.py          # TikTok API
│   ├── utils/
│   │   ├── video_validator.py   # Validacion de videos
│   │   ├── logger.py            # Logging
│   │   └── exceptions.py        # Excepciones
│   └── models/
│       └── video_metadata.py    # Modelos de datos
├── scripts/
│   ├── authenticate_youtube.py  # Setup YouTube OAuth
│   └── test_apis.py             # Verificar configuracion
├── credentials/                  # Credenciales (no en git)
├── logs/                         # Logs de ejecucion
├── upload.py                     # CLI principal
├── requirements.txt
├── .env                          # Variables de entorno (no en git)
└── .env.example
```

## Limitaciones

- **Formato**: Solo videos MP4
- **Duracion**: Maximo 60 segundos (configurable)
- **Tamano**: Maximo 500 MB (configurable)
- **Instagram**: Requiere video en URL publica
- **TikTok**: Requiere app aprobada

## Flujo de Procesamiento

1. **Validacion**: Verifica formato, duracion y tamano del video
2. **Transcripcion**: Extrae audio y lo transcribe con Whisper
3. **Descripciones**: GPT-4 genera descripciones optimizadas para cada plataforma
4. **Upload**: Sube el video a cada plataforma habilitada

Si una plataforma falla, el proceso continua con las demas.

## Troubleshooting

### "OPENAI_API_KEY no configurada"
Asegurate de tener el archivo `.env` con la API key correcta.

### "Archivo de credenciales no encontrado" (YouTube)
Descarga el archivo OAuth JSON de Google Cloud Console y guardalo en `credentials/youtube_client_secret.json`.

### "Token corrupto" (YouTube)
Elimina `credentials/tokens/youtube_token.json` y ejecuta `python scripts/authenticate_youtube.py` nuevamente.

### "Se requiere URL publica" (Instagram)
Instagram Graph API no acepta archivos locales. Sube el video a Cloudinary, S3, u otro servicio que proporcione URLs publicas.

### Rate limits
El sistema tiene reintentos automaticos con backoff exponencial. Si persiste, espera unos minutos antes de reintentar.

## Costos Estimados

- **OpenAI Whisper**: ~$0.006 por minuto de audio
- **GPT-4**: ~$0.03 por 1K tokens (aprox. $0.02-0.05 por video)
- **YouTube/Instagram/TikTok**: Gratis

Para un video de 60 segundos, el costo aproximado es **$0.03-0.08 USD**.

## Licencia

MIT

## Contribuir

Pull requests son bienvenidos. Para cambios grandes, abre un issue primero.
