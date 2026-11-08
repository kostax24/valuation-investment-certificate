import datetime as dt

# iShares 20+ Year Treasury Bond ETF Bonus Outperformance Certificate

underlying = "TLT" # iShares 20+ Year Treasury Bond ETF

initial_fixing_price = 90.24 # 90.24 USD or 100%
capital_protection_ratio = 1
settlement_currency = "USD"
DENOMINATION = 1_000

bonus_ratio = 1.086 # 108.6%
participation_rate = 2 # 200%
barrier_ratio = 1 # 100% of initial fixing lvl


final_fixing_date = dt.date(2027, 11, 26)
redemption_date = dt.date(2027, 12, 3)

EARLY_REDEMPTION_COUPON = 86.0

CALL_OBSERVATION_DATES: tuple[dt.date, ...] = (
    dt.date(2025, 12, 26),
    dt.date(2026, 1, 26),
    dt.date(2026, 2, 25),
    dt.date(2026, 3, 25),
    dt.date(2026, 4, 27),
    dt.date(2026, 5, 26),
    dt.date(2026, 6, 25),
    dt.date(2026, 7, 27),
    dt.date(2026, 8, 25),
    dt.date(2026, 9, 25),
    dt.date(2026, 10, 26),
    dt.date(2026, 11, 25),
    dt.date(2026, 12, 28),
    dt.date(2027, 1, 25),
    dt.date(2027, 2, 25),
    dt.date(2027, 3, 25),
    dt.date(2027, 4, 26),
    dt.date(2027, 5, 25),
    dt.date(2027, 6, 25),
    dt.date(2027, 7, 26),
    dt.date(2027, 8, 25),
    dt.date(2027, 9, 27),
    dt.date(2027, 10, 25),
)


CALL_EARLY_REDEMPTION_DATES: tuple[dt.date, ...] = (
    dt.date(2026, 1, 6),
    dt.date(2026, 1, 30),
    dt.date(2026, 3, 4),
    dt.date(2026, 4, 1),
    dt.date(2026, 5, 4),
    dt.date(2026, 6, 1),
    dt.date(2026, 7, 2),
    dt.date(2026, 7, 31),
    dt.date(2026, 9, 1),
    dt.date(2026, 10, 2),
    dt.date(2026, 10, 30),
    dt.date(2026, 12, 2),
    dt.date(2027, 1, 4),
    dt.date(2027, 2, 1),
    dt.date(2027, 3, 4),
    dt.date(2027, 4, 5),
    dt.date(2027, 4, 30),
    dt.date(2027, 6, 1),
    dt.date(2027, 7, 2),
    dt.date(2027, 7, 30),
    dt.date(2027, 9, 1),
    dt.date(2027, 10, 1),
    dt.date(2027, 11, 1),
)

if len(CALL_OBSERVATION_DATES) != len(CALL_EARLY_REDEMPTION_DATES):
    raise ValueError(
        "Every call observation date must have a matching redemption date."
    )


