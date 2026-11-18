# Changelog

Bu projedeki tüm önemli değişiklikler bu dosyada belgelenmektedir.

Biçim [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına dayanır.

## [v0.2.0] - 2026-11-18

### Düzeltilenler
- **DLP Log Güvenliği:** `dlp_guard.py` içinde loglara ham PII (`raw_val`) yazılması engellendi; loglama yalnızca placeholder, katman adı, `request_id` ve SHA-256 hash ile sınırlandırıldı.
- **Rehidrasyon Sıralaması:** `processor.py` içindeki string değiştirme mantığı `rehydrate_text` fonksiyonuna taşındı; `PERSON_1` etiketinin `PERSON_10` gibi iki basamaklı etiketleri bozmasını önlemek için regex sınırları ve uzunluğa göre azalan sıralama eklendi.
- **Türkçe Karakter Normalizasyonu:** Python standart `lower()` fonksiyonunun Türkçe karakterlerde (`I`/`ı`, `İ`/`i`) eşleşme kaçırması `fold_text` fonksiyonu ile giderildi.
- **Telefon Katmanı Ayrıştırması:** Metindeki tüm rakamların birleştirilerek aranması yerine `_extract_phone_chunks` ile rakam öbekleri ayrı ayrı çıkarılarak alakasız metin içi sayıların yanlış alarm üretmesi önlendi.
- **HTTP Durum Kodu:** Model çıktısında sızıntı tespit edildiğinde dönen HTTP 200 düz metin yanıtı `HTTPException(status_code=403)` olarak güncellendi.
- **Dinamik İstek Kimliği:** Sabit `"req_123"` yerine her istek için `uuid4()` üretilmesi sağlandı.

### Eklenenler
- API uç noktasını (403 hata kodu ve UUID kontrolü) doğrulayan `test_api.py` test paketi eklendi.
- Toplam otomatik test sayısı 43'e çıkarıldı.

## [v0.1.0] - 2026-11-02

### Eklenenler
- Temel FastAPI proxy mimarisi (`main.py`).
- Microsoft Presidio ve spaCy tabanlı giriş anonimleştirme (`processor.py`).
- Çok katmanlı çıkış denetleyicisi (`dlp_guard.py`).
- MIT Lisansı (`LICENSE`).
- İlk test paketi (28 test).

