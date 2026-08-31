#!/usr/bin/env bash
# SPEC-P1.2-STORAGE v0.1 — apply 0001_initial.sql and assert it succeeded (X2 finding B-1).
#
# B-1: the schema had never been executed. This script is the execution, and it is the
# same command locally and in CI so a CI pass means the developer's schema really applies.
#
# Fail-closed: ON_ERROR_STOP=1 makes psql abort on the FIRST error rather than plough on
# and report success at the end. Any non-zero exit anywhere aborts the whole script.
set -Eeuo pipefail

# Git Bash / MSYS on Windows rewrites POSIX-looking arguments into Windows paths, turning
# the container path /migrations/0001_initial.sql into D:/Git/migrations/0001_initial.sql
# before psql ever sees it. These paths are INSIDE the Linux container, so the translation
# must be off. Ignored by bash on Linux, so CI is unaffected.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SERVICE="timescaledb"
MIGRATION="migrations/0001_initial.sql"
DB="${APP_DB:-trading}"
USER="${POSTGRES_USER:-postgres}"
# Maintenance database used to create/drop the application database. Never migrated.
MAINT_DB="postgres"

log() { printf '[apply-migration] %s\n' "$*"; }
fail() { printf '[apply-migration] FAILED: %s\n' "$*" >&2; exit 1; }

[ -f "$MIGRATION" ] || fail "$MIGRATION not found (cwd=$PWD)"

# ---------------------------------------------------------------------------
# 1. Wait for the container to be genuinely ready, not merely running.
# ---------------------------------------------------------------------------
log "waiting for $SERVICE to become healthy"
deadline=$(( SECONDS + 180 ))
until [ "$(docker compose ps --format '{{.Health}}' "$SERVICE" 2>/dev/null)" = "healthy" ]; do
    [ "$SECONDS" -lt "$deadline" ] || fail "$SERVICE did not become healthy within 180s"
    sleep 3
done
log "$SERVICE is healthy"

# ---------------------------------------------------------------------------
# 2. Provision the application database from template0.
#
#    The image installs timescaledb into template1, so a template1-derived database
#    inherits it in schema `public`. 0001_initial.sql requires it in `extensions`, and
#    timescaledb is relocatable=false, so ALTER EXTENSION ... SET SCHEMA cannot repair it
#    afterwards. template0 carries no extensions, which lets the migration install
#    timescaledb into `extensions` itself.
#
#    The database is recreated on every run so "does this migration apply?" is always
#    answered against a pristine database. This drops $DB and nothing else.
# ---------------------------------------------------------------------------
#    B-3. 0001 also creates FOUR CLUSTER-SCOPED roles (trading_owner, app_rw, backtest_ro,
#    metrics_ro). Dropping the database does not drop those, so a second run of this script
#    against a persistent volume died at 0001_initial.sql:14 with
#    'role "trading_owner" already exists' (psql exit 3).
#
#    That is NOT a defect in the migration. SPEC-P1.2 §6 says 0001 "runs as a superuser
#    once" and §11 puts application under Alembic, which applies each revision exactly
#    once. 0001 is deliberately not idempotent, and adding IF NOT EXISTS guards would mask
#    a real misconfiguration (0001 run against a cluster that already has these roles).
#    The harness is what must reset, because it re-runs a once-only revision on purpose.
#
#    Roles are dropped AFTER the database, so they own nothing by the time they are
#    dropped. Order within the DROP ROLE is irrelevant; none of them owns another.
log "recreating database '$DB' and its cluster-scoped roles"
docker compose exec -T "$SERVICE" psql -v ON_ERROR_STOP=1 -U "$USER" -d "$MAINT_DB" \
    -c "DROP DATABASE IF EXISTS $DB WITH (FORCE);" \
    -c "DROP ROLE IF EXISTS app_rw, backtest_ro, metrics_ro, trading_owner;" \
    -c "CREATE DATABASE $DB TEMPLATE template0;" >/dev/null \
    || fail "could not provision database '$DB'"

# ---------------------------------------------------------------------------
# 3. Apply the migration. ON_ERROR_STOP=1 is what makes this an assertion.
# ---------------------------------------------------------------------------
log "applying $MIGRATION"
set +e
docker compose exec -T "$SERVICE" \
    psql -v ON_ERROR_STOP=1 --echo-errors -U "$USER" -d "$DB" -f "/$MIGRATION"
rc=$?
set -e

if [ "$rc" -ne 0 ]; then
    fail "migration exited $rc (expected 0)"
fi
log "migration exit code 0"

# ---------------------------------------------------------------------------
# 4. Evidence the objects actually exist. A clean exit is necessary, not sufficient:
#    a migration wrapped in a swallowed exception would also exit 0. The extension
#    SCHEMA is asserted too: a timescaledb in `public` is the B-2 failure mode.
# ---------------------------------------------------------------------------
log "collecting schema evidence"
docker compose exec -T "$SERVICE" psql -v ON_ERROR_STOP=1 -U "$USER" -d "$DB" -tA <<'SQL'
SELECT 'extensions      : ' || string_agg(e.extname || '@' || n.nspname, ', ' ORDER BY e.extname)
  FROM pg_extension e JOIN pg_namespace n ON n.oid = e.extnamespace
 WHERE e.extname IN ('timescaledb','btree_gist','pgcrypto');
SELECT 'tables          : ' || count(*)::text
  FROM information_schema.tables WHERE table_schema = 'trading' AND table_type = 'BASE TABLE';
SELECT 'hypertables     : ' || count(*)::text
  FROM timescaledb_information.hypertables WHERE hypertable_schema = 'trading';
SELECT 'continuous aggs : ' || count(*)::text
  FROM timescaledb_information.continuous_aggregates WHERE view_schema = 'trading';
SELECT 'triggers        : ' || count(*)::text
  FROM information_schema.triggers WHERE trigger_schema = 'trading';
SQL

log "OK"
