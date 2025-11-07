CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE,
  source TEXT,
  published_at TEXT,
  fetched_at TEXT,
  title TEXT,
  author TEXT,
  summary TEXT,
  text TEXT,
  content_hash TEXT,
  status TEXT,
  bucket TEXT,
  bucket_confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_bucket ON articles(bucket);
CREATE INDEX IF NOT EXISTS idx_articles_fetched ON articles(fetched_at);

-- Track daily ingestion runs
CREATE TABLE IF NOT EXISTS ingestion_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_date TEXT UNIQUE,
  started_at TEXT,
  completed_at TEXT,
  rss_processed INTEGER DEFAULT 0,
  rss_skipped INTEGER DEFAULT 0,
  crawl_processed INTEGER DEFAULT 0,
  crawl_skipped INTEGER DEFAULT 0,
  total_new_articles INTEGER DEFAULT 0,
  status TEXT,
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_runs_date ON ingestion_runs(run_date);

-- Track yield curve changes for ML training
CREATE TABLE IF NOT EXISTS yield_curve_daily (
  date TEXT PRIMARY KEY,
  zeros_pct TEXT,  -- JSON string of {tenor: yield}
  spreads_pct TEXT,  -- JSON string of {spread_name: value}
  delta_zeros_pct TEXT,  -- JSON string of day-over-day changes
  delta_spreads_pct TEXT,
  snapshot_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_yield_curve_date ON yield_curve_daily(date);

-- Training data: news buckets mapped to yield curve changes
CREATE TABLE IF NOT EXISTS news_yield_training (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT,
  bucket TEXT,
  bucket_count INTEGER,
  bucket_weight REAL,  -- normalized weight based on article count/importance
  delta_2y REAL,
  delta_5y REAL,
  delta_10y REAL,
  delta_30y REAL,
  delta_2s10s REAL,
  delta_2s30s REAL,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_training_date ON news_yield_training(date);
CREATE INDEX IF NOT EXISTS idx_training_bucket ON news_yield_training(bucket);
