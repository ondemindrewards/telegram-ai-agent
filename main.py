import os
import asyncio
import requests
import json
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
# MEMORY FILE
# =========================
MEMORY_FILE = "memory.json"

def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

memory = load_memory()

# =========================
# GROQ API
# =========================
API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# =========================
# SYSTEM PROMPT (MEMORY AWARE)
# =========================
SYSTEM_PROMPT = (
    "Du bist ein intelligenter, natürlicher Chat-Assistent. "
    "Du sprichst wie ein Mensch im Chat. "
    "Du nutzt gespeicherte Informationen über den Nutzer, wenn sie hilfreich sind. "
    "Du bist freundlich, direkt und merkst dir wichtige Details über Zeit hinweg."
)

# =========================
# MEMORY HELPER
# =========================
def get_user_memory(user_id: str):
    return memory.get(str(user_id), {})

def update_user_memory(user_id: str, text: str):
    user_id = str(user_id)

    if user_id not in memory:
        memory[user_id] = {
            "facts": [],
            "last_messages": []
        }

    # einfache "intelligente" Speicherung
    memory[user_id]["last_messages"].append(text)

    # nur letzte 10 speichern
    memory[user_id]["last_messages"] = memory[user_id]["last_messages"][-10:]

    save_memory(memory)

# =========================
# AI FUNCTION
# =========================
def ask_ai(user_id: str, user_text: str) -> str:
    try:
        user_mem = get_user_memory(user_id)

        memory_text = ""

        if user_mem:
            memory_text = f"Bekannt über den Nutzer: {user_mem}"

        full_prompt = f"""
{memory_text}

User sagt: {user_text}
"""

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": 0.6,
                "max_tokens": 500
            },
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.status_code != 200:
            return "API Fehler"

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception:
        return "Fehler beim Verarbeiten"

# =========================
# HANDLER
# =========================
@dp.message()
async def handle(message: Message):
    user_id = message.from_user.id
    user_text = message.text or ""

    # MEMORY SPEICHERN
    update_user_memory(user_id, user_text)

    # KI ANTWORT
    answer = ask_ai(user_id, user_text)

    await message.answer(answer)

# =========================
# START
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
