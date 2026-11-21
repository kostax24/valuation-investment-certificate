import datetime as dt
import pandas as pd
import numpy as np

from src.certificate import final_fixing_date, redemption_date, CALL_OBSERVATION_DATES, CALL_EARLY_REDEMPTION_DATES

# valuation_date = dt.date(2025, 12, 3)
# valuation_date = dt.date(2026, 10, 23)
valuation_date = dt.date(2026, 11, 19)

# price from Yahoo finance TLT 2025-03-12
# spot_price = 89.06

# price from Yahoo finance TLT 2026-10-23
# spot_price = 81.34

# price from Yahoo finance TLT 2026-11-19
spot_price = 80.35


# SOFR observation for 2026-03-12, available for our valuation snapshot.
# Annualised overnight rate, Actual/360.
# SOFR = 0.0395

# SOFR observation for 2026-10-23
# SOFR = 0.0392

# SOFR observation for 2026-11-19,
SOFR = 0.0391


# Modelling assumption: flat future overnight rate.
# Convert a repeated one-calendar-day accrual factor into an
# annual continuously compounded rate on an Actual/365 Fixed basis.
risk_free_rate = 365.0 * np.log(1 + SOFR / 360.0)

## HISTORICAL proxy ## Should be ANNUAL

# 3y standard annualized vol as 2026-12-03
# volatility = 0.154

# 3y standard annualized vol as 2026-10-23
#volatility = 0.1294

# 3y standard annualized vol as 2026-11-19
volatility = 0.1252

# Approximation: using the 12M trailing cash-distribution yield
# as the model's constant continuous proportional yield.
# This is not an exact conversion of discrete distributions.

# as 2025-12-03
# distribution_yield = 0.043446

# as 2025-10-23
# distribution_yield = 0.04784

# as 2026-11-19
distribution_yield = 0.048654


# TIME
time_to_fixing_days = (final_fixing_date - valuation_date).days
time_to_redemption_days = (redemption_date - valuation_date).days

# Actual/365 Fixed YEAR fraction
time_to_fixing = time_to_fixing_days / 365.0
time_to_redemption = time_to_redemption_days / 365.0

## TREE estimation inputs
steps_per_day = 2
n_steps = time_to_fixing_days * steps_per_day


## Working on CALLABLE section
# Dates from EARLY CALL BERMUDIAN OPTION
call_schedule = tuple(
    zip(CALL_OBSERVATION_DATES, CALL_EARLY_REDEMPTION_DATES)
)

future_call_schedule = tuple(
    (observation_date, payment_date)
    for observation_date, payment_date in call_schedule
    if observation_date > valuation_date
)

call_observation_dates = np.array([
    (observation_date - valuation_date).days / 365
    for observation_date, payment_date in future_call_schedule
])

call_payment_dates = np.array([
    (payment_date - valuation_date).days / 365
    for observation_date, payment_date in future_call_schedule
])

############################################################################
### Market Data Setting for Hull-White model

# getting the Treasury Yield Curve (its par yield curve)

import pandas_datareader.data as web

def get_treasury_par_yields(valuation_date):
    valuation_date = pd.to_datetime(valuation_date)
    series = {
        "DGS1MO": "1M",
        "DGS3MO": "3M",
        "DGS6MO": "6M",
        "DGS1": "1Y",
        "DGS2": "2Y",
        "DGS3": "3Y",
        "DGS5": "5Y",
        "DGS7": "7Y",
        "DGS10": "10Y",
        "DGS20": "20Y",
        "DGS30": "30Y",
    }

    raw_yields = web.DataReader(
        list(series),
        "fred",
        start=valuation_date - pd.Timedelta(days=30),
        end = valuation_date,
    )

    raw_yields = raw_yields.rename(columns=series).sort_index()

    complete_yields = raw_yields.loc[
        raw_yields.index <= valuation_date
    ].dropna(how="any")

    if complete_yields.empty:
        raise ValueError("No complete Treasury yield snapshot was found.")

    par_yields_pct = complete_yields.loc[
        pd.Timestamp(valuation_date)
    ].copy()

    par_yields = par_yields_pct / 100

    return par_yields

