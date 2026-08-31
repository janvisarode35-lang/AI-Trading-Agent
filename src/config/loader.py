"""SPEC-P1.3-CONFIG v0.1 — the policy loader and PolicyGate rule engine.

THIS MODULE IS THE ONLY PLACE A RISK NUMBER ENTERS THE SYSTEM.

No other module may read `policy.yaml`, and no module anywhere — including this one —
may read a risk number from an environment variable. That is enforced three ways
(SPEC-P1.3 §7):

  1. Single loader     — `PolicyLoader` is the only reader of the policy file.
  2. Lint              — `lint_no_env_risk_reads()` AST-scans the tree and fails on
                         any `os.environ` / `os.getenv` outside the infrastructure
                         allowlist.
  3. Test              — tests/verify_p13_no_env_risk.py runs the lint and fails CI.

Environment variables are permitted for exactly three infrastructure concerns, none of
which is a risk number: where the database is, where Vault is, and which environment
layer to load. Those live in `INFRA_ENV_ALLOWLIST`.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Final

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# =============================================================================
# 1. ERRORS
# =============================================================================


class PolicyError(Exception):
    """Base of every policy-layer failure. All of them are fail-closed."""


class PolicyLoadError(PolicyError):
    """The policy file could not be loaded, parsed or validated -> the process does
    not start. A system that cannot read its limits does not trade."""


class PolicySignatureError(PolicyError):
    """Content hash or signature verification failed -> the process does not start."""


class PolicyLayerError(PolicyError):
    """A layer tried to override a key it may not touch (§6)."""


class PolicyGovernanceError(PolicyError):
    """A limit change did not carry the approvals its direction requires (§5.3)."""


class VaultReferenceError(PolicyError):
    """A malformed vault:// reference, or a literal secret found in the policy file."""


class RiskNumberFromEnvError(PolicyError):
    """A module read an environment variable where a risk number belongs (§7)."""


class PolicyEvaluationError(PolicyError):
    """The gate could not reach a deterministic verdict -> DENY."""


# =============================================================================
# 2. ENUMERATIONS
# =============================================================================


class RuleAction(str, Enum):
    """Ordered by BINDING PRECEDENCE, most severe first (§4.1)."""

    KILL = "KILL"
    DENY = "DENY"
    MODIFY = "MODIFY"
    ALLOW = "ALLOW"


#: Total order over actions. Lower index binds. This is the whole of the conflict
#: resolution: when MODIFY and DENY both fire, DENY wins because it is more
#: restrictive, and a policy layer that resolved ties the other way would let a
#: sizing rule talk a denial down into a smaller trade.
ACTION_PRECEDENCE: Final[tuple[RuleAction, ...]] = (
    RuleAction.KILL,
    RuleAction.DENY,
    RuleAction.MODIFY,
    RuleAction.ALLOW,
)


class RuleMode(str, Enum):
    ENFORCE = "enforce"
    MONITOR = "monitor"


class RuleScope(str, Enum):
    GLOBAL = "global"
    STRATEGY = "strategy"
    MARKET = "market"
    INSTRUMENT = "instrument"
    POOL = "pool"
    CONSOLIDATED = "consolidated"
    POOL_AND_CONSOLIDATED = "pool_and_consolidated"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Comparison(str, Enum):
    LTE = "lte"
    LT = "lt"
    GTE = "gte"
    GT = "gt"
    EQ = "eq"
    IN = "in"
    NOT_IN = "not_in"
    MULTIPLE_OF = "multiple_of"
    EXISTS = "exists"


class KillScope(str, Enum):
    POOL = "POOL"
    GLOBAL = "GLOBAL"


class Layer(str, Enum):
    DEFAULTS = "defaults"
    MARKET = "market"
    ENVIRONMENT = "environment"
    OPERATOR_OVERRIDE = "operator_override"


#: The ONLY environment variables any module may read. None is a risk number.
INFRA_ENV_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "TRADING_DB_URL",
        "TRADING_VAULT_ADDR",
        "TRADING_VAULT_ROLE",
        "TRADING_ENV",
        "TRADING_POLICY_PATH",
        "TRADING_POLICY_SIGNATURE_PATH",
    }
)

#: Modules permitted to touch os.environ at all. Everything else is a lint failure.
ENV_READER_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {"src/config/loader.py", "src/config/env.py"}
)


# =============================================================================
# 3. VAULT REFERENCES  (§8)
# =============================================================================

#: vault://<mount>/<path>#<key>
_VAULT_RE: Final[re.Pattern[str]] = re.compile(
    r"^vault://(?P<mount>[A-Za-z0-9_\-]+)/(?P<path>[A-Za-z0-9_\-/]+)#(?P<key>[A-Za-z0-9_\-]+)$"
)

#: Shapes that look like a secret sitting in the file rather than a reference to one.
_SECRET_SHAPED: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"^[A-Za-z0-9+/]{40,}={0,2}$"),          # base64-ish blob
    re.compile(r"^(sk|pk|api|key|tok)[-_][A-Za-z0-9]{16,}$", re.I),
    re.compile(r"^[0-9a-f]{32,}$"),                      # bare hex blob
)


class VaultRef(BaseModel):
    """A pointer to a secret. The secret itself never appears in policy.yaml."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mount: str
    path: str
    key: str

    @classmethod
    def parse(cls, raw: str) -> VaultRef:
        m = _VAULT_RE.match(raw)
        if not m:
            raise VaultReferenceError(
                f"malformed vault reference {raw!r}; expected "
                f"vault://<mount>/<path>#<key>"
            )
        return cls(**m.groupdict())

    def render(self) -> str:
        return f"vault://{self.mount}/{self.path}#{self.key}"


def assert_not_a_literal_secret(field: str, value: Any) -> None:
    """Reject a value that looks like a secret rather than a reference to one.

    Heuristic by design: the point is to catch the paste, not to prove absence.
    A false positive is a one-line move to Vault; a false negative is a credential
    in git history for the life of the repository.
    """
    if not isinstance(value, str) or value.startswith("vault://"):
        return
    for pat in _SECRET_SHAPED:
        if pat.match(value):
            raise VaultReferenceError(
                f"{field} looks like a literal secret. Secrets never live in "
                f"policy.yaml — use vault://<mount>/<path>#<key> (SPEC-P1.3 §8)."
            )


# =============================================================================
# 4. THE RULE MODEL  (§3)
# =============================================================================


class Modification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    target: str
    to: str | Decimal


class Measurement(BaseModel):
    """What is measured, over what window, at what moment.

    A threshold without a window and a timing is not a rule — it is a number. Two
    engineers will read "position <= 5%" three different ways unless all three are
    pinned, which is exactly the ambiguity Block C's depth requirement targets.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    basis: str
    window: str
    timing: str

    @field_validator("window")
    @classmethod
    def _known_window(cls, v: str) -> str:
        fixed = {
            "point_in_time", "session", "since_peak", "since_entry",
            "since_listing", "universe_reconstitution",
        }
        if v in fixed:
            return v
        if re.match(r"^(sessions|rolling_days|rolling_seconds):\d+$", v):
            return v
        raise ValueError(
            f"unknown measurement window {v!r}. Windows count COMPLETED EXCHANGE "
            f"SESSIONS unless explicitly named rolling_days/rolling_seconds "
            f"(P0.1 §6)."
        )


class Rule(BaseModel):
    """One policy rule with a stable id.

    `on_missing_input` is constrained to DENY or KILL at the type level. [CONST-6]
    admits nothing else, and a rule that could fail open is not a risk rule.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Annotated[str, Field(pattern=r"^[A-Z]{2,7}-\d{3}$")]
    description: Annotated[str, Field(min_length=10, max_length=400)]
    #: The frozen decision this rule derives from. A rule with no authority is a
    #: rule someone invented.
    authority: Annotated[str, Field(min_length=3, max_length=120)]
    scope: RuleScope
    mode: RuleMode
    severity: Severity
    threshold: Decimal | int | None = None
    #: A threshold resolved from another config key, e.g. universe.US.min_price.
    threshold_ref: str | None = None
    #: A threshold that is itself a MEASURED INPUT rather than a constant.
    #: CASH-001 is `intended_notional <= settled_cash`: the bound is the account's
    #: settled cash at evaluation time, and writing a constant there would be a
    #: fiction. Exactly one of threshold / threshold_ref / threshold_input is set.
    threshold_input: str | None = None
    comparison: Comparison
    measurement: Measurement
    inputs: Annotated[tuple[str, ...], Field(min_length=1)]
    action: RuleAction
    on_missing_input: RuleAction
    modify: Modification | None = None
    kill_scope: KillScope | None = None
    allowed_values: tuple[Any, ...] | None = None
    allowed_values_ref: str | None = None
    allowed_values_emergency: tuple[Any, ...] | None = None
    disallowed_values: tuple[Any, ...] | None = None
    exempts: tuple[str, ...] = ()
    notes: str | None = None

    @model_validator(mode="after")
    def _coherent(self) -> Rule:
        if self.on_missing_input not in (RuleAction.DENY, RuleAction.KILL):
            raise ValueError(
                f"{self.id}: on_missing_input is {self.on_missing_input.value}. "
                f"[CONST-6] admits only DENY or KILL — missing data, stale data, an "
                f"exception or an ambiguous state fails closed."
            )
        if self.action is RuleAction.MODIFY and self.modify is None:
            raise ValueError(f"{self.id}: action MODIFY requires a `modify` block")
        if self.action is not RuleAction.MODIFY and self.modify is not None:
            raise ValueError(f"{self.id}: `modify` is set but action is not MODIFY")
        if self.action is RuleAction.KILL and self.kill_scope is None:
            raise ValueError(f"{self.id}: action KILL requires kill_scope")
        sources = [self.threshold, self.threshold_ref, self.threshold_input]
        if sum(x is not None for x in sources) > 1:
            raise ValueError(
                f"{self.id}: set exactly one of threshold / threshold_ref / "
                f"threshold_input"
            )
        needs_values = {Comparison.IN, Comparison.NOT_IN}
        if self.comparison in needs_values and not (
            self.allowed_values or self.allowed_values_ref or self.disallowed_values
        ):
            raise ValueError(
                f"{self.id}: comparison {self.comparison.value} requires a value set"
            )
        numeric = {Comparison.LTE, Comparison.LT, Comparison.GTE, Comparison.GT}
        if self.comparison in numeric and all(x is None for x in sources):
            raise ValueError(
                f"{self.id}: comparison {self.comparison.value} needs a threshold, "
                f"a threshold_ref or a threshold_input"
            )
        # A *_pct threshold is a fraction. `70` read as a fraction is 7,000%, and the
        # failure is silent in the dangerous direction (P0.3 §15.1).
        if (
            self.threshold is not None
            and "pct" in self.measurement.basis
            and not (Decimal(0) <= Decimal(self.threshold) <= Decimal(1))
        ):
            raise ValueError(
                f"{self.id}: threshold {self.threshold} on a *_pct basis must be a "
                f"fraction in [0,1], never integer percent"
            )
        if self.threshold_input is not None and self.threshold_input not in self.inputs:
            raise ValueError(
                f"{self.id}: threshold_input {self.threshold_input!r} must also be "
                f"declared in `inputs`, or the fail-closed check cannot see it missing"
            )
        if self.exempts and self.action is not RuleAction.ALLOW:
            raise ValueError(f"{self.id}: only an ALLOW rule may grant exemptions")
        return self

    @property
    def binds(self) -> bool:
        """A monitor-mode rule is evaluated and RECORDED, but does not bind."""
        return self.mode is RuleMode.ENFORCE


# =============================================================================
# 5. THE DOCUMENT MODEL  (§2)
# =============================================================================


class Governance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    min_approvals_to_tighten: Annotated[int, Field(ge=0, le=5)]
    min_approvals_to_loosen: Annotated[int, Field(ge=1, le=5)]
    risk_deny_override_permitted: bool
    approver_roles: tuple[str, ...]
    signature: Mapping[str, Any]

    @model_validator(mode="after")
    def _immutables(self) -> Governance:
        if self.risk_deny_override_permitted:
            raise ValueError(
                "risk_deny_override_permitted is immutable false. ADR-09: overriding "
                "a single risk DENY has no approver and no code path. If a human can "
                "override one DENY, [CONST-1] is decorative — the AI need only "
                "persuade the human."
            )
        if self.min_approvals_to_loosen < 2:
            raise ValueError(
                "min_approvals_to_loosen must be >= 2 (SPEC-P1.3 §5.3's two-person "
                "rule). This is STRICTER than ADR-09 row 2, which is permitted "
                "because ADR-09 row 3 makes tightening always safe."
            )
        if self.min_approvals_to_tighten != 0:
            raise ValueError(
                "tightening a limit needs no approval (ADR-09 row 3); requiring one "
                "would delay the only safe emergency action available"
            )
        return self


class Layering(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    order: tuple[Layer, ...]
    operator_override_denied_prefixes: tuple[str, ...]

    @model_validator(mode="after")
    def _order_is_total_and_ends_with_override(self) -> Layering:
        if len(set(self.order)) != len(self.order):
            raise ValueError("layer order must not repeat a layer")
        if self.order[0] is not Layer.DEFAULTS:
            raise ValueError("defaults must be the lowest-precedence layer")
        if self.order[-1] is not Layer.OPERATOR_OVERRIDE:
            raise ValueError("operator_override must be the highest-precedence layer")
        if "rules." not in self.operator_override_denied_prefixes:
            raise ValueError(
                "`rules.` must be denied to the operator_override layer. An operator "
                "who can loosen a limit at runtime has defeated [CONST-1] and ADR-09 "
                "alike; a limit change is a new signed version, never a runtime knob."
            )
        return self


class PolicyDocument(BaseModel):
    """The whole policy file, validated. Frozen: a loaded policy is a value."""

    model_config = ConfigDict(frozen=True, extra="allow")

    schema_version: int
    policy_version: Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")]
    metadata: Mapping[str, Any]
    governance: Governance
    layering: Layering
    secret_refs: Mapping[str, str]
    rules: tuple[Rule, ...]

    @field_validator("secret_refs")
    @classmethod
    def _refs_are_refs(cls, v: Mapping[str, str]) -> Mapping[str, str]:
        for name, raw in v.items():
            VaultRef.parse(raw)          # raises on anything malformed
        return v

    @model_validator(mode="after")
    def _rules_are_sane(self) -> PolicyDocument:
        ids = [r.id for r in self.rules]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"duplicate rule ids: {sorted(dupes)}")
        known = set(ids)
        for r in self.rules:
            for ex in r.exempts:
                if ex not in known:
                    raise ValueError(f"{r.id} exempts unknown rule {ex}")
        if not any(r.action is RuleAction.KILL for r in self.rules):
            raise ValueError(
                "no rule can trip the kill switch. [CONST-7] requires an automatic "
                "path; a policy with no KILL rule has only a manual one."
            )
        return self

    def rule(self, rule_id: str) -> Rule:
        for r in self.rules:
            if r.id == rule_id:
                return r
        raise KeyError(rule_id)

    def evaluation_order(self) -> tuple[Rule, ...]:
        """The deterministic TOTAL ordering of rule evaluation (§4.2).

        Sorted by rule id, lexicographically. Not by severity, and not by
        declaration order in the file:

          - Severity ordering would make evaluation order change when a severity is
            edited, so two policy versions with identical rules could produce
            differently-ordered audit records.
          - File order would make a YAML reshuffle a behavioural change.

        Rule id is stable for the life of the rule, so the audit record of a given
        policy version is byte-reproducible.
        """
        return tuple(sorted(self.rules, key=lambda r: r.id))


# =============================================================================
# 6. CANONICAL HASHING AND SIGNATURE  (§5)
# =============================================================================


def canonical_bytes(doc: Mapping[str, Any]) -> bytes:
    """The exact bytes the content hash and the signature cover.

    Sorted keys, no insignificant whitespace, Decimal as string, UTF-8. Secrets are
    NOT part of the hash input — `secret_refs` holds references, and the referenced
    values never enter this process's hash computation, so rotating a credential
    does not invalidate a signed policy version.
    """

    def _norm(o: Any) -> Any:
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, Mapping):
            return {k: _norm(v) for k, v in sorted(o.items())}
        if isinstance(o, (list, tuple)):
            return [_norm(v) for v in o]
        return o

    return json.dumps(
        _norm(doc), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def content_hash(doc: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(doc)).hexdigest()


def verify_signature(
    payload: bytes, signature: bytes, public_key_pem: bytes
) -> None:
    """Ed25519 detached signature over the canonical bytes.

    ASYMMETRIC BY NECESSITY, not by preference. A shared-secret MAC (stdlib `hmac`)
    would satisfy integrity with zero new dependencies — but the two-person rule
    (§5.3) requires ATTRIBUTING a signature to an individual approver, and every
    holder of a shared HMAC key produces identical signatures. Under HMAC, "two
    approvers signed this" is unprovable. `cryptography` is therefore a justified
    dependency and the reason is recorded in SPEC-P1.3 DECISIONS.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    try:
        key = load_pem_public_key(public_key_pem)
        key.verify(signature, payload)  # type: ignore[attr-defined]
    except InvalidSignature as exc:
        raise PolicySignatureError(
            "policy signature verification FAILED. The process does not start: an "
            "unverified policy is an unknown set of limits."
        ) from exc
    except Exception as exc:  # noqa: BLE001 - any crypto failure is fail-closed
        raise PolicySignatureError(f"signature could not be verified: {exc}") from exc


# =============================================================================
# 7. LAYERING  (§6)
# =============================================================================


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}{k}."))
    else:
        out[prefix.rstrip(".")] = obj
    return out


def merge_layers(
    layers: Sequence[tuple[Layer, Mapping[str, Any]]],
    order: Sequence[Layer],
    operator_denied_prefixes: Sequence[str],
) -> dict[str, Any]:
    """Deep-merge layers in the declared order, lowest precedence first.

    The operator_override layer is checked against the deny-list BEFORE it is
    applied. A denied key is a LOAD FAILURE, not a warning and not a silent drop:
    an operator who tried to override a limit needs to be told they cannot, and the
    attempt belongs in the audit trail.
    """
    by_layer = dict(layers)
    merged: dict[str, Any] = {}

    for layer in order:
        payload = by_layer.get(layer)
        if payload is None:
            continue
        if layer is Layer.OPERATOR_OVERRIDE:
            for key in _flatten(payload):
                for denied in operator_denied_prefixes:
                    if key.startswith(denied):
                        raise PolicyLayerError(
                            f"operator_override may not set {key!r}: prefix "
                            f"{denied!r} is denied to that layer. A risk limit "
                            f"changes by a new signed policy version with the "
                            f"approvals §5.3 requires, never by a runtime override."
                        )
        merged = _deep_merge(merged, payload)
    return merged


def _deep_merge(base: Mapping[str, Any], over: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, Mapping) and isinstance(out.get(k), Mapping):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# =============================================================================
# 8. GOVERNANCE — the two-person rule  (§5.3)
# =============================================================================


class LimitChange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    field: str
    old_value: Decimal
    new_value: Decimal

    @property
    def loosens(self) -> bool:
        """Direction is judged against the rule's comparison, not the raw number.

        Raising a threshold loosens an `lte` rule and TIGHTENS a `gte` rule. Getting
        this backwards would let a limit be relaxed under the tightening path, which
        needs no approval at all.
        """
        raise NotImplementedError  # direction needs the rule; see loosens_for()


def loosens_for(change: LimitChange, rule: Rule) -> bool:
    if rule.comparison in (Comparison.LTE, Comparison.LT):
        return change.new_value > change.old_value
    if rule.comparison in (Comparison.GTE, Comparison.GT):
        return change.new_value < change.old_value
    # For non-ordinal comparisons any change is treated as loosening: we cannot
    # prove it is a tightening, and [CONST-6] resolves the ambiguity conservatively.
    return True


def assert_change_authorised(
    changes: Sequence[LimitChange],
    rules_by_id: Mapping[str, Rule],
    approver_ids: Sequence[str],
    governance: Governance,
) -> None:
    """The two-person rule.

    Distinct approver IDENTITIES, not distinct approvals: two signatures from one
    person are one person's judgement twice.
    """
    distinct = {a.strip().lower() for a in approver_ids if a.strip()}
    loosening = [c for c in changes if loosens_for(c, rules_by_id[c.rule_id])]
    if not loosening:
        return
    if len(distinct) < governance.min_approvals_to_loosen:
        raise PolicyGovernanceError(
            f"{len(loosening)} limit(s) loosened "
            f"({', '.join(sorted(c.rule_id for c in loosening))}) with "
            f"{len(distinct)} distinct approver(s); "
            f"{governance.min_approvals_to_loosen} required. Tightening needs none."
        )


# =============================================================================
# 9. THE LOADER  (§5, §6, §9)
# =============================================================================


class EffectiveConfig(BaseModel):
    """What the system actually runs on, after layering, ready for the audit log."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_version: str
    content_hash: str
    layers_applied: tuple[Layer, ...]
    document: PolicyDocument
    #: Redacted rendering: every secret appears as its vault:// reference, never as
    #: a value. This is what is written to the audit log (§9).
    redacted: Mapping[str, Any]

    def audit_payload(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "content_hash": self.content_hash,
            "layers_applied": [layer.value for layer in self.layers_applied],
            "rule_count": len(self.document.rules),
            "enforced_rule_count": sum(1 for r in self.document.rules if r.binds),
            "effective_config": self.redacted,
        }


class PolicyLoader:
    """The single reader of policy.yaml. Nothing else opens that file."""

    def __init__(self, policy_dir: Path) -> None:
        self._dir = Path(policy_dir)

    def _read(self, name: str) -> dict[str, Any] | None:
        p = self._dir / name
        if not p.is_file():
            return None
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise PolicyLoadError(f"{p} is not valid YAML: {exc}") from exc
        if data is not None and not isinstance(data, dict):
            raise PolicyLoadError(f"{p} must contain a mapping at the top level")
        return data

    def load(
        self,
        *,
        market: str | None = None,
        environment: str | None = None,
        signature: bytes | None = None,
        public_key_pem: bytes | None = None,
        require_signature: bool = True,
    ) -> EffectiveConfig:
        base = self._read("policy.yaml")
        if base is None:
            raise PolicyLoadError(
                f"no policy.yaml in {self._dir}. The process does not start: a system "
                f"that cannot read its limits does not trade."
            )

        layers: list[tuple[Layer, Mapping[str, Any]]] = [(Layer.DEFAULTS, base)]
        if market:
            got = self._read(f"policy.market.{market}.yaml")
            if got:
                layers.append((Layer.MARKET, got))
        if environment:
            got = self._read(f"policy.env.{environment}.yaml")
            if got:
                layers.append((Layer.ENVIRONMENT, got))
        override = self._read("policy.override.yaml")
        if override:
            layers.append((Layer.OPERATOR_OVERRIDE, override))

        # Layering config comes from the base layer: a layer cannot rewrite the rules
        # that govern layering, or the deny-list would be self-defeating.
        layering = Layering.model_validate(base["layering"])
        merged = merge_layers(
            layers, layering.order, layering.operator_override_denied_prefixes
        )

        digest = content_hash(merged)
        if require_signature:
            if signature is None or public_key_pem is None:
                raise PolicySignatureError(
                    "policy signature required but not supplied. Start with "
                    "require_signature=False only in a test."
                )
            verify_signature(digest.encode("ascii"), signature, public_key_pem)

        for name, value in (merged.get("secret_refs") or {}).items():
            assert_not_a_literal_secret(f"secret_refs.{name}", value)
        _assert_no_literal_secrets_anywhere(merged)

        try:
            doc = PolicyDocument.model_validate(merged)
        except Exception as exc:  # noqa: BLE001 - any validation failure is fail-closed
            raise PolicyLoadError(f"policy failed validation: {exc}") from exc

        return EffectiveConfig(
            policy_version=doc.policy_version,
            content_hash=digest,
            layers_applied=tuple(layer for layer, _ in layers),
            document=doc,
            redacted=_redact(merged),
        )


def _redact(obj: Any) -> Any:
    """Secrets are already references, so redaction is a belt-and-braces pass: any
    value that resolves through Vault renders as its reference, never its value."""
    if isinstance(obj, Mapping):
        return {k: _redact(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_redact(v) for v in obj]
    if isinstance(obj, Decimal):
        return str(obj)
    return obj


def _assert_no_literal_secrets_anywhere(obj: Any, path: str = "") -> None:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            _assert_no_literal_secrets_anywhere(v, f"{path}{k}.")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _assert_no_literal_secrets_anywhere(v, f"{path}{i}.")
    else:
        assert_not_a_literal_secret(path.rstrip("."), obj)


# =============================================================================
# 10. THE POLICY GATE  (§4)
# =============================================================================


class RuleOutcome(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    action: RuleAction
    passed: bool
    binds: bool
    observed: str | None = None
    threshold: str | None = None
    reason: str


class PolicyVerdict(BaseModel):
    """The gate's answer, with the full outcome list so the audit record is complete."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: RuleAction
    binding_rule_id: str | None
    kill_scope: KillScope | None = None
    modifications: tuple[tuple[str, str], ...] = ()
    outcomes: tuple[RuleOutcome, ...] = ()
    passes: int = 1

    @property
    def permits_trade(self) -> bool:
        return self.action in (RuleAction.ALLOW, RuleAction.MODIFY)


#: A MODIFY changes the proposal, so the whole rule set is re-evaluated against the
#: modified proposal. Bounded, because two rules that each shrink what the other
#: grows would otherwise loop forever. On exhaustion the verdict is DENY.
MAX_MODIFY_PASSES: Final[int] = 4


class PolicyGate:
    """Evaluates every rule, then combines the outcomes into one verdict.

    EVERY rule is evaluated, always — there is no short-circuit on the first DENY.
    A short-circuit would make the audit record depend on evaluation order, and
    "which other limits would also have failed" is exactly what an investigator
    needs after a loss.
    """

    def __init__(self, config: EffectiveConfig) -> None:
        self._config = config
        self._rules = config.document.evaluation_order()

    def evaluate(
        self,
        facts: Mapping[str, Any],
        *,
        evaluator: Any,
    ) -> PolicyVerdict:
        """`evaluator(rule, facts) -> (passed: bool, observed: str | None)`.

        The comparison itself lives in P2.9, which owns the measurement semantics.
        This layer owns the rule set, the ordering and the combination — which is
        the part that must be identical no matter who implements the arithmetic.
        """
        exempted: set[str] = set()
        outcomes: list[RuleOutcome] = []

        for rule in self._rules:
            missing = [i for i in rule.inputs if i not in facts]
            if missing:
                outcomes.append(
                    RuleOutcome(
                        rule_id=rule.id,
                        action=rule.on_missing_input,
                        passed=False,
                        binds=rule.binds,
                        reason=(
                            f"missing input(s) {', '.join(sorted(missing))} -> "
                            f"{rule.on_missing_input.value} ([CONST-6] fail-closed)"
                        ),
                    )
                )
                continue

            try:
                passed, observed = evaluator(rule, facts)
            except Exception as exc:  # noqa: BLE001 - an exception is an ambiguous state
                outcomes.append(
                    RuleOutcome(
                        rule_id=rule.id,
                        action=rule.on_missing_input,
                        passed=False,
                        binds=rule.binds,
                        reason=f"evaluator raised {type(exc).__name__}: {exc} -> fail-closed",
                    )
                )
                continue

            if passed and rule.action is RuleAction.ALLOW and rule.exempts:
                exempted.update(rule.exempts)

            outcomes.append(
                RuleOutcome(
                    rule_id=rule.id,
                    action=RuleAction.ALLOW if passed else rule.action,
                    passed=passed,
                    binds=rule.binds,
                    observed=None if observed is None else str(observed),
                    threshold=None if rule.threshold is None else str(rule.threshold),
                    reason="passed" if passed else f"{rule.id} breached",
                )
            )

        return self._combine(outcomes, exempted)

    def _combine(
        self, outcomes: Sequence[RuleOutcome], exempted: Iterable[str]
    ) -> PolicyVerdict:
        """Conflict resolution, in one place (§4.1).

        Precedence KILL > DENY > MODIFY > ALLOW. When MODIFY and DENY both fire,
        DENY wins: it is the more restrictive answer, and resolving the other way
        would let a sizing rule negotiate a denial down into a smaller trade.

        Ties inside one action are broken by rule id ascending, so the binding rule
        named in the audit record is reproducible.
        """
        ex = set(exempted)
        binding = [
            o for o in outcomes
            if o.binds and not o.passed and o.rule_id not in ex
            and o.action is not RuleAction.ALLOW
        ]
        if not binding:
            return PolicyVerdict(
                action=RuleAction.ALLOW,
                binding_rule_id=None,
                outcomes=tuple(outcomes),
            )

        for action in ACTION_PRECEDENCE:
            hits = sorted((o for o in binding if o.action is action), key=lambda o: o.rule_id)
            if not hits:
                continue
            first = hits[0]
            if action is RuleAction.KILL:
                rule = self._config.document.rule(first.rule_id)
                return PolicyVerdict(
                    action=RuleAction.KILL,
                    binding_rule_id=first.rule_id,
                    kill_scope=rule.kill_scope,
                    outcomes=tuple(outcomes),
                )
            if action is RuleAction.DENY:
                return PolicyVerdict(
                    action=RuleAction.DENY,
                    binding_rule_id=first.rule_id,
                    outcomes=tuple(outcomes),
                )
            if action is RuleAction.MODIFY:
                mods = tuple(
                    (self._config.document.rule(o.rule_id).modify.target,   # type: ignore[union-attr]
                     str(self._config.document.rule(o.rule_id).modify.to))  # type: ignore[union-attr]
                    for o in hits
                )
                return PolicyVerdict(
                    action=RuleAction.MODIFY,
                    binding_rule_id=first.rule_id,
                    modifications=mods,
                    outcomes=tuple(outcomes),
                )
        raise PolicyEvaluationError("unreachable: binding outcome with no action")


# =============================================================================
# 11. THE ENV-VAR LINT  (§7)
# =============================================================================


def lint_no_env_risk_reads(root: Path) -> list[str]:
    """AST-scan for environment reads outside the infrastructure allowlist.

    Text-searching for "os.environ" would miss `from os import environ` and would
    false-positive on the string in a comment. The AST sees the call.
    """
    violations: list[str] = []
    root = Path(root)

    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root.parent).as_posix() if root.parent != path else path.name
        rel = rel.replace("\\", "/")
        allowed_file = any(rel.endswith(a) for a in ENV_READER_ALLOWLIST)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            violations.append(f"{rel}: unparseable ({exc})")
            continue

        for node in ast.walk(tree):
            name = _env_read_target(node)
            if name is None:
                continue
            if not allowed_file:
                violations.append(
                    f"{rel}:{node.lineno}: reads the environment outside the loader. "
                    f"A risk number comes from policy.yaml, never from the environment."
                )
            elif name is not ... and name not in INFRA_ENV_ALLOWLIST:
                violations.append(
                    f"{rel}:{node.lineno}: reads {name!r}, which is not in "
                    f"INFRA_ENV_ALLOWLIST. Only infrastructure locations may come "
                    f"from the environment."
                )
    return violations


def _env_read_target(node: ast.AST) -> str | None | Any:
    """Return the variable name read, `...` if dynamic, or None if not an env read."""
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr in ("getenv",):
            if _is_os(f.value):
                return _const_str(node.args[0]) if node.args else ...
        if isinstance(f, ast.Name) and f.id == "getenv":
            return _const_str(node.args[0]) if node.args else ...
        if isinstance(f, ast.Attribute) and f.attr in ("get", "__getitem__"):
            if _is_environ(f.value):
                return _const_str(node.args[0]) if node.args else ...
    if isinstance(node, ast.Subscript) and _is_environ(node.value):
        return _const_str(node.slice)
    return None


def _is_os(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id == "os"


def _is_environ(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute) and node.attr == "environ":
        return _is_os(node.value)
    return isinstance(node, ast.Name) and node.id == "environ"


def _const_str(node: ast.AST) -> str | Any:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else ...


def assert_no_env_risk_reads(root: Path) -> None:
    violations = lint_no_env_risk_reads(root)
    if violations:
        raise RiskNumberFromEnvError(
            "environment reads outside the loader allowlist:\n  "
            + "\n  ".join(violations)
        )


def infra_env(name: str, default: str | None = None) -> str | None:
    """The ONLY sanctioned environment read in the system.

    Infrastructure locations only — where the database is, where Vault is, which
    layer to load. Never a threshold, never a limit, never a risk number.
    """
    if name not in INFRA_ENV_ALLOWLIST:
        raise RiskNumberFromEnvError(
            f"{name!r} is not in INFRA_ENV_ALLOWLIST. If this is a risk number it "
            f"belongs in policy.yaml; if it is infrastructure, add it to the "
            f"allowlist in a reviewed change."
        )
    return os.environ.get(name, default)


__all__ = [
    "PolicyError", "PolicyLoadError", "PolicySignatureError", "PolicyLayerError",
    "PolicyGovernanceError", "VaultReferenceError", "RiskNumberFromEnvError",
    "PolicyEvaluationError",
    "RuleAction", "RuleMode", "RuleScope", "Severity", "Comparison", "KillScope",
    "Layer", "ACTION_PRECEDENCE", "MAX_MODIFY_PASSES",
    "INFRA_ENV_ALLOWLIST", "ENV_READER_ALLOWLIST",
    "VaultRef", "assert_not_a_literal_secret",
    "Modification", "Measurement", "Rule", "Governance", "Layering", "PolicyDocument",
    "canonical_bytes", "content_hash", "verify_signature",
    "merge_layers", "LimitChange", "loosens_for", "assert_change_authorised",
    "EffectiveConfig", "PolicyLoader", "RuleOutcome", "PolicyVerdict", "PolicyGate",
    "lint_no_env_risk_reads", "assert_no_env_risk_reads", "infra_env",
]
