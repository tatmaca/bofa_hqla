-- Schema for factor extraction and linear online learning model
-- Run this to add support for ONYL (Online News→Yield Learner) algorithm

-- 1. Article-level factor scores: stores extracted factors from individual articles
CREATE TABLE IF NOT EXISTS article_factors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  factor_name TEXT NOT NULL,
  intensity REAL,  -- s ∈ [-2..2]
  confidence REAL,  -- c ∈ [0..1]
  extracted_at TEXT,
  FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE INDEX IF NOT EXISTS idx_article_factors_date ON article_factors(date);
CREATE INDEX IF NOT EXISTS idx_article_factors_factor ON article_factors(factor_name);
CREATE INDEX IF NOT EXISTS idx_article_factors_article ON article_factors(article_id);

-- 2. Daily aggregated factor scores: sum of c*s per factor per day (clipped to [-2.5, +2.5])
CREATE TABLE IF NOT EXISTS daily_factor_scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  factor_name TEXT NOT NULL,
  factor_score REAL,  -- aggregated score (sum of c*s, clipped)
  total_articles INTEGER,  -- number of articles contributing to this factor
  created_at TEXT,
  UNIQUE(date, factor_name)
);

CREATE INDEX IF NOT EXISTS idx_daily_factors_date ON daily_factor_scores(date);
CREATE INDEX IF NOT EXISTS idx_daily_factors_factor ON daily_factor_scores(factor_name);

-- 3. Linear model coefficients: stores B_k,f (coefficient for tenor k, factor f) updated daily
CREATE TABLE IF NOT EXISTS linear_model_coefficients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  tenor TEXT NOT NULL,  -- '3M', '2Y', '5Y', '10Y', '30Y'
  factor_name TEXT NOT NULL,
  coefficient_bps REAL,  -- B_k,f in bps per unit factor
  updated_at TEXT,
  UNIQUE(date, tenor, factor_name)
);

CREATE INDEX IF NOT EXISTS idx_linear_coef_date ON linear_model_coefficients(date);
CREATE INDEX IF NOT EXISTS idx_linear_coef_tenor ON linear_model_coefficients(tenor);
CREATE INDEX IF NOT EXISTS idx_linear_coef_factor ON linear_model_coefficients(factor_name);

-- 4. Linear model predictions: stores predictions and errors for evaluation
CREATE TABLE IF NOT EXISTS linear_model_predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  tenor TEXT NOT NULL,  -- '3M', '2Y', '5Y', '10Y', '30Y'
  predicted_delta_bps REAL,
  actual_delta_bps REAL,
  error_bps REAL,  -- actual - predicted
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_linear_pred_date ON linear_model_predictions(date);
CREATE INDEX IF NOT EXISTS idx_linear_pred_tenor ON linear_model_predictions(tenor);

-- 5. Linear model intercepts (bias terms): b_k per tenor
CREATE TABLE IF NOT EXISTS linear_model_intercepts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  tenor TEXT NOT NULL,
  intercept_bps REAL,
  updated_at TEXT,
  UNIQUE(date, tenor)
);

CREATE INDEX IF NOT EXISTS idx_linear_intercept_date ON linear_model_intercepts(date);
CREATE INDEX IF NOT EXISTS idx_linear_intercept_tenor ON linear_model_intercepts(tenor);

