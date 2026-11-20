import logging

import pytest

from pii_guard.config import get_settings
from pii_guard.llm import get_llm_client
from pii_guard.masking import get_analyzer


@pytest.fixture(scope="session", autouse=True)
def warm_up_presidio():
    """Test oturumu başında Presidio analyzer'ı ısıtır (spaCy modelini önceden yükler)."""
    analyzer = get_analyzer()
    analyzer.analyze(text="warm up test", entities=["PERSON"], language="en")


@pytest.fixture(autouse=True)
def reset_caches():
    """Her test öncesi ve sonrası get_settings ve get_llm_client önbelleğini sıfırlar."""
    get_settings.cache_clear()
    get_llm_client.cache_clear()
    yield
    get_settings.cache_clear()
    get_llm_client.cache_clear()


@pytest.fixture(autouse=True)
def clean_logging_handlers():
    """Her test sonrasında root logger üzerindeki dosya handler'larını kapatır ve temizler.

    Bu sayede Windows üzerinde dosya kilidi (PermissionError) oluşması ve testler
    arasında log kirliliği engellenir.
    """
    yield
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            root_logger.removeHandler(handler)
