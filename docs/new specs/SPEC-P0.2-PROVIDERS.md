---
id: SPEC-P0.2-PROVIDERS
version: 0.3
status: DRAFT
phase: P0.2
depends_on: [SPEC-A-CONSTITUTION, SPEC-P0.1-DECISIONS, MODEL-B-DECISION, SPEC-CR1-US-DAY-TRADING]
produces: [F-6..F-64, F-77..F-108, DEFAULT-22..DEFAULT-31, DEFAULT-59..DEFAULT-64, ProviderId, Capability, SelectionStatus, VerificationLevel, LimitBasis, ProviderErrorClass, AdjustmentBasis, BarResolution, LicensedUse, DormancyStatus, ClientOrderRef, RateLimitFact, ClientThrottle, ProviderSelection, ProviderSelectionSet, VendorSeriesSnapshot, AccountActivity, ResearchGateApproval, dormancy_status, research_gate_open, publication_data_cleared, row_cleared, throttle_matches, SEL-1..SEL-23, PE-1..PE-25, THR-1..THR-14]
---

> **Model B notice (2026-10-14).** The Owner chose signals only for v1 (no order routing, no broker integration, no handling of user funds). This spec's text below is unchanged. Where it concerns orders, brokers or accounts it is superseded or deferred as listed in `MODEL-B-DECISION.md` section 6, and Block A items are read with the amendments BA-1 to BA-6 there. Phases are re-run per `ROADMAP-V1.md`.

# SPEC-P0.2 — Provider and Broker Due Diligence (new run)

Date: 2026-10-13; amended 2026-10-30. Decision owner: Owner. Author: integration engineer (this run).

Version history: 0.1 (2026-10-13) first record. 0.2 (2026-10-30) amendment for issue #2: section 0
says what changed, and why. This amendment is not the Model B re-run that `ROADMAP-V1.md` requires
of P0.2; it changes the India data rows and the items in section 0 only. 0.3 (2026-10-30) fixes from
the full-spec X2 in claude.ai and DeepSeek: typed licence gate, research gate revocation, shared
rate budget, candle ordering, tick unit, a status in place of the dormancy sentinel, and the check
moved into the repository. No selection changed.

Inputs consumed by v0.1: `CONSTITUTION.md` v0.3 (SPEC-A-CONSTITUTION) and `SPEC-P0.1-DECISIONS.md`
v0.1, both as supplied in full with the phase prompt. No other repository file was read (N-3).
Added for v0.2: `MODEL-B-DECISION.md`, issues #2, #37, #56 and #68, root `DECISIONS.md` (Owner
decision of 2026-10-17) and the historical `docs/specs/SPEC-P0.2-PROVIDERS.md` and
`docs/specs/SPEC-P2N.13-FAST-FEEDS.md`, read as records and not edited (N-2).

Run notes:
- This phase ran in a fresh conversation, as the pack requires.
- The Owner has paused direct requests to SEC hosts. No request was made to `sec.gov`,
  `data.sec.gov` or `efts.sec.gov`. Everything this spec says about SEC EDGAR comes from
  third-party pages and is marked SECONDARY.
- No account was created, no terms were accepted, no credential was read, and no authenticated
  API was called. Every fact comes from a public documentation or pricing page.
- Identifier series continue from P0.1 (D-10): DEFAULT-22, A-37, OQ-27, NB-28, D-11, F-6, UP-11,
  E-9 onward. v0.2 continues from the highest number used across the new-run specs: BQ-48,
  [DEFAULT-59], A-76, OQ-67, NB-63, D-39, F-77, UP-40, E-33, PE-17, THR-13, SEL-22.
- The v0.2 run kept the same limits: no SEC host was contacted, directly or through a fetching
  service; no account was created; no terms were accepted; no credential was read; no authenticated
  API was called.

Status of this spec: DRAFT, and it cannot be frozen as it stands. ADR-11 says a phase that cannot
be completed for one market because a vendor fact is missing stays DRAFT. After v0.2 every India
capability has a named candidate, but each rests on a licence that is not verified for Model B
(section 6.3, OQ-68), and no India daily history covers delisted stocks.

Contents: 0 amendment v0.2; 1 blocking questions and defaults; 2 upstream problems; 3 evidence register;
4 capabilities needed; 5 provider fact sheets; 6 decision matrix and selection; 7 what breaks at
09:31; 8 typed form; 9 error paths; 10 documentation that could not be verified;
11 non-blocking details; then the four tables.

## 0. Amendment v0.2 (2026-10-30)

Issue #2 asked for three things after v0.1: fact sheets for Upstox, Fyers and SEC EDGAR, re-using
the figures recorded in #68; two corrections from `SPEC-P2N.13` (F-1); and verification of the
USD 25,000 PDT floor.

The PDT item is already done in `SPEC-CR1-US-DAY-TRADING` v0.2 and is not repeated: USD 25,000 is
verified only as the legacy value, and FINRA replaced the rule effective 2026-06-04. This spec never
stated the figure, so nothing here changes for it.

**The result that matters.** The price, history and limit figures recorded in #68 were re-read at the vendors' pages before
being re-used, and one of them does not hold as recorded. Fyers documents intraday history from
3 July 2017, but its free Standard plan serves intraday only from 2025 and daily only from 2021;
the deeper history needs the paid Prime plan (F-77, F-83). Fyers' plan-based limits took effect on
2026-10-16 (F-98), the day before the Owner's decision of 2026-10-17, which was made on the reading
that this depth was free. Separately, the Fyers API terms restrict derived
works, distribution and paper trading in ways that bear directly on a signals service (F-82), and
Upstox publishes a one-year read-only token that removes the daily login for data (F-87). See
UP-40, UP-41, UP-45.

Four Owner decisions come out of this. They are the ones that change the design; the six PENDING
defaults and the not-applied patch for the historical spec also wait for the Owner's yes:

| # | Decision needed | Where | Default until then |
|---|-----------------|-------|--------------------|
| 1 | India intraday source: accept Upstox (free, from January 2022), or buy Fyers Prime (INR 5,888.20 a year with GST, depth to be confirmed). The ranking is close and could flip (section 6.2). Buying Prime also conflicts with the Owner's "no subscriptions" instruction of 2026-10-16, as does Massive at USD 79 (UP-46) | BQ-48, OQ-67 | [DEFAULT-59] Upstox primary, no intraday backup |
| 2 | India data licence for a commercial signals service. Upstox staff say a paid service needs a separate business arrangement and name the route: the Business Trading API form or api@upstox.com (F-100). Writing to them, to Fyers and to counsel is the Owner's step | UP-41, OQ-68 | No India selection may be SELECTED; research use only |
| 3 | SEC EDGAR: confirm whether the pause on SEC requests stands, and name the contact identity | UP-47, OQ-41 | Stays BLOCKED; no request made |
| 4 | Research on Upstox data before a written answer: accept the risk, or wait for OQ-68 | Section 6.3, research gate | Closed: no client runs until the Owner accepts |

Change log:

| Section | Change |
|---------|--------|
| Header | Version 0.2; `depends_on` adds MODEL-B-DECISION and SPEC-CR1-US-DAY-TRADING |
| 1 | BQ-48 to BQ-53, [DEFAULT-59] to [DEFAULT-64] |
| 2 | UP-40 to UP-48; UP-24, UP-25 notes added |
| 3 | F-77 to F-108; F-39 and F-43 re-read and unchanged; F-97 partly re-read |
| 4 | New capability `intraday_bars` |
| 5.2 | Benzinga feed facts (corrections of SPEC-P2N.13 F-1) |
| 5.4 | Upstox rewritten for its data role; execution paragraphs kept, deferred |
| 5.9 | SEC EDGAR completed from recorded figures; still SECONDARY and blocked |
| 5.11 | India news candidate added |
| 5.15 | New: Fyers. Non-trading app required |
| 6.1, 6.2, 6.3 | C6 scored for Model B on re-scored rows; 12 rows added and 2 re-scored; SEL-4, SEL-6, SEL-8, SEL-10, SEL-12, SEL-14, SEL-16 changed; SEL-22, SEL-23 added; research gate and publication gate stated |
| 7 | Upstox row changed; Fyers and India news rows added |
| 8 | `ProviderId` adds `FYERS`, `REVIEWED_CALENDAR_FILE`; `Capability` adds `INTRADAY_BARS`; `ProviderErrorClass` adds `ACCOUNT_RESTRICTED`; `ProviderSelection` adds `licensed_use`; new `AdjustmentBasis`, `BarResolution`, `LicensedUse`, `DormancyStatus`, `ProviderSelectionSet`, `VendorSeriesSnapshot`, `AccountActivity`, `ResearchGateApproval` and five functions; THR-13, THR-14 |
| 9 | PE-17 to PE-25; E-33 to E-36; E-12 amended for the research gate |
| 10 | Rows 37 to 49 |
| 11 | NB-63 to NB-73; NB-34, NB-35 moved to the Upstox file |
| Tables | D-39 to D-46; D-11, D-20, D-22 updated; A-76 to A-83; OQ-67 to OQ-80; OQ-30, OQ-40, OQ-41, OQ-46 changed; contracts updated |

Propagation. [DEFAULT-53] requires a dated notice, and a re-run where an imported contract changed:

| Consumer | What changes for it |
|----------|---------------------|
| `SPEC-P0.3-BUDGET` | Kite Connect INR 500 a month is no longer a data cost; Upstox and Fyers Standard are INR 0; Fyers Prime is an option. Already due for its Model B re-run |
| P1.1 | `ProviderId`, `Capability`, `ProviderErrorClass` gain members; `AdjustmentBasis`, `BarResolution` are new |
| P1.2, P1.3, P1.4 | Snapshot storage and its DDL; new config keys; `ACCOUNT_RESTRICTED` in the audit event field. P1.3's loader must also reject an enabled publication switch unless `publication_data_cleared` is true for that market; `MODEL-B-DECISION.md` has no such error path yet (a proposed MB-E9, OQ-78). P1.3 also resolves `licence_audit_id` and `backup_licence_audit_id` at every load, as MB-E4 does for a switch, and loads selections through `model_validate_json` |
| P2.7 | Signal entry accepts only `1D` bars, and every signal input only from a provider that `row_cleared` confirms; both need tests |
| P2.1 | Client is Upstox (read-only HTTP, [DEFAULT-50]) once the Owner opens the research gate; Fyers only after OQ-68 for Fyers; snapshot rule [DEFAULT-62]; expected-session check PE-24 |
| P2.2 | PE-22 data-quality event; threshold is P2.2's |
| P2.3 | Instrument master and sector from Upstox; delisted coverage still missing |
| P4.1 | India news candidate with a 7-day window, so capture must be daily; enforces that no gated content reaches an external LLM until OQ-76 closes |
| P5.x | Every India result stays labelled survivorship-biased ([DEFAULT-29]) |
| P6.1 | `AccountActivity` metric; token renewal alert |
| P6.3 | OQ-68 is an input; BO-1 and MB-AC-14 are not met for either market; records a negative answer to OQ-68 by setting `revoked_on` |
| Historical issues #8, #26, #27, #33, #34, #62, #63, #64, #67, #69 | The #67 "9 years of free Fyers intraday" premise fails (UP-40); #64 has no daily token step for Upstox data (UP-45); two static-IP registrations are not needed while no order is sent (BA-1) |

Review. X2 ran in a separate conversation and in DeepSeek; findings and their disposition are in
`reviews/P0.2-V0.2-REVIEW.md`.

Freeze. `STAGE-1-FREEZE` section 14 is the procedure the issue names; it requires X2, X3, X5 and an
Owner decision. This spec stays DRAFT: ADR-11 forbids a freeze with a market incomplete, and the
Owner's questions above are open.

## 1. Blocking questions and the defaults used

| # | Question | Options | Default used | If the default is wrong |
|---|----------|---------|--------------|-------------------------|
| BQ-11 | What is the "stop resting at the broker" in India? Kite stop orders (`SL`, `SL-M`) have validity `DAY`, `IOC` or `TTL` only (F-9). The only instruction that survives the session is a GTT, and the Kite API documents `LIMIT` as the only GTT order type (F-10). | (a) one single-leg sell GTT per position, with a limit price below the trigger; (b) a fresh `SL-M` order placed every morning; (c) both | [DEFAULT-22] (a). The limit price is strictly below the trigger. The size of the gap between them is P3.4's decision and is not assumed here. | Under (a) a gap through the limit price leaves the position open with no stop, and the GTT does not fire again (F-11). Under (b) a day with no human login has no stop at all. Under (c) two sell instructions exist for the same shares. |
| BQ-12 | Which US order is the resting stop? | (a) `stop`, `gtc`; (b) `stop_limit`, `gtc`; (c) bracket order at entry | [DEFAULT-23] (a). A `stop` becomes a market order when elected (F-21). It is re-placed before its 90-day expiry. | Under (b) a gap through the limit leaves the position open. Under (c) the stop cannot be re-priced independently of the entry group. |
| BQ-13 | Are fractional shares used in the US? | yes; no | [DEFAULT-24] No. Fractional orders must be `day` (F-23), so a fractional quantity cannot carry a `gtc` stop. Whole shares in both markets. | Small US accounts cannot hold high-priced names (ADR-14, small accounts). |
| BQ-14 | How many years of US daily history are bought? | 5 years (Massive Starter, USD 29); 10 years (Developer, USD 79); 20+ years (Advanced, USD 199) (F-48) | [DEFAULT-25] 10 years, Developer plan. ADR-13 sized storage for 10 years. | P0.3 budget and P5.2 walk-forward length both change. |
| BQ-15 | Are bars stored adjusted or raw? | vendor-adjusted; raw plus our own adjustment | [DEFAULT-26] Raw bars and corporate actions are stored separately. Adjustment is computed by our code. A vendor-adjusted series is used only as a cross-check. | With vendor-adjusted storage, a vendor restating history silently changes model inputs (ADR-07 T-3) and breaks point-in-time. |
| BQ-16 | What number is "settled cash" at Alpaca? No account field is described as settled cash (F-24). | (a) `cash`; (b) `non_marginable_buying_power`; (c) our own ledger of settled cash; (d) the minimum of all three | [DEFAULT-27] (d), and the account is configured with `no_shorting=true` and `max_margin_multiplier="1"` (F-25). | A buy funded by unsettled proceeds is borrowing, which ADR-12 forbids and F-4 may make unlawful. |
| BQ-17 | What happens to US fundamentals while SEC requests are paused? | (a) build the EDGAR client anyway; (b) use a paid aggregator as primary; (c) the capability stays blocked | [DEFAULT-28] (c). No EDGAR client is built or run until the Owner lifts the pause. FMP is the named backup and is used only if the Owner approves its cost and OQ-47 is answered. | P2.4 has no fundamentals features in the first model. |
| BQ-18 | Where does India full-market daily history with delisted stocks come from (ADR-14)? | (a) a paid exchange end-of-day licence; (b) broker history for currently listed stocks only; (c) no India backtest | [DEFAULT-29] (a) is required before any India backtest is accepted as ADR-08 evidence. Until then the pipeline is built on (b) and every result from it is labelled survivorship-biased. | India results look better than they are; a model is promoted on biased evidence. |
| BQ-19 | What is the internal order reference, given Kite's `tag` is at most 20 alphanumeric characters (F-9) and Alpaca's `client_order_id` at most 128 (F-22)? | a UUID (36 characters); one short format for both brokers | [DEFAULT-30] Exactly 20 characters from `A-Z0-9`, used as Kite `tag`, Alpaca `client_order_id`, and Upstox `tag`. | With two formats, the order path is broker-specific at the identifier level, which INV-10 warns against. |
| BQ-20 | How close to a documented rate limit does a client run? | at the limit; a fixed fraction | [DEFAULT-31] At most half of the documented limit, enforced client-side (section 8.3). A provider with no documented number gets an ASSUMPTION budget and an OPEN QUESTION, never a guessed limit. | Slower backfills than necessary. |
| BQ-48 | Which source is the India intraday primary, now that the free Fyers plan serves intraday only from 2025 (UP-40)? | (a) Upstox, free, from January 2022; (b) Fyers Prime, paid, documented archive from 3 July 2017; (c) Fyers Standard, free, about the last year | [DEFAULT-59] (a), with no intraday backup, because Fyers Standard cannot carry an event study. This departs from the text of the Owner's decision of 2026-10-17 because the premise of that text fails; the Owner confirms this or buys Prime (OQ-67). | Under (a) the event window has about 4.8 years instead of about 9.3. Under (b) the cost is INR 5,888.20 a year with GST, the depth is not settled (OQ-67), it conflicts with "no subscriptions" (UP-46), and the Fyers terms (F-82) apply to all of it. Under (c) a year or so cannot carry an event study. |
| BQ-49 | Which Upstox credential does the data client use? | (a) Analytics Token; (b) the daily OAuth token; (c) the TOTP token endpoint, unattended | [DEFAULT-60] (a). It lasts one year, needs no redirect and cannot place an order (F-87), so MB-AC-2 also holds at the credential, not only in our code. | Under (b) a human logs in every day. Under (c) OQ-46 is unresolved. If Upstox withdraws the token type, India data stops until (b) is built. |
| BQ-50 | How is Fyers used, given its token dies daily at 06:30, the documented login is a browser login, and Fyers says continuous refresh-token sessions are no longer supported (F-79, F-103)? | (a) human-started pulls only, on a non-trading app; (b) a scheduled job with scripted login; (c) a scheduled job on a refresh token | [DEFAULT-61] (a). Fyers has no scheduled job and no scripted login, and any Fyers app is a non-trading app, which cannot place an order (F-104). No Fyers client is built until OQ-68 is answered for Fyers. | Under (b) a scripted login is outside the documented means, and F-82 section 3 allows access to be terminated for that. Under (c) the refresh flow is absent from the API reference and the notice withdraws it for automated strategies; whether that reaches a non-trading app is not stated (OQ-74). If it does not, C3 rises and the ranking in section 6.2 can flip. |
| BQ-51 | How are India bars stored, given [DEFAULT-26] requires raw bars and Fyers serves adjusted ones (F-84)? | (a) store each complete fetch as an immutable snapshot, labelled by basis; (b) reject the source; (c) reverse the adjustment ourselves | [DEFAULT-62] (a). A snapshot is never overwritten, and two snapshots are never joined across a corporate action. Each fetch re-requests the last 5 sessions [ASSUMPTION A-83], so a restatement shows up as a difference. After a corporate action the instrument's history is fetched again as a new snapshot. Upstox is `UNSTATED` until OQ-69 answers. [DEFAULT-26] stays the target and is not met for India. Fyers snapshots, if OQ-68 ever allows them, are deleted on termination (F-82 section 15), so "never overwritten" does not mean kept for ever; the retention rule is P2.1's. | Under (b) India has no bars at all. Under (c) our reversal is unverifiable against a source. If the snapshot rule is skipped, a later fetch silently restates history under a stored model (ADR-07 T-3). |
| BQ-52 | May Upstox fundamentals, news and sector fill the empty India rows? | (a) yes, each with its stated limit; (b) leave them UNFILLED | [DEFAULT-63] (a) for corporate actions, news and sector, as PROVISIONAL. Fundamentals are named but BLOCKED, because the response carries a period label and no filing date, so it cannot be point-in-time (F-88, ADR-04). | Under (b) the rows stay empty though a documented source exists. If the rows are used without their limits, a backtest sees figures before they were public. |
| BQ-53 | When does the dormancy guard alert, and what counts as activity? | a fixed number of days inside the 12-month rule | [DEFAULT-64] 300 days since the last recorded trade or KYC update per account, and again at 330. A login, API call or token generation does not count until OQ-71 says so. Dormancy is treated as permanent until a human acts (PE-20). A signals-only v1 never trades, so the guard is the normal path, not a rare one. | A later alert leaves less time to reactivate. If a yearly token login reset the clock, the alert might never fire while the account went dormant. |

## 2. Problems in the upstream material

RULE-5 requires this section.

| # | Where | Problem | Handling in this spec |
|---|-------|---------|-----------------------|
| UP-11 | [DEFAULT-4], ADR-13 HP-4, ADR-10 REC-4: "every open position has a stop resting at the broker" | In India no stop *order* rests across sessions. A GTT is a trigger held by Zerodha, not an exchange order. Per F-10 and F-11: it places a limit order when triggered, it triggers once only, only during market hours, it is cancelled on a corporate action with more than 2% impact, it expires after 365 days, an account may hold 500, and a sell GTT on holdings needs DDPI/POA or a per-day TPIN authorisation. Execution after the trigger is not guaranteed. REC-4 treats the stop as protection; in India it is weaker than that. | BQ-11, [DEFAULT-22]. The gap is stated in section 5.3 and in PE-9. The constitution's Q3 edge case ("the broker does not support a resting stop: not eligible for entry") would, read strictly, make every Indian stock ineligible. Owner ruling needed: OQ-27. |
| UP-12 | Constitution Q1, RISK-13: "an exit sent as a market order needs no market value" | Zerodha rejects an API market order, and an `SL-M` order, whose market protection is 0 (F-16, F-18). Upstox does the same (F-41). An Indian "market" exit through the API is therefore bounded by a protection percentage and can remain unfilled. | Recorded as PE-10. P3.4 must treat an India emergency exit as possibly unfilled and must re-check it. |
| UP-13 | ADR-12, [DEFAULT-16]: "only settled cash is read" | Alpaca's documented account object has no field described as settled cash (F-24). The rule cannot be coded as written. | BQ-16, [DEFAULT-27]. OQ-33. |
| UP-14 | Constitution C-6, OQ-7 | Confirmed. A Kite access token expires at 06:00 the next day, described by Zerodha as a regulatory requirement; a refresh token is given only to approved platforms (F-6). Zerodha forum staff state a manual login at least once a day is an exchange requirement and that automating it is not recommended (F-20, search excerpt only). | [DEFAULT-6] stands. The human login window is 06:00 to 09:15 `Asia/Kolkata`, 3 hours 15 minutes. HITL-7 is real. The terms text is OQ-28. |
| UP-15 | INV-9 "static IP"; ADR-10 recovery | Zerodha requires a registered static IP for API order placement. The registration holds at most two addresses and allows one change per calendar week (F-16, F-17). A VM restored on a new address cannot place India orders for up to a week unless the address is portable or already registered as the secondary. ADR-10's RTO of 4 hours does not account for this. | D-17: the recovery address is registered as the secondary before go-live. P6.4 must reserve it. Zerodha's own pages disagree on the effective date (1 April 2026 in the article, 1 April 2025 in the FAQ): OQ-29. |
| UP-16 | INV-9 "live-like testing"; P6.5 paper trading | Zerodha has no sandbox (F-16). India cannot be paper-traded at the broker. Alpaca paper trading does not simulate queue position, market impact, dividends or regulatory fees, and fills 10% of eligible orders partially at random (F-32). | Recorded for P5.3 and P6.5: India paper trading needs our own fill simulator; US paper results overstate fill quality. |
| UP-17 | ADR-14: "P0.2 must find a data source with delisted-stock history for both markets" | US: found in principle, not confirmed (Massive ticker reference has `active`, `delisted_utc` and a point-in-time `date` parameter, F-51; whether bars are served for delisted tickers is OQ-38). India: not found. Kite's instrument master lists live instruments only (F-13). NSE's website terms prohibit automated collection (F-63, search excerpt), so the public bhavcopy files are not a lawful automated source without a licence. | BQ-18, [DEFAULT-29]. OQ-39. This is the main reason the spec stays DRAFT. |
| UP-18 | STACK-1: "DeepSeek (primary LLM) + GPT-4o-mini (fallback)" | DeepSeek's pricing page lists two models, `deepseek-flash` and `deepseek-v4-pro`, and says legacy names are still accepted but served by a newer model (F-57). A name that is silently re-pointed changes model behaviour with no change on our side. GPT-4o-mini has one snapshot, dated 2024-07-18, and no shutdown date on the page read (F-60). | D-18: the DeepSeek model identifier is `deepseek-flash`, and the served model version returned in each response is recorded with the decision. A change of served version is treated like ADR-07 T-3 for the LLM path (P4.2 owns the rule). OQ-43, OQ-44. |
| UP-19 | P0.2 prompt SCOPE (Interactive Brokers, Upstox) and OUTPUT ("a primary and a backup per capability") against ADR-10 ("no backup broker") | The prompt asks for a backup per capability; ADR-10 decides there is no backup broker. | For broker execution the "backup" column is a named cold alternate: evaluated, not integrated, not funded. Activating one is a new ADR and HITL-6. |
| UP-20 | P0.2 prompt DELIVERABLE | Names `docs/specs/SPEC-P0.2-PROVIDERS.md`, a historical path (N-2). N-5 maps it to `docs/new specs/`. The run instruction for this conversation names a third path. | Written to `paste-ready/outputs/P0.2-CLAUDE.md` as instructed. Moving it under `docs/new specs/` is the Owner's step. |
| UP-21 | F-3 (P0.1): "all accounts are set up as margin accounts" | Alpaca's own commission disclosure refers to "self-directed individual cash brokerage accounts" (F-37, search excerpt), and the account configuration accepts `max_margin_multiplier` of `"1"` (F-25). Alpaca's statements about cash accounts are not consistent across pages. | Not resolved. OQ-33. UP-4 and OQ-14 remain open. |
| UP-22 | OQ-6 (Alpaca from India) | Alpaca's "countries" support article, dated February 2026, contains no country list and refers the reader to support (F-38). Alpaca's documentation site metadata lists separate documentation sets named "Alpaca India - Domestic" and "Alpaca India - GIFT City"; their content was not read. | OQ-6 stays open and is widened: OQ-35. |
| UP-23 | A-26 (session times) | Partly confirmed. NYSE core session 09:30 to 16:00 ET, early close 13:00 (F-61). NSE normal market 09:15 to 15:30, closing session 15:40 to 16:00 (F-62, search excerpt). Two NSE pages describe the close of pre-open order collection differently. | A-26 arithmetic stands. OQ-49 for the pre-open detail and the India holiday list. A-27 (settlement) was not verified: OQ-48. |
| UP-24 | ADR-13 "LLM affordability" and ADR-04 "news" | No verified news source exists for India (section 6.2). INV-10 forbids "US-only by accident". | The LLM news path is declared US-scoped until an India source is selected (ADR-11 edge case: a market-scoped feature must be declared). OQ-40. v0.2: India has a candidate with a 7-day window (SEL-12, F-89); the declaration stands until OQ-68 and OQ-76 close. |
| UP-25 | Constitution U-5 (sector taxonomy) | No licensed-free taxonomy was verified for either market. US SIC codes appear in EDGAR data (F-64, secondary). Alpaca's asset object has no sector and no security-type field, so it cannot tell common stock from an ETF or a depositary receipt (F-33), which ADR-05 requires. | Instrument class for the US comes from the Massive ticker `type` field (F-51; code list unverified, OQ-38). Sector taxonomy is UNFILLED for both markets: OQ-40, OQ-41. RISK-2 cannot be enforced until it is filled. v0.2: India has a candidate (SEL-14, F-88); the US row is unchanged. |
| UP-40 | Owner decision of 2026-10-17 (root `DECISIONS.md`, #68), which also "closes OQ-14" | "Fyers: intraday from 3 July 2017, free" is true of the archive and not of the free plan. The Standard plan serves "1 year (from 2025)" of intraday and "5 years (from 2021)" of daily, each resetting yearly; the same page set says 3 July 2017 and "unlimited" symbols, and also caps Data APIs at 5,000 requests a day (F-77, F-78). Prime is paid, by waitlist (F-83). Fyers' Standard and Prime rate limits took effect on 2026-10-16, and the notice says Prime gets broader history (F-98); it does not date the Standard history window, but the #68 figure may have been right when read. The stated reason for choosing Fyers does not survive on the free plan. | BQ-48, [DEFAULT-59], OQ-67. The decision as written cannot be reproduced on the free plan. Free multi-year intraday does exist at Upstox from January 2022 on all plans (F-43, F-90), but that is a substitution and a new decision for the Owner, not the old decision surviving; it is shorter, about 4.8 years against about 9.3. OQ-14 is closed by that fact only if the Owner accepts the substitute. |
| UP-41 | Owner decision of 2026-10-17 against Model B (2026-10-14), BO-1, MB-AC-14 | The decision and the #68 ticket drafts describe a personal system, and were made three days after the Owner chose Model B, which serves other people. **On their face the Fyers API terms give no route to a signals service for people who are not FYERS clients**: sections 2, 8 and 9 allow onward platforms only for other FYERS clients after approvals. They also limit exchange data to legitimate, fair and transparent trading, bar paper trading, gaming and virtual trading, bar third-party use of the APIs, and need written consent for databases with intent to redistribute, derivative works, distribution and public display (F-82, sections 11 and 12). A model portfolio and a published track record may fall inside those words. Section 2 does mention a platform offered to the public, but section 8 limits onward platforms to other FYERS clients after approvals, and section 9 says all end users are FYERS clients. Upstox API-specific terms were not found (F-92), but an Upstox developer states that storage and derived analytics are fine for informational use and that a monetised service needs a separate business arrangement (F-100); a forum reply is not a licence. The exchanges' own redistribution rules were not read. | MB-AC-14 is not met for India, so the Owner's decision holds for research at most, and is not compatible with Model B publication as it stands. The first question for Fyers is whether it can be used at all under Model B. This spec does not decide what those clauses mean: OQ-68, a legal question. No India row can be SELECTED. Whether a free signals service counts as monetised, and whether signals are derived analytics or a redistribution, are for the written answer. |
| UP-42 | [DEFAULT-26], D-13: "raw bars, adjustment is ours" | Fyers staff state history is adjusted for corporate actions, price and volume (F-84). Upstox pages say nothing (F-43). No raw India source is verified. | BQ-51, [DEFAULT-62]. The rule stands as the target and is recorded as unmet for India. |
| UP-43 | ADR-14; #68 open item 5 (delisted symbols) | Confirmed for the instrument masters: the Upstox next-day file excludes delisted stocks (F-91) and its `instrument_key` identifies an active instrument (F-90); its expired-instrument APIs are for derivatives and need the Upstox Plus plan (F-90). A Fyers forum reply says delisted companies are not provided (F-85, not a documentation page). Whether the Upstox archive answers for a delisted ISIN is not stated. | UP-17 and [DEFAULT-29] stand. SEL-4 runs labelled survivorship-biased and is no ADR-08 evidence. OQ-69. Free price data does not close survivorship. |
| UP-44 | #68 table: Upstox "50 req/s orders" | That is the landing-page figure. The rate-limit page gives 10 per second for regular algos and 50 only for exchange-registered ones (F-39). For data, 50 per second is a burst figure: the binding limit is 2,000 per 30 minutes, 1.11 per second on average. | THR-13 budgets the 30-minute limit. |
| UP-45 | #68 open item 4; Owner decision item 4 (daily auth per broker) | Answered. Upstox needs no daily step for read-only data (F-87). A standard access token cannot be generated on an account with no active segment (F-105); the same for the Analytics Token is not stated (OQ-71). Fyers: the token dies daily at 06:30; login is a browser login (F-79). A `refresh_token` appears in the sample response on the validate-auth-code page, but the attributes table and the login flow do not describe it, and Fyers' notice of 2026-03-10 requires 2FA once every trading day and says continuous refresh-token sessions are no longer supported (F-103). That notice addresses automated trading strategies; whether it reaches a non-trading data app is not stated. "Two brokers, two daily steps" does not arise while Fyers has no scheduled job, but each day Fyers is used is still a human step: a missed login means no Fyers data that day. | BQ-49, BQ-50, OQ-74. |
| UP-46 | Issue #2: "these replace the paid feeds"; #37 and `SPEC-P2N.13` v0.3: "no subscriptions" | True only of the India rows. The instrument files read for Upstox and Fyers list NSE, BSE and MCX, with global indices at Upstox, and no US equities (F-81, F-91), so Massive at USD 79 (SEL-3) still stands in the table. But `SPEC-P2N.13` v0.3 records "no subscriptions, at all" as an Owner instruction of 2026-10-16, and it is not in root `DECISIONS.md` or any new-run record. Massive and Fyers Prime both conflict with it, and Model B expects commercial licences to cost more (MB-RQ-6). EDGAR replaces FMP only when the SEC pause lifts. | Not applied: SEL-3 is unchanged, and Alpaca work is held until #68 lands, as issue #2 says. The Owner decides whether the instruction stands under Model B (section 0, decision 1). USD 79 is an individual-plan price, not a Model B cost (BO-1). |
| UP-47 | `SPEC-P2N.13` section 15; #37 ("SEC EDGAR is free and open") | That section records a live request to `data.sec.gov` on 2026-10-16, six days after O-16 paused direct SEC requests. No record lifts the pause or says a project contact string was configured. | This run made no SEC request. The recorded facts are re-used as SECONDARY (F-96). The Owner confirms the position: OQ-41. |
| UP-48 | `SPEC-P2N.13` F-1, called a correction, and its ladder row "Alpaca bundled Benzinga: REST poll" | F-1 is fair as to Benzinga's product. It is not an error in what Alpaca said: the 130+ and 2015 figures were Alpaca's own. Alpaca's 2022 announcement itself lists 600 to 900 headlines a day and a WebSocket (F-99), so the headline stream and push were never Benzinga-only. Benzinga's page also disagrees with itself on volume (F-94). | Section 5.2 records both. OQ-72 is narrowed. |

## 3. Evidence register

F-6 to F-64 were retrieved on 2026-10-13, F-77 to F-95 and F-98 to F-108 on 2026-10-30. F-96 is an
earlier record, not re-read; F-97 is an earlier record of which only the Fyers KB article was re-read. F-39 and F-43 were read again on 2026-10-30 and are unchanged. Levels:
- PRIMARY_FULL: the provider's own page, whole page text read in this conversation.
- PRIMARY_EXTRACT: the provider's own page, read through an automated question-answering fetch.
  The page was reached; it was not read line by line. A full read is owed by the phase named.
- SEARCH_EXCERPT: only a search-result excerpt of the provider's page was seen.
- SECONDARY: a third party's statement about the provider.

| # | Fact (summary; detail in section 5) | Source URL | Level | Full read owed by |
|---|--------------------------------------|------------|-------|-------------------|
| F-6 | Kite login flow, token fields, 06:00 expiry, refresh token for approved platforms only, margin fields | https://kite.trade/docs/connect/v3/user/ | PRIMARY_EXTRACT | P3.1 |
| F-7 | Kite rate limits: quote 1/s, historical 3/s, order placement 10/s, others 10/s; 400 orders/min; 5,000 orders/day; 25 modifications per order | https://kite.trade/docs/connect/v3/exceptions/ | PRIMARY_FULL | done |
| F-8 | Kite exception names and HTTP codes | https://kite.trade/docs/connect/v3/exceptions/ | PRIMARY_FULL | done |
| F-9 | Kite orders: varieties, order types, products, validity, parameters, `tag`, statuses, response fields | https://kite.trade/docs/connect/v3/orders/ | PRIMARY_EXTRACT | P3.1 |
| F-10 | Kite GTT API: `single` and `two-leg`, order type `LIMIT`, statuses, `expires_at` | https://kite.trade/docs/connect/v3/gtt/ | PRIMARY_EXTRACT | P3.4 |
| F-11 | Zerodha GTT behaviour: 365 days, 500 active, single use, market hours only, cancelled on corporate actions, TPIN/DDPI | https://support.zerodha.com/category/trading-and-markets/charts-and-orders/gtt/articles/what-is-the-good-till-triggered-gtt-feature | PRIMARY_EXTRACT | P3.4 |
| F-12 | Kite WebSocket: URL, modes, 3,000 instruments per connection, 3 connections per key, paise encoding | https://kite.trade/docs/connect/v3/websocket/ | PRIMARY_EXTRACT | P3.1 |
| F-13 | Kite historical candles: endpoint, intervals, candle layout, `+0530` timestamps, instrument master lists live instruments only | https://kite.trade/docs/connect/v3/historical/ | PRIMARY_EXTRACT | P2.1 |
| F-14 | Kite instrument dump and quote endpoints: columns, daily generation, 500/1,000 instruments per call | https://kite.trade/docs/connect/v3/market-quotes/ | PRIMARY_EXTRACT | P2.1 |
| F-15 | Kite holdings and positions fields; sell needs POA or depository authorisation | https://kite.trade/docs/connect/v3/portfolio/ | PRIMARY_EXTRACT | P3.1 |
| F-16 | Zerodha API FAQ: static IP rules, 10 orders/s per client with HTTP 429, market protection mandatory, plans (Personal free, Connect INR 500/month), no sandbox | https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/kite-connect-api-faqs | PRIMARY_EXTRACT | P3.1, P6.3 |
| F-17 | Zerodha static-IP article: effective 1 April 2026, one primary and one optional secondary address, one change per calendar week, order placement only | https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/static-ip | PRIMARY_EXTRACT | P6.3 |
| F-18 | Zerodha staff forum post: only order endpoints are IP-checked; above 10 orders/s needs exchange registration; `SL-M` needs market protection; slicing capped at 10 | https://kite.trade/forum/discussion/15912/preparing-to-comply-with-sebis-retail-algo-rules-static-ip-ratelimits-order-types | PRIMARY_EXTRACT | P6.3 |
| F-19 | Zerodha charges for equity delivery and intraday | https://zerodha.com/charges/ | PRIMARY_EXTRACT | P5.3 |
| F-20 | Zerodha staff: a manual login at least once a day is an exchange requirement; automating login is not recommended | https://kite.trade/forum/discussion/16212/batch-automating-kite-login and https://kite.trade/forum/discussion/9770/automating-retrieval-of-request-token | SEARCH_EXCERPT | P3.1 |
| F-21 | Alpaca orders: types, time in force, 90-day GTC expiry, price increments, stop election, statuses, extended hours | https://docs.alpaca.markets/docs/orders-at-alpaca | PRIMARY_EXTRACT | P3.1, P3.4 |
| F-22 | Alpaca create-order reference: request fields, `client_order_id` max 128, responses 200/403/422, base URLs, order object | https://docs.alpaca.markets/reference/postorder | PRIMARY_EXTRACT | P3.1 |
| F-23 | Alpaca fractional trading: time in force `day` only, 9 decimal places, `fractionable` flag | https://docs.alpaca.markets/docs/fractional-trading | PRIMARY_EXTRACT | P3.1 |
| F-24 | Alpaca account object fields; none described as settled cash | https://docs.alpaca.markets/reference/getaccount-1 | PRIMARY_EXTRACT | P2.8 |
| F-25 | Alpaca account configuration: `no_shorting`, `suspend_trade`, `fractional_trading`, `max_margin_multiplier` in `"1"`, `"2"`, `"4"` | https://docs.alpaca.markets/reference/patchaccountconfig-1 | PRIMARY_EXTRACT | P2.8 |
| F-26 | Alpaca margin: under USD 2,000 equity limited to 1x; maintenance and interest rates | https://docs.alpaca.markets/docs/margin-and-short-selling | PRIMARY_EXTRACT | P2.8 |
| F-27 | Alpaca market-data plans: Basic (free) and Algo Trader Plus (USD 99/month); 200 and 10,000 historical calls/min; 30 WebSocket symbols on Basic; history since 2016 | https://docs.alpaca.markets/docs/about-market-data-api | PRIMARY_EXTRACT | P2.1 |
| F-28 | Alpaca stock bars reference: parameters, bar fields, response codes, rate-limit headers | https://docs.alpaca.markets/reference/stockbars | PRIMARY_EXTRACT | P2.1 |
| F-29 | Alpaca feeds: `iex` about 2.5% of volume; `sip` 100% | https://docs.alpaca.markets/docs/historical-stock-data-1 | PRIMARY_EXTRACT | P2.1 |
| F-30 | Alpaca trade-update stream: URLs, auth and listen messages, event list | https://docs.alpaca.markets/docs/websocket-streaming | PRIMARY_EXTRACT | P3.1 |
| F-31 | Alpaca market-data stream: URL pattern, 10-second auth window, error codes 400 to 410 and 500 | https://docs.alpaca.markets/docs/streaming-market-data | PRIMARY_EXTRACT | P3.2 |
| F-32 | Alpaca paper trading: fill rules and what is not simulated | https://docs.alpaca.markets/docs/paper-trading | PRIMARY_EXTRACT | P5.3, P6.5 |
| F-33 | Alpaca asset object: fields; no security-type or sector field | https://docs.alpaca.markets/reference/get-v2-assets-1 | PRIMARY_EXTRACT | P2.3 |
| F-34 | Alpaca corporate actions: endpoint, parameters, 16 types, split and dividend fields | https://docs.alpaca.markets/reference/corporateactions-1 | PRIMARY_EXTRACT | P2.1 |
| F-35 | Alpaca news: endpoint, parameters, article fields, page limit 50 | https://docs.alpaca.markets/reference/news-3 | PRIMARY_EXTRACT | P4.1 |
| F-36 | Alpaca Trading API throttle: 200 requests per minute per account | https://alpaca.markets/support/usage-limit-api-calls | SEARCH_EXCERPT | P3.1 |
| F-37 | Alpaca fees: no commission; SEC fee USD 0.0000206 x trade value on sells; TAF USD 0 per share; CAT USD 0.000003 per share on buys and sells; outbound international wire USD 35 | https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf and https://alpaca.markets/support/regulatory-fees | SEARCH_EXCERPT | P5.3 |
| F-38 | Alpaca countries article (February 2026): no list of countries on the page | https://alpaca.markets/support/countries-alpaca-is-available | PRIMARY_EXTRACT | Owner, OQ-35 |
| F-39 | Upstox rate limits per API group | https://upstox.com/developer/api-documentation/rate-limiting/ | PRIMARY_FULL | done |
| F-40 | Upstox authentication and token: OAuth flow, TOTP token endpoint, 03:30 expiry, `extended_token` | https://upstox.com/developer/api-documentation/authentication/ and https://upstox.com/developer/api-documentation/get-token/ | PRIMARY_EXTRACT | only if activated |
| F-41 | Upstox place order v3: fields, `tag` max 40, error codes, market protection | https://upstox.com/developer/api-documentation/v3/place-order/ | PRIMARY_EXTRACT | only if activated |
| F-42 | Upstox GTT: limit order on trigger, valid up to one year, up to three rules | https://upstox.com/developer/api-documentation/place-gtt-order/ | PRIMARY_EXTRACT | only if activated |
| F-43 | Upstox historical candles v3: availability and per-request range by unit | https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/ | PRIMARY_FULL (code samples excluded; read in full on 2026-10-30) | done |
| F-44 | Upstox market feed v3: protobuf, modes, subscription and connection limits | https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ | PRIMARY_EXTRACT | only if activated |
| F-45 | Upstox: a sandbox host exists; APIs are free; INR 10 per order | https://upstox.com/developer/api-documentation/api-overview/ and https://upstox.com/trading-api/ | SEARCH_EXCERPT | only if activated |
| F-46 | IBKR Web API: 10 requests/s global, per-endpoint limits, HTTP 429 and a 10-minute penalty box, nightly reset about 01:00 regional time, order endpoint path | https://www.interactivebrokers.com/campus/ibkr-api-page/web-api-trading/ | PRIMARY_EXTRACT | only if activated |
| F-47 | IBKR India account structures and commissions (US fixed USD 0.005/share, minimum USD 1.00; NSE INR 6 to INR 20 per order) | https://www.interactivebrokers.co.in/en/accounts/individual-account-india.php and https://www.interactivebrokers.com/en/pricing/commissions-stocks.php | SEARCH_EXCERPT | only if activated |
| F-48 | Massive stock plans: Basic USD 0 (5 calls/min, 2 years, end of day); Starter USD 29; Developer USD 79; Advanced USD 199; individual use | https://massive.com/pricing | PRIMARY_EXTRACT | P0.3 |
| F-49 | Polygon.io was renamed Massive; `api.polygon.io` keeps working "for an extended period"; `api.massive.com` runs in parallel | https://massive.com/blog/polygon-is-now-massive | SEARCH_EXCERPT | P2.1 |
| F-50 | Massive aggregates: path, parameters, `adjusted` defaults to true, limit default 5,000 and maximum 50,000, bar fields | https://massive.com/docs/rest/stocks/aggregates/custom-bars | PRIMARY_EXTRACT | P2.1 |
| F-51 | Massive tickers: path, `active`, point-in-time `date`, `delisted_utc`, `type`, limit maximum 1,000 | https://massive.com/docs/rest/stocks/tickers/all-tickers | PRIMARY_EXTRACT | P2.1, P2.3 |
| F-52 | Finnhub: HTTP 429 on excess; 30 calls/s cap on top of every plan; token in query or `X-Finnhub-Token` header | https://finnhub.io/docs/api/rate-limit | PRIMARY_EXTRACT | P4.1 |
| F-53 | Finnhub plans: Free (60 calls/min, US, company news 1 year, 50 WebSocket symbols); All-In-One USD 3,500/month; both "Personal Use" | https://finnhub.io/pricing | PRIMARY_EXTRACT | P0.3 |
| F-54 | FMP plans: Basic USD 0 (250 calls/day, 500 MB); Starter (300 calls/min, 5 years, US, 20 GB); Premium USD 99 (750 calls/min, 30 years, US/UK/Canada, 50 GB); Ultimate (3,000 calls/min, global, 150 GB); display or redistribution needs a separate agreement | https://site.financialmodelingprep.com/developer/docs/pricing | PRIMARY_EXTRACT | P0.3 |
| F-55 | FRED API terms: no numeric limit; required notice; third-party copyrighted series; licence revocable | https://fred.stlouisfed.org/docs/api/terms_of_use.html | PRIMARY_EXTRACT | P2.1 |
| F-56 | FRED `series/observations`: URL, parameters, observation fields, vintage support | https://fred.stlouisfed.org/docs/api/fred/series_observations.html | PRIMARY_EXTRACT | P2.1 |
| F-57 | DeepSeek models and prices: `deepseek-flash`, `deepseek-v4-pro`; peak and off-peak prices; 1M context | https://api-docs.deepseek.com/quick_start/pricing | PRIMARY_EXTRACT | P0.3, P4.2 |
| F-58 | DeepSeek rate limiting is by account-level concurrency; HTTP 429; keep-alive lines; 10-minute server timeout | https://api-docs.deepseek.com/quick_start/rate_limit | PRIMARY_EXTRACT | P4.2 |
| F-59 | DeepSeek error codes 400, 401, 402, 422, 429, 500, 503 | https://api-docs.deepseek.com/quick_start/error_codes | PRIMARY_EXTRACT | P4.2 |
| F-60 | OpenAI `gpt-4o-mini`: USD 0.15 / 0.075 / 0.60 per 1M input / cached input / output tokens; 128,000 context; 16,384 output; snapshot `gpt-4o-mini-2024-07-18` | https://developers.openai.com/api/docs/models/gpt-4o-mini | PRIMARY_EXTRACT | P0.3, P4.2 |
| F-61 | NYSE core session 09:30 to 16:00 ET; early close 13:00 ET; 2026 and 2027 holidays | https://www.nyse.com/markets/hours-calendars | PRIMARY_EXTRACT | P2.1 |
| F-62 | NSE timings: pre-open from 09:00, normal market 09:15 to 15:30, closing session 15:40 to 16:00 | https://www.nseindia.com/static/market-data/market-timings | SEARCH_EXCERPT | P2.1 |
| F-63 | NSE website terms prohibit systematic or automated data collection; NSE sells end-of-day and historical data through NSE Data & Analytics | https://www.nseindia.com/static/nse-terms-of-use and https://www.nseindia.com/static/market-data/eod-historical-data-subscription | SEARCH_EXCERPT | P2.1 |
| F-64 | SEC EDGAR: at most 10 requests per second per user; a `User-Agent` header naming the requester and a contact address is required; JSON endpoints for submissions and company facts | https://tldrfiling.com/blog/free-sec-edgar-api-guide/ and https://sec-edgar-api.readthedocs.io/ | SECONDARY | Owner lifts pause, then P2.1 |
| F-77 | Fyers plans: Standard and Prime request limits, history windows, socket limits, error -429, blocking after more than 3 per-minute breaches in a day | https://fyers.in/api-docs/v3/getting-started/plans-and-limits/ | PRIMARY_FULL | done |
| F-78 | Fyers `GET /data/history`: parameters, resolutions, 100-day and 366-day windows, data from 3 July 2017, plan limits, completed-candle rule; `Retry-After` in the guide's sample | https://fyers.in/api-docs/v3/api/market-data/historical-data/ and https://fyers.in/api-docs/v3/getting-started/guides/work-with-historical-market-data/ | PRIMARY_FULL | done |
| F-79 | Fyers auth: individual app, browser login, auth code, `POST /api/v3/validate-authcode`, `appIdHash`, header form, expiry at 6:30 AM daily, individual app usable only by its creator. The attributes table lists `access_token` only; the page's sample response also shows `refresh_token` | https://fyers.in/api-docs/v3/api/authentication/ and its individual-app pages | PRIMARY_FULL (the first read excluded code samples; the sample was then read in the page HTML) | OQ-74 |
| F-80 | Fyers API standards and error codes: envelope, HTTP codes, codes -8, -15, -16, -17, -50, -300, -352, -360, -429 | https://fyers.in/api-docs/v3/api/api-standards/ and https://fyers.in/api-docs/v3/api/appendix/common-api-error-codes/ | PRIMARY_FULL | done |
| F-81 | Fyers symbol master: public CSV per segment, columns including lot size, tick size, ISIN, symbol ticker | https://fyers.in/api-docs/v3/api/market-information/symbol-master/symbol-master-file/ | PRIMARY_FULL | done |
| F-82 | Fyers API terms, read in full. Section 2: personal use, or a trading platform offered onward, within regulations. Sections 8, 9: platforms for other FYERS clients after approvals; end users are exclusively FYERS clients. Section 11: no third-party use; exchange data only for legitimate, fair and transparent trading; not to be disseminated, supplied or processed for unauthorised purposes; not for developing charting or technical tools, paper trading, gaming or virtual trading. Section 12: written consent needed to build databases or copies with intent to redistribute, to copy, modify, make derivative works, sell, distribute, publicly display or sub-license, and to disclose source or ownership. Section 6: not meant for fully automated trades. Section 15: rights end automatically on non-compliance; on termination, use stops, and the clause says FYERS shall delete cached and stored content. Section 17: indemnity | https://fyers.in/terms-and-conditions-api | PRIMARY_FULL | OQ-68 |
| F-83 | Fyers Prime: INR 499 plus 18% GST a month or INR 4,990 plus 18% GST a year; rollout by waitlist; same limits as F-77 | https://fyers.in/prime | PRIMARY_FULL | OQ-67 |
| F-84 | Fyers Product Manager, 2026-02-19: historical API data is adjusted for corporate actions, both price and volume as per the ratio | https://fyers.in/community/t/are-stocks-price-and-volume-adjusted-for-corp-actions-like-splits-bonuses-dividends-etc-in-daily-and-1-min-timeframe-sourced-via-historical-api/22387 | PRIMARY_FULL (staff forum post, not documentation) | OQ-70 |
| F-85 | Fyers forum reply, August 2023: data for delisted companies is not provided; data is served for symbols in the symbol master. Author shown as an inactive member; role not confirmed | https://fyers.in/community/t/api-data-availability/12942 | SECONDARY | OQ-70 |
| F-86 | Fyers WebSockets: Data Socket and General socket; 100 and 5,000 symbols per user across connections; one instance at a time; auto-reconnect up to 50 tries; no replay described | https://fyers.in/api-docs/v3/api/websockets/websocket-overview/ | PRIMARY_FULL | only if streaming is added |
| F-87 | Upstox Analytics Token: one year, read-only, GET only, free, one per account, generated in the Developer Apps page, no static IP for market-data categories | https://upstox.com/developer/api-documentation/analytics-token/ | PRIMARY_FULL | done |
| F-88 | Upstox Fundamentals: company profile with `sector`; income statement, balance sheet, cash flow, holdings, ratios by ISIN, period label only; corporate actions with name, ex or effective date, amount, ratio, event details | https://upstox.com/developer/api-documentation/fundamentals and its get-company-profile, get-income-statement and get-corporate-actions pages | PRIMARY_FULL (code samples excluded) | P2.1 |
| F-89 | Upstox News: past 7 days only; up to 30 instrument keys per request; fields heading, summary, thumbnail, article link, published time | https://upstox.com/developer/api-documentation/get-news | PRIMARY_FULL (code samples excluded) | P4.1 |
| F-90 | Upstox backtesting guide: `instrument_key` identifies an active instrument; historical candles on all plans; expired-instrument APIs need Upstox Plus and cover derivatives | https://upstox.com/developer/api-documentation/backtesting/ | PRIMARY_FULL (code samples excluded) | done |
| F-91 | Upstox instrument files: JSON by exchange, suspended list, fields `isin`, `instrument_key`, `tick_size`, `lot_size`, `security_type`; refreshed around 06:00; next-day file excludes delisted stocks | https://upstox.com/developer/api-documentation/instruments | PRIMARY_FULL (code samples excluded) | done |
| F-92 | Upstox general terms (last updated 2026-08-15): materials on the website, in a clause that opens with content on the website or delivered to you, may not be modified, reproduced, copied, stored, transmitted, distributed, used for creating works or used for commercial or public purposes without written consent. No API-specific terms were found | https://upstox.com/terms-of-use-and-privacy-policy/ | PRIMARY_FULL | OQ-68 |
| F-93 | Upstox sandbox supports place, modify and cancel order APIs only | https://upstox.com/developer/api-documentation/api-overview/ | SEARCH_EXCERPT | only if activated |
| F-94 | Benzinga Stock Market Newswire: history from 2010; 130 to 160 full-length articles and 600 to 900 real-time headlines a day; elsewhere on the page more than 200 stories and 1,000 pieces a day; REST, TCP streaming and RSS; API pull or TCP push; no price | https://www.benzinga.com/apis/cloud-product/stock-news-api/ | PRIMARY_FULL | OQ-72 |
| F-95 | Alpaca news: `source` given as an example "Benzinga"; articles can come from one or more feeds; a real-time news WebSocket exists; the sample record is a headline-only article. No start year on the pages read, and no article count in the live fetch, though a search excerpt of the same page shows "130+" | https://docs.alpaca.markets/us/reference/news-3 and https://docs.alpaca.markets/us/docs/historical-news-data | PRIMARY_FULL | OQ-72 |
| F-96 | SEC EDGAR, as recorded by the historical specs from a primary read (August 2026) and a live request (2026-10-16, UP-47): limit, User-Agent, cutoffs, index rebuilds, depth, submissions fields, 8-K items | `docs/specs/SPEC-P0.2-PROVIDERS.md` section 3.8; `docs/specs/SPEC-P2N.13-FAST-FEEDS.md` sections 2.1, 15 | SECONDARY | Owner lifts pause, then P2.1 |
| F-97 | Dormancy: no trading activity for 12 consecutive months may mark a trading account inactive under NSE and BSE circulars; reactivation within 2 years needs no re-KYC; account opening INR 0 at both brokers, no funding required. The Fyers KB article was re-read on 2026-10-30 (last updated 2025-12-26) and matches; the X2 review reports other Fyers KB pages giving 24 months, and listing qualifying activity without login | https://github.com/janvisarode35-lang/AI-Trading-Agent/issues/68 and https://support.fyers.in/portal/en/kb/articles/what-is-the-expiry-or-deactivation-period-for-trading-and-demat-accounts | SECONDARY | OQ-71 |
| F-98 | Fyers notice of 2026-10-15: from 2026-10-16 limits depend on plan, Standard without an active Prime subscription and Prime with one; Data API limits as F-77; Prime gets broader historical access | https://fyers.in/notice-board/changes-to-fyers-api-rate-limits-and-usage | PRIMARY_FULL | done |
| F-99 | Alpaca's News API announcement, February 2022, last modified 2023-07: Benzinga the only source then; 130 to 160 full-length articles; 600 to 900 real-time headlines a day; history to 2015; REST and WebSocket | https://alpaca.markets/blog/introducing-news-api-for-real-time-fiancial-news/ | PRIMARY_FULL | OQ-72 |

| F-100 | Upstox developer, forum reply of 2026-10-19 on free API use for a commercial platform: no charge for the APIs; candles may be stored with no retention limit; derived analytics and backtesting are fine for informational and educational use; once monetised, a separate business arrangement is needed, by the Business Trading API form or api@upstox.com; resale or redistribution of the raw feed is not covered by the individual API. A staff answer on a forum, not a licence | https://community.upstox.com/t/clarification-on-free-upstox-api-usage-for-a-commercial-saas-platform/18037 | PRIMARY_FULL (staff forum post, not documentation) | OQ-68 |
| F-101 | Upstox static-IP notice, effective 2026-04-01: applies to place, modify, cancel, multi-order, GTT and exit-all; other standard APIs, historical candles included, are not restricted; one primary and one secondary IP per user; changed once per calendar week, and a change invalidates existing access tokens | https://upstox.com/developer/api-documentation/announcements/algo-trading-circular | PRIMARY_FULL | only if activated |
| F-102 | A third-party catalogue says Upstox API access requires an active, non-dormant trading account | https://raw.githubusercontent.com/api-evangelist/upstox/refs/heads/main/plans/upstox-plans-pricing.yml | SECONDARY | OQ-71 |

| F-103 | Fyers notice of 2026-03-10, effective 2026-04-01, for users running automated strategies: orders only from a registered App ID on a whitelisted static IP; 2FA once every trading day; continuous refresh-token sessions no longer supported | https://fyers.in/notice-board/new-sebi-framework-for-retail-algo-trading-from-april-01-2026 | PRIMARY_FULL | OQ-74 |
| F-104 | Fyers individual apps: a trading app (orders, one per user, static IP required) or a non-trading app (data only, order placement not enabled, several allowed, no static IP). Creating either means accepting the API terms | https://fyers.in/api-docs/v3/getting-started/create-an-app/individual-app/ | PRIMARY_FULL | done |
| F-105 | Upstox developer, forum reply of 2026-10-27, on the standard API access token: its generation needs at least one active trading segment; a dormant account gets "No segments for these users are active"; reactivating the segment is enough, then a new token works for market data. A staff answer on a forum, not documentation | https://community.upstox.com/t/unable-to-generate-api-access-token-dormant-equity-segment/18269 | PRIMARY_FULL (staff forum post, not documentation) | OQ-71 |
| F-106 | Upstox error codes: `UDAPI10005` too many requests; `UDAPI100050` invalid token; `UDAPI100016` invalid credentials; `UDAPI100073` inactive `client_id`; `UDAPI100067` API not permitted with an extended token; HTTP "Too Many Requests" and "Service Unavailable" | https://upstox.com/developer/api-documentation/error-codes | PRIMARY_FULL | done |
| F-107 | Upstox Intraday Candle Data V3: candles for the current trading day, units `minutes`, `hours`, `days`; the historical page sends the current day here | https://upstox.com/developer/api-documentation/v3/get-intra-day-candle-data | PRIMARY_FULL (code samples excluded) | OQ-75 |
| F-108 | Upstox Market Holidays: holidays for the current year, or the status of a given date; `date`, `description`, `holiday_type`, `closed_exchanges`, `open_exchanges` with start and end times. Coverage of past years not stated | https://upstox.com/developer/api-documentation/get-market-holidays | PRIMARY_FULL (code samples excluded) | OQ-75 |

Count: 91 fact rows. 31 PRIMARY_FULL, 46 PRIMARY_EXTRACT, 9 SEARCH_EXCERPT, 5 SECONDARY. F-84 is a staff forum post, and F-88 to F-91 exclude code samples; each row says so.

## 4. Capabilities the design needs

Derived from P0.1. A capability not listed here is not needed in v1. Under Model B the
`broker_execution` row is deferred (MB-8), and the rows below are data capabilities only.

| Capability | Why it is needed | Market scope | Frequency |
|------------|------------------|--------------|-----------|
| broker_execution | Orders, resting stops, positions, cash, reconciliation (ADR-10, ADR-12, ADR-13) | US, IN | Order windows; reconciliation each session |
| eod_bars | Daily bars for the whole listed market including delisted stocks (ADR-13 HP-1, ADR-14) | US, IN | Once per session after the close |
| intraday_bars | Minute bars for the event window of research studies (Owner decision of 2026-10-17). Research only: no published signal may depend on it, because HP-1 uses completed daily bars and Model B has no intraday signals | IN; US not selected (SEL-23) | On demand |
| instrument_master | Symbols, instrument class, tick size, lot size, listing status (ADR-05, UNI-3) | US, IN | Once per session |
| corporate_actions | Splits, bonus issues, dividends, mergers, delistings (BQ-15, ADR-13 edge case) | US, IN | Once per session |
| fundamentals | Point-in-time financial statements (ADR-04 option A) | US, IN | On filing |
| news | Text for the gated LLM packet (ADR-04, INV-4) | US, IN | Once per decision cycle |
| sector_taxonomy | RISK-2 (U-5) | US, IN | Monthly |
| calendar | Sessions, holidays, half-days (ADR-02) | US, IN | Yearly, checked each session |
| macro | Macro series for regime features (ADR-04 option A) | none | Daily or slower |
| fx_reference | Reporting figure only (ADR-15, OQ-22) | none | Once per India day |
| llm | Gated analysis (INV-3, STACK-1) | none | At most 20 calls a day (ADR-13) |

Not needed in v1 and therefore not specified for integration: streaming market data for
decisions (HP-1 uses completed daily bars), options data, alternative data (ADR-04), a second
broker (ADR-10).

## 5. Provider fact sheets

Convention: a cell that says NOT VERIFIED names the OPEN QUESTION that resolves it. Nothing in a
NOT VERIFIED cell may be coded against.

### 5.1 Alpaca — Trading API (US broker, fixed by INV-10)

Auth. Two HTTP headers, `APCA-API-KEY-ID` and `APCA-API-SECRET-KEY` (F-22). No token lifetime
and no refresh flow are documented for Trading API keys: a key is valid until revoked. No daily
login. IP allowlisting and 2FA for API use: NOT VERIFIED (OQ-34). Paper and live use different
keys and different hosts (F-32).

Hosts (F-22, F-30): live `https://api.alpaca.markets`, paper `https://paper-api.alpaca.markets`;
streams `wss://api.alpaca.markets/stream` and `wss://paper-api.alpaca.markets/stream`.

Endpoints needed:

| Purpose | Method and path | Verified fields | Source |
|---------|-----------------|-----------------|--------|
| Place order | `POST /v2/orders` | Request: `symbol` str; `qty` str; `side` `buy`/`sell`; `type` `market`/`limit`/`stop`/`stop_limit`/`trailing_stop`; `time_in_force` `day`/`gtc`/`opg`/`cls`/`ioc`/`fok`; `limit_price` str; `stop_price` str; `extended_hours` bool, default false; `client_order_id` str, max 128; `order_class` `simple`/`bracket`/`oco`/`oto`; `position_intent`. `type` and `time_in_force` are required. `notional` is not used (BQ-13). | F-22 |
| Order object | response of the above | `id` UUID; `client_order_id` str; `symbol` str; `qty` str or null; `filled_qty` str; `filled_avg_price` str or null; `side`; `type`; `time_in_force`; `limit_price`, `stop_price` str or null; `status`; `created_at`, `updated_at`, `submitted_at` date-time; `filled_at`, `canceled_at`, `expired_at`, `failed_at`, `replaced_at` date-time or null; `expires_at`; `replaced_by`, `replaces` UUID or null | F-22 |
| Replace order | `PATCH /v2/orders/{id}` | Semantics only: `limit_price` and `stop_price` can be updated; an order in `pending_replace` rejects a cancel. Path and body fields NOT VERIFIED (OQ-34) | F-21 |
| Cancel, list, get by client id | NOT VERIFIED (OQ-34) | none | none |
| Account | `GET /v2/account` | `cash`, `buying_power`, `regt_buying_power`, `non_marginable_buying_power`, `equity`, `last_equity`, `multiplier`, `long_market_value`, `initial_margin`, `maintenance_margin`, `sma`, `accrued_fees`, `pending_transfer_in`: all str. `trading_blocked`, `account_blocked`, `trade_suspended_by_user`: bool. `status`, `currency`: str. `last_equity` is equity at 16:00:00 ET of the previous trading day. | F-24 |
| Account configuration | `PATCH /v2/account/configurations` | `no_shorting` bool; `suspend_trade` bool ("if true, new orders are blocked"); `fractional_trading` bool; `max_margin_multiplier` str in `"1"`, `"2"`, `"4"`; `trade_confirm_email` `all`/`none`; `ptp_no_exception_entry` bool. Path taken from the reference page identifier; exact path NOT VERIFIED (OQ-34) | F-25 |
| Assets | `GET /v2/assets` | Query: `status`, `asset_class` (default `us_equity`), `exchange`, `attributes`. Object: `id`, `class`, `exchange` in `AMEX`/`ARCA`/`BATS`/`NYSE`/`NASDAQ`/`NYSEARCA`/`OTC`/`CRYPTO`, `symbol`, `name`, `status` `active`/`inactive`, `tradable`, `marginable`, `shortable`, `fractionable` bool, `attributes` list, `cusip` str or null | F-33 |
| Positions, calendar, clock | NOT VERIFIED (OQ-34, OQ-36) | none | none |
| Trade updates | stream `trade_updates` | Auth message: a JSON object with `action` = `"auth"`, `key` = the key id and `secret` = the secret key; listen message `{"action":"listen","data":{"streams":["trade_updates"]}}`. Events: `new`, `fill`, `partial_fill`, `canceled`, `expired`, `done_for_day`, `replaced`, `rejected`, `pending_new`, `stopped`, `pending_cancel`, `pending_replace`, `calculated`, `suspended`, `order_replace_rejected`, `order_cancel_rejected`, `accepted`. `fill` and `partial_fill` carry `timestamp`, `price`, `qty`, `position_qty`. JSON or MessagePack; the paper stream uses binary frames. | F-30 |

Rate limits. 200 requests per minute per account, paper and live counted separately (F-36,
SEARCH_EXCERPT; documented, not empirical). Burst and per-endpoint limits: none documented in the
pages read. The 429 body for trading endpoints: NOT VERIFIED (OQ-34). The market-data reference
documents headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (F-28);
whether trading endpoints send them is NOT VERIFIED.

WebSocket. Connection limit, heartbeat and replay after reconnect are not covered on the page
read (F-30). Design rule D-14: the stream is never the record. After any disconnect, and at
least once per session, order and position state is read over REST and compared (P5.5).

Order specifics (F-21, F-22, F-23):
- Types: `market`, `limit`, `stop`, `stop_limit`, `trailing_stop`. A `stop` becomes a market
  order when elected and does not guarantee a price. A `stop_limit` that gaps through its limit
  stays open.
- Stop election: on the consolidated print; a sell stop elects on a trade at or below the stop
  price that is not outside the NBBO. Trailing stops do not trigger outside regular hours.
- Time in force: `day` (cancelled after the closing auction), `gtc`, `opg` (rejected between
  09:28 and 19:00 ET), `cls` (rejected between 15:50 and 19:00 ET), `ioc`, `fok`.
- GTC lifetime: cancelled automatically 90 days after creation; the cancel job runs at 16:15 ET
  on that date; `expires_at` gives the date.
- Price increments: at or above USD 1.00, at most 2 decimal places; below USD 1.00, at most 4.
  A violation is rejected, error code `42210000`.
- Quantity: `qty` is a string. Fractional quantities are allowed only for `day` orders; the
  reference page says "fractional only for market and day orders" while the fractional page says
  limit, stop and stop-limit are supported with `day`. The two pages disagree; BQ-13 avoids the
  question by using whole shares.
- Minimum and maximum quantity: NOT VERIFIED (OQ-34).
- Idempotency: `client_order_id`, max 128 characters, described as unique. Charset and the
  response to a duplicate: NOT VERIFIED (OQ-34).
- Amend: replace through `PATCH`; an order placed with `notional` cannot be replaced.
- Partial fills: status `partially_filled`; stream event `partial_fill` with cumulative
  `position_qty`.
- Corporate actions: non-marketable GTC limit orders are price-adjusted; "do not reduce" is not
  supported for GTC. Treatment of a GTC `stop` on a split: NOT VERIFIED (OQ-34). ADR-13 already
  cancels and re-decides orders across a corporate action; the same rule is applied to resting
  stops (PE-11).
- Statuses: `new`, `partially_filled`, `filled`, `done_for_day`, `canceled`, `expired`,
  `replaced`, `pending_cancel`, `pending_replace`, `accepted`, `pending_new`,
  `accepted_for_bidding`, `stopped`, `rejected`, `suspended`, `calculated`, `held`.
- Rejections documented: HTTP 403 "buying power or shares is not sufficient"; HTTP 422 "input
  parameters are not recognized"; `42210000` sub-penny; extended-hours order that is not a
  `day`/`gtc` limit; `opg`/`cls` outside their windows; non-limit order on an IPO symbol before
  its first trade; "requested asset is not fractionable". A complete rejection code list is not
  published on the pages read: OQ-34.

Account and margin (F-24, F-25, F-26). Equity under USD 2,000 is limited to 1x buying power.
Margin interest 6.50% a year for non-elite users, charged on the end-of-day debit balance. No
"settled cash" field (UP-13). Settlement cycle: NOT VERIFIED (OQ-48).

Failure modes. Paper differs from live (F-32): fills only when marketable against the NBBO; 10%
of eligible orders get a random partial fill; order size is not checked against quoted size;
queue position, market impact, latency slippage, dividends and regulatory fees are not
simulated. Known outages and maintenance windows: NOT VERIFIED (no status-page read; OQ-34).

Cost (F-37, SEARCH_EXCERPT). No commission on US-listed equities through the API. Pass-through:
SEC fee USD 0.0000206 x trade value on sells; FINRA TAF listed as USD 0 per share; CAT
USD 0.000003 per executed share on buys and sells; fees are rounded up to the cent. Outbound
international wire USD 35.

Legal. Eligibility of an Indian resident: NOT VERIFIED (OQ-35, OQ-14). Customer agreement terms
on automated trading: NOT VERIFIED (OQ-37).

### 5.2 Alpaca — Market Data API (US bars backup, corporate actions, news)

Auth. Same two headers as trading, or HTTP Basic (F-28). Host `https://data.alpaca.markets`;
sandbox `https://data.sandbox.alpaca.markets`.

Plans (F-27): Basic, free: real-time IEX only, 200 historical calls/min, 30 WebSocket symbols,
no historical data from the latest 15 minutes. Algo Trader Plus, USD 99/month: all US exchanges,
10,000 calls/min, unlimited symbols. History since 2016 on both.

Bars (F-28): `GET /v2/stocks/bars`.

| Parameter | Type | Default | Range and notes |
|-----------|------|---------|-----------------|
| `symbols` | str, comma-separated | required | none stated |
| `timeframe` | str | required | `1Day` for this design |
| `start`, `end` | RFC 3339 or `YYYY-MM-DD` | start of current day; now, or now minus 15 minutes without real-time access | inclusive |
| `limit` | int | 1000 | 1 to 10,000; counts data points across all symbols |
| `adjustment` | str | `raw` | `raw`, `split`, `dividend`, `spin-off`, `all`; comma-combinable |
| `asof` | `YYYY-MM-DD` | current day | maps symbol renames; `-` disables mapping |
| `feed` | str | `sip` | `sip`, `iex`, `boats`, `otc` |
| `sort` | str | `asc` | `asc`, `desc` |
| `page_token` | str | none | from `next_page_token` |

Bar fields: `t` RFC 3339 string (examples end in `Z`; the page does not state the zone), `o`,
`h`, `l`, `c` number, `v` int64, `n` int64, `vw` number. Response codes 400, 401, 403, 429, 500.

Data specifics. `sip` is the consolidated tape, 100% of volume; `iex` is one venue, about 2.5%
of volume (F-29), and must never feed a traded-value ranking (UNI-1). Adjustment defaults to
raw. Delisted symbol coverage, survivorship and the daily-bar session definition: NOT VERIFIED
(OQ-36). Latency: not relevant to an end-of-day design; the 15-minute restriction on Basic means
the daily bar is requested no earlier than 16:15 ET.

Corporate actions (F-34): `GET /v1/corporate-actions`; parameters `symbols`, `cusips`, `types`,
`start`, `end` (inclusive, default current day), `ids`, `limit` (default 100, max 1,000),
`sort` by `process_date`, `page_token`. Types: `reverse_split`, `forward_split`, `unit_split`,
`cash_dividend`, `stock_dividend`, `spin_off`, `cash_merger`, `stock_merger`,
`stock_and_cash_merger`, `redemption`, `name_change`, `worthless_removal`,
`rights_distribution`, `partial_call`, `reorganization`, `capital_gains_distribution`.
`forward_split`: `id`, `symbol`, `cusip`, `old_rate`, `new_rate` (double), `ex_date`,
`record_date`, `payable_date`, `process_date`. `cash_dividend`: `rate` (double), `special`,
`foreign` (bool), `ex_date`, `record_date`, `payable_date`, `process_date`. The page warns that
actions may arrive late. History depth: NOT VERIFIED (OQ-36).

News (F-35): `GET /v1beta1/news`; `start`, `end`, `sort` (default `desc`), `symbols`, `limit`
1 to 50 (default 10), `include_content`, `exclude_contentless`, `page_token`. Article: `id`
int64, `headline`, `author`, `created_at`, `updated_at` (RFC 3339), `summary`, `content` (may
contain HTML), `url`, `symbols` list, `source`. The example source is Benzinga. History depth
and licence to store or to pass text to a third-party LLM: NOT VERIFIED (OQ-37).

Benzinga feed (v0.2, F-94, F-95; the two corrections of `SPEC-P2N.13` F-1). Benzinga's own newswire
page gives history **from 2010**, and **600 to 900 real-time headlines a day in addition to 130 to
160 full-length articles**. It offers **TCP push** as well as REST pull and RSS. The same page says
elsewhere that more than 200 stories and 1,000 pieces are produced each day, so treat the volume as
a vendor range. Direct pricing and a latency figure for the newswire are not published there. The
earlier record of "130+ articles a day, back to 2015" was Alpaca's statement about its own feed.
Alpaca's 2022 announcement also lists 600 to 900 real-time headlines a day and history to 2015
(F-99), and its reference sample is a headline-only article (F-95), so the evidence leans towards
Alpaca carrying headlines. That is not proof of what the feed carries today: current pages say
articles can come from one or more feeds, and a daily volume was not measured (OQ-72). History
through Alpaca is 2015, not 2010. Alpaca also documents a real-time news WebSocket. No selection
changes: the news path runs once per decision cycle, so push delivery has no use in v1.

Market-data stream (F-31), not used by any decision: `wss://stream.data.alpaca.markets/{version}/{feed}`;
authenticate within 10 seconds; errors 400 invalid syntax, 401 not authenticated, 402 auth
failed, 403 already authenticated, 404 auth timeout, 405 symbol limit exceeded, 406 connection
limit exceeded, 407 slow client, 409 insufficient subscription, 410 invalid subscribe action,
500 internal error. No replay of missed data is documented.

Legal. Redistribution and storage terms: NOT VERIFIED (OQ-37).

### 5.3 Zerodha Kite Connect (India broker, fixed by INV-10)

Auth (F-6, F-16, F-17, F-20).
- Flow: browser login at `https://kite.zerodha.com/connect/login` with query parameters `v=3` and
  `api_key`; redirect with a one-time `request_token`; `POST https://api.kite.trade/session/token`
  with `api_key`, `request_token`, `checksum` = SHA-256 of `api_key + request_token + api_secret`;
  response `access_token` (str), `user_id`, `login_time`, `exchanges`, `products`, `order_types`,
  `public_token`, `refresh_token`.
- Lifetime: the access token expires at 06:00 the next day unless invalidated earlier by logout
  or by a master logout from the web terminal.
- Refresh: `refresh_token` is "only available to certain approved platforms". An individual has
  none. Refresh cannot be automated.
- Daily manual login: required (F-20, SEARCH_EXCERPT). TOTP is mandatory for the login.
- Session conflict: `TokenException` (HTTP 403) is also raised when the user logs in to another
  Kite instance (F-8). An operator opening a second API session can invalidate the system's.
- Static IP: order placement requires a registered static IP; one primary and one optional
  secondary; one change per calendar week; IPv4 and IPv6; registered per developer account;
  shareable only within immediate family; data, order book and positions endpoints work from any
  address. An order from an unregistered address is rejected; the error body is NOT VERIFIED
  (OQ-29).
- Logout: `DELETE /session/token`.

Endpoints needed (host `https://api.kite.trade`):

| Purpose | Method and path | Verified fields | Source |
|---------|-----------------|-----------------|--------|
| Place order | `POST /orders/:variety` | `tradingsymbol`, `exchange`, `transaction_type` `BUY`/`SELL`, `order_type` `MARKET`/`LIMIT`/`SL`/`SL-M`, `quantity`, `product` `CNC`/`NRML`/`MIS`/`MTF`, `price`, `trigger_price`, `disclosed_quantity`, `validity` `DAY`/`IOC`/`TTL`, `validity_ttl` (minutes), `market_protection` (greater than 0 up to 100, or -1 for automatic), `autoslice` bool (at most 10 slices), `tag` (alphanumeric, max 20). Variety: `regular`, `amo`, `co`, `iceberg`, `auction`. Path taken from the modify and cancel paths; NOT separately verified (OQ-31) | F-9 |
| Modify | `PUT /orders/:variety/:order_id` | `order_type`, `quantity`, `price`, `trigger_price`, `disclosed_quantity`, `validity`; at most 25 modifications per order | F-9, F-7 |
| Cancel | `DELETE /orders/:variety/:order_id` | none beyond the path | F-9 |
| Order object | order book and history | `order_id` str; `exchange_order_id` str or null; `status` str; `status_message`, `status_message_raw` str or null; `tradingsymbol`, `exchange`, `transaction_type`, `order_type`, `product`, `validity`, `variety` str; `price`, `trigger_price`, `average_price` float64; `quantity`, `filled_quantity`, `pending_quantity`, `cancelled_quantity`, `disclosed_quantity` int64; `order_timestamp`, `exchange_timestamp`, `exchange_update_timestamp` str; `tag` str or null; `guid` str | F-9 |
| Trades | `GET /trades`, `GET /orders/:order_id/trades` | `trade_id`, `order_id`, `exchange_order_id`, `tradingsymbol`, `exchange`, `transaction_type`, `product` str; `average_price` float64; `filled` int64; `fill_timestamp`, `order_timestamp`, `exchange_timestamp` str | F-9 |
| GTT | `POST`, `GET`, `PUT`, `DELETE` on `/gtt/triggers` and `/gtt/triggers/:id` | `type` `single`/`two-leg`; `condition` {`exchange`, `tradingsymbol`, `trigger_values` array, `last_price`}; `orders` array of {`exchange`, `tradingsymbol`, `transaction_type`, `quantity`, `order_type` `LIMIT`, `product`, `price`}. Trigger object: `id`, `type`, `created_at`, `updated_at`, `expires_at`, `status`. Statuses: `active`, `triggered`, `disabled`, `expired`, `cancelled`, `rejected`, `deleted` | F-10 |
| Holdings | `GET /portfolio/holdings` | `quantity`, `t1_quantity`, `used_quantity`, `authorised_quantity`, `collateral_quantity` int64; `average_price`, `last_price`, `close_price`, `pnl` float64; `isin` str | F-15 |
| Positions | `GET /portfolio/positions` | `net` and `day` lists; `quantity`, `overnight_quantity`, `multiplier` int64; `average_price` float64 | F-15 |
| Margins | `GET /user/margins/:segment` | `enabled` bool; `net`, `available.cash`, `available.opening_balance`, `available.live_balance`, `available.intraday_payin`, `available.collateral`, `utilised.debits`, `utilised.delivery`, `utilised.holding_sales`, `utilised.payout` float64 | F-6 |
| Instruments | `GET /instruments` | gzipped CSV, generated once a day; `instrument_token`, `exchange_token`, `tradingsymbol`, `name` str; `last_price`, `strike`, `tick_size` float64; `lot_size` int64; `expiry`, `instrument_type`, `segment`, `exchange` str | F-14 |
| Quote | `GET /quote` (500 instruments), `/quote/ohlc` (1,000), `/quote/ltp` (1,000) | `last_price` float64; `last_trade_time` str or null; `timestamp` str; `volume` int64; `ohlc.open/high/low/close` float64; `lower_circuit_limit`, `upper_circuit_limit` float64; `depth.buy[]`, `depth.sell[]` {`price`, `orders`, `quantity`} | F-14 |
| Historical | `GET /instruments/historical/:instrument_token/:interval` | `from`, `to` as `yyyy-mm-dd hh:mm:ss`; `interval` in `minute`, `day`, `3minute`, `5minute`, `10minute`, `15minute`, `30minute`, `60minute`; candles `[timestamp, open, high, low, close, volume]`; timestamp `yyyy-mm-ddThh:mm:ss+0530` | F-13 |

Rate limits (F-7, PRIMARY_FULL; documented, not empirical):

| Scope | Limit |
|-------|-------|
| Quote | 1 request per second |
| Historical candle | 3 requests per second |
| Order placement | 10 requests per second |
| All other endpoints | 10 requests per second |
| Orders | 10 per second and 400 per minute |
| Orders per user or API key per day | 5,000, across all segments and varieties |
| Modifications per order | 25, then cancel and place again |

HTTP 429 means "too many requests to the API". The 10 orders per second is per trading account,
not per app, and requests that are blocked as invalid still count (F-16). Above 10 orders per
second a strategy must be registered with the exchange (F-18). No burst allowance and no
rate-limit headers are documented.

WebSocket (F-12): `wss://ws.kite.trade` with `api_key` and `access_token`; modes `ltp` (8
bytes), `quote` (44 bytes), `full` (184 bytes, with depth); up to 3,000 instruments per
connection and 3 connections per API key; a 1-byte heartbeat every couple of seconds when idle;
market data is binary, order postbacks and errors are text (`order`, `error`, `message`).
Prices are integers in paise: divide by 100. Reconnect guidance and replay of missed ticks or
order updates are not on the page (OQ-31). Rule D-14 applies. The Personal (free) plan excludes
live and historical data (F-16).

Data specifics.
- Adjustment of historical candles for splits, bonus issues and dividends: NOT VERIFIED (OQ-30).
- History depth: "several years"; no number (OQ-30). Maximum range per request: NOT VERIFIED.
- Delisted coverage: none. The instrument master returns only live instruments (F-13).
- Instrument identity: Zerodha recommends `exchange` plus `tradingsymbol` as the key, because
  exchanges may reuse `instrument_token` (F-14). Neither survives a rename; the internal
  instrument identifier of UNI-4 must be mapped through ISIN (`isin` is on holdings, F-15; it is
  not a column of the instrument dump as listed).
- Tick size and lot size: per instrument, from the dump, refreshed daily. No constant is
  assumed.
- Timestamp zone of order and trade timestamps: not stated on the page (OQ-30). Historical
  candles carry `+0530`.
- Tape: NSE and BSE are separate venues with separate `exchange` values; there is no
  consolidated tape. Traded value for UNI-1 is per exchange; which exchange is used is P2.3's.
- Extended hours: `amo` variety exists for after-market orders (F-9); behaviour NOT VERIFIED.

Order specifics.
- Order types: `MARKET`, `LIMIT`, `SL`, `SL-M`. Market and `SL-M` need non-zero market
  protection through the API (UP-12).
- Time in force: `DAY`, `IOC`, `TTL` (minutes). There is no GTC. GTT is the multi-session
  mechanism: valid 365 days, 500 active per account, single use, triggers only in market hours
  (to 15:30 for non-F&O stocks, to 15:15 for F&O stocks), cancelled on corporate actions with
  more than 2% impact, sell GTT on holdings needs DDPI/POA or TPIN (F-11).
- Disagreement between Zerodha's own pages: the API reference lists `LIMIT` as the GTT order
  type (F-10); the support article says a "limit order or market order with market protection"
  is placed (F-11). OQ-27.
- Fractional shares: not offered; `quantity` is int64.
- Idempotency: none on the request. `tag` (alphanumeric, max 20) is echoed on the order and is
  the only caller-supplied identifier. `guid` appears on the order object; its guarantee is
  NOT VERIFIED (OQ-31). Rule D-15: after an unknown outcome the order book is read and matched on
  `tag` before anything is sent again.
- Amend: in place through `PUT`, 25 times per order.
- Partial fill: `filled_quantity`, `pending_quantity`, `cancelled_quantity` on the order;
  per-fill rows from the trades endpoint.
- Statuses: `OPEN`, `COMPLETE`, `CANCELLED`, `REJECTED`, plus interim `PUT ORDER REQ RECEIVED`,
  `VALIDATION PENDING`, `OPEN PENDING`, `MODIFY VALIDATION PENDING`, `MODIFY PENDING`,
  `TRIGGER PENDING`, `CANCEL PENDING`, `AMO REQ RECEIVED`.
- Rejection reasons: delivered as free text in `status_message`. No list is published on the
  pages read (OQ-32). The exception classes are the only stable taxonomy: `TokenException`,
  `UserException`, `OrderException`, `InputException`, `MarginException`, `HoldingException`,
  `NetworkException`, `DataException`, `GeneralException` (F-8).
- HTTP codes: 400, 403 (session expired), 404, 405, 410, 429, 500, 502 (order management system
  down), 503, 504 (F-8).

Failure modes. No sandbox (F-16). A 502 means the broker's order system is down while the API
answers. Known outage history and maintenance windows: NOT VERIFIED (OQ-32).

Cost. Connect plan INR 500 per month per API key, includes WebSocket and historical data;
Personal plan free, without data (F-16). Charges on trades (F-19): equity delivery brokerage
zero; STT 0.1% on buy and sell; exchange transaction charge NSE 0.00307%, BSE 0.00375%; SEBI
charge INR 10 per crore; stamp duty 0.015% on the buy side; GST 18% on brokerage, SEBI and
transaction charges; depository charge INR 15.34 per scrip on each sell day. Equity intraday:
brokerage 0.03% or INR 20 per executed order, whichever is lower; STT 0.025% on the sell side;
stamp duty 0.003% on the buy side. Whether a same-day buy and sell under product `CNC` is charged
as intraday is NOT VERIFIED (OQ-48; A-33 stays an assumption).

Legal. Kite Connect terms on automated login, data storage and redistribution: NOT VERIFIED
(OQ-28). Zerodha staff describe Kite Connect as "purely an execution platform" (forum excerpt),
which bears on using its data as a research store.

### 5.4 Upstox (India daily and intraday history, instrument master, corporate actions; execution deferred)

Role (v0.2). Data role by the Owner's decision of 2026-10-17 and [DEFAULT-59]. Order paragraphs
below are kept for any future execution phase (MB-8); no v1 code may call them (MB-AC-2), and the
client is a read-only HTTP client with a path allowlist, never the Upstox SDK ([DEFAULT-50]).

Auth for data (F-87, [DEFAULT-60]). An Analytics Token is generated by a human on the Developer Apps
page, Analytics tab. It lasts 1 year from generation; one token per account; read-only, GET only;
free; no OAuth redirect. It cannot place or modify an order. Market Quote, Historical Data, Market
Information, Fundamentals, News, WebSocket, Charges, Margins, Option Chain and IPO categories work
with no static IP; account categories (User, Orders, Portfolio and others) need a whitelisted IP. So Upstox data has **no daily human
step**; the human step is once a year (UP-45). Sent as `Authorization: Bearer` (F-90 samples). It is
a one-year credential: read from the secret store at process start, held in memory only, and never
written to a log, traceback or audit event. Replace it with the client stopped. Whether generating a
new token ends the old one at once is not stated (OQ-75). The allowlist is deny-by-default and holds
market-data paths only; the exact paths are frozen in P2.1 from the vendor pages. It is the only
barrier between this credential and the account's holdings, so a test asserts it rejects `/portfolio`,
`/user`, `/charges` and `/margins` paths, and a percent-encoded path (MB-AC-4). The match is on exact
path templates after one decode, and a path with a remaining `%` or a `.` or `..` segment is rejected.

Auth for orders, not used in v1 (F-40). OAuth: `https://api.upstox.com/v2/login/authorization/dialog` then
`POST https://api.upstox.com/v2/login/authorization/token` with `code`, `client_id`,
`client_secret`, `redirect_uri`, `grant_type=authorization_code`. A second endpoint,
`POST /v2/totp-login/authorization/token`, issues a token from header `x-api-key` and body
`totp` (6 digits) and `pin` (6 digits), for individual apps with TOTP enabled; issuing a new
token revokes the active one. The token "lasts until 3:30 AM the following day, regardless of
the time it was generated". `extended_token` is for prolonged, mainly read-only access. Whether
the TOTP endpoint may be called unattended under Upstox terms and exchange rules is NOT VERIFIED
(OQ-46); F-20 suggests the exchange requirement is broker-independent.

Rate limits (F-39, PRIMARY_FULL; per API, per user):

| Group | Per second | Per minute | Per 30 minutes |
|-------|-----------|------------|----------------|
| Order placement (place, modify, cancel, multi-order, GTT), regular algos | 10 | 500 | 2,000 |
| Order placement, exchange-registered algos | 50 | 500 | 2,000 |
| Other standard APIs (holdings, positions, funds, historical candles) | 50 | 500 | 2,000 |
| TOTP login | 1 | 10 | 60 |

Exceeding a limit "might result in temporary suspension of access". The response code is not
stated on the page (OQ-75). Limits are per API, per user. Re-read 2026-10-30, unchanged. For a data
client the binding row is 2,000 per 30 minutes, 1.11 per second on average (UP-44, THR-13).

Orders (F-41). `POST https://api-hft.upstox.com/v3/order/place`, `Authorization: Bearer`.
Fields: `quantity` int32, `product` `I`/`D`/`MTF`, `validity` `DAY`/`IOC`, `price` float,
`tag` str max 40, `instrument_token` str (for example `NSE_EQ|INE669E01016`), `order_type`
`MARKET`/`LIMIT`/`SL`/`SL-M`, `transaction_type` `BUY`/`SELL`, `disclosed_quantity` int32,
`trigger_price` float, `slice` bool, `market_protection` int32 (-1 automatic, 1 to 25; 0 is
rejected for market orders). Response `data.order_ids` list. No idempotency key. Selected error
codes: `UDAPI1154` static IP restriction; `UDAPI1158` market orders not allowed; `UDAPI1118`
maximum order limit exceeded; `UDAPI1119` tag too long; `UDAPI100074` order API available 05:30
to 00:00 IST. Header `X-Algo-Name` is required only for exchange-approved strategies.

GTT (F-42). `POST https://api.upstox.com/v3/order/gtt/place`; `SINGLE` or `MULTIPLE` with
rules `ENTRY`, `TARGET`, `STOPLOSS`; an `ENTRY` rule is mandatory, so a stand-alone stop for an
existing holding is not directly expressible; "always placed as a LIMIT order"; valid up to one
year; sell legs need EDIS authorisation.

Historical (F-43, F-90). `GET https://api.upstox.com/v3/historical-candle/:instrument_key/:unit/:interval/:to_date/:from_date`.
Available on all plans.

| Unit | Interval | Available from | Maximum per request |
|------|----------|----------------|---------------------|
| `minutes` | 1 to 300 | January 2022 | 1 month for 1 to 15 minutes; 1 quarter above 15 minutes |
| `hours` | 1 to 5 | January 2022 | 1 quarter |
| `days` | 1 | January 2000 | 1 decade |
| `weeks`, `months` | 1 | January 2000 | no limit |

`to_date` is required and inclusive; `from_date` is optional; both `YYYY-MM-DD`. A range above the
limit is an error, not a truncated answer: `UDAPI1148`. Others: `UDAPI1021` bad instrument key
format, `UDAPI100011` unknown key, `UDAPI1022` missing `to_date`, `UDAPI1015` bad date order,
`UDAPI1146` bad unit, `UDAPI1147` bad interval. Candle `[timestamp, open, high, low, close, volume,
open_interest]`, timestamp ISO 8601 with `+05:30`. The current trading day is served by Intraday
Candle Data V3, units `minutes`, `hours`, `days` (F-107); when the historical endpoint starts to
carry a finished session is not stated (OQ-75), so the evening batch checks that the last returned
session is the expected one (PE-24). Corporate-action adjustment: the page says nothing (OQ-69);
treated as `UNSTATED` ([DEFAULT-62]). Delisted coverage: see below.

Calendar (F-108). Market Holidays returns the current year, or the status of one date, with
`holiday_type`, `closed_exchanges` and `open_exchanges` (start and end times). It works under the
Analytics Token's Market Information category (F-87). Past years are not stated, so whether an
empty historical session is a holiday or a gap may not be decidable for backfill (OQ-75). Only a row
that closes the exchange for trading counts as a non-session; other holiday types, such as a
settlement holiday, do not. If the calendar cannot be read, the expected session is unknown and no
India batch runs. In backfill, a session with no bars and no calendar answer is recorded as
"unknown: holiday or gap", never as a confirmed holiday, and P2.2 decides what a run may do with it.

Instruments (F-91). Gzipped JSON at `https://assets.upstox.com/market-quote/instruments/exchange/`:
`NSE.json.gz`, `BSE.json.gz`, `complete.json.gz`, `suspended-instrument.json.gz`. Equity fields:
`segment`, `name`, `exchange`, `isin`, `instrument_type`, `instrument_key`, `lot_size`,
`freeze_quantity`, `exchange_token`, `tick_size`, `trading_symbol`, `short_name`, `security_type`,
`cas_eligible`. Refreshed around 06:00, rarely during the day. Upstox recommends `instrument_key`
because `exchange_token` can be reused. CSV is deprecated; use JSON. The next-day file does not
include delisted stocks or expired contracts. The suspended list is a separate file. `security_type`
is what ADR-05 needs to separate classes; its code list was not read (OQ-75). ISIN is present, so
UNI-4 mapping is direct for a current instrument. An ISIN can change at a split, which would end
history under one `instrument_key` (OQ-69). Whether the files need a token: A-80. `tick_size` is not
to be used until its unit is confirmed: the CSV sample shows 0.05, and the JSON samples reportedly
show 5.0 (OQ-75).

Delisted coverage (F-90, F-91). The master is live-only (UP-43). `instrument_key` "uniquely
identifies an active instrument". Expired-instrument APIs need Upstox Plus and cover derivatives.
Whether a historical query with the key of a delisted ISIN returns candles is not stated (OQ-69).
Any result is labelled survivorship-biased ([DEFAULT-29]).

Fundamentals (F-88). By ISIN. `GET` company profile: `data.company_profile`, `data.sector`,
`data.sector_market_cap_inr` and `_usd`. Income statement, with query `type`, `time_period`, `fs`:
`data.type`, `data.time_period`, `data.units_in`, `data.income_statement[].category`,
`.history[].value` (INR crore; negative is a loss), `.period` (a label), `.change`;
`data.full_statement[]` is annual only. Balance sheet, cash flow, holdings, ratios and competitors
have sibling pages (not read). There is **no filing or publication date**, only a period label, so
these figures cannot be used point-in-time (ADR-04): SEL-10 is BLOCKED. Depth and vendor: OQ-73.
Errors: `UDAPI1206` invalid ISIN, `UDAPI1207` invalid type, `UDAPI1208` invalid period.

Corporate actions (F-88). By ISIN. `data[].name`, `.expiry_date` (ex or effective date), `.amount`,
`.ratio`, `.event_details[]` {`name`, `value`}. Covers dividends, bonus issues, splits and rights.
Mergers, demergers and delistings are not named. Depth: OQ-73.

News (F-89). Past 7 days only. `category` required; up to 30 instrument keys per request;
`page_number` 1 to 100, `page_size` 1 to 100. Fields `heading`, `summary`, `thumbnail`,
`article_link`, `published_time` (Unix milliseconds). The origin of the articles is not stated, and
the licence to store them or pass them to an LLM is unknown (OQ-76). With a 7-day window, history
exists only if we capture it daily. Errors `UDAPI1189`, `UDAPI1190`, `UDAPI1193`.

Market feed (F-44), not used by any decision: protobuf over WebSocket; 2 connections (5 on Upstox
Plus); up to 5,000 instrument keys in `ltpc` mode; standard ping frames; no replay documented.

Sandbox: a sandbox host exists (F-45, SEARCH_EXCERPT), and it supports place, modify and cancel
order APIs only (F-93), so it says nothing about data. Cost: APIs free; INR 10 per order (F-45).
Analytics Token free (F-87). Account opening INR 0 (F-97).

Dormancy (F-97, F-105). Applies by NSE and BSE circular, so it does not separate the two brokers.
An Upstox developer states that generating an API access token needs at least one active trading
segment; a dormant account gets "No segments for these users are active", and reactivating is
enough (F-105). That reply concerns the standard access token. Whether an Analytics Token can be
generated, or keeps working, on a dormant account is not documented (OQ-71). A third-party catalogue
says API access needs a non-dormant account (F-102). The safe reading is that dormancy may stop
Upstox data. Under Model B the account never trades, so this is the expected case: a human action
is needed inside each 12 months per account. [DEFAULT-64], PE-20.

Errors (F-106). `UDAPI10005` too many requests; `UDAPI100050` invalid token; `UDAPI100016` invalid
credentials; `UDAPI100073` inactive `client_id`; `UDAPI100067` API not permitted with an extended
token. `UDAPI100500` unexpected error.

Failure modes. Outage history and maintenance windows: NOT VERIFIED. The token is one credential
with a one-year life; expiry is a known date, so it is alerted, not discovered (PE-17).

Legal. API-specific terms were not found, though a forum post refers to "API Terms", so they may
exist. The general terms bar copying, storing or distributing website materials or using them for
commercial or public purposes without written consent (F-92); whether that reaches API data, or
news articles linked from the API, is not stated. An Upstox developer's forum reply is the best evidence so far (F-100): storing candles is
allowed with no retention limit; derived analytics and backtesting are fine for informational and
educational use; a monetised service needs a business arrangement through the Business Trading API
form or api@upstox.com; resale or redistribution of the raw feed is outside the individual API; an
individual app logs in only its owner. Under MB-AC-14 a forum reply is not a permission: OQ-68.

Static IP (F-101). Applies to order APIs only; historical candles are not restricted. So v1 needs
no static IP at Upstox.

### 5.5 Interactive Brokers (US cold alternate)

Facts (F-46, F-47). Web API: 10 requests per second globally; per-endpoint limits include
`/iserver/orders` GET 1 per 5 seconds, `/iserver/trades` GET 1 per 5 seconds,
`/portfolio/accounts` GET 1 per 5 seconds, `/iserver/marketdata/snapshot` 10 per second,
`/tickle` 1 per second, `/sso/validate` 1 per minute. Exceeding a limit returns HTTP 429 and
puts the client in a penalty box for 10 minutes. Individual clients authenticate through the
Client Portal Gateway with username and password. Brokerage endpoints are briefly unavailable
each night at about 01:00 regional time. Orders: `POST /iserver/account/{accountId}/orders`,
which can answer with an "order reply" message that must be confirmed before the order is
live. A paper account needs a funded live account. Indian residents are offered account
structures for NSE only, overseas only, or both (SEARCH_EXCERPT). US commission, fixed plan:
USD 0.005 per share, minimum USD 1.00 per order, maximum 1% of trade value.

Not verified: 2FA and daily re-login for the gateway, session lifetime, customer order
identifier, full order types and time in force, stream replay (OQ-45). The page read was last
modified 2024-12-17 per its metadata.

Assessment. The nightly reset, the 10-minute penalty box and the order-reply confirmation step
are three more states than Alpaca's order path has. IBKR stays a cold alternate.

### 5.6 Massive, formerly Polygon.io (US daily bars and instrument master, primary)

Naming (F-49, SEARCH_EXCERPT): Polygon.io is now Massive. `api.polygon.io` continues to work
for an extended period; `api.massive.com` runs in parallel. Config key `massive.base_url` holds
the host so the change is one value.

Auth: API key. Header or query form NOT VERIFIED (OQ-38).

Plans (F-48): Basic USD 0, 5 calls/min, 2 years, end of day. Starter USD 29/month, unlimited
calls, 5 years, 15-minute delayed. Developer USD 79/month, unlimited calls, 10 years, 15-minute
delayed. Advanced USD 199/month, unlimited calls, 20+ years, real time, includes financials.
"Financials & Ratios" add-on USD 29/month. All plans include reference data and corporate
actions. Plans are labelled individual use; a "non-pros only" condition is linked and was not
read (OQ-38).

Bars (F-50): `GET /v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}`;
`adjusted` bool, default true; `sort` `asc`/`desc`; `limit` default 5,000, max 50,000. Result
fields: `o`, `h`, `l`, `c`, `v`, `vw` number; `t` integer, Unix milliseconds at the start of
the window; `n` integer. Split-adjusted by default; dividend adjustment is not mentioned.
[DEFAULT-26] requires `adjusted=false`.

Tickers (F-51): `GET /v3/reference/tickers`; `ticker`, `type`, `market`, `exchange`, `active`
(default true), `date` (point-in-time: "tickers available on that date"), `limit` default 100,
max 1,000. Fields: `ticker`, `name`, `market`, `locale`, `primary_exchange`, `type`, `active`,
`currency_name`, `cik`, `composite_figi`, `share_class_figi`, `delisted_utc`,
`last_updated_utc`.

Not verified (OQ-38): whether bars are returned for delisted tickers; the meaning of
`active=false`; the list of `type` codes; the split and dividend endpoints and fields; a whole
market daily endpoint; the zone that defines a daily bar; fair-use limits behind "unlimited";
429 behaviour; WebSocket details (not needed for end-of-day).

Legal: individual, non-professional use. Storage and redistribution terms NOT VERIFIED (OQ-38).

### 5.7 Finnhub (US news backup)

Facts (F-52, F-53). Base path `/api/v1`. Auth: `token` query parameter or `X-Finnhub-Token`
header. D-16 requires the header form, because a key in a URL is written to access logs. HTTP
429 when a limit is exceeded; a cap of 30 calls per second sits on top of every plan. Free plan:
60 calls/min, US coverage, company news for 1 year with real-time updates, 50 WebSocket
symbols. All-In-One: USD 3,500/month, 900 market-data and 300 fundamental calls/min. Both are
labelled "Personal Use. Terms apply". India coverage is not mentioned on the pricing page.

Not verified (OQ-50): news endpoint path and fields, terms on storage and LLM processing, India
coverage.

### 5.8 Financial Modeling Prep (US fundamentals backup)

Facts (F-54). Basic: USD 0, 250 calls per day, 500 MB bandwidth. Starter: 300 calls/min, up to
5 years, US, 20 GB; the page displays both USD 19.00 and USD 49.00 for it, so the price is
NOT VERIFIED (OQ-47). Premium: USD 99.00, 750 calls/min, up to 30 years, US, UK and Canada,
50 GB. Ultimate: 3,000 calls/min, global, full history, 150 GB; price not shown. "Displaying or
redistributing data sourced from FMP requires a specific Data Display and Licensing Agreement."

Not verified (OQ-47): every endpoint and field; whether statements carry filing and acceptance
dates (needed for point-in-time use); India coverage; 429 behaviour.

### 5.9 SEC EDGAR (US fundamentals and filings; blocked)

Status. This run contacted no SEC host. Everything here is SECONDARY: F-64 is third-party pages,
and F-96 is what the historical specs recorded from their own primary read and a live request made
after the pause (UP-47). **None of this may be coded against.** The capability is BLOCKED by the
Owner's pause ([DEFAULT-28]) and by a second issue: the required `User-Agent` discloses a contact
identity, which the Owner must choose and approve (HITL-14 treats it like a credential). OQ-41.

Auth. No key. Every request sends a `User-Agent` naming the requester with a contact address; the
historical form is `<Company> <admin@domain>`. The Owner's personal or account address is never
used (O-16). Requests without it are commonly answered 403 (F-64). No token, no daily step, no IP
allowlist recorded.

Rate limit. 10 requests per second, documented (F-96). 429 behaviour and what a block looks like:
NOT VERIFIED (OQ-41). Cost: free.

Endpoints, recorded. `GET https://data.sec.gov/submissions/CIK##########.json`, keyed by a CIK
zero-padded to 10 digits. Recorded fields: `acceptanceDateTime`, `accessionNumber`, `act`,
`core_type`, `fileNumber`, `filingDate`, `filmNumber`, `form`, `isInlineXBRL`, `isXBRL`,
`isXBRLNumeric`, `items`, `primaryDocDescription`, `primaryDocument`, `reportDate`, `size`; a `sic`
code per F-64. 1,002 recent filings per company, plus older batches. XBRL company facts exist
(F-64); their shape is not recorded. The Atom feed `action=getcurrent`, the full-text search and
the full and quarterly indexes exist; none has a measured latency.

Data specifics, recorded. History from 1994/1995. Dissemination cutoffs 17:30 ET, and 22:00 ET for
Forms 3, 4 and 5, so a feature is lagged to the dissemination date, never the filing date.
Propagation latency after acceptance is not published. Full and quarterly indexes are rebuilt
weekly early on Saturday, so a retrieved index is snapshotted and never re-derived. Filings are not
restated in the vendor sense, which is why EDGAR scores 5 on C4. For 8-K filings `items` carries
item codes (recorded examples 2.02, 5.02, 9.01), a structured event source. US only: it does
nothing for INV-10's India side.

WebSocket: none. Delisted issuers: filings remain, per the historical record; not re-verified.

Legal. Public-domain government data per the historical record. Fair-access terms were not read.

Failure at 09:31: section 7.

### 5.10 FRED (macro, primary)

Facts (F-55, F-56). `GET https://api.stlouisfed.org/fred/series/observations`; `api_key`
(32-character lower-case alphanumeric), `series_id`, `file_type` (`json`), `observation_start`,
`observation_end`, `limit` 1 to 100,000 (default 100,000), `offset`, `sort_order`,
`realtime_start`, `realtime_end`, `vintage_dates`, `output_type` 1 to 4. Observation:
`realtime_start`, `realtime_end`, `date`, `value`, all strings. Vintage data is supported, which
is what point-in-time macro features need (ADR-04 admission rule 1). Terms: no numeric rate
limit is stated; the service "may impose limits"; the application must display "This product
uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.";
series marked as copyrighted need the owner's permission for non-personal use; the licence can
be ended at any time.

Not verified (OQ-42): the numeric rate limit and the 429 body; how a missing observation is
written in `value`; India macro series and their source.

### 5.11 News API (US)

Selected: Alpaca News (section 5.2), because it adds no account and no key. Backup: Finnhub
company news (section 5.7). Neither has verified terms for storing article text or for sending
it to DeepSeek or OpenAI (OQ-37, OQ-50); until those are answered the LLM packet may carry only
the headline, the summary and the URL is a P4.1 decision that this spec does not make. India:
v0.2 names one candidate, Upstox News, with a 7-day window and unknown origin and licence (section
5.4, SEL-12, OQ-76). Moneycontrol is named for the historical news registry (#68); it is a
publisher, not an API, and is not assessed here.

### 5.12 DeepSeek API (primary LLM, fixed by STACK-1)

Facts (F-57, F-58, F-59).

| Item | `deepseek-flash` | `deepseek-v4-pro` |
|------|------------------|-------------------|
| Served version on 2026-10-13 | DeepSeek-V4.1-Flash | DeepSeek-V4-Pro-0813 |
| Context | 1M tokens | 1M tokens |
| Maximum output | 384K tokens | 384K tokens |
| JSON output, tool calls | yes, yes | yes, yes |
| Input, cache hit, per 1M tokens (peak / off-peak) | 0.006 / 0.003 | 0.044 / 0.022 |
| Input, cache miss, per 1M tokens (peak / off-peak) | 0.3 / 0.15 | 1.32 / 0.66 |
| Output, per 1M tokens (peak / off-peak) | 1.2 / 0.6 | 3.96 / 1.98 |
| Concurrency limit | 2,500 | 500 |

Prices carry a `$` sign with no currency code (A-43). Peak hours are 01:00 to 04:00 and 06:00
to 10:00 UTC, Monday to Friday, excluding Chinese public holidays. Thinking mode is on by
default. Limits are by concurrency at account level, not by requests per minute; exceeding
returns HTTP 429. Under load the server holds the connection open with empty lines (or
`: keep-alive` comments when streaming) and closes it if inference has not started after 10
minutes. Errors: 400 invalid format, 401 authentication fails, 402 insufficient balance, 422
invalid parameters, 429 rate limit reached, 500 server error, 503 server overloaded.

Timing against the session clocks: the India decision cycle starts after 15:30 IST = 10:00
UTC, the end of a peak window; the US cycle starts after 16:00 ET = 20:00 or 21:00 UTC,
off-peak. No price is assumed for P0.3 from this; P0.3 prices at peak.

Not verified (OQ-43): base URL and auth header (not on the three pages read); whether
`deepseek-chat` is still accepted; whether a dated version can be pinned; default output limit;
data retention, training use and processing location.

A client that reads a body before the 10-minute server timeout would stall the decision cycle;
PE-14 sets our own deadline.

### 5.13 OpenAI API (fallback LLM, fixed by STACK-1)

Facts (F-60). `gpt-4o-mini`: USD 0.15 per 1M input tokens, USD 0.075 cached input, USD 0.60
output; context 128,000 tokens; maximum output 16,384 tokens; knowledge cutoff 2023-10-01;
structured outputs and function calling supported; single snapshot `gpt-4o-mini-2024-07-18`;
lowest listed tier 5,000 requests and 2,000,000 tokens per minute; no shutdown date on the page.

Not verified (OQ-44): base URL and auth header on a page read in this run; the account's tier;
shutdown date; data retention terms; 429 body.

D-18 pins the snapshot identifier, not the alias.

### 5.14 NSE and BSE (exchange facts)

- Sessions (F-62, SEARCH_EXCERPT): NSE pre-open from 09:00; normal market 09:15 to 15:30;
  closing session 15:40 to 16:00. BSE times were not retrieved (OQ-49).
- Holidays and special sessions for 2026 and 2027: not retrieved (OQ-49). v0.2: Upstox publishes a
  current-year list (F-108); the exchanges' own lists remain unread.
- Algo rules (F-2 of P0.1; F-16, F-18, F-39): the threshold of 10 orders per second is applied
  by both brokers per client; under it no strategy registration is needed (Upstox states this
  directly, citing the NSE circular of 2025-05-05); above it the strategy is registered with the
  exchange. Who generates the per-order exchange tag for an unregistered client strategy is
  still open (OQ-51, the remainder of OQ-1).
- Data (F-63, SEARCH_EXCERPT): the NSE website terms prohibit systematic or automated data
  collection. End-of-day and historical files are sold through NSE Data & Analytics. Price,
  licence terms and whether delisted securities are included: NOT VERIFIED (OQ-39).
- Tick size and lot size: read per instrument from the Upstox instrument file, and not used until
  the unit of `tick_size` is confirmed (OQ-75). Price bands are Kite quote fields, deferred. No
  exchange constant is assumed.

### 5.15 Fyers (India daily-history backup and instrument master backup; execution deferred)

Role. Backup for India daily bars on the free plan, and the backup instrument master. The Owner's
decision of 2026-10-17 names Fyers as the intraday source; UP-40 and BQ-48 say why that is not
applied on the free plan. **No Fyers client is built until OQ-68 is answered for Fyers**, so THR-14,
PE-18 and PE-19 are conditional on that. Order specifics are deferred (MB-8) and were not
researched: the documentation lists single, multi and async orders, GTT and smart orders, and its
standards page says not to replay requests blindly after a timeout (F-80). The client is read-only
HTTP with a path allowlist ([DEFAULT-50]), on a **non-trading app** (below).

Plans (F-77, F-83, F-98; pages last updated 2026-10-14; in force from 2026-10-16):

| Item | Standard, free | Prime, paid |
|------|----------------|-------------|
| Data APIs | 5 per second, 50 per minute, 5,000 per day | 10 per second, 500 per minute, 500,000 per day |
| Transaction and user APIs | 10 per second, 200 per minute, 100,000 per day | 10 per second, 500 per minute, 500,000 per day |
| Daily history | "5 years (from 2021)", last 5 years, resetting each year | all available, stated as 25+ years |
| Intraday history | "1 year (from 2025)", last 1 year, resetting each year | all available, stated as 5+ years |
| Seconds data | none | available, 30 trading days |
| Quotes | 50 symbols per request | 1,000 |
| Data Socket | 100 symbols | 5,000 |
| Price | INR 0 | INR 499 + 18% GST a month, or INR 4,990 + 18% GST a year; by waitlist |

The history page says intraday data is available from 3 July 2017; the Prime row says "5+ years".
Whether Prime reaches 2017 is not settled by those two statements (OQ-67). A Fyers KB article shows
Prime daily as "20+ years", against 25+ on the plans page. Fyers says a reached
limit may restrict requests until it resets (F-98). "From 2025" with a yearly reset does not say
whether Standard reaches back a rolling 365 days or to 1 January 2025; on 2026-10-30 that is 365 or
667 days (section 8.3, OQ-74). The KB says "Last 1 year" and "Last 5 years", which favours rolling.

App type (F-104). There are two kinds of individual app. A trading app places orders, is one per
user and needs a static IP. A non-trading app gets data only: order placement is not granted,
several are allowed, and no static IP is needed. **v1 uses a non-trading app**, so MB-AC-2 holds at
the credential for Fyers as it does for Upstox. Creating either app means accepting the API terms,
so OQ-68 comes first.

Auth (F-79). Individual app, usable only by its creator. Step 1: the user opens the login URL in a
browser with `client_id`, `redirect_uri`, `response_type=code` and a random `state`, and logs in.
Step 2: `POST /api/v3/validate-authcode` with JSON `grant_type` = `authorization_code`, `appIdHash`
= SHA-256 of `app_id:app_secret`, `code` = the auth code. Response `s`, `code`, `message`,
`access_token`. Every later request sends `Authorization: app_id:access_token`. **Tokens expire
daily at 6:30 AM** (zone not stated, A-76). Refresh: the page's sample response shows a
`refresh_token`, but its attributes table and the login flow do not describe one, and Fyers' notice
requires 2FA once every trading day and says continuous refresh-token sessions are no longer
supported (F-103). That notice addresses automated trading strategies; whether a refresh works for a
non-trading app is not stated (OQ-74). Until it is, a day on which Fyers is used needs a human
browser login ([DEFAULT-61]). Hosts for login and for `/data/history` are not on the pages read
(OQ-74).

Endpoints needed:

| Purpose | Method and path | Verified fields | Source |
|---------|-----------------|-----------------|--------|
| Historical | `GET /data/history` | `symbol` str, for example `NSE:SBIN-EQ`; `resolution` str: `1`, `2`, `3`, `5`, `10`, `15`, `20`, `30`, `45`, `60`, `120`, `180`, `240`, `1D`, `1W`, `1M`; `date_format` int: 0 epoch, 1 `yyyy-mm-dd`; `range_from`, `range_to` str; `cont_flag`, `oi_flag` int. Response `s`, `candles[]` = [epoch, open, high, low, close, volume], with open interest when `oi_flag` is 1 | F-78 |
| Symbol master | `GET https://public.fyers.in/sym_details/NSE_CM.csv`, `BSE_CM.csv` | `Fytoken`, `Symbol Details`, `Exchange Instrument type`, `Minimum lot size`, `Tick size`, `ISIN`, `Trading Session`, `Last update date`, `Expiry date`, `Symbol ticker`, `Exchange`, `Segment`, `Scrip code`, and others; `tradeStatus`, `upperPrice`, `lowerPrice` are in the JSON file only | F-81 |

Per request (F-78): up to 100 days for 1 to 240 minutes; up to 366 days for `1D`, `1W`, `1M`. The
page's "unlimited" refers to symbols, not requests: the 5,000-a-day cap still applies on Standard.
To get only completed candles, `range_to` must be earlier than the current bar by one resolution.

Rate limits (F-77, F-78, F-80, documented). Over a limit: HTTP 429 with code -429. The appendix
also lists -360 for a Standard-plan user over a limit. **More than 3 per-minute breaches in a day
block the user for the rest of that day.** The guide says a 429 can also mean a plan entitlement,
and its sample shows `Retry-After: 1` and no numeric code. PE-19, PE-21.

WebSocket (F-86), not used by any decision: Data Socket and General socket; symbol limits are per
user across connections, and a subscription over the limit is refused at connection; one instance
at a time; SDK auto-reconnect up to 50 tries. No replay of missed ticks is described; D-14 applies.

Data specifics.
- Adjustment: history is adjusted for corporate actions, price and volume, per a Fyers Product
  Manager (F-84). So a later fetch can differ from an earlier one for the same session
  ([DEFAULT-62], PE-22). Dates of adjustment and any dividend treatment: not stated (OQ-70).
- Delisted: not provided, per a forum reply of unconfirmed authority (F-85). The instrument master
  lists current symbols. Treated as absent ([DEFAULT-29], OQ-70).
- Tick and lot size: per instrument from the symbol master; no constant is assumed.
- Timestamps: epoch seconds; the zone that defines a daily candle is not stated (NB-65).
- Tape: NSE and BSE are separate symbols.

Errors (F-80). HTTP 200, 400, 401, 403, 429, 500. Body `s`, `code`, `message`. -8, -15, -16, -17
token expired or invalid; -50 bad parameter; -300 bad symbol; -352 means two different things, so
the message is read (NB-67). The Fyers pages warn that one code can cover several conditions.

Failure modes. A status page exists (`status.fyers.in`, not read). Dormancy: as Upstox (F-97,
OQ-71). One KB article says an account can avoid it by logging in periodically or trading once in
12 months; others reportedly give 24 months. This spec uses 12 months and does not count a login
(BQ-53).

Cost. Standard INR 0; account opening and AMC INR 0 (F-97). Prime as above.

Legal (F-82, read in full; not legal advice). The terms cover the use of APIs by a client. Under
Model B these clauses matter. Section 11: third-party use is barred; exchange data may be used only
for legitimate, fair and transparent trading, must not be disseminated, supplied or processed for
unauthorised purposes, and must not be used to develop charting or technical tools, paper trading,
gaming or virtual trading. That first limb reaches further than the list, and bears on backtests
and research as well as on a track record. Section 12: written consent is needed to build databases
or copies with intent to redistribute; to copy, modify, make derivative works, sell, distribute,
publicly display or sub-license API content; and to disclose its source or ownership. Section 15:
rights end automatically on non-compliance, a breach not cured within one day can end the
relationship, and on termination use stops and the clause says FYERS shall delete cached and stored
content; how that reaches our snapshots ([DEFAULT-62]) is for counsel. Section 2 mentions platforms
for the public or other FYERS clients; sections 8 and 9 limit that to other FYERS clients after
approvals, so they are no route for Model B subscribers at other brokers. Section 17 is an indemnity. What these mean is a legal question: OQ-68.

## 6. Decision matrix and selection

### 6.1 Method

Six criteria, each scored 0 to 5 from the fact sheets, weights summing to 100. Score =
sum(weight x points) / 5, so the maximum is 100. A capability's highest score is the primary and
the next is the backup. A tie is broken in favour of the provider that adds no new account
(RULE-3). A provider that INV-10 or STACK-1 fixes is primary regardless of score; its score is
still shown.

| Criterion | Weight | 5 points means | 0 points means |
|-----------|--------|----------------|----------------|
| C1 Fit to the requirement in section 4 | 30 | covers it fully | does not cover it |
| C2 Documented behaviour (limits, fields, errors) | 20 | documented and read | undocumented or unread |
| C3 Operability on one VM with one operator | 15 | key-based, no daily human step, no new account | daily human step or blocked |
| C4 Integrity (point-in-time, delisted, adjustment; for brokers, safety of the resting stop) | 15 | verified strong | verified weak or unknown |
| C5 Cost | 10 | free | above USD 500 a month or unknown |
| C6 Legal clarity for automated use and storage | 10 | terms read and permissive | terms read and prohibitive |

Points for C6 are capped at 3 wherever the terms were not read in this run.

v0.2: on rows re-scored or added by this amendment, C6 is scored for the Model B use, commercial
publication of derived signals (BO-1), and is capped at 2 unless a permission for that use is read.
Rows not re-scored keep their v0.1 C6 and are re-scored by the Model B re-run. A broker's score for
a data capability assumes no broker account is otherwise integrated (MB-8). Exceptions to "the next
score is the backup": a paid plan the Owner has not bought is shown for OQ-67 but is not a candidate,
and a row that cannot do the job (Fyers Standard for an event study) is no backup.

### 6.2 Scores

| Capability | Market | Candidate | C1 | C2 | C3 | C4 | C5 | C6 | Score |
|------------|--------|-----------|----|----|----|----|----|----|-------|
| broker_execution | US | Alpaca | 5 | 4 | 5 | 4 | 5 | 2 | 87 |
| broker_execution | US | Interactive Brokers | 4 | 3 | 2 | 4 | 3 | 3 | 66 |
| broker_execution | IN | Zerodha Kite | 5 | 4 | 2 | 3 | 4 | 3 | 75 |
| broker_execution | IN | Upstox | 4 | 4 | 3 | 3 | 4 | 3 | 72 |
| eod_bars, instrument_master | US | Massive | 5 | 4 | 5 | 4 | 3 | 3 | 85 |
| eod_bars, instrument_master | US | Alpaca Market Data | 3 | 4 | 5 | 3 | 5 | 3 | 74 |
| eod_bars | US | FMP | 3 | 2 | 4 | 2 | 4 | 3 | 58 |
| eod_bars | US | Finnhub | 2 | 3 | 4 | 2 | 3 | 2 | 52 |
| eod_bars, instrument_master | IN | Zerodha Kite (v0.2) | 3 | 3 | 0 | 1 | 4 | 2 | 45 |
| eod_bars | IN | Upstox (v0.2) | 3 | 4 | 4 | 1 | 5 | 2 | 63 |
| eod_bars | IN | Fyers Standard | 2 | 5 | 0 | 1 | 5 | 1 | 47 |
| eod_bars | IN | Fyers Prime | 3 | 5 | 0 | 1 | 4 | 1 | 51 |
| intraday_bars | IN | Upstox | 4 | 4 | 4 | 1 | 5 | 2 | 69 |
| intraday_bars | IN | Fyers Prime | 5 | 5 | 0 | 1 | 4 | 1 | 63 |
| intraday_bars | IN | Fyers Standard | 1 | 5 | 0 | 1 | 5 | 1 | 41 |
| instrument_master | IN | Upstox | 4 | 5 | 4 | 1 | 5 | 2 | 73 |
| instrument_master | IN | Fyers | 3 | 5 | 5 | 1 | 5 | 1 | 68 |
| corporate_actions | IN | Upstox | 3 | 4 | 4 | 2 | 5 | 2 | 66 |
| fundamentals | IN | Upstox | 2 | 4 | 4 | 1 | 5 | 2 | 57 |
| news | IN | Upstox | 2 | 4 | 4 | 2 | 5 | 2 | 60 |
| sector_taxonomy | IN | Upstox | 3 | 3 | 4 | 1 | 5 | 2 | 59 |
| calendar | IN | Upstox | 3 | 4 | 4 | 2 | 5 | 2 | 66 |
| corporate_actions | US | Alpaca Market Data | 4 | 4 | 5 | 3 | 5 | 3 | 80 |
| corporate_actions | US | Massive | 4 | 2 | 5 | 3 | 3 | 3 | 68 |
| fundamentals | US | SEC EDGAR | 5 | 1 | 2 | 5 | 5 | 3 | 71 |
| fundamentals | US | FMP | 4 | 2 | 4 | 2 | 4 | 3 | 64 |
| fundamentals | US | Finnhub (free) | 3 | 3 | 4 | 2 | 5 | 2 | 62 |
| news | US | Alpaca News | 4 | 4 | 5 | 3 | 5 | 2 | 78 |
| news | US | Finnhub | 3 | 3 | 4 | 3 | 5 | 2 | 65 |
| macro | none | FRED | 4 | 4 | 5 | 5 | 5 | 3 | 86 |
| llm | none | DeepSeek | 5 | 4 | 4 | 3 | 5 | 2 | 81 |
| llm | none | OpenAI | 5 | 4 | 4 | 4 | 4 | 3 | 84 |

Arithmetic, one row shown in full: Alpaca broker = (30x5 + 20x4 + 15x5 + 15x4 + 10x5 + 10x2) / 5
= (150 + 80 + 75 + 60 + 50 + 20) / 5 = 435 / 5 = 87.

Notes on the scores:
- India daily bars tied at 62 in v0.1, and Zerodha won because it added no account and no second
  daily token. Model B removes that reason: no broker is integrated, so Kite would add both a new
  account and a daily human login. v0.2 re-scores it at 45. C3 rewards Upstox for the Analytics
  Token (F-87). C4 falls on every India row because the delisted gap is now confirmed (UP-43).
- C3 is 0 for Fyers bar rows, by the definition in section 6.1: a daily human step. The Fyers symbol
  master is a public file, so that row keeps 5.
- India intraday: Upstox 69 against Fyers Prime 63, and the ranking is sensitive. If a non-trading
  Fyers app could refresh unattended (OQ-74), C3 at 3 makes Prime 72, ahead of Upstox. If Prime does
  not reach 2017, C1 at 4 makes it 57. If Upstox C6 fell to 1 it would be 67. Data depth favours
  Prime; operability and legal columns favour Upstox. That is why BQ-48 goes to the Owner.
- Fyers C6 is 1 because its terms were read and restrict this use (F-82). Upstox C6 is 2 because no
  API terms were found. A higher Upstox score there means unread, not permitted.
- The LLM scores differ by 3 points in OpenAI's favour (a dated snapshot against an alias that
  is re-pointed). STACK-1 fixes DeepSeek as primary; the matrix does not overrule it. The
  difference is recorded, not acted on.
- SEC EDGAR's score rests on SECONDARY evidence for C1 and C4. It is shown so that the
  comparison exists; the capability is BLOCKED either way.
- Not scored, because no fact was verified: NSE Data & Analytics (India end-of-day licence), any
  India source of corporate actions, fundamentals, news or sector taxonomy other than Upstox, FBIL.

### 6.3 Selection

Status values: SELECTED (ready to specify a client), PROVISIONAL (chosen; a named question must
close before code, except a research client admitted by the research gate below), BLOCKED (chosen; cannot be used until a named item is resolved), UNFILLED
(no provider can be named from verified facts).

| ID | Capability | Market | Primary | Backup | Status | Open items | Licensed use |
|----|------------|--------|---------|--------|--------|------------|--------------|
| SEL-1 | broker_execution | US | Alpaca Trading API | none integrated; cold alternate Interactive Brokers | PROVISIONAL | OQ-33, OQ-34, OQ-35 | NONE |
| SEL-2 | broker_execution | IN | Zerodha Kite Connect | none integrated; cold alternate Upstox | PROVISIONAL | OQ-27, OQ-28, OQ-29, OQ-31 | NONE |
| SEL-3 | eod_bars | US | Massive, Developer plan | Alpaca Market Data, Basic plan, `feed=sip` | PROVISIONAL | OQ-38, OQ-36 | NONE |
| SEL-4 | eod_bars | IN | Upstox historical | Fyers historical, Standard plan | PROVISIONAL | OQ-39, OQ-68, OQ-69 | NONE |
| SEL-5 | instrument_master | US | Massive tickers (class, listing status) with Alpaca assets (tradability) | none | PROVISIONAL | OQ-38 | NONE |
| SEL-6 | instrument_master | IN | Upstox instrument files | Fyers symbol master | PROVISIONAL | OQ-68, OQ-75 | NONE |
| SEL-7 | corporate_actions | US | Alpaca Market Data | Massive | PROVISIONAL | OQ-36, OQ-38 | NONE |
| SEL-8 | corporate_actions | IN | Upstox fundamentals, corporate actions | none | PROVISIONAL | OQ-68, OQ-73 | NONE |
| SEL-9 | fundamentals | US | SEC EDGAR | FMP | BLOCKED | OQ-41, OQ-47 | NONE |
| SEL-10 | fundamentals | IN | Upstox fundamentals | none | BLOCKED | OQ-68, OQ-73 | NONE |
| SEL-11 | news | US | Alpaca News | Finnhub | PROVISIONAL | OQ-37, OQ-50 | NONE |
| SEL-12 | news | IN | Upstox news | none | PROVISIONAL | OQ-68, OQ-76 | NONE |
| SEL-13 | sector_taxonomy | US | none | none | UNFILLED | OQ-41, OQ-38 | NONE |
| SEL-14 | sector_taxonomy | IN | Upstox company profile `sector` | none | PROVISIONAL | OQ-68, OQ-73 | NONE |
| SEL-15 | calendar | US | NYSE published calendar, entered as a reviewed file | none | PROVISIONAL | OQ-36 | NONE |
| SEL-16 | calendar | IN | Upstox market holidays | none | PROVISIONAL | OQ-49, OQ-68, OQ-75 | NONE |
| SEL-17 | macro | none | FRED | none | PROVISIONAL | OQ-42 | NONE |
| SEL-18 | fx_reference | none | none | none | UNFILLED | OQ-22 | NONE |
| SEL-19 | llm | none | DeepSeek, model `deepseek-flash` | OpenAI, model `gpt-4o-mini-2024-07-18` | PROVISIONAL | OQ-43, OQ-44 | NONE |
| SEL-20 | streaming quotes at order time | US | not selected; P3.2 decides whether it is needed | none | UNFILLED | OQ-36 | NONE |
| SEL-21 | streaming quotes at order time | IN | not selected; P3.2 decides whether it is needed | none | UNFILLED | OQ-31 | NONE |
| SEL-22 | intraday_bars | IN | Upstox historical | none | PROVISIONAL | OQ-67, OQ-68, OQ-69 | NONE |
| SEL-23 | intraday_bars | US | none | none | UNFILLED | OQ-77 | NONE |

SEL-20 and SEL-21 are recorded so that P3.2 finds the question; they are not `Capability`
values in section 8 and have no client.

SEL-1, SEL-2, SEL-20 and SEL-21 are execution rows, deferred by MB-8. Their text is unchanged.

No row is SELECTED. Three capability rows are UNFILLED (SEL-13, SEL-18, SEL-23) and two are BLOCKED
(SEL-9, SEL-10). In v0.1 five of the seven UNFILLED capability rows were India rows; in v0.2 none
is. SEL-4 moves from BLOCKED to PROVISIONAL because [DEFAULT-29] already allows the pipeline to be
built on survivorship-biased history with every result labelled; **no India result counts as ADR-08
evidence until OQ-39 closes**. The note on SEL-18: Upstox lists a USD INR indicator among its global
instruments (F-43), a market rate and not a reference rate, so the row stays UNFILLED.

Two gates, because E-12 alone would stop everything:
- **Research gate. Closed until the Owner opens it.** If the Owner accepts the risk, recorded as a
  `ResearchGateApproval`, a read-only client in `v2/research` may run on a PROVISIONAL Upstox row for
  the Owner's own research. With no record the gate is closed. US research clients are not defined
  here; the Model B re-run defines them. F-100
  licenses nothing: it is the best evidence of what Upstox would say, and the acceptance is the
  Owner's own. Output is labelled and reaches no user. Not on a BLOCKED row, and not on Fyers before
  OQ-68 is answered for Fyers. One approval covers all PROVISIONAL Upstox rows, and a revoked approval
  closes the gate: recording a negative answer to OQ-68 revokes it (P6.3). No gated content goes to an
  external LLM until OQ-76 closes (P4.1).
- **Publication gate.** Data from a row that names OQ-68 may not feed a published signal, and the
  publication switch for a market (MB-5) may not be turned on while any data row of that market lacks
  a licence for that use (MB-AC-14, D-44). This is typed. `ProviderSelection.licensed_use` records
  whether a written licence covers publication, and `licence_audit_id` names the audit record of it,
  which P1.3 resolves at every load as MB-E4 does for a switch, checking that the record names that
  provider, capability and market. A forum reply never sets that value.
  A backup on a cleared row needs its own licence record, `backup_licence_audit_id`; otherwise the
  backup rule below could put an unlicensed source in a signal. `publication_data_cleared` is true only if every signal-input
  capability has a row, for that market or market-less, and that row is `PUBLICATION`; an absent
  capability fails it. `row_cleared` applies the same test at signal entry to the provider of any
  signal input, so a value from another source does not pass because its market cleared. Three
  capabilities are not signal inputs: `broker_execution` (deferred, MB-8), `intraday_bars` (D-43) and
  `fx_reference`, a reporting figure only (ADR-15), with each model portfolio in its own currency
  ([DEFAULT-46]). If a published number ever uses the reporting rate, OQ-22 must bring that row into
  the test. Every other capability counts for now, so neither market can clear yet, even on a row no
  strategy uses; OQ-79 narrows the set, and a row is never marked cleared to get past it. Training
  data is outside both functions (OQ-80). The loader rule is proposed, not made (MB-E9, OQ-78). **The same applies to the US rows**: Massive's and
  Finnhub's plans are individual or personal use (BO-1), so MB-AC-14 is equally unmet there, pending
  the Model B re-run. Fyers is excluded from Model B publication unless OQ-68 says otherwise; its
  backup entries are inactive until then.

Either way, nothing here publishes anything.

Known recurring cost of the selection, from verified prices only: Massive Developer USD 79 per
month; Upstox INR 0; Fyers Standard INR 0; Alpaca Basic data USD 0; FRED USD 0; LLM cost is per
token and is P0.3's to compute from F-57 and F-60. Kite Connect at INR 500 a month is no longer a
data cost (the execution row is deferred). Optional: Fyers Prime INR 5,888.20 a year with GST, or
INR 7,065.84 if paid monthly. Unknown and therefore not totalled: any commercial licence from a
broker or an exchange (OQ-68), the India end-of-day licence (OQ-39), FMP.

Edge cases of the selection rules:
- A backup is promoted: this is ADR-07 T-3 (a data vendor changes for a model input). New
  entries in that market stop until a model trained on the backup's data is promoted. A backup
  for a model input is therefore a continuity-of-history measure, not a hot failover.
- Primary and backup disagree on a value: neither is averaged. The value from the primary is
  stored; the disagreement is recorded as a data-quality event; the instrument is quarantined
  (HITL-12) if the difference exceeds a threshold that P2.2 owns.
- The primary is down and the backup is up, for a non-model input (calendar, reporting rate):
  the backup may be used the same day, and the record says which source supplied the value. On a
  row cleared for publication, only a backup with its own licence record may be used.
- A provider is renamed or re-hosted (F-49): the base URL is a config value changed through
  HITL-5; the provider identity in `ProviderId` does not change.
- Upstox is both primary and the only source for several India rows (SEL-4, 6, 8, 10, 12, 14, 22).
  One expired token stops all of them. That concentration is accepted while nothing is published;
  it is a design item for the Model B re-run.
- A Fyers backup needs a human login that day (BQ-50), so it is never an automatic failover.
- An intraday bar reaches a signal path: rejected at signal entry, which accepts `BarResolution.ONE_DAY`
  only (D-43). `v2/signals` may import `v2/research`, so an import check alone does not stop this; the
  resolution check needs its own test in P2.7.

## 7. What breaks if this provider dies at 09:31

09:31 is taken as one minute after the US open (09:31 `America/New_York`) for US providers and
09:31 `Asia/Kolkata`, sixteen minutes after the India open, for India providers. Under HP-1 to
HP-4 the decision was made after the previous close and the day's orders are already working.

v0.2: under Model B no order is working in v1, so the broker rows describe a future execution phase.
Data providers are not on any 09:31 path in v1, because signals are built after the close; the
question for them is what the evening batch loses.

| Provider | State at 09:31 | What breaks | What still works | Fail-closed action |
|----------|----------------|-------------|------------------|--------------------|
| Alpaca Trading | Entry limit orders working at the broker; `gtc` stops resting | No cancel, no replace, no new order, no fill events. A fill that happens is not seen, so the new position has no stop until the API returns. If the broker itself is down, resting stops may not execute. | Orders already at the venue, if only the API is down. | No new US orders. On return: reconcile over REST before anything else (D-14), then place missing stops (REC-4 order). The kill switch cannot flatten; the manual path is the broker's own console. |
| Alpaca Market Data | Not on the 09:31 path | Nothing at 09:31. After the close: no cross-check bars, no US corporate actions, no US news. Without corporate actions, tomorrow's orders cannot be confirmed against the share basis. | Orders and stops. | If corporate actions for the session are missing at the decision cycle: no US entries for the next session (INV-6). |
| Zerodha Kite | Entry limit orders working; GTTs held by Zerodha | As Alpaca Trading, and worse: a GTT is evaluated by Zerodha, so a Zerodha outage disables every India stop. A fill that occurs has no GTT until the API returns. | Orders already at the exchange. | No new India orders. HTTP 502 or 503, or `NetworkException`: treated as broker down. On return: reconcile, then place missing GTTs. Manual path: Kite web, which needs the same broker to be up. |
| Zerodha session (token invalidated, not an outage) | Same | Every authenticated call returns 403 `TokenException`. Identical to "no login" in [DEFAULT-6] from that moment. | Orders at the exchange and existing GTTs. | India disabled; alert; HITL-7. No automated re-login. |
| Upstox | Not on the 09:31 path | Nothing at 09:31. After the close, the whole India data side: no daily bars, instrument file, corporate actions, sector, calendar or news. The token is a single point of failure for all of them. | The US side. Stored India data, which stays usable but stale. | No India batch for that session; no signal is built on a missing or stale bar (INV-6, PE-16, PE-24). Fyers is not switched in automatically: it needs a human login, and a source change is T-3. |
| Fyers | Not on the 09:31 path | Nothing at 09:31. A planned human pull fails. | Everything; it has no scheduled job. | The pull is retried by a human later. No automated action. |
| Upstox News | Not on the 09:31 path | Tonight's India candidates have no news, and with a 7-day window a gap of more than 7 days is permanent. | The deterministic path. | As the News (Alpaca News) row. The capture gap is recorded. |
| Interactive Brokers | Not integrated | Nothing. | Everything. | None. |
| Massive | Not on the 09:31 path | Nothing at 09:31. After the close: no US daily bars. | Orders and stops. | No US decision cycle for that session (ADR-13 edge case: no decision on D-1's bar). The backup is not switched in automatically, because that is T-3. |
| Finnhub | Not on the 09:31 path | Nothing; it is a backup. | Everything. | None. |
| FMP | Not on the 09:31 path | Nothing; it is a backup. | Everything. | None. |
| SEC EDGAR | Blocked | Nothing. | Everything. | None. |
| FRED | Not on the 09:31 path | Nothing at 09:31. A macro series not updated by the decision cycle is missing data. | Orders and stops. | Features that need the series are absent; P2.6 owns whether the regime gate denies entries. A stale value is never reused as current (INV-6). |
| News (Alpaca News) | Not on the 09:31 path | The LLM packet for tonight's US candidates has no news. | The deterministic path. | The LLM is not called with an empty packet presented as "no news"; the candidate is handled as P4.2 decides for an unavailable LLM input. |
| DeepSeek | Not on the 09:31 path | The gated LLM step in tonight's cycle. | Everything deterministic. INV-1 and INV-2 mean no order depends on the LLM alone. | One attempt within our deadline (PE-14), then the fallback once, then the candidate proceeds or is dropped as P4.2 decides. |
| OpenAI | Not on the 09:31 path | Nothing unless DeepSeek is also down. | Everything. | If both are down: the LLM step is unavailable for the cycle; never retried in a loop. |
| NSE or BSE (exchange halt) | Session interrupted | No fills; GTTs do not trigger outside market hours; resting orders may be purged by the exchange. | Nothing in that market. | India disabled until the exchange resumes and reconciliation passes. |

## 8. Typed form

Entities this spec defines: the provider and capability vocabularies, a rate-limit fact, a
client throttle, a provider selection, the internal order reference, and the provider error
classes, plus, from v0.2, a vendor series snapshot, an account activity record and a research gate
approval. Provider request
and response objects are the providers' own; section 5 lists their verified fields, and the client
phases (P2.1, P3.1, P4.2) define the models that wrap them.

### 8.1 Models

`Market` is the P0.1 type. It is re-declared in the block only so the block runs alone.

```python
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator


class Market(StrEnum):
    US = "US"
    IN = "IN"


class ProviderId(StrEnum):
    ALPACA_TRADING = "alpaca_trading"
    ALPACA_DATA = "alpaca_data"
    IBKR = "ibkr"
    ZERODHA_KITE = "zerodha_kite"
    UPSTOX = "upstox"
    FYERS = "fyers"
    MASSIVE = "massive"
    FINNHUB = "finnhub"
    FMP = "fmp"
    SEC_EDGAR = "sec_edgar"
    FRED = "fred"
    NSE_DATA = "nse_data"
    REVIEWED_CALENDAR_FILE = "reviewed_calendar_file"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


class Capability(StrEnum):
    BROKER_EXECUTION = "broker_execution"
    EOD_BARS = "eod_bars"
    INTRADAY_BARS = "intraday_bars"
    INSTRUMENT_MASTER = "instrument_master"
    CORPORATE_ACTIONS = "corporate_actions"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    SECTOR_TAXONOMY = "sector_taxonomy"
    CALENDAR = "calendar"
    MACRO = "macro"
    FX_REFERENCE = "fx_reference"
    LLM = "llm"


MARKETLESS = frozenset({Capability.MACRO, Capability.FX_REFERENCE, Capability.LLM})


class SelectionStatus(StrEnum):
    SELECTED = "SELECTED"
    PROVISIONAL = "PROVISIONAL"
    BLOCKED = "BLOCKED"
    UNFILLED = "UNFILLED"


class VerificationLevel(StrEnum):
    PRIMARY_FULL = "PRIMARY_FULL"
    PRIMARY_EXTRACT = "PRIMARY_EXTRACT"
    SEARCH_EXCERPT = "SEARCH_EXCERPT"
    SECONDARY = "SECONDARY"


class LimitBasis(StrEnum):
    DOCUMENTED = "DOCUMENTED"
    EMPIRICAL = "EMPIRICAL"


class ProviderErrorClass(StrEnum):
    AUTH_EXPIRED = "AUTH_EXPIRED"
    IP_NOT_ALLOWED = "IP_NOT_ALLOWED"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_REQUEST = "INVALID_REQUEST"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    INSUFFICIENT_HOLDINGS = "INSUFFICIENT_HOLDINGS"
    ORDER_REJECTED = "ORDER_REJECTED"
    BACKEND_DOWN = "BACKEND_DOWN"
    SERVER_ERROR = "SERVER_ERROR"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    BALANCE_EXHAUSTED = "BALANCE_EXHAUSTED"
    ACCOUNT_RESTRICTED = "ACCOUNT_RESTRICTED"


class AdjustmentBasis(StrEnum):
    RAW = "RAW"
    VENDOR_ADJUSTED = "VENDOR_ADJUSTED"
    UNSTATED = "UNSTATED"


class BarResolution(StrEnum):
    ONE_MINUTE = "1MIN"
    ONE_DAY = "1D"


class LicensedUse(StrEnum):
    NONE = "NONE"
    PUBLICATION = "PUBLICATION"


class DormancyStatus(StrEnum):
    OK = "OK"
    DUE = "DUE"
    UNKNOWN = "UNKNOWN"


BAR_PROVIDER_MARKET = {
    ProviderId.UPSTOX: Market.IN,
    ProviderId.FYERS: Market.IN,
    ProviderId.MASSIVE: Market.US,
    ProviderId.ALPACA_DATA: Market.US,
}
DORMANCY_PROVIDERS = frozenset({ProviderId.UPSTOX, ProviderId.FYERS})
NOT_SIGNAL_INPUTS = frozenset({Capability.BROKER_EXECUTION, Capability.INTRADAY_BARS, Capability.FX_REFERENCE})


ClientOrderRef = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z0-9]{20}$")]
OpenItemRef = Annotated[str, StringConstraints(strict=True, pattern=r"^(OQ|BQ|UP)-[1-9][0-9]*$")]
HttpsUrl = Annotated[str, StringConstraints(strict=True, pattern=r"^https://[^\s]+$")]
ScopeText = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=120)]
Sha256Text = Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9a-f]{64}$")]


class RateLimitFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    provider: ProviderId
    scope: ScopeText
    max_count: int = Field(ge=1)
    window_seconds: int = Field(ge=1)
    basis: LimitBasis
    verification: VerificationLevel
    source_url: HttpsUrl
    retrieved_on: date


class ClientThrottle(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    provider: ProviderId
    scope: ScopeText
    documented_max_count: int = Field(ge=1)
    client_max_count: int = Field(ge=1)
    window_seconds: int = Field(ge=1)

    @model_validator(mode="after")
    def _headroom(self) -> "ClientThrottle":
        if self.client_max_count * 2 > self.documented_max_count:
            raise ValueError("client budget must be at most half the documented limit")
        return self


class ProviderSelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    capability: Capability
    market: Market | None
    primary: ProviderId | None
    backup: ProviderId | None
    status: SelectionStatus
    blocked_by: tuple[OpenItemRef, ...] = ()
    licensed_use: LicensedUse = LicensedUse.NONE
    licence_audit_id: UUID | None = None
    backup_licence_audit_id: UUID | None = None

    @model_validator(mode="after")
    def _consistent(self) -> "ProviderSelection":
        if (self.market is None) != (self.capability in MARKETLESS):
            raise ValueError("market is None if and only if the capability is market-less")
        if (self.status is SelectionStatus.UNFILLED) != (self.primary is None):
            raise ValueError("primary is None if and only if status is UNFILLED")
        if self.primary is None and self.backup is not None:
            raise ValueError("a backup without a primary is not a selection")
        if self.primary is not None and self.primary == self.backup:
            raise ValueError("primary and backup must differ")
        if (self.status is SelectionStatus.SELECTED) != (len(self.blocked_by) == 0):
            raise ValueError("blocked_by is empty if and only if status is SELECTED")
        if (self.licensed_use is LicensedUse.PUBLICATION) != (self.licence_audit_id is not None):
            raise ValueError("licence_audit_id is set if and only if the row is cleared for publication")
        if self.licensed_use is LicensedUse.PUBLICATION and self.status is not SelectionStatus.SELECTED:
            raise ValueError("only a SELECTED row can be cleared for publication")
        cleared_backup = self.licensed_use is LicensedUse.PUBLICATION and self.backup is not None
        if cleared_backup != (self.backup_licence_audit_id is not None):
            raise ValueError("backup_licence_audit_id is set if and only if a cleared row has a backup")
        if self.licence_audit_id is not None and self.licence_audit_id == self.backup_licence_audit_id:
            raise ValueError("a backup needs a licence record of its own")
        return self


class ProviderSelectionSet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    rows: tuple[ProviderSelection, ...]

    @model_validator(mode="after")
    def _one_row_per_key(self) -> "ProviderSelectionSet":
        keys = [(s.capability, s.market) for s in self.rows]
        if len(keys) != len(set(keys)):
            raise ValueError("one row per capability and market")
        return self


class VendorSeriesSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    snapshot_id: ScopeText
    provider: ProviderId
    market: Market
    instrument_ref: ScopeText
    resolution: BarResolution
    adjustment_basis: AdjustmentBasis
    retrieved_at: AwareDatetime
    first_session: date
    last_session: date
    content_sha256: Sha256Text

    @model_validator(mode="after")
    def _consistent(self) -> "VendorSeriesSnapshot":
        if BAR_PROVIDER_MARKET.get(self.provider) is not self.market:
            raise ValueError("provider does not serve bars for this market")
        if self.provider is ProviderId.FYERS and self.adjustment_basis is not AdjustmentBasis.VENDOR_ADJUSTED:
            raise ValueError("Fyers history is vendor-adjusted (F-84)")
        if self.market is Market.IN and self.adjustment_basis is AdjustmentBasis.RAW:
            raise ValueError("no India source is verified as raw (UP-42)")
        if self.first_session > self.last_session:
            raise ValueError("first_session must not be after last_session")
        latest = self.retrieved_at.astimezone(timezone.utc).date() + timedelta(days=1)
        if self.last_session > latest:
            raise ValueError("a snapshot cannot hold a session after its retrieval")
        return self


class AccountActivity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    provider: ProviderId
    last_activity_on: date
    alert_after_days: tuple[int, ...]

    @model_validator(mode="after")
    def _consistent(self) -> "AccountActivity":
        if self.provider not in DORMANCY_PROVIDERS:
            raise ValueError("the dormancy guard is for broker accounts")
        days = self.alert_after_days
        if not days or list(days) != sorted(set(days)) or days[0] < 1 or days[-1] > 364:
            raise ValueError("thresholds must be ascending, distinct, and within 1 to 364 days")
        return self


class ResearchGateApproval(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    approved_by: ScopeText
    approval_ref: ScopeText
    approved_on: date
    revoked_on: date | None = None

    @model_validator(mode="after")
    def _traceable(self) -> "ResearchGateApproval":
        if not self.approved_by.strip() or not self.approval_ref.strip():
            raise ValueError("an approval must be traceable")
        return self


def research_gate_open(approval: ResearchGateApproval | None, selection: ProviderSelection, today: date) -> bool:
    """Closed unless a current approval exists and the row is a PROVISIONAL Upstox row. Bad input closes it."""
    if approval is None or type(today) is not date:
        return False
    if selection.primary is not ProviderId.UPSTOX or selection.status is not SelectionStatus.PROVISIONAL:
        return False
    if approval.revoked_on is not None and approval.revoked_on <= today:
        return False
    return approval.approved_on <= today


def _row_for(capability: Capability, market: Market, selections: ProviderSelectionSet) -> ProviderSelection | None:
    return next((s for s in selections.rows if s.capability is capability and (s.market is market or s.market is None)), None)


def publication_data_cleared(market: Market, selections: ProviderSelectionSet) -> bool:
    """True only if every signal-input capability has a row licensed for publication."""
    rows = [_row_for(c, market, selections) for c in Capability if c not in NOT_SIGNAL_INPUTS]
    return all(r is not None and r.licensed_use is LicensedUse.PUBLICATION for r in rows)


def row_cleared(provider: ProviderId, capability: Capability, market: Market, selections: ProviderSelectionSet) -> bool:
    """True only if the row is licensed for publication and this is its primary, or its backup with a record."""
    row = _row_for(capability, market, selections)
    if row is None or row.licensed_use is not LicensedUse.PUBLICATION:
        return False
    return provider is row.primary or (row.backup_licence_audit_id is not None and provider is row.backup)


def throttle_matches(throttle: ClientThrottle, fact: RateLimitFact) -> bool:
    """A throttle may only be built from the fact it cites."""
    return (
        throttle.provider is fact.provider
        and throttle.scope == fact.scope
        and throttle.window_seconds == fact.window_seconds
        and throttle.documented_max_count == fact.max_count
    )


def dormancy_status(record: AccountActivity | None, today: date) -> tuple[DormancyStatus, int]:
    """Status and the highest threshold reached. Bad or missing input is UNKNOWN, which alerts (INV-6)."""
    if record is None or type(today) is not date:
        return (DormancyStatus.UNKNOWN, 0)
    days = (today - record.last_activity_on).days
    if days < 0:
        return (DormancyStatus.UNKNOWN, 0)
    reached = [d for d in record.alert_after_days if days >= d]
    return (DormancyStatus.DUE, reached[-1]) if reached else (DormancyStatus.OK, 0)
```

Config and stored records enter these models through `model_validate_json`: strict mode refuses a
list for a tuple, or a string for an enum or a date, in Python input, and accepts them in JSON. A YAML
value is therefore turned into JSON text first.

Evidence, v0.3: the block and the tables of this spec are checked by
`v2/tests/providers/verify_p02_spec.py`, run on 2026-10-31 with Python 3.11.9 and Pydantic 2.13.5, the
only local version with Pydantic; the stack's Python 3.12 is not exercised here (R-4). Covered: enum
sizes; `NOT_SIGNAL_INPUTS` against a list written in the script; the arithmetic of all 32 rows of
section 6.2; the 21 capability rows of section 6.3 loaded through `ProviderSelection` and
`ProviderSelectionSet`, licensed use read from the table, none SELECTED, none licensed, the UNFILLED
and BLOCKED sets as stated, the India primaries and backups, and every India data row naming OQ-68;
every row reloaded from JSON text; a duplicate key rejected; `PUBLICATION` rejected on a non-SELECTED
row, with an unlicensed backup and without `licence_audit_id`, and either id rejected where it does
not apply, and one record rejected for both providers;
`publication_data_cleared` false for the rows as they stand, for a single cleared row, and for each
signal-input capability missing or uncleared in turn, and true only for a full cleared set;
`row_cleared` false for another provider, market or capability, true for a backup with its own record
and false for one without; the THR-13 and THR-14 budgets parsed
from their rows, each half of its documented limit, a budget over half rejected, and `throttle_matches`
false for a limit that differs from its fact; `VendorSeriesSnapshot` distinct across fetches and
instruments, and rejecting a bad provider, market, basis, session range, resolution, time or digest;
`dormancy_status` `OK` at 299 days, `DUE` at 300 and 330, and `UNKNOWN` rather than a crash on bad
input; `research_gate_open` closed for no record, a future approval, a revoked approval, a BLOCKED row,
a row that is not Upstox and bad input; the presence of each new row; and that every cited F (from
F-77), OQ (from OQ-27), PE, THR, SEL and E identifier has a row. The fact counts of section 3 are
checked too. Deliberate breaks of a copy of this spec each failed the check: a wrong score, OQ-68
removed from a row, a removed enum member, disabled validators, a changed boundary, guards that fail
open, each gate weakened, a wider exclusion set, duplicate keys allowed, a throttle at the full limit,
a swapped selection, a licensed table cell, deleted rows and a FROZEN status. There is no loader yet,
so P1.3's path (E-36) is not tested here: the script covers the functions and the tables only.
Client-phase tests still owed: shared budgets across processes, a restart keeping the PE-19 count,
descending and duplicate candles, and the allowlist.

Evidence, v0.2: the block and the tables of this spec were checked on 2026-10-30 with Python 3.11.9
and Pydantic 2.13.5, all checks passing; the check script is not in the repository, so a client
phase must carry these cases into its own tests. Covered: enum sizes; the arithmetic of all 32 rows
of section 6.2; the 21 capability rows of section 6.3 loaded through `ProviderSelection` (SEL-1 and
SEL-2 with no backup value, per ADR-10), none SELECTED, the UNFILLED and BLOCKED sets as stated, and
every India data row naming OQ-68; six `RateLimitFact` and six `ClientThrottle` values for THR-13
and THR-14; a budget over half rejected; `VendorSeriesSnapshot`: two fetches or two instruments on
one day stay distinct, a changed digest is visible, and it rejects Fyers as raw or unstated, Upstox
as raw, a provider in the wrong market, a non-bar provider, a session after retrieval, reversed
sessions, a vendor resolution string, a naive time, a bad digest and assignment after construction;
`dormancy_alerts`: nothing at 299 days, one threshold at 300, both at 330, and an alert rather than a
crash for a missing record, a future date or a bad `today`; `AccountActivity` rejected for 0, 365,
empty, unordered thresholds and a non-broker provider; `ResearchGateApproval` accepted for Upstox
and rejected for Fyers and for a blank name or reference; and that every identifier cited has a row.
Deliberate breaks of a copy of this spec each failed the check: a wrong score, OQ-68 removed from a
row, a removed enum member, a disabled validator, a changed boundary and a guard that fails open.
Not run on Python 3.12 or later (R-4).

Evidence, v0.1: the block was executed on 2026-10-13 with Python 3.11.9 and Pydantic 2.13.5. Accepted:
a market-less SELECTED row, a BLOCKED row with one open item, an UNFILLED row with one open
item, a `RateLimitFact` for the Kite order limit, a `ClientThrottle` of 100 against a documented
200, and the reference `A1B2C3D4E5F6G7H8J9K0`. Rejected as expected: a market on a market-less
capability; no market on a per-market capability; SELECTED with no primary; a backup with no
primary; primary equal to backup; SELECTED with open items; BLOCKED with none; a lower-case open
item reference; a plain string for `primary`; `max_count` of 0; an `http` URL; a float count; a
string date; a client budget of 101 against 200; a client budget of 1 against 1; order
references that are lower case, 19 or 21 characters long, contain a hyphen, or end in a newline;
assignment after construction. Not run on Python 3.12 or later (R-4).

### 8.2 Fields

No field is nullable unless the table says so. `retrieved_at` is the only field that carries a
time of day; the other date fields are calendar or session dates.

| Model.field | Type | Unit | Timezone | Nullable | Valid range | A violation means |
|-------------|------|------|----------|----------|-------------|-------------------|
| RateLimitFact.provider | ProviderId | none | none | no | a member of `ProviderId` | a limit recorded for a provider this spec did not examine; rejected (E-9) |
| RateLimitFact.scope | str | none | none | no | 1 to 120 characters | an unscoped limit cannot be applied to an endpoint; rejected (E-9) |
| RateLimitFact.max_count | int | requests, or orders where the scope says so | none | no | at least 1 | a limit of zero would be a prohibition, which is recorded as a legal fact, not a limit; rejected (E-9) |
| RateLimitFact.window_seconds | int | seconds | none | no | at least 1; a per-day limit is 86,400 | rejected (E-9) |
| RateLimitFact.basis | LimitBasis | none | none | no | `DOCUMENTED` or `EMPIRICAL` | a limit of unknown origin is a guess; rejected (E-9) |
| RateLimitFact.verification | VerificationLevel | none | none | no | one of four levels | rejected (E-9) |
| RateLimitFact.source_url | str | none | none | no | starts with `https://`, no whitespace | a fact with no source breaks RULE-2; rejected (E-9) |
| RateLimitFact.retrieved_on | date | calendar date | `Asia/Kolkata` [DEFAULT-12] | no | a `date` object | a string or datetime was passed; rejected (E-9) |
| ClientThrottle.documented_max_count | int | requests per window | none | no | at least 1; equals a `RateLimitFact.max_count` for the same provider and scope | E-10 |
| ClientThrottle.client_max_count | int | requests per window | none | no | at least 1 and at most half of `documented_max_count`, rounded down | the client could run closer to the limit than [DEFAULT-31] allows; rejected (E-10). A documented limit of 1 per window has no valid client count in that window: the window is doubled instead (THR-3) |
| ClientThrottle.window_seconds | int | seconds | none | no | at least 1 | E-10 |
| ProviderSelection.capability | Capability | none | none | no | a member of `Capability` | E-11 |
| ProviderSelection.market | Market or None | none | none | yes | None exactly when the capability is `macro`, `fx_reference` or `llm` | a per-market capability with no market is "US-only by accident" (INV-10); rejected (E-11) |
| ProviderSelection.primary | ProviderId or None | none | none | yes | None exactly when status is `UNFILLED` | E-11 |
| ProviderSelection.backup | ProviderId or None | none | none | yes | None, or a provider different from the primary; None for `broker_execution` (ADR-10); on a row cleared for publication it needs `backup_licence_audit_id` | E-11; a broker backup is additionally rejected by the check in E-12 |
| ProviderSelection.status | SelectionStatus | none | none | no | one of four values | E-11 |
| ProviderSelection.blocked_by | tuple of str | none | none | no | empty exactly when status is `SELECTED`; each item `OQ-n`, `BQ-n` or `UP-n` | a selection that claims to be ready while a question is open, or blocked with no reason; rejected (E-11) |
| ProviderSelection.licensed_use | LicensedUse | none | none | no | `NONE` by default; `PUBLICATION` only with a written licence for that use, only with `licence_audit_id`, and only on a SELECTED row | a forum reply or an assumption cleared for publication; E-11 |
| ProviderSelection.licence_audit_id | UUID or None | none | none | yes | set exactly when `licensed_use` is `PUBLICATION`; P1.3 resolves it against the audit trail at every load and checks that the record names this provider, capability and market | a row cleared with no licence behind it; E-11, E-36 |
| ProviderSelection.backup_licence_audit_id | UUID or None | none | none | yes | set exactly when a row cleared for publication has a backup; a record of its own, different from `licence_audit_id`; P1.3 checks it the same way, for the backup | a fallback in a published signal with no licence behind it; E-11, E-36 |
| ProviderSelectionSet.rows | tuple of ProviderSelection | none | none | no | one row per capability and market | a duplicate could hide an uncleared row; rejected (E-11) |
| ClientOrderRef | str | none | none | no | exactly 20 characters from `A-Z0-9` | the reference would be truncated or rejected by Kite (`tag` max 20, alphanumeric); the order is not sent (E-13) |
| VendorSeriesSnapshot.snapshot_id | str | none | none | no | unique per complete fetch, 1 to 120 characters; generation is P2.1's | two fetches on one day must stay two snapshots; E-33 |
| VendorSeriesSnapshot.provider | ProviderId | none | none | no | a key of `BAR_PROVIDER_MARKET` | a provider that serves no bars; E-33 |
| VendorSeriesSnapshot.market | Market | none | none | no | the market of that provider | E-33 |
| VendorSeriesSnapshot.instrument_ref | str | internal identifier (UNI-4) | none | no | 1 to 120 characters | without it, PE-22 has nothing to compare; E-33 |
| VendorSeriesSnapshot.resolution | BarResolution | none | none | no | `1MIN` or `1D` | a vendor's own string was stored; the same bar would be spelled two ways; E-33 |
| VendorSeriesSnapshot.adjustment_basis | AdjustmentBasis | none | none | no | Fyers: `VENDOR_ADJUSTED` only. India: never `RAW` until a vendor states it | an unknown basis recorded as raw breaks [DEFAULT-26]; E-33 |
| VendorSeriesSnapshot.retrieved_at | datetime | instant | any offset; stored as UTC | no | timezone-aware | a naive time; E-33 |
| VendorSeriesSnapshot.first_session, last_session | date | exchange session date | exchange local | no | `first_session` not after `last_session`; `last_session` not later than one day past the UTC date of retrieval (a coarse bound; the exact check against the exchange's local date and session close is P2.1's) | a range that cannot exist; E-33 |
| VendorSeriesSnapshot.content_sha256 | str | hex digest of the snapshot's bars in canonical form; the form is P2.1's | none | no | 64 lower-case hex characters | shows that a stored snapshot is unchanged. It does not detect restatement: snapshots cover different ranges, so PE-22 compares bar by bar; E-33 |
| AccountActivity.provider | ProviderId | none | none | no | `UPSTOX` or `FYERS`. This is the time-based guard only; PE-20 classifies an error, separately | E-34 |
| AccountActivity.last_activity_on | date | calendar date | `Asia/Kolkata` | no | an executed trade or a KYC update recorded by a human. Not a login, an API call or a token (BQ-53, OQ-71) | counting a login could keep the alert from ever firing |
| AccountActivity.alert_after_days | tuple of int | days | none | no | ascending, distinct, 1 to 364; [DEFAULT-64] sets (300, 330) | a value of 365 or more could alert after the account is dormant; E-34 |
| ResearchGateApproval.approved_by, approval_ref | str | none | none | no | 1 to 120 characters; the Owner, and the record of the acceptance | an approval nobody can trace; E-35 |
| ResearchGateApproval.approved_on, revoked_on | date; `revoked_on` nullable | calendar date | `Asia/Kolkata` | `revoked_on` yes | `research_gate_open` is false before `approved_on` and from `revoked_on` | an approval that outlives a negative answer to OQ-68; E-35 |

`ClientOrderRef` edge cases: it must be unique for the life of the system, not per day, because
Alpaca treats `client_order_id` as unique and a `gtc` order lives 90 days. 36^20 values exist;
how the 20 characters are generated (random, or derived from the audit record) is P3.1's
decision. A replacement order gets a new reference. Kite GTTs carry no `tag` in the documented
GTT order fields (F-10), so a GTT is matched by its `trigger_id`, stored at creation.

### 8.3 Client throttles ([DEFAULT-31])

| ID | Provider and scope | Documented limit | Basis | Client budget |
|----|--------------------|------------------|-------|---------------|
| THR-1 | Kite, order placement | 10 per second; 400 per minute; 5,000 per day (F-7) | DOCUMENTED | Governed by [DEFAULT-5]: one order per 3 seconds, at most 20 per minute. Far inside every Kite limit. |
| THR-2 | Kite, historical candles | 3 per second (F-7) | DOCUMENTED | 1 per second |
| THR-3 | Kite, quote | 1 per second (F-7) | DOCUMENTED | 1 per 2 seconds |
| THR-4 | Kite, all other endpoints | 10 per second (F-7) | DOCUMENTED | 5 per second |
| THR-5 | Alpaca Trading, all endpoints | 200 per minute per account (F-36, SEARCH_EXCERPT) | DOCUMENTED | 100 per minute |
| THR-6 | Alpaca Market Data, Basic, historical | 200 per minute (F-27) | DOCUMENTED | 100 per minute |
| THR-7 | Massive, paid plans | "unlimited" (F-48) | none stated | 5 per second [ASSUMPTION A-41]; OQ-38 |
| THR-8 | FRED | none stated (F-55) | none stated | 1 per second [ASSUMPTION A-41]; OQ-42 |
| THR-9 | Finnhub, free | 60 per minute; 30 per second overall (F-52, F-53) | DOCUMENTED | 30 per minute |
| THR-10 | FMP, Starter | 300 per minute (F-54) | DOCUMENTED | 150 per minute |
| THR-11 | DeepSeek | concurrency 2,500 (`deepseek-flash`) (F-57, F-58) | DOCUMENTED | 1 concurrent request |
| THR-12 | OpenAI, `gpt-4o-mini` | 5,000 requests per minute at the lowest listed tier (F-60) | DOCUMENTED | 1 concurrent request |
| THR-13 | Upstox, standard APIs, historical candles included | 50 per second; 500 per minute; 2,000 per 30 minutes (F-39) | DOCUMENTED | 25 per second; 250 per minute; 1,000 per 30 minutes |
| THR-14 | Fyers, Data APIs, Standard plan | 5 per second; 50 per minute; 5,000 per day (F-77) | DOCUMENTED | 2 per second; 25 per minute; 2,500 per day |

Edge cases:
- Two processes share one account's limit (the trading process and the kill switch, both on
  Alpaca's 200 per minute or Kite's 10 per second). The kill switch has its own credentials
  ([DEFAULT-4]) but not its own limit, because limits are per account. The trading process's
  budget is half the documented limit precisely so the other half is left for the kill switch.
- A provider answers 429 although the client is inside its budget: the budget for that scope is
  halved for the rest of the session and an alert is raised; the documented fact is re-checked
  (PE-3).
- `X-RateLimit-Remaining` (Alpaca data, F-28) reports less than the client's own count: the
  header wins.
- Windows are measured on the monotonic clock (NB-10).
- THR-7 and THR-8 are our pace, not the provider's limit. They may only be loosened after the
  open question is answered with a documented number.
- All windows of a scope are checked before each request; a request is sent only if every window
  has headroom.
- A budget is per provider account, not per process. Counters live in Redis, keyed by provider,
  account and scope, or one runner lock per account is held. Two jobs on separate in-process counters
  would reach the documented limit together, and PE-23 would stop every India row. If Redis is
  unreachable, or a counter vanishes while a job runs, the client sends nothing until it is back and
  the longest window of that account has passed, for Fyers the rest of the `Asia/Kolkata` day: a lost
  count cannot be told from a free one. The PE-19 day count is
  stored in PostgreSQL. A throttle is built only from the fact it cites (`throttle_matches`).
- THR-13 backfill arithmetic, 500 India instruments: daily since 2000 needs 3 calls each, 1,500
  calls, 45 minutes at 1,000 per 30 minutes; 1-minute bars from January 2022, at one month per
  request (F-43), need 58 calls each,
  29,000 calls, 14.5 hours. The evening batch shares this budget, so the 1-minute backfill runs in
  parts around it.
- THR-14: on a rolling year, Fyers intraday at 100 days per request is 4 calls per instrument, 2,000
  calls for 500 instruments, 80 minutes at 25 per minute, one human login. If "from 2025" means from
  1 January 2025, on 2026-10-30 that is 667 days, 7 calls each, 3,500 calls, over the 2,500-a-day
  budget, so two days and two logins.
- Fyers punishes per-minute breaches with a block for the rest of the day (F-77), so THR-14 is
  enforced before sending, and a limit answer stops the job (PE-19). Two jobs on one Fyers account
  share one budget. THR-14 applies only once a Fyers client exists (OQ-68).

## 9. Error paths

Each row is a provider failure and what the client does. "Order call" means place, modify or
cancel. No row permits a default or substituted value (INV-6).

| # | Condition | Seen as | Class | Fail-closed behaviour |
|---|-----------|---------|-------|-----------------------|
| PE-1 | Kite session expired or invalidated | HTTP 403, `TokenException` (F-8) | AUTH_EXPIRED | India disabled from that moment ([DEFAULT-6]). No automatic re-login. Alert. HITL-7. Orders at the exchange and GTTs are left as they are. |
| PE-2 | Alpaca or other key rejected | HTTP 401 or 403 on a non-order call | AUTH_EXPIRED | That provider is unavailable. No retry with the same key. Alert; HITL-14. A 403 on an Alpaca order call is PE-5, not this row. |
| PE-3 | Rate limit hit | HTTP 429 (Kite, Alpaca, Finnhub, DeepSeek, IBKR) | RATE_LIMITED | Data call: wait until the window resets (the `X-RateLimit-Reset` time where given, otherwise one full window), then at most 3 retries [ASSUMPTION A-42]; after that the job fails and the data is missing. Order call: not retried inside the session's order job; the order is recorded as not sent; alert. Budget halved (section 8.3). |
| PE-4 | Order placed from an unregistered address | Kite: rejection, body not verified (OQ-29). Upstox: `UDAPI1154` | IP_NOT_ALLOWED | India order path disabled; alert. Not retried. The fix is a human change to the IP registration, limited to one per week (UP-15). |
| PE-5 | Insufficient funds or shares | Alpaca HTTP 403 on an order; Kite `MarginException`, `HoldingException` | INSUFFICIENT_FUNDS, INSUFFICIENT_HOLDINGS | The order is not sent again. It means our cash or position state disagrees with the broker's: reconciliation runs before any further order in that market (HITL-8 if a difference remains). |
| PE-6 | Request rejected as invalid | Alpaca HTTP 422 or code `42210000`; Kite `InputException`, HTTP 400; Upstox `UDAPI10xx` | INVALID_REQUEST | Not retried. Recorded with the full response. It is a defect in our code or a stale tick size: the instrument is denied new entries until the instrument master is refreshed. Counts toward RISK-10 ([DEFAULT-5]) and toward Kite's 10 per second (F-16). |
| PE-7 | Order accepted, later rejected by the exchange or risk system | Alpaca status `rejected`; Kite status `REJECTED` with `status_message` | ORDER_REJECTED | Recorded. An entry is not re-sent in that session. A stop or GTT that is rejected leaves a position unprotected: placing the stop is retried once with corrected parameters if the reason is machine-readable, otherwise the position is escalated at once. |
| PE-8 | No response, or connection dropped, after an order call was sent | timeout | UNKNOWN_OUTCOME | Never re-sent blind. The order book is read and matched on `ClientOrderRef` (Alpaca `client_order_id`, Kite `tag`). Found: adopt it. Not found after the book is read successfully: the order was not placed; whether it is sent again is P3.1's rule, with a new audit record. Book unreadable: the market is disabled until it is readable. |
| PE-9 | India GTT triggered but its limit order did not fill | GTT status `triggered`; resulting order `OPEN` or `CANCELLED` at the close | ORDER_REJECTED | The position has no stop. A new GTT cannot fire again for the old one (single use). The system does not watch prices inside the session (HP-4), so it learns this only at reconciliation. Escalated; what is done next is P3.4's rule and OQ-27. |
| PE-10 | India market or `SL-M` order with protection did not fill | order `OPEN`, then `CANCELLED` at the close | ORDER_REJECTED | An emergency exit in India is not assumed complete until the fill is read back. An unfilled exit is escalated. |
| PE-11 | A resting stop or GTT is cancelled by the broker (90-day expiry at Alpaca, 365-day expiry or corporate action at Zerodha) | Alpaca status `expired` or `canceled`; GTT status `expired`, `cancelled`, `disabled` | ORDER_REJECTED | Every session, before entries: each open position is checked for a live stop; a missing one is placed first (REC-4 order). Stops are re-placed ahead of expiry: at 60 days for Alpaca and at 300 days for a GTT [ASSUMPTION A-42]. |
| PE-12 | Broker backend down | Kite HTTP 502, `NetworkException`; any HTTP 503 or 504 | BACKEND_DOWN | That market disabled. Reads are retried with backoff, bounded by PE-25; order calls are not. On recovery: reconcile first. |
| PE-13 | Response does not match the documented shape: missing field, wrong type, unknown status or enum value, duplicate key | validation failure in our client | MALFORMED_RESPONSE | The value is not used. For an order or account response: the market is disabled and reconciliation is required. For data: the record is rejected and the instrument has no data for that session. An unknown status string is never mapped to the nearest known one. |
| PE-14 | LLM does not answer in time | our deadline of 120 seconds per call passes [ASSUMPTION A-42]; DeepSeek may hold a connection up to 10 minutes (F-58) | SERVER_ERROR | The connection is closed. One call to the fallback under the same deadline. Then the LLM step is unavailable for that candidate. No order depends on it (INV-2). |
| PE-15 | LLM account out of credit | DeepSeek HTTP 402 | BALANCE_EXHAUSTED | No retry. Fallback used for the rest of the cycle; alert; a human tops up (HITL-14 class of action). |
| PE-16 | A data provider returns an empty result for a session that the calendar says was open | empty `bars`, empty candle list | MALFORMED_RESPONSE | Empty is not zero volume and is not "no change". The bar is missing: no decision for that instrument (ADR-13 edge case). If more than a threshold of the universe is missing, the whole cycle is skipped; the threshold is P2.2's. |
| PE-17 | Upstox Analytics Token expired or revoked | `UDAPI100050` invalid token, `UDAPI100016` invalid credentials (F-106); HTTP status not verified | AUTH_EXPIRED | Every Upstox job stops. No retry with the same token. Alert; a human generates a new token (HITL-14). Renewal is alerted 30 days before the known expiry [ASSUMPTION A-81], so this path means the alert failed. If a fresh token is refused, this becomes PE-20. |
| PE-18 | Fyers token expired or invalid | HTTP 401 with code -8, -15, -16 or -17 (F-79, F-80) | AUTH_EXPIRED | The pull stops. No scripted login ([DEFAULT-61]). A human logs in after 06:30 and restarts it. |
| PE-19 | Fyers limit or entitlement answer | Any HTTP 429, with or without a code; -429 and -360 are the documented codes (F-77, F-78, F-80) | RATE_LIMITED | The job stops and waits one full window, then resumes at half the pace. A second such answer in the same `Asia/Kolkata` day stops Fyers until the next day, because more than 3 per-minute breaches block the user for the day. The day's count is persisted, so a restart does not clear it. If the request began within 30 days of `fyers.standard_history_start` [ASSUMPTION A-83], PE-21 is checked first. Never a retry loop. |
| PE-20 | Broker account dormant or otherwise restricted | Upstox: `UDAPI100073` inactive `client_id` (F-106). A human generating a token may see "No segments for these users are active" (F-105). Fyers: not verified (OQ-71). Dormancy may also show as an auth failure that persists after a fresh credential, or as empty data night after night | ACCOUNT_RESTRICTED | Permanent until a human acts: never retried, never placed in a retry queue, never mapped to a transient error. A machine assigns this class only on `UDAPI100073`; anything else is held as PE-17, PE-18 or PE-16, stops the job and is classified by a human. It takes precedence over those rows once assigned. Everything depending on that account stops; alert at once; HITL-14. |
| PE-21 | Requested range outside what the plan or endpoint serves, or a partial answer | Upstox `UDAPI1148`; Fyers: possibly HTTP 429 (entitlement), or an answer starting later than asked; not verified (OQ-74) | INVALID_REQUEST | The client checks the range against `fyers.standard_history_start` before sending, so this means the configuration is stale. After any answer, the first returned session is compared with the requested start: a later start is recorded and never treated as "no data before this date". Not retried with a narrower range silently. An empty answer here is PE-16. |
| PE-22 | A vendor series differs from a stored snapshot for the same instrument and session | bar-by-bar comparison over the sessions two snapshots share | MALFORMED_RESPONSE | Neither is overwritten or averaged. A data-quality event is recorded. The two snapshots are not joined across that session ([DEFAULT-62]). Training data for a model stays the snapshot it was built on. Threshold for quarantine is P2.2's. |
| PE-23 | Upstox limit reached | HTTP 429, `UDAPI10005` (F-106); the page warns of temporary suspension of access (F-39) | RATE_LIMITED | Not the PE-3 retry. The job stops for the rest of the session and alerts, because a suspension hits every India row at once. It resumes the next session at half the pace, after a human has looked at it. THR-13 exists so that this never fires. A job stopped here or in PE-19 keeps every instrument and range already complete; the one in progress is partial, is not a snapshot and is discarded. |
| PE-24 | A batch asks for session D and the last returned session is earlier (a stale but well-formed answer) | the highest session date in the answer, which need not be the last row, compared with the expected session from the calendar | MALFORMED_RESPONSE | The bar for D is missing (PE-16 applies), though the response looks valid. No signal is built on the older bar (INV-6). Fetched again in that evening's window; if still absent, the instrument has no data for that session. Candle order is not documented, so the client sorts by session; a duplicate key is PE-13, never resolved by keeping one bar. |
| PE-25 | A data read times out or the connection drops | no response within 30 seconds [ASSUMPTION A-83] | SERVER_ERROR | At most 3 tries with backoff, under the throttle. Then the data is missing (PE-16), never a stale or substituted value. After 20 instruments fail in a row [ASSUMPTION A-83], the job stops and alerts, so an outage costs minutes, not hours. A read that fails this way is not an account problem and does not enter PE-20. |

Errors of the models in section 8:

| # | Condition | Detected by | Fail-closed behaviour |
|---|-----------|-------------|-----------------------|
| E-9 | A `RateLimitFact` field is missing, of the wrong type or out of range | Pydantic `ValidationError` | The fact is not recorded. A throttle cannot be built from it. |
| E-10 | A `ClientThrottle` budget exceeds half the documented limit | the model validator | The client process does not start. |
| E-11 | A `ProviderSelection` is inconsistent | the model validator | The selection table does not load. No client is constructed for any provider. |
| E-12 | A production client is constructed for a selection whose status is not `SELECTED`, or a backup is given for `broker_execution` | a start-up check in each client phase's code | The process does not start. This is why no client can go live while section 6.3 has open items. v0.2: a research client in `v2/research` may start on a PROVISIONAL Upstox row only if a valid `ResearchGateApproval` is on record (section 6.3); it may not start on a BLOCKED row, and its output cannot reach publication. |
| E-13 | A `ClientOrderRef` fails its pattern | Pydantic `ValidationError` | The order is not sent. |
| E-14 | A served LLM model version differs from the one recorded at the last promotion | comparison of the response's model field with the stored value | The LLM output is not used for that call; alert; treated as a T-3 event for the LLM path (P4.2 owns the rule). |
| E-33 | A `VendorSeriesSnapshot` is inconsistent: a missing field, a session after retrieval, a provider that does not serve that market, a basis the evidence does not support, a naive time | Pydantic `ValidationError` | The snapshot is not stored. Its bars are not used. |
| E-35 | `research_gate_open` is false: no valid approval, a revoked one, a row that is not a PROVISIONAL Upstox row, or a bad date | start-up check of a research client | The client does not start. This is the default state. |
| E-34 | An `AccountActivity` record is missing or invalid, its date is in the future, or `today` is not a `date` | `dormancy_status` returns `UNKNOWN`; a bad record fails `ValidationError` at load | The guard treats `UNKNOWN` as overdue and alerts; it does not crash. A missing record is never read as recent activity (INV-6). |
| E-36 | A publication switch is enabled for a market where `publication_data_cleared` is false, or a signal input reaches signal entry from a provider `row_cleared` does not confirm | P1.3 loader, under a proposed MB-E9 (OQ-78); signal entry, P2.7 | The configuration is rejected and publication stays off (MB-AC-14); the input is not used. Until MB-E9 is adopted, the loader part is a requirement on P1.3 and not yet a rule of `MODEL-B-DECISION.md`. |

## 10. Documentation that could not be verified

Pages that were needed and were not read, or were reached and did not contain the fact. Nothing
from these is stated as fact anywhere above, except where a row says a figure was re-used from an
earlier record.

| # | URL or document | What was needed | Why it is unverified |
|---|-----------------|-----------------|----------------------|
| 1 | https://www.sec.gov/os/accessing-edgar-data and https://www.sec.gov/search-filings/edgar-application-programming-interfaces | EDGAR fair-access rate, `User-Agent` rule, endpoint list | Not requested: Owner's pause on SEC hosts |
| 2 | https://data.sec.gov (submissions and company-facts endpoints) | Field names and types | Not requested: same pause |
| 3 | https://kite.trade/docs/connect/v3/gtt/ and the Zerodha GTT article | Whether a GTT can place anything but a limit order | The two Zerodha pages disagree |
| 4 | Kite Connect terms and conditions (URL not located) | Automated login, data storage, redistribution | Page not located |
| 5 | https://kite.trade/forum/discussion/16212/batch-automating-kite-login and https://kite.trade/forum/discussion/9770/automating-retrieval-of-request-token | Staff statement on daily manual login | Search excerpt only |
| 6 | https://kite.trade/docs/connect/v3/historical/ | Adjustment of candles, range per request, history depth | Reached; not stated on the page |
| 7 | https://kite.trade/docs/connect/v3/websocket/ | Reconnect and replay behaviour | Reached; not stated |
| 8 | https://kite.trade/docs/connect/v3/orders/ | Zone of order timestamps; the place-order path; `guid` semantics; rejection list | Reached; not stated |
| 9 | https://alpaca.markets/support/usage-limit-api-calls | Trading API throttle of 200 per minute | Search excerpt only |
| 10 | https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf | Fee schedule | Search excerpt only |
| 11 | https://docs.alpaca.markets/reference/getaccount-1 | A settled-cash field | Reached; no such field described |
| 12 | https://docs.alpaca.markets/reference/patchaccountconfig-1 | Meaning of `max_margin_multiplier` = `"1"` | Reached; description absent |
| 13 | https://docs.alpaca.markets/docs/websocket-streaming and https://docs.alpaca.markets/docs/streaming-market-data | Heartbeat, connection limit, replay after reconnect | Reached; not stated |
| 14 | Alpaca references for cancel, replace, list orders, get order by client order id, positions, calendar, clock | Paths and fields | Not fetched in this run |
| 15 | https://alpaca.markets/support/countries-alpaca-is-available | Whether India is supported | Reached; the page has no list |
| 16 | Alpaca documentation sets "Alpaca India - Domestic" and "Alpaca India - GIFT City" (under docs.alpaca.markets) | What they offer an Indian resident | Seen only as names in page metadata |
| 17 | Alpaca customer agreement and market-data agreement | Automated trading, storage, redistribution, news text use | Not located |
| 18 | https://massive.com/docs (splits, dividends, ticker types, grouped daily, authentication, WebSocket) | Fields and behaviour | Not fetched; two pages were read |
| 19 | Massive terms and the "non-pros only" page | Individual-use restriction, storage | Not read |
| 20 | https://finnhub.io/docs/api (company-news endpoint) and Finnhub terms | Fields, storage and commercial-use terms | Not fetched |
| 21 | https://site.financialmodelingprep.com/developer/docs (statement endpoints) | Fields, filing dates, India coverage, Starter price | Pricing page read; price ambiguous; endpoints not fetched |
| 22 | https://fred.stlouisfed.org/docs/api/fred/ (errors and limits) | Numeric rate limit | Not stated on the two pages read |
| 23 | https://api-docs.deepseek.com (first call, chat completion reference, terms) | Base URL, auth header, model aliases, data terms | Not fetched; three pages were read |
| 24 | https://developers.openai.com/api/docs (deprecations, rate limits, data controls) | Shutdown date, tier limits, retention | Not fetched; one page was read |
| 25 | https://www.interactivebrokers.com/campus/ibkr-api-page/web-api-trading/ | Authentication detail, 2FA, order types | Reached by extraction; direct fetch returned HTTP 403; page dated 2024-12-17 |
| 26 | https://upstox.com/developer/api-documentation/v3/place-gtt-order/ | GTT v3 page | HTTP 404; the non-v3 path was read instead |
| 27 | Upstox terms; sandbox documentation | Unattended TOTP login, sandbox scope | Not fetched |
| 28 | https://www.nseindia.com/static/nse-terms-of-use | Exact clause on automated collection | Fetch timed out; search excerpt only |
| 29 | https://www.nseindia.com/static/market-data/eod-historical-data-subscription and https://www.nseindia.com/static/market-data/nse-data-policy | Price, licence, delisted coverage | Search excerpt only |
| 30 | https://www.nseindia.com/static/market-data/market-timings and https://www.nseindia.com/resources/exchange-communication-holidays | Session times and holidays | Search excerpt only; holiday list not seen |
| 31 | https://www.bseindia.com (trading hours, holidays, data products) | BSE equivalents | Not fetched |
| 32 | https://nsearchives.nseindia.com/content/circulars/INVG67858.pdf | NSE circular of 2025-05-05 on retail algo trading | Not fetched; cited by Upstox |
| 33 | SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 at sebi.gov.in | Full text (OQ-1) | Not fetched |
| 34 | https://www.fbil.org.in (reference rates) | USD/INR reference rate and its publication time (OQ-22) | Not fetched |
| 35 | Broker and vendor status pages (Alpaca, Zerodha, Massive, DeepSeek, OpenAI) | Outage history and maintenance windows | Not fetched |
| 36 | Exchange and broker settlement pages | T+1 settlement in both markets (A-27) | Not fetched |
| 37 | Upstox API or developer terms (no URL located; a forum post refers to "API Terms") | Storage, redistribution, commercial use, derived works | Searched upstox.com and its community; only general website terms were found |
| 38 | https://community.upstox.com (posts on adjustment and delisted symbols) | Vendor statement on adjustment and delisted coverage | Search returned no such post |
| 39 | https://upstox.com/developer/api-documentation/get-balance-sheet and the cash-flow, holdings, ratios and competitors pages | Fields | Not fetched; the index and three sibling pages were read |
| 40 | https://upstox.com/developer/api-documentation/appendix/equity-security-type | `security_type` codes | Not fetched |
| 41 | https://fyers.in/api-docs/v3/api/websockets/data-socket/ and the General socket pages | Heartbeat, replay | Not fetched; the overview was read |
| 42 | https://fyers.in/community/t/how-do-we-adjust-historical-prices-downloaded-and-saved-on-our-local-system-through-the-fyers-api-based-on-corporate-actions/22441 | Whether stored data must be re-fetched after a corporate action | Fetch failed; search excerpt only |
| 43 | NSE circular INSP49743; the BSE notice cited with it; Fyers KB pages reported to give 24 months | Dormancy wording | Not read; the one Fyers KB article cited in #68 was re-read (F-97) |
| 44 | https://docs.benzinga.io/benzinga/newsfeed-v2.html | Whether the TCP stream carries the headlines; latency | Not fetched; the product page was read |
| 45 | https://docs.alpaca.markets/us/docs/streaming-real-time-news | Real-time news stream | Not fetched: Alpaca work is held until #68 lands (issue #2) |
| 46 | Exchange data redistribution policies at NSE and BSE | Whether a signal derived from exchange data needs an exchange licence | Not fetched; part of OQ-68 |
| 47 | https://community.upstox.com/t/subscription-model-nse-data-licence-and-multi-user-api-access-written-clarification-needed/17264 and https://upstox.com/uplink/business-trading-api/ | Upstox's reply on a paid analytics product, an NSE licence and multi-user access; business terms | The question was read; the fetch did not return the reply text; the form page was not fetched |
| 48 | Upstox Market Timings page and the path of Intraday Candle Data V3 | Session times; exact path | Not fetched, or inside excluded code samples |
| 49 | Fyers refresh-token documentation and the KB article reported to give 15 days | Whether a refresh works for a non-trading app | Not read; found only as a sample field (F-79) and through the X2 review |

## 11. Non-blocking details resolved in this spec

| # | Detail | Resolution |
|---|--------|------------|
| NB-28 | Money and price types from providers | Kite returns prices as JSON numbers (`float64`); Alpaca returns strings. Both are parsed into `Decimal` from the response text, never through a binary float (NB-3). A JSON parser is configured to read numbers as `Decimal`. |
| NB-29 | Kite WebSocket prices | Integers in paise; divided by 100 as `Decimal`. Not used by any decision in v1. |
| NB-30 | Timestamps | Alpaca: RFC 3339; examples are UTC; a timestamp without an offset is rejected (PE-13). Kite candles: `+0530`. Kite order timestamps: zone not documented; treated as `Asia/Kolkata` [ASSUMPTION A-39]. Massive `t`: Unix milliseconds, UTC by definition of Unix time. All are stored as UTC instants plus the exchange session date (NB-4). |
| NB-31 | Daily bar identity | A daily bar is keyed by market, instrument and session date, never by the vendor's timestamp, because vendors stamp daily bars differently (start of window, midnight UTC, midnight IST). |
| NB-32 | Request date bounds | Alpaca `start` and `end` are inclusive. Upstox `to_date` is inclusive. Kite `from` and `to`: inclusiveness not stated (OQ-30); the client requests one extra day on each side and discards rows outside the range. |
| NB-33 | Pagination | Alpaca `limit` counts points across all symbols, not per symbol; the client pages until `next_page_token` is null and treats a missing token field as PE-13. |
| NB-34 | Tick size | US: 2 decimals at or above USD 1.00, 4 below (F-21); a price is rounded to the tick toward the passive side (down for a buy limit, down for a sell stop). India: `tick_size` from the Upstox instrument file, used only once its unit is confirmed (OQ-75); until then no signal that needs the tick is built for that instrument (INV-6). The Kite dump is deferred. The rounding direction for a stop is confirmed by P3.4. |
| NB-35 | Lot size | India cash equities: `lot_size` from the Upstox instrument file is read, not assumed to be 1. Quantity is a multiple of it, rounded down (NB-22). |
| NB-36 | Alpaca `opg` and `cls` windows | Not used. Entries are `limit`, `day` orders submitted before the open ([RISK-13], HP-2). The 09:28 ET cutoff therefore does not apply. |
| NB-37 | GTC expiry arithmetic | 90 days are calendar days from creation; the cancel runs at 16:15 ET on the expiry date. Re-placement at 60 days leaves 30 calendar days of margin. |
| NB-38 | Kite token boundary | Expiry at 06:00 `Asia/Kolkata`; India has no daylight saving. A token obtained at 05:59 lasts one minute. Login is accepted by our system only after 06:00. |
| NB-39 | India evening window | A token obtained in the morning is valid until 06:00 the next day, so after the 15:30 close there are 14 hours 30 minutes in which the same token works. Whether next-session entries are placed in that window as after-market orders is P3.2's decision; it would not remove the morning login, because stops for new fills need a valid session during the next session. |
| NB-40 | DST and the LLM price windows | DeepSeek peak windows are fixed in UTC; the US close moves between 20:00 and 21:00 UTC with daylight saving; both are off-peak. |
| NB-41 | Percent units in fees | Fees are recorded as written by the provider (0.1% is stored as 0.1 under A-4); the SEC fee is a multiplier of trade value (0.0000206), stored as a rate with its unit stated. |
| NB-42 | Fee rounding | Alpaca rounds regulatory fees up to the cent (F-37). P5.3 models that, not half-even. |
| NB-43 | API keys in URLs | Where a provider accepts a key as a query parameter or as a header (Finnhub; FRED takes it only as a parameter), the header is used when available; for FRED the URL is never logged with its query string. |
| NB-44 | 09:31 | Read as local exchange time of the provider's market (section 7). |
| NB-63 | Upstox instrument key in a URL path | The key holds a pipe character, as in the F-41 example, and is percent-encoded in the path (F-90 sample). The allowlist check runs on the decoded path. |
| NB-64 | Upstox date ranges | `to_date` comes first in the path and is inclusive; `from_date` is optional. The client always sends both, so a default range never decides what is fetched. |
| NB-65 | Fyers daily candle stamp | Epoch seconds; the instant that defines a daily candle is not stated. NB-31 applies: the bar is keyed by session date, derived in `Asia/Kolkata`. |
| NB-66 | Fyers partial candles | `range_to` is set at least one resolution before now; a batch run after the close meets this by construction. |
| NB-67 | Fyers error code -352 | Means both an invalid App ID and no position to exit (F-80). The read-only client only ever treats it as the App ID case; any other reading is PE-13. |
| NB-68 | Indian number formats in vendor pages | `5,00,000` is 500,000; `1,00,000` is 100,000. Recorded here in plain digits. |
| NB-69 | Crore | Upstox fundamentals report INR crore (F-88). 1 crore is 10,000,000. Stored with the unit stated; never multiplied through a binary float (NB-3). |
| NB-70 | Fyers and Upstox symbols | `NSE:SBIN-EQ` and the Upstox `instrument_key` are vendor keys. The internal identifier of UNI-4 maps through ISIN, present in both masters (F-81, F-91). A symbol change therefore does not break a series; an ISIN change at a split might (OQ-69). |
| NB-71 | Upstox decade boundary | "1 decade" is not defined further. Requests run by calendar decade with `to_date` inclusive; rows outside the range are discarded, and an overlap of one day is requested at each boundary. A gap at a boundary is PE-16. |
| NB-72 | Fyers 100-day window and plan start | Calendar or trading days is not stated. The client counts calendar days, the shorter reading. A request is clamped to `fyers.standard_history_start`, and the clamp is recorded on the snapshot's job log, never silent. |
| NB-73 | Intraday bar identity | NB-31 covers daily bars only. A 1-minute bar is keyed by market, instrument and the UTC instant of the start of its minute. |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| D-11 | Selections SEL-1 to SEL-23 as in section 6.3; none is SELECTED; the spec stays DRAFT. | ADR-11: a phase is not frozen for one market. Facts are missing, mostly for India. | Yes. | Every client phase. |
| D-12 | US daily bars come from Massive (Developer plan, 10 years), with Alpaca Market Data as backup. | INV-10 requires a data provider separate from the broker; highest score; point-in-time ticker reference. | Yes; a switch is a T-3 event. | P2.1, P2.3, P5.x. |
| D-13 | Raw bars and corporate actions are stored separately; adjustment is ours. Requests use `adjusted=false` (Massive) and `adjustment=raw` (Alpaca). | [DEFAULT-26]; point-in-time integrity; vendor restatements must not move stored values. | Costly after data is stored. | P2.1, P2.4. |
| D-14 | No WebSocket stream is a system of record. State is read over REST after every disconnect and at least once per session. | No provider documents replay of missed events (F-12, F-30, F-31, F-44). | Yes. | P3.1, P5.5. |
| D-15 | No order call is retried blind. An unknown outcome is resolved by reading the order book and matching `ClientOrderRef`. | Kite has no idempotency key; Alpaca's duplicate behaviour is unverified. | Yes. | P3.1. |
| D-16 | Credentials are sent in headers wherever the provider accepts them. | A key in a URL reaches logs. | Yes. | P6.2. |
| D-17 | Before India goes live, the recovery host's address is registered as Zerodha's secondary static IP. | UP-15: one IP change per calendar week against an RTO of 4 hours. | Yes. | P6.4, ADR-10. |
| D-18 | LLM model identifiers are `deepseek-flash` and `gpt-4o-mini-2024-07-18`; the served model version is recorded with every call. | UP-18. | Yes. | P4.2, P0.3. |
| D-19 | The India resting stop is a single-leg sell GTT ([DEFAULT-22]); the US resting stop is a `stop`, `gtc` order ([DEFAULT-23]); whole shares only ([DEFAULT-24]). | F-9, F-10, F-21, F-23. | Yes. | P2.10, P3.4. |
| D-20 | Interactive Brokers and Upstox are cold alternates for execution: documented here, not integrated, not funded. v0.2: this now covers execution only; Upstox has a data role (D-39). | ADR-10; UP-19. | Yes, by new ADR. | None while unused. |
| D-21 | SEC EDGAR is not contacted and no client for it is written until the Owner lifts the pause and names the contact identity for the `User-Agent`. | Owner's instruction; [DEFAULT-28]. | Yes. | US fundamentals features. |
| D-22 | Client request budgets are at most half of each documented limit (THR-1 to THR-14). | [DEFAULT-31]; the kill switch shares the account limit. | Yes. | Backfill duration. |
| D-23 | The decision matrix of section 6.1 (six criteria, weights 30/20/15/15/10/10) is the selection method; a constitution-fixed provider is primary regardless of score. | The prompt requires a weighted matrix; INV-10 and STACK-1 are not open to redesign. | Yes. | Selections. |
| D-39 | India data rows are as in section 6.3: Upstox primary for daily bars, intraday bars, instrument master, corporate actions, news, sector and calendar; Fyers Standard backup for daily bars and the master, with no intraday backup; Kite leaves the data rows. | Matrix; Model B removes Kite's tie-break; Owner decision of 2026-10-17 as far as its facts hold. | Yes; a source change is T-3. | P2.1, P2.3, P4.1, P5.x. |
| D-40 | The only Upstox credential in v1 is the Analytics Token. | It cannot place an order (F-87); no daily human step. | Yes. | P2.1, P6.2. |
| D-41 | Fyers has no scheduled job and no scripted login, uses a non-trading app only, and has no client until OQ-68 is answered for Fyers. | [DEFAULT-61]; F-79; F-82; F-103; F-104. | Yes, by Owner choice of Prime and a written answer. | Backup is manual. |
| D-42 | India bars are stored as immutable snapshots of complete fetches, labelled by adjustment basis, each re-requesting the last 5 sessions, and are not joined across a corporate action. Completeness is per instrument and range: a partial one is discarded, finished ones are kept. | [DEFAULT-62]; F-84. | Costly after data is stored. | P2.1, P2.4, P5.x. |
| D-43 | `intraday_bars` is for research only; signal entry accepts `1D` bars only, and every signal input only from a provider `row_cleared` confirms, with a test for each. | HP-1; Model B has no intraday signals; `v2/signals` may import `v2/research`, so an import check is not enough, and a research snapshot must not reach a signal through storage. | Yes. | P2.1, P2.7, P4.x. |
| D-44 | No data row of either market may feed a published signal, and no row of OQ-68 becomes SELECTED, until its licence is answered in writing. Research runs only under the Owner-opened gate of section 6.3. | MB-AC-14; BO-1; F-82; F-92; F-100. | No: it is the rule. | Go-live in both markets. |
| D-45 | `ACCOUNT_RESTRICTED` is never retried; the dormancy guard runs per account. | #68; F-97. | Yes. | P2.1, P6.1. |
| D-46 | No SEC host is contacted; EDGAR facts stay SECONDARY until the Owner lifts the pause. | O-16; [DEFAULT-28]. | Yes. | US fundamentals. |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| A-37 | The PRIMARY_EXTRACT facts in section 3 state their source pages accurately. | They were read through automated extraction, not line by line. | Full read by the phase named in the register. | Any field name, limit or fee in section 5. |
| A-38 | [DEFAULT-22] to [DEFAULT-31] as given in section 1. | Each is a fork with no Owner ruling. | Owner reviews BQ-11 to BQ-20. | As stated per row in section 1. |
| A-39 | Kite order and trade timestamps without an offset are `Asia/Kolkata`. | The page does not state the zone. | OQ-30. | Fill times wrong by 5 hours 30 minutes in the audit trail. |
| A-40 | A request to `GET /v2/account/configurations` style paths and the Kite place-order path follow the patterns shown in section 5. | Derived from reference page names and sibling paths, not read. | OQ-31, OQ-34. | Client code fails at first call; no trading risk. |
| A-41 | Client pace of 5 requests per second for Massive and 1 per second for FRED. | No numeric limit is published on the pages read. These are our pace, not a claimed limit. | OQ-38, OQ-42. | A 429 or a block during backfill. |
| A-42 | Three retries on a data 429; LLM deadline 120 seconds; stops re-placed at 60 days (Alpaca) and 300 days (GTT). | No data to derive them; chosen inside the documented lifetimes (90 and 365 days, 10-minute server timeout). | P3.4, P4.2, P6.1 after paper trading. | Slow cycles, or a stop that lapses if the re-placement job fails for 30 or 65 consecutive days. |
| A-43 | DeepSeek's `$` prices are US dollars. | The page gives no currency code. | OQ-43. | LLM budget in P0.3. |
| A-44 | The 10 orders per second threshold and the static-IP rule apply to this account as an individual client running its own logic. | Read from broker pages, not from the SEBI or NSE circular. | OQ-51, OQ-1. | Registration requirements in P6.3. |
| A-45 | Alpaca's Trading API limit is 200 requests per minute per account. | Seen only as a search excerpt of Alpaca's support article. | Read the article; OQ-34. | THR-5. |
| A-46 | Zerodha's static-IP requirement took effect on 1 April 2026. | The article says 2026; the FAQ says 2025; the staff forum post is dated late March with a 1 April deadline. | OQ-29. | None for a system going live after both dates. |
| A-76 | The Fyers expiry of "6:30 AM" is `Asia/Kolkata`. | The pages give no zone. | OQ-74. | A pull starts with a token that dies within the hour. |
| A-77 | [DEFAULT-59] to [DEFAULT-64] as given in section 1. | Each is a fork with no Owner ruling. | Owner reviews BQ-48 to BQ-53. | As stated per row. |
| A-78 | A read-only Upstox token may be used by an unattended job for its year. | F-87 describes no restriction; API terms were not found. | OQ-68. | Back to a daily login, or to no Upstox data. |
| A-79 | Upstox candles are treated as of unknown adjustment, and as restatable. | The pages say nothing. | OQ-69. | If raw, the snapshot rule costs a little storage and nothing else. |
| A-80 | The Upstox instrument files need no token. | The URLs are public paths; the page does not say. | Fetch one with no token in the first code phase; OQ-75. | The master joins the token's failure path. |
| A-81 | Renew the Upstox token 30 days before expiry. | No data to derive them; chosen inside the documented lives. | P6.1 after operation. | A late renewal stops India data. |
| A-82 | Backfill estimates in section 8.3 assume 500 India instruments (ADR-14) and calls at the client budget. | Measured values do not exist. | P2.1 first backfill. | Longer backfill. |
| A-83 | Each fetch re-requests the last 5 sessions; a data read times out at 30 seconds, with at most 3 tries; a job stops after 20 instruments fail in a row; a Fyers 429 within 30 days of the plan start is checked as a range problem first. | No data to derive them; chosen to catch a restatement and to bound a stalled batch. | P2.1 first month of operation. | A restatement older than 5 sessions is missed until the next full fetch; a slow provider costs a session. |

A-33 and A-27 of P0.1 remain assumptions (OQ-48). A-26 is confirmed for the regular-session
times of NYSE (PRIMARY_EXTRACT) and NSE (SEARCH_EXCERPT).

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| OQ-27 | UP-11: does the Owner accept a single-use, limit-order GTT as the India "resting stop", and can a Kite API GTT place a market order with protection? | Owner; Zerodha | Ruling on UP-11. kite.trade/docs/connect/v3/gtt (order_type); Kite forum, search "GTT market order API" | P2.10, P3.4, India go-live |
| OQ-28 | Do Kite Connect's terms prohibit automated login, and what is the exchange rule requiring a daily manual login? | Zerodha | Kite Connect terms on developers.kite.trade; forum threads 16212 and 9770 read in full | P3.1 |
| OQ-29 | Zerodha static IP: effective date; response to an order from an unregistered address; whether GTT, modify and cancel calls are IP-checked. | Zerodha | support.zerodha.com article "static-ip"; kite.trade/forum/discussion/15912 | P3.1, P6.4 |
| OQ-30 | Kite historical data: are daily candles adjusted for splits, bonus issues and dividends; maximum range per request; history depth; inclusiveness of `from`/`to`; zone of order timestamps. | Zerodha | kite.trade/docs/connect/v3/historical; Kite forum FAQ thread 4732 | Only if Kite data is activated (v0.2) |
| OQ-31 | Kite: place-order path confirmation; `guid` semantics; is a duplicate `tag` rejected; WebSocket reconnect and replay; after-market order behaviour. | Zerodha | kite.trade/docs/connect/v3/orders and /websocket; pykiteconnect source | P3.1, P3.2 |
| OQ-32 | Kite: list of order rejection reasons (`status_message`); outage history and maintenance windows. | Zerodha | Kite forum; Zerodha status and bulletin pages | P3.1, P3.4 |
| OQ-33 | Alpaca (rest of OQ-15): which field or method gives settled cash; what `max_margin_multiplier="1"` does; can an account be cash-only (UP-21); how a same-day stop exit is treated under the intraday margin framework. | Alpaca | docs.alpaca.markets: account, account configurations, margin; Alpaca support | P2.8, P2.9 |
| OQ-34 | Alpaca Trading API: paths and fields for cancel, replace, list, get-by-client-order-id, positions; response to a duplicate `client_order_id` and its charset; 429 body and headers; stream heartbeat and replay; treatment of a `gtc` stop on a split; minimum and maximum quantity; complete rejection codes; IP allowlisting. | Alpaca | docs.alpaca.markets/reference (orders, positions); alpaca.markets/support/usage-limit-api-calls | P3.1, P3.4 |
| OQ-35 | Alpaca and India (OQ-6, OQ-14 widened): is an Indian resident eligible for a US live account; what are "Alpaca India - Domestic" and "Alpaca India - GIFT City"; do they change the LRS analysis in UP-4? | Alpaca; a qualified adviser | Alpaca support; docs.alpaca.markets India documentation sets | US go-live, P6.3 |
| OQ-36 | Alpaca Market Data: are bars served for delisted symbols; corporate-actions history depth; calendar and clock endpoint fields; how the daily bar session is defined. | Alpaca | docs.alpaca.markets/reference (stock bars, corporate actions, calendar) | P2.1 |
| OQ-37 | May Alpaca bars and news be stored indefinitely, and may news text be sent to DeepSeek or OpenAI for processing? | Alpaca; Benzinga | Alpaca market data agreement; Alpaca customer agreement | P2.1, P4.1 |
| OQ-38 | Massive: bars for delisted tickers; `active=false`; ticker `type` codes for common stock, ETF and depositary receipt; split and dividend endpoints; whole-market daily endpoint; daily bar zone; fair-use behind "unlimited"; 429 behaviour; auth header; non-professional and storage terms; sector or SIC field. | Massive | massive.com/docs/rest/stocks; massive.com terms; the "non-pros only" page | P2.1, P2.3 |
| OQ-39 | India whole-market daily history including delisted stocks: product, price, licence and format from NSE Data & Analytics; the BSE equivalent (part of OQ-19). | NSE Data & Analytics; BSE | nseindia.com/static/market-data/eod-historical-data-subscription; NSE data policy; bseindia.com data products | P0.3, P2.1, P2.3, P5.x |
| OQ-40 | v0.2, narrowed: a second India source, with licence, for corporate actions, fundamentals, news and sector, since Upstox is the only candidate for each; and a point-in-time India fundamentals source. | NSE, BSE, data vendors | NSE and BSE corporate-filings data products; vendor coverage pages (FMP Ultimate, Finnhub) | P2.1, P2.3, P4.1 |
| OQ-41 | SEC EDGAR, Owner decision: does the pause stand, given `SPEC-P2N.13` section 15 records a live request after it (UP-47); which contact identity goes in the `User-Agent`; then the primary facts (rate, 429 behaviour, endpoints, fields, SIC as a sector source, fair-access terms). | Owner; SEC | Owner decision; then sec.gov "Accessing EDGAR Data" and the EDGAR API page | P2.1, P2.3 |
| OQ-42 | FRED: numeric rate limit and 429 body; representation of a missing observation; whether storing observations is permitted; a source for India macro series. | Federal Reserve Bank of St. Louis; RBI | fred.stlouisfed.org/docs/api/fred (errors); FRED terms read in full; RBI database pages | P2.1 |
| OQ-43 | DeepSeek: base URL and auth header; is `deepseek-chat` still accepted; can a dated version be pinned; default output limit; currency of prices; data retention, training use and processing location. | DeepSeek | api-docs.deepseek.com: first API call, chat completion reference, model list; DeepSeek terms and privacy policy | P0.3, P4.2 |
| OQ-44 | OpenAI: shutdown date of `gpt-4o-mini`; the account's usage tier; data retention terms; 429 body. | OpenAI | developers.openai.com/api/docs: deprecations, rate limits, data controls | P0.3, P4.2 |
| OQ-45 | Interactive Brokers: 2FA and daily login for the gateway; session lifetime; customer order id; order types and time in force; API permissions for Indian residents. | Interactive Brokers | IBKR Campus Web API pages | Only if the alternate is activated |
| OQ-46 | Upstox: may the TOTP token endpoint be called unattended; maximum GTTs; `extended_token` validity. v0.2: adjustment and delisted coverage moved to OQ-69; sandbox scope answered by F-93 at excerpt level. | Upstox | upstox.com/developer/api-documentation: get-token; Upstox terms | Only if activated |
| OQ-47 | FMP: Starter price (USD 19 or USD 49); Ultimate price; India coverage; do statements carry filing and acceptance dates; endpoint fields. | FMP | site.financialmodelingprep.com pricing and developer docs | P0.3, P2.1 |
| OQ-48 | Settlement cycle in both markets (A-27); is a same-day buy and sell under `CNC` charged and taxed as intraday (A-33). | Exchanges; Zerodha | NSE and BSE settlement pages; a US clearing or FINRA page on T+1; zerodha.com/charges; Zerodha support | P2.8, P5.3 |
| OQ-49 | NSE and BSE: exact pre-open order-collection close; holiday and special-session lists for 2026 and 2027; BSE session times (rest of OQ-26). | NSE, BSE | nseindia.com/resources/exchange-communication-holidays; bseindia.com trading holidays | P2.1 |
| OQ-50 | Finnhub: company-news endpoint fields; what "Personal Use" permits; storage; India coverage. | Finnhub | finnhub.io/docs/api/company-news; finnhub.io terms of service | P4.1 |
| OQ-51 | Rest of OQ-1: for an unregistered client strategy under 10 orders per second, who generates the exchange order tag and does the client send anything; is the threshold counted per exchange, per segment or per client. | NSE; SEBI; Zerodha | NSE circular INVG67858 (2025-05-05) and INVG69255 (2025-07-22); the NSE retail-algo FAQ of 2025-11-03; SEBI circular text | P2.9, P6.3 |
| OQ-67 | Owner decision: accept Upstox as the India intraday source, or buy Fyers Prime. If Prime: does it reach 3 July 2017 (the pages say both that and "5+ years"), does the depth apply to the API, and when does the waitlist open? | Owner; Fyers | BQ-48; fyers.in/prime; ask Fyers support to confirm the earliest intraday date on Prime through `/data/history` | P2.1, the event study |
| OQ-68 | Legal: does the Owner's own Upstox token count as a user's broker credential under MB-2 and MB-AC-4? May India market data from Upstox and Fyers be stored, used in a backtest, used to run a model portfolio and track record, and used to derive signals published to users, paying or not? Is written consent available, on what terms, and from which entity? Does an exchange licence also apply? Which account holds the credential, an individual's or a company's? For Fyers, does research use fall inside "legitimate, fair and transparent trading"? Upstox's answer so far is a forum reply (F-100); its API terms must be located. | Upstox business team; Fyers; NSE, BSE; qualified counsel | Upstox: Business Trading API form or api@upstox.com, describing the Model B use. Fyers, first: can it be used at all under Model B? F-82 sections 2, 3, 8, 9, 11, 12, 15, 17, in writing. NSE and BSE data policies | Every India data row; MB-AC-14; P6.3 |
| OQ-69 | Upstox: are candles adjusted; are they restated after a corporate action; does a historical query answer for a delisted ISIN; does history survive an ISIN change at a split (from general knowledge, not a vendor page: Indian splits commonly issue a new ISIN)? Do corporate actions answer for the old ISIN? | Upstox | Ticket drafted on #68, questions 3 and 4, plus the ISIN question | P2.1, P5.x |
| OQ-70 | Fyers: which actions adjust the series (dividends too?); are delisted symbols served; confirm F-85 from a staff source. | Fyers | Ticket drafted on #68, questions 3 and 4 | P2.1, P5.x |
| OQ-71 | A standard access token needs an active segment (F-105). Still open: can an Analytics Token be generated, or keep working, on a dormant account; what activity keeps a segment active (a trade, a KYC update, a login); the Fyers answers to the same, and its 12 or 24 months. If the Owner becomes the registered RA, does a keep-alive trade fall inside the personal-trading window of IN-4, and is a KYC update enough? | Upstox; Fyers | Tickets drafted on #68, questions 1 and 2; Fyers KB pages; counsel for the IN-4 point | P2.1, P6.1 |
| OQ-72 | Does Alpaca's news feed still carry Benzinga's headline stream at the 2022 volume, and from what date? Narrowed by F-95 and F-99. | Alpaca; a day of measurement | Same as `SPEC-P2N.13` OQ-4; count one day of `/v1beta1/news`; held until #68 lands | P4.1, if Alpaca stays in scope |
| OQ-73 | Upstox fundamentals and corporate actions: publication or filing date, history depth, the vendor behind them, restatement; are mergers, demergers and delistings included; is `sector` a stable taxonomy and is its history available? | Upstox | Sibling pages in section 10 row 39; Upstox support | P2.1, P2.3 |
| OQ-74 | Fyers: does `refresh_token` work for a non-trading app under F-103, and for how long; login URL and API hosts; zone of the 6:30 AM expiry; response to an out-of-plan or straddling range; whether "from 2025" is a rolling year or 1 January 2025; WebSocket heartbeat and replay. | Fyers | fyers.in/api-docs: generate-auth-code samples, data-socket pages, status.fyers.in; Fyers support | The ranking in section 6.2; any Fyers client |
| OQ-75 | Upstox: when a finished session appears in the historical endpoint; exact path of Intraday V3; `security_type` codes; unit of `tick_size` (the CSV sample shows 0.05, the JSON sample 5.0, possibly paise); do instrument files need a token; do Market Holidays cover past years? | Upstox | upstox.com/developer/api-documentation: error-codes, get-intra-day-candle-data, appendix, get-market-holidays; one unauthenticated fetch of a file; one call with a past date | P2.1 |
| OQ-76 | Upstox News: who supplies the articles; may they be stored; may the text be sent to DeepSeek or OpenAI? | Upstox | Upstox support; the licence chain named in the answer | P4.1 |
| OQ-77 | Is US intraday needed at all, and from whom? The Owner's decision covers India. | Owner, after #68; the event-study phase | `SPEC-P2N.13` sections 15 to 18 | The US side of any event study |
| OQ-78 | Owner: add error path MB-E9 to `MODEL-B-DECISION.md`, so that an enabled publication switch is rejected unless `publication_data_cleared` is true for that market? This spec cannot change that document. | Owner | E-36; `MODEL-B-DECISION.md` section 9, MB-E1 to MB-E8 | P1.3, publication in either market |
| OQ-79 | Which capabilities are signal inputs of the strategy to be published? `publication_data_cleared` counts every capability outside `NOT_SIGNAL_INPUTS`, which includes rows that may never carry a licence: `fundamentals` (BLOCKED in both markets), US `sector_taxonomy` (UNFILLED), the NYSE calendar file and `llm`. Neither market can clear until a spec amendment narrows the set. | Owner, at the first frozen strategy | Section 6.3 | Publication in either market |
| OQ-80 | A research run may train a model on a row never licensed, such as SEL-22, and neither gate sees it. Does a model calibrated on research data count as a derived work (for counsel, with OQ-68)? The phase that promotes a model records which providers trained it, and publication then needs `row_cleared` for each, or counsel's written answer that it is not required. | Counsel, Owner | MB-AC-14; ADR-07; section 6.3 | Promotion of a model trained under the research gate |

Upstream questions answered or narrowed by this spec:
- OQ-7: answered in substance (F-6; F-20 as excerpt). The terms text remains OQ-28.
- OQ-11: answered. US: `stop`, `gtc`, 90 days. India: no resting stop order; GTT, 365 days,
  with the limits in UP-11.
- OQ-15: partly answered. No borrowing-prevention setting is described beyond
  `max_margin_multiplier` and `no_shorting`; no settled-cash field; fractional orders are `day`
  only. The rest is OQ-33.
- OQ-1: partly answered (10 orders per second per client; static IP for order placement). The
  rest is OQ-51.
- OQ-19: narrowed to OQ-38 (US) and OQ-39 (India). The counts of listed and delisted stocks
  were not obtained.
- OQ-26: NYSE answered; NSE by excerpt; BSE and settlement open (OQ-48, OQ-49).
- OQ-22: not addressed; still open.
- OQ-6, OQ-14: not answered; widened by OQ-35.

Answered or narrowed by v0.2:
- #68 open item 2 (data-only account): account opening is free and neither broker requires funding
  (F-97); dormancy is OQ-71.
- #68 open item 3 (two static IPs): does not arise in v1. Upstox data needs no static IP (F-87,
  F-101), and no order is sent (BA-1).
- #68 open item 4 (daily auth): answered, UP-45.
- #68 open item 5 (delisted): narrowed, UP-43, OQ-69, OQ-70.
- `SPEC-P2N.13` OQ-14 (free intraday): Fyers no longer closes it. Upstox does if the Owner accepts the substitute (UP-40, decision 1 in section 0).

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| F-6..F-64, F-77..F-108 | external fact identifier | Section 3 row, cited as `F-n`, with its verification level | every later spec that states a provider fact |
| DEFAULT-22..DEFAULT-31, DEFAULT-59..DEFAULT-64 | provisional default identifier | Section 1, cited as `[DEFAULT-n]`; not a ruling | P2.1, P2.8, P2.10, P3.1, P3.4, P0.3, P6.1 |
| ProviderId | type | `StrEnum`, 15 members, section 8.1 | P1.1, P2.1, P3.1, P4.2, P6.1 |
| Capability | type | `StrEnum`, 12 members, section 8.1 | P2.1, P3.1, P4.1, P6.1 |
| SelectionStatus | type | `StrEnum`: `SELECTED`, `PROVISIONAL`, `BLOCKED`, `UNFILLED` | every client phase (start-up check E-12) |
| VerificationLevel | type | `StrEnum`: `PRIMARY_FULL`, `PRIMARY_EXTRACT`, `SEARCH_EXCERPT`, `SECONDARY` | X3 merge; later fact registers |
| LimitBasis | type | `StrEnum`: `DOCUMENTED`, `EMPIRICAL` | P3.1, P6.1 |
| ProviderErrorClass | type | `StrEnum`, 13 members, section 8.1; mapping in section 9 | P1.4 (audit event field), P3.1, P3.4, P6.1 |
| AdjustmentBasis | type | `StrEnum`: `RAW`, `VENDOR_ADJUSTED`, `UNSTATED` | P1.1, P2.1, P2.2 |
| BarResolution | type | `StrEnum`: `1MIN`, `1D` | P1.1, P2.1, P2.7 |
| LicensedUse, `publication_data_cleared`, `row_cleared` | type, functions | `StrEnum`: `NONE`, `PUBLICATION`; market-level and provider-level checks, section 8.1; an absent capability fails the market check | P1.3, P2.7, P6.3 |
| `throttle_matches` | function | a throttle against the `RateLimitFact` it cites | P2.1, P3.1 |
| ClientOrderRef | type | strict `str`, pattern `^[A-Z0-9]{20}$` | P1.1, P1.4, P3.1, P5.5 |
| RateLimitFact | type | frozen Pydantic v2 model, 8 fields, section 8.2 | P3.1, P6.1 |
| ClientThrottle | type | frozen Pydantic v2 model, 5 fields; client budget at most half the documented limit | P2.1, P3.1, P4.2 |
| ProviderSelection, ProviderSelectionSet | type | frozen Pydantic v2 models, 9 fields and validator in section 8.1; one row per capability and market; the rows of section 6.3 are the source, carried as config key `providers.selections` and loaded through `model_validate_json` | P0.3, P1.3, P2.1, P2.7, P3.1, P4.1, P4.2 |
| VendorSeriesSnapshot | type | frozen Pydantic v2 model, 10 fields, section 8.1; storage is P2.1's | P1.2, P2.1, P2.2, P5.x |
| AccountActivity, DormancyStatus, `dormancy_status` | type, function | frozen Pydantic v2 model, 3 fields; `OK`, `DUE`, `UNKNOWN`; a function that treats bad input as `UNKNOWN`; section 8.1 | P2.1, P6.1 |
| SEL-1..SEL-23 | selection identifier | Section 6.3 row | P0.3 and every client phase |
| THR-1..THR-14 | client throttle identifier | Section 8.3 row | P2.1, P3.1, P4.2, P6.1 |
| PE-1..PE-25 | provider error path identifier | Section 9 row: condition, class, fail-closed behaviour | P2.1, P3.1, P3.4, P2.10, P5.5 |
| `massive.base_url`, `alpaca.trading_base_url`, `alpaca.data_base_url`, `kite.base_url` | config key | `str`, an `https://` URL; changed only through HITL-5 | P1.3, P2.1, P3.1 |
| `llm.primary_model`, `llm.fallback_model` | config key | `str`; decided values `deepseek-flash`, `gpt-4o-mini-2024-07-18` (D-18) | P1.3, P4.2 |
| `stops.us_replace_after_days`, `stops.in_gtt_replace_after_days` | config key | `int`, days; decided values 60 and 300 [ASSUMPTION A-42]; valid range 1 to 89 and 1 to 364 | P1.3, P3.4 |
| `upstox.base_url`, `upstox.assets_base_url`, `fyers.data_base_url`, `fyers.public_base_url` | config key | `str`, an `https://` URL; the Fyers data host is not yet verified (OQ-74); changed only through HITL-5 | P1.3, P2.1 |
| `research.http_path_allowlist` | config key | list of `str`; the read-only paths of [DEFAULT-50]: historical, intraday, instruments, fundamentals, news, market holidays; a test enumerates them (MB-AC-2) | P1.3, P2.1, P6.4 |
| `fyers.standard_history_start` | config key | `date`, per resolution; moves yearly on a date not stated by Fyers (OQ-74) | P1.3, P2.1 |
| ResearchGateApproval, `research_gate_open` | type, function | frozen Pydantic v2 model, 4 fields; the function takes the selection row; no record or a revoked record means closed; section 8.1 | P1.3, P2.1 |
| `upstox.analytics_token_expires_on`, `upstox.analytics_token_renew_before_days` | config key | `date`; `int`, days, decided value 30 [ASSUMPTION A-81], valid range 1 to 180 | P1.3, P6.1 |
| `dormancy.alert_after_days` | config key | list of `int`, days, decided value [300, 330] [DEFAULT-64], each 1 to 364, ascending | P1.3, P6.1 |
