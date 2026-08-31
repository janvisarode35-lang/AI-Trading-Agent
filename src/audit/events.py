"""SPEC-P1.4-AUDIT v0.1 — the event taxonomy, envelope and canonical serialisation.

THE AUDIT LOG IS THE SYSTEM OF RECORD. Not the database's derived tables, not the
broker's statement, not the logs: this. Every other store is a projection of it, and
where they disagree, this wins for the question "what did the system do and why".

Three properties this module exists to guarantee:

  APPEND-ONLY     nothing here mutates an event; P1.2 §9 enforces it at the database.
  TAMPER-EVIDENT  every event is chained to its predecessor over a canonical byte
                  string, so altering one row invalidates every row after it.
  REPLAYABLE      every decision event carries enough to re-derive itself bit-for-bit
                  months later — see ReproducibilityBundle.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import secrets
import threading
import time
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from domain.models import AuditEventClass

# =============================================================================
# 1. UUIDv7  (RFC 9562 §5.7)
# =============================================================================
#
# SUPERSEDES SPEC-P1.1-DOMAIN §2 row 10, and by that row's own reasoning.
#
# P1.1 chose uuid4 because "Python 3.12 stdlib has no UUIDv7 and [CONST] forbids a
# dependency that ten lines of stdlib would cover." That rule says IMPLEMENT the ten
# lines, not avoid the format — and the implementation below is twenty. P1.4 needs a
# time-ordered id because an event id that sorts randomly makes every range scan over
# the audit trail a full scan.
#
# `seq` REMAINS the authoritative ordering (P1.2 §9.1). A UUIDv7 is time-ordered but
# not gapless, and chain verification needs gapless. UUIDv7 gives locality; seq gives
# the proof.

_UUID7_LOCK: Final[threading.Lock] = threading.Lock()
_UUID7_STATE: dict[str, int] = {"last_ms": 0, "counter": 0}

#: 12 bits of rand_a are used as a within-millisecond counter (RFC 9562 §6.2
#: "Replace Leftmost Random Bits with Increased Clock Precision"), so ids minted in
#: the same millisecond still sort in creation order.
_UUID7_MAX_COUNTER: Final[int] = 0xFFF


def uuid7(now_ms: int | None = None) -> UUID:
    """A time-ordered UUID. Monotonic within a millisecond, and across threads.

    Layout: 48b unix_ts_ms | 4b version(7) | 12b counter | 2b variant(0b10) | 62b random.
    """
    with _UUID7_LOCK:
        ms = int(time.time() * 1000) if now_ms is None else now_ms
        if ms > _UUID7_STATE["last_ms"]:
            _UUID7_STATE["last_ms"] = ms
            _UUID7_STATE["counter"] = 0
        else:
            # Clock went backwards, or we are still inside the same millisecond.
            # Either way, keep issuing increasing ids rather than colliding.
            ms = _UUID7_STATE["last_ms"]
            _UUID7_STATE["counter"] += 1
            if _UUID7_STATE["counter"] > _UUID7_MAX_COUNTER:
                _UUID7_STATE["last_ms"] = ms + 1
                _UUID7_STATE["counter"] = 0
                ms += 1
        counter = _UUID7_STATE["counter"]

    rand_b = secrets.randbits(62)
    value = (
        (ms & 0xFFFFFFFFFFFF) << 80
        | 0x7 << 76
        | (counter & 0xFFF) << 64
        | 0b10 << 62
        | rand_b
    )
    return UUID(int=value)


def uuid7_timestamp_ms(u: UUID) -> int:
    """The millisecond a UUIDv7 was minted. Useful for a coarse range scan."""
    if u.version != 7:
        raise ValueError(f"{u} is not a UUIDv7 (version={u.version})")
    return u.int >> 80


# =============================================================================
# 2. CANONICAL SERIALISATION  (closes SPEC-P1.2 Q-P1.2-1)
# =============================================================================
#
# The bytes the hash chain covers. RFC 8785 (JCS) with ONE ADDITIONAL RESTRICTION
# that removes its hardest part:
#
#   NO JSON NUMBERS ARE PERMITTED IN AN AUDIT PAYLOAD. Every numeric is a string.
#
# JCS's number canonicalisation (ECMAScript Number::toString) is the only part of the
# spec that is genuinely difficult to implement identically in two languages, and it
# is the part where a float would re-enter through the back door. P1.1 already
# mandates Decimal-as-string on the wire; this makes it a validated precondition of
# the audit log rather than a convention, and canonicalisation reduces to:
#
#   * object keys sorted by UTF-16 code unit
#   * no insignificant whitespace
#   * UTF-8 output, minimal escaping
#   * no duplicate keys (impossible in a dict, checked on parse)

CANONICAL_SCHEMA_VERSION: Final[str] = "jcs-nonum-1"


class NonCanonicalPayloadError(Exception):
    """A payload that cannot be canonically serialised -> the event is not written,
    and therefore ([CONST-5]) the action does not happen."""


def _assert_no_json_numbers(obj: Any, path: str = "$") -> None:
    if isinstance(obj, bool):
        return  # JSON booleans are fine; only numbers are banned
    if isinstance(obj, (int, float, Decimal)):
        raise NonCanonicalPayloadError(
            f"{path} is a JSON number ({obj!r}). Audit payloads carry every numeric as "
            f"a STRING: JCS number canonicalisation is the one part of RFC 8785 that "
            f"differs between implementations, and a float here is the float-money bug "
            f"re-entering through the audit log. Use str(Decimal(...))."
        )
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise NonCanonicalPayloadError(f"{path}: object key {k!r} is not a string")
            _assert_no_json_numbers(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _assert_no_json_numbers(v, f"{path}[{i}]")


def canonical_json(payload: Mapping[str, Any]) -> str:
    """The exact string the hash covers. Deterministic across processes and versions."""
    _assert_no_json_numbers(payload)
    return json.dumps(
        payload,
        sort_keys=True,           # UTF-16 code-unit order for the ASCII keys we emit
        separators=(",", ":"),    # no insignificant whitespace
        ensure_ascii=False,       # UTF-8 output
        allow_nan=False,
    )


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return canonical_json(payload).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


GENESIS_HASH: Final[str] = "0" * 64


# =============================================================================
# 3. EVENT TAXONOMY
# =============================================================================


#: RULE-B4's durability split. IMPORTED, not redefined: P1.1 owns the enum
#: (`domain.models.AuditEventClass`) and P1.2's `audit_log.event_class` column is
#: typed against it. Two definitions of one enum is precisely the drift X3 hunts for,
#: and the failure mode is silent — a member added in one place and not the other.
#:
#: ACTION events are individually durable at `synchronous_commit = remote_write`.
#: EVALUATION events may be batched — EXCEPT when one becomes the REASON for an
#: action, at which point it is promoted (see `promote_to_action`).
EventClass = AuditEventClass


class EventType(str, Enum):
    """The complete catalogue. Adding a member is an additive migration (P1.2 §11.2);
    removing one is not permitted — an event type in a six-year-old row must still
    resolve to exactly one meaning."""

    # --- lifecycle ---------------------------------------------------------
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    EFFECTIVE_CONFIG_RENDERED = "EFFECTIVE_CONFIG_RENDERED"
    # --- ingest ------------------------------------------------------------
    DATA_RECEIVED = "DATA_RECEIVED"
    DATA_REJECTED = "DATA_REJECTED"
    FX_RATE_RECORDED = "FX_RATE_RECORDED"
    CORPORATE_ACTION_APPLIED = "CORPORATE_ACTION_APPLIED"
    UNIVERSE_RECONSTITUTED = "UNIVERSE_RECONSTITUTED"
    # --- analysis ----------------------------------------------------------
    CANDIDATE_SCREENED = "CANDIDATE_SCREENED"
    SCORE_COMPUTED = "SCORE_COMPUTED"
    REGIME_CLASSIFIED = "REGIME_CLASSIFIED"
    GATE_OPENED = "GATE_OPENED"
    GATE_CLOSED = "GATE_CLOSED"
    # --- llm ---------------------------------------------------------------
    LLM_CALLED = "LLM_CALLED"
    LLM_OUTPUT_ACCEPTED = "LLM_OUTPUT_ACCEPTED"
    LLM_OUTPUT_REJECTED = "LLM_OUTPUT_REJECTED"
    # --- decision and risk -------------------------------------------------
    DECISION_MADE = "DECISION_MADE"
    RISK_EVALUATED = "RISK_EVALUATED"
    LIMIT_BREACHED = "LIMIT_BREACHED"
    # --- execution ---------------------------------------------------------
    ORDER_INTENT = "ORDER_INTENT"
    ORDER_SENT = "ORDER_SENT"
    ORDER_ACKED = "ORDER_ACKED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_CANCELED = "ORDER_CANCELED"
    ORDER_STATE_UNKNOWN = "ORDER_STATE_UNKNOWN"
    FILL_RECEIVED = "FILL_RECEIVED"
    # --- portfolio ---------------------------------------------------------
    POSITION_OPENED = "POSITION_OPENED"
    POSITION_CLOSED = "POSITION_CLOSED"
    POSITION_UNRECONCILED = "POSITION_UNRECONCILED"
    RECONCILIATION_COMPLETED = "RECONCILIATION_COMPLETED"
    NAV_SNAPSHOT = "NAV_SNAPSHOT"
    # --- control -----------------------------------------------------------
    KILL_SWITCH_ARMED = "KILL_SWITCH_ARMED"
    KILL_SWITCH_TRIPPED = "KILL_SWITCH_TRIPPED"
    KILL_SWITCH_RESET = "KILL_SWITCH_RESET"
    CONFIG_CHANGED = "CONFIG_CHANGED"
    MODEL_DEPLOYED = "MODEL_DEPLOYED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
    # --- integrity ---------------------------------------------------------
    CHAIN_ANCHORED = "CHAIN_ANCHORED"
    CHAIN_VERIFIED = "CHAIN_VERIFIED"
    INTEGRITY_INCIDENT = "INTEGRITY_INCIDENT"


class Producer(str, Enum):
    """Which component emits an event. One producer per type — two producers for one
    type means two code paths can disagree about what the event means."""

    INGEST = "P2.1_INGEST"
    QUALITY = "P2.2_QUALITY"
    SCANNER = "P2.3_SCANNER"
    SCORER = "P2.5_SCORER"
    REGIME = "P2.6_REGIME"
    DECISION = "P2.7_DECISION"
    SIZER = "P2.8_SIZER"
    RISK = "P2.9_RISK"
    KILL_SWITCH = "P2.10_KILL_SWITCH"
    BROKER = "P3.1_BROKER"
    EXECUTION = "P3.2_EXECUTION"
    MONITOR = "P3.3_MONITOR"
    EXIT = "P3.4_EXIT"
    GATE = "P4.2_GATE"
    RESEARCH = "P4.3_RESEARCH"
    VALIDATOR = "P4.4_VALIDATOR"
    ORCHESTRATOR = "P6.4_ORCHESTRATOR"
    AUDITOR = "P6.1_AUDITOR"
    GOVERNANCE = "P6.6_GOVERNANCE"


class EventSpec(BaseModel):
    """One row of the taxonomy: what the event is, who emits it, when."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_type: EventType
    event_class: EventClass
    producer: Producer
    trigger: Annotated[str, Field(min_length=10, max_length=300)]
    required_payload_keys: tuple[str, ...]
    #: True when this event, on its own, authorises or records a side effect. Those
    #: are the events [CONST-5]'s write-before-act protocol governs (§5).
    is_effectful: bool = False
    #: True when the event must carry a full ReproducibilityBundle (§4).
    requires_reproducibility: bool = False


def _s(
    t: EventType,
    c: EventClass,
    p: Producer,
    trigger: str,
    keys: Sequence[str],
    *,
    effectful: bool = False,
    repro: bool = False,
) -> EventSpec:
    return EventSpec(
        event_type=t, event_class=c, producer=p, trigger=trigger,
        required_payload_keys=tuple(keys), is_effectful=effectful,
        requires_reproducibility=repro,
    )


E, C, P = EventType, EventClass, Producer

#: THE TAXONOMY. Every event type maps to exactly one spec.
EVENT_REGISTRY: Final[Mapping[EventType, EventSpec]] = {
    s.event_type: s
    for s in (
        # -- lifecycle -------------------------------------------------------
        _s(E.RUN_STARTED, C.SYSTEM, P.ORCHESTRATOR,
           "A pipeline, ingest, monitor or backtest invocation begins.",
           ["run_id", "run_type", "market", "trading_date", "code_version",
            "config_hash", "is_paper", "is_backtest"]),
        _s(E.RUN_FINISHED, C.SYSTEM, P.ORCHESTRATOR,
           "The invocation ends, successfully or not.",
           ["run_id", "outcome", "duration_seconds"]),
        _s(E.EFFECTIVE_CONFIG_RENDERED, C.SYSTEM, P.ORCHESTRATOR,
           "Policy layers merged and validated at run start, before any decision.",
           ["policy_version", "content_hash", "layers_applied", "rule_count",
            "enforced_rule_count", "effective_config"]),
        # -- ingest ----------------------------------------------------------
        _s(E.DATA_RECEIVED, C.EVALUATION, P.INGEST,
           "A vendor payload is accepted into the store after quality checks pass.",
           ["source", "data_type", "row_count", "as_of", "retrieved_at", "input_hash"]),
        _s(E.DATA_REJECTED, C.EVALUATION, P.QUALITY,
           "A vendor payload fails a quality gate and is not stored.",
           ["source", "data_type", "reason", "rejected_count", "input_hash"]),
        _s(E.FX_RATE_RECORDED, C.NAV, P.INGEST,
           "An FX rate is written. Immutable thereafter (ADR-15 §5).",
           ["as_of_date", "base", "quote", "rate", "source"], effectful=True),
        _s(E.CORPORATE_ACTION_APPLIED, C.ACTION, P.INGEST,
           "A split, dividend, merger or delisting is applied to stored history.",
           ["instrument_id", "action_type", "effective_date", "ratio"], effectful=True),
        _s(E.UNIVERSE_RECONSTITUTED, C.ACTION, P.SCANNER,
           "Weekly reconstitution writes a new immutable universe version (I7).",
           ["universe_version", "market", "effective_from", "instrument_count",
            "entered_count", "exited_count"], effectful=True),
        # -- analysis --------------------------------------------------------
        _s(E.CANDIDATE_SCREENED, C.EVALUATION, P.SCANNER,
           "An instrument is evaluated against the Tier-1 deterministic screen.",
           ["instrument_id", "trading_date", "passed", "filters_passed",
            "filters_failed", "universe_version"]),
        _s(E.SCORE_COMPUTED, C.EVALUATION, P.SCORER,
           "A deterministic model scores a candidate.",
           ["instrument_id", "kind", "value", "model_id", "model_version",
            "feature_vector_hash"], repro=True),
        _s(E.REGIME_CLASSIFIED, C.EVALUATION, P.REGIME,
           "The regime classifier produces a label for the session.",
           ["market", "trading_date", "label", "confidence", "model_id"], repro=True),
        _s(E.GATE_OPENED, C.EVALUATION, P.GATE,
           "The inference gate selects a candidate for the LLM tier.",
           ["instrument_id", "gate_width", "rank", "reason"]),
        _s(E.GATE_CLOSED, C.EVALUATION, P.GATE,
           "The gate declines a candidate; it proceeds on the deterministic path only.",
           ["instrument_id", "rank", "reason"]),
        # -- llm -------------------------------------------------------------
        _s(E.LLM_CALLED, C.EVALUATION, P.RESEARCH,
           "A gated LLM call is issued for one candidate.",
           ["llm_call_id", "instrument_id", "provider_id", "model_id", "prompt_version",
            "sanitiser_version", "prompt_hash", "sampling_parameters", "tier"], repro=True),
        _s(E.LLM_OUTPUT_ACCEPTED, C.EVALUATION, P.VALIDATOR,
           "LLM output passes schema and content validation and becomes a Thesis.",
           ["llm_call_id", "thesis_id", "response_hash", "input_tokens",
            "output_tokens", "cost_usd"], repro=True),
        _s(E.LLM_OUTPUT_REJECTED, C.EVALUATION, P.VALIDATOR,
           "LLM output fails validation. The candidate becomes a NO-THESIS candidate; "
           "it is never repaired (RULE-B10).",
           ["llm_call_id", "instrument_id", "reason", "response_hash"]),
        # -- decision and risk ------------------------------------------------
        _s(E.DECISION_MADE, C.ACTION, P.DECISION,
           "The decision engine emits a final action for one instrument, AFTER an "
           "ALLOW risk verdict.",
           ["decision_id", "instrument_id", "action", "target_quantity",
            "risk_verdict_id", "strategy_version", "model_id"],
           effectful=True, repro=True),
        _s(E.RISK_EVALUATED, C.RISK, P.RISK,
           "The deterministic risk engine returns a verdict on one proposal.",
           ["verdict_id", "request_id", "instrument_id", "decision", "binding_rule_id",
            "limits_evaluated", "policy_content_hash"], effectful=True, repro=True),
        _s(E.LIMIT_BREACHED, C.RISK, P.RISK,
           "A policy rule breached. Emitted for every breach, including monitor-mode "
           "rules that did not bind.",
           ["rule_id", "scope", "mode", "observed", "threshold", "action_taken"]),
        # -- execution -------------------------------------------------------
        _s(E.ORDER_INTENT, C.ACTION, P.EXECUTION,
           "Written BEFORE the broker call. This is the write half of write-before-act "
           "and the dedupe key rule N12 requires.",
           ["order_id", "client_order_id", "instrument_id", "side", "order_type",
            "quantity", "limit_price", "broker_id", "strategy_id"], effectful=True),
        _s(E.ORDER_SENT, C.ACTION, P.EXECUTION,
           "The broker call returned without a transport error.",
           ["order_id", "client_order_id", "broker_id", "sent_at"], effectful=True),
        _s(E.ORDER_ACKED, C.ACTION, P.BROKER,
           "The broker acknowledged and assigned its own order id.",
           ["order_id", "broker_order_id", "state"], effectful=True),
        _s(E.ORDER_REJECTED, C.ACTION, P.BROKER,
           "The broker rejected the order.",
           ["order_id", "reason", "broker_code"], effectful=True),
        _s(E.ORDER_CANCELED, C.ACTION, P.EXECUTION,
           "The order was cancelled, by us or by the broker (rule N13).",
           ["order_id", "reason", "initiated_by"], effectful=True),
        _s(E.ORDER_STATE_UNKNOWN, C.ACTION, P.EXECUTION,
           "The broker became unreachable or answered ambiguously. Fail-closed: no new "
           "order for this instrument until reconciliation resolves it.",
           ["order_id", "instrument_id", "last_known_state", "reason"], effectful=True),
        _s(E.FILL_RECEIVED, C.ACTION, P.BROKER,
           "A fill arrived. Idempotent on (broker_id, broker_fill_id).",
           ["fill_id", "order_id", "broker_fill_id", "quantity", "price", "fees"],
           effectful=True),
        # -- portfolio -------------------------------------------------------
        _s(E.POSITION_OPENED, C.ACTION, P.MONITOR,
           "The first fill on an instrument creates a lot and opens a position.",
           ["instrument_id", "pool_id", "lot_id", "quantity", "cost_total"],
           effectful=True),
        _s(E.POSITION_CLOSED, C.ACTION, P.MONITOR,
           "The last open lot is fully consumed.",
           ["instrument_id", "pool_id", "realised_pnl", "sessions_held", "exit_reason"],
           effectful=True),
        _s(E.POSITION_UNRECONCILED, C.ACTION, P.MONITOR,
           "Our quantity disagrees with the broker's. Denies new entries POOL-WIDE.",
           ["instrument_id", "pool_id", "our_quantity", "broker_quantity"],
           effectful=True),
        _s(E.RECONCILIATION_COMPLETED, C.ACTION, P.MONITOR,
           "A human-verified reconciliation resolves an UNRECONCILED position.",
           ["instrument_id", "pool_id", "resolved_quantity", "approval_id"],
           effectful=True),
        _s(E.NAV_SNAPSHOT, C.NAV, P.MONITOR,
           "Pool or consolidated NAV computed. Invariant I4 replays counters from these.",
           ["nav_id", "scope", "total_value", "peak_value", "trading_date"],
           effectful=True),
        # -- control ---------------------------------------------------------
        _s(E.KILL_SWITCH_ARMED, C.KILL_SWITCH, P.KILL_SWITCH,
           "A human re-enabled trading. Requires an ApprovalGrant (ADR-09 row 1).",
           ["scope", "pool_id", "approval_id", "approver"], effectful=True),
        _s(E.KILL_SWITCH_TRIPPED, C.KILL_SWITCH, P.KILL_SWITCH,
           "Automatic or manual halt.",
           ["scope", "pool_id", "reason", "triggering_rule_id", "tripped_by"],
           effectful=True),
        _s(E.KILL_SWITCH_RESET, C.KILL_SWITCH, P.KILL_SWITCH,
           "Boot restores the switch to TRIPPED unconditionally (invariant I3).",
           ["scope", "restored_state", "reason"], effectful=True),
        _s(E.CONFIG_CHANGED, C.SYSTEM, P.GOVERNANCE,
           "A new signed policy version was applied.",
           ["old_content_hash", "new_content_hash", "policy_version", "approver_ids",
            "changes", "loosened"], effectful=True),
        _s(E.MODEL_DEPLOYED, C.SYSTEM, P.GOVERNANCE,
           "A model was promoted to champion or deployed as challenger (ADR-08).",
           ["model_id", "model_version", "role", "artifact_sha256", "wf_windows",
            "wf_closed_trades", "approval_id"], effectful=True),
        _s(E.APPROVAL_REQUESTED, C.APPROVAL, P.GOVERNANCE,
           "The pipeline requests a human approval. It can never grant one.",
           ["approval_id", "action", "payload_hash", "nonce", "sla_hours"]),
        _s(E.APPROVAL_GRANTED, C.APPROVAL, P.GOVERNANCE,
           "A human granted an approval out of band, consuming a single-use nonce.",
           ["approval_id", "action", "approver", "role", "nonce", "payload_hash"],
           effectful=True),
        _s(E.APPROVAL_EXPIRED, C.APPROVAL, P.GOVERNANCE,
           "An approval SLA elapsed; the conservative default action applies.",
           ["approval_id", "action", "default_action_taken"]),
        # -- integrity -------------------------------------------------------
        _s(E.CHAIN_ANCHORED, C.SYSTEM, P.AUDITOR,
           "A checkpoint hash was published off-VM (§6.3).",
           ["anchor_seq", "anchor_hash", "destination", "published_at"], effectful=True),
        _s(E.CHAIN_VERIFIED, C.SYSTEM, P.AUDITOR,
           "A chain verification pass completed.",
           ["from_seq", "to_seq", "events_checked", "duration_seconds", "result"]),
        _s(E.INTEGRITY_INCIDENT, C.SYSTEM, P.AUDITOR,
           "A gap, fork or anchor mismatch. HARD STOP (ADR-10 §5).",
           ["broken_at_seq", "reason", "detected_by"], effectful=True),
    )
}

#: Events that authorise or record a side effect. [CONST-5]'s protocol governs these.
EFFECTFUL_EVENT_TYPES: Final[frozenset[EventType]] = frozenset(
    t for t, s in EVENT_REGISTRY.items() if s.is_effectful
)

#: Events that must carry a full reproducibility bundle.
REPRODUCIBLE_EVENT_TYPES: Final[frozenset[EventType]] = frozenset(
    t for t, s in EVENT_REGISTRY.items() if s.requires_reproducibility
)


# =============================================================================
# 4. REPRODUCIBILITY
# =============================================================================


class ReproducibilityBundle(BaseModel):
    """Everything needed to re-derive a decision BIT-FOR-BIT months later.

    The test for whether a field belongs here is blunt: if changing it changes the
    output, and it is not captured, the decision is not reproducible. Every field
    below has failed that test at least once in somebody's post-mortem.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # -- what code ran --------------------------------------------------------
    code_version: Annotated[str, Field(min_length=7, max_length=40)]
    #: Interpreter and OS. A Decimal context or a locale differs between them, and
    #: "it reproduced on my machine" is not a reproduction.
    runtime: Mapping[str, str]
    #: name -> exact version, for every library that touches a number or a model.
    library_versions: Mapping[str, str]

    # -- what configuration ---------------------------------------------------
    config_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    policy_version: str

    # -- what model -----------------------------------------------------------
    model_id: str
    model_version: str
    #: Hash of the serialised model artifact, not of its name. Two artifacts can
    #: share a version string; they cannot share a digest.
    model_artifact_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None

    # -- what data ------------------------------------------------------------
    #: NOT the data. A reference the bitemporal as-of functions can resolve
    #: (SPEC-P1.2 §3.3) plus a hash of the exact rows that came back.
    input_snapshot_refs: tuple[str, ...]
    input_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    #: The two cutoffs that make an as-of read reproducible (SPEC-P1.2 §3.3).
    market_asof: datetime
    knowledge_asof: datetime

    # -- what randomness ------------------------------------------------------
    #: Every seed the run consumed. An unseeded RNG makes a model output
    #: irreproducible, and "it was close enough" is not a defence to a regulator.
    random_seeds: Mapping[str, str] = Field(default_factory=dict)

    # -- llm-specific ---------------------------------------------------------
    llm_prompt_hash: str | None = None
    llm_response_hash: str | None = None
    #: temperature, top_p, seed, max_tokens, stop. Two of these differing produce a
    #: different thesis from the same prompt.
    llm_sampling_parameters: Mapping[str, str] | None = None

    @model_validator(mode="after")
    def _llm_fields_travel_together(self) -> ReproducibilityBundle:
        llm = (self.llm_prompt_hash, self.llm_response_hash, self.llm_sampling_parameters)
        if any(x is not None for x in llm) and not all(x is not None for x in llm):
            raise ValueError(
                "an LLM-derived event needs prompt hash, response hash AND sampling "
                "parameters; any one alone cannot reproduce the output"
            )
        return self

    @classmethod
    def capture_runtime(cls) -> dict[str, str]:
        return {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "system": platform.system(),
            "machine": platform.machine(),
        }


# =============================================================================
# 5. THE ENVELOPE
# =============================================================================

#: Bumped when the envelope's shape changes. Written on every event so a reader six
#: years from now knows which shape it is looking at.
ENVELOPE_SCHEMA_VERSION: Final[str] = "1"


class AuditEnvelope(BaseModel):
    """One event. Immutable, chained, and self-describing.

    Extends SPEC-P1.1's envelope with the four fields P1.4 owns: `causation_id`,
    `schema_version`, `input_hash` and `canonical_schema`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # -- identity -------------------------------------------------------------
    event_id: UUID
    #: Gapless, monotonic, GLOBAL. Assigned by the database under an advisory lock
    #: (SPEC-P1.2 §9.4). ORDERING COMES FROM HERE, never from event_id or a clock.
    seq: Annotated[int, Field(ge=0)]

    # -- causality ------------------------------------------------------------
    #: The event that DIRECTLY caused this one. Null for a root event.
    causation_id: UUID | None = None
    #: The run every event in this causal tree belongs to. This is the correlation id.
    run_id: UUID

    # -- classification -------------------------------------------------------
    event_type: EventType
    event_class: EventClass
    schema_version: str = ENVELOPE_SCHEMA_VERSION
    canonical_schema: str = CANONICAL_SCHEMA_VERSION

    # -- time -----------------------------------------------------------------
    #: When the thing happened in the world.
    occurred_at: datetime
    #: When we wrote it down. Distinct: the gap between them is observability data,
    #: and a gap that grows is a system falling behind.
    recorded_at: datetime

    # -- provenance -----------------------------------------------------------
    actor: Annotated[str, Field(min_length=1, max_length=120)]
    is_paper: bool
    is_backtest: bool
    #: SHA-256 over the canonical form of the FULL INPUT that produced this event.
    #: Not the payload — the input. Two events with identical payloads produced by
    #: different inputs are different events, and this is how you tell.
    input_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

    # -- content --------------------------------------------------------------
    payload: Mapping[str, Any]
    reproducibility: ReproducibilityBundle | None = None

    # -- chain ----------------------------------------------------------------
    prev_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    payload_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

    @field_validator("occurred_at", "recorded_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("audit timestamps are tz-aware UTC; a naive value is rejected")
        return v.astimezone(timezone.utc)

    @model_validator(mode="after")
    def _coherent(self) -> AuditEnvelope:
        spec = EVENT_REGISTRY.get(self.event_type)
        if spec is None:
            raise ValueError(f"{self.event_type} is not in EVENT_REGISTRY")
        if spec.event_class is not self.event_class:
            raise ValueError(
                f"{self.event_type.value} is class {spec.event_class.value} in the "
                f"registry but was written as {self.event_class.value}"
            )
        missing = [k for k in spec.required_payload_keys if k not in self.payload]
        if missing:
            raise ValueError(
                f"{self.event_type.value} payload is missing {sorted(missing)}"
            )
        if spec.requires_reproducibility and self.reproducibility is None:
            raise ValueError(
                f"{self.event_type.value} must carry a ReproducibilityBundle: it is a "
                f"model- or LLM-derived event and cannot otherwise be re-derived"
            )
        if self.recorded_at < self.occurred_at:
            raise ValueError("recorded_at precedes occurred_at")
        if self.is_paper and self.is_backtest:
            raise ValueError("an event is paper or backtest, never both (rule N11)")
        if self.seq == 0 and self.prev_hash != GENESIS_HASH:
            raise ValueError("the genesis event must carry the all-zero prev_hash")
        if self.seq > 0 and self.prev_hash == GENESIS_HASH:
            raise ValueError("only seq 0 may carry the genesis hash")
        if self.causation_id is not None and self.causation_id == self.event_id:
            raise ValueError("an event cannot cause itself")
        _assert_no_json_numbers(self.payload, f"payload[{self.event_type.value}]")
        return self

    # -- the hashed preimage --------------------------------------------------
    def hash_preimage(self) -> bytes:
        """EXACTLY what the chain hash covers, in EXACTLY this order (§6.1).

        Field order is fixed here and nowhere else. It is not the model's field order
        — reordering a Pydantic model would then silently invalidate every historical
        hash — and it is not alphabetical, because a field rename would do the same.
        It is an explicit list, and changing it is a schema_version bump.
        """
        return canonical_bytes(
            {
                "canonical_schema": self.canonical_schema,
                "schema_version": self.schema_version,
                "seq": str(self.seq),
                "prev_hash": self.prev_hash,
                "event_id": str(self.event_id),
                "causation_id": "" if self.causation_id is None else str(self.causation_id),
                "run_id": str(self.run_id),
                "event_type": self.event_type.value,
                "event_class": self.event_class.value,
                "occurred_at": self.occurred_at.isoformat(),
                "actor": self.actor,
                "is_paper": self.is_paper,
                "is_backtest": self.is_backtest,
                "input_hash": self.input_hash,
                "payload": self.payload,
            }
        )

    def compute_hash(self) -> str:
        return sha256_hex(self.hash_preimage())

    def verify_self(self) -> bool:
        """Does this row's stored hash match its own content?"""
        return self.compute_hash() == self.payload_hash

    @property
    def is_effectful(self) -> bool:
        return EVENT_REGISTRY[self.event_type].is_effectful


def promote_to_action(event_class: EventClass, became_a_reason: bool) -> EventClass:
    """RULE-B4(a): an evaluation that becomes the REASON for an action is promoted to
    ACTION class, and is therefore written durably BEFORE the decision that cites it.

    A Tier-1 screen row for a name that gets selected is evidence, not a scan result.
    """
    if became_a_reason and event_class is EventClass.EVALUATION:
        return EventClass.ACTION
    return event_class


__all__ = [
    "uuid7", "uuid7_timestamp_ms",
    "canonical_json", "canonical_bytes", "sha256_hex", "GENESIS_HASH",
    "CANONICAL_SCHEMA_VERSION", "ENVELOPE_SCHEMA_VERSION", "NonCanonicalPayloadError",
    "EventClass", "EventType", "Producer", "EventSpec", "EVENT_REGISTRY",
    "EFFECTFUL_EVENT_TYPES", "REPRODUCIBLE_EVENT_TYPES",
    "ReproducibilityBundle", "AuditEnvelope", "promote_to_action",
]
