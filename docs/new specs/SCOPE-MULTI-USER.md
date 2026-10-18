---
id: SCOPE-MULTI-USER
version: 0.4
status: DRAFT
phase: Scope change before the P0.1 re-run
depends_on: [STAGE-0-OWNER-DECISIONS v0.1 section 1.5]
produces: [SC-1..SC-12]
---

# Scope: a multi-user trading service for India and the US

Version history: 0.1 (2026-10-14) written with Model A as the provisional service model.
0.2 (2026-10-14) the Owner chose **Model B, signals only for v1** (`MODEL-B-DECISION.md`). Rules
SC-2, SC-3 and SC-8 are superseded by MB-1, MB-2 and MODEL-B-DECISION section 3; SC-7 is
superseded by section 2 of that file (the system trades for no one in v1). The v0.1 text is kept
below unchanged for the record; read it with this note.
0.3 (2026-10-17) Block B conformance pass: the four mandatory tables are added at the end. This
file defines rules, not entities; the user, consent and account entities named in SC-12 are typed
by P1.1 (Adapted per `ROADMAP-V1.md`), so no model is added here. No rule changes.
0.4 (2026-10-17) Block C conformance pass: section 5 (blocking question BQ-43 with
[DEFAULT-54]), section 6 (edge cases for the rules still in force), section 7 (non-blocking
details). No rule changes.

Date: 2026-10-14. Source: the Owner's answers of 2026-10-14 ("serve other people, this ai
trading agent is for all"; markets "both india and us"). This file is an input to every phase
from the P0.1 re-run onward. Where it conflicts with `master-research-summary.md` or with a
Stage 0 spec written before it, this file governs the scope; Block A still governs the
invariants.

Nothing here is legal advice. Every regulatory statement is marked with its source and level;
a qualified adviser in each market must confirm the route before any outside user is onboarded.

## 1. Service model (Model A, provisional)

| # | Rule |
|---|------|
| SC-1 | The system is a software service used by other retail investors in **India and the US**. |
| SC-2 | Each user trades **only in their own brokerage account**, opened in their own name with a broker that supports third-party algorithms or apps. The service never holds, pools or moves user money. |
| SC-3 | The service sends orders to a user's account only with that user's recorded, revocable consent, through the broker's sanctioned route (India: a partner broker under the exchange algo framework; US: the broker's authorised third-party access, for example OAuth). Users never hand over passwords. |
| SC-4 | No discretionary management of pooled money and no portfolio-management service (Model C is out of scope). |
| SC-5 | Every Block A invariant and HARD RISK NUMBER applies **per user account**: risk engine, kill switch, audit trail, fail-closed, limits. One user's state can never affect another user's limits or orders. |
| SC-6 | A user may be a resident of India using Indian markets, or a US person using US markets. Cross-border use (an Indian resident trading US stocks through the service, or the reverse) is **out of scope for v1**: it adds exchange-control (LRS), tax and eligibility questions per user. |
| SC-7 | The Owner may use the service on their own account for testing before any outside user. |

Model A was recommended on 2026-10-14 and is used here provisionally; the Owner's confirmation
is pending (OWQ-4).

## 2. Regulatory gates before any outside user (to be confirmed by advisers)

| # | Market | Gate | Source and level |
|---|--------|------|------------------|
| SC-8 | India | The provider is empanelled with NSE and/or BSE through a partner broker; does not connect to an exchange directly; every algo order carries an exchange-issued Algo ID; a strategy whose logic is not disclosed to users ("black box") requires SEBI Research Analyst registration and a research report per strategy, and any change of logic is a new registration. | SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 (2025-02-04), NSE standards (2025-05-05), in force 2026-04-01 — **secondary sources, search excerpts, 2026-10-14**; primary text unread (OQ-1) |
| SC-9 | US | A service that directs trading in other people's accounts for compensation is expected to need investment-adviser registration (SEC or state) and to follow the broker's third-party app rules. | `master-research-summary.md` §16 (repository); **not verified** at any primary source |
| SC-10 | Both | Users' personal and financial data falls under data-protection law (India: Digital Personal Data Protection Act 2023; US: state privacy laws). | **ASSUMPTION**, not verified |
| SC-11 | Both | Who holds each registration (the Owner personally or a company) is undecided. | Owner (OWQ-5) |

Until SC-8 and SC-9 are cleared for a market, the service is used in that market by the Owner
only (SC-7).

## 3. What this changes for the phases

| # | Area | Change from the Stage 0 single-user design |
|---|------|--------------------------------------------|
| SC-12 | Domain and storage (P1.1, P1.2) | User, consent, broker connection and user account are first-class entities; every position, order, limit, audit event and NAV belongs to exactly one user account. |
| — | Configuration (P1.3) | Per-user risk settings within the Block A hard limits; a user may make limits stricter, never looser. |
| — | Audit (P1.4) | Per-user audit chains or a per-user partition of one chain; regulator export per user and per strategy (Algo ID). |
| — | Approvals (ADR-09) | Operator approvals (the Owner) stay; users get their own consent and kill controls for their own account. |
| — | Kill switch (P2.10) | Per-user and global. |
| — | Costs (P0.3) | Cost per user and fixed platform cost; data licences for redistribution to users (single-user licences do not cover a multi-user service). |
| — | Security and compliance (P6.2, P6.3) | Authentication of users, isolation between users, KYC is the broker's, suitability and disclosures per market. |

## 4. What does not change

Block A invariants; the fixed stack; daily-bar swing trading, long-only, common stock only, no
backup broker and Python 3.13, as decided in `STAGE-0-OWNER-DECISIONS.md`, unless the P0.1 re-run
finds a reason to reopen one under the new scope.

## 5. Blocking questions and the defaults used

Numbering continues from `ROADMAP-V1.md` (BQ-42, [DEFAULT-53]). The other scope forks are
answered in `MODEL-B-DECISION.md` section 11 ([DEFAULT-42] covers residence and delivery).

| # | Question | Options | Default used | If the default is wrong |
|---|----------|---------|--------------|-------------------------|
| BQ-43 | Who may be a user in v1? | (a) natural persons only; (b) also Hindu Undivided Families, companies and trusts; (c) also non-resident Indians and US persons living abroad | [DEFAULT-54] (a): natural persons of full legal age, resident in India (for `IN` signals) or in the US (for `US` signals). HUFs, companies, trusts, non-resident Indians and US persons living abroad are out of scope for v1. | HUFs are a common client type in India and IN-5 reports fee limits for "individual and HUF clients"; including them later changes onboarding, KYC and fee rules (P6.3, PB.1). Non-resident cases bring exchange-control and tax questions, which SC-6 already excludes. |

## 6. Edge cases for the rules still in force

SC-2, SC-3, SC-7 and SC-8 are superseded (version note) and get no edge cases.

| Rule | Edge case | Resolution |
|------|-----------|------------|
| SC-1 | A user resident in India wants US signals, or the reverse. | Not delivered ([DEFAULT-42]); the user sees only their own market's signals. |
| SC-1 | A user moves between India and the US. | Delivery follows the residence recorded at each send; the change of residence is the user's declaration, verified as P6.2 and counsel decide. |
| SC-4 | A user asks the service to manage their money. | Refused; v1 publishes impersonal signals only (MB-10). |
| SC-5 | Read under Model B, there are no user accounts to apply limits to. | BA-4 applies the limits to each market's model portfolio ([DEFAULT-46]); no limit is per user. |
| SC-6 | A non-resident Indian trading Indian stocks through Indian accounts. | Out of scope for v1 ([DEFAULT-54]); onboarding asks for residence and refuses non-residents. |
| SC-9 | Superseded for v1 (no trades in others' accounts). | Returns only with an execution phase (MB-8). |
| SC-10 | A user requests deletion of personal data. | P6.2 handles it against the 5-year record duty (`MODEL-B-DECISION.md` section 12, MB-AC-12 row). |
| SC-11 | The Owner registers as an individual and later moves to a company. | Each registration change is a new legal review; the publication switch is turned off and on again with a new approval record (`MODEL-B-DECISION.md` section 9). |
| SC-12 | Read under Model B, "broker connection" and "user account" are not v1 entities. | P1.1 types user, consent, plan and subscription; no broker connection, no user brokerage account (MB-2, MB-AC-4). |

## 7. Non-blocking details resolved in this file

| # | Detail | Resolution |
|---|--------|------------|
| SD-1 | Age of majority | 18 in India. In the US the age of majority differs by state; v1 requires 18 or the user's state age of majority, whichever is higher. Which states set a higher age is not asserted here; P6.3 checks it. |
| SD-2 | Residence evidence | A declared country plus the evidence P6.2 and counsel require; an IP address alone is never treated as proof of residence. |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| SC-1 | The service is for other retail investors in India and the US | Owner, 2026-10-14: "serve other people, this ai trading agent is for all"; markets "both india and us" | Yes, by the Owner | Every phase from the P0.1 re-run |
| SC-4 | No pooled money and no portfolio-management service | Model C was not chosen; pooled management is a separately regulated activity in both markets | Yes, only with its own registration and phase | Domain, compliance |
| SC-5 | Block A controls apply per user account | One user's state must never affect another's | Yes | Under Model B there are no user accounts; read as the model portfolio per BA-4 |
| SC-6 | Cross-border use is out of scope for v1 | Adds exchange-control (LRS), tax and eligibility questions per user | Yes, by a later phase | Onboarding, compliance |
| SC-2, SC-3, SC-7, SC-8 | Superseded by Model B (version note above) | `MODEL-B-DECISION.md` MB-1, MB-2, section 2 and section 3 | Only through MB-8 | Kept for the record; not inputs to v1 phases |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| DEFAULT-54 | v1 users are natural persons of full legal age resident in India or the US | BQ-43 | Counsel in each market; Owner on HUF clients | Onboarding, KYC and fee rules change |
| SC-10 | Users' personal and financial data falls under India's Digital Personal Data Protection Act 2023 and US state privacy laws | Not checked against any primary text | Counsel in each market; the DPDP Act 2023 text and its rules; the privacy statutes of the states where users live | P6.2 and P1.2 data handling change |
| SC-9 | Directing trades in other people's accounts for compensation needs investment-adviser registration in the US | Taken from `master-research-summary.md` section 16, not verified | US securities counsel; Investment Advisers Act of 1940 section 202(a)(11) | Superseded for v1 by Model B; returns with any execution phase |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| SC-11 / OWQ-5 | Who holds each registration: the Owner personally or a company? | Owner | `STAGE-0-OWNER-DECISIONS.md` OWQ-5; `MODEL-B-DECISION.md` MB-RQ-1 | First outside user in each market; P6.3 |
| OQ-1 | What does SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 require, read from its primary text? | SEBI | sebi.gov.in, search the circular number | Only the future execution phase (BA-1) |

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| SC-1..SC-12 | rule identifier | Sections 1 to 3; SC-2, SC-3, SC-7 and SC-8 superseded per the version note | P0.1 to P0.3 re-runs, P1.1, P1.2, P6.2, P6.3 |
