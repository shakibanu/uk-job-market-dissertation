"""
startup_cache.py

The SARIMA models, the sponsorship classifier and the skills extraction
all take a while to compute (together, close to 90 seconds), and they
were all set up to recompute every time the app starts. That's fine
running locally, but it's a real problem on a hosting platform like
Render's free tier, where the app "spins down" when nobody's used it for
a while and has to cold-start again on the next visit - meaning the
first person to load the site after any quiet period would wait 90+
seconds instead of the 5 seconds this needs to load in.

This just saves whatever gets computed to a file the first time, and
loads it back from that file on every startup after that, instead of
recomputing from scratch. The cache only needs clearing out if the
underlying data actually changes (e.g. after the automated weekly/
monthly data refresh runs).
"""

import os
import pickle

CACHE_FOLDER = "startup_cache"


def load_or_compute(cache_name, compute_function):
    """Loads a cached result if one exists, otherwise runs the (slow)
    compute_function, saves the result for next time, and returns it."""
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    cache_path = os.path.join(CACHE_FOLDER, f"{cache_name}.pkl")

    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            print(f"loaded {cache_name} from cache (skipping recomputation)")
            return pickle.load(f)

    result = compute_function()

    with open(cache_path, "wb") as f:
        pickle.dump(result, f)

    return result


def clear_cache():
    """Deletes every cached result - call this after the automated data
    refresh runs, since a stale cache would otherwise keep showing old
    SARIMA forecasts, classifier results and skills lists even after
    the underlying data has changed."""
    if not os.path.exists(CACHE_FOLDER):
        return
    for filename in os.listdir(CACHE_FOLDER):
        os.remove(os.path.join(CACHE_FOLDER, filename))
    print("startup cache cleared")


if __name__ == "__main__":
    clear_cache()
