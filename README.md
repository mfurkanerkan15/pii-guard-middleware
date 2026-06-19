## Zero-Trust LLM Veri Güvenliği Katmanı

Bu proje, Kullanıcılar ile Büyük Dil Modelleri (LLM) arasında konumlanan, **"Veri Minimalizmi"** ve **"Sıfır Güven" (Zero-Trust)** prensipleriyle çalışan çift katmanlı bir siber güvenlik proxy/middleware yazılımıdır. Kullanıcı verilerinin yapay zeka modelleri tarafından "öğrenilmesini", bulut sunucularında depolanmasını ve model çıktılarından üçüncü şahıslara sızmasını (**Data Leakage / PII Exfiltration**) engeller.

## Öne Çıkan Özellikler

- **Dinamik Giriş Güvenliği (Ingress Masking):** Kullanıcı girdisindeki hassas verileri (PII: İsim, Telefon, E-posta, Konum) Microsoft Presidio (NLP tabanlı Adlandırılmış Varlık Tanıma - NER) ile yapay zeka modeline gitmeden önce yakalar ve dinamik yer tutucularla (`PERSON_1`, `LOCATION_1`) maskeler.
- **Gelişmiş Durum Yönetimi (State Mapping):** Metin içindeki mükerrer hassas verileri hafıza haritasında eşleştirerek tutarlı etiketleme sağlar ve karakter kaymalarını (index shifting) önlemek için çift yönlü sıralama algoritması kullanır.
- **DLP Guard ile Çıkış Güvenliği (Egress Inspection):** Modelin ürettiği yanıtları kullanıcıya ulaşmadan önce denetler. Modelin prompt injection saldırılarıyla kırılması veya halüsinasyon görmesi durumunda, orijinal hassas verileri dışarı sızdırma girişimlerini anlık olarak tespit edip isteği bloklar.
- **Kıyaslamalı Akış Raporu:** Her istek sonucunda verinin orijinal halini, maskelenmiş halini, modelin ham cevabını ve unmasked halini gösteren şeffaf bir denetim raporu üretir.
- **Güvenlik Günlüğü (Audit Logging):** Tüm maskeleme ve proxy hareketlerini `logs/security_audit.log` dosyasında kriptik denetim izleri olarak saklar.

---

## Çalışma Mimarisi (Data Flow)

1. **User Prompt** ➡️ `Muhammed Furkan Erkan, İstanbul'da yaşıyor.`
2. **Ingress (Presidio NER)** ➡️ PII tespiti ve dinamik mapping oluşturulması.
3. **LLM Payload** ➡️ `PERSON_1, LOCATION_1'da yaşıyor.` (Modele giden güvenli metin)
4. **LLM Response Evaluation** ➡️ Model çıktısı `dlp_guard` tarafından taranır. Sızıntı yoksa onaylanır.
5. **Egress (Unmasking)** ➡️ `PERSON_1` -> `Muhammed Furkan Erkan` değişimi yapılarak kullanıcıya temiz çıktı dönülür.

---

## Kurulum ve Çalıştırma

## Gereksinimler
- Python 3.10+
- Gemini API Anahtarı

## Adımlar

1. Sanal ortamı başlatın: `python -m venv venv`
2. Gereksinimleri yükleyin: `pip install -r requirements.txt`
3. Dil modelini indirin  `python -m spacy download en_core_web_sm`
4. Proje kök dizininde yer alan `.env.example` dosyasının adını `.env` olarak değiştirin. Ardından Gemini API anahtarınızı yapıştırın.
5. Uygulamayı çalıştırın: `python -m uvicorn main:app --reload`
6. `http://127.0.0.1:8000/docs` üzerinden Swagger arayüzüne erişin.
7. Post isteği altında 'Try it out' basın ve örnek promtları execute edin.

---

## Örnekler

"My name is Furkan Erkan, I live in Istanbul and my phone number is 0555 123 44 55. What can you tell me about myself?"

"Please send the confidential project report to deneme@deneme.com or call me at 0500 999 88 77."

"My phone number is 0555 123 44 55. Remember this. Now, can you remind me what my phone number is?"
