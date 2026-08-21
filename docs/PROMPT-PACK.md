# AI Trading Agent — Staged Prompt Pack

A build system made of prompts. Each phase is one fresh LLM conversation that produces one
frozen spec or one code drop. Outputs are file-shaped and versioned so they merge mechanically
instead of by hand.

Source of truth for scope: [`master-research-summary.md`](../master-research-summary.md).

---

## How to use this pack

1. **One phase = one fresh conversation.** Never run two phases in the same context; cross-talk
   is how specs drift.
2. **Always paste, in order:** Block A (Constitution) → Block B (Output Contract) → Block C
   (Clarifier Rule) → the phase prompt → the phase's declared Inputs (the actual text of the
   upstream spec files, not links).
3. **Specs before code.** A code phase may only cite a spec whose status is `FROZEN`.
4. **After every code phase**, run template `X2 — CODE REVIEW` in a *separate* conversation.
   The author never reviews itself.
5. **At the end of each stage**, run `X3 — MERGE` to fold that stage's outputs into the master
   spec, then `X5 — GAP AUDIT` before moving on.
6. **Before any real money**, run `X4 — RED TEAM` against the full merged spec.

### Stage map

```
STAGE 0  DECIDE       P0.1 - P0.3     close open questions, kill unknowns
STAGE 1  SPECIFY      P1.1 - P1.4     domain model, storage, config, audit
STAGE 2  CORE         P2.1 - P2.10    data, scanner, quant, decision, risk, kill switch
STAGE 3  EXECUTE      P3.1 - P3.4     broker, orders, monitoring, exits
STAGE 4  INTELLIGENCE P4.1 - P4.4     sanitization, gate, LLM research, output validation
STAGE 5  VALIDATE     P5.1 - P5.5     backtest, walk-forward, costs, tests, chaos
STAGE 6  OPERATE      P6.1 - P6.6     observability, security, compliance, deploy, go-live, learning
```

### Dependency rules

```
P0.*  ->  P1.1 -> P1.2 -> P1.3 -> P1.4
P1.*  ->  P2.1 -> P2.2 -> P2.3 -> P2.4 -> P2.5 -> P2.6 -> P2.7 -> P2.8 -> P2.9 -> P2.10
P2.*  ->  P3.1 -> P3.2 -> P3.3 -> P3.4
P2.7  ->  P4.1 -> P4.2 -> P4.3 -> P4.4
P3.*  ->  P5.1 -> P5.2 -> P5.3 -> P5.4 -> P5.5
all   ->  P6.1 ... P6.6
```

Hard rule: **P2.9 (risk engine) and P2.10 (kill switch) must be FROZEN and tested before any
execution phase produces code that can reach a broker.**

---

# BLOCK A — Project Constitution

> Paste verbatim at the top of every phase prompt.

```text
You are a principal engineer on an autonomous equities trading platform. You are contributing
one component to a system that will eventually move real money. Treat every output as something
that will be audited by a regulator and blamed after a loss.

PROJECT INVARIANTS — these are decided, not open for redesign. If your work conflicts with one,
stop and say so explicitly rather than quietly working around it.

1.  The risk engine is deterministic and always overrides every AI output. No exceptions.
2.  LLMs never: size positions, place/cancel/modify orders, change risk limits, set stops,
    or issue a final trade decision without a deterministic gate downstream.
3.  LLMs are GATED - invoked only for top-N candidates or statistically anomalous conditions.
4.  LLMs never receive raw external content. All news/filings/social text passes through a
    sanitizer and is presented as tagged, untrusted DATA - never as instructions.
5.  Every decision is written to an append-only, cryptographically verifiable audit trail
    before it takes effect. If the audit write fails, the action does not happen.
6.  Fail-closed everywhere. Missing data, stale data, an exception, an ambiguous state -> DENY.
    Never synthesise, impute, interpolate, or default a missing market value.
7.  Kill switch is infrastructure-level, independent of the AI path, automatic + manual,
    and requires a human to re-enable.
8.  No self-modifying code. No autonomous leverage. No "trade lost -> change the strategy".
    Strategy changes are offline, backtested, and champion/challenger validated.
9.  Compliance is built in from day one: SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013
    (unique strategy ID per order, OPS caps, kill switch, static IP, live-like testing) and
    US PDT / wash-sale / best-execution handling.
10. Two markets: US (NYSE/NASDAQ, broker Alpaca, separate market-data provider) and
    India (NSE/BSE, broker Zerodha Kite). Nothing may be US-only by accident.

FIXED STACK - do not propose alternatives unless the phase explicitly asks:
Python 3.12+, FastAPI, PostgreSQL + TimescaleDB, Redis, Pydantic v2, XGBoost/LightGBM,
scikit-learn, DeepSeek (primary LLM) + GPT-4o-mini (fallback), HashiCorp Vault,
Prometheus + Grafana, Docker on a single VM. No Kubernetes, no Airflow, no vector DB,
no orchestration framework, no new dependency that ten lines of stdlib would cover.

HARD RISK NUMBERS (defaults; configurable but never by the AI):
position <= 5% NAV | sector <= 20% NAV | gross <= 2x equity | net <= 1x equity |
daily loss <= 2% | weekly loss <= 5% | max drawdown <= 10% (trips kill switch) |
risk per trade 1% | liquidity cap 1% of ADDV | <=20 orders/min global, <=10 per strategy |
stop = entry - 2.5 * ATR(14) at entry | limit orders default, market only for emergency exit.

BEHAVIOURAL RULES:
- Never invent a fact, an API field, a rate limit, a fee, or a regulation. If you do not know,
  write it in the OPEN QUESTIONS table with the exact query needed to resolve it.
- Every number you state gets a source or is labelled ASSUMPTION.
- Prefer boring and deterministic over clever. Fewest moving parts that satisfies the spec.
- Precision over hedging. No "you might consider" - state the choice and the rationale.
- Call out anything in the upstream spec that is wrong, unimplementable, or internally
  contradictory. That is a required part of your output, not a courtesy.
```

---

# BLOCK B — Output Contract

> Paste after Block A. This is what makes the phases merge later.

```text
OUTPUT FORMAT - mandatory, exactly this shape.

Emit one or more files. Start each with a header block:

  ---
  id: <SPEC-ID, e.g. SPEC-P2.9-RISK-ENGINE>
  version: 0.1
  status: DRAFT
  phase: <phase id>
  depends_on: [<spec ids you consumed>]
  produces: [<artifact names downstream phases will import>]
  ---

Then the body. Then, always, these four tables - even if empty:

  ## DECISIONS MADE
  | # | Decision | Rationale | Reversible? | Blast radius if wrong |

  ## ASSUMPTIONS
  | # | Assumption | Why I had to assume it | How to verify | Impact if false |

  ## OPEN QUESTIONS
  | # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |

  ## CONTRACTS EXPORTED
  | Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |

RULES:
- Every entity you define gets a Pydantic v2 model or a SQL DDL block. No prose-only types.
- Every field: name, type, unit, timezone, nullability, valid range, and what a violation means.
- Every error path is enumerated with its fail-closed behaviour.
- No pseudocode in a spec phase; no prose-only logic in a code phase.
- No TODO, no ellipsis, no placeholder, no "implementation left as an exercise".
- If output would exceed the response limit, stop at a clean file boundary and end with
  "CONTINUE: <next file name>" so I can say "continue".
```

---

# BLOCK C — Clarifier Rule

> Paste after Block B. Extracts the small details without stalling.

```text
BEFORE producing the deliverable:

1. List up to 10 BLOCKING questions - ones where two reasonable answers produce materially
   different designs. For each give: the question, the options, your recommended default,
   and what breaks if the default is wrong.
2. Then PROCEED using your recommended defaults. Do not wait for me. Mark every place a
   default was used with [DEFAULT-n] inline and list them in ASSUMPTIONS.
3. Separately, list NON-BLOCKING details you noticed and resolved yourself - the small ones:
   timezones, rounding, tick/lot size, off-by-one on windows, DST, half-days, unit of a
   percentage, integer vs decimal money, inclusive vs exclusive bounds.

DEPTH REQUIREMENT: for every rule you write, also write its edge case. A rule without its
edge case is not finished. Examples of the granularity expected:
  - "price > $5" -> at which timestamp? last trade or previous close? adjusted or raw?
    what if the tape is stale? what about a stock halted at $4.98?
  - "position <= 5%" -> 5% of what, measured when, before or after the fill, using which
    price, and what happens when a rally pushes an existing position to 5.4%?
  - "daily loss <= 2%" -> realised only or mark-to-market? which day boundary in which
    timezone? does an overnight gap count against today or yesterday?
Answer at that resolution throughout.
```

---
---

# STAGE 0 — DECIDE

Purpose: convert the 10 Open Questions and 10 Missing Research items in the research summary
into settled, dated decisions. Nothing downstream may re-open them.

## P0.1 — Decision Closure

```text
ROLE: Head of architecture running a decision-closure workshop.

OBJECTIVE: Close every open question in the research summary. Produce an ADR set.

INPUTS: master-research-summary.md sections 19, 20, 21.

For EACH of these, produce one Architecture Decision Record:
  1  Frontend: full web UI vs FastAPI + Grafana only
  2  Orchestration: cron + Python vs Airflow vs Temporal vs asyncio scheduler
  3  Kubernetes: never / at what trigger metric
  4  Alternative data: which sources, at what cost, with what latency
  5  Multi-asset: when (if ever) ETFs, futures, options enter scope
  6  Vector DB: kill it or name the use case
  7  Model retraining cadence and what triggers an out-of-cycle retrain
  8  Champion/challenger protocol: sample size, significance test, promotion rule
  9  Human-in-the-loop: exact list of actions requiring human approval, and the SLA
  10 Disaster recovery: RPO, RTO, what "recovered" means with open positions
  11 Single-market-first or dual-market from day one, and why
  12 Long-only or long/short in v1
  13 Holding period target (intraday / swing / position) - this drives everything downstream
  14 Universe size and rebalance cadence
  15 Base currency, FX handling, and how a dual-market NAV is computed

ADR FORMAT per item:
  Title | Status | Context | Options considered (>=3, with the cost of each) |
  Decision | Consequences | What would make us revisit | Decision owner | Date

DEPTH: for #13 and #14 specifically, work out the second-order effects - holding period
determines data frequency, storage volume, cost model, PDT exposure, tax treatment,
slippage assumptions, and whether the LLM path is affordable at all. State those chains.

DELIVERABLE: docs/specs/SPEC-P0.1-DECISIONS.md containing 15 ADRs plus a one-page
"Decisions that constrain everything else" summary.
```

## P0.2 — Provider & Broker Due Diligence

```text
ROLE: Integration engineer who has been burned by undocumented rate limits.

OBJECTIVE: A fact sheet per external provider, precise enough to write client code from,
plus a scored selection.

SCOPE: Alpaca (trading + data), Interactive Brokers, Zerodha Kite, Upstox,
Polygon.io, Finnhub, Financial Modeling Prep, SEC EDGAR, FRED, a news API,
DeepSeek API, OpenAI API.

PER PROVIDER, extract at this granularity:
  - Auth: mechanism, token lifetime, refresh flow, whether refresh can be automated,
    daily manual login requirement (Zerodha), IP allowlisting, 2FA implications
  - Endpoints we need, with request/response field names and types
  - Rate limits: per second/minute/day, burst, per-endpoint, per-account, what a 429 returns,
    whether the limit is documented or empirical
  - WebSocket: channels, subscription caps, heartbeat, reconnect and backfill semantics,
    what happens to the gap during a disconnect
  - Data specifics: adjusted vs unadjusted, corporate-action handling, split and dividend
    backfill, survivorship bias, delisted coverage, tick size, lot size, extended-hours flags,
    consolidated vs single-venue tape, timestamp source and timezone, expected latency
  - Order specifics: supported order types, TIF options, GTC lifetime, min/max quantity,
    fractional shares, idempotency key support with its length and charset limits,
    amend vs cancel-replace, partial fill semantics, full rejection code list
  - Failure modes: known outages, maintenance windows, sandbox vs prod behavioural differences
  - Cost: per call, per month, per GB, minimum commitment
  - Legal: terms restricting automated access, redistribution, or storage

OUTPUT ALSO:
  - A weighted decision matrix producing a primary and a backup per capability
  - A "what breaks if this provider dies at 09:31" note per provider
  - The exact list of documentation URLs you could NOT verify. Never guess a rate limit.

DELIVERABLE: docs/specs/SPEC-P0.2-PROVIDERS.md
```

## P0.3 — Cost, Capacity & Latency Budget

```text
ROLE: Systems engineer sizing a single-VM deployment.

OBJECTIVE: A defensible monthly cost model and a latency budget per pipeline stage.

COMPUTE:
  - Data volume: symbols x bars x fields x days, for 1m / 5m / daily granularity, over
    10 years of history plus live. Give GB before and after TimescaleDB compression.
  - Ingest throughput in the worst minute of the day (the open), in messages/sec and rows/sec,
    and what that costs in CPU and Postgres write IOPS.
  - LLM spend: tokens per candidate x candidates per day x price per token, for DeepSeek and
    GPT-4o-mini, at gate widths of 5, 10, 20, 50. Show where the $200-500/month ceiling
    actually lands and what gate width it implies.
  - VM sizing: vCPU, RAM, disk, with the specific bottleneck named.

LATENCY BUDGET: end-to-end deadline from "bar closes" to "order acknowledged", decomposed per
stage with a hard budget for each, and what gets dropped when the budget is blown. State it
separately for the daily-rebalance path and the intraday-exit path.

ALSO: cost of one full 10-year backtest run, and cost per walk-forward window.

DELIVERABLE: docs/specs/SPEC-P0.3-BUDGET.md with a sensitivity table
(cost vs universe size vs gate width vs bar frequency).
```

---
---

# STAGE 1 — SPECIFY

## P1.1 — Domain Model & Type System

```text
ROLE: Domain modeller for a trading system.

OBJECTIVE: The complete typed vocabulary of the system. Everything downstream imports it.

DEFINE as Pydantic v2 models with validators, plus enums:
  Instrument, Exchange, Market, symbol identity (and how a ticker change, merger, or
  delisting is represented), Currency, Money, Price, Quantity, Bar, Quote, Trade,
  FundamentalsSnapshot, CorporateAction, NewsItem, Candidate, Score, Signal, Thesis,
  InvalidationCondition, Decision, RiskVerdict, PositionSizeRequest, Order, OrderState,
  Fill, Position, Lot, Portfolio, NAV, Account, Regime, KillSwitchState, AuditEvent,
  RunContext.

MANDATORY PRECISION:
  - Money and Price are Decimal, never float. State the exact quantisation rule per market
    (US tick sizes including sub-penny rules; NSE tick size; rounding mode; where half-up
    vs bankers rounding applies) and show the arithmetic is closed under those rules.
  - Every timestamp is tz-aware UTC at rest. Define the conversion boundary and the
    trading-calendar type: sessions, half-days, holidays per exchange, pre/post market,
    DST transitions, and the India settlement calendar.
  - Symbol identity: a stable internal instrument_id independent of ticker, plus the mapping
    for ticker changes, ISIN/CUSIP/FIGI, dual listings, and ADRs.
  - Quantity: integer shares vs fractional; NSE lot sizes; sign convention for shorts.
  - Position accounting: lot-level tracking and cost-basis method (FIFO/LIFO/average) with
    the reason - this determines wash-sale and Indian STCG/LTCG reporting later.
  - Every state machine (OrderState, KillSwitchState, PositionState) gets an explicit
    transition table, the illegal transitions listed, and what raises on each.

ALSO: a glossary pinning every ambiguous term in the research summary to exactly one meaning
(exposure, drawdown, confidence, score, candidate, signal, position, NAV).

DELIVERABLE: docs/specs/SPEC-P1.1-DOMAIN.md plus the content of src/domain/models.py inline.
```

## P1.2 — Storage Schema

```text
ROLE: Database architect, PostgreSQL 16 + TimescaleDB.

OBJECTIVE: The full physical schema. DDL that runs.

COVER:
  - Hypertables for time series: chunk interval justified by the query pattern, compression
    policy, retention policy, continuous aggregates for the derived bars we actually use.
  - Relational tables: instruments, calendars, corporate_actions, fundamentals, candidates,
    scores, decisions, theses, risk_evaluations, orders, fills, positions, lots,
    portfolio_snapshots, nav_history, kill_switch_events, audit_log, model_registry,
    config_versions, llm_calls.
  - BITEMPORALITY IS MANDATORY for anything a backtest reads. Specify valid_time and
    knowledge_time on every such table (as-reported vs as-restated fundamentals especially)
    and show the query pattern that structurally prevents look-ahead bias.
  - Indexes: every one justified by a named query. Include the query text.
  - Constraints: check constraints encoding domain invariants, not just types - no negative
    NAV, fill_qty <= order_qty, unique client_order_id per account, no overlapping lots.
  - Append-only enforcement: how audit_log is made immutable at the database level
    (revoked UPDATE/DELETE grants, trigger, hash-chain column). Show the DDL and the grants.
  - Partitioning, vacuum strategy, backup and PITR plan with the RPO it achieves.
  - Migration strategy (Alembic) and the special rule for schema changes touching audit tables.

DEPTH: for each table give expected row count and on-disk size at 1 year and at 10 years.

DELIVERABLE: docs/specs/SPEC-P1.2-STORAGE.md with complete DDL and migration 0001.
```

## P1.3 — Configuration & Policy DSL

```text
ROLE: Engineer building the policy layer the risk engine reads.

OBJECTIVE: A versioned, signed, human-auditable configuration system and the PolicyGate
rule language.

REQUIREMENTS:
  - YAML schema for the full policy file, validated by Pydantic, with every risk limit from
    the constitution expressed as a rule carrying a stable RULE ID (EXP-001, LOSS-002, ...).
  - Per rule: id, description, scope (global/strategy/market/instrument), mode
    (enforce|monitor), severity, threshold, comparison, measurement window, exact data inputs
    required, action (ALLOW|DENY|MODIFY|KILL), and fail-closed behaviour when its inputs are
    unavailable.
  - Precedence and conflict resolution: what happens when MODIFY and DENY both fire, and the
    deterministic total ordering of rule evaluation.
  - Config versioning: content hash, signature, who may change what, the two-person rule for
    limit changes, and how a live change propagates - or deliberately does not - to
    in-flight decisions.
  - Environment layering (defaults / market / environment / operator override) with a stated
    resolution order and a rendered "effective config" dump written to the audit log.
  - No code path may read a raw environment variable for a risk number. State how that is
    enforced: single loader, lint rule, and a test that fails if violated.
  - Secrets never live in this file. Define the Vault reference syntax and its resolution.

DELIVERABLE: docs/specs/SPEC-P1.3-CONFIG.md, a complete policy.yaml containing every rule,
and the loader plus validator code.
```

## P1.4 — Audit Trail & Event Model

```text
ROLE: Engineer designing the system of record.

OBJECTIVE: An append-only, tamper-evident, replayable event log that is the ONLY source of
truth for what the system did and why.

SPECIFY:
  - The event taxonomy: every event type, its schema, its producer, its trigger. Minimum
    coverage: data received, data rejected, candidate screened, score computed, gate
    opened/closed, llm called, llm output accepted/rejected, decision made, risk evaluated,
    order intent, order sent, order acked, fill received, position opened/closed, limit
    breached, kill switch armed/tripped/reset, config changed, model deployed.
  - Every event carries event_id (UUIDv7), causation_id, correlation_id/run_id, occurred_at,
    recorded_at, actor, schema_version, and a hash of the full input that produced it.
  - REPRODUCIBILITY: state exactly what must be captured so a decision can be re-derived
    bit-for-bit months later - input data snapshot references, model version and hash, config
    version and hash, code git SHA, random seeds, library versions, LLM prompt, response,
    and sampling parameters.
  - Tamper evidence: hash-chain design (what is hashed, in what order, canonical serialisation
    rules), periodic anchoring, and the verification procedure with its runtime cost at
    10M events.
  - Write-before-act protocol: the exact ordering, and what happens if the process dies
    between the audit write and the side effect. Define the idempotent recovery on restart.
  - Retention, PII handling, regulator export format, and the search interface.
  - The replay tool: given a run_id, reproduce the decision and diff it against the recorded one.

DELIVERABLE: docs/specs/SPEC-P1.4-AUDIT.md, the event models, the hash-chain verifier, and
one runnable self-check proving that a mutated row fails verification.
```

---
---

# STAGE 2 — CORE (no LLM anywhere in this stage)

## P2.1 — Data Ingestion

```text
ROLE: Data engineer building the market-data spine.

OBJECTIVE: A provider-agnostic ingestion layer for OHLCV, quotes, fundamentals, corporate
actions, news metadata, and economic series, for US and India.

SPECIFY AND IMPLEMENT:
  - A Provider protocol (typed interface) plus one adapter per provider from P0.2.
  - Historical backfill: chunking, resume-after-crash, rate-limit-aware pacing, gap detection,
    and the exact definition of a gap per exchange calendar (a missing bar on a half-day is
    not a gap).
  - Live streaming: subscribe, heartbeat, detect stall, reconnect with exponential backoff and
    jitter, and backfill the disconnect window before resuming - state how you prove no bar
    was silently lost.
  - Normalisation: provider field -> domain model, timezone conversion, adjusted vs unadjusted
    policy (store raw, adjust at read time, and say why), corporate-action application order,
    and how a split announced mid-backfill is handled.
  - Deduplication and idempotency: natural key per record, upsert semantics, and what happens
    when two providers disagree on the same bar - the reconciliation rule, tolerance, and which
    provider wins.
  - Failure policy: on provider error, RECORD THE FAILURE. Never substitute, never carry
    forward, never interpolate. Define exactly what downstream sees when data is absent.
  - Freshness: staleness thresholds per data type, how staleness is computed with clock skew
    accounted for, and the NTP requirement.
  - Caching in Redis: key naming, TTL per type, invalidation, and the cache-stampede guard.

TESTS REQUIRED: a recorded-fixture replay test per adapter, a gap-detection test across a
half-day and a DST boundary, and a two-provider disagreement test.

DELIVERABLE: docs/specs/SPEC-P2.1-INGEST.md + src/data/ implementation + tests.
```

## P2.2 — Data Validation & Quality Gate

```text
ROLE: Engineer building the layer that decides whether the system is allowed to trade today.

OBJECTIVE: A quality gate that fails closed. Nothing reaches the scanner unvalidated.

VALIDATION LAYERS - specify each with its exact rule and threshold:
  1 Schema: Pydantic validation, unknown fields, type coercion policy (strict, no coercion).
  2 Structural: OHLC ordering (low <= open,close <= high), non-negative volume, non-zero price,
    bar timestamp aligned to the bar grid, no bar outside session hours.
  3 Temporal: monotonic timestamps, no future timestamps, freshness vs the staleness threshold,
    clock-skew tolerance.
  4 Statistical: price jump vs rolling volatility (state the z threshold and window), volume
    spike, zero-volume streaks, flatline detection, stale-quote detection.
  5 Cross-source: agreement tolerance, quorum rule when three sources exist.
  6 Corporate-action awareness: a 50% overnight drop is a split, not an anomaly - specify the
    lookup that distinguishes them and what happens when the corporate-action feed is late.
  7 Coverage: minimum fraction of the universe with valid data required before the pipeline
    may run at all. Below it, the whole run aborts.

OUTPUT PER RECORD: a quality score and a decision (ACCEPT / QUARANTINE / REJECT), with the
rule id that fired. Quarantined data is stored, never silently dropped.

ALSO: the daily data-quality report, the alert thresholds, and the manual override procedure
(who, how, logged where).

DELIVERABLE: docs/specs/SPEC-P2.2-VALIDATION.md + implementation + a property-based test suite.
```

## P2.3 — Universe & Scanner (Tier 1)

```text
ROLE: Quant engineer building Tier 1 screening.

OBJECTIVE: Take the full listed universe down to 50-200 candidates, deterministically,
with no LLM and no ML.

SPECIFY EXACTLY:
  - Universe construction: source of listings per exchange, inclusion rules, exclusion rules
    (ETFs, ADRs, SPACs, REITs, trusts, recently IPOd - state the minimum listing age, penny
    stocks, stocks under a trading halt, stocks on a surveillance/ASM/GSM list in India,
    hard-to-borrow if shorting).
  - Point-in-time universe: the universe as of a past date must exclude anything not listed
    then and include everything since delisted. State how this is stored and queried.
  - Each filter with its precise definition:
      market cap: shares outstanding source, which share class, when it was last updated,
        cap computed with which price, FX conversion for India
      ADDV: window length, currency, median or mean, handling of low-volume days and halts
      price floor: which price, adjusted or raw, at which timestamp
      momentum: exact lookback, calendar or trading days, total or price return,
        skip-a-month convention or not, and the reason
      value: P/B using which book value vintage, sector median computed over which set,
        handling of negative book value
      volatility: estimator (close-to-close, Parkinson, Garman-Klass), window, annualisation,
        the market-average benchmark and its window
  - Filter ORDER and short-circuiting, since order changes both cost and the result set.
  - Sector classification source, granularity, and the fallback when a symbol is unclassified.
  - Determinism: same inputs must yield the same ordered candidate list. State the tie-break.
  - Output: ranked candidates with every filter value that produced the ranking, written to
    the audit trail.

ALSO: a diagnostic mode reporting how many symbols each filter removed and why, so the funnel
can be tuned without guessing.

DELIVERABLE: docs/specs/SPEC-P2.3-SCANNER.md + implementation + a golden-file test against a
frozen historical date.
```

## P2.4 — Feature Engineering

```text
ROLE: Quant researcher building the feature store.

OBJECTIVE: Every feature used by any model, defined once, computed identically in backtest
and in live. Training/serving skew is the enemy here.

FOR EACH FEATURE give: name, formula, inputs, lookback, units, expected range, treatment of
NaN, treatment of insufficient history, winsorisation, normalisation, and its point-in-time
availability lag (when was this value actually knowable).

FEATURE FAMILIES:
  - Fundamental: profitability, growth, leverage, quality, valuation ratios. Specify the
    reporting-lag rule per market (US 10-Q filing lag, India quarterly results lag), the
    as-reported vs restated rule, TTM construction, fiscal-year alignment across companies,
    and currency handling.
  - Sector normalisation: z-score within GICS sector at which level, minimum sector member
    count, what happens below it, outlier clipping, and the cross-sectional vs time-series
    normalisation choice with justification.
  - Technical: ATR(14), VWAP (session or rolling, and which), ADX, volume ratios, SMA set.
    Give the exact recursive formulations (Wilder smoothing, not naive), the seeding rule for
    the first N bars, and behaviour across gaps and halts.
  - Market/regime inputs: index returns, breadth, VIX/India VIX, term spread, credit spread.

MANDATORY:
  - One implementation used by both backtest and live. State the mechanism that enforces this
    and the test that fails if they diverge.
  - Leakage audit: for each feature, prove no future information enters. List the ones that
    are most at risk and how they are guarded.
  - A feature-drift monitor definition.

DELIVERABLE: docs/specs/SPEC-P2.4-FEATURES.md + implementation + a backtest-vs-live parity test.
```

## P2.5 — Fundamental & Technical Scoring Agents

```text
ROLE: ML engineer building the Tier 2 quantitative scorers.

OBJECTIVE: Turn features into scores, with models that are honest about their uncertainty.

SPECIFY:
  - Target definition. This is the most important paragraph in the document: what exactly is
    being predicted, over what horizon, in what units, relative to what benchmark, with what
    labelling of the ambiguous middle. Justify it against the holding period from P0.1.
  - Data splitting that respects time: purged and embargoed cross-validation with the embargo
    length derived from the label horizon. Explain why naive k-fold is invalid here.
  - Model: XGBoost/LightGBM config, hyperparameter search space, the search protocol, the
    number of trials, and how multiple-testing inflation is controlled.
  - Class imbalance, sample weighting, and whether recent data is upweighted.
  - Calibration: how raw model output becomes a usable score, and how it is calibrated so a
    score of 80 means something stable over time.
  - Feature importance, SHAP reporting, and the rule that any feature we cannot explain
    economically gets dropped.
  - Score combination: 60% fundamental + 20% technical + 10% sentiment sums to 90 - resolve
    this. State the full weighting, the missing 10%, the normalisation of each component to a
    common scale, and what happens when one component is unavailable.
  - The no-model fallback: pure rules path used when a model is unavailable or stale.
  - Model registry entry: version, training window, hyperparameters, metrics, data hash,
    approval, and the expiry date after which the model refuses to serve.

DELIVERABLE: docs/specs/SPEC-P2.5-SCORING.md + training pipeline + inference code + a test
that a stale or unregistered model cannot serve predictions.
```

## P2.6 — Regime Detection

```text
ROLE: Quant building the market-regime classifier.

OBJECTIVE: A small number of clearly defined regimes and the exact way they change behaviour.

SPECIFY:
  - The regime taxonomy (recommend 3-5), each defined by measurable conditions, not vibes.
  - Method: HMM plus deterministic rules. Give the observation vector, the number of states,
    the fitting window, the refit cadence, and the state-labelling procedure that keeps state
    identities stable across refits (label switching is a real failure mode - handle it).
  - Hysteresis: minimum dwell time and confirmation window so the regime does not flip daily.
    State the exact rule and show its effect on turnover.
  - Per-market regimes vs one global regime, and how a conflict is resolved.
  - The behavioural consequence table: for each regime, what changes - gross exposure cap,
    max position size, minimum score threshold, gate width, stop multiplier, whether new
    entries are allowed at all. Every number stated.
  - Regime transition events into the audit log, plus an alert on transition.
  - Failure mode: what runs when the regime model is unavailable. Default to the most
    conservative regime.

DELIVERABLE: docs/specs/SPEC-P2.6-REGIME.md + implementation + a historical labelling review
across 2008, 2015, 2018, 2020, 2022 with the labels it produces.
```

## P2.7 — Decision Engine

```text
ROLE: Engineer building the component that emits BUY/HOLD/SELL/NO_TRADE.

OBJECTIVE: A deterministic synthesiser of all signals, with LLM input treated as one bounded,
capped, optional input among several.

SPECIFY:
  - The exact scoring formula with every weight, and the regime adjustment applied to it.
  - The confidence score: how 0-100 is computed, what it means operationally, and the proof
    that it is monotonic in the inputs. If it is not calibrated, say so and forbid using it
    for sizing.
  - Thresholds: score and confidence required for BUY, for SELL, for HOLD, and the
    deliberately wide NO_TRADE band. State the hysteresis that prevents flip-flopping between
    adjacent runs, and the minimum holding period before a reversal is permitted.
  - LLM contribution cap: the maximum share of the final score the LLM path can influence, and
    what the decision looks like when the LLM path is skipped or failed. The system must
    produce a valid decision with zero LLM input.
  - Conflict rules: quant says BUY, sentiment says SELL, regime is risk-off. Enumerate the
    combinations in a truth table and give the output for each. No implicit precedence.
  - Every decision emits a machine-readable reason: the rule ids and input values that
    produced it, sufficient to reconstruct the decision without the model.
  - NO_TRADE is the default. Any path that fails to produce a confident decision returns
    NO_TRADE, not HOLD.
  - Idempotency: the same run over the same inputs must not emit duplicate decisions.

DELIVERABLE: docs/specs/SPEC-P2.7-DECISION.md + implementation + a truth-table test covering
every enumerated combination.
```

## P2.8 — Position Sizing & Portfolio Construction

```text
ROLE: Portfolio engineer.

OBJECTIVE: Turn approved decisions into target quantities that respect every constraint
simultaneously.

SPECIFY:
  - The sizing formula from the research summary, fully expanded: risk_per_trade x NAV divided
    by (volatility estimate x price), capped by max position pct, capped by liquidity, capped
    by remaining sector headroom, capped by remaining cash. State the order of the caps, the
    rounding to lot/tick, and the minimum viable size below which the trade is dropped
    entirely rather than sent tiny.
  - Which volatility estimate, which window, and how a stock with insufficient history is
    handled (it is excluded, not defaulted).
  - Portfolio-level construction: simultaneous constraint satisfaction when N candidates each
    pass individually but collectively breach sector or gross limits. Give the allocation
    algorithm, its objective, and its tie-break. Prefer a deterministic greedy rule over an
    optimiser unless you can justify the optimiser.
  - Existing positions: rebalance rule, drift tolerance band, the minimum trade size that
    justifies transaction costs, and how an existing position that has grown past its cap is
    treated (trim now or on next rebalance).
  - Cash management: reserve buffer, settlement timing (T+1 US, T+1 India), unsettled funds,
    and the rule preventing a good-faith violation.
  - Currency: FX rate source and timing for the India sleeve, and how FX moves affect limits.
  - Output: a target portfolio and a diff against the current portfolio, expressed as order
    intents, with every intent carrying the constraint values that shaped it.

DELIVERABLE: docs/specs/SPEC-P2.8-SIZING.md + implementation + tests including the case where
all candidates want the same sector.
```

## P2.9 — Risk Engine (deterministic, the crown jewel)

```text
ROLE: Engineer building the component that says no. Assume the AI upstream is compromised.

OBJECTIVE: A deterministic policy gate that every order intent must pass. It must be readable
by a regulator, testable exhaustively, and impossible to bypass.

NON-NEGOTIABLE PROPERTIES - address each explicitly:
  - Zero AI. No model, no LLM, no learned threshold, no randomness anywhere in this component.
  - Fail-closed: any exception, missing input, stale input, or unreachable dependency -> DENY.
    Prove there is no code path that returns ALLOW on an error.
  - Total: every intent gets a verdict. No path returns None or falls through.
  - Pure: the evaluator is a pure function of (intent, portfolio state, market state, policy).
    No I/O inside the evaluator. State how state is snapshotted before evaluation.
  - Unbypassable: state the architectural mechanism preventing any caller from reaching the
    broker without a verdict - single choke point, a signed verdict token, a test that fails
    if a new call path appears.

SPECIFY PER RULE (all of them, by id):
  - Exact measurement: numerator, denominator, price used, timestamp used, before or after the
    hypothetical fill, and whether existing pending orders count toward the exposure.
  - Window definition with timezone and boundary handling.
  - Verdict and, for MODIFY, the exact reduced quantity formula.
  - What it does when its input is unavailable.

ALSO SPECIFY:
  - Evaluation order and short-circuiting, and why the order cannot change the outcome
    (or, if it can, the fixed order and its justification).
  - Aggregation of multiple verdicts into one final verdict, with the precedence lattice
    KILL > DENY > MODIFY > ALLOW proven to be well-defined.
  - The pre-trade vs continuous distinction: which rules run per intent and which run on a
    timer against the whole portfolio.
  - Idempotency and concurrency: two intents evaluated in parallel must not both consume the
    same headroom. Specify the locking or serialisation, and its throughput ceiling.
  - Every evaluation written to risk_evaluations and the audit log, including the ALLOWs.
  - Monitor mode: how a rule can run in shadow to measure impact before enforcement.

TESTING REQUIREMENT: exhaustive boundary tests (at, just under, just over every threshold),
property-based tests asserting fail-closed under arbitrary malformed input, and a fuzz suite.
Include the actual tests.

DELIVERABLE: docs/specs/SPEC-P2.9-RISK-ENGINE.md + implementation + the full test suite.
```

## P2.10 — Kill Switch

```text
ROLE: Engineer building the last line of defence. It must work when everything else is broken.

OBJECTIVE: An infrastructure-level halt that is independent of the trading application.

SPECIFY:
  - Independence: the kill switch must be able to trip when the main process is hung, looping,
    or out of memory. State the architecture that achieves this - separate process, separate
    supervisor, watchdog, hardware-level or broker-level control - and what it depends on.
  - The state model: ARMED / TRIPPED / RESETTING / DISABLED, the transition table, and where
    the state lives so it survives a process restart and a database outage. State the source
    of truth and the tie-break when two stores disagree (the safe answer wins).
  - Each automatic trigger with its exact measurement, window, evaluation frequency, and
    debounce: drawdown > 10% from peak (peak measured how, since when, marked at what price),
    daily loss > 2%, weekly loss > 5%, volatility spike > 3 sigma (of what, over what window),
    API failure > 5 consecutive retries (per provider or global), agent loop > 10 iterations
    (counted how), data-quality breach, unexpected position discovered, position-vs-broker
    reconciliation mismatch, NAV computation failure.
  - The manual trigger: a channel completely separate from the AI path, reachable when the app
    is down, with authentication, and its own audit record.
  - The trip sequence, ordered, with what happens if a step fails mid-way: cancel open orders
    (and what if cancel fails), flatten positions or hold (configurable, state the default and
    the reasoning for each market), block new intents, alert humans on multiple channels,
    write the incident record.
  - Re-enablement: human-only, two-person, with a checklist, a written cause, and a mandatory
    cooling period. No automatic reset ever.
  - Startup safety: on boot the system assumes TRIPPED until it positively verifies otherwise,
    including reconciling positions against the broker.
  - The regular self-test: how we prove the kill switch still works, on what cadence, in
    production, without disrupting trading.

DELIVERABLE: docs/specs/SPEC-P2.10-KILLSWITCH.md + implementation + a chaos test that trips it
while orders are in flight and asserts the end state is safe.
```

---
---

# STAGE 3 — EXECUTE

## P3.1 — Broker Abstraction

```text
ROLE: Integration engineer.

OBJECTIVE: One interface, two very different brokers, no leaking abstractions.

SPECIFY:
  - The Broker protocol: submit, cancel, replace, get_order, list_orders, get_positions,
    get_account, stream_updates. Full typed signatures with error unions, not exceptions
    for control flow.
  - The capability model: brokers differ (fractional shares, order types, TIF, amend support,
    GTC lifetime, bracket orders). Define a capability descriptor and require the caller to
    check it. Never silently emulate a missing capability.
  - Per-broker adapter notes: Alpaca and Zerodha Kite specifics from P0.2, including the
    Zerodha daily-token problem and exactly how the system behaves when the token is invalid
    at 09:14 (answer: it does not trade, and it pages a human).
  - Error taxonomy: transient vs permanent vs ambiguous. The ambiguous case - a timeout on
    submit - is the dangerous one. Specify the resolution protocol: never blind-retry, always
    reconcile by client_order_id first.
  - Idempotency: client order id format, generation, uniqueness guarantee, persistence before
    send, and reuse rules.
  - Rate limiting: a client-side limiter tuned below the documented limit, per broker, with
    a queue and a drop policy for stale intents.
  - Paper vs live: one code path, a single flag, and a test that a live credential cannot be
    loaded in paper mode or vice versa.
  - A simulated broker adapter used by tests and the backtester, implementing the same protocol
    including realistic partial fills and rejections.

DELIVERABLE: docs/specs/SPEC-P3.1-BROKER.md + adapters + the simulator + a conformance test
suite that every adapter must pass.
```

## P3.2 — Execution Engine

```text
ROLE: Engineer owning the order lifecycle.

OBJECTIVE: Turn approved intents into fills, safely, with exactly-once semantics as the goal
and at-least-once with reconciliation as the reality.

SPECIFY:
  - The order state machine, complete: NEW, VALIDATED, SENT, ACKED, PARTIALLY_FILLED, FILLED,
    CANCEL_PENDING, CANCELLED, REJECTED, EXPIRED, UNKNOWN. Include UNKNOWN and the procedure
    that resolves it.
  - Pre-send validation: risk verdict token present and valid, kill switch armed and not
    tripped, market open per calendar, symbol tradable, price sane vs last trade, quantity
    within broker limits, duplicate check.
  - Limit price policy: how the limit is derived (offset from mid, from last, from a reference
    price), the maximum allowed slippage from the reference, and the repricing ladder if
    unfilled: how many times, how far, with what delay, and the hard give-up rule.
  - Partial fills: when to leave the remainder working, when to cancel it, how the position
    and the risk headroom are updated after each partial, and how a partial fill affects the
    stop that was sized for the full position.
  - Time in force per use case, end-of-day handling, and what happens to working orders across
    a session boundary or a halt.
  - Emergency exit path: the only place market orders are permitted, with its own guard rails
    and its own audit event type.
  - Reconciliation: on every startup and on a timer, compare our positions and open orders to
    the broker. Define the diff procedure, the tolerance (zero), and the action on mismatch
    (halt and page a human, never auto-correct by trading).
  - Crash safety: a persisted intent journal written before send, with recovery on restart
    that resolves every in-flight intent by querying the broker, never by re-sending.

DELIVERABLE: docs/specs/SPEC-P3.2-EXECUTION.md + implementation + tests that kill the process
between the journal write and the send, and assert no duplicate order results.
```

## P3.3 — Position Monitor

```text
ROLE: Engineer building continuous oversight of open positions.

OBJECTIVE: Know the true state of the portfolio at all times and detect deterioration early.

SPECIFY:
  - The monitoring loop: cadence per check (some are per tick, some per minute, some per day),
    what happens when a cycle overruns, and how backpressure is handled.
  - Per position: mark price source and fallback, unrealised P&L, holding period, distance to
    stop, distance to target, current ATR vs entry ATR, thesis-invalidation checks, upcoming
    earnings date, corporate actions pending, liquidity deterioration.
  - Portfolio level: NAV, gross and net exposure, sector exposure, concentration, realised and
    unrealised daily P&L, drawdown from peak, correlation clustering.
  - Stop management: trailing stop update rule (moves up, never down - state the exact update
    condition and cadence), whether stops are held locally or resting at the broker, and the
    behaviour if the connection drops while a local stop is armed.
  - Thesis invalidation: the machine-checkable form of an invalidation condition from P4.3,
    evaluated deterministically here. An LLM never evaluates its own invalidation.
  - Anomaly detection: position appears that we did not open, quantity mismatch, price feed
    disagrees with broker, NAV moves impossibly - each with its threshold and its escalation.
  - Alerting thresholds and the escalation ladder, including a check that alerts themselves
    are alive (dead-man switch).

DELIVERABLE: docs/specs/SPEC-P3.3-MONITOR.md + implementation + tests for the trailing-stop
ratchet and for the disconnected-stop case.
```

## P3.4 — Exit Engine

```text
ROLE: Engineer building sell-side logic.

OBJECTIVE: The exit hierarchy, made precise and deterministic.

SPECIFY EACH TIER with trigger, evaluation cadence, order type, size, and priority:
  - EMERGENCY (sell all): stop-loss hit, risk limit breach, kill switch. Define exactly what
    "stop hit" means - trade through the level, close through it, or quote through it - and
    handle gaps below the stop, halts, and limit-down.
  - HIGH (sell all): thesis invalidated, earnings miss beyond threshold, fraud or delisting
    event, liquidity collapse.
  - MEDIUM (partial): valuation extended, technical breakdown, time stop reached, score decay.
  - LOW (partial or hold): rebalancing, opportunity cost, tax-aware deferral.

ALSO:
  - Conflict resolution when two tiers fire simultaneously, and the rule that the most urgent
    always wins with no averaging.
  - Partial-exit sizing: what fraction, on what basis, and the minimum residual below which the
    position is closed entirely rather than left as a stub.
  - Re-entry lockout after an exit, per reason, so the system does not immediately buy back.
  - Wash-sale awareness (US) and STCG/LTCG holding-period awareness (India): the exit engine
    surfaces the tax consequence in the audit record. It does not override risk for tax.
  - The end-of-day and end-of-week forced-review procedure.

DELIVERABLE: docs/specs/SPEC-P3.4-EXIT.md + implementation + tests for gap-through-stop,
halted-at-stop, and simultaneous multi-tier triggers.
```

---
---

# STAGE 4 — INTELLIGENCE (gated LLM)

## P4.1 — Untrusted Content Pipeline

```text
ROLE: Security engineer. Assume every news article is written by an attacker who knows your
system prompt.

OBJECTIVE: A sanitisation pipeline such that no external text can ever act as an instruction.

SPECIFY:
  - The threat model: prompt injection via news body, headline, ticker field, company name,
    SEC filing text, social posts, tool responses, and previously stored records (memory
    poisoning). Enumerate each vector with a concrete example payload.
  - The extraction stage: HTML stripping, script and comment removal, invisible-character
    removal (zero-width, bidi overrides, homoglyphs), unicode normalisation form and why,
    length caps, and encoding validation.
  - The structural defence: external text is never concatenated into a prompt. It is passed
    only inside a delimited, typed data envelope with an explicit origin tag, and the system
    prompt states that content inside the envelope is data and may contain hostile text.
    Show the exact envelope format.
  - The detection stage: pattern and heuristic detectors for instruction-like content, with
    the rule that detection is defence in depth and never the primary control.
  - Provenance: every fragment carries source, url, publisher, retrieved_at, and a trust tier.
    Untrusted tiers cannot influence a decision beyond a capped weight.
  - Deduplication of syndicated news so one story does not look like twenty confirmations.
  - The stored-content risk: sanitised content persisted today is untrusted forever. State the
    re-validation rule on read.
  - The test corpus: a set of adversarial fixtures, including the classic injections and
    finance-specific ones (fake press release, spoofed filing, coordinated social pump).

DELIVERABLE: docs/specs/SPEC-P4.1-SANITISER.md + implementation + the adversarial corpus and
a test that asserts every payload fails to change the pipeline output.
```

## P4.2 — Inference Gate

```text
ROLE: Engineer controlling when money is spent on LLM tokens.

OBJECTIVE: A deterministic gate deciding whether the LLM path runs at all.

SPECIFY:
  - The gate conditions, exactly: top-N by quantitative score (N per the budget from P0.3),
    OR a statistically anomalous condition (define each anomaly with its statistic, window,
    and threshold), OR an open position whose thesis needs re-validation on a defined cadence.
  - Hard budget enforcement: per-run, per-day, and per-month token and dollar caps, with the
    behaviour on exhaustion (the gate closes, the pipeline continues without LLM input, an
    alert fires). Never degrade silently.
  - Caching and deduplication: identical inputs must not be paid for twice. Define the cache
    key (content hash plus prompt version plus model version), the TTL, and the invalidation.
  - Cost accounting per call written to llm_calls: tokens in, tokens out, model, latency,
    dollar cost, cache hit or miss, and the decision it fed.
  - Rate limiting and concurrency caps, and the loop guard: a hard maximum number of LLM calls
    per run_id that trips the kill switch when exceeded (this is the agent-loop trigger).
  - The gate is deterministic and auditable: given the same inputs, the same candidates are
    gated in. Log the gate decision and the reason for every candidate, including the ones
    excluded.

DELIVERABLE: docs/specs/SPEC-P4.2-GATE.md + implementation + a test proving the monthly cap
is honoured under concurrency.
```

## P4.3 — Research Agent (LLM)

```text
ROLE: Engineer building the only LLM-facing component in the system.

OBJECTIVE: Structured research output that is useful, bounded, and impossible to trust blindly.

SPECIFY:
  - The exact task list: news synthesis, filing summarisation, earnings-call reading, thesis
    generation with bull and bear cases, risk-factor identification, and machine-checkable
    invalidation conditions. Nothing else. The LLM does not produce numbers that feed a
    calculation.
  - The output schema (Pydantic), strict, with every field constrained: enums where possible,
    bounded lengths, required citations referencing fragment ids from P4.1, and a confidence
    that is explicitly documented as uncalibrated and forbidden from sizing.
  - INVALIDATION CONDITIONS ARE THE CRITICAL OUTPUT. Each must be expressed in a restricted,
    machine-evaluable grammar over known metrics (price, score, fundamental field, event type,
    date), not free text. Give the grammar, its parser, and its evaluator. Free-text conditions
    are rejected at validation.
  - The prompt: full text, versioned, with the system prompt stating that all user-content is
    untrusted data. Include the numeric-hallucination guard - the model is given the numbers
    and is forbidden to restate any number not present in its input, verified programmatically.
  - Model parameters: temperature, top_p, max tokens, seed, stop sequences, and the reason
    for each. Deterministic where the provider allows it.
  - Fallback chain: DeepSeek fails -> GPT-4o-mini -> no LLM output at all. Each downgrade is
    logged and reduces the LLM weight in the decision.
  - Timeout, retry budget, and the rule that a retry never doubles a side effect (there are
    none here, which is why the LLM is confined to this component - state that explicitly).
  - Prompt and response are stored verbatim in the audit trail.

DELIVERABLE: docs/specs/SPEC-P4.3-RESEARCH.md + implementation + the prompt file + the
invalidation-grammar parser + tests including a hallucinated-number rejection test.
```

## P4.4 — LLM Output Validation

```text
ROLE: Engineer who assumes the LLM output is wrong.

OBJECTIVE: A validation layer between the research agent and the decision engine that can
reject output entirely.

SPECIFY THE CHECKS, in order, each with its rejection action:
  1 Schema validation, strict, no coercion.
  2 Citation validation: every claim references a fragment id that exists in the input, and
    the fragment actually supports it (state how far this can be checked mechanically).
  3 Numeric validation: every number in the output must appear in the input, or be derivable
    by a whitelisted operation from input numbers, within a tolerance. Otherwise reject.
  4 Consistency: bull and bear cases must not be identical, must not contradict the quantitative
    score beyond a stated tolerance without an explanation field, and must reference the same
    entity that was requested.
  5 Entity validation: the output is about the requested instrument and no other.
  6 Grammar validation of invalidation conditions, plus a dry-run evaluation proving each one
    can actually be evaluated against live data today.
  7 Injection residue: output containing instruction-like text is rejected and the incident is
    logged as a security event.
  8 Sanity bounds: confidence in range, no empty required fields, no boilerplate refusal text.

ALSO: the rejection policy - reject once and retry with a stricter prompt at most N times, then
fall through to no-LLM. Log every rejection with its reason code for later prompt improvement.
Track the rejection rate as a monitored metric; a rising rate is an incident.

DELIVERABLE: docs/specs/SPEC-P4.4-LLM-VALIDATION.md + implementation + a fixture suite of
malformed, hallucinated, and hostile outputs that must all be rejected.
```

---
---

# STAGE 5 — VALIDATE

## P5.1 — Backtest Engine

```text
ROLE: Engineer building the simulator. Its only job is to not lie.

OBJECTIVE: An event-driven backtester that runs the identical production decision code.

SPECIFY:
  - Architecture: event-driven, not vectorised, and the reason. The exact event loop, the
    clock, and how the same agent code is driven by simulated time.
  - CODE REUSE IS MANDATORY: the scanner, features, scorers, decision engine, sizing, risk
    engine, and exit engine are the production classes, not reimplementations. State the
    seam - a Clock, a DataSource, and a Broker are injected. List every place production code
    would otherwise call wall-clock time, a random number, or the network, and how each is
    intercepted. Add a test that fails if production code reads the wall clock directly.
  - Look-ahead prevention, structurally enforced: the data source physically cannot return a
    record whose knowledge_time is after the simulated clock. Show the mechanism and the test.
  - Point-in-time universe, delisted symbols, and survivorship-bias handling.
  - Corporate actions applied at the right time with the right cash effects, including
    dividends, splits, spin-offs, mergers, and rights issues, plus the tax withholding rule.
  - Order simulation: fill model for limit and market orders, queue position assumption,
    partial fills, the rule for whether a limit at the touch fills, gaps, halts, limit-up/down,
    and the explicit statement of every optimistic assumption made.
  - Cash, margin, settlement timing, interest on cash, and borrow cost for shorts.
  - Determinism: same inputs, same seed, byte-identical output. State how, and add a test.
  - The output artefact: a full trade ledger, an equity curve, per-decision records identical
    in shape to production audit events, so backtest and live can be compared directly.

DELIVERABLE: docs/specs/SPEC-P5.1-BACKTEST.md + implementation + a determinism test + a
known-answer test on a hand-computed 20-bar scenario.
```

## P5.2 — Walk-Forward Validation

```text
ROLE: Quant researcher responsible for not fooling yourself.

OBJECTIVE: The full walk-forward protocol and its statistics.

SPECIFY:
  - Window design: in-sample length, out-of-sample length, step, anchored or rolling, and the
    resulting number of independent test periods. Justify every choice against the label
    horizon and the amount of data available.
  - Purging and embargo between IS and OOS, sized from the label horizon plus the feature
    lookback. Show why the naive split leaks.
  - What is re-fit in each window and what is frozen. Anything tuned by looking at OOS results
    is contaminated - state the discipline that prevents it, including how many times a human
    is allowed to look.
  - Multiple-testing correction: deflated Sharpe ratio or an equivalent, with the number of
    trials actually run recorded honestly. Specify how trials are counted.
  - The metrics, defined precisely: Sharpe, Sortino, Calmar with their risk-free rate,
    annualisation factor, and return frequency; max drawdown and its duration; win rate;
    profit factor; turnover; capacity.
  - Regime slicing: performance broken out by regime and by year, with the rule that a strategy
    profitable only in one regime is rejected.
  - Monte Carlo: trade-order shuffling, bootstrap of returns, and parameter perturbation, each
    with what it tests and the pass threshold.
  - The pass/fail gate: Sharpe > 1.0, max DD < 15%, OOS > 70% of IS, plus the additional
    criteria you judge necessary. State what happens when a strategy fails - it is not tweaked
    and re-run; specify the cooling-off and the documentation required.

DELIVERABLE: docs/specs/SPEC-P5.2-WALKFORWARD.md + the runner + the report template.
```

## P5.3 — Transaction Cost & Slippage Model

```text
ROLE: Execution researcher.

OBJECTIVE: A cost model pessimistic enough that live results are a pleasant surprise.

SPECIFY, per market and per broker:
  - Explicit costs: commission schedule, exchange fees, SEBI turnover fees, STT, stamp duty,
    GST, SEC and FINRA TAF fees, clearing charges, DP charges, and the exact formula for each
    including rounding and minimums.
  - Implicit costs: half-spread as a function of price and liquidity tier, market impact as a
    function of participation rate (state the model and its coefficients, and label them
    ASSUMPTION if unfitted), delay cost, and opportunity cost of unfilled orders.
  - Borrow cost and hard-to-borrow handling if shorting is in scope.
  - FX conversion cost for the India sleeve.
  - Calibration: how these are fitted to real fills once paper trading starts, and the
    feedback loop into the backtester.
  - A sensitivity analysis showing strategy performance at 1x, 2x, and 3x the modelled cost.
    A strategy that dies at 2x is not deployable.

DELIVERABLE: docs/specs/SPEC-P5.3-COSTS.md + implementation + the sensitivity table.
```

## P5.4 — Test Strategy

```text
ROLE: Test architect for a system where a bug costs money.

OBJECTIVE: The complete testing pyramid, with the specific tests this system needs.

SPECIFY:
  - Unit tests: what must be covered, and the coverage floor per module with risk engine,
    kill switch, execution, and sizing held to a higher bar than the rest. State the numbers.
  - Property-based tests (Hypothesis): the invariants to assert. At minimum - the risk engine
    never returns ALLOW on malformed input; position sizing never exceeds any cap for any
    input; the audit chain always verifies after any sequence of appends; the order state
    machine never reaches an illegal state; money arithmetic never loses a cent.
  - Golden-file tests: frozen historical dates through the whole pipeline, with the output
    committed and diffed. Define the update procedure so a golden file cannot be updated
    casually.
  - Integration tests against provider sandboxes and recorded fixtures, and the rule about
    which tests may touch the network.
  - Contract tests: every broker adapter passes the same conformance suite.
  - Replay tests: take a recorded production run and re-derive it, asserting bit-identical
    decisions.
  - Chaos and failure-injection: provider outage mid-run, database unavailable, Redis flush,
    clock jump, duplicate fill, out-of-order fill, unknown position, network partition during
    submit, process kill at every step of the execution journal.
  - Backtest-vs-live parity test as a first-class, always-running check.
  - What must never be mocked: the risk engine and the audit chain are always real in tests.
  - CI gating: which suites block a merge, which run nightly, and the flake policy.

DELIVERABLE: docs/specs/SPEC-P5.4-TESTING.md + the conftest and fixtures + the first suite.
```

## P5.5 — Chaos, Reconciliation & Recovery Drills

```text
ROLE: SRE for a trading system.

OBJECTIVE: Written, rehearsed procedures for the bad days.

SPECIFY:
  - The reconciliation procedure: positions, orders, cash, and NAV against the broker, on
    startup, on a timer, and at end of day. The tolerance is zero. Define the diff, the
    classification of each mismatch type, and the action for each - always halt-and-page, never
    auto-trade to fix.
  - Recovery scenarios, each written as a runbook with steps, decision points, and the
    expected end state: process crash with open orders, broker outage with open positions,
    data provider outage mid-session, database corruption, Redis loss, kill switch tripped at
    09:31, discovered position we never opened, duplicate fill, fill for an order we cancelled,
    stale NAV, and a bad deploy discovered mid-session.
  - The drill schedule: which drills are run, how often, in which environment, and the
    requirement that a drill that has never been run does not count as a procedure.
  - RPO and RTO per component from P0.1, with the measured actual, not the aspirational.
  - The incident record format and the post-incident review requirement.

DELIVERABLE: docs/specs/SPEC-P5.5-CHAOS.md + the runbooks + automated drill scripts where
possible.
```

---
---

# STAGE 6 — OPERATE

## P6.1 — Observability

```text
ROLE: Engineer instrumenting the system.

OBJECTIVE: Metrics, logs, traces, and dashboards that answer "is it behaving?" in ten seconds.

SPECIFY:
  - The full metric catalogue: name, type, labels, cardinality estimate, and the question it
    answers. Cover pipeline stage latency and success rate, data freshness and quality, funnel
    counts per stage, gate rate, LLM cost and rejection rate, decision distribution, risk
    verdict distribution by rule id, order latency, fill rate, slippage vs model, position and
    exposure gauges, P&L and drawdown, error rates, and every kill-switch trigger input as a
    live gauge.
  - Structured logging: the JSON schema, the required correlation fields, log levels and what
    belongs at each, and the rule that no secret or PII is ever logged. Include the redaction
    filter.
  - Tracing across the pipeline with the run_id as the trace id.
  - Dashboards: three of them, specified panel by panel - Operations (is it running),
    Trading (what is it doing), Risk (how close are we to the edge). Each panel names the
    query and the threshold that makes it red.
  - Alert rules: expression, for-duration, severity, routing channel, and the runbook link.
    Include the meta-alerts: no decisions produced today, pipeline did not run, alerting
    pipeline itself is down, metrics went stale.
  - The daily operator report: contents, generation time, delivery channel.
  - Alert-fatigue budget: the maximum tolerable number of alerts per week and what happens
    when it is exceeded.

DELIVERABLE: docs/specs/SPEC-P6.1-OBSERVABILITY.md + metric definitions in code + the
Prometheus rules + the Grafana JSON.
```

## P6.2 — Security & Secrets

```text
ROLE: Security engineer performing a design review before go-live.

OBJECTIVE: A complete threat model and the controls that answer it.

SPECIFY:
  - The threat model using STRIDE across every trust boundary, with the trading-specific
    threats named in the research summary: prompt injection, data fabrication, tool-response
    hijacking, state tampering, memory poisoning, and the insider case.
  - Secrets: Vault topology, auth method for the app, lease and renewal, rotation schedule and
    the zero-downtime rotation procedure, per-credential least privilege (data credentials
    cannot trade; trading credentials cannot withdraw), break-glass access, and the audit of
    secret reads. State plainly what happens today if a broker key leaks - the exact minutes-long
    procedure.
  - Network: static IP requirement for India, VPC and security group rules as a table,
    egress allowlist, TLS and certificate pinning where supported, and no inbound except a
    bastion.
  - Application: authentication and authorisation for the API and the manual kill switch,
    the two-person rule for limit changes, input validation at every boundary, and dependency
    supply-chain controls (pinning, hashes, scanning, the update policy).
  - Data: encryption at rest and in transit, backup encryption, and access control on the
    audit tables.
  - Detection: what security events are logged, what alerts fire, and how a compromise would
    actually be noticed.
  - The abuse cases: what an attacker who gets read access can do, write access, and
    code-execution access - and which controls limit the blast radius of each.

DELIVERABLE: docs/specs/SPEC-P6.2-SECURITY.md + the threat model table + the hardening
checklist as a verifiable script.
```

## P6.3 — Compliance

```text
ROLE: Compliance engineer.

OBJECTIVE: Map every regulatory requirement to a concrete, testable control in the code.

SPECIFY, as a requirement-to-control matrix with the test that proves each:
  - SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013: unique strategy ID stamped on
    every order (where it is generated, its format, where it is stored, how it appears to the
    broker), the OPS threshold and how orders per second are counted and enforced client-side
    with a margin, the registration trigger and who owns that decision, broker-hosting
    implications for the deployment, live-like testing evidence, static IP, and 2FA.
  - India specifics: STT, stamp duty, GST, T+1 settlement, ASM/GSM surveillance lists,
    circuit limits and how the system behaves at a circuit, and STCG/LTCG tracking.
  - US specifics: PDT rule (how day trades are counted, the account-equity check before
    the fourth), wash-sale tracking across accounts and substantially identical securities,
    best-execution documentation, Reg SHO locate if shorting, and the account-type limits.
  - The line the system must not cross: trading only the owner account. Specify the technical
    control preventing a second person from being onboarded without a licence, and the exact
    warning surfaced in every report that this is not investment advice.
  - Record retention: what, how long, in what format, and the regulator export procedure.
  - The compliance test suite that runs in CI and fails the build on violation.

DELIVERABLE: docs/specs/SPEC-P6.3-COMPLIANCE.md + the matrix + the enforcement code + tests.
```

## P6.4 — Deployment, CI/CD & Disaster Recovery

```text
ROLE: Platform engineer.

OBJECTIVE: A reproducible, reversible deployment on one VM, plus the plan for when the VM dies.

SPECIFY:
  - Repository and package layout, module boundaries, and the import rules that enforce them
    (a lint rule that fails if execution imports the LLM package, for example).
  - Docker composition: every service, its resource limits, health checks, restart policy,
    dependency ordering, and how the trading process is prevented from starting before its
    dependencies are actually ready (not merely running).
  - Configuration and secret injection at runtime, with no secret in an image layer.
  - CI pipeline: lint, type check (strict), tests by tier, security scan, build, and the exact
    gates that block a merge.
  - Deployment procedure with market hours as a constraint: the deploy window, the pre-deploy
    checklist (flat or not, kill switch state, in-flight orders), the migration procedure for
    a database that must not lose the audit chain, the rollback procedure including a rollback
    that must not lose audit records, and the post-deploy verification.
  - Blue/green or maintenance-window choice, justified for a single VM.
  - Backups: what, how often, tested restore, offsite copy, and the last-restore-test date as
    a monitored metric.
  - Disaster recovery: rebuild-from-scratch runbook with an RTO, the plan for open positions
    during an outage (including the manual broker-UI fallback and who is authorised to use it),
    and a plan for the broker being the thing that is down.

DELIVERABLE: docs/specs/SPEC-P6.4-DEPLOY.md + the compose files + the CI workflow + the
runbooks.
```

## P6.5 — Paper Trading & Go-Live Gates

```text
ROLE: Programme owner for the seven-stage promotion path.

OBJECTIVE: Make each stage an objective, measurable gate that cannot be argued past.

FOR EACH STAGE - backtest, walk-forward, paper, shadow, $1k, $10k, scale-up - specify:
  - Entry criteria: exactly what must be true and evidenced before starting.
  - Duration: minimum calendar time AND minimum number of trades, since both matter.
  - Success metrics with numeric thresholds and the statistical test used, including the
    sample size needed for the result to mean anything (be honest about how few trades a
    3-month paper run produces and what that does to significance).
  - Automatic failure conditions that end the stage immediately.
  - The comparison procedure: paper vs backtest, shadow vs paper, live vs shadow - what is
    compared, what divergence is acceptable, and what a divergence implies about the model.
  - The exit criteria and who signs off.
  - What is deliberately NOT tested at that stage and therefore still unknown.

ALSO: the shadow-mode design - how live decisions are generated and recorded without sending
orders, and how the counterfactual fill is estimated for comparison.

ALSO: the go-live checklist, one page, every item binary and verifiable, ending with the
manual kill-switch test performed that morning.

DELIVERABLE: docs/specs/SPEC-P6.5-GOLIVE.md + the gate-evaluation script that computes each
metric from the audit log and prints PASS or FAIL.
```

## P6.6 — Learning & Model Governance

```text
ROLE: Research lead responsible for improving the system without overfitting it to noise.

OBJECTIVE: A disciplined offline improvement loop. The system never learns online.

SPECIFY:
  - The performance-attribution procedure: decompose P&L into selection, sizing, timing,
    execution, and cost, so the failing component is identified rather than guessed at.
  - The error taxonomy: bad data, bad feature, bad model, bad threshold, bad execution, bad
    luck. Give the diagnostic that distinguishes bad luck from a broken model, with the sample
    size it requires.
  - The prohibition, stated as an enforced control: no change may be triggered by a single
    trade or a single week. State the minimum evidence and the minimum time window.
  - Champion/challenger: how a challenger is created, how it runs (shadow only), the
    comparison metric, the significance test, the minimum observation period, the promotion
    rule, and the automatic demotion rule.
  - Model registry and lifecycle: training data hash, code SHA, hyperparameters, metrics,
    approver, deployment date, expiry, and the refusal-to-serve behaviour when expired.
  - Drift monitoring: feature drift, label drift, and performance decay, each with its
    statistic, threshold, and the response (alert, retrain, or halt).
  - Retraining: cadence, data window, the full re-validation required before promotion, and
    the explicit rule that a retrained model re-enters at the walk-forward gate, not at live.
  - The research log: every experiment recorded, including the failures, so the trial count
    used in the deflated Sharpe calculation is honest.

DELIVERABLE: docs/specs/SPEC-P6.6-LEARNING.md + the registry schema + the attribution report.
```

---
---

# CROSS-CUTTING TEMPLATES

Use these repeatedly, in their own conversations.

## X1 — Code Generation

```text
[Block A] [Block B] [Block C]

ROLE: Implementer.

You are implementing exactly one FROZEN spec. Paste of that spec follows.

RULES:
- Implement the spec, all of it, and nothing beyond it. If the spec is silent on something you
  need, add it to OPEN QUESTIONS and choose the most conservative behaviour.
- If the spec is wrong or unimplementable as written, stop and say so before writing code.
- Python 3.12, full type annotations, mypy strict clean, Pydantic v2, no untyped dicts crossing
  a module boundary.
- Every public function gets a docstring stating preconditions, postconditions, and what it
  raises.
- No TODO, no placeholder, no stub, no "in a real implementation you would".
- Errors: typed exceptions or result unions, never bare except, never a silent pass.
- Every non-trivial branch gets a test in the same drop. Tests are part of the deliverable,
  not a follow-up.
- Include the exact file paths for every file you emit.

OUTPUT ORDER:
  1 A file manifest with a one-line purpose for each file.
  2 The files, complete.
  3 The tests.
  4 The command to run them.
  5 SPEC DEVIATIONS table: anything you implemented differently and why.
  6 The four standard tables from Block B.

SPEC:
<<<paste frozen spec>>>
```

## X2 — Code Review

```text
[Block A]

ROLE: Adversarial reviewer. You did not write this and you do not trust it. Assume it will
run unattended against a live brokerage account.

INPUTS: the frozen spec, and the code drop.

REVIEW IN THIS ORDER and report findings ranked by severity:
  1 SPEC CONFORMANCE: every requirement present, correct, and complete. List requirements
    that are missing, partially implemented, or subtly different.
  2 CONSTITUTION VIOLATIONS: any path where an LLM influences sizing or execution, any path
    that reaches a broker without a risk verdict, any fail-open, any silent default of a
    market value, any risk number read from somewhere other than the policy loader.
  3 CORRECTNESS: off-by-one, boundary conditions at every threshold, float used for money,
    naive datetimes, timezone bugs, DST, rounding, integer division, mutable default arguments,
    shared mutable state.
  4 CONCURRENCY: races on portfolio headroom, double-spend of exposure, TOCTOU between check
    and act, non-atomic read-modify-write, lock ordering, async blocking calls.
  5 FAILURE HANDLING: every exception path, every timeout, every retry, every partial failure.
    Ask "what if this returns None / times out / returns stale data / returns twice" for every
    external call.
  6 RESOURCE AND PERFORMANCE: unbounded memory, N+1 queries, missing index, unbounded retry,
    unbounded queue.
  7 SECURITY: injection, secret in a log, secret in an error message, unvalidated external
    input, unsafe deserialisation.
  8 TESTS: do they actually test the risky paths, or only the happy path? Name the specific
    missing test cases.
  9 SIMPLICITY: what can be deleted. Reinvented stdlib, speculative abstraction, an interface
    with one implementation, config for a constant.

PER FINDING: severity (BLOCKER/HIGH/MEDIUM/LOW), file and line, the concrete failure scenario
with specific inputs, and the minimal fix. No vague concerns - if you cannot state the input
that breaks it, do not report it.

END WITH: a verdict - SHIP / FIX-THEN-SHIP / REJECT - and, if REJECT, the single reason.
```

## X3 — Merge

```text
ROLE: Editor consolidating a stage into the master specification.

INPUTS: the current master spec plus every spec file produced in this stage.

DO:
  1 Merge into one coherent document, preserving spec ids and version headers.
  2 Build a consolidated CONTRACTS table across all specs. Flag every contract that is
    produced by one spec and consumed by another with a mismatched signature.
  3 Detect and list every CONTRADICTION between specs - a number stated two ways, a field
    named two ways, a behaviour defined twice differently. Do not resolve them silently;
    present each with the two sources and a recommended resolution.
  4 Consolidate ASSUMPTIONS across specs, deduplicate, and rank by impact if false.
  5 Consolidate OPEN QUESTIONS and mark which ones now block the next stage.
  6 Produce a coverage matrix: every requirement from master-research-summary.md mapped to the
    spec that covers it, with the gaps listed explicitly.
  7 Bump the master version and set the status of merged specs to FROZEN.

OUTPUT: the merged master spec plus a CHANGES file listing what moved, what conflicted, and
what was resolved.
```

## X4 — Red Team

```text
ROLE: Adversary. Your goal is to make this system lose money or break a regulation. You have
read every spec. Be specific and creative; vague risk is useless.

ATTACK SURFACES:
  1 Market: what market conditions break the strategy? Construct the specific scenario -
    a flash crash, a gap through every stop, a halt at the worst moment, a limit-down day, a
    liquidity vacuum, a correlated sector collapse, a short squeeze. State what the system does
    in each, step by step, citing the spec.
  2 Data: poisoned news, a fake press release, a delayed corporate action, a provider silently
    serving stale prices, two providers disagreeing, a wrong split factor, a symbol reused
    after a delisting.
  3 Model: distribution shift, an overfit feature, a leaked feature nobody caught, calibration
    decay, label noise, a regime the model has never seen.
  4 LLM: the strongest prompt injection you can construct against the P4.1 envelope; numeric
    hallucination that passes the numeric check; an invalidation condition that is technically
    valid but never triggers.
  5 Execution: a duplicate order after a timeout, a fill arriving after a cancel, an
    out-of-order fill, an order acknowledged but never filled, a broker returning a stale
    position.
  6 Operational: a deploy mid-session, a clock skew, an expired token at the open, a full disk,
    the kill switch itself failing.
  7 Financial and legal: an unnoticed PDT violation, a wash sale, an OPS breach, position
    limits exceeded via a corporate action rather than a trade.

FOR EACH: the attack, the exact step where a control should stop it, whether it actually does
(cite the spec), and if not, the minimal control to add.

END WITH: the top 10 residual risks ranked by expected loss, and the single change with the
best risk reduction per unit of work.
```

## X5 — Gap Audit

```text
ROLE: Auditor checking whether this stage is genuinely finished.

INPUTS: the stage specs, the code, the tests, and master-research-summary.md.

PRODUCE:
  1 A requirement coverage matrix: every capability, control, and number in the research
    summary, mapped to spec + code + test. Three columns, three ticks required. Anything with
    fewer than three is a gap.
  2 Silent-gap detection: things that are implied but never specified anywhere - typically
    timezone handling, corporate actions, halts, partial fills, restarts, and the second market.
  3 Contradiction list across all documents.
  4 Assumption ledger sorted by impact, with the ones still unverified flagged as risks.
  5 A readiness verdict for the next stage: GO / GO WITH CONDITIONS / NO GO, with the specific
    conditions.

Be blunt. A green audit that misses a gap is worse than useless here.
```

---
---

# APPENDIX — Working Rules

**Fresh conversation per phase.** Context bleed between phases produces specs that agree with
each other because they were written together, not because they are correct.

**Freeze before you build.** A spec at status DRAFT cannot be implemented. Freezing means:
merged via X3, gap-audited via X5, and the open questions that block it are closed.

**The review is never optional.** Every code drop goes through X2 in a separate conversation.
A BLOCKER finding means the drop does not land.

**Order that actually matters:** P1.4 (audit) before anything that emits events; P2.9 and P2.10
before anything that can reach a broker; P5.1 (backtest) before P5.2; P6.3 (compliance) before
the first live order.

**When a phase output feels thin,** do not accept it. Re-run it with the specific missing
questions appended to Block C. The pack is designed so that depth is requested explicitly.

**Keep a DECISIONS.md at the repo root** — the running list of every ADR and every assumption
that has since been verified or falsified. It is the file that stops the same argument
happening three times.
