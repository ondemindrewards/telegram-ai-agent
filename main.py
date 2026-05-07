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

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# =========================
# MEMORY FILE
# =========================
MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

memory = load_memory()

def get_user(uid):
    uid = str(uid)
    if uid not in memory:
        memory[uid] = {
            "facts": [],
            "important": [],
            "history": [],
            "summary": ""
        }
    return memory[uid]

# =========================
# MEMORY TRIGGER LOGIC
# =========================
MEMORY_TRIGGERS = [
    "merk dir das",
    "behalt das im hinterkopf",
    "das ist wichtig",
    "remember:",
    "save:"
]

def should_save(text: str):
    t = text.lower()
    return any(trigger in t for trigger in MEMORY_TRIGGERS)

def clean_memory_text(text: str):
    for trigger in MEMORY_TRIGGERS:
        text = text.replace(trigger, "")
    return text.strip()

# =========================
# MEMORY COMPRESSION
# =========================
def compress(user):
    user["history"] = user["history"][-25:]
    user["summary"] = " | ".join(user["history"][-8:])

# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = (
    "Du bist ein extrem natürlicher, stabiler Chat-Assistent. "
    "Du nutzt gespeicherte Infos sinnvoll, ohne sie zu übertreiben. "

    "REGELN:"
    "- Keine Selbstwidersprüche"
    "- Keine KI-Erklärungen"
    "- Keine Meta-Kommentare"
    "- Klar, direkt, menschlich antworten"
)

# =========================
# AI CALL
# =========================
def ask_ai(uid, user_text):
    try:
        user = get_user(uid)
        compress(user)

        memory_block = f"""
MEMORY:
Summary: {user['summary']}
Important: {user['important']}
"""

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": memory_block + "\n\nUser: " + user_text}
                ],
                "temperature": 0.55,
                "max_tokens": 500
            },
            timeout=60
        )

        if response.status_code != 200:
            return "API Fehler"

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception:
        return "Fehler"

# =========================
# MEMORY UPDATE
# =========================
def update_memory(uid, text):
    user = get_user(uid)

    user["history"].append(text)

    # NUR speichern wenn Nutzer es will
    if should_save(text):
        clean = clean_memory_text(text)
        user["important"].append(clean)

    save_memory(memory)

# =========================
# HANDLER
# =========================
@dp.message()
async def handle(message: Message):
    uid = message.from_user.id
    text = message.text or ""

    update_memory(uid, text)

    answer = ask_ai(uid, text)

    await message.answer(answer)

# =========================
# START
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
