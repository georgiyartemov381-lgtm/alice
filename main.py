import os
import traceback
from fastapi import FastAPI, Request
from openai import OpenAI
import uvicorn

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

# Список бесплатных моделей в порядке приоритета
FREE_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-3.2-3b-instruct:free",
    "meta-llama/llama-3.2-1b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free"
]

client = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
    timeout=2.4
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
        reply_text = ""
        last_error = None

        for model_candidate in FREE_MODELS:
            try:
                completion = client.chat.completions.create(
                    model=model_candidate,
                    messages=[
                        {
                            "role": "system",
                            "content": "Отвечай кратко на русском языке без markdown, спецсимволов и таблиц."
                        },
                        {"role": "user", "content": command}
                    ],
                    max_tokens=250
                )
                reply_text = completion.choices[0].message.content.strip()
                if reply_text:
                    print(f"SUCCESS: Answered by {model_candidate}", flush=True)
                    break
            except Exception as err:
                last_error = err
                print(f"WARN: Model {model_candidate} failed: {err}", flush=True)
                continue

        if not reply_text:
            print("=== ALL MODELS FAILED ===", flush=True)
            traceback.print_exc()
            reply_text = f"Сбой API: {type(last_error).__name__ if last_error else 'Нет ответа'}"

    return {
        "response": {
            "text": reply_text,
            "end_session": False
        },
        "version": "1.0"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
