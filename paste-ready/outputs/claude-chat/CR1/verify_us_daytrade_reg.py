"""SPEC-P2.9-US-DAYTRADE-REG verification. Pins the US day-trading / cash-account
regulatory facts so no value can drift silently. Same runner pattern as
tests/verify_p13_config.py: require() not assert (survives python -O), every t_* runs,
non-zero exit on any failure."""
import re
import sys
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from regulatory import us_daytrade as R  # noqa: E402

# Changing ANY fact changes this hash. Updating it requires the same commit to update
# STAGE-0-FREEZE §6.5 and cite the new primary source.
PINNED_FACTS_SHA256 = "d3895e19666ee12e44af9ff45aaa6b34fc589dc9cbb2733b1310d6a7ef078399"


def require(cond, msg=""):
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


# ---- the pin -----------------------------------------------------------------
def t_facts_hash_is_pinned():
    require(R.FACTS_SHA256 == PINNED_FACTS_SHA256,
            f"regulatory facts changed: {R.FACTS_SHA256} != pinned {PINNED_FACTS_SHA256}")


def t_fact_keys_are_unique():
    keys = [f.key for f in R.FACTS]
    require(len(keys) == len(set(keys)), "duplicate fact key")


# ---- the PDT floor: verified, and verified RETIRED ---------------------------
def t_pdt_floor_is_25000_and_retired():
    f = R.fact("us.pdt.min_equity_usd")
    require(D(f.value) == D("25000"), f.value)
    require(f.status is R.FactStatus.RETIRED, f.status)
    require(f.effective_to == date(2026, 6, 4), f.effective_to)
    require("4210(f)(8)(B)(iv)a." in f.citation and "34-105226" in f.citation, f.citation)


def t_pdt_count_and_window_retired():
    for k, v in (("us.pdt.day_trades_in_window", "4"), ("us.pdt.window_business_days", "5")):
        f = R.fact(k)
        require(f.value == v and f.status is R.FactStatus.RETIRED, k)


def t_no_retired_fact_is_in_force():
    for f in R.FACTS:
        if f.status is R.FactStatus.RETIRED:
            require(f.effective_to is not None and f.effective_to <= date.today(), f.key)


# ---- replacement regime (margin accounts; not applicable to ADR-12 cash) -----
def t_intraday_margin_dates():
    require(R.fact("us.intraday_margin.effective_date").value == "2026-06-04")
    require(R.fact("us.intraday_margin.member_phase_in_end").value == "2027-10-20")


def t_intraday_margin_freeze_parameters():
    require(R.fact("us.intraday_margin.freeze_trigger_business_days").value == "5")
    require(R.fact("us.intraday_margin.freeze_calendar_days").value == "90")
    require(R.fact("us.intraday_margin.deficit_lapse_business_days").value == "15")
    require(D(R.fact("us.intraday_margin.de_minimis_pct_equity").value) == D("0.05"))
    require(D(R.fact("us.intraday_margin.de_minimis_usd").value) == D("1000"))
    for f in R.FACTS:
        if f.key.startswith("us.intraday_margin."):
            require(f.status is R.FactStatus.NOT_APPLICABLE,
                    f"{f.key}: becomes binding only if ADR-12 (cash account) changes")


# ---- what actually binds a cash account --------------------------------------
def t_regt_and_settlement_in_force():
    f = R.fact("us.regt.cash_freeze_calendar_days")
    require(f.value == "90" and f.status is R.FactStatus.IN_FORCE, f)
    s = R.fact("us.settlement.cycle_business_days")
    require(s.value == "1" and s.status is R.FactStatus.IN_FORCE, s)


def t_retired_fact_without_end_is_rejected():
    raises(Exception, lambda: R.RegulatoryFact(
        key="x.y", value="1", unit="u", status=R.FactStatus.RETIRED, citation="0123456789"))


# ---- REGT-001 / REGT-002 fail closed -----------------------------------------
def _inp(**kw):
    base = dict(settled_cash_usd=D("1000.00"), open_buy_notional_usd=D("0"),
                unsettled_buy_cost_usd=D("0"),
                fee_reserve_usd=D("5.00"), proposed_buy_notional_usd=D("500"),
                broker_restriction_active=False)
    base.update(kw)
    return R.EntryFundingInput(**base)


def t_funded_entry_allowed():
    v, _ = R.evaluate_entry_funding(_inp())
    require(v is R.FundingVerdict.ALLOW)


def t_boundary_is_inclusive():
    v, _ = R.evaluate_entry_funding(_inp(proposed_buy_notional_usd=D("995.00")))
    require(v is R.FundingVerdict.ALLOW, "exactly-available must be allowed")
    v, _ = R.evaluate_entry_funding(_inp(proposed_buy_notional_usd=D("995.01")))
    require(v is R.FundingVerdict.DENY, "one cent over must be denied")


def t_open_buys_consume_settled_cash():
    v, _ = R.evaluate_entry_funding(_inp(open_buy_notional_usd=D("600")))
    require(v is R.FundingVerdict.DENY)


def t_unsettled_buys_consume_settled_cash():
    v, _ = R.evaluate_entry_funding(_inp(unsettled_buy_cost_usd=D("495.01")))
    require(v is R.FundingVerdict.DENY, "a same-day filled buy must reduce what can be spent")


def t_unknown_cash_denies():
    v, why = R.evaluate_entry_funding(_inp(settled_cash_usd=None))
    require(v is R.FundingVerdict.DENY and "missing input" in why, why)


def t_unknown_or_active_restriction_denies():
    for flag in (None, True):
        v, _ = R.evaluate_entry_funding(_inp(broker_restriction_active=flag))
        require(v is R.FundingVerdict.DENY, flag)


# ---- nobody re-introduces the PDT floor as a live limit ----------------------
_PDT = re.compile(r"(pdt|pattern[_ ]?day)", re.I)
_25K = re.compile(r"25[_,]?000")
_ALLOWED = {Path("src/regulatory/us_daytrade.py")}


def t_no_live_pdt_floor_in_src_or_config():
    hits = []
    for base in (ROOT / "src", ROOT / "config"):
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.suffix not in {".py", ".yaml", ".yml", ".toml", ".json"}:
                continue
            if p.relative_to(ROOT) in _ALLOWED:
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if _PDT.search(line) and _25K.search(line):
                    hits.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    require(not hits, "retired PDT floor referenced as a value:\n" + "\n".join(hits))


for _n, _f in sorted((n, f) for n, f in list(globals().items()) if n.startswith("t_")):
    check(_n, _f)

print(f"PASSED {len(PASS)}")
for f in FAIL:
    print("FAILED", f)
sys.exit(1 if FAIL else 0)
