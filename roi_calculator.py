"""
roi_calculator.py

This works out the numbers for the "Is the UK Worth It" section - the
sponsorship activity ranking per sector, and the actual ROI calculation
(cost, salary, break-even year) for a given country and sector.

Kept separate from the dashboard code so the actual maths can be tested
on its own, without needing the whole app running.
"""

import pandas as pd

# Approximate USD to GBP exchange rate - this moves around day to day,
# so treating this as a rough conversion rather than a precise one.
# Worth updating closer to submission if I want a more current figure.
USD_TO_GBP = 0.79

# standard taught masters course length, used as the default
DEFAULT_COURSE_LENGTH_MONTHS = 12


def get_sponsorship_activity_ranking(master_df):
    """Ranks the 5 sectors by visa grants relative to vacancies, for the
    latest year available. This is a relative ranking, not a calibrated
    probability - the raw ratio (visa grants divided by vacancies) comes
    out far too small to mean anything on its own (well under 1%, since
    vacancy counts are on a much bigger scale than visa grant counts),
    so I'm only using it to rank sectors against each other, not as a
    real percentage.

    This is an interim measure until the proper Sponsorship Fit
    Calculator (Random Forest classifier, S4-02/S4-03) is built, which
    will give a genuine company-level prediction instead of this
    sector-level proxy."""
    latest_year = master_df["Year"].max()
    year_data = master_df[master_df["Year"] == latest_year]

    ratios = []
    for sector in sorted(master_df["Sector"].unique()):
        sector_data = year_data[year_data["Sector"] == sector]
        vacancies = sector_data["Vacancy_Count"].sum()
        visa_grants = sector_data["Visa_Grants"].mean()  # annual figure, repeated across quarters
        ratio = visa_grants / vacancies if vacancies else 0
        ratios.append({"Sector": sector, "ratio": ratio})

    ranking_df = pd.DataFrame(ratios).sort_values("ratio", ascending=False).reset_index(drop=True)
    labels = ["Highest", "High", "Medium", "Low", "Lowest"]
    ranking_df["Activity_Level"] = labels[:len(ranking_df)]

    return ranking_df[["Sector", "Activity_Level"]]


def calculate_roi(country, sector, master_df, gdp_df, tuition_df, living_cost_df,
                   region="Outside London", course_length_months=DEFAULT_COURSE_LENGTH_MONTHS,
                   tuition_override=None):
    """Works out the ROI numbers for one country/sector combination -
    total cost, UK salary, home-country equivalent salary, and how many
    years it would take for the UK salary advantage to cover the cost.

    Returns a dictionary of results, or an error message if the country
    or sector isn't found in the data."""
    gdp_row = gdp_df[gdp_df["Country"] == country]
    if gdp_row.empty:
        return {"error": f"'{country}' not found in the GDP dataset"}

    tuition_row = tuition_df[tuition_df["Sector"] == sector]
    if tuition_row.empty:
        return {"error": f"'{sector}' not found in the tuition dataset"}

    living_cost_row = living_cost_df[living_cost_df["Region"] == region]
    if living_cost_row.empty:
        return {"error": f"'{region}' not found in the living cost dataset"}

    tuition = tuition_override if tuition_override is not None else tuition_row["Tuition_Mid_GBP"].iloc[0]
    monthly_living_cost = living_cost_row["Monthly_Living_Cost_GBP"].iloc[0]
    total_cost = tuition + (monthly_living_cost * course_length_months)

    latest_year = master_df["Year"].max()
    sector_salary_data = master_df[(master_df["Sector"] == sector) & (master_df["Year"] == latest_year)]
    uk_salary = sector_salary_data["Median_Salary"].mean()

    gdp_per_capita_usd = gdp_row["GDP_Per_Capita_USD"].iloc[0]
    home_salary_gbp = gdp_per_capita_usd * USD_TO_GBP

    annual_advantage = uk_salary - home_salary_gbp

    if annual_advantage <= 0:
        # the UK salary doesn't actually beat the home-country reference
        # figure under this model - genuine result, not an error, and
        # worth showing honestly rather than hiding
        return {
            "country": country,
            "sector": sector,
            "total_cost": round(total_cost),
            "uk_salary": round(uk_salary),
            "home_salary_gbp": round(home_salary_gbp),
            "annual_advantage": round(annual_advantage),
            "break_even_year": None,
            "breaks_even": False,
        }

    break_even_year = total_cost / annual_advantage

    return {
        "country": country,
        "sector": sector,
        "total_cost": round(total_cost),
        "uk_salary": round(uk_salary),
        "home_salary_gbp": round(home_salary_gbp),
        "annual_advantage": round(annual_advantage),
        "break_even_year": round(break_even_year, 1),
        "breaks_even": True,
    }
