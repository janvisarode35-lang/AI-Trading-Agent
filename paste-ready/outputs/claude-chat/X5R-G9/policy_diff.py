"""SPEC-P1.3.1-POLICY-DIFF v0.1 — derive and classify every change between two policy versions.

Closes X5R-G2. Before this module, SPEC-P1.3 §5.3's two-person rule could see exactly one kind
of change — a numeric threshold — and only when a caller hand-built a `LimitChange` for it. A
change of `action`, `mode`, `comparison`, `scope`, a removed rule, or a moved config key that a
rule reads was invisible to governance and therefore flowed down the zero-approval path.

The contract here is the reverse: the change list is DERIVED from the two documents, never
supplied by the person asking for approval, and every difference is classified

    LOOSENS | TIGHTENS | NEUTRAL | UNDECIDABLE

UNDECIDABLE is a real outcome, not an error, and for approval purposes it IS a loosening
(`requires_two_person`). If this module cannot prove a change tightens, it does not get the
tightening path. That is [CONST-6] applied to governance.

Direction is always judged on the PASS SET of the rule: the set of observed values for which
the rule does not act. A change that shrinks the pass set makes the rule act more often and
tightens it; a change that grows it loosens it; a change to an incomparable set is
UNDECIDABLE. `lte 0.05 -> lte 0.08`, `eq 2.5 -> lte 2.5`, `[LIMIT] -> [LIMIT, MARKET]` are the
same operation seen through three fields.

ONE DELIBERATE EXCEPTION TO "SMALLER PASS SET = SAFER": a rule that can block a RISK-REDUCING
action. Narrowing the kill-switch liquidation exemption (KILL-002), narrowing the emergency
order types (EXEC-001.allowed_values_emergency), or raising the minimum hold on an exit
(HOLD-001, timing `pre_exit`) all shrink a pass set — and all make it harder to get OUT of a
position. Those are classified UNDECIDABLE, never TIGHTENS, so a single operator cannot
disable the exit path under the banner of "tightening is always safe" (ADR-09 row 3).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from enum import Enum
from fnmatch import fnmatchcase
from typing import Any, Final

from pydantic import BaseModel, ConfigDict

from .loader import (
    Comparison,
    Governance,
    KillScope,
    PolicyDocument,
    PolicyError,
    PolicyGovernanceError,
    Rule,
    RuleAction,
    RuleMode,
    RuleScope,
    Severity,
)

# =============================================================================
# 1. TYPES
# =============================================================================


class PolicyDiffError(PolicyError):
    """One of the two versions could not be validated, so no change list exists.

    Fail-closed: a diff that cannot be computed authorises nothing.
    """


class Direction(str, Enum):
    LOOSENS = "LOOSENS"
    TIGHTENS = "TIGHTENS"
    NEUTRAL = "NEUTRAL"
    UNDECIDABLE = "UNDECIDABLE"


class ChangeKind(str, Enum):
    RULE_ADDED = "RULE_ADDED"
    RULE_REMOVED = "RULE_REMOVED"
    RULE_FIELD = "RULE_FIELD"
    CONFIG_ADDED = "CONFIG_ADDED"
    CONFIG_REMOVED = "CONFIG_REMOVED"
    CONFIG_VALUE = "CONFIG_VALUE"


class PolicyChange(BaseModel):
    """One classified difference between two policy versions.

    `path` is `rules.<RULE-ID>.<field>` for a rule field, `rules.<RULE-ID>` for an added or
    removed rule, and the dotted config path otherwise. `old`/`new` are canonical strings
    (Decimal rendered by `str`, sets sorted) so the record is byte-reproducible; `None` means
    "absent in that version", which is distinct from the string "None".
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ChangeKind
    path: str
    rule_id: str | None
    field: str | None
    old: str | None
    new: str | None
    direction: Direction
    reason: str

    @property
    def requires_two_person(self) -> bool:
        """UNDECIDABLE is treated as LOOSENS for approval purposes (SPEC-P1.3.1 §4)."""
        return self.direction in (Direction.LOOSENS, Direction.UNDECIDABLE)


class PolicyDiff(BaseModel):
    """The complete, ordered change list between two policy versions.

    Ordered by `path` ascending, so two runs of the diff over the same pair of documents
    produce the same record (the same property §4.2 buys for evaluation order).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    old_version: str
    new_version: str
    changes: tuple[PolicyChange, ...]

    @property
    def requires_two_person(self) -> bool:
        return any(c.requires_two_person for c in self.changes)

    def by_direction(self, d: Direction) -> tuple[PolicyChange, ...]:
        return tuple(c for c in self.changes if c.direction is d)

    def for_rule(self, rule_id: str) -> tuple[PolicyChange, ...]:
        return tuple(c for c in self.changes if c.rule_id == rule_id)


# =============================================================================
# 2. PASS-SET ALGEBRA FOR ORDINAL COMPARISONS
# =============================================================================
#
# A bound is either a Decimal (a constant threshold) or an opaque token (a threshold_ref or a
# threshold_input). Two tokens are comparable only when they are the SAME token: `lte
# settled_cash -> lt settled_cash` is decidable (pass set shrinks), `lte settled_cash -> lte
# cash` is not.

_ORDINAL: Final = frozenset({Comparison.LTE, Comparison.LT, Comparison.GTE, Comparison.GT,
                             Comparison.EQ})


class _Incomparable(Exception):
    pass


def _cmp_bounds(a: Any, b: Any) -> int:
    if isinstance(a, Decimal) and isinstance(b, Decimal):
        return (a > b) - (a < b)
    if a == b:
        return 0
    raise _Incomparable


def _interval(cmp: Comparison, t: Any) -> tuple[Any, bool, Any, bool]:
    """(lo, lo_closed, hi, hi_closed); None is an infinite end."""
    if cmp is Comparison.LTE:
        return (None, False, t, True)
    if cmp is Comparison.LT:
        return (None, False, t, False)
    if cmp is Comparison.GTE:
        return (t, True, None, False)
    if cmp is Comparison.GT:
        return (t, False, None, False)
    return (t, True, t, True)  # EQ


def _subset(a: tuple, b: tuple) -> bool:
    alo, alc, ahi, ahc = a
    blo, blc, bhi, bhc = b
    if blo is not None:
        if alo is None:
            return False
        c = _cmp_bounds(alo, blo)
        if c < 0 or (c == 0 and alc and not blc):
            return False
    if bhi is not None:
        if ahi is None:
            return False
        c = _cmp_bounds(ahi, bhi)
        if c > 0 or (c == 0 and ahc and not bhc):
            return False
    return True


def _set_direction(old_pass: frozenset | tuple, new_pass: frozenset | tuple) -> Direction:
    """Direction from two pass sets (or two intervals). Smaller pass set = rule acts more."""
    try:
        if isinstance(old_pass, frozenset):
            sub, sup = new_pass <= old_pass, new_pass >= old_pass
        else:
            sub, sup = _subset(new_pass, old_pass), _subset(old_pass, new_pass)
    except _Incomparable:
        return Direction.UNDECIDABLE
    if sub and sup:
        return Direction.NEUTRAL
    if sub:
        return Direction.TIGHTENS
    if sup:
        return Direction.LOOSENS
    return Direction.UNDECIDABLE


def _bound(rule: Rule) -> Any:
    if rule.threshold is not None:
        return Decimal(str(rule.threshold))
    if rule.threshold_ref is not None:
        return ("ref", rule.threshold_ref)
    if rule.threshold_input is not None:
        return ("input", rule.threshold_input)
    return None


# =============================================================================
# 3. RULE-LEVEL CLASSIFICATION  (SPEC-P1.3.1 §3)
# =============================================================================

#: Lower index = acts more strongly. Moving toward index 0 tightens.
_ACTION_RANK: Final = {RuleAction.KILL: 0, RuleAction.DENY: 1, RuleAction.MODIFY: 2,
                       RuleAction.ALLOW: 3}
_SEVERITY_RANK: Final = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2,
                         Severity.LOW: 3}
_KILL_SCOPE_RANK: Final = {KillScope.GLOBAL: 0, KillScope.POOL: 1}

#: Scopes as COVERAGE sets. Only the pool/consolidated family nests; every other pair of
#: scopes measures a different population and is incomparable.
_SCOPE_COVERAGE: Final = {
    RuleScope.POOL: frozenset({"pool"}),
    RuleScope.CONSOLIDATED: frozenset({"consolidated"}),
    RuleScope.POOL_AND_CONSOLIDATED: frozenset({"pool", "consolidated"}),
}

#: Free text. Changing it changes no verdict.
_TEXT_FIELDS: Final = frozenset({"description", "notes"})

#: Fields compared for every rule present in both versions. A field added to `Rule` without
#: being added here is caught by `t_every_rule_field_is_classified`, not silently ignored.
RULE_FIELDS: Final[tuple[str, ...]] = (
    "action", "allowed_values", "allowed_values_emergency", "allowed_values_ref",
    "authority", "comparison", "description", "disallowed_values", "exempts", "id",
    "inputs", "kill_scope", "measurement", "mode", "modify", "notes", "on_missing_input",
    "scope", "severity", "threshold", "threshold_input", "threshold_ref",
)


def _rank_direction(rank: Mapping, old: Any, new: Any) -> Direction:
    if rank[new] < rank[old]:
        return Direction.TIGHTENS
    if rank[new] > rank[old]:
        return Direction.LOOSENS
    return Direction.NEUTRAL


def _canon(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, Enum):
        return str(v.value)
    if isinstance(v, BaseModel):
        return _canon(v.model_dump())
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{k}:{_canon(v[k])}" for k in sorted(v)) + "}"
    if isinstance(v, (list, tuple, set, frozenset)):
        items = [_canon(x) for x in v]
        if isinstance(v, (set, frozenset)):
            items = sorted(items, key=str)
        return "[" + ",".join(str(x) for x in items) + "]"
    if isinstance(v, float):
        return str(Decimal(str(v)))
    return str(v)


def _is_exemption_rule(r: Rule) -> bool:
    return bool(r.exempts)


#: Rules that still bind against a kill-switch liquidation order, because KILL-002 does not
#: exempt them, and whose predicate is tunable. A "tightening" of any of these slows or blocks
#: the exit: RATE-001 at 1 order/min liquidates a 20-name book in 20 minutes.
#: The schema has no field that says whether a rule applies to exits (SPEC-P1.3.1 F-5), so
#: this set is explicit and pinned by `t_liquidation_path_set_is_pinned`. It is a
#: classification, not a risk number: it changes no verdict, only who must approve.
LIQUIDATION_PATH_RULES: Final[frozenset[str]] = frozenset(
    {"RATE-001", "RATE-002", "DATA-001", "LIQ-001"}
)


def _blocks_exit(r: Rule) -> bool:
    """A rule that can stand between the book and a risk-reducing exit."""
    return r.measurement.timing == "pre_exit" or r.id in LIQUIDATION_PATH_RULES


def _threshold_and_comparison(old: Rule, new: Rule) -> tuple[Direction, str]:
    """Joint classification: comparison and threshold are one predicate, not two fields.

    Classifying them separately is how `eq 2.5 -> lte 2.5` (STOP-001) slips through: the
    threshold did not move, and "comparison changed" alone has no direction.
    """
    oc, nc = old.comparison, new.comparison
    ob, nb = _bound(old), _bound(new)
    if oc in _ORDINAL and nc in _ORDINAL and ob is not None and nb is not None:
        d = _set_direction(_interval(oc, ob), _interval(nc, nb))
        return d, (f"pass set {oc.value} {_canon(ob)} -> {nc.value} {_canon(nb)}: "
                   f"{'incomparable' if d is Direction.UNDECIDABLE else d.value.lower()}")
    if oc == nc and ob == nb:
        return Direction.NEUTRAL, "predicate unchanged"
    return Direction.UNDECIDABLE, (
        f"predicate {oc.value} {_canon(ob)} -> {nc.value} {_canon(nb)} has no decidable "
        f"pass-set relation (non-ordinal comparison, or threshold source changed)")


def _value_set(vs: Sequence[Any] | None) -> frozenset:
    return frozenset(_canon(v) for v in (vs or ()))


def _rule_field_changes(old: Rule, new: Rule) -> list[PolicyChange]:
    rid = old.id
    out: list[PolicyChange] = []

    def add(field: str, ov: Any, nv: Any, d: Direction, why: str) -> None:
        out.append(PolicyChange(kind=ChangeKind.RULE_FIELD, path=f"rules.{rid}.{field}",
                                rule_id=rid, field=field, old=_canon(ov), new=_canon(nv),
                                direction=d, reason=why))

    def differs(f: str) -> bool:
        return _canon(getattr(old, f)) != _canon(getattr(new, f))

    # --- the predicate: comparison + threshold source, jointly -----------------------
    pred_fields = ("comparison", "threshold", "threshold_ref", "threshold_input")
    if any(differs(f) for f in pred_fields):
        d, why = _threshold_and_comparison(old, new)
        for f in pred_fields:
            if differs(f):
                add(f, getattr(old, f), getattr(new, f), d, why)

    for f in RULE_FIELDS:
        if f in pred_fields or f == "id" or not differs(f):
            continue
        ov, nv = getattr(old, f), getattr(new, f)
        if f in _TEXT_FIELDS:
            add(f, ov, nv, Direction.NEUTRAL, "free text; changes no verdict")
        elif f == "authority":
            add(f, ov, nv, Direction.UNDECIDABLE,
                "authority decides which approval regime governs the rule; re-attributing a "
                "[CONST] rule is the first step of de-constitutionalising it")
        elif f == "action":
            add(f, ov, nv, _rank_direction(_ACTION_RANK, ov, nv),
                f"action lattice KILL > DENY > MODIFY > ALLOW: {ov.value} -> {nv.value}")
        elif f == "on_missing_input":
            add(f, ov, nv, _rank_direction(_ACTION_RANK, ov, nv),
                f"fail-closed response {ov.value} -> {nv.value}")
        elif f == "mode":
            d = Direction.LOOSENS if nv is RuleMode.MONITOR else Direction.TIGHTENS
            add(f, ov, nv, d, f"{ov.value} -> {nv.value}: a monitor rule records but never binds")
        elif f == "severity":
            add(f, ov, nv, _rank_direction(_SEVERITY_RANK, ov, nv),
                "severity routes alerts; a lower severity is a slower human response")
        elif f == "kill_scope":
            if ov is None or nv is None:
                add(f, ov, nv, Direction.UNDECIDABLE, "kill_scope appeared or disappeared")
            else:
                add(f, ov, nv, _rank_direction(_KILL_SCOPE_RANK, ov, nv),
                    f"kill scope {ov.value} -> {nv.value}")
        elif f == "scope":
            if ov in _SCOPE_COVERAGE and nv in _SCOPE_COVERAGE:
                d = _set_direction(_SCOPE_COVERAGE[ov], _SCOPE_COVERAGE[nv])
                # Coverage is the inverse of a pass set: MORE coverage = acts more often.
                d = {Direction.TIGHTENS: Direction.LOOSENS,
                     Direction.LOOSENS: Direction.TIGHTENS}.get(d, d)
                add(f, ov, nv, d, f"evaluation coverage {ov.value} -> {nv.value}")
            else:
                add(f, ov, nv, Direction.UNDECIDABLE,
                    f"scope {ov.value} -> {nv.value} measures a different population")
        elif f == "allowed_values":
            if new.comparison is Comparison.IN and old.comparison is Comparison.IN:
                add(f, ov, nv, _set_direction(_value_set(ov), _value_set(nv)),
                    "`in`: the allowed set IS the pass set")
            else:
                add(f, ov, nv, Direction.UNDECIDABLE,
                    "value set under a non-`in` comparison has no set semantics")
        elif f == "disallowed_values":
            if new.comparison is Comparison.NOT_IN and old.comparison is Comparison.NOT_IN:
                # A bigger deny-set is a smaller pass set.
                d = _set_direction(_value_set(ov), _value_set(nv))
                d = {Direction.TIGHTENS: Direction.LOOSENS,
                     Direction.LOOSENS: Direction.TIGHTENS}.get(d, d)
                add(f, ov, nv, d, "`not_in`: the disallowed set is the complement of the pass set")
            else:
                add(f, ov, nv, Direction.UNDECIDABLE,
                    "value set under a non-`not_in` comparison has no set semantics")
        elif f == "allowed_values_emergency":
            d = _set_direction(_value_set(ov), _value_set(nv))
            if d is Direction.TIGHTENS:
                d = Direction.UNDECIDABLE
                why = ("narrows what an EMERGENCY EXIT may use: a smaller pass set that blocks "
                       "a risk-reducing action is not provably safer")
            else:
                why = "emergency order-type set"
            add(f, ov, nv, d, why)
        elif f == "allowed_values_ref":
            add(f, ov, nv, Direction.UNDECIDABLE, "value-set reference repointed")
        elif f == "exempts":
            # More exemptions = fewer rules bind = loosens. Fewer exemptions re-exposes the
            # kill-switch liquidation path: not provably safer, so never TIGHTENS.
            ex_old, ex_new = _value_set(ov), _value_set(nv)
            if ex_new >= ex_old:
                add(f, ov, nv, Direction.LOOSENS, "exemption set grew: fewer rules bind")
            else:
                add(f, ov, nv, Direction.UNDECIDABLE,
                    "exemption set shrank: kill-switch liquidation can now be blocked by "
                    + ", ".join(sorted(ex_old - ex_new)))
        elif f == "inputs":
            io, inew = frozenset(ov), frozenset(nv)
            if inew >= io:
                add(f, ov, nv, Direction.TIGHTENS,
                    "inputs added: each is one more fail-closed path ([CONST-6])")
            elif inew <= io:
                add(f, ov, nv, Direction.LOOSENS,
                    "inputs removed: the fail-closed check can no longer see "
                    + ", ".join(sorted(io - inew)) + " go missing")
            else:
                add(f, ov, nv, Direction.UNDECIDABLE, "inputs swapped")
        elif f == "measurement":
            for sub in ("basis", "window", "timing"):
                so, sn = getattr(ov, sub), getattr(nv, sub)
                if so != sn:
                    add(f"measurement.{sub}", so, sn, Direction.UNDECIDABLE,
                        f"measurement {sub} changed: a different quantity, or the same "
                        f"quantity over a different span, is not monotone in the threshold")
        elif f == "modify":
            _modify_change(old, new, add)
        else:  # pragma: no cover - guarded by t_every_rule_field_is_classified
            add(f, ov, nv, Direction.UNDECIDABLE, "unclassified field")

    # --- overlays: exit-path and exemption rules never get the tightening path -------
    if _blocks_exit(old) or _blocks_exit(new) or _is_exemption_rule(old) \
            or _is_exemption_rule(new):
        what = ("grants the kill-switch liquidation exemption"
                if (_is_exemption_rule(old) or _is_exemption_rule(new))
                else "can bind against a risk-reducing exit (pre_exit, or "
                     "LIQUIDATION_PATH_RULES)")
        out = [
            c.model_copy(update={
                "direction": Direction.UNDECIDABLE,
                "reason": f"{c.reason}; reclassified UNDECIDABLE because {rid} {what}: "
                          f"acting more often here can trap a position",
            }) if c.direction is Direction.TIGHTENS else c
            for c in out
        ]
        if _is_exemption_rule(old) or _is_exemption_rule(new):
            out = [
                c.model_copy(update={
                    "direction": Direction.UNDECIDABLE,
                    "reason": f"{c.reason}; mode does not gate exemptions in PolicyGate, so "
                              f"this change has no defined effect (SPEC-P1.3.1 F-3)",
                }) if c.field == "mode" else c
                for c in out
            ]
    return out


def _modify_change(old: Rule, new: Rule, add: Any) -> None:
    om, nm = old.modify, new.modify
    if om is None or nm is None:
        add("modify", om, nm, Direction.UNDECIDABLE, "modify block appeared or disappeared")
        return
    if om.target != nm.target:
        add("modify.target", om.target, nm.target, Direction.UNDECIDABLE,
            "MODIFY now changes a different quantity")
    if _canon(om.to) != _canon(nm.to):
        try:
            o, n = Decimal(str(om.to)), Decimal(str(nm.to))
        except (InvalidOperation, ValueError):
            add("modify.to", om.to, nm.to, Direction.UNDECIDABLE,
                "symbolic MODIFY target changed; its arithmetic lives in P2.9")
            return
        if om.target == nm.target and om.target.endswith("_pct"):
            d = (Direction.LOOSENS if n > o else
                 Direction.TIGHTENS if n < o else Direction.NEUTRAL)
            add("modify.to", om.to, nm.to, d,
                f"{om.target} reset to a {'larger' if n > o else 'smaller'} weight")
        else:
            add("modify.to", om.to, nm.to, Direction.UNDECIDABLE,
                "numeric MODIFY target with no known direction")


def _rule_added(r: Rule) -> PolicyChange:
    if r.exempts:
        d, why = Direction.LOOSENS, f"new rule grants exemptions from {', '.join(r.exempts)}"
    elif r.action is RuleAction.ALLOW:
        d, why = Direction.NEUTRAL, "new ALLOW rule with no exemptions can never bind"
    elif r.mode is RuleMode.MONITOR:
        d, why = Direction.NEUTRAL, "new monitor rule records but does not bind"
    elif _blocks_exit(r):
        d, why = Direction.UNDECIDABLE, "new rule gates a risk-reducing exit (timing pre_exit)"
    else:
        d, why = Direction.TIGHTENS, f"new enforced {r.action.value} rule"
    return PolicyChange(kind=ChangeKind.RULE_ADDED, path=f"rules.{r.id}", rule_id=r.id,
                        field=None, old=None, new=_canon(r), direction=d, reason=why)


def _rule_removed(r: Rule) -> PolicyChange:
    if r.exempts:
        d, why = Direction.UNDECIDABLE, (
            "removing an exemption rule re-subjects kill-switch liquidation to "
            + ", ".join(r.exempts))
    else:
        d, why = Direction.LOOSENS, (
            "rule removed: whatever it bounded is now unbounded. Its id is retired, never "
            "reused (SPEC-P1.3 §2 row 1)")
    return PolicyChange(kind=ChangeKind.RULE_REMOVED, path=f"rules.{r.id}", rule_id=r.id,
                        field=None, old=_canon(r), new=None, direction=d, reason=why)


# =============================================================================
# 4. NON-RULE CONFIGURATION  (SPEC-P1.3.1 §3.3)
# =============================================================================


class KeyDirection(str, Enum):
    NEUTRAL = "NEUTRAL"
    HIGHER_LOOSENS = "HIGHER_LOOSENS"
    LOWER_LOOSENS = "LOWER_LOOSENS"
    TRUE_LOOSENS = "TRUE_LOOSENS"
    FALSE_LOOSENS = "FALSE_LOOSENS"
    SET_GROW_LOOSENS = "SET_GROW_LOOSENS"
    SET_SHRINK_LOOSENS = "SET_SHRINK_LOOSENS"
    UNDECIDABLE = "UNDECIDABLE"


#: Ordered; FIRST match wins. Segment-wise glob: `*` matches within one dotted segment,
#: `**` matches the rest of the path. The last entry makes every unlisted key UNDECIDABLE,
#: so a new key is two-person until someone classifies it in a reviewed change.
CONFIG_KEY_DIRECTIONS: Final[tuple[tuple[str, KeyDirection], ...]] = (
    ("metadata.**", KeyDirection.NEUTRAL),
    ("policy_version", KeyDirection.NEUTRAL),
    ("governance.min_approvals_to_loosen", KeyDirection.LOWER_LOOSENS),
    ("governance.risk_deny_override_permitted", KeyDirection.TRUE_LOOSENS),
    ("hitl.risk_deny_override_permitted", KeyDirection.TRUE_LOOSENS),
    ("kill_switch.requires_human_to_re_enable", KeyDirection.FALSE_LOOSENS),
    ("kill_switch.auto_re_enable_permitted", KeyDirection.TRUE_LOOSENS),
    ("fx.system_may_convert", KeyDirection.TRUE_LOOSENS),
    ("risk_evaluation.*", KeyDirection.FALSE_LOOSENS),
    ("llm.may_receive_portfolio_state", KeyDirection.TRUE_LOOSENS),
    ("llm.replay_requires_approval", KeyDirection.FALSE_LOOSENS),
    ("llm.replay_offpeak_only", KeyDirection.FALSE_LOOSENS),
    ("llm.gate_width", KeyDirection.HIGHER_LOOSENS),
    ("llm.max_concurrency", KeyDirection.HIGHER_LOOSENS),
    ("llm.spend_alarm_*", KeyDirection.HIGHER_LOOSENS),
    ("account.enforce_settled_cash", KeyDirection.FALSE_LOOSENS),
    ("account.enforce_day_trades", KeyDirection.FALSE_LOOSENS),
    ("account.pdt_equity_floor_usd", KeyDirection.LOWER_LOOSENS),
    ("account.pdt_max_day_trades_5d", KeyDirection.HIGHER_LOOSENS),
    ("portfolio.max_position_pct", KeyDirection.HIGHER_LOOSENS),
    ("portfolio.forced_trim_pct", KeyDirection.HIGHER_LOOSENS),
    ("portfolio.min_cash_pct", KeyDirection.LOWER_LOOSENS),
    ("turnover.*", KeyDirection.HIGHER_LOOSENS),
    ("holding.time_stop_sessions", KeyDirection.HIGHER_LOOSENS),
    ("holding.hard_max_sessions", KeyDirection.HIGHER_LOOSENS),
    ("holding.time_stop_min_return_pct", KeyDirection.LOWER_LOOSENS),
    ("universe.*.min_*", KeyDirection.LOWER_LOOSENS),
    ("universe.*.max_instruments", KeyDirection.HIGHER_LOOSENS),
    ("universe.*.enter_rank", KeyDirection.HIGHER_LOOSENS),
    ("universe.*.exit_rank", KeyDirection.HIGHER_LOOSENS),
    ("decision.min_edge_multiple_of_cost", KeyDirection.LOWER_LOOSENS),
    ("cost.assumed_round_trip_bps.*", KeyDirection.LOWER_LOOSENS),
    ("cost.verified_monthly_usd.*", KeyDirection.NEUTRAL),
    ("cost.vm_monthly_usd", KeyDirection.NEUTRAL),
    ("cost.backup_monthly_usd", KeyDirection.NEUTRAL),
    ("cost.total_operating_is_complete", KeyDirection.NEUTRAL),
    ("instrument_allowlist.tradeable", KeyDirection.SET_GROW_LOOSENS),
    ("instrument_allowlist.permanently_banned", KeyDirection.SET_SHRINK_LOOSENS),
    ("latency.exit.stale_bar_critical_seconds", KeyDirection.HIGHER_LOOSENS),
    ("dr.rpo_state_seconds", KeyDirection.HIGHER_LOOSENS),
    ("dr.rto_*", KeyDirection.HIGHER_LOOSENS),
    ("storage.records_retention_years", KeyDirection.LOWER_LOOSENS),
    ("storage.disk_*_pct", KeyDirection.HIGHER_LOOSENS),
    ("promotion.min_*", KeyDirection.LOWER_LOOSENS),
    ("promotion.shadow_min_sessions", KeyDirection.LOWER_LOOSENS),
    ("promotion.dsr_threshold", KeyDirection.LOWER_LOOSENS),
    ("**", KeyDirection.UNDECIDABLE),
)

_SET_KINDS: Final = frozenset({KeyDirection.SET_GROW_LOOSENS, KeyDirection.SET_SHRINK_LOOSENS})


def _match(pattern: str, path: str) -> bool:
    ps, xs = pattern.split("."), path.split(".")
    for i, p in enumerate(ps):
        if p == "**":
            return True
        if i >= len(xs) or not fnmatchcase(xs[i], p):
            return False
    return len(ps) == len(xs)


def key_direction(path: str) -> KeyDirection:
    for pat, d in CONFIG_KEY_DIRECTIONS:
        if _match(pat, path):
            return d
    return KeyDirection.UNDECIDABLE  # unreachable: the table ends in "**"


def _leaves(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten mappings and lists of mappings to dotted paths. A list of scalars is a leaf
    (it is a value, and set-valued keys compare it as a set)."""
    out: dict[str, Any] = {}
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            out.update(_leaves(v, f"{prefix}{k}."))
    elif isinstance(obj, list) and any(isinstance(x, (Mapping, list)) for x in obj):
        for i, v in enumerate(obj):
            out.update(_leaves(v, f"{prefix}{i}."))
    else:
        out[prefix.rstrip(".")] = obj
    return out


def _num(v: Any) -> Decimal | None:
    if isinstance(v, bool) or v is None:
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return None


def _config_value_direction(path: str, ov: Any, nv: Any) -> tuple[Direction, str]:
    kd = key_direction(path)
    if kd is KeyDirection.NEUTRAL:
        return Direction.NEUTRAL, "informational key"
    if kd is KeyDirection.UNDECIDABLE:
        return Direction.UNDECIDABLE, "no declared direction for this key (CONFIG_KEY_DIRECTIONS)"
    if kd in _SET_KINDS:
        if not isinstance(ov, list) or not isinstance(nv, list):
            return Direction.UNDECIDABLE, "set-valued key is not a list in both versions"
        so, sn = frozenset(map(_canon, ov)), frozenset(map(_canon, nv))
        if so == sn:
            return Direction.NEUTRAL, "same set, different order"
        grew, shrank = sn > so, sn < so
        if not (grew or shrank):
            return Direction.UNDECIDABLE, "set changed by both adding and removing"
        loosens = grew if kd is KeyDirection.SET_GROW_LOOSENS else shrank
        return (Direction.LOOSENS if loosens else Direction.TIGHTENS,
                f"set {'grew' if grew else 'shrank'} under {kd.value}")
    if kd in (KeyDirection.TRUE_LOOSENS, KeyDirection.FALSE_LOOSENS):
        if not isinstance(ov, bool) or not isinstance(nv, bool):
            return Direction.UNDECIDABLE, "boolean key is not a bool in both versions"
        loosens = nv if kd is KeyDirection.TRUE_LOOSENS else not nv
        return (Direction.LOOSENS if loosens else Direction.TIGHTENS,
                f"{ov} -> {nv} under {kd.value}")
    o, n = _num(ov), _num(nv)
    if o is None or n is None:
        return Direction.UNDECIDABLE, "numeric key is not numeric in both versions"
    if o == n:
        return Direction.NEUTRAL, "same number, different representation"
    higher = n > o
    loosens = higher if kd is KeyDirection.HIGHER_LOOSENS else not higher
    return (Direction.LOOSENS if loosens else Direction.TIGHTENS,
            f"{o} -> {n} under {kd.value}")


def _config_changes(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[PolicyChange]:
    lo = _leaves({k: v for k, v in old.items() if k != "rules"})
    ln = _leaves({k: v for k, v in new.items() if k != "rules"})
    out: list[PolicyChange] = []
    for path in sorted(set(lo) | set(ln)):
        if path in lo and path in ln:
            if _canon(lo[path]) == _canon(ln[path]):
                continue
            d, why = _config_value_direction(path, lo[path], ln[path])
            kind = ChangeKind.CONFIG_VALUE
        elif path in lo:
            kind = ChangeKind.CONFIG_REMOVED
            if key_direction(path) is KeyDirection.NEUTRAL:
                d, why = Direction.NEUTRAL, "informational key removed"
            else:
                d, why = Direction.LOOSENS, ("key removed: a rule or component that read it "
                                             "now reads nothing")
        else:
            kind = ChangeKind.CONFIG_ADDED
            if key_direction(path) is KeyDirection.NEUTRAL:
                d, why = Direction.NEUTRAL, "informational key added"
            else:
                d, why = Direction.UNDECIDABLE, "new key: no prior value to compare against"
        out.append(PolicyChange(kind=kind, path=path, rule_id=None, field=None,
                                old=_canon(lo.get(path)) if path in lo else None,
                                new=_canon(ln.get(path)) if path in ln else None,
                                direction=d, reason=why))
    return out


# =============================================================================
# 5. THE DIFF AND THE AUTHORISATION CHECK
# =============================================================================


def _validate(raw: Mapping[str, Any], which: str) -> PolicyDocument:
    try:
        return PolicyDocument.model_validate(raw)
    except Exception as exc:  # noqa: BLE001 - an unvalidatable version has no change list
        raise PolicyDiffError(
            f"{which} policy does not validate, so no change list can be derived and no "
            f"change is authorised: {exc}") from exc


def diff_policies(old_raw: Mapping[str, Any], new_raw: Mapping[str, Any]) -> PolicyDiff:
    """Derive and classify every difference between two EFFECTIVE (merged) policy documents.

    Inputs are the merged mappings `PolicyLoader` hashes and signs, not single layer files: a
    loosening that lives only in `policy.market.IN.yaml` is a loosening of the IN effective
    config, and is only visible after merging (SPEC-P1.3.1 [DEFAULT-D2]).
    """
    old_doc, new_doc = _validate(old_raw, "old"), _validate(new_raw, "new")
    old_rules = {r.id: r for r in old_doc.rules}
    new_rules = {r.id: r for r in new_doc.rules}

    changes: list[PolicyChange] = []
    for rid in sorted(set(old_rules) | set(new_rules)):
        if rid not in new_rules:
            changes.append(_rule_removed(old_rules[rid]))
        elif rid not in old_rules:
            changes.append(_rule_added(new_rules[rid]))
        else:
            changes.extend(_rule_field_changes(old_rules[rid], new_rules[rid]))
    changes.extend(_config_changes(old_raw, new_raw))
    changes.sort(key=lambda c: (c.path, c.field or ""))
    return PolicyDiff(old_version=old_doc.policy_version, new_version=new_doc.policy_version,
                      changes=tuple(changes))


def assert_policy_change_authorised(
    old_raw: Mapping[str, Any],
    new_raw: Mapping[str, Any],
    approver_ids: Sequence[str],
) -> PolicyDiff:
    """SPEC-P1.3 §5.3 as amended by SPEC-P1.3.1 §5: the two-person rule over the DERIVED diff.

    The approval threshold is read from the OLD (currently active) version's governance. A
    version that lowered its own approval threshold would otherwise approve itself.
    Returns the diff so the caller writes exactly what was approved to the audit trail.
    """
    d = diff_policies(old_raw, new_raw)
    governance: Governance = _validate(old_raw, "old").governance
    distinct = {a.strip().lower() for a in approver_ids if a and a.strip()}
    gated = [c for c in d.changes if c.requires_two_person]
    if gated and len(distinct) < governance.min_approvals_to_loosen:
        raise PolicyGovernanceError(
            f"{len(gated)} change(s) loosen or cannot be proven to tighten "
            f"({', '.join(sorted({c.path for c in gated}))}) with {len(distinct)} distinct "
            f"approver(s); {governance.min_approvals_to_loosen} required by the ACTIVE "
            f"version's governance. Tightening needs none.")
    return d


__all__ = [
    "PolicyDiffError", "Direction", "ChangeKind", "PolicyChange", "PolicyDiff",
    "KeyDirection", "CONFIG_KEY_DIRECTIONS", "RULE_FIELDS", "LIQUIDATION_PATH_RULES",
    "key_direction", "diff_policies", "assert_policy_change_authorised",
]
