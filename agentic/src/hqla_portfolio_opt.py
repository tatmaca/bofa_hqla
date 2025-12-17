"""
hqla_portfolio_opt.py
-------------
Optimizes a portfolio of HQLA instruments (Fixed, Floating, Discount)
across Basel III liquidity levels by maxmizing expect returns given bounds.

Author: Aryaa Gunavante (agunavante)
Updated: 2025-12-01
"""


from typing import Dict, Optional, Tuple

import hqla_portfolio as HQLA
import hqla_scenarios as SCENARIO
import numpy as np
import pandas as pd
import QuantLib as ql
from scipy import linalg
from scipy.optimize import minimize


class HQLA_Portfolio_Opt_Enhanced:
    """
    Enhanced HQLA portfolio optimizer with:
    - Proper LCR calculation
    - Duration constraints
    - Improved covariance estimation
    - Concentration limits
    """

    def __init__(
        self,
        portfolio: HQLA.Portfolio,
        net_cash_outflow: float,
        min_lcr: float = 1.0,
        max_lcr: float = 1.5,
        target_duration: Optional[float] = None,
        duration_tolerance: float = 0.5,
        allocation_buffer: float = 0.02,
    ):
        self.portfolio = portfolio
        self.assets = portfolio.assets
        self.net_cash_outflow = net_cash_outflow
        self.min_lcr = min_lcr
        self.max_lcr = max_lcr
        self.target_duration = target_duration
        self.duration_tolerance = duration_tolerance
        self.allocation_buffer = allocation_buffer

        # Build enhanced summary table
        self._build_assets_summary()

    def _build_assets_summary(self):
        """Build comprehensive asset summary with all required metrics"""
        rows = []

        for level, group in self.assets.items():
            for inst in group:
                if inst.bond is None:
                    raise ValueError(
                        f"Instrument {inst.name} has no QuantLib bond built yet."
                    )

                # Get prices
                clean_price_float = inst.clean_price or inst.bond.cleanPrice()
                dirty_price_float = inst.dirty_price or inst.bond.dirtyPrice()
                clean_price = ql.BondPrice(clean_price_float, ql.BondPrice.Clean)

                # Compute YTM
                try:
                    ytm = inst.bond.bondYield(
                        clean_price, inst.day_count, ql.Compounded, ql.Semiannual
                    )
                except:
                    ytm = 0.0  # Fallback for zero-coupon or short bonds

                # Compute modified duration
                try:
                    # QuantLib's duration is Macaulay duration
                    settlement = ql.Settings.instance().evaluationDate
                    mac_duration = ql.BondFunctions.duration(
                        inst.bond,
                        ytm,
                        inst.day_count,
                        ql.Compounded,
                        ql.Semiannual,
                        ql.Duration.Macaulay,
                        settlement,
                    )
                    # Modified duration = Macaulay / (1 + y/k) where k=2 for semiannual
                    mod_duration = mac_duration / (1 + ytm / 2)
                except:
                    mod_duration = 0.0

                # Time to maturity in years
                eval_date = ql.Settings.instance().evaluationDate
                ttm = (inst.maturity_date - eval_date) / 365.25

                rows.append(
                    {
                        "Name": inst.name,
                        "Level": level,
                        "Quantity": inst.quantity,
                        "CleanPrice": clean_price_float,
                        "DirtyPrice": dirty_price_float,
                        "Haircut": inst.haircut,
                        "LCR_Weight": inst.max_lcr_weight,
                        "YTM": ytm,
                        "ModDuration": mod_duration,
                        "TimeToMaturity": ttm,
                    }
                )

        self.assets_summary = pd.DataFrame(rows)
        self.n_assets = len(self.assets_summary)

    def _compute_hqla_value(self, weights: np.ndarray) -> float:
        """
        Compute Basel III HQLA value:
        HQLA = sum_i [Market_Value_i * (1 - Haircut_i)]

        Level 2A and 2B have additional caps:
        Adjusted_HQLA = min(Level2A_value, 0.4 * Total_HQLA) +
                        min(Level2B_value, 0.15 * Total_HQLA) +
                        Level1_value
        """
        df = self.assets_summary

        # Market values (assuming we're allocating net_cash_outflow total)
        market_values = weights * self.net_cash_outflow

        # Compute gross HQLA per level (after haircut)
        level1_hqla = np.sum(
            market_values[df["Level"] == "L1"]
            * (1 - df.loc[df["Level"] == "L1", "Haircut"].values)
        )
        level2a_hqla = np.sum(
            market_values[df["Level"] == "L2A"]
            * (1 - df.loc[df["Level"] == "L2A", "Haircut"].values)
        )
        level2b_hqla = np.sum(
            market_values[df["Level"] == "L2B"]
            * (1 - df.loc[df["Level"] == "L2B", "Haircut"].values)
        )

        total_gross_hqla = level1_hqla + level2a_hqla + level2b_hqla

        # Apply composition caps
        level2a_capped = min(level2a_hqla, 0.4 * total_gross_hqla)
        level2b_capped = min(level2b_hqla, 0.15 * total_gross_hqla)

        adjusted_hqla = level1_hqla + level2a_capped + level2b_capped

        return adjusted_hqla

    def _compute_portfolio_duration(self, weights: np.ndarray) -> float:
        """Compute portfolio modified duration"""
        df = self.assets_summary
        return np.dot(weights, df["ModDuration"].values)

    def ledoit_wolf_shrinkage(self, R: np.ndarray) -> np.ndarray:
        """
        Ledoit-Wolf shrinkage estimator for covariance matrix.
        More robust than sample covariance for limited scenarios.
        """
        S, N = R.shape

        # Sample covariance
        sample_cov = np.cov(R, rowvar=False, ddof=1)

        # Target: diagonal matrix (constant correlation model)
        trace = np.trace(sample_cov)
        target = (trace / N) * np.eye(N)

        # Compute shrinkage intensity (simplified Ledoit-Wolf)
        # Full LW formula is complex; this is a practical approximation

        # Compute Frobenius norm of sample - target
        diff = sample_cov - target
        phi = np.sum(diff**2)

        # Estimate pi (variance of sample covariance)
        # Simplified: use empirical variance
        pi = 0.0
        for s in range(S):
            dev = np.outer(R[s] - R.mean(axis=0), R[s] - R.mean(axis=0)) - sample_cov
            pi += np.sum(dev**2)
        pi /= S

        # Shrinkage intensity
        rho = min(1.0, pi / phi) if phi > 1e-10 else 0.0

        # Shrunk covariance
        shrunk_cov = rho * target + (1 - rho) * sample_cov

        # Ensure PSD
        eigvals, eigvecs = linalg.eigh(shrunk_cov)
        eigvals_clipped = np.maximum(eigvals, 1e-12)
        shrunk_cov_psd = (eigvecs * eigvals_clipped) @ eigvecs.T

        return shrunk_cov_psd

    def _build_base_constraints(self, levels, max_total_allocation=2.0):
        """Build common constraints used in all optimizations"""
        constraints = []

        # Total allocation upper bound (for numerical stability)
        constraints.append(
            {"type": "ineq", "fun": lambda w: max_total_allocation - np.sum(w)}
        )

        # Basel III composition: Level 1 at least 60% of allocated weights
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: (
                    np.sum(w[levels == "L1"]) - 0.6 * np.sum(w)
                    if np.sum(w) > 1e-6
                    else 0.0
                ),
            }
        )

        # Level 2B max 15% of allocated weights
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: (
                    0.15 * np.sum(w) - np.sum(w[levels == "L2B"])
                    if np.sum(w) > 1e-6
                    else 0.0
                ),
            }
        )

        # LCR constraints
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: self._compute_hqla_value(w) / self.net_cash_outflow
                - self.min_lcr,
            }
        )
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: self.max_lcr
                - self._compute_hqla_value(w) / self.net_cash_outflow,
            }
        )

        # Duration constraints (if specified)
        if self.target_duration is not None:
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: self._compute_portfolio_duration(w)
                    - (self.target_duration - self.duration_tolerance),
                }
            )
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: (self.target_duration + self.duration_tolerance)
                    - self._compute_portfolio_duration(w),
                }
            )

        return constraints

    def lexicographic_mean_optimize(
        self,
        max_position_size: float = 0.30,
        min_position_size: float = 0.0,
        max_total_allocation: float = 2.0,
        verbose: bool = True,
    ) -> Tuple[pd.DataFrame, object, float, float, float]:
        """
        TWO-STAGE LEXICOGRAPHIC OPTIMIZATION:

        Stage 1: Find MINIMUM total HQLA allocation that satisfies LCR
        Stage 2: MAXIMIZE returns while keeping allocation near minimum

        This reflects actual bank behavior: minimize capital in HQLA,
        then optimize returns within that constraint.
        """
        df = self.assets_summary
        mu = df["YTM"].values
        levels = df["Level"].values

        # ============= STAGE 1: MINIMIZE TOTAL ALLOCATION =============
        if verbose:
            print("\n" + "=" * 60)
            print("STAGE 1: Finding minimum HQLA allocation...")
            print("=" * 60)

        def stage1_objective(w):
            return np.sum(w)  # Minimize total allocation

        stage1_constraints = self._build_base_constraints(levels, max_total_allocation)
        bounds = [(min_position_size, max_position_size) for _ in range(self.n_assets)]

        # Initial guess: allocate to Level 1 (lowest haircut)
        x0 = np.zeros(self.n_assets)
        l1_mask = levels == "L1"
        n_l1 = np.sum(l1_mask)
        if n_l1 > 0:
            x0[l1_mask] = self.min_lcr / n_l1
        else:
            x0 = np.ones(self.n_assets) * self.min_lcr / self.n_assets

        stage1_result = minimize(
            stage1_objective,
            x0=x0,
            bounds=bounds,
            constraints=stage1_constraints,
            method="SLSQP",
            options={"disp": verbose, "maxiter": 1000, "ftol": 1e-9},
        )

        if not stage1_result.success:
            print(f"WARNING: Stage 1 did not converge: {stage1_result.message}")

        min_allocation = np.sum(stage1_result.x)
        min_lcr_achieved = (
            self._compute_hqla_value(stage1_result.x) / self.net_cash_outflow
        )

        if verbose:
            print(f"\nStage 1 Results:")
            print(
                f"  Minimum allocation: {min_allocation:.4f} × NCO = ${min_allocation * self.net_cash_outflow:,.2f}"
            )
            print(f"  LCR achieved: {min_lcr_achieved:.2%}")
            print(f"  Implied return: {np.dot(stage1_result.x, mu):.4%}")

        # ============= STAGE 2: MAXIMIZE RETURNS =============
        if verbose:
            print("\n" + "=" * 60)
            print("STAGE 2: Maximizing returns within allocation constraint...")
            print("=" * 60)

        # Allow small buffer above minimum for optimization flexibility
        max_allowed_allocation = min_allocation * (1 + self.allocation_buffer)

        def stage2_objective(w):
            return -np.dot(w, mu)  # Maximize returns

        # Add constraint: total allocation ≤ min_allocation * (1 + buffer)
        stage2_constraints = self._build_base_constraints(levels, max_total_allocation)
        stage2_constraints.append(
            {"type": "ineq", "fun": lambda w: max_allowed_allocation - np.sum(w)}
        )

        # Start from Stage 1 solution
        x0_stage2 = stage1_result.x

        stage2_result = minimize(
            stage2_objective,
            x0=x0_stage2,
            bounds=bounds,
            constraints=stage2_constraints,
            method="SLSQP",
            options={"disp": verbose, "maxiter": 1000, "ftol": 1e-9},
        )

        if not stage2_result.success:
            print(f"WARNING: Stage 2 did not converge: {stage2_result.message}")
            print("Using Stage 1 solution instead.")
            stage2_result = stage1_result

        # ============= BUILD OUTPUT =============
        df = df.copy()
        df["Opt_Weight"] = stage2_result.x
        df["Allocated_Amount"] = stage2_result.x * self.net_cash_outflow

        total_allocated = df["Allocated_Amount"].sum()
        expected_return = -stage2_result.fun
        lcr = self._compute_hqla_value(stage2_result.x) / self.net_cash_outflow
        portfolio_duration = self._compute_portfolio_duration(stage2_result.x)

        output_df = df[
            ["Name", "Level", "DirtyPrice", "YTM", "ModDuration", "Allocated_Amount"]
        ]

        if verbose:
            print(f"\n" + "=" * 60)
            print("FINAL RESULTS (After Both Stages)")
            print("=" * 60)
            print(f"Total Allocated: ${total_allocated:,.2f}")
            print(f"  As % of NCO: {total_allocated/self.net_cash_outflow:.2%}")
            print(
                f"  Excess over minimum: {(total_allocated/self.net_cash_outflow - min_allocation):.2%}"
            )
            print(f"Net Cash Outflow: ${self.net_cash_outflow:,.2f}")
            print(f"Expected Return: {expected_return:.4%}")
            print(
                f"  Improvement over Stage 1: {expected_return - np.dot(stage1_result.x, mu):.4%}"
            )
            print(
                f"LCR Ratio: {lcr:.2%} (target: {self.min_lcr:.0%}-{self.max_lcr:.0%})"
            )
            print(f"Portfolio Duration: {portfolio_duration:.2f} years")
            print("=" * 60)

        return output_df, stage2_result, total_allocated, expected_return, lcr

    def mean_variance_lexicographic(
        self,
        risk_aversion: float = 2.0,
        base_curve_handle: ql.YieldTermStructureHandle = None,
        up_curve: ql.YieldTermStructureHandle = None,
        down_curve: ql.YieldTermStructureHandle = None,
        survival_curves: Dict[str, ql.DefaultProbabilityTermStructureHandle] = None,
        survival_curves_up: Dict[str, ql.DefaultProbabilityTermStructureHandle] = None,
        survival_curves_down: Dict[
            str, ql.DefaultProbabilityTermStructureHandle
        ] = None,
        n_random: int = 500,
        bp_std: float = 0.01,
        use_shrinkage: bool = True,
        max_position_size: float = 0.30,
        min_position_size: float = 0.0,
        max_total_allocation: float = 2.0,
        verbose: bool = True,
    ) -> Tuple[pd.DataFrame, object, float, float, float]:
        """
        TWO-STAGE MEAN-VARIANCE OPTIMIZATION:

        Stage 1: Find minimum allocation
        Stage 2: Optimize mean-variance within allocation constraint
        """
        if base_curve_handle is None:
            raise ValueError("base_curve_handle required for scenario repricing.")

        # Generate scenarios
        sg = SCENARIO.ScenarioGenerator(self.portfolio)
        scenarios = sg.generate_parallel_scenarios(n_random=n_random, bp_std=bp_std)
        R, base_prices, inst_list = sg.compute_returns_matrix(
            base_curve_handle,
            scenarios,
            up_curve,
            down_curve,
            survival_curves,
            survival_curves_up,
            survival_curves_down,
        )

        if use_shrinkage:
            Omega = self.ledoit_wolf_shrinkage(R)
        else:
            Omega = sg.make_psd_cov(R)

        mu = np.array(self.assets_summary["YTM"].values, dtype=float)
        levels = self.assets_summary["Level"].values
        N = len(mu)

        # ============= STAGE 1: MINIMIZE ALLOCATION =============
        if verbose:
            print("\n" + "=" * 60)
            print("STAGE 1: Finding minimum HQLA allocation...")
            print("=" * 60)

        def stage1_objective(w):
            return np.sum(w)

        stage1_constraints = self._build_base_constraints(levels, max_total_allocation)
        bounds = [(min_position_size, max_position_size) for _ in range(N)]

        x0 = np.zeros(N)
        l1_mask = levels == "L1"
        n_l1 = np.sum(l1_mask)
        if n_l1 > 0:
            x0[l1_mask] = self.min_lcr / n_l1
        else:
            x0 = np.ones(N) * self.min_lcr / N

        stage1_result = minimize(
            stage1_objective,
            x0=x0,
            bounds=bounds,
            constraints=stage1_constraints,
            method="SLSQP",
            options={"disp": False, "maxiter": 1000, "ftol": 1e-9},
        )

        min_allocation = np.sum(stage1_result.x)

        if verbose:
            print(f"Minimum allocation: {min_allocation:.4f} × NCO")

        # ============= STAGE 2: MEAN-VARIANCE =============
        if verbose:
            print("\n" + "=" * 60)
            print("STAGE 2: Optimizing mean-variance...")
            print("=" * 60)

        max_allowed_allocation = min_allocation * (1 + self.allocation_buffer)

        def stage2_objective(w):
            ret = float(w @ mu)
            var = float(w @ (Omega @ w))
            return -(ret - risk_aversion * var)

        stage2_constraints = self._build_base_constraints(levels, max_total_allocation)
        stage2_constraints.append(
            {"type": "ineq", "fun": lambda w: max_allowed_allocation - np.sum(w)}
        )

        stage2_result = minimize(
            stage2_objective,
            x0=stage1_result.x,
            bounds=bounds,
            constraints=stage2_constraints,
            method="SLSQP",
            options={"disp": verbose, "maxiter": 1000, "ftol": 1e-9},
        )

        if not stage2_result.success:
            print(f"WARNING: Stage 2 did not converge: {stage2_result.message}")
            stage2_result = stage1_result

        # Build output
        df = self.assets_summary.copy()
        df["Opt_Weight"] = stage2_result.x
        df["Allocated_Amount"] = stage2_result.x * self.net_cash_outflow

        port_return = float(stage2_result.x @ mu)
        port_var = float(stage2_result.x @ (Omega @ stage2_result.x))
        port_std = np.sqrt(port_var)
        lcr = self._compute_hqla_value(stage2_result.x) / self.net_cash_outflow
        portfolio_duration = self._compute_portfolio_duration(stage2_result.x)
        total_allocated = df["Allocated_Amount"].sum()

        sharpe = port_return / port_std if port_std > 0 else 0

        output_df = df[
            ["Name", "Level", "DirtyPrice", "YTM", "ModDuration", "Allocated_Amount"]
        ]

        if verbose:
            print(f"\n" + "=" * 60)
            print("FINAL MEAN-VARIANCE RESULTS")
            print("=" * 60)
            print(f"Risk Aversion: {risk_aversion:.2f}")
            print(
                f"Total Allocated: ${total_allocated:,.2f} ({total_allocated/self.net_cash_outflow:.2%} of NCO)"
            )
            print(f"Expected Return: {port_return:.4%}")
            print(f"Portfolio Volatility: {port_std:.4%}")
            print(f"Sharpe Ratio: {sharpe:.2f}")
            print(f"LCR Ratio: {lcr:.2%}")
            print(f"Portfolio Duration: {portfolio_duration:.2f} years")
            print("=" * 60)

        return output_df, stage2_result, total_allocated, port_return, lcr

    def mean_optimize_enhanced(
        self,
        max_position_size: float = 0.5,
        min_position_size: float = 0.01,
    ) -> Tuple[pd.DataFrame, object, float, float, float]:
        """
        Mean optimization with:
        - Proper LCR calculation
        - Duration constraints
        - Position size limits
        """
        df = self.assets_summary
        mu = df["YTM"].values

        # Objective: maximize expected return
        def objective(w):
            return -np.dot(w, mu)

        # Constraints list
        constraints = []

        # 1. Level 1 at least 60% (Level 2 combined max 40%)
        levels = df["Level"].values
        constraints.append(
            {"type": "ineq", "fun": lambda w: np.sum(w[levels == "L1"]) - 0.6}
        )

        # 2. Level 2B max 15%
        constraints.append(
            {"type": "ineq", "fun": lambda w: 0.15 - np.sum(w[levels == "L2B"])}
        )

        # 3. LCR constraints
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: self._compute_hqla_value(w) / self.net_cash_outflow
                - self.min_lcr,
            }
        )
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: self.max_lcr
                - self._compute_hqla_value(w) / self.net_cash_outflow,
            }
        )

        # 4. Duration constraint
        if self.target_duration is not None:
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: self._compute_portfolio_duration(w)
                    - (self.target_duration - self.duration_tolerance),
                }
            )
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: (self.target_duration + self.duration_tolerance)
                    - self._compute_portfolio_duration(w),
                }
            )

        # Bounds: position size limits
        bounds = [(min_position_size, max_position_size) for _ in range(self.n_assets)]

        # Initial guess: equal weight
        x0 = np.ones(self.n_assets) / self.n_assets

        # Optimize
        result = minimize(
            objective,
            x0=x0,
            bounds=bounds,
            constraints=constraints,
            method="SLSQP",
            options={"disp": True, "maxiter": 1000, "ftol": 1e-9},
        )

        if not result.success:
            print(f"Warning: Optimization did not converge: {result.message}")

        # Build output
        df = df.copy()
        df["Opt_Weight"] = result.x
        df["Allocated_Amount"] = result.x * self.net_cash_outflow

        total_value = df["Allocated_Amount"].sum()
        expected_return = -result.fun  # Negate because we minimized -return
        lcr = self._compute_hqla_value(result.x) / self.net_cash_outflow
        portfolio_duration = self._compute_portfolio_duration(result.x)

        output_df = df[
            ["Name", "Level", "DirtyPrice", "YTM", "ModDuration", "Allocated_Amount"]
        ]

        print(f"\n=== Optimization Results ===")
        print(f"Total Portfolio Value: ${total_value:,.2f}")
        print(f"Expected Return: {expected_return:.4%}")
        print(f"LCR Ratio: {lcr:.2%}")
        print(f"Portfolio Duration: {portfolio_duration:.2f} years")

        return output_df, result, total_value, expected_return, lcr

    def mean_variance_optimize_enhanced(
        self,
        lam: float = 0.5,
        base_curve_handle: ql.YieldTermStructureHandle = None,
        n_random: int = 500,
        bp_std: float = 0.01,
        use_shrinkage: bool = True,
        max_position_size: float = 0.25,
        min_position_size: float = 0.01,
    ) -> Tuple[pd.DataFrame, object, float, float, float]:
        """
        Mean-variance optimization with:
        - Ledoit-Wolf shrinkage covariance
        - Duration constraints
        - Proper LCR calculation
        """
        if base_curve_handle is None:
            raise ValueError("base_curve_handle required for scenario repricing.")

        # Generate scenarios and compute returns
        sg = SCENARIO.ScenarioGenerator(self.portfolio)
        scenarios = sg.generate_parallel_scenarios(n_random=n_random, bp_std=bp_std)
        R, base_prices, inst_list = sg.compute_returns_matrix(
            base_curve_handle, scenarios
        )

        # Covariance estimation
        if use_shrinkage:
            Omega = self.ledoit_wolf_shrinkage(R)
        else:
            Omega = sg.make_psd_cov(R)

        # Expected returns (use YTM as forward-looking estimate)
        mu = np.array(self.assets_summary["YTM"].values, dtype=float)

        N = len(mu)

        # Objective: -λ * return + (1-λ) * variance
        def obj(w):
            ret = float(w @ mu)
            var = float(w @ (Omega @ w))
            return -lam * ret + (1 - lam) * var

        # Constraints: same as mean optimization
        constraints = []

        levels = self.assets_summary["Level"].values
        constraints.append(
            {"type": "ineq", "fun": lambda w: np.sum(w[levels == "L1"]) - 0.6}
        )
        constraints.append(
            {"type": "ineq", "fun": lambda w: 0.15 - np.sum(w[levels == "L2B"])}
        )

        constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: self._compute_hqla_value(w) / self.net_cash_outflow
                - self.min_lcr,
            }
        )
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: self.max_lcr
                - self._compute_hqla_value(w) / self.net_cash_outflow,
            }
        )

        if self.target_duration is not None:
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: self._compute_portfolio_duration(w)
                    - (self.target_duration - self.duration_tolerance),
                }
            )
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: (self.target_duration + self.duration_tolerance)
                    - self._compute_portfolio_duration(w),
                }
            )

        bounds = [(min_position_size, max_position_size) for _ in range(N)]
        x0 = np.ones(N) / N

        result = minimize(
            obj,
            x0=x0,
            bounds=bounds,
            constraints=constraints,
            method="SLSQP",
            options={"maxiter": 1000, "ftol": 1e-9, "disp": True},
        )

        if not result.success:
            print(f"Warning: MV optimization did not converge: {result.message}")

        # Build output
        df = self.assets_summary.copy()
        df["Opt_Weight"] = result.x
        df["Allocated_Amount"] = result.x * self.net_cash_outflow

        port_return = float(result.x @ mu)
        port_var = float(result.x @ (Omega @ result.x))
        port_std = np.sqrt(port_var)
        lcr = self._compute_hqla_value(result.x) / self.net_cash_outflow
        portfolio_duration = self._compute_portfolio_duration(result.x)

        total_value = df["Allocated_Amount"].sum()

        output_df = df[
            ["Name", "Level", "DirtyPrice", "YTM", "ModDuration", "Allocated_Amount"]
        ]

        print(f"\n=== Mean-Variance Optimization Results ===")
        print(f"Total Portfolio Value: ${total_value:,.2f}")
        print(f"Expected Return: {port_return:.4%}")
        print(f"Portfolio Volatility: {port_std:.4%}")
        print(
            f"Sharpe Ratio (approx): {port_return/port_std if port_std > 0 else 0:.2f}"
        )
        print(f"LCR Ratio: {lcr:.2%}")
        print(f"Portfolio Duration: {portfolio_duration:.2f} years")

        return output_df, result, total_value, port_return, lcr
