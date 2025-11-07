import QuantLib as ql
from abc import ABC, abstractmethod

"""
HQLAInstrument (abstract base)
│
├── FixedRateInstrument
├── FloatingRateInstrument
└── DiscountInstrument
"""

class HQLAInstrument(ABC):

    def __init__(self, name, face_value, issue_date, maturity_date,
                 calendar, day_count, business_day_convention, settlement_days=1):
        self.name = name
        self.face_value = face_value
        self.issue_date = issue_date
        self.maturity_date = maturity_date
        self.calendar = calendar
        self.day_count = day_count
        self.business_day_convention = business_day_convention
        self.settlement_days = settlement_days
        self.bond = None
        self.haircut = None
        self.lcr_weight = None

        @abstractmethod
        def build_bond(self):
            """Build the bond object using QuantLib"""
            pass

        def price_from_curve(self, yield_curve):
            """Price (clean) the bond using a QuantLib yield curve"""

            if self.bond is None:
                self.build_bond()

            engine = ql.DiscountingBondEngine(ql.YieldTermStructureHandle(yield_curve))
            self.bond.setPricingEngine(engine)
            self.price = self.bond.cleanPrice()
            return self.price



# Fixed Rate Instruments

class FixedRateInstrument(HQLAInstrument):
    def __init__(self, coupon_rate, frequency=ql.Semiannual, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.coupon_rate = coupon_rate
        self.frequency = frequency

    def build_bond(self):
        schedule = ql.Schedule(
            self.issue_date,
            self.maturity_date,
            ql.Period(self.frequency),
            self.calendar,
            self.business_day_convention,
            self.business_day_convention,
            ql.DateGeneration.Backward, # rule for generating dates
            False # end of month
        )
        self.bond = ql.FixedRateBond(
            self.settlement_days,
            self.face_value,
            schedule,
            [self.coupon_rate],
            self.day_count,
            self.business_day_convention
        )

# Floating Rate Instruments
class FloatingRateInstrument(HQLAInstrument):
    def __init__(self, index, spread=0.0, frequency=ql.Quarterly, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        self.spread = spread
        self.frequency = frequency

    def build_bond(self):
        schedule = ql.Schedule(
            self.issue_date,
            self.maturity_date,
            ql.Period(self.frequency),
            self.calendar,
            ql.Following, 
            ql.Following,
            ql.DateGeneration.Backward, # rule for generating dates
            False # end of month
        )
        self.bond = ql.FloatingRateBond(
            self.settlement_days,
            self.face_value,
            schedule,
            self.index,
            self.day_count,
            ql.Following,
            2,  # fixing days
            [1.0],  # gearing
            [self.spread],
            [],
            [],
            [],
            True,
            self.face_value
        )

# Discount Instruments
class DiscountInstrument(HQLAInstrument):
    def build_bond(self):
        self.bond = ql.ZeroCouponBond(
            self.settlement_days,
            self.calendar,
            self.face_value,
            self.maturity_date,
            self.business_day_convention,
            self.face_value,
            self.issue_date
        )

# Levels
class Level1:
    haircut = 0.0
    lcr_weight = 1.0

class Level2A:
    haircut = 0.15
    lcr_weight = 0.85

class Level2B:
    haircut = 0.25
    lcr_weight = 0.75

# Examples of Level1, Level2A, and Level2B instruments to use in portfolio 

class Level1Fixed(Level1, FixedRateInstrument): 
    pass # inherit from Level1 and FixedRateInstrument

class Level2AFloating(Level2A, FloatingRateInstrument): 
    pass # inherit from Level2A and FloatingRateInstrument

class Level2BDiscount(Level2B, DiscountInstrument): 
    pass # inherit from Level2B and DiscountInstrument

