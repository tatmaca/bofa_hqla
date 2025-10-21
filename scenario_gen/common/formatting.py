import pandas as pd
from typing import List
from .scenario import Scenario

def scenarios_to_matrix(scenarios: List[Scenario]) -> pd.DataFrame:
    rows = [s.to_matrix_row() for s in scenarios]
    return pd.DataFrame(rows, columns=["Scenario","Description","Probability","Rationale","Impact Channels"])