#!/usr/bin/env python3
"""Read-only vendor evidence checks for SPEC-P2.1-INGEST open questions.

This is NOT P2.1 ingest code. It sends a fixed list of GET requests so that open questions
can be answered from real responses instead of documentation, and prints only status codes,
field names and non-sensitive values. Standard library only.

Safety rules, enforced in code:
  * GET only. There is no code path that sends another method.
  * Every request host must be in ALLOWED_HOSTS. The Alpaca LIVE trading host is refused by
    name (Owner decision O-14: paper host and a paper-account key only).
  * Credentials are read from the repository's ignored .env file or the environment. They are
    sent only as request headers, never placed in a URL, and never printed.
  * A check whose credential is missing is reported as SKIPPED. Nothing is sent for it.
  * SEC requests run only with --sec AND a configured SEC_EDGAR_USER_AGENT (Owner decision
    O-16). The contact string is never taken from anywhere else.

Usage:
    python scripts/vendor_evidence_check.py            # Alpaca and Massive checks
    python scripts/vendor_evidence_check.py --sec      # also the SEC checks
    python scripts/vendor_evidence_check.py --dry-run  # show what would be sent; send nothing
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALLOWED_HOSTS = frozenset({
    "paper-api.alpaca.markets",   # Alpaca trading API, PAPER
    "data.alpaca.markets",        # Alpaca market data
    "api.polygon.io",             # Massive (formerly Polygon), SPEC-P0.2
    "data.sec.gov",               # SEC, only with --sec
})
REFUSED_HOSTS = frozenset({"api.alpaca.markets"})   # Alpaca LIVE trading host: never
TIMEOUT_SECONDS = 30
MAX_BODY_BYTES = 20_000_000


class Refused(Exception):
    """The request is not allowed by this script's rules. Nothing was sent."""


def load_env(path: str) -> dict[str, str]:
    """KEY=VALUE lines of the ignored .env file. Process environment wins."""
    values: dict[str, str] = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
    for key, value in os.environ.items():
        values[key] = value
    return values


def check_url(url: str) -> str:
    """Return the host, or raise Refused. Called before every request."""
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https":
        raise Refused(f"not https: {parts.scheme!r}")
    if host in REFUSED_HOSTS:
        raise Refused(f"{host} is the Alpaca live trading host and is never called")
    if host not in ALLOWED_HOSTS:
        raise Refused(f"{host!r} is not an allowed host")
    if parts.username or parts.password:
        raise Refused("credentials in a URL are not allowed")
    return host


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: urllib would resend the credential headers to the new host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, D102
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def get(url: str, headers: dict[str, str], dry_run: bool) -> tuple[int | None, object]:
    """One GET. Returns (status, parsed JSON or error text). Never prints a header."""
    host = check_url(url)
    if dry_run:
        return None, f"DRY RUN: would GET https://{host}{urllib.parse.urlsplit(url).path}"
    request = urllib.request.Request(url, method="GET", headers={"Accept-Encoding": "gzip", **headers})
    if request.get_method() != "GET":
        raise Refused("only GET is permitted")
    try:
        with _OPENER.open(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read(MAX_BODY_BYTES + 1)
            if len(body) > MAX_BODY_BYTES:
                return response.status, "body larger than the read limit; not parsed"
            if response.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            return response.status, json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, f"HTTP {exc.code} {exc.reason}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {str(exc)[:200]}"


def keys_of(value: object) -> list[str]:
    return sorted(value.keys()) if isinstance(value, dict) else []


def report(question: str, title: str, status: int | None, lines: list[str]) -> None:
    print(f"\n[{question}] {title}")
    print(f"  status: {status if status is not None else 'no response'}")
    for line in lines:
        print(f"  {line}")


def skipped(question: str, title: str, missing: str) -> None:
    print(f"\n[{question}] {title}\n  SKIPPED: {missing} is not configured. Nothing was sent.")


# --------------------------------------------------------------------------- Alpaca

def alpaca_checks(env: dict[str, str], dry_run: bool) -> None:
    key, secret = env.get("ALPACA_PAPER_KEY_ID"), env.get("ALPACA_PAPER_SECRET_KEY")
    if not (key and secret):
        skipped("OQ-35, OQ-36, A-16, A-17", "Alpaca paper checks",
                "ALPACA_PAPER_KEY_ID / ALPACA_PAPER_SECRET_KEY")
        return
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}

    # OQ-35: range, span and truncation of /v3/calendar/{market}. A-16: core session length.
    spans = [("one recent year", "2025-01-01", "2025-12-31"), ("an early year", "1990-01-01", "1990-12-31"),
             ("the last documented year of /v2", "2029-01-01", "2029-12-31"),
             ("a ten-year span", "2015-01-01", "2024-12-31")]
    for market in ("NYSE", "NASDAQ"):
        for label, start, end in spans:
            url = (f"https://paper-api.alpaca.markets/v3/calendar/{market}?"
                   + urllib.parse.urlencode({"start": start, "end": end, "timezone": "UTC"}))
            status, data = get(url, headers, dry_run)
            lines = [f"requested {start} to {end} ({label})"]
            days = data.get("calendar") if isinstance(data, dict) else None
            if isinstance(days, list) and days:
                lengths: dict[int, int] = {}
                for day in days:
                    try:
                        seconds = int((dt.datetime.fromisoformat(day["core_end"].replace("Z", "+00:00"))
                                       - dt.datetime.fromisoformat(day["core_start"].replace("Z", "+00:00"))
                                       ).total_seconds())
                    except (KeyError, ValueError, AttributeError):
                        seconds = -1
                    lengths[seconds] = lengths.get(seconds, 0) + 1
                lines += [f"top-level keys: {keys_of(data)}", f"day keys (union): "
                          f"{sorted({k for d in days if isinstance(d, dict) for k in d})}",
                          f"days returned: {len(days)}; first {days[0].get('date')}; last {days[-1].get('date')}",
                          f"core session length in seconds -> day count: {dict(sorted(lengths.items()))}",
                          f"sample core_start: {days[0].get('core_start')!r}"]
            else:
                lines.append(f"result: {data if not isinstance(data, dict) else keys_of(data)}")
            report("OQ-35, A-16, A-17", f"Alpaca paper GET /v3/calendar/{market}", status, lines)

    # OQ-36: plan access (200 or 403), fields, date semantics of /v1/corporate-actions.
    url = ("https://data.alpaca.markets/v1/corporate-actions?"
           + urllib.parse.urlencode({"types": "spin_off,rights_distribution", "start": "2024-01-01",
                                     "end": "2024-12-31", "limit": 50}))
    status, data = get(url, headers, dry_run)
    lines = []
    actions = data.get("corporate_actions") if isinstance(data, dict) else None
    if isinstance(actions, dict):
        lines.append(f"top-level keys: {keys_of(data)}; next_page_token present: "
                     f"{bool(data.get('next_page_token'))}")
        for kind, records in sorted(actions.items()):
            if isinstance(records, list) and records:
                first = records[0]
                lines.append(f"{kind}: {len(records)} records; keys: {keys_of(first)}")
                lines.append(f"  sample (public data): { {k: first.get(k) for k in ('ex_date', 'process_date', 'source_symbol', 'new_symbol', 'source_rate', 'new_rate', 'rate') if k in first} }")
                dates = sorted(str(r.get("process_date")) for r in records)
                lines.append(f"  process_date range in this page: {dates[0]} to {dates[-1]}")
    else:
        lines.append(f"result: {data}")
    report("OQ-36, A-17, A-18", "Alpaca data GET /v1/corporate-actions (spin_off, rights_distribution)",
           status, lines)


# --------------------------------------------------------------------------- Massive

def massive_checks(env: dict[str, str], dry_run: bool) -> None:
    key = env.get("MASSIVE_API_KEY")
    if not key:
        skipped("OQ-22, A-10", "Massive checks", "MASSIVE_API_KEY")
        return
    headers = {"Authorization": f"Bearer {key}"}

    status, data = get("https://api.polygon.io/v3/reference/tickers/types?asset_class=stocks&locale=us",
                       headers, dry_run)
    results = data.get("results") if isinstance(data, dict) else None
    lines = ([f"record keys: {keys_of(results[0])}",
              f"type codes: {sorted(str(r.get('code')) for r in results)}"]
             if isinstance(results, list) and results else [f"result: {data}"])
    report("OQ-22", "Massive GET /v3/reference/tickers/types", status, lines)

    status, data = get("https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit=1000",
                       headers, dry_run)
    results = data.get("results") if isinstance(data, dict) else None
    if isinstance(results, list) and results:
        lines = [f"record keys (union): {sorted({k for r in results for k in r})}",
                 f"primary_exchange values in this page: {sorted({str(r.get('primary_exchange')) for r in results})}",
                 f"type values in this page: {sorted({str(r.get('type')) for r in results})}",
                 f"records: {len(results)}; next_url present: {bool(data.get('next_url'))}"]
    else:
        lines = [f"result: {data}"]
    report("OQ-22", "Massive GET /v3/reference/tickers (one page)", status, lines)

    # A-10: one documented rename. Facebook became Meta Platforms, ticker FB -> META, in June 2022.
    status, data = get("https://api.polygon.io/vX/reference/tickers/META/events?types=ticker_change",
                       headers, dry_run)
    results = data.get("results") if isinstance(data, dict) else None
    lines = ([f"result keys: {keys_of(results)}", f"composite_figi: {results.get('composite_figi')}",
              f"events: {results.get('events')}"] if isinstance(results, dict) else [f"result: {data}"])
    report("A-10", "Massive GET ticker events for META", status, lines)
    for ticker, date in (("FB", "2022-06-01"), ("META", "2022-06-15")):
        status, data = get(f"https://api.polygon.io/v3/reference/tickers/{ticker}?date={date}", headers, dry_run)
        results = data.get("results") if isinstance(data, dict) else None
        lines = ([f"ticker {results.get('ticker')} on {date}: composite_figi {results.get('composite_figi')}, "
                  f"share_class_figi {results.get('share_class_figi')}"]
                 if isinstance(results, dict) else [f"result: {data}"])
        report("A-10", f"Massive GET /v3/reference/tickers/{ticker}?date={date}", status, lines)


# --------------------------------------------------------------------------- SEC

def sec_checks(env: dict[str, str], dry_run: bool) -> None:
    agent = env.get("SEC_EDGAR_USER_AGENT")
    if not agent:
        skipped("OQ-9", "SEC submissions JSON", "SEC_EDGAR_USER_AGENT")
        return
    status, data = get("https://data.sec.gov/submissions/CIK0000320193.json", {"User-Agent": agent}, dry_run)
    lines = []
    recent = data.get("filings", {}).get("recent") if isinstance(data, dict) else None
    if isinstance(recent, dict):
        lines += [f"top-level keys: {keys_of(data)}", f"filings.recent keys: {keys_of(recent)}"]
        forms = recent.get("form", [])
        for index, form in enumerate(forms[:400]):
            if form in ("3", "4", "5", "10-K", "10-Q", "8-K") and len(lines) < 12:
                lines.append(f"{form}: filingDate {recent['filingDate'][index]}, acceptanceDateTime "
                             f"{recent['acceptanceDateTime'][index]!r}")
    else:
        lines.append(f"result: {data if not isinstance(data, dict) else keys_of(data)}")
    report("OQ-9", "SEC GET data.sec.gov/submissions/CIK0000320193.json", status, lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--sec", action="store_true", help="also run the SEC checks (needs SEC_EDGAR_USER_AGENT)")
    parser.add_argument("--dry-run", action="store_true", help="send nothing; show what would be requested")
    args = parser.parse_args(argv)
    env = load_env(os.path.join(REPO_ROOT, ".env"))
    print(f"vendor evidence check, {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}"
          f"{' (dry run)' if args.dry_run else ''}")
    alpaca_checks(env, args.dry_run)
    massive_checks(env, args.dry_run)
    if args.sec:
        sec_checks(env, args.dry_run)
    else:
        print("\n[OQ-9] SEC checks not requested (run with --sec once SEC_EDGAR_USER_AGENT is configured).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
