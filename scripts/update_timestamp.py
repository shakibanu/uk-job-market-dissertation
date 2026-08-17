"""
update_timestamp.py

Writes the current time to a small JSON file whenever a data refresh
happens, so the dashboard can show a genuine "last refreshed" timestamp
instead of a hardcoded date that goes stale the moment it's written.
"""

import json
import sys
from datetime import datetime, timezone


def update_timestamp(source):
    """Updates the last-refreshed record for one data source. Keeping a
    timestamp per source rather than a single overall one, since Adzuna
    refreshes weekly but NOMIS only monthly - a single combined
    timestamp would hide that difference."""
    try:
        with open("data/last_refreshed.json", "r") as f:
            timestamps = json.load(f)
    except FileNotFoundError:
        timestamps = {}

    timestamps[source] = datetime.now(timezone.utc).isoformat()

    with open("data/last_refreshed.json", "w") as f:
        json.dump(timestamps, f, indent=2)

    print(f"updated last_refreshed.json: {source} -> {timestamps[source]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python update_timestamp.py <source_name>")
        sys.exit(1)
    update_timestamp(sys.argv[1])
