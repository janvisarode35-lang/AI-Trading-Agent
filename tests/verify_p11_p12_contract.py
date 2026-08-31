"""Cross-spec conformance: every P1.2 column that mirrors a P1.1 field must exist on
the model. This is the check that would have caught X2 findings F-5 and F-9
automatically instead of by hand."""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from domain import models as m  # noqa: E402
from audit import events as ae  # noqa: E402

DDL = (REPO_ROOT / "migrations" / "0001_initial.sql").read_text(encoding="utf-8")

# Columns that are storage concerns, not domain concerns, and are deliberately absent
# from the model. Each needs a reason or it is drift wearing a waiver.
STORAGE_ONLY = {
    "knowledge_from", "knowledge_to",   # bitemporal axes: P1.2 §3.1, not domain fields
    "valid_from", "valid_to",           # ditto, except on SymbolMapping where they ARE fields
    "currency",                         # P1.2 [DEFAULT-S5]: one currency column per table;
                                        # the model carries it inside Money/Price
    "observation_id", "created_at", "updated_at",
    "restatement_seq", "edgar_index_hash",  # P1.2 §6.5 bitemporal mechanics
    "universe_version", "effective_from", "instrument_count", "enter_rank", "exit_rank",
    "addv_rank", "retained_as_held",
    "pool_nav_ids", "fx_rate_ids",
}

# table -> (model, extra storage-only columns for this table)
MAPPING = {
    "order_intent": (m.Order, set()),
    "fill": (m.Fill, set()),
    "lot": (m.Lot, set()),
    "decision": (m.Decision, set()),
    "risk_evaluation": (m.RiskVerdict, set()),
    "thesis": (m.Thesis, {"llm_call_id"}),
    "score": (m.Score, set()),
    "candidate": (m.Candidate, {"run_id"}),
    # The envelope moved to P1.4 (SPEC-P1.4 §4); P1.1 kept only the enum.
    "audit_log": (ae.AuditEnvelope, {"seq", "payload_hash", "prev_hash"}),
    "run_context": (m.RunContext, set()),
    "account": (m.Account, set()),
    "exchange_session": (m.ExchangeSession, set()),
    "position_state": (m.PositionState, set()),   # enum, not a model - skipped below
    # kill_switch_event is the TRANSITION LOG (one row per transition); KillSwitch is
    # the CURRENT STATE object. Different shapes on purpose, so the log's own
    # identity and transition columns have no model counterpart.
    "kill_switch_event": (m.KillSwitch, {"from_state", "to_state", "occurred_at",
                                         "event_id"}),
    "instrument": (m.Instrument, set()),
    "symbol_mapping": (m.SymbolMapping, {"mapping_id"}),
    "successor_link": (m.SuccessorLink, {"audit_event_id", "cash_currency"}),
    "fx_rate": (m.FxRate, set()),
    "nav_pool": (m.PoolNAV, set()),
    "nav_consolidated": (m.ConsolidatedNAV, set()),
    # news_id is an UNUSED surrogate in P1.2: the PK is (vendor_id, revision_seq,
    # first_seen_at) and news_instrument references that, not news_id. Waived here
    # and raised as an observation against P1.2's own X2, not a P1.1 defect.
    "news_item": (m.NewsItem, {"news_id"}),
    "invalidation_condition": (m.InvalidationCondition, {"thesis_id"}),
}

# Model-side aliases where the column name differs deliberately.
ALIASES = {
    ("audit_log", "seq"): "seq",
    ("nav_pool", "nav_id"): "nav_id",
    ("thesis", "generated_at"): "generated_at",
}

problems = []
checked = 0

for table, (model, extra) in MAPPING.items():
    if not (isinstance(model, type) and hasattr(model, "model_fields")):
        continue  # enums such as PositionState have no columns to align
    body = re.search(
        r"CREATE TABLE trading\.%s \((.*?)\n\)" % re.escape(table), DDL, re.S)
    if not body:
        problems.append(f"{table}: no CREATE TABLE found in migration 0001")
        continue
    cols = []
    for line in body.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("--") or line.upper().startswith(
                ("PRIMARY KEY", "CONSTRAINT", "UNIQUE", "CHECK", "FOREIGN KEY", "EXCLUDE")):
            continue
        mm = re.match(r"([a-z_][a-z0-9_]*)\s+", line)
        if mm:
            cols.append(mm.group(1))
    fields = set(model.model_fields)
    for c in cols:
        if c in STORAGE_ONLY or c in extra or c in fields:
            continue
        if ALIASES.get((table, c)) in fields:
            continue
        problems.append(f"{table}.{c} has no field on {model.__name__}")
    checked += 1

print(f"checked {checked} table/model pairs")
if problems:
    print(f"FAILED — {len(problems)} unmapped column(s):")
    for p in problems:
        print("  *", p)
    sys.exit(1)
print("P1.1 <-> P1.2 CONTRACT ALIGNED")
