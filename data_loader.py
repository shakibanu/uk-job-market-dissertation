"""
data_loader.py

This file loads the datasets and stores the shared variables used across
the dashboard. The data is loaded once here and then reused by the other
files in the project.
"""

import json
import pandas as pd

# Loading the cleaned datasets I built earlier in the project
master_df = pd.read_csv("data/Master_Dataset_v1.csv")
sponsors_df = pd.read_csv("data/HO_Sponsors_Clean.csv")
adzuna_df = pd.read_csv("data/Adzuna_Clean.csv")
sector_mapping_df = pd.read_csv("data/Final_Matched_Companies.csv")

# Loading the datasets used for the Is the UK Worth It ROI calculator
gdp_df = pd.read_csv("data/GDP_Per_Capita_By_Country.csv")
tuition_df = pd.read_csv("data/Tuition_By_Sector.csv")
living_cost_df = pd.read_csv("data/Living_Costs_UK.csv")
COUNTRIES = sorted(gdp_df["Country"].unique())

# Loading the regional data and merging the Region into sponsors_df,
# which already has Sector - this way both are available together for
# the regional heatmap's sector filter, without redoing any matching.
# This is a genuinely different measure from visa grants - it's a count
# of licensed sponsor organisations by region, matched from the City
# field with 77.63% coverage (94,718 of 122,015) - the unmapped 22.37%
# is kept visible in the UI, not silently dropped.
region_df = pd.read_csv("data/Sponsors_By_Region.csv")
# HO_Sponsors_Clean.csv has some pre-existing duplicate Organisation rows
# (same company listed more than once in the original Home Office data) -
# deduplicating the lookup table first so the merge doesn't fan out and
# inflate the row count
region_df_dedup = region_df.drop_duplicates(subset="Organisation")[["Organisation", "Region"]]
sponsors_df = sponsors_df.merge(region_df_dedup, on="Organisation", how="left")
REGION_MAPPED_COUNT = sponsors_df["Region"].notna().sum()
REGION_TOTAL_COUNT = len(sponsors_df)

# UK region boundary geometry for the 3D globe on the Regional tab
# (S4-15). Built from official ONS Open Geography Portal boundaries
# (Open Government Licence v3) - see build_region_boundaries.py for the
# exact source datasets, the "Yorkshire and The Humber" -> "Yorkshire
# and the Humber" naming fix, and a note on the two source files using
# different generalisation levels. Loaded once here, like every other
# dataset, and reused by the globe callback.
with open("data/UK_Region_Boundaries.geojson") as f:
    UK_REGION_GEOJSON = json.load(f)
UK_REGION_NAMES = sorted(feat["properties"]["Region"] for feat in UK_REGION_GEOJSON["features"])

# The Migration Advisory Committee's Skilled Worker 5-year stay rate by
# region - a retention measure, not a count of sponsors or visa grants.
# Kept as its own separate dataframe deliberately, since it must never
# be combined or blended with the sponsor count above.
mac_stay_rate_df = pd.read_csv("data/MAC_Stay_Rate_By_Region.csv")

# Match sponsor companies with Adzuna job postings using company names
sponsors_df["match_name"] = sponsors_df["Organisation"].str.upper().str.strip()
# Count the number of active job postings for each company
adzuna_job_counts = (
    adzuna_df.assign(match_name=adzuna_df["company"].str.upper().str.strip())
    .groupby("match_name").size().reset_index(name="Active_Job_Count")
)
sponsors_df = sponsors_df.merge(adzuna_job_counts, on="match_name", how="left")

# Add the sector for each sponsor, matched against Companies House SIC
# data using the staged matching pipeline (exact, normalised, trading
# name and fuzzy matching combined). About 25% of sponsors end up with a
# sector - most licensed sponsors aren't in the 5 sectors this project
# tracks, so that's expected, not a matching problem.
sector_mapping_df = sector_mapping_df.rename(columns={"Company_Name": "match_name", "Industry": "Sector"})
sector_mapping_df["match_name"] = sector_mapping_df["match_name"].str.upper().str.strip()
# A handful of sponsor names appear more than once in the original
# register (same company, slightly different casing), which means the
# matched file has a few duplicate keys too - keeping just the first one
# per company so the merge below doesn't create extra rows
sector_mapping_df = sector_mapping_df.drop_duplicates(subset="match_name")[["match_name", "Sector"]]
sponsors_df = sponsors_df.merge(sector_mapping_df, on="match_name", how="left")

sponsors_df = sponsors_df.drop(columns=["match_name"])

SECTORS = sorted(master_df["Sector"].unique())

# Theme colours - these need to match assets/style.css, since Plotly
# charts can't read colours from the CSS file directly
SURFACE = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT = "#111827"
TEXT_SECONDARY = "#6B7280"
BLUE = "#2563EB"
TEAL = "#16A34A"   # used for success/positive indicators
AMBER = "#D97706"  # used for warnings and thresholds
DANGER = "#DC2626"

# These are the summary numbers shown on the Overview tab
latest_year = master_df["Year"].max()
total_sponsors = len(sponsors_df)
total_vacancies_latest = master_df[master_df["Year"] == latest_year]["Vacancy_Count"].sum()
n_sectors = master_df["Sector"].nunique()

# Trend series for the vacancy sparkline on the overview cards - this
# stays quarterly, since the sparkline is meant to show the shape of the
# trend over time, not just two points
national_trend = master_df.groupby("Quarter")["Vacancy_Count"].sum().tolist()

# Separate annual totals, used specifically for the +/-% badge next to
# "Vacancies (2025)" - this needs to compare the same kind of number
# (annual total vs annual total), not a single quarter vs a single
# quarter, since the headline figure itself is an annual total
national_trend_annual = master_df.groupby("Year")["Vacancy_Count"].sum().tolist()

# Store the Skilled Worker salary thresholds for each year
SALARY_THRESHOLDS = {2021: 26200, 2022: 26200, 2023: 26200, 2024: 38700, 2025: 41700}

# Loading when each data source was last refreshed by the automated
# pipeline, so the Overview tab can show a genuine timestamp instead of
# a hardcoded date that goes stale the moment it's written. Falling back
# to a placeholder if the file doesn't exist yet - it only gets created
# once the automated refresh has actually run for the first time.
try:
    with open("data/last_refreshed.json") as f:
        LAST_REFRESHED = json.load(f)
except FileNotFoundError:
    LAST_REFRESHED = {}


def get_last_refreshed_display():
    """Turns the last_refreshed.json data into one readable string for
    the Overview tab - showing the oldest of the automated sources,
    since that's the more honest number to show (if Adzuna refreshed
    today but NOMIS hasn't run in 3 weeks, showing today's date would
    be misleading about how current the NOMIS-based charts actually are)."""
    if not LAST_REFRESHED:
        return "Vacancy, salary and visa data current to 2025; job postings current to mid-2026 (automated refresh not yet run)"

    from datetime import datetime
    oldest_source = min(LAST_REFRESHED, key=lambda source: LAST_REFRESHED[source])
    oldest_timestamp = datetime.fromisoformat(LAST_REFRESHED[oldest_source])
    return f"Data last refreshed {oldest_timestamp.strftime('%d %b %Y')} ({oldest_source})"


# Nationality-by-sector data - built from two official Home Office
# files (SOC 2010 edition for 2021 Q1-2024 Q1, SOC 2020 edition for
# 2024 Q4-2026 Q1), validated separately (see build_nationality_dataset.py).
# 2024 Q2-Q3 are genuinely missing from both official sources - they
# don't appear as rows here at all, not as zeros.
nationality_df = pd.read_csv("data/Nationality_By_Sector.csv")

# building an ordered list of every quarter that COULD exist across the
# full period, so the trend chart can show real gaps at the right place
# on the x-axis, instead of the missing quarters just disappearing
ALL_POSSIBLE_QUARTERS = [f"{y} Q{q}" for y in [2021, 2022, 2023, 2024, 2025] for q in [1, 2, 3, 4]] + ["2026 Q1"]
