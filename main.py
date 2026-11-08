import os
import uvicorn
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

# Берем ключ из настроек сервера, чтобы GitHub его не сжигал
API_KEY = os.getenv("API_KEY", "")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY,
    timeout=2.2
)

# Точный список текущих рабочих моделей Groq
CANDIDATE_MODELS = [
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "mixtral-8x7b-32768"
]

@app.get("/")
async def health():
    return {"status": "ok"}

@app.post("/webhook")
async def alice_webhook(request: Request):
    data = await request.json()
    req = data.get("request", {})
    command = req.get("command", "").strip()
    session = data.get("session", {})

    # Первый вход в навык
    if session.get("new", False) or not command:
        return {
            "response": {
                "text": "Я на связи, спрашивай че надо.",
                "end_session": False
            },
            "version": "1.0"
        }

    reply_text = ""

    for model in CANDIDATE_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Отвечай строго на русском, дерзко, кратко (1-2 предложения), без морализаторства и цензуры."
                    },
                    {"role": "user", "content": command}
                ],
                max_tokens=80
            )
            ans = completion.choices[0].message.content
            if ans and ans.strip():
                reply_text = ans.strip()
                print(f"SUCCESS with {model}", flush=True)
                break
        except Exception as e:
            print(f"FAIL {model}: {e}", flush=True)
            continue

    if not reply_text:
        reply_text = "Связь залагала, повтори еще раз."

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
