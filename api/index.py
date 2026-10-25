
import os
import requests
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.get("/")
async def health():
    return {"status": "ok"}

@app.post("/")
async def webhook(request: Request):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    secret = os.getenv("WEBHOOK_SECRET")

    if not token or not secret:
        raise HTTPException(500, "Missing configuration")

    if request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    ) != secret:
        raise HTTPException(403, "Forbidden")

    update = await request.json()
    message = update.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not chat_id:
        return {"ok": True}

    if text.startswith("/start"):
        reply = "Welcome! Your bot is online."
    elif text.startswith("/help"):
        reply = "Available commands: /start, /help"
    else:
        reply = "Please send /start or /help."

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": reply},
        timeout=8,
    )
    response.raise_for_status()

    return {"ok": True}
  
