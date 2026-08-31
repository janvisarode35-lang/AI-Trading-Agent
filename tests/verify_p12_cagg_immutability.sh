#!/usr/bin/env bash
# SPEC-P1.2-STORAGE v0.1 §5 / P0.3 §9.4 / measurement-by-design Q15 — X2 finding B-4.
#
# A continuous aggregate must not depend on a non-IMMUTABLE expression. TimescaleDB warns
# about it rather than refusing, so nothing fails loudly if one is reintroduced - which is
# how B-4 survived until the migration was actually executed.
#
# pg_column_size is STABLE because it reports STORED size: the same logical jsonb measures
# 192 B in an lz4 column, 487 B in a pglz column and 40,020 B as an uncompressed literal.
# Rows in audit_log are immutable, so routine refresh is stable; the exposure is anything
# that re-TOASTs them (pg_dump/restore under a different default_toast_compression,
# ALTER COLUMN ... SET COMPRESSION, VACUUM FULL). This cagg refreshes back 35 days, so
# such a change silently rewrites already-materialised buckets.
#
# Runs against the live pinned database.
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
q()   { docker compose exec -T "$SERVICE" psql -U "$USER" -d "$DB" -tA -c "$1" | tr -d '\r'; }

[ "$(docker compose ps --format '{{.Health}}' "$SERVICE" 2>/dev/null)" = "healthy" ] \
    || { echo "service '$SERVICE' not healthy; run: docker compose up -d --wait"; exit 2; }

echo "== B-4.1  no pg_column_size in executable migration SQL (comments excluded) =="
# Comment lines are excluded deliberately: the fix's own rationale names the function.
N="$(grep -vE '^[[:space:]]*--' migrations/0001_initial.sql | grep -c 'pg_column_size' || true)"
if [ "$N" = "0" ]; then ok "pg_column_size absent from executable SQL"
else bad "pg_column_size present $N time(s) in executable SQL - B-4 regression"
     grep -nE 'pg_column_size' migrations/0001_initial.sql | grep -vE ':[[:space:]]*--'; fi

echo "== B-4.2  applying the migration emits no non-immutable warning =="
LOG=/tmp/b4_apply.log
if bash scripts/apply-migration.sh >"$LOG" 2>&1; then
    W="$(grep -c 'non-immutable' "$LOG" || true)"
    if [ "$W" = "0" ]; then ok "migration applied clean, 0 non-immutable warnings"
    else bad "$W non-immutable warning(s) emitted"; grep -m3 'non-immutable' "$LOG"; fi
else
    bad "migration failed (see $LOG)"; tail -5 "$LOG"
fi

echo "== B-4.3  every cagg definition uses only IMMUTABLE functions =="
# Scans the DEPLOYED definition in the catalog, not the source file, so it also catches a
# cagg created outside 0001. Every non-IMMUTABLE function name in pg_proc is matched against
# each definition in call form (\mname\s*\().
BAD_FN="$(q "
WITH ca AS (
    SELECT view_name, view_definition
      FROM timescaledb_information.continuous_aggregates
     WHERE view_schema = 'trading' AND view_definition IS NOT NULL
), nonimm AS (
    SELECT DISTINCT proname,
           CASE provolatile WHEN 's' THEN 'STABLE' ELSE 'VOLATILE' END AS vol
      FROM pg_proc WHERE provolatile <> 'i'
       -- Exclude type-coercion functions: a cast rendered as numeric(12,2) in the view
       -- definition is not a function call. Their names are exactly the type names.
       AND proname NOT IN (SELECT typname FROM pg_type)
)
SELECT ca.view_name || ' uses ' || n.proname || ' (' || n.vol || ')'
  FROM ca JOIN nonimm n
    ON ca.view_definition ~ ('\\m' || n.proname || '\\s*\\(')
 ORDER BY 1;
")"
if [ -z "$BAD_FN" ]; then ok "no non-IMMUTABLE function referenced by any trading cagg"
else bad "non-IMMUTABLE function(s) in a cagg: $BAD_FN"; fi

echo "== B-4.4  the replacement is storage-INDEPENDENT (the property B-4 needed) =="
RES="$(q "
CREATE TEMP TABLE b4_lz4 (j jsonb);  ALTER TABLE b4_lz4  ALTER COLUMN j SET COMPRESSION lz4;
CREATE TEMP TABLE b4_pglz(j jsonb);  ALTER TABLE b4_pglz ALTER COLUMN j SET COMPRESSION pglz;
INSERT INTO b4_lz4  SELECT jsonb_build_object('blob', repeat('y', 40000));
INSERT INTO b4_pglz SELECT jsonb_build_object('blob', repeat('y', 40000));
SELECT (SELECT octet_length(j::text) FROM b4_lz4) || ':' || (SELECT octet_length(j::text) FROM b4_pglz)
    || ':' || (SELECT pg_column_size(j) FROM b4_lz4) || ':' || (SELECT pg_column_size(j) FROM b4_pglz);
" | tail -1)"
IMM_LZ4="${RES%%:*}"; REST="${RES#*:}"; IMM_PGLZ="${REST%%:*}"; REST="${REST#*:}"
STA_LZ4="${REST%%:*}"; STA_PGLZ="${REST##*:}"
if [ "$IMM_LZ4" = "$IMM_PGLZ" ] && [ -n "$IMM_LZ4" ]; then
    ok "octet_length identical across lz4/pglz ($IMM_LZ4 both)"
else
    bad "octet_length differed across storage: lz4=$IMM_LZ4 pglz=$IMM_PGLZ"
fi
if [ "$STA_LZ4" != "$STA_PGLZ" ]; then
    ok "control: pg_column_size DOES differ (lz4=$STA_LZ4 pglz=$STA_PGLZ) - the hazard is real"
else
    bad "control failed: pg_column_size did not differ, test is not exercising the hazard"
fi

echo "== B-4.5  rematerialisation is byte-identical to direct recomputation =="
q "INSERT INTO trading.audit_log (event_type,event_class,occurred_at,recorded_at,actor,run_id,is_paper,is_backtest,payload)
   SELECT 'B4_TEST','SYSTEM', now()-interval '60 days', now()-interval '60 days','b4',gen_random_uuid(),true,false,
          jsonb_build_object('i',g,'blob',repeat('x', 900 + (g%100)))
   FROM generate_series(1,100) g;" >/dev/null
q "CALL extensions.refresh_continuous_aggregate('trading.cagg_audit_events_daily', NULL, NULL);" >/dev/null
CAGG="$(q "SELECT coalesce(sum(payload_bytes),0)||'/'||coalesce(sum(event_count),0) FROM trading.cagg_audit_events_daily;" | tail -1)"
BASE="$(q "SELECT coalesce(sum(octet_length(payload::text)),0)||'/'||count(*) FROM trading.audit_log;" | tail -1)"
if [ "$CAGG" = "$BASE" ] && [ -n "$CAGG" ]; then
    ok "cagg matches base-table recomputation exactly ($CAGG)"
else
    bad "cagg $CAGG != base table $BASE"
fi

echo
echo "PASSED $PASS   FAILED $FAIL"
[ "$FAIL" -eq 0 ]
