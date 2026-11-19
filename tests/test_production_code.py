from src.market_data import (
    valuation_date,
    get_treasury_par_yields,
)
from src.curves import build_treasury_discount_curve

par_yields = get_treasury_par_yields(valuation_date)

curve, helpers = build_treasury_discount_curve(
    valuation_date,
    par_yields,
)

import csv
import pandas as pd

holdings = pd.read_csv(
    r"C:\Users\kosta\Development\Active\valuation-investment-certificate\data\raw\tlt_holdings_clean.csv",
    sep=";",
    skiprows=10,
    thousands=",",
    encoding="cp1252"
)

bonds = holdings.loc[
    holdings["Sector"] == "Treasuries"
].copy()

numeric_columns = [
    "Par_Value",
    "Market_Value",
    "Price",
    "Coupon_pct",
    "Weight_pct",
]

for column in numeric_columns:
    bonds[column] = pd.to_numeric(
        bonds[column].astype(str).str.replace(",", "", regex=False),
        errors="raise",
    )

for column in ["Maturity", "Accrual_Date"]:
    bonds[column] = pd.to_datetime(
        bonds[column],
        format="%b %d, %Y",
    )

bonds["coupon_rate"] = bonds["Coupon_pct"] / 100.0

# print(
#     bonds[
#         [
#             "CUSIP",
#             "coupon_rate",
#             "Accrual_Date",
#             "Maturity",
#             "Par_Value",
#             "Market_Value",
#         ]
#     ].head()
# )
#
# print("Number of Treasury positions:", len(bonds))
# print("Total Treasury market value:", bonds["Market_Value"].sum())

import QuantLib as ql

ql_valuation_date = curve.referenceDate()
ql.Settings.instance().evaluationDate = ql_valuation_date

# Temporary date checks
# print("Input valuation date:", valuation_date)
# print("Curve reference date:", curve.referenceDate().ISO())
# print("QuantLib evaluation date:", ql.Settings.instance().evaluationDate.ISO())

calendar = ql.UnitedStates(
    ql.UnitedStates.GovernmentBond
)

curve_handle = ql.YieldTermStructureHandle(curve)

bond_engine = ql.DiscountingBondEngine(curve_handle)

bond_objects = {}
results = []

for _, row in bonds.iterrows():
    start_date = row["Accrual_Date"]
    maturity_date = row["Maturity"]

    ql_start_date = ql.Date(
        start_date.day,
        start_date.month,
        start_date.year,
    )

    ql_maturity_date = ql.Date(
        maturity_date.day,
        maturity_date.month,
        maturity_date.year,
    )

    schedule = ql.Schedule(
        ql_start_date,
        ql_maturity_date,
        ql.Period(ql.Semiannual),
        calendar,
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )

    day_count = ql.ActualActual(
        ql.ActualActual.Bond,
        schedule
    )

    bond = ql.FixedRateBond(
        0,
        float(row["Par_Value"]),
        schedule,
        [float(row["coupon_rate"])],
        day_count,
        ql.Following,
        100.0,
        ql_start_date,
    )

    if bond.cashflows()[-1].date() > curve.maxDate():
        raise ValueError(
            f"Curve does not cover all payments for {row['CUSIP']}."
        )

    bond.setPricingEngine(bond_engine)

    model_value = bond.NPV()
    reported_value = float(row["Market_Value"])

    bond_objects[row["CUSIP"]] = bond

    results.append({
        "CUSIP": row["CUSIP"],
        "maturity": maturity_date,
        "coupon_rate": row["coupon_rate"],
        "par_value": row["Par_Value"],
        "model_value": model_value,
        "reported_market_value": reported_value,
    })

basket_values = pd.DataFrame(results)

basket_values["difference"] = (
    basket_values["model_value"]
    - basket_values["reported_market_value"]
)

basket_values["difference_pct"] = (
    100.0
    * basket_values["difference"]
    / basket_values["reported_market_value"]
)

print(basket_values)

model_basket_value = basket_values["model_value"].sum()

reported_basket_value = (
    basket_values["reported_market_value"].sum()
)

basket_difference_pct = 100.0 *(
    model_basket_value / reported_basket_value - 1.0
)

# print(f"Model Treasury basket: USD {model_basket_value:,.2f}")
# print(f"Reported Treasury value: USD {reported_basket_value:,.2f}")
# print(f"Difference: {basket_difference_pct:.3f}%")
#
#
# price_checks = []
#
# for _, row in bonds.iterrows():
#     bond = bond_objects[row["CUSIP"]]
#
#     price_checks.append({
#         "CUSIP": row["CUSIP"],
#         "file_price": float(row["Price"]),
#         "reported_value_per_100": (
#             100.0
#             * float(row["Market_Value"])
#             / float(row["Par_Value"])
#         ),
#         "model_clean_price": bond.cleanPrice(),
#         "model_dirty_price": bond.dirtyPrice(),
#         "model_accrued_per_100": bond.accruedAmount(),
#     })
#
# price_checks = pd.DataFrame(price_checks)
#
# print(price_checks.head(10).to_string(index=False))
#
# price_checks["reported_accrued_per_100"] = (
#     price_checks["reported_value_per_100"]
#     - price_checks["file_price"]
# )
#
# print(
#     price_checks[
#         [
#             "CUSIP",
#             "file_price",
#             "reported_value_per_100",
#             "reported_accrued_per_100",
#             "model_accrued_per_100",
#         ]
#     ].head(10).to_string(index=False)
# )
#
# largest_differences = basket_values.loc[
#     basket_values["difference"].abs().nlargest(5).index,
#     ["CUSIP", "model_value", "reported_market_value",
#      "difference", "difference_pct"],
# ]
#
# print(largest_differences.to_string(index=False))


# Provisional parameters for implementation rating
a = 0.10
sigma_r = 0.01

curve_handle = ql.YieldTermStructureHandle(curve)

hw_model = ql.HullWhite( #supplies state-dependent zero-coupon bond prices
    curve_handle,
    a,
    sigma_r,
)

hw_process = ql.HullWhiteProcess( #describes short-rate evolution and will later support simulation
    curve_handle,
    a,
    sigma_r,
)

r0 = hw_process.x0()

curve_fit = []

for maturity_date in curve.dates()[1:]:
    T = curve.timeFromReference(maturity_date)

    curve_df = curve.discount(maturity_date)
    hw_df = hw_model.discountBond(0.0, T, r0)

    curve_fit.append({
        "maturity": maturity_date.ISO(),
        "curve_df": curve_df,
        "hw_df": hw_df,
        "error": hw_df - curve_df,
    })

curve_fit = pd.DataFrame(curve_fit)

print(curve_fit.to_string(index=False))
print("Maximum absolute error:", curve_fit["error"].abs().max())

cashflows = [
    (cf.date(), cf.amount())
    for bond in bond_objects.values()
    for cf in bond.cashflows()
    if cf.date() > curve.referenceDate()
]

def basket_value_at_rate(as_of_date, short_rate):
    t = curve.timeFromReference(as_of_date)

    return sum(
        amount * hw_model.discountBond(
            t,
            curve.timeFromReference(payment_date),
            short_rate
        )
        for payment_date, amount in cashflows
        if payment_date > as_of_date
    )

from math import isclose

r0 = hw_process.x0()
hw_basket_0 = basket_value_at_rate(curve.referenceDate(), r0)

print(f"Original basket:   USD {model_basket_value:,.2f}")
print(f"Hull–White basket: USD {hw_basket_0:,.2f}")

assert isclose(hw_basket_0, model_basket_value, rel_tol=1e-9)

future_date = ql.Date(17, 5, 2027)

low = basket_value_at_rate(future_date, r0 - 0.01)
base = basket_value_at_rate(future_date, r0)
high = basket_value_at_rate(future_date, r0 + 0.01)

for label, value in [("Low rate", low), ("Base rate", base), ("High rate", high)]:
    print(f"{label:10s} USD {value:,.2f}")

assert low > base > high

