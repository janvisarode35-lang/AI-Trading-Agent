"""US day-trading and cash-account regulatory facts, pinned.

SPEC-P2.9-US-DAYTRADE-REG v0.1. Every value here is a REGULATORY FACT with a primary
source, not a tunable. Changing any field changes FACTS_SHA256, which
tests/verify_us_daytrade_reg.py pins - so a change cannot land without a deliberate,
reviewed edit to both files and to STAGE-0-FREEZE §6.5.

Finding that drives this module: the FINRA pattern-day-trader $25,000 floor in
Rule 4210(f)(8)(B)(iv)a. was ELIMINATED, effective 2026-06-04 (SEC Rel. 34-105226,
FINRA Reg. Notice 26-10). It is recorded below as RETIRED history, never as a live limit.
The system runs a long-only CASH account (ADR-12); the binding US constraint is
Regulation T 12 CFR 220.8 (free-riding / 90-day freeze), enforced by SETTLED-CASH-ONLY
funding of every purchase.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FactStatus(StrEnum):
    IN_FORCE = "IN_FORCE"   # binds this system today
    RETIRED = "RETIRED"     # historical only; must never be enforced
    NOT_APPLICABLE = "NOT_APPLICABLE"  # in force for others, not for a cash account


class RegulatoryFact(BaseModel):
    """One pinned regulatory value. Violation of any validator = refuse to import."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_.]+$")
    value: str = Field(min_length=1, description="Canonical string; Decimal/int/date text.")
    unit: str = Field(min_length=1)
    status: FactStatus
    citation: str = Field(min_length=10)
    effective_from: date | None = None
    effective_to: date | None = Field(default=None, description="Exclusive.")

    @model_validator(mode="after")
    def _retired_needs_end(self) -> "RegulatoryFact":
        if self.status is FactStatus.RETIRED and self.effective_to is None:
            raise ValueError(f"{self.key}: RETIRED fact requires effective_to")
        if self.effective_from and self.effective_to and self.effective_to <= self.effective_from:
            raise ValueError(f"{self.key}: effective_to must follow effective_from")
        return self


_SEC_105226 = "SEC Rel. 34-105226 (2026-04-14), 91 FR 20731; FINRA Reg. Notice 26-10 (2026-04-20)"
_REGT = "12 CFR 220.8 (Regulation T, cash account)"

FACTS: tuple[RegulatoryFact, ...] = (
    RegulatoryFact(key="us.pdt.min_equity_usd", value="25000", unit="USD",
                   status=FactStatus.RETIRED,
                   citation="Former FINRA Rule 4210(f)(8)(B)(iv)a.; eliminated by " + _SEC_105226,
                   effective_from=None, effective_to=date(2026, 6, 4)),
    RegulatoryFact(key="us.pdt.day_trades_in_window", value="4", unit="day_trades",
                   status=FactStatus.RETIRED,
                   citation="Former FINRA Rule 4210(f)(8)(B)(ii); eliminated by " + _SEC_105226,
                   effective_to=date(2026, 6, 4)),
    RegulatoryFact(key="us.pdt.window_business_days", value="5", unit="business_days",
                   status=FactStatus.RETIRED,
                   citation="Former FINRA Rule 4210(f)(8)(B)(ii); eliminated by " + _SEC_105226,
                   effective_to=date(2026, 6, 4)),
    RegulatoryFact(key="us.intraday_margin.effective_date", value="2026-06-04", unit="date",
                   status=FactStatus.NOT_APPLICABLE, citation=_SEC_105226 + "; Rule 4210(d)(2)",
                   effective_from=date(2026, 6, 4)),
    RegulatoryFact(key="us.intraday_margin.member_phase_in_end", value="2027-10-20", unit="date",
                   status=FactStatus.NOT_APPLICABLE, citation="FINRA Reg. Notice 26-10, Implementation",
                   effective_from=date(2026, 6, 4)),
    RegulatoryFact(key="us.intraday_margin.freeze_trigger_business_days", value="5",
                   unit="business_days", status=FactStatus.NOT_APPLICABLE,
                   citation="FINRA Rule 4210(d)(2)(D) per Reg. Notice 26-10",
                   effective_from=date(2026, 6, 4)),
    RegulatoryFact(key="us.intraday_margin.freeze_calendar_days", value="90", unit="calendar_days",
                   status=FactStatus.NOT_APPLICABLE,
                   citation="FINRA Rule 4210(d)(2)(D) per Reg. Notice 26-10",
                   effective_from=date(2026, 6, 4)),
    RegulatoryFact(key="us.intraday_margin.deficit_lapse_business_days", value="15",
                   unit="business_days", status=FactStatus.NOT_APPLICABLE,
                   citation="FINRA Rule 4210(d)(2)(C)(iii) per Reg. Notice 26-10",
                   effective_from=date(2026, 6, 4)),
    RegulatoryFact(key="us.intraday_margin.de_minimis_pct_equity", value="0.05", unit="fraction",
                   status=FactStatus.NOT_APPLICABLE,
                   citation="FINRA Rule 4210(d)(2)(D)(i) per Reg. Notice 26-10",
                   effective_from=date(2026, 6, 4)),
    RegulatoryFact(key="us.intraday_margin.de_minimis_usd", value="1000", unit="USD",
                   status=FactStatus.NOT_APPLICABLE,
                   citation="FINRA Rule 4210(d)(2)(D)(i) per Reg. Notice 26-10",
                   effective_from=date(2026, 6, 4)),
    RegulatoryFact(key="us.regt.cash_freeze_calendar_days", value="90", unit="calendar_days",
                   status=FactStatus.IN_FORCE, citation=_REGT + " paragraph (c)(1)"),
    RegulatoryFact(key="us.settlement.cycle_business_days", value="1", unit="business_days",
                   status=FactStatus.IN_FORCE,
                   citation="SEC Rule 15c6-1(a) as amended, Rel. 34-96930; compliance 2024-05-28",
                   effective_from=date(2024, 5, 28)),
)


def canonical_facts_bytes() -> bytes:
    rows = [f.model_dump(mode="json") for f in sorted(FACTS, key=lambda f: f.key)]
    return json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")


FACTS_SHA256: str = hashlib.sha256(canonical_facts_bytes()).hexdigest()


def fact(key: str) -> RegulatoryFact:
    for f in FACTS:
        if f.key == key:
            return f
    raise KeyError(key)


# ---------------------------------------------------------------------------
# REGT-001: settled-cash-only funding. The one rule that binds a cash account.
# ---------------------------------------------------------------------------
class EntryFundingInput(BaseModel):
    """All money in USD as Decimal, 2dp max for cash, unrounded for notional."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    settled_cash_usd: Decimal | None = Field(description="Broker-reported settled cash; None = unknown.")
    open_buy_notional_usd: Decimal = Field(ge=0, description="Limit price x remaining qty of all open buys.")
    unsettled_buy_cost_usd: Decimal = Field(ge=0, description=(
        "Our ledger's cost of filled-but-unsettled buys. Always subtracted: if the broker's "
        "settled figure already nets them we double-count, which errs toward DENY (fail-closed)."))
    fee_reserve_usd: Decimal = Field(ge=0)
    proposed_buy_notional_usd: Decimal = Field(gt=0, description="limit_price x qty of the new order.")
    broker_restriction_active: bool | None = Field(description="Any broker freeze/restriction flag; None = unknown.")


class FundingVerdict(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


def evaluate_entry_funding(x: EntryFundingInput) -> tuple[FundingVerdict, str]:
    """Deterministic, fail-closed. Applies to position-INCREASING orders only.

    Sells of fully-paid shares are permitted by 12 CFR 220.8(a)(2)(i) and are not gated here
    (their gating is A-14's question, not this rule's).
    """
    if x.settled_cash_usd is None:
        return FundingVerdict.DENY, "REGT-001 missing input: settled_cash_usd"
    if x.broker_restriction_active is None:
        return FundingVerdict.DENY, "REGT-002 missing input: broker_restriction_active"
    if x.broker_restriction_active:
        return FundingVerdict.DENY, "REGT-002 broker restriction active"
    # Unsettled SALE proceeds are never added: spending them is the free-riding path (220.8(c)).
    available = (x.settled_cash_usd - x.open_buy_notional_usd
                 - x.unsettled_buy_cost_usd - x.fee_reserve_usd)
    if x.proposed_buy_notional_usd > available:
        return FundingVerdict.DENY, (
            f"REGT-001 proposed {x.proposed_buy_notional_usd} > settled available {available}")
    return FundingVerdict.ALLOW, "REGT-001 funded from settled cash"
