import sys
import os
import uuid
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from main import handle_request

# TODO (v0.3.0): Async event loop ve HTTP entegrasyonu conftest.py ve TestClient üzerinden koordine edilecek.
def _run_coroutine(coro):
    """Event loop gerektirmeyen coroutine'leri doğrudan senkron yürütür."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value

def test_leak_raises_http_exception_403(monkeypatch):
    """Model çıktısında PII sızıntısı olduğunda HTTPException(status_code=403) fırlatılmalı."""
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value.generate_content.return_value = MagicMock(text="Sızdırılan model çıktısı")
    monkeypatch.setattr(main, "genai", mock_genai)
    
    monkeypatch.setattr(main, "process_and_mask_dynamic", lambda text, req_id: ("PERSON_1", {"PERSON_1": "Test User"}))
    monkeypatch.setattr(main, "check_for_leaks", lambda text, mapping, req_id: True)

    with pytest.raises(HTTPException) as exc_info:
        _run_coroutine(handle_request(user_input="Test prompt"))

    assert exc_info.value.status_code == 403
    assert "Blocked" in exc_info.value.detail

def test_request_id_is_uuid(monkeypatch):
    """Her istekte sabit req_123 yerine rastgele ve geçerli bir UUID4 üretilmeli."""
    captured_request_ids = []

    def mock_process_and_mask(text, request_id="N/A"):
        captured_request_ids.append(request_id)
        return text, {}

    monkeypatch.setattr(main, "process_and_mask_dynamic", mock_process_and_mask)
    monkeypatch.setattr(main, "check_for_leaks", lambda text, mapping, req_id: False)

    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value.generate_content.return_value = MagicMock(text="Cevap metni.")
    monkeypatch.setattr(main, "genai", mock_genai)

    response = _run_coroutine(handle_request(user_input="Normal prompt"))
    assert "ZERO-TRUST" in response
    assert len(captured_request_ids) == 1
    req_id = captured_request_ids[0]

    # UUID4 formatında olduğunu doğrula
    parsed_uuid = uuid.UUID(req_id, version=4)
    assert str(parsed_uuid) == req_id


def test_api_real_pipeline_leak_blocks_and_hides_raw_value(monkeypatch):
    """Gerçek check_for_leaks ile model ham PII sızdırdığında 403 dönmeli ve detail'de ham değer olmamalı."""
    raw_name = "Furkan Erkan"
    user_prompt = f"Merhaba, benim adım {raw_name}"

    # Sadece genai mock'lanır; check_for_leaks ve rehydrate_text GERÇEKTİR
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value.generate_content.return_value = MagicMock(
        text=f"Model sızıntı yaptı: {raw_name} sisteme eklendi."
    )
    monkeypatch.setattr(main, "genai", mock_genai)

    with pytest.raises(HTTPException) as exc_info:
        _run_coroutine(handle_request(user_input=user_prompt))

    assert exc_info.value.status_code == 403
    assert "Blocked" in exc_info.value.detail
    # HTTPException.detail içinde ham hassas değer kesinlikle bulunmamalı
    assert raw_name not in exc_info.value.detail
    assert "Furkan" not in exc_info.value.detail


def test_api_real_pipeline_rehydration_success_ten_plus_entities(monkeypatch):
    """Gerçek rehydrate_text ile 10+ varlıkta PERSON_1 ve PERSON_10 karışmadan doğru geri yazılmalı."""
    names_prompt = (
        "Meeting with Alice Smith, Bob Jones, Charlie Brown, David Miller, "
        "Eve Davis, Frank Wilson, Grace Taylor, Heidi Clark, Ivan White, "
        "Judy Hall, Kevin Lewis."
    )

    # Model sadece placeholder içeren temiz yanıt döndürsün
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value.generate_content.return_value = MagicMock(
        text="Attending: PERSON_1 and PERSON_10 will lead the discussion."
    )
    monkeypatch.setattr(main, "genai", mock_genai)

    response = _run_coroutine(handle_request(user_input=names_prompt))
    assert "ZERO-TRUST" in response
    assert "Blocked" not in response

    # PERSON_1 (Alice Smith) ve PERSON_10 (Judy Hall) doğru rehidre edilmeli
    # PERSON_1, PERSON_10'u bozup "Alice Smith0" yapmamalı
    assert "Alice Smith0" not in response
    assert "Alice Smith and Judy Hall will lead the discussion" in response
