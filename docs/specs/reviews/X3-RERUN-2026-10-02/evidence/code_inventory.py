"""X3 re-run: inventory the Stage 1 code so contracts can be compared with it.

AST only — nothing is imported or executed from the repository.
"""
import ast
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]  # repository root (path made relative for publication)
PY = ["src/domain/models.py", "src/config/loader.py", "src/audit/events.py", "src/audit/chain.py"]


def sig(fn: ast.FunctionDef) -> str:
    a = fn.args
    parts = []
    pos = a.posonlyargs + a.args
    defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    for arg, d in zip(pos, defaults):
        s = arg.arg + (": " + ast.unparse(arg.annotation) if arg.annotation else "")
        if d is not None:
            s += " = " + ast.unparse(d)
        parts.append(s)
    if a.vararg:
        parts.append("*" + a.vararg.arg)
    elif a.kwonlyargs:
        parts.append("*")
    for arg, d in zip(a.kwonlyargs, a.kw_defaults):
        s = arg.arg + (": " + ast.unparse(arg.annotation) if arg.annotation else "")
        if d is not None:
            s += " = " + ast.unparse(d)
        parts.append(s)
    ret = " -> " + ast.unparse(fn.returns) if fn.returns else ""
    return f"({', '.join(parts)}){ret}"


def inventory(rel: str) -> dict:
    tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
    out = {"classes": {}, "functions": {}, "constants": {}}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) for b in node.bases]
            members, fields, methods = [], [], {}
            for b in node.body:
                if isinstance(b, ast.Assign) and len(b.targets) == 1 and isinstance(b.targets[0], ast.Name):
                    members.append((b.targets[0].id, ast.unparse(b.value)[:80]))
                elif isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name):
                    fields.append((b.target.id, ast.unparse(b.annotation)))
                elif isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods[b.name] = sig(b)
            out["classes"][node.name] = {
                "line": node.lineno, "bases": bases, "members": members,
                "fields": fields, "methods": methods,
            }
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out["functions"][node.name] = {"line": node.lineno, "sig": sig(node)}
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            tgt = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(tgt, ast.Name) and tgt.id.isupper():
                val = node.value
                out["constants"][tgt.id] = {
                    "line": node.lineno,
                    "value": ast.unparse(val)[:400] if val is not None else None,
                }
    return out


def sql_inventory() -> dict:
    sql = (REPO / "migrations/0001_initial.sql").read_text(encoding="utf-8")
    nocomment = re.sub(r"--[^\n]*", "", sql)
    out = {}
    out["tables"] = re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?trading\.(\w+)", nocomment)
    out["hypertables"] = re.findall(r"create_hypertable\(\s*'trading\.(\w+)'", nocomment)
    out["caggs"] = re.findall(r"CREATE MATERIALIZED VIEW (?:IF NOT EXISTS )?trading\.(\w+)", nocomment)
    out["functions"] = re.findall(r"CREATE (?:OR REPLACE )?FUNCTION trading\.(\w+)\s*\(([^)]*)\)", nocomment)
    out["indexes"] = re.findall(r"CREATE (?:UNIQUE )?INDEX (\w+)", nocomment)
    out["static_triggers"] = re.findall(r"CREATE (?:CONSTRAINT )?TRIGGER (\w+)", nocomment)
    out["roles"] = re.findall(r"CREATE ROLE (\w+)", nocomment)
    out["n_check"] = len(re.findall(r"\bCHECK\s*\(", nocomment))
    out["n_unique"] = len(re.findall(r"\bUNIQUE\b", nocomment))
    out["n_exclude"] = len(re.findall(r"\bEXCLUDE USING\b", nocomment))
    out["n_security_definer"] = len(re.findall(r"SECURITY DEFINER", nocomment))
    out["n_enable_always"] = len(re.findall(r"ENABLE ALWAYS TRIGGER", nocomment))
    out["header_comment"] = sql.splitlines()[:6]
    # CHECK (col IN (...)) value lists, per table
    checks = {}
    for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?trading\.(\w+)\s*\((.*?)\n\)\s*(?:WITH[^;]*)?;", nocomment, re.S):
        t, body = m.group(1), m.group(2)
        for c in re.finditer(r"(\w+)\s+IN\s*\(\s*((?:'[^']*'\s*,?\s*)+)\)", body):
            vals = re.findall(r"'([^']*)'", c.group(2))
            checks.setdefault(t, {}).setdefault(c.group(1), [])
            if vals not in checks[t][c.group(1)]:
                checks[t][c.group(1)].append(vals)
    out["in_checks"] = checks
    return out


def main() -> None:
    res = {rel: inventory(rel) for rel in PY}
    res["sql"] = sql_inventory()
    Path(sys.argv[1]).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for rel in PY:
        inv = res[rel]
        print(f"{rel}: {len(inv['classes'])} classes, {len(inv['functions'])} module functions, "
              f"{len(inv['constants'])} UPPER constants")
    s = res["sql"]
    print("sql: tables", len(s["tables"]), "| hypertables", len(s["hypertables"]), "| caggs", len(s["caggs"]),
          "| functions", len(s["functions"]), "| indexes", len(s["indexes"]),
          "| static triggers", len(s["static_triggers"]), "| CHECK(", s["n_check"],
          "| UNIQUE", s["n_unique"], "| EXCLUDE", s["n_exclude"],
          "| SECURITY DEFINER", s["n_security_definer"], "| ENABLE ALWAYS", s["n_enable_always"])
    print("sql header:", s["header_comment"])
    print("hypertables:", s["hypertables"])
    print("caggs:", s["caggs"])
    print("functions:", [f[0] for f in s["functions"]])
    print("roles:", s["roles"])
    print("tables:", s["tables"])


if __name__ == "__main__":
    main()
