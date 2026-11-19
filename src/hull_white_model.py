import QuantLib as ql

def build_hull_white(curve, a, sigma_r):
    curve_handle = ql.YieldTermStructureHandle(curve)
    hw_model = ql.HullWhite(  # supplies state-dependent zero-coupon bond prices
        curve_handle,
        a,
        sigma_r,
    )
    hw_process = ql.HullWhiteProcess(  # describes short-rate evolution and will later support simulation
        curve_handle,
        a,
        sigma_r,
    )
    return hw_model, hw_process
