import ast, json, sys, glob, os, types
runs = sys.argv[1:]
hits = {}
for r in runs:
    d = json.load(open(r))
    for k, v in d["hits"].items():
        hits.setdefault(k, set()).update(v)
def exec_lines(code, acc):
    for _, _, ln in code.co_lines():
        if ln: acc.add(ln)
    for c in code.co_consts:
        if isinstance(c, types.CodeType): exec_lines(c, acc)
tot_pub = tot_un = 0
for mod in ["src/domain/models.py", "src/audit/events.py", "src/audit/chain.py", "src/config/loader.py"]:
    srcs = open(mod, encoding="utf-8").read()
    tree = ast.parse(srcs)
    lines = set(); exec_lines(compile(srcs, mod, "exec"), lines)
    # drop docstring-only lines: co_lines does not include docstrings as executable in 3.11 except module/class assignment
    h = {l for l in hits.get(mod, set()) if l > 0}
    covered = lines & h
    funcs = []
    class V(ast.NodeVisitor):
        def __init__(s): s.stack = []
        def visit_ClassDef(s, n):
            s.stack.append(n.name); s.generic_visit(n); s.stack.pop()
        def visit_FunctionDef(s, n):
            decos = [ast.unparse(d) for d in n.decorator_list]
            body = n.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
                body = body[1:]
            bl = set()
            for b in body:
                for x in ast.walk(b):
                    if hasattr(x, "lineno"): bl.add(x.lineno)
            bl &= lines
            funcs.append((".".join(s.stack + [n.name]), n.name, n.lineno, decos, bl, bool(s.stack) and False))
            s.stack.append(n.name); s.generic_visit(n); s.stack.pop()
        visit_AsyncFunctionDef = visit_FunctionDef
    V().visit(tree)
    pub = [f for f in funcs if not f[1].startswith("_")]
    val = [f for f in pub if any("validator" in d or "field_serializer" in d or "model_serializer" in d for d in f[3])]
    api = [f for f in pub if f not in val]
    def unex(fs): return [f for f in fs if f[4] and not (f[4] & h)] + [f for f in fs if not f[4]]
    print(f"\n== {mod}")
    print(f" executable lines {len(lines)}  executed {len(covered)}  = {100*len(covered)/len(lines):.1f}%")
    print(f" defs total {len(funcs)}; non-underscore {len(pub)} (validators {len(val)}, API {len(api)}); underscore {len(funcs)-len(pub)}")
    for label, fs in (("API", api), ("validators", val), ("underscore", [f for f in funcs if f[1].startswith('_')])):
        u = [f for f in fs if f[4] and not (f[4] & h)]
        nobody = [f for f in fs if not f[4]]
        print(f" {label}: never executed {len(u)} / {len(fs)}" + (f"  (no executable body: {len(nobody)})" if nobody else ""))
        for f in u: print(f"     - {f[0]}  line {f[2]}  {f[3] if f[3] else ''}")
        for f in nobody: print(f"     ~ {f[0]}  line {f[2]} (docstring-only body)")
    tot_pub += len(api); tot_un += len([f for f in api if f[4] and not (f[4] & h)])
print(f"\nTOTAL API never executed: {tot_un} / {tot_pub}")
