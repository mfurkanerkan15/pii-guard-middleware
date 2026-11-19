import os
import uuid
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import PlainTextResponse
from pii_guard.masking import process_and_mask_dynamic, rehydrate_text
from pii_guard.dlp import check_for_leaks


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("HATA: .env dosyasında 'GEMINI_API_KEY' bulunamadı!")

genai.configure(api_key=api_key)

app = FastAPI(title="Zero-Trust LLM Veri Güvenliği Katmanı")

@app.post("/process", response_class=PlainTextResponse)
async def handle_request(user_input: str = Body(..., media_type="text/plain")):
    request_id = str(uuid.uuid4())

    # 1. Giriş Güvenliği: Dinamik Maskeleme yapılıyor
    masked_text, mapping = process_and_mask_dynamic(user_input, request_id)

    # 2. LLM Ayarları ve İngilizce Sistem Talimatı
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=(
            "You are an assistant working behind a secure proxy. "
            "You will see placeholders like PERSON_1, PERSON_2 in the input text. "
            "DO NOT transform, translate, or change these placeholders into real names or values. "
            "Keep them EXACTLY as they are in your response, and treat them as if they are the actual names."
        )
    )
    
    # Modele maskelenmiş metni gönderiyoruz
    response = model.generate_content(masked_text)
    llm_text = response.text
    
    # 3. Çıkış Güvenliği
    if check_for_leaks(llm_text, mapping, request_id):
        raise HTTPException(
            status_code=403,
            detail="Blocked: Güvenlik İhlali: Model çıktısında maskelenmemiş ham hassas veri saptandı!"
        )
    
    # 4. Geri Çözme (Unmasking / Rehydration)
    final_clean_response = rehydrate_text(llm_text, mapping)
    
    # 5. KARŞILAŞTIRMALI VE METİN FORMATI
    report = (
        "======================================================================\n"
        "                  ZERO-TRUST LLM VERİ GÜVENLİĞİ KATMANI             \n"
        "======================================================================\n\n"
        "1) KULLANICIDAN GELEN ORİJİNAL PROMPT:\n"
        "----------------------------------------------------------------------\n"
        f"{user_input}\n\n"
        "2) ARA KATMANIN (MIDDLEWARE) MASKELEYİP MODELE GÖNDERDİĞİ METİN:\n"
        "----------------------------------------------------------------------\n"
        f"{masked_text}\n\n"
        "3) MODELİN (LLM) ÜRETTİĞİ MASKELEDİĞİMİZ ETİKETLİ HAM CEVAP:\n"
        "----------------------------------------------------------------------\n"
        f"{llm_text}\n\n"
        "4) KULLANICIYA DÖNEN GERİ ÇÖZÜLMÜŞ (UNMASKED) NİHAİ TEMİZ CEVAP:\n"
        "----------------------------------------------------------------------\n"
        f"{final_clean_response}\n"
        "======================================================================\n"
    )
    
    return report
