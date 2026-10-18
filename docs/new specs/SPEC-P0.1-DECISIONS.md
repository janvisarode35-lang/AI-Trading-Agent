---
id: SPEC-P0.1-DECISIONS
version: 0.1
status: DRAFT
phase: P0.1
depends_on: [SPEC-A-CONSTITUTION]
produces: [ADR-01..ADR-15, DEFAULT-12..DEFAULT-21, Market, Currency, AdrStatus, AdrId, AdrOption, AdrRecord, ScopeDecisions, HP-1..HP-5, UNI-1..UNI-6, HITL-1..HITL-14, REC-1..REC-6, T-1..T-3]
---

> **Model B notice (2026-10-14).** The Owner chose signals only for v1 (no order routing, no broker integration, no handling of user funds). This spec's text below is unchanged. Where it concerns orders, brokers or accounts it is superseded or deferred as listed in `MODEL-B-DECISION.md` section 6, and Block A items are read with the amendments BA-1 to BA-6 there. Phases are re-run per `ROADMAP-V1.md`.

# SPEC-P0.1 — Decision Closure (new run)

Date: 2026-10-13. Decision owner for every ADR: Owner. Author: principal engineer (this run).

Inputs consumed: `master-research-summary.md` sections 19, 20 and 21 (as committed at `HEAD`),
and `docs/new specs/CONSTITUTION.md` v0.3. No historical spec was read (N-3).

Run note: the pack asks for one fresh conversation per phase. This phase was run in the same
conversation as Blocks A, B and C, at the Owner's direction.

Every ADR below has status PROPOSED. An ADR becomes ACCEPTED when this spec is FROZEN. Until
then no code phase may cite it.

Contents: 1 upstream problems; 2 external facts used; 3 blocking questions; 4 the fifteen
ADRs; 5 decisions that constrain everything else; 6 mapping of the research summary; 7 typed
form; 8 error paths; 9 non-blocking details; then the four tables.

## 1. Problems in the upstream material

RULE-5 requires this section.

| # | Where | Problem | Handling in this spec |
|---|-------|---------|-----------------------|
| UP-1 | P0.1 prompt, DELIVERABLE | Names `docs/specs/SPEC-P0.1-DECISIONS.md`. That path is historical (N-2). | Written to `docs/new specs/SPEC-P0.1-DECISIONS.md` (N-5). |
| UP-2 | P0.1 prompt, OBJECTIVE | "Close every open question." Section 21 of the summary lists ten research items. A research item is closed by evidence, not by a decision. | Section 6.3 assigns each to the phase that must produce the evidence. None is declared closed. |
| UP-3 | INV-9, "US PDT" | FINRA has replaced the day-trading margin requirements. The pattern-day-trader designation and the USD 25,000 minimum are eliminated, effective 2026-06-04, with a phase-in for firms that ends 2027-10-20 (F-1). INV-9 names a rule that is being retired. | Not edited here; Block A is the Owner's. ADR-13 designs for the new standard and for a firm still on the old one. OQ-13. |
| UP-4 | INV-10 with INV-8 | Alpaca sets up every account as a margin account (F-3). RBI prohibits remittance from India "for margins or margin calls" under the Liberalised Remittance Scheme (F-4). If the account holder is an Indian resident, the only US account INV-10 allows is of a type whose defining feature they may not use. | ADR-12 forbids borrowing. Whether holding the account is itself permitted is a legal question: OQ-14. |
| UP-5 | P0.1 prompt, items 2, 3, 6 | STACK-1 already excludes Airflow, any orchestration framework, Kubernetes and a vector DB. The prompt asks for these to be decided again with three or more options. | Each ADR lists the excluded options and marks them "excluded by STACK-1". The decision cannot differ from STACK-1 and does not. |
| UP-6 | P0.1 prompt, ADR FORMAT | "Options considered, with the cost of each." Money costs come from P0.2 (prices) and P0.3 (budget), and both depend on this phase. | Cost is stated as what must be built and operated. A money figure appears only with a source. Nothing is estimated. |
| UP-7 | P0.1 prompt, items 7, 8, 10 | They ask for numbers (cadence, sample size, RPO, RTO) for which sections 19 to 21 give no data. | Each number is labelled ASSUMPTION and assigned to the phase that must confirm it (P5.2, P6.4). |
| UP-8 | Summary section 19, row 6 | Says "entry - 2.5×ATR" with no period. Block A says ATR(14). | Block A governs (RISK-12). |
| UP-9 | Summary section 19, row 10 | "7-stage progression" for paper trading. The seven stages are not in the declared inputs. | Not used here. P6.5 owns it. |
| UP-10 | INV-9, SEBI items | NSE material states a threshold of 10 orders per second, and that a client static IP is needed when the algo logic runs at the client's end (F-2). It does not, in the part retrieved, say who issues the order tag or what registration is needed. | Partly answers OQ-1. OQ-1 stays open for the remaining points. |

## 2. External facts used

Each fact was retrieved on 2026-10-13. "Extract" means the page was read through an automated
question-answering fetch, not line by line; the primary text must be read in full by the phase
named before that phase freezes.

| # | Fact | Source | Level | Full read owed by |
|---|------|--------|-------|-------------------|
| F-1 | FINRA adopted intraday margin standards that replace the day-trading margin requirements "in their entirety", including the day-trade count and the USD 25,000 pattern-day-trader minimum equity. Effective 2026-06-04. Firms needing more time may phase in until 2027-10-20. The new standard applies to margin accounts other than good-faith and portfolio-margin accounts. | FINRA Regulatory Notice 26-10, finra.org/rules-guidance/notices/26-10 | Primary, extract | P6.3 |
| F-2 | NSE FAQ on retail algorithmic trading: orders received via API from clients are treated as algo orders and need tagging, including a standardised tag where the rate is within the threshold of 10 orders per second; a client static IP is required where a client uses the API with the algo logic at their own end. | NSE FAQ dated 2025-11-03, nsearchives.nseindia.com, file `FAQ_Retail Algo_03112025_NSE.pdf`, citing NSE circulars NSE/INVG/69255 (2025-07-22) and NSE/INVG/67858 (2025-05-05) | Primary, extract | P0.2, P6.3 |
| F-3 | Alpaca: "All accounts are set up as margin accounts." Accounts under USD 2,000 equity are treated as limited margin accounts. Margin trading and short selling need USD 2,000 or more. | alpaca.markets/support/alpaca-cash-accounts and alpaca.markets/support/determine-margin-account | Vendor, search excerpt | P0.2 |
| F-4 | RBI Liberalised Remittance Scheme: limit USD 250,000 per financial year (April to March). Prohibited item 2: "Remittance from India for margins or margin calls to overseas exchanges / overseas counterparty." Income may be retained and reinvested; foreign exchange not reinvested is repatriated within 180 days. | RBI FAQ, rbi.org.in/commonman/english/Scripts/FAQs.aspx?Id=1834, Q1, Q2 | Primary, extract | P6.3 |
| F-5 | Alpaca moved to the new intraday margin framework on 2026-06-04: intraday buying power replaces day-trade buying power, and pre-trade checks reject orders that would create a margin deficit. | Alpaca blog, "FINRA Retires the PDT Rule", published 2026-04-27, updated 2026-06-04 | Vendor, extract | P0.2 |

Facts I rely on that I did not verify in this phase are in ASSUMPTIONS, not here.

## 3. Blocking questions and the defaults used

Numbering continues from the constitution (`[DEFAULT-1]` to `[DEFAULT-11]`).

| # | Question | Options | Default used | If the default is wrong |
|---|----------|---------|--------------|-------------------------|
| BQ-1 | Where is the account holder resident for tax and exchange control? | India; US; other | [DEFAULT-12] An individual resident in India. | ADR-11, ADR-12, ADR-13 and ADR-15 are re-decided: first live market, borrowing, tax handling and reporting currency all follow from residency. |
| BQ-2 | What is the holding period? | intraday; swing (days to weeks); position (months) | [DEFAULT-13] Swing, decided once per session on daily bars. | Data frequency, storage, latency budget, cost model and LLM use all change (ADR-13 chains). |
| BQ-3 | Which market goes live first? | India; US; both together | [DEFAULT-14] India. Both are built and paper-traded together. | Go-live order changes. The design does not: it is dual-market either way. |
| BQ-4 | How is the tradable universe defined? | index membership; top-K by traded value; all listed | [DEFAULT-15] Top 500 per market by median daily traded value over 60 sessions, rebuilt monthly. | Universe, storage and scan cost change; an index-based universe needs licensed point-in-time constituents. |
| BQ-5 | How is the US account operated, given F-3? | margin account, borrowing allowed; margin account, zero borrowing | [DEFAULT-16] Zero borrowing: buys are sized against settled cash only. | With borrowing, C-2 reopens and F-4 may be breached. |
| BQ-6 | How wide is the LLM gate? | 5; 10; 20; 50 per market per session | [DEFAULT-17] 10. | LLM spend scales linearly with it. P0.3 prices it. |
| BQ-7 | What is the reporting currency for a combined figure? | INR; USD; none | [DEFAULT-18] INR. Reporting only. | A label and one conversion direction change. Risk is unaffected. |
| BQ-8 | May backups be stored off the VM, given STACK-1 names one VM? | no; yes, object storage for backups only | [DEFAULT-19] Yes, for backups and write-ahead-log archives only. Nothing executes there. | With "no", loss of the VM's disk loses the audit trail and RPO is unbounded. |
| BQ-9 | Are ETFs and depositary receipts tradable in v1? | yes; no | [DEFAULT-20] No. Common stock only. | The universe is smaller than intended. |
| BQ-10 | What starting capital does each account have? | any amount | [DEFAULT-21] Not assumed. The design must hold at any NAV: an order whose quantity rounds to zero is not sent. | At a small NAV many instruments are untradable, especially in India where one share can exceed 5% of NAV (ADR-14). |

## 4. Architecture Decision Records

Format per ADR: Title, Status, Context, Options considered, Decision, Edge cases, Consequences,
What would make us revisit, Decision owner, Date. "Edge cases" is added to the pack's format
because Block C requires one for every rule.

### ADR-01 — Operator surface: FastAPI and Grafana, no web UI

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 1. The system is autonomous. A human needs to see state
and to perform the approvals in ADR-09. STACK-1 already contains FastAPI and Grafana and no
front-end framework.

Options considered:

| Option | Cost |
|--------|------|
| A. Full web UI (single-page application on a JavaScript framework) | A second language and build toolchain outside STACK-1. A browser-facing authentication surface. A second place where an approval can be granted, which must be audited like the first. The largest build of the four. |
| B. FastAPI endpoints for actions, Grafana for viewing | Nothing new in the stack. Actions are less convenient: a command line or an HTTP client. |
| C. Command line only, no dashboards | Smallest build. State is visible only through queries, so a problem is seen later. |
| D. Grafana only, with actions done by editing the database | No action code to write. Every approval bypasses the audit trail, which breaks INV-5. Rejected outright. |

Decision. B.
- Grafana is read-only. It has no credential that can write to the trading database.
- Every human action in ADR-09 is a FastAPI endpoint, called from a small command-line client.
- The manual kill-switch trip is not served by this FastAPI process. It belongs to the
  kill-switch process ([DEFAULT-4]).

Edge cases:
- FastAPI is down: approvals cannot be granted, so everything waiting on one stays denied. The
  kill switch still works because it does not depend on FastAPI.
- Grafana is down: nothing is blocked. Alerts are delivered by Prometheus alerting, not by a
  person watching a dashboard.
- Grafana shows a stale panel: every panel shows the timestamp of its newest data point.
- An approval is attempted by editing the database directly: it has no audit record, so the
  action it would unlock does not happen (INV-5).

Consequences. No front-end code. The operator needs a terminal. P6.1 specifies dashboards;
P6.2 specifies authentication for the endpoints.

Revisit when: a second human operator is added, or the Owner cannot complete a HITL action
within its expiry (ADR-09) on three occasions in any 60 sessions [ASSUMPTION for the count].

### ADR-02 — Scheduling: one in-process asyncio scheduler driven by exchange calendars

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 2. Jobs run relative to exchange sessions in two
timezones, with holidays, half-days and US daylight saving. STACK-1 excludes Airflow and any
orchestration framework (UP-5).

Options considered:

| Option | Cost |
|--------|------|
| A. Host `cron` running Python scripts | No code. `cron` knows wall-clock time only: it does not know a holiday, a half-day or a session date, so each script must re-derive them, and a missed run is silent. |
| B. Airflow | Excluded by STACK-1. A scheduler, a web server and a metadata database to operate. |
| C. Temporal | Excluded by STACK-1 (orchestration framework). A server cluster to operate. |
| D. One long-running Python process using `asyncio`, with times computed from the exchange calendar | A few hundred lines of our own code to write and test. One more process that must be supervised. |

Decision. D.
- One scheduler process. A database advisory lock guarantees a single instance.
- Each job run is identified by job name, market and session date. A run with a given identity
  happens at most once.
- Each job has a start time and a deadline, both expressed relative to that market's session
  (for example "after the close"), never as fixed wall-clock times.
- A job that can produce orders and has missed its deadline is skipped and alerted. It never
  runs late. A data job that missed its window runs at the next opportunity.
- The scheduler holds no trading logic and cannot place an order.

Edge cases:
- The process restarts mid-job: on start it reads which runs are complete. An incomplete
  order-producing run is not resumed; it is skipped and alerted. Reconciliation with the broker
  (P5.5) runs first.
- A US clock change falls between two sessions: start times follow the session, so nothing
  shifts. Times are never stored as a UTC offset.
- A half-day: "after the close" follows the early close because it is computed from the
  calendar.
- The calendar has no entry for today: the market is treated as closed and an alert is raised.
  A weekday is never assumed to be a session.
- The VM clock is wrong: P6.1 monitors clock offset. The threshold is P6.1's.
- Two markets need a job in the same minute: jobs for different markets are independent.

Consequences. No orchestration product. P1.2 stores job-run records; P2.1 supplies the
calendar; P6.4 supervises the process.

Revisit when: more than one host is needed (ADR-03), or the number of distinct jobs exceeds
what one process can run inside the P0.3 latency budget.

### ADR-03 — Kubernetes: not used

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 3. STACK-1 says Docker on a single VM and "No
Kubernetes" (UP-5). The question that remains is what would reopen it.

Options considered:

| Option | Cost |
|--------|------|
| A. Never, with no stated trigger | Nothing to build. Leaves no agreed signal for when one VM is not enough. |
| B. Not used; a measured trigger moves to a second VM first, and only a later trigger reopens Kubernetes | Requires the trigger metrics to be collected (P6.1). |
| C. Managed Kubernetes from the start | Excluded by STACK-1. A control plane to pay for and operate, and a failure domain that sits between the kill switch and the broker. |
| D. Warm standby VM from the start | A second host from day one. Solves availability, not capacity. Outside STACK-1 as written; relevant to C-4 and OQ-12. |

Decision. B.
- Kubernetes is not used.
- Capacity trigger: the daily decision path misses its P0.3 deadline on 5 or more sessions in
  any 20, on the largest VM size inside the P0.3 budget [ASSUMPTION: 5 in 20].
- The response to the trigger is a second VM running Docker, not Kubernetes.
- Kubernetes is put to the Owner again only if four or more hosts are needed
  [ASSUMPTION: four].

Edge cases:
- The deadline is missed because a vendor was slow, not because the VM was short of capacity:
  that session does not count toward the trigger. P6.1 records the cause.
- The trigger fires during a drawdown or an incident: no infrastructure change is made while
  any position is open without a resting stop.
- A second VM is added: the kill switch moves to it first (C-4).

Consequences. All services share one failure domain. ADR-10 and [DEFAULT-4] carry the
resulting risk.

Revisit when: the capacity trigger above fires, or the Owner allows a second host under OQ-12.

### ADR-04 — Alternative data: none in v1

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 4. The prompt asks which sources, at what cost and with
what latency. No price or latency for any alternative-data product is in the inputs, and none
was verified (UP-6).

Options considered:

| Option | Cost |
|--------|------|
| A. None. v1 uses prices, corporate actions, fundamentals, regulatory filings, macro series and news | Nothing added. The model has no source of information that a price-and-fundamentals model lacks. |
| B. Social-media sentiment | Price and licence terms not verified. The content is attacker-controlled text, the hardest input for INV-4. Needs point-in-time history that such feeds rarely keep. |
| C. A purchased dataset such as short interest, options flow or web traffic | Price not verified. Usually US-only, which conflicts with INV-10 unless scoped. Needs several years of point-in-time history to pass ADR-08. |
| D. Broker-estimate revisions | Price not verified. Coverage of Indian mid-caps not verified. |

Decision. A. No alternative data in v1. Latency and cost are therefore not applicable.

A source may be admitted later only if all of these hold:
- Its history is point-in-time: each value carries the time it became available.
- Its history is long enough for the walk-forward protocol (P5.2).
- It covers both markets, or the spec that adds it scopes it to one market by name.
- A model using it beats the champion under ADR-08.
- Its cost fits the P0.3 budget and its licence permits automated use and storage.

Edge cases:
- News is not alternative data here. It is in v1 scope and goes through P4.1.
- A free source appears: free is not a reason. The five conditions still apply.
- A source passes for the US only: it is added as a US-only feature and named as such, so that
  it is not "US-only by accident" (INV-10).
- A vendor revises history after the fact: the stored point-in-time value is never overwritten.

Consequences. P0.2 does not evaluate alternative-data vendors. P2.4 has no alternative-data
features.

Revisit when: the system has completed the paper-trading gates (P6.5) and a specific source is
proposed with its price, licence and history length in hand.

### ADR-05 — Instruments: common stock only

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 5. INV-8 forbids autonomous leverage. Futures and options
are leveraged by construction.

Options considered:

| Option | Cost |
|--------|------|
| A. Common stock only | Smallest instrument model. No hedge instrument: in a falling market the only defence is holding cash. |
| B. Common stock and ETFs | ETFs need their own handling: no fundamentals, creation and redemption, leveraged and inverse products that must be excluded by name. |
| C. Add index futures for hedging | Margin, expiry, rollover and daily settlement. Conflicts with INV-8 unless the Owner amends it. Under F-4, margin remittance abroad is prohibited for an Indian resident. |
| D. Add options | Everything in C, plus a pricing model and assignment handling. |

Decision. A. [DEFAULT-20]
- Tradable in v1: common stock listed on NYSE or NASDAQ, and on NSE or BSE.
- Not tradable: ETFs, depositary receipts, preferred shares, units, warrants, rights, closed-end
  funds, real-estate and infrastructure trusts, futures, options.
- An ETF or an index may be read as data (for a benchmark or for regime detection) and is
  never ordered.
- Futures and options do not enter scope without an Owner amendment to INV-8.
- Earliest order of expansion, each by a new ADR: ETFs first, and not before the live go-live
  gates of P6.5 have been passed.

Edge cases:
- The vendor's instrument-type field is missing or unknown for a symbol: not tradable (INV-6).
- A held stock is reclassified, for example it converts to a trust: no new buys; the position
  is managed to its exit.
- A corporate action delivers a non-tradable instrument such as rights or a spun-off unit: it
  is not a strategy position. It is escalated to a human (ADR-09, HITL-11).
- A company has two share classes: each is a separate instrument. Whether both may be held at
  once is P2.3's rule.
- An Indian share in a trade-for-trade or surveillance category: eligibility by series is
  P2.3's rule. This ADR decides the instrument class only.

Consequences. P1.1 models one instrument class with a type field and a closed list of values.
There is no hedging instrument, so P2.6 can only reduce exposure, not offset it.

Revisit when: the P6.5 live gates are passed and a specific need is shown, for example cash
held through a long bearish regime.

### ADR-06 — Vector database: not used

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 6. STACK-1 says "no vector DB" (UP-5). The question is
whether any use case justifies asking the Owner to change that.

Options considered:

| Option | Cost |
|--------|------|
| A. A dedicated vector database | Excluded by STACK-1. A new stateful service, an embedding model, and a retrieval step whose output the LLM would read: a new path for untrusted text (INV-4). |
| B. The `pgvector` extension inside the existing PostgreSQL | No new service. Still needs an embedding model and still adds retrieval in front of the LLM. |
| C. None. Exact and near-duplicate news detection by deterministic hashing | A hash function. No semantic search. |

Decision. C. No vector storage of any kind.
- The LLM receives a bounded, sanitised packet for each gated candidate (P4.1, P4.3). It does
  not search a corpus.
- Duplicate news is detected by a deterministic hash of normalised text. Normalisation is
  P4.1's.

Edge cases:
- Two articles say the same thing in different words: they are not detected as duplicates and
  both may reach the packet. P4.1 bounds the packet size, so the cost is bounded.
- A later phase wants "similar past events": it must show a measured benefit under ADR-08
  first, and option B is considered before option A.

Consequences. No embedding model, no embedding cost, no retrieval step to secure.

Revisit when: a P4 spec demonstrates, under ADR-08, that retrieval improves decisions.

### ADR-07 — Model retraining: quarterly, with three out-of-cycle triggers

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 7. INV-8: no "trade lost, change the strategy"; changes
are offline and validated. Retraining therefore produces a challenger and never changes the
live model by itself. No data in the inputs supports a specific cadence (UP-7).

Options considered:

| Option | Cost |
|--------|------|
| A. Never retrain; fixed model | No pipeline. The model ages as the market changes, with nothing to catch it. |
| B. Retrain every month | Twelve challengers a year. Each needs an ADR-08 evaluation of at least 60 sessions, so evaluations overlap and ADR-08's one-challenger rule cannot hold. |
| C. Retrain every calendar quarter, plus defined out-of-cycle triggers | Four scheduled challengers a year. About 63 sessions per quarter [ASSUMPTION: 252 sessions a year], which fits one ADR-08 evaluation. |
| D. Retrain when performance drops | This is "trade lost, change the strategy". Breaks INV-8. Rejected outright. |

Decision. C.
- Scheduled: one retrain per market per calendar quarter, run offline after the last session
  of the quarter. The output is a challenger.
- Out-of-cycle triggers:
  - T-1, input drift. The population stability index of any model input, measured over the
    trailing 20 sessions against the training sample, is above 0.25 for 5 consecutive sessions
    [ASSUMPTION: 20, 0.25 and 5].
  - T-2, loss of rank information. The rank correlation between model score and realised
    forward return over the trailing 60 sessions is at or below zero [ASSUMPTION: 60].
  - T-3, input definition change. A data vendor, a field definition or an adjustment method
    changes for any model input.
- T-1 and T-2 raise an alert and start an offline retrain. They do not block trading by
  themselves. The human may disable entries (HITL-13).
- T-3 blocks new entries in the affected market until a model trained on the new definition is
  promoted. The old model was fitted to different inputs, so its output is not valid data.
- At most one out-of-cycle retrain per market per calendar month [ASSUMPTION: one].
- Things that are never a trigger: a losing trade, a losing day or week, a drawdown, an LLM
  output, a human hunch without one of T-1 to T-3.

Edge cases:
- PSI exactly 0.25: not above the threshold; no trigger.
- A feature is missing for some sessions in the 20-session window: PSI is not computed on a
  partial window. A missing input is already a DENY for that instrument (INV-6).
- T-1 fires again the month after an out-of-cycle retrain: the monthly cap holds; the alert
  stays raised.
- A scheduled retrain falls due while a challenger is under evaluation: it is skipped for that
  quarter and recorded. The evaluation is not interrupted.
- T-2 is measured on few trades because the regime kept the system in cash: with fewer than
  60 sessions of scores it is not computed.
- The two markets trigger separately. Models are per market.

Consequences. P6.6 builds the pipeline. P5.2's walk-forward step should equal the retrain
interval, one quarter; P5.2 confirms or challenges that.

Revisit when: P5.2 shows that a different interval gives materially better out-of-sample
results, or T-1 fires in more than two quarters of four.

### ADR-08 — Champion/challenger: one challenger, shadow portfolios, one pre-set test

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 8. INV-8 requires champion/challenger validation. The
prompt asks for sample size, significance test and promotion rule. The inputs give no data to
derive them (UP-7), so each number is an ASSUMPTION that P5.2 must confirm with a power
calculation on backtest data.

Options considered:

| Option | Cost |
|--------|------|
| A. Compare backtests only; promote the better one | No waiting. The challenger has seen the test period during development, so the comparison is biased toward it. |
| B. Split live capital between champion and challenger | Real evidence. Real money on an unproven model, and half the capital on each halves the sample of each. |
| C. Shadow evaluation: both run on shadow portfolios with the same fill model; one pre-set test; a human promotes | No capital at risk. At least 60 sessions of waiting. Results depend on the fill model (P5.3). |
| D. Promote on a human's judgement | No statistics to build. Not reproducible and not auditable. |

Decision. C.
- One challenger per market at a time. This removes multiple-comparison correction.
- The challenger receives no capital. It makes decisions on the same inputs as the champion,
  through the same risk engine, against a shadow portfolio.
- The champion is also tracked on a shadow portfolio with the same fill model. The test
  compares shadow with shadow. The champion's live fills are not used in the test.
- Sample: the evaluation ends at the later of 60 sessions and 100 closed challenger trades,
  and no later than 120 sessions [ASSUMPTION: 60, 100, 120].
- Test: one-sided, on the paired daily difference in net return (challenger minus champion),
  using a moving-block bootstrap with blocks of 5 sessions and 10,000 resamples, at
  significance level 0.05 [ASSUMPTION: 5, 10,000, 0.05]. The random seed is fixed before the
  evaluation starts and recorded.
- The test is run once, at the end. No interim look.
- Promotion requires all of:
  - the test rejects "challenger is not better" at 0.05;
  - the challenger's maximum drawdown over the window is not larger than the champion's;
  - the challenger caused no risk-engine denial that the champion's decisions did not;
  - a human approves (HITL-3), and the approval is in the audit trail before the switch.
- Any other outcome, including an inconclusive one, leaves the champion in place.
- After promotion the old champion is retained and can be restored by a human (HITL-3).

Edge cases:
- p-value exactly 0.05: not rejected. The champion stays.
- 120 sessions pass with fewer than 100 closed trades: inconclusive. The champion stays.
- One of the two has no result for a session (a crash, a missing input): that session is
  dropped for both. If more than 5% of sessions are dropped the evaluation is void and
  restarts [ASSUMPTION: 5%].
- A T-3 trigger (ADR-07) fires during an evaluation: the evaluation is void. The first
  challenger trained on the new definition becomes champion only through the same test against
  a baseline of holding cash, because the old champion is no longer valid.
- The first model ever has no champion: it is tested against holding cash, same rules.
- Drawdowns equal to the last unit of precision: "not larger" includes equal.
- Both markets: evaluated and promoted separately.
- The fill model changes during an evaluation: the evaluation is void.

Consequences. A model change takes at least one quarter from training to promotion. P5.3's
fill model becomes part of the promotion evidence. P6.6 implements this.

Revisit when: P5.2's power calculation shows the sample cannot detect an effect of the size
the backtests suggest, or shows that fewer sessions suffice.

### ADR-09 — Human-in-the-loop: fourteen actions, expiry at end of session

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 9. INV-7 requires a human to re-enable after a kill.
INV-2 and INV-8 keep limits and strategy out of the AI's hands. The system has one human
operator [DEFAULT-12 implies they are in India]. In India Standard Time the US regular session
runs 19:00 to 01:30 during US daylight time and 20:00 to 02:30 otherwise (A-26, computed), so
part of every US session falls when the operator is likely asleep.

Options considered:

| Option | Cost |
|--------|------|
| A. A human approves every order | The system is no longer autonomous. Every US entry needs a person awake at night. |
| B. A human approves nothing; alerts only | Nothing to build. Breaks INV-7, and lets policy, models and code change without a person. |
| C. A fixed list of actions needs approval; individual trades inside the limits do not; a request not answered expires | An approval endpoint and its audit records. Work waits when the human is away, by design. |
| D. As C, with two different people approving | Needs a second person. There is one operator. |

Decision. C. The system never performs these without a human approval recorded in the audit
trail first:

| ID | Action |
|----|--------|
| HITL-1 | Re-enable trading after any kill-switch trip (INV-7). |
| HITL-2 | Enable live trading for a market for the first time, and each stage progression in P6.5. |
| HITL-3 | Promote a challenger to champion, or restore a previous champion (ADR-08). |
| HITL-4 | Change any policy or risk value. |
| HITL-5 | Deploy code or configuration to the live VM. |
| HITL-6 | Add or remove a market, an instrument class or a data source, or change the universe rule (ADR-14). |
| HITL-7 | Log in to the India broker each trading day, if OQ-7 confirms it is manual ([DEFAULT-6]). |
| HITL-8 | Accept a difference between the system's positions or orders and the broker's. |
| HITL-9 | Declare recovery complete after a disaster (ADR-10, REC-6). |
| HITL-10 | Register a deposit, a withdrawal or a transfer between the two accounts. |
| HITL-11 | Dispose of a holding that is not a strategy position: an unexpected instrument, a negative quantity. |
| HITL-12 | Release an instrument or a data source from data-quality quarantine. |
| HITL-13 | Re-enable new entries for a market after a human or an alert disabled them. |
| HITL-14 | Issue or rotate a broker, data or LLM credential. |

Actions that need no approval: an individual order inside all limits; a stop or an exit; a
scheduled retrain; tripping the kill switch; disabling new entries. Anything that only reduces
risk can be done by the system or by a human without waiting.

Service levels:
- While a request is pending, the thing it would allow is denied.
- A request expires at the end of the session of the market it concerns. A request that
  concerns no single market expires at 23:59:59 `Asia/Kolkata` on the day it was raised
  [DEFAULT-12]. An expired request must be raised again. Nothing is ever approved by timeout.
- A critical alert not acknowledged within 15 minutes disables new entries in both markets
  [ASSUMPTION: 15]. Re-enabling is HITL-13.
- No response time is imposed on the human for HITL-1. The system stays off until they act.

Edge cases:
- A request is raised one minute before the close: it expires at the close. It is raised again
  next session if still needed.
- The approval arrives after expiry: rejected. The audit trail records the late attempt.
- The approval arrives, and the condition that prompted it has changed: an approval names the
  exact object approved (a model hash, a policy version, a reconciliation difference). If the
  object differs, the approval does not apply.
- A critical alert fires at 01:00 India time: no acknowledgement is likely. Entries are
  disabled at 01:15. This is the designed outcome, not a failure.
- The human is unreachable for several sessions: no new entries; open positions keep their
  resting stops; nothing is liquidated automatically. Whether a time limit should force a
  flatten is OQ-24.
- The same person requests and approves: allowed. There is one operator. P6.2 authenticates
  them.
- Two approvals of the same request: the second is rejected.

Consequences. P1.4 defines approval events. P6.2 defines who may approve and how they are
authenticated. Night-time US incidents resolve to "entries disabled" until morning.

Revisit when: a second operator exists (option D becomes possible), or approvals expire
unanswered on more than 3 sessions in any 60 [ASSUMPTION: 3 in 60].

### ADR-10 — Disaster recovery: RPO 60 seconds, RTO 4 hours, "recovered" means reconciled

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Summary section 20, question 10, and section 21, item 4. Everything runs on one VM
(STACK-1). The audit trail must survive (INV-5). The broker, not the VM, holds the true
positions and orders. STACK-1 names no place to keep a backup (BQ-8).

Options considered:

| Option | Cost |
|--------|------|
| A. Nightly database backup kept on the VM | Nothing off the VM. Losing the disk loses the audit trail entirely. |
| B. Nightly backup copied off the VM | One storage bucket. Up to a full day of audit records lost: RPO 24 hours. |
| C. A daily base backup plus continuous write-ahead-log archiving off the VM | One storage bucket and archive configuration. RPO is the archive interval. Recovery is a restore and replay, which takes time. |
| D. A synchronous replica on a second host | RPO zero and fast recovery. A second host, outside STACK-1; a replica outage would block every audit write and therefore every action. |

Decision. C. [DEFAULT-19]
- RPO: 60 seconds for the database, by forcing a write-ahead-log segment to the off-VM archive
  at least every 60 seconds [ASSUMPTION: 60].
- Records lost inside the RPO window are rebuilt from the broker's order and fill history and
  appended as recovery records. They are never inserted into the past.
- RTO: 4 hours from the declaration of a disaster to REC-6 [ASSUMPTION: 4]. Independently of
  the 4 hours, a market that is not recovered before its next order window stays disabled for
  that session.
- No backup broker. A position cannot be moved between brokers during an outage. If a broker
  is down, that market has no new entries and relies on the stops resting at that broker.
- A backup market-data provider is P0.2's decision (summary section 21, item 10).

"Recovered" means all six hold, in this order:

| ID | Condition |
|----|-----------|
| REC-1 | The database is restored and the audit hash chain verifies from the first record to the last restored one. |
| REC-2 | The gap between the last restored record and the moment of failure is identified and written as a recovery record. |
| REC-3 | Positions, open orders and cash at each broker are read and compared with the restored state. Every difference is explained by a broker record or accepted by a human (HITL-8). |
| REC-4 | Every open position has a stop resting at its broker. A position without one is given one before anything else. |
| REC-5 | The kill switch is in the tripped state. It is restored tripped regardless of its state before the failure. |
| REC-6 | A human declares recovery complete (HITL-9) and re-enables (HITL-1). |

Edge cases:
- An order was sent, and the VM died before the acknowledgement was stored: REC-3 finds it at
  the broker. It is adopted or cancelled by HITL-8. It is never re-sent.
- The off-VM archive is unreachable while the VM is healthy: the RPO is no longer met. New
  entries are disabled until archiving resumes. Exits continue.
- The local audit file sink ([DEFAULT-2]) is on the same disk as the database: it does not
  survive a disk loss and gives no protection in this scenario.
- The restore succeeds and the chain fails to verify: not recovered. No trading. Escalated.
- The broker's history does not reach back to the failure time: the difference is unexplained
  and needs HITL-8.
- The disaster happens with no open positions: REC-4 is trivially true; the rest still apply.
- A restore is attempted during a session: RTO may pass the close. The market stays disabled;
  resting stops are the only protection, and they do not protect against a gap.

Consequences. One off-VM storage location is needed, which STACK-1 does not list; this is
flagged for the Owner (BQ-8). P6.4 specifies backup, restore and drills. P5.5 tests REC-1 to
REC-6. P1.4 defines the recovery record.

Revisit when: a restore drill takes longer than 4 hours, or the Owner allows a second host
(OQ-12), which makes option D available.

### ADR-11 — Markets: dual-market design from day one, India live first

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Prompt item 11. INV-10: two markets, nothing US-only by accident. The manual kill
path and the HITL list both lean on one human, assumed to be in India [DEFAULT-12].

Options considered:

| Option | Cost |
|--------|------|
| A. Build and go live in the US first; add India later | Fastest first trade in one market. India becomes a retrofit, which is how "US-only by accident" happens. The live market trades while the operator sleeps (ADR-09). Capital must be remitted under the limit in F-4. |
| B. Build and go live in India first; add the US later | The operator is awake. Capital is in its home currency. The US becomes the retrofit. |
| C. Build both and go live in both at once | No retrofit. Two brokers, two regulators and two calendars fail together for the first time on the same day. |
| D. Build both from day one; paper-trade both together; go live in one, then the other | No retrofit. Each phase carries both markets, so each phase is larger. Live incidents are met one market at a time. |

Decision. D, with India live first. [DEFAULT-14]
- Every type, table, job and test carries a market. A phase is not complete until both markets
  pass its tests.
- Both markets are paper-traded together through the P6.5 stages.
- India goes live first. The US goes live only after India has passed the P6.5 live gates and
  OQ-6 and OQ-14 are answered.
- A market can be enabled and disabled independently at run time.

Edge cases:
- A feature exists for one market only, for example a filing type: it is declared
  market-scoped in the spec that defines it. Undeclared is a defect.
- The first live market is disabled for a long period: the other does not go live in its place
  without HITL-2.
- A phase cannot be completed for one market because a vendor fact is missing: the phase stays
  DRAFT. It is not frozen for one market.
- A security is listed in both markets, as an Indian share and as a US depositary receipt:
  ADR-05 excludes the depositary receipt, so there is no double exposure in v1.
- Both markets are closed on the same day: no jobs run that produce orders.

Consequences. Every downstream spec is dual-market. Stage 0 and Stage 1 work roughly doubles
in vendor fact-finding. If BQ-1 is answered "not India", the first live market is re-decided
and nothing else in the design changes.

Revisit when: OQ-6 or OQ-14 shows the US account cannot be held, or OQ-1 and OQ-7 show the
India path cannot be operated by one person.

### ADR-12 — Direction: long-only, no borrowing

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Prompt item 12. C-2 and C-3 in the constitution. INV-8 forbids autonomous leverage.
F-4 prohibits margin remittance abroad for an Indian resident. F-3: the US account is a margin
account by type.

Options considered:

| Option | Cost |
|--------|------|
| A. Long-only, no borrowing | Simplest sizing and stops. No profit from falling prices. RISK-3 can never be reached. |
| B. Long-only with margin up to RISK-3 | Larger positions. Interest, margin calls and forced liquidation by the broker. Leverage chosen by the system, which INV-8 forbids, and which F-4 may make unlawful for the US account. |
| C. Long and short | Two-sided. Borrow availability and cost, recalls, unlimited loss on a short, and a short-side stop that RISK-12 does not define. Overnight shorts in the Indian cash segment are believed unavailable to retail clients (A-34, unverified). |
| D. Long-only with an index hedge | Needs futures or inverse ETFs, both excluded by ADR-05. |

Decision. A. This confirms [DEFAULT-3] for v1 and closes C-2 and C-3 for v1.
- No short sale. A sell order is never larger than the settled, held quantity.
- No borrowing. In each account the total cost of open buy orders plus the cost of the order
  being checked is at most the settled cash in that account. [DEFAULT-16]
- RISK-3 (gross at most 2x) stays in the record and is unreachable. RISK-4 (net at most 1x)
  is the binding exposure limit.
- RISK-12 applies as written.

Edge cases:
- Proceeds of a sale made today: not settled cash until settlement (A-27). They cannot fund a
  buy today.
- A buy fills at a better price than its limit: less cash is used; no issue. It cannot fill
  worse than its limit.
- The broker reports buying power larger than cash (F-3): buying power is ignored. Only
  settled cash is read.
- A dividend, fee or tax debit takes cash below zero: no new buys until it is non-negative.
  It is escalated, because a negative cash balance is borrowing.
- A sell is sent while a resting stop for the same shares is live: together they must never
  exceed the held quantity. P3.4 owns the mechanism ([DEFAULT-4] edge case).
- A split increases the share count between the decision and the order: quantities are
  re-read from the broker before any sell.

Consequences. P2.8 sizes against settled cash. P2.9 has no short-side rules. P2.6 can respond
to a bearish regime only by reducing or stopping entries. The system holds cash in a bear
market.

Revisit when: the Owner amends INV-8, or ADR-05 admits a hedging instrument.

### ADR-13 — Holding period: swing, decided once per session on daily bars

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Prompt item 13, with its required depth. The holding period fixes the data frequency
and, through it, almost everything else.

Options considered:

| Option | Cost |
|--------|------|
| A. Intraday: positions opened and closed inside a session | Minute or tick data for every instrument. A latency budget in seconds. Every trade is a same-day round trip, so the intraday margin standard (F-1) applies in full in the US, and in India each trade is an intraday trade for charges and tax (A-33, unverified). LLM calls scale with bars, not sessions. An operator awake for both sessions. |
| B. Swing: days to weeks, decided after each close on daily bars | Daily data. Hours between decision and order. Exposure to overnight gaps on every position. All gains short-term. |
| C. Position: months, decided weekly or monthly | Least data and least trading. Few trades a year, so ADR-08's 100 trades take many quarters and model validation becomes very slow. |
| D. Mixed: swing entries with intraday exits managed by the system | Intraday data and an intraday latency budget for exits only. Two data frequencies and two decision loops. |

Decision. B. [DEFAULT-13]

| ID | Rule |
|----|------|
| HP-1 | One decision cycle per market per session, run after that session's close, using daily bars of completed sessions only. |
| HP-2 | An entry decided after the close of session D is submitted as a limit order for session D+1. It is never submitted in session D. |
| HP-3 | A strategy exit is decided the same way: after the close of D, submitted for D+1. |
| HP-4 | Inside a session the only things that can sell are the stop resting at the broker and the kill switch. |
| HP-5 | The strategy never initiates a buy and a sell of the same instrument in the same session. |

The expected holding time is 2 to 30 sessions [ASSUMPTION]. It is a description, not an
enforced limit. A maximum-hold exit, if any, is P3.4's.

Second-order effects:

| Area | Chain |
|------|-------|
| Data frequency | HP-1 needs daily bars only. Minute bars are not an input to any decision. A quote at order time may be needed to set a limit price; that is P3.2's question. |
| Storage volume | Daily: 1,000 instruments (500 per market, ADR-14) x 252 sessions x 10 years = 2,520,000 rows. One-minute bars for the same set: 500 x 390 x 252 x 10 = 491,400,000 (US) plus 500 x 375 x 252 x 10 = 472,500,000 (India) = 963,900,000 rows. Swing needs about 1/382 of the rows (A-25, A-26). Ranking the whole listed market needs daily bars for every listed stock; that count is OQ-19. |
| Latency | From the India close at 15:30 to the next open at 09:15 is 17 hours 45 minutes. From the US close at 16:00 to the next open at 09:30 is 17 hours 30 minutes (A-26). The daily path has hours, not seconds. P0.3 sets the budget inside that. |
| Cost model | Turnover is low. Each trade pays delivery-type charges in India, not intraday charges. The dominant cost is the gap between the decision price (close of D) and the fill (session D+1) plus the spread. P5.3 models it. |
| Day-trading rules | HP-5 means the strategy creates no same-day round trip. One can still occur: a stop resting at the broker can fire on the day of entry. In the US that is a transaction under the intraday margin standard (F-1); with zero borrowing ([DEFAULT-16]) no deficit should arise, but how Alpaca treats it is OQ-15. A firm may still apply the old pattern-day-trader rule until 2027-10-20 (F-1); Alpaca states it switched on 2026-06-04 (F-5). In India a same-day buy and sell is believed to be treated as intraday for charges and tax (A-33). |
| Tax | Every holding is far shorter than a year, so every gain is short-term wherever a holding-period distinction exists. No rate is stated here: India rates are OQ-17; US treatment depends on residency and is OQ-5 and OQ-18. Re-entering a stock within 30 days of a loss will be common in swing trading, so wash-sale tracking is needed if OQ-5 is answered "US taxpayer". |
| Slippage | Orders are limit orders placed for D+1 from a decision at the close of D. A backtest must fill at D+1 prices or later, never at the close of D. A limit order may not fill at all; an unfilled entry is cancelled at the end of D+1 and not chased. RISK-9 (1% of ADDV) keeps each order small against volume. |
| LLM affordability | The LLM is called at most once per gated candidate per session: 10 per market ([DEFAULT-17]) x 2 markets = 20 calls per day when both markets trade, x 252 = 5,040 calls a year, about 420 a month. Response time is not a constraint. P0.3 multiplies by tokens and price. At one-minute frequency the same gate would allow up to 390 times as many decision points per session, which no stated budget covers. |
| Operations | The operator acts between sessions. Nothing in the decision path needs a human during a session (ADR-09). |
| Stops | The stop must rest at the broker, because the system does not watch prices inside the session ([DEFAULT-4], OQ-11). A gap through the stop fills at the market, below the stop price. |

Edge cases:
- Session D+1 is a holiday or the market is closed unexpectedly: the order goes to the next
  session that opens. If more than one session passes, the decision is stale and the order is
  not sent; the next decision cycle decides afresh.
- The daily bar for D arrives late or fails validation: no decision for that instrument for D
  (INV-6). It is not decided on D-1's bar.
- A half-day: the cycle runs after the early close.
- A stop fires on the day of entry: allowed (HP-4). It is recorded as a same-day round trip.
- A corporate action takes effect on D+1: the order decided on D is cancelled before the open
  and re-decided, because its price and quantity refer to the old share basis.
- An entry order is partly filled at the close of D+1: the unfilled part is cancelled. The
  filled part is a position and gets its stop.
- Trading halts in a held stock: a resting stop cannot fill during a halt. Nothing is done
  until trading resumes.
- A decision cycle overruns into the next session's order window: its orders are not sent
  (ADR-02 deadline rule).

Consequences. P0.3 sizes for daily data. P2.1 ingests end-of-day data as its required path.
P3.3 monitors positions between sessions and relies on broker-side stops inside them. P5.1
fills at D+1.

Revisit when: P5.2 shows the edge does not survive the D-to-D+1 gap after costs, or the Owner
wants exits managed inside the session (option D).

### ADR-14 — Universe: 500 per market by traded value, rebuilt monthly; decisions every session

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Prompt item 14, with its required depth. The universe size sets data volume, scan
cost and how many candidates reach the LLM gate.

Options considered:

| Option | Cost |
|--------|------|
| A. Index constituents (a large-cap or broad index per market) | A familiar set. Needs point-in-time constituent history for backtests, which is licensed data; without it the backtest has survivorship bias. |
| B. Every listed common stock | No selection rule to defend. Many names are too illiquid for RISK-9; data volume and vendor cost are the highest. |
| C. Top K per market by traded value, computed from our own price history | Point-in-time by construction, if delisted stocks are in the history. Needs daily bars for the whole listed market to compute the ranking. |
| D. A hand-picked watchlist | Smallest. Not reproducible, and a human choosing stocks is a strategy change outside ADR-08. |

Decision. C, with K = 500. [DEFAULT-15]

| ID | Rule |
|----|------|
| UNI-1 | The universe of a market is the 500 eligible common stocks with the highest median daily traded value over the trailing 60 sessions, in the market's currency [ASSUMPTION: 500, 60]. |
| UNI-2 | It is rebuilt once a month. It takes effect on the first session of the calendar month and is computed from data up to and including the last session of the previous month. |
| UNI-3 | Eligible means: instrument class is common stock (ADR-05); at least 60 sessions of validated daily bars; not suspended on the computation date. Further filters, such as price, are P2.3's. |
| UNI-4 | Ties in traded value are broken by the internal instrument identifier, ascending. |
| UNI-5 | A held stock that leaves the universe is kept and managed to its exit. It receives no new buys. |
| UNI-6 | The decision cycle runs every session (HP-1). There is no periodic re-weighting of held positions ([DEFAULT-9]). |

Second-order effects:

| Area | Chain |
|------|-------|
| Position count | RISK-1 caps a position at 5% of NAV and RISK-4 caps the total at 100%, so 20 full-size positions fill an account. RISK-2 at 20% allows 4 full-size positions in one sector. |
| Which limit binds | Risk-based size is 1% of NAV divided by the stop distance (RISK-8, RISK-12). As a fraction of NAV that is 1% / (2.5 x ATR%). The 5% cap binds whenever 2.5 x ATR% is below 20%, that is whenever daily ATR is below 8% of price. For most liquid stocks the 5% cap, not the 1% risk, sets the size. |
| Loss at the stop | With the cap binding, the loss at the stop is 5% x 2.5 x ATR%. At ATR 2% that is 0.25% of NAV per position; at 3%, 0.375%. |
| Loss if every stop fires | 20 positions x 0.25% = 5.0% of NAV at ATR 2%; 20 x 0.375% = 7.5% at ATR 3%. Both exceed RISK-5 (2% a day), and gaps make it worse. Resting stops alone can breach the daily limit and approach RISK-7 (10%). Block A has no limit on total open stop risk. This is OQ-23. |
| Small accounts | India trades whole shares. If one share costs more than 5% of NAV, the quantity rounds to zero and no order is sent ([DEFAULT-21]). At a small NAV this removes high-priced names. Whether the US broker supports fractional shares is part of OQ-15. |
| Data and storage | 1,000 universe instruments. The ranking needs the whole listed market at daily frequency (OQ-19). |
| LLM gate | At most 10 candidates per market per session reach the LLM ([DEFAULT-17]), 2% of the universe. |
| Order rate | A cycle that opens 20 positions needs 20 orders: 57 seconds at the spacing in [DEFAULT-5]. Well inside the hours available (ADR-13). |
| Validation | 20 slots turning over every 2 to 30 sessions gives enough closed trades for ADR-08's 100 within its window only if holding times are toward the short end. P5.2 checks this (OQ-20). |

Edge cases:
- Fewer than 500 stocks are eligible: the universe is smaller. It is not padded.
- A stock listed 59 sessions ago: not eligible this month.
- The first calendar day of the month is a holiday: the universe takes effect on the first
  session.
- A symbol changes, or two companies merge: identity follows the internal instrument
  identifier, not the ticker. The history of the surviving identifier is used.
- A stock is suspended on the computation date and resumes two days later: not eligible until
  the next monthly rebuild.
- A day with no trades in a stock counts as traded value zero in the median. It is not
  skipped.
- The rebuild job fails: the previous month's universe stays in force and an alert is raised.
  New entries are denied for any stock whose eligibility cannot be confirmed.
- A stock is delisted while held: a corporate-action event; P2.1 and P3.4 handle it. It is not
  in the next universe.
- Traded value is computed in local currency, so the two markets' universes are never ranked
  against each other.

Consequences. P0.2 must find a data source with delisted-stock history for both markets. P0.3
sizes for the full listed market at daily frequency. P2.3 implements UNI-1 to UNI-5.

Revisit when: P0.3 shows the full-market daily data is unaffordable (then option A with
licensed constituents is re-examined), or P5.2 shows too few trades for ADR-08.

### ADR-15 — Currency: each account in its own currency, no FX in the risk path, INR for reporting

Status: PROPOSED. Decision owner: Owner. Date: 2026-10-13.

Context. Prompt item 15. U-1 in the constitution. Two accounts in two currencies. INV-6
forbids defaulting a missing market value, and an FX rate is a market value.

Options considered:

| Option | Cost |
|--------|------|
| A. One combined NAV in INR, used for every limit | One set of limits. Every risk check depends on an FX rate; when the rate is missing, both markets are denied. A currency move changes position limits with no trade. |
| B. One combined NAV in USD, used for every limit | As A, with the home-currency account converted instead. |
| C. Two accounts, each measured in its own currency; limits per account; a combined figure for reporting only | No FX dependency in trading. Limits are tighter than a combined limit would be. Currency gains and losses on the US account are invisible to the risk engine. |
| D. Two fully separate systems | No shared state at all. Two of everything to run, and no combined view. |

Decision. C. This confirms [DEFAULT-7] and adopts [DEFAULT-18].
- The US account is measured in USD and the India account in INR.
- NAV and equity are one number per account ([DEFAULT-7]). Every RISK limit is applied per
  account.
- No FX rate is read anywhere in the decision, sizing, risk or execution path.
- The system never converts currency and never moves money between accounts. Funding is a
  human action (HITL-10) and is recorded as an external cash flow in each account affected.
- Reporting: combined NAV in INR = India NAV + US NAV x the USD/INR reference rate. It is
  computed once per India calendar day and is shown with the as-of time of each of its three
  inputs. It is used by no rule.

Edge cases:
- No reference rate for the day (an Indian holiday, a source outage): the combined figure is
  shown as unavailable. Yesterday's rate is not reused. Trading is unaffected.
- The US close used in the figure is from the previous US session, because the India day ends
  before the US session does: the figure says so through its as-of times.
- The rupee falls 10% against the dollar: the US account's limits do not change. The combined
  INR figure rises. Measured in INR, the US account can gain or lose value with no trade and
  no limit will react. That is accepted and stated.
- A drawdown trip is per account and kills both ([DEFAULT-8]). A combined-currency drawdown is
  not computed for any rule.
- A transfer leaves one account today and arrives in the other two days later: each account
  records its own flow on its own date. In between, the combined figure is lower by the amount
  in transit; the report lists flows in transit.
- One account is unfunded: its NAV is zero and it places no orders. The other is unaffected.
- Rounding: the combined figure is reported to two decimal places, rounded half to even.

Consequences. P1.1 has a currency on every money value and no implicit conversion. P2.9 has no
FX input. P6.1 shows the combined figure. The reference-rate source is OQ-22.

Revisit when: the Owner wants capital allocated between markets by rule, which needs a
combined NAV in the decision path.

## 5. Decisions that constrain everything else

1. **Swing trading on daily bars (ADR-13).** One decision per market per session, after the
   close; orders for the next session. No minute data in any decision. Hours, not seconds, of
   latency budget.
2. **Long-only, no borrowing (ADR-12).** Buys are funded by settled cash only. No shorts, no
   margin, no short-side rules anywhere.
3. **Common stock only (ADR-05).** One instrument class. No hedge instrument.
4. **Two markets in every type, table and test; India live first (ADR-11).** A phase is not
   done until both markets pass.
5. **Two accounts, two currencies, no FX in the risk path (ADR-15).** Every limit is per
   account. INR is for reporting only.
6. **Universe of 500 per market by traded value, rebuilt monthly (ADR-14).** Needs daily data
   for the whole listed market, including delisted stocks.
7. **Stops rest at the broker (ADR-13, [DEFAULT-4]).** The system does not watch prices inside
   a session.
8. **One VM, no Kubernetes, one in-process scheduler, no vector store (ADR-02, 03, 06).**
9. **FastAPI for actions, Grafana for viewing, no web UI (ADR-01).**
10. **Fourteen actions need a human; unanswered requests expire; nothing is approved by
    timeout (ADR-09).**
11. **Models change only by quarterly or triggered retrain, then one shadow test, then a human
    (ADR-07, ADR-08).** A loss is never a trigger.
12. **No alternative data (ADR-04).**
13. **Recovery means reconciled with the broker and re-enabled by a human; RPO 60 seconds,
    RTO 4 hours; backups live off the VM (ADR-10).**

Three things in this spec are not settled and can overturn items above:
- BQ-1, the account holder's residency. It underlies items 2, 4 and 5.
- OQ-14, whether the US account can lawfully be held as Alpaca offers it.
- OQ-23, total open stop risk. Under item 6's arithmetic, stops alone can lose 5% to 7.5% of
  NAV in a day against a 2% daily limit.

## 6. Mapping of the research summary

### 6.1 Section 19, decisions already made

| Row | Summary decision | Constitution item | Note |
|-----|------------------|-------------------|------|
| 1 | Deterministic risk engine overrides AI | INV-1 | Consistent. |
| 2 | LLMs gated | INV-3 | Consistent. Width set by [DEFAULT-17]. |
| 3 | Three-tier screening | INV-3 | Consistent. Tier sizes: ADR-14. |
| 4 | Volatility-based sizing with hard caps | RISK-1, RISK-8, RISK-12 | Consistent. ADR-14 shows the cap usually binds. |
| 5 | Kill switch automatic, manual, infrastructure-level | INV-7 | C-4 open; OQ-12. |
| 6 | ATR stop | RISK-12 | UP-8. |
| 7 | Append-only verifiable audit trail | INV-5 | Consistent. |
| 8 | External content untrusted | INV-4 | Consistent. |
| 9 | Walk-forward validation | none in Block A | P5.2. |
| 10 | Paper trading before live, 7 stages | none in Block A | UP-9; P6.5. |
| 11 | US broker Alpaca plus separate data provider | INV-10 | UP-4. |
| 12 | India broker Zerodha Kite | INV-10 | C-6; OQ-7. |
| 13 | Python, FastAPI, PostgreSQL/TimescaleDB, Redis | STACK-1 | Consistent. |
| 14 | DeepSeek primary, GPT-4o-mini backup | STACK-1 | Consistent. |
| 15 | No bull/bear/debate agents | none in Block A | Carried as a constraint on P4.3. |
| 16 | LLM-controlled execution never | INV-2 | Consistent. |
| 17 | AI changing risk limits never | INV-2 | Consistent. |
| 18 | Autonomous leverage never | INV-8 | ADR-12 makes it true for v1. |
| 19 | SEBI compliance from day one | INV-9 | OQ-1 partly answered by F-2. |
| 20 | Never "trade lost, change strategy" | INV-8 | ADR-07 lists the non-triggers. |

### 6.2 Section 20, open questions

| Row | Question | Closed by |
|-----|----------|-----------|
| 1 | Frontend | ADR-01 |
| 2 | Orchestration | ADR-02 |
| 3 | Kubernetes | ADR-03 |
| 4 | Alternative data | ADR-04 |
| 5 | Multi-asset | ADR-05 |
| 6 | Vector database | ADR-06 |
| 7 | Retraining frequency | ADR-07 |
| 8 | Champion/challenger | ADR-08 |
| 9 | Human approval | ADR-09 |
| 10 | Disaster recovery | ADR-10 |

### 6.3 Section 21, missing research

None is closed by this spec (UP-2).

| Row | Area | Owning phase | Related item here |
|-----|------|--------------|-------------------|
| 1 | Broker API limitations | P0.2 | OQ-7, OQ-11, OQ-15 |
| 2 | SEBI implementation standards | P0.2, P6.3 | OQ-1, F-2 |
| 3 | Market data provider selection | P0.2 | OQ-19 |
| 4 | Disaster recovery procedures | P6.4 | ADR-10 gives the targets; no backup broker |
| 5 | Tax implications | P6.3 | OQ-5, OQ-17, OQ-18 |
| 6 | Model hyperparameters | P2.5 | none |
| 7 | LLM prompt engineering | P4.3 | none |
| 8 | Cost breakdown by provider | P0.2, P0.3 | UP-6 |
| 9 | SEC/FINRA registration if managing others' money | P6.3 | Out of scope while the only capital is the Owner's own [ASSUMPTION, A-36] |
| 10 | Backup data providers | P0.2 | ADR-10 |

## 7. Typed form

Two entities are defined: the ADR record and the set of scope decisions. HITL, HP, UNI and REC
items are rules cited by identifier.

### 7.1 Models

```python
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class Market(StrEnum):
    US = "US"
    IN = "IN"


class Currency(StrEnum):
    USD = "USD"
    INR = "INR"


class AdrStatus(StrEnum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    SUPERSEDED = "SUPERSEDED"


AdrId = Annotated[str, StringConstraints(strict=True, pattern=r"^ADR-(0[1-9]|1[0-5])$")]
NonEmptyText = Annotated[str, StringConstraints(strict=True, min_length=1)]


class AdrOption(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    label: NonEmptyText
    cost: NonEmptyText


class AdrRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    adr_id: AdrId
    title: NonEmptyText
    status: AdrStatus
    context: NonEmptyText
    options: tuple[AdrOption, ...] = Field(min_length=3)
    decision: NonEmptyText
    consequences: NonEmptyText
    revisit_when: NonEmptyText
    decision_owner: NonEmptyText
    decided_on: date
    superseded_by: AdrId | None = None

    @model_validator(mode="after")
    def _superseded_consistent(self) -> "AdrRecord":
        if (self.status is AdrStatus.SUPERSEDED) != (self.superseded_by is not None):
            raise ValueError("superseded_by is set if and only if status is SUPERSEDED")
        if self.superseded_by == self.adr_id:
            raise ValueError("an ADR cannot supersede itself")
        return self


def _int(value: int) -> int:
    return Field(default=value, ge=value, le=value)


def _dec(value: str) -> Decimal:
    return Field(default=Decimal(value), ge=Decimal(value), le=Decimal(value))


class ScopeDecisions(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    operator_surface: Literal["fastapi_and_grafana"] = "fastapi_and_grafana"
    scheduler: Literal["asyncio_in_process"] = "asyncio_in_process"
    kubernetes: Literal["not_used"] = "not_used"
    vector_db: Literal["not_used"] = "not_used"
    alternative_data_sources: tuple[()] = ()
    tradable_instrument_classes: tuple[Literal["common_stock"]] = ("common_stock",)
    scheduled_retrain_interval: Literal["calendar_quarter"] = "calendar_quarter"
    drift_psi_threshold: Decimal = _dec("0.25")
    drift_consecutive_sessions: int = _int(5)
    out_of_cycle_retrains_per_month_max: int = _int(1)
    cc_min_sessions: int = _int(60)
    cc_max_sessions: int = _int(120)
    cc_min_closed_trades: int = _int(100)
    cc_alpha_one_sided: Decimal = _dec("0.05")
    cc_bootstrap_resamples: int = _int(10000)
    cc_bootstrap_block_sessions: int = _int(5)
    cc_concurrent_challengers_max: int = _int(1)
    approval_expiry: Literal["end_of_session"] = "end_of_session"
    critical_alert_ack_minutes: int = _int(15)
    rpo_seconds: int = _int(60)
    rto_hours: int = _int(4)
    markets_in_design: tuple[Literal[Market.US], Literal[Market.IN]] = (Market.US, Market.IN)
    first_live_market: Literal[Market.IN] = Market.IN
    direction: Literal["long_only"] = "long_only"
    borrowing: Literal["not_allowed"] = "not_allowed"
    holding_period_class: Literal["swing"] = "swing"
    decision_bar: Literal["1d"] = "1d"
    decision_cycles_per_session: int = _int(1)
    universe_size_per_market: int = _int(500)
    universe_rank_window_sessions: int = _int(60)
    universe_reconstitution: Literal["first_session_of_calendar_month"] = (
        "first_session_of_calendar_month"
    )
    llm_gate_width_per_market_per_session: int = _int(10)
    us_account_currency: Literal[Currency.USD] = Currency.USD
    in_account_currency: Literal[Currency.INR] = Currency.INR
    reporting_currency: Literal[Currency.INR] = Currency.INR
    fx_in_risk_path: Literal["not_used"] = "not_used"
```

`ScopeDecisions` records what this spec decides. Like `ConstitutionRiskDefaults`, each field
accepts only the decided value. A phase that turns one of these into a configurable policy key
(P1.3) sets its default equal to the field here and tests that equality.

### 7.2 Fields of `AdrRecord` and `AdrOption`

No field carries a time of day, so timezone applies only to `decided_on`.

| Field | Type | Unit | Timezone | Nullable | Valid range | A violation means |
|-------|------|------|----------|----------|-------------|-------------------|
| adr_id | str | none | none | no | `ADR-01` to `ADR-15`, two digits | The record names an ADR this spec does not contain; rejected (E-1). |
| title, context, decision, consequences, revisit_when, decision_owner | str | none | none | no | at least 1 character | An ADR with a missing part; rejected (E-1). |
| status | AdrStatus | none | none | no | PROPOSED, ACCEPTED, SUPERSEDED | Unknown status; rejected (E-1). |
| options | tuple of AdrOption | none | none | no | 3 or more items | Fewer than three options were considered; rejected (E-1). |
| decided_on | date | calendar date | `Asia/Kolkata` [DEFAULT-12] | no | a valid ISO 8601 date, passed as a `date` object | A string or a datetime was passed; rejected (E-1). |
| superseded_by | str or None | none | none | yes | None unless status is SUPERSEDED; then a different valid `adr_id` | Status and reference disagree, or an ADR supersedes itself; rejected (E-2). |
| AdrOption.label, AdrOption.cost | str | none | none | no | at least 1 character | An option with no stated cost; rejected (E-1). |

### 7.3 Fields of `ScopeDecisions`

No field is nullable and none carries a time. The valid range of every field is its single
decided value. A violation of any row is E-3.

| Field | Type | Unit | Decided value | Source |
|-------|------|------|---------------|--------|
| operator_surface | str literal | none | `fastapi_and_grafana` | ADR-01 |
| scheduler | str literal | none | `asyncio_in_process` | ADR-02 |
| kubernetes | str literal | none | `not_used` | ADR-03 |
| vector_db | str literal | none | `not_used` | ADR-06 |
| alternative_data_sources | empty tuple | none | `()` | ADR-04 |
| tradable_instrument_classes | 1-tuple | none | `("common_stock",)` | ADR-05 |
| scheduled_retrain_interval | str literal | none | `calendar_quarter` | ADR-07 |
| drift_psi_threshold | Decimal | dimensionless index | 0.25, breach is strictly above | ADR-07, ASSUMPTION |
| drift_consecutive_sessions | int | sessions | 5 | ADR-07, ASSUMPTION |
| out_of_cycle_retrains_per_month_max | int | retrains per market per calendar month | 1 | ADR-07, ASSUMPTION |
| cc_min_sessions | int | sessions | 60 | ADR-08, ASSUMPTION |
| cc_max_sessions | int | sessions | 120 | ADR-08, ASSUMPTION |
| cc_min_closed_trades | int | closed challenger trades | 100 | ADR-08, ASSUMPTION |
| cc_alpha_one_sided | Decimal | probability, 0.05 means 5% | 0.05, reject only if p is strictly below | ADR-08, ASSUMPTION |
| cc_bootstrap_resamples | int | resamples | 10000 | ADR-08, ASSUMPTION |
| cc_bootstrap_block_sessions | int | sessions | 5 | ADR-08, ASSUMPTION |
| cc_concurrent_challengers_max | int | challengers per market | 1 | ADR-08 |
| approval_expiry | str literal | none | `end_of_session` | ADR-09 |
| critical_alert_ack_minutes | int | minutes | 15 | ADR-09, ASSUMPTION |
| rpo_seconds | int | seconds | 60 | ADR-10, ASSUMPTION |
| rto_hours | int | hours | 4 | ADR-10, ASSUMPTION |
| markets_in_design | 2-tuple of Market | none | `(US, IN)` in that order | ADR-11 |
| first_live_market | Market | none | `IN` | ADR-11, [DEFAULT-14] |
| direction | str literal | none | `long_only` | ADR-12 |
| borrowing | str literal | none | `not_allowed` | ADR-12, [DEFAULT-16] |
| holding_period_class | str literal | none | `swing` | ADR-13, [DEFAULT-13] |
| decision_bar | str literal | bar length | `1d` | ADR-13 |
| decision_cycles_per_session | int | cycles per market per session | 1 | ADR-13, HP-1 |
| universe_size_per_market | int | instruments | 500 | ADR-14, [DEFAULT-15] |
| universe_rank_window_sessions | int | sessions | 60 | ADR-14, ASSUMPTION |
| universe_reconstitution | str literal | none | `first_session_of_calendar_month` | ADR-14, UNI-2 |
| llm_gate_width_per_market_per_session | int | candidates | 10 | [DEFAULT-17] |
| us_account_currency | Currency | none | `USD` | ADR-15 |
| in_account_currency | Currency | none | `INR` | ADR-15 |
| reporting_currency | Currency | none | `INR` | ADR-15, [DEFAULT-18] |
| fx_in_risk_path | str literal | none | `not_used` | ADR-15 |

## 8. Error paths

| # | Condition | Detected by | Fail-closed behaviour |
|---|-----------|-------------|-----------------------|
| E-1 | An `AdrRecord` or `AdrOption` field is missing, empty, of the wrong type, or out of range. | Pydantic `ValidationError` at construction. | The record is not created. A check that loads ADR records fails. |
| E-2 | `status` and `superseded_by` disagree, or an ADR supersedes itself. | The model validator. | As E-1. |
| E-3 | A `ScopeDecisions` field is given anything but its decided value, an unknown field is supplied, or a field is assigned after construction. | Pydantic `ValidationError` (`strict`, `extra="forbid"`, `frozen`, equal bounds). | The object is not created or not changed. A process that constructs it at start-up does not start. |
| E-4 | A later spec states a value that differs from a field here without a superseding ADR. | X3 merge (contradiction list) and the P1.3 equality test. | The later spec is not frozen. |
| E-5 | An ASSUMPTION number here is shown wrong by its owning phase. | That phase. | That phase raises a new ADR that supersedes this one. The value here is not edited in place after FROZEN. |
| E-6 | BQ-1 is answered with a residency other than India. | Owner. | ADR-11, ADR-12, ADR-13 and ADR-15 return to PROPOSED and are re-decided before any spec that cites them is frozen. |
| E-7 | A HITL request is unanswered at expiry. | The scheduler, at the session close. | The request is closed as expired; what it would allow stays denied (ADR-09). |
| E-8 | A REC condition cannot be met. | The recovery procedure. | Not recovered. The kill switch stays tripped (REC-5). |

Evidence: the models in 7.1 were executed on 2026-10-13 with Python 3.11 and Pydantic 2.13.5.
Default construction of `ScopeDecisions` (36 fields) succeeded. Rejected as expected:
`universe_size_per_market` given 501, 500.0 or `True`; `direction="long_short"`; a non-empty
`alternative_data_sources`; `first_live_market=Market.US`; `markets_in_design` reversed;
`cc_alpha_one_sided=0.05` as a float; an extra field; an `AdrRecord` with two options, with
`ADR-16`, with `ADR-1`, with an empty title, with a string date, with SUPERSEDED and no
reference, with a reference and no SUPERSEDED status, and superseding itself. Accepted, and
recorded as a known behaviour: the plain string `"IN"` for `first_live_market`, because a
`StrEnum` member equals its string. Not run on Python 3.12 or later (R-4). `StrEnum` needs
Python 3.11 or later, which STACK-1 satisfies.

## 9. Non-blocking details resolved in this spec

| # | Detail | Resolution |
|---|--------|------------|
| NB-14 | Session identity | A session is identified by market and the exchange-local session date. "D+1" means the next session of that market, not the next calendar day. |
| NB-15 | "After the close" | Computed from the calendar's close time for that session, so half-days follow automatically. |
| NB-16 | Month and quarter boundaries | Calendar months and quarters in the exchange's timezone. The first session on or after the first calendar day. |
| NB-17 | Window lengths | "Trailing 60 sessions" includes the computation session and the 59 before it. An instrument with 59 has no value. |
| NB-18 | Median of an even count | The mean of the two middle values, computed in `Decimal`. |
| NB-19 | Thresholds | "Above 0.25" is strict. "At or below zero" includes zero. A p-value must be strictly below 0.05 to reject. "Not larger" includes equal. |
| NB-20 | Percent convention | Percent values follow A-4 (5 means 5%). The exception is `cc_alpha_one_sided`, a probability, where 0.05 means 5%; its unit column says so. |
| NB-21 | Counting sessions per year | 252 is used only for sizing arithmetic (A-25). No rule depends on it. |
| NB-22 | Whole shares | A quantity is rounded down. A quantity of zero means no order. |
| NB-23 | Expiry time for requests that concern no market | 23:59:59 `Asia/Kolkata`, inclusive. India has no daylight saving, so the instant is unambiguous. |
| NB-24 | Random seed | An integer fixed and written to the audit trail before an ADR-08 evaluation starts. |
| NB-25 | Rounding of the combined INR figure | Two decimal places, half to even. Reporting only. |
| NB-26 | Tick size, lot size, price rounding | Not resolved here. No rule in this spec produces a price. P1.1 and P3.2. |
| NB-27 | Integer or decimal money | Not resolved here. P1.1. |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| ADR-01 | FastAPI for actions, Grafana read-only, no web UI. | Nothing new in the stack; one audited place for approvals. | Yes. | P6.1, P6.2. |
| ADR-02 | One in-process asyncio scheduler on exchange calendars; order jobs never run late. | `cron` does not know sessions; frameworks are excluded by STACK-1. | Yes. | Every scheduled job. |
| ADR-03 | No Kubernetes; a capacity trigger leads to a second VM first. | STACK-1. | Yes. | P6.4. |
| ADR-04 | No alternative data in v1; five admission conditions. | No verified price, licence or history for any source. | Yes. | P2.4 features. |
| ADR-05 | Common stock only. | INV-8; smallest instrument model. | Yes, by new ADR. | P1.1, P2.3, P2.6. |
| ADR-06 | No vector storage. | STACK-1; no retrieval use case. | Yes. | P4.1, P4.3. |
| ADR-07 | Quarterly retrain; triggers T-1 to T-3; a loss is never a trigger. | INV-8; fits one ADR-08 evaluation per quarter. | Yes. | P6.6, P5.2. |
| ADR-08 | One challenger; shadow against shadow; one block-bootstrap test at 0.05; human promotes. | Reproducible and free of multiple comparisons. | Yes. | P6.6, P5.3. |
| ADR-09 | Fourteen HITL actions; expiry at end of session; nothing approved by timeout. | INV-7, INV-2, INV-8; one operator. | Yes. | P1.4, P6.2, operations. |
| ADR-10 | RPO 60 s by off-VM log archiving; RTO 4 h; REC-1 to REC-6; no backup broker. | The broker holds the truth; the audit trail must survive the VM. | Yes. | P6.4, P5.5, P1.4. |
| ADR-11 | Dual-market design; both paper; India live first. | INV-10; the operator is awake for India. | Order of go-live: yes. Dual design: costly to undo. | Every phase. |
| ADR-12 | Long-only, no borrowing; buys against settled cash. | INV-8, F-3, F-4. | Yes, with an Owner amendment. | P2.8, P2.9, P3.4. |
| ADR-13 | Swing on daily bars; HP-1 to HP-5. | Lowest data, latency and operating burden that still trades. | Hard: it sizes P0.3 and shapes P2.1, P3, P5. | Every phase. |
| ADR-14 | Universe 500 per market by traded value, monthly; UNI-1 to UNI-6. | Point-in-time from our own data; no licensed index. | Yes. | P0.2, P0.3, P2.3. |
| ADR-15 | Per-account currency; no FX in the risk path; INR reporting. | INV-6: an FX rate is a market value that can be missing. | Yes. | P1.1, P2.9, P6.1. |
| D-8 | Every ADR is PROPOSED until this spec is FROZEN. | The Owner has not reviewed them. | n/a | n/a |
| D-9 | No money cost is stated without a source. | RULE-1, RULE-2, UP-6. | n/a | n/a |
| D-10 | Identifier series continue from the constitution: DEFAULT-12 onward, A-15 onward, OQ-13 onward, NB-14 onward, D-8 onward. | One namespace across new-run specs avoids collisions at X3 merge. | Yes. | Renumbering. |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| A-15 | [DEFAULT-12] The account holder is an individual resident in India. | Not stated anywhere in the inputs; the India broker suggests it. | Owner answers BQ-1. | E-6: four ADRs re-decided. |
| A-16 | [DEFAULT-13] Swing holding period. | The inputs do not state one. | Owner confirms ADR-13. | P0.3 and most of Stage 2 are sized wrongly. |
| A-17 | [DEFAULT-14] India goes live first. | Follows from A-15. | Owner confirms ADR-11. | Go-live order only. |
| A-18 | [DEFAULT-15] Universe is the top 500 by 60-session median traded value, monthly. | No universe is given. 500 and 60 are round numbers, not derived. | P0.3 cost; P5.2 results. | Data volume and candidate quality. |
| A-19 | [DEFAULT-16] The US account is run with zero borrowing against settled cash. | F-3 leaves no cash-account option. | OQ-15. | INV-8 or F-4 breached. |
| A-20 | [DEFAULT-17] LLM gate width is 10 per market per session. | The inputs give no width. | P0.3 prices 5, 10, 20, 50. | LLM spend, linearly. |
| A-21 | [DEFAULT-18] Reporting currency is INR. | Follows from A-15. | Owner confirms. | A label. |
| A-22 | [DEFAULT-19] Backups and log archives may be stored off the VM. | STACK-1 names one VM and no backup target. | Owner answers BQ-8. | RPO unbounded on disk loss. |
| A-23 | [DEFAULT-20] ETFs and depositary receipts are not tradable in v1. | The inputs leave it undecided. | Owner confirms ADR-05. | Smaller universe. |
| A-24 | [DEFAULT-21] No starting capital is assumed. | Not stated. | Owner answers OQ-16. | Many instruments untradable at a small NAV. |
| A-25 | A year has 252 trading sessions. | Needed for sizing arithmetic only. | Exchange calendars, P0.2. | Row counts off by a few percent. |
| A-26 | US regular session 09:30 to 16:00 `America/New_York` (390 minutes); NSE 09:15 to 15:30 `Asia/Kolkata` (375 minutes). | Used for arithmetic and for the IST conversion in ADR-09. Not verified in this phase. | Exchange websites, P0.2 (OQ-26). | Arithmetic in ADR-09 and ADR-13. No rule depends on it; rules use the calendar. |
| A-27 | Both markets settle equity trades one session after the trade. | Affects when sale proceeds fund a buy (ADR-12). Not verified in this phase. | Exchange and broker documentation, P0.2 (OQ-26). | Settled-cash timing. The rule reads the broker's settled cash, so it stays correct; only the description changes. |
| A-28 | ADR-07 numbers: PSI window 20 sessions, threshold 0.25, 5 consecutive sessions; rank-correlation window 60 sessions; one out-of-cycle retrain a month. | No data in the inputs. 0.25 is a commonly used convention, not derived. | P5.2 and P6.6 on backtest data. | Too many or too few triggers. |
| A-29 | ADR-08 numbers: 60 and 120 sessions, 100 trades, block 5, 10,000 resamples, 0.05, 5% dropped sessions. | No data in the inputs. | P5.2 power calculation (OQ-20). | Promotions that are noise, or real improvements never promoted. |
| A-30 | Operations thresholds: 15 minutes to acknowledge; 3 expiries in 60 sessions; 5 missed deadlines in 20; four hosts. | No data in the inputs. | Owner; P6.1 after paper trading. | Alert fatigue or slow reaction. |
| A-31 | RPO 60 seconds and RTO 4 hours are achievable on the chosen VM and storage. | No restore has been timed. | P6.4 restore drill. | ADR-10 targets restated. |
| A-32 | Expected holding time is 2 to 30 sessions. | Descriptive; nothing enforces it. | P5.1 backtest distribution. | ADR-14's trade-count reasoning. |
| A-33 | In India a buy and sell of the same share on the same day is treated as an intraday trade for charges and tax. | Affects the entry-day stop edge case. Not verified. | Zerodha charges page; Income-tax guidance (OQ-17). | Cost and tax of entry-day stops. |
| A-34 | Retail clients cannot hold a short position overnight in the Indian cash segment. | Used only as a cost of option C in ADR-12. Not verified. | NSE and Zerodha documentation (OQ-25). | None on the decision; long-only rests on INV-8. |
| A-35 | The extracts F-1 to F-5 state their sources accurately. | They were retrieved by automated extraction, not read in full. | Full read by the phase named in section 2. | UP-3, UP-4, ADR-12 and ADR-13 reasoning. |
| A-36 | The only capital traded is the Owner's own. | Section 21 row 9 is conditional on managing others' money. | Owner confirms. | Registration requirements enter scope (P6.3). |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| OQ-13 | UP-3: will the Owner amend INV-9, which names the US pattern-day-trader rule that FINRA has replaced? | Owner | FINRA Regulatory Notice 26-10, read in full | P6.3 |
| OQ-14 | UP-4: may an Indian resident hold an Alpaca account, which is a margin account by type, under the Liberalised Remittance Scheme if no borrowing ever occurs? | A qualified adviser; the remitting bank | RBI FAQ Id=1834 Q2 item 2; FEMA Overseas Investment Rules 2022; the bank's LRS declaration form | US go-live (P6.5); P0.2 |
| OQ-15 | Does Alpaca offer a setting that prevents borrowing; which API field gives settled cash; how is a same-day stop exit treated under its intraday margin framework; are fractional shares supported for limit orders? | Alpaca | docs.alpaca.markets: account configuration, account fields, margin, fractional trading | P0.2, P2.8, P3.1 |
| OQ-16 | What starting capital will each account have? | Owner | Owner statement | P0.3, P2.8 |
| OQ-17 | India: tax rate on short-term gains on listed shares, treatment of same-day trades, and the transaction taxes and charges on delivery and intraday trades. | Income-tax Act as amended; the broker's charges schedule | incometax.gov.in; zerodha.com/charges | P5.3, P6.3 |
| OQ-18 | US tax treatment of the account holder's gains and dividends, given OQ-5. | A qualified adviser | IRS Publication 519; the India-US tax treaty | P6.3 |
| OQ-19 | How many common stocks are listed per market today, and how many have delisted in the last ten years; which vendor carries delisted history for each market? | Exchanges and data vendors | NYSE, NASDAQ, NSE, BSE listings; vendor coverage pages | P0.2, P0.3 |
| OQ-20 | Do the ADR-08 sample numbers give adequate power, and is one quarter the right retrain interval? | P5.2 | Power calculation on walk-forward backtest returns | P6.6 |
| OQ-21 | Which off-VM storage holds backups and log archives, in which region, at what cost? | Owner; P6.4 | The VM provider's object-storage pricing page | P0.3, P6.4 |
| OQ-22 | Which published USD/INR reference rate is used for reporting, and when is it published each day? | P0.2 | fbil.org.in reference rates | P6.1 |
| OQ-23 | Should there be a limit on total open stop risk across positions? Block A has none, and ADR-14 shows stops alone can lose 5% to 7.5% of NAV in a day against RISK-5 of 2%. | Owner | Ruling; then P2.8 | P2.8, P2.9 |
| OQ-24 | If no human responds for several sessions, should open positions be flattened after a time limit? | Owner | Ruling; then P2.10 | P2.10 |
| OQ-25 | A-34: can a retail client hold an overnight short in the Indian cash segment? | NSE; Zerodha | NSE securities lending and borrowing documentation; Zerodha support | None while ADR-12 stands |
| OQ-26 | A-26, A-27: exact session times, half-day rules and settlement cycles for NYSE, NASDAQ, NSE and BSE. | Exchanges | nyse.com, nasdaq.com, nseindia.com, bseindia.com: trading hours and holidays; settlement | P0.2, P2.1 |

Constitution questions still open and relevant here: OQ-1 (partly answered by F-2), OQ-5,
OQ-6, OQ-7, OQ-11, OQ-12. Closed for v1 by this spec, once FROZEN: OQ-3 (ADR-12).

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| ADR-01..ADR-15 | decision identifier | Section 4, cited as `ADR-nn` | every later spec |
| DEFAULT-12..DEFAULT-21 | provisional default identifier | Section 3, cited as `[DEFAULT-n]`; not a ruling | every later spec that builds on one |
| Market | type | `StrEnum`: `US`, `IN` | P1.1 and every later spec |
| Currency | type | `StrEnum`: `USD`, `INR` | P1.1, P2.9, P6.1 |
| AdrStatus | type | `StrEnum`: `PROPOSED`, `ACCEPTED`, `SUPERSEDED` | X3 merge, `docs/new specs/DECISIONS.md` |
| AdrId | type | strict `str` matching `ADR-01` to `ADR-15` | any spec citing an ADR |
| AdrOption, AdrRecord | type | Section 7.1; fields in 7.2 | X3 merge |
| ScopeDecisions | type | Section 7.1; frozen, 36 fields, section 7.3 | P0.2, P0.3, P1.1, P1.3 (default-equality test) |
| HP-1..HP-5 | rule identifier | ADR-13 table | P2.7, P3.2, P3.4, P5.1 |
| UNI-1..UNI-6 | rule identifier | ADR-14 table | P2.3 |
| HITL-1..HITL-14 | rule identifier | ADR-09 table | P1.4, P6.2 |
| REC-1..REC-6 | rule identifier | ADR-10 table | P5.5, P6.4 |
| T-1..T-3 | rule identifier | ADR-07 retrain triggers | P6.6 |
