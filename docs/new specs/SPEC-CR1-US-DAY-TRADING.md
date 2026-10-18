---
id: SPEC-CR1-US-DAY-TRADING
version: 0.2
status: DRAFT
phase: CR-1 Compliance research (US day trading, cash-account settlement); feeds P6.3 (Adapted) and the deferred P3.2
depends_on: [SPEC-A-CONSTITUTION v0.3, MODEL-B-DECISION v0.3, ROADMAP-V1 v0.3, SPEC-P0.1-DECISIONS v0.1, SPEC-P0.2-PROVIDERS v0.1, STAGE-0-OWNER-DECISIONS v0.2]
produces: [CR1-F-1..CR1-F-12, CR1-R-1..CR1-R-14, UsDayTradingRules, BrokerDayTradingPolicy, US_DAY_TRADING_RULES]
---

# CR-1: US day-trading and cash-account rules, verified at primary sources

Date: 2026-10-18. Researcher role: compliance. Version history: 0.1 (2026-10-18) first record.
0.2 (2026-10-18) after the claude.ai cross-check: CR1-R-10 also needs a human acknowledgement;
OQ-CR1-6 added; section 13 extended. No fact or pinned value changed. Nothing here is legal advice; it records what the
primary texts say on the date read, and what the system does with that.

Inputs read for this phase: `docs/specs/SPEC-P0.2-PROVIDERS.md`, `docs/specs/STAGE-0-FREEZE.md` §6,
`docs/specs/STAGE-1-GAP-AUDIT.md` §4 and open question G-2, `tests/verify_p13_config.py`,
`docs/specs/SPEC-P1.1-DOMAIN.md` §9.4 and `config/policy.yaml` (all historical run), plus the
new-run specs in `depends_on`. Historical files are read, not edited (constitution N-2); the change
to `STAGE-0-FREEZE.md` is a proposed diff only (section 7).

## 0. Result in one paragraph

**The figure the prompt asks to verify is no longer the rule.** FINRA replaced the whole
pattern-day-trader framework of Rule 4210(f)(8)(B), including the USD 25,000 minimum equity and the
four-day-trades-in-five-business-days count, with a new intraday margin standard in Rule 4210(d)(2).
The SEC approved the change on 2026-04-14; it became effective on **2026-06-04**; members that need
more time may phase it in until **2027-10-20**. USD 25,000 is verified only as the **legacy** value.
Alpaca, the US broker named in INV-10, states it lifted the PDT rule in production on 2026-06-04. The
historical project still carries `pdt_equity_floor_usd: 25000` as a live rule input; that value is now
wrong as a description of current regulation.

## 1. Problems in the upstream material

| # | Where | Problem | Resolution |
|---|-------|---------|------------|
| CR1-P1 | The phase prompt | It assumes the PDT rule is in force and asks for its window, equity check and flag. On 2026-10-18 it is not (CR1-F-1 to CR1-F-4). | The prompt's questions are answered twice: for the rule now in force (section 4) and for the legacy rule a broker may still apply during the phase-in or as a house rule (section 5). |
| CR1-P2 | The phase prompt vs Model B | Under Model B, v1 has no broker account and sends no orders (MB-1, MB-2). PDT, intraday margin and Regulation T bind account holders and brokers, not a signal publisher. BA-1 already moves them to "any future execution phase". | This spec is research for the deferred P3.2 (issue #19) and for P6.3 (issue #33, Adapted). For v1 it produces one design rule for the model portfolio (CR1-R-13) and one disclosure duty (CR1-R-14). Nothing here enables execution (MB-AC-16). |
| CR1-P3 | The prompt's file list | `STAGE-0-FREEZE.md`, `STAGE-1-GAP-AUDIT.md`, `tests/verify_p13_config.py` and `config/policy.yaml` are historical-run files that the new run does not edit (N-2; the Owner's instruction of 2026-10-13). `STAGE-0-FREEZE.md` is also FROZEN; its own §8 requires an amendment record to change it. | The register diff is written as a patch file and shown, not applied (section 7). The new run's own register, `docs/new specs/DECISIONS.md` §3, is updated. The pinning test is new-run code under `v2/` (OWD-6). |
| CR1-P4 | Historical `SPEC-P1.1-DOMAIN.md` §9.4 and `config/policy.yaml` rule `CASH-002` | They state the USD 25,000 / 3-in-5 rule as the margin-account constraint. Since 2026-06-04 that is the legacy rule only. | Recorded as a falsified assumption (section 8). Correcting the historical files is the Owner's call (OQ-CR1-4). |
| CR1-P5 | New-run `SPEC-P0.1-DECISIONS.md` UP-4, BQ-5 and P0.2 F-3 vs historical ADR-12 | The new run's US account is a margin account run with zero borrowing ([DEFAULT-16], [DEFAULT-27]); the historical run chose a cash account. The two runs therefore need different US rules. | Section 4 covers the margin account of the new run, section 6 the cash account. |
| CR1-P6 | Prompt item 2, "the equity check before or after the fourth trade" | Under the rule in force there is no fourth trade, no count and no equity floor. | Answered for the legacy rule in section 5 (CR1-R-6) and marked not applicable to the rule in force. |
| CR1-P7 | Stage 1 gap audit G-2 and condition 16 | They ask to "verify the PDT floor 25,000 and register it". Verifying it as a live number is impossible because it was repealed. | Condition 16 is closed by this spec with the outcome "falsified as current, verified as legacy", which is what the register records. |

## 2. Evidence register

Read on 2026-10-18 with a fresh fetch (no cache). "Primary" means the rule-maker's or the official
publisher's own text. Direct requests to `sec.gov` are paused for this project (Owner decision O-16),
so the SEC's approval order is read in the Federal Register, which publishes it.

| # | Fact | Source | Level |
|---|------|--------|-------|
| CR1-F-1 | The current text of FINRA Rule 4210 carries the history line "Amended by SR-FINRA-2025-017 eff. June 4, 2026." Its paragraph (f)(8) is now headed "Special Initial and Maintenance Margin Requirements" and contains no day-trading provision; the new paragraph (d)(2) is headed "Intraday Margin". | `https://www.finra.org/rules-guidance/rulebooks/finra-rules/4210` | Primary |
| CR1-F-2 | FINRA Regulatory Notice 26-10, published 2026-04-20, states the new standards replace the day-trading margin requirements in their entirety, including the PDT day-trade count and the USD 25,000 PDT minimum equity. Effective date 2026-06-04 (45 days from the notice); members that need more time may phase in implementation over 18 months, until 2027-10-20. | `https://www.finra.org/rules-guidance/notices/26-10` | Primary |
| CR1-F-3 | The SEC approved the change on an accelerated basis: Securities Exchange Act Release No. 105226 (April 14, 2026), 91 FR 20731 (April 17, 2026), File No. SR-FINRA-2025-017. During the interim, members "may continue applying the current day trading margin requirements as appropriate (e.g., by account)". | Federal Register document 2026-07485, `https://www.federalregister.gov/d/2026-07485`; citation as given in Notice 26-10 endnote 1 | Primary (SEC order as published in the Federal Register) |
| CR1-F-4 | The legacy rule, as the SEC's notice of filing describes it: FINRA adopted "a specified minimum equity requirement of $25,000" for pattern day traders; "a customer who executes four or more day trades within five consecutive business days in a margin account is generally designated a pattern day trader". The legacy definition of day trading was the purchasing and selling, or selling and purchasing, of the same security on the same day in a margin account, subject to exceptions. | Release No. 34-104572 (January 9, 2026), 91 FR 1580 (January 14, 2026), `https://www.federalregister.gov/d/2026-00519`; the definition as restated in document 2026-07485 | Primary (SEC publication describing the repealed text) |
| CR1-F-5 | The rule in force applies to "each margin account of a customer … (other than a good faith account or portfolio margin account)" on each day with an IML-reducing transaction (4210(d)(2)(A)). IML, IML-reducing transaction and intraday margin deficit are defined in 4210(a)(17) to (a)(19). | FINRA Rule 4210 current text | Primary |
| CR1-F-6 | A deficit is satisfied by net deposits or an IML increase "from the end of such day to the end of a subsequent day" (4210(d)(2)(C)(ii)); it remains outstanding until satisfied or until immediately after the close of business on the 15th business day after it arose (4210(d)(2)(C)(iii)). | FINRA Rule 4210 current text | Primary |
| CR1-F-7 | 90-day freeze (4210(d)(2)(D)): if a customer makes a practice of failing to satisfy deficits promptly and fails to satisfy one by close of business on the fifth business day, the member restricts new short positions and debit balances for 90 calendar days after that fifth business day, or until the deficit is satisfied. Deficits not exceeding the lesser of 5% of the account's equity or USD 1,000, or arising in extraordinary circumstances, do not count toward "a practice". | FINRA Rule 4210 current text | Primary |
| CR1-F-8 | Unchanged by the amendment: initial margin requires equity of at least USD 2,000 (4210(b)(4)); maintenance margin is 25% of the current market value of margin securities held long (4210(c)(1)); firms may set their own higher house requirements (4210(d)(1)). | FINRA Rule 4210 current text | Primary |
| CR1-F-9 | US standard settlement: a broker-dealer may not contract for settlement later than "the first business day after the date of the contract" (T+1), with stated exceptions. | 17 CFR 240.15c6-1(a), eCFR, up to date as of 2026-10-15 | Primary |
| CR1-F-10 | Regulation T: "Payment period means the number of business days in the standard securities settlement cycle … plus two business days" (12 CFR 220.2). Cash account: a creditor buys for a customer if there are sufficient funds, or on the customer's good-faith agreement to pay in full before selling (220.8(a)(1)); unpaid purchases are cancelled or liquidated after the payment period, and a creditor may disregard a sum due not exceeding USD 1,000 (220.8(b)(4)); a security sold before it was paid for in full withdraws the privilege of delayed payment for 90 calendar days (220.8(c)). No change after 2017-01-03. | 12 CFR 220.2 and 220.8, eCFR, up to date as of 2026-10-15 | Primary |
| CR1-F-11 | "Good faith violation" is not a term of Regulation T. FINRA's investor guidance describes it as buying with proceeds that have not settled and then selling the security before those proceeds settle. Broker policies on counting such violations are the broker's. | `https://www.finra.org/investors/insights/frequent-intraday-trading` (FINRA investor guidance, not a rule) | Primary for the description; not a rule |
| CR1-F-12 | Alpaca: "We have officially lifted the Pattern Day Trader rule and replaced it with the new intraday margin framework in production for both Trading API users and Broker API partners" (page last updated 2026-06-04). | `https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/` | Vendor primary |

Not found: Alpaca's own published policy on good-faith violations in cash accounts (searched
`docs.alpaca.markets`; no page returned). It stays OQ-CR1-2. The SEC's investor.gov pages were not
read; the SEC's position is taken from its approval order (CR1-F-3).

## 3. Blocking questions and the defaults used

Numbering continues from `SCOPE-MULTI-USER.md` (BQ-43, [DEFAULT-54]).

| # | Question | Options | Default used | If the default is wrong |
|---|----------|---------|--------------|-------------------------|
| BQ-44 | Does a future execution path still implement the legacy PDT check? | (a) no, the rule is repealed; (b) yes, always; (c) per broker: on unless that broker's own published policy says it no longer applies the legacy rule | [DEFAULT-55] (c). A `BrokerDayTradingPolicy` record per broker says whether the legacy PDT rule (or a house rule like it) is enforced, with its source and check date. A broker with no verified record is treated as enforcing it. Alpaca's record is `false` (CR1-F-12). | Under (a), an account at a broker still on the phase-in or with a house rule is flagged and restricted for 90 days; under (b), a broker that has moved on is treated as if it had not, which only costs trades. |
| BQ-45 | Which equity figure and timestamp does a legacy check use? | (a) live equity at order time; (b) equity at the previous session's close; (c) the lower of the two | [DEFAULT-56] (c). | Under (a) or (b) alone, an intraday loss or a stale close can let the fourth day trade through. |
| BQ-46 | How are day trades counted when fills are partial or split, given FINRA has deleted its interpretations of the legacy rule (Notice 26-10, endnote 2)? | (a) per order pair; (b) per fill, conservatively; (c) per instrument per session | [DEFAULT-57] (b): every sell fill that reduces shares bought earlier in the same session counts as one day trade. A buy fill followed by three partial sell fills is three. This over-counts compared with most broker conventions, which is the fail-closed direction (INV-6). | Over-counting blocks trades the broker would allow; it can never cause a flag. |
| BQ-47 | Does the model portfolio fund an `ENTER` with proceeds of an `EXIT` that has not settled? | (a) yes, at the exit price; (b) no, only from model cash settled by the entry session | [DEFAULT-58] (b), in both markets (INV-10). With US T+1 (CR1-F-9), proceeds of an `EXIT` filled at the open of session S fund `ENTER` signals from session S+1. | Under (a), a follower who mirrors the model in a cash account buys with unsettled funds, and if the new position's stop is hit before those funds settle, sells it in exactly the way CR1-F-11 calls a good faith violation. |

## 4. The rule in force: intraday margin (FINRA Rule 4210(d)(2), effective 2026-06-04)

This binds the **broker**. It affects the system only through any future execution phase, on the
new run's US margin account ([DEFAULT-16]: zero borrowing).

| # | Rule | Edge case | Resolution |
|---|------|-----------|------------|
| CR1-R-1 | There is no day-trade count, no "pattern day trader" designation and no USD 25,000 floor under FINRA rules from 2026-06-04 (CR1-F-1, CR1-F-2). | A broker still on the phase-in, or with a house rule (CR1-F-8, 4210(d)(1)). | Section 5 applies to that broker, per [DEFAULT-55]. |
| CR1-R-2 | What triggers the rule: an IML-reducing transaction in a margin account (a purchase other than to cover a short, a short sale, a withdrawal) (CR1-F-5). | A long purchase paid entirely from the account's own cash, with zero borrowing. | ASSUMPTION CR1-A-1: it reduces the IML by the position's maintenance requirement but cannot make the IML negative while the account holds no debit balance, so no deficit arises. This is reasoning from the definitions in 4210(a)(17) to (a)(19), not a FINRA interpretation. |
| CR1-R-3 | The system's pre-trade guard for any future execution: no order may be sent that the broker's own reported buying power for the account does not cover, and buys are limited by the lower of broker cash and our own settled-cash ledger ([DEFAULT-27], AMD-4). | The broker reports more buying power than settled cash because the account is a margin account. | The lower figure binds; no buying-power figure may raise it (AMD-4). |
| CR1-R-4 | How a deficit clears: net deposits or an IML increase from the end of that day to the end of a later day; it lapses after the close of business on the 15th business day (CR1-F-6). | The deficit lapses unsatisfied. | It still counts toward the 90-day freeze test of CR1-R-5 until satisfied (4210(d)(2)(D), "without regard to its expiration"). |
| CR1-R-5 | The freeze: practice of not satisfying deficits and one unsatisfied by close of business on the fifth business day: no new short or debit balance for 90 calendar days after that day, or until satisfied (CR1-F-7). | A deficit at or below the lesser of 5% of equity and USD 1,000. | It does not count toward "a practice" (CR1-F-7); the system still treats any deficit as an incident, because the design target is zero deficits (CR1-R-2). |

Window and timezone: "business day" and "close of business" are the US market's. The system takes
business days from the NYSE calendar and dates in `America/New_York` (ND-1 of `MODEL-B-DECISION.md`).

## 5. The legacy rule: only where a broker still applies it ([DEFAULT-55])

Values are verified as the legacy values (CR1-F-4); they are not current FINRA requirements.

| # | Rule | Edge case | Resolution |
|---|------|-----------|------------|
| CR1-R-6 | Equity check: before sending any opening buy, if the account's day-trade count in the window is 3 or more, the buy is denied unless account equity is at least USD 25,000. Equity is the lower of live equity and the previous close's equity ([DEFAULT-56]). The check is before the trade that would be the fourth, never after. | Equity is exactly USD 25,000.00. | Allowed: the legacy floor is a minimum ("at least"). |
| CR1-R-7 | What counts as a day trade: per [DEFAULT-57], each sell fill that reduces shares bought earlier in the same session. | Shares held overnight and sold today, plus shares bought today and sold today, in one sell fill. | Counts as one day trade; any sell fill that touches same-day shares counts. |
| CR1-R-7 | (same) | A buy order filled in several partial fills, then one sell. | One day trade: one sell fill. |
| CR1-R-7 | (same) | One buy, then a sell order filled in three partial fills. | Three day trades ([DEFAULT-57]); the over-count is deliberate. |
| CR1-R-7 | (same) | Extended-hours fills. | They belong to the session date of the trading day they occur on, in `America/New_York`. |
| CR1-R-8 | Window: the current session and the four previous NYSE business days (five business days, rolling). | A market holiday. | Not a business day; the window reaches back further in calendar days. |
| CR1-R-8 | (same) | An early-close day. | A full business day. |
| CR1-R-9 | Kill-switch liquidation is exempt from the count (historical ADR-13 Chain D, carried as the design rule). | The liquidation makes the account a pattern day trader at the broker. | Accepted and alerted: a 90-day restriction is recoverable, an unmanaged loss is not. |
| CR1-R-10 | When the broker flags or restricts the account: no opening buy is sent until the broker's account status no longer shows the flag **and** a human has acknowledged the clearance (as INV-7 does for the kill switch); exits and stops continue. How a broker removes a flag is that broker's policy and is read from its status field, never assumed. | The broker's status cannot be read. | Treated as flagged (INV-6). |

## 6. Cash accounts: Regulation T (12 CFR 220.8) and good-faith violations

This answers the question part of historical Q-P1.1-1 (Stage 1 gap audit condition 3). The intraday
margin rule does not apply to cash accounts (it applies to margin accounts, CR1-F-5); neither did the
legacy PDT rule (CR1-F-4, "in a margin account").

| # | Rule | Edge case | Resolution |
|---|------|-----------|------------|
| CR1-R-11 | Settlement is T+1 (CR1-F-9); the Regulation T payment period is T+1 plus two business days, three business days in all (CR1-F-10). | A trade on the business day before a market holiday. | Settlement and payment periods count business days only; the holiday is skipped. |
| CR1-R-12 | Buys are funded from settled cash only (historical CASH-001; new-run AMD-4). A position bought with settled cash may be sold at any time, including the same session. | A sale of shares bought with proceeds that have not settled, before those proceeds settle. | Cannot happen under CR1-R-12, because unsettled proceeds never fund a buy. If it happened, it is the CR1-F-11 good faith violation, and a sale before payment in full brings Regulation T's 90-day freeze (220.8(c)). The broker's own counting of good faith violations is OQ-CR1-2. |
| CR1-R-12 | (same) | The broker disregards a shortfall of up to USD 1,000 (220.8(b)(4)). | The system never relies on it: the disregard is the broker's option, not a customer right. |

## 6a. What this means for v1 under Model B

| # | Rule | Edge case | Resolution |
|---|------|-----------|------------|
| CR1-R-13 | The model portfolio funds `ENTER` signals only from model cash settled by the entry session ([DEFAULT-58]), in both markets. India's settlement cycle is not researched here; the same rule is used there because it can only make the model more conservative. | An `EXIT` and an `ENTER` in the same batch. | The `ENTER` is funded only if settled model cash covers it without the `EXIT` proceeds; otherwise it waits until those proceeds settle, or is not published. |
| CR1-R-14 | Disclosure duty for P6.3 and PB.1: US signals carry a statement that the follower's own broker, account type and house rules govern day trading and settlement, and that a sale of a position bought with unsettled funds may be a good faith violation at their broker. The wording is counsel's (MB-AC-11). | A follower uses a margin account. | The disclosure names the intraday margin rule as the broker's (CR1-R-1); the system gives no account-specific advice (MB-10). |

## 7. Register: proposed diff to the historical `STAGE-0-FREEZE.md` (not applied)

`docs/specs/STAGE-0-FREEZE.md` is a frozen historical-run file. Per N-2 and the Owner's instruction
of 2026-10-13 it is not edited by the new run, and its own §8 makes any change a §9 change-log entry.
The diff below adds the item to §6, under a new §6.5, and logs it in §9 as a T3 trigger ("a verified
external fact changes"). It is saved as
`docs/new specs/reviews/CR1-STAGE-0-FREEZE-register.patch` and is applied only on the Owner's yes
(OQ-CR1-4). `git apply --check` on that file passes against the working tree as of 2026-10-18.

```diff
--- a/docs/specs/STAGE-0-FREEZE.md
+++ b/docs/specs/STAGE-0-FREEZE.md
@@ -192,6 +192,13 @@ unpublished → M-8.
 | **Q14** | Tokens per thesis | 6,000 in / 1,500 out | P4.3, first 50 live gate calls |
 | **Q15** | Audit-event rate and row width | 15,000/session, ~1 KB | P1.2 / P6.1, after 20 live sessions |
 
+### 6.5 VERIFIED AFTER THE FREEZE — external fact changed (T3)
+
+| # | Item | Verified answer, with source | Decision effect |
+|---|---|---|---|
+| **G-2 / condition 16** | PDT equity floor USD 25,000 (`config/policy.yaml` `account.pdt_equity_floor_usd`, rule `CASH-002`, SPEC-P1.1 §9.4) | **Repealed** `[V]`. FINRA replaced the day-trading margin provisions of Rule 4210(f)(8)(B), including the USD 25,000 minimum and the 4-in-5 count, with intraday margin standards in 4210(d)(2). SEC Release 34-105226 (2026-04-14), 91 FR 20731 (2026-04-17); FINRA Regulatory Notice 26-10: effective **2026-06-04**, phase-in to **2027-10-20**. USD 25,000 is verified as the **legacy** value only. Alpaca lifted PDT in production on 2026-06-04. `finra.org/rules-guidance/notices/26-10`; `federalregister.gov/d/2026-07485` | **ADR-12 UNCHANGED** (cash account; neither rule applies to it). `CASH-002` describes a repealed rule and stays monitor-only; its correction needs an Owner-approved amendment. Full record: new-run `SPEC-CR1-US-DAY-TRADING` |
+| **Q-P1.1-1 (question part) / condition 3** | US settlement cycle; good-faith violations | **T+1** `[V]` (17 CFR 240.15c6-1(a)); Regulation T payment period = settlement cycle + 2 business days (12 CFR 220.2); 90-day freeze for a sale before payment in full (12 CFR 220.8(c)). "Good faith violation" is broker usage described in FINRA investor guidance, not a Regulation T term | Settled-cash sizing (`CASH-001`) UNCHANGED and confirmed. Condition 3's test of `settlement_date_for` remains OPEN |
+
 ---
 
 ## 7. Conditions that permit re-opening a frozen decision
@@ -237,6 +244,7 @@ A re-opening that does not produce a §9 entry has not happened. That is the who
 | 2026-08-26 | SPEC-P0.3-BUDGET | v0.4 → **v0.5** | **T3** — rule N16 | Phase author (§8, changes no decision) | News storage line carries a revision factor; quantified as immaterial (news is 1.3% of compressed storage). **No VM, latency, LLM or sensitivity figure changed** |
 | 2026-08-26 | SPEC-P0.2-PROVIDERS | v0.3 → **v0.4** | Defect in the 2026-08-25 freeze: three sites still asserted the pre-AD-5 LLM ordering | Phase author (§8, changes no decision) | §3.11/§3.12 headings and DECISIONS row 7 aligned with AD-5; **M-11** added for OpenAI auth/legal. **No fact, price, limit or decision changed** |
 | 2026-08-25 | SPEC-P0.3-BUDGET | v0.3 → **v0.4** | AD-2, AD-5 | Owner | LLM cost model recomputed on the new primary; RULE-B8 made provider-conditional; Q-9 closed by AD-2. **No storage, latency or VM figure changed**; **FROZEN** |
+| 2026-10-18 | STAGE-0-FREEZE | §6 register | **T3** — verified external fact changed (FINRA Rule 4210 amendment, eff. 2026-06-04) | Phase author (§8, changes no decision) | §6.5 added: PDT floor repealed (G-2, condition 16 closed); settlement T+1 and Regulation T cash-account rules verified (condition 3, question part). **No ADR or AD changed** |
 
 ---
 
```

## 8. New-run register entries (applied)

`docs/new specs/DECISIONS.md` gains, in §2, [DEFAULT-55] to [DEFAULT-58], and in §3 (assumptions
verified or falsified) two rows: the USD 25,000 PDT floor, **falsified as current and verified as
legacy**, and US T+1 settlement with the Regulation T payment period, **verified**.

## 9. Pinning test

`v2/tests/compliance/verify_cr1_us_day_trading.py` follows the pattern of the historical
`tests/verify_p13_config.py`: `require()` instead of `assert` (so `python -O` cannot strip checks),
`check()` collecting PASS and FAIL, every `t_` function run in sorted order, and exit code 1 on any
failure. It loads the Python block of section 10 from this file and fails if:

- any pinned value of `US_DAY_TRADING_RULES` differs from the value written in the test;
- the model accepts any other value for a pinned field;
- a current PDT minimum equity or day-trade limit is anything but `None`;
- the historical `config/policy.yaml` changes its `pdt_equity_floor_usd` line without this spec's
  record of the divergence (section 7) changing with it, so that line cannot drift silently in
  either direction.

Run: `py -3.13 v2/tests/compliance/verify_cr1_us_day_trading.py` once Pydantic is installed for
3.13. On this machine on 2026-10-18 only the 3.11 interpreter had Pydantic, and the run was made
with it (OWD-8 edge case).

## 10. Typed form

```python
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StrictBool, field_validator

_PINNED_DATES = {
    "sec_approval_date": date(2026, 4, 14),
    "federal_register_date": date(2026, 4, 17),
    "finra_notice_date": date(2026, 4, 20),
    "effective_date": date(2026, 6, 4),
    "phase_in_end_date": date(2027, 10, 20),
}


class UsDayTradingRules(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    finra_rule: Literal["FINRA Rule 4210"] = "FINRA Rule 4210"
    amending_filing: Literal["SR-FINRA-2025-017"] = "SR-FINRA-2025-017"
    sec_release: Literal["34-105226"] = "34-105226"
    federal_register_cite: Literal["91 FR 20731"] = "91 FR 20731"
    finra_notice: Literal["Regulatory Notice 26-10"] = "Regulatory Notice 26-10"
    sec_approval_date: date = _PINNED_DATES["sec_approval_date"]
    federal_register_date: date = _PINNED_DATES["federal_register_date"]
    finra_notice_date: date = _PINNED_DATES["finra_notice_date"]
    effective_date: date = _PINNED_DATES["effective_date"]
    phase_in_end_date: date = _PINNED_DATES["phase_in_end_date"]

    current_pdt_minimum_equity_usd: None = None
    current_day_trade_count_limit: None = None

    legacy_pdt_minimum_equity_usd: Literal[25000] = 25000
    legacy_pattern_day_trades: Literal[4] = 4
    legacy_window_business_days: Literal[5] = 5

    intraday_deficit_expiry_business_days: Literal[15] = 15
    intraday_freeze_trigger_business_days: Literal[5] = 5
    intraday_freeze_calendar_days: Literal[90] = 90
    intraday_practice_exclusion_fraction: Decimal = Decimal("0.05")
    intraday_practice_exclusion_usd: Literal[1000] = 1000
    margin_initial_minimum_equity_usd: Literal[2000] = 2000
    margin_maintenance_long_fraction: Decimal = Decimal("0.25")

    us_settlement_business_days: Literal[1] = 1
    regt_payment_period_extra_business_days: Literal[2] = 2
    regt_cash_freeze_calendar_days: Literal[90] = 90
    regt_disregard_usd: Literal[1000] = 1000

    business_day_calendar: Literal["NYSE"] = "NYSE"
    business_day_timezone: Literal["America/New_York"] = "America/New_York"

    @field_validator(*_PINNED_DATES)
    @classmethod
    def _date_is_pinned(cls, value: date, info) -> date:
        if value != _PINNED_DATES[info.field_name]:
            raise ValueError(f"{info.field_name} is pinned to {_PINNED_DATES[info.field_name]}")
        return value

    @field_validator("intraday_practice_exclusion_fraction", "margin_maintenance_long_fraction")
    @classmethod
    def _fraction_is_pinned(cls, value: Decimal, info) -> Decimal:
        pinned = {"intraday_practice_exclusion_fraction": Decimal("0.05"),
                  "margin_maintenance_long_fraction": Decimal("0.25")}[info.field_name]
        if value != pinned:
            raise ValueError(f"{info.field_name} is pinned to {pinned}")
        return value


class BrokerDayTradingPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    broker_id: Literal["alpaca"]
    legacy_pdt_enforced: StrictBool
    source_url: HttpUrl
    checked_on: date
    note: str = Field(max_length=300)


US_DAY_TRADING_RULES = UsDayTradingRules()

ALPACA_DAY_TRADING_POLICY = BrokerDayTradingPolicy(
    broker_id="alpaca",
    legacy_pdt_enforced=False,
    source_url="https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/",
    checked_on=date(2026, 10, 18),
    note="Vendor states PDT lifted in production for Trading API and Broker API on 2026-06-04",
)
```

### 10.1 Fields

| Field | Type | Unit | Timezone | Nullable | Valid range | Violation means |
|-------|------|------|----------|----------|-------------|-----------------|
| `finra_rule`, `amending_filing`, `sec_release`, `federal_register_cite`, `finra_notice` | `str` | none | n/a | no | Exactly the literal shown (CR1-F-1 to CR1-F-3) | Model rejects; test fails |
| `sec_approval_date`, `federal_register_date`, `finra_notice_date`, `effective_date`, `phase_in_end_date` | `date` | calendar date | as published (US) | no | Exactly the pinned date | Model rejects; test fails |
| `current_pdt_minimum_equity_usd`, `current_day_trade_count_limit` | `None` | USD; count | n/a | always null | Only `None`: no current FINRA value exists (CR1-R-1) | Model rejects any number; test fails |
| `legacy_pdt_minimum_equity_usd` | `int` | USD, whole dollars | n/a | no | 25000 only (CR1-F-4) | Model rejects; test fails |
| `legacy_pattern_day_trades` | `int` | day trades | n/a | no | 4 only | As above |
| `legacy_window_business_days` | `int` | business days | `America/New_York` | no | 5 only | As above |
| `intraday_deficit_expiry_business_days` | `int` | business days | `America/New_York` | no | 15 only (CR1-F-6) | As above |
| `intraday_freeze_trigger_business_days` | `int` | business days | `America/New_York` | no | 5 only (CR1-F-7) | As above |
| `intraday_freeze_calendar_days`, `regt_cash_freeze_calendar_days` | `int` | calendar days | `America/New_York` | no | 90 only (CR1-F-7, CR1-F-10) | As above |
| `intraday_practice_exclusion_fraction` | `Decimal` | fraction of account equity | n/a | no | 0.05 only | As above |
| `intraday_practice_exclusion_usd`, `regt_disregard_usd` | `int` | USD | n/a | no | 1000 only | As above |
| `margin_initial_minimum_equity_usd` | `int` | USD | n/a | no | 2000 only (CR1-F-8) | As above |
| `margin_maintenance_long_fraction` | `Decimal` | fraction of current market value | n/a | no | 0.25 only (CR1-F-8) | As above |
| `us_settlement_business_days` | `int` | business days after trade date | `America/New_York` | no | 1 only (CR1-F-9) | As above |
| `regt_payment_period_extra_business_days` | `int` | business days | `America/New_York` | no | 2 only (CR1-F-10) | As above |
| `business_day_calendar`, `business_day_timezone` | `str` | none | n/a | no | `NYSE`, `America/New_York` | As above |
| `BrokerDayTradingPolicy.broker_id` | `str` | none | n/a | no | `alpaca` only in this version; another broker needs a new version with its own source | Model rejects |
| `BrokerDayTradingPolicy.legacy_pdt_enforced` | `bool` (strict) | none | n/a | no | `true` or `false`; a broker with no record is treated as `true` ([DEFAULT-55]) | Model rejects non-bool |
| `BrokerDayTradingPolicy.source_url` | URL | none | n/a | no | The broker's own published page | Model rejects |
| `BrokerDayTradingPolicy.checked_on` | `date` | calendar date | `Asia/Kolkata` (date of the check) | no | Not later than the load date | Rejected by the loader of the future execution phase |
| `BrokerDayTradingPolicy.note` | `str` | none | n/a | no | 0 to 300 characters | Model rejects |

### 10.2 Error paths

| # | Condition | Fail-closed behaviour |
|---|-----------|-----------------------|
| CR1-E1 | The spec block cannot be loaded or a pinned value differs | The pinning test fails; CI fails (P6.4) |
| CR1-E2 | A future execution phase has no `BrokerDayTradingPolicy` for its broker | Legacy PDT check applies ([DEFAULT-55]) |
| CR1-E3 | The broker's account status (flag, buying power) cannot be read | No opening buy is sent (CR1-R-10, INV-6) |
| CR1-E4 | Settled-cash ledger and broker cash disagree | The lower figure binds (CR1-R-3) |
| CR1-E5 | The NYSE calendar for a date is missing | No window, settlement or payment date is computed for it; the dependent action is denied |

## 11. Non-blocking details resolved

| # | Detail | Resolution |
|---|--------|------------|
| CR1-ND-1 | Money unit | Whole US dollars as `int` for regulatory thresholds; account money elsewhere stays `Decimal` (ND-4 of `MODEL-B-DECISION.md`). |
| CR1-ND-2 | Inclusive bounds | "At least USD 25,000" is inclusive; "four or more" means 4 is a pattern; "does not exceed the lesser of 5% or USD 1,000" is inclusive. |
| CR1-ND-3 | Business vs calendar days | Deficit expiry and freeze trigger are business days; both 90-day freezes are calendar days, as the texts say. |
| CR1-ND-4 | Day boundary | The trading day of the US market in `America/New_York`; extended-hours fills belong to that day. |
| CR1-ND-5 | Which day counts as "after" | "The fifth business day after it occurs": the day of the deficit is day 0. |

## 12. Which of #19 and #33 this unblocks

The numbers are GitHub issues in `janvisarode35-lang/AI-Trading-Agent`, read on 2026-10-18.

| Issue | What it is | Its PDT dependency | Unblocked? |
|-------|-----------|--------------------|------------|
| #19 | P3.2 Execution Engine (depends on #16, #17, #18) | Needed a verified day-trading rule for pre-send validation | **No.** The PDT input is settled (sections 4 and 5, [DEFAULT-55]), but #19 is still blocked by #16 to #18 and is **Deferred** in v1 under Model B (`ROADMAP-V1.md` RM-MAP, MB-8). |
| #33 | P6.3 Compliance (depends on #1, #19, #21) | Its US section asks how day trades are counted and for "the equity check before the fourth" | **Partly.** Its PDT item is answered: no count and no floor under the rule in force; the legacy check only per broker; the cash-account controls and the disclosure duty CR1-R-14. #33 as a whole stays blocked by #1, #19 and #21; under Model B its scope is Adapted (`ROADMAP-V1.md`). |

Historical Stage 1 gap-audit conditions: **condition 16 is closed** (falsified as current, verified
as legacy). **Condition 3 is half answered**: the question part (T+1, good-faith violations) is
answered in section 6, and its test of `settlement_date_for` remains open.

## 13. Cross-check against DeepSeek

The same prompt was run in DeepSeek on 2026-10-18 (raw answer:
`paste-ready/outputs/CR1-DEEPSEEK-raw.txt`; comparison:
`docs/new specs/reviews/CR1-DEEPSEEK-COMPARISON.md`). It reached the same central finding. It did
not fetch primary sources, and its register diff dates the phase-in end as 2026-10-20 instead of
2027-10-20. One point it raised is added here as OQ-CR1-5: the legacy definition's condition that
day trades exceed 6% of the account's trades in the window, which it attributes to investor.gov and
which was not verified for this spec. [DEFAULT-57] ignores that condition, which can only over-count.

The same prompt was also run in a new claude.ai chat (Opus 5.5) on 2026-10-18 (files:
`paste-ready/outputs/claude-chat/CR1/`; comparison:
`docs/new specs/reviews/CR1-CLAUDE-CHAT-COMPARISON.md`). It reached the same finding with the same
SEC release. Two of its points are adopted: the human acknowledgement in CR1-R-10, and OQ-CR1-6 on
the wording of INV-9. Its lint test, run against the real `config/policy.yaml`, fails on line 174
`pdt_equity_floor_usd: 25000`, which is the divergence recorded in section 7 and OQ-CR1-4.

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| CR1-D-1 | USD 25,000 is recorded as the repealed legacy value, not as a current regulatory number | CR1-F-1 to CR1-F-4 | Yes | A future execution phase mis-sizes a margin account's day-trading capacity |
| CR1-D-2 | The historical register is changed only by an Owner-approved patch (section 7) | N-2; STAGE-0-FREEZE §8 | Yes | None; the patch is ready |
| CR1-D-3 | Model-portfolio entries use settled model cash only ([DEFAULT-58]) | Keeps cash-account followers clear of good faith violations | Yes | Model portfolio slightly slower to redeploy |
| CR1-D-4 | The pinning test lives in `v2/tests/compliance/` | OWD-6: new-run code goes in `v2/` | Yes | None |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| DEFAULT-55 | Legacy PDT check per broker, on unless the broker says otherwise | BQ-44 | Each broker's published policy | Restricted account, or forgone trades |
| DEFAULT-56 | Legacy equity check uses the lower of live and previous-close equity | BQ-45 | Broker's legacy computation | Fourth day trade let through |
| DEFAULT-57 | Legacy day trades counted per sell fill | BQ-46; FINRA's interpretations deleted | Broker's counting method | Over-counting only |
| DEFAULT-58 | Model `ENTER` funded from settled model cash only, both markets | BQ-47 | P2.8 | Followers incur good faith violations |
| CR1-A-1 | A fully cash-paid long purchase in a zero-borrowing margin account cannot create an intraday margin deficit | Reasoned from 4210(a)(17) to (a)(19); no FINRA interpretation read | FINRA's interpretive guidance announced in Notice 26-10; Alpaca's intraday margin documentation | CR1-R-3 needs an IML check of its own |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| OQ-CR1-1 | FINRA's interpretive guidance for the intraday margin rule (announced as forthcoming in Notice 26-10) | FINRA | `https://www.finra.org/rules-guidance/notices/26-11`; `https://www.finra.org/4210interps` | Deferred P3.2 (#19) |
| OQ-CR1-2 | Alpaca's policy on good faith violations in cash accounts and on its own house day-trading rules | Alpaca | `docs.alpaca.markets`, search "good faith violation", "cash account", "intraday margin" | Deferred P3.2 (#19); historical condition 3 |
| OQ-CR1-3 | India: does any Indian rule or broker policy restrict same-day buy and sell in the cash segment for the follower, and what is India's settlement cycle? | NSE, SEBI, Zerodha | NSE and SEBI circulars on the settlement cycle; Zerodha support pages | P6.3 India disclosures |
| OQ-CR1-5 | Did the legacy pattern-day-trader definition also require day trades to exceed 6% of the account's total trades in the five-day window? Matters only for a broker still applying the legacy rule | SEC investor education; FINRA | investor.gov glossary entry "Pattern Day Trader"; Federal Register 91 FR 1580, section on the current requirements | Deferred P3.2 (#19), legacy mode only |
| OQ-CR1-6 | When an execution phase returns (MB-8), INV-9's words "US PDT" name a repealed rule. Replace them with the Regulation T cash-account rules and, for a margin account, FINRA Rule 4210(d)(2)? | Owner (a constitutional amendment) | Constitution INV-9; `MODEL-B-DECISION.md` BA-1; this spec section 4 | The future execution phase only |
| OQ-CR1-4 | Will the Owner apply the section 7 patch to the historical `STAGE-0-FREEZE.md`, and correct `CASH-002` and SPEC-P1.1 §9.4? | Owner | Section 7; `docs/new specs/reviews/CR1-STAGE-0-FREEZE-register.patch` | Historical run only |

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| `UsDayTradingRules` | type | Section 10 | P6.3, deferred P3.2, P2.9 |
| `US_DAY_TRADING_RULES` | constant | `UsDayTradingRules()` | Pinning test; P6.3 |
| `BrokerDayTradingPolicy` | type | Section 10 | Deferred P3.2 |
| `ALPACA_DAY_TRADING_POLICY` | constant | Section 10 | Deferred P3.2 |
| CR1-R-1..CR1-R-14 | rule identifier | Sections 4 to 6a | P2.8 (CR1-R-13), P6.3 and PB.1 (CR1-R-14), deferred P3.2 |
| `v2/tests/compliance/verify_cr1_us_day_trading.py` | test | Section 9 | P6.4 CI |
