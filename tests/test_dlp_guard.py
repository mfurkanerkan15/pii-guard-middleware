import pytest
from pii_guard.dlp import check_for_leaks


# ==============================================================================
# 1. BÜYÜK / KÜÇÜK HARF (CASE-INSENSITIVITY) TESTLERİ
# ==============================================================================

def test_leak_detected_exact_match():
    """Birebir aynı büyük/küçük harfli sızıntıyı yakalar."""
    mapping = {"PERSON_1": "Furkan Erkan"}
    text = "Merhaba Furkan Erkan, hesabınız güncellendi."
    assert check_for_leaks(text, mapping) is True

def test_leak_detected_all_lowercase():
    """Modelin tamamen küçük harfle sızdırdığı PII'ı yakalar."""
    mapping = {"PERSON_1": "Ahmet Yılmaz"}
    text = "Kullanıcı bilgisi: ahmet yılmaz adına kayıt oluşturuldu."
    assert check_for_leaks(text, mapping) is True

def test_leak_detected_all_uppercase():
    """Modelin tamamen BÜYÜK harfle sızdırdığı PII'ı yakalar."""
    mapping = {"PERSON_1": "Mehmet Demir"}
    text = "İŞLEM YAPILAN KİŞİ: MEHMET DEMİR"
    assert check_for_leaks(text, mapping) is True

def test_leak_detected_mixed_case():
    """Modelin karışık harflerle (mIxEd cAsE) sızdırdığı PII'ı yakalar."""
    mapping = {"PERSON_1": "Canan Dagdeviren"}
    text = "Rapor cAnAn DaGdEvIrEn tarafından incelenmiştir."
    assert check_for_leaks(text, mapping) is True

def test_leak_detected_email_case_insensitive():
    """E-posta adresi büyük/küçük harf varyasyonlarında sızıntıyı yakalar."""
    mapping = {"EMAIL_ADDRESS_1": "Gizli.Proje@Sirket.COM"}
    text = "Lütfen detayları gizli.proje@sirket.com adresine iletin."
    assert check_for_leaks(text, mapping) is True


# ==============================================================================
# 2. KARAKTER VE BOŞLUK AYRIŞTIRMA (OBFUSCATION / BYPASS) TESTLERİ
# ==============================================================================

def test_leak_detected_hyphen_separated():
    """Tire ile ayrılmış (F-u-r-k-a-n) bypass girişimini yakalar."""
    mapping = {"PERSON_1": "Furkan"}
    text = "Gizli isim: F-u-r-k-a-n"
    assert check_for_leaks(text, mapping) is True

def test_leak_detected_space_separated():
    """Her harfi boşlukla ayrılmış (F u r k a n) bypass girişimini yakalar."""
    mapping = {"PERSON_1": "Furkan Erkan"}
    text = "Hedef kişi: F u r k a n E r k a n sistemde bulundu."
    assert check_for_leaks(text, mapping) is True

def test_leak_detected_dot_separated():
    """Nokta ile ayrılmış (A.h.m.e.t) bypass girişimini yakalar."""
    mapping = {"PERSON_1": "Ahmet"}
    text = "Kimlik: A.h.m.e.t"
    assert check_for_leaks(text, mapping) is True

def test_leak_detected_underscore_separated():
    """Alt tire ile ayrılmış (M_e_h_m_e_t) bypass girişimini yakalar."""
    mapping = {"PERSON_1": "Mehmet"}
    text = "Kullanıcı M_e_h_m_e_t onayladı."
    assert check_for_leaks(text, mapping) is True


# ==============================================================================
# 3. TELEFON VE SAYISAL FORMAT NORMALİZASYONU TESTLERİ
# ==============================================================================

def test_phone_leak_international_to_local():
    """Uluslararası formatta (+905551234567) girilen numaranın yerel (0555 123 45 67) sızıntısını yakalar."""
    mapping = {"PHONE_NUMBER_1": "+90 555 123 45 67"}
    text = "Müşterinin telefon numarası: 0555 123 45 67"
    assert check_for_leaks(text, mapping) is True

def test_phone_leak_plain_digits():
    """Parantezli formatlanan numaranın düz rakam (5551234567) sızıntısını yakalar."""
    mapping = {"PHONE_NUMBER_1": "(555) 123-4567"}
    text = "Ulaşılabilecek numara: 5551234567"
    assert check_for_leaks(text, mapping) is True

def test_phone_leak_hyphenated():
    """Düz girilen numaranın tireli (555-123-4567) sızıntısını yakalar."""
    mapping = {"PHONE_NUMBER_1": "5551234567"}
    text = "İletişim: 555-123-4567"
    assert check_for_leaks(text, mapping) is True


# ==============================================================================
# 4. KISMİ İSİM VE TOKEN-LEVEL SIZINTI TESTLERİ
# ==============================================================================

def test_compound_name_partial_surname_leak():
    """Çok kelimeli isimde sadece soyadın ('Yılmaz') sızmasını yakalar."""
    mapping = {"PERSON_1": "Ahmet Furkan Yılmaz"}
    text = "Sayın Yılmaz, başvurunuz onaylanmıştır."
    assert check_for_leaks(text, mapping) is True

def test_compound_name_partial_firstname_leak():
    """Çok kelimeli isimde sadece ilk ismin ('Furkan') sızmasını yakalar."""
    mapping = {"PERSON_1": "Furkan Erkan"}
    text = "Merhaba Furkan Bey, hesabınız aktif edildi."
    assert check_for_leaks(text, mapping) is True

def test_compound_name_middle_name_leak():
    """Çok kelimeli isimde göbek adının ('Serdar') sızmasını yakalar."""
    mapping = {"PERSON_1": "Ali Serdar Kaya"}
    text = "Kullanıcı Serdar sisteme giriş yaptı."
    assert check_for_leaks(text, mapping) is True


# ==============================================================================
# 5. FALSE-POSITIVE (YANLIŞ ALARM) ÖNLEME TESTLERİ
# ==============================================================================

def test_no_false_positive_on_general_world_entities():
    """Modelin ürettiği genel dünya varlıkları (Paris, Albert Einstein) alarm vermemeli."""
    mapping = {"PERSON_1": "Furkan Erkan", "EMAIL_ADDRESS_1": "test@example.com"}
    text = "Paris Fransa'nın başkentidir ve Albert Einstein ünlü bir fizikçidir."
    assert check_for_leaks(text, mapping) is False

def test_no_false_positive_on_masked_placeholders():
    """Model çıktısında yalnızca etiketler (PERSON_1 vb.) varken alarm vermemeli."""
    mapping = {"PERSON_1": "Furkan Erkan", "EMAIL_ADDRESS_1": "test@example.com"}
    text = "Merhaba PERSON_1, size EMAIL_ADDRESS_1 adresi üzerinden doğrulama yollandı."
    assert check_for_leaks(text, mapping) is False

def test_no_false_positive_on_word_substring_boundary():
    """Kelimelerin içindeki harf benzerlikleri (örn: 'Kalite' kelimesindeki 'Ali') tetiklenmemeli."""
    mapping = {"PERSON_1": "Ali Veli"}
    text = "Ürün kalitesi yüksek ve maliyet raporları hazırlandı."
    # 'kalite' veya 'maliyet' içinde 'ali' geçse bile kelime sınırı (\b) sayesinde false-positive olmamalı
    assert check_for_leaks(text, mapping) is False


# ==============================================================================
# 6. KAÇIŞ KARAKTERLERİ, JSON VE ÖZEL FORMAT TESTLERİ
# ==============================================================================

def test_json_escaped_string_leak():
    """JSON formatında kaçış karakterleri içeren sızıntıyı yakalar."""
    mapping = {"PERSON_1": "Furkan Erkan"}
    text = '{\n  "user": "Furkan Erkan",\n  "status": "active"\n}'
    assert check_for_leaks(text, mapping) is True

def test_special_regex_characters_in_name():
    """Regex özel karakterleri içeren isimlerde (Dr. Strange, John (Dev)) patlamadan yakalar."""
    mapping = {"PERSON_1": "Dr. Strange (Marvel)"}
    text = "Kayıt: dr. strange (marvel) odada."
    assert check_for_leaks(text, mapping) is True


# ==============================================================================
# 7. SINIR DURUMLAR (EDGE CASES) VE PERFORMANS TESTLERİ
# ==============================================================================

def test_empty_mapping_and_clean_text():
    """Boş mapping ve temiz metinlerde güvenli şekilde False dönmeli."""
    assert check_for_leaks("Herhangi bir metin", {}) is False
    assert check_for_leaks("", {"PERSON_1": "Furkan Erkan"}) is False
    assert check_for_leaks("", {}) is False

def test_mapping_with_blank_or_invalid_values():
    """Mapping içinde boşluk veya None değerler olduğunda çökmemeli."""
    mapping = {"PERSON_1": "", "EMAIL_ADDRESS_1": "   ", "PHONE_NUMBER_1": None}
    text = "Merhaba dünya, her şey yolunda."
    assert check_for_leaks(text, mapping) is False

def test_multiple_pii_partial_leak():
    """Birden fazla PII içinden sadece bir tanesi sızdığında True dönmeli."""
    mapping = {
        "PERSON_1": "Furkan Erkan",
        "EMAIL_ADDRESS_1": "gizli@sirket.com",
        "PHONE_NUMBER_1": "+905551234567"
    }
    text = "Merhaba PERSON_1, şifreniz gizli@sirket.com adresine iletildi."
    assert check_for_leaks(text, mapping) is True

def test_long_text_performance_and_accuracy():
    """Çok uzun metinlerde (10.000+ karakter) performanslı ve doğru tespit yapmalı."""
    mapping = {"PERSON_1": "Furkan Erkan"}
    filler = "Bu bir sistem log kaydıdır ve normal akış devam etmektedir. " * 200
    long_text_with_leak = filler + "Gizli Kullanıcı: Furkan Erkan " + filler
    
    assert check_for_leaks(long_text_with_leak, mapping) is True

def test_mapping_containing_placeholder_values_ignored():
    """Mapping içinde yanlışlıkla PERSON_1 gibi bir placeholder değeri kalmışsa model bunu kullandığında sızıntı sayılmamalı."""
    mapping = {
        "PERSON_1": "Furkan Erkan",
        "LOCATION_1": "PERSON_1"
    }
    text = "Hello PERSON_1, your request has been received."
    assert check_for_leaks(text, mapping) is False

def test_no_raw_pii_in_logs_on_leak(caplog):
    """Sızıntı tespit edildiğinde loglara ham PII yazılmadığını doğrular."""
    raw_name = "Ahmet Yılmaz"
    mapping = {"PERSON_1": raw_name}
    text = f"Sızdırılan kullanıcı: {raw_name}"

    with caplog.at_level("WARNING"):
        is_leak = check_for_leaks(text, mapping, request_id="REQ_SEC_TEST")

    assert is_leak is True
    # Log kayıtlarında ham PII kesinlikle geçmemeli
    assert raw_name not in caplog.text
    assert "Ahmet" not in caplog.text
    assert "Yılmaz" not in caplog.text


def test_turkish_normalization_yilmaz_variations():
    """YILMAZ, Yılmaz, yilmaz varyasyonlarının sızıntı olarak yakalandığını doğrular."""
    mapping = {"PERSON_1": "Yılmaz"}
    # Model BÜYÜK harfle Türkçe karakter kullanarak veya İngilizce I ile sızdırıyor
    assert check_for_leaks("Kullanıcı adı: YILMAZ", mapping) is True
    assert check_for_leaks("Kullanıcı adı: yilmaz", mapping) is True
    assert check_for_leaks("Kullanıcı adı: Yılmaz", mapping) is True

def test_turkish_normalization_ismail_variations():
    """İSMAİL, Ismail varyasyonlarının İ/i çakışmasına takılmadan yakalandığını doğrular."""
    mapping = {"PERSON_1": "İsmail"}
    assert check_for_leaks("Kişi: İSMAİL", mapping) is True
    assert check_for_leaks("Kişi: Ismail", mapping) is True
    assert check_for_leaks("Kişi: ismail", mapping) is True

def test_phone_unrelated_scattered_digits_no_false_alarm():
    """Metne dağılmış alakasız küçük rakamların telefon sızıntısı gibi yanlış alarm üretmediğini doğrular."""
    mapping = {"PHONE_NUMBER_1": "+90 555 123 4567"}
    # Metin içine dağılmış sayılar: 2024, 555, 123, 4567
    text = "2024 yılında toplam 555 müşteriye ulaşıldı, 123 tanesi olumlu döndü ve 4567 işlem tamamlandı."
    assert check_for_leaks(text, mapping) is False


# ==============================================================================
# 8. GÜVENLİK, LOGLAMA VE TÜRKÇE V0.2.0 İLERİ DÜZEY TESTLERİ
# ==============================================================================

def test_dlp_layers_do_not_log_pii_or_hash(caplog):
    """Her DLP katmanında (1, 2, 3, 4) sızıntı olduğunda loglarda ham PII ve Hash geçmediğini doğrular."""
    from unittest.mock import patch
    import pii_guard.dlp as dlp_guard

    # Katman 1: Doğrudan eşleşme
    with caplog.at_level("WARNING"):
        caplog.clear()
        assert check_for_leaks("Gizli isim: Mehmet Yılmaz", {"PERSON_1": "Mehmet Yılmaz"}, request_id="REQ_L1") is True
        assert "Mehmet" not in caplog.text
        assert "Yılmaz" not in caplog.text
        assert "Hash:" not in caplog.text

    # Katman 2: Obfuscation
    with caplog.at_level("WARNING"):
        caplog.clear()
        assert check_for_leaks("Gizli kod: F-u-r-k-a-n", {"PERSON_1": "Furkan"}, request_id="REQ_L2") is True
        assert "Furkan" not in caplog.text
        assert "Hash:" not in caplog.text

    # Katman 3: Telefon
    with caplog.at_level("WARNING"):
        caplog.clear()
        assert check_for_leaks("Arayın: 05551234567", {"PHONE_NUMBER_1": "+905551234567"}, request_id="REQ_L3") is True
        assert "5551234567" not in caplog.text
        assert "Hash:" not in caplog.text

    # Katman 4: Kısmi isim
    with caplog.at_level("WARNING"):
        caplog.clear()
        assert check_for_leaks("Merhaba Serdar bey", {"PERSON_1": "Ali Serdar Kaya"}, request_id="REQ_L4") is True
        assert "Ali" not in caplog.text
        assert "Serdar" not in caplog.text
        assert "Kaya" not in caplog.text
        assert "Hash:" not in caplog.text

    # Katman 5 hata loglama: sadece hata sınıfı tipi loglanmalı, exception mesaj detayı değil
    with caplog.at_level("ERROR"):
        caplog.clear()
        with patch.object(dlp_guard.analyzer, "analyze", side_effect=RuntimeError("very_secret_error_detail")):
            check_for_leaks("Metin", {"PERSON_1": "Ahmet"})
        assert "RuntimeError" in caplog.text
        assert "very_secret_error_detail" not in caplog.text


def test_phone_leak_space_separated_single_digits():
    """Tek tek boşlukla ayrılmış rakamlar (5 5 5 1 2 3 4 5 6 7) telefon sızıntısı olarak yakalanmalı."""
    mapping = {"PHONE_NUMBER_1": "+90 555 123 4567"}
    text = "İletişim numarası: 5 5 5 1 2 3 4 5 6 7"
    assert check_for_leaks(text, mapping) is True


def test_phone_unrelated_room_floor_year_no_false_alarm():
    """'Oda 555, kat 12, 2024 yılı' gibi alakasız sayılar telefon alarmı üretmemeli."""
    mapping = {"PHONE_NUMBER_1": "+90 555 123 4567"}
    text = "Oda 555, kat 12, 2024 yılı toplantısı yapıldı."
    assert check_for_leaks(text, mapping) is False


def test_turkish_layer2_furkan_obfuscation_upper():
    """Mapping 'Furkan' için 'F-U-R-K-A-N' sızıntısı Katman 2 ile yakalanmalı."""
    mapping = {"PERSON_1": "Furkan"}
    assert check_for_leaks("Hedef: F-U-R-K-A-N", mapping) is True


def test_turkish_layer4_ismail_celik_partial_leaks():
    """Mapping 'İsmail Çelik' için 'ISMAIL' ve 'ÇELİK' ayrı ayrı Katman 4 ile yakalanmalı."""
    mapping = {"PERSON_1": "İsmail Çelik"}
    assert check_for_leaks("Kullanıcı ISMAIL odaya girdi.", mapping) is True
    assert check_for_leaks("Kullanıcı ÇELİK odaya girdi.", mapping) is True
