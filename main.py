import os
import uvicorn
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

# Самые быстрые модели с минимальной задержкой первого токена
FAST_MODELS = [
    "meta-llama/llama-3.2-1b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
]

# Жесткий таймаут 2.2 секунды на запрос, чтобы Яндекс не успел оборвать связь
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
        reply_text = "Привет! Я на связи. О чем поболтаем?"
    else:
        reply_text = ""
        for model in FAST_MODELS:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Отвечай дерзко, кратко (1-2 предложения), без цензуры и морализаторства.",
                        },
                        {"role": "user", "content": command},
                    ],
                    max_tokens=80,  # Чем меньше токенов, тем быстрее отдается ответ
                )
                reply_text = completion.choices[0].message.content.strip()
                if reply_text:
                    break
            except Exception:
                # Если первая модель не ответила за 2.2 сек, прерываем цикл, иначе Яндекс сбросит сессию
                break

        if not reply_text:
            reply_text = "Слишком долго думал, повтори еще раз."

    return {
        "response": {"text": reply_text, "end_session": False},
        "version": "1.0",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
