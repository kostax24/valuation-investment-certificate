from src.models import simulate_gbm_terminal_prices
from src.payoff import maturity_payoff
import numpy as np

def price_non_callable(
    spot_price: float,
    time_to_fixing: float,
    volatility: float,
    risk_free_rate: float,
    distribution_yield: float,
    time_to_redemption: float,
    random_seed: int,
    n_simulations: int = 1_000,
    return_simulations: bool = False,
) -> dict[str, float | np.ndarray]:
    """Estimate the clean non-callable value and Monte Carlo standard error."""

    terminal_prices = simulate_gbm_terminal_prices(
        spot_price,
        time_to_fixing,
        risk_free_rate,
        distribution_yield,
        volatility,
        n_simulations=n_simulations,
        random_seed=random_seed,
    )

    payoffs = np.array([
        maturity_payoff(final_price)
        for final_price in terminal_prices
    ])

    discount_factor = np.exp(-risk_free_rate * time_to_redemption)
    discounted_payoffs = payoffs * discount_factor

    price_estimate = np.mean(discounted_payoffs)

    standard_error = (
        np.std(discounted_payoffs, ddof=1)
        / np.sqrt(n_simulations)
    )

    result = {
        "price": float(price_estimate),
        "standard_error": float(standard_error),
    }

    if return_simulations:
        result["terminal_prices"] = terminal_prices
        result["payoffs"] = payoffs

    return result
    
    

