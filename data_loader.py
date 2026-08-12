"""
data_loader.py

This file loads the datasets and stores the shared variables used across
the dashboard. The data is loaded once here and then reused by the other
files in the project.
"""

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

# Trend series for the vacancy sparkline on the overview cards
national_trend = master_df.groupby("Quarter")["Vacancy_Count"].sum().tolist()

# Store the Skilled Worker salary thresholds for each year
SALARY_THRESHOLDS = {2021: 26200, 2022: 26200, 2023: 26200, 2024: 38700, 2025: 41700}
