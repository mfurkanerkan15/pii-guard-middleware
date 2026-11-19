import pytest
from pii_guard.config import get_settings
from pii_guard.masking import get_analyzer


@pytest.fixture(scope="session", autouse=True)
def warm_up_presidio():
    """Test oturumu başında Presidio analyzer'ı ısıtır (spaCy modelini önceden yükler)."""
    analyzer = get_analyzer()
    analyzer.analyze(text="warm up test", entities=["PERSON"], language="en")


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Her test öncesi ve sonrası get_settings önbelleğini temizler."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
