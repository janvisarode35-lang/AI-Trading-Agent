import shutil, subprocess, sys, pathlib, re
S = pathlib.Path(sys.argv[1]); base = S / "copy"; work = S / "sabp"
SUITES = ["verify_p11_invariants","verify_p11_x2_regressions","verify_p11_x5_conditions","verify_p13_config","verify_p14_audit"]
def block(s, rid):
    a = s.index(f"  - id: {rid}\n"); b = s.find("\n  - id: ", a + 5); return a, (b if b != -1 else len(s))
def in_rule(rid, old, new):
    def f(s):
        a, b = block(s, rid); blk = s[a:b]
        assert blk.count(old) == 1, (rid, old, blk.count(old))
        return s[:a] + blk.replace(old, new) + s[b:]
    return f
def glob(old, new):
    def f(s):
        assert s.count(old) == 1, (old, s.count(old)); return s.replace(old, new)
    return f
MUT = [
 ("P01 EXP-001 position cap 5% -> 6%", in_rule("EXP-001", "threshold: 0.050", "threshold: 0.060")),
 ("P02 EXP-001 comparison lte -> gte", in_rule("EXP-001", "comparison: lte", "comparison: gte")),
 ("P03 EXP-002 action DENY -> ALLOW", in_rule("EXP-002", "    action: DENY", "    action: ALLOW")),
 ("P04 LOSS-001 daily loss mode enforce -> monitor", in_rule("LOSS-001", "mode: enforce", "mode: monitor")),
 ("P05 LOSS-004 consolidated drawdown 10% -> 20%", in_rule("LOSS-004", "threshold: 0.100", "threshold: 0.200")),
 ("P06 LOSS-003 drawdown action KILL -> DENY", in_rule("LOSS-003", "    action: KILL", "    action: DENY")),
 ("P07 EXEC-001 MARKET allowed by default", in_rule("EXEC-001", "allowed_values: [LIMIT]", "allowed_values: [LIMIT, MARKET]")),
 ("P08 STOP-001 comparison eq -> lte", in_rule("STOP-001", "comparison: eq", "comparison: lte")),
 ("P09 RATE-001 scope global -> strategy", in_rule("RATE-001", "scope: global", "scope: strategy")),
 ("P10 LIQ-001 action MODIFY -> ALLOW", in_rule("LIQ-001", "    action: MODIFY", "    action: ALLOW")),
 ("P11 PDT floor 25000 -> 1", glob("pdt_equity_floor_usd: 25000", "pdt_equity_floor_usd: 1")),
 ("P12 US min price 5.00 -> 0.50", glob('min_price_usd: "5.00"', 'min_price_usd: "0.50"')),
 ("P13 KILL-001 mode enforce -> monitor", in_rule("KILL-001", "mode: enforce", "mode: monitor")),
 ("P14 DATA-001 staleness 600 -> 86400", in_rule("DATA-001", "threshold: 600", "threshold: 86400")),
]
for name, fn in MUT:
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(base, work, ignore=shutil.ignore_patterns("__pycache__"))
    p = work / "config/policy.yaml"; s = p.read_text(encoding="utf-8")
    try: s2 = fn(s)
    except AssertionError as e: print(f"{name}: NOT APPLIED {e}"); continue
    p.write_text(s2, encoding="utf-8", newline="\n")
    failed = []
    for t in SUITES:
        r = subprocess.run(["py", "-3.11", "-O", f"tests/{t}.py"], cwd=work, capture_output=True, text=True)
        if r.returncode != 0:
            fl = re.findall(r"^FAILED (\S+)", r.stdout, re.M)
            failed.append(f"{t.replace('verify_','')}: {', '.join(x.rstrip(':') for x in fl[:3]) or ('exit ' + str(r.returncode) + ' ' + (r.stderr.strip().splitlines() or [''])[-1][:90])}")
    print(f"{name}\n    -O: {'; '.join(failed) or 'ALL GREEN - NOT DETECTED'}")
shutil.rmtree(work)
