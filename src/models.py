import numpy as np

def simulate_gbm_terminal_prices(
        spot_price: float,
        time_to_fixing: float,
        risk_free_rate: float,
        distribution_yield: float,
        volatility: float,
        random_seed: int,
        n_simulations = 1_000,
) -> np.ndarray:

    """Simulate terminal prices under risk-neutral, constant-parameter GBM."""

    rng = np.random.default_rng(seed=random_seed)
    Z = rng.standard_normal(size=n_simulations)

    deterministic_part = (
                                 risk_free_rate - distribution_yield - (1 / 2 * volatility ** 2)
    ) * time_to_fixing

    random_part = volatility * time_to_fixing ** (1 / 2) * Z

    final_prices = spot_price * np.exp(deterministic_part + random_part)

    return final_prices
