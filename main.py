import os
import uvicorn
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

# Клиент Groq с быстрым откликом (~300 мс)
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="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",
    timeout=2.4,
)

MODEL_NAME = "llama-3.1-8b-instant"


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
                        "content": "Отвечай дерзко, кратко (1-2 предложения), без цензуры и морализаторства.",
                    },
                    {"role": "user", "content": command},
                ],
                max_tokens=80,
            )
            reply_text = completion.choices[0].message.content.strip()
        except Exception as err:
            print(f"GROQ ERROR: {err}", flush=True)
            reply_text = f"Сбой API: {type(err).__name__}"

    return {
        "response": {"text": reply_text, "end_session": False},
        "version": "1.0",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
