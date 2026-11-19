import pandas as pd
import QuantLib as ql

def load_treasury_holdings(file_path):
    holdings = pd.read_csv(
        file_path,
        sep=";",
        skiprows=10,
        thousands=",",
        encoding="cp1252"
    )

    bonds = holdings.loc[
        holdings["Sector"] == "Treasuries"
    ].copy()

    numeric_columns = [
        "Par_Value",
        "Market_Value",
        "Price",
        "Coupon_pct",
        "Weight_pct",
    ]

    for column in numeric_columns:
        bonds[column] = pd.to_numeric(
            bonds[column].astype(str).str.replace(",", "", regex=False),
            errors="raise",
        )

    for column in ["Maturity", "Accrual_Date"]:
        bonds[column] = pd.to_datetime(
            bonds[column],
            format="%b %d, %Y",
        )

    bonds["coupon_rate"] = bonds["Coupon_pct"] / 100.0

    return bonds

def build_treasury_basket(bonds, curve):
    """Build the bonds and calculate their values on the curve reference date."""
    ql_valuation_date = curve.referenceDate()
    ql.Settings.instance().evaluationDate = ql_valuation_date

    calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
    curve_handle = ql.YieldTermStructureHandle(curve)
    bond_engine = ql.DiscountingBondEngine(curve_handle)

    bond_objects = {}
    results = []

    for _, row in bonds.iterrows():
        start_date = row["Accrual_Date"]
        maturity_date = row["Maturity"]

        ql_start_date = ql.Date(
            start_date.day,
            start_date.month,
            start_date.year,
        )

        ql_maturity_date = ql.Date(
            maturity_date.day,
            maturity_date.month,
            maturity_date.year,
        )

        schedule = ql.Schedule(
            ql_start_date,
            ql_maturity_date,
            ql.Period(ql.Semiannual),
            calendar,
            ql.Unadjusted,
            ql.Unadjusted,
            ql.DateGeneration.Backward,
            False,
        )

        day_count = ql.ActualActual(ql.ActualActual.Bond, schedule)

        bond = ql.FixedRateBond(
            0,
            float(row["Par_Value"]),
            schedule,
            [float(row["coupon_rate"])],
            day_count,
            ql.Following,
            100.0,
            ql_start_date,
        )

        if bond.cashflows()[-1].date() > curve.maxDate():
            raise ValueError(f"Curve does not cover all payments for {row['CUSIP']}.")

        bond.setPricingEngine(bond_engine)
        bond_objects[row["CUSIP"]] = bond

        model_value = bond.NPV()
        reported_value = float(row["Market_Value"])

        results.append({
            "CUSIP": row["CUSIP"],
            "maturity": maturity_date,
            "coupon_rate": row["coupon_rate"],
            "par_value": row["Par_Value"],
            "model_value": model_value,
            "reported_market_value": reported_value,
        })

    basket_values = pd.DataFrame(results)
    basket_values["difference"] = (
        basket_values["model_value"]
        - basket_values["reported_market_value"]
    )

    basket_values["difference_pct"] = (
        100.0
        * basket_values["difference"]
        / basket_values["reported_market_value"]
    )

    return bond_objects, basket_values

def get_basket_cashflows(bond_objects, reference_date):
    """Return dated dollar payments strictly after the reference date."""
    return [
        (cf.date(), cf.amount())
        for bond in bond_objects.values()
        for cf in bond.cashflows()
        if cf.date() > reference_date
    ]

def basket_value_at_rate(as_of_date, short_rate, cashflows, curve, hw_model):
    """Value remaining dollar payments strictly after the reference date."""
    t = curve.timeFromReference(as_of_date)

    return sum(
        amount * hw_model.discountBond(
            t,
            curve.timeFromReference(payment_date),
            short_rate
        )
        for payment_date, amount in cashflows
        if payment_date > as_of_date
    )
