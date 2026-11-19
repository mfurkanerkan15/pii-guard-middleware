import logging
import re
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine

PLACEHOLDER_PATTERN = re.compile(r"^(PERSON|LOCATION|PHONE_NUMBER|EMAIL_ADDRESS)_\d+$")

logger = logging.getLogger(__name__)


@lru_cache
def get_analyzer() -> AnalyzerEngine:
    """Presidio AnalyzerEngine'i tembel (lazy) olarak bir kez oluşturur."""
    return AnalyzerEngine()


def process_and_mask_dynamic(text: str, request_id: str = "N/A"):
    analyzer = get_analyzer()
    results = analyzer.analyze(
        text=text, entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"], language="en"
    )

    # Prompt içinde önceden yer alan placeholder etiketlerini (PERSON_1 vb.) filtrele
    valid_results = [
        res for res in results if not PLACEHOLDER_PATTERN.match(text[res.start : res.end].strip())
    ]

    forward_results = sorted(valid_results, key=lambda x: x.start)

    mapping: dict[str, str] = {}
    counters: dict[str, int] = {}
    value_to_placeholder: dict[str, str] = {}

    for res in forward_results:
        original_value = text[res.start : res.end]
        entity_type = res.entity_type

        if original_value not in value_to_placeholder:
            counters[entity_type] = counters.get(entity_type, 0) + 1
            placeholder = f"{entity_type}_{counters[entity_type]}"
            value_to_placeholder[original_value] = placeholder

    sorted_results = sorted(valid_results, key=lambda x: x.start, reverse=True)
    masked_text = text

    for res in sorted_results:
        start = res.start
        end = res.end
        original_value = text[start:end]
        placeholder = value_to_placeholder[original_value]

        # Hafızaya tersine eşleme için kaydet
        mapping[placeholder] = original_value
        # Maskeleme
        masked_text = masked_text[:start] + placeholder + masked_text[end:]

    entity_types = sorted(list(set(res.entity_type for res in valid_results)))
    logger.info(
        f"{request_id} | Giriş maskeleme tamamlandı | Varlık Sayısı: {len(valid_results)} | Tipler: {entity_types}"
    )

    return masked_text, mapping


def rehydrate_text(text: str, mapping: dict) -> str:
    """
    LLM çıktısındaki placeholder etiketlerini orijinal hassas verilerle geri değiştirir.
    Prefix çakışmalarını (örn. PERSON_10'un PERSON_1 tarafından kısmen bozulmasını)
    engellemek için regex word boundary ve uzunluğa göre azalan sıralama kullanır.
    """
    if not text or not mapping:
        return text

    sorted_placeholders = sorted(mapping.keys(), key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(p) for p in sorted_placeholders) + r")\b")
    return pattern.sub(lambda m: mapping.get(m.group(0), m.group(0)), text)
