#!/usr/bin/env python3
"""
Scenario Loading Module
Loads scenarios from JSONL file for scenario-based yield curve predictions.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


def load_scenarios_from_jsonl(file_path: str) -> List[Dict]:
    """
    Load scenarios from JSONL file.
    
    Args:
        file_path: Path to JSONL file containing scenarios
    
    Returns:
        List of scenario dictionaries
    """
    scenarios = []
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Scenarios file not found: {file_path}")
    
    with open(path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                scenario = json.loads(line)
                scenarios.append(scenario)
            except json.JSONDecodeError as e:
                print(f"[WARN] Failed to parse scenario on line {line_num}: {e}")
                continue
    
    print(f"[LOAD] Loaded {len(scenarios)} scenarios from {file_path}")
    return scenarios


def get_scenario_descriptions(scenarios: List[Dict]) -> Dict[str, str]:
    """
    Extract scenario names and descriptions.
    
    Args:
        scenarios: List of scenario dictionaries
    
    Returns:
        Dictionary mapping scenario names to descriptions
    """
    descriptions = {}
    
    for scenario in scenarios:
        name = scenario.get("Scenario", "Unknown")
        description = scenario.get("Description", "")
        descriptions[name] = description
    
    return descriptions


def get_default_scenarios_path() -> Optional[Path]:
    """
    Get default path to scenarios file.
    
    Returns:
        Path to scenarios file if it exists, None otherwise
    """
    # Try relative path from project root
    repo_root = Path(__file__).resolve().parents[2]
    scenarios_path = repo_root / "backend" / "mad_debate" / "data" / "scenarios" / "out.jsonl"
    
    if scenarios_path.exists():
        return scenarios_path
    
    return None


if __name__ == "__main__":
    import argparse
    
    ap = argparse.ArgumentParser(description="Load scenarios from JSONL file")
    ap.add_argument("--scenarios-path", type=str, help="Path to scenarios JSONL file")
    args = ap.parse_args()
    
    scenarios_path = args.scenarios_path
    if not scenarios_path:
        default_path = get_default_scenarios_path()
        if default_path:
            scenarios_path = str(default_path)
        else:
            print("[ERROR] No scenarios path provided and default not found")
            exit(1)
    
    try:
        scenarios = load_scenarios_from_jsonl(scenarios_path)
        print(f"\nLoaded {len(scenarios)} scenarios:")
        for i, scenario in enumerate(scenarios, 1):
            name = scenario.get("Scenario", "Unknown")
            desc = scenario.get("Description", "")[:80]
            print(f"  {i}. {name}: {desc}...")
    except Exception as e:
        print(f"[ERROR] Failed to load scenarios: {e}")
        exit(1)

