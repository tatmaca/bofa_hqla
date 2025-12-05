#!/usr/bin/env python3
"""
Scenario Factor Extraction
Extracts economic factors from scenario descriptions using LLM.
Similar to extract_factors.py but adapted for scenario descriptions.
"""

import os
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import timezone
import datetime as dt

# Import factor extraction utilities
from extract_factors import (
    ALL_FACTORS,
    FACTOR_DESCRIPTIONS,
    get_openai_api_key,
    call_openai_with_retry,
    CONFIG_PATH
)

# Try to import OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[WARN] OpenAI not installed. Install with: pip install openai")

# Cache file for scenario factors (scenarios don't change daily)
CACHE_FILE = Path(__file__).parent / "scenario_factors_cache.json"


def extract_factors_from_scenario(client: OpenAI, scenario: Dict) -> Optional[List[Dict]]:
    """
    Uses LLM to extract economic factors from a scenario description.
    Returns list of {factor_name, intensity, confidence} dicts.
    
    Args:
        client: OpenAI client
        scenario: Scenario dictionary with "Scenario" and "Description" keys
    
    Returns:
        List of factor dictionaries or None if extraction fails
    """
    scenario_name = scenario.get("Scenario", "Unknown Scenario")
    description = scenario.get("Description", "")
    
    if not description:
        return None
    
    # Build factor list for prompt
    factor_list = "\n".join([f"- {f}: {FACTOR_DESCRIPTIONS.get(f, '')}" for f in ALL_FACTORS])
    
    prompt = f"""You are an expert fixed income strategist. Analyze this hypothetical economic scenario and identify which economic factors would be present and their intensity.

This is a SCENARIO - a hypothetical future event that may occur. Treat it as if it were major news that will definitely happen.

Available factors:
{factor_list}

For each factor that would be present in this scenario:
- intensity: Real number from -2.0 to +2.0 indicating direction and strength
  - Positive: factor increases yields (e.g., hawkish Fed, strong inflation)
  - Negative: factor decreases yields (e.g., dovish Fed, risk-off)
  - Magnitude: 0.5 (weak), 1.0 (moderate), 1.5 (strong), 2.0 (very strong)
  - For major scenarios, use higher intensities (1.5-2.0)
- confidence: Real number from 0.0 to 1.0 indicating how confident you are this factor is present
  - 0.9-1.0: Explicitly mentioned or very clear
  - 0.7-0.9: Strongly implied
  - 0.5-0.7: Moderately implied
  - 0.3-0.5: Weakly implied
  - 0.0-0.3: Very uncertain

Scenario: {scenario_name}
Description: {description}

Respond with ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
    "factors": [
        {{
            "factor_name": "FED_TONE",
            "intensity": 1.5,
            "confidence": 0.9,
            "reasoning": "Brief explanation"
        }},
        // ... more factors if present
    ]
}}

If no factors are present, return: {{"factors": []}}
"""

    messages = [
        {
            "role": "system",
            "content": "You are an expert fixed income strategist specializing in U.S. Treasury markets. Analyze scenarios and identify economic factors accurately. Always respond with valid JSON only, no markdown."
        },
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = call_openai_with_retry(
            client,
            messages,
            model="gpt-4o",
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        if not response:
            return None
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON directly first
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # If direct parse fails, try to extract JSON from markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            result = json.loads(result_text)
        
        factors = result.get("factors", [])
        
        # Validate factors
        validated_factors = []
        for factor in factors:
            factor_name = factor.get("factor_name")
            intensity = factor.get("intensity", 0.0)
            confidence = factor.get("confidence", 0.0)
            
            if factor_name in ALL_FACTORS:
                # Clamp intensity and confidence to valid ranges
                intensity = max(-2.0, min(2.0, float(intensity)))
                confidence = max(0.0, min(1.0, float(confidence)))
                
                validated_factors.append({
                    "factor_name": factor_name,
                    "intensity": intensity,
                    "confidence": confidence,
                    "reasoning": factor.get("reasoning", "")
                })
        
        return validated_factors if validated_factors else None
        
    except Exception as e:
        print(f"[WARN] Failed to extract factors from scenario '{scenario_name}': {e}")
        return None


def aggregate_scenario_factor_scores(factors: List[Dict]) -> Dict[str, float]:
    """
    Aggregate scenario factors to daily factor scores.
    Formula: factor_score = sum(c * s) clipped to [-2.5, +2.5]
    
    Args:
        factors: List of {factor_name, intensity, confidence} dicts
    
    Returns:
        Dictionary mapping factor names to aggregated scores
    """
    factor_scores = {}
    
    for factor in factors:
        factor_name = factor["factor_name"]
        intensity = factor["intensity"]
        confidence = factor["confidence"]
        
        # Calculate contribution: c * s
        contribution = confidence * intensity
        
        if factor_name not in factor_scores:
            factor_scores[factor_name] = 0.0
        
        factor_scores[factor_name] += contribution
    
    # Clip to [-2.5, +2.5]
    for factor_name in factor_scores:
        factor_scores[factor_name] = max(-2.5, min(2.5, factor_scores[factor_name]))
    
    return factor_scores


def load_scenario_factors_cache() -> Dict[str, Dict[str, float]]:
    """
    Load cached scenario factors from file.
    
    Returns:
        Dictionary mapping scenario names to factor scores
    """
    if not CACHE_FILE.exists():
        return {}
    
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        return cache
    except Exception as e:
        print(f"[WARN] Failed to load scenario factors cache: {e}")
        return {}


def save_scenario_factors_cache(cache: Dict[str, Dict[str, float]]):
    """
    Save scenario factors to cache file.
    
    Args:
        cache: Dictionary mapping scenario names to factor scores
    """
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to save scenario factors cache: {e}")


def extract_factors_for_scenarios(scenarios: List[Dict], 
                                  api_key: Optional[str] = None,
                                  use_cache: bool = True) -> Dict[str, Dict[str, float]]:
    """
    Extract factors for all scenarios.
    
    Args:
        scenarios: List of scenario dictionaries
        api_key: OpenAI API key (if None, loads from config)
        use_cache: Whether to use cached factors if available
    
    Returns:
        Dictionary mapping scenario names to factor scores
    """
    if not HAS_OPENAI:
        print("[ERROR] OpenAI not available. Cannot extract scenario factors.")
        return {}
    
    # Load cache
    cache = load_scenario_factors_cache() if use_cache else {}
    
    # Initialize OpenAI client
    if not api_key:
        api_key = get_openai_api_key()
    
    if not api_key:
        print("[ERROR] No OpenAI API key found")
        return {}
    
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"[ERROR] Failed to initialize OpenAI client: {e}")
        return {}
    
    scenario_factors = {}
    updated_cache = {}
    
    for scenario in scenarios:
        scenario_name = scenario.get("Scenario", "Unknown")
        
        # Check cache first
        if use_cache and scenario_name in cache:
            scenario_factors[scenario_name] = cache[scenario_name]
            updated_cache[scenario_name] = cache[scenario_name]
            print(f"[CACHE] Using cached factors for scenario: {scenario_name}")
            continue
        
        # Extract factors
        print(f"[EXTRACT] Extracting factors for scenario: {scenario_name}")
        factors = extract_factors_from_scenario(client, scenario)
        
        if factors:
            factor_scores = aggregate_scenario_factor_scores(factors)
            scenario_factors[scenario_name] = factor_scores
            updated_cache[scenario_name] = factor_scores
            print(f"[EXTRACT] Extracted {len(factor_scores)} factors for {scenario_name}")
        else:
            print(f"[WARN] No factors extracted for scenario: {scenario_name}")
            scenario_factors[scenario_name] = {}
            updated_cache[scenario_name] = {}
    
    # Save updated cache
    if use_cache:
        save_scenario_factors_cache(updated_cache)
    
    return scenario_factors


if __name__ == "__main__":
    import argparse
    from load_scenarios import load_scenarios_from_jsonl, get_default_scenarios_path
    
    ap = argparse.ArgumentParser(description="Extract factors from scenarios")
    ap.add_argument("--scenarios-path", type=str, help="Path to scenarios JSONL file")
    ap.add_argument("--no-cache", action="store_true", help="Don't use cached factors")
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
        scenario_factors = extract_factors_for_scenarios(scenarios, use_cache=not args.no_cache)
        
        print(f"\nExtracted factors for {len(scenario_factors)} scenarios:")
        for scenario_name, factors in scenario_factors.items():
            if factors:
                top_factors = sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
                print(f"\n  {scenario_name}:")
                for factor, score in top_factors:
                    print(f"    {factor}: {score:.2f}")
            else:
                print(f"\n  {scenario_name}: No factors extracted")
    except Exception as e:
        print(f"[ERROR] Failed to extract scenario factors: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

