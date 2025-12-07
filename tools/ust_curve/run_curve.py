#!/usr/bin/env python3
import sys, os, math, json, argparse, datetime as dt, requests, csv
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# Force a non-interactive backend so it always saves a PNG even on servers/CLI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -------------------- Dynamic import of your core --------------------
def import_core(module_name):
    try:
        m = __import__(module_name, fromlist=["Curve", "SolvedCurve", "Swap", "Dual"])
    except Exception as e:
        print(f"[ERROR] Could not import module '{module_name}'. Make sure the file {module_name}.py is in this folder.")
        print(f"        Import error: {e}")
        sys.exit(1)
    for attr in ("Curve", "SolvedCurve", "Swap", "Dual"):
        if not hasattr(m, attr):
            print(f"[ERROR] Module '{module_name}' is missing '{attr}'.")
            sys.exit(1)
    return m.Curve, m.SolvedCurve, m.Swap, m.Dual

# -------------------- Treasury data fetch --------------------
XML_BASE = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
XML_DATA_KEY = "daily_treasury_yield_curve"
CSV_ARCHIVE_BASE = "https://home.treasury.gov/system/files/276"
CSV_ARCHIVE_FILES = {
    "1990-2024": "yield-curve-rates-1990-2024.csv",
    "2011-2020": "yield-curve-rates-2011-2020.csv",
    "2001-2010": "yield-curve-rates-2001-2010.csv",
    "1990-2000": "yield-curve-rates-1990-2000.csv",
}

def _find_between(s, a, b):
    out, i = [], 0
    while True:
        p = s.find(a, i)
        if p < 0: break
        q = s.find(b, p+len(a))
        if q < 0: break
        out.append(s[p+len(a):q])
        i = q + len(b)
    return out

def fetch_par_from_xml(as_of):
    yyyymm = as_of.strftime("%Y%m")
    r = requests.get(XML_BASE, params={"data": XML_DATA_KEY, "field_tdr_date_value_month": yyyymm}, timeout=20)
    r.raise_for_status()
    text = r.text
    entries = _find_between(text, "<entry>", "</entry>")
    target_alt  = as_of.strftime("%B %d, %Y").replace(" 0", " ")
    target_long = as_of.strftime("%B %-d, %Y") if sys.platform != "win32" else target_alt
    for entry in entries:
        title = _find_between(entry, "<title>", "</title>")
        title = title[0] if title else ""
        if target_long in title or target_alt in title:
            rows = _find_between(entry, "<tr>", "</tr>")
            raw = {}
            for row in rows:
                cols = _find_between(row, "<td>", "</td>")
                if len(cols) >= 2:
                    k = cols[0].strip().lower().replace(" ", "")
                    v = cols[1].strip()
                    if v and v.upper() != "N/A":
                        try: raw[k] = float(v)
                        except: pass
            out = {}
            def g(key): return raw.get(key)
            mapping = {
                "0.25": g("3mo") or g("6mo"),  # 3 months (prefer 3mo, fallback to 6mo)
                "1": g("1yr"),
                "2": g("2yr"),
                "3": g("3yr"),
                "5": g("5yr"),
                "7": g("7yr"),
                "10": g("10yr"),
                "20": g("20yr"),
                "30": g("30yr"),
            }
            for k, v in mapping.items():
                if isinstance(v, float): out[k] = v
            return out or None
    return None

def _csv_url_for_year(y):
    if 1990 <= y <= 2024: return f"{CSV_ARCHIVE_BASE}/{CSV_ARCHIVE_FILES['1990-2024']}"
    if 2011 <= y <= 2020: return f"{CSV_ARCHIVE_BASE}/{CSV_ARCHIVE_FILES['2011-2020']}"
    if 2001 <= y <= 2010: return f"{CSV_ARCHIVE_BASE}/{CSV_ARCHIVE_FILES['2001-2010']}"
    if 1990 <= y <= 2000: return f"{CSV_ARCHIVE_BASE}/{CSV_ARCHIVE_FILES['1990-2000']}"
    return None

def fetch_par_from_csv_archive(as_of):
    url = _csv_url_for_year(as_of.year)
    if not url: return None
    r = requests.get(url, timeout=30); r.raise_for_status()
    lines = r.text.splitlines()
    import io
    rdr = csv.DictReader(io.StringIO("\n".join(lines)))
    target = as_of.strftime("%m/%d/%Y")
    alt    = as_of.strftime("%-m/%-d/%Y") if sys.platform != "win32" else target
    for rec in rdr:
        if rec.get("Date") in (target, alt):
            def f(col):
                v = rec.get(col, "").strip()
                if v in ("", "N/A"): return None
                try: return float(v)
                except: return None
            out = {
                "0.25": f("3 Mo") or f("6 Mo"),  # 3 months (prefer 3 Mo, fallback to 6 Mo)
                "1": f("1 Yr"),
                "2": f("2 Yr"),
                "3": f("3 Yr"),
                "5": f("5 Yr"),
                "7": f("7 Yr"),
                "10": f("10 Yr"),
                "20": f("20 Yr"),
                "30": f("30 Yr"),
            }
            return {k:v for k,v in out.items() if isinstance(v, float)}
    return None

YEARLY_CSV_TMPL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?_format=csv&type=daily_treasury_yield_curve&field_tdr_date_value={year}"

def fetch_par_from_year_csv(as_of):
    import io, csv, requests
    url = YEARLY_CSV_TMPL.format(year=as_of.year)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    rdr = csv.DictReader(io.StringIO(r.text))
    target = as_of.strftime("%m/%d/%Y")
    alt    = as_of.strftime("%-m/%-d/%Y") if sys.platform != "win32" else target
    for rec in rdr:
        if rec.get("Date") not in (target, alt):
            continue
        def f(col):
            v = (rec.get(col) or "").strip()
            if not v or v.upper() == "N/A":
                return None
            try:
                return float(v)
            except:
                return None
        out = {
            "0.25": f("3 Mo") or f("6 Mo"),  # 3 months (prefer 3 Mo, fallback to 6 Mo)
            "1":    f("1 Yr"),
            "2":    f("2 Yr"),
            "3":    f("3 Yr"),
            "5":    f("5 Yr"),
            "7":    f("7 Yr"),
            "10":   f("10 Yr"),
            "20":   f("20 Yr"),
            "30":   f("30 Yr"),
        }
        # keep only valid floats
        return {k: v for k, v in out.items() if isinstance(v, float)}
    return None


def try_fetch_par_for_date(d):
    par = None
    # 1) New per-year CSV (works for current year pages like 2025)
    try:
        par = fetch_par_from_year_csv(d)
    except Exception:
        par = None
    # 2) Legacy monthly XML (kept as a fallback)
    if not par:
        try:
            par = fetch_par_from_xml(d)
        except Exception:
            par = None
    # 3) Old archive CSVs (1990–2024)
    if not par:
        try:
            par = fetch_par_from_csv_archive(d)
        except Exception:
            par = None
    return par


def fetch_with_lookback(as_of, lookback_days=10):
    d = as_of
    for _ in range(lookback_days+1):
        par = try_fetch_par_for_date(d)
        if par and len(par) >= 3: return d, par
        d = d - dt.timedelta(days=1)
    return None, None

# -------------------- mapping & solve --------------------
def par_map_to_months(par):
    mapping = {"0.25":6, "1":12, "2":24, "3":36, "5":60, "7":84, "10":120, "20":240, "30":360}
    items = [(mapping[k], v) for k,v in par.items() if k in mapping]
    items.sort(key=lambda x: x[0])
    return items

def add_months(d, m):
    y = d.year + (d.month - 1 + m)//12
    m2 = (d.month - 1 + m) % 12 + 1
    day = min(d.day, [31, 29 if (y%4==0 and (y%100!=0 or y%400==0)) else 28,31,30,31,30,31,31,30,31,30,31][m2-1])
    return dt.datetime(y, m2, day)

def make_dual(Dual_cls, name: str, value: float):
    # Your Dual ctor is Dual(real_value, dual_dict)
    # e.g., Dual(0.95, {'v1': 1.0})
    try:
        return Dual_cls(value, {name: 1.0})
    except TypeError:
        return Dual_cls(real=value, dual={name: 1.0})


def build_initial_nodes(Dual_cls, as_of_dt, months_list, flat_guess=0.04):
    pillar_dates = [add_months(as_of_dt, m) for m in months_list]
    nodes = {pillar_dates[0]: 1.0}
    for i, d in enumerate(pillar_dates[1:], start=1):
        guess = math.exp(-flat_guess * (months_list[i] / 12.0))
        nodes[d] = make_dual(Dual_cls, f"v{i}", guess)
    return nodes, pillar_dates




def build_swaps(Swap_cls, as_of_dt, quotes_months, fixed_leg_m, float_leg_m):
    swaps, obj_rates = [], []
    for m, rate_percent in quotes_months:
        swaps.append(Swap_cls(start=as_of_dt, tenor=m, period_fix=fixed_leg_m, period_float=float_leg_m,
                              days=False, fixed_rate=None, notional=1_000_000))
        obj_rates.append(rate_percent)
    return swaps, obj_rates


def solve_curve(SolvedCurve_cls, Dual_cls, Swap_cls, as_of_dt, quotes_months, fixed_leg_m, float_leg_m,
                interpolation, algorithm, flat_guess, months_for_nodes=None, verbose=True):
    if months_for_nodes is None:
        months_for_nodes = [0] + [m for m,_ in quotes_months]
    nodes, pillar_dates = build_initial_nodes(Dual_cls, as_of_dt, months_for_nodes, flat_guess)
    swaps, obj_rates = build_swaps(Swap_cls, as_of_dt, quotes_months, fixed_leg_m, float_leg_m)

    curve = SolvedCurve_cls(nodes=nodes, interpolation=interpolation, swaps=swaps,
                            obj_rates=obj_rates, algorithm=algorithm, w=None)
    if verbose:
        print(f"[INFO] Solving curve with {len(obj_rates)} quotes…")
    msg = curve.iterate(max_i=300, tol=1e-12)
    if verbose:
        print(f"[INFO] Solver: {msg}")

    pillars = []
    first_date = list(curve.nodes.keys())[0]
    for d, v in curve.nodes.items():
        if d == first_date:
            continue
        DF = v.real if hasattr(v, "real") else float(v)
        tyears = (d - as_of_dt).days / 365.25
        z = 0.0 if tyears <= 0 else -math.log(max(1e-12, DF))/tyears
        pillars.append((tyears, DF, z))
    pillars.sort(key=lambda x: x[0])
    return curve, pillars


# -------------------- plot + save --------------------
def plot_curve_with_risks(pillars, as_of_dt, out_png):
    tenors = [t for t,_,_ in pillars]
    zeros  = [z*100.0 for _,_,z in pillars]   # %
    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(tenors, zeros, marker='o')
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Zero Rate (%)")
    ax.set_title(f"Zero Curve (swap-style fit to Treasury par) — {as_of_dt.date()}")
    ax.grid(True, alpha=0.4)

    def get_at(year):
        if year <= tenors[0]: return zeros[0]
        if year >= tenors[-1]: return zeros[-1]
        for (t0,z0),(t1,z1) in zip(zip(tenors, zeros), zip(tenors[1:], zeros[1:])):
            if t0 <= year <= t1:
                w = (year - t0)/(t1 - t0)
                return (1-w)*z0 + w*z1
        return zeros[-1]

    z2, z5, z10, z30 = get_at(2.0), get_at(5.0), get_at(10.0), get_at(30.0)
    inv_2s10 = (z10 - z2)
    steep_2s30 = (z30 - z2)
    belly_hump = (2*z5 - (z2 + z10))

    if inv_2s10 < 0:
        ax.axvspan(2, 10, alpha=0.12, label="2s10s inversion risk")
    if steep_2s30 < 0.25:
        ax.axvspan(10, 30, alpha=0.10, label="Flat long-end risk")
    if belly_hump > 0.30:
        ax.axvspan(3, 7, alpha=0.10, label="Belly hump risk")

    ax.annotate(f"2s10s: {inv_2s10:.2f}%", xy=(10, z10), xytext=(10, z10+0.4),
                arrowprops=dict(arrowstyle="->", lw=0.8), fontsize=9)
    ax.annotate(f"2s30s: {steep_2s30:.2f}%", xy=(27, z30), xytext=(24, z30+0.6),
                arrowprops=dict(arrowstyle="->", lw=0.8), fontsize=9)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_png, dpi=300)
    print(f"[OK] Saved plot: {out_png}")

def save_outputs(pillars, as_of_dt, out_prefix):
    csv_path = f"{out_prefix}_{as_of_dt.isoformat()}.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["as_of","tenor_years","DF","zero_cc_annual"])
        for t, DF, z in pillars:
            w.writerow([as_of_dt.isoformat(), f"{t:.6f}", f"{DF:.8f}", f"{z:.8f}"])
    print(f"[OK] Wrote {csv_path}")

    json_path = f"{out_prefix}_{as_of_dt.isoformat()}.json"
    with open(json_path, "w") as f:
        json.dump({"as_of": as_of_dt.isoformat(),
                   "pillars": [{"tenor_years": t, "DF": DF, "zero_cc_annual": z} for t,DF,z in pillars]}, f, indent=2)
    print(f"[OK] Wrote {json_path}")

# -------------------- CLI --------------------
def main():
    ap = argparse.ArgumentParser(description="Fetch Treasury par yields, solve with your core, and plot risks.")
    ap.add_argument("--core-module", required=True, help="Python module name with Curve/SolvedCurve/Swap/Dual (e.g., curve)")
    ap.add_argument("date", nargs="?", help="YYYY-MM-DD (defaults to today)")
    ap.add_argument("--float", dest="float_leg_m", type=int, default=3, help="Float reset months (3=IRS, 1=OIS)")
    ap.add_argument("--fix", dest="fixed_leg_m", type=int, default=6, help="Fixed pay freq months (6=semiannual)")
    ap.add_argument("--lookback", type=int, default=10, help="Max lookback days when no posting")
    ap.add_argument("--flat-guess", type=float, default=0.04, help="Seed flat zero for DF guesses (e.g., 0.04=4%)")
    args = ap.parse_args()

    as_of = dt.date.today() if not args.date else dt.datetime.strptime(args.date, "%Y-%m-%d").date()
    Curve, SolvedCurve, Swap, Dual = import_core(args.core_module)

    print(f"[INFO] Requested date: {as_of}  |  core: {args.core_module}")
    eff_date, par = fetch_with_lookback(as_of, lookback_days=args.lookback)
    if not par:
        print(f"[ERROR] No Treasury par data on or before {as_of} (looked back {args.lookback} days).")
        sys.exit(1)
    if eff_date != as_of:
        print(f"[WARN] No posting for {as_of}; using previous available date: {eff_date}.")

    quotes_months = par_map_to_months(par)
    print(f"[INFO] Tenors fetched: {quotes_months}")

    as_of_dt = dt.datetime(eff_date.year, eff_date.month, eff_date.day)
    #global Swap  # needed inside solve_curve call above
    curve, pillars = solve_curve(SolvedCurve, Dual, Swap, as_of_dt, quotes_months,
                             fixed_leg_m=args.fixed_leg_m, float_leg_m=args.float_leg_m,
                             interpolation="log_linear", algorithm="gauss_newton",
                             flat_guess=args.flat_guess, months_for_nodes=None, verbose=True)


    out_prefix = "ust_zero_curve"
    save_outputs(pillars, as_of_dt, out_prefix)
    plot_curve_with_risks(pillars, as_of_dt, f"{out_prefix}_{as_of_dt.isoformat()}.png")

    print("[DONE] All artifacts written.")

if __name__ == "__main__":
    main()
