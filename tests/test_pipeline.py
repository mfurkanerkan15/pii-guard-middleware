import sys
import os

# Proje ana dizinini Python yoluna ekler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from processor import process_and_mask_dynamic

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