from pathlib import Path
import json, sys
import pandas as pd
from .scenario import Scenario
from .formatting import scenarios_to_matrix

def load_json_scenarios(folder: Path):
    scenarios = []
    for p in sorted(folder.glob("*.json")):
        with open(p, "r") as f:
            d = json.load(f)
        scenarios.append(Scenario(**d))
    return scenarios

if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scenario_gen/registry/today")
    scens = load_json_scenarios(folder)
    df = scenarios_to_matrix(scens)
    print(df.to_markdown(index=False))
    df.to_csv(folder / "Scenario_Matrix.csv", index=False)