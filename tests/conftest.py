import pytest
from pii_guard.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Her test öncesi ve sonrası get_settings önbelleğini temizler."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
