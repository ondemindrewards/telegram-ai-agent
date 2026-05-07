import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message

# Environment Variables (Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN fehlt in Railway Variables")
if not HF_TOKEN:
    raise Exception("HF_TOKEN fehlt in Railway Variables")

# Bot Setup (aiogram 3.x)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✔ stabiles HF Modell
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

# KI Anfrage
def ask_ai(prompt):
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "inputs": prompt,
                "options": {
                    "wait_for_model": True
                }
            },
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.status_code != 200:
            return f"HF Fehler {response.status_code}: {response.text}"

        data = response.json()

        # HuggingFace Antwort verarbeiten
        if isinstance(data, list) and len(data) > 0:
            item = data[0]
            if isinstance(item, dict):
                return item.get("generated_text", str(item))
            return str(item)

        if isinstance(data, dict):
            return data.get("generated_text", str(data))

        return str(data)

    except Exception as e:
        return f"Bot Fehler: {e}"


# Telegram Handler
@dp.message()
async def handle(message: Message):
    user_text = message.text or ""

    prompt = f"""
Du bist ein hilfreicher Assistent.
Antworte kurz und klar.

User: {user_text}
"""

    answer = ask_ai(prompt)

    await message.answer(answer)


# Start Bot
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
