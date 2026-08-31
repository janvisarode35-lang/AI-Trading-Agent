---
id: SPEC-P1.2-STORAGE
version: 0.1
status: DRAFT
phase: P1.2 — Storage Schema
depends_on: [SPEC-P1.1-DOMAIN v0.1, SPEC-P0.1-DECISIONS v0.3, SPEC-P0.2-PROVIDERS v0.5, SPEC-P0.3-BUDGET v0.5, STAGE-0-FREEZE v1.1]
produces: [migrations/0001_initial.sql, role.trading_owner, role.app_rw, role.backtest_ro, role.metrics_ro, table.instrument, table.symbol_mapping, table.successor_link, table.exchange_session, table.tick_size_regime, table.corporate_action, table.fundamentals_snapshot, table.universe_membership, table.bar_daily, table.bar_intraday_5m, table.bar_intraday_5m_validation, table.news_item, table.fx_rate, table.candidate, table.score, table.thesis, table.invalidation_condition, table.risk_evaluation, table.decision, table.order_intent, table.fill, table.lot, table.position_state, table.portfolio_snapshot, table.nav_pool, table.nav_consolidated, table.kill_switch_event, table.audit_log, table.model_registry, table.config_version, table.llm_call, table.provider_quota_usage, table.stage_latency_observation, cagg.llm_spend_daily, cagg.audit_events_daily, cagg.bar_weekly, fn.fundamentals_asof, fn.news_asof, fn.universe_asof, fn.instrument_asof, fn.symbol_asof]
---

# SPEC-P1.2 — Storage Schema

**Phase:** Stage 1 — SPECIFY, prompt `P1.2`
**Date:** 2026-08-27
**Author role:** Database architect, PostgreSQL 16 + TimescaleDB
**Consumes:** SPEC-P1.1-DOMAIN v0.1 (DRAFT — see §0.3), plus the three frozen Stage 0 specs.

---

## 0. Governing material

### 0.1 What binds this phase

| Requirement | Source | Discharged in |
|---|---|---|
| Choose `numeric` vs `float8` for OHLC **explicitly**, with precision and scale declared; same choice in bar tables and feature views | **RULE-B3** | §4 |
| Compression ratio **measured** at day 45, ≥3 compressed chunks, live-written chunks only | **RULE-B2** | §5.3 |
| `storage.compression_after_days = 30` | P0.3 `[DEFAULT-B10]` | §5.3 |
| Action audit writes individually durable; evaluation writes may be batched | **RULE-B4** | §9.4, §10.4 |
| News revisions are **new rows**; first-seen revision is the point-in-time record | **N16** `[V]` | §3.4, §6.6 |
| EDGAR index retrievals **snapshotted immutably**, never re-derived | **N2** `[V]` | §6.5 |
| Tick size resolved by `(market, symbol, trading_date)` from `tick_size_regime` | **N10** `[V]` | §6.2 (frozen DDL adopted verbatim) |
| Universe membership point-in-time immutable; **delisted names never deleted** | **I7** | §5.4, §6.5 |
| Risk counters replayed from the audit trail, never recomputed | **I4** | §9.5 |
| Audit trail append-only and cryptographically verifiable; write **before** effect | `[CONST-5]`, ADR-10 §5 | §9 |
| Kill-switch state restored `TRIPPED` on boot | **I3** | §6.9 |
| Immutable `fx_rate`; a past rate is never re-fetched or corrected in place | ADR-15 §5 | §6.6 |
| `stage_latency_observation` becomes a hypertable on `started_at`, 7-day chunks | P0.3 §14.5 | §5.2 |
| RPO 0 for **state**; RTO-safe 30 min; RTO-operational 4 h | ADR-10 | §10.3 |
| 250 GB NVMe, 16 GB RAM, 4 vCPU | P0.3 §4.3 | §5.1, §12 |

### 0.2 Three DDL blocks are already frozen upstream and are adopted **verbatim**

`tick_size_regime` and `provider_quota_usage` (P0.2 §10.3) and `stage_latency_observation`
(P0.3 §14.5). This phase does not restate, reformat or "improve" them; it wraps them in the
migration, adds the hypertable conversion P0.3 explicitly delegated here, and adds the indexes
§7 justifies. Editing a frozen DDL block would be a silent change to a FROZEN artifact
(STAGE-0-FREEZE §1).

### 0.3 One process deviation, declared

The prompt pack's rule 3 is "**Specs before code.** A code phase may only cite a spec whose status
is `FROZEN`." P1.2 is a **spec** phase, so it may proceed on P1.1 `DRAFT` — but P1.1 has **not yet
had its `X2 — CODE REVIEW`**, and this schema is derived from it field by field. If X2 changes a
P1.1 type, this schema changes with it. That is a stated dependency, not a hidden one.

---

## 1. BLOCKING questions — and the defaults applied

| # | Question | Options | Default applied | What breaks if the default is wrong |
|---|---|---|---|---|
| **1** | How is look-ahead bias prevented — by convention, or structurally? | (a) code review and discipline; (b) **the backtest role cannot read base tables at all; only `*_asof()` functions, which require a knowledge-time argument** | **(b)** `[DEFAULT-S1]` | Under (a) the guarantee is a habit. Under (b) a backtest that forgets the cutoff gets a permission error, not silently contaminated data. Cost of (b): every backtest read goes through a `SECURITY DEFINER` function, so the function set must cover every legitimate read or the backtest is blocked |
| **2** | Two time axes or one? | (a) one (`knowledge_time`) with restatements as new rows; (b) **`valid_time` + `knowledge_time`, both closed intervals with exclusive upper bound** | **(b)** `[DEFAULT-S2]` | Fundamentals need both: a Q3 figure is *valid* for the fiscal quarter and *known* from its dissemination. Collapsing to one axis makes "what did the Q3 number look like on 15 Nov, before the January restatement" unanswerable — and that is exactly the backtest question |
| **3** | Is the market-availability cutoff the same as the knowledge cutoff? | (a) yes, one parameter; (b) **two: `p_market_asof` (rule N1 dissemination) and `p_knowledge_asof` (our ingest)** | **(b)** `[DEFAULT-S3]` | They answer different questions. `p_market_asof` prevents look-ahead against the market; `p_knowledge_asof` makes a past backtest run reproducible after we re-ingest or correct data. One parameter cannot do both, and conflating them silently makes old backtests unreproducible |
| **4** | OHLC as `numeric` or `double precision`? | (a) `float8` (92 B/row); (b) **`numeric(18,6)`** (116 B/row) | **(b) `numeric(18,6)`** `[DEFAULT-S4]` | RULE-B3 forces the explicit choice. P1.1 mandates `Decimal` for price and stores at 6 dp; `float8` cannot represent `10.005` exactly, so a tick-multiple check (rule N10) against a float column is unsound. P0.3 §2.2 already computed every figure on the 116 B branch, so the disk budget already absorbs it |
| **5** | Is `Money` one column or two? | (a) `numeric` + a currency column per amount; (b) **`numeric(18,2)` plus **one** currency column per table, with a CHECK tying it to the pool** | **(b)** `[DEFAULT-S5]` | Invariant I1 forbids cross-currency arithmetic. A per-table currency with a CHECK against `pool_id` makes a mixed-currency row unrepresentable, which is stronger than validating it in the application |
| **6** | Does `audit_log` get a retention policy? | (a) 7 years; (b) **none, ever** | **(b) none** `[DEFAULT-S6]` | `audit.retention_years = indefinite` (P0.1 §10.2). A retention policy on the audit trail would drop the rows invariant I4 replays counters from, and would break hash-chain continuity — ADR-10 §5 makes a broken chain a hard stop |
| **7** | One 5-minute bar table or two? | (a) one, with an `is_validation_slice` flag; (b) **two tables** | **(b)** `[DEFAULT-S7]` | Retention policies act on **chunks**, not rows, so a flag cannot be excluded from a drop. The held-names table gets 3-year retention; the validation slice gets none. One table means either keeping 912 MB of slice forever by accident or dropping it by accident |
| **8** | Is `synchronous_commit` global? | (a) global `on`; (b) global `off`; (c) **per-transaction: `on` for state, `off` for market-data bulk load** | **(c)** `[DEFAULT-S8]` | This is what makes ADR-10's "RPO **0 for state**" qualifier mean something (§10.3). Global `on` puts the EOD `COPY` of 3,800 rows behind a network fsync for no benefit — bars are re-fetchable. Global `off` loses committed orders on a crash, which is not survivable |
| **9** | Hash chain: one global chain or one per stream? | (a) **one global chain**, `seq` monotonic; (b) per-market or per-run chains | **(a) one global** `[DEFAULT-S9]` | A single chain gives a single verification and a single break-detection point (ADR-10 §5). Per-stream chains need a merge proof to establish global ordering, and the cost of the global chain is one serialised insert path — at 15,000 events/session over a 14.95 h window that is ~0.3 writes/second, nowhere near a bottleneck |
| **10** | Does the schema store LLM prompts and responses? | (a) hashes only; (b) **full sanitised prompt + full response, plus hashes** | **(b)** `[DEFAULT-S10]` | ADR-07 reproducibility and P4.4 output validation both need the actual text; a hash proves integrity but cannot be re-validated against a changed schema. Cost: ~300 MB at 10 years, which **P0.3 §2.2 does not line-item** — quantified as immaterial in §12.3 |

---

## 2. NON-BLOCKING details resolved

| # | Detail | Resolution |
|---|---|---|
| 1 | Interval bound convention | Every temporal interval in this schema is `[from, to)` — **inclusive lower, exclusive upper** — matching P1.1 `SymbolMapping`. `to IS NULL` means open-ended. Stated once here and never restated per table |
| 2 | `timestamptz` vs `timestamp` | **`timestamptz` everywhere.** `timestamp` without a zone is P1.1's rejected naive datetime, persisted |
| 3 | `trading_date` column type | `date`, exchange-local, never derived from a UTC timestamp (P0.1 §6) |
| 4 | Surrogate key type | `uuid` matching P1.1, **except** `audit_log.seq` which is `bigint GENERATED ALWAYS AS IDENTITY` — ordering comes from `seq`, never from a uuid |
| 5 | Enum representation | **`text` + `CHECK (col IN (...))`**, never PostgreSQL `ENUM`. A native enum cannot have a value removed and its `ALTER TYPE ... ADD VALUE` cannot run inside a transaction, which breaks Alembic's transactional migrations |
| 6 | `numeric` bounds | Every `numeric` is declared with precision and scale. **Bare `numeric` appears nowhere** — RULE-B3: it is unbounded-precision and defeats TimescaleDB's numeric compression |
| 7 | Percentage columns | `numeric(9,6)` fractions in `[0,1]`, named `*_pct`, with a `CHECK` on both bounds. Never integers-as-percent (P0.3 §15.1) |
| 8 | `NULL` vs zero | `NULL` means missing and is fail-closed; `0` means measured zero. No column uses one for the other (P1.1 §2 row 16) |
| 9 | Fillfactor | `100` on append-only tables (no HOT updates will ever occur); `90` on the four mutable tables (`order_intent`, `position_state`, `instrument`, `symbol_mapping`) so HOT updates stay in-page |
| 10 | Text length | `text` with an explicit `CHECK (length(...) BETWEEN ...)` rather than `varchar(n)`. Identical storage; the check is visible in `\d` and carries the domain reason |
| 11 | Foreign keys into hypertables | **Not used.** TimescaleDB does not support incoming FKs to hypertables. Referential integrity to `audit_log` is enforced by a `CHECK (audit_event_id IS NOT NULL)` plus the §9.5 verification job, not by an FK constraint that cannot exist |
| 12 | `ON DELETE` | Every FK is `ON DELETE RESTRICT`. There is no cascade anywhere: a cascade is a silent multi-row delete, and I7 forbids deleting reference data at all |
| 13 | Schema name | All objects in schema `trading`. `public` is left empty and `REVOKE CREATE ON SCHEMA public FROM PUBLIC` is issued, so an unqualified `CREATE TABLE` fails rather than landing in `public` |
| 14 | `search_path` | Set explicitly on every `SECURITY DEFINER` function (`SET search_path = trading, pg_temp`). Omitting it is the standard `SECURITY DEFINER` privilege-escalation hole |
| 15 | Extension placement | `timescaledb` and `btree_gist` are created in schema `extensions`, not `public`, so a `pg_dump` restore ordering problem cannot silently shadow an operator class |
| 16 | Chunk time column | Every hypertable partitions on a **UTC event timestamp**, never on `trading_date`. Chunk exclusion on a `date` column would be wrong across the DST boundary and unusable for the intraday monitor |

---

## 3. Bitemporality

### 3.1 The two axes

| Axis | Columns | Meaning | Set by |
|---|---|---|---|
| **Valid time** | `valid_from`, `valid_to` | When the fact was true **in the world** | The fact itself (fiscal period, effective date, session date) |
| **Knowledge time** | `knowledge_from`, `knowledge_to` | When **we** held that belief | The ingest transaction |

Both are `[from, to)`. `knowledge_to IS NULL` is the currently-believed row.

**Nothing is ever UPDATEd on a bitemporal table except `knowledge_to`.** A restatement is:

```sql
UPDATE trading.fundamentals_snapshot
   SET knowledge_to = now()
 WHERE instrument_id = $1 AND period_end = $2 AND knowledge_to IS NULL;
INSERT INTO trading.fundamentals_snapshot (...) VALUES (..., knowledge_from = now(), knowledge_to = NULL);
```

That is the **only** permitted mutation, and §8.4's trigger enforces it: any `UPDATE` touching a
column other than `knowledge_to`, or setting `knowledge_to` on a row that already has one, raises.

### 3.2 Which tables are bitemporal, and why

**Bitemporal** — anything a backtest reads whose value can be restated:
`fundamentals_snapshot`, `news_item`, `instrument`, `symbol_mapping`, `universe_membership`,
`corporate_action`, `tick_size_regime` (already, as `effective_from`/`effective_to`).

**Uni-temporal, append-only** — facts that cannot be restated because they are events we
generated or observed at an instant: `bar_daily`, `bar_intraday_5m`, `fill`, `audit_log`,
`llm_call`, `decision`, `risk_evaluation`, `nav_pool`, `nav_consolidated`, `kill_switch_event`.

**Mutable-with-history** — `order_intent` and `position_state` carry a current-state column
**and** every transition is an `audit_log` row. The state column is a cache of the audit trail,
never the authority (invariant I4).

`fx_rate` is **immutable, not bitemporal**: ADR-15 §5 forbids re-fetching or correcting a past
rate at all, so there is no second knowledge version to represent. A correction would be a new
`as_of_date`, which is a different fact.

### 3.3 The query pattern that structurally prevents look-ahead

Convention is not a mechanism. The mechanism is **permissions** `[DEFAULT-S1]`:

1. Base tables are owned by `trading_owner`.
2. `backtest_ro` is granted **no** privilege on any bitemporal base table.
3. `backtest_ro` is granted `EXECUTE` on `*_asof()` functions only.
4. Each function is `STABLE SECURITY DEFINER`, takes **both** cutoffs, and filters on both.

A backtest that forgets the cutoff does not get contaminated data — it gets
`ERROR: permission denied for table fundamentals_snapshot`.

```sql
-- The canonical read. Both cutoffs are mandatory arguments; neither has a default,
-- because a default cutoff is a cutoff somebody will forget to think about.
SELECT * FROM trading.fundamentals_asof(
    p_instrument_id  => $1,
    p_market_asof    => $2,   -- rule N1: dissemination cutoff, prevents look-ahead vs the market
    p_knowledge_asof => $3    -- our ingest cutoff, makes a past run reproducible
);
```

The two cutoffs answer different questions `[DEFAULT-S3]`:

| Cutoff | Prevents | Set to |
|---|---|---|
| `p_market_asof` | Reading a filing before it was public — **rule N1** | The decision instant of the simulated session |
| `p_knowledge_asof` | A re-run producing different numbers because we later re-ingested or corrected | The original run's `started_at`, from `run_context`; `now()` for a fresh run |

### 3.4 As-reported vs as-restated, worked

Amgen files Q3 on 2026-11-04, restates it on 2027-01-20. Two rows, same `period_end`:

| `restatement_seq` | `disseminated_at` | `knowledge_from` | `knowledge_to` | `revenue` |
|---|---|---|---|---|
| 1 | 2026-11-04 | 2026-11-04 21:12 | 2027-01-20 22:03 | 8,300,000,000 |
| 2 | 2027-01-20 | 2027-01-20 22:03 | `NULL` | 8,150,000,000 |

- Backtest at **2026-12-01** with `p_market_asof = 2026-12-01`: row 1 only. Row 2's
  `disseminated_at` is in the future. **Correct — as-reported.**
- Backtest at **2027-03-01**: both rows pass the market cutoff; the function returns the one with
  the highest `restatement_seq` whose `disseminated_at <= p_market_asof`, i.e. row 2.
- Re-running the December backtest in 2028 with `p_knowledge_asof = <original run start>`: row 2
  is excluded by the knowledge cutoff **as well as** the market cutoff. Belt and braces, and the
  belt matters when a restatement is back-dated by the vendor.

**News (rule N16) is the same shape with one difference:** the vendor archive is not
point-in-time, so `revision_seq = 1` is the only point-in-time record. `news_asof()` therefore
returns `revision_seq = 1` rows and **ignores later revisions entirely** for backtest reads. The
later revisions are stored — they are evidence of what the vendor did — but they are not
readable through the backtest path. This is N16's load-bearing corollary made physical.

---

## 4. Numeric types — RULE-B3 discharged explicitly

RULE-B3 requires this phase to choose, declare precision and scale, accommodate the November 2027
sub-penny regime, and apply the same choice to the bar table **and** any materialised feature view.

| Quantity | Type | Reason |
|---|---|---|
| **Price (OHLC, limit, stop, fill)** | `numeric(18,6)` | P1.1 `Price` is exactly 6 dp. `float8` cannot represent `10.005` exactly, so rule N10's exact tick-multiple test would be unsound against a float column. 6 dp covers the `$0.005` increment arriving on the first business day of November 2027 `[V]` (F-10) with 3 dp to spare |
| **Money** | `numeric(18,2)` | P1.1 `Money`, both USD and INR at 2 minor units |
| **Quantity** | `numeric(18,6)` | P1.1 `Quantity`, 6 dp, non-negative |
| **FX rate** | `numeric(18,6)` | ADR-15 §5: rates stored at 6 dp |
| **Fraction (`*_pct`, scores, confidence)** | `numeric(9,6)` | `[0,1]` with 6 dp; a percentage is never an integer here |
| **LLM cost** | `numeric(18,6)` | P0.3 §15.1: quantising `$0.00300` to cents would zero the spend model |
| **Volume** | `bigint` | Share counts are integral |

**Same choice in the continuous aggregates.** `cagg_bar_weekly` (§5.5) declares `numeric(18,6)`
for its OHLC outputs. RULE-B3's second edge case is that a feature view at a different row width
makes P0.3 §2.2 double-count; the CAGG sizing in §12 uses the same 116 B basis.

**Cost accepted.** 116 B/row against `float8`'s 92 B — a 26% width penalty on bar tables. Bar
tables are 101 MB compressed out of ~9.7 GB (P0.3 §2.3), so the penalty is **~26 MB at year 10**,
against a 250 GB disk with 4.7× headroom. Correctness wins trivially on this trade.

---

## 5. Hypertables

### 5.1 The sizing constraint

TimescaleDB's guidance is that the **uncompressed** chunks of all active hypertables should fit
comfortably in ~25% of RAM. P0.3 §4.3 fixes RAM at **16 GB**, so the budget is **~4 GB**. §5.2's
intervals are chosen against that ceiling and against the named query patterns, not by habit.

### 5.2 Chunk intervals, each justified by its query

| Hypertable | Time column | Chunk | Rows/chunk | Uncompressed chunk | Justification |
|---|---|---|---|---|---|
| `bar_daily` | `ts` | **1 month** | 31,500 | ~3.7 MB | Dominant query is ADR-14's 250-session full-universe lookback (`universe.US.min_sessions_history = 250`), which touches ~12 chunks. A 1-year chunk would be 44 MB and could not become compression-eligible until the whole chunk was 30 days past its end; a 1-day chunk would mean 2,520 chunks in 10 years |
| `bar_intraday_5m` | `ts` | **7 days** | 9,750 | ~1.1 MB | Monitor query is "last N 5-minute bars for the ~25 held names, this session" — served from exactly one chunk, always the newest and always uncompressed |
| `bar_intraday_5m_validation` | `ts` | **7 days** | 78,000 | ~9 MB | Same shape, read as a full 2-year sweep by P5.2. 104 chunks; chunk exclusion is irrelevant to a full sweep but the interval matches the sibling table so one code path serves both |
| `audit_log` | `occurred_at` | **7 days** | 75,000 | ~75 MB | Two query shapes: hash-chain verification over a contiguous `seq` range, and counter replay over the current drawdown window. At 30-day compression ~5 chunks stay uncompressed ≈ **375 MB**, the largest single consumer of the 4 GB budget. A 1-day chunk gives 3,650 chunks in 10 years; a 1-month chunk gives a 322 MB uncompressed working set per chunk |
| `news_item` | `first_seen_at` | **1 month** | ~6,000 × rf | ~12 MB × rf | Read by `news_asof()` over a session window; written continuously at ~200/day. Monthly keeps the chunk count at 120 over 10 years |
| `llm_call` | `called_at` | **1 month** | 315 | ~2.5 MB | RULE-B9's alarm reads a trailing 30-day window — one or two chunks |
| `stage_latency_observation` | `started_at` | **7 days** | 60 | ~9 KB | **Mandated by P0.3 §14.5.** Adopted, not re-derived |
| `provider_quota_usage` | `window_start` | **1 month** | 4,380 | ~260 KB | RULE-B5's trailing rolling 30-day byte sum |

Everything else is a **plain table**. `nav_pool` at 504 rows/year and `kill_switch_event` at ~10
rows/year are not time-series workloads; making them hypertables would add chunk overhead
exceeding the data.

### 5.3 Compression

`storage.compression_after_days = 30` (P0.3 `[DEFAULT-B10]`).

| Hypertable | `segmentby` | `orderby` | Ratio basis |
|---|---|---|---|
| `bar_daily` | `instrument_id` | `ts DESC` | 15× central (P0.3 §2.1 `[A]`) |
| `bar_intraday_5m` | `instrument_id` | `ts DESC` | 15× |
| `bar_intraday_5m_validation` | `instrument_id` | `ts DESC` | 15× |
| `audit_log` | `event_class` | `seq` | 4× (text/JSONB-dominant) |
| `news_item` | `source` | `first_seen_at DESC` | 4× |
| `llm_call` | `provider_id` | `called_at DESC` | 4× |

`segmentby` is the column the query filters on; `orderby` is the column it ranges over. For
`audit_log` the segment is `event_class` rather than `run_id`, because chain verification ranges
over `seq` across all runs and a high-cardinality `segmentby` would produce one segment per run.

**RULE-B2 is written into the runbook, not just cited.** Measurement is at **day 45** (not day 30
— on day 30 the oldest chunk has only just become eligible and `hypertable_compression_stats()`
can legitimately report zero compressed chunks, which a naive reading records as a 1× ratio),
requires **≥3 compressed chunks**, and is taken on **live-written chunks only** — the 10-year
backfill arrives fully sorted and compresses better, so measuring on it would overstate the ratio
and undersize the disk. §7 Q-14 is the query.

### 5.4 Retention

| Hypertable | Policy | Authority |
|---|---|---|
| `audit_log` | **NONE. Indefinite.** | `audit.retention_years = indefinite`; invariant I4 replays counters from it; ADR-10 §5 makes a chain gap a hard stop `[DEFAULT-S6]` |
| `bar_daily` | **NONE** | Backtest history; I7 forbids deleting delisted names' data |
| `bar_intraday_5m_validation` | **NONE** | P5.2's fixed validation slice |
| `bar_intraday_5m` | **3 years** | P0.3 §2.2 provisions 3 years of held-name 5-minute data. Separate table from the validation slice precisely so this policy can exist `[DEFAULT-S7]` |
| `news_item` | **NONE** | Rule N16: our store *is* the point-in-time record. Dropping it destroys the only PIT news archive that exists |
| `llm_call` | **7 years** | `records.retention_years = 7` |
| `stage_latency_observation` | **2 years** | P0.3 §14.5 anticipates a retention policy; 2 years covers ADR-07's quarterly-retrain trend analysis |
| `provider_quota_usage` | **400 days** | RULE-B5 needs a trailing 30 days; 400 keeps a year of audit |

### 5.5 Continuous aggregates — three, each with a named consumer

| CAGG | Bucket | Consumer | Why a CAGG rather than a query |
|---|---|---|---|
| `cagg_llm_spend_daily` | 1 day | RULE-B9's two-tier alarm (WARN $5, CRITICAL $50, trailing 30 days, UTC, metered, replay-excluded) | The alarm is evaluated every scrape interval; rescanning raw `llm_call` each time is waste, and the daily bucket is exactly the grain the rule names |
| `cagg_audit_events_daily` | 1 day | P0.3 §9.4's audit-volume measurement; the answer to measurement-by-design question **Q15** | Q15 is answered "after 20 live sessions" — that is a rollup query run repeatedly against a growing table |
| `cagg_bar_weekly` | 7 days | P2.6 regime features; ADR-07's T3 universe-shock trigger | Weekly OHLCV over 1,500 names × 10 years is 3.78 M rows rescanned per call; the CAGG makes it 78,000 |

**There is deliberately no continuous aggregate for ADDV, and the reason is worth recording.**
ADR-14 defines ADDV as the **20-session median** of `close × volume` (P0.1 §6: median, not mean —
one spike must not qualify a name). Median is not an incrementally-materialisable aggregate;
computing it in a CAGG needs the TimescaleDB Toolkit's `percentile_agg`, which is a **new
dependency** `[CONST]` excludes. The scanner instead computes ADDV over 20 rows × 1,500
instruments = 30,000 rows per session, from a compressed chunk with `segmentby = instrument_id`.
That is a sub-second query once per session against a 14.95 h slack budget (P0.3 §6.1). Adding a
dependency to optimise it would be the wrong trade.

**Real-time aggregation is disabled** (`materialized_only = true`) on all three. A real-time CAGG
unions materialised buckets with a live scan of the raw table, which would let a backtest read
data past its knowledge cutoff through the aggregate — the exact bypass §3.3 exists to close.

---

## 6. Migration 0001 — complete DDL

**Assembly order.** The SQL in this document is written in the order a *reader* needs it, which is
not the order PostgreSQL needs it — `audit_log` is defined in §9 because that is where its
append-only argument belongs, but §6.10's continuous aggregate and grants both reference it.
`migrations/versions/0001_initial.sql` concatenates the fenced blocks in **this** order, and the
verification harness in §6.11 asserts that the result executes:

```
§6.0  extensions, schema, roles
§6.1  instrument, symbol_mapping, successor_link
§6.2  exchange_session, tick_size_regime (+ seed)
§6.3  corporate_action
§6.4  bar_daily, bar_intraday_5m, bar_intraday_5m_validation, fx_rate
§6.5  fundamentals_snapshot, universe_membership, universe_version, news_item, news_instrument
§6.6  candidate, score, thesis, invalidation_condition, risk_evaluation, decision
§6.7  order_intent, fill, lot, position_state, account
§6.8  nav_pool, nav_consolidated, portfolio_snapshot
§6.9  kill_switch_event, model_registry, config_version, llm_call,
      provider_quota_usage, stage_latency_observation, run_context
§9.1  audit_log                       <-- must precede §6.10
§6.10 policies, continuous aggregates, as-of functions, grants
§7    indexes
§8    constraint triggers
§9.2  audit grants
§9.3  append-only triggers
§9.4  hash-chain assignment trigger
§9.5  verify_audit_chain()
```

Everything runs in **one transaction**. `CREATE INDEX CONCURRENTLY` is not used in 0001 — the
tables are empty — and is required for every index added afterwards (§11.1).

### 6.0 Extensions, schema, roles

```sql
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
```

### 6.1 Reference: instruments, symbols, successors

```sql
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
```

### 6.2 Calendars and tick regime

```sql
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
```

### 6.3 Corporate actions

```sql
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
```

### 6.4 Market data hypertables

```sql
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
```

### 6.5 Fundamentals, universe, news

```sql
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
```

### 6.6 Analysis chain

```sql
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
```

### 6.7 Execution and accounting

```sql
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
```

### 6.8 NAV and snapshots

```sql
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
```

### 6.9 Control plane

```sql
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
```

### 6.10 Policies, continuous aggregates, as-of functions, grants

```sql
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
```

> **A later migration that adds a bitemporal table must also add its `*_asof()`
> function and grant it.** Without one, the backtest cannot read the new table at all — which is
> the correct direction of failure, and is why ASSUMPTION 1 is stated as it is.

### 6.11 What has been verified, and what has not

The prompt asks for "DDL that runs." **It has not been executed.** Docker is present on the build
host but its containerd storage layer is mounted read-only, so no PostgreSQL or TimescaleDB image
could be pulled. Saying the DDL runs would be a claim I did not test.

What **was** mechanically verified, by extracting the fenced blocks in §6's declared assembly order
and running a static validator over the result:

| Check | Result |
|---|---|
| Dollar-quote (`$$`) balance | **PASS** |
| Parenthesis balance, string literals and `$$` bodies excluded | **PASS** |
| Every statement terminated; file ends on a terminator | **PASS**, 144 statements |
| Every `REFERENCES` target defined **before** use | **PASS** |
| Every `create_hypertable` / `add_*_policy` target defined before use | **PASS** |
| Every `ALTER TABLE`, `CREATE TRIGGER`, `CREATE INDEX` target defined before use | **PASS** |
| No duplicate table or index names | **PASS** |
| Every `SECURITY DEFINER` function pins `SET search_path` | **PASS**, 12 functions |
| No bare `numeric` without precision and scale (RULE-B3) | **PASS** |
| No retention policy on `audit_log`, `bar_daily` or `news_item` | **PASS** |
| `backtest_ro` holds no table privilege ([DEFAULT-S1]) | **PASS** |
| Exactly 3 continuous aggregates, all `materialized_only` | **PASS** |
| `jsonb_canonical` absent from executable SQL | **PASS** (prose mention only) |

Inventory: **37 tables**, 3 continuous aggregates, 16 indexes, 240 `CHECK` constraints, 3
`EXCLUDE USING gist` constraints, 28 triggers (14 static + 14 created by the §9.3 loop), 12
functions.

**Three defects were found and fixed by this pass**, which is the argument for running it at all:
a `SEQUENCE` behind `audit_log.seq` that would have made `verify_audit_chain()` report a false
integrity incident after the first rolled-back write; a duplicate unique index on `(seq,
occurred_at)` shadowing the primary key; and **`lot` missing from the `UPDATE` grant**, which would
have failed every FIFO exit with `permission denied` on the first live sell.

**Q-P1.2-6** records the execution that must still happen: run the extracted migration against
`timescale/timescaledb:*-pg16`, then assert the runtime behaviours a static check cannot reach —
that the `ENABLE ALWAYS` triggers fire under `session_replication_role = 'replica'`, that the
`EXCLUDE` constraints reject an overlapping mapping, that a `DENY` verdict cannot be inserted into
`decision`, and that `backtest_ro` receives `permission denied` on a base table.

---

## 7. Indexes — each justified by a named query

Every index below exists because a specific query needs it. Indexes not on this list are not
created; an index with no named query is storage and write amplification with no consumer.

| # | Index | Query it serves |
|---|---|---|
| **Q-1** | `bar_daily` PK `(instrument_id, ts)` | `SELECT close, volume FROM trading.bar_daily WHERE instrument_id = $1 AND ts >= $2 AND ts < $3 ORDER BY ts;` — the 250-session lookback ADR-14 requires (`min_sessions_history = 250`), run 1,500 times per reconstitution |
| **Q-2** | `bar_daily_trading_date_idx (trading_date, market)` | `SELECT instrument_id, close, volume FROM trading.bar_daily WHERE trading_date = $1 AND market = $2 AND is_final;` — the nightly full-universe pull that feeds the Tier-1 screen |
| **Q-3** | `symbol_mapping_lookup_idx (market, symbol, valid_from DESC) WHERE knowledge_to IS NULL` | `SELECT instrument_id FROM trading.symbol_mapping WHERE market = $1 AND symbol = $2 AND valid_from <= $3 AND (valid_to IS NULL OR $3 < valid_to) AND knowledge_to IS NULL;` — symbol→id resolution on every vendor row ingested |
| **Q-4** | `symbol_mapping_reverse_idx (instrument_id, valid_from DESC) WHERE knowledge_to IS NULL` | `SELECT symbol FROM trading.symbol_mapping WHERE instrument_id = $1 AND valid_from <= $2 AND (valid_to IS NULL OR $2 < valid_to) AND knowledge_to IS NULL;` — id→symbol for every outbound broker order |
| **Q-5** | `fundamentals_asof_idx (instrument_id, period_end DESC, disseminated_at DESC)` | The body of `fundamentals_asof()` (§3.3): `... WHERE instrument_id = $1 AND disseminated_at <= $2 AND knowledge_from <= $3 AND (knowledge_to IS NULL OR knowledge_to > $3) ORDER BY period_end DESC, restatement_seq DESC` — run for every candidate in every backtest session |
| **Q-6** | `universe_membership_version_idx (universe_version, addv_rank)` | `SELECT instrument_id FROM trading.universe_membership WHERE universe_version = $1 ORDER BY addv_rank;` — universe resolution at the head of every pipeline run and every backtest session |
| **Q-7** | `universe_version_asof_idx (market, effective_from DESC)` | `SELECT universe_version FROM trading.universe_version WHERE market = $1 AND effective_from <= $2 ORDER BY effective_from DESC LIMIT 1;` — "which universe was in force on this decision date" |
| **Q-8** | `audit_log` PK `(seq, occurred_at)` — no separate index | `SELECT seq, prev_hash, payload_hash FROM trading.audit_log WHERE seq BETWEEN $1 AND $2 ORDER BY seq;` — hash-chain verification (ADR-10 §5), run on every boot and nightly. The partitioning column is in the key because TimescaleDB requires it in every unique index (§9.1) |
| **Q-9** | `audit_log_run_idx (run_id, occurred_at)` | `SELECT * FROM trading.audit_log WHERE run_id = $1 ORDER BY occurred_at;` — forensic reconstruction of one pipeline run |
| **Q-10** | `audit_log_counter_idx (event_class, occurred_at DESC) WHERE event_class IN ('NAV','RISK','KILL_SWITCH')` | `SELECT payload FROM trading.audit_log WHERE event_class = 'NAV' AND occurred_at >= $1 ORDER BY occurred_at;` — **invariant I4's counter replay**. Partial index because these three classes are ~2% of rows and are the only ones replayed |
| **Q-11** | `order_intent_open_idx (state, market) WHERE state NOT IN ('FILLED','CANCELED','REJECTED','EXPIRED','REPLACED')` | `SELECT * FROM trading.order_intent WHERE state NOT IN (...) AND market = $1;` — the reconciliation sweep. Partial index: open orders are a handful against 15,120 rows at 10 years |
| **Q-12** | `order_intent_unknown_idx (instrument_id) WHERE state = 'UNKNOWN'` | `SELECT 1 FROM trading.order_intent WHERE instrument_id = $1 AND state = 'UNKNOWN';` — the fail-closed check before creating any new order for an instrument (P1.1 §11.1) |
| **Q-13** | `lot_fifo_idx (instrument_id, pool_id, opened_on, lot_id) WHERE quantity_remaining > 0` | `SELECT lot_id, quantity_remaining, cost_total FROM trading.lot WHERE instrument_id = $1 AND pool_id = $2 AND quantity_remaining > 0 ORDER BY opened_on, lot_id;` — FIFO consumption on every exit fill |
| **Q-14** | *(no index — named for RULE-B2)* | `SELECT hypertable_name, number_compressed_chunks, before_compression_total_bytes, after_compression_total_bytes FROM timescaledb_information.hypertable_compression_stats;` — the day-45, ≥3-chunk compression measurement |
| **Q-15** | `position_unreconciled_idx (pool_id) WHERE state = 'UNRECONCILED'` | `SELECT 1 FROM trading.position_state WHERE pool_id = $1 AND state = 'UNRECONCILED';` — ADR-10 §2's pool-wide entry block, evaluated before every sizing request |
| **Q-16** | `news_pit_idx (first_seen_at DESC) WHERE revision_seq = 1` | The body of `news_asof()`: only `revision_seq = 1` rows are point-in-time (rule N16). Partial index keeps it to the PIT subset |
| **Q-17** | `fill_order_idx (order_id)` | `SELECT sum(quantity) FROM trading.fill WHERE order_id = $1;` — the overfill constraint trigger (§8.2) |
| **Q-18** | `llm_call_spend_idx (called_at DESC) WHERE replay_job_id IS NULL` | `SELECT sum(cost_usd) FROM trading.llm_call WHERE called_at >= now() - INTERVAL '30 days' AND replay_job_id IS NULL;` — RULE-B9's trailing-30-day alarm with the replay exclusion |

```sql
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
```

---

## 8. Constraints that encode domain invariants

§6's DDL carries 47 `CHECK`, 6 `UNIQUE` and 3 `EXCLUDE` constraints. The four the prompt names
explicitly, plus the two that need triggers because they span rows:

### 8.1 The four named invariants

| Invariant | Where | Mechanism |
|---|---|---|
| **No negative NAV** | `nav_pool`, `nav_consolidated` | `CHECK (total_value >= 0)`, plus `CHECK (peak_value >= total_value)` — a peak below the current value is the recomputation bug invariant I4 forbids, caught at write time |
| **`fill_qty <= order_qty`** | `order_intent` | `CHECK (filled_quantity <= quantity)` for the cached column, **plus** the cross-row constraint trigger in §8.2 for the sum over `fill` |
| **Unique `client_order_id` per account** | `order_intent` | `UNIQUE (account_id, client_order_id)` — rule N12's client-side dedupe key, unique per account rather than globally, because two accounts may legitimately reuse an intent id |
| **No overlapping lots** | `lot`, `symbol_mapping`, `tick_size_regime` | For lots: `UNIQUE (opening_fill_id)` — one fill opens at most one lot, so a replayed fill cannot double-count. For temporal overlap: `EXCLUDE USING gist` with `daterange(..., '[)')` on `symbol_mapping` and `tick_size_regime`, which makes P1.1's `AmbiguousSymbolError` and `AmbiguousTickRegimeError` unrepresentable rather than merely detected |

### 8.2 Cross-row: cumulative fills may not exceed the order

```sql
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
```

### 8.3 Cross-row: a thesis needs at least one invalidation condition

```sql
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
```

### 8.4 Bitemporal tables: only `knowledge_to` may ever be updated

```sql
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
```

---

## 9. `audit_log` — append-only at the database level

`[CONST-5]`: every decision is written to an append-only, cryptographically verifiable audit trail
**before it takes effect**. If the audit write fails, the action does not happen. Four independent
mechanisms, because any one of them alone has a bypass.

### 9.1 The table

```sql
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
```

> **Two notes on `seq`, because both are easy to get wrong.**
>
> 1. **The primary key must include the partitioning column.** TimescaleDB requires every unique
>    index on a hypertable to contain the partitioning column, so the key is `(seq, occurred_at)`
>    rather than `(seq)`. It serves query **Q-8** directly; no separate `audit_log_seq_idx` is
>    created, and one would be a pure duplicate.
> 2. **There is no `SEQUENCE` behind `seq`.** A PostgreSQL sequence **leaves gaps on rollback**,
>    and a gap is exactly what `verify_audit_chain()` reports as a broken chain (§9.5). `seq` is
>    assigned as `max(seq) + 1` under an advisory lock (§9.4), which is gapless because a rolled-back
>    transaction never committed a row to count. Using a sequence here would make the verifier
>    raise a false integrity incident after the first rolled-back write.

### 9.2 Mechanism 1 — grants

```sql
-- The application can INSERT and SELECT. It cannot UPDATE, DELETE or TRUNCATE.
REVOKE ALL ON trading.audit_log FROM PUBLIC;
GRANT INSERT, SELECT ON trading.audit_log TO app_rw;
GRANT SELECT ON trading.audit_log TO metrics_ro;
-- backtest_ro gets nothing: the audit trail is not a backtest input.
```

**Grants alone are not enough**, and stating why is the point: the **table owner bypasses them**.
`app_rw` is therefore deliberately *not* the owner — `trading_owner` is, and `trading_owner` is
`NOLOGIN`. That closes the ordinary path. Mechanisms 2 and 3 close the rest.

### 9.3 Mechanism 2 — triggers, enabled `ALWAYS`

```sql
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
```

### 9.4 Mechanism 3 — the hash chain, assigned by the database

```sql
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
```

> **`jsonb_canonical` does not exist in PostgreSQL 16.** `jsonb`'s own key ordering is
> deterministic for a given value, but its text rendering is not guaranteed stable across major
> versions, and a hash over an unstable rendering silently invalidates the whole chain on upgrade.
> **Resolution:** the application passes a pre-canonicalised `payload` (sorted keys, `Decimal` as
> string, no whitespace) and the trigger hashes `NEW.payload::text`. The canonicalisation rule
> belongs to P1.4, which owns the event catalogue. This is recorded as **Q-P1.2-1**, and the
> migration ships with `NEW.payload::text` until P1.4 fixes the canonical form.

### 9.5 Mechanism 4 — verification, run on boot and nightly

```sql
CREATE OR REPLACE FUNCTION trading.verify_audit_chain(p_from bigint DEFAULT 0)
RETURNS TABLE (broken_at bigint, reason text)
LANGUAGE sql STABLE SET search_path = trading, pg_temp AS $$
    WITH ordered AS (
        SELECT seq, prev_hash, payload_hash,
               lag(payload_hash) OVER (ORDER BY seq) AS expected_prev,
               lag(seq)          OVER (ORDER BY seq) AS prior_seq
          FROM trading.audit_log WHERE seq >= p_from
    )
    SELECT seq, 'gap: prior seq ' || coalesce(prior_seq::text, 'NULL')
      FROM ordered WHERE prior_seq IS NOT NULL AND seq <> prior_seq + 1
    UNION ALL
    SELECT seq, 'fork: prev_hash does not match preceding payload_hash'
      FROM ordered WHERE expected_prev IS NOT NULL AND prev_hash <> expected_prev;
$$;
```

ADR-10 §5: a broken or forked chain is a **hard stop** — no trading resumes and the break is
investigated as a potential integrity incident. The boot sequence runs this **before** it does
anything else, and a non-empty result leaves the kill switch `TRIPPED` (invariant I3, which it
already is on boot).

### 9.6 The remaining bypass, stated rather than hidden

A **superuser** can `ALTER TABLE ... DISABLE TRIGGER`, `DROP TRIGGER`, or edit the heap through
`pg_filedump`. No in-database mechanism survives a superuser. What closes it is outside the
database and belongs to P6.2: the application's role is not superuser, superuser credentials live
in Vault under ADR-09 row 11, DDL is logged via `log_statement = 'ddl'` to an off-VM sink, and the
off-VM WAL archive (§10.3) preserves a copy of every audit row that a local tamper cannot reach.
**This spec does not claim tamper-proof; it claims tamper-evident**, which is what a hash chain
plus off-VM WAL actually delivers.

---

## 10. Physical operations

### 10.1 Partitioning

Time partitioning is TimescaleDB chunking (§5.2). **No space partitioning.** TimescaleDB's
`number_partitions` exists to spread writes across parallel disks; P0.3 §4.3 specifies a single
250 GB NVMe volume, so a space dimension would add chunk count and planning cost with nothing to
spread across.

### 10.2 Vacuum

| Table class | Settings | Reason |
|---|---|---|
| Append-only (`audit_log`, `bar_*`, `fill`, `news_item`, `llm_call`) | `fillfactor = 100`, `autovacuum_vacuum_insert_threshold = 10000`, `autovacuum_vacuum_insert_scale_factor = 0` | No updates means no dead tuples, so the classic vacuum trigger never fires — but the **visibility map** still needs maintaining or index-only scans degrade, and freezing must keep pace or a 10-year table hits anti-wraparound. The insert-based trigger (PG13+) is the one that matters here |
| Mutable (`order_intent`, `position_state`, `instrument`, `symbol_mapping`, `account`) | `fillfactor = 90`, `autovacuum_vacuum_scale_factor = 0.05` | Room in-page for HOT updates; a tighter scale factor because these are small and hot |
| All | `autovacuum_freeze_max_age = 400000000`, `vacuum_freeze_min_age = 50000000` | A 10-year audit table must be frozen incrementally. The default 200 M would trigger aggressive vacuums during trading hours |

**Compressed chunks are not vacuumed** — they are immutable by construction, which is a second,
incidental benefit of the 30-day compression policy on the audit trail.

### 10.3 Backup, PITR, and the RPO actually achieved

ADR-10 fixes **RPO 0 for state**, RTO-safe 30 min, RTO-operational 4 h, with WAL continuous /
35 days, nightly base backup / 35 days, weekly VM image / 8 weeks, all off-VM.

**The qualifier "for state" is doing real work, and §1 `[DEFAULT-S8]` is what makes it true.**
Asynchronous WAL archiving cannot deliver RPO 0 — it delivers RPO = archive latency. RPO 0
requires the commit to wait for the WAL to reach durable off-VM storage. The design:

```
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'pgbackrest --stanza=trading archive-push %p'
synchronous_standby_names = 'walreceiver'   # pg_receivewal, off-VM target
synchronous_commit = on                     # cluster default
```

```sql
-- Bulk market-data load: bars are re-fetchable from the vendor, so paying a
-- network fsync per COPY buys nothing. NOT state.
SET LOCAL synchronous_commit = 'off';
COPY trading.bar_daily FROM STDIN;

-- State: audit, orders, fills, NAV, kill switch. Commit waits for the WAL to
-- reach the off-VM receiver. THIS is where RPO 0 comes from.
SET LOCAL synchronous_commit = 'remote_write';
INSERT INTO trading.audit_log (...) VALUES (...);
```

| Path | `synchronous_commit` | RPO | Justification |
|---|---|---|---|
| `audit_log`, `order_intent`, `fill`, `nav_*`, `kill_switch_event`, `lot` | `remote_write` | **0** for committed transactions | ADR-10 "RPO 0 **state**" |
| `bar_*`, `news_item`, `fundamentals_snapshot`, `provider_quota_usage` | `off` | Up to `wal_writer_delay` + archive latency | Re-fetchable from the vendor; a lost bar is re-ingested, not lost |

**The failure mode is fail-closed and correct.** If the off-VM WAL receiver is unreachable, state
commits **block**. The application cannot write an audit row, so by `[CONST-5]` the action does
not happen. A trading system that cannot durably record cannot trade. This is `[CONST-6]`
behaving exactly as intended, at the storage layer.

**The cost, stated.** Blocking commits add network round-trip latency to the state path. P0.3
§6.1 gives the daily path ~14.95 h of slack, so it is immaterial there. **P0.3 §6.2's intraday
exit budget is 5 s soft / 10 s hard**, and a blocking commit sits inside it. At a same-region
receiver this is single-digit milliseconds; across regions it is not. **Q-P1.2-2** records the
measurement that must happen before go-live.

**PITR.** `pgbackrest` with a nightly `--type=full`, WAL retained 35 days, restore target by time
or LSN. RTO-operational 4 h = VM rebuild + base restore + WAL replay + human reconciliation,
unchanged from ADR-10. **Restore drills are monthly** (`dr.restore_drill_cadence = monthly`) and
a drill that does not end in a successful `verify_audit_chain()` (§9.5) is a failed drill.

### 10.4 RULE-B4 in the write path

Action-class events (`event_class = 'ACTION'`) are written one transaction each at
`synchronous_commit = remote_write`. Evaluation-class events are batched. Three boundaries, from
RULE-B4 and enforced in P1.4's writer rather than the schema:

(a) an evaluation that becomes the reason for an action is **promoted to `ACTION`** and written
durably before the decision that cites it; (b) a batch that fails midway is **discarded and
retried whole** — a half-written screen is not a screen; (c) all batches **flush before
`AUDIT_FREEZE`**, so no evaluation is still buffered when the order list seals.

---

## 11. Migrations (Alembic)

### 11.1 Ordinary rules

- One Alembic revision per logical change; `down_revision` always set; no branching.
- Every migration runs in a **transaction**. This is why §2 row 5 uses `text` + `CHECK` rather
  than native `ENUM`: `ALTER TYPE ... ADD VALUE` cannot run in a transaction block.
- DDL and data migrations are **separate revisions**. A revision that both alters a table and
  rewrites its rows cannot be rolled back cleanly.
- `CREATE INDEX CONCURRENTLY` requires `autocommit_block()` and is used for every index added
  after 0001 — the tables will not be empty then.
- Every revision is applied by `trading_owner`, never by `app_rw`.

### 11.2 The special rule for audit tables

A migration touching `audit_log`, `kill_switch_event`, `fx_rate` or `universe_membership` is
governed differently, because these tables are append-only **including their shape**:

1. **Additive only.** `ADD COLUMN` with a non-volatile default (PG11+ does not rewrite the heap).
   `ALTER COLUMN ... TYPE`, `DROP COLUMN` and `RENAME` are **forbidden** — each rewrites or
   reinterprets rows whose hashes were computed over the old shape, silently invalidating every
   `payload_hash` before the change.
2. **A shape change that cannot be additive is not a migration.** It is a new table plus a
   **chain-linking event**: the final `audit_log` row records the new table's identity and its
   genesis `prev_hash` is the old chain's last `payload_hash`. The chain continues across the
   table boundary; the rows do not move.
3. **Verify before and after.** The revision's `upgrade()` calls `verify_audit_chain()` as its
   first and last statement. A non-empty result aborts the migration.
4. **ADR-09 row 10 approval.** Deploying any code to the production VM requires Owner approval;
   a migration touching an audit table is explicitly in scope, with no SLA.
5. **The migration is itself an audit event**, written after the chain re-verifies.

```python
def upgrade() -> None:
    _assert_chain_intact()                       # rule 3, before
    op.add_column("audit_log",
                  sa.Column("event_subclass", sa.Text(), nullable=True),
                  schema="trading")              # rule 1: additive, nullable, no rewrite
    _assert_chain_intact()                       # rule 3, after
    _write_migration_audit_event()               # rule 5

def downgrade() -> None:
    raise RuntimeError(
        "audit tables do not downgrade: dropping a column rewrites rows whose hashes "
        "were computed over the old shape (SPEC-P1.2 §11.2 rule 1)")
```

---

## 12. Expected rows and on-disk size

### 12.1 Basis

252 sessions/year (P0.3 §2.2). Row widths per §4 and P0.3 §2.1 (28 B tuple overhead + column
data). Compression 15× for numeric time-series, 4× for text/JSONB-dominant `[A]` — **to be
measured at day 45 per RULE-B2, not trusted**.

### 12.2 Per table

| Table | Rows/yr | Rows @10y | Row width | Raw @1y | Raw @10y | Compressed @10y |
|---|---|---|---|---|---|---|
| `audit_log` | 3,780,000 | 37,800,000 | ~1,000 B | 3.78 GB | **37.8 GB** | **9.45 GB** |
| `bar_intraday_5m_validation` | one-off | 7,862,400 | 116 B | 912 MB | 912 MB | 61 MB |
| `bar_daily` | 378,000 | 3,780,000 | 116 B | 43.8 MB | 438 MB | 29 MB |
| `bar_intraday_5m` | 491,400 | 1,474,200 (3 y) | 116 B | 57 MB | 171 MB | 11 MB |
| `universe_membership` | 78,300 | 783,000 | 40 B | 3.1 MB | 31 MB | 8 MB |
| `news_item` | 73,000 × rf | 219,000 × rf (3 y fwd) | 2,000 B | 146 MB × rf | 438 MB × rf | 125 MB × rf |
| `score` | 94,500 | 945,000 | 150 B | 14 MB | 142 MB | 36 MB |
| `provider_quota_usage` | 52,560 | 525,600 | 60 B | 3.1 MB | 31 MB | 8 MB |
| `candidate` | 31,500 | 315,000 | 100 B | 3.1 MB | 31 MB | 8 MB |
| `corporate_action` | 9,000 | 90,000 | 200 B | 1.8 MB | 18 MB | 5 MB |
| `fundamentals_snapshot` | 9,000 | 90,000 | 1,500 B | 13.5 MB | 135 MB | 45 MB |
| `risk_evaluation` | 7,560 | 75,600 | 400 B | 3.0 MB | 30 MB | 8 MB |
| `decision` | 5,040 | 50,400 | 300 B | 1.5 MB | 15 MB | 4 MB |
| `llm_call` | 3,780 | 37,800 | 8,000 B | 30 MB | **300 MB** | **75 MB** |
| `thesis` | 3,780 | 37,800 | 4,000 B | 15 MB | 151 MB | 38 MB |
| `stage_latency_observation` | 3,024 | 30,240 (2 y policy) | 150 B | 0.45 MB | 0.9 MB | 0.3 MB |
| `fill` | 2,268 | 22,680 | 200 B | 0.45 MB | 4.5 MB | 1.2 MB |
| `lot` | 2,268 | 22,680 | 250 B | 0.57 MB | 5.7 MB | 1.5 MB |
| `order_intent` | 1,512 | 15,120 | 400 B | 0.6 MB | 6 MB | 1.5 MB |
| `exchange_session` | 1,008 | 10,080 | 150 B | 0.15 MB | 1.5 MB | 0.4 MB |
| `nav_pool` | 504 | 5,040 | 200 B | 0.1 MB | 1.0 MB | 0.3 MB |
| `portfolio_snapshot` | 504 | 5,040 | 150 B | 0.08 MB | 0.8 MB | 0.2 MB |
| `fx_rate` | 252 | 2,520 | 100 B | 0.03 MB | 0.25 MB | 0.06 MB |
| `nav_consolidated` | 252 | 2,520 | 250 B | 0.06 MB | 0.6 MB | 0.2 MB |
| `position_state` | ~1,000 | ~10,000 | 200 B | 0.2 MB | 2 MB | 0.5 MB |
| `symbol_mapping` | ~4,000 | ~12,000 | 120 B | 0.5 MB | 1.4 MB | 0.4 MB |
| `instrument` | ~3,000 | ~8,000 | 500 B | 1.5 MB | 4 MB | 1 MB |
| `tick_size_regime` | 1 → 3,000 from Nov 2027 | ~24,000 | 80 B | negligible | 1.9 MB | 0.5 MB |
| `config_version` | ~50 | ~500 | 2,000 B | 0.1 MB | 1 MB | 0.25 MB |
| `model_registry` | ~8 | ~80 | 300 B | negligible | 0.02 MB | negligible |
| `kill_switch_event` | ~10 | ~100 | 250 B | negligible | 0.03 MB | negligible |
| **TOTAL** | | **~53.5 M** | | **~5.0 GB** | **~40.5 GB** | **~9.9 GB** |

Against P0.3 §2.2's independently-derived **~52.5 M rows / ~39.9 GB raw / ~9.7 GB compressed**,
this schema lands at **~53.5 M / ~40.5 GB / ~9.9 GB** — a **+2.0% / +1.5% / +2.1%** deviation,
inside the noise of the row-width model. **P0.3's disk conclusion survives unchanged.**

### 12.3 The one line P0.3 omits

**`llm_call` payload storage is not line-itemed in P0.3 §2.2.** `[DEFAULT-S10]` stores full
sanitised prompts and responses for ADR-07 reproducibility and P4.4 validation, at ~8 KB/row ×
3,780 rows/year = **300 MB raw / 75 MB compressed at year 10**. Against the 250 GB disk with 4.7×
headroom that is **0.75% of raw application data — immaterial**, and it does not move P0.3's
conclusion. Reported rather than absorbed silently, because P0.3 §2.2 presents itself as the
complete provisioned list and a later reader would otherwise find an uncosted table.

### 12.4 Against the disk budget

P0.3 §2.3's year-10 on-VM total is **~52.7 GB** against a **250 GB** volume (4.7× headroom on the
70%-full rule). This schema adds 75 MB compressed. **No change to the VM specification.**

---

## 13. Error paths, with fail-closed behaviour

| # | Condition | Detection | Fail-closed behaviour |
|---|---|---|---|
| 1 | Audit chain gap or fork | `verify_audit_chain()` on boot and nightly | **Hard stop.** Kill switch stays `TRIPPED`; no trading resumes; integrity incident (ADR-10 §5) |
| 2 | Audit write fails (disk, WAL receiver, constraint) | Transaction aborts | The action does not happen `[CONST-5]`. The caller must not catch and continue |
| 3 | Off-VM WAL receiver unreachable | State commit blocks | Trading halts by starvation. Correct: a system that cannot record cannot trade (§10.3) |
| 4 | Overfill | §8.2 constraint trigger | Transaction aborts; position → `UNRECONCILED`; pool denies new entries |
| 5 | Duplicate `(broker_id, broker_fill_id)` | `fill_dedupe` unique | Insert is a **no-op**, not an error — brokers legitimately re-send on reconnect |
| 6 | Duplicate `(account_id, client_order_id)` | unique constraint | Order not placed. Rule N12's client-side dedupe working as designed |
| 7 | Two open symbol mappings for one `(market, symbol)` | `EXCLUDE USING gist` | Insert rejected. `AmbiguousSymbolError` is unrepresentable |
| 8 | Overlapping tick regimes | `EXCLUDE USING gist` | Insert rejected |
| 9 | No tick regime row for `(market, symbol, trading_date)` | Empty lookup | **DENY.** Never defaults to `0.01` |
| 10 | No session row for `(exchange, trading_date)` | Empty lookup | **DENY** for that market. Never inferred, never assumed open or closed |
| 11 | Missing FX rate for the accounting date | `nav_consolidated` insert has empty `fx_rate_ids` with a non-USD pool | **No new entries in EITHER pool** (invariant I10). Never carried forward, never interpolated |
| 12 | `Decision` constructed from a `DENY` verdict | `CHECK (risk_decision = 'ALLOW')` | Insert rejected. Unrepresentable, not merely validated |
| 13 | Bitemporal `UPDATE` touching a fact column | §8.4 trigger | Rejected. Restatements are `INSERT`s |
| 14 | `UPDATE`/`DELETE`/`TRUNCATE` on `audit_log` | Grants + `ENABLE ALWAYS` trigger | Rejected in both normal and `session_replication_role = replica` modes |
| 15 | Backtest reads a base table directly | No grant to `backtest_ro` | `permission denied`. Look-ahead is a permission error, not silent contamination |
| 16 | Disk ≥ 70% / ≥ 85% of the PostgreSQL volume | P6.1, 5-minute median | WARN / CRITICAL (P0.3 §15.1). Median, so a base-backup staging spike does not page at 02:00 |
| 17 | Compression measured before day 45 or on < 3 chunks | RULE-B2 | The measurement is discarded, not recorded. A 1× reading would undersize the disk |
| 18 | A migration touching an audit table fails chain verification | §11.2 rule 3 | Migration aborts and rolls back |
| 19 | `numeric` overflow on a price or money column | Column precision | Insert rejected. `numeric(18,6)` holds prices to 10^12; an overflow is a unit error upstream |
| 20 | Champion model without walk-forward evidence | `model_champion_has_evidence` | Insert rejected. ADR-08's ≥34 windows / ≥1,000 trades / Owner approval is a schema constraint, not a process |

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | **Look-ahead prevention is a GRANT, not a convention** — `backtest_ro` cannot read base tables, only `*_asof()` | A discipline is forgotten once and the result is a silently optimistic backtest that nobody can distinguish from a good one | Yes | **Critical.** This is the mechanism the entire promotion process rests on |
| 2 | **Two cutoffs, `p_market_asof` and `p_knowledge_asof`** | They prevent different failures: look-ahead vs the market (rule N1), and irreproducibility after a re-ingest | Yes | High — one parameter silently makes old backtests unreproducible |
| 3 | **OHLC is `numeric(18,6)`, not `float8`** (RULE-B3) | `float8` cannot represent `10.005` exactly, so rule N10's exact tick test is unsound against it. P0.3 already costed the 116 B branch | Yes | High — a float price column makes every tick-multiple check probabilistic |
| 4 | **Native `ENUM` is used nowhere; `text` + `CHECK` everywhere** | `ALTER TYPE ... ADD VALUE` cannot run inside a transaction, which breaks Alembic's transactional migrations | Yes | Medium |
| 5 | **`audit_log` has no retention policy, ever** | Invariant I4 replays counters from it; ADR-10 §5 makes a gap a hard stop | **No** | Critical |
| 6 | **Two 5-minute bar tables**, not one with a flag | Retention acts on chunks, not rows; a flag cannot be excluded from a drop | Yes | Medium — either 912 MB kept by accident or the validation slice dropped by accident |
| 7 | **Per-transaction `synchronous_commit`**: `remote_write` for state, `off` for market data | This is what makes ADR-10's "RPO 0 **for state**" achievable on a single VM. Bars are re-fetchable; orders are not | Yes | **Critical** — global `off` loses committed orders on a crash |
| 8 | **Blocking state commits when the WAL receiver is unreachable is the CORRECT failure** | A system that cannot durably record cannot trade — `[CONST-5]` and `[CONST-6]` at the storage layer | Yes | High — the alternative is trading with an unrecorded audit trail |
| 9 | **`seq` and `prev_hash` are assigned by a database trigger under an advisory lock**, not by the application | An application that computes its own chain can be made to compute a wrong one; a serialised database assignment cannot be raced | Yes | High |
| 10 | **`ENABLE ALWAYS TRIGGER` on every append-only table** | A normal trigger is silently skipped under `session_replication_role = 'replica'`, which is a `SET`, not an exploit | Yes | High — it is the bypass that looks like configuration |
| 11 | **Tamper-EVIDENT is claimed; tamper-PROOF is not** (§9.6) | No in-database mechanism survives a superuser. Saying otherwise would be the kind of claim a regulator tests | n/a | Medium — an overclaim here is worse than the gap |
| 12 | **`EXCLUDE USING gist` on `symbol_mapping` and `tick_size_regime`** | Makes P1.1's `AmbiguousSymbolError` and `AmbiguousTickRegimeError` unrepresentable rather than detected after the fact | Yes | High — ambiguous identity silently corrupts every backtest |
| 13 | **No continuous aggregate for ADDV** | The 20-session **median** is not incrementally materialisable without the TimescaleDB Toolkit, a new dependency `[CONST]` excludes. 30,000 rows/session is sub-second | Yes | Low — if it ever binds, the fix is a plain materialised view refreshed weekly |
| 14 | **`materialized_only = true` on all three CAGGs** | A real-time CAGG unions materialised buckets with a live raw scan, which would let a backtest read past its knowledge cutoff through the aggregate | Yes | High — it is a silent bypass of decision 1 |
| 15 | **`ON DELETE RESTRICT` everywhere; no cascade** | A cascade is a silent multi-row delete, and I7 forbids deleting reference data at all | Yes | Medium |
| 16 | **Audit-table migrations are additive-only; a shape change is a new table plus a chain-link event** | A rewrite invalidates every `payload_hash` computed over the old shape | **No** | Critical |
| 17 | **`llm_call` stores full prompt and response text** | ADR-07 reproducibility and P4.4 validation need the text; a hash proves integrity but cannot be re-validated | Yes | Low — 75 MB compressed at year 10 |
| 18 | **`portfolio_snapshot` CHECKs `gross = net` and `gross <= 1.0`** | ADR-12 long-only cash makes gross ≡ net ≤ 1.0×; P0.1 §C-2 keeps `[CONST]`'s 2× as an unreachable config ceiling | Yes | Medium — the check would need relaxing on an ADR-12 revisit, which is the point |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | `[DEFAULT-S1]` `SECURITY DEFINER` as-of functions cover every legitimate backtest read | The full backtest read set is P5.1's, not written yet | Review against P5.1's queries at its freeze | A missing function blocks a backtest — loud and safe, which is the intended direction of failure |
| 2 | `[DEFAULT-S4]` 6 dp is enough price precision through the November 2027 regime | F-10 `[V]` gives `$0.005`; no vendor documents a maximum precision | P1.1 Q-P1.1-6: `max(scale(price))` over a month of prints | Truncation on a higher-precision vendor. Detected by the P2.2 quality gate |
| 3 | 15× / 4× compression ratios | P0.3 §2.1 `[A]`; not yet measured on this schema | RULE-B2: day 45, ≥3 chunks, live-written only (query Q-14) | At 8× overall, year-10 compressed is ~19 GB and on-VM ~62 GB — still 4× headroom on 250 GB |
| 4 | ~1,000 B mean `audit_log` row | P0.3 §2.1 `[A]`, and it is that document's single most load-bearing assumption | Measurement-by-design **Q15**, after 20 live sessions, via `cagg_audit_events_daily` | P0.3 §9.4 already stress-tests to 10×: at 150,000 events/session the 250 GB volume needs resizing. Below 5× it holds |
| 5 | ~8 KB mean `llm_call` row | Q14's default of 6,000 in / 1,500 out tokens, not yet measured | Measurement-by-design **Q14**, first 50 live gate calls | 4× would be 300 MB compressed — still immaterial |
| 6 | ~200 news items/day with revision factor `rf` unmeasured | P0.3 §2.2; `rf` is carried open item **M-12** | Count revision rows after 3 months of forward collection | At `rf = 3`, +250 MB compressed. P0.3 already declares this immaterial against 4.7× headroom |
| 7 | `pgbackrest` is the archive tool | ADR-10 specifies the schedule and retention, not the tool | P6.4 deployment | Any tool with WAL push and PITR substitutes; `archive_command` is one line |
| 8 | An off-VM WAL receiver is reachable with low enough latency for the 5 s intraday budget | ADR-10 requires off-VM; P0.3 §6.2 sets the budget; neither measured the interaction | **Q-P1.2-2** — measure commit latency to the chosen target before go-live | If it exceeds the budget, the intraday exit path moves to `local` durability with a stated, audited RPO > 0 for exits only — a real reduction in ADR-10's guarantee that must be taken as a decision, not absorbed |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| **Q-P1.2-1** | ~~What is the canonical JSON serialisation the hash chain covers?~~ | **CLOSED 2026-08-27 by SPEC-P1.4 §6.2** | **`jcs-nonum-1`** — RFC 8785 JCS with JSON numbers banned (every numeric is a string), sorted keys, no insignificant whitespace, UTF-8. The application supplies the canonical string and the hash covers that, so `jsonb`'s text rendering never enters and a Postgres major upgrade cannot invalidate history. `audit.events.canonical_json()` is the implementation | **Closed.** P1.2's §9.4 trigger comment describing `NEW.payload::text` as interim is now resolved |
| **Q-P1.2-2** | What is the commit latency to the off-VM WAL receiver, and does it fit P0.3 §6.2's 5 s intraday exit budget? | Measurement, on the chosen infrastructure | `pgbench -c1 -t1000` on a single-row insert at `synchronous_commit = remote_write`, against the real target | **P6.4/P6.5 go-live.** If it does not fit, ADR-10's RPO 0 and P0.3's exit budget are in direct tension and one must be amended by the Owner |
| **Q-P1.2-3** | Does TimescaleDB compression on `audit_log` interact with the `ENABLE ALWAYS` deny-mutation triggers? | TimescaleDB documentation and a test | Compress a chunk, then attempt `UPDATE`/`DELETE` against it; confirm the trigger still fires and that the compression job itself is not blocked by it | **P1.4 / P6.4.** A compression job blocked by our own trigger would silently stop compressing and the disk model would drift |
| **Q-P1.2-4** | What is the real mean `audit_log` row width and events/session? | Measurement-by-design **Q15** | `cagg_audit_events_daily` after 20 live sessions | Not blocking. Feeds P0.3 §9.4's sensitivity and the T4 re-open trigger |
| **Q-P1.2-5** | Is `pg_advisory_xact_lock` on the chain head acceptable under the P1.4 writer's concurrency? | P1.4 design + load test | Measure insert throughput at the expected 15,000 events over a 14.95 h window (~0.3/s) and at the 10× stress case (~3/s) | **P1.4.** At 10× it is still far from contended, but the number should be measured rather than argued |
| **Q-P1.2-6** | Does migration 0001 execute, and do its runtime behaviours hold? | Execution against `timescale/timescaledb:*-pg16` | Run the extracted migration, then assert: `ENABLE ALWAYS` triggers fire under `SET session_replication_role = 'replica'`; `EXCLUDE` rejects an overlapping symbol mapping; a `DENY` verdict cannot be inserted into `decision`; `backtest_ro` gets `permission denied` on a base table; the overfill trigger fires on a deferred commit | **P6.4.** Static checks pass (§6.11) but the DDL is unexecuted — Docker's storage layer is read-only on the build host |
| **M-12** *(carried)* | News revision factor `rf` | Measurement after 3 months of forward collection | `SELECT avg(max_rev) FROM (SELECT vendor_id, max(revision_seq) AS max_rev FROM trading.news_item GROUP BY vendor_id) t;` | Not blocking. P0.3 declares it immaterial |
| **Q-P1.1-1** *(carried)* | US settlement cycle and good-faith rules | Broker documentation | Feeds `exchange_session.settlement_date` | **P2.9.** This schema stores whatever the loader resolved; it asserts no cycle |

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| `trading.instrument` | table (bitemporal) | See §6.1 | P2.1, P2.2, P2.3, P3.1 |
| `trading.symbol_mapping` | table (bitemporal) | `EXCLUDE` prevents overlapping claims on `(market, symbol)` | P2.1, P5.1 |
| `trading.successor_link` | table | `(predecessor, successor, share_ratio, cash_per_share, effective_date)` | P2.1, P3.3 |
| `trading.exchange_session` | table | Explicit UTC instants + `settlement_date` + `counts_for_sequencing` | P2.1, P2.9, P3.2 |
| `trading.tick_size_regime` | table | **P0.2 frozen DDL, verbatim** + overlap `EXCLUDE` | P3.2 |
| `trading.corporate_action` | table (bitemporal) | Closed `action_type`; deny-by-default on unknown codes | P2.1, P2.4, P5.1 |
| `trading.bar_daily` | hypertable | 1-month chunks, `numeric(18,6)` OHLC, `is_final` gate | P2.1, P2.4, P5.1 |
| `trading.bar_intraday_5m` | hypertable | 7-day chunks, 3-year retention | P3.3 |
| `trading.bar_intraday_5m_validation` | hypertable | 7-day chunks, **no retention** | P5.2 |
| `trading.fundamentals_snapshot` | table (bitemporal) | `restatement_seq`; rule N1 lags to `disseminated_at` | P2.1, P2.5, P5.1 |
| `trading.news_item` | hypertable | Rule N16: revisions are new rows; `revision_seq = 1` is PIT | P2.1, P4.1, P4.3 |
| `trading.universe_membership` / `universe_version` | tables | I7: immutable, append-only, never deleted | P2.3, P5.1 |
| `trading.fx_rate` | table (immutable) | ADR-15 §5; `deny_mutation` triggers | P2.9, P6.1 |
| `trading.candidate`, `score`, `thesis`, `invalidation_condition` | tables | See §6.6 | P2.5, P2.7, P4.3, P4.4 |
| `trading.risk_evaluation` | table | Frozen verdict; `DENY` must name its constraint | P2.9, P1.4 |
| `trading.decision` | table | **`CHECK (risk_decision = 'ALLOW')`** — a denied decision is unrepresentable | P2.7, P3.2 |
| `trading.order_intent` | table | `UNIQUE (account_id, client_order_id)`; `CHECK (filled_quantity <= quantity)` | P3.2, P3.3 |
| `trading.fill` | table | `UNIQUE (broker_id, broker_fill_id)`; overfill constraint trigger | P3.2, P3.3 |
| `trading.lot` | table | `cost_total` (never per-share); wash-sale US-only; `UNIQUE (opening_fill_id)` | P3.3, P5.1, P6.3 |
| `trading.position_state` | table | `UNRECONCILED` + `position_unreconciled_idx` for the pool-wide block | P2.9, P3.3 |
| `trading.account` | table | `settled_cash` and `day_trades_5d` both present | P2.9, P3.2 |
| `trading.nav_pool` / `nav_consolidated` | tables | Local/`trading_date` vs USD/`utc_accounting_date` + `translation_effect_usd` | P2.9, P6.1 |
| `trading.portfolio_snapshot` | table | `CHECK (gross = net AND gross <= 1.0)` | P2.8, P6.1 |
| `trading.kill_switch_event` | table | `CHECK` forbids arming without an approval; no partial de-escalation | P2.10, P6.1 |
| `trading.audit_log` | hypertable | Append-only: grants + `ENABLE ALWAYS` triggers + DB-assigned hash chain | **P1.4**, every effectful phase |
| `trading.verify_audit_chain(bigint)` | function | `RETURNS TABLE (broken_at bigint, reason text)` — empty means intact | P1.4, P6.4, boot sequence |
| `trading.model_registry` | table | `CHECK` enforces ADR-08's ≥34 windows / ≥1,000 trades / approval for `CHAMPION` | P5.2, P6.6 |
| `trading.config_version` | table | `config_hash` is the FK target for `run_context` | P1.3, P6.4 |
| `trading.llm_call` | hypertable | `replay_job_id` excludes approved replay from RULE-B9's alarm | P4.3, P6.1 |
| `trading.run_context` | table | `is_paper` / `is_backtest`, mutually exclusive — makes rule N11 checkable | every phase |
| `fundamentals_asof`, `news_asof`, `universe_asof`, `instrument_asof`, `symbol_asof` | functions | `STABLE SECURITY DEFINER`, two mandatory cutoffs; **the only backtest read path** | **P5.1, P5.2** |
| `cagg_llm_spend_daily`, `cagg_audit_events_daily`, `cagg_bar_weekly` | continuous aggregates | `materialized_only = true` | P6.1, P2.6 |
| roles `trading_owner` / `app_rw` / `backtest_ro` / `metrics_ro` | roles | §6.0; `backtest_ro` has **no** base-table grant | P6.2, P6.4 |

---

**END OF SPEC-P1.2-STORAGE v0.1**
