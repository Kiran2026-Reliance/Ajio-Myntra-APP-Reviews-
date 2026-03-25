"""
scrape.py  –  Fetch latest Android (Play Store) + iOS (App Store) reviews
Outputs: data/reviews_raw.json
"""

import json, time, re, urllib.request, os
from datetime import datetime
from collections import Counter, defaultdict
from google_play_scraper import reviews as gplay_reviews, Sort

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANDROID_APPS = {
    "ajio":   "com.ril.ajio",
    "myntra": "com.myntra.android",
}
IOS_APPS = {
    "ajio":   "1113425372",
    "myntra": "907394059",
}
TARGET_DATE   = "2025-03-01"          # fetch everything from this date onwards
ANDROID_BATCH = 3000                  # reviews per pagination call
COUNTRY       = "in"
LANGUAGE      = "en"

os.makedirs("data", exist_ok=True)


# ── ANDROID SCRAPER ───────────────────────────────────────────────────────────
def scrape_android(app_id: str, label: str) -> list[dict]:
    print(f"  [Android] {label} …", flush=True)
    all_reviews, token = gplay_reviews(
        app_id, lang=LANGUAGE, country=COUNTRY,
        sort=Sort.NEWEST, count=ANDROID_BATCH
    )
    print(f"    batch 1 → {len(all_reviews)} | oldest {min(r['at'] for r in all_reviews).strftime('%Y-%m-%d')}")

    while token:
        oldest = min(r["at"] for r in all_reviews[-ANDROID_BATCH:]).strftime("%Y-%m-%d")
        if oldest <= TARGET_DATE:
            break
        batch, token = gplay_reviews(
            app_id, lang=LANGUAGE, country=COUNTRY,
            sort=Sort.NEWEST, count=ANDROID_BATCH,
            continuation_token=token
        )
        if not batch:
            break
        all_reviews.extend(batch)
        oldest = min(r["at"] for r in batch).strftime("%Y-%m-%d")
        print(f"    → {len(all_reviews)} total | oldest {oldest}")

    result = [
        {"text": r["content"], "score": r["score"],
         "date": r["at"].strftime("%Y-%m-%d"), "src": "android"}
        for r in all_reviews
        if r["content"] and r["at"].strftime("%Y-%m-%d") >= TARGET_DATE
    ]
    print(f"    ✓ {len(result)} reviews ({TARGET_DATE} onwards)")
    return result


# ── iOS SCRAPER ───────────────────────────────────────────────────────────────
def scrape_ios(app_id: str, label: str) -> list[dict]:
    print(f"  [iOS]     {label} …", flush=True)
    seen, combined = set(), []

    for sort in ("mostRecent", "mostHelpful"):
        for page in range(1, 11):
            url = (f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/"
                   f"page={page}/id={app_id}/sortBy={sort}/json")
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)"}
                )
                with urllib.request.urlopen(req, timeout=15) as r:
                    data = json.loads(r.read())
                entries = data.get("feed", {}).get("entry", [])
                if not entries or len(entries) <= 1:
                    break
                for e in entries[1:]:
                    try:
                        dt  = datetime.fromisoformat(e["updated"]["label"].replace("Z", "+00:00"))
                        txt = e["content"]["label"]
                        key = txt[:60]
                        if key in seen or dt.strftime("%Y-%m-%d") < TARGET_DATE:
                            continue
                        seen.add(key)
                        combined.append({
                            "text":  (e["title"]["label"] + ". " + txt).strip(". "),
                            "score": int(e["im:rating"]["label"]),
                            "date":  dt.strftime("%Y-%m-%d"),
                            "src":   "ios",
                        })
                    except Exception:
                        pass
                time.sleep(0.15)
            except Exception as ex:
                print(f"    page {page} ({sort}): {ex}")
                break

    print(f"    ✓ {len(combined)} unique reviews")
    return combined


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"Scraping started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    raw = {}
    for brand in ("ajio", "myntra"):
        print(f"\n── {brand.upper()} ──────────────────────────────────")
        android = scrape_android(ANDROID_APPS[brand], brand)
        ios     = scrape_ios(IOS_APPS[brand], brand)
        raw[brand] = android + ios
        print(f"  TOTAL: {len(raw[brand])} reviews")

    # Sanitise text (remove control chars)
    for brand in raw:
        for r in raw[brand]:
            r["text"] = re.sub(r"[\x00-\x1f\x7f]", " ", r["text"]).strip()

    out_path = "data/reviews_raw.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=True, separators=(",", ":"))

    print(f"\n✅  Saved {out_path}")
    for brand in raw:
        dates = [r["date"] for r in raw[brand]]
        srcs  = Counter(r["src"] for r in raw[brand])
        print(f"  {brand}: {len(raw[brand])} reviews | "
              f"{min(dates)} → {max(dates)} | "
              f"android={srcs['android']} ios={srcs['ios']}")


if __name__ == "__main__":
    main()
