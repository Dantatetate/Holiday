PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS holidays (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  canonical_title TEXT NOT NULL,
  canonical_title_norm TEXT NOT NULL,
  lang TEXT NOT NULL DEFAULT 'ru'
);

CREATE INDEX IF NOT EXISTS idx_holidays_title_norm ON holidays(canonical_title_norm);

CREATE TABLE IF NOT EXISTS occurrences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  holiday_id INTEGER NOT NULL,
  date TEXT NOT NULL, 
  UNIQUE(holiday_id, date),
  FOREIGN KEY (holiday_id) REFERENCES holidays(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_occurrences_date ON occurrences(date);

CREATE TABLE IF NOT EXISTS mentions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  occurrence_id INTEGER NOT NULL,
  source_id INTEGER NOT NULL,
  title_raw TEXT NOT NULL,
  title_norm TEXT NOT NULL,
  description TEXT,
  url TEXT NOT NULL,
  date_parsed TEXT NOT NULL,
  FOREIGN KEY (occurrence_id) REFERENCES occurrences(id) ON DELETE CASCADE,
  FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS descriptions_dict (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title_norm TEXT NOT NULL UNIQUE,
  title_raw TEXT NOT NULL,
  description TEXT NOT NULL,
  url TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_desc_title_norm ON descriptions_dict(title_norm);
CREATE INDEX IF NOT EXISTS idx_mentions_occurrence ON mentions(occurrence_id);
CREATE INDEX IF NOT EXISTS idx_mentions_source ON mentions(source_id);
