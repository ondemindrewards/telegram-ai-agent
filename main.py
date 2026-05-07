import os
import asyncio
import requests
import json
import re
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
# URL CONTENT READER
# =========================
def extract_urls(text):
    return re.findall(r'https?://\\S+', text)

def fetch_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            return f"Fehler {r.status_code}"

        html = r.text

        # clean html
        html = re.sub(r'<script.*?</script>', '', html, flags=re.S)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.S)
        html = re.sub(r'<.*?>', ' ', html)

        return html[:3000]

    except Exception as e:
        return str(e)

# =========================
# MEMORY UPDATE
# =========================
def update_memory(uid, text):
    user = get_user(uid)
    user["history"].append(text)
    save_memory(memory)

# =========================
# SYSTEM PROMPT (RESEARCH MODE)
# =========================
SYSTEM_PROMPT = (
    "Du bist ein professioneller Deep-Research-KI-Assistent. "
    "Du analysierst Informationen aus Websuche und Webseiteninhalt. "

    "ARBEITSWEISE:"
    "1. Verstehe die Frage"
    "2. Nutze Webdaten + Webseiteninhalt"
    "3. Strukturierte Analyse schreiben"
    "4. Klare Schlussfolgerung geben"

    "REGELN:"
    "- Keine Halluzinationen"
    "- Nur basierend auf Daten antworten"
    "- Strukturiert und professionell"
)

# =========================
# AI RESEARCH ENGINE
# =========================
def ask_ai(uid, user_text):
    try:
        user = get_user(uid)
        compress(user)

        # 🌐 WEB SEARCH
        search_results = web_search(user_text)
        web_data = "\n".join(search_results)

        # 🌐 URL CONTENT
        urls = extract_urls(user_text)
        url_data = ""

        for u in urls[:2]:
            url_data += "\n\nURL CONTENT:\n"
            url_data += fetch_url(u)

        memory_block = f"MEMORY: {user['summary']}"

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"""
WEB SEARCH:
{web_data}

URL DATA:
{url_data}

MEMORY:
{memory_block}

QUESTION:
{user_text}
"""}
                ],
                "temperature": 0.3,
                "max_tokens": 900
            },
            timeout=60
        )

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
