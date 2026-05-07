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
# TRUST SCORE
# =========================
def domain_trust(url: str):
    url = (url or "").lower()

    if "wikipedia.org" in url:
        return 10
    if "britannica.com" in url:
        return 9
    if any(x in url for x in ["reuters", "bbc", "nytimes", "cnn"]):
        return 8
    if any(x in url for x in ["medium", "blog"]):
        return 4
    return 6

# =========================
# WEB SEARCH
# =========================
def web_search(query):
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            },
            timeout=10
        )

        data = r.json()
        results = []

        if data.get("AbstractText"):
            results.append({
                "text": data["AbstractText"],
                "url": data.get("AbstractURL", "")
            })

        for t in data.get("RelatedTopics", [])[:10]:
            if isinstance(t, dict) and t.get("Text"):
                results.append({
                    "text": t["Text"],
                    "url": t.get("FirstURL", "")
                })

        return results

    except:
        return []

# =========================
# RANK + DEDUPE
# =========================
def rank_sources(results):
    seen = set()
    scored = []

    for r in results:
        text = r.get("text", "")
        url = r.get("url", "")

        if not text:
            continue

        key = text.lower()
        if key in seen:
            continue
        seen.add(key)

        trust = domain_trust(url)
        score = trust + min(len(text) / 300, 3)

        scored.append({
            "text": text,
            "url": url,
            "trust": trust,
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:8]

# =========================
# BUILD RESEARCH PACK
# =========================
def build_research(query):
    raw = web_search(query)
    ranked = rank_sources(raw)

    out = []
    for i, r in enumerate(ranked, 1):
        out.append(f"[{i}] (Trust {r['trust']}) {r['text']} | {r['url']}")

    return "\n".join(out)

# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = (
    "Du bist ein professioneller Research AI Assistant. "
    "Du arbeitest mit priorisierten Quellen und Zitaten. "
    "Antworte strukturiert: Erklärung → Analyse → Fazit. "
    "Nutze nur bereitgestellte Informationen. "
    "Wenn möglich, beziehe dich auf Quellen [1], [2]."
)

# =========================
# AI ENGINE
# =========================
def ask_ai(uid, user_text):
    try:
        user = get_user(uid)
        compress(user)

        research = build_research(user_text)

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"""
QUELLEN:
{research}

MEMORY:
{user['summary']}

FRAGE:
{user_text}
"""}
                ],
                "temperature": 0.2,
                "max_tokens": 1000
            },
            timeout=60
        )

        if response.status_code != 200:
            return f"API Fehler {response.text}"

        return response.json()["choices"][0]["message"]["content"]

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
