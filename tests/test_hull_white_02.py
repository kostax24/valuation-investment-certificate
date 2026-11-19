from math import isclose
from pathlib import Path

import QuantLib as ql

from src.curves import build_treasury_discount_curve
from src.etf_portfolio import (
    basket_value_at_rate,
    build_treasury_basket,
    get_basket_cashflows,
    load_treasury_holdings,
)
from src.hull_white_model import build_hull_white
from src.market_data import get_treasury_par_yields, valuation_date


# 1) Building the initial discount curve
par_yields = get_treasury_par_yields(valuation_date)
curve, _ = build_treasury_discount_curve(valuation_date, par_yields)
reference_date = curve.referenceDate()

# 2) Building and valuing the Treasury basket
project_root = Path(__file__).resolve().parent.parent
holdings_path = project_root / "data" / "raw" / "tlt_holdings_clean.csv"

bonds = load_treasury_holdings(holdings_path)
bond_objects, basket_values = build_treasury_basket(bonds, curve)
cashflows = get_basket_cashflows(bond_objects, reference_date)

model_basket_value = basket_values["model_value"].sum()
reported_basket_value = basket_values["reported_market_value"].sum()
basket_difference_pct = 100.0 * (
    model_basket_value / reported_basket_value - 1.0
)

print(f"Valuation date:   {reference_date.ISO()}")
print(f"Treasury holdings: {len(bonds)}")
print(f"Model basket:     USD {model_basket_value:,.2f}")
print(f"Reported basket:  USD {reported_basket_value:,.2f}")
print(f"Difference:       {basket_difference_pct:+.3f}%")

# 3) Building the Hull White with PROVISIONAL parameters a and sigma_r
hw_model, hw_process = build_hull_white(curve, a = 0.10, sigma_r=0.01)
r0 = hw_process.x0()

max_curve_error = max(
    abs(
        hw_model.discountBond(0.0, curve.timeFromReference(date), r0)
        - curve.discount(date)
    )
    for date in curve.dates()[1:]
)

print(f"Maximum Hull–White curve error: {max_curve_error:.3e}")
assert max_curve_error < 1e-10

hw_basket_0 = basket_value_at_rate(
    reference_date, r0, cashflows, curve, hw_model
)

assert isclose(hw_basket_0, model_basket_value, rel_tol=1e-9)

# 4) Anchoring the proxy and comparing 3 future rate states.
tlt_spot = 79.38 # input from 13.11.26 Yahoo Finance
scale = tlt_spot / hw_basket_0

tlt_proxy_0 = scale * basket_value_at_rate(
    reference_date, r0, cashflows, curve, hw_model
)
assert isclose(tlt_proxy_0, tlt_spot, rel_tol=1e-12)
print(f"Time-zero TLT proxy: USD {tlt_proxy_0:.2f}")

future_date = ql.Date(17,5,2027)
scenarios = [
    ("Low rate", r0 - 0.01),
    ("Base rate", r0),
    ("High rate", r0 + 0.01),
]

proxy_prices = []
print(f"\nTLT proxy scenarios for {future_date.ISO()}:")
for label, short_rate in scenarios:
    future_basket = basket_value_at_rate(
        future_date, short_rate, cashflows, curve, hw_model
    )
    proxy_price = scale * future_basket
    proxy_prices.append(proxy_price)
    print(f"{label:10s} USD {proxy_price:.2f}")

assert proxy_prices[0] > proxy_prices[1] > proxy_prices[2]

