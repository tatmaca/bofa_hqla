#!/usr/bin/env python3
"""
Setup script for ONYL (Linear Online Learning) implementation.
Applies database schema and verifies configuration.
"""

import os
import sys
import sqlite3
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn

def apply_schema():
    """Apply database schema for factors and linear model."""
    print("=" * 70)
    print("Applying ONYL Database Schema")
    print("=" * 70)
    
    schema_path = Path(__file__).parent / "schema_factors.sql"
    if not schema_path.exists():
        print(f"[ERROR] Schema file not found: {schema_path}")
        return False
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        with open(schema_path) as f:
            schema_sql = f.read()
        
        c.executescript(schema_sql)
        conn.commit()
        print("[OK] Schema applied successfully")
        
        # Verify tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        
        required_tables = [
            "article_factors",
            "daily_factor_scores",
            "linear_model_coefficients",
            "linear_model_intercepts",
            "linear_model_predictions"
        ]
        
        print("\nTable verification:")
        for table in required_tables:
            if table in tables:
                count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  ✅ {table}: exists ({count} rows)")
            else:
                print(f"  ❌ {table}: not found")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to apply schema: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def verify_config():
    """Verify cold-start coefficients are in config."""
    print("\n" + "=" * 70)
    print("Verifying Configuration")
    print("=" * 70)
    
    config_path = Path(__file__).parent / "news_config.yaml"
    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        return False
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    cold_start = config.get("linear_model_cold_start", {})
    
    if not cold_start:
        print("[ERROR] linear_model_cold_start section not found in config")
        return False
    
    # Check for key factors
    key_factors = ["FED_TONE", "INFLATION_NEWS", "SUPPLY_LONG", "RISK_REGIME"]
    found_factors = [f for f in key_factors if f in cold_start]
    
    print(f"\nCold-start coefficients:")
    print(f"  Found {len(cold_start)} factors")
    print(f"  Key factors present: {len(found_factors)}/{len(key_factors)}")
    
    # Check hyperparameters
    hyperparams = ["learning_rate", "forgetting_factor", "max_daily_coef_change", "smoothing_gamma"]
    found_hyperparams = [h for h in hyperparams if h in cold_start]
    
    print(f"  Hyperparameters: {len(found_hyperparams)}/{len(hyperparams)}")
    
    if len(found_factors) == len(key_factors) and len(found_hyperparams) == len(hyperparams):
        print("[OK] Configuration verified")
        return True
    else:
        print("[WARN] Some configuration missing")
        return False

def main():
    print("\n" + "=" * 70)
    print("ONYL Setup Script")
    print("=" * 70)
    
    # Apply schema
    schema_ok = apply_schema()
    
    # Verify config
    config_ok = verify_config()
    
    print("\n" + "=" * 70)
    print("Setup Summary")
    print("=" * 70)
    
    if schema_ok and config_ok:
        print("✅ Setup complete!")
        print("\nNext steps:")
        print("1. Extract factors for historical articles:")
        print("   python3 extract_factors_historical.py --start-date 2025-10-01 --end-date 2025-11-20 --resume")
        print("2. Train linear model for recent dates:")
        print("   python3 train_linear_online.py --date 2025-11-20")
        print("3. Compare models:")
        print("   python3 compare_models.py --date 2025-11-20")
    else:
        print("⚠️  Setup incomplete - check errors above")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

