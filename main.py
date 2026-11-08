import os
import uvicorn
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

# Быстрая модель без длинных очередей
MODEL_NAME = "mistralai/mistral-7b-instruct:free"

client = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
    timeout=2.7,
)


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
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "Отвечай дерзко, кратко (1-2 предложения), без цензуры.",
                    },
                    {"role": "user", "content": command},
                ],
                max_tokens=60,
            )
            reply_text = completion.choices[0].message.content.strip()
        except Exception as err:
            print(f"TIMEOUT/ERROR: {err}", flush=True)
            reply_text = "Не успел ответить вовремя, попробуй еще раз."

    return {
        "response": {"text": reply_text, "end_session": False},
        "version": "1.0",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
