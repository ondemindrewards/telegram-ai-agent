import os
import asyncio
import requests
from aiogram import Bot, Dispatcher
from aiogram.types import Message

# ===== ENV VARS (Railway) =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN fehlt")
if not GROQ_API_KEY:
    raise Exception("GROQ_API_KEY fehlt")

# ===== TELEGRAM BOT =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== GROQ API =====
API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def ask_ai(prompt: str) -> str:
    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                # 🔥 AKTUELLES FUNKTIONIERENDES MODELL
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.status_code != 200:
            return f"Groq Fehler {response.status_code}: {response.text}"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Fehler: {e}"


# ===== TELEGRAM HANDLER =====
@dp.message()
async def handle(message: Message):
    user_text = message.text or ""
    answer = ask_ai(user_text)
    await message.answer(answer)


# ===== START BOT =====
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
