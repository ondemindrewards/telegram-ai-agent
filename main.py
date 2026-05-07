import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types

# Tokens aus Railway Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Bot Setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# HuggingFace Model
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# KI Anfrage
def ask_ai(prompt):
    try:
        r = requests.post(API_URL, headers=headers, json={"inputs": prompt})

        print("STATUS:", r.status_code)
        print("TEXT:", r.text)

        if r.status_code != 200:
            return "HF API Fehler"

        data = r.json()

        # verschiedene mögliche Antwortformate abfangen
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return data[0].get("generated_text", str(data[0]))
            return str(data[0])

        if isinstance(data, dict):
            return data.get("generated_text", str(data))

        return str(data)

    except Exception as e:
        return f"Fehler: {e}"


# Message Handler
@dp.message()
async def handle(message: types.Message):
    prompt = f"User: {message.text}"
    answer = ask_ai(prompt)
    await message.answer(answer)


# Start Bot
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
