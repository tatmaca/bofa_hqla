-- Schema updates for enhanced yield curve prediction system
-- Run this to update existing database

-- 1. Add market close time tracking to yield_curve_daily
-- Note: ALTER TABLE will fail if columns already exist - that's OK
ALTER TABLE yield_curve_daily ADD COLUMN market_close_time TEXT;
ALTER TABLE yield_curve_daily ADD COLUMN snapshot_time TEXT;

-- 2. Expert attribution table: stores expert opinions on which news contributed to yield changes
CREATE TABLE IF NOT EXISTS expert_attributions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  article_id INTEGER,
  article_url TEXT,
  attribution_text TEXT,
  source TEXT,
  extracted_at TEXT,
  confidence REAL,
  created_at TEXT,
  FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE INDEX IF NOT EXISTS idx_expert_attrib_date ON expert_attributions(date);
CREATE INDEX IF NOT EXISTS idx_expert_attrib_article ON expert_attributions(article_id);
CREATE INDEX IF NOT EXISTS idx_expert_attrib_url ON expert_attributions(article_url);

-- 3. Article-level impact weights: learned weights for each article's impact on yields
CREATE TABLE IF NOT EXISTS article_yield_impact_weights (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  target TEXT NOT NULL,
  weight REAL,
  model_name TEXT,
  created_at TEXT,
  FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE INDEX IF NOT EXISTS idx_article_weights_date ON article_yield_impact_weights(date);
CREATE INDEX IF NOT EXISTS idx_article_weights_article ON article_yield_impact_weights(article_id);
CREATE INDEX IF NOT EXISTS idx_article_weights_target ON article_yield_impact_weights(target);

-- 4. Time series lag features: track news from t-n affecting yields at t
CREATE TABLE IF NOT EXISTS news_yield_training_lagged (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  lag_days INTEGER NOT NULL,
  bucket TEXT NOT NULL,
  bucket_count INTEGER,
  bucket_weight REAL,
  delta_2y REAL,
  delta_5y REAL,
  delta_10y REAL,
  delta_30y REAL,
  delta_2s10s REAL,
  delta_2s30s REAL,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_training_lagged_date ON news_yield_training_lagged(date);
CREATE INDEX IF NOT EXISTS idx_training_lagged_lag ON news_yield_training_lagged(lag_days);

-- 5. Add published_at timestamp index for look-ahead bias prevention
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);

