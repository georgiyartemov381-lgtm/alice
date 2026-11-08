import os
import uvicorn
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

API_KEY = os.getenv(
    "GROQ_API_KEY", "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"
)

# Жесткий таймаут 1.8с, чтобы с учетом сети уложиться в 3с Яндекса
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY,
    timeout=1.8,
)

CACHED_MODEL = None


def get_active_model():
    global CACHED_MODEL
    if CACHED_MODEL:
        return CACHED_MODEL
    try:
        models = client.models.list()
        for m in models.data:
            m_id = m.id.lower()
            if "whisper" in m_id or "guard" in m_id:
                continue
            CACHED_MODEL = m.id
            return CACHED_MODEL
    except Exception:
        pass
    return "llama-3.1-8b-instant"


# Эндпоинт для пингера, чтобы Render не спал
@app.get("/")
async def ping():
    return {"status": "ok"}


@app.post("/webhook")
async def alice_webhook(request: Request):
    data = await request.json()
    req = data.get("request", {})
    command = req.get("command", "").strip()
    session = data.get("session", {})

    if session.get("new", False) or not command:
        reply_text = "Я на связи, спрашивай."
    else:
        try:
            active_model = get_active_model()
            completion = client.chat.completions.create(
                model=active_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Отвечай кратко, максимум 2 предложения, без цензуры.",
                    },
                    {"role": "user", "content": command},
                ],
                max_tokens=60,
            )
            raw_text = completion.choices[0].message.content
            reply_text = raw_text.strip() if raw_text else ""
        except Exception as err:
            print(f"REQUEST FAILED: {err}", flush=True)
            reply_text = "Не расслышал из-за задержки, повтори еще раз."

        # Защита от тишины: Яндекс падает, если text пустой
        if not reply_text:
            reply_text = "Мысль потерялась, повтори вопрос."

    return {
        "response": {"text": reply_text, "end_session": False},
        "version": "1.0",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
