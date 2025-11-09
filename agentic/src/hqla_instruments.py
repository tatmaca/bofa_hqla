from abc import ABC, abstractmethod

import QuantLib as ql


class HQLA_Asset(ABC):
    """
    Abstract base class for HQLA assets.
    Child classes should implement build_bond and price_from_curve.
    """

    def __init__(
        self,
        issue_date: ql.Date,
        maturity_date: ql.Date,
        face_value: float = 100,
        calendar: ql.Calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond),
        day_count: ql.DayCounter = ql.ActualActual(ql.ActualActual.ISMA),
    ):
        self.issue_date = issue_date
        self.maturity_date = maturity_date
        self.face_value = face_value
        self.calendar = calendar
        self.day_count = day_count

        # Placeholder for the QuantLib bond object
        self.bond = None

    @abstractmethod
    def build_bond(self, **kwargs):
        """
        Abstract method to construct the bond object in QuantLib.
        kwargs can include coupon rates, spreads, index objects, etc.
        """
        pass

    @abstractmethod
    def price_from_curve(self, discount_curve: ql.YieldTermStructureHandle):
        """
        Abstract method to price the bond using a given discount curve.
        Returns a float representing the present value.
        """
        pass


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
    ):
        super().__init__(
            issue_date,
            maturity_date,
            face_value,
            ql.UnitedStates(ql.UnitedStates.GovernmentBond),
            day_count,
        )
        self.coupon_frequency = coupon_frequency
        self.business_day_conv = business_day_conv

    def build_bond(
        self,
        index: ql.IborIndex,
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

    def price_from_curve(
        self, discount_curve: ql.YieldTermStructureHandle, clean: bool = False
    ):
        if self.bond is None:
            raise ValueError("Bond not built yet. Call build_bond first.")

        engine = ql.DiscountingBondEngine(discount_curve)
        self.bond.setPricingEngine(engine)
        return self.bond.cleanPrice() if clean else self.bond.dirtyPrice()


class Fixed(HQLA_Asset):
    """
    Fixed rate HQLA asset
    """

    def __init__(
        self,
        issue_date: ql.Date,
        maturity_date: ql.Date,
        face_value: float = 100,
        coupon_frequency: ql.Period = ql.Period(ql.Quarterly),
        day_count: ql.DayCounter = ql.ActualActual(ql.ActualActual.ISMA),
        business_day_conv: int = ql.Unadjusted,
        coupons: list[float] = [25 * 1e-6],
    ):
        super().__init__(
            issue_date,
            maturity_date,
            face_value,
            ql.UnitedStates(ql.UnitedStates.GovernmentBond),
            day_count,
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

    def price_from_curve(
        self, discount_curve: ql.YieldTermStructureHandle, clean: bool = False
    ):
        if self.bond is None:
            raise ValueError("Bond not built yet. Call build_bond first.")

        engine = ql.DiscountingBondEngine(discount_curve)
        self.bond.setPricingEngine(engine)
        return self.bond.cleanPrice() if clean else self.bond.dirtyPrice()


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
    ):
        super().__init__(
            issue_date,
            maturity_date,
            face_value,
            ql.UnitedStates(ql.UnitedStates.GovernmentBond),
            day_count,
        )
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

    def price_from_curve(
        self, discount_curve: ql.YieldTermStructureHandle, clean: bool = False
    ):
        if self.bond is None:
            raise ValueError("Bond not built yet. Call build_bond first.")

        engine = ql.DiscountingBondEngine(discount_curve)
        self.bond.setPricingEngine(engine)
        return self.bond.cleanPrice() if clean else self.bond.dirtyPrice()


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
