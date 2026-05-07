import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def ask_ai(prompt):
    r = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    try:
        return r.json()[0]["generated_text"]
    except:
        return "KI gerade nicht erreichbar"

@dp.message()
async def handle(message: types.Message):
    prompt = f"User: {message.text}"
    answer = ask_ai(prompt)
    await message.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
