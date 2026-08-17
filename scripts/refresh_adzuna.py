"""
refresh_adzuna.py

Re-runs the Adzuna collection on a schedule (weekly, via GitHub Actions)
so the job postings data doesn't stay stuck on the June 2026 snapshot
forever. Same collection logic as the original script from Sprint 1 -
one search per sector, respecting Adzuna's 100-calls-per-hour free tier
limit with a delay between calls.
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY")

SECTORS = ["Technology", "Healthcare", "Finance", "Engineering", "Education"]
# same single-keyword-per-sector approach from Sprint 1 - multi-word
# search terms returned zero results for most sectors when this was
# first tried
SECTOR_KEYWORDS = {
    "Technology": "technology",
    "Healthcare": "healthcare",
    "Finance": "finance",
    "Engineering": "engineering",
    "Education": "education",
}

RATE_LIMIT_DELAY_SECONDS = 5  # keeping well under the 100-calls-per-hour limit


def fetch_postings_for_sector(sector, keyword, pages=2):
    """Pulls job postings for one sector from the Adzuna API, a couple
    of pages at a time, with a delay between calls to stay within the
    free tier's rate limit."""
    all_postings = []
    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/{page}"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": keyword,
            "results_per_page": 50,
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        results = response.json().get("results", [])

        for job in results:
            all_postings.append({
                "sector": sector,
                "title": job.get("title"),
                "company": job.get("company", {}).get("display_name"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "description": (job.get("description") or "")[:500],
                "city": job.get("location", {}).get("display_name"),
                "date_posted": job.get("created"),
                "is_agency": None,  # kept for compatibility with the existing cleaned columns
            })

        time.sleep(RATE_LIMIT_DELAY_SECONDS)

    return all_postings


def refresh_adzuna_data():
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise RuntimeError("ADZUNA_APP_ID and ADZUNA_APP_KEY must be set as environment variables")

    all_rows = []
    for sector, keyword in SECTOR_KEYWORDS.items():
        print(f"fetching postings for {sector}...")
        all_rows.extend(fetch_postings_for_sector(sector, keyword))

    new_df = pd.DataFrame(all_rows)
    new_df.to_csv("data/Adzuna_Clean.csv", index=False)
    print(f"saved {len(new_df)} postings to data/Adzuna_Clean.csv")

    return len(new_df)


if __name__ == "__main__":
    count = refresh_adzuna_data()
    print(f"Adzuna refresh complete: {count} postings, {datetime.now(timezone.utc).isoformat()}")
