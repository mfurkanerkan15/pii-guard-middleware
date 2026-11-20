# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.3.0] - 2026-11-20

### Added
- **Package Architecture (`src/pii_guard`):** Migrated monolithic scripts into a standard package layout (`api.py`, `masking.py`, `dlp.py`, `config.py`, `llm.py`, `logging_config.py`).
- **Declarative Packaging:** Added `pyproject.toml` (PEP 517/621) with editable install support (`pip install -e ".[dev]"`).
- **Centralized Configuration:** Integrated `pydantic-settings` with `.env` loading, `PII_GUARD_` prefix isolation, and secure `SecretStr` handling for `GEMINI_API_KEY`.
- **SDK-Agnostic LLM Client:** Added `LLMClient` wrapper in `llm.py` with singleton caching and lazy runtime key validation to ensure offline/CI testability.
- **Lazy Presidio Analyzer:** Encapsulated Presidio engine in cached `get_analyzer()` function to eliminate cold-start overhead at package import time.
- **Structured JSON Logging:** Implemented zero-dependency `JSONFormatter` writing UTC ISO timestamps, log level, extracted `request_id`, and redacted messages to `logs/security_audit.log`.
- **Quality Assurance & CI:** Added Ruff linting/formatting rules, Mypy static type checking, `.gitattributes` LF normalization, `.pre-commit-config.yaml` with `.env` leak prevention, and automated GitHub Actions CI testing on Python 3.10 and 3.12.
- **Automated Test Expansion:** Expanded test suite from 43 to 56 automated tests with session-scoped Presidio warmup and comprehensive cache resetting.

### Changed
- Replaced root modules `main.py`, `processor.py`, and `dlp_guard.py` with clean imports from `pii_guard.*`.
- Updated server execution entrypoint to `python -m uvicorn pii_guard.api:app --reload`.
- Migrated all changelog entries and error messages to international English.

### Removed
- Removed legacy `requirements.txt` in favor of declarative `pyproject.toml`.
- Removed all import-time side effects (`logs/` directory creation, global `basicConfig`, and eager API key validation).

## [v0.2.0] - 2026-11-18

### Fixed
- **DLP Log Security:** Prevented raw PII (`raw_val`) from being logged in `dlp_guard.py`; restricted logging strictly to entity placeholder, layer name, `request_id`, and SHA-256 hash.
- **Rehydration Ordering:** Moved string replacement logic in `processor.py` to `rehydrate_text`; added regex word boundaries and length-descending sorting to prevent two-digit placeholders like `PERSON_10` from being corrupted by `PERSON_1`.
- **Turkish Character Normalization:** Resolved issue where standard Python `lower()` misses Turkish character variations (`I`/`ı`, `İ`/`i`) using `fold_text`.
- **Phone Layer Tokenization:** Replaced raw concatenated digit search with `_extract_phone_chunks` to prevent unrelated numbers from triggering false positives.
- **HTTP Status Code:** Updated model leak detection response from HTTP 200 plain text to `HTTPException(status_code=403)`.
- **Dynamic Request ID:** Replaced static `"req_123"` with unique `uuid4()` for every request.

### Added
- Added `test_api.py` test suite validating the API endpoint (403 status code and UUID generation).
- Expanded automated test suite to 43 passing tests.

## [v0.1.0] - 2026-11-02

### Added
- Core FastAPI proxy architecture (`main.py`).
- Ingress dynamic anonymization powered by Microsoft Presidio and spaCy (`processor.py`).
- Multi-layer egress data leakage protection (DLP) guard (`dlp_guard.py`).
- MIT License (`LICENSE`).
- Initial automated test suite (28 tests).
