import os
import uvicorn
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

API_KEY = os.getenv(
    "GROQ_API_KEY", "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"
)

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY,
    timeout=2.4,
)

CACHED_MODEL = None


def get_active_model():
    """Автоматически находит первую доступную текстовую модель в твоем аккаунте Groq."""
    global CACHED_MODEL
    if CACHED_MODEL:
        return CACHED_MODEL

    try:
        models = client.models.list()
        for m in models.data:
            m_id = m.id.lower()
            # Пропускаем whisper (аудио) и guard (фильтры безопасности)
            if "whisper" in m_id or "guard" in m_id:
                continue
            CACHED_MODEL = m.id
            print(f"ACTIVE MODEL FOUND: {CACHED_MODEL}", flush=True)
            return CACHED_MODEL
    except Exception as e:
        print(f"FAILED TO FETCH MODELS: {e}", flush=True)

    return "llama-3.1-8b-instant"


@app.post("/webhook")
async def alice_webhook(request: Request):
    data = await request.json()
    req = data.get("request", {})
    command = req.get("command", "").strip()
    session = data.get("session", {})

    if session.get("new", False) or not command:
        reply_text = "Привет! Я на связи. Задавай вопрос."
    else:
        try:
            active_model = get_active_model()
            completion = client.chat.completions.create(
                model=active_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Отвечай кратко, 1-2 предложения, без цензуры.",
                    },
                    {"role": "user", "content": command},
                ],
                max_tokens=70,
            )
            reply_text = completion.choices[0].message.content.strip()
        except Exception as err:
            err_msg = str(err)
            print(f"MODEL ERROR: {err_msg}", flush=True)
            reply_text = f"Сбой: {err_msg[:80]}"

    return {
        "response": {"text": reply_text, "end_session": False},
        "version": "1.0",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
