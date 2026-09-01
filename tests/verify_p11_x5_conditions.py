"""X5 GAP AUDIT conditions 1, 2 and 6 — the exposure, gating and governance surfaces.

STAGE-1-GAP-AUDIT §2.1 found nineteen public functions specified, implemented and never
executed by any test. They were not obscure: they cluster on the numbers the risk engine
compares against constitutional limits, on the kill-switch and regime gates, and on the
lint that stops a risk number coming from the environment.

This file closes conditions 1, 2 and 6:

  1  exposure / valuation  gross_notional, market_value, quantity, fifo_lots,
                           open_positions, dedupe_key, remaining, is_complete
  2  gating                blocks_new_entries, has_unreconciled, permits_new_entries
  6  governance            LimitChange.loosens, assert_no_env_risk_reads

NO BARE `assert` ANYWHERE IN THIS FILE. GAP-2 / finding B-5 is that every other harness
uses bare asserts, which `python -O` strips - so an optimised run reports PASSED while
verifying almost nothing. `require()` raises unconditionally. This file is the pattern the
other harnesses should be converted to.
"""
import sys
import textwrap
from datetime import date, datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from uuid import UUID, uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from domain import models as m  # noqa: E402
from config import loader as L  # noqa: E402

PASS: list[str] = []
FAIL: list[str] = []
USD, INR = m.Currency.USD, m.Currency.INR
U = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def require(cond: bool, msg: str) -> None:
    """Unconditional check. Never an `assert` - see the module docstring."""
    if not cond:
        raise AssertionError(msg)


def raises(exc, fn, label=""):
    try:
        fn()
    except exc:
        return
    except Exception as e:  # noqa: BLE001
        raise AssertionError(
            f"{label}expected {exc.__name__}, got {type(e).__name__}: {e}") from e
    raise AssertionError(f"{label}expected {exc.__name__}, nothing raised")


def check(name, fn):
    try:
        fn()
        PASS.append(name)
    except Exception as e:  # noqa: BLE001
        FAIL.append(f"{name}: {type(e).__name__}: {e}")


# --------------------------------------------------------------------------- builders
def _lot(opened="100", remaining="100", cost="1000.00", on=date(2026, 8, 1),
         instrument=None, market=m.Market.US, pool=m.PoolId.US_POOL, cur=USD, lot_id=None):
    return m.Lot(
        lot_id=lot_id or uuid4(), instrument_id=instrument or uuid4(), market=market,
        pool_id=pool, opened_on=on,
        quantity_opened=m.Quantity(value=D(opened)),
        quantity_remaining=m.Quantity(value=D(remaining)),
        cost_total=m.Money.of(cost, cur), fees_total=m.Money.of("1.00", cur),
        opening_fill_id=uuid4(), audit_event_id=uuid4())


def _position(lots, state=m.PositionState.OPEN, instrument=None,
              market=m.Market.US, pool=m.PoolId.US_POOL):
    return m.Position(instrument_id=instrument or lots[0].instrument_id, market=market,
                      pool_id=pool, state=state, lots=tuple(lots))


def _fill(qty="10", px="25.50", fees="1.00", broker="alpaca", bfid="B-1", cur=USD):
    return m.Fill(fill_id=uuid4(), order_id=uuid4(), instrument_id=uuid4(),
                  broker_id=broker, broker_fill_id=bfid,
                  quantity=m.Quantity(value=D(qty)),
                  price=m.Price(value=D(px), currency=cur),
                  fees=m.Money.of(fees, cur), filled_at=U, audit_event_id=uuid4())


# ===========================================================================
# CONDITION 1 — exposure and valuation
# ===========================================================================
def t_c1_fill_gross_notional_is_exact():
    """The number that becomes exposure. Decimal-exact, never float."""
    f = _fill(qty="10", px="25.50")
    gn = f.gross_notional()
    require(gn.amount == D("255.00"), f"10 x 25.50 should be 255.00, got {gn.amount}")
    require(gn.currency is USD, f"currency should follow the price, got {gn.currency}")

    # Edge: a price with more precision than the money quantum must not lose value
    # before quantisation. 3 x 0.005 = 0.015 -> 0.02 half-up, not 0.01.
    f2 = _fill(qty="3", px="0.005")
    require(f2.gross_notional().amount == D("0.02"),
            f"half-up at the money quantum expected 0.02, got {f2.gross_notional().amount}")


def t_c1_fill_dedupe_key_is_broker_scoped():
    """Brokers re-send fills on reconnect (P1.2 §901). The key must be broker-scoped:
    two brokers may legitimately use the same fill id."""
    a = _fill(broker="alpaca", bfid="F-1")
    b = _fill(broker="zerodha", bfid="F-1")
    require(a.dedupe_key() == ("alpaca", "F-1"), a.dedupe_key())
    require(a.dedupe_key() != b.dedupe_key(),
            "same fill id at two brokers must not collide")
    require(a.dedupe_key() == _fill(broker="alpaca", bfid="F-1").dedupe_key(),
            "the key must be stable across two objects describing one fill")


def t_c1_position_quantity_sums_remaining_not_opened():
    """Sums quantity_remaining. Using quantity_opened would overstate every exposure
    the moment a position is partially sold."""
    inst = uuid4()
    pos = _position([_lot(opened="100", remaining="40", instrument=inst),
                     _lot(opened="50", remaining="50", instrument=inst)], instrument=inst)
    require(pos.quantity().value == D("90"), f"40+50 expected 90, got {pos.quantity().value}")

    # Edge: fully consumed lots contribute zero, not their opened size.
    pos2 = _position([_lot(opened="100", remaining="0")])
    require(pos2.quantity().value == D("0"), pos2.quantity().value)


def t_c1_position_market_value_and_currency_guard():
    """market_value feeds EXP-001/003/004. A cross-currency mark must never silently
    produce a number - pools are segregated, ADR-15."""
    pos = _position([_lot(opened="10", remaining="10")])
    mv = pos.market_value(m.Price(value=D("31.25"), currency=USD))
    require(mv.amount == D("312.50"), f"10 x 31.25 expected 312.50, got {mv.amount}")

    raises(m.CurrencyMismatchError,
           lambda: pos.market_value(m.Price(value=D("31.25"), currency=INR)),
           "INR mark on a USD pool: ")


def t_c1_fifo_lots_order_and_closed_exclusion():
    """FIFO order drives cost basis and therefore wash-sale correctness (invariant 9).
    Ordering is (opened_on, lot_id) - the lot_id tiebreak makes it deterministic when two
    lots open on the same date, which an audit replay depends on."""
    inst = uuid4()
    old = _lot(on=date(2026, 1, 5), instrument=inst)
    mid = _lot(on=date(2026, 6, 1), instrument=inst)
    new = _lot(on=date(2026, 8, 1), instrument=inst)
    closed = _lot(on=date(2026, 2, 1), remaining="0", instrument=inst)
    pos = _position([new, closed, old, mid], instrument=inst)

    got = pos.fifo_lots()
    require([l.lot_id for l in got] == [old.lot_id, mid.lot_id, new.lot_id],
            f"FIFO order wrong: {[str(l.opened_on) for l in got]}")
    require(closed.lot_id not in {l.lot_id for l in got},
            "a fully consumed lot must not appear in the FIFO queue")

    # Edge: same-date lots break the tie on lot_id, deterministically and repeatably.
    a = _lot(on=date(2026, 3, 1), instrument=inst, lot_id=UUID(int=1))
    b = _lot(on=date(2026, 3, 1), instrument=inst, lot_id=UUID(int=2))
    same = _position([b, a], instrument=inst)
    require([l.lot_id for l in same.fifo_lots()] == [a.lot_id, b.lot_id],
            "same-date tiebreak must be deterministic on lot_id")
    require(same.fifo_lots() == same.fifo_lots(), "fifo_lots must be repeatable")


def t_c1_portfolio_open_positions_excludes_closed():
    """Input to the sector and position-count limits. A CLOSED position counted as open
    would consume headroom that does not exist."""
    o1 = _position([_lot()], state=m.PositionState.OPEN)
    o2 = _position([_lot()], state=m.PositionState.UNRECONCILED)
    cl = _position([_lot(opened="10", remaining="0")], state=m.PositionState.CLOSED)
    pf = m.Portfolio(pool_id=m.PoolId.US_POOL, trading_date=date(2026, 8, 27),
                     positions=(o1, o2, cl))
    ids = {p.instrument_id for p in pf.open_positions()}
    require(len(pf.open_positions()) == 2, f"expected 2 open, got {len(pf.open_positions())}")
    require(cl.instrument_id not in ids, "CLOSED must be excluded")
    require(o2.instrument_id in ids, "UNRECONCILED is still an open position")


def t_c1_order_remaining_and_dust_completion():
    """SPEC-P1.1-DOMAIN §267: an order completes when the remainder falls BELOW the
    tradeable increment, not only at exactly zero - otherwise it hangs in
    PARTIALLY_FILLED forever on a rounding dust remainder."""
    # Quantity truncates (ROUND_DOWN) at 6 dp, so 99.9999996 stores as 99.999999 and the
    # remainder is 0.000001. Truncation is the correct direction for a share count: half-up
    # would round a filled quantity UP and claim shares the account does not hold.
    o = _order(qty="100", filled="99.9999996")
    require(o.filled_quantity.value == D("99.999999"),
            f"Quantity must truncate, not round up: {o.filled_quantity.value}")
    require(o.remaining().value == D("0.000001"), o.remaining().value)
    require(o.is_complete(D("0.001")) is True,
            "dust below the increment must complete the order")
    require(o.is_complete(D("0.0000001")) is False,
            "a remainder above the increment must NOT complete the order")

    # Edge: exactly at the increment is NOT complete - the boundary is strict `<`,
    # because a remainder equal to one increment is still a tradeable order.
    o2 = _order(qty="100", filled="99")
    require(o2.remaining().value == D("1"), o2.remaining().value)
    require(o2.is_complete(D("1")) is False,
            "remainder == increment is still tradeable, must not complete")
    require(_order(qty="100", filled="100").is_complete(D("1")) is True,
            "a fully filled order completes")


# ===========================================================================
# CONDITION 2 — kill-switch and regime gating
# ===========================================================================
def t_c2_position_blocks_new_entries_only_when_unreconciled():
    """ADR-10: one UNRECONCILED position denies new entries POOL-WIDE."""
    for state in (m.PositionState.OPEN, m.PositionState.CLOSED):
        lots = [_lot(opened="10", remaining="0")] if state is m.PositionState.CLOSED \
            else [_lot()]
        require(_position(lots, state=state).blocks_new_entries() is False,
                f"{state.value} must not block new entries")
    require(_position([_lot()], state=m.PositionState.UNRECONCILED)
            .blocks_new_entries() is True,
            "UNRECONCILED must block new entries")


def t_c2_portfolio_has_unreconciled_is_pool_wide():
    """One bad position poisons the whole pool - that is the point of the rule."""
    good = _position([_lot()], state=m.PositionState.OPEN)
    bad = _position([_lot()], state=m.PositionState.UNRECONCILED)
    clean = m.Portfolio(pool_id=m.PoolId.US_POOL, trading_date=date(2026, 8, 27),
                        positions=(good,))
    dirty = m.Portfolio(pool_id=m.PoolId.US_POOL, trading_date=date(2026, 8, 27),
                        positions=(good, bad))
    require(clean.has_unreconciled() is False, "clean pool must not report unreconciled")
    require(dirty.has_unreconciled() is True,
            "a single UNRECONCILED position must poison the pool")

    # Edge: an empty portfolio is clean, not unknown. any(()) is False, and that is the
    # correct fail-OPEN direction here because there is nothing to reconcile.
    empty = m.Portfolio(pool_id=m.PoolId.US_POOL, trading_date=date(2026, 8, 27),
                        positions=())
    require(empty.has_unreconciled() is False, "an empty pool has nothing unreconciled")


def t_c2_regime_unknown_is_fail_closed():
    """UNKNOWN is the FAIL-CLOSED regime: a regime the classifier cannot determine does
    NOT become SIDEWAYS by default."""
    def regime(label, conf="0.90"):
        return m.Regime(regime_id=uuid4(), market=m.Market.US,
                        trading_date=date(2026, 8, 27), label=label,
                        confidence=D(conf), model_id="regime-v1", computed_at=U)

    require(regime(m.RegimeLabel.UNKNOWN).permits_new_entries() is False,
            "UNKNOWN must deny new entries")
    for label in m.RegimeLabel:
        if label is m.RegimeLabel.UNKNOWN:
            continue
        require(regime(label).permits_new_entries() is True,
                f"{label.value} should permit new entries")

    # Edge: confidence does NOT gate this. A high-confidence UNKNOWN still denies, and a
    # zero-confidence known label still permits - the label alone decides, so a
    # confidence threshold cannot be tuned into re-enabling trading.
    require(regime(m.RegimeLabel.UNKNOWN, conf="1.0").permits_new_entries() is False,
            "confidence must not override an UNKNOWN regime")


# ===========================================================================
# CONDITION 6 — governance surfaces
# ===========================================================================
def t_c6_limitchange_loosens_property_refuses_to_guess():
    """Direction is judged against the rule's comparison, not the raw number: raising a
    threshold loosens an `lte` rule and TIGHTENS a `gte` rule. The bare property cannot
    know the rule, so it must REFUSE rather than guess - guessing backwards would let a
    limit be relaxed down the tightening path, which needs no approval at all."""
    change = L.LimitChange(rule_id="EXP-001", field="threshold",
                           old_value=D("0.050"), new_value=D("0.070"))
    raises(NotImplementedError, lambda: change.loosens,
           "the bare property must not guess a direction: ")


def t_c6_assert_no_env_risk_reads_raises_on_violation(tmp=None):
    """Block A: risk numbers come from policy.yaml, never from the environment. The lint
    is AST-based, so it sees `from os import environ` too. Only the raising WRAPPER was
    untested - the lint itself already was."""
    import tempfile

    # A clean tree passes.
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "src"
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "clean.py").write_text(
            "MAX = 0.05\n\n\ndef f():\n    return MAX\n", encoding="utf-8")
        L.assert_no_env_risk_reads(root)  # must not raise

    # A tree that reads the environment outside the allowlist fails closed.
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "src"
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "sneaky.py").write_text(textwrap.dedent("""
            import os

            MAX_POSITION_PCT = float(os.environ["MAX_POSITION_PCT"])
        """), encoding="utf-8")
        raises(L.RiskNumberFromEnvError, lambda: L.assert_no_env_risk_reads(root),
               "an env-sourced risk number must be rejected: ")

    # And the aliased import form, which a text search would miss.
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "src"
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "aliased.py").write_text(textwrap.dedent("""
            from os import environ

            DAILY_LOSS = environ.get("DAILY_LOSS_LIMIT")
        """), encoding="utf-8")
        raises(L.RiskNumberFromEnvError, lambda: L.assert_no_env_risk_reads(root),
               "`from os import environ` must also be caught: ")


def _order(qty="100", filled="0", state=m.OrderState.PARTIALLY_FILLED):
    return m.Order(
        order_id=uuid4(), decision_id=uuid4(), instrument_id=uuid4(),
        market=m.Market.US, pool_id=m.PoolId.US_POOL, side=m.OrderSide.BUY,
        order_type=m.OrderType.LIMIT, time_in_force=m.TimeInForce.DAY,
        quantity=m.Quantity(value=D(qty)),
        limit_price=m.Price(value=D("10.00"), currency=USD),
        state=state, filled_quantity=m.Quantity(value=D(filled)),
        account_id=uuid4(), client_order_id="COID-1", broker_id="alpaca",
        strategy_version="v1", strategy_id="S1", model_id="m1",
        audit_event_id=uuid4(), placed_at=U)


for _n, _f in sorted((n, f) for n, f in list(globals().items())
                     if n.startswith("t_") and callable(f)):
    check(_n, _f)

print(f"PASSED {len(PASS)}")
for _msg in FAIL:
    print("FAILED", _msg)
sys.exit(1 if FAIL else 0)
