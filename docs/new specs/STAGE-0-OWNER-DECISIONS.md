---
id: STAGE-0-OWNER-DECISIONS
version: 0.2
status: DRAFT
phase: X3 follow-up (end of Stage 0)
depends_on: [SPEC-A-CONSTITUTION v0.3, SPEC-P0.1-DECISIONS v0.1, SPEC-P0.2-PROVIDERS v0.1, SPEC-P0.3-BUDGET v0.1, X3-STAGE0-CLAUDE-CHANGES]
produces: [OWD-1..OWD-9, AMD-1..AMD-14]
---

# Stage 0 — Owner decisions resolved under delegation

Date: 2026-10-14. Prepared by the implementer under the Owner's written delegation of the same
date ("resolve these nine decisions using your best technical judgment ... mark each decision
as verified, provisional, or blocked ... ask only when a material decision cannot responsibly be
made"). The Owner adopts or overrules each item by approving this file.

This file answers OD-1 to OD-10 of the X3 CHANGES file
(`paste-ready/outputs/X3-STAGE0-CLAUDE-CHANGES.md` §8.1). It edits no spec. Where a decision
requires a spec to change, the change is listed as an amendment (AMD-n, section 11) owed by the
next version of that spec. Until then this file, not the earlier spec text, governs the items it
names.

Status values:

- **VERIFIED**: decided on evidence that was checked in this work, and the check is recorded here.
- **PROVISIONAL**: decided as the safest defensible default; it rests on at least one item that is
  not yet verified, and names what would change it.
- **BLOCKED**: cannot be decided from available evidence; names exactly what is missing.

Facts are marked with their source. Anything not checked is labelled ASSUMPTION.

## Summary

| # | Subject | Decision | Status |
|---|---------|----------|--------|
| OWD-1 | Residency and jurisdiction | India is the primary jurisdiction. **Owner answered 2026-10-14: the system serves other people** (section 1.5) | PROVISIONAL: Model B chosen; legal review pending (MB-5) |
| OWD-2 | Audit or data unavailable | Fail closed for anything that adds risk; risk-reducing exits only through a defined audited path with broker confirmation | PROVISIONAL (to be specified and tested in P1.4, P2.9, P2.10, P3.4) |
| OWD-3 | The 15 ADRs of P0.1 | All retained provisionally; ADR-11 changed (no live-market order fixed now); nine ADRs owe corrections | PROVISIONAL |
| OWD-4 | The USD 200–500 figure | LLM spend ceiling, as the repository states; platform cost reported separately | VERIFIED (interpretation); cost figures PROVISIONAL |
| OWD-5 | India-first data deadlock | No live trading and no biased evidence; licensed India data must be quoted before any India result counts | BLOCKED for evidence; does not block Stage 1 |
| OWD-6 | Where new code goes | A new `v2/` tree; historical `src/`, `tests/`, `migrations/`, `config/` untouched | VERIFIED |
| OWD-7 | "Single VM" | One application host; encrypted off-VM backups and one reserved recovery address allowed | PROVISIONAL |
| OWD-8 | Python version | Python 3.13 | VERIFIED |
| OWD-9 | Uncommitted historical changes | Preserved untouched; no overlap with the new run | VERIFIED |

Stage 1 does **not** start yet: the Owner's answer in section 1.5 triggers the stop condition of section 10.

---

## 1. OWD-1 — Residency and jurisdiction

### 1.1 Decision

- The account holder is treated as an individual resident in India, and India is the primary
  jurisdiction for the initial product ([DEFAULT-12] confirmed provisionally).
- The system trades **only the Owner's own capital in the Owner's own accounts** (A-36 confirmed
  provisionally). It does not recommend to, trade for, or hold funds of anyone else.
- Residency does **not** decide the hosting location, data-localisation duties or any other legal
  obligation. Those stay with P6.2 and P6.3.

### 1.2 Evidence

- `master-research-summary.md` §16 "What Changes with Scale" (repository text): "Individual
  trading own account — Allowed — Up to 10 OPS: no registration needed"; "System gives
  recommendations to others — Restricted — May constitute investment advice"; "System
  automatically trades for others — Not allowed without license — Requires Portfolio Management
  license"; "Holding client funds — Not allowed — Requires SEBI registration."
- The India broker named in INV-10 is Zerodha Kite (repository, Block A).
- P0.1 F-4 (RBI LRS FAQ, extract level): remittance from India "for margins or margin calls" is
  prohibited. This is why ADR-12 forbids borrowing in the US account.

### 1.3 Risks and what is not verified

- Whether an Indian resident may hold the Alpaca account as Alpaca offers it (OQ-14, OQ-35) is a
  legal question. It blocks **US go-live**, not Stage 1. Not resolved here; no legal conclusion is
  drawn.
- US tax status of the Owner (OQ-5, OQ-18) is unverified.

### 1.4 The one question this file asks the Owner

The delegation text describes the project as "oriented toward Indian retail traders". The
repository's scope is one individual trading their own account (§1.2). These are different
products with different law:

- **Own account only** (the repository's scope): no registration up to 10 orders per second
  (summary §16; P0.2 F-2/F-16, extract level). Everything in Stage 0 assumes this.
- **A product used by, or acting for, other retail traders**: summary §16 says this needs SEBI
  registration (investment adviser, research analyst or portfolio manager, depending on what it
  does). That changes Block A, the HITL list, the audit and compliance phases, and possibly the
  architecture (multi-tenant accounts, client funds).

**Question: is this system only for trading your own money, or is it meant to serve other people?**
Until answered, this file assumes own money only. If the answer is "other people", stop before
P1.1 and re-run P0.1 with that scope.

### 1.5 Owner's answer, 2026-10-14

The Owner answered section 1.4: "serve other people, this ai trading agent is for all".

Consequences, all to be confirmed by a qualified adviser (no legal conclusion is drawn here):

- Everything in Stage 0 that assumes a single person trading their own account is now out of
  scope as the product definition: A-36, [DEFAULT-12]'s single holder, ADR-09's single operator,
  ADR-15's two accounts, P0.3's single-account costs.
- India's retail algo framework applies to anyone offering algorithms to other investors. From
  secondary sources (search excerpts, 2026-10-14; equityresearchindia.com, quantinsti.com,
  spiceroutelegal.com), describing SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 of
  2025-02-04 and NSE standards of 2025-05-05, fully in force from 2026-04-01:
  - an algo provider must be empanelled with NSE or BSE through a partner broker and may not
    connect to an exchange directly;
  - every algo order carries an exchange-issued Algo ID;
  - an algorithm whose logic is not disclosed to the user ("black box") requires the provider to
    hold SEBI Research Analyst registration and keep a research report per strategy; any change
    of logic is a new registration.
  The circular's primary text has still not been read (OQ-1). A model-plus-LLM signal engine is
  most likely a black box in this sense.
- `master-research-summary.md` §16 already states that trading automatically for others needs a
  licence and that holding client funds needs SEBI registration.
- Serving US users brings US adviser or broker-dealer registration into scope
  (summary §16 "SEC/FINRA ... for managing others' money").

Status of OWD-1: BLOCKED until the Owner chooses the service model. P1.1 is not started.

Owner's further answer, 2026-10-14: markets for other users are **both India and the US**. The
scope is written in `SCOPE-MULTI-USER.md` (SC-1 to SC-12) with Model A (each user trades their own
broker account; the service never holds money) as the provisional service model, pending the
Owner's confirmation (OWQ-4). Cross-border use is out of scope for v1 (SC-6).

Owner's decision, 2026-10-14: **Model B, signals only for v1**. Recorded in `MODEL-B-DECISION.md`,
which also lists which decisions and amendments of this file are deferred (section 6 there) and the
roadmap in `ROADMAP-V1.md`. OWD-1 is no longer blocked on the model; it stays PROVISIONAL pending
legal review (MB-5).

---

## 2. OWD-2 — When audit logging, market data or a critical dependency is unavailable

### 2.1 Decision

Constitution C-1 and OQ-2 are resolved as option (c) of X3 OD-2, refined:

| Condition | New entries, adds, any risk-increasing order | Risk-reducing actions (exit, stop placement, kill-switch flatten) |
|-----------|----------------------------------------------|-------------------------------------------------------------------|
| Primary audit store (PostgreSQL) unavailable, local append-only audit sink writable ([DEFAULT-2]) | DENY | Allowed only through the defined exit path (2.2), each written to the local sink first |
| Both audit sinks unavailable | DENY | No system-initiated order. Stops already resting at the broker continue to protect. Immediate incident (2.3) |
| Market data missing or stale for an instrument | DENY for that instrument (INV-6) | Resting broker stops unaffected. A system-initiated exit may go out only as the most aggressive order the market accepts without a reference price (US: market; India: market with exchange-mandated protection, which may not fill, P0.2 UP-12) |
| Risk engine or its policy unavailable | DENY | Exit path only; the kill switch does not depend on the risk engine ([DEFAULT-4]) |
| Broker API unavailable | Nothing can be sent | Resting stops at the broker are the only protection; manual broker console path ([DEFAULT-4]) |

### 2.2 The exit path

- An exit is "risk-reducing" only if it reduces or closes an existing position and opens nothing.
  A sell larger than the held quantity is not an exit (ADR-12).
- Every exit is written to an audit sink **before** it is sent (INV-5 is not relaxed; only the
  sink may be the local one).
- An exit is never reported as done until the broker's order status or fill confirms it. An
  unfilled or unconfirmed exit is an incident, not a success (P0.2 PE-9, PE-10).
- Records written to the local sink are replayed into the primary store when it returns, as
  appended recovery records, never inserted into the past (ADR-10 rule).

### 2.3 Incident rule

- An audit failure is never silent: it raises a critical alert and disables new entries in the
  affected market until a human re-enables (HITL-13).
- If an exit cannot be executed safely, the system stops trying after one attempt per the
  owning phase's rule, alerts, and the documented recovery procedure (P5.5) takes over.

### 2.4 Status and owners

PROVISIONAL. The rules above are a design decision; they become verified only when tested.
Owners: P1.4 (two sinks, replay), P2.9 (DENY scope), P2.10 (flatten without the primary sink),
P3.4 (exit path, read-back). P5.4 must contain a failure-injection test for each row of 2.1.

---

## 3. OWD-3 — The 15 decisions of P0.1

All fifteen are retained **provisionally**. None is approved blindly: each was checked against
the X3 findings, and the corrections it owes are listed. The three the Owner named are discussed
first.

### 3.1 The three named constraints

| Constraint | Kept? | Reason | Correction owed |
|------------|-------|--------|-----------------|
| Daily bars, no intraday monitoring (ADR-13) | Yes | Lowest data, cost and operating burden; P0.3 shows minute bars cost more (P0.3 §12) and need a human awake during the US session (ADR-09). Departs from summary §4/§6/§8 "real-time monitoring" (X3 CS-08); recorded here as an accepted departure. | AMD-1 (late fills, X3 MM-10), AMD-2 (storage figure, X3 CX-01), AMD-3 (HP-3/HP-4 wording, X3 CX-20) |
| Long-only, no borrowing (ADR-12) | Yes | INV-8, P0.1 F-3 and F-4; no short-side stop is defined (RISK-12). | AMD-4 (settled cash, X3 MM-03) |
| No backup broker (ADR-10) | Yes | A position cannot be moved between brokers in an outage; a second broker doubles integration and reconciliation. Resting stops and the broker console are the fallback. Departs from summary §12 (X3 CS-13), recorded. | AMD-5 (RTO precondition, X3 CX-02) |

The late-fill gap (AMD-1) is the one finding that would have created an unprotected position
under ADR-13 as written. The correction chosen keeps "no intraday monitoring" true:

> **AMD-1.** An entry order that is not completely filled when the order job's watch window ends
> (open + 900 s, P0.3 D-30) is cancelled at that moment; a partial fill is kept and gets its stop
> inside the same window. No entry order is left working after the window, so no fill can arrive
> without a process watching for it.

This is the safest of the two options X3 named (the other, a fill-watch job until the close, adds
a process and intraday duty). Cost: fewer fills.

### 3.2 All fifteen

| ADR | Decision (P0.1) | Verdict | Correction owed |
|-----|-----------------|---------|-----------------|
| 01 | FastAPI for actions, Grafana read-only | Keep | None |
| 02 | One in-process scheduler on exchange calendars | Keep | AMD-6: the scheduler only triggers jobs; a separate trader process holds decision and order logic, and P0.3's memory table gains that process (X3 MM-02) |
| 03 | No Kubernetes; second VM on a capacity trigger | Keep | AMD-7: the "largest VM in budget" reference must include a priced disk (X3 MM-20) |
| 04 | No alternative data in v1 | Keep | None |
| 05 | Common stock only | Keep | None |
| 06 | No vector storage | Keep | None |
| 07 | Quarterly retrain plus three triggers | Keep | AMD-8: "up to four" scheduled retrains a year (X3 CX-08) |
| 08 | One challenger, shadow test, human promotes | Keep | AMD-9: "one to two quarters" to promotion (X3 CX-23) |
| 09 | Fourteen human approvals, expiry at session end | Keep | AMD-10: HITL-7 India login deadline is 08:45 `Asia/Kolkata`, and a missed login also costs that day's data (X3 MM-08) |
| 10 | RPO 60 s, RTO 4 h, recovered = reconciled | Keep | AMD-5: the RTO holds only if the recovery address is pre-registered with Zerodha (P0.2 D-17) |
| 11 | Dual-market design; India live first | **Changed** | AMD-11: dual-market design and joint paper trading stay; the order of go-live is **not** fixed now (OWD-5). India paper trading uses our own fill simulator because Zerodha has no sandbox (X3 CX-03) |
| 12 | Long-only, no borrowing | Keep | AMD-4 |
| 13 | Swing on daily bars | Keep | AMD-1, AMD-2, AMD-3 |
| 14 | Universe of 500 by traded value | Keep | AMD-12: order-spacing arithmetic is 114 s for 20 entries of one strategy and 234 s with stops, not 57 s (X3 MM-06) |
| 15 | Per-account currency, INR reporting | Keep | None |

### 3.3 Not expanded

No intraday monitoring, short selling, derivatives or second broker is added. Each would need a
new ADR with its own evidence.

---

## 4. OWD-4 — What the USD 200–500 a month covers

### 4.1 Decision

The figure is the **LLM spend ceiling**, not the platform budget. The total platform cost is
reported separately.

### 4.2 Evidence (repository text)

- `master-research-summary.md` line 286, inside the box "PHASE 5: INFERENCE GATE": "LLM invoked
  ONLY for: Top 10-20 candidates OR Statistically anomalous market conditions → Cost:
  ~$200-500/month".
- `docs/PROMPT-PACK.md` line 277, in the P0.3 prompt's LLM-spend item: "Show where the
  $200-500/month ceiling actually lands and what gate width it implies."

Both place the figure on the LLM line. The delegation says to follow such a definition. P0.3
[DEFAULT-32] read it as the whole platform; that reading is overruled (AMD-13).

### 4.3 Consequence

The LLM line is about USD 1.76 a month at gate width 10 (P0.3 §7.2; re-checked independently in
the separate Claude-chat P0.3 run: 420 calls × (6,000 × 0.30 + 800 × 1.20) / 1,000,000 = USD 1.16
with that run's token counts). The ceiling does not bind at daily cadence. It would bind only with
intraday re-scoring, which ADR-13 excludes.

### 4.4 Total platform cost, reported separately

From SPEC-P0.3-BUDGET §9.1 (prices read from vendor pages in that run; not re-verified here):

| Line | Monthly | Kind |
|------|---------|------|
| VM, DigitalOcean 16 GiB / 8 vCPU (CL-01) | USD 96.00 | recurring |
| US daily bars, Massive Developer (CL-06) | USD 79.00 | recurring |
| Object storage for backups and WAL archive (CL-04, CL-05) | USD 6.00 | recurring |
| Reserved recovery address (CL-03) | USD 5.00 | recurring |
| Kite Connect (CL-10) | INR 500 | recurring |
| LLM, both models (CL-11, CL-12) | USD 2.65 | recurring |
| **Priced total** | **about USD 194 a month** | recurring, floor |

One-time costs: none priced. Setup labour is not costed. A possible one-time India data licence
fee is unknown (OWD-5).

Not deliverable reliably today, regardless of budget, because no source is priced or selected:
India whole-market history with delisted stocks (CL-13), India corporate actions, fundamentals,
news and sector taxonomy (CL-14, CL-18), US fundamentals while SEC requests are paused (CL-15),
the USD/INR reference-rate source (CL-17), the alert channel (CL-19).

Note: the separate Claude-chat P0.3 run priced USD 319 a month because its P0.2 chose real-time
US and FX feeds (USD 199 + USD 49). A daily-bar design does not need real-time feeds; the
end-of-day plan above is the decided one.

### 4.5 Status

VERIFIED as an interpretation of the repository text. The cost figures are PROVISIONAL: they are
P0.3's vendor reads, a floor, with seven lines unpriced.

---

## 5. OWD-5 — The India-first data deadlock

### 5.1 Decision

- No live trading in either market until its own legal, data and test evidence is in place.
  Nothing is launched to break the deadlock.
- No survivorship-biased or unlicensed-data result is ever presented as evidence of trading
  performance ([DEFAULT-29] stands).
- The go-live order is decided later, at P6.5, in favour of whichever market first has
  (a) licensed point-in-time history including delisted stocks, (b) legal clearance for the
  account, and (c) a passed walk-forward. ADR-11's "India live first" is withdrawn (AMD-11).
- Development may proceed on three clearly separated kinds of data, which every report must label:

| Kind | Allowed for | Never used for |
|------|-------------|----------------|
| Synthetic or fixture data | Unit, property and integration tests | Any performance claim |
| Broker history of currently listed stocks (survivorship-biased) | Pipeline plumbing, parity tests | Any performance claim or ADR-08 evidence |
| Licensed point-in-time history including delisted stocks | Backtests, walk-forward, ADR-08 evidence | — |

### 5.2 Evidence gathered on 2026-10-14

- NSE sells paid end-of-day and historical data through NSE Data & Analytics: page
  `nseindia.com/static/market-data/eod-historical-data-subscription` (search excerpt only; no
  price visible).
- NSE-authorised data vendors offering historical Indian data and corporate actions include
  TrueData (`truedata.in`, "authorized ... vendor for NSE, BSE and MCX"; mentions corporate-action
  history) and Global Datafeeds (`globaldatafeeds.in`, "authorized real-time data vendor of Indian
  Stock Exchanges"). Search excerpts only; no prices seen; delisted-stock coverage not confirmed.
- NSE's website terms prohibit automated collection (P0.2 F-63, search excerpt), so scraping the
  public bhavcopy archive is not a licensed source.
- US: Massive's ticker reference carries `delisted_utc` and a point-in-time `date` parameter
  (P0.2 F-51, extract level); whether bars are served for delisted tickers is unverified (OQ-38).

### 5.3 What is blocked and who unblocks it

BLOCKED for evidence: no price is published, so a quote is needed. This is an action for the
Owner, not a decision: ask NSE Data & Analytics, TrueData and Global Datafeeds for (1) end-of-day
history for all NSE and BSE equities since at least 2016 **including delisted securities**,
(2) corporate actions for the same period, (3) licence terms allowing storage and automated use
for one individual's own trading, (4) price, one-time and recurring. For the US, confirm with
Massive that delisted tickers' bars are included on the Developer plan (OQ-38).

Does not block Stage 1: P1.1 to P1.4 define types, storage, configuration and audit; none needs
market data.

---

## 6. OWD-6 — Where new code goes

### 6.1 Decision

New-run code goes in a new top-level `v2/` tree ([DEFAULT-10] confirmed). The historical `src/`,
`tests/`, `migrations/`, `config/` and `scripts/` are not edited, moved or deleted (N-2).

### 6.2 Evidence (inspected 2026-10-14)

- `src/` holds the historical run's Stage 1 code: `src/domain/models.py`, `src/audit/chain.py`,
  `src/audit/events.py`, `src/config/loader.py`. `tests/` holds `verify_p11_*`, `verify_p12_*`,
  `verify_p13_config.py`, `verify_p14_audit.py`. `config/` holds `policy.yaml`.
- These implement the historical specs under `docs/specs/` (frozen in that run), not the new-run
  specs. Their contracts differ from the new run's (for example the new run's money and percent
  conventions are still open, X3 MM-17), so reuse cannot be assumed.

### 6.3 Reuse, migration and maintenance

- Reuse: a historical module may be copied into `v2/` only when a new-run phase's spec shows its
  contract matches, and it then passes that phase's X2 review. Nothing is copied now.
- Maintenance cost: the historical tree is frozen, not maintained; there is one live
  implementation (`v2/`). When `v2/` covers everything the historical tree did, retiring the
  historical tree is a separate Owner decision.
- Testing: `v2/` gets its own test suite and CI target on Python 3.13 (OWD-8).
- No structural change is made now. The first code phase creates `v2/`.

Status: VERIFIED.

---

## 7. OWD-7 — "Single VM" and off-VM recovery

### 7.1 Decision

"Single VM" means one primary application host. Allowed:

- Encrypted, access-controlled backups and WAL archives in off-VM object storage
  ([DEFAULT-19] confirmed). Nothing executes there.
- One reserved static address held for recovery and pre-registered as Zerodha's secondary static
  IP (P0.2 D-17). It is not a second application server.
- Offline backtests and retrains on the same VM, in a container that is paused during live
  windows (P0.3 [DEFAULT-35]).

Not allowed without a new decision: a second host that runs any application process (OD-11).

### 7.2 Cost

USD 5 a month storage plus about USD 1 overage, and USD 5 a month for the reserved address
(P0.3 CL-03 to CL-05, vendor prices read in that run).

### 7.3 Single points of failure that remain

| Failure | What still works | What does not |
|---------|------------------|---------------|
| VM lost | Stops resting at the broker; manual broker console | Automatic kill switch (INV-7 not fully met on VM loss, OD-11); new orders; reconciliation until restore |
| Disk lost | Backups and WAL archive off the VM; up to 60 s of records lost, rebuilt from broker history (ADR-10) | Trading until restore and reconciliation (RTO 4 h) |
| Object storage unreachable | Trading continues | RPO no longer met; new entries disabled until archiving resumes (ADR-10) |
| Broker down | Resting stops at that broker | Everything else in that market |
| India login missed | US market | India orders and India data that day (AMD-10) |

Status: PROVISIONAL (the INV-7 gap on VM loss is accepted for now and is OD-11's to revisit
before P2.10).

---

## 8. OWD-8 — Python version

### 8.1 Decision

**Python 3.13**, pinned to the 3.13 series for code, CI and the container image.

### 8.2 Evidence (run on 2026-10-14, in throwaway environments outside the repository)

- Interpreters installed on this machine: 3.11.9, 3.13.15, 3.14.7. Python 3.12 is not installed.
- The typed models of all four Stage 0 specs (12 Pydantic models) were executed and their JSON
  schemas generated, with warnings treated as errors, under 3.11.9 (Pydantic 2.13.5), 3.13.15 and
  3.14.7 (Pydantic 2.14.1): 12 of 12 passed on each.
- Binary wheels resolve for Linux x86-64 (the VM) and Windows for both 3.13 and 3.14: FastAPI,
  uvicorn, psycopg 3.3.6 with binary, redis, Pydantic, numpy 2.5.4, pandas 3.0.6,
  scikit-learn 1.9.1, scipy 1.18.1, LightGBM 4.7.0, XGBoost 3.4.1, hvac, prometheus-client,
  httpx, PyYAML, alpaca-py, statsmodels, hypothesis, pytest, mypy, alembic, SQLAlchemy.
- **hmmlearn** (the HMM library regime detection in P2.6 is expected to use) resolves for Linux
  on 3.13 but **has no Linux wheel for 3.14**.
- Kite Connect SDK 5.2.2 ships a pure-Python wheel; its pinned dependency set
  (`autobahn[twisted]==19.11.2`, service_identity, pyOpenSSL, python-dateutil, requests) resolves
  as Linux wheels on 3.13 and 3.14.

### 8.3 Reasoning

The newest version that is demonstrably compatible with everything required is 3.13: 3.14 fails
on hmmlearn. 3.13 satisfies STACK-1's "Python 3.12+". There is no evidence that 3.12 is needed, and
it is not installed.

### 8.4 Residual risks

- The Kite SDK pins an autobahn release from 2019; P3.1 must review that dependency.
- Resolving wheels is not running the libraries; each phase's tests run on 3.13 in CI.
- The X3 finding CX-32 (models only ever run on 3.11) is closed by 8.2.

Status: VERIFIED.

---

## 9. OWD-9 — The uncommitted historical changes

### 9.1 What they are (inspected 2026-10-14)

| Path | State | Content |
|------|-------|---------|
| `DECISIONS.md` | modified, 3 lines | Adds a 2026-10-10 row "X5 condition 9 decided" and updates the Q-P1.2-7 row |
| `docs/specs/STAGE-1-FREEZE.md` | modified, +81 / −3 | Adds §15 "Condition 9 — decision, 2026-10-10" and updates two gate rows |
| `docs/specs/SPEC-P2.6-REGIME.md` | untracked | A historical-run P2.6 draft (v0.1), written before P2.4 and P2.5 existed |

All three belong to the **historical** run.

### 9.2 Decision

Preserved exactly as they are. Not committed, stashed, discarded or overwritten. The new run does
not touch these paths, so there is no overlap: the new run writes only under `docs/new specs/`,
`paste-ready/` and `.claude/launch.json`.

Recommendation, for the Owner to act on when convenient: commit the three as one historical-run
commit with the message that matches their content, since §15 is an Owner-approved decision
record. Nothing in the new run depends on it.

Status: VERIFIED.

---

## 10. What this means for Stage 1

- **May start now, as specification work:** P1.1 Domain, P1.2 Storage, P1.3 Config, P1.4 Audit.
  P0.2 and P0.3 are inputs as provisional contracts only (X3 §7).
- **Stop condition: triggered on 2026-10-14** (section 1.5). Stage 1 waits for the service-model decision.
- **Code** (the first X1) needs only OWD-6 and OWD-8, both settled.
- **P1.4 must implement OWD-2's two audit sinks and replay.**
- Not needed before Stage 1 (X3 §8.2): VM-loss kill path (OD-11), India GTT as resting stop
  (OD-12), kill triggers (OD-13), total stop-risk cap (OD-14), unattended flatten (OD-15),
  starting capital (OD-16), INV-9 amendment (OD-17), SEC pause (OD-18), US legal advice (OD-19),
  VM provider (OD-20), stops and rate limits (OD-21), alert channel (OD-23).

---

## 11. Amendments owed by the next version of each spec

| # | Spec | Change | Source |
|---|------|--------|--------|
| AMD-1 | P0.1 ADR-13, P0.3 D-30 | Unfilled entries cancelled at the end of the order job's window; partial fills get their stop inside it | X3 MM-10 |
| AMD-2 | P0.1 ADR-13 | Storage row cites P0.3 §5.2 (whole market, 53.7 million rows) | X3 CX-01 |
| AMD-3 | P0.1 HP-4 | "Only things that can decide to sell" | X3 CX-20 |
| AMD-4 | P0.1 ADR-12 | Buys limited by the minimum of broker cash and our own settled-cash ledger; no buying-power figure may raise it | X3 MM-03 |
| AMD-5 | P0.1 ADR-10 | RTO precondition: recovery address pre-registered with Zerodha | X3 CX-02 |
| AMD-6 | P0.1 ADR-02, P0.3 §8.2 | Scheduler triggers only; separate trader process; memory table re-cut | X3 MM-02 |
| AMD-7 | P0.3 §8.6 | Largest VM in budget includes a priced disk | X3 MM-20 |
| AMD-8 | P0.1 ADR-07 | "Up to four" scheduled retrains | X3 CX-08 |
| AMD-9 | P0.1 ADR-08 | "One to two quarters" | X3 CX-23 |
| AMD-10 | P0.1 HITL-7; Constitution Q5 | Login deadline 08:45 IST; data consequence stated | X3 MM-08 |
| AMD-11 | P0.1 ADR-11 | Go-live order not fixed; decided at P6.5 by OWD-5's three conditions; India paper trading on own simulator | OWD-5; X3 CX-03, CX-10 |
| AMD-12 | P0.1 ADR-14; Constitution Q4 | 114 s / 234 s spacing arithmetic | X3 MM-06 |
| AMD-13 | P0.3 [DEFAULT-32] | Ceiling is LLM-only; platform total reported separately | OWD-4 |
| AMD-14 | Constitution C-1, Q1, [DEFAULT-2] | Replaced by OWD-2 | OWD-2 |

---

## 12. Block C conformance (added in version 0.2, 2026-10-17)

This file was written as a record of decisions, not through Block C. This section adds what Block
C requires. It changes no decision above; Model B (`MODEL-B-DECISION.md`) governs where it says so.

### 12.1 Blocking questions

None new. The questions this file raised (OWQ-1 to OWQ-5) went to the Owner; OWQ-4 is answered
by Model B, and the forks that answer opened are BQ-31 to BQ-43 in `MODEL-B-DECISION.md`,
`ROADMAP-V1.md` and `SCOPE-MULTI-USER.md`.

### 12.2 Edge cases for the decisions above

| Rule | Edge case | Resolution |
|------|-----------|------------|
| OWD-1 | The Owner also wants to follow the signals personally. | Outside the system in v1 (Model B section 2); the restriction in MB-RQ-4 applies and is the Owner's to answer. |
| OWD-2 | Under Model B there are no exits to send. | Read for publication: no signal is published unless its audit record is written first (MB-AC-5). Whether the local sink may carry publication while the primary store is down is P1.4's to decide; until then publication is denied (`MODEL-B-DECISION.md` section 12, MB-AC-5 row). |
| OWD-2 | The local audit sink's disk is full. | Treated as "both audit sinks unavailable": nothing is published and the global kill switch trips ([DEFAULT-47]). |
| OWD-3 | An ADR covers execution (for example ADR-09's order-related human approvals). | Only its publication-relevant parts apply; the P0.1 re-run under Model B decides which, per `MODEL-B-DECISION.md` section 6. |
| OWD-4 | The LLM ceiling is reached mid-month. | Further LLM calls are refused until the next month. Whether a candidate may be published without its LLM review is P4.2's decision; until P4.2 makes it, a candidate that needs an LLM review and cannot get one is not published (INV-6). The month is the calendar month in UTC. The enforced cap is P0.3 section 7.5's. |
| OWD-4 | DeepSeek or OpenAI bills in a currency other than USD, or adds tax. | The ceiling is compared with the USD amount before tax; taxes are reported separately, as P0.3 leaves them unpriced (CL-16). |
| OWD-5 | One result mixes licensed point-in-time data with broker history used to fill gaps. | The whole result takes the weakest label in the table of section 5.1 and is never a performance claim. |
| OWD-6 | A tool expects files at the repository root (`pyproject.toml`, `.github/workflows/`). | New-run project files go under `v2/` with their own `pyproject.toml`. A new file under `.github/` is a change outside `docs/new specs/` and `v2/` and needs the Owner's approval of the diff (constitution N-2 edge case). |
| OWD-7 | PB.1 uses an external email or push-notification provider. | A third-party service is a provider, like a data vendor, not a second application host of ours; it is allowed and must be assessed like any provider (`ROADMAP-V1.md` section 6). |
| OWD-8 | A dependency has no wheel for Python 3.13. | It is not used, or a version with 3.13 wheels is pinned; the interpreter is not changed. (Observed 2026-10-17: Pydantic is not installed for the machine's 3.13 interpreter, only for 3.11; that is a local environment fact, not a wheel gap.) |
| OWD-9 | A commit of new-run files sweeps in the historical changes. | New-run commits stage explicit paths (`docs/new specs/`, `paste-ready/`, `.claude/launch.json`), never `git add -A` or `git commit -a`. |

### 12.3 Non-blocking details

| # | Detail | Resolution |
|---|--------|------------|
| OD-ND-1 | Dates in this file | Calendar dates in `Asia/Kolkata`. |
| OD-ND-2 | Money in OWD-4 | USD, before tax, per calendar month in UTC. |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| OWD-1 | India primary jurisdiction; the service serves other people in India and the US (Owner, 2026-10-14); service model pending (OWQ-4) | Owner's answers, section 1.5; `SCOPE-MULTI-USER.md` | Yes | Whole design: P0.1 to P0.3 re-run under the new scope |
| OWD-2 | Fail closed for risk-adding actions; audited, confirmed exit path | INV-5, INV-6; a resting stop already protects | Yes | P1.4, P2.9, P2.10, P3.4 |
| OWD-3 | Keep all 15 ADRs provisionally; change ADR-11; 14 amendments | X3 findings; no expansion of scope | Yes | Every phase |
| OWD-4 | USD 200–500 is the LLM ceiling | Summary line 286; pack line 277 | Yes | P0.3, P4.2 |
| OWD-5 | No live trading, no biased evidence; quote India data | INV-6, [DEFAULT-29]; no published price | Yes | P2.1, P5.x, P6.5 |
| OWD-6 | `v2/` tree | Historical code implements different specs; N-2 | Yes | Every code phase |
| OWD-7 | One application host; off-VM backups and recovery address | ADR-10 durability; P0.2 D-17 | Yes | P6.4 |
| OWD-8 | Python 3.13 | Tests and wheel resolution (section 8) | Yes | Every code phase |
| OWD-9 | Preserve historical changes | Not the new run's; no overlap | n/a | None |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| OWA-1 | Only the Owner's own capital is traded | The delegation's wording suggests a retail product | Owner answers section 1.4 | Re-scope from P0.1 |
| OWA-2 | NSE-authorised vendors can supply delisted-inclusive history under a single-user licence | No price or licence text was visible | Quotes (section 5.3) | India stays research-only |
| OWA-3 | P0.3's vendor prices still hold | Not re-read in this work | Re-read at P0.3 v0.2 | Total cost moves |
| OWA-4 | Wheels resolving means the libraries install and import on the VM | Libraries were resolved, not installed and run | First CI run on 3.13 | Version choice revisited |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| OWQ-1 | Is the system only for the Owner's own money, or will it serve other people? | Owner | Answered 2026-10-14: other people (section 1.5) | Closed |
| OWQ-4 | Which service model, and which markets for other users? | Owner | Answered 2026-10-14: India and US; **Model B, signals only for v1** (`MODEL-B-DECISION.md`) | Closed |
| OWQ-5 | Who will hold each registration: the Owner personally or a company? | Owner | `SCOPE-MULTI-USER.md` SC-11 | First outside user in each market |
| OWQ-2 | Price, coverage of delisted securities and licence terms of India end-of-day history | NSE Data & Analytics; TrueData; Global Datafeeds | Section 5.3 request | India evidence (P5.1, P5.2); go-live order (P6.5) |
| OWQ-3 | Are delisted tickers' bars included on Massive Developer? | Massive | OQ-38 | US evidence (P5.1) |

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| OWD-1..OWD-9 | decision identifier | Sections 1 to 9 | Every later spec |
| AMD-1..AMD-14 | amendment identifier | Section 11 | Next version of the Constitution, P0.1, P0.3 |
| `python_version` | config key | `"3.13"` | P6.4 (image, CI), every code phase |
| `code_root` | config key | `"v2/"` | Every code phase |
