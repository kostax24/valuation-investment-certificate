#### ASSUMPTIONS FOR THESE MODELS
# Default-free contractual payments.
#
# A flat SOFR-derived risk-free rate.
#
# Constant historical volatility.
#
# A constant distribution-yield approximation.
#
# Optimal issuer exercise on the specified dates.


### NO CALL TREE VALUE
import numpy as np
from src.certificate import (
    final_fixing_date,
    redemption_date,
)
from src.market_data import (
    valuation_date,
    spot_price,
    risk_free_rate,
    distribution_yield,
    volatility, steps_per_day,
)
from src.pricing import price_non_callable_tree


tree_result = price_non_callable_tree(
    spot_price=spot_price,
    valuation_date=valuation_date,
    final_fixing_date=final_fixing_date,
    redemption_date=redemption_date,
    risk_free_rate=risk_free_rate,
    distribution_yield=distribution_yield,
    volatility=volatility,
    steps_per_day=2,
)

print(f"No-call tree value: USD {tree_result['price']:.2f}")
print(f"Tree steps: {tree_result['n_steps']}")


### NO CALL TREE VALUE AND CALL TREE VALUE
from src.certificate import (
    CALL_OBSERVATION_DATES,
    CALL_EARLY_REDEMPTION_DATES,
    DENOMINATION,
    EARLY_REDEMPTION_COUPON,
)
from src.pricing import (
    price_non_callable_tree,
    price_callable_tree,
)

tree_inputs = {
    "spot_price": spot_price,
    "valuation_date": valuation_date,
    "final_fixing_date": final_fixing_date,
    "redemption_date": redemption_date,
    "risk_free_rate": risk_free_rate,
    "distribution_yield": distribution_yield,
    "volatility": volatility,
    "steps_per_day": 2,
}

no_call_result = price_non_callable_tree(**tree_inputs)

callable_result = price_callable_tree(
    **tree_inputs,
    call_observation_dates=CALL_OBSERVATION_DATES,
    call_payment_dates=CALL_EARLY_REDEMPTION_DATES,
    early_redemption_amount=(
            DENOMINATION + EARLY_REDEMPTION_COUPON
    ),
)

issuer_call_value = (
    no_call_result["price"] - callable_result["price"]
)

print(f"No-call value: USD {no_call_result['price']:.2f}")
print(f"Callable value: USD {callable_result['price']:.2f}")
print(f"Issuer call-right value: USD {issuer_call_value:.2f}")


### TEST OF DIFFERENT RESOLUTIONS - CONVERGENCE

import pandas as pd
import matplotlib.pyplot as plt


rows = []

for steps_per_day in [1, 2, 3, 4, 6, 8]:
    current_inputs = {
        **tree_inputs,
        "steps_per_day": steps_per_day,
    }

    no_call_result = price_non_callable_tree(**current_inputs)

    callable_result = price_callable_tree(
        **current_inputs,
        call_observation_dates=CALL_OBSERVATION_DATES,
        call_payment_dates=CALL_EARLY_REDEMPTION_DATES,
        early_redemption_amount=(
            DENOMINATION + EARLY_REDEMPTION_COUPON
        ),
    )

    no_call_value = no_call_result["price"]
    callable_value = callable_result["price"]

    assert callable_value <= no_call_value + 1e-10

    rows.append({
        "steps_per_day": steps_per_day,
        "n_steps": no_call_result["n_steps"],
        "no_call_value": no_call_value,
        "callable_value": callable_value,
        "issuer_call_value": no_call_value - callable_value,
    })

convergence = pd.DataFrame(rows)

print(convergence)


convergence["no_call_change"] = (
    convergence["no_call_value"].diff()
)

convergence["callable_change"] = (
    convergence["callable_value"].diff()
)

convergence["call_right_change"] = (
    convergence["issuer_call_value"].diff()
)

print(convergence.round(4))

fig, axes = plt.subplots(1, 2, figsize=(13, 4))

axes[0].plot(
    convergence["n_steps"],
    convergence["no_call_value"],
    marker="o",
    label="Non-callable",
)

axes[0].plot(
    convergence["n_steps"],
    convergence["callable_value"],
    marker="o",
    label="Callable",
)

axes[0].set_title("Certificate values versus tree resolution")
axes[0].set_xlabel("Number of tree steps")
axes[0].set_ylabel("Present value (USD)")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(
    convergence["n_steps"],
    convergence["issuer_call_value"],
    marker="o",
    color="darkorange",
)

axes[1].set_title("Issuer call-right value versus tree resolution")
axes[1].set_xlabel("Number of tree steps")
axes[1].set_ylabel("Present value (USD)")
axes[1].grid(alpha=0.3)

fig.tight_layout()
plt.show()

### NO CALL MONTE CARLO PRICING
# import matplotlib
# matplotlib.use("QtAgg")
#
# import matplotlib.pyplot as plt
#
# from src.market_data import (
#     spot_price,
#     time_to_fixing,
#     risk_free_rate,
#     distribution_yield,
#     volatility,
#     time_to_redemption,
# )
# from src.certificate import (
#     initial_fixing_price,
#     barrier_ratio,
#     bonus_ratio,
# )
# from src.pricing import price_non_callable
#
#
# # Run the valuation and retain the simulations for plotting.
# result = price_non_callable(
#     spot_price=spot_price,
#     time_to_fixing=time_to_fixing,
#     risk_free_rate=risk_free_rate,
#     distribution_yield=distribution_yield,
#     volatility=volatility,
#     time_to_redemption=time_to_redemption,
#     n_simulations=10_000,
#     random_seed=42,
#     return_simulations=True,
# )
#
#
# # Extract the simulated terminal prices and undiscounted payoffs.
# terminal_prices = result["terminal_prices"]
# payoffs = result["payoffs"]
#
#
# # Convert contractual ratios into underlying-price thresholds.
# barrier_price = initial_fixing_price * barrier_ratio
# participation_threshold_price = initial_fixing_price * bonus_ratio
#
# fig, axes = plt.subplots(1, 2, figsize=(13, 4))
#
# # Distribution of TLT prices at final fixing.
# axes[0].hist(
#     terminal_prices,
#     bins=40,
#     color="steelblue",
#     edgecolor="white",
# )
#
# axes[0].axvline(
#     barrier_price,
#     color="red",
#     linestyle="--",
#     label="Barrier",
# )
#
# axes[0].axvline(
#     participation_threshold_price,
#     color="darkorange",
#     linestyle="--",
#     label="Participation threshold",
# )
#
# axes[0].set_title("Simulated TLT prices at final fixing")
# axes[0].set_xlabel("TLT price (USD)")
# axes[0].set_ylabel("Number of simulations")
# axes[0].legend()
#
#
# # Distribution of undiscounted payments at redemption.
# axes[1].hist(
#     payoffs,
#     bins=40,
#     color="seagreen",
#     edgecolor="white",
# )
#
# axes[1].set_title("Simulated payments at redemption")
# axes[1].set_xlabel("Redemption payment (USD)")
# axes[1].set_ylabel("Number of simulations")
#
# ### TESTING OF CONVERGENCE
#
# mc_price = result["price"]
# mc_standard_error = result["standard_error"]
#
# convergence["no_call_minus_mc"] = (
#     convergence["no_call_value"] - mc_price
# )
#
# print(f"MC non-callable value: USD {mc_price:.4f}")
# print(f"MC standard error: USD {mc_standard_error:.4f}")
#
# print(convergence.round(4))
#
# fig, ax = plt.subplots(figsize=(8, 4))
#
# ax.plot(
#     convergence["n_steps"],
#     convergence["no_call_value"],
#     marker="o",
#     label="Non-callable tree",
# )
#
# ax.axhline(
#     mc_price,
#     color="black",
#     linestyle="--",
#     label="Monte Carlo estimate",
# )
#
# ax.axhspan(
#     mc_price - 1.96 * mc_standard_error,
#     mc_price + 1.96 * mc_standard_error,
#     color="grey",
#     alpha=0.2,
#     label="Approximate 95% MC interval",
# )
#
# ax.set_title("Non-callable tree versus Monte Carlo")
# ax.set_xlabel("Number of tree steps")
# ax.set_ylabel("Present value (USD)")
# ax.legend()
# ax.grid(alpha=0.3)
#
# fig.tight_layout()
# plt.show()


#### RESULTS INDICATE that Binomial tree pricing and Monte Carlo pricing produce approximately
#### same results of NO CALL price when incorporating the SE of MC. CALL price was only produced by binomial tree.

# WHY are these models inaccurate to price this investment certificate?
#  - TLT is the iShares 20+ Year Treasury Bond ETF. It is a collection
#  of long-term bonds. Binomial model converges to GBM. Standard GBM fails here for three major reasons:

#  1) No Mean Reversion: GBM assumes prices can drift indefinitely upward. In reality, bond prices are
#       tethered to par values and macroeconomic cycles. Interest rates and bond prices exhibit strong mean reversion
#  2) Constant Volatility: GBM assumes constant proportional dollar volatility. For fixed-income products, volatility
#       changes over time as bonds approach maturity (the "pull-to-par" effect) and fluctuates
#       dynamically with the interest rate yield curve.
#  3) Ignoring the Yield Curve: A Bermudan option allows exercise at discrete times in the future.
#       To price it accurately, you must know what the interest rate environment will look like at those
#       specific future dates. A stock-based GBM ignores the term structure of interest rates entirely.