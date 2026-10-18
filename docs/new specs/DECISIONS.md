---
id: DECISIONS-INDEX
version: 0.1
status: DRAFT
phase: P0.1
depends_on: [SPEC-A-CONSTITUTION, SPEC-P0.1-DECISIONS]
produces: [decision index for the new run]
---

# Decision log (new run)

This is an index. It decides nothing. The text of each decision is in the spec named. The
historical log at the repository root, `DECISIONS.md`, belongs to the earlier project and is
not continued here (N-2, [DEFAULT-1]).

Maintained by: each phase adds its rows when its spec is written, and updates the status
column when a spec is frozen or an assumption is verified or falsified.

## 1. Architecture decision records

All dated 2026-10-13. All PROPOSED until `SPEC-P0.1-DECISIONS` is FROZEN.

| ADR | Decision | Status | Spec |
|-----|----------|--------|------|
| ADR-01 | FastAPI for actions, Grafana read-only, no web UI | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-02 | One in-process asyncio scheduler on exchange calendars | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-03 | No Kubernetes; second VM first on a capacity trigger | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-04 | No alternative data in v1 | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-05 | Common stock only | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-06 | No vector storage | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-07 | Quarterly retrain; three out-of-cycle triggers; a loss is never a trigger | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-08 | One challenger, shadow test, human promotes | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-09 | Fourteen human-approval actions; expiry at end of session | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-10 | RPO 60 seconds, RTO 4 hours, recovery means reconciled | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-11 | Dual-market design; India live first | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-12 | Long-only, no borrowing | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-13 | Swing holding period on daily bars | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-14 | Universe of 500 per market by traded value, rebuilt monthly | PROPOSED | SPEC-P0.1-DECISIONS |
| ADR-15 | Per-account currency, no FX in the risk path, INR reporting | PROPOSED | SPEC-P0.1-DECISIONS |

## 1a. Stage 0 Owner decisions

Resolved under the Owner's delegation of 2026-10-14 in `STAGE-0-OWNER-DECISIONS.md` (DRAFT until the Owner approves it). That file governs the items it names until the specs absorb its amendments AMD-1 to AMD-14.

| Decision | Subject | Status |
|----------|---------|--------|
| OWD-1 | Residency; serves other people in India and the US (Owner, 2026-10-14) | PROVISIONAL; legal review pending |
| Scope | Multi-user service, India and US (`SCOPE-MULTI-USER.md` v0.4) | DRAFT |
| CR-1 | US day-trading and cash-account rules verified at primary sources (`SPEC-CR1-US-DAY-TRADING.md` v0.2) | DRAFT |
| Model B | Signals only for v1; no order routing, no broker integration, no user funds (`MODEL-B-DECISION.md` v0.3); roadmap `ROADMAP-V1.md` v0.3 | Owner decision 2026-10-14 |
| OWD-2 | Audit or data unavailable | PROVISIONAL |
| OWD-3 | The 15 ADRs (ADR-11 changed) | PROVISIONAL |
| OWD-4 | USD 200-500 is the LLM ceiling | VERIFIED interpretation |
| OWD-5 | India data deadlock | BLOCKED for evidence; not for Stage 1 |
| OWD-6 | Code in `v2/` | VERIFIED |
| OWD-7 | Single VM, off-VM backups, recovery address | PROVISIONAL |
| OWD-8 | Python 3.13 | VERIFIED |
| OWD-9 | Historical uncommitted changes preserved | VERIFIED |

## 2. Provisional defaults awaiting the Owner

A default is not a ruling. Status is PENDING until the Owner confirms or overrules it.

| Default | Subject | Status | Spec |
|---------|---------|--------|------|
| DEFAULT-1 | Location of this log | PENDING | SPEC-A-CONSTITUTION |
| DEFAULT-2 | DENY and risk-reducing actions; second audit sink | REPLACED by OWD-2 (provisional), 2026-10-14 | STAGE-0-OWNER-DECISIONS |
| DEFAULT-3 | Long-only, no borrowing | PENDING; adopted by ADR-12 | SPEC-A-CONSTITUTION |
| DEFAULT-4 | Kill switch on one VM; resting stops; manual off-VM path | PENDING | SPEC-A-CONSTITUTION |
| DEFAULT-5 | Order-rate limits as minimum spacing | PENDING | SPEC-A-CONSTITUTION |
| DEFAULT-6 | India disabled on a day with no human login | PENDING | SPEC-A-CONSTITUTION |
| DEFAULT-7 | NAV equals equity, per account | PENDING; adopted by ADR-15 | SPEC-A-CONSTITUTION |
| DEFAULT-8 | Loss-limit base, boundary and breach action | PENDING | SPEC-A-CONSTITUTION |
| DEFAULT-9 | Position limit measured before the order; no forced trim | PENDING | SPEC-A-CONSTITUTION |
| DEFAULT-10 | New-run code under `v2/` | CONFIRMED by OWD-6 (verified), 2026-10-14 | STAGE-0-OWNER-DECISIONS |
| DEFAULT-11 | Pack restarts at P0.1 | PENDING | SPEC-A-CONSTITUTION |
| DEFAULT-12 | Account holder is resident in India | CONFIRMED PROVISIONALLY by OWD-1, 2026-10-14; OWQ-1 open | STAGE-0-OWNER-DECISIONS |
| DEFAULT-13 | Swing holding period | PENDING | SPEC-P0.1-DECISIONS |
| DEFAULT-14 | India live first | WITHDRAWN by OWD-5 / AMD-11, 2026-10-14; go-live order decided at P6.5 | STAGE-0-OWNER-DECISIONS |
| DEFAULT-15 | Universe rule | PENDING | SPEC-P0.1-DECISIONS |
| DEFAULT-16 | US account run with zero borrowing | PENDING | SPEC-P0.1-DECISIONS |
| DEFAULT-17 | LLM gate width 10 | PENDING | SPEC-P0.1-DECISIONS |
| DEFAULT-18 | Reporting currency INR | PENDING | SPEC-P0.1-DECISIONS |
| DEFAULT-19 | Backups stored off the VM | CONFIRMED PROVISIONALLY by OWD-7, 2026-10-14 | STAGE-0-OWNER-DECISIONS |
| DEFAULT-20 | ETFs and depositary receipts not tradable | PENDING | SPEC-P0.1-DECISIONS |
| DEFAULT-21 | No starting capital assumed | PENDING | SPEC-P0.1-DECISIONS |
| DEFAULT-22 | India resting stop: GTT limit strictly below trigger | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-23 | US resting stop: `stop`, `gtc` | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-24 | No fractional shares | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-25 | 10 years of US daily history | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-26 | Raw bars and corporate actions stored separately | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-27 | US settled cash from our own ledger; no shorting, no margin | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-28 | US fundamentals blocked while SEC requests are paused | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-29 | Licensed India point-in-time history before any India evidence | PENDING | SPEC-P0.2-PROVIDERS; stands per OWD-5 |
| DEFAULT-30 | Internal order reference: 20 characters A-Z0-9 | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-31 | Clients run at most half of a documented rate limit | PENDING | SPEC-P0.2-PROVIDERS |
| DEFAULT-32 | Budget ceiling covers all platform cost | PENDING | SPEC-P0.3-BUDGET; overruled by OWD-4 / AMD-13 |
| DEFAULT-33 | VM: DigitalOcean Bangalore, 16 GiB | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-34 | Daily history for the whole listed market | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-35 | Offline work in a capped container on the live VM | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-36 | No LLM calls inside walk-forward backtests | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-37 | LLM call size planning figures and hard caps | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-38 | Decision-cycle deadline close + 21,600 s | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-39 | Whole-market ingest off the decision path | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-40 | RPO via 16 MB WAL segments, 60 s archive timeout | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-41 | Stop placements count toward order spacing, stops first | PENDING | SPEC-P0.3-BUDGET |
| DEFAULT-42 | Publication keyed by instrument market and user residence | PENDING | MODEL-B-DECISION |
| DEFAULT-43 | Signal content, deterministic rationale, no target price | PENDING | MODEL-B-DECISION |
| DEFAULT-44 | One batch per market per session, same time for every plan | PENDING | MODEL-B-DECISION |
| DEFAULT-45 | Track record enters at next official open | PENDING | MODEL-B-DECISION |
| DEFAULT-46 | One model portfolio per market, own currency | PENDING | MODEL-B-DECISION |
| DEFAULT-47 | Kill switch per market and global; suspension notice | PENDING | MODEL-B-DECISION |
| DEFAULT-48 | Corrections appended, originals kept | PENDING | MODEL-B-DECISION |
| DEFAULT-49 | One signal set per market for every plan | PENDING | MODEL-B-DECISION |
| DEFAULT-50 | No broker SDK in v1, even for data | PENDING | MODEL-B-DECISION |
| DEFAULT-51 | Risk gate and model portfolio in pure `v2/signals/core` | PENDING | MODEL-B-DECISION |
| DEFAULT-52 | A phase result counts once committed with the Owner's yes | PENDING | ROADMAP-V1 |
| DEFAULT-53 | Upstream version change: notice, re-run only on contract change | PENDING | ROADMAP-V1 |
| DEFAULT-54 | v1 users are natural persons resident in India or the US | PENDING | SCOPE-MULTI-USER |
| DEFAULT-55 | Legacy PDT check per broker, on unless the broker says it no longer applies it | PENDING | SPEC-CR1-US-DAY-TRADING |
| DEFAULT-56 | Legacy PDT equity check uses the lower of live and previous-close equity | PENDING | SPEC-CR1-US-DAY-TRADING |
| DEFAULT-57 | Legacy day trades counted per sell fill | PENDING | SPEC-CR1-US-DAY-TRADING |
| DEFAULT-58 | Model-portfolio entries funded from settled model cash only, both markets | PENDING | SPEC-CR1-US-DAY-TRADING |

## 3. Assumptions verified or falsified

An assumption moves here, with the evidence and the date, when its "How to verify" step has
been carried out.

| Assumption | Outcome | Evidence | Date |
|------------|---------|----------|------|
| PDT equity floor USD 25,000 (historical `ASSUMPTION [VERIFY-P0.2]`, SPEC-P1.1 §9.4, `config/policy.yaml`; Stage 1 gap audit G-2, condition 16) | **FALSIFIED as current; VERIFIED as the legacy value.** FINRA Rule 4210(f)(8)(B) day-trading provisions replaced by intraday margin, 4210(d)(2), effective 2026-06-04, phase-in to 2027-10-20; Alpaca lifted PDT on 2026-06-04 | SEC Release 34-105226, 91 FR 20731; FINRA Regulatory Notice 26-10; `SPEC-CR1-US-DAY-TRADING` section 2 | 2026-10-18 |
| US settlement T+1; Regulation T payment period (historical Q-P1.1-1, question part) | **VERIFIED.** T+1 (17 CFR 240.15c6-1(a)); payment period = settlement cycle + 2 business days (12 CFR 220.2); 90-day freeze for a sale before payment (12 CFR 220.8(c)) | eCFR, up to date as of 2026-10-15; `SPEC-CR1-US-DAY-TRADING` section 2 | 2026-10-18 |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
