---
id: SPEC-P0.3-BUDGET
version: 0.5
status: FROZEN
phase: P0.3 — Cost, Capacity & Latency Budget
depends_on: [SPEC-P0.1-DECISIONS, SPEC-P0.2-PROVIDERS, docs/PROMPT-PACK.md BLOCK-A, docs/PROMPT-PACK.md BLOCK-B, docs/PROMPT-PACK.md BLOCK-C]
produces: [BUDGET-P0.3, VM-SPECIFICATION-P0.3, LATENCY-BUDGET-P0.3, ERROR-PATHS-P0.3, config.budget.*, config.latency.*, config.llm.*, config.storage.*, config.monitor.subscribe_channels, config.backtest.walkforward.roll_months, enum.PipelineStage, enum.BudgetBreachAction, enum.DiskClass, model.StageBudget, model.CostLine, model.VmSpec, model.DiskAlarms, model.StoragePolicy, model.ExitLatencyPolicy, model.LlmCostPolicy, model.BudgetConfig, table.stage_latency_observation, RULE-B1..B12, A-13..A-20]
supersedes: SPEC-P0.3-BUDGET v0.4 (2026-08-25), v0.3, v0.2, v0.1
frozen_by: STAGE-0-FREEZE.md (2026-08-25)
---

# SPEC-P0.3 — Cost, Capacity & Latency Budget

**Phase:** Stage 0 — DECIDE, prompt `P0.3`
**Date:** 2026-08-25
**Owner:** JS — Project Owner, acting as Systems Engineer

**What changed in v0.5 (2026-08-26).** The M-5 retrieval established that the vendor news archive is **not** point-in-time, so new rule **N16** requires news revisions to be stored as new rows rather than overwritten. **The only budget consequence is the news storage line**, and it is immaterial: news is 125 MB of a 9.7 GB compressed decade (1.3%), so even a 3× revision multiplier adds ~250 MB against 4.7× disk headroom. **No VM, latency, LLM or sensitivity figure changes.** The revision rate itself is unmeasured and is carried as **M-12**, not estimated.

**What changed in v0.4.** **AD-5 reversed the LLM primary/fallback ordering**: the primary is
now OpenAI `gpt-5.6-luna` at **$0.00300/call**, not DeepSeek at $0.00231. Every LLM figure in
§5, §7, §8, §9.2 and §14.4 is recomputed on the new primary, and RULE-B8's off-peak constraint
becomes **provider-conditional** because OpenAI does not price by time of day. **Every
conclusion survives**: the $200–500/month ceiling is still unreachable (it now needs 2.12× the
universe rather than 2.75×), gate width is still cost-irrelevant, and RULE-B7's four boundary
cases still land on the same side. **AD-2 closes Q-9**: `walkforward_roll_months = 3` is
decided, no longer pending. No storage, latency or VM figure changed.

**What changed in v0.3.** v0.2 was authored before Block C (Clarifier Rule) was supplied and
failed its depth requirement: twelve binding rules shipped as bare statements with no edge
case. Writing the edge cases out found **eight defects in the rules themselves** — B2 measured
compression before its own policy had compressed anything; B7's “full-history” was undefined
and trivially evadable by replaying 2,519 of 2,520 sessions; B8 checked only a job's start
time, so a replay could run into peak pricing and silently pay double; B9 left window,
timezone, basis and scope undefined, and would have been pinned on by any approved replay;
B12 never defined “completed bar” and would have raised a false CRITICAL on every trading
halt; and `warn_pct` used integer percent where P0.1 uses fractions. All are fixed and marked
**FIXED IN v0.3** in §15. §15.1 resolves every threshold in this document for timezone,
rounding, window boundary, DST, half-days, percentage unit and bound inclusivity. Blocking
question B10 is new. **No cost, storage, latency or sizing figure changed.**

**What changed in v0.2.** v0.1 was authored before Block B (Output Contract) was supplied and
missed five of its rules. v0.2 adds **§13**, the enumeration of all 40 error paths with their
fail-closed behaviour; adds **per-field specification tables** (name, type, unit, timezone,
nullability, valid range, violation meaning) for every model and for the DDL; promotes the
configuration namespace from a prose key table to **seven Pydantic v2 models** with validators that
make decisions 8, 12, 16 and 17 unrepresentable when violated; restructures CONTRACTS EXPORTED into
Block B's mandated four-column shape; drops the numbering from the four mandated headings; and
removes v0.1's one literal ellipsis. **No figure, decision or finding from v0.1 changed** — the
arithmetic was re-verified unchanged.
**Depends on:** [SPEC-P0.1-DECISIONS](SPEC-P0.1-DECISIONS.md) (ADR-13 Chains A/B/C/F/G, ADR-14
throughput table, ADR-02 scheduling, ADR-10 backup schedule) and
[SPEC-P0.2-PROVIDERS](SPEC-P0.2-PROVIDERS.md) (verified prices, verified rate limits, F-2, F-3,
F-8, F-9, F-11, F-13).

**Fact labels**, continuing P0.2's convention:
`[V]` verified in an upstream spec against primary documentation ·
`[D]` derived by arithmetic in this document from `[V]` inputs ·
`[A]` assumption, with a stated verification method ·
`[U]` unverified, carried to OPEN QUESTIONS.

---

## 0. Headline findings — read these before the tables

Eight findings change the plan or contradict upstream material. Each is expanded below and
reconciled in §10.

**B-F1 — The phase prompt asks for an open-burst analysis of an architecture ADR-13 forecloses,
and the honest answer is that the worst minute is not the open.** `[D]`
`docs/PROMPT-PACK.md` P0.3 asks for "ingest throughput in the worst minute of the day (the open),
in messages/sec and rows/sec". ADR-13 Chain C already states that this burst "simply does not
exist here", and this phase confirms it by computing every candidate for *worst minute*: the peak
sustained write in normal operation is the **21:45 UTC end-of-day bulk load at ~63 rows/s and
~250 write IOPS**, which is **0.5% of a commodity NVMe SSD**. The genuine peak load on the machine
is the **one-time 10-year backfill**, and the genuine *recurring* peak is **backtest read and CPU**,
neither of which is a "minute of the day". The prompt's framing is answered in §3 rather than
followed, and the deviation is recorded here as Block A requires.

**B-F2 — The $200–500/month LLM ceiling cannot select a gate width, because no feasible gate width
violates it.** `[D]`
Against P0.2's verified prices for the **AD-5 primary, OpenAI `gpt-5.6-luna`**, a live LLM call
costs **$0.00300**. Reaching $200/month requires **66,667 calls/month = 3,175 candidates per
session**, which is **2.12× the entire 1,500-name universe**. Gating *every* name in the
universe every session costs **$94.50/month**. The prompt's implied deliverable — "where the $200-500/month ceiling actually
lands and what gate width it implies" — therefore has no solution in the feasible domain, and the
`create-issues.sh` acceptance criterion "the gate width from this phase is the number P4.2
implements" **is unsatisfiable on cost grounds**. Gate width stays at ADR-13's `llm.gate_width = 15`
for the reasons ADR-13 gave — hallucination control, determinism, attack-surface reduction — and
**P0.3 declines to set it**. §5 gives the full arithmetic.

**B-F3 — The $200–500/month figure describes an activity invariant I9 forbids.** `[D]`
The only way to spend that much is backtest replay of the LLM tier (2.3–5.7 full 10-year runs per
month at gate 15, $113.40/run). But P0.1 invariant **I9** — "LLM-derived features never enter
walk-forward optimisation" — means there is no promotion-related reason to replay the LLM across
history at all. The legitimate replay cases are a one-off forward-validation dataset build and
prompt-version regression testing, both deliberate and owner-approved. **The LLM budget line is
therefore driven by `prompt_version` revisions, not by trading activity or gate width**, because
Chain G's cache key includes `prompt_version` and a revision invalidates the entire cache.

**B-F4 — ADR-08 requires ≥34 walk-forward windows; 10 years of history at 6-month rolls yields
about 16. The three ways out have different price tags, and one of them costs $120/month.** `[D]`
`promotion.min_wf_windows = 34` with "6-month rolls" `[RS §13]` needs roughly **20 years** of
history (initial train + 17 years of 6-month test periods). P0.2 buys **Massive Stocks Developer
at $79/mo for 10 years**; 20+ years is **Stocks Advanced at $199/mo** `[V]`. Resolutions and cost
in §7.2 and §10 (A-13). Recommended: **3-month rolls**, which yields 32–34 windows from the 10
years already bought, holds the data line at $79, and still puts ~100 closed trades in each window
against ADR-13's ~3,400-trade decade. This is ADR-08's decision, not P0.3's; P0.3 reports and
prices it.

**B-F5 — The audit trail is 97% of compressed storage, not the 30× ADR-13 Chain B estimated.** `[D]`
Recomputed with an explicit row-width model (§2.1): compressed market data across every bar
dataset the system actually provisions totals **~101 MB**; the audit trail totals **~9.45 GB** over
ten years. That is **94×**, and it means every storage, backup and retention decision downstream
is an *audit-trail* decision. Chain B's conclusion is right and its magnitude is understated.

**B-F6 — P0.1's 92 B/row figure silently assumes `double precision` OHLC. Under `numeric` it is
~116 B.** `[D]`
The composition is given in §2.1. The 26% difference changes no conclusion, but P1.2 must choose
deliberately rather than inherit a number whose assumption was never stated — and the choice
interacts with P1.1's `Decimal`-not-`float` mandate, which was written about money arithmetic and
may or may not have been intended to reach bar storage. Flagged to P1.2 as `RULE-B3`.

**B-F7 — The verified cost model excludes the VM and off-VM backup storage, so amendment A-6 is
still low.** `[D]`
P0.2 A-6 amends P0.1's A14 band to "$130–230/mo, staged", but that total is **data and broker
only**. It carries **no compute line and no backup-storage line**, and ADR-10 mandates 35 days of
WAL, nightly base backups and 8 weekly VM images held off-VM — approximately **300 GB** of object
storage. Neither price is verified anywhere in the programme. Both are in OPEN QUESTIONS (Q-1,
Q-2) with exact queries, and §8 presents the total as a function of them so it becomes a number the
moment they are filled in.

**B-F8 — "Fail-closed → DENY" is ambiguous for an exit, and the latency budget is where it
surfaces.** `[D]`
`[CONST-6]` reads "Missing data, stale data, an exception, an ambiguous state → DENY". For an
*entry* that means do not buy — risk falls. For an *exit* it means do not sell — **risk rises**.
§6.2 cannot state a drop behaviour for the intraday-exit path without resolving this. The
architecture already contains the resolution (the broker-side protective stop placed at entry,
ADR-13), and ADR-13 Chain D already carves the kill switch out of the PDT counters, so the
precedent exists — but no upstream document states the general rule. Recommended wording in §6.3
and §10 (A-14). **This is not P0.3's to decide**: it touches `[CONST-1]` and `[CONST-6]` and
belongs to P2.9 with owner sign-off.

---

## 1. Inputs consumed, and their state

| Input | Source | State | Used for |
|---|---|---|---|
| Universe = 1,500 US names, hard cap | ADR-14 | `[V]` | Every volume and throughput figure |
| Sessions/year = 252; sessions/month = 21 | ADR-14, ADR-13 Chain G | `[A]` | Row counts, LLM monthly spend |
| 10-year backtest horizon | P0.1 §0.3 C-3 | `[V]` | Storage, backtest cost |
| Daily bars primary; 5-min held-only (≤25) | ADR-13 Chain A | `[V]` | Storage tiers, monitor load |
| ~15,000 audit events/session, ~1 KB each | ADR-13 Chain B | `[A]` | Dominant storage line |
| Gate width 15; 6,000 in / 1,500 out tokens per candidate | ADR-13 Chain G, P0.1 A11 | `[A]` | LLM spend |
| **`gpt-5.6-luna` $0.20/M in, $1.20/M out — PRIMARY since AD-5** | P0.2 §3.12 | `[V]` | LLM spend |
| `deepseek-v4-flash` $0.22/$0.66 off-peak — **fallback** since AD-5 | P0.2 §3.11 | `[V]` | Fallback LLM spend |
| OpenAI does **not** price by time of day; Batch = 50% but turnaround undocumented (**M-10**) | P0.2 §3.12 | `[V]`/`[U]` | RULE-B8 is provider-conditional; live path uses Standard |
| DeepSeek concurrency 2,500; idle close 600 s | P0.2 §10.4 | `[V]` | LLM stage timeout design |
| Massive Developer $79, 10 y history, unlimited calls, 15-min delayed | P0.2 §3.3 | `[V]` | Data cost, B-F4 |
| Massive Advanced $199, 20+ y history, real-time | P0.2 §3.3 | `[V]` | B-F4 resolution pricing |
| Alpaca Algo Trader Plus $99; free tier IEX-only | P0.2 §3.2, F-2 | `[V]` | Staged cost, monitor feed |
| Alpaca WS connection limit 1; message types incl. `b`, `t`, `c`, `x` | P0.2 §3.2, §10.4 | `[V]` | Monitor load, correction handling |
| FMP Premium $49, 750 req/min, **50 GB / 30 days bandwidth** | P0.2 §3.4, F-11 | `[V]` | Backfill feasibility |
| Alpaca Trading 200 req/min per account | P0.2 §10.4 | `[V]` | Order-window budget |
| Backup schedule: WAL 35 d, nightly base, weekly image ×8 | ADR-10 | `[V]` | Off-VM storage sizing |
| `promotion.min_wf_windows = 34` | ADR-08 | `[V]` | B-F4 |
| Retail plans are individual-use / non-professional | P0.2 F-9, N15 | `[V]` | §8 licensing note |

---

## 2. Data volume and storage

### 2.1 Row-width model — stated, not assumed

ADR-13 Chain B uses "~92 B/bar including overhead" as an `ASSUMPTION [VERIFY-P0.3]`. This phase
was asked to verify it, so the composition is written out rather than inherited.

A PostgreSQL heap tuple carries a **23-byte `HeapTupleHeaderData`**, MAXALIGN-padded to 24 bytes on
a 64-bit build, plus a **4-byte line pointer** in the page — **28 B of fixed overhead per row**
before any column data. `[A]` — from PostgreSQL's documented page layout; verification query in
OPEN QUESTIONS Q-6.

| Column | Type A (`numeric`) | Type B (`double precision`) |
|---|---|---|
| `instrument_id` | int4 — 4 B | 4 B |
| `ts` | timestamptz — 8 B | 8 B |
| `open`,`high`,`low`,`close`,`vwap` | numeric ≈ 12 B each — 60 B | float8 8 B each — 40 B |
| `volume` | int8 — 8 B | 8 B |
| `trade_count` | int4 — 4 B | 4 B |
| Column data | 84 B | 64 B |
| + tuple overhead | 28 B | 28 B |
| **Row total (with alignment)** | **~116 B** | **~92 B** |

> **B-F6 restated precisely.** P0.1's 92 B is Type B. It is correct *if OHLC are stored as
> `double precision`*, and that premise was never written down. P1.1 mandates `Decimal` for money
> and price; whether that mandate reaches a bar table is P1.2's call. **All figures below use
> Type A (116 B), the conservative branch.** Every conclusion survives either choice.

Secondary index `(instrument_id, ts)` on uncompressed chunks ≈ **24 B/row** `[A]`. TimescaleDB
replaces it with `segmentby`/`orderby` metadata once a chunk is compressed, so it does not persist
into the steady-state figures.

**Compression ratio.** `[A]` **15× central, 10–20× band** for numeric time-series columns
(delta-of-delta timestamps, run-length on the segmentby column, float/integer compression) and
`[A]` **4× central, 3–6× band** for the text/JSONB-dominant audit and news tables. Verification
method: measure `hypertable_compression_stats()` after the first month of real data — this is
`RULE-B2` and is binding on P1.2.

### 2.2 Volume at every granularity the prompt asks for

Sessions: 252/year, 2,520 over ten years. US regular session 09:30–16:00 ET =
**390 one-minute bars, 78 five-minute bars** per instrument per session `[D]`.

**Provisioned — datasets the system actually stores:**

| Dataset | Rows | Raw | Compressed |
|---|---|---|---|
| Daily bars, 1,500 × 2,520 (10 y) | 3,780,000 | 438 MB | **29 MB** (22–44) |
| Daily bars, ongoing | 378,000/yr | 43.8 MB/yr | 2.9 MB/yr |
| Fundamentals, 1,500 × 40 q × 1.5 restatement factor `[A]` | 90,000 | 135 MB | 45 MB |
| Corporate actions, 10 y | ~90,000 | 18 MB | 5 MB |
| Universe membership snapshots, 522 weeks × 1,500 (I7, kept forever) | 783,000 | 31 MB | 8 MB |
| News, 200/day × 3 y forward, **plus revision rows (N16)** | 219,000 × revision factor | 438 MB × rf | 125 MB × rf |
| 5-min bars, **held only**, 25 × 78 × 252 × 3 y | 1,474,200 | 171 MB | 11 MB |
| 5-min validation slice, top 200 × 2 y | 7,862,400 | 912 MB | 61 MB |
| **Audit trail**, 15,000/session × 252 × 10 y | **37,800,000** | **37.8 GB** | **9.45 GB** |
| *(news revision factor `rf`)* | *unmeasured — **M-12***  | *—* | *at rf = 3, +250 MB; immaterial against 4.7× headroom* |
| **TOTAL, 10 years** | **~52.5 M** | **~39.9 GB** | **~9.7 GB** |

**Counterfactuals — the prompt's 1m and 5m full-universe cases, computed so no later phase
"discovers" them:**

| Counterfactual | Rows | Raw | Compressed |
|---|---|---|---|
| 5-min, **full universe**, 1,500 × 78 × 2,520 | 294,840,000 | 34.2 GB | 2.28 GB |
| 1-min, **full universe**, 1,500 × 390 × 2,520 | **1,474,200,000** | **171 GB** | **11.4 GB** |
| Quotes / ticks, full universe | — | multiple TB `[V]` ADR-13 Chain B | requires a paid consolidated feed |

> **The 1-minute case does not break on disk — 11.4 GB compressed is affordable — it breaks on
> backtest RAM.** §4.3 computes where. ADR-13 Chain B warned that a later phase must not conclude
> "1-minute bars are cheap, therefore intraday is affordable"; §4.3 is the arithmetic that closes
> that door quantitatively rather than by assertion.

### 2.3 Where the disk actually goes — B-F5

Compressed market data across **every** bar dataset provisioned: 29 + 11 + 61 = **101 MB**.
Compressed audit trail: **9,450 MB**. Ratio **94:1** `[D]`. Audit is **97.1%** of compressed
application data.

**On-VM disk budget at year 10:**

| Line | Size | Basis |
|---|---|---|
| Compressed hypertable data | 9.7 GB | §2.2 |
| Uncompressed hot chunks (30-day compression policy) | 1.0 GB | 30/365 of annual audit + bars, with indexes |
| WAL held on-VM between archives | 2.0 GB | checkpoint churn and full-page writes `[A]` |
| Base-backup staging (needs ~1× DB free) | 10.0 GB | ADR-10 nightly base backup |
| Postgres free-space / bloat factor 1.3× | 3.0 GB | `[A]` |
| OS + Docker images (Timescale, Redis, FastAPI, Prometheus, Grafana, Vault, app) | 15.0 GB | `[A]` |
| Prometheus TSDB, 90-day retention | 2.0 GB | `[A]` |
| Model artifacts held hot (champion + challenger + recent) | 5.0 GB | ADR-10 keeps the archive off-VM |
| journald logs | 5.0 GB | `[A]` |
| **Total** | **~52.7 GB** | |

A Postgres data volume should not be run above ~70% full. 52.7 / 0.70 = **75 GB floor**; with 2×
growth headroom, **150 GB**. **Decision: 250 GB NVMe SSD**, which confirms ADR-13 Chain B's "a
single 250 GB SSD covers a decade" and leaves 4.7× headroom on the year-10 figure. `[D]`

**Stress case — audit volume 5× the estimate** (P1.4 writes one audit row per symbol per pipeline
stage rather than per decision): audit compressed 47 GB, total ~90 GB, /0.70 = 129 GB. **250 GB
still holds, at 1.9× headroom.** The audit estimate is the single most load-bearing assumption in
this document and is the first row of the sensitivity table in §9.4.

**Off-VM backup storage**, from ADR-10's schedule: 8 weekly VM images ≈ 240 GB + 35 days of WAL
≈ 2 GB + retained base backups ≈ 50 GB = **~300 GB** `[D]`. **Unpriced** — OPEN QUESTIONS Q-2.

---

## 3. Ingest throughput, and the worst minute — B-F1

### 3.1 Every candidate for "worst minute", ranked

| # | Candidate | Rows | Rows/s | Messages/s | Verdict |
|---|---|---|---|---|---|
| 1 | **21:45 UTC EOD bulk load** | ~3,780 in one `COPY` | **~63** (over 60 s) | n/a — REST | **Worst sustained minute in normal operation** |
| 2 | 14:30 UTC US open, monitor running | 25 minute-bars | 0.4 | **0.42** | Not a burst. See §12.12 |
| 3 | 13:45–14:15 UTC order window | ≤8 orders + audit | <1 | <1 | Trivial |
| 4 | Sat 06:00 UTC reconstitution | read-mostly; writes 1,500 snapshot rows | 25 | n/a | Trivial |
| 5 | **One-time 10-year backfill** | 3,780,000 | see §3.4 | n/a | **Genuine peak load on the machine** |
| 6 | **Backtest / walk-forward run** | read 3.78 M repeatedly | n/a | n/a | **Genuine recurring peak — CPU and RAM, not writes** |

### 3.2 The EOD bulk load, costed

3,780 rows × 116 B = **438 KB** of column data → 55 heap pages of 8 KB, ~30 index pages, and WAL
with full-page writes at ~2–3× ≈ 1.3 MB. Total physical write ≈ **2 MB ≈ 250 × 8 KB write ops**,
completing in **well under one second**. `[D]`

A commodity NVMe SSD sustains 50,000–500,000 random IOPS `[A]`. Utilisation at the worst minute:
**~0.5%**. CPU for a `COPY` of 3,780 narrow rows: **milliseconds**.

> **RULE-B1.** No downstream phase may size the VM, the disk class, or the Postgres configuration
> against ingest write throughput. It is four orders of magnitude below a single SSD's capability
> and it is not the constraint. Size against §4.

### 3.3 The fsync count is the interesting number, not the byte volume

15,000 audit events per session, each durable **before** the action it records `[CONST-5]`. If each
is an individually fsync'd transaction: 15,000 fsyncs × ~0.5 ms on NVMe `[A]` = **~7.5 seconds of
pure fsync latency**, consumed inside the 18-minute pipeline budget (§6.1). Comfortable, but it is
the only place in the write path where the audit trail is visible in the *latency* budget rather
than the storage budget.

> **RULE-B4, handed to P1.4.** Audit writes for **actions** (an order, a risk verdict, a
> kill-switch transition, a config change) are individually durable before the action —
> `[CONST-5]` admits no batching. Audit writes for **evaluations** (a Tier-1 screen result for a
> name that was not selected) may be batched, because an evaluation is not an action and nothing
> takes effect on it. This distinction is what keeps the 15,000-event figure from becoming a
> latency problem if it grows; it is also the lever that makes §9.4's stress case survivable.

### 3.4 The real peak: initial backfill

| Step | Volume | Path | Budget |
|---|---|---|---|
| 10 y daily bars, 1,500 names | 3.78 M rows | Massive flat files (S3, Starter+) or REST at `limit=50,000` → 76 requests `[V]` | 2 h |
| Splits since 1978-10-25, dividends since 2000-01-15 | ~90 k rows | Massive REST `[V]` | 15 min |
| Point-in-time ticker membership, 522 weekly snapshots | 783 k rows | Massive `/v3/reference/tickers` with `date` + `active` `[V]` | 2 h |
| **Fundamentals, 1,500 × 40 quarters** | 90 k rows | **FMP — bandwidth-bound, see below** | 6 h |
| 5-min validation slice, 200 × 2 y | 7.86 M rows | Massive | 2 h |

**F-11 bites here and nowhere else.** FMP Premium meters **50 GB per trailing 30 days** `[V]`.
At `[A]` ~150 KB per statement payload, a full 1,500-name × 40-quarter backfill is
**1,500 × 40 × 150 KB ≈ 9 GB = 18% of the monthly bandwidth**. Steady state is
25 symbols/session × 21 × 150 KB ≈ **79 MB/month = 0.16%**.

> **RULE-B5.** The FMP client carries a **byte budget** as well as a rate limiter, and the
> fundamentals backfill is checkpointed and resumable so a bandwidth stall does not restart it.
> The bandwidth headroom means a full re-backfill is possible about **five times per month**, and
> that is the operational limit to know. Extrapolated: the 50 GB ceiling binds on backfill at
> roughly **8,000 names** — see §9.1.

`COPY` throughput for the bulk load: 100,000–500,000 narrow rows/s on SSD `[A]`, so 3.78 M rows is
**~10–40 s of `COPY`**. The multi-hour budgets above are **vendor pagination and rate limits, not
database write capability**.

---

## 4. VM sizing, and the named bottleneck

### 4.1 What runs, and what it needs

| Workload | When | CPU | RAM | Notes |
|---|---|---|---|---|
| Postgres + TimescaleDB | always | low | 4 GB `shared_buffers` ~25% | |
| Redis | always | negligible | 0.5 GB | |
| FastAPI | always | negligible | 0.3 GB | ADR-01: no custom frontend |
| Prometheus + Grafana | always | low | 1.0 GB | |
| Vault | always | negligible | 0.3 GB | |
| Intraday monitor | session hours | negligible | 0.3 GB | ≤25 symbols, 0.42 msg/s |
| Nightly ingest | 21:45 UTC | low, ~1 min | 0.5 GB | §3.2 |
| Nightly pipeline | 22:30 UTC | moderate, ~18 min | 2 GB | 1,500-name screen + XGBoost inference |
| **10-year backtest** | on demand | **all cores** | **4–8 GB peak** | **The RAM driver** |
| **Quarterly retrain** | quarterly + 5 triggers | **all cores** | **4 GB peak** | ADR-07 |
| **Baseline resident total** | | | **~6.4 GB** | |

### 4.2 The bottleneck is RAM, and specifically the backtest working set

A vectorised 10-year backtest holds `[D]`:

> 3,780,000 bars × `[A]` ~60 engineered feature columns × 8 B = **1.81 GB** as one dense frame,
> and pandas/numpy intermediate copies during feature construction realistically **2–4×** that
> → **4–8 GB peak RSS**.

Add the ~6.4 GB resident baseline and a retrain that may run in the same quarter, and:

| RAM | Verdict |
|---|---|
| 8 GB | **Rejected.** Baseline 6.4 GB leaves 1.6 GB — the backtest must be chunked by date range, which is implementable but slows walk-forward materially and adds a class of chunk-boundary bugs to the one component whose correctness the whole promotion process depends on |
| **16 GB** | **SELECTED.** Baseline + an 8 GB backtest with ~1.6 GB spare. One heavy job at a time, which is exactly what ADR-02's serial systemd-timer model schedules |
| 32 GB | Headroom for a concurrent backtest **and** retrain. Nothing in the schedule requires concurrency. Revisit at the §9 triggers |

**vCPU.** The only CPU-hungry work is offline and parallel: XGBoost `hist` training and vectorised
feature construction. **4 vCPU** is sufficient for every deadline in §6. What **8 vCPU** buys is
*walk-forward wall-clock*, roughly halved — relevant only if §7's 1–3 h becomes an operational
irritant during a champion/challenger cycle. Not required for v1.

### 4.3 The specification

| Resource | Value | Bottleneck rationale |
|---|---|---|
| vCPU | **4** | Sufficient at every deadline; 8 only shortens walk-forward wall-clock |
| RAM | **16 GB** | **The binding resource** — vectorised backtest working set (§4.2) |
| Disk | **250 GB NVMe SSD** | Audit trail dominates (§2.3); 4.7× headroom at year 10 |
| Network | Any. No co-location, no low-latency path | ADR-13 Chain A |
| Egress IP | **Static, ≥1, ≤2 registered** | `[CONST-9]`; Zerodha mandates it for order placement from 2026-04-01 `[V]` |

> **RULE-B6 — the counterfactual that closes the intraday door on arithmetic.** At 1-minute bars
> for the full universe the same vectorised backtest holds
> **1,474,200,000 × 60 × 8 B = 708 GB** as one frame — **44× a 16 GB VM and beyond any single-VM
> configuration**. It forces an out-of-core or columnar-store backtest, which is a different
> program. This, not disk and not data subscription price, is where "just use 1-minute bars"
> actually fails, and it is recorded so no later phase has to rediscover it.

---

## 5. LLM spend — B-F2, B-F3

### 5.1 Unit cost, from verified prices

Per candidate: `[A]` 6,000 input + 1,500 output tokens (P0.1 A11, still unverified — Q-4).
**AD-5 makes OpenAI `gpt-5.6-luna` the primary and DeepSeek `deepseek-v4-flash` the fallback**,
conditional on M-7. OpenAI does not price by time of day, so the primary's rate is
time-invariant. The fallback still does: the 22:30 UTC pipeline sits **inside DeepSeek's
off-peak window by construction** — peak is Mon–Fri 01:00–04:00 and 06:00–10:00 UTC `[V]`.
**The live path uses OpenAI's Standard tier, never Batch**, because `TIER3_LLM` has a 600 s
deadline and Batch turnaround is undocumented (**M-10**).

| Model | In $/M | Out $/M | **$/call** |
|---|---|---|---|
| **`gpt-5.6-luna`, Standard — PRIMARY (AD-5)** `[V]` | 0.20 | 1.20 | **$0.00300** |
| `gpt-5.6-luna`, Batch (−50%) — **replay only, pending M-10** `[V]` | 0.10 | 0.60 | $0.00150 |
| `deepseek-v4-flash`, off-peak — **fallback** `[V]` | 0.22 | 0.66 | $0.00231 |
| `deepseek-v4-flash`, peak — fallback `[V]` | 0.44 | 1.32 | $0.00462 |
| `gpt-4o-mini` — **named by `[CONST]`, absent from OpenAI's catalogue** `[V]` F-8 | — | — | **not purchasable** |

### 5.2 Live monthly spend at the gate widths the prompt names

21 sessions/month, one gate firing per session.

| Gate width | Calls/mo | **`gpt-5.6-luna` Std — PRIMARY** | `deepseek-v4-flash` off-peak — fallback | Batch (replay only) |
|---|---|---|---|---|
| 5 | 105 | **$0.32** | $0.24 | $0.16 |
| 10 | 210 | **$0.63** | $0.49 | $0.32 |
| **15 — ADR-13 design point** | **315** | **$0.95** | $0.73 | $0.47 |
| 20 | 420 | **$1.26** | $0.97 | $0.63 |
| 50 | 1,050 | **$3.15** | $2.43 | $1.58 |
| **1,500 — no gate at all** | **31,500** | **$94.50** | $72.77 | $47.25 |

### 5.3 Where the $200–500/month ceiling lands: nowhere reachable

$200 ÷ $0.00300 = **66,667 calls/month** ÷ 21 = **3,175 candidates per session** = **2.12× the
entire universe**. `[D]` On the DeepSeek fallback it would take 4,123/session, or 2.75×.

> **B-F2, stated as the finding it is.** The bottom row of §5.2 is the proof: **abolishing the gate
> entirely costs $94.50/month**, comfortably inside the ceiling. A cost ceiling that is not
> violated by the maximum possible value of a parameter cannot constrain that parameter. The
> acceptance criterion "the gate width from this phase is the number P4.2 implements" is therefore
> **not satisfiable on cost grounds and P0.3 does not satisfy it**.
>
> **`llm.gate_width` remains 15, unchanged, on ADR-13 Chain G's authority** — the gate exists for
> hallucination control, determinism and attack-surface reduction. P4.2 is designed against
> *those* objectives. A gate tuned to minimise spend would be tuned differently and worse, and
> this document exists in part to stop that from happening.

### 5.4 Where the money actually is: replay, and it is forbidden

Full 10-year replay = 2,520 sessions × gate width, on the **AD-5 primary at Standard rates**
(Batch would halve these, pending M-10):

| Gate width | Calls/run | Cost/run — primary | Cost/run — DeepSeek fallback |
|---|---|---|---|
| 5 | 12,600 | $37.80 | $29.11 |
| 10 | 25,200 | $75.60 | $58.21 |
| **15** | **37,800** | **$113.40** | $87.32 |
| 20 | 50,400 | $151.20 | $116.42 |
| 50 | 126,000 | $378.00 | $291.06 |

$200–500/month = **1.8–4.4 full replays per month at gate 15**. That is the only activity in the
programme that reaches the ceiling — and **invariant I9 forbids the reason anyone would do it.**

Chain G's cache key is `hash(sanitised_payload ‖ model_id ‖ prompt_version)`. Consequences `[D]`:

- Re-running a backtest with an unchanged prompt costs **$0** — every key hits.
- Changing `prompt_version` invalidates **every** key. One prompt revision = one full replay = **$113.40** if a full replay is performed.
- **The LLM cost driver is `prompt_version` revisions, not gate width and not trading activity.**

> **RULE-B7.** A full-history LLM replay is an owner-approved action, not a developer convenience.
> `llm.replay_requires_approval = true`, and the approval is ADR-09's mechanism.
>
> **RULE-B8 (provider-conditional since AD-5).** OpenAI, the primary, does **not** price by
> time of day, so no window arithmetic applies to a replay on the primary. **DeepSeek, the
> fallback, does**: a replay routed to it is scheduled **off-peak** (outside Mon–Fri
> 01:00–04:00 and 06:00–10:00 UTC) or it costs exactly double `[V]`. The rule is retained
> rather than deleted precisely because the fallback keeps the exposure.

### 5.5 Alarm thresholds

P0.1 sets `llm.monthly_spend_alarm_usd = 50`. Against the **AD-5 primary's $0.95 live baseline**
that is **53× headroom** — it fires only on a runaway loop or an unauthorised replay, which is its intent, and it
is kept. But 68× is too coarse to notice a gate that has quietly widened, so this phase **adds** a
warning tier rather than changing the critical one:

| Tier | Threshold | Fires on |
|---|---|---|
| **WARN** (new, `RULE-B9`) | **$5.00/month** | ~7× the live baseline — a widened gate, a retry storm, peak-hour drift, or a token payload that has grown |
| **CRITICAL** (P0.1, unchanged) | **$50.00/month** | Runaway loop or unauthorised replay |

---

## 6. Latency budget

### 6.1 Path A — daily rebalance: a deadline-scheduled batch, not a latency problem

The prompt asks for "bar closes → order acknowledged". On this architecture that span is
**~17.75 hours by design**: the bar closes at 20:00 UTC and the order is acknowledged at
~13:45 UTC the next session (ADR-14). An end-to-end latency budget in the millisecond sense would
be meaningless. **The correct object is a set of per-stage wall-clock budgets against fixed clock
deadlines**, and that is what follows.

All times UTC, EDT shown. ADR-02's two-timer/calendar rule shifts them one hour in EST; the
session calendar is authoritative and a job that cannot resolve it exits non-zero.

| # | Stage | Starts | Budget | Deadline | Over budget → |
|---|---|---|---|---|---|
| 1 | `INGEST` — EOD bars, corporate actions, fundamentals deltas | 21:45 | **30 min** | 22:15 | **ABORT.** Precondition unmet, no order list, no trading next session. Matches P0.2's Massive outage analysis |
| 2 | `UNIVERSE_RESOLVE` — as-of membership | 22:30 | 30 s | 22:30:30 | **ABORT.** A guessed universe is a survivorship-bias event (I7) |
| 3 | `TIER1_SCREEN` — 1,500 names | 22:30:30 | 2 min | 22:32:30 | **ABORT** |
| 4 | `TIER2_QUANT` — XGBoost scoring | 22:32:30 | 2 min | 22:34:30 | **ABORT** |
| 5 | `INFERENCE_GATE` — select top-N | 22:34:30 | 30 s | 22:35 | **ABORT** |
| 6 | `TIER3_LLM` — 15 concurrent calls | 22:35 | **10 min** | 22:45 | **DEGRADE — the one documented exception. See below** |
| 7 | `DECISION` | 22:45 | 1 min | 22:46 | **ABORT** |
| 8 | `RISK` | 22:46 | 1 min | 22:47 | **DENY ALL** — `[CONST-1]`, `[CONST-6]` |
| 9 | `AUDIT_FREEZE` — order list written and sealed | 22:47 | 1 min | **22:48** | **ABORT.** If the audit write fails, nothing happens `[CONST-5]` |
| — | *Total pipeline* | 22:30 | **18 min** | 22:48 | Slack to the order window: **~14.95 h** |
| 10 | `ORDER_PLACEMENT` — per order | 13:45 | **5 s**, hard 30 s | 14:15 | Retry within the window; **abandon at 14:15** |

**Stage 6 is the only stage that degrades rather than aborts, and the exception is justified, not
convenient.** ADR-13 Chain G excludes the LLM tier from the promotable strategy, so its absence
cannot invalidate the deterministic path. On timeout: candidates proceed with **no thesis**, and
any decision rule requiring a thesis emits **NO-TRADE**. The degradation can therefore only ever
**reduce** the number of orders, never increase or alter one. That property is what makes it safe,
and `RULE-B10` requires P4.3 to preserve it.

**Stage 6's budget is set by a verified vendor behaviour, not by taste.** DeepSeek closes a
connection only after **600 s** if inference has not started `[V]`. Fifteen *sequential* calls
could therefore hang for **150 minutes** and blow an 18-minute pipeline by 8×. Hence:

> **RULE-B11, binding on P4.3.** The 15 gate calls are issued **concurrently** (DeepSeek
> concurrency limit is 2,500 — no constraint `[V]`), each with a **120 s client timeout**, under a
> **600 s stage deadline**. And because DeepSeek under load "continuously returns empty lines" on
> non-streaming requests `[V]`, **a client that treats an empty line as EOF truncates silently** —
> the client must use streaming or explicitly handle keep-alive lines. A silent truncation here
> produces a *plausible partial thesis*, which is worse than no thesis.

**Order placement, stage 10.** Alpaca Trading allows **200 requests/min per account** `[V]`; the
session places ≤8 orders. Per order: audit write **before** submit `[CONST-5]` → submit → ack. The
30-minute window gives enormous slack even fully serialised with retries.
**Missing the 14:15 deadline abandons the remaining orders — it never places them late.** The order
list was frozen against the prior session's completed bar (ADR-14); placing at 15:00 would be an
undocumented intraday entry that ADR-13 forecloses. Not trading is the safe outcome.

### 6.2 Path B — intraday exit: a real latency budget

Applies to held positions only (≤25), on 5-minute bars assembled from Alpaca's `b` minute-bar
stream.

| # | Stage | Budget | Hard | Over budget → |
|---|---|---|---|---|
| 1 | Bar close → WS message received | `[A]` **3 s** | 10 s | See stale-data rule below |
| 2 | Message → 5-min bar assembled | 100 ms | 500 ms | Log; bar deferred one interval |
| 3 | Stop + exit-hierarchy evaluation, ≤25 positions | 100 ms | 500 ms | CRITICAL alert |
| 4 | Risk engine pre-trade check | 200 ms | 1 s | **See §6.3 — unresolved upstream** |
| 5 | **Audit write, durable, before the order** `[CONST-5]` | **50 ms** | 500 ms | **No order.** Backstop is the broker-side protective stop |
| 6 | Order submit → broker ack | `[A]` **500 ms** | 5 s | Retry once, then CRITICAL |
| — | **Bar close → order acknowledged** | **≤5 s** | **10 s** | |

Stages 1 and 6 are `[A]` — neither Alpaca's bar-aggregation delay nor its order-ack latency is
published on any page P0.2 retrieved. Both are OPEN QUESTIONS (Q-3) and both are measurable in
paper trading on day one, subject to rule N11 (paper proves plumbing, not fill quality).

**Stale-data rule.** No `b` message for a subscribed symbol for **> 600 s** (two 5-minute
intervals) → **CRITICAL**, halt all new entries immediately, and hold positions on their
**broker-side protective stops placed at entry**. This is precisely why ADR-13 places those stops
at the broker rather than evaluating them only in our process, and it is what makes a monitor
outage survivable instead of catastrophic.

**Corrections are a live message type, and the latency budget is where that matters.** Alpaca
streams `c` (correction) and `x` (cancel/error): a trade already delivered can be revised `[V]`.

> **RULE-B12.** The monitor acts **only on completed bars**, never on the in-progress bar. A
> correction arriving *after* an exit has been submitted is recorded as an audit event and **is not
> reversed** — a sale cannot be unwound, and pretending otherwise would put a compensating trade on
> an untrusted vendor message. A correction arriving *before* the next evaluation revises the bar
> normally. Binding on P3.3.

### 6.3 The unresolved contradiction this budget surfaced — B-F8

Stage 4 above cannot be completed honestly. `[CONST-6]` says an ambiguous state → **DENY**. For an
entry, DENY reduces risk. **For an exit, DENY means holding a position the exit logic just decided
to close — it increases risk.** A literal reading of `[CONST-6]` makes the risk engine's failure
mode dangerous on exactly the path where speed matters.

The architecture already contains the answer and no document states it. ADR-13 Chain D exempts
kill-switch liquidation from the PDT and settled-cash counters, establishing that
**exposure-reducing actions are treated differently from exposure-increasing ones**. §6.2 stage 5
relies on the same idea: the broker-side stop is the fail-safe.

**Recommended wording, for P2.9 and owner sign-off — not adopted here** (see A-14):

> `[CONST-6]`'s DENY applies to **exposure-increasing** actions. For **exposure-reducing** actions
> — exits, trims, kill-switch liquidation — a risk-engine failure must not block the action; it
> escalates to CRITICAL, and the pre-placed broker-side protective stop is the backstop. The risk
> engine never blocks a strictly risk-reducing order.

This is `[CONST-1]` and `[CONST-6]` territory. **P0.3 reports it and stops**, per Block A.

---

## 7. Backtest and walk-forward cost

### 7.1 The framing the prompt's question needs

On a **fixed-price single VM**, a backtest has **no metered cash cost**. The meaningful answers are
wall-clock and amortised VM time. Both are given.

**One full 10-year backtest run:**

| Component | Value | Basis |
|---|---|---|
| Feature construction, 3.78 M bars × ~60 features | `[A]` 3–10 min | 4 vCPU, vectorised |
| Session loop, 2,520 iterations incl. kill-switch simulation (I8) | `[A]` 1–5 min | ~10–100 ms/session |
| Cost and tax model, post-tax line (ADR-13 Chain E) | `[A]` 1 min | |
| **Wall clock** | **`[A]` 10–30 min** | Measure on the first real run — `RULE-B2` |
| **Marginal data cost** | **$0** | Subscription already held |
| **Marginal LLM cost** | **$0** | I9 — the LLM tier is not in the promotable strategy |
| **Amortised VM cost** | **< $0.10** | 0.5 h ÷ 720 h × monthly VM price, for any plausible price |
| *If an owner-approved LLM replay is attached* | **$113.40** | §5.4, gate 15, primary at Standard |

**Per walk-forward window** (34 windows at **3-month rolls**, ADR-08 as amended by **AD-2**):

| Component | Value |
|---|---|
| XGBoost training on the expanding window | `[A]` 1–5 min |
| OOS test over the roll | `[A]` <1 min |
| **Wall clock per window** | **`[A]` 2–6 min** |
| **Full walk-forward, 34 windows (3-month rolls, AD-2)** | **`[A]` 1–3 h** |
| **Marginal cash cost per window** | **≈ $0.004** at any plausible VM price |

> **The operationally useful conclusion.** A backtest costs **wall-clock, not money**. There is no
> financial reason to economise on backtest runs, and P5.2 may explore many walk-forward
> configurations freely. The only budget that binds is the human's patience during a
> champion/challenger cycle, which is what 8 vCPU would buy if it ever becomes an irritant.

### 7.2 B-F4 — 34 windows do not fit in 10 years, and the fix has a price

Walk-forward with an expanding train and non-overlapping OOS test windows yields
`(total_years − initial_train_years) ÷ roll_length_years` windows. `[D]`

| Configuration | History needed | Windows from 10 y | Data line |
|---|---|---|---|
| 6-month rolls, 2 y initial train | 20 y | **16** ✗ | Massive **Advanced $199/mo** (+$120) |
| **3-month rolls, 1.5 y initial train** | **10 y** | **34** ✓ | **Massive Developer $79/mo — already bought** |
| 6-month rolls, overlapping test windows | 10 y | 34 | $79, but OOS windows overlap — the independence ADR-08's ≥34 assumes is gone |
| Reduce `min_wf_windows` to 16 | 10 y | 16 | $79, but weakens ADR-08's promotion evidence |

**Recommended: 3-month rolls.** It is the only option that satisfies ADR-08's window count and its
independence premise from history already purchased. At ADR-13's ~3,400 closed trades per decade,
34 windows hold **~100 closed trades each**, which is a workable per-window sample.

**DECIDED — AD-2, 2026-08-25.** The Owner adopted **3-month rolls with a 1.5-year initial
training window**, and explicitly rejected the +$120/mo 20-year alternative as not required by
the architecture. SPEC-P0.1 ADR-08 and `config.promotion.*` are updated;
`backtest.walkforward.roll_months = 3` is no longer pending. **Q-9 is CLOSED.**

---

## 8. Monthly cost model, staged — B-F7

Two lines in this table are **unpriced**, and they are unpriced because no phase in the programme
has verified them. Block A forbids inventing them.

| Line | Stage 1–4 (backtest, WF, paper, shadow) | Stage 5+ (live) | State |
|---|---|---|---|
| Massive Stocks Developer — 10 y history, unlimited calls | **$79** | **$79** | `[V]` |
| FMP Premium — fundamentals (annual-billed personal rate) | **$49** | **$49** | `[V]` |
| Alpaca Trading — commission $0 + pass-through fees | $0 | $0 + fees | `[V]` |
| Alpaca Algo Trader Plus — all-venue 5-min for held names | — *(deferred)* | **$99** | `[V]` |
| SEC EDGAR · FRED · Alpaca/Benzinga news · IBKR backup | $0 | $0 | `[V]` |
| **OpenAI `gpt-5.6-luna`** (primary, AD-5) | **$0.95** | **$0.95** | `[D]` §5.2 |
| **Verified subtotal (P0.2 §4.3)** | **≈ $129** | **≈ $228** | |
| **VM — 4 vCPU / 16 GB / 250 GB NVMe / static IP** | **unpriced** | **unpriced** | **`[U]` Q-1** |
| **Off-VM backup storage — ~300 GB** | **unpriced** | **unpriced** | **`[U]` Q-2** |
| **TOTAL** | **$129 + V + B** | **$228 + V + B** | |

**Sensitivity of the total to the two unknowns**, so the model is usable the instant they are
filled in `[D]`:

| VM + backup (V + B) | Stage 1–4 total | Stage 5+ total | Inside A-6's amended $130–230 band? |
|---|---|---|---|
| $25 | $154 | $253 | Live: **no**, +10% |
| $50 | $179 | $278 | Live: **no**, +21% |
| $100 | $229 | $328 | Live: **no**, +43% |
| $200 | $329 | $428 | Live: **no**, +86% |

> **B-F7 restated.** P0.2's A-6 amended P0.1's A14 to "$130–230/mo, staged", but that figure is
> **data and broker only** and carries no compute or backup line. **At any VM price above roughly
> $2/month the live total leaves the amended band.** A-6 is therefore still low and needs a second
> amendment to an infrastructure-inclusive figure — A-15 in §10.

**Two non-cash cost constraints that belong in this model** (P0.2 F-9, N15): every plan above is
licensed **individual-use, non-professional**, and Massive requires the account to be in the
subscriber's own name. **The moment the system manages anyone else's money, three vendors reprice
simultaneously** and this entire table is void. And FMP's footer requires a separate Data Display
and Licensing Agreement to display or redistribute its data `[V]` — a live constraint on any
future Grafana dashboard shared outside the owner.

---

## 9. Sensitivity table — cost vs universe size vs gate width vs bar frequency

Base case: **1,500 names · gate width 15 · daily bars · 10 years · audit 15,000 events/session.**
A full cross-product is 60 unreadable rows; each factor is varied against the base case, and the
combined corner that matters is called out at the end.

### 9.1 Universe size

| Names | Daily-bar rows 10 y | Compressed | Data $/mo | FMP backfill bandwidth | VM change |
|---|---|---|---|---|---|
| 500 | 1.26 M | 10 MB | **$128** | 3 GB (6% of 50 GB) | none |
| **1,500 (base)** | **3.78 M** | **29 MB** | **$128** | **9 GB (18%)** | **none** |
| 3,000 | 7.56 M | 58 MB | **$128** | 18 GB (36%) | none |
| 6,000 | 15.1 M | 116 MB | **$128** | 36 GB (**72%**) | none |
| ~8,000 | 20.2 M | 155 MB | **$128** | **50 GB — F-11 binds** | none |

**Monthly cost is flat in universe size.** Massive Developer is unlimited-call, FMP Premium is
flat-rate, and the storage delta across the whole range is under 150 MB against a 250 GB disk. The
constraint that eventually binds is **FMP's 50 GB/30-day bandwidth on backfill at ~8,000 names**
(§3.4) — a bandwidth limit, not a price. ADR-14 chose 1,500 on signal quality and fundamentals
coverage, and this table confirms cost was never the reason.

### 9.2 Gate width

| Gate | Live $/mo (primary) | Δ vs base | Full replay $/run | Share of the $228 live stack |
|---|---|---|---|---|
| 5 | $0.32 | −$0.63 | $37.80 | 0.1% |
| **15 (base)** | **$0.95** | — | **$113.40** | **0.4%** |
| 20 | $1.26 | +$0.31 | $151.20 | 0.6% |
| 50 | $3.15 | +$2.20 | $378.00 | 1.4% |
| 1,500 (no gate) | $94.50 | +$93.55 | — | 29.3% |

**Gate width is cost-irrelevant across its entire feasible range** (B-F2). Even the degenerate
no-gate case stays inside the ceiling. The gate's justification is safety.

### 9.3 Bar frequency — the only factor that steps

| Frequency | Rows 10 y | Compressed | Backtest frame | Data $/mo | VM | Verdict |
|---|---|---|---|---|---|---|
| **Daily (base)** | **3.78 M** | **29 MB** | **1.8 GB** | **$128** | **4 vCPU / 16 GB** | **Selected** |
| 5-min, held only (base, additive) | +1.47 M | +11 MB | n/a — monitor, not backtest | +$99 live | unchanged | Selected |
| 5-min, full universe | 294.8 M | 2.28 GB | **141 GB** | $128–$199 | **out-of-core backtest required** | Rejected |
| 1-min, full universe | **1.474 B** | 11.4 GB | **708 GB** | $128–$199 | **single-VM model breaks** | Rejected — ADR-13 |
| Quotes / ticks | multiple TB `[V]` | — | — | **$300–2,000+** `[V]` | different program | Rejected — ADR-13 |

> **The whole sensitivity story in one line:** cost is **flat** in universe size, **flat** in gate
> width, and **steps hard** at bar frequency — and the step is in **backtest RAM and development
> effort**, not in the data subscription. Data for full-universe 1-minute bars is affordable;
> *backtesting on it* is not, at 708 GB of working set against a 16 GB machine (RULE-B6). This
> confirms ADR-13 from an angle ADR-13 did not use, and it is the durable reason intraday stays
> closed even if a vendor discounts minute data to zero.

### 9.4 Audit volume — the load-bearing assumption

| Events/session | Compressed/yr | 10 y | On-VM total | 250 GB verdict |
|---|---|---|---|---|
| 5,000 | 0.32 GB | 3.2 GB | 46 GB | 5.4× headroom |
| **15,000 (base)** | **0.95 GB** | **9.5 GB** | **53 GB** | **4.7× headroom** |
| 45,000 (3×) | 2.84 GB | 28 GB | 71 GB | 3.5× headroom |
| 75,000 (5×) | 4.73 GB | 47 GB | 90 GB | 1.9× headroom — **still holds** |
| 150,000 (10×) | 9.45 GB | 95 GB | 138 GB | **1.8× over the 70% rule — resize** |

RULE-B4's action/evaluation split is the lever that keeps this in range if P1.4's design pushes
event counts up.

### 9.5 The corner that matters

**1,500 names · gate 50 · daily bars · audit 5× · live stage** =
$79 + $49 + $99 + $3.15 = **$230.15/month** + VM + backup, on a 90 GB disk with 1.9× headroom.
**The base architecture absorbs the pessimistic corner of every factor simultaneously without a
hardware change.** That is the real finding of this section.

---

## 10. Upstream defects, and proposed amendments

P0.3 sits below the Constitution, P0.1 and P0.2 in precedence. It reports and proposes; it does not
overturn. Numbering continues P0.2's A-series.

| # | Conflict | Proposed resolution | Authority needed |
|---|---|---|---|
| **A-13** | **ADR-08 requires ≥34 walk-forward windows; 10 years at 6-month rolls yields ~16** (B-F4) | Adopt **3-month rolls with a 1.5 y initial train** — 34 windows from history already bought, ~100 trades each. Alternative is Massive Advanced at **+$120/mo** for 20 y | **ADR-08 author (Owner)** |
| **A-14** | **`[CONST-6]`'s "ambiguous → DENY" is dangerous on the exit path** (B-F8) | Adopt the §6.3 wording: DENY governs **exposure-increasing** actions; exposure-reducing actions escalate to CRITICAL and fall back to the broker-side stop. Never block a strictly risk-reducing order | **Owner — this touches `[CONST-1]` and `[CONST-6]`** |
| **A-15** | **P0.2 A-6's "$130–230/mo" excludes the VM and off-VM backup** (B-F7) | Re-amend to an **infrastructure-inclusive** band once Q-1 and Q-2 resolve. §8's table converts either price into a total | Author of P0.1 A14 / P0.2 A-6 (same Owner) |
| **A-16** | The P0.3 prompt asks for an **open-burst** ingest analysis that ADR-13 Chain C forecloses (B-F1) | **Amend the prompt pack**, not the architecture: P0.3's ingest question is "what is the worst minute, and is it the open?" §3 answers it and shows the answer is no | Prompt-pack maintainer (Owner) |
| **A-17** | `create-issues.sh` acceptance "the gate width from this phase is the number P4.2 implements" is **unsatisfiable on cost grounds** (B-F2) | **Strike the criterion.** Replace with: "P0.3 confirms cost does not constrain gate width; P4.2 sets it on safety grounds per ADR-13 Chain G." `llm.gate_width` stays **15** | Prompt-pack maintainer (Owner) |
| **A-18** | **`[CONST]` names `gpt-4o-mini`; it is not purchasable** (P0.2 F-8, still open) | P0.2's A-1 is **still pending**. This phase's fallback figures price **`gpt-5.6-luna`**. Until A-1 is ratified the fallback line is formally unfunded | **Owner — pending from P0.2** |
| **A-19** | ADR-13 Chain B's **92 B/row** silently assumes `double precision` OHLC (B-F6) | Additive: P1.2 chooses `numeric` or `float8` **explicitly** and records why, against P1.1's `Decimal` mandate. Figures here use the conservative 116 B | None — additive to P1.2 |
| **A-20** | ADR-13 Chain B omits **bitemporality**, which P1.2's issue makes mandatory | Additive: as-reported vs as-restated fundamentals multiply that table by a restatement factor (`[A]` 1.5×) and add 16 B to every backtest-read row. Included in §2.2; immaterial to the total, material to P1.2's schema | None — additive to P1.2 |

---

## 11. BLOCKING QUESTIONS — and the defaults applied

Per Block C: listed, then proceeded on the recommended default. Every use is marked `[DEFAULT-Bn]`
inline and repeated in ASSUMPTIONS. Every rule these defaults feed carries its edge case in §15.

| # | Question | Options | Default applied | What breaks if wrong |
|---|---|---|---|---|
| **B1** | Which VM provider and price? | Hetzner / DigitalOcean / Vultr / AWS / OVH | **None.** Spec the machine (4/16/250), leave price as **Q-1** | Nothing in the design; §8's total stays parameterised until answered |
| **B2** | `numeric` or `float8` for OHLC? | numeric (exact, 116 B) / float8 (92 B) | **`[DEFAULT-B2]` numeric**, the conservative branch | 26% storage overestimate. No conclusion changes |
| **B3** | TimescaleDB compression ratio? | 8× / 15× / 20× | **`[DEFAULT-B3]` 15× numeric, 4× text**, band shown | Disk sizing moves within the 4.7× headroom |
| **B4** | Audit events per session? | 5 k / 15 k / 75 k | **`[DEFAULT-B4]` 15,000**, inherited from ADR-13 Chain B | §9.4 shows 250 GB survives to 75 k. Breaks at ~150 k |
| **B5** | Backtest feature-column count? | 30 / 60 / 120 | **`[DEFAULT-B5]` 60** | 120 columns → 3.6 GB frame, 8–14 GB peak. **16 GB starts to bind** — first revisit trigger |
| **B6** | Do walk-forward windows retrain per window? | yes / no | **`[DEFAULT-B6]` yes** — expanding-window retrain per ADR-07 | If no, walk-forward drops from 1–3 h to minutes |
| **B7** | Is the LLM replayed across the backtest? | yes / no / on approval | **`[DEFAULT-B7]` on owner approval only** — I9 forbids it as promotion evidence | If routinely yes, LLM becomes the largest single line at $87/run |
| **B8** | Order-ack and bar-delivery latency? | measure / assume | **`[DEFAULT-B8]` assume 500 ms / 3 s**, measure in paper (**Q-3**) | §6.2's 5 s budget has ~2× margin; a 3 s ack still fits the 10 s hard deadline |
| **B9** | Prometheus retention, and compression-policy delay? | 15 d / 90 d / 1 y; 7 d / 30 d | **`[DEFAULT-B9]` 90 days and 30 days** — merged, both immaterial storage knobs | ±2.7 GB combined. Immaterial to sizing, but the 30-day policy sets when compression can first be measured, which is the RULE-B2 defect |
| **B10** | **At the 14:15 order-window deadline, what happens to a partially filled order?** | (a) cancel the unfilled remainder; (b) leave it working; (c) cancel and re-place next session | **`[DEFAULT-B10]` cancel the remainder immediately**, and place the protective stop on the **filled** quantity, never the intended quantity | (b) executes outside the window ADR-14 froze — an undocumented intraday entry that ADR-13 forecloses. (c) re-derives against a stale frozen list. (a) leaves a position below the 4.0% target, which is safe and self-correcting: the next rebalance tops it up or the time stop closes it. If (a) is wrong the cost is opportunity, not risk — the right direction to be wrong in |

---

## 12. NON-BLOCKING details noticed and resolved

1. **Session length.** US regular session 09:30–16:00 ET = 390 minutes = **390 one-minute or 78
   five-minute bars**. Half-days (13:00 ET close) yield 210 and 42; they shorten ingest, never the
   09:45–10:15 order window (ADR-02).
2. **Sessions per year = 252, per month = 21.** Inherited from ADR-13 Chain G so the LLM figures
   remain directly comparable to Chain G's table.
3. **Off-peak by construction.** The 22:30 UTC pipeline sits outside DeepSeek's Mon–Fri
   01:00–04:00 and 06:00–10:00 UTC peak `[V]`. No scheduling gymnastics; a *retry* that drifts past
   01:00 UTC pays double (RULE-B8).
4. **Monthly LLM spend uses 21 sessions, not 30 days.** The gate fires once per *trading* session.
5. **`GB` throughout is 10⁹ bytes**, matching how vendors and cloud providers quote disk. Where
   Postgres reports GiB the difference is 7.4% and is inside every headroom band here.
6. **Compression applies to compressed hypertable chunks only.** Hot chunks stay uncompressed for
   30 days (`[DEFAULT-B10]`), which is why §2.3 carries a separate 1.0 GB line rather than applying
   the ratio uniformly.
7. **Index bytes disappear on compression.** Timescale replaces the b-tree with segmentby/orderby
   metadata, so the 24 B/row index is counted in hot chunks and not in the ten-year total.
8. **The 70% fill rule** on the Postgres volume is applied *before* growth headroom, not after —
   the order matters and gets it wrong in the safe direction.
9. **Backup staging needs ~1× DB free on-VM**; a base backup that cannot stage is a silent DR
   failure, which is why it is a line item rather than an afterthought.
10. **Model artifacts live off-VM** per ADR-10 ("forever"), so only champion, challenger and recent
    windows are budgeted on-disk. Off-VM model archive growth is folded into Q-2's 300 GB.
11. **`$` is USD throughout.** ADR-15 fixes USD base and forbids system-initiated conversion, so no
    FX assumption enters this budget. Zerodha's ₹500/month API fee is out of scope until ADR-11's
    India gate opens and is **not** in §8's totals.
12. **The monitor subscribes to `b` (minute bars), never `t` (trades).** At 25 symbols that is
    **0.42 msg/s, flat**. Subscribing to trades would deliver `[A]` 500–5,000 msg/s at the open for
    the same basket — the only place in the entire design where an open burst could exist, created
    entirely by a subscription choice. Exported as `monitor.subscribe_channels`.
13. **Alpaca's WebSocket connection limit is 1** `[V]`, so the monitor is a singleton and its
    restart must be crash-safe. Not a capacity constraint; a concurrency one.
14. **Order-window budget is per order, not per batch.** ≤8 orders against a 200/min account limit
    `[V]` leaves 25× headroom even with retries.
15. **Rows/s at EOD is quoted over a 60-second window** (63 rows/s) although the `COPY` completes in
    under a second — because the prompt asked for a *per-minute* figure and quoting the
    instantaneous rate would overstate load by ~60×.
16. **`[CONST]`'s ≤20 orders/min global and ≤10 per strategy** are never approached: peak is ~8
    orders in a 30-minute window. Consistent with ADR-13 Chain C's SEBI OPS finding.
17. **Fundamentals restatement factor of 1.5×** is applied only to the fundamentals table, the one
    table where as-reported vs as-restated genuinely diverges. Bars are not restated; corrections
    are handled by RULE-B12.
18. **Unit of a percentage — aligned to P0.1, and it was wrong in v0.2.** P0.1 uses the `_pct`
    suffix to mean a **fraction** (`portfolio.max_position_pct = 0.050`). v0.2 declared
    `warn_pct: int = 70`. Two conventions in one namespace fail silently in the dangerous
    direction — `0.70` misread as a percent is harmless, `70` misread as a fraction is 7,000%
    and the alarm never fires. v0.3 uses fractions throughout (§15.1).
19. **Integer versus decimal money.** Every monetary field is `Decimal`, never `float` (P1.1).
    Per-call cost is quantised to **6 decimal places** — quantising $0.00231 to cents yields
    $0.00 and zeroes the entire spend model. Totals are stored at 6 dp and displayed at 2.
20. **Inclusive versus exclusive bounds, stated per threshold.** A stage budget breaches on
    `observed > budget` (**exclusive**) — finishing exactly at budget is not a breach, or every
    budget is one tick tighter than written. The disk alarm fires on `>=` (**inclusive**). The
    `gate_width` upper bound of 1,500 is **inclusive**, so the degenerate no-gate case of §5.2
    is representable and priced rather than rejected.
21. **Rounding direction on measured latency.** `observed_seconds` is `numeric(12,3)` and is
    **truncated toward zero, never rounded**, so a stage can never be recorded as faster than
    it ran. Twelve digits cover 31 years of seconds; the column cannot overflow before
    retention discards the row.
22. **Off-by-one on the compression measurement window.** The compression policy fires at 30
    days, so a ratio measured “after month 1” can legitimately read 1× because nothing has been
    compressed yet. Measurement moves to **day 45 with a ≥3-compressed-chunk minimum**, on
    live-written chunks only — backfilled chunks arrive pre-sorted and compress better, which
    would overstate the ratio and undersize the disk (RULE-B2).
23. **DST and half-days on the order window.** The 14:15 UTC abandon deadline is 15:15 in EST;
    ADR-02's two timer definitions are selected from P1.1's calendar, never one local-time
    timer, and a job that cannot resolve the calendar exits non-zero. **Half-days do not move
    the order window** — ADR-14 fixes it at 09:45–10:15 ET on every session that opens at all;
    half-days move the ingest and pipeline timers instead.
24. **A trading halt is not stale data.** A halted symbol legitimately emits no bars, so the
    600 s stale-bar timer is **suspended** while the calendar reports the symbol halted. Without
    the suspension a routine halt raises CRITICAL and blocks new entries pool-wide — a
    self-inflicted outage triggered by an ordinary market event (RULE-B12c).
25. **Alert-storm control.** The stale-bar CRITICAL is raised **once per symbol per session**.
    A feed outage makes all 25 held symbols stale simultaneously; 25 identical pages at the
    same instant is an outage of the alerting channel, not an escalation.

---

## 13. Error paths, enumerated with fail-closed behaviour

Block B requires every error path to be enumerated with its fail-closed behaviour. "Fail-closed"
here means the invariant of `[CONST-6]`: **no error path may produce an order that would not
otherwise have been placed.** Every row below is checked against that property.

The one place where a literal DENY is *not* fail-closed is row 22, and it is the unresolved
upstream contradiction of §6.3 (B-F8, amendment A-14) rather than a decision this phase made.

### 13.1 Path A — daily rebalance

| # | Error path | Detected by | Fail-closed behaviour | Alarm |
|---|---|---|---|---|
| 1 | Market-data vendor unreachable at 21:45 | HTTP timeout / connection error | `INGEST` aborts non-zero. No order list. **No trading next session.** Backfill by `--trading-date` next day | CRITICAL |
| 2 | Vendor returns fewer symbols than the resolved universe | Row count vs universe membership | `INGEST` aborts. **Never impute the missing bars** `[CONST-6]` | CRITICAL |
| 3 | Vendor returns a provisional (non-final) daily aggregate | Unresolved — **Q-7** | Until Q-7 closes, `INGEST` treats a bar revised after write as a data-quality event and aborts the next pipeline | CRITICAL |
| 4 | FMP 30-day bandwidth exhausted mid-backfill | `429` or byte budget in the client (RULE-B5) | Backfill checkpoints and **pauses**; it does not restart and does not partially commit a quarter | WARN |
| 5 | Session calendar unresolvable | Calendar lookup returns no session | Job exits non-zero **rather than guessing** the session or the DST offset (ADR-02) | CRITICAL |
| 6 | Universe snapshot missing for the as-of date | `UNIVERSE_RESOLVE` finds no row | Abort. A guessed universe is a survivorship-bias event (I7) | CRITICAL |
| 7 | Model artifact missing or hash mismatch | Artifact hash vs registry | `TIER2_QUANT` aborts. **Never fall back to an older model silently** — that would change the strategy without champion/challenger (`[CONST-8]`) | CRITICAL |
| 8 | OpenAI (primary) **and** DeepSeek (fallback) both unavailable | Both clients exhaust retries | `TIER3_LLM` **DEGRADES**: candidates carry no thesis; any rule requiring a thesis emits NO-TRADE. Order count can only fall | WARN |
| 9 | LLM returns malformed or truncated JSON | Schema validation on the response | That candidate's thesis is **discarded**, not repaired. Treated as row 8 for that candidate | WARN |
| 10 | LLM stage exceeds 600 s | Stage deadline (RULE-B11) | DEGRADE, as row 8. In-flight calls are cancelled | WARN |
| 11 | DeepSeek keep-alive empty lines misread as EOF | Client-side; the failure is **silent** by construction | RULE-B11 forbids the naive client. A response that fails schema validation falls to row 9 | WARN |
| 12 | Risk engine raises | Exception in `RISK` | **DENY ALL** candidates. `[CONST-1]`, `[CONST-6]` | CRITICAL |
| 13 | Risk engine exceeds 60 s | Stage deadline | **DENY ALL** | CRITICAL |
| 14 | Audit write fails at any stage | Transaction error / fsync failure | **The action does not happen** `[CONST-5]`. For `AUDIT_FREEZE`, no order list exists and the session does not trade | CRITICAL |
| 15 | Audit hash chain broken or forked | Chain verification | **Hard stop.** No trading resumes; investigated as an integrity incident (ADR-10 clause 5) | CRITICAL |
| 16 | Postgres unreachable | Connection error | Every stage aborts. Nothing can be audited, therefore nothing may act `[CONST-5]` | CRITICAL |
| 17 | Redis unreachable | Connection error | Pipeline aborts. Redis holds no system-of-record state, but a cache miss must never become a silent data default | CRITICAL |
| 18 | Disk above `critical_pct` (85%) | Prometheus node exporter | New entries halted; ingest continues so the audit trail is never the thing that is dropped | CRITICAL |
| 19 | OOM during the pipeline | Kernel / container OOM kill | systemd `OnFailure=` fires; the run is not retried automatically within the session | CRITICAL |
| 20 | Clock skew or NTP failure | Drift check against the time source | Abort. Every deadline in §6 and every `timestamptz` in §14.5 is meaningless under skew | CRITICAL |
| 21 | Kill switch tripped (including restored TRIPPED on boot) | Kill-switch state read | **No stage past `UNIVERSE_RESOLVE` runs.** Re-enable is a human action with no auto-expiry (ADR-09, ADR-10, I3) | CRITICAL |
| 22 | Order window 14:15 passes with orders unplaced | Window deadline | **ABANDON.** Never placed late — the list was frozen against the prior bar (ADR-14) | WARN |

### 13.2 Path B — intraday exit

| # | Error path | Detected by | Fail-closed behaviour | Alarm |
|---|---|---|---|---|
| 23 | WebSocket disconnect | Socket close / error frame | Gap is **assumed lost** (rule N5). Reconcile the window from REST before resuming. New entries halted meanwhile | CRITICAL |
| 24 | WS symbol or connection limit exceeded (`405` / `406`) | Alpaca error code `[V]` | Monitor is a **singleton** by design; a second instance exits rather than evicting the first | CRITICAL |
| 25 | No bar for a held symbol for > 600 s | Staleness timer | CRITICAL; halt new entries; positions hold on **broker-side protective stops placed at entry** | CRITICAL |
| 26 | Trade correction (`c`) or cancel (`x`) after an exit was submitted | Message type | Recorded as an audit event. **The exit is not reversed** (RULE-B12) — a sale cannot be unwound | WARN |
| 27 | **Risk engine fails on an exit** | Exception or timeout in `RISK` | **UNRESOLVED — see §6.3 and A-14.** A literal `[CONST-6]` DENY would hold a position the exit logic decided to close. Until the Owner rules, the broker-side stop is the only backstop and the path is **not implementable** | CRITICAL |
| 28 | Broker rejects the order | Rejection code | No retry on a business rejection (insufficient settled cash, halted symbol, tick-size violation per N10). Escalate | CRITICAL |
| 29 | Broker returns `429` | HTTP status `[V]` | Back off with jitter inside the window; **never** widen the order window to compensate | WARN |
| 30 | Order ack never arrives | 5 s hard timeout | **Do not resubmit blind.** Reconcile against the broker order book first (N12 client-side dedupe) | CRITICAL |
| 31 | Broker-side stop cancelled by a corporate action | Alpaca cancels open GTC orders ahead of mandatory actions `[V]` | **CRITICAL event; the stop is re-placed**, never treated as a silent state change (N13) | CRITICAL |
| 32 | Broker and local positions disagree | Reconciliation | Position marked `UNRECONCILED`; **all new entries denied pool-wide** while any position is unreconciled (ADR-10 clause 2) | CRITICAL |

### 13.3 Budget-specific and operational

| # | Error path | Detected by | Fail-closed behaviour | Alarm |
|---|---|---|---|---|
| 33 | OOM during a backtest | Container OOM kill | The run fails and produces **no result**. A partial backtest must never be reported as a completed one — it would understate drawdown | WARN |
| 34 | Backup staging fails for want of disk | Base-backup exit code | CRITICAL. A base backup that cannot stage is a silent DR failure (§2.3) | CRITICAL |
| 35 | LLM spend crosses $5/month | Metered spend counter | WARN (RULE-B9). Investigate gate width, retries, peak drift, payload growth | WARN |
| 36 | LLM spend crosses $50/month | Metered spend counter | CRITICAL. Indicates a runaway loop or an unauthorised replay | CRITICAL |
| 37 | Full-history LLM replay attempted without approval | Replay job precondition check | **Job refuses to start** (RULE-B7) | WARN |
| 38 | Replay **routed to the DeepSeek fallback** scheduled inside its peak window | Job precondition check | Job refuses to start (RULE-B8, provider-conditional). Cost doubles, silently, otherwise. **Not applicable to a replay on the OpenAI primary**, which has no time-of-day pricing | WARN |
| 39 | A pipeline stage runs with no `StageBudget` configured | `BudgetConfig` validator (§14.4) | **The pipeline refuses to start.** An unbudgeted stage is an unbounded stage | CRITICAL |
| 40 | `monitor.subscribe_channels` set to anything but `("b",)` | `BudgetConfig` validator (§14.4) | Config rejected at load. Prevents the only open burst in the design from being reintroduced by configuration | CRITICAL |

---

## 14. Exported entities — models, DDL and field specifications

Block B: every entity gets a Pydantic v2 model or a SQL DDL block, and every field carries name,
type, unit, timezone, nullability, valid range, and what a violation means. Both follow for each
entity. All models are `frozen=True, extra="forbid"` — a budget that can be mutated at runtime is
not a budget, and an unrecognised key in a budget file is a typo that must fail loudly, not be
ignored.

**Timezone convention, stated once and applying to every field below.** There are exactly two
temporal kinds in this spec. `timestamptz` fields are **UTC at rest**, without exception.
`date` fields are **exchange-local session dates** — a session date is a calendar label owned by
P1.1's trading calendar, not an instant, and converting one to UTC is a category error. Every
duration field is a **plain number with an explicit unit in its name suffix** (`_seconds`, `_ms`,
`_days`, `_months`, `_gb`, `_pct`, `_usd_month`) and therefore carries no timezone at all.

### 14.1 Enumerations

```python
"""Budget contracts exported by SPEC-P0.3-BUDGET.

Consumed by P1.3 (config schema), P1.4 (audit), P2.x/P3.x (stage execution),
P6.1 (observability). Every stage that runs under a budget MUST resolve its
StageBudget from config and MUST apply `on_breach` when the budget is exceeded.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PipelineStage(StrEnum):
    INGEST = "INGEST"
    UNIVERSE_RESOLVE = "UNIVERSE_RESOLVE"
    TIER1_SCREEN = "TIER1_SCREEN"
    TIER2_QUANT = "TIER2_QUANT"
    INFERENCE_GATE = "INFERENCE_GATE"
    TIER3_LLM = "TIER3_LLM"
    DECISION = "DECISION"
    RISK = "RISK"
    AUDIT_FREEZE = "AUDIT_FREEZE"
    ORDER_PLACEMENT = "ORDER_PLACEMENT"
    MONITOR_EVAL = "MONITOR_EVAL"
    EXIT_SUBMIT = "EXIT_SUBMIT"


class BudgetBreachAction(StrEnum):
    """What happens when a stage exceeds its budget. Every value is fail-closed
    in the sense of CONST-6: none of them can cause an order that would not
    otherwise have been placed."""

    ABORT = "ABORT"                     # stop the run; no order list is produced
    DEGRADE = "DEGRADE"                 # continue with less information; TIER3_LLM only
    DENY_ALL = "DENY_ALL"               # risk engine verdict on every candidate
    RETRY_IN_WINDOW = "RETRY_IN_WINDOW"
    ABANDON = "ABANDON"                 # drop remaining work; never execute late
    ALERT_CRITICAL = "ALERT_CRITICAL"


class DiskClass(StrEnum):
    NVME_SSD = "NVME_SSD"
    SATA_SSD = "SATA_SSD"
    HDD = "HDD"
```

**`PipelineStage` — 12 values.** Path A runs stages 1–10 in the order listed; `MONITOR_EVAL` and
`EXIT_SUBMIT` are Path B only and never appear in a daily run.

| Value | Path | Meaning | A violation means |
|---|---|---|---|
| `INGEST` | A | EOD bars, corporate actions, fundamentals deltas | — |
| `UNIVERSE_RESOLVE` | A | Point-in-time membership as of the decision date | — |
| `TIER1_SCREEN` | A | Hard filters over the resolved universe | — |
| `TIER2_QUANT` | A | XGBoost/LightGBM scoring | — |
| `INFERENCE_GATE` | A | Select top-N for the LLM tier | — |
| `TIER3_LLM` | A | Gated LLM research, **the only degradable stage** | — |
| `DECISION` | A | Deterministic decision engine | — |
| `RISK` | A | Deterministic risk engine, overrides everything | — |
| `AUDIT_FREEZE` | A | Order list written, sealed, hash-chained | — |
| `ORDER_PLACEMENT` | A | Limit orders in the 13:45–14:15 UTC window | — |
| `MONITOR_EVAL` | B | Stop and exit-hierarchy evaluation on a completed 5-min bar | — |
| `EXIT_SUBMIT` | B | Exit order submission | — |
| *any other string* | — | — | An unknown stage is an **unbudgeted** stage; `BudgetConfig` refuses to load (row 39) |

**`BudgetBreachAction` — 6 values.**

| Value | Applies to | Meaning | A violation means |
|---|---|---|---|
| `ABORT` | Any Path-A stage | Stop the run; no order list is produced | — |
| `DEGRADE` | **`TIER3_LLM` only** | Continue with less information; order count can only fall | Used on any other stage → validator raises; it would make an optional tier load-bearing |
| `DENY_ALL` | `RISK` | Every candidate denied | — |
| `RETRY_IN_WINDOW` | `ORDER_PLACEMENT` | Retry inside the existing window, never by extending it | — |
| `ABANDON` | `ORDER_PLACEMENT` | Drop remaining orders at the deadline | — |
| `ALERT_CRITICAL` | Path B stages | Raise and hold on broker-side stops | — |

**`DiskClass` — 3 values.** `NVME_SSD` is the specified class (§4.3). `SATA_SSD` still clears the
0.5% utilisation figure of §3.2 with margin; `HDD` does not clear the fsync requirement of §3.3
and is recorded only so the enum can express a misconfiguration rather than silently accept one.

### 14.2 `StageBudget`

```python
class StageBudget(BaseModel):
    """A wall-clock budget for one pipeline stage, plus its breach behaviour.

    A stage with no StageBudget MUST NOT run: an unbudgeted stage is an
    unbounded stage, and an unbounded stage can hold the pipeline past its
    clock deadline (CONST-6)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: PipelineStage
    budget_seconds: Annotated[Decimal, Field(gt=0, le=7200)]
    hard_timeout_seconds: Annotated[Decimal, Field(gt=0, le=7200)]
    on_breach: BudgetBreachAction
    rationale: Annotated[str, Field(min_length=10, max_length=500)]

    @model_validator(mode="after")
    def _hard_timeout_not_below_budget(self) -> "StageBudget":
        if self.hard_timeout_seconds < self.budget_seconds:
            raise ValueError(
                f"{self.stage}: hard_timeout_seconds "
                f"({self.hard_timeout_seconds}) < budget_seconds "
                f"({self.budget_seconds}); a hard timeout below the budget "
                f"makes the budget unreachable"
            )
        return self

    @model_validator(mode="after")
    def _only_llm_may_degrade(self) -> "StageBudget":
        # SPEC-P0.3 §6.1 decision 8: TIER3_LLM is the single stage permitted to
        # continue on breach, because ADR-13 Chain G excludes the LLM tier from
        # the promotable strategy. Any other stage degrading would make an
        # optional tier load-bearing.
        if (
            self.on_breach is BudgetBreachAction.DEGRADE
            and self.stage is not PipelineStage.TIER3_LLM
        ):
            raise ValueError(
                f"{self.stage}: DEGRADE is permitted only for TIER3_LLM "
                f"(SPEC-P0.3 §6.1 decision 8)"
            )
        return self
```

| Field | Type | Unit | Timezone | Nullable | Valid range | What a violation means |
|---|---|---|---|---|---|---|
| `stage` | `PipelineStage` | — | n/a | No | one of the 12 values | An unknown stage is unbudgeted; the pipeline refuses to start (row 39) |
| `budget_seconds` | `Decimal` | seconds | n/a | No | `(0, 7200]` | `≤0` is breached the instant it starts. `>7200` exceeds the longest stage in §6 by 4× and indicates a copied-in wrong unit (minutes for seconds) |
| `hard_timeout_seconds` | `Decimal` | seconds | n/a | No | `[budget_seconds, 7200]` | Below `budget_seconds` the budget can never be reached and the breach action can never fire — validator raises |
| `on_breach` | `BudgetBreachAction` | — | n/a | No | one of the 6 values | `DEGRADE` on any stage but `TIER3_LLM` makes an optional tier load-bearing — validator raises |
| `rationale` | `str` | — | n/a | No | 10–500 characters | A budget with no stated reason cannot be reviewed by an auditor, which is the whole point of writing it down |

### 14.3 `CostLine`

```python
class CostLine(BaseModel):
    """One line of the monthly cost model. `monthly_usd is None` means the price
    is genuinely unknown and is carried in OPEN QUESTIONS -- it is never
    defaulted to zero, because a zero would silently understate the total
    (CONST-6: never default a missing value)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=120)]
    monthly_usd: Annotated[Decimal, Field(ge=0, le=100_000)] | None
    verified: bool
    open_question_id: Annotated[str, Field(pattern=r"^Q-\d+$")] | None = None

    @model_validator(mode="after")
    def _unknown_price_needs_a_question(self) -> "CostLine":
        if self.monthly_usd is None and self.open_question_id is None:
            raise ValueError(
                f"{self.name}: an unpriced line must name the OPEN QUESTION "
                f"that resolves it"
            )
        if self.monthly_usd is None and self.verified:
            raise ValueError(f"{self.name}: an unpriced line cannot be verified")
        return self
```

| Field | Type | Unit | Timezone | Nullable | Valid range | What a violation means |
|---|---|---|---|---|---|---|
| `name` | `str` | — | n/a | No | 1–120 characters | An unnamed cost line cannot be reconciled against an invoice |
| `monthly_usd` | `Decimal` | USD per month | n/a | **Yes — `None` means genuinely unknown** | `[0, 100000]` | `None` is the *only* representation of an unknown price. A `0` for an unknown silently understates the total, which is exactly the defaulting `[CONST-6]` forbids. The `100000` ceiling catches a per-year figure entered as per-month |
| `verified` | `bool` | — | n/a | No | `true` / `false` | `True` alongside `monthly_usd is None` claims verification of something unknown — validator raises |
| `open_question_id` | `str` | — | n/a | Yes | `^Q-\d+$` | An unpriced line without one cannot be traced to the query that resolves it — validator raises. A malformed id cannot be looked up in OPEN QUESTIONS |

### 14.4 Budget and latency configuration

The configuration keys this phase defines are **entities, not prose**, so they get a model. P1.3
owns the file format and loading; the shape below is what it must produce.

```python
class DiskAlarms(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    # Fractions, not integer percent: P0.1 uses `_pct` to mean a fraction
    # (portfolio.max_position_pct = 0.050). Two conventions in one config
    # namespace is a bug generator, and `70` misread as a fraction is 7000%.
    warn_pct: Annotated[Decimal, Field(gt=0, lt=1)]
    critical_pct: Annotated[Decimal, Field(gt=0, lt=1)]

    @model_validator(mode="after")
    def _warn_below_critical(self) -> "DiskAlarms":
        if self.warn_pct >= self.critical_pct:
            raise ValueError(
                f"warn_pct ({self.warn_pct}) must be below critical_pct "
                f"({self.critical_pct}); a warning that fires with or after "
                f"the critical alarm gives no lead time"
            )
        return self


class VmSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    vcpu: Annotated[int, Field(ge=1, le=64)]
    ram_gb: Annotated[int, Field(ge=1, le=1024)]
    disk_gb: Annotated[int, Field(ge=1, le=10_000)]
    disk_class: DiskClass
    static_egress_ips: Annotated[int, Field(ge=1, le=2)]


class StoragePolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    compression_after_days: Annotated[int, Field(ge=1, le=365)]
    expected_compression_ratio_numeric: Annotated[Decimal, Field(ge=1, le=100)]
    expected_compression_ratio_text: Annotated[Decimal, Field(ge=1, le=100)]


class ExitLatencyPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    bar_to_ack_budget_seconds: Annotated[Decimal, Field(gt=0, le=300)]
    bar_to_ack_hard_seconds: Annotated[Decimal, Field(gt=0, le=300)]
    stale_bar_critical_seconds: Annotated[int, Field(ge=60, le=3600)]
    audit_write_budget_ms: Annotated[int, Field(ge=1, le=10_000)]
    audit_write_hard_ms: Annotated[int, Field(ge=1, le=10_000)]

    @model_validator(mode="after")
    def _hard_deadlines_exceed_budgets(self) -> "ExitLatencyPolicy":
        if self.bar_to_ack_hard_seconds < self.bar_to_ack_budget_seconds:
            raise ValueError("bar_to_ack_hard_seconds is below its budget")
        if self.audit_write_hard_ms < self.audit_write_budget_ms:
            raise ValueError("audit_write_hard_ms is below its budget")
        return self


class LlmCostPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gate_width: Annotated[int, Field(ge=1, le=1500)]
    cost_per_call_usd: Annotated[Decimal, Field(gt=0, le=1)]
    spend_alarm_warn_usd_month: Annotated[Decimal, Field(gt=0, le=10_000)]
    spend_alarm_critical_usd_month: Annotated[Decimal, Field(gt=0, le=10_000)]
    replay_requires_approval: bool
    replay_offpeak_only: bool
    # RULE-B9: the alarm window is trailing and rolling, never a calendar
    # month, and approved replay spend is excluded -- otherwise one $87
    # replay pins CRITICAL on for the whole window and masks a live-path
    # regression underneath it.
    spend_window_days: Annotated[int, Field(ge=1, le=90)]
    spend_excludes_approved_replay: bool

    @model_validator(mode="after")
    def _alarms_and_immutables(self) -> "LlmCostPolicy":
        if self.spend_alarm_warn_usd_month >= self.spend_alarm_critical_usd_month:
            raise ValueError(
                "spend_alarm_warn_usd_month must be below "
                "spend_alarm_critical_usd_month"
            )
        # RULE-B7 and RULE-B8 are not tunable. They exist because replay is the
        # only activity that reaches the $200-500/month ceiling (SPEC-P0.3 B-F3).
        if not self.replay_requires_approval:
            raise ValueError("replay_requires_approval is immutable true (RULE-B7)")
        if not self.replay_offpeak_only:
            raise ValueError("replay_offpeak_only is immutable true (RULE-B8)")
        if not self.spend_excludes_approved_replay:
            raise ValueError(
                "spend_excludes_approved_replay is immutable true (RULE-B9): "
                "one approved replay would otherwise pin the CRITICAL alarm "
                "on for the whole window and hide a live-path regression"
            )
        return self


class BudgetConfig(BaseModel):
    """Root of the SPEC-P0.3 configuration namespace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vm: VmSpec
    disk_alarms: DiskAlarms
    backup_offvm_gb_estimate: Annotated[int, Field(ge=1, le=100_000)]
    # A tuple, not a dict keyed by stage: `frozen=True` stops attribute
    # reassignment but would NOT stop `cfg.stage_budgets[RISK] = ...` on a dict.
    # A budget that can be mutated at runtime is not a budget. Each StageBudget
    # already carries its own `stage`, so a keyed mapping was redundant anyway.
    stage_budgets: tuple[StageBudget, ...]
    exit_latency: ExitLatencyPolicy
    llm: LlmCostPolicy
    storage: StoragePolicy
    monitor_subscribe_channels: tuple[str, ...]
    walkforward_roll_months: Annotated[int, Field(ge=1, le=24)]
    cost_lines: tuple[CostLine, ...]

    # Every stage that runs in the daily pipeline. MONITOR_EVAL and EXIT_SUBMIT
    # are Path B and are governed by ExitLatencyPolicy instead.
    _PATH_A_STAGES = (
        PipelineStage.INGEST,
        PipelineStage.UNIVERSE_RESOLVE,
        PipelineStage.TIER1_SCREEN,
        PipelineStage.TIER2_QUANT,
        PipelineStage.INFERENCE_GATE,
        PipelineStage.TIER3_LLM,
        PipelineStage.DECISION,
        PipelineStage.RISK,
        PipelineStage.AUDIT_FREEZE,
        PipelineStage.ORDER_PLACEMENT,
    )

    @model_validator(mode="after")
    def _every_path_a_stage_is_budgeted(self) -> "BudgetConfig":
        held = {b.stage for b in self.stage_budgets}
        missing = [s for s in self._PATH_A_STAGES if s not in held]
        if missing:
            raise ValueError(
                f"unbudgeted Path-A stages {[s.value for s in missing]}; "
                f"an unbudgeted stage is an unbounded stage and may not run"
            )
        return self

    @model_validator(mode="after")
    def _no_duplicate_stage_budgets(self) -> "BudgetConfig":
        seen = [b.stage for b in self.stage_budgets]
        duplicated = sorted({s.value for s in seen if seen.count(s) > 1})
        if duplicated:
            raise ValueError(
                f"duplicate budgets for stages {duplicated}; which deadline "
                f"applies would depend on iteration order"
            )
        return self

    def budget_for(self, stage: PipelineStage) -> StageBudget:
        """The budget a stage runs under. Raises rather than returning None:
        a stage with no budget must not run (SPEC-P0.3 section 13 row 39)."""
        for budget in self.stage_budgets:
            if budget.stage is stage:
                return budget
        raise KeyError(
            f"no StageBudget configured for {stage.value}; an unbudgeted "
            f"stage is an unbounded stage and may not run"
        )

    @model_validator(mode="after")
    def _monitor_never_subscribes_to_trades(self) -> "BudgetConfig":
        # SPEC-P0.3 decision 12: subscribing to `t` recreates the only market-open
        # burst in the design (500-5,000 msg/s) for no signal benefit.
        if self.monitor_subscribe_channels != ("b",):
            raise ValueError(
                f"monitor_subscribe_channels must be exactly ('b',), got "
                f"{self.monitor_subscribe_channels}; trade-level subscription "
                f"reintroduces the market-open burst (SPEC-P0.3 decision 12)"
            )
        return self
```

| Field | Type | Unit | Timezone | Nullable | Valid range | What a violation means |
|---|---|---|---|---|---|---|
| `vm.vcpu` | `int` | cores | n/a | No | 1–64 | Below 4 the walk-forward wall-clock of §7 no longer holds |
| `vm.ram_gb` | `int` | GB (10⁹ B) | n/a | No | 1–1024 | **The binding resource.** Below 16 forces a chunked backtest (§4.2) |
| `vm.disk_gb` | `int` | GB (10⁹ B) | n/a | No | 1–10000 | Below 128 breaches the 70% fill rule before year 10 (§2.3) |
| `vm.disk_class` | `DiskClass` | — | n/a | No | 3 values | `HDD` fails the fsync requirement of §3.3 |
| `vm.static_egress_ips` | `int` | count | n/a | No | 1–2 | Zerodha registers **at most 2** `[V]`; 0 breaks India order placement from 2026-04-01 |
| `disk_alarms.warn_pct` | `Decimal` | **fraction of the Postgres data volume**, not integer percent | n/a | No | `(0, 1)`, `< critical_pct` | Warning at or above critical gives no lead time — validator raises. Integer `70` here reads as 7,000% and never fires (§15.1) |
| `disk_alarms.critical_pct` | `Decimal` | fraction, as above | n/a | No | `(0, 1)` | Above `0.85` leaves no room to stage a base backup (§2.3) |
| `backup_offvm_gb_estimate` | `int` | GB (10⁹ B) | n/a | No | 1–100000 | Feeds Q-2's pricing query; an estimate of 0 hides the line |
| `stage_budgets` | `tuple[StageBudget, ...]` | — | n/a | No | must cover all 10 Path-A stages, no duplicates | A missing stage is an unbounded stage — validator raises (row 39). A duplicate makes the applied deadline depend on iteration order — validator raises. A `dict` was rejected here because `frozen=True` does not prevent mutating a dict field |
| `exit_latency.bar_to_ack_budget_seconds` | `Decimal` | seconds | n/a | No | `(0, 300]`, `≤ hard` | Above the 300 s 5-minute bar interval, stop evaluation is meaningless |
| `exit_latency.bar_to_ack_hard_seconds` | `Decimal` | seconds | n/a | No | `(0, 300]` | Below the budget the budget is unreachable — validator raises |
| `exit_latency.stale_bar_critical_seconds` | `int` | seconds | n/a | No | 60–3600 | Below 300 a single missed bar false-alarms; above 900 a blind monitor goes unnoticed for three intervals |
| `exit_latency.audit_write_budget_ms` | `int` | milliseconds | n/a | No | 1–10000 | — |
| `exit_latency.audit_write_hard_ms` | `int` | milliseconds | n/a | No | 1–10000, `≥ budget` | Below the budget — validator raises |
| `llm.gate_width` | `int` | candidates per session | n/a | No | 1–1500 | Capped at the universe size; above it the gate is not a gate. **Set by ADR-13, not by P0.3** (B-F2) |
| `llm.cost_per_call_usd` | `Decimal` | USD per call | n/a | No | `(0, 1]` | Above $1 the §5 arithmetic is wrong by ~430× and the alarms are miscalibrated |
| `llm.spend_alarm_warn_usd_month` | `Decimal` | USD per month | n/a | No | `(0, 10000]`, `< critical` | At or above critical it never fires first — validator raises |
| `llm.spend_alarm_critical_usd_month` | `Decimal` | USD per month | n/a | No | `(0, 10000]` | — |
| `llm.replay_requires_approval` | `bool` | — | n/a | No | **`true`, immutable** | `false` re-opens the only path to the $200–500 ceiling — validator raises (RULE-B7) |
| `llm.replay_offpeak_only` | `bool` | — | n/a | No | **`true`, immutable** | `false` doubles replay cost silently — validator raises (RULE-B8) |
| `llm.spend_window_days` | `int` | days | **UTC, trailing and rolling — never a calendar month** | No | 1–90 | A calendar reset means a gate widened on the 28th needs 30 further days to trip (RULE-B9) |
| `llm.spend_excludes_approved_replay` | `bool` | — | n/a | No | **`true`, immutable** | `false` lets one approved $87 replay hold CRITICAL on for the whole window and mask a live-path regression — validator raises (RULE-B9) |
| `storage.compression_after_days` | `int` | days | n/a | No | 1–365 | Above 365 nothing ever compresses and §2.3's 9.7 GB becomes 39.9 GB |
| `storage.expected_compression_ratio_numeric` | `Decimal` | ratio (×) | n/a | No | 1–100 | Used only to alarm when measured compression diverges (RULE-B2) |
| `storage.expected_compression_ratio_text` | `Decimal` | ratio (×) | n/a | No | 1–100 | As above, for the audit and news tables |
| `monitor_subscribe_channels` | `tuple[str, ...]` | — | n/a | No | **exactly `("b",)`** | Any other value, `("t",)` above all, reintroduces the market-open burst — validator raises (row 40) |
| `walkforward_roll_months` | `int` | months | n/a | No | 1–24 | `6` yields only 16 windows from 10 years and fails ADR-08 (B-F4). **Pending Q-9** |
| `cost_lines` | `tuple[CostLine, ...]` | — | n/a | No | each a valid `CostLine` | An unpriced line without an OPEN QUESTION id is an invented zero — `CostLine` raises |

**Key-path mapping for P1.3.** The dotted keys downstream phases cite map to model fields as
`budget.vm.*` → `BudgetConfig.vm`, `budget.disk.{warn,critical}_pct` → `BudgetConfig.disk_alarms`,
`budget.backup.offvm_gb_estimate` → `BudgetConfig.backup_offvm_gb_estimate`,
`budget.monthly_usd.*` → `BudgetConfig.cost_lines`,
`latency.stage_budget_s.<STAGE>` → `BudgetConfig.budget_for(<STAGE>).budget_seconds` — P1.3's
loader may accept a stage-keyed map in the config file, but it must cross-check each map key
against the entry's own `stage` field and reject a mismatch rather than trusting either alone;
`latency.exit.*` and `latency.audit.*` → `BudgetConfig.exit_latency`,
`llm.*` → `BudgetConfig.llm`, `storage.*` → `BudgetConfig.storage`,
`monitor.subscribe_channels` → `BudgetConfig.monitor_subscribe_channels`,
`backtest.walkforward.roll_months` → `BudgetConfig.walkforward_roll_months`.

**Bound values, from §6.1, §6.2, §4.3, §5.5 and §2.3.** `vm` = 4 / 16 / 250 / `NVME_SSD` / 2.
`disk_alarms` = `0.70` / `0.85` (fractions). `backup_offvm_gb_estimate` = 300. `stage_budgets` = `INGEST` 1800,
`UNIVERSE_RESOLVE` 30, `TIER1_SCREEN` 120, `TIER2_QUANT` 120, `INFERENCE_GATE` 30, `TIER3_LLM` 600,
`DECISION` 60, `RISK` 60, `AUDIT_FREEZE` 60, `ORDER_PLACEMENT` 5 (hard 30). `exit_latency` =
5 / 10 / 600 / 50 / 500. `llm` = 15 / **0.00300** (AD-5 primary) / 5.00 / 50.00 / true / true / 30 / true. `storage` = 30 / 15 / 4.
`monitor_subscribe_channels` = `("b",)`. `walkforward_roll_months` = **3, decided by AD-2** (Q-9 closed).

### 14.5 SQL DDL — `stage_latency_observation`

```sql
-- A latency budget nobody measures is a wish. Every stage listed in
-- SPEC-P0.3 §6 writes one row per execution; P6.1 alerts on the p95 of
-- observed_seconds against budget_seconds, and P5.5 (chaos) asserts that
-- breach_action_taken matches the configured on_breach.
CREATE TABLE stage_latency_observation (
    observation_id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
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
    CONSTRAINT finished_after_started
        CHECK (finished_at >= started_at),
    -- A breach with no recorded action means the budget was decorative.
    CONSTRAINT breach_implies_action
        CHECK (NOT breached OR breach_action_taken IS NOT NULL),
    CONSTRAINT action_implies_breach
        CHECK (breach_action_taken IS NULL OR breached),
    -- DEGRADE is reserved to TIER3_LLM in the database as well as in the model,
    -- so a bug in the application cannot record an unpermitted degradation.
    CONSTRAINT degrade_is_llm_only
        CHECK (breach_action_taken IS DISTINCT FROM 'DEGRADE'
               OR stage = 'TIER3_LLM')
);

CREATE INDEX stage_latency_observation_stage_date_idx
    ON stage_latency_observation (stage, trading_date DESC);

-- P1.2 converts this to a TimescaleDB hypertable on started_at with a
-- 7-day chunk interval; it is low-volume (~12 rows/session) and is NOT a
-- material line in the storage budget of SPEC-P0.3 §2.
```

| Field | Type | Unit | Timezone | Nullable | Valid range | What a violation means |
|---|---|---|---|---|---|---|
| `observation_id` | `bigint` identity | — | n/a | No | ≥ 1, generated | — |
| `market` | `text` | — | n/a | No | `'US'`, `'IN'` | A third value means P0.1's `Market` enum drifted from the database |
| `trading_date` | `date` | — | **exchange-local session date, never UTC** | No | a session on P1.1's calendar | Storing a UTC calendar date here mislabels every US session that starts after 19:00 ET — the classic off-by-one that makes a whole day of latency data unattributable |
| `stage` | `text` | — | n/a | No | the 12 `PipelineStage` values | An unknown stage means an unbudgeted stage ran (row 39) |
| `started_at` | `timestamptz` | — | **UTC at rest** | No | `≤ finished_at` | — |
| `finished_at` | `timestamptz` | — | **UTC at rest** | No | `≥ started_at` | A negative duration means a clock step during the stage; §13 row 20 halts on skew for exactly this reason |
| `observed_seconds` | `numeric(12,3)` | seconds | n/a | No | `≥ 0` | — |
| `budget_seconds` | `numeric(12,3)` | seconds | n/a | No | `> 0` | Recorded per row, not looked up later, so a budget change cannot silently rewrite history |
| `breached` | `boolean` | — | n/a | No | `true` / `false` | — |
| `breach_action_taken` | `text` | — | n/a | **Yes — NULL if and only if `breached` is false** | the 6 `BudgetBreachAction` values | Null with `breached` true means the budget was **decorative**; non-null with `breached` false means an action fired without cause. Both are rejected by CHECK constraints. `'DEGRADE'` on any stage but `TIER3_LLM` is rejected by `degrade_is_llm_only` |
| `strategy_version` | `text` | — | n/a | No | non-empty | I6 requires every order to carry `strategy_version`; latency must be attributable to the same version or a regression cannot be traced to a release |

**DDL verification status.** This block has **not** been executed — no PostgreSQL instance and no
SQL parser was available in the authoring environment. It is `[U]` until P1.2 runs it as a
migration. The Pydantic models in §14.1–14.4 **were** executed and their validators exercised.

---

## 15. Binding rules exported, each with its edge case

Block C: *a rule without its edge case is not finished.* v0.2 shipped twelve unfinished rules —
bare statements with no boundary behaviour. Writing the edge cases out found **eight defects in the
rules themselves**, marked **FIXED IN v0.3** below. They are corrections to this document, not to
anything upstream.

| # | Rule | Edge case resolved |
|---|---|---|
| **B1** | No phase sizes the VM, disk class or Postgres config against ingest write throughput | **Dual-market does not change this.** When ADR-11's India gate opens, the NSE close (10:00 UTC) and the US EOD load (21:45 UTC) are 11.75 h apart, so the two batch loads can never coincide and the combined worst minute stays the single-market figure of §3.2. The rule is void only if some phase introduces a streaming ingest path — which ADR-13 Chain A forecloses — and any phase proposing one must re-derive §3 rather than reuse it |
| **B2** | Compression ratio and backtest wall-clock are **measured**, not assumed forever | **FIXED IN v0.3 — v0.2 said "after month 1", which is an off-by-one against its own compression policy.** `storage.compression_after_days` is 30 `[DEFAULT-B10]`, so on day 30 the oldest chunk has only just become *eligible*; `hypertable_compression_stats()` can legitimately report zero compressed chunks and a naive reading would record a 1× ratio. Corrected rule: **measure at day 45**, and require **≥3 compressed chunks** before treating the ratio as representative. If the policy is later set to 7 days, measure at day 22 under the same ≥3-chunk rule. Second edge case: **backfilled chunks compress better than live-written ones** because they arrive fully sorted, so the ratio is measured on live-written chunks only — measuring on the 10-year backfill would overstate compression and undersize the disk |
| **B3** | P1.2 chooses `numeric` or `float8` for OHLC **explicitly**, against P1.1's `Decimal` mandate | **`numeric` must be declared with precision and scale.** Bare `numeric` is unbounded-precision and defeats TimescaleDB's numeric compression path, turning §2.2's 15× into something far worse; `numeric(12,4)` or similar is required, and the scale must accommodate the sub-penny tick regime that F-10 brings from November 2027. Second edge case: **the same choice must apply to the bar table and to any materialised feature view**, or §2.2 double-counts at two different row widths |
| **B4** | Audit writes for **actions** are individually durable; **evaluations** may be batched | Three boundaries. (a) **An evaluation that becomes the reason for an action is promoted to action class** — the Tier-1 row for a name that gets selected is written durably before the decision that cites it, because at that point it is evidence, not a scan result. (b) **A batch that fails midway is discarded and retried whole**, never partially applied: a half-written screen is not a screen, and a gap in the evaluation record would be indistinguishable from a name that was never screened. (c) **All batches flush before `AUDIT_FREEZE`** — no evaluation may still be buffered when the order list seals, or the sealed hash covers a record that is still in memory |
| **B5** | The FMP client carries a **byte budget** as well as a rate limiter; backfill is resumable | **The 30-day window is trailing and rolling, not calendar** `[V]`. Bytes spent on day 1 free up on day 31, so the client tracks a rolling 30-day sum rather than resetting on the 1st — a calendar reset would permit 100 GB across a month boundary. Second edge case: **the client's byte count is an estimate**, since it observes `Content-Length` and not FMP's own accounting, so it reserves a 20% margin and stops at **40 GB**, not 50. Third: **backfill checkpoints at (symbol, fiscal quarter) granularity**, so a stall never leaves a symbol holding a half-written quarter that a later run would read as complete |
| **B6** | The 1-minute full-universe backtest frame is **708 GB** — intraday is closed on RAM, not price | **The conclusion is insensitive to the feature count, and that must be stated or it will be argued.** 708 GB assumes `[DEFAULT-B5]` 60 features. At 30 features it is 354 GB; at 15 it is 177 GB — still **11× a 16 GB VM**. There is no feature count in the plausible range that makes full-universe 1-minute backtesting fit a single VM, so "we will use fewer features" is not an escape route |
| **B7** | Full-history LLM replay requires **owner approval** | **FIXED IN v0.3 — v0.2 never defined "full-history", so the guard was trivially evadable** by replaying 2,519 of 2,520 sessions. The guard is redefined on **cost, not scope**: any LLM job whose **projected** spend — `calls × cost_per_call_usd`, computed before the first call — exceeds `llm.spend_alarm_warn_usd_month` ($5.00) requires approval. At the AD-5 primary's $0.00300/call that captures a full replay ($113.40), captures a 200-session partial ($9.00), leaves a single-date sweep of all 1,500 names ($4.50 — below the threshold, and correctly so, though the margin narrowed from $1.54 to $0.50 when the primary changed), and lets a 20-call debugging run ($0.06) proceed unimpeded. Second edge case: **a job that cannot compute its own projected call count refuses to start**, because an unbounded job is exactly the runaway the alarm exists to catch |
| **B8** | Replay jobs run **off-peak** (outside Mon–Fri 01:00–04:00 and 06:00–10:00 UTC) `[V]` | **FIXED IN v0.3 — v0.2 checked only the start time, so a replay beginning at 00:30 UTC on a Tuesday ran into peak at 01:00 and silently paid double.** Corrected rule: the job computes projected wall-clock as `calls ÷ concurrency × mean_call_seconds × 1.5` and **refuses to start if the projected window intersects a peak window**. Second edge case: a job still running when a peak window opens **pauses at the next call boundary and resumes at 04:00 or 10:00 UTC** — it does not abort, because aborting wastes the spend already incurred and the cache entries already earned. Third: **peak is Mon–Fri only** `[V]`, so a weekend replay needs no window arithmetic at all, and the weekend is therefore the default slot |
| **B9** | LLM spend alarms are **two-tier**: WARN $5, CRITICAL $50 | **FIXED IN v0.3 — v0.2 left the window, the timezone, the basis and the scope all undefined.** (a) **Trailing 30-day rolling window in UTC, not a calendar month**: a calendar reset means a gate that widened on the 28th needs 30 further days to trip. (b) **Basis is metered, not invoiced** — our own summed `usage` × the price in force at call time — because the vendor invoice arrives after the month it should have warned about. (c) **Off-peak and peak calls are priced at the rate in force when the call was made**, never at a blended monthly rate. (d) **Approved replay spend is excluded from the counter, tagged by job id** — otherwise a single approved $87 replay pins CRITICAL on for 30 days and masks a genuine live-path regression underneath it. That exclusion is the one that matters: without it the alarm is useless for exactly the month in which something interesting happened |
| **B10** | `TIER3_LLM` is the **only** stage permitted to degrade rather than abort | **Degradation is per candidate, never per stage.** If 12 of 15 calls return and 3 time out, the 12 keep their theses and the 3 are treated as no-thesis; the stage does not discard the 12. Second edge case: **zero returns is still DEGRADE, not ABORT** — it is identical in kind to all 15 timing out, and ADR-13 Chain G's exclusion of the LLM tier from the promotable strategy holds regardless of how many calls failed. Third: a candidate whose thesis fails schema validation is a no-thesis candidate, **never a repaired one** (§13 row 9) |
| **B11** | Gate calls are **concurrent**, 120 s per-call timeout, 600 s stage deadline; the client must not treat DeepSeek's keep-alive empty lines as EOF `[V]` | **Concurrency is `min(gate_width, 25)`, not a fixed 15**, so a change to `llm.gate_width` cannot silently serialise the stage past its deadline; DeepSeek's 2,500-connection limit `[V]` is never the binding constraint at any gate width the universe permits. Second edge case: **exactly one retry fits** — 120 s + 120 s plus backoff jitter sits inside the 600 s deadline, a second retry does not, so a second is refused rather than attempted and truncated. Third: **a retry opens a fresh connection**, because the documented failure mode is a connection on which inference never starts `[V]`; reusing it retries into the same stall |
| **B12** | The monitor subscribes to **`b` only**, acts on **completed bars only**, and never reverses a submitted exit on a late correction | **FIXED IN v0.3 — v0.2 never defined "completed".** A 5-minute bar is completed when a bar with a **later window-start** arrives, or when the window end plus the 3 s delivery budget has passed on the wall clock — **whichever comes first**, except that wall-clock completion alone never fires while the feed is silent, because that is the staleness case (§13 row 25), not a completed bar. Four boundaries follow. (a) **The 16:00 ET closing bar** has no successor to confirm it, so it completes on P1.1's session-close event. (b) **Half-days** (13:00 ET) are identical on the early-close event; the final 12:55–13:00 bar is full length, not a stub. (c) **A halted symbol emits no bars, and a halt is not staleness** — the stale-bar timer is **suspended** while the calendar reports the symbol halted and resumes on the resume print. Without this suspension a routine halt raises a false CRITICAL and blocks new entries pool-wide, which is a self-inflicted outage. (d) **Whether the vendor emits a zero-trade bar or omits the window entirely is not documented** on any page P0.2 retrieved — **Q-12**. Until it closes, an omitted bar is indistinguishable from a lost one and counts toward the stale timer unless the symbol is halted, which is the fail-closed reading |

### 15.1 Threshold edge cases — every number in this document that a rule compares against

Block C names timezones, rounding, off-by-one on windows, DST, half-days, the unit of a
percentage, integer versus decimal money, and inclusive versus exclusive bounds. Each is resolved
here for the thresholds this phase defines.

| Threshold | Value | Edge case resolved |
|---|---|---|
| **Unit of a percentage** | — | **FIXED IN v0.3.** v0.2 declared `warn_pct: int = 70`. P0.1's config uses `_pct` to mean a **fraction** — `portfolio.max_position_pct = 0.050`, `portfolio.min_cash_pct = 0.20`. Two conventions in one namespace is a bug generator, and the failure is silent in the dangerous direction: a `0.70` read as 70% is harmless, a `70` read as a fraction is 7,000%. v0.3 **matches P0.1**: `warn_pct` and `critical_pct` are `Decimal` fractions, `0.70` and `0.85` |
| Disk WARN / CRITICAL | 0.70 / 0.85 | Of the **PostgreSQL data volume**, not `/` and not the sum of all mounts. Sampled every 60 s, evaluated on a **5-minute median** so the transient ~1× spike while a base backup stages (§2.3) does not page a human at 02:00. Comparison is **inclusive** (`>=`) |
| Stage budget breach | per §6.1 | **Exclusive** (`observed > budget`). A stage finishing at exactly its budget is not breached — otherwise every budget is effectively one tick tighter than written |
| Stale bar | 600 s | Wall clock since the **last received message for that symbol**, not derived from bar-window arithmetic, so a feed that goes quiet is caught even if our clock and the vendor's disagree. **Suspended during a halt** (B12c). Per symbol, but CRITICAL is raised **once per symbol per session** to prevent an alert storm from 25 simultaneously stale symbols |
| Exit latency budget | 5 s / 10 s | Measured from the **bar window end**, not from message receipt — receipt-relative timing would hide vendor delay, which is the largest and least controllable term (§6.2 stage 1) |
| LLM spend | $5 / $50 | Trailing 30 days, UTC, metered, replay-excluded — B9 above |
| `cost_per_call_usd` | $0.00300 | **Money is `Decimal`, never float**, per P1.1. Per-call cost is quantised to **6 decimal places**; rounding to cents would quantise $0.00300 to $0.00 and zero the entire spend model. Monthly totals are **stored at 6 dp and displayed at 2**, and the display rounding mode is **`ROUND_HALF_UP`, stated explicitly** because Python's `Decimal` defaults to `ROUND_HALF_EVEN`: $3.465 displays as $3.47 under the former and $3.46 under the latter, and a spec that leaves the mode unstated will disagree with its own implementation at every half-way value |
| `observed_seconds` | `numeric(12,3)` | Milliseconds, **truncated toward zero, never rounded**, so a stage can never be recorded as faster than it ran. A 12-digit precision covers 31 years of seconds — the column can never overflow before the retention policy discards the row |
| Order-window abandon | 14:15 UTC EDT / 15:15 EST | **DST is resolved by two timer definitions selected from P1.1's calendar, never one local-time timer** (ADR-02). A job that cannot resolve the calendar exits non-zero rather than guessing which offset applies. **Half-days do not move this window** — ADR-14 fixes the order window at 09:45–10:15 ET on every session that is open at all; half-days move the ingest and pipeline timers, not this one |
| Partial fill at 14:15 | — | See `[DEFAULT-B10]` in §11: the unfilled remainder is **cancelled**, and the protective stop is placed on the **filled quantity**, not the intended quantity |
| Compression measurement | day 45, ≥3 chunks | B2 above |
| FMP byte budget | 40 GB of 50 GB | B5 above — trailing rolling window with a 20% estimation margin |
| `gate_width` upper bound | 1,500 | **Inclusive.** A gate equal to the universe is degenerate but representable, and §5.2 prices it deliberately so the "no gate at all" case has a number. Above the universe it is rejected, because a gate wider than its input is a configuration error, not a wide gate |

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | **VM = 4 vCPU / 16 GB / 250 GB NVMe / static egress IP** | RAM binds on the vectorised backtest working set (§4.2); every other resource has ≥4× headroom | **Yes** — resize | A too-small VM forces a chunked backtest: slower walk-forward and a new class of chunk-boundary bugs in the component promotion depends on |
| 2 | **The bottleneck is named: backtest RAM.** Not ingest, not IOPS, not network | §3 and §4 compute it | Yes | Sizing against ingest (the intuitive choice) buys the wrong machine — too many cores, too little RAM |
| 3 | **Disk sized off the audit trail, at 97% of compressed data** | §2.3, B-F5 | Yes | Sizing off market data underestimates the disk by ~94× |
| 4 | **`llm.gate_width` stays 15. P0.3 declines to set it on cost grounds** | No feasible gate width violates the ceiling (§5.3) | n/a — deferred to ADR-13 | A gate tuned to spend would be tuned differently and worse |
| 5 | **LLM WARN alarm added at $5/month; P0.1's $50 CRITICAL unchanged** | 68× headroom is too coarse to detect a widened gate | Yes | A silently widened gate goes unnoticed for a month |
| 6 | **Full-history LLM replay requires owner approval** (RULE-B7) | It is the only activity that reaches the $200–500 ceiling, and I9 forbids its main motivation | Yes | Uncontrolled replay becomes the largest single cost line |
| 7 | **Pipeline stage budgets fixed; total 18 min against ~14.95 h of slack** | §6.1 | Yes | Budgets set without slack would create false alarms on a path that has no deadline pressure |
| 8 | **Every Path-A stage aborts on breach except `TIER3_LLM`, which degrades** | The LLM tier is excluded from the promotable strategy (Chain G), so its absence cannot invalidate the deterministic path, and degradation can only reduce orders | Yes | Aborting on LLM timeout would make an optional tier load-bearing |
| 9 | **Missing the 14:15 order deadline abandons orders — never places them late** | The list was frozen against the prior bar; late placement is an undocumented intraday entry | **No** — ADR-13 | A late order is an unvalidated strategy path executing with real money |
| 10 | **Intraday-exit budget: 5 s bar-close→ack, 10 s hard** | §6.2 | Yes | A budget looser than the 5-minute bar interval makes stop evaluation meaningless |
| 11 | **Stale-bar CRITICAL at 600 s; positions hold on broker-side stops** | Two missed intervals is unambiguous; the broker-side stop is the designed backstop | Yes | A monitor outage becomes an unprotected book |
| 12 | **Monitor subscribes to `b` only, never `t`** (§12.12) | Removes the only possible open burst by construction | Yes | Trade-level subscription creates a 500–5,000 msg/s open burst for no signal benefit |
| 13 | **Corrections are never reversed post-submission** (RULE-B12) | A sale cannot be unwound; a compensating trade on a vendor message is worse | Yes | Auto-reversal puts an untrusted message in the order path |
| 14 | **Audit writes: actions individually durable, evaluations batchable** (RULE-B4) | `[CONST-5]` binds actions; an evaluation is not an action | Yes | Batching action writes breaks `[CONST-5]`; not batching evaluations makes §9.4's stress case expensive |
| 15 | **P0.3 reports B-F4 and B-F8 rather than deciding them** | Both belong to ADR-08 / `[CONST-1]` / `[CONST-6]`; Block A forbids quietly working around an invariant | n/a | Deciding them here would let a budget phase silently amend the Constitution |
| 16 | **`replay_requires_approval` and `replay_offpeak_only` are immutable `true`, enforced by a validator** | A tunable guard against the only route to the cost ceiling is not a guard | **No** — RULE-B7, RULE-B8 | A config flip re-opens uncontrolled replay spend |
| 17 | **`monitor_subscribe_channels` is validated to exactly `("b",)`, and `DEGRADE` is constrained to `TIER3_LLM` in both the model and the DDL** | Decisions 8 and 12 are load-bearing enough to be unrepresentable when violated, not merely documented | Yes | A prose-only rule is a rule that gets broken by the next contributor |

---

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | Heap tuple overhead 28 B/row `[DEFAULT-B2]` | PostgreSQL page layout not re-derived here | `SELECT pg_column_size(t.*)` on a populated table (Q-6) | ±10% on raw sizes; nothing changes |
| 2 | Compression 15× numeric, 4× text `[DEFAULT-B3]` | Ratio is data-dependent | `hypertable_compression_stats()` after month 1 (RULE-B2) | Disk moves inside 4.7× headroom |
| 3 | 15,000 audit events/session `[DEFAULT-B4]` | Inherited from ADR-13 Chain B; P1.4 has not specified event granularity | Count rows after 20 live sessions | §9.4: 250 GB holds to 75 k, resize at ~150 k |
| 4 | ~60 backtest feature columns `[DEFAULT-B5]` | P2.3 has not been written | Count columns in P2.3's feature spec | 120 columns → 16 GB begins to bind |
| 5 | 6,000 in / 1,500 out tokens per candidate | P0.1 A11, never verified | `usage` field on the first 50 live calls (Q-4) | Linear on LLM spend; 4× still under $3/month |
| 6 | Backtest 10–30 min, walk-forward 1–3 h | No code exists to measure | Time the first real run (RULE-B2) | Wall-clock only; no cash impact |
| 7 | Alpaca order ack ~500 ms `[DEFAULT-B8]` | Not published on any page P0.2 retrieved | Measure in paper trading (Q-3, subject to N11) | 5 s budget has ~2× margin; 3 s still fits the 10 s hard deadline |
| 8 | Alpaca bar delivery ~3 s after bar close `[DEFAULT-B8]` | Not published | Measure in paper trading (Q-3) | Erodes the 5 s budget; the 10 s hard deadline absorbs it |
| 9 | NVMe 50,000–500,000 IOPS, ~0.5 ms fsync | Provider not chosen (Q-1) | Provider spec sheet + `fio` on delivery | Utilisation is 0.5%; a 100× slower disk still suffices |
| 10 | FMP statement payload ~150 KB | Not published | Measure `Content-Length` on 10 requests (Q-5) | Backfill bandwidth 18% → binding at ~1.5 MB/payload |
| 11 | Fundamentals restatement factor 1.5× | Bitemporality not yet specified (A-20) | Count restatements in the first year | ±45 MB. Immaterial |
| 12 | 200 news items/day, ~2 KB each | ADR-13 Chain B; Alpaca states "130+ articles/day" `[V]` | Count after month 1 | ±125 MB. Immaterial |
| 13 | A trades subscription would be 500–5,000 msg/s at the open | Not measured; the design avoids it | Only if `monitor_subscribe_channels` ever changes | Justifies decision 12; no current exposure |
| 14 | 252 sessions/year, 21/month | Standard US calendar; P1.1 owns the authoritative calendar | Cross-check against P1.1's calendar | ±2% on every monthly figure |
| 15 | Backup set ≈ 300 GB off-VM | Derived from ADR-10's schedule, not measured | Measure after the first monthly restore drill | Feeds Q-2 |
| 16 | **`[DEFAULT-B10]`** A partial fill at the 14:15 deadline has its remainder cancelled, with the stop placed on the filled quantity | Neither ADR-14 nor P0.2 states what happens to a working order at the window boundary | Confirm against Alpaca cancel semantics in paper trading (Q-3 instrumentation covers it) | If leaving it working were correct instead, entries would fill closer to target weight — at the cost of an order executing outside the frozen window, which ADR-13 forecloses. Cost of the default is opportunity, not risk |
| 17 | Mean LLM call latency is needed to project a replay's wall clock for RULE-B8's peak-window check | No call has been made; Q-4 measures tokens, not latency | Record p50/p95 call duration on the first 50 gate calls, alongside Q-4 | If the projection is low, a replay pauses at a peak boundary and resumes rather than overrunning — the RULE-B8 pause path handles it, so the failure is a delay, not an overspend |
| 18 | A 5-minute bar arriving from the vendor is final unless a `c` or `x` message revises it | Alpaca documents corrections as a live message type but not their latency bound `[V]` | Count corrections against held names over one month | A correction arriving after an exit is submitted is audited and **not** reversed (RULE-B12); a wider correction window raises how often that happens without changing the rule |
| 19 | The `stage_latency_observation` DDL is syntactically valid PostgreSQL | No database and no SQL parser in the authoring environment | Run it as P1.2 migration 0001 against PostgreSQL 16 + TimescaleDB | A syntax error is caught at migration time, before any data exists. No downstream figure depends on it |

---

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| **Q-1** | **Monthly price of 4 vCPU / 16 GB / 250 GB NVMe with a static IP, in a region acceptable for US + India latency** | Provider pricing pages | Compare, on the same day, published monthly prices for: Hetzner **CCX23** (dedicated vCPU); DigitalOcean **General Purpose 4 vCPU / 16 GB**; Vultr **High Frequency 4 vCPU / 16 GB**; OVH; AWS **m7i.xlarge** + 250 GB gp3. Record the static-IP line and the egress allowance separately | **P0.3 §8 total; P6.4 deploy** |
| **Q-2** | **Monthly price of ~300 GB off-VM backup object storage with 35-day retention** | Provider pricing pages | Published $/GB-month for Backblaze B2, Hetzner Storage Box, AWS S3 Standard-IA, Cloudflare R2. Record **egress cost for a full restore** separately — a restore drill that costs money is a drill that gets skipped | **P0.3 §8 total; P6.4; ADR-10 drill cadence** |
| **Q-3** | **Alpaca order-ack latency and bar-delivery delay after bar close** | Measurement, not documentation | Instrument the paper client: record submit→ack for 100 orders and bar-close→message for 1,000 bars; report p50/p95/p99. Subject to **N11** — this is plumbing evidence, which is exactly what a latency budget needs | **P3.2, P3.3; confirms §6.2** |
| **Q-4** | **Actual tokens per candidate** | Measurement | Log the `usage` object on the first 50 live gate calls; compare against the 6,000/1,500 assumption | **P4.3; confirms §5** |
| **Q-5** | **FMP payload size per statement request** | Measurement | `Content-Length` on 10 representative `income-statement` / `balance-sheet` / `cash-flow` calls | **P2.1 backfill plan; confirms §3.4** |
| **Q-6** | **Measured row width for the bar and audit tables** | Measurement | `SELECT pg_column_size(t.*) FROM daily_bar t LIMIT 1000` and `SELECT pg_total_relation_size('daily_bar'), pg_total_relation_size('audit_event')` after loading one month | **P1.2; confirms §2.1** |
| **Q-7** | **When does Massive finalise daily aggregates after the close?** | Massive docs or support | Is a `1/day` aggregate for date D final at 21:45 UTC on D, or revised later? If revised, the 21:45 ingest reads provisional data and the whole Path-A schedule shifts | **P2.1; §6.1 stage 1; §13 row 3** |
| **Q-8** | **Does Massive retain price history for delisted names?** | Carried from P0.2 §5 M-2 | Request bars for a known delisted ticker over a window before its `delisted_utc` | **P5.1 — survivorship bias; storage unchanged either way** |
| ~~**Q-9**~~ | ~~Does ADR-08 accept 3-month walk-forward rolls?~~ | **Owner** | **CLOSED 2026-08-25 by AD-2** — 3-month rolls with a 1.5 y initial train adopted; the +$120/mo 20-year alternative rejected as not architecturally required | — |
| **Q-10** | **Does `[CONST-6]`'s DENY apply to exposure-reducing actions?** (B-F8 / A-14) | **Owner** | Ratify or reject the §6.3 wording | **P2.9; §6.2 stage 4 and §13 row 27 are not implementable until answered** |
| **Q-11** | **Should the four mandatory Block B section headings be numbered or bare?** | Prompt-pack maintainer (Owner) | Block B specifies bare `## DECISIONS MADE`; SPEC-P0.1 and SPEC-P0.2 both use `## 7. DECISIONS MADE`. This file follows **Block B**. A mechanical merge (X3) grepping `^## DECISIONS MADE$` matches this file and misses both upstream ones | **X3 — MERGE; P0.1 and P0.2 v-next** |
| **Q-12** | **Does the vendor emit a zero-trade 5-minute bar, or omit the window entirely?** | Measurement, then Alpaca support | Subscribe to a thinly traded held name and check whether a window with no prints yields a `b` message with `n = 0` or no message at all. Until answered, an omitted bar is indistinguishable from a lost one and counts toward the stale-bar timer unless the symbol is halted — the fail-closed reading | **P3.3; RULE-B12d; §6.2 stage 1** |

---

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|---|---|---|---|
| `PipelineStage` | type (enum, `StrEnum`) | 12 values: `INGEST`, `UNIVERSE_RESOLVE`, `TIER1_SCREEN`, `TIER2_QUANT`, `INFERENCE_GATE`, `TIER3_LLM`, `DECISION`, `RISK`, `AUDIT_FREEZE`, `ORDER_PLACEMENT`, `MONITOR_EVAL`, `EXIT_SUBMIT` — §14.1 | P1.3, P1.4, P2.x, P3.x, P6.1 |
| `BudgetBreachAction` | type (enum, `StrEnum`) | 6 values: `ABORT`, `DEGRADE`, `DENY_ALL`, `RETRY_IN_WINDOW`, `ABANDON`, `ALERT_CRITICAL` — §14.1 | P1.3, P2.x, P3.x, P6.1 |
| `DiskClass` | type (enum, `StrEnum`) | 3 values: `NVME_SSD`, `SATA_SSD`, `HDD` — §14.1 | P1.3, P6.4 |
| `StageBudget` | type (Pydantic v2, frozen) | `(stage: PipelineStage, budget_seconds: Decimal, hard_timeout_seconds: Decimal, on_breach: BudgetBreachAction, rationale: str)` — §14.2 | P1.3, P2.x, P3.x, P5.5, P6.1 |
| `CostLine` | type (Pydantic v2, frozen) | `(name: str, monthly_usd: Decimal \| None, verified: bool, open_question_id: str \| None)` — §14.3 | P1.3, P6.1, P6.4 |
| `VmSpec` | type (Pydantic v2, frozen) | `(vcpu: int, ram_gb: int, disk_gb: int, disk_class: DiskClass, static_egress_ips: int)` — §14.4 | P1.3, P6.4 |
| `DiskAlarms` | type (Pydantic v2, frozen) | `(warn_pct: int, critical_pct: int)` — §14.4 | P1.3, P6.1 |
| `StoragePolicy` | type (Pydantic v2, frozen) | `(compression_after_days: int, expected_compression_ratio_numeric: Decimal, expected_compression_ratio_text: Decimal)` — §14.4 | P1.2, P1.3, P6.1 |
| `ExitLatencyPolicy` | type (Pydantic v2, frozen) | `(bar_to_ack_budget_seconds: Decimal, bar_to_ack_hard_seconds: Decimal, stale_bar_critical_seconds: int, audit_write_budget_ms: int, audit_write_hard_ms: int)` — §14.4 | P1.3, P3.3, P3.4 |
| `LlmCostPolicy` | type (Pydantic v2, frozen) | `(gate_width: int, cost_per_call_usd: Decimal, spend_alarm_warn_usd_month: Decimal, spend_alarm_critical_usd_month: Decimal, replay_requires_approval: bool, replay_offpeak_only: bool, spend_window_days: int, spend_excludes_approved_replay: bool)` — §14.4 | P1.3, P4.2, P4.3, P6.1 |
| `BudgetConfig` | type (Pydantic v2, frozen) — **root of the namespace** | `(vm, disk_alarms, backup_offvm_gb_estimate, stage_budgets: tuple[StageBudget, ...], exit_latency, llm, storage, monitor_subscribe_channels, walkforward_roll_months, cost_lines)` plus `budget_for(stage) -> StageBudget` — §14.4 | P1.3 (owns loading), all of P2.x–P6.x |
| `stage_latency_observation` | table (PostgreSQL → TimescaleDB hypertable) | 12 columns, 5 CHECK constraints, DDL in §14.5. **Unexecuted — `[U]` until P1.2 migration 0001** | P1.2, P5.5, P6.1 |
| `budget.vm.*` | config key | → `BudgetConfig.vm` (`VmSpec`). Bound: 4 / 16 / 250 / `NVME_SSD` / 2 | P1.3, P6.4 |
| `budget.disk.warn_pct`, `budget.disk.critical_pct` | config key | → `BudgetConfig.disk_alarms` (`DiskAlarms`), **fractions** `0.70` / `0.85` | P1.3, P6.1 |
| `budget.backup.offvm_gb_estimate` | config key | → `BudgetConfig.backup_offvm_gb_estimate: int`. Bound: 300 | P1.3, P6.4 |
| `budget.monthly_usd.*` | config key | → `BudgetConfig.cost_lines: tuple[CostLine, ...]`. Verified $129 / $228; VM and backup lines carry `monthly_usd=None` with `Q-1` / `Q-2` | P1.3, P6.1 |
| `latency.stage_budget_s.<STAGE>` | config key | → `BudgetConfig.stage_budgets[<STAGE>].budget_seconds`. Bound in §14.4 | P1.3, P2.x, P3.x, P6.1 |
| `latency.llm.per_call_timeout_s`, `latency.llm.concurrency` | config key | `120`, `15` — RULE-B11 | P4.3 |
| `latency.order.window_abandon_utc` | config key | `14:15` EDT / `15:15` EST, resolved by P1.1's calendar | P3.2 |
| `latency.exit.*`, `latency.audit.*` | config key | → `BudgetConfig.exit_latency` (`ExitLatencyPolicy`). Bound: 5 / 10 / 600 / 50 / 500 | P1.3, P3.3, P3.4 |
| `llm.gate_width` | config key | `15` — **set by ADR-13 Chain G; P0.3 declines to set it** (B-F2) | P4.2 |
| `llm.cost_per_call_usd`, `llm.spend_alarm_*`, `llm.replay_*` | config key | → `BudgetConfig.llm` (`LlmCostPolicy`). Bound: **0.00300** / 5.00 / 50.00 / true / true | P1.3, P4.3, P6.1 |
| `monitor.subscribe_channels` | config key | → `BudgetConfig.monitor_subscribe_channels`. **Exactly `("b",)`, validator-enforced** | P1.3, P3.3 |
| `storage.compression_after_days`, `storage.expected_compression_ratio.*` | config key | → `BudgetConfig.storage` (`StoragePolicy`). Bound: 30 / 15 / 4 | P1.2, P1.3, P6.1 |
| `backtest.walkforward.roll_months` | config key | `3` — **decided by AD-2**; Q-9 closed | P5.2 |
| `RULE-B1` through `RULE-B12` | event (binding rule) | 12 rules, §15, each naming the phase that enforces it | P1.2, P1.4, P2.1, P3.3, P4.3, P5.1, P6.1, P6.4 |
| `A-13` through `A-20` | event (proposed amendment) | 8 amendments to upstream specs, §10. **A-13 and A-14 require Owner ratification** | P0.1, P0.2, P2.9, P5.2, prompt-pack maintainer |

---

## Acceptance self-check

Verified against the deliverable as written, not against intent.

### Against the phase issue and the P0.3 prompt

| Acceptance criterion | Result | Verification |
|---|---|---|
| Data volume in GB before and after TimescaleDB compression, at 1m / 5m / daily, over 10 years plus live | **PASS** | §2.2 gives provisioned datasets and both full-universe counterfactuals, with an explicit row-width model in §2.1 rather than an inherited constant |
| Ingest throughput in the worst minute, in msg/s and rows/s, with CPU and write IOPS | **PASS, with the premise corrected** | §3 ranks every candidate for "worst minute", computes 63 rows/s, 0.42 msg/s, ~250 IOPS, 0.5% SSD utilisation — and shows the worst minute is **not** the open (B-F1, A-16) |
| LLM spend at gate widths 5, 10, 20, 50 | **PASS** | §5.2, on P0.2's verified prices, plus gate 15 and the no-gate degenerate case |
| Which gate width the $200–500/month ceiling implies | **PASS by refutation** | §5.3 — the ceiling implies **no** gate width; reaching it needs 2.75× the universe. Recorded as B-F2 and A-17; `llm.gate_width` stays 15 |
| VM sizing with the specific bottleneck named | **PASS** | §4 — 4 vCPU / 16 GB / 250 GB NVMe, bottleneck named as **backtest working-set RAM**, with the 8 GB and 32 GB cases costed and the 1-minute counterfactual computed at 708 GB |
| Cost of one full 10-year backtest and per walk-forward window | **PASS** | §7 — <$0.10 amortised and ~$0.004/window, reframed as wall-clock because the VM is fixed-price; $113.40 if an owner-approved LLM replay is attached |
| Latency budget, per stage, each with a hard budget | **PASS** | §6.1 (10 stages) and §6.2 (6 stages) |
| Every stage of the latency budget has a defined behaviour when over budget | **PASS** | Every row of both tables carries an over-budget action, typed as `BudgetBreachAction`; §14.5's `breach_implies_action` constraint makes an undefined one unrepresentable in the database |
| Stated separately for the daily-rebalance and intraday-exit paths | **PASS** | §6.1 and §6.2, with §6.1 reframed as deadline-scheduled because the span is 17.75 h by design |
| Sensitivity table: cost vs universe size vs gate width vs bar frequency | **PASS** | §9, one factor per sub-table plus the combined pessimistic corner in §9.5, and audit volume added in §9.4 as the load-bearing assumption |
| Upstream defects reported | **PASS** | §0 (8 findings) and §10 (8 proposed amendments, A-13 through A-20), including two — A-13 and A-14 — that P0.3 explicitly declines to decide |

### Against Block B — Output Contract

| Block B rule | Result | Verification |
|---|---|---|
| Header block with `id`, `version`, `status`, `phase`, `depends_on`, `produces` | **PASS** | All six keys present at the top of the file |
| `## DECISIONS MADE` with the mandated 5 columns | **PASS** | Bare heading, exact column set, 17 rows |
| `## ASSUMPTIONS` with the mandated 5 columns | **PASS** | Bare heading, exact column set, 19 rows |
| `## OPEN QUESTIONS` with the mandated 5 columns | **PASS** | Bare heading, exact column set, 12 rows |
| `## CONTRACTS EXPORTED` with the mandated 4 columns | **PASS** | Bare heading, exact column set (`Name`, `Kind (type/table/event/endpoint/config key)`, `Signature or schema`, `Consumers`), 27 rows |
| Every entity gets a Pydantic v2 model or a SQL DDL block. No prose-only types | **PASS** | §14.1–14.4 define 11 Pydantic v2 entities including the configuration namespace, which v0.1 carried as a prose key table; §14.5 defines the one table |
| Every field: name, type, unit, timezone, nullability, valid range, and what a violation means | **PASS** | A 7-column field table follows every model in §14.2, §14.3, §14.4 and §14.5; §14.1's enums carry value tables. The timezone convention is stated once at the head of §14 and applied per field |
| Every error path enumerated with its fail-closed behaviour | **PASS** | §13 — 40 error paths across Path A, Path B and operations, each with detection, fail-closed behaviour and alarm tier. Row 27 is marked **not implementable** pending Q-10 rather than given a false resolution |
| No pseudocode in a spec phase | **PASS** | §14's Python is executable and was executed; §14.5's SQL is real DDL, marked `[U]` because it was not run |
| No TODO, no ellipsis, no placeholder, no "implementation left as an exercise" | **PASS** | Text-searched. v0.1's one literal ellipsis in Q-6 is replaced with concrete table names. Unpriced cost lines are typed `None` with a mandatory OPEN QUESTION id — a modelled unknown, not a placeholder |
| Stop at a clean file boundary with `CONTINUE:` if over the response limit | **N/A** | The deliverable is one complete file |

### Against Block C — Clarifier Rule

| Block C rule | Result | Verification |
|---|---|---|
| Up to 10 BLOCKING questions, each with question, options, recommended default, and what breaks if the default is wrong | **PASS** | §11 — exactly 10 rows, all four elements per row. v0.2's two immaterial storage knobs are merged into B9 to make room for B10, the partial-fill question, which is genuinely blocking: two reasonable answers produce materially different order-lifecycle designs |
| Proceed on the defaults; do not wait | **PASS** | Every default is applied throughout the document; nothing is deferred pending an answer except the two upstream questions P0.3 is not entitled to decide (Q-9, Q-10) |
| Mark every default inline with `[DEFAULT-n]` and list them in ASSUMPTIONS | **PASS** | `[DEFAULT-B2]` through `[DEFAULT-B10]` appear inline in §2.1, §2.2, §4.2, §6.2, §9.4 and §15.1; ASSUMPTIONS carries 19 rows, each with a verification method |
| Separately list NON-BLOCKING details noticed and resolved | **PASS** | §12 — 25 items, covering timezones, rounding direction, percentage unit, integer-versus-decimal money, inclusive-versus-exclusive bounds, an off-by-one on the compression window, DST, half-days, and trading halts |
| **Depth: for every rule, also its edge case** | **PASS — and it found eight defects** | §15 pairs all twelve binding rules with their edge cases; §15.1 resolves every numeric threshold in the document. Eight rules were **wrong**, not merely underspecified, and are marked FIXED IN v0.3: B2, B7, B8, B9, B12 and the percentage-unit inconsistency. This is the rule that earned its keep |

### Known deviations, declared rather than hidden

| # | Deviation | Why |
|---|---|---|
| 1 | Body sections §0–§15 are numbered; only the four mandated sections and this self-check are bare | Block B mandates the shape of the four tables, not of the whole document. P0.1 and P0.2 number **all** their headings including the four mandated ones — see **Q-11**, which asks the Owner to settle it, because a mechanical X3 merge grepping `^## DECISIONS MADE$` matches this file and misses both upstream specs |
| 2 | `stage_latency_observation` DDL is unexecuted | No PostgreSQL and no SQL parser in the authoring environment. Declared in §14.5 and as ASSUMPTION 16 rather than claimed as verified |

---

**END OF SPEC-P0.3-BUDGET v0.2**
