"""One regression test per X2 finding. Each FAILS against the pre-X2 models.py."""
import sys
import threading
from datetime import date, datetime, timezone
from decimal import Decimal as D
from uuid import uuid4

sys.path.insert(0, "D:/GitHub/AI-Trading-Agent/src")
from domain import models as m  # noqa: E402
from audit import events as ae  # noqa: E402
from audit import chain as ac  # noqa: E402

PASS, FAIL = [], []
USD, INR = m.Currency.USD, m.Currency.INR
U = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


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


def _lot(opened, remaining, cost="1000.00", market=m.Market.US, pool=m.PoolId.US_POOL,
         cur=USD, **kw):
    return m.Lot(lot_id=uuid4(), instrument_id=uuid4(), market=market, pool_id=pool,
                 opened_on=date(2026, 8, 1),
                 quantity_opened=m.Quantity(value=D(opened)),
                 quantity_remaining=m.Quantity(value=D(remaining)),
                 cost_total=m.Money.of(cost, cur), fees_total=m.Money.of("1.00", cur),
                 opening_fill_id=uuid4(), audit_event_id=uuid4(), **kw)


# ---- F-1 BLOCKER: lot cost basis after partial consumption -----------------
def t_f1_basis_after_partial_consumption():
    lot = _lot(100, 50)                       # 50 already sold, cost_total untouched
    assert lot.remaining_cost().amount == D("500.00"), lot.remaining_cost()
    assert lot.consumed_cost(m.Quantity(value=D(25))).amount == D("250.00")
    assert lot.consumed_cost(m.Quantity(value=D(50))).amount == D("500.00")
    assert lot.consumed_cost(m.Quantity(value=D(0))).amount == D("0.00")


def t_f1_full_lot_unchanged():
    lot = _lot(100, 100)
    assert lot.remaining_cost().amount == D("1000.00")
    assert lot.consumed_cost(m.Quantity(value=D(100))).amount == D("1000.00")
    assert lot.consumed_cost(m.Quantity(value=D(30))).amount == D("300.00")


def t_f1_consumption_path_is_exactly_additive():
    """The property the telescoping fix exists to guarantee: consuming a lot in ANY
    sequence of steps releases exactly cost_total, to the cent, with no drift."""
    for cost in ("1000.00", "999.99", "0.07", "1234.56", "0.01"):
        for steps in ([30, 20, 50], [1, 1, 1, 97], [99, 1], [100], [33, 33, 34]):
            remaining, released = 100, m.Money.zero(USD)
            for step in steps:
                lot = _lot(100, remaining, cost=cost)
                released = released + lot.consumed_cost(m.Quantity(value=D(step)))
                remaining -= step
            assert remaining == 0
            assert released.amount == D(cost), (cost, steps, released.amount)


def t_f1_position_cost_basis_uses_remaining():
    lot = _lot(100, 50)
    pos = m.Position(instrument_id=lot.instrument_id, market=m.Market.US,
                     pool_id=m.PoolId.US_POOL, state=m.PositionState.OPEN, lots=(lot,))
    assert pos.cost_basis().amount == D("500.00"), pos.cost_basis()


def t_f1_overconsume_still_raises():
    raises(ValueError, lambda: _lot(100, 50).consumed_cost(m.Quantity(value=D(51))))


# ---- F-2 HIGH: Decimal context must not depend on the calling thread -------
def t_f2_rounding_is_thread_independent():
    out = {}

    def worker():
        # This thread never calls install_domain_decimal_context().
        out["money"] = m.Money.of("1.005", USD).amount           # half-up -> 1.01
        out["money2"] = m.Money.of("1.015", USD).amount          # half-up -> 1.02
        out["price"] = m.Price(value=D("1.0000005"), currency=USD).value
        out["qty"] = m.Quantity.round_to_increment(D("13.7"), D(1)).value
        lot = _lot(3, 3, cost="1000.00")
        out["per_share"] = lot.derived_basis_per_share().value

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    # Under bankers' rounding 1.015 -> 1.02 as well, but 1.005 -> 1.00. The second
    # value is the one that discriminates.
    assert out["money"] == D("1.01"), f"half-up violated on a worker thread: {out['money']}"
    assert out["money2"] == D("1.02"), out["money2"]
    assert out["price"] == D("1.000001"), out["price"]
    assert out["qty"] == D("13.000000"), out["qty"]
    assert out["per_share"] == D("333.333333"), out["per_share"]


def t_f2_float_still_rejected_off_thread():
    out = {}

    def worker():
        try:
            m.Money(amount=1.5, currency=USD)
            out["r"] = "ACCEPTED"
        except m.FloatContaminationError:
            out["r"] = "REJECTED"

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    assert out["r"] == "REJECTED", out


# ---- F-3 HIGH: chain verification must accept a contiguous slice ------------
def _chain(n, start=0):
    """X2 F-3/F-5 coverage, retargeted to audit.events.AuditEnvelope.

    The envelope moved to P1.4 (SPEC-P1.4 §4) when consolidating two definitions of
    one concept. The FINDINGS stay regression-tested here; only the type moved.
    """
    evs, prev = [], "0" * 64
    for i in range(start, start + n):
        d = ae.AuditEnvelope(
            event_id=ae.uuid7(), seq=i, run_id=uuid4(),
            event_type=ae.EventType.RUN_FINISHED, event_class=ae.EventClass.SYSTEM,
            occurred_at=U, recorded_at=U, actor="sys", is_paper=False,
            is_backtest=False, input_hash="a" * 64,
            payload={"run_id": "r", "outcome": "OK", "duration_seconds": "1"},
            prev_hash=prev if i > start or start == 0 else "1" * 64,
            payload_hash="0" * 64)
        real = d.model_copy(update={"payload_hash": d.compute_hash()})
        evs.append(real)
        prev = real.payload_hash
    return evs



def t_f3_slice_verifies():
    full = _chain(6)
    assert ac.verify_chain(full, require_genesis=True).intact
    assert ac.verify_chain(full[2:], expected_prev_hash=full[1].payload_hash).intact
    assert ac.verify_chain(full[3:5], expected_prev_hash=full[2].payload_hash).intact
    assert ac.verify_chain([]).intact          # empty is vacuously intact


def t_f3_gap_and_fork_still_caught():
    full = _chain(6)
    gap = ac.verify_chain([full[0], full[2]])
    assert ac.BreakKind.GAP in {b.kind for b in gap.breaks}
    forked = list(full)
    forked[3] = forked[3].model_copy(update={"prev_hash": "f" * 64})
    fork = ac.verify_chain(forked)
    assert ac.BreakKind.FORK in {b.kind for b in fork.breaks}



def t_f3_require_genesis_still_available():
    assert ac.verify_chain(_chain(4), require_genesis=True).intact
    r = ac.verify_chain(_chain(6)[2:], require_genesis=True)
    assert ac.BreakKind.GENESIS_MISSING in {b.kind for b in r.breaks}


# ---- F-4 HIGH: a price must be denominated in its pool's currency ----------
def _decision(**kw):
    base = dict(decision_id=uuid4(), instrument_id=uuid4(), market=m.Market.US,
                pool_id=m.PoolId.US_POOL, trading_date=date(2026, 8, 27),
                action=m.DecisionAction.ENTER, target_quantity=m.Quantity(value=D(10)),
                limit_price=m.Price(value=D("10"), currency=USD), strategy_version="v1",
                model_id="mdl", risk_verdict_id=uuid4(),
                risk_decision=m.RiskDecision.ALLOW, audit_event_id=uuid4(), decided_at=U)
    return m.Decision(**{**base, **kw})


def t_f4_decision_rejects_foreign_currency_price():
    _decision()                                                   # matching currency is fine
    raises(m.CurrencyMismatchError,
           lambda: _decision(limit_price=m.Price(value=D("100"), currency=INR)))


def t_f4_order_rejects_foreign_currency_price():
    base = dict(order_id=uuid4(), decision_id=uuid4(), account_id=uuid4(),
                instrument_id=uuid4(), market=m.Market.US, pool_id=m.PoolId.US_POOL,
                side=m.OrderSide.BUY, order_type=m.OrderType.LIMIT,
                time_in_force=m.TimeInForce.DAY, quantity=m.Quantity(value=D(10)),
                state=m.OrderState.NEW, filled_quantity=m.Quantity.zero(),
                client_order_id="c1", broker_id="alpaca", strategy_version="v1",
                strategy_id="s1", model_id="mdl", audit_event_id=uuid4(), placed_at=U)
    m.Order(**base, limit_price=m.Price(value=D("10"), currency=USD))
    raises(m.CurrencyMismatchError,
           lambda: m.Order(**base, limit_price=m.Price(value=D("10"), currency=INR)))


# ---- F-5 HIGH: fields the P1.2 schema requires ------------------------------
def t_f5_audit_event_carries_class_and_provenance():
    for f in ("event_class", "is_paper", "is_backtest"):
        assert f in ae.AuditEnvelope.model_fields, f
    e = _chain(1)[0]
    assert e.event_class is m.AuditEventClass.SYSTEM
    # RULE-B4's durability split needs every class the schema enumerates.
    assert {c.value for c in m.AuditEventClass} == {
        "ACTION", "EVALUATION", "NAV", "RISK", "KILL_SWITCH", "APPROVAL", "SYSTEM"}


def t_f5_audit_event_paper_xor_backtest():
    raises(Exception, lambda: ae.AuditEnvelope(
        event_id=ae.uuid7(), seq=0, run_id=uuid4(),
        event_type=ae.EventType.RUN_FINISHED, event_class=ae.EventClass.SYSTEM,
        occurred_at=U, recorded_at=U, actor="s", is_paper=True, is_backtest=True,
        input_hash="a" * 64,
        payload={"run_id": "r", "outcome": "OK", "duration_seconds": "1"},
        prev_hash="0" * 64, payload_hash="a" * 64))



def t_f5_run_context_has_finished_at():
    assert "finished_at" in m.RunContext.model_fields
    kw = dict(run_id=uuid4(), run_type=m.RunType.PIPELINE, market=m.Market.US,
              trading_date=date(2026, 8, 27), started_at=U, code_version="abc1234",
              config_hash="f" * 64, strategy_version="v1", model_id="mdl",
              is_paper=False, is_backtest=False)
    assert m.RunContext(**kw).finished_at is None
    raises(ValueError, lambda: m.RunContext(
        **kw, finished_at=datetime(2026, 8, 27, 11, 0, tzinfo=timezone.utc)))


# ---- F-6 MEDIUM: calendar lookups must not re-sort per call -----------------
def _cal(n=2520):
    sess = []
    for i in range(n):
        d = date.fromordinal(date(2016, 1, 4).toordinal() + i)
        sess.append(m.ExchangeSession(
            exchange=m.Exchange.NYSE, market=m.Market.US, trading_date=d,
            session_type=m.SessionType.REGULAR,
            regular_open_utc=datetime(d.year, d.month, d.day, 14, 30, tzinfo=timezone.utc),
            regular_close_utc=datetime(d.year, d.month, d.day, 21, 0, tzinfo=timezone.utc),
            settlement_date=date.fromordinal(d.toordinal() + 1)))
    return m.TradingCalendar(exchange=m.Exchange.NYSE, sessions=tuple(sess))


def t_f6_lookup_is_fast_and_correct():
    import timeit
    cal = _cal()
    n = 2000
    per = timeit.timeit(lambda: cal.sequenced_sessions(), number=n) / n
    assert per * 1500 < 0.05, f"{per*1500:.3f}s per session across 1,500 names"
    ref = date.fromordinal(date(2016, 1, 4).toordinal() + 300)
    assert cal.nth_prior_session(ref, 0).trading_date == ref
    assert cal.nth_prior_session(ref, 20).trading_date == \
        date.fromordinal(date(2016, 1, 4).toordinal() + 280)
    raises(m.MissingSessionError, lambda: cal.nth_prior_session(date(2016, 1, 5), 20))
    raises(m.MissingSessionError, lambda: cal.nth_prior_session(date(1999, 1, 1), 0))


def t_f6_sessions_between_bounds_inclusive():
    cal = _cal(50)
    base = date(2016, 1, 4).toordinal()
    got = cal.sessions_between(date.fromordinal(base + 10), date.fromordinal(base + 14))
    assert [s.trading_date for s in got] == [date.fromordinal(base + i) for i in range(10, 15)]
    assert cal.sessions_between(date(1999, 1, 1), date(1999, 1, 2)) == ()


def t_f6_construction_sorts_input():
    cal = _cal(10)
    shuffled = tuple(reversed(cal.sessions))
    resorted = m.TradingCalendar(exchange=m.Exchange.NYSE, sessions=shuffled)
    dates = [s.trading_date for s in resorted.sessions]
    assert dates == sorted(dates)


# ---- F-7 MEDIUM: bounded untrusted news body -------------------------------
def t_f7_news_body_is_bounded():
    from pydantic import ValidationError
    ok = dict(instrument_id=uuid4(), market=m.Market.US, as_of=U, retrieved_at=U,
              source="v", vendor_id="V1", revision_seq=1, headline="H",
              sanitiser_version="s1", vendor_published_at=U, first_seen_at=U)
    m.NewsItem(**ok, body_sanitised="A" * 200_000)
    raises(ValidationError, lambda: m.NewsItem(**ok, body_sanitised="A" * 200_001))
    raises(ValidationError, lambda: m.NewsItem(**{**ok, "headline": "H" * 1001},
                                               body_sanitised="B"))


# ---- F-8 LOW: the LLM guard raises its own error ----------------------------
def t_f8_llm_signal_raises_its_own_error():
    kw = dict(signal_id=uuid4(), instrument_id=uuid4(), trading_date=date(2026, 8, 27),
              direction=m.SignalDirection.BUY, strength=D("0.7"), horizon_sessions=15,
              model_id="x", computed_at=U)
    m.Signal(**kw)
    raises(m.LlmOutputNotPermitted, lambda: m.Signal(**kw, is_llm_derived=True))
    assert not issubclass(m.LlmOutputNotPermitted, m.RiskDenyIsFinal)
    assert issubclass(m.LlmOutputNotPermitted, m.DomainError)


for _n, _f in sorted((n, f) for n, f in list(globals().items()) if n.startswith("t_")):
    check(_n, _f)

print(f"PASSED {len(PASS)}")
for f in FAIL:
    print("FAILED", f)
sys.exit(1 if FAIL else 0)
