import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types

# Environment Variables (Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Bot initialisieren
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✔ funktionierendes Modell
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# KI Anfrage
def ask_ai(prompt):
    try:
        r = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt}
        )

        print("STATUS:", r.status_code)
        print("TEXT:", r.text)

        # Fehler sauber anzeigen
        if r.status_code != 200:
            return f"HF Fehler {r.status_code}: {r.text}"

        data = r.json()

        # verschiedene Antwortformate abfangen
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return data[0].get("generated_text", str(data[0]))
            return str(data[0])

        if isinstance(data, dict):
            return data.get("generated_text", str(data))

        return str(data)

    except Exception as e:
        return f"Fehler im Bot: {e}"


# Telegram Handler
@dp.message()
async def handle(message: types.Message):
    user_text = message.text

    prompt = f"""
Du bist ein hilfreicher KI-Assistent.
Antworte kurz und verständlich.

User: {user_text}
"""

    answer = ask_ai(prompt)
    await message.answer(answer)


# Start Bot
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
