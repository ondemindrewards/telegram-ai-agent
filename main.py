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
# MEMORY SYSTEM (ULTRA)
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
# INTELLIGENT MEMORY DETECTION
# =========================
IMPORTANT_HINTS = [
    "ich heiße",
    "mein name ist",
    "ich bin",
    "ich arbeite",
    "ich studiere",
    "mein projekt",
    "ich will",
    "ich mache",
    "ich wohne"
]

USER_SAVE_COMMANDS = [
    "merk dir das",
    "behalt das im hinterkopf",
    "das ist wichtig",
    "remember:",
    "save:"
]

def is_important(text: str):
    t = text.lower()
    return any(hint in t for hint in IMPORTANT_HINTS)

def user_forced_save(text: str):
    t = text.lower()
    return any(cmd in t for cmd in USER_SAVE_COMMANDS)

def clean(text: str):
    for cmd in USER_SAVE_COMMANDS:
        text = text.replace(cmd, "")
    return text.strip()

# =========================
# MEMORY COMPRESSION
# =========================
def compress(user):
    user["history"] = user["history"][-40:]  # mehr Kontext behalten

    # Auto-Summary (leichtgewichtig)
    user["summary"] = " | ".join(user["history"][-10:])

# =========================
# SYSTEM PROMPT (ULTRA NATURAL)
# =========================
SYSTEM_PROMPT = (
    "Du bist ein extrem intelligenter, natürlicher und stabiler Chat-Assistent. "
    "Du führst echte Gespräche wie ein Mensch. "

    "REGELN:"
    "- Antworte klar und ohne Widersprüche"
    "- Keine KI-Erklärungen"
    "- Keine Meta-Diskussionen über dich selbst"
    "- Keine unnötigen Wiederholungen"
    "- Nutze gespeicherte Informationen sinnvoll"
    "- Sei natürlich, direkt und hilfreich"
)

# =========================
# AI FUNCTION
# =========================
def ask_ai(uid, user_text):
    try:
        user = get_user(uid)
        compress(user)

        memory_block = f"""
MEMORY SUMMARY:
{user['summary']}

IMPORTANT FACTS:
{user['important']}
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
                "max_tokens": 600
            },
            timeout=60
        )

        if response.status_code != 200:
            return "API Fehler"

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception:
        return "Fehler im System"

# =========================
# MEMORY UPDATE ENGINE
# =========================
def update_memory(uid, text):
    user = get_user(uid)

    user["history"].append(text)

    t = text.lower()

    # 1. User forced memory
    if user_forced_save(t):
        user["important"].append(clean(text))

    # 2. Auto important detection
    elif is_important(t):
        user["facts"].append(text)

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
