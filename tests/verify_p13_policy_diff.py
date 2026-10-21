"""SPEC-P1.3.1-POLICY-DIFF verification — closes STAGE-1-GAP-AUDIT §10 condition 12.

Two halves:

  A. PINS. Every constitutional rule's governed fields — not only its value — are pinned
     against a literal table in this file. X5R-G9's five mutations each change exactly one
     such field, so each fails here. A pin failure means "this policy differs from the
     constitution", and the remedy is a reviewed change to this table, never to the check.

  B. DIFF. `diff_policies` derives the complete change list from two policy versions and
     classifies every field; `assert_policy_change_authorised` applies the two-person rule
     to that derived list. Every field in `Rule` has at least one classification test.

NO BARE `assert` ANYWHERE IN THIS FILE: `require()` raises unconditionally, so the suite holds
under `python -O` (X5 GAP-2). Run both ways in CI.
"""
import copy
import sys
from decimal import Decimal as D
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import loader as L  # noqa: E402
from config import policy_diff as P  # noqa: E402

PASS: list[str] = []
FAIL: list[str] = []


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


# The REAL file, read through the real loader, so a mutation of config/policy.yaml reaches
# both the pins and the diff fixtures.
CFG = L.PolicyLoader(ROOT / "config").load(require_signature=False)
DOC = CFG.document
RAW = yaml.safe_load((ROOT / "config" / "policy.yaml").read_text(encoding="utf-8"))

E, M = "enforce", "monitor"
DENY, KILL, MODIFY = "DENY", "KILL", "MODIFY"

# =============================================================================
# A. PINS — the constitution, field by field
# =============================================================================
# A rule is constitutional when its authority cites [CONST...] or is marked IMMUTABLE.
# Columns: action, mode, comparison, scope, threshold, on_missing_input, kill_scope,
#          allowed_values, allowed_values_emergency, disallowed_values,
#          (basis, window, timing), inputs
CONSTITUTION = {
    "EXP-001": (DENY, E, "lte", "pool", D("0.050"), DENY, None, None, None, None,
                ("pool_nav", "point_in_time", "pre_trade_intended_post_fill"),
                {"pool_nav", "position_market_value", "intended_fill_quantity", "mark_price"}),
    "EXP-002": (DENY, E, "lte", "pool", D("0.200"), DENY, None, None, None, None,
                ("pool_nav", "point_in_time", "pre_trade_intended_post_fill"),
                {"pool_nav", "sector_classification", "position_market_value",
                 "intended_fill_quantity"}),
    "EXP-003": (DENY, E, "lte", "pool", D("2.0"), DENY, None, None, None, None,
                ("equity", "point_in_time", "pre_trade_intended_post_fill"),
                {"equity", "gross_exposure_value"}),
    "EXP-004": (DENY, E, "lte", "pool", D("1.0"), DENY, None, None, None, None,
                ("equity", "point_in_time", "pre_trade_intended_post_fill"),
                {"equity", "net_exposure_value"}),
    "LOSS-001": (DENY, E, "lte", "pool_and_consolidated", D("0.020"), DENY, None, None, None,
                 None, ("nav_at_session_start", "session", "continuous"),
                 {"nav_at_session_start", "nav_current", "realised_pnl_session",
                  "unrealised_pnl_session"}),
    "LOSS-002": (DENY, E, "lte", "pool_and_consolidated", D("0.050"), DENY, None, None, None,
                 None, ("nav_at_week_start", "sessions:5", "continuous"),
                 {"nav_at_week_start", "nav_current", "realised_pnl_week",
                  "unrealised_pnl_week"}),
    "LOSS-003": (KILL, E, "lte", "pool", D("0.100"), KILL, "POOL", None, None, None,
                 ("peak_nav_from_audit_trail", "since_peak", "continuous"),
                 {"peak_nav_from_audit_trail", "nav_current"}),
    "LOSS-004": (KILL, E, "lte", "consolidated", D("0.100"), KILL, "GLOBAL", None, None, None,
                 ("consolidated_peak_nav_from_audit_trail", "since_peak", "continuous"),
                 {"consolidated_peak_nav_from_audit_trail", "consolidated_nav_current",
                  "fx_rate"}),
    "SIZE-001": (MODIFY, E, "lte", "pool", D("0.010"), DENY, None, None, None, None,
                 ("pool_nav", "point_in_time", "pre_trade_intended_post_fill"),
                 {"pool_nav", "entry_price", "stop_price", "intended_fill_quantity"}),
    "LIQ-001": (MODIFY, E, "lte", "instrument", D("0.010"), DENY, None, None, None, None,
                ("addv_20_session_median", "sessions:20", "pre_trade_intended_post_fill"),
                {"addv_20_session_median", "intended_fill_quantity", "mark_price"}),
    "RATE-001": (DENY, E, "lte", "global", D("20"), DENY, None, None, None, None,
                 ("order_count", "rolling_seconds:60", "pre_trade"),
                 {"order_submission_timestamps"}),
    "RATE-002": (DENY, E, "lte", "strategy", D("10"), DENY, None, None, None, None,
                 ("order_count", "rolling_seconds:60", "pre_trade"),
                 {"order_submission_timestamps", "strategy_id"}),
    "STOP-001": (DENY, E, "eq", "instrument", D("2.5"), DENY, None, None, None, None,
                 ("atr_14_completed_bars", "sessions:14", "at_entry"),
                 {"entry_price", "atr_14_completed_bars"}),
    "EXEC-001": (DENY, E, "in", "instrument", None, DENY, None, ("LIMIT",),
                 ("MARKET", "LIMIT"), None, ("order_type", "point_in_time", "pre_trade"),
                 {"order_type", "is_emergency_exit"}),
    "DATA-001": (DENY, E, "lte", "instrument", D("600"), DENY, None, None, None, None,
                 ("seconds_since_as_of", "point_in_time", "pre_trade"),
                 {"data_as_of", "evaluation_time"}),
    "REGIME-001": (DENY, E, "not_in", "market", None, DENY, None, None, None, ("UNKNOWN",),
                   ("regime_label", "session", "pre_trade"), {"regime_label"}),
    "KILL-001": (DENY, E, "in", "global", None, DENY, None, ("ARMED",), None, None,
                 ("kill_switch_state", "point_in_time", "pre_trade"), {"kill_switch_state"}),
    "AUDIT-001": (DENY, E, "exists", "global", None, DENY, None, None, None, None,
                  ("audit_event_id", "point_in_time", "pre_trade"), {"audit_event_id"}),
    "LLM-001": (DENY, E, "eq", "global", None, DENY, None, (False,), None, None,
                ("llm_prompt_contains_portfolio_state", "point_in_time", "pre_llm_call"),
                {"llm_prompt_contains_portfolio_state"}),
    "LLM-002": (DENY, E, "exists", "global", None, DENY, None, None, None, None,
                ("sanitiser_version", "point_in_time", "pre_llm_call"),
                {"sanitiser_version", "content_is_sanitised"}),
}


def _v(x):
    return None if x is None else getattr(x, "value", x)


def _pin(rid):
    (action, mode, cmp, scope, thr, omi, ks, av, ave, dv, meas, inputs) = CONSTITUTION[rid]
    r = DOC.rule(rid)
    pairs = [
        ("action", _v(r.action), action),
        ("mode", _v(r.mode), mode),
        ("comparison", _v(r.comparison), cmp),
        ("scope", _v(r.scope), scope),
        ("on_missing_input", _v(r.on_missing_input), omi),
        ("kill_scope", _v(r.kill_scope), ks),
        ("allowed_values", r.allowed_values, av),
        ("allowed_values_emergency",
         None if r.allowed_values_emergency is None else frozenset(r.allowed_values_emergency),
         None if ave is None else frozenset(ave)),
        ("disallowed_values", r.disallowed_values, dv),
        ("measurement", (r.measurement.basis, r.measurement.window, r.measurement.timing),
         meas),
        ("inputs", set(r.inputs), inputs),
        ("threshold_ref", r.threshold_ref, None),
        ("threshold_input", r.threshold_input, None),
        ("modify", r.modify is None, r.action is not L.RuleAction.MODIFY),
    ]
    for name, got, want in pairs:
        require(got == want, f"{rid}.{name} is {got!r}; the constitution says {want!r}")
    got_t = None if r.threshold is None else D(str(r.threshold))
    require(got_t == thr, f"{rid}.threshold is {got_t}; the constitution says {thr}")
    require(r.binds, f"{rid} does not bind: a constitutional rule in monitor mode is decorative")


def _make_pin_test(rid):
    def t():
        _pin(rid)
    t.__name__ = f"t_pin_{rid}"
    return t


for _rid in CONSTITUTION:
    globals()[f"t_pin_{_rid.replace('-', '_')}"] = _make_pin_test(_rid)


def t_constitutional_set_is_exactly_the_table():
    """A rule cannot leave the constitution by having its authority edited, and a new
    [CONST] rule cannot arrive unpinned."""
    have = {r.id for r in DOC.rules
            if "[CONST" in r.authority or "IMMUTABLE" in r.authority}
    require(have == set(CONSTITUTION),
            f"constitutional rules {sorted(have)} != pinned {sorted(CONSTITUTION)}")


def t_exemption_scope_is_pinned():
    """KILL-002 is the only exemption in the system. Growing it loosens the gate; shrinking
    it can trap a liquidation. Either way it changes only with this table."""
    r = DOC.rule("KILL-002")
    require(r.action is L.RuleAction.ALLOW and r.mode is L.RuleMode.ENFORCE, "KILL-002 shape")
    require(set(r.exempts) == {"CASH-001", "CASH-002", "KILL-001", "HOLD-001", "TURN-001",
                               "TURN-002", "EXEC-001"}, f"KILL-002.exempts {r.exempts}")
    others = [x.id for x in DOC.rules if x.exempts and x.id != "KILL-002"]
    require(not others, f"exemption rules other than KILL-002: {others}")


# =============================================================================
# B. DIFF — fixtures
# =============================================================================
def _raw():
    return copy.deepcopy(RAW)


def _rule_raw(doc, rid):
    for r in doc["rules"]:
        if r["id"] == rid:
            return r
    raise KeyError(rid)


def _edit(rid, **fields):
    new = _raw()
    r = _rule_raw(new, rid)
    for k, v in fields.items():
        if v is _DROP:
            r.pop(k, None)
        else:
            r[k] = v
    return new


_DROP = object()


def _only(diff, path=None, field=None):
    cs = [c for c in diff.changes
          if (path is None or c.path == path) and (field is None or c.field == field)]
    require(len(cs) == 1, f"expected one change at {path or field}, got {list(diff.changes)}")
    return cs[0]


def _dir(new, rid, field):
    return _only(P.diff_policies(RAW, new), path=f"rules.{rid}.{field}").direction


LO, TI, NE, UN = (P.Direction.LOOSENS, P.Direction.TIGHTENS, P.Direction.NEUTRAL,
                  P.Direction.UNDECIDABLE)


# ---- the five X5R-G9 mutations, through the diff -----------------------------
X5R_G9 = {
    "EXP-002 action -> ALLOW": ("EXP-002", "action", {"action": "ALLOW"}),
    "LOSS-001 mode -> monitor": ("LOSS-001", "mode", {"mode": "monitor"}),
    "LOSS-004 threshold -> 20%": ("LOSS-004", "threshold", {"threshold": 0.200}),
    "EXEC-001 allows MARKET": ("EXEC-001", "allowed_values",
                               {"allowed_values": ["LIMIT", "MARKET"]}),
    "STOP-001 comparison -> lte": ("STOP-001", "comparison", {"comparison": "lte"}),
}


def t_x5r_g9_each_mutation_is_a_loosening_needing_two_people():
    for label, (rid, field, edit) in X5R_G9.items():
        new = _edit(rid, **edit)
        d = P.diff_policies(RAW, new)
        c = _only(d, path=f"rules.{rid}.{field}")
        require(c.direction is LO, f"{label}: classified {c.direction.value}, expected LOOSENS")
        require(len(d.changes) == 1, f"{label}: expected exactly one change, got {d.changes}")
        raises(L.PolicyGovernanceError,
               lambda n=new: P.assert_policy_change_authorised(RAW, n, ["js"]),
               f"{label} with one approver: ")
        raises(L.PolicyGovernanceError,
               lambda n=new: P.assert_policy_change_authorised(RAW, n, ["js", " JS"]),
               f"{label} with one person twice: ")
        P.assert_policy_change_authorised(RAW, new, ["js", "second-owner"])


# ---- completeness ------------------------------------------------------------
def t_every_rule_field_is_classified():
    """A field added to `Rule` without a classification would be invisible to governance."""
    require(set(P.RULE_FIELDS) == set(L.Rule.model_fields),
            f"unclassified: {sorted(set(L.Rule.model_fields) - set(P.RULE_FIELDS))}; "
            f"stale: {sorted(set(P.RULE_FIELDS) - set(L.Rule.model_fields))}")


def t_identical_versions_have_no_changes():
    d = P.diff_policies(RAW, _raw())
    require(d.changes == () and not d.requires_two_person, f"{d.changes}")
    P.assert_policy_change_authorised(RAW, _raw(), [])


def t_diff_is_deterministic_and_path_ordered():
    new = _edit("EXP-001", threshold=0.08, severity="LOW", notes="changed")
    new["portfolio"]["min_cash_pct"] = 0.10
    a, b = P.diff_policies(RAW, new), P.diff_policies(RAW, copy.deepcopy(new))
    require(a == b, "same inputs must give the same record")
    keys = [(c.path, c.field or "") for c in a.changes]
    require(keys == sorted(keys), f"not path-ordered: {keys}")


# ---- action, mode, severity, on_missing_input, kill_scope ----------------------
def t_action_follows_the_lattice():
    require(_dir(_edit("EXP-002", action="ALLOW"), "EXP-002", "action") is LO, "DENY->ALLOW")
    require(_dir(_edit("SIZE-001", action="DENY", modify=_DROP), "SIZE-001", "action") is TI,
            "MODIFY->DENY")
    require(_dir(_edit("EXP-001", action="KILL", kill_scope="POOL"), "EXP-001", "action")
            is TI, "DENY->KILL")
    require(_dir(_edit("LOSS-003", action="DENY", kill_scope=_DROP), "LOSS-003", "action")
            is LO, "KILL->DENY")


def t_mode_enforce_to_monitor_loosens_and_back_tightens():
    require(_dir(_edit("LOSS-001", mode="monitor"), "LOSS-001", "mode") is LO, "to monitor")
    require(_dir(_edit("PORT-002", mode="enforce"), "PORT-002", "mode") is TI,
            "promotion to enforce is a tightening (Q-P1.3-4)")


def t_monitor_rule_threshold_cannot_be_laundered():
    """Loosen a MONITOR rule's threshold (free if mode excused it), then promote it to enforce
    (free: a tightening). Two free steps would equal one unapproved loosening. So a monitor
    rule's predicate is classified as if it bound."""
    require(_dir(_edit("CASH-002", threshold=5), "CASH-002", "threshold") is LO,
            "monitor rule loosened must still be LOOSENS")


def t_severity_on_missing_input_and_kill_scope():
    require(_dir(_edit("EXP-001", severity="LOW"), "EXP-001", "severity") is LO, "sev down")
    require(_dir(_edit("HOLD-002", severity="CRITICAL"), "HOLD-002", "severity") is TI, "sev up")
    require(_dir(_edit("LOSS-003", on_missing_input="DENY"), "LOSS-003", "on_missing_input")
            is LO, "KILL->DENY on missing")
    require(_dir(_edit("EXP-001", on_missing_input="KILL"), "EXP-001", "on_missing_input")
            is TI, "DENY->KILL on missing")
    require(_dir(_edit("LOSS-004", kill_scope="POOL"), "LOSS-004", "kill_scope") is LO,
            "GLOBAL->POOL")
    require(_dir(_edit("LOSS-003", kill_scope="GLOBAL"), "LOSS-003", "kill_scope") is TI,
            "POOL->GLOBAL")


# ---- scope -------------------------------------------------------------------
def t_scope_nests_only_in_the_pool_family():
    require(_dir(_edit("LOSS-001", scope="pool"), "LOSS-001", "scope") is LO,
            "dropping consolidated evaluation loosens (ADR-15)")
    require(_dir(_edit("LOSS-003", scope="pool_and_consolidated"), "LOSS-003", "scope") is TI,
            "adding consolidated evaluation tightens")
    require(_dir(_edit("RATE-002", scope="global"), "RATE-002", "scope") is UN,
            "strategy->global counts a different population")
    require(_dir(_edit("EXP-001", scope="instrument"), "EXP-001", "scope") is UN, "pool->inst")


# ---- comparison and threshold, jointly ----------------------------------------
def t_threshold_direction_respects_comparison():
    require(_dir(_edit("LOSS-004", threshold=0.2), "LOSS-004", "threshold") is LO, "lte up")
    require(_dir(_edit("EXP-001", threshold=0.04), "EXP-001", "threshold") is TI, "lte down")
    require(_dir(_edit("PORT-001", threshold=0.10), "PORT-001", "threshold") is LO, "gte down")
    require(_dir(_edit("PORT-001", threshold=0.30), "PORT-001", "threshold") is TI, "gte up")
    require(_dir(_edit("RECON-001", threshold=1), "RECON-001", "threshold") is UN,
            "eq moved: {0} vs {1} share nothing")


def t_comparison_changes_by_pass_set():
    require(_dir(_edit("STOP-001", comparison="lte"), "STOP-001", "comparison") is LO, "eq->lte")
    require(_dir(_edit("EXP-001", comparison="lt"), "EXP-001", "comparison") is TI, "lte->lt")
    require(_dir(_edit("HOLD-001", comparison="gt"), "HOLD-001", "comparison") is UN,
            "gte->gt tightens, but HOLD-001 gates an exit")
    require(_dir(_edit("EDGE-001", comparison="gt"), "EDGE-001", "comparison") is TI, "gte->gt")
    require(_dir(_edit("EXP-001", comparison="gte"), "EXP-001", "comparison") is UN,
            "lte->gte inverts the predicate: incomparable")
    require(_dir(_edit("EXP-001", comparison="eq"), "EXP-001", "comparison") is TI,
            "lte->eq: {t} is inside (-inf, t]")


def t_comparison_and_threshold_moving_together_are_judged_together():
    new = _edit("EXP-001", comparison="lt", threshold=0.10)   # (-inf,.05] -> (-inf,.10)
    d = P.diff_policies(RAW, new)
    for c in d.for_rule("EXP-001"):
        require(c.direction is LO, f"{c.field}: {c.direction}")
    new2 = _edit("EXP-001", comparison="lt", threshold=0.05)  # strictly inside
    require(all(c.direction is TI for c in P.diff_policies(RAW, new2).for_rule("EXP-001")),
            "lte .05 -> lt .05 tightens")


def t_threshold_source_switch_is_undecidable():
    require(_dir(_edit("EXP-001", threshold=_DROP, threshold_ref="portfolio.max_position_pct"),
                 "EXP-001", "threshold") is UN, "constant -> reference")
    require(_dir(_edit("UNIV-004", threshold_ref="universe.{market}.min_reported_quarters"),
                 "UNIV-004", "threshold_ref") is UN, "reference repointed")
    new = _edit("CASH-001", threshold_input="cash", inputs=["cash", "settled_cash",
                                                             "intended_notional"])
    require(_only(P.diff_policies(RAW, new), path="rules.CASH-001.threshold_input").direction
            is UN, "measured bound swapped")
    require(_dir(_edit("CASH-001", comparison="lt"), "CASH-001", "comparison") is TI,
            "same measured bound, strict comparison: decidable")


def t_undecidable_fails_closed_for_approval():
    new = _edit("EXP-001", comparison="gte")
    d = P.diff_policies(RAW, new)
    require(d.by_direction(UN) and d.requires_two_person, "UNDECIDABLE must gate")
    raises(L.PolicyGovernanceError, lambda: P.assert_policy_change_authorised(RAW, new, ["js"]))


# ---- value sets ---------------------------------------------------------------
def t_value_sets():
    require(_dir(_edit("EXEC-001", allowed_values=["LIMIT", "MARKET"]), "EXEC-001",
                 "allowed_values") is LO, "in: grew")
    require(_dir(_edit("INST-002", allowed_values=["ACTIVE", "HALTED"]), "INST-002",
                 "allowed_values") is LO, "in: HALTED admitted")
    require(_dir(_edit("KILL-001", allowed_values=["ARMED", "TRIPPED"]), "KILL-001",
                 "allowed_values") is LO, "KILL-001 admitting TRIPPED")
    require(_dir(_edit("REGIME-001", disallowed_values=["UNKNOWN", "BEAR"]), "REGIME-001",
                 "disallowed_values") is TI, "not_in: grew")
    raises(P.PolicyDiffError,
           lambda: P.diff_policies(RAW, _edit("REGIME-001", disallowed_values=[])),
           "an emptied not_in set is rejected by the model before the diff: ")
    require(_dir(_edit("REGIME-001", disallowed_values=["UNKNOWN", "BEAR"]), "REGIME-001",
                 "disallowed_values") is TI, "not_in: grew")
    require(_dir(_edit("LLM-001", allowed_values=[True]), "LLM-001", "allowed_values") is UN,
            "eq with a value: no set semantics")
    require(_dir(_edit("INST-001", allowed_values_ref="instrument_allowlist.read_only"),
                 "INST-001", "allowed_values_ref") is UN, "ref repointed")


def t_emergency_and_exemption_sets_never_tighten():
    """The challenge to ADR-09 row 3: shrinking these pass sets makes it harder to EXIT."""
    require(_dir(_edit("EXEC-001", allowed_values_emergency=["LIMIT"]), "EXEC-001",
                 "allowed_values_emergency") is UN, "emergency set shrank")
    require(_dir(_edit("EXEC-001", allowed_values_emergency=["MARKET", "LIMIT", "STOP"]),
                 "EXEC-001", "allowed_values_emergency") is LO, "emergency set grew")
    shrink = _edit("KILL-002", exempts=["CASH-002", "KILL-001", "HOLD-001", "TURN-001",
                                        "TURN-002", "EXEC-001"])
    c = _only(P.diff_policies(RAW, shrink), path="rules.KILL-002.exempts")
    require(c.direction is UN and "CASH-001" in c.reason, c.reason)
    grow = _edit("KILL-002", exempts=list(DOC.rule("KILL-002").exempts) + ["EXP-001"])
    require(_dir(grow, "KILL-002", "exempts") is LO, "exemption grew")
    raises(L.PolicyGovernanceError,
           lambda: P.assert_policy_change_authorised(RAW, shrink, ["js"]),
           "single operator must not be able to narrow the liquidation exemption: ")


def t_liquidation_path_set_is_pinned():
    """Every rule here must (a) exist, (b) not be exempted by KILL-002, and (c) have a tunable
    predicate. A rule leaving or joining the set is a reviewed change to this line."""
    require(P.LIQUIDATION_PATH_RULES == {"RATE-001", "RATE-002", "DATA-001", "LIQ-001"},
            f"{sorted(P.LIQUIDATION_PATH_RULES)}")
    exempt = set(DOC.rule("KILL-002").exempts)
    for rid in P.LIQUIDATION_PATH_RULES:
        r = DOC.rule(rid)
        require(rid not in exempt, f"{rid} is exempt, so it cannot block liquidation")
        require(r.threshold is not None, f"{rid} has no tunable threshold")


def t_tightening_a_liquidation_path_rule_is_undecidable():
    require(_dir(_edit("RATE-001", threshold=1), "RATE-001", "threshold") is UN,
            "1 order/min stalls a kill-switch liquidation")
    require(_dir(_edit("DATA-001", threshold=1), "DATA-001", "threshold") is UN,
            "a 1-second staleness bound denies liquidation on any quiet tape")
    require(_dir(_edit("RATE-001", threshold=40), "RATE-001", "threshold") is LO,
            "loosening stays a loosening")
    raises(L.PolicyGovernanceError,
           lambda: P.assert_policy_change_authorised(RAW, _edit("RATE-001", threshold=1), ["js"]))


def t_exit_gate_tightening_is_undecidable():
    require(_dir(_edit("HOLD-001", threshold=30), "HOLD-001", "threshold") is UN,
            "a 30-session minimum hold traps positions; not a provable tightening")
    require(_dir(_edit("HOLD-001", threshold=1), "HOLD-001", "threshold") is LO,
            "a shorter minimum hold is a plain loosening of the rule")
    require(_dir(_edit("KILL-002", mode="monitor"), "KILL-002", "mode") is UN,
            "mode does not gate exemptions in PolicyGate (F-3)")


# ---- inputs, measurement, modify, text, authority ------------------------------
def t_inputs():
    r = DOC.rule("EXP-001")
    require(_dir(_edit("EXP-001", inputs=list(r.inputs) + ["fx_rate"]), "EXP-001", "inputs")
            is TI, "input added")
    c = _only(P.diff_policies(RAW, _edit("EXP-001", inputs=list(r.inputs)[:-1])),
              path="rules.EXP-001.inputs")
    require(c.direction is LO and "mark_price" in c.reason, c.reason)
    require(_dir(_edit("EXP-001", inputs=["pool_nav", "x"]), "EXP-001", "inputs") is UN,
            "swapped")


def t_measurement_changes_are_undecidable():
    m = dict(_rule_raw(RAW, "LOSS-002")["measurement"])
    for sub, val in (("window", "sessions:3"), ("basis", "nav_current"),
                     ("timing", "end_of_session")):
        mm = dict(m, **{sub: val})
        c = _only(P.diff_policies(RAW, _edit("LOSS-002", measurement=mm)),
                  path=f"rules.LOSS-002.measurement.{sub}")
        require(c.direction is UN, f"{sub}: {c.direction}")


def t_modify_block():
    require(_dir(_edit("EXP-006", modify={"target": "position_weight_pct", "to": 0.06}),
                 "EXP-006", "modify.to") is LO, "trim to a larger weight")
    require(_dir(_edit("EXP-006", modify={"target": "position_weight_pct", "to": 0.03}),
                 "EXP-006", "modify.to") is TI, "trim to a smaller weight")
    require(_dir(_edit("SIZE-001", modify={"target": "order_quantity", "to": "half"}),
                 "SIZE-001", "modify.to") is UN, "symbolic")
    require(_dir(_edit("SIZE-001", modify={"target": "order_notional",
                                           "to": "max_quantity_within_risk_budget"}),
                 "SIZE-001", "modify.target") is UN, "target")


def t_text_is_neutral_and_authority_is_not():
    require(_dir(_edit("EXP-001", description="Single position cap, reworded."), "EXP-001",
                 "description") is NE, "description")
    require(_dir(_edit("EXP-001", notes="new notes"), "EXP-001", "notes") is NE, "notes")
    require(_dir(_edit("EXP-001", authority="ADR-14"), "EXP-001", "authority") is UN,
            "re-attributing a [CONST] rule")
    P.assert_policy_change_authorised(RAW, _edit("EXP-001", notes="typo fixed"), [])


# ---- rule addition and removal --------------------------------------------------
def _new_rule(**kw):
    base = dict(id="EXP-099", description="test rule added in a diff", authority="ADR-14",
                scope="pool", mode="enforce", severity="HIGH", threshold=0.5,
                comparison="lte", measurement={"basis": "pool_nav", "window": "point_in_time",
                                               "timing": "pre_trade"},
                inputs=["pool_nav"], action="DENY", on_missing_input="DENY")
    base.update(kw)
    return base


def t_rule_addition_and_removal():
    for kw, want in (({}, TI), ({"mode": "monitor"}, NE), ({"action": "ALLOW"}, NE),
                     ({"measurement": {"basis": "x", "window": "since_entry",
                                       "timing": "pre_exit"}}, UN),
                     ({"action": "ALLOW", "exempts": ["EXP-001"]}, LO)):
        new = _raw()
        new["rules"].append(_new_rule(**kw))
        c = _only(P.diff_policies(RAW, new), path="rules.EXP-099")
        require(c.kind is P.ChangeKind.RULE_ADDED and c.direction is want,
                f"add {kw}: {c.direction}")
    gone = _raw()
    gone["rules"] = [r for r in gone["rules"] if r["id"] != "EXP-002"]
    c = _only(P.diff_policies(RAW, gone), path="rules.EXP-002")
    require(c.kind is P.ChangeKind.RULE_REMOVED and c.direction is LO, f"{c}")
    raises(L.PolicyGovernanceError, lambda: P.assert_policy_change_authorised(RAW, gone, ["js"]))
    nok = _raw()
    nok["rules"] = [r for r in nok["rules"] if r["id"] != "KILL-002"]
    require(_only(P.diff_policies(RAW, nok), path="rules.KILL-002").direction is UN, "KILL-002")


def t_remove_and_readd_under_a_new_id_is_caught():
    """Renaming a rule to dodge its pins: EXP-001 removed, EXP-007 added at 8%. The removal is
    a loosening on its own, whatever the addition is."""
    new = _raw()
    r = copy.deepcopy(_rule_raw(new, "EXP-001"))
    new["rules"] = [x for x in new["rules"] if x["id"] != "EXP-001"]
    r.update(id="EXP-007", threshold=0.08)
    new["rules"].append(r)
    d = P.diff_policies(RAW, new)
    require(_only(d, path="rules.EXP-001").direction is LO, "removal")
    require(d.requires_two_person, "rename must gate")


# ---- non-rule configuration ------------------------------------------------------
def _cfg(path_value_pairs):
    new = _raw()
    for path, val in path_value_pairs:
        node = new
        *head, last = path.split(".")
        for k in head:
            node = node[k]
        node[last] = val
    return new


def _cdir(path, val):
    return _only(P.diff_policies(RAW, _cfg([(path, val)])), path=path).direction


def t_config_keys_rules_read_are_governed():
    require(_cdir("universe.US.min_price_usd", "1.00") is LO, "UNIV-001's floor lowered")
    require(_cdir("cost.assumed_round_trip_bps.US", 5) is LO, "EDGE-001's cost lowered")
    require(_cdir("cost.assumed_round_trip_bps.US", 40) is TI, "cost raised")
    require(_cdir("portfolio.max_position_pct", 0.08) is LO, "duplicate of EXP-001 raised")
    require(_cdir("portfolio.min_cash_pct", 0.10) is LO, "PORT-001's buffer lowered")
    require(_cdir("account.enforce_settled_cash", False) is LO, "settled-cash off")
    require(_cdir("instrument_allowlist.tradeable", ["COMMON_STOCK", "ETF"]) is LO, "ETF")
    require(_cdir("instrument_allowlist.permanently_banned", ["FUTURE"]) is LO, "options ok")
    require(_cdir("instrument_allowlist.tradeable", ["ETF"]) is UN, "swap")
    require(_cdir("llm.gate_width", 30) is LO, "wider LLM gate")
    require(_cdir("metadata.description", "reworded") is NE, "metadata")
    require(_cdir("policy_version", "0.1.1") is NE, "version")
    require(_cdir("schedule.US.pipeline_utc", "23:00") is UN, "unlisted key")


def t_config_key_added_or_removed():
    new = _raw()
    new["portfolio"]["max_gross_override"] = 3
    c = _only(P.diff_policies(RAW, new), path="portfolio.max_gross_override")
    require(c.kind is P.ChangeKind.CONFIG_ADDED and c.direction is UN, f"{c}")
    gone = _raw()
    del gone["universe"]["US"]["min_price_usd"]
    c = _only(P.diff_policies(RAW, gone), path="universe.US.min_price_usd")
    require(c.kind is P.ChangeKind.CONFIG_REMOVED and c.direction is LO, f"{c}")


def t_every_config_leaf_has_a_rule_in_the_table():
    """The table ends in `**` -> UNDECIDABLE, so this is a coverage REPORT, not a gap: it
    pins that the default stays fail-closed."""
    require(P.CONFIG_KEY_DIRECTIONS[-1] == ("**", P.KeyDirection.UNDECIDABLE),
            "the catch-all must stay last and UNDECIDABLE")
    require(P.key_direction("anything.new.here") is P.KeyDirection.UNDECIDABLE, "default")


# ---- authorisation ---------------------------------------------------------------
def t_mixed_change_set_needs_two_people():
    new = _edit("EXP-001", threshold=0.04)              # tightens
    _rule_raw(new, "EXP-002")["threshold"] = 0.25        # loosens
    raises(L.PolicyGovernanceError, lambda: P.assert_policy_change_authorised(RAW, new, ["js"]))
    P.assert_policy_change_authorised(RAW, new, ["js", "second-owner"])


def t_pure_tightening_needs_nobody():
    new = _edit("EXP-001", threshold=0.04)
    _rule_raw(new, "LOSS-001")["threshold"] = 0.015
    new["portfolio"]["min_cash_pct"] = 0.25
    d = P.assert_policy_change_authorised(RAW, new, [])
    require(all(c.direction is TI for c in d.changes), f"{d.changes}")


def t_approval_threshold_comes_from_the_active_version():
    """A version that changes its own approval count must not be judged by it."""
    old = _raw()
    old["governance"]["min_approvals_to_loosen"] = 3
    new = copy.deepcopy(old)
    new["governance"]["min_approvals_to_loosen"] = 2
    _rule_raw(new, "EXP-002")["threshold"] = 0.25
    raises(L.PolicyGovernanceError,
           lambda: P.assert_policy_change_authorised(old, new, ["a", "b"]),
           "two approvers against an active threshold of three: ")
    P.assert_policy_change_authorised(old, new, ["a", "b", "c"])


def t_unvalidatable_version_authorises_nothing():
    bad = _edit("EXP-001", on_missing_input="ALLOW")
    raises(P.PolicyDiffError, lambda: P.diff_policies(RAW, bad))
    raises(L.PolicyError, lambda: P.assert_policy_change_authorised(RAW, bad, ["a", "b", "c"]))


def t_diff_agrees_with_loosens_for_on_every_ordinal_threshold():
    """The diff supersedes `loosens_for` for approval, so it must never disagree with it on
    the one case `loosens_for` decides."""
    for r in DOC.rules:
        if r.threshold is None or r.comparison not in (
                L.Comparison.LTE, L.Comparison.LT, L.Comparison.GTE, L.Comparison.GT):
            continue
        for factor in (D("1.5"), D("0.5")):
            old_t = D(str(r.threshold))
            new_t = old_t * factor if old_t else D("1")
            if "pct" in r.measurement.basis and new_t > 1:
                continue
            got = _dir(_edit(r.id, threshold=float(new_t)), r.id, "threshold")
            lf = L.loosens_for(L.LimitChange(rule_id=r.id, field="threshold",
                                             old_value=old_t, new_value=new_t), r)
            exit_gate = (r.measurement.timing == "pre_exit"
                         or r.id in P.LIQUIDATION_PATH_RULES)
            want = LO if lf else (UN if exit_gate else TI)
            require(got is want, f"{r.id} x{factor}: diff {got.value}, loosens_for {lf}")


for _n, _f in sorted((n, f) for n, f in list(globals().items())
                     if n.startswith("t_") and callable(f)):
    check(_n, _f)

print(f"PASSED {len(PASS)}")
for _msg in FAIL:
    print("FAILED", _msg)
sys.exit(1 if FAIL else 0)
