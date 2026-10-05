import shutil, subprocess, sys, pathlib, re
S = pathlib.Path(sys.argv[1]); base = S / "copy"; work = S / "sab"
SUITES = ["verify_p11_invariants","verify_p11_p12_contract","verify_p11_x2_regressions","verify_p11_x5_conditions","verify_p13_config","verify_p14_audit"]
MUT = [tuple(l.split("|")) for l in (S / "mut2.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
for name, path, old, new in MUT:
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(base, work, ignore=shutil.ignore_patterns("__pycache__"))
    p = work / path; s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        print(f"{name}: MUTATION NOT APPLIED (matches={s.count(old)})"); continue
    p.write_text(s.replace(old, new), encoding="utf-8")
    res = []
    for mode in ([], ["-O"]):
        failed = []
        for t in SUITES:
            r = subprocess.run(["py", "-3.11", *mode, f"tests/{t}.py"], cwd=work, capture_output=True, text=True)
            if r.returncode != 0:
                n = len(re.findall(r"^FAILED", r.stdout, re.M))
                failed.append(f"{t.replace('verify_','')}({n or 'exit'+str(r.returncode)})")
        res.append(", ".join(failed) or "ALL GREEN - NOT DETECTED")
    print(f"{name}\n    normal: {res[0]}\n    -O    : {res[1]}")
shutil.rmtree(work)
