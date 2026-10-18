"""SPEC-CR1-US-DAY-TRADING verification. Pins every regulatory number of the spec's typed form
so that none can change without this file changing with it.

Pattern: the historical tests/verify_p13_config.py (require() instead of assert, check() collecting
PASS and FAIL, every t_ function run in sorted order, exit code 1 on any failure).
"""
import re
import sys
from datetime import date
from decimal import Decimal as D
from pathlib import Path

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "docs" / "new specs" / "SPEC-CR1-US-DAY-TRADING.md"
INDEX = ROOT / "docs" / "new specs" / "DECISIONS.md"
HISTORICAL_POLICY = ROOT / "config" / "policy.yaml"


def require(cond, msg=""):
    """Unconditional check. Replaces bare `assert`, which `python -O` strips (X5 GAP-2)."""
    if not cond:
        raise AssertionError(msg)


PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
    except Exception as e:  # noqa: BLE001
        FAIL.append(f"{name}: {type(e).__name__}: {e}")


def raises(exc, fn):
    try:
        fn()
    except exc:
        return
    except Exception as e:  # noqa: BLE001
        raise AssertionError(f"expected {exc.__name__}, got {type(e).__name__}: {e}") from e
    raise AssertionError(f"expected {exc.__name__}, nothing raised")


SPEC_TEXT = SPEC.read_text(encoding="utf-8")
_section = SPEC_TEXT[SPEC_TEXT.index("## 10. Typed form"):]
_block = re.search(r"```python\n(.*?)```", _section, re.S).group(1)
NS = {"__name__": "spec_cr1"}
exec(compile(_block, f"{SPEC.name}#section-10", "exec"), NS)  # noqa: S102
Rules = NS["UsDayTradingRules"]
RULES = NS["US_DAY_TRADING_RULES"]
Policy = NS["BrokerDayTradingPolicy"]
ALPACA = NS["ALPACA_DAY_TRADING_POLICY"]

# The pinned values, written out a second time. Changing one place without the other fails.
PINNED = {
    "finra_rule": "FINRA Rule 4210",
    "amending_filing": "SR-FINRA-2025-017",
    "sec_release": "34-105226",
    "federal_register_cite": "91 FR 20731",
    "finra_notice": "Regulatory Notice 26-10",
    "sec_approval_date": date(2026, 4, 14),
    "federal_register_date": date(2026, 4, 17),
    "finra_notice_date": date(2026, 4, 20),
    "effective_date": date(2026, 6, 4),
    "phase_in_end_date": date(2027, 10, 20),
    "current_pdt_minimum_equity_usd": None,
    "current_day_trade_count_limit": None,
    "legacy_pdt_minimum_equity_usd": 25000,
    "legacy_pattern_day_trades": 4,
    "legacy_window_business_days": 5,
    "intraday_deficit_expiry_business_days": 15,
    "intraday_freeze_trigger_business_days": 5,
    "intraday_freeze_calendar_days": 90,
    "intraday_practice_exclusion_fraction": D("0.05"),
    "intraday_practice_exclusion_usd": 1000,
    "margin_initial_minimum_equity_usd": 2000,
    "margin_maintenance_long_fraction": D("0.25"),
    "us_settlement_business_days": 1,
    "regt_payment_period_extra_business_days": 2,
    "regt_cash_freeze_calendar_days": 90,
    "regt_disregard_usd": 1000,
    "business_day_calendar": "NYSE",
    "business_day_timezone": "America/New_York",
}

# A value each pinned field must refuse.
WRONG = {
    "finra_rule": "FINRA Rule 4211",
    "amending_filing": "SR-FINRA-2025-018",
    "sec_release": "34-104572",
    "federal_register_cite": "91 FR 1580",
    "finra_notice": "Regulatory Notice 26-11",
    "sec_approval_date": date(2026, 4, 15),
    "federal_register_date": date(2026, 4, 18),
    "finra_notice_date": date(2026, 4, 21),
    "effective_date": date(2026, 6, 5),
    "phase_in_end_date": date(2027, 10, 21),
    "current_pdt_minimum_equity_usd": 25000,
    "current_day_trade_count_limit": 3,
    "legacy_pdt_minimum_equity_usd": 25001,
    "legacy_pattern_day_trades": 3,
    "legacy_window_business_days": 6,
    "intraday_deficit_expiry_business_days": 14,
    "intraday_freeze_trigger_business_days": 4,
    "intraday_freeze_calendar_days": 89,
    "intraday_practice_exclusion_fraction": D("0.050001"),
    "intraday_practice_exclusion_usd": 999,
    "margin_initial_minimum_equity_usd": 2500,
    "margin_maintenance_long_fraction": D("0.30"),
    "us_settlement_business_days": 2,
    "regt_payment_period_extra_business_days": 1,
    "regt_cash_freeze_calendar_days": 91,
    "regt_disregard_usd": 1001,
    "business_day_calendar": "NASDAQ",
    "business_day_timezone": "UTC",
}


# ---- the typed form holds exactly the verified values ---------------------------------
def t_every_field_is_pinned():
    fields = set(Rules.model_fields)
    require(fields == set(PINNED), f"unpinned or missing: {sorted(fields ^ set(PINNED))}")


def t_values_match_the_pins():
    for name, expected in PINNED.items():
        got = getattr(RULES, name)
        require(got == expected and type(got) is type(expected),
                f"{name}: {got!r} != {expected!r}")


def t_current_pdt_rule_has_no_number():
    require(RULES.current_pdt_minimum_equity_usd is None, "a current PDT floor must not exist")
    require(RULES.current_day_trade_count_limit is None, "a current day-trade limit must not exist")


def t_every_pinned_field_refuses_another_value():
    for name, bad in WRONG.items():
        raises(ValidationError, lambda n=name, b=bad: Rules(**{n: b}))


def t_unknown_field_is_refused():
    raises(ValidationError, lambda: Rules(pdt_equity_floor_usd=25000))


def t_rules_are_frozen():
    raises(ValidationError, lambda: setattr(RULES, "legacy_pdt_minimum_equity_usd", 30000))


def t_phase_in_ends_after_effective_date():
    require(RULES.phase_in_end_date > RULES.effective_date > RULES.sec_approval_date)


# ---- broker policy --------------------------------------------------------------------
def t_alpaca_does_not_enforce_legacy_pdt():
    require(ALPACA.legacy_pdt_enforced is False, ALPACA.legacy_pdt_enforced)
    require(str(ALPACA.source_url).startswith("https://alpaca.markets/"), ALPACA.source_url)


def t_broker_policy_is_strict():
    base = ALPACA.model_dump()
    raises(ValidationError, lambda: Policy(**(base | {"legacy_pdt_enforced": "false"})))
    raises(ValidationError, lambda: Policy(**(base | {"broker_id": "zerodha"})))


# ---- registers --------------------------------------------------------------------------
def t_new_run_register_carries_the_result():
    idx = INDEX.read_text(encoding="utf-8")
    for n in (55, 56, 57, 58):
        require(f"| DEFAULT-{n} |" in idx, f"DEFAULT-{n} missing from the index")
    require("FALSIFIED as current" in idx and "SPEC-CR1-US-DAY-TRADING" in idx,
            "the PDT result is not in DECISIONS.md section 3")


def t_historical_policy_divergence_is_recorded():
    """The historical config still says 25000. This pins that line too: if it changes, the
    spec's record of the divergence (section 7) must be revisited, so neither drifts silently."""
    lines = [ln.split("#")[0].strip() for ln in
             HISTORICAL_POLICY.read_text(encoding="utf-8").splitlines()
             if "pdt_equity_floor_usd" in ln]
    require(lines == ["pdt_equity_floor_usd: 25000"], lines)
    require("account.pdt_equity_floor_usd" in SPEC_TEXT, "section 7 no longer records the divergence")


for _n, _f in sorted((n, f) for n, f in list(globals().items()) if n.startswith("t_")):
    check(_n, _f)

print(f"PASSED {len(PASS)}")
for f in FAIL:
    print("FAILED", f)
sys.exit(1 if FAIL else 0)
