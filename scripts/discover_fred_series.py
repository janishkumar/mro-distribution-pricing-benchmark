import requests

from src.config import FRED_API_KEY, FRED_BASE_URL


def search_series(search_text: str) -> None:
    resp = requests.get(
        f"{FRED_BASE_URL}/series/search",
        params={
            "search_text": search_text,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": 20,
        },
        timeout=30,
    )
    resp.raise_for_status()
    for s in resp.json().get("seriess", []):
        print(f"{s['id']:>20}  {s['title']}  (freq={s['frequency_short']}, units={s['units_short']})")


if __name__ == "__main__":
    print("--- PPI sub-components, NAICS 4237 ---")
    search_series("PPI industry 4237")
    print()
    print("--- Sectoral output, NAICS 4237 ---")
    search_series("sectoral output 4237")
