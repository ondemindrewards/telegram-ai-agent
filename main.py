import os
import asyncio
import requests
import json
import re
from collections import defaultdict
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
# MULTI SEARCH ENGINE
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

        return results

    except:
        return []

# =========================
# QUALITY SCORING (SIMPLE RANKING ENGINE)
# =========================
def score_source(text):
    score = 0

    # length = more info = better
    score += min(len(text) / 200, 5)

    # keywords boost
    trusted_keywords = ["study", "research", "data", "analysis", "report", "official"]
    for k in trusted_keywords:
        if k in text.lower():
            score += 2

    return score

def deduplicate_and_rank(results):
    seen = set()
    scored = []

    for r in results:
        clean = r.strip()
        if not clean:
            continue

        # dedup
        if clean.lower() in seen:
            continue

        seen.add(clean.lower())

        scored.append((score_source(clean), clean))

    # sort by score (highest first)
    scored.sort(reverse=True, key=lambda x: x[0])

    return [s[1] for s in scored[:8]]

# =========================
# RESEARCH BUILDER
# =========================
def build_research(query):
    # Multi-query expansion
    queries = [
        query,
        query + " explanation",
        query + " facts",
    ]

    all_results = []

    for q in queries:
        all_results.extend(web_search(q))

    ranked = deduplicate_and_rank(all_results)

    return "\n".join(ranked)

# =========================
# SYSTEM PROMPT (PRO LEVEL)
# =========================
SYSTEM_PROMPT = (
    "Du bist ein professioneller Research AI Agent mit Quellenlogik. "
    "Du analysierst Informationen strukturiert und vergleichst Quellen. "

    "ARBEITSWEISE:"
    "1. Informationen lesen"
    "2. Unterschiede erkennen"
    "3. logische Zusammenfassung erstellen"
    "4. klare, saubere Antwort liefern"

    "REGELN:"
    "- keine Halluzinationen"
    "- nutze nur bereitgestellte Daten"
    "- klare Struktur"
)

# =========================
# AI ENGINE
# =========================
def ask_ai(uid, user_text):
    try:
        user = get_user(uid)
        compress(user)

        research_data = build_research(user_text)

        memory_block = f"MEMORY: {user['summary']}"

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"""
RESEARCH SOURCES (ranked + deduplicated):
{research_data}

MEMORY:
{memory_block}

QUESTION:
{user_text}
"""}
                ],
                "temperature": 0.2,
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
