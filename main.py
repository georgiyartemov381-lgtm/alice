import os
import traceback
from fastapi import FastAPI, Request
from openai import OpenAI
import uvicorn

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("MODEL", "google/gemini-2.0-flash-exp:free")

client = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
    timeout=2.2,
)

@app.post("/webhook")
async def alice_webhook(request: Request):
    data = await request.json()
    req = data.get("request", {})
    command = req.get("command", "").strip()
    session = data.get("session", {})

    if session.get("new", False) or not command:
        reply_text = "Привет! Я нейросеть без цензуры. Задай мне любой вопрос."
    else:
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "Отвечай кратко на русском языке без markdown, спецсимволов и таблиц.",
                    },
                    {"role": "user", "content": command},
                ],
                max_tokens=250,
            )
            reply_text = completion.choices[0].message.content.strip()
        except Exception as err:
            print("=== ERROR DETAILS START ===", flush=True)
            print(f"Type: {type(err).__name__}", flush=True)
            print(f"Message: {err}", flush=True)
            traceback.print_exc()
            print("=== ERROR DETAILS END ===", flush=True)
            reply_text = f"Сбой: {type(err).__name__}"

    return {
        "response": {
            "text": reply_text,
            "end_session": False,
        },
        "version": "1.0",
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
