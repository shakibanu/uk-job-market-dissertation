"""
check_manual_sources.py

Home Office Immigration Statistics, ONS ASHE and ONS VACS02 don't have a
proper API the way NOMIS and Adzuna do - they're published as static
Excel files on GOV.UK on a predictable schedule (HO quarterly, ONS ASHE
annually, VACS02 monthly), but there's no endpoint to query for "the
latest one automatically".

Being honest about what this actually does: it can't download and clean
a new release on its own, since the file format sometimes changes
between releases and needs a human to check it still matches what the
cleaning script expects. This is especially true for VACS02, which has
a rolling 3-month-period structure that needs care to map onto calendar
quarters correctly - not something to rebuild unattended. What this
script CAN do is check whether a newer release looks like it exists
yet, by trying the URL pattern these releases normally follow, and flag
it if so - turning "did a new one come out" from something I'd have to
remember to check manually into something that gets flagged
automatically. Nothing here downloads, merges, or replaces any dataset
on its own.
"""

import requests
from datetime import datetime

# the URL patterns these sources have historically followed - worth
# checking these are still accurate if this hasn't been run in a while,
# since GOV.UK/ONS do sometimes restructure their URLs
HO_URL_PATTERN = "https://www.gov.uk/government/statistics/immigration-system-statistics-{quarter}-{year}"
ONS_ASHE_URL_PATTERN = "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/annualsurveyofhoursandearnings/{year}"
VACS02_URL_PATTERN = "https://www.ons.gov.uk/employmentandlabourmarket/peoplenotinwork/unemployment/datasets/vacanciesbyindustryvacs02"


def check_url_exists(url):
    """A HEAD request is enough here - just checking if the page exists
    yet, not downloading its content."""
    try:
        response = requests.head(url, timeout=15, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def check_for_new_releases():
    """Checks whether a newer Home Office, ONS ASHE, or ONS VACS02
    release looks like it's out yet, based on the URL pattern these
    releases follow. Returns a list of anything worth a manual check.
    VACS02's dataset page always shows the current edition rather than
    having a dated URL each month, so this just confirms the page is
    still reachable at the expected address - a genuine format or
    location change would need a human to catch anyway, same as the
    other two sources."""
    today = datetime.utcnow()
    flags = []

    # Home Office releases quarterly - checking the current quarter's URL
    current_quarter = (today.month - 1) // 3 + 1
    ho_url = HO_URL_PATTERN.format(quarter=f"q{current_quarter}", year=today.year)
    if check_url_exists(ho_url):
        flags.append(f"Possible new Home Office release: {ho_url}")

    # ONS ASHE releases annually - checking this year's URL
    ons_url = ONS_ASHE_URL_PATTERN.format(year=today.year)
    if check_url_exists(ons_url):
        flags.append(f"Possible new ONS ASHE release: {ons_url}")

    # ONS VACS02 releases monthly - just confirming the dataset page is
    # reachable, since a new edition replaces the old one at the same
    # URL rather than getting a new dated address
    if check_url_exists(VACS02_URL_PATTERN):
        flags.append(
            f"VACS02 dataset page is live - worth checking whether a newer "
            f"edition has been published since the last manual update: {VACS02_URL_PATTERN}"
        )

    return flags


if __name__ == "__main__":
    flags = check_for_new_releases()
    if flags:
        print("New releases may be available - worth checking manually:")
        for flag in flags:
            print(f"  - {flag}")
        # writing this to a file so the GitHub Actions workflow can pick
        # it up and open an issue, rather than this just printing to a
        # log nobody looks at
        with open("manual_source_flags.txt", "w") as f:
            f.write("\n".join(flags))
    else:
        print("No new Home Office, ONS ASHE, or VACS02 releases detected at the expected URLs.")
