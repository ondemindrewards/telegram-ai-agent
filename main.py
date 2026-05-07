import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def ask_ai(prompt):
    r = requests.post(API_URL, headers=headers, json={"inputs": prompt})

    print("STATUS:", r.status_code)
    print("TEXT:", r.text)

    if r.status_code != 200:
        return "HF API Fehler"

    try:
        data = r.json()

        if isinstance(data, list):
            return data[0].get("generated_text", "Keine Antwort")

        return str(data)

    except Exception as e:
        return f"Parse Fehler: {e}"

@dp.message()
async def handle(message: types.Message):
    prompt = f"User: {message.text}"
    answer = ask_ai(prompt)
    await message.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
