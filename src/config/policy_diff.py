"""SPEC-P1.3.1-POLICY-DIFF v0.3.4 — derive and classify every policy change; the two-person rule.

Closes X5R-G2. The change list and the set of (market, environment) combinations it covers are
DERIVED from the policy files, never supplied by the person asking for approval. Every change is
classified by Owner Ruling 12 as

    LOOSENS | TIGHTENS | NEUTRAL | UNDECIDABLE

UNDECIDABLE is a real outcome, not an error, and for approval it counts as LOOSENS ([CONST-6]).
Every record carries `basis`, the id of the row of SPEC-P1.3.1 §3 that produced it.

Where a change to one rule alters what ANOTHER rule does (an exemption, a displaced GLOBAL kill), that
effect is a separate, derived record against the other rule. A ruled record is never overwritten.

An approval is valid only for the version it was diffed against, only for 24 hours, and only once.
`assert_authorisation_current` proves all three on the writer's own transaction. Nothing here runs
SQL: the store is reached only through `IN_FORCE_STORE`, which is `None` until a frozen spec defines
it, so today nothing can be applied by this path. That is deliberate (SPEC-P1.3.1 B6).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Final, Protocol

from audit.events import canonical_json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_public_key,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .loader import (
    Comparison,
    EffectiveConfig,
    PolicyDocument,
    PolicyError,
    PolicyGovernanceError,
    PolicyLoader,
    Rule,
    RuleAction,
    RuleMode,
    content_hash,
    verify_signature,
)

# =============================================================================
# 1. TYPES  (§4)
# =============================================================================

_RULE_ID = r"^[A-Z]{2,7}-\d{3}$"
_VERSION = r"^\d+\.\d+\.\d+$"
_HASH = r"^[0-9a-f]{64}$"
_BASIS = r"^C-\d{2}$"
_IDENTITY = r"^[a-z0-9][a-z0-9._-]{0,63}$"
_UUID7 = r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
_UTC_SECOND = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
_UTC_SECOND_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class PolicyDiffError(PolicyError):
    """A version could not be validated or classified, so no change list exists. Nothing is
    authorised."""


class StaleAuthorisationError(PolicyGovernanceError):
    """The authorisation no longer matches what is stored, proposed or spent. Nothing is written,
    and the candidate must be re-diffed and re-approved."""


class InForceAnchorError(StaleAuthorisationError):
    """No authoritative in-force record is available (SPEC-P1.3.1 B6)."""


class ApprovalExpiredError(StaleAuthorisationError):
    """`requested_at` is older than `APPROVAL_TTL_HOURS`, or in the future.

    The writer catches this BEFORE `StaleAuthorisationError`, because it is a subclass. Only
    `reason == "EXPIRED"` writes an `APPROVAL_EXPIRED` event; `"FUTURE"` writes nothing.
    """

    def __init__(self, message: str, *, reason: str, request_id: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.request_id = request_id


class Direction(str, Enum):
    LOOSENS = "LOOSENS"
    TIGHTENS = "TIGHTENS"
    NEUTRAL = "NEUTRAL"
    UNDECIDABLE = "UNDECIDABLE"


class ChangeKind(str, Enum):
    RULE_ADDED = "RULE_ADDED"
    RULE_REMOVED = "RULE_REMOVED"
    RULE_FIELD = "RULE_FIELD"
    RULE_EXEMPTED = "RULE_EXEMPTED"              # derived, C-36 [DEFAULT-B3]
    RULE_KILL_DISPLACED = "RULE_KILL_DISPLACED"  # derived, C-40 [DEFAULT-B5]
    CONFIG_ADDED = "CONFIG_ADDED"
    CONFIG_REMOVED = "CONFIG_REMOVED"
    CONFIG_VALUE = "CONFIG_VALUE"
    LAYER_ADDED = "LAYER_ADDED"                  # C-41
    LAYER_REMOVED = "LAYER_REMOVED"              # C-41


class KeyDirection(str, Enum):
    NEUTRAL = "NEUTRAL"
    HIGHER_LOOSENS = "HIGHER_LOOSENS"
    LOWER_LOOSENS = "LOWER_LOOSENS"
    TRUE_LOOSENS = "TRUE_LOOSENS"
    FALSE_LOOSENS = "FALSE_LOOSENS"
    SET_GROW_LOOSENS = "SET_GROW_LOOSENS"
    SET_SHRINK_LOOSENS = "SET_SHRINK_LOOSENS"
    UNDECIDABLE = "UNDECIDABLE"


_RULE_KINDS = frozenset({ChangeKind.RULE_ADDED, ChangeKind.RULE_REMOVED, ChangeKind.RULE_FIELD,
                         ChangeKind.RULE_EXEMPTED, ChangeKind.RULE_KILL_DISPLACED})
_DERIVED_KINDS = frozenset({ChangeKind.RULE_EXEMPTED, ChangeKind.RULE_KILL_DISPLACED})
_CONFIG_KINDS = frozenset({ChangeKind.CONFIG_ADDED, ChangeKind.CONFIG_REMOVED,
                           ChangeKind.CONFIG_VALUE})


class PolicyChange(BaseModel):
    """One classified difference between two versions. Every value is a string or an enum, so a
    record canonicalises under P1.4's jcs-nonum-1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ChangeKind
    path: Annotated[str, Field(min_length=1, max_length=300)]
    rule_id: Annotated[str, Field(pattern=_RULE_ID)] | None
    field: Annotated[str, Field(min_length=1, max_length=80)] | None
    related_rule_id: Annotated[str, Field(pattern=_RULE_ID)] | None = None
    old: str | None
    new: str | None
    direction: Direction
    basis: Annotated[str, Field(pattern=_BASIS)]
    reason: Annotated[str, Field(min_length=1, max_length=600)]

    @model_validator(mode="after")
    def _coherent(self) -> PolicyChange:
        if (self.kind in _RULE_KINDS) != (self.rule_id is not None):
            raise ValueError("rule_id is set iff the change is about a rule")
        if (self.kind is ChangeKind.RULE_FIELD) != (self.field is not None):
            raise ValueError("field is set iff kind is RULE_FIELD")
        if (self.kind in _DERIVED_KINDS) != (self.related_rule_id is not None):
            raise ValueError("related_rule_id is set iff the record is derived")
        added = (ChangeKind.RULE_ADDED, ChangeKind.CONFIG_ADDED, ChangeKind.LAYER_ADDED)
        removed = (ChangeKind.RULE_REMOVED, ChangeKind.CONFIG_REMOVED, ChangeKind.LAYER_REMOVED)
        if self.kind in added and self.old is not None:
            raise ValueError("an addition has no old value")
        if self.kind in removed and self.new is not None:
            raise ValueError("a removal has no new value")
        if self.basis not in CLASSIFICATION_BASES:
            raise ValueError(f"unknown classification basis {self.basis}")
        return self

    @property
    def requires_two_person(self) -> bool:
        return self.direction in (Direction.LOOSENS, Direction.UNDECIDABLE)


def _change_key(c: PolicyChange) -> tuple[str, str, str]:
    return (c.path, c.field or "", c.basis)


class PolicyDiff(BaseModel):
    """The complete change list for ONE (market, environment) combination."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    market: Annotated[str, Field(pattern=r"^(US|IN)$")] | None
    environment: Annotated[str, Field(pattern=r"^[a-z0-9_-]{1,32}$")] | None
    old_version: Annotated[str, Field(pattern=_VERSION)]
    new_version: Annotated[str, Field(pattern=_VERSION)]
    old_content_hash: Annotated[str, Field(pattern=_HASH)]
    new_content_hash: Annotated[str, Field(pattern=_HASH)]
    changes: tuple[PolicyChange, ...]

    @model_validator(mode="after")
    def _ordered(self) -> PolicyDiff:
        keys = [_change_key(c) for c in self.changes]
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            raise ValueError("changes must be unique and sorted by (path, field, basis)")
        return self

    @property
    def requires_two_person(self) -> bool:
        return any(c.requires_two_person for c in self.changes)


class ApprovalSignature(BaseModel):
    """One approver's Ed25519 signature over authorisation_digest(diffs), hex-encoded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    identity: Annotated[str, Field(pattern=_IDENTITY)]
    signature_hex: Annotated[str, Field(pattern=r"^[0-9a-f]{128}$")]


class PolicyAuthorisation(BaseModel):
    """What was approved: written to the audit trail before the new version takes effect.

    Every field is a string or a model of strings, so it canonicalises under jcs-nonum-1.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    diffs: Annotated[tuple[PolicyDiff, ...], Field(min_length=1)]
    request_id: Annotated[str, Field(pattern=_UUID7)]
    requested_at: Annotated[str, Field(pattern=_UTC_SECOND)]
    digest: Annotated[str, Field(pattern=_HASH)]
    approvals: tuple[ApprovalSignature, ...]
    required_approvals: Annotated[str, Field(pattern=r"^[0-5]$")]
    gated_paths: tuple[str, ...]

    @model_validator(mode="after")
    def _ordered(self) -> PolicyAuthorisation:
        combos = [(d.market or "", d.environment or "") for d in self.diffs]
        if combos != sorted(combos) or len(set(combos)) != len(combos):
            raise ValueError("diffs must be unique and sorted by (market, environment)")
        ids = [a.identity for a in self.approvals]
        if ids != sorted(set(ids)):
            raise ValueError("approvals must be distinct and sorted by identity")
        if list(self.gated_paths) != sorted(set(self.gated_paths)):
            raise ValueError("gated_paths must be distinct and sorted")
        try:
            parsed = datetime.strptime(self.requested_at, _UTC_SECOND_FORMAT)
        except ValueError as exc:
            raise ValueError("requested_at is not a real UTC time") from exc
        if parsed.strftime(_UTC_SECOND_FORMAT) != self.requested_at:
            raise ValueError("requested_at does not round-trip")
        gated = sorted({c.path for d in self.diffs for c in d.changes if c.requires_two_person})
        if list(self.gated_paths) != gated:
            raise ValueError("gated_paths must be the paths of the two-person records")
        if (self.required_approvals == "0") != (not gated):
            raise ValueError("required_approvals is 0 exactly when nothing is gated")
        if len(self.approvals) < int(self.required_approvals):
            raise ValueError("fewer approvals than required")
        return self


#: The two markets (SPEC-P1.1 Market). A market layer file for any other name fails closed.
MARKETS: Final[tuple[str, ...]] = ("US", "IN")
#: Domain separation for approval signatures (X2D-5): prefixed to the digest preimage, so an
#: approval can never be read as a policy signature (SPEC-P1.3 §5.2) or anything else.
APPROVAL_DIGEST_TAG: Final[bytes] = b"SPEC-P1.3.1 approval v1\n"
#: ADR-09 row 2: an approval request expires 24 h after requested_at; on expiry it is denied.
APPROVAL_TTL_HOURS: Final[int] = 24
#: The approval ladder, most restrictive first (the Owner's answer to B2).
ACTION_LADDER: Final[tuple[str, ...]] = ("KILL", "HALT_ENTRIES", "DENY", "MODIFY", "ALLOW")
#: The rules Ruling 14 moves to HALT_ENTRIES. Any other rule moved there is UNDECIDABLE (C-42).
HALT_ENTRIES_RULES: Final[frozenset[str]] = frozenset({"LOSS-001", "LOSS-002"})
#: (narrower, wider). Every other distinct pair is UNDECIDABLE ([DEFAULT-B4]).
SCOPE_NARROWER_THAN: Final[frozenset[tuple[str, str]]] = frozenset(
    {("pool", "pool_and_consolidated"), ("consolidated", "pool_and_consolidated")}
)
#: C-01 .. C-42, each a row of §3.5 to §3.8.
CLASSIFICATION_BASES: Final[frozenset[str]] = frozenset(f"C-{n:02d}" for n in range(1, 43))


class InForceStore(Protocol):
    """The B6 store as this module reads it. Implemented by that store's module and by tests."""

    def in_force_hashes(self, conn: Any) -> Mapping[tuple[str | None, str | None], str]:
        """The current config_hash of every combination with a current row, read on conn.

        Closed rows are never returned, so presence in the mapping means current.
        """
        ...

    def database_time(self, conn: Any) -> datetime:
        """clock_timestamp() on conn, read after the policy-change lock is held, timezone-aware UTC."""
        ...

    def request_used(self, conn: Any, request_id: str) -> bool:
        """True if any in-force row already carries this request_id."""
        ...


#: None until a frozen spec defines the B6 store. Assigned only by that store's module and tests.
IN_FORCE_STORE: InForceStore | None = None
#: None until P6.2 delivers Vault. Takes a vault:// reference, returns an Ed25519 public key in PEM.
VAULT_RESOLVER: Callable[[str], bytes] | None = None

#: Equals set(Rule.model_fields); t_every_rule_field_is_classified fails CI if they part.
RULE_FIELDS: Final[frozenset[str]] = frozenset({
    "action", "allowed_values", "allowed_values_emergency", "allowed_values_ref", "authority",
    "comparison", "description", "disallowed_values", "exempts", "id", "inputs", "kill_scope",
    "measurement", "mode", "modify", "notes", "on_missing_input", "scope", "severity",
    "threshold", "threshold_input", "threshold_ref",
})

def _keys(direction: KeyDirection, names: Iterable[str]) -> list[tuple[str, KeyDirection]]:
    return [(name, direction) for name in names]


#: Exact dotted keys, each with its direction (§3.7), ending in the catch-all. There is no other
#: wildcard: a key that does not exist yet gets no direction until a reviewed change lists it.
CONFIG_KEY_DIRECTIONS: Final[tuple[tuple[str, KeyDirection], ...]] = (
    *_keys(KeyDirection.NEUTRAL, (
        "policy_version", "metadata.description", "metadata.authored_by", "metadata.authored_at",
        "cost.verified_monthly_usd.paper", "cost.verified_monthly_usd.live", "cost.vm_monthly_usd",
        "cost.backup_monthly_usd", "cost.total_operating_is_complete",
    )),
    *_keys(KeyDirection.TRUE_LOOSENS, (
        "governance.risk_deny_override_permitted", "hitl.risk_deny_override_permitted",
        "kill_switch.auto_re_enable_permitted", "fx.system_may_convert",
        "llm.may_receive_portfolio_state",
    )),
    *_keys(KeyDirection.FALSE_LOOSENS, (
        "kill_switch.requires_human_to_re_enable", "risk_evaluation.evaluate_per_pool",
        "risk_evaluation.evaluate_consolidated", "risk_evaluation.stricter_binds",
        "llm.replay_requires_approval", "llm.replay_offpeak_only", "account.enforce_settled_cash",
        "account.enforce_day_trades",
    )),
    *_keys(KeyDirection.LOWER_LOOSENS, (
        "governance.min_approvals_to_loosen", "account.pdt_equity_floor_usd",
        "portfolio.min_cash_pct", "decision.min_edge_multiple_of_cost",
        "cost.assumed_round_trip_bps.US", "cost.assumed_round_trip_bps.IN",
        "holding.time_stop_min_return_pct", "holding.min_sessions",
        "storage.records_retention_years", "promotion.min_wf_windows",
        "promotion.min_closed_trades", "promotion.shadow_min_sessions", "promotion.dsr_threshold",
        *(f"universe.{m}.{k}" for m in MARKETS for k in (
            "min_addv_position_multiple", "min_sessions_history", "min_reported_quarters")),
        "universe.US.min_market_cap_usd", "universe.US.min_addv_usd_floor",
        "universe.US.min_price_usd", "universe.IN.min_market_cap_inr",
        "universe.IN.min_addv_inr_floor", "universe.IN.min_price_inr",
    )),
    *_keys(KeyDirection.HIGHER_LOOSENS, (
        "account.pdt_max_day_trades_5d", "portfolio.max_position_pct", "portfolio.forced_trim_pct",
        "turnover.max_new_entries_per_session", "turnover.max_nav_traded_pct_per_session",
        "holding.time_stop_sessions", "holding.hard_max_sessions", "llm.gate_width",
        "llm.max_concurrency", "llm.spend_alarm_warn_usd_month",
        "llm.spend_alarm_critical_usd_month", "latency.exit.stale_bar_critical_seconds",
        "dr.rpo_state_seconds", "dr.rto_safe_minutes", "dr.rto_operational_hours",
        "storage.disk_warn_pct", "storage.disk_critical_pct",
        *(f"universe.{m}.{k}" for m in MARKETS for k in (
            "max_instruments", "enter_rank", "exit_rank")),
    )),
    ("instrument_allowlist.tradeable", KeyDirection.SET_GROW_LOOSENS),
    ("instrument_allowlist.permanently_banned", KeyDirection.SET_SHRINK_LOOSENS),
    ("**", KeyDirection.UNDECIDABLE),
)

#: §3.3: why each unordered scope pair cannot be ranked.
_SCOPE_REASONS: Final[Mapping[frozenset[str], str]] = {
    frozenset(pair): reason for pair, reason in (
        (("global", "strategy"), "R1"), (("global", "market"), "R1"),
        (("global", "instrument"), "R1"), (("global", "pool"), "R1"),
        (("global", "consolidated"), "R3"), (("global", "pool_and_consolidated"), "R4"),
        (("strategy", "market"), "R2"), (("strategy", "instrument"), "R2"),
        (("strategy", "pool"), "R2"), (("strategy", "consolidated"), "R1"),
        (("strategy", "pool_and_consolidated"), "R4"), (("market", "instrument"), "R1"),
        (("market", "pool"), "R3"), (("market", "consolidated"), "R1"),
        (("market", "pool_and_consolidated"), "R4"), (("instrument", "pool"), "R1"),
        (("instrument", "consolidated"), "R1"), (("instrument", "pool_and_consolidated"), "R4"),
        (("pool", "consolidated"), "R1"),
    )
}

_MAX_VALUE: Final = Comparison.LTE, Comparison.LT
_MIN_VALUE: Final = Comparison.GTE, Comparison.GT
_NO_CONSTANT: Final = Comparison.IN, Comparison.NOT_IN, Comparison.EXISTS, Comparison.MULTIPLE_OF
_THRESHOLD_SOURCES: Final = "threshold", "threshold_ref", "threshold_input"
_SET_FIELDS: Final = ("allowed_values", "allowed_values_emergency", "disallowed_values",
                      "exempts", "inputs")
#: §3.4: changed together with `comparison`, each of these is UNDECIDABLE by C-08.
_PREDICATE_FIELDS: Final = (*_THRESHOLD_SOURCES, "allowed_values", "disallowed_values",
                            "allowed_values_ref")


# =============================================================================
# 2. VALUES
# =============================================================================


def _canon(v: Any) -> str | None:
    """A canonical string: Decimal via str, sets sorted by canonical string, None stays absent."""
    if v is None:
        return None
    if isinstance(v, Enum):
        return str(v.value)
    if isinstance(v, BaseModel):
        return _canon(v.model_dump())
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{k}:{_canon(v[k])}" for k in sorted(v, key=str)) + "}"
    if isinstance(v, (set, frozenset)):
        return "[" + ",".join(sorted(str(_canon(x)) for x in v)) + "]"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(str(_canon(x)) for x in v) + "]"
    if isinstance(v, float):
        return str(Decimal(str(v)))
    return str(v)


def _as_set(v: Iterable[Any] | None) -> frozenset[str] | None:
    """For display in a record. Compare with `_members`."""
    return None if v is None else frozenset(str(_canon(x)) for x in v)


def _identity(v: Any) -> tuple[Any, ...]:
    """An injective form of a value, for comparison.

    `_canon` is for display and is not injective: False and "False", 1 and "1", or ["a,b"] and
    ["a", "b"] each give one string. Comparing on it would hide a type change, so a real change
    would produce no record at all (X2H-2).
    """
    if v is None:
        return ("none",)
    if isinstance(v, Enum):
        return ("enum", v.value)
    if isinstance(v, BaseModel):
        return ("model", _identity(v.model_dump()))
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, (int, float, Decimal)):
        return ("number", str(Decimal(str(v))))
    if isinstance(v, str):
        return ("str", v)
    if isinstance(v, Mapping):
        return ("map", tuple(sorted(((repr(k), _identity(x)) for k, x in v.items()), key=repr)))
    if isinstance(v, (list, tuple)):
        return ("list", tuple(_identity(x) for x in v))
    if isinstance(v, (set, frozenset)):
        return ("set", tuple(sorted((_identity(x) for x in v), key=repr)))
    return ("other", type(v).__name__, repr(v))


def _members(v: Iterable[Any] | None) -> frozenset[tuple[Any, ...]] | None:
    """Set members for comparison. Absent stays distinct from empty."""
    return None if v is None else frozenset(_identity(x) for x in v)


def _kind(v: Any) -> str:
    """The scalar kind of a config value. A change of kind has no direction (C-39)."""
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float, Decimal)):
        return "number"
    return "string" if isinstance(v, str) else type(v).__name__


def _num(v: Any) -> Decimal | None:
    if isinstance(v, bool) or v is None:
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return None


def _set_move(old: Iterable[Any] | None, new: Iterable[Any] | None, *, grow: Direction,
              shrink: Direction) -> Direction:
    """Direction of a set change, compared on `_members`."""
    a, b = _members(old) or frozenset(), _members(new) or frozenset()
    if a == b:
        return Direction.NEUTRAL
    if b > a:
        return grow
    if b < a:
        return shrink
    return Direction.UNDECIDABLE


# =============================================================================
# 3. DIRECTION HELPERS  (§3.2, §3.3, §3.7)
# =============================================================================


def action_direction(old: str, new: str) -> tuple[Direction, str]:
    """Direction of an action change on the bare ladder (§3.2).

    Preconditions: none; takes strings so that `HALT_ENTRIES` is ranked before `RuleAction` has it.
    Postconditions: returns (direction, basis), the basis being "C-09" or "C-10".
    Raises: nothing. A value outside the ladder is UNDECIDABLE, never an error.
    """
    if old not in ACTION_LADDER or new not in ACTION_LADDER:
        return Direction.UNDECIDABLE, "C-10"
    i, j = ACTION_LADDER.index(old), ACTION_LADDER.index(new)
    if j < i:
        return Direction.TIGHTENS, "C-09"
    if j > i:
        return Direction.LOOSENS, "C-09"
    return Direction.NEUTRAL, "C-09"


def rule_action_direction(rule_id: str, old: str, new: str) -> tuple[Direction, str]:
    """Direction of an action change on one named rule: C-42 where it applies, else the ladder.

    Exits are always permitted under `HALT_ENTRIES` (Ruling 14), so moving any rule but those
    Ruling 14 names to it narrows entries and widens exits, and neither is provable.

    Preconditions: none; takes strings so that C-42 is tested before `RuleAction` has the member.
    Postconditions: returns (direction, basis), the basis being "C-09", "C-10" or "C-42".
    Raises: nothing.
    """
    if (new == "HALT_ENTRIES" and old not in ("HALT_ENTRIES", "KILL")
            and rule_id not in HALT_ENTRIES_RULES):
        return Direction.UNDECIDABLE, "C-42"
    return action_direction(old, new)


def scope_direction(old: str, new: str) -> tuple[Direction, str, str]:
    """Direction of a scope change (§3.3).

    Preconditions: none; takes strings, so an unknown scope is UNDECIDABLE, not an error.
    Postconditions: returns (direction, basis, note); basis "C-12" or "C-13", and the note is the
    containment note or the reason class R1 to R4.
    Raises: nothing.
    """
    if old == new:
        return Direction.NEUTRAL, "C-12", "same scope"
    if (old, new) in SCOPE_NARROWER_THAN:
        return Direction.TIGHTENS, "C-12", f"{new} evaluates everything {old} does"
    if (new, old) in SCOPE_NARROWER_THAN:
        return Direction.LOOSENS, "C-12", f"{old} evaluates everything {new} does"
    return Direction.UNDECIDABLE, "C-13", _SCOPE_REASONS.get(frozenset((old, new)), "unranked")


def key_direction(path: str) -> KeyDirection:
    """First match in `CONFIG_KEY_DIRECTIONS`.

    Preconditions: `path` is a dotted config key.
    Postconditions: the listed direction, or UNDECIDABLE from the final catch-all.
    Raises: nothing.
    """
    for pattern, direction in CONFIG_KEY_DIRECTIONS:
        if pattern in (path, "**"):
            return direction
    return KeyDirection.UNDECIDABLE


# =============================================================================
# 4. RULE RECORDS  (§3.4 to §3.6)
# =============================================================================


class _Records:
    """Collects the RULE_FIELD records of one rule."""

    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        self.changes: list[PolicyChange] = []

    def add(self, field: str, old: Any, new: Any, direction: Direction, basis: str,
            reason: str) -> None:
        self.changes.append(PolicyChange(
            kind=ChangeKind.RULE_FIELD, path=f"rules.{self.rule_id}.{field}", rule_id=self.rule_id,
            field=field, old=_canon(old), new=_canon(new), direction=direction, basis=basis,
            reason=reason))


def _source(rule: Rule) -> str | None:
    for name in _THRESHOLD_SOURCES:
        if getattr(rule, name) is not None:
            return name
    return None


def _differs(old: Rule, new: Rule, field: str) -> bool:
    a, b = getattr(old, field), getattr(new, field)
    if field in _SET_FIELDS:
        return _members(a) != _members(b)
    return _identity(a) != _identity(b)


def _threshold_record(old: Rule, new: Rule, out: _Records) -> None:
    a, b = old.threshold, new.threshold
    comparison = new.comparison
    if comparison in _NO_CONSTANT:
        out.add("threshold", a, b, Direction.UNDECIDABLE, "C-04",
                f"{comparison.value} takes no constant")
        return
    if _source(old) != _source(new):
        out.add("threshold", a, b, Direction.UNDECIDABLE, "C-05", "the threshold source switched")
        return
    x, y = _num(a), _num(b)
    if x is None or y is None:
        out.add("threshold", a, b, Direction.UNDECIDABLE, "C-05", "a bound is not a number")
    elif comparison is Comparison.EQ:
        same = x == y
        out.add("threshold", a, b, Direction.NEUTRAL if same else Direction.UNDECIDABLE, "C-03",
                "same number" if same else "an eq bound that moves is disjoint from the old one")
    elif comparison in _MAX_VALUE:
        d = (Direction.LOOSENS if y > x else Direction.TIGHTENS if y < x else Direction.NEUTRAL)
        out.add("threshold", a, b, d, "C-01", f"{comparison.value}: {x} -> {y}")
    elif comparison in _MIN_VALUE:
        d = (Direction.TIGHTENS if y > x else Direction.LOOSENS if y < x else Direction.NEUTRAL)
        out.add("threshold", a, b, d, "C-02", f"{comparison.value}: {x} -> {y}")
    else:  # unreachable today; a future Comparison member must not inherit a direction
        out.add("threshold", a, b, Direction.UNDECIDABLE, "C-04", "no ordered comparison")


def _predicate_records(old: Rule, new: Rule, out: _Records) -> None:
    if old.comparison is not new.comparison:
        out.add("comparison", old.comparison, new.comparison, Direction.UNDECIDABLE, "C-08",
                "any comparison change is UNDECIDABLE (Ruling 12)")
        for field in _PREDICATE_FIELDS:
            if _differs(old, new, field):
                out.add(field, getattr(old, field), getattr(new, field), Direction.UNDECIDABLE,
                        "C-08", "changed together with the comparison")
        return
    if _differs(old, new, "threshold"):
        _threshold_record(old, new, out)
    for field, basis, what in (("threshold_ref", "C-06", "repointed"),
                               ("threshold_input", "C-07", "a different measured bound")):
        if _differs(old, new, field):
            switched = getattr(old, field) is None or getattr(new, field) is None
            out.add(field, getattr(old, field), getattr(new, field), Direction.UNDECIDABLE,
                    "C-05" if switched else basis,
                    "the threshold source switched" if switched else what)
    if _differs(old, new, "allowed_values"):
        a, b = old.allowed_values, new.allowed_values
        if new.comparison is Comparison.IN:
            d = _set_move(a, b, grow=Direction.LOOSENS, shrink=Direction.TIGHTENS)
            out.add("allowed_values", _as_set(a), _as_set(b), d, "C-20",
                    "under `in` the set is the permitted set")
        else:
            out.add("allowed_values", _as_set(a), _as_set(b), Direction.UNDECIDABLE, "C-21",
                    f"{new.comparison.value} has no stated set semantics")
    if _differs(old, new, "disallowed_values"):
        a, b = old.disallowed_values, new.disallowed_values
        if new.comparison is Comparison.NOT_IN:
            d = _set_move(a, b, grow=Direction.TIGHTENS, shrink=Direction.LOOSENS)
            out.add("disallowed_values", _as_set(a), _as_set(b), d, "C-22",
                    "the complement of the permitted set")
        else:
            out.add("disallowed_values", _as_set(a), _as_set(b), Direction.UNDECIDABLE, "C-23",
                    f"{new.comparison.value} has no stated set semantics")
    if _differs(old, new, "allowed_values_ref"):
        out.add("allowed_values_ref", old.allowed_values_ref, new.allowed_values_ref,
                Direction.UNDECIDABLE, "C-25", "repointed")


def _kill_scope_record(old: Rule, new: Rule, action: Direction, out: _Records) -> None:
    a, b = old.kill_scope, new.kill_scope
    kill = RuleAction.KILL
    if old.action is kill and new.action is kill and a is not None and b is not None:
        d = Direction.LOOSENS if b.value == "POOL" else Direction.TIGHTENS
        out.add("kill_scope", a, b, d, "C-17", "a global halt stops a superset of a pool halt")
    elif (old.action is kill) != (new.action is kill) and (a is None) != (b is None):
        out.add("kill_scope", a, b, action, "C-18", "takes the action change's direction")
    else:
        out.add("kill_scope", a, b, Direction.UNDECIDABLE, "C-19",
                "defined only for KILL on both sides")


def _modify_records(old: Rule, new: Rule, action: Direction, out: _Records) -> None:
    a, b = old.modify, new.modify
    if a is None or b is None:
        with_action = (old.action is RuleAction.MODIFY) != (new.action is RuleAction.MODIFY)
        d = action if with_action else Direction.UNDECIDABLE
        out.add("modify", a, b, d, "C-18" if with_action else "C-30",
                "takes the action change's direction" if with_action else "no action change")
        return
    if a.target != b.target:
        out.add("modify.target", a.target, b.target, Direction.UNDECIDABLE, "C-30",
                "a different quantity")
    if _identity(a.to) != _identity(b.to):
        if (isinstance(a.to, Decimal) and isinstance(b.to, Decimal) and a.target == b.target
                and a.target.endswith("_pct")):
            x, y = a.to, b.to
            d = (Direction.LOOSENS if y > x else Direction.TIGHTENS if y < x
                 else Direction.NEUTRAL)
            out.add("modify.to", a.to, b.to, d, "C-29", f"{a.target}: {x} -> {y}")
        else:
            out.add("modify.to", a.to, b.to, Direction.UNDECIDABLE, "C-30",
                    "the arithmetic lives in P2.9")


def _rule_field_changes(old: Rule, new: Rule) -> list[PolicyChange]:
    out = _Records(old.id)
    _predicate_records(old, new, out)

    action_change = Direction.NEUTRAL
    if old.action is not new.action:
        action_change, basis = rule_action_direction(old.id, old.action.value, new.action.value)
        out.add("action", old.action, new.action, action_change, basis,
                f"{old.action.value} -> {new.action.value}")
    if old.mode is not new.mode:
        d = Direction.LOOSENS if new.mode is RuleMode.MONITOR else Direction.TIGHTENS
        out.add("mode", old.mode, new.mode, d, "C-11", f"{old.mode.value} -> {new.mode.value}")
    if old.scope is not new.scope:
        d, basis, note = scope_direction(old.scope.value, new.scope.value)
        out.add("scope", old.scope, new.scope, d, basis, note)
    if old.severity is not new.severity:
        if old.action is new.action:
            out.add("severity", old.severity, new.severity, Direction.NEUTRAL, "C-14",
                    "reporting metadata, not a control")
        else:
            out.add("severity", old.severity, new.severity, action_change, "C-15",
                    "takes the action change's direction")
    if old.on_missing_input is not new.on_missing_input:
        d, _ = action_direction(old.on_missing_input.value, new.on_missing_input.value)
        out.add("on_missing_input", old.on_missing_input, new.on_missing_input, d, "C-16",
                f"{old.on_missing_input.value} -> {new.on_missing_input.value}")
    if _differs(old, new, "kill_scope"):
        _kill_scope_record(old, new, action_change, out)
    if _differs(old, new, "modify"):
        _modify_records(old, new, action_change, out)
    if _differs(old, new, "allowed_values_emergency"):
        a, b = old.allowed_values_emergency, new.allowed_values_emergency
        out.add("allowed_values_emergency", _as_set(a), _as_set(b),
                _set_move(a, b, grow=Direction.LOOSENS, shrink=Direction.TIGHTENS), "C-24",
                "the permitted set for an emergency exit")
    if _differs(old, new, "exempts"):
        a, b = frozenset(old.exempts), frozenset(new.exempts)
        out.add("exempts", a, b,
                _set_move(a, b, grow=Direction.LOOSENS, shrink=Direction.TIGHTENS), "C-26",
                "an exemption narrows the exempted rule's coverage")
    if _differs(old, new, "inputs"):
        a, b = frozenset(old.inputs), frozenset(new.inputs)
        d = _set_move(a, b, grow=Direction.TIGHTENS, shrink=Direction.LOOSENS)
        gone = ", ".join(sorted(a - b))
        out.add("inputs", a, b, d, "C-27",
                f"no longer fails closed on {gone}" if gone else "one more fail-closed path")
    for sub in ("basis", "window", "timing"):
        x, y = getattr(old.measurement, sub), getattr(new.measurement, sub)
        if x != y:
            out.add(f"measurement.{sub}", x, y, Direction.UNDECIDABLE, "C-28",
                    "not monotone in the threshold")
    if old.authority != new.authority:
        out.add("authority", old.authority, new.authority, Direction.UNDECIDABLE, "C-31",
                "keys membership of the pinned constitutional set")
    for field in ("description", "notes"):
        if _differs(old, new, field):
            out.add(field, getattr(old, field), getattr(new, field), Direction.NEUTRAL, "C-32",
                    "free text")
    return out.changes


def _rule_added(rule: Rule) -> PolicyChange:
    if rule.mode is RuleMode.MONITOR or rule.action is RuleAction.ALLOW:
        d, basis = Direction.NEUTRAL, "C-35"
        why = "cannot bind a verdict itself; any exemption it grants is a separate record"
    else:
        d, basis = Direction.TIGHTENS, "C-34"
        why = f"new enforced {rule.action.value} rule: addition never loosens (Ruling 12)"
    return PolicyChange(kind=ChangeKind.RULE_ADDED, path=f"rules.{rule.id}", rule_id=rule.id,
                        field=None, old=None, new=rule.id, direction=d, basis=basis, reason=why)


def _rule_removed(rule: Rule) -> PolicyChange:
    return PolicyChange(kind=ChangeKind.RULE_REMOVED, path=f"rules.{rule.id}", rule_id=rule.id,
                        field=None, old=rule.id, new=None, direction=Direction.LOOSENS,
                        basis="C-33", reason="removal always loosens (Ruling 12)")


def _exemption_records(old: Mapping[str, Rule], new: Mapping[str, Rule]) -> list[PolicyChange]:
    """C-36: one record per (G exempts X) pair the old version does not have, in any mode of G."""
    out: list[PolicyChange] = []
    for grantor in sorted(new):
        before = set(old[grantor].exempts) if grantor in old else set()
        for exempted in sorted(set(new[grantor].exempts) - before):
            out.append(PolicyChange(
                kind=ChangeKind.RULE_EXEMPTED, path=f"rules.{exempted}.exempted_by.{grantor}",
                rule_id=exempted, field=None, related_rule_id=grantor, old=None, new=grantor,
                direction=Direction.LOOSENS, basis="C-36",
                reason=f"{exempted} no longer covers the orders {grantor} passes"))
    return out


def _kill_capable_below_global(rule: Rule) -> bool:
    kill = RuleAction.KILL
    can_kill = rule.action is kill or rule.on_missing_input is kill
    return (rule.mode is RuleMode.ENFORCE and can_kill
            and (rule.kill_scope is None or rule.kill_scope.value != "GLOBAL"))


def _global_kill(rule: Rule) -> bool:
    return (rule.mode is RuleMode.ENFORCE and rule.action is RuleAction.KILL
            and rule.kill_scope is not None and rule.kill_scope.value == "GLOBAL")


def _displacement_records(old: Mapping[str, Rule], new: Mapping[str, Rule],
                          changes: Sequence[PolicyChange]) -> list[PolicyChange]:
    """C-40: an UNDECIDABLE record against each GLOBAL kill a rule can now take a kill ahead of."""
    touched = {c.rule_id for c in changes
               if c.rule_id is not None and c.direction is not Direction.NEUTRAL
               and c.kind not in _DERIVED_KINDS}
    config_moved = any(c.kind in _CONFIG_KINDS and c.direction is not Direction.NEUTRAL
                       for c in changes)
    unexempted = {x for g in old if g in new
                  for x in set(old[g].exempts) - set(new[g].exempts)
                  if set(new[g].exempts) < set(old[g].exempts)}
    out: list[PolicyChange] = []
    for rule_id in sorted(new):
        rule = new[rule_id]
        if not _kill_capable_below_global(rule):
            continue
        reads_config = rule.threshold_ref is not None or rule.allowed_values_ref is not None
        fires = (rule_id not in old or rule_id in touched or (reads_config and config_moved)
                 or rule_id in unexempted)
        if not fires:
            continue
        for global_id in sorted(old):
            if global_id in new and _global_kill(old[global_id]) and rule_id < global_id:
                out.append(PolicyChange(
                    kind=ChangeKind.RULE_KILL_DISPLACED,
                    path=f"rules.{global_id}.kill_displaced_by.{rule_id}", rule_id=global_id,
                    field=None, related_rule_id=rule_id, old=None, new=rule_id,
                    direction=Direction.UNDECIDABLE, basis="C-40",
                    reason=f"{rule_id}'s kill binds ahead of {global_id}'s, with its own scope"))
    return out


# =============================================================================
# 5. CONFIGURATION AND LAYER RECORDS  (§3.7, §3.8)
# =============================================================================


def _leaves(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten to dotted paths, one path per leaf. A list of mappings flattens by index, as
    `a[0].b`; a list of scalars, or an empty container, is a leaf.

    A path must name exactly one leaf. A key holding a dot or a bracket could collide with another
    leaf's path, and the overwritten value would hide a real change with no record (X2H-1). The
    loader accepts such a key, so it is refused here. No legitimate key has one.
    """
    out: dict[str, Any] = {}
    if isinstance(obj, Mapping) and obj:
        for k, v in obj.items():
            if not isinstance(k, str) or not k or set(k) & set(".[]"):
                raise PolicyDiffError(f"config key {k!r} under {prefix!r} cannot be classified: "
                                      f"it must be a non-empty string without . [ or ]")
            out.update(_leaves(v, f"{prefix}{k}."))
    elif isinstance(obj, (list, tuple)) and any(isinstance(x, (Mapping, list, tuple)) for x in obj):
        for i, v in enumerate(obj):
            out.update(_leaves(v, f"{prefix.rstrip('.')}[{i}]."))
    else:
        out[prefix.rstrip(".")] = obj
    return out


def _config_value(path: str, old: Any, new: Any) -> tuple[Direction, str, str]:
    """Direction, basis and reason for a value change, or NEUTRAL with an empty reason for none."""
    kind = key_direction(path)
    if kind is KeyDirection.UNDECIDABLE:
        return Direction.UNDECIDABLE, "C-39", "an unlisted key"
    if kind in (KeyDirection.SET_GROW_LOOSENS, KeyDirection.SET_SHRINK_LOOSENS):
        if not isinstance(old, (list, tuple)) or not isinstance(new, (list, tuple)):
            return Direction.UNDECIDABLE, "C-39", "a set-valued key is not a list on both sides"
        grow_loosens = kind is KeyDirection.SET_GROW_LOOSENS
        d = _set_move(old, new, grow=Direction.LOOSENS if grow_loosens else Direction.TIGHTENS,
                      shrink=Direction.TIGHTENS if grow_loosens else Direction.LOOSENS)
        if d is Direction.UNDECIDABLE:
            return d, "C-39", "the set changed by both adding and removing"
        return d, "C-37", kind.value
    if _kind(old) != _kind(new):
        return Direction.UNDECIDABLE, "C-39", f"a type change: {_kind(old)} -> {_kind(new)}"
    if kind is KeyDirection.NEUTRAL:
        return Direction.NEUTRAL, "C-37", "informational key"
    if kind in (KeyDirection.TRUE_LOOSENS, KeyDirection.FALSE_LOOSENS):
        if not isinstance(old, bool) or not isinstance(new, bool):
            return Direction.UNDECIDABLE, "C-39", "a boolean key is not a bool on both sides"
        loosens = new if kind is KeyDirection.TRUE_LOOSENS else not new
        return (Direction.LOOSENS if loosens else Direction.TIGHTENS), "C-37", kind.value
    x, y = _num(old), _num(new)
    if x is None or y is None:
        return Direction.UNDECIDABLE, "C-39", "a numeric key is not numeric on both sides"
    if x == y:
        return Direction.NEUTRAL, "C-37", "same number, re-represented"
    loosens = y > x if kind is KeyDirection.HIGHER_LOOSENS else y < x
    return (Direction.LOOSENS if loosens else Direction.TIGHTENS), "C-37", f"{x} -> {y}"


def _config_changes(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[PolicyChange]:
    a = _leaves({k: v for k, v in old.items() if k != "rules"})
    b = _leaves({k: v for k, v in new.items() if k != "rules"})
    out: list[PolicyChange] = []
    for path in sorted(set(a) | set(b)):
        neutral = key_direction(path) is KeyDirection.NEUTRAL
        if path not in b:
            d = Direction.NEUTRAL if neutral else Direction.LOOSENS
            out.append(PolicyChange(kind=ChangeKind.CONFIG_REMOVED, path=path, rule_id=None,
                                    field=None, old=_canon(a[path]), new=None, direction=d,
                                    basis="C-38", reason="key removed"))
        elif path not in a:
            d = Direction.NEUTRAL if neutral else Direction.UNDECIDABLE
            out.append(PolicyChange(kind=ChangeKind.CONFIG_ADDED, path=path, rule_id=None,
                                    field=None, old=None, new=_canon(b[path]), direction=d,
                                    basis="C-38", reason="key added"))
        else:
            set_key = key_direction(path) in (KeyDirection.SET_GROW_LOOSENS,
                                              KeyDirection.SET_SHRINK_LOOSENS)
            both_lists = isinstance(a[path], (list, tuple)) and isinstance(b[path], (list, tuple))
            same = (_members(a[path]) == _members(b[path]) if set_key and both_lists
                    else _identity(a[path]) == _identity(b[path]))
            if same:
                continue
            d, basis, why = _config_value(path, a[path], b[path])
            out.append(PolicyChange(kind=ChangeKind.CONFIG_VALUE, path=path, rule_id=None,
                                    field=None, old=_canon(a[path]), new=_canon(b[path]),
                                    direction=d, basis=basis, reason=why))
    return out


def _applicable_layers(market: str | None, environment: str | None) -> list[tuple[str, str]]:
    """(file name, record path) of every layer file that applies to one combination."""
    out = [("policy.override.yaml", "layers.override")]
    if market:
        out.append((f"policy.market.{market}.yaml", f"layers.market.{market}"))
    if environment:
        out.append((f"policy.env.{environment}.yaml", f"layers.env.{environment}"))
    return out


def _layer_changes(market: str | None, environment: str | None, old_layers: frozenset[str],
                   new_layers: frozenset[str]) -> list[PolicyChange]:
    out: list[PolicyChange] = []
    for name, path in _applicable_layers(market, environment):
        if name in new_layers and name not in old_layers:
            out.append(PolicyChange(kind=ChangeKind.LAYER_ADDED, path=path, rule_id=None,
                                    field=None, old=None, new=name,
                                    direction=Direction.UNDECIDABLE, basis="C-41",
                                    reason="a layer file appeared"))
        elif name in old_layers and name not in new_layers:
            out.append(PolicyChange(kind=ChangeKind.LAYER_REMOVED, path=path, rule_id=None,
                                    field=None, old=name, new=None,
                                    direction=Direction.UNDECIDABLE, basis="C-41",
                                    reason="a layer file disappeared"))
    return out


# =============================================================================
# 6. THE DIFF  (§5.1)
# =============================================================================


def _validate(raw: Mapping[str, Any], which: str) -> PolicyDocument:
    try:
        return PolicyDocument.model_validate(raw)
    except ValidationError as exc:
        raise PolicyDiffError(f"the {which} policy does not validate, so no change list can be "
                              f"derived and no change is authorised: {exc}") from exc


def _build_diff(old_raw: Mapping[str, Any], new_raw: Mapping[str, Any], market: str | None,
                environment: str | None, old_layers: frozenset[str], new_layers: frozenset[str],
                old_hash: str, new_hash: str) -> PolicyDiff:
    old_doc, new_doc = _validate(old_raw, "old"), _validate(new_raw, "new")
    old_rules = {r.id: r for r in old_doc.rules}
    new_rules = {r.id: r for r in new_doc.rules}

    changes: list[PolicyChange] = []
    for rule_id in sorted(set(old_rules) | set(new_rules)):
        if rule_id not in new_rules:
            changes.append(_rule_removed(old_rules[rule_id]))
        elif rule_id not in old_rules:
            changes.append(_rule_added(new_rules[rule_id]))
        else:
            changes.extend(_rule_field_changes(old_rules[rule_id], new_rules[rule_id]))
    changes.extend(_exemption_records(old_rules, new_rules))
    changes.extend(_config_changes(old_raw, new_raw))
    changes.extend(_layer_changes(market, environment, old_layers, new_layers))
    changes.extend(_displacement_records(old_rules, new_rules, changes))
    changes.sort(key=_change_key)
    return PolicyDiff(market=market, environment=environment, old_version=old_doc.policy_version,
                      new_version=new_doc.policy_version, old_content_hash=old_hash,
                      new_content_hash=new_hash, changes=tuple(changes))


def diff_policies(
    old_raw: Mapping[str, Any],
    new_raw: Mapping[str, Any],
    *,
    market: str | None = None,
    environment: str | None = None,
    old_layers: frozenset[str] = frozenset(),
    new_layers: frozenset[str] = frozenset(),
) -> PolicyDiff:
    """Derive and classify every difference between two effective documents, for one combination.

    Preconditions: both mappings are merged effective documents. `old_layers` and `new_layers`
    hold the names of the layer files present in each directory, for example
    `policy.env.paper.yaml`.
    Postconditions: a `PolicyDiff` with every record of §3, sorted, byte-reproducible for equal
    inputs.
    Raises: `PolicyDiffError` if either document fails validation or anything else goes wrong
    while classifying. No change list exists then, and nothing is authorised.
    """
    try:
        return _build_diff(old_raw, new_raw, market, environment, old_layers, new_layers,
                           content_hash(old_raw), content_hash(new_raw))
    except PolicyDiffError:
        raise
    except Exception as exc:  # noqa: BLE001 - §8: any failure here authorises nothing
        raise PolicyDiffError(f"the diff could not be derived: {exc}") from exc


def _layer_files(directory: Path) -> frozenset[str]:
    """The layer files present, from the listing: `layers_applied` omits an empty file."""
    names = {p.name for p in Path(directory).glob("policy.*.yaml")}
    return frozenset(n for n in names
                     if n.startswith(("policy.market.", "policy.env."))
                     or n == "policy.override.yaml")


def derive_combinations(old_dir: Path, new_dir: Path) -> tuple[tuple[str | None, str | None], ...]:
    """Every (market, environment) combination the files of either directory can produce.

    Preconditions: both directories are readable.
    Postconditions: `({None} ∪ MARKETS) × ({None} ∪ E)` sorted by (market or "", environment or ""),
    where E is every `<name>` of a `policy.env.<name>.yaml` in either directory. Never takes a
    combination list from a caller.
    Raises: `PolicyDiffError` on a market layer for a market not in `MARKETS`, or an env layer
    whose name is not valid.
    """
    environments: set[str] = set()
    for name in _layer_files(old_dir) | _layer_files(new_dir):
        stem = name.removesuffix(".yaml")
        if stem.startswith("policy.market."):
            market = stem.removeprefix("policy.market.")
            if market not in MARKETS:
                raise PolicyDiffError(f"{name}: {market!r} is not a market")
        elif stem.startswith("policy.env."):
            environment = stem.removeprefix("policy.env.")
            if not _valid_environment(environment):
                raise PolicyDiffError(f"{name}: {environment!r} is not a valid environment name")
            environments.add(environment)
    combos = [(m, e) for m in (None, *MARKETS) for e in (None, *sorted(environments))]
    return tuple(sorted(combos, key=lambda c: (c[0] or "", c[1] or "")))


def _valid_environment(name: str) -> bool:
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    return 1 <= len(name) <= 32 and set(name) <= allowed


def _load(directory: Path, market: str | None, environment: str | None) -> EffectiveConfig:
    try:
        return PolicyLoader(directory).load(market=market, environment=environment,
                                            require_signature=False)
    except Exception as exc:  # noqa: BLE001 - §8: any failure here authorises nothing
        raise PolicyDiffError(f"{directory} does not load for ({market}, {environment}): "
                              f"{exc}") from exc


def diff_policy_dirs(old_dir: Path, new_dir: Path) -> tuple[PolicyDiff, ...]:
    """The diff of every derived combination, each loaded from both directories.

    Preconditions: both directories hold a `policy.yaml`.
    Postconditions: one `PolicyDiff` per combination, in `PolicyAuthorisation` order. A combination
    whose layer files exist in only one directory is still loaded from both, because the loader
    skips absent files.
    Raises: `PolicyDiffError` on any loader, validation or classification failure.
    """
    old_layers, new_layers = _layer_files(old_dir), _layer_files(new_dir)
    out: list[PolicyDiff] = []
    for market, environment in derive_combinations(old_dir, new_dir):
        a, b = _load(old_dir, market, environment), _load(new_dir, market, environment)
        try:
            out.append(_build_diff(a.redacted, b.redacted, market, environment, old_layers,
                                   new_layers, a.content_hash, b.content_hash))
        except PolicyDiffError:
            raise
        except Exception as exc:  # noqa: BLE001 - §8: any failure here authorises nothing
            raise PolicyDiffError(f"the diff could not be derived: {exc}") from exc
    return tuple(out)


# =============================================================================
# 7. AUTHORISING A CHANGE  (§5.1, §5.2)
# =============================================================================


def authorisation_digest(diffs: Sequence[PolicyDiff], request_id: str, requested_at: str) -> str:
    """What every approver signs: a tagged hash of the request and every combination's hashes.

    Preconditions: `diffs` is in `PolicyAuthorisation` order.
    Postconditions: 64 lower-case hex characters. The preimage starts with `APPROVAL_DIGEST_TAG`.
    Raises: nothing of its own; `canonical_json` refuses a value it cannot canonicalise.
    """
    payload = {
        "request_id": request_id,
        "requested_at": requested_at,
        "combinations": [
            {"market": d.market or "", "environment": d.environment or "",
             "old_content_hash": d.old_content_hash, "new_content_hash": d.new_content_hash}
            for d in diffs
        ],
    }
    return hashlib.sha256(APPROVAL_DIGEST_TAG + canonical_json(payload).encode("utf-8")).hexdigest()


def _normalise_identity(identity: str) -> str:
    return identity.strip().lower()


def _approver_map(old_base: EffectiveConfig) -> dict[str, Mapping[str, Any]]:
    signature = old_base.redacted["governance"]["signature"]
    entries = signature.get("approver_key_refs") or {}
    if not isinstance(entries, Mapping):
        raise PolicyGovernanceError("governance.signature.approver_key_refs is not a mapping")
    out: dict[str, Mapping[str, Any]] = {}
    for identity, entry in entries.items():
        name = _normalise_identity(str(identity))
        if name in out or not isinstance(entry, Mapping):
            raise PolicyGovernanceError(f"approver map entry {identity!r} is not usable")
        out[name] = entry
    return out


def _resolve_key(identity: str, entry: Mapping[str, Any]) -> tuple[bytes, bytes]:
    """(PEM, raw 32-byte key) for one listed identity, or `PolicyGovernanceError`."""
    if VAULT_RESOLVER is None:
        raise PolicyGovernanceError("no Vault client: no approver key can be resolved")
    ref, pin = entry.get("ref"), entry.get("raw_key_sha256")
    if not isinstance(ref, str) or not isinstance(pin, str) or not pin.startswith("sha256:"):
        raise PolicyGovernanceError(f"approver {identity}: the map entry is malformed")
    try:
        pem = VAULT_RESOLVER(ref)
        key = load_pem_public_key(pem)
    except Exception as exc:  # noqa: BLE001 - an unresolvable key counts as no approval
        raise PolicyGovernanceError(f"approver {identity}: the key does not resolve") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise PolicyGovernanceError(f"approver {identity}: the key is not Ed25519")
    raw = key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    if hashlib.sha256(raw).hexdigest() != pin.removeprefix("sha256:"):
        raise PolicyGovernanceError(f"approver {identity}: the key differs from its policy pin")
    return pem, raw


def _derive_authorisation(old_dir: Path, new_dir: Path, approvals: Sequence[ApprovalSignature],
                          request_id: str, requested_at: str) -> PolicyAuthorisation:
    """§5.2 without its process-clock check: the part §5.3 step 7 re-runs."""
    diffs = diff_policy_dirs(old_dir, new_dir)
    digest = authorisation_digest(diffs, request_id, requested_at)
    gated = sorted({c.path for d in diffs for c in d.changes if c.requires_two_person})
    required = 0
    if gated:
        required = max(_load(old_dir, d.market, d.environment).document.governance
                       .min_approvals_to_loosen for d in diffs)

    keys = _approver_map(_load(old_dir, None, None))
    unique: dict[str, ApprovalSignature] = {}
    raw_keys: set[bytes] = set()
    for approval in approvals:
        entry = keys.get(approval.identity)
        if entry is None:
            raise PolicyGovernanceError(f"approver {approval.identity} is not listed in the "
                                        f"version in force")
        pem, raw = _resolve_key(approval.identity, entry)
        try:
            verify_signature(digest.encode("ascii"), bytes.fromhex(approval.signature_hex), pem)
        except PolicyError as exc:
            raise PolicyGovernanceError(f"approver {approval.identity}: the signature does not "
                                        f"verify") from exc
        unique.setdefault(approval.identity, approval)
        raw_keys.add(raw)

    if len(raw_keys) < required:
        raise PolicyGovernanceError(
            f"{len(gated)} change(s) loosen or cannot be proven to tighten "
            f"({', '.join(gated)}) with {len(raw_keys)} distinct approver(s); {required} required "
            f"by the version in force. Tightening needs none.")
    try:
        return PolicyAuthorisation(
            diffs=diffs, request_id=request_id, requested_at=requested_at, digest=digest,
            approvals=tuple(unique[k] for k in sorted(unique)),
            required_approvals=str(required), gated_paths=tuple(gated))
    except ValidationError as exc:
        raise PolicyDiffError(f"the authorisation is not valid: {exc}") from exc


def _check_age(requested_at: str, now: datetime, request_id: str) -> None:
    try:
        then = datetime.strptime(requested_at, _UTC_SECOND_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise PolicyDiffError("requested_at is not a real UTC time") from exc
    if then > now:
        raise ApprovalExpiredError(f"requested_at {requested_at} is in the future",
                                   reason="FUTURE", request_id=request_id)
    if now - then > timedelta(hours=APPROVAL_TTL_HOURS):
        raise ApprovalExpiredError(f"request {request_id} is older than {APPROVAL_TTL_HOURS} h",
                                   reason="EXPIRED", request_id=request_id)


def assert_policy_change_authorised(
    old_dir: Path,
    new_dir: Path,
    approvals: Sequence[ApprovalSignature],
    *,
    request_id: str,
    requested_at: str,
) -> PolicyAuthorisation:
    """SPEC-P1.3 §5.3 as amended: the two-person rule over the derived change list.

    There is no key-lookup parameter: keys come from the in-force document's
    `governance.signature.approver_key_refs`, through `VAULT_RESOLVER`.

    Preconditions: `old_dir` holds the version in force and `new_dir` the candidate. `requested_at`
    is UTC, whole seconds. The local-clock check here is an early refusal only; §5.3's database
    clock is the binding one.
    Postconditions: a `PolicyAuthorisation` whose approvals all verified, with at least the count
    the OLD documents require. Nothing is written.
    Raises: `PolicyGovernanceError` on an unlisted identity, an unresolvable or non-Ed25519 key, a
    key differing from its pin, a bad signature, or too few distinct approvers.
    `ApprovalExpiredError` on a future or expired request. `PolicyDiffError` if no change list can
    be derived.
    """
    _check_age(requested_at, datetime.now(timezone.utc), request_id)
    return _derive_authorisation(old_dir, new_dir, approvals, request_id, requested_at)


# =============================================================================
# 8. APPLYING AN AUTHORISATION  (§5.3)
# =============================================================================


def _adds_own_env(diff: PolicyDiff) -> bool:
    path = f"layers.env.{diff.environment}"
    return any(c.kind is ChangeKind.LAYER_ADDED and c.path == path for c in diff.changes)


def _compare_anchor(auth: PolicyAuthorisation,
                    stored: Mapping[tuple[str | None, str | None], str],
                    candidate_dir: Path) -> None:
    by_combo = {(d.market, d.environment): d for d in auth.diffs}
    try:
        candidate = set(derive_combinations(candidate_dir, candidate_dir))
    except PolicyDiffError as exc:
        raise StaleAuthorisationError(f"the candidate has an unknown layer: {exc}") from exc
    if set(stored) | candidate != set(by_combo):
        raise StaleAuthorisationError("the combination set differs from what was authorised; "
                                      "re-diff and re-approve")
    for combo, diff in by_combo.items():
        if combo in stored:
            anchor = stored[combo]
        elif diff.environment is not None and _adds_own_env(diff):
            anchor = stored.get((diff.market, None))
        else:
            raise StaleAuthorisationError(f"{combo}: no in-force row")
        if anchor != diff.old_content_hash:
            raise StaleAuthorisationError(f"{combo}: the stored hash differs from the hash this "
                                          f"change was diffed against")


def _check_files(auth: PolicyAuthorisation, old_dir: Path, candidate_dir: Path) -> None:
    for diff in auth.diffs:
        if _load(candidate_dir, diff.market, diff.environment).content_hash != diff.new_content_hash:
            raise StaleAuthorisationError(
                f"({diff.market}, {diff.environment}): the candidate changed after approval")
    if authorisation_digest(auth.diffs, auth.request_id, auth.requested_at) != auth.digest:
        raise StaleAuthorisationError("the digest does not match the authorisation")
    for diff in auth.diffs:
        if _load(old_dir, diff.market, diff.environment).content_hash != diff.old_content_hash:
            raise StaleAuthorisationError(
                f"({diff.market}, {diff.environment}): old_dir is not the version diffed")
    derived = _derive_authorisation(old_dir, candidate_dir, auth.approvals, auth.request_id,
                                    auth.requested_at)
    if derived != auth:
        raise StaleAuthorisationError("the authorisation does not re-derive to itself")


def assert_authorisation_current(auth: PolicyAuthorisation, conn: Any, old_dir: Path,
                                 candidate_dir: Path) -> None:
    """Prove, on the writer's transaction, that an authorisation may be applied now (§5.3).

    Call this inside the transaction that records the new in-force version, after the writer has
    taken the policy-change lock. `old_dir` supplies no anchor: step 4 compares the store with the
    authorisation, and `old_dir` is only re-derived from after that (a coherence check).

    Preconditions: the writer holds the lock, and `conn` is its open transaction.
    Postconditions: returns only if the request is unused and unexpired, every stored hash matches,
    the candidate is what was approved, and the authorisation re-derives to itself.
    Raises: `InForceAnchorError` if no store is installed, it cannot be read, or it has no rows
    (always, until a frozen spec defines the store). `ApprovalExpiredError` on a future or expired request, which the
    writer catches first; only `reason == "EXPIRED"` writes an event. `StaleAuthorisationError`
    otherwise. On any raise, the writer writes no version.
    """
    if IN_FORCE_STORE is None:
        raise InForceAnchorError("no in-force store is installed (SPEC-P1.3.1 B6): nothing can "
                                 "be applied by this path")
    try:
        stored = IN_FORCE_STORE.in_force_hashes(conn)
        now = IN_FORCE_STORE.database_time(conn)
        used = IN_FORCE_STORE.request_used(conn, auth.request_id)
    except Exception as exc:  # noqa: BLE001 - an unreadable store applies nothing
        raise InForceAnchorError("the in-force store could not be read") from exc
    if not stored:
        raise InForceAnchorError("the in-force store has no rows: its first rows are the genesis, "
                                 "not an approved change")
    if now.tzinfo is None:
        raise InForceAnchorError("the store returned a naive clock")
    if used:
        raise StaleAuthorisationError(f"request {auth.request_id} has already been applied")
    _check_age(auth.requested_at, now, auth.request_id)
    _compare_anchor(auth, stored, candidate_dir)
    try:
        _check_files(auth, old_dir, candidate_dir)
    except StaleAuthorisationError:
        raise
    except PolicyError as exc:
        raise StaleAuthorisationError(f"the authorisation could not be re-checked: {exc}") from exc


__all__ = [
    "ACTION_LADDER", "APPROVAL_DIGEST_TAG", "APPROVAL_TTL_HOURS", "ApprovalExpiredError",
    "ApprovalSignature", "CLASSIFICATION_BASES", "CONFIG_KEY_DIRECTIONS", "ChangeKind",
    "Direction", "HALT_ENTRIES_RULES", "IN_FORCE_STORE", "InForceAnchorError", "InForceStore",
    "KeyDirection", "MARKETS", "PolicyAuthorisation", "PolicyChange", "PolicyDiff",
    "PolicyDiffError", "RULE_FIELDS", "SCOPE_NARROWER_THAN", "StaleAuthorisationError",
    "VAULT_RESOLVER", "action_direction", "assert_authorisation_current",
    "assert_policy_change_authorised", "authorisation_digest", "derive_combinations",
    "diff_policies", "diff_policy_dirs", "key_direction", "rule_action_direction",
    "scope_direction",
]
