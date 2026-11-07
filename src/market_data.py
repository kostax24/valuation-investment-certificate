import datetime as dt
import pandas as pd
import numpy as np

from src.certificate import final_fixing_date, redemption_date

valuation_date = dt.date(2026, 11, 6)

# current price from Yahoo finance TLT
spot_price = 81.93

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
time_to_fixing_days = final_fixing_date - valuation_date
time_to_redemption_days = redemption_date - valuation_date

# Actual/365 Fixed YEAR fraction
time_to_fixing = time_to_fixing_days.days / 365.0
time_to_redemption = time_to_redemption_days.days / 365.0