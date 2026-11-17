import QuantLib as ql

def build_treasury_discount_curve(valuation_date, par_yields):
    """Build an approximate Treasury zero coupon discount curve from decimal par yields. (bootstrap)

      Uses synthetic simple-interest instruments for 1M–6M and
      synthetic semiannual par bonds for 1Y–30Y.

      Sets QuantLib's global evaluation date.

    Parameters
    ----------
    valuation_date : date-like
        Curve reference date and synthetic instrument start date.
    par_yields : pandas.Series
        Finite decimal yields indexed by the required tenor labels.
        No percentage conversion is performed here.

    Returns
    -------
    curve : QuantLib.PiecewiseLogLinearDiscount
        Bootstrapped discount curve.
    helpers : list
        Calibration helpers ordered according to CURVE_LABELS.
    """
    ql_valuation_date = ql.Date(
        valuation_date.day,
        valuation_date.month,
        valuation_date.year
    )

    ql.Settings.instance().evaluationDate = ql_valuation_date

    tenors = {
        "1M": ql.Period(1, ql.Months),
        "3M": ql.Period(3, ql.Months),
        "6M": ql.Period(6, ql.Months),
        "1Y": ql.Period(1, ql.Years),
        "2Y": ql.Period(2, ql.Years),
        "3Y": ql.Period(3, ql.Years),
        "5Y": ql.Period(5, ql.Years),
        "7Y": ql.Period(7, ql.Years),
        "10Y": ql.Period(10, ql.Years),
        "20Y": ql.Period(20, ql.Years),
        "30Y": ql.Period(30, ql.Years),
    }

    assert set(par_yields.index) == set(tenors)

    calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)

    short_end_day_count = ql.Actual365Fixed() # Use actual elapsed days divided by 365


    # A helper tells QuantLib how an input quote relates to discount factors.
    # DepositRateHelper describes a simple-interest instrument using its rate, tenor,
    # settlement lag, calendar and day-count convention.

    # Short-end helpers: 1M, 3M, 6M
    short_end_helpers = []

    for label in ["1M", "3M", "6M"]:
        helper = ql.DepositRateHelper(
            float(par_yields.loc[label]), # input yield, decimal form
            tenors[label],
            0, # settlement lag
            calendar, # US Government Bond
            ql.ModifiedFollowing, #Move to the next business day unless that changes the month; then move backward
            False, # Do not force end-of-month preservation
            short_end_day_count,
        )

        short_end_helpers.append(helper)

    # Synthetic par-bond helpers: 1Y-30Y
    bond_labels = ["1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

    bond_helpers = []

    for label in bond_labels:
        maturity_date = ql_valuation_date + tenors[label]

        schedule = ql.Schedule(
            ql_valuation_date,
            maturity_date,
            ql.Period(ql.Semiannual),
            calendar,
            ql.Unadjusted, # Keep contractual coupon accrual dates on their original calendar dates
            ql.Unadjusted,
            ql.DateGeneration.Backward,
            False,
        )

        coupon_day_count = ql.ActualActual( # Calculate coupon accrual fractions using the bond’s schedule
            ql.ActualActual.Bond,
            schedule,
        )

        helper = ql.FixedRateBondHelper(
            ql.QuoteHandle(ql.SimpleQuote(100.0)),
            0, # zero settlement days
            100.0,
            schedule,
            [float(par_yields.loc[label])],
            coupon_day_count,
            ql.Following, # Move payments falling on non-business days to the next business day
            100.0,
            ql_valuation_date,
        )

        bond_helpers.append(helper)

    helpers = short_end_helpers + bond_helpers

    assert len(helpers) == len(tenors)

    curve_day_count = ql.Actual365Fixed()

    curve = ql.PiecewiseLogLinearDiscount(
        ql_valuation_date,
        helpers,
        curve_day_count,
    )

    # Request a discount factor to trigger the bootstrap
    curve.discount(helpers[-1].latestDate())

    return curve, helpers
