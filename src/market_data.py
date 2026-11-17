import datetime as dt
import pandas as pd
import numpy as np

from src.certificate import final_fixing_date, redemption_date, CALL_OBSERVATION_DATES, CALL_EARLY_REDEMPTION_DATES


valuation_date = dt.date(2026, 11, 13)

# current price from Yahoo finance TLT
spot_price = 79.38

# SOFR observation for 2026-11-17, available for our valuation snapshot.
# Annualised overnight rate, Actual/360.
SOFR = 0.039

# Modelling assumption: flat future overnight rate.
# Convert a repeated one-calendar-day accrual factor into an
# annual continuously compounded rate on an Actual/365 Fixed basis.
risk_free_rate = 365.0 * np.log(1 + SOFR / 360.0)

# 13.35% 3y standard annualized vol ## HISTORICAL proxy ## Should be ANNUAL 
volatility = 0.133

# Approximation: use the trailing cash-distribution yield
# as the model's constant continuous proportional yield.
# This is not an exact conversion of discrete distributions.
distribution_yield = 0.0493


# TIME
time_to_fixing_days = (final_fixing_date - valuation_date).days
time_to_redemption_days = (redemption_date - valuation_date).days

# Actual/365 Fixed YEAR fraction
time_to_fixing = time_to_fixing_days / 365.0
time_to_redemption = time_to_redemption_days / 365.0

## TREE estimation inputs
steps_per_day = 1
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