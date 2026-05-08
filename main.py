import requests

# Deine SearXNG URL
SEARXNG_URL = "https://searxng-production-1ec0.up.railway.app"

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

        print("\n========== RAW RESPONSE ==========\n")
        print(r.text[:1500])
        print("\n==================================\n")

        # Versuch JSON zu lesen
        try:
            data = r.json()
        except Exception as e:
            print("JSON ERROR:", e)
            return []

        print("\n========== PARSED JSON ==========\n")
        print(data)
        print("\n=================================\n")

        results = data.get("results", [])

        print(f"\nRESULT COUNT: {len(results)}\n")

        return results

    except Exception as e:
        print("SEARCH ERROR:", e)
        return []


# TEST
if __name__ == "__main__":
    query = "AI news"
    results = web_search(query)

    print("\n========== FINAL RESULTS ==========\n")
    for r in results:
        print(r)
