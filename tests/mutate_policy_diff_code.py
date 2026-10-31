"""SPEC-P1.3.1 §7.7: the tests fail when the code is broken.

    py -3.11 tests/mutate_policy_diff_code.py
    py -3.11 tests/mutate_policy_diff_code.py --negative-control

Applies each code mutation to a throwaway copy of `src/config/policy_diff.py` and runs
`tests/verify_p13_policy_diff.py` in `python` and `python -O`. A mutation is caught only if EVERY test
named for it is among the `FAILED` lines in both modes. Any other failure does not count.

A text that no longer occurs exactly once stops the harness: a mutation that silently applies to
nothing would report a test as proven when it proved nothing.

`--negative-control` stubs the named tests and exits 0 only if every mutation is reported uncaught.

The suite must first pass on the unmutated source, in both modes. Without that, a test that always
fails would give every mutation naming it a CAUGHT it did not earn.

M-1 to M-30 are §7.7's table. M-31 onward are what the X2 of the code found: its mutants survived the
first suite, so each is held here with the test that now kills it, and the rest guard its fixes.
"""
from __future__ import annotations

import argparse
import ast
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = "tests/verify_p13_policy_diff.py"
TARGET = "src/config/policy_diff.py"

_ADAPTER = """

class _Default:
    def in_force_hashes(self, conn):
        return {(None, None): "0" * 64}

    def database_time(self, conn):
        return datetime.now(timezone.utc)

    def request_used(self, conn, request_id):
        return False


IN_FORCE_STORE = _Default()
"""
_RESOLVER = """

def _default_resolver(ref):
    return b""


VAULT_RESOLVER = _default_resolver
"""


@dataclass(frozen=True)
class CodeMutation:
    name: str
    edits: tuple[tuple[str, str], ...]
    tests: tuple[str, ...]
    append: str = ""



_SET_FIELDS_TEXT = ('_SET_FIELDS: Final = ("allowed_values", "allowed_values_emergency", "disallowed_values",\n'
                    '                      "exempts", "inputs")')
_DIGEST_FIELDS = ('"old_content_hash": d.old_content_hash, "new_content_hash": d.new_content_hash}\n'
                  '            for d in diffs')
_CHECKS = ("    for diff in auth.diffs:\n"
           "        if _load(candidate_dir, diff.market, diff.environment).content_hash != diff.new_content_hash:\n"
           "            raise StaleAuthorisationError(\n"
           '                f"({diff.market}, {diff.environment}): the candidate changed after approval")\n')
_DIGEST_CHECK = ("    if authorisation_digest(auth.diffs, auth.request_id, auth.requested_at) != auth.digest:\n"
                 '        raise StaleAuthorisationError("the digest does not match the authorisation")\n')
_FILES = ("    _compare_anchor(auth, stored, candidate_dir)\n    try:\n"
          "        _check_files(auth, old_dir, candidate_dir)\n    except StaleAuthorisationError:\n"
          "        raise\n    except PolicyError as exc:\n"
          '        raise StaleAuthorisationError(f"the authorisation could not be re-checked: {exc}") from exc\n')
_FILES_FIRST = ("    try:\n"
                "        _check_files(auth, old_dir, candidate_dir)\n    except StaleAuthorisationError:\n"
                "        raise\n    except PolicyError as exc:\n"
                '        raise StaleAuthorisationError(f"the authorisation could not be re-checked: {exc}") from exc\n'
                "    _compare_anchor(auth, stored, candidate_dir)\n")

#: (name, edits, named tests). The X2 of the code wrote the first group as F01 to F43.
_X2_MUTANTS: tuple[tuple[str, tuple[tuple[str, str], ...], tuple[str, ...]], ...] = (
    ("approver keys read from the NEW version", (("keys = _approver_map(_load(old_dir, None, None))", "keys = _approver_map(_load(new_dir, None, None))"),), ("t_keys_come_from_the_in_force_base",)),
    ("approval count from (None, None) only", (("min_approvals_to_loosen for d in diffs)", "min_approvals_to_loosen for d in diffs[:1])"),), ("t_count_uses_every_old_document",)),
    ("approval count takes the minimum", (("required = max(_load(old_dir, d.market", "required = min(_load(old_dir, d.market"),), ("t_count_uses_every_old_document",)),
    ("digest omits request_id", (('        "request_id": request_id,\n        "requested_at": requested_at,', '        "requested_at": requested_at,'),), ("t_digest_known_answer",)),
    ("digest omits old_content_hash", ((_DIGEST_FIELDS, '"new_content_hash": d.new_content_hash}\n            for d in diffs'),), ("t_digest_known_answer",)),
    ("digest omits new_content_hash", ((_DIGEST_FIELDS, '"old_content_hash": d.old_content_hash}\n            for d in diffs'),), ("t_digest_known_answer",)),
    ("digest omits market and environment", (('{"market": d.market or "", "environment": d.environment or "",\n             "old_content_hash"', '{\n             "old_content_hash"'),), ("t_digest_known_answer",)),
    ("TRUE_LOOSENS inverted", (("loosens = new if kind is KeyDirection.TRUE_LOOSENS else not new", "loosens = not new"),), ("t_key_kind_directions",)),
    ("bool guard on boolean keys removed", (('        if not isinstance(old, bool) or not isinstance(new, bool):\n            return Direction.UNDECIDABLE, "C-39", "a boolean key is not a bool on both sides"\n', ""),), ("t_c39",)),
    ("a numeric key turned non-numeric is NEUTRAL", (('return Direction.UNDECIDABLE, "C-39", "a numeric key is not numeric on both sides"', 'return Direction.NEUTRAL, "C-37", "a numeric key is not numeric on both sides"'),), ("t_c39",)),
    ("a set-valued key not a list is NEUTRAL", (('return Direction.UNDECIDABLE, "C-39", "a set-valued key is not a list on both sides"', 'return Direction.NEUTRAL, "C-37", "a set-valued key is not a list on both sides"'),), ("t_c39",)),
    ("forced_trim_pct moved to LOWER_LOOSENS", (('"account.pdt_max_day_trades_5d", "portfolio.max_position_pct", "portfolio.forced_trim_pct",', '"account.pdt_max_day_trades_5d", "portfolio.max_position_pct",'), ('"governance.min_approvals_to_loosen", "account.pdt_equity_floor_usd",', '"governance.min_approvals_to_loosen", "account.pdt_equity_floor_usd", "portfolio.forced_trim_pct",'),), ("t_every_key_direction_is_pinned",)),
    ("requires_human moved to TRUE_LOOSENS", (('"kill_switch.requires_human_to_re_enable", "risk_evaluation.evaluate_per_pool",', '"risk_evaluation.evaluate_per_pool",'), ('"governance.risk_deny_override_permitted", "hitl.risk_deny_override_permitted",', '"governance.risk_deny_override_permitted", "hitl.risk_deny_override_permitted", "kill_switch.requires_human_to_re_enable",'),), ("t_every_key_direction_is_pinned",)),
    ("C-40 trigger 3 ignores allowed_values_ref", (("reads_config = rule.threshold_ref is not None or rule.allowed_values_ref is not None", "reads_config = rule.threshold_ref is not None"),), ("t_c40",)),
    ("no C-41 record for policy.override.yaml", (('    out = [("policy.override.yaml", "layers.override")]\n', "    out: list[tuple[str, str]] = []\n"),), ("t_c41",)),
    ("C-40 ignores the mode of R", (("return (rule.mode is RuleMode.ENFORCE and can_kill\n", "return (can_kill\n"),), ("t_c40",)),
    ("C-40 takes G from the new version", (("if global_id in new and _global_kill(old[global_id]) and rule_id < global_id:", "if global_id in new and _global_kill(new[global_id]) and rule_id < global_id:"),), ("t_c40",)),
    ("C-40 trigger 2 counts NEUTRAL records", (("if c.rule_id is not None and c.direction is not Direction.NEUTRAL\n", "if c.rule_id is not None\n"),), ("t_c40",)),
    ("C-40 trigger 3 counts NEUTRAL config records", (("config_moved = any(c.kind in _CONFIG_KINDS and c.direction is not Direction.NEUTRAL\n", "config_moved = any(c.kind in _CONFIG_KINDS\n"),), ("t_c40",)),
    ("C-29 applied to a non-pct target", (('and a.target.endswith("_pct")):', "):"),), ("t_c30",)),
    ("non-Ed25519 guard removed", (('    if not isinstance(key, Ed25519PublicKey):\n        raise PolicyGovernanceError(f"approver {identity}: the key is not Ed25519")\n', ""),), ("t_key_must_be_ed25519",)),
    ("FUTURE boundary includes now", (("    if then > now:\n", "    if then >= now:\n"),), ("t_expiry",)),
    ("C-03 same number is UNDECIDABLE", (("        same = x == y\n", "        same = False\n"),), ("t_c03",)),
    ("unknown basis accepted by the model", (('        if self.basis not in CLASSIFICATION_BASES:\n            raise ValueError(f"unknown classification basis {self.basis}")\n', ""),), ("t_models",)),
    ("rule_id iff check removed", (('        if (self.kind in _RULE_KINDS) != (self.rule_id is not None):\n            raise ValueError("rule_id is set iff the change is about a rule")\n', ""),), ("t_models",)),
    ("an addition may carry an old value", (('        if self.kind in added and self.old is not None:\n            raise ValueError("an addition has no old value")\n', ""),), ("t_models",)),
    ("naive clock check removed", (('    if now.tzinfo is None:\n        raise InForceAnchorError("the store returned a naive clock")\n', ""),), ("t_store_failures",)),
    ("unknown candidate layer not wrapped", (('    try:\n        candidate = set(derive_combinations(candidate_dir, candidate_dir))\n    except PolicyDiffError as exc:\n        raise StaleAuthorisationError(f"the candidate has an unknown layer: {exc}") from exc\n', "    candidate = set(derive_combinations(candidate_dir, candidate_dir))\n"),), ("t_store_failures",)),
    ("anchor accepts a LAYER_ADDED for any layer", (("return any(c.kind is ChangeKind.LAYER_ADDED and c.path == path for c in diff.changes)", "return any(c.kind is ChangeKind.LAYER_ADDED for c in diff.changes)"),), ("t_anchor_needs_its_own_layer",)),
    ("key source is the US document", (("keys = _approver_map(_load(old_dir, None, None))", 'keys = _approver_map(_load(old_dir, "US", None))'),), ("t_keys_come_from_the_in_force_base",)),
    ("C-08 joint fields omit the refs", (('_PREDICATE_FIELDS: Final = (*_THRESHOLD_SOURCES, "allowed_values", "disallowed_values",\n                            "allowed_values_ref")', '_PREDICATE_FIELDS: Final = ("threshold", "allowed_values", "disallowed_values")'),), ("t_c08",)),
    ("inputs compared as a list", ((_SET_FIELDS_TEXT, '_SET_FIELDS: Final = ("allowed_values", "allowed_values_emergency", "disallowed_values",\n                      "exempts")'),), ("t_order_is_not_a_change",)),
    ("exempts and allowed_values compared as lists", ((_SET_FIELDS_TEXT, '_SET_FIELDS: Final = ("inputs",)'),), ("t_order_is_not_a_change",)),
    ("a duplicate approver in the map tolerated", (("if name in out or not isinstance(entry, Mapping):", "if not isinstance(entry, Mapping):"),), ("t_approver_map_is_normalised",)),
    ("identities in the map not normalised", (("    return identity.strip().lower()\n", "    return identity\n"),), ("t_approver_map_is_normalised",)),
    ("same-number config change not NEUTRAL", (('    if x == y:\n        return Direction.NEUTRAL, "C-37", "same number, re-represented"\n', ""),), ("t_c37",)),
    ("digest checked before the candidate", ((_CHECKS + _DIGEST_CHECK, _DIGEST_CHECK + _CHECKS),), ("t_check_order",)),
    ("anchor compared after the files", ((_FILES, _FILES_FIRST),), ("t_first_env_layer",)),
    ("approvals not re-verified at step 7", (("    derived = _derive_authorisation(old_dir, candidate_dir, auth.approvals, auth.request_id,\n                                    auth.requested_at)\n    if derived != auth:\n", "    derived = auth if not auth.approvals else _derive_authorisation(old_dir, candidate_dir, (), auth.request_id, auth.requested_at)\n    if derived != auth:\n"),), ("t_stripped_authorisation",)),
    ("C-36 skipped for an existing grantor", (("before = set(old[grantor].exempts) if grantor in old else set()", "before = set(new[grantor].exempts) if grantor in old else set()"),), ("t_c26",)),
    ("C-41 stops at the first layer removed", (("            out.append(PolicyChange(kind=ChangeKind.LAYER_REMOVED, path=path, rule_id=None,\n", "            return [PolicyChange(kind=ChangeKind.LAYER_REMOVED, path=path, rule_id=None,\n"), ('                                    reason="a layer file disappeared"))\n', '                                    reason="a layer file disappeared")]\n'),), ("t_c41",)),
    ("a removed NEUTRAL key is LOOSENS", (("d = Direction.NEUTRAL if neutral else Direction.LOOSENS", "d = Direction.LOOSENS"),), ("t_c38",)),
    ("the C-13 reason lost", (('return Direction.UNDECIDABLE, "C-13", _SCOPE_REASONS.get(frozenset((old, new)), "unranked")', 'return Direction.UNDECIDABLE, "C-13", "R1"'),), ("t_c13", "t_every_scope_pair_is_classified")),
    # The fixes for X2H-1, X2H-2, X2H-6 and X2H-9.
    ("the dotted-key refusal removed", (('            if not isinstance(k, str) or not k or set(k) & set(".[]"):\n                raise PolicyDiffError(f"config key {k!r} under {prefix!r} cannot be classified: "\n                                      f"it must be a non-empty string without . [ or ]")\n', ""),), ("t_dotted_keys_are_refused",)),
    ("config values compared on the display string", (("else _identity(a[path]) == _identity(b[path]))", "else _canon(a[path]) == _canon(b[path]))"),), ("t_type_changes_are_recorded",)),
    ("the type-change check removed", (("    if _kind(old) != _kind(new):\n", "    if False:\n"),), ("t_type_changes_are_recorded",)),
    ("set members compared on the display string", (("    return None if v is None else frozenset(_identity(x) for x in v)\n", "    return None if v is None else frozenset((str(_canon(x)),) for x in v)\n"),), ("t_type_changes_are_recorded",)),
    ("an empty mapping gives no leaf", (("    if isinstance(obj, Mapping) and obj:\n", "    if isinstance(obj, Mapping):\n"),), ("t_type_changes_are_recorded",)),
    ("modify.to compared on the display string", (("    if _identity(a.to) != _identity(b.to):\n", "    if _canon(a.to) != _canon(b.to):\n"),), ("t_type_changes_are_recorded",)),
    ("_load catches only PolicyError", (('    except Exception as exc:  # noqa: BLE001 - §8: any failure here authorises nothing\n        raise PolicyDiffError(f"{directory} does not load', '    except PolicyError as exc:\n        raise PolicyDiffError(f"{directory} does not load'),), ("t_loader_failures_are_refused",)),
    ("an adapter failure escapes", (("    except Exception as exc:  # noqa: BLE001 - an unreadable store applies nothing\n", "    except KeyError as exc:\n"),), ("t_store_failures",)),
)
EXTRA = tuple(CodeMutation(f"M-{31 + i} {name}", edits, tests)
              for i, (name, edits, tests) in enumerate(_X2_MUTANTS))

MUTATIONS = (
    CodeMutation("M-1 requires_two_person excludes UNDECIDABLE", (
        ("return self.direction in (Direction.LOOSENS, Direction.UNDECIDABLE)",
         "return self.direction is Direction.LOOSENS"),),
        ("t_c08", "t_x5r_g9_each_mutation_is_gated")),
    CodeMutation("M-2 DENY and MODIFY swapped", (
        ('("KILL", "HALT_ENTRIES", "DENY", "MODIFY", "ALLOW")',
         '("KILL", "HALT_ENTRIES", "MODIFY", "DENY", "ALLOW")'),), ("t_c09",)),
    CodeMutation("M-3 HALT_ENTRIES and DENY swapped", (
        ('("KILL", "HALT_ENTRIES", "DENY", "MODIFY", "ALLOW")',
         '("KILL", "DENY", "HALT_ENTRIES", "MODIFY", "ALLOW")'),), ("t_c09",)),
    CodeMutation("M-4 comparison change classified by interval", (
        ('out.add("comparison", old.comparison, new.comparison, Direction.UNDECIDABLE, "C-08",',
         'out.add("comparison", old.comparison, new.comparison, Direction.TIGHTENS if new.comparison'
         ' is Comparison.LT else Direction.UNDECIDABLE, "C-08",'),), ("t_c08",)),
    CodeMutation("M-5 severity classified on its own rank", (
        ('out.add("severity", old.severity, new.severity, Direction.NEUTRAL, "C-14",',
         'out.add("severity", old.severity, new.severity, Direction.LOOSENS, "C-14",'),),
        ("t_c14",)),
    CodeMutation("M-6 approval count read from the new version", (
        ("required = max(_load(old_dir, d.market, d.environment).document.governance",
         "required = max(_load(new_dir, d.market, d.environment).document.governance"),),
        ("t_counts",)),
    CodeMutation("M-7 approver de-duplication removed", (
        ("raw_keys: set[bytes] = set()", "raw_keys: list[bytes] = []"),
        ("raw_keys.add(raw)", "raw_keys.append(raw)"),), ("t_signatures",)),
    CodeMutation("M-8 C-36 records not emitted", (
        ("    changes.extend(_exemption_records(old_rules, new_rules))\n", ""),), ("t_c36",)),
    CodeMutation("M-9 SCOPE_NARROWER_THAN pairs reversed", (
        ('{("pool", "pool_and_consolidated"), ("consolidated", "pool_and_consolidated")}',
         '{("pool_and_consolidated", "pool"), ("pool_and_consolidated", "consolidated")}'),),
        ("t_c12",)),
    CodeMutation("M-10 C-01 and C-02 directions swapped", (
        ('d = (Direction.LOOSENS if y > x else Direction.TIGHTENS if y < x else Direction.NEUTRAL)\n'
         '        out.add("threshold", a, b, d, "C-01"',
         'd = (Direction.TIGHTENS if y > x else Direction.LOOSENS if y < x else Direction.NEUTRAL)\n'
         '        out.add("threshold", a, b, d, "C-01"'),
        ('d = (Direction.TIGHTENS if y > x else Direction.LOOSENS if y < x else Direction.NEUTRAL)\n'
         '        out.add("threshold", a, b, d, "C-02"',
         'd = (Direction.LOOSENS if y > x else Direction.TIGHTENS if y < x else Direction.NEUTRAL)\n'
         '        out.add("threshold", a, b, d, "C-02"'),),
        ("t_c01", "t_diff_agrees_with_loosens_for_on_every_ordinal_threshold")),
    CodeMutation("M-11 config catch-all set to NEUTRAL", (
        ('("**", KeyDirection.UNDECIDABLE),', '("**", KeyDirection.NEUTRAL),'),), ("t_c39",)),
    CodeMutation("M-12 removal of a rule with exempts classified UNDECIDABLE", (
        ('field=None, old=rule.id, new=None, direction=Direction.LOOSENS,',
         'field=None, old=rule.id, new=None, direction=Direction.UNDECIDABLE if rule.exempts else'
         ' Direction.LOOSENS,'),), ("t_c33",)),
    CodeMutation("M-13 C-40 records not emitted", (
        ("    changes.extend(_displacement_records(old_rules, new_rules, changes))\n", ""),),
        ("t_c16", "t_c18")),
    CodeMutation("M-14 derive_combinations ignores market layer files", (
        ('if n.startswith(("policy.market.", "policy.env."))',
         'if n.startswith(("policy.env.",))'),), ("t_combinations_are_derived",)),
    CodeMutation("M-15 the in-force reference read from a directory", (
        ("""    if IN_FORCE_STORE is None:
        raise InForceAnchorError("no in-force store is installed (SPEC-P1.3.1 B6): nothing can "
                                 "be applied by this path")
    try:
        stored = IN_FORCE_STORE.in_force_hashes(conn)
        now = IN_FORCE_STORE.database_time(conn)
        used = IN_FORCE_STORE.request_used(conn, auth.request_id)
    except Exception as exc:  # noqa: BLE001 - an unreadable store applies nothing
        raise InForceAnchorError("the in-force store could not be read") from exc
""", """    stored = {(d.market, d.environment): _load(old_dir, d.market, d.environment).content_hash
              for d in auth.diffs}
    now, used = datetime.now(timezone.utc), False
"""),),
        ("t_anchor_stale_base", "t_no_adapter")),
    CodeMutation("M-16 signature verification skipped", (
        ('verify_signature(digest.encode("ascii"), bytes.fromhex(approval.signature_hex), pem)',
         "pass"),), ("t_signatures",)),
    CodeMutation("M-17 CONFIG_KEY_DIRECTIONS restored to a turnover.* glob", (
        ('    ("**", KeyDirection.UNDECIDABLE),\n)',
         '    ("turnover.*", KeyDirection.HIGHER_LOOSENS),\n    ("**", KeyDirection.UNDECIDABLE),\n)'),
        ('if pattern in (path, "**"):',
         'if pattern in (path, "**") or __import__("fnmatch").fnmatchcase(path, pattern):'),),
        ("t_config_keys_are_exact", "t_c39")),
    CodeMutation("M-18a expiry check removed", (
        ("    _check_age(auth.requested_at, now, auth.request_id)\n", ""),), ("t_expiry",)),
    CodeMutation("M-18b expiry moved after the anchor", (
        ("    _check_age(auth.requested_at, now, auth.request_id)\n"
         "    _compare_anchor(auth, stored, candidate_dir)\n",
         "    _compare_anchor(auth, stored, candidate_dir)\n"
         "    _check_age(auth.requested_at, now, auth.request_id)\n"),), ("t_expiry",)),
    CodeMutation("M-18c expiry measured on the process clock", (
        ("    _check_age(auth.requested_at, now, auth.request_id)\n",
         "    _check_age(auth.requested_at, datetime.now(timezone.utc), auth.request_id)\n"),),
        ("t_expiry",)),
    CodeMutation("M-19 approver keys compared as PEM bytes", (
        ("raw_keys.add(raw)", "raw_keys.add(pem)"),), ("t_signatures",)),
    CodeMutation("M-20 APPROVAL_DIGEST_TAG dropped from the preimage", (
        ('hashlib.sha256(APPROVAL_DIGEST_TAG + canonical_json(payload).encode("utf-8"))',
         'hashlib.sha256(canonical_json(payload).encode("utf-8"))'),), ("t_signatures",)),
    CodeMutation("M-21 C-40's indirect triggers removed", (
        ("fires = (rule_id not in old or rule_id in touched or (reads_config and config_moved)\n"
         "                 or rule_id in unexempted)",
         "fires = rule_id not in old or rule_id in touched"),), ("t_c40",)),
    CodeMutation("M-22a a default adapter installed", (),
                 ("t_store_adapter_assigned_only_by_store_module", "t_defaults_are_none"),
                 append=_ADAPTER),
    CodeMutation("M-22b a default Vault resolver installed", (),
                 ("t_store_adapter_assigned_only_by_store_module", "t_defaults_are_none"),
                 append=_RESOLVER),
    CodeMutation("M-23 the (m, None) anchor applied to any missing row", (
        ("elif diff.environment is not None and _adds_own_env(diff):",
         "elif diff.environment is not None:"),), ("t_first_env_layer",)),
    CodeMutation("M-24 the requested_at real-time check removed", (
        ("        try:\n"
         "            parsed = datetime.strptime(self.requested_at, _UTC_SECOND_FORMAT)\n"
         "        except ValueError as exc:\n"
         '            raise ValueError("requested_at is not a real UTC time") from exc\n'
         "        if parsed.strftime(_UTC_SECOND_FORMAT) != self.requested_at:\n"
         '            raise ValueError("requested_at does not round-trip")\n', ""),),
        ("t_models",)),
    CodeMutation("M-25 conn.execute called directly", (
        ("    _compare_anchor(auth, stored, candidate_dir)\n",
         '    conn.execute("SELECT 1")\n    _compare_anchor(auth, stored, candidate_dir)\n'),),
        ("t_conn_reaches_only_the_store_adapter",)),
    CodeMutation("M-26 the request_used check removed", (
        ("    if used:\n        raise StaleAuthorisationError(",
         "    if False:\n        raise StaleAuthorisationError("),), ("t_replay",)),
    CodeMutation("M-27 the re-derivation at step 7 removed", (
        ("    derived = _derive_authorisation(old_dir, candidate_dir, auth.approvals, auth.request_id,\n"
         "                                    auth.requested_at)\n"
         "    if derived != auth:\n"
         '        raise StaleAuthorisationError("the authorisation does not re-derive to itself")\n',
         ""),), ("t_stripped_authorisation",)),
    CodeMutation("M-28 the raw_key_sha256 comparison removed", (
        ('if hashlib.sha256(raw).hexdigest() != pin.removeprefix("sha256:"):', "if False:"),),
        ("t_signatures",)),
    CodeMutation("M-29 C-42 removed from rule_action_direction", (
        ('    if (new == "HALT_ENTRIES" and old not in ("HALT_ENTRIES", "KILL")\n'
         "            and rule_id not in HALT_ENTRIES_RULES):\n"
         '        return Direction.UNDECIDABLE, "C-42"\n', ""),), ("t_c42",)),
    CodeMutation("M-30 the used-request check moved after expiry", (
        ("    if used:\n"
         '        raise StaleAuthorisationError(f"request {auth.request_id} has already been applied")\n'
         "    _check_age(auth.requested_at, now, auth.request_id)\n",
         "    _check_age(auth.requested_at, now, auth.request_id)\n"
         "    if used:\n"
         '        raise StaleAuthorisationError(f"request {auth.request_id} has already been applied")\n'),),
        ("t_late_replay",)),
    *EXTRA,
)


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def mutated_source(source: str, m: CodeMutation) -> str:
    for old, new in m.edits:
        if source.count(old) != 1:
            raise SystemExit(f"{m.name}: expected one match for {old[:70]!r}, "
                             f"found {source.count(old)}")
        source = source.replace(old, new)
    return source + m.append


def stub_tests(source: str, names: Sequence[str]) -> str:
    """Replace the body of each named test with `return None`."""
    lines = source.split("\n")
    targets = [n for n in ast.parse(source).body
               if isinstance(n, ast.FunctionDef) and n.name in names]
    missing = set(names) - {n.name for n in targets}
    if missing:
        raise SystemExit(f"cannot stub, not found: {sorted(missing)}")
    for fn in sorted(targets, key=lambda n: n.lineno, reverse=True):
        lines[fn.body[0].lineno - 1:fn.end_lineno] = ["    return None"]
    return "\n".join(lines)


def _failed(dst: Path, optimise: bool) -> set[str]:
    cmd = [sys.executable] + (["-O"] if optimise else []) + [SUITE]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    env.pop("P13_PINS_ONLY", None)
    r = subprocess.run(cmd, cwd=dst, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", check=False, env=env)
    names = {line.split(":", 1)[0].removeprefix("FAILED ") for line in r.stdout.splitlines()
             if line.startswith("FAILED ")}
    if r.returncode != 0 and not names:
        names.add("<suite crashed>")
    return names


def run_one(m: CodeMutation, negative_control: bool) -> tuple[str, bool, set[str]]:
    source = _read(ROOT / TARGET)
    suite = _read(ROOT / SUITE)
    with tempfile.TemporaryDirectory() as d:
        dst = Path(d)
        for sub in ("src", "tests", "config"):
            shutil.copytree(ROOT / sub, dst / sub,
                            ignore=shutil.ignore_patterns("__pycache__", "_lint_probe_tmp"))
        (dst / TARGET).write_bytes(mutated_source(source, m).encode("utf-8"))
        if negative_control:
            (dst / SUITE).write_bytes(stub_tests(suite, m.tests).encode("utf-8"))
        plain, optimised = _failed(dst, False), _failed(dst, True)
    want = set(m.tests)
    return m.name, want <= plain and want <= optimised, want - (plain & optimised)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative-control", action="store_true")
    args = ap.parse_args()
    for m in MUTATIONS:  # every text must apply before anything runs
        mutated_source(_read(ROOT / TARGET), m)
    for optimise in (False, True):
        red = _failed(ROOT, optimise)
        if red:
            print(f"[BASELINE FAILED]{' -O:' if optimise else ':'} {sorted(red)}")
            return 1
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
        results = list(pool.map(lambda m: run_one(m, args.negative_control), MUTATIONS))
    caught = 0
    for name, ok, missing in results:
        caught += ok
        print(f"[{'CAUGHT' if ok else 'UNCAUGHT'}] {name}"
              + ("" if ok or args.negative_control else f"  (not failed: {sorted(missing)})"))
    print(f"{caught} of {len(results)} caught")
    return 0 if caught == (0 if args.negative_control else len(results)) else 1


if __name__ == "__main__":
    sys.exit(main())
