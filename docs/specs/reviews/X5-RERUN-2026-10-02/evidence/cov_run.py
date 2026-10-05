"""Run one harness under sys.settrace; dump executed (file,line) for src/ files."""
import sys, json, runpy, os, threading
harness, out = sys.argv[1], sys.argv[2]
SRC = os.path.normcase(os.path.abspath("src"))
hits = {}
def tracer(frame, event, arg):
    fn = frame.f_code.co_filename
    if not os.path.normcase(os.path.abspath(fn)).startswith(SRC):
        return None
    s = hits.setdefault(os.path.relpath(fn).replace("\\", "/"), set())
    def local(frame, event, arg):
        if event == "line":
            s.add(frame.f_lineno)
        return local
    if event == "call":
        s.add(-frame.f_code.co_firstlineno)  # negative = code object entered
    return local
import timeit as _ti
_ti.timeit = lambda stmt, number=1, **k: (stmt(), 0.0)[1]  # tracer overhead must not fail a wall-clock test
threading.settrace(tracer); sys.settrace(tracer)
sys.argv = [harness]
rc = 0
try:
    runpy.run_path(harness, run_name="__main__")
except SystemExit as e:
    rc = e.code or 0
finally:
    sys.settrace(None)
json.dump({"rc": rc, "hits": {k: sorted(v) for k, v in hits.items()}}, open(out, "w"))
