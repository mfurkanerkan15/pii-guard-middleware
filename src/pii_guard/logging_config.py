"""JSON tabanlı yapılandırılmış loglama — yalnızca standart kütüphane."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pii_guard.config import Settings


class JSONFormatter(logging.Formatter):
    """Log kayıtlarını JSON formatında biçimlendirir."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "request_id": getattr(record, "request_id", None),
            "message": record.getMessage(),
        }
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(settings: "Settings") -> None:
    """Uygulama başlangıcında çağrılır. Log dizinini oluşturur ve JSON handler ekler."""
    log_dir = settings.log_dir
    os.makedirs(log_dir, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Zaten yapılandırılmışsa yeniden ekleme
    if any(
        isinstance(h, logging.FileHandler) and "security_audit" in getattr(h, "baseFilename", "")
        for h in root_logger.handlers
    ):
        return

    file_handler = logging.FileHandler(
        os.path.join(log_dir, "security_audit.log"),
        encoding="utf-8",
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
