import datetime as dt
import pandas as pd
import numpy as np

from src.certificate import final_fixing_date, redemption_date, CALL_OBSERVATION_DATES, CALL_EARLY_REDEMPTION_DATES


valuation_date = dt.date(2026, 11, 6)

# current price from Yahoo finance TLT
spot_price = 81.85

# SOFR observation for 2026-11-05, available for our valuation snapshot.
# Annualised overnight rate, Actual/360.
SOFR = 0.0392

# Modelling assumption: flat future overnight rate.
# Convert a repeated one-calendar-day accrual factor into an
# annual continuously compounded rate on an Actual/365 Fixed basis.
risk_free_rate = 365.0 * np.log(1 + SOFR / 360.0)

# 13.35% 3y standard annualized vol ## HISTORICAL proxy ## Should be ANNUAL 
volatility = 0.1335

# Approximation: use the trailing cash-distribution yield
# as the model's constant continuous proportional yield.
# This is not an exact conversion of discrete distributions.
distribution_yield = 0.0478


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