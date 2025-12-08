-- Schema for prediction accuracy tracking
-- Stores accuracy metrics for baseline and scenario predictions

-- Scenario prediction accuracy: stores predictions and actuals for all scenarios
CREATE TABLE IF NOT EXISTS scenario_prediction_accuracy (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,  -- prediction date (when prediction was made, base_date)
  actual_date TEXT NOT NULL,  -- actual yield change date (prediction_date from scenario, typically date+1)
  scenario_name TEXT NOT NULL,  -- 'baseline' or scenario name
  tenor TEXT NOT NULL,
  predicted_delta_bps REAL,
  actual_delta_bps REAL,
  error_bps REAL,  -- actual - predicted
  created_at TEXT,
  UNIQUE(date, actual_date, scenario_name, tenor)
);

CREATE INDEX IF NOT EXISTS idx_scenario_acc_date ON scenario_prediction_accuracy(date);
CREATE INDEX IF NOT EXISTS idx_scenario_acc_actual_date ON scenario_prediction_accuracy(actual_date);
CREATE INDEX IF NOT EXISTS idx_scenario_acc_scenario ON scenario_prediction_accuracy(scenario_name);
CREATE INDEX IF NOT EXISTS idx_scenario_acc_tenor ON scenario_prediction_accuracy(tenor);

-- Daily accuracy summary: aggregated metrics per date and scenario
CREATE TABLE IF NOT EXISTS daily_accuracy_summary (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,  -- prediction date
  actual_date TEXT NOT NULL,  -- actual yield change date
  scenario_name TEXT NOT NULL,
  mae_bps REAL,  -- Mean Absolute Error
  rmse_bps REAL,  -- Root Mean Squared Error
  r2 REAL,  -- R-squared
  directional_accuracy REAL,  -- Percentage of correct directions
  correlation REAL,  -- Pearson correlation
  total_tenors INTEGER,  -- Number of tenors with data
  created_at TEXT,
  UNIQUE(date, actual_date, scenario_name)
);

CREATE INDEX IF NOT EXISTS idx_daily_acc_date ON daily_accuracy_summary(date);
CREATE INDEX IF NOT EXISTS idx_daily_acc_actual_date ON daily_accuracy_summary(actual_date);
CREATE INDEX IF NOT EXISTS idx_daily_acc_scenario ON daily_accuracy_summary(scenario_name);

