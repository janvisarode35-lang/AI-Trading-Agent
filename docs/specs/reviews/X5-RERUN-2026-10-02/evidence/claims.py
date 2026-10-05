import sys, inspect, json, re
from pathlib import Path
from decimal import Decimal
sys.path.insert(0, "src")
from config import loader as L
from audit import events as E, chain as K
from domain import models as M
print("loader public:", [n for n in dir(L) if not n.startswith("_")][:80])
ld = L.PolicyLoader(Path("config"))
eff = ld.load(require_signature=False)
doc = eff.policy if hasattr(eff, "policy") else None
print("EffectiveConfig fields:", list(type(eff).model_fields))
rules = None
for name in type(eff).model_fields:
    v = getattr(eff, name)
    if hasattr(v, "rules"): rules = v.rules; print("rules via", name)
if rules is None and hasattr(eff, "rules"): rules = eff.rules
print("rule count", len(rules))
want = ["EXP-001","EXP-002","EXP-003","EXP-004","LOSS-001","LOSS-002","LOSS-003","LOSS-004","SIZE-001","LIQ-001","RATE-001","RATE-002","STOP-001","DATA-001","CASH-002","EXEC-001","HOLD-002","KILL-001","EDGE-001","PORT-002"]
byid = {r.id: r for r in rules}
for w in want:
    r = byid.get(w)
    if r is None: print(w, "MISSING"); continue
    d = r.model_dump()
    print(w, {k: (str(v) if isinstance(v, Decimal) else getattr(v, 'value', v)) for k, v in d.items() if k in ("threshold","comparison","action","mode","severity","on_missing_input","scope")}, "|", str(d.get("description",""))[:70])
import collections
print("actions", collections.Counter(getattr(r.action,'value',r.action) for r in rules))
print("modes", collections.Counter(getattr(r.mode,'value',r.mode) for r in rules))
print("on_missing", collections.Counter(str(getattr(r.on_missing_input,'value',r.on_missing_input)) for r in rules))
print("ids:", sorted(byid))
# X3R-M2
pl = eff.audit_payload()
nums = []
def walk(x, p="$"):
    if isinstance(x, bool): return
    if isinstance(x, (int, float, Decimal)): nums.append((p, type(x).__name__, x))
    elif isinstance(x, dict):
        for k, v in x.items(): walk(v, p + "." + str(k))
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x): walk(v, p + f"[{i}]")
walk(pl)
print("M2 numeric leaves", len(nums), collections.Counter(t for _, t, _ in nums), nums[:2])
try:
    E.canonical_json(pl); print("M2 canonical_json ACCEPTED")
except Exception as ex: print("M2 canonical_json raised", type(ex).__name__, str(ex)[:110])
print("AuditEnvelope fields:", list(E.AuditEnvelope.model_fields))
print("EFFECTIVE_CONFIG spec:", E.EVENT_REGISTRY[E.EventType.EFFECTIVE_CONFIG_RENDERED])
# M3
try: print("M3 P1.3:", L.canonical_bytes({"b": 1, "a": Decimal("0.050"), "c": True}))
except Exception as ex: print("M3 P1.3 raised", type(ex).__name__)
try: print("M3 P1.4:", E.canonical_bytes({"b": 1, "a": "0.050", "c": True}))
except Exception as ex: print("M3 P1.4 raised", type(ex).__name__)
# M1 fields vs columns
sql = Path("migrations/0001_initial.sql").read_text(encoding="utf-8")
mt = re.search(r"CREATE TABLE (?:IF NOT EXISTS )?trading\.audit_log\s*\((.*?)\n\);", sql, re.S)
cols = [l.strip().split()[0] for l in mt.group(1).splitlines() if l.strip() and not l.strip().startswith(("--","CONSTRAINT","CHECK","PRIMARY","UNIQUE","FOREIGN"))]
print("audit_log cols", len(cols), cols)
print("envelope minus cols:", sorted(set(E.AuditEnvelope.model_fields) - set(cols)), " cols minus envelope:", sorted(set(cols) - set(E.AuditEnvelope.model_fields)))
# registry
print("event types", len(E.EventType), "effectful", len(E.EFFECTFUL_EVENT_TYPES), "repro", len(E.REPRODUCIBLE_EVENT_TYPES))
prod = collections.defaultdict(list)
for t, s in E.EVENT_REGISTRY.items(): prod[getattr(s.producer,'value',s.producer)].append(t.value)
for k in sorted(prod): print("  ", k, prod[k])
print("M4 AuditEvent in models:", hasattr(M, "AuditEvent"))
print("OrderType", [x.value for x in M.OrderType]); print("InvalidationKind", [x.value for x in M.InvalidationKind])
print("RiskDecision", [x.value for x in M.RiskDecision]); print("RuleAction", [x.value for x in L.RuleAction])
print("DomainError subclasses", len([v for v in vars(M).values() if inspect.isclass(v) and issubclass(v, M.DomainError) and v is not M.DomainError]))
