PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA busy_timeout=3000;
CREATE TABLE IF NOT EXISTS node_meta (k TEXT PRIMARY KEY, v TEXT NOT NULL); -- region, next_seq, hlc_l, hlc_c
CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, origin TEXT NOT NULL, seq INTEGER NOT NULL,
  report_id TEXT NOT NULL, type TEXT NOT NULL, field TEXT, priority INTEGER NOT NULL,
  hlc_l INTEGER NOT NULL, hlc_c INTEGER NOT NULL, hash TEXT NOT NULL, body TEXT NOT NULL,
  received_at REAL NOT NULL, UNIQUE (origin, seq));
CREATE INDEX IF NOT EXISTS ix_events_report ON events (report_id);
CREATE TABLE IF NOT EXISTS reports (report_id TEXT PRIMARY KEY, view TEXT NOT NULL, n_conflicts INTEGER NOT NULL,
  needs_review INTEGER NOT NULL, incomplete INTEGER NOT NULL, updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS origin_progress (origin TEXT PRIMARY KEY, contiguous INTEGER NOT NULL, max_seen INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS peer_view (peer TEXT, origin TEXT, seq INTEGER, seen_at REAL, PRIMARY KEY (peer, origin));
CREATE TABLE IF NOT EXISTS peer_state (peer TEXT PRIMARY KEY, last_ok REAL, last_error TEXT, fails INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS links (peer TEXT PRIMARY KEY, mode TEXT NOT NULL DEFAULT 'up', delay_ms INTEGER DEFAULT 0,
  rate_bps INTEGER DEFAULT 0, drop_pct INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS quarantine (event_id TEXT, source TEXT, reason TEXT, body TEXT, at REAL);
CREATE TABLE IF NOT EXISTS idempotency (key TEXT PRIMARY KEY, req_hash TEXT, response TEXT, at REAL);
