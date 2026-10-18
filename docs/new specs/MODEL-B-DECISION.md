---
id: MODEL-B-DECISION
version: 0.3
status: DRAFT
phase: Owner decision on the product operating model (end of Stage 0)
depends_on: [SPEC-A-CONSTITUTION v0.3, SPEC-P0.1-DECISIONS v0.1, SPEC-P0.2-PROVIDERS v0.1, SPEC-P0.3-BUDGET v0.1, STAGE-0-OWNER-DECISIONS v0.1, SCOPE-MULTI-USER v0.1]
produces: [MB-1..MB-10, MB-AC-1..MB-AC-16, BA-1..BA-6, MB-RQ-1..MB-RQ-6, MB-IMP-*, PublicationSwitch, PublicationSwitchSet]
---

# Owner decision: Model B — signals only for v1

Date: 2026-10-14. Decision owner: Owner. Recorded by the implementer.

Version history: 0.1 (2026-10-14) decision recorded. 0.2 (2026-10-17) Block B conformance pass:
section 9 gives the per-market publication switch (MB-5, MB-AC-10), the one entity this file
defines, a Pydantic v2 model, a field table and enumerated error paths; MB-D-11, MBA-4 and two
contracts added. No rule, criterion or amendment changes. 0.3 (2026-10-17) Block C conformance
pass: section 10 (problems found in this file), section 11 (ten blocking questions, BQ-31 to
BQ-40, with [DEFAULT-42] to [DEFAULT-51]), section 12 (an edge case for every rule), section 13
(non-blocking details); the defaults are listed in ASSUMPTIONS. No rule, criterion or amendment
changes; the defaults fill gaps the rules leave open. Sections 2 and 4 carry inline [DEFAULT-n]
marks where a default narrows them.

**Owner's decision, verbatim summary:** "I choose Model B: Signals-only for v1. The
AI-Trading-Agent v1 will provide research, strategy validation, backtesting, and trading signals
where legally permitted. Users will make their own trading decisions and place orders themselves
through their chosen broker." Eight requirements followed; they are rules MB-1 to MB-8 below.

This file answers OWQ-4 of `STAGE-0-OWNER-DECISIONS.md`. It does not edit any earlier record. Each
earlier spec carries a dated notice pointing here; its decided text is unchanged and is superseded
only where section 6 says so.

Nothing in this file is legal advice. Regulatory statements carry their source and how it was
read; a qualified adviser must confirm them before any jurisdiction-specific feature is enabled
(MB-5).

## 1. The decision and its rules

| # | Rule | Source |
|---|------|--------|
| MB-1 | v1 contains **no** broker order routing, no automated order placement and no autonomous trade execution. No component of v1 can submit, modify or cancel an order at any broker. | Owner requirement 1 |
| MB-2 | v1 never collects, holds, moves or controls any user's money or securities, and never stores a user's broker credentials. | Owner requirement 2 |
| MB-3 | Research, backtesting, signal generation and any future execution are separate components with enforced boundaries (section 4). | Owner requirement 3 |
| MB-4 | Signals-only operation is **not** assumed to remove any registration, licensing or other obligation. | Owner requirement 4 |
| MB-5 | No feature that publishes signals to users in a jurisdiction is enabled until that jurisdiction's requirements (section 3) are assessed and confirmed by qualified legal review. Each such feature has its own per-jurisdiction switch, off by default. | Owner requirement 5 |
| MB-6 | This decision, its rationale, scope and acceptance criteria are recorded in `docs/new specs/` (this file and `ROADMAP-V1.md`). | Owner requirement 6 |
| MB-7 | Dependent specifications are updated by dated notices and by the next version of each spec; historical specifications and approved decisions are never rewritten. | Owner requirement 7 |
| MB-8 | Broker integration and order routing are out of scope for v1. Model A may return only through a separately approved future phase after regulatory, broker, security and cost assessment. | Owner requirement 8 |
| MB-9 | A signal is published to users only after the same deterministic controls that Block A applies to an order: a written audit record first (INV-5), the deterministic risk gate (INV-1), fail-closed on missing or stale inputs (INV-6), and a kill switch that stops publication (INV-7). An LLM never issues a published signal without the deterministic gate downstream (INV-2). | Block A carried over (section 5) |
| MB-10 | Signals are **impersonal**: the same signal goes to every user of a plan; nothing is tailored to an individual's finances, goals or portfolio. Personalisation is out of scope for v1 because it is investment-advice territory in both markets (section 3). | Section 3 |

### Rationale

- Removing execution removes the highest-impact failure modes of the design: duplicate or
  runaway orders, a kill switch that cannot reach a broker, a GTT that does not fill, unsettled
  cash used as borrowing (X3 MM-03, MM-04, MM-09, MM-10 all concern execution).
- It removes the India-specific execution regime (exchange empanelment, Algo IDs, static IPs,
  daily broker login) from v1.
- It does not remove regulation: publishing recommendations is itself regulated in both markets.
- Research, backtesting and the deterministic decision pipeline that Stages 2 and 5 build are
  needed by both models, so no work in those stages is wasted if Model A returns.

## 2. Scope boundaries for v1

| In scope | Out of scope for v1 |
|----------|--------------------|
| Market and reference data ingestion, validation, features, scoring, regime (Stage 2 up to P2.7) | Any broker API client used to trade; order, fill, position-at-broker objects in the live path |
| Gated LLM research with untrusted-content defences (Stage 4) | Storing users' broker credentials, API keys or account numbers |
| Backtesting, walk-forward, cost models used to validate strategies (Stage 5) | Handling user funds, payments for securities, pooling |
| A **model portfolio**: a published, versioned set of recommended holdings and weights per strategy and market, with entry, exit and stop levels ([DEFAULT-43], [DEFAULT-46]) | Personalised advice based on a user's own finances (MB-10) |
| Signal publication to registered users through the service, with mandatory disclosures | Copy-trading, one-click trading, deep links that pre-fill orders at a broker |
| Track record of every published signal, computed from market data, never from users' fills | Cross-border use (SC-6) |
| Per-jurisdiction publication switches, off by default (MB-5) | Short selling, derivatives, intraday signals (unchanged Stage 0 decisions) |

The Owner's own trading is outside the system in v1: the system does not trade for anyone,
including the Owner. See MB-RQ-4 for the restriction this may create.

## 3. Regulatory assessment (to be confirmed by qualified legal review)

Read on 2026-10-14. "Primary extract" means the regulator's or court's own page was seen through
an automated excerpt, not read in full; "secondary" means a law firm or other publication.

### 3.1 India

| # | Finding | Source and level |
|---|---------|------------------|
| IN-1 | No person may act as, or hold itself out as, a research analyst without SEBI registration unless exempt. Providing research services, **including buy/sell/hold recommendations on a security based on any methodology** (technical analysis is not exempt), is within the RA Regulations. | SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/105, 2025-07-23, FAQs 5 and 8 — primary extract (sebi.gov.in PDF) |
| IN-2 | Since the SEBI (Research Analysts) Amendment Regulations of 2024-12-16 and the guidelines of 2025-01-08: a research analyst using AI tools is solely responsible for the security, confidentiality and integrity of client data and must disclose to clients the extent to which AI tools are used. | Guidelines circular SEBI/HO/MIRSD/MIRSD-PoD-1/P/CIR/2025/004 (2025-01-08) as summarised by sarthaklaw.com and Lexology (Lakshmikumaran & Sridharan) — secondary |
| IN-3 | Obligations include qualification and NISM certification, a deposit linked to client numbers, client KYC for fee-paying clients, disclosure of terms and consent, a functional website with specified details, an annual compliance audit, records kept 5 years, and documented rationale for every recommendation. | Same sources — secondary |
| IN-4 | Independent and part-time analysts, employed analysts and their associates may not trade a security they recommend or follow from 30 days before to 5 days after a report, nor trade against their own recommendation. | SEBI FAQ 26 (2025-07-23) — primary extract |
| IN-5 | Research is normally non-personalised; advice based on an individual's circumstances falls under the Investment Advisers Regulations instead. Model portfolios offered by an RA follow separate SEBI guidelines. Fee limits apply to individual and HUF clients (a figure of INR 1,51,000 per family per year is reported). | algotest.in (secondary); fee figure not verified at SEBI |
| IN-6 | Registration applications go through BSE as the Research Analyst Administration and Supervisory Body. | SEBI FAQ 13 — primary extract |

**Implication:** publishing v1 signals to users in India is expected to require SEBI Research
Analyst registration of the provider (an individual or a research entity), regardless of whether
the service charges a fee directly. Whether a free tier changes this is a question for counsel
(IN-1 refers to "consideration"; the FAQ also applies obligations to non-fee-paying clients).

### 3.2 United States

| # | Finding | Source and level |
|---|---------|------------------|
| US-1 | The Investment Advisers Act defines an investment adviser broadly and excludes "the publisher of any bona fide newspaper, news magazine or business or financial publication of general and regular circulation". The Supreme Court held that a publisher of impersonal, non-personalised advice in a publication of general and regular circulation falls within this exclusion. | Lowe v. SEC, 472 U.S. 181 (1985) — primary extract (justia.com) |
| US-2 | Whether timed, security-specific trading signals delivered to subscribers qualify as a "bona fide publication of general and regular circulation" is fact-dependent; signals timed to market events are a known weak point of the exclusion. | **Not verified**; counsel required |
| US-3 | An adviser that does not qualify for the exclusion registers with one or more states or, if eligible, with the SEC. The SEC's internet adviser exemption (amended 2024-03-27) requires an operational interactive website through which all advice is given; advisers no longer eligible had to move to state registration by 2025-06-29. | SEC press release 2024-42 — primary extract |
| US-4 | Anti-fraud provisions apply to publishers and advisers alike (scalping: trading ahead of one's own recommendations). | Lowe v. SEC discussion — primary extract |

**Implication:** for US users, v1 either fits the publisher exclusion (impersonal, regular, not
timed to the individual) or registers as an adviser. MB-10 keeps the design inside the
impersonal shape; counsel decides which route applies.

### 3.3 Both markets

| # | Finding | Status |
|---|---------|--------|
| BO-1 | Market-data licences that permit individual use do not cover a commercial service that publishes signals derived from the data to other people. P0.2 records Massive's plans as "individual use" (P0.2 F-48) and Finnhub's as "Personal Use" (F-53); FMP requires a separate agreement for display or redistribution (F-54). | Facts from P0.2 (extract level); the consequence for Model B is an **ASSUMPTION** until each vendor confirms |
| BO-2 | Users' personal data falls under data-protection law (India: Digital Personal Data Protection Act 2023; US: state laws). | **ASSUMPTION**, not verified |

## 4. Architecture: separation of research, backtest, signals and execution

| Package (under `v2/`, OWD-6) | Contains | May import | Must not import |
|------------------------------|----------|------------|-----------------|
| `v2/research` | data ingestion, validation, features, scoring, regime, LLM research | stdlib, stack libraries | `v2/signals`, `v2/execution`, any broker SDK |
| `v2/backtest` | event-driven simulator, simulated broker, walk-forward, cost model | `v2/research`, `v2/signals/core` [DEFAULT-51] | `v2/signals/publish` and any other `v2/signals` code, `v2/execution`, any broker SDK |
| `v2/signals` | decision engine output to signal, signal risk gate, model portfolio, audit, publication, kill switch, disclosures; gate and portfolio in the pure `v2/signals/core` [DEFAULT-51] | `v2/research` | `v2/execution`, any broker SDK |
| `v2/execution` | **does not exist in v1** | — | — |

Enforcement (to be built in the first code phase and P6.4):

- An import-boundary check in CI fails the build on any forbidden import above.
- A dependency check fails the build if a broker trading SDK (`kiteconnect`, `alpaca-py` trading
  client, `ib_insync` or any successor) appears in the v1 dependency set. Broker **data** APIs used
  for market data, if any are selected by the P0.2 re-run, are wrapped in `v2/research` with
  read-only endpoints only and the check whitelists exactly those. [DEFAULT-50] narrows this: no broker
  SDK at all, only a read-only HTTP client with a path allowlist (section 11, MB-P6).
- A test asserts that no v1 module defines a function that calls a broker order endpoint.

## 5. Conflicts with approved requirements, and how they are resolved

Block A says: "If your work conflicts with one, stop and say so explicitly rather than quietly
working around it." These are the conflicts. None stops the Owner's decision; each is resolved by a
proposed amendment that takes effect when the Owner approves this file. Block A's text in
`CONSTITUTION.md` is not edited.

| # | Block A item | Conflict with Model B | Proposed amendment |
|---|--------------|-----------------------|--------------------|
| BA-1 | INV-9 (SEBI algo circular: strategy ID per order, OPS caps, static IP, live-like testing; US PDT, wash sale, best execution) | These govern order execution. v1 sends no orders, so none applies to v1; v1's obligations are the RA Regulations (India) and the Advisers Act or its publisher exclusion (US). | INV-9 for v1 reads: "Compliance is built in from day one: SEBI Research Analyst Regulations (as amended 2024) for India; the Investment Advisers Act and its publisher exclusion, or adviser registration, for the US. The execution-side items (algo circular, OPS, static IP, PDT, wash sale, best execution) return with any future execution phase." |
| BA-2 | INV-10 (US broker Alpaca, India broker Zerodha Kite) | No broker is integrated in v1 (MB-8). | INV-10 for v1 keeps the two markets and the rule "nothing may be US-only by accident"; the named brokers are deferred to the future execution phase. |
| BA-3 | INV-7 (kill switch independent of the AI path, human re-enable) | There are no orders to stop. | The kill switch stops **publication**: no signal leaves the system while it is tripped; human re-enable unchanged. |
| BA-4 | HARD RISK NUMBERS (per order and per account) | There are no orders or accounts. | They apply to the **model portfolio**: position at most 5% of model NAV, sector at most 20%, gross at most 1x (long-only, BA-5), daily, weekly and drawdown limits measured on the model portfolio's marked value, risk per position 1%, stop at entry minus 2.5 x ATR(14), liquidity cap 1% of ADDV. The per-minute order limits do not apply to v1. |
| BA-5 | "gross <= 2x equity" default | Already unreachable under long-only (P0.1 ADR-12). | Unchanged; recorded for completeness. |
| BA-6 | Fixed stack: "DeepSeek (primary) + GPT-4o-mini (fallback)" | No conflict with Model B. Note: SEBI's RA guidelines require disclosure of AI use to clients (IN-2). | No amendment; P4.3 and the disclosures phase must state AI use. |

## 6. Impact on the Stage 0 specifications (MB-IMP)

Status meanings: **Kept** (unchanged), **Adapted** (kept with the change stated), **Deferred**
(out of v1; returns only with a future execution phase), **Re-run** (the phase must be run again
under Model B).

| Item | Status | Note |
|------|--------|------|
| CONSTITUTION INV-1 to INV-8 | Kept / Adapted | Adapted per BA-3, BA-4; INV-9, INV-10 per BA-1, BA-2 |
| CONSTITUTION Q1 (DENY and exits), Q3 (kill switch on one VM, resting stops), Q4 (order spacing), Q5 (India login), C-4, C-5, C-6 | Deferred | All concern orders or broker sessions |
| P0.1 ADR-01 Operator surface | **Re-run** | Users now need a signal delivery surface; ADR-01 covered only the operator |
| P0.1 ADR-02 to ADR-08 | Kept | Retrain, champion/challenger, scheduling, no K8s, no alt data, common stock, no vector DB |
| P0.1 ADR-09 Human approvals | Adapted | Broker items (HITL-7 India login, HITL-8 broker differences, HITL-10 transfers, HITL-11) deferred; add approval of each strategy before publication and of each change to published logic (IN-1/IN-3 research-report duty) |
| P0.1 ADR-10 Disaster recovery | Adapted | "Recovered" no longer involves broker reconciliation (REC-3, REC-4 deferred); the audit trail of published signals is the record of truth |
| P0.1 ADR-11 Markets | Adapted | Both markets; go-live per market by MB-5 and OWD-5, not "India first" |
| P0.1 ADR-12 Long-only | Kept | Settled-cash rule (AMD-4) deferred: there is no account |
| P0.1 ADR-13 Swing, daily bars | Kept | HP-2 to HP-4 become signal timing rules (published after the close for the next session); AMD-1 (late fills) deferred |
| P0.1 ADR-14 Universe | Kept | AMD-12 (order spacing) deferred |
| P0.1 ADR-15 Currency | Adapted | Model portfolio per market in its own currency; no user accounts |
| P0.2 broker sections (Alpaca Trading, Kite trading, Upstox, IBKR; SEL-1, SEL-2; PE paths for orders; THR for orders) | Deferred | MB-8 |
| P0.2 data selections (SEL-3 to SEL-19) | **Re-run** | Licences must permit commercial use and publication of derived signals (BO-1) |
| P0.3 budget | **Re-run** | Data licence costs change (BO-1); Kite Connect, recovery static IP and order-path stages are not needed; a user-facing delivery service is added |
| STAGE-0-OWNER-DECISIONS OWD-2 | Adapted | "Exits" become exit signals; with no orders, the rule is: no signal is published without an audit record and the risk gate |
| STAGE-0-OWNER-DECISIONS AMD-1, AMD-4, AMD-5, AMD-10, AMD-12, AMD-14 | Deferred | Execution-side |
| SCOPE-MULTI-USER SC-2, SC-3, SC-8 | Superseded by MB-1, MB-2 and section 3 | See its version 0.2 |

## 7. Acceptance criteria for v1 (MB-AC)

Each is testable; the owning phase writes the test.

| # | Criterion | Verified by |
|---|-----------|-------------|
| MB-AC-1 | The v1 dependency set contains no broker trading SDK; CI fails if one is added. | Dependency check (P6.4) |
| MB-AC-2 | No v1 module calls any broker order, modify or cancel endpoint; a static test enumerates network calls. | Test in first code phase; X2 review |
| MB-AC-3 | The import boundaries of section 4 are enforced in CI. | Import check (P6.4) |
| MB-AC-4 | No table, model or log field stores a user's broker credential, account number, balance or holdings. | Schema review (P1.2); test |
| MB-AC-5 | Every published signal has an audit record written before publication, with inputs, model and config versions, the risk-gate verdict and its rationale; publication fails if the write fails. | P1.4, P2.9 tests |
| MB-AC-6 | Every published signal passes the deterministic risk gate against the model portfolio; any missing or stale input denies publication. | P2.9 boundary and property tests |
| MB-AC-7 | No LLM output is published without the deterministic gate; LLM content shown to users is labelled as AI-generated. | P4.4, delivery phase |
| MB-AC-8 | The publication kill switch stops all signal delivery within the stated deadline and needs a human to re-enable. | P2.10 chaos test |
| MB-AC-9 | Signals are identical for every user of a plan; no input describing an individual user's finances reaches the signal pipeline. | Schema review; test |
| MB-AC-10 | Each jurisdiction has a publication switch, off by default; turning it on requires a recorded approval naming the legal review. | Config (P1.3); approval record (P1.4) |
| MB-AC-11 | Every signal shown to a user carries the disclosures required for that jurisdiction (registration status, AI use, risk), as confirmed by counsel. | Delivery phase; P6.3 |
| MB-AC-12 | The track record of every published signal is computed from market data, kept at least 5 years, and never edited; corrections are appended. | P1.2, P1.4, P6.3 |
| MB-AC-13 | Performance shown to users comes only from licensed point-in-time data or live published signals, labelled as such; never from biased or synthetic data (OWD-5). | P5.1, P5.2, delivery phase |
| MB-AC-14 | Data used to produce published signals is covered by a licence that permits that use (BO-1). | P0.2 re-run; P6.3 |
| MB-AC-15 | User personal data is minimised, encrypted at rest and in transit, and isolated per user. | P6.2 |
| MB-AC-16 | The Model A boundary holds: re-adding execution requires a new approved phase; no feature flag or config value can enable order placement in v1. | Review at X2 and X4 |

## 8. Questions only the Owner can answer (MB-RQ)

These are legal or business decisions. None blocks Stage 0 re-runs or Stage 1 specification work;
each blocks the item named.

| # | Question | Blocks |
|---|----------|--------|
| MB-RQ-1 | Who will hold SEBI Research Analyst registration: you as an individual, or a company (research entity)? | Publishing to Indian users |
| MB-RQ-2 | For US users: will counsel be asked whether the service fits the publisher exclusion, and if not, will you register as an investment adviser (state or SEC)? | Publishing to US users |
| MB-RQ-3 | Will the service be paid, free, or both? (Affects RA obligations, deposits and fee limits.) | Delivery phase; P0.3 re-run |
| MB-RQ-4 | You planned to test on your own account (SC-7). If you or an associate are the registered analyst, trading recommended securities is restricted (IN-4). Will you keep your personal trading entirely separate from the signals? | Your own trading once registered |
| MB-RQ-5 | Which delivery channels: web app, email, mobile notifications, an API for users? | Delivery phase |
| MB-RQ-6 | Budget for commercial data licences, which are typically far above individual plans (BO-1). | P0.2 and P0.3 re-runs |

## 9. Typed form of the publication switch

MB-5 and MB-AC-10 require one publication switch per market, off by default, turned on only with a
recorded legal-review approval. The `publication` configuration section holds one
`PublicationSwitchSet`; the config key `publication.enabled.<market>` is read as
`PublicationSwitchSet.is_enabled(market)`. `Market` is the enum exported by
`SPEC-P0.1-DECISIONS.md` (`US`, `IN`).

```python
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, model_validator


class PublicationSwitch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    market: Market
    enabled: StrictBool
    legal_review_ref: Annotated[str, Field(min_length=1, max_length=200)] | None
    approval_audit_id: UUID | None
    approved_at_utc: AwareDatetime | None

    @model_validator(mode="after")
    def _approval_matches_state(self) -> "PublicationSwitch":
        approval = (self.legal_review_ref, self.approval_audit_id, self.approved_at_utc)
        if self.enabled and any(value is None for value in approval):
            raise ValueError("an enabled switch needs legal_review_ref, approval_audit_id and approved_at_utc")
        if not self.enabled and any(value is not None for value in approval):
            raise ValueError("a disabled switch carries no approval fields")
        if self.approved_at_utc is not None and self.approved_at_utc.utcoffset() != timedelta(0):
            raise ValueError("approved_at_utc must be in UTC")
        return self


class PublicationSwitchSet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    switches: tuple[PublicationSwitch, ...]

    @model_validator(mode="after")
    def _one_switch_per_market(self) -> "PublicationSwitchSet":
        if sorted(switch.market for switch in self.switches) != sorted(Market):
            raise ValueError("exactly one switch per market is required")
        return self

    def is_enabled(self, market: Market) -> bool:
        return next(switch.enabled for switch in self.switches if switch.market is market)
```

| Field | Type | Unit | Timezone | Nullable | Valid range | Violation means |
|-------|------|------|----------|----------|-------------|-----------------|
| `market` | `Market` | none | n/a | no | `US` or `IN`; each exactly once in the set | The whole set is rejected (MB-E2, MB-E3) |
| `enabled` | `bool` (strict) | none | n/a | no | `true` or `false`; strings and integers are refused | The whole set is rejected (MB-E2) |
| `legal_review_ref` | `str` | none | n/a | yes; null exactly when `enabled` is `false` | 1 to 200 characters identifying the written legal review for this market | The whole set is rejected (MB-E2) |
| `approval_audit_id` | `UUID` | none | n/a | yes; null exactly when `enabled` is `false` | Identifier of an approval record in the audit trail (P1.4) that names this market and this `legal_review_ref` | Rejected at load (MB-E2) or at the audit check (MB-E4) |
| `approved_at_utc` | aware `datetime` | instant | UTC (offset zero) | yes; null exactly when `enabled` is `false` | Not later than the load time | Rejected at load (MB-E2, MB-E5) |
| `switches` | `tuple[PublicationSwitch, ...]` | none | n/a | no | Exactly one entry for each `Market` member, so both markets are always stated (INV-10) | The whole set is rejected (MB-E3) |

### 9.1 Error paths

Every path leaves publication off. A rejected set never falls back to a previous set, a partial
set or a default.

| # | Condition | Fail-closed behaviour |
|---|-----------|-----------------------|
| MB-E1 | The `publication` section is missing or the configuration cannot be read | No set is loaded; no signal is published in any market |
| MB-E2 | Any field fails validation, including an enabled switch without its approval fields or a disabled switch with them | The whole set is rejected; no signal is published in any market; the operator is alerted |
| MB-E3 | A market is missing from the set or appears twice | As MB-E2 |
| MB-E4 | `approval_audit_id` does not resolve to an approval record that names this market and this `legal_review_ref`, or the audit trail cannot be read to check it | As MB-E2; the P1.3 loader does this check against P1.4 at every load |
| MB-E5 | `approved_at_utc` is later than the load time | As MB-E2 |
| MB-E6 | A switch is turned on at run time without a new approval record | The change is refused; the switch stays off |
| MB-E7 | A switch is turned off and the audit write for that change fails | The change is not recorded. No signal can be published meanwhile, because publication itself needs an audit write first (MB-AC-5). The general rule for a safety stop while the audit store is down is constitution conflict C-1, owned by P2.10 |
| MB-E8 | The publication kill switch is tripped (BA-3) | No signal is published in any market, whatever the switches say; the kill switch takes precedence |

## 10. Problems found in this file

Block A requires these to be called out. Each is resolved provisionally in section 11 or 13.

| # | Where | Problem | Resolution |
|---|-------|---------|------------|
| MB-P1 | MB-2 vs MB-RQ-3 | MB-2 says v1 never collects any user's money; MB-RQ-3 contemplates a paid service. A subscription fee is money collected from a user. | MB-2 is read as Owner requirement 2 states it: no user **investment** funds or securities. Subscription fees are collected only through a payment processor's hosted page; no card or bank detail reaches our systems (section 12, MB-2). |
| MB-P2 | MB-AC-8 | "Within the stated deadline": no deadline is stated anywhere. | Non-blocking detail ND-6 (section 13); P2.10 confirms the number. |
| MB-P3 | BA-4 | Block A's "limit orders default, market only for emergency exit" is not mentioned. With no orders it cannot apply, but the track record still needs a fill convention, or it can show prices nobody could get. | [DEFAULT-45]. |
| MB-P4 | BA-4 | "Liquidity cap 1% of ADDV" needs a position size in money. A model portfolio's NAV is a number we choose, so the cap means nothing until that number is fixed; and the real flow is the sum of every follower's orders, which the system never sees. | Section 12, BA-4 rows; P2.8 fixes the notional NAV. |
| MB-P5 | Section 4 | `v2/backtest` must not import `v2/signals`, yet backtest-to-live parity needs the same risk gate and model-portfolio accounting, which section 4 places in `v2/signals`. | [DEFAULT-51]. |
| MB-P6 | Section 4 | Broker data APIs "wrapped in `v2/research`" and a dependency check that bans `kiteconnect` and the `alpaca-py` trading client cannot both hold if the wrapper uses the broker's SDK: both SDKs ship order functions. | [DEFAULT-50]. |
| MB-P7 | BA-3 | The kill switch stops all publication, exit signals included. Followers holding a position would get no exit signal while it is tripped. | [DEFAULT-47]: every entry signal carries its stop, so followers have the exit level before any trip. |

## 11. Blocking questions and the defaults used

Numbering continues from P0.3 (BQ-30, [DEFAULT-41]). Work proceeds on each default; each is
provisional and the owning phase confirms or replaces it.

| # | Question | Options | Default used | If the default is wrong |
|---|----------|---------|--------------|-------------------------|
| BQ-31 | Is a publication switch keyed by the market of the instrument or by the jurisdiction of the user? | (a) instrument market only; (b) user residence only; (c) both must match | [DEFAULT-42] (c). A signal on an instrument of market M is delivered only to a user whose declared residence is M's jurisdiction (India for `IN`, the US for `US`), and only while M's switch is on. This is SC-6 (no cross-border use) applied to delivery. | Under (a), Indian residents receive US-stock signals with no review of whether SEBI's RA rules or US rules govern that; under (c) wrongly, the service only loses reach. |
| BQ-32 | What does one published signal contain? | (a) instrument and action only; (b) instrument, action, reference price, stop level, model-portfolio weight and a deterministic rationale; (c) (b) plus target price and expected return | [DEFAULT-43] (b). Action is `ENTER` or `EXIT`. The rationale is generated from the decision engine's recorded inputs by fixed templates, not by an LLM; any LLM text shown beside it is labelled (MB-AC-7). No target price, no expected return, no limit price. | (a) cannot be audited against IN-3's "documented rationale"; (c) publishes projections whose disclosure rules have not been read. If counsel requires a target, a field is added in a new version. |
| BQ-33 | When are signals released, and may plans differ in timing? | (a) one batch per market per session after the close; (b) continuous during the session; plans may or may not get different release times | [DEFAULT-44] (a). One batch per market per session, released when the decision cycle completes and no later than session close + 21,600 s (the cycle deadline of P0.3 [DEFAULT-38]). A batch not released by then is withheld for that session and recorded as withheld. Every user in a market receives the batch at the same release time; plans differ only in delivery channel and history depth, never in content or timing. | (b) needs intraday data the design does not buy (ADR-13). Early release for a premium plan creates a fairness and front-running exposure that counsel has not reviewed. |
| BQ-34 | At what price does the track record enter and exit? | (a) the close the signal was computed on; (b) the official open of the first session after release; (c) the next session's VWAP | [DEFAULT-45] (b). Entry: the official opening price of the first session that opens after the release. If that open is at or below the published stop, the entry is recorded as "not triggered" and no position is opened. Stop exit: the first session whose low is at or below the stop; the exit price is the lower of that session's open and the stop (a gap through the stop exits at the open). Exit signal: the official open of the first session after its release. Costs per P5.3 are deducted. | (a) shows prices no follower could have traded at (MB-AC-13); (c) needs intraday data. |
| BQ-35 | One model portfolio per market, or one combined? | (a) one per market, in its own currency; (b) one combined, in a reporting currency | [DEFAULT-46] (a). Each market's model portfolio has its own notional NAV in its own currency (ADR-15), its own BA-4 limits and its own loss counters. No FX enters the risk path. | (b) needs an FX source in the risk path, which ADR-15 excludes, and lets one market's loss stop the other's publication. |
| BQ-36 | What is the scope of the publication kill switch, and what do followers get when it trips? | (a) global only; (b) per market only; (c) per market automatic, plus global manual and global automatic on infrastructure faults | [DEFAULT-47] (c). A market's switch trips automatically on its model portfolio's drawdown breach (BA-4); the global switch trips manually or when both audit sinks are unavailable (OWD-2). On a trip, one status notice per affected market says that signals are suspended; it names no security and is not a signal. Every entry signal already carries its stop ([DEFAULT-43]). | Under (a), a fault in one market stops the other; under (b), an infrastructure fault has no single stop. If counsel holds that a suspension notice must list open positions, it becomes a signal and needs the audit and gate path. |
| BQ-37 | How is a published signal corrected? | (a) withdraw it and remove it from the track record; (b) append a correction that references it; the original stays | [DEFAULT-48] (b). A correction is a new audited record that references the original signal's identifier and states what was wrong. The original keeps its outcome in the track record (MB-AC-12). If the correction reverses the action, an `EXIT` signal is published through the normal path. | (a) lets a bad signal disappear from the record, which MB-AC-12 forbids and which inflates the track record. |
| BQ-38 | Do plans receive different signals? | (a) one signal set per market for every plan; (b) per-plan strategies and model portfolios | [DEFAULT-49] (a). | (b) needs one model portfolio, risk state and track record per plan; P2.8 and P1.2 change shape. |
| BQ-39 | How is broker market data reached, if the P0.2 re-run selects a broker as a data source? | (a) the broker's SDK, with order functions unused; (b) no broker SDK; a minimal read-only HTTP client in `v2/research` with an allowlist of data paths | [DEFAULT-50] (b). The dependency check of section 4 bans every broker SDK outright; the HTTP client may call only allowlisted read-only paths and a test enumerates them (MB-AC-2). | Under (a), MB-AC-1 cannot be enforced by a dependency check, and one wrong call places an order. |
| BQ-40 | Where do the risk gate and model-portfolio accounting live, given that `v2/backtest` must use the same code? | (a) in `v2/signals`, and the backtest re-implements them; (b) in a pure package `v2/signals/core` that `v2/backtest` may import; publication code stays in `v2/signals/publish`, which `v2/backtest` may not import | [DEFAULT-51] (b). `v2/signals/core` has no I/O: no network, no database, no delivery. | (a) breaks parity: a backtest gated by different code is not evidence for the live gate (ADR-08). |

## 12. Edge cases for the rules this file writes

| Rule | Edge case | Resolution |
|------|-----------|------------|
| MB-1 | A transitive dependency bundles a broker SDK. | The dependency check reads the resolved lock file, not only direct dependencies; any match fails the build ([DEFAULT-50]). |
| MB-1 | A "trade on your broker" button or a basket link that pre-fills an order. | Out of scope (section 2). A plain link to a broker's home page that carries no instrument, side or quantity is not an order path and is allowed only on a disclosures page. |
| MB-1 | The backtester's simulated broker. | It is in-process and sends nothing outside the process; the static test of MB-AC-2 enumerates its network calls as zero (`ROADMAP-V1.md` RM-A-2). |
| MB-2 | Subscription fees. | Read per MB-P1: allowed only through a payment processor's hosted page; we store the processor's customer and subscription identifiers, never card or bank details. |
| MB-2 | A user emails a screenshot of their holdings to support. | Support content is never an input to the signal pipeline (MB-AC-9); its retention and deletion are P6.2's. No field is created to hold holdings (MB-AC-4). |
| MB-3 | Shared helpers (exchange calendar, decimal arithmetic). | They live in `v2/research`, which `v2/signals` and `v2/backtest` may both import. |
| MB-3 | The backtest needs the risk gate. | [DEFAULT-51]: `v2/signals/core` is importable by `v2/backtest`; `v2/signals/publish` is not. |
| MB-4 | A free tier. | Treated as regulated until counsel says otherwise (MBA-1); the switch stays off. |
| MB-5 | Counsel approves India and the US at different times. | Each market's switch is independent ([DEFAULT-46]); turning one on changes nothing in the other. |
| MB-5, section 9 | Counsel withdraws or narrows an approval. | The switch is turned off at once (turning off needs no approval, MB-E7); turning it on again needs a new approval record. Approvals have no built-in expiry in v1; P6.3 decides whether they need renewal. |
| MB-5, section 9 | The switch is turned off while a batch is being delivered. | The check is made per message, immediately before each message is handed to a delivery channel. Messages already handed over cannot be recalled; the delivery log records which were sent. |
| MB-5, section 9 | `approved_at_utc` is a few seconds ahead of the loader's clock (clock skew). | Rejected (MB-E5); publication stays off; the operator corrects the clock or the record and reloads. No tolerance window. |
| MB-5 | A user's declared residence changes. | Delivery follows the residence recorded at the moment of each send ([DEFAULT-42]); a user whose residence matches no switched-on market receives no signals. How residence is verified is P6.2's and counsel's. |
| MB-6, MB-7 | A later spec contradicts a rule here. | The later spec cannot override it silently; it carries a conflict row and a new version of this file is written. |
| MB-8 | A feature flag or config key that would enable order placement. | No such key exists in v1 (MB-AC-16); a review at X2 and X4 checks the config schema for one. |
| MB-9 | The audit write succeeds, then delivery fails for some users. | The signal is published as of its audit time; failed deliveries are retried by the delivery service and logged. The signal is never regenerated and its track-record entry is unchanged. |
| MB-9 | The kill switch trips after the audit record is written and before delivery. | Nothing more is delivered; the audit trail gets a "withheld by kill switch" record that references the signal. A withheld signal is still in the track record, labelled withheld, so it can be reviewed; it is excluded from performance shown to users. |
| MB-9 | Market data for the instrument is stale at cycle time. | The signal is not generated (INV-6). An `EXIT` that cannot be generated is not replaced by a guess; the published stop stays the follower's exit level ([DEFAULT-43]). |
| MB-10 | A user filters the signals they see by sector, or keeps a watchlist. | Allowed for display and notification only; the filter is never an input to signal generation, so every user of a market still receives the same signals. |
| MB-10 | A calculator that turns a weight into a share count from the user's capital. | Not in v1. Weights are published as percentages of the model portfolio only. Whether such a tool is personalised advice is for counsel. |
| MB-AC-5 | The primary audit store is down, the local sink is up. | Publication may proceed only on the local-sink path that OWD-2 defines, and P1.4 must say whether that path applies to publication. Until P1.4 says so, publication is denied while the primary store is down. |
| MB-AC-8 | A message is accepted by an external email or push provider just before the trip. | It cannot be recalled; ND-6 defines the deadline for messages not yet handed over. |
| MB-AC-9 | A user joins after an entry signal was published. | They see the current model portfolio as published, with each holding's original publication time, reference price and stop; nothing is re-dated or re-priced for them. |
| MB-AC-12 | A user asks for their personal data to be deleted. | Track-record records hold no user data and are kept. Delivery logs that hold user identifiers are handled by P6.2 and P6.3 against the 5-year record duty (IN-3); the conflict is theirs to resolve with counsel. |
| MB-AC-13 | A backtest on licensed point-in-time data and a live track record are shown together. | Each is labelled with its kind (OWD-5 table); they are never added into one figure. |
| BA-3 | The kill switch trips during a batch. | As MB-9 row 2. |
| BA-4 position | A rally pushes a held model position from 5.0% to 5.4% of model NAV. | No forced trim signal ([DEFAULT-9] carried over). No further `ENTER` on that instrument while it is above 5%. Measured at each session's official close, in the market's currency. |
| BA-4 position | An `ENTER` would put the position at exactly 5.00%. | Allowed; the bound is inclusive. Weights are rounded down to 0.0001 before the check (ND-3). |
| BA-4 risk per position | ATR(14) is zero (no price movement), or the instrument has fewer than 14 daily bars. | No signal (INV-6): the weight `1% x reference price / (2.5 x ATR)` cannot be computed. |
| BA-4 risk per position | The weight from the 1% risk rule exceeds 5%. | The weight is the lower of the two: `min(5%, 1% x reference price / (2.5 x ATR(14)))`. |
| BA-4 loss limits | An overnight gap on a held position. | It counts in the session whose official close first shows it. Daily loss is mark-to-market on official closes, measured from the previous session's closing model NAV. Day is the market's session date in its exchange timezone; week is the sessions of one ISO week in that timezone. |
| BA-4 loss limits | Daily loss exactly 2.00%. | Not a breach; breach is strictly greater than 2%. On a breach, no `ENTER` signals are published in that market for the next session; `EXIT` signals continue. |
| BA-4 drawdown | Drawdown reaches 10.00%. | Trips that market's kill switch ([DEFAULT-47]). Drawdown is measured from the highest closing model NAV since the portfolio started. |
| BA-4 liquidity | A thin stock where the model position is small but followers' combined orders are large. | The cap is applied to the model position at the notional NAV that P2.8 fixes; the follower flow cannot be measured and is disclosed as a risk (MB-AC-11). P2.8 may add a minimum-ADDV eligibility rule. |
| BA-4 stop | The next session opens at or below the published stop. | The entry is "not triggered" ([DEFAULT-45]). |
| BA-4 stop | The stop computed as reference close minus 2.5 x ATR(14) is at or below zero. | No signal; a stop at or below zero means ATR is out of range for that price. |

## 13. Non-blocking details resolved in this file

| # | Detail | Resolution |
|---|--------|------------|
| ND-1 | Timezones | Every timestamp is stored in UTC. Session dates are in the exchange timezone: `Asia/Kolkata` (no DST) for `IN`, `America/New_York` (DST) for `US`. Users see times in their market's timezone. |
| ND-2 | Half-days and DST | The release deadline is computed from the actual close in the exchange calendar for that date, so a US early close moves it earlier. DST changes never shift a session date because dates are taken in exchange-local time. |
| ND-3 | Percentages and weights | Stored as `Decimal` fractions (0.05 means 5%). Weights are rounded down to 0.0001 so that rounding never breaks a cap. |
| ND-4 | Prices and money | `Decimal` in the instrument's currency, never `float`. A long stop is rounded down to the instrument's tick size from the instrument master, and the weight is computed from the rounded stop. |
| ND-5 | Inclusive bounds | Every Block A "<=" is inclusive: exactly at the limit is allowed; strictly above is a breach. |
| ND-6 | Kill-switch deadline (MB-P2) | No message is handed to any delivery channel after the trip is committed to the audit trail; the delivery service re-checks the switch before each hand-off, and every hand-off in progress at the trip completes or fails within 60 seconds. ASSUMPTION; P2.10 confirms or replaces the number. |
| ND-7 | 5-year retention | Counted from each record's publication timestamp to the same calendar date five years later, inclusive; deletion only after the later of that date and any legal hold. |
| ND-8 | Signal identifier and ordering | A UUID per signal; order between signals is the audit trail's sequence, never the wall clock. |
| ND-9 | Release time | The release time of a batch is the audit commit time of its last signal, in UTC. |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| MB-1..MB-8 | Owner's Model B requirements | Owner decision 2026-10-14 | Model A only by a separately approved phase | Whole roadmap |
| MB-9 | Block A controls apply to publication | Same safety logic without orders | Yes | P1.4, P2.9, P2.10 |
| MB-10 | Impersonal signals only | Stays inside RA (India) and the impersonal shape relevant to the US exclusion | Yes, with registration as adviser | Delivery phase, P6.3 |
| BA-1..BA-6 | Block A amendments for v1 | Section 5 | Yes | Every later spec |
| MB-IMP | Spec impact as in section 6 | Section 6 | Yes | Stage 0 re-runs |
| MB-D-11 | The publication switch is one typed record per market; both markets must be stated; any error rejects the whole set (section 9) | MB-5, MB-AC-10; INV-6 fail-closed; INV-10 nothing US-only by accident | Yes, by a new version before P1.3 | P1.3 loader, P1.4 approval records, delivery phase |
| MB-D-12 | Problems MB-P1 to MB-P7 resolved provisionally (sections 10 to 13) | Block A requires them called out; Block C requires defaults and edge cases | Yes, each default by its owning phase | As listed per default in ASSUMPTIONS |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| MBA-1 | Publishing signals to Indian users requires RA registration even for a free tier | IN-1 refers to research services; the free-tier position was not read | Counsel; SEBI RA master circular (Feb 2026) | Free tier may be lighter or still regulated |
| MBA-2 | Individual-use data plans do not permit a signals service | Vendor terms not read for this use | Each vendor (P0.2 re-run) | Data cost lower than feared |
| MBA-3 | The secondary summaries in IN-2, IN-3, IN-5 reflect the regulations | Primary texts not read in full | Read the SEBI master circular for RAs and the 2025-01-08 guidelines | Obligations differ |
| DEFAULT-42 | Switch keyed by instrument market and user residence together | BQ-31 | Counsel in each market | Delivery rules change in PB.1 |
| DEFAULT-43 | Signal content: instrument, action, reference price, stop, weight, deterministic rationale | BQ-32 | Counsel; IN-3 rationale rule | Signal schema gains or loses fields |
| DEFAULT-44 | One batch per market per session, same time for every plan, withheld after close + 21,600 s | BQ-33 | PB.1; counsel on fairness | Delivery timing and P2.7 deadline change |
| DEFAULT-45 | Track record enters at the next official open; stop exits at the lower of open and stop | BQ-34 | P5.2 and P5.3 review | Track-record figures change |
| DEFAULT-46 | One model portfolio per market, own currency | BQ-35 | P2.8 | P2.8 and P2.9 change shape |
| DEFAULT-47 | Kill switch per market and global; suspension notice names no security | BQ-36 | P2.10; counsel | P2.10 trip scope and notice content |
| DEFAULT-48 | Corrections appended; originals kept in the track record | BQ-37 | P1.4, P6.3 | Track-record and audit schemas |
| DEFAULT-49 | One signal set per market for every plan | BQ-38 | Owner (MB-RQ-3) | P2.8, P1.2 |
| DEFAULT-50 | No broker SDK in v1, even for data | BQ-39 | P0.2 re-run | Dependency check and research client |
| DEFAULT-51 | Risk gate and model portfolio in pure `v2/signals/core`, importable by the backtest | BQ-40 | First code phase; X2 | Package boundaries of section 4 |
| ND-6 | Kill-switch hand-off deadline 60 seconds | No deadline was stated (MB-P2) | P2.10 chaos test | Deadline changes |
| MBA-4 | A reference to the written legal review plus the audit approval record is enough to show which review approved a market | MB-AC-10 asks for an approval naming the review; the form of that review is not set | Counsel and P6.3 state the record they need | The switch gains fields in a new version |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| MB-RQ-1..6 | Section 8 | Owner | Section 8 | As listed |
| MBQ-7 | Exact RA obligations, fee limits and model-portfolio rules in force today | SEBI | `sebi.gov.in` master circular for Research Analysts (Feb 2026); circular 2025-01-08 | P6.3, delivery phase |
| MBQ-8 | Does an automated, impersonal signal service fit the US publisher exclusion? | US securities counsel | Lowe v. SEC; Advisers Act §202(a)(11)(D) | US publication |

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| MB-1..MB-10 | rule identifier | Section 1 | Every later spec |
| MB-AC-1..MB-AC-16 | acceptance criterion | Section 7 | X2 reviews, X5, P6.5 |
| BA-1..BA-6 | Block A amendment | Section 5 | Every later spec |
| `publication.enabled.<market>` | config key | `bool`, read as `PublicationSwitchSet.is_enabled(market)`; off unless enabled with a recorded legal-review approval (section 9) | P1.3, delivery phase |
| `PublicationSwitch` | type | `market: Market`, `enabled: StrictBool`, `legal_review_ref: str or None`, `approval_audit_id: UUID or None`, `approved_at_utc: AwareDatetime or None` (section 9) | P1.3, P1.4, P2.10, delivery phase |
| `PublicationSwitchSet` | type | `switches: tuple[PublicationSwitch, ...]`, one per `Market`; `is_enabled(market) -> bool` (section 9) | P1.3, P2.10, delivery phase |
| `v2/research`, `v2/backtest`, `v2/signals` | package boundary | Section 4 | Every code phase |
