import sys
import os

# Proje ana dizinini Python yoluna ekler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from processor import process_and_mask_dynamic, rehydrate_text

def test_ingress_masking():
    sample_text = "Hello, my name is Furkan Erkan and my email is test@example.com"
    masked_text, mapping = process_and_mask_dynamic(sample_text, request_id="TEST_001")
    
    # Orijinal hassas veriler metinden temizlenmeli
    assert "Furkan Erkan" not in masked_text
    assert "test@example.com" not in masked_text
    
    # Maskeleme etiketleri yerleşmeli
    assert "PERSON_1" in masked_text
    assert "EMAIL_ADDRESS_1" in masked_text
    
    # Mapping orijinal değerleri doğru tutmalı
    assert mapping.get("PERSON_1") == "Furkan Erkan"
    assert mapping.get("EMAIL_ADDRESS_1") == "test@example.com"

def test_no_pii_intact():
    sample_text = "This is a standard system message without sensitive data."
    masked_text, mapping = process_and_mask_dynamic(sample_text, request_id="TEST_002")
    
    # PII yoksa metin bozulmamalı ve harita boş dönmeli
    assert masked_text == sample_text
    assert len(mapping) == 0

def test_pre_existing_placeholder_not_remasked():
    """Kullanıcı prompt'u içinde önceden PERSON_1 gibi etiketler varsa bunlar tekrar maskelenmemeli."""
    sample_text = "Hello, my name is Furkan Erkan. Please do not use PERSON_1 in your answer."
    masked_text, mapping = process_and_mask_dynamic(sample_text, request_id="TEST_003")
    
    # PERSON_1 etiketi yeni bir entity gibi tekrar maskelenmemeli
    assert "Furkan Erkan" not in masked_text
    assert mapping.get("PERSON_1") == "Furkan Erkan"
    assert "PERSON_1" not in mapping.values()

def test_rehydration_with_more_than_ten_entities():
    """PERSON_10+ olduğunda PERSON_1'in PERSON_10'u bozmadığını doğrular."""
    mapping = {f"PERSON_{i}": f"User_{i}" for i in range(1, 15)}
    text = "Meeting attendees: " + ", ".join(f"PERSON_{i}" for i in range(1, 15))
    
    rehydrated = rehydrate_text(text, mapping)
    
    for i in range(1, 15):
        assert f"User_{i}" in rehydrated
    assert "PERSON_" not in rehydrated

    # Özellikle PERSON_1 ve PERSON_10 çakışma kontrolü
    mapping_collision = {"PERSON_1": "Ahmet", "PERSON_10": "Mehmet"}
    sample = "Katılımcılar: PERSON_10 ve PERSON_1."
    result = rehydrate_text(sample, mapping_collision)
    assert result == "Katılımcılar: Mehmet ve Ahmet."
    assert "Ahmet0" not in result


def test_process_and_mask_does_not_log_masked_text_or_pii(caplog):
    """process_and_mask_dynamic loglarında ham PII ve maskelenmiş metin olmamalı, sadece sayı/tipler loglanmalı."""
    import logging
    with caplog.at_level(logging.INFO):
        masked_text, mapping = process_and_mask_dynamic(
            "Hello, my name is Furkan Erkan and email is secret@corp.com",
            request_id="REQ_MASK_LOG_TEST"
        )
    assert "Furkan Erkan" not in caplog.text
    assert "secret@corp.com" not in caplog.text
    assert "Masked:" not in caplog.text
    assert "Varlık Sayısı:" in caplog.text or "Count:" in caplog.text
