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

    terminal_prices = spot_price * np.exp(deterministic_part + random_part)

    return terminal_prices

def calculate_crr_parameters(
        time_to_fixing: float,
        n_steps: int,
        risk_free_rate: float,
        distribution_yield: float,
        volatility: float
) -> dict[str, float]:
    """
    Calaculate CRR parameters for a uniform grid.

    Time is measured in years.
    Rates are annual and continuously compounded.
    Volatility is annualized and must be strictly positive.
    """

    inputs = [
        time_to_fixing,
        risk_free_rate,
        distribution_yield,
        volatility
    ]

    time_step = time_to_fixing / n_steps

    up_factor = np.exp(volatility * np.sqrt(time_step))
    down_factor = 1 / up_factor

    growth_factor = np.exp(
        (risk_free_rate - distribution_yield) * time_step
    )

    up_probability = (
        (growth_factor - down_factor)
        / (up_factor - down_factor)
    )

    discount_factor = np.exp(-risk_free_rate * time_step)

    return {
        "time_step": float(time_step),
        "up_factor": float(up_factor),
        "down_factor": float(down_factor),
        "up_probability": float(up_probability),
        "discount_factor": float(discount_factor),
    }

def calculate_crr_node_prices(
    spot_price: float,
    step_index: int,
    up_factor: float,
    down_factor: float,
) -> np.ndarray:
    """Return underlying prices at one CRR tree layer.

    Node j represents j moves up and step_index -j down moves.
    Prices are returned is ascending order.
    """
    up_moves = np.arange(step_index + 1)
    down_moves = step_index - up_moves

    log_prices = (
        np.log(spot_price)
        + up_moves * np.log(up_factor)
        + down_moves * np.log(down_factor)
    )

    return np.exp(log_prices)





























