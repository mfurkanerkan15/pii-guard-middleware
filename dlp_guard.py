import re
import logging
from processor import analyzer

def _normalize_text(text: str) -> str:
    """Metni küçük harfe çevirir ve ardışık boşlukları tek boşluğa indirger."""
    return re.sub(r'\s+', ' ', text.lower()).strip()

def _extract_digits(text: str) -> str:
    """Metindeki yalnızca rakamları çeker."""
    return re.sub(r'\D', '', text)

def _strip_separators(text: str) -> str:
    """Tüm boşluk ve noktalama işaretlerini kaldırarak sadece harf ve rakamları bırakır."""
    return re.sub(r'[\W_]+', '', text.lower(), flags=re.UNICODE)

def check_for_leaks(
    text: str, 
    mapping: dict, 
    request_id: str = "N/A", 
    token_min_len: int = 4
) -> bool:
    """
    Zero-Trust DLP Çıkış Denetleyicisi (Production-Grade):
    LLM çıktısında kullanıcının orijinal PII verilerinin (veya bunların türevlerinin/parçalarının)
    sızıp sızmadığını çok katmanlı normalizasyon ve regex ile denetler.

    Katmanlar:
    1. Case-Insensitive Doğrudan Eşleşme (Ahmet Yılmaz <-> ahmet yılmaz)
    2. Obfuscation / Ayrıştırma Engelleme (A-h-m-e-t, F u r k a n)
    3. Sayısal / Telefon Format Normalizasyonu (+90 555 123 4567 <-> 05551234567)
    4. Kısmi / Token-Level İsim Tespiti ("Ahmet Furkan Yılmaz" -> "Furkan Yılmaz")
    5. Harici Varlık Gözlemi (Paris, Einstein vb. bloklanmaz, telemetri için loglanır)
    """
    if not text or not mapping:
        return False

    text_norm = _normalize_text(text)
    text_clean = _strip_separators(text)
    text_digits = _extract_digits(text)

    PLACEHOLDER_REGEX = re.compile(r"^(PERSON|LOCATION|PHONE_NUMBER|EMAIL_ADDRESS)_\d+$")

    for placeholder, original_val in mapping.items():
        if not original_val or not isinstance(original_val, str) or not original_val.strip():
            continue

        raw_val = original_val.strip()
        if PLACEHOLDER_REGEX.match(raw_val):
            continue

        val_norm = _normalize_text(raw_val)
        val_clean = _strip_separators(raw_val)
        val_digits = _extract_digits(raw_val)

        # 1. Katman: Doğrudan & Büyük/Küçük Harf (Case-Insensitive) Eşleşmesi
        if val_norm in text_norm:
            logging.warning(
                f"{request_id} | SIZINTI TESPİT EDİLDİ (Doğrudan Eşleşme): '{raw_val}' ({placeholder})"
            )
            return True

        # 2. Katman: Obfuscation / Noktalama & Boşluk Ayırma Engelleme (Ör: A-h-m-e-t, F u r k a n)
        if len(val_clean) >= 4 and val_clean in text_clean:
            logging.warning(
                f"{request_id} | SIZINTI TESPİT EDİLDİ (Karakter/Boşluk Ayrıştırma): '{raw_val}' ({placeholder})"
            )
            return True

        # 3. Katman: Sayısal / Telefon / Kimlik Format Normalizasyonu (Ör: +90 555 123 4567 -> 5551234567)
        if len(val_digits) >= 7:
            core_digits = val_digits[-10:] if len(val_digits) >= 10 else val_digits
            if core_digits in text_digits or val_digits in text_digits:
                logging.warning(
                    f"{request_id} | SIZINTI TESPİT EDİLDİ (Sayısal/Telefon Formatı): '{raw_val}' ({placeholder})"
                )
                return True

        # 4. Katman: Kelime Bazlı / Parçalı İsim Tespiti (Yalnızca PERSON varlıkları için)
        # Ör: "Ahmet Furkan Yılmaz" -> "Furkan" veya "Yılmaz" (LOCATION vb. varlıklardaki genel kelimeleri ayırmaz)
        if placeholder.startswith("PERSON"):
            tokens = [t for t in re.split(r'\s+', val_norm) if len(t) >= token_min_len]
            if len(re.split(r'\s+', val_norm)) > 1:
                for token in tokens:
                    pattern = rf"\b{re.escape(token)}\b"
                    if re.search(pattern, text_norm, re.IGNORECASE):
                        logging.warning(
                            f"{request_id} | SIZINTI TESPİT EDİLDİ (Kısmi İsim Sızıntısı): '{token}' in '{raw_val}' ({placeholder})"
                        )
                        return True

    # 5. Katman: Telemetri & Bilgi Amaçlı Varlık Analizi (Bloklama yapmaz)
    try:
        results = analyzer.analyze(
            text=text, 
            entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"], 
            language='en',
            score_threshold=0.6
        )
        
        for res in results:
            found_value = text[res.start:res.end].strip()
            
            # Placeholder etiketlerini atla
            if any(tag in found_value for tag in ["PERSON", "LOCATION", "PHONE", "EMAIL"]):
                continue
                
            logging.info(
                f"{request_id} | Model çıktısında harici varlık gözlendi (sızıntı değil): '{found_value}' ({res.entity_type})"
            )
    except Exception as e:
        logging.error(f"{request_id} | DLP analiz sırasında hata oluştu: {e}")

    return False