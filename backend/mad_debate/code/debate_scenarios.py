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

import os, sys, json, argparse, copy, statistics, time, random, traceback, logging, textwrap, re
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
         max_tokens: int = 2000,
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
    sysA = cfg["prompts"]["system_debater"]
    sysB = cfg["prompts"]["system_debater"]
    run_tag = f"RUN#{run_idx + 1}"

    transcript: List[Dict[str, Any]] = []

    seed_user = textwrap.dedent(f"""\
        Portfolio: {cfg['inputs']['portfolio_snapshot']}
        Constraints: {cfg['inputs']['constraints']}
        Indicators: {cfg['inputs']['indicators']}
        Priors: {cfg['inputs']['priors']}

        Task:
        Propose and DEFEND 3–5 distinct 6-month scenarios with quantitative shocks and probabilities that ~sum to 1.
        Use finance-consistent channels: {{Rates (bps), Curve (bull/bear & steep/flat), Credit OAS (bps), MBS basis (bps),
        Deposits/runoff (%), Reg changes (brief text)}}.

        Respond in TWO parts every time:
        (1) Reasoning: critique, assumptions, and why your shocks/probabilities make sense (NO JSON here).
        (2) Revised JSON: a STRICT JSON array matching the schema. DO NOT use backticks. No extra prose.

        Schema (top-level keys for each scenario):
        ["Scenario","Description","Probability","Rationale","ImpactChannels","Shocks","MetricsDelta","TradeList","Assumptions"]
    """)

    hist: List[Dict[str, str]] = []
    for r in range(rounds):
        # ----- A speaks -----
        round_tag = f"R{r + 1}-A"
        promptA = seed_user if r == 0 else textwrap.dedent("""\
            Critique B's last JSON in words first (no numbers can be hand-wavy; be precise).
            Then produce: 
            Revised JSON: <STRICT JSON array per schema, no backticks, no prose after>
        """)
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
        transcript.append({
            "speaker": "A",
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
            Critique A's position in words first (focus on macro/flows, funding, basis, convexity).
            Then produce:
            Revised JSON: <STRICT JSON array per schema, no backticks, no prose after>
        """)
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
        transcript.append({
            "speaker": "B",
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

    # Judge merges/selects
    judge_sys = cfg["prompts"]["system_judge"].format(**cfg["inputs"]["constraints"])
    judge_user = (
        "From the above A/B reasoning and JSON proposals, produce a FINAL merged JSON array of scenarios "
        "that EXACTLY matches the schema. Reject duplicates; ensure probabilities sum to ~1 across the set. "
        "Output RAW JSON only (no markdown, no backticks, no labels)."
    )
    logging.info(f"[{run_tag}] Invoking judge model={cfg['debate']['judge_model']}")
    judge_out = chat(
        model=cfg["debate"]["judge_model"],
        messages=make_messages(judge_sys, judge_user, hist),
        temperature=cfg["debate"]["judge_temperature"],
        top_p=1.0,
        max_tokens=int(cfg["debate"].get("judge_max_tokens", 2000)),
        run_tag=run_tag, round_tag="JUDGE"
    )

    # For transcript: attempt to extract JSON block for judge as well
    judge_json_for_tx = extract_json_block(judge_out) or ""
    transcript.append({
        "speaker": "JUDGE",
        "round": 0,
        "reasoning": "",  # judge shouldn't add prose; keep empty
        "json": judge_json_for_tx,
        "raw": judge_out
    })

    # Save judge raw (always, for auditability)
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
    args = parser.parse_args()

    setup_logging(args.logdir, args.verbose)
    logging.info("Starting HQLA MAD Scenario Generator (max-debug rewrite).")
    client_init()

    # Load config
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.rounds:
        cfg["debate"]["rounds"] = args.rounds

    runs = args.runs or cfg["debate"]["runs"]
    out_path = args.out or cfg["output"]["path"]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Show model/params summary
    logging.info(f"Debaters: {cfg['debate']['debater_models']} | Judge: {cfg['debate']['judge_model']}")
    logging.info(f"Rounds={cfg['debate']['rounds']} Runs={runs} "
                 f"Temp(deb)={cfg['debate']['debater_temperature']} Temp(judge)={cfg['debate']['judge_temperature']} "
                 f"Top_p={cfg['debate']['top_p']} MaxTokens(deb)={cfg['debate']['max_tokens']} "
                 f"JudgeMaxTokens={cfg['debate'].get('judge_max_tokens', 2000)}")

    artifacts_dir = os.path.join("data", "scenarios")
    all_runs: List[List[Dict[str, Any]]] = []

    try:
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
        if args.format == "json":
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(final, f, ensure_ascii=False, indent=2)
        else:  # jsonl
            with open(out_path, "w", encoding="utf-8") as f:
                for row in final:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

        logging.info(f"Wrote {len(final)} aggregated scenarios to {out_path}")

    finally:
        logging.info("Done.")

if __name__ == "__main__":
    main()