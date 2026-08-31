"""SPEC-P1.4-AUDIT verification, including the deliverable's required self-check:
ONE RUNNABLE PROOF THAT A MUTATED ROW FAILS VERIFICATION.

Run directly:  python tests/verify_p14_audit.py
"""
import sys
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path("D:/GitHub/AI-Trading-Agent")
sys.path.insert(0, str(ROOT / "src"))
from audit import chain as K  # noqa: E402
from audit import events as V  # noqa: E402

PASS, FAIL = [], []
U0 = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
RUN = uuid4()


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


# =============================================================================
# chain builder — the same primitive the writer uses
# =============================================================================
def build_chain(n, run_id=RUN, start_seq=0, prev=V.GENESIS_HASH):
    """Build a valid chain of DATA_RECEIVED events (EVALUATION class, no bundle)."""
    out, cause = [], None
    for i in range(n):
        seq = start_seq + i
        eid = V.uuid7()
        payload = {
            "source": "massive", "data_type": "bar_daily", "row_count": str(1500 + i),
            "as_of": U0.isoformat(), "retrieved_at": U0.isoformat(),
            "input_hash": "a" * 64,
        }
        draft = V.AuditEnvelope(
            event_id=eid, seq=seq, causation_id=cause, run_id=run_id,
            event_type=V.EventType.DATA_RECEIVED, event_class=V.EventClass.EVALUATION,
            occurred_at=U0 + timedelta(seconds=i), recorded_at=U0 + timedelta(seconds=i),
            actor="P2.1_INGEST", is_paper=False, is_backtest=False,
            input_hash="a" * 64, payload=payload,
            prev_hash=prev, payload_hash="0" * 64,
        )
        real = draft.model_copy(update={"payload_hash": draft.compute_hash()})
        out.append(real)
        prev, cause = real.payload_hash, eid
    return out


# =============================================================================
# ***  THE REQUIRED SELF-CHECK  ***
# =============================================================================
def t_AAA_mutated_row_fails_verification():
    """THE DELIVERABLE'S REQUIRED PROOF.

    Build a valid chain, verify it, mutate ONE FIELD of ONE ROW, verify again, and
    assert the mutation is caught. Three mutation shapes, because they are caught by
    three different checks and a verifier that only implements one of them looks fine
    until the day it matters.
    """
    events = build_chain(12)
    clean = K.verify_chain(events, require_genesis=True, deep=True)
    assert clean.intact, f"a freshly built chain must verify: {clean.breaks}"

    # ---- 1. CONTENT MUTATION: edit a payload, leave every hash alone -------
    tampered = list(events)
    victim = tampered[5]
    tampered[5] = victim.model_copy(
        update={"payload": {**victim.payload, "row_count": "999999"}}
    )
    r = K.verify_chain(tampered, require_genesis=True, deep=True)
    assert not r.intact, "a mutated payload MUST fail verification"
    kinds = {b.kind for b in r.breaks}
    assert K.BreakKind.CONTENT_MUTATED in kinds, kinds
    assert any(b.at_seq == 5 for b in r.breaks), "the break must name the mutated seq"
    raises(K.ChainError, lambda: K.assert_chain_intact(r))

    # ---- 2. RE-HASHED MUTATION: edit the payload AND fix that row's hash ---
    # A cleverer attacker. Caught by LINKAGE, because seq 6's prev_hash still
    # points at the old digest.
    v2 = events[5]
    fixed = v2.model_copy(update={"payload": {**v2.payload, "row_count": "999999"}})
    fixed = fixed.model_copy(update={"payload_hash": fixed.compute_hash()})
    t2 = list(events)
    t2[5] = fixed
    r2 = K.verify_chain(t2, require_genesis=True, deep=True)
    assert not r2.intact, "a re-hashed mutation MUST still fail via linkage"
    assert K.BreakKind.FORK in {b.kind for b in r2.breaks}, r2.breaks

    # ---- 3. DELETION: remove a row entirely --------------------------------
    t3 = [e for e in events if e.seq != 7]
    r3 = K.verify_chain(t3, require_genesis=True, deep=True)
    assert not r3.intact, "a deleted row MUST fail verification"
    assert K.BreakKind.GAP in {b.kind for b in r3.breaks}, r3.breaks

    print("    [self-check] mutated / re-hashed / deleted rows all caught:")
    for label, res in (("mutated", r), ("re-hashed", r2), ("deleted", r3)):
        print(f"      {label:10s} -> {res.breaks[0]}")


def t_AAB_full_tail_rewrite_is_caught_only_by_the_anchor():
    """The attack the chain ALONE cannot catch, and the anchor can.

    Rewrite a row and recompute every hash after it. The result is internally
    perfect — checks 1, 2 and 3 all pass. Only a hash published somewhere the
    rewriter does not control reveals it.
    """
    events = build_chain(10)
    anchor = K.Anchor(anchor_seq=8, anchor_hash=events[8].payload_hash,
                      published_at=U0, destination="s3://offvm-audit-anchors/")

    # rewrite seq 4, then re-chain 5..9 so everything is self-consistent
    rebuilt = list(events[:4])
    v = events[4]
    forged = v.model_copy(update={"payload": {**v.payload, "row_count": "1"},
                                  "prev_hash": rebuilt[-1].payload_hash})
    forged = forged.model_copy(update={"payload_hash": forged.compute_hash()})
    rebuilt.append(forged)
    for e in events[5:]:
        nxt = e.model_copy(update={"prev_hash": rebuilt[-1].payload_hash})
        nxt = nxt.model_copy(update={"payload_hash": nxt.compute_hash()})
        rebuilt.append(nxt)

    internal = K.verify_chain(rebuilt, require_genesis=True, deep=True)
    assert internal.intact, "a fully rewritten tail is internally consistent — that is the point"

    breach = K.verify_against_anchor(rebuilt, anchor)
    assert breach is not None, "the anchor MUST catch a full-tail rewrite"
    assert breach.kind is K.BreakKind.ANCHOR_MISMATCH
    assert K.verify_against_anchor(events, anchor) is None, "the honest chain must still match"
    print(f"    [self-check] full-tail rewrite passed internal verification, "
          f"caught by anchor: {breach.detail[:60]}...")


# =============================================================================
# UUIDv7
# =============================================================================
def t_uuid7_is_version_7_and_time_ordered():
    ids = [V.uuid7() for _ in range(2000)]
    assert all(u.version == 7 for u in ids)
    assert all(u.variant == "specified in RFC 4122" for u in ids[:5])
    assert [str(u) for u in ids] == sorted(str(u) for u in ids), "must sort in creation order"
    assert len(set(ids)) == len(ids), "no collisions"


def t_uuid7_monotonic_across_threads():
    out, lock = [], threading.Lock()

    def w():
        got = [V.uuid7() for _ in range(500)]
        with lock:
            out.extend(got)

    ts = [threading.Thread(target=w) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(set(out)) == len(out), "concurrent minting must not collide"


def t_uuid7_timestamp_recoverable():
    u = V.uuid7(now_ms=1_800_000_000_000)
    assert V.uuid7_timestamp_ms(u) == 1_800_000_000_000
    raises(ValueError, lambda: V.uuid7_timestamp_ms(uuid4()))


# =============================================================================
# canonical serialisation (closes Q-P1.2-1)
# =============================================================================
def t_canonical_is_key_order_independent():
    a = V.canonical_json({"b": "2", "a": "1", "c": {"z": "9", "y": "8"}})
    b = V.canonical_json({"c": {"y": "8", "z": "9"}, "a": "1", "b": "2"})
    assert a == b == '{"a":"1","b":"2","c":{"y":"8","z":"9"}}'


def t_canonical_rejects_json_numbers():
    """The restriction that removes JCS's hardest part — and the float-money bug."""
    for bad in ({"v": 1}, {"v": 1.5}, {"v": D("0.05")}, {"a": [{"b": 2}]}):
        raises(V.NonCanonicalPayloadError, lambda b=bad: V.canonical_json(b))
    # strings and booleans are fine
    V.canonical_json({"v": "0.05", "ok": True, "n": None, "l": ["a", "b"]})


def t_canonical_is_stable_and_utf8():
    assert V.canonical_bytes({"k": "café"}) == '{"k":"café"}'.encode("utf-8")
    assert V.canonical_json({"k": "x"}) == V.canonical_json({"k": "x"})


# =============================================================================
# taxonomy
# =============================================================================
def t_taxonomy_covers_every_required_event():
    """The prompt's minimum coverage list, checked name by name."""
    required = [
        "DATA_RECEIVED", "DATA_REJECTED", "CANDIDATE_SCREENED", "SCORE_COMPUTED",
        "GATE_OPENED", "GATE_CLOSED", "LLM_CALLED", "LLM_OUTPUT_ACCEPTED",
        "LLM_OUTPUT_REJECTED", "DECISION_MADE", "RISK_EVALUATED", "ORDER_INTENT",
        "ORDER_SENT", "ORDER_ACKED", "FILL_RECEIVED", "POSITION_OPENED",
        "POSITION_CLOSED", "LIMIT_BREACHED", "KILL_SWITCH_ARMED",
        "KILL_SWITCH_TRIPPED", "KILL_SWITCH_RESET", "CONFIG_CHANGED", "MODEL_DEPLOYED",
    ]
    have = {e.value for e in V.EventType}
    assert set(required) <= have, f"missing: {sorted(set(required) - have)}"


def t_every_event_type_has_a_complete_spec():
    for t in V.EventType:
        s = V.EVENT_REGISTRY.get(t)
        assert s is not None, f"{t.value} has no registry entry"
        assert s.producer and s.trigger and s.required_payload_keys, t.value
        assert len(s.trigger) >= 10, t.value


def t_effectful_events_are_the_ones_const5_governs():
    eff = V.EFFECTFUL_EVENT_TYPES
    for t in (V.EventType.ORDER_INTENT, V.EventType.ORDER_SENT, V.EventType.FILL_RECEIVED,
              V.EventType.DECISION_MADE, V.EventType.KILL_SWITCH_TRIPPED,
              V.EventType.CONFIG_CHANGED, V.EventType.MODEL_DEPLOYED):
        assert t in eff, t.value
    # a pure observation is not effectful
    assert V.EventType.CANDIDATE_SCREENED not in eff
    assert V.EventType.GATE_CLOSED not in eff


def t_model_and_llm_events_require_reproducibility():
    for t in (V.EventType.SCORE_COMPUTED, V.EventType.LLM_CALLED,
              V.EventType.DECISION_MADE, V.EventType.RISK_EVALUATED):
        assert t in V.REPRODUCIBLE_EVENT_TYPES, t.value


def t_registry_class_is_authoritative():
    """Writing an event under the wrong class must fail — RULE-B4 keys durability on it."""
    raises(Exception, lambda: V.AuditEnvelope(
        event_id=V.uuid7(), seq=0, run_id=RUN, event_type=V.EventType.DECISION_MADE,
        event_class=V.EventClass.EVALUATION,      # registry says ACTION
        occurred_at=U0, recorded_at=U0, actor="x", is_paper=False, is_backtest=False,
        input_hash="a" * 64, payload={}, prev_hash=V.GENESIS_HASH, payload_hash="b" * 64))


def t_missing_required_payload_key_is_rejected():
    raises(Exception, lambda: V.AuditEnvelope(
        event_id=V.uuid7(), seq=0, run_id=RUN, event_type=V.EventType.DATA_RECEIVED,
        event_class=V.EventClass.EVALUATION, occurred_at=U0, recorded_at=U0,
        actor="x", is_paper=False, is_backtest=False, input_hash="a" * 64,
        payload={"source": "massive"},            # missing the rest
        prev_hash=V.GENESIS_HASH, payload_hash="b" * 64))


def t_reproducible_event_without_bundle_is_rejected():
    raises(Exception, lambda: V.AuditEnvelope(
        event_id=V.uuid7(), seq=0, run_id=RUN, event_type=V.EventType.SCORE_COMPUTED,
        event_class=V.EventClass.EVALUATION, occurred_at=U0, recorded_at=U0,
        actor="x", is_paper=False, is_backtest=False, input_hash="a" * 64,
        payload={"instrument_id": "i", "kind": "COMPOSITE", "value": "0.7",
                 "model_id": "m", "model_version": "1", "feature_vector_hash": "c" * 64},
        prev_hash=V.GENESIS_HASH, payload_hash="b" * 64))


def t_promotion_to_action_class():
    assert V.promote_to_action(V.EventClass.EVALUATION, True) is V.EventClass.ACTION
    assert V.promote_to_action(V.EventClass.EVALUATION, False) is V.EventClass.EVALUATION
    assert V.promote_to_action(V.EventClass.ACTION, True) is V.EventClass.ACTION


# =============================================================================
# envelope invariants
# =============================================================================
def t_naive_timestamp_rejected():
    raises(Exception, lambda: V.AuditEnvelope(
        event_id=V.uuid7(), seq=0, run_id=RUN, event_type=V.EventType.RUN_FINISHED,
        event_class=V.EventClass.SYSTEM, occurred_at=datetime(2026, 1, 1),
        recorded_at=U0, actor="x", is_paper=False, is_backtest=False,
        input_hash="a" * 64, payload={"run_id": "r", "outcome": "OK",
                                      "duration_seconds": "1"},
        prev_hash=V.GENESIS_HASH, payload_hash="b" * 64))


def t_paper_xor_backtest():
    raises(Exception, lambda: build_chain(1)[0].model_copy(
        update={"is_paper": True, "is_backtest": True}).model_validate(
            build_chain(1)[0].model_dump() | {"is_paper": True, "is_backtest": True}))


def t_genesis_rules():
    e = build_chain(1)[0]
    assert e.seq == 0 and e.prev_hash == V.GENESIS_HASH
    raises(Exception, lambda: V.AuditEnvelope.model_validate(
        e.model_dump() | {"seq": 3}))          # seq>0 with the genesis hash


def t_hash_preimage_order_is_explicit_not_field_order():
    """The preimage must not follow the model's field order — reordering a Pydantic
    model would then silently invalidate every historical hash."""
    e = build_chain(1)[0]
    pre = e.hash_preimage().decode()
    # canonical_json sorts keys, so the ORDER in the dict literal is irrelevant; what
    # matters is the exact KEY SET, which is pinned.
    import json
    keys = set(json.loads(pre))
    assert keys == {
        "canonical_schema", "schema_version", "seq", "prev_hash", "event_id",
        "causation_id", "run_id", "event_type", "event_class", "occurred_at",
        "actor", "is_paper", "is_backtest", "input_hash", "payload",
    }, sorted(keys)
    # recorded_at is deliberately NOT hashed: it is when we wrote it down, not what
    # happened, and a replayed write would otherwise never reproduce the hash.
    assert "recorded_at" not in keys


def t_causation_chain_is_walkable():
    events = build_chain(6)
    by_id = {e.event_id: e for e in events}
    cur, depth = events[-1], 0
    while cur.causation_id is not None:
        cur = by_id[cur.causation_id]
        depth += 1
    assert depth == 5 and cur.seq == 0


def t_event_cannot_cause_itself():
    e = build_chain(1)[0]
    raises(Exception, lambda: V.AuditEnvelope.model_validate(
        e.model_dump() | {"causation_id": e.event_id}))


# =============================================================================
# verification behaviour
# =============================================================================
def t_slice_verification_is_first_class():
    events = build_chain(20)
    r = K.verify_chain(events[5:12], expected_prev_hash=events[4].payload_hash)
    assert r.intact, r.breaks
    bad = K.verify_chain(events[5:12], expected_prev_hash="f" * 64)
    assert not bad.intact and K.BreakKind.FORK in {b.kind for b in bad.breaks}


def t_duplicate_seq_detected():
    events = build_chain(5)
    r = K.verify_chain([*events, events[2]])
    assert K.BreakKind.DUPLICATE_SEQ in {b.kind for b in r.breaks}


def t_shallow_scan_misses_content_mutation_by_design():
    events = build_chain(8)
    t = list(events)
    t[3] = t[3].model_copy(update={"payload": {**t[3].payload, "row_count": "0"}})
    assert not K.verify_chain(t, deep=True).intact
    assert K.verify_chain(t, deep=False).intact, \
        "deep=False is documented as structural-only; if this ever fails, the doc is wrong"


def t_empty_chain_is_vacuously_intact():
    assert K.verify_chain([]).intact


# =============================================================================
# verification cost at 10M events (§6.4)
# =============================================================================
def t_verification_cost_at_10m_events():
    eps, secs = K.benchmark_verification(build_chain, n=8000)
    print(f"    [cost] deep verification: {eps:,.0f} events/s -> "
          f"10M events in {secs/60:.1f} min ({secs:.0f} s)")
    assert eps > 1000, f"only {eps:.0f} events/s — too slow to audit annually"
    assert secs < 6 * 3600, f"10M events would take {secs/3600:.1f} h"


# =============================================================================
# write-before-act and recovery (§7)
# =============================================================================
def _intent():
    return K.IntentRecord(intent_event_id=V.uuid7(), idempotency_key="cli-1",
                          event_type=V.EventType.ORDER_INTENT, occurred_at=U0)


def t_audit_failure_means_the_action_does_not_happen():
    effects = []

    def boom():
        raise RuntimeError("disk full")

    raises(K.ChainError, lambda: K.write_before_act(
        write_intent=boom,
        perform_effect=lambda i: effects.append("SENT"),
        write_outcome=lambda i, e: None))
    assert effects == [], "[CONST-5]: no audit write means NO SIDE EFFECT"


def t_death_between_effect_and_outcome_is_reconcilable_not_lost():
    outcome, intent = K.write_before_act(
        write_intent=_intent,
        perform_effect=lambda i: "broker-ack",
        write_outcome=lambda i, e: (_ for _ in ()).throw(RuntimeError("process died")))
    assert outcome is K.ActOutcome.UNKNOWN_NEEDS_RECONCILE
    assert intent.idempotency_key == "cli-1"


def t_recovery_is_idempotent_and_covers_all_three_answers():
    intents = [K.IntentRecord(V.uuid7(), f"cli-{i}", V.EventType.ORDER_INTENT, U0)
               for i in range(3)]
    outcomes = {"cli-0": "recorded"}          # already complete

    def broker(key):
        if key == "cli-1":
            return {"status": "filled"}       # it DID land
        if key == "cli-2":
            return None                       # it never landed
        return None

    a1 = K.recover_incomplete_intents(intents, outcomes, broker)
    assert [k for _, k in a1] == ["RECORD_OUTCOME", "ABANDONED"], a1
    a2 = K.recover_incomplete_intents(intents, outcomes, broker)
    assert [k for _, k in a1] == [k for _, k in a2], "recovery must be idempotent"

    def flaky(key):
        raise TimeoutError("broker unreachable")

    a3 = K.recover_incomplete_intents(intents, outcomes, flaky)
    assert all(k == "UNRECONCILED" for _, k in a3), "an unanswerable broker is fail-closed"


def t_happy_path_commits():
    outcome, effect = K.write_before_act(
        write_intent=_intent, perform_effect=lambda i: "ack",
        write_outcome=lambda i, e: None)
    assert outcome is K.ActOutcome.COMMITTED and effect == "ack"


# =============================================================================
# replay (§10)
# =============================================================================
def _score_event(seq, prev, value, cause=None):
    bundle = V.ReproducibilityBundle(
        code_version="abc1234", runtime=V.ReproducibilityBundle.capture_runtime(),
        library_versions={"pydantic": "2.13.4"}, config_hash="c" * 64,
        policy_version="0.1.0", model_id="scorer", model_version="3",
        model_artifact_sha256="d" * 64, input_snapshot_refs=("bars:2026-08-26",),
        input_hash="e" * 64, market_asof=U0, knowledge_asof=U0,
        random_seeds={"numpy": "42"})
    payload = {"instrument_id": "AAPL", "kind": "COMPOSITE", "value": value,
               "model_id": "scorer", "model_version": "3", "feature_vector_hash": "f" * 64}
    d = V.AuditEnvelope(
        event_id=V.uuid7(), seq=seq, causation_id=cause, run_id=RUN,
        event_type=V.EventType.SCORE_COMPUTED, event_class=V.EventClass.EVALUATION,
        occurred_at=U0, recorded_at=U0, actor="P2.5_SCORER", is_paper=False,
        is_backtest=False, input_hash="e" * 64, payload=payload,
        reproducibility=bundle, prev_hash=prev, payload_hash="0" * 64)
    return d.model_copy(update={"payload_hash": d.compute_hash()})


def t_replay_identical_run_has_no_diff():
    ev = [_score_event(0, V.GENESIS_HASH, "0.712")]
    r = K.replay_run(ev, RUN, re_derive=lambda e: dict(e.payload))
    assert r.identical, (r.diffs, r.missing_reproducibility)


def t_replay_detects_non_determinism():
    ev = [_score_event(0, V.GENESIS_HASH, "0.712")]
    r = K.replay_run(ev, RUN, re_derive=lambda e: dict(e.payload) | {"value": "0.713"})
    assert not r.identical
    assert len(r.diffs) == 1 and "value" in r.diffs[0].field
    assert "0.712" in r.diffs[0].recorded and "0.713" in r.diffs[0].replayed


def t_replay_reports_missing_bundle_separately_from_a_mismatch():
    """They mean different things: a mismatch is non-determinism, a missing bundle is
    a gap in what we captured. Only the first is a model bug."""
    e = _score_event(0, V.GENESIS_HASH, "0.712")
    stripped = V.AuditEnvelope.model_construct(
        **(e.model_dump() | {"reproducibility": None}))
    r = K.replay_run([stripped], RUN, re_derive=lambda x: dict(x.payload))
    assert r.missing_reproducibility == (0,) and not r.diffs


def t_reproducibility_bundle_requires_llm_fields_together():
    base = dict(code_version="abc1234", runtime={}, library_versions={},
                config_hash="c" * 64, policy_version="0.1.0", model_id="m",
                model_version="1", input_snapshot_refs=(), input_hash="e" * 64,
                market_asof=U0, knowledge_asof=U0)
    raises(Exception, lambda: V.ReproducibilityBundle(**base, llm_prompt_hash="x" * 64))
    V.ReproducibilityBundle(**base, llm_prompt_hash="x" * 64,
                            llm_response_hash="y" * 64,
                            llm_sampling_parameters={"temperature": "0.0"})


# =============================================================================
# regulator export (§8.3)
# =============================================================================
def t_export_is_ndjson_and_independently_verifiable():
    import json
    events = build_chain(6)
    lines = list(K.export_for_regulator(events))
    assert len(lines) == 6
    rows = [json.loads(x) for x in lines]
    assert [int(r["seq"]) for r in rows] == list(range(6)), "must export in seq order"
    # A recipient can re-chain it without trusting our verifier.
    prev = V.GENESIS_HASH
    for r in rows:
        assert r["prev_hash"] == prev
        prev = r["payload_hash"]
    assert all("payload" in r for r in rows)
    assert all("payload" not in json.loads(x)
               for x in K.export_for_regulator(events, include_payload=False))


# =============================================================================
if __name__ == "__main__" or True:
    for _n, _f in sorted((n, f) for n, f in list(globals().items()) if n.startswith("t_")):
        check(_n, _f)
    print(f"PASSED {len(PASS)}")
    for f in FAIL:
        print("FAILED", f)
    sys.exit(1 if FAIL else 0)
