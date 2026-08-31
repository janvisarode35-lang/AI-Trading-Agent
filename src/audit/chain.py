"""SPEC-P1.4-AUDIT v0.1 — hash chain, anchoring, write-before-act recovery, replay.

The chain is what makes the log tamper-EVIDENT. It does not make it tamper-PROOF, and
§9 of the spec is explicit about the difference: nothing inside a database survives a
superuser. What the chain guarantees is that a mutation cannot go unnoticed, and what
anchoring adds is that it cannot go unnoticed even by whoever holds the database.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Final
from uuid import UUID

from .events import (
    GENESIS_HASH,
    AuditEnvelope,
    EventType,
    canonical_bytes,
    sha256_hex,
)


class ChainError(Exception):
    """Any chain integrity failure. Every one of them is a HARD STOP (ADR-10 §5)."""


class BreakKind(str, Enum):
    GAP = "GAP"                       # a seq is missing
    FORK = "FORK"                     # prev_hash does not match the predecessor
    CONTENT_MUTATED = "CONTENT_MUTATED"   # a row's stored hash != its own content
    GENESIS_MISSING = "GENESIS_MISSING"
    ANCHOR_MISMATCH = "ANCHOR_MISMATCH"   # an off-VM checkpoint disagrees
    DUPLICATE_SEQ = "DUPLICATE_SEQ"


@dataclass(frozen=True, slots=True)
class ChainBreak:
    kind: BreakKind
    at_seq: int
    detail: str

    def __str__(self) -> str:
        return f"{self.kind.value} at seq {self.at_seq}: {self.detail}"


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """What a verification pass found, and what it cost."""

    from_seq: int
    to_seq: int
    events_checked: int
    breaks: tuple[ChainBreak, ...]
    duration_seconds: float
    head_hash: str

    @property
    def intact(self) -> bool:
        return not self.breaks

    @property
    def events_per_second(self) -> float:
        return self.events_checked / self.duration_seconds if self.duration_seconds else 0.0


def link(prev_hash: str, envelope_preimage: bytes) -> str:
    """One link. `prev_hash` is already inside the preimage (see hash_preimage), so
    this is a plain digest — the chaining is in the content, not in the function."""
    return sha256_hex(envelope_preimage)


def verify_chain(
    events: Iterable[AuditEnvelope],
    *,
    require_genesis: bool = False,
    expected_prev_hash: str | None = None,
    deep: bool = True,
) -> VerificationResult:
    """Walk a contiguous run of events and report every break.

    Three independent checks, and all three are needed:

      1. SEQUENCE   — seq increments by exactly one. Catches a DELETED row.
      2. LINKAGE    — prev_hash equals the predecessor's payload_hash. Catches an
                      INSERTED or REORDERED row.
      3. CONTENT    — each row's stored payload_hash equals a hash recomputed from
                      its own content. Catches a MUTATED row.

    Check 3 is the one that matters most and is the one a naive implementation omits.
    Without it, an attacker who edits a payload AND recomputes that row's hash AND
    every subsequent prev_hash produces a chain that passes checks 1 and 2 — but they
    must rewrite every row after it, which is what anchoring (§6.3) makes detectable.
    Omitting check 3 means they need only rewrite ONE row.

    `deep=False` skips check 3 for a fast structural scan. The nightly pass runs deep.
    Verifying a SLICE is first-class: ADR-10 §5 verifies "across the outage window".
    """
    started = time.perf_counter()
    breaks: list[ChainBreak] = []
    ordered = sorted(events, key=lambda e: e.seq)

    if not ordered:
        return VerificationResult(0, 0, 0, (), time.perf_counter() - started, GENESIS_HASH)

    first, last = ordered[0], ordered[-1]

    if require_genesis and first.seq != 0:
        breaks.append(
            ChainBreak(BreakKind.GENESIS_MISSING, first.seq,
                       f"whole-chain verification began at seq {first.seq}, not 0")
        )
    if expected_prev_hash is not None and first.prev_hash != expected_prev_hash:
        breaks.append(
            ChainBreak(BreakKind.FORK, first.seq,
                       f"slice does not attach: prev_hash {first.prev_hash[:12]}... != "
                       f"expected {expected_prev_hash[:12]}...")
        )

    prev: AuditEnvelope | None = None
    for e in ordered:
        if prev is not None:
            if e.seq == prev.seq:
                breaks.append(
                    ChainBreak(BreakKind.DUPLICATE_SEQ, e.seq,
                               f"two events share seq {e.seq}")
                )
            elif e.seq != prev.seq + 1:
                breaks.append(
                    ChainBreak(BreakKind.GAP, e.seq,
                               f"expected seq {prev.seq + 1}, found {e.seq}")
                )
            if e.prev_hash != prev.payload_hash:
                breaks.append(
                    ChainBreak(BreakKind.FORK, e.seq,
                               f"prev_hash {e.prev_hash[:12]}... does not match the "
                               f"preceding payload_hash {prev.payload_hash[:12]}...")
                )
        if deep and not e.verify_self():
            breaks.append(
                ChainBreak(BreakKind.CONTENT_MUTATED, e.seq,
                           f"stored payload_hash {e.payload_hash[:12]}... != recomputed "
                           f"{e.compute_hash()[:12]}... — this row's CONTENT was altered")
            )
        prev = e

    return VerificationResult(
        from_seq=first.seq,
        to_seq=last.seq,
        events_checked=len(ordered),
        breaks=tuple(breaks),
        duration_seconds=time.perf_counter() - started,
        head_hash=last.payload_hash,
    )


def assert_chain_intact(result: VerificationResult) -> None:
    """ADR-10 §5: a broken or forked chain is a HARD STOP. No trading resumes."""
    if not result.intact:
        raise ChainError(
            "AUDIT CHAIN INTEGRITY FAILURE — hard stop. No trading resumes; this is "
            "investigated as a potential integrity incident (ADR-10 §5).\n  "
            + "\n  ".join(str(b) for b in result.breaks)
        )


# =============================================================================
# ANCHORING  (§6.3)
# =============================================================================


@dataclass(frozen=True, slots=True)
class Anchor:
    """A checkpoint published where the database cannot reach it.

    The chain alone proves internal consistency. It does NOT stop someone with write
    access from rewriting the whole tail — recompute every hash from the mutation
    forward and the result is a perfectly consistent chain telling a different story.

    An anchor closes that: once seq N's hash is published off-VM, every event at or
    below N is frozen, because rewriting them changes a hash that already exists
    somewhere the rewriter does not control.
    """

    anchor_seq: int
    anchor_hash: str
    published_at: datetime
    destination: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "anchor_seq": str(self.anchor_seq),
            "anchor_hash": self.anchor_hash,
            "destination": self.destination,
            "published_at": self.published_at.isoformat(),
        }


def verify_against_anchor(
    events: Sequence[AuditEnvelope], anchor: Anchor
) -> ChainBreak | None:
    """Does the live chain still agree with what we published?"""
    for e in events:
        if e.seq == anchor.anchor_seq:
            if e.payload_hash != anchor.anchor_hash:
                return ChainBreak(
                    BreakKind.ANCHOR_MISMATCH, anchor.anchor_seq,
                    f"live hash {e.payload_hash[:12]}... != anchored "
                    f"{anchor.anchor_hash[:12]}... published {anchor.published_at.isoformat()} "
                    f"to {anchor.destination}. History at or below this seq was rewritten."
                )
            return None
    return ChainBreak(
        BreakKind.GAP, anchor.anchor_seq,
        f"anchored seq {anchor.anchor_seq} is absent from the live chain"
    )


#: One anchor per session close. At 252 sessions/year that is 252 anchors/year and
#: 2,520 over ten years — trivial to store and to re-verify, and it bounds any
#: undetectable rewrite to a single session's events.
ANCHOR_CADENCE: Final[str] = "per_session_close"


# =============================================================================
# VERIFICATION COST  (§6.4)
# =============================================================================


def projected_verification_seconds(
    event_count: int, measured_events_per_second: float
) -> float:
    return event_count / measured_events_per_second if measured_events_per_second else float("inf")


def benchmark_verification(
    make_events: Callable[[int], Sequence[AuditEnvelope]], n: int = 20_000
) -> tuple[float, float]:
    """Measure, then project to 10M events. Returns (events_per_second, seconds_at_10M).

    The spec asks for the runtime cost at 10 million events. 10M is roughly 2.6 years
    of production at P0.3's 15,000 events/session — so this is not a hypothetical
    number, it is the cost of the routine annual audit.
    """
    events = make_events(n)
    result = verify_chain(events, deep=True)
    eps = result.events_per_second
    return eps, projected_verification_seconds(10_000_000, eps)


# =============================================================================
# WRITE-BEFORE-ACT  (§7)
# =============================================================================


class ActOutcome(str, Enum):
    COMMITTED = "COMMITTED"
    ABORTED_AUDIT_FAILED = "ABORTED_AUDIT_FAILED"
    UNKNOWN_NEEDS_RECONCILE = "UNKNOWN_NEEDS_RECONCILE"


@dataclass(frozen=True, slots=True)
class IntentRecord:
    """The row written BEFORE the side effect. Rule N12's client-side dedupe key."""

    intent_event_id: UUID
    idempotency_key: str
    event_type: EventType
    occurred_at: datetime


def write_before_act(
    *,
    write_intent: Callable[[], IntentRecord],
    perform_effect: Callable[[IntentRecord], Any],
    write_outcome: Callable[[IntentRecord, Any], None],
) -> tuple[ActOutcome, Any]:
    """[CONST-5]'s protocol, in the exact order it must happen.

        1. WRITE INTENT, durably (synchronous_commit = remote_write).
           If this fails -> the action DOES NOT HAPPEN. Return, do not retry blind.
        2. PERFORM THE EFFECT, carrying the intent's idempotency key.
        3. WRITE OUTCOME.

    THE DANGEROUS WINDOW IS BETWEEN 2 AND 3, and it cannot be eliminated — no
    protocol makes a broker call and a local commit atomic. What it can be is
    RECOVERABLE, which is why step 1 exists and why the key travels into step 2: on
    restart, an intent with no outcome is a question the broker can answer
    (`recover_incomplete_intents`).

    A failure between 1 and 2 is benign: an intent with no effect is a no-op, and the
    reconciler finds no matching broker order.
    """
    try:
        intent = write_intent()
    except Exception as exc:  # noqa: BLE001
        raise ChainError(
            f"audit write failed before the action: {exc}. [CONST-5] — the action "
            f"does not happen."
        ) from exc

    try:
        effect = perform_effect(intent)
    except Exception:
        # We do not know whether the effect landed. This is NOT a failure to retry.
        return ActOutcome.UNKNOWN_NEEDS_RECONCILE, intent

    try:
        write_outcome(intent, effect)
    except Exception:
        # The effect DID land but we failed to record it. Also a reconcile case, and
        # the more dangerous of the two — the world moved and our record did not.
        return ActOutcome.UNKNOWN_NEEDS_RECONCILE, intent

    return ActOutcome.COMMITTED, effect


def recover_incomplete_intents(
    intents: Sequence[IntentRecord],
    outcomes_by_key: Mapping[str, Any],
    ask_broker: Callable[[str], Any | None],
) -> list[tuple[IntentRecord, str]]:
    """Idempotent restart recovery (§7.2).

    For every intent with no recorded outcome, ask the broker using the SAME
    idempotency key. Three answers, three actions:

      broker has it, filled/open  -> RECORD the outcome. Do NOT re-send.
      broker does not have it     -> the effect never landed. Mark ABANDONED.
      broker cannot say           -> UNRECONCILED. Position denies new entries
                                     pool-wide until a human resolves it (ADR-10 §2).

    Idempotent by construction: running this twice produces the same result, because
    it only ever records what the broker already believes.
    """
    actions: list[tuple[IntentRecord, str]] = []
    for intent in intents:
        if intent.idempotency_key in outcomes_by_key:
            continue
        try:
            found = ask_broker(intent.idempotency_key)
        except Exception:
            actions.append((intent, "UNRECONCILED"))
            continue
        if found is None:
            actions.append((intent, "ABANDONED"))
        else:
            actions.append((intent, "RECORD_OUTCOME"))
    return actions


# =============================================================================
# REPLAY  (§10)
# =============================================================================


@dataclass(frozen=True, slots=True)
class FieldDiff:
    field: str
    recorded: str
    replayed: str

    def __str__(self) -> str:
        return f"{self.field}: recorded={self.recorded!r} replayed={self.replayed!r}"


@dataclass(frozen=True, slots=True)
class ReplayResult:
    run_id: UUID
    events_replayed: int
    diffs: tuple[FieldDiff, ...]
    missing_reproducibility: tuple[int, ...]

    @property
    def identical(self) -> bool:
        return not self.diffs and not self.missing_reproducibility


def replay_run(
    events: Sequence[AuditEnvelope],
    run_id: UUID,
    re_derive: Callable[[AuditEnvelope], Mapping[str, Any]],
) -> ReplayResult:
    """Re-derive every reproducible event in a run and diff against what was recorded.

    `re_derive` is supplied by the phase that owns the computation — P2.9 for a risk
    verdict, P2.5 for a score. This module owns the harness, the diff and the verdict,
    because those must be identical no matter which computation is being checked.

    An event whose bundle is missing is reported separately from a mismatch. They mean
    different things: a mismatch is non-determinism, a missing bundle is a gap in what
    we captured, and only the first is a bug in the model.
    """
    diffs: list[FieldDiff] = []
    missing: list[int] = []

    for e in sorted((x for x in events if x.run_id == run_id), key=lambda x: x.seq):
        spec_needs_repro = e.event_type in {
            t for t in EventType if _requires_repro(t)
        }
        if not spec_needs_repro:
            continue
        if e.reproducibility is None:
            missing.append(e.seq)
            continue
        replayed = re_derive(e)
        for key in sorted(set(e.payload) | set(replayed)):
            rec = e.payload.get(key)
            rep = replayed.get(key)
            if rec != rep:
                diffs.append(FieldDiff(f"seq{e.seq}.{key}", str(rec), str(rep)))

    return ReplayResult(
        run_id=run_id,
        events_replayed=sum(1 for x in events if x.run_id == run_id),
        diffs=tuple(diffs),
        missing_reproducibility=tuple(missing),
    )


def _requires_repro(t: EventType) -> bool:
    from .events import EVENT_REGISTRY

    spec = EVENT_REGISTRY.get(t)
    return bool(spec and spec.requires_reproducibility)


# =============================================================================
# REGULATOR EXPORT  (§8.3)
# =============================================================================


def export_for_regulator(
    events: Sequence[AuditEnvelope],
    *,
    include_payload: bool = True,
) -> Iterator[str]:
    """NDJSON, one canonical event per line, in seq order, with the hash fields.

    NDJSON rather than a single JSON array so an export of ten million events streams
    rather than materialises, and so a partial export is still parseable. Each line is
    the CANONICAL form, so a recipient can recompute the chain themselves and verify
    it without trusting our verifier — which is the entire point of handing it over.
    """
    for e in sorted(events, key=lambda x: x.seq):
        row: dict[str, Any] = {
            "seq": str(e.seq),
            "event_id": str(e.event_id),
            "causation_id": "" if e.causation_id is None else str(e.causation_id),
            "run_id": str(e.run_id),
            "event_type": e.event_type.value,
            "event_class": e.event_class.value,
            "schema_version": e.schema_version,
            "canonical_schema": e.canonical_schema,
            "occurred_at": e.occurred_at.isoformat(),
            "recorded_at": e.recorded_at.isoformat(),
            "actor": e.actor,
            "is_paper": e.is_paper,
            "is_backtest": e.is_backtest,
            "input_hash": e.input_hash,
            "prev_hash": e.prev_hash,
            "payload_hash": e.payload_hash,
        }
        if include_payload:
            row["payload"] = e.payload
        yield canonical_bytes(row).decode("utf-8")


__all__ = [
    "ChainError", "BreakKind", "ChainBreak", "VerificationResult",
    "link", "verify_chain", "assert_chain_intact",
    "Anchor", "verify_against_anchor", "ANCHOR_CADENCE",
    "projected_verification_seconds", "benchmark_verification",
    "ActOutcome", "IntentRecord", "write_before_act", "recover_incomplete_intents",
    "FieldDiff", "ReplayResult", "replay_run",
    "export_for_regulator",
]
