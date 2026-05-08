import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

SEARXNG_URL = "https://searxng-production-1ec0.up.railway.app"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# SEARCH
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

        r = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15
        )

        print("\n========== STATUS ==========")
        print(r.status_code)

        print("\n========== RAW RESPONSE ==========")
        print(r.text[:1000])

        try:
            data = r.json()
        except Exception as e:
            print("JSON ERROR:", e)
            return []

        print("\n========== JSON OK ==========")

        results = data.get("results", [])

        print(f"\nRESULTS FOUND: {len(results)}")

        return results

    except Exception as e:
        print("SEARCH ERROR:", e)
        return []

# =========================
# BOT RESPONSE
# =========================

@dp.message()
async def handle(message: types.Message):

    user_text = message.text or ""

    results = web_search(user_text)

    if not results:
        await message.answer(
            "❌ Keine Web-Ergebnisse gefunden.\nChecke Railway Logs."
        )
        return

    output = []

    for r in results[:5]:
        output.append(
            f"🔹 {r.get('title')}\n{r.get('url')}"
        )

    final_text = "\n\n".join(output)

    await message.answer(final_text)

# =========================
# START
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
