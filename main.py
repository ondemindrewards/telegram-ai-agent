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
# MEMORY
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
        memory[uid] = {"history": [], "summary": ""}
    return memory[uid]

def compress(user):
    user["history"] = user["history"][-40:]
    user["summary"] = " | ".join(user["history"][-10:])

# =========================
# STEP 1: SEARCH
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

        for topic in data.get("RelatedTopics", [])[:10]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(topic["Text"])

        return results[:8]

    except:
        return []

# =========================
# STEP 2: URL EXTRACTION
# =========================
def extract_urls(text):
    return re.findall(r'https?://\\S+', text)

# =========================
# STEP 3: FETCH CONTENT
# =========================
def fetch_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            return ""

        html = r.text

        html = re.sub(r'<script.*?</script>', '', html, flags=re.S)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.S)
        html = re.sub(r'<.*?>', ' ', html)

        return html[:2500]

    except:
        return ""

# =========================
# STEP 4: RESEARCH PIPELINE (MULTI STEP)
# =========================
def build_research_package(query):
    search_results = web_search(query)

    # optional: extract fake URLs from results text
    urls = []
    for r in search_results:
        urls += extract_urls(r)

    urls = list(set(urls))[:3]

    url_content = ""
    for u in urls:
        url_content += fetch_url(u) + "\n\n"

    return {
        "search": "\n".join(search_results),
        "urls": url_content
    }

# =========================
# SYSTEM PROMPT (PREMIUM RESEARCH)
# =========================
SYSTEM_PROMPT = (
    "Du bist ein professioneller Multi-Step Research AI Agent. "
    "Du analysierst Informationen wie ein Analyst. "

    "DU ARBEITEST IN GEDANKLICHEN SCHRITTEN:"
    "1. Verstehen der Frage"
    "2. Analyse der Webdaten"
    "3. Vergleich der Informationen"
    "4. Bildung einer finalen, strukturierten Antwort"

    "REGELN:"
    "- Keine Halluzinationen"
    "- Nur basierend auf Daten antworten"
    "- Strukturierte Antwort (Einleitung, Analyse, Fazit)"
)

# =========================
# AI ENGINE
# =========================
def ask_ai(uid, user_text):
    try:
        user = get_user(uid)
        compress(user)

        research = build_research_package(user_text)

        memory_block = f"MEMORY: {user['summary']}"

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"""
STEP 1 - SEARCH DATA:
{research['search']}

STEP 2 - WEB CONTENT:
{research['urls']}

MEMORY:
{memory_block}

QUESTION:
{user_text}
"""}
                ],
                "temperature": 0.25,
                "max_tokens": 1000
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

    user = get_user(uid)
    user["history"].append(text)
    save_memory(memory)

    answer = ask_ai(uid, text)

    await message.answer(answer)

# =========================
# START
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
