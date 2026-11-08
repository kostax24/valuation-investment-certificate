from src.certificate import bonus_ratio, capital_protection_ratio, DENOMINATION, participation_rate, \
    initial_fixing_price, barrier_ratio


def maturity_payoff(final_price):
    """
    Takes final price and based on payoff criteria returns USD amount at redemption.
    """
    ## omitting for now from early calls

    final_lvl = final_price / initial_fixing_price

    if final_lvl <= barrier_ratio:
        return DENOMINATION * capital_protection_ratio

    elif final_lvl <= bonus_ratio:
        return DENOMINATION * bonus_ratio

    else:
        return DENOMINATION * (
            bonus_ratio
            + participation_rate * (final_lvl - bonus_ratio)
        )


