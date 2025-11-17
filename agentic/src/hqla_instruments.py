from abc import ABC, abstractmethod

import QuantLib as ql


class HQLA_Asset(ABC):
    """
    Abstract base class for HQLA assets.
    Child classes should implement build_bond and price_from_curve.
    """

    RECOVERY_BY_RATING = {
        "AAA": 0.741,
        "AA": 0.621,
        "A": 0.457,
        "BBB": 0.381,
    }

    def __init__(
        self,
        issue_date: ql.Date,
        maturity_date: ql.Date,
        face_value: float = 100,
        calendar: ql.Calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond),
        day_count: ql.DayCounter = ql.ActualActual(ql.ActualActual.ISMA),
        quantity: float = 0,
        name: str = "No Name Assigned",
        isin: str = "No ISIN Provided",
        isRisky: bool = False,
        grade: str = None,
    ):
        self.issue_date = issue_date
        self.maturity_date = maturity_date
        self.face_value = face_value
        self.calendar = calendar
        self.day_count = day_count
        self.dirty_price = None
        self.clean_price = None
        self.ytm = None
        self.dv01 = None
        self.cs01 = None
        self.duration = None
        self.convexity = None
        self.gamma = None
        self.quantity = quantity
        self.name = name
        self.isin = isin
        self.isRisky = isRisky
        self.grade = grade

        # Placeholder for the QuantLib bond object
        self.bond = None

    @abstractmethod
    def build_bond(self, **kwargs):
        """
        Abstract method to construct the bond object in QuantLib.
        kwargs can include coupon rates, spreads, index objects, etc.
        """
        pass

    def price_from_curve(
        self,
        discount_curve: ql.YieldTermStructureHandle,
        survival_curve: ql.YieldTermStructureHandle = None,
        clean: bool = False,
    ):
        if self.bond is None:
            raise ValueError("Bond not built yet. Call build_bond first.")

        if self.isRisky:
            rr = self.RECOVERY_BY_RATING[self.grade]
            engine = ql.RiskyBondEngine(survival_curve, rr, discount_curve)
        else:
            engine = ql.DiscountingBondEngine(discount_curve)
        self.bond.setPricingEngine(engine)
        self.clean_price = self.bond.cleanPrice()
        self.dirty_price = self.bond.dirtyPrice()
        self.ytm = (
            self.bond.bondYield(
                self.clean_price,
                ql.Thirty360(ql.Thirty360.USA),
                ql.Compounded,
                ql.Semiannual,
            )
            * 100
        )
        return self.bond.cleanPrice() if clean else self.bond.dirtyPrice()

    def bond_greeks(
        self,
        discount_curve: ql.YieldTermStructureHandle,
        up_curve: ql.YieldTermStructureHandle,
        down_curve: ql.YieldTermStructureHandle,
        survival_curve: ql.YieldTermStructureHandle = None,
        survival_curve_up: ql.YieldTermStructureHandle = None,
        survival_curve_down: ql.YieldTermStructureHandle = None,
    ):
        if self.isRisky:
            rr = self.RECOVERY_BY_RATING[self.grade]
            # first, get cs01
            og_engine = ql.RiskyBondEngine(survival_curve, rr, discount_curve)
            up_engine = ql.RiskyBondEngine(survival_curve_up, rr, discount_curve)
            down_engine = ql.RiskyBondEngine(survival_curve_down, rr, discount_curve)

            self.bond.setPricingEngine(up_engine)
            up_price = self.bond.dirtyPrice()
            self.bond.setPricingEngine(down_engine)
            down_price = self.bond.dirtyPrice()

            cs01 = (down_price - up_price) / 2
            self.cs01 = cs01

            # then, set up dv01 calc
            up_engine = ql.RiskyBondEngine(survival_curve, rr, up_curve)
            down_engine = ql.RiskyBondEngine(survival_curve, rr, down_curve)
        else:
            og_engine = ql.DiscountingBondEngine(discount_curve)
            up_engine = ql.DiscountingBondEngine(up_curve)
            down_engine = ql.DiscountingBondEngine(down_curve)

        self.bond.setPricingEngine(up_engine)
        up_price = self.bond.dirtyPrice()
        self.bond.setPricingEngine(down_engine)
        down_price = self.bond.dirtyPrice()
        self.bond.setPricingEngine(og_engine)
        base_price = self.dirty_price

        try:
            dv01 = (down_price - up_price) / 2
            duration = (dv01 / base_price) * 1e4
            gamma_1bp = down_price - 2 * base_price + up_price
            convexity = gamma_1bp * 1e8 / base_price
        except:
            print(f"{ self.name } has issues")
            return -1

        self.dv01 = dv01
        self.duration = duration
        self.gamma = gamma_1bp
        self.convexity = convexity


class Floating(HQLA_Asset):
    """
    Floating rate HQLA asset
    """

    def __init__(
        self,
        issue_date: ql.Date,
        maturity_date: ql.Date,
        face_value: float = 100,
        coupon_frequency: ql.Period = ql.Period(ql.Quarterly),
        day_count: ql.DayCounter = ql.Actual360(),
        business_day_conv: int = ql.Unadjusted,
        quantity: float = 0,
        name: str = "No Name Assigned",
        isin: str = "No ISIN Provided",
        isRisky: bool = False,
        grade: str = "AAA",
    ):
        super().__init__(
            issue_date,
            maturity_date,
            face_value,
            ql.UnitedStates(ql.UnitedStates.GovernmentBond),
            day_count,
            quantity,
            name,
            isin,
            isRisky,
            grade,
        )
        self.coupon_frequency = coupon_frequency
        self.business_day_conv = business_day_conv

    def build_bond(
        self,
        index: ql.Index,
        spread: list[float] = [25 * 1e-6],
        settlement_days: int = 1,
    ):
        self.schedule = ql.Schedule(
            self.issue_date,
            self.maturity_date,
            ql.Period(ql.Quarterly),
            self.calendar,
            self.business_day_conv,
            self.business_day_conv,
            ql.DateGeneration.Backward,
            True,
        )
        self.bond = ql.FloatingRateBond(
            settlementDays=settlement_days,
            faceAmount=self.face_value,
            schedule=self.schedule,
            index=index,
            paymentDayCounter=self.day_count,
            paymentConvention=self.business_day_conv,
            spreads=spread,
            issueDate=self.issue_date,
        )
        return self.bond


class Fixed(HQLA_Asset):
    """
    Fixed rate HQLA asset
    """

    def __init__(
        self,
        issue_date: ql.Date,
        maturity_date: ql.Date,
        face_value: float = 100,
        coupon_frequency: ql.Period = ql.Period(ql.Semiannual),
        day_count: ql.DayCounter = ql.ActualActual(ql.ActualActual.ISMA),
        business_day_conv: int = ql.Unadjusted,
        coupons: list[float] = [25 * 1e-6],
        quantity: float = 0,
        name: str = "No Name Assigned",
        isin: str = "No ISIN Provided",
        isRisky: bool = False,
        grade: str = "AAA",
    ):
        super().__init__(
            issue_date,
            maturity_date,
            face_value,
            ql.UnitedStates(ql.UnitedStates.GovernmentBond),
            day_count,
            quantity,
            name,
            isin,
            isRisky,
            grade,
        )
        self.coupon_frequency = coupon_frequency
        self.business_day_conv = business_day_conv
        self.coupons = coupons

    def build_bond(
        self,
        settlement_days: int = 1,
    ):
        self.schedule = ql.Schedule(
            self.issue_date,
            self.maturity_date,
            ql.Period(ql.Semiannual),
            self.calendar,
            self.business_day_conv,
            self.business_day_conv,
            ql.DateGeneration.Backward,
            True,
        )
        self.bond = ql.FixedRateBond(
            settlementDays=settlement_days,
            faceAmount=self.face_value,
            schedule=self.schedule,
            coupons=self.coupons,
            paymentDayCounter=self.day_count,
            paymentConvention=self.business_day_conv,
        )
        return self.bond


class Zero(HQLA_Asset):
    """
    Zero coupon instrument
    """

    def __init__(
        self,
        issue_date: ql.Date,
        maturity_date: ql.Date,
        face_value: float = 100,
        day_count: ql.DayCounter = ql.ActualActual(ql.ActualActual.ISMA),
        business_day_conv: int = ql.Unadjusted,
        quantity: float = 0,
        name: str = "No Name Assigned",
        isin: str = "No ISIN Provided",
        isRisky: bool = False,
        grade: str = "AAA",
    ):
        super().__init__(
            issue_date,
            maturity_date,
            face_value,
            ql.UnitedStates(ql.UnitedStates.GovernmentBond),
            day_count,
            quantity,
            name,
            isin,
            isRisky,
            grade,
        )
        self.coupon = 0.0
        self.business_day_conv = business_day_conv

    def build_bond(
        self,
        settlement_days: int = 1,
    ):
        self.bond = ql.ZeroCouponBond(
            settlementDays=settlement_days,
            faceAmount=self.face_value,
            calendar=self.calendar,
            maturityDate=self.maturity_date,
            paymentConvention=self.business_day_conv,
        )
        return self.bond


# Levels
class Level1:
    haircut = 0.0
    max_lcr_weight = 1.0


class Level2A:
    haircut = 0.15
    max_lcr_weight = 0.40


class Level2B:
    haircut = 0.25
    max_lcr_weight = 0.15


class Level1Fixed(Level1, Fixed):
    pass  # inherit from Level1 and FixedRateInstrument


class Level1Floating(Level1, Floating):
    pass  # inherit from Level1 and FixedRateInstrument


class Level1Discount(Level1, Zero):
    pass  # inherit from Level1 and FixedRateInstrument


class Level2AFixed(Level2A, Fixed):
    pass  # inherit from Level2A and FloatingRateInstrument


class Level2AFloating(Level2A, Floating):
    pass  # inherit from Level2A and FloatingRateInstrument


class Level2ADiscount(Level2A, Zero):
    pass  # inherit from Level2A and FloatingRateInstrument


class Level2BFixed(Level2B, Fixed):
    pass  # inherit from Level2B and DiscountInstrument


class Level2BFloating(Level2B, Floating):
    pass  # inherit from Level2B and DiscountInstrument


class Level2BDiscount(Level2B, Zero):
    pass  # inherit from Level2B and DiscountInstrument
