"""SPEC-P0.2-PROVIDERS verification. Runs the spec's typed block and checks its tables, so that a
score, a selection, a gate or an identifier cannot change without this file noticing.

Pattern: the historical tests/verify_p13_config.py (require() instead of assert, check() collecting
PASS and FAIL, every t_ function run in sorted order, exit code 1 on any failure).

Usage: py -3.11 v2/tests/providers/verify_p02_spec.py [path to a copy of the spec]
"""
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
SPEC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "new specs" / "SPEC-P0.2-PROVIDERS.md"
TEXT = SPEC.read_bytes().decode("utf-8").replace("\r\n", "\n")

NS = {}
BLOCK = re.search(r"```python\n(.*?)\n```", TEXT, re.S).group(1)
exec(compile(BLOCK, "spec-block", "exec"), NS)
ProviderId, Market, Capability = NS["ProviderId"], NS["Market"], NS["Capability"]
SelectionStatus, LicensedUse = NS["SelectionStatus"], NS["LicensedUse"]
AdjustmentBasis, BarResolution, DormancyStatus = NS["AdjustmentBasis"], NS["BarResolution"], NS["DormancyStatus"]
ProviderSelection, ClientThrottle, RateLimitFact = NS["ProviderSelection"], NS["ClientThrottle"], NS["RateLimitFact"]
VendorSeriesSnapshot, AccountActivity = NS["VendorSeriesSnapshot"], NS["AccountActivity"]
ResearchGateApproval = NS["ResearchGateApproval"]
research_gate_open, publication_data_cleared = NS["research_gate_open"], NS["publication_data_cleared"]
dormancy_status, throttle_matches = NS["dormancy_status"], NS["throttle_matches"]
row_cleared, NOT_SIGNAL_INPUTS, MARKETLESS = NS["row_cleared"], NS["NOT_SIGNAL_INPUTS"], NS["MARKETLESS"]
ProviderSelectionSet = NS["ProviderSelectionSet"]

TODAY = date(2026, 10, 30)
WEIGHTS = (30, 20, 15, 15, 10, 10)
AUDIT = UUID("00000000-0000-4000-8000-000000000001")
AUDIT_B = UUID("00000000-0000-4000-8000-000000000002")
EXCLUDED = {Capability.BROKER_EXECUTION, Capability.INTRADAY_BARS, Capability.FX_REFERENCE}
SIGNAL_INPUTS = (Capability.EOD_BARS, Capability.INSTRUMENT_MASTER, Capability.CORPORATE_ACTIONS, Capability.FUNDAMENTALS,
                 Capability.NEWS, Capability.SECTOR_TAXONOMY, Capability.CALENDAR, Capability.MACRO, Capability.LLM)
PASS, FAIL = [], []


def require(cond, msg=""):
    """Unconditional check. Replaces bare `assert`, which `python -O` strips (X5 GAP-2)."""
    if not cond:
        raise AssertionError(msg)


def rejected(fn):
    try:
        fn()
    except (ValidationError, ValueError):
        return True
    return False


def section(start, end):
    return TEXT[TEXT.index(start):TEXT.index(end)]


def selections():
    names = (("Upstox", "UPSTOX"), ("Fyers", "FYERS"), ("Massive", "MASSIVE"), ("Alpaca Market Data", "ALPACA_DATA"),
             ("Alpaca Trading", "ALPACA_TRADING"), ("Alpaca", "ALPACA_DATA"), ("Zerodha", "ZERODHA_KITE"),
             ("SEC EDGAR", "SEC_EDGAR"), ("FMP", "FMP"), ("Finnhub", "FINNHUB"), ("FRED", "FRED"),
             ("DeepSeek", "DEEPSEEK"), ("OpenAI", "OPENAI"), ("NYSE", "REVIEWED_CALENDAR_FILE"))

    def provider(text):
        if text.startswith(("none", "not selected")):
            return None
        return next(ProviderId[v] for k, v in names if text.startswith(k))

    out = {}
    for line in section("### 6.3 Selection", "Edge cases of the selection rules").splitlines():
        if not re.match(r"\| SEL-\d+ \|", line):
            continue
        sid, cap, market, primary, backup, status, items, use = [c.strip() for c in line.strip().strip("|").split("|")]
        if cap.startswith("streaming"):
            continue
        out[sid] = ProviderSelection(
            capability=Capability(cap), market=None if market == "none" else Market(market), primary=provider(primary),
            backup=provider(backup), status=SelectionStatus(status),
            blocked_by=tuple(x.strip() for x in items.split(",")), licensed_use=LicensedUse(use))
    return out


def selection_set():
    return ProviderSelectionSet(rows=tuple(selections().values()))


def snapshot(**kw):
    good = dict(snapshot_id="s1", provider=ProviderId.UPSTOX, market=Market.IN, instrument_ref="INE062A01020",
                resolution=BarResolution.ONE_DAY, adjustment_basis=AdjustmentBasis.UNSTATED,
                retrieved_at=datetime(2026, 10, 30, 14, 0, tzinfo=timezone.utc), first_session=date(2025, 11, 3),
                last_session=date(2026, 10, 30), content_sha256="a" * 64)
    return VendorSeriesSnapshot(**{**good, **kw})


def t_enum_sizes():
    for enum, size in ((ProviderId, 15), (Capability, 12), (NS["ProviderErrorClass"], 13), (AdjustmentBasis, 3),
                       (BarResolution, 2), (LicensedUse, 2), (DormancyStatus, 3)):
        require(len(enum) == size, enum)


def t_exclusion_set_is_pinned():
    require(NOT_SIGNAL_INPUTS == EXCLUDED, NOT_SIGNAL_INPUTS)
    require(set(Capability) == EXCLUDED | set(SIGNAL_INPUTS))


def t_matrix_arithmetic():
    rows = 0
    for line in section("### 6.2 Scores", "### 6.3 Selection").splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 10 and c[3].isdigit():
            rows += 1
            total = sum(w * int(p) for w, p in zip(WEIGHTS, c[3:9]))
            require(total % 5 == 0 and total // 5 == int(c[9]), line)
    require(rows == 32, rows)


def t_selection_states():
    sel = selections()
    require(len(sel) == 21, len(sel))
    require(not any(s.status is SelectionStatus.SELECTED for s in sel.values()))
    require({k for k, s in sel.items() if s.status is SelectionStatus.UNFILLED} == {"SEL-13", "SEL-18", "SEL-23"})
    require({k for k, s in sel.items() if s.status is SelectionStatus.BLOCKED} == {"SEL-9", "SEL-10"})
    require(sel["SEL-22"].backup is None)
    require(all(s.licensed_use is LicensedUse.NONE and s.licence_audit_id is None for s in sel.values()))


def t_every_india_data_row_names_the_licence_question():
    for k, s in selections().items():
        if s.market is Market.IN and s.capability is not Capability.BROKER_EXECUTION:
            require("OQ-68" in s.blocked_by, k)


def cleared_rows(skip=None, uncleared=None):
    rows = []
    for cap in SIGNAL_INPUTS:
        if cap is skip:
            continue
        ok = cap is not uncleared
        rows.append(ProviderSelection(
            capability=cap, market=None if cap in MARKETLESS else Market.IN, primary=ProviderId.UPSTOX, backup=None,
            status=SelectionStatus.SELECTED if ok else SelectionStatus.PROVISIONAL, blocked_by=() if ok else ("OQ-68",),
            licensed_use=LicensedUse.PUBLICATION if ok else LicensedUse.NONE, licence_audit_id=AUDIT if ok else None))
    return ProviderSelectionSet(rows=tuple(rows))


def t_publication_stays_off_until_every_capability_is_cleared():
    rows = selection_set()
    require(not publication_data_cleared(Market.IN, rows))
    require(not publication_data_cleared(Market.US, rows))
    require(not publication_data_cleared(Market.IN, ProviderSelectionSet(rows=())))
    require(publication_data_cleared(Market.IN, cleared_rows()), "a full cleared set clears")
    require(not publication_data_cleared(Market.US, cleared_rows()), "India rows do not clear the US")
    one = ProviderSelectionSet(rows=cleared_rows().rows[:1])
    require(not publication_data_cleared(Market.IN, one), "one row is not enough")
    for cap in SIGNAL_INPUTS:
        require(not publication_data_cleared(Market.IN, cleared_rows(skip=cap)), ("absent", cap))
        require(not publication_data_cleared(Market.IN, cleared_rows(uncleared=cap)), ("uncleared", cap))


def t_row_level_check():
    rows = cleared_rows()
    require(row_cleared(ProviderId.UPSTOX, Capability.EOD_BARS, Market.IN, rows))
    require(row_cleared(ProviderId.UPSTOX, Capability.MACRO, Market.IN, rows), "market-less rows count")
    require(not row_cleared(ProviderId.FYERS, Capability.EOD_BARS, Market.IN, rows), "another provider")
    require(not row_cleared(ProviderId.UPSTOX, Capability.EOD_BARS, Market.US, rows), "another market")
    require(not row_cleared(ProviderId.UPSTOX, Capability.INTRADAY_BARS, Market.IN, rows), "no such row")
    require(not row_cleared(ProviderId.UPSTOX, Capability.EOD_BARS, Market.IN, selection_set()), "not licensed")
    require(not row_cleared(ProviderId.FYERS, Capability.EOD_BARS, Market.IN, selection_set()), "an unlicensed backup")
    require(not row_cleared(None, Capability.EOD_BARS, Market.IN, rows), "bad input closes it")
    llm = ProviderSelectionSet(rows=(ProviderSelection(
        capability=Capability.LLM, market=None, primary=ProviderId.DEEPSEEK, backup=ProviderId.OPENAI,
        status=SelectionStatus.SELECTED, licensed_use=LicensedUse.PUBLICATION, licence_audit_id=AUDIT,
        backup_licence_audit_id=AUDIT_B),))
    require(row_cleared(ProviderId.DEEPSEEK, Capability.LLM, Market.IN, llm))
    require(row_cleared(ProviderId.OPENAI, Capability.LLM, Market.IN, llm), "the fixed fallback, with its own record")
    require(not row_cleared(ProviderId.FYERS, Capability.LLM, Market.IN, llm))


def t_one_row_per_key():
    a = cleared_rows().rows[0]
    b = ProviderSelection(capability=a.capability, market=a.market, primary=ProviderId.FYERS, backup=None,
                          status=SelectionStatus.PROVISIONAL, blocked_by=("OQ-68",))
    require(rejected(lambda: ProviderSelectionSet(rows=(a, b))))


def t_rows_load_from_json_text():
    for sid, row in selections().items():
        require(ProviderSelection.model_validate_json(row.model_dump_json()) == row, sid)
    text = ('{"capability":"eod_bars","market":"IN","primary":"upstox","backup":"fyers","status":"PROVISIONAL",'
            '"blocked_by":["OQ-68"]}')
    require(ProviderSelection.model_validate_json(text).blocked_by == ("OQ-68",))
    rec = AccountActivity.model_validate_json('{"provider":"upstox","last_activity_on":"2026-01-01","alert_after_days":[300,330]}')
    require(rec.alert_after_days == (300, 330))


def t_india_rows_are_as_decided():
    want = {"SEL-4": ("UPSTOX", "FYERS", "PROVISIONAL"), "SEL-6": ("UPSTOX", "FYERS", "PROVISIONAL"),
            "SEL-8": ("UPSTOX", None, "PROVISIONAL"), "SEL-10": ("UPSTOX", None, "BLOCKED"),
            "SEL-12": ("UPSTOX", None, "PROVISIONAL"), "SEL-14": ("UPSTOX", None, "PROVISIONAL"),
            "SEL-16": ("UPSTOX", None, "PROVISIONAL"), "SEL-22": ("UPSTOX", None, "PROVISIONAL")}
    sel = selections()
    for sid, (primary, backup, status) in want.items():
        s = sel[sid]
        require(s.primary is ProviderId[primary] and s.status is SelectionStatus[status], sid)
        require(s.backup is (ProviderId[backup] if backup else None), sid)


def throttle_rows(prefix):
    line = next(l for l in TEXT.splitlines() if l.startswith(prefix))
    _, _, limits, _, budgets = [c.strip() for c in line.strip().strip("|").split("|")]
    rx = r"([\d,]+) per (second|minute|30 minutes|day)"
    pairs = list(zip(re.findall(rx, limits), re.findall(rx, budgets)))
    require(len(pairs) == 3, line)
    seconds = {"second": 1, "minute": 60, "30 minutes": 1800, "day": 86400}
    for (doc, win), (cli, win2) in pairs:
        require(win == win2, line)
        yield int(doc.replace(",", "")), int(cli.replace(",", "")), seconds[win]


def t_throttle_rows_are_half_of_the_limit():
    require([d for d, _, _ in throttle_rows("| THR-13 |")] == [50, 500, 2000])
    require([d for d, _, _ in throttle_rows("| THR-14 |")] == [5, 50, 5000])
    for prefix in ("| THR-13 |", "| THR-14 |"):
        for doc, cli, _ in throttle_rows(prefix):
            require(cli == doc // 2, (prefix, doc, cli))


def t_every_new_row_exists():
    for kind, low, high in (("PE", 17, 25), ("E", 33, 36), ("THR", 13, 14), ("UP", 40, 48), ("D", 39, 46), ("A", 76, 83),
                            ("NB", 63, 73), ("BQ", 48, 53), ("OQ", 67, 80), ("F", 77, 108), ("SEL", 22, 23)):
        rows = {int(x) for x in re.findall(rf"^\| {kind}-(\d+) \|", TEXT, re.M)}
        missing = set(range(low, high + 1)) - rows
        require(not missing, (kind, missing))


def t_publication_needs_a_licence_record():
    good = dict(capability=Capability.EOD_BARS, market=Market.IN, primary=ProviderId.UPSTOX, backup=None,
                status=SelectionStatus.SELECTED, licensed_use=LicensedUse.PUBLICATION, licence_audit_id=AUDIT)
    ProviderSelection(**good)
    for name, kw in (("provisional", {"status": SelectionStatus.PROVISIONAL, "blocked_by": ("OQ-68",)}),
                     ("no record", {"licence_audit_id": None}),
                     ("an unlicensed backup", {"backup": ProviderId.FYERS}),
                     ("a backup record with no backup", {"backup_licence_audit_id": AUDIT_B}),
                     ("one record for two providers", {"backup": ProviderId.FYERS, "backup_licence_audit_id": AUDIT}),
                     ("record without a licence", {"licensed_use": LicensedUse.NONE}),
                     ("backup record on an uncleared row", {"status": SelectionStatus.PROVISIONAL, "blocked_by": ("OQ-68",),
                                                            "licensed_use": LicensedUse.NONE, "licence_audit_id": None,
                                                            "backup": ProviderId.FYERS, "backup_licence_audit_id": AUDIT_B})):
        require(rejected(lambda kw=kw: ProviderSelection(**{**good, **kw})), name)
    ProviderSelection(**{**good, "backup": ProviderId.FYERS, "backup_licence_audit_id": AUDIT_B})


def t_throttles_are_half_and_match_their_facts():
    url = "https://upstox.com/developer/api-documentation/rate-limiting/"
    for prov, prefix in ((ProviderId.UPSTOX, "| THR-13 |"), (ProviderId.FYERS, "| THR-14 |")):
        for doc, cli, win in throttle_rows(prefix):
            fact = RateLimitFact(provider=prov, scope="s", max_count=doc, window_seconds=win, basis=NS["LimitBasis"].DOCUMENTED,
                                 verification=NS["VerificationLevel"].PRIMARY_FULL, source_url=url, retrieved_on=TODAY)
            throttle = ClientThrottle(provider=prov, scope="s", documented_max_count=doc, client_max_count=cli, window_seconds=win)
            require(throttle_matches(throttle, fact))
            wrong = ClientThrottle(provider=prov, scope="s", documented_max_count=doc * 2, client_max_count=cli, window_seconds=win)
            require(not throttle_matches(wrong, fact))
    require(rejected(lambda: ClientThrottle(provider=ProviderId.FYERS, scope="s", documented_max_count=5,
                                            client_max_count=3, window_seconds=1)))


def t_snapshot_identity():
    a = snapshot()
    require(a != snapshot(snapshot_id="s2"), "two fetches on one day must differ")
    require(a != snapshot(instrument_ref="INE040A01034"), "two instruments must differ")
    require(a.content_sha256 != snapshot(content_sha256="b" * 64).content_sha256)


def t_snapshot_rejections():
    fyers = dict(provider=ProviderId.FYERS, adjustment_basis=AdjustmentBasis.VENDOR_ADJUSTED)
    snapshot(**fyers)
    snapshot(provider=ProviderId.MASSIVE, market=Market.US, adjustment_basis=AdjustmentBasis.RAW)
    for name, kw in (("fyers raw", {**fyers, "adjustment_basis": AdjustmentBasis.RAW}),
                     ("fyers unstated", {**fyers, "adjustment_basis": AdjustmentBasis.UNSTATED}),
                     ("upstox raw", {"adjustment_basis": AdjustmentBasis.RAW}),
                     ("upstox in US", {"market": Market.US}),
                     ("massive in IN", {"provider": ProviderId.MASSIVE}),
                     ("kite left the bar rows", {"provider": ProviderId.ZERODHA_KITE}),
                     ("non-bar provider", {"provider": ProviderId.DEEPSEEK}),
                     ("session after retrieval", {"last_session": date(2026, 11, 1)}),
                     ("reversed", {"first_session": date(2026, 10, 30), "last_session": date(2026, 10, 29)}),
                     ("vendor resolution", {"resolution": "1minute"}),
                     ("naive time", {"retrieved_at": datetime(2026, 10, 30, 14, 0)}),
                     ("bad digest", {"content_sha256": "A" * 64})):
        require(rejected(lambda kw=kw: snapshot(**kw)), name)


def t_dormancy_status():
    rec = AccountActivity(provider=ProviderId.UPSTOX, last_activity_on=date(2026, 1, 1), alert_after_days=(300, 330))
    require(dormancy_status(rec, date(2026, 10, 27)) == (DormancyStatus.OK, 0))
    require(dormancy_status(rec, date(2026, 10, 28)) == (DormancyStatus.DUE, 300))
    require(dormancy_status(rec, date(2026, 11, 27)) == (DormancyStatus.DUE, 330))
    require(dormancy_status(rec, date(2027, 2, 4)) == (DormancyStatus.DUE, 330))
    future = AccountActivity(provider=ProviderId.UPSTOX, last_activity_on=date(2027, 1, 1), alert_after_days=(300,))
    for record, today in ((None, TODAY), (future, TODAY), (rec, None), (rec, "2026-10-30"), (rec, datetime(2026, 10, 30))):
        require(dormancy_status(record, today) == (DormancyStatus.UNKNOWN, 0), (record, today))


def t_dormancy_record_rejections():
    for days in ((365,), (0,), (), (330, 300), (300, 300)):
        require(rejected(lambda days=days: AccountActivity(provider=ProviderId.UPSTOX, last_activity_on=TODAY,
                                                           alert_after_days=days)), days)
    require(rejected(lambda: AccountActivity(provider=ProviderId.OPENAI, last_activity_on=TODAY, alert_after_days=(300,))))


def t_research_gate_is_closed_by_default():
    sel = selections()
    up = sel["SEL-4"]
    ok = ResearchGateApproval(approved_by="Owner", approval_ref="rec-1", approved_on=TODAY)
    require(research_gate_open(ok, up, TODAY))
    require(not research_gate_open(None, up, TODAY))
    require(not research_gate_open(ok, sel["SEL-10"], TODAY), "a BLOCKED Upstox row")
    fyers = ProviderSelection(capability=Capability.EOD_BARS, market=Market.IN, primary=ProviderId.FYERS, backup=None,
                              status=SelectionStatus.PROVISIONAL, blocked_by=("OQ-68",))
    require(not research_gate_open(ok, fyers, TODAY), "the gate covers Upstox only")
    require(not research_gate_open(ok, up, date(2026, 10, 29)), "approved in the future")
    require(not research_gate_open(ok, up, None))
    gone = ResearchGateApproval(approved_by="Owner", approval_ref="rec-1", approved_on=date(2026, 1, 1), revoked_on=TODAY)
    require(not research_gate_open(gone, up, TODAY))
    require(research_gate_open(gone, up, date(2026, 10, 29)))
    for kw in ({"approved_by": "   "}, {"approval_ref": ""}):
        require(rejected(lambda kw=kw: ResearchGateApproval(**{"approved_by": "Owner", "approval_ref": "r", "approved_on": TODAY, **kw})))


def t_identifier_series():
    for kind, top in (("OQ", 80), ("PE", 25), ("THR", 14), ("UP", 48), ("D", 46), ("A", 83), ("NB", 73), ("BQ", 53),
                      ("F", 108), ("E", 36)):
        used = {int(x) for x in re.findall(rf"\b{kind}-(\d+)\b", TEXT)}
        require(max(used) == top, (kind, max(used)))
    for kind, low in (("F", 77), ("OQ", 27), ("PE", 1), ("THR", 1), ("SEL", 1), ("E", 1)):
        rows = {int(x) for x in re.findall(rf"^\| {kind}-(\d+) \|", TEXT, re.M)}
        cited = {int(x) for x in re.findall(rf"\b{kind}-(\d+)\b", TEXT) if int(x) >= low}
        require(cited <= rows, (kind, cited - rows))


def t_fact_counts():
    rows = [l for l in TEXT.splitlines() if re.match(r"\| F-\d+ \|", l)]
    require(len(rows) == 91, len(rows))
    for level, want in (("PRIMARY_FULL", 31), ("PRIMARY_EXTRACT", 46), ("SEARCH_EXCERPT", 9), ("SECONDARY", 5)):
        got = sum(1 for l in rows if f"| {level} |" in l or f"| {level} (" in l)
        require(got == want, (level, got))


def t_header_and_placeholders():
    require(re.search(r"^version: 0\.3$", TEXT, re.M))
    require(re.search(r"^status: DRAFT$", TEXT, re.M), "the spec may not freeze with a market incomplete (ADR-11)")
    require(not re.search(r"\b(TODO|TBD|FIXME)\b", TEXT))
    require(not re.search(r"\bdormancy_alerts\b", BLOCK))


def check(name, fn):
    try:
        fn()
        PASS.append(name)
    except Exception as e:  # noqa: BLE001
        FAIL.append(f"{name}: {type(e).__name__}: {e}")


for _n, _f in sorted((n, f) for n, f in list(globals().items()) if n.startswith("t_")):
    check(_n, _f)

print(f"PASSED {len(PASS)} FAILED {len(FAIL)}")
for f in FAIL:
    print("FAILED", f)
sys.exit(1 if FAIL else 0)
