---
id: SPEC-A-CONSTITUTION
version: 0.3
status: DRAFT
phase: BLOCK-A
depends_on: []
produces: [INV-1..INV-10, STACK-1, RISK-1..RISK-13, RULE-1..RULE-5, N-1..N-6, DEFAULT-1..DEFAULT-11, ConstitutionRef, ConstitutionRiskDefaults]
---

> **Model B notice (2026-10-14).** The Owner chose signals only for v1 (no order routing, no broker integration, no handling of user funds). This spec's text below is unchanged. Where it concerns orders, brokers or accounts it is superseded or deferred as listed in `MODEL-B-DECISION.md` section 6, and Block A items are read with the amendments BA-1 to BA-6 there. Phases are re-run per `ROADMAP-V1.md`.

# SPEC-A — Project Constitution (new run)

Date: 2026-10-13. Decision owner: Owner.

This file opens the new run of the project. It records Block A as the governing baseline,
states how the new run relates to the files already in the repository, and lists every place
where Block A conflicts with itself or cannot be implemented as written. It decides nothing
that Block A leaves to a later phase.

Version history: 0.1 (2026-10-13) Block A recorded. 0.2 (2026-10-13) Block B conformance pass:
section 5 added so that the two entities this file defines have a Pydantic v2 model, a field
table and enumerated error paths; D-5, D-6, A-4 and two contracts added. 0.3 (2026-10-13)
Block C conformance pass: section 6 (ten blocking questions with provisional defaults),
section 7 (edge case for every rule this file writes), section 8 (non-blocking details);
D-4 reworded, D-7 added, A-2 replaced by A-5 to A-14, OQ-11 and OQ-12 added.

## 1. Relationship to the existing repository

| # | Rule | Source |
|---|------|--------|
| N-1 | Every specification of the new run is written under `docs/new specs/`. | Owner instruction, 2026-10-13 |
| N-2 | Nothing under `docs/specs/`, `docs/specs/reviews/`, `DECISIONS.md`, `src/`, `migrations/`, `tests/`, `config/` or `scripts/` is edited, moved or deleted by the new run. These are the historical project. | Owner instruction, 2026-10-13 |
| N-3 | A historical file is not an input to a new-run phase. A new-run spec may not cite a historical spec as authority. Where a historical file holds a verified external fact, the new run re-verifies it and cites the external source. | Owner instruction "treat it as new", 2026-10-13 |
| N-4 | Work stays in the repository `janvisarode35-lang/AI-Trading-Agent`, branch `main`. No second repository. | Owner instruction, 2026-10-13 |
| N-5 | `docs/PROMPT-PACK.md` names deliverables as `docs/specs/SPEC-*.md`. In the new run the same file names are used under `docs/new specs/`. | N-1 applied to the pack |
| N-6 | The directory name contains a space. Every command and every CI path that touches it quotes the path. | Fact of the directory name |

## 2. The constitution

The text below is Block A exactly as the Owner supplied it on 2026-10-13. Identifiers
(INV-n, RISK-n, RULE-n) are added in section 3 so that later specs can cite single items.

```text
You are a principal engineer on an autonomous equities trading platform. You are contributing
one component to a system that will eventually move real money. Treat every output as something
that will be audited by a regulator and blamed after a loss.

PROJECT INVARIANTS — these are decided, not open for redesign. If your work conflicts with one,
stop and say so explicitly rather than quietly working around it.

1.  The risk engine is deterministic and always overrides every AI output. No exceptions.
2.  LLMs never: size positions, place/cancel/modify orders, change risk limits, set stops,
    or issue a final trade decision without a deterministic gate downstream.
3.  LLMs are GATED - invoked only for top-N candidates or statistically anomalous conditions.
4.  LLMs never receive raw external content. All news/filings/social text passes through a
    sanitizer and is presented as tagged, untrusted DATA - never as instructions.
5.  Every decision is written to an append-only, cryptographically verifiable audit trail
    before it takes effect. If the audit write fails, the action does not happen.
6.  Fail-closed everywhere. Missing data, stale data, an exception, an ambiguous state -> DENY.
    Never synthesise, impute, interpolate, or default a missing market value.
7.  Kill switch is infrastructure-level, independent of the AI path, automatic + manual,
    and requires a human to re-enable.
8.  No self-modifying code. No autonomous leverage. No "trade lost -> change the strategy".
    Strategy changes are offline, backtested, and champion/challenger validated.
9.  Compliance is built in from day one: SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013
    (unique strategy ID per order, OPS caps, kill switch, static IP, live-like testing) and
    US PDT / wash-sale / best-execution handling.
10. Two markets: US (NYSE/NASDAQ, broker Alpaca, separate market-data provider) and
    India (NSE/BSE, broker Zerodha Kite). Nothing may be US-only by accident.

FIXED STACK - do not propose alternatives unless the phase explicitly asks:
Python 3.12+, FastAPI, PostgreSQL + TimescaleDB, Redis, Pydantic v2, XGBoost/LightGBM,
scikit-learn, DeepSeek (primary LLM) + GPT-4o-mini (fallback), HashiCorp Vault,
Prometheus + Grafana, Docker on a single VM. No Kubernetes, no Airflow, no vector DB,
no orchestration framework, no new dependency that ten lines of stdlib would cover.

HARD RISK NUMBERS (defaults; configurable but never by the AI):
position <= 5% NAV | sector <= 20% NAV | gross <= 2x equity | net <= 1x equity |
daily loss <= 2% | weekly loss <= 5% | max drawdown <= 10% (trips kill switch) |
risk per trade 1% | liquidity cap 1% of ADDV | <=20 orders/min global, <=10 per strategy |
stop = entry - 2.5 * ATR(14) at entry | limit orders default, market only for emergency exit.

BEHAVIOURAL RULES:
- Never invent a fact, an API field, a rate limit, a fee, or a regulation. If you do not know,
  write it in the OPEN QUESTIONS table with the exact query needed to resolve it.
- Every number you state gets a source or is labelled ASSUMPTION.
- Prefer boring and deterministic over clever. Fewest moving parts that satisfies the spec.
- Precision over hedging. No "you might consider" - state the choice and the rationale.
- Call out anything in the upstream spec that is wrong, unimplementable, or internally
  contradictory. That is a required part of your output, not a courtesy.
```

## 3. Citable identifiers

Invariants: `INV-1` to `INV-10` are items 1 to 10 of PROJECT INVARIANTS, in order.

Stack: `STACK-1` is the FIXED STACK paragraph as a whole.

Risk numbers. Every value below has the source "Block A, HARD RISK NUMBERS". Block A calls
them defaults. None may be changed by an LLM or by any code path an LLM can reach (INV-2).

| ID | Limit as written | Value | Unit as written |
|----|------------------|-------|-----------------|
| RISK-1 | position | <= 5 | % of NAV |
| RISK-2 | sector | <= 20 | % of NAV |
| RISK-3 | gross exposure | <= 2 | multiple of equity |
| RISK-4 | net exposure | <= 1 | multiple of equity |
| RISK-5 | daily loss | <= 2 | % (base not stated) |
| RISK-6 | weekly loss | <= 5 | % (base not stated) |
| RISK-7 | max drawdown, trips kill switch | <= 10 | % (base not stated) |
| RISK-8 | risk per trade | 1 | % (base not stated) |
| RISK-9 | liquidity cap | 1 | % of ADDV (window not stated) |
| RISK-10 | order rate, global | <= 20 | orders per minute |
| RISK-11 | order rate, per strategy | <= 10 | orders per minute |
| RISK-12 | stop | entry - 2.5 * ATR(14) at entry | price |
| RISK-13 | order type | limit by default; market only for emergency exit | - |

Behavioural rules: `RULE-1` to `RULE-5` are the five bullets of BEHAVIOURAL RULES, in order.

## 4. Conflicts and unimplementable items in Block A

RULE-5 requires this section. Each item is a place where two parts of Block A cannot both
hold as written, or where a rule cannot be coded without a value Block A does not give.
None is ruled on here; each is assigned to the phase that owns it. Section 6 gives a
provisional default for the ones that fork the design.

### 4.1 Contradictions

| # | Items | The conflict | What breaks if left alone | Owning phase |
|---|-------|--------------|---------------------------|--------------|
| C-1 | INV-5, INV-6 vs INV-7, RISK-13 | INV-5 says an action does not happen if its audit write fails. INV-6 says any exception is DENY. Applied literally to a stop-loss exit, an emergency exit or a kill-switch flatten, an audit-store outage or a stale quote blocks the action that reduces risk, and the position stays open. INV-7 says the kill switch is independent. The text does not say whether DENY covers risk-reducing actions. | In a database outage during a falling market the system holds every position and cannot exit. This is the worst-case loss path. | P1.4 (audit), P2.9, P2.10. Needs an Owner ruling before P1.4. |
| C-2 | INV-8 vs RISK-3, RISK-4 | INV-8 says no autonomous leverage. RISK-3 allows gross exposure of 2x equity. Gross above 1x equity is reached only by borrowing or by short positions. Either the system may use leverage up to 2x inside a fixed limit, or RISK-3 is unreachable. | Sizing (P2.8) and the risk engine (P2.9) cannot both be written. | P0.1 ADR 12 (long-only or long/short) |
| C-3 | RISK-12 vs RISK-3, RISK-4 | The stop formula `entry - 2.5 * ATR(14)` is below entry, so it is a long-position stop. If short positions exist (the only way net <= 1x and gross <= 2x differ without margin), a short has no defined stop. | A short position with no stop, or a stop on the wrong side of entry. | P0.1 ADR 12, then P3.4 |
| C-4 | INV-7 vs STACK-1 | The kill switch must be infrastructure-level and independent of the AI path. The stack is one VM. A kill switch that runs on the same VM as the trading process dies with the VM, while orders already at the broker stay live. | VM failure leaves working orders and open positions with no kill path. | P2.10, P6.4 |
| C-5 | INV-9 vs RISK-10, RISK-11 | INV-9 requires SEBI "OPS caps" (orders per second). RISK-10 and RISK-11 are per minute. Twenty orders in one second satisfy RISK-10 and may breach a per-second threshold. The two caps need one enforcement rule. | An OPS breach on NSE/BSE while the internal limiter reports compliant. | P2.9, P6.3 |
| C-6 | "autonomous" (opening sentence) vs INV-10 | The platform is described as autonomous. The prompt pack (P0.2) states Zerodha has a daily manual login requirement. If that is true, the India path cannot start a session without a human each day. | India trading silently does not start, or someone automates a login in breach of broker terms. | P0.2 |

### 4.2 Rules that cannot be coded without a missing value

| # | Item | What is missing | Owning phase |
|---|------|-----------------|--------------|
| U-1 | RISK-1, RISK-2 vs RISK-3, RISK-4 | Two bases are used: "NAV" and "equity". Block A does not say whether they are the same number. With two markets and two currencies (INV-10) they need one definition each, a base currency and an FX source. | P0.1 ADR 15, P1.1 |
| U-2 | RISK-5, RISK-6, RISK-7, RISK-8 | The percentage base is not stated (start-of-day NAV, current NAV, peak NAV, equity). Realised or mark-to-market is not stated. The day and week boundary and its timezone are not stated, and the two markets have different session days. | P2.9 |
| U-3 | RISK-5, RISK-6 | The action on breach is not stated. Only RISK-7 names a consequence (kill switch). | P2.9, P2.10 |
| U-4 | RISK-1 | Not stated whether 5% is tested before the order, after the fill, or continuously, nor what happens when price movement pushes a held position above 5%. | P2.9 |
| U-5 | RISK-2 | No sector taxonomy is named. US and India listings use different classification schemes, and some schemes are licensed. | P0.2, P2.3 |
| U-6 | RISK-9 | ADDV window length, currency, and whether the cap applies per order or per day are not stated. | P2.8 |
| U-7 | RISK-12 | ATR bar frequency, whether prices are adjusted, and rounding to tick size are not stated. | P2.4, P3.4 |
| U-8 | RISK-10, RISK-11 | Not stated whether cancels and modifies count as orders, nor whether the window is rolling or calendar-minute. | P2.9 |
| U-9 | RISK-13 | "Emergency exit" is not defined. | P3.4 |
| U-10 | INV-3 | N and the definition of "statistically anomalous" are not given. | P4.2 |
| U-11 | INV-5 | The verification scheme (hash chain, signature, external anchor) and what "before it takes effect" means for an event the system only observes, such as a broker fill, are not given. | P1.4 |
| U-12 | INV-9 | "Unique strategy ID per order": Block A does not say who issues the identifier. Not asserted here; see OQ-1. | P6.3 |

### 4.3 Conflicts between Block A and the repository state

| # | Fact | Conflict | Decision needed from |
|---|------|----------|----------------------|
| R-1 | `src/`, `migrations/`, `tests/`, `config/policy.yaml` hold code written against the historical specs. | The Owner asked for the new phases to be implemented. New code under the same paths overwrites historical files, which N-2 forbids. A location for new-run code is not decided. | Owner, before the first code phase |
| R-2 | The working tree has uncommitted historical changes: `DECISIONS.md` and `docs/specs/STAGE-1-FREEZE.md` modified, `docs/specs/SPEC-P2.6-REGIME.md` untracked (git status, 2026-10-13). | They are not part of the new run. Left untouched. Any commit of the new run stages only paths under `docs/new specs/`. | Owner: commit, stash or discard them |
| R-3 | `docs/PROMPT-PACK.md` says to keep `DECISIONS.md` at the repository root. The root file is the historical index. | The new run needs its own decision log. [DEFAULT-1] It is `docs/new specs/DECISIONS.md`, created by P0.1. | Owner may overrule |
| R-4 | STACK-1 requires Python 3.12+. This machine has 3.14.7, 3.13 and 3.11 installed and no 3.12 (`py -0`, 2026-10-13). | 3.13 and 3.14 satisfy "3.12+". The pack's X1 template says "Python 3.12". The interpreter version for code and CI is not pinned. | P6.4; pinned earlier if a code phase starts first |
| R-5 | The pack's working rule is one fresh conversation per phase. | The Owner's instruction covers creating and implementing "the new phase" in this repository; which phase follows Block A is not stated. Per the pack, P0.1 is first. | Owner |

## 5. Typed form of the entities this file defines

This file defines two entities: a citation identifier and the set of risk defaults. Rules
(INV, RULE, STACK, N) are text and are cited by identifier; they are not data types.

### 5.1 Model

```python
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ConstitutionRef = Annotated[
    str,
    StringConstraints(
        strict=True,
        pattern=r"^(INV-(10|[1-9])|RISK-(1[0-3]|[1-9])|RULE-[1-5]|STACK-1|N-[1-6])$",
    ),
]


def _fixed(value: str) -> Decimal:
    return Field(default=Decimal(value), ge=Decimal(value), le=Decimal(value))


class ConstitutionRiskDefaults(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    position_max_pct_nav: Decimal = _fixed("5")
    sector_max_pct_nav: Decimal = _fixed("20")
    gross_max_multiple_of_equity: Decimal = _fixed("2")
    net_max_multiple_of_equity: Decimal = _fixed("1")
    daily_loss_max_pct: Decimal = _fixed("2")
    weekly_loss_max_pct: Decimal = _fixed("5")
    max_drawdown_pct: Decimal = _fixed("10")
    risk_per_trade_pct: Decimal = _fixed("1")
    liquidity_cap_pct_addv: Decimal = _fixed("1")
    orders_per_minute_global_max: Literal[20] = 20
    orders_per_minute_per_strategy_max: Literal[10] = 10
    stop_atr_multiple: Decimal = _fixed("2.5")
    stop_atr_period_bars: Literal[14] = 14
    default_order_type: Literal["limit"] = "limit"
    emergency_exit_order_type: Literal["market"] = "market"
```

`ConstitutionRiskDefaults` is the record of what Block A says, not the runtime policy. The
configurable policy and its permitted ranges belong to P1.3. The contract on P1.3 is: the
default value of each corresponding policy key equals the field here, and a test in the P1.3
code drop asserts it.

### 5.2 Fields

No field carries a time, so timezone is "none" for every row. No field is nullable. Every
valid range is the single Block A value, because this model records a constant; a different
value means the record no longer matches Block A. All bounds written "<=" in Block A are
inclusive: a measured value equal to the limit passes.

`ConstitutionRef`: type `str`; unit none; timezone none; not nullable; valid values are
exactly `INV-1` to `INV-10`, `RISK-1` to `RISK-13`, `RULE-1` to `RULE-5`, `STACK-1`, `N-1` to
`N-6`, upper case, no surrounding whitespace. A violation means a spec or a code comment cites
a constitution item that does not exist; the citation is rejected.

| Field | Type | Unit | Nullable | Valid range | Source | Not stated by Block A | A violation means |
|-------|------|------|----------|-------------|--------|-----------------------|-------------------|
| position_max_pct_nav | Decimal | percent of NAV (5 means 5%) | no | exactly 5 | RISK-1 | measurement time and price (U-4); NAV definition (U-1) | record does not match Block A; E-1 |
| sector_max_pct_nav | Decimal | percent of NAV | no | exactly 20 | RISK-2 | sector taxonomy (U-5); NAV definition (U-1) | E-1 |
| gross_max_multiple_of_equity | Decimal | multiple of equity (2 means 2.0x) | no | exactly 2 | RISK-3 | equity definition (U-1); reachability (C-2) | E-1 |
| net_max_multiple_of_equity | Decimal | multiple of equity | no | exactly 1 | RISK-4 | equity definition (U-1) | E-1 |
| daily_loss_max_pct | Decimal | percent; base not stated | no | exactly 2 | RISK-5 | base, realised or mark-to-market, day boundary (U-2); action on breach (U-3) | E-1 |
| weekly_loss_max_pct | Decimal | percent; base not stated | no | exactly 5 | RISK-6 | base, week boundary (U-2); action on breach (U-3) | E-1 |
| max_drawdown_pct | Decimal | percent; base not stated | no | exactly 10 | RISK-7 | base and peak definition (U-2) | E-1 |
| risk_per_trade_pct | Decimal | percent; base not stated | no | exactly 1 | RISK-8 | base (U-2) | E-1 |
| liquidity_cap_pct_addv | Decimal | percent of ADDV | no | exactly 1 | RISK-9 | ADDV window, currency, per order or per day (U-6) | E-1 |
| orders_per_minute_global_max | int | orders per minute | no | exactly 20 | RISK-10 | what counts as an order, window type (U-8); relation to per-second cap (C-5) | E-1 |
| orders_per_minute_per_strategy_max | int | orders per minute | no | exactly 10 | RISK-11 | same as RISK-10 | E-1 |
| stop_atr_multiple | Decimal | dimensionless multiple of ATR | no | exactly 2.5 | RISK-12 | short-side formula (C-3); tick rounding (U-7) | E-1 |
| stop_atr_period_bars | int | bars | no | exactly 14 | RISK-12 | bar frequency, adjusted or raw prices (U-7) | E-1 |
| default_order_type | str literal | none | no | exactly `limit` | RISK-13 | none | E-1 |
| emergency_exit_order_type | str literal | none | no | exactly `market` | RISK-13 | definition of emergency exit (U-9) | E-1 |

A field whose "Not stated by Block A" cell is not "none" records a number only. No phase may
write a rule that enforces it until the cited U or C item is closed in a new-run spec.

### 5.3 Error paths

| # | Condition | Detected by | Fail-closed behaviour |
|---|-----------|-------------|-----------------------|
| E-1 | A field of `ConstitutionRiskDefaults` is given a value other than its Block A value, a value of the wrong type (for example a `float` for a `Decimal` field), or an unknown field is supplied. | Pydantic `ValidationError` at construction (`strict=True`, `extra="forbid"`, `ge` equal to `le`). | The object is not created. Any process that constructs it at start-up does not start. No order path exists in a process that did not start. |
| E-2 | Code assigns to a field after construction. | Pydantic `ValidationError` (`frozen=True`). | The assignment does not happen; the exception propagates and is not caught. |
| E-3 | A string that is not a valid `ConstitutionRef` is validated as one. | Pydantic `ValidationError` on the pattern. | The citation is rejected; a check that validates citations fails. |
| E-4 | A P1.3 policy default differs from the corresponding field here. | The equality test required by 5.1, run in CI. | CI fails; the P1.3 code drop does not land. |
| E-5 | A phase needs a value listed under "Not stated by Block A". | Author of that phase. | The phase records an OPEN QUESTION or closes the cited U or C item; it does not assume a value (RULE-1). |

Evidence: the model in 5.1 was executed on 2026-10-13 with Python 3.11 and Pydantic 2.13.5.
Default construction succeeded. Rejected as expected: `position_max_pct_nav=Decimal("6")`,
`position_max_pct_nav=5.0`, `orders_per_minute_global_max=21`, an extra field,
`default_order_type="market"`, assignment after construction, and the references `INV-0`,
`INV-11`, `RISK-14`, `RULE-6`, `N-7`, `inv-1`, and `INV-1` with a trailing space. It was not
run on Python 3.12 or later: Pydantic is not installed for 3.13 or 3.14 on this machine (R-4).

## 6. Blocking questions and the defaults used

Block C requires up to ten blocking questions, a recommended default for each, and that work
proceeds on the defaults. These are the ten where two reasonable answers give materially
different designs. A default here is provisional: it is not a ruling, it does not close the
C or U item it refers to, and the owning phase must either confirm it or replace it. A later
spec that relies on one cites it as `[DEFAULT-n]`. If the Owner overrules a default, every
spec that cites it is re-checked. `[DEFAULT-1]` is the decision-log location in R-3.

### Q1. Does DENY cover risk-reducing actions? (C-1, OQ-2) [DEFAULT-2]

Options:
- (a) Literal. Any audit failure or stale input denies every action, exits included.
- (b) Exits are exempt from INV-5 during an outage.
- (c) INV-5 stays absolute, the audit trail gets a second local sink, and INV-6 is read by
  direction of risk.

Default: (c).
- INV-5 has no exception. The audit trail has two sinks: the database, and an append-only,
  hash-chained, fsynced file on the VM's local disk. A record written to either sink before
  the action satisfies INV-5. Records written only to the file are copied into the database
  when it returns, and the chain is verified across both.
- If both sinks fail, no automated action happens, exits included. The kill switch (INV-7) is
  then the only path, and it keeps its own record.
- INV-6 DENY means "do not open or increase risk". An exit whose trigger was evaluated on
  valid data is not cancelled because data went stale afterwards. An exit sent as a market
  order (RISK-13) needs no market value, so nothing is synthesised.

Edge cases:
- Data is stale before any trigger fires: no stop can be evaluated, so no exit is generated.
  That state is an escalation condition; which one is P2.10's decision.
- The local disk is full: the file sink fails; if the database is also down, see "both fail".
- A record is in the file but the action's outcome is unknown after a crash: the position is
  reconciled against the broker before anything else runs (P5.5).

If the default is wrong: under (a) the system holds every position through a database outage.
Under (b) a regulator finds orders with no prior audit record.

### Q2. Long-only or long/short, and is margin allowed? (C-2, C-3, OQ-3) [DEFAULT-3]

Options: (a) long-only, cash only; (b) long-only with margin up to RISK-3; (c) long/short.

Default: (a), until P0.1 ADR 12 decides.
- No short sales and no borrowing. Gross exposure equals net exposure, so RISK-4 (1x) binds and
  RISK-3 (2x) is never reached. RISK-3 stays in the record unchanged.
- RISK-12 applies as written, because every position is long.

Edge cases:
- A corporate action or a broker error produces a negative quantity: it is not a strategy
  position. New entries in that market are denied and the position is escalated.
- A buy fills for more than was ordered: the excess counts toward RISK-1 and RISK-4 at once.
- Unsettled sale proceeds used for a new buy can create broker-side margin use without any
  borrowing decision. Whether unsettled cash may be spent is P2.8's question.

If the default is wrong: sizing, short-side stops, borrow costs, and margin and PDT handling
are all missing from the design.

### Q3. What makes the kill switch independent on one VM? (C-4) [DEFAULT-4]

Options:
- (a) A separate process on the same VM only.
- (b) A separate process on the VM, plus protective stop orders resting at the broker, plus a
  written manual procedure a human runs from another device.
- (c) A second host running an automatic watchdog.

Default: (b).
- The kill switch is its own OS process and container. It imports no code from the model,
  LLM or decision path and has its own broker credentials.
- Every open position has a stop order resting at the broker where the broker supports one
  (OQ-11), so a dead VM does not leave a position without a stop.
- VM loss is handled manually: a human cancels orders and flattens from the broker's own
  console, following a runbook (P6.4).

This default does not fully satisfy INV-7. INV-7 says "automatic + manual". If the VM is lost,
only the manual path and the resting stops remain; nothing automatic runs. Option (c) would
satisfy it but adds a host, which STACK-1 excludes. The Owner must accept the gap or allow (c).

Edge cases:
- The broker does not support a resting stop for an instrument or session: that instrument is
  not eligible for entry.
- A resting stop and the system's own exit both fire: the second order must be rejected or
  cancelled before it opens a short position; P3.4 owns the mechanism.
- The VM dies while no human is available: positions are protected only by resting stops,
  which do not protect against a gap through the stop price.

If the default is wrong: under (a) a VM failure leaves live orders and unprotected positions.

### Q4. How are the per-minute limits enforced, and do exits count? (C-5, U-8) [DEFAULT-5]

Options:
- (a) Rolling 60-second count.
- (b) Calendar-minute count.
- (c) Minimum spacing between submissions.

Default: (c).
- Global: at least 3 seconds between any two order submissions (60 / 20, from RISK-10).
- Per strategy: at least 6 seconds between two submissions of one strategy (60 / 10, RISK-11).
- Spacing satisfies both (a) and (b). It also means at most one order in any second, which
  meets any per-second exchange threshold of one or more. The real threshold is OQ-1.
- New orders and modifications count. Cancellations do not count toward RISK-10 or RISK-11.
- Exits count. There is no exemption for risk-reducing orders.

Edge cases:
- Exactly 3.000 seconds after the previous submission: allowed (inclusive).
- An order that the broker rejects still counts: it was submitted.
- The clock steps backwards: spacing is measured on a monotonic clock, not wall time.
- Flattening N positions takes at least (N - 1) x 3 seconds. Twenty positions take 57 seconds.
  Whether the kill switch may bypass RISK-10 is P2.10's decision; the exchange cap can never be
  bypassed.
- Cancels may count toward the exchange's per-second measure even though they do not count
  here (OQ-1).

If the default is wrong: a rebalance that needs a burst is slower than intended; in the other
direction, a rolling count would allow twenty orders in one second.

### Q5. What happens in India on a day with no human login? (C-6, OQ-7) [DEFAULT-6]

Options: (a) automate the login; (b) a human logs in before each session; (c) no India trading.

Default: (b), assuming OQ-7 confirms that a daily manual login is required.
- With no valid session at the India open, the India market is disabled for that session: no
  new orders. An alert is raised. The US market is unaffected.
- Existing India positions are protected only by stops resting at the broker (Q3).

Edge cases:
- The login happens mid-session: India is enabled from the next decision cycle; no order that
  was skipped is sent late.
- The session token expires during the session: same state as no login, from that moment.
- An Indian trading day that is a US holiday, or the reverse: each market is enabled or
  disabled on its own calendar.

If the default is wrong: if login can be automated within broker terms, the human step is
unneeded; if it cannot and nobody logs in, India positions go unmanaged for the session.

### Q6. Are NAV and equity the same number, and per market or combined? (U-1) [DEFAULT-7]

Options: (a) one combined NAV in a base currency; (b) one number per market account.

Default: (b). "NAV" and "equity" are the same number.
- Per market account: cash plus the sum of quantity x price over open positions, in the
  account's currency (USD for the US account, INR for the India account).
- RISK-1 to RISK-8 are measured per account against that account's number. No FX rate enters
  the risk path. A combined figure, if P0.1 ADR 15 wants one, is for reporting only.

Edge cases:
- A held position has no valid price: the NAV of that account cannot be computed. New entries
  in that market are denied. The last close is not substituted (INV-6).
- Which cash figure (settled, unsettled, buying power) is used is not decided here; P2.9.
- A deposit or withdrawal changes NAV without any profit or loss; see Q7.
- One account is empty: its NAV is zero and every percentage limit denies entry there.

If the default is wrong: per-account limits are tighter than combined ones, so positions are
smaller than intended. The error is in the safe direction.

### Q7. Loss limits: base, valuation, day boundary, action on breach (U-2, U-3) [DEFAULT-8]

Options for valuation: realised only, or mark-to-market. Options for the base: start-of-day
NAV, current NAV, or peak NAV.

Default:
- Valuation is mark-to-market: realised plus unrealised, per account (Q6).
- Daily loss base: that account's NAV at the previous session close. An overnight gap counts
  against today.
- The day is the exchange's session date in exchange local time: `America/New_York` for the
  US, `Asia/Kolkata` for India. It is never the UTC date.
- Weekly loss base: NAV at the close of the last session of the previous ISO week. The week is
  Monday to Sunday by session date.
- Drawdown: (peak - current) / peak, where peak is the highest session-close NAV on record
  and current is the live mark-to-market NAV.
- A limit is breached when the loss is strictly greater than the limit. A loss of exactly
  2.00% is not a breach.
- Daily breach: no new entries in that market for the rest of that session. Weekly breach: no
  new entries in that market until the next ISO week. In both, exits and stops keep working
  and nothing is liquidated. Drawdown breach in either account trips the kill switch for both.
- External cash flows are removed from the calculation: the base is adjusted by the amount.

Edge cases:
- First session of an account: there is no previous close. The base is the first valid NAV
  computed that day.
- A week whose Monday is a holiday starts at its first session. A half-day session has the
  same date boundary as a full one.
- US daylight-saving changes do not move the session date. India has no daylight saving.
- NAV cannot be computed (Q6): the loss cannot be measured, so new entries are denied.
- A daily breach clears at the next session on its own. A drawdown breach does not clear on
  its own; INV-7 requires a human.
- A new peak is recorded only at a session close, so an intraday high does not raise the peak.

If the default is wrong: realised-only would let an open losing position run past 2% unseen;
a current-NAV base would shrink the allowance as losses grow.

### Q8. When is the 5% position limit measured? (U-4) [DEFAULT-9]

Options: (a) before the order only; (b) before the order and continuously with forced trims;
(c) before the order, with a passive breach blocking further buys only.

Default: (c).
- Before a buy: (held quantity + order quantity) x the order's limit price, divided by the
  account NAV (Q6) last computed from valid prices. The result must be at most 5% (inclusive).
- Open, unfilled buy orders in the same instrument count as if filled.
- If a price rise takes a held position above 5%, nothing is sold for that reason. Further
  buys of that instrument are denied until it is at or below 5%.
- RISK-2 (sector) follows the same three rules with 20%.

Edge cases:
- Projected weight exactly 5.000%: allowed.
- NAV falls because other positions lose value, pushing this one above 5%: same as a rally.
- A partial fill leaves the remainder open: the remainder still counts.
- Shares arrive from a split or bonus issue: quantity changes, weight does not; no action.
- A passive breach has no upper bound under this default. Whether to add a forced-trim
  ceiling is P2.9's decision.

If the default is wrong: under (b) the system sells winners automatically, which changes
strategy results and adds orders.

### Q9. Where does new-run code go? (R-1, OQ-8) [DEFAULT-10]

Options:
- (a) Overwrite `src/`, `migrations/`, `tests/`, `config/` in place; git history keeps the
  old versions.
- (b) A new top-level directory `v2/` holding `v2/src/`, `v2/migrations/`, `v2/tests/`,
  `v2/config/`.

Default: (b). N-2 says historical files are not edited.

Edge cases:
- `docker-compose.yml`, `.github/workflows/`, `.gitignore`, `.env.example` and `README.md` are
  shared root files. None is edited without the Owner approving that file's diff.
- The historical migration `0001_initial.sql` and a new-run migration cannot be applied to
  the same database. The new run uses its own database name.
- A historical test imports `src.`; new-run code is never importable under that name.

If the default is wrong: under (a) the working tree no longer shows the historical code, and
the Owner's instruction to preserve it is met only through history.

### Q10. What runs next, and where? (R-5, OQ-10) [DEFAULT-11]

Options: (a) the pack restarts at P0.1; (b) Blocks A to C are re-applied to an existing spec.

Default: (a). Phases run in pack order, one at a time, each only when the Owner supplies that
phase's prompt. No phase is started unasked.

Edge cases:
- The pack says one fresh conversation per phase. If the Owner runs a phase in this
  conversation instead, the spec records that in its header notes.
- `master-research-summary.md` is the pack's stated scope source and the declared input of
  P0.1. It is used for scope. Any external fact in it is re-verified before a new-run spec
  states it (N-3).

If the default is wrong: work is done on the wrong phase.

## 7. Edge cases for the rules this file writes

| Rule | Edge case | Resolution |
|------|-----------|------------|
| N-1 | Output that is not a spec: review reports, evidence, proposed diffs. | It goes under `docs/new specs/reviews/`. |
| N-1 | `docs/PROMPT-PACK.md` sits outside `docs/new specs/`. | It is the process definition. It is read, not edited. |
| N-2 | A defect is found in a historical file. | It is recorded in a new-run spec. The historical file is not fixed. |
| N-2 | A file not named in N-2 (`docker-compose.yml`, `.github/`, `.gitignore`, `.env.example`, `README.md`, `master-research-summary.md`, `issues/`, `DeepSeek-Research/`). | Treated as historical. Edited only with the Owner's approval of that diff. `.env` is never read or edited. |
| N-3 | A historical spec holds a fact whose external source can no longer be reached. | The fact is not carried over. It becomes an OPEN QUESTION. |
| N-3 | `master-research-summary.md` is a required input of P0.1. | Used for scope only; see Q10. |
| N-4 | A change needs review before it lands. | The diff is shown to the Owner and committed on `main` after approval. No force-push, no amended published commit. |
| N-5 | The same spec id exists in `docs/specs/` and `docs/new specs/`. | A new-run `depends_on` always means the file under `docs/new specs/`. N-3 forbids the other. Prose that mentions a historical spec gives its full path. |
| N-6 | A tool that cannot take a quoted path. | The tool is not used on that path. The directory is not renamed. |
| N-6 | The path inside a URL. | The space is written `%20`. |
| D-3 | A range such as `INV-1..INV-10`. | It is shorthand in prose and in `produces`. It is not a valid `ConstitutionRef`; each item is cited singly where a citation is checked. |
| D-3 | Block A text changes. | Section 2 is replaced, identifiers are re-derived, the version is raised, and every spec citing a changed item is re-checked. An identifier is never reused for a different item. |
| 5.1 fixed values | `Decimal("5.00")` for a field fixed at 5. | Accepted: comparison is numeric. Verified. |
| 5.1 fixed values | Python `int` 5 or `str` "5" for a `Decimal` field. | Rejected in Python construction. Verified. |
| 5.1 fixed values | JSON input `5`, `5.0` or `"5"` through `model_validate_json`. | Accepted: JSON has no decimal type. `5.0000001` is rejected. Verified. No consumer loads this record from JSON; it is constructed with defaults. |
| 5.1 fixed values | `Decimal("NaN")`. | Rejected. Verified. |
| 5.1 integer literals | `20.0` passed for `orders_per_minute_global_max`. | Accepted, because `Literal` compares by equality and `20.0 == 20`. Verified. Harmless for a record built from defaults; P1.3 must not reuse `Literal` to validate integers read from a file. |
| 5.1 integer literals | `True` passed for an integer field. | Rejected. Verified. |
| 5.2 inclusive bounds | A measured value equal to the limit. | Passes. A breach is strictly greater than the limit (Q7, Q8). |
| 5.2 enforcement bar | A phase needs a field whose gap has a section 6 default. | It may build on the default by citing `[DEFAULT-n]`, and it must close the U or C item in its own spec. |
| 5.3 E-1 | The process that fails to start is the kill switch. | The kill switch does not construct this record. It has no dependency on it (Q3). |
| `ConstitutionRef` | `INV-01`, lower case, trailing newline or space. | Rejected. Verified. |
| Block A "configurable but never by the AI" | Who may change a value in this record. | Nobody at run time. The Owner changes Block A; this file follows as a new version. |

Evidence for the rows marked "Verified": executed on 2026-10-13 with Python 3.11 and Pydantic
2.13.5, same limits as the evidence note in section 5.3.

## 8. Non-blocking details resolved in this file

| # | Detail | Resolution |
|---|--------|------------|
| NB-1 | Unit of a percentage | The number as written: 5 means 5% (A-4). |
| NB-2 | Inclusive or exclusive bounds | Every "<=" is inclusive. Breach means strictly greater. |
| NB-3 | Number types | Percent and ratio values are `Decimal`. Counts are `int`. `float` is never used for a limit or for money. |
| NB-4 | Timezones | Named by IANA identifier: `America/New_York`, `Asia/Kolkata`. A "day" is the exchange session date in that zone, never the UTC date. |
| NB-5 | Daylight saving | The US zone changes offset twice a year; the session date does not move. India has none. |
| NB-6 | Half-days | Same session-date boundary as a full day. |
| NB-7 | Week | ISO week, Monday to Sunday, by session date. |
| NB-8 | Off-by-one in ATR(14) | Each true range uses the previous bar's close, so 14 true ranges need 15 bars. With fewer, there is no ATR, no stop, and therefore no entry (INV-6). The smoothing method is P2.4's decision. |
| NB-9 | "At entry" in RISK-12 | The ATR from the last completed bar before the decision. A bar still forming is never used. |
| NB-10 | Rate-limit clock | Monotonic clock for spacing (Q4). |
| NB-11 | Dates in this file | ISO 8601 calendar dates. |
| NB-12 | Tick size, lot size, and rounding of a stop price | Not resolved here. No rule in this file produces a price or a quantity. Owned by P1.1 and P3.4 (U-7). |
| NB-13 | Integer or decimal money | Not resolved here. This file holds no money amount. Owned by P1.1. |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| D-1 | New-run specs live in `docs/new specs/` under the pack's file names. | N-1, N-5. | Yes, by moving files. | Path references in later specs. |
| D-2 | Historical files are preserved and are not inputs to the new run. | N-2, N-3. | Yes. | Re-verification work repeated. |
| D-3 | Block A is recorded verbatim and cited by INV/RISK/RULE identifiers. | Later specs need single-item citations. | Yes. | Renumbering across specs. |
| D-4 | No contradiction in section 4 is ruled on in this file. Section 6 gives provisional defaults only. | Block A states the invariants are decided; a ruling between two of them is the Owner's. Block C requires work to proceed on stated defaults. | Yes. | Every spec citing an overruled default. |
| D-5 | The risk defaults are typed as a frozen model whose fields accept only the Block A value. Percent and ratio values are `Decimal`, counts are `int`. | Block B: no prose-only types. A constant record that accepted other values would be a second policy file. | Yes. | P1.3 equality test. |
| D-7 | Where a default must choose between a looser and a tighter reading, it takes the tighter one (per-account NAV, spacing instead of a count, long-only, mark-to-market). | INV-6. A wrong tight default costs opportunity; a wrong loose one costs money. | Yes. | Smaller or slower trading than intended. |
| D-6 | This file does not give permitted configuration ranges for the risk numbers. | Block A says they are configurable and gives no range; P1.3 owns the policy DSL. | Yes. | None here. |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| A-1 | [DEFAULT-1] The new-run decision log is `docs/new specs/DECISIONS.md`. | The root file is historical and N-2 forbids editing it. | Owner confirms. | One file move. |
| A-3 | The prompt pack `docs/PROMPT-PACK.md` remains the process for the new run. | It is the only place Blocks A, B, C and the phase prompts are defined. | Owner confirms. | Phase order and deliverable names change. |
| A-4 | Percent fields store the number as written (5 means 5%), not a fraction (0.05). | Block A writes percentages and does not state a storage convention. | P1.1 fixes the convention for all specs. | Field values in 5.1 change; a factor-of-100 error if a consumer assumes the other form. |
| A-5 | [DEFAULT-2] INV-5 is absolute; the audit trail has a database sink and a local file sink; DENY is read by direction of risk. | C-1 has no ruling. | Owner rules on OQ-2. | P1.4, P2.9, P2.10, P3.4 designs change. |
| A-6 | [DEFAULT-3] Long-only, no borrowing. | C-2 and C-3 have no ruling. | P0.1 ADR 12. | Sizing, stops and margin handling for shorts are missing. |
| A-7 | [DEFAULT-4] Kill switch is a separate process on the VM, with broker-resting stops and a manual off-VM procedure. Does not fully meet INV-7 on VM loss. | C-4; STACK-1 allows one VM. | Owner accepts the gap or allows a second host; OQ-11. | No protection on VM loss beyond a human. |
| A-8 | [DEFAULT-5] Rate limits are enforced as minimum spacing of 3 s global and 6 s per strategy; exits count; cancels do not. | C-5 and U-8. | OQ-1; P2.9 confirms. | Slower bursts, or an exchange breach if cancels are counted by the exchange. |
| A-9 | [DEFAULT-6] India needs a human login each trading day; without it India is disabled for that session. | C-6. | OQ-7. | Unneeded human step, or unmanaged India positions. |
| A-10 | [DEFAULT-7] NAV equals equity, one number per market account in its own currency; no FX in the risk path. | U-1. | P0.1 ADR 15; P1.1. | Limits tighter than intended. |
| A-11 | [DEFAULT-8] Loss limits are mark-to-market against previous-close NAV, by exchange session date; breach is strictly greater; daily and weekly breaches stop new entries; drawdown trips the kill switch for both accounts. | U-2 and U-3. | P2.9. | Loss allowance and halt behaviour differ from the Owner's intent. |
| A-12 | [DEFAULT-9] Position and sector limits are tested before the order on projected weight; a passive breach blocks buys and forces no sale. | U-4. | P2.9. | Unbounded passive concentration, or unwanted automatic sells. |
| A-13 | [DEFAULT-10] New-run code goes under `v2/`. | R-1. | Owner answers OQ-8. | Paths in every code drop. |
| A-14 | [DEFAULT-11] The pack restarts at P0.1, one phase at a time, each on the Owner's prompt. | The instruction says to work from the start. | Owner answers OQ-10. | Work on the wrong phase. |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| OQ-1 | What exactly does SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 require for: the per-order identifier and who issues it, the orders-per-second threshold and its value, static IP, kill switch, and testing? What is its effective date after any extension? | SEBI circular text; NSE and BSE implementation circulars | sebi.gov.in, search the circular number; nseindia.com and bseindia.com circulars citing it | P0.2, P2.9, P6.3 |
| OQ-2 | C-1: does DENY (INV-5, INV-6) apply to risk-reducing actions (stop exit, emergency exit, kill-switch flatten) when the audit store or market data is unavailable? | Owner | Ruling on C-1 | P1.4, P2.9, P2.10, P3.4 |
| OQ-3 | C-2, C-3: long-only or long/short, and is margin borrowing permitted up to RISK-3? | Owner, through P0.1 ADR 12 | P0.1 | P2.8, P2.9, P3.4 |
| OQ-4 | Is the US pattern-day-trader rule in INV-9 still in force in its USD 25,000 form? | FINRA Rule 4210 current text and any SEC approval order amending it | finra.org Rule 4210; sec.gov SRO rule filings for FINRA, search "pattern day trader" | P0.1 ADR 13, P2.9, P6.3 |
| OQ-5 | Is the account holder a US taxpayer? Wash-sale handling (INV-9) depends on it. | Owner; then a tax adviser | Owner states tax residency; IRC section 1091 applicability | P6.3 |
| OQ-6 | Can the account holder open an Alpaca live trading account from their country of residence, and under which account type? | Alpaca | alpaca.markets supported-countries documentation; Alpaca support | P0.2 |
| OQ-7 | C-6: does Zerodha Kite Connect require a manual login each day, and do its terms allow automating it? | Zerodha | kite.trade/docs/connect/v3/user (login flow); Kite Connect terms | P0.2, P3.1 |
| OQ-8 | R-1: where does new-run code go so that historical `src/`, `migrations/`, `tests/` are preserved? | Owner | Owner decision | First code phase |
| OQ-9 | R-2: what should happen to the three uncommitted historical changes in the working tree? | Owner | Owner decision | None; affects commit hygiene |
| OQ-10 | R-5: which phase follows Block A in this run, and is it run in this conversation or a fresh one? | Owner | Owner decision | P0.1 |
| OQ-11 | For each broker, which stop order types can rest at the broker across sessions, for which instruments, and for how long before they expire? | Alpaca and Zerodha order documentation | docs.alpaca.markets, orders: stop and time-in-force; kite.trade/docs/connect/v3, orders and GTT | P0.2, P2.10, P3.4 |
| OQ-12 | Does the Owner accept that DEFAULT-4 leaves no automatic kill path when the VM is lost, or is a second host allowed for a watchdog? | Owner | Ruling on C-4 | P2.10, P6.4 |

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| INV-1..INV-10 | invariant identifier | Section 2 item n, cited as `INV-n` | every new-run spec |
| RISK-1..RISK-13 | risk-limit identifier | Section 3 table row, cited as `RISK-n` | P1.3, P2.8, P2.9, P2.10, P3.4 |
| RULE-1..RULE-5 | behavioural-rule identifier | Section 2 bullet n, cited as `RULE-n` | every new-run spec |
| STACK-1 | stack constraint | Section 2 FIXED STACK paragraph | every new-run spec |
| N-1..N-6 | repository rule | Section 1 table | every new-run phase |
| DEFAULT-1..DEFAULT-11 | provisional default identifier | R-3 and section 6, cited as `[DEFAULT-n]`; not a ruling | every new-run spec that builds on one |
| ConstitutionRef | type | Section 5.1; a strict `str` constrained by the regular expression given there | every new-run spec and code drop that cites the constitution |
| ConstitutionRiskDefaults | type | Section 5.1; frozen Pydantic v2 model, 15 fields, section 5.2 | P1.3 (default-equality test), P2.9 |
