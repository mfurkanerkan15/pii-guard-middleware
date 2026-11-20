from pii_guard.config import Settings, get_settings


def test_default_settings():
    """Varsayılan yapılandırma değerlerinin doğruluğu."""
    s = Settings()
    assert s.gemini_model == "gemini-2.5-flash"
    assert s.token_min_len == 4
    assert s.dlp_ner_enabled is True
    assert s.ner_score_threshold == 0.6
    assert s.log_level == "INFO"
    assert s.log_dir == "logs"


def test_gemini_api_key_unprefixed_and_secret(monkeypatch):
    """GEMINI_API_KEY öneksiz okunmalı ve SecretStr olarak saklanmalı."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key-123")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "test-secret-key-123"
    assert "test-secret-key-123" not in str(settings.gemini_api_key)


def test_pii_guard_prefixed_settings_override(monkeypatch):
    """PII_GUARD_ önekli değişkenlerin ayarları geçersiz kılması."""
    monkeypatch.setenv("PII_GUARD_GEMINI_MODEL", "gemini-2.0-pro")
    monkeypatch.setenv("PII_GUARD_TOKEN_MIN_LEN", "6")
    monkeypatch.setenv("PII_GUARD_DLP_NER_ENABLED", "false")
    monkeypatch.setenv("PII_GUARD_NER_SCORE_THRESHOLD", "0.85")
    monkeypatch.setenv("PII_GUARD_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("PII_GUARD_LOG_DIR", "custom_logs")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.gemini_model == "gemini-2.0-pro"
    assert settings.token_min_len == 6
    assert settings.dlp_ner_enabled is False
    assert settings.ner_score_threshold == 0.85
    assert settings.log_level == "DEBUG"
    assert settings.log_dir == "custom_logs"


def test_unknown_env_keys_ignored(monkeypatch):
    """Bilinmeyen ortam değişkenleri pydantic-settings tarafından yoksayılmalı (extra='ignore')."""
    monkeypatch.setenv("RANDOM_THIRD_PARTY_VAR", "some_value")
    monkeypatch.setenv("PII_GUARD_UNKNOWN_FIELD", "another_value")
    get_settings.cache_clear()

    # Hata vermeden yüklenmeli
    settings = get_settings()
    assert settings is not None


def test_get_settings_lru_cached(monkeypatch):
    """get_settings() çağrısının aynı örneği önbellekten döndürmesi."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
