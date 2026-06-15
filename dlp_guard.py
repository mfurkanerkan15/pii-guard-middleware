from processor import analyzer

def check_for_leaks(text: str, mapping: dict):
    results = analyzer.analyze(
        text=text, 
        entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"], 
        language='en',
        score_threshold=0.6
    )
    
    known_clean_values = list(mapping.values())
    
    for res in results:
        found_value = text[res.start:res.end].strip()
        
        if any(tag in found_value for tag in ["PERSON", "LOCATION", "PHONE", "EMAIL"]):
            continue
        
        if found_value in known_clean_values:
            return True 
            
        if len(found_value) <= 2:
            continue
            
        return True
        
    return False