"""
data_loader.py

This file loads the datasets and stores the shared variables used across
the dashboard. Keeping everything here means the data only needs to be
loaded once and can be reused in other files.
"""

import pandas as pd

# Loading the cleaned datasets I built earlier in the project
master_df = pd.read_csv("data/Master_Dataset_v1.csv")
sponsors_df = pd.read_csv("data/HO_Sponsors_Clean.csv")

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

# Store the Skilled Worker salary thresholds used for each year.
SALARY_THRESHOLDS = {2021: 26200, 2022: 26200, 2023: 26200, 2024: 38700, 2025: 41700}
