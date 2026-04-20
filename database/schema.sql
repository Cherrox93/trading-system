-- ==============================================
-- TRADING SYSTEM — SCHEMAT BAZY DANYCH
-- ==============================================

-- Agenci i ich konfiguracja
CREATE TABLE IF NOT EXISTS agents (
    id                TEXT PRIMARY KEY,        -- 'trader_01'
    status            TEXT DEFAULT 'pending',  -- pending/onboarding/active/paused/killed
    created_at        TEXT DEFAULT (datetime('now')),
    onboarding_done   INTEGER DEFAULT 0,       -- 0/1
    strategies        TEXT,                    -- JSON array ["pivot_mr", "ema_cross"]
    strategy_reasoning TEXT,                   -- uzasadnienie wyboru strategii
    preferred_tokens  TEXT,                    -- JSON array ["WLD", "SOL"]
    personality       TEXT,                    -- 'aggressive'/'cautious'/'neutral'
    budget_usdt       REAL DEFAULT 0.0,        -- przydzielony budżet
    used_usdt         REAL DEFAULT 0.0,        -- środki w otwartych pozycjach
    pnl_usdt          REAL DEFAULT 0.0,        -- całkowity PnL
    risk_per_trade    REAL DEFAULT 0.007,      -- % kapitału per trade
    workspace_path    TEXT,                    -- ścieżka do workspace OpenClaw
    notes             TEXT,                    -- notatki Supervisora
    strategy_notes    TEXT,                    -- JSON dict {strategy_id: "nota agenta"}
    personal_notes    TEXT                     -- JSON array lekcji agenta [{timestamp, note}]
);

-- Historia transakcji
CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id        TEXT NOT NULL,
    timestamp       TEXT DEFAULT (datetime('now')),
    token           TEXT NOT NULL,             -- 'WLD'
    direction       TEXT NOT NULL,             -- 'long'/'short'
    size_usdt       REAL NOT NULL,             -- wartość pozycji
    entry_price     REAL NOT NULL,
    exit_price      REAL,                      -- NULL jeśli otwarta
    sl_price        REAL,
    tp_price        REAL,
    pnl_usdt        REAL,                      -- NULL jeśli otwarta
    status          TEXT DEFAULT 'open',       -- open/closed/cancelled
    strategy_used   TEXT,                      -- która strategia
    reasoning       TEXT,                      -- uzasadnienie wejścia
    confidence      REAL,                      -- 0.0-1.0
    mode            TEXT DEFAULT 'paper',      -- paper/live
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Korekty Supervisora
CREATE TABLE IF NOT EXISTS corrections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now')),
    agent_id    TEXT NOT NULL,
    type        TEXT NOT NULL,                 -- 'risk_reduction'/'strategy_change'/'pause'
    old_value   TEXT,                          -- JSON
    new_value   TEXT,                          -- JSON
    reasoning   TEXT,
    applied     INTEGER DEFAULT 0,             -- 0/1
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Logi aktywności systemu
CREATE TABLE IF NOT EXISTS activity_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now')),
    source      TEXT NOT NULL,                 -- 'trader_01'/'supervisor'/'system'
    level       TEXT DEFAULT 'info',           -- info/warning/error
    message     TEXT NOT NULL,
    metadata    TEXT                           -- JSON dodatkowe dane
);

-- Stan rynku (snapshoty co godzinę)
CREATE TABLE IF NOT EXISTS market_snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now')),
    token       TEXT NOT NULL,
    price       REAL,
    rsi         REAL,
    funding_rate REAL,
    volume_24h  REAL,
    regime      TEXT                           -- 'trending'/'ranging'/'volatile'
);

-- Indeksy dla wydajności
CREATE INDEX IF NOT EXISTS idx_trades_agent    ON trades(agent_id);
CREATE INDEX IF NOT EXISTS idx_trades_status   ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_time     ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_source      ON activity_log(source);
CREATE INDEX IF NOT EXISTS idx_log_time        ON activity_log(timestamp);
