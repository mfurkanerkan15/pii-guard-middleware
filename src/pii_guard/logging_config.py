"""JSON tabanlı yapılandırılmış loglama — yalnızca standart kütüphane."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pii_guard.config import Settings


class JSONFormatter(logging.Formatter):
    """Log kayıtlarını JSON formatında biçimlendirir."""

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        request_id = getattr(record, "request_id", None)

        # Eğer extra ile verilmemişse, standart "<request_id> | <mesaj>" formatından ayıkla
        if not request_id and " | " in msg:
            parts = msg.split(" | ", 1)
            candidate_id = parts[0].strip()
            # ID boşluk içermiyorsa ve makul bir uzunluktaysa request_id olarak kabul et
            if candidate_id and " " not in candidate_id:
                request_id = candidate_id
                msg = parts[1].strip()

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "request_id": request_id or "N/A",
            "message": msg,
        }

        if record.exc_info:
            # Traceback formatla (yalnızca exception türü ve mesajı standart güvenli formatlanır)
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(settings: "Settings") -> None:
    """Uygulama başlangıcında çağrılır. Log dizinini oluşturur ve JSON handler'ı bağlar.

    İdempotenttir: art arda çağrıldığında yinelenen handler eklemez, mevcut eski dosya
    bağlantısını güvenle kapatıp günceller.
    """
    log_dir = settings.log_dir
    os.makedirs(log_dir, exist_ok=True)
    target_path = os.path.abspath(os.path.join(log_dir, "security_audit.log"))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Mevcut security_audit dosya handler'larını kapat ve temizle (idempotency)
    for h in root_logger.handlers[:]:
        if isinstance(h, logging.FileHandler) and "security_audit" in getattr(
            h, "baseFilename", ""
        ):
            if os.path.abspath(getattr(h, "baseFilename", "")) == target_path:
                return  # Zaten tam olarak bu dosyaya bağlı
            h.close()
            root_logger.removeHandler(h)

    file_handler = logging.FileHandler(target_path, encoding="utf-8")
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
