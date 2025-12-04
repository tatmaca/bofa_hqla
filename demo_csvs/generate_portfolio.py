import random
from datetime import datetime, timedelta

import pandas as pd

# Settings
num_instruments = 1000
today = datetime.today()

# Level mapping and attributes
levels = {
    "1": {
        "type": ["Fixed", "Floating"],
        "ratings": [""],
        "coupon_range": (0.0, 0.05),
    },  # T-bills, gov
    "2A": {"type": ["Fixed"], "ratings": ["AAA", "AA"], "coupon_range": (0.02, 0.08)},
    "2B": {
        "type": ["Fixed", "Floating"],
        "ratings": ["A", "BBB"],
        "coupon_range": (0.03, 0.09),
    },
}


# Helper functions
def random_isin():
    prefix = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    digits = "".join(random.choices("0123456789", k=9))
    return prefix + digits


def random_name(level):
    prefix_map = {
        "1": ["GOV", "TBILL", "SOFR"],
        "2A": ["Corp", "GovBond"],
        "2B": ["Corp", "Emerging", "Foreign"],
    }
    return f"{random.choice(prefix_map[level])}-{random.randint(1,10000)}"


def random_maturity(issue_date, min_years=1, max_years=30):
    years = random.randint(min_years, max_years)
    return issue_date + timedelta(days=365 * years)


# Build portfolio
portfolio = []

for _ in range(num_instruments):
    level = random.choices(["1", "2A", "2B"], weights=[0.2, 0.4, 0.4])[0]
    attr = levels[level]

    bond_type = random.choice(attr["type"])
    rating = random.choice(attr["ratings"])
    coupon = (
        round(random.uniform(*attr["coupon_range"]), 4) if bond_type == "Fixed" else ""
    )
    issue_date = today - timedelta(days=random.randint(0, 365 * 5))
    maturity_date = random_maturity(issue_date, 1, 30)

    # Skip expired instruments
    if maturity_date <= today:
        continue

    face_value = random.choice([100, 500, 1000])
    quantity = random.randint(1, 50)

    name = random_name(level)
    isin = random_isin()

    portfolio.append(
        {
            "level": level,
            "type": bond_type,
            "name": name,
            "isin": isin,
            "issue_date": issue_date.strftime("%Y-%m-%d"),
            "maturity_date": maturity_date.strftime("%Y-%m-%d"),
            "face_value": face_value,
            "quantity": quantity,
            "coupon": coupon,
            "rating": rating,
        }
    )

# Convert to DataFrame and save
df = pd.DataFrame(portfolio)
df.to_csv("simulated_portfolio_2.csv", index=False)
print("Portfolio CSV generated:", len(df), "rows")
