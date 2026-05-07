import os
import asyncio
import requests
from aiogram import Bot, Dispatcher
from aiogram.types import Message

# =====================
# ENV VARIABLES
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN fehlt")
if not GROQ_API_KEY:
    raise Exception("GROQ_API_KEY fehlt")

# =====================
# BOT SETUP
# =====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =====================
# GROQ API
# =====================
API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# =====================
# NATÜRLICHE PERSÖNLICHKEIT (WICHTIG)
# =====================
SYSTEM_PROMPT = (
    "Du bist ein natürlicher, freundlicher und intelligenter Chat-Assistent in einem Telegram-Chat. "
    "Sprich wie ein echter Mensch. Keine KI-Erklärungen, keine Disclaimer, keine Hinweise auf Regeln oder Einschränkungen. "
    "Keine Sätze wie 'als KI', 'ich kann nicht' oder ähnliche Floskeln. "
    "Antworte kurz, klar und natürlich. Kein unnötiges Gerede. "
    "Passe dich dem Stil des Nutzers an (locker oder ernst)."
)

# =====================
# KI FUNKTION
# =====================
def ask_ai(user_text: str) -> str:
    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ],
                "temperature": 0.6,
                "max_tokens": 400
            },
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.status_code != 200:
            return f"API Fehler {response.status_code}"

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Fehler: {e}"

# =====================
# TELEGRAM HANDLER
# =====================
@dp.message()
async def handle(message: Message):
    user_text = message.text or ""

    answer = ask_ai(user_text)

    await message.answer(answer)

# =====================
# START
# =====================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
