import json, glob, sys, collections, inspect
sys.path.insert(0, "src")
import pydantic
from domain import models as m
from audit import events as e, chain as c
from config import loader as l
ok = collections.Counter(); bad = collections.Counter()
for f in glob.glob(sys.argv[1] + "/inst_verify_*.json"):
    d = json.load(open(f)); ok.update(d["ok"]); bad.update(d["bad"])
for mod in (m, e, c, l):
    cls = [v for k, v in vars(mod).items() if inspect.isclass(v) and issubclass(v, pydantic.BaseModel) and v.__module__ == mod.__name__]
    never = [k.__qualname__ for k in cls if not ok[k.__module__ + "." + k.__qualname__] and not bad[k.__module__ + "." + k.__qualname__]]
    onlybad = [k.__qualname__ for k in cls if not ok[k.__module__ + "." + k.__qualname__] and bad[k.__module__ + "." + k.__qualname__]]
    noreject = [k.__qualname__ for k in cls if ok[k.__module__ + "." + k.__qualname__] and not bad[k.__module__ + "." + k.__qualname__]]
    print(f"{mod.__name__}: {len(cls)} pydantic models; never constructed {len(never)}: {never}")
    print(f"    only ever rejected (no valid instance built): {onlybad}")
    print(f"    built but never rejected by any test ({len(noreject)}): {noreject}")
    enums = [v for k, v in vars(mod).items() if inspect.isclass(v) and issubclass(v, __import__('enum').Enum) and v.__module__ == mod.__name__]
    print(f"    enums {len(enums)}; exception classes {len([v for v in vars(mod).values() if inspect.isclass(v) and issubclass(v, Exception) and v.__module__ == mod.__name__])}")
