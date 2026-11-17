
import json
import time
from pathlib import Path

import requests

API_URL = "https://wallhaven.cc/api/v1/search"
HISTORY_FILE = Path("seen_ids.json")
OUTPUT_FILE = Path("wallpapers.json")

MAX_WALLPAPERS = 24
MAX_PAGES = 8
HISTORY_LIMIT = 500


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def fetch_wallpapers():
    params = {
        "q": "nature",
        "categories": "100",
        "purity": "100",
        "resolutions": "3840x2160",
        "ratios": "16x9",
        "sorting": "random",
        "page": 1,
    }

    results = []
    seed = None
    last_page = MAX_PAGES

    for page in range(1, MAX_PAGES + 1):
        params["page"] = page

        if seed:
            params["seed"] = seed

        response = requests.get(
            API_URL,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        payload = response.json()
        meta = payload.get("meta", {})

        if page == 1:
            seed = meta.get("seed")
            last_page = min(
                meta.get("last_page", MAX_PAGES),
                MAX_PAGES,
            )

        results.extend(payload.get("data", []))

        if page >= last_page:
            break

        time.sleep(1)

    return results


def main():
    history = load_history()
    seen = set(history)

    candidates = fetch_wallpapers()
    selected = []

    for wallpaper in candidates:
        wallpaper_id = wallpaper.get("id")
        image_url = wallpaper.get("path")

        if not wallpaper_id or not image_url:
            continue

        if wallpaper_id in seen:
            continue

        if wallpaper.get("resolution") != "3840x2160":
            continue

        if wallpaper.get("purity") != "sfw":
            continue

        selected.append({
            "location": "Wallhaven",
            "title": f"Nature 4K {wallpaper_id}",
            "author": "Wallhaven",
            "url_img": image_url,
        })

        seen.add(wallpaper_id)

        if len(selected) >= MAX_WALLPAPERS:
            break

    if not selected:
        raise RuntimeError(
            "No new wallpapers found. Existing feed was preserved."
        )

    OUTPUT_FILE.write_text(
        json.dumps(selected, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    new_history = [
        item["title"].replace("Nature 4K ", "")
        for item in selected
    ]

    updated_history = (
        new_history + [
            item for item in history
            if item not in set(new_history)
        ]
    )[:HISTORY_LIMIT]

    HISTORY_FILE.write_text(
        json.dumps(updated_history, indent=2),
        encoding="utf-8",
    )

    print(f"Generated {len(selected)} new 4K wallpapers.")


if __name__ == "__main__":
    main()
