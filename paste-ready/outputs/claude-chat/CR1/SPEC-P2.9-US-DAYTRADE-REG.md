---
id: SPEC-P2.9-US-DAYTRADE-REG
version: 0.1
status: DRAFT
phase: P2.9 — Risk engine, US regulatory controls (resolves STAGE-1-GAP-AUDIT G-2)
depends_on: [SPEC-P0.2-PROVIDERS v0.5, STAGE-0-FREEZE §6, STAGE-1-GAP-AUDIT §4 + G-2, SPEC-P1.3-CONFIG (tests/verify_p13_config.py pattern)]
produces: [regulatory.us_daytrade.FACTS, regulatory.us_daytrade.FACTS_SHA256, rule REGT-001, rule REGT-002, metric DTR-TELEMETRY, table cash_settlement_ledger, STAGE-0-FREEZE §6.5, amendment A-PDT-1]
---

# SPEC-P2.9 — US day-trading rules for a cash account

## 0. Verdict first

**The question was framed wrong.** G-2 asks whether the PDT floor of $25,000 is *verified*.
It is — and it is **dead**. As of today (2026-10-18) there is no pattern-day-trader floor to
enforce, and for this system there never was one: ADR-12 makes the US account a long-only
**cash** account, and the PDT rule only ever governed **margin** accounts.

| Claim | Confidence | Source |
|---|---|---|
| The floor was **$25,000** under Rule 4210(f)(8)(B)(iv)a. | `[V]` Certain | SEC Rel. 34-42418 (2001 approval of the NASD rule): customers "deemed to be pattern day traders shall be $25,000." FINRA Reg. Notice 21-24 Interpretation /025 cites the same paragraph |
| SEC approved **SR-FINRA-2025-017** on **2026-04-14**, replacing the day-trading margin rules, including the PDT designation and the $25,000 floor | `[V]` Certain | FINRA weekly update 2026-04-15; SEC Rel. 34-105226, 91 FR 20731 (2026-04-17) |
| **Effective 2026-06-04**; members may phase in until **2027-10-20** | `[V]` Certain | FINRA Reg. Notice 26-10 (2026-04-20) — the new standards "replace in their entirety the outdated day trading margin requirements" |
| Paragraph **(f)(8)(B) is eliminated**, with associated text in (b), (f)(10), (g)(13); interpretations /025 etc. deleted | `[V]` Certain | Reg. Notice 26-10, endnote 2 (paraphrased) |
| The replacement **intraday margin rule applies to margin accounts other than good-faith and portfolio-margin accounts** | `[V]` Certain | Reg. Notice 26-10, new Rule 4210(d)(2) |
| Alpaca implemented the change on 2026-06-04 | `[F]` Likely | Alpaca staff on `forum.alpaca.markets` thread 18701 — forum, not API reference. Not binding in code |
| What binds a cash account is **Reg T 12 CFR 220.8(c)**: selling a security not previously paid for in full means the delayed-payment privilege is "withdrawn for 90 calendar days following the date of sale" | `[V]` Certain | eCFR 12 CFR 220.8 |
| US standard settlement is **T+1**, compliance date **2024-05-28** | `[V]` Certain (secondary) | SEC Rel. 34-96930, via Davis Polk / Cahill summaries; the SEC PDF itself was not fetched this session |
| Exact FINRA historical interpretations of multi-fill day-trade counting | `[U]` Guessing | Deleted from FINRA's site by Reg. Notice 26-10; not retrieved. Only used for telemetry (§3.1) |

**Consequence:** the frozen spec's `25000 ASSUMPTION [VERIFY-P0.2]` is not "verified and kept".
It is **verified and retired**. Leaving it enforced would block trading on a rule that no
longer exists; deleting it silently would erase audit history. It is therefore registered as
a `RETIRED` fact, pinned by test, and the live control becomes REGT-001 (settled-cash-only).

**Conflict with a Constitution invariant — stated, not worked around.** Invariant 9 requires
"US PDT … handling". PDT no longer exists. Proposed amendment **A-PDT-1**: replace "US PDT" with
"US Reg T cash-account (free-riding) and, if ADR-12 ever changes, FINRA 4210(d)(2) intraday
margin". Needs Owner authority (ADR-09 row 12). Until then this spec satisfies the invariant's
intent: the PDT handling *is* the documented, tested retirement.

---

## 0.5 BLOCKING QUESTIONS — defaults applied

| # | Question | Options | Default applied | What breaks if wrong |
|---|---|---|---|---|
| 1 | Cash or margin account? | (a) cash per ADR-12; (b) margin | **(a)** `[DEFAULT-1]` | Margin makes FINRA 4210(d)(2) intraday-margin binding: deficits, 5-business-day trigger, 90-day freeze. Facts are already pinned as `NOT_APPLICABLE` so the switch is a status flip plus a new rule, not research |
| 2 | Fund entries from settled cash only, or allow unsettled proceeds and track good-faith violations? | (a) settled only; (b) unsettled + GFV budget | **(a)** `[DEFAULT-2]` | Under (a) a GFV/free-ride is structurally impossible, so broker GFV counting (M-6) stops mattering. Cost: exit proceeds idle one business day (T+1). At ≤4 entries/session that is a capacity loss, not a correctness loss |
| 3 | Assume the broker might still apply legacy PDT during its phase-in (to 2027-10-20)? | (a) build PDT logic; (b) telemetry only + react to broker restriction flags | **(b)** `[DEFAULT-3]` | PDT never applied to cash accounts, and Alpaca states (forum) it migrated on 2026-06-04. Any broker restriction, for any reason, is caught by REGT-002 |
| 4 | Does REGT DENY apply to exposure-reducing sells? (STAGE-0 A-14) | (a) sells exempt from REGT; (b) gated | **(a)** `[DEFAULT-4]` | Reg T 220.8(a)(2)(i) permits selling a security held in the account. Under REGT-001 every held share is paid for, so a sale can never free-ride. Other rules may still deny — A-14 remains the Owner's call |
| 5 | Settlement date: broker-reported or computed? | (a) broker-reported; (b) computed | **(a), fallback (b), missing → unsettled** `[DEFAULT-5]` | Settlement days follow the clearing calendar, which can differ from the NYSE trading calendar (e.g. bank holidays with markets open). A wrong date releases cash early → free-ride risk |
| 6 | Where does the frozen `25000` live? | — | Treated as "the FROZEN spec cited by STAGE-1-GAP-AUDIT §4 rank 4" `[DEFAULT-6]` | The lint in the test catches any PDT+25,000 value in `src/` or `config/`; a markdown spec is not linted. OPEN Q-3 asks for the path |

## 0.6 NON-BLOCKING details resolved

| Area | Resolution |
|---|---|
| Trading date | Exchange-local `America/New_York` date of execution. Extended-hours fills belong to that date. DST changes nothing because the key is the local date, not a UTC offset |
| Half-days (13:00 ET close) | Same trading date; T+1 unchanged |
| Settlement day | Next **settlement** business day, not next trading day (`[DEFAULT-5]`) |
| 90-day Reg T freeze counting | 220.8(c)(1): "following the date of sale" → day 1 = sale date + 1 calendar day; restriction lifts at the start of sale date + 91 (inclusive end at sale + 90) |
| Money | `Decimal`, never float. Cash 2 dp; notional unrounded until compared. Boundary is **inclusive**: proposed == available is ALLOW (tested) |
| Fees | `fee_reserve_usd` deducted before comparison; buys carry no SEC/TAF fee (sells only, per P0.2 §3.1), reserve covers rounding-up of daily aggregates |
| Partial fills | Filled part moves from `open_buy_notional` to `unsettled_buy_cost`; remaining qty × limit stays in `open_buy_notional`. Never counted twice in one bucket |
| Same-day buys | Subtracted even if the broker's settled-cash figure already nets them — double-deduct errs toward DENY |
| Unsettled sale proceeds | **Never** added to available cash (that is the free-riding path) |
| Fractional / notional | `notional` orders are market-only (P0.2) and therefore excluded by EXEC-001 for entries; entry notional = `limit_price × qty` |
| Deposits | Only broker-reported **settled** cash counts; an ACH deposit in transit is not spendable |
| Dividends | Count when broker reports them settled; never on ex-date (P0.2 §0.6 `pay_date` rule) |

---

## 1. Primary-source record

| # | Source | What it establishes | Retrieved |
|---|---|---|---|
| S1 | `sec.gov/rule-release/34-42418` | Original operative text of the $25,000 floor | 2026-10-18 |
| S2 | `finra.org/rules-guidance/notices/21-24` | Interpretation /025: PDT floor sits in 4210(f)(8)(B)(iv)a.; /024: the $2,000 margin minimum does not apply to cash accounts | 2026-10-18 |
| S3 | `finra.org/compliance-tools/weekly-archive/04152026` | SEC approval of SR-FINRA-2025-017 on 2026-04-14 | 2026-10-18 |
| S4 | `finra.org/sites/default/files/2026-04/Regulatory-Notice-26-10.pdf` | Effective 2026-06-04; phase-in to 2027-10-20; (f)(8)(B) eliminated; intraday-margin mechanics; Rel. 34-105226, 91 FR 20731 | 2026-10-18 |
| S5 | `ecfr.gov/current/title-12/.../section-220.8` | Cash account; 90-day freeze | 2026-10-18 |
| S6 | Davis Polk / Cahill summaries of SEC Rel. 34-96930 | T+1, compliance 2024-05-28 | 2026-10-18 (secondary) |
| S7 | `forum.alpaca.markets/t/.../18701` | Alpaca's own implementation date | 2026-10-18 `[F]` |

Not retrieved: the 4210 Attachment A full rule text (the Notice is FINRA's summary and states
the rule language prevails), FINRA Reg. Notice 26-11 interpretations, SEC 34-96930 PDF.

---

## 2. The implementable rules

### 2.1 REGT-001 — settled-cash-only funding (DENY)

Applies to every **position-increasing** US order, evaluated pre-trade, after all other
exposure rules, at submission time (not at signal time — cash changes overnight).

```
available = settled_cash_usd
          − open_buy_notional_usd      # all open buys, remaining qty × limit
          − unsettled_buy_cost_usd     # our ledger, filled not yet settled
          − fee_reserve_usd
ALLOW iff proposed_buy_notional_usd ≤ available
```

| Error path | Fail-closed behaviour |
|---|---|
| `settled_cash_usd` unknown / stale (> one reconciliation cycle) | DENY, reason `missing input` |
| Broker cash disagrees with ledger by > $0.01 | DENY all entries pool-wide, CRITICAL, reconcile (ADR-10 condition 2) |
| Settlement date absent on a fill and calendar lookup fails | Treat proceeds as unsettled indefinitely; DENY spending them |
| Evaluator exception | DENY (gate already maps exceptions to fail-closed, per P1.3 test `t_evaluator_exception_fails_closed`) |

Implemented as `regulatory.us_daytrade.evaluate_entry_funding`. **Overlap note:** `policy.yaml`
already contains a rule `CASH-001` (referenced by `t_kill_switch_liquidation_exemption`). Its text
was not supplied; OPEN Q-4 asks whether REGT-001 supersedes or duplicates it.

### 2.2 REGT-002 — broker restriction (DENY + CRITICAL)

Any broker-side account restriction — Reg T freeze, trading block, legacy PDT flag during a
broker's phase-in, anything — denies all **entries** pool-wide. Unknown flag state = DENY.
Exits remain governed by `[DEFAULT-4]`/A-14. **Clears** only when the broker reports the
restriction lifted **and** a human acknowledges (kill-switch pattern, invariant 7). The
broker's field names are not documented in P0.2 → OPEN Q-1; no field name is invented here.

### 2.3 What counts as a day trade — telemetry only, `DTR-TELEMETRY` (monitor mode)

No regulation in force uses this count for our account. It is kept because (1) auditors will ask,
(2) a broker could restrict on it during phase-in, (3) a move to margin needs history.

| Case | Count |
|---|---|
| Buy 100 then sell 100, same trading date, same symbol | 1 |
| One buy order filled in 3 executions, then one sell order | 1 — fills of one order collapse to that order |
| Buy, buy, sell (one sell order) | 1 |
| Buy, sell, buy, sell | 2 |
| Position opened yesterday, sold today, re-bought today | 0 for the sale; the re-buy only counts if sold again today |
| Partial sell of a same-day buy, remainder held overnight | 1 |
| Broker-initiated cancel of a stop (N13), no fill | 0 |

Rule: per (account, symbol, trading date), each **sell order** with ≥1 fill that reduces shares
bought earlier on that same trading date counts 1. `[ASSUMPTION A1]` — this matches the widely
cited historical FINRA reading, but those interpretations are deleted and were not retrieved.
Rolling window for the metric: 5 NYSE trading dates ending on the current trading date,
`America/New_York`, inclusive. Before/after the fourth trade, equity checks, flagging and clearing:
**not implemented — no rule exists to implement** (§0).

### 2.4 Good-faith / free-riding interaction (ties to Q-P1.1-1 condition 3, blocking #16)

"Good-faith violation" is a **broker** policy name; the regulation is Reg T 220.8. Under
REGT-001 every purchase is paid from settled cash before any sale, so neither a GFV nor a
free-ride can occur by construction. M-6 (how Alpaca counts GFVs) is therefore **downgraded
to informational**. I was not given the text of Q-P1.1-1 or #16, so I cannot state that their
condition 3 is met — only that if it asks "how is the GFV counter specified", the answer is
"it is held at zero by REGT-001 and REGT-002 catches the broker disagreeing".

---

## 3. Entities

```python
# src/regulatory/us_daytrade.py (delivered alongside this spec; abridged signature)
class FactStatus(StrEnum): IN_FORCE; RETIRED; NOT_APPLICABLE
class RegulatoryFact(BaseModel):          # frozen, extra=forbid
    key: str                # ^[a-z0-9_.]+$
    value: str              # canonical text
    unit: str
    status: FactStatus      # RETIRED requires effective_to
    citation: str           # >= 10 chars
    effective_from: date | None
    effective_to: date | None   # exclusive, > effective_from
class EntryFundingInput(BaseModel):       # all Decimal USD
    settled_cash_usd: Decimal | None      # None -> DENY
    open_buy_notional_usd: Decimal  (>=0)
    unsettled_buy_cost_usd: Decimal (>=0)
    fee_reserve_usd: Decimal        (>=0)
    proposed_buy_notional_usd: Decimal (>0)
    broker_restriction_active: bool | None  # None -> DENY
```

```sql
-- Source of unsettled_buy_cost_usd and of settled-cash reconciliation.
CREATE TABLE cash_settlement_ledger (
    fill_id           TEXT          PRIMARY KEY,          -- broker execution id
    account_id        TEXT          NOT NULL,
    market            TEXT          NOT NULL CHECK (market IN ('US','IN')),
    side              TEXT          NOT NULL CHECK (side IN ('BUY','SELL')),
    symbol            TEXT          NOT NULL,
    trade_date        DATE          NOT NULL,             -- exchange-local trading date
    settle_date       DATE,                               -- NULL = unknown -> treated unsettled
    settle_date_src   TEXT          NOT NULL CHECK (settle_date_src IN ('BROKER','CALENDAR','UNKNOWN')),
    qty               NUMERIC(20,9) NOT NULL CHECK (qty > 0),
    price             NUMERIC(18,6) NOT NULL CHECK (price > 0),
    gross_usd         NUMERIC(20,2) NOT NULL CHECK (gross_usd > 0),
    fees_usd          NUMERIC(20,2) NOT NULL DEFAULT 0 CHECK (fees_usd >= 0),
    recorded_at       TIMESTAMPTZ   NOT NULL,             -- UTC
    CHECK (settle_date IS NULL OR settle_date > trade_date),
    CHECK ((settle_date IS NULL) = (settle_date_src = 'UNKNOWN'))
);
-- Append-only (invariant 5): corrections are new rows keyed by a correction fill_id, never UPDATE.
```

---

## 4. Register diff — STAGE-0-FREEZE §6

```diff
--- a/docs/specs/STAGE-0-FREEZE.md
+++ b/docs/specs/STAGE-0-FREEZE.md
@@ ### 6.2 OPEN — carried, not gating
-`Q7/M-6` settlement and good-faith rules · `Q8` India tax schedule · `Q9` LRS/TCS ·
+`Q7/M-6` settlement and good-faith rules — **settlement VERIFIED T+1 (SEC 15c6-1, 2024-05-28);
+GFV counting downgraded to informational by REGT-001 (SPEC-P2.9-US-DAYTRADE-REG §2.4)** ·
+`Q8` India tax schedule · `Q9` LRS/TCS ·
@@
 `P0.3 Q-12` zero-trade bar behaviour.
+· **`PDT-Q1`** broker restriction-flag field names for REGT-002 (Alpaca) ·
+**`A-PDT-1`** amend invariant 9 "US PDT" → Reg T cash-account + 4210(d)(2) if margin (Owner)
@@ after ### 6.4
+
+### 6.5 REGULATORY VALUES — registered, primary-sourced, pinned by test
+
+Freezing a spec must not freeze an unverified regulatory number. Every regulatory value any
+frozen spec relies on is listed here, lives in `src/regulatory/`, and is pinned by
+`tests/verify_us_daytrade_reg.py` (SHA-256 over the canonical fact set). Changing one fails CI.
+
+| Key | Value | Status | Source | Pinned |
+|---|---|---|---|---|
+| `us.pdt.min_equity_usd` | 25,000 USD | **RETIRED 2026-06-04** | ex-FINRA 4210(f)(8)(B)(iv)a.; SEC Rel. 34-105226; Reg. Notice 26-10 | yes |
+| `us.pdt.day_trades_in_window` / `window_business_days` | 4 / 5 | **RETIRED 2026-06-04** | ex-4210(f)(8)(B)(ii) | yes |
+| `us.intraday_margin.*` (eff. 2026-06-04, phase-in end 2027-10-20, 5 bd trigger, 90 cd freeze, 15 bd lapse, de minimis lesser of 5% / $1,000) | — | NOT_APPLICABLE (cash acct, ADR-12) | Reg. Notice 26-10; Rule 4210(d)(2) | yes |
+| `us.regt.cash_freeze_calendar_days` | 90 | IN_FORCE | 12 CFR 220.8(c)(1) | yes |
+| `us.settlement.cycle_business_days` | 1 | IN_FORCE | SEC 15c6-1(a), Rel. 34-96930 | yes |
+
+**Closes STAGE-1-GAP-AUDIT G-2 and §4 rank 4.** The frozen `25000 [VERIFY-P0.2]` is
+superseded by the RETIRED row above under §8 (additive: records a verified external fact,
+T3); the live control is REGT-001.
```

## 5. Test

`tests/verify_us_daytrade_reg.py` — 16 checks, same runner as `verify_p13_config.py`
(`require()` survives `python -O`). Pins `FACTS_SHA256`; asserts the floor is 25,000 **and**
RETIRED from 2026-06-04; asserts intraday-margin facts stay NOT_APPLICABLE; tests REGT-001
boundaries (inclusive at the cent, open buys and same-day fills consume cash, unknown inputs
deny); and lints `src/` + `config/` for any PDT-and-25,000 value outside the facts module.
**Mutation-checked:** editing the floor to 25,001 fails two checks; restoring passes.

---

## DECISIONS MADE
| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | PDT $25,000 recorded as RETIRED, never enforced | Eliminated 2026-06-04 (S3, S4) | Yes | Low — enforcing it would only block trading |
| 2 | Live US control is REGT-001 settled-cash-only | Makes free-riding/GFV impossible by construction | Yes | Medium — one day of idle proceeds |
| 3 | Broker restriction of any kind → DENY entries, human re-enable | Covers broker PDT phase-in and Reg T freezes without knowing the reason | Yes | Low |
| 4 | Day-trade count kept as monitor-mode telemetry only | No rule uses it for us; audit + optionality | Yes | Nil |
| 5 | Intraday-margin facts pinned now as NOT_APPLICABLE | A move off ADR-12 becomes a status flip, not new research | Yes | Low |
| 6 | Regulatory values get their own register §6.5 and a hash pin | G-2 happened because no register tracked a regulatory number | No | Medium |
| 7 | Same-day buy cost always subtracted, even if broker nets it | Errs toward DENY | Yes | Low — slight under-use of cash |

## ASSUMPTIONS
| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| A1 | Day-trade counting rule in §2.3 matches historical FINRA practice | Interpretations deleted by RN 26-10 | Read RN 26-11 and archived 4210(f)(8)(B) interpretations | Telemetry miscounts; no trading impact |
| A2 | Alpaca migrated off PDT on 2026-06-04 | Forum statement `[F]` | Alpaca support ticket / account object after a test day-trade | REGT-002 catches it anyway |
| A3 | `[DEFAULT-1]`–`[DEFAULT-6]` as in §0.5 | Phase directive to proceed | Owner review | See §0.5 |
| A4 | T+1 per secondary summaries of Rel. 34-96930 | SEC PDF not fetched | Fetch `sec.gov/rules/final/2023/34-96930.pdf` | Ledger settle dates wrong; broker-reported dates mitigate |

## OPEN QUESTIONS
| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| Q-1 | Which Alpaca account fields expose settled cash and account restrictions? | Alpaca docs | `docs.alpaca.markets/us/reference/getaccount.md` — list cash, settled-cash and block/restriction fields with semantics | P3.2 (REGT-001/002 wiring) |
| Q-2 | Does Alpaca report `settle_date` per fill/activity? | Alpaca docs | Account activities reference, `FILL` activity schema | P3.3 ledger |
| Q-3 | Path and line of the frozen `25000 [VERIFY-P0.2]` | Repo | `grep -rn "25000\|25,000" docs/specs` | Closing G-2 in that file |
| Q-4 | Does existing `policy.yaml` CASH-001 duplicate REGT-001? | Repo | Read CASH-001 in `config/policy.yaml` | P2.9 merge |
| Q-5 | Text of #16, #19, #33 and Q-P1.1-1 condition 3 | Owner / tracker | Paste the items | Unblock statement below |
| Q-6 | A-PDT-1 accepted? | Owner | ADR-09 row 12 | Invariant 9 wording |

## CONTRACTS EXPORTED
| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| `regulatory.us_daytrade.FACTS` | type | `tuple[RegulatoryFact, ...]` | P2.9, P6.3 |
| `regulatory.us_daytrade.FACTS_SHA256` | config key | `str` (sha256 hex) | CI |
| `evaluate_entry_funding` | function | `(EntryFundingInput) -> (FundingVerdict, str)` | P2.9 gate, P3.2 |
| REGT-001 | rule | DENY, pre-trade, on_missing_input=DENY | policy gate |
| REGT-002 | rule | DENY entries + CRITICAL, human re-enable | policy gate, kill switch |
| DTR-TELEMETRY | metric | count per (account, symbol, trading_date), 5-date window | P6.1, P6.3 |
| `cash_settlement_ledger` | table | §3 DDL | P3.3, P2.9 |
| STAGE-0-FREEZE §6.5 | register | §4 | all phases |

## Unblock statement
G-2 named **P3.2 and P6.3** as blocked: **both are unblocked** — the regulatory number is
resolved (retired) and the live control is specified and tested. Items **#19 and #33** were
not in the inputs I was given, so I cannot honestly say which of them this unblocks; if they
are the P3.2 PDT order-gate and P6.3 regulatory-record items, both are unblocked. REGT-001's
Alpaca wiring remains gated on Q-1.
