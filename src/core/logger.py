import logging
import os
import sys
from typing import Optional

from src.core.config import settings


def get_logger(name: Optional[str] = "financial_platform") -> logging.Logger:
    """
    Retorna uma instância configurada do Logger padronizado para o projeto.
    Integra-se automaticamente ao Google Cloud Logging se disponível e ativo,
    ou gera logs estruturados com timestamp ISO e severidade (INFO, WARNING, ERROR).
    """
    logger = logging.getLogger(name)

    # Evita adicionar múltiplos handlers caso get_logger seja chamado mais de uma vez
    if logger.handlers:
        return logger

    log_level_str = getattr(settings, "LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    # Formato padronizado de log (Compatível com Cloud Logging)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler para Console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Tenta integração opcional com o Google Cloud Logging
    try:
        from google.cloud import logging as cloud_logging

        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            client = cloud_logging.Client(project=settings.PROJECT_ID)
            cloud_handler = cloud_logging.handlers.CloudLoggingHandler(client, name=name)
            cloud_handler.setLevel(log_level)
            logger.addHandler(cloud_handler)
    except Exception:
        # Silenciosamente prossegue utilizando o ConsoleHandler caso não esteja configurado
        pass

    return logger


# Logger global da plataforma
logger = get_logger("financial_platform")
