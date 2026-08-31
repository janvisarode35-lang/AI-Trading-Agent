"""Verification harness for SPEC-P1.1-DOMAIN. Asserts the invariants the spec claims."""
import sys
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

sys.path.insert(0, "D:/GitHub/AI-Trading-Agent/src")
from domain import models as m  # noqa: E402

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


U = lambda h=0: datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc) + timedelta(hours=h)  # noqa: E731
USD, INR = m.Currency.USD, m.Currency.INR
D = Decimal


# ---- Money closure (spec 3.2) ----------------------------------------------
def t_money_closed():
    a = m.Money.of("1.005", USD)          # quantises half-up
    assert a.amount == D("1.01"), a.amount
    b = m.Money.of("2.00", USD)
    assert (a + b).amount == D("3.01")
    assert (b - a).amount == D("0.99")
    assert (b * 3).amount == D("6.00")
    assert (3 * b).amount == D("6.00")
    for v in (a + b, b - a, b * 3):
        assert v.amount.as_tuple().exponent == -2, v


def t_money_no_division():
    raises(TypeError, lambda: m.Money.of("1.00", USD) / 3)
    raises(TypeError, lambda: m.Money.of("1.00", USD) // 3)


def t_money_no_decimal_mult():
    raises(TypeError, lambda: m.Money.of("1.00", USD) * D("1.5"))


def t_cross_currency():
    u, i = m.Money.of("1.00", USD), m.Money.of("1.00", INR)
    raises(m.CurrencyMismatchError, lambda: u + i)
    raises(m.CurrencyMismatchError, lambda: u - i)
    raises(m.CurrencyMismatchError, lambda: u < i)
    assert (u == i) is False          # equality must NOT raise
    assert len({u, i}) == 2           # hashable


def t_float_rejected():
    raises(m.FloatContaminationError, lambda: m.Money(amount=1.5, currency=USD))
    raises(m.FloatContaminationError, lambda: m.Price(value=1.5, currency=USD))


def t_allocate_exact():
    # the classic penny-split
    parts = m.Money.of("0.01", USD).allocate([D(1), D(1), D(1)])
    assert [p.amount for p in parts] == [D("0.01"), D("0.00"), D("0.00")], parts
    assert sum(p.amount for p in parts) == D("0.01")
    # uneven weights, 100 ways
    total = m.Money.of("100.00", USD)
    parts = total.allocate([D(1), D(1), D(1)])
    assert sum(p.amount for p in parts) == D("100.00")
    assert [p.amount for p in parts] == [D("33.34"), D("33.33"), D("33.33")]
    # negative total (realised loss)
    neg = m.Money.of("-10.00", USD).allocate([D(3), D(7)])
    assert sum(p.amount for p in neg) == D("-10.00"), neg
    raises(ValueError, lambda: total.allocate([D(1), D(0)]))
    raises(ValueError, lambda: total.allocate([]))


# ---- Price / tick (rule N10) ------------------------------------------------
def t_tick_rejects_never_rounds():
    p = m.Price(value=D("10.005"), currency=USD)
    raises(m.TickSizeViolation, lambda: p.validate_tick(D("0.01")))
    assert p.value == D("10.005000")           # unchanged: never rounded
    m.Price(value=D("10.00"), currency=USD).validate_tick(D("0.01"))
    p.validate_tick(D("0.005"))                # legal under the Nov-2027 regime


def t_notional_one_rounding():
    px = m.Price(value=D("10.123456"), currency=USD)
    q = m.Quantity(value=D("3"))
    n = px.notional(q)
    assert n.amount == D("30.37"), n.amount     # 30.370368 -> half-up
    assert n.currency is USD


# ---- Quantity (ADR-12 sign, P0.1 rounding) ---------------------------------
def t_quantity_rules():
    raises(m.NegativeQuantityError, lambda: m.Quantity(value=D("-1")))
    assert m.Quantity.round_to_increment(D("13.7"), D(1)).value == D("13.000000")
    assert m.Quantity.round_to_increment(D("0.4"), D(1)).is_zero()
    assert m.Quantity.round_to_increment(D("137"), D(50)).value == D("100.000000")
    raises(m.QuantityIncrementError, lambda: m.Quantity(value=D("137")).validate_increment(D(50)))
    raises(m.MissingReferenceDataError, lambda: m.Quantity.round_to_increment(D(10), D(0)))


# ---- Time ------------------------------------------------------------------
def t_naive_datetime_rejected():
    raises(m.NaiveDatetimeError, lambda: m.StalenessPolicy(
        data_type="bar", max_age_seconds=60).check(datetime(2026, 1, 1), U()))


def t_calendar():
    s = m.ExchangeSession(
        exchange=m.Exchange.NYSE, market=m.Market.US, trading_date=date(2026, 8, 26),
        session_type=m.SessionType.REGULAR,
        regular_open_utc=datetime(2026, 8, 26, 13, 30, tzinfo=timezone.utc),
        regular_close_utc=datetime(2026, 8, 26, 20, 0, tzinfo=timezone.utc),
        settlement_date=date(2026, 8, 27))
    cal = m.TradingCalendar(exchange=m.Exchange.NYSE, sessions=(s,))
    assert cal.session(date(2026, 8, 26)) is s
    assert s.utc_accounting_date == date(2026, 8, 26)
    raises(m.MissingSessionError, lambda: cal.session(date(2026, 8, 27)))  # absence == closed
    assert cal.is_open(date(2026, 8, 27)) is False


def t_muhurat_excluded():
    base = dict(exchange=m.Exchange.NSE, market=m.Market.IN, session_type=m.SessionType.REGULAR,
                settlement_date=date(2026, 11, 3))
    reg = m.ExchangeSession(**base, trading_date=date(2026, 11, 2),
                            regular_open_utc=datetime(2026, 11, 2, 3, 45, tzinfo=timezone.utc),
                            regular_close_utc=datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc))
    muh = m.ExchangeSession(exchange=m.Exchange.NSE, market=m.Market.IN,
                            trading_date=date(2026, 11, 3), session_type=m.SessionType.SPECIAL,
                            regular_open_utc=datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc),
                            regular_close_utc=datetime(2026, 11, 3, 14, 0, tzinfo=timezone.utc),
                            settlement_date=date(2026, 11, 4), counts_for_sequencing=False)
    cal = m.TradingCalendar(exchange=m.Exchange.NSE, sessions=(reg, muh))
    assert len(cal.sequenced_sessions()) == 1


# ---- Identity --------------------------------------------------------------
def t_symbol_reuse_after_delisting():
    old, new = uuid4(), uuid4()
    maps = (
        m.SymbolMapping(instrument_id=old, market=m.Market.US, exchange=m.Exchange.NASDAQ,
                        symbol="ABCD", valid_from=date(2015, 1, 1), valid_to=date(2020, 6, 1)),
        m.SymbolMapping(instrument_id=new, market=m.Market.US, exchange=m.Exchange.NASDAQ,
                        symbol="ABCD", valid_from=date(2022, 3, 1)),
    )
    assert m.resolve_instrument(maps, m.Market.US, "ABCD", date(2018, 5, 1)) == old
    assert m.resolve_instrument(maps, m.Market.US, "ABCD", date(2024, 5, 1)) == new
    raises(m.UnknownSymbolError,
           lambda: m.resolve_instrument(maps, m.Market.US, "ABCD", date(2021, 1, 1)))


def t_ambiguous_symbol():
    maps = tuple(
        m.SymbolMapping(instrument_id=uuid4(), market=m.Market.US, exchange=m.Exchange.NYSE,
                        symbol="DUP", valid_from=date(2020, 1, 1)) for _ in range(2))
    raises(m.AmbiguousSymbolError,
           lambda: m.resolve_instrument(maps, m.Market.US, "DUP", date(2024, 1, 1)))


def t_corporate_action_deny_by_default():
    raises(m.UnknownCorporateActionError, lambda: m.parse_corporate_action_type("WEIRD_VENDOR_CODE"))
    assert m.parse_corporate_action_type("split") is m.CorporateActionType.SPLIT


def t_india_requires_lot_size():
    raises(m.MissingReferenceDataError, lambda: m.Instrument(
        instrument_id=uuid4(), market=m.Market.IN, exchange=m.Exchange.NSE,
        instrument_type=m.InstrumentType.COMMON_STOCK, status=m.InstrumentStatus.ACTIVE,
        currency=INR, qty_increment=D(1)))


def t_us_fractional_blocked():
    raises(m.MissingReferenceDataError, lambda: m.Instrument(
        instrument_id=uuid4(), market=m.Market.US, exchange=m.Exchange.NASDAQ,
        instrument_type=m.InstrumentType.COMMON_STOCK, status=m.InstrumentStatus.ACTIVE,
        currency=USD, qty_increment=D("0.001"), supports_fractional=True))


# ---- Bar / Quote -----------------------------------------------------------
def _px(v):
    return m.Price(value=D(v), currency=USD)


def t_bar_integrity_and_finality():
    base = dict(instrument_id=uuid4(), market=m.Market.US, as_of=U(), retrieved_at=U(),
                source="massive", interval=m.BarInterval.DAILY, trading_date=date(2026, 8, 26),
                volume=1000)
    good = m.Bar(**base, open=_px("10"), high=_px("11"), low=_px("9"), close=_px("10.5"),
                 is_final=True)
    good.assert_signal_eligible()
    partial = m.Bar(**base, open=_px("10"), high=_px("11"), low=_px("9"), close=_px("10.5"),
                    is_final=False)
    raises(m.StaleDataError, partial.assert_signal_eligible)
    raises(m.BarIntegrityError, lambda: m.Bar(**base, open=_px("12"), high=_px("11"),
                                              low=_px("9"), close=_px("10"), is_final=True))
    # zero-volume bar is valid and not imputed
    m.Bar(**{**base, "volume": 0}, open=_px("10"), high=_px("10"), low=_px("10"),
          close=_px("10"), is_final=True)


def t_crossed_quote():
    base = dict(instrument_id=uuid4(), market=m.Market.US, as_of=U(), retrieved_at=U(),
                source="alpaca", bid_size=100, ask_size=100, venue="IEX")
    raises(m.CrossedQuoteError, lambda: m.Quote(**base, bid=_px("11"), ask=_px("10"),
                                                is_consolidated=True))
    q = m.Quote(**base, bid=_px("10"), ask=_px("10.02"), is_consolidated=False)
    raises(m.StaleDataError, q.assert_screening_eligible)  # rule N6


# ---- Rule N16 --------------------------------------------------------------
def t_news_point_in_time():
    t = U()
    n1 = m.NewsItem(instrument_id=uuid4(), market=m.Market.US, as_of=t, retrieved_at=t,
                    source="benzinga", vendor_id="V1", revision_seq=1, headline="H",
                    body_sanitised="B", sanitiser_version="s1", vendor_published_at=t,
                    first_seen_at=t)
    assert n1.is_point_in_time_record
    n2 = m.NewsItem(instrument_id=uuid4(), market=m.Market.US, as_of=t, retrieved_at=U(1),
                    source="benzinga", vendor_id="V1", revision_seq=2, headline="H2",
                    body_sanitised="B2", sanitiser_version="s1", vendor_published_at=t,
                    vendor_updated_at=U(1), first_seen_at=t)
    assert not n2.is_point_in_time_record
    assert not hasattr(n1, "body_raw") and not hasattr(n1, "content")


# ---- [CONST-2] structural gate ---------------------------------------------
def _decision(rd):
    return m.Decision(
        decision_id=uuid4(), instrument_id=uuid4(), market=m.Market.US,
        pool_id=m.PoolId.US_POOL, trading_date=date(2026, 8, 26),
        action=m.DecisionAction.ENTER, target_quantity=m.Quantity(value=D(100)),
        limit_price=_px("10"), strategy_version="v1", model_id="mdl",
        risk_verdict_id=uuid4(), risk_decision=rd, audit_event_id=uuid4(), decided_at=U())


def t_risk_deny_is_final():
    _decision(m.RiskDecision.ALLOW)
    raises(m.RiskDenyIsFinal, lambda: _decision(m.RiskDecision.DENY))


def t_thesis_has_no_size_fields():
    banned = {"quantity", "target_quantity", "size", "weight", "limit_price", "price",
              "notional", "position_pct", "nav", "cash"}
    assert banned & set(m.Thesis.model_fields) == set(), banned & set(m.Thesis.model_fields)
    ic = m.InvalidationCondition(condition_id=uuid4(), kind=m.InvalidationKind.PRICE_BELOW,
                                 threshold_price=_px("9"), description="stop")
    raises(ValueError, lambda: m.Thesis(
        thesis_id=uuid4(), candidate_id=uuid4(), instrument_id=uuid4(),
        trading_date=date(2026, 8, 26), bull_case="b", bear_case="r",
        invalidation_conditions=(), stated_confidence=D("0.5"), model_id="x",
        prompt_version="p", sanitiser_version="s", input_content_hashes=("a" * 64,),
        audit_event_id=uuid4(), generated_at=U()))
    m.Thesis(thesis_id=uuid4(), candidate_id=uuid4(), instrument_id=uuid4(),
             trading_date=date(2026, 8, 26), bull_case="b", bear_case="r",
             invalidation_conditions=(ic,), stated_confidence=D("0.5"), model_id="x",
             prompt_version="p", sanitiser_version="s", input_content_hashes=("a" * 64,),
             audit_event_id=uuid4(), generated_at=U())


def t_no_override_parameters():
    import inspect
    banned = {"force", "override", "bypass", "ignore_risk", "skip_risk"}
    for name, obj in vars(m).items():
        if inspect.isfunction(obj):
            params = set(inspect.signature(obj).parameters)
            assert not (params & banned), f"{name} accepts {params & banned}"


def t_llm_cannot_emit_signal():
    kw = dict(signal_id=uuid4(), instrument_id=uuid4(), trading_date=date(2026, 8, 26),
              direction=m.SignalDirection.BUY, strength=D("0.7"), horizon_sessions=15,
              model_id="x", computed_at=U())
    m.Signal(**kw)
    raises(m.LlmOutputNotPermitted, lambda: m.Signal(**kw, is_llm_derived=True))


def t_no_sell_short():
    assert "SELL_SHORT" not in {e.name for e in m.SignalDirection}


def t_holding_band():
    from pydantic import ValidationError
    raises(ValidationError, lambda: m.Signal(
        signal_id=uuid4(), instrument_id=uuid4(), trading_date=date(2026, 8, 26),
        direction=m.SignalDirection.BUY, strength=D("0.5"), horizon_sessions=200,
        model_id="x", computed_at=U()))


# ---- State machines --------------------------------------------------------
def t_order_transitions():
    oid = uuid4()
    m.assert_order_transition(m.OrderState.PENDING_NEW, m.OrderState.FILLED, oid)
    m.assert_order_transition(m.OrderState.PENDING_CANCEL, m.OrderState.FILLED, oid)
    for term in m.TERMINAL_ORDER_STATES:
        assert m.ORDER_TRANSITIONS[term] == frozenset()
        raises(m.IllegalOrderTransition,
               lambda t=term: m.assert_order_transition(t, m.OrderState.NEW, oid))
    raises(m.IllegalOrderTransition,
           lambda: m.assert_order_transition(m.OrderState.CANCELED, m.OrderState.FILLED, oid))
    assert m.parse_order_state("some_broker_state") is m.OrderState.UNKNOWN
    # every state has a table entry
    assert set(m.ORDER_TRANSITIONS) == set(m.OrderState)


def t_position_transitions():
    iid = uuid4()
    raises(m.IllegalPositionTransition,
           lambda: m.assert_position_transition(m.PositionState.OPEN,
                                                m.PositionState.CLOSED, iid))
    m.assert_position_transition(m.PositionState.OPEN, m.PositionState.PENDING_CLOSE, iid)
    m.assert_position_transition(m.PositionState.CLOSED, m.PositionState.UNRECONCILED, iid)
    assert set(m.POSITION_TRANSITIONS) == set(m.PositionState)


def t_kill_switch():
    assert m.BOOT_KILL_SWITCH_STATE is m.KillSwitchState.TRIPPED
    ks = m.KillSwitch.at_boot(uuid4(), uuid4())
    assert ks.state is m.KillSwitchState.TRIPPED and not ks.permits_trading()
    # every toward-halt transition is automatic
    m.assert_kill_switch_transition(m.KillSwitchState.ARMED, m.KillSwitchState.TRIPPED, None)
    m.assert_kill_switch_transition(m.KillSwitchState.POOL_HALTED,
                                    m.KillSwitchState.TRIPPED, None)
    # every away-from-halt transition needs a human approval
    raises(m.IllegalKillSwitchTransition, lambda: m.assert_kill_switch_transition(
        m.KillSwitchState.TRIPPED, m.KillSwitchState.ARMED, None))
    m.assert_kill_switch_transition(m.KillSwitchState.TRIPPED, m.KillSwitchState.ARMED, uuid4())
    # no partial de-escalation
    raises(m.IllegalKillSwitchTransition, lambda: m.assert_kill_switch_transition(
        m.KillSwitchState.TRIPPED, m.KillSwitchState.POOL_HALTED, uuid4()))
    # no ARMED without an approval id
    raises(m.IllegalKillSwitchTransition, lambda: m.KillSwitch(
        kill_switch_id=uuid4(), scope=m.KillSwitchScope.GLOBAL,
        state=m.KillSwitchState.ARMED, audit_event_id=uuid4()))
    assert not any(n in dir(m.KillSwitch) for n in ("force_arm", "reset", "arm"))


# ---- Lots, wash sale, FX, NAV ----------------------------------------------
def _lot(market=m.Market.US, pool=m.PoolId.US_POOL, cur=USD, **kw):
    base = dict(lot_id=uuid4(), instrument_id=uuid4(), market=market, pool_id=pool,
                opened_on=date(2026, 8, 1), quantity_opened=m.Quantity(value=D(3)),
                quantity_remaining=m.Quantity(value=D(3)),
                cost_total=m.Money.of("100.00", cur), fees_total=m.Money.of("1.00", cur),
                opening_fill_id=uuid4(), audit_event_id=uuid4())
    return m.Lot(**{**base, **kw})


def t_lot_basis_exact():
    lot = _lot()
    c1 = lot.consumed_cost(m.Quantity(value=D(1)))
    c2 = lot.consumed_cost(m.Quantity(value=D(2)))
    assert c1.amount + c2.amount == D("100.00"), (c1, c2)   # exact, no lost cent
    assert lot.consumed_cost(m.Quantity(value=D(3))).amount == D("100.00")
    assert "cost_basis_per_share" not in m.Lot.model_fields   # never stored
    assert lot.derived_basis_per_share().value == D("33.333333")


def t_wash_sale_india_blocked():
    raises(m.WashSaleNotApplicableError, lambda: _lot(
        market=m.Market.IN, pool=m.PoolId.IN_POOL, cur=INR,
        cost_total=m.Money.of("100.00", INR), fees_total=m.Money.of("1.00", INR),
        wash_sale_disallowed_loss=m.Money.of("5.00", INR)))
    _lot(wash_sale_disallowed_loss=m.Money.of("5.00", USD))   # US is fine


def t_account_settled_cash():
    a = m.Account(account_id=uuid4(), pool_id=m.PoolId.US_POOL, market=m.Market.US,
                  account_type=m.AccountType.CASH, broker_id="alpaca",
                  equity=m.Money.of("100000.00", USD), total_cash=m.Money.of("50000.00", USD),
                  settled_cash=m.Money.of("30000.00", USD), day_trades_5d=0, as_of=U())
    assert a.entry_buying_power().amount == D("30000.00")   # settled, not total
    raises(ValueError, lambda: m.Account(
        account_id=uuid4(), pool_id=m.PoolId.US_POOL, market=m.Market.US,
        account_type=m.AccountType.CASH, broker_id="alpaca",
        equity=m.Money.of("1.00", USD), total_cash=m.Money.of("1.00", USD),
        settled_cash=m.Money.of("2.00", USD), day_trades_5d=0, as_of=U()))


def t_fx_missing_blocks_both_pools():
    us = m.PoolNAV(nav_id=uuid4(), pool_id=m.PoolId.US_POOL, trading_date=date(2026, 8, 26),
                   total_value=m.Money.of("100000.00", USD), cash=m.Money.of("20000.00", USD),
                   positions_value=m.Money.of("80000.00", USD),
                   peak_value=m.Money.of("110000.00", USD), audit_event_id=uuid4(), computed_at=U())
    ind = m.PoolNAV(nav_id=uuid4(), pool_id=m.PoolId.IN_POOL, trading_date=date(2026, 8, 26),
                    total_value=m.Money.of("500000.00", INR), cash=m.Money.of("500000.00", INR),
                    positions_value=m.Money.zero(INR),
                    peak_value=m.Money.of("500000.00", INR), audit_event_id=uuid4(), computed_at=U())
    assert us.drawdown_pct() == D("0.090909")
    raises(m.MissingFxRateError, lambda: m.ConsolidatedNAV(
        nav_id=uuid4(), utc_accounting_date=date(2026, 8, 26),
        total_value_usd=m.Money.of("105000.00", USD),
        peak_value_usd=m.Money.of("115000.00", USD), pool_navs=(us, ind), fx_rate_ids=(),
        translation_effect_usd=m.Money.zero(USD), audit_event_id=uuid4(), computed_at=U()))
    # US-only pool needs no FX; the code path still runs (ADR-15)
    m.ConsolidatedNAV(nav_id=uuid4(), utc_accounting_date=date(2026, 8, 26),
                      total_value_usd=m.Money.of("100000.00", USD),
                      peak_value_usd=m.Money.of("110000.00", USD), pool_navs=(us,),
                      fx_rate_ids=(), translation_effect_usd=m.Money.zero(USD),
                      audit_event_id=uuid4(), computed_at=U())


def t_fx_convert_only_direction():
    fx = m.FxRate(fx_rate_id=uuid4(), as_of_date=date(2026, 8, 26), base=INR, quote=USD,
                  rate=D("0.011950"), source="RBI_REFERENCE", retrieved_at=U())
    assert fx.convert(m.Money.of("500000.00", INR)).amount == D("5975.00")
    raises(m.CurrencyMismatchError, lambda: fx.convert(m.Money.of("100.00", USD)))


# ---- Risk / sizing ---------------------------------------------------------
def t_invalid_stop():
    kw = dict(request_id=uuid4(), instrument_id=uuid4(), pool_id=m.PoolId.US_POOL,
              signal_id=uuid4(), nav_snapshot_id=uuid4(),
              settled_cash=m.Money.of("30000.00", USD), regime=m.RegimeLabel.BULL,
              requested_at=U())
    m.PositionSizeRequest(**kw, entry_price=_px("100"), stop_price=_px("95"))
    raises(m.InvalidStopError,
           lambda: m.PositionSizeRequest(**kw, entry_price=_px("100"), stop_price=_px("100")))


def t_verdict_frozen_and_deny_names_constraint():
    v = m.RiskVerdict(verdict_id=uuid4(), request_id=uuid4(), instrument_id=uuid4(),
                      pool_id=m.PoolId.US_POOL, decision=m.RiskDecision.ALLOW,
                      limits_evaluated=("position_pct",), nav_snapshot_id=uuid4(),
                      evaluated_at=U(), audit_event_id=uuid4())
    raises(Exception, lambda: setattr(v, "decision", m.RiskDecision.DENY))
    raises(ValueError, lambda: m.RiskVerdict(
        verdict_id=uuid4(), request_id=uuid4(), instrument_id=uuid4(),
        pool_id=m.PoolId.US_POOL, decision=m.RiskDecision.DENY,
        limits_evaluated=("position_pct",), nav_snapshot_id=uuid4(), evaluated_at=U(),
        audit_event_id=uuid4()))


# ---- Audit / RunContext ----------------------------------------------------
# t_audit_chain moved to tests/verify_p14_audit.py: the envelope and the
# verifier are now owned by audit.events / audit.chain (SPEC-P1.4 §4).


def t_run_context_n11():
    kw = dict(run_id=uuid4(), market=m.Market.US, trading_date=date(2026, 8, 26),
              started_at=U(), code_version="abc1234", config_hash="f" * 64,
              strategy_version="v1", model_id="mdl")
    live = m.RunContext(**kw, run_type=m.RunType.PIPELINE, is_paper=False, is_backtest=False)
    paper = m.RunContext(**kw, run_type=m.RunType.PAPER, is_paper=True, is_backtest=False)
    assert live.may_cite_for_cost_model() and not paper.may_cite_for_cost_model()
    raises(ValueError, lambda: m.RunContext(**kw, run_type=m.RunType.BACKTEST,
                                            is_paper=True, is_backtest=True))


# ---- Cross-cutting ---------------------------------------------------------
def t_all_enums_are_str():
    import enum as _e
    for name, obj in vars(m).items():
        if isinstance(obj, type) and issubclass(obj, _e.Enum) and obj is not _e.Enum:
            assert issubclass(obj, str), f"{name} is not str-valued"


def t_all_models_frozen_and_forbid():
    from pydantic import BaseModel
    for name, obj in vars(m).items():
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
            if name.startswith("_"):
                continue
            assert obj.model_config.get("frozen") is True, f"{name} not frozen"
            assert obj.model_config.get("extra") == "forbid", f"{name} allows extras"


def t_decimal_serialises_to_string():
    import json
    payload = json.loads(m.Money.of("1.23", USD).model_dump_json())
    assert isinstance(payload["amount"], str), payload


def t_instrument_allowlist():
    assert m.TRADEABLE_INSTRUMENT_TYPES_V1 == frozenset({m.InstrumentType.COMMON_STOCK})
    assert m.InstrumentType.FUTURE in m.PERMANENTLY_BANNED_INSTRUMENT_TYPES
    assert m.InstrumentType.OPTION in m.PERMANENTLY_BANNED_INSTRUMENT_TYPES
    inst = m.Instrument(instrument_id=uuid4(), market=m.Market.US, exchange=m.Exchange.NASDAQ,
                        instrument_type=m.InstrumentType.ETF, status=m.InstrumentStatus.ACTIVE,
                        currency=USD, qty_increment=D(1))
    assert not inst.is_tradeable_v1()          # ETFs read-only in v1


def t_pool_segregation():
    assert m.PoolId.US_POOL.currency is USD and m.PoolId.IN_POOL.currency is INR
    raises(m.CurrencyMismatchError, lambda: _lot(
        market=m.Market.US, pool=m.PoolId.US_POOL, cost_total=m.Money.of("100.00", INR)))


for _n, _f in sorted((n, f) for n, f in list(globals().items()) if n.startswith("t_")):
    check(_n, _f)

print(f"PASSED {len(PASS)}")
for f in FAIL:
    print("FAILED", f)
sys.exit(1 if FAIL else 0)
