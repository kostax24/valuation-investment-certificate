from src.models import simulate_gbm_terminal_prices, calculate_crr_parameters, calculate_crr_node_prices
from src.payoff import maturity_payoff
import numpy as np
import datetime as dt

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


def price_non_callable_tree(
    spot_price: float,
    valuation_date: dt.date,
    final_fixing_date: dt.date,
    redemption_date: dt.date,
    risk_free_rate: float,
    distribution_yield: float,
    volatility: float,
    steps_per_day: int = 1,
) -> dict[str, float | int]:
    """Price the non-callable certificate using a uniform CRR tree.

    Uses Actual/365 Fixed and an integer number of steps per calendar day.
    The existing maturity_payoff function supplies the contractual payoff.
    """
    time_to_fixing_days = (final_fixing_date - valuation_date).days
    time_to_redemption_days = (redemption_date - valuation_date).days

    # Actual/365 Fixed YEAR fraction
    time_to_fixing = time_to_fixing_days / 365.0
    time_to_redemption = time_to_redemption_days / 365.0
    n_steps = time_to_fixing_days * steps_per_day

    parameters = calculate_crr_parameters(
        time_to_fixing=time_to_fixing,
        n_steps=n_steps,
        risk_free_rate=risk_free_rate,
        distribution_yield=distribution_yield,
        volatility=volatility,
    )

    # generate underlying prices at final fixing
    terminal_prices = calculate_crr_node_prices(
        spot_price=spot_price,
        step_index=n_steps,
        up_factor=parameters["up_factor"],
        down_factor=parameters["down_factor"],
    )

    # calculate USD payments due at redemption
    maturity_payments = np.array([
        maturity_payoff(price)
        for price in terminal_prices
    ])

    # express terminal certificate values as of final fixing
    fixing_to_redemption = time_to_redemption - time_to_fixing

    node_values = maturity_payments * np.exp(
        -risk_free_rate * fixing_to_redemption
    )

    # roll certificate values
    up_probability = parameters["up_probability"]
    step_discount_factor = parameters["discount_factor"]

    for _ in range(n_steps):
        node_values = step_discount_factor * (
            (1.0 - up_probability) * node_values[:-1]
            + up_probability * node_values[1:]
        )

    return {
        "price": float(node_values[0]),
        "n_steps": int(n_steps),
        "steps_per_day": int(steps_per_day),
        "time_step": parameters["time_step"],
    }

def prepare_tree_call_schedule(
    valuation_date: dt.date,
    final_fixing_date: dt.date,
    call_observation_dates: tuple[dt.date, ...],
    call_payment_dates: tuple[dt.date, ...],
    early_redemption_amount: float,
    risk_free_rate: float,
    steps_per_day: int,
) -> dict[int, float]:
    """ Map call-observation tree steps to observation-date settlement values.

    Assume the certificate is outstanding and no prior call is awaiting payment.
    Observation on the valuation date are treated as already completed.
    """

    call_values_by_step = {}

    for observation_date, payment_date in zip(
        call_observation_dates,
        call_payment_dates,
    ):
        if payment_date < observation_date:
            raise ValueError("Call payment cannot precede observation.")

        if observation_date > final_fixing_date:
            raise ValueError("Call observation cannot follow final fixing.")

        if observation_date <= valuation_date:
            continue

        observation_step = (
            observation_date - valuation_date
        ).days * steps_per_day

        payment_delay = (
            payment_date - observation_date
        ).days / 365.0

        call_value = early_redemption_amount * np.exp(
            -risk_free_rate * payment_delay
        )

        call_values_by_step[observation_step] = float(call_value)

    return call_values_by_step

def price_callable_tree(
    spot_price: float,
    valuation_date: dt.date,
    final_fixing_date: dt.date,
    redemption_date: dt.date,
    risk_free_rate: float,
    distribution_yield: float,
    volatility: float,
    call_observation_dates: tuple[dt.date, ...],
    call_payment_dates: tuple[dt.date, ...],
    early_redemption_amount: float,
    steps_per_day: int = 1,
) -> dict[str, float | int]:
    """Price the callable certificate using a uniform CRR tree.

    Uses Actual/365 Fixed and an integer number of steps per calendar day.
    The existing maturity_payoff function supplies the contractual payoff.
    """
    time_to_fixing_days = (final_fixing_date - valuation_date).days
    time_to_redemption_days = (redemption_date - valuation_date).days

    # Actual/365 Fixed YEAR fraction
    time_to_fixing = time_to_fixing_days / 365.0
    time_to_redemption = time_to_redemption_days / 365.0
    n_steps = time_to_fixing_days * steps_per_day

    call_values_by_step = prepare_tree_call_schedule(
        valuation_date=valuation_date,
        final_fixing_date=final_fixing_date,
        call_observation_dates=call_observation_dates,
        call_payment_dates=call_payment_dates,
        early_redemption_amount=early_redemption_amount,
        risk_free_rate=risk_free_rate,
        steps_per_day=steps_per_day,
    )

    parameters = calculate_crr_parameters(
        time_to_fixing=time_to_fixing,
        n_steps=n_steps,
        risk_free_rate=risk_free_rate,
        distribution_yield=distribution_yield,
        volatility=volatility,
    )

    # generate underlying prices at final fixing
    terminal_prices = calculate_crr_node_prices(
        spot_price=spot_price,
        step_index=n_steps,
        up_factor=parameters["up_factor"],
        down_factor=parameters["down_factor"],
    )

    # calculate USD payments due at redemption
    maturity_payments = np.array([
        maturity_payoff(price)
        for price in terminal_prices
    ])

    # express terminal certificate values as of final fixing
    fixing_to_redemption = time_to_redemption - time_to_fixing

    node_values = maturity_payments * np.exp(
        -risk_free_rate * fixing_to_redemption
    )


    up_probability = parameters["up_probability"]
    step_discount_factor = parameters["discount_factor"]

    # handle a call observation at final fixing, if the schedule permits one
    if n_steps in call_values_by_step:
        node_values = np.minimum(
            node_values,
            call_values_by_step[n_steps],
        )

    # move from final fixing back to valuation
    for step_index in range(n_steps - 1, -1, -1):
        continuation_values = step_discount_factor * (
            (1.0 - up_probability) * node_values[:-1]
            + up_probability * node_values[1:]
        )

        if step_index in call_values_by_step:
            node_values = np.minimum(
                continuation_values,
                call_values_by_step[step_index],
            )
        else:
            node_values = continuation_values


    return {
        "price": float(node_values[0]),
        "n_steps": int(n_steps),
        "steps_per_day": int(steps_per_day),
        "time_step": parameters["time_step"],
    }

