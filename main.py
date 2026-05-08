import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ DEINE FIXE SEARXNG URL
SEARXNG_URL = "https://searxng-production-1ec0.up.railway.app"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# WEB SEARCH (SEARXNG)
# =========================

def web_search(query):
    try:
        url = f"{SEARXNG_URL}/search"

        params = {
            "q": query,
            "format": "json"
        }

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()

        results = []

        for item in data.get("results", [])[:8]:
            results.append({
                "title": item.get("title", ""),
                "text": item.get("content", ""),
                "url": item.get("url", "")
            })

        return results

    except Exception as e:
        print("Search error:", e)
        return []

# =========================
# RESEARCH BUILDER
# =========================

def build_research(query):
    results = web_search(query)

    if not results:
        return "❌ Keine aktuellen Webdaten gefunden."

    output = []

    for i, r in enumerate(results, 1):
        output.append(
            f"[{i}] {r['title']}\n{r['text']}\nQuelle: {r['url']}"
        )

    return "\n\n".join(output)

# =========================
# RESPONSE GENERATION
# =========================

def generate_answer(user_text):
    research = build_research(user_text)

    return f"""
🧠 LIVE WEB RESEARCH

{research}

---

💬 Kurz-Zusammenfassung:
Die oben genannten Quellen wurden live aus dem Internet abgerufen und für dich zusammengefasst.
"""

# =========================
# TELEGRAM HANDLER
# =========================

@dp.message()
async def handle(message: types.Message):
    user_text = message.text or ""

    answer = generate_answer(user_text)

    await message.answer(answer)

# =========================
# START BOT
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
