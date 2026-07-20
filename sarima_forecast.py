"""
sarima_forecast.py

This file fits a SARIMA model for each sector and generates a forecast
for the next four quarters.

The models are created once when the dashboard starts so they can be
reused by the callbacks without fitting them again.
"""

import warnings
import pmdarima as pm
from data_loader import master_df, SECTORS

warnings.filterwarnings("ignore")


def fit_sarima_for_all_sectors():
    """Fits a SARIMA model per sector and returns a dictionary of results,
    keyed by sector name."""
    results = {}

    # Fit a separate SARIMA model for each sector
    for sector in SECTORS:
        # Get the vacancy data for the current sector
        sector_data = master_df[master_df["Sector"] == sector].sort_values("Quarter")
        vacancy_series = sector_data["Vacancy_Count"].values
        last_quarter_label = sector_data["Quarter"].iloc[-1]

        # Fit the SARIMA model using the sector's historical vacancy data
        sarima_model = pm.auto_arima(
            vacancy_series, seasonal=True, m=4,
            start_p=0, start_q=0, max_p=3, max_q=3,
            start_P=0, start_Q=0, max_P=2, max_Q=2,
            d=None, D=None, stepwise=True,
            error_action="ignore", suppress_warnings=True,
            information_criterion="aic",
        )
        # Generate the 4-quarter forecast with 80% and 95% confidence intervals
        forecast_80, interval_80 = sarima_model.predict(n_periods=4, return_conf_int=True, alpha=0.20)
        forecast_95, interval_95 = sarima_model.predict(n_periods=4, return_conf_int=True, alpha=0.05)

        # Working out the labels for the next 4 quarters,
        # e.g. 2025-Q4 -> 2026-Q1, Q2, Q3, Q4
        year, quarter_number = int(last_quarter_label.split("-Q")[0]), int(last_quarter_label.split("-Q")[1])
        future_quarters = []
        for _ in range(4):
            quarter_number += 1
            if quarter_number > 4:
                quarter_number = 1
                year += 1
            future_quarters.append(f"{year}-Q{quarter_number}")

        # Store the forecast results for the current sector
        results[sector] = {
            "order": sarima_model.order,
            "seasonal_order": sarima_model.seasonal_order,
            "aic": round(sarima_model.aic(), 1),
            "bic": round(sarima_model.bic(), 1),
            "future_quarters": future_quarters,
            "forecast": [round(float(v)) for v in forecast_80],
            "ci80_lower": [round(float(v)) for v in interval_80[:, 0]],
            "ci80_upper": [round(float(v)) for v in interval_80[:, 1]],
            "ci95_lower": [round(float(v)) for v in interval_95[:, 0]],
            "ci95_upper": [round(float(v)) for v in interval_95[:, 1]],
        }

    return results


# Fit the models once so they can be used throughout the dashboard
SARIMA_RESULTS = fit_sarima_for_all_sectors()
print("SARIMA models fitted for all sectors:", {k: v["order"] for k, v in SARIMA_RESULTS.items()})
