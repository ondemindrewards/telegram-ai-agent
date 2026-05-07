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

if not BOT_TOKEN or not GROQ_API_KEY:
    raise Exception("Fehlende Environment Variables")

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
# MEMORY SYSTEM
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
            "history": [],
            "important": [],
            "summary": ""
        }
    return memory[uid]

def compress(user):
    user["history"] = user["history"][-40:]
    user["summary"] = " | ".join(user["history"][-10:])

# =========================
# WEB SEARCH (FREE)
# =========================
def web_search(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        results = []

        if data.get("AbstractText"):
            results.append(data["AbstractText"])

        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(topic["Text"])

        return results[:5]

    except:
        return []

# =========================
# MEMORY UPDATE
# =========================
def update_memory(uid, text):
    user = get_user(uid)

    user["history"].append(text)
    save_memory(memory)

# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = (
    "Du bist ein intelligenter Deep-Research-Assistent. "
    "Du nutzt Webdaten und Memory, um präzise Antworten zu geben. "

    "REGELN:"
    "- Keine Halluzinationen"
    "- Nutze Webdaten wenn vorhanden"
    "- Antworte strukturiert"
    "- Keine KI-Erklärungen"
)

# =========================
# AI FUNCTION (RESEARCH MODE)
# =========================
def ask_ai(uid, user_text):
    try:
        user = get_user(uid)
        compress(user)

        # 🌐 WEB SEARCH
        search_results = web_search(user_text)
        web_data = "\n".join(search_results) if search_results else "Keine Webdaten gefunden."

        memory_block = f"""
MEMORY SUMMARY:
{user['summary']}
"""

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"""
WEB SEARCH RESULTS:
{web_data}

MEMORY:
{memory_block}

QUESTION:
{user_text}
"""}
                ],
                "temperature": 0.3,
                "max_tokens": 800
            },
            timeout=60
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.status_code != 200:
            return "API Fehler"

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Fehler: {e}"

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
