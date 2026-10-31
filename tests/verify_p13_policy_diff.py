"""SPEC-P1.3.1-POLICY-DIFF v0.3.4 verification — STAGE-1-GAP-AUDIT §10 condition 12.

Two halves:

  A. PINS (§7.2). Every constitutional rule's governed fields, not only its value, are pinned
     against a literal table in this file, and `scope` and `mode` are pinned for all 47 rules. A pin
     failure means this policy differs from the table, and the remedy is a reviewed change to the
     table, never to the check. Every pin failure message begins `<RULE-ID>.<field>`.

  B. DIFF AND APPROVAL (§7.4, §7.6). Each required case asserts direction and basis, and the full
     set of records produced.

NO BARE `assert` ANYWHERE IN THIS FILE: `require()` raises unconditionally, so the suite holds
under `python -O` (X5 GAP-2). Run both ways in CI. The harnesses read the `FAILED` lines, one per
message line, so a kill is credited to a named test (§7.1 rule 3).
"""
import ast
import copy
import hashlib
import inspect
import os
import shutil
import subprocess
import sys
import tempfile
import weakref
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

import yaml
from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1
from cryptography.hazmat.primitives.asymmetric.ec import generate_private_key as ec_key
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

_SLOW_YAML_LOAD = yaml.safe_load
_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
_YAML_DUMPER = getattr(yaml, "CSafeDumper", yaml.SafeDumper)
_parsed: dict[str, object] = {}


def _fast_yaml_load(text):
    """The suite parses the same few files over a thousand times. Test speed only."""
    if text not in _parsed:
        _parsed[text] = yaml.load(text, Loader=_YAML_LOADER)  # noqa: S506 - a safe loader
    return copy.deepcopy(_parsed[text])


yaml.safe_load = _fast_yaml_load

from audit.events import canonical_json  # noqa: E402
from config import loader as L  # noqa: E402
from config import policy_diff as P  # noqa: E402

PASS: list[str] = []
FAIL: list[tuple[str, str]] = []
SEEN_BASES: set[str] = set()


def require(cond: bool, msg: str) -> None:
    """Unconditional check. Never an `assert` - see the module docstring."""
    if not cond:
        raise AssertionError(msg)


def raises(exc, fn, label="", match="", exact=False):
    """Requires `exc`; `exact` refuses a subclass, `match` a substring of the message."""
    try:
        fn()
    except exc as e:
        require(not exact or type(e) is exc, f"{label}expected exactly {exc.__name__}, "
                                             f"got {type(e).__name__}: {e}")
        require(match in str(e), f"{label}expected {match!r} in: {e}")
        return e
    except Exception as e:  # noqa: BLE001
        raise AssertionError(f"{label}expected {exc.__name__}, got {type(e).__name__}: {e}") from e
    raise AssertionError(f"{label}expected {exc.__name__}, nothing raised")


# The REAL file, read through the real loader, so a mutation of config/policy.yaml reaches
# both the pins and the diff fixtures.
CFG = L.PolicyLoader(ROOT / "config").load(require_signature=False)
DOC = CFG.document
RAW = yaml.safe_load((ROOT / "config" / "policy.yaml").read_text(encoding="utf-8"))

E, M = "enforce", "monitor"
DENY, KILL, MODIFY = "DENY", "KILL", "MODIFY"
LO, TI, NE, UN = (P.Direction.LOOSENS, P.Direction.TIGHTENS, P.Direction.NEUTRAL,
                  P.Direction.UNDECIDABLE)

# =============================================================================
# A. PINS (§7.2)
# =============================================================================
# (a) A rule is constitutional when its authority cites [CONST...] or is marked IMMUTABLE.
# Columns: action, mode, comparison, scope, threshold, on_missing_input, kill_scope,
#          allowed_values, allowed_values_emergency, disallowed_values,
#          (basis, window, timing), inputs
CONSTITUTION = {
    "EXP-001": (DENY, E, "lte", "pool", D("0.050"), DENY, None, None, None, None,
                ("pool_nav", "point_in_time", "pre_trade_intended_post_fill"),
                {"pool_nav", "position_market_value", "intended_fill_quantity", "mark_price"}),
    "EXP-002": (DENY, E, "lte", "pool", D("0.200"), DENY, None, None, None, None,
                ("pool_nav", "point_in_time", "pre_trade_intended_post_fill"),
                {"pool_nav", "sector_classification", "position_market_value",
                 "intended_fill_quantity"}),
    "EXP-003": (DENY, E, "lte", "pool", D("2.0"), DENY, None, None, None, None,
                ("equity", "point_in_time", "pre_trade_intended_post_fill"),
                {"equity", "gross_exposure_value"}),
    "EXP-004": (DENY, E, "lte", "pool", D("1.0"), DENY, None, None, None, None,
                ("equity", "point_in_time", "pre_trade_intended_post_fill"),
                {"equity", "net_exposure_value"}),
    "LOSS-001": (DENY, E, "lte", "pool_and_consolidated", D("0.020"), DENY, None, None, None,
                 None, ("nav_at_session_start", "session", "continuous"),
                 {"nav_at_session_start", "nav_current", "realised_pnl_session",
                  "unrealised_pnl_session"}),
    "LOSS-002": (DENY, E, "lte", "pool_and_consolidated", D("0.050"), DENY, None, None, None,
                 None, ("nav_at_week_start", "sessions:5", "continuous"),
                 {"nav_at_week_start", "nav_current", "realised_pnl_week",
                  "unrealised_pnl_week"}),
    "LOSS-003": (KILL, E, "lte", "pool", D("0.100"), KILL, "POOL", None, None, None,
                 ("peak_nav_from_audit_trail", "since_peak", "continuous"),
                 {"peak_nav_from_audit_trail", "nav_current"}),
    "LOSS-004": (KILL, E, "lte", "consolidated", D("0.100"), KILL, "GLOBAL", None, None, None,
                 ("consolidated_peak_nav_from_audit_trail", "since_peak", "continuous"),
                 {"consolidated_peak_nav_from_audit_trail", "consolidated_nav_current",
                  "fx_rate"}),
    "SIZE-001": (MODIFY, E, "lte", "pool", D("0.010"), DENY, None, None, None, None,
                 ("pool_nav", "point_in_time", "pre_trade_intended_post_fill"),
                 {"pool_nav", "entry_price", "stop_price", "intended_fill_quantity"}),
    "LIQ-001": (MODIFY, E, "lte", "instrument", D("0.010"), DENY, None, None, None, None,
                ("addv_20_session_median", "sessions:20", "pre_trade_intended_post_fill"),
                {"addv_20_session_median", "intended_fill_quantity", "mark_price"}),
    "RATE-001": (DENY, E, "lte", "global", D("20"), DENY, None, None, None, None,
                 ("order_count", "rolling_seconds:60", "pre_trade"),
                 {"order_submission_timestamps"}),
    "RATE-002": (DENY, E, "lte", "strategy", D("10"), DENY, None, None, None, None,
                 ("order_count", "rolling_seconds:60", "pre_trade"),
                 {"order_submission_timestamps", "strategy_id"}),
    "STOP-001": (DENY, E, "eq", "instrument", D("2.5"), DENY, None, None, None, None,
                 ("atr_14_completed_bars", "sessions:14", "at_entry"),
                 {"entry_price", "atr_14_completed_bars"}),
    "EXEC-001": (DENY, E, "in", "instrument", None, DENY, None, ("LIMIT",),
                 ("MARKET", "LIMIT"), None, ("order_type", "point_in_time", "pre_trade"),
                 {"order_type", "is_emergency_exit"}),
    "DATA-001": (DENY, E, "lte", "instrument", D("600"), DENY, None, None, None, None,
                 ("seconds_since_as_of", "point_in_time", "pre_trade"),
                 {"data_as_of", "evaluation_time"}),
    "REGIME-001": (DENY, E, "not_in", "market", None, DENY, None, None, None, ("UNKNOWN",),
                   ("regime_label", "session", "pre_trade"), {"regime_label"}),
    "KILL-001": (DENY, E, "in", "global", None, DENY, None, ("ARMED",), None, None,
                 ("kill_switch_state", "point_in_time", "pre_trade"), {"kill_switch_state"}),
    "AUDIT-001": (DENY, E, "exists", "global", None, DENY, None, None, None, None,
                  ("audit_event_id", "point_in_time", "pre_trade"), {"audit_event_id"}),
    "LLM-001": (DENY, E, "eq", "global", None, DENY, None, (False,), None, None,
                ("llm_prompt_contains_portfolio_state", "point_in_time", "pre_llm_call"),
                {"llm_prompt_contains_portfolio_state"}),
    "LLM-002": (DENY, E, "exists", "global", None, DENY, None, None, None, None,
                ("sanitiser_version", "point_in_time", "pre_llm_call"),
                {"sanitiser_version", "content_is_sanitised"}),
}

# (b) `scope` and `mode` for all 47 rules. Every rule is `enforce` unless listed in MONITOR_RULES.
SCOPES = {
    "pool": ("EXP-001", "EXP-002", "EXP-003", "EXP-004", "EXP-005", "EXP-006", "LOSS-003",
             "SIZE-001", "CASH-001", "CASH-002", "PORT-001", "PORT-002", "TURN-001", "TURN-002",
             "RECON-001"),
    "instrument": ("SIZE-002", "LIQ-001", "STOP-001", "EXEC-001", "HOLD-001", "HOLD-002",
                   "HOLD-003", "EDGE-001", "INST-001", "INST-002", "DATA-001", "DATA-002",
                   "DATA-003"),
    "global": ("RATE-001", "FX-001", "KILL-001", "KILL-002", "AUDIT-001", "AUDIT-002", "LLM-001",
               "LLM-002", "LLM-003"),
    "market": ("UNIV-001", "UNIV-002", "UNIV-003", "UNIV-004", "UNIV-005", "REGIME-001"),
    "pool_and_consolidated": ("LOSS-001", "LOSS-002"),
    "consolidated": ("LOSS-004",),
    "strategy": ("RATE-002",),
}
MONITOR_RULES = {"CASH-002", "PORT-002"}
SCOPE_OF = {rid: scope for scope, rids in SCOPES.items() for rid in rids}


def _v(x):
    return None if x is None else getattr(x, "value", x)


def _pin(rid):
    (action, mode, cmp, scope, thr, omi, ks, av, ave, dv, meas, inputs) = CONSTITUTION[rid]
    r = DOC.rule(rid)
    pairs = [
        ("action", _v(r.action), action),
        ("mode", _v(r.mode), mode),
        ("comparison", _v(r.comparison), cmp),
        ("scope", _v(r.scope), scope),
        ("on_missing_input", _v(r.on_missing_input), omi),
        ("kill_scope", _v(r.kill_scope), ks),
        ("allowed_values", r.allowed_values, av),
        ("allowed_values_emergency",
         None if r.allowed_values_emergency is None else frozenset(r.allowed_values_emergency),
         None if ave is None else frozenset(ave)),
        ("disallowed_values", r.disallowed_values, dv),
        ("measurement", (r.measurement.basis, r.measurement.window, r.measurement.timing), meas),
        ("inputs", set(r.inputs), inputs),
        ("threshold_ref", r.threshold_ref, None),
        ("threshold_input", r.threshold_input, None),
        ("binds", r.binds, True),
    ]
    for name, got, want in pairs:
        require(got == want, f"{rid}.{name} is {got!r}; the table says {want!r}")
    got_t = None if r.threshold is None else D(str(r.threshold))
    require(got_t == thr, f"{rid}.threshold is {got_t}; the table says {thr}")


def _make_pin_test(rid):
    def t():
        _pin(rid)
    return t


for _rid in CONSTITUTION:
    globals()[f"t_pin_{_rid.replace('-', '_')}"] = _make_pin_test(_rid)


def t_constitutional_set_is_exactly_the_table():
    have = {r.id for r in DOC.rules if "[CONST" in r.authority or "IMMUTABLE" in r.authority}
    require(have == set(CONSTITUTION),
            f"constitutional rules {sorted(have)} != pinned {sorted(CONSTITUTION)}")


def t_scope_and_mode_pinned_for_every_rule():
    bad = []
    for r in DOC.rules:
        want_scope = SCOPE_OF.get(r.id)
        want_mode = M if r.id in MONITOR_RULES else E
        if r.scope.value != want_scope:
            bad.append(f"{r.id}.scope is {r.scope.value}; the table says {want_scope}")
        if r.mode.value != want_mode:
            bad.append(f"{r.id}.mode is {r.mode.value}; the table says {want_mode}")
    require(not bad, "\n".join(bad))


def t_pinned_rule_set_is_exactly_the_file():
    have = {r.id for r in DOC.rules}
    require(have == set(SCOPE_OF) and len(have) == 47,
            f"rule ids differ from the 47 pinned: {sorted(have ^ set(SCOPE_OF))}")


def t_exemption_scope_is_pinned():
    r = DOC.rule("KILL-002")
    require(r.action is L.RuleAction.ALLOW and r.mode is L.RuleMode.ENFORCE,
            f"KILL-002.action is {r.action.value}/{r.mode.value}; the table says ALLOW/enforce")
    require(set(r.exempts) == {"CASH-001", "CASH-002", "KILL-001", "HOLD-001", "TURN-001",
                               "TURN-002", "EXEC-001"}, f"KILL-002.exempts is {r.exempts}")
    others = [x.id for x in DOC.rules if x.exempts and x.id != "KILL-002"]
    require(not others, f"{(others or ['?'])[0]}.exempts: only KILL-002 may grant exemptions")


def t_kill_scope_rules_are_pinned():
    have = {r.id: _v(r.kill_scope) for r in DOC.rules
            if r.action is L.RuleAction.KILL or r.on_missing_input is L.RuleAction.KILL}
    want = {"LOSS-003": "POOL", "LOSS-004": "GLOBAL", "AUDIT-002": "GLOBAL"}
    for rid in sorted(set(have) | set(want)):
        require(have.get(rid) == want.get(rid),
                f"{rid}.kill_scope is {have.get(rid)}; the table says {want.get(rid)}")


def _approver_refs(mapping):
    return ((mapping.get("governance") or {}).get("signature") or {}).get("approver_key_refs")


def t_no_approver_is_listed():
    require(_approver_refs(RAW) is None, "governance.signature.approver_key_refs is present")
    fixture = _with_map(_raw(), (AB, JS))
    require(_approver_refs(fixture) is not None, "self-check: the fixture must list a map")


def _halt_rules(mapping):
    return {r["id"] for r in mapping.get("rules", ()) if r.get("action") == "HALT_ENTRIES"}


def _raw_merged(directory, market, environment):
    """The raw mapping of one combination. A policy using HALT_ENTRIES does not load yet."""
    names = [f"policy.market.{market}.yaml"] if market else []
    names += [f"policy.env.{environment}.yaml"] if environment else []
    names.append("policy.override.yaml")
    merged = yaml.safe_load((Path(directory) / "policy.yaml").read_text(encoding="utf-8"))
    for name in names:
        path = Path(directory) / name
        layer = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
        if layer:
            merged.update(layer)
    return merged


def t_halt_entries_rules_are_pinned():
    cfg = ROOT / "config"
    for market, environment in P.derive_combinations(cfg, cfg):
        extra = _halt_rules(_raw_merged(cfg, market, environment))
        require(not extra, f"{sorted(extra or ['?'])[0]}.action is HALT_ENTRIES in "
                           f"({market}, {environment}); no rule may use it before #17's edit")
    fixture = _raw()
    _rule_raw(fixture, "HOLD-001")["action"] = "HALT_ENTRIES"
    require(_halt_rules(fixture) == {"HOLD-001"}, "self-check: the same check must see HOLD-001")


# =============================================================================
# B. FIXTURES
# =============================================================================
_DROP = object()
_TMP = tempfile.TemporaryDirectory(prefix="p13diff")
weakref.finalize(_TMP, _TMP.cleanup)
_serial = [0]


def _raw():
    return copy.deepcopy(RAW)


def _rule_raw(doc, rid):
    for r in doc["rules"]:
        if r["id"] == rid:
            return r
    raise KeyError(rid)


def _apply(doc, rid, fields):
    r = _rule_raw(doc, rid)
    for k, v in fields.items():
        if v is _DROP:
            r.pop(k, None)
        else:
            r[k] = v
    return doc


def _edit(rid, **fields):
    return _apply(_raw(), rid, fields)


def _set_key(doc, dotted, value):
    node = doc
    parts = dotted.split(".")
    for p in parts[:-1]:
        node = node.setdefault(p, {})
    if value is _DROP:
        del node[parts[-1]]
    else:
        node[parts[-1]] = value
    return doc


def _new_rule(rid, *, action="DENY", mode="enforce", base="EXP-005", **fields):
    r = copy.deepcopy(_rule_raw(RAW, base))
    r.update(id=rid, action=action, mode=mode, **fields)
    return r


def _added(*rules):
    doc = _raw()
    doc["rules"].extend(rules)
    return doc


def _expect(new, want, *, old=None, **layers):
    """Requires exactly these records: {path: (direction, basis)}. Returns the diff."""
    d = P.diff_policies(RAW if old is None else old, new, **layers)
    got = {c.path: (c.direction, c.basis) for c in d.changes}
    require(len(got) == len(d.changes), f"two records on one path: {list(d.changes)}")
    require(got == want, f"records differ.\n  got  {got}\n  want {want}")
    SEEN_BASES.update(c.basis for c in d.changes)
    return d


def _action(old, new, direction, basis):
    got = P.action_direction(old, new)
    require(got == (direction, basis), f"action_direction {old}->{new} is {got}")
    SEEN_BASES.add(basis)


def _dir(doc, **files):
    """A throwaway policy directory holding `doc`, plus layer files by dotted-safe keyword."""
    _serial[0] += 1
    d = Path(_TMP.name) / f"d{_serial[0]}"
    d.mkdir()
    (d / "policy.yaml").write_text(_dump(doc), encoding="utf-8")
    for key, content in files.items():
        text = "" if content is None else _dump(content)
        (d / f"policy.{key.replace('__', '.')}.yaml").write_text(text, encoding="utf-8")
    return d


def _dump(doc):
    return yaml.dump(doc, Dumper=_YAML_DUMPER, sort_keys=False)


class Key:
    """A test key, generated here, never a real one."""

    def __init__(self, name):
        self.name = name
        self.priv = Ed25519PrivateKey.generate()
        pub = self.priv.public_key()
        self.pem = pub.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        self.raw = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.ref = f"vault://kv/data/trading/approvers/{name}#public_key"
        self.pin = "sha256:" + hashlib.sha256(self.raw).hexdigest()

    def sign(self, digest):
        return P.ApprovalSignature(identity=self.name,
                                   signature_hex=self.priv.sign(digest.encode("ascii")).hex())


AB, JS, CD, ZZ = Key("ab"), Key("js"), Key("cd"), Key("zz")


def _with_map(doc, keys):
    doc["governance"]["signature"]["approver_key_refs"] = {
        k.name: {"ref": k.ref, "raw_key_sha256": k.pin} for k in keys}
    return doc


@contextmanager
def _vault(*keys, pem=None):
    table = {k.ref: k.pem for k in keys}
    table.update(pem or {})
    P.VAULT_RESOLVER = table.__getitem__
    try:
        yield
    finally:
        P.VAULT_RESOLVER = None


REQUEST = "01920000-0000-7000-8000-000000000001"
REQUEST_B = "01920000-0000-7000-8000-000000000002"


def _at(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def _signed(old_dir, new_dir, keys, *, request_id=REQUEST, at=None):
    at = at or _at(_now())
    digest = P.authorisation_digest(P.diff_policy_dirs(old_dir, new_dir), request_id, at)
    return [k.sign(digest) for k in keys], request_id, at


def _authorise(old_dir, new_dir, keys=(), *, request_id=REQUEST, at=None):
    approvals, rid, when = _signed(old_dir, new_dir, keys, request_id=request_id, at=at)
    return P.assert_policy_change_authorised(old_dir, new_dir, approvals, request_id=rid,
                                             requested_at=when)


def _hashes(directory):
    return {(m, e): L.PolicyLoader(directory).load(market=m, environment=e,
                                                   require_signature=False).content_hash
            for m, e in P.derive_combinations(directory, directory)}


class FakeStore:
    """The B6 store as P reads it."""

    def __init__(self, hashes, now=None, used=()):
        self.hashes = dict(hashes)
        self.now = now or datetime.now(timezone.utc)
        self.used = set(used)

    def in_force_hashes(self, conn):
        require(conn == "conn", "the adapter must get the writer's connection")
        return dict(self.hashes)

    def database_time(self, conn):
        return self.now

    def request_used(self, conn, request_id):
        return request_id in self.used


@contextmanager
def _store(store):
    P.IN_FORCE_STORE = store
    try:
        yield
    finally:
        P.IN_FORCE_STORE = None


def _current(auth, store, old_dir, new_dir):
    with _store(store):
        P.assert_authorisation_current(auth, "conn", old_dir, new_dir)


def _refused_with_one(new_doc):
    """Refused for one signed approval, accepted for two distinct enrolled identities."""
    old_doc = _with_map(_raw(), (AB, JS))
    a, b = _dir(old_doc), _dir(_with_map(copy.deepcopy(new_doc), (AB, JS)))
    with _vault(AB, JS):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB,)), "one approver: ")
        _authorise(a, b, (AB, JS))


def _zero_approvals(new_doc):
    auth = _authorise(_dir(_raw()), _dir(new_doc))
    require(auth.required_approvals == "0", f"required {auth.required_approvals}")


# ---- the five X5R-G9 mutations, through the diff (§7.3; not counted as mutation evidence) ------
X5R_G9 = {
    "EXP-002 action -> ALLOW": ("EXP-002", "action", {"action": "ALLOW"}, LO, "C-09"),
    "LOSS-001 mode -> monitor": ("LOSS-001", "mode", {"mode": "monitor"}, LO, "C-11"),
    "LOSS-004 threshold -> 20%": ("LOSS-004", "threshold", {"threshold": 0.200}, LO, "C-01"),
    "EXEC-001 allows MARKET": ("EXEC-001", "allowed_values",
                               {"allowed_values": ["LIMIT", "MARKET"]}, LO, "C-20"),
    "STOP-001 comparison -> lte": ("STOP-001", "comparison", {"comparison": "lte"}, UN, "C-08"),
}


def t_x5r_g9_each_mutation_is_gated():
    a = _dir(_with_map(_raw(), (AB, JS)))
    for label, (rid, field, edit, direction, basis) in X5R_G9.items():
        b = _dir(_with_map(_edit(rid, **edit), (AB, JS)))
        changes = [c for d in P.diff_policy_dirs(a, b) for c in d.changes]
        require(len(changes) == 3, f"{label}: expected one change in each of 3 combinations")
        for c in changes:
            require(c.path == f"rules.{rid}.{field}" and c.direction is direction
                    and c.basis == basis, f"{label}: {c}")
        with _vault(AB, JS):
            raises(L.PolicyGovernanceError, lambda bb=b: _authorise(a, bb, (AB,)),
                   f"{label}, one approver: ")
            raises(L.PolicyGovernanceError, lambda bb=b: _authorise(a, bb, (AB, AB)),
                   f"{label}, one identity twice: ")
            _authorise(a, b, (AB, JS))


# =============================================================================
# C. CLASSIFICATION (§7.4)
# =============================================================================
def t_c01():
    _expect(_edit("LOSS-004", threshold=0.20), {"rules.LOSS-004.threshold": (LO, "C-01")})
    _expect(_edit("EXP-001", threshold=0.04), {"rules.EXP-001.threshold": (TI, "C-01")})
    _expect(_edit("RATE-001", threshold=20.0), {"rules.RATE-001.threshold": (NE, "C-01")})
    new = _edit("TURN-002", threshold=0.02)
    _expect(new, {"rules.TURN-002.threshold": (TI, "C-01")})
    _zero_approvals(new)


def t_c02():
    _expect(_edit("PORT-001", threshold=0.10), {"rules.PORT-001.threshold": (LO, "C-02")})
    _expect(_edit("PORT-001", threshold=0.30), {"rules.PORT-001.threshold": (TI, "C-02")})
    _expect(_edit("HOLD-001", threshold=30), {"rules.HOLD-001.threshold": (TI, "C-02")})
    _expect(_edit("EDGE-001", threshold=1.5), {"rules.EDGE-001.threshold": (LO, "C-02")})


def t_c03():
    _expect(_edit("RECON-001", threshold=1), {"rules.RECON-001.threshold": (UN, "C-03")})
    _expect(_edit("RECON-001", threshold=0.0), {"rules.RECON-001.threshold": (NE, "C-03")})
    _expect(_edit("STOP-001", threshold=3.0), {"rules.STOP-001.threshold": (UN, "C-03")})


def t_c04():
    _expect(_edit("SIZE-002", threshold=1), {"rules.SIZE-002.threshold": (UN, "C-04")})


def t_c05():
    _expect(_edit("EXP-001", threshold=_DROP, threshold_ref="portfolio.max_position_pct"),
            {"rules.EXP-001.threshold": (UN, "C-05"), "rules.EXP-001.threshold_ref": (UN, "C-05")})


def t_c06():
    _expect(_edit("UNIV-004", threshold_ref="universe.{market}.min_reported_quarters"),
            {"rules.UNIV-004.threshold_ref": (UN, "C-06")})


def t_c07():
    r = _rule_raw(RAW, "CASH-001")
    _expect(_edit("CASH-001", threshold_input="cash", inputs=[*r["inputs"], "cash"]),
            {"rules.CASH-001.threshold_input": (UN, "C-07"), "rules.CASH-001.inputs": (TI, "C-27")})


def t_c08():
    for rid, cmp in (("STOP-001", "lte"), ("EXP-001", "lt"), ("EXP-001", "eq"), ("EDGE-001", "gt"),
                     ("CASH-001", "lt")):
        d = _expect(_edit(rid, comparison=cmp), {f"rules.{rid}.comparison": (UN, "C-08")})
        require(d.requires_two_person, f"{rid} {cmp}: an UNDECIDABLE change must be gated")
    _expect(_edit("EXP-001", comparison="lt", threshold=0.10),
            {"rules.EXP-001.comparison": (UN, "C-08"), "rules.EXP-001.threshold": (UN, "C-08")})
    _expect(_edit("EXEC-001", comparison="not_in", allowed_values=_DROP,
                  disallowed_values=["MARKET"]),
            {"rules.EXEC-001.comparison": (UN, "C-08"),
             "rules.EXEC-001.allowed_values": (UN, "C-08"),
             "rules.EXEC-001.disallowed_values": (UN, "C-08")})
    _expect(_edit("UNIV-004", comparison="gt", threshold_ref="universe.{market}.min_reported_quarters"),
            {"rules.UNIV-004.comparison": (UN, "C-08"),
             "rules.UNIV-004.threshold_ref": (UN, "C-08")})
    _expect(_edit("CASH-001", comparison="lt", threshold_input="intended_notional"),
            {"rules.CASH-001.comparison": (UN, "C-08"),
             "rules.CASH-001.threshold_input": (UN, "C-08")})
    _expect(_edit("INST-001", comparison="not_in",
                  allowed_values_ref="instrument_allowlist.permanently_banned"),
            {"rules.INST-001.comparison": (UN, "C-08"),
             "rules.INST-001.allowed_values_ref": (UN, "C-08")})


def t_c09():
    _expect(_edit("EXP-002", action="ALLOW"), {"rules.EXP-002.action": (LO, "C-09")})
    _expect(_edit("SIZE-001", action="DENY", modify=_DROP),
            {"rules.SIZE-001.action": (TI, "C-09"), "rules.SIZE-001.modify": (TI, "C-18")})
    new = _edit("REGIME-001", action="KILL", kill_scope="POOL")
    _expect(new, {"rules.REGIME-001.action": (TI, "C-09"),
                  "rules.REGIME-001.kill_scope": (TI, "C-18")})
    _zero_approvals(new)
    for old, to, direction in (("KILL", "HALT_ENTRIES", LO), ("HALT_ENTRIES", "MODIFY", LO),
                               ("MODIFY", "HALT_ENTRIES", TI), ("HALT_ENTRIES", "KILL", TI),
                               ("HALT_ENTRIES", "DENY", LO), ("DENY", "HALT_ENTRIES", TI),
                               ("DENY", "DENY", NE)):
        _action(old, to, direction, "C-09")


def t_c10():
    _action("FOO", "DENY", UN, "C-10")
    _action("DENY", "FOO", UN, "C-10")


def t_c11():
    _expect(_edit("LOSS-001", mode="monitor"), {"rules.LOSS-001.mode": (LO, "C-11")})
    _expect(_edit("KILL-002", mode="monitor"), {"rules.KILL-002.mode": (LO, "C-11")})
    _expect(_edit("PORT-002", mode="enforce"), {"rules.PORT-002.mode": (TI, "C-11")})
    _expect(_raw(), {"rules.LOSS-003.mode": (TI, "C-11"),
                     "rules.LOSS-004.kill_displaced_by.LOSS-003": (UN, "C-40")},
            old=_edit("LOSS-003", mode="monitor"))


def t_c12():
    _expect(_edit("LOSS-001", scope="pool"), {"rules.LOSS-001.scope": (LO, "C-12")})
    _expect(_edit("LOSS-004", scope="pool_and_consolidated"),
            {"rules.LOSS-004.scope": (TI, "C-12")})
    new = _edit("LOSS-003", scope="pool_and_consolidated")
    _expect(new, {"rules.LOSS-003.scope": (TI, "C-12"),
                  "rules.LOSS-004.kill_displaced_by.LOSS-003": (UN, "C-40")})
    _refused_with_one(new)
    require(P.scope_direction("pool", "pool")[:2] == (NE, "C-12"), "same scope is NEUTRAL")


SCOPE_ORDER = {("pool", "pool_and_consolidated"), ("consolidated", "pool_and_consolidated")}
SCOPE_TABLE = {
    ("global", "strategy"): "R1", ("global", "market"): "R1", ("global", "instrument"): "R1",
    ("global", "pool"): "R1", ("global", "consolidated"): "R3",
    ("global", "pool_and_consolidated"): "R4", ("strategy", "market"): "R2",
    ("strategy", "instrument"): "R2", ("strategy", "pool"): "R2",
    ("strategy", "consolidated"): "R1", ("strategy", "pool_and_consolidated"): "R4",
    ("market", "instrument"): "R1", ("market", "pool"): "R3", ("market", "consolidated"): "R1",
    ("market", "pool_and_consolidated"): "R4", ("instrument", "pool"): "R1",
    ("instrument", "consolidated"): "R1", ("instrument", "pool_and_consolidated"): "R4",
    ("pool", "consolidated"): "R1",
}


def t_c13():
    for rid, scope, why in (("RATE-002", "global", "R1"), ("EXP-001", "consolidated", "R1"),
                            ("UNIV-001", "pool", "R3"), ("SIZE-002", "strategy", "R2"),
                            ("RATE-001", "pool_and_consolidated", "R4")):
        d = _expect(_edit(rid, scope=scope), {f"rules.{rid}.scope": (UN, "C-13")})
        require(why in d.changes[0].reason, f"{rid}: reason {d.changes[0].reason}")


def t_every_scope_pair_is_classified():
    scopes = sorted({s.value for s in L.RuleScope})
    require(len(scopes) == 7, f"{len(scopes)} scopes")
    for a in scopes:
        for b in scopes:
            got = P.scope_direction(a, b)
            SEEN_BASES.add(got[1])
            if a == b:
                require(got[:2] == (NE, "C-12"), f"{a}->{b}: {got}")
            elif (a, b) in SCOPE_ORDER:
                require(got[:2] == (TI, "C-12"), f"{a}->{b}: {got}")
            elif (b, a) in SCOPE_ORDER:
                require(got[:2] == (LO, "C-12"), f"{a}->{b}: {got}")
            else:
                why = SCOPE_TABLE.get((a, b)) or SCOPE_TABLE[(b, a)]
                require(got == (UN, "C-13", why), f"{a}->{b}: {got}")


def t_c14():
    a = _edit("EXP-001", severity="LOW")
    _expect(a, {"rules.EXP-001.severity": (NE, "C-14")})
    b = _edit("HOLD-002", severity="CRITICAL")
    _expect(b, {"rules.HOLD-002.severity": (NE, "C-14")})
    _zero_approvals(a)


def t_c15():
    _expect(_edit("EXP-002", action="ALLOW", severity="LOW"),
            {"rules.EXP-002.action": (LO, "C-09"), "rules.EXP-002.severity": (LO, "C-15")})
    _expect(_edit("SIZE-001", action="DENY", modify=_DROP, severity="LOW"),
            {"rules.SIZE-001.action": (TI, "C-09"), "rules.SIZE-001.modify": (TI, "C-18"),
             "rules.SIZE-001.severity": (TI, "C-15")}, old=_edit("SIZE-001", severity="HIGH"))


def t_c16():
    new = _edit("REGIME-001", on_missing_input="KILL")
    _expect(new, {"rules.REGIME-001.on_missing_input": (TI, "C-16")})
    _zero_approvals(new)
    new = _edit("FX-001", on_missing_input="KILL")
    _expect(new, {"rules.FX-001.on_missing_input": (TI, "C-16"),
                  "rules.LOSS-004.kill_displaced_by.FX-001": (UN, "C-40")})
    _refused_with_one(new)
    _expect(_edit("AUDIT-001", on_missing_input="KILL"),
            {"rules.AUDIT-001.on_missing_input": (TI, "C-16"),
             "rules.AUDIT-002.kill_displaced_by.AUDIT-001": (UN, "C-40"),
             "rules.LOSS-004.kill_displaced_by.AUDIT-001": (UN, "C-40")})
    _expect(_edit("LOSS-003", on_missing_input="DENY"),
            {"rules.LOSS-003.on_missing_input": (LO, "C-16"),
             "rules.LOSS-004.kill_displaced_by.LOSS-003": (UN, "C-40")})


def t_c17():
    _expect(_edit("LOSS-004", kill_scope="POOL"), {"rules.LOSS-004.kill_scope": (LO, "C-17")})
    _expect(_edit("LOSS-003", kill_scope="GLOBAL"), {"rules.LOSS-003.kill_scope": (TI, "C-17")})


def t_c18():
    _expect(_edit("LOSS-003", action="DENY", kill_scope=_DROP),
            {"rules.LOSS-003.action": (LO, "C-09"), "rules.LOSS-003.kill_scope": (LO, "C-18"),
             "rules.LOSS-004.kill_displaced_by.LOSS-003": (UN, "C-40")})
    new = _edit("CASH-001", action="KILL", kill_scope="POOL")
    _expect(new, {"rules.CASH-001.action": (TI, "C-09"), "rules.CASH-001.kill_scope": (TI, "C-18"),
                  "rules.LOSS-004.kill_displaced_by.CASH-001": (UN, "C-40")})
    _refused_with_one(new)


def t_c19():
    _expect(_edit("EXP-001", kill_scope="POOL"), {"rules.EXP-001.kill_scope": (UN, "C-19")})


def t_c20():
    _expect(_edit("EXEC-001", allowed_values=["LIMIT", "MARKET"]),
            {"rules.EXEC-001.allowed_values": (LO, "C-20")})
    _expect(_edit("INST-002", allowed_values=["ACTIVE", "HALTED"]),
            {"rules.INST-002.allowed_values": (LO, "C-20")})
    _expect(_edit("KILL-001", allowed_values=["ARMED", "TRIPPED"]),
            {"rules.KILL-001.allowed_values": (LO, "C-20")})
    _expect(_edit("EXEC-001", allowed_values=["MARKET"]),
            {"rules.EXEC-001.allowed_values": (UN, "C-20")})


def t_c21():
    _expect(_edit("LLM-001", allowed_values=[True]), {"rules.LLM-001.allowed_values": (UN, "C-21")})


def t_c22():
    _expect(_edit("REGIME-001", disallowed_values=["UNKNOWN", "BEAR"]),
            {"rules.REGIME-001.disallowed_values": (TI, "C-22")})
    _expect(_edit("REGIME-001", disallowed_values=["BEAR"]),
            {"rules.REGIME-001.disallowed_values": (UN, "C-22")})


def t_c23():
    _expect(_edit("EXEC-001", disallowed_values=["MARKET"]),
            {"rules.EXEC-001.disallowed_values": (UN, "C-23")})


def t_c24():
    _expect(_edit("EXEC-001", allowed_values_emergency=["MARKET", "LIMIT", "STOP"]),
            {"rules.EXEC-001.allowed_values_emergency": (LO, "C-24")})
    _expect(_edit("EXEC-001", allowed_values_emergency=["LIMIT"]),
            {"rules.EXEC-001.allowed_values_emergency": (TI, "C-24")})


def t_c25():
    _expect(_edit("INST-001", allowed_values_ref="instrument_allowlist.read_only"),
            {"rules.INST-001.allowed_values_ref": (UN, "C-25")})


def t_c26():
    r = _rule_raw(RAW, "KILL-002")
    _expect(_edit("KILL-002", exempts=[*r["exempts"], "EXP-001"]),
            {"rules.KILL-002.exempts": (LO, "C-26"),
             "rules.EXP-001.exempted_by.KILL-002": (LO, "C-36")})
    _expect(_edit("KILL-002", exempts=[x for x in r["exempts"] if x != "CASH-001"]),
            {"rules.KILL-002.exempts": (TI, "C-26")})


def t_c27():
    r = _rule_raw(RAW, "EXP-001")
    _expect(_edit("EXP-001", inputs=[*r["inputs"], "fx_rate"]),
            {"rules.EXP-001.inputs": (TI, "C-27")})
    d = _expect(_edit("EXP-001", inputs=[x for x in r["inputs"] if x != "mark_price"]),
                {"rules.EXP-001.inputs": (LO, "C-27")})
    require("mark_price" in d.changes[0].reason, f"reason: {d.changes[0].reason}")
    _expect(_edit("EXP-001", inputs=[x for x in r["inputs"] if x != "mark_price"] + ["fx_rate"]),
            {"rules.EXP-001.inputs": (UN, "C-27")})
    k = _rule_raw(RAW, "LOSS-003")
    _expect(_edit("LOSS-003", inputs=[*k["inputs"], "fx_rate"]),
            {"rules.LOSS-003.inputs": (TI, "C-27"),
             "rules.LOSS-004.kill_displaced_by.LOSS-003": (UN, "C-40")})


def t_c28():
    r = _rule_raw(RAW, "LOSS-002")
    _expect(_edit("LOSS-002", measurement={"basis": "nav_current", "window": "sessions:3",
                                           "timing": "end_of_session"}),
            {f"rules.LOSS-002.measurement.{k}": (UN, "C-28") for k in r["measurement"]})


def t_c29():
    m = _rule_raw(RAW, "EXP-006")["modify"]
    _expect(_edit("EXP-006", modify={**m, "to": 0.06}), {"rules.EXP-006.modify.to": (LO, "C-29")})
    _expect(_edit("EXP-006", modify={**m, "to": 0.03}), {"rules.EXP-006.modify.to": (TI, "C-29")})


def t_c30():
    m = _rule_raw(RAW, "SIZE-001")["modify"]
    _expect(_edit("SIZE-001", modify={**m, "to": "another_symbol"}),
            {"rules.SIZE-001.modify.to": (UN, "C-30")})
    _expect(_edit("SIZE-001", modify={**m, "target": "other_quantity"}),
            {"rules.SIZE-001.modify.target": (UN, "C-30")})
    base = _edit("SIZE-001", modify={"target": "order_quantity", "to": 1})
    new = _edit("SIZE-001", modify={"target": "order_quantity", "to": 2})
    _expect(new, {"rules.SIZE-001.modify.to": (UN, "C-30")}, old=base)


def t_c31():
    _expect(_edit("EXP-001", authority="ADR-14"), {"rules.EXP-001.authority": (UN, "C-31")})


def t_c32():
    new = _edit("EXP-001", description="A reworded description of this limit.", notes="reworded")
    _expect(new, {"rules.EXP-001.description": (NE, "C-32"), "rules.EXP-001.notes": (NE, "C-32")})
    _zero_approvals(new)


def _without(rid):
    doc = _raw()
    doc["rules"] = [r for r in doc["rules"] if r["id"] != rid]
    return doc


def t_c33():
    _expect(_without("EXP-002"), {"rules.EXP-002": (LO, "C-33")})
    _expect(_without("KILL-002"), {"rules.KILL-002": (LO, "C-33")})
    renamed = _raw()
    _apply(renamed, "EXP-001", {"id": "EXP-007", "threshold": 0.08})
    d = _expect(renamed, {"rules.EXP-001": (LO, "C-33"), "rules.EXP-007": (TI, "C-34")})
    require(d.requires_two_person, "a rename must be gated")


def t_c34():
    _expect(_added(_new_rule("EXP-009")), {"rules.EXP-009": (TI, "C-34")})
    _expect(_added(_new_rule("HOLD-009", base="HOLD-001")), {"rules.HOLD-009": (TI, "C-34")})
    predicate = dict(kill_scope="POOL", on_missing_input="KILL")
    new = _added(_new_rule("KILL-003", action="KILL", base="LOSS-004", **predicate))
    _expect(new, {"rules.KILL-003": (TI, "C-34"),
                  "rules.LOSS-004.kill_displaced_by.KILL-003": (UN, "C-40")})
    _refused_with_one(new)
    _expect(_added(_new_rule("TURN-009", action="KILL", kill_scope="POOL")),
            {"rules.TURN-009": (TI, "C-34")})


def t_c35():
    _expect(_added(_new_rule("EXP-009", mode="monitor")), {"rules.EXP-009": (NE, "C-35")})
    _expect(_added(_new_rule("EXP-009", action="ALLOW")), {"rules.EXP-009": (NE, "C-35")})


def _exempting(mode):
    r = _new_rule("KILL-003", action="ALLOW", mode=mode, base="AUDIT-001",
                  exempts=["LOSS-003", "LOSS-004"])
    return _added(r)


def t_c36():
    want = {"rules.KILL-003": (NE, "C-35"), "rules.LOSS-003.exempted_by.KILL-003": (LO, "C-36"),
            "rules.LOSS-004.exempted_by.KILL-003": (LO, "C-36")}
    _expect(_exempting("enforce"), want)
    _refused_with_one(_exempting("enforce"))
    _expect(_exempting("monitor"), want)
    # A new rule exempted by a new grantor still gets its record.
    grantor = _new_rule("KILL-003", action="ALLOW", base="AUDIT-001", exempts=["EXP-009"])
    _expect(_added(_new_rule("EXP-009"), grantor),
            {"rules.EXP-009": (TI, "C-34"), "rules.KILL-003": (NE, "C-35"),
             "rules.EXP-009.exempted_by.KILL-003": (LO, "C-36")})


def t_c37():
    for key, value, direction in (
            ("universe.US.min_price_usd", "1.00", LO), ("cost.assumed_round_trip_bps.US", 5, LO),
            ("cost.assumed_round_trip_bps.US", 40, TI), ("portfolio.max_position_pct", 0.08, LO),
            ("portfolio.min_cash_pct", 0.10, LO), ("account.enforce_settled_cash", False, LO),
            ("llm.gate_width", 30, LO), ("holding.min_sessions", 30, TI),
            ("holding.min_sessions", 1, LO), ("turnover.max_nav_traded_pct_per_session", 0.02, TI),
            ("metadata.description", "reworded", NE), ("policy_version", "0.1.1", NE)):
        _expect(_set_key(_raw(), key, value), {key: (direction, "C-37")})
    tradeable = list(RAW["instrument_allowlist"]["tradeable"])
    _expect(_set_key(_raw(), "instrument_allowlist.tradeable", [*tradeable, "ETF"]),
            {"instrument_allowlist.tradeable": (LO, "C-37")})
    banned = list(RAW["instrument_allowlist"]["permanently_banned"])
    _expect(_set_key(_raw(), "instrument_allowlist.permanently_banned",
                     [x for x in banned if x != "OPTION"]),
            {"instrument_allowlist.permanently_banned": (LO, "C-37")})
    # A set compares as a set: reordering is not a change (§2 row 7).
    _expect(_set_key(_raw(), "instrument_allowlist.permanently_banned", list(reversed(banned))), {})
    _expect(_set_key(_raw(), "cost.assumed_round_trip_bps.US", 25.0),
            {"cost.assumed_round_trip_bps.US": (NE, "C-37")})


def t_c38():
    _expect(_set_key(_raw(), "portfolio.max_gross_override", 1.5),
            {"portfolio.max_gross_override": (UN, "C-38")})
    _expect(_set_key(_raw(), "universe.US.min_price_usd", _DROP),
            {"universe.US.min_price_usd": (LO, "C-38")})
    _expect(_set_key(_raw(), "metadata.description", _DROP),
            {"metadata.description": (NE, "C-38")})


def t_c39():
    _expect(_set_key(_raw(), "schedule.US.pipeline_utc", "02:00"),
            {"schedule.US.pipeline_utc": (UN, "C-39")})
    _expect(_set_key(_raw(), "instrument_allowlist.tradeable", ["ETF"]),
            {"instrument_allowlist.tradeable": (UN, "C-39")})
    first = _set_key(_raw(), "turnover.min_sessions_between_reentry", 5)
    _expect(first, {"turnover.min_sessions_between_reentry": (UN, "C-38")})
    second = _set_key(copy.deepcopy(first), "turnover.min_sessions_between_reentry", 0)
    _expect(second, {"turnover.min_sessions_between_reentry": (UN, "C-39")}, old=first)
    key = "kill_switch.requires_human_to_re_enable"
    _expect(_set_key(_raw(), key, "no"), {key: (UN, "C-39")}, old=_set_key(_raw(), key, "yes"))
    key = "universe.US.min_price_usd"
    _expect(_set_key(_raw(), key, "abc"), {key: (UN, "C-39")})
    key = "instrument_allowlist.tradeable"
    _expect(_set_key(_raw(), key, "ETF"), {key: (UN, "C-39")})


def t_c40():
    base = _edit("EXP-005", action="KILL", kill_scope="POOL", threshold=_DROP,
                 threshold_ref="portfolio.max_position_pct")
    new = _set_key(copy.deepcopy(base), "portfolio.max_position_pct", 0.04)
    _expect(new, {"portfolio.max_position_pct": (TI, "C-37"),
                  "rules.LOSS-004.kill_displaced_by.EXP-005": (UN, "C-40")}, old=base)
    exempts = [*_rule_raw(RAW, "KILL-002")["exempts"], "LOSS-003"]
    base = _edit("KILL-002", exempts=exempts)
    _expect(_raw(), {"rules.KILL-002.exempts": (TI, "C-26"),
                     "rules.LOSS-004.kill_displaced_by.LOSS-003": (UN, "C-40")}, old=base)
    # Trigger 3 reads allowed_values_ref too.
    base = _edit("INST-001", action="KILL", kill_scope="POOL")
    new = _set_key(copy.deepcopy(base), "portfolio.max_position_pct", 0.04)
    _expect(new, {"portfolio.max_position_pct": (TI, "C-37"),
                  "rules.LOSS-004.kill_displaced_by.INST-001": (UN, "C-40")}, old=base)
    # A NEUTRAL config record is not a trigger.
    new = _set_key(copy.deepcopy(base), "metadata.description", "reworded")
    _expect(new, {"metadata.description": (NE, "C-37")}, old=base)
    # A NEUTRAL record on the rule is not a trigger.
    _expect(_edit("LOSS-003", severity="LOW"), {"rules.LOSS-003.severity": (NE, "C-14")})
    # A monitor rule never binds, so it displaces nothing.
    base = _edit("LOSS-003", mode="monitor")
    new = _edit("LOSS-003", mode="monitor", threshold=0.08)
    _expect(new, {"rules.LOSS-003.threshold": (TI, "C-01")}, old=base)
    # G is judged on the OLD version: it was GLOBAL when this change was made.
    new = _edit("LOSS-003", threshold=0.08)
    _apply(new, "LOSS-004", {"kill_scope": "POOL"})
    _expect(new, {"rules.LOSS-003.threshold": (TI, "C-01"), "rules.LOSS-004.kill_scope": (LO, "C-17"),
                  "rules.LOSS-004.kill_displaced_by.LOSS-003": (UN, "C-40")})


def t_c41():
    rules = _edit("EXP-001", threshold=0.10)["rules"]
    a, b = _dir(_raw()), _dir(_raw(), market__IN={"rules": rules})
    by = {(d.market, d.environment): d for d in P.diff_policy_dirs(a, b)}
    require(set(by) == {(None, None), ("IN", None), ("US", None)}, f"combinations {sorted(by, key=str)}")
    SEEN_BASES.add("C-41")
    got = {c.path: (c.direction, c.basis) for c in by[("IN", None)].changes}
    require(got == {"layers.market.IN": (UN, "C-41"), "rules.EXP-001.threshold": (LO, "C-01")},
            f"IN: {got}")
    require(not by[("US", None)].changes and not by[(None, None)].changes, "others must be empty")

    # The override layer applies to every combination.
    b = _dir(_raw(), override={"metadata": {"description": "an override"}})
    for d in P.diff_policy_dirs(a, b):
        paths = {c.path: (c.direction, c.basis) for c in d.changes}
        require(paths.get("layers.override") == (UN, "C-41"), f"({d.market}, {d.environment}): {paths}")

    # Two layers removed together give two records.
    a = _dir(_raw(), market__IN={"metadata": {"description": "india"}},
             env__paper={"metadata": {"authored_by": "someone"}})
    by = {(d.market, d.environment): d for d in P.diff_policy_dirs(a, _dir(_raw()))}
    gone = {c.path for c in by[("IN", "paper")].changes if c.basis == "C-41"}
    require(gone == {"layers.market.IN", "layers.env.paper"}, f"layers removed: {gone}")


def t_c42():
    for rid, old, want in (("HOLD-001", "DENY", (UN, "C-42")), ("RECON-001", "DENY", (UN, "C-42")),
                           ("INST-002", "MODIFY", (UN, "C-42")), ("KILL-002", "ALLOW", (UN, "C-42")),
                           ("LOSS-001", "DENY", (TI, "C-09")),
                           ("HOLD-001", "KILL", (LO, "C-09"))):
        got = P.rule_action_direction(rid, old, "HALT_ENTRIES")
        require(got == want, f"{rid} {old}->HALT_ENTRIES is {got}")
        SEEN_BASES.add(want[1])
    require(set(P.HALT_ENTRIES_RULES) == {"LOSS-001", "LOSS-002"}, "HALT_ENTRIES_RULES differs")


# =============================================================================
# D. AUTHORISATION (§7.4)
# =============================================================================
def t_combinations_are_derived():
    a = _dir(_with_map(_raw(), (AB, JS)))
    b = _dir(_with_map(_raw(), (AB, JS)),
             market__IN={"rules": _edit("EXP-001", threshold=0.10)["rules"]})
    with _vault(AB, JS):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB,)), "market layer: ")
    raises(P.PolicyDiffError, lambda: P.derive_combinations(_dir(_raw(), market__XX={"a": 1}),
                                                            a), "unknown market: ")
    raises(P.PolicyDiffError, lambda: P.derive_combinations(_dir(_raw(), env__BAD={"a": 1}),
                                                            a), "bad env name: ")
    c = _dir(_raw(), env__paper={"metadata": {"description": "paper"}})
    combos = P.derive_combinations(_dir(_raw()), c)
    require(len(combos) == 6 and (None, "paper") in combos and ("IN", "paper") in combos
            and ("US", "paper") in combos, f"env file in one directory: {combos}")


def t_retired_combination():
    layer = {"rules": _with_map(_edit("EXP-001", threshold=0.04), (AB, JS))["rules"]}
    a = _dir(_with_map(_raw(), (AB, JS)), market__IN=layer)
    b = _dir(_with_map(_raw(), (AB, JS)))
    paths = {c.path for d in P.diff_policy_dirs(a, b) for c in d.changes}
    require("layers.market.IN" in paths, f"no LAYER_REMOVED: {paths}")
    SEEN_BASES.add("C-41")
    with _vault(AB, JS):
        auth = _authorise(a, b, (AB, JS))
    require("layers.market.IN" in auth.gated_paths, f"gated {auth.gated_paths}")


def t_signatures():
    a = _dir(_with_map(_raw(), (AB, JS)))
    b = _dir(_with_map(_edit("LOSS-004", threshold=0.20), (AB, JS)))
    require(isinstance(L.PolicyLoader(a).load(require_signature=False), L.EffectiveConfig),
            "the signatures fixture must load through PolicyLoader")
    bare = _with_map(_raw(), (AB, JS))
    for entry in _approver_refs(bare).values():
        entry["raw_key_sha256"] = entry["raw_key_sha256"].removeprefix("sha256:")
    raises(L.VaultReferenceError,
           lambda: L.PolicyLoader(_dir(bare)).load(require_signature=False), "bare hex: ")

    with _vault(AB, JS, CD):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB, CD)), "unlisted: ",
               match="not listed")
        approvals, rid, at = _signed(a, b, (AB, JS))
        wrong = P.ApprovalSignature(identity="js", signature_hex=JS.priv.sign(b"x").hex())
        raises(L.PolicyGovernanceError,
               lambda: P.assert_policy_change_authorised(a, b, [approvals[0], wrong],
                                                         request_id=rid, requested_at=at),
               "wrong digest: ", match="does not verify")

        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB, AB)), "one identity twice: ",
               match="1 distinct approver")

        diffs = P.diff_policy_dirs(a, b)
        payload = {"request_id": rid, "requested_at": at, "combinations": [
            {"market": d.market or "", "environment": d.environment or "",
             "old_content_hash": d.old_content_hash, "new_content_hash": d.new_content_hash}
            for d in diffs]}
        untagged = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        raises(L.PolicyGovernanceError,
               lambda: P.assert_policy_change_authorised(
                   a, b, [AB.sign(untagged), JS.sign(untagged)], request_id=rid, requested_at=at),
               "untagged digest: ", match="does not verify")

        _authorise(a, b, (AB, JS))

    # Two identities, one raw key, spelled in LF-PEM and CRLF-PEM: counted once.
    twin = Key("zz")
    twin.priv, twin.raw, twin.pin = AB.priv, AB.raw, AB.pin
    crlf = AB.pem.replace(b"\n", b"\r\n")
    a2 = _dir(_with_map(_raw(), (AB, twin)))
    b2 = _dir(_with_map(_edit("LOSS-004", threshold=0.20), (AB, twin)))
    with _vault(AB, pem={twin.ref: crlf}):
        raises(L.PolicyGovernanceError, lambda: _authorise(a2, b2, (AB, twin)), "one raw key: ",
               match="1 distinct approver")

    # A key replaced in Vault no longer matches its pin (X2F-7).
    with _vault(AB, pem={JS.ref: CD.pem}):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB, JS)), "pin: ",
               match="differs from its policy pin")

    params = set(inspect.signature(P.assert_policy_change_authorised).parameters)
    require(params == {"old_dir", "new_dir", "approvals", "request_id", "requested_at"},
            f"a key parameter crept in: {params}")
    raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB, JS)), "no Vault: ",
           match="no Vault client")


def t_no_adapter():
    d = _dir(_raw())
    auth = _authorise(d, _dir(_edit("EXP-001", threshold=0.04)))
    raises(P.InForceAnchorError,
           lambda: P.assert_authorisation_current(auth, "conn", d, d), "no store: ")
    raises(P.InForceAnchorError, lambda: _current(auth, FakeStore({}), d, d), "empty store: ")


def t_anchor_stale_base():
    v1 = _dir(_raw())
    v2a = _dir(_edit("LOSS-004", threshold=0.08))
    v2b = _dir(_edit("EXP-001", notes="a description edit"))
    a, b = _authorise(v1, v2a, request_id=REQUEST), _authorise(v1, v2b, request_id=REQUEST_B)
    _current(a, FakeStore(_hashes(v1)), v1, v2a)
    in_force = FakeStore(_hashes(v2a), used={REQUEST})
    raises(P.StaleAuthorisationError, lambda: _current(b, in_force, v1, v2b), "stale base: ",
           match="stored hash differs")
    edited = _dir(_edit("LOSS-004", threshold=0.07))
    raises(P.StaleAuthorisationError, lambda: _current(a, FakeStore(_hashes(v1)), v1, edited),
           "candidate edited: ", match="changed after approval")
    missing = _hashes(v1)
    del missing[("US", None)]
    raises(P.StaleAuthorisationError, lambda: _current(a, FakeStore(missing), v1, v2a),
           "row missing: ", match="no in-force row")
    params = set(inspect.signature(P.assert_authorisation_current).parameters)
    require(params == {"auth", "conn", "old_dir", "candidate_dir"}, f"parameters {params}")


def _env_fixture(layer):
    a = _dir(_with_map(_raw(), (AB, JS)))
    b = _dir(_with_map(_raw(), (AB, JS)), env__paper=layer)
    return a, b


def t_first_env_layer():
    a, b = _env_fixture({"metadata": {"description": "paper"}})
    with _vault(AB, JS):
        auth = _authorise(a, b, (AB, JS))
        require(len(auth.diffs) == 6, f"{len(auth.diffs)} combinations")
        _current(auth, FakeStore(_hashes(a)), a, b)

        # A new combination whose hash differs from its (m, None) row. Only step 4 can say so.
        doctored = tuple(
            d.model_copy(update={"old_content_hash": "0" * 64})
            if (d.market, d.environment) == ("US", "paper") else d for d in auth.diffs)
        forged = auth.model_copy(update={"diffs": doctored})
        raises(P.StaleAuthorisationError, lambda: _current(forged, FakeStore(_hashes(a)), a, b),
               "hand-built hash: ", match="stored hash differs")

    # An EMPTY env file, so the hashes agree: only this fixture catches M-23.
    a, b = _env_fixture(None)
    with _vault(AB, JS):
        auth = _authorise(a, b, (AB, JS))
    bare = tuple(d.model_copy(update={"changes": ()}) for d in auth.diffs)
    plain = auth.model_copy(update={"diffs": bare, "gated_paths": (), "required_approvals": "0",
                                    "approvals": ()})
    with _vault(AB, JS):
        raises(P.StaleAuthorisationError, lambda: _current(plain, FakeStore(_hashes(a)), a, b),
               "no LAYER_ADDED: ", match="no in-force row")


def t_retired_env_layer():
    layer = {"metadata": {"description": "paper"}}
    a = _dir(_with_map(_raw(), (AB, JS)), env__paper=layer)
    b = _dir(_with_map(_raw(), (AB, JS)))
    with _vault(AB, JS):
        auth = _authorise(a, b, (AB, JS))
        _current(auth, FakeStore(_hashes(a)), a, b)

        # A paper row left current after an earlier removal.
        c = _dir(_with_map(_edit("EXP-001", notes="next"), (AB, JS)))
        next_auth = _authorise(b, c, request_id=REQUEST_B)
        left = _hashes(b)
        left.update({("US", "paper"): "0" * 64})
        raises(P.StaleAuthorisationError, lambda: _current(next_auth, FakeStore(left), b, c),
               "left current: ", match="combination set")

        # Revival: the closed rows are gone, and (m, None) has changed in between.
        revived = _dir(_with_map(_edit("EXP-001", notes="next"), (AB, JS)),
                       env__paper={"metadata": {"description": "paper, revived"}})
        again = _authorise(c, revived, (AB, JS), request_id=REQUEST_B)
        _current(again, FakeStore(_hashes(c)), c, revived)


def _replay_fixture():
    v1 = _dir(_with_map(_raw(), (AB, JS)))
    v2 = _dir(_with_map(_set_key(_raw(), "portfolio.max_position_pct", 0.08), (AB, JS)))
    return v1, v2


def t_replay():
    v1, v2 = _replay_fixture()
    with _vault(AB, JS):
        auth = _authorise(v1, v2, (AB, JS))
        _current(auth, FakeStore(_hashes(v1)), v1, v2)
        back = _authorise(v2, v1, request_id=REQUEST_B)
        _current(back, FakeStore(_hashes(v2), used={REQUEST}), v2, v1)
        # v1 is in force again, so every hash matches. Only the used request refuses it.
        raises(P.StaleAuthorisationError,
               lambda: _current(auth, FakeStore(_hashes(v1), used={REQUEST, REQUEST_B}), v1, v2),
               "replay: ", match="already been applied")


def t_late_replay():
    v1, v2 = _replay_fixture()
    with _vault(AB, JS):
        auth = _authorise(v1, v2, (AB, JS))
        late = datetime.now(timezone.utc) + timedelta(hours=25)
        raises(P.StaleAuthorisationError,
               lambda: _current(auth, FakeStore(_hashes(v1), now=late, used={REQUEST}), v1, v2),
               "late replay: ", exact=True)


def t_stripped_authorisation():
    a = _dir(_raw())
    b = _dir(_edit("LOSS-004", threshold=0.20))
    diffs = P.diff_policy_dirs(a, b)
    at = _at(_now())
    digest = P.authorisation_digest(diffs, REQUEST, at)
    raises(ValueError, lambda: P.PolicyAuthorisation(
        diffs=diffs, request_id=REQUEST, requested_at=at, digest=digest, approvals=(),
        required_approvals="0", gated_paths=()), "stripped: ")
    blanked = tuple(d.model_copy(update={"changes": ()}) for d in diffs)
    forged = P.PolicyAuthorisation(diffs=blanked, request_id=REQUEST, requested_at=at,
                                   digest=digest, approvals=(), required_approvals="0",
                                   gated_paths=())
    raises(P.StaleAuthorisationError, lambda: _current(forged, FakeStore(_hashes(a)), a, b),
           "blanked: ", match="re-checked")


def t_doctored_old_dir():
    a = _dir(_raw())
    b = _dir(_edit("EXP-001", threshold=0.04))
    auth = _authorise(a, b)
    other = _dir(_edit("EXP-002", threshold=0.10))
    raises(P.StaleAuthorisationError, lambda: _current(auth, FakeStore(_hashes(a)), other, b),
           "doctored old_dir: ", match="old_dir is not the version diffed")


def t_digest_and_load_failures():
    a = _dir(_raw())
    b = _dir(_edit("EXP-001", threshold=0.04))
    auth = _authorise(a, b)
    wrong = auth.model_copy(update={"digest": "0" * 64})
    raises(P.StaleAuthorisationError, lambda: _current(wrong, FakeStore(_hashes(a)), a, b),
           "digest: ", match="digest")
    broken = _dir(_raw())
    (broken / "policy.yaml").write_text("rules: [", encoding="utf-8")
    raises(P.StaleAuthorisationError, lambda: _current(auth, FakeStore(_hashes(a)), a, broken),
           "candidate does not load: ")


def t_expiry():
    a = _dir(_raw())
    b = _dir(_edit("EXP-001", threshold=0.04))
    start = _now()
    auth = _authorise(a, b, at=_at(start))
    hashes = _hashes(a)

    def at(delta):
        return FakeStore(hashes, now=start + delta)

    _current(auth, at(timedelta(hours=24) - timedelta(seconds=1)), a, b)
    _current(auth, at(timedelta(hours=24)), a, b)
    _current(auth, at(timedelta(0)), a, b)
    e = raises(P.ApprovalExpiredError,
               lambda: _current(auth, at(timedelta(hours=24, seconds=1)), a, b), "expired: ")
    require(e.reason == "EXPIRED" and e.request_id == REQUEST, f"{e.reason} {e.request_id}")
    e = raises(P.ApprovalExpiredError,
               lambda: _current(auth, at(timedelta(seconds=-1)), a, b), "future: ")
    require(e.reason == "FUTURE", f"reason {e.reason}")
    stale = FakeStore({k: "0" * 64 for k in hashes}, now=start + timedelta(hours=25))
    e = raises(P.ApprovalExpiredError, lambda: _current(auth, stale, a, b), "expired and stale: ")
    require(e.reason == "EXPIRED", f"reason {e.reason}")

    # requested_at is inside the digest, so changing it after signing breaks every signature.
    k1 = _dir(_with_map(_raw(), (AB, JS)))
    k2 = _dir(_with_map(_edit("LOSS-004", threshold=0.20), (AB, JS)))
    approvals, rid, when = _signed(k1, k2, (AB, JS))
    later = _at(_now() - timedelta(seconds=5))
    require(later != when, "fixture")
    with _vault(AB, JS):
        raises(L.PolicyGovernanceError,
               lambda: P.assert_policy_change_authorised(k1, k2, approvals, request_id=rid,
                                                         requested_at=later), "edited time: ")

    # The local clock refuses early too.
    for offset in (timedelta(hours=25), timedelta(hours=-1)):
        raises(P.ApprovalExpiredError,
               lambda o=offset: _authorise(a, b, at=_at(_now() - o)), "local clock: ")


def t_canonical_payload():
    a = _dir(_with_map(_raw(), (AB, JS)))
    b = _dir(_with_map(_edit("LOSS-004", threshold=0.20), (AB, JS)))
    with _vault(AB, JS):
        auth = _authorise(a, b, (AB, JS))
    require(auth.required_approvals == "2" and auth.gated_paths, f"{auth.required_approvals}")
    require(canonical_json(auth.model_dump(mode="json")), "no payload")


def t_models():
    change = P.PolicyChange(kind=P.ChangeKind.RULE_FIELD, path="rules.EXP-002.action",
                            rule_id="EXP-002", field="action", old="DENY", new="ALLOW",
                            direction=LO, basis="C-09", reason="down")
    other = change.model_copy(update={"path": "rules.EXP-001.action", "rule_id": "EXP-001"})
    h1, h2 = "a" * 64, "b" * 64

    def diff(changes=(), market=None):
        return P.PolicyDiff(market=market, environment=None, old_version="1.0.0",
                            new_version="1.0.1", old_content_hash=h1, new_content_hash=h2,
                            changes=changes)

    def auth(**kw):
        base = dict(diffs=(diff(),), request_id=REQUEST, requested_at="2026-10-31T06:30:00Z",
                    digest=h1, approvals=(), required_approvals="0", gated_paths=())
        return P.PolicyAuthorisation(**{**base, **kw})

    sig = "0" * 128
    ab, js = (P.ApprovalSignature(identity=i, signature_hex=sig) for i in ("ab", "js"))
    auth()
    raises(ValueError, lambda: diff((change, other)), "unsorted changes: ")
    raises(ValueError, lambda: auth(diffs=(diff(market="US"), diff(market="IN"))), "unsorted: ")
    raises(ValueError, lambda: auth(diffs=(diff(), diff())), "duplicate diffs: ")
    raises(ValueError, lambda: P.ApprovalSignature(identity=" JS", signature_hex=sig), "identity: ")
    raises(ValueError, lambda: auth(approvals=(ab, ab)), "duplicate approver: ")
    raises(ValueError, lambda: auth(approvals=(js, ab)), "unsorted approvers: ")
    raises(ValueError, lambda: auth(required_approvals="6"), "required 6: ")
    for bad in ("2026-13-45T99:99:99Z", "2026-02-30T00:00:00Z", "2026-01-01T23:59:60Z"):
        raises(ValueError, lambda b=bad: auth(requested_at=b), f"{bad}: ")
    gated = (diff((change,)),)
    path = "rules.EXP-002.action"
    raises(ValueError, lambda: auth(diffs=gated, required_approvals="2", approvals=(ab, js)),
           "gated_paths differ: ")
    raises(ValueError, lambda: auth(diffs=gated, gated_paths=(path,)), "0 with a gated path: ")
    raises(ValueError, lambda: auth(required_approvals="5"), "non-0 with none gated: ")

    def rule_change(**over):
        base = dict(kind=P.ChangeKind.RULE_ADDED, path="rules.EXP-009", rule_id="EXP-009", field=None,
                    old=None, new="EXP-009", direction=TI, basis="C-34", reason="added")
        return P.PolicyChange(**{**base, **over})

    rule_change()
    raises(ValueError, lambda: rule_change(basis="C-99"), "unknown basis: ")
    raises(ValueError, lambda: rule_change(rule_id=None), "a rule change with no rule_id: ")
    raises(ValueError, lambda: rule_change(old="x"), "an addition with an old value: ")
    raises(ValueError, lambda: rule_change(kind=P.ChangeKind.RULE_REMOVED, old="EXP-009"),
           "a removal with a new value: ")
    raises(ValueError, lambda: rule_change(field="threshold"), "field off a RULE_FIELD: ")
    raises(ValueError, lambda: rule_change(related_rule_id="EXP-001"), "related on a non-derived: ")
    raises(ValueError, lambda: diff((change, change)), "repeated changes: ")
    raises(ValueError, lambda: auth(diffs=gated, gated_paths=(path, path), required_approvals="2",
                                    approvals=(ab, js)), "repeated gated_paths: ")
    raises(ValueError, lambda: auth(diffs=gated, gated_paths=(path,), required_approvals="2",
                                    approvals=(ab,)), "too few approvals: ")
    auth(diffs=gated, gated_paths=(path,), required_approvals="2", approvals=(ab, js))


def t_counts():
    mixed = _edit("EXP-001", threshold=0.04)
    _apply(mixed, "EXP-002", {"threshold": 0.30})
    a = _dir(_with_map(_raw(), (AB, JS, CD)))
    b = _dir(_with_map(mixed, (AB, JS, CD)))
    with _vault(AB, JS, CD):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB,)), "mixed, one: ")
        _authorise(a, b, (AB, JS))
    _zero_approvals(_edit("EXP-001", threshold=0.04))

    old = _set_key(_with_map(_raw(), (AB, JS, CD)), "governance.min_approvals_to_loosen", 3)
    new = _set_key(_with_map(_edit("EXP-002", threshold=0.30), (AB, JS, CD)),
                   "governance.min_approvals_to_loosen", 2)
    a, b = _dir(old), _dir(new)
    with _vault(AB, JS, CD):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB, JS)), "old 3, new 2: ")
        _authorise(a, b, (AB, JS, CD))


def t_fail_closed():
    raises(P.PolicyDiffError, lambda: P.diff_policies(RAW, _edit("EXP-001",
                                                                 on_missing_input="ALLOW")),
           "unvalidatable: ")
    broken = _dir(_edit("EXP-001", on_missing_input="ALLOW"))
    raises(P.PolicyDiffError, lambda: P.diff_policy_dirs(_dir(_raw()), broken), "loader: ")
    raises(P.PolicyDiffError, lambda: P.diff_policies(RAW, _edit("EXP-001",
                                                                 action="HALT_ENTRIES")),
           "HALT_ENTRIES before #17: ")
    same = _dir(_raw())
    d = P.diff_policy_dirs(same, same)
    require(not any(x.changes for x in d), "an identical pair has no changes")
    require(_authorise(same, same).required_approvals == "0", "identical needs no approval")
    require(P.diff_policies(RAW, _edit("EXP-001", threshold=0.04)) ==
            P.diff_policies(RAW, _edit("EXP-001", threshold=0.04)), "not reproducible")


def t_redaction_equals_hash():
    cfg = ROOT / "config"
    for market, environment in P.derive_combinations(cfg, cfg):
        c = L.PolicyLoader(cfg).load(market=market, environment=environment,
                                     require_signature=False)
        require(L.content_hash(c.redacted) == c.content_hash, f"({market}, {environment})")


def t_diff_agrees_with_loosens_for_on_every_ordinal_threshold():
    ordinal = (L.Comparison.LTE, L.Comparison.LT, L.Comparison.GTE, L.Comparison.GT)
    checked = 0
    for r in DOC.rules:
        if r.threshold is None or r.comparison not in ordinal:
            continue
        for factor in ("1.5", "0.5"):
            value = D(str(r.threshold)) * D(factor)
            if "pct" in r.measurement.basis:
                value = min(value, D(1))
            if value == D(str(r.threshold)):
                continue
            change = L.LimitChange(rule_id=r.id, field="threshold",
                                   old_value=D(str(r.threshold)), new_value=value)
            d = P.diff_policies(RAW, _edit(r.id, threshold=float(value)))
            rec = [c for c in d.changes if c.path == f"rules.{r.id}.threshold"]
            require(len(rec) == 1, f"{r.id}: {rec}")
            want = LO if L.loosens_for(change, r) else TI
            require(rec[0].direction is want, f"{r.id} x{factor}: {rec[0].direction} != {want}")
            checked += 1
    require(checked > 20, f"only {checked} checked")


def t_dotted_keys_are_refused():
    """A path must name one leaf, or an overwritten value hides a real change (X2H-1)."""
    hidden = _set_key(_raw(), "kill_switch.auto_re_enable_permitted", True)
    hidden["kill_switch.auto_re_enable_permitted"] = False
    trailing = _raw()
    trailing["portfolio"]["max_position_pct."] = 0.05
    bracket = _raw()
    bracket["hitl"]["actions[0]"] = {"action": "x"}
    empty = _raw()
    empty["portfolio"][""] = 1
    for label, doc in (("dotted", hidden), ("trailing dot", trailing), ("bracket", bracket),
                       ("empty", empty)):
        raises(P.PolicyDiffError, lambda d=doc: P.diff_policies(RAW, d), f"{label}, new: ",
               match="cannot be classified")
        raises(P.PolicyDiffError, lambda d=doc: P.diff_policies(d, RAW), f"{label}, old: ",
               match="cannot be classified")
    mixed = _raw()
    mixed["portfolio"][1] = "x"
    raises(P.PolicyDiffError, lambda: P.diff_policies(RAW, mixed), "a non-string key: ")


def t_type_changes_are_recorded():
    """Every change of type gives a record (X2H-2). Each of these once gave none."""
    for key, value in (("fx.system_may_convert", "False"),
                       ("kill_switch.auto_re_enable_permitted", "False"),
                       ("account.enforce_settled_cash", "True"),
                       ("portfolio.max_position_pct", "0.05"),
                       ("portfolio.max_position_pct", "0.050"),
                       ("turnover.max_new_entries_per_session", "4")):
        _expect(_set_key(_raw(), key, value), {key: (UN, "C-39")})
    base = _set_key(_raw(), "schedule.extra", ["a", "b"])
    _expect(_set_key(copy.deepcopy(base), "schedule.extra", ["a,b"]),
            {"schedule.extra": (UN, "C-39")}, old=base)
    base = _set_key(_raw(), "schedule.extra", 1)
    _expect(_set_key(copy.deepcopy(base), "schedule.extra", "1"),
            {"schedule.extra": (UN, "C-39")}, old=base)
    _expect(_edit("DATA-002", allowed_values=["True"]),
            {"rules.DATA-002.allowed_values": (UN, "C-21")})
    base = _edit("REGIME-001", disallowed_values=[1, "UNKNOWN"])
    _expect(_edit("REGIME-001", disallowed_values=["1", "UNKNOWN"]),
            {"rules.REGIME-001.disallowed_values": (UN, "C-22")}, old=base)
    m = _rule_raw(RAW, "EXP-006")["modify"]
    _expect(_edit("EXP-006", modify={**m, "to": "0.04"}),
            {"rules.EXP-006.modify.to": (UN, "C-30")})

    # A NEUTRAL key is not exempt: a change of type there has no direction either.
    _expect(_set_key(_raw(), "cost.total_operating_is_complete", 1),
            {"cost.total_operating_is_complete": (UN, "C-39")})

    # An empty mapping is a leaf, and a list of mappings cannot pose as an index-keyed mapping.
    _expect(_set_key(_raw(), "kill_switch.extra", {}), {"kill_switch.extra": (UN, "C-38")})
    swapped = _raw()
    swapped["hitl"]["actions"] = {str(i): v for i, v in enumerate(RAW["hitl"]["actions"])}
    d = P.diff_policies(RAW, swapped)
    require(d.requires_two_person, "a list turned into a mapping must be gated")


# Every directed key of §3.7, typed out here so that a key moved in the module fails this test.
KEY_TABLE = {
    "NEUTRAL": """policy_version metadata.description metadata.authored_by metadata.authored_at
        cost.verified_monthly_usd.paper cost.verified_monthly_usd.live cost.vm_monthly_usd
        cost.backup_monthly_usd cost.total_operating_is_complete""",
    "TRUE_LOOSENS": """governance.risk_deny_override_permitted hitl.risk_deny_override_permitted
        kill_switch.auto_re_enable_permitted fx.system_may_convert llm.may_receive_portfolio_state""",
    "FALSE_LOOSENS": """kill_switch.requires_human_to_re_enable risk_evaluation.evaluate_per_pool
        risk_evaluation.evaluate_consolidated risk_evaluation.stricter_binds
        llm.replay_requires_approval llm.replay_offpeak_only account.enforce_settled_cash
        account.enforce_day_trades""",
    "LOWER_LOOSENS": """governance.min_approvals_to_loosen account.pdt_equity_floor_usd
        portfolio.min_cash_pct decision.min_edge_multiple_of_cost cost.assumed_round_trip_bps.US
        cost.assumed_round_trip_bps.IN holding.time_stop_min_return_pct holding.min_sessions
        storage.records_retention_years promotion.min_wf_windows promotion.min_closed_trades
        promotion.shadow_min_sessions promotion.dsr_threshold
        universe.US.min_addv_position_multiple universe.IN.min_addv_position_multiple
        universe.US.min_sessions_history universe.IN.min_sessions_history
        universe.US.min_reported_quarters universe.IN.min_reported_quarters
        universe.US.min_market_cap_usd universe.US.min_addv_usd_floor universe.US.min_price_usd
        universe.IN.min_market_cap_inr universe.IN.min_addv_inr_floor universe.IN.min_price_inr""",
    "HIGHER_LOOSENS": """account.pdt_max_day_trades_5d portfolio.max_position_pct
        portfolio.forced_trim_pct turnover.max_new_entries_per_session
        turnover.max_nav_traded_pct_per_session holding.time_stop_sessions holding.hard_max_sessions
        llm.gate_width llm.max_concurrency llm.spend_alarm_warn_usd_month
        llm.spend_alarm_critical_usd_month latency.exit.stale_bar_critical_seconds
        dr.rpo_state_seconds dr.rto_safe_minutes dr.rto_operational_hours storage.disk_warn_pct
        storage.disk_critical_pct universe.US.max_instruments universe.IN.max_instruments
        universe.US.enter_rank universe.IN.enter_rank universe.US.exit_rank universe.IN.exit_rank""",
    "SET_GROW_LOOSENS": "instrument_allowlist.tradeable",
    "SET_SHRINK_LOOSENS": "instrument_allowlist.permanently_banned",
}


def t_every_key_direction_is_pinned():
    want = {key: kind for kind, keys in KEY_TABLE.items() for key in keys.split()}
    require(len(want) == 72, f"{len(want)} keys in the table")
    have = {key: kind.value for key, kind in P.CONFIG_KEY_DIRECTIONS[:-1]}
    for key in sorted(set(want) | set(have)):
        require(have.get(key) == want.get(key),
                f"{key} is {have.get(key)}; the table says {want.get(key)}")


def t_key_kind_directions():
    key = "fx.system_may_convert"
    off, on = _set_key(_raw(), key, False), _set_key(_raw(), key, True)
    _expect(on, {key: (LO, "C-37")}, old=off)
    _expect(off, {key: (TI, "C-37")}, old=on)
    key = "account.enforce_day_trades"
    off, on = _set_key(_raw(), key, False), _set_key(_raw(), key, True)
    _expect(off, {key: (LO, "C-37")}, old=on)
    _expect(on, {key: (TI, "C-37")}, old=off)


def t_digest_known_answer():
    """The preimage is typed out here, so that any field leaving it fails this test."""
    h1, h2 = "a" * 64, "b" * 64
    diff = P.PolicyDiff(market="US", environment="paper", old_version="1.0.0", new_version="1.0.1",
                        old_content_hash=h1, new_content_hash=h2, changes=())
    preimage = (
        b"SPEC-P1.3.1 approval v1\n"
        b'{"combinations":[{"environment":"paper","market":"US",'
        b'"new_content_hash":"' + h2.encode() + b'","old_content_hash":"' + h1.encode() + b'"}],'
        b'"request_id":"' + REQUEST.encode() + b'","requested_at":"2026-10-31T06:30:00Z"}')
    require(P.authorisation_digest((diff,), REQUEST, "2026-10-31T06:30:00Z")
            == hashlib.sha256(preimage).hexdigest(), "the digest preimage changed")


def t_keys_come_from_the_in_force_base():
    a = _dir(_with_map(_raw(), (AB, JS)))
    b = _dir(_with_map(_edit("LOSS-004", threshold=0.20), (CD, ZZ)))
    with _vault(AB, JS, CD, ZZ):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (CD, ZZ)), "the candidate's keys: ",
               match="not listed")
    # A market layer may carry a map. It is not the source of keys.
    layer = {"governance": {"signature": {"approver_key_refs": {
        k.name: {"ref": k.ref, "raw_key_sha256": k.pin} for k in (CD, ZZ)}}}}
    base = _with_map(_raw(), (AB, JS))
    a = _dir(base, market__US=layer)
    b = _dir(_with_map(_edit("LOSS-004", threshold=0.20), (AB, JS)), market__US=layer)
    with _vault(AB, JS, CD, ZZ):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (CD, ZZ)), "a layer's keys: ",
               match="not listed")


def t_key_must_be_ed25519():
    ec = ec_key(SECP256R1()).public_key().public_bytes(Encoding.PEM,
                                                       PublicFormat.SubjectPublicKeyInfo)
    a = _dir(_with_map(_raw(), (AB, JS)))
    b = _dir(_with_map(_edit("LOSS-004", threshold=0.20), (AB, JS)))
    with _vault(AB, pem={JS.ref: ec}):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB, JS)), "EC key: ",
               match="not Ed25519")


def t_approver_map_is_normalised():
    doc = _with_map(_raw(), (AB, JS))
    refs = _approver_refs(doc)
    refs["AB "] = refs.pop("ab")
    a = _dir(doc)
    new = _with_map(_edit("LOSS-004", threshold=0.20), (AB, JS))
    _approver_refs(new)["AB "] = _approver_refs(new).pop("ab")
    b = _dir(new)
    with _vault(AB, JS):
        _authorise(a, b, (AB, JS))
    clash = _with_map(_raw(), (AB, JS))
    _approver_refs(clash)["AB"] = dict(_approver_refs(clash)["ab"])
    c = _dir(clash)
    with _vault(AB, JS):
        raises(L.PolicyGovernanceError, lambda: _authorise(c, c, (AB,)), "a duplicate: ",
               match="not usable")
    listed = _raw()
    listed["governance"]["signature"]["approver_key_refs"] = ["ab"]
    d = _dir(listed)
    raises(L.PolicyGovernanceError, lambda: _authorise(d, d), "not a mapping: ",
           match="not a mapping")


def t_count_uses_every_old_document():
    layer = {"governance": {"min_approvals_to_loosen": 3}}
    a = _dir(_with_map(_raw(), (AB, JS, CD)), market__US=layer)
    b = _dir(_with_map(_edit("EXP-002", threshold=0.30), (AB, JS, CD)), market__US=layer)
    with _vault(AB, JS, CD):
        raises(L.PolicyGovernanceError, lambda: _authorise(a, b, (AB, JS)), "US requires 3: ",
               match="3 required")
        require(_authorise(a, b, (AB, JS, CD)).required_approvals == "3", "the count must be 3")


def t_store_failures():
    a = _dir(_raw())
    b = _dir(_edit("EXP-001", threshold=0.04))
    auth = _authorise(a, b)
    naive = FakeStore(_hashes(a), now=datetime.now())  # noqa: DTZ005 - the naive clock under test
    raises(P.InForceAnchorError, lambda: _current(auth, naive, a, b), "naive clock: ", match="naive")

    class Broken(FakeStore):
        def in_force_hashes(self, conn):
            raise RuntimeError("connection lost")

    raises(P.InForceAnchorError, lambda: _current(auth, Broken({}), a, b), "store fails: ",
           match="could not be read")
    bad = _dir(_edit("EXP-001", threshold=0.04), market__XX={"a": 1})
    raises(P.StaleAuthorisationError, lambda: _current(auth, FakeStore(_hashes(a)), a, bad),
           "unknown layer: ", match="unknown layer")


def t_anchor_needs_its_own_layer():
    """The (m, None) anchor is for a combination's OWN env file, not any layer added with it."""
    a = _dir(_with_map(_raw(), (AB, JS)), env__paper=None)
    b = _dir(_with_map(_raw(), (AB, JS)), env__paper=None,
             market__US={"metadata": {"description": "a US layer"}})
    with _vault(AB, JS):
        auth = _authorise(a, b, (AB, JS))
        rows = _hashes(a)
        del rows[("US", "paper")]
        raises(P.StaleAuthorisationError, lambda: _current(auth, FakeStore(rows), a, b),
               "another layer's record: ", match="no in-force row")


def t_check_order():
    """§5.3: the candidate is checked before the digest."""
    a = _dir(_raw())
    b = _dir(_edit("EXP-001", threshold=0.04))
    auth = _authorise(a, b).model_copy(update={"digest": "0" * 64})
    edited = _dir(_edit("EXP-001", threshold=0.03))
    raises(P.StaleAuthorisationError, lambda: _current(auth, FakeStore(_hashes(a)), a, edited),
           "both wrong: ", match="changed after approval")


def t_order_is_not_a_change():
    """§2 row 7: value sets compare as sets."""
    r = _rule_raw(RAW, "EXP-001")
    _expect(_edit("EXP-001", inputs=list(reversed(r["inputs"]))), {})
    e = _rule_raw(RAW, "KILL-002")
    _expect(_edit("KILL-002", exempts=list(reversed(e["exempts"]))), {})
    x = _rule_raw(RAW, "EXEC-001")
    _expect(_edit("EXEC-001", allowed_values_emergency=list(reversed(x["allowed_values_emergency"]))),
            {})
    base = _edit("EXEC-001", allowed_values=["LIMIT", "STOP"])
    _expect(_edit("EXEC-001", allowed_values=["STOP", "LIMIT"]), {}, old=base)


def t_loader_failures_are_refused():
    """§8's catch-all: whatever the loader raises, the documented types come out (X2H-6)."""
    good = _dir(_raw())
    no_layering = _raw()
    del no_layering["layering"]
    null_layering = _raw()
    null_layering["layering"] = None
    mixed = _raw()
    mixed["portfolio"][1] = "x"
    not_utf8 = _dir(_raw())
    (not_utf8 / "policy.yaml").write_bytes(b"\xff\xfe\x00")
    cases = (_dir(no_layering), _dir(null_layering), _dir(mixed), not_utf8)
    auth = _authorise(good, _dir(_edit("EXP-001", threshold=0.04)))
    for bad in cases:
        raises(P.PolicyDiffError, lambda b=bad: P.diff_policy_dirs(good, b), f"{bad.name}: ")
        raises(P.StaleAuthorisationError,
               lambda b=bad: _current(auth, FakeStore(_hashes(good)), good, b), f"{bad.name}, apply: ")


# =============================================================================
# E. COMPLETENESS (§7.6)
# =============================================================================
def t_every_rule_field_is_classified():
    require(set(P.RULE_FIELDS) == set(L.Rule.model_fields),
            f"unclassified: {sorted(set(L.Rule.model_fields) ^ set(P.RULE_FIELDS))}")


def t_every_action_is_ranked():
    values = {a.value for a in L.RuleAction}
    require(values <= set(P.ACTION_LADDER), f"unranked: {values - set(P.ACTION_LADDER)}")
    require(set(P.ACTION_LADDER) <= values | {"HALT_ENTRIES"}, f"ladder {P.ACTION_LADDER}")


def t_ladder_agrees_with_gate_precedence():
    gate = [a.value for a in L.ACTION_PRECEDENCE]
    ranked = [a for a in P.ACTION_LADDER if a in gate]
    require(ranked == gate, f"ladder {ranked} != gate {gate}")


def t_config_keys_are_exact():
    table = P.CONFIG_KEY_DIRECTIONS
    leaves = P._leaves({k: v for k, v in CFG.redacted.items() if k != "rules"})
    require(table[-1] == ("**", P.KeyDirection.UNDECIDABLE), f"last entry {table[-1]}")
    for key, _ in table[:-1]:
        require(not set(key) & set("*?["), f"{key}: a wildcard")
        require(key in leaves, f"{key}: not in today's file")
    require(len(table) - 1 == 72, f"{len(table) - 1} directed keys")


def _src_trees():
    for path in sorted((ROOT / "src").rglob("*.py")):
        yield path, ast.parse(path.read_text(encoding="utf-8"))


def t_v1_authorisation_not_on_the_approval_path():
    for path, tree in _src_trees():
        if path.name == "loader.py":
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", getattr(node.func, "id", ""))
                require(name != "assert_change_authorised", f"{path.name} calls the v1 path")


NAMES = {"IN_FORCE_STORE", "VAULT_RESOLVER"}


def _bindings(tree):
    """Every way these two names are bound. `(line, how)` for each."""
    out = []
    exported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "__all__"
                                                for t in node.targets):
            exported.update(id(x) for x in ast.walk(node.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in NAMES and isinstance(node.ctx, ast.Store):
            out.append((node.lineno, "name"))
        elif isinstance(node, ast.Attribute) and node.attr in NAMES and isinstance(node.ctx,
                                                                                    ast.Store):
            out.append((node.lineno, "attribute"))
        elif isinstance(node, ast.Constant) and node.value in NAMES and id(node) not in exported:
            out.append((node.lineno, "string"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and node.name in NAMES:
            out.append((node.lineno, "def"))
        elif isinstance(node, ast.alias) and (node.asname in NAMES or node.name in NAMES):
            out.append((node.lineno, "import"))
        elif isinstance(node, ast.Global) and NAMES & set(node.names):
            out.append((node.lineno, "global"))
    return out


def _none_declarations(tree):
    return {n.target.id for n in tree.body
            if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") in NAMES
            and isinstance(n.value, ast.Constant) and n.value.value is None}


def t_store_adapter_assigned_only_by_store_module():
    for path, tree in _src_trees():
        found = _bindings(tree)
        if path.name == "policy_diff.py":
            require(_none_declarations(tree) == NAMES, "the = None declarations are missing")
            require(len(found) == len(NAMES), f"policy_diff.py binds them again: {found}")
        else:
            require(not found, f"{path.name} binds the adapter: {found}")


def t_defaults_are_none():
    code = ("import sys; sys.path[:0] = [sys.argv[1], sys.argv[1] + '/src'];"
            "import src.config.policy_diff as P;"
            "sys.exit(0 if P.IN_FORCE_STORE is None and P.VAULT_RESOLVER is None else 1)")
    r = subprocess.run([sys.executable, "-c", code, str(ROOT)], capture_output=True, text=True,
                       check=False)
    require(r.returncode == 0, f"a default is installed at import: {r.stderr[-300:]}")


def t_conn_reaches_only_the_store_adapter():
    tree = ast.parse((ROOT / "src" / "config" / "policy_diff.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
              and n.name == "assert_authorisation_current")
    require("conn" in [a.arg for a in fn.args.args], "no parameter named conn")
    require(fn.args.vararg is None and fn.args.kwarg is None, "conn could arrive through *args")
    allowed = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and node.args and isinstance(node.func, ast.Attribute) \
                and getattr(node.func.value, "id", "") == "IN_FORCE_STORE" \
                and getattr(node.args[0], "id", "") == "conn":
            allowed.add(id(node.args[0]))
    uses = [n for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id == "conn"]
    require(len(uses) >= 2, f"conn is used {len(uses)} time(s)")
    for use in uses:
        require(id(use) in allowed, f"line {use.lineno}: conn reaches something but the adapter")


def t_no_bare_assert():
    for name in ("verify_p13_policy_diff.py", "mutate_x5r_g9.py", "mutate_policy_diff_code.py"):
        tree = ast.parse((ROOT / "tests" / name).read_text(encoding="utf-8"))
        bad = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assert)]
        require(not bad, f"{name}: bare assert at {bad}")


def t_fast_yaml_parser_agrees():
    text = (ROOT / "config" / "policy.yaml").read_text(encoding="utf-8")
    require(_SLOW_YAML_LOAD(text) == RAW, "the test-only parser disagrees with yaml.safe_load")


def t_production_parser_gives_the_same_hash():
    """One load through the unpatched parser, with a layer, so the memo cannot hide a difference."""
    d = _dir(_raw(), market__US={"metadata": {"description": "a US layer"}})
    fast = L.PolicyLoader(d).load(market="US", require_signature=False).content_hash
    yaml.safe_load = _SLOW_YAML_LOAD
    try:
        slow = L.PolicyLoader(d).load(market="US", require_signature=False).content_hash
    finally:
        yaml.safe_load = _fast_yaml_load
    require(fast == slow, "the production parser and the test parser disagree")


def t_every_basis_is_exercised():
    missing = set(P.CLASSIFICATION_BASES) - SEEN_BASES
    require(not missing, f"never produced: {sorted(missing)}")


# =============================================================================
# RUN
# =============================================================================
PIN_TESTS = {"t_constitutional_set_is_exactly_the_table", "t_scope_and_mode_pinned_for_every_rule",
             "t_pinned_rule_set_is_exactly_the_file", "t_exemption_scope_is_pinned",
             "t_kill_scope_rules_are_pinned", "t_no_approver_is_listed",
             "t_halt_entries_rules_are_pinned"}


def main() -> int:
    # A failure message may hold any character; a console encoding must not lose a FAILED line.
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    tests: list[tuple[str, Callable[[], None]]] = sorted(
        (n, f) for n, f in globals().items() if n.startswith("t_") and callable(f))
    if os.environ.get("P13_PINS_ONLY") == "1":  # the sweep: attribution reads only these
        print("PINS-ONLY MODE: this run is not evidence that the suite passes")
        tests = [(n, f) for n, f in tests if n.startswith("t_pin_") or n in PIN_TESTS]
    tests.sort(key=lambda item: item[0] == "t_every_basis_is_exercised")
    for name, fn in tests:
        try:
            fn()
            PASS.append(name)
        except Exception as e:  # noqa: BLE001
            FAIL.append((name, str(e) or type(e).__name__))
    print(f"PASSED {len(PASS)}")
    for name, message in FAIL:
        for line in message.splitlines() or [""]:
            print(f"FAILED {name}: {line}")
    shutil.rmtree(_TMP.name, ignore_errors=True)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
