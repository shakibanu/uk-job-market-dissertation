"""
build_roi_datasets.py

This builds the 3 reference datasets needed for the "Is the UK Worth It"
ROI calculator - GDP per capita by country, typical UK tuition fees by
sector, and UK living costs. Tuition doesn't actually vary by country of
origin (everyone pays the same "international" rate for a given course),
so the country-of-origin comparison comes from GDP per capita instead -
that's what makes the ROI genuinely different depending on where a
student is from.

Run this once from the same folder as my other data-cleaning scripts -
it downloads the GDP and population data fresh each time, so it doesn't
need any input files.
"""

import pandas as pd
import urllib.request

GDP_URL = "https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv"
POPULATION_URL = "https://raw.githubusercontent.com/datasets/population/master/data/population.csv"


def download_csv(url, local_filename):
    """Downloads a CSV from the given URL and saves it locally."""
    urllib.request.urlretrieve(url, local_filename)
    return pd.read_csv(local_filename)


def build_gdp_per_capita():
    """GDP per capita by country, computed from World Bank GDP and
    population data (CC-BY-4.0, via the datasets.datahub.io mirror).
    Using 2023 since that's the most recent year both datasets have in
    common - this is a normal lag for World Bank data, not a data
    quality issue."""
    gdp_df = download_csv(GDP_URL, "gdp_raw.csv")
    population_df = download_csv(POPULATION_URL, "population_raw.csv")

    YEAR = 2023
    gdp_year = gdp_df[gdp_df["Year"] == YEAR][["Country Name", "Country Code", "Value"]]
    gdp_year = gdp_year.rename(columns={"Value": "GDP_USD"})

    population_year = population_df[population_df["Year"] == YEAR][["Country Code", "Value"]]
    population_year = population_year.rename(columns={"Value": "Population"})

    gdp_per_capita = gdp_year.merge(population_year, on="Country Code", how="inner")
    gdp_per_capita["GDP_Per_Capita_USD"] = gdp_per_capita["GDP_USD"] / gdp_per_capita["Population"]
    gdp_per_capita = gdp_per_capita.rename(columns={"Country Name": "Country"})
    gdp_per_capita = gdp_per_capita[["Country", "Country Code", "GDP_Per_Capita_USD"]]
    gdp_per_capita = gdp_per_capita.round({"GDP_Per_Capita_USD": 0})

    gdp_per_capita.to_csv("data/GDP_Per_Capita_By_Country.csv", index=False)
    print(f"saved GDP per capita for {len(gdp_per_capita)} countries")
    return gdp_per_capita


def build_tuition_by_sector():
    """Typical UK postgraduate tuition fees by sector, compiled from
    published figures (British Council, Complete University Guide).
    Using postgraduate taught masters ranges since that's the more
    realistic level for this platform's audience. Healthcare uses the
    general health-related masters range (Public Health, Health Data
    Science etc), not full clinical Medicine degrees, which are priced
    far higher and would skew the figure - worth double-checking against
    Brookes' own published fees if a more precise number is needed."""
    tuition_data = [
        {"Sector": "Technology", "Tuition_Min_GBP": 17000, "Tuition_Max_GBP": 28000, "Tuition_Mid_GBP": 22500},
        {"Sector": "Engineering", "Tuition_Min_GBP": 18000, "Tuition_Max_GBP": 30000, "Tuition_Mid_GBP": 24000},
        {"Sector": "Finance", "Tuition_Min_GBP": 15000, "Tuition_Max_GBP": 28000, "Tuition_Mid_GBP": 21500},
        {"Sector": "Healthcare", "Tuition_Min_GBP": 15000, "Tuition_Max_GBP": 25000, "Tuition_Mid_GBP": 20000},
        {"Sector": "Education", "Tuition_Min_GBP": 12000, "Tuition_Max_GBP": 20000, "Tuition_Mid_GBP": 16000},
    ]
    tuition_df = pd.DataFrame(tuition_data)
    tuition_df.to_csv("data/Tuition_By_Sector.csv", index=False)
    print(f"saved tuition estimates for {len(tuition_df)} sectors")
    return tuition_df


def build_living_costs():
    """UK living costs, from the official Student visa financial
    requirement figures (gov.uk / UKCISA) - these are the government's
    own minimum monthly living cost estimates, so they're a defensible,
    citable source rather than a guess."""
    living_cost_data = [
        {"Region": "London", "Monthly_Living_Cost_GBP": 1334},
        {"Region": "Outside London", "Monthly_Living_Cost_GBP": 1023},
    ]
    living_cost_df = pd.DataFrame(living_cost_data)
    living_cost_df.to_csv("data/Living_Costs_UK.csv", index=False)
    print(f"saved living cost estimates for {len(living_cost_df)} regions")
    return living_cost_df


if __name__ == "__main__":
    build_gdp_per_capita()
    build_tuition_by_sector()
    build_living_costs()
    print("all 3 ROI reference datasets saved to data/")
