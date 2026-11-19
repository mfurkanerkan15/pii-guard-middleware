# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
