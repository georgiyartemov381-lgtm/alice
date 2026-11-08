import os
from fastapi import FastAPI, Request
from openai import OpenAI
import uvicorn

app = FastAPI()

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENAI_API_KEY"),
)
MODEL_NAME = os.getenv("MODEL", "meta-llama/llama-3.3-70b-instruct:free")

@app.post("/webhook")
async def alice_webhook(request: Request):
    data = await request.json()
    req = data.get("request", {})
    command = req.get("command", "").strip()
    session = data.get("session", {})

    # Приветствие при первом запуске навыка
    if session.get("new", False) or not command:
        reply_text = "Привет! Я нейросеть без цензуры. Задай мне любой вопрос."
    else:
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Отвечай кратко и емко на русском языке. Ответы зачитываются голосом, не используй сложные спецсимволы, markdown и таблицы."},
                    {"role": "user", "content": command}
                ],
                max_tokens=400,
            )
            reply_text = completion.choices[0].message.content.strip()
        except Exception as e:
            reply_text = "Ошибка обращения к нейросети. Попробуй еще раз чуть позже."

    return {
        "response": {
            "text": reply_text,
            "end_session": False
        },
        "version": "1.0"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
