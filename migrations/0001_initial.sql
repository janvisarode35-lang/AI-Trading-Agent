-- ===== section 6.0 =====
-- ---------------------------------------------------------------------------
-- 0001_initial.sql — SPEC-P1.2-STORAGE v0.1
-- PostgreSQL 16 + TimescaleDB. Runs as a superuser once; everything it creates
-- is owned by trading_owner, which is NOT the role the application connects as.
-- ---------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS btree_gist  WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS pgcrypto    WITH SCHEMA extensions;

-- Owns every object. The application never connects as this role.
CREATE ROLE trading_owner NOLOGIN;
-- The application. INSERT/SELECT everywhere; UPDATE only where §3.2 permits it.
CREATE ROLE app_rw        LOGIN;
-- The backtest. NO privilege on any bitemporal base table (§3.3, [DEFAULT-S1]).
CREATE ROLE backtest_ro   LOGIN;
-- Grafana. SELECT on continuous aggregates and metric tables only.
CREATE ROLE metrics_ro    LOGIN;

CREATE SCHEMA trading AUTHORIZATION trading_owner;

-- An unqualified CREATE TABLE must fail rather than land in public.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

GRANT USAGE ON SCHEMA trading, extensions TO app_rw, backtest_ro, metrics_ro;

SET search_path = trading, extensions, pg_catalog;

-- ===== section 6.1 =====
-- Bitemporal. instrument_id is assigned at first sighting and NEVER changes:
-- it survives ticker changes, exchange transfers, mergers and delisting.
-- [DEFAULT-1 of P1.1]: identity is PER LISTING VENUE. NSE RELIANCE and BSE
-- RELIANCE are two rows sharing one issuer_id.
CREATE TABLE trading.instrument (
    instrument_id     uuid          NOT NULL,
    issuer_id         uuid          NULL,
    market            text          NOT NULL CHECK (market IN ('US','IN')),
    exchange          text          NOT NULL CHECK (exchange IN ('NYSE','NASDAQ','NSE','BSE')),
    instrument_type   text          NOT NULL CHECK (instrument_type IN (
                          'COMMON_STOCK','ETF','ADR','ETN','CEF','SPAC','UNIT',
                          'WARRANT','RIGHT','PREFERRED','FUTURE','OPTION')),
    status            text          NOT NULL CHECK (status IN (
                          'ACTIVE','HALTED','SUSPENDED','DELISTED')),
    currency          text          NOT NULL CHECK (currency IN ('USD','INR')),
    qty_increment     numeric(18,6) NOT NULL CHECK (qty_increment > 0),
    lot_size          numeric(18,6) NULL CHECK (lot_size IS NULL OR lot_size > 0),
    supports_fractional boolean     NOT NULL DEFAULT false,
    isin              text          NULL CHECK (isin IS NULL OR length(isin) = 12),
    cusip             text          NULL CHECK (cusip IS NULL OR length(cusip) = 9),
    figi              text          NULL CHECK (figi IS NULL OR length(figi) = 12),
    figi_composite    text          NULL CHECK (figi_composite IS NULL OR length(figi_composite) = 12),
    delisted_on       date          NULL,
    final_price       numeric(18,6) NULL CHECK (final_price IS NULL OR final_price >= 0),
    knowledge_from    timestamptz   NOT NULL,
    knowledge_to      timestamptz   NULL,
    PRIMARY KEY (instrument_id, knowledge_from),

    -- The exchange determines the market; a mismatch is a loader bug, not a value.
    CONSTRAINT instrument_exchange_market_agree CHECK (
        (exchange IN ('NYSE','NASDAQ') AND market = 'US') OR
        (exchange IN ('NSE','BSE')     AND market = 'IN')),
    -- Invariant I1 at the schema level: a market implies its currency.
    CONSTRAINT instrument_market_currency_agree CHECK (
        (market = 'US' AND currency = 'USD') OR (market = 'IN' AND currency = 'INR')),
    -- India is lot-based; a missing lot_size would place an illegal quantity.
    CONSTRAINT instrument_india_needs_lot_size CHECK (
        market <> 'IN' OR lot_size IS NOT NULL),
    -- I7: a delisted instrument keeps its terminal facts and is never deleted.
    CONSTRAINT instrument_delisted_has_date CHECK (
        status <> 'DELISTED' OR delisted_on IS NOT NULL),
    -- P1.1 [DEFAULT-3] / Q-P1.1-3: US fractional needs market/day orders, which
    -- [CONST] reserves for emergency exit. Unrepresentable until Q-P1.1-3 closes.
    CONSTRAINT instrument_us_no_fractional_v1 CHECK (
        NOT (market = 'US' AND supports_fractional)),
    CONSTRAINT instrument_knowledge_interval CHECK (
        knowledge_to IS NULL OR knowledge_to > knowledge_from)
) WITH (fillfactor = 90);

-- Bitemporal, and the EXCLUDE is the point: it makes P1.1's AmbiguousSymbolError
-- unrepresentable rather than merely detected. A ticker reused by a different
-- company after a delisting is legal here; two live claims on it are not.
CREATE TABLE trading.symbol_mapping (
    mapping_id      uuid        NOT NULL DEFAULT extensions.gen_random_uuid(),
    instrument_id   uuid        NOT NULL,
    market          text        NOT NULL CHECK (market IN ('US','IN')),
    exchange        text        NOT NULL CHECK (exchange IN ('NYSE','NASDAQ','NSE','BSE')),
    symbol          text        NOT NULL CHECK (length(symbol) BETWEEN 1 AND 32),
    valid_from      date        NOT NULL,
    valid_to        date        NULL,
    knowledge_from  timestamptz NOT NULL,
    knowledge_to    timestamptz NULL,
    PRIMARY KEY (mapping_id),
    CONSTRAINT symbol_mapping_valid_interval CHECK (valid_to IS NULL OR valid_to > valid_from),
    CONSTRAINT symbol_mapping_knowledge_interval CHECK (
        knowledge_to IS NULL OR knowledge_to > knowledge_from),
    -- No two CURRENTLY-BELIEVED mappings may claim one (market, symbol) at once.
    CONSTRAINT symbol_mapping_no_overlap EXCLUDE USING gist (
        market WITH =, symbol WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&
    ) WHERE (knowledge_to IS NULL),
    -- Nor may one instrument carry two symbols on the same venue at once.
    CONSTRAINT symbol_mapping_one_symbol_per_instrument EXCLUDE USING gist (
        instrument_id WITH =, exchange WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&
    ) WHERE (knowledge_to IS NULL)
) WITH (fillfactor = 90);

-- A merger converts lots at share_ratio, carrying the ORIGINAL cost basis and
-- the ORIGINAL acquisition date (P1.1 §5.3, ASSUMPTION [VERIFY-P0.2], Q-P1.1-5).
CREATE TABLE trading.successor_link (
    predecessor_instrument_id uuid          NOT NULL,
    successor_instrument_id   uuid          NOT NULL,
    share_ratio               numeric(18,6) NOT NULL CHECK (share_ratio > 0),
    cash_per_share            numeric(18,2) NULL,
    cash_currency             text          NULL CHECK (cash_currency IN ('USD','INR')),
    effective_date            date          NOT NULL,
    audit_event_id            uuid          NOT NULL,
    PRIMARY KEY (predecessor_instrument_id, effective_date),
    CONSTRAINT successor_not_self CHECK (predecessor_instrument_id <> successor_instrument_id),
    CONSTRAINT successor_cash_has_currency CHECK (
        (cash_per_share IS NULL) = (cash_currency IS NULL))
);

-- ===== section 6.2 =====
-- ADR-11 requirement 2 forbids a hard-coded holiday list, so sessions are DATA.
-- Storing resolved UTC instants per date removes DST arithmetic from the runtime:
-- the loader resolved it once from the IANA database. ABSENCE OF A ROW IS "CLOSED";
-- there is no is_holiday flag to fall out of sync with reality.
CREATE TABLE trading.exchange_session (
    exchange              text        NOT NULL CHECK (exchange IN ('NYSE','NASDAQ','NSE','BSE')),
    trading_date          date        NOT NULL,
    market                text        NOT NULL CHECK (market IN ('US','IN')),
    session_type          text        NOT NULL CHECK (session_type IN ('REGULAR','HALF_DAY','SPECIAL')),
    pre_market_open_utc   timestamptz NULL,
    regular_open_utc      timestamptz NOT NULL,
    regular_close_utc     timestamptz NOT NULL,
    post_market_close_utc timestamptz NULL,
    settlement_date       date        NOT NULL,
    -- FALSE excludes Muhurat and other special sessions from trading_date
    -- sequencing and from every rolling-window count (P0.1 §6).
    counts_for_sequencing boolean     NOT NULL DEFAULT true,
    PRIMARY KEY (exchange, trading_date),
    CONSTRAINT session_open_before_close CHECK (regular_close_utc > regular_open_utc),
    CONSTRAINT session_pre_before_open   CHECK (
        pre_market_open_utc IS NULL OR pre_market_open_utc < regular_open_utc),
    CONSTRAINT session_post_after_close  CHECK (
        post_market_close_utc IS NULL OR post_market_close_utc > regular_close_utc),
    CONSTRAINT session_settles_not_before CHECK (settlement_date >= trading_date),
    CONSTRAINT session_exchange_market_agree CHECK (
        (exchange IN ('NYSE','NASDAQ') AND market = 'US') OR
        (exchange IN ('NSE','BSE')     AND market = 'IN'))
);

-- ADOPTED VERBATIM from SPEC-P0.2-PROVIDERS v0.5 §10.3 (FROZEN). Not restated,
-- not reformatted. P1.2 adds only the overlap constraint P0.2 delegated by
-- describing overlapping rows as an ambiguous state.
CREATE TABLE trading.tick_size_regime (
    market           TEXT        NOT NULL,
    symbol           TEXT        NOT NULL,
    effective_from   DATE        NOT NULL,
    effective_to     DATE,
    tick_size        NUMERIC(12,6) NOT NULL CHECK (tick_size > 0),
    min_price        NUMERIC(12,6) NOT NULL DEFAULT 0 CHECK (min_price >= 0),
    source           TEXT        NOT NULL,
    PRIMARY KEY (market, symbol, effective_from),
    CHECK (effective_to IS NULL OR effective_to > effective_from)
);

-- P1.1 AmbiguousTickRegimeError made unrepresentable.
ALTER TABLE trading.tick_size_regime
    ADD CONSTRAINT tick_size_regime_no_overlap EXCLUDE USING gist (
        market WITH =, symbol WITH =,
        daterange(effective_from, effective_to, '[)') WITH &&);

-- Seed: US $0.01 for NMS stocks >= $1.00. The $0.005 increment is adopted but
-- exempted until the first business day of November 2027, then reassigned per
-- symbol twice yearly [V] (SEC Rule 612; release 34-105656). Date-versioned, so
-- the changeover is a data load, not a code change.
INSERT INTO trading.tick_size_regime
    (market, symbol, effective_from, effective_to, tick_size, min_price, source)
VALUES
    ('US','*', DATE '2015-01-01', NULL, 0.010000, 1.000000,
     'SEC Rule 612; $0.005 increment exempted until the first business day of November 2027 per release 34-105656');

-- ===== section 6.3 =====
-- Bitemporal. Deny-by-default on action_type: an unrecognised vendor code has no
-- enum member and the ingest raises rather than inserting. Ignoring a split does
-- not raise — it silently misprices every subsequent bar.
CREATE TABLE trading.corporate_action (
    action_id       uuid          NOT NULL,
    instrument_id   uuid          NOT NULL,
    market          text          NOT NULL CHECK (market IN ('US','IN')),
    action_type     text          NOT NULL CHECK (action_type IN (
                        'SPLIT','REVERSE_SPLIT','CASH_DIVIDEND','STOCK_DIVIDEND',
                        'TICKER_CHANGE','EXCHANGE_TRANSFER','MERGER','ACQUISITION',
                        'SPINOFF','RIGHTS_ISSUE','DELISTING')),
    ex_date         date          NOT NULL,
    effective_date  date          NOT NULL,
    ratio           numeric(18,6) NULL CHECK (ratio IS NULL OR ratio > 0),
    cash_amount     numeric(18,2) NULL,
    cash_currency   text          NULL CHECK (cash_currency IN ('USD','INR')),
    source          text          NOT NULL,
    as_of           timestamptz   NOT NULL,
    retrieved_at    timestamptz   NOT NULL,
    knowledge_from  timestamptz   NOT NULL,
    knowledge_to    timestamptz   NULL,
    PRIMARY KEY (action_id, knowledge_from),
    CONSTRAINT ca_split_needs_ratio CHECK (
        action_type NOT IN ('SPLIT','REVERSE_SPLIT','STOCK_DIVIDEND') OR ratio IS NOT NULL),
    CONSTRAINT ca_dividend_needs_cash CHECK (
        action_type <> 'CASH_DIVIDEND' OR cash_amount IS NOT NULL),
    CONSTRAINT ca_cash_has_currency CHECK ((cash_amount IS NULL) = (cash_currency IS NULL)),
    CONSTRAINT ca_knowledge_interval CHECK (knowledge_to IS NULL OR knowledge_to > knowledge_from)
);

-- ===== section 6.4 =====
-- RULE-B3 discharged: numeric(18,6), NOT float8. float8 cannot represent 10.005
-- exactly, so rule N10's exact tick-multiple test would be unsound. Row width
-- 116 B — the branch P0.3 §2.2 already costed.
-- Rule N9: stored UNADJUSTED (adjusted=false on every vendor request); adjustment
-- is computed on read from corporate_action.
CREATE TABLE trading.bar_daily (
    instrument_id uuid          NOT NULL,
    ts            timestamptz   NOT NULL,
    trading_date  date          NOT NULL,
    market        text          NOT NULL CHECK (market IN ('US','IN')),
    open          numeric(18,6) NOT NULL CHECK (open  > 0),
    high          numeric(18,6) NOT NULL CHECK (high  > 0),
    low           numeric(18,6) NOT NULL CHECK (low   > 0),
    close         numeric(18,6) NOT NULL CHECK (close > 0),
    volume        bigint        NOT NULL CHECK (volume >= 0),
    trade_count   integer       NULL CHECK (trade_count IS NULL OR trade_count >= 0),
    -- A non-final bar MAY NOT feed a signal. This is P0.1 §6's "ATR(14) excludes
    -- today's partial bar" made enforceable in storage rather than remembered.
    is_final      boolean       NOT NULL,
    source        text          NOT NULL,
    retrieved_at  timestamptz   NOT NULL,
    CONSTRAINT bar_daily_ohlc_ordered CHECK (
        low <= open AND open <= high AND low <= close AND close <= high),
    PRIMARY KEY (instrument_id, ts)
) WITH (fillfactor = 100);

SELECT extensions.create_hypertable(
    'trading.bar_daily', 'ts', chunk_time_interval => INTERVAL '1 month');

CREATE TABLE trading.bar_intraday_5m (LIKE trading.bar_daily INCLUDING ALL);
SELECT extensions.create_hypertable(
    'trading.bar_intraday_5m', 'ts', chunk_time_interval => INTERVAL '7 days');

-- Separate table, NOT a flag: retention policies act on chunks, not rows, so a
-- flagged subset cannot be excluded from a drop. [DEFAULT-S7]
CREATE TABLE trading.bar_intraday_5m_validation (LIKE trading.bar_daily INCLUDING ALL);
SELECT extensions.create_hypertable(
    'trading.bar_intraday_5m_validation', 'ts', chunk_time_interval => INTERVAL '7 days');

-- ADR-15 §5: immutable once written. A past date's rate is NEVER re-fetched or
-- corrected in place — a silently revised rate rewrites NAV history. Enforced by
-- the append-only trigger in §9.3, not by convention.
CREATE TABLE trading.fx_rate (
    fx_rate_id   uuid          NOT NULL DEFAULT extensions.gen_random_uuid(),
    as_of_date   date          NOT NULL,
    base         text          NOT NULL CHECK (base  IN ('USD','INR')),
    quote        text          NOT NULL CHECK (quote IN ('USD','INR')),
    rate         numeric(18,6) NOT NULL CHECK (rate > 0),
    source       text          NOT NULL,
    retrieved_at timestamptz   NOT NULL,
    PRIMARY KEY (as_of_date, base, quote),
    CONSTRAINT fx_base_not_quote CHECK (base <> quote)
);

-- ===== section 6.5 =====
-- BITEMPORAL, and the reason this table exists in this shape.
-- Rule N1: features are lagged to disseminated_at, NEVER filed_at. Using filed_at
-- is look-ahead — the filing existed before anyone could act on it.
-- Rule N2: EDGAR index retrievals are snapshotted immutably; edgar_index_hash
-- pins the index this row was derived from so a Saturday rebuild cannot re-derive it.
-- restatement_seq = 1 is AS-REPORTED; higher values are restatements (§3.4).
CREATE TABLE trading.fundamentals_snapshot (
    snapshot_id      uuid        NOT NULL DEFAULT extensions.gen_random_uuid(),
    instrument_id    uuid        NOT NULL,
    market           text        NOT NULL CHECK (market IN ('US','IN')),
    period_end       date        NOT NULL,
    fiscal_period    text        NOT NULL CHECK (length(fiscal_period) BETWEEN 1 AND 16),
    calendar_as_of   date        NOT NULL,
    restatement_seq  integer     NOT NULL CHECK (restatement_seq >= 1),
    filed_at         timestamptz NOT NULL,
    disseminated_at  timestamptz NOT NULL,
    metrics          jsonb       NOT NULL,
    source           text        NOT NULL,
    edgar_index_hash text        NULL CHECK (edgar_index_hash IS NULL OR length(edgar_index_hash) = 64),
    retrieved_at     timestamptz NOT NULL,
    valid_from       date        NOT NULL,
    valid_to         date        NULL,
    knowledge_from   timestamptz NOT NULL,
    knowledge_to     timestamptz NULL,
    PRIMARY KEY (snapshot_id),
    UNIQUE (instrument_id, period_end, restatement_seq),
    CONSTRAINT fundamentals_disseminated_after_filed CHECK (disseminated_at >= filed_at),
    CONSTRAINT fundamentals_valid_interval CHECK (valid_to IS NULL OR valid_to > valid_from),
    CONSTRAINT fundamentals_knowledge_interval CHECK (
        knowledge_to IS NULL OR knowledge_to > knowledge_from),
    CONSTRAINT fundamentals_metrics_is_object CHECK (jsonb_typeof(metrics) = 'object')
);

-- I7: point-in-time and IMMUTABLE. Weekly reconstitution (ADR-14, Sat 06:00 UTC)
-- with 1,300/1,700 hysteresis. Every backtest selects membership AS OF the
-- decision date; this is the concrete mechanism delivering survivorship-bias-free
-- backtests, and it only works because rows are never deleted or updated.
CREATE TABLE trading.universe_membership (
    universe_version uuid    NOT NULL,
    market           text    NOT NULL CHECK (market IN ('US','IN')),
    instrument_id    uuid    NOT NULL,
    effective_from   date    NOT NULL,
    addv_rank        integer NOT NULL CHECK (addv_rank >= 1),
    -- TRUE when the name is retained purely because it is held (ADR-14: a held
    -- name is never dropped from the data universe regardless of rank, or the
    -- monitor and exit agent go blind on a position we still own).
    retained_as_held boolean NOT NULL DEFAULT false,
    PRIMARY KEY (universe_version, instrument_id)
);

CREATE TABLE trading.universe_version (
    universe_version uuid        NOT NULL PRIMARY KEY,
    market           text        NOT NULL CHECK (market IN ('US','IN')),
    effective_from   date        NOT NULL,
    instrument_count integer     NOT NULL CHECK (instrument_count >= 0),
    enter_rank       integer     NOT NULL CHECK (enter_rank > 0),
    exit_rank        integer     NOT NULL CHECK (exit_rank > enter_rank),
    audit_event_id   uuid        NOT NULL,
    created_at       timestamptz NOT NULL,
    UNIQUE (market, effective_from)
);

-- RULE N16 SHAPES THIS TABLE.
-- M-5 resolved [V]: the vendor news archive is NOT point-in-time — both vendors
-- expose a revision timestamp and neither offers an as-of-content parameter, so a
-- historical query returns the article as CURRENTLY stored. Therefore our store
-- must be the point-in-time record: revisions are NEW ROWS, never overwrites, and
-- revision_seq = 1 is the only point-in-time record.
-- Rule N14 / [CONST-4]: body_sanitised is the only body column. The raw vendor
-- text is NOT in this table and is not reachable from any LLM-bound path.
CREATE TABLE trading.news_item (
    news_id            uuid        NOT NULL DEFAULT extensions.gen_random_uuid(),
    vendor_id          text        NOT NULL CHECK (length(vendor_id) > 0),
    revision_seq       integer     NOT NULL CHECK (revision_seq >= 1),
    headline           text        NOT NULL,
    body_sanitised     text        NOT NULL,
    sanitiser_version  text        NOT NULL CHECK (length(sanitiser_version) > 0),
    vendor_published_at timestamptz NOT NULL,
    vendor_updated_at  timestamptz NULL,
    first_seen_at      timestamptz NOT NULL,
    source             text        NOT NULL,
    retrieved_at       timestamptz NOT NULL,
    PRIMARY KEY (vendor_id, revision_seq, first_seen_at),
    -- Revision 1 IS the point-in-time anchor a backtest joins on.
    CONSTRAINT news_rev1_is_anchor CHECK (revision_seq > 1 OR first_seen_at = retrieved_at)
);

SELECT extensions.create_hypertable(
    'trading.news_item', 'first_seen_at', chunk_time_interval => INTERVAL '1 month');

CREATE TABLE trading.news_instrument (
    vendor_id     text NOT NULL,
    revision_seq  integer NOT NULL,
    instrument_id uuid NOT NULL,
    PRIMARY KEY (vendor_id, revision_seq, instrument_id)
);

-- ===== section 6.6 =====
CREATE TABLE trading.candidate (
    candidate_id     uuid        NOT NULL PRIMARY KEY,
    instrument_id    uuid        NOT NULL,
    market           text        NOT NULL CHECK (market IN ('US','IN')),
    trading_date     date        NOT NULL,
    rank             integer     NOT NULL CHECK (rank >= 1),
    filters_passed   text[]      NOT NULL CHECK (cardinality(filters_passed) > 0),
    universe_version uuid        NOT NULL REFERENCES trading.universe_version ON DELETE RESTRICT,
    run_id           uuid        NOT NULL,
    created_at       timestamptz NOT NULL,
    UNIQUE (trading_date, market, instrument_id)
);

-- A Score is a DETERMINISTIC model output and is NEVER produced by an LLM
-- ([CONST-2]: an LLM does not size, and a score feeds sizing).
-- feature_vector_hash is required: ADR-07 reproducibility and ADR-08 promotion
-- accounting are both impossible if the exact input vector cannot be identified.
CREATE TABLE trading.score (
    score_id            uuid          NOT NULL PRIMARY KEY,
    instrument_id       uuid          NOT NULL,
    trading_date        date          NOT NULL,
    kind                text          NOT NULL CHECK (kind IN ('FUNDAMENTAL','TECHNICAL','COMPOSITE')),
    value               numeric(9,6)  NOT NULL CHECK (value >= 0 AND value <= 1),
    model_id            text          NOT NULL CHECK (length(model_id) > 0),
    model_version       text          NOT NULL CHECK (length(model_version) > 0),
    feature_vector_hash text          NOT NULL CHECK (length(feature_vector_hash) = 64),
    computed_at         timestamptz   NOT NULL,
    UNIQUE (instrument_id, trading_date, kind, model_id)
);

-- The ONLY LLM-derived table. It has NO quantity, price, weight or limit column.
-- That absence is the schema-level expression of [CONST-2]: an LLM never sizes a
-- position, so the columns do not exist and no query can read one.
CREATE TABLE trading.thesis (
    thesis_id           uuid         NOT NULL PRIMARY KEY,
    candidate_id        uuid         NOT NULL REFERENCES trading.candidate ON DELETE RESTRICT,
    instrument_id       uuid         NOT NULL,
    trading_date        date         NOT NULL,
    bull_case           text         NOT NULL CHECK (length(bull_case) BETWEEN 1 AND 4000),
    bear_case           text         NOT NULL CHECK (length(bear_case) BETWEEN 1 AND 4000),
    -- The LLM's self-report. EXPLICITLY UNTRUSTED; never used for sizing.
    stated_confidence   numeric(9,6) NOT NULL CHECK (stated_confidence BETWEEN 0 AND 1),
    model_id            text         NOT NULL CHECK (length(model_id) > 0),
    prompt_version      text         NOT NULL CHECK (length(prompt_version) > 0),
    sanitiser_version   text         NOT NULL CHECK (length(sanitiser_version) > 0),
    input_content_hashes text[]      NOT NULL CHECK (cardinality(input_content_hashes) > 0),
    llm_call_id         uuid         NOT NULL,
    audit_event_id      uuid         NOT NULL,
    generated_at        timestamptz  NOT NULL
);

-- Machine-evaluable predicates only. A condition only a human can evaluate cannot
-- fire automatically, and a thesis-deterioration detector needing a human is not a
-- detector. At least one per thesis is enforced by the constraint trigger in §8.3.
CREATE TABLE trading.invalidation_condition (
    condition_id       uuid          NOT NULL PRIMARY KEY,
    thesis_id          uuid          NOT NULL REFERENCES trading.thesis ON DELETE RESTRICT,
    kind               text          NOT NULL CHECK (kind IN (
                           'PRICE_BELOW','ATR_STOP','TIME_STOP','FUNDAMENTAL_BREACH','NEWS_EVENT')),
    threshold_price    numeric(18,6) NULL CHECK (threshold_price IS NULL OR threshold_price >= 0),
    threshold_sessions integer       NULL CHECK (threshold_sessions IS NULL OR
                                                 threshold_sessions BETWEEN 1 AND 120),
    threshold_value    numeric(18,6) NULL,
    description        text          NOT NULL CHECK (length(description) BETWEEN 1 AND 500),
    CONSTRAINT invalidation_kind_has_threshold CHECK (
        (kind IN ('PRICE_BELOW','ATR_STOP')   AND threshold_price    IS NOT NULL) OR
        (kind =  'TIME_STOP'                  AND threshold_sessions IS NOT NULL) OR
        (kind IN ('FUNDAMENTAL_BREACH','NEWS_EVENT') AND threshold_value IS NOT NULL))
);

-- Frozen once written. A changed input produces a NEW verdict with a new id;
-- there is no mutation path, which is what makes invariant I2 checkable.
-- max_permissible_quantity is INFORMATIONAL on a DENY: it lets the sizer
-- re-propose once, and the re-proposal is evaluated from scratch. It is not the
-- risk engine sizing the position.
CREATE TABLE trading.risk_evaluation (
    verdict_id               uuid          NOT NULL PRIMARY KEY,
    request_id               uuid          NOT NULL,
    instrument_id            uuid          NOT NULL,
    pool_id                  text          NOT NULL CHECK (pool_id IN ('US_POOL','IN_POOL')),
    decision                 text          NOT NULL CHECK (decision IN ('ALLOW','DENY')),
    binding_constraint       text          NULL,
    max_permissible_quantity numeric(18,6) NULL CHECK (
                                 max_permissible_quantity IS NULL OR max_permissible_quantity >= 0),
    limits_evaluated         text[]        NOT NULL CHECK (cardinality(limits_evaluated) > 0),
    nav_snapshot_id          uuid          NOT NULL,
    evaluated_at             timestamptz   NOT NULL,
    audit_event_id           uuid          NOT NULL,
    -- A DENY that does not name its binding constraint is not reproducible.
    CONSTRAINT risk_deny_names_constraint CHECK (
        decision <> 'DENY' OR binding_constraint IS NOT NULL)
);

-- [CONST-2] MADE STRUCTURAL IN THE SCHEMA.
-- risk_verdict_id is NOT NULL and the CHECK forbids storing a DENY. A decision
-- carrying a denied verdict is UNREPRESENTABLE, not merely rejected in code.
-- thesis_id is NULLABLE: the deterministic path produces decisions with no LLM
-- involvement, and the LLM path can only ANNOTATE a decision the deterministic
-- path and the risk engine have already permitted.
CREATE TABLE trading.decision (
    decision_id      uuid          NOT NULL PRIMARY KEY,
    instrument_id    uuid          NOT NULL,
    market           text          NOT NULL CHECK (market IN ('US','IN')),
    pool_id          text          NOT NULL CHECK (pool_id IN ('US_POOL','IN_POOL')),
    trading_date     date          NOT NULL,
    action           text          NOT NULL CHECK (action IN ('ENTER','ADD','TRIM','EXIT','NO_TRADE')),
    target_quantity  numeric(18,6) NOT NULL CHECK (target_quantity >= 0),
    limit_price      numeric(18,6) NULL CHECK (limit_price IS NULL OR limit_price > 0),
    strategy_version text          NOT NULL CHECK (length(strategy_version) > 0),
    model_id         text          NOT NULL CHECK (length(model_id) > 0),
    risk_verdict_id  uuid          NOT NULL REFERENCES trading.risk_evaluation ON DELETE RESTRICT,
    risk_decision    text          NOT NULL CHECK (risk_decision = 'ALLOW'),
    signal_id        uuid          NULL,
    thesis_id        uuid          NULL REFERENCES trading.thesis ON DELETE RESTRICT,
    audit_event_id   uuid          NOT NULL,
    decided_at       timestamptz   NOT NULL,
    CONSTRAINT decision_no_trade_is_zero CHECK (
        (action = 'NO_TRADE' AND target_quantity = 0) OR
        (action <> 'NO_TRADE' AND target_quantity > 0)),
    CONSTRAINT decision_pool_market_agree CHECK (
        (pool_id = 'US_POOL' AND market = 'US') OR (pool_id = 'IN_POOL' AND market = 'IN'))
);

-- ===== section 6.7 =====
-- Invariant I6: every order carries strategy_version, model_id and a broker
-- idempotency key. [CONST-9]/SEBI: a unique strategy ID per order — harmless on
-- US orders, mandatory on Indian ones.
-- Rule N12: brokers without a documented idempotency key get client-side dedupe;
-- client_order_id is that persisted intent key, written BEFORE the broker call.
CREATE TABLE trading.order_intent (
    order_id         uuid          NOT NULL PRIMARY KEY,
    decision_id      uuid          NOT NULL REFERENCES trading.decision ON DELETE RESTRICT,
    account_id       uuid          NOT NULL,
    instrument_id    uuid          NOT NULL,
    market           text          NOT NULL CHECK (market IN ('US','IN')),
    pool_id          text          NOT NULL CHECK (pool_id IN ('US_POOL','IN_POOL')),
    side             text          NOT NULL CHECK (side IN ('BUY','SELL')),
    order_type       text          NOT NULL CHECK (order_type IN ('LIMIT','MARKET','STOP','STOP_LIMIT')),
    time_in_force    text          NOT NULL CHECK (time_in_force IN ('DAY','GTC','IOC','FOK')),
    quantity         numeric(18,6) NOT NULL CHECK (quantity > 0),
    limit_price      numeric(18,6) NULL CHECK (limit_price IS NULL OR limit_price > 0),
    stop_price       numeric(18,6) NULL CHECK (stop_price  IS NULL OR stop_price  > 0),
    state            text          NOT NULL CHECK (state IN (
                         'PENDING_NEW','NEW','PARTIALLY_FILLED','FILLED','PENDING_CANCEL',
                         'CANCELED','PENDING_REPLACE','REPLACED','REJECTED','EXPIRED','UNKNOWN')),
    filled_quantity  numeric(18,6) NOT NULL DEFAULT 0 CHECK (filled_quantity >= 0),
    client_order_id  text          NOT NULL CHECK (length(client_order_id) BETWEEN 1 AND 128),
    broker_order_id  text          NULL,
    broker_id        text          NOT NULL CHECK (length(broker_id) > 0),
    strategy_version text          NOT NULL CHECK (length(strategy_version) > 0),
    strategy_id      text          NOT NULL CHECK (length(strategy_id) > 0),
    model_id         text          NOT NULL CHECK (length(model_id) > 0),
    -- Kill-switch liquidation is EXEMPT from settled_cash and day_trades_5d
    -- (ADR-13 Chain D). A good-faith violation is a 90-day inconvenience; an
    -- uncontrolled drawdown is permanent. Audited and alerted on.
    kill_switch_exempt boolean     NOT NULL DEFAULT false,
    audit_event_id   uuid          NOT NULL,
    placed_at        timestamptz   NOT NULL,
    -- The prompt's named invariant, at the schema level.
    CONSTRAINT order_fill_not_over CHECK (filled_quantity <= quantity),
    CONSTRAINT order_limit_needs_price CHECK (order_type <> 'LIMIT' OR limit_price IS NOT NULL),
    CONSTRAINT order_market_has_no_limit CHECK (order_type <> 'MARKET' OR limit_price IS NULL),
    CONSTRAINT order_stop_needs_stop CHECK (
        order_type NOT IN ('STOP','STOP_LIMIT') OR stop_price IS NOT NULL),
    CONSTRAINT order_pool_market_agree CHECK (
        (pool_id = 'US_POOL' AND market = 'US') OR (pool_id = 'IN_POOL' AND market = 'IN')),
    -- The prompt's named invariant: unique client_order_id PER ACCOUNT.
    CONSTRAINT order_client_id_unique_per_account UNIQUE (account_id, client_order_id)
) WITH (fillfactor = 90);

-- Brokers re-send fills on reconnect; without the dedupe key a replayed fill
-- double-counts a position. Re-receipt of a known key is a no-op, not an update.
-- price is NOT tick-validated: sub-penny price improvement is real at execution.
-- Tick validation (rule N10) applies to prices we SEND, never to prices reported.
CREATE TABLE trading.fill (
    fill_id        uuid          NOT NULL PRIMARY KEY,
    order_id       uuid          NOT NULL REFERENCES trading.order_intent ON DELETE RESTRICT,
    instrument_id  uuid          NOT NULL,
    broker_id      text          NOT NULL CHECK (length(broker_id) > 0),
    broker_fill_id text          NOT NULL CHECK (length(broker_fill_id) > 0),
    quantity       numeric(18,6) NOT NULL CHECK (quantity > 0),
    price          numeric(18,6) NOT NULL CHECK (price >= 0),
    fees           numeric(18,2) NOT NULL,
    currency       text          NOT NULL CHECK (currency IN ('USD','INR')),
    filled_at      timestamptz   NOT NULL,
    audit_event_id uuid          NOT NULL,
    CONSTRAINT fill_dedupe UNIQUE (broker_id, broker_fill_id)
);

-- One tax-accounting acquisition unit. FIFO (P0.1 §6).
-- cost_total is stored; PER-SHARE BASIS IS NEVER STORED — storing it forces a
-- division, makes lot arithmetic non-closed, and loses a cent on every partial
-- consumption. Partial consumption uses largest-remainder allocation.
-- [DEFAULT-6 of P1.1]: wash-sale columns are US-only. India has no wash-sale rule
-- (ADR-13 Chain E), so a populated column on an IN lot would corrupt the export.
CREATE TABLE trading.lot (
    lot_id                    uuid          NOT NULL PRIMARY KEY,
    instrument_id             uuid          NOT NULL,
    market                    text          NOT NULL CHECK (market IN ('US','IN')),
    pool_id                   text          NOT NULL CHECK (pool_id IN ('US_POOL','IN_POOL')),
    opened_on                 date          NOT NULL,
    quantity_opened           numeric(18,6) NOT NULL CHECK (quantity_opened > 0),
    quantity_remaining        numeric(18,6) NOT NULL CHECK (quantity_remaining >= 0),
    cost_total                numeric(18,2) NOT NULL,
    fees_total                numeric(18,2) NOT NULL,
    currency                  text          NOT NULL CHECK (currency IN ('USD','INR')),
    cost_basis_method         text          NOT NULL DEFAULT 'FIFO'
                                            CHECK (cost_basis_method IN ('FIFO','LIFO','AVERAGE')),
    opening_fill_id           uuid          NOT NULL REFERENCES trading.fill ON DELETE RESTRICT,
    wash_sale_disallowed_loss numeric(18,2) NULL,
    wash_sale_adjusted_basis  numeric(18,2) NULL,
    audit_event_id            uuid          NOT NULL,
    CONSTRAINT lot_remaining_within_opened CHECK (quantity_remaining <= quantity_opened),
    CONSTRAINT lot_pool_market_agree CHECK (
        (pool_id = 'US_POOL' AND market = 'US') OR (pool_id = 'IN_POOL' AND market = 'IN')),
    CONSTRAINT lot_currency_matches_pool CHECK (
        (pool_id = 'US_POOL' AND currency = 'USD') OR (pool_id = 'IN_POOL' AND currency = 'INR')),
    CONSTRAINT lot_india_no_wash_sale CHECK (
        market <> 'IN' OR (wash_sale_disallowed_loss IS NULL AND wash_sale_adjusted_basis IS NULL)),
    -- "No overlapping lots", concretely: one fill opens at most one lot. Two lots
    -- from one fill would double-count the position against the broker's record.
    CONSTRAINT lot_one_per_opening_fill UNIQUE (opening_fill_id)
);

-- The projection over open lots. DERIVED, never the authority: ADR-10 makes the
-- BROKER the system of record for positions and cash. On disagreement the broker
-- wins for quantity and the discrepancy is escalated, never silently corrected.
-- While ANY position in a pool is UNRECONCILED the risk engine denies all new
-- entries ACROSS THE ENTIRE POOL (ADR-10 §2) — pool scope, not instrument scope.
CREATE TABLE trading.position_state (
    instrument_id             uuid          NOT NULL,
    pool_id                   text          NOT NULL CHECK (pool_id IN ('US_POOL','IN_POOL')),
    market                    text          NOT NULL CHECK (market IN ('US','IN')),
    state                     text          NOT NULL CHECK (state IN (
                                  'PENDING_OPEN','OPEN','PENDING_CLOSE','CLOSED','UNRECONCILED')),
    opened_on                 date          NULL,
    thesis_id                 uuid          NULL REFERENCES trading.thesis ON DELETE RESTRICT,
    stop_price                numeric(18,6) NULL CHECK (stop_price IS NULL OR stop_price > 0),
    broker_reported_quantity  numeric(18,6) NULL CHECK (
                                  broker_reported_quantity IS NULL OR broker_reported_quantity >= 0),
    audit_event_id            uuid          NOT NULL,
    updated_at                timestamptz   NOT NULL,
    PRIMARY KEY (instrument_id, pool_id),
    CONSTRAINT position_pool_market_agree CHECK (
        (pool_id = 'US_POOL' AND market = 'US') OR (pool_id = 'IN_POOL' AND market = 'IN'))
) WITH (fillfactor = 90);

CREATE TABLE trading.account (
    account_id     uuid          NOT NULL PRIMARY KEY,
    pool_id        text          NOT NULL CHECK (pool_id IN ('US_POOL','IN_POOL')),
    market         text          NOT NULL CHECK (market IN ('US','IN')),
    account_type   text          NOT NULL CHECK (account_type IN ('CASH','MARGIN')),
    broker_id      text          NOT NULL CHECK (length(broker_id) > 0),
    currency       text          NOT NULL CHECK (currency IN ('USD','INR')),
    equity         numeric(18,2) NOT NULL,
    total_cash     numeric(18,2) NOT NULL,
    -- ADR-13 Chain D / correction R-1: [RS §16] names PDT as the binding US
    -- constraint. Given ADR-12's CASH account it is not — settled funds are.
    settled_cash   numeric(18,2) NOT NULL,
    -- Computed and stored even in a CASH account, where it is not enforced, so
    -- the counter is proven correct before it ever becomes binding.
    day_trades_5d  integer       NOT NULL DEFAULT 0 CHECK (day_trades_5d >= 0),
    as_of          timestamptz   NOT NULL,
    CONSTRAINT account_settled_within_total CHECK (settled_cash <= total_cash),
    CONSTRAINT account_currency_matches_pool CHECK (
        (pool_id = 'US_POOL' AND currency = 'USD') OR (pool_id = 'IN_POOL' AND currency = 'INR'))
) WITH (fillfactor = 90);

-- ===== section 6.8 =====
-- Local currency, on that exchange's own trading_date.
-- ADR-15 §3: position limits are per-pool, in local currency. 5% means 5% of THAT
-- POOL's NAV — a consolidated-NAV position limit would authorise an India position
-- larger than the entire India pool.
-- peak_value is RESTORED FROM THE AUDIT TRAIL, never recomputed (invariant I4):
-- recomputation resets peak to the present value and silently un-trips the
-- drawdown condition — the kill switch would forget why it fired.
CREATE TABLE trading.nav_pool (
    nav_id           uuid          NOT NULL PRIMARY KEY,
    pool_id          text          NOT NULL CHECK (pool_id IN ('US_POOL','IN_POOL')),
    trading_date     date          NOT NULL,
    currency         text          NOT NULL CHECK (currency IN ('USD','INR')),
    total_value      numeric(18,2) NOT NULL CHECK (total_value      >= 0),
    cash             numeric(18,2) NOT NULL CHECK (cash             >= 0),
    positions_value  numeric(18,2) NOT NULL CHECK (positions_value  >= 0),
    peak_value       numeric(18,2) NOT NULL CHECK (peak_value       >= 0),
    -- ADR-15 §7: on a date where one market is open and the other is on holiday,
    -- the closed pool contributes its last computed NAV unchanged, flagged —
    -- distinguishable in the audit trail from a MISSING value, which fails closed.
    is_stale_holiday boolean       NOT NULL DEFAULT false,
    audit_event_id   uuid          NOT NULL,
    computed_at      timestamptz   NOT NULL,
    UNIQUE (pool_id, trading_date),
    CONSTRAINT nav_peak_not_below_total CHECK (peak_value >= total_value),
    CONSTRAINT nav_currency_matches_pool CHECK (
        (pool_id = 'US_POOL' AND currency = 'USD') OR (pool_id = 'IN_POOL' AND currency = 'INR'))
);

-- USD base, on the UTC ACCOUNTING DATE (ADR-15 §7) — distinct from trading_date.
-- ADR-15 §6: FX translation is its OWN line, never blended into trading P&L, so a
-- good year in India is neither flattered nor hidden by a rupee move.
-- While India is unfunded NAV_IN = 0 and this computation runs anyway, exercising
-- the code path daily: an FX layer first exercised on the day it matters fails on
-- the day it matters.
CREATE TABLE trading.nav_consolidated (
    nav_id                 uuid          NOT NULL PRIMARY KEY,
    utc_accounting_date    date          NOT NULL UNIQUE,
    total_value_usd        numeric(18,2) NOT NULL CHECK (total_value_usd >= 0),
    peak_value_usd         numeric(18,2) NOT NULL CHECK (peak_value_usd  >= 0),
    translation_effect_usd numeric(18,2) NOT NULL,
    fx_rate_ids            uuid[]        NOT NULL,
    pool_nav_ids           uuid[]        NOT NULL CHECK (cardinality(pool_nav_ids) > 0),
    audit_event_id         uuid          NOT NULL,
    computed_at            timestamptz   NOT NULL,
    CONSTRAINT nav_consolidated_peak_not_below CHECK (peak_value_usd >= total_value_usd)
);

CREATE TABLE trading.portfolio_snapshot (
    snapshot_id     uuid          NOT NULL PRIMARY KEY,
    pool_id         text          NOT NULL CHECK (pool_id IN ('US_POOL','IN_POOL')),
    trading_date    date          NOT NULL,
    position_count  integer       NOT NULL CHECK (position_count >= 0),
    gross_exposure_pct numeric(9,6) NOT NULL CHECK (gross_exposure_pct >= 0),
    net_exposure_pct   numeric(9,6) NOT NULL CHECK (net_exposure_pct   >= 0),
    cash_pct        numeric(9,6)  NOT NULL CHECK (cash_pct BETWEEN 0 AND 1),
    has_unreconciled boolean      NOT NULL,
    audit_event_id  uuid          NOT NULL,
    computed_at     timestamptz   NOT NULL,
    UNIQUE (pool_id, trading_date),
    -- ADR-12 long-only cash: gross ≡ net ≤ 1.0×. P0.1 §C-2 keeps [CONST]'s 2×
    -- ceiling in config as an unreachable upper bound while 1.0× binds.
    CONSTRAINT portfolio_gross_equals_net_long_only CHECK (gross_exposure_pct = net_exposure_pct),
    CONSTRAINT portfolio_gross_within_account_ceiling CHECK (gross_exposure_pct <= 1.0)
);

-- ===== section 6.9 =====
-- Every transition is a row. The asymmetry is the design: transitions TOWARD halt
-- are automatic; transitions AWAY require an ADR-09 row 1 Owner approval with no
-- SLA, no auto-expiry and no auto-re-enable.
CREATE TABLE trading.kill_switch_event (
    event_id             uuid        NOT NULL PRIMARY KEY,
    scope                text        NOT NULL CHECK (scope IN ('GLOBAL','POOL')),
    pool_id              text        NULL CHECK (pool_id IS NULL OR pool_id IN ('US_POOL','IN_POOL')),
    from_state           text        NULL CHECK (from_state IS NULL OR
                                         from_state IN ('ARMED','POOL_HALTED','TRIPPED')),
    to_state             text        NOT NULL CHECK (to_state IN ('ARMED','POOL_HALTED','TRIPPED')),
    reason               text        NULL,
    tripped_by           text        NULL,
    re_enable_approval_id uuid       NULL,
    audit_event_id       uuid        NOT NULL,
    occurred_at          timestamptz NOT NULL,
    CONSTRAINT ks_pool_scope_has_pool CHECK ((scope = 'POOL') = (pool_id IS NOT NULL)),
    CONSTRAINT ks_halt_has_reason CHECK (to_state = 'ARMED' OR reason IS NOT NULL),
    -- No code path arms the switch without an Owner approval (invariant I3).
    CONSTRAINT ks_arm_requires_approval CHECK (
        to_state <> 'ARMED' OR re_enable_approval_id IS NOT NULL),
    -- No partial de-escalation: a global trip clears to ARMED by a human, or not at all.
    CONSTRAINT ks_no_partial_deescalation CHECK (
        NOT (from_state = 'TRIPPED' AND to_state = 'POOL_HALTED'))
);

CREATE TABLE trading.model_registry (
    model_id           text        NOT NULL,
    model_version      text        NOT NULL,
    kind               text        NOT NULL CHECK (kind IN (
                           'SCREENER','FUNDAMENTAL','TECHNICAL','COMPOSITE','REGIME')),
    role               text        NOT NULL CHECK (role IN ('CHAMPION','CHALLENGER','RETIRED')),
    trained_at         timestamptz NOT NULL,
    train_window_start date        NOT NULL,
    train_window_end   date        NOT NULL,
    artifact_sha256    text        NOT NULL CHECK (length(artifact_sha256) = 64),
    feature_list_hash  text        NOT NULL CHECK (length(feature_list_hash) = 64),
    -- ADR-08 / AD-2: promotion is proven on walk-forward OOS at 3-month rolls,
    -- >= 34 windows and >= 1,000 closed trades. Live shadow detects harm only.
    wf_windows         integer     NULL CHECK (wf_windows IS NULL OR wf_windows >= 0),
    wf_closed_trades   integer     NULL CHECK (wf_closed_trades IS NULL OR wf_closed_trades >= 0),
    dsr                numeric(9,6) NULL,
    promoted_at        timestamptz NULL,
    promotion_approval_id uuid     NULL,
    audit_event_id     uuid        NOT NULL,
    PRIMARY KEY (model_id, model_version),
    CONSTRAINT model_train_window_ordered CHECK (train_window_end > train_window_start),
    -- A champion must carry the evidence ADR-08 requires and an Owner approval.
    CONSTRAINT model_champion_has_evidence CHECK (
        role <> 'CHAMPION' OR (wf_windows >= 34 AND wf_closed_trades >= 1000
                               AND promotion_approval_id IS NOT NULL))
);

CREATE TABLE trading.config_version (
    config_hash    text        NOT NULL PRIMARY KEY CHECK (length(config_hash) = 64),
    payload        jsonb       NOT NULL,
    applied_at     timestamptz NOT NULL,
    applied_by     text        NOT NULL,
    approval_id    uuid        NULL,
    audit_event_id uuid        NOT NULL,
    CONSTRAINT config_payload_is_object CHECK (jsonb_typeof(payload) = 'object')
);

-- [DEFAULT-S10]: prompt and response text are stored, not only hashed. ADR-07
-- reproducibility and P4.4 output validation both need the actual text.
-- prompt_sanitised is post-sanitiser (rule N14): raw vendor text never lands here.
-- cost_usd is numeric(18,6): quantising $0.00300 to cents would zero the spend model.
CREATE TABLE trading.llm_call (
    llm_call_id       uuid          NOT NULL,
    called_at         timestamptz   NOT NULL,
    provider_id       text          NOT NULL CHECK (provider_id IN ('OPENAI','DEEPSEEK')),
    model_id          text          NOT NULL CHECK (length(model_id) > 0),
    prompt_version    text          NOT NULL CHECK (length(prompt_version) > 0),
    sanitiser_version text          NOT NULL CHECK (length(sanitiser_version) > 0),
    prompt_sanitised  text          NOT NULL,
    prompt_hash       text          NOT NULL CHECK (length(prompt_hash) = 64),
    response_text     text          NULL,
    response_hash     text          NULL CHECK (response_hash IS NULL OR length(response_hash) = 64),
    input_tokens      integer       NOT NULL CHECK (input_tokens  >= 0),
    output_tokens     integer       NOT NULL CHECK (output_tokens >= 0),
    cost_usd          numeric(18,6) NOT NULL CHECK (cost_usd >= 0),
    -- AD-5: STANDARD tier only on the live path until M-10 closes.
    tier              text          NOT NULL DEFAULT 'STANDARD' CHECK (tier IN ('STANDARD','BATCH')),
    outcome           text          NOT NULL CHECK (outcome IN ('OK','TIMEOUT','SCHEMA_FAIL','ERROR')),
    -- RULE-B9(d): approved replay spend is EXCLUDED from the alarm counter, tagged
    -- by job id. Without this exclusion one approved $87 replay pins CRITICAL on
    -- for 30 days and masks a genuine live-path regression underneath it.
    replay_job_id     uuid          NULL,
    run_id            uuid          NOT NULL,
    audit_event_id    uuid          NOT NULL,
    PRIMARY KEY (llm_call_id, called_at),
    CONSTRAINT llm_ok_has_response CHECK (outcome <> 'OK' OR response_text IS NOT NULL),
    -- AD-5: the live path is never BATCH until M-10 closes.
    CONSTRAINT llm_live_is_standard CHECK (replay_job_id IS NOT NULL OR tier = 'STANDARD')
);

SELECT extensions.create_hypertable(
    'trading.llm_call', 'called_at', chunk_time_interval => INTERVAL '1 month');

-- ADOPTED VERBATIM from SPEC-P0.2-PROVIDERS v0.5 §10.3 (FROZEN).
CREATE TABLE trading.provider_quota_usage (
    provider_id      TEXT        NOT NULL,
    scope            TEXT        NOT NULL,
    window_start     TIMESTAMPTZ NOT NULL,
    window_end       TIMESTAMPTZ NOT NULL,
    request_count    BIGINT      NOT NULL DEFAULT 0 CHECK (request_count   >= 0),
    response_bytes   BIGINT      NOT NULL DEFAULT 0 CHECK (response_bytes  >= 0),
    throttled_count  BIGINT      NOT NULL DEFAULT 0 CHECK (throttled_count >= 0),
    PRIMARY KEY (provider_id, scope, window_start),
    CHECK (window_end > window_start)
);
SELECT extensions.create_hypertable('trading.provider_quota_usage', 'window_start',
    chunk_time_interval => INTERVAL '1 month', migrate_data => true);

-- ADOPTED VERBATIM from SPEC-P0.3-BUDGET v0.5 §14.5 (FROZEN), including its
-- indexes. P0.3 explicitly delegates the hypertable conversion to this phase.
CREATE TABLE trading.stage_latency_observation (
    observation_id        bigint GENERATED ALWAYS AS IDENTITY,
    market                text          NOT NULL CHECK (market IN ('US', 'IN')),
    trading_date          date          NOT NULL,
    stage                 text          NOT NULL CHECK (stage IN (
                              'INGEST','UNIVERSE_RESOLVE','TIER1_SCREEN',
                              'TIER2_QUANT','INFERENCE_GATE','TIER3_LLM',
                              'DECISION','RISK','AUDIT_FREEZE',
                              'ORDER_PLACEMENT','MONITOR_EVAL','EXIT_SUBMIT')),
    started_at            timestamptz   NOT NULL,
    finished_at           timestamptz   NOT NULL,
    observed_seconds      numeric(12,3) NOT NULL CHECK (observed_seconds >= 0),
    budget_seconds        numeric(12,3) NOT NULL CHECK (budget_seconds > 0),
    breached              boolean       NOT NULL,
    breach_action_taken   text          NULL CHECK (breach_action_taken IN (
                              'ABORT','DEGRADE','DENY_ALL','RETRY_IN_WINDOW',
                              'ABANDON','ALERT_CRITICAL')),
    strategy_version      text          NOT NULL CHECK (length(strategy_version) > 0),
    CONSTRAINT finished_after_started CHECK (finished_at >= started_at),
    CONSTRAINT breach_implies_action  CHECK (NOT breached OR breach_action_taken IS NOT NULL),
    CONSTRAINT action_implies_breach  CHECK (breach_action_taken IS NULL OR breached),
    CONSTRAINT degrade_is_llm_only    CHECK (breach_action_taken IS DISTINCT FROM 'DEGRADE'
                                             OR stage = 'TIER3_LLM'),
    PRIMARY KEY (observation_id, started_at)
);
SELECT extensions.create_hypertable('trading.stage_latency_observation', 'started_at',
    chunk_time_interval => INTERVAL '7 days');
CREATE INDEX stage_latency_observation_stage_date_idx
    ON trading.stage_latency_observation (stage, trading_date DESC);

-- run_context stamps is_paper on every audit event. Rule N11: paper results are
-- PLUMBING EVIDENCE ONLY — no slippage, fill-quality, fee or edge conclusion may
-- cite paper data. Storing the flag is what makes N11 mechanically checkable
-- rather than a discipline P5.3 has to remember.
CREATE TABLE trading.run_context (
    run_id           uuid        NOT NULL PRIMARY KEY,
    run_type         text        NOT NULL CHECK (run_type IN (
                         'INGEST','PIPELINE','ORDER','MONITOR','RECONCILE','BACKTEST','PAPER')),
    market           text        NOT NULL CHECK (market IN ('US','IN')),
    trading_date     date        NOT NULL,
    started_at       timestamptz NOT NULL,
    finished_at      timestamptz NULL,
    code_version     text        NOT NULL CHECK (length(code_version) BETWEEN 7 AND 40),
    config_hash      text        NOT NULL REFERENCES trading.config_version ON DELETE RESTRICT,
    strategy_version text        NOT NULL CHECK (length(strategy_version) > 0),
    model_id         text        NOT NULL CHECK (length(model_id) > 0),
    is_paper         boolean     NOT NULL,
    is_backtest      boolean     NOT NULL,
    -- A run is paper or backtest, never both: conflating them would let a backtest
    -- result be cited as paper plumbing evidence and vice versa.
    CONSTRAINT run_not_both_paper_and_backtest CHECK (NOT (is_paper AND is_backtest)),
    CONSTRAINT run_backtest_flag_agrees CHECK (run_type <> 'BACKTEST' OR is_backtest),
    CONSTRAINT run_paper_flag_agrees    CHECK (run_type <> 'PAPER'    OR is_paper)
);

-- ===== section 9.1 =====
CREATE TABLE trading.audit_log (
    event_id     uuid        NOT NULL DEFAULT extensions.gen_random_uuid(),
    -- Monotonic, gapless, GLOBAL [DEFAULT-S9]. Ordering comes from here, never
    -- from a uuid and never from a timestamp.
    seq          bigint      NOT NULL,
    prev_hash    text        NOT NULL CHECK (length(prev_hash)    = 64),
    payload_hash text        NOT NULL CHECK (length(payload_hash) = 64),
    event_type   text        NOT NULL CHECK (length(event_type) > 0),
    -- RULE-B4: actions are individually durable; evaluations may be batched.
    -- An evaluation that becomes the REASON for an action is promoted to ACTION.
    event_class  text        NOT NULL CHECK (event_class IN (
                     'ACTION','EVALUATION','NAV','RISK','KILL_SWITCH','APPROVAL','SYSTEM')),
    occurred_at  timestamptz NOT NULL,
    recorded_at  timestamptz NOT NULL,
    actor        text        NOT NULL CHECK (length(actor) > 0),
    run_id       uuid        NOT NULL,
    is_paper     boolean     NOT NULL,
    is_backtest  boolean     NOT NULL,
    payload      jsonb       NOT NULL,
    PRIMARY KEY (seq, occurred_at),
    CONSTRAINT audit_recorded_not_before_occurred CHECK (recorded_at >= occurred_at),
    CONSTRAINT audit_payload_is_object CHECK (jsonb_typeof(payload) = 'object'),
    CONSTRAINT audit_genesis_hash CHECK (seq > 0 OR prev_hash = repeat('0', 64))
) WITH (fillfactor = 100);

SELECT extensions.create_hypertable(
    'trading.audit_log', 'occurred_at', chunk_time_interval => INTERVAL '7 days');

-- ===== section 6.10 =====
-- ---- Compression (§5.3). storage.compression_after_days = 30 -----------------
ALTER TABLE trading.bar_daily SET (
    timescaledb.compress, timescaledb.compress_segmentby = 'instrument_id',
    timescaledb.compress_orderby = 'ts DESC');
ALTER TABLE trading.bar_intraday_5m SET (
    timescaledb.compress, timescaledb.compress_segmentby = 'instrument_id',
    timescaledb.compress_orderby = 'ts DESC');
ALTER TABLE trading.bar_intraday_5m_validation SET (
    timescaledb.compress, timescaledb.compress_segmentby = 'instrument_id',
    timescaledb.compress_orderby = 'ts DESC');
-- segmentby is event_class, NOT run_id: chain verification ranges over seq across
-- all runs, and a high-cardinality segment would produce one segment per run.
ALTER TABLE trading.audit_log SET (
    timescaledb.compress, timescaledb.compress_segmentby = 'event_class',
    timescaledb.compress_orderby = 'seq');
ALTER TABLE trading.news_item SET (
    timescaledb.compress, timescaledb.compress_segmentby = 'source',
    timescaledb.compress_orderby = 'first_seen_at DESC');
ALTER TABLE trading.llm_call SET (
    timescaledb.compress, timescaledb.compress_segmentby = 'provider_id',
    timescaledb.compress_orderby = 'called_at DESC');

SELECT extensions.add_compression_policy('trading.bar_daily',                   INTERVAL '30 days');
SELECT extensions.add_compression_policy('trading.bar_intraday_5m',             INTERVAL '30 days');
SELECT extensions.add_compression_policy('trading.bar_intraday_5m_validation',  INTERVAL '30 days');
SELECT extensions.add_compression_policy('trading.audit_log',                   INTERVAL '30 days');
SELECT extensions.add_compression_policy('trading.news_item',                   INTERVAL '30 days');
SELECT extensions.add_compression_policy('trading.llm_call',                    INTERVAL '30 days');

-- ---- Retention (§5.4) --------------------------------------------------------
-- NOTE THE ABSENCES. There is deliberately NO retention policy on audit_log
-- (audit.retention_years = indefinite; invariant I4 replays counters from it;
-- ADR-10 §5 makes a gap a hard stop), NO policy on bar_daily, NO policy on
-- news_item (rule N16: our store IS the point-in-time record), and NO policy on
-- bar_intraday_5m_validation (P5.2's fixed slice). Adding one to any of these is
-- a spec violation, not a tuning decision.
SELECT extensions.add_retention_policy('trading.bar_intraday_5m',          INTERVAL '3 years');
SELECT extensions.add_retention_policy('trading.llm_call',                 INTERVAL '7 years');
SELECT extensions.add_retention_policy('trading.stage_latency_observation',INTERVAL '2 years');
SELECT extensions.add_retention_policy('trading.provider_quota_usage',     INTERVAL '400 days');

-- ---- Continuous aggregates (§5.5) -------------------------------------------
-- materialized_only = true on all three. A real-time CAGG unions materialised
-- buckets with a LIVE scan of the raw table, which would let a backtest read past
-- its knowledge cutoff through the aggregate — the exact bypass §3.3 closes.

-- Consumer: RULE-B9's two-tier alarm (WARN $5 / CRITICAL $50, trailing 30 days,
-- UTC, metered, replay-excluded). cost_usd stays numeric(18,6) per RULE-B3.
CREATE MATERIALIZED VIEW trading.cagg_llm_spend_daily
    WITH (timescaledb.continuous, timescaledb.materialized_only = true) AS
SELECT extensions.time_bucket(INTERVAL '1 day', called_at) AS bucket,
       provider_id,
       model_id,
       (replay_job_id IS NOT NULL)      AS is_replay,
       count(*)                          AS call_count,
       sum(cost_usd)::numeric(18,6)      AS cost_usd,
       sum(input_tokens)                 AS input_tokens,
       sum(output_tokens)                AS output_tokens,
       count(*) FILTER (WHERE outcome <> 'OK') AS failure_count
  FROM trading.llm_call
 GROUP BY bucket, provider_id, model_id, is_replay
WITH NO DATA;

-- Consumer: P0.3 §9.4's audit-volume line and measurement-by-design Q15
-- ("audit-event rate and row width, after 20 live sessions").
CREATE MATERIALIZED VIEW trading.cagg_audit_events_daily
    WITH (timescaledb.continuous, timescaledb.materialized_only = true) AS
SELECT extensions.time_bucket(INTERVAL '1 day', occurred_at) AS bucket,
       event_class,
       is_paper,
       is_backtest,
       count(*)                                   AS event_count,
       sum(pg_column_size(payload))::bigint       AS payload_bytes,
       avg(pg_column_size(payload))::numeric(12,2) AS mean_payload_bytes
  FROM trading.audit_log
 GROUP BY bucket, event_class, is_paper, is_backtest
WITH NO DATA;

-- Consumer: P2.6 regime features and ADR-07's T3 universe-shock trigger.
-- RULE-B3's second edge case: the same numeric(18,6) choice as the base table, or
-- P0.3 §2.2 would double-count at two different row widths.
CREATE MATERIALIZED VIEW trading.cagg_bar_weekly
    WITH (timescaledb.continuous, timescaledb.materialized_only = true) AS
SELECT extensions.time_bucket(INTERVAL '7 days', ts) AS bucket,
       instrument_id,
       market,
       (extensions.first(open, ts))::numeric(18,6)  AS open,
       max(high)::numeric(18,6)                     AS high,
       min(low)::numeric(18,6)                      AS low,
       (extensions.last(close, ts))::numeric(18,6)  AS close,
       sum(volume)::bigint                          AS volume
  FROM trading.bar_daily
 WHERE is_final
 GROUP BY bucket, instrument_id, market
WITH NO DATA;

-- Refresh windows lag the live edge so a partially-written session never
-- materialises. end_offset > 0 is what keeps a same-day bucket out of the CAGG.
SELECT extensions.add_continuous_aggregate_policy('trading.cagg_llm_spend_daily',
    start_offset => INTERVAL '35 days', end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
SELECT extensions.add_continuous_aggregate_policy('trading.cagg_audit_events_daily',
    start_offset => INTERVAL '35 days', end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
SELECT extensions.add_continuous_aggregate_policy('trading.cagg_bar_weekly',
    start_offset => INTERVAL '90 days', end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- ---- AS-OF FUNCTIONS: the only path by which a backtest reads anything -------
-- STABLE SECURITY DEFINER. search_path is pinned on every one of them; omitting
-- it is the standard SECURITY DEFINER privilege-escalation hole.
-- NEITHER cutoff has a default. A default cutoff is a cutoff somebody forgets to
-- think about, and the whole design of §3.3 is that forgetting must fail loudly.

-- Rule N1: disseminated_at, NEVER filed_at. The filing existed before anyone
-- could act on it. restatement_seq DESC picks the latest restatement that was
-- public by p_market_asof — as-reported in December, restated in March (§3.4).
CREATE OR REPLACE FUNCTION trading.fundamentals_asof(
    p_instrument_id  uuid,
    p_market_asof    timestamptz,
    p_knowledge_asof timestamptz)
RETURNS SETOF trading.fundamentals_snapshot
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = trading, pg_temp AS $$
    SELECT DISTINCT ON (period_end) *
      FROM trading.fundamentals_snapshot
     WHERE instrument_id  = p_instrument_id
       AND disseminated_at <= p_market_asof
       AND knowledge_from  <= p_knowledge_asof
       AND (knowledge_to IS NULL OR knowledge_to > p_knowledge_asof)
     ORDER BY period_end DESC, restatement_seq DESC;
$$;

-- Rule N16's load-bearing corollary made physical: ONLY revision_seq = 1 is a
-- point-in-time record, so later revisions are unreadable through the backtest
-- path. They remain stored as evidence of what the vendor did.
CREATE OR REPLACE FUNCTION trading.news_asof(
    p_instrument_id  uuid,
    p_market_asof    timestamptz,
    p_knowledge_asof timestamptz)
RETURNS SETOF trading.news_item
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = trading, pg_temp AS $$
    SELECT n.*
      FROM trading.news_item n
      JOIN trading.news_instrument ni
        ON ni.vendor_id = n.vendor_id AND ni.revision_seq = n.revision_seq
     WHERE ni.instrument_id = p_instrument_id
       AND n.revision_seq   = 1
       AND n.vendor_published_at <= p_market_asof
       AND n.first_seen_at        <= p_knowledge_asof
     ORDER BY n.first_seen_at DESC;
$$;

-- I7 / ADR-14: membership is selected AS OF the decision date from the stored
-- snapshot history. This is the concrete mechanism delivering survivorship-bias-
-- free backtests.
CREATE OR REPLACE FUNCTION trading.universe_asof(
    p_market      text,
    p_trading_date date)
RETURNS TABLE (instrument_id uuid, addv_rank integer, retained_as_held boolean)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = trading, pg_temp AS $$
    SELECT um.instrument_id, um.addv_rank, um.retained_as_held
      FROM trading.universe_membership um
     WHERE um.universe_version = (
            SELECT uv.universe_version
              FROM trading.universe_version uv
             WHERE uv.market = p_market
               AND uv.effective_from <= p_trading_date
             ORDER BY uv.effective_from DESC
             LIMIT 1)
     ORDER BY um.addv_rank;
$$;

CREATE OR REPLACE FUNCTION trading.instrument_asof(
    p_instrument_id  uuid,
    p_knowledge_asof timestamptz)
RETURNS SETOF trading.instrument
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = trading, pg_temp AS $$
    SELECT * FROM trading.instrument
     WHERE instrument_id = p_instrument_id
       AND knowledge_from <= p_knowledge_asof
       AND (knowledge_to IS NULL OR knowledge_to > p_knowledge_asof);
$$;

-- A ticker reused by a different company after a delisting resolves correctly by
-- construction: the two rows carry different instrument_ids and disjoint
-- valid ranges. Two live claims are prevented by the EXCLUDE in §6.1.
CREATE OR REPLACE FUNCTION trading.symbol_asof(
    p_market         text,
    p_symbol         text,
    p_trading_date   date,
    p_knowledge_asof timestamptz)
RETURNS uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = trading, pg_temp AS $$
    SELECT instrument_id FROM trading.symbol_mapping
     WHERE market = p_market
       AND symbol = p_symbol
       AND valid_from <= p_trading_date
       AND (valid_to IS NULL OR p_trading_date < valid_to)
       AND knowledge_from <= p_knowledge_asof
       AND (knowledge_to IS NULL OR knowledge_to > p_knowledge_asof);
$$;

-- Bars and corporate actions are uni-temporal and immutable, so they need only
-- the market cutoff. is_final excludes a session still in progress, which is
-- P0.1 §6's "ATR(14) excludes today's partial bar" enforced at the read path.
CREATE OR REPLACE FUNCTION trading.bars_asof(
    p_instrument_id uuid,
    p_from          timestamptz,
    p_market_asof   timestamptz)
RETURNS SETOF trading.bar_daily
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = trading, pg_temp AS $$
    SELECT * FROM trading.bar_daily
     WHERE instrument_id = p_instrument_id
       AND ts >= p_from AND ts <= p_market_asof
       AND is_final
     ORDER BY ts;
$$;

-- ---- GRANTS: the mechanism, not the convention (§3.3, [DEFAULT-S1]) ----------
REVOKE ALL ON ALL TABLES    IN SCHEMA trading FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA trading FROM PUBLIC;

GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA trading TO app_rw;
-- UPDATE is granted ONLY where §3.2 permits it. Three groups, and nothing else:
--   (a) mutable state:   order_intent.state/filled_quantity, position_state.state,
--                        account balances, lot.quantity_remaining (FIFO consumption
--                        decrements it on every exit fill — without this grant the
--                        exit path fails with permission denied)
--   (b) bitemporal close: instrument, symbol_mapping, fundamentals_snapshot,
--                        corporate_action — and ONLY knowledge_to, further narrowed
--                        by the §8.4 trigger, which rejects any UPDATE that touches
--                        a fact column
--   (c) run completion:   run_context.finished_at
GRANT UPDATE ON trading.order_intent, trading.position_state, trading.account,
                trading.lot, trading.run_context,
                trading.instrument, trading.symbol_mapping,
                trading.fundamentals_snapshot, trading.corporate_action TO app_rw;
-- No DELETE anywhere, for any role. Nothing in this schema is ever deleted by the
-- application; retention is TimescaleDB dropping whole chunks as trading_owner.

-- THE LOAD-BEARING GRANT BLOCK. backtest_ro receives NO privilege on any base
-- table. A backtest that forgets its cutoff gets
--   ERROR: permission denied for table fundamentals_snapshot
-- rather than silently contaminated data. This is decision 1 of this spec.
GRANT EXECUTE ON FUNCTION
    trading.fundamentals_asof(uuid, timestamptz, timestamptz),
    trading.news_asof(uuid, timestamptz, timestamptz),
    trading.universe_asof(text, date),
    trading.instrument_asof(uuid, timestamptz),
    trading.symbol_asof(text, text, date, timestamptz),
    trading.bars_asof(uuid, timestamptz, timestamptz)
TO backtest_ro;

GRANT SELECT ON trading.cagg_llm_spend_daily, trading.cagg_audit_events_daily,
                trading.cagg_bar_weekly, trading.stage_latency_observation,
                trading.nav_pool, trading.nav_consolidated,
                trading.portfolio_snapshot, trading.kill_switch_event TO metrics_ro;

-- Default privileges, so a table added by a later migration does not silently
-- become readable by backtest_ro. The default for backtest_ro is nothing, and
-- there is no ALTER DEFAULT PRIVILEGES line granting it anything.
ALTER DEFAULT PRIVILEGES FOR ROLE trading_owner IN SCHEMA trading
    GRANT SELECT, INSERT ON TABLES TO app_rw;

-- ===== section 7 =====
CREATE INDEX bar_daily_trading_date_idx ON trading.bar_daily (trading_date, market);
CREATE INDEX symbol_mapping_lookup_idx  ON trading.symbol_mapping (market, symbol, valid_from DESC)
    WHERE knowledge_to IS NULL;
CREATE INDEX symbol_mapping_reverse_idx ON trading.symbol_mapping (instrument_id, valid_from DESC)
    WHERE knowledge_to IS NULL;
CREATE INDEX fundamentals_asof_idx ON trading.fundamentals_snapshot
    (instrument_id, period_end DESC, disseminated_at DESC);
CREATE INDEX universe_membership_version_idx ON trading.universe_membership (universe_version, addv_rank);
CREATE INDEX universe_version_asof_idx ON trading.universe_version (market, effective_from DESC);
CREATE INDEX audit_log_run_idx ON trading.audit_log (run_id, occurred_at);
CREATE INDEX audit_log_counter_idx ON trading.audit_log (event_class, occurred_at DESC)
    WHERE event_class IN ('NAV','RISK','KILL_SWITCH');
CREATE INDEX order_intent_open_idx ON trading.order_intent (state, market)
    WHERE state NOT IN ('FILLED','CANCELED','REJECTED','EXPIRED','REPLACED');
CREATE INDEX order_intent_unknown_idx ON trading.order_intent (instrument_id) WHERE state = 'UNKNOWN';
CREATE INDEX lot_fifo_idx ON trading.lot (instrument_id, pool_id, opened_on, lot_id)
    WHERE quantity_remaining > 0;
CREATE INDEX position_unreconciled_idx ON trading.position_state (pool_id) WHERE state = 'UNRECONCILED';
CREATE INDEX news_pit_idx ON trading.news_item (first_seen_at DESC) WHERE revision_seq = 1;
CREATE INDEX fill_order_idx ON trading.fill (order_id);
CREATE INDEX llm_call_spend_idx ON trading.llm_call (called_at DESC) WHERE replay_job_id IS NULL;

-- ===== section 8.2 =====
-- OverfillError at the database level. A DEFERRABLE constraint trigger, because a
-- partial fill and the order's cached filled_quantity update land in one
-- transaction and the intermediate state is legitimately inconsistent.
CREATE OR REPLACE FUNCTION trading.assert_no_overfill() RETURNS trigger
LANGUAGE plpgsql SET search_path = trading, pg_temp AS $$
DECLARE
    v_ordered numeric(18,6);
    v_filled  numeric(18,6);
BEGIN
    SELECT quantity INTO v_ordered FROM trading.order_intent WHERE order_id = NEW.order_id;
    SELECT coalesce(sum(quantity), 0) INTO v_filled FROM trading.fill WHERE order_id = NEW.order_id;
    IF v_filled > v_ordered THEN
        RAISE EXCEPTION
            'OverfillError: order % filled %, ordered % — position is UNRECONCILED and the pool denies new entries',
            NEW.order_id, v_filled, v_ordered
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END $$;

CREATE CONSTRAINT TRIGGER fill_no_overfill
    AFTER INSERT ON trading.fill
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION trading.assert_no_overfill();

-- ===== section 8.3 =====
-- [RS §13] requires structured theses with invalidation conditions for every
-- position. A thesis that cannot be falsified is not a thesis. DEFERRED, because
-- the thesis row necessarily precedes its condition rows in the same transaction.
CREATE OR REPLACE FUNCTION trading.assert_thesis_falsifiable() RETURNS trigger
LANGUAGE plpgsql SET search_path = trading, pg_temp AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM trading.invalidation_condition WHERE thesis_id = NEW.thesis_id) THEN
        RAISE EXCEPTION 'thesis % has no invalidation condition; a thesis that cannot be falsified is not a thesis',
            NEW.thesis_id USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END $$;

CREATE CONSTRAINT TRIGGER thesis_must_be_falsifiable
    AFTER INSERT ON trading.thesis
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION trading.assert_thesis_falsifiable();

-- ===== section 8.4 =====
-- §3.1's single permitted mutation, enforced. Any UPDATE touching a fact column,
-- or re-closing an already-closed row, raises. This is what makes "restatements
-- are new rows" a property of the database rather than a property of the ORM.
CREATE OR REPLACE FUNCTION trading.assert_bitemporal_close_only() RETURNS trigger
LANGUAGE plpgsql SET search_path = trading, pg_temp AS $$
BEGIN
    IF OLD.knowledge_to IS NOT NULL THEN
        RAISE EXCEPTION 'row already closed at %; a closed knowledge interval is immutable',
            OLD.knowledge_to USING ERRCODE = 'check_violation';
    END IF;
    IF NEW.knowledge_to IS NULL THEN
        RAISE EXCEPTION 'the only permitted UPDATE on a bitemporal table is setting knowledge_to'
            USING ERRCODE = 'check_violation';
    END IF;
    -- to_jsonb minus the one mutable column must be identical on both sides.
    IF (to_jsonb(OLD) - 'knowledge_to') IS DISTINCT FROM (to_jsonb(NEW) - 'knowledge_to') THEN
        RAISE EXCEPTION 'bitemporal UPDATE altered a fact column; restatements are INSERTs, not UPDATEs'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER instrument_close_only BEFORE UPDATE ON trading.instrument
    FOR EACH ROW EXECUTE FUNCTION trading.assert_bitemporal_close_only();
CREATE TRIGGER symbol_mapping_close_only BEFORE UPDATE ON trading.symbol_mapping
    FOR EACH ROW EXECUTE FUNCTION trading.assert_bitemporal_close_only();
CREATE TRIGGER fundamentals_close_only BEFORE UPDATE ON trading.fundamentals_snapshot
    FOR EACH ROW EXECUTE FUNCTION trading.assert_bitemporal_close_only();
CREATE TRIGGER corporate_action_close_only BEFORE UPDATE ON trading.corporate_action
    FOR EACH ROW EXECUTE FUNCTION trading.assert_bitemporal_close_only();

-- ===== section 9.2 =====
-- The application can INSERT and SELECT. It cannot UPDATE, DELETE or TRUNCATE.
REVOKE ALL ON trading.audit_log FROM PUBLIC;
GRANT INSERT, SELECT ON trading.audit_log TO app_rw;
GRANT SELECT ON trading.audit_log TO metrics_ro;
-- backtest_ro gets nothing: the audit trail is not a backtest input.

-- ===== section 9.3 =====
CREATE OR REPLACE FUNCTION trading.deny_mutation() RETURNS trigger
LANGUAGE plpgsql SET search_path = trading, pg_temp AS $$
BEGIN
    RAISE EXCEPTION 'trading.% is append-only: % is not permitted ([CONST-5])',
        TG_TABLE_NAME, TG_OP USING ERRCODE = 'insufficient_privilege';
END $$;

CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON trading.audit_log
    FOR EACH ROW EXECUTE FUNCTION trading.deny_mutation();
CREATE TRIGGER audit_log_no_delete BEFORE DELETE ON trading.audit_log
    FOR EACH ROW EXECUTE FUNCTION trading.deny_mutation();
CREATE TRIGGER audit_log_no_truncate BEFORE TRUNCATE ON trading.audit_log
    FOR EACH STATEMENT EXECUTE FUNCTION trading.deny_mutation();

-- THE LINE THAT MATTERS. A normal trigger is silently skipped when
-- session_replication_role = 'replica', which any superuser can SET. ENABLE
-- ALWAYS makes the trigger fire in that mode too, closing the one bypass that
-- looks like a configuration change rather than an attack.
ALTER TABLE trading.audit_log ENABLE ALWAYS TRIGGER audit_log_no_update;
ALTER TABLE trading.audit_log ENABLE ALWAYS TRIGGER audit_log_no_delete;
ALTER TABLE trading.audit_log ENABLE ALWAYS TRIGGER audit_log_no_truncate;

-- fx_rate is immutable for the same reason (ADR-15 §5): a silently revised past
-- rate rewrites NAV history.
CREATE TRIGGER fx_rate_no_update BEFORE UPDATE ON trading.fx_rate
    FOR EACH ROW EXECUTE FUNCTION trading.deny_mutation();
CREATE TRIGGER fx_rate_no_delete BEFORE DELETE ON trading.fx_rate
    FOR EACH ROW EXECUTE FUNCTION trading.deny_mutation();
ALTER TABLE trading.fx_rate ENABLE ALWAYS TRIGGER fx_rate_no_update;
ALTER TABLE trading.fx_rate ENABLE ALWAYS TRIGGER fx_rate_no_delete;

-- I7: universe membership is point-in-time and immutable; delisted names are
-- never deleted. Same treatment.
CREATE TRIGGER universe_membership_no_update BEFORE UPDATE ON trading.universe_membership
    FOR EACH ROW EXECUTE FUNCTION trading.deny_mutation();
CREATE TRIGGER universe_membership_no_delete BEFORE DELETE ON trading.universe_membership
    FOR EACH ROW EXECUTE FUNCTION trading.deny_mutation();
ALTER TABLE trading.universe_membership ENABLE ALWAYS TRIGGER universe_membership_no_update;
ALTER TABLE trading.universe_membership ENABLE ALWAYS TRIGGER universe_membership_no_delete;

-- The financial record proper. §3.2 calls these uni-temporal append-only; the
-- GRANT block already withholds UPDATE from app_rw, so these triggers add nothing
-- against the ORDINARY path. They exist for the same reason the audit triggers do:
-- grants are bypassed by the table owner, and an altered fill or an altered NAV is
-- exactly the tamper a regulator would look for. Tamper-EVIDENT, not tamper-proof
-- (§9.6).
-- NOTE the tables deliberately ABSENT: lot (quantity_remaining decrements on FIFO
-- consumption), order_intent and position_state (state machines), account
-- (balances), and the four bitemporal tables (knowledge_to close, §8.4).
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['fill','decision','risk_evaluation','nav_pool',
                             'nav_consolidated','kill_switch_event','portfolio_snapshot']
    LOOP
        EXECUTE format(
            'CREATE TRIGGER %I_no_update BEFORE UPDATE ON trading.%I '
            'FOR EACH ROW EXECUTE FUNCTION trading.deny_mutation()', t, t);
        EXECUTE format(
            'CREATE TRIGGER %I_no_delete BEFORE DELETE ON trading.%I '
            'FOR EACH ROW EXECUTE FUNCTION trading.deny_mutation()', t, t);
        EXECUTE format('ALTER TABLE trading.%I ENABLE ALWAYS TRIGGER %I_no_update', t, t);
        EXECUTE format('ALTER TABLE trading.%I ENABLE ALWAYS TRIGGER %I_no_delete', t, t);
    END LOOP;
END $$;

-- ===== section 9.4 =====
-- seq and prev_hash are assigned HERE, not by the application. An application
-- that computes its own chain can be made to compute a wrong one; a database that
-- assigns it under a lock cannot be raced.
-- pg_advisory_xact_lock serialises the chain head. At ~0.3 writes/second
-- (15,000 events over a 14.95 h window, P0.3 §6.1) this is not a bottleneck.
CREATE OR REPLACE FUNCTION trading.audit_chain_assign() RETURNS trigger
LANGUAGE plpgsql SET search_path = trading, extensions, pg_temp AS $$
DECLARE
    v_prev text;
    v_seq  bigint;
BEGIN
    -- X2 finding H-1. The advisory lock below serialises EXECUTION, but it does not
    -- refresh a SNAPSHOT. Under REPEATABLE READ or SERIALIZABLE the SELECT that reads the
    -- chain head runs on the snapshot taken at the transaction's first statement, so a
    -- transaction that began before a concurrent writer committed reads a stale head and
    -- assigns a seq that is already taken. The primary key is (seq, occurred_at) -- forced,
    -- because a hypertable's unique index must contain the partitioning column -- so seq
    -- alone is NOT unique and nothing rejects the duplicate. Reproduced 2026-08-31: two
    -- rows at seq=2, both with prev_hash of seq=1, inserted without error.
    --
    -- timescaledb is relocatable=false and the PK cannot be narrowed, so the only place to
    -- close this is here, before the head is read. Fail closed: refuse the write.
    IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION
            'audit_log insert requires READ COMMITTED isolation, got %; a snapshot older '
            'than a concurrent commit assigns a duplicate seq and forks the chain '
            '(X2 finding H-1)',
            current_setting('transaction_isolation')
            USING ERRCODE = 'invalid_transaction_state';
    END IF;

    PERFORM pg_advisory_xact_lock(hashtext('trading.audit_log'));
    SELECT seq, payload_hash INTO v_seq, v_prev
      FROM trading.audit_log ORDER BY seq DESC LIMIT 1;

    IF v_seq IS NULL THEN
        NEW.seq       := 0;
        NEW.prev_hash := repeat('0', 64);
    ELSE
        NEW.seq       := v_seq + 1;
        NEW.prev_hash := v_prev;
    END IF;

    -- The hash covers the chain link and every field that gives the event meaning.
    -- payload::text, NOT a canonicalising function: PostgreSQL 16 has no
    -- jsonb_canonical. The application passes a PRE-CANONICALISED payload (sorted
    -- keys, Decimal as string, no insignificant whitespace) and P1.4 owns that
    -- rule. See Q-P1.2-1 — this is the interim form, and it is interim in the
    -- canonicalisation rule only, not in the chain construction.
    NEW.payload_hash := encode(digest(
        NEW.prev_hash || NEW.seq::text || NEW.event_type || NEW.event_class ||
        NEW.occurred_at::text || NEW.actor || NEW.run_id::text ||
        NEW.payload::text, 'sha256'), 'hex');
    RETURN NEW;
END $$;

CREATE TRIGGER audit_log_assign_chain BEFORE INSERT ON trading.audit_log
    FOR EACH ROW EXECUTE FUNCTION trading.audit_chain_assign();
ALTER TABLE trading.audit_log ENABLE ALWAYS TRIGGER audit_log_assign_chain;

-- ===== section 9.5 =====
CREATE OR REPLACE FUNCTION trading.verify_audit_chain(p_from bigint DEFAULT 0)
RETURNS TABLE (broken_at bigint, reason text)
LANGUAGE sql STABLE SET search_path = trading, pg_temp AS $$
    WITH ordered AS (
        -- X2 finding M-1: ORDER BY seq alone is not deterministic when a duplicate seq
        -- exists, so lag() could pair the rows either way between runs. occurred_at is
        -- the tiebreak because it is the other half of the primary key.
        SELECT seq, prev_hash, payload_hash,
               lag(payload_hash) OVER (ORDER BY seq, occurred_at) AS expected_prev,
               lag(seq)          OVER (ORDER BY seq, occurred_at) AS prior_seq
          FROM trading.audit_log WHERE seq >= p_from
    )
    -- X2 finding M-1. A duplicate seq must be reported as a duplicate. Previously it fell
    -- through to the gap branch (seq <> prior_seq + 1 is true when seq = prior_seq) and
    -- was reported as 'gap: prior seq N', sending an operator to look for a missing row
    -- that does not exist. A duplicate is the H-1 fork signature, not a gap.
    SELECT seq, 'duplicate seq: ' || count(*)::text || ' rows share this seq'
      FROM trading.audit_log WHERE seq >= p_from
     GROUP BY seq HAVING count(*) > 1
    UNION ALL
    SELECT seq, 'gap: prior seq ' || coalesce(prior_seq::text, 'NULL')
      FROM ordered
     WHERE prior_seq IS NOT NULL AND seq <> prior_seq + 1 AND seq <> prior_seq
    UNION ALL
    SELECT seq, 'fork: prev_hash does not match preceding payload_hash'
      FROM ordered WHERE expected_prev IS NOT NULL AND prev_hash <> expected_prev;
$$;