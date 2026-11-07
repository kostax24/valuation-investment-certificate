import matplotlib
matplotlib.use("QtAgg")

import matplotlib.pyplot as plt

from src.market_data import (
    spot_price,
    time_to_fixing,
    risk_free_rate,
    distribution_yield,
    volatility,
    time_to_redemption,
)
from src.certificate import (
    initial_fixing_price,
    barrier_ratio,
    bonus_ratio,
)
from src.pricing import price_non_callable


# Run the valuation and retain the simulations for plotting.
result = price_non_callable(
    spot_price=spot_price,
    time_to_fixing=time_to_fixing,
    risk_free_rate=risk_free_rate,
    distribution_yield=distribution_yield,
    volatility=volatility,
    time_to_redemption=time_to_redemption,
    n_simulations=1_000,
    random_seed=42,
    return_simulations=True,
)

print(f"Estimated value: USD {result['price']:.2f}")
print(
    f"Monte Carlo standard error: "
    f"USD {result['standard_error']:.2f}"
)


# Extract the simulated terminal prices and undiscounted payoffs.
terminal_prices = result["terminal_prices"]
payoffs = result["payoffs"]


# Convert contractual ratios into underlying-price thresholds.
barrier_price = initial_fixing_price * barrier_ratio
participation_threshold_price = initial_fixing_price * bonus_ratio

fig, axes = plt.subplots(1, 2, figsize=(13, 4))

# Distribution of TLT prices at final fixing.
axes[0].hist(
    terminal_prices,
    bins=40,
    color="steelblue",
    edgecolor="white",
)

axes[0].axvline(
    barrier_price,
    color="red",
    linestyle="--",
    label="Barrier",
)

axes[0].axvline(
    participation_threshold_price,
    color="darkorange",
    linestyle="--",
    label="Participation threshold",
)

axes[0].set_title("Simulated TLT prices at final fixing")
axes[0].set_xlabel("TLT price (USD)")
axes[0].set_ylabel("Number of simulations")
axes[0].legend()


# Distribution of undiscounted payments at redemption.
axes[1].hist(
    payoffs,
    bins=40,
    color="seagreen",
    edgecolor="white",
)

axes[1].set_title("Simulated payments at redemption")
axes[1].set_xlabel("Redemption payment (USD)")
axes[1].set_ylabel("Number of simulations")

fig.tight_layout()
plt.show()