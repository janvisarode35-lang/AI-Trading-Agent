---
id: SPEC-P0.1-DECISIONS
version: 0.3
status: FROZEN
phase: P0.1 — Decision Closure
depends_on: [master-research-summary.md §19 §20 §21, docs/PROMPT-PACK.md BLOCK-A, docs/PROMPT-PACK.md BLOCK-B, docs/PROMPT-PACK.md BLOCK-C]
supersedes: SPEC-P0.1-DECISIONS v0.2 (2026-08-25), v0.1 (2026-08-23)
frozen_by: STAGE-0-FREEZE.md (2026-08-25)
produces: [ADR-01..ADR-15, AD-1..AD-5, CONSTRAINT-SET-P0.1, config.universe, config.holding, config.market, config.fx, config.hitl, config.dr, config.retrain, config.llm, enum.Market, enum.AccountType, enum.InstrumentType, enum.ApproverRole]
---

# SPEC-P0.1 — Decision Closure

**Phase:** Stage 0 — DECIDE, prompt `P0.1`
**Date closed:** 2026-08-23
**Decision authority:** JS — Project Owner, acting as Head of Architecture and Risk Owner
**Next scheduled review:** 2027-02-23, or earlier on any listed revisit trigger
**Version 0.3, 2026-08-26:** four retrievals closed or answered M-2, M-3, M-5 and M-11a (STAGE-0-FREEZE §7 trigger T3). **No ADR and no AD changed.** ADR-04 gains the news point-in-time finding and rule N16; §9 is reclassified. **Stage 1 has no remaining documentary gate.**
**Version 0.2, 2026-08-25:** twenty amendments from P0.2 and P0.3 applied, five Owner
decisions taken (§0.5), Stage 0 frozen. **No v0.1 architectural decision is re-opened.**

This document closes every open question in `master-research-summary.md` §20 (10 open questions)
and the decision-shaped items in §21, plus the five foundational questions (#11–#15) the prompt
pack adds. **Nothing downstream may re-open these.** A later phase that believes an ADR here is
wrong must raise it as an amendment to *this* file under a new version number — it may not
quietly decide differently.

---

## 0. Governing material, precedence, and how this document was produced

### 0.1 Precedence actually applied

| Rank | Source | Where it lives | Applied? |
|---|---|---|---|
| 1 | Project Constitution | `docs/PROMPT-PACK.md` → BLOCK A | Yes, verbatim |
| 2 | Output Contract | `docs/PROMPT-PACK.md` → BLOCK B | Yes — the four mandatory tables are §7–§10 |
| 3 | Clarifier Rule | `docs/PROMPT-PACK.md` → BLOCK C | Yes — §5 (blocking) and §6 (non-blocking) |
| 4 | Accepted prior specs | none exist — P0.1 is the first phase | N/A |
| 5 | Current issue | GitHub issue *P0.1 — Decision Closure* | Yes |
| 6 | Dependency specs | issue states **"Depends on: nothing"** | N/A |
| 7 | Existing implementation | repo contains no source code | N/A |
| 8 | Research / evidence | `master-research-summary.md`, cited as `[RS §n]` | Yes |
| 9 | Engineering judgement | used only where 1–8 are silent; every such use is an ADR | Yes |

**Procedural note.** The execution request supplied Blocks A, B and C as unfilled placeholders
(`[PASTE THE COMPLETE CONSTITUTION HERE]`). The authoritative text was recovered from
`docs/PROMPT-PACK.md` on `origin/main` and applied verbatim. The local checkout was three
commits behind `origin/main` and was fast-forwarded so this deliverable sits alongside the
prompt pack and the research summary it cites. No content was invented to fill those blocks.

### 0.2 Fact-labelling convention

| Tag | Meaning |
|---|---|
| `[RS §n]` | Sourced from the master research summary, section *n* |
| `[CONST-n]` | Sourced from Constitution invariant *n* (Block A) |
| `ASSUMPTION` | Stated by this document, not verified against a primary source |
| `[VERIFY-P0.2]` | An ASSUMPTION whose verification is assigned to phase P0.2 |
| `[VERIFY-P0.3]` | An ASSUMPTION whose verification is assigned to phase P0.3 |
| `[DEFAULT-n]` | A Clarifier-Rule default used in place of an answer (see §5) |

Constitution Block A forbids inventing a fact, an API field, a rate limit, a fee or a
regulation. Every regulatory rate, tax rate, settlement cycle, provider price and rate limit
below is therefore either sourced to `[RS §n]` or carries an `ASSUMPTION` tag naming the phase
that must verify it. **No number here is presented as verified when it is not.**

### 0.3 Conflicts between sources, and their resolution

Block A requires that contradictions in upstream material be reported as part of the output.
Four were found; each is resolved here so no later phase inherits the ambiguity.

**C-1 — `[CONST-10]` "two markets, nothing US-only by accident" vs. question #11
"single-market-first or dual-market".**
*Resolution:* not a true conflict. `[CONST-10]` constrains **architecture** (the operative words
are "by accident"), not **funding sequence**. ADR-11 keeps the two-market contract mandatory in
every artifact from day one and sequences live capital US-first as a deliberate, dated, gated
decision. A deliberate sequence is not an accident. `[CONST-10]` is preserved in full.

**C-2 — Constitutional ceilings `gross <= 2x equity` / `net <= 1x equity` vs. ADR-12
(long-only, cash account, no margin).**
*Resolution:* ADR-12 **tightens**, it does not contradict. In a long-only cash account
gross ≡ net ≤ 1.0×, so the constitutional ceilings are retained in config as unreachable upper
bounds while `gross <= 1.0x` becomes binding. The risk engine enforces
`min(constitutional_ceiling, account_type_ceiling)`. Reaching 2× requires margin, which requires
the ADR-12 revisit procedure **and** ADR-09 Owner approval.

**C-3 — `[RS §12]` backtest acceptance "DD < 15%" vs. `[CONST]` "max drawdown ≤ 10% trips the
kill switch".**
*Resolution:* the research summary is wrong, and the error is dangerous — a strategy validated
at 15% drawdown would have been force-liquidated by its own kill switch in live trading, so the
backtest would be validating a strategy that cannot exist. **Decision:** every backtest and
walk-forward run **must simulate the kill switch**, including its human re-enable delay.
Acceptance becomes: max drawdown ≤ 10% *with the kill switch modelled*, and the kill switch
trips **≤ 1 time per 10-year backtest**. A strategy that trips it more often is rejected
regardless of return. Binding on P5.1, P5.2, P5.5.

**C-4 — `[RS §6 Phase 4]` Tier-2 score "60% Fundamental + 20% Technical + 10% Sentiment" sums to
90%, while `[RS §6 Phase 7]` uses "60 quant + 20 thesis + 10 sentiment + 10 technical" = 100%.**
*Resolution:* the Tier-2 weights do not sum to 1. Scoring weights are out of P0.1 scope (they
belong to P2.5/P2.8), so this ADR set does **not** set them — but the defect is recorded so the
downstream phase resolves it deliberately instead of copying a broken table. **Binding
instruction to P2.5/P2.8:** Tier-2 weights must be declared as a normalised vector that provably
sums to 1.0, validated at config-load, with a unit test asserting the sum. The 90% figure must
not propagate.

### 0.4 Corrections to the research summary carried by this phase

**R-1 — `[RS §16]` names the Pattern Day Trader rule as the binding US constraint on a small
account. Given ADR-12, it is not.** PDT is a **margin-account** rule `ASSUMPTION [VERIFY-P0.2]`.
ADR-12 selects a **cash account**, where PDT does not apply but **settled-funds rules do**:
proceeds are unavailable until settlement, and reusing unsettled proceeds creates good-faith /
free-riding violations carrying a 90-day restriction after repeat occurrences
`ASSUMPTION [VERIFY-P0.2]`. The risk engine must therefore size entries against **settled
cash**, not total cash. Both counters (`day_trades_5d` for the margin case, `settled_cash` for
the cash case) are specified in ADR-13 Chain D so a future switch to margin does not require
re-deriving the rule.

**R-2 — `[RS §20 Q6]` treats a vector database as an open question.** ADR-06 kills it and adds
the reason the research summary missed: an unaudited semantic memory is directly at odds with
`[CONST-5]` (append-only, verifiable audit of everything affecting a decision) and is precisely
the surface the memory-poisoning threat in `[RS §15]` describes.

**R-3 — `[RS §6 Phase 5]` states the gated LLM tier costs "~$200–500/month".** ADR-13 Chain G
computes the figure from token arithmetic: **under $5/month in live operation at any gate width
up to 50, on any model tier.** The $200–500 band is the right order of magnitude for something
else — *full-history LLM replay during backtesting* — and is retained as a budget **ceiling and
alarm threshold**, not a forecast. This materially changes the design objective of the inference
gate (P4.2): the gate exists for hallucination control and attack-surface reduction, **not** for
cost control.

---

## 0.5 Amendments applied in v0.2, and the Stage 0 freeze

v0.1 closed fifteen architectural decisions. v0.2 does **not** re-open any of them. It applies the
twenty amendments raised by SPEC-P0.2 (A-1 through A-12) and SPEC-P0.3 (A-13 through A-20), of
which five required the Owner's authority, and then freezes Stage 0.

**What "frozen" means here, stated because the prompt pack never defined it:** the *architectural
decisions* are frozen and may not be changed silently. It does **not** mean every research question
is closed — §9 carries eleven items forward explicitly. Reopening requires a documented trigger,
named in [STAGE-0-FREEZE.md](STAGE-0-FREEZE.md).

### 0.5.1 The five authority decisions

**AD-1 — Assumption A14 replaced (amendments A-6 and A-15).**
v0.1's `$30–200/month` retail-data band was an unverified estimate. It is replaced by a figure
that **keeps verified recurring cost and full operating cost visibly separate**, because
conflating them is how an infrastructure line disappears from a budget:

| Line | Paper (ladder stages 1–4) | Live (stage 5+) | State |
|---|---|---|---|
| Data + broker, verified | **≈ $129/mo** | **≈ $228/mo** | `[V]` P0.2 §4.3 |
| VM (4 vCPU / 16 GB / 250 GB NVMe / static IP) | **unpriced** | **unpriced** | `[U]` P0.3 Q-1 |
| Off-VM backup storage, ~300 GB | **unpriced** | **unpriced** | `[U]` P0.3 Q-2 |
| **Total infrastructure operating cost** | **INCOMPLETE** | **INCOMPLETE** | — |

> **The total is marked INCOMPLETE, not estimated.** No VM or backup price is invented here. Any
> downstream phase quoting a monthly total must quote the verified subtotal **and** the two
> unpriced lines, never the subtotal alone. P0.3 §8 carries the sensitivity table that converts
> either price into a total the moment Q-1 and Q-2 resolve.

**AD-2 — Walk-forward rolls set to 3 months (amendment A-13).**
P0.3 B-F4 showed `promotion.min_wf_windows = 34` is unreachable at 6-month rolls: expanding train
plus non-overlapping 6-month OOS windows needs ~20 years, and the purchased history is 10 years
(Massive Stocks Developer, $79/mo `[V]`). **Decision: 3-month rolls with a 1.5-year initial
training window**, which yields **34 windows from the 10 years already bought**. The 20-year
alternative (Massive Stocks Advanced, **+$120/mo**) is **rejected** — nothing in the architecture
requires 20 years, and ADR-08's own premise is window count and independence, both of which
3-month rolls satisfy. At ADR-13's ~3,400 closed trades per decade this places **~100 closed
trades in each window**. ADR-08 Stage 1 and `config.promotion.*` are updated in place.

**AD-3 — The US backup broker is MANUAL-ONLY (amendment A-9).**
P0.2 F-12 verified that IBKR's Client Portal Gateway requires a browser login **on the same
machine**, times out after ~6 minutes idle, needs a `/tickle` roughly every minute, and hard-resets
every 24 hours. **The backup broker therefore cannot authenticate itself at the moment it is
needed on an unattended systemd-driven VM.** Decision:

- The backup broker is **not** an automated failover path and is **excluded from every RTO claim**.
- **`RTO-operational = 4 h` is unchanged**, because v0.1 already derived it from VM rebuild plus
  WAL replay plus human reconciliation — it never depended on the backup broker.
- **`RTO-safe = 30 min` is unchanged**, because the panic script acts against the **primary**
  broker's API, not the backup.
- Using the backup requires a **human browser login before it can accept an order**. That
  intervention is now stated in the ADR rather than assumed away.
- The backup remains available as a **manual recovery path for new entries only** — never for
  taking over existing positions, which v0.1 already established is impossible on any relevant
  timescale.

**AD-4 — Broker hierarchy fixed in three tiers (amendment A-4).**
P0.2 F-5 showed Upstox issues an `extended_token` for read-only endpoints that survives the daily
expiry, while Zerodha's `access_token` expires at 06:00 IST for **everything** `[V]`. That is an
operational convenience, and **convenience does not promote a broker.** `[CONST-10]` names Zerodha
and it stands. Decision:

| Tier | Broker | Role | Authentication reality |
|---|---|---|---|
| **Primary** | **Zerodha Kite** | India execution and data, per `[CONST-10]` | Daily human login before 06:00 IST expiry; static IP mandatory for order placement from 2026-04-01 `[V]` |
| **Automated backup / monitoring candidate** | **Upstox** | Read-only monitoring and order-book reconciliation where supported, via `extended_token` | `extended_token` survives the daily expiry for read-only endpoints; the **order path still needs daily re-auth** `[V]` |
| **Manual-only emergency backup** | **IBKR** | US new entries only, after a human login | Browser login on the gateway machine; ~6 min idle timeout; 24 h hard reset (AD-3) |

> Upstox is **not** promoted to primary. It is evaluated as an automated *monitoring* path at the
> ADR-11 activation gate, and adopting it for the order path would need a `[CONST-10]` amendment.

**AD-5 — OpenAI becomes the preferred LLM, conditionally (amendment A-10).**
P0.2 §4.2 Capability E scored OpenAI above DeepSeek on **published data-governance terms alone**:
OpenAI publishes that API data is not used for training absent opt-in, and that abuse-monitoring
logs are retained **30 days** `[V]`. DeepSeek's terms host timed out and **no retention or
training-use terms could be retrieved** — carried as **M-7 `[U]`**.

| | Before (v0.1 / `[CONST]`) | After (v0.2) |
|---|---|---|
| Primary | DeepSeek | **OpenAI `gpt-5.6-luna`** |
| Fallback | `gpt-4o-mini` — **not in OpenAI's catalogue** `[V]` F-8 | **DeepSeek `deepseek-v4-flash`** |

**This is a Constitutional amendment, and it is recorded as one rather than hidden inside an ADR.**
`[CONST]` FIXED STACK reads "DeepSeek (primary LLM) + GPT-4o-mini (fallback)". Both halves change:
the ordering reverses, and the named fallback does not exist. The FIXED STACK line must be amended
to **"OpenAI `gpt-5.6-luna` (primary LLM) + DeepSeek `deepseek-v4-flash` (fallback)"**. This also
resolves amendment **A-1**.

**The decision is CONDITIONAL and M-7 is NOT closed.** The entire margin is the one criterion C5
(data governance), and it rests on an **absence of retrievable evidence** about DeepSeek, not on
evidence against it. If M-7 resolves and DeepSeek's terms are comparable, the two providers
re-score and this decision is re-taken — it does not automatically stand. Recorded as
`llm.primary_conditional_on = "M-7"`.

**Two consequences that must not be lost:**
1. **The live gate path uses the Standard tier, not Batch.** P0.2 §3.12 observed Batch is 50% of
   Standard and that "the 22:30 UTC pipeline has no latency pressure". That is **wrong**: P0.3 §6.1
   gives the pipeline an 18-minute budget and the `TIER3_LLM` stage a 600-second deadline. Batch
   turnaround is not documented on any page P0.2 retrieved, so Batch may **not** be assumed for the
   live path. Carried as new open item **M-10**.
2. **The off-peak pricing rule is now provider-conditional.** DeepSeek prices peak/off-peak by
   time of day `[V]`; OpenAI does not. P0.3 RULE-B8 is amended accordingly rather than deleted,
   because DeepSeek remains the fallback and still has the time-of-day exposure.

### 0.5.2 Amendment disposition — all twenty

| # | Source | Subject | Disposition in v0.2 |
|---|---|---|---|
| **A-1** | P0.2 | `gpt-4o-mini` absent from OpenAI's catalogue | **APPLIED** — resolved by AD-5; fallback is now `deepseek-v4-flash`, primary `gpt-5.6-luna` |
| **A-2** | P0.2 | DeepSeek vendor unchanged; pin model id in config | **APPLIED** — model ids live in `config.llm.*`, never in the Constitution |
| **A-3** | P0.2 | Polygon.io is now Massive | **APPLIED (cosmetic)** — §9 Q3 renamed; config records brand host `massive.com` and API host `api.polygon.io` |
| **A-4** | P0.2 | Upstox vs Zerodha for India | **APPLIED — AD-4.** Zerodha primary, Upstox automated backup/monitoring, IBKR manual-only |
| **A-5** | P0.2 | Chain A named a tier, not a vendor | **NO CHANGE NEEDED** — confirmed; §4 of P0.2 fills the tier |
| **A-6** | P0.2 | A14 cost band low | **APPLIED — AD-1** |
| **A-7** | P0.2 | EDGAR dissemination lag and index mutability | **APPLIED (additive)** — ADR-04 adopts rules N1 and N2 |
| **A-8** | P0.2 | Macro data revisions | **APPLIED (additive)** — ADR-04 adopts rule N3 (ALFRED decision-date vintage) |
| **A-9** | P0.2 | Backup broker unauthenticated when needed | **APPLIED — AD-3** |
| **A-10** | P0.2 | LLM data-governance scoring | **APPLIED — AD-5**, conditional on M-7 |
| **A-11** | P0.2 | Tick size / lot size resolved | **APPLIED (additive)** — §6 updated; tick size is a date-versioned instrument attribute |
| **A-12** | P0.2 | Paper stage proves plumbing, not edge | **APPLIED (additive)** — §0.4 and ADR-08 Stage 2 adopt rule N11 |
| **A-13** | P0.3 | 34 windows do not fit 10 years | **APPLIED — AD-2** |
| **A-14** | P0.3 | `[CONST-6]` DENY on the exit path | **NOT APPLIED — REMAINS OPEN.** Not among the five decisions taken; carried to Stage 1 as a gating item for P2.9 |
| **A-15** | P0.3 | A-6's band still excludes VM and backup | **APPLIED — AD-1** |
| **A-16** | P0.3 | P0.3 prompt asks for an open-burst analysis ADR-13 forecloses | **APPLIED (cosmetic)** — prompt-pack defect, recorded; no spec change |
| **A-17** | P0.3 | Gate-width acceptance criterion unsatisfiable on cost | **APPLIED (cosmetic)** — `llm.gate_width` stays 15 on ADR-13 Chain G's authority |
| **A-18** | P0.3 | A-1 still pending | **APPLIED** — closed by AD-5 |
| **A-19** | P0.3 | Chain B's 92 B/row assumes `double precision` | **APPLIED (additive)** — Chain B states the premise; P1.2 chooses explicitly |
| **A-20** | P0.3 | Chain B omits bitemporality | **APPLIED (additive)** — Chain B carries the restatement factor |

**Nineteen applied, one deliberately not.** A-14 is an unresolved `[CONST-1]` / `[CONST-6]`
question and is carried forward, not silently decided.

---

## 1. ONE PAGE — Decisions that constrain everything else

> If a downstream phase reads only one page of this document, it is this one.
> Every line is binding. The ADR number is where to argue, not the phase you are in.

| # | Constraint | Binding value | Why everything else bends around it |
|---|---|---|---|
| 1 | **Holding period** (ADR-13) | Swing. Median **15 trading days**, band 3–40, min hold 3 sessions, time-stop 40, hard max **120 trading days** | Sets data granularity (daily, not tick), storage class (<60 GB, not TB), the cost model, the tax regime (always US short-term), the slippage budget, and the minimum edge the strategy must clear |
| 2 | **Signal granularity** (ADR-13) | **Daily bars** for all signals. 5-minute bars only for instruments currently held | Removes the need for a consolidated tape, removes the market-open ingest burst, drops market-data cost from institutional to retail tier |
| 3 | **Decision cadence** (ADR-14) | **Once per trading session.** Signals computed after close; orders placed 09:45–10:15 ET | Makes ingest a nightly batch, not a stream. Nothing downstream may assume an intraday entry path |
| 4 | **Universe** (ADR-14) | US primary-listed common stock, hard cap **1,500**, weekly reconstitution with 1,300 / 1,700 hysteresis band | Fixes ingest throughput, storage and the scanner's working set for all of Stage 2 |
| 5 | **Portfolio shape** (ADR-14) | Target **20 positions**, target weight **4.0%**, hard cap **5.0%**, ≥20% cash buffer | 20 × 5% = 100% leaves no headroom and no settled cash; the 4% target is what makes the 5% cap survivable |
| 6 | **Market sequencing** (ADR-11) | **Dual-market by contract, US-first by capital.** India adapter built, tested, unfunded | Every spec carries two calendars, two currencies, two brokers and an FX layer from P1.1 — but only one is funded |
| 7 | **Direction & account** (ADR-12) | **Long-only, cash account, no margin, no borrow, no leverage** | Makes gross ≡ net ≤ 1.0× binding; makes settled funds the real cash constraint; makes the design structurally portable to India's cash segment |
| 8 | **Instruments** (ADR-05) | Single-name cash equities only. ETFs read-only in v1. **Futures and options: never in this program** | Deny-by-default `InstrumentType` allowlist enforced inside the risk engine |
| 9 | **Base currency & NAV** (ADR-15) | Base **USD**. Two segregated pools, **no system-initiated FX conversion, ever**. Limits enforced per-pool **and** consolidated; stricter binds | Without per-pool enforcement a 10% loss in a small India pool reads as ~1% consolidated and never trips the kill switch |
| 10 | **LLM in the backtest** (ADR-13 Chain G) | The walk-forward-validated strategy is the **deterministic Tier-1/Tier-2 path only**. The LLM tier is validated forward, in paper trading | An LLM's training data contains the backtest's future. Optimising against it is look-ahead bias no amount of walk-forward discipline removes |
| 11 | **LLM data boundary** (`[DEFAULT-7]`) | The LLM never receives NAV, cash, positions, P&L or limits. Candidate-level sanitised facts only | Caps the blast radius of a successful prompt injection to one candidate's thesis |
| 12 | **Kill switch in backtests** (§0.3 C-3) | Every backtest simulates the kill switch. Accept only if DD ≤ 10% **and** ≤ 1 trip per 10-year run | A strategy validated at 15% DD cannot exist under a 10% kill switch |
| 13 | **Promotion evidence** (ADR-08) | Promotion is proven on **walk-forward OOS (≥34 windows at 3-month rolls, ≥1,000 trades)** (AD-2). Live shadow is a **harm-detection** gate only, never proof of improvement | 250 live sessions can only detect a ~12.5%/yr improvement. Asking live shadow to prove benefit is statistically impossible at retail sample sizes |
| 14 | **Risk override is absolute** (ADR-09) | There is **no human-approval path to override a single risk DENY**. Every other privileged action has one | It is the one exception that would hollow out `[CONST-1]` |
| 15 | **Recovery is fail-closed** (ADR-10) | After any restart the kill switch is restored **tripped**. Drawdown counters restore from the audit trail, never recompute from scratch | Recomputing from scratch resets the drawdown counter and the kill switch forgets why it fired |
| 16 | **Storage reality** (ADR-14 Chain B) | The **audit trail (~1 GB/yr compressed), not market data (~35 MB/yr), is the dominant storage line** | Sizing the VM off market data underestimates the disk by an order of magnitude |
| 17 | **Minimum edge** (ADR-13 Chain F) | Expected 15-day alpha must be **≥ 2× expected round-trip cost** (≥50 bps US, ≥180 bps India) before a BUY is emitted | At 15-day holds, round-trip costs run ~4.2%/yr of the traded book. The edge threshold is not optional |
| 18 | **Never a retrain trigger** (ADR-07) | A losing trade, a losing week or a drawdown **never** triggers a model change | `[CONST-8]`. The five legitimate triggers in ADR-07 are the complete list |

**The single most load-bearing line above is #1.** ADR-13 is the decision the other fourteen are
downstream of. It is argued at length in §3.13.

---

## 2. ADR index

| ADR | Question | Decision in one line | Reversible? |
|---|---|---|---|
| [ADR-01](#adr-01--frontend) | Frontend: full web UI vs FastAPI + Grafana | Grafana + FastAPI + Telegram. No custom frontend before live capital | Yes |
| [ADR-02](#adr-02--orchestration) | Orchestration: cron / Airflow / Temporal / asyncio | Host systemd timers → `docker compose run`, plus one long-lived monitor unit | Yes |
| [ADR-03](#adr-03--kubernetes) | Kubernetes: never / at what trigger | Not before three named metrics hold simultaneously | Yes |
| [ADR-04](#adr-04--alternative-data) | Alternative data: which sources | EDGAR + FRED + one news API + broker corporate actions. Social media excluded | Yes |
| [ADR-05](#adr-05--multi-asset-scope) | Multi-asset: ETFs / futures / options | Equities only; ETFs read-only in v1, tradeable in v2; futures and options never | Partly |
| [ADR-06](#adr-06--vector-database) | Vector DB: kill or justify | Killed. pgvector inside existing Postgres is the only escape hatch | Yes |
| [ADR-07](#adr-07--model-retraining-cadence) | Retraining cadence and triggers | Quarterly expanding-window + 5 enumerated out-of-cycle triggers | Yes |
| [ADR-08](#adr-08--championchallenger-protocol) | Champion/challenger protocol | Promotion proven on walk-forward OOS; live shadow detects harm only | Yes |
| [ADR-09](#adr-09--human-in-the-loop) | Human-in-the-loop actions and SLA | 12 enumerated actions; risk DENY is never overridable | Partly |
| [ADR-10](#adr-10--disaster-recovery) | DR: RPO, RTO, "recovered" | RPO 0 for state, RTO-safe 30 min / RTO-operational 4 h; 5-part recovery definition | Yes |
| [ADR-11](#adr-11--single-market-first-vs-dual-market) | Single-market-first vs dual-market | Dual-market by contract, US-first by capital | Partly |
| [ADR-12](#adr-12--long-only-vs-longshort) | Long-only vs long/short in v1 | Long-only, cash account, no margin, through v2 | Partly |
| [ADR-13](#adr-13--holding-period) | **Holding period** | **Swing: median 15 trading days, band 3–40, hard max 120** | **No — treat as irreversible** |
| [ADR-14](#adr-14--universe-size-and-rebalance-cadence) | Universe size and rebalance cadence | 1,500 US names, weekly reconstitution, once-per-session decisions | Partly |
| [ADR-15](#adr-15--base-currency-fx-and-dual-market-nav) | Base currency, FX, dual-market NAV | USD base, segregated pools, no system FX conversion, dual limit enforcement | Partly |

---

## 3. Architecture Decision Records

Every ADR below carries: Title, Status, Context, Options considered (≥3, each costed), Decision,
Consequences, What would make us revisit, Decision owner, Date — as required by the P0.1 prompt.

Cost columns use these categories where a verified price does not exist, per Block A's
prohibition on invented figures:

| Category | Meaning |
|---|---|
| **Dev** | one-time engineering effort, in developer-weeks for one engineer |
| **Run** | recurring monthly cash cost, USD |
| **Ops** | recurring human attention, in hours/month |
| **Cx** | permanent complexity added to every downstream spec: LOW / MED / HIGH |

---

### ADR-01 — Frontend

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture) · **Date:** 2026-08-23

**Context.** `[RS §10]` and `[RS §20 Q1]` leave the UI undecided: "FastAPI + Grafana may suffice
initially". The system has exactly one human operator `[DEFAULT-3]`. The operator needs three
distinct things, and conflating them is the usual mistake: (a) *observation* — is the system
healthy, what did it do, why; (b) *control* — a small number of privileged actions (ADR-09);
(c) *alerting* — being told, out of band, when something is wrong. `[CONST-7]` additionally
requires that the manual kill switch be independent of the AI path, which means it must not
depend on the same UI stack the rest of the system uses.

**Options considered.**

| # | Option | Dev | Run | Ops | Cx | Notes |
|---|---|---|---|---|---|---|
| A | Grafana (observe) + FastAPI OpenAPI/CLI (control) + Telegram (alert + approve) | 0.5 wk | $0 (self-hosted) | ~1 h/mo | LOW | Grafana already required by `[CONST]` stack for Prometheus |
| B | A + a server-rendered ops console (FastAPI + Jinja2 + HTMX) | 3–4 wk | $0 | ~2 h/mo | MED | No JS build; adds session auth, CSRF, and a template layer to maintain |
| C | React/Next SPA with a REST/WS backend | 8–12 wk | $0–20 | ~4 h/mo | HIGH | Adds a Node toolchain, a bundler, SPA auth (token storage, refresh, XSS surface), and a second deploy artifact |
| D | Buy a hosted dashboard product | 0.5 wk | $50–300 | ~1 h/mo | MED | Exports position and P&L data to a third party — a data-egress and ToS problem for a trading book |

**Decision.** **Option A.** No custom frontend is built before live capital.
- **Observation:** Grafana, self-hosted on the same VM, reading Prometheus and Postgres.
- **Control:** a `trading-agent` CLI on the VM (the primary path) plus a small authenticated
  FastAPI control surface for the same verbs. Both write an `AuditEvent` before acting.
- **Alerting and approval:** Telegram bot restricted to an allowlisted `chat_id`, with TOTP
  required for any ADR-09 action.
- **Kill switch (manual):** three independently sufficient channels, none of which may depend on
  another — (1) the CLI on the VM, (2) a signed HTTP endpoint served by a *separate* minimal
  process with its own port and no dependency on the pipeline or the database, (3) a Telegram
  command. Requirement (2) exists because if the main app is the thing that is broken, the CLI
  and the app-hosted endpoint may both be unavailable.

**Consequences.**
- No JavaScript build, no bundler, no `node_modules` in the repository; no SPA auth surface,
  no CORS policy, no CSRF tokens to get wrong.
- Grafana becomes load-bearing for incident response, so it is in scope for ADR-10's DR plan and
  must be restorable within RTO-operational. Its dashboards are provisioned as code
  (JSON in `ops/grafana/`), never hand-edited in the UI, or they are lost on restore.
- The human-approval UX is a Telegram inline keyboard. That bounds ADR-09's approval payloads to
  what fits legibly in a chat message, which is a useful forcing function: an approval a human
  cannot read in a message is an approval a human cannot meaningfully give.
- Multi-operator workflows are not supported. Acceptable at team size 1; see revisit.

**What would make us revisit.**
1. Team size ≥ 2, so approvals need per-user identity and an approval queue rather than one chat.
2. A broker or regulator requires a screen-recorded or in-product approval trail.
3. An ADR-09 approval payload stops fitting a chat message (e.g. approving a 40-line config diff).
4. Grafana alerting cannot express a rule the monitor needs, forcing alert logic back into the app.

---

### ADR-02 — Orchestration

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture) · **Date:** 2026-08-23

**Context.** `[RS §20 Q2]` asks Airflow/Temporal vs cron + Python. `[CONST]` FIXED STACK already
rules: "no Airflow, no orchestration framework", and "Docker on a single VM". Options C and D
below are therefore costed for the record and rejected on constitutional grounds, not
re-litigated. The real design question is what *replaces* an orchestrator: ADR-14 sets a
once-per-session cadence, so the workload is a handful of scheduled batch jobs plus one
long-lived intraday monitor — not a DAG.

**Options considered.**

| # | Option | Dev | Run | Ops | Cx | Notes |
|---|---|---|---|---|---|---|
| A | Plain `cron` → `docker compose run` | 0.2 wk | $0 | ~2 h/mo | LOW | No restart policy, no failure hook, no log capture, poor DST behaviour, no dependency ordering |
| B | Host **systemd timers** → `docker compose run --rm`, plus `docker compose up -d monitor` with `restart: unless-stopped` | 0.5 wk | $0 | ~1 h/mo | LOW | Gets `OnFailure=`, journald capture, `Persistent=true` catch-up after downtime, randomised delay, and explicit ordering |
| C | In-process asyncio/APScheduler inside the FastAPI app | 0.5 wk | $0 | ~1 h/mo | MED | A crash in one job takes down the API and the scheduler together; no process isolation; memory from a heavy backtest leaks into the serving process |
| D | Airflow | 3–4 wk | $30–80 (extra RAM) | ~4 h/mo | HIGH | Scheduler + webserver + metadata DB + executor on a single VM; **excluded by `[CONST]`** |
| E | Temporal | 4–6 wk | $40–120 | ~4 h/mo | HIGH | Durable execution is genuinely nice for order state, but a server + worker + its own DB; **excluded by `[CONST]`** |

**Decision.** **Option B.** Host-level systemd timers invoke containerised entrypoints; the
intraday monitor is a long-lived container. Concretely:

| Unit | Trigger | Job |
|---|---|---|
| `agent-ingest-us.timer` | 21:45 UTC on US session days (post-close + settle window) | EOD bar, corporate-action and fundamentals ingest |
| `agent-pipeline-us.timer` | 22:30 UTC on US session days | Scan → quant → gate → LLM → decide → risk → order list |
| `agent-orders-us.timer` | 13:45 UTC (09:45 ET) on US session days | Place the order list into the 09:45–10:15 ET window |
| `agent-monitor.service` | always on, `restart: unless-stopped` | Held-position monitoring, stops, exit hierarchy |
| `agent-reconcile.timer` | 21:15 UTC and on every start | Broker reconciliation (ADR-10) |
| `agent-reconstitute.timer` | Sat 06:00 UTC | Weekly universe reconstitution (ADR-14) |
| `agent-retrain.timer` | first Sat after quarter end | Scheduled retrain (ADR-07) |

Dependency order is expressed **inside a single Python entrypoint per job**, which fails closed:
if a precondition is unmet the job exits non-zero and `OnFailure=agent-alert@%n.service` raises
a CRITICAL alert. There is no DAG engine and no implicit retry.

**Idempotency is the load-bearing part.** Every job takes a `(job_name, market, trading_date)`
key and writes a `job_run` row with a `UNIQUE` constraint on that triple. A double-fire — from a
`Persistent=true` catch-up, a manual re-run, or an operator retry — hits the constraint and
exits 0 without repeating work. Without this, a timer catch-up after downtime would re-place an
order list. Order placement additionally carries a broker idempotency key derived from the same
triple plus the instrument (`[VERIFY-P0.2]` for per-broker key charset and length limits).

**Consequences.**
- Timezone hazard closed explicitly: all timers are specified in **UTC**, never in `America/New_York`,
  so a DST transition cannot move a job. The 09:45 ET order window is 13:45 UTC in EDT and
  14:45 UTC in EST, which means **two timer definitions selected by a calendar lookup**, not one
  local-time timer. The session calendar (P1.1) is the authority on which applies; a job that
  cannot resolve the session calendar exits non-zero rather than guessing.
- Half-days (US early close 13:00 ET) do not affect the 09:45–10:15 order window but do move the
  ingest and pipeline timers earlier; the calendar drives this, and the timers fire on a wide
  window with the entrypoint blocking until the session is confirmed closed.
- Backfill is an explicit CLI flag (`--trading-date`), not a framework "clear and rerun".
- No DAG visualisation. Job status is a Postgres table and a Grafana panel.

**What would make us revisit.**
1. Scheduled jobs exceed ~15, or cross-job dependencies stop being expressible as a linear
   entrypoint.
2. India activation (ADR-11) creates genuinely concurrent cross-market fan-out with shared
   downstream steps.
3. Order-state durability proves too hard to hand-roll — the honest failure mode that would make
   Temporal (Option E) worth a constitutional amendment.

---

### ADR-03 — Kubernetes

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture) · **Date:** 2026-08-23

**Context.** `[RS §20 Q3]` asks *when* to migrate, presupposing that we eventually will.
`[CONST]` says "Docker on a single VM. No Kubernetes." A "when" question with no trigger metric
is the exact kind of thing that gets re-opened every phase, so this ADR names the metrics.

**Options considered.**

| # | Option | Dev | Run | Ops | Cx | Notes |
|---|---|---|---|---|---|---|
| A | Single VM + Docker Compose, cold-standby VM for DR | 0 wk | $40–120 | ~2 h/mo | LOW | Current constitutional stack |
| B | Two VMs (US pool / India pool), Compose on each | 0.5 wk | $80–240 | ~3 h/mo | LOW-MED | The realistic scale step: isolate by market, not by pod |
| C | Managed Kubernetes (EKS/GKE/AKS) | 4–6 wk | $150–400 + control plane | ~6 h/mo | HIGH | Adds manifests, ingress, secrets integration, a container registry, and a second failure domain |
| D | Self-managed k3s on the same VM | 1–2 wk | $40–120 | ~4 h/mo | MED-HIGH | All the abstraction cost, none of the availability benefit — worst of both |

**Decision.** **Option A now. Option B is the designated next step. Kubernetes is not adopted
until all three of the following hold simultaneously**, verified from Prometheus data and
recorded in an ADR amendment:

1. Live capital under management ≥ **USD 250,000** (below this, the operational risk of a
   platform migration exceeds the risk it mitigates); **and**
2. ≥ **3 concurrently live strategy versions** requiring independent resource isolation
   (champion + ≥2 challengers running live shadow under ADR-08); **and**
3. A **documented single-VM saturation event**: sustained CPU > 70% for 3 consecutive sessions
   during the 13:45–14:15 UTC order window, **or** Postgres write IOPS > 70% of provisioned for
   3 consecutive sessions, **or** an ADR-10 restore that demonstrably cannot meet RTO-operational
   on a single VM.

Any one or two of these is explicitly *not* sufficient. Cost/capacity headroom is quantified in
P0.3; ADR-14 Chain B already indicates the workload is nowhere near these thresholds.

**Consequences.**
- No k8s manifests, no Helm, no service mesh, no operator, no `kubectl` in any runbook.
- Horizontal scale, when needed, is "run India on a second VM" (Option B), not "add replicas".
  This is only possible because ADR-15 segregates the pools with no cross-margining — the two
  markets share no mutable state except the consolidated NAV snapshot, which is a read.
- High availability is **not** provided. The system is deliberately allowed to be down: it trades
  once per session (ADR-14), and ADR-10's RTO-safe path (cancel/liquidate from a laptop) covers
  the case where being down is dangerous. HA would be a large cost to protect a once-a-day batch.
- DR is VM image + Postgres PITR from WAL, not cluster failover.

**What would make us revisit.** The three trigger metrics above, jointly. Additionally: if a
broker or regulator mandates infrastructure controls only expressible in an orchestrated
environment, or if `[CONST-9]`'s SEBI "broker hosting" requirement turns out to dictate a
deployment topology we do not control `[VERIFY-P0.2]`.

---

### ADR-04 — Alternative data

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture) · **Date:** 2026-08-23

**Context.** `[RS §8]` lists SEC EDGAR, insider transactions, social media, FRED and VIX;
`[RS §20 Q4]` leaves the selection open. Two constraints bound the answer hard. First, ADR-13
sets a 15-day horizon: data whose signal decays in minutes has no place, and data that updates
quarterly is already covered by the fundamentals feed. Second, `[CONST-4]` forbids raw external
content reaching the LLM, and `[RS §15]` names data fabrication and prompt injection as live
threats — so every source is also an attack surface that must be sanitised, which is a real
recurring cost, not a checkbox.

**Options considered.**

| # | Option | Dev | Run | Ops | Cx | Notes |
|---|---|---|---|---|---|---|
| A | Minimal: EDGAR + FRED only | 1.5 wk | $0 | ~1 h/mo | LOW | Free, high-quality, but no news → the LLM research agent `[RS §5]` has almost nothing to synthesise |
| B | **Minimal + one commercial news API + broker corporate actions** | 3 wk | $0–450 `[VERIFY-P0.2]` | ~2 h/mo | MED | Covers every input the Tier-3 research agent actually consumes |
| C | B + social sentiment (X / Reddit / StockTwits) | +3 wk | +$100–500 | +4 h/mo | HIGH | Highest injection surface in the entire system; signal at a 15-day horizon is weak and crowded |
| D | B + a paid alt-data panel (card spend, web traffic, satellite) | +4 wk | +$1,000–25,000 | +4 h/mo | HIGH | Priced for institutions; ToS typically forbid the redistribution and retention patterns we need |

**Decision.** **Option B.** v1 ships exactly four non-price sources:

| Source | Content | Cost | Latency | Role |
|---|---|---|---|---|
| SEC EDGAR (submissions + full-text) | 10-K, 10-Q, 8-K, and Forms 3/4/5 insider transactions | free; **10 req/s, declared User-Agent required** `[V]` | **dissemination cutoff 17:30 ET, 22:00 ET for Forms 3/4/5** `[V]`; propagation latency after acceptance still unpublished (M-8) | Fundamental confirmation, event flags, insider signal |
| FRED | rates, yields, VIX, macro series | free; **numeric rate limit unpublished — adaptive backoff, never a fixed budget (rule N8)** `[U]` | daily/monthly, **read at decision-date vintage via ALFRED (rule N3, A-8)** | Regime detection input `[RS §5]` |
| One commercial news API | headline + body + timestamp + symbol tagging | `[VERIFY-P0.2]`, provider chosen in P0.2 | seconds–minutes | Sole input to the Tier-3 research agent, post-sanitisation |
| Broker / exchange corporate-action feed | splits, dividends, symbol changes, delistings | bundled | daily | Correctness, not alpha — see ADR-14 Chain B |

**Explicitly excluded from v1, v2 and v3, each with its reason** (recorded so no later phase
re-proposes them as novel ideas):

| Excluded | Reason |
|---|---|
| Social media sentiment | Largest prompt-injection and data-fabrication surface in the system `[RS §15]`, adversarially manipulable by design, and weak at a 15-day horizon. Directly at odds with `[CONST-4]`'s spirit even after sanitisation |
| Satellite / geolocation / card-panel | Institutional pricing (Option D) against a portfolio measured in thousands of dollars `[DEFAULT-1]` |
| Web-scraped pricing or product data | ToS risk, silent breakage, no provenance for the audit trail `[CONST-5]` |
| Options flow / dark-pool prints | Would imply an options data subscription for a program that never trades options (ADR-05) |
| Analyst estimates and ratings | Deferred, not banned: high look-ahead-bias risk (point-in-time consensus is expensive and easy to get wrong). Requires a point-in-time vendor to be admissible; see revisit |

**Insider transactions (Forms 3/4/5) are included** and are the one genuine alt-data signal in
v1: free, filed, timestamped, and directly relevant at a multi-week horizon.

**Consequences.**
- The Tier-3 research agent's entire world is: our own fundamentals, our own price history,
  EDGAR text, and sanitised news. That is a small, enumerable, sanitisable input set — which is
  what makes P4.1 (sanitisation) tractable at all.
- **v0.3 (2026-08-26) — the news archive is NOT point-in-time, verified, and ADR-04 stands.**
  Both news vendors expose a post-publication revision timestamp (Massive/Benzinga
  `last_updated` “when the news article was last updated in the system”; Alpaca `updated_at`)
  and **neither offers any version, revision or as-of-content parameter**, so a historical
  query returns the article **as currently stored, not as originally published** `[V]`.
  **The source selection does not change** — every candidate vendor has the same property, so
  this is a characteristic of financial news, not a defect of Benzinga. What changes is that
  **rule N4 (news forward-validated only, excluded from walk-forward optimisation) moves from
  precautionary to evidence-based**, and **new rule N16** requires our ingest to snapshot
  headline and body at first receipt and write a new revision row rather than overwriting —
  our store becomes the point-in-time record because the vendor's is not. Corollary:
  **historical news backfill is structurally unsound for any content-derived feature.**
- **v0.2 (A-7, A-8) — three binding rules adopted additively, changing no decision.**
  **N1:** EDGAR-derived features are lagged to the **dissemination date**, never the filing
  date. **N2:** EDGAR index retrievals are **snapshotted immutably** and never re-derived after
  a Saturday rebuild. **N3:** macro features are read at **decision-date vintage** (ALFRED
  `series/vintagedates`), because FRED series are revised and a naive read imports the
  revision into a backtest as if it had been knowable.
- Every source needs point-in-time correctness for backtesting. EDGAR gives a true filing
  timestamp, so no look-ahead. **News does not**: most news APIs do not guarantee that their
  historical archive matches what was visible at the time. Binding instruction to P5.1: news
  features may only enter a backtest with an explicit ingestion-timestamp lag of at least one
  full session, and any news feature whose backtest contribution is material must be flagged as
  unverifiable and validated forward in paper trading only. **v0.2 (A-12):** paper trading
  proves **plumbing only** — Alpaca paper fills against IEX data, injects random 10% partial
  fills, simulates no dividends and no fees `[V]` F-13. **No slippage, fill-quality, fee or
  edge conclusion may cite paper data** (rule N11); ADR-13 Chain F's ≥2× cost threshold is
  validated on **live** fills only.
- No data source in v1 costs more than a rounding error against the $200–500 LLM ceiling except
  the news API, making the news provider the single largest recurring data line item.

**What would make us revisit.**
1. Walk-forward OOS Sharpe below 0.7 for 3 consecutive windows with the current feature set —
   evidence the feature set, not the model, is exhausted.
2. A candidate source demonstrates ≥ 0.15 incremental OOS Sharpe in a properly lagged,
   point-in-time backtest across ≥ 20 walk-forward windows (≥ 34 at 3-month rolls, AD-2).
3. A point-in-time analyst-estimate vendor becomes affordable, which would move estimates from
   "deferred" to a costed proposal.
4. Capital ≥ USD 250,000, at which point Option D's pricing stops being absurd.

---

### ADR-05 — Multi-asset scope

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Risk Owner) · **Date:** 2026-08-23

**Context.** `[RS §20 Q5]` asks when ETFs, futures and options enter scope. `[CONST-8]` bans
autonomous leverage; `[RS §23]` bans "unrestricted options". "When" questions without a gate get
re-opened, and each instrument class changes the domain model (P1.1), the risk engine (P2.9) and
the broker adapter (P3.1) in ways that are expensive to retrofit — so the *allowlist mechanism*
must exist from day one even though the list has one entry.

**Options considered.**

| # | Option | Dev | Run | Cx | Notes |
|---|---|---|---|---|---|
| A | Equities only, forever, no allowlist mechanism | 0 wk | $0 | LOW | Cheapest now; every later addition is a schema migration and a risk-engine rewrite |
| B | **Equities only in v1, with a deny-by-default `InstrumentType` allowlist from day one; ETFs read-only in v1, tradeable in v2** | 0.5 wk | $0 | LOW-MED | The mechanism is ~50 lines; adding ETFs later is a config change plus a sizing rule |
| C | Equities + ETFs tradeable in v1 | +1 wk | $0 | MED | ETFs need their own liquidity, tracking-error and creation/redemption handling, and sector classification is ambiguous — extra work before the equity path is proven |
| D | Add futures and/or options | +8–12 wk | data subs | HIGH | Margin, SPAN, expiry, roll, assignment, Greeks, and a different broker set. Leverage is intrinsic |

**Decision.** **Option B**, with an explicit, dated ladder:

| Instrument class | v1 (now) | v2 (gate below) | v3 | Ever? |
|---|---|---|---|---|
| Single-name common stock (US primary listing) | **Tradeable** | Tradeable | Tradeable | — |
| ETFs (broad-market and sector) | **Read-only** — regime input and sector benchmark `[RS §5]`, never held | **Tradeable** as ballast and as the only permitted hedge instrument | Tradeable | — |
| Leveraged / inverse-leveraged ETFs (≥2×) | Banned | Banned | Banned | **Never** — path-dependent decay plus embedded leverage, contra `[CONST-8]` |
| Unleveraged inverse ETFs | Banned | **Permitted hedge only**, ≤10% NAV, never as an alpha position | Same | — |
| ADRs, ETNs, closed-end funds, SPACs, units, warrants, rights, preferred, OTC | Banned | Banned | Reviewable | — |
| Futures | Banned | Banned | Banned | **Never in this program** |
| Options | Banned | Banned | Banned | **Never in this program** |

**v2 gate for ETF tradeability** — all must hold: (a) ≥6 months paper trading with positive
Sharpe `[RS §12 stage 3]`; (b) ≥3 months controlled live `[RS §12 stage 6]`; (c) an ETF-specific
sizing and sector-attribution rule written and frozen (an S&P 500 ETF is not "one position in one
sector" for the ≤20% sector limit — it is a basket, and the risk engine must decompose it or
treat it as a sector-neutral exposure); (d) ADR-09 Owner approval.

**Why futures and options are "never" rather than "later".** Futures embed leverage in the
instrument, so holding one is autonomous leverage regardless of position size — `[CONST-8]`.
Options add assignment risk, expiry mechanics, and a payoff that a 2.5×ATR stop cannot bound;
an autonomous system that can be assigned overnight has a risk profile the kill switch cannot
enforce. Both also require a different broker relationship, invalidating the P0.2 selection. If
either is ever wanted, it is a **different program** with its own constitution, not an
extension of this one.

**Consequences.**
- `InstrumentType` is an enum in P1.1 and the risk engine denies by default on it — an unknown or
  newly appearing instrument type is a DENY, not a pass-through. This is the fail-closed
  behaviour `[CONST-6]` requires, applied to instrument identity.
- The universe filters in ADR-14 must *actively exclude* the banned classes rather than rely on
  them not appearing; exclusion is by security-type field plus a name-pattern guard for
  units/warrants/rights `[VERIFY-P0.2]` for the reference-data field names.
- Because ETFs are read-only in v1, sector exposure `[CONST]` ≤20% is computed on single names
  only, which is unambiguous. This gets harder at the v2 gate, which is why (c) above exists.
- No margin agreement is needed with the broker in v1 (see ADR-12), which is also what keeps the
  account a cash account.

**What would make us revisit.** The v2 gate for ETFs, on its stated conditions. For futures and
options: nothing within this program. A constitutional amendment plus a new risk framework would
be required, and it would be a new spec tree.

---

### ADR-06 — Vector database

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture) · **Date:** 2026-08-23

**Context.** `[RS §10]` already says "Vector DB: Not needed"; `[RS §20 Q6]` re-opens it as
"Any real use case?". `[CONST]` FIXED STACK says "no vector DB". This ADR closes it permanently
and names the escape hatch so a future phase does not treat "no vector DB" as "no similarity
search of any kind" and reinvent one badly.

**Options considered.**

| # | Option | Dev | Run | Cx | Notes |
|---|---|---|---|---|---|
| A | **No vector store. Deterministic text handling in Postgres** | 0 wk | $0 | LOW | `tsvector` full-text + `pg_trgm` fuzzy + MinHash/SimHash for near-duplicate news |
| B | `pgvector` extension inside the existing Postgres | 0.5 wk | $0 | LOW-MED | No new service; embeddings still cost an API call each and still need audit provenance |
| C | Dedicated vector service (Qdrant / Weaviate / Milvus) | 2 wk | $20–80 (RAM on the same VM) | MED-HIGH | A second stateful service to back up, restore and version — ADR-10 cost, for a corpus of ~10^5 items |
| D | Managed vector cloud (Pinecone et al.) | 1 wk | $70–300 | MED | Ships our news corpus and its embeddings to a third party; ToS and data-egress problem |

**Decision.** **Option A. The vector database is killed for the lifetime of this program.**

The use case people reach for is news deduplication and "find similar past situations". Both are
solved deterministically and more auditably:

| Need | Deterministic solution | Why it is better here |
|---|---|---|
| Near-duplicate news suppression (the same wire story on 6 outlets) | SimHash / MinHash over normalised token shingles, threshold-tuned, stored as a `bigint` | Exactly reproducible; the same inputs always dedupe identically, which a backtest requires and an approximate-nearest-neighbour index does not guarantee across rebuilds |
| Keyword / entity retrieval over filings | Postgres `tsvector` + GIN index | Auditable: the query that selected a document is a literal string in the audit trail |
| "Similar historical setups" | A feature-space k-NN over our own **numeric** factor vectors, computed in NumPy over ≤1,500 × ≤2,520 rows | The similarity is over the features we actually model, not over prose. Fits in RAM, no index to corrupt |

**The decisive argument is not cost — it is `[CONST-5]`.** A vector store used as agent memory is
an unversioned, non-reproducible influence on a trading decision: retrieval results change when
the index is rebuilt, when embeddings are re-generated with a new model version, or when a
neighbour is inserted. A decision that cannot be reproduced cannot be audited, and `[RS §15]`
names memory poisoning as an active threat class — a semantic memory is the ideal target,
because poisoning it requires no code execution, only a document.

**Escape hatch, named precisely so it is not a loophole.** If a future phase demonstrates a
retrieval need that Option A cannot meet, the *only* permitted implementation is **`pgvector`
inside the existing Postgres instance** (Option B), subject to: every embedding row records
`model_id`, `prompt_version` and `content_hash`; retrieval results are written to the audit trail
as an explicit ID list before they influence anything; the index is rebuildable to bit-identical
results from stored inputs. A separate vector *service* (Options C, D) is never permitted.

**Consequences.**
- No embedding API spend, no embedding-model version drift, no second stateful service in ADR-10's
  backup and restore procedure.
- P4.3 (LLM research agent) must assemble context **deterministically** — a fixed query over
  Postgres by symbol, date range and document type — not by semantic retrieval. This is
  simultaneously the anti-injection posture `[CONST-4]` wants: a bounded, enumerable context.
- News dedup becomes a P2.x/P4.1 implementation task with a concrete algorithm rather than a
  hand-wave.

**What would make us revisit.** A documented requirement for retrieval over > 10^6 unstructured
documents where Option A is measurably insufficient (recall measured against a labelled set), and
where the audit-reproducibility conditions above can be met. Note the corpus at ADR-04's sources
is roughly 200 news items/day plus filings — approximately 10^5 documents over 3 years, two
orders of magnitude below that threshold.

---

### ADR-07 — Model retraining cadence

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture) · **Date:** 2026-08-23

**Context.** `[RS §20 Q7]` asks how often to retrain XGBoost models; `[RS §4]` says "walk-forward
retraining on expanding window"; `[CONST-8]` and `[RS §19 #20]` forbid "trade lost → change
strategy". The failure mode being guarded against is **reactive retraining**: a drawdown creates
pressure to retrain, retraining on the recent window fits the drawdown, and the system quietly
becomes a momentum-chaser. The cadence must therefore be calendar-driven by default, with
out-of-cycle triggers that are *statistical properties of the inputs*, never *P&L outcomes*.

**Options considered.**

| # | Option | Dev | Run | Cx | Notes |
|---|---|---|---|---|---|
| A | Annual retrain | 0.5 wk | ~$0 compute | LOW | Too slow: a full year of universe reconstitution and reporting-standard drift accumulates |
| B | **Quarterly scheduled, expanding window, plus enumerated out-of-cycle triggers** | 1.5 wk | ~$0 | MED | Aligns with the quarterly fundamentals cycle, which is what the features are actually made of |
| C | Monthly retrain | 1.5 wk | ~$0 | MED-HIGH | 12 promotion decisions/year against ADR-08's sample requirements is not achievable; each retrain also multiplies the ADR-08 trial count, inflating the deflated-Sharpe haircut |
| D | Continuous / online learning | 3 wk | ~$0 | HIGH | No stable model version to audit, no reproducible decision, and structurally identical to "trade lost → change strategy". Contra `[CONST-8]` |

Compute cost is near zero for all options: XGBoost on ~1,500 × 2,520 rows with a few hundred
features trains in minutes on the existing VM, so cadence is governed entirely by statistical
validity and audit discipline, not by cost. That is worth stating because it removes the usual
argument for infrequent retraining.

**Decision.** **Option B.**

**Scheduled cadence:** quarterly, on the first Saturday after calendar-quarter end
(`agent-retrain.timer`, ADR-02), on an **expanding** window (all history from the fixed start
date to the cutoff — never a rolling window, which would silently discard the 2008/2020 stress
regimes the model most needs). Every retrain produces an immutable artifact:
`model_id` (UUID), a hash of the training data selection, the training-data cutoff timestamp, the
hyperparameter set, the library versions, and the walk-forward report. No in-place weight updates
ever.

**Out-of-cycle retrain triggers — this is the complete list. Anything not here is not a trigger.**

| # | Trigger | Measurement | Threshold |
|---|---|---|---|
| T1 | Feature drift | Population Stability Index of each top-10 feature, current 21-session window vs. training distribution | PSI > 0.25 on any top-10 feature `CONVENTION/ASSUMPTION` |
| T2 | Prediction-quality drift | Rolling 60-session rank IC (or AUC) of the model's score vs. realised 15-day forward return | Below the lower bound of the training-time bootstrap 95% CI |
| T3 | Universe shock | Fraction of the universe replaced at one weekly reconstitution (ADR-14) | > 15% in a single reconstitution |
| T4 | Input-schema break | A reporting-standard or vendor-schema change invalidates a feature's definition (e.g. a new GAAP/Ind-AS line item, a vendor field retirement) | Any occurrence |
| T5 | Regime under-representation | Time spent in a detected regime `[RS §5]` whose training-set representation is < 60 sessions | Persisting > 21 consecutive sessions |

**Explicitly not triggers, at any magnitude:** a losing trade; a losing day, week, month or
quarter; a drawdown; a kill-switch trip; a single bad prediction; operator intuition. `[CONST-8]`.
The risk engine and kill switch respond to losses. The model does not.

**Every retrain — scheduled or triggered — must pass ADR-08's promotion gate before it can
influence a live order.** A retrained model is a challenger, never automatically the champion.
This is what stops T1–T5 from becoming a backdoor to reactive strategy change: a trigger only
authorises *training a candidate*, never *deploying it*.

**Consequences.**
- At most ~4 scheduled + a small number of triggered candidates per year, which is compatible
  with ADR-08's sample-size requirements and keeps the deflated-Sharpe trial count small enough
  that the multiple-testing haircut does not swamp any real improvement.
- P2.x must record `model_id` on every score it produces, and the audit trail (P1.4) must carry it
  on every decision, or a decision cannot be reproduced after a promotion.
- Model artifacts are stored, versioned and never deleted — they are needed to reproduce
  historical decisions and to run ADR-08's rollback comparison. Storage is negligible (megabytes).
- T2 requires storing the realised 15-day forward return per scored candidate, which only exists
  because ADR-13 fixes the horizon at 15 days. A variable horizon would make this trigger
  ill-defined.

**What would make us revisit.** T1–T5 firing more than ~6 times a year, which would indicate the
feature set is unstable rather than the model being stale (route to ADR-04 revisit instead); or
the arrival of a genuinely non-stationary feature class that needs a different regime.

---

### ADR-08 — Champion/Challenger protocol

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Risk Owner) · **Date:** 2026-08-23

**Context.** `[RS §20 Q8]` asks for the exact protocol: sample size, significance test, promotion
rule. This is where most retail systems fool themselves, so the arithmetic is done explicitly
below rather than asserted.

**The statistical reality, computed.** The standard error of an estimated per-period Sharpe is
approximately `SE(Ŝ_p) ≈ sqrt((1 + Ŝ_p²/2) / n)`. For an annualised Sharpe of 1.0, the daily
Sharpe is `1.0/√252 ≈ 0.063`, so `Ŝ_p²/2 ≈ 0.002 ≈ 0`, giving
`SE(Ŝ_annualised) ≈ √(252/n)`.

| n (sessions) | SE of annualised Sharpe |
|---|---|
| 60 | ≈ 2.05 |
| 250 (≈1 year) | ≈ 1.00 |
| 1,000 (≈4 years) | ≈ 0.50 |
| 2,520 (≈10 years) | ≈ 0.32 |

**One year of live data cannot distinguish a Sharpe of 1.0 from a Sharpe of 0.0 at 95%
confidence.** Any protocol that asks live shadow trading to *prove* a challenger is better is
asking for something the sample size cannot deliver.

Pairing helps, because champion and challenger share most of their positions and nearly all of
their market exposure. If both have daily volatility σ and correlation ρ, the difference series
has volatility `σ_d = σ·√(2(1−ρ))`. At ρ = 0.95, `σ_d = 0.316σ` — a ~3.2× variance reduction,
worth roughly 10× the sample. Even so, for a one-sided test at α = 0.05 with 80% power,
`n ≥ (1.645 + 0.842)² · σ_d² / Δ² = 6.18 · σ_d²/Δ²`. With daily strategy vol σ = 1.0% and
ρ = 0.95 (`σ_d = 0.316%`):

| Detectable improvement Δ (annualised) | Required paired sessions |
|---|---|
| 12.5% / yr | 250 |
| 7.9% / yr (at ρ = 0.98) | 250 |
| 3.0% / yr | ~4,300 (≈17 years) |
| 1.5% / yr | ~17,400 (≈69 years) |

**Conclusion, and it is the decision:** live shadow can detect a catastrophe, not an improvement.
Improvement must be demonstrated where the sample actually exists — in walk-forward
out-of-sample testing across 10 years, which yields ≥34 independent windows **at 3-month rolls**
and thousands of trades `[RS §13]`. **v0.2 (AD-2):** at 6-month rolls 10 years yields only ~16
windows, so the roll length is fixed at **3 months with a 1.5-year initial training window** — the
only configuration that reaches 34 independent windows from the 10 years of history actually
purchased (P0.3 B-F4).

**Options considered.**

| # | Option | Dev | Ops | Cx | Notes |
|---|---|---|---|---|---|
| A | Promote on live-shadow outperformance over N sessions | 1 wk | ~2 h/mo | LOW | Statistically void per the table above; promotes noise |
| B | Promote on backtest improvement alone | 1 wk | ~1 h/mo | LOW | Ignores implementation bugs, data-plumbing differences and live-only failure modes |
| C | **Promote on walk-forward OOS evidence; use live shadow as a harm-detection / non-inferiority gate; require human approval** | 3 wk | ~3 h/mo | MED | Puts each test where its sample size supports it |
| D | Multi-armed bandit / automatic capital allocation between versions | 5 wk | ~2 h/mo | HIGH | Automatic capital shifting on short-run P&L is "trade lost → change strategy" with better branding. Contra `[CONST-8]` |

**Decision.** **Option C.** The protocol, in full:

**Stage 1 — Offline evidence (this is where promotion is earned).**
- Sample: ≥ **34 walk-forward OOS windows at 3-month rolls** (AD-2), ≥ **1,000 closed trades**,
  ≥ **8 years** of history spanning ≥ **2 distinct bear regimes** `[RS §13]`. At ADR-13's ~3,400
  closed trades per decade each window holds ~100 closed trades. **6-month rolls are rejected**:
  they need ~20 years of history, which would cost **+$120/mo** (Massive Advanced) for no gain in
  window independence.
- Test: paired **stationary bootstrap** (Politis–Romano, mean block length 10, 10,000
  resamples) on the per-window OOS metric differences (challenger − champion), one-sided.
  Requirement: the **95% bootstrap lower bound of the mean difference > 0**.
- Multiple-testing control: **Deflated Sharpe Ratio** (Bailey & López de Prado) computed with the
  *actual* number of challengers trialled since the champion was promoted — a counter the system
  maintains and cannot be reset by hand. Requirement: **DSR > 0.95**.
- Robustness: challenger max drawdown ≤ champion max drawdown × 1.10; challenger OOS/IS ratio
  ≥ 0.70 `[RS §13]`; challenger passes the C-3 kill-switch-simulated acceptance (≤ 1 trip per
  10-year run).

**Stage 2 — Live shadow (this is where harm is detected, not benefit proven).**
- Duration: ≥ **60 trading sessions** and ≥ **40 paired decisions**, running against live data,
  logging decisions, placing **no orders**.
- Blocking conditions — any one blocks promotion: the paired bootstrap **upper** bound of the mean
  daily difference < 0 (positive evidence of harm); any risk-limit violation in the shadow log
  that the champion did not also produce; turnover > champion × 1.5; average position count
  outside 15–25 (ADR-14); any dependency on a data field the champion does not consume that is
  not already ingested and monitored; any decision the challenger could not reproduce on replay.
- Note the asymmetry, deliberately: Stage 2 can **veto** but never **promote**.

**Stage 3 — Human approval.** ADR-09 Owner approval, 72-hour SLA, default "stays shadow".

**Concurrency.** Exactly **one** challenger in live shadow at a time; others queue. Every trialled
challenger increments the DSR trial counter whether or not it reaches Stage 2 — this is what
prevents "try 50 models, promote the luckiest".

**Rollback.** On promotion, the ex-champion is retained and continues running in shadow for
**60 sessions**. If the paired bootstrap upper bound of (new champion − ex-champion) daily
difference falls below 0 during that period, the system **automatically reverts** to the
ex-champion and raises a CRITICAL alert. Reverting to a previously validated model on evidence of
harm is not "trade lost → change strategy"; it is undoing a change, which is always permitted.

**Consequences.**
- Promotion is slow by construction: realistically 1–3 promotions per year. That is the intended
  outcome, and P6.6 (learning) must not design around a faster loop.
- The backtest infrastructure (P5.1, P5.2) is the load-bearing validation surface, so its
  correctness matters more than the live dashboard's. Combined with ADR-13 Chain G (the LLM tier
  is not backtestable), this means **the thing that gets promoted is the deterministic path** —
  the LLM tier's contribution is validated separately and cannot be tuned by this loop.
- The system must run two full decision paths simultaneously during shadow, roughly doubling
  pipeline CPU for the shadow period. At ADR-14's volumes this is minutes of extra compute per
  session, well inside ADR-03's headroom.
- A `strategy_version` and `model_id` must be on every decision and order — also required for
  `[CONST-9]`'s SEBI unique-strategy-ID tagging, so this is one mechanism serving two masters.

**What would make us revisit.** Live sample sizes reaching the ranges where Stage 2 could carry
statistical weight (capital and time scale far beyond this program's horizon); or a demonstrated
walk-forward/live divergence showing the offline evidence is systematically optimistic, which
would mean the backtest, not the protocol, needs fixing.

---

### ADR-09 — Human-in-the-loop

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Risk Owner) · **Date:** 2026-08-23

**Context.** `[RS §20 Q9]` asks which actions require human approval and with what SLA. Two
failure modes bound the answer: too many approvals and the human rubber-stamps (approval theatre,
which is worse than no approval because it creates a false audit signal); too few and the system
can quietly change its own risk posture, contra `[CONST-1]` and `[CONST-8]`. There is exactly one
operator `[DEFAULT-3]`, so the approver role split is notional today but the *audit fields* must
exist from day one or retrofitting them invalidates the historical trail.

**Options considered.**

| # | Option | Dev | Ops | Cx | Notes |
|---|---|---|---|---|---|
| A | Fully autonomous; human only for the kill switch | 0.5 wk | ~0.5 h/mo | LOW | The system could raise its own limits, promote its own models and move capital stages unattended |
| B | **Enumerated allowlist of privileged actions requiring approval; everything else automatic** | 2 wk | ~2 h/mo | MED | Approval load is a handful of events per month, so each one gets real attention |
| C | Approve every order before placement | 1 wk | ~20 h/mo | MED | ~2.7 orders/session (ADR-14) × 21 sessions ≈ 57 approvals/month. Guarantees rubber-stamping, and defeats the point of an autonomous agent |
| D | Approve every order above a size threshold | 1.5 wk | ~6 h/mo | MED | Better, but the threshold is arbitrary and the risk engine already enforces the real constraint deterministically |

**Decision.** **Option B.** Two roles exist in the schema from day one — `Operator` and `Owner`
— and are held by the same person today; the distinction becomes operative at team size ≥2. The
list below is **complete**: an action not on it is automatic.

| # | Action | Approver | SLA | If SLA expires |
|---|---|---|---|---|
| 1 | Re-enable trading after **any** kill-switch trip | Owner | none — no auto-expiry, no auto-re-enable | stays halted, indefinitely `[CONST-7]` |
| 2 | Increase **any** risk limit | Owner | 24 h | request denied |
| 3 | Decrease a risk limit | — | — | **automatic**, no approval needed (tightening is always safe) |
| 4 | Promote a challenger to champion (ADR-08 Stage 3) | Owner | 72 h | stays in shadow |
| 5 | Advance to the next capital stage on the 7-stage ladder `[RS §12]` | Owner | none | stays at current stage |
| 6 | First live order in a new market (ADR-11 India activation) | Owner | none | denied |
| 7 | Add or remove an `InstrumentType` from the allowlist (ADR-05) | Owner | 24 h | denied |
| 8 | Add or change a data provider, LLM provider, or LLM model id | Owner | 24 h | denied |
| 9 | Any manual order placed outside the pipeline | Owner | immediate | n/a — always permitted, always dual-logged and reconciled |
| 10 | Deploy any code to the production VM | Owner | none | not deployed |
| 11 | Rotate or replace a broker credential | Owner | 4 h | old credential expires → **fail-closed trading halt** `[CONST-6]` |
| 12 | Amend a `[CONST]` invariant or an ADR in this document | Owner | none | denied |
| — | **Override a single risk-engine DENY** | **No one. There is no approval path.** | — | — |

**Row 12's absence of a path is the most important line in this ADR.** If a human can override
one DENY, then `[CONST-1]` ("the risk engine always overrides every AI output") is decorative: the
AI need only persuade the human. The permitted action is to change the *limit* (row 2, with its
own approval, audit and 24-hour SLA) and let the engine re-evaluate deterministically — which
leaves a durable record of a policy change rather than an invisible one-off exception.

**Approval mechanics.**
- Channel is **out of band from the AI path** — a signed CLI invocation on the VM, or a Telegram
  command from an allowlisted `chat_id` with a TOTP code. The pipeline can request an approval;
  it can never grant, forge or infer one.
- Each approval is an `AuditEvent` recording: approver identity, role, timestamp (UTC),
  the exact diff or payload approved, its content hash, and a **single-use nonce binding the
  approval to one instance of one action**. Blanket, standing, or "approve all future" approvals
  are structurally impossible — a nonce is consumed on use.
- SLA is measured from `approval_requested` to `approval_granted` in the audit trail, and is
  reported in Grafana. An SLA breach is not itself an alert; the *default action on expiry* (last
  column) is the safety mechanism, and every default is the conservative one.
- Requests are re-issued, never queued indefinitely: an expired request must be raised again by
  the system, so a stale approval cannot be granted against changed conditions.

**Consequences.**
- Expected approval load: roughly 1–4 events per month in steady state (a promotion per quarter,
  a provider change occasionally, capital-stage advances a handful of times ever). This is small
  enough that each approval can be read properly — the whole point of Option B over C.
- The Telegram payload constraint from ADR-01 binds here: an approval payload that does not fit
  legibly in a chat message must be summarised with a content hash plus a CLI command to view the
  full diff. Approving a hash you have not read is exactly the rubber-stamping this ADR avoids,
  so row 12 and row 10 payloads must be reviewed via the CLI.
- P1.4 (audit) must model `ApprovalRequest` / `ApprovalGrant` as first-class audited entities with
  the nonce lifecycle, not as log lines.
- Because row 1 has no SLA and no auto-re-enable, an unattended kill-switch trip means the system
  stays flat and halted until a human acts. That is the correct trade for an autonomous system
  trading its owner's own capital `[DEFAULT-3]`.

**What would make us revisit.** Team size ≥ 2 (activating the Operator/Owner split and requiring
an approval queue with per-user identity); a regulator or broker mandating pre-trade human
approval for a class of orders; or evidence from the audit trail that approvals are being granted
in under ~30 seconds, which is measurable proof of rubber-stamping and would mean the list is too
long.

---

### ADR-10 — Disaster recovery

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Risk Owner) · **Date:** 2026-08-23

**Context.** `[RS §20 Q10]` and `[RS §21 #4]` leave RPO/RTO and "what recovered means with open
positions" undefined. This is the question most likely to be answered wrongly by analogy with web
services: for a trading system the dangerous state is not "down", it is **"up, and wrong about
what it owns"**. A system that restarts with a stale position table and a reset drawdown counter
will trade confidently into a position it already holds, with a kill switch that has forgotten
why it fired.

**Options considered.**

| # | Option | Dev | Run | Cx | RPO / RTO | Notes |
|---|---|---|---|---|---|---|
| A | Nightly VM snapshot only | 0.3 wk | $5–15 | LOW | RPO 24 h / RTO 2–6 h | Up to a day of orders and audit trail lost. Unacceptable — the audit trail is the drawdown counter's source of truth |
| B | **Nightly base backup + continuous WAL archiving + weekly image + a standalone panic script** | 1.5 wk | $10–30 | MED | **RPO 0 (state) / RTO-safe 30 min, RTO-operational 4 h** | Postgres PITR; broker is the reconciliation authority |
| C | B + a warm standby VM with streaming replication | +1 wk | +$40–120 | MED-HIGH | RPO 0 / RTO ~15 min | Buys ~3.5 h of RTO for a once-per-session system that is allowed to be down (ADR-03) |
| D | Multi-region active/active | 4+ wk | $200+ | HIGH | RPO 0 / RTO ~0 | Split-brain risk against a single broker account is a *new* failure mode, strictly worse than being down |

**Decision.** **Option B**, with the objectives and definitions below.

**Recovery objectives, stated per data class** (a single RPO number for the whole system would be
a lie — the classes have genuinely different requirements):

| Data class | RPO | Mechanism |
|---|---|---|
| Orders, fills, positions, audit trail, approvals | **0** | `synchronous_commit = on` for these tables; continuous WAL archiving to off-VM object storage |
| Model artifacts, config, universe snapshots | **0** | Version-controlled and/or WAL-covered; immutable once written |
| Market data (bars, fundamentals, news) | **≤ 24 h** | Re-fetchable from the provider by `trading_date`; loss costs an ingest re-run, not information |
| Prometheus metrics | **≤ 24 h** | Observability only; never an input to a trading decision |

**RTO is two-tier**, because "safe" and "operational" are different problems:

- **RTO-safe = 30 minutes.** The ability to cancel every open order and, if required, flatten the
  book. Delivered by a **standalone panic script**: a single file, no dependency on the
  application, the database, Docker, Grafana or the VM, runnable from any laptop, talking
  directly to the broker REST API using a credential held in a sealed offline envelope. It is
  tested monthly against the paper account. This is the single most important artifact in this
  ADR — every other recovery step can take hours, but the ability to stop must not.
- **RTO-operational = 4 hours.** Full pipeline restored on a rebuilt VM from the weekly image plus
  WAL replay to the last committed transaction, reconciled and re-enabled by a human.

**"Recovered", defined precisely for a system with open positions.** All five must hold. Anything
less is not recovered, and the system stays halted:

1. **Order-book reconciliation.** Every open order at the broker is either matched to a known
   local order row, or cancelled. An unrecognised open order at the broker is cancelled, not
   adopted — an order we cannot explain is an order we did not intend `[CONST-6]`.
2. **Position reconciliation.** Every broker position matches a local `position` row with
   lot-level cost basis. Any mismatch marks the position `UNRECONCILED`, and while any position
   is `UNRECONCILED` the risk engine treats it as full-size risk and **denies all new entries**
   across the entire pool.
3. **Counter restoration from the audit trail, never recomputation.** Peak NAV, current drawdown,
   daily-loss and weekly-loss counters are replayed from the append-only audit trail. They are
   **never** recomputed from the current portfolio, because recomputation resets peak NAV to the
   present value and silently un-trips the drawdown condition — the kill switch would forget why
   it fired. This is the specific, concrete failure this clause exists to prevent.
4. **Kill switch restored TRIPPED.** Always, unconditionally, regardless of its state before the
   incident. Re-enabling is ADR-09 row 1 — an explicit human action with no SLA and no
   auto-expiry. Fail-closed on recovery `[CONST-6]`, `[CONST-7]`.
5. **Audit-chain continuity verified.** The hash chain is verified continuous across the outage
   window. A broken or forked chain is a **hard stop**: no trading resumes, and the break is
   investigated as a potential integrity incident `[RS §15]` before anything else.

**The broker is the system of record for positions and cash.** Our database is a derived, richer
view (lots, cost basis, thesis linkage). On any disagreement, the broker wins for quantity and
the discrepancy is escalated — never silently corrected in one direction.

**Backup broker ≠ failover, and it is MANUAL-ONLY (AD-3).** Positions cannot be
transferred between brokers on any operationally relevant timescale. A backup broker `[RS §12]`
is a second, funded, API-tested account usable for **new entries only** while the primary is
down. Positions held at the primary can only be managed at the primary — which means a primary
outage with open positions is managed by the panic script's cancel path and by waiting, not by
switching. Any downstream spec that models the backup broker as hot failover is wrong.

**v0.2 (AD-3) — the backup broker cannot authenticate itself when it is needed.** P0.2 F-12
verified that IBKR, the designated US backup, requires a **browser login on the gateway
machine**, idles out after **~6 minutes**, needs a `/tickle` about **every minute**, and
hard-resets every **24 hours** `[V]`. On an unattended systemd-driven VM (ADR-02) that means:

- The backup broker is **excluded from every RTO claim** and is **not** an automated failover path.
- **`RTO-safe = 30 min` is unchanged** — the panic script acts against the **primary** broker's
  API and never depended on the backup.
- **`RTO-operational = 4 h` is unchanged** — it was always VM rebuild + WAL replay + human
  reconciliation, and never depended on the backup either.
- Reaching the backup requires a **human browser login before it can accept a single order**.
  That intervention is a stated precondition, not an assumption.
- The backup stays available as a **manual recovery path for new entries only**.

**No RTO number changes as a result of AD-3.** What changes is that neither number was ever
attributable to the backup broker, and v0.1 left that implicit where a reader could have
assumed otherwise.

**Backup schedule and the drill.**

| Artifact | Frequency | Retention | Off-VM? |
|---|---|---|---|
| WAL segments | continuous | 35 days | yes |
| Postgres base backup | nightly | 35 days | yes |
| VM image | weekly | 8 weeks | yes |
| Config + Grafana dashboards + model artifacts | on change (version-controlled) | forever | yes |
| Audit trail export (signed) | monthly | **7 years** `[DEFAULT-10]` | yes |

**A restore drill runs monthly**, restores to a scratch VM, and asserts all five recovery
conditions plus the panic script against the paper account. It emits an `AuditEvent` on success
and a CRITICAL alert on failure or on a missed drill. A backup that has never been restored is
not a backup, and a drill that is not scheduled and audited does not happen.

**Consequences.**
- `synchronous_commit = on` for the trading tables costs write latency, which is irrelevant at
  ADR-14's volumes (a few thousand rows per session) and is the correct trade.
- The panic script is a permanent maintenance obligation: it must be re-tested whenever the broker
  API changes `[VERIFY-P0.2]`, and it holds a credential outside Vault by design (Vault is part of
  the stack that may be down), which is an accepted, documented exception to `[RS §15]`'s
  Vault-only rule. The mitigation is that the credential is trade-and-cancel scoped, offline, and
  its use is alerted on.
- Condition 3 forces the audit trail to be the authoritative source for risk counters, which is a
  hard requirement on P1.4's schema: the trail must be replayable into counter state efficiently
  (an event-sourced projection with periodic checkpoints), not just greppable.
- Condition 2's "deny all new entries while UNRECONCILED" means a single unexplained position
  halts new entries pool-wide. This is intentionally blunt.

**What would make us revisit.** Capital ≥ USD 250,000 (making Option C's warm standby
proportionate); a broker offering a genuinely transferable position model; or evidence from the
monthly drill that RTO-operational cannot be met in 4 hours.

---

### ADR-11 — Single-market-first vs dual-market

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture) · **Date:** 2026-08-23

**Context.** `[CONST-10]` mandates two markets — US (NYSE/NASDAQ, Alpaca, separate data provider)
and India (NSE/BSE, Zerodha Kite) — and states that "nothing may be US-only by accident". The
issue frames this as deciding "whether every downstream spec carries two calendars, two brokers
and an FX layer from day one". Those are two different questions, and conflating them is the
trap: **architectural readiness** and **funded live trading** do not have to happen at the same
time, and the cost profiles are very different. See §0.3 C-1 for the constitutional reading.

The forcing facts:
- Zerodha requires a **daily manual login** to mint a session token `[RS §12 implied]`
  `[VERIFY-P0.2]`, and SEBI requires a **static IP** `[RS §15]`, `[RS §16]`. Neither is a code
  problem; both are operational obligations that must be solved before India can run unattended.
- India's cash segment has **no fractional shares** and has **lot sizes**, so a ≤5% position in a
  ₹100,000 pool is ₹5,000 — often below one lot of a liquid name, making the position-sizing rule
  unsatisfiable at small capital. The US side does not have this problem because Alpaca supports
  fractional shares `ASSUMPTION [VERIFY-P0.2]`.
- India equity round-trip costs are materially higher (ADR-13 Chain F: ~90 bps vs ~25 bps), so the
  same strategy needs roughly 3.5× the gross edge to break even there.
- Funding a US account from India is an LRS remittance with its own limits and TCS treatment
  `ASSUMPTION [VERIFY-P0.2]`, so capital allocation between the pools is a slow, manual,
  regulated operation — which is exactly why ADR-15 forbids the system from moving money.

**Options considered.**

| # | Option | Dev | Run | Ops | Cx | Notes |
|---|---|---|---|---|---|---|
| A | US-only architecture; add India later | 0 wk now | lowest | lowest | LOW now, **VERY HIGH later** | Retrofitting a currency, a calendar and a broker abstraction into a frozen domain model touches every spec from P1.1 onward. Violates `[CONST-10]` |
| B | **Dual-market by contract, US-first by capital**: two-market abstractions mandatory from P1.1; India adapter implemented and tested against recorded fixtures; India unfunded until a named gate | +2–3 wk across Stage 1–3 | +$0 (no India data/broker spend until activation) | +0 h/mo | MED | Pays the abstraction cost once, at the cheapest possible time, without paying the operational cost |
| C | Dual-market live from day one | +6–8 wk | +$10–20/mo (Zerodha ₹500 `[RS §10]`) + India data | +6 h/mo (daily login, two session windows spanning ~14 h) | HIGH | Two live markets before one is proven; two sets of live bugs; capital split across two pools, halving the already-small position sizes |

**Decision.** **Option B — dual-market by contract, US-first by capital.**

**Mandatory from day one (so nothing is US-only by accident, satisfying `[CONST-10]`).** Every
item below is a hard requirement on P1.1–P1.4 and Stage 2/3, and a phase that omits one is
non-compliant:

| # | Requirement | Where it binds |
|---|---|---|
| 1 | `Market` enum (`US`, `IN`) on **every** instrument, bar, order, position, decision and audit row. No table has an implicit market | P1.1, P1.2 |
| 2 | `Exchange` and a **trading-calendar type** — sessions, holidays, half-days, pre/post, DST, settlement cycle — not a hard-coded US holiday list | P1.1 |
| 3 | `Currency` and `Money` as explicit types. Arithmetic between different currencies **raises**; there is no implicit conversion anywhere | P1.1 |
| 4 | Broker adapter **interface** with ≥2 implementations: Alpaca (live) and Zerodha (implemented, unit-tested against recorded fixtures, never funded in v1). One implementation is not an abstraction. **Broker hierarchy per AD-4: Zerodha primary (India), Upstox automated backup/monitoring candidate via `extended_token`, IBKR manual-only emergency backup (US, AD-3)** | P3.1 |
| 5 | FX rate table and consolidated-NAV computation (ADR-15) present and exercised, even while `NAV_IN = 0` | P1.2, P2.9 |
| 6 | Tick size, lot size and fractional-share capability as **per-market instrument attributes**, never constants | P1.1 |
| 7 | Per-market config namespace (`market.US.*`, `market.IN.*`) with **no global defaults** — a missing per-market key is a startup failure, not a silent fallback to the US value | P1.3 |
| 8 | Per-market **and** consolidated risk-limit evaluation paths, both implemented and tested (ADR-15) | P2.9 |
| 9 | SEBI unique-strategy-ID tagging on every order `[CONST-9]`, harmless on US orders, mandatory on Indian ones | P3.2 |

**India activation gate** — all five, with ADR-09 row 6 Owner approval:
1. The US ladder `[RS §12]` is complete through stage 6 (controlled live, 3 months, meeting risk targets).
2. Zerodha daily-login token minting and static-IP hosting are solved and operationally proven for ≥30 consecutive sessions in paper mode `[VERIFY-P0.2]`.
3. A **separate** India capital pool of ≥ **₹5,00,000** exists — derived from the lot-size arithmetic above, so that a 4% target weight (₹20,000) reliably buys at least one lot of a liquid NSE name `ASSUMPTION`.
4. SEBI obligations discharged: strategy-ID tagging live, OPS measured and under the 10/exchange threshold or registration complete `[RS §16]`.
5. India-specific cost and tax modelling (STT, stamp duty, exchange charges, GST, STCG) is implemented in the backtest and the minimum-edge rule (ADR-13 Chain F) is re-derived for India.

**Consequences (this is the part the issue asks about explicitly).**
- **Every downstream spec carries two calendars, two brokers and an FX layer from day one.** Yes —
  deliberately. The alternative (Option A) makes P1.1's domain model US-shaped, and every later
  spec inherits that shape.
- The daily-loss and drawdown limits need a per-market day boundary *and* a consolidated one from
  the start, even while India is empty. ADR-15 defines both; P2.9 implements both.
- Testing burden roughly doubles for calendar-sensitive logic: every session-boundary test needs a
  US case and an India case (India has no DST; the US does — see ADR-02 and §6).
- v1 accepts that a fully-implemented Zerodha adapter ships without ever having placed a live
  order. Mitigation: it is tested against recorded response fixtures and against the Zerodha
  sandbox where one exists `[VERIFY-P0.2]`, and gate item 2 requires 30 sessions of paper
  operation before funding.
- Because ADR-12 is long-only cash and India's cash segment has no overnight short anyway, the
  strategy is structurally portable — a long/short design would have been silently US-only, which
  is precisely the accident `[CONST-10]` forbids. ADR-12 and this ADR reinforce each other.

**v0.2 (AD-4) — broker hierarchy, fixed in three tiers.** P0.2 F-5 verified that Upstox issues an
`extended_token` surviving the daily expiry for **read-only** endpoints, while Zerodha's
`access_token` expires at 06:00 IST for **everything** `[V]`. That is an operational
convenience and **convenience does not promote a broker**:

| Tier | Broker | Role | Authentication reality |
|---|---|---|---|
| **Primary** | **Zerodha Kite** | India execution and data, per `[CONST-10]` | Daily human login before the 06:00 IST expiry; static IP mandatory for order placement from 2026-04-01 `[V]` |
| **Automated backup / monitoring** | **Upstox** | Read-only monitoring and order-book reconciliation where supported | `extended_token` survives daily expiry for read-only endpoints; **the order path still needs daily re-auth** `[V]` |
| **Manual-only emergency** | **IBKR** | US new entries only, after a human login | Browser login on the gateway machine; ~6 min idle timeout; 24 h hard reset (AD-3) |

Upstox is **not** primary and is evaluated as a monitoring path at the activation gate below.
Moving it to the order path would require a `[CONST-10]` amendment.

**What would make us revisit.** India activation gate met (moves India from contract to capital);
or a Zerodha/SEBI change making unattended operation impossible `[VERIFY-P0.2]`, which would move
India from "deferred" to "not viable" and would need an explicit `[CONST-10]` amendment rather
than silent abandonment.

---

### ADR-12 — Long-only vs long/short

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Risk Owner) · **Date:** 2026-08-23

**Context.** `[CONST]` sets `gross <= 2x equity` and `net <= 1x equity`, which *implies* the
possibility of shorts and leverage, while `[CONST-8]` bans autonomous leverage outright. The
research summary never states a direction constraint. Left open, P2.8/P2.9 would have to invent
one. See §0.3 C-2 for how the ceilings are reconciled.

**Options considered.**

| # | Option | Dev | Run | Cx | Notes |
|---|---|---|---|---|---|
| A | **Long-only, cash account, no margin, no borrow** | 0 wk | $0 | LOW | No margin agreement, no borrow fees, no locate, no recall, no assignment. Portable to India's cash segment |
| B | Long-only + inverse-ETF hedging | +1.5 wk | $0 | MED | Deferred to ADR-05's v2 gate, not v1 |
| C | Long/short single names, margin account | +4–6 wk | borrow fees, variable and unmodellable in backtest | HIGH | Requires margin → leverage exists structurally; hard-to-borrow recalls are an execution failure we cannot model or control |
| D | Market-neutral (matched long/short book) | +6–8 wk | borrow + higher turnover | HIGH | All of C, plus roughly double the round-trip cost drag (ADR-13 Chain F), against a strategy whose edge is unproven |

**Decision.** **Option A — long-only, cash account, no margin, no borrow, no leverage, through
v1 and v2.**

**Reasons, in descending weight:**
1. **Shorting requires a margin account, and margin is leverage.** Even a nominally unlevered
   short book borrows the shares. `[CONST-8]` bans autonomous leverage; an autonomous system with
   a margin agreement has leverage available to it by construction. Removing the *capability*
   is stronger than policing its use.
2. **Unbounded loss is incompatible with the risk framework.** A 2.5×ATR stop `[CONST]` bounds a
   long position's loss to a known fraction of NAV. On a short, a gap-up can exceed the stop
   without limit, and the 10% drawdown kill switch is a *detector*, not a *preventer* — it fires
   after the loss.
3. **Hard-to-borrow and recall risk is an unmodellable execution failure.** A forced buy-in is an
   exit the system did not choose, at a price it did not choose, and it cannot be backtested
   because historical borrow availability is not in any dataset we have (ADR-04).
4. **India's cash segment has no overnight short.** A long/short design would be structurally
   US-only, violating `[CONST-10]` (see ADR-11).
5. Long-only makes the account a **cash account**, which is what makes settled-funds the binding
   cash constraint rather than PDT (§0.4 R-1) — a simpler, more deterministic rule to enforce.

**Consequences.**
- `gross ≡ net ≤ 1.0×`. The constitutional 2× / 1× ceilings stay in config as unreachable upper
  bounds; the risk engine enforces `min(constitutional, account_type)` (§0.3 C-2).
- **The system cannot profit in a falling market.** Accepted. The mitigation is the regime
  detector's ability to move to cash, which `[RS §23]` identifies as the most valuable capability
  the system has: "know when to stay out of the market". Cash is the v1 hedge.
- Cash drag: with a 20% cash buffer (ADR-14) plus regime-driven de-risking, expected invested
  exposure is roughly 60–80%. Performance metrics must be reported on **NAV**, not on invested
  capital, or the Sharpe is flattered by excluding the cash the strategy chose to hold.
- Benchmark selection follows: a long-only, sometimes-in-cash US equity strategy is measured
  against a total-return index, and the fraction of time in cash is itself a reported metric.
- No margin agreement, no `Regulation T` handling, no maintenance-margin monitoring, no
  short-locate integration, no borrow-fee accrual in the P&L model. Each is a subsystem that does
  not need to be built, specified, tested or audited.

**What would make us revisit.** Not before v3, and only with **all** of: (a) a fully-funded or
cash-secured structure that does not create leverage; (b) an explicit, sourced borrow-cost and
recall model in the backtest; (c) a hard per-name and aggregate short cap; (d) a `[CONST-8]`
amendment; (e) ADR-09 row 12 Owner approval. Option B (inverse-ETF hedging) is the nearer, cheaper
step and is already gated in ADR-05.

---

### ADR-13 — Holding period

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture and Risk Owner) · **Date:** 2026-08-23
**Reversibility: treat as irreversible.** Fourteen other ADRs, the storage class, the cost model,
the tax module and the entire validation pipeline are derived from it.

**Context.** The research summary never states a holding period, yet almost every design choice
in it silently assumes one. The prompt is explicit that this "drives everything downstream" and
requires the second-order chains to be written out. The internal evidence in the research summary
already constrains the answer more than it appears:

| Evidence in `[RS]` | What it implies about horizon |
|---|---|
| Fundamental analysis weighted 60% of the score `[RS §6]` | Fundamentals update quarterly. A 60%-fundamental score is incoherent at an intraday horizon — the dominant input would be constant across the entire holding period |
| Stop = `entry − 2.5 × ATR(14)` `[CONST]`, `[RS §11]` | A 2.5×ATR distance on daily bars is a multi-day move. Intraday it would be hit rarely and meaninglessly |
| "Momentum OR Value filter, 6-month return" `[RS §4]` | A 6-month momentum feature has no intraday interpretation |
| Walk-forward, **3-month rolls** (AD-2), 34+ windows `[RS §13]` | Presumes trades whose outcomes resolve within a window — a 15-day median hold resolves ~6× inside a 3-month window |
| PDT limits for accounts < $25,000 `[RS §16]`; capital ladder starts at $1,000 `[RS §12]` | Intraday trading is legally and practically foreclosed at this capital level |
| "Know when to stay out of the market" as the key feature `[RS §23]` | A patient, low-turnover posture |

**Options considered.**

| # | Option | Horizon | Dev | Run (data + infra) | Cx | Round-trip cost drag `ASSUMPTION` | Verdict |
|---|---|---|---|---|---|---|---|
| A | **Intraday** | minutes–hours, flat overnight | +8–12 wk (streaming ingest, quote handling, latency budget, smart order handling) | **$300–2,000+/mo** (quote/consolidated feed, higher-spec VM) | HIGH | ~63%/yr at 1-day turnover | **Rejected** |
| B | **Swing** | days–weeks | baseline | **≈$129–228/mo verified data+broker; VM and backup unpriced (AD-1)** | MED | **~4.2%/yr at 15-day median** | **SELECTED** |
| C | **Position** | months–quarters | baseline − 1 wk | $30–120/mo | LOW-MED | ~0.35–1.05%/yr | Rejected — see below |
| D | Hybrid: position-horizon core + intraday overlay | mixed | +10–14 wk | $300–2,000+ | VERY HIGH | mixed | Rejected — pays A's costs to get C's returns |

**Why not intraday (Option A).** Four independent disqualifiers, any one of which is sufficient:
transaction-cost drag of ~63%/yr (Chain F below) exceeds any plausible gross edge; PDT/settled-cash
rules foreclose it at the program's capital `[RS §12]`, `[RS §16]`; the 60%-fundamental score is
meaningless at that horizon; and the infrastructure cost is 10–60× higher for a program whose
edge is unproven. Note that **LLM cost is *not* one of the disqualifiers** — see Chain G, where
the honest arithmetic is reported rather than an inflated one.

**Why not position (Option C), despite the lowest costs.** It is the tempting answer and it is
wrong here for reasons of *evidence*, not cost: at a 6-month horizon a 10-year backtest yields
roughly 20 non-overlapping holding periods per position slot, which is nowhere near ADR-08's
≥1,000-closed-trade requirement, so no model could ever be promoted on statistically meaningful
evidence. A 15-day horizon yields ~17 round trips per slot per year — roughly 3,400 closed trades
over 10 years at 20 slots — which clears ADR-08's bar with room. **The holding period is
constrained from below by transaction costs and from above by statistical sample size, and 15
days sits in that window.** This is the argument that decides between B and C, and it is the one
most likely to be forgotten later, so it is recorded here explicitly.

**Decision. Swing horizon, specified exactly:**

| Parameter | Value | Notes |
|---|---|---|
| Target **median** holding period | **15 trading days** | The design centre |
| Design band (95% of exits) | **3–40 trading days** | |
| **Minimum** holding period | **3 trading sessions** | Overridable only by an exit-hierarchy trigger of MEDIUM or higher `[RS §6 Phase 11]` |
| **Time stop** | **40 trading days** | If unrealised return < +2% and the thesis is unchanged → exit at the next rebalance `[RS §11]` |
| **Hard maximum** | **120 trading days** (~5.7 months) | Absolute. Forces slot turnover and guarantees uniform tax treatment (Chain E) |
| **Entry timing** | Once per session, orders placed 09:45–10:15 ET | No intraday entries, ever (ADR-14) |
| **Exit timing** | Intraday permitted for stop-loss and exit-hierarchy triggers, on 5-minute bars for held instruments only | Exits are allowed to be fast; entries are not |

The asymmetry in the last two rows is deliberate and load-bearing: **getting out may be urgent;
getting in never is.** It is what allows daily-bar signals with intraday protection, and it is
what keeps the streaming-data requirement scoped to ≤25 held instruments instead of 1,500.

---

#### ADR-13 second-order effect chains

The prompt requires these chains to be written out, not merely asserted. Each ends in the
downstream specification it constrains.

**Chain A — Holding period → data frequency → provider tier → infrastructure class.**

> 15-day median hold → signal features are daily and quarterly (6-month momentum, ATR(14),
> ADX(14), VWAP-relative, 20-day volume, sector-normalised fundamental z-scores `[RS §5]`)
> → **daily bars are the primary signal granularity**; 5-minute bars are needed only for
> instruments currently held (≤25), for stop and exit-trigger evaluation
> → no consolidated tape, no L2 depth, no tick data, no quote feed for the universe
> → market-data spend drops from the institutional tier (**$300–2,000+/mo**) to the retail tier
> — **verified at ≈$129/mo paper and ≈$228/mo live** `[V]` P0.2 §4.3, with VM and off-VM backup
> still unpriced so the operating total is **INCOMPLETE** (AD-1)
> → **third order:** no low-latency or co-located ingest path is needed → any cloud region works →
> a single VM suffices (ADR-03) → DR is an image plus WAL replay rather than cluster failover
> (ADR-10) → the whole operational model is a once-a-day batch that is *allowed to be down*.
>
> **Constrains:** P0.2 (which data tier we even shop for), P0.3 (VM sizing), P2.1 (ingest design),
> P3.3 (monitoring scope).

**Chain B — Holding period → data volume → storage class → what the disk is actually for.**

Row-count arithmetic, all figures `ASSUMPTION [VERIFY-P0.3]` on row width (~92 B/bar including
overhead) and on TimescaleDB compression (8–20× on numeric time series).

> **v0.2 (A-19).** The ~92 B figure **silently assumes `double precision` OHLC**. Under
> `numeric` the row is **~116 B** (P0.3 §2.1 gives the composition). P1.2 must choose
> explicitly against P1.1's `Decimal` mandate rather than inherit an unstated premise, and
> `numeric` must be declared with precision and scale or Timescale's numeric compression is
> defeated. The 26% difference changes no conclusion in this chain.
>
> **v0.2 (A-20).** This chain **omits bitemporality**, which P1.2 makes mandatory for anything
> a backtest reads. As-reported versus as-restated fundamentals multiply that table by a
> restatement factor (`ASSUMPTION` ~1.5×) and add 16 B to every backtest-read row. Immaterial
> to the total (<60 GB stands), material to P1.2's schema.

| Dataset | Rows | Raw | Compressed |
|---|---|---|---|
| Daily bars, 1,500 symbols × 2,520 sessions (10 y) | 3.78 M | ~348 MB | **~20–45 MB** |
| Daily bars, ongoing | 378 k/yr | ~35 MB/yr | ~3 MB/yr |
| Fundamentals, 1,500 × 40 quarters | 60 k | ~90 MB | ~30 MB |
| Corporate actions, 10 y | ~90 k | small | small |
| News, ~200 items/day × 3 y forward | ~220 k | ~440 MB | ~120 MB |
| 5-min bars, **held positions only**, 25 × 78 × 252 × 3 y | 1.47 M | ~135 MB | ~15 MB |
| 5-min validation slice, top 200 × 2 y | 7.86 M | ~720 MB | ~70 MB |
| **Audit trail**, ~15 k events/session × 252, ~1 KB each | 3.8 M/yr | **~3.8 GB/yr** | **~1 GB/yr** |

> **Finding: the audit trail, not market data, is the dominant storage line — by roughly 30×.**
> Ten-year steady state is well under **60 GB**, so a single 250 GB SSD covers a decade.
> **Storage is not a design constraint** — but that is *only* true because of this ADR.
>
> Contrast, computed rather than asserted: 1-minute bars for the full universe over 10 years =
> 1,500 × 390 × 2,520 ≈ **1.47 billion rows**, ~135 GB raw, ~7–17 GB compressed — large but
> survivable. The genuine breaker at intraday is not bars but **quotes and ticks**, which run to
> multiple terabytes and require a paid consolidated feed; and intraday *execution* needs quotes,
> not bars. Stating this precisely matters: a later phase must not "discover" that 1-minute bars
> are cheap and conclude intraday is therefore affordable.
>
> **Constrains:** P0.3 (VM disk sizing must be driven by the audit trail), P1.2 (hypertable chunk
> intervals and compression policy differ sharply between a 3.8 M-row/yr audit table and a
> 378 k-row/yr bar table), P1.4 (retention and export).

**Chain C — Holding period → order flow → ingest shape → the burst that does not exist.**

> 20 slots ÷ 15-day median hold ≈ **1.33 exits/session and 1.33 entries/session**, ≈ **2.7
> orders/session** in steady state (capped at 4 new entries/session by ADR-14's turnover governor)
> → SEBI's 10 OPS *per second* threshold `[RS §16]` is under-run by roughly four orders of
> magnitude, so no strategy registration is triggered on OPS grounds `[VERIFY-P0.2]`
> → ingest is a **nightly batch** (3,780 daily-bar rows in one `COPY`, under a second), not a
> stream
> → **the market-open ingest burst that dominates intraday system design simply does not exist
> here.** P0.3's "worst minute of the day" analysis should conclude that the worst minute is the
> EOD bulk load, and it is trivial.
>
> **Constrains:** P0.3 (throughput and IOPS modelling), P2.1 (batch ingest, not streaming),
> P3.2 (order-rate limits are never approached), P6.3 (SEBI OPS compliance posture).

**Chain D — Holding period → PDT and settlement → a rule the research summary got wrong.**

> Entries at a fixed daily window, exits ≥ T+1 by design → **structurally zero day trades in
> normal operation**
> → **but** ADR-12 selects a **cash account**, in which PDT does not apply at all; the binding
> constraint is instead **settled funds** (§0.4 R-1). US equity settlement is T+1
> `ASSUMPTION [VERIFY-P0.2]`; reusing unsettled proceeds creates good-faith / free-riding
> violations, with a 90-day restriction after repeat occurrences `ASSUMPTION [VERIFY-P0.2]`
> → **therefore the risk engine must size entries against `settled_cash`, not `total_cash`** —
> a field that must exist in P1.1's `Account` model and be enforced in P2.9
> → **second order:** ADR-14's ≥20% cash buffer is not only a position-drift buffer; it is the
> settlement buffer that makes a T+1 cycle workable without ever touching unsettled proceeds
> → **third order:** if the account ever becomes a margin account (ADR-12 revisit), PDT becomes
> binding instead. Both counters are therefore specified now so the switch is a config change:

| Counter | Applies when | Rule |
|---|---|---|
| `settled_cash` | `AccountType.CASH` (v1) | New entries sized against settled cash only. A buy that would consume unsettled proceeds is **DENIED** |
| `day_trades_5d` | `AccountType.MARGIN` (future) | While equity < $25,000, **deny all new entries** when `day_trades_5d >= 3` — because any new position could stop out the same session and become the fourth day trade |

> Kill-switch liquidation is **exempt** from both counters. A PDT flag or a good-faith violation
> is a 90-day inconvenience; an uncontrolled drawdown is permanent. This exemption is deliberate,
> documented, and alerted on.
>
> **Constrains:** P1.1 (`Account`, `AccountType`, `settled_cash`), P2.9 (both counters as
> deterministic pre-trade checks), P3.2 (order timing), P6.3 (compliance monitoring).

**Chain E — Holding period → tax treatment → what the accounting layer must carry.**

All rates below are `ASSUMPTION [VERIFY-P0.2]`; this document does not assert tax law and this is
system-design analysis, not tax advice — the owner's actual position needs a qualified
professional.

> **US:** every holding is < 365 days → **always short-term capital gains**, taxed as ordinary
> income → there is no tax-driven holding-period optimisation to model, and the **hard 120-day
> maximum guarantees a single tax regime**, so the accounting layer never needs mixed
> STCG/LTCG lot treatment. That simplification is a *direct consequence* of the 120-day cap and is
> the main reason it exists.
> → **but** the **wash-sale rule (30 days before and after) binds hard at a 15-day median hold
> with a weekly-reconstituted universe**: the system will routinely re-enter a name it exited
> within the window
> → **therefore lot-level cost basis with a wash-sale adjustment field is mandatory in P1.1 from
> day one**, not a later reporting feature. At a >12-month horizon (Option C) wash-sale exposure
> would have been near zero and this requirement would not exist.
>
> **India (when ADR-11's gate opens):** holdings < 12 months → STCG; the Finance Act 2024 raised
> listed-equity STCG to 20% and LTCG to 12.5% with a ₹1.25 lakh exemption, effective 23 July 2024
> `ASSUMPTION [VERIFY-P0.2]`. Add STT on both legs, stamp duty, exchange charges and GST. India
> has no wash-sale rule but does have set-off and carry-forward rules.
> → **second order:** India's higher STCG plus STT raises the required gross edge materially,
> reinforcing ADR-11's US-first sequencing on economics as well as operations.
>
> **Third order, applying to both:** because the strategy is always short-term,
> **post-tax Sharpe ≈ pre-tax Sharpe × (1 − marginal rate)** on the P&L component.
> → **binding instruction to P5.1/P5.3: every backtest must report a post-tax line alongside the
> pre-tax line.** A pre-tax-only Sharpe of 1.0 `[RS §13]` is not a 1.0 the owner receives, and a
> strategy accepted on a pre-tax number may be rejected on a post-tax one.
>
> **Constrains:** P1.1 (lot-level basis, wash-sale field, `CostBasisMethod`), P5.1/P5.3 (post-tax
> reporting), P6.3 (tax reporting export).

**Chain F — Holding period → turnover → transaction-cost drag → the minimum edge. This is the
strongest quantitative argument in the ADR.**

Cost assumptions, all `ASSUMPTION [VERIFY-P0.2]`, with the calibration method named so P5.3 can
replace them with measured values: half-spread 2–10 bps for names passing ADR-14's liquidity
filters; market impact 5–15 bps at ≤1% of ADDV participation over a 30-minute window
(square-root impact model, calibrated on realised fills once ≥200 live fills exist); Alpaca
commission $0 with SEC/FINRA fees a fraction of a bp on sells.

> **Assumed round trip: ~25 bps US, ~90 bps India** (India adds STT ~0.1% per delivery leg, stamp
> duty, exchange charges and GST, plus wider spreads `ASSUMPTION [VERIFY-P0.2]`).
>
> Annual cost drag on the traded book = (252 ÷ median hold in days) × round-trip cost:

| Median hold | Round trips / slot / yr | US drag @ 25 bps | India drag @ 90 bps |
|---|---|---|---|
| 1 day (intraday) | 252 | **63.0 %** | 226.8 % |
| 3 days | 84 | 21.0 % | 75.6 % |
| **15 days (selected)** | **16.8** | **4.20 %** | 15.1 % |
| 40 days | 6.3 | 1.58 % | 5.67 % |
| 120 days | 2.1 | 0.53 % | 1.89 % |
| 6 months | 2.0 | 0.50 % | 1.80 % |

> At 80% invested (ADR-14), the 15-day figure is ≈ **3.4% of NAV per year**. The strategy must
> generate more than that in gross alpha before it earns anything at all — and then Chain E's
> post-tax haircut applies on what remains.
>
> → **This is the decisive number against intraday**: a 63%/yr cost drag cannot be out-earned by
> a daily-bar, fundamentals-weighted strategy. It is also the argument against the *short end* of
> the swing band, which is why the median target is 15 days and not 3, and why a 3-session
> minimum hold exists.
> → **Binding rule derived here:** the decision engine must not emit a BUY unless
> **expected 15-day alpha ≥ 2 × expected round-trip cost** — i.e. **≥ 50 bps in the US and
> ≥ 180 bps in India**. The 2× multiple is a margin of safety for slippage-model error, not a
> precise optimum; it is recorded as `[DEFAULT-8]` and is recalibrated against measured fills in
> P5.3.
>
> **Constrains:** P2.8 (decision engine must carry an explicit expected-edge threshold),
> P5.3 (cost model must reproduce this table with measured inputs), P0.3 (cost sensitivity).

**Chain G — Holding period → LLM invocation frequency → cost → and the finding that actually
matters.**

Token assumptions: ~6,000 input tokens per candidate (structured fundamentals, price/technical
summary, ~10 sanitised news items, sector context) and ~1,500 output tokens (structured thesis
JSON). **Prices below are v0.1 estimates, since superseded by verified figures in P0.2 §3.11–3.12
and recomputed in P0.3 §5; and since AD-5 the primary is OpenAI `gpt-5.6-luna`, not DeepSeek.
The table is retained because Chain G's *conclusion* — that cost is not the binding constraint —
survives every price revision.** v0.1 estimates: DeepSeek ~$0.27/M in, ~$1.10/M out; GPT-4o-mini
~$0.15/M in, ~$0.60/M out; a frontier fallback ~$3/M in, ~$15/M out. One gate firing per session,
21 sessions/month.

| Gate width | Calls/mo | DeepSeek | GPT-4o-mini | Frontier |
|---|---|---|---|---|
| 5 | 105 | $0.34 | $0.19 | $4.25 |
| 10 | 210 | $0.69 | $0.38 | $8.51 |
| 15 (design point) | 315 | $1.03 | $0.57 | $12.76 |
| 20 | 420 | $1.37 | $0.76 | $17.01 |
| 50 | 1,050 | $3.43 | $1.89 | $42.53 |

> **Finding, reported honestly: at swing frequency the live LLM tier costs under $5/month at any
> gate width up to 50, on any non-frontier model — two orders of magnitude below the $200–500/month
> figure in `[RS §6 Phase 5]`.** (§0.4 R-3.)
>
> **Where the $200–500 actually lands: backtest replay.** A 10-year walk-forward replay at
> 15 candidates/session = 2,520 × 15 = **37,800 calls per full run** → ~$124/run on DeepSeek,
> ~$1,530/run on a frontier model. Two full replays a month is exactly the $200–500 band. The
> figure is retained as a **ceiling and alarm threshold** (alert if monthly LLM spend > $50 in
> live operation, which would indicate the gate has failed), not as a forecast.
> → **Derived requirement:** the LLM path must be **deterministically cacheable and replayable** —
> cache key = hash(sanitised input payload ‖ `model_id` ‖ `prompt_version`) — so a re-run costs
> ~$0 and only new `(date, symbol)` pairs are billed. Binding on P4.3 and P5.1.
>
> **Second order, and this reframes the inference gate entirely:** since cost is *not* the binding
> constraint at swing frequency, **the gate (P4.2) exists for hallucination control, determinism
> and attack-surface reduction — not for cost control.** `[CONST-3]` still mandates the gate; this
> chain establishes *why*, and P4.2 must be designed against that objective. A gate designed to
> minimise spend would be tuned very differently from one designed to minimise the number of
> untrusted-text-derived claims that can reach a decision.
>
> **Third order, and it is a hard methodological constraint:** an LLM's training corpus contains
> the backtest period's future. Any walk-forward optimisation of LLM-derived features is
> irreducibly contaminated by look-ahead — no amount of careful date-slicing removes it, because
> the leakage is in the model weights, not in the data pipeline.
> → **Therefore: the walk-forward-validated, promotable strategy is the deterministic
> Tier-1/Tier-2 path only. The LLM tier's contribution is validated forward, in paper trading
> `[RS §12 stage 3]`, and never enters ADR-08's promotion evidence.** This is constraint #10 on
> the one-page sheet and is binding on P4.3, P5.1, P5.2 and ADR-08.
>
> **Constrains:** P0.3 (LLM budget model), P4.2 (gate design objective), P4.3 (caching and
> replay), P5.1/P5.2 (what may be optimised), ADR-08 (what may be promoted).

**Chain H — Holding period → thesis shelf life → LLM call pattern.**

> A 15-day hold gives a thesis a ~15-day shelf life → the LLM generates a thesis **once per
> entry**, and it is thereafter **re-validated, not regenerated**, by deterministic checks against
> its own invalidation conditions `[RS §6 Phase 6]`
> → LLM calls scale with **entries (~1.33/session) plus gate width**, never with bars
> → the Research agent is idempotent per `(symbol, trading_date)`, which is what makes Chain G's
> cache key well-defined
> → contrast: an intraday horizon would require intraday thesis regeneration, ~100× the calls, and
> would make the cache useless because the input payload changes every bar.
>
> **Constrains:** P4.3 (call pattern and idempotency), P2.8 (thesis re-validation is deterministic,
> never an LLM re-ask), P3.3 (monitoring checks invalidation conditions, not thesis quality).

**Chain I — architecture viability, the summary of A–H.**

> Swing (15-day) → daily bars → retail data tier → nightly batch ingest → no open burst → <60 GB
> for a decade → single VM → no Kubernetes → simple DR → cash account → settled-funds rule →
> uniform short-term tax with mandatory wash-sale tracking → ~4.2%/yr cost drag setting a ≥50 bps
> minimum edge → ~2.7 orders/session → LLM cost negligible live and cacheable in backtest → gate
> justified by safety rather than cost → ~3,400 closed trades per 10-year backtest, clearing
> ADR-08's promotion sample requirement.
>
> **The architecture in `[RS §7]` is viable at a swing horizon and is not viable at an intraday
> horizon on this budget.** That is the answer to the question the issue poses.

**Consequences (beyond the chains).**
- Nothing downstream may assume an intraday entry path exists. P3.2's order types are limit orders
  placed in a fixed daily window `[CONST]`.
- The 5-minute exit path is scoped to held instruments only, which is what keeps a streaming
  subscription to ≤25 symbols instead of 1,500.
- Backtest intrabar stop simulation must not require 10 years of 5-minute bars for the whole
  universe. **Decision:** backtests simulate stops on daily OHLC with a conservative intrabar
  assumption — if `Low ≤ stop`, fill at `min(stop, Open)` less slippage, which prices a gap-down
  honestly rather than optimistically. The top-200 × 2-year 5-minute slice (Chain B) exists
  specifically to validate that assumption, not to run the backtest. Binding on P5.1.

**What would make us revisit.** Realised median holding period drifting outside 8–25 trading days
for two consecutive quarters (the design centre is wrong); measured round-trip costs exceeding
40 bps US (the cost table's premise fails and the horizon must lengthen); capital exceeding
$250,000 *and* measured turnover falling such that Option C's sample-size objection weakens; or a
change in settlement or tax treatment that alters Chains D or E materially.

---

### ADR-14 — Universe size and rebalance cadence

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Head of Architecture) · **Date:** 2026-08-23

**Context.** `[RS §4]` specifies the filters (market cap > $500M, volume > $1M, price > $5,
momentum-or-value, volatility < 3× market) and expects "50–200 candidates" from Tier 1 and
"20–50" from Tier 2, but never states the size of the *input* set or how often the pipeline runs.
The issue notes this "drives ingest throughput and the entire cost model". ADR-13 has already
fixed the cadence's upper bound (no intraday entries), so the remaining questions are the
universe's size, its reconstitution rule, and the portfolio's shape.

**Options considered — universe size.**

| # | Option | Instruments | Daily rows/yr | Fundamentals refresh | Cx | Notes |
|---|---|---|---|---|---|---|
| A | Mega/large cap (S&P 500-ish) | ~500 | 126 k | ~500/qtr | LOW | Most-researched, most-efficient names; the least likely place for a retail system to find edge |
| B | **Large + mid, ADDV-ranked, capped** | **1,500** | **378 k** | ~1,500/qtr | LOW-MED | Where sector-relative fundamental scoring `[RS §5]` has room to work, still all liquid |
| C | Broad (Russell 3000-ish) | ~3,000 | 756 k | ~3,000/qtr | MED | Doubles data cost and fundamentals coverage burden; the marginal names sit near the liquidity floor |
| D | All listed passing filters | ~6,000–8,000 | 1.5–2.0 M | large | HIGH | Includes microcaps where the 1%-of-ADDV cap makes positions too small to matter at any plausible NAV |

Data cost scales roughly linearly with instrument count at the retail tier `[VERIFY-P0.2]`;
compute is immaterial at every option (XGBoost scoring 1,500 rows is sub-second). The binding
consideration is not cost but **signal quality vs. fundamentals-coverage burden**: options C and D
add names whose fundamental data quality is materially worse, which degrades the 60%-weighted
component `[RS §6]`.

**Decision — universe.**

**Eligibility (all must hold, evaluated on the most recent completed session):**

| Filter | Value | Edge case resolved |
|---|---|---|
| Listing | US primary listing, NYSE / NASDAQ / NYSE American | ADRs, ETNs, closed-end funds, SPACs, units, warrants, rights, preferred, OTC excluded (ADR-05) |
| Security type | Common stock only | Enforced on the reference-data type field **plus** a name-pattern guard for units/warrants/rights `[VERIFY-P0.2]` |
| Market cap | ≥ **$500M** `[RS §4]` | Measured on the last completed session's close × most recent reported shares outstanding; not intraday |
| Liquidity | 20-session **median** ADDV ≥ **max($1M, 100 × max_position_value)** | Median, not mean, so one spike cannot qualify a name. The NAV-scaling term is derived below |
| Price | ≥ **$5.00** `[RS §4]` | On the last completed session's **official close**, unadjusted. A stock halted below $5 is excluded on its last valid close |
| History | ≥ **250 completed sessions** | Excludes recent IPOs — no momentum feature, no lockup visibility, unreliable early fundamentals |
| Fundamentals | ≥ **4 reported quarters** | Sector-normalised z-scores need a history to be normalised against |
| State | Not halted; not subject to an announced merger/acquisition | Deal-spread names break both momentum and value signals and are excluded until the deal resolves |
| Cap | Top **1,500** by 20-session median ADDV | Deterministic and bounded |

**The NAV-scaling liquidity term matters and is easy to miss.** `[CONST]` caps a position at
1% of ADDV. At a $10,000 NAV a 5% position is $500, so a $1M ADDV floor is ample. At a $250,000
NAV a 5% position is $12,500, which exceeds 1% of a $1M-ADDV name — the liquidity cap would bind
and silently shrink positions below their target weight. Scaling the floor as
`max($1M, 100 × max_position_value)` keeps the two rules consistent at every capital stage
instead of letting them collide at ~$100,000 NAV.

**Reconstitution: weekly, Saturday 06:00 UTC, with hysteresis.** A name **enters** at ADDV rank
≤ **1,300** and **exits** only at rank > **1,700** or on a hard-filter failure. The 1,300/1,700
band prevents names oscillating across a hard rank boundary from churning the universe every week
(the same reasoning behind index-provider banding rules). **A name currently held is never dropped
from the data universe while held**, regardless of rank — otherwise the system would stop
ingesting data for a position it still owns, which would blind the monitor and the exit agent.

**Decision — cadence.**

| Stage | When (UTC) | What |
|---|---|---|
| Ingest | 21:45 | EOD bars, corporate actions, fundamentals deltas for the completed session |
| Pipeline | 22:30 | Tier 1 screen → Tier 2 quant → inference gate → Tier 3 LLM → decision → risk → order list |
| Order placement | 13:45–14:15 (09:45–10:15 ET) | Limit orders from the frozen order list |
| Monitor | continuous during session | Held positions only, 5-minute bars, stops and exit hierarchy |

Signals are computed on the **prior session's completed daily bar**. Orders are placed 15 minutes
after the next open, avoiding the opening auction and letting the tape settle. **The order list is
frozen at pipeline time and is not re-derived at placement time** — if the market has moved such
that a limit no longer makes sense, the order simply does not fill, which is a safe outcome. Any
"refresh the signal at placement" logic would reintroduce an intraday decision path that ADR-13
forecloses.

**Decision — portfolio shape and turnover governor.**

| Parameter | Value | Reasoning |
|---|---|---|
| Target positions | **20** (band 15–25) | |
| **Target weight at entry** | **4.0%** | 20 × 5.0% = 100% would leave zero cash and put every position at the hard cap, so any favourable drift would breach it immediately. 4.0% gives ~25% headroom to the cap |
| Hard position cap | **5.0%** `[CONST]` | Breach on drift → REDUCE at next rebalance, not an emergency sale (see below) |
| Target invested | **80%**, ≥20% cash buffer | Doubles as the settled-cash buffer for Chain D's T+1 cycle |
| Max new entries | **4 / session** | Bounds slippage and prevents a regime flip turning the book over in a day |
| Max NAV traded | **20% / session** | Same purpose, expressed as value |

**Drift handling, stated because `[RS]` leaves it ambiguous:** the 5% cap is evaluated **pre-trade
on intended post-fill weight** for new and increased positions. An existing position that drifts
above 5% through appreciation alone does **not** trigger a forced sale — it is trimmed back to
4.0% at the next scheduled rebalance, and meanwhile it blocks any increase. Forcing an immediate
sale on drift would create trades driven purely by a rising price, which is both costly (Chain F)
and perverse. A drift above **7.5%** (1.5× the cap) does force a trim at the next session's order
window, so the exception cannot run away.

**Derived throughput and cost — the numbers the issue asks this ADR to produce.**

| Quantity | Value |
|---|---|
| Instruments ingested per session | 1,500 daily bars |
| Rows written per session | ~3,780 (bars + fundamentals deltas + corporate actions) |
| Peak write | one `COPY` of ~3,800 rows, < 1 s. **No open-burst ingest problem** (Chain C) |
| Provider requests per session | 1 bulk grouped-daily request, or ~1,500 per-symbol requests at ~5 req/s ≈ 5 min `[VERIFY-P0.2]` |
| Fundamentals refresh | staggered, ~25 symbols/session |
| News ingest | ~200 items/session, continuous |
| LLM calls | 15/session (gate width, ADR-13 Chain G) |
| Orders | ~2.7/session steady state, ≤4 entries + exits, hard-capped by the governor |
| 10-year storage | **< 60 GB**, audit-trail-dominated (Chain B) |

**India universe when ADR-11's gate opens:** NSE-listed, same rule shape, thresholds
₹500 Cr market cap and ₹5 Cr ADDV `[RS §4]`, hard cap **500** names, lot-size aware, with the
target weight re-derived so that 4% of the India pool buys at least one lot of the median
eligible name.

**Consequences.**
- The scanner's working set is fixed at 1,500 for all of Stage 2; P2.2 may size arrays and caches
  against that number rather than an open-ended universe.
- Weekly reconstitution means universe membership is a **point-in-time, versioned artifact**. Every
  backtest must select the universe as of the decision date from the stored membership history —
  this is the concrete mechanism that delivers `[RS §13]`'s survivorship-bias-free requirement,
  and it only works if reconstitution snapshots are immutable and retained forever.
- Delisted names must remain in the historical store with their delisting event and final price.
  Deleting them silently reintroduces survivorship bias — the exact failure `[RS §13]` warns about.
- The 1,300/1,700 band and the weekly cadence together bound universe turnover, which feeds
  ADR-07's T3 retrain trigger (> 15% replacement at one reconstitution).
- 20 positions at a 15-day median hold produce ~3,400 closed trades per 10-year backtest, which is
  what clears ADR-08's ≥1,000-trade promotion requirement (ADR-13's B-vs-C argument).

**What would make us revisit.** NAV crossing ~$100,000, where the ADDV floor's scaling term starts
to bind on the smaller half of the universe; measured Tier-1 output falling outside `[RS §4]`'s
50–200 candidates for 4 consecutive weeks (the filters, not the universe size, would be
mis-calibrated); fundamentals coverage quality below ~95% for the bottom ADDV quintile (shrink
toward Option A); or India activation, which adds a second universe under the same rule shape.

---

### ADR-15 — Base currency, FX, and dual-market NAV

**Status:** ACCEPTED · **Owner:** JS — Project Owner (acting Risk Owner) · **Date:** 2026-08-23

**Context.** `[CONST-10]` mandates two markets and ADR-11 requires the FX layer from day one, so
"how is a dual-market NAV computed" must be answered before P1.1 defines `Money` and before P2.9
defines what "2% daily loss" is a percentage *of*. The dangerous failure here is subtle and worth
stating up front: **if risk limits are evaluated only on consolidated NAV, a catastrophic loss in
the smaller pool is invisible.** A 10% loss in a ₹5,00,000 India pool alongside a $60,000 US pool
is roughly 1% of consolidated NAV — the drawdown kill switch would never fire, while one of the
two books was being destroyed.

**Options considered.**

| # | Option | Dev | Cx | Notes |
|---|---|---|---|---|
| A | Single pooled NAV in USD; system converts FX as needed | 2 wk | MED | Requires the system to execute currency conversions — a financial transfer, and squarely the kind of autonomous money movement `[CONST-8]`'s spirit and ADR-09 forbid. Also legally fraught under LRS `[VERIFY-P0.2]` |
| B | **Segregated pools, USD base for reporting, no system-initiated FX, dual limit enforcement** | 2.5 wk | MED | Matches the actual legal and operational reality: two accounts, two currencies, two regulators, one owner |
| C | Two fully independent systems, no consolidation | 1 wk | LOW | No consolidated risk view at all — a limit could be respected in each pool while the combined book breaches it |
| D | B + FX hedging of the India pool | +3 wk | HIGH | Requires an FX instrument, contra ADR-05; introduces a position whose purpose is not alpha and whose sizing rules do not exist |

**Decision.** **Option B.** Specified precisely:

**1. Base currency is USD.** Consolidated reporting, the performance record and the consolidated
risk counters are denominated in USD.

**2. Two segregated capital pools. The system never converts currency, ever.** Each market has its
own account, its own local cash, its own local NAV. Funding or defunding a pool is a **human
treasury action** under ADR-09 (an LRS remittance in practice `[VERIFY-P0.2]`), never an automated
one. There is no cross-margining and no cross-pool netting: USD cash cannot fund an INR trade.

**3. Position limits are per-pool, in local currency.** `position ≤ 5%` means 5% of **that pool's**
NAV, because that is the capital actually available to the trade. A consolidated-NAV position
limit would authorise an India position larger than the entire India pool.

**4. Loss and drawdown limits are enforced BOTH per-pool AND consolidated. The stricter binds.**

| Limit | Per-pool | Consolidated |
|---|---|---|
| Daily loss ≤ 2% | of that pool's NAV | of consolidated NAV |
| Weekly loss ≤ 5% | of that pool's NAV | of consolidated NAV |
| Max drawdown ≤ 10% (kill switch) | of that pool's peak NAV | of consolidated peak NAV |

A per-pool breach halts **that pool** and alerts. A consolidated breach trips the **global** kill
switch across both pools. This dual evaluation is the direct fix for the failure described in the
Context, and P2.9 must implement both paths and test both — including the asymmetric case where
the small pool breaches and the consolidated does not.

**5. FX rate handling.**

| Aspect | Rule |
|---|---|
| Source | RBI reference rate as primary, published each Indian business day `ASSUMPTION [VERIFY-P0.2]`; a named commercial fallback selected in P0.2 |
| Storage | `fx_rate(as_of_date, pair, rate NUMERIC(18,6), source, retrieved_at)`, **immutable once written** |
| Reproducibility | A past date's rate is **never re-fetched or corrected in place**. NAV history must be reproducible, and a silently revised rate rewrites history |
| Missing rate | **Fail-closed** `[CONST-6]`: no consolidated NAV is computed, consolidated limits cannot be evaluated, and therefore **no new entries are permitted in either pool** until the rate is available. Never carry forward, never interpolate, never default |
| Precision | Rate stored at 6 dp; conversion rounds **half-up at the final step only**, never at intermediates |

**6. FX is not a P&L source and is not hedged.** Strategy performance is measured **in local
currency per pool**. Consolidated performance is reported both **with** and **without** FX
translation, so a good year in India is not flattered or hidden by a rupee move. FX translation
effects appear as their own line, never blended into trading P&L.

**7. Day boundaries — the edge cases resolved.**
- Each pool's `trading_date` is its own exchange-local session date, from its own calendar (ADR-11
  requirement 2).
- The **consolidated accounting date is the UTC calendar date** on which each session closes.
- This mapping is unambiguous: the India close (15:30 IST = 10:00 UTC) and the US close
  (16:00 ET = 20:00 UTC in EDT, 21:00 UTC in EST) fall on the same UTC calendar date as each
  other. India observes no DST; the US does, which shifts its close by an hour twice a year — but
  **never across midnight UTC**, so the mapping holds year-round. This is exactly the kind of
  detail that would otherwise surface as an off-by-one-day bug in P2.9's daily-loss counter.
- The consolidated daily-loss counter is evaluated **after the later of the two closes** on a
  given UTC date, i.e. after the US close.
- On a date where one market is open and the other is on holiday, the closed pool contributes its
  last computed NAV unchanged, and its contribution is flagged `STALE_HOLIDAY` in the snapshot —
  distinguishable in the audit trail from a missing value, which would fail closed.

**Consequences.**
- P1.1's `Money` type carries an explicit currency and **raises on cross-currency arithmetic**.
  There is no implicit conversion anywhere in the system — the only place a conversion happens is
  the consolidated NAV snapshot, which is a single, audited, dated computation.
- P2.9 evaluates every loss limit twice (per-pool and consolidated) and must test the asymmetric
  cases in both directions.
- P1.2 needs the immutable `fx_rate` table and a consolidated NAV snapshot table with a
  `trading_date` / `utc_accounting_date` distinction.
- While India is unfunded (ADR-11), `NAV_IN = 0` and every consolidated computation runs anyway,
  exercising the code path daily rather than leaving it untested until the day capital arrives.
  This is deliberate: an FX layer first exercised on the day it matters is an FX layer that fails
  on the day it matters.
- Cash-drag and performance reporting must be per-pool, since the pools' cash buffers are separate
  and cannot subsidise each other.

**What would make us revisit.** India activation (moves this from an exercised-but-empty path to a
live one); a third market (would force a general N-pool consolidation rather than a two-pool one);
or the owner's treasury arrangements changing such that a single multi-currency account replaces
the two-account structure, which would change the segregation premise entirely.

---

## 4. Consolidated second-order effect map

A compact index of which ADR constrains which downstream phase, so a later phase can find its
inherited constraints without reading all fifteen records.

| Downstream phase | Inherited constraints |
|---|---|
| **P0.2 Providers** | ADR-13 A (retail data tier, daily bars + 5-min for ≤25 held), ADR-14 (1,500 US / 500 IN symbols), ADR-11 (Alpaca + Zerodha both needed, only one funded), ADR-04 (one news API, EDGAR, FRED), ADR-05 (no options/futures data) |
| **P0.3 Budget** | ADR-14 (throughput: ~3,800 rows/session, no open burst), ADR-13 B (audit trail dominates storage), ADR-13 G (LLM budget is a backtest-replay number, not a live one), ADR-03 (single VM, named saturation triggers) |
| **P1.1 Domain** | ADR-11 (`Market` everywhere, calendar type, per-market tick/lot/fractional), ADR-15 (`Money` with currency, raises on cross-currency), ADR-12 (`AccountType.CASH`), ADR-13 D (`settled_cash`, `day_trades_5d`), ADR-13 E (lot-level basis + wash-sale field), ADR-05 (`InstrumentType` deny-by-default) |
| **P1.2 Storage** | ADR-13 B (chunk/compression sized for an audit-dominated workload), ADR-14 (immutable universe-membership snapshots, delisted names retained), ADR-15 (immutable `fx_rate`, consolidated NAV snapshot) |
| **P1.3 Config** | ADR-11 (per-market namespaces, no global defaults), ADR-13/14 (holding and universe parameters), ADR-09 (approval policy) |
| **P1.4 Audit** | ADR-10 (trail must be replayable into risk-counter state with checkpoints), ADR-09 (`ApprovalRequest`/`ApprovalGrant` with nonce lifecycle), ADR-08 (`strategy_version`, `model_id` on every decision) |
| **P2.1 Data** | ADR-13 A/C (nightly batch, not streaming), ADR-04 (source list), ADR-14 (reconstitution job), `[DEFAULT-9]` (raw bars + corporate-action table, adjusted computed on read) |
| **P2.2 Scanner** | ADR-14 (fixed 1,500 working set, exact filters and their edge cases) |
| **P2.5 / P2.8 Decision** | §0.3 C-4 (weights must sum to 1.0, with a test), ADR-13 F (minimum-edge threshold), ADR-13 H (thesis re-validated deterministically, never re-asked) |
| **P2.9 Risk** | ADR-15 (dual per-pool + consolidated evaluation), ADR-12 (gross ≡ net ≤ 1.0×), ADR-13 D (settled-cash sizing), ADR-14 (drift handling, turnover governor), ADR-09 (no override path for a DENY) |
| **P2.10 Kill switch** | ADR-10 (restored TRIPPED, counters replayed from the trail), ADR-01 (three independent manual channels), ADR-15 (per-pool and global trip semantics) |
| **P3.1 Broker** | ADR-11 (two adapters, one funded), ADR-10 (broker is system of record; backup broker is not failover) |
| **P3.2 Orders** | ADR-13 (fixed daily window, limit orders, no intraday entries), ADR-02 (idempotency key from `(job, market, date, instrument)`) |
| **P3.3 Monitoring** | ADR-13 (5-min bars, held instruments only), ADR-14 (drift rules) |
| **P4.2 Gate** | ADR-13 G (**gate objective is safety, not cost**) |
| **P4.3 LLM research** | ADR-13 G (deterministic cache key, replayable), ADR-06 (context assembled by deterministic query, never semantic retrieval), `[DEFAULT-7]` (no portfolio data in the prompt) |
| **P5.1 / P5.2 Backtest** | §0.3 C-3 (simulate the kill switch), ADR-13 G (LLM tier excluded from optimisation), ADR-13 (daily-OHLC intrabar stop assumption), ADR-14 (point-in-time universe), ADR-13 E (post-tax reporting) |
| **P5.3 Costs** | ADR-13 F (reproduce the cost table with measured inputs) |
| **P6.1–P6.6 Operate** | ADR-01 (Grafana as code), ADR-02 (systemd units), ADR-10 (monthly drill), ADR-09 (approval SLAs), ADR-07/08 (retrain and promotion cadence) |

---

## 5. BLOCKING QUESTIONS — and the defaults used

Per Block C: these are the questions where two reasonable answers produce materially different
designs. Each is listed with its options, the default applied, and what breaks if the default is
wrong. **This phase proceeded on these defaults rather than stalling**; every one is tagged
`[DEFAULT-n]` where it is used above and repeated in §8 ASSUMPTIONS.

| # | Question | Options | **Default applied** | What breaks if wrong |
|---|---|---|---|---|
| 1 | Capital base and ladder | (a) $1k→$10k→$25k+ per `[RS §12]`; (b) start at $25k+; (c) paper only indefinitely | **(a)** — ladder as specified in `[RS §12]` | ADR-14's ADDV scaling term and ADR-05's alt-data cost rejection assume small capital. At (b), the ADR-03 and ADR-10 revisit thresholds arrive much sooner |
| 2 | Account type | (a) cash; (b) margin; (c) margin but unused | **(a) cash** (ADR-12) | If margin: PDT binds instead of settled funds (Chain D), and ADR-12's leverage argument weakens |
| 3 | Whose capital, and how many operators | (a) owner's own capital, one operator; (b) friends-and-family; (c) client money | **(a)** | (b)/(c) trigger investment-adviser / portfolio-manager registration `[RS §16]` and would make ADR-09's single-role model non-compliant |
| 4 | Owner's tax residency | (a) India-resident individual operating a US account; (b) US person; (c) other | **(a)** | Chain E's tax analysis, the LRS funding constraint (ADR-11), and W-8BEN/withholding handling all change. System design is unaffected except in the reporting module |
| 5 | Concurrent position target | (a) 10; (b) **20**; (c) 30+ | **(b) 20** (ADR-14) | At 10, single-name risk rises and the 5% cap binds constantly; at 30+, 4% target weights fall below viable order sizes at the early capital stages |
| 6 | Observability co-location | (a) Prometheus + Grafana on the same VM; (b) external managed | **(a)** | If the VM dies, observability dies with it — accepted, because ADR-10's panic script is deliberately independent of both |
| 7 | May the LLM see portfolio state? | (a) **never**; (b) aggregate only; (c) full | **(a) never** — no NAV, cash, positions, P&L or limits in any prompt | If (b)/(c): a successful injection could target the portfolio rather than one candidate's thesis, and blast radius stops being bounded `[CONST-4]` |
| 8 | Minimum-edge multiple over round-trip cost | (a) 1×; (b) **2×**; (c) 3× | **(b) 2×** (Chain F) | At 1× the strategy trades at breakeven whenever the slippage model is optimistic; at 3× the signal may rarely clear the bar. Calibrate against measured fills in P5.3 |
| 9 | Corporate-action storage | (a) store adjusted bars; (b) **store raw + a corporate-action table, compute adjusted on read** | **(b)** | (a) silently rewrites history on every split/dividend, destroying backtest reproducibility and creating look-ahead in re-runs |
| 10 | Retention period | (a) 3 y; (b) **7 y for records, audit trail indefinite**; (c) indefinite for everything | **(b)** | Regulatory retention minima are unverified `[VERIFY-P0.2]`; 7 y is the conservative common denominator and storage cost is negligible (Chain B) |

---

## 6. NON-BLOCKING details noticed and resolved

Per Block C, the small things that cause bugs if left implicit. Each is decided here so no later
phase has to guess.

| Area | Resolution |
|---|---|
| **Timezone at rest** | Every timestamp is tz-aware **UTC**. Exchange-local time exists only at presentation and calendar boundaries. `trading_date` is exchange-local and is a `DATE`, never a timestamp |
| **Timers** | All systemd timers are specified in UTC (ADR-02). The 09:45 ET window is 13:45 UTC in EDT and 14:45 UTC in EST — two definitions selected by calendar lookup, never one local-time timer |
| **US DST** | Two transitions/year shift the US close by one hour but never across midnight UTC, so ADR-15's UTC accounting-date mapping is safe year-round. India observes no DST |
| **US half-days** | Early close 13:00 ET. The 09:45–10:15 order window is unaffected; ingest and pipeline timers move earlier, driven by the calendar, not by a constant |
| **India special sessions** | Muhurat and other special trading sessions are **excluded** from `trading_date` sequencing and from all rolling-window counts |
| **Money type** | `Decimal`, never `float`. USD and INR quantised to 2 dp. FX rates 6 dp. Rounding **half-up**, applied only at the final step of a computation, never at intermediates |
| **Percentages** | Stored and compared as fractions (`0.05`), never as `5`. Any config key ending `_pct` is a fraction, validated to `[0, 1]` at load |
| **Limit bounds** | All risk limits are **inclusive**: `position_pct <= 0.05` passes at exactly 0.05. Breach is strictly greater |
| **Rolling windows** | Counted in **completed exchange sessions**, never calendar days. `ATR(14)` uses 14 completed bars and **excludes today's partial bar**. "20-day volume" is 20 completed sessions |
| **"Rolling 5 business days"** (PDT, Chain D) | Exchange business days for the relevant market, not calendar days, not the other market's days |
| **Price used for filters** | ADR-14's filters use the **official close** of the last completed session, unadjusted, never a live or intraday price |
| **Market cap** | Last completed close × most recent reported shares outstanding. Never intraday, never a vendor's live estimate |
| **ADDV** | 20-session **median** of (close × volume), not mean — one spike must not qualify a name |
| **Halted stocks** | Excluded from the universe on their last valid close. A halt while held is an exit-hierarchy event, not a price update |
| **Tick size** | **RESOLVED (A-11)** `[V]`. US: **$0.01** for all NMS stocks ≥ $1.00 today; the $0.005 second increment is adopted but deferred to **the first business day of November 2027**, then reassigned **per symbol, twice yearly**. Therefore a **date-versioned instrument attribute**, never a constant. India: `tick_size` and `lot_size` are fields of Zerodha's instruments dump. **US has no lot size**; fractional via `qty` or `notional`, market/day orders only |
| **Lot size / fractional** | Per-market instrument attribute. US fractional supported `[VERIFY-P0.2]`; India lot-based |
| **Order quantity rounding** | Round **down** to the tradeable increment after sizing, never up — rounding up can breach the 5% cap by construction |
| **Sign convention** | Quantities are positive; long-only (ADR-12) means no negative quantities exist in v1, and a negative quantity is a validation error, not a short |
| **Cost basis method** | **FIFO** at lot level, chosen because it is the default assumption in both jurisdictions' reporting `ASSUMPTION [VERIFY-P0.2]` and because it interacts predictably with wash-sale adjustment (Chain E) |
| **Day boundary for daily loss** | Per-pool: that exchange's session. Consolidated: the UTC accounting date, evaluated after the later close (ADR-15) |
| **Overnight gaps** | A gap counts against the session in which it is *realised* — i.e. the session that opens at the gapped price — never retroactively against the prior session |
| **Stop activation** | The protective stop is placed at the broker at entry. A same-session stop-out is possible and is accounted for by Chain D's counters rather than prevented |
| **Universe membership** | Point-in-time and immutable. Backtests select membership as of the decision date |
| **Delisted instruments** | Retained forever with the delisting event and final price. Never deleted `[RS §13]` |
| **`model_id` / `prompt_version`** | Recorded on every score, thesis and decision. Required for reproducibility (ADR-07), promotion accounting (ADR-08) and LLM cache keys (Chain G) |
| **Fiscal vs calendar quarter** | ADR-07's retrain cadence uses **calendar** quarters. Fundamentals use the issuer's fiscal periods, mapped to a calendar `as_of` date at ingest |
| **Empty-universe / no-candidate sessions** | A session producing zero candidates is a valid outcome, logged, and is **not** an error. `[RS §23]` — knowing when to stay out is a feature |

---

## 7. DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Grafana + FastAPI/CLI + Telegram; no custom frontend (ADR-01) | Three needs, zero new stack; kill switch kept independent | Yes | Low — a UI can be added at any time |
| 2 | systemd timers → containerised jobs; DB-enforced job idempotency (ADR-02) | Restart/failure/logging semantics without an orchestrator | Yes | Medium — a missed idempotency key could double-place an order list |
| 3 | No Kubernetes until three named metrics hold jointly (ADR-03) | Removes a recurring "should we migrate" debate | Yes | Low |
| 4 | Alt data = EDGAR + FRED + one news API + corporate actions; social media excluded permanently (ADR-04) | Bounded, sanitisable input set; social is the largest injection surface | Yes | Medium — an excluded source could hold real alpha |
| 5 | Equities only; ETFs read-only in v1; futures and options never (ADR-05) | Leverage and assignment are incompatible with the risk framework | Partly | Low now, High if reversed late |
| 6 | Vector DB killed; pgvector-in-Postgres is the only escape hatch (ADR-06) | Reproducibility and memory-poisoning surface, not cost | Yes | Low |
| 7 | Quarterly expanding-window retrain + 5 enumerated triggers; P&L is never a trigger (ADR-07) | Prevents reactive retraining | Yes | Medium — a stale model degrades quietly |
| 8 | Promotion proven on walk-forward OOS; live shadow detects harm only (ADR-08) | Live sample sizes cannot prove improvement — arithmetic in ADR-08 | Yes | **High** — a bad promotion protocol promotes noise into live capital |
| 9 | 12 enumerated approval actions; **no override path for a risk DENY** (ADR-09) | Keeps `[CONST-1]` real rather than decorative | Partly | **High** |
| 10 | RPO 0 for state; RTO-safe 30 min via an independent panic script; 5-part recovery definition; kill switch restored TRIPPED (ADR-10) | "Up and wrong about what it owns" is the dangerous state | Yes | **High** |
| 11 | Dual-market by contract, US-first by capital; 9 mandatory dual-market artifacts (ADR-11) | Satisfies `[CONST-10]` without paying India's operational cost early | Partly | **High** if deferred — retrofitting a currency and calendar is a rewrite |
| 12 | Long-only, cash account, no margin/borrow/leverage through v2 (ADR-12) | Removes the leverage capability rather than policing it | Partly | Medium |
| 13 | **Swing horizon: median 15 trading days, band 3–40, min 3, time-stop 40, hard max 120** (ADR-13) | Bounded below by transaction costs, above by statistical sample size | **Treat as irreversible** | **Total — the architecture is derived from it** |
| 14 | 1,500 US names, ADDV-ranked with 1,300/1,700 hysteresis, weekly reconstitution; once-per-session decisions; 20 positions at 4% target, 5% cap, ≥20% cash (ADR-14) | Fixes throughput, storage and the scanner's working set | Partly | **High** |
| 15 | USD base, segregated pools, no system FX conversion, limits enforced per-pool AND consolidated (ADR-15) | A small-pool catastrophe must not be invisible in a consolidated number | Partly | **High** |
| 16 | Backtests must simulate the kill switch; accept at DD ≤ 10% and ≤ 1 trip / 10 y (§0.3 C-3) | A 15%-DD strategy cannot exist under a 10% kill switch | Yes | **High** |
| 17 | The LLM tier is excluded from walk-forward optimisation and validated forward only (Chain G) | The model's weights contain the backtest's future | No | **High** |
| 18 | Tier-2 weights must sum to 1.0 with a test (§0.3 C-4) | The research summary's weights sum to 0.9 | Yes | Medium |
| **19** | **AD-1 — A14 replaced: ≈$129/mo paper, ≈$228/mo live verified; VM and backup unpriced; total operating cost marked INCOMPLETE** | Conflating verified recurring cost with full operating cost is how an infrastructure line disappears from a budget | Yes — on Q-1/Q-2 | Medium — a total quoted without the unpriced lines understates by an unknown amount |
| **20** | **AD-2 — walk-forward rolls fixed at 3 months, 1.5-year initial train** | 34 windows are unreachable at 6-month rolls from 10 years of purchased history; the 20-year alternative costs +$120/mo for no gain in independence | Yes | **High** — an unreachable promotion bar means nothing is ever promotable, or the bar is quietly lowered later |
| **21** | **AD-3 — the US backup broker is MANUAL-ONLY and excluded from every RTO claim** | It cannot authenticate itself unattended at the moment it is needed (P0.2 F-12) | Yes — if a broker with unattended auth replaces it | **High** — a backup believed automatic is a recovery plan that fails exactly when exercised |
| **22** | **AD-4 — broker hierarchy: Zerodha primary, Upstox automated monitoring backup, IBKR manual-only emergency** | `[CONST-10]` names Zerodha; authentication convenience is not grounds for promotion | Partly — Upstox to primary needs a `[CONST-10]` amendment | Medium — a wrong hierarchy surfaces only during an incident |
| **23** | **AD-5 — OpenAI `gpt-5.6-luna` primary, DeepSeek `deepseek-v4-flash` fallback, CONDITIONAL on M-7** | OpenAI publishes its retention and training-use terms; DeepSeek's could not be retrieved. **A Constitutional amendment**, recorded as one | **Yes — explicitly re-taken when M-7 resolves** | Medium — the margin is one criterion resting on absence of evidence, not evidence against |

---

## 8. ASSUMPTIONS

| # | Assumption | Why it had to be assumed | How to verify | Impact if false |
|---|---|---|---|---|
| A1 | US equity settlement is T+1 | Chain D's settled-cash rule depends on the cycle length | Broker/DTCC documentation | `[VERIFY-P0.2]` — a longer cycle enlarges the required cash buffer beyond ADR-14's 20% |
| A2 | PDT is a margin-account rule and does not apply to cash accounts; good-faith/free-riding rules apply instead | §0.4 R-1 corrects `[RS §16]` on this | FINRA rules + broker account agreement | `[VERIFY-P0.2]` — if PDT applies to cash accounts, Chain D's second counter becomes active in v1 |
| A3 | Alpaca supports fractional shares and $0 commission | ADR-11's India lot-size contrast and ADR-14's small-capital sizing rely on it | Alpaca docs | `[VERIFY-P0.2]` — without fractionals, the $1k capital stage is unworkable |
| A4 | Zerodha requires a daily manual login and a static IP | ADR-11's activation gate item 2 | Zerodha Kite Connect docs, SEBI circular | `[VERIFY-P0.2]` — if automatable, India activation becomes cheaper |
| A5 | India STCG 20% / LTCG 12.5% with ₹1.25 L exemption from 23 Jul 2024; STT on both delivery legs | Chain E's India cost and the ADR-11 economics argument | Income Tax Act / Finance Act 2024, a qualified professional | `[VERIFY-P0.2]` — changes India's required gross edge |
| A6 | Funding a US account from India is an LRS remittance with an annual cap and TCS | ADR-15's "no system FX conversion" and ADR-11's gate item 3 | RBI LRS master direction, a qualified professional | `[VERIFY-P0.2]` — affects capital-stage pacing only, not system design |
| A7 | India-US DTAA dividend withholding applies to US-source dividends | Post-tax reporting completeness (Chain E) | DTAA text, W-8BEN process | `[VERIFY-P0.2]` — reporting-module scope only |
| A8 | Round-trip cost ≈ 25 bps US, ≈ 90 bps India | No live fills exist yet | Recalibrate on ≥200 live fills; P5.3 | **High** — Chain F's whole argument and the minimum-edge rule scale with this |
| A9 | Half-spread 2–10 bps, impact 5–15 bps at ≤1% ADDV | Component inputs to A8 | Same as A8 | Same as A8 |
| A10 | **CLOSED by P0.2 §3.11–3.12** `[V]`. Verified: `gpt-5.6-luna` $0.20/M in, $1.20/M out (primary since AD-5); `deepseek-v4-flash` $0.22/$0.66 off-peak (fallback). `gpt-4o-mini` **does not exist** (F-8) | Chain G's cost table | Closed — P0.2 §3.11, §3.12 | Chain G's conclusion (cost is not binding) survives: live spend ≈$0.95/mo |
| A11 | ~6,000 input / ~1,500 output tokens per candidate thesis | No prompt exists yet | Measure on the first P4.3 prototype | `[VERIFY-P0.3]` — linear effect on Chain G |
| A12 | Row width ~92 B/bar; TimescaleDB compression 8–20× on numeric series | Chain B's storage table | Measure on a loaded sample | `[VERIFY-P0.3]` — Chain B's conclusion (audit-dominated, <60 GB) is robust to a 3× error |
| A13 | ~15 k audit events per session at ~1 KB | Chain B's dominant line | Measure once P1.4 exists | `[VERIFY-P0.3]` — drives disk sizing |
| A14 | **SUPERSEDED by AD-1.** Verified data + broker: **≈$129/mo paper, ≈$228/mo live** `[V]`. VM and off-VM backup **unpriced** (P0.3 Q-1, Q-2), so **total infrastructure operating cost is INCOMPLETE**, not estimated. Institutional intraday tier remains $300–2,000+ `[V]` | Chain A's cost step | P0.2 §4.3; P0.3 §8 | **Partly `[V]`, partly `[U]`** |
| A15 | RBI publishes a daily USD/INR reference rate on Indian business days | ADR-15's FX source | RBI site | `[VERIFY-P0.2]` — a fallback source is already required |
| A16 | Champion/challenger daily return correlation ρ ≈ 0.95 | ADR-08's power table | Measure on the first shadow run | Medium — a lower ρ makes Stage 2 even weaker, strengthening the decision |
| A17 | PSI > 0.25 is a reasonable drift threshold | ADR-07 T1 | Industry convention; recalibrate on observed drift | Low — tunable |
| A18 | ~200 news items/session for a 1,500-name universe | Chain B storage, Chain G token budget | Measure at P2.1 | Low |
| A19 | FIFO is the appropriate default cost-basis method in both jurisdictions | §6 | A qualified professional | `[VERIFY-P0.2]` — affects the tax module, not the trading logic |
| A20 | Reference data exposes a security-type field sufficient to exclude units/warrants/rights | ADR-14's eligibility filter | Provider schema | `[VERIFY-P0.2]` — otherwise the name-pattern guard carries the load alone |
| D1–D10 | The ten Clarifier-Rule defaults in §5 | Answers unavailable at P0.1 time | Owner confirmation | See §5's "what breaks" column |

---

## 9. OPEN QUESTIONS — the Stage 0 open-item register

**No architectural question is left open by this phase.** All fifteen ADRs are closed, and v0.2
adds five Owner decisions (§0.5.1). The register below is the **complete set of items carried
across the Stage 0 freeze**, each classified. Freezing does not close them; it forbids changing a
*decision* silently while these remain outstanding.

### 9.1 CLOSED by P0.2 / P0.3

| # | Question | Closed by | Verified value |
|---|---|---|---|
| **Q2** | Zerodha daily login; static IP | P0.2 F-4 `[V]` | `access_token` expires **06:00 IST next day** (regulatory); `refresh_token` restricted to approved platforms; static IP mandatory for **order placement** from **2026-04-01**, up to 2 IPs |
| **Q3** | Market-data tiers and prices | P0.2 §3.2–3.4, §4.3 `[V]` | Massive $0/$29/**$79**/$199; Alpaca $0/**$99**; FMP $0/$19/**$49**/$99; Finnhub $0/$3,500. Vendor renamed Massive (A-3) |
| **Q6** | DeepSeek / OpenAI prices and limits | P0.2 §3.11–3.12 `[V]` | `gpt-5.6-luna` $0.20/$1.20 per 1M; `deepseek-v4-flash` $0.22/$0.66 off-peak. DeepSeek limits by **concurrency** (2,500/500); OpenAI by RPM/TPM/RPD/TPD with `Retry-After`. Surfaced F-8 |
| **Q11** | Reference-data security-type field | P0.2 §3.3 `[V]` | Massive `/v3/reference/tickers` returns `type`, `active`, `primary_exchange`, `cik`, `delisted_utc`, and accepts `date` for point-in-time membership |
| **Tick size** | US sub-penny rules | P0.2 F-10, A-11 `[V]` | **$0.01** ≥$1.00 today; $0.005 increment deferred to **first business day of November 2027**, then per-symbol semi-annual reassignment. A **date-versioned instrument attribute** |
| **Lot size** | Lot / fractional support | P0.2 §2, A-11 `[V]` | US: **no lot size**; fractional via `qty` or `notional`, market/day only. India: `lot_size` and `tick_size` from Zerodha's instruments dump |

### 9.2 PARTIAL — the headline is verified, a detail is not

| # | Question | Verified | Outstanding |
|---|---|---|---|
| **Q1** | Alpaca fractional, commission, idempotency key, rejection codes | Fractional confirmed (market/day only); commission "0%–3%", zero is the norm not a guarantee; `client_order_id` **max 128** `[V]` | **Charset undocumented** and the granular reject-reason enumeration unpublished → **M-1**. Mitigated by self-restricting to `[A-Za-z0-9-]` ≤ 64 and treating reject reasons as opaque text |
| **Q5** | EDGAR rate limits and filing latency | **10 req/s**, declared User-Agent required; dissemination cutoffs 17:30 ET / 22:00 ET for Forms 3/4/5 `[V]` | **Propagation latency after acceptance unpublished** → **M-8**. Measure empirically over a week of Form 4s |

### 9.3 FORMERLY GATING — all three resolved 2026-08-26

The three items that gated Stage 1 sign-off were retrieved on **2026-08-26**. **None of them
changed an architectural decision**; two confirmed existing decisions were right, and one
produced an additive rule.

| # | Question | Answer, and its source | Effect |
|---|---|---|---|
| **Q4 / M-5** | **Is the news archive point-in-time?** | **NO** `[V]`. Massive/Benzinga documents `last_updated` = “when the news article was last updated in the system” against `published` = “when the news article was originally published”, with a sample record showing them differ; Alpaca documents `created_at` / `updated_at`. **Neither exposes any version, revision or as-of-content parameter.** `massive.com/docs/rest/partners/benzinga/news`, `docs.alpaca.markets/reference/news-3` | **ADR-04 unchanged** — every candidate vendor shares the property. **Rule N4 becomes evidence-based; new rule N16** makes our own store the point-in-time record. Residual materiality → **M-12**, not gating |
| **M-2** | Is **price history for delisted names** retained? | **YES** `[V]`. “our market data includes companies that have been delisted from the exchanges and is stored as it occurred on that date.” `massive.com/knowledge-base/article/what-does-massive-do-with-delisted-tickers` | **ADR-14 and invariant I7 unchanged and now vendor-supportable.** The requirement that delisted names are never deleted was already correct; it is no longer at risk |
| **M-3** | **WebSocket reconnect / replay semantics** | **No mechanism is documented** `[V]`. Two Alpaca streaming pages retrieved in full; both silent on reconnect, replay, sequence numbers and gap recovery | **Rule N5 (gap-is-lost) unchanged and confirmed correct.** An undocumented replay could only ever be an optimisation, never a correctness dependency — so this no longer gates |

### 9.4 OPEN — carried forward, not gating

| # | Question | Owner / phase | Status |
|---|---|---|---|
| **Q7 / M-6** | US T+1 settlement; cash-account good-faith / free-riding as the broker applies them | P2.9 | Requires the account agreement behind login. **Downgraded**: ADR-13 Chain D specifies both counters, so either answer is implementable |
| **Q8** | India STCG/LTCG rates; STT / stamp / exchange / GST schedule | ADR-11 activation gate | Not attempted — India is unfunded. Tax law, needs a qualified professional |
| **Q9** | LRS annual limit and TCS treatment for funding a US brokerage account | Informational | Not attempted. Needs a qualified professional |
| **Q10** | Regulatory record-retention minima (US and India) | P6.3 | Not attempted. P0.1's 7-year default stands unchallenged |
| **Q12** | RBI USD/INR reference-rate endpoint and a commercial fallback | ADR-11 activation gate | Not attempted — India unfunded; not a P0.3 blocker |
| **M-7** | **DeepSeek data-retention and training-use terms** | P4.3 / P6.2 | **AD-5 is conditional on this.** ToS host timed out; retry, or obtain from the platform console after signup |
| **M-9** | Upstox cost/idempotency/partial-fill/rejection codes; IBKR `cOID`/order-status/commissions; Zerodha SEBI retail-algo obligations | ADR-11 gate | Vendor docs deeper in each tree, plus the NSE/SEBI circulars themselves |
| **M-10** | **NEW in v0.2.** OpenAI **Batch tier turnaround time** | P4.3 | AD-5 uses the **Standard** tier for the live gate because the `TIER3_LLM` stage has a 600 s deadline and Batch turnaround is undocumented. Batch may be used for **replay** only once turnaround is verified |
| **A-14** | **Does `[CONST-6]`'s DENY apply to exposure-reducing actions?** | **P2.9, Owner** | **Not among the five decisions taken.** A literal DENY on an exit *increases* risk. P0.3 §6.3 carries the recommended wording; §13 row 27 is marked not implementable until ratified |
| **P0.3 Q-1 / Q-2** | VM and off-VM backup pricing | P6.4 | Feeds AD-1's INCOMPLETE total |
| **P0.3 Q-11** | Bare vs numbered headings for the four mandated Block B sections | Prompt-pack maintainer | P0.1 and P0.2 number them; P0.3 does not. Affects a mechanical X3 merge |
| **P0.3 Q-12** | Does the vendor emit a zero-trade 5-minute bar, or omit the window? | P3.3 | Until answered, an omitted bar counts toward the stale-bar timer unless halted — the fail-closed reading |

### 9.5 MEASUREMENT-BY-DESIGN — answerable only by running the system

These are **not** pre-implementation decisions and must never be converted into ones. Each has a
specified default that is safe until measured, and a named phase that measures it.

| # | Quantity | Default in force | Measured by |
|---|---|---|---|
| **Q13** | Round-trip transaction cost | 25 bps US / 90 bps India `ASSUMPTION` | **P5.3**, recalibrated after ≥200 **live** fills. Paper fills are excluded by rule N11 |
| **Q14** | Tokens per thesis | 6,000 in / 1,500 out `ASSUMPTION` | **P4.3**, from the `usage` object on the first 50 live gate calls (P0.3 Q-4) |
| **Q15** | Audit-event rate and row width | 15,000 events/session, ~1 KB `ASSUMPTION` | **P1.2 / P6.1**, after 20 live sessions (P0.3 Q-6). P0.3 §9.4 shows 250 GB survives a 5× miss |

---

## 10. CONTRACTS EXPORTED

Names, values and semantics that downstream phases import. A phase that needs one of these must
use the name below rather than inventing a synonym.

### 10.1 Enumerations (defined here, implemented in P1.1)

| Name | Kind | Values | Consumers |
|---|---|---|---|
| `Market` | enum | `US`, `IN` | every table, every model, every config namespace |
| `AccountType` | enum | `CASH` (v1), `MARGIN` (future) | P1.1, P2.9 |
| `InstrumentType` | enum, **deny-by-default** | `COMMON_STOCK` (allowed v1), `ETF` (read-only v1), `ADR`, `ETN`, `CEF`, `SPAC`, `UNIT`, `WARRANT`, `RIGHT`, `PREFERRED`, `FUTURE`, `OPTION` (all denied) | P1.1, P2.2, P2.9 |
| `ApproverRole` | enum | `OPERATOR`, `OWNER` | P1.4, P6.x |
| `PoolId` | identifier | one per `Market`; segregated, no cross-margining | P1.1, P2.9, P1.2 |

### 10.2 Configuration keys (defined here, schema'd in P1.3)

| Key | Value | Source |
|---|---|---|
| `holding.median_target_sessions` | `15` | ADR-13 |
| `holding.min_sessions` | `3` | ADR-13 |
| `holding.band_sessions` | `[3, 40]` | ADR-13 |
| `holding.time_stop_sessions` | `40` | ADR-13 |
| `holding.time_stop_min_return_pct` | `0.02` | ADR-13 |
| `holding.hard_max_sessions` | `120` | ADR-13 |
| `universe.US.max_instruments` | `1500` | ADR-14 |
| `universe.US.enter_rank` / `exit_rank` | `1300` / `1700` | ADR-14 |
| `universe.US.min_market_cap_usd` | `500_000_000` | `[RS §4]` |
| `universe.US.min_addv_usd` | `max(1_000_000, 100 * max_position_value)` | ADR-14 |
| `universe.US.min_price_usd` | `5.00` | `[RS §4]` |
| `universe.US.min_sessions_history` | `250` | ADR-14 |
| `universe.US.min_reported_quarters` | `4` | ADR-14 |
| `universe.IN.max_instruments` | `500` | ADR-14 |
| `universe.reconstitution_cron_utc` | `Sat 06:00` | ADR-14 |
| `portfolio.target_positions` / `band` | `20` / `[15, 25]` | ADR-14 |
| `portfolio.target_weight_pct` | `0.040` | ADR-14 |
| `portfolio.max_position_pct` | `0.050` | `[CONST]` |
| `portfolio.forced_trim_pct` | `0.075` | ADR-14 |
| `portfolio.min_cash_pct` | `0.20` | ADR-14 |
| `turnover.max_new_entries_per_session` | `4` | ADR-14 |
| `turnover.max_nav_traded_pct_per_session` | `0.20` | ADR-14 |
| `decision.min_edge_multiple_of_cost` | `2.0` | ADR-13 Chain F, `[DEFAULT-8]` |
| `cost.assumed_round_trip_bps.US` / `.IN` | `25` / `90` | ADR-13 Chain F `ASSUMPTION` |
| `schedule.US.ingest_utc` / `pipeline_utc` | `21:45` / `22:30` | ADR-02, ADR-14 |
| `schedule.US.order_window_et` | `09:45–10:15` | ADR-14 |
| `fx.base_currency` | `USD` | ADR-15 |
| `fx.source_primary` | `RBI_REFERENCE` | ADR-15 `ASSUMPTION` |
| `fx.system_may_convert` | `false` — **immutable** | ADR-15 |
| `risk.evaluate_per_pool` / `risk.evaluate_consolidated` | `true` / `true` | ADR-15 |
| `retrain.schedule` | `quarterly_expanding_window` | ADR-07 |
| `retrain.triggers` | `[PSI_GT_0_25, IC_BELOW_CI, UNIVERSE_SHOCK_GT_15PCT, SCHEMA_BREAK, REGIME_UNDERREPRESENTED]` | ADR-07 |
| `promotion.min_wf_windows` / `min_closed_trades` | `34` / `1000` | ADR-08 |
| `promotion.shadow_min_sessions` | `60` | ADR-08 |
| `promotion.dsr_threshold` | `0.95` | ADR-08 |
| `hitl.actions` | the 12 rows of ADR-09 | ADR-09 |
| `hitl.risk_deny_override_permitted` | `false` — **immutable, no code path exists** | ADR-09 |
| `dr.rpo_state_seconds` / `dr.rto_safe_minutes` / `dr.rto_operational_hours` | `0` / `30` / `4` | ADR-10 |
| `dr.restore_drill_cadence` | `monthly` | ADR-10 |
| `killswitch.restore_state_on_boot` | `TRIPPED` — **immutable** | ADR-10 |
| `llm.monthly_spend_alarm_usd` | `50` | ADR-13 Chain G |
| `llm.gate_width` | `15` | ADR-13 Chain G |
| `llm.may_receive_portfolio_state` | `false` — **immutable** | `[DEFAULT-7]` |
| `audit.retention_years` / `records.retention_years` | `indefinite` / `7` | `[DEFAULT-10]` |
| `promotion.walkforward_roll_months` | `3` | **AD-2** |
| `promotion.walkforward_initial_train_years` | `1.5` | **AD-2** |
| `llm.primary_provider` / `llm.primary_model_id` | `OPENAI` / `gpt-5.6-luna` | **AD-5** |
| `llm.fallback_provider` / `llm.fallback_model_id` | `DEEPSEEK` / `deepseek-v4-flash` | **AD-5** |
| `llm.primary_conditional_on` | `"M-7"` — re-scored when M-7 resolves | **AD-5** |
| `llm.live_path_tier` | `STANDARD` — **never `BATCH`** until M-10 closes | **AD-5** |
| `broker.IN.primary` | `ZERODHA` | **AD-4**, `[CONST-10]` |
| `broker.IN.monitoring_backup` | `UPSTOX` (read-only via `extended_token`) | **AD-4** |
| `broker.US.emergency_backup` | `IBKR` | **AD-4** |
| `broker.emergency_backup_is_manual_only` | `true` — **immutable** | **AD-3** |
| `broker.emergency_backup_counts_toward_rto` | `false` — **immutable** | **AD-3** |
| `cost.verified_monthly_usd.paper` / `.live` | `129` / `228` | **AD-1** |
| `cost.vm_monthly_usd` / `cost.backup_monthly_usd` | `null` — unpriced, P0.3 Q-1 / Q-2 | **AD-1** |
| `cost.total_operating_is_complete` | `false` until Q-1 and Q-2 resolve | **AD-1** |

### 10.3 Invariants downstream phases must enforce (not merely honour)

| # | Invariant | Enforced in |
|---|---|---|
| I1 | No code path converts currency. `Money` arithmetic across currencies raises | P1.1, P2.9 |
| I2 | No code path overrides a risk DENY | P2.9, P1.4 |
| I3 | Kill-switch state on boot is `TRIPPED`, unconditionally | P2.10 |
| I4 | Risk counters are replayed from the audit trail, never recomputed from portfolio state | P2.10, P1.4 |
| I5 | `InstrumentType` not on the allowlist → DENY | P2.9 |
| I6 | Every order carries `strategy_version`, `model_id` and a broker idempotency key | P3.2 |
| I7 | Universe membership is point-in-time immutable; delisted names are never deleted | P1.2, P5.1 |
| I8 | Every backtest simulates the kill switch | P5.1, P5.2 |
| I9 | LLM-derived features never enter walk-forward optimisation | P5.1, P5.2, P4.3 |
| I10 | A missing FX rate blocks new entries in **both** pools | P2.9, P2.1 |

---

## 11. Acceptance self-check

Verified against the deliverable as written, not against intent.

| Acceptance criterion (from the issue) | Result | Verification |
|---|---|---|
| All 15 ADRs written, none left as "TBD" | **PASS** | §3 contains ADR-01…ADR-15, each with Title, Status, Context, ≥3 costed options, Decision, Consequences, revisit triggers, owner and date. §9 confirms no architectural question is left open; the OPEN QUESTIONS table holds only external verification queries assigned to P0.2/P0.3 as the prompt pack's stage map already requires |
| Q13 second-order effect chains stated, not just the decision | **PASS** | ADR-13 carries nine explicit chains, A–I, covering data frequency, storage volume, order flow, PDT/settlement, tax, slippage and minimum edge, LLM cost and affordability, thesis shelf life, and an architecture-viability summary — each terminating in the downstream specs it constrains |
| A one-page "decisions that constrain everything else" summary | **PASS** | §1, an 18-row table, each row naming the binding value and why other work bends around it |
| Every ADR names a decision owner and a date | **PASS** | Every ADR header in §3 carries `Owner: JS — Project Owner (role)` and `Date: 2026-08-23` |
| ≥3 options costed per ADR | **PASS** | Every ADR has a 3–5 row options table with Dev / Run / Ops / Cx columns as defined at the head of §3 |
| Output Contract's four mandatory tables | **PASS** | §7 DECISIONS MADE, §8 ASSUMPTIONS, §9 OPEN QUESTIONS, §10 CONTRACTS EXPORTED |
| Clarifier Rule applied | **PASS** | §5 lists 10 blocking questions with options, applied defaults and failure impact; §6 lists 27 non-blocking details resolved; `[DEFAULT-n]` markers appear inline throughout |
| Upstream defects reported | **PASS** | §0.3 (four conflicts) and §0.4 (three corrections), as Block A requires |
| No placeholders anywhere | **PASS** | Verified by text search — no `TBD`, `TODO`, `to be decided`, `pending`, `unknown` or `future decision` appears as an unresolved marker in any ADR |

---

**END OF SPEC-P0.1-DECISIONS v0.1**
