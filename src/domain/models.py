"""SPEC-P1.1-DOMAIN v0.3 — the complete typed vocabulary of the trading system.

Everything downstream imports from here. This module has NO I/O, NO database, NO broker
and NO clock: `datetime.now()` never appears in it. Time enters as a parameter, which is
what makes every rule here testable without a fixture.

Constitutional and frozen-spec references appear inline as:
  [CONST-n]  Block A Constitution invariant n
  In         SPEC-P0.1-DECISIONS v0.3 invariant I1..I10 (P0.1 section 10.3)
  Nn         SPEC-P0.2-PROVIDERS v0.5 correctness rule N1..N16 (P0.2 section 10.5)
  ADR-nn     SPEC-P0.1-DECISIONS v0.3 architecture decision record
  [DEFAULT-n] Block C default applied by SPEC-P1.1-DOMAIN section 1

Python 3.12+, Pydantic v2. No dependency beyond the standard library and Pydantic.
"""

from __future__ import annotations

import decimal
from bisect import bisect_left, bisect_right
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from functools import cached_property
from typing import Annotated, Any, Final
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
    model_validator,
)

# =============================================================================
# 1. ERRORS  (SPEC-P1.1-DOMAIN section 12)
# =============================================================================
#
# DomainError deliberately subclasses Exception, NOT ValueError.
#
# Pydantic v2 converts ValueError and AssertionError raised inside a validator into a
# ValidationError, which would erase the specific exception type. Every exception below
# carries its own fail-closed semantics ([CONST-6]), and the caller must be able to
# distinguish TickSizeViolation from MissingTickRegimeError. Subclassing Exception makes
# Pydantic propagate them unwrapped.


class DomainError(Exception):
    """Base of every domain error. Each subclass carries a fail-closed behaviour."""


# --- numeric -----------------------------------------------------------------
class CurrencyMismatchError(DomainError):
    """Arithmetic or ordering across currencies. Invariant I1 - no conversion, ever."""


class MoneyPrecisionError(DomainError):
    """A Money amount whose exponent is not the currency's minor units."""


class FloatContaminationError(DomainError):
    """A float reached a Decimal boundary. Money and Price are never float."""


class TickSizeViolation(DomainError):
    """Order limit price is not an exact multiple of the effective tick. Rule N10.

    The order is NOT sent and the price is NOT rounded.
    """


class MissingTickRegimeError(DomainError):
    """No tick_size_regime row covers (market, symbol, trading_date) -> DENY."""


class AmbiguousTickRegimeError(DomainError):
    """Overlapping tick regime rows -> DENY."""


class NegativeQuantityError(DomainError):
    """Quantity < 0. Long-only (ADR-12): this is a validation error, not a short."""


class QuantityIncrementError(DomainError):
    """Quantity is not a multiple of the instrument's qty_increment. Never rounded up."""


class MissingReferenceDataError(DomainError):
    """A required instrument attribute is absent -> DENY. Never defaulted."""


# --- time and calendar --------------------------------------------------------
class NaiveDatetimeError(DomainError):
    """A naive datetime at a model boundary [DEFAULT-5]. Rejected, never coerced."""


class MissingSessionError(DomainError):
    """No calendar row for (exchange, trading_date) -> DENY for that market."""


# --- identity -----------------------------------------------------------------
class UnknownSymbolError(DomainError):
    """No symbol mapping covers the date -> DENY."""


class AmbiguousSymbolError(DomainError):
    """Two open mappings for one (market, symbol) -> DENY. Never 'pick the newest'."""


class UnknownCorporateActionError(DomainError):
    """Vendor action code maps to no enum member -> DENY. Never ignored."""


class CorporateActionCalendarError(DomainError):
    """Action effective on a date with no session -> DENY, escalated."""


# --- market data ---------------------------------------------------------------
class BarIntegrityError(DomainError):
    """OHLC ordering violated, negative volume, or mixed currency."""


class CrossedQuoteError(DomainError):
    """bid > ask -> DENY. Usually a stale or mixed-venue feed."""


class StaleDataError(DomainError):
    """as_of older than the type's StalenessPolicy -> DENY."""


class UnsanitisedContentError(DomainError):
    """Raw vendor text reached an LLM-bound path. Rule N14, [CONST-4]."""


# --- portfolio and FX ------------------------------------------------------------
class MissingFxRateError(DomainError):
    """No FX rate for the accounting date -> DENY in BOTH pools. Invariant I10."""


class WashSaleNotApplicableError(DomainError):
    """Wash-sale field populated on a Market.IN lot [DEFAULT-6]. India has no such rule."""


# --- risk and decision -----------------------------------------------------------
class InvalidStopError(DomainError):
    """stop_price >= entry_price. Sizing off it produces an unbounded position."""


class RiskDenyIsFinal(DomainError):
    """A Decision was constructed from a DENY verdict.

    Invariant I2 and ADR-09: there is no approver and no code path to override a risk
    DENY. If a human could override one DENY, [CONST-1] would be decorative.
    """


class LlmOutputNotPermitted(DomainError):
    """LLM-derived data reached a type that may only carry deterministic output.

    X2 finding F-8. This previously raised RiskDenyIsFinal, which is a different
    condition entirely: a risk DENY is a verdict the engine reached, and recording
    one where no verdict exists misleads anyone reading the audit trail.
    """


class AuditWriteRequiredError(DomainError):
    """An effectful type was constructed without audit_event_id.

    [CONST-5]: the audit write happens BEFORE the action takes effect. If the audit write
    fails, the action does not happen.
    """


# --- state machines ---------------------------------------------------------------
class IllegalOrderTransition(DomainError):
    """Transition not in the OrderState table. The order is not mutated."""


class OverfillError(DomainError):
    """Cumulative fills exceed order quantity -> position UNRECONCILED, pool denies entries."""


class IllegalPositionTransition(DomainError):
    """Transition not in the PositionState table."""


class IllegalKillSwitchTransition(DomainError):
    """Transition not in the KillSwitchState table. There is no force_arm()."""


# =============================================================================
# 2. DECIMAL CONTEXT  (SPEC-P1.1-DOMAIN section 2, rows 1-3)
# =============================================================================

#: Precision headroom for intermediate products such as Price(-6) * Quantity(-6) = -12.
DECIMAL_PRECISION: Final[int] = 34

#: P0.1 section 6 froze ROUND_HALF_UP for money. Python's Decimal default is
#: ROUND_HALF_EVEN (bankers), so the frozen rule is silently violated unless overridden.
#: Bankers rounding is used NOWHERE in this system.
MONEY_ROUNDING: Final[str] = decimal.ROUND_HALF_UP

#: Quantity rounds DOWN, never half-anything. Since quantity >= 0 (long-only) this is
#: floor. P0.1 section 6: rounding a size up can breach the 5% cap by construction.
QUANTITY_ROUNDING: Final[str] = decimal.ROUND_DOWN

#: Price storage precision [DEFAULT-2]. Matches tick_size NUMERIC(12,6) already frozen in
#: P0.2's tick_size_regime DDL.
PRICE_EXPONENT: Final[int] = -6
_PRICE_QUANTUM: Final[Decimal] = Decimal(1).scaleb(PRICE_EXPONENT)

#: Quantity storage precision. Constrained further by the instrument's qty_increment.
QUANTITY_EXPONENT: Final[int] = -6
_QUANTITY_QUANTUM: Final[Decimal] = Decimal(1).scaleb(QUANTITY_EXPONENT)

#: FX rates are stored at 6 dp and are immutable once written (ADR-15 section 5).
FX_RATE_EXPONENT: Final[int] = -6


def build_domain_context() -> decimal.Context:
    """The Decimal context every domain computation runs under.

    The FloatOperation trap is the one that matters: it makes ``Decimal("1.00") + 1.5``
    and ``Decimal(1.5)`` raise, which is how "Money is never float" becomes enforced
    rather than asserted.

    Inexact and Rounded are deliberately NOT trapped - quantise() legitimately rounds at
    the final step of a computation (P0.1 section 6).
    """
    return decimal.Context(
        prec=DECIMAL_PRECISION,
        rounding=MONEY_ROUNDING,
        traps=[
            decimal.InvalidOperation,
            decimal.DivisionByZero,
            decimal.Overflow,
            decimal.FloatOperation,
        ],
    )


#: The single authoritative context. Every quantisation and every division in this
#: module runs under a COPY of this, via `_domain_context()`, so correctness does not
#: depend on which thread the caller is on.
_DOMAIN_CTX: Final[decimal.Context] = build_domain_context()


def _domain_context() -> Any:
    """Run a block under the domain Decimal context, on ANY thread.

    X2 finding F-2. `decimal.setcontext` is THREAD-LOCAL: a worker thread that never
    called `install_domain_decimal_context()` runs with Python's defaults —
    `prec=28`, `ROUND_HALF_EVEN` (bankers), and the `FloatOperation` trap OFF. In a
    threaded server that silently violates P0.1 §6's half-up rule at every half-way
    value. Relying on a process-wide install was a latent correctness bug; every
    rounding site now pins the context explicitly instead.
    """
    return decimal.localcontext(_DOMAIN_CTX)


def install_domain_decimal_context() -> None:
    """Install the domain context as the CURRENT THREAD's default.

    Convenience for interactive use and for third-party code that does Decimal
    arithmetic outside this module. It is NOT load-bearing: every operation in this
    module pins its own context via `_domain_context()` (X2 finding F-2).
    """
    decimal.setcontext(build_domain_context())


install_domain_decimal_context()


def _quantise(value: Decimal, quantum: Decimal, rounding: str) -> Decimal:
    """The single rounding primitive. Always runs under the domain context."""
    with _domain_context():
        return value.quantize(quantum, rounding=rounding)


def _reject_float(value: Any, field: str) -> None:
    """Guard the boundary Pydantic could otherwise coerce before the trap fires."""
    if isinstance(value, float):
        raise FloatContaminationError(
            f"{field} received a float ({value!r}). Money and Price are Decimal, never "
            f"float. Pass a str or a Decimal."
        )


def _to_decimal(value: Any, field: str) -> Decimal:
    _reject_float(value, field)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        return Decimal(value)
    raise FloatContaminationError(f"{field} cannot be built from {type(value).__name__}")


# Decimal serialises to a JSON *string*, never a JSON number. A JSON number is an
# IEEE-754 double on the far side of every parser, which reintroduces float through the
# back door. (SPEC-P1.1-DOMAIN section 2, row 8.)
DecimalStr = Annotated[
    Decimal, PlainSerializer(str, return_type=str, when_used="json")
]


def _require_utc(value: datetime) -> datetime:
    """Reject naive datetimes; normalise any tz-aware value to exactly UTC.

    [DEFAULT-5]. A naive datetime carries no evidence of intent - coercion silently
    shifts an exchange-local timestamp by 4-5.5 hours and stays invisible until a
    session-boundary test fails.
    """
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise NaiveDatetimeError(
            f"naive datetime {value!r} rejected; supply a tz-aware value"
        )
    return value.astimezone(timezone.utc)


UtcDatetime = Annotated[datetime, AfterValidator(_require_utc)]

#: A fraction in [0, 1]. Any field named *_pct is a fraction, never a percentage number
#: (P0.1 section 6). Bounds are INCLUSIVE: position_pct <= 0.05 passes at exactly 0.05.
Fraction01 = Annotated[Decimal, Field(ge=Decimal(0), le=Decimal(1))]

#: SHA-256 hex digest.
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

_GENESIS_HASH: Final[str] = "0" * 64


class _Frozen(BaseModel):
    """Base config for every domain model.

    frozen: domain objects are values. A state change produces a new object and a new
        audit event, never an in-place mutation the audit trail cannot explain.
    extra=forbid: a vendor adding a field is a data-quality event to be noticed, not
        silently dropped.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=False,
        # cached_property is derived state, not a field. Declaring it here stops
        # Pydantic treating it as one; `frozen` still holds for every actual field.
        ignored_types=(cached_property,),
    )


# =============================================================================
# 3. ENUMERATIONS
# =============================================================================
#
# Every enum is str-valued, never auto-numbered. An integer enum reorders silently on
# insertion and corrupts every persisted row and every audit hash.


class Market(str, Enum):
    """P0.1 section 10.1. Present on EVERY instrument, bar, order, position, decision and
    audit row (ADR-11 requirement 1). No table has an implicit market."""

    US = "US"
    IN = "IN"


class Exchange(str, Enum):
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    NSE = "NSE"
    BSE = "BSE"

    @property
    def market(self) -> Market:
        return _EXCHANGE_MARKET[self]


_EXCHANGE_MARKET: Final[Mapping[Exchange, Market]] = {
    Exchange.NYSE: Market.US,
    Exchange.NASDAQ: Market.US,
    Exchange.NSE: Market.IN,
    Exchange.BSE: Market.IN,
}


class Currency(str, Enum):
    USD = "USD"
    INR = "INR"

    @property
    def minor_units(self) -> int:
        """Decimal places. Both are 2 (P0.1 section 6)."""
        return _CURRENCY_MINOR_UNITS[self]


_CURRENCY_MINOR_UNITS: Final[Mapping[Currency, int]] = {
    Currency.USD: 2,
    Currency.INR: 2,
}

_MARKET_CURRENCY: Final[Mapping[Market, Currency]] = {
    Market.US: Currency.USD,
    Market.IN: Currency.INR,
}


class PoolId(str, Enum):
    """One segregated capital pool per market (ADR-15).

    No cross-margining and no cross-pool netting: USD cash cannot fund an INR trade.
    """

    US_POOL = "US_POOL"
    IN_POOL = "IN_POOL"

    @property
    def market(self) -> Market:
        return Market.US if self is PoolId.US_POOL else Market.IN

    @property
    def currency(self) -> Currency:
        return _MARKET_CURRENCY[self.market]


class InstrumentType(str, Enum):
    """DENY-BY-DEFAULT allowlist (ADR-05, invariant I5).

    An unknown or newly appearing instrument type is a DENY, not a pass-through. Futures
    and options are 'never in this program', not 'later': futures embed leverage in the
    instrument ([CONST-8]) and options carry an assignment payoff a 2.5*ATR stop cannot
    bound.
    """

    COMMON_STOCK = "COMMON_STOCK"
    ETF = "ETF"
    ADR = "ADR"
    ETN = "ETN"
    CEF = "CEF"
    SPAC = "SPAC"
    UNIT = "UNIT"
    WARRANT = "WARRANT"
    RIGHT = "RIGHT"
    PREFERRED = "PREFERRED"
    FUTURE = "FUTURE"
    OPTION = "OPTION"


#: The v1 allowlist. Enforced in P2.9; stated here so there is exactly one definition.
TRADEABLE_INSTRUMENT_TYPES_V1: Final[frozenset[InstrumentType]] = frozenset(
    {InstrumentType.COMMON_STOCK}
)
#: ETFs are read-only in v1: regime input and sector benchmark, never held (ADR-05).
READ_ONLY_INSTRUMENT_TYPES_V1: Final[frozenset[InstrumentType]] = frozenset(
    {InstrumentType.ETF}
)
#: Never tradeable in this program, at any version (ADR-05).
PERMANENTLY_BANNED_INSTRUMENT_TYPES: Final[frozenset[InstrumentType]] = frozenset(
    {InstrumentType.FUTURE, InstrumentType.OPTION}
)


class InstrumentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    HALTED = "HALTED"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"


class AccountType(str, Enum):
    """ADR-12: CASH in v1. MARGIN exists so the Chain D counter switch is config, not code."""

    CASH = "CASH"
    MARGIN = "MARGIN"


class ApproverRole(str, Enum):
    OPERATOR = "OPERATOR"
    OWNER = "OWNER"


class CostBasisMethod(str, Enum):
    """FIFO in v1 (P0.1 section 6, ASSUMPTION [VERIFY-P0.2]).

    LIFO and AVERAGE are defined so a method change is a config value rather than a
    schema migration.
    """

    FIFO = "FIFO"
    LIFO = "LIFO"
    AVERAGE = "AVERAGE"


class CorporateActionType(str, Enum):
    """Closed set. An unrecognised vendor code raises UnknownCorporateActionError.

    Deny-by-default applies here exactly as ADR-05 applies it to instrument types:
    ignoring a split does not raise, it silently misprices every subsequent bar.
    """

    SPLIT = "SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"
    CASH_DIVIDEND = "CASH_DIVIDEND"
    STOCK_DIVIDEND = "STOCK_DIVIDEND"
    TICKER_CHANGE = "TICKER_CHANGE"
    EXCHANGE_TRANSFER = "EXCHANGE_TRANSFER"
    MERGER = "MERGER"
    ACQUISITION = "ACQUISITION"
    SPINOFF = "SPINOFF"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    DELISTING = "DELISTING"


class SessionType(str, Enum):
    REGULAR = "REGULAR"
    HALF_DAY = "HALF_DAY"
    SPECIAL = "SPECIAL"


class BarInterval(str, Enum):
    """ADR-13: daily bars for all signals; 5-minute bars only for instruments held.

    The enum has exactly the two members the architecture permits.
    """

    DAILY = "DAILY"
    MIN_5 = "MIN_5"


class ScoreKind(str, Enum):
    FUNDAMENTAL = "FUNDAMENTAL"
    TECHNICAL = "TECHNICAL"
    COMPOSITE = "COMPOSITE"


class SignalDirection(str, Enum):
    """No SELL_SHORT. ADR-12 is long-only and the enum does not contain a member the
    system may not act on. EXIT is the closing of a held position."""

    BUY = "BUY"
    HOLD = "HOLD"
    EXIT = "EXIT"


class DecisionAction(str, Enum):
    ENTER = "ENTER"
    ADD = "ADD"
    TRIM = "TRIM"
    EXIT = "EXIT"
    NO_TRADE = "NO_TRADE"


class InvalidationKind(str, Enum):
    """Machine-evaluable predicates only.

    An invalidation condition only a human can evaluate cannot fire automatically, and a
    thesis-deterioration detector that needs a human is not a detector.
    """

    PRICE_BELOW = "PRICE_BELOW"
    ATR_STOP = "ATR_STOP"
    TIME_STOP = "TIME_STOP"
    FUNDAMENTAL_BREACH = "FUNDAMENTAL_BREACH"
    NEWS_EVENT = "NEWS_EVENT"


class RiskDecision(str, Enum):
    """Binary, deliberately. A three-valued verdict would put the risk engine into the
    sizing business."""

    ALLOW = "ALLOW"
    DENY = "DENY"


class RegimeLabel(str, Enum):
    """[DEFAULT-7]; vocabulary from [RS section 13] 'Bull, bear, sideways, volatile'.

    UNKNOWN is the fail-closed regime: a regime the classifier cannot determine does not
    become SIDEWAYS by default. P2.9 treats UNKNOWN as no-new-entries.
    """

    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """[CONST]: limit orders default, market only for emergency exit."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class OrderState(str, Enum):
    PENDING_NEW = "PENDING_NEW"
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELED = "CANCELED"
    PENDING_REPLACE = "PENDING_REPLACE"
    REPLACED = "REPLACED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class PositionState(str, Enum):
    PENDING_OPEN = "PENDING_OPEN"
    OPEN = "OPEN"
    PENDING_CLOSE = "PENDING_CLOSE"
    CLOSED = "CLOSED"
    UNRECONCILED = "UNRECONCILED"


class KillSwitchState(str, Enum):
    ARMED = "ARMED"
    POOL_HALTED = "POOL_HALTED"
    TRIPPED = "TRIPPED"


class KillSwitchScope(str, Enum):
    GLOBAL = "GLOBAL"
    POOL = "POOL"


class AuditEventClass(str, Enum):
    """RULE-B4's durability classes, plus the classes invariant I4 replays.

    X2 finding F-5: P1.2's audit_log requires this and P1.1 never defined it.
    ACTION events are individually durable; EVALUATION events may be batched - but an
    evaluation that becomes the REASON for an action is promoted to ACTION.
    """

    ACTION = "ACTION"
    EVALUATION = "EVALUATION"
    NAV = "NAV"
    RISK = "RISK"
    KILL_SWITCH = "KILL_SWITCH"
    APPROVAL = "APPROVAL"
    SYSTEM = "SYSTEM"


class RunType(str, Enum):
    INGEST = "INGEST"
    PIPELINE = "PIPELINE"
    ORDER = "ORDER"
    MONITOR = "MONITOR"
    RECONCILE = "RECONCILE"
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"


class StalenessAction(str, Enum):
    """[CONST-6] admits no value but DENY. The field exists so the policy is explicit and
    auditable rather than implied."""

    DENY = "DENY"


# =============================================================================
# 4. MONEY, PRICE, QUANTITY  (SPEC-P1.1-DOMAIN section 3)
# =============================================================================


class Money(_Frozen):
    """A signed currency amount, quantised to the currency's minor units.

    Closure (SPEC-P1.1-DOMAIN section 3.2). Let M_c = {d : exponent(d) == -2}:
        Money + Money  -> exponent min(-2,-2) = -2   CLOSED
        Money - Money  -> exponent -2                CLOSED
        Money * int    -> exponent -2 + 0 = -2       CLOSED   (the share-count case)
        Money * Price  -> exponent -8                NOT closed -> quantise() explicitly
        Money / x      -> undefined exponent         OPERATOR NOT PROVIDED [DEFAULT-4]

    The first three are the entire set of operations performed on money without an
    explicit rounding step. Everything else is forced through quantise(), which is the
    only place ROUND_HALF_UP is applied - satisfying P0.1 section 6's "final step only,
    never at intermediates".

    Money is SIGNED. Realised P&L, fees and cash adjustments are legitimately negative.
    Only Quantity is sign-constrained.
    """

    amount: DecimalStr
    currency: Currency

    @model_validator(mode="before")
    @classmethod
    def _coerce_and_quantise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw = data.get("amount")
        cur = data.get("currency")
        if raw is None or cur is None:
            return data
        currency = cur if isinstance(cur, Currency) else Currency(cur)
        amount = _to_decimal(raw, "Money.amount")
        if not amount.is_finite():
            raise MoneyPrecisionError(f"Money.amount must be finite, got {amount!r}")
        quantum = Decimal(1).scaleb(-currency.minor_units)
        return {
            "amount": _quantise(amount, quantum, MONEY_ROUNDING),
            "currency": currency,
        }

    @model_validator(mode="after")
    def _check_exponent(self) -> Money:
        expected = -self.currency.minor_units
        if self.amount.as_tuple().exponent != expected:
            raise MoneyPrecisionError(
                f"{self.currency.value} requires exponent {expected}, got "
                f"{self.amount.as_tuple().exponent}"
            )
        return self

    # -- construction helpers -------------------------------------------------
    @classmethod
    def zero(cls, currency: Currency) -> Money:
        return cls(amount=Decimal(0), currency=currency)

    @classmethod
    def of(cls, amount: str | int | Decimal, currency: Currency) -> Money:
        return cls(amount=amount, currency=currency)

    # -- guards ---------------------------------------------------------------
    def _same_currency(self, other: Money, op: str) -> None:
        if self.currency is not other.currency:
            raise CurrencyMismatchError(
                f"cannot {op} {self.currency.value} and {other.currency.value}. "
                f"Invariant I1: no code path converts currency."
            )

    # -- closed arithmetic ----------------------------------------------------
    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other, "add")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other, "subtract")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: int) -> Money:
        """Money * int only. Multiplying by a Decimal leaves the type - use quantise()."""
        if not isinstance(factor, int) or isinstance(factor, bool):
            raise TypeError(
                "Money may only be multiplied by an int (a share count). For any other "
                "factor, compute in Decimal and quantise() once at the final step."
            )
        return Money(amount=self.amount * Decimal(factor), currency=self.currency)

    __rmul__ = __mul__

    def __neg__(self) -> Money:
        return Money(amount=-self.amount, currency=self.currency)

    def __abs__(self) -> Money:
        return Money(amount=abs(self.amount), currency=self.currency)

    def __truediv__(self, other: Any) -> Any:
        raise TypeError(
            "Money division is not provided [DEFAULT-4]: division is not closed over a "
            "fixed-exponent decimal and the sum of the parts would silently differ from "
            "the whole. Use Money.allocate(weights), which is exact by construction."
        )

    __floordiv__ = __truediv__

    # -- comparison -----------------------------------------------------------
    def __eq__(self, other: Any) -> bool:
        """Cross-currency equality is False and does NOT raise.

        Equality must not raise or Money becomes unusable in sets, as dict keys, and in
        assert comparisons. Ordering across currencies DOES raise - the asymmetry is
        deliberate (SPEC-P1.1-DOMAIN section 2, row 7).
        """
        if not isinstance(other, Money):
            return NotImplemented
        return self.currency is other.currency and self.amount == other.amount

    def __hash__(self) -> int:
        return hash((self.currency, self.amount))

    def __lt__(self, other: Money) -> bool:
        self._same_currency(other, "compare")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._same_currency(other, "compare")
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        self._same_currency(other, "compare")
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        self._same_currency(other, "compare")
        return self.amount >= other.amount

    # -- the only rounding point ---------------------------------------------
    @classmethod
    def quantise(cls, raw: Decimal, currency: Currency) -> Money:
        """Turn an unquantised Decimal into Money with ONE ROUND_HALF_UP application.

        This is the only place a monetary rounding happens. P0.1 section 6: rounding is
        applied at the final step of a computation, never at intermediates.
        """
        _reject_float(raw, "Money.quantise")
        return cls(amount=raw, currency=currency)

    # -- exact splitting ------------------------------------------------------
    def allocate(self, weights: Sequence[Decimal | int]) -> tuple[Money, ...]:
        """Split this amount proportionally with NO loss of minor units.

        Largest-remainder: floor each share in minor units, then hand the remaining
        minor units one at a time to the largest fractional remainders, ties broken by
        ascending index. The tie-break is deterministic because a nondeterministic one
        would make an audit replay diverge.

        Postcondition, asserted: sum(allocate(w)) == self, exactly, for every input.
        """
        if not weights:
            raise ValueError("allocate requires at least one weight")
        decs: list[Decimal] = []
        for i, w in enumerate(weights):
            _reject_float(w, f"allocate weight[{i}]")
            d = w if isinstance(w, Decimal) else Decimal(w)
            if d <= 0:
                raise ValueError(
                    f"allocate weight[{i}] = {d} must be > 0; a non-positive weight has "
                    f"no meaning in a proportional split"
                )
            decs.append(d)

        # Scale every weight to an integer on a common denominator.
        shift = max(-min(d.as_tuple().exponent, 0) for d in decs)
        w_int = [int(d.scaleb(shift).to_integral_value(rounding=decimal.ROUND_DOWN)) for d in decs]
        w_sum = sum(w_int)
        if w_sum <= 0:
            raise ValueError("allocate weights sum to zero after scaling")

        minor = self.currency.minor_units
        total_minor = int(self.amount.scaleb(minor).to_integral_value(rounding=MONEY_ROUNDING))
        sign = -1 if total_minor < 0 else 1
        magnitude = abs(total_minor)

        base = [magnitude * wi // w_sum for wi in w_int]
        remainder = magnitude - sum(base)
        # Fractional remainder numerators, compared without division.
        frac = [magnitude * wi - b * w_sum for wi, b in zip(w_int, base, strict=True)]
        order = sorted(range(len(base)), key=lambda i: (-frac[i], i))
        for i in order[:remainder]:
            base[i] += 1

        out = tuple(
            Money(amount=Decimal(sign * b).scaleb(-minor), currency=self.currency)
            for b in base
        )
        # X2 finding M-2. This was an `assert`, which `python -O` strips: the one check
        # that money is conserved across a split vanished in an optimised deployment and
        # no test noticed. A guard on money conservation must not depend on __debug__.
        total = sum((m.amount for m in out), Decimal(0))
        if total != self.amount:
            raise MoneyPrecisionError(
                f"allocate postcondition violated: parts sum to {total}, expected "
                f"{self.amount} ({self.currency.value})"
            )
        return out

    def __str__(self) -> str:
        return f"{self.amount} {self.currency.value}"


class Price(_Frozen):
    """Currency per share, stored at exactly 6 dp [DEFAULT-2].

    Tick validation applies ONLY to prices we send. Venues legitimately fill sub-penny -
    rejecting those fills would break reconciliation on every price-improved execution.
    """

    value: DecimalStr
    currency: Currency

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw = data.get("value")
        if raw is None:
            return data
        value = _to_decimal(raw, "Price.value")
        if not value.is_finite():
            raise MoneyPrecisionError(f"Price.value must be finite, got {value!r}")
        if value < 0:
            raise MoneyPrecisionError(f"Price.value must be >= 0, got {value}")
        return {**data, "value": _quantise(value, _PRICE_QUANTUM, MONEY_ROUNDING)}

    def is_multiple_of(self, tick: Decimal) -> bool:
        """Exact Decimal modulo. No epsilon, no float comparison."""
        _reject_float(tick, "tick")
        if tick <= 0:
            raise MissingTickRegimeError(f"tick must be > 0, got {tick}")
        return self.value % tick == 0

    def validate_tick(self, tick: Decimal) -> None:
        """Rule N10: reject, never round.

        Silent rounding moves a price the strategy chose in a direction nobody decided,
        and the audit trail then records a price the decision engine never produced.
        """
        if not self.is_multiple_of(tick):
            raise TickSizeViolation(
                f"limit price {self.value} is not an exact multiple of tick {tick}. "
                f"Rule N10: rejected locally, never rounded."
            )

    def notional(self, quantity: Quantity) -> Money:
        """Price(-6) * Quantity(-6) -> exponent -12, exact; then ONE quantise to money."""
        with _domain_context():
            raw = self.value * quantity.value
        return Money.quantise(raw, self.currency)

    def __lt__(self, other: Price) -> bool:
        self._same_currency(other)
        return self.value < other.value

    def __le__(self, other: Price) -> bool:
        self._same_currency(other)
        return self.value <= other.value

    def __gt__(self, other: Price) -> bool:
        self._same_currency(other)
        return self.value > other.value

    def __ge__(self, other: Price) -> bool:
        self._same_currency(other)
        return self.value >= other.value

    def _same_currency(self, other: Price) -> None:
        if self.currency is not other.currency:
            raise CurrencyMismatchError(
                f"cannot compare prices in {self.currency.value} and {other.currency.value}"
            )

    def __str__(self) -> str:
        return f"{self.value} {self.currency.value}"


class Quantity(_Frozen):
    """Shares. Non-negative, 6 dp, and a multiple of the instrument's qty_increment.

    Sign convention (P0.1 section 6): quantities are POSITIVE. ADR-12 is long-only, so no
    negative quantity exists in v1 and a negative quantity is a validation error, NOT a
    short. Direction lives in OrderSide, never in the quantity.
    """

    value: DecimalStr

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw = data.get("value")
        if raw is None:
            return data
        value = _to_decimal(raw, "Quantity.value")
        if not value.is_finite():
            raise NegativeQuantityError(f"Quantity.value must be finite, got {value!r}")
        if value < 0:
            raise NegativeQuantityError(
                f"Quantity.value = {value} is negative. Long-only (ADR-12): a negative "
                f"quantity is a validation error, not a short."
            )
        return {"value": _quantise(value, _QUANTITY_QUANTUM, QUANTITY_ROUNDING)}

    @classmethod
    def zero(cls) -> Quantity:
        return cls(value=Decimal(0))

    @classmethod
    def round_to_increment(cls, raw: Decimal, increment: Decimal) -> Quantity:
        """Round DOWN to the tradeable increment (P0.1 section 6).

        Never up: rounding a size up can breach the 5% cap by construction. A result of
        zero is a no-trade outcome, not an error - a session with no trades is a feature.
        """
        _reject_float(raw, "quantity")
        _reject_float(increment, "increment")
        if increment <= 0:
            raise MissingReferenceDataError(
                f"qty_increment must be > 0, got {increment}. Never defaulted to 1: in "
                f"India that would place an order for an illegal quantity."
            )
        with _domain_context():
            units = (raw / increment).to_integral_value(rounding=QUANTITY_ROUNDING)
            value = units * increment
        return cls(value=value)

    def validate_increment(self, increment: Decimal) -> None:
        _reject_float(increment, "increment")
        if increment <= 0:
            raise MissingReferenceDataError(f"qty_increment must be > 0, got {increment}")
        if self.value % increment != 0:
            raise QuantityIncrementError(
                f"quantity {self.value} is not a multiple of increment {increment}"
            )

    def __add__(self, other: Quantity) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        return Quantity(value=self.value + other.value)

    def __sub__(self, other: Quantity) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        return Quantity(value=self.value - other.value)

    def __lt__(self, other: Quantity) -> bool:
        return self.value < other.value

    def __le__(self, other: Quantity) -> bool:
        return self.value <= other.value

    def __gt__(self, other: Quantity) -> bool:
        return self.value > other.value

    def __ge__(self, other: Quantity) -> bool:
        return self.value >= other.value

    def is_zero(self) -> bool:
        return self.value == 0

    def __str__(self) -> str:
        return str(self.value)


# =============================================================================
# 5. TIME, SESSIONS, CALENDAR  (SPEC-P1.1-DOMAIN section 4)
# =============================================================================


class ExchangeSession(_Frozen):
    """One row per (exchange, trading_date), storing EXPLICIT UTC instants.

    Storing resolved UTC instants per date removes DST arithmetic from the runtime
    entirely: the loader resolved it once, from the IANA database, when the row was
    written. P0.1 section 6's observation that the 09:45 ET window is 13:45 UTC in EDT
    and 14:45 UTC in EST becomes a property of two rows rather than a branch in the code.

    ABSENCE OF A ROW IS THE REPRESENTATION OF "CLOSED". There is no is_holiday boolean to
    fall out of sync with reality.
    """

    exchange: Exchange
    market: Market
    trading_date: date
    session_type: SessionType
    pre_market_open_utc: UtcDatetime | None = None
    regular_open_utc: UtcDatetime
    regular_close_utc: UtcDatetime
    post_market_close_utc: UtcDatetime | None = None
    settlement_date: date
    counts_for_sequencing: bool = True

    @model_validator(mode="after")
    def _check_ordering(self) -> ExchangeSession:
        if self.regular_open_utc >= self.regular_close_utc:
            raise MissingSessionError(
                f"{self.exchange.value} {self.trading_date}: open >= close"
            )
        if self.pre_market_open_utc is not None and (
            self.pre_market_open_utc >= self.regular_open_utc
        ):
            raise MissingSessionError("pre_market_open_utc must precede regular_open_utc")
        if self.post_market_close_utc is not None and (
            self.post_market_close_utc <= self.regular_close_utc
        ):
            raise MissingSessionError("post_market_close_utc must follow regular_close_utc")
        if self.settlement_date < self.trading_date:
            raise MissingSessionError("settlement_date precedes trading_date")
        if self.exchange.market is not self.market:
            raise MissingSessionError(
                f"{self.exchange.value} belongs to {self.exchange.market.value}, not "
                f"{self.market.value}"
            )
        return self

    @property
    def utc_accounting_date(self) -> date:
        """ADR-15 section 7: the UTC calendar date on which the session closes.

        Used for consolidated daily loss, consolidated NAV and the consolidated drawdown
        counter. Distinct from trading_date, which is exchange-local and drives per-pool
        counters. Conflating the two is the off-by-one-day bug ADR-15 names explicitly.
        """
        return self.regular_close_utc.date()


class TradingCalendar(_Frozen):
    """Sessions are DATA (ADR-11 requirement 2 forbids a hard-coded US holiday list).

    This type asserts no holiday and hard-codes no date. It is constructed from rows the
    loader produced and answers questions about them.
    """

    exchange: Exchange
    #: Sorted by trading_date ascending at construction, and that ordering is an
    #: INVARIANT the lookup methods rely on.
    #:
    #: X2 finding F-6: the previous implementation rebuilt a dict and re-sorted the
    #: whole calendar on EVERY call. Measured at 0.89 ms against a 10-year calendar,
    #: which is ~1.3 s per session across a 1,500-name universe - paid repeatedly for
    #: a value that cannot change, on a frozen model.
    sessions: tuple[ExchangeSession, ...]

    @model_validator(mode="before")
    @classmethod
    def _sort_sessions(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("sessions") is not None:
            return {
                **data,
                "sessions": tuple(sorted(data["sessions"], key=lambda s: s.trading_date)),
            }
        return data

    @model_validator(mode="after")
    def _check_sessions(self) -> TradingCalendar:
        seen: set[date] = set()
        for s in self.sessions:
            if s.exchange is not self.exchange:
                raise MissingSessionError(
                    f"session for {s.exchange.value} in {self.exchange.value} calendar"
                )
            if s.trading_date in seen:
                raise MissingSessionError(f"duplicate session {s.trading_date}")
            seen.add(s.trading_date)
        return self

    @cached_property
    def _by_date(self) -> Mapping[date, ExchangeSession]:
        return {s.trading_date: s for s in self.sessions}

    @cached_property
    def _sequenced(self) -> tuple[ExchangeSession, ...]:
        """Sessions counting for sequencing and rolling-window counts.

        Excludes Muhurat and other special sessions (P0.1 section 6). Already in date
        order, because `sessions` is sorted at construction.
        """
        return tuple(s for s in self.sessions if s.counts_for_sequencing)

    @cached_property
    def _sequenced_dates(self) -> tuple[date, ...]:
        return tuple(s.trading_date for s in self._sequenced)

    @cached_property
    def _sequenced_index(self) -> Mapping[date, int]:
        return {d: i for i, d in enumerate(self._sequenced_dates)}

    def session(self, trading_date: date) -> ExchangeSession:
        """Missing row -> DENY. Never inferred from the previous day, never assumed open,
        never assumed closed."""
        found = self._by_date.get(trading_date)
        if found is None:
            raise MissingSessionError(
                f"no session row for {self.exchange.value} on {trading_date}; "
                f"[CONST-6] fail-closed - the pipeline halts for this market"
            )
        return found

    def is_open(self, trading_date: date) -> bool:
        return trading_date in self._by_date

    def sequenced_sessions(self) -> tuple[ExchangeSession, ...]:
        return self._sequenced

    def sessions_between(self, start: date, end: date) -> tuple[ExchangeSession, ...]:
        """Inclusive of both endpoints, sequenced sessions only."""
        dates = self._sequenced_dates
        lo = bisect_left(dates, start)
        hi = bisect_right(dates, end)
        return self._sequenced[lo:hi]

    def nth_prior_session(self, reference: date, n: int) -> ExchangeSession:
        """n completed sessions before `reference`. n=0 is the reference session itself.

        Rolling windows are counted in COMPLETED EXCHANGE SESSIONS, never calendar days
        (P0.1 section 6). "20-day volume" is 20 sequenced sessions.
        """
        if n < 0:
            raise ValueError("n must be >= 0")
        i = self._sequenced_index.get(reference)
        if i is None:
            raise MissingSessionError(f"{reference} is not a sequenced session")
        if i - n < 0:
            raise MissingSessionError(
                f"only {i} sequenced sessions precede {reference}; {n} requested"
            )
        return self._sequenced[i - n]

    def settlement_date_for(self, trading_date: date) -> date:
        """Resolved by the loader from the configured cycle and this calendar, so a
        holiday shifts it.

        US and India settlement cycles are both ASSUMPTION [VERIFY-P0.2] carried from
        ADR-13 Chain D. This spec stores whatever the loader resolved; it asserts no
        settlement cycle. See OPEN QUESTIONS Q-P1.1-1 and Q-P1.1-2.
        """
        return self.session(trading_date).settlement_date


# =============================================================================
# 6. SYMBOL IDENTITY  (SPEC-P1.1-DOMAIN section 5)
# =============================================================================


class Instrument(_Frozen):
    """instrument_id is a uuid4 assigned at first sighting and IMMUTABLE FOREVER.

    It survives ticker changes, exchange transfers, mergers and delisting, and is never
    derived from a symbol - deriving identity from a mutable attribute is the same bug as
    using a phone number as a primary key.

    [DEFAULT-1]: identity is PER LISTING VENUE. NSE RELIANCE and BSE RELIANCE are two
    instruments sharing one issuer_id, because they have different tick regimes, different
    liquidity and different order books.
    """

    instrument_id: UUID
    issuer_id: UUID | None = None
    market: Market
    exchange: Exchange
    instrument_type: InstrumentType
    status: InstrumentStatus
    currency: Currency
    #: Tradeable quantity increment. US = 1 in v1 [DEFAULT-3]; India = lot_size from the
    #: Zerodha instruments dump. Never a constant, never defaulted.
    qty_increment: DecimalStr
    lot_size: DecimalStr | None = None
    #: Modelled but disabled in v1 [DEFAULT-3]: [CONST] mandates limit orders and P0.2
    #: verified US fractional trading is market/day orders only. Jointly unsatisfiable.
    supports_fractional: bool = False
    isin: str | None = None
    cusip: str | None = None
    figi: str | None = None
    figi_composite: str | None = None
    delisted_on: date | None = None
    final_price: Price | None = None

    @model_validator(mode="after")
    def _check(self) -> Instrument:
        if self.exchange.market is not self.market:
            raise MissingReferenceDataError(
                f"{self.exchange.value} belongs to {self.exchange.market.value}"
            )
        if self.currency is not _MARKET_CURRENCY[self.market]:
            raise CurrencyMismatchError(
                f"{self.market.value} instruments are denominated in "
                f"{_MARKET_CURRENCY[self.market].value}, got {self.currency.value}"
            )
        if self.qty_increment <= 0:
            raise MissingReferenceDataError(
                f"qty_increment must be > 0, got {self.qty_increment}. Never defaulted."
            )
        if self.market is Market.IN and self.lot_size is None:
            raise MissingReferenceDataError(
                "India instruments require lot_size from the broker instruments dump"
            )
        if self.status is InstrumentStatus.DELISTED and self.delisted_on is None:
            raise MissingReferenceDataError("a DELISTED instrument requires delisted_on")
        if self.supports_fractional and self.market is Market.US:
            # [DEFAULT-3] / Q-P1.1-3: the capability is modelled, not enabled.
            raise MissingReferenceDataError(
                "US fractional trading requires market/day orders (P0.2 [V]) which "
                "[CONST] reserves for emergency exit. Fractional is unreachable in v1; "
                "see SPEC-P1.1-DOMAIN section 3.4 and OPEN QUESTION Q-P1.1-3."
            )
        return self

    def is_tradeable_v1(self) -> bool:
        """Deny-by-default (ADR-05, invariant I5)."""
        return (
            self.instrument_type in TRADEABLE_INSTRUMENT_TYPES_V1
            and self.status is InstrumentStatus.ACTIVE
        )


class SymbolMapping(_Frozen):
    """Bitemporal. valid_from inclusive, valid_to EXCLUSIVE, None = open-ended.

    A ticker change closes one row and opens another. It never updates a symbol in place,
    because a backtest resolving a symbol as of a past decision date must see the symbol
    that was in force on that date.

    A symbol reused by a different company after a delisting resolves correctly by
    construction - the two rows carry different instrument_ids. This is the single most
    common identity/survivorship bug and the bitemporal key eliminates it.
    """

    instrument_id: UUID
    market: Market
    exchange: Exchange
    symbol: Annotated[str, Field(min_length=1, max_length=32)]
    valid_from: date
    valid_to: date | None = None

    @model_validator(mode="after")
    def _check(self) -> SymbolMapping:
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise UnknownSymbolError("valid_to must be strictly after valid_from")
        return self

    def covers(self, on: date) -> bool:
        return self.valid_from <= on and (self.valid_to is None or on < self.valid_to)


def resolve_instrument(
    mappings: Sequence[SymbolMapping], market: Market, symbol: str, on: date
) -> UUID:
    """Symbol -> instrument_id as of a date. Never a bare symbol-column lookup."""
    hits = [m for m in mappings if m.market is market and m.symbol == symbol and m.covers(on)]
    if not hits:
        raise UnknownSymbolError(f"no mapping for {market.value}:{symbol} on {on}")
    if len(hits) > 1:
        raise AmbiguousSymbolError(
            f"{len(hits)} open mappings for {market.value}:{symbol} on {on}; "
            f"never 'pick the newest'"
        )
    return hits[0].instrument_id


def resolve_symbol(mappings: Sequence[SymbolMapping], instrument_id: UUID, on: date) -> str:
    """instrument_id -> symbol as of a date."""
    hits = [m for m in mappings if m.instrument_id == instrument_id and m.covers(on)]
    if not hits:
        raise UnknownSymbolError(f"no symbol for {instrument_id} on {on}")
    if len(hits) > 1:
        raise AmbiguousSymbolError(f"{len(hits)} symbols for {instrument_id} on {on}")
    return hits[0].symbol


class SuccessorLink(_Frozen):
    """Merger or acquisition conversion.

    Existing lots close and new lots open against the successor carrying the ORIGINAL
    cost basis and the ORIGINAL acquisition date: a share-for-share exchange does not
    reset the tax holding period, ASSUMPTION [VERIFY-P0.2] (see OPEN QUESTION Q-P1.1-5).
    Any cash component is a realised event on the predecessor lot.
    """

    predecessor_instrument_id: UUID
    successor_instrument_id: UUID
    share_ratio: DecimalStr
    cash_per_share: Money | None = None
    effective_date: date

    @field_validator("share_ratio")
    @classmethod
    def _positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("share_ratio must be > 0")
        return v


class CorporateAction(_Frozen):
    """Rule N9: aggregates are requested with adjusted=false and adjustment is computed
    on read from the splits and dividends tables. Adjustment is never taken from the
    vendor."""

    action_id: UUID
    instrument_id: UUID
    market: Market
    action_type: CorporateActionType
    ex_date: date
    effective_date: date
    ratio: DecimalStr | None = None
    cash_amount: Money | None = None
    successor: SuccessorLink | None = None
    source: str
    as_of: UtcDatetime
    retrieved_at: UtcDatetime

    @model_validator(mode="after")
    def _check(self) -> CorporateAction:
        needs_ratio = {
            CorporateActionType.SPLIT,
            CorporateActionType.REVERSE_SPLIT,
            CorporateActionType.STOCK_DIVIDEND,
        }
        if self.action_type in needs_ratio and self.ratio is None:
            raise UnknownCorporateActionError(
                f"{self.action_type.value} requires a ratio; a missing ratio would "
                f"silently misprice every subsequent bar"
            )
        if self.action_type is CorporateActionType.CASH_DIVIDEND and self.cash_amount is None:
            raise UnknownCorporateActionError("CASH_DIVIDEND requires cash_amount")
        if (
            self.action_type in {CorporateActionType.MERGER, CorporateActionType.ACQUISITION}
            and self.successor is None
        ):
            raise UnknownCorporateActionError(
                f"{self.action_type.value} requires a SuccessorLink"
            )
        if self.ratio is not None and self.ratio <= 0:
            raise UnknownCorporateActionError("ratio must be > 0")
        return self


def parse_corporate_action_type(vendor_code: str) -> CorporateActionType:
    """Deny-by-default. An unrecognised code raises rather than being ignored."""
    try:
        return CorporateActionType(vendor_code.strip().upper())
    except ValueError as exc:
        raise UnknownCorporateActionError(
            f"vendor corporate-action code {vendor_code!r} maps to no known type; "
            f"[CONST-6] fail-closed - never silently ignored"
        ) from exc


# =============================================================================
# 7. MARKET DATA  (SPEC-P1.1-DOMAIN section 6)
# =============================================================================


class StalenessPolicy(_Frozen):
    """[CONST-6] admits only DENY. The field exists so the policy is explicit and
    auditable rather than implied."""

    data_type: str
    max_age_seconds: Annotated[int, Field(gt=0)]
    on_breach: StalenessAction = StalenessAction.DENY

    def check(self, as_of: datetime, now: datetime) -> None:
        """`now` is a parameter, never datetime.now(): the domain has no clock."""
        age = (_require_utc(now) - _require_utc(as_of)).total_seconds()
        if age > self.max_age_seconds:
            raise StaleDataError(
                f"{self.data_type} is {age:.0f}s old, limit {self.max_age_seconds}s -> DENY"
            )


class _MarketDatum(_Frozen):
    """Provenance is not optional.

    Rule N7 requires that a disagreement between two sources be a data-quality event
    rather than a silent tiebreak, and that is only expressible if every row knows where
    it came from.
    """

    instrument_id: UUID
    market: Market
    as_of: UtcDatetime
    retrieved_at: UtcDatetime
    source: str


class Bar(_MarketDatum):
    """OHLCV for one instrument over one interval.

    is_final is False for a session still in progress and such a bar MAY NOT feed a
    signal. This is what makes P0.1 section 6's "ATR(14) excludes today's partial bar"
    enforceable at the type level rather than remembered in P2.4.
    """

    interval: BarInterval
    trading_date: date
    open: Price
    high: Price
    low: Price
    close: Price
    volume: Annotated[int, Field(ge=0)]
    is_final: bool

    @model_validator(mode="after")
    def _check(self) -> Bar:
        prices = (self.open, self.high, self.low, self.close)
        currencies = {p.currency for p in prices}
        if len(currencies) != 1:
            raise BarIntegrityError(f"mixed currencies in one bar: {currencies}")
        if any(p.value <= 0 for p in prices):
            raise BarIntegrityError("bar prices must all be > 0")
        if not (self.low <= self.open <= self.high):
            raise BarIntegrityError(
                f"open {self.open.value} outside [{self.low.value}, {self.high.value}]"
            )
        if not (self.low <= self.close <= self.high):
            raise BarIntegrityError(
                f"close {self.close.value} outside [{self.low.value}, {self.high.value}]"
            )
        return self

    def assert_signal_eligible(self) -> None:
        """A non-final bar in an indicator is look-ahead bias."""
        if not self.is_final:
            raise StaleDataError(
                f"bar {self.instrument_id} {self.trading_date} is not final and may not "
                f"feed a signal (P0.1 section 6)"
            )


class Quote(_MarketDatum):
    """Rule N6: screening must never run on single-venue (IEX) prices."""

    bid: Price
    ask: Price
    bid_size: Annotated[int, Field(ge=0)]
    ask_size: Annotated[int, Field(ge=0)]
    venue: str
    is_consolidated: bool

    @model_validator(mode="after")
    def _check(self) -> Quote:
        if self.bid.currency is not self.ask.currency:
            raise CrossedQuoteError("bid and ask in different currencies")
        if self.bid > self.ask:
            raise CrossedQuoteError(
                f"crossed quote bid {self.bid.value} > ask {self.ask.value}; usually a "
                f"stale or mixed-venue feed -> DENY"
            )
        return self

    def assert_screening_eligible(self) -> None:
        if not self.is_consolidated:
            raise StaleDataError(
                "rule N6: screening must never run on single-venue prices"
            )


class Trade(_MarketDatum):
    """A single executed print on the PUBLIC TAPE - not our fill.

    The glossary (SPEC-P1.1-DOMAIN section 13) pins the distinction: [RS] uses "trade"
    for a tape print, our fill, and a round-turn. Conflating them is how a slippage model
    ends up measuring the wrong thing.
    """

    price: Price
    size: Annotated[int, Field(gt=0)]
    venue: str
    tape_sequence: int | None = None


class FundamentalsSnapshot(_MarketDatum):
    """Three distinct dates, and the distinction is the whole point.

    Rule N1: features are lagged to the DISSEMINATION date, never the filing date. Using
    filed_at is look-ahead bias - the filing existed before anyone could act on it.

    Rule N7: where FMP and EDGAR disagree materially, EDGAR is authoritative and the
    discrepancy is a data-quality event. The reconciliation writes a second row rather
    than editing the first, which is why `source` is on every snapshot.
    """

    period_end: date
    filed_at: UtcDatetime
    disseminated_at: UtcDatetime
    fiscal_period: Annotated[str, Field(min_length=1, max_length=16)]
    #: Calendar as_of, mapped at ingest. ADR-07's retrain cadence uses CALENDAR quarters
    #: while fundamentals use the issuer's fiscal periods - two different clocks.
    calendar_as_of: date
    metrics: Mapping[str, DecimalStr]

    @model_validator(mode="after")
    def _check(self) -> FundamentalsSnapshot:
        if self.disseminated_at < self.filed_at:
            raise BarIntegrityError("disseminated_at precedes filed_at")
        return self

    def feature_timestamp(self) -> datetime:
        """Rule N1. The only timestamp a feature may be lagged to."""
        return self.disseminated_at


class NewsItem(_MarketDatum):
    """Rule N16 shapes this type.

    M-5 resolved [V] 2026-08-26: the vendor news archive is NOT point-in-time. Both
    candidate vendors expose a post-publication revision timestamp and neither offers any
    version, revision or as-of-content parameter, so a historical query returns the
    article as currently stored.

    Therefore OUR store must be the point-in-time record:
      - keyed (vendor_id, revision_seq), revision_seq starting at 1 on first receipt
      - headline and body_sanitised SNAPSHOTTED at first receipt
      - the vendor revision timestamp persisted
      - any later change writes a NEW REVISION ROW, never an overwrite
      - a backtest reads the FIRST-SEEN revision as of the decision date

    Rule N14 / [CONST-4]: body_sanitised is the ONLY body field the domain exposes, and it
    is untrusted DATA. The raw body lives in P1.2's ingest table and is NOT REACHABLE from
    the domain model, so there is no attribute an LLM prompt builder could accidentally
    read. Alpaca's news content "might contain HTML", which is exactly the shape an
    injection arrives in.
    """

    vendor_id: Annotated[str, Field(min_length=1)]
    revision_seq: Annotated[int, Field(ge=1)]
    headline: Annotated[str, Field(max_length=1000)]
    #: Bounded. X2 finding F-7: an unbounded body is an untrusted vendor string with
    #: no ceiling, and rule N14 already treats this field as hostile input. 200,000
    #: characters is ~100x the largest plausible article and still bounds the blast
    #: radius of a malformed or malicious payload.
    body_sanitised: Annotated[str, Field(max_length=200_000)]
    sanitiser_version: Annotated[str, Field(min_length=1)]
    vendor_published_at: UtcDatetime
    vendor_updated_at: UtcDatetime | None = None
    first_seen_at: UtcDatetime
    instrument_ids: tuple[UUID, ...] = ()

    @model_validator(mode="after")
    def _check(self) -> NewsItem:
        if self.revision_seq == 1 and self.first_seen_at != self.retrieved_at:
            raise UnsanitisedContentError(
                "revision 1 first_seen_at must equal retrieved_at; it is the "
                "point-in-time anchor a backtest joins on (rule N16)"
            )
        return self

    @property
    def is_point_in_time_record(self) -> bool:
        """Only the first-seen revision is point-in-time. Rule N16's corollary: historical
        news BACKFILL is structurally unsound for any content-derived feature, which is
        why rule N4 excludes news from walk-forward optimisation."""
        return self.revision_seq == 1


# =============================================================================
# 8. ANALYSIS CHAIN  (SPEC-P1.1-DOMAIN section 7)
# =============================================================================


class Candidate(_Frozen):
    """An instrument that passed the Tier-1 deterministic screen for one trading_date."""

    candidate_id: UUID
    instrument_id: UUID
    market: Market
    trading_date: date
    rank: Annotated[int, Field(ge=1)]
    filters_passed: tuple[str, ...]
    #: ADR-14 makes universe membership an immutable versioned artifact; a backtest must
    #: select membership AS OF the decision date.
    universe_version: UUID

    @field_validator("filters_passed")
    @classmethod
    def _non_empty(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if not v:
            raise ValueError("a candidate must record which filters it passed")
        return v


class Score(_Frozen):
    """A DETERMINISTIC model output. Never produced by an LLM.

    [CONST-2]: an LLM does not size, and a score feeds sizing. LLM output is a Thesis,
    which is a different type with different rules.

    feature_vector_hash is not decoration: ADR-07 requires reproducibility and ADR-08
    requires promotion accounting, and neither is possible if the exact input vector to a
    score cannot be identified after the fact.
    """

    score_id: UUID
    instrument_id: UUID
    trading_date: date
    kind: ScoreKind
    value: Fraction01
    model_id: Annotated[str, Field(min_length=1)]
    model_version: Annotated[str, Field(min_length=1)]
    feature_vector_hash: Sha256Hex
    computed_at: UtcDatetime


#: ADR-13, treated as irreversible: median 15 trading days, band 3-40, hard max 120.
HOLDING_MIN_SESSIONS: Final[int] = 3
HOLDING_MAX_SESSIONS: Final[int] = 40
HOLDING_HARD_MAX_SESSIONS: Final[int] = 120


class Signal(_Frozen):
    """A directional recommendation with a horizon. Not a decision - it has passed no
    risk gate."""

    signal_id: UUID
    instrument_id: UUID
    trading_date: date
    direction: SignalDirection
    strength: Fraction01
    horizon_sessions: Annotated[int, Field(ge=HOLDING_MIN_SESSIONS, le=HOLDING_MAX_SESSIONS)]
    is_llm_derived: bool = False
    model_id: Annotated[str, Field(min_length=1)]
    computed_at: UtcDatetime

    @model_validator(mode="after")
    def _check(self) -> Signal:
        if self.is_llm_derived:
            raise LlmOutputNotPermitted(
                "[CONST-2]: an LLM does not issue signals. LLM output is a Thesis, which "
                "carries no direction and no size."
            )
        return self


class InvalidationCondition(_Frozen):
    """A deterministic, machine-evaluable predicate. Not free text."""

    condition_id: UUID
    kind: InvalidationKind
    threshold_price: Price | None = None
    threshold_sessions: Annotated[int, Field(ge=1, le=HOLDING_HARD_MAX_SESSIONS)] | None = None
    threshold_value: DecimalStr | None = None
    description: Annotated[str, Field(min_length=1, max_length=500)]

    @model_validator(mode="after")
    def _check(self) -> InvalidationCondition:
        required: Mapping[InvalidationKind, str] = {
            InvalidationKind.PRICE_BELOW: "threshold_price",
            InvalidationKind.ATR_STOP: "threshold_price",
            InvalidationKind.TIME_STOP: "threshold_sessions",
            InvalidationKind.FUNDAMENTAL_BREACH: "threshold_value",
            InvalidationKind.NEWS_EVENT: "threshold_value",
        }
        field = required[self.kind]
        if getattr(self, field) is None:
            raise ValueError(
                f"{self.kind.value} requires {field}; a condition that cannot be "
                f"evaluated automatically is not an invalidation condition"
            )
        return self


class Thesis(_Frozen):
    """The ONLY LLM-derived model in this file, shaped by what an LLM may not do.

    It has NO quantity field, NO price field, NO weight field and NO limit field. This is
    the type-level expression of [CONST-2]: an LLM never sizes a position. The fields do
    not exist, so there is no code path that could read one.

    llm.may_receive_portfolio_state = false is IMMUTABLE (P0.1 section 10.2). The
    construction path takes a Candidate and sanitised facts - never a Portfolio, NAV,
    Account or Position. The blast radius of a successful prompt injection is capped at
    one candidate's thesis.
    """

    thesis_id: UUID
    candidate_id: UUID
    instrument_id: UUID
    trading_date: date
    bull_case: Annotated[str, Field(min_length=1, max_length=4000)]
    bear_case: Annotated[str, Field(min_length=1, max_length=4000)]
    invalidation_conditions: tuple[InvalidationCondition, ...]
    #: The LLM's self-reported certainty. EXPLICITLY UNTRUSTED and never used for sizing.
    #: Distinct from Regime.confidence - see the glossary.
    stated_confidence: Fraction01
    model_id: Annotated[str, Field(min_length=1)]
    prompt_version: Annotated[str, Field(min_length=1)]
    sanitiser_version: Annotated[str, Field(min_length=1)]
    #: Hashes of the exact untrusted inputs that produced this thesis, so a sanitiser bug
    #: is retroactively identifiable.
    input_content_hashes: tuple[Sha256Hex, ...]
    #: X2 finding F-10. [CONST-5]: the audit event is written BEFORE the action
    #: takes effect, so every effectful record names it. P1.2's DDL carried this
    #: column; P1.1 omitted the field.
    audit_event_id: UUID
    generated_at: UtcDatetime

    @model_validator(mode="after")
    def _check(self) -> Thesis:
        if not self.invalidation_conditions:
            raise ValueError(
                "a thesis requires at least one invalidation condition ([RS section 13]); "
                "a thesis that cannot be falsified is not a thesis"
            )
        if not self.input_content_hashes:
            raise UnsanitisedContentError(
                "a thesis must name the sanitised inputs that produced it (rule N14)"
            )
        return self


class RiskVerdict(_Frozen):
    """Frozen, binary, and non-overridable.

    Invariant I2 and ADR-09's final row: overriding a single risk DENY has no approver and
    no code path. Concretely, in this module: RiskVerdict has no mutating method and no
    non-frozen variant; no function accepts force/override/bypass/ignore_risk; Decision
    raises RiskDenyIsFinal if handed a DENY; hitl.risk_deny_override_permitted is
    immutable false.

    ADR-09 states why: if a human can override one DENY, [CONST-1] is decorative, because
    the AI need only persuade the human. The permitted action is to change the LIMIT - an
    audited policy change with its own approval and 24-hour SLA - and let the engine
    re-evaluate deterministically.

    It has no state machine because it has no lifecycle. A changed input produces a NEW
    verdict with a new id; there is no mutation path to audit.
    """

    verdict_id: UUID
    request_id: UUID
    instrument_id: UUID
    pool_id: PoolId
    decision: RiskDecision
    #: Which limit bound, by name. Null only on ALLOW.
    binding_constraint: str | None = None
    #: INFORMATIONAL on DENY so the sizer may re-propose once. The re-proposal is
    #: evaluated from scratch. This is not the risk engine sizing the position.
    max_permissible_quantity: Quantity | None = None
    limits_evaluated: tuple[str, ...]
    nav_snapshot_id: UUID
    evaluated_at: UtcDatetime
    audit_event_id: UUID

    @model_validator(mode="after")
    def _check(self) -> RiskVerdict:
        if not self.limits_evaluated:
            raise ValueError(
                "a verdict must record every limit evaluated, or it is not reproducible "
                "from the audit trail"
            )
        if self.decision is RiskDecision.DENY and not self.binding_constraint:
            raise ValueError("a DENY must name the binding constraint")
        return self


class Decision(_Frozen):
    """The final actionable output for one instrument on one trading_date.

    [DEFAULT-8] - this is where [CONST-2] becomes STRUCTURAL rather than conventional:
      - risk_verdict_id is required and non-null, always
      - risk_decision MUST be ALLOW; a DENY raises RiskDenyIsFinal
      - audit_event_id is required: the audit event written BEFORE the decision takes
        effect ([CONST-5]) - if the audit write fails, the action does not happen
      - thesis_id is OPTIONAL

    That last point is the point. The deterministic path produces decisions with no LLM
    involvement; the LLM path can only ANNOTATE a decision the deterministic path and the
    risk engine have already permitted. There is no constructor that turns a Thesis into a
    Decision.
    """

    decision_id: UUID
    instrument_id: UUID
    market: Market
    pool_id: PoolId
    trading_date: date
    action: DecisionAction
    target_quantity: Quantity
    limit_price: Price | None = None
    #: Invariant I6 carries these through to the order.
    strategy_version: Annotated[str, Field(min_length=1)]
    model_id: Annotated[str, Field(min_length=1)]
    risk_verdict_id: UUID
    risk_decision: RiskDecision
    signal_id: UUID | None = None
    thesis_id: UUID | None = None
    audit_event_id: UUID
    decided_at: UtcDatetime

    @model_validator(mode="after")
    def _gate(self) -> Decision:
        if self.risk_decision is not RiskDecision.ALLOW:
            raise RiskDenyIsFinal(
                f"Decision {self.decision_id} carries risk verdict "
                f"{self.risk_decision.value}. Invariant I2 / ADR-09: a risk DENY has no "
                f"approver and no override path. Change the LIMIT (an audited policy "
                f"change) and let the engine re-evaluate."
            )
        if self.action is not DecisionAction.NO_TRADE and self.target_quantity.is_zero():
            raise ValueError(f"{self.action.value} requires a non-zero target_quantity")
        if self.action is DecisionAction.NO_TRADE and not self.target_quantity.is_zero():
            raise ValueError("NO_TRADE requires target_quantity == 0")
        if self.pool_id.market is not self.market:
            raise ValueError(f"{self.pool_id.value} is not a {self.market.value} pool")
        # X2 finding F-4. Invariant I1 forbids implicit conversion, but nothing
        # stopped a US decision from carrying an INR limit price: the mismatch would
        # surface downstream as a CurrencyMismatchError inside the risk engine, or -
        # worse - not at all, if the price only ever reached the broker adapter.
        if (
            self.limit_price is not None
            and self.limit_price.currency is not self.pool_id.currency
        ):
            raise CurrencyMismatchError(
                f"{self.pool_id.value} trades in {self.pool_id.currency.value}, but "
                f"limit_price is {self.limit_price.currency.value}"
            )
        return self


# =============================================================================
# 9. RISK AND SIZING  (SPEC-P1.1-DOMAIN section 8)
# =============================================================================


class PositionSizeRequest(_Frozen):
    """Sizing is deterministic and is NOT an LLM output [CONST-2].

    The stop is entry - 2.5*ATR(14) at entry ([CONST]), where ATR(14) uses 14 COMPLETED
    bars and excludes today's partial bar (enforced by Bar.is_final).
    """

    request_id: UUID
    instrument_id: UUID
    pool_id: PoolId
    signal_id: UUID
    entry_price: Price
    stop_price: Price
    nav_snapshot_id: UUID
    settled_cash: Money
    regime: RegimeLabel
    requested_at: UtcDatetime

    @model_validator(mode="after")
    def _check(self) -> PositionSizeRequest:
        if self.entry_price.currency is not self.stop_price.currency:
            raise CurrencyMismatchError("entry and stop prices in different currencies")
        if self.settled_cash.currency is not self.pool_id.currency:
            raise CurrencyMismatchError(
                f"{self.pool_id.value} settles in {self.pool_id.currency.value}, got "
                f"{self.settled_cash.currency.value}"
            )
        if self.stop_price >= self.entry_price:
            raise InvalidStopError(
                f"stop {self.stop_price.value} >= entry {self.entry_price.value}: either "
                f"a sign error or a data error, and sizing off it produces an unbounded "
                f"position"
            )
        return self


# =============================================================================
# 10. EXECUTION  (SPEC-P1.1-DOMAIN sections 11.1)
# =============================================================================

#: Legal OrderState transitions. Terminal states have NO outgoing transitions.
#: Non-obvious cells are real broker behaviour, not defensive programming:
#:   PENDING_NEW -> FILLED    a marketable order fills before the ack arrives
#:   PENDING_CANCEL -> FILLED a cancel races a fill and loses; treating the cancel as
#:                            authoritative is how systems double-sell
#:   any -> UNKNOWN           the broker became unreachable or answered ambiguously
ORDER_TRANSITIONS: Final[Mapping[OrderState, frozenset[OrderState]]] = {
    OrderState.PENDING_NEW: frozenset(
        {
            OrderState.NEW,
            OrderState.PARTIALLY_FILLED,
            OrderState.FILLED,
            OrderState.CANCELED,
            OrderState.REJECTED,
            OrderState.EXPIRED,
            OrderState.UNKNOWN,
        }
    ),
    OrderState.NEW: frozenset(
        {
            OrderState.PARTIALLY_FILLED,
            OrderState.FILLED,
            OrderState.PENDING_CANCEL,
            OrderState.CANCELED,
            OrderState.PENDING_REPLACE,
            OrderState.EXPIRED,
            OrderState.UNKNOWN,
        }
    ),
    OrderState.PARTIALLY_FILLED: frozenset(
        {
            OrderState.PARTIALLY_FILLED,
            OrderState.FILLED,
            OrderState.PENDING_CANCEL,
            OrderState.CANCELED,
            OrderState.PENDING_REPLACE,
            OrderState.EXPIRED,
            OrderState.UNKNOWN,
        }
    ),
    OrderState.PENDING_CANCEL: frozenset(
        {
            OrderState.PARTIALLY_FILLED,
            OrderState.FILLED,
            OrderState.CANCELED,
            OrderState.EXPIRED,
            OrderState.UNKNOWN,
        }
    ),
    OrderState.PENDING_REPLACE: frozenset(
        {
            OrderState.NEW,
            OrderState.PARTIALLY_FILLED,
            OrderState.FILLED,
            OrderState.PENDING_CANCEL,
            OrderState.CANCELED,
            OrderState.REPLACED,
            OrderState.EXPIRED,
            OrderState.UNKNOWN,
        }
    ),
    OrderState.UNKNOWN: frozenset(
        {
            OrderState.NEW,
            OrderState.PARTIALLY_FILLED,
            OrderState.FILLED,
            OrderState.CANCELED,
            OrderState.REJECTED,
            OrderState.EXPIRED,
        }
    ),
    OrderState.FILLED: frozenset(),
    OrderState.CANCELED: frozenset(),
    OrderState.REJECTED: frozenset(),
    OrderState.EXPIRED: frozenset(),
    OrderState.REPLACED: frozenset(),
}

TERMINAL_ORDER_STATES: Final[frozenset[OrderState]] = frozenset(
    {
        OrderState.FILLED,
        OrderState.CANCELED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
        OrderState.REPLACED,
    }
)


def assert_order_transition(
    from_state: OrderState, to_state: OrderState, order_id: UUID
) -> None:
    """The order is NOT mutated on failure; the caller writes a reconciliation event."""
    if to_state not in ORDER_TRANSITIONS[from_state]:
        raise IllegalOrderTransition(
            f"order {order_id}: {from_state.value} -> {to_state.value} is illegal. "
            + (
                "A fill arriving on a terminal order is a reconciliation incident, not an "
                "update."
                if from_state in TERMINAL_ORDER_STATES
                else "See SPEC-P1.1-DOMAIN section 11.1."
            )
        )


def parse_order_state(vendor_code: str) -> OrderState:
    """A broker state we do not model maps to UNKNOWN, never to the nearest-looking
    member [DEFAULT-10]."""
    try:
        return OrderState(vendor_code.strip().upper())
    except ValueError:
        return OrderState.UNKNOWN


class Order(_Frozen):
    """Invariant I6: every order carries strategy_version, model_id and a broker
    idempotency key.

    [CONST-9] / SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013: a unique
    strategy ID per order - harmless on US orders, mandatory on Indian ones.

    Rule N12: brokers without a documented idempotency key (Zerodha, and Upstox until M-9
    closes) get client-side dedupe - a persisted intent row written before the call and
    reconciled against the order book after it. client_order_id is that intent key.
    """

    order_id: UUID
    decision_id: UUID
    #: X2 finding F-9. The stated invariant is "unique client_order_id PER ACCOUNT",
    #: and P1.2 enforces it as UNIQUE (account_id, client_order_id) - but P1.1's Order
    #: carried no account, so the domain could not express the scope its own
    #: uniqueness rule is defined over. Two accounts may legitimately reuse an intent
    #: id; one account may never.
    account_id: UUID
    instrument_id: UUID
    market: Market
    pool_id: PoolId
    side: OrderSide
    order_type: OrderType
    time_in_force: TimeInForce
    quantity: Quantity
    limit_price: Price | None = None
    stop_price: Price | None = None
    state: OrderState
    filled_quantity: Quantity
    #: Broker idempotency key / client intent key (invariant I6, rule N12). Charset is
    #: unverified for Alpaca - carried open item M-1.
    client_order_id: Annotated[str, Field(min_length=1, max_length=128)]
    broker_order_id: str | None = None
    broker_id: Annotated[str, Field(min_length=1)]
    strategy_version: Annotated[str, Field(min_length=1)]
    strategy_id: Annotated[str, Field(min_length=1)]
    model_id: Annotated[str, Field(min_length=1)]
    audit_event_id: UUID
    placed_at: UtcDatetime
    #: Kill-switch liquidation is EXEMPT from settled_cash and day_trades_5d (ADR-13
    #: Chain D). A good-faith violation is a 90-day inconvenience; an uncontrolled
    #: drawdown is permanent. The exemption is audited and alerted on.
    kill_switch_exempt: bool = False

    @model_validator(mode="after")
    def _check(self) -> Order:
        if self.order_type is OrderType.LIMIT and self.limit_price is None:
            raise ValueError(
                "a LIMIT order requires limit_price; it never defaults to the last trade"
            )
        if self.order_type is OrderType.MARKET and self.limit_price is not None:
            raise ValueError("a MARKET order must not carry a limit_price")
        if self.order_type in {OrderType.STOP, OrderType.STOP_LIMIT} and self.stop_price is None:
            raise ValueError(f"{self.order_type.value} requires stop_price")
        if self.side is OrderSide.SELL and self.quantity.is_zero():
            raise ValueError("a SELL order requires a non-zero quantity")
        if self.filled_quantity > self.quantity:
            raise OverfillError(
                f"order {self.order_id}: filled {self.filled_quantity.value} exceeds "
                f"quantity {self.quantity.value}"
            )
        if self.pool_id.market is not self.market:
            raise ValueError(f"{self.pool_id.value} is not a {self.market.value} pool")
        # X2 finding F-4, order path.
        for name in ("limit_price", "stop_price"):
            px = getattr(self, name)
            if px is not None and px.currency is not self.pool_id.currency:
                raise CurrencyMismatchError(
                    f"{self.pool_id.value} trades in {self.pool_id.currency.value}, "
                    f"but {name} is {px.currency.value}"
                )
        return self

    def remaining(self) -> Quantity:
        return self.quantity - self.filled_quantity

    def is_complete(self, qty_increment: Decimal) -> bool:
        """An order completes when the remainder falls BELOW the tradeable increment, not
        only at exactly zero - otherwise it hangs in PARTIALLY_FILLED forever on a
        rounding dust remainder."""
        return self.remaining().value < qty_increment


class Fill(_Frozen):
    """Unique on (broker_id, broker_fill_id).

    Brokers re-send fills on reconnect; without this key a replayed fill double-counts a
    position. Re-receipt of a known key is a NO-OP, not an update.
    """

    fill_id: UUID
    order_id: UUID
    instrument_id: UUID
    broker_id: Annotated[str, Field(min_length=1)]
    broker_fill_id: Annotated[str, Field(min_length=1)]
    quantity: Quantity
    #: Any 6 dp value. Sub-penny price improvement is real at execution even where
    #: quoting is at $0.01. Tick validation applies to prices we SEND, never to prices
    #: the venue reports.
    price: Price
    fees: Money
    filled_at: UtcDatetime
    audit_event_id: UUID

    @model_validator(mode="after")
    def _check(self) -> Fill:
        if self.quantity.is_zero():
            raise ValueError("a fill must have a non-zero quantity")
        if self.fees.currency is not self.price.currency:
            raise CurrencyMismatchError("fee currency differs from fill price currency")
        return self

    def gross_notional(self) -> Money:
        return self.price.notional(self.quantity)

    def dedupe_key(self) -> tuple[str, str]:
        return (self.broker_id, self.broker_fill_id)


# =============================================================================
# 11. PORTFOLIO AND ACCOUNTING  (SPEC-P1.1-DOMAIN section 9)
# =============================================================================


class Lot(_Frozen):
    """One tax-accounting acquisition unit.

    Lot-level cost basis with a wash-sale adjustment field is MANDATORY FROM DAY ONE
    (ADR-13 Chain E): a 15-day median hold against a weekly-reconstituted universe means
    the system will routinely re-enter a name it exited inside the 30-day wash-sale window.

    cost_total is stored; PER-SHARE BASIS IS NEVER STORED. Storing it would force a
    division, make lot arithmetic non-closed, and lose a cent on every partial
    consumption. Partial consumption uses Money.allocate(), which is exact.

    [DEFAULT-6]: wash-sale fields are US-only. India has no wash-sale rule (ADR-13 Chain
    E), so a populated field on an IN lot is a data-integrity error that would corrupt the
    India tax export.
    """

    lot_id: UUID
    instrument_id: UUID
    market: Market
    pool_id: PoolId
    opened_on: date
    quantity_opened: Quantity
    quantity_remaining: Quantity
    cost_total: Money
    fees_total: Money
    opening_fill_id: UUID
    cost_basis_method: CostBasisMethod = CostBasisMethod.FIFO
    wash_sale_disallowed_loss: Money | None = None
    wash_sale_adjusted_basis: Money | None = None
    #: X2 finding F-10. [CONST-5]: the audit event is written BEFORE the action
    #: takes effect, so every effectful record names it. P1.2's DDL carried this
    #: column; P1.1 omitted the field.
    audit_event_id: UUID

    @model_validator(mode="after")
    def _check(self) -> Lot:
        if self.quantity_opened.is_zero():
            raise ValueError("a lot must open with a non-zero quantity")
        if self.quantity_remaining > self.quantity_opened:
            raise ValueError("quantity_remaining exceeds quantity_opened")
        if self.cost_total.currency is not self.pool_id.currency:
            raise CurrencyMismatchError(
                f"{self.pool_id.value} accounts in {self.pool_id.currency.value}"
            )
        if self.fees_total.currency is not self.cost_total.currency:
            raise CurrencyMismatchError("fee currency differs from cost currency")
        if self.market is Market.IN and (
            self.wash_sale_disallowed_loss is not None
            or self.wash_sale_adjusted_basis is not None
        ):
            raise WashSaleNotApplicableError(
                "India has no wash-sale rule (ADR-13 Chain E) [DEFAULT-6]; a populated "
                "wash-sale field on an IN lot would corrupt the India tax export"
            )
        return self

    def is_closed(self) -> bool:
        """A fully consumed lot is RETAINED FOREVER - it is the tax record."""
        return self.quantity_remaining.is_zero()

    def _basis_for(self, held: Quantity) -> Money:
        """Basis attributable to `held` shares OF THE ORIGINAL LOT.

        Always allocated against `quantity_opened`, which never changes.

        X2 finding F-1 (BLOCKER). This model previously allocated against
        `quantity_remaining`, which re-divides the FULL original basis across a
        shrinking denominator: every consumption after the first over-stated its
        basis, corrupting realised P&L, the wash-sale adjustment (ADR-13 Chain E) and
        the tax export.
        """
        if held.is_zero():
            return Money.zero(self.cost_total.currency)
        if held == self.quantity_opened:
            return self.cost_total
        unheld = self.quantity_opened - held
        held_part, _unheld_part = self.cost_total.allocate([held.value, unheld.value])
        return held_part

    def remaining_cost(self) -> Money:
        """Basis still attached to this lot. What a position marks against."""
        return self._basis_for(self.quantity_remaining)

    def consumed_cost(self, quantity: Quantity) -> Money:
        """Basis released by consuming `quantity` from this lot, right now.

        Computed by TELESCOPING the remaining basis:

            basis(remaining) - basis(remaining - quantity)

        Telescoping is what makes a consumption path exactly additive. Allocating each
        consumption independently would not be: largest-remainder over [30, 70] and
        then over [20, 80] can place a minor unit differently than a single allocation
        over [30, 20, 50], and the cents would not sum back to `cost_total`.

        Worked, on the case F-1 caught - a lot of 100 shares for $1,000.00 with 50
        already sold:
            remaining_cost()  = basis(50)             = $500.00
            consumed_cost(25) = basis(50) - basis(25)
                              = $500.00 - $250.00     = $250.00   (was $500.00)
        """
        if quantity > self.quantity_remaining:
            raise ValueError(
                f"cannot consume {quantity.value} from a lot with "
                f"{self.quantity_remaining.value} remaining"
            )
        if quantity.is_zero():
            return Money.zero(self.cost_total.currency)
        return self._basis_for(self.quantity_remaining) - self._basis_for(
            self.quantity_remaining - quantity
        )

    def derived_basis_per_share(self) -> Price:
        """For REPORTING only. Never persisted, never used in lot arithmetic."""
        if self.quantity_opened.is_zero():
            raise ValueError("cannot derive per-share basis from a zero-quantity lot")
        with _domain_context():
            raw = self.cost_total.amount / self.quantity_opened.value
        return Price(value=raw, currency=self.cost_total.currency)


#: Legal PositionState transitions (SPEC-P1.1-DOMAIN section 11.2).
#:   PENDING_OPEN -> CLOSED   the opening order was cancelled or rejected with zero fills
#:   OPEN -> CLOSED           ILLEGAL directly: something must have been sent to the
#:                            broker. A position that appears closed with no exit order is
#:                            a reconciliation event
#:   CLOSED -> UNRECONCILED   a late fill or broker restatement must be able to reopen the
#:                            question
POSITION_TRANSITIONS: Final[Mapping[PositionState, frozenset[PositionState]]] = {
    PositionState.PENDING_OPEN: frozenset(
        {PositionState.OPEN, PositionState.CLOSED, PositionState.UNRECONCILED}
    ),
    PositionState.OPEN: frozenset(
        {PositionState.PENDING_CLOSE, PositionState.UNRECONCILED}
    ),
    PositionState.PENDING_CLOSE: frozenset(
        {PositionState.OPEN, PositionState.CLOSED, PositionState.UNRECONCILED}
    ),
    PositionState.CLOSED: frozenset({PositionState.UNRECONCILED}),
    PositionState.UNRECONCILED: frozenset({PositionState.OPEN, PositionState.CLOSED}),
}


def assert_position_transition(
    from_state: PositionState, to_state: PositionState, instrument_id: UUID
) -> None:
    if to_state not in POSITION_TRANSITIONS[from_state]:
        raise IllegalPositionTransition(
            f"position {instrument_id}: {from_state.value} -> {to_state.value} is "
            f"illegal. See SPEC-P1.1-DOMAIN section 11.2."
        )


class Position(_Frozen):
    """The PROJECTION over open lots for one (instrument_id, pool_id). Derived, never the
    authority.

    ADR-10: THE BROKER IS THE SYSTEM OF RECORD for positions and cash. Our database is a
    derived, richer view (lots, cost basis, thesis linkage). On any disagreement the
    broker wins for quantity and the discrepancy is escalated - never silently corrected
    in one direction.

    UNRECONCILED expresses that rule. Per ADR-10: while ANY position is UNRECONCILED the
    risk engine treats it as full-size risk and DENIES ALL NEW ENTRIES ACROSS THE ENTIRE
    POOL. Note the scope - pool-wide, not instrument-wide.
    """

    instrument_id: UUID
    market: Market
    pool_id: PoolId
    state: PositionState
    lots: tuple[Lot, ...]
    opened_on: date | None = None
    thesis_id: UUID | None = None
    stop_price: Price | None = None
    broker_reported_quantity: Quantity | None = None

    @model_validator(mode="after")
    def _check(self) -> Position:
        for lot in self.lots:
            if lot.instrument_id != self.instrument_id or lot.pool_id is not self.pool_id:
                raise ValueError("lot does not belong to this position")
        if self.state is PositionState.CLOSED and not self.quantity().is_zero():
            raise IllegalPositionTransition(
                "a CLOSED position must hold zero remaining quantity"
            )
        return self

    def quantity(self) -> Quantity:
        total = Quantity.zero()
        for lot in self.lots:
            total = total + lot.quantity_remaining
        return total

    def cost_basis(self) -> Money:
        """Basis still attached to the open lots.

        Uses `remaining_cost()`, not `consumed_cost(quantity_remaining)` — X2 finding
        F-1: the latter answered "what would I release if I sold it all", which the
        pre-fix implementation returned as the untouched `cost_total`.
        """
        total = Money.zero(self.pool_id.currency)
        for lot in self.lots:
            if not lot.is_closed():
                total = total + lot.remaining_cost()
        return total

    def market_value(self, mark: Price) -> Money:
        if mark.currency is not self.pool_id.currency:
            raise CurrencyMismatchError("mark currency differs from pool currency")
        return mark.notional(self.quantity())

    def fifo_lots(self) -> tuple[Lot, ...]:
        """FIFO consumption order (P0.1 section 6)."""
        return tuple(
            sorted(
                (lot for lot in self.lots if not lot.is_closed()),
                key=lambda lot: (lot.opened_on, str(lot.lot_id)),
            )
        )

    def blocks_new_entries(self) -> bool:
        """ADR-10: one UNRECONCILED position denies new entries POOL-WIDE."""
        return self.state is PositionState.UNRECONCILED


class Portfolio(_Frozen):
    """Projection over positions for ONE pool. Pools are segregated (ADR-15): no
    cross-margining, no cross-pool netting."""

    pool_id: PoolId
    trading_date: date
    positions: tuple[Position, ...]

    @model_validator(mode="after")
    def _check(self) -> Portfolio:
        seen: set[UUID] = set()
        for p in self.positions:
            if p.pool_id is not self.pool_id:
                raise ValueError(f"position in {p.pool_id.value} inside {self.pool_id.value}")
            if p.instrument_id in seen:
                raise ValueError(f"duplicate position for {p.instrument_id}")
            seen.add(p.instrument_id)
        return self

    def open_positions(self) -> tuple[Position, ...]:
        return tuple(p for p in self.positions if p.state is not PositionState.CLOSED)

    def has_unreconciled(self) -> bool:
        """True -> the risk engine denies all new entries across this entire pool."""
        return any(p.blocks_new_entries() for p in self.positions)


class Account(_Frozen):
    """ADR-12: AccountType.CASH in v1.

    BOTH settlement counters exist in v1 so a future switch to margin is a config change
    rather than a re-derivation (ADR-13 Chain D):

      settled_cash   CASH (v1)      new entries sized against SETTLED cash only; a buy
                                    that would consume unsettled proceeds is DENIED
      day_trades_5d  MARGIN (future) while equity < $25,000, deny all new entries when
                                    day_trades_5d >= 3, because any new position could
                                    stop out the same session and become the fourth

    day_trades_5d is computed and stored even in a cash account, where it is not enforced,
    so the counter is proven correct before it ever becomes binding.

    Correction R-1 (P0.1 section 0.4): [RS section 16] names PDT as the binding US
    constraint. Given ADR-12's cash account it is NOT - PDT is a margin-account rule
    (ASSUMPTION [VERIFY-P0.2]) and the binding constraint is settled funds.
    """

    account_id: UUID
    pool_id: PoolId
    market: Market
    account_type: AccountType
    broker_id: Annotated[str, Field(min_length=1)]
    equity: Money
    total_cash: Money
    settled_cash: Money
    #: Rolling 5 EXCHANGE BUSINESS DAYS for the relevant market - not calendar days, not
    #: the other market's days (P0.1 section 6).
    day_trades_5d: Annotated[int, Field(ge=0)]
    as_of: UtcDatetime

    @model_validator(mode="after")
    def _check(self) -> Account:
        currency = self.pool_id.currency
        for name in ("equity", "total_cash", "settled_cash"):
            if getattr(self, name).currency is not currency:
                raise CurrencyMismatchError(
                    f"{name} must be denominated in {currency.value}"
                )
        if self.settled_cash > self.total_cash:
            raise ValueError("settled_cash cannot exceed total_cash")
        if self.pool_id.market is not self.market:
            raise ValueError(f"{self.pool_id.value} is not a {self.market.value} pool")
        return self

    def entry_buying_power(self) -> Money:
        """ADR-13 Chain D: new entries are sized against SETTLED cash only."""
        if self.account_type is AccountType.CASH:
            return self.settled_cash
        return self.total_cash


class FxRate(_Frozen):
    """ADR-15 section 5. Immutable once written.

    A past date's rate is NEVER re-fetched or corrected in place: NAV history must be
    reproducible, and a silently revised rate rewrites history.
    """

    fx_rate_id: UUID
    as_of_date: date
    base: Currency
    quote: Currency
    rate: DecimalStr
    source: Annotated[str, Field(min_length=1)]
    retrieved_at: UtcDatetime

    @model_validator(mode="before")
    @classmethod
    def _quantise(cls, data: Any) -> Any:
        if not isinstance(data, dict) or data.get("rate") is None:
            return data
        rate = _to_decimal(data["rate"], "FxRate.rate")
        if rate <= 0:
            raise MissingFxRateError(f"fx rate must be > 0, got {rate}")
        quantum = Decimal(1).scaleb(FX_RATE_EXPONENT)
        return {**data, "rate": rate.quantize(quantum, rounding=MONEY_ROUNDING)}

    @model_validator(mode="after")
    def _check(self) -> FxRate:
        if self.base is self.quote:
            raise MissingFxRateError("base and quote currency are identical")
        return self

    def convert(self, amount: Money) -> Money:
        """The ONLY conversion in the system, and it happens only inside the consolidated
        NAV snapshot - a single, audited, dated computation.

        fx.system_may_convert = false is immutable: this converts for REPORTING. It never
        moves money.
        """
        if amount.currency is not self.base:
            raise CurrencyMismatchError(
                f"rate converts {self.base.value}->{self.quote.value}, got "
                f"{amount.currency.value}"
            )
        return Money.quantise(amount.amount * self.rate, self.quote)


class PoolNAV(_Frozen):
    """Local currency, on that exchange's own trading_date.

    ADR-15 section 3: position limits are per-pool, in local currency. `position <= 5%`
    means 5% of THAT POOL's NAV, because that is the capital actually available to the
    trade. A consolidated-NAV position limit would authorise an India position larger than
    the entire India pool.
    """

    nav_id: UUID
    pool_id: PoolId
    trading_date: date
    total_value: Money
    cash: Money
    positions_value: Money
    peak_value: Money
    is_stale_holiday: bool = False
    #: X2 finding F-10. [CONST-5]: the audit event is written BEFORE the action
    #: takes effect, so every effectful record names it. P1.2's DDL carried this
    #: column; P1.1 omitted the field.
    audit_event_id: UUID
    computed_at: UtcDatetime

    @model_validator(mode="after")
    def _check(self) -> PoolNAV:
        currency = self.pool_id.currency
        for name in ("total_value", "cash", "positions_value", "peak_value"):
            if getattr(self, name).currency is not currency:
                raise CurrencyMismatchError(f"{name} must be in {currency.value}")
        return self

    def drawdown_pct(self) -> Decimal:
        """Peak-to-trough, from the running peak RESTORED FROM THE AUDIT TRAIL.

        Invariant I4 / ADR-10: peak NAV is replayed from the append-only audit trail,
        never recomputed from current portfolio state - recomputation resets peak to the
        present value and silently un-trips the drawdown condition. The kill switch would
        forget why it fired.
        """
        if self.peak_value.amount <= 0:
            return Decimal(0)
        drop = self.peak_value.amount - self.total_value.amount
        if drop <= 0:
            return Decimal(0)
        with _domain_context():
            ratio = drop / self.peak_value.amount
        return _quantise(ratio, Decimal("0.000001"), MONEY_ROUNDING)


class ConsolidatedNAV(_Frozen):
    """USD base, on the UTC ACCOUNTING DATE (ADR-15 section 7).

    ADR-15 section 4: loss and drawdown limits are enforced BOTH per-pool AND
    consolidated; the stricter binds. A per-pool breach halts that pool; a consolidated
    breach trips the GLOBAL kill switch. Without per-pool enforcement a 10% loss in a small
    India pool reads as ~1% consolidated and never trips the kill switch.

    ADR-15 section 6: FX translation appears as its OWN line, never blended into trading
    P&L, so a good year in India is neither flattered nor hidden by a rupee move.
    """

    nav_id: UUID
    utc_accounting_date: date
    total_value_usd: Money
    peak_value_usd: Money
    pool_navs: tuple[PoolNAV, ...]
    fx_rate_ids: tuple[UUID, ...]
    translation_effect_usd: Money
    #: X2 finding F-10. [CONST-5]: the audit event is written BEFORE the action
    #: takes effect, so every effectful record names it. P1.2's DDL carried this
    #: column; P1.1 omitted the field.
    audit_event_id: UUID
    computed_at: UtcDatetime

    @model_validator(mode="after")
    def _check(self) -> ConsolidatedNAV:
        for name in ("total_value_usd", "peak_value_usd", "translation_effect_usd"):
            if getattr(self, name).currency is not Currency.USD:
                raise CurrencyMismatchError(f"{name} must be USD (fx.base_currency)")
        if not self.pool_navs:
            raise MissingFxRateError(
                "a consolidated NAV requires at least one pool NAV; while India is "
                "unfunded NAV_IN = 0 and the computation runs anyway (ADR-15), "
                "exercising the code path daily"
            )
        non_usd = {p.pool_id.currency for p in self.pool_navs} - {Currency.USD}
        if non_usd and not self.fx_rate_ids:
            raise MissingFxRateError(
                "no FX rate for the accounting date. Invariant I10: consolidated limits "
                "cannot be evaluated, so NO NEW ENTRIES ARE PERMITTED IN EITHER POOL. "
                "Never carried forward, never interpolated, never defaulted."
            )
        return self


# =============================================================================
# 12. CONTROL PLANE  (SPEC-P1.1-DOMAIN section 10)
# =============================================================================


class Regime(_Frozen):
    """UNKNOWN is a real value with a real behaviour: it is the FAIL-CLOSED regime.

    A regime the classifier cannot determine does not become SIDEWAYS by default; P2.9
    treats UNKNOWN as no-new-entries.

    `confidence` here is the classifier's probability output - pinned by the glossary and
    distinct from Thesis.stated_confidence, which is the LLM's self-report and is never
    used for sizing.
    """

    regime_id: UUID
    market: Market
    trading_date: date
    label: RegimeLabel
    confidence: Fraction01
    model_id: Annotated[str, Field(min_length=1)]
    computed_at: UtcDatetime

    def permits_new_entries(self) -> bool:
        return self.label is not RegimeLabel.UNKNOWN


#: Legal KillSwitchState transitions (SPEC-P1.1-DOMAIN section 11.3).
#: The asymmetry is the entire design: every transition TOWARD halt is automatic, every
#: transition AWAY from halt requires a human (ADR-09 row 1, Owner, no SLA, no auto-expiry,
#: no auto-re-enable). TRIPPED -> POOL_HALTED is illegal: there is no partial de-escalation.
KILL_SWITCH_TRANSITIONS: Final[Mapping[KillSwitchState, frozenset[KillSwitchState]]] = {
    KillSwitchState.ARMED: frozenset(
        {KillSwitchState.POOL_HALTED, KillSwitchState.TRIPPED}
    ),
    KillSwitchState.POOL_HALTED: frozenset(
        {KillSwitchState.ARMED, KillSwitchState.TRIPPED}
    ),
    KillSwitchState.TRIPPED: frozenset({KillSwitchState.ARMED}),
}

#: Transitions that MAY NOT happen automatically. Each requires an ApprovalGrant whose
#: nonce is single-use, so a blanket or standing approval is structurally impossible.
HUMAN_ONLY_KILL_SWITCH_TRANSITIONS: Final[
    frozenset[tuple[KillSwitchState, KillSwitchState]]
] = frozenset(
    {
        (KillSwitchState.POOL_HALTED, KillSwitchState.ARMED),
        (KillSwitchState.TRIPPED, KillSwitchState.ARMED),
    }
)

#: Invariant I3 / ADR-10 section 4 / killswitch.restore_state_on_boot - IMMUTABLE.
BOOT_KILL_SWITCH_STATE: Final[KillSwitchState] = KillSwitchState.TRIPPED


def assert_kill_switch_transition(
    from_state: KillSwitchState,
    to_state: KillSwitchState,
    approval_id: UUID | None,
) -> None:
    """There is no force_arm(), no reset(), and no path to ARMED without an approval_id."""
    if to_state not in KILL_SWITCH_TRANSITIONS[from_state]:
        raise IllegalKillSwitchTransition(
            f"{from_state.value} -> {to_state.value} is illegal. There is no partial "
            f"de-escalation: a global trip clears to ARMED by a human, or not at all."
        )
    if (from_state, to_state) in HUMAN_ONLY_KILL_SWITCH_TRANSITIONS and approval_id is None:
        raise IllegalKillSwitchTransition(
            f"{from_state.value} -> {to_state.value} requires an ADR-09 row 1 Owner "
            f"approval. No SLA, no auto-expiry, no auto-re-enable: an unattended trip "
            f"leaves the system flat and halted until a human acts."
        )


class KillSwitch(_Frozen):
    """Infrastructure-level halt, independent of the AI path ([CONST-7])."""

    kill_switch_id: UUID
    scope: KillSwitchScope
    pool_id: PoolId | None = None
    state: KillSwitchState
    reason: str | None = None
    tripped_at: UtcDatetime | None = None
    tripped_by: str | None = None
    re_enable_approval_id: UUID | None = None
    audit_event_id: UUID

    @model_validator(mode="after")
    def _check(self) -> KillSwitch:
        if self.scope is KillSwitchScope.POOL and self.pool_id is None:
            raise ValueError("a POOL-scoped kill switch requires a pool_id")
        if self.scope is KillSwitchScope.GLOBAL and self.pool_id is not None:
            raise ValueError("a GLOBAL kill switch must not name a pool")
        if self.state is not KillSwitchState.ARMED and self.reason is None:
            raise ValueError("a halted or tripped kill switch must record its reason")
        if self.state is KillSwitchState.ARMED and self.re_enable_approval_id is None:
            # Boot and first-arm both go through an Owner approval; there is no
            # constructor that yields ARMED without one.
            raise IllegalKillSwitchTransition(
                "ARMED requires re_enable_approval_id: no code path arms the switch "
                "without an ADR-09 row 1 Owner approval (invariant I3)"
            )
        return self

    @classmethod
    def at_boot(cls, kill_switch_id: UUID, audit_event_id: UUID) -> KillSwitch:
        """Boot is NOT a transition.

        On every start the state is TRIPPED unconditionally, regardless of the state
        before the incident. Invariant I3, ADR-10 section 4, [CONST-6], [CONST-7].
        """
        return cls(
            kill_switch_id=kill_switch_id,
            scope=KillSwitchScope.GLOBAL,
            state=BOOT_KILL_SWITCH_STATE,
            reason="restored TRIPPED on boot (invariant I3, immutable)",
            audit_event_id=audit_event_id,
        )

    def permits_trading(self) -> bool:
        return self.state is KillSwitchState.ARMED


# ---------------------------------------------------------------------------
# AuditEvent and verify_audit_chain lived here in v0.1-v0.2. Both are SUPERSEDED
# by `audit.events.AuditEnvelope` and `audit.chain.verify_chain`
# (SPEC-P1.4-AUDIT §4, §6).
#
# P1.1 [DEFAULT-9] split the envelope from the catalogue: "P1.1 owns the chained
# envelope, P1.4 owns the event catalogue." Building P1.4 showed that the split
# produces TWO models of one concept - the real envelope needs causation_id,
# schema_version, input_hash and a reproducibility bundle, and a domain-layer
# copy lacking them is a second definition free to drift from the one that
# actually writes rows. One type for one thing.
#
# What P1.1 still owns is `AuditEventClass` above: an ENUM that the domain, the
# storage layer and the audit layer all type against, and which audit.events
# IMPORTS rather than redefines.
# ---------------------------------------------------------------------------


class RunContext(_Frozen):
    """Every pipeline invocation carries one.

    is_paper carries more weight than it looks. Rule N11 [V]: paper-trading results are
    PLUMBING EVIDENCE ONLY - no slippage, fill-quality, fee or edge conclusion may cite
    paper data. Stamping is_paper on the run context, and thence on every audit event, is
    what makes that rule mechanically checkable rather than a discipline. P5.3's cost
    model filters on it.

    is_backtest carries invariant I9: LLM-derived features never enter walk-forward
    optimisation.

    code_version and config_hash exist because ADR-07 requires reproducibility and ADR-08
    requires promotion accounting; a result that cannot name the code and config that
    produced it cannot be promoted.
    """

    run_id: UUID
    run_type: RunType
    market: Market
    trading_date: date
    started_at: UtcDatetime
    #: X2 finding F-5. P1.2 stores and updates this; P1.1 had no field for it.
    #: None means the run is still in flight.
    finished_at: UtcDatetime | None = None
    code_version: Annotated[str, Field(min_length=7, max_length=40)]
    config_hash: Sha256Hex
    strategy_version: Annotated[str, Field(min_length=1)]
    model_id: Annotated[str, Field(min_length=1)]
    is_paper: bool
    is_backtest: bool

    @model_validator(mode="after")
    def _check(self) -> RunContext:
        if self.run_type is RunType.BACKTEST and not self.is_backtest:
            raise ValueError("RunType.BACKTEST requires is_backtest=True")
        if self.run_type is RunType.PAPER and not self.is_paper:
            raise ValueError("RunType.PAPER requires is_paper=True")
        if self.is_paper and self.is_backtest:
            raise ValueError(
                "a run is paper or backtest, never both; conflating them would let a "
                "backtest result be cited as paper plumbing evidence and vice versa"
            )
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at precedes started_at")
        return self

    def may_cite_for_cost_model(self) -> bool:
        """Rule N11: only live runs produce citable slippage, fee and edge evidence."""
        return not self.is_paper and not self.is_backtest


__all__ = [
    # errors
    "DomainError", "CurrencyMismatchError", "MoneyPrecisionError",
    "FloatContaminationError", "TickSizeViolation", "MissingTickRegimeError",
    "AmbiguousTickRegimeError", "NegativeQuantityError", "QuantityIncrementError",
    "MissingReferenceDataError", "NaiveDatetimeError", "MissingSessionError",
    "UnknownSymbolError", "AmbiguousSymbolError", "UnknownCorporateActionError",
    "CorporateActionCalendarError", "BarIntegrityError", "CrossedQuoteError",
    "StaleDataError", "UnsanitisedContentError", "MissingFxRateError",
    "WashSaleNotApplicableError", "InvalidStopError", "RiskDenyIsFinal",
    "AuditWriteRequiredError", "LlmOutputNotPermitted",
    "IllegalOrderTransition", "OverfillError",
    "IllegalPositionTransition", "IllegalKillSwitchTransition",
    # decimal
    "build_domain_context", "install_domain_decimal_context", "DECIMAL_PRECISION",
    "MONEY_ROUNDING", "QUANTITY_ROUNDING", "PRICE_EXPONENT", "QUANTITY_EXPONENT",
    "FX_RATE_EXPONENT",
    # enums
    "Market", "Exchange", "Currency", "PoolId", "InstrumentType", "InstrumentStatus",
    "AccountType", "ApproverRole", "CostBasisMethod", "CorporateActionType",
    "SessionType", "BarInterval", "ScoreKind", "SignalDirection", "DecisionAction",
    "InvalidationKind", "RiskDecision", "RegimeLabel", "OrderSide", "OrderType",
    "TimeInForce", "OrderState", "PositionState", "KillSwitchState", "KillSwitchScope",
    "RunType", "StalenessAction", "AuditEventClass",
    # allowlists
    "TRADEABLE_INSTRUMENT_TYPES_V1", "READ_ONLY_INSTRUMENT_TYPES_V1",
    "PERMANENTLY_BANNED_INSTRUMENT_TYPES",
    # numeric types
    "Money", "Price", "Quantity",
    # time
    "ExchangeSession", "TradingCalendar", "UtcDatetime",
    # identity
    "Instrument", "SymbolMapping", "SuccessorLink", "CorporateAction",
    "resolve_instrument", "resolve_symbol", "parse_corporate_action_type",
    # market data
    "StalenessPolicy", "Bar", "Quote", "Trade", "FundamentalsSnapshot", "NewsItem",
    # analysis
    "Candidate", "Score", "Signal", "InvalidationCondition", "Thesis", "RiskVerdict",
    "Decision", "PositionSizeRequest",
    # execution
    "Order", "Fill", "ORDER_TRANSITIONS", "TERMINAL_ORDER_STATES",
    "assert_order_transition", "parse_order_state",
    # portfolio
    "Lot", "Position", "Portfolio", "Account", "FxRate", "PoolNAV", "ConsolidatedNAV",
    "POSITION_TRANSITIONS", "assert_position_transition",
    # control
    "Regime", "KillSwitch", "RunContext", "KILL_SWITCH_TRANSITIONS",
    "HUMAN_ONLY_KILL_SWITCH_TRANSITIONS", "BOOT_KILL_SWITCH_STATE",
    "assert_kill_switch_transition",
    # holding period (ADR-13)
    "HOLDING_MIN_SESSIONS", "HOLDING_MAX_SESSIONS", "HOLDING_HARD_MAX_SESSIONS",
]
