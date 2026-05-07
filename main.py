import os
import asyncio
import requests
from aiogram import Bot, Dispatcher
from aiogram.types import Message

# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN fehlt")
if not GROQ_API_KEY:
    raise Exception("GROQ_API_KEY fehlt")

# =========================
# BOT
# =========================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# API
# =========================
API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# =========================
# SYSTEM PROMPT (CONTROL + CLEAN)
# =========================
SYSTEM_PROMPT = (
    "Du bist ein extrem hilfreicher, kooperativer und gut steuerbarer Chat-Assistent in Telegram. "
    "Du folgst Anweisungen sehr genau und bist immer freundlich, direkt und klar. "

    "REGELN:"
    "- Keine Hinweise auf KI, Modelle oder Systemdetails "
    "- Keine Disclaimer oder unnötige Erklärungen "
    "- Keine Wiederholungen "
    "- Antworte immer präzise und hilfreich "
    "- Passe dich dem Nutzerstil an (locker oder ernst) "
)

# =========================
# COMMAND HANDLING
# =========================
def parse_command(text: str):
    text = text.strip().lower()

    if text.startswith("/help"):
        return "short", "Ich kann dir helfen. Schreib mir einfach deine Frage 🙂"

    if text.startswith("/short"):
        return "short", text.replace("/short", "").strip()

    if text.startswith("/long"):
        return "long", text.replace("/long", "").strip()

    return "normal", text

# =========================
# AI FUNCTION
# =========================
def ask_ai(user_text: str, mode: str) -> str:
    try:
        if mode == "short":
            style = "Antworte sehr kurz (max 2 Sätze)."
        elif mode == "long":
            style = "Antworte ausführlich, strukturiert und erklärend."
        else:
            style = "Antworte normal, klar und natürlich."

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"{style}\n\n{user_text}"}
                ],
                "temperature": 0.6,
                "max_tokens": 500
            },
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.status_code != 200:
            return "API Fehler – bitte später erneut versuchen."

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception:
        return "Verbindungsfehler – bitte erneut versuchen."

# =========================
# HANDLER
# =========================
@dp.message()
async def handle(message: Message):
    mode, text = parse_command(message.text or "")

    if mode == "short" and not text:
        await message.answer("Kurz-Modus aktiv. Schreib deine Frage.")
        return

    answer = ask_ai(text, mode)

    await message.answer(answer)

# =========================
# START
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
