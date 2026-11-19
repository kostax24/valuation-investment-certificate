import pandas as pd

from src.market_data import valuation_date, get_treasury_par_yields
from src.curves import build_treasury_discount_curve

par_yields = get_treasury_par_yields(valuation_date)

curve, helpers = build_treasury_discount_curve(
    valuation_date,
    par_yields,
)

print("Valuation date:", valuation_date)
print(par_yields)

labels = [
    "1M", "3M", "6M", "1Y", "2Y", "3Y",
    "5Y", "7Y", "10Y", "20Y", "30Y",
]

repricing = pd.DataFrame([
    {
        "tenor": label,
        "input_quote": helper.quote().value(),
        "model_quote": helper.impliedQuote(),
    }
    for label, helper in zip(labels, helpers)
])

repricing["error"] = (
    repricing["model_quote"] - repricing["input_quote"]
)

print(repricing)

curve_nodes = pd.DataFrame({
    "date": [d.ISO() for d in curve.dates()],
    "discount_factor": list(curve.data()),
})

print(curve_nodes)

