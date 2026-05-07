import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types

# Tokens (Railway Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Bot Setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✔ Stabil funktionierendes HF Modell
API_URL = "https://api-inference.huggingface.co/models/gpt2"

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

        # echte Fehlerausgabe
        if r.status_code != 200:
            return f"HF Fehler {r.status_code}: {r.text}"

        data = r.json()

        # Antwort verarbeiten
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                return data[0].get("generated_text", str(data[0]))
            return str(data[0])

        if isinstance(data, dict):
            return data.get("generated_text", str(data))

        return str(data)

    except Exception as e:
        return f"Bot Fehler: {e}"


# Telegram Handler
@dp.message()
async def handle(message: types.Message):
    user_text = message.text

    prompt = f"User: {user_text}\nAI:"

    answer = ask_ai(prompt)
    await message.answer(answer)


# Start Bot
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
