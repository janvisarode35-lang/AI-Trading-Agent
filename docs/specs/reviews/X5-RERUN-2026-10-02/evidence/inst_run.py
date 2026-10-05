import sys, json, runpy, collections, io, contextlib
import pydantic
harness, out = sys.argv[1], sys.argv[2]
ok = collections.Counter(); bad = collections.Counter()
_init = pydantic.BaseModel.__init__
def init(self, /, **data):
    n = type(self).__module__ + "." + type(self).__qualname__
    try:
        _init(self, **data)
    except BaseException:
        bad[n] += 1; raise
    ok[n] += 1
pydantic.BaseModel.__init__ = init
_mv = pydantic.BaseModel.model_validate.__func__
def mv(cls, *a, **k):
    n = cls.__module__ + "." + cls.__qualname__
    try:
        r = _mv(cls, *a, **k)
    except BaseException:
        bad[n] += 1; raise
    ok[n] += 1; return r
pydantic.BaseModel.model_validate = classmethod(mv)
sys.argv = [harness]
try:
    with contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(harness, run_name="__main__")
except SystemExit:
    pass
json.dump({"ok": ok, "bad": bad}, open(out, "w"))
