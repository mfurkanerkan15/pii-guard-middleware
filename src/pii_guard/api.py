import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from pii_guard.config import get_settings
from pii_guard.dlp import check_for_leaks
from pii_guard.llm import get_llm_client
from pii_guard.logging_config import configure_logging
from pii_guard.masking import process_and_mask_dynamic, rehydrate_text

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):  # noqa: ARG001
    """Uygulama başlangıcında loglama yapılandırılır."""
    configure_logging(get_settings())
    logger.info("PII Guard Middleware başlatıldı")
    yield


app = FastAPI(title="Zero-Trust LLM Veri Güvenliği Katmanı", lifespan=lifespan)


# TODO (v0.4.0): Async event loop ve HTTP entegrasyonu — _run_coroutine / send(None)
# yaklaşımı TestClient ile değiştirilecek.
@app.post("/process", response_class=PlainTextResponse)
async def handle_request(user_input: str = Body(..., media_type="text/plain")):
    request_id = str(uuid.uuid4())

    # 1. Giriş Güvenliği: Dinamik Maskeleme yapılıyor
    masked_text, mapping = process_and_mask_dynamic(user_input, request_id)

    # 2. LLM çağrısı (sarmalayıcı üzerinden)
    llm_client = get_llm_client()
    llm_text = llm_client.generate(masked_text)

    # 3. Çıkış Güvenliği
    if check_for_leaks(llm_text, mapping, request_id):
        raise HTTPException(
            status_code=403,
            detail="Blocked: Güvenlik İhlali: Model çıktısında maskelenmemiş ham hassas veri saptandı!",
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
