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
    Floating rate HQLA asset with daily pricing capability.
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

    def daily_price(self, dates, discount_curves, fixings_dict=None, clean=True):
        """
        Compute daily MTM prices for a floating rate bond.

        Parameters:
        -----------
        dates : list of ql.Date
            Dates for which to calculate prices.
        discount_curves : list of ql.YieldTermStructureHandle
            Discount/forward curves corresponding to each date.
        fixings_dict : dict (optional)
            Dictionary with {ql.Date: fixing} to update the index for past rates.
        clean : bool
            If True, return clean price; otherwise return dirty price.

        Returns:
        --------
        dict : {ql.Date: price}
        """
        if self.bond is None:
            raise ValueError("Bond not built yet. Call build_bond first.")
        if len(dates) != len(discount_curves):
            raise ValueError("dates and discount_curves must have the same length.")

        prices = {}
        index = self.bond.index()  # Retrieve the bond's index

        for d, curve in zip(dates, discount_curves):
            # 1. Update evaluation date
            ql.Settings.instance().evaluationDate = d

            # 2. Apply new fixings if provided
            if fixings_dict:
                for fix_date, fix_value in fixings_dict.items():
                    if fix_date <= d:  # Only update past or current fixings
                        index.addFixing(fix_date, fix_value)

            # 3. Update discount curve
            engine = ql.DiscountingBondEngine(curve)
            self.bond.setPricingEngine(engine)

            # 4. Price
            prices[d] = self.bond.cleanPrice() if clean else self.bond.dirtyPrice()

        return prices
