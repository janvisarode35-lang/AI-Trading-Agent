---
id: SPEC-P1.1-DOMAIN
version: 0.3
status: DRAFT
phase: P1.1 — Domain Model & Type System
depends_on: [SPEC-P0.1-DECISIONS v0.3, SPEC-P0.2-PROVIDERS v0.5, SPEC-P0.3-BUDGET v0.5, STAGE-0-FREEZE v1.1, master-research-summary.md]
produces: [src/domain/models.py, src/domain/errors.py, type.Money, type.Price, type.Quantity, type.InstrumentId, type.TradingCalendar, enum.Market, enum.Exchange, enum.Currency, enum.InstrumentType, enum.InstrumentStatus, enum.AccountType, enum.PoolId, enum.CorporateActionType, enum.OrderState, enum.OrderSide, enum.OrderType, enum.TimeInForce, enum.PositionState, enum.KillSwitchState, enum.KillSwitchScope, enum.RiskDecision, enum.SignalDirection, enum.ScoreKind, enum.RegimeLabel, enum.CostBasisMethod, enum.SessionType, enum.RunType, enum.ApproverRole, enum.AuditEventClass, model.Instrument, model.SymbolMapping, model.SuccessorLink, model.ExchangeSession, model.Bar, model.Quote, model.Trade, model.FundamentalsSnapshot, model.CorporateAction, model.NewsItem, model.Candidate, model.Score, model.Signal, model.Thesis, model.InvalidationCondition, model.Decision, model.RiskVerdict, model.PositionSizeRequest, model.Order, model.Fill, model.Lot, model.Position, model.Portfolio, model.NAV, model.Account, model.Regime, model.KillSwitch, model.AuditEvent, model.RunContext, model.StalenessPolicy]
---

# SPEC-P1.1 — Domain Model & Type System

**Phase:** Stage 1 — SPECIFY, prompt `P1.1`
**Date:** 2026-08-26 (v0.1) · **2026-08-27 (v0.2, post-X2)**
**Author role:** Domain modeller
**Version 0.3, 2026-08-27:** two decisions **superseded by P1.4** — see SPEC-P1.4 §0. `AuditEvent` and `verify_audit_chain` are removed from the domain module in favour of `audit.events.AuditEnvelope` / `audit.chain.verify_chain`; `AuditEventClass` stays here and is imported by the audit layer. Identifier guidance for audit events becomes **UUIDv7**.
**Version 0.2, 2026-08-27:** ten findings from `X2 — CODE REVIEW` applied — one BLOCKER,
five HIGH, three MEDIUM, one LOW. See §15. **Status remains DRAFT**: `X3 — MERGE` is the
step that sets a spec to FROZEN, and it has not run.
**Consumes:** SPEC-P0.1-DECISIONS **v0.3** — per STAGE-0-FREEZE §10's specific instruction to this
phase, including the twelve configuration keys added by AD-1…AD-5.

> This document defines the typed vocabulary. Every downstream phase imports these names rather
> than inventing synonyms. Where a name here differs from one in `master-research-summary.md`,
> **this document wins** and §13's glossary records the mapping.

---

## 0. Governing material and precedence

Precedence actually applied, inherited from SPEC-P0.1 §0.1:

1. **Block A Constitution** — except the one line STAGE-0-FREEZE §3.1 has already amended
   (LLM primary/fallback ordering). That amendment is honoured here.
2. **Frozen Stage 0 specs** — P0.1 v0.3, P0.2 v0.5, P0.3 v0.5.
3. **Block B Output Contract** and **Block C Clarifier Rule**.
4. `master-research-summary.md` — research input, not a decision record. Where it conflicts with a
   frozen decision, the frozen decision wins.

### 0.1 Fact-labelling convention

Carried unchanged from P0.1 §0.2 so labels mean the same thing across the spec tree.

| Label | Meaning |
|---|---|
| `[V]` | Verified against primary documentation, with the source named |
| `ASSUMPTION` | Stated, unverified, with a verification route |
| `[DEFAULT-n]` | A Block C default applied because the question was blocking |
| `[RS §n]` | Sourced from `master-research-summary.md` section n |
| `[CONST-n]` | Block A Constitution, invariant n |

### 0.2 What binds this phase specifically

STAGE-0-FREEZE §10 and P0.1 §8's downstream-constraint table name the following as hard
requirements on P1.1. Each is discharged at the section given.

| Requirement | Source | Discharged in |
|---|---|---|
| `Market` enum on every instrument, bar, order, position, decision, audit row | ADR-11 req 1 | §5.1, §14 |
| `Exchange` + a trading-calendar **type** — not a hard-coded US holiday list | ADR-11 req 2 | §4 |
| `Currency` and `Money` explicit; cross-currency arithmetic **raises** | ADR-11 req 3, ADR-15, I1 | §3.2 |
| Tick size, lot size, fractional capability as **per-market instrument attributes**, never constants | ADR-11 req 6, A-11, rule N10 | §3.3, §5.2 |
| `AccountType.CASH`; `settled_cash` and `day_trades_5d` both present | ADR-12, ADR-13 Chain D | §9.4 |
| Lot-level cost basis + wash-sale adjustment field, from day one | ADR-13 Chain E | §9.1 |
| `InstrumentType` deny-by-default allowlist | ADR-05, I5 | §5.3 |
| Order price not an exact tick multiple → **rejected locally, never rounded** | rule N10 `[V]` | §3.3 |
| News revisions stored as new rows; first-seen revision is the point-in-time record | rule N16 `[V]` | §6.5 |
| A WebSocket gap is assumed lost | rule N5 `[V]` | §6.7 |
| Kill switch restores `TRIPPED` on boot, unconditionally | ADR-10, I3 | §11.3 |
| No code path overrides a risk DENY | ADR-09, I2 | §8.2, §11.4 |
| Paper results may never be cited as live evidence | rule N11 | §10.4 |

---

## 1. BLOCKING questions — and the defaults applied

Per Block C: ten questions where two reasonable answers produce materially different designs. Each
is answered with the recommended default and **proceeded on**. Every `[DEFAULT-n]` below appears
inline at its point of use and again in ASSUMPTIONS.

| # | Question | Options | Default applied | What breaks if the default is wrong |
|---|---|---|---|---|
| **1** | Is `instrument_id` identity per **security** or per **listing venue**? | (a) per issuer/security, one id across venues; (b) **per listing venue** | **(b) per listing** `[DEFAULT-1]` | If (a) were right, a dual-listed name (NSE + BSE) would need one position spanning two currencies and two tick regimes — which ADR-15's segregated pools forbid anyway. If (b) is wrong, cross-venue aggregation needs a later `issuer_id` rollup, which §5.1 already provides as a nullable field, so the cost of being wrong is a reporting join, not a migration |
| **2** | What is the storage precision of `Price`? | (a) 2 dp; (b) 4 dp; (c) **6 dp** | **(c) 6 dp** `[DEFAULT-2]` | Matches `tick_size NUMERIC(12,6)`, already frozen in P0.2's `tick_size_regime` DDL. At 2 dp a sub-penny execution price truncates and reconciliation against the broker fails on every price-improved fill. At 6 dp nothing observed to date truncates |
| **3** | Are fractional shares usable in v1? | (a) yes; (b) **capability modelled, disabled**; (c) not modelled at all | **(b)** `[DEFAULT-3]` | `[CONST]` mandates limit orders by default; P0.2 verified US fractional trading is **market/day orders only**. The two constraints are jointly unsatisfiable, so fractional is structurally unreachable in v1 — see §3.4 and OPEN QUESTION Q-P1.1-3. Modelling the capability while setting `qty_increment = 1` for US costs nothing now and avoids a schema change if the broker constraint moves |
| **4** | May `Money` be divided? | (a) yes, with a rounding mode; (b) **no — `allocate()` only** | **(b)** `[DEFAULT-4]` | Division is not closed over a fixed-exponent decimal (§3.2). Permitting it means the sum of the parts silently differs from the whole, which surfaces as a one-cent NAV drift compounding across every partial-lot consumption. `allocate()` uses largest-remainder and is exact by construction |
| **5** | How is a naive `datetime` handled at a model boundary? | (a) coerce, assuming UTC; (b) coerce, assuming exchange-local; (c) **reject** | **(c) reject** `[DEFAULT-5]` | A naive datetime carries no evidence of intent. Coercion under (a) silently shifts an exchange-local timestamp by 4–5.5 hours and stays invisible until a session-boundary test fails. Rejection is the `[CONST-6]` reading of an ambiguous state |
| **6** | Is the wash-sale field global or US-only? | (a) global, nullable; (b) **US-only, `NULL` enforced for `IN`** | **(b)** `[DEFAULT-6]` | ADR-13 Chain E: India has no wash-sale rule. A populated wash-sale field on an Indian lot is a data-integrity error that would corrupt the India tax export. Enforced by validator, not by convention |
| **7** | What is the closed set of `RegimeLabel` values? | (a) free string; (b) **`BULL`/`BEAR`/`SIDEWAYS`/`VOLATILE`/`UNKNOWN`** | **(b)** `[DEFAULT-7]`, vocabulary from `[RS §13]` "Bull, bear, sideways, volatile" | P2.6 owns the classifier, not the vocabulary. A free string means the risk engine cannot exhaustively match on regime and an unrecognised label passes through — the opposite of deny-by-default. `UNKNOWN` exists so the fail-closed path has a value to carry |
| **8** | How is `[CONST-2]` ("no final trade decision without a deterministic gate") enforced? | (a) by convention and code review; (b) **structurally — `Decision` cannot be constructed without an `ALLOW` `RiskVerdict`** | **(b)** `[DEFAULT-8]` | Under (a) the invariant is a comment. Under (b) an LLM-originated `Thesis` has no type-level path to becoming a `Decision`: the only constructor requires a `risk_verdict_id` whose verdict is `ALLOW`, and `RiskVerdict` is frozen and produced only by P2.9 |
| **9** | Does P1.1 or P1.4 own `AuditEvent`? | (a) P1.4 entirely; (b) P1.1 owns the chained envelope, P1.4 owns the event catalogue | **(b) — SUPERSEDED. P1.4 §0 moved to (a)** `[DEFAULT-9]` | Every model in this file needs to reference an audit event id, so the envelope must exist here or P1.1 acquires a forward dependency on P1.4. Splitting envelope from catalogue lets P1.4 add event types without reopening this spec |
| **10** | Is an ambiguous broker order response a state or an exception? | (a) exception, retry; (b) **an explicit `UNKNOWN` state** | **(b)** `[DEFAULT-10]` | An exception that is caught and retried loses the fact that an order **may** be live at the broker. `UNKNOWN` is a real, persisted, fail-closed state: it blocks new entries for that instrument and forces reconciliation before anything else happens (§11.1) |

---

## 2. NON-BLOCKING details noticed and resolved

P0.1 §6 already froze 27 of these — timezone at rest, timers, US DST, half-days, Muhurat
exclusion, money type, percentages, inclusive limit bounds, rolling windows, filter prices, market
cap, ADDV, halted stocks, tick size, lot size, order-quantity rounding, sign convention,
cost-basis method, day boundary, overnight gaps, stop activation, universe membership, delisting,
`model_id`/`prompt_version`, fiscal-vs-calendar quarters, empty-universe sessions. Those are
**adopted verbatim and not re-decided here.** Below is only what P1.1 additionally had to resolve.

| # | Detail | Resolution |
|---|---|---|
| 1 | Python `Decimal` context | `prec=34`; traps `InvalidOperation`, `DivisionByZero`, `Overflow`, **and `FloatOperation`**. The `FloatOperation` trap is the one that matters: it makes `Decimal("1.00") + 1.5` raise, which is how "Money is never float" becomes enforced rather than asserted |
| 2 | Default rounding mode | `ROUND_HALF_UP` set **explicitly** on the context. Python's `Decimal` default is `ROUND_HALF_EVEN` (bankers), so P0.1 §6's half-up rule is silently violated unless overridden. Bankers rounding is used **nowhere** in this system |
| 3 | Quantity rounding | `ROUND_DOWN`. Since quantity ≥ 0 (long-only), this is floor. Never `ROUND_HALF_*` — rounding a size up can breach the 5% cap by construction (P0.1 §6) |
| 4 | Enum representation | All enums are `str`-valued (`class Market(str, Enum)`), never auto-numbered. An integer enum reorders silently on insertion and corrupts every persisted row and every audit hash |
| 5 | Model mutability | Every model is `frozen=True`. Domain objects are values; a state change produces a new object and a new audit event. `Position` and `Portfolio` are computed projections, also frozen |
| 6 | Unknown fields | `extra="forbid"` on every model. A vendor adding a field is a data-quality event to be noticed, not silently dropped |
| 7 | `Money` equality vs ordering across currencies | `==` returns `False` across currencies — it must not raise, or `Money` becomes unusable in sets, as dict keys, and in `assert` comparisons. `<`, `<=`, `>`, `>=`, `+`, `-` **raise** `CurrencyMismatchError`. The asymmetry is deliberate and is explicitly tested |
| 8 | JSON serialisation of `Decimal` | Always to **string**, never to a JSON number. A JSON number is an IEEE-754 double on the far side of every parser, which reintroduces float through the back door |
| 9 | `datetime` normalisation | Accepted only if tz-aware, then converted to exactly `timezone.utc`. A tz-aware value in `America/New_York` is normalised, not rejected — only naive values are rejected `[DEFAULT-5]` |
| 10 | Identifier type | **SUPERSEDED BY P1.4 §0.** Audit event ids are **UUIDv7** (RFC 9562 §5.7), implemented in ~20 lines of stdlib — this row's own reasoning ("a dependency that ten lines of stdlib would cover") argues for *implementing* the format, not avoiding it, and a randomly-sorting event id makes every audit range scan a full scan. `uuid4` remains correct for non-audit surrogate ids. **`seq` remains the authoritative ordering** either way: UUIDv7 is time-ordered but not gapless, and chain verification needs gapless |
| 11 | Bar finality | Every `Bar` carries `is_final`. A bar for a session still in progress is `is_final=False` and **may not feed a signal**. This makes P0.1 §6's "ATR(14) excludes today's partial bar" enforceable at the type level instead of remembered in P2.4 |
| 12 | Staleness | Every market-data model carries `as_of` (event time) and `retrieved_at` (ingest time). `StalenessPolicy` (§6.7) turns "how old is too old" into a declared per-type value; exceeding it is a `DENY`, never a warning |
| 13 | Per-share cost basis | **Never stored.** A lot stores `cost_total: Money` and `quantity`. Per-share basis is derived at 6 dp for reporting only. Storing it would make lot arithmetic non-closed (§3.2) and lose a cent on every partial consumption |
| 14 | `trading_date` type | `datetime.date`, exchange-local, never a timestamp, never UTC-derived. Confirms P0.1 §6 |
| 15 | Percent field naming | Any field ending `_pct` is a fraction in `[0, 1]`, validated at construction. `_bps` fields are integers in basis points. The two never mix in one field |
| 16 | Empty vs missing | `None` means **missing** and is fail-closed at the consumer. Zero means **measured zero**. No model uses `0` as a sentinel for absent, and none uses `None` to mean zero |
| 17 | Instrument-level idempotency of `Fill` | A `Fill` is keyed by `(broker_id, broker_fill_id)`, unique. Brokers re-send fills on reconnect; without this key a replayed fill double-counts a position. Re-receipt of a known key is a no-op, not an update |
| 18 | `Order` price on a market order | `limit_price` is `None` for `MARKET`, and **required** for `LIMIT`. A `LIMIT` order with `limit_price=None` raises rather than defaulting to the last trade |

---

## 3. Numeric foundation — Money, Price, Quantity

This section is the load-bearing one. Every monetary bug in a trading system traces back to a type
that permitted an operation it should not have.

### 3.1 Why three types and not one

`Money`, `Price` and `Quantity` are all decimals, and are **not** interchangeable:

| Type | Dimension | Exponent | Closed under |
|---|---|---|---|
| `Money` | currency amount | exactly −2 for USD and INR | `+`, `-` (same currency), `× int` |
| `Price` | currency per share | exactly −6 | nothing — a price times anything leaves the type |
| `Quantity` | shares | −6, constrained to a multiple of the instrument's `qty_increment` | `+`, `-` |

Multiplying two `Money` values is meaningless; adding a `Price` to a `Money` is meaningless; a
`Quantity` has no currency. Encoding this in three types means the mistakes are `TypeError` at
construction rather than a wrong number in a NAV report.

### 3.2 Money — quantisation and the closure argument

**Definition.** `Money = (amount: Decimal, currency: Currency)` where
`amount.as_tuple().exponent == -minor_units(currency)`. For both `USD` and `INR`,
`minor_units = 2` (P0.1 §6). The constructor quantises **once**, `ROUND_HALF_UP`, and thereafter
the exponent is an invariant checked on every operation.

**Closure.** Let `M_c = { d ∈ Decimal : exponent(d) = −2 }` for a fixed currency `c`. Python's
`Decimal` gives exact exponent arithmetic: addition yields `min(exp_a, exp_b)`, multiplication
yields `exp_a + exp_b`, both exact while the result fits in `prec=34`.

| Operation | Result exponent | In `M_c`? | Consequence |
|---|---|---|---|
| `Money(c) + Money(c)` | `min(−2, −2) = −2` | **yes** | closed; no rounding, no rounding mode needed |
| `Money(c) − Money(c)` | `−2` | **yes** | closed |
| `Money(c) × n`, `n ∈ ℤ` (exponent 0) | `−2 + 0 = −2` | **yes** | closed — this is the share-count case |
| `Money(c) × Price` (exponent −6) | `−8` | **no** | not closed → must `quantise()` explicitly, one rounding at the final step |
| `Money(c) ÷ anything` | undefined exponent | **no** | **operator not provided** `[DEFAULT-4]`; use `allocate()` |
| `Money(c1) ∘ Money(c2)`, `c1 ≠ c2` | — | — | raises `CurrencyMismatchError` — invariant **I1** |

The first three rows are the entire set of operations the system performs on money without an
explicit rounding step. Everything else is forced through `quantise()`, which takes a rounding mode
and is the **only** place `ROUND_HALF_UP` is applied — satisfying P0.1 §6's "final step only,
never at intermediates".

**Notional, worked.** `notional = quantise(price × quantity)`:
`Price` (−6) × `Quantity` (−6) → exponent −12, exact; one `quantise(−2, ROUND_HALF_UP)` produces
`Money`. Fees are already `Money` at −2, so `total_cost = notional + fees` stays closed. There is
exactly one rounding in the path from a quote to a cash movement.

**`allocate(weights) -> list[Money]`** — splitting money without losing a cent. Largest-remainder:
compute each share as `floor(total × w_i / Σw)` in minor units, then distribute the remaining
minor units one at a time to the largest fractional remainders, ties broken by index ascending
(deterministic — a nondeterministic tie-break would make an audit replay diverge). **Postcondition,
asserted in code:** `sum(allocate(w)) == total`, exactly, for every input. This is what makes
partial-lot consumption reproducible.

**Edge cases.**

| Edge case | Behaviour |
|---|---|
| `Money("0.005", USD)` | Quantised at construction to `0.01` (half-up). Not an error — sub-cent inputs come from vendor fee schedules |
| `Money("-1.00", USD)` | **Permitted.** Money is signed: realised P&L, fees and cash adjustments are legitimately negative. Only `Quantity` is sign-constrained |
| `Money("1.00", USD) + Money("1.00", INR)` | `CurrencyMismatchError`. No conversion. Invariant I1 |
| `Money("1.00", USD) == Money("1.00", INR)` | `False`. Does not raise (§2 row 7) |
| `Money("1.00", USD) < Money("1.00", INR)` | `CurrencyMismatchError` |
| `Money(1.5, USD)` — a float literal | Raises via the `FloatOperation` trap. Float never enters |
| `allocate` with total `0.01` across 3 equal weights | `[0.01, 0.00, 0.00]` — the remainder rule assigns the single minor unit to index 0. Sum is exact |
| `allocate` with a zero or negative weight | `ValueError`. A negative weight has no meaning in a proportional split and would silently produce a negative allocation |

### 3.3 Price — precision, tick regime, and the local rejection rule

**Definition.** `Price = (value: Decimal, currency: Currency)`, exponent exactly −6
`[DEFAULT-2]`, `value ≥ 0`. Zero is permitted only on a `CorporateAction` terminal record (a
delisting at zero); an order or a bar with `price = 0` is a validation error.

**Tick size is a date-versioned, per-symbol attribute, never a constant** — ADR-11 req 6, amendment
A-11, rule N10, all `[V]`. Resolution is by lookup into P0.2's frozen `tick_size_regime` table on
`(market, symbol, trading_date)`, with `symbol = '*'` as the market-wide fallback row. Verified
facts carried from P0.2 F-10:

- **US:** `$0.01` for all NMS stocks priced ≥ `$1.00` today. The `$0.005` second increment is
  adopted but exempted until **the first business day of November 2027**, after which it is
  reassigned **per symbol, twice yearly** `[V]` (SEC Rule 612 as amended; release 34-105656).
- **India:** `tick_size` and `lot_size` are fields of Zerodha's instruments dump `[V]`. No value is
  asserted here — it is reference data, loaded, never hard-coded.

**The rule (N10), and it is a rejection rule, not a rounding rule.** An order's `limit_price` must
satisfy `value % tick == 0` exactly, in `Decimal`. A price that is not an exact multiple is
**rejected locally before the order leaves the process** and raises `TickSizeViolation`. It is
never silently rounded to the nearest tick. Rationale: silent rounding moves a price the strategy
chose, in a direction nobody decided, and the audit trail then records a price the decision engine
never produced.

**Edge cases.**

| Edge case | Behaviour |
|---|---|
| Limit price `10.005` when tick is `0.01` | `TickSizeViolation`, order not sent. Not rounded to `10.00` or `10.01` |
| **Fill** price `10.0042` | **Accepted.** Sub-penny price improvement is real at execution even where quoting is at `$0.01`. Tick validation applies to prices **we send**, never to prices the venue reports |
| No `tick_size_regime` row covers `(market, symbol, trading_date)` | `MissingTickRegimeError` → **DENY**. Never defaults to `0.01`. `[CONST-6]`: a missing reference value is fail-closed, and this is precisely the case A-11 exists to prevent |
| Two overlapping regime rows | `AmbiguousTickRegimeError` → DENY. The DDL's primary key prevents duplicates on `effective_from`, but an overlapping `effective_to` is possible and is treated as ambiguous state |
| A US stock priced at `$0.98` (below the `$1.00` regime floor) | The `min_price` column on the regime row means the `≥ $1.00` row does not apply; if no sub-dollar row exists, `MissingTickRegimeError` → DENY. Sub-dollar names are excluded from the universe by ADR-14's `min_price_usd = 5.00` anyway, so this path should be unreachable in production and its reachability is itself a data-quality alarm |
| First business day of November 2027 | Handled by data, not code: new regime rows are loaded with `effective_from` on that date. No code change, no deployment, no constant to find |

### 3.4 Quantity — increments, lots, and the fractional dead end

**Definition.** `Quantity = Decimal`, exponent −6, `≥ 0`, and an exact multiple of the
instrument's `qty_increment`.

**Sign convention.** Quantities are **positive**. ADR-12 is long-only, so no negative quantity
exists in v1 and a negative quantity is a **validation error, not a short** (P0.1 §6). Direction
lives in `OrderSide` and in the sign of a `Lot`'s realised P&L, never in the quantity itself.

**Increments.**

| Market | `qty_increment` | Source |
|---|---|---|
| US | `1` in v1 `[DEFAULT-3]` | Fractional capability exists on the type but is disabled — see below |
| IN | `lot_size` from the Zerodha instruments dump `[V]` | Reference data. No value asserted here |

**The fractional dead end — a cross-spec finding this phase is required to report.** `[CONST]`
sets "limit orders default, market only for emergency exit". P0.2 verified US fractional trading is
available "via `qty` or `notional`, **market/day orders only**" `[V]`. A fractional entry therefore
requires a market order, which `[CONST]` reserves for emergency exit. **The two constraints are
jointly unsatisfiable, so fractional shares are structurally unreachable for entries in v1.** This
is not a defect in either document — it is an interaction neither could see alone. The resolution
adopted is `[DEFAULT-3]`: model the capability, set `qty_increment = 1` for US, and record the
interaction as OPEN QUESTION Q-P1.1-3 rather than silently permitting an order shape `[CONST]`
forbids.

**Edge cases.**

| Edge case | Behaviour |
|---|---|
| Sizing yields `13.7` shares, `qty_increment = 1` | Rounds **down** to `13` (`ROUND_DOWN`, P0.1 §6). Never up — rounding up can breach the 5% cap by construction |
| Sizing yields `0.4` shares, `qty_increment = 1` | Rounds down to `0` → the order is **not placed**. A zero-quantity order is not an error, it is a no-trade outcome, logged. P0.1 §6: a session with no trades is a valid outcome |
| India, `lot_size = 50`, sizing yields `137` | Rounds down to `100` (2 lots). The residual is not carried, netted, or accumulated across sessions |
| `Quantity("-1")` | `NegativeQuantityError` — explicitly *not* interpreted as a short (P0.1 §6) |
| `qty_increment` missing on an instrument | `MissingReferenceDataError` → DENY. Never defaults to `1`, because defaulting to 1 in India would place an order for an illegal quantity |
| Partial fill leaves `0.0000004` unfilled | Below the increment, so the remainder is not re-sent. The order moves to `FILLED` when `remaining < qty_increment`, not only when `remaining == 0` — otherwise an order hangs in `PARTIALLY_FILLED` forever on a rounding dust remainder |

---

## 4. Time, sessions, and calendars

### 4.1 The conversion boundary

**Every timestamp is tz-aware UTC at rest** (P0.1 §6). Exchange-local time exists at exactly two
boundaries and nowhere in between:

| Boundary | Direction | Who does it |
|---|---|---|
| **Ingest** | vendor-local → UTC | The provider adapter, using the vendor's documented timezone. A vendor timestamp whose timezone is undocumented is a data-quality event, not a guess |
| **Presentation and calendar construction** | UTC → exchange-local | The calendar loader and the reporting layer only |

Nothing between those two boundaries holds a local time. `trading_date` is the single exception and
it is a `date`, not a timestamp — it is exchange-local by definition and carries no clock.

A naive `datetime` at any model boundary is **rejected**, never coerced `[DEFAULT-5]`.

### 4.2 The calendar is data, not code

ADR-11 req 2 forbids a hard-coded US holiday list. Accordingly `TradingCalendar` is a **type with
behaviour**, and the sessions it serves are **rows** loaded from P1.2's session table. P1.1 defines
the shape and the semantics; it asserts no holiday, and hard-codes no date.

`ExchangeSession` is one row per `(exchange, trading_date)` and stores **explicit UTC instants**:

| Field | Type | Unit / tz | Null? | Range | Violation means |
|---|---|---|---|---|---|
| `exchange` | `Exchange` | enum | no | enum | Unknown venue → DENY |
| `market` | `Market` | enum | no | `US`\|`IN` | — |
| `trading_date` | `date` | exchange-local | no | — | — |
| `session_type` | `SessionType` | enum | no | `REGULAR`\|`HALF_DAY`\|`SPECIAL` | — |
| `pre_market_open_utc` | `datetime` | UTC | **yes** | < `regular_open_utc` | `None` = venue has no pre-market |
| `regular_open_utc` | `datetime` | UTC | no | < `regular_close_utc` | — |
| `regular_close_utc` | `datetime` | UTC | no | > `regular_open_utc` | — |
| `post_market_close_utc` | `datetime` | UTC | **yes** | > `regular_close_utc` | `None` = venue has no post-market |
| `settlement_date` | `date` | exchange-local | no | ≥ `trading_date` | The date cash from a sale placed today becomes settled |
| `counts_for_sequencing` | `bool` | — | no | — | `False` excludes the session from `trading_date` sequencing and every rolling-window count |

**Storing explicit UTC instants per date is what removes DST from the runtime entirely.** There is
no timezone arithmetic at decision time; the loader resolved it once, from the IANA database, when
the row was written. P0.1 §6's observation that the 09:45 ET window is 13:45 UTC in EDT and 14:45
UTC in EST becomes a property of two rows rather than a branch in the code.

**Rolling windows are counted in completed exchange sessions where `counts_for_sequencing` is
`True`**, never in calendar days (P0.1 §6).

**Edge cases.**

| Edge case | Behaviour |
|---|---|
| US half-day (early close 13:00 ET) | A `HALF_DAY` row with an earlier `regular_close_utc`. The 09:45–10:15 order window is unaffected; ingest and pipeline timers move earlier because they are derived from the row, not from a constant (P0.1 §6) |
| India Muhurat and other special sessions | `session_type = SPECIAL`, `counts_for_sequencing = False`. Excluded from `trading_date` sequencing and from every rolling-window count (P0.1 §6) |
| US DST transition | Two rows with `regular_close_utc` an hour apart. Never crosses midnight UTC, so ADR-15's UTC accounting-date mapping holds year-round |
| India DST | Does not exist. India observes no DST |
| No session row for a date | `MissingSessionError` → **DENY**. Never inferred from the previous day, never assumed open, never assumed closed. A missing calendar row halts the pipeline for that market |
| A date that is a holiday | There is simply **no row**. Absence of a row is the representation of "closed"; there is no `is_holiday` boolean to get out of sync with reality |
| One market open, the other on holiday | ADR-15 §7: the closed pool contributes its **last computed NAV unchanged**, flagged `STALE_HOLIDAY` in the snapshot — distinguishable in the audit trail from a missing value, which fails closed |
| `settlement_date` on a session before a holiday run | Computed by the loader from the settlement cycle and the calendar, so a holiday shifts it. **US T+1 and India T+1 are both `ASSUMPTION [VERIFY-P0.2]`** carried from P0.1 Chain D — this spec does not assert a settlement cycle, it stores whatever the loader resolved |

### 4.3 The two day boundaries

Both exist, and conflating them is a bug class ADR-15 §7 names explicitly.

| Boundary | Definition | Used for |
|---|---|---|
| `trading_date` | The exchange-local session date, from that exchange's own calendar | Per-pool daily loss, per-pool counters, universe membership, signals |
| `utc_accounting_date` | The UTC calendar date on which the session closes | Consolidated daily loss, consolidated NAV, the consolidated drawdown counter |

The consolidated daily-loss counter is evaluated **after the later of the two closes** on a given
UTC date — in practice after the US close (ADR-15 §7).

---

## 5. Symbol identity

### 5.1 `instrument_id` is not a ticker, and never derived from one

`instrument_id` is a `uuid4` assigned at first sighting and **immutable forever**. It survives
ticker changes, exchange transfers, mergers and delisting. It is never derived from a symbol,
because deriving identity from a mutable attribute is the same bug as using a phone number as a
primary key.

`Instrument` carries a nullable `issuer_id` — also a `uuid4` — which groups listings of the same
issuer across venues. `[DEFAULT-1]` makes `instrument_id` **per listing venue**: NSE `RELIANCE` and
BSE `RELIANCE` are two instruments sharing one `issuer_id`, because they have different tick
regimes, different liquidity and different order books. An ADR on NYSE and its underlying on NSE
are likewise two instruments with one `issuer_id` — and the ADR is `InstrumentType.ADR`, which
ADR-05 denies in v1 regardless.

### 5.2 Ticker changes are bitemporal rows, not updates

`SymbolMapping` is `(instrument_id, market, exchange, symbol, valid_from, valid_to)` where
`valid_from`/`valid_to` are exchange-local dates, `valid_from` inclusive and `valid_to`
**exclusive**, `NULL` meaning open-ended.

A ticker change **closes one row and opens another**. It never updates a symbol in place, because
a backtest resolving a symbol as of a past decision date must see the symbol that was in force on
that date. Resolution is always `symbol_at(instrument_id, trading_date)` or its inverse
`instrument_at(market, symbol, trading_date)` — never a bare `symbol` column lookup.

External identifiers — `isin`, `cusip`, `figi` — are carried on the same bitemporal footing, for
the same reason: an ISIN can change on reincorporation or redomiciliation.

**Edge cases.**

| Edge case | Behaviour |
|---|---|
| A symbol is reused by a different company after a delisting | Correct by construction: the old mapping's `valid_to` closed, the new mapping's `valid_from` opens, and the two rows carry different `instrument_id`s. `instrument_at(market, symbol, date)` returns the right one for the date. This is the single most common survivorship/identity bug and the bitemporal key eliminates it |
| Two open mappings for one `(market, symbol)` | `AmbiguousSymbolError` → DENY. Never "pick the newest" |
| No mapping covers the date | `UnknownSymbolError` → DENY. Never fall back to a bare symbol match |
| A vendor sends a symbol we have never seen | Not auto-created. It is a data-quality event; the instrument is created by the reference-data loader, which is the only writer of `Instrument` rows |
| FIGI share-class vs composite | Both stored, separately named (`figi`, `figi_composite`). Collapsing them loses the distinction between a listing and a share class |

### 5.3 Corporate actions, mergers and delisting

`CorporateActionType` is a closed enum: `SPLIT`, `REVERSE_SPLIT`, `CASH_DIVIDEND`,
`STOCK_DIVIDEND`, `TICKER_CHANGE`, `EXCHANGE_TRANSFER`, `MERGER`, `ACQUISITION`, `SPINOFF`,
`RIGHTS_ISSUE`, `DELISTING`. An unrecognised vendor action code maps to no enum member and raises
`UnknownCorporateActionError` → DENY. Deny-by-default applies to corporate actions exactly as
ADR-05 applies it to instrument types: an action we cannot interpret must not be silently ignored,
because ignoring a split misprices every subsequent bar.

**Mergers and successors.** `SuccessorLink` is
`(predecessor_instrument_id, successor_instrument_id, share_ratio, cash_per_share, effective_date)`.
A held position in the predecessor converts on `effective_date`: existing lots are closed and new
lots opened against the successor, carrying the **original cost basis** and the **original
acquisition date** — because the tax lot's holding period does not reset on a share-for-share
exchange `ASSUMPTION [VERIFY-P0.2]`. Any cash component is a realised event on the predecessor lot.

**Delisting.** `InstrumentStatus` moves to `DELISTED` with a `delisted_on` date and a
`final_price`. **The instrument row is never deleted** — invariant I7, and P0.2 M-2 verified `[V]`
that the market-data vendor retains delisted price history "as it occurred on that date"
(`massive.com/knowledge-base/article/what-does-massive-do-with-delisted-tickers`), so the
never-delete rule is vendor-supportable rather than aspirational.

**Edge cases.**

| Edge case | Behaviour |
|---|---|
| A split announced but not yet effective | Stored with its `effective_date`; bars before that date are unadjusted. Rule N9 `[V]`: every aggregate request sends `adjusted=false` and adjustment is computed on read from the splits and dividends tables. Adjustment is never taken from the vendor |
| A merger where we hold the predecessor and the successor is a **banned** `InstrumentType` | The conversion still happens — we own what we own — but the resulting position is flagged and the exit hierarchy is invoked. The allowlist governs what we may **buy**, not what a corporate action may hand us |
| A delisting while a position is open | An exit-hierarchy event, not a price update (P0.1 §6, halted-stock rule applied by analogy). The position cannot be marked to a live price and its contribution to NAV uses `final_price`, flagged |
| A split effective on a date with no session | Impossible to apply unambiguously → `CorporateActionCalendarError` → DENY, escalated. Never applied to the nearest session by guess |
| A dividend with an ex-date before our first ingested bar | Ignored for adjustment purposes and recorded. Adjusting a bar we do not hold history for produces a phantom price |

---

## 6. Market data types

All five carry `as_of` (event time, UTC), `retrieved_at` (ingest time, UTC), `source`
(`ProviderId`, from P0.2's `enum.ProviderId`) and `market`. Provenance is not optional: rule N7
requires that a disagreement between two sources be a data-quality event rather than a silent
tiebreak, and that is only expressible if every row knows where it came from.

### 6.1 `Bar`

OHLCV for one instrument over one interval. `interval` is an enum (`DAILY`, `MIN_5`) — ADR-13 fixes
daily bars for all signals and 5-minute bars only for instruments currently held, so the enum has
exactly the two members the architecture permits.

Invariants, each raising `BarIntegrityError` on violation: `low ≤ open ≤ high`,
`low ≤ close ≤ high`, `low ≤ high`, `volume ≥ 0`, all four prices > 0, all four in the same
currency. `is_final` is `False` for a session in progress; **a non-final bar may not feed a
signal**, which is how P0.1 §6's "ATR(14) excludes today's partial bar" is enforced by type rather
than by memory.

**Edge cases.** A zero-volume bar is valid (an illiquid name that did not trade) and is **not**
imputed. A bar with `volume = 0` and four equal prices is a venue's placeholder for "no trade" and
is stored as received — never interpolated, never forward-filled `[CONST-6]`. A duplicate
`(instrument_id, interval, as_of)` from a replayed stream is idempotent on primary key and does not
overwrite.

### 6.2 `Quote`

Best bid/ask with sizes. Invariants: `bid ≤ ask` (a crossed quote raises `CrossedQuoteError` →
DENY, because a crossed book usually means a stale or mixed-venue feed), sizes ≥ 0, both prices in
the same currency, `venue` recorded.

**Rule N6 `[V]` binds here: screening must never run on single-venue (IEX) prices.** `Quote`
therefore carries a `is_consolidated: bool`. A non-consolidated quote is usable for monitoring and
never for screening; the screening path asserts `is_consolidated is True` and raises otherwise.

### 6.3 `Trade`

A single executed print on the tape — **not** our fill. Named `Trade` because the prompt names it;
§13's glossary pins the distinction, since "trade" colloquially means both a tape print and a
round-turn position, and conflating them is how a slippage model ends up measuring the wrong thing.

### 6.4 `FundamentalsSnapshot`

Point-in-time fundamentals with three distinct dates, and the distinction is the whole point:

| Date | Meaning |
|---|---|
| `period_end` | The issuer's fiscal period end |
| `filed_at` | When the filing was made |
| `disseminated_at` | When it became publicly available |

**Rule N1 `[V]`: features are lagged to the dissemination date, never the filing date.** Using
`filed_at` is look-ahead bias — the filing existed before anyone could act on it. P0.1 §6 adds that
fundamentals use the issuer's fiscal periods mapped to a calendar `as_of` at ingest, while ADR-07's
retrain cadence uses **calendar** quarters; the two are different clocks and the model carries both.

**Rule N7 `[V]`: where FMP and EDGAR disagree materially, EDGAR is authoritative** and the
discrepancy is recorded as a data-quality event. The snapshot therefore carries `source` and the
reconciliation writes a second row rather than editing the first.

### 6.5 `NewsItem` — and rule N16, which shapes the type

**M-5 resolved `[V]` on 2026-08-26: the vendor news archive is _not_ point-in-time.** Both
candidate vendors expose a post-publication revision timestamp and neither offers any version,
revision or as-of-content parameter, so a historical query returns the article **as currently
stored** (`massive.com/docs/rest/partners/benzinga/news`; `docs.alpaca.markets/reference/news-3`).

Rule N16 is therefore load-bearing on this type: **our store must be the point-in-time record**.

- `NewsItem` is keyed `(vendor_id, revision_seq)`. `revision_seq` starts at 1 on first receipt.
- `headline` and `body_sanitised` are **snapshotted at first receipt**.
- The vendor revision timestamp (`vendor_updated_at`) is persisted.
- On any later change, ingest **writes a new revision row**. It never overwrites.
- A backtest reads the **first-seen** revision as of the decision date, never the current one.

`first_seen_at` is the field a backtest joins on, and it is `retrieved_at` of `revision_seq = 1`.

**`body_sanitised` is the only body field the type exposes, and it is tagged `UNTRUSTED_DATA`.**
Rule N14 `[V]`: all vendor news, filing and social text passes through the `[CONST-4]` sanitiser
before any LLM sees it; Alpaca's news `content` "might contain HTML", which is exactly the shape an
injection arrives in. The raw body is stored in P1.2's ingest table and is **not reachable from the
domain model**, so there is no attribute an LLM prompt builder could accidentally read. The type
also carries `sanitiser_version` so a sanitiser bug is retroactively identifiable.

**The corollary is the load-bearing half of N16:** historical news backfill is structurally unsound
for any content-derived feature — only forward-collected news is point-in-time. This is why rule N4
excludes news from walk-forward optimisation, and P5.1/P5.2 inherit that exclusion.

### 6.6 `CorporateAction`

Covered at §5.3. It is market data by delivery and reference data by consequence, and it is the one
data type whose loss is silently wrong rather than loudly missing: a missed split does not raise,
it just misprices every subsequent bar. Hence deny-by-default on unrecognised action codes.

### 6.7 `StalenessPolicy` and the gap rule

`StalenessPolicy = (data_type, max_age_seconds, on_breach)` where `on_breach` is always `DENY` in
v1. `[CONST-6]` admits no other value, and the field exists only so the policy is explicit and
auditable rather than implied.

**Rule N5 `[V]`: a WebSocket disconnect gap is _assumed lost_.** P0.2 retrieved two Alpaca
streaming pages in full; **no reconnect, replay, sequence-number or gap-recovery mechanism is
documented**, and the pages do document a 1-connection limit and that slow clients may be
disconnected when their buffer fills. The domain consequence: a stream gap is not a recoverable
hole to be stitched. The affected window is **reconciled from REST before resuming**, and until it
is, every affected instrument is stale and therefore `DENY`. No model in this file has a field that
could express "probably fine" about a gap.

---

## 7. The analysis chain — Candidate → Score → Signal → Thesis → Decision

This is the path from a universe of 1,500 names to at most 4 new entries per session (ADR-14). Each
stage narrows, and each stage records what produced it.

### 7.1 `Candidate`

An instrument that passed the Tier-1 deterministic screen for one `trading_date`. Carries the
screen's `rank`, the `filters_passed` tuple, and `universe_version` — the point-in-time universe
snapshot id, because ADR-14 makes universe membership an immutable versioned artifact and a
backtest must select membership as of the decision date.

### 7.2 `Score`

A deterministic model output. `kind ∈ {FUNDAMENTAL, TECHNICAL, COMPOSITE}`, `value` a `Decimal`
constrained to `[0, 1]`, plus `model_id`, `model_version` and `feature_vector_hash`.

`feature_vector_hash` is not decoration: ADR-07 requires reproducibility and ADR-08 requires
promotion accounting, and neither is possible if the exact input vector to a score cannot be
identified after the fact. P0.1 §6 already requires `model_id`/`prompt_version` on every score,
thesis and decision.

**A `Score` is never produced by an LLM.** `[CONST-2]` — an LLM does not size, and a score feeds
sizing. LLM output is a `Thesis`, which is a different type with different rules.

### 7.3 `Signal`

`direction ∈ {BUY, HOLD, EXIT}`. **There is no `SELL_SHORT`** — ADR-12 is long-only and the enum
does not contain a member the system may not act on. `EXIT` is distinct from `SELL` because an exit
is the closing of a held position, while "sell" in the research summary is used for both that and
for shorting; §13 pins the meaning.

Carries `horizon_sessions`, validated against ADR-13's band `[3, 40]` with a hard maximum of 120. A
signal with a horizon outside the band raises — the holding period is ADR-13 and ADR-13 is marked
irreversible.

### 7.4 `Thesis` and `InvalidationCondition`

`Thesis` is the **only** LLM-derived model in this file, and it is shaped by what an LLM is not
permitted to do.

- It carries `bull_case`, `bear_case` and a **non-empty tuple of `InvalidationCondition`** —
  `[RS §13]` requires structured theses with invalidation conditions for every position, and an
  empty tuple raises. A thesis that cannot be falsified is not a thesis.
- It carries `model_id`, `prompt_version`, `sanitiser_version` and `input_content_hashes`, so the
  exact untrusted inputs that produced it are identifiable.
- **It has no quantity field, no price field, no weight field and no limit field.** This is the
  type-level expression of `[CONST-2]`: an LLM never sizes a position. The fields do not exist, so
  there is no code path that could read one.
- `llm.may_receive_portfolio_state = false` is **immutable** (P0.1 §10.2, `[DEFAULT-7]` of P0.1).
  Correspondingly the `Thesis` construction path takes a `Candidate` and sanitised facts, never a
  `Portfolio`, `NAV`, `Account` or `Position`. The blast radius of a successful prompt injection is
  capped at one candidate's thesis.

`InvalidationCondition` is a **deterministic, machine-evaluable predicate** —
`kind ∈ {PRICE_BELOW, ATR_STOP, TIME_STOP, FUNDAMENTAL_BREACH, NEWS_EVENT}` with a typed threshold.
It is not free text. An invalidation condition that only a human can evaluate cannot fire
automatically, and a thesis-deterioration detector that needs a human is not a detector.

### 7.5 `Decision` — where `[CONST-2]` becomes structural

A `Decision` is the final, actionable output for one instrument on one `trading_date`. Its
construction requires:

| Field | Constraint |
|---|---|
| `risk_verdict_id` | **Required.** Non-null, always |
| `risk_decision` | **Must be `ALLOW`.** Constructing a `Decision` carrying `DENY` raises `RiskDenyIsFinal` |
| `audit_event_id` | **Required** — the audit event written *before* the decision takes effect, `[CONST-5]` |
| `strategy_version`, `model_id` | Required — invariant I6 carries these to the order |
| `thesis_id` | **Optional.** A decision may exist with no thesis at all |

That last row is the point. The deterministic path produces decisions without any LLM involvement;
the LLM path can only **annotate** a decision that the deterministic path and the risk engine have
already permitted. There is no constructor that turns a `Thesis` into a `Decision`
`[DEFAULT-8]`.

**Edge cases.** A `Decision` whose `risk_verdict_id` refers to a verdict that has since been
superseded is still valid for audit purposes but is **not executable** — executability is checked
at order-placement time against a fresh verdict, because ADR-14 freezes the order list at pipeline
time and a stale verdict is an ambiguous state. A `Decision` with `action = NO_TRADE` is valid and
is recorded; P0.1 §6 makes a zero-candidate session a feature, not an error.

---

## 8. Risk and sizing types

### 8.1 `PositionSizeRequest`

The input to sizing: `instrument_id`, `pool_id`, `signal_id`, `entry_price`, `stop_price`,
`nav_snapshot_id`, `settled_cash`, `regime`. Sizing is deterministic and is **not** an LLM output
`[CONST-2]`.

The stop is `entry − 2.5 × ATR(14)` at entry (`[CONST]`), where ATR(14) uses 14 **completed** bars
and excludes today's partial bar (P0.1 §6, enforced by `Bar.is_final` at §6.1). A
`PositionSizeRequest` whose `stop_price ≥ entry_price` raises `InvalidStopError` — a stop at or
above entry is either a sign error or a data error, and sizing off it produces an unbounded
position.

### 8.2 `RiskVerdict` — frozen, binary, and non-overridable

`RiskDecision ∈ {ALLOW, DENY}`. Binary, deliberately. A three-valued verdict with a "reduce" member
would put the risk engine in the sizing business; instead a `DENY` carries an **informational**
`max_permissible_quantity` so the sizer may re-propose once, and the re-proposal is evaluated from
scratch.

`RiskVerdict` is `frozen=True`, carries `binding_constraint` (which limit bound, by name),
`evaluated_at`, `nav_snapshot_id`, and the full tuple of `limits_evaluated` so the verdict is
reproducible from the audit trail.

**There is no override.** Invariant I2 and ADR-09's final row: overriding a single risk DENY has no
approver and no code path. Concretely, in this module:

- `RiskVerdict` has no mutating method and no non-frozen variant.
- No function accepts a `force`, `override`, `bypass` or `ignore_risk` parameter.
- `Decision` raises `RiskDenyIsFinal` if handed a `DENY` verdict (§7.5).
- `hitl.risk_deny_override_permitted = false` is immutable config (P0.1 §10.2).

ADR-09 states why: if a human can override one DENY, `[CONST-1]` is decorative, because the AI need
only persuade the human. The permitted action is to change the **limit** — an audited policy change
with its own approval and 24-hour SLA — and let the engine re-evaluate deterministically.

**Limit bounds are inclusive** (P0.1 §6): `position_pct <= 0.05` **passes** at exactly `0.05`.
Breach is strictly greater. Every limit comparison in this system uses `<=`, and the test suite
asserts the boundary value passes.

---

## 9. Portfolio, accounting and NAV

### 9.1 `Lot` — the unit of tax truth

Lot-level cost basis with a wash-sale adjustment field is **mandatory from day one** (ADR-13 Chain
E), because a 15-day median hold against a weekly-reconstituted universe means the system will
routinely re-enter a name it exited inside the 30-day wash-sale window.

| Field | Type | Unit | Null? | Notes |
|---|---|---|---|---|
| `lot_id` | `UUID` | — | no | — |
| `instrument_id` | `UUID` | — | no | — |
| `pool_id` | `PoolId` | — | no | Segregated per ADR-15 |
| `opened_on` | `date` | exchange-local | no | Tax holding period starts here |
| `quantity_opened` | `Quantity` | shares | no | > 0 |
| `quantity_remaining` | `Quantity` | shares | no | `0 ≤ remaining ≤ opened` |
| `cost_total` | `Money` | pool currency | no | **Total for `quantity_opened`, never per-share** (§2 row 13). It is NOT decremented as the lot is consumed — `remaining_cost()` derives the live figure. **X2 F-1** |
| `fees_total` | `Money` | pool currency | no | Allocated at open |
| `opening_fill_id` | `UUID` | — | no | Provenance to the exact fill |
| `audit_event_id` | `UUID` | — | no | `[CONST-5]`, added by **X2 F-10** |
| `wash_sale_disallowed_loss` | `Money \| None` | USD | **yes** | **`None` for `Market.IN`, enforced** `[DEFAULT-6]` |
| `wash_sale_adjusted_basis` | `Money \| None` | USD | **yes** | Same enforcement |

**Cost-basis method is FIFO** (P0.1 §6, `ASSUMPTION [VERIFY-P0.2]`), chosen because it is the
default assumption in both jurisdictions' reporting and because it interacts predictably with
wash-sale adjustment. `CostBasisMethod` is nonetheless an enum with `FIFO`, `LIFO` and `AVERAGE`
defined, because a method change is a reporting decision that must not require a schema migration.

**Partial consumption allocates against `quantity_opened`, never `quantity_remaining`**, and
`consumed_cost` telescopes `basis(remaining) - basis(remaining - q)`. Telescoping is what makes a
consumption path exactly additive: independent allocations over `[30, 70]` then `[20, 80]` can
place a minor unit differently than one allocation over `[30, 20, 50]`, and the cents would not
sum back to `cost_total`. **This is X2 finding F-1**, the one BLOCKER in the review.

**Edge cases.** A lot fully consumed has `quantity_remaining = 0` and is **retained forever** — it
is the tax record. A wash-sale adjustment discovered after a lot closed writes a new adjustment row
rather than editing the closed lot. A `Market.IN` lot with a non-null wash-sale field raises
`WashSaleNotApplicableError` at construction.

### 9.2 `Position` and `PositionState`

A `Position` is the **projection over open lots** for one `(instrument_id, pool_id)`. It is derived,
frozen, and never the authority: **the broker is the system of record for positions and cash**
(ADR-10). On disagreement the broker wins for quantity and the discrepancy is escalated — never
silently corrected in one direction.

`UNRECONCILED` is the state that expresses that rule. Per ADR-10 §2: while **any** position is
`UNRECONCILED`, the risk engine treats it as full-size risk and **denies all new entries across the
entire pool**. Note the scope — pool-wide, not instrument-wide. One unreconciled position halts
entries for the whole pool.

### 9.3 `NAV` and the dual-pool computation

ADR-15 is implemented here in full.

- **Base currency is USD.** `fx.base_currency = USD`, `fx.system_may_convert = false` — immutable.
- **Two segregated pools.** `PoolId` per `Market`. No cross-margining, no cross-pool netting. USD
  cash cannot fund an INR trade.
- **Position limits are per-pool, in local currency.** `position ≤ 5%` means 5% of **that pool's**
  NAV. A consolidated-NAV position limit would authorise an India position larger than the entire
  India pool.
- **Loss and drawdown limits are enforced BOTH per-pool AND consolidated; the stricter binds.** A
  per-pool breach halts that pool; a consolidated breach trips the **global** kill switch.

`NAV` therefore comes in two shapes, and the type distinguishes them: `PoolNAV` (local currency,
`trading_date`) and `ConsolidatedNAV` (USD, `utc_accounting_date`, with the `fx_rate_id` used and a
`translation_effect` line reported separately from trading P&L — ADR-15 §6, so a good year in India
is neither flattered nor hidden by a rupee move).

**Missing FX rate is fail-closed, and it blocks both pools.** Invariant I10: no consolidated NAV is
computed, consolidated limits cannot be evaluated, and therefore **no new entries are permitted in
either pool** until the rate is available. Never carried forward, never interpolated, never
defaulted. The FX rate itself is stored at 6 dp, immutable once written, and **never re-fetched or
corrected in place** — a silently revised rate rewrites NAV history.

**While India is unfunded, `NAV_IN = 0` and every consolidated computation runs anyway** (ADR-15),
exercising the code path daily. An FX layer first exercised on the day it matters is an FX layer
that fails on the day it matters.

### 9.4 `Account`

Carries `account_type: AccountType` (`CASH` in v1, ADR-12), and **both** settlement counters, so a
future switch to margin is a config change rather than a re-derivation (ADR-13 Chain D):

| Counter | Applies when | Rule |
|---|---|---|
| `settled_cash` | `AccountType.CASH` (v1) | New entries are sized against **settled cash only**. A buy that would consume unsettled proceeds is **DENIED** |
| `day_trades_5d` | `AccountType.MARGIN` (future) | While equity < $25,000, **deny all new entries** when `day_trades_5d >= 3` — because any new position could stop out the same session and become the fourth day trade |

Both fields exist on the model in v1. `day_trades_5d` is computed and stored even in a cash account,
where it is not enforced, so the counter is proven correct before it ever becomes binding.

**Kill-switch liquidation is exempt from both counters** (ADR-13 Chain D). A PDT flag or a
good-faith violation is a 90-day inconvenience; an uncontrolled drawdown is permanent. The exemption
is explicit in the model as `KillSwitchExempt`, is audited, and is alerted on.

**Correction R-1 carried from P0.1 §0.4:** `[RS §16]` names PDT as the binding US constraint. Given
ADR-12's cash account it is **not** — PDT is a margin-account rule `ASSUMPTION [VERIFY-P0.2]`, and
the binding constraint is settled funds. `[RS §16]` is wrong on this point and this spec follows
P0.1, not the research summary.

---

## 10. Control-plane types

### 10.1 `Regime`

`RegimeLabel ∈ {BULL, BEAR, SIDEWAYS, VOLATILE, UNKNOWN}` `[DEFAULT-7]`, vocabulary from `[RS §13]`.
Carries `confidence` (a `Decimal` in `[0, 1]`), `model_id`, `computed_at` and `trading_date`.

`UNKNOWN` is a real value with a real behaviour: it is the fail-closed regime. A regime the
classifier cannot determine does not become `SIDEWAYS` by default; it becomes `UNKNOWN`, and P2.9
treats `UNKNOWN` as no-new-entries. §13 pins `confidence` to exactly one meaning, because the
research summary uses it for three different things.

### 10.2 `KillSwitch`

`KillSwitchState ∈ {ARMED, POOL_HALTED, TRIPPED}` with `KillSwitchScope ∈ {GLOBAL, POOL}`.
Transition table at §11.3. The boot rule — restore `TRIPPED`, unconditionally — is at §11.3 and is
invariant I3.

### 10.3 `AuditEvent` — the envelope

P1.1 owns the chained envelope; P1.4 owns the event catalogue `[DEFAULT-9]`.

| Field | Type | Notes |
|---|---|---|
| `event_id` | `UUID` | Surrogate |
| `seq` | `int` | **Monotonic, gapless, per chain.** Ordering comes from here, never from a uuid or a timestamp |
| `prev_hash` | `str` (hex) | SHA-256 of the previous event's `payload_hash`; genesis is 64 zeros |
| `payload_hash` | `str` (hex) | SHA-256 over the canonical serialisation |
| `event_type` | `str` | P1.4 owns the catalogue |
| `event_class` | `AuditEventClass` | `ACTION`/`EVALUATION`/`NAV`/`RISK`/`KILL_SWITCH`/`APPROVAL`/`SYSTEM`. RULE-B4 splits durability on it; P1.2 uses it as the compression `segmentby` and in the invariant-I4 replay index. **X2 F-5** |
| `is_paper` / `is_backtest` | `bool` | Stamped from `RunContext` so rule N11 is checkable on the event itself. Mutually exclusive. **X2 F-5** |
| `occurred_at` / `recorded_at` | `datetime` UTC | Event time and write time, distinct |
| `actor` | `str` | System component, or an `ApproverRole` for a human action |
| `run_id` | `UUID` | Links to `RunContext` |
| `payload` | `Mapping` | Canonically serialised; `Decimal` → string |

**`[CONST-5]`: the audit write happens _before_ the action takes effect. If the audit write fails,
the action does not happen.** In this module that means every constructor for an effectful type
(`Decision`, `Order`, `Fill`, `KillSwitch` transition) requires a non-null `audit_event_id`. The
field is not nullable and there is no default.

**Invariant I4:** risk counters are **replayed from the audit trail, never recomputed from portfolio
state**. ADR-10 §3 gives the reason concretely: recomputation resets peak NAV to the present value
and silently un-trips the drawdown condition — the kill switch would forget why it fired.

**Audit-chain continuity is a hard stop** (ADR-10 §5): a broken or forked chain means no trading
resumes and the break is investigated as a potential integrity incident.

### 10.4 `RunContext`

Every pipeline invocation carries one. `run_type ∈ {INGEST, PIPELINE, ORDER, MONITOR, RECONCILE,
BACKTEST, PAPER}`, plus `run_id`, `market`, `trading_date`, `started_at`,
**`finished_at` (nullable — `None` means still in flight; **X2 F-5**)**, `code_version` (git sha),
`config_hash`, `strategy_version`, `model_id`.

Two boolean fields carry more weight than they look:

- **`is_paper`** — rule N11 `[V]`: paper-trading results are **plumbing evidence only**; no
  slippage, fill-quality, fee or edge conclusion may cite paper data. Stamping `is_paper` on the
  run context, and thence on every audit event, is what makes that rule mechanically checkable
  rather than a discipline. P5.3's cost model filters on it.
- **`is_backtest`** — invariant I9: LLM-derived features never enter walk-forward optimisation.

`config_hash` and `code_version` exist because ADR-07 requires reproducibility and ADR-08 requires
promotion accounting; a result that cannot name the code and config that produced it cannot be
promoted.

---

## 11. State machines

Every transition table below lists legal transitions, illegal transitions, and what raises. All
illegal transitions raise; none is silently ignored, because a silently ignored transition leaves
the object in a state the audit trail does not explain.

### 11.1 `OrderState`

States: `PENDING_NEW`, `NEW`, `PARTIALLY_FILLED`, `FILLED`, `PENDING_CANCEL`, `CANCELED`,
`PENDING_REPLACE`, `REPLACED`, `REJECTED`, `EXPIRED`, `UNKNOWN`.

Terminal: `FILLED`, `CANCELED`, `REJECTED`, `EXPIRED`, `REPLACED`.

| From \ To | PENDING_NEW | NEW | PARTIALLY_FILLED | FILLED | PENDING_CANCEL | CANCELED | PENDING_REPLACE | REPLACED | REJECTED | EXPIRED | UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **PENDING_NEW** | — | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ |
| **NEW** | ✗ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| **PARTIALLY_FILLED** | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| **PENDING_CANCEL** | ✗ | ✗ | ✓ | ✓ | — | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ |
| **PENDING_REPLACE** | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✗ | ✓ | ✓ |
| **UNKNOWN** | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | ✓ | — |
| **FILLED / CANCELED / REJECTED / EXPIRED / REPLACED** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Notes on the non-obvious cells, each of which is a real broker behaviour:**

- `PENDING_NEW → FILLED` is legal: a marketable order can fill before the acknowledgement arrives.
- `PENDING_CANCEL → PARTIALLY_FILLED` and `→ FILLED` are legal: a cancel races a fill and loses.
  Modelling the cancel as authoritative is how systems double-sell.
- `PARTIALLY_FILLED → PARTIALLY_FILLED` is legal — successive partials.
- **Any state → `UNKNOWN` is legal** `[DEFAULT-10]`: the broker became unreachable or answered
  ambiguously. From `UNKNOWN` the only exits are the states a reconciliation can prove.
- **No terminal state has any outgoing transition.** A fill arriving on a `CANCELED` order raises
  `IllegalOrderTransition` and is a reconciliation incident, not an update.

**What raises.** `IllegalOrderTransition(from_state, to_state, order_id)`. The order is **not**
mutated; the exception carries the attempted transition and the caller writes a reconciliation
event. Fail-closed: while any order for an instrument is in `UNKNOWN`, no new order for that
instrument may be created.

**Edge cases.** A broker that reports a state we do not model maps to `UNKNOWN`, never to the
nearest-looking member. A fill whose cumulative quantity exceeds the order quantity raises
`OverfillError` → the position is marked `UNRECONCILED` and the pool denies new entries.

### 11.2 `PositionState`

States: `PENDING_OPEN`, `OPEN`, `PENDING_CLOSE`, `CLOSED`, `UNRECONCILED`.

| From \ To | PENDING_OPEN | OPEN | PENDING_CLOSE | CLOSED | UNRECONCILED |
|---|---|---|---|---|---|
| **PENDING_OPEN** | — | ✓ | ✗ | ✓ | ✓ |
| **OPEN** | ✗ | — | ✓ | ✗ | ✓ |
| **PENDING_CLOSE** | ✗ | ✓ | — | ✓ | ✓ |
| **CLOSED** | ✗ | ✗ | ✗ | — | ✓ |
| **UNRECONCILED** | ✗ | ✓ | ✗ | ✓ | — |

- `PENDING_OPEN → CLOSED` is legal: the opening order was cancelled or rejected with zero fills.
- `OPEN → CLOSED` is **illegal directly** — a position closes through `PENDING_CLOSE`, because
  something must have been sent to the broker. A position that appears closed without an exit order
  is a reconciliation event, hence `→ UNRECONCILED`.
- `PENDING_CLOSE → OPEN` is legal: the exit order was cancelled and the position remains.
- `CLOSED → UNRECONCILED` is legal and important: a late fill or a broker restatement on a closed
  position must be able to reopen the question.
- **`UNRECONCILED → OPEN` or `→ CLOSED` requires a completed reconciliation** carrying the broker's
  authoritative quantity (ADR-10: the broker is the system of record).

**What raises.** `IllegalPositionTransition`. While any position in a pool is `UNRECONCILED`, the
risk engine denies all new entries **across that entire pool** (ADR-10 §2).

### 11.3 `KillSwitchState`

States: `ARMED`, `POOL_HALTED`, `TRIPPED`.

| From \ To | ARMED | POOL_HALTED | TRIPPED |
|---|---|---|---|
| **ARMED** | — | ✓ automatic | ✓ automatic |
| **POOL_HALTED** | ✓ **human only** | — | ✓ automatic |
| **TRIPPED** | ✓ **human only** | ✗ | — |

**The asymmetry is the entire design.** Every transition *toward* halt is automatic. Every
transition *away* from halt requires a human — ADR-09 row 1, Owner authority, **no SLA, no
auto-expiry, no auto-re-enable**. An unattended trip means the system stays flat and halted until a
human acts, and that is the correct trade for an autonomous system trading its owner's own capital.

- `POOL_HALTED → TRIPPED` is escalation: a per-pool breach (ADR-15 §4) followed by a consolidated
  breach.
- `TRIPPED → POOL_HALTED` is **illegal**. There is no partial de-escalation; a global trip is
  cleared to `ARMED` by a human, or not at all.
- **Boot is not a transition.** On every start the state is set to `TRIPPED` unconditionally,
  regardless of the state before the incident — `killswitch.restore_state_on_boot = TRIPPED`,
  immutable, invariant I3, ADR-10 §4.

**What raises.** `IllegalKillSwitchTransition`. There is **no `force_arm()`, no `reset()` and no
constructor that yields `ARMED` without an `approval_id`** — the re-enable path requires an
`ApprovalGrant` id whose nonce is single-use, so a blanket or standing approval is structurally
impossible (ADR-09).

**Kill-switch liquidation is exempt from `settled_cash` and `day_trades_5d`** (§9.4), and that
exemption is itself audited and alerted.

### 11.4 Why `RiskVerdict` has no state machine

Because it has no lifecycle. A verdict is computed once, frozen, and written to the audit trail. It
is never amended, never re-opened, never superseded in place. A changed input produces a **new**
verdict with a new id. This is what makes invariant I2 checkable: there is no mutation path to
audit, because there is no mutation.

---

## 12. Error taxonomy and fail-closed behaviour

Every error below is a subclass of `DomainError`. `[CONST-6]` admits exactly one default:
**missing data, stale data, an exception, or an ambiguous state → DENY.** No error in this table
resolves to a synthesised, imputed, interpolated or defaulted market value.

| Exception | Raised when | Fail-closed behaviour |
|---|---|---|
| `CurrencyMismatchError` | Arithmetic or ordering across currencies | Operation aborts. Invariant I1 — no conversion, ever |
| `MoneyPrecisionError` | A `Money` amount whose exponent is not the currency's minor units | Construction aborts |
| `FloatContaminationError` | A `float` reaches a `Decimal` operation (via the `FloatOperation` trap) | Construction aborts |
| `TickSizeViolation` | Order limit price is not an exact multiple of the effective tick | **Order not sent.** Never rounded — rule N10 |
| `MissingTickRegimeError` | No `tick_size_regime` row covers `(market, symbol, trading_date)` | DENY. Never defaults to `0.01` |
| `AmbiguousTickRegimeError` | Overlapping tick regime rows | DENY |
| `NegativeQuantityError` | Quantity < 0 | Aborts. Explicitly not a short (ADR-12) |
| `QuantityIncrementError` | Quantity is not a multiple of `qty_increment` | Aborts. Never rounded up |
| `MissingReferenceDataError` | `qty_increment`, `lot_size` or another required attribute absent | DENY |
| `NaiveDatetimeError` | A naive `datetime` at a model boundary | Aborts `[DEFAULT-5]` |
| `MissingSessionError` | No calendar row for `(exchange, trading_date)` | DENY for that market. Never assumes open or closed |
| `UnknownSymbolError` | No symbol mapping covers the date | DENY |
| `AmbiguousSymbolError` | Two open mappings for one `(market, symbol)` | DENY. Never "pick the newest" |
| `UnknownCorporateActionError` | Vendor action code maps to no enum member | DENY. Never ignored |
| `CorporateActionCalendarError` | Action effective on a date with no session | DENY, escalated |
| `BarIntegrityError` | OHLC ordering violated, negative volume, or mixed currency | Row rejected, data-quality event |
| `CrossedQuoteError` | `bid > ask` | DENY — usually a stale or mixed-venue feed |
| `StaleDataError` | `as_of` older than the type's `StalenessPolicy` | DENY |
| `MissingFxRateError` | No FX rate for the accounting date | **DENY in _both_ pools.** Invariant I10 |
| `InvalidStopError` | `stop_price >= entry_price` | Sizing aborts |
| `RiskDenyIsFinal` | A `Decision` is constructed from a `DENY` verdict | Aborts. Invariant I2 — there is no override path |
| `LlmOutputNotPermitted` | LLM-derived data reaches a type that may carry only deterministic output | Aborts. **X2 F-8**: previously raised `RiskDenyIsFinal`, which records a verdict that was never reached |
| `IllegalOrderTransition` | Transition not in §11.1 | Order unmutated; reconciliation event |
| `OverfillError` | Cumulative fills exceed order quantity | Position → `UNRECONCILED`; pool denies new entries |
| `IllegalPositionTransition` | Transition not in §11.2 | Position → `UNRECONCILED` |
| `IllegalKillSwitchTransition` | Transition not in §11.3 | Aborts. No `force_arm()` exists |
| `WashSaleNotApplicableError` | Wash-sale field populated on a `Market.IN` lot | Aborts `[DEFAULT-6]` |
| `AuditWriteRequiredError` | An effectful type constructed without `audit_event_id` | Aborts. `[CONST-5]` — if the audit write fails, the action does not happen |
| `UnsanitisedContentError` | Raw vendor text reaches an LLM-bound path | Aborts. Rule N14, `[CONST-4]` |

---

## 13. Glossary — one meaning per term

The research summary uses several of these words for more than one thing. Each is pinned here to
exactly one meaning; every downstream phase uses the pinned meaning.

| Term | **The one meaning** | What it does *not* mean here |
|---|---|---|
| **Exposure** | The absolute market value of positions, as a fraction of the **relevant** NAV — per-pool for position and sector limits, consolidated for gross/net. Always a fraction, never a percentage number | Not notional traded; not a count of positions; not a risk-adjusted figure |
| **Gross exposure** | Σ \|position value\| / equity. Under ADR-12 (long-only, cash) **gross ≡ net ≤ 1.0×** | Not the `[CONST]` 2× ceiling — P0.1 §C-2 keeps that in config as an unreachable upper bound while `gross ≤ 1.0×` binds. The engine enforces `min(constitutional_ceiling, account_type_ceiling)` |
| **Drawdown** | Peak-to-trough decline in NAV, measured from the **running peak restored from the audit trail** (never recomputed — invariant I4). Evaluated per-pool against that pool's peak **and** consolidated against consolidated peak | Not intra-session excursion; not per-position loss; not the ≤15% figure `[RS §12]` uses, which P0.1 §C-3 rejected as dangerous against a 10% kill switch |
| **Confidence** | The classifier's probability output for a `Regime`, a `Decimal` in `[0, 1]` | Not the LLM's self-reported certainty in a `Thesis` (that is `Thesis.stated_confidence`, explicitly untrusted and never used for sizing); not a score |
| **Score** | A deterministic model output in `[0, 1]` on a `Candidate`, with `kind ∈ {FUNDAMENTAL, TECHNICAL, COMPOSITE}` | Never an LLM output. LLM output is a `Thesis` |
| **Candidate** | An instrument that passed the Tier-1 deterministic screen for one `trading_date` | Not a position, not an order, not something the system has decided to buy |
| **Signal** | A directional recommendation with a horizon: `BUY`, `HOLD`, `EXIT` | Not a decision — a signal has passed no risk gate. There is no `SELL_SHORT` (ADR-12) |
| **Decision** | The final actionable output for one instrument on one `trading_date`, carrying an `ALLOW` `RiskVerdict` | Never exists with a `DENY` verdict. Never produced by an LLM |
| **Position** | The projection over open lots for one `(instrument_id, pool_id)`. Derived; the **broker is the system of record** | Not a lot; not an order; not our database's opinion when it disagrees with the broker |
| **Lot** | One tax-accounting acquisition unit, FIFO-consumed, carrying `cost_total` and holding period | Not a position; not a fill (a fill may create one lot, a lot may span no more than one fill) |
| **Trade** | A single executed print on the public tape | **Not** our fill (that is `Fill`), and **not** a round-turn (that is a closed lot). `[RS]` uses "trade" for all three |
| **NAV** | `PoolNAV` in local currency on a `trading_date`, or `ConsolidatedNAV` in USD on a `utc_accounting_date`. The two are never interchanged | Never a single global number without a stated scope. A bare "NAV" in any spec is a defect |
| **Equity** | Account equity as reported by the broker, per pool | Not NAV — they differ by unsettled activity and pending fees |
| **Settled cash** | Cash available without consuming unsettled proceeds. **The binding US constraint** (ADR-13 Chain D, correction R-1) | Not total cash; not buying power |
| **Session** | One `ExchangeSession` row where `counts_for_sequencing = True` | Not a calendar day; excludes Muhurat and other special sessions |
| **Regime** | `BULL`/`BEAR`/`SIDEWAYS`/`VOLATILE`/`UNKNOWN` on a `trading_date`, with confidence | `UNKNOWN` is fail-closed, not a synonym for `SIDEWAYS` |
| **Kill switch** | Infrastructure-level halt, independent of the AI path, automatic **and** manual, requiring a human to re-enable | Not a risk DENY (which is per-order and has no override); not a circuit breaker on one instrument |

---

## 14. Module layout

```
src/domain/
  __init__.py      re-exports the public vocabulary
  errors.py        DomainError and every exception in §12
  money.py         Currency, Money, Price, Quantity, the Decimal context
  time.py          SessionType, ExchangeSession, TradingCalendar
  identity.py      Market, Exchange, InstrumentType, InstrumentStatus, Instrument,
                   SymbolMapping, SuccessorLink, CorporateAction
  marketdata.py    Bar, Quote, Trade, FundamentalsSnapshot, NewsItem, StalenessPolicy
  analysis.py      Candidate, Score, Signal, Thesis, InvalidationCondition, Decision
  risk.py          PositionSizeRequest, RiskVerdict, RiskDecision
  execution.py     OrderSide, OrderType, TimeInForce, OrderState, Order, Fill
  portfolio.py     Lot, Position, PositionState, Portfolio, NAV, Account, PoolId
  control.py       Regime, KillSwitch, AuditEvent, RunContext
```

`models.py` is the single flat module the prompt asks for inline; the package layout above is how
it is split when it lands in the repository, with `models.py` re-exporting everything so the
import surface is one name. **No module in `src/domain` imports from outside the standard library
and Pydantic v2.** The domain is the one layer with no I/O, no database, no broker and no clock —
`datetime.now()` never appears in it. Time enters as a parameter, which is what makes every rule
here testable without a fixture.

---

## 15. X2 — CODE REVIEW record (2026-08-27)

**Verdict: FIX-THEN-SHIP.** Ten findings, all fixed, each covered by a regression test that fails
against v0.1.

### 15.1 Reviewer independence — declared, not glossed

The pack requires X2 to run in a **separate conversation** because "the author never reviews
itself." This review was run by the author of v0.1, at the Owner's explicit direction. That is a
real conflict of interest and it bounds what this verdict is worth: these are the findings the
author's own blind spots did not hide. **An independent X2 is still owed**, recorded as
`Q-P1.1-8`. It is not a formality — F-1 survived a 43-test suite that passed 43/43, because every
one of those tests happened to exercise a full, unconsumed lot.

### 15.2 Findings

| # | Sev | Where | Concrete failure | Fix |
|---|---|---|---|---|
| **F-1** | **BLOCKER** | `Lot.consumed_cost` | Basis was allocated against `quantity_remaining` instead of `quantity_opened`, so the **full original basis was re-divided across a shrinking denominator**. A 100-share lot at $1,000.00 with 50 already sold reported `consumed_cost(25) = $500.00` instead of `$250.00`, and remaining basis `$1,000.00` instead of `$500.00`. Every consumption after the first over-stated basis → wrong realised P&L, wrong wash-sale adjustment (ADR-13 Chain E), wrong tax export | Allocate against `quantity_opened` in `_basis_for()`; `consumed_cost` telescopes `basis(remaining) − basis(remaining − q)`, exactly additive over any consumption path. Added `remaining_cost()`; `Position.cost_basis()` now uses it |
| **F-2** | **HIGH** | Decimal context | `decimal.setcontext` is **thread-local**. A worker thread that never called `install_domain_decimal_context()` ran at `prec=28`, `ROUND_HALF_EVEN`, `FloatOperation` **untrapped** — measured directly, not inferred. In a threaded server that silently violates P0.1 §6's half-up rule at every half-way value | Every rounding and division site pins the context via `_domain_context()` / `_quantise()`. The process-wide install is retained as a convenience and is no longer load-bearing |
| **F-3** | **HIGH** | `verify_audit_chain` | Required `events[i].seq == i`, so verifying any slice not starting at genesis raised a **false integrity incident**. ADR-10 §5 verifies "across the outage window" — a slice. A false hard stop halts trading and sends an operator hunting a tamper that never happened | Contiguity checked relative to the first event; `require_genesis=True` preserves whole-chain semantics |
| **F-4** | **HIGH** | `Decision`, `Order` | A US decision accepted an **INR limit price**. Invariant I1 forbids conversion, but nothing tied a price's currency to its pool; the mismatch would surface deep inside the risk engine, or not at all if the price only ever reached the broker adapter | Validator ties `limit_price`/`stop_price` currency to `pool_id.currency` |
| **F-5** | **HIGH** | `AuditEvent`, `RunContext` | P1.2's schema requires `event_class` (RULE-B4's durability split, the compression `segmentby`, the invariant-I4 replay index), `is_paper`/`is_backtest` (rule N11), and `run_context.finished_at`. **P1.1 defined none of them** — RULE-B4 had no field to key on | Added `AuditEventClass` enum and the four fields, with a paper-XOR-backtest check |
| **F-9** | **HIGH** | `Order` | The stated invariant is "unique `client_order_id` **per account**", and P1.2 enforces `UNIQUE (account_id, client_order_id)` — but `Order` carried **no account**, so the domain could not express the scope its own uniqueness rule is defined over | Added `account_id` |
| **F-6** | MEDIUM | `TradingCalendar` | Rebuilt a dict and re-sorted the entire calendar on **every call**: 0.89 ms against a 10-year calendar ≈ 1.3 s per session across a 1,500-name universe, for a value that cannot change on a frozen model | Sorted once at construction; `cached_property` indexes; `bisect` range queries. Re-measured under 0.05 s per session |
| **F-10** | MEDIUM | `Lot`, `Thesis`, `PoolNAV`, `ConsolidatedNAV` | `[CONST-5]` requires the audit event written before the action, and P1.2's DDL carries `audit_event_id` on all four — **P1.1 omitted the field**, so four effectful records could not name their audit event | Added `audit_event_id` |
| **F-7** | MEDIUM | `NewsItem` | `body_sanitised` was unbounded. It is untrusted vendor text that rule N14 already treats as hostile; a 5,000,000-character body was accepted | Bounded to 200,000 chars; `headline` to 1,000 |
| **F-8** | LOW | `Signal` | An LLM-derived signal raised **`RiskDenyIsFinal`** — a different condition entirely. Recording a risk verdict where none exists misleads anyone reading the audit trail | New `LlmOutputNotPermitted` error |

### 15.3 Reviewed and found clean

**Constitution (X2 item 2):** no path lets an LLM size or reach a broker — `Decision` still cannot
be constructed from a `DENY`, `Thesis` still has no size field, and no function anywhere accepts
`force`/`override`/`bypass`/`ignore_risk`, asserted by introspection over the whole module.
**Concurrency (item 4):** frozen values, no shared mutable state, no locks, no async; F-2 was the
only thread-sensitive surface and it is closed. **Security (item 7):** no secrets, no
deserialisation, no injection surface; F-7 was the one unbounded external input.
**Simplicity (item 9):** `StalenessAction` has one member and `Trade.tape_sequence` has no
consumer yet. Both retained deliberately — the first makes a `[CONST-6]` policy explicit and
auditable rather than implied, the second is vendor data P5.3 needs — and both recorded here so a
later reviewer need not re-derive the judgement.

### 15.4 Verification

| Suite | Result |
|---|---|
| Base invariant harness — 43 assertions, unchanged from v0.1 except for newly required fields | **43/43 PASS** |
| X2 regression suite — one test per finding, each failing against v0.1 | **20/20 PASS** |
| P1.1 ↔ P1.2 contract conformance — every P1.2 column mapped to a model field or an explicit, reasoned waiver | **21/21 pairs ALIGNED** |

The contract check is new, and it is the mechanism that would have caught F-5, F-9 and F-10
automatically rather than by hand. It also surfaced one **P1.2** observation, waived here and
raised against P1.2's own X2: `news_item.news_id` is an unused surrogate — the primary key is
`(vendor_id, revision_seq, first_seen_at)` and `news_instrument` references that, not `news_id`.

### 15.5 Status after X2

**P1.1 remains `DRAFT` at v0.2.** X2 freezes nothing: the pack's `X3 — MERGE` is the step that
"sets the status of merged specs to FROZEN", and Stage 1 is incomplete — P1.3 and P1.4 have not
run. Nothing in this review authorises freezing P1.1 or `src/domain/models.py`.

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Three distinct numeric types — `Money`, `Price`, `Quantity` — not one `Decimal` | Encodes dimensional analysis in the type system: adding a price to a money becomes a `TypeError` at construction rather than a wrong number in a NAV report | Yes, but expensive after Stage 2 | **High** — a collapsed type reintroduces the entire class of unit-confusion bugs across every downstream phase |
| 2 | `Money` exponent is an enforced invariant; division is not provided; `allocate()` is | Division is not closed over a fixed-exponent decimal (§3.2). Largest-remainder allocation is exact by construction and deterministic under replay | Yes | **High** — permitting division produces cent drift that compounds through every partial-lot consumption and corrupts the tax record |
| 3 | Per-share cost basis is **never stored**; lots store `cost_total` | Storing per-share basis forces a division and loses a cent on every partial consumption (§2 row 13) | Yes | **Medium** — a wrong tax lot is a reporting error and a wash-sale error |
| 4 | `Price` is 6 dp; tick validation applies only to prices **we send** | Matches the frozen `tick_size_regime` DDL. Venues legitimately fill sub-penny; rejecting those fills would break reconciliation on every price-improved execution | Yes | **Medium** — at lower precision every improved fill fails reconciliation |
| 5 | Tick violation **rejects**, never rounds — rule N10 | Silent rounding moves a price nobody chose and the audit trail then records a price the decision engine never produced | No — it is rule N10, `[V]` | **High** — a rounded price is an unauditable order |
| 6 | Calendar sessions store **explicit UTC instants** per `trading_date` | Removes DST arithmetic from the runtime entirely; the loader resolved it once from the IANA database. ADR-11 req 2 forbids a hard-coded holiday list | Yes | **High** — runtime tz arithmetic is the classic source of off-by-one-session bugs in both markets |
| 7 | Absence of a session row **is** the representation of "closed" | Removes an `is_holiday` boolean that can disagree with reality | Yes | **Low** |
| 8 | `instrument_id` is a `uuid4` per **listing venue**, never derived from a ticker; symbol mappings are bitemporal | A reused ticker after a delisting resolves correctly by construction — the single most common identity/survivorship bug | Partly `[DEFAULT-1]` | **High** — identity errors silently corrupt every backtest |
| 9 | `Decision` **cannot be constructed** without an `ALLOW` `RiskVerdict` | Makes `[CONST-2]` structural rather than conventional. An LLM `Thesis` has no type-level path to becoming a `Decision` | No — it is `[CONST-1]`/`[CONST-2]` | **Critical** — this is the invariant the whole constitution rests on |
| 10 | `Thesis` has **no** quantity, price, weight or limit field | An LLM never sizes. The fields do not exist, so no code path can read one | No | **Critical** |
| 11 | `RiskVerdict` is binary `ALLOW`/`DENY`, frozen, with `max_permissible_quantity` as information only | A three-valued verdict would put the risk engine into the sizing business | No — ADR-09 | **Critical** |
| 12 | `UNKNOWN` is an `OrderState`, not an exception | An exception that is caught and retried loses the fact that an order may be live at the broker | Yes `[DEFAULT-10]` | **High** — the alternative is duplicate orders |
| 13 | Terminal order states have **no** outgoing transitions | A fill on a `CANCELED` order is a reconciliation incident, not an update | No | **High** |
| 14 | One `UNRECONCILED` position denies new entries **pool-wide**, not instrument-wide | ADR-10 §2 states it at pool scope | No — ADR-10 | **High** |
| 15 | `Bar.is_final` gates signal eligibility | Makes "ATR(14) excludes today's partial bar" enforceable by type instead of by memory | Yes | **Medium** — a partial bar in an indicator is look-ahead bias |
| 16 | `NewsItem` is keyed `(vendor_id, revision_seq)`; first-seen content is snapshotted | Rule N16 `[V]` — the vendor archive is not point-in-time, so our store must be | No — rule N16 | **High** — without it every news-derived backtest reads revised content |
| 17 | `body_sanitised` is the only body field the domain exposes; raw text is unreachable | Rule N14 `[V]` — no attribute exists that a prompt builder could accidentally read | No — `[CONST-4]` | **Critical** — this is the injection boundary |
| 18 | `RunContext.is_paper` and `.is_backtest` stamp every audit event | Makes rule N11 (paper is plumbing evidence only) and invariant I9 mechanically checkable rather than a discipline | Yes | **Medium** — otherwise a paper-derived slippage number can reach a go-live gate |
| 19 | Both `settled_cash` and `day_trades_5d` exist in v1; `day_trades_5d` computed but unenforced | ADR-13 Chain D — a future margin switch becomes a config change, and the counter is proven correct before it binds | Yes | **Low** |
| 20 | `Money.__eq__` returns `False` across currencies; ordering raises | Equality must not raise or `Money` is unusable in sets and dict keys; ordering across currencies is always a bug | Yes | **Low** |
| 21 | Explicit `Decimal` context with `FloatOperation` trapped | Turns "never float" from a rule into a runtime failure | Yes | **High** — float contamination is silent and unrecoverable once persisted |
| 22 | All enums are `str`-valued | An integer enum reorders on insertion and corrupts every persisted row and audit hash | No | **High** |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | `[DEFAULT-1]` `instrument_id` is per listing venue, not per issuer | Neither P0.1 nor P0.2 states the identity grain; ADR-15's segregated pools imply but do not state it | Owner ratification; or the first dual-listed India name at the ADR-11 activation gate | Cross-venue aggregation needs an `issuer_id` rollup — a reporting join, not a migration, since `issuer_id` already exists |
| 2 | `[DEFAULT-2]` `Price` at 6 dp is sufficient | No vendor documents a maximum price precision | Inspect the widest observed decimal in a month of `Trade` prints during P2.1 | If a vendor emits >6 dp, prices truncate silently; the check is one query and belongs in P2.2's quality gate |
| 3 | `[DEFAULT-3]` Fractional shares are unreachable in v1 | Derived from `[CONST]` limit-orders-default against P0.2's verified "market/day only" fractional constraint | Alpaca order-type documentation for fractional; re-read at P3.1 | If fractional works with limit orders, `qty_increment` becomes a per-instrument value and sizing gains resolution at small NAV. No schema change — the field already exists |
| 4 | `[DEFAULT-4]` Largest-remainder allocation with ascending-index tie-break | No upstream spec names an allocation rule | Assert `sum(allocate(w)) == total` over a property-based test in P5.4 | A different tie-break changes cent placement; deterministic replay would diverge between two implementations |
| 5 | `[DEFAULT-5]` Naive datetimes are rejected, not coerced | `[CONST-6]` implies it; no spec states it | Owner ratification | Ingest adapters for a vendor that emits naive timestamps need an explicit tz declaration — which is the correct outcome |
| 6 | `[DEFAULT-6]` India has no wash-sale rule, so the field must be `NULL` for `IN` | ADR-13 Chain E states it, labelled `ASSUMPTION [VERIFY-P0.2]` there | A qualified Indian tax professional (P0.1 open item Q8) | If India has an analogous rule, the validator inverts and the India tax export needs the field |
| 7 | `[DEFAULT-7]` `RegimeLabel` is the four `[RS §13]` labels plus `UNKNOWN` | P2.6 owns the classifier but the vocabulary must exist before P2.6 | P2.6 design | Adding a member is additive and cheap; the closed enum is what matters, not the exact membership |
| 8 | `[DEFAULT-8]` `[CONST-2]` is enforced structurally at the `Decision` constructor | The constitution states the rule, not the mechanism | Red-team template X4 — attempt to construct a `Decision` from a `Thesis` | If a bypass exists, `[CONST-1]` is decorative. This is the single highest-value test in the suite |
| 9 | `[DEFAULT-9]` P1.1 owns the audit envelope, P1.4 the catalogue | The prompt lists `AuditEvent` in P1.1 while P1.4 is the audit phase | P1.4 reconciles at its own freeze | If P1.4 wants the envelope too, the two must merge — a rename, not a redesign |
| 10 | `[DEFAULT-10]` `UNKNOWN` is a persisted order state | No upstream spec models broker unreachability | P3.1 broker adapter design | Without it, an ambiguous broker response becomes a retry and then a duplicate order |
| 11 | US and India equity settlement are both T+1 | Carried from P0.1 ADR-13 Chain D, labelled `ASSUMPTION [VERIFY-P0.2]` there and **not** resolved by P0.2 | Broker settlement documentation; NSE settlement calendar | `settlement_date` is computed by the calendar loader from a configured cycle, so a different cycle is a config change. But `settled_cash` sizing would be wrong in the interim — this is the highest-impact unverified assumption in this spec |
| 12 | A merger preserves the tax holding period and cost basis on a share-for-share exchange | Standard treatment, but no upstream spec states it | A qualified tax professional, both jurisdictions | Lot `opened_on` would reset on conversion, changing STCG/LTCG classification in India and wash-sale windows in the US |
| 13 | FIFO is the correct cost-basis method | P0.1 §6, labelled `ASSUMPTION [VERIFY-P0.2]` there | A qualified tax professional | `CostBasisMethod` is already an enum with `LIFO` and `AVERAGE`, so the change is a config value plus a re-run of the lot consumer |

## OPEN QUESTIONS

Items already carried in STAGE-0-FREEZE §6.2/§6.3 keep their existing ids so the register does not
fork. New items are numbered `Q-P1.1-n`.

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| **Q-P1.1-1** | Is US equity settlement T+1, and what exactly constitutes a good-faith violation in a cash account? | Broker documentation | Alpaca account documentation, "settlement" and "cash account" pages; SEC Regulation T / FINRA 4210 on free-riding | **P2.9** — `settled_cash` sizing is unimplementable without it. Also P1.2's session table |
| **Q-P1.1-2** | What is the NSE equity settlement cycle and its holiday-shift rule? | NSE / Zerodha documentation | NSE settlement calendar; Zerodha console documentation on payout timing | P2.9, and P1.2's `settlement_date` computation. Not blocking while India is unfunded |
| **Q-P1.1-3** | Can a US fractional order be a **limit** order, or is it market/day only? | Alpaca documentation | Alpaca "fractional trading" page — supported order types and TIF | **P3.1/P3.2.** If market/day only, `[CONST]`'s limit-order default makes fractional unreachable and `qty_increment = 1` is correct permanently |
| **Q-P1.1-4** | Does India have a wash-sale-equivalent (bed-and-breakfasting) restriction on listed equity? | Qualified Indian tax professional | Income Tax Act provisions on set-off and carry-forward for listed equity | P6.3 tax export. Folds into existing item **Q8** |
| **Q-P1.1-5** | Does a share-for-share merger preserve the tax holding period in both jurisdictions? | Qualified tax professional, both jurisdictions | US: IRC §368 reorganisation treatment. India: capital-gains treatment of amalgamation | P6.3. Not blocking Stage 1 |
| **Q-P1.1-6** | What is the maximum decimal precision any selected vendor emits for a trade price? | Measurement during P2.1 | One month of `Trade` prints; `max(scale(price))` | P2.2 quality gate. Confirms or refutes `[DEFAULT-2]` |
| **Q-P1.1-7** | Is `Money` at 2 dp correct for INR in all broker-reported contexts, or does any Zerodha field carry paise beyond 2 dp? | Zerodha documentation | Kite Connect order and holdings response schemas | P3.1. If a field carries more precision, the INR minor-units constant needs a per-field exception |
| **Q-P1.1-8** | An **independent** X2 review, by someone who did not author this spec | A separate conversation, per the pack's rule 4 | Re-run `X2 — CODE REVIEW` against v0.2 with the author excluded | **Not blocking P1.3.** §15.1 is explicit that the 2026-08-27 X2 was author-run, and F-1 survived a suite passing 43/43 because the author's tests shared the author's blind spot. Highest-value outstanding item on P1.1 |
| **Q8** *(carried)* | India tax schedule — STCG/LTCG rates, STT, stamp duty, set-off rules | Qualified professional | Income Tax Act / Finance Act 2024 | P6.3 |
| **M-9** *(carried)* | Broker detail gaps — including idempotency-key semantics for Zerodha and Upstox | Broker documentation | Kite Connect and Upstox order-placement references | P3.2. Rule N12 already prescribes client-side dedupe in the interim |
| **M-1** *(carried)* | Alpaca idempotency-key **charset** | Alpaca documentation | Alpaca order submission reference, `client_order_id` constraints | P3.2. Constrains a field this spec types as `str` |

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| `Market` | enum | `US` \| `IN` | every phase, every table |
| `Exchange` | enum | `NYSE` \| `NASDAQ` \| `NSE` \| `BSE` | P1.2, P2.1, P3.1 |
| `Currency` | enum | `USD` \| `INR`, each with `minor_units = 2` | P1.2, P2.9, P3.1 |
| `Money` | type | `(amount: Decimal[exp=-2], currency: Currency)`; `+`/`-`/`×int` closed; no `/`; `allocate()`; cross-currency raises | every phase |
| `Price` | type | `(value: Decimal[exp=-6], currency: Currency)`; tick-validated on send only | P2.x, P3.x, P5.x |
| `Quantity` | type | `Decimal[exp=-6]`, `≥ 0`, multiple of `qty_increment` | P2.8, P2.9, P3.2 |
| `InstrumentType` | enum, **deny-by-default** | `COMMON_STOCK` allowed; `ETF` read-only; `ADR`,`ETN`,`CEF`,`SPAC`,`UNIT`,`WARRANT`,`RIGHT`,`PREFERRED`,`FUTURE`,`OPTION` denied | P2.2, P2.9 |
| `InstrumentStatus` | enum | `ACTIVE` \| `HALTED` \| `SUSPENDED` \| `DELISTED` | P2.2, P2.3, P3.3 |
| `AccountType` | enum | `CASH` (v1) \| `MARGIN` (future) | P2.9 |
| `PoolId` | enum | one per `Market`; segregated, no cross-margining | P1.2, P2.9 |
| `Instrument` | model | `instrument_id`, `issuer_id?`, `market`, `exchange`, `instrument_type`, `status`, `tick_source`, `qty_increment`, `lot_size?`, `supports_fractional` | every phase |
| `SymbolMapping` | model | bitemporal `(instrument_id, market, exchange, symbol, valid_from, valid_to)`; `valid_to` exclusive | P1.2, P2.1, P5.1 |
| `SuccessorLink` | model | `(predecessor_id, successor_id, share_ratio, cash_per_share, effective_date)` | P2.1, P3.3 |
| `CorporateAction` | model | closed `CorporateActionType`; unknown code raises | P2.1, P2.4, P5.1 |
| `ExchangeSession` | model | explicit UTC instants + `settlement_date` + `counts_for_sequencing` | P1.2, P2.1, P2.9, P3.2 |
| `TradingCalendar` | type | `session(exchange, date)`, `sessions_between()`, `nth_prior_session()`, `settlement_date_for()` — data-driven, no hard-coded holidays | P2.x, P3.x, P5.x |
| `Bar` | model | OHLCV + `interval ∈ {DAILY, MIN_5}` + `is_final` | P2.1, P2.4, P5.1 |
| `Quote` | model | bid/ask/sizes + `is_consolidated` (rule N6) | P2.2, P3.3 |
| `Trade` | model | tape print — **not** our `Fill` | P5.3 |
| `FundamentalsSnapshot` | model | `period_end`, `filed_at`, `disseminated_at` (rule N1 lags to dissemination) | P2.1, P2.5 |
| `NewsItem` | model | `(vendor_id, revision_seq)`, first-seen snapshot, `body_sanitised` only (rules N16, N14) | P2.1, P4.1, P4.3 |
| `StalenessPolicy` | model | `(data_type, max_age_seconds, on_breach=DENY)` | P2.2, P2.9 |
| `Candidate` | model | + `rank`, `filters_passed`, `universe_version` | P2.3, P2.5, P4.2 |
| `Score` | model | `kind`, `value ∈ [0,1]`, `model_id`, `feature_vector_hash` — never LLM-produced | P2.5, P2.7 |
| `Signal` | model | `direction ∈ {BUY, HOLD, EXIT}` — no `SELL_SHORT`; `horizon_sessions ∈ [3,40]` | P2.7, P3.4 |
| `Thesis` | model | bull/bear + non-empty invalidation tuple + `sanitiser_version`; **no size fields** | P4.3, P4.4, P3.4 |
| `InvalidationCondition` | model | machine-evaluable predicate, typed threshold | P3.3, P3.4 |
| `Decision` | model | **requires `ALLOW` `RiskVerdict` + `audit_event_id`**; `thesis_id` optional | P2.7, P3.2 |
| `PositionSizeRequest` | model | `entry_price`, `stop_price`, `settled_cash`, `nav_snapshot_id`, `regime` | P2.8, P2.9 |
| `RiskVerdict` | model | frozen; `ALLOW`\|`DENY`; `binding_constraint`; `max_permissible_quantity` informational | P2.9, P1.4 |
| `Order` | model | + `account_id` (**X2 F-9**, the scope of the per-account `client_order_id` uniqueness rule), `strategy_version`, `model_id`, broker idempotency key (invariant I6), SEBI strategy id; price currency tied to the pool (**X2 F-4**) | P3.2 |
| `OrderState` | enum + transition table | §11.1; terminals have no outgoing transitions; `UNKNOWN` is fail-closed | P3.2, P3.3 |
| `Fill` | model | unique on `(broker_id, broker_fill_id)`; re-receipt is a no-op | P3.2, P3.3 |
| `Lot` | model | `cost_total` for `quantity_opened` (never per-share, never decremented); `remaining_cost()` / telescoping `consumed_cost()` (**X2 F-1**); FIFO; wash-sale fields US-only; `audit_event_id` (**X2 F-10**) | P3.3, P6.3, P5.1 |
| `Position` / `PositionState` | model + transition table | §11.2; `UNRECONCILED` denies new entries pool-wide | P2.9, P3.3 |
| `Portfolio` | model | projection over positions for one pool | P2.8, P2.9 |
| `PoolNAV` / `ConsolidatedNAV` | model | local-currency/`trading_date` vs USD/`utc_accounting_date` + `fx_rate_id` + `translation_effect` | P2.9, P6.1 |
| `Account` | model | `account_type`, `settled_cash`, `day_trades_5d`, `equity` | P2.9, P3.2 |
| `Regime` | model | `RegimeLabel` + `confidence ∈ [0,1]`; `UNKNOWN` fail-closed | P2.6, P2.7, P2.9 |
| `KillSwitch` / `KillSwitchState` | model + transition table | §11.3; boot = `TRIPPED`; re-arm requires `approval_id`; no `force_arm()` | P2.10, P6.1 |
| `AuditEvent` | model | `seq`, `prev_hash`, `payload_hash` chain + `event_class`, `is_paper`, `is_backtest` (**X2 F-5**); envelope only, catalogue in P1.4 | P1.4, every effectful phase |
| `AuditEventClass` | enum | `ACTION`\|`EVALUATION`\|`NAV`\|`RISK`\|`KILL_SWITCH`\|`APPROVAL`\|`SYSTEM` — RULE-B4's durability split | P1.2, P1.4 |
| `RunContext` | model | `run_type`, `code_version`, `config_hash`, `is_paper`, `is_backtest` | every phase |
| `DomainError` hierarchy | exceptions | §12 — 28 named exceptions, each with its fail-closed behaviour | every phase |

---

**END OF SPEC-P1.1-DOMAIN v0.1**

CONTINUE: src/domain/models.py
