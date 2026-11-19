import logging
import re
import unicodedata

from pii_guard.config import get_settings
from pii_guard.masking import get_analyzer


def fold_text(text: str) -> str:
    """
    Unicode (NFKC) normalizasyonu, Türkçe büyük harf ön eşlemesi (İ->i, I->ı),
    casefold() ve Türkçe karakter katlama (ı->i, ş->s, ğ->g, ü->u, ö->o, ç->c)
    uygular.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(str.maketrans({"İ": "i", "I": "ı"}))
    text = text.casefold()
    return text.translate(
        str.maketrans({"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c"})
    )


def _normalize_text(text: str) -> str:
    """Metni Türkçe ve Unicode uyumlu katlar ve ardışık boşlukları tek boşluğa indirger."""
    return re.sub(r"\s+", " ", fold_text(text)).strip()


def _extract_digits(text: str) -> str:
    """Metindeki yalnızca rakamları çeker."""
    return re.sub(r"\D", "", text)


def _strip_separators(text: str) -> str:
    """Tüm boşluk ve noktalama işaretlerini kaldırarak sadece harf ve rakamları bırakır."""
    return re.sub(r"[\W_]+", "", fold_text(text), flags=re.UNICODE)


def _extract_phone_chunks(text: str) -> list[str]:
    """
    Metindeki telefon veya sayı dizisi öbeklerini (boşluk, tire, nokta, parantez veya + ile ayrılmış)
    ayıklar ve her bir öbeğin yalnızca rakamlarını döner.
    En az 7 haneli rakam gruplarını filtreleyerek metne dağılmış bağımsız sayıların
    yanlış alarm üretmesini engeller.
    """
    raw_chunks = re.findall(r"(?:\+?\d[\d\s\-\.\(\)/]{5,}\d|\b\d{7,}\b)", text)
    cleaned_chunks = []
    for c in raw_chunks:
        digits = re.sub(r"\D", "", c)
        if len(digits) >= 7:
            cleaned_chunks.append(digits)
    return cleaned_chunks


def check_for_leaks(
    text: str,
    mapping: dict,
    request_id: str = "N/A",
    token_min_len: int | None = None,
    dlp_ner_enabled: bool | None = None,
    ner_score_threshold: float | None = None,
) -> bool:
    """
    Zero-Trust DLP Çıkış Denetleyicisi (Production-Grade):
    LLM çıktısında kullanıcının orijinal PII verilerinin (veya bunların türevlerinin/parçalarının)
    sızıp sızmadığını çok katmanlı normalizasyon ve regex ile denetler.

    Katmanlar:
    1. Case-Insensitive & Türkçe Uyumlu Doğrudan Eşleşme (Ahmet Yılmaz <-> ahmet yılmaz)
    2. Obfuscation / Ayrıştırma Engelleme (A-h-m-e-t, F u r k a n)
    3. Sayısal / Telefon Format Normalizasyonu (+90 555 123 4567 <-> 05551234567)
    4. Kısmi / Token-Level İsim Tespiti ("Ahmet Furkan Yılmaz" -> "Furkan Yılmaz")
    5. Harici Varlık Gözlemi (Paris, Einstein vb. bloklanmaz, telemetri için loglanır)
    """
    if not text or not mapping:
        return False

    settings = get_settings()
    if token_min_len is None:
        token_min_len = settings.token_min_len
    if dlp_ner_enabled is None:
        dlp_ner_enabled = settings.dlp_ner_enabled
    if ner_score_threshold is None:
        ner_score_threshold = settings.ner_score_threshold

    text_norm = _normalize_text(text)
    text_clean = _strip_separators(text)
    phone_chunks = _extract_phone_chunks(text)

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
                f"{request_id} | SIZINTI TESPİT EDİLDİ (Katman 1 - Doğrudan Eşleşme) | Placeholder: {placeholder}"
            )
            return True

        # 2. Katman: Obfuscation / Noktalama & Boşluk Ayırma Engelleme (Ör: A-h-m-e-t, F u r k a n)
        if len(val_clean) >= 4 and val_clean in text_clean:
            logging.warning(
                f"{request_id} | SIZINTI TESPİT EDİLDİ (Katman 2 - Obfuscation / Ayrıştırma) | Placeholder: {placeholder}"
            )
            return True

        # 3. Katman: Sayısal / Telefon / Kimlik Format Normalizasyonu (Ör: +90 555 123 4567 -> 5551234567)
        if len(val_digits) >= 7:
            core_digits = val_digits[-10:] if len(val_digits) >= 10 else val_digits
            for chunk_digits in phone_chunks:
                chunk_core = chunk_digits[-10:] if len(chunk_digits) >= 10 else chunk_digits
                if (
                    core_digits in chunk_digits
                    or val_digits in chunk_digits
                    or (len(chunk_core) >= 10 and chunk_core in val_digits)
                    or chunk_digits == core_digits
                ):
                    logging.warning(
                        f"{request_id} | SIZINTI TESPİT EDİLDİ (Katman 3 - Sayısal / Telefon Formatı) | Placeholder: {placeholder}"
                    )
                    return True

        # 4. Katman: Kelime Bazlı / Parçalı İsim Tespiti (Yalnızca PERSON varlıkları için)
        if placeholder.startswith("PERSON"):
            tokens = [t for t in re.split(r"\s+", val_norm) if len(t) >= token_min_len]
            if len(re.split(r"\s+", val_norm)) > 1:
                for token in tokens:
                    pattern = rf"\b{re.escape(token)}\b"
                    if re.search(pattern, text_norm):
                        logging.warning(
                            f"{request_id} | SIZINTI TESPİT EDİLDİ (Katman 4 - Kısmi İsim Sızıntısı) | Placeholder: {placeholder}"
                        )
                        return True

    # 5. Katman: Telemetri & Bilgi Amaçlı Varlık Analizi (Bloklama yapmaz)
    if dlp_ner_enabled:
        try:
            results = get_analyzer().analyze(
                text=text,
                entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"],
                language="en",
                score_threshold=ner_score_threshold,
            )

            for res in results:
                found_value = text[res.start : res.end].strip()

                # Placeholder etiketlerini atla
                if any(tag in found_value for tag in ["PERSON", "LOCATION", "PHONE", "EMAIL"]):
                    continue

                logging.info(
                    f"{request_id} | Model çıktısında harici varlık gözlendi (Katman 5 - Telemetri) | Tip: {res.entity_type}"
                )
        except Exception as e:
            logging.error(f"{request_id} | DLP analiz sırasında hata oluştu: {type(e).__name__}")

    return False
