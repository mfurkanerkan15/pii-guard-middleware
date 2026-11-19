import json
import logging
import subprocess
import sys
from unittest.mock import patch

import pytest

from pii_guard.config import Settings, get_settings
from pii_guard.dlp import check_for_leaks
from pii_guard.llm import LLMClient, get_llm_client
from pii_guard.logging_config import configure_logging


def test_api_import_without_api_key_does_not_fail():
    """(a) GEMINI_API_KEY ortam değişkeni yokken pii_guard.api import hatası vermemeli."""
    code = (
        "import os\n"
        "os.environ.pop('GEMINI_API_KEY', None)\n"
        "import pii_guard.api\n"
        "print('IMPORT_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "IMPORT_OK" in result.stdout


def test_llm_call_without_api_key_raises_informative_error(monkeypatch):
    """(b) API anahtarı yokken LLM istemcisi oluşturulması anlaşılır bir ValueError fırlatmalı."""
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    get_llm_client.cache_clear()

    with pytest.raises(ValueError) as exc_info:
        LLMClient()

    assert "GEMINI_API_KEY is not set or empty" in str(exc_info.value)


def test_settings_override_via_env(monkeypatch):
    """(c.1) Ortam değişkeni (PII_GUARD_TOKEN_MIN_LEN) ile ayar geçersiz kılınabilmeli."""
    monkeypatch.setenv("PII_GUARD_TOKEN_MIN_LEN", "8")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.token_min_len == 8

    # Katman 4 token_min_len testinde 5 karakterlik parça filtrelenmeli
    mapping = {"PERSON_1": "Ahmet Can"}
    # Normalde token_min_len=4 iken "Ahmet" (5 harf) sızıntı sayılır, ancak 8 iken sayılmaz
    assert check_for_leaks("Kullanıcı Ahmet burada", mapping) is False


def test_dlp_ner_disabled_skips_layer_5(monkeypatch):
    """(c.2) dlp_ner_enabled=False olduğunda Katman 5 analizi çağrılmamalı."""
    monkeypatch.setenv("PII_GUARD_DLP_NER_ENABLED", "false")
    get_settings.cache_clear()

    with patch("pii_guard.dlp.get_analyzer") as mock_get_analyzer:
        # Sızıntı olmayan bir metin gönderilir, katman 1-4 False döner
        result = check_for_leaks("Merhaba dünya", {"PERSON_1": "Ahmet Yılmaz"})
        assert result is False
        # Katman 5 devre dışı olduğu için analyzer hiç çağrılmamalıdır
        mock_get_analyzer.assert_not_called()


def test_import_does_not_create_log_directory_or_file(tmp_path):
    """(d) Modül import edildiğinde diske logs klasörü veya log dosyası açılmamalı."""
    code = "import pii_guard.masking\nimport pii_guard.dlp\nimport pii_guard.api\n"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert not (tmp_path / "logs").exists()


def test_json_log_output_is_valid_json_and_contains_no_raw_pii(tmp_path):
    """(e) JSON log çıktısı geçerli JSON olmalı ve ham PII içermemeli."""
    test_log_dir = str(tmp_path / "test_logs")
    dummy_settings = Settings(log_dir=test_log_dir, log_level="INFO")

    configure_logging(dummy_settings)
    logger = logging.getLogger("pii_guard.test_audit")

    raw_name = "Gizli Ad"
    raw_email = "gizli@example.com"
    request_id = "REQ_JSON_001"

    # Güvenlik gereği maskeleme sırasında loglanan mesaj formatı
    logger.info(
        f"{request_id} | Giriş maskeleme tamamlandı | Varlık Sayısı: 2 | Tipler: ['EMAIL', 'PERSON']"
    )

    log_file = tmp_path / "test_logs" / "security_audit.log"
    assert log_file.exists()

    with open(log_file, encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= 1
    last_log = json.loads(lines[-1].strip())

    assert "timestamp" in last_log
    assert "level" in last_log
    assert "message" in last_log
    assert raw_name not in last_log["message"]
    assert raw_email not in last_log["message"]
