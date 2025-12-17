# scenario_rebalancing.py
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional, Any
import textwrap
import warnings
import json
import copy
from openai import OpenAI
import QuantLib as ql


from hqla_portfolio_opt import HQLA_Portfolio_Opt_Enhanced
from hqla_portfolio import Portfolio
from hqla_instruments import Fixed, Floating, Zero

# ------------------------
# Scenario dataclass
# ------------------------
@dataclass
class Scenario:
    name: str
    yield_curve_handle: ql.YieldTermStructureHandle
    sofr_handle: Optional[Any] = None
    probability: float = 0.0
    metadata: Dict = None  # Optional extra info (description)

    def build_sofr_handle(self):
        # Create a SOFR index using the scenario yield curve
        self.sofr_handle = ql.OvernightIndex(
            "SOFR",
            0,
            ql.USDCurrency(),
            ql.TARGET(),
            ql.Actual360(),
            self.yield_curve_handle
        )


# ------------------------
# ScenarioRebalancingEngine
# ------------------------
class ScenarioRebalancingEngine:
    """
    Manages running portfolio rebalances across scenarios, storing results,
    combining scenario portfolios, and generating an AI report.
    """

    def __init__(
        self,
        base_portfolio: Portfolio,
        net_cash_outflow: float,
        min_lcr: float = 1.0,
        max_lcr: float = 1.5,
        target_duration: Optional[float] = None,
        duration_tolerance: float = 0.5,
        allocation_buffer: float = 0.02,
    ):
        self.base_portfolio = base_portfolio

        # scenario-specific results
        self.scenarios: Dict[str, Scenario] = {}
        self.results: Dict[str, Dict] = {}

        # final combined weights
        self.final_portfolio_weights: Optional[np.ndarray] = None

        # global optimizer defaults
        self.net_cash_outflow = net_cash_outflow
        self.min_lcr = min_lcr
        self.max_lcr = max_lcr
        self.target_duration = target_duration
        self.duration_tolerance = duration_tolerance
        self.allocation_buffer = allocation_buffer
        

    # ------------------------
    # Scenario management
    # ------------------------
    def add_scenario(self, scenario: Scenario):
        if scenario.name in self.scenarios:
            warnings.warn(f"Overwriting existing scenario '{scenario.name}'")
        self.scenarios[scenario.name] = scenario

    def remove_scenario(self, name: str):
        self.scenarios.pop(name, None)
        self.results.pop(name, None)

    # ------------------------
    # Running rebalances
    # ------------------------
    def run_rebalancing(self, method: str = "mean_lexicographic", **kwargs):
        """
        Run optimization for each scenario using the chosen method.
        method: "lexicographic", "mean_variance_lexicographic", "mean_optimize_enhanced", "mean_variance_optimize_enhanced"
        method_kwargs: forwarded to optimizer method
        """

        for name, scen in self.scenarios.items():

            # Create a deep copy
            scen_portfolio = self.base_portfolio.clone()

            if scen.sofr_handle is None:
                raise ValueError(f"Scenario {scen.name} has no SOFR handle")

            for level, group in scen_portfolio.assets.items():
                for inst in group:
                    if isinstance(inst, Floating):
                        inst.build_bond(index=scen.sofr_handle)
                    else:
                        inst.build_bond()

            # Reprice the portfolio with all
            #  curves (up/down and survival curves)
            # Extract curves from scenario metadata (built in convert_frontend_scenarios_with_curves)
            up_curve = scen.metadata.get("up_curve")
            down_curve = scen.metadata.get("down_curve")
            survival_curves = scen.metadata.get("survival_curves", {})
            survival_curves_up = scen.metadata.get("survival_curves_up", {})
            survival_curves_down = scen.metadata.get("survival_curves_down", {})
            
            # If curves are in metadata, use them; otherwise fallback to base curves
            if up_curve and down_curve:
                scen_portfolio.update_prices(
                    scen.yield_curve_handle,
                    up_curve,
                    down_curve,
                    survival_curves,
                    survival_curves_up,
                    survival_curves_down,
                )
            else:
                # Fallback: use base curves if scenario curves not available
                # This shouldn't happen if convert_frontend_scenarios_with_curves is used correctly
                raise RuntimeError(
                    f"Scenario '{name}' missing required curves in metadata. "
                    "Ensure convert_frontend_scenarios_with_curves builds all curves."
                )

            # Construct optimizer for THIS scenario
            opt = HQLA_Portfolio_Opt_Enhanced(portfolio=scen_portfolio,
                                            net_cash_outflow=self.net_cash_outflow,
                                            min_lcr=self.min_lcr,
                                            max_lcr=self.max_lcr,
                                            target_duration=self.target_duration,
                                            duration_tolerance=self.duration_tolerance,
                                            allocation_buffer=self.allocation_buffer,)


            # call chosen method and normalize returned tuple
            if method == "mean_lexicographic":
                out = opt.lexicographic_mean_optimize(**kwargs)
            elif method == "mean_variance_lexicographic":
                kwargs = {
                    **kwargs,
                    "base_curve_handle": scen.yield_curve_handle,
                    "up_curve": up_curve,
                    "down_curve": down_curve,
                    "survival_curves": survival_curves,
                    "survival_curves_up": survival_curves_up,
                    "survival_curves_down": survival_curves_down,
                }
                out = opt.mean_variance_lexicographic(**kwargs)
            else:
                raise ValueError(f"Unknown method '{method}'")

            # Normalize and store
            df, res_obj, total_alloc, port_return, lcr = out
            weights = self._extract_weights(df, res_obj)
            metrics = {
                "total_allocated": float(total_alloc),
                "expected_return": float(port_return),
                "lcr": float(lcr),
                "weights_sum": float(np.sum(weights)),
            }
            self.results[name] = {"scenario": scen, "df": df, "result": res_obj, "metrics": metrics, "weights": weights}

    def _extract_weights(self, df: pd.DataFrame, res_obj) -> np.ndarray:
        """
        Robust extraction of weights vector from returned df/result:
        - Prefer df column 'Opt_Weight' or 'Opt_Weight_MV' if present
        - Else, try res_obj.x (scipy optimize result)
        - Else, try from Allocated_Amount normalized by net_cash_outflow
        """
        if "Opt_Weight" in df.columns:
            return np.array(df["Opt_Weight"].fillna(0.0), dtype=float)
        if "Opt_Weight_MV" in df.columns:
            return np.array(df["Opt_Weight_MV"].fillna(0.0), dtype=float)
        # result.x
        try:
            x = np.array(res_obj.x, dtype=float)
            return x
        except Exception:
            # fallback to Allocated_Amount / NCO
            if "Allocated_Amount" in df.columns and self.optimizer.net_cash_outflow > 0:
                return np.array(df["Allocated_Amount"].fillna(0.0) / self.net_cash_outflow, dtype=float)
        # last resort: zeros
        return np.zeros(len(df))

    # ------------------------
    # Combining portfolios
    # ------------------------
    def combine_portfolios(
        self,
        mode: str = "probability_weighted",
        worst_by: str = "expected_return",
        top_k: int = 2,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Combine scenario-specific portfolios into final weights.
        Modes:
          - "probability_weighted" : w = sum p_i * w_i
          - "worst_case"           : choose w of the single worst scenario (worst_by = 'expected_return' or 'lcr')
          - "top_k_worst_avg"      : average the top_k worst scenarios (by worst_by)
          - "custom"               : custom_weights dict name->weight (must sum to 1)
        Returns combined weight vector (numpy array).
        """
        if not self.results:
            raise RuntimeError("No scenario results to combine. Run run_rebalancing() first.")

        # Ensure scenario ordering consistent
        scenario_names = list(self.results.keys())
        first_weights = next(iter(self.results.values()))["weights"]
        N = len(first_weights)

        # Helper: build mapping name -> weights and metrics
        w_map = {name: info["weights"] for name, info in self.results.items()}
        metrics_map = {name: info["metrics"] for name, info in self.results.items()}

        if mode == "probability_weighted":
            # Ensure probabilities sum to ~1; renormalize if needed
            probs = np.array([self.scenarios[name].probability for name in scenario_names], dtype=float)
            if probs.sum() <= 0:
                warnings.warn("Scenario probabilities sum to zero or were not provided. Using uniform probabilities.")
                probs = np.ones_like(probs) / len(probs)
            else:
                probs = probs / probs.sum()
            combined = np.zeros(N)
            for name, p in zip(scenario_names, probs):
                w = w_map[name]
                if len(w) != N:
                    raise ValueError(f"Mismatch in weights length for scenario {name}")
                combined += p * w
            self.final_portfolio_weights = combined
            return combined

        elif mode == "worst_case":
            # worst_by can be 'expected_return' (smallest return) or 'lcr' (smallest lcr)
            if worst_by == "expected_return":
                worst_name = min(metrics_map.items(), key=lambda kv: kv[1]["expected_return"])[0]
            elif worst_by == "lcr":
                worst_name = min(metrics_map.items(), key=lambda kv: kv[1]["lcr"])[0]
            else:
                raise ValueError("worst_by must be 'expected_return' or 'lcr'")
            self.final_portfolio_weights = w_map[worst_name]
            return w_map[worst_name]

        elif mode == "top_k_worst_avg":
            if worst_by == "expected_return":
                sorted_names = sorted(metrics_map.keys(), key=lambda n: metrics_map[n]["expected_return"])
            elif worst_by == "lcr":
                sorted_names = sorted(metrics_map.keys(), key=lambda n: metrics_map[n]["lcr"])
            else:
                raise ValueError("worst_by must be 'expected_return' or 'lcr'")

            worst_k = sorted_names[:min(top_k, len(sorted_names))]
            avg = np.mean(np.vstack([w_map[n] for n in worst_k]), axis=0)
            self.final_portfolio_weights = avg
            return avg

        elif mode == "custom":
            if not custom_weights:
                raise ValueError("custom_weights must be provided for mode='custom'")
            # Normalize provided weights
            keys = list(custom_weights.keys())
            vals = np.array([custom_weights[k] for k in keys], dtype=float)
            if vals.sum() <= 0:
                raise ValueError("custom_weights sum to zero or negative")
            vals = vals / vals.sum()
            combined = np.zeros(N)
            for k, v in zip(keys, vals):
                if k not in w_map:
                    raise KeyError(f"Scenario '{k}' not found in results")
                combined += v * w_map[k]
            self.final_portfolio_weights = combined
            return combined

        else:
            raise ValueError(f"Unknown combine mode '{mode}'")

    # ------------------------
    # Apply / show final portfolio
    # ------------------------
    def build_combined_dataframe(self) -> pd.DataFrame:
        """
        Build a DataFrame for the final combined portfolio compatible with your existing output schema.
        Uses today's prices from base_portfolio.
        """
        if self.final_portfolio_weights is None:
            raise RuntimeError("No final portfolio computed. Call combine_portfolios() first.")
        
        # Build dataframe from base_portfolio instruments (using today's prices)
        rows = []
        for level, group in self.base_portfolio.assets.items():
            for inst in group:
                rows.append({
                    "Name": inst.name,
                    "Level": level,
                    "DirtyPrice": getattr(inst, "dirty_price", np.nan),
                    "YTM": getattr(inst, "ytm", np.nan),
                    "ModDuration": getattr(inst, "duration", np.nan),
                })
        
        assets_df = pd.DataFrame(rows)
        w = np.array(self.final_portfolio_weights, dtype=float)
        assets_df["Combined_Weight"] = w
        assets_df["Allocated_Amount"] = w * self.net_cash_outflow
        
        # Keep key columns
        cols = [c for c in ["Name", "Level", "DirtyPrice", "YTM", "ModDuration"] if c in assets_df.columns]
        return assets_df[cols + ["Combined_Weight", "Allocated_Amount"]]

    def apply_final_portfolio(self, update_quantities: bool = True):
        """
        Optionally update the underlying Portfolio instrument quantities using
        today's prices from base_portfolio to calculate quantities:
            new_qty = Allocated_Amount / inst.dirty_price
        (This uses today's prices, not scenario prices, since we're buying today.)
        """
        df = self.build_combined_dataframe()
        if update_quantities:
            for _, row in df.iterrows():
                name = row["Name"]
                alloc = float(row["Allocated_Amount"])
                # Find instrument in base_portfolio and use its current dirty_price (today's price)
                for lev, group in self.base_portfolio.assets.items():
                    for inst in group:
                        if inst.name == name:
                            # Use today's price from the instrument, not scenario price
                            price = getattr(inst, "dirty_price", None)
                            if price is None or price == 0:
                                new_qty = 0.0
                            else:
                                new_qty = alloc / price
                            inst.quantity = new_qty
                            break
        return df

    # ------------------------
    # User interactions (simple CLI)
    # ------------------------
    def ask_user_for_mode(self) -> str:
        msg = textwrap.dedent("""
        Choose combination mode:
          1. probability_weighted
          2. worst_case (by expected return)
          3. top_k_worst_avg (by expected return)
          4. custom (provide weights)
        Enter 1/2/3/4: """)
        choice = input(msg).strip()
        mapping = {"1": "probability_weighted", "2": "worst_case", "3": "top_k_worst_avg", "4": "custom"}
        return mapping.get(choice, "probability_weighted")

    def prompt_user_for_custom_weights(self) -> Dict[str, float]:
        print("Enter scenario weights as 'scenario_name:weight' one per line. Empty line to finish.")
        weights = {}
        while True:
            line = input().strip()
            if not line:
                break
            if ":" not in line:
                print("Bad format, use 'name:weight'")
                continue
            name, w = line.split(":", 1)
            weights[name.strip()] = float(w.strip())
        return weights

    # ------------------------
    # AI-style report generator (templated)
    # ------------------------

    def generate_report_llm(
        self,
        scenario_descriptions: Dict[str, str],
        openai_api_key: str,
        model: str = "gpt-5.1",
    ) -> str:
        """
        Generates a fixed-income, HQLA-focused professional report using OpenAI.
        The report structure is tightly controlled and uses scenario data +
        optimized portfolios + combined portfolio.

        Parameters
        ----------
        scenario_descriptions : dict
            Mapping: scenario name -> description (from scenario generation module)
        openai_api_key : str
            Secret API key (not stored)
        model : str
            OpenAI model name (default: "gpt-5.1")
        """

        if not self.results:
            raise RuntimeError("No scenario results found. Run run_rebalancing() first.")
        if self.final_portfolio_weights is None:
            raise RuntimeError("Final combined portfolio missing. Call combine_portfolios().")

        # Prepare portfolio details
        combined_df = self.build_combined_dataframe()

        # --- Construct structured JSON for LLM ---
        scenario_payload = {}
        for name, info in self.results.items():
            scen = info["scenario"]
            df = info["df"]
            metrics = info["metrics"]

            scenario_payload[name] = {
                "description": scen.metadata.get("description", ""),
                "probability": scen.probability,
                "net_cash_outflow": scen.metadata.get("net_cash_outflow", self.net_cash_outflow),
                "metrics": metrics,
                "per_asset": df.to_dict(orient="records"),
                "rationale": scen.metadata.get("rationale", ""),
                "impact_channels": scen.metadata.get("impact_channels", ""),
                "trade_list": scen.metadata.get("trade_list", []),
                "shock_type": scen.metadata.get("shock_type", ""),
                "shock_magnitude_bp": scen.metadata.get("shock_magnitude_bp", 0),
                "credit_spreads": scen.metadata.get("credit_spreads", {}),
                "metrics_delta": scen.metadata.get("metrics_delta", {}),
            }

        combined_payload = combined_df.to_dict(orient="records")

        full_payload = {
            "base_portfolio_nco": getattr(self.base_portfolio, "net_cash_outflow", None),
            "scenarios": scenario_payload,
            "final_combined_portfolio": combined_payload,
        }

        # --- Build VERY TIGHT prompt for the LLM ---
        system_msg = """
You are an expert fixed-income portfolio manager specializing in HQLA, liquidity ratios, bank treasury,
and stress scenario construction.

Your task is to produce a CLEAN, PRECISE, HIGHLY STRUCTURED report. 
Tone: institutional, concise, no marketing language, no fluff.
Do NOT invent numbers. Use only what is given in the payload.
"""

        user_msg = f"""
Write a **strictly structured** professional report titled:

    **“HQLA Scenario Optimization & Rebalancing Analysis”**

Use ONLY the data provided in the JSON block below.
Do NOT invent, guess, or extrapolate unknown numbers.

DATA:
{json.dumps(full_payload, indent=2)}

---
### REQUIRED STRUCTURE (DO NOT DEVIATE)

1. Executive Summary  
   - Purpose of exercise
   - Number of scenarios
   - Key optimization method
   - High-level outcome (LCR direction, allocation shifts)
   - One-line risk characterization

2. Scenario Set Description  
   For each scenario:  
   - Scenario name  
   - Description (from input)  
   - Probability  
   - Net Cash Outflow  
   - 2–3 bullets summarizing unique pressures (YTM shifts, curve shocks, liquidity stress)  

3. Portfolio Behavior Under Scenarios  
   For each scenario:  
   - One paragraph explaining how the optimized portfolio reacts  
   - Highlight drivers: yield pickup, LCR constraints, haircuts, duration changes  
   - Mention any concentration risk  
   - Identify the most constraining scenario and most return-enhancing scenario

4. Final Combined Portfolio Recommendation  
   - Describe overall allocation profile  
   - Major overweight/underweight vs base  
   - Provide commentary on risk, duration, LCR buffer, and haircut implications

5. Recommendations
   - Clear, concise bullets (max 6)
   - Topics: liquidity buffer, asset class adjustments, curve exposure, duration, haircut constraints,
     robustness to severe stress scenarios.
   - No fluff.

ABSOLUTE RULES:
- Do NOT include JSON.
- Do NOT repeat the data verbatim.
- Do NOT speculate or add data that is missing.
- Do NOT speak generically — ground all statements in the provided numbers.
- Maintain numerical consistency.
"""

        # --- Call OpenAI API ---
        client = OpenAI(api_key=openai_api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_completion_tokens=2800,
            temperature=0.2,
        )

        report_text = response.choices[0].message.content
        return report_text


    def run_full_workflow_with_scenarios(self, scenarios_dict: Dict[str, Dict], openai_api_key: str):
        """
        Full workflow using a pre-specified dictionary of scenarios.

        Parameters
        ----------
        scenarios_dict : dict
            Mapping of scenario_name -> {
                "description": str,
                "probability": float,
                "yield_curve_handle": QuantLib YieldTermStructureHandle (optional),
                "sofr_handle": optional
            }
        openai_api_key : str
            OpenAI API key for report generation.
        """

        

        # ------------------------
        # Step 2: Ask user for optimization method
        # ------------------------
        print("\nChoose optimization method:")
        print("1. Mean-only (lexicographic)")
        print("2. Mean-variance lexicographic")
        method_choice = input("Enter 1 or 2 [default=1]: ").strip()
        if method_choice == "2":
            method = "mean_variance_lexicographic"
        else:
            method = "mean_lexicographic"

        # ------------------------
        # Step 3: Ask user for portfolio combination mode
        # ------------------------
        print("\nChoose portfolio combination mode:")
        mode = self.ask_user_for_mode()
        custom_weights = None
        if mode == "custom":
            custom_weights = self.prompt_user_for_custom_weights()

        # ------------------------
        # Step 4: Run scenario rebalancing
        # ------------------------
        print("\nRunning scenario rebalancing...")
        self.run_rebalancing(method=method)

        # ------------------------
        # Step 5: Combine portfolios
        # ------------------------
        print("\nCombining scenario portfolios...")
        combined = self.combine_portfolios(mode=mode, custom_weights=custom_weights)
        print(f"Final combined portfolio weights:\n{combined}")

        # ------------------------
        # Step 6: Generate AI report
        # ------------------------
        scenario_descriptions = {
            name: info["scenario"].metadata.get("description", "")
            for name, info in self.results.items()
        }
        print("\nGenerating AI report...")
        report = self.generate_report_llm(
            scenario_descriptions=scenario_descriptions,
            openai_api_key=openai_api_key
        )
        print("\n--- AI Generated Report ---")
        print(report)

        # ------------------------
        # Step 7: Update base portfolio
        # ------------------------
        update = input("\nUpdate underlying base portfolio today? (y/n): ").strip().lower()
        if update in ("y", "yes"):
            df_updated = self.apply_final_portfolio(update_quantities=True)
            print("\nBase portfolio updated. Summary:")
            print(df_updated)
        else:
            print("Base portfolio not updated.")




