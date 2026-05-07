import os
import requests
from aiogram import Bot, Dispatcher, types

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

def ask_ai(prompt):
    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": prompt}
    )

    try:
        return response.json()[0]["generated_text"]
    except:
        return "KI gerade nicht erreichbar"

@dp.message_handler()
async def handle(message: types.Message):
    user_text = message.text

    prompt = f"""
Du bist ein hilfreicher KI-Assistent.
Antworte klar und verständlich.

User: {user_text}
"""

    answer = ask_ai(prompt)

    await message.answer(answer)

if __name__ == "__main__":
    executor.start_polling(dp)
import asyncio
from aiogram import Bot, Dispatcher

async def main():
    bot = Bot(token="DEIN_TOKEN")
    dp = Dispatcher()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
