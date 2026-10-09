---
id: SPEC-P2.1-INGEST
version: 0.4
status: DRAFT
phase: P2.1 — Data Ingestion
depends_on: [SPEC-P0.1-DECISIONS v0.3, SPEC-P0.2-PROVIDERS v0.5, SPEC-P0.3-BUDGET v0.5, SPEC-P1.1-DOMAIN v0.3, SPEC-P1.2-STORAGE v0.5, SPEC-P1.3-CONFIG v0.1, SPEC-P1.4-AUDIT v0.1, STAGE-0-FREEZE v1.1, STAGE-1-FREEZE v1.0]
produces: [migrations/0002_ingest.sql, config/ingest.yaml, src/provider/enums.py, src/provider/spec.py, src/data/, enum.IngestDataType, enum.ManifestStatus, enum.FailureKind, enum.GapKind, enum.GapState, enum.ReconKind, class.IngestConfig, class.IngestSet, class.BackfillJobRequest, class.DailyRunRequest, class.DailyRunResult, protocol.ReferenceProvider, protocol.CalendarProvider, protocol.DailyBarProvider, protocol.IntradayBarProvider, protocol.CorporateActionProvider, protocol.FundamentalsProvider, protocol.FilingsProvider, protocol.MacroProvider, protocol.FxProvider, protocol.NewsProvider, protocol.BarStream, table.ingest_manifest, table.ingest_checkpoint, table.ingest_failure, table.ingest_gap, table.ingest_reconciliation, table.provider_instrument_ref, table.raw_news_snapshot, table.macro_series, table.macro_observation, table.edgar_index_snapshot, table.edgar_filing, table.insider_filing_raw, table.corporate_action_terms, rule.IR-1..IR-21]
---

# SPEC-P2.1 — Data Ingestion

**Phase:** Stage 2 — CORE, prompt `P2.1`
**Date:** 2026-10-07
**Author role:** Data engineer building the market-data spine
**Written against:** repository `main` at `44c78ad` (Stage 1 re-frozen, STAGE-1-FREEZE §14)

> **THIS DOCUMENT IS A DRAFT.** Nothing in it may be implemented. `docs/PROMPT-PACK.md` rule 3:
> a code phase may only cite a spec whose status is `FROZEN`. No code, test, migration or
> configuration file named here exists. `migrations/0002_ingest.sql` and `config/ingest.yaml` are
> **specified, not created**.

> **Ingestion records what the vendor said and when we heard it. It decides nothing.** It never
> substitutes, carries forward, interpolates or rounds a market value; when data is absent it says
> so in a record a consumer must read. Whether the system may trade on what was ingested is
> P2.2's decision and P2.9's, not this phase's.

---

## 0. Governing material and precedence

Precedence, highest first: `docs/PROMPT-PACK.md` Block A (Constitution) → STAGE-0-FREEZE and the
three Stage 0 specs → STAGE-1-FREEZE and the four Stage 1 specs → the P2.1 phase prompt → this
document. Where the P2.1 prompt conflicts with a frozen decision, **the frozen decision wins and
the conflict is listed in §3.2**; it is not worked around.

### 0.1 Fact-labelling convention

| Tag | Meaning |
|---|---|
| `[V-P0.2]` | A provider fact verified and recorded in SPEC-P0.2 §3 or §10.4. This document verified nothing itself |
| `[FROZEN <ref>]` | A decision or number taken from a frozen spec, with its location |
| `[DEFAULT-n]` | A Block C default applied by this phase. Listed in §1 and in ASSUMPTIONS |
| `ASSUMPTION [A-n]` | A number or fact this phase had to assume. Listed in ASSUMPTIONS with how to verify it |
| `[OQ-n]` | Not known. In OPEN QUESTIONS with the exact query. **No value is supplied** |
| `[P21-n]` | An upstream defect or conflict found by this phase. Listed in §27. **None is resolved here** |

### 0.2 Gates this document does not open

From STAGE-1-FREEZE §9.2, restated, not changed:

| Gate | State | Effect on P2.1 |
|---|---|---|
| P2.1 specification | Open | This document |
| P2.1 — any code | Closed | Requires (1) this spec `FROZEN`, which requires its blocking open questions closed; (2) **X5 condition 11** landed and passed X2 |
| P2.1 — code that writes an audit event | Closed | Requires **X5 condition 9** (`Q-P1.2-7` / X3R-M1; where the reproducibility bundle is stored; who owns the audit writer). **Not decided here, and nothing in this document depends on a particular answer** |
| The first run that writes `EFFECTIVE_CONFIG_RENDERED` | Closed | X5 condition 10 (X3R-M2). Not P2.1's |
| P2.1 code that relies on `[DEFAULT-13]` | Closed | Requires `ASSUMPTION [A-10]` verified against one documented ticker-rename case (Owner decision O-9) |

### 0.3 Owner decisions this draft is built on (O-1 to O-8: 2026-10-07; O-9, O-10: 2026-10-08; O-11, O-12: 2026-10-09)

| # | Decision |
|---|---|
| O-1 | P2.1 may specify an additive, P2.1-owned migration 0002 for its own tables only. No 0001 object is modified, redefined or altered |
| O-2 | P2.1 owns the **raw first-receipt news snapshot only**. P4.1 owns `trading.news_item` semantics and rows |
| O-3 | P2.1 specifies the held-names 5-minute stream adapter and the N5 reconciliation and gap contract. P3.3 owns the monitor that consumes it |
| O-4 | Macro series and EDGAR (including Forms 3/4/5) are in scope. Quotes are out. Trades are limited to a one-month precision measurement and are not persisted |
| O-5 | A P2.1-owned provider configuration file, loaded through the existing loader mechanisms. SPEC-P1.3 and `config/policy.yaml` are not touched |
| O-6 | P2.1 owns the calendar and reference-data loaders. The calendar source stays an open question |
| O-7 | `[DEFAULT-1]` to `[DEFAULT-10]` are approved |
| O-8 | `Q-P1.2-7` / X3R-M1, OQ-12 and OQ-13 are carried with condition 9 and are not resolved in P2.1 |
| O-9 | `[DEFAULT-11]` to `[DEFAULT-16]` are approved. `[DEFAULT-13]` is conditional: `[A-10]` must be verified against one documented ticker-rename case before any P2.1 code relies on it |
| O-10 | `[OQ-21]`: a P2.1-owned 0002 table of exact corporate-action terms keyed by `action_id` (`corporate_action_terms`, §22.12). The 0001 `corporate_action` row keeps its constrained, rounded representation. SPEC-P1.1 and SPEC-P1.2 are not re-opened. `[DEFAULT-14]` is amended to match |
| O-11 | Block C correction: the blocking questions are presented as ten grouped questions with their options (§1). P2.1's reference loader writes India tick-size rows to `tick_size_regime` from the instruments dump (`[DEFAULT-17]`, rule IR-21). The wording approved was "a new row only when the value changes"; `[P21-28]` makes that unwritable, so IR-21 uses one-day rows; see O-12 |
| O-12 | IR-21's one-day row form is adopted **provisionally**. `[OQ-25]` stays open: whether the India instruments dump is available before the order window it must serve has not been verified, and no pre-open readiness is claimed. The form must be revisited if the dump is not available in time `[OQ-34]` |

### 0.4 Version history

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-10-07 | First draft (`8efcf3e`) |
| 0.2 | 2026-10-08 | Block B conformance correction and Owner decisions O-9 and O-10. Adds the request and result models (§12.3) and the field specifications (§28); replaces stub bodies with docstrings; lists `[DEFAULT-1]` to `[DEFAULT-16]` individually; writes out abbreviated lists; adds four validators that §28 relies on. Records the approval of `[DEFAULT-11]` to `[DEFAULT-16]` (O-9). Closes `[OQ-21]` (O-10): adds the table `corporate_action_terms` (§22.12) and changes `[DEFAULT-14]` for dividend amounts and split ratios from "reject" to "store exactly, 0001 row rounded and flagged" (§7.2, §8.2, §8.4). No other decision, default, rule or DDL constraint is changed |
| 0.3 | 2026-10-09 | Block C conformance correction and Owner decision O-11. Section 1 is restructured into ten grouped blocking questions with an Options column; no approved default is changed or renumbered. Section 2 gains seven non-blocking categories. Every rule gains its edge case: IR-14, IR-19, and a new edge-case column in §13.1, §16.1, §16.2, §17, §18, §19.2, §19.5 and §23.1. Adds `[DEFAULT-17]` and rule IR-21 (India tick-size loading) and findings `[P21-26]` to `[P21-28]`. No DDL is changed |
| 0.4 | 2026-10-09 | Owner decision O-12: rule IR-21's one-day row form is adopted provisionally, conditional on `[OQ-25]`. Wording only; no other rule, default or DDL is changed |

---

## 1. BLOCKING QUESTIONS — and the defaults applied

Block C: up to ten questions where two reasonable answers produce materially different designs,
each with its options, the default applied, and what breaks if the default is wrong. Related
questions are grouped as parts (a), (b), (c) of one question; every part keeps its own
`[DEFAULT-n]` marker, and no marker was renumbered when the questions were grouped. In the
Options column the options of each part are separated by semicolons. **Every default below has been
approved by the Owner**; the last column gives the date and the default numbers it covers.

| # | Question | Options | Default applied | What breaks if the default is wrong | Approved |
|---|---|---|---|---|---|
| **1** | How is a bar timed, declared final and formed? (a) What is `ts` for a daily bar `[P21-12]`? (b) When is a daily bar written as final, given insert-only storage and P0.3 Q-7 open? (c) How is a 5-minute bar formed from the `b` minute-bar stream? | (a) Session open; session close; midnight UTC. (b) Trust the scheduled fetch; re-fetch at the next session's ingest and compare. (c) Aggregate the minute bars received; fetch each 5-minute bar from REST at the window end | (a) **`regular_close_utc` of the session** `[DEFAULT-1]`; 5-minute bars keep window start, per SPEC-P0.2 §0.6. (b) **Write at the scheduled ingest; re-fetch at the next session's ingest and compare** `[DEFAULT-2]`; a difference is recorded and fails the run, as SPEC-P0.3 §13.1 row 3 already requires. (c) **Deterministic aggregation of the minute bars received for the window, as SPEC-P0.3 §6.2 fixes; completion is exactly RULE-B12** `[DEFAULT-16]` | (a) Window-start `ts` lets `bars_asof` return the day's close to a backtest asking as of that morning. (b) A bar revised by the vendor after we stored it stays wrong permanently. (c) A bar assembled across an unnoticed loss; §13.5 is the check that detects it | 2026-10-07 (1, 2); 2026-10-08 (16) |
| **2** | What happens to a vendor value that disagrees with another source, or does not fit its column? (a) Where does a second source's bar go, and who wins? (b) What is the bar tolerance? (c) How is rule N7 stored, given `[P21-3]` and `[P21-13]`? (d) A value more precise than the column that must hold it? | (a) A second row in `bar_daily`, which the one-row-per-key table cannot hold; the P2.1 reconciliation table. (b) Exact match; the tick for prices plus a ratio for volume. (c) Reuse the `restatement_seq`, which `[P21-13]` forbids; reconciliation rows plus an EDGAR row at the next sequence number. (d) Reject; round and record; keep the exact value in a P2.1 table | (a) **The P2.1 reconciliation table. Only the SPEC-P0.2 primary writes a 0001 market-data table** `[DEFAULT-3]`; P2.2 owns the accept/quarantine verdict. (b) **Price: the tick in force from `tick_size_regime`. Volume: a ratio, `ASSUMPTION [A-1]`** `[DEFAULT-4]`. (c) **Evidence in the reconciliation table; the EDGAR-sourced row at the next `restatement_seq`; the FMP row's knowledge interval closed** `[DEFAULT-5]`; the conflation is carried as `[P21-13]`. (d) **Prices, volumes and FX rates: rejected and recorded, never rounded. Dividend amounts and split ratios: the exact vendor terms are stored in `corporate_action_terms`, and the 0001 `corporate_action` row holds the value rounded half-up to its column, flagged as rounded** `[DEFAULT-14]`, as amended by O-10. `Price` and `Money` round silently (`[P21-16]`), so the check runs before either is constructed | (a) A silent tiebreak, which rule N7 forbids. (b) Too tight: constant false alarms. Too loose: real errors pass. (c) A source correction is indistinguishable from an issuer restatement. (d) A reader that takes a dividend amount or a ratio from the 0001 row while its flag is set uses a rounded value; §8.4 directs readers to the exact terms | 2026-10-07 (3, 4, 5); 2026-10-08 (14) |
| **3** | How is raw news kept away from LLM-bound code? | Schema `trading` with explicit grants and a module boundary; a separate schema or a second database role | **Schema `trading`, explicit grants, module boundary** `[DEFAULT-6]`. Limitation, stated: one application role exists, so the isolation is not enforced by the database | Raw vendor text reachable by a prompt builder (`[CONST-4]`) | 2026-10-07 |
| **4** | What does downstream see about data that is absent or old? (a) When data is absent? (b) Freshness for batch data? | (a) No row plus manifest and failure records; sentinel rows. (b) Seconds since `as_of`; presence of the datum for the most recent completed sequenced session | (a) **No row, plus a manifest and failure records. No sentinel rows** `[DEFAULT-7]`. (b) **Presence of the datum for the most recent completed sequenced session** `[DEFAULT-8]`; 600 s for the held-names stream stays as frozen | (a) A missing bar read as "did not trade". (b) A 600 s rule applied to daily bars denies every decision the next morning | 2026-10-07 (7, 8) |
| **5** | How is the India adapter tested with no India data spend? | Fixtures built from documented response shapes, labelled synthetic; buy one month of data to record; defer the adapter | **Fixtures built from documented response shapes, labelled synthetic** `[DEFAULT-9]`. Recorded fixtures are required before India activation | A synthetic fixture can encode a wrong field. See `[P21-25]`: the shapes are not yet documented in any frozen spec | 2026-10-07 |
| **6** | How does P2.1 reach its stores? (a) Which client libraries, and who owns non-audit database writes? (b) Does `ingest_manifest.run_id` reference `run_context`? | (a) Named libraries; the standard library only. (b) A foreign key; no foreign key | (a) **`psycopg` 3, `httpx`, `redis`, `websockets`; P2.1 owns a write module for the tables it writes** `[DEFAULT-10]`; the audit writer stays with condition 9. (b) **No foreign key** `[DEFAULT-15]`: a `run_context` row needs a `config_version` row, which needs an audit event (`[P21-20]`); a key would silently widen the condition 9 gate to every P2.1 write | (a) Later phases inherit the choice. (b) A manifest row whose run has no `run_context` row | 2026-10-07 (10); 2026-10-08 (15) |
| **7** | Which instruments does a daily run ingest? | An explicit set supplied by the caller; every active instrument of an allowed type; universe members resolved inside the run | **An explicit ingest set supplied to the run: universe members as of the session, plus names flagged `retained_as_held`, plus any instruments the caller adds** `[DEFAULT-11]`, typed as `IngestSet` (§12.3). When no universe version exists, the caller must supply the set; there is no implicit "everything" | Reconstitution needs bars for names outside the universe. Who requests them is `[OQ-19]` | 2026-10-08 |
| **8** | Where does `disseminated_at` come from? | An EDGAR filing record only; a vendor filing or acceptance date; our own first-retrieval time | **Only from an EDGAR filing record, through the cutoff rule of §19.2. A fundamentals row with no matching filing record is not stored** `[DEFAULT-12]` | Rule N1 look-ahead if a vendor "filing date" is trusted. Cost: fundamentals with no EDGAR match are absent | 2026-10-08 |
| **9** | How is an instrument recognised across a ticker change? | `composite_figi`; exchange and ticker only; block the reference loader until the vendor's ticker-events data is documented | **By `composite_figi` when present, `ASSUMPTION [A-10]`** `[DEFAULT-13]`. Conditional (O-9): no P2.1 code may rely on it until `[A-10]` is verified against one documented ticker-rename case | A renamed ticker becomes a delisting plus a new instrument: an identity break | 2026-10-08, conditional |
| **10** | Who loads India tick sizes `[P21-27]`? | P2.1's reference loader writes `tick_size_regime` rows from the instruments dump; leave it to P3.1 or P3.2 | **P2.1's reference loader, by rule IR-21** `[DEFAULT-17]` | With no loader, rule N10 denies every India order for want of a regime row. India is unfunded, so nothing breaks before activation | 2026-10-09: that P2.1 loads them (O-11); the one-day row form provisionally (O-12), to be revisited on `[OQ-25]` |

---

## 2. NON-BLOCKING DETAILS noticed and resolved

| Area | Resolution |
|---|---|
| Timestamps at rest | tz-aware UTC everywhere. The adapter converts; nothing downstream holds a local time `[FROZEN P1.1 §4.1]` |
| Naive timestamp from a vendor | Rejected, `FailureKind.UNDOCUMENTED_TIMEZONE`. Never coerced `[FROZEN P1.1 DEFAULT-5]` |
| Massive bar `t` | Unix milliseconds, window start, presented in Eastern Time `[V-P0.2]`. Converted with IANA zone `America/New_York`, `ASSUMPTION [A-11]` |
| Alpaca bar `t` | RFC-3339, window start `[V-P0.2 §0.6]` |
| `trading_date` | The exchange-local date of the session, taken from the request and confirmed against `exchange_session`. Never the UTC date of a timestamp |
| Window bounds | `[start, end)`. A 5-minute bar stamped `13:30Z` covers `13:30:00.000` to `13:34:59.999` |
| Expected windows | Derived from `exchange_session` UTC instants only. A half-day has 42 five-minute windows against 78 `[FROZEN P0.3 §12]`. There is no DST arithmetic at run time |
| Session length not a multiple of 300 s | `FailureKind.MISSING_SESSION`; no windows are derived. Never truncated to the last whole window |
| Split ratio | `split_to / split_from` `[V-P0.2 §0.6]`. Greater than 1 is `SPLIT`; less than 1 is `REVERSE_SPLIT`; equal to 1 is rejected |
| Dividend dates | `ex_date` ← `ex_dividend_date`; `effective_date` ← `pay_date` `[V-P0.2 §0.6]`. A dividend with no `pay_date` is rejected and recorded, not defaulted to the ex-date |
| Split dates | `ex_date` and `effective_date` ← `execution_date` |
| Dividend before the first stored bar | Stored; ignored for adjustment `[FROZEN P1.1 §5.3]` |
| Zero-volume bar | Stored as received `[FROZEN P1.1 §6.1]` |
| Volume | Integer. A non-integer volume is rejected (`PRECISION_EXCEEDED`), not rounded |
| `vw` (VWAP) | Not stored: `bar_daily` has no column. Carried in `[P21-18]` |
| `retrieved_at` | One value per HTTP response, read from the process clock when the last byte is received |
| `source` | The `ProviderId` value as text, e.g. `MASSIVE` |
| Massive `adjusted` | Sent as `false` on every aggregate request (rule N9). Set in the request builder; a request without it cannot be constructed |
| Alpaca `adjustment` | Sent explicitly as `raw`. The default is already `raw` `[V-P0.2]`; relying on a default is not accepted |
| Alpaca `feed` | Sent explicitly as `sip`. `iex` is never requested (rule N6) |
| Alpaca `asof` | Set to the bar's `trading_date` on every historical request `[V-P0.2 §3.2]` |
| Paging | Counts data points, not symbols: Alpaca max 10,000 across all symbols, Massive max 50,000 `[V-P0.2]` |
| Quota windows | Fixed UTC calendar minutes in `provider_quota_usage`. FMP uses a rolling 30-day byte sum and stops at 40 GB `[FROZEN P0.3 RULE-B5]` |
| Inclusive or exclusive | Tolerance comparisons are inclusive: a difference equal to the tolerance agrees. Stage budget breach is exclusive `[FROZEN P0.3 §15.1]` |
| Money and price arithmetic | `Decimal` only. A float anywhere in a wire record is rejected by the domain's `_reject_float` |
| News identity | `(provider_id, vendor_id, revision_seq)`. Alpaca's `id` is stored as text |
| Unknown JSON field in a vendor response | Ignored for storage, counted, and reported in the manifest's `detail`. A **missing** mapped field is a `SCHEMA_VIOLATION` |
| 0002 mutability | Every 0002 table is append-only. Corrections are new rows. No `UPDATE` grant is requested |
| Rounding mode | The only rounding P2.1 performs is half-up, and only into the two 0001 corporate-action columns (§8.2), with the exact value stored beside it. Every other value is rejected or kept exact |
| Tick size | Read from `tick_size_regime` for the bar's `trading_date`. P2.1 uses it only as the price tolerance (§14.2) and never rounds a price to a tick. India rows are loaded by IR-21 |
| Lot size | India only: the instruments dump's `lot_size` goes to `instrument.lot_size` and `instrument.qty_increment`. US `qty_increment` is 1 and `lot_size` is `NULL` `[FROZEN P1.1 DEFAULT-3]` |
| Unit of a percentage | Every ratio in `ingest.yaml` is a fraction: `volume_ratio = 0.05` means 5%. This is the convention SPEC-P0.3 §15.1 fixed for `_pct` keys; no P2.1 key holds a percent |
| DST | Never computed. Every session boundary is a UTC instant read from an `exchange_session` row; the first session after a change simply carries different instants (§11.2, test T-5) |
| Half-days | One daily bar is expected, as on a full day. Five-minute windows stop at the early close: 42, not 78. Nothing after the close is expected and nothing is a gap (§11) |
| Integer or decimal | Money and prices are `Decimal`. Volume, trade count and every manifest count are integers. Exact corporate-action terms are unconstrained `numeric`. No float is accepted anywhere |

---

## 3. Scope

### 3.1 In and out

| In scope | Out of scope, and whose it is |
|---|---|
| Provider protocols, registry and adapters | Any accept, quarantine or reject verdict on stored data — P2.2 |
| Reference data (instruments, symbols) and exchange calendar loaders | Universe reconstitution and ranking — P2.3 |
| Daily bars, US and India | Adjusted prices and features — P2.4. This phase states the read-time order only (§8.4) |
| Held-names 5-minute stream adapter; the 5-minute validation slice | The monitor, the stale-bar timer, stops and exits — P3.3, P3.4 |
| Corporate actions | Sanitising news; `news_item` and `news_instrument` rows — P4.1 |
| Fundamentals; EDGAR filings; Forms 3/4/5 raw documents | Parsing Forms 3/4/5 into features — P2.5, after `[OQ-9]` |
| Macro series at vintage | Regime detection and the choice of series — P2.6 |
| FX rate recording | Consolidated NAV — P2.9, P3.3 |
| Raw first-receipt news snapshot | The audit writer and the hash of record — condition 9 |
| Backfill, gap detection, reconciliation evidence, freshness facts, the Redis cache | Quotes (no bought tier supplies them); persisted trades |

### 3.2 Where the P2.1 prompt is overridden by a frozen decision

| Prompt text | Frozen decision | What this spec does |
|---|---|---|
| "Live streaming: subscribe, heartbeat…" (unqualified) | ADR-13/14: ingest is a nightly batch; RULE-B1: a streaming ingest path voids SPEC-P0.3 §3 | Streaming is specified for **held names only**, as SPEC-P0.3 §6.2 already budgets. No universe stream |
| "quotes" | No table; Massive Developer has no quotes `[V-P0.2 §3.3]`; no Stage 2 consumer stores them | Out of scope (O-4) |
| "upsert semantics" | `bar_*` is uni-temporal append-only; `app_rw` has no `UPDATE` on it `[FROZEN P1.2 §3.2]` | Insert-only. "Upsert" means insert-if-absent, compare-if-present (§9) |
| "when two providers disagree on the same bar… which provider wins" | One row per `(instrument_id, ts)`; one consolidated US daily source is bought | The primary always holds the stored row; the disagreement is evidence (§14) |
| "news metadata" | `news_item` requires a sanitised body; the sanitiser is P4.1 `[P21-1]` | Raw snapshot only (O-2) |
| "DELIVERABLE: … + src/data/ implementation + tests" | Pack rule 3; STAGE-1-FREEZE §9.2 | This document is the specification half only |

---

## 4. Provider protocol and registry

### 4.1 The registry is SPEC-P0.2's, unchanged

`ProviderId`, `DataCapability`, `ProviderRole`, `TokenLifetime`, `RateLimit`, `CredentialSpec`,
`IdempotencySpec` and `ProviderSpec` are implemented **verbatim** from SPEC-P0.2 §10.1–10.2 at
`src/provider/enums.py` and `src/provider/spec.py`, the module names those code blocks carry. P2.1
is their first consumer and adds no member and no field.

`DataCapability` has no member for calendars, corporate actions, FX or India reference data
(`[P21-15]`). P2.1 therefore defines its **own** enum for what it ingests and maps onto
`DataCapability` only where a member exists:

```python
# src/data/enums.py
from enum import StrEnum


class IngestDataType(StrEnum):
    """What P2.1 ingests. Persisted in every 0002 table; a member is never renamed or removed."""
    REFERENCE = "REFERENCE"                    # instruments and symbol mappings
    CALENDAR = "CALENDAR"                      # exchange_session rows
    BAR_DAILY = "BAR_DAILY"
    BAR_5M = "BAR_5M"                          # held names, stream plus REST reconciliation
    BAR_5M_VALIDATION = "BAR_5M_VALIDATION"    # P5.2's fixed slice, backfill only
    CORPORATE_ACTION = "CORPORATE_ACTION"
    FUNDAMENTALS = "FUNDAMENTALS"
    EDGAR_INDEX = "EDGAR_INDEX"
    EDGAR_FILING = "EDGAR_FILING"
    INSIDER_FILING = "INSIDER_FILING"          # Forms 3/4/5, raw document
    MACRO = "MACRO"
    FX_RATE = "FX_RATE"
    RAW_NEWS = "RAW_NEWS"
    TRADE_PRECISION_SAMPLE = "TRADE_PRECISION_SAMPLE"   # measurement only, never persisted
```

| `IngestDataType` | `DataCapability` | Provider `[FROZEN P0.2 §4.3, §7]` |
|---|---|---|
| `REFERENCE` (US) | `US_REFERENCE_DATA` | `MASSIVE` |
| `REFERENCE` (IN) | `IN_MARKET_DATA` | `ZERODHA` (instruments dump) |
| `CALENDAR` | none `[P21-15]` | **`[OQ-1]` — no frozen spec names a source** |
| `BAR_DAILY` (US) | `US_DAILY_HISTORY` | `MASSIVE` |
| `BAR_DAILY` (IN) | `IN_MARKET_DATA` | `ZERODHA` |
| `BAR_5M` | `US_REALTIME_INTRADAY` | `ALPACA_DATA`, from `[RS §12]` stage 5 `[FROZEN P0.2 DEFAULT-P9]` |
| `BAR_5M_VALIDATION` | `US_DAILY_HISTORY` | `MASSIVE` `[FROZEN P0.3 §3.4]` |
| `CORPORATE_ACTION` (US) | none `[P21-15]` | `MASSIVE` splits and dividends `[FROZEN P0.3 §3.4]`; other types `[P21-24]` |
| `CORPORATE_ACTION` (IN) | none | **`[OQ-8]`** |
| `FUNDAMENTALS` (US) | `US_FUNDAMENTALS` | `FMP` primary; `SEC_EDGAR` authority (N7) |
| `FUNDAMENTALS` (IN) | none | **`[OQ-8]`** |
| `EDGAR_*`, `INSIDER_FILING` | `FILINGS` | `SEC_EDGAR` |
| `MACRO` | `MACRO` | `FRED` |
| `FX_RATE` | none `[P21-15]` | `fx.source_primary = RBI_REFERENCE` `[FROZEN P1.3, ASSUMPTION there]`; endpoint **`[OQ-7]`** |
| `RAW_NEWS` | `NEWS` | `ALPACA_DATA` (Benzinga) |
| `TRADE_PRECISION_SAMPLE` | `US_DAILY_HISTORY` | `MASSIVE` (Developer includes Trades `[V-P0.2 §3.3]`) |

`FINNHUB` is a free supplementary source `[FROZEN P0.2 decision 8]`. No adapter is specified for
it in v0.1: nothing in this phase's scope requires it.

### 4.2 Wire records

An adapter returns **wire records**: the vendor's values, typed, with vendor field names already
translated and nothing else done. No rounding, no defaulting, no symbol resolution. The normaliser
(§7) turns wire records into domain types.

Common rules for every wire model: `model_config = ConfigDict(frozen=True, extra="forbid")`;
every `Decimal` is parsed from the vendor's **text**, never through a float; every `datetime` is
tz-aware UTC; a violation raises and the record becomes an `ingest_failure` row with
`failure_kind = SCHEMA_VIOLATION` unless a more specific kind is named.

```python
# src/data/wire.py
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

from provider.enums import ProviderId


class _Wire(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_id: ProviderId
    retrieved_at: datetime = Field(description="UTC. Process clock when the response's last byte arrived.")
    response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$",
                                 description="SHA-256 of the raw response body this record was parsed from.")


class WireBar(_Wire):
    provider_symbol: str = Field(min_length=1, max_length=32, description="The vendor's ticker, as sent.")
    window_start: datetime = Field(description="UTC. Start of the bar window, [start, end).")
    window_seconds: int = Field(description="60, 300 or 86400. Any other value is a SCHEMA_VIOLATION.")
    open: Decimal = Field(gt=0, description="Price units of the listing currency. Unadjusted.")
    high: Decimal = Field(gt=0)
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: Decimal = Field(ge=0, description="Shares. Kept as Decimal so a non-integer is detected, not truncated.")
    trade_count: int | None = Field(default=None, ge=0, description="Vendor 'n'. None when the vendor sends none.")


class WireSplit(_Wire):
    provider_symbol: str = Field(min_length=1, max_length=32)
    execution_date: date = Field(description="Exchange-local date.")
    split_from: Decimal = Field(gt=0, description="Old shares (denominator).")
    split_to: Decimal = Field(gt=0, description="New shares (numerator).")


class WireDividend(_Wire):
    provider_symbol: str = Field(min_length=1, max_length=32)
    ex_dividend_date: date
    pay_date: date | None = Field(default=None, description="None is carried here and rejected in the normaliser.")
    record_date: date | None = None
    declaration_date: date | None = None
    cash_amount: Decimal = Field(gt=0, description="Per share, listing currency, vendor precision.")
    distribution_type: str | None = Field(default=None, max_length=32)
    frequency: int | None = Field(default=None, ge=0, le=365)


class WireInstrument(_Wire):
    provider_symbol: str = Field(min_length=1, max_length=32)
    primary_exchange: str = Field(min_length=1, max_length=32, description="Vendor code, unmapped.")
    security_type: str = Field(min_length=1, max_length=32, description="Vendor code, unmapped.")
    active: bool
    currency_name: str = Field(min_length=1, max_length=16)
    cik: str | None = Field(default=None, max_length=16)
    composite_figi: str | None = Field(default=None, min_length=12, max_length=12)
    share_class_figi: str | None = Field(default=None, min_length=12, max_length=12)
    delisted_utc: datetime | None = Field(default=None, description="UTC. 'The last date that the asset was traded'.")
    as_of_date: date = Field(description="The 'date' the reference query was made for. Exchange-local.")
    lot_size: Decimal | None = Field(default=None, gt=0, description="India only, from the instruments dump.")
    tick_size: Decimal | None = Field(default=None, gt=0, description="India only, from the instruments dump.")


class WireSession(_Wire):
    exchange_code: str = Field(min_length=1, max_length=16, description="Vendor code, unmapped.")
    trading_date: date
    regular_open_utc: datetime
    regular_close_utc: datetime
    pre_market_open_utc: datetime | None = None
    post_market_close_utc: datetime | None = None
    is_half_day: bool
    is_special: bool

    @model_validator(mode="after")
    def _one_session_type(self) -> "WireSession":
        if self.is_half_day and self.is_special:
            raise ValueError("a session is a half-day or a special session, not both")
        return self


class WireNews(_Wire):
    vendor_id: str = Field(min_length=1, max_length=128)
    headline: str = Field(max_length=4000)
    author: str | None = Field(default=None, max_length=400)
    created_at: datetime = Field(description="UTC. Vendor 'created_at'.")
    updated_at: datetime | None = Field(default=None, description="UTC. Vendor 'updated_at'.")
    summary: str | None = Field(default=None, max_length=20_000)
    content: str | None = Field(default=None, max_length=1_000_000,
                                description="UNTRUSTED. May contain HTML. Bound is ASSUMPTION [A-5].")
    symbols: tuple[str, ...] = Field(default=(), max_length=200)
    source: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=2000)


class WireFundamentals(_Wire):
    provider_symbol: str = Field(min_length=1, max_length=32)
    cik: str | None = Field(default=None, max_length=16)
    period_end: date
    fiscal_period: str = Field(min_length=1, max_length=16)
    metrics: dict[str, Decimal] = Field(min_length=1, description="Metric name to value, vendor precision.")


class WireFiling(_Wire):
    filing_key: str = Field(min_length=1, max_length=64, description="The SEC's unique filing identifier. See [OQ-9].")
    cik: str = Field(min_length=1, max_length=16)
    form_type: str = Field(min_length=1, max_length=16)
    accepted_at: datetime = Field(description="UTC. The acceptance instant the cutoff rule is applied to.")
    period_end: date | None = None
    document_ref: str = Field(min_length=1, max_length=400)


class WireMacroObservation(_Wire):
    series_id: str = Field(min_length=1, max_length=64)
    observation_date: date
    vintage_date: date = Field(description="The date from which this value was the published value.")
    value: Decimal


class WireFxRate(_Wire):
    as_of_date: date
    base: str = Field(min_length=3, max_length=3)
    quote: str = Field(min_length=3, max_length=3)
    rate: Decimal = Field(gt=0)
```

`WireBar.volume`, `WireDividend.cash_amount` and every price field are deliberately wider than the
column they end in: §7.2 needs the vendor's value intact, to refuse it or to store it exactly.

### 4.3 Protocols

One protocol per data type. A provider implements only the protocols for the capabilities its
`ProviderSpec` declares. Batch protocols are synchronous; the stream is asynchronous because the
`websockets` library is.

```python
# src/data/protocols.py
from collections.abc import AsyncIterator, Sequence
from datetime import date, datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from data.wire import (WireBar, WireDividend, WireFiling, WireFundamentals, WireFxRate,
                       WireInstrument, WireMacroObservation, WireNews, WireSession, WireSplit)
from provider.enums import ProviderId


class Page[T](BaseModel):
    """One page of results. `next_cursor is None` means the provider said there is no more.
    A page that ends without that statement is INCOMPLETE_RESPONSE, never 'probably all'."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    items: tuple[T, ...]
    next_cursor: str | None = Field(default=None, max_length=2000)
    response_bytes: int = Field(ge=0, description="Bytes of the body, for provider_quota_usage and RULE-B5.")
    response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


@runtime_checkable
class ReferenceProvider(Protocol):
    provider_id: ProviderId
    def fetch_instruments(self, *, as_of_date: date, active: bool, cursor: str | None) -> Page[WireInstrument]:
        """One page of the provider's instruments as of `as_of_date`."""


@runtime_checkable
class CalendarProvider(Protocol):
    provider_id: ProviderId
    def fetch_sessions(self, *, exchange_code: str, date_from: date, date_to: date) -> Page[WireSession]:
        """Sessions of one exchange for `[date_from, date_to]`, both inclusive. A closed date is absent."""


@runtime_checkable
class DailyBarProvider(Protocol):
    provider_id: ProviderId
    def fetch_daily_bars(self, *, provider_symbol: str, date_from: date, date_to: date,
                         cursor: str | None) -> Page[WireBar]:
        """Unadjusted daily bars for one symbol, `[date_from, date_to]` both inclusive."""


@runtime_checkable
class IntradayBarProvider(Protocol):
    provider_id: ProviderId
    def fetch_intraday_bars(self, *, provider_symbols: Sequence[str], window_seconds: int,
                            start: datetime, end: datetime, symbol_asof: date,
                            cursor: str | None) -> Page[WireBar]:
        """Unadjusted bars of `window_seconds` for windows starting in `[start, end)`."""


@runtime_checkable
class CorporateActionProvider(Protocol):
    provider_id: ProviderId
    def fetch_splits(self, *, provider_symbol: str | None, date_from: date, date_to: date,
                     cursor: str | None) -> Page[WireSplit]:
        """Splits executed in `[date_from, date_to]`; every symbol when `provider_symbol` is None."""
    def fetch_dividends(self, *, provider_symbol: str | None, ex_date_from: date, ex_date_to: date,
                        cursor: str | None) -> Page[WireDividend]:
        """Dividends going ex in `[ex_date_from, ex_date_to]`; every symbol when `provider_symbol` is None."""


@runtime_checkable
class FundamentalsProvider(Protocol):
    provider_id: ProviderId
    def fetch_fundamentals(self, *, provider_symbol: str, period_end_from: date,
                           period_end_to: date) -> Page[WireFundamentals]:
        """Reported fundamentals for periods ending in `[period_end_from, period_end_to]`."""


@runtime_checkable
class FilingsProvider(Protocol):
    provider_id: ProviderId
    def fetch_index(self, *, index_kind: str, index_ref: str) -> bytes:
        """The bytes of one index, exactly as served."""
    def fetch_filings(self, *, cik: str, accepted_from: datetime, accepted_to: datetime) -> Page[WireFiling]:
        """Filings of one CIK accepted in `[accepted_from, accepted_to)`."""
    def fetch_document(self, *, document_ref: str) -> bytes:
        """The bytes of one filing document, exactly as served."""
    def fetch_reported_metrics(self, *, cik: str, period_end: date) -> Page[WireFundamentals]:
        """Metrics as reported to the SEC for one CIK and period: rule N7's authority."""


@runtime_checkable
class MacroProvider(Protocol):
    provider_id: ProviderId
    def fetch_observations(self, *, series_id: str, observation_from: date, observation_to: date,
                           vintage_from: date, vintage_to: date) -> Page[WireMacroObservation]:
        """Observations in the range, one record per (observation date, vintage date)."""
    def fetch_series_notes(self, *, series_id: str) -> str:
        """The series' notes text, for the copyright screen of §19.5."""


@runtime_checkable
class FxProvider(Protocol):
    provider_id: ProviderId
    def fetch_rate(self, *, as_of_date: date, base: str, quote: str) -> WireFxRate | None:
        """The rate for one date, or None only when the provider affirmatively has none."""


@runtime_checkable
class NewsProvider(Protocol):
    provider_id: ProviderId
    def fetch_news(self, *, updated_from: datetime, updated_to: datetime, cursor: str | None) -> Page[WireNews]:
        """Items created or updated in `[updated_from, updated_to)`."""


@runtime_checkable
class BarStream(Protocol):
    """Held-names minute-bar stream. One connection per process (SPEC-P0.2: the limit is 1)."""
    provider_id: ProviderId
    async def connect(self) -> None:
        """Open the socket and authenticate. Raises `StreamError` or `CredentialInvalid`."""
    async def subscribe(self, provider_symbols: Sequence[str]) -> None:
        """Replace the subscription with exactly these symbols, channel `b` only."""
    def messages(self) -> AsyncIterator[WireBar]:
        """Minute bars in arrival order. The iterator ends when the connection closes."""
    async def close(self) -> None:
        """Close the socket. Idempotent."""
```

**Errors.** Every protocol method raises exactly one of these, and nothing else escapes an adapter:

```python
# src/data/errors.py
class IngestError(Exception):
    """Base. Every subclass maps to exactly one FailureKind (§15.1)."""


class ProviderUnreachable(IngestError):
    """Connection refused, DNS, TLS."""


class ProviderTimeout(IngestError):
    """No complete response inside the configured timeout."""


class ProviderHttpError(IngestError):
    """A status the adapter does not classify as throttling."""


class ProviderThrottled(IngestError):
    """429, or the provider's documented equivalent."""


class QuotaRefusedLocally(IngestError):
    """The call was not sent: it would breach a published limit."""


class CredentialInvalid(IngestError):
    """401/403 or a failed pre-flight."""


class SchemaViolation(IngestError):
    """Response does not parse into the wire model."""


class IncompleteResponse(IngestError):
    """Truncated body, or a page chain that did not terminate."""


class StreamError(IngestError):
    """A WebSocket error frame or an unexpected close."""
```

`fetch_rate` returns `None` only when the provider **affirmatively** reports no rate for that date.
An error is never translated into `None`.

### 4.4 Adapters

| Adapter | Protocols | Source fields | State |
|---|---|---|---|
| `adapters/massive.py` | `ReferenceProvider`, `DailyBarProvider`, `IntradayBarProvider`, `CorporateActionProvider` | §7.3 | Bars, splits, dividends, tickers: fields `[V-P0.2]`. Ticker-type values, `primary_exchange` values, Ticker Events, trades: **`[OQ-22]`** |
| `adapters/alpaca_data.py` | `IntradayBarProvider`, `BarStream`, `NewsProvider` | §7.3 | Fields `[V-P0.2]` |
| `adapters/fmp.py` | `FundamentalsProvider` | none recorded | **`[OQ-23]`** — SPEC-P0.2 §3.4 records pricing and quotas only |
| `adapters/sec_edgar.py` | `FilingsProvider` | none recorded | **`[OQ-9]`** — SPEC-P0.2 §3.8 records policy, hosts and cutoffs only |
| `adapters/fred.py` | `MacroProvider` | endpoint names only | **`[OQ-24]`** |
| `adapters/zerodha.py` | `ReferenceProvider`, `DailyBarProvider` | `tick_size`, `lot_size` only | **`[OQ-25]`** |
| Calendar adapter | `CalendarProvider` | — | **`[OQ-1]`** — no provider named |
| FX adapter | `FxProvider` | — | **`[OQ-7]`** |

**An adapter whose row names an open question has a complete contract (its protocol, its wire
model, its normalisation target in §7) and no field mapping.** Its field mapping is added to §7.3
when the question closes. Until then that adapter cannot be implemented and this spec cannot be
frozen for it `[P21-25]`.

---

## 5. Client layer

One client object per provider, shared by every protocol method of that provider.

### 5.1 Rules

| # | Rule | Edge case |
|---|---|---|
| **IR-1** | A call that would exceed a **published** limit is not sent `[FROZEN P0.2 §10.3]`. It raises `QuotaRefusedLocally` after waiting for the window to roll, up to the caller's deadline | Waiting past the `INGEST` stage budget is not allowed: the run fails with `STAGE_BUDGET_EXCEEDED` instead |
| **IR-2** | Where a limit is **not published** (FRED, rule N8), the client uses adaptive backoff only and no request budget | The backoff parameters are `ASSUMPTION [A-3]` |
| **IR-3** | Every response updates `provider_quota_usage` for its `(provider_id, scope, window_start)`: `request_count`, `response_bytes`, and `throttled_count` on a throttle | The row is written with `INSERT`; a second response in the same window inserts into a staging counter held in the process and the row is written once, when the window closes, because `app_rw` has no `UPDATE` on this table. A crash loses at most the open window's counts; the FMP byte budget therefore reserves the 20% margin RULE-B5 already sets |
| **IR-4** | The FMP client refuses a call when the rolling 30-day `response_bytes` sum is at or above 40 GB `[FROZEN P0.3 RULE-B5]` | The sum is read from `provider_quota_usage` at client start and maintained in the process |
| **IR-5** | A throttle response is retried with exponential backoff and full jitter. `Retry-After`, when present, is a **minimum** wait | Providers whose throttle status is undocumented `[V-P0.2 M-4]`: Massive, FMP, SEC, Upstox. For these, any 4xx other than 400, 401, 403 and 404 is treated as a throttle |
| **IR-6** | A credential is checked before the first call of a run, by the lifetime in its `CredentialSpec` | Zerodha: a token that expires at 06:00 Asia/Kolkata before the run's deadline fails pre-flight (`CREDENTIAL_INVALID`); the run does not start and discover it mid-way |
| **IR-7** | SEC requests carry the declared User-Agent, `Accept-Encoding: gzip, deflate` and stay at or below 10 requests per second `[V-P0.2 §3.8]` | The User-Agent comes from `ingest.yaml`. An empty one fails config validation |
| **IR-8** | No retry is attempted on `SchemaViolation`, `CredentialInvalid` or a 400 | Retrying a response we cannot parse fetches the same response |

### 5.2 Retry and timeout parameters

All four are `ASSUMPTION [A-3]`, set in `ingest.yaml`, and bounded by the frozen `INGEST` stage
budget of 1800 s (`policy.yaml` `latency.stages`).

| Key | Value | Unit |
|---|---|---|
| `client.backoff_base_seconds` | 1 | seconds |
| `client.backoff_cap_seconds` | 300 | seconds |
| `client.max_attempts` | 6 | attempts, including the first |
| `client.request_timeout_seconds` | 30 | seconds, connect plus read |

Wait before attempt *k* (k ≥ 2) is a uniform random value in `[0, min(cap, base × 2^(k−2))]`. The
random source is seeded from the operating system; the wait is not part of any stored record, so
it does not affect replay.

---

## 6. Reference data and calendar loaders

### 6.1 Instruments and symbols

The loader is the **only** code that creates an `instrument` row `[FROZEN P1.1 §5]`. A bar, a
split or a news item naming a symbol with no mapping is `UNKNOWN_SYMBOL`; it never creates one.

| # | Rule | Edge case |
|---|---|---|
| **IR-9** | `instrument_id` is a random UUID assigned at first sighting and never changed | "First sighting" is decided by IR-10 |
| **IR-10** | A vendor record is matched to an existing instrument by `composite_figi` when the record carries one `[DEFAULT-13]`; otherwise by the open `symbol_mapping` for `(market, symbol)` on `as_of_date` | Two existing instruments with the same `composite_figi`: `AMBIGUOUS_SYMBOL`, no write. A record with no FIGI and no open mapping is a new instrument |
| **IR-11** | A change to an instrument fact closes the open row (`knowledge_to`) and inserts a new one. A changed ticker closes the open `symbol_mapping` (`valid_to` = the first date the new ticker is seen, exclusive bound) and opens another for the **same** `instrument_id` | Both statements run in one transaction. The `EXCLUDE` constraints of 0001 reject an overlap; that rejection is `AMBIGUOUS_SYMBOL` and the whole reference run fails |
| **IR-12** | A vendor `security_type` or `primary_exchange` with no entry in the configured mapping table creates **no** instrument and is recorded (`UNKNOWN_INSTRUMENT_TYPE`) | Deny-by-default `[FROZEN P1.1 §5.3, ADR-05]`. Venues outside `Exchange` cannot be represented at all `[P21-21]`; they are counted in the manifest's `skipped_count`, not as failures, when the mapping table lists them as `EXCLUDED` |
| **IR-13** | `delisted_utc` present → `status = DELISTED`, `delisted_on` = its UTC date. The row is never deleted (invariant I7) | `final_price` is left `NULL`. This phase does not derive it from the last bar |
| **IR-21** | For an India instrument, the instruments dump's `tick_size` is written to `tick_size_regime` as one row per symbol per dump date: `market = IN`, the instrument's symbol, `effective_from = as_of_date`, `effective_to = as_of_date + 1 day`, the dump's `tick_size`, `min_price = 0`, and a `source` naming the dump and its date `[DEFAULT-17]` | The row is bounded to one day because a regime row cannot be superseded: `app_rw` has no `UPDATE` on the table and its `EXCLUDE` constraint rejects an overlapping open-ended row `[P21-28]`. A date with no loaded dump has no row, so rule N10 denies orders in that symbol on that date: fail-closed. **This form is provisional (O-12).** Whether the dump for a session is available before that session's order window is `[OQ-25]` and has not been verified; this spec claims no pre-open readiness. If the dump is not available in time, this form denies every India order and must be revisited `[OQ-34]`. Re-loading a date with the same value is a duplicate; with a different value it is `DUPLICATE_CONFLICT`. P2.1 writes no US row: the seeded `*` row stands |

Fields with **no verified source** are written `NULL` and never guessed: `issuer_id`, `isin`,
`cusip`, `figi` (US), `final_price`. `HALTED` and `SUSPENDED` have no source in any frozen fact
sheet `[OQ-26]`; the loader writes `ACTIVE` or `DELISTED` only. `qty_increment` is `1` for US
`[FROZEN P1.1 DEFAULT-3]` and the dump's `lot_size` for India. `supports_fractional` is `false`.

Each provider's own identifier for an instrument is stored in `provider_instrument_ref` (§22),
because `instrument` has no column for a CIK, a share-class FIGI or a Zerodha instrument token.

### 6.2 Calendar

| # | Rule | Edge case |
|---|---|---|
| **IR-14** | One `exchange_session` row per `(exchange, trading_date)` on which the exchange is open, holding explicit UTC instants `[FROZEN P1.1 §4.2]`. A closed date has no row | A date that becomes a holiday after its row was loaded: the row stays (IR-17), ingest expects bars that never come, and the gaps stay `OPEN` until an operator resolves the row `[OQ-27]`. Code never removes a session row |
| **IR-15** | Every calendar load writes an `ingest_manifest` row with `data_type = CALENDAR` and `coverage_from` / `coverage_to`. **A date with no session row means "closed" only inside a recorded coverage range.** Outside it, the date is `MISSING_SESSION` | This is what separates a holiday from a calendar that was never loaded `[P21-19]`. A scheduled run on a covered date with no row exits zero with manifest status `NO_SESSION` |
| **IR-16** | `settlement_date` is computed by the loader from `calendar.{market}.settlement_cycle_sessions` and the loaded sessions | The cycle value is `1` for both markets, **carried** from SPEC-P1.1 assumption A11 / `Q-P1.1-1`, unverified. A settlement date that would fall outside the coverage range fails the load; it is not approximated |
| **IR-17** | A session row is immutable once a bar has been stored against it | A vendor that later changes a session's close (an unscheduled early close) produces a `DUPLICATE_CONFLICT` failure for the calendar and stops the market's ingest. `exchange_session` has no bitemporal axis and `app_rw` cannot update it; resolving the row is a manual `trading_owner` action `[OQ-27]` |

`session_type` is `HALF_DAY` when the wire record says so, `SPECIAL` when it says so (with
`counts_for_sequencing = false` `[FROZEN P1.1 §4.2]`), otherwise `REGULAR`.

---

## 7. Normalisation

### 7.1 Order of operations for every record

1. Parse the response into wire records (§4.2). Failure: `SCHEMA_VIOLATION`.
2. Reject a vendor timestamp later than `retrieved_at` plus the skew limit (§16.2). Failure: `FUTURE_TIMESTAMP`.
3. Check precision (§7.2). Failure: `PRECISION_EXCEEDED`.
4. Resolve the provider symbol to an `instrument_id` as of the record's trading date. Failure: `UNKNOWN_SYMBOL` or `AMBIGUOUS_SYMBOL`.
5. Resolve the session. Failure: `MISSING_SESSION`.
6. Construct the domain type. Failure: `DOMAIN_VALIDATION_FAILED`, with the domain error's class name.
7. Write (§9).

A failure at any step discards **that record only**, writes one `ingest_failure` row, and counts
in the manifest. It never discards the batch silently and never substitutes a value.

### 7.2 Precision — reject or keep exact, never round silently `[DEFAULT-14]`

`Price` quantises to 6 decimal places and `Money` to 2, both with `ROUND_HALF_UP`, inside their
constructors (`src/domain/models.py`). Constructing either from a more precise vendor value
therefore **rounds without raising** `[P21-16]`. The normaliser checks the vendor value's scale
first:

| Target | Maximum scale | On excess |
|---|---|---|
| `Price` (`numeric(18,6)`) | 6 | `PRECISION_EXCEEDED`; record not stored |
| `bar_*.volume` (`bigint`) | 0 | `PRECISION_EXCEEDED` |
| `corporate_action.ratio` (`numeric(18,6)`) | not bounded | Never refused. The exact `split_from` and `split_to` go to `corporate_action_terms`; the 0001 `ratio` is the quotient rounded half-up to 6 places and `ratio_rounded_in_0001` records whether rounding occurred (§8.2) |
| `corporate_action.cash_amount` (`numeric(18,2)`) | not bounded | Never refused. The exact amount goes to `corporate_action_terms.cash_amount_exact`; the 0001 `cash_amount` is that amount rounded half-up to 2 places — the `Money` constructor's own rounding — and `cash_rounded_in_0001` records whether rounding occurred (§8.2) |
| `fx_rate.rate` (`numeric(18,6)`) | 6 | `PRECISION_EXCEEDED` |
| Fundamentals metrics (`jsonb`, decimal strings) | not bounded by the column | stored at vendor precision |

Every `PRECISION_EXCEEDED` on a price is also the standing measurement for `Q-P1.1-6` (§21).

### 7.3 Provider field mappings

Only fields recorded in SPEC-P0.2 are mapped. A vendor field not listed is not read.

**Massive — aggregates `GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`,
always with `adjusted=false`** `[V-P0.2 §3.3]`

| Vendor field | Wire field | Stored as |
|---|---|---|
| path `ticker` | `provider_symbol` | resolved to `instrument_id` |
| `t` (Unix ms, window start) | `window_start` | Daily: used to confirm `trading_date`; **`ts` = that session's `regular_close_utc`** `[DEFAULT-1]`. 5-minute: `ts` = `window_start` |
| `o`, `h`, `l`, `c` | `open`, `high`, `low`, `close` | `numeric(18,6)`, currency from the instrument |
| `v` | `volume` | `bigint` |
| `n` | `trade_count` | `integer`, nullable |
| `vw` | not read | no column |

**Alpaca — bars (REST and the `b` stream message)** `[V-P0.2 §3.2]`

| Vendor field | Wire field | Stored as |
|---|---|---|
| `t` (RFC-3339, window start) | `window_start` | §13.3 |
| `o`, `h`, `l`, `c`, `v`, `n` | as Massive | §13.3 |
| `vw` | not read | no column |

**Massive — splits `GET /stocks/v1/splits`** `[V-P0.2 §3.3]`

| Vendor field | Wire field |
|---|---|
| `ticker` | `provider_symbol` |
| `execution_date` | `execution_date` |
| `split_from`, `split_to` | `split_from`, `split_to` |

**Massive — dividends `GET /stocks/v1/dividends`** `[V-P0.2 §3.3]`

| Vendor field | Wire field |
|---|---|
| `ticker` | `provider_symbol` |
| `ex_dividend_date`, `pay_date`, `record_date`, `declaration_date` | same names |
| `cash_amount` | `cash_amount` |
| `distribution_type`, `frequency` | same names — stored in `corporate_action_terms`, with `record_date` and `declaration_date`. 0001 has no column for them `[P21-18]` |

**Massive — tickers `GET /v3/reference/tickers` with `date` and `active`** `[V-P0.2 §3.3]`

| Vendor field | Wire field | Stored as |
|---|---|---|
| `ticker` | `provider_symbol` | `symbol_mapping.symbol` |
| `primary_exchange` | `primary_exchange` | `instrument.exchange` through the configured mapping; values `[OQ-22]` |
| `type` | `security_type` | `instrument.instrument_type` through the configured mapping; values `[OQ-22]` |
| `active`, `delisted_utc` | same | `status`, `delisted_on` (IR-13) |
| `currency_name` | `currency_name` | must map to `USD` for a US instrument, else `DOMAIN_VALIDATION_FAILED` |
| `cik` | `cik` | `provider_instrument_ref`, kind `CIK` |
| `composite_figi` | `composite_figi` | `instrument.figi_composite`; also the identity key (IR-10) |
| `share_class_figi` | `share_class_figi` | `provider_instrument_ref`, kind `SHARE_CLASS_FIGI`. **Not** written to `instrument.figi`: no frozen spec says which FIGI that column holds `[OQ-28]` |
| `name`, `market`, `locale`, `last_updated_utc` | not read | — |

**Alpaca — news `GET /v1beta1/news` with `include_content=true`** `[V-P0.2 §3.2]`

| Vendor field | Wire field | `raw_news_snapshot` column |
|---|---|---|
| `id` | `vendor_id` | `vendor_id` |
| `headline` | `headline` | `headline_raw` |
| `author` | `author` | `author_raw` |
| `created_at` | `created_at` | `vendor_created_at` |
| `updated_at` | `updated_at` | `vendor_updated_at` |
| `summary` | `summary` | `summary_raw` |
| `content` | `content` | `body_raw` |
| `symbols` | `symbols` | `symbols_raw` |
| `source` | `source` | `source_raw` |
| `url` | `url` | `url_raw` |
| `images` | not read | — |

**FMP, SEC EDGAR, FRED, Zerodha, the calendar source and the FX source: no mapping.** See §4.4.

### 7.4 Domain type to table

The contract test `tests/verify_p11_p12_contract.py` does not cover `bar_daily`,
`corporate_action` or `fundamentals_snapshot`, and checks column-to-field only `[P21-8]`. This
table is therefore the mapping of record for what P2.1 writes. Neither side is changed.

| Table.column | Source |
|---|---|
| `bar_*.instrument_id`, `market`, `trading_date`, `open`, `high`, `low`, `close`, `volume`, `is_final`, `source`, `retrieved_at` | The `Bar` field of the same name; prices from `Price.value` |
| `bar_*.ts` | `Bar.as_of` |
| `bar_*.trade_count` | `WireBar.trade_count`. `Bar` has no such field; the value passes from the wire record to the insert beside the `Bar` |
| — | `Bar.interval` selects the table (`DAILY` → `bar_daily`; `MIN_5` → `bar_intraday_5m` or its validation twin). It has no column |
| `corporate_action.*` | `CorporateAction` fields of the same name; `cash_amount` and `cash_currency` from `Money`; `knowledge_from` = the insert transaction's start; `knowledge_to` = `NULL` |
| `successor_link.*` | `CorporateAction.successor`; `audit_event_id` — **condition 9** |
| `fundamentals_snapshot.period_end`, `fiscal_period`, `calendar_as_of`, `filed_at`, `disseminated_at`, `metrics`, `source`, `retrieved_at`, `instrument_id`, `market` | `FundamentalsSnapshot` fields of the same name; `metrics` as a JSON object of decimal **strings** |
| `fundamentals_snapshot.restatement_seq` | Assigned by §19.3 |
| `fundamentals_snapshot.edgar_index_hash` | `edgar_index_snapshot.content_sha256` of the index the filing record came from |
| `fundamentals_snapshot.valid_from`, `valid_to` | `valid_from` = `period_end`; `valid_to` = `NULL` |
| `fundamentals_snapshot.knowledge_from`, `knowledge_to` | As `corporate_action` |
| `fx_rate.*` | `FxRate` fields of the same name |
| `corporate_action_terms.*` | The `WireSplit` or `WireDividend` the action was built from, unrounded; `action_id` and `knowledge_from` from the `corporate_action` row written in the same transaction |
| `instrument.*`, `symbol_mapping.*`, `exchange_session.*` | Fields of the same name; bitemporal columns as above |
| `tick_size_regime.*` (India rows only) | `WireInstrument.tick_size` and `as_of_date`, by rule IR-21. `min_price` is 0; `source` names the dump and its date |

`FundamentalsSnapshot.as_of` (inherited from `_MarketDatum`) is set to `disseminated_at`. It has
no column.

`calendar_as_of` is the calendar date of `period_end` `[FROZEN P0.1 §6]`: the fiscal period is
mapped to the calendar by its end date, and nothing else is inferred.

---

## 8. Corporate actions

### 8.1 What can be ingested today

`CorporateActionType` has eleven members. Verified source fields exist for four `[P21-24]`:

| Type | Source | State |
|---|---|---|
| `SPLIT`, `REVERSE_SPLIT` | Massive splits | Mapped (§7.3) |
| `CASH_DIVIDEND` | Massive dividends | Mapped (§7.3); exact terms in `corporate_action_terms` (§8.2) |
| `DELISTING` | Massive tickers `delisted_utc` | Written when the reference loader first sees the delisting; `ex_date` = `effective_date` = `delisted_on` |
| `STOCK_DIVIDEND`, `TICKER_CHANGE`, `EXCHANGE_TRANSFER`, `MERGER`, `ACQUISITION`, `SPINOFF`, `RIGHTS_ISSUE` | none recorded | **`[OQ-29]`**. `TICKER_CHANGE` is observable from the reference loader (IR-11) and is written from there; the other six have no source |

### 8.2 Rules

| # | Rule | Edge case |
|---|---|---|
| **IR-18** | The action type is decided by the **endpoint** the record came from, through a mapping table per adapter. A record that fits no type raises `UnknownCorporateActionError` → `UNKNOWN_CORPORATE_ACTION`; it is never skipped | `parse_corporate_action_type` in the domain only upper-cases a string; no vendor emits our enum names, so adapters do not call it with vendor text |
| — | `ratio` = `split_to / split_from`, computed in `Decimal` and rounded half-up to 6 places for the 0001 column | A quotient that does not terminate within 6 places (1-for-3 is 0.333333 recurring) cannot be exact in 0001 `[P21-18]`. The exact `split_from` and `split_to` are stored in `corporate_action_terms` with `ratio_rounded_in_0001 = true`. A split is never refused for this reason: a missing split misprices every later bar |
| — | `cash_amount` in 0001 = the vendor's per-share amount rounded half-up to 2 places, which is the `Money` constructor's own rounding | An amount with more than 2 decimals cannot be exact in 0001 `[P21-17]`. The exact amount is stored in `corporate_action_terms.cash_amount_exact` with `cash_rounded_in_0001 = true`. A dividend is never refused for this reason |
| — | Every `SPLIT`, `REVERSE_SPLIT` and `CASH_DIVIDEND` row in `corporate_action` has exactly one `corporate_action_terms` row with the same `(action_id, knowledge_from)`, written in the same transaction (O-10) | A changed fact closes the 0001 row and inserts a new one; the new row gets its own terms row. If either insert fails the transaction rolls back: the action is absent, never half-recorded. `DELISTING` and `TICKER_CHANGE` have no terms row |
| — | Natural key: `(instrument_id, action_type, ex_date, source)` among rows with `knowledge_to IS NULL` | A re-fetched action identical on every fact column: no write. A changed fact: close the open row, insert a new one with the **same** `action_id` |
| — | `as_of` = the `retrieved_at` of the first sighting. No verified source field carries an announcement time | A backfilled split therefore has an `as_of` on the backfill date. A backtest must select actions by `effective_date`, not `as_of` |
| — | An action whose `effective_date` has no session row inside calendar coverage: `CorporateActionCalendarError` → `DOMAIN_VALIDATION_FAILED`, not stored `[FROZEN P1.1 §5.3]` | Applies to splits. A dividend `pay_date` on a closed date is legitimate and is stored |

### 8.3 A split announced during a backfill

Bars are stored unadjusted (rule N9), so a split arriving at any time changes no stored bar. The
order inside every run is fixed: reference → calendar → corporate actions → bars. A backfill job
re-fetches splits and dividends for its instruments as its **last** step and again in the next
daily run. A split whose `execution_date` falls inside a range already backfilled needs no
re-fetch of bars.

### 8.4 Read-time application order (exported to P2.4 and P5.1)

For a price on trading date *d* read as of decision date *D*: apply, in ascending `effective_date`
and then `action_id` order, every action with `d < effective_date ≤ D` and `knowledge_to IS NULL`
as of the reader's knowledge cutoff. Splits scale price by `split_from / split_to` and volume by
`split_to / split_from`, both taken from `corporate_action_terms`; the 0001 `ratio` is a rounded
representation whenever `ratio_rounded_in_0001` is true and is not used for adjustment. A reader
that needs a dividend's amount takes `cash_amount_exact`, and its `distribution_type` from the same
row. Whether and how dividends adjust is P2.4's decision; this phase guarantees only that both
dates and the exact amount are stored and that `ex_date` is the vendor's ex-dividend date.

---

## 9. Keys, idempotency and write rules

### 9.1 Natural keys

| Record | Natural key | Storage key |
|---|---|---|
| Daily or 5-minute bar | `(instrument_id, ts)` | Primary key |
| Instrument | `instrument_id`, found by IR-10 | `(instrument_id, knowledge_from)` |
| Symbol mapping | `(instrument_id, exchange, valid_from)` among open rows | `mapping_id` |
| Exchange session | `(exchange, trading_date)` | Primary key |
| Corporate action | §8.2 | `(action_id, knowledge_from)` |
| Fundamentals | `(instrument_id, period_end, restatement_seq)` | Unique constraint |
| FX rate | `(as_of_date, base, quote)` | Primary key |
| Raw news | `(provider_id, vendor_id, revision_seq)` | Primary key |
| Macro observation | `(series_id, observation_date, vintage_date)` | Primary key |
| EDGAR index | `(index_kind, index_ref, content_sha256)` | Primary key |
| EDGAR filing | `(filing_key, observed_at)` | Primary key |
| Corporate-action exact terms | `(action_id, knowledge_from)` | Primary key |

### 9.2 Write rules

| # | Rule | Edge case |
|---|---|---|
| **IR-19** | **Insert-only.** Every write to a uni-temporal table is an `INSERT` with `ON CONFLICT DO NOTHING` on its key, followed by a read of the stored row when the insert affected nothing | Two runs inserting the same key at once: one inserts; the other's insert affects nothing, so it reads the stored row and classifies it as duplicate or conflict like any other. No lock is taken and no row is overwritten |
| — | Stored row identical on every fact column (everything except `retrieved_at`): a duplicate. Counted in `duplicate_count`; nothing written | A replayed backfill partition is entirely duplicates and succeeds |
| — | Stored row **different**: `DUPLICATE_CONFLICT` failure plus an `ingest_reconciliation` row of kind `REVISION`. The stored row is not changed and cannot be | For `fx_rate` this is ADR-15 §5 working as designed: a past rate is never corrected |
| **IR-20** | Only the SPEC-P0.2 `PRIMARY` provider for a capability writes a 0001 market-data table `[DEFAULT-3]` | Rule N7's EDGAR row in `fundamentals_snapshot` is the one exception, by SPEC-P0.2 decision 5: `SEC_EDGAR` is `AUTHORITY` |
| — | `is_final = false` is never written to `bar_daily`, `bar_intraday_5m` or its twin | The row could never be finalised. A daily bar is written only after the session's `regular_close_utc`; a 5-minute bar only when completed (§13.3) |
| — | Market-data writes run at `synchronous_commit = off` `[FROZEN P1.2 §10.3]`. `fx_rate` is NAV state and is written at `remote_write` | A lost market-data commit is re-fetched; that is why the checkpoint is written in the same transaction as its rows (§10.2) |
| — | Bitemporal tables: `UPDATE` sets `knowledge_to` only, then `INSERT`. Both in one transaction | The 0001 trigger rejects anything else |

---

## 10. Historical backfill

### 10.1 Jobs and partitions

| Job | Partition | Source | Budget `[FROZEN P0.3 §3.4]` |
|---|---|---|---|
| Reference snapshots | one `as_of_date` | Massive tickers | 2 h |
| Calendar | one `(exchange, year)` | `[OQ-1]` | — |
| Splits, dividends | one instrument | Massive | 15 min |
| Daily bars | one `(instrument, symbol-validity interval, date range)` of at most 50,000 points | Massive | 2 h |
| 5-minute validation slice | one `(instrument, trading_date)` | Massive | 2 h |
| Fundamentals | one `(instrument, fiscal quarter)` `[FROZEN RULE-B5]` | FMP | 6 h |
| EDGAR filings | one `(cik, calendar quarter)` | SEC EDGAR | — |
| Macro | one `(series_id, vintage-date range)` | FRED / ALFRED | — |

Backfill is not a pipeline stage and is not bound by the 1800 s `INGEST` budget; the figures above
are SPEC-P0.3's and are vendor-pacing estimates, not deadlines this phase enforces.

**News is never backfilled** (rule N16's corollary). A raw news row exists only for an item first
seen by the live poll, with a truthful `first_seen_at`.

### 10.2 Resume after a crash

1. A job has a `job_id`. Its partitions are enumerated deterministically from its parameters, in a fixed order.
2. Before the first request for a partition: one `ingest_checkpoint` row, state `STARTED`.
3. The partition's rows and one checkpoint row with state `COMMITTED` are written in **one transaction**.
4. On restart with the same `job_id`, a partition whose latest checkpoint is `COMMITTED` is skipped. Every other partition is redone from its first page.
5. A redone partition is safe by IR-19: its already-stored rows are duplicates.

A partition is never partly committed: a fiscal quarter, a ticker's date range or a reference
snapshot is in the store whole or not at all `[FROZEN RULE-B5]`. A provider page cursor is not
persisted across a crash; `ingest_checkpoint.cursor` records it for diagnosis only.

FMP bandwidth exhausted mid-job: the job writes a `PAUSED` checkpoint and exits non-zero; it does
not restart from the beginning `[FROZEN P0.3 §13.1 row 4]`.

### 10.3 Symbols across history

A daily-bar partition never spans a change of symbol: the range is cut at every `symbol_mapping`
boundary for the instrument, and each piece is requested under the symbol valid for it. Each
returned bar is still resolved independently with `symbol_asof(market, symbol, trading_date,
knowledge_asof)`; a bar that resolves to a different instrument than the partition's is
`AMBIGUOUS_SYMBOL` and is not stored.

---

## 11. Gap definition

A **gap** is an expected record that is absent after the fetch that should have produced it. What
is expected comes from `exchange_session` and the ingest set, and from nowhere else.

### 11.1 Daily bars

For a run on `(market, trading_date D)`, a daily bar is **expected** for instrument *i* when all hold:

1. *i* is in the run's ingest set `[DEFAULT-11]`;
2. a session row exists for `(i.exchange, D)` with `session_type` `REGULAR` or `HALF_DAY`;
3. *i* has an open symbol mapping covering *D*;
4. *i* is not `DELISTED` with `delisted_on < D`.

| Case | Result |
|---|---|
| Half-day | One daily bar is expected, exactly as on a full day. **A half-day is not a gap and produces no fewer daily bars** |
| `SPECIAL` session (Muhurat) | No bar is expected. A bar received for it is stored with that session's `regular_close_utc`; its absence is not a gap |
| No session row for *D*, inside calendar coverage | Nothing is expected for that exchange. A bar received for *D* is `MISSING_SESSION` and is not stored: there is no close instant to stamp it with |
| *D* outside calendar coverage | `MISSING_SESSION`; the run fails before any bar is fetched |
| An expected bar absent from the response | One `ingest_gap` row, kind `MISSING_EXPECTED`, state `OPEN`. **Never filled from the previous close.** Whether the instrument was halted all day is not known to this phase `[OQ-26]`; it is a gap either way |
| DST change between *D−1* and *D* | No effect. The two session rows carry different UTC instants; no code computes an offset |

### 11.2 Five-minute bars

For a held instrument on session *S*, the expected windows are
`[S.regular_open_utc + 300k s, S.regular_open_utc + 300(k+1) s)` for every integer `k` from 0 to
`N − 1`, where `N = (S.regular_close_utc − S.regular_open_utc) / 300 s`.

| Case | Result |
|---|---|
| Full US day | 78 windows `[FROZEN P0.3 §2.2]` |
| US half-day (13:00 ET close) | 42 windows. Windows after the early close are **not expected** and their absence is not a gap |
| First session after a DST change | Windows start one hour earlier or later in UTC than the previous session's. They are read from the row |
| A window with no bar | §13.4 decides whether it is a gap, a confirmed no-trade window, or a detected loss |

### 11.3 Resolution

A gap row is never updated. A resolution is a **new** row with `resolves_gap_id` set and one of:
`RESOLVED_FILLED` (the record was later obtained from the same primary source and stored),
`RESOLVED_NO_DATA_AT_SOURCE` (the source, asked again, affirmatively returned nothing for it), or
`UNRESOLVABLE` (the source can no longer be asked, with the reason). The current state of a gap is
its latest row. `RESOLVED_NO_DATA_AT_SOURCE` still means the datum is absent for every consumer.

---

## 12. Daily batch ingest

Scheduled at `schedule.{market}.ingest_utc` `[FROZEN policy.yaml]`. One run per market per session.

### 12.1 Sequence

| Step | Action | On failure |
|---|---|---|
| 1 | Pre-flight: clock (§16.2), Redis reachable, database reachable, credentials (IR-6), `ingest.yaml` valid and hashed | Exit non-zero. No manifest row can be written if the database is unreachable; the process exit code and the service manager's failure hook are the only record `[FROZEN P0.3 §13.1 rows 16, 17, 20]` |
| 2 | Resolve session *D*. Inside coverage with no row: write `NO_SESSION`, exit zero. Outside coverage: `MISSING_SESSION`, exit non-zero | `[FROZEN P0.3 §13.1 row 5]` |
| 3 | Refuse to start before `D.regular_close_utc` | A timer that fires early on a half-day mis-set by an operator must not fetch an in-progress bar |
| 4 | Reference refresh for *D* | Run status `FAILED`; later steps do not run |
| 5 | Corporate actions with `ex_date` or `execution_date` in a configured look-back and look-ahead around *D* | As step 4 |
| 6 | **Revision check** `[DEFAULT-2]`: re-fetch daily bars for the previous sequenced session for the ingest set and compare with the stored rows (§14.2) | Any `DISAGREE`: the run status for `BAR_DAILY` is `FAILED` and the process exits non-zero `[FROZEN P0.3 §13.1 row 3]` |
| 7 | Fetch and store daily bars for *D* | Per record: §7.1. Vendor unreachable: `FAILED`, exit non-zero `[FROZEN P0.3 §13.1 row 1]` |
| 8 | Completeness: expected (§11.1) against present | Any absent expected bar: gap rows, status `INCOMPLETE`, exit non-zero `[FROZEN P0.3 §13.1 row 2]` — see `[P21-22]` |
| 9 | Fundamentals for the instruments scheduled this session; EDGAR; macro; FX | Each has its own manifest row and status. A failure in one does not undo another; the exit code is non-zero if any is not `COMPLETE` |
| 10 | Write manifest rows; emit audit events (§20, gated) | A manifest insert that fails is `DB_WRITE_FAILED`: exit 1. The absence of a `COMPLETE` row for the run is then the durable signal (§15.2) |

The whole run is bounded by the `INGEST` stage budget, 1800 s, `on_breach: ABORT` `[FROZEN]`. On
breach the run stops issuing requests, writes `STAGE_BUDGET_EXCEEDED`, marks every unfinished data
type `FAILED` and exits non-zero. Rows already committed stay; they are correct rows.

### 12.2 Exit codes

| Code | Meaning |
|---|---|
| 0 | Every data type of the run is `COMPLETE`, or the run is `NO_SESSION` |
| 1 | At least one data type is `INCOMPLETE` or `FAILED` |
| 2 | Pre-flight failed; nothing was fetched |

A non-zero exit means **no order list for the next session** `[FROZEN P0.3 §13.1 row 1]`. That
consequence is enforced by the pipeline's precondition, not by this phase.

### 12.3 Request and result models

The ingest set of `[DEFAULT-11]`, a backfill job (§10) and a daily run (§12.1) are typed. Field
specifications are in §28.3.

```python
# src/data/requests.py
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from data.enums import IngestDataType, ManifestStatus
from domain.models import Market
from provider.enums import ProviderId

BACKFILLABLE: frozenset[IngestDataType] = frozenset({
    IngestDataType.REFERENCE, IngestDataType.CALENDAR, IngestDataType.CORPORATE_ACTION,
    IngestDataType.BAR_DAILY, IngestDataType.BAR_5M_VALIDATION, IngestDataType.FUNDAMENTALS,
    IngestDataType.EDGAR_FILING, IngestDataType.MACRO,
})


class _Req(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class IngestSet(_Req):
    """The instruments one run must ingest. Supplied by the caller; never inferred ([DEFAULT-11])."""
    market: Market
    trading_date: date
    instrument_ids: frozenset[UUID] = Field(min_length=1)
    universe_version: UUID | None = None
    includes_held: bool


class BackfillJobRequest(_Req):
    """One backfill job (§10). Re-submitting the same job_id resumes it (§10.2)."""
    job_id: UUID
    data_type: IngestDataType
    provider_id: ProviderId
    market: Market
    instrument_ids: frozenset[UUID] = frozenset()
    series_ids: tuple[str, ...] = ()
    date_from: date
    date_to: date
    code_version: str = Field(min_length=7, max_length=40)

    @model_validator(mode="after")
    def _coherent(self) -> "BackfillJobRequest":
        if self.data_type not in BACKFILLABLE:
            raise ValueError(f"{self.data_type} is never backfilled (§10.1)")
        if self.date_to < self.date_from:
            raise ValueError("date_to precedes date_from")
        if (self.data_type is IngestDataType.MACRO) != bool(self.series_ids):
            raise ValueError("series_ids is required for MACRO and forbidden otherwise")
        return self


class DailyRunRequest(_Req):
    """One scheduled run for one market and one session (§12.1)."""
    run_id: UUID
    market: Market
    trading_date: date
    ingest_set: IngestSet
    code_version: str = Field(min_length=7, max_length=40)

    @model_validator(mode="after")
    def _set_matches_run(self) -> "DailyRunRequest":
        if self.ingest_set.market is not self.market or self.ingest_set.trading_date != self.trading_date:
            raise ValueError("ingest_set is for a different market or trading_date")
        return self


class DailyRunResult(_Req):
    """What a daily run returns. The manifest rows are the record; this is their summary."""
    run_id: UUID
    market: Market
    trading_date: date
    exit_code: int = Field(ge=0, le=2)
    statuses: dict[IngestDataType, ManifestStatus]
    manifest_ids: tuple[UUID, ...]
    started_at: datetime
    finished_at: datetime

    @model_validator(mode="after")
    def _exit_code_agrees(self) -> "DailyRunResult":
        ok = {ManifestStatus.COMPLETE, ManifestStatus.NO_SESSION}
        expected = 2 if not self.statuses else (0 if set(self.statuses.values()) <= ok else 1)
        if self.exit_code != expected:
            raise ValueError(f"exit_code {self.exit_code} disagrees with statuses (§12.2): expected {expected}")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at precedes started_at")
        return self
```

---

## 13. Held-names 5-minute stream adapter

Scope (O-3): the adapter, its persistence, and the gap contract. The process that hosts it, the
600 s stale timer, halts, and every decision taken on a bar are P3.3's.

The live feed is not bought until `[RS §12]` stage 5 `[FROZEN P0.2 DEFAULT-P9]`. Until then this
adapter is exercised only against recorded or synthetic frames.

### 13.1 Connection

| Aspect | Rule | Edge case |
|---|---|---|
| Endpoint | `wss://stream.data.alpaca.markets/v2/sip` `[V-P0.2 §3.2]`. Never `v2/iex` (rule N6) | `409` (insufficient subscription) on `v2/sip`: the adapter stops with `CREDENTIAL_INVALID`. It never falls back to `v2/iex` or `v2/delayed_sip` |
| Authentication | In-band `{"action":"auth","key":"<key id>","secret":"<secret key>"}`; success is `[{"T":"success","msg":"authenticated"}]` `[V-P0.2]`. Credentials from Vault references | No success frame within `stream.ping_timeout_seconds` of sending the auth frame is a failed connect and is retried under the Reconnect rule. `402` is not retried |
| Subscription | Channel `b` only `[FROZEN P0.3 §13.3 row 40]` | An empty held set opens no connection. A bar for a symbol that was not subscribed is discarded and counted, never stored |
| Connections | One per process. Error `406` (connection limit) means another instance holds the socket: this instance exits; it does not retry and evict `[FROZEN P0.3 §13.2 row 24]` | `406` at any point, including after a successful subscribe, exits this instance |
| Other error frames | `401`, `402`, `404`, `409`: `CREDENTIAL_INVALID`, no reconnect. `405` (symbol limit): `STREAM_ERROR`, no reconnect. `407` (slow client), `500`, or any close without an error frame: reconnect | An error code not in this list is `STREAM_ERROR` with no reconnect: an unknown code is not assumed transient |
| Liveness | WebSocket protocol ping every `stream.ping_interval_seconds`; no pong within `stream.ping_timeout_seconds` is a disconnect. Both `ASSUMPTION [A-7]`. SPEC-P0.2 records no application-level heartbeat for this stream | A connection that still delivers bars but returns no pong is treated as disconnected: liveness is judged by the pong alone, so it does not depend on how actively the held names trade |
| Reconnect | Exponential backoff with full jitter, base `stream.reconnect_base_seconds`, cap `stream.reconnect_cap_seconds`, `ASSUMPTION [A-7]`. Unbounded attempts inside session hours; none outside | A wait that would end after `regular_close_utc` is abandoned; the remaining windows become gaps and the session-close check (§13.5) handles them. Before `regular_open_utc` no connection is attempted |

### 13.2 Disconnect and rule N5

1. On disconnect, record `disconnected_at` = the receive time of the last frame of any kind.
2. On re-authentication, record `reconnected_at`.
3. Every expected window (§11.2) of every subscribed instrument that overlaps `[disconnected_at, reconnected_at]`, **and the window in progress at `disconnected_at`**, gets an `ingest_gap` row, kind `STREAM_DISCONNECT`, state `OPEN`.
4. **Before any new bar is delivered to the consumer**, each such window is fetched from REST (`IntradayBarProvider`, `window_seconds = 300`, `feed = sip`, `symbol_asof` = the trading date) and written; the gap gets a resolution row.
5. A window REST cannot fill stays `OPEN`, and the adapter reports the instrument as not reconciled (§13.6).
6. Minute bars held in memory for a window that became a gap are discarded. A bar is never assembled from minutes on both sides of a disconnect.

A gap is **assumed lost** `[FROZEN rule N5]`. No replay or resume mechanism is relied on; none is
documented `[V-P0.2 M-3]`.

### 13.3 Assembly and completion `[DEFAULT-16]`

A 5-minute bar for window *w* is built from the minute bars whose `window_start` lies in *w*:
`open` = the earliest minute's open; `high` = the maximum high; `low` = the minimum low; `close` =
the latest minute's close; `volume` and `trade_count` = sums. `ts` = the window start. No value is
taken from any other window.

Completion is **exactly RULE-B12's definition** `[FROZEN P0.3 §15]`; this phase adds no condition
and relaxes none. A completed bar is written with `is_final = true`, `source = ALPACA_DATA`, and
then delivered. An in-progress bar is neither written nor delivered.

A window in which **no** minute bar arrived while the connection was up produces no row. A bar is
not invented for it.

### 13.4 A silent window

Whether Alpaca emits a zero-trade minute bar or omits it is unknown `[FROZEN P0.3 Q-12]`. So, for
an expected window that completed with no row while the connection was continuously up: one
`ingest_gap` row, kind `MISSING_EXPECTED`; then one REST fetch of that window after
`stream.silent_window_recheck_seconds`.

| REST answer | Result |
|---|---|
| A bar | Stored. Gap `RESOLVED_FILLED`. **And one `ingest_failure` of kind `STREAM_SILENT_LOSS`**: the stream lost data without disconnecting |
| No bar | Gap `RESOLVED_NO_DATA_AT_SOURCE` |
| Error | Gap stays `OPEN` |

### 13.5 How it is shown that no bar was silently lost

At session close, for every instrument subscribed at any time during the session:

1. Fetch the whole session's 5-minute bars from REST.
2. **Existence.** Every REST bar must have a stored row with the same `(instrument_id, ts)`. A missing one is stored now, and recorded as `STREAM_SILENT_LOSS`.
3. **Values.** Each stored row is compared with its REST bar under §14's tolerances; a disagreement is an `ingest_reconciliation` row of kind `STREAM_VS_REST`.
4. **Accounting.** For each instrument: *expected windows* = *stored rows* + *gaps whose latest state is `RESOLVED_NO_DATA_AT_SOURCE`* + *gaps still `OPEN` or `UNRESOLVABLE`*. The manifest row for `BAR_5M` is `COMPLETE` only when the last term is zero and step 2 found nothing missing.

This proves agreement with the vendor's REST record. It cannot prove the REST record is itself
complete; nothing available to this system can.

### 13.6 Interface exported to P3.3

```python
# src/data/stream.py — signatures only; the consumer is P3.3
from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from domain.models import Bar


class StreamGapNotice(BaseModel):
    """Delivered instead of a bar when a window could not be reconciled."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    instrument_id: UUID
    window_start: datetime      # UTC
    gap_id: UUID                # the ingest_gap row
    reconciled: bool            # False: the instrument has an OPEN gap


class HeldNamesBarFeed:
    async def start(self, instrument_ids: Sequence[UUID]) -> None:
        """Connect, subscribe and begin delivering events for these instruments."""
    async def set_instruments(self, instrument_ids: Sequence[UUID]) -> None:
        """Replace the subscribed set."""
    def events(self) -> AsyncIterator[Bar | StreamGapNotice]:
        """Completed 5-minute bars and gap notices, under the guarantees stated below."""
    async def reconcile_session_close(self) -> None:
        """Run the session-close check of §13.5."""
    async def stop(self) -> None:
        """Unsubscribe and close. Idempotent."""
```

Guarantees: bars for one instrument are delivered in ascending `as_of`; a bar is delivered only
after its row is committed; after a disconnect, no bar later than the gap is delivered for an
instrument until that instrument's gap rows have a resolution or a `StreamGapNotice` with
`reconciled = False` has been delivered for it. What P3.3 does on that notice is P3.3's.

---

## 14. Cross-provider reconciliation

### 14.1 What is compared

| Kind | Primary | Other | When |
|---|---|---|---|
| `REVISION` | Stored `bar_daily` row | The same provider, re-fetched | Every daily run, for the previous sequenced session (§12.1 step 6); every `DUPLICATE_CONFLICT` |
| `SECOND_SOURCE` | Stored bar | A second provider's bar for the same `(instrument_id, ts)` | Only where a second **consolidated** source exists. Before stage 5 none is bought for US daily bars (Alpaca's free tier is IEX-only and is not used, rule N6), so in production this kind is empty until then. The test of §25 exercises it with fixtures |
| `STREAM_VS_REST` | Stored 5-minute row | Alpaca REST | §13.5 |
| `N7_FUNDAMENTALS` | FMP metric | EDGAR reported metric | §19.3 |

### 14.2 Tolerance `[DEFAULT-4]`

| Field | Tolerance | Source |
|---|---|---|
| `open`, `high`, `low`, `close` | `abs(primary − other) ≤ tick`, where `tick` is the `tick_size_regime` row in force for `(market, symbol or '*', trading_date)` | `[FROZEN P0.2 §10.3]` table. No row: the comparison is `DISAGREE` and `MISSING_TICK_REGIME` is recorded. Never a default of 0.01. A symbol-specific row and a `*` row that both cover the date: also `DISAGREE` with `MISSING_TICK_REGIME`, because no frozen spec says which applies `[P21-26]` |
| `volume` | `abs(primary − other) ≤ reconciliation.volume_ratio × max(primary, other)` | `volume_ratio = 0.05`, **`ASSUMPTION [A-1]`**, to be replaced by a measurement |
| `REVISION` of any field | Exact. The same provider re-asked must return the same bar | By definition of a revision: one provider, one key, two answers |
| Fundamentals metric | `[OQ-10]` — "materially" is not defined by SPEC-P0.2 | Until it closes, every numeric difference is `DISAGREE` |

### 14.3 Outcome and authority

| Outcome | Stored |
|---|---|
| `WITHIN_TOLERANCE` | Nothing per field. Counted in the manifest's `compared_count` |
| `DISAGREE` | One `ingest_reconciliation` row per disagreeing field, with both values, the tolerance, and `authority_provider` |
| `PRIMARY_MISSING` / `OTHER_MISSING` | One row. A bar the second source has and the primary lacks is **not** copied into `bar_*` (IR-20) |

The stored bar is always the primary's. `authority_provider` is the primary for bars and
`SEC_EDGAR` for fundamentals. **This phase records the disagreement and stops**; whether the
instrument's data is accepted is P2.2's verdict (its layer 5).

---

## 15. Failure policy and the absence contract

### 15.1 Failure kinds

```python
# src/data/enums.py (continued)
class FailureKind(StrEnum):
    PROVIDER_UNREACHABLE = "PROVIDER_UNREACHABLE"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_HTTP_ERROR = "PROVIDER_HTTP_ERROR"
    THROTTLED = "THROTTLED"                          # after retries were exhausted
    QUOTA_REFUSED_LOCAL = "QUOTA_REFUSED_LOCAL"
    CREDENTIAL_INVALID = "CREDENTIAL_INVALID"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    INCOMPLETE_RESPONSE = "INCOMPLETE_RESPONSE"
    UNDOCUMENTED_TIMEZONE = "UNDOCUMENTED_TIMEZONE"
    FUTURE_TIMESTAMP = "FUTURE_TIMESTAMP"
    PRECISION_EXCEEDED = "PRECISION_EXCEEDED"
    UNKNOWN_SYMBOL = "UNKNOWN_SYMBOL"
    AMBIGUOUS_SYMBOL = "AMBIGUOUS_SYMBOL"
    UNKNOWN_INSTRUMENT_TYPE = "UNKNOWN_INSTRUMENT_TYPE"
    UNKNOWN_CORPORATE_ACTION = "UNKNOWN_CORPORATE_ACTION"
    MISSING_SESSION = "MISSING_SESSION"
    MISSING_TICK_REGIME = "MISSING_TICK_REGIME"
    DOMAIN_VALIDATION_FAILED = "DOMAIN_VALIDATION_FAILED"
    DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"
    NO_DISSEMINATION_EVIDENCE = "NO_DISSEMINATION_EVIDENCE"
    STREAM_ERROR = "STREAM_ERROR"
    STREAM_SILENT_LOSS = "STREAM_SILENT_LOSS"
    CLOCK_SKEW = "CLOCK_SKEW"
    CACHE_UNREACHABLE = "CACHE_UNREACHABLE"
    STAGE_BUDGET_EXCEEDED = "STAGE_BUDGET_EXCEEDED"
    DB_WRITE_FAILED = "DB_WRITE_FAILED"


class ManifestStatus(StrEnum):
    COMPLETE = "COMPLETE"        # every expected record is present; no failure
    INCOMPLETE = "INCOMPLETE"    # the fetch ran; at least one expected record is absent or failed
    FAILED = "FAILED"            # the fetch did not run to its end
    NO_SESSION = "NO_SESSION"    # the exchange was closed on this date, inside calendar coverage


class GapKind(StrEnum):
    MISSING_EXPECTED = "MISSING_EXPECTED"
    STREAM_DISCONNECT = "STREAM_DISCONNECT"


class GapState(StrEnum):
    OPEN = "OPEN"
    RESOLVED_FILLED = "RESOLVED_FILLED"
    RESOLVED_NO_DATA_AT_SOURCE = "RESOLVED_NO_DATA_AT_SOURCE"
    UNRESOLVABLE = "UNRESOLVABLE"


class ReconKind(StrEnum):
    REVISION = "REVISION"
    SECOND_SOURCE = "SECOND_SOURCE"
    STREAM_VS_REST = "STREAM_VS_REST"
    N7_FUNDAMENTALS = "N7_FUNDAMENTALS"
```

### 15.2 On a provider error

**Record the failure. Never substitute, never carry forward, never interpolate, never default.**
Concretely: one `ingest_failure` row; the affected records are absent from the store; the manifest
status is not `COMPLETE`; the process exits non-zero. No code path in `src/data/` writes a market
value that did not arrive in a vendor response for exactly that key.

`DB_WRITE_FAILED` cannot always be recorded in the database it describes. When the failure row
itself cannot be written, the process logs to standard error and exits with code 1; the absence of
a `COMPLETE` manifest row for the run is the durable signal.

### 15.3 What downstream sees when data is absent `[DEFAULT-7]`

| A consumer asks | It must read | And treat as |
|---|---|---|
| "Is `(market, trading_date, data_type)` usable?" | The latest `ingest_manifest` row by `finished_at` for that key and provider | Usable only when `status = COMPLETE`. **No row at all means not ingested, never "fine"** |
| "Does instrument *i* have its bar for *D*?" | The `bar_daily` row | Absent row = absent datum. The `ingest_gap` and `ingest_failure` rows for `(i, D)` say why |
| "Was the exchange closed?" | A `NO_SESSION` manifest row for that date | Closed. Distinct from missing |
| "Is this bar disputed?" | `ingest_reconciliation` rows for `(i, ts)` with outcome other than `WITHIN_TOLERANCE` | A fact for P2.2 to rule on |

There is no sentinel row, no zero bar, no `NULL` price. `bar_*` cannot hold one (`CHECK (open > 0)`).

---

## 16. Freshness and clock

### 16.1 Freshness per data type `[DEFAULT-8]`

This phase **states the fact**; `DATA-001`, P2.2 and P2.9 decide what a stale fact forbids. Let *S*
be the most recent session of the instrument's exchange with `counts_for_sequencing = true` and
`regular_close_utc ≤ now`.

| Data type | Fresh when | Source of the threshold | Edge case |
|---|---|---|---|
| `BAR_DAILY`, `REFERENCE`, `CORPORATE_ACTION` | The manifest for *S* is `COMPLETE` | `[DEFAULT-8]` | A later rerun that writes `FAILED` or `INCOMPLETE` after a `COMPLETE` makes the type not fresh: the latest row wins. A `SPECIAL` session is never *S*. No manifest row for *S* is not fresh, whatever older rows say |
| `FUNDAMENTALS`, `EDGAR_FILING`, `INSIDER_FILING`, `MACRO` | The manifest for *S* is `COMPLETE` | `[DEFAULT-8]`. A manifest says the scheduled fetch succeeded; it does not say a new filing or observation existed | A session on which nothing was scheduled still writes a manifest with `expected_count = 0`; that is `COMPLETE` and fresh. Macro ingest disabled in config writes no manifest and is never fresh |
| `FX_RATE` | An `fx_rate` row exists for the accounting date | `[FROZEN FX-001, I10]` | The accounting date is the UTC date on which the session closes (ADR-15 §7). A date on which the source publishes no rate has no row and is not fresh; the previous date's rate is never used |
| `CALENDAR` | Coverage extends at least `calendar.min_forward_coverage_sessions` sequenced sessions past *S* | `ASSUMPTION [A-8]` | Coverage is counted in sequenced sessions actually loaded, so a range that ends in a holiday run covers fewer sessions than its calendar days suggest |
| `BAR_5M` | 600 s since the last received message for the symbol | `[FROZEN P0.3 §15.1; policy.yaml stale_bar_critical_seconds]`. Evaluated by P3.3, not here | Suspended while the symbol is halted (RULE-B12c). P2.1 supplies only the receive time of the last message; P3.3 runs the timer |
| `RAW_NEWS` | The last successful poll ended within `2 × news.poll_interval_seconds` | `ASSUMPTION [A-4]` | A poll that returned no items is a successful poll. A poll that failed part-way through its pages is not, and the poll end time does not advance |

The research summary's "reject data older than 5 s" and `DATA-001`'s 600 s are different numbers
for what the summary treats as one rule (X3R-C6, open). Neither is applied to batch data here.

### 16.2 Clock

| Rule | Detail | Edge case |
|---|---|---|
| The host must run a time-synchronisation daemon | A P6.4 deployment requirement, stated here because every `retrieved_at` depends on it | A daemon that is running but not synchronised is caught only by the offset check below; the daemon's own status is not trusted |
| Pre-flight offset check | At the start of every run and every stream session, query the configured time servers by SNTP and compute the offset. `abs(offset) > clock.max_skew_seconds` on the median of the answers, or fewer than `clock.min_servers_answering` answers: `CLOCK_SKEW`, exit code 2 `[FROZEN P0.3 §13.1 row 20]` | An offset exactly equal to the limit passes: the comparison is `>`. Answers on both sides of zero are judged by their median, not their spread. Exactly `clock.min_servers_answering` answers is enough |
| `clock.max_skew_seconds` | `1`, **`ASSUMPTION [A-2]`**. It must be below the 3 s delivery budget of SPEC-P0.3 §6.2 stage 1 or that budget cannot be measured | Config validation rejects a value of 3 or more; it does not clamp it |
| Time servers | Listed in `ingest.yaml`. No default is supplied: an empty list fails config validation | A server that does not answer within `client.request_timeout_seconds` counts as not answering |
| Skew in comparisons | A vendor timestamp is "in the future" only when it exceeds `retrieved_at + clock.max_skew_seconds` (§7.1 step 2). Staleness against a session close uses the calendar instant, not a vendor clock | A vendor timestamp exactly at `retrieved_at + clock.max_skew_seconds` is accepted |
| The stream | The offset check repeats every `clock.recheck_seconds` while the stream is up; a breach closes the stream with `CLOCK_SKEW` | A breach found by a recheck closes the stream. Bars already committed stay; every window from the breach to the close becomes a `STREAM_DISCONNECT` gap |

---

## 17. Redis cache

Redis holds **no system-of-record state and no market value** `[FROZEN P0.3 §13.1 row 17]`. Bars,
prices, rates and fundamentals are never cached by this phase. Three read-through caches only:

| Key | Value | TTL (s) | Invalidated when |
|---|---|---|---|
| `ingest:v1:{cfg}:session:{exchange}:{trading_date}` | The session row, or the literal `CLOSED` inside coverage | 86,400 | A calendar load commits |
| `ingest:v1:{cfg}:symref:{provider_id}:{key_kind}:{provider_symbol}:{date}` | `instrument_id` | 3,600 | A reference load commits |
| `ingest:v1:{cfg}:manifest:{market}:{trading_date}:{data_type}:{provider_id}` | Latest manifest status and `finished_at` | 60 | A manifest row commits |

`{cfg}` is the first 12 hex characters of the ingest config hash, so a config change orphans every
old key. All three TTLs are `ASSUMPTION [A-9]`.

| Rule | Detail | Edge case |
|---|---|---|
| A miss | Reads the database and repopulates. **A miss never yields a default, an empty set or "open"** | A TTL that expires between a read and its use changes nothing: no cached value is a market value |
| A negative result | Not cached, except `CLOSED`, which is a positive statement backed by coverage (IR-15) | `CLOSED` is written only for a date inside recorded coverage. For a date outside it nothing is cached and the lookup raises `MISSING_SESSION` every time |
| Invalidation | The writer deletes the affected keys **after** its transaction commits. A crash between the two leaves a stale key for at most its TTL; the three cached values are tolerant of that by construction — the session row is immutable (IR-17), a symbol reference changes only with a reference load, and a manifest status is re-read by any consumer that acts on it | A Redis restart that drops every key is a run of misses, not an error |
| Stampede guard | Before repopulating, `SET {key}:lock <token> NX PX 5000`. The holder reads the database and sets the key. A non-holder waits up to 5 s, polling the key; if it is still absent it reads the database itself. The database is the truth, so the guard bounds load; correctness does not depend on it | A lock holder that dies leaves the lock to expire; waiters then read the database themselves. Two holders after an expiry write the same value |
| Redis unreachable | The run aborts: `CACHE_UNREACHABLE`, exit code 2 `[FROZEN P0.3 §13.1 row 17]` | Unreachable at pre-flight: exit 2, nothing fetched. Becoming unreachable mid-run: the run stops at the next cache call, rows already committed stay, and unfinished data types are `FAILED` |
| Address | A Vault reference in `ingest.yaml`. `INFRA_ENV_ALLOWLIST` has no Redis entry and is frozen `[P21-15]` | A reference that resolves to an empty value fails pre-flight as `CACHE_UNREACHABLE` |

---

## 18. Raw news snapshot

**Ownership (O-2).** P2.1 writes `trading.raw_news_snapshot` and nothing else about news. It does
not sanitise, does not write `news_item` or `news_instrument`, does not resolve news symbols to
instruments, and has no opinion on what a `NewsItem` means.

| Rule | Detail | Edge case |
|---|---|---|
| Poll | `NewsProvider.fetch_news` over `[last successful poll end − news.revision_lookback_seconds, now]`, every `news.poll_interval_seconds`. Both `ASSUMPTION [A-4]` | The first poll ever has no previous end and starts at `now − news.revision_lookback_seconds`. Two polls that return the same unchanged item write one row |
| First sighting | `revision_seq = 1`, `first_seen_at = retrieved_at`. Headline, summary and body are stored exactly as received (rule N16) | An item first seen days after its `created_at` still gets `first_seen_at = retrieved_at`. The vendor's `created_at` is stored and is never used as the first-seen time |
| A later change | Detected when `vendor_updated_at` differs from the latest stored revision's, **or** `content_sha256` differs. A new row, `revision_seq` + 1. Never an overwrite | Any difference in `vendor_updated_at`, forwards or backwards, is a revision even when the text is identical: the vendor said it changed. A change to `symbols`, `author`, `source` or `url` alone, with `vendor_updated_at` unchanged, is not detected |
| `content_sha256` | SHA-256 over the UTF-8 bytes of `headline`, `summary` and `content`, each followed by one `0x00` byte, in that order; an absent field contributes only its `0x00` | An absent field and an empty string hash identically. The stored column keeps the distinction: `NULL` against an empty string |
| Unchanged | No write | Unchanged means both `vendor_updated_at` and `content_sha256` equal the latest stored revision's |
| Oversize body | A `content` longer than 1,000,000 characters is `SCHEMA_VIOLATION` and is **not** truncated and not stored, `ASSUMPTION [A-5]` | Exactly 1,000,000 characters is accepted. A rejected item is returned again by later polls inside the look-back and is rejected each time, with one failure row per poll |
| No backfill | §10.1 | An item published before collection began and first returned by a live poll is stored, with a truthful `first_seen_at` |
| Untrusted | Every text column is untrusted DATA (rule N14). No code in `src/data/` interprets it, renders it, or passes it to anything but the insert | Vendor text is never copied into `ingest_failure.detail` or a log line; a failure about a news item names its `vendor_id` and hashes only |

**Hand-off contract to P4.1** — what P2.1 guarantees and nothing more: the row for
`(provider_id, vendor_id, revision_seq = 1)` carries the text as first received and a truthful
`first_seen_at`; later revisions have strictly increasing `revision_seq` and non-decreasing
`first_seen_at`; rows are never changed or deleted. `news_item.first_seen_at` for revision 1 can
therefore be taken from this row.

**Limitation `[DEFAULT-6]`.** `app_rw` can read this table and is the only application role. The
table is unreachable from LLM-bound code only because no module outside `src/data/` and the future
sanitiser is permitted to import the accessor — a convention a lint can check, not a permission.
A database-enforced boundary needs a second role, which is a P4.1 or P6.2 decision.

---

## 19. EDGAR and macro

### 19.1 EDGAR indexes — rule N2

Every index retrieved is stored whole in `edgar_index_snapshot`, keyed by its SHA-256, before
anything is derived from it. An index is never re-derived from a later retrieval: a filing absent
after a Saturday rebuild stays in every snapshot that held it. Retrieving bytes identical to a
stored snapshot writes nothing.

### 19.2 Filings and the dissemination rule — rule N1

`disseminated_at` is computed, never taken from a vendor `[DEFAULT-12]`:

| Form | `accepted_at` in Eastern Time | `disseminated_at` | Edge case |
|---|---|---|---|
| Any form except 3, 4, 5 | At or before 17:30 on an EDGAR business day | `accepted_at` | Exactly 17:30:00 is at or before. Eastern Time is resolved per date from the IANA zone, so the cutoff is 21:30 or 22:30 UTC by season. A form type the adapter cannot classify as 3, 4 or 5 uses this, the earlier cutoff |
| Any form except 3, 4, 5 | After 17:30 | 06:00 Eastern on the next EDGAR business day, `ASSUMPTION [A-13]` | Across a weekend, Friday evening goes to Monday |
| Forms 3, 4, 5 | At or before 22:00 | `accepted_at` | Exactly 22:00:00 is at or before |
| Forms 3, 4, 5 | After 22:00 | 06:00 Eastern on the next EDGAR business day, `ASSUMPTION [A-13]` | An `accepted_at` outside EDGAR's stated acceptance hours is stored and treated as after the cutoff; it is not rejected |

17:30 and 22:00 are `[V-P0.2 §3.8]`, as is "disseminated the next business day". **The instant on
that day is not recorded.** 06:00 Eastern is the hour EDGAR opens ("Accepts filings Mon–Fri
06:00–22:00 ET") and so the earliest it could be; it is used as `ASSUMPTION [A-13]`, and if
dissemination is in fact later the difference is look-ahead. **Which days are EDGAR business days
is not recorded in any frozen spec either** `[OQ-30]`; until it is, "next business day" is computed as the next Monday to
Friday and every row so computed across a weekend-adjacent federal holiday is suspect. Propagation
latency after acceptance is unmeasured `[V-P0.2 M-8]`; §21 measures it.

A filing later absent from a rebuilt index gets a **new** `edgar_filing` row with
`observed_state = ABSENT_AFTER_REBUILD`. Nothing derived from the original is withdrawn by this
phase.

### 19.3 Fundamentals and rule N7

1. FMP supplies metrics per `(instrument, period_end)`. EDGAR supplies the filing record and the reported metrics for the same CIK and period.
2. No matching `edgar_filing` row: `NO_DISSEMINATION_EVIDENCE`. The FMP record is not stored `[DEFAULT-12]`.
3. With a match: the FMP row is stored with `filed_at` = `accepted_at`, `disseminated_at` from §19.2, `source = FMP`, `restatement_seq` = one more than the highest stored for that `(instrument_id, period_end)`, starting at 1.
4. Each metric in the configured comparison list (`fundamentals.n7_metrics`, **`[OQ-10]`**: the list and the metric-name mapping between the two sources are not defined anywhere) is compared. A disagreement writes `ingest_reconciliation` rows of kind `N7_FUNDAMENTALS` with `authority_provider = SEC_EDGAR`.
5. On disagreement `[DEFAULT-5]`: the FMP row's `knowledge_to` is set, and an EDGAR-sourced row is inserted at the **next** `restatement_seq` with `source = SEC_EDGAR` and the same `filed_at` and `disseminated_at`. The unique constraint forbids reusing the sequence number `[P21-13]`. A reader therefore sees a "restatement" that is really a source correction; only the reconciliation row tells them apart.
6. A later issuer restatement (a new filing for the same period) is a new row at the next `restatement_seq` with its own `disseminated_at`.

### 19.4 Forms 3, 4 and 5

The filing record goes to `edgar_filing`. The document goes to `insider_filing_raw`, whole and
immutable. **No transaction is parsed in v0.1**: the fields to extract are `[OQ-9]`. The raw
document is untrusted DATA under the same boundary as raw news.

### 19.5 Macro — rule N3

| Rule | Detail | Edge case |
|---|---|---|
| Series | Only those in `macro.series_allowlist`. **The list is P2.6's requirement and is empty in this spec** `[OQ-31]`. `macro.enabled: true` with an empty list fails config validation | A series removed from the allowlist stops being ingested; its stored observations stay |
| Copyright screen | Before a series is first ingested, `fetch_series_notes` is read; a series whose notes contain the word "Copyright" is recorded in `macro_series` with `third_party_copyright = true` and **is not ingested** `[V-P0.2 §3.9]` | A series whose notes cannot be fetched is not ingested: an unread note is not a clean note |
| Vintage | Every observation is stored with its `vintage_date`. A revised value is a new row. A reader takes, per `observation_date`, the row with the greatest `vintage_date` at or before its decision date and `retrieved_at` at or before its knowledge cutoff | A vintage date earlier than one already stored for the same observation is a new row. The same `(series_id, observation_date, vintage_date)` with a different value is `DUPLICATE_CONFLICT` |
| A non-numeric vendor value | Not stored; counted in `skipped_count`. How FRED marks a missing observation is `[OQ-24]` | A value that parses as a number but is not finite is treated as non-numeric |
| Throttling | Adaptive backoff on `429` and `423`; no request budget (rule N8) | `423` and `429` are both backoff signals. Any other 4xx is not retried |
| Attribution | The mandatory FRED notice `[V-P0.2 §3.9]` belongs on whatever displays macro data — P6.1. Recorded so it is not lost | Applies to the internal Grafana panel SPEC-P0.2 names, not only to an external display |

### 19.6 FX

One rate per `(as_of_date, base, quote)`, written once (ADR-15 §5). A missing rate is no row;
`FX-001` then blocks new entries in both pools `[FROZEN I10]`. The rate is never carried forward
from the previous date. The source endpoint is `[OQ-7]`; `FX_RATE_RECORDED` is effectful and
therefore gated by condition 9 (§20).

---

## 20. Audit events

**Nothing in this section may be implemented until X5 condition 9 is decided.** This phase makes
no decision about the hash of record, the preimage, the reproducibility bundle or who owns the
audit writer. It states only which registered events P2.1 would produce and with what payload, so
that the decision has P2.1's needs in front of it.

`EVENT_REGISTRY` (`src/audit/events.py`) names `P2.1_INGEST` as producer of three types:

| Event | Class | Effectful | Proposed trigger in P2.1 | Required payload keys `[FROZEN registry]` |
|---|---|---|---|---|
| `DATA_RECEIVED` | `EVALUATION` | no | One per manifest row with `stored_count > 0` | `source`, `data_type`, `row_count`, `as_of`, `retrieved_at`, `input_hash` |
| `FX_RATE_RECORDED` | `NAV` | yes | Around the `fx_rate` insert, by `write_before_act` | `as_of_date`, `base`, `quote`, `rate`, `source` |
| `CORPORATE_ACTION_APPLIED` | `ACTION` | yes | Around each `corporate_action` insert, by `write_before_act` | `instrument_id`, `action_type`, `effective_date`, `ratio` |

Every payload value is a string (SPEC-P1.4 §6.2 rule 4 bans JSON numbers): `row_count` and `ratio`
included.

Carried, **not resolved**:

| Id | Issue |
|---|---|
| `[OQ-13]` | `DATA_RECEIVED`'s registered trigger is "accepted into the store **after quality checks pass**", but its producer is ingest and the quality gate (P2.2) runs on stored data. `DATA_REJECTED` is P2.2's, so P2.1 has no registered event for its own rejections. `CORPORATE_ACTION_APPLIED`'s trigger says "applied to stored history"; under rule N9 nothing is applied to stored bars |
| `[OQ-12]` | `RUN_STARTED` and `RUN_FINISHED` belong to `P6.4_ORCHESTRATOR`, which does not exist until Stage 6. Which component emits them for an ingest run before then is not assigned |
| `[OQ-14]` | `Q-P1.2-7` / X3R-M1 |
| `[P21-20]` | A `run_context` row requires a `config_version` row, which requires `audit_event_id`. So no `run_context` row can exist before conditions 9 and 10. P2.1's own tables therefore carry `run_id` without a foreign key `[DEFAULT-15]` |
| — | `successor_link.audit_event_id` is `NOT NULL`: a merger cannot be stored before condition 9 |

Until condition 9: every fact an event would carry is already in a manifest, failure, gap or
reconciliation row. Those rows are operational records. **They are not the audit trail and are not
a substitute for it**; `[CONST-5]` is satisfied for `fx_rate` and `corporate_action` only once the
events above can be written.

---

## 21. Measurements this phase takes

| Id | Measurement | Method | Feeds |
|---|---|---|---|
| `Q-P1.1-6` | Maximum decimal scale of a vendor trade price | (a) Standing: every `PRECISION_EXCEEDED` on a price, and the maximum scale seen per run recorded in the manifest's `detail`. (b) One-off: one month of trade prints for the ingest set from Massive, scale computed in the adapter, prints discarded (`TRADE_PRECISION_SAMPLE`). The trades endpoint and its fields are `[OQ-22]` | X5 condition 4; P2.2 |
| P0.3 Q-5 | FMP payload size per statement request | `response_bytes` in `provider_quota_usage`, per request, over the first backfill | RULE-B5 |
| P0.3 Q-7 | Whether a Massive daily bar changes after 21:45 UTC | The `REVISION` rows of §12.1 step 6, over the first 20 sessions | §12 schedule |
| P0.2 M-8 | EDGAR acceptance-to-availability delay | First `retrieved_at` minus `accepted_at`, per filing, with a poll interval recorded beside it | §19.2 |
| P0.2 M-12 | News revision factor and materiality | Count and diff of `revision_seq > 1` rows | P5.1 |
| P0.1 A18 | News items per session | Row count in `raw_news_snapshot` per session | P0.3 storage model |
| `[A-1]` | Volume agreement between two consolidated sources | Distribution of volume differences once a second source exists | §14.2 |
| P0.3 Q-12 | Zero-trade bar emitted or omitted | The `RESOLVED_NO_DATA_AT_SOURCE` rows of §13.4 | RULE-B12d |

A measurement result is reported to the Owner and recorded where the question lives. It does not
change a threshold by itself.

---

## 22. Migration 0002 — P2.1-owned tables

**Specified, not created, not applied.** The file will be `migrations/0002_ingest.sql`, following
0001's naming. How it is applied (`scripts/apply-migration.sh` applies 0001; SPEC-P1.2 §11 names
Alembic and a `migrations/versions/` directory that does not exist, X3R-C12) is `[OQ-32]`.

Rules the migration obeys:

1. It creates objects only. It contains no `ALTER`, `DROP`, `CREATE OR REPLACE` or `COMMENT` on any object 0001 created, and no `INSERT`, `UPDATE` or `DELETE` on any 0001 table.
2. It **uses** two 0001 objects without changing them: the function `trading.deny_mutation()` and the extension schema's `gen_random_uuid()`.
3. Every table is append-only: `app_rw` gets `SELECT` and `INSERT`, and each table gets `no_update` and `no_delete` triggers, `ENABLE ALWAYS`, exactly as 0001 does for `fx_rate`.
4. `backtest_ro` and `metrics_ro` receive **nothing**. 0001's default privileges already give `app_rw` `SELECT, INSERT` on new tables; the grants are still written out so the migration does not depend on a default.
5. No table is a hypertable. Expected volumes are small `ASSUMPTION [A-6]`, and a plain table keeps X5 Finding A's hypertable trigger bypass out of these tables.
6. No retention policy. These are provenance records.
7. All `timestamptz` values are UTC. All `date` values are exchange-local unless the comment says otherwise.

```sql
-- migrations/0002_ingest.sql — SPEC-P2.1-INGEST v0.4 (DRAFT). NOT APPLIED.
SET search_path = trading, extensions, pg_catalog;

-- ===== 22.1 ingest_manifest =====
-- One row per (run, market, session, data type, provider): what was expected, what
-- arrived, what is in the store. The latest row by finished_at is the status of record.
-- run_id has NO foreign key to run_context: see SPEC-P2.1 [DEFAULT-15] / [P21-20].
CREATE TABLE trading.ingest_manifest (
    manifest_id        uuid        NOT NULL DEFAULT extensions.gen_random_uuid(),
    run_id             uuid        NOT NULL,
    market             text        NOT NULL CHECK (market IN ('US','IN')),
    trading_date       date        NOT NULL,                 -- the session the run is for
    data_type          text        NOT NULL CHECK (data_type IN (
                           'REFERENCE','CALENDAR','BAR_DAILY','BAR_5M','BAR_5M_VALIDATION',
                           'CORPORATE_ACTION','FUNDAMENTALS','EDGAR_INDEX','EDGAR_FILING',
                           'INSIDER_FILING','MACRO','FX_RATE','RAW_NEWS','TRADE_PRECISION_SAMPLE')),
    provider_id        text        NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    status             text        NOT NULL CHECK (status IN ('COMPLETE','INCOMPLETE','FAILED','NO_SESSION')),
    expected_count     integer     NOT NULL CHECK (expected_count  >= 0),  -- records expected (section 11)
    received_count     integer     NOT NULL CHECK (received_count  >= 0),  -- wire records parsed
    stored_count       integer     NOT NULL CHECK (stored_count    >= 0),  -- rows inserted by this run
    duplicate_count    integer     NOT NULL CHECK (duplicate_count >= 0),  -- identical to a stored row
    skipped_count      integer     NOT NULL CHECK (skipped_count   >= 0),  -- deliberately not stored
    failed_count       integer     NOT NULL CHECK (failed_count    >= 0),  -- ingest_failure rows written
    present_count      integer     NOT NULL CHECK (present_count   >= 0),  -- expected records in the store at the end
    compared_count     integer     NOT NULL CHECK (compared_count  >= 0),  -- fields compared (section 14)
    disagreed_count    integer     NOT NULL CHECK (disagreed_count >= 0),
    coverage_from      date        NULL,                     -- CALENDAR only: first date covered, inclusive
    coverage_to        date        NULL,                     -- CALENDAR only: last date covered, inclusive
    input_hash         text        NOT NULL CHECK (input_hash ~ '^[0-9a-f]{64}$'),
                                   -- SHA-256 over the response_sha256 values of the run, sorted, joined by '\n'
    ingest_config_hash text        NOT NULL CHECK (ingest_config_hash ~ '^[0-9a-f]{64}$'),
    code_version       text        NOT NULL CHECK (length(code_version) BETWEEN 7 AND 40),
    detail             text        NULL CHECK (detail IS NULL OR length(detail) <= 4000),
    started_at         timestamptz NOT NULL,
    finished_at        timestamptz NOT NULL,
    PRIMARY KEY (manifest_id),
    CONSTRAINT manifest_finished_after_started CHECK (finished_at >= started_at),
    CONSTRAINT manifest_complete_means_complete CHECK (
        status <> 'COMPLETE' OR (present_count = expected_count AND failed_count = 0)),
    CONSTRAINT manifest_no_session_is_empty CHECK (
        status <> 'NO_SESSION' OR (expected_count = 0 AND received_count = 0 AND stored_count = 0)),
    CONSTRAINT manifest_coverage_pair CHECK ((coverage_from IS NULL) = (coverage_to IS NULL)),
    CONSTRAINT manifest_coverage_ordered CHECK (coverage_from IS NULL OR coverage_to >= coverage_from),
    CONSTRAINT manifest_coverage_is_calendar CHECK (coverage_from IS NULL OR data_type = 'CALENDAR'),
    CONSTRAINT manifest_disagreed_le_compared CHECK (disagreed_count <= compared_count)
);
CREATE INDEX ingest_manifest_status_idx
    ON trading.ingest_manifest (market, trading_date, data_type, provider_id, finished_at DESC);

-- ===== 22.2 ingest_checkpoint =====
-- Backfill progress. Append-only; the latest row per (job_id, partition_key) wins.
CREATE TABLE trading.ingest_checkpoint (
    checkpoint_id  uuid        NOT NULL DEFAULT extensions.gen_random_uuid(),
    job_id         uuid        NOT NULL,
    data_type      text        NOT NULL CHECK (length(data_type) BETWEEN 1 AND 32),
    provider_id    text        NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    market         text        NOT NULL CHECK (market IN ('US','IN')),
    partition_key  text        NOT NULL CHECK (length(partition_key) BETWEEN 1 AND 400),
    state          text        NOT NULL CHECK (state IN ('STARTED','COMMITTED','FAILED','PAUSED')),
    range_from     date        NULL,
    range_to       date        NULL,                         -- inclusive
    rows_stored    integer     NOT NULL DEFAULT 0 CHECK (rows_stored >= 0),
    cursor         text        NULL CHECK (cursor IS NULL OR length(cursor) <= 2000),  -- diagnosis only
    recorded_at    timestamptz NOT NULL,
    PRIMARY KEY (checkpoint_id),
    CONSTRAINT checkpoint_range_ordered CHECK (range_from IS NULL OR range_to IS NULL OR range_to >= range_from)
);
CREATE INDEX ingest_checkpoint_latest_idx
    ON trading.ingest_checkpoint (job_id, partition_key, recorded_at DESC);

-- ===== 22.3 ingest_failure =====
-- One row per failure. detail is OUR text (an exception class and message we wrote),
-- never vendor text: untrusted content does not land here.
CREATE TABLE trading.ingest_failure (
    failure_id      uuid        NOT NULL DEFAULT extensions.gen_random_uuid(),
    run_id          uuid        NOT NULL,
    occurred_at     timestamptz NOT NULL,
    market          text        NOT NULL CHECK (market IN ('US','IN')),
    data_type       text        NOT NULL CHECK (length(data_type) BETWEEN 1 AND 32),
    provider_id     text        NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    failure_kind    text        NOT NULL CHECK (failure_kind IN (
                        'PROVIDER_UNREACHABLE','PROVIDER_TIMEOUT','PROVIDER_HTTP_ERROR','THROTTLED',
                        'QUOTA_REFUSED_LOCAL','CREDENTIAL_INVALID','SCHEMA_VIOLATION',
                        'INCOMPLETE_RESPONSE','UNDOCUMENTED_TIMEZONE','FUTURE_TIMESTAMP',
                        'PRECISION_EXCEEDED','UNKNOWN_SYMBOL','AMBIGUOUS_SYMBOL',
                        'UNKNOWN_INSTRUMENT_TYPE','UNKNOWN_CORPORATE_ACTION','MISSING_SESSION',
                        'MISSING_TICK_REGIME','DOMAIN_VALIDATION_FAILED','DUPLICATE_CONFLICT',
                        'NO_DISSEMINATION_EVIDENCE','STREAM_ERROR','STREAM_SILENT_LOSS',
                        'CLOCK_SKEW','CACHE_UNREACHABLE','STAGE_BUDGET_EXCEEDED','DB_WRITE_FAILED')),
    instrument_id   uuid        NULL,
    provider_symbol text        NULL CHECK (provider_symbol IS NULL OR length(provider_symbol) <= 32),
    trading_date    date        NULL,
    window_start    timestamptz NULL,
    http_status     integer     NULL CHECK (http_status IS NULL OR http_status BETWEEN 100 AND 599),
    response_sha256 text        NULL CHECK (response_sha256 IS NULL OR response_sha256 ~ '^[0-9a-f]{64}$'),
    detail          text        NOT NULL CHECK (length(detail) BETWEEN 1 AND 2000),
    PRIMARY KEY (failure_id)
);
CREATE INDEX ingest_failure_run_idx ON trading.ingest_failure (run_id);
CREATE INDEX ingest_failure_subject_idx
    ON trading.ingest_failure (instrument_id, trading_date) WHERE instrument_id IS NOT NULL;

-- ===== 22.4 ingest_gap =====
-- An expected record that is absent. A resolution is a NEW row pointing at the gap.
CREATE TABLE trading.ingest_gap (
    gap_id          uuid        NOT NULL DEFAULT extensions.gen_random_uuid(),
    resolves_gap_id uuid        NULL,                        -- NULL on the row that opens the gap
    run_id          uuid        NOT NULL,
    recorded_at     timestamptz NOT NULL,
    market          text        NOT NULL CHECK (market IN ('US','IN')),
    data_type       text        NOT NULL CHECK (data_type IN ('BAR_DAILY','BAR_5M','BAR_5M_VALIDATION')),
    provider_id     text        NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    instrument_id   uuid        NOT NULL,
    trading_date    date        NOT NULL,
    window_start    timestamptz NOT NULL,                    -- the ts the absent bar would carry
    window_end      timestamptz NOT NULL,                    -- exclusive
    gap_kind        text        NOT NULL CHECK (gap_kind IN ('MISSING_EXPECTED','STREAM_DISCONNECT')),
    state           text        NOT NULL CHECK (state IN (
                        'OPEN','RESOLVED_FILLED','RESOLVED_NO_DATA_AT_SOURCE','UNRESOLVABLE')),
    detail          text        NULL CHECK (detail IS NULL OR length(detail) <= 2000),
    PRIMARY KEY (gap_id),
    CONSTRAINT gap_window_ordered CHECK (window_end >= window_start),
    CONSTRAINT gap_open_is_root CHECK ((state = 'OPEN') = (resolves_gap_id IS NULL)),
    CONSTRAINT gap_resolution_not_self CHECK (resolves_gap_id IS NULL OR resolves_gap_id <> gap_id)
);
CREATE INDEX ingest_gap_subject_idx ON trading.ingest_gap (instrument_id, data_type, window_start);
CREATE INDEX ingest_gap_resolution_idx ON trading.ingest_gap (resolves_gap_id) WHERE resolves_gap_id IS NOT NULL;

-- ===== 22.5 ingest_reconciliation =====
-- Evidence of a comparison that did not agree. Agreement is counted in the manifest.
CREATE TABLE trading.ingest_reconciliation (
    recon_id           uuid          NOT NULL DEFAULT extensions.gen_random_uuid(),
    run_id             uuid          NOT NULL,
    compared_at        timestamptz   NOT NULL,
    recon_kind         text          NOT NULL CHECK (recon_kind IN (
                           'REVISION','SECOND_SOURCE','STREAM_VS_REST','N7_FUNDAMENTALS')),
    market             text          NOT NULL CHECK (market IN ('US','IN')),
    data_type          text          NOT NULL CHECK (length(data_type) BETWEEN 1 AND 32),
    instrument_id      uuid          NOT NULL,
    key_ts             timestamptz   NULL,                   -- bars: the bar's ts
    period_end         date          NULL,                   -- fundamentals: the fiscal period end
    field              text          NOT NULL CHECK (length(field) BETWEEN 1 AND 120),
    primary_provider   text          NOT NULL CHECK (length(primary_provider) BETWEEN 1 AND 32),
    primary_value      numeric(28,6) NULL,                   -- NULL only when outcome = PRIMARY_MISSING
    other_provider     text          NOT NULL CHECK (length(other_provider) BETWEEN 1 AND 32),
    other_value        numeric(28,6) NULL,                   -- NULL only when outcome = OTHER_MISSING
    tolerance_kind     text          NOT NULL CHECK (tolerance_kind IN ('EXACT','TICK','RATIO','UNDEFINED')),
    tolerance_value    numeric(28,6) NULL,                   -- NULL for EXACT and UNDEFINED
    outcome            text          NOT NULL CHECK (outcome IN ('DISAGREE','PRIMARY_MISSING','OTHER_MISSING')),
    authority_provider text          NOT NULL CHECK (length(authority_provider) BETWEEN 1 AND 32),
    PRIMARY KEY (recon_id),
    CONSTRAINT recon_has_a_key CHECK ((key_ts IS NULL) <> (period_end IS NULL)),
    CONSTRAINT recon_missing_side_is_null CHECK (
        (outcome = 'PRIMARY_MISSING') = (primary_value IS NULL)
        AND (outcome = 'OTHER_MISSING') = (other_value IS NULL))
);
CREATE INDEX ingest_reconciliation_subject_idx
    ON trading.ingest_reconciliation (instrument_id, key_ts, period_end);

-- ===== 22.6 provider_instrument_ref =====
-- A provider's own identifier for one of our instruments. Append-only and date-versioned:
-- the row in force on a date is the one with the greatest effective_from at or before it.
CREATE TABLE trading.provider_instrument_ref (
    instrument_id   uuid        NOT NULL,
    provider_id     text        NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    key_kind        text        NOT NULL CHECK (key_kind IN (
                        'TICKER','CIK','COMPOSITE_FIGI','SHARE_CLASS_FIGI','INSTRUMENT_TOKEN')),
    effective_from  date        NOT NULL,                    -- exchange-local, inclusive
    provider_symbol text        NULL CHECK (provider_symbol IS NULL OR length(provider_symbol) BETWEEN 1 AND 64),
                                -- NULL: from effective_from this instrument has no such identifier
    recorded_at     timestamptz NOT NULL,
    PRIMARY KEY (instrument_id, provider_id, key_kind, effective_from)
);
CREATE INDEX provider_instrument_ref_lookup_idx
    ON trading.provider_instrument_ref (provider_id, key_kind, provider_symbol, effective_from DESC);

-- ===== 22.7 raw_news_snapshot =====
-- Rule N16: the first-receipt record. UNTRUSTED vendor text in every *_raw column
-- (rule N14 / [CONST-4]). P2.1 writes it; P4.1 reads it; news_item is P4.1's.
CREATE TABLE trading.raw_news_snapshot (
    provider_id       text        NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    vendor_id         text        NOT NULL CHECK (length(vendor_id) BETWEEN 1 AND 128),
    revision_seq      integer     NOT NULL CHECK (revision_seq >= 1),
    first_seen_at     timestamptz NOT NULL,                  -- retrieved_at of THIS revision
    vendor_created_at timestamptz NOT NULL,
    vendor_updated_at timestamptz NULL,
    headline_raw      text        NOT NULL CHECK (length(headline_raw) <= 4000),
    summary_raw       text        NULL CHECK (summary_raw IS NULL OR length(summary_raw) <= 20000),
    body_raw          text        NULL CHECK (body_raw IS NULL OR length(body_raw) <= 1000000),
    author_raw        text        NULL CHECK (author_raw IS NULL OR length(author_raw) <= 400),
    source_raw        text        NULL CHECK (source_raw IS NULL OR length(source_raw) <= 200),
    url_raw           text        NULL CHECK (url_raw IS NULL OR length(url_raw) <= 2000),
    symbols_raw       text[]      NOT NULL DEFAULT '{}',
    content_sha256    text        NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    response_sha256   text        NOT NULL CHECK (response_sha256 ~ '^[0-9a-f]{64}$'),
    run_id            uuid        NOT NULL,
    PRIMARY KEY (provider_id, vendor_id, revision_seq)
);
CREATE INDEX raw_news_snapshot_seen_idx ON trading.raw_news_snapshot (first_seen_at);

-- ===== 22.8 macro_series, macro_observation =====
CREATE TABLE trading.macro_series (
    series_id             text        NOT NULL CHECK (length(series_id) BETWEEN 1 AND 64),
    provider_id           text        NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    recorded_at           timestamptz NOT NULL,
    third_party_copyright boolean     NOT NULL,             -- notes contain 'Copyright': not ingested
    notes_sha256          text        NOT NULL CHECK (notes_sha256 ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (series_id, provider_id, recorded_at)
);

-- Rule N3: every value is kept with the date from which it was the published value.
CREATE TABLE trading.macro_observation (
    series_id        text          NOT NULL CHECK (length(series_id) BETWEEN 1 AND 64),
    observation_date date          NOT NULL,                -- the period the value describes
    vintage_date     date          NOT NULL,                -- first date this value was the published one
    value            numeric(28,6) NOT NULL,
    provider_id      text          NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    retrieved_at     timestamptz   NOT NULL,
    run_id           uuid          NOT NULL,
    PRIMARY KEY (series_id, observation_date, vintage_date),
    CONSTRAINT macro_vintage_not_before_observation CHECK (vintage_date >= observation_date)
);

-- ===== 22.9 edgar_index_snapshot =====
-- Rule N2: an index is stored whole, as retrieved, and never re-derived.
CREATE TABLE trading.edgar_index_snapshot (
    index_kind     text        NOT NULL CHECK (index_kind IN (
                       'DAILY','QUARTERLY','FULL','SUBMISSIONS','COMPANY_TICKERS')),
    index_ref      text        NOT NULL CHECK (length(index_ref) BETWEEN 1 AND 400),  -- path on the SEC host
    content_sha256 text        NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    content        bytea       NOT NULL,                     -- the response body, as received
    content_bytes  bigint      NOT NULL CHECK (content_bytes > 0),
    retrieved_at   timestamptz NOT NULL,
    run_id         uuid        NOT NULL,
    PRIMARY KEY (index_kind, index_ref, content_sha256)
);

-- ===== 22.10 edgar_filing =====
-- One row per observation of a filing. A filing that disappears after a rebuild gets
-- a second row; the first is never changed.
CREATE TABLE trading.edgar_filing (
    filing_key      text        NOT NULL CHECK (length(filing_key) BETWEEN 1 AND 64),
    observed_at     timestamptz NOT NULL,
    observed_state  text        NOT NULL CHECK (observed_state IN ('PRESENT','ABSENT_AFTER_REBUILD')),
    cik             text        NOT NULL CHECK (length(cik) BETWEEN 1 AND 16),
    instrument_id   uuid        NULL,                        -- NULL when the CIK maps to none of ours
    form_type       text        NOT NULL CHECK (length(form_type) BETWEEN 1 AND 16),
    accepted_at     timestamptz NOT NULL,
    disseminated_at timestamptz NOT NULL,                    -- computed, SPEC-P2.1 section 19.2
    period_end      date        NULL,
    document_ref    text        NOT NULL CHECK (length(document_ref) BETWEEN 1 AND 400),
    index_sha256    text        NOT NULL CHECK (index_sha256 ~ '^[0-9a-f]{64}$'),
    run_id          uuid        NOT NULL,
    PRIMARY KEY (filing_key, observed_at),
    CONSTRAINT edgar_disseminated_not_before_accepted CHECK (disseminated_at >= accepted_at)
);
CREATE INDEX edgar_filing_cik_idx ON trading.edgar_filing (cik, accepted_at DESC);

-- ===== 22.11 insider_filing_raw =====
-- Forms 3/4/5, the document as retrieved. UNTRUSTED. Not parsed in v0.1 ([OQ-9]).
CREATE TABLE trading.insider_filing_raw (
    filing_key      text        NOT NULL CHECK (length(filing_key) BETWEEN 1 AND 64),
    document_sha256 text        NOT NULL CHECK (document_sha256 ~ '^[0-9a-f]{64}$'),
    form_type       text        NOT NULL CHECK (length(form_type) BETWEEN 1 AND 16),
    document        bytea       NOT NULL,
    document_bytes  bigint      NOT NULL CHECK (document_bytes > 0),
    retrieved_at    timestamptz NOT NULL,
    run_id          uuid        NOT NULL,
    PRIMARY KEY (filing_key, document_sha256)
);

-- ===== 22.12 corporate_action_terms =====
-- Owner decision O-10 ([OQ-21]). The exact terms of a corporate action that 0001's
-- corporate_action cannot hold: its cash_amount is numeric(18,2) and its ratio numeric(18,6).
-- One row per SPLIT, REVERSE_SPLIT or CASH_DIVIDEND row of corporate_action, with the same
-- (action_id, knowledge_from), written in the same transaction.
-- No foreign key: 0002 adds no constraint that reaches into a 0001 table.
-- Unconstrained numeric is deliberate: it stores the vendor's decimal exactly, at any scale.
CREATE TABLE trading.corporate_action_terms (
    action_id             uuid        NOT NULL,              -- corporate_action.action_id
    knowledge_from        timestamptz NOT NULL,              -- corporate_action.knowledge_from of the row described
    action_type           text        NOT NULL CHECK (action_type IN ('SPLIT','REVERSE_SPLIT','CASH_DIVIDEND')),
    cash_amount_exact     numeric     NULL CHECK (cash_amount_exact IS NULL
                                          OR (cash_amount_exact > 0 AND cash_amount_exact < 'Infinity'::numeric)),
                                      -- per share, listing currency, vendor precision
    cash_currency         text        NULL CHECK (cash_currency IN ('USD','INR')),
    split_from            numeric     NULL CHECK (split_from IS NULL
                                          OR (split_from > 0 AND split_from < 'Infinity'::numeric)),  -- old shares
    split_to              numeric     NULL CHECK (split_to IS NULL
                                          OR (split_to > 0 AND split_to < 'Infinity'::numeric)),      -- new shares
    distribution_type     text        NULL CHECK (distribution_type IS NULL OR length(distribution_type) <= 32),
    frequency             integer     NULL CHECK (frequency IS NULL OR frequency BETWEEN 0 AND 365),
    record_date           date        NULL,
    declaration_date      date        NULL,
    cash_rounded_in_0001  boolean     NOT NULL,              -- TRUE: corporate_action.cash_amount <> cash_amount_exact
    ratio_rounded_in_0001 boolean     NOT NULL,              -- TRUE: corporate_action.ratio <> split_to / split_from
    provider_id           text        NOT NULL CHECK (length(provider_id) BETWEEN 1 AND 32),
    response_sha256       text        NOT NULL CHECK (response_sha256 ~ '^[0-9a-f]{64}$'),
    retrieved_at          timestamptz NOT NULL,
    run_id                uuid        NOT NULL,
    PRIMARY KEY (action_id, knowledge_from),
    CONSTRAINT cat_dividend_has_cash CHECK ((action_type = 'CASH_DIVIDEND') = (cash_amount_exact IS NOT NULL)),
    CONSTRAINT cat_cash_has_currency CHECK ((cash_amount_exact IS NULL) = (cash_currency IS NULL)),
    CONSTRAINT cat_split_has_both CHECK (
        (action_type IN ('SPLIT','REVERSE_SPLIT')) = (split_from IS NOT NULL AND split_to IS NOT NULL)
        AND (split_from IS NULL) = (split_to IS NULL)),
    CONSTRAINT cat_split_changes_count CHECK (split_from IS NULL OR split_from <> split_to),
    CONSTRAINT cat_dividend_fields_only_on_dividend CHECK (
        action_type = 'CASH_DIVIDEND'
        OR (distribution_type IS NULL AND frequency IS NULL
            AND record_date IS NULL AND declaration_date IS NULL)),
    CONSTRAINT cat_flags_match_type CHECK (
        (NOT cash_rounded_in_0001 OR action_type = 'CASH_DIVIDEND')
        AND (NOT ratio_rounded_in_0001 OR action_type IN ('SPLIT','REVERSE_SPLIT')))
);

-- ===== 22.13 append-only, enforced =====
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['ingest_manifest','ingest_checkpoint','ingest_failure','ingest_gap',
                             'ingest_reconciliation','provider_instrument_ref','raw_news_snapshot',
                             'macro_series','macro_observation','edgar_index_snapshot',
                             'edgar_filing','insider_filing_raw','corporate_action_terms']
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

-- ===== 22.14 grants =====
-- app_rw: SELECT and INSERT, nothing else. backtest_ro and metrics_ro: NOTHING.
REVOKE ALL ON trading.ingest_manifest, trading.ingest_checkpoint, trading.ingest_failure,
              trading.ingest_gap, trading.ingest_reconciliation, trading.provider_instrument_ref,
              trading.raw_news_snapshot, trading.macro_series, trading.macro_observation,
              trading.edgar_index_snapshot, trading.edgar_filing, trading.insider_filing_raw,
              trading.corporate_action_terms
    FROM PUBLIC;
GRANT SELECT, INSERT ON trading.ingest_manifest, trading.ingest_checkpoint, trading.ingest_failure,
              trading.ingest_gap, trading.ingest_reconciliation, trading.provider_instrument_ref,
              trading.raw_news_snapshot, trading.macro_series, trading.macro_observation,
              trading.edgar_index_snapshot, trading.edgar_filing, trading.insider_filing_raw,
              trading.corporate_action_terms
    TO app_rw;
```

The Owner's list of 2026-10-07 names eleven objects, which are twelve tables because "macro series
and observations" is two. The thirteenth, `corporate_action_terms`, was added by Owner decision O-10
of 2026-10-08. `trading.deny_mutation()` is defined in 0001 §9.3. Its body names the table through
`TG_TABLE_NAME` and raises for any row it is fired for, so by reading it serves any table; that
has **not been executed** against a 0002 table — `ASSUMPTION [A-14]`, part of `[OQ-32]`.

Violation semantics, for every table above: a row that breaks a `CHECK`, a key or a trigger is
rejected by the database; the writer records `DB_WRITE_FAILED` and the run's status is `FAILED`.

---

## 23. Ingest configuration file

`config/ingest.yaml` — P2.1-owned (O-5). It holds provider plumbing and ingest parameters. **It
holds no risk number and no policy rule; those stay in `config/policy.yaml`, which this phase reads
and never writes.**

### 23.1 Loading

| Aspect | Rule | Edge case |
|---|---|---|
| Location | The file `ingest.yaml` in the directory of the policy file named by `TRADING_POLICY_PATH`. No new environment variable: `INFRA_ENV_ALLOWLIST` is frozen | `ingest.yaml` absent from that directory: the run does not start (exit code 2). No built-in defaults exist |
| Environment reads | Only through `config.loader.infra_env()`. `src/data/` contains no `os.environ` access, so `lint_no_env_risk_reads` passes unchanged | An infrastructure address P2.1 needs and the allowlist lacks (Redis) is a Vault reference in the file, never a new environment variable |
| Secrets | Every credential is a `vault://` reference parsed by `config.loader.VaultRef`; `assert_not_a_literal_secret` is applied to every string leaf | A string that merely looks like a secret in a non-credential field is still rejected; the fix is to move it to Vault, not to exempt the field |
| Hash | `config.loader.content_hash()` over the parsed document with secrets as references. Written to every manifest row as `ingest_config_hash` | Two runs of one session under different hashes each record their own; manifests are never merged across hashes |
| Signature | Not signed in v0.1. `policy.yaml` is Ed25519-signed; whether this file should be is `[OQ-33]` | An unsigned file can change a tolerance without two approvals; that exposure is what `[OQ-33]` asks about |
| Validation | `IngestConfig` below, `extra="forbid"`. Any violation: the run does not start (exit code 2) | An unknown key is a violation, not a warning |
| Values read from `policy.yaml` | `schedule.{market}.ingest_utc`, the `INGEST` stage budget, `fx.source_primary`, `latency.exit.stale_bar_critical_seconds`. Read through `PolicyLoader`; never duplicated in `ingest.yaml` | A key missing for one market stops that market's run; the other market's value is never used in its place (ADR-11 requirement 7) |

How `ingest_config_hash` relates to `run_context.config_hash`, which references
`config_version`, is `[OQ-17]`.

### 23.2 Schema

```python
# src/data/config.py
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

from data.enums import IngestDataType
from domain.models import Exchange, InstrumentType
from provider.enums import ProviderId
from provider.spec import ProviderSpec


class _Cfg(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ClientConfig(_Cfg):                                   # all ASSUMPTION [A-3]
    backoff_base_seconds: Decimal = Field(gt=0, le=60)
    backoff_cap_seconds: Decimal = Field(gt=0, le=600)
    max_attempts: int = Field(ge=1, le=10)
    request_timeout_seconds: Decimal = Field(gt=0, le=120)


class ClockConfig(_Cfg):
    max_skew_seconds: Decimal = Field(gt=0, lt=3, description="ASSUMPTION [A-2]. Below P0.3's 3 s delivery budget.")
    time_servers: tuple[str, ...] = Field(min_length=1, description="Host names. No default is supplied.")
    min_servers_answering: int = Field(ge=1)
    recheck_seconds: int = Field(ge=60, le=3600)

    @model_validator(mode="after")
    def _enough_servers(self) -> "ClockConfig":
        if self.min_servers_answering > len(self.time_servers):
            raise ValueError("min_servers_answering exceeds the number of time_servers")
        return self


class RedisConfig(_Cfg):
    url_ref: str = Field(pattern=r"^vault://", description="Vault reference to the Redis URL.")
    session_ttl_seconds: int = Field(ge=1, le=604_800)      # ASSUMPTION [A-9]
    symref_ttl_seconds: int = Field(ge=1, le=86_400)        # ASSUMPTION [A-9]
    manifest_ttl_seconds: int = Field(ge=1, le=3_600)       # ASSUMPTION [A-9]
    lock_ms: int = Field(ge=100, le=60_000)


class ReconciliationConfig(_Cfg):
    volume_ratio: Decimal = Field(ge=0, le=1, description="ASSUMPTION [A-1]. A fraction, not a percent.")
    corporate_action_lookback_sessions: int = Field(ge=0, le=250)
    corporate_action_lookahead_sessions: int = Field(ge=0, le=250)


class StreamConfig(_Cfg):                                   # all ASSUMPTION [A-7]
    ping_interval_seconds: int = Field(ge=1, le=120)
    ping_timeout_seconds: int = Field(ge=1, le=120)
    reconnect_base_seconds: Decimal = Field(gt=0, le=60)
    reconnect_cap_seconds: Decimal = Field(gt=0, le=600)
    silent_window_recheck_seconds: int = Field(ge=1, le=300)


class NewsConfig(_Cfg):                                     # both ASSUMPTION [A-4]
    poll_interval_seconds: int = Field(ge=30, le=3600)
    revision_lookback_seconds: int = Field(ge=0, le=2_592_000)


class CalendarMarketConfig(_Cfg):
    settlement_cycle_sessions: int = Field(ge=0, le=5, description="Carried from SPEC-P1.1 A11. Unverified.")
    exchange_codes: dict[str, str] = Field(min_length=1, description="Vendor exchange code -> Exchange member.")


class CalendarConfig(_Cfg):
    min_forward_coverage_sessions: int = Field(ge=1, le=500)   # ASSUMPTION [A-8]
    markets: dict[str, CalendarMarketConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def _every_market_present(self) -> "CalendarConfig":
        if set(self.markets) != {"US", "IN"}:
            raise ValueError("calendar.markets must have exactly the keys US and IN; "
                             "a missing market is a startup failure, never a fallback (ADR-11 req 7)")
        for market, cfg in self.markets.items():
            for code, member in cfg.exchange_codes.items():
                if member not in Exchange.__members__ or Exchange[member].market.value != market:
                    raise ValueError(f"calendar.markets.{market}.exchange_codes[{code!r}] = {member!r} "
                                     f"is not an Exchange member of {market}")
        return self


class ReferenceMapping(_Cfg):
    """Vendor code -> our enum member, or the literal 'EXCLUDED'. Deny-by-default: a code absent
    from the table creates no instrument and is recorded (IR-12)."""
    security_type: dict[str, str]
    primary_exchange: dict[str, str]

    @model_validator(mode="after")
    def _values_are_members(self) -> "ReferenceMapping":
        for value in self.security_type.values():
            if value != "EXCLUDED" and value not in InstrumentType.__members__:
                raise ValueError(f"security_type maps to {value!r}, which is not an InstrumentType member")
        for value in self.primary_exchange.values():
            if value != "EXCLUDED" and value not in Exchange.__members__:
                raise ValueError(f"primary_exchange maps to {value!r}, which is not an Exchange member")
        return self


class MacroConfig(_Cfg):
    enabled: bool
    series_allowlist: tuple[str, ...]

    @model_validator(mode="after")
    def _allowlist_explicit(self) -> "MacroConfig":
        if self.enabled and not self.series_allowlist:
            raise ValueError("macro.enabled is true with an empty series_allowlist")
        return self


class EdgarConfig(_Cfg):
    user_agent: str = Field(min_length=10, max_length=200, description="'<Company> <admin@domain>'.")
    forms: tuple[str, ...] = Field(min_length=1)


class FundamentalsConfig(_Cfg):
    n7_metrics: tuple[str, ...] = Field(description="Metrics compared under rule N7. See [OQ-10].")


class ProviderEntry(_Cfg):
    spec: ProviderSpec
    credential_refs: dict[str, str] = Field(description="Name -> vault:// reference. Empty for SEC_EDGAR.")
    serves: tuple[IngestDataType, ...] = Field(min_length=1)
    reference_mapping: ReferenceMapping | None = None

    @model_validator(mode="after")
    def _reference_needs_mapping(self) -> "ProviderEntry":
        if IngestDataType.REFERENCE in self.serves and self.reference_mapping is None:
            raise ValueError("a provider that serves REFERENCE requires reference_mapping (IR-12)")
        for name, ref in self.credential_refs.items():
            if not ref.startswith("vault://"):
                raise ValueError(f"credential_refs[{name!r}] is not a vault:// reference")
        return self


class IngestConfig(_Cfg):
    schema_version: int = Field(ge=1, le=1)
    client: ClientConfig
    clock: ClockConfig
    redis: RedisConfig
    reconciliation: ReconciliationConfig
    stream: StreamConfig
    news: NewsConfig
    calendar: CalendarConfig
    macro: MacroConfig
    edgar: EdgarConfig
    fundamentals: FundamentalsConfig
    providers: dict[ProviderId, ProviderEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _keys_match_specs(self) -> "IngestConfig":
        for key, entry in self.providers.items():
            if entry.spec.provider_id is not key:
                raise ValueError(f"providers[{key}] carries the spec of {entry.spec.provider_id}")
        return self
```

Every numeric limit in a `ProviderSpec` entry is taken from SPEC-P0.2 §10.4 and nowhere else. A
limit SPEC-P0.2 marks unpublished is written `published: false` with no number.

---

## 24. Error paths, with fail-closed behaviour

"Absent" means: no row in the 0001 table, a failure or gap row, a manifest that is not `COMPLETE`.

| # | Condition | Detected by | Fail-closed behaviour |
|---|---|---|---|
| 1 | Provider unreachable or timing out | Client | Retries per §5; then `FAILED`, exit 1. Absent |
| 2 | Throttled beyond the retry budget | Client | `THROTTLED`; `FAILED`. Absent |
| 3 | A call would breach a published limit | Client, before sending | Not sent. Waits for the window, else `QUOTA_REFUSED_LOCAL` |
| 4 | FMP byte budget reached | IR-4 | Backfill pauses with a `PAUSED` checkpoint; no partial quarter |
| 5 | Credential expired or invalid | Pre-flight, or 401/403 | `CREDENTIAL_INVALID`; no retry; exit 2 at pre-flight, 1 mid-run |
| 6 | Response does not parse | Wire model | `SCHEMA_VIOLATION` for that response; nothing from it is stored |
| 7 | Page chain does not terminate, or body truncated | `Page.next_cursor`, content length | `INCOMPLETE_RESPONSE`; **the whole partition is discarded**, not kept in part |
| 8 | Naive or undocumented-timezone timestamp | Adapter | `UNDOCUMENTED_TIMEZONE`; record absent |
| 9 | Vendor timestamp in the future | §7.1 step 2 | `FUTURE_TIMESTAMP`; record absent |
| 10 | Value more precise than its column | §7.2 | Price, volume, FX rate: `PRECISION_EXCEEDED`; record absent. Dividend amount and split ratio: stored; exact terms in `corporate_action_terms`; the 0001 value is flagged as rounded (§8.2) |
| 11 | Symbol with no mapping | `symbol_asof` | `UNKNOWN_SYMBOL`; record absent; no instrument created |
| 12 | Symbol with two mappings, or two instruments for one FIGI | Lookup, or 0001 `EXCLUDE` | `AMBIGUOUS_SYMBOL`; record absent; never "pick the newest" |
| 13 | Unmapped security type or exchange | IR-12 | No instrument; recorded |
| 14 | Record fits no corporate-action type | IR-18 | `UNKNOWN_CORPORATE_ACTION`; the corporate-action manifest is not `COMPLETE` |
| 15 | No session row, outside calendar coverage | IR-15 | `MISSING_SESSION`; the market's run fails |
| 16 | No session row, inside coverage | IR-15 | `NO_SESSION`; exit 0; nothing fetched |
| 17 | Domain constructor raises any `DomainError`. Those reachable from the types P2.1 constructs: `BarIntegrityError`, `MissingReferenceDataError`, `CurrencyMismatchError`, `MissingSessionError`, `UnknownSymbolError`, `UnknownCorporateActionError`, `CorporateActionCalendarError`, `MoneyPrecisionError`, `FloatContaminationError`, `NaiveDatetimeError`, `MissingFxRateError` | Domain model | `DOMAIN_VALIDATION_FAILED` with the error class; record absent |
| 18 | Stored row differs from a re-fetched one | IR-19 | `DUPLICATE_CONFLICT` plus a `REVISION` row; stored row unchanged; daily run exits 1 |
| 19 | Expected daily bar absent | §11.1 | Gap `OPEN`; `INCOMPLETE`; exit 1 |
| 20 | Second source disagrees | §14 | Reconciliation rows; the primary row stays; no verdict here |
| 21 | No tick regime for a compared price | §14.2 | `MISSING_TICK_REGIME`; outcome `DISAGREE`; never 0.01 |
| 22 | Fundamentals with no EDGAR filing record | §19.3 | `NO_DISSEMINATION_EVIDENCE`; not stored |
| 23 | FX source returns no rate | `fetch_rate` → `None` | No row; `FX-001` blocks both pools. Never the previous date's rate |
| 24 | Stream disconnect | §13.2 | Gaps opened; REST reconciliation before any later bar is delivered |
| 25 | Stream connection limit (`406`) | §13.1 | This instance exits; it does not evict the holder |
| 26 | Stream delivered nothing for a window REST has | §13.4, §13.5 | Bar stored from REST; `STREAM_SILENT_LOSS` |
| 27 | Clock offset beyond the limit, or too few time servers answer | §16.2 | `CLOCK_SKEW`; exit 2; a running stream closes |
| 28 | Redis unreachable | §17 | `CACHE_UNREACHABLE`; exit 2 |
| 29 | Database unreachable or a write rejected | Driver | `DB_WRITE_FAILED` where it can be written; exit 1 or 2; the transaction's rows are absent |
| 30 | `INGEST` stage budget exceeded | Run timer | `STAGE_BUDGET_EXCEEDED`; unfinished types `FAILED`; exit 1 |
| 31 | `ingest.yaml` invalid, a literal secret in it, or `macro.enabled` with no allowlist | §23 | The run does not start; exit 2 |
| 32 | Audit write fails (once condition 9 allows any) | `write_before_act` | The `fx_rate` or `corporate_action` row is **not written** `[CONST-5]` |
| 33 | Raw news body over the bound | Wire model | `SCHEMA_VIOLATION`; not truncated; not stored |
| 34 | Macro series notes contain "Copyright" | §19.5 | Recorded; the series is not ingested |
| 35 | Session row would change after bars reference it | IR-17 | `DUPLICATE_CONFLICT`; the market's ingest stops until an operator resolves it |

---

## 25. Test plan

Specified for the code phase. Nothing here is written yet.

| # | Test | What it must show |
|---|---|---|
| T-1 | **Recorded-fixture replay, one per adapter**: Massive (aggregates, splits, dividends, tickers), Alpaca data (REST bars, stream frames, news) | Byte-for-byte recorded responses in; the exact expected rows and manifest counts out. Massive requests carry `adjusted=false`; Alpaca requests carry `adjustment=raw`, `feed=sip`, `asof` |
| T-2 | Fixture replay for FMP, SEC EDGAR, FRED | Blocked until `[OQ-23]`, `[OQ-9]`, `[OQ-24]` close and responses can be recorded |
| T-3 | Zerodha replay on **synthetic** fixtures, named `synthetic_*` and asserted to be labelled so `[DEFAULT-9]` | Blocked until `[OQ-25]` gives a documented shape to build them from. Not evidence for India activation |
| T-4 | **Gap detection across a half-day**: calendar with a `HALF_DAY` row | 42 expected 5-minute windows, not 78; one expected daily bar; a response missing the 12:55 ET window yields exactly one gap; windows after 13:00 ET yield none |
| T-5 | **Gap detection across a DST boundary**: two consecutive US sessions whose UTC opens differ by one hour | Expected windows follow each row's instants; a bar stamped at the previous session's UTC open time is not matched to the wrong window; no gap is invented |
| T-6 | India calendar: a `SPECIAL` session row | No bar expected; no gap; `counts_for_sequencing = false` leaves freshness unchanged |
| T-7 | **Two-provider disagreement**: a primary fixture and a second-source fixture differing in `close` by more than one tick for one instrument and by exactly one tick for another | First: one `DISAGREE` row with both values and the tick as tolerance. Second: no row, counted as compared. `bar_daily` holds the primary's values in both cases |
| T-8 | Revision: the same provider returns a different bar on re-fetch | `REVISION` row; `DUPLICATE_CONFLICT`; stored row unchanged; exit 1 |
| T-9 | Crash and resume: kill the backfill between two partitions and inside one | After restart with the same `job_id` the store equals an uninterrupted run's; no partition is half present |
| T-10 | Idempotency: run the same daily ingest twice | Second run stores nothing, `duplicate_count` equals the first run's `stored_count`, status `COMPLETE` |
| T-11 | Stream disconnect mid-window | The interrupted window and every window in the outage are gaps; they are filled from REST before any later bar is delivered; no bar mixes minutes from both sides |
| T-12 | Silent loss: stream fixture omits a window the REST fixture has | Bar stored from REST; `STREAM_SILENT_LOSS`; the session's `BAR_5M` manifest is not `COMPLETE` |
| T-13 | Precision: a price with seven decimals; a dividend with four decimals; a 1-for-3 reverse split | The price is neither stored nor rounded: `PRECISION_EXCEEDED`. The dividend and the split are stored: `corporate_action_terms` holds the exact amount and the exact `split_from` and `split_to`; the 0001 row holds the half-up rounded value; the matching `rounded_in_0001` flag is true |
| T-14 | No substitution, as a property test | For arbitrary sets of missing responses, every stored market value equals a value present in a fixture response for exactly that key |
| T-15 | Raw news revision | First sight is revision 1 with `first_seen_at = retrieved_at`; a changed body is revision 2; an unchanged re-poll writes nothing; no `news_item` row is written by any P2.1 path |
| T-16 | Migration 0002 against the pinned image, after 0001 | Applies with exit 0; `UPDATE` and `DELETE` are rejected on all thirteen tables; `backtest_ro` and `metrics_ro` are denied on all thirteen; a `pg_dump` of every 0001 object is identical before and after |
| T-17 | Clock, Redis, credential pre-flight failures | Exit 2; no request sent |
| T-18 | Config | A literal secret, a missing market, an empty time-server list and `macro.enabled` with no allowlist each stop the run |

Every test names the rule it covers. X1 requires every non-trivial branch to have a test in the
same drop; X2 reviews it in a separate conversation.

---

## 26. CONDITION 11 TESTABLE INVARIANTS

X5 condition 11: "Tests for the types P2.1 constructs … have landed and passed X2." **That work is
Stage 1's and is not done by this phase.** This is the list of Stage 1 behaviours P2.1 depends on.
"Undetected" means the X5 re-run of 2026-10-02 found that breaking the line passes every existing
suite (`docs/specs/reviews/X5-RERUN-2026-10-02/`).

| # | Type | Invariant P2.1 relies on | X5 state |
|---|---|---|---|
| C11-1 | `Instrument` | A `HALTED` instrument is not `is_tradeable_v1()` | Undetected — M03 |
| C11-2 | `Instrument` | `DELISTED` requires `delisted_on` | Undetected — M18 |
| C11-3 | `Instrument` | India requires `lot_size`; the exchange fixes the market; the market fixes the currency; `qty_increment > 0`; a US instrument cannot be fractional | Not mutation-tested |
| C11-4 | `SymbolMapping` | `covers()` treats `valid_to` as exclusive | Undetected — M04 |
| C11-5 | `SymbolMapping` | `valid_to` must be after `valid_from` | Not mutation-tested |
| C11-6 | `resolve_instrument` | No mapping raises `UnknownSymbolError`; two open mappings raise `AmbiguousSymbolError` | Not mutation-tested |
| C11-7 | `resolve_symbol` | Two hits raise instead of returning the first | Undetected — M17 |
| C11-8 | `ExchangeSession` | `regular_open_utc` strictly before `regular_close_utc` | Undetected — M08 |
| C11-9 | `ExchangeSession` | `settlement_date` not before `trading_date` | Undetected — M07 |
| C11-10 | `ExchangeSession` | Pre-market before open; post-market after close; the exchange belongs to the market | Not mutation-tested |
| C11-11 | `ExchangeSession` | A `HALF_DAY` row constructs and carries an earlier close; a DST pair has closes one hour apart in UTC; `utc_accounting_date` is the UTC date of the close | No test exists (X5R-E2) |
| C11-12 | `TradingCalendar` | `session()` on a missing date raises `MissingSessionError`; a duplicate session raises; a session with `counts_for_sequencing = false` is excluded from sequenced counts | Not mutation-tested |
| C11-13 | `CorporateAction` | `SPLIT`, `REVERSE_SPLIT` and `STOCK_DIVIDEND` without a ratio raise | Undetected — M09 |
| C11-14 | `CorporateAction` | `CASH_DIVIDEND` without `cash_amount` raises; `MERGER` and `ACQUISITION` without a successor raise; a non-positive ratio raises | Never constructed by a test |
| C11-15 | `parse_corporate_action_type` | An unknown code raises `UnknownCorporateActionError` | Never constructed by a test |
| C11-16 | `SuccessorLink` | `share_ratio` must be positive | Never constructed by a test |
| C11-17 | `FundamentalsSnapshot` | `disseminated_at` before `filed_at` raises | Undetected — M10 |
| C11-18 | `FundamentalsSnapshot` | `feature_timestamp()` is `disseminated_at`; a float metric is rejected | Never constructed by a test |
| C11-19 | `Trade` | `size > 0`; a UTC `as_of` is required | Never constructed by a test |
| C11-20 | `Bar` | `low ≤ open ≤ high`, `low ≤ close ≤ high`; all prices positive; one currency; `volume ≥ 0`; a zero-volume bar is valid | Not mutation-tested |
| C11-21 | `Bar` | `assert_signal_eligible()` raises on a non-final bar | Detected — M05 |
| C11-22 | `FxRate` | Rate positive; base differs from quote; quantised to 6 places | Not mutation-tested |
| C11-23 | `StalenessPolicy` | Age equal to `max_age_seconds` passes; one second more raises `StaleDataError` | Not mutation-tested |
| C11-24 | `UtcDatetime` | A naive `datetime` is rejected, not coerced | Not mutation-tested |
| C11-25 | `Price`, `Money` | Both **round** a more precise input rather than raising `[P21-16]`. P2.1 relies on this being the documented behaviour so that §7.2's pre-check is known to be necessary | Not mutation-tested |

`NewsItem` is not on this list: under O-2, P2.1 does not construct it.

---

## 27. Upstream defects, conflicts and gaps

Block A requires this list. **Nothing here is resolved or changed by this document.** No frozen
file is edited. Each item names what it needs.

| Id | Finding | Evidence | Needs |
|---|---|---|---|
| P21-1 | `news_item.body_sanitised` and `sanitiser_version` are `NOT NULL`; the sanitiser is P4.1; SPEC-P1.1 §6.5's "P1.2's ingest table" for the raw body does not exist | Migration §6.5; SPEC-P1.1 §6.5 | Addressed by O-2 for P2.1's side. The SPEC-P1.1 sentence stays wrong |
| P21-2 | The prompt asks for upsert; `bar_*` is insert-only and a non-final bar can never be finalised | Grants block; SPEC-P1.2 §3.2 | Handled by IR-19 and §12 |
| P21-3 | One row per `(instrument_id, ts)`; no place for a second source. `fundamentals_snapshot`'s unique key has no `source` | Migration §6.4, §6.5 | Handled by §14, `[DEFAULT-3]`, `[DEFAULT-5]` |
| P21-4 | The prompt's unqualified live streaming conflicts with ADR-13/14 and RULE-B1 | SPEC-P0.1; SPEC-P0.3 §15 | Handled by O-3 |
| P21-5 | No type or table for macro series, insider filings, EDGAR index snapshots; quotes not in any bought tier | Migration; SPEC-P0.2 §3.3 | Handled by O-1, O-4 |
| P21-6 | No storage for backfill state, gaps or failures; no audit event type for a provider failure | Migration; `EventType` | Storage: O-1. Event type: `[OQ-13]` |
| P21-7 | `DATA_RECEIVED` trigger wording; no P2.1 rejection event; `CORPORATE_ACTION_APPLIED` wording; `successor_link.audit_event_id NOT NULL` | `src/audit/events.py` | `[OQ-13]`, condition 9 |
| P21-8 | Domain types and tables disagree for bars, corporate actions and fundamentals; the contract test omits those three tables and checks one direction | `tests/verify_p11_p12_contract.py` | §7.4 is P2.1's mapping. The test gap is Stage 1's |
| P21-9 | `policy.yaml` has no provider registry, no per-type staleness, no Redis or clock keys | `config/policy.yaml` | Handled by O-5 |
| P21-10 | The calendar and reference-data loaders had no owner; no calendar source is named | SPEC-P1.1 §4.1; SPEC-P0.2 | Owner: O-6. Source: `[OQ-1]` |
| P21-11 | Nothing in `src/` opens a database connection; no dependency manifest | Repository | `[DEFAULT-10]` |
| P21-12 | A window-start `ts` on a daily bar would let `bars_asof` leak the close | `bars_asof` in migration §6.10 | `[DEFAULT-1]`. `bars_asof` itself is unchanged; a 5-minute-bar reader would need its own rule |
| P21-13 | `UNIQUE (instrument_id, period_end, restatement_seq)` is not limited to open knowledge rows, so a knowledge correction cannot reuse its sequence number | Migration §6.5 | **Owner / SPEC-P1.2.** Worked around by `[DEFAULT-5]`, which conflates a source correction with a restatement |
| P21-14 | India has no named source for fundamentals, corporate actions or news. FMP Premium covers "US, UK, Canada" | SPEC-P0.2 §3.4, §4.3 | `[OQ-8]`; India activation |
| P21-15 | `DataCapability` has no member for calendars, corporate actions, FX or India reference data; `ProviderId` has no member for the FX source; `INFRA_ENV_ALLOWLIST` has no Redis entry | SPEC-P0.2 §10.1; `loader.py` | Worked around (§4.1, §17). A Stage 0 / P1.3 amendment would be cleaner; not proposed here |
| P21-16 | `Price` and `Money` round a more precise input silently. SPEC-P1.1 assumption A2 says prices would "truncate silently"; they round half-up | `src/domain/models.py` `Price._coerce`, `Money._coerce_and_quantise` | Pre-check in §7.2. Condition 11 should pin the behaviour (C11-25) |
| P21-17 | `corporate_action.cash_amount` is `numeric(18,2)` and `CorporateAction.cash_amount` is `Money` (2 places). A per-share dividend with more than two decimals cannot be stored exactly in 0001 | Migration §6.3; `models.py` | **Decided by the Owner 2026-10-08 (O-10):** exact terms in the P2.1-owned `corporate_action_terms`; the 0001 row keeps its rounded value. The 0001 column is unchanged and stays inexact |
| P21-18 | `corporate_action.ratio numeric(18,6)` cannot hold a non-terminating ratio exactly; there is no column for `distribution_type`, `frequency`, `record_date`, `declaration_date`, or a bar's `vw`. SPEC-P0.2 §0.6 requires special dividends not be annualised, which needs `distribution_type` | Migration §6.3, §6.4 | Corporate-action terms: decided with P21-17 (O-10). A bar's `vw` still has no column and is not stored |
| P21-19 | "No session row" means both "closed" and "calendar not loaded"; nothing in Stage 1 separates them | SPEC-P1.1 §4.2; SPEC-P0.3 §13.1 row 5 | Handled by IR-15 |
| P21-20 | `run_context.config_hash` references `config_version`, whose `audit_event_id` is `NOT NULL`. No `run_context` row can be written before conditions 9 and 10, though STAGE-1-FREEZE §9.2 gates only "code that writes an audit event" | Migration §6.9 | `[DEFAULT-15]`; stated to the Owner because it widens the practical reach of condition 9 |
| P21-21 | `Exchange` has four members. A US instrument listed elsewhere cannot be represented, including exchange-traded funds `models.py` marks as read-only regime inputs | `models.py` `Exchange`, `READ_ONLY_INSTRUMENT_TYPES_V1` | `[OQ-22]` first (what values the vendor sends); then P2.6's need |
| P21-22 | SPEC-P0.3 §13.1 row 2 aborts ingest on any shortfall against the universe; the P2.2 prompt defines a minimum coverage fraction | SPEC-P0.3; `PROMPT-PACK.md` P2.2 | P2.2. This phase follows the frozen row |
| P21-23 | `stage_latency_observation.strategy_version` is `NOT NULL`; an ingest run has no strategy | Migration §6.9 | `[OQ-20]`. P2.1 does not write this table in v0.1 |
| P21-24 | Verified source fields exist for four of eleven `CorporateActionType` members | SPEC-P0.2 §3.3 | `[OQ-29]` |
| **P21-25** | **SPEC-P0.2 records no response fields for FMP, SEC EDGAR, FRED, Zerodha historical candles or the Zerodha instruments dump beyond `tick_size` and `lot_size`, nor for Massive trades, ticker types, ticker events or `primary_exchange` values.** Six of eight adapters therefore have no field mapping | SPEC-P0.2 §3.3–3.9 | **Blocks freeze of those adapters.** `[OQ-9]`, `[OQ-22]`–`[OQ-25]` |
| P21-26 | No precedence is defined between a symbol-specific `tick_size_regime` row and a `*` row. The 0001 `EXCLUDE` constraint covers `(market, symbol)`, so both can cover one date | Migration §6.2; SPEC-P0.2 §10.3 | P3.2 and rule N10 most of all. P2.1 treats the overlap as fail-closed for its own tolerance (§14.2) and decides nothing else |
| P21-27 | The India `tick_size` in the Zerodha instruments dump was read and mapped to no table, so India's reference source for tick size never reached `tick_size_regime` | SPEC-P0.2 §0.6; this spec's v0.2 §7.4 | **Decided by the Owner 2026-10-09 (O-11):** rule IR-21, `[DEFAULT-17]` |
| P21-28 | A `tick_size_regime` row cannot be superseded by the application: `app_rw` has no `UPDATE` on the table, and the `EXCLUDE` constraint rejects a new row that overlaps an open-ended one. A changed tick cannot be recorded by closing the old row | Migration §6.2, §6.10 grants | Worked around by IR-21's one-day rows. The US changeover of November 2027 (SPEC-P0.2 F-10) meets the same limit and will need `trading_owner` or a SPEC-P1.2 amendment |

---

## 28. Field specifications

Block B: every field carries its name, type, unit, timezone, nullability, valid range and what a
violation means. The models and DDL above are the definitions; these tables complete them and add
no constraint that is not already in the code block or the `CHECK` it describes.

**Reading the tables.** *Unit; tz*: the unit, then the timezone. `UTC` = a tz-aware UTC instant;
`local` = an exchange-local calendar date with no clock; `—` = not applicable. *Null*: whether
`None` / `NULL` is permitted. *Violation* is one of:

| Code | Applies to | Meaning |
|---|---|---|
| **W** | Wire records, `Page`, `StreamGapNotice` | The model raises. The record becomes an `ingest_failure` row of kind `SCHEMA_VIOLATION` (or the more specific kind named in the row) and is not stored |
| **C** | `IngestConfig` and its parts | Configuration is rejected. The run does not start; exit code 2 (§24 row 31) |
| **R** | Request and result models | The caller's request is rejected before any provider call; nothing is fetched and nothing is written |
| **D** | 0002 columns | The database rejects the insert. The writer records `DB_WRITE_FAILED`; the run's status is `FAILED` (§22) |

### 28.1 Wire records, `Page`, `StreamGapNotice`

Every wire record also has the three `_Wire` fields.

| Model.field | Type | Unit; tz | Null | Valid range | Violation |
|---|---|---|---|---|---|
| `_Wire.provider_id` | `ProviderId` | —; — | no | An enum member | W |
| `_Wire.retrieved_at` | `datetime` | instant; UTC | no | tz-aware; not after the process clock | W; naive → `UNDOCUMENTED_TIMEZONE` |
| `_Wire.response_sha256` | `str` | lowercase hex; — | no | Exactly 64 hex characters | W |
| `WireBar.provider_symbol` | `str` | —; — | no | 1–32 characters | W |
| `WireBar.window_start` | `datetime` | instant; UTC | no | tz-aware; ≤ `retrieved_at` + skew limit | W; later → `FUTURE_TIMESTAMP` |
| `WireBar.window_seconds` | `int` | seconds; — | no | 60, 300 or 86400 | W |
| `WireBar.open`, `high`, `low`, `close` | `Decimal` | listing currency per share, unadjusted; — | no | > 0; scale ≤ 6 (§7.2) | W; excess scale → `PRECISION_EXCEEDED` |
| `WireBar.volume` | `Decimal` | shares; — | no | ≥ 0; scale 0 (§7.2) | W; non-integer → `PRECISION_EXCEEDED` |
| `WireBar.trade_count` | `int` | trades; — | yes | ≥ 0 | W |
| `WireSplit.provider_symbol` | `str` | —; — | no | 1–32 characters | W |
| `WireSplit.execution_date` | `date` | date; local | no | Any date | W |
| `WireSplit.split_from` | `Decimal` | old shares; — | no | > 0 | W |
| `WireSplit.split_to` | `Decimal` | new shares; — | no | > 0; `split_to ≠ split_from` (§2) | W; equal → `DOMAIN_VALIDATION_FAILED` |
| `WireDividend.provider_symbol` | `str` | —; — | no | 1–32 characters | W |
| `WireDividend.ex_dividend_date` | `date` | date; local | no | Any date | W |
| `WireDividend.pay_date` | `date` | date; local | yes at the wire | Any date | `None` → `DOMAIN_VALIDATION_FAILED` in the normaliser (§2) |
| `WireDividend.record_date`, `declaration_date` | `date` | date; local | yes | Any date | W |
| `WireDividend.cash_amount` | `Decimal` | listing currency per share; — | no | > 0; any scale. Stored exactly in `corporate_action_terms` (§8.2) | W |
| `WireDividend.distribution_type` | `str` | —; — | yes | ≤ 32 characters | W |
| `WireDividend.frequency` | `int` | payouts per year; — | yes | 0–365 | W |
| `WireInstrument.provider_symbol` | `str` | —; — | no | 1–32 characters | W |
| `WireInstrument.primary_exchange` | `str` | vendor code; — | no | 1–32 characters; must be in the mapping table (IR-12) | W; unmapped → `UNKNOWN_INSTRUMENT_TYPE` |
| `WireInstrument.security_type` | `str` | vendor code; — | no | 1–32 characters; must be in the mapping table (IR-12) | W; unmapped → `UNKNOWN_INSTRUMENT_TYPE` |
| `WireInstrument.active` | `bool` | —; — | no | `true`, `false` | W |
| `WireInstrument.currency_name` | `str` | vendor code; — | no | 1–16 characters; must map to the market's currency | W; mismatch → `DOMAIN_VALIDATION_FAILED` |
| `WireInstrument.cik` | `str` | —; — | yes | ≤ 16 characters | W |
| `WireInstrument.composite_figi`, `share_class_figi` | `str` | —; — | yes | Exactly 12 characters | W |
| `WireInstrument.delisted_utc` | `datetime` | instant; UTC | yes | tz-aware | W |
| `WireInstrument.as_of_date` | `date` | date; local | no | The date the reference query was made for | W |
| `WireInstrument.lot_size`, `tick_size` | `Decimal` | shares; price units; — | yes (required for India by the domain) | > 0. India `tick_size` is stored in `tick_size_regime` by rule IR-21 | W; India without `lot_size` → `DOMAIN_VALIDATION_FAILED` |
| `WireSession.exchange_code` | `str` | vendor code; — | no | 1–16 characters; must be in `calendar.markets.*.exchange_codes` | W |
| `WireSession.trading_date` | `date` | date; local | no | Any date | W |
| `WireSession.regular_open_utc`, `regular_close_utc` | `datetime` | instant; UTC | no | open < close; close − open a multiple of 300 s (§2) | W; `MISSING_SESSION` |
| `WireSession.pre_market_open_utc` | `datetime` | instant; UTC | yes | < `regular_open_utc` | W |
| `WireSession.post_market_close_utc` | `datetime` | instant; UTC | yes | > `regular_close_utc` | W |
| `WireSession.is_half_day`, `is_special` | `bool` | —; — | no | Not both `true` | W |
| `WireNews.vendor_id` | `str` | —; — | no | 1–128 characters | W |
| `WireNews.headline` | `str` | characters; — | no | ≤ 4,000. UNTRUSTED | W |
| `WireNews.author` | `str` | characters; — | yes | ≤ 400. UNTRUSTED | W |
| `WireNews.created_at` | `datetime` | instant; UTC | no | tz-aware | W |
| `WireNews.updated_at` | `datetime` | instant; UTC | yes | tz-aware | W |
| `WireNews.summary` | `str` | characters; — | yes | ≤ 20,000. UNTRUSTED | W |
| `WireNews.content` | `str` | characters; — | yes | ≤ 1,000,000, `ASSUMPTION [A-5]`. UNTRUSTED | W; not truncated |
| `WireNews.symbols` | `tuple[str, ...]` | vendor tickers; — | no (may be empty) | ≤ 200 items | W |
| `WireNews.source` | `str` | characters; — | yes | ≤ 200. UNTRUSTED | W |
| `WireNews.url` | `str` | characters; — | yes | ≤ 2,000. UNTRUSTED; never fetched | W |
| `WireFundamentals.provider_symbol` | `str` | —; — | no | 1–32 characters | W |
| `WireFundamentals.cik` | `str` | —; — | yes | ≤ 16 characters | W |
| `WireFundamentals.period_end` | `date` | date; issuer's fiscal calendar | no | Any date | W |
| `WireFundamentals.fiscal_period` | `str` | —; — | no | 1–16 characters | W |
| `WireFundamentals.metrics` | `dict[str, Decimal]` | per metric, as the vendor reports it; — | no | ≥ 1 entry; finite values | W |
| `WireFiling.filing_key` | `str` | —; — | no | 1–64 characters `[OQ-9]` | W |
| `WireFiling.cik` | `str` | —; — | no | 1–16 characters | W |
| `WireFiling.form_type` | `str` | —; — | no | 1–16 characters | W |
| `WireFiling.accepted_at` | `datetime` | instant; UTC | no | tz-aware; ≤ `retrieved_at` + skew limit | W; later → `FUTURE_TIMESTAMP` |
| `WireFiling.period_end` | `date` | date; issuer's fiscal calendar | yes | Any date | W |
| `WireFiling.document_ref` | `str` | path on the SEC host; — | no | 1–400 characters | W |
| `WireMacroObservation.series_id` | `str` | —; — | no | 1–64 characters; in `macro.series_allowlist` | W |
| `WireMacroObservation.observation_date` | `date` | date; the series' own calendar | no | Any date | W |
| `WireMacroObservation.vintage_date` | `date` | date; the publisher's calendar | no | ≥ `observation_date` | W |
| `WireMacroObservation.value` | `Decimal` | the series' own unit; — | no | Finite | W; a non-numeric vendor value is skipped (§19.5) |
| `WireFxRate.as_of_date` | `date` | date; UTC accounting date | no | Any date | W |
| `WireFxRate.base`, `quote` | `str` | ISO currency code; — | no | Exactly 3 characters; `USD` or `INR`; different from each other | W |
| `WireFxRate.rate` | `Decimal` | quote per unit of base; — | no | > 0; scale ≤ 6 (§7.2) | W; excess scale → `PRECISION_EXCEEDED` |
| `Page.items` | `tuple[T, ...]` | records; — | no (may be empty) | Any length | W |
| `Page.next_cursor` | `str` | opaque vendor token; — | yes | ≤ 2,000 characters. `None` = the provider said there is no more | W; a chain that never reaches `None` → `INCOMPLETE_RESPONSE` |
| `Page.response_bytes` | `int` | bytes; — | no | ≥ 0 | W |
| `Page.response_sha256` | `str` | lowercase hex; — | no | Exactly 64 hex characters | W |
| `StreamGapNotice.instrument_id` | `UUID` | —; — | no | A subscribed instrument | W |
| `StreamGapNotice.window_start` | `datetime` | instant; UTC | no | An expected window start (§11.2) | W |
| `StreamGapNotice.gap_id` | `UUID` | —; — | no | An existing `ingest_gap.gap_id` | W |
| `StreamGapNotice.reconciled` | `bool` | —; — | no | `false` = the instrument has an `OPEN` gap | W |

### 28.2 Configuration (`IngestConfig`)

| Model.field | Type | Unit; tz | Null | Valid range | Violation |
|---|---|---|---|---|---|
| `ClientConfig.backoff_base_seconds` | `Decimal` | seconds; — | no | (0, 60] | C |
| `ClientConfig.backoff_cap_seconds` | `Decimal` | seconds; — | no | (0, 600] | C |
| `ClientConfig.max_attempts` | `int` | attempts, first included; — | no | 1–10 | C |
| `ClientConfig.request_timeout_seconds` | `Decimal` | seconds, connect plus read; — | no | (0, 120] | C |
| `ClockConfig.max_skew_seconds` | `Decimal` | seconds; — | no | (0, 3) | C |
| `ClockConfig.time_servers` | `tuple[str, ...]` | host names; — | no | ≥ 1 entry | C |
| `ClockConfig.min_servers_answering` | `int` | servers; — | no | 1 to `len(time_servers)` | C |
| `ClockConfig.recheck_seconds` | `int` | seconds; — | no | 60–3,600 | C |
| `RedisConfig.url_ref` | `str` | Vault reference; — | no | Starts `vault://`; never a literal URL | C |
| `RedisConfig.session_ttl_seconds` | `int` | seconds; — | no | 1–604,800 | C |
| `RedisConfig.symref_ttl_seconds` | `int` | seconds; — | no | 1–86,400 | C |
| `RedisConfig.manifest_ttl_seconds` | `int` | seconds; — | no | 1–3,600 | C |
| `RedisConfig.lock_ms` | `int` | milliseconds; — | no | 100–60,000 | C |
| `ReconciliationConfig.volume_ratio` | `Decimal` | fraction, not percent; — | no | [0, 1] | C |
| `ReconciliationConfig.corporate_action_lookback_sessions` | `int` | sequenced sessions; — | no | 0–250 | C |
| `ReconciliationConfig.corporate_action_lookahead_sessions` | `int` | sequenced sessions; — | no | 0–250 | C |
| `StreamConfig.ping_interval_seconds` | `int` | seconds; — | no | 1–120 | C |
| `StreamConfig.ping_timeout_seconds` | `int` | seconds; — | no | 1–120 | C |
| `StreamConfig.reconnect_base_seconds` | `Decimal` | seconds; — | no | (0, 60] | C |
| `StreamConfig.reconnect_cap_seconds` | `Decimal` | seconds; — | no | (0, 600] | C |
| `StreamConfig.silent_window_recheck_seconds` | `int` | seconds; — | no | 1–300 | C |
| `NewsConfig.poll_interval_seconds` | `int` | seconds; — | no | 30–3,600 | C |
| `NewsConfig.revision_lookback_seconds` | `int` | seconds; — | no | 0–2,592,000 | C |
| `CalendarMarketConfig.settlement_cycle_sessions` | `int` | sequenced sessions after the trade date; — | no | 0–5 | C |
| `CalendarMarketConfig.exchange_codes` | `dict[str, str]` | vendor code → `Exchange` member; — | no | ≥ 1 entry; every value an `Exchange` member of that market | C |
| `CalendarConfig.min_forward_coverage_sessions` | `int` | sequenced sessions; — | no | 1–500 | C |
| `CalendarConfig.markets` | `dict[str, CalendarMarketConfig]` | —; — | no | Exactly the keys `US` and `IN` | C |
| `ReferenceMapping.security_type` | `dict[str, str]` | vendor code → `InstrumentType` member or `EXCLUDED`; — | no | Every value a member or the literal `EXCLUDED` | C |
| `ReferenceMapping.primary_exchange` | `dict[str, str]` | vendor code → `Exchange` member or `EXCLUDED`; — | no | Every value a member or the literal `EXCLUDED` | C |
| `MacroConfig.enabled` | `bool` | —; — | no | `true`, `false` | C |
| `MacroConfig.series_allowlist` | `tuple[str, ...]` | series ids; — | no | Non-empty when `enabled` | C |
| `EdgarConfig.user_agent` | `str` | characters; — | no | 10–200 | C |
| `EdgarConfig.forms` | `tuple[str, ...]` | form types; — | no | ≥ 1 entry | C |
| `FundamentalsConfig.n7_metrics` | `tuple[str, ...]` | metric names; — | no | May be empty until `[OQ-10]` closes; empty = no N7 comparison is run | C |
| `ProviderEntry.spec` | `ProviderSpec` | —; — | no | Valid under SPEC-P0.2 §10.2 | C |
| `ProviderEntry.credential_refs` | `dict[str, str]` | name → Vault reference; — | no (may be empty) | Every value starts `vault://` | C |
| `ProviderEntry.serves` | `tuple[IngestDataType, ...]` | —; — | no | ≥ 1 member | C |
| `ProviderEntry.reference_mapping` | `ReferenceMapping` | —; — | yes | Required when `serves` contains `REFERENCE` | C |
| `IngestConfig.schema_version` | `int` | —; — | no | 1 | C |
| `IngestConfig.client`, `clock`, `redis`, `reconciliation`, `stream`, `news`, `calendar`, `macro`, `edgar`, `fundamentals` | the model of the same name | —; — | no | Valid under its own rows | C |
| `IngestConfig.providers` | `dict[ProviderId, ProviderEntry]` | —; — | no | ≥ 1 entry; each key equals its entry's `spec.provider_id` | C |

### 28.3 Request and result models

| Model.field | Type | Unit; tz | Null | Valid range | Violation |
|---|---|---|---|---|---|
| `IngestSet.market` | `Market` | —; — | no | `US`, `IN` | R |
| `IngestSet.trading_date` | `date` | date; local | no | The session the set is for | R |
| `IngestSet.instrument_ids` | `frozenset[UUID]` | —; — | no | ≥ 1 member; every member an existing `instrument_id` of that market | R; an unknown id → `UNKNOWN_SYMBOL` for that id |
| `IngestSet.universe_version` | `UUID` | —; — | yes | An existing `universe_version`. `None` = no universe exists yet; the caller chose the set | R |
| `IngestSet.includes_held` | `bool` | —; — | no | `true` when the caller has already added the held names | R |
| `BackfillJobRequest.job_id` | `UUID` | —; — | no | Any UUID; reusing one resumes that job | R |
| `BackfillJobRequest.data_type` | `IngestDataType` | —; — | no | A member of `BACKFILLABLE` | R |
| `BackfillJobRequest.provider_id` | `ProviderId` | —; — | no | A provider whose `serves` contains `data_type` | R |
| `BackfillJobRequest.market` | `Market` | —; — | no | `US`, `IN` | R |
| `BackfillJobRequest.instrument_ids` | `frozenset[UUID]` | —; — | no (may be empty) | Empty = every instrument the data type applies to | R |
| `BackfillJobRequest.series_ids` | `tuple[str, ...]` | series ids; — | no | Non-empty for `MACRO`, empty otherwise | R |
| `BackfillJobRequest.date_from`, `date_to` | `date` | date; local | no | `date_from ≤ date_to`; both inclusive | R |
| `BackfillJobRequest.code_version` | `str` | git commit id; — | no | 7–40 characters | R |
| `DailyRunRequest.run_id` | `UUID` | —; — | no | Any UUID; one per invocation | R |
| `DailyRunRequest.market` | `Market` | —; — | no | `US`, `IN` | R |
| `DailyRunRequest.trading_date` | `date` | date; local | no | The session the run is for | R |
| `DailyRunRequest.ingest_set` | `IngestSet` | —; — | no | Same `market` and `trading_date` as the request | R |
| `DailyRunRequest.code_version` | `str` | git commit id; — | no | 7–40 characters | R |
| `DailyRunResult.run_id`, `market`, `trading_date` | as the request | as the request | no | Equal to the request's | R |
| `DailyRunResult.exit_code` | `int` | —; — | no | 0, 1 or 2, agreeing with `statuses` (§12.2) | R |
| `DailyRunResult.statuses` | `dict[IngestDataType, ManifestStatus]` | —; — | no (empty when pre-flight failed) | The worst status per data type attempted | R |
| `DailyRunResult.manifest_ids` | `tuple[UUID, ...]` | —; — | no (may be empty) | The `ingest_manifest` rows this run wrote | R |
| `DailyRunResult.started_at`, `finished_at` | `datetime` | instant; UTC | no | `started_at ≤ finished_at` | R |

### 28.4 Migration 0002 columns

Columns that mean the same thing in every table they appear in:

| Column | Type | Unit; tz | Null | Valid range | Violation |
|---|---|---|---|---|---|
| `run_id` | `uuid` | —; — | no | The id of the ingest invocation that wrote the row. No foreign key `[DEFAULT-15]` | D |
| `market` | `text` | —; — | no | `US`, `IN` | D |
| `provider_id` | `text` | —; — | no | 1–32 characters; a registry provider, checked in the application | D |
| `data_type` | `text` | —; — | no | An `IngestDataType` value; enumerated in the `CHECK` on `ingest_manifest` and `ingest_gap`, 1–32 characters elsewhere and checked in the application | D |
| `response_sha256`, `content_sha256`, `document_sha256`, `index_sha256`, `notes_sha256`, `input_hash`, `ingest_config_hash` | `text` | lowercase hex; — | no, except `ingest_failure.response_sha256` | Exactly 64 hex characters | D |
| `retrieved_at`, `recorded_at` | `timestamptz` | instant; UTC | no | The process clock when the response arrived, or when the row was written | D |

Per table, the remaining columns:

| Table.column | Type | Unit; tz | Null | Valid range | Violation |
|---|---|---|---|---|---|
| `ingest_manifest.manifest_id` | `uuid` | —; — | no | Generated | D |
| `ingest_manifest.trading_date` | `date` | date; local | no | The session the run is for | D |
| `ingest_manifest.status` | `text` | —; — | no | A `ManifestStatus` value | D |
| `ingest_manifest.expected_count`, `received_count`, `stored_count`, `duplicate_count`, `skipped_count`, `failed_count`, `present_count` | `integer` | records; — | no | ≥ 0; `COMPLETE` requires `present_count = expected_count` and `failed_count = 0`; `NO_SESSION` requires expected, received and stored all 0 | D |
| `ingest_manifest.compared_count`, `disagreed_count` | `integer` | fields compared; — | no | ≥ 0; `disagreed_count ≤ compared_count` | D |
| `ingest_manifest.coverage_from`, `coverage_to` | `date` | date; local, both inclusive | yes | Both or neither; `coverage_to ≥ coverage_from`; only when `data_type = CALENDAR` | D |
| `ingest_manifest.code_version` | `text` | git commit id; — | no | 7–40 characters | D |
| `ingest_manifest.detail` | `text` | characters; — | yes | ≤ 4,000. Our text, never vendor text | D |
| `ingest_manifest.started_at`, `finished_at` | `timestamptz` | instant; UTC | no | `finished_at ≥ started_at` | D |
| `ingest_checkpoint.checkpoint_id` | `uuid` | —; — | no | Generated | D |
| `ingest_checkpoint.job_id` | `uuid` | —; — | no | `BackfillJobRequest.job_id` | D |
| `ingest_checkpoint.partition_key` | `text` | —; — | no | 1–400 characters; deterministic from the job's parameters (§10.2) | D |
| `ingest_checkpoint.state` | `text` | —; — | no | `STARTED`, `COMMITTED`, `FAILED`, `PAUSED` | D |
| `ingest_checkpoint.range_from`, `range_to` | `date` | date; local, both inclusive | yes | `range_to ≥ range_from` when both are set | D |
| `ingest_checkpoint.rows_stored` | `integer` | rows; — | no | ≥ 0 | D |
| `ingest_checkpoint.cursor` | `text` | opaque vendor token; — | yes | ≤ 2,000 characters. Diagnosis only; never used to resume | D |
| `ingest_failure.failure_id` | `uuid` | —; — | no | Generated | D |
| `ingest_failure.occurred_at` | `timestamptz` | instant; UTC | no | The process clock at detection | D |
| `ingest_failure.failure_kind` | `text` | —; — | no | A `FailureKind` value | D |
| `ingest_failure.instrument_id` | `uuid` | —; — | yes | Set when the failure concerns one resolved instrument | D |
| `ingest_failure.provider_symbol` | `text` | vendor ticker; — | yes | ≤ 32 characters | D |
| `ingest_failure.trading_date` | `date` | date; local | yes | Set when the failure concerns one session | D |
| `ingest_failure.window_start` | `timestamptz` | instant; UTC | yes | Set when the failure concerns one bar | D |
| `ingest_failure.http_status` | `integer` | HTTP status code; — | yes | 100–599 | D |
| `ingest_failure.detail` | `text` | characters; — | no | 1–2,000. Our text, never vendor text | D |
| `ingest_gap.gap_id` | `uuid` | —; — | no | Generated | D |
| `ingest_gap.resolves_gap_id` | `uuid` | —; — | yes | `NULL` exactly when `state = OPEN`; otherwise the `gap_id` of the row that opened the gap; never its own id | D |
| `ingest_gap.instrument_id` | `uuid` | —; — | no | The instrument the absent bar belongs to | D |
| `ingest_gap.trading_date` | `date` | date; local | no | The session of the absent bar | D |
| `ingest_gap.window_start` | `timestamptz` | instant; UTC | no | The `ts` the absent bar would carry | D |
| `ingest_gap.window_end` | `timestamptz` | instant; UTC, exclusive | no | ≥ `window_start` | D |
| `ingest_gap.gap_kind` | `text` | —; — | no | A `GapKind` value | D |
| `ingest_gap.state` | `text` | —; — | no | A `GapState` value | D |
| `ingest_gap.detail` | `text` | characters; — | yes | ≤ 2,000. Our text | D |
| `ingest_reconciliation.recon_id` | `uuid` | —; — | no | Generated | D |
| `ingest_reconciliation.compared_at` | `timestamptz` | instant; UTC | no | The process clock at comparison | D |
| `ingest_reconciliation.recon_kind` | `text` | —; — | no | A `ReconKind` value | D |
| `ingest_reconciliation.instrument_id` | `uuid` | —; — | no | The instrument compared | D |
| `ingest_reconciliation.key_ts` | `timestamptz` | instant; UTC | yes | The bar's `ts`. Exactly one of `key_ts` and `period_end` is set | D |
| `ingest_reconciliation.period_end` | `date` | date; issuer's fiscal calendar | yes | The fiscal period end. Exactly one of `key_ts` and `period_end` is set | D |
| `ingest_reconciliation.field` | `text` | —; — | no | 1–120 characters: `open`, `high`, `low`, `close`, `volume`, `trade_count`, or a metric name | D |
| `ingest_reconciliation.primary_provider`, `other_provider`, `authority_provider` | `text` | —; — | no | 1–32 characters; registry providers | D |
| `ingest_reconciliation.primary_value`, `other_value` | `numeric(28,6)` | the unit of `field`; — | yes | `NULL` exactly when `outcome` is `PRIMARY_MISSING` / `OTHER_MISSING` respectively | D |
| `ingest_reconciliation.tolerance_kind` | `text` | —; — | no | `EXACT`, `TICK`, `RATIO`, `UNDEFINED` | D |
| `ingest_reconciliation.tolerance_value` | `numeric(28,6)` | price units for `TICK`, a fraction for `RATIO`; — | yes | `NULL` for `EXACT` and `UNDEFINED` | D |
| `ingest_reconciliation.outcome` | `text` | —; — | no | `DISAGREE`, `PRIMARY_MISSING`, `OTHER_MISSING` | D |
| `provider_instrument_ref.instrument_id` | `uuid` | —; — | no | An existing `instrument_id` | D |
| `provider_instrument_ref.key_kind` | `text` | —; — | no | `TICKER`, `CIK`, `COMPOSITE_FIGI`, `SHARE_CLASS_FIGI`, `INSTRUMENT_TOKEN` | D |
| `provider_instrument_ref.effective_from` | `date` | date; local, inclusive | no | Any date | D |
| `provider_instrument_ref.provider_symbol` | `text` | the provider's identifier; — | yes | 1–64 characters. `NULL` = from `effective_from` the instrument has no such identifier | D |
| `raw_news_snapshot.vendor_id` | `text` | —; — | no | 1–128 characters | D |
| `raw_news_snapshot.revision_seq` | `integer` | —; — | no | ≥ 1; 1 is the first receipt | D |
| `raw_news_snapshot.first_seen_at` | `timestamptz` | instant; UTC | no | `retrieved_at` of this revision; non-decreasing in `revision_seq` | D |
| `raw_news_snapshot.vendor_created_at` | `timestamptz` | instant; UTC | no | The vendor's `created_at` | D |
| `raw_news_snapshot.vendor_updated_at` | `timestamptz` | instant; UTC | yes | The vendor's `updated_at` | D |
| `raw_news_snapshot.headline_raw` | `text` | characters; — | no | ≤ 4,000. UNTRUSTED | D |
| `raw_news_snapshot.summary_raw` | `text` | characters; — | yes | ≤ 20,000. UNTRUSTED | D |
| `raw_news_snapshot.body_raw` | `text` | characters; — | yes | ≤ 1,000,000. UNTRUSTED | D |
| `raw_news_snapshot.author_raw`, `source_raw`, `url_raw` | `text` | characters; — | yes | ≤ 400, ≤ 200, ≤ 2,000. UNTRUSTED | D |
| `raw_news_snapshot.symbols_raw` | `text[]` | vendor tickers; — | no (may be empty) | As received; not resolved to instruments | D |
| `macro_series.series_id` | `text` | —; — | no | 1–64 characters | D |
| `macro_series.third_party_copyright` | `boolean` | —; — | no | `true` = the notes contain "Copyright"; the series is not ingested | D |
| `macro_observation.series_id` | `text` | —; — | no | 1–64 characters | D |
| `macro_observation.observation_date` | `date` | date; the series' own calendar | no | The period the value describes | D |
| `macro_observation.vintage_date` | `date` | date; the publisher's calendar | no | ≥ `observation_date` | D |
| `macro_observation.value` | `numeric(28,6)` | the series' own unit; — | no | Any finite value | D |
| `edgar_index_snapshot.index_kind` | `text` | —; — | no | `DAILY`, `QUARTERLY`, `FULL`, `SUBMISSIONS`, `COMPANY_TICKERS` | D |
| `edgar_index_snapshot.index_ref` | `text` | path on the SEC host; — | no | 1–400 characters | D |
| `edgar_index_snapshot.content` | `bytea` | bytes, as received; — | no | Non-empty | D |
| `edgar_index_snapshot.content_bytes` | `bigint` | bytes; — | no | > 0; the length of `content` | D |
| `edgar_filing.filing_key` | `text` | —; — | no | 1–64 characters `[OQ-9]` | D |
| `edgar_filing.observed_at` | `timestamptz` | instant; UTC | no | The process clock at this observation | D |
| `edgar_filing.observed_state` | `text` | —; — | no | `PRESENT`, `ABSENT_AFTER_REBUILD` | D |
| `edgar_filing.cik` | `text` | —; — | no | 1–16 characters | D |
| `edgar_filing.instrument_id` | `uuid` | —; — | yes | `NULL` = the CIK maps to none of our instruments | D |
| `edgar_filing.form_type` | `text` | —; — | no | 1–16 characters | D |
| `edgar_filing.accepted_at` | `timestamptz` | instant; UTC | no | The acceptance instant | D |
| `edgar_filing.disseminated_at` | `timestamptz` | instant; UTC | no | ≥ `accepted_at`; computed by §19.2 | D |
| `edgar_filing.period_end` | `date` | date; issuer's fiscal calendar | yes | Any date | D |
| `edgar_filing.document_ref` | `text` | path on the SEC host; — | no | 1–400 characters | D |
| `insider_filing_raw.filing_key` | `text` | —; — | no | 1–64 characters | D |
| `insider_filing_raw.form_type` | `text` | —; — | no | 1–16 characters | D |
| `insider_filing_raw.document` | `bytea` | bytes, as retrieved; — | no | Non-empty. UNTRUSTED | D |
| `insider_filing_raw.document_bytes` | `bigint` | bytes; — | no | > 0; the length of `document` | D |
| `corporate_action_terms.action_id` | `uuid` | —; — | no | The `action_id` of the `corporate_action` row described | D |
| `corporate_action_terms.knowledge_from` | `timestamptz` | instant; UTC | no | The `knowledge_from` of that same row | D |
| `corporate_action_terms.action_type` | `text` | —; — | no | `SPLIT`, `REVERSE_SPLIT`, `CASH_DIVIDEND` | D |
| `corporate_action_terms.cash_amount_exact` | `numeric` | listing currency per share, vendor precision; — | yes | > 0 and finite; set exactly when `action_type = CASH_DIVIDEND` | D |
| `corporate_action_terms.cash_currency` | `text` | ISO currency code; — | yes | `USD`, `INR`; set exactly when `cash_amount_exact` is set | D |
| `corporate_action_terms.split_from` | `numeric` | old shares; — | yes | > 0 and finite; set exactly for `SPLIT` and `REVERSE_SPLIT`; ≠ `split_to` | D |
| `corporate_action_terms.split_to` | `numeric` | new shares; — | yes | > 0 and finite; set exactly for `SPLIT` and `REVERSE_SPLIT`; ≠ `split_from` | D |
| `corporate_action_terms.distribution_type` | `text` | vendor code; — | yes | ≤ 32 characters; dividends only | D |
| `corporate_action_terms.frequency` | `integer` | payouts per year; — | yes | 0–365; dividends only | D |
| `corporate_action_terms.record_date`, `declaration_date` | `date` | date; local | yes | Any date; dividends only | D |
| `corporate_action_terms.cash_rounded_in_0001` | `boolean` | —; — | no | `true` only for a dividend whose 0001 `cash_amount` differs from `cash_amount_exact` | D |
| `corporate_action_terms.ratio_rounded_in_0001` | `boolean` | —; — | no | `true` only for a split whose 0001 `ratio` differs from `split_to / split_from` | D |

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Daily bar `ts` is the session's `regular_close_utc` `[DEFAULT-1]` | `bars_asof` filters on `ts ≤ cutoff`; a bar must not be visible before it existed | No, once bars are stored: `ts` is in the primary key | **High** — look-ahead in every backtest, or a re-key of the bar table |
| 2 | Insert-only writes; a differing duplicate is recorded, never applied (IR-19) | The grants and SPEC-P1.2 §3.2 permit nothing else | No — it is the storage contract | **High** if a vendor revises often: the store keeps first values. §21 measures it |
| 3 | A daily bar is written at the scheduled ingest and checked against a re-fetch one session later `[DEFAULT-2]` | SPEC-P0.3 §13.1 row 3 already prescribes this; Q-7 is unanswered | Yes | Medium — a revision is caught a session late, after one decision may have used it |
| 4 | Only the primary provider writes a 0001 market-data table; other sources are evidence (IR-20) | One row per key exists; rule N7 forbids a silent tiebreak | Yes | Medium |
| 5 | Price tolerance is the tick in force; volume tolerance is a configured ratio `[DEFAULT-4]` | The tick is the smallest meaningful price difference and is already date-versioned | Yes | Low — evidence only; P2.2 rules |
| 6 | Rule N7 is stored as reconciliation rows plus an EDGAR row at the next `restatement_seq` `[DEFAULT-5]` | The unique key leaves no other insert | Yes | Medium — `[P21-13]` |
| 7 | Absence is no row plus manifest, failure and gap records; no sentinel `[DEFAULT-7]` | `[CONST-6]`; the bar tables cannot hold a sentinel | No | **High** if a consumer skips the manifest — which is why §15.3 is an exported contract |
| 8 | Batch freshness is "the last completed sequenced session is `COMPLETE`", not seconds `[DEFAULT-8]` | A daily bar is hours old by design at the next order window | Yes | Medium |
| 9 | The stream adapter serves held names only, assembles 5-minute bars from `b` minute bars, and reconciles every disconnect and every session from REST (§13) | SPEC-P0.3 §6.2, RULE-B12, rule N5 | Yes | **High** — a lost bar hides a stop breach. §13.5 is the control |
| 10 | Raw news is snapshotted at first receipt into a P2.1 table; P2.1 writes no `news_item` (O-2) | Rule N16 loses history for every uncollected session; the sanitiser is P4.1 | Yes | Medium — isolation is by convention until a second role exists `[DEFAULT-6]` |
| 11 | `disseminated_at` is computed from an EDGAR acceptance instant only `[DEFAULT-12]` | Rule N1; no vendor date is verified as a dissemination time | Yes | Medium — fundamentals without an EDGAR match are absent |
| 12 | A price, volume or FX rate more precise than its column is rejected, not rounded. A dividend amount or split ratio is stored exactly in `corporate_action_terms`, with the 0001 row holding the rounded value and a flag `[DEFAULT-14]`, O-10 | `[CONST-6]` forbids a silently rounded market value; refusing a dividend or a split would misprice every later bar | Yes | Medium — a reader that ignores the flag uses a rounded amount or ratio |
| 13 | Thirteen append-only tables in migration 0002, no hypertable, no retention, no grant beyond `app_rw` (§22) | O-1, O-10; smallest set that holds the provenance the prompt requires and the exact corporate-action terms | Additive — a later migration can extend | Low |
| 14 | `run_id` in 0002 tables has no foreign key `[DEFAULT-15]` | `[P21-20]` | Yes — a constraint can be added | Low |
| 15 | A separate `config/ingest.yaml`, hashed, unsigned, read through the existing loader helpers (§23) | O-5 | Yes | Low |
| 16 | Redis caches three lookups and no market value (§17) | SPEC-P0.3 §13.1 row 17: not a system of record; a miss must never become a default | Yes | Low |
| 17 | `psycopg` 3, `httpx`, `redis`, `websockets` `[DEFAULT-10]` | Each replaces well over ten lines of standard library; none is an orchestration framework | Yes | Low |
| 18 | SPEC-P0.2's provider contracts are implemented verbatim at `src/provider/`; P2.1's own enum covers what `DataCapability` lacks (§4.1) | A frozen enum is not extended by a downstream phase | Yes | Low |
| 19 | An adapter with no verified field list has a contract and no mapping, and is not implementable (§4.4) | Block A: never invent an API field | — | None; the alternative is invented fields |
| 20 | Instruments are matched across ticker changes by `composite_figi` `[DEFAULT-13]`. No code may rely on it until `[A-10]` is verified against one documented ticker-rename case (O-9) | The only stable identifier in the verified reference fields | Yes, before live data; costly after | **High** — an identity break corrupts history for that name |
| 21 | P2.1's reference loader writes India tick-size rows to `tick_size_regime`, one bounded row per symbol per dump date (IR-21) `[DEFAULT-17]`, O-11. The one-day form is provisional (O-12) | P2.1 owns the reference loader (O-6); SPEC-P0.2 names the dump as India's reference source; one-day rows are the only form `app_rw` can write without superseding a row `[P21-28]` | Yes | Low today (India unfunded). After activation: a session with no dump loaded before its order window denies every India order; whether that is every session depends on `[OQ-25]` |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| A-1 | Volume agreement ratio 0.05 | No frozen spec gives a volume tolerance; two consolidated feeds can differ on late prints | Distribution of differences once a second source exists (§21) | Evidence only: more or fewer reconciliation rows |
| A-2 | Maximum clock skew 1 s | SPEC-P0.3 §13.1 row 20 requires a drift check and gives no number | Observe the host's offset under the chosen time daemon for a week | Too tight: false aborts. Too loose: the 3 s delivery budget is unmeasurable |
| A-3 | Backoff base 1 s, cap 300 s, 6 attempts, 30 s request timeout | Throttle semantics are unpublished for four providers (M-4) | Vendor answers to SPEC-P0.2 Q3, Q4; observed throttles | A run that gives up too early or overruns the 1800 s budget; the budget still bounds it |
| A-4 | News poll every 300 s; revision look-back 7 days | SPEC-P0.1 says "continuous" and gives no interval; edit latency is unmeasured (M-12) | M-12's measurement | Later first-seen times; missed late edits |
| A-5 | A raw news body over 1,000,000 characters is malformed | An unbounded untrusted string needs a ceiling; `NewsItem` bounds the sanitised body at 200,000 | Largest observed body after one month | A legitimate long item is not stored |
| A-6 | The 0002 tables stay small enough for plain tables without retention | Failure, gap and reconciliation rows are exceptional by design; EDGAR index bytes are the unknown | Table sizes after the first backfill, especially `edgar_index_snapshot` | SPEC-P0.3's disk model omits these tables; a large index archive would need its own line |
| A-7 | Stream ping interval and timeout 20 s; reconnect base 1 s, cap 60 s; silent-window recheck 10 s | SPEC-P0.2 records no application heartbeat or reconnect guidance for the Alpaca stream | Vendor documentation or support; observation at the stage 5 rehearsal | Slow detection of a dead socket, or needless reconnects |
| A-8 | Calendar must cover 20 sessions ahead | No frozen number | Owner | A late calendar load stops ingest earlier or later than intended |
| A-9 | Cache TTLs 86,400 s, 3,600 s, 60 s; lock 5,000 ms | No frozen number; none of the three values is authoritative | Load observation | Database load only |
| A-10 | `composite_figi` is stable across a ticker change | Not stated in any frozen spec | Vendor documentation and one documented ticker-rename case in the reference history. **Required by the Owner (O-9) before any P2.1 code relies on `[DEFAULT-13]`** | `[DEFAULT-13]` fails: identity breaks on rename |
| A-11 | Massive's "Eastern Time" is IANA `America/New_York` | SPEC-P0.2 says "presented in ET" | Vendor documentation | Bars assigned to the wrong trading date around midnight |
| A-12 | Settlement cycle of one session in both markets | Carried from SPEC-P1.1 A11 / `Q-P1.1-1`; this phase must write `settlement_date NOT NULL` | `Q-P1.1-1`, `Q-P1.1-2` | Wrong `settlement_date` on every session row; P2.9's settled-cash sizing inherits it |
| A-13 | A filing accepted after its cutoff is disseminated at 06:00 Eastern on the next Monday to Friday; one accepted before its cutoff is disseminated at acceptance | SPEC-P0.2 gives the cutoffs and "next business day", not the instant, the holiday list, or the propagation delay (M-8) | `[OQ-30]`; the M-8 measurement of §21 | `disseminated_at` too early: look-ahead by the difference, a full day across a federal holiday |
| D-1 | `[DEFAULT-1]` A daily bar's `ts` is the session's `regular_close_utc`; a 5-minute bar's is its window start | No frozen spec fixes the daily `ts`; SPEC-P0.2 §0.6 speaks of window start for minute bars | Owner approved 2026-10-07; check against P5.1's read set at its freeze | Look-ahead through `bars_asof`, or a re-key of `bar_daily` |
| D-2 | `[DEFAULT-2]` A daily bar is written at the scheduled ingest and compared with a re-fetch at the next session's ingest | SPEC-P0.3 Q-7 is open; storage is insert-only | Owner approved 2026-10-07; the `REVISION` measurement of §21 | A vendor revision is stored wrong for good, or caught one session late |
| D-3 | `[DEFAULT-3]` A second source's bar goes to `ingest_reconciliation`; only the SPEC-P0.2 primary writes a 0001 market-data table | One row per `(instrument_id, ts)`; rule N7 forbids a silent tiebreak | Owner approved 2026-10-07 | No second-source evidence, or a silent tiebreak |
| D-4 | `[DEFAULT-4]` Price tolerance is the tick in force; volume tolerance is the ratio of `[A-1]` | No frozen tolerance exists | Owner approved 2026-10-07; `[A-1]` by measurement | False alarms if too tight; missed errors if too loose |
| D-5 | `[DEFAULT-5]` Rule N7 is stored as reconciliation rows plus an EDGAR-sourced row at the next `restatement_seq` | `[P21-13]`: the unique key leaves no other insert | Owner approved 2026-10-07 | A source correction reads as an issuer restatement |
| D-6 | `[DEFAULT-6]` Raw news sits in schema `trading` behind explicit grants and a module boundary | Only one application role exists | Owner approved 2026-10-07; a second role is a P4.1 or P6.2 decision | Raw vendor text reachable from LLM-bound code |
| D-7 | `[DEFAULT-7]` Absence is no row plus manifest, failure and gap records; no sentinel row | `[CONST-6]`; `bar_*` cannot hold a sentinel | Owner approved 2026-10-07 | A consumer that skips the manifest reads absence as "did not trade" |
| D-8 | `[DEFAULT-8]` Batch freshness is "the most recent completed sequenced session is `COMPLETE`"; the stream keeps the frozen 600 s | `DATA-001`'s 600 s describes the intraday monitor; X3R-C6 is open | Owner approved 2026-10-07 | Every daily decision denied, or stale data accepted |
| D-9 | `[DEFAULT-9]` The India adapter is tested on fixtures built from documented response shapes, labelled synthetic | ADR-11: no India data spend before activation | Owner approved 2026-10-07; recorded fixtures before India activation; shapes pending `[OQ-25]` | A synthetic fixture encodes a wrong field |
| D-10 | `[DEFAULT-10]` `psycopg` 3, `httpx`, `redis`, `websockets`; P2.1 owns the write module for the tables it writes | Nothing in `src/` opens a connection; no dependency manifest exists | Owner approved 2026-10-07 | Later phases inherit an unsuitable client |
| D-11 | `[DEFAULT-11]` A daily run ingests an explicit `IngestSet` supplied by its caller; there is no implicit "everything" | ADR-14 and SPEC-P0.3 §13.1 row 2 speak of "the resolved universe"; nothing says who requests bars for non-members | Owner approved 2026-10-08; `[OQ-19]` | Reconstitution cannot rank names that were never ingested |
| D-12 | `[DEFAULT-12]` `disseminated_at` comes only from an EDGAR filing record through §19.2; fundamentals with no such record are not stored | Rule N1; no vendor date is verified as a dissemination time | Owner approved 2026-10-08; `[OQ-9]`, `[OQ-23]` | Look-ahead if relaxed; missing fundamentals as applied |
| D-13 | `[DEFAULT-13]` An instrument is recognised across a ticker change by `composite_figi` | It is the only stable identifier among the verified reference fields | Owner approved 2026-10-08, conditional on `[A-10]` being verified before any code relies on it | An identity break on rename |
| D-14 | `[DEFAULT-14]` A price, volume or FX rate more precise than its column is rejected and recorded; a dividend amount or split ratio is stored exactly in `corporate_action_terms`, with the 0001 row rounded and flagged | `[CONST-6]`; `Price` and `Money` round silently `[P21-16]`; 0001 cannot hold the exact terms `[P21-17]`, `[P21-18]` | Owner approved 2026-10-08, as amended by O-10 | A reader that ignores the flag uses a rounded amount or ratio |
| D-15 | `[DEFAULT-15]` `run_id` in the 0002 tables has no foreign key to `run_context` | `[P21-20]`: a key would gate every P2.1 write behind conditions 9 and 10 | Owner approved 2026-10-08 | A manifest row whose run has no `run_context` row |
| D-16 | `[DEFAULT-16]` A 5-minute bar is the deterministic aggregate of the minute bars received for its window; completion is exactly RULE-B12 | SPEC-P0.3 §6.2 fixes assembly from the `b` stream and does not state the aggregation | Owner approved 2026-10-08; the session-close check of §13.5 | A bar assembled across an unnoticed loss |
| D-17 | `[DEFAULT-17]` P2.1's reference loader writes India tick sizes to `tick_size_regime` from the instruments dump, by rule IR-21 | `[P21-27]`: nothing else loads them, and SPEC-P0.2 names the dump as India's reference source | Owner approved 2026-10-09 that P2.1 loads them (O-11) and, provisionally, the one-day row form (O-12); the dump's columns and publication time are `[OQ-25]`, unverified | Rule N10 denies every India order for want of a regime row |
| A-14 | `trading.deny_mutation()` works unchanged on a table 0001 did not attach it to | Read from the migration text, not executed | T-16 | The 0002 triggers need their own function |
| A-15 | SPEC-P0.2's facts are still true | Retrieved 2026-08-23 to 2026-08-26; this phase re-verified none | Re-read each cited page before the code phase | A field or limit changed under the adapter |

## OPEN QUESTIONS

"Blocks freeze" means SPEC-P2.1 cannot move to `FROZEN` for the named part while the question is
open. Nothing here is answered by this document.

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| OQ-1 | What is the source of exchange sessions, half-days and special sessions for NYSE, NASDAQ, NSE and BSE? | Owner, then vendor documentation | Does any bought provider publish a trading-calendar endpoint with early closes? For India: the NSE and BSE holiday and Muhurat circulars. Name the source, its fields and its update cadence | **Blocks freeze** of §6.2 and the calendar adapter; all P2.1 gap detection |
| OQ-2 | When is a Massive daily aggregate final? (SPEC-P0.3 Q-7) | Massive documentation or support | "Is a `1/day` aggregate for date D final at 21:45 UTC on D, or revised later, and until when?" | P2.1 schedule; mitigated by `[DEFAULT-2]` |
| OQ-3 | FMP payload size per statement request (SPEC-P0.3 Q-5) | Measurement | `Content-Length` on 10 representative statement calls | Backfill plan |
| OQ-4 | Throttle status and headers for Massive, FMP, SEC; FRED's numeric limit (SPEC-P0.2 M-4) | Vendor support | "Which status code and headers indicate throttling, and is `Retry-After` set?" | Client tuning only |
| OQ-5 | Stream reconnect and replay semantics (SPEC-P0.2 M-3) | Vendor support | "On reconnect, are missed messages replayed; is there a resume token or sequence number?" | Nothing — rule N5 holds either way |
| OQ-6 | EDGAR propagation latency (SPEC-P0.2 M-8) | Measurement, §21 | Acceptance-to-availability deltas over one week of Form 4 filings | The margin in §19.2 |
| OQ-7 | The RBI USD/INR reference-rate endpoint, its fields and a fallback (SPEC-P0.1 Q12) | RBI publications | The published location and format of the daily reference rate; publication time; holiday behaviour | FX adapter; India activation |
| OQ-8 | India sources for fundamentals, corporate actions and news | Owner | Does Zerodha Kite Connect publish corporate actions? Which vendor covers NSE/BSE fundamentals? | India activation |
| OQ-9 | SEC EDGAR response fields: the filing identifier, acceptance timestamp, form type, document path on `data.sec.gov` submissions; the XBRL company-facts shape; the Forms 3/4/5 document format and the fields to extract | SEC documentation | The SEC's EDGAR API documentation for `data.sec.gov`, and its technical specification for ownership documents (exact pages not retrieved by this phase) | **Blocks freeze** of §19 mappings and the EDGAR adapter; P2.5's insider feature |
| OQ-10 | What is a "material" disagreement under rule N7, and which metrics are compared under which names in each source? | Owner | SPEC-P0.2 rule N7 gives no threshold or list | **Blocks freeze** of §19.3 step 4 |
| OQ-11 | Replace `[A-1]` and `[A-2]` with measured or decided values | Measurement; Owner | §21 | Not blocking |
| OQ-12 | Who emits `RUN_STARTED` and `RUN_FINISHED` for an ingest run before P6.4 exists? | Owner, **with condition 9** | `EVENT_REGISTRY`: producer `P6.4_ORCHESTRATOR` | P2.1 code that writes an audit event |
| OQ-13 | What does `DATA_RECEIVED`'s trigger mean when P2.2 runs after storage; what event records a P2.1 rejection or a provider failure; what does `CORPORATE_ACTION_APPLIED` mean under rule N9? | Owner, **with condition 9** | `src/audit/events.py` lines 322–334; SPEC-P1.4 §3 | P2.1 code that writes an audit event |
| OQ-14 | `Q-P1.2-7` / X3R-M1: columns or database preimage; where the reproducibility bundle is stored; who owns the audit writer | Owner — **X5 condition 9. Not decided in P2.1** | SPEC-P1.2 OPEN QUESTIONS; STAGE-1-FREEZE §12.3; STAGE-1-GAP-AUDIT §10 | P2.1 code that writes an audit event |
| OQ-15 | By what authority is 600 s used where the research summary says 5 s? (X3R-C6) | Owner | STAGE-1-FREEZE §12.4 | Recorded only |
| OQ-16 | Which data subscriptions are active, so that fixtures can be recorded? | Owner | Massive Stocks Developer, FMP Premium, an Alpaca account | P2.1 tests T-1, T-2 |
| OQ-17 | How does `ingest_config_hash` relate to `run_context.config_hash` and `config_version`? | Owner / P1.3 | SPEC-P1.3 §9; migration §6.9 | Provenance; with `[P21-20]` |
| OQ-18 | Do the Stage 1 suites pass on Python 3.12+? (X5 condition 15) | Execution | Run the six suites on 3.12 | Carried |
| OQ-19 | Which instruments outside the current universe need daily bars so that reconstitution can rank them, and which phase requests them? | P2.3 | ADR-14: 1,300/1,700 hysteresis needs ranks beyond membership | P2.3; P2.1's ingest-set default `[DEFAULT-11]` |
| OQ-20 | Does an ingest run write `stage_latency_observation`, and with what `strategy_version`? | Owner / P6.1 | Migration §6.9: `strategy_version NOT NULL` | Not blocking |
| OQ-21 | ~~How are corporate-action terms that 0001 cannot hold exactly to be stored?~~ | **CLOSED 2026-10-08 by Owner decision O-10** | Option 2 was chosen: the P2.1-owned table `corporate_action_terms` (§22.12), keyed by `action_id`. SPEC-P1.1 and SPEC-P1.2 are not re-opened | **Closed** |
| OQ-22 | Massive: the Ticker Types value list; `primary_exchange` values; the Ticker Events endpoint and fields; the trades endpoint and fields; whether `v` is ever non-integer | Massive documentation | Massive's REST documentation for tickers, ticker types, ticker events and trades, under `massive.com/docs/rest/stocks/` (exact pages not retrieved by this phase) | **Blocks freeze** of the reference mapping tables and `Q-P1.1-6` method (b) |
| OQ-23 | FMP: statement endpoints, field names, period and date fields, how restatements appear | FMP documentation | FMP's developer documentation under `site.financialmodelingprep.com/developer/docs` for income statement, balance sheet and cash flow (exact pages not retrieved by this phase) | **Blocks freeze** of the FMP adapter |
| OQ-24 | FRED / ALFRED: parameters and fields of `series/observations` and `series/vintagedates`; how a missing observation is marked; where series notes are returned | FRED documentation | The `fred/series/observations`, `fred/series/vintagedates` and `fred/series` pages under `fred.stlouisfed.org/docs/api/fred/` (exact pages not retrieved by this phase) | **Blocks freeze** of the FRED adapter |
| OQ-25 | Zerodha: historical-candle endpoint parameters and response shape; the instruments dump columns; timestamp timezone; whether the dump for a session is published before that session's order window (IR-21) | Kite Connect documentation | The historical-candle and instruments pages under `kite.trade/docs/connect/v3/` (exact pages not retrieved by this phase) | **Blocks freeze** of the Zerodha adapter; `[DEFAULT-9]` fixtures; IR-21's provisional form (O-12) |
| OQ-26 | What is the source of `HALTED` and `SUSPENDED` status? | Owner; vendor documentation | Alpaca's `s` trading-status channel is excluded by SPEC-P0.3 §13.3 row 40; RULE-B12c refers to "the calendar" reporting a halt | P3.3; P2.1 writes neither status |
| OQ-27 | How is an `exchange_session` row corrected after an unscheduled early close? | Owner / SPEC-P1.2 | The table has no bitemporal axis and `app_rw` cannot update it | Operational runbook, P6.4 |
| OQ-28 | Which FIGI does `instrument.figi` hold? | SPEC-P1.1 / SPEC-P1.2 author | Both columns are documented only by name | Not blocking; the column stays `NULL` |
| OQ-29 | What is the source for stock dividends, mergers, acquisitions, spin-offs, rights issues and exchange transfers? | Vendor documentation | Alpaca's corporate-actions announcements API; Massive Ticker Events | Seven of eleven action types; P3.3 conversion |
| OQ-30 | Which days are EDGAR business days, and at what instant on the next business day is a post-cutoff filing disseminated? | SEC | The SEC's published federal-holiday closure list; the EDGAR dissemination schedule | §19.2; `[A-13]` |
| OQ-31 | Which macro series does regime detection need? | P2.6 | ADR-04: "rates, yields, VIX, macro series" | P2.6; macro ingest is disabled until then |
| OQ-32 | How is migration 0002 applied, and does `trading.deny_mutation()` serve tables beyond 0001's? | Owner / SPEC-P1.2 §11 | `scripts/apply-migration.sh`; X3R-C12 | P2.1 code |
| OQ-33 | Should `ingest.yaml` be signed like `policy.yaml`? | Owner / P6.2 | SPEC-P1.3 §5 | Not blocking |
| OQ-34 | Does IR-21's one-day row form survive the answer to `[OQ-25]`? **Decided provisionally 2026-10-09 (O-12): one row per symbol per dump date, valid one day.** The Owner first approved "a new row only when the value changes"; `[P21-28]` shows that form cannot be written by `app_rw` | Owner, once `[OQ-25]` is answered | If the dump for a session is available before that session's order window: confirm the form. If it is not: choose between writing the next session's row from the previous dump, a pre-open reference run, removing IR-21 in favour of P3.1 or P3.2, or amending SPEC-P1.2 so a regime row can be closed | **Blocks freeze** of IR-21 only. India is unfunded |

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|---|---|---|---|
| `IngestDataType`, `ManifestStatus`, `FailureKind`, `GapKind`, `GapState`, `ReconKind` | type (enum) | §4.1, §15.1 | P2.2, P2.3, P6.1 |
| `ProviderId`, `DataCapability`, `ProviderRole`, `TokenLifetime`, `RateLimit`, `CredentialSpec`, `IdempotencySpec`, `ProviderSpec` at `src/provider/` | type | SPEC-P0.2 §10.1–10.2, verbatim | P3.1, P6.1 |
| Provider protocols (`ReferenceProvider`, `CalendarProvider`, `DailyBarProvider`, `IntradayBarProvider`, `CorporateActionProvider`, `FundamentalsProvider`, `FilingsProvider`, `MacroProvider`, `FxProvider`, `NewsProvider`, `BarStream`), `Page`, the `IngestError` hierarchy and the wire records (`WireBar`, `WireSplit`, `WireDividend`, `WireInstrument`, `WireSession`, `WireNews`, `WireFundamentals`, `WireFiling`, `WireMacroObservation`, `WireFxRate`) | type (protocol, model, exception) | §4.2, §4.3, §28.1 | P2.1 adapters only; P3.1 as a pattern |
| `trading.ingest_manifest` | table | §22.1. Status of record = latest row by `finished_at` | **P2.2, P2.3**, P6.1 |
| `trading.ingest_failure`, `trading.ingest_gap` | table | §22.3, §22.4 | **P2.2**, P6.1 |
| `trading.ingest_reconciliation` | table | §22.5 | **P2.2** (layer 5) |
| `trading.ingest_checkpoint` | table | §22.2 | P2.1 only; P6.4 runbook |
| `trading.provider_instrument_ref` | table | §22.6 | P2.5 (CIK join), P3.1 |
| `trading.raw_news_snapshot` and its hand-off guarantees | table + rule | §22.7, §18 | **P4.1 only** |
| `trading.macro_series`, `trading.macro_observation` and the vintage read rule | table + rule | §22.8, §19.5 | **P2.6**, P5.1 |
| `trading.edgar_index_snapshot`, `trading.edgar_filing`, `trading.insider_filing_raw` | table | §22.9–22.11 | P2.5, P4.1, P5.1 |
| `trading.corporate_action_terms` | table | §22.12, §8.2. Exact dividend amount, `split_from`, `split_to`, `distribution_type`, `frequency`, record and declaration dates; one row per `corporate_action` row of those three types | **P2.4**, P2.5, P5.1 |
| Absence contract | rule | §15.3 | **Every consumer of market data** |
| Bar write rules; daily `ts` = session close; `is_final` is always true in storage | rule | IR-19, IR-20, `[DEFAULT-1]`, §9.2 | P2.4, P5.1 |
| Corporate-action read-time order, using the exact terms | rule | §8.4 | P2.4, P5.1 |
| Gap definition | rule | §11 | P2.2 |
| Freshness facts per data type | rule | §16.1 | P2.2, P2.9 |
| `HeldNamesBarFeed`, `StreamGapNotice` | type (interface) | §13.6 | **P3.3** |
| Calendar loader; reference-data loader | function | §6; writes `exchange_session`, `instrument`, `symbol_mapping`, and India rows of `tick_size_regime` (IR-21) | P2.3, P2.9, P3.2 |
| `config/ingest.yaml`, `IngestConfig` | config | §23, §28.2 | P6.2, P6.4 |
| `IngestSet`, `BackfillJobRequest`, `DailyRunRequest`, `DailyRunResult` | type (model) | §12.3, §28.3 | P2.3 (builds the ingest set), P6.4 (invokes runs and jobs) |
| Redis keys under the prefix `ingest:v1:` | convention | §17 | Other phases must not write under this prefix |
| Rules IR-1 to IR-21 | rule | §5, §6, §8, §9 | P2.2, X2 |
| Measurement of maximum vendor price scale | measurement | §21 | P2.2 (X5 condition 4) |
| `DATA_RECEIVED`, `FX_RATE_RECORDED`, `CORPORATE_ACTION_APPLIED` — P2.1's proposed emission points | event (proposal, gated) | §20. **Defined by SPEC-P1.4; nothing is added or changed** | Condition 9 decision; P1.4 |

---

## Acceptance self-check

| Requirement | State |
|---|---|
| Block B header, four tables | Present |
| Every entity has a Pydantic model or DDL | Wire records, protocols, errors: §4. Request and result models: §12.3. Stream interface: §13.6. Enums: §4.1, §15.1. Config: §23. Tables: §22 |
| Every field: name, type, unit, timezone, nullability, valid range, violation | §28 |
| Every error path enumerated with fail-closed behaviour | §24, 35 rows |
| Block C: at most ten blocking questions, each with options, default and consequence | §1: ten grouped questions covering `[DEFAULT-1]` to `[DEFAULT-17]` |
| Block C: every default marked inline and listed in ASSUMPTIONS | Markers throughout the body; rows D-1 to D-17 |
| Block C: non-blocking details | §2, including rounding, tick and lot size, percentage units, DST, half-days, integer or decimal, inclusive or exclusive bounds |
| Block C: every rule has its edge case | Rule tables in §5, §6, §8, §9, §13.1, §16, §17, §18, §19, §23.1 each carry an edge-case column with no empty cell |
| No pseudocode; no ellipsis; no placeholder | No stub body is an ellipsis. The four remaining ellipsis characters are elisions inside quotations of the P2.1 prompt and of X5 condition 11. Six adapters have no field mapping. That is stated as open questions with exact queries (§4.4, `[P21-25]`), which is what Block A prescribes for an unknown API field |
| P2.1 prompt items | Protocol and adapters §4; backfill §10; streaming §13; normalisation §7, §8; idempotency and reconciliation §9, §14; failure policy §15; freshness §16; Redis §17; tests §25 |
| Frozen specs modified | None |
| `Q-P1.2-7` / X3R-M1, OQ-12, OQ-13 | Carried, unresolved |
| P3 / P4 responsibilities absorbed | None: no monitor, no sanitiser, no `news_item`, no verdicts |

**Known deviations, declared.** (1) This is the specification half of the P2.1 deliverable; the
implementation and tests are blocked by STAGE-1-FREEZE §9.2. (2) The spec cannot be frozen whole
while OQ-1, OQ-9, OQ-10 and OQ-22 to OQ-25 are open; it could be frozen for the Massive and Alpaca
paths alone if the Owner chose to split it. (3) `[DEFAULT-13]` is approved conditionally: no code
may rely on it until `[A-10]` is verified against one documented ticker-rename case.

---

# SPEC-P2.1-INGEST v0.4 — DRAFT. NOT FROZEN. NOT IMPLEMENTABLE.
