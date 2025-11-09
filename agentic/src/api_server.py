# api_server.py
import pandas as pd
import QuantLib as ql
from fastapi import FastAPI, UploadFile

from . import hqla_instruments as HQLA
from .portfolio import Portfolio

app = FastAPI()
portfolio = Portfolio()


@app.post("/upload_csv/")
async def upload_csv(file: UploadFile):
    df = pd.read_csv(file.file)
    today = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = today
    sofr_index = ql.Sofr()

    for _, row in df.iterrows():
        cls = getattr(HQLA, f"{row['level']}{row['type']}")
        issue = ql.DateParser.parseISO(row["issue_date"])
        maturity = ql.DateParser.parseISO(row["maturity_date"])
        inst = cls(
            issue,
            maturity,
            row["face_value"],
            quantity=row["quantity"],
            name=row["name"],
            isin=row["isin"],
        )
        if row["type"] == "Fixed":
            inst.build_bond(coupons=[float(row["coupon"])])
        elif row["type"] == "Floating":
            inst.build_bond(index=sofr_index)
        else:
            inst.build_bond()
        portfolio.add_instrument(inst)
    return {"status": "Portfolio created", "count": len(df)}
