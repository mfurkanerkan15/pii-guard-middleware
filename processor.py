import re
import logging
import os
from presidio_analyzer import AnalyzerEngine


if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/security_audit.log',
    level=logging.INFO,
    format='%(asctime)s - ID: %(message)s'
)

analyzer = AnalyzerEngine()
PLACEHOLDER_PATTERN = re.compile(r"^(PERSON|LOCATION|PHONE_NUMBER|EMAIL_ADDRESS)_\d+$")

def process_and_mask_dynamic(text: str, request_id: str = "N/A"):
    results = analyzer.analyze(
        text=text, 
        entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"], 
        language='en'
    )

    # Prompt içinde önceden yer alan placeholder etiketlerini (PERSON_1 vb.) filtrele
    valid_results = [
        res for res in results 
        if not PLACEHOLDER_PATTERN.match(text[res.start:res.end].strip())
    ]

    forward_results = sorted(valid_results, key=lambda x: x.start)
    
    mapping = {}
    counters = {}
    value_to_placeholder = {} 

    for res in forward_results:
        original_value = text[res.start:res.end]
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

    logging.info(f"{request_id} | Masked: {masked_text}")
    
    return masked_text, mapping