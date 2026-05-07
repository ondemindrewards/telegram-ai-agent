import os
import asyncio
import requests
from aiogram import Bot, Dispatcher
from aiogram.types import Message

# =========================
# ENV VARS
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN fehlt")
if not GROQ_API_KEY:
    raise Exception("GROQ_API_KEY fehlt")

# =========================
# BOT SETUP
# =========================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# GROQ API
# =========================
API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# =========================
# STABILER KI PROMPT
# =========================
SYSTEM_PROMPT = (
    "Du bist ein hilfreicher, präziser und freundlicher Assistent. "
    "Antworte klar, direkt und ohne Wiederholungen. "
    "Keine Rollennamen, keine Formatierungen wie 'User:' oder 'AI:'. "
    "Keine unnötigen Fragen am Ende, außer es ist wirklich sinnvoll. "
    "Wenn du unsicher bist, sage es ehrlich."
)

# =========================
# KI FUNKTION (ROBUST)
# =========================
def ask_ai(prompt: str) -> str:
    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,   # 🔥 stabiler, weniger Chaos
                "max_tokens": 400     # 🔥 verhindert Endlos-Antworten
            },
            timeout=60
        )

        # Debug (wichtig für Railway)
        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        # Fehler sauber behandeln
        if response.status_code != 200:
            return f"API Fehler {response.status_code}"

        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Systemfehler: {e}"


# =========================
# TELEGRAM HANDLER
# =========================
@dp.message()
async def handle(message: Message):
    user_text = message.text or ""

    # leichte Strukturierung verbessert Qualität
    prompt = user_text.strip()

    answer = ask_ai(prompt)

    await message.answer(answer)


# =========================
# START
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
