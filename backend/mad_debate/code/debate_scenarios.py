#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HQLA Multi-Agent Debate (MAD) Scenario Generator — max-debug rewrite

Key improvements vs previous version:
- Robust JSON parsing from judge (handles ```json fences & stray prose)
- Larger judge token budget to reduce truncation
- Configurable output format (--format json|jsonl)
- Clearer logging + optional raw/WIP artifacts per run
- Retry/backoff around API calls
"""

from __future__ import annotations

import os, sys, json, argparse, copy, statistics, time, random, traceback, logging, textwrap, re, shutil, datetime, calendar
from typing import List, Dict, Any, Optional

import yaml

# --- OpenAI new SDK (>=1.0) ---
try:
    import openai as openai_pkg
    from openai import OpenAI
except Exception as e:
    print("ERROR: Failed to import the new OpenAI SDK. Try: pip install --upgrade 'openai>=1.0.0'", file=sys.stderr)
    raise

# =========================================================
# Logging / Utils
# =========================================================

def setup_logging(logdir: Optional[str], verbose: bool) -> None:
    logfmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%H:%M:%S"
    handlers = [logging.StreamHandler(sys.stdout)]
    if logdir:
        os.makedirs(logdir, exist_ok=True)
        handlers.append(logging.FileHandler(os.path.join(logdir, "run.log"), encoding="utf-8"))
    logging.basicConfig(level=(logging.DEBUG if verbose else logging.INFO),
                        format=logfmt, datefmt=datefmt, handlers=handlers)

def short(s: str, n=900) -> str:
    s = (s or "").strip()
    return (s[:n] + " …[trunc]") if len(s) > n else s

def pretty(obj: Any, n=1500) -> str:
    try:
        txt = json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        txt = str(obj)
    return short(txt, n)

def require_env(var: str) -> str:
    val = os.getenv(var, "")
    if not val:
        logging.error(f"Environment variable {var} is not set.")
        sys.exit(1)
    return val

def add_months(d: datetime.date, months: int) -> datetime.date:
    """Return date d advanced by <months>, clamping day to month end."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)

# =========================================================
# OpenAI client
# =========================================================

CLIENT: Optional[OpenAI] = None

def client_init() -> None:
    global CLIENT
    key = require_env("OPENAI_API_KEY")
    logging.info(f"Detected OPENAI_API_KEY (length={len(key)}).")
    logging.info(f"openai package version: {getattr(openai_pkg, '__version__', 'unknown')}")
    # Honor optional custom base URL / project if present
    opts = {}
    base = os.getenv("OPENAI_BASE_URL")
    if base:
        opts["base_url"] = base
        logging.info(f"Using custom OPENAI_BASE_URL={base}")
    project = os.getenv("OPENAI_PROJECT")
    if project:
        opts["project"] = project
        logging.info(f"Using OPENAI_PROJECT={project}")
    CLIENT = OpenAI(**opts)  # auto-uses env var

# =========================================================
# Chat wrapper w/ retries
# =========================================================

def chat(model: str,
         messages: List[Dict[str, str]],
         temperature: float = 0.7,
         top_p: float = 0.9,
         max_tokens: int = 10000,
         run_tag: str = "",
         round_tag: str = "",
         max_retries: int = 6) -> str:
    assert CLIENT is not None, "CLIENT not initialized"
    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            logging.debug(f"[{run_tag} {round_tag}] Calling model={model} temp={temperature} top_p={top_p} max_tokens={max_tokens}")
            logging.debug(f"[{run_tag} {round_tag}] Messages preview:\n{pretty(messages, 3000)}")
            resp = CLIENT.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            content = (resp.choices[0].message.content or "").strip()
            usage = getattr(resp, "usage", None)
            if usage:
                logging.info(f"[{run_tag} {round_tag}] tokens: prompt={usage.prompt_tokens} output={usage.completion_tokens} total={usage.total_tokens}")
            logging.debug(f"[{run_tag} {round_tag}] Output preview:\n{short(content, 1500)}")
            return content
        except Exception as e:
            etxt = f"{type(e).__name__}: {e}"
            logging.warning(f"[{run_tag} {round_tag}] API error on attempt {attempt}/{max_retries}: {etxt}")
            if attempt == max_retries:
                logging.error(f"[{run_tag} {round_tag}] Exhausted retries. Raising.")
                raise
            sleep = backoff * (1.0 + random.random())
            logging.info(f"[{run_tag} {round_tag}] Backing off {sleep:.2f}s before retry.")
            time.sleep(sleep)
            backoff *= 2.0

# =========================================================
# Prompt helpers
# =========================================================

def make_messages(system_prompt: str,
                  user_prompt: str,
                  history: Optional[List[Dict[str, str]]] = None):
    msgs = [{"role": "system", "content": system_prompt}]
    if history:
        msgs += history
    msgs.append({"role": "user", "content": user_prompt})
    return msgs

# =========================================================
# JSON extraction / validation
# =========================================================

REQUIRED_TOP_KEYS = {
    "Scenario",
    "Description",
    "Probability",
    "Rationale",
    "ImpactChannels",
    "Shocks",
    "MetricsDelta",
    "TradeList",
    "Assumptions",
    "Signals",
}

def validate_schema_one(obj: Dict[str, Any]) -> List[str]:
    missing = []
    for k in REQUIRED_TOP_KEYS:
        if k not in obj:
            missing.append(k)
    return missing

def extract_json_block(s: str) -> Optional[str]:
    """Return a JSON string extracted from s.
    Prefers fenced ```json blocks; falls back to first top-level [] or {}."""
    if not s:
        return None
    m = re.search(r"```json\s*(.+?)\s*```", s, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Fallback: take the first top-level array/object
    start = None
    for i, ch in enumerate(s):
        if ch in "[{":
            start = i
            break
    if start is None:
        return None

    stack = []
    for j in range(start, len(s)):
        ch = s[j]
        if ch in "[{":
            stack.append(ch)
        elif ch in "]}":
            if not stack:
                return None
            top = stack.pop()
            if (top, ch) not in {('[', ']'), ('{', '}')}:
                return None
            if not stack:
                return s[start:j + 1].strip()
    return None

def loads_relaxed(s: str) -> Any:
    """Try strict json.loads, else try to extract a JSON block, then load.
    As an extra fallback, also handle simple JSONL (one JSON object per line)."""
    if not s:
        raise ValueError("Empty string for JSON parse")

    # 1) First try strict JSON on the whole string
    try:
        return json.loads(s)
    except Exception:
        pass

    # 2) Try to extract a fenced / top-level JSON array or object
    clip = extract_json_block(s)
    if clip is not None:
        try:
            return json.loads(clip)
        except Exception:
            # fall through to JSONL attempt
            pass

    # 3) Fallback: JSONL-style (one object per line)
    objs: List[Any] = []
    for line in s.splitlines():
        line = line.strip()
        if not line:
            continue
        # ignore obvious log noise lines
        if line.startswith("#"):
            continue
        try:
            obj = json.loads(line)
            objs.append(obj)
        except Exception:
            continue

    if objs:
        return objs

    raise ValueError("No JSON block or JSONL-style content could be parsed")

# =========================================================
# Two-phase reasoning+JSON helpers
# =========================================================

def split_reasoning_json(s: str) -> tuple[str, str]:
    """
    Split a two-phase model response into (reasoning, json_text).
    We look for a 'Revised JSON:' (case-insensitive) label. If not found,
    we return ("", s) to keep backward compatibility with JSON-only replies.
    """
    if not s:
        return "", ""
    # Normalize line endings
    t = s.replace("\r\n", "\n")
    # Find the label 'Revised JSON:'
    m = re.search(r"(?im)^\s*Revised\s+JSON\s*:\s*", t)
    if not m:
        # Some models may emit "Final JSON:" or "Final Answer (JSON):"
        m = re.search(r"(?im)^\s*(Final\s+JSON|Final\s+Answer\s*\(JSON\))\s*:\s*", t)
    if not m:
        return "", t.strip()
    idx = m.end()
    reasoning = t[:m.start()].strip()
    json_part = t[idx:].strip()
    return reasoning, json_part

def normalize_two_phase(reasoning: str, json_part: str) -> str:
    """
    Build a compact assistant message that keeps both the reasoning
    and the raw JSON for downstream judge context.
    """
    reasoning = (reasoning or "").strip()
    json_part = (json_part or "").strip()
    if reasoning:
        return f"Reasoning:\n{reasoning}\n\nRevised JSON:\n{json_part}"
    else:
        return json_part


# =========================================================
# One debate run
# =========================================================

# Write a per-run transcript as both JSONL and Markdown
def write_transcript(artifacts_dir: str, run_idx: int, transcript: List[Dict[str, Any]]) -> None:
    """Write a per-run transcript as both JSONL and Markdown."""
    os.makedirs(artifacts_dir, exist_ok=True)
    base = os.path.join(artifacts_dir, f"transcript_run_{run_idx + 1}")
    # JSONL
    with open(base + ".jsonl", "w", encoding="utf-8") as f:
        for ev in transcript:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    # Markdown (human-friendly)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(f"# Debate Transcript — Run {run_idx + 1}\n\n")
        rounds = {}
        for ev in transcript:
            rounds.setdefault(ev.get("round") or 0, []).append(ev)
        for rnd in sorted(rounds.keys()):
            if rnd != 0:
                f.write(f"## Round {rnd}\n\n")
            for ev in rounds[rnd]:
                speaker = ev.get("speaker", "?")
                label = f"**{speaker}**"
                if rnd == 0:
                    f.write(f"### {label} (Judge)\n\n")
                else:
                    f.write(f"### {label}\n\n")
                if ev.get("reasoning"):
                    f.write("**Reasoning**\n\n")
                    f.write(ev["reasoning"].strip() + "\n\n")
                if ev.get("json"):
                    f.write("**JSON**\n\n")
                    f.write("```json\n")
                    f.write(ev["json"].strip() + "\n")
                    f.write("```\n\n")
                if ev.get("raw") and not ev.get("json"):
                    # If we couldn't split, dump raw for visibility
                    f.write("**Raw**\n\n")
                    f.write(ev["raw"].strip() + "\n\n")

def debate_once(cfg: Dict[str, Any], run_idx: int, artifacts_dir: str, save_wip: bool) -> List[Dict[str, Any]]:
    deb_models = cfg["debate"]["debater_models"]
    rounds = int(cfg["debate"]["rounds"])
    prompts_cfg = cfg.get("prompts", {})
    sysA = (
        prompts_cfg.get("system_debater_a")
        or prompts_cfg.get("system_debater")
        or ""
    )
    sysB = (
        prompts_cfg.get("system_debater_b")
        or prompts_cfg.get("system_debater")
        or ""
    )
    runtime_cfg = cfg.get("_runtime", {})
    if "debater_prompt_a_effective" not in runtime_cfg:
        runtime_cfg["debater_prompt_a_effective"] = sysA
    if "debater_prompt_b_effective" not in runtime_cfg:
        runtime_cfg["debater_prompt_b_effective"] = sysB
    run_tag = f"RUN#{run_idx + 1}"

    transcript: List[Dict[str, Any]] = []

    inputs_cfg = cfg.get("inputs", {})
    header_lines = []
    today = datetime.date.today()
    horizon_date = add_months(today, 6)
    horizon_label = f"{horizon_date.isoformat()} (6 months from {today.isoformat()})"
    header_lines.append(f"Forecast horizon: {horizon_label}")
    portfolio_name = inputs_cfg.get("portfolio_name")
    if portfolio_name:
        header_lines.append(f"Portfolio Name: {portfolio_name}")
    header_lines.append(f"Portfolio: {inputs_cfg.get('portfolio_snapshot')}")
    header_lines.append(f"Constraints: {inputs_cfg.get('constraints')}")
    header_lines.append(f"Indicators: {inputs_cfg.get('indicators')}")
    header_lines.append(f"Priors: {inputs_cfg.get('priors')}")
    header_lines.append(
        "Institution Context: Bank of America — US G-SIB with ~$2.5T assets, "
        "diversified deposits, and a HQLA stack anchored in USTs/Agencies/MBS. "
        "Risk appetite prioritizes LCR ≥ target, NSFR stability, and tight OCI control."
    )
    shock_yaml = inputs_cfg.get("shock_yaml")
    if shock_yaml:
        shock_text = str(shock_yaml).strip()
        if shock_text:
            header_lines.append(f"Shock YAML:\n{shock_text}")
    holdings_csv = inputs_cfg.get("holdings_csv")
    if holdings_csv:
        header_lines.append("Holdings CSV (uploaded preview):\n" + short(str(holdings_csv), 3500))
    risk_ladder_csv = inputs_cfg.get("risk_ladder_csv")
    if risk_ladder_csv:
        header_lines.append("Risk ladder CSV (uploaded preview):\n" + short(str(risk_ladder_csv), 3500))
    news_context = inputs_cfg.get("news_context")
    if news_context:
        header_lines.append("Latest news drivers:\n" + str(news_context).strip())
    header_block = "\n".join([line for line in header_lines if line])

    instructions = textwrap.dedent(f"""\
        Task:
        Propose and DEFEND roughly ten distinct 6-month scenarios (target 9–11) with quantitative shocks and probabilities that ~sum to 1. Anchor every scenario on the forecast date {horizon_date.isoformat()} (6 months from today) and state that date explicitly in your output.
        Use finance-consistent channels: Rates (bps), Curve (bull/bear & steep/flat), Credit OAS (bps), MBS basis (bps),
        Deposits/runoff (%), Reg changes (brief text).
        Every round, probabilities across the array must sum to 1.0 (normalize before sending).

        Respond in TWO parts every time:
        (1) Reasoning: critique, assumptions, and why your shocks/probabilities make sense (NO JSON here).
        (2) Revised JSON: a STRICT JSON array matching the schema. DO NOT use backticks. No extra prose.

        Schema (top-level keys for each scenario):
        ["Scenario","Description","Probability","Rationale","ImpactChannels","Shocks","MetricsDelta","TradeList","Assumptions","Signals"]

        EVERY element must include ALL schema keys with realistic values. Missing fields = invalid output.
        Be specific: quantify shocks (bps, %, $bn), describe deposit behavior, and list concrete trades/liquidity actions. Spell out dated milestones or key markers to watch between now and {horizon_date.isoformat()} (e.g., policy meetings, large bill paydowns, earnings, big roll dates) and make event descriptions concrete.
        Include a Signals array per scenario with 3–5 specific "watch for X/Y" items (dated releases/meetings/auctions with levels or thresholds) so the matrix clearly shows what to monitor as the scenario materializes.
    """)

    seed_user = f"{header_block}\n\n{instructions}"

    hist: List[Dict[str, str]] = []

    judge_template = cfg["prompts"].get("system_judge", "")
    judge_constraints = cfg.get("inputs", {}).get("constraints", {})
    judge_override = bool(runtime_cfg.get("judge_prompt_override"))
    if judge_override:
        judge_sys = judge_template
    else:
        try:
            judge_sys = judge_template.format(**judge_constraints)
        except Exception as exc:
            logging.warning(
                f"Judge prompt formatting failed ({type(exc).__name__}); using raw template."
            )
            judge_sys = judge_template
    runtime_cfg.setdefault("judge_prompt_effective", judge_sys)
    judge_user = (
        "From the above A/B reasoning and JSON proposals, produce a FINAL merged JSON array of scenarios "
        "that EXACTLY matches the schema. Deliver 9–11 distinct scenarios (target 10) with probabilities summing to ~1 across the set. "
        "Output RAW JSON only (no markdown, no backticks, no labels)."
    )
    def emit_stage(label: str, content: str) -> None:
        pretty_label = label
        upper = label.upper()
        if upper.startswith("R") and "-" in upper:
            round_part, suffix = upper.split("-", 1)
            role = "PROPONENT" if suffix == "A" else "DEVIL" if suffix == "B" else suffix
            pretty_label = f"{round_part}-{role}"
        elif upper == "JUDGE":
            pretty_label = "JUDGE"
        tag = f"[STAGE RUN#{run_idx + 1} {pretty_label}]"
        print(tag)
        print((content or "").strip())
        print("[/STAGE]")
        sys.stdout.flush()
    for r in range(rounds):
        # ----- A speaks -----
        round_tag = f"R{r + 1}-A"
        if r == 0:
            promptA = seed_user
        else:
            promptA = textwrap.dedent("""\
                Critique the Devil's advocate's last JSON in words first (highlight precise numeric deltas vs. their prior round proposal).
                Reference the previous round's debate when explaining what you kept, modified, or rejected.
                Rebalance probabilities so the set sums to 1.0 before you emit JSON.
                Then produce:
                Revised JSON: <STRICT JSON array per schema, no backticks, no prose after>
            """).strip()
        mA = make_messages(sysA, promptA, hist)
        outA = chat(
            model=deb_models[0],
            messages=mA,
            temperature=cfg["debate"]["debater_temperature"],
            top_p=cfg["debate"]["top_p"],
            max_tokens=cfg["debate"]["max_tokens"],
            run_tag=run_tag, round_tag=round_tag
        )
        reaA, jsonA = split_reasoning_json(outA)
        # If model ignored two-phase, fall back to extracting any JSON from entire output
        if not jsonA:
            jsonA = extract_json_block(outA) or outA
        emit_stage(round_tag, outA)
        transcript.append({
            "speaker": "Proponent",
            "round": r + 1,
            "reasoning": reaA,
            "json": extract_json_block(jsonA) or jsonA,
            "raw": outA
        })
        hist.append({"role": "assistant", "content": normalize_two_phase(reaA, jsonA)})

        if save_wip:
            pA = os.path.join(artifacts_dir, f"{run_tag}_{round_tag}.txt")
            with open(pA, "w", encoding="utf-8") as f:
                f.write(outA)

        # ----- B responds -----
        round_tag = f"R{r + 1}-B"
        promptB = textwrap.dedent("""\
            Critique the Proponent's position in words first (focus on macro/flows, funding, basis, convexity). Never refer to them as "A" or "B".
            React to the Proponent's latest JSON and spell out which elements you are embracing vs. changing, with precise numbers, relative to the prior round.
            Rebalance probabilities so the set sums to 1.0 before you emit JSON.
            Then produce:
            Revised JSON: <STRICT JSON array per schema, no backticks, no prose after>
        """).strip()
        mB = make_messages(sysB, promptB, hist)
        outB = chat(
            model=deb_models[1],
            messages=mB,
            temperature=cfg["debate"]["debater_temperature"],
            top_p=cfg["debate"]["top_p"],
            max_tokens=cfg["debate"]["max_tokens"],
            run_tag=run_tag, round_tag=round_tag
        )
        reaB, jsonB = split_reasoning_json(outB)
        if not jsonB:
            jsonB = extract_json_block(outB) or outB
        emit_stage(round_tag, outB)
        transcript.append({
            "speaker": "Devil's advocate",
            "round": r + 1,
            "reasoning": reaB,
            "json": extract_json_block(jsonB) or jsonB,
            "raw": outB
        })
        hist.append({"role": "assistant", "content": normalize_two_phase(reaB, jsonB)})

        if save_wip:
            pB = os.path.join(artifacts_dir, f"{run_tag}_{round_tag}.txt")
            with open(pB, "w", encoding="utf-8") as f:
                f.write(outB)

    logging.info(f"[{run_tag}] Invoking judge model={cfg['debate']['judge_model']} (final)")
    judge_out = chat(
        model=cfg["debate"]["judge_model"],
        messages=make_messages(judge_sys, judge_user, hist),
        temperature=cfg["debate"]["judge_temperature"],
        top_p=1.0,
        max_tokens=int(cfg["debate"].get("judge_max_tokens", 10000)),
        run_tag=run_tag,
        round_tag="JUDGE"
    )
    emit_stage("JUDGE", judge_out)

    judge_json_for_tx = extract_json_block(judge_out) or ""
    transcript.append({
        "speaker": "JUDGE",
        "round": 0,
        "reasoning": "",
        "json": judge_json_for_tx,
        "raw": judge_out
    })

    if save_wip:
        raw_path = os.path.join(artifacts_dir, f"judge_raw_run_{run_idx + 1}.txt")
        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(judge_out)
        logging.info(f"[{run_tag}] Wrote raw judge output to {raw_path}")

    # Always write a human-readable + machine-parsable transcript per run
    try:
        write_transcript(artifacts_dir, run_idx, transcript)
        logging.info(f"[{run_tag}] Wrote transcript to {os.path.join(artifacts_dir, f'transcript_run_{run_idx + 1}.{{jsonl,md}}')}")
    except Exception as e:
        logging.warning(f"[{run_tag}] Failed to write transcript: {type(e).__name__}: {e}")

    # Try parse JSON array
    try:
        data = loads_relaxed(judge_out)
        if isinstance(data, dict):
            data = [data]
    except Exception as e:
        logging.error(f"[{run_tag}] JSON parse error on judge output: {type(e).__name__}: {e}")
        data = []

    # Validate schema minimally
    for i, obj in enumerate(data):
        miss = validate_schema_one(obj)
        if miss:
            logging.warning(f"[{run_tag}] Scenario[{i}] missing keys: {miss}")

    # Save intermediate per run
    tmp_path = os.path.join(artifacts_dir, f"tmp_run_{run_idx + 1}.json")
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logging.info(f"[{run_tag}] Saved intermediate results to {tmp_path} (count={len(data)})")

    return data

# =========================================================
# Aggregation
# =========================================================

def median_prob(p_list: List[float]) -> float:
    return statistics.median(p_list) if p_list else 0.0

def aggregate(runs_outputs: List[List[Dict[str, Any]]], keep_k: int = 10) -> List[Dict[str, Any]]:
    # naive dedupe by Scenario text prefix
    pool: Dict[str, List[Dict[str, Any]]] = {}
    for arr in runs_outputs:
        for sc in arr:
            key = (sc.get("Scenario", "") or "")[:160].lower()
            pool.setdefault(key, []).append(sc)
    merged: List[Dict[str, Any]] = []
    for key, items in pool.items():
        one = copy.deepcopy(items[0])
        probs = [it.get("Probability", 0) for it in items if isinstance(it.get("Probability", 0), (int, float))]
        one["Probability"] = round(float(median_prob(probs)), 4)
        merged.append(one)
    merged.sort(key=lambda x: x.get("Probability", 0), reverse=True)
    return merged[:keep_k]

def run_offline_sample(sample_dir: str, dest_dir: str, out_path: str, output_format: str) -> List[Dict[str, Any]]:
    logging.info(f"Offline mode enabled. Loading sample from {sample_dir}")
    scenarios_path_json = os.path.join(sample_dir, "scenarios.json")
    scenarios_path_jsonl = os.path.join(sample_dir, "scenarios.jsonl")
    scenarios: List[Dict[str, Any]] = []
    if os.path.exists(scenarios_path_json):
        with open(scenarios_path_json, "r", encoding="utf-8") as f:
            scenarios = json.load(f)
    elif os.path.exists(scenarios_path_jsonl):
        with open(scenarios_path_jsonl, "r", encoding="utf-8") as f:
            scenarios = [json.loads(line) for line in f if line.strip()]
    else:
        raise FileNotFoundError(f"No scenarios.json or scenarios.jsonl found in {sample_dir}")

    if not isinstance(scenarios, list):
        raise ValueError("Sample scenarios file must contain a JSON array.")

    os.makedirs(dest_dir, exist_ok=True)

    # Copy transcript and artifact files if present
    for name in os.listdir(sample_dir):
        if any(name.startswith(prefix) for prefix in ["transcript_run_", "tmp_run_", "judge_raw_run_"]):
            src = os.path.join(sample_dir, name)
            dst = os.path.join(dest_dir, name)
            shutil.copy2(src, dst)

    # Write scenario outputs to requested format
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if output_format == "json":
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(scenarios, f, ensure_ascii=False, indent=2)
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            for row in scenarios:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    final_copy_path = os.path.join(dest_dir, "scenarios_final.json")
    with open(final_copy_path, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)

    logging.info(f"Offline sample copied to {dest_dir}")
    return scenarios

# =========================================================
# Main
# =========================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--format", choices=["jsonl", "json"], default="jsonl",
                        help="jsonl = one scenario per line; json = single JSON array")
    parser.add_argument("--logdir", default="logs")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--save-wip", action="store_true",
                        help="If set, save per-run judge_raw_*.txt and tmp_run_*.json artifacts")
    parser.add_argument("--offline-sample", default=None,
                        help="Path to a folder containing sample scenarios/transcripts for offline testing.")
    args = parser.parse_args()

    setup_logging(args.logdir, args.verbose)
    logging.info("Starting HQLA MAD Scenario Generator (max-debug rewrite).")
    client_init()

    # Load config
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.rounds:
        cfg["debate"]["rounds"] = args.rounds

    env_rounds = os.getenv("MAD_DEBATE_ROUNDS")
    if env_rounds:
        try:
            cfg["debate"]["rounds"] = int(env_rounds)
            logging.info(f"Override rounds via MAD_DEBATE_ROUNDS={env_rounds}")
        except ValueError:
            logging.warning(f"Ignoring invalid MAD_DEBATE_ROUNDS={env_rounds!r}")

    prompts_cfg = cfg.setdefault("prompts", {})
    runtime_cfg = cfg.setdefault("_runtime", {})
    runtime_cfg["judge_prompt_override"] = False
    env_prompt_a = os.getenv("MAD_PROMPT_DEBATER_A")
    if env_prompt_a:
        prompts_cfg["system_debater_a"] = env_prompt_a
        logging.info("Override debater A prompt via MAD_PROMPT_DEBATER_A")
    env_prompt_b = os.getenv("MAD_PROMPT_DEBATER_B")
    if env_prompt_b:
        prompts_cfg["system_debater_b"] = env_prompt_b
        logging.info("Override debater B prompt via MAD_PROMPT_DEBATER_B")
    env_judge = os.getenv("MAD_PROMPT_JUDGE")
    if env_judge:
        prompts_cfg["system_judge"] = env_judge
        logging.info("Override judge prompt via MAD_PROMPT_JUDGE")
        runtime_cfg["judge_prompt_override"] = True

    inputs_cfg = cfg.setdefault("inputs", {})
    env_portfolio = os.getenv("MAD_PORTFOLIO_NAME")
    if env_portfolio:
        inputs_cfg["portfolio_name"] = env_portfolio
        logging.info("Override portfolio name via MAD_PORTFOLIO_NAME")
    env_shock_yaml = os.getenv("MAD_SHOCK_YAML")
    if env_shock_yaml:
        inputs_cfg["shock_yaml"] = env_shock_yaml
        logging.info("Attach user shock YAML via MAD_SHOCK_YAML")
    env_holdings_csv = os.getenv("MAD_HOLDINGS_CSV")
    if env_holdings_csv:
        inputs_cfg["holdings_csv"] = env_holdings_csv
        logging.info("Attach holdings CSV via MAD_HOLDINGS_CSV")
    env_risk_csv = os.getenv("MAD_RISK_LADDER_CSV")
    if env_risk_csv:
        inputs_cfg["risk_ladder_csv"] = env_risk_csv
        logging.info("Attach risk ladder CSV via MAD_RISK_LADDER_CSV")
    env_news_context = os.getenv("MAD_NEWS_CONTEXT")
    if env_news_context:
        inputs_cfg["news_context"] = env_news_context
        logging.info("Inject news context via MAD_NEWS_CONTEXT")

    run_timestamp = time.strftime("%Y%m%d_%H%M%S")
    artifacts_root = os.path.join("data", "scenarios")
    runs_root = os.path.join(artifacts_root, "runs")
    os.makedirs(runs_root, exist_ok=True)
    current_run_dir = os.path.join(runs_root, run_timestamp)
    os.makedirs(current_run_dir, exist_ok=True)
    runtime_cfg["run_timestamp"] = run_timestamp
    runtime_cfg["run_dir"] = current_run_dir

    runs = args.runs or cfg["debate"]["runs"]
    out_path = args.out or cfg["output"]["path"]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    offline_sample_dir = args.offline_sample or os.getenv("MAD_OFFLINE_SAMPLE_DIR")

    # Show model/params summary
    logging.info(f"Debaters: {cfg['debate']['debater_models']} | Judge: {cfg['debate']['judge_model']}")
    logging.info(f"Rounds={cfg['debate']['rounds']} Runs={runs} "
                 f"Temp(deb)={cfg['debate']['debater_temperature']} Temp(judge)={cfg['debate']['judge_temperature']} "
                 f"Top_p={cfg['debate']['top_p']} MaxTokens(deb)={cfg['debate']['max_tokens']} "
                 f"JudgeMaxTokens={cfg['debate'].get('judge_max_tokens', 2000)}")

    artifacts_dir = current_run_dir
    all_runs: List[List[Dict[str, Any]]] = []
    final: List[Dict[str, Any]] = []
    offline_mode = bool(offline_sample_dir)

    try:
        if offline_mode:
            final = run_offline_sample(offline_sample_dir, artifacts_dir, out_path, args.format)
        else:
            for i in range(runs):
                logging.info(f"[RUN#{i + 1}/{runs}] starting debate...")
                try:
                    one = debate_once(cfg, i, artifacts_dir=artifacts_dir, save_wip=args.save_wip)
                    all_runs.append(one)
                    logging.info(f"[RUN#{i + 1}] finished; scenarios={len(one)}")
                except KeyboardInterrupt:
                    logging.error(f"[RUN#{i + 1}] Interrupted by user.")
                    break
                except Exception as e:
                    logging.error(f"[RUN#{i + 1}] FAILED with error: {type(e).__name__}: {e}")
                    logging.debug(traceback.format_exc())

            final = aggregate(all_runs, keep_k=cfg["aggregation"]["keep_top_k"])

        # Write final
        if not offline_mode:
            if args.format == "json":
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(final, f, ensure_ascii=False, indent=2)
            else:  # jsonl
                with open(out_path, "w", encoding="utf-8") as f:
                    for row in final:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")

            logging.info(f"Wrote {len(final)} aggregated scenarios to {out_path}")
            try:
                final_copy_path = os.path.join(current_run_dir, "scenarios_final.json")
                with open(final_copy_path, "w", encoding="utf-8") as f:
                    json.dump(final, f, ensure_ascii=False, indent=2)
                logging.info(f"Wrote run-local scenario copy to {final_copy_path}")
            except Exception as exc:
                logging.warning(f"Failed to write run-local scenario copy: {type(exc).__name__}: {exc}")

        completed_runs = len(all_runs) if not offline_mode else runs

        metadata = {
            "run_timestamp": run_timestamp,
            "run_directory": os.path.abspath(current_run_dir),
            "config_file": os.path.abspath(args.config),
            "runs_requested": runs,
            "runs_completed": completed_runs,
            "rounds_per_run": cfg["debate"]["rounds"],
            "portfolio_name": inputs_cfg.get("portfolio_name"),
        "shock_yaml": inputs_cfg.get("shock_yaml"),
        "news_context": inputs_cfg.get("news_context"),
        "output_path": os.path.abspath(out_path),
        "offline_sample_dir": offline_sample_dir,
            "prompts": {
                "debater_a": runtime_cfg.get("debater_prompt_a_effective") or prompts_cfg.get("system_debater") or "",
                "debater_b": runtime_cfg.get("debater_prompt_b_effective") or prompts_cfg.get("system_debater") or "",
                "judge": runtime_cfg.get("judge_prompt_effective") or prompts_cfg.get("system_judge") or "",
            },
        }
        metadata_path = os.path.join(current_run_dir, "metadata.json")
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logging.info(f"Wrote run metadata to {metadata_path}")
        except Exception as exc:
            logging.warning(f"Failed to write run metadata: {type(exc).__name__}: {exc}")

        latest_marker = os.path.join(runs_root, "latest.txt")
        try:
            with open(latest_marker, "w", encoding="utf-8") as f:
                f.write(run_timestamp)
        except Exception as exc:
            logging.warning(f"Failed to update latest run marker: {type(exc).__name__}: {exc}")

    finally:
        logging.info("Done.")

if __name__ == "__main__":
    main()
