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

def process_and_mask_dynamic(text: str, request_id: str):
    results = analyzer.analyze(
        text=text, 
        entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"], 
        language='en'
    )

    forward_results = sorted(results, key=lambda x: x.start)
    
    mapping = {}
    counters = {}
    value_to_placeholder = {} # Aynı kelimeye hep aynı etiketi vermek için

    for res in forward_results:
        original_value = text[res.start:res.end]
        entity_type = res.entity_type
        
        if original_value not in value_to_placeholder:
            counters[entity_type] = counters.get(entity_type, 0) + 1
            placeholder = f"{entity_type}_{counters[entity_type]}"
            value_to_placeholder[original_value] = placeholder

    sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
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
    
    #logging.info(f"{request_id} - Original: {text} | Masked: {masked_text} | Mapping: {mapping}")
    
    return masked_text, mapping