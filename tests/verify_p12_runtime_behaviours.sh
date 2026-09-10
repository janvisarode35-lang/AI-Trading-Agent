#!/usr/bin/env bash
# X5 GAP AUDIT condition 7 / open question Q-P1.2-6 — and Q-P1.2-3 alongside it.
#
# Q-P1.2-6 asked: "Does migration 0001 execute, and do its runtime behaviours hold?"
# B-1 closed the first half. This closes the second: the five assertions the question
# names, each run against the real pinned database rather than argued from the DDL.
#
#   7.1  append-only enforcement in normal mode; the replica-role bypass (Finding A,
#        pinned as known-open); and the CONTENT check that detects it (Finding B)
#   7.2  EXCLUDE rejects an overlapping symbol mapping
#   7.3  a DENY verdict cannot be inserted into `decision`
#   7.4  backtest_ro gets permission denied on a base table
#   7.5  the overfill trigger fires on a DEFERRED commit, not on the INSERT
#   7.6  (Q-P1.2-3) compression does not disarm the deny-mutation triggers, and the
#        deny triggers do not block the compression job
#   7.7  (Finding C) the hash preimage is timezone-independent
#   7.8  (X2 BLOCKER-1) the hash preimage is DateStyle-independent — the other half of
#        Finding C, which pinning TimeZone alone did not close
#
# 7.1 and 7.5 are the two that could not be established by reading. session_replication_role
# = 'replica' is exactly how a replication tool or a careless superuser bypasses ordinary
# triggers; ENABLE ALWAYS is the only thing that survives it. And a DEFERRABLE constraint
# trigger that fired on INSERT rather than at COMMIT would reject the legitimate
# intermediate state of a partial fill.
#
# No bare `assert` anywhere (finding B-5): every check raises or records explicitly.
set -Eeuo pipefail
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SERVICE="timescaledb"
USER="${POSTGRES_USER:-postgres}"
DB="${APP_DB:-trading}"
PASS=0
FAIL=0
ok()  { printf '  PASS  %s\n' "$*"; PASS=$((PASS+1)); }
bad() { printf '  FAIL  %s\n' "$*"; FAIL=$((FAIL+1)); }

# Run SQL, return output. Never let a failing psql kill the script - we test failures.
# Strips psql's command tags ("INSERT 0 1") so a RETURNING value comes back clean.
sql()  { docker compose exec -T "$SERVICE" psql -U "$USER" -d "$DB" -tA -c "$1" 2>&1 \
           | tr -d '\r' | grep -vE '^(INSERT [0-9]+ [0-9]+|UPDATE [0-9]+|DELETE [0-9]+|SELECT [0-9]+|SET|RESET|BEGIN|COMMIT|ROLLBACK)$' || true; }
sqlf() { docker compose exec -T "$SERVICE" psql -v ON_ERROR_STOP=1 -U "$USER" -d "$DB" -tA 2>&1 | tr -d '\r'; }

# expect_fail <label> <sqltext> <substring that must appear in the error>
expect_fail() {
    local label="$1" stmt="$2" want="$3" out
    out="$(docker compose exec -T "$SERVICE" psql -v ON_ERROR_STOP=1 -U "$USER" -d "$DB" -tA -c "$stmt" 2>&1 | tr -d '\r' || true)"
    if printf '%s' "$out" | grep -qiE "$want"; then
        ok "$label"
    else
        bad "$label — expected an error matching /$want/, got: $(printf '%s' "$out" | head -2 | tr '\n' ' ')"
    fi
}

[ "$(docker compose ps --format '{{.Health}}' "$SERVICE" 2>/dev/null)" = "healthy" ] \
    || { echo "service '$SERVICE' not healthy; run: docker compose up -d --wait"; exit 2; }

# --------------------------------------------------------------------------------------
# Fixture. Everything hangs off one instrument and one order.
# --------------------------------------------------------------------------------------
# Every run uses a fresh symbol. The EXCLUDE constraint under test is exactly what makes a
# fixed symbol non-rerunnable: a previous run's mapping would block this run's fixture. That
# is the B-3 lesson applied to this harness - a test against a persistent database must
# isolate itself.
INST=$(sql "SELECT gen_random_uuid();")
ORD=$(sql  "SELECT gen_random_uuid();")
DEC=$(sql  "SELECT gen_random_uuid();")
VER=$(sql  "SELECT gen_random_uuid();")
VOK=$(sql  "SELECT gen_random_uuid();")
SYM="RT$(sql "SELECT upper(substr(replace(gen_random_uuid()::text,'-',''),1,6));")"

sqlf <<SQL
INSERT INTO trading.instrument (instrument_id, market, exchange, instrument_type, status,
                                currency, qty_increment, knowledge_from)
VALUES ('$INST','US','NASDAQ','COMMON_STOCK','ACTIVE','USD',1,now());

INSERT INTO trading.symbol_mapping (instrument_id, market, exchange, symbol, valid_from, knowledge_from)
VALUES ('$INST','US','NASDAQ','$SYM', DATE '2026-01-01', now());

-- order_intent.decision_id references decision, and decision only accepts an ALLOW
-- verdict, so the chain must be built verdict -> decision -> order.
INSERT INTO trading.risk_evaluation (verdict_id, request_id, instrument_id, pool_id, decision,
       limits_evaluated, nav_snapshot_id, evaluated_at, audit_event_id)
VALUES ('$VOK',gen_random_uuid(),'$INST','US_POOL','ALLOW', ARRAY['EXP-001'],
        gen_random_uuid(), now(), gen_random_uuid());

INSERT INTO trading.decision (decision_id, instrument_id, market, pool_id, trading_date,
       action, target_quantity, strategy_version, model_id, risk_verdict_id, risk_decision,
       audit_event_id, decided_at)
VALUES ('$DEC','$INST','US','US_POOL', CURRENT_DATE,'ENTER',100,'v1','m1','$VOK','ALLOW',
        gen_random_uuid(), now());

INSERT INTO trading.order_intent (order_id, decision_id, account_id, instrument_id, market,
       pool_id, side, order_type, time_in_force, quantity, limit_price, state, client_order_id,
       broker_id, strategy_version, strategy_id, model_id, audit_event_id, placed_at)
VALUES ('$ORD','$DEC',gen_random_uuid(),'$INST','US','US_POOL','BUY','LIMIT','DAY',
        100, 10.00, 'NEW','COID-RT-1','alpaca','v1','S1','m1',gen_random_uuid(), now());
SQL

echo "== 7.1  append-only enforcement, and the replica-role bypass (Finding A) =="
# Baseline: rows before this point may carry deliberate tampering from an earlier run, so
# every assertion below is scoped to seq >= BASE.
BASE=$(sql "SELECT coalesce(max(seq),-1)+1 FROM trading.audit_log;")
SEQ=$(sql "INSERT INTO trading.audit_log (event_type,event_class,occurred_at,recorded_at,actor,run_id,is_paper,is_backtest,payload)
           VALUES ('RT_PROBE','SYSTEM',now(),now(),'rt',gen_random_uuid(),true,false,'{}'::jsonb) RETURNING seq;")
# Six further rows, untampered, in the SAME verification range as the probe. 7.1e needs
# them: a false-positive check whose scan range holds nothing but the row it excludes is
# vacuous (X2 finding N-1). These are what the CONTENT check must NOT flag.
sql "INSERT INTO trading.audit_log (event_type,event_class,occurred_at,recorded_at,actor,run_id,is_paper,is_backtest,payload)
     SELECT 'RT_CLEAN','SYSTEM',now(),now(),'rt',gen_random_uuid(),true,false,
            jsonb_build_object('i',g) FROM generate_series(1,6) g;" >/dev/null
CLEAN_N=$(sql "SELECT count(*)::text FROM trading.audit_log WHERE seq >= $BASE AND seq <> $SEQ;")

# 7.1a — in NORMAL mode the deny triggers work. This is the property that must never regress.
expect_fail "normal role: audit_log UPDATE rejected" \
    "UPDATE trading.audit_log SET actor='x' WHERE seq=$SEQ;" \
    "append-only|not permitted"
expect_fail "normal role: audit_log DELETE rejected" \
    "DELETE FROM trading.audit_log WHERE seq=$SEQ;" \
    "append-only|not permitted"

# 7.1b — X5 Finding A, pinned as KNOWN-OPEN rather than asserted away. audit_log is a
# hypertable; DML routes to chunks; chunk triggers are ORIGIN; 'replica' skips ORIGIN.
# TimescaleDB refuses to promote them ("operation not supported on chunk tables"), so
# there is no in-database fix. This check asserts the bypass STILL EXISTS. If it ever
# starts failing, prevention has been fixed — update Finding A and this test together.
BYP=$(sql "SET session_replication_role='replica';
           UPDATE trading.audit_log SET actor='tampered_by_replica' WHERE seq=$SEQ;
           RESET session_replication_role;
           SELECT actor FROM trading.audit_log WHERE seq=$SEQ;")
if [ "$BYP" = "tampered_by_replica" ]; then
    ok "Finding A CONFIRMED STILL OPEN: replica role bypasses the deny triggers"
else
    bad "replica bypass no longer reproduces (actor='$BYP') — prevention may be fixed; update Finding A"
fi

# 7.1c — X5 Finding B, THE REGRESSION TEST. Prevention failed above; detection must not.
# verify_audit_chain() must recompute payload_hash and report the mutated row. Before the
# fix this returned zero rows for exactly this tamper.
DET=$(sql "SELECT count(*)::text FROM trading.verify_audit_chain($BASE)
           WHERE broken_at=$SEQ AND reason LIKE 'content mutated%';")
if [ "$DET" = "1" ]; then
    ok "Finding B FIXED: CONTENT check detects the in-place edit prevention missed"
else
    bad "content mutation NOT detected (matching rows=$DET) — the CONTENT check is missing or bypassed"
fi

# 7.1d — guard the mechanism itself, so removing the re-hash fails loudly even if some
# future refactor happens to leave the row undetectably clean.
HASHES=$(sql "SELECT CASE WHEN pg_get_functiondef('trading.verify_audit_chain(bigint)'::regprocedure)
                          ~* 'digest' THEN 'yes' ELSE 'no' END;")
if [ "$HASHES" = "yes" ]; then ok "verify_audit_chain still recomputes a digest"
else bad "verify_audit_chain no longer calls digest() — the CONTENT check was removed"; fi

# 7.1e — PRECISION: the CONTENT check must name the tampered row and ONLY the tampered row.
#
# X2 finding N-1. The previous form of this check asked for
#     count(*) FROM verify_audit_chain(BASE) WHERE broken_at <> SEQ
# and called 0 a pass. But BASE = max(seq)+1 and the probe insert then TAKES that seq, so
# BASE == SEQ always, the scan range held exactly one row, and `broken_at <> SEQ` excluded
# it. The query returned 0 over an empty set — it passed with the CONTENT check entirely
# deleted from the verifier, which is how BLOCKER-1's false positives went unnoticed.
#
# This form asserts the exact identity of the reported set against $CLEAN_N untampered rows
# sharing the range. It has teeth in BOTH directions:
#   * delete the CONTENT check  -> set is empty      -> FAIL (a miss)
#   * make the preimage drift   -> set gains clean rows -> FAIL (a false positive)
# The second direction is the one that catches a GUC left unpinned, because an unpinned
# render mismatches every row it touches, not just the tampered one.
MUT=$(sql "SELECT coalesce(string_agg(DISTINCT broken_at::text, ',' ORDER BY broken_at::text), 'NONE')
             FROM trading.verify_audit_chain($BASE) WHERE reason LIKE 'content mutated%';")
if [ "$MUT" = "$SEQ" ]; then
    ok "CONTENT check names EXACTLY the tampered row (seq $SEQ) against $CLEAN_N untampered rows in range"
elif [ "$MUT" = "NONE" ]; then
    bad "CONTENT check reported NOTHING over a range containing a known tamper at seq $SEQ — check removed or bypassed"
else
    bad "CONTENT check reported {$MUT}, expected exactly {$SEQ} — false positive on an untampered row ($CLEAN_N clean rows in range)"
fi

# ---------------------------------------------------------------------------------------
# 7.1f  KEY-SET COVERAGE — X2 BLOCKER-A (third review, 2026-09-06)
#
# 7.1c, 7.1d and 7.1e prove the CONTENT check EXISTS, recomputes a digest, and names the
# tampered row and only that row. None of them proves it covers the right COLUMNS: all
# three drive it through a single `actor` mutation, and `actor` was already in the preimage
# before the v0.5 correction. The third X2 measured the consequence — with `event_id`,
# `is_paper` and `is_backtest` deleted from the preimage in BOTH audit_chain_assign() and
# verify_audit_chain(), this suite stayed at 28/28, all six Python suites stayed green, the
# migration applied clean, and an UPDATE flipping `is_paper` on an ACTION row reported
# 0 breaks. The correction that closed the previous BLOCKER-1 could silently revert.
#
# ONE PROBE PER COLUMN, each on its own row and its own scan range. A shared row would let
# any one still-covered column mask the loss of another: a single UPDATE touching all three
# is detected as long as ONE of them is hashed, which is exactly the discrimination this
# section has to provide.
#
# The sabotage these must survive is removal from BOTH sides. Removing a field from the
# verifier alone already fails 7.1e — writer/verifier divergence makes every clean row
# report — so that direction proves nothing about the FIELD, only that the two functions
# agree. Removed from both, the preimage is internally consistent and only a probe that
# mutates that specific column can see the loss.
#
# Each probe also carries two untampered rows in its range, so it has teeth in the
# false-positive direction too (the N-1 lesson that made 7.1e non-vacuous).
PROBE_SEQ=""
PROBE_BASE=""
audit_field_probe() {
    local label="$1" mutation="$2" readback="$3" expect="$4" want="$5"
    local pbase pseq clean got mut
    pbase=$(sql "SELECT coalesce(max(seq),-1)+1 FROM trading.audit_log;")
    pseq=$(sql "INSERT INTO trading.audit_log (event_type,event_class,occurred_at,recorded_at,
                        actor,run_id,is_paper,is_backtest,payload)
                VALUES ('RT_KEYSET','ACTION',now(),now(),'keyset',gen_random_uuid(),
                        true,false,'{\"probe\":\"1\"}'::jsonb) RETURNING seq;")
    sql "INSERT INTO trading.audit_log (event_type,event_class,occurred_at,recorded_at,
                 actor,run_id,is_paper,is_backtest,payload)
         SELECT 'RT_KEYSET_CLEAN','ACTION',now(),now(),'keyset',gen_random_uuid(),true,false,
                jsonb_build_object('i',g) FROM generate_series(1,2) g;" >/dev/null
    clean=$(sql "SELECT count(*)::text FROM trading.audit_log WHERE seq >= $pbase AND seq <> $pseq;")

    # The mutation goes through the SAME replica-role bypass 7.1b pins as still open.
    sql "SET session_replication_role='replica';
         UPDATE trading.audit_log SET $mutation WHERE seq=$pseq;
         RESET session_replication_role;" >/dev/null

    # Read the column back before judging. An UPDATE that never landed looks identical to a
    # mutation the CONTENT check missed, and the two have opposite meanings: the first says
    # prevention was fixed (Finding A closed, and 7.1b would already have failed), the
    # second says detection regressed. Fail with the right message, not the plausible one.
    got=$(sql "SELECT ($readback)::text FROM trading.audit_log WHERE seq=$pseq;")
    if [ "$got" != "$expect" ]; then
        bad "$label — the mutation did not land (read back '$got', expected '$expect'); the replica-role bypass may have closed, see 7.1b"
        return
    fi

    mut=$(sql "SELECT coalesce(string_agg(DISTINCT broken_at::text, ',' ORDER BY broken_at::text), 'NONE')
                 FROM trading.verify_audit_chain($pbase) WHERE reason LIKE 'content mutated%';")
    case "$want" in
      detected)
        if [ "$mut" = "$pseq" ]; then
            ok "$label — reported at seq $pseq as 'content mutated' ($clean untampered rows in range, none flagged)"
        elif [ "$mut" = "NONE" ]; then
            bad "$label — NOT DETECTED. verify_audit_chain($pbase) reported no content mutation for a row whose ${mutation%%=*} was changed: that column is absent from the preimage in BOTH functions (X2 BLOCKER-A regression)"
        else
            bad "$label — reported {$mut}, expected exactly {$pseq}: false positive on an untampered row ($clean clean rows in range)"
        fi ;;
      ignored)
        if [ "$mut" = "NONE" ]; then
            ok "$label — correctly NOT reported"
        else
            bad "$label — reported {$mut}. recorded_at has entered the preimage; P1.4 6.1 [DEFAULT-A2] requires it OUT, because hashing when we wrote a row down means a replayed write can never reproduce the hash"
        fi ;;
    esac
    PROBE_SEQ="$pseq"
    PROBE_BASE="$pbase"
}

# The three columns the v0.5 correction added, plus `actor` through the identical harness so
# the four results are like for like and a harness fault cannot be mistaken for a finding.
audit_field_probe "7.1f is_paper mutation detected" \
    "is_paper=false"    "is_paper"    "false" detected
audit_field_probe "7.1f is_backtest mutation detected" \
    "is_backtest=true"  "is_backtest" "true"  detected
audit_field_probe "7.1f event_id mutation detected" \
    "event_id='00000000-0000-4000-8000-0000000000ff'" \
    "event_id" "00000000-0000-4000-8000-0000000000ff" detected
audit_field_probe "7.1f actor mutation detected (control, covered before v0.5)" \
    "actor='tampered_keyset'" "actor" "tampered_keyset" detected

# 7.1g — the NEGATIVE half, and it is not optional. P1.4 6.1 [DEFAULT-A2] keeps recorded_at
# OUT of the preimage on purpose: it records when we wrote the row down, not what happened,
# so hashing it would mean a replayed write could never reproduce the hash and the replay
# tool (P1.4 6.4) would be dead. A future correction that over-reaches and hashes "every
# column" would pass every check in 7.1f and break replay silently.
audit_field_probe "7.1g recorded_at mutation NOT reported ([DEFAULT-A2] keeps it out)" \
    "recorded_at = recorded_at + interval '400 days'" \
    "recorded_at > occurred_at + interval '300 days'" "true" ignored

# 7.1g control. A negative result is worthless without evidence the check was live over the
# range that produced it: with the CONTENT branch deleted entirely, the assertion above also
# passes. So mutate a column that IS hashed, on the SAME row in the SAME range, and require
# it to appear. Only then does "recorded_at was not reported" mean recorded_at is excluded
# rather than that nothing was being checked at all.
sql "SET session_replication_role='replica';
     UPDATE trading.audit_log SET actor='tampered_after_recorded_at' WHERE seq=$PROBE_SEQ;
     RESET session_replication_role;" >/dev/null
CTRLMUT=$(sql "SELECT coalesce(string_agg(DISTINCT broken_at::text, ',' ORDER BY broken_at::text), 'NONE')
                 FROM trading.verify_audit_chain($PROBE_BASE) WHERE reason LIKE 'content mutated%';")
if [ "$CTRLMUT" = "$PROBE_SEQ" ]; then
    ok "7.1g control: the SAME row and range DOES report once a hashed column changes — the negative result above is not vacuous"
else
    bad "7.1g control failed: expected {$PROBE_SEQ}, got {$CTRLMUT} — the CONTENT check was not live over this range, so the recorded_at result proves nothing"
fi

# ---------------------------------------------------------------------------------------
# 7.1h  MECHANICAL KEY-SET CONFORMANCE, read out of PostgreSQL's own catalogue.
#
# 7.1f/7.1g are behavioural and are what actually close BLOCKER-A. This is the structural
# companion, and it is written to avoid the trap X2 finding N-9 identified in checks
# 7.7a/7.8a: a guard that greps the raw function text is satisfied by prose in a comment.
# SQL line comments are stripped FIRST, then the digest() argument is extracted, split on
# '||' and reduced to a field list. A comment can no longer answer for a field.
#
# Two assertions, catching different regressions:
#   * writer and verifier must produce the SAME ORDERED term list. Divergence makes every
#     row report as mutated — loud, but this names the cause instead of the symptom.
#   * the field SET must be exactly the 11 SPEC-P1.4 6.1 keys that have an audit_log
#     column. Set equality, so it fails on an omission AND on an addition — including
#     recorded_at, which is the [DEFAULT-A2] direction 7.1g guards behaviourally.
preimage_terms() {
    sql "WITH d AS (
             SELECT regexp_replace(pg_get_functiondef('$1'::regprocedure), '--[^\n]*', '', 'g') AS src
         ), e AS (
             SELECT substring(src from 'digest\((.*?),\s*''sha256''') AS expr FROM d
         )
         SELECT string_agg(
                    regexp_replace(replace(replace(t, 'NEW.', ''), '::text', ''), '\s', '', 'g'),
                    '|' ORDER BY ord)
           FROM e, unnest(string_to_array(expr, '||')) WITH ORDINALITY AS u(t, ord);"
}
W_TERMS=$(preimage_terms 'trading.audit_chain_assign()')
V_TERMS=$(preimage_terms 'trading.verify_audit_chain(bigint)')
# SPEC-P1.4 6.1 pins 15 keys; four of them (canonical_schema, schema_version, causation_id,
# input_hash) have no audit_log column and are tracked as Q-P1.2-7. These are the other 11.
EXPECT_SET="actor,event_class,event_id,event_type,is_backtest,is_paper,occurred_at,payload,prev_hash,run_id,seq"
W_SET=$(printf '%s' "$W_TERMS" | tr '|' '\n' | LC_ALL=C sort | tr '\n' ',' | sed 's/,$//')

if [ -n "$W_TERMS" ] && [ "$W_TERMS" = "$V_TERMS" ]; then
    ok "7.1h writer and verifier hash the IDENTICAL ordered preimage"
else
    bad "7.1h writer/verifier preimage MISMATCH — writer {$W_TERMS} verifier {$V_TERMS}"
fi
if [ "$W_SET" = "$EXPECT_SET" ]; then
    ok "7.1h preimage covers exactly the 11 P1.4 6.1 keys that have an audit_log column"
else
    bad "7.1h preimage key set is {$W_SET}, expected {$EXPECT_SET} — a required field was dropped, or an excluded one (recorded_at) was added"
fi

echo "== 7.2  EXCLUDE rejects an overlapping symbol mapping =="
expect_fail "overlapping (market, symbol) date range rejected" \
    "INSERT INTO trading.symbol_mapping (instrument_id, market, exchange, symbol, valid_from, knowledge_from)
     VALUES (gen_random_uuid(),'US','NASDAQ','$SYM', DATE '2026-06-01', now());" \
    "symbol_mapping_no_overlap|exclusion|conflicting key"
# The EXCLUDE is partial: WHERE knowledge_to IS NULL. So the way to free the symbol is to
# RETIRE THE BELIEF, not to edit the fact. Closing valid_to would alter a fact column, which
# assert_bitemporal_close_only rejects - restatements are INSERTs, not UPDATEs.
expect_fail "editing a fact column (valid_to) on a bitemporal row rejected"     "UPDATE trading.symbol_mapping SET valid_to = DATE '2026-03-01'
     WHERE instrument_id='$INST' AND symbol='$SYM';"     "altered a fact column|restatements are INSERTs|only permitted UPDATE"

CLOSED=$(sql "UPDATE trading.symbol_mapping SET knowledge_to = now()
              WHERE instrument_id='$INST' AND symbol='$SYM' AND knowledge_to IS NULL RETURNING 1;")
if [ "$CLOSED" = "1" ]; then ok "retiring the belief (setting knowledge_to) is permitted"
else bad "could not close the mapping's knowledge interval: $CLOSED"; fi

# With the old belief retired the partial index no longer covers it, so the same symbol is
# free again - proving the constraint keys on the CURRENTLY-BELIEVED set, not on the symbol.
OUT=$(sql "INSERT INTO trading.symbol_mapping (instrument_id, market, exchange, symbol, valid_from, knowledge_from)
           VALUES (gen_random_uuid(),'US','NASDAQ','$SYM', DATE '2026-06-01', now()) RETURNING 1;")
if [ "$OUT" = "1" ]; then ok "same symbol re-mappable once the prior belief is retired (control)"
else bad "re-mapping after retiring the belief was rejected: $OUT"; fi

echo "== 7.3  a DENY verdict cannot be inserted into decision =="
sqlf <<SQL
INSERT INTO trading.risk_evaluation (verdict_id, request_id, instrument_id, pool_id, decision,
       limits_evaluated, nav_snapshot_id, evaluated_at, audit_event_id, binding_constraint)
VALUES ('$VER',gen_random_uuid(),'$INST','US_POOL','DENY', ARRAY['EXP-001'],
        gen_random_uuid(), now(), gen_random_uuid(), 'EXP-001');
SQL
expect_fail "decision rejects risk_decision = 'DENY'" \
    "INSERT INTO trading.decision (decision_id, instrument_id, market, pool_id, trading_date,
        action, target_quantity, strategy_version, model_id, risk_verdict_id, risk_decision,
        audit_event_id, decided_at)
     VALUES (gen_random_uuid(),'$INST','US','US_POOL', CURRENT_DATE,'ENTER',10,'v1','m1','$VER','DENY',
        gen_random_uuid(), now());" \
    "risk_decision|check constraint|violates"

echo "== 7.4  backtest_ro is denied on a bitemporal base table =="
expect_fail "backtest_ro SELECT on trading.instrument denied" \
    "SET ROLE backtest_ro; SELECT count(*) FROM trading.instrument;" \
    "permission denied"

echo "== 7.5  the overfill trigger is DEFERRED to COMMIT, not fired on INSERT =="
# Two fills of 60 against an order of 100. The first is fine. The second overfills, but the
# trigger is DEFERRABLE INITIALLY DEFERRED, so the INSERT must SUCCEED and the COMMIT must
# fail - that is what lets a partial fill and its cached filled_quantity update share one
# transaction while the intermediate state is briefly inconsistent.
OUT="$(docker compose exec -T "$SERVICE" psql -U "$USER" -d "$DB" -tA 2>&1 <<SQL | tr -d '\r' || true
BEGIN;
INSERT INTO trading.fill (fill_id, order_id, instrument_id, broker_id, broker_fill_id,
       quantity, price, fees, currency, filled_at, audit_event_id)
VALUES (gen_random_uuid(),'$ORD','$INST','alpaca','RT-F1',60,10.00,1.00,'USD',now(),gen_random_uuid());
SELECT 'first-insert-ok';
INSERT INTO trading.fill (fill_id, order_id, instrument_id, broker_id, broker_fill_id,
       quantity, price, fees, currency, filled_at, audit_event_id)
VALUES (gen_random_uuid(),'$ORD','$INST','alpaca','RT-F2',60,10.00,1.00,'USD',now(),gen_random_uuid());
SELECT 'second-insert-ok';
COMMIT;
SQL
)"
if printf '%s' "$OUT" | grep -q 'second-insert-ok' && printf '%s' "$OUT" | grep -qi 'OverfillError'; then
    ok "overfilling INSERT succeeded, COMMIT rejected it (deferred as specified)"
elif printf '%s' "$OUT" | grep -qi 'OverfillError'; then
    bad "OverfillError fired on INSERT, not at COMMIT — the trigger is not deferred"
else
    bad "no OverfillError at all: $(printf '%s' "$OUT" | tr '\n' ' ' | head -c 200)"
fi
# And the overfill must not have persisted.
LEFT=$(sql "SELECT coalesce(sum(quantity),0)::text FROM trading.fill WHERE order_id='$ORD';")
if [ "$LEFT" = "0.000000" ] || [ "$LEFT" = "0" ]; then
    ok "the rolled-back transaction left no fills behind ($LEFT)"
else bad "expected 0 fills after rollback, found sum=$LEFT"; fi

echo "== 7.6  Q-P1.2-3: compression vs the deny-mutation triggers =="
sql "INSERT INTO trading.audit_log (event_type,event_class,occurred_at,recorded_at,actor,run_id,is_paper,is_backtest,payload)
     SELECT 'RT_OLD','SYSTEM', now()-interval '90 days', now()-interval '90 days','rt',gen_random_uuid(),true,false,'{}'::jsonb
     FROM generate_series(1,20);" >/dev/null
CHUNKS=$(sql "SELECT count(*)::text FROM (SELECT extensions.compress_chunk(c, if_not_compressed => true)
              FROM extensions.show_chunks('trading.audit_log', older_than => INTERVAL '30 days') c) x;")
# compress_chunk emits a NOTICE when a chunk is already compressed, so keep only the
# last numeric line rather than assuming the output is a bare integer.
CHUNKS=$(printf '%s' "$CHUNKS" | grep -oE '^[0-9]+$' | tail -1)
if [ -n "$CHUNKS" ] && [ "$CHUNKS" -ge 1 ]; then
    ok "compression job ran, $CHUNKS chunk(s) compressed — deny triggers did not block it"
else bad "compression did not run: $CHUNKS"; fi
OLDSEQ=$(sql "SELECT min(seq)::text FROM trading.audit_log WHERE event_type='RT_OLD';")
expect_fail "UPDATE on a COMPRESSED chunk still rejected" \
    "UPDATE trading.audit_log SET actor='tampered' WHERE seq=$OLDSEQ;" \
    "append-only|immutable|not permitted|denied|cannot|deny|compress"

echo "== 7.7  Finding C: the hash preimage is timezone-INDEPENDENT =="
# occurred_at::text renders per session TimeZone, so without a pin the same instant hashes
# three different ways and a legitimate row written under a non-UTC session would verify as
# CONTENT MUTATED. Both audit_chain_assign() and verify_audit_chain() pin TimeZone='UTC'.

# 7.7a — the mechanism guard. Fails if either pin is removed.
for fn in audit_chain_assign verify_audit_chain; do
    sig="trading.$fn()"; [ "$fn" = "verify_audit_chain" ] && sig="trading.$fn(bigint)"
    PIN=$(sql "SELECT CASE WHEN pg_get_functiondef('$sig'::regprocedure) ~* 'TimeZone'
                           THEN 'yes' ELSE 'no' END;")
    if [ "$PIN" = "yes" ]; then ok "$fn pins TimeZone"
    else bad "$fn does NOT pin TimeZone — Finding C regression"; fi
done

# 7.7b — a DISCRIMINATING control. Comparing the three stored rows in one query proves
# nothing: that query renders occurred_at under its own single TimeZone, so the answer is
# the same whether or not the trigger is pinned. Instead, exercise the mechanism directly —
# two scratch functions, identical but for the pin, evaluated from three timezones.
CTRL=$(sql "
CREATE OR REPLACE FUNCTION pg_temp.h_unpinned(ts timestamptz) RETURNS text
LANGUAGE sql STABLE SET search_path = extensions, pg_temp AS \$f\$
    SELECT encode(digest(ts::text,'sha256'),'hex') \$f\$;
CREATE OR REPLACE FUNCTION pg_temp.h_pinned(ts timestamptz) RETURNS text
LANGUAGE sql STABLE SET search_path = extensions, pg_temp SET TimeZone='UTC' AS \$f\$
    SELECT encode(digest(ts::text,'sha256'),'hex') \$f\$;
SET TimeZone='UTC';          SELECT pg_temp.h_unpinned(TIMESTAMPTZ '2026-08-27 12:00:00+00');
SET TimeZone='Asia/Kolkata'; SELECT pg_temp.h_unpinned(TIMESTAMPTZ '2026-08-27 12:00:00+00');
SET TimeZone='UTC';          SELECT pg_temp.h_pinned(TIMESTAMPTZ '2026-08-27 12:00:00+00');
SET TimeZone='Asia/Kolkata'; SELECT pg_temp.h_pinned(TIMESTAMPTZ '2026-08-27 12:00:00+00');
RESET TimeZone;")
HEX=$(printf '%s' "$CTRL" | grep -oE '^[0-9a-f]{64}$')
U1=$(printf '%s' "$HEX" | sed -n '1p'); K1=$(printf '%s' "$HEX" | sed -n '2p')
U2=$(printf '%s' "$HEX" | sed -n '3p'); K2=$(printf '%s' "$HEX" | sed -n '4p')
if [ -n "$U1" ] && [ "$U1" != "$K1" ]; then
    ok "control: WITHOUT the pin the same instant hashes differently across timezones"
else bad "control failed: unpinned digests did not differ (U=$U1 K=$K1) — test not discriminating"; fi
if [ -n "$U2" ] && [ "$U2" = "$K2" ]; then
    ok "WITH the pin the same instant hashes identically across timezones"
else bad "pinned digests differ across timezones (U=$U2 K=$K2) — Finding C not fixed"; fi

# 7.7c — the end-to-end property: rows written under non-UTC sessions must verify clean.
TZBASE=$(sql "SELECT coalesce(max(seq),-1)+1 FROM trading.audit_log;")
RID=$(sql "SELECT gen_random_uuid();")
for tz in UTC Asia/Kolkata America/New_York; do
    sql "SET TimeZone='$tz';
         INSERT INTO trading.audit_log (event_type,event_class,occurred_at,recorded_at,actor,
                run_id,is_paper,is_backtest,payload)
         VALUES ('TZ_PROBE','SYSTEM', TIMESTAMPTZ '2026-08-27 12:00:00+00', now(),
                 'tz','$RID',true,false,'{\"k\":1}'::jsonb);" >/dev/null
done
# 7.7c — and those rows must verify clean. Before the fix a non-UTC insert would have been
# reported as content mutated: a false tamper alarm on a legitimate row.
TZBROKEN=$(sql "SELECT count(*)::text FROM trading.verify_audit_chain($TZBASE)
                WHERE reason LIKE 'content mutated%';")
if [ "$TZBROKEN" = "0" ]; then
    ok "rows written under non-UTC sessions verify clean (no false tamper alarm)"
else bad "$TZBROKEN row(s) falsely reported as content-mutated"; fi

echo "== 7.8  X2 BLOCKER-1: the hash preimage is DateStyle-INDEPENDENT too =="
# Finding C pinned TimeZone and stopped there. occurred_at::text depends on DateStyle as
# well, so the same defect survived with a different GUC: under a pinned UTC the one
# instant still rendered '2026-08-27 12:00:00+00' (ISO) vs '27.08.2026 12:00:00 UTC'
# (German). Measured before the fix, via PGDATESTYLE alone and no SQL: an untampered row
# written under a hostile DateStyle verified as CONTENT MUTATED, and an untampered chain
# verified FROM a hostile session reported every row mutated. Both pins are now required.

# 7.8a — mechanism guard, both functions. Fails the moment either DateStyle pin is dropped.
for fn in audit_chain_assign verify_audit_chain; do
    sig="trading.$fn()"; [ "$fn" = "verify_audit_chain" ] && sig="trading.$fn(bigint)"
    PIN=$(sql "SELECT CASE WHEN pg_get_functiondef('$sig'::regprocedure) ~* 'DateStyle'
                           THEN 'yes' ELSE 'no' END;")
    if [ "$PIN" = "yes" ]; then ok "$fn pins DateStyle"
    else bad "$fn does NOT pin DateStyle — X2 BLOCKER-1 regression"; fi
done

# 7.8b — the DISCRIMINATING control. TimeZone is pinned in BOTH scratch functions so the
# only variable under test is DateStyle; otherwise a passing control would prove nothing
# about the half of the bug this section exists for.
DCTRL=$(sql "
CREATE OR REPLACE FUNCTION pg_temp.d_unpinned(ts timestamptz) RETURNS text
LANGUAGE sql STABLE SET search_path = extensions, pg_temp SET TimeZone='UTC' AS \$f\$
    SELECT encode(digest(ts::text,'sha256'),'hex') \$f\$;
CREATE OR REPLACE FUNCTION pg_temp.d_pinned(ts timestamptz) RETURNS text
LANGUAGE sql STABLE SET search_path = extensions, pg_temp SET TimeZone='UTC'
                    SET DateStyle='ISO, MDY' AS \$f\$
    SELECT encode(digest(ts::text,'sha256'),'hex') \$f\$;
SET DateStyle='ISO, MDY';      SELECT pg_temp.d_unpinned(TIMESTAMPTZ '2026-08-27 12:00:00+00');
SET DateStyle='German, DMY';   SELECT pg_temp.d_unpinned(TIMESTAMPTZ '2026-08-27 12:00:00+00');
SET DateStyle='ISO, MDY';      SELECT pg_temp.d_pinned(TIMESTAMPTZ '2026-08-27 12:00:00+00');
SET DateStyle='German, DMY';   SELECT pg_temp.d_pinned(TIMESTAMPTZ '2026-08-27 12:00:00+00');
RESET DateStyle;")
DHEX=$(printf '%s' "$DCTRL" | grep -oE '^[0-9a-f]{64}$')
DU1=$(printf '%s' "$DHEX" | sed -n '1p'); DG1=$(printf '%s' "$DHEX" | sed -n '2p')
DU2=$(printf '%s' "$DHEX" | sed -n '3p'); DG2=$(printf '%s' "$DHEX" | sed -n '4p')
if [ -n "$DU1" ] && [ "$DU1" != "$DG1" ]; then
    ok "control: WITHOUT the DateStyle pin the same instant hashes differently (ISO vs German)"
else bad "control failed: unpinned digests did not differ (ISO=$DU1 German=$DG1) — test not discriminating"; fi
if [ -n "$DU2" ] && [ "$DU2" = "$DG2" ]; then
    ok "WITH the DateStyle pin the same instant hashes identically across DateStyles"
else bad "pinned digests differ across DateStyles (ISO=$DU2 German=$DG2) — BLOCKER-1 not fixed"; fi

# 7.8c — WRITER side, end to end. Rows written under hostile DateStyles must verify clean.
# Fails if audit_chain_assign() loses its pin: the row is then hashed from a German render
# and the verifier, rendering ISO, reports a legitimate row as mutated.
DSBASE=$(sql "SELECT coalesce(max(seq),-1)+1 FROM trading.audit_log;")
DRID=$(sql "SELECT gen_random_uuid();")
for ds in 'ISO, MDY' 'German, DMY' 'SQL, DMY' 'Postgres, DMY'; do
    sql "SET DateStyle='$ds';
         INSERT INTO trading.audit_log (event_type,event_class,occurred_at,recorded_at,actor,
                run_id,is_paper,is_backtest,payload)
         VALUES ('DS_PROBE','SYSTEM', TIMESTAMPTZ '2026-08-27 12:00:00+00', now(),
                 'ds','$DRID',true,false,'{\"k\":1}'::jsonb);" >/dev/null
done
DSWRITE=$(sql "SELECT count(*)::text FROM trading.verify_audit_chain($DSBASE)
               WHERE reason LIKE 'content mutated%';")
if [ "$DSWRITE" = "0" ]; then
    ok "rows written under hostile DateStyle sessions verify clean (no false tamper alarm)"
else bad "$DSWRITE row(s) written under a non-ISO DateStyle falsely reported as content-mutated"; fi

# 7.8d — VERIFIER side. The same untampered rows must verify clean when the CALLING session
# carries a hostile DateStyle. This is the check the TimeZone half never had (X2 finding
# N-4): 7.7c cannot see a missing verify-side pin because the container session is already
# UTC. Here the session is deliberately hostile, so dropping verify_audit_chain()'s pin
# makes every row in range mismatch and this check fails behaviourally, not just by grep.
for ds in 'German, DMY' 'SQL, DMY'; do
    DSREAD=$(sql "SET DateStyle='$ds';
                  SELECT count(*)::text FROM trading.verify_audit_chain($DSBASE)
                   WHERE reason LIKE 'content mutated%';
                  RESET DateStyle;")
    if [ "$DSREAD" = "0" ]; then
        ok "untampered chain verifies clean from a '$ds' verifier session"
    else bad "verifier session '$ds' falsely reported $DSREAD row(s) as content-mutated"; fi
done

echo
echo "PASSED $PASS   FAILED $FAIL"
[ "$FAIL" -eq 0 ]
