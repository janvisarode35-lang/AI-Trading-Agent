#!/usr/bin/env bash
# SPEC-P1.2-STORAGE v0.1 §6, §11 — X2 finding B-3.
#
# Two properties, and they pull in opposite directions. Both must hold.
#
#   1. THE MIGRATION IS NOT IDEMPOTENT, BY DESIGN. §6 says 0001 "runs as a superuser
#      once"; §11 applies revisions under Alembic, exactly once each. Applying 0001 twice
#      to one cluster MUST fail - it means the cluster is not in the state 0001 assumes.
#      A passing re-apply would mean someone had added IF NOT EXISTS guards and destroyed
#      that signal.
#
#   2. THE VERIFICATION HARNESS IS RERUNNABLE. scripts/apply-migration.sh deliberately
#      re-runs a once-only revision to prove the DDL executes (B-1), so it must reset
#      cluster state - the four roles as well as the database - before each apply.
#
# This test runs against a PERSISTENT container. It never calls `docker compose down -v`;
# the whole point is that the volume survives between the two runs.
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

ok()   { printf '  PASS  %s\n' "$*"; PASS=$((PASS+1)); }
bad()  { printf '  FAIL  %s\n' "$*"; FAIL=$((FAIL+1)); }
psqlq() { docker compose exec -T "$SERVICE" psql -U "$USER" -d "$1" -tA -c "$2"; }

command -v docker >/dev/null || { echo "docker not on PATH"; exit 2; }
[ "$(docker compose ps --format '{{.Health}}' "$SERVICE" 2>/dev/null)" = "healthy" ] \
    || { echo "service '$SERVICE' is not healthy; start it with: docker compose up -d --wait"; exit 2; }

CONTAINER_AT_START="$(docker compose ps -q "$SERVICE")"

echo "== B-3.1  harness run #1 on the persistent cluster =="
if bash scripts/apply-migration.sh >/tmp/b3_run1.log 2>&1; then
    ok "first apply exited 0"
else
    bad "first apply exited $? (see /tmp/b3_run1.log)"; tail -5 /tmp/b3_run1.log
fi
EV1="$(grep -E '^(extensions|tables|hypertables|continuous aggs|triggers)' /tmp/b3_run1.log || true)"

echo "== B-3.2  harness run #2 on the SAME cluster, no down -v =="
if bash scripts/apply-migration.sh >/tmp/b3_run2.log 2>&1; then
    ok "second apply exited 0 (harness resets cluster-scoped roles)"
else
    bad "second apply exited $? - B-3 regression (see /tmp/b3_run2.log)"; tail -5 /tmp/b3_run2.log
fi
EV2="$(grep -E '^(extensions|tables|hypertables|continuous aggs|triggers)' /tmp/b3_run2.log || true)"

echo "== B-3.3  both runs produced an identical schema =="
if [ -n "$EV1" ] && [ "$EV1" = "$EV2" ]; then
    ok "schema evidence identical across runs"
    printf '        %s\n' "$EV1"
else
    bad "schema evidence differs between runs"
    printf '        run1: %s\n        run2: %s\n' "$EV1" "$EV2"
fi

echo "== B-3.4  the volume really did persist (same container, no recreate) =="
if [ "$CONTAINER_AT_START" = "$(docker compose ps -q "$SERVICE")" ]; then
    ok "same container id throughout - this was a persistent-cluster test"
else
    bad "container was recreated; this did not test persistence"
fi

echo "== B-3.5  §6/§11 contract: re-applying 0001 to the SAME database MUST fail =="
# No harness reset here - apply 0001 straight onto the database the harness just built.
set +e
OUT="$(docker compose exec -T "$SERVICE" psql -v ON_ERROR_STOP=1 -U "$USER" -d "$DB" \
        -f /migrations/0001_initial.sql 2>&1)"
RC=$?
set -e
if [ "$RC" -ne 0 ] && printf '%s' "$OUT" | grep -q 'role "trading_owner" already exists'; then
    ok "re-apply rejected (psql exit $RC, role collision) - 'runs once' contract intact"
elif [ "$RC" -eq 0 ]; then
    bad "re-apply SUCCEEDED - 0001 has been made idempotent, which contradicts SPEC-P1.2 §6/§11"
else
    bad "re-apply failed for an unexpected reason (exit $RC): $(printf '%s' "$OUT" | grep -m1 ERROR)"
fi

echo "== B-3.6  cluster left in a good state =="
ROLES="$(psqlq "$DB" "SELECT count(*) FROM pg_roles WHERE rolname IN ('trading_owner','app_rw','backtest_ro','metrics_ro');" | tr -d '[:space:]')"
if [ "$ROLES" = "4" ]; then ok "all four roles present"; else bad "expected 4 roles, found '$ROLES'"; fi

echo
echo "PASSED $PASS   FAILED $FAIL"
[ "$FAIL" -eq 0 ]
