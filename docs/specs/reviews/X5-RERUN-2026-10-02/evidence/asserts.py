import ast,sys,pathlib,subprocess
for p in sorted(pathlib.Path("tests").glob("*.py")):
    t=ast.parse(p.read_text(encoding="utf-8"))
    n=sum(isinstance(x,ast.Assert) for x in ast.walk(t))
    fns=[f.name for f in ast.walk(t) if isinstance(f,ast.FunctionDef)]
    tf=[f for f in fns if f.startswith("t_") or f.startswith("test")]
    print(p.name,"bare_assert=",n,"funcs=",len(fns),"t_funcs=",len(tf))
for p in ["src/domain/models.py","src/audit/events.py","src/audit/chain.py","src/config/loader.py"]:
    t=ast.parse(pathlib.Path(p).read_text(encoding="utf-8"))
    print(p,"bare_assert=",sum(isinstance(x,ast.Assert) for x in ast.walk(t)))
