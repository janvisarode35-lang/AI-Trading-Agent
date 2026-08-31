"""SPEC-P1.3-CONFIG verification. Loads the real policy.yaml, exercises the gate's
conflict resolution, and runs the no-env-risk lint that §7 promises."""
import sys
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import loader as L  # noqa: E402

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


CFG = L.PolicyLoader(ROOT / "config").load(require_signature=False)
DOC = CFG.document


# ---- the real file loads and validates -------------------------------------
def t_policy_loads():
    assert DOC.policy_version == "0.1.0"
    assert len(DOC.rules) >= 35, len(DOC.rules)
    assert CFG.content_hash and len(CFG.content_hash) == 64


def t_every_const_limit_has_a_rule():
    """Every HARD RISK NUMBER in Block A must be expressed as a rule."""
    want = {
        "EXP-001",   # position <= 5% NAV
        "EXP-002",   # sector <= 20% NAV
        "EXP-003",   # gross <= 2x equity
        "EXP-004",   # net <= 1x equity
        "LOSS-001",  # daily loss <= 2%
        "LOSS-002",  # weekly loss <= 5%
        "LOSS-003",  # max drawdown <= 10% -> kill switch
        "SIZE-001",  # risk per trade 1%
        "LIQ-001",   # liquidity cap 1% of ADDV
        "RATE-001",  # <=20 orders/min global
        "RATE-002",  # <=10 per strategy
        "STOP-001",  # stop = entry - 2.5*ATR(14)
        "EXEC-001",  # limit default, market only for emergency exit
    }
    have = {r.id for r in DOC.rules}
    assert want <= have, f"missing constitutional rules: {sorted(want - have)}"


def t_const_thresholds_match_the_constitution():
    want = {
        "EXP-001": D("0.050"), "EXP-002": D("0.200"), "EXP-003": D("2.0"),
        "EXP-004": D("1.0"), "LOSS-001": D("0.020"), "LOSS-002": D("0.050"),
        "LOSS-003": D("0.100"), "SIZE-001": D("0.010"), "LIQ-001": D("0.010"),
        "RATE-001": 20, "RATE-002": 10, "STOP-001": D("2.5"),
    }
    for rid, expected in want.items():
        got = DOC.rule(rid).threshold
        assert D(str(got)) == D(str(expected)), f"{rid}: {got} != {expected}"


def t_every_rule_names_its_authority():
    for r in DOC.rules:
        assert r.authority and len(r.authority) >= 3, r.id


def t_every_rule_fails_closed():
    """[CONST-6]: no rule may fail open when its inputs are unavailable."""
    for r in DOC.rules:
        assert r.on_missing_input in (L.RuleAction.DENY, L.RuleAction.KILL), r.id


def t_every_rule_declares_inputs_and_window():
    for r in DOC.rules:
        assert r.inputs, r.id
        assert r.measurement.window and r.measurement.timing and r.measurement.basis, r.id


def t_drawdown_trips_the_kill_switch():
    for rid, scope in (("LOSS-003", L.KillScope.POOL), ("LOSS-004", L.KillScope.GLOBAL)):
        r = DOC.rule(rid)
        assert r.action is L.RuleAction.KILL and r.kill_scope is scope, rid
        # An unknown drawdown against a kill rule halts rather than declines.
        assert r.on_missing_input is L.RuleAction.KILL, rid


# ---- model-level guards -----------------------------------------------------
def t_fail_open_rule_is_rejected():
    bad = dict(id="XXX-001", description="a rule that fails open", authority="none",
               scope="global", mode="enforce", severity="LOW", threshold=1,
               comparison="lte", measurement=dict(basis="x", window="point_in_time",
                                                  timing="pre_trade"),
               inputs=["x"], action="DENY", on_missing_input="ALLOW")
    raises(Exception, lambda: L.Rule.model_validate(bad))


def t_integer_percent_on_a_pct_basis_is_rejected():
    bad = dict(id="XXX-002", description="integer percent smuggled in", authority="x",
               scope="pool", mode="enforce", severity="LOW", threshold=70,
               comparison="lte", measurement=dict(basis="nav_pct", window="point_in_time",
                                                  timing="pre_trade"),
               inputs=["x"], action="DENY", on_missing_input="DENY")
    raises(Exception, lambda: L.Rule.model_validate(bad))


def t_modify_without_a_modify_block_is_rejected():
    bad = dict(id="XXX-003", description="modify with nothing to modify", authority="x",
               scope="pool", mode="enforce", severity="LOW", threshold=D("0.5"),
               comparison="lte", measurement=dict(basis="x", window="point_in_time",
                                                  timing="pre_trade"),
               inputs=["x"], action="MODIFY", on_missing_input="DENY")
    raises(Exception, lambda: L.Rule.model_validate(bad))


def t_risk_deny_override_cannot_be_enabled():
    g = dict(min_approvals_to_tighten=0, min_approvals_to_loosen=2,
             risk_deny_override_permitted=True, approver_roles=["OWNER"], signature={})
    raises(Exception, lambda: L.Governance.model_validate(g))


def t_two_person_rule_cannot_be_weakened():
    g = dict(min_approvals_to_tighten=0, min_approvals_to_loosen=1,
             risk_deny_override_permitted=False, approver_roles=["OWNER"], signature={})
    raises(Exception, lambda: L.Governance.model_validate(g))


def t_tightening_needs_no_approval():
    g = dict(min_approvals_to_tighten=1, min_approvals_to_loosen=2,
             risk_deny_override_permitted=False, approver_roles=["OWNER"], signature={})
    raises(Exception, lambda: L.Governance.model_validate(g))


# ---- governance: the two-person rule ---------------------------------------
def t_loosening_direction_respects_comparison():
    lte = DOC.rule("EXP-001")          # lte: raising the number loosens
    gte = DOC.rule("PORT-001")         # gte: LOWERING the number loosens
    up = L.LimitChange(rule_id="EXP-001", field="threshold",
                       old_value=D("0.05"), new_value=D("0.08"))
    down = L.LimitChange(rule_id="PORT-001", field="threshold",
                         old_value=D("0.20"), new_value=D("0.10"))
    assert L.loosens_for(up, lte) is True
    assert L.loosens_for(down, gte) is True
    tighten = L.LimitChange(rule_id="EXP-001", field="threshold",
                            old_value=D("0.05"), new_value=D("0.03"))
    assert L.loosens_for(tighten, lte) is False


def t_two_distinct_approvers_required_to_loosen():
    rules = {r.id: r for r in DOC.rules}
    loosen = [L.LimitChange(rule_id="EXP-001", field="threshold",
                            old_value=D("0.05"), new_value=D("0.08"))]
    tighten = [L.LimitChange(rule_id="EXP-001", field="threshold",
                             old_value=D("0.05"), new_value=D("0.03"))]
    # tightening: no approval at all
    L.assert_change_authorised(tighten, rules, [], DOC.governance)
    # loosening with one approver: refused
    raises(L.PolicyGovernanceError,
           lambda: L.assert_change_authorised(loosen, rules, ["js"], DOC.governance))
    # the same person twice is still one person
    raises(L.PolicyGovernanceError,
           lambda: L.assert_change_authorised(loosen, rules, ["js", "JS "], DOC.governance))
    # two distinct identities: permitted
    L.assert_change_authorised(loosen, rules, ["js", "second-owner"], DOC.governance)


# ---- layering ---------------------------------------------------------------
def t_operator_override_cannot_touch_a_rule():
    raises(L.PolicyLayerError, lambda: L.merge_layers(
        [(L.Layer.DEFAULTS, {"rules": []}),
         (L.Layer.OPERATOR_OVERRIDE, {"rules": {"EXP-001": {"threshold": 0.9}}})],
        DOC.layering.order, DOC.layering.operator_override_denied_prefixes))
    raises(L.PolicyLayerError, lambda: L.merge_layers(
        [(L.Layer.DEFAULTS, {}),
         (L.Layer.OPERATOR_OVERRIDE, {"governance": {"min_approvals_to_loosen": 1}})],
        DOC.layering.order, DOC.layering.operator_override_denied_prefixes))
    raises(L.PolicyLayerError, lambda: L.merge_layers(
        [(L.Layer.DEFAULTS, {}),
         (L.Layer.OPERATOR_OVERRIDE, {"kill_switch": {"restore_state_on_boot": "ARMED"}})],
        DOC.layering.order, DOC.layering.operator_override_denied_prefixes))


def t_operator_override_may_touch_an_operational_knob():
    merged = L.merge_layers(
        [(L.Layer.DEFAULTS, {"latency": {"exit": {"audit_write_budget_ms": 100}}}),
         (L.Layer.OPERATOR_OVERRIDE, {"latency": {"exit": {"audit_write_budget_ms": 250}}})],
        DOC.layering.order, DOC.layering.operator_override_denied_prefixes)
    assert merged["latency"]["exit"]["audit_write_budget_ms"] == 250


def t_layer_precedence_is_last_wins():
    merged = L.merge_layers(
        [(L.Layer.DEFAULTS, {"a": 1, "b": 1}),
         (L.Layer.MARKET, {"b": 2, "c": 2}),
         (L.Layer.ENVIRONMENT, {"c": 3})],
        DOC.layering.order, DOC.layering.operator_override_denied_prefixes)
    assert merged == {"a": 1, "b": 2, "c": 3}


# ---- hashing and signature ---------------------------------------------------
def t_content_hash_is_order_independent_and_change_sensitive():
    a = L.content_hash({"x": 1, "y": {"p": 2, "q": 3}})
    b = L.content_hash({"y": {"q": 3, "p": 2}, "x": 1})
    assert a == b, "hash must not depend on key order"
    assert a != L.content_hash({"x": 1, "y": {"p": 2, "q": 4}})


def t_decimal_hashes_as_string_not_float():
    assert L.canonical_bytes({"v": D("0.050")}) == b'{"v":"0.050"}'


def t_signature_is_required_by_default():
    raises(L.PolicySignatureError,
           lambda: L.PolicyLoader(ROOT / "config").load())


def t_signature_roundtrip_and_tamper_detection():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    sk = Ed25519PrivateKey.generate()
    pem = sk.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    good = sk.sign(CFG.content_hash.encode("ascii"))
    cfg = L.PolicyLoader(ROOT / "config").load(
        signature=good, public_key_pem=pem, require_signature=True)
    assert cfg.content_hash == CFG.content_hash
    # a signature over a DIFFERENT hash must not verify
    wrong = sk.sign(b"0" * 64)
    raises(L.PolicySignatureError, lambda: L.PolicyLoader(ROOT / "config").load(
        signature=wrong, public_key_pem=pem, require_signature=True))
    # a different key must not verify
    other = Ed25519PrivateKey.generate().public_key().public_bytes(
        Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    raises(L.PolicySignatureError, lambda: L.PolicyLoader(ROOT / "config").load(
        signature=good, public_key_pem=other, require_signature=True))


# ---- secrets ----------------------------------------------------------------
def t_vault_ref_syntax():
    r = L.VaultRef.parse("vault://kv/data/trading/alpaca#api_key")
    assert (r.mount, r.path, r.key) == ("kv", "data/trading/alpaca", "api_key")
    assert r.render() == "vault://kv/data/trading/alpaca#api_key"
    for bad in ("vault://kv/data#", "vault://#k", "kv/data/x#k",
                "vault://kv/data/x", "https://kv/data/x#k"):
        raises(L.VaultReferenceError, lambda b=bad: L.VaultRef.parse(b))


def t_literal_secret_is_refused():
    for bad in ("sk-abcdefghijklmnopqrstuvwx",
                "A" * 48,
                "deadbeefdeadbeefdeadbeefdeadbeef"):
        raises(L.VaultReferenceError,
               lambda b=bad: L.assert_not_a_literal_secret("broker.key", b))
    # a reference is fine, and so is ordinary prose
    L.assert_not_a_literal_secret("broker.key", "vault://kv/data/x#k")
    L.assert_not_a_literal_secret("schedule.US.ingest_utc", "21:45")


def t_policy_file_contains_no_literal_secret():
    for name, ref in DOC.secret_refs.items():
        assert ref.startswith("vault://"), name
        L.VaultRef.parse(ref)


def t_effective_dump_carries_no_secret_value():
    payload = CFG.audit_payload()
    blob = str(payload)
    assert "vault://" in blob, "references should survive into the dump"
    assert payload["rule_count"] == len(DOC.rules)
    assert payload["content_hash"] == CFG.content_hash
    assert payload["enforced_rule_count"] < payload["rule_count"], \
        "at least one rule is in monitor mode, so the counts must differ"


# ---- the gate: precedence and conflict resolution ---------------------------
def _evaluator(fail_ids):
    def ev(rule, facts):
        return (rule.id not in fail_ids, facts.get("observed"))
    return ev


def _facts():
    return {i: 1 for r in DOC.rules for i in r.inputs} | {"observed": "1"}


def t_all_pass_is_allow():
    v = L.PolicyGate(CFG).evaluate(_facts(), evaluator=_evaluator(set()))
    assert v.action is L.RuleAction.ALLOW and v.binding_rule_id is None
    assert v.permits_trade


def t_deny_beats_modify():
    """The conflict the prompt asks about explicitly."""
    gate = L.PolicyGate(CFG)
    # SIZE-001 is MODIFY, EXP-001 is DENY. Both fail.
    v = gate.evaluate(_facts(), evaluator=_evaluator({"SIZE-001", "EXP-001"}))
    assert v.action is L.RuleAction.DENY, v.action
    assert v.binding_rule_id == "EXP-001"
    assert not v.permits_trade
    # MODIFY alone still modifies
    v2 = gate.evaluate(_facts(), evaluator=_evaluator({"SIZE-001"}))
    assert v2.action is L.RuleAction.MODIFY and v2.modifications
    assert v2.permits_trade


def t_kill_beats_deny():
    gate = L.PolicyGate(CFG)
    v = gate.evaluate(_facts(), evaluator=_evaluator({"EXP-001", "LOSS-003"}))
    assert v.action is L.RuleAction.KILL
    assert v.binding_rule_id == "LOSS-003"
    assert v.kill_scope is L.KillScope.POOL


def t_global_kill_beats_pool_kill_by_rule_id_order():
    """Ties inside one action break by rule id ascending, so the binding rule named
    in the audit record is reproducible across runs."""
    gate = L.PolicyGate(CFG)
    v = gate.evaluate(_facts(), evaluator=_evaluator({"LOSS-003", "LOSS-004"}))
    assert v.action is L.RuleAction.KILL
    assert v.binding_rule_id == "LOSS-003"     # lexicographically first


def t_monitor_mode_records_but_does_not_bind():
    gate = L.PolicyGate(CFG)
    monitors = [r.id for r in DOC.rules if r.mode is L.RuleMode.MONITOR]
    assert monitors, "the fixture needs at least one monitor rule"
    v = gate.evaluate(_facts(), evaluator=_evaluator(set(monitors)))
    assert v.action is L.RuleAction.ALLOW, v.binding_rule_id
    recorded = {o.rule_id for o in v.outcomes if not o.passed}
    assert set(monitors) <= recorded, "a monitor breach must still be recorded"


def t_missing_input_fails_closed():
    gate = L.PolicyGate(CFG)
    v = gate.evaluate({}, evaluator=_evaluator(set()))     # no facts at all
    assert v.action in (L.RuleAction.KILL, L.RuleAction.DENY)
    assert not v.permits_trade
    reasons = [o.reason for o in v.outcomes if "missing input" in o.reason]
    assert len(reasons) == len(DOC.rules)


def t_evaluator_exception_fails_closed():
    def boom(rule, facts):
        raise RuntimeError("evaluator blew up")
    v = L.PolicyGate(CFG).evaluate(_facts(), evaluator=boom)
    assert not v.permits_trade
    assert all("fail-closed" in o.reason for o in v.outcomes)


def t_every_rule_appears_in_the_outcome_record():
    """No short-circuit: an investigator needs to know which OTHER limits failed."""
    v = L.PolicyGate(CFG).evaluate(_facts(), evaluator=_evaluator({"EXP-001"}))
    assert len(v.outcomes) == len(DOC.rules)


def t_evaluation_order_is_deterministic_and_id_sorted():
    order = [r.id for r in DOC.evaluation_order()]
    assert order == sorted(order)
    assert order == [r.id for r in DOC.evaluation_order()]


def t_kill_switch_liquidation_exemption():
    gate = L.PolicyGate(CFG)
    # KILL-002 passes (it IS a liquidation) and exempts the settlement rules.
    v = gate.evaluate(_facts(), evaluator=_evaluator({"CASH-001", "KILL-001"}))
    assert v.action is L.RuleAction.ALLOW, (v.action, v.binding_rule_id)
    # But it does NOT exempt exposure rules: liquidation only reduces exposure.
    v2 = gate.evaluate(_facts(), evaluator=_evaluator({"EXP-001"}))
    assert v2.action is L.RuleAction.DENY


# ---- §7: no risk number from the environment --------------------------------
def t_lint_finds_no_violation_in_src():
    violations = L.lint_no_env_risk_reads(ROOT / "src")
    assert not violations, "\n".join(violations)


def t_lint_catches_a_planted_violation(tmp=ROOT / "src" / "_lint_probe_tmp"):
    tmp.mkdir(exist_ok=True)
    probe = tmp / "bad.py"
    try:
        probe.write_text("import os\nMAX_POS = float(os.environ['MAX_POSITION_PCT'])\n",
                         encoding="utf-8")
        v = L.lint_no_env_risk_reads(ROOT / "src")
        assert any("bad.py" in x for x in v), v
        probe.write_text("from os import environ\nX = environ.get('DAILY_LOSS_PCT')\n",
                         encoding="utf-8")
        v = L.lint_no_env_risk_reads(ROOT / "src")
        assert any("bad.py" in x for x in v), "from-import form must be caught too"
        probe.write_text("import os\nX = os.getenv('WEEKLY_LOSS')\n", encoding="utf-8")
        v = L.lint_no_env_risk_reads(ROOT / "src")
        assert any("bad.py" in x for x in v), "os.getenv form must be caught too"
    finally:
        probe.unlink(missing_ok=True)
        tmp.rmdir()


def t_infra_env_refuses_a_non_allowlisted_name():
    raises(L.RiskNumberFromEnvError, lambda: L.infra_env("MAX_POSITION_PCT"))
    L.infra_env("TRADING_DB_URL")          # allowlisted: returns None, does not raise


for _n, _f in sorted((n, f) for n, f in list(globals().items()) if n.startswith("t_")):
    check(_n, _f)

print(f"PASSED {len(PASS)}")
for f in FAIL:
    print("FAILED", f)
sys.exit(1 if FAIL else 0)
