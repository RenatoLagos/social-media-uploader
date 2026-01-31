"""Sistema de logging estructurado"""

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog


_logger_configured = False


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO") -> None:
    """Configurar logging estructurado"""
    global _logger_configured

    if _logger_configured:
        return

    # Crear directorio de logs si no existe
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers = [
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    else:
        handlers = [logging.StreamHandler(sys.stdout)]

    # Configurar logging basico
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        handlers=handlers
    )

    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True)
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _logger_configured = True


def get_logger(name: str = "upload_to_socialmedia") -> structlog.stdlib.BoundLogger:
    """Obtener logger configurado"""
    # Importar settings aqui para evitar circular import
    from src.config.settings import settings

    setup_logging(settings.log_file, settings.log_level)
    return structlog.get_logger(name)
