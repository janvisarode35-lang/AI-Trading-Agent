---
id: SPEC-P0.2-PROVIDERS
version: 0.5
status: FROZEN
phase: P0.2 — Provider & Broker Due Diligence
depends_on: [SPEC-P0.1-DECISIONS, docs/PROMPT-PACK.md BLOCK-A, docs/PROMPT-PACK.md BLOCK-B, docs/PROMPT-PACK.md BLOCK-C]
produces: [PROVIDER-SELECTION-P0.2, provider fact sheets, config.provider.*, enum.ProviderId, enum.DataCapability, enum.ProviderRole, UNVERIFIED-URL-REGISTER, RULE-N1..N14]
supersedes: SPEC-P0.2-PROVIDERS v0.4 (2026-08-26), v0.3, v0.2, v0.1
frozen_by: STAGE-0-FREEZE.md (2026-08-25)
---

# SPEC-P0.2 — Provider & Broker Due Diligence

**Phase:** Stage 0 — DECIDE, prompt `P0.2`
**Date:** 2026-08-24
**Owner:** JS — Project Owner, acting as Integration Engineer
**Depends on:** [SPEC-P0.1-DECISIONS](SPEC-P0.1-DECISIONS.md) — ADR-13 (swing; daily bars, 5-minute
only for held names) fixes which data granularity is being shopped for; ADR-14 (1,500 US names,
one decision per session, 09:45–10:15 ET order window) fixes throughput; ADR-11 (US-first by
capital, India by contract) fixes which broker must work now versus later; ADR-12 (long-only cash
account) removes margin, borrow and short-locate from scope.

**What changed in v0.5 (2026-08-26).** Controlled amendment under STAGE-0-FREEZE §7 trigger **T3** (a verified external fact changes). Four retrievals: **M-2 CLOSED** — Massive retains delisted price history “stored as it occurred on that date”. **M-3 downgraded from gating** — two Alpaca streaming pages retrieved in full and confirmed silent on replay, so N5 is the documented reality. **M-5 ANSWERED, and the answer is no** — both news vendors expose a revision timestamp and neither offers a way to recover prior text, so the archive is **not** point-in-time; new **rule N16** makes our own store the point-in-time record, residual materiality split to **M-12**. **M-11 split**: auth CLOSED with exact vendor wording, ToS still open as M-11b. **No ADR and no AD-level decision changed.** The unverified register goes from 10 items to 9, and **Stage 1 has no remaining documentary gate**.

**What changed in v0.4 (2026-08-26).** Correction only, under STAGE-0-FREEZE §8 (“additive, changes no decision”). v0.3 applied AD-5 to §4.3, §6 and §10.4 but **left three sites still asserting the old LLM ordering**: the §3.11 and §3.12 headings and DECISIONS row 7. All three now match AD-5. Separately, §5.2 gains **M-11**: §3.12 has no Auth row and no legal row, which was tolerable while OpenAI was the fallback and is a real gap now that it is the primary. **No fact, price, limit or decision changed.**

**What changed in v0.3.** Amendment dispositions only. The Owner took the five authority
decisions in SPEC-P0.1 §0.5.1: **AD-5 makes OpenAI `gpt-5.6-luna` the primary LLM and
DeepSeek `deepseek-v4-flash` the fallback**, conditional on M-7; AD-4 fixes the broker
hierarchy; AD-3 makes IBKR manual-only. **No fact sheet, price or verified limit in this
document changed** — the evidence stands exactly as retrieved; only the selections built on
it moved. Marked inline as AMENDED BY STAGE-0-FREEZE.

**What changed from v0.1.** v0.1 established the structure and the verification discipline but
left **21 facts and 5 fact sheets substantially unretrieved**, including several the issue names
explicitly: adjusted-vs-unadjusted, partial fills, rejection codes, tick size, sandbox differences,
commissions, and IBKR in its entirety. v0.2 is a **second retrieval pass** that closes 17 of them
against vendor and regulator primary sources, adds the Block C clarifier sections v0.1 omitted, and
**reverses one v0.1 decision** (bundled news — see F-6). The unverified register in §5 shrinks from
21 items to 9, and every survivor is a fact the vendor genuinely does not publish.

---

## 0. Verification protocol, and what "verified" means in this document

Block A forbids inventing a rate limit, a fee, a field, or a regulation. The issue sharpens it:
**"No guessed rate limits — a guessed limit is worse than a missing one."** Every fact below
carries one of four tags:

| Tag | Meaning |
|---|---|
| **`[V]`** | **Verified** — retrieved from the provider's or regulator's own documentation on 2026-08-23/24, URL recorded, figure quoted |
| **`[U]`** | **Unverified** — the page could not be retrieved, or the figure is genuinely not published. **No number is supplied.** Listed in §5 |
| **`[D]`** | **Derived** — arithmetic performed here on `[V]` inputs; the inputs are cited so it can be rechecked |
| **`[F]`** | **Forum / support-article** — stated by vendor staff outside the API reference. Usable as a warning, never as a binding limit in code |

Retrieval used a plain HTTP fetcher first, a JS-rendering scraper second, and a PDF parser for fee
schedules and SEC releases. Two vendors publish machine-readable documentation indexes that made
the second pass possible where v0.1's first pass failed — `docs.alpaca.markets/us/llms.txt` and
`interactivebrokers.com/docs/web-api/llms.txt` — and both expose a `.md` suffix on every page.
That is recorded because it is *why* v0.2 could close gaps v0.1 could not, and because P3.x should
reuse it. **There is not a single guessed rate limit, price, fee or error code in this document.**

---

## 0.5 BLOCKING QUESTIONS — and the defaults applied

Per Block C: questions where two reasonable answers produce materially different designs. This
phase **proceeded on the recommended default** rather than stalling. Each is tagged `[DEFAULT-Pn]`
where used and repeated in §8 ASSUMPTIONS.

| # | Question | Options | **Default applied** | What breaks if the default is wrong |
|---|---|---|---|---|
| 1 | Is the operator a **Non-Professional Subscriber** under exchange rules? | (a) non-pro; (b) professional | **(a) non-pro** `[DEFAULT-P1]` — owner trades own capital in own name, not registered with SEC/CFTC, not an adviser (P0.1 `[DEFAULT-3]`) | Every retail data price in §4 is void. Massive, FMP and Finnhub retail tiers are individual-use only (F-9). Professional status moves the data line from ~$130/mo to business pricing none of them publishes |
| 2 | Where does the **10-year backtest history** come from? | (a) one vendor's REST history; (b) vendor flat files; (c) two vendors reconciled | **(a) Massive Stocks Developer REST** `[DEFAULT-P2]`, with flat files as the bulk-load path if REST paging is too slow | If Developer's 10 years excludes delisted names, §5 M-2 becomes a Stage-1 blocker instead of a Stage-5 one |
| 3 | **Adjusted or raw** bars on the wire? | (a) request adjusted; (b) request raw, adjust on read | **(b) raw** `[DEFAULT-P3]` — P0.1 `[DEFAULT-9]` already requires raw plus a corporate-action table. Alpaca already defaults to `raw`; **Massive defaults to `adjusted=true` and must be explicitly overridden** | Storing vendor-adjusted bars rewrites history on every split and destroys backtest reproducibility |
| 4 | Which venue's prices drive the **screen**? | (a) consolidated SIP; (b) whatever the broker gives away | **(a) consolidated** `[DEFAULT-P4]` | IEX-only ADDV and closes are wrong, not noisy (F-2). A universe built on them is silently wrong in a way that looks like it works |
| 5 | Is **paper trading** evidence of anything? | (a) paper P&L estimates fill quality; (b) paper is a plumbing test only | **(b) plumbing only** `[DEFAULT-P5]` | Alpaca paper fills against free IEX quotes, injects random partial fills 10% of the time, charges no regulatory fees and pays no dividends (F-13). Any P&L conclusion from it is unfounded |
| 6 | Does the system need a **standalone news vendor**? | (a) NewsAPI Business $449/mo; (b) Benzinga bundled with Alpaca data; (c) no news in v1 | **(b) bundled with Alpaca** `[DEFAULT-P6]` — Alpaca's news API *is* Benzinga, back to 2015, included with the data subscription | If Alpaca's news licence forbids our use, the fallback is **(c)**, not (a): ADR-04 gives news a supporting role and $449/mo is ~3.5× the rest of the stack |
| 7 | **US tick size** — one value or a time-varying attribute? | (a) constant $0.01; (b) per-symbol, date-versioned | **(b) date-versioned** `[DEFAULT-P7]`; currently **$0.01** for all NMS stocks ≥ $1.00 | The $0.005 increment is deferred, not cancelled (F-10). A constant baked into the order layer becomes a rounding bug on the first business day it changes |
| 8 | **India broker** — Zerodha or Upstox? | (a) Zerodha per `[CONST-10]`; (b) Upstox on operational merit | **(a) Zerodha** `[DEFAULT-P8]` — P0.2 has no authority to overturn a Constitution invariant; the evidence is escalated as amendment A-4 | If Upstox is later chosen, the adapter interface must already be broker-neutral. §10 exports it that way regardless, so the cost of being wrong is one adapter, not one architecture |
| 9 | When is the **$99/mo real-time feed** bought? | (a) now; (b) at first real capital | **(b) at `[RS §12]` stage 5** `[DEFAULT-P9]` | Buying at stage 1 wastes ~$1,200 across validation against $1,000 of starting capital. Deferring is safe *only* because ADR-14 decides on the prior session's completed daily bar |
| 10 | What is the **LLM's contractual data posture**? | (a) DeepSeek primary as `[CONST]` says; (b) OpenAI primary because its data terms are published | **(a) DeepSeek** `[DEFAULT-P10]`, valid only because P0.1 `[DEFAULT-7]` holds absolutely: no NAV, cash, positions, P&L, limits or PII ever reach any LLM. OpenAI's retention terms are published; DeepSeek's could not be retrieved (§5 M-7) | If DeepSeek's terms claim training rights over inputs, the sanitiser boundary is the only thing between us and leaked strategy logic. That boundary is already mandatory — which is why this is a default, not a blocker |

---

## 0.6 NON-BLOCKING details noticed and resolved

The small things that become bugs if left implicit. These **extend** P0.1 §6; where they touch the
same subject they are strictly more specific.

| Area | Resolution | State |
|---|---|---|
| **Bar timestamp semantics** | Alpaca returns `t` as RFC-3339. Massive returns `t` as **Unix milliseconds for the window start**, presented in ET. Both normalise to tz-aware UTC window-start at ingest: a bar stamped `13:30Z` is the 09:30–09:31 ET minute, never 09:29–09:30 | `[V]` |
| **Bar paging limits** | Alpaca `limit` default 1,000, **max 10,000, counted across all symbols in the request** — "The limit applies to the total number of data points, not per symbol!" Massive `limit` default 5,000, max 50,000. The pager counts points, not symbols | `[V]` |
| **Adjustment default asymmetry** | Alpaca `adjustment` defaults to **`raw`**. Massive `adjusted` defaults to **`true`**. Two vendors, opposite defaults, same concept. Every Massive aggregate call in this system passes `adjusted=false` explicitly | `[V]` |
| **Alpaca `asof`** | `asof` (YYYY-MM-DD, default: current day) controls **symbol mapping across name changes**. Backfilling a renamed or delisted name without setting `asof` to the decision date silently maps to today's owner of that ticker | `[V]` |
| **Split ratio direction** | Massive gives `split_from` (denominator, old shares) and `split_to` (numerator, new shares); a 4-for-1 is `split_from=1, split_to=4`. Reversing them inverts every adjusted price | `[V]` |
| **Which dividend date** | Massive exposes `declaration_date`, `ex_dividend_date`, `record_date`, `pay_date`. Total-return adjustment uses **`ex_dividend_date`**; cash arriving in the ledger uses **`pay_date`**. They are different dates and must never be conflated | `[V]` |
| **Dividend `frequency` and type** | `frequency` is an integer 0–365 payouts/year; `distribution_type` ∈ `recurring`/`special`/`supplemental`/`irregular`/`unknown`. **Special dividends must not be annualised into a yield feature** | `[V]` |
| **Fee rounding direction** | Alpaca aggregates each fee type per account per day and then **rounds up to the nearest cent**. The cost model rounds up at the daily aggregate, not per fill, or it under-estimates on high-fill days | `[V]` |
| **TAF cap arithmetic** | FINRA TAF is $0.000195/share on sells, capped at **$9.79 per trade** — the cap binds at **50,205 shares**. Irrelevant at our size; recorded so the cost model is not wrong at a larger one | `[V]` |
| **SEC fee is value-based; TAF is share-based** | SEC fee = $0.0000206 × trade **value**; TAF = per **share**. A cost model expressing both in bps is wrong on low-priced names | `[V]` |
| **Zerodha `tag` charset** | `tag` is **alphanumeric, max 20 characters** — it cannot hold a hyphenated UUID. The `[CONST-9]` unique-strategy-ID-per-order requirement must fit that alphabet and that length in India | `[V]` |
| **Alpaca `client_order_id` length** | **Max 128 characters**; charset undocumented (§5 M-1). We self-constrain to `[A-Za-z0-9-]`, ≤ 64 chars — a strict subset of anything the vendor could plausibly accept, and long enough for `{market}-{strategy}-{date}-{seq}` | `[V]` length, `[U]` charset |
| **Zerodha batch-quote caps** | `/quote` **500** instruments per call, `/quote/ohlc` **1,000**, `/quote/ltp` **1,000**. Combined with the 1 req/s quote limit, a 500-name India universe is **one request per second**, not 500 | `[V]` |
| **Where India static data lives** | Zerodha `tick_size` and `lot_size` are fields of the **instruments CSV dump**, not of the quote response. The dump is India's reference-data source of record | `[V]` |
| **Upstox instrument identity** | `instrument_token` is `<segment>` + `|` + `<ISIN>` (e.g. `NSE_EQ|INE669E01016`) — **ISIN-keyed, not ticker-keyed**, which satisfies ADR-11's stable-identity rule for free | `[V]` |
| **DeepSeek off-peak boundary** | Peak = **01:00–04:00 and 06:00–10:00 UTC, Monday–Friday**; all other hours are off-peak at half price. ADR-14's 22:30 UTC pipeline is off-peak by construction, Fridays included | `[V]` |
| **DeepSeek idle-connection behaviour** | Under load, non-streaming requests receive **continuous empty lines**; streaming receives `: keep-alive` SSE comments; the server **closes the connection if inference has not begun within 10 minutes**. A client that treats an empty line as EOF will truncate silently | `[V]` |
| **OpenAI retry discipline** | `Retry-After` is returned on 429 and the official SDKs honour it. Our client honours it as a **minimum** wait, with exponential backoff plus jitter on top | `[V]` |
| **EDGAR index mutability** | Full and quarterly indexes are rebuilt **weekly, early Saturday**. Retrieved indexes are snapshotted immutably and never re-derived | `[V]` |
| **FRED attribution is mandatory** | The ToS **requires** the notice: "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis." It goes on the Grafana macro panel, not in a code comment | `[V]` |
| **FRED third-party copyright** | Series whose notes contain "Copyright" are third-party owned and need the owner's permission for anything beyond personal use. The macro allowlist is screened for this at P2.1 rather than assumed clean | `[V]` |
| **Massive ticker point-in-time** | `/v3/reference/tickers` accepts `active` and `date`, and returns `delisted_utc`. Universe membership is therefore reconstructible as-of a date from the vendor, not only from our own snapshots | `[V]` |

---

## 1. Headline findings — read these before the fact sheets

Thirteen findings materially change the P0.1 plan or contradict an assumption in it. Each is
expanded in the relevant fact sheet and reconciled in §6.

**F-1 — Polygon.io no longer exists under that name. It is Massive.** `[V]`
`polygon.io/*` issues `301` redirects to `massive.com/*`, including the docs tree. Existing
endpoints, SDKs and accounts continue to work and `api.polygon.io` remains a live API host.
*Impact:* cosmetic for code, but every P0.1/P0.3 reference to "Polygon" is renamed, and config
records **both** the brand host and the API host.

**F-2 — Alpaca's free market-data tier is IEX-only, and that disqualifies it for screening.** `[V]`
The free plan's `Exchanges` row reads **"IEX"**; the $99/mo plan reads **"All US Exchanges"**.
ADR-14 screens on 20-session median ADDV and on the official close. Computed from one venue, both
are wrong — not noisy, *wrong*. *Impact:* the free tier cannot drive the scanner at any point in
the programme, including paper trading.

**F-3 — Alpaca offers "7+ years" of history on *both* tiers. ADR-08 needs ≥ 8 years across ≥ 2 bear
regimes and §0.3 C-3 needs a 10-year backtest.** `[V]` *Impact:* **Alpaca cannot supply backtest
history at any price.** The history line must be bought elsewhere.

**F-4 — Zerodha's daily login is regulatory, and since 1 April 2026 a static IP is mandatory for
API order placement.** `[V]` `access_token` "will expire at `6 AM` on the next day (regulatory
requirement)"; `refresh_token` is "only available to certain approved platforms". Separately,
Zerodha's support documentation states a static IP is required for **API-based order placement**
"effective 1 April 2026", with up to two IPs registered, while "the WebSocket market data stream
and other APIs, such as orderbook and positions, can continue to be accessed from any IP address."
*Impact:* India go-live needs a human action every trading morning **and** a fixed egress IP. Both
are now facts, not risks. This also satisfies half of `[CONST-9]`'s static-IP requirement by
supplying the mechanism.

**F-5 — Upstox splits its token model, and only the order path needs daily re-auth.** `[V]`
The `access_token` "has a specific validity period that lasts until `3:30 AM` the following day,
regardless of the time it was generated"; the same response carries an `extended_token`
"designed for prolonged usage, primarily for read-only access to various API endpoints".
*Impact:* at Upstox the daily-login burden falls on order placement only, and the monitoring loop
can run unattended. At Zerodha it falls on everything. This is the strongest operational argument
in the India comparison and is escalated, not actioned (A-4).

**F-6 — v0.1's "take bundled news" decision was half wrong, and the correction is free.** `[V]`
Massive's news is **Benzinga partner data at $99/month per dataset** — an additional line item, not
a bundled freebie, so v0.1's reasoning does not hold for Massive. But Alpaca's news API is *also*
Benzinga, "provided directly by Benzinga", with history "dating back to 2015" and ~130+ articles a
day, served from the same `data.alpaca.markets` host as the bars. *Impact:* the conclusion
survives — do not buy a standalone news vendor — but the **source changes from "Massive or Alpaca"
to "Alpaca specifically"**, and the news dependency is therefore coupled to the Alpaca data
subscription rather than to Massive's.

**F-7 — Finnhub has no middle tier: $0 or $3,500/month.** `[V]` Free is 60 calls/min, US-only, one
year of company news, 50 WebSocket symbols. The next tier is All-In-One at **$3,500/month billed
annually**. *Impact:* Finnhub is a free supplementary source only. Its All-In-One tier is also the
only offering in scope that explicitly advertises **survivorship-bias-free** data, which is worth
recording as the market price of buying that property outright.

**F-8 — `gpt-4o-mini`, the fallback the Constitution names, is not in OpenAI's current catalogue.** `[V]`
It survives only in the transcription line-up. The nearest current equivalent by role and price is
`gpt-5.6-luna` at $0.20 / $1.20 per 1M tokens. *Impact:* minimal constitutional amendment A-1.

**F-9 — Every retail data plan in this stack is licensed for *individual* use, and Massive gates it
on non-professional status.** `[V]` Massive's four stock plans each carry an "Individual use" badge
and a "Non-pros only" link; the professional-status test asks 11 questions and "Your account must
be in your own name to qualify as a Non-Professional Subscriber." FMP's comparison table shows
`Usage: Individual` on all four retail plans and its footer states that **"Displaying or
redistributing data sourced from FMP requires a specific Data Display and Licensing Agreement"**.
Finnhub labels both tiers "Personal Use. Terms apply." *Impact:* the §4 stack is licensable
**only** while `[DEFAULT-P1]` holds — one owner, own capital, own name, no redistribution, no
display to third parties. The moment the system manages anyone else's money, the data line is
repriced by three vendors simultaneously. That is a business constraint that belongs in P0.3's
cost model and in `[RS §16]`'s registration analysis, not a footnote.

**F-10 — The US half-penny tick is real, is *not* in force, and is currently deferred to
November 2027.** `[V]` The SEC amended Rule 612 on 18 September 2024 to add a **$0.005** minimum
pricing increment for NMS stocks priced ≥ $1.00 whose Time Weighted Average Quoted Spread over the
evaluation period is **$0.015 or less**; tick assignments are recomputed **twice a year**
(Jan–Mar evaluation → operative first business day of May–end of October; Jul–Sep evaluation →
operative first business day of November–end of April). The original compliance date was the first
business day of November 2025. Release 34-104172 (31 Oct 2025) deferred it to November 2026;
**release 34-105656 (11 June 2026) further deferred Rules 600(b)(89)(i)(F), 610(c) and 612 to the
first business day of November 2027**, and the Chairman has directed staff to review whether the
increments should change at all. *Impact:* this resolves P0.1's `[VERIFY-P0.2]` marker on tick
size with a precise answer — **$0.01 today, per-symbol and semi-annually reassigned from November
2027 unless changed again**. Tick size is therefore a *date-versioned instrument attribute*
(`[DEFAULT-P7]`), never a constant. The same order also notes 23/5 trading and Rule 605 compliance
landing in 2026, which is consistent with Alpaca already shipping `overnight` and `boats` feeds.

**F-11 — FMP meters bandwidth as well as requests, and nobody notices until ingest is written.** `[V]`
"API usage has a trailing 30 days bandwidth limit of: Free plan - 500MB, Starter plan - 20GB,
Premium plan - 50GB, Ultimate plan - 150GB". *Impact:* a second, independent quota axis. A
fundamentals backfill across 1,500 names is a *bandwidth* event, not a call-count event, and the
client needs a byte budget as well as a rate limiter.

**F-12 — IBKR is now fully verified, and it is operationally disqualifying for an unattended VM.** `[V]`
Sessions "will timeout after approximately 6 minutes without sending new requests" and are capped
at 24 hours "resetting at midnight for New York, U.S.; Zug, Switzerland; or Hong Kong time";
`/tickle` must be called "approximately every minute"; the Client Portal Gateway requires that
"Users must log in through the browser on the same machine as Client Portal Gateway in order to
authenticate" and that "All API Endpoint calls must be made on the same machine"; and orders can
return **reply messages that must be explicitly confirmed** by POSTing `{"confirmed":true}` to
`/iserver/reply/{messageId}` before they transmit. Pacing is a **global 10 requests/second** with
per-endpoint carve-outs, and violators are placed in a **15-minute IP penalty box**, with repeat
violators "permanently blocked". *Impact:* IBKR remains a credible **backup** under ADR-10's
narrow definition (new entries only, never position takeover), but it cannot be the primary broker
for an unattended systemd-driven design without a daily human browser login — the same burden F-4
imposes on Zerodha. v0.1 scored it `UNVERIFIED`; v0.2 scores it on evidence.

**F-13 — Alpaca paper trading is a plumbing test, not a fill-quality experiment.** `[V]`
Paper fills against "Free IEX Real Time Data"; orders "are filled only when they become
marketable"; the simulator injects "partial fills for a random size 10% of the time"; it "does NOT
simulate dividends"; and it explicitly does not model market impact, information leakage, latency
slippage, queue position, price improvement, regulatory fees or borrow fees, nor does it validate
order quantity against NBBO size. *Impact:* `[RS §12]`'s paper stage proves the *plumbing* — order
lifecycle, reconciliation, audit writes, kill-switch behaviour — and proves **nothing** about
slippage or edge. ADR-13 Chain F's ≥ 2× cost threshold must be validated against **live** fills at
`[RS §12]` stage 5+, never against paper.

---

## 2. What P0.1 assumed, and what the documentation actually says

Direct disposition of every P0.1 assumption, open question and `[VERIFY-P0.2]` marker assigned to
this phase.

| P0.1 ref | Assumption / question | Verdict | Verified value |
|---|---|---|---|
| A3 / Q1 | Alpaca supports fractional shares; $0 commission | **Confirmed, with a caveat** `[V]` | `qty` "Can be fractionable for only market and day order types"; `notional` supported, market + day TIF only, "Cannot work with `qty`". Fee schedule (rev. 20 July 2026) states "In general, we do not charge a commission for trades" and lists **Commissions: 0%-3% per transaction** — i.e. zero is the norm, not a contractual guarantee, and Elite Smart Router or partner arrangements "may preclude commission-free trades" |
| Q1 | Alpaca idempotency key charset / length | **Length confirmed; charset still undocumented** `[V]`+`[U]` | `client_order_id`, **max 128 characters**, auto-generated if omitted. Charset not published — §5 M-1. We self-restrict to `[A-Za-z0-9-]` ≤ 64 |
| A4 / Q2 | Zerodha daily login; static IP | **Both confirmed** `[V]` | `access_token` expires **06:00 next day** ("regulatory requirement"); `refresh_token` restricted to approved platforms; 2FA TOTP required. Static IP mandatory for **API order placement** effective **1 April 2026**; up to two IPs; data and read APIs unrestricted |
| Q3 | Market-data tiers and prices | **Confirmed; P0.1's band is low** `[V]` | Massive $0 / $29 / $79 / $199 (monthly billed, −20% annual); Alpaca $0 / $99; FMP $0 / $19 / $49 / $99 (annual-billed rates); Finnhub $0 / $3,500 |
| Q4 | News API price; **is the archive point-in-time?** | **Price confirmed; point-in-time NOT confirmed** `[V]`+`[U]` | NewsAPI $449/mo Business, 5-year archive. **No vendor in scope documents archive integrity.** Escalated as §5 M-5 — the one gap that materially threatens P5.1 |
| Q5 | EDGAR rate limit and latency | **Limit confirmed; latency not published** `[V]`+`[U]` | **10 requests/second**, declared User-Agent required. Dissemination cutoffs documented (17:30 ET; 22:00 ET for Forms 3/4/5); propagation latency after acceptance is not |
| Q6 | DeepSeek / OpenAI prices and limits | **Confirmed** `[V]` | Full tables in §3.11–3.12. DeepSeek publishes **concurrency** limits (2,500 / 500) and 429 behaviour; OpenAI publishes tiered RPM/TPM/RPD/TPD, 429, and `x-ratelimit-*` + `Retry-After` headers. ADR-13 Chain G's conclusion survives at **$0.73/month** |
| Q11 | Reference-data field identifying security type | **Resolved** `[V]` | Massive `/v3/reference/tickers` returns `type` (with a Ticker Types endpoint enumerating values), `active`, `primary_exchange`, `cik`, `composite_figi`, `share_class_figi`, `delisted_utc`, and accepts a `date` parameter for point-in-time membership |
| Q12 | RBI USD/INR reference-rate endpoint | **Not attempted** `[U]` | India is unfunded under ADR-11; deferred to the India activation gate. Not a P0.3 blocker |
| A1 / Q7 | US T+1 settlement; cash-account good-faith rules | **Still not verified** `[U]` | Requires the account agreement behind login. §5 M-6. ADR-13 Chain D specifies both counters, so either answer is implementable |
| A14 | Retail data tier $30–200/mo | **Low** `[D]` | Recommended stack: **≈$129/mo paper → ≈$228/mo live**. §4.3. **Superseded by AD-1**, which adds the unpriced VM and backup lines and marks the total operating cost INCOMPLETE |
| §6 `[VERIFY-P0.2]` | **US tick size / sub-penny rules** | **Resolved** `[V]` | **$0.01** for all NMS stocks ≥ $1.00 today. The $0.005 second increment is adopted but exempted until **the first business day of November 2027**, then reassigned per symbol twice yearly. F-10 |
| §6 `[VERIFY-P0.2]` | **Lot size / fractional support** | **Resolved (US); India sourced** `[V]` | US: no lot size; fractional via `qty` (market/day only) or `notional` (market/day only). India: `lot_size` and `tick_size` are fields of Zerodha's instruments CSV dump |
| §5 Q10 | Regulatory record-retention minima | **Not attempted** `[U]` | Out of scope for a provider phase; belongs to P6.3. P0.1's 7-year default stands unchallenged |
| §6 `[VERIFY-P0.2]` | FIFO cost basis as jurisdictional default | **Not attempted** `[U]` | Tax-accounting question, not a provider question. Remains P0.1's assumption |

---

## 3. Provider fact sheets

Every sheet covers the same twelve dimensions the issue names — auth and token lifetime, rate
limits with 429 behaviour, WebSocket reconnect/backfill, adjusted vs unadjusted, corporate actions,
survivorship bias, tick and lot size, idempotency key and charset, partial fills, rejection codes,
sandbox vs prod, cost, ToS on automated access — and ends with a **"dies at 09:31"** note. 09:31 ET
is one minute after the US open: the worst realistic moment, and 14 minutes before ADR-14's
09:45–10:15 ET order window.

Where a dimension does not apply to a provider (a macro API has no partial fills) the row says so
rather than being omitted, so that a missing row always means "not checked", never "not relevant".

---

### 3.1 Alpaca — Trading API

**Role:** primary US broker (`[CONST-10]`, `[RS §10]`).
**Docs retrieved `[V]`:** `docs.alpaca.markets/us/reference/postorder.md`,
`docs.alpaca.markets/docs/orders-at-alpaca`, `docs.alpaca.markets/us/docs/websocket-streaming.md`,
`docs.alpaca.markets/us/docs/paper-trading.md`,
`docs.alpaca.markets/us/docs/mandatory-corporate-actions.md`,
`alpaca.markets/support/usage-limit-api-calls`,
`files.alpaca.markets/disclosures/library/BrokFeeSched.pdf` (rev. 20 July 2026).

| Dimension | Finding | State |
|---|---|---|
| **Auth / token lifetime** | API key ID + secret key headers. **No token expiry, no daily re-auth, no OAuth dance for a first-party account** — the operational opposite of Zerodha and IBKR | `[V]` |
| **Rate limit** | "200 requests per minute, per account". Scope is **per account, not per key** — adding keys adds nothing | `[V]` |
| **429 behaviour** | "A **429 - Too Many Requests** status will be returned". Increases are not self-serve: "we do not support users increasing the limit by users themselves… please contact [support] for more information". **Retry-header names and reset semantics are not published** — the client must use its own token bucket at 200/min and exponential backoff on 429 | `[V]` / `[U]` §5 M-1 |
| **Order types** | `market`, `limit`, `stop`, `stop_limit`, `trailing_stop` | `[V]` |
| **Time in force** | `day`, `gtc`, `opg`, `cls`, `ioc`, `fok` | `[V]` |
| **Order classes** | `simple`, `bracket`, `oco`, `oto`, `mleg` (multi-leg, ≤ 4 legs). ADR-05 and ADR-12 restrict us to `simple` and `bracket` on equities | `[V]` |
| **Idempotency key** | `client_order_id`, string, **max 128 characters**, "uniquely identifies the order", auto-generated if omitted | `[V]` |
| **Idempotency charset** | **Not documented.** We self-restrict to `[A-Za-z0-9-]` ≤ 64 characters | `[U]` §5 M-1 |
| **Fractional / notional** | `qty` accepts up to 9 decimals and "can be fractionable for only market and day order types"; `notional` accepts up to 9 decimals, "Can only work for market order types and day for time in force", and "Cannot work with `qty`" | `[V]` |
| **Partial fills** | First-class. Order status `partially_filled` = "The order has been partially filled"; the order object carries `filled_qty` and `filled_avg_price`; the `trade_updates` stream emits a `partial_fill` event per execution carrying `price`, `qty`, `position_qty` (position size *after* the event) and `timestamp` | `[V]` |
| **Full status list** | Common: `new`, `partially_filled`, `filled`, `done_for_day`, `canceled`, `expired`, `replaced`, `pending_cancel`, `pending_replace`. Uncommon: `accepted`, `pending_new`, `accepted_for_bidding`, `stopped`, `rejected`, `suspended`, `calculated` | `[V]` |
| **Trade-update event list** | 16 events: `new`, `fill`, `partial_fill`, `canceled`, `expired`, `done_for_day`, `replaced`, `accepted`, `rejected`, `pending_new`, `stopped`, `pending_cancel`, `pending_replace`, `calculated`, `suspended`, `order_replace_rejected`, `order_cancel_rejected` | `[V]` |
| **Rejection codes** | Alpaca publishes **HTTP-level** rejection semantics on order creation — **403** "Buying power or shares is not sufficient", **422** "Input parameters are not recognized" — plus the terminal `rejected` order status and the `order_replace_rejected` / `order_cancel_rejected` stream events. **A granular numeric reject-reason enumeration is not published**; the reject reason arrives as free text on the order object | `[V]` / `[U]` §5 M-1 |
| **Amend vs cancel-replace** | `PATCH` replace is supported and may update `limit_price` / `stop_price`; **"notional orders cannot be replaced"**. Cancellation is permitted "up until the point it reaches a state of either `filled`, `canceled`, or `expired`". A replace produces `replaced` on the old order with `replaced_by` / `replaces` linkage — the audit trail must follow that chain, not treat the new order as unrelated | `[V]` |
| **Corporate actions** | Processes dividends (cash and stock), forward and reverse splits, spinoffs, mergers (stock, cash, stock-and-cash), name/symbol/CUSIP changes, full calls, liquidations, recapitalisations. **Order impact:** "For reverse splits all GTC orders will be canceled that were in the market with a trade date prior to the effective date"; "For forward splits, GTC buy limits and sell stops are adjusted"; and "Alpaca cancels open GTC orders on symbols that have an upcoming mandatory corporate action", surfaced as a trade event with `reason = "CORPORATE_ACTION"`. On a CUSIP change "the old asset becomes inactive and a new asset object is created" | `[V]` |
| **Tick / lot size** | No lot size on US equities. Tick size is the regulatory value, not a broker field: **$0.01** for NMS stocks ≥ $1.00 (F-10) | `[V]` (SEC) |
| **Sandbox vs prod** | `https://paper-api.alpaca.markets` (stream: `wss://paper-api.alpaca.markets/stream`) vs `https://api.alpaca.markets`. Differences are substantive — see F-13 and §3.2 | `[V]` |
| **Cost** | Commission-free in the normal case: "In general, we do not charge a commission for trades", schedule row **Commissions 0%–3% per transaction**. Pass-through: **SEC transaction fee $0.0000206 × trade value (sells only)**; **FINRA TAF $0.000195/share (sells only), max $9.79/trade**; **FINRA CAT $0.000003 per executed equivalent share (buys and sells)**. ADRs "typically $0.01 to $0.05 per share". Voluntary corporate-action election **$100 each**. Outbound ACATS **$25**. Margin 6.25% (not used — ADR-12) | `[V]` |
| **ToS on automated access** | Automated trading is the product; a "Risks of Automated Trading" disclosure is part of the account pack. The one clause with teeth: **"Alpaca reserves the right to charge additional fees if it is determined that the orders' flow is non-retail in nature."** At ADR-14's ~2.7 orders/session that is not a live risk, but it is the clause that would bite a higher-frequency redesign | `[V]` |

**Design consequence.** 200 req/min against ADR-14's ~2.7 orders/session and ≤ 25 monitored
positions is enormous headroom; Alpaca's *trading* limit is a non-issue. Three things do bind:
(1) `partial_fill` is normal and the position ledger must be event-sourced from `trade_updates`,
not polled; (2) the replace chain (`replaces` / `replaced_by`) is part of the audit story under
`[CONST-5]`; (3) **GTC orders are cancelled by Alpaca ahead of mandatory corporate actions** — a
protective stop can therefore disappear without our system doing anything, which is a fail-closed
event that must raise CRITICAL and re-place the stop, not be discovered at the next reconciliation.

**Dies at 09:31.** Highest-impact single failure in the stack. In order: (1) held positions lose
their protective-stop venue — ADR-10's panic script is the mitigation and must not depend on our
app; (2) the 09:45–10:15 window is missed, which under ADR-14 is **safe** — the order list is
frozen and simply does not fill, costing one day of entries, not money; (3) reconciliation
(ADR-10 condition 2) cannot complete, so on recovery all positions mark `UNRECONCILED` and new
entries are denied pool-wide. **The backup broker cannot take over open positions** (ADR-10); it
can only accept new entries, which we do not need during an outage. Correct response: wait, and
use the panic script only if a stop level is breached while Alpaca is down.

---

### 3.2 Alpaca — Market Data API (bars, streaming, news)

**Docs retrieved `[V]`:** `alpaca.markets/data`, `docs.alpaca.markets/us/reference/stockbars.md`,
`docs.alpaca.markets/us/docs/real-time-stock-pricing-data.md`,
`docs.alpaca.markets/docs/streaming-market-data`,
`docs.alpaca.markets/us/docs/historical-news-data.md`, `docs.alpaca.markets/us/reference/news-3.md`.

| Plan | Price | API calls | History | Exchanges | WebSocket | Real-time |
|---|---|---|---|---|---|---|
| **Free** | **$0/mo** | **200 calls/min** | **7+ years** | **IEX only** | **limited to 30 symbols** | via WebSocket; **15-minute delay via API** |
| **Algo Trader Plus** | **$99/mo** | **Unlimited** | **7+ years** | **All US Exchanges** | **Unlimited symbols** | Yes |

Both tiers: 100% market coverage claim, extended hours, corporate actions, aggregate bars,
snapshots, and indicative (free) or real-time (paid) US options. `[V]`

| Dimension | Finding | State |
|---|---|---|
| **Auth** | Same API key/secret as trading; WebSocket authenticates in-band with `{"action":"auth","key":…,"secret":…}` → `[{"T":"success","msg":"authenticated"}]` | `[V]` |
| **Rate limit / 429** | Free 200 calls/min, paid unlimited. Same 429 semantics as §3.1 | `[V]` |
| **Adjusted vs unadjusted** | **`adjustment` parameter, default `raw`**, values `raw`, `split`, `dividend`, `spin-off`, `all`, and they are **combinable with commas**. This is the cleanest corporate-action control of any vendor in scope | `[V]` |
| **Symbol-change handling** | **`asof` (YYYY-MM-DD, default current day)** maps symbols across name changes — set it to the decision date when backfilling history | `[V]` |
| **Bar schema** | `t` RFC-3339 timestamp, `o`, `h`, `l`, `c`, `v` (volume), `n` (trade count), `vw` (VWAP). Timeframes `[1-59]Min`, `[1-23]Hour`, `1Day`, `1Week`, `[1,2,3,4,6,12]Month`. `limit` default 1,000, max 10,000 **total points across all symbols**. `feed` default **`sip`**, options `sip`/`iex`/`boats`/`otc`. `currency` default USD. `sort` default `asc` | `[V]` |
| **WebSocket endpoints** | `wss://stream.data.alpaca.markets/{version}/{feed}` — `v2/sip`, `v2/iex`, `v2/delayed_sip`, `v1beta1/boats` (Blue Ocean ATS), `v1beta1/overnight`. Sandbox: `wss://stream.data.sandbox.alpaca.markets/...` | `[V]` |
| **WebSocket connection limit** | "The number of connections to a single endpoint from a user is limited based on the user's subscription, but in many subscriptions (or without one) **this limit is 1**." One process owns the socket; a second connection evicts or is refused | `[V]` |
| **WebSocket error codes** | `400` invalid syntax, `401` not authenticated, `402` auth failed, `403` already authenticated, `404` auth timeout, `405` symbol limit exceeded, `406` connection limit exceeded, `407` slow client, `409` insufficient subscription, `410` invalid subscribe action for this feed, `500` internal error | `[V]` |
| **WebSocket message types** | `t` trades, `q` quotes, `b` minute bars, `d` daily bars, `u` updated bars, `c` trade corrections, `x` trade cancels/errors, `s` trading status, `i` order imbalances, `l` LULD | `[V]` |
| **Reconnect / backfill** | **CONFIRMED ABSENT, 2026-08-26.** Both `docs.alpaca.markets/docs/streaming-market-data` and `…/us/docs/real-time-stock-pricing-data` were retrieved in full and **neither addresses reconnection, message replay, sequence numbers, resume tokens, or what happens to data missed during a disconnect**. The same pages *do* document the connection limit (“in many subscriptions (or without one) this limit is 1”) and that “**slow clients may get disconnected if their buffer becomes full**”. **Gap-is-lost is therefore the documented reality, not a precaution**: on reconnect the client re-fetches the affected window from REST before resuming (rule N5) | `[V]` retrieved 2026-08-26 — status upgraded from `[U] not retrieved` to `[V] retrieved, silence confirmed` |
| **Corrections are a live message type** | `c` (correction) and `x` (cancel/error) mean a trade already delivered can be revised. Any 5-minute bar built client-side from trades must be revisable, or stops will trigger on prints that were later cancelled | `[V]` |
| **Survivorship / delisted coverage** | Not claimed and not documented. Alpaca is not used for backtest history (F-3), so this does not bind | `[U]` §5 M-2 |
| **News** | `GET /v1beta1/news` on `data.alpaca.markets` (sandbox `data.sandbox.alpaca.markets`). "All news data is currently provided directly by **Benzinga**", "dating back to **2015**", "130+ news articles per day". Params `symbols`, `start`, `end` (RFC-3339 or YYYY-MM-DD), `sort` (default `desc`), `limit` **default 10, max 50**, `include_content`, `exclude_contentless`, `page_token`. Fields: `id`, `headline`, `author`, `created_at`, `updated_at`, `summary`, `content` (may contain HTML), `images`, `symbols`, `source`, `url` | `[V]` |
| **News redistribution terms** | **Not published on the retrieved pages.** Since ADR-04 uses news only as internal LLM context and never redisplays it, the exposure is low, but the licence text is an open item | `[U]` §5 M-8 |
| **Sandbox vs prod** | Paper API + `data.sandbox.alpaca.markets` + `stream.data.sandbox.alpaca.markets`. **Paper accounts receive free IEX real-time data**, so a paper run is also an IEX-quality run (F-2 + F-13 compound) | `[V]` |
| **Cost** | $0 / $99 per month | `[V]` |
| **Tick / lot, partial fills, rejection codes** | Not applicable to a data API; see §3.1 | — |

**Design consequence.** Alpaca data earns exactly one job: the **live 5-minute monitoring path for
held positions** (ADR-13), where broker-native coherence is a real advantage — the bar that trips a
stop comes from the venue that will fill the resulting order. It must not screen (F-2) and cannot
backtest (F-3). Two hard client rules fall out: the **stream is single-connection**, so the
monitor process is a singleton and its restart must be crash-safe; and because `content` "might
contain HTML", **news text is untrusted input** that goes through the `[CONST-4]` sanitiser before
any LLM sees it — HTML in a field is exactly the shape a prompt injection arrives in.

**Dies at 09:31.** Held-position monitoring goes blind: no 5-minute bars, so ATR stops and
exit-hierarchy triggers cannot evaluate. Under `[CONST-6]` and ADR-10, stale price data halts new
entries immediately and raises CRITICAL. Open positions retain their broker-side protective stops
placed at entry (ADR-13 §6) — which is precisely why that rule exists. Backup: Massive real-time,
if the Advanced tier is held; otherwise the correct behaviour is to stop, not to substitute a
delayed feed for a real-time one.

---

### 3.3 Massive (formerly Polygon.io) — Market Data

**Docs retrieved `[V]`:** `massive.com/pricing`, `massive.com/docs/rest/stocks/aggregates/custom-bars`,
`massive.com/docs/rest/stocks/corporate-actions/splits`,
`massive.com/docs/rest/stocks/corporate-actions/dividends`,
`massive.com/docs/rest/stocks/tickers/all-tickers.md`,
`massive.com/blog/understanding-professional-status`.

**Rebrand (F-1).** `polygon.io/*` → `301` → `massive.com/*`. Existing endpoints, SDKs and accounts
continue to work; `api.polygon.io` remains a live API host. Config records both. `[V]`

| Plan (monthly billed; −20% annual) | Price | API calls | History | Real-time | Included |
|---|---|---|---|---|---|
| Stocks Basic | **$0** | **5 calls/minute** | **2 years** | End-of-day | Reference data, corporate actions, minute aggregates. **No WebSockets, no flat files** |
| Stocks Starter | **$29** | Unlimited | **5 years** | 15-min delayed | + Flat Files, WebSockets, Snapshot, Second Aggregates |
| **Stocks Developer** | **$79** | Unlimited | **10 years** | 15-min delayed | + Trades |
| Stocks Advanced | **$199** | Unlimited | **20+ years** | **Real-time** | + Quotes, + **Financials & Ratios** |

`[V]` — every figure quoted from the pricing page. Standalone **Financials & Ratios $29/mo**;
**Benzinga partner data $99/mo per dataset** (F-6); NYSE order imbalances $49/mo.

| Dimension | Finding | State |
|---|---|---|
| **Auth** | API key. No expiry, no daily re-auth | `[V]` |
| **Rate limit / 429** | **5 calls/minute on Basic; unlimited on Starter and above.** The exact HTTP status and headers returned on breach were **not retrievable** — the client uses a conservative 5/min bucket on Basic and treats any 4xx above 400 as retry-with-backoff | `[V]` limit / `[U]` §5 M-4 |
| **Adjusted vs unadjusted** | `GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`, parameter **`adjusted`, default `true`**: "By default, results are adjusted. Set this to false to get results that are NOT adjusted for splits." **We always pass `adjusted=false`** (`[DEFAULT-P3]`). Note the wording covers **splits**, not dividends — dividend adjustment is ours to compute from the dividends endpoint | `[V]` |
| **Bar schema** | `t` **Unix milliseconds, window start**, presented in Eastern Time; `o`, `h`, `l`, `c`, `v`, `vw`, `n`. `limit` default 5,000, max 50,000. "Aggregates are constructed exclusively from qualifying trades" | `[V]` |
| **Corporate actions — splits** | `GET /stocks/v1/splits`; params `ticker`, `execution_date`, `adjustment_type`, `limit` (max 5,000). Fields `execution_date`, `split_from` (denominator/old), `split_to` (numerator/new), `ticker`. **Basic 2 years; Starter and above all history back to 25 October 1978** | `[V]` |
| **Corporate actions — dividends** | `GET /stocks/v1/dividends`; filters on `ticker`, `ex_dividend_date` (with gt/gte/lt/lte), `frequency`, `distribution_type`. Fields `declaration_date`, `ex_dividend_date`, `record_date`, `pay_date`, `cash_amount`, `frequency` (0–365), `distribution_type` ∈ recurring/special/supplemental/irregular/unknown. **Basic 2 years; Starter and above all history since 15 January 2000** | `[V]` |
| **Survivorship bias** | **RESOLVED IN FULL, 2026-08-26.** The vendor knowledge base states: “**our market data includes companies that have been delisted from the exchanges and is stored as it occurred on that date**”, framed explicitly against survivorship bias (“the tendency to focus on the performance of existing stocks or funds without considering those that have failed”), plus a **Ticker Events Endpoint** that “displays a ticker symbol’s history”. `[V]` retrieved 2026-08-26 from `massive.com/knowledge-base/article/what-does-massive-do-with-delisted-tickers`. **M-2 is closed: delisted price history is retained, not merely delisted reference data.** The v0.4 wording below stands as the reference-data half of the answer. **Materially addressed, and this is the finding that settles the capability.** `GET /v3/reference/tickers` accepts **`active`** ("tickers … actively traded on the queried date") and **`date`** ("Specify a point in time to retrieve tickers available on that date"), and returns **`delisted_utc`** ("The last date that the asset was traded"), with records extending back to **10 September 2003** depending on tier. A point-in-time universe is therefore reconstructible from the vendor. **What is still not stated is whether *price history* for delisted names is retained** — the reference data survives, and the bars are the open question | `[V]` for reference data; `[U]` for delisted price history, §5 M-2 |
| **Reference-data fields** | `ticker`, `name`, `market`, `locale`, `primary_exchange`, `type`, `active`, `currency_name`, `cik`, `composite_figi`, `share_class_figi`, `last_updated_utc`, `delisted_utc`. This closes P0.1 Q11: `type` (with a Ticker Types endpoint) is the security-type discriminator ADR-14's exclusion filter needs, and `cik` is the free join key to EDGAR | `[V]` |
| **Consolidated vs single-venue** | The pricing page claims "100% Market Coverage" on every tier and the aggregates page says bars are built "exclusively from qualifying trades", but **the word "consolidated" is not used**. Given ADR-14's ADDV filter depends on it, this is verified enough to prefer Massive over IEX-only Alpaca and **not** verified enough to stop cross-checking (rule N7) | `[V]` claim / `[U]` wording, §5 M-4 |
| **WebSocket** | Included from Starter upward, absent on Basic. Endpoint shape `WS /stocks/AM` for minute aggregates, subscribable per-ticker, comma-separated, or `*`. **Auth flow, connection limits, reconnect and replay semantics were not retrievable** — same gap-is-lost treatment as Alpaca (rule N5) | `[V]` availability / `[U]` §5 M-3 |
| **Flat files** | Included from Starter upward: daily S3 downloads per asset class. This is the bulk-load path if REST paging of 10 years × 1,500 names proves slow | `[V]` |
| **Tick / lot size** | Not a vendor field; regulatory (F-10) | — |
| **Sandbox** | No separate sandbox environment is documented; the free Basic tier is the practice environment | `[U]` §5 |
| **ToS / automated access** | Every retail plan is badged **"Individual use"** and gated on **non-professional** status: an 11-question test where registration with the SEC/CFTC, acting as an investment adviser, or performing bank functions requiring registration makes the subscriber professional; **"Your account must be in your own name to qualify as a Non-Professional Subscriber."** Business plans are priced separately | `[V]` |

**Design consequence.** **Stocks Developer at $79/mo is the load-bearing purchase of this phase** —
the cheapest verified source of the 10-year history §0.3 C-3 and ADR-08 require, of point-in-time
ticker membership, and of full split and dividend history. Its 15-minute delay is irrelevant to
ADR-14, which computes on the prior session's completed daily bar at 22:30 UTC and freezes the
order list overnight. Note what Developer does **not** include: **Financials & Ratios is an
Advanced-tier or $29 add-on feature**, which is why fundamentals stay with FMP rather than
collapsing into one vendor.

**Dies at 09:31.** Almost no live impact: Massive serves the **nightly** ingest and backtests,
neither of which runs at 09:31. If it is still down at 21:45 UTC, that session's ingest fails, the
pipeline precondition is unmet, the job exits non-zero (ADR-02), no order list is produced and
there is **no trading that session** — the correct fail-closed outcome. Backfill by `trading_date`
the next day; ADR-10 rates market data RPO ≤ 24 h precisely because it is re-fetchable.

---

### 3.4 Financial Modeling Prep (FMP) — Fundamentals

**Docs retrieved `[V]`:** `site.financialmodelingprep.com/developer/docs/pricing` (including the
comparison table and licensing footer).

| Plan | Price | API calls | History | Coverage | Notable |
|---|---|---|---|---|---|
| Basic | **Free** | **250 calls/day** | 5 years | — | EOD only, profile/reference, 150+ endpoints |
| Starter | **$19.00/mo** billed annually | **300 calls/min** | 5 years | US | Annual fundamentals and ratios, historical prices, news, crypto/forex |
| **Premium** | **$49.00/mo** billed annually | **750 calls/min** | **30+ years** | US, UK, Canada | **Full fundamentals and ratios**, intraday charts, technical indicators, corporate calendars, custom DCF |
| Ultimate | **$99.00/mo** billed annually | **3,000 calls/min** | 30+ years | Global | Transcripts, ETF/MF holdings, 13F, 1-minute intraday, bulk and batch delivery |

`[V]`. The page carries a **Personal Use / Commercial Use** toggle and a **Monthly / Annual**
toggle advertising "Up To 34% Discount"; the prices above are the **annual-billed personal** view.

| Dimension | Finding | State |
|---|---|---|
| **Auth** | API key as a query parameter. No expiry, no daily re-auth | `[V]` |
| **Rate limit** | Per-minute call limits by plan as tabled; Basic is a **per-day** limit instead | `[V]` |
| **Second quota axis — bandwidth (F-11)** | "API usage has a trailing 30 days bandwidth limit of: **Free plan - 500MB, Starter plan - 20GB, Premium plan - 50GB, Ultimate plan - 150GB**, Build plan - 100GB, and Enterprise plan 1TB+." A 1,500-name fundamentals backfill is a bandwidth event, not a call-count event | `[V]` |
| **429 behaviour** | **Not published on the pricing page**, and no separate rate-limit doc was retrievable. Client uses its own bucket at the plan limit plus a rolling byte counter, and backs off on any 429 | `[U]` §5 M-4 |
| **Adjusted vs unadjusted / corporate actions** | FMP is used for **fundamentals**, not prices, under this design; its price-adjustment semantics were not retrieved and are not relied on | `[U]` — not on the critical path |
| **Survivorship bias** | The comparison table lists a **"Delisted Companies"** endpoint on the retail plans, so delisted issuers are addressable. Whether fundamentals histories are restated or point-in-time is **not stated** — which is exactly why rule N7 makes EDGAR the authority on disagreement | `[V]` endpoint / `[U]` point-in-time |
| **Tick / lot, partial fills, rejection codes, WebSocket** | Not applicable — REST fundamentals API, no trading and no streaming in this role | — |
| **Sandbox** | None documented; the free tier is the practice environment | `[U]` |
| **Cost** | As tabled; **month-to-month pricing is higher than the annual-billed figures shown and was not captured** | `[V]` annual / `[U]` monthly |
| **ToS / automated access** | Automated access is the product. The binding clause: **"Displaying or redistributing data sourced from FMP requires a specific Data Display and Licensing Agreement with FMP."** All four retail plans show `Usage: Individual`. Internal computation of a private signal is not display or redistribution; a public dashboard would be | `[V]` |

**Design consequence.** ADR-14 needs ≥ 4 reported quarters per name across 1,500 names and
sector-normalised z-scores; ADR-13 Chain B budgeted 40 quarters. Starter's 5 years is marginal;
**Premium at $49/mo (30+ years, full fundamentals and ratios, 750 calls/min) is the right tier**,
and 750 calls/min trivially covers ADR-14's staggered ~25-symbol refresh. The bandwidth limit,
not the call limit, is what a naive backfill will hit first.

**Dies at 09:31.** No live impact — fundamentals refresh is a staggered nightly job. An extended
outage degrades gracefully: ADR-14's eligibility filter requires ≥ 4 reported quarters, so names
whose fundamentals go stale simply fail eligibility at the next weekly reconstitution instead of
being scored on stale data. `[CONST-6]` forbids imputing the missing values. Backup: SEC EDGAR
XBRL (authoritative but unnormalised) and Finnhub free for a reduced field set.

---

### 3.5 Finnhub — supplementary fundamentals and news

**Docs retrieved `[V]`:** `finnhub.io/pricing`, `finnhub.io/docs/api` (Rate Limits section).

| | Free | All-In-One |
|---|---|---|
| **Price** | **$0/month** | **$3,500/month**, billed annually |
| **Rate limit** | **60 API calls/minute** | Market data **900/min**; fundamentals **300/min** |
| **Global cap** | **"On top of all plan's limit, there is a 30 API calls/second limit."** | same |
| **Coverage** | US | Global |
| **Company news** | 1 year + real-time | 20 years + real-time |
| **WebSocket** | **50 symbols** | Unlimited |
| **OHLC history** | — | 30+ years |
| **Survivorship-bias free** | — | **Yes (explicitly advertised)** |
| **Licence** | "Personal Use. Terms apply" | "Personal Use. Terms apply" |

| Dimension | Finding | State |
|---|---|---|
| **Auth** | `token=apiKey` query parameter **or** `X-Finnhub-Token: apiKey` header. Base path `/api/v1`. A Swagger schema is published at `finnhub.io/static/swagger.json` — useful for generating a typed client rather than hand-rolling one | `[V]` |
| **429 behaviour** | **"If your limit is exceeded, you will receive a response with status code `429`."** Header names for remaining quota were not documented on the retrieved section | `[V]` / `[U]` |
| **Adjusted, corporate actions, tick/lot, partial fills, rejection codes** | Not applicable in the supplementary role assigned here | — |
| **Sandbox** | None documented | `[U]` |
| **ToS** | Both tiers are labelled "Personal Use. Terms apply" (F-9) | `[V]` |

**F-7 restated:** nothing exists between $0 and $3,500/month. Finnhub is a **free supplementary
source only**, never a paid primary or backup at this programme's scale. Its All-In-One tier is
the only offering in scope that explicitly advertises **survivorship-bias-free** data, which
`[RS §13]` demands — worth recording as the market price of buying that property outright rather
than engineering it.

**Dies at 09:31.** Negligible. Nothing in the critical path depends on it, by design.

---

### 3.6 Zerodha Kite Connect — India broker (primary per `[CONST-10]`)

**Docs retrieved `[V]`:** `kite.trade/docs/connect/v3/` (user, orders, market-quotes, websocket,
exceptions), `zerodha.com/products/api/`,
`support.zerodha.com/…/kite-api/articles/static-ip`,
`support.zerodha.com/…/kite-api/articles/kite-connect-api-faqs`.

**Authentication — the decisive detail (F-4).**

| Aspect | Finding | State |
|---|---|---|
| Prerequisites | Active Zerodha trading account; **2FA TOTP enabled**; developer account; registered redirect URL | `[V]` |
| Login flow | Browser → `https://kite.zerodha.com/connect/login?v=3&api_key=…` → `request_token` at the redirect URL → POST `request_token` + `checksum` to `/session/token` → `access_token` | `[V]` |
| Checksum | **SHA-256 of (`api_key` + `request_token` + `api_secret`)** | `[V]` |
| `request_token` lifetime | "only a few minutes", single-use | `[V]` |
| **`access_token` lifetime** | **"it'll expire at `6 AM` on the next day (regulatory requirement)"**; also invalidated by API logout or a master logout from Kite Web | `[V]` |
| **`refresh_token`** | **"only available to certain approved platforms"** — not to an ordinary developer app | `[V]` |
| Request signing | `Authorization: token api_key:access_token` | `[V]` |
| Expiry signal | `TokenException` preceded by **403**; "clear the user's session and re-initiate a login" | `[V]` |

**This is the answer to P0.1's A4 and to ADR-11 gate item 2: the daily login is a hard, regulatory,
interactive requirement, and the documented automatic-refresh mechanism is unavailable to us.** Any
India go-live plan budgets a human action every trading morning before 06:00 IST.

**Static IP (new in v0.2).** Zerodha's support documentation states a static IP is required for
**"API-based order placement"**, **"effective 1 April 2026"**; "You can add up to two IPs, one per
line" registered in the developer console; and **"The WebSocket market data stream and other APIs,
such as orderbook and positions, can continue to be accessed from any IP address."** The
registrant must confirm "the static IPs will be used exclusively by me and/or my immediate
family." `[V]` This is already in force today and directly serves `[CONST-9]`'s static-IP clause.

**Rate limits — documented per endpoint.** `[V]`

| Endpoint | Limit |
|---|---|
| Quote | **1 req/second** (batched: 500 instruments per call) |
| Historical candle | **3 req/second** |
| Order placement | **10 req/second** |
| All other endpoints | **10 req/second** |

Plus, verbatim: **"limitations at 400 orders per minute and 10 orders per second"**; **"a single
user/API key will not be able to place more than 5000 orders per day"** across all segments and
varieties; and **"a maximum of 25 modifications are allowed per order"**, after which the order
must be cancelled and re-placed. `[V]`

The 1 req/second quote limit sounds fatal for a 500-name India universe until it is read together
with the batch cap: `/quote` accepts **500 instruments per request**, so the entire India universe
is **one request per second**, not five hundred. v0.1 flagged this as the sharpest constraint in
the document; with the batch cap verified, it is not a constraint at all.

| Dimension | Finding | State |
|---|---|---|
| **Error model** | HTTP `400` bad params, `403` session expired (must re-login), `404`, `405`, `410`, `429` rate limited, `500`, **`502` "The backend OMS is down and the API is unable to communicate with it"**, `503` service unavailable, `504` gateway timeout | `[V]` |
| **Exception taxonomy** | `TokenException`, `UserException`, `OrderException`, `InputException`, `MarginException`, `HoldingException`, `NetworkException`, `DataException`, `GeneralException` — returned in `error_type`. This is the richest rejection taxonomy of any broker in scope: `MarginException` (insufficient funds) and `HoldingException` (insufficient holdings to sell) are separately identifiable, which most brokers collapse into one generic reject | `[V]` |
| **Order model** | `order_type` ∈ `MARKET`, `LIMIT`, `SL`, `SL-M`; `product` ∈ `CNC`, `NRML`, `MIS`, `BO`, `CO`; `exchange` ∈ `NSE`, `NFO`, `BFO`, `CDS`, `BSE`, `MCX`, `MF`, `BCD`. Under ADR-12 (long-only cash) and ADR-05 (equities only), **only `CNC` on `NSE`/`BSE` is in scope** | `[V]` |
| **Other order params** | `price`, `trigger_price`, `disclosed_quantity`, `validity`, `validity_ttl`, **`market_protection`** (0–100 for a custom %, or −1 for automatic), **`autoslice`** (automatic order splitting) | `[V]` |
| **Idempotency key** | **No idempotency key exists.** The nearest facility is **`tag`: "alphanumeric, max 20 chars"**, which identifies but does not deduplicate. **Design consequence: the India adapter cannot rely on broker-side idempotency and must implement client-side dedupe** — a persisted intent record written before the call, reconciled against the order book after it | `[V]` |
| **Partial fills** | Represented by three quantity fields — `filled_quantity`, `pending_quantity`, `cancelled_quantity`. **`average_price` reflects the actual execution price only for `COMPLETE` orders**, so a partially filled order's average price must be computed from trades, not read from the order | `[V]` |
| **Order statuses** | Terminal: `COMPLETE`, `REJECTED`, `CANCELLED`; live: `OPEN`, `TRIGGER PENDING`. Interim: `PUT ORDER REQ RECEIVED`, `VALIDATION PENDING`, `OPEN PENDING`, `MODIFY VALIDATION PENDING`, `MODIFY PENDING`, `CANCEL PENDING`. The interim states are **not** errors and a state machine that treats unknown strings as failures will misfire on all six | `[V]` |
| **WebSocket** | **3 connections per API key**; **3,000 instruments per connection**; binary frames of 8 / 44 / 184 bytes for `ltp` / `quote` / `full` modes; "the API will send a 1 byte 'heartbeat' every couple seconds to keep the connection alive" when idle. **Reconnect and backfill semantics are not documented** — gap-is-lost (rule N5). A missing heartbeat is the liveness signal | `[V]` / `[U]` §5 M-3 |
| **Tick / lot size** | `tick_size` and `lot_size` are fields of the **instruments CSV dump**; `/quote` returns market depth but the static attributes come from the dump | `[V]` |
| **Sandbox** | No sandbox is documented for Kite Connect. Testing happens against the live API with the live account | `[U]` §5 |
| **Cost** | **₹500/month per API key**, and "Both are included at no additional cost with the paid Kite Connect plan" — i.e. **historical candle data and WebSocket streaming are included**, not separately priced. A free "Personal" tier exists for order/portfolio management without the full API suite | `[V]` |
| **ToS / automated access** | API-based order placement is permitted subject to the static-IP regime above. Additional SEBI/NSE retail-algo obligations (order-rate thresholds triggering exchange registration of the strategy, and mandatory market protection on market orders) are described by Zerodha staff on the Kite Connect forum but **not in the API reference**, and are therefore recorded as `[F]`, not as binding limits | `[V]` static IP / `[F]` the rest, §5 M-9 |

**Design consequence.** Zerodha's documentation quality is the best in this phase — its rate
limits, exception taxonomy, token lifetime and static-IP regime are all explicit. Its two hard
edges for our design are (1) **no idempotency key**, forcing client-side dedupe, and (2) **an
interactive daily login that no documented mechanism automates**.

**Dies at 09:31.** India is unfunded under ADR-11, so today: no impact. Post-activation the
equivalent question is "dies at 09:16 IST" — one minute after the NSE open. Then it is the same
shape as Alpaca, with two extra hazards: a `403`/`TokenException` at that moment is
**indistinguishable from a normal daily expiry** and needs an interactive human login during
market hours; and a `502` means the OMS is down while the API is up, which is retryable in a way
that `400` is not and must be classified differently by the retry policy.

---

### 3.7 Upstox — India broker (backup per `[RS §12]`)

**Docs retrieved `[V]`:** `upstox.com/developer/api-documentation/api-overview`,
`…/authentication/`, `…/get-token/`, `…/rate-limiting/`.

| Dimension | Finding | State |
|---|---|---|
| **Auth flow** | OAuth 2.0 authorization-code: `GET https://api.upstox.com/v2/login/authorization/dialog` (`client_id`, `redirect_uri`, `response_type=code`) → single-use `code` → server-to-server `POST /v2/login/authorization/token`. "The `code` … is valid for a single use, regardless of whether the access token generation succeeds or encounters an issue" — a failed exchange costs a full re-login | `[V]` |
| **Token lifetime (F-5)** | **"The `access_token` … has a specific validity period that lasts until `3:30 AM` the following day, regardless of the time it was generated."** The token response also carries an **`extended_token`**, "designed for prolonged usage, primarily for read-only access to various API endpoints" | `[V]` |
| **Why F-5 matters** | The daily re-auth burden at Upstox lands on the **order path only**; market data, streaming and read-only portfolio/account can run unattended. For a system whose monitor runs continuously (ADR-13) but whose orders occupy one short window, that is a materially better operational fit than Zerodha's all-or-nothing token | `[V]` |
| **Rate limits** | **Per-API, per-user** — "The rate limits are enforced on a per-API, per-user basis": order placement group (place/modify/cancel/multi-order/GTT) **10/sec, 500/min, 2,000/30min** for regular algos and **50/sec** for SEBI-registered algos; other standard APIs (holdings, positions, funds, historical candles) **50/sec, 500/min, 2,000/30min**; payout 10/sec (restricted access 10/min, 300/30min); Apply IPO 1/sec, 10/min, 300/30min | `[V]` |
| **429 behaviour** | **"Exceeding these limits might result in temporary suspension of access."** **No HTTP status code is documented** — the client must treat any 4xx on a throttled endpoint as a backoff signal and must not assume 429 | `[V]` wording / `[U]` §5 M-4 |
| **`[CONST-9]` alignment** | Upstox exposes first-class **Kill Switch** (`/update-kill-switch`) and **Static IP** (`/update-app-static-ips`) API endpoints. A broker-side kill switch is genuine defence in depth beneath ADR-01's three channels, because it survives our VM being compromised or unreachable | `[V]` |
| **Instrument identity** | `instrument_token` = `<segment>` + `|` + `<ISIN>` (e.g. `NSE_EQ|INE669E01016`) — ISIN-keyed, satisfying ADR-11's stable-identity requirement without a mapping table | `[V]` |
| **Sandbox vs prod** | `sandbox.upstox.com`, **"Currently supports place, modify, and cancel order APIs"** only — no market data, no portfolio. Adequate for order-lifecycle tests, useless for end-to-end rehearsal | `[V]` |
| **Order fields (sandbox example)** | `quantity`, `product`, `validity`, `price`, `instrument_token`, `order_type`, `transaction_type`, `disclosed_quantity`, `trigger_price` | `[V]` |
| **Idempotency, partial fills, rejection codes** | **Not retrieved.** No idempotency key is documented; partial-fill representation and the rejection enumeration are unknown | `[U]` §5 M-9 |
| **WebSocket reconnect / backfill** | Not retrieved | `[U]` §5 M-3 |
| **Tick / lot size** | Not retrieved; expected in the instrument master, as at Zerodha | `[U]` §5 M-9 |
| **Cost** | **Not published on the retrieved pages** | `[U]` §5 M-9 |
| **Regulatory banner** | The docs carry "Regulatory Changes for API and Algo Trading are Now Live", consistent with the SEBI 2025 framework in `[RS §16]`; the specific changes were not retrieved | `[V]` banner / `[U]` content |

**Dies at 09:31.** Not in the live path today. Note that the `extended_token`'s independence is
itself a resilience property: an Upstox *login* outage would not sever the data and monitoring
path the way a Zerodha login outage does.

---

### 3.8 SEC EDGAR — filings and insider transactions

**Docs retrieved `[V]`:** `sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`.

| Dimension | Finding | State |
|---|---|---|
| **Auth** | None. No key, no token, no expiry | `[V]` |
| **Rate limit** | **"Current max request rate: 10 requests/second."** The SEC "reserves the right to limit request rates" | `[V]` |
| **Required headers** | Declared **User-Agent** of the form `Sample Company Name AdminContact@<domain>.com`, plus `Accept-Encoding: gzip, deflate` and `Host: www.sec.gov` | `[V]` |
| **429 behaviour** | **The HTTP status returned on breach is not specified.** The policy text says traffic "identified as part of a botnet or an automated tool outside of the acceptable policy will be managed to ensure fair access" — enforcement may be a block rather than a status code, so the client stays strictly under 10/s rather than probing the boundary | `[V]` policy / `[U]` status code, §5 M-4 |
| **History depth** | EDGAR begins **1994/1995**; earlier filings are paper-only | `[V]` |
| **Business hours** | Accepts filings **Mon–Fri 06:00–22:00 ET** | `[V]` |
| **Dissemination cutoff** | Submissions beginning after **17:30 ET** — or **22:00 ET for Ownership Forms 3, 4 and 5** — are disseminated the **next business day** and appear in the following day's index | `[V]` |
| **Index build** | Daily indexes update nightly from ~22:00 ET. **Full and quarterly indexes are rebuilt weekly, early Saturday**, to incorporate post-acceptance corrections | `[V]` |
| **Mutability** | Filings can be removed or corrected after acceptance. Corrections land in that evening's index, but **removals processed later are never reflected in previously built daily/feed/oldload indexes** | `[V]` |
| **Data API** | JSON REST at `data.sec.gov` — submissions and XBRL company facts | `[V]` |
| **Identity** | CIK, permanent and never recycled. `company_tickers.json` / `company_tickers_exchange.json` map ticker ↔ CIK ↔ exchange, with the SEC's own caveat that it does "not guarantee accuracy or scope". Massive's `cik` field is the join key | `[V]` |
| **Filing-availability latency** | **Not documented.** P0.1 assumed "minutes after filing"; that assumption is **not confirmed** | `[U]` §5 M-8 |
| **Cost / ToS** | Free. Automated access is permitted within the declared-User-Agent and 10 req/s policy; "The SEC does not allow botnets or automated tools to crawl the site" outside that policy | `[V]` |
| **Adjusted data, corporate actions, tick/lot, partial fills, WebSocket** | Not applicable — filings archive, no prices and no trading | — |

**Two consequences P0.1 did not anticipate, both affecting P5.1's point-in-time correctness.**

1. **The 17:30 / 22:00 ET dissemination cutoff is a documented, exploitable-in-backtest boundary.**
   A Form 4 filed at 22:30 ET on day *T* is not in *T*'s index; it appears on *T+1*. A backtest
   timestamping insider signals by *filing* time rather than *dissemination* time carries up to a
   full session of look-ahead. **Binding on P5.1 (rule N1).**
2. **Weekly Saturday index rebuilds make EDGAR history mutable.** A filing present in Monday's
   index may be absent after Saturday's rebuild. Reproducibility (`[CONST-5]`, ADR-06) therefore
   requires snapshotting the index as retrieved and never re-deriving it. **Rule N2.**

**Dies at 09:31.** No live impact — EDGAR feeds a nightly ingest, and ADR-04 uses filings for
fundamental confirmation and the insider signal, neither intraday. A multi-day outage stalls the
insider feature; under `[CONST-6]` its absence propagates as a missing feature, never as a zero.
Backup: FMP's SEC-filings endpoints, accepting that a vendor's copy is not the primary source.

---

### 3.9 FRED — macro and regime inputs

**Docs retrieved `[V]`:** `fred.stlouisfed.org/docs/api/fred/`, `…/fred/errors.html`,
`…/api/terms_of_use.html`.

| Dimension | Finding | State |
|---|---|---|
| **Auth** | Free registered API key, "alphanumeric… uniquely associated with you"; "the Federal Reserve Bank of St. Louis will block requests with an invalid key". No expiry, no rotation requirement documented | `[V]` |
| **Base URL / format** | `https://api.stlouisfed.org/fred/`; XML by default, JSON via `file_type=json` | `[V]` |
| **Key endpoint** | `fred/series/observations` — "the observations or data values for an economic data series" | `[V]` |
| **Rate limit** | **Exists but is NOT numerically published.** Verbatim: *"Our API has rate limiting which returns a status code if exceeded. If you have a reason that you need to exceed our limit, please contact us."* The ToS reinforces it: the Bank "may impose or adjust the limit on the amount of bandwidth you may use or the number of transactions you may send or receive… at any time, at [its] discretion" | `[V]` that a limit exists; **`[U]` for the number**, §5 M-4 |
| **Error codes** | `400`, `404`, **`423 Locked`**, **`429 Too Many Requests`**, `500` | `[V]` |
| **Point-in-time** | **ALFRED** and `fred/series/vintagedates` give "the dates in history when a series' data values were revised" | `[V]` |
| **ToS — attribution** | **Mandatory notice:** "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis." | `[V]` |
| **ToS — third-party copyright** | "Data series available through the FRED® API may be owned by third parties and subject to copyright restrictions… Before using data series owned by third parties for anything other than your own personal use, you must contact the data owner." Copyrighted series "contain the word 'Copyright' in their notes" | `[V]` |
| **ToS — prohibitions** | No cloaking of identity, no unreasonable bandwidth, no use of "FRED"/"ALFRED"/"Federal Reserve Bank" in the application hostname, no implying endorsement | `[V]` |
| **Cost** | Free | `[V]` |
| **Adjusted data, corporate actions, tick/lot, partial fills, WebSocket, sandbox** | Not applicable — macro time-series REST API | — |

**This is the cleanest illustration of the "no guessed limits" rule in this phase.** A figure of
120 requests/minute circulates widely for FRED. **It does not appear anywhere in FRED's own
documentation**, so it is **not recorded as a limit anywhere in this document.** The client
implements adaptive backoff on `429` and `423` rather than a fixed budget (rule N8), and the
number goes to §5.

**Genuinely valuable finding: ALFRED solves a real look-ahead problem.** Macro series are
*revised*. A regime detector `[RS §5]` trained on the final revised value of GDP or unemployment
uses data that did not exist at the decision date. **Binding on P2.x and P5.1: macro features are
read at their vintage as of the decision date via ALFRED / `series/vintagedates`, never at their
current value (rule N3).** ADR-04 selected FRED without noticing this; it is the kind of subtlety
that silently inflates a backtest.

**Dies at 09:31.** Negligible intraday. Macro series update daily or monthly and the regime
detector consumes them nightly. A stale macro input is flagged `STALE` and the regime held at its
last computed value — never silently recomputed on partial data.

---

### 3.10 News — Benzinga via Alpaca, and why no standalone subscription is bought

**Docs retrieved `[V]`:** `newsapi.org/pricing`, `massive.com/pricing` (partner data),
`docs.alpaca.markets/us/docs/historical-news-data.md`, `…/us/reference/news-3.md`.

**NewsAPI.org**

| Plan | Price | Requests | Archive | Commercial use | Restrictions |
|---|---|---|---|---|---|
| **Developer** | **$0** | **100/day** | 1 month | **Not permitted** — "development and testing in a development environment only" | **Articles delayed 24 hours**; **localhost CORS only** |
| Business | **$449/mo** | 250,000/mo; overage $0.0018/req | **5 years** | Permitted | 99.95% SLA |
| Advanced | **$1,749/mo** | 2,000,000/mo; overage $0.0009/req | 5 years | Permitted | 99.95% SLA |
| Enterprise | Custom | Unlimited | Extended | Permitted | On-prem option |

`[V]`. The free tier fails on three independent grounds — non-commercial licence, 24-hour delay
(fatal for a news signal), and localhost-only CORS. The first usable tier is **$449/month, roughly
3.5× the entire rest of the recommended stack**, for a data class ADR-04 assigns a supporting role
and ADR-13 Chain G feeds into ~15 LLM calls per session.

**The bundled alternatives, corrected (F-6).**

| Source | Reality | State |
|---|---|---|
| **Massive** | Benzinga is **partner data at $99/month per dataset** — an add-on, not an inclusion. v0.1's assumption that Massive's news came free with the subscription was **wrong** | `[V]` |
| **Alpaca** | The news API is served from the same `data.alpaca.markets` host as the bars, "provided directly by **Benzinga**", history "dating back to **2015**", "130+ news articles per day", `limit` max 50 per page with `page_token` paging. **Same underlying publisher as Massive's $99 add-on, reached through a subscription we are already buying** | `[V]` |
| **FMP** | "Financial Market News" is included from Starter upward — a secondary source, field-suitability unassessed | `[V]` |

**Decision: no standalone news subscription. News comes from Alpaca's Benzinga feed
(`[DEFAULT-P6]`), with FMP as a degraded fallback.** This keeps vendor count, ToS surface and
marginal cost at zero, and it couples the news dependency to the Alpaca data plan rather than to
Massive's — which is the correction v0.1 needs.

**The unresolved question that matters more than price.** P0.1 Q4 asked whether a news archive is
**point-in-time** — whether the historical archive matches what was visible at the time. **No
provider in scope documents this.** ADR-04 already imposed a one-session ingestion lag; this phase
confirms the concern is real and unaddressed by every vendor examined. **Binding on P5.1: news
features remain forward-validated only and may not enter walk-forward optimisation (rule N4)**
until a vendor documents archive integrity.

**Dies at 09:31.** No impact on the decision path — news feeds the Tier-3 research agent at
22:30 UTC. A news outage means the gate has less context; per `[CONST-6]` the correct behaviour is
to degrade to the deterministic Tier-1/Tier-2 path — which ADR-13 Chain G already establishes as
the only promotable path — never to invent context.

---

### 3.11 DeepSeek — **fallback** LLM (was primary until AD-5, 2026-08-25)

**Docs retrieved `[V]`:** `api-docs.deepseek.com/`, `…/quick_start/pricing`, `…/quick_start/rate_limit`.

| Dimension | Finding | State |
|---|---|---|
| **Auth / endpoint** | API key. Base `https://api.deepseek.com` (OpenAI format) and `https://api.deepseek.com/anthropic` (Anthropic format). "The DeepSeek API uses an API format compatible with OpenAI/Anthropic" — an existing SDK works by configuration alone | `[V]` |
| **Models** | `deepseek-v4-flash`, `deepseek-v4-pro`, `deepseek-v4-flash-vision-exp` | `[V]` |
| **Context / output** | Context length **1M tokens**; maximum output **384K tokens** — far beyond anything ADR-13 Chain G needs, so context is not a design constraint | `[V]` |
| **Rate limit model** | **Concurrency, not RPM/TPM**: "A request counts as one concurrent connection from the time it is sent until the model response is complete." Limits: `deepseek-v4-flash` **2,500**, `deepseek-v4-pro` **500** | `[V]` |
| **429 behaviour** | "you will receive an HTTP 429 error code", applied at the account level and per `user_id` where isolation is used | `[V]` |
| **Idle-connection behaviour** | Under load: non-streaming requests "Continuously return empty lines"; streaming returns `: keep-alive` SSE comments; **"If the request has not started inference after 10 minutes, the server will close the connection."** A client treating an empty line as EOF truncates silently | `[V]` |
| **Cost** | Per 1M tokens, USD. **Off-peak rates are half of peak.** Peak = **01:00–04:00 and 06:00–10:00 UTC, Mon–Fri** | `[V]` |
| **Data retention / training use** | **Not retrieved** — `cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html` timed out and no terms link appears on the retrieved doc pages | `[U]` §5 M-7 |
| **Sandbox** | None documented; the production endpoint is the only environment | `[U]` |
| **Adjusted data, corporate actions, tick/lot, partial fills, WebSocket** | Not applicable | — |

| Model | Input (cache hit) | Input (cache miss) | Output | Concurrency |
|---|---|---|---|---|
| **`deepseek-v4-flash`** | $0.007 off / $0.014 peak | **$0.22 off / $0.44 peak** | **$0.66 off / $1.32 peak** | 2,500 |
| `deepseek-v4-pro` | $0.022 off / $0.044 peak | $0.66 off / $1.32 peak | $1.98 off / $3.96 peak | 500 |
| `deepseek-v4-flash-vision-exp` | $0.007 off / $0.014 peak | $0.22 off / $0.44 peak | $0.66 off / $1.32 peak | 2,500 |

**Recomputing ADR-13 Chain G against verified prices.** `[D]` ADR-14 runs the pipeline at
**22:30 UTC**, inside DeepSeek's **off-peak** window — the system pays the discounted rate by
construction, with no scheduling gymnastics. At gate width 15, 21 sessions/month, 6,000 input +
1,500 output tokens per candidate (P0.1 A11, still unverified):

- Input: 315 × 6,000 = 1.89M tokens × $0.22/M = **$0.42**
- Output: 315 × 1,500 = 0.47M tokens × $0.66/M = **$0.31**
- **≈ $0.73/month on `deepseek-v4-flash`.**

Full-history backtest replay, 2,520 sessions × 15 candidates = 37,800 calls:
37,800 × (6,000 × $0.22/M + 1,500 × $0.66/M) = 37,800 × $0.00231 ≈ **$87 per full run.** `[D]`

**ADR-13 Chain G's conclusion survives contact with real prices.** Live LLM cost is ~$0.73/month
against a $200–500 ceiling, and the ceiling is again shown to be a *backtest-replay* number
(2–5 full runs). P0.1's $124/run estimate was ~40% high. The gate's design objective remains
safety, not cost — cost cannot justify widening or narrowing it.

**Dies at 09:31.** No impact — the LLM runs at 22:30 UTC. If it is down then, the inference gate
fails closed: candidates proceed on deterministic Tier-1/Tier-2 scores with no thesis, and any
decision rule requiring a thesis emits NO-TRADE. This is safe precisely because Chain G already
excludes the LLM tier from the promotable strategy. Backup: OpenAI (§3.12).

---

### 3.12 OpenAI — **primary** LLM since AD-5 (was fallback in v0.1–v0.3)

**Docs retrieved `[V]`:** `developers.openai.com/api/docs/pricing`,
`…/api/docs/guides/rate-limits.md`, `…/api/docs/guides/your-data.md`.

Prices per 1M tokens, USD, **Standard** tier, short context:

**Auth (M-11a, RESOLVED 2026-08-26** `[V]`, `developers.openai.com/api/reference/overview`**).** “The OpenAI API accepts **bearer credentials from API keys or from short-lived access tokens created with workload identity federation**.” Header: `Authorization: Bearer OPENAI_API_KEY_OR_ACCESS_TOKEN`. Optional scoping headers `OpenAI-Organization: $ORGANIZATION_ID` and `OpenAI-Project: $PROJECT_ID`. Key handling, in the vendor’s own words: “**Remember that your API key is a secret. Don’t share it with others or expose it in any client-side code such as browsers or apps**” and “**Load API keys from an environment variable or key management service on the server**”. Revocation: “**Revocations of an API key take effect within a few seconds**”. No key expiry policy is published. **This is consistent with the `[CONST]` HashiCorp Vault line and needs no design change**; workload-identity federation is recorded as an available future option for P6.2, not adopted now.

| Model | Input | Cached input | Cache writes | Output |
|---|---|---|---|---|
| `gpt-5.6-sol` | $4.00 | $0.40 | $5.00 | $20.00 |
| `gpt-5.6-terra` | $2.00 | $0.20 | $2.50 | $12.00 |
| **`gpt-5.6-luna`** | **$0.20** | **$0.02** | $0.25 | **$1.20** |

**Batch** and **Flex** tiers are 50% of Standard; **Fast mode** is 200%; long context is roughly
2× short; regional data-residency endpoints carry a **10% uplift** for models released on or after
2026-03-05. `[V]`

| Dimension | Finding | State |
|---|---|---|
| **Rate-limit metrics** | **RPM**, **RPD**, **TPM**, **TPD**, **IPM**, plus audio-minutes-per-minute for some streaming audio models. Limits bind on whichever is hit first | `[V]` |
| **Usage tiers** | Free (allowed geography, $100/mo cap); Tier 1 ($5 paid, $100/mo); Tier 2 ($50, $500); Tier 3 ($100, $1,000); Tier 4 ($250, $5,000); Tier 5 ($1,000, $200,000). At ~$1/month of usage the system sits in **Tier 1**, whose per-model RPM/TPM values are shown in account settings rather than the guide | `[V]` |
| **429 behaviour and headers** | 429 on breach, with `x-ratelimit-limit-requests`, `x-ratelimit-limit-tokens`, `x-ratelimit-remaining-requests`, `x-ratelimit-remaining-tokens`, `x-ratelimit-reset-requests`, `x-ratelimit-reset-tokens`, the `-project-` variants, and **`Retry-After`**. "Each official OpenAI SDK automatically retries eligible rate-limit errors and honors `Retry-After`" — custom clients must use exponential backoff with jitter, respecting `Retry-After` as a minimum | `[V]` |
| **Data retention / training use** | "data sent to the OpenAI API is not used to train or improve OpenAI models (unless you explicitly opt in)". **"abuse monitoring logs are generated for all API feature usage and retained for up to 30 days"** unless longer retention is legally required. Zero Data Retention exists but is "subject to prior approval by OpenAI and acceptance of additional requirements" | `[V]` |
| **Cost at our volumes** | 1.89M input + 0.47M output/month on `gpt-5.6-luna` = $0.38 + $0.56 = **$0.94/month**. Batch tier would halve it | `[D]` |
> **AMENDED BY STAGE-0-FREEZE (2026-08-25).** v0.2's “the 22:30 UTC pipeline has no latency pressure” is **wrong**: P0.3 §6.1 gives the
> pipeline an 18-minute budget and the `TIER3_LLM` stage a 600-second deadline. Batch
> turnaround is undocumented on every page retrieved, so **Batch may not be assumed for the
> live path** — carried as **M-10**. Batch remains available for **replay** once turnaround
> is verified. |
| **Sandbox** | No separate sandbox; tiering is the safety mechanism | `[U]` |
| **Adjusted data, corporate actions, tick/lot, partial fills, WebSocket** | Not applicable | — |

**F-8: `gpt-4o-mini`, the model `[CONST]` names as the fallback, is absent from the current pricing
catalogue.** It survives only in the transcription line-up. The nearest current equivalent by role
and price is **`gpt-5.6-luna`** ($0.20 / $1.20 per 1M). §6 proposes this as amendment A-1.

**The 30-day abuse-monitoring retention is the operative privacy fact**, and it is the reason
P0.1 `[DEFAULT-7]` is load-bearing rather than decorative: for 30 days, whatever we send is
retained by a third party. Since no NAV, cash, position, P&L or limit ever enters a prompt, what
is retained is a sanitised candidate thesis — recoverable strategy *style*, never portfolio state.

**Dies at 09:31.** No impact (22:30 UTC pipeline). As the *fallback*, its failure matters only
concurrently with DeepSeek's, in which case the gate fails closed as in §3.11.

---

### 3.13 Interactive Brokers — US backup broker

**Status in v0.1: NOT VERIFIED (403/404 on every URL). Status in v0.2: VERIFIED.** The
documentation moved from `interactivebrokers.com/campus/ibkr-api-page/*` (now 404) and
`interactivebrokers.github.io/cpwebapi` (now carries "This documentation is now deprecated") to
`interactivebrokers.com/docs/web-api/*` and `ibkrcampus.com/docs/web-api/*`, both of which serve
`.md` and publish an `llms.txt` index.

**Docs retrieved `[V]`:** `interactivebrokers.com/docs/web-api/v1/pacing-limitations`,
`ibkrcampus.com/docs/web-api/authentication/faq.md`, `…/authentication/sessions.md`,
`…/authentication/cpgw/limitations-of-the-client-portal-gateway.md`,
`…/authentication/paper.md`, `…/trading/orders/order-reply-messages.md`.

| Dimension | Finding | State |
|---|---|---|
| **What it requires** | A REST API reached either through a **locally-running Client Portal Gateway** or, for institutional clients, **OAuth** / a dedicated connection | `[V]` |
| **Session model** | Two layers: a read-only "session" (non-`/iserver` endpoints) and a **brokerage session** (trading, `/iserver`) | `[V]` |
| **Session lifetime** | Sessions "remain valid for up to 24 hours, resetting at midnight for New York, U.S.; Zug, Switzerland; or Hong Kong time"; and **"Daily maintenance of IBKR's servers could result in a disconnect earlier than the 24 hour period."** | `[V]` |
| **Idle timeout / keep-alive** | Sessions "timeout after approximately **6 minutes** without sending new requests"; **`/tickle` should be called "approximately every minute"**. Even with tickles, the 24-hour reset still terminates the session | `[V]` |
| **Gateway limitation — the disqualifier** | **"Users must log in through the browser on the same machine as Client Portal Gateway in order to authenticate"** and **"All API Endpoint calls must be made on the same machine where the Client Portal Gateway was authenticated."** Endpoints beginning `/gw/api`, `/oauth`, `/oauth2` are unsupported under the gateway | `[V]` |
| **Rate limits (pacing)** | **Global 10 requests/second**, with per-endpoint carve-outs including `/iserver/account/orders` 1 req/5s, `/iserver/account/trades` 1 req/5s, `/iserver/marketdata/snapshot` 10 req/s, `/iserver/marketdata/history` **5 concurrent requests**, `/iserver/scanner/params` 1 req/15 min, `/portfolio/accounts` 1 req/5s, `/sso/validate` 1 req/min, `/tickle` 1 req/s. Unlisted endpoints follow the global 10 req/s | `[V]` |
| **429 behaviour** | **"the API will return a '429 Too Many Requests' exception. Violator IP addresses are put in a penalty box for 15 minutes… Repeat violator IP addresses can be permanently blocked until the issue is resolved."** This is the harshest throttling regime in the phase: a retry storm costs 15 minutes of total blindness, and repeating it costs the account | `[V]` |
| **Order confirmation quirk** | Orders may return **reply messages** that "must be confirmed via a second request before order execution" — POST `{"confirmed":true}` to `/iserver/reply/{messageId}`. They are not rejections but "fat finger" precautions. `messageIds` can be suppressed for the remainder of the session. **An order-placing client that does not implement the reply loop will silently fail to transmit orders** | `[V]` |
| **Partial fills / statuses** | Order lifecycle endpoints exist (`/iserver/account/orders`, Monitoring Live Orders) but are pace-limited to **1 request per 5 seconds** — polling order state is therefore rate-constrained by design | `[V]` pacing / `[U]` status enumeration, §5 M-9 |
| **Idempotency** | A client order id (`cOID`) exists in the order payload; **its constraints were not retrieved** | `[U]` §5 M-9 |
| **Sandbox vs prod** | Paper is supported, but **"there is no toggle or slider to distinguish between paper and live account logins"** — "customers must use their specific Paper username to authenticate". **The environment is selected by which credential you type**, which is a footgun worth a config-level guard | `[V]` |
| **Cost** | "There are no additional fees associated with the use of Client Portal API… no minimum funding requirements", though "Funding may be required where clients wish to receive real time market data", and minimum commissions apply for dedicated connections. Commission schedule itself not retrieved | `[V]` / `[U]` |
| **ToS / automated access** | Permitted and documented; IBKR's own note: "Use of any API involves technology and operational risks… Users are strongly encouraged to test any application thoroughly in a simulated environment before deploying it in a live account" | `[V]` |
| **Adjusted data, corporate actions, tick/lot** | Not assessed — IBKR is scored as an execution backup only, and ADR-10 forbids it taking over open positions | — |

**Design consequence (F-12).** IBKR is now scored on evidence, and the evidence is that it is a
**poor fit for an unattended single-VM design**: browser login on the gateway host, a 24-hour hard
session reset in a named timezone, a ~6-minute idle timeout requiring a per-minute tickle, an
order-reply confirmation loop, and a punitive 15-minute IP penalty box. Every one of those is
manageable; together they are a second operational burden of the same shape as Zerodha's daily
login (F-4). **It remains the right US backup** under ADR-10's narrow definition — new entries
only, never position takeover — because ADR-14 caps new entries at 4/session and a missed session
is a safe outcome. It is not a candidate to replace Alpaca as primary.

**Dies at 09:31.** No impact — it is not in the live path. Its relevance is the inverse case: if
*Alpaca* dies, IBKR is only useful if its session was already authenticated, which under the
24-hour reset means someone logged in that morning. **A backup broker that requires a human login
after the primary has already failed is not a backup.** If IBKR is to serve, the daily gateway
login must be part of the normal morning routine, not a break-glass step — recorded as amendment
A-9.

---

## 4. Weighted decision matrix — primary and backup per capability

### 4.1 Scoring criteria

| Criterion | Weight | Rationale |
|---|---|---|
| **C1 Fitness** for the specific P0.1 requirement | **30%** | A cheap provider that cannot meet ADR-08's history requirement is worthless, not cheap |
| **C2 Verifiability** of its documentation | **20%** | This phase's own lesson. A provider whose limits we cannot read is one we cannot write a correct client for |
| **C3 Cost** against the programme's capital `[DEFAULT-1]` | **20%** | |
| **C4 Failure semantics** — how gracefully it degrades, per its "09:31" note | **15%** | |
| **C5 Legal / ToS clarity** for automated access and storage | **15%** | |

Scores are 1–5. An unverified capability scores **no points** rather than an assumed midpoint — a
provider is not credited for documentation we could not read. Three v0.1 scores move in v0.2
because the documentation was subsequently read: Massive C2 4→5 (adjustment, corporate actions and
point-in-time tickers all confirmed), Alpaca C2 4→5 (order lifecycle, adjustment and paper
semantics confirmed), IBKR from `UNVERIFIED` to a real score.

### 4.2 Contested capabilities

**Capability A — US historical daily bars, ≥ 10 years (ADR-08, §0.3 C-3)**

| Provider | C1 | C2 | C3 | C4 | C5 | **Weighted** | Note |
|---|---|---|---|---|---|---|---|
| **Massive Stocks Developer $79** | 5 | 5 | 4 | 4 | 3 | **4.35** | 10 years, `adjusted=false` available, full split/dividend history, point-in-time tickers |
| Finnhub All-In-One $3,500 | 5 | 4 | 1 | 3 | 2 | 3.25 | 30+ yrs and explicitly survivorship-bias free, at 44× the price |
| Alpaca Algo Trader Plus $99 | 2 | 5 | 3 | 4 | 3 | 3.25 | **7+ years fails the requirement (F-3)** |
| FMP Ultimate $99 | 3 | 4 | 3 | 3 | 2 | 3.05 | Full history, but prices are secondary to its fundamentals focus |

→ **Primary: Massive Stocks Developer ($79/mo). Backup: FMP Ultimate ($99/mo).**

**Capability B — US real-time 5-minute bars for held positions (ADR-13)**

| Provider | C1 | C2 | C3 | C4 | C5 | **Weighted** |
|---|---|---|---|---|---|---|
| **Alpaca Algo Trader Plus $99** | 5 | 5 | 3 | 4 | 3 | **4.15** |
| Massive Stocks Advanced $199 | 4 | 4 | 2 | 4 | 3 | 3.45 |
| Alpaca Free $0 | 1 | 5 | 5 | 3 | 3 | 3.20 |

→ **Primary: Alpaca Algo Trader Plus. Backup: Massive Advanced.**
The decisive argument is not price but **coherence**: the bar that trips a stop comes from the
venue that fills the resulting order, so stop logic and fill reality cannot diverge across vendors.
Alpaca Free scores 1 on fitness because IEX-only prices (F-2) would trigger stops on a tape we do
not trade against — worse than no stop, because it looks like it works.

**Capability C — US fundamentals (ADR-14: ≥ 4 reported quarters × 1,500 names)**

| Provider | C1 | C2 | C3 | C4 | C5 | **Weighted** |
|---|---|---|---|---|---|---|
| **SEC EDGAR XBRL (`data.sec.gov`)** | 3 | 5 | 5 | 4 | 5 | **4.25** |
| **FMP Premium $49** | 5 | 5 | 4 | 3 | 2 | **4.05** |
| Massive Advanced $199 (Financials & Ratios) | 4 | 3 | 2 | 4 | 3 | 3.25 |
| Finnhub Free | 2 | 5 | 5 | 3 | 2 | 3.35 |

→ **Primary: FMP Premium. Authoritative cross-check: SEC EDGAR XBRL.**
EDGAR scores highest overall — free, authoritative, legally unambiguous, genuinely point-in-time —
but scores 3 on fitness because it ships raw XBRL, and building the normalisation, restatement and
sector-mapping layer ADR-14's z-scores need is weeks of work FMP has already done. The right
architecture uses both, as `[RS §8]` asks: **FMP for breadth and convenience, EDGAR as the
authority when they disagree (rule N7).** A material discrepancy is a data-quality event under
`[CONST-6]`, never a tiebreak silently resolved toward the more convenient source. Note that
folding fundamentals into Massive would cost $199/mo (Advanced) or a $29 add-on and lose EDGAR's
authority, so single-vendor consolidation is not the saving it appears to be.

**Capability D — News (ADR-04)** *(revised in v0.2 — see F-6)*

| Provider | C1 | C2 | C3 | C4 | C5 | **Weighted** |
|---|---|---|---|---|---|---|
| **Alpaca news (Benzinga, bundled)** | 4 | 4 | 5 | 4 | 2 | **3.90** |
| NewsAPI.org Business $449 | 4 | 5 | 1 | 4 | 4 | 3.60 |
| Massive Benzinga add-on $99 | 4 | 3 | 2 | 4 | 3 | 3.25 |
| FMP news (bundled from Starter) | 2 | 3 | 5 | 3 | 2 | 2.95 |
| NewsAPI.org Developer $0 | 0 | 5 | 5 | 3 | 1 | 2.60 |

→ **Primary: Alpaca's Benzinga news, included in the data subscription. Backup: FMP news.**
v0.1 chose "bundled news" generically; v0.2 names the source, because the generic version was
partly false — Massive's Benzinga is a **$99/month add-on**, not an inclusion. Alpaca's is the same
publisher through a subscription already being paid. C5 scores 2 because the redistribution licence
was not retrievable (§5 M-8); since ADR-04 uses news only as internal LLM context and never
redisplays it, that risk is contained but not zero. The NewsAPI Developer tier scores **0 on
fitness** — non-commercial licence, 24-hour delay, localhost-only CORS — and is not an option at
any price.

**Capability E — LLM inference (ADR-13 Chain G)**

| Provider | C1 | C2 | C3 | C4 | C5 | **Weighted** |
|---|---|---|---|---|---|---|
| **DeepSeek `deepseek-v4-flash`** | 5 | 4 | 5 | 4 | 2 | **4.20** |
| OpenAI `gpt-5.6-luna` | 5 | 5 | 4 | 4 | 4 | **4.50** |

→ **Primary: DeepSeek `deepseek-v4-flash` per `[CONST]`. Backup: OpenAI `gpt-5.6-luna`.**
**Note the matrix now favours OpenAI**, entirely on C5: OpenAI publishes its retention terms
(no training by default; 30-day abuse-monitoring logs; ZDR on approval) and DeepSeek's terms could
not be retrieved (§5 M-7). Cost is irrelevant between them — $0.73 vs $0.94 per month — exactly as
Chain G predicted. **`[CONST]` names DeepSeek as primary and P0.2 does not overturn a Constitution
invariant**, so the selection stands and the evidence is escalated as amendment A-10. The tiebreak
that *does* apply: ADR-14's 22:30 UTC pipeline lands in DeepSeek's off-peak window, halving an
already trivial bill. Since failover carries no cost penalty, **the fallback should be exercised on
a schedule rather than kept as a cold path that has never run.**

**Capability F — India execution (ADR-11, post-activation)**

| Provider | C1 | C2 | C3 | C4 | C5 | **Weighted** |
|---|---|---|---|---|---|---|
| **Upstox** | 5 | 4 | — | 4 | 3 | see note |
| Zerodha Kite | 3 | 5 | 5 | 3 | 4 | see note |

Zerodha scores higher on verifiability, cost transparency (₹500/month all-in, historical and
WebSocket included) and ToS clarity (static-IP regime documented and dated). Upstox scores higher
on fitness because of the `extended_token` (F-5) — no daily re-auth on the data and monitoring
path — and its native Kill Switch and Static IP endpoints, which map directly onto `[CONST-9]`.
→ **Selection deferred. `[CONST-10]` names Zerodha; Zerodha remains primary, Upstox remains
backup**, and the evidence is escalated as amendment **A-4** for Owner decision under ADR-09 row 12.

**Capability G — US reference data and point-in-time universe (ADR-14, `[RS §13]`)** *(new in v0.2)*

| Provider | C1 | C2 | C3 | C4 | C5 | **Weighted** |
|---|---|---|---|---|---|---|
| **Massive `/v3/reference/tickers`** | 5 | 5 | 4 | 4 | 3 | **4.35** |
| SEC `company_tickers_exchange.json` | 2 | 5 | 5 | 4 | 5 | 3.95 |
| FMP profile / delisted-companies | 3 | 4 | 4 | 3 | 2 | 3.25 |

→ **Primary: Massive tickers. Backup: SEC company-ticker files.**
This capability did not exist in v0.1 because the field list had not been retrieved. It matters:
`active` + `date` + `delisted_utc` is the mechanism that makes ADR-14's point-in-time universe
membership reconstructible from a vendor rather than only from our own snapshots, and `cik` is the
free join to EDGAR. SEC's files score 2 on fitness only because they carry no security-type,
exchange-history or delisting-date semantics — and the SEC itself does "not guarantee accuracy or
scope".

**Capability H — US backup execution (ADR-10)** *(scored for the first time in v0.2)*

| Provider | C1 | C2 | C3 | C4 | C5 | **Weighted** |
|---|---|---|---|---|---|---|
| **Interactive Brokers Web API** | 3 | 5 | 4 | 2 | 4 | **3.60** |

→ **Backup: IBKR, conditional on amendment A-9.** C4 scores 2 — the worst failure-semantics score
in the document — because of the 24-hour session reset, the same-machine browser login and the
15-minute IP penalty box (F-12). A backup that needs a human login *after* the primary has failed
is not a backup; either the gateway login joins the daily routine or the backup is nominal.

### 4.3 Assembled stack and verified monthly cost

| Capability | Provider | Paper phase | Live phase |
|---|---|---|---|
| US execution | Alpaca Trading | $0 (paper) | $0 commission + pass-through fees |
| US 10-year daily history | Massive Stocks Developer | **$79** | **$79** |
| US real-time 5-min (held) | Alpaca Algo Trader Plus | — (deferred, `[DEFAULT-P9]`) | **$99** |
| US fundamentals | FMP Premium | **$49** | **$49** |
| US reference / point-in-time universe | Massive (same subscription) | $0 | $0 |
| Filings / insider | SEC EDGAR | $0 | $0 |
| Macro | FRED | $0 | $0 |
| News | Alpaca (Benzinga, bundled) | $0 | $0 |
| LLM | **OpenAI `gpt-5.6-luna`** (primary since AD-5); DeepSeek `deepseek-v4-flash` fallback | ~$1 | ~$1 |
| US backup execution | IBKR | $0 | $0 (market-data subscriptions extra) |
| **Total** | | **≈ $129/month** | **≈ $228/month** |

`[D]` from the `[V]` prices above. Three caveats: FMP's $49 is the **annually-billed personal**
rate (month-to-month is higher and was not captured); Massive's $79 is the **monthly-billed** rate
and annual billing saves 20% (≈ $63/mo equivalent); and **every retail plan here is individual-use
and non-professional (F-9)**, so this total is valid only while `[DEFAULT-P1]` holds.

**Against P0.1 assumption A14 ($30–200/mo):** the paper phase fits; **the live phase at ~$228
exceeds the band by ~14%.** Not a design breaker, but P0.3 must model the staged number.
**Resolved as AD-1 (2026-08-25):** A14 is replaced, not re-banded — the verified figures above
stand, and the **VM and off-VM backup lines remain unpriced (P0.3 Q-1, Q-2), so the total
infrastructure operating cost is marked INCOMPLETE** rather than estimated. This total is
**data and broker only**.

**Cost-staging recommendation.** Do not buy Alpaca Algo Trader Plus until real capital is at risk.
Through `[RS §12]` stages 1–4 (backtest, walk-forward, paper, shadow) the 15-minute-delayed Massive
feed is adequate, because ADR-14 computes signals on the prior session's completed daily bar and
freezes the order list overnight. **$99/month deferred to stage 5** saves roughly $1,200 over a
12-month validation period — which, against $1,000 of starting capital `[DEFAULT-1]`, is not a
rounding error. The counter-argument, and the reason this is a recommendation rather than a rule:
paper trading on the free tier runs on **IEX data** (F-13), so the paper stage never exercises the
SIP code path. **P3.x must therefore include a one-month paid-tier rehearsal before stage 5**, not
a cold switch on the day capital arrives.

---

## 5. UNVERIFIED — the explicit register

The issue requires "an explicit list of every doc URL that could not be verified". Both halves are
given: URLs that failed, and facts that no retrievable page publishes.

### 5.1 Documentation URLs that could not be retrieved

| # | URL | Result | Resolution |
|---|---|---|---|
| U1 | `docs.alpaca.markets/docs/rate-limit` | **404** | **Resolved** — `alpaca.markets/support/usage-limit-api-calls` carries the 200/min figure |
| U2 | `docs.alpaca.markets/docs/historical-stock-data` | **404** | **Resolved** — `docs.alpaca.markets/us/reference/stockbars.md` |
| U3 | `docs.alpaca.markets/docs/corporate-actions-1` | **404** | **Resolved** — `docs.alpaca.markets/us/docs/mandatory-corporate-actions.md` |
| U4 | `docs.alpaca.markets/docs/news-api` | **404** (v0.1) | **Resolved** — `…/us/docs/historical-news-data.md` and `…/us/reference/news-3.md` |
| U5 | `alpaca.markets/support/alpaca-data-plans` | **404** (v0.1) | **Resolved** — `alpaca.markets/data` carries the plan table |
| U6 | `interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/` and `/webapi-doc/` | **404 / 403** | **Resolved** — the docs moved to `interactivebrokers.com/docs/web-api/*` and `ibkrcampus.com/docs/web-api/*` |
| U7 | `interactivebrokers.github.io/cpwebapi/` | **200, deprecated** | Superseded; banner reads "This documentation is now deprecated" |
| U8 | `raw.githubusercontent.com/InteractiveBrokers/cpwebapi/main/README.md` | **404** | Superseded by U6's resolution |
| U9 | `interactivebrokers.com/docs/web-api/v1/pacing-limitations.md` | **403** to a plain fetcher | **Resolved** — same page retrieved with a JS-rendering scraper |
| U10 | `massive.com/docs/websocket/quickstart`, `massive.com/docs/rest/quickstart` | **200, content JS-gated** — only the section shell rendered | **Not resolved.** WebSocket auth, connection limits and reconnect semantics remain unknown (M-3) |
| U11 | `site.financialmodelingprep.com/developer/docs/pricing` | **403** to a plain fetcher | **Resolved** — retrieved with the renderer, including the licensing footer |
| U12 | `fred.stlouisfed.org/docs/api/api_key.html` | **403** | Partially resolved — `…/api/terms_of_use.html` retrieved instead; it confirms limits exist without a number |
| U13 | `cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html` | **DNS timeout** | **Not resolved.** DeepSeek's data-retention and training-use terms remain unknown (M-7) |
| U14 | `sec.gov/rules/final/2024/34-101070.pdf` (adopting release) | **403** to a plain fetcher | **Resolved by substitution** — the SEC's own small-entity compliance guide plus exemptive orders 34-104172 and 34-105656 were retrieved and carry the operative dates |
| U15 | `sec.gov/os/webmaster-faq` | **403** (v0.1) | Superseded — canonical page retrieved |
| U16 | `openai.com/api/pricing/` | **403** (v0.1) | Superseded — `developers.openai.com/api/docs/pricing` |

**Genuine remaining gaps: U10 and U13.** Everything else was resolved by finding the canonical
location, and the failed attempts are recorded so the audit trail of attempts is complete.

### 5.2 Facts that no retrievable documentation publishes

Each with the exact query needed to resolve it. **No value is guessed for any of these.**

| # | Missing fact | Provider(s) | How to resolve | Blocks |
|---|---|---|---|---|
| **M-1** | `client_order_id` **allowed charset**; the granular **order-reject reason enumeration**; **429 retry-header names** | Alpaca | Support ticket, or empirical probe in paper. Mitigated today by self-restricting to `[A-Za-z0-9-]` ≤ 64 and treating reject reasons as opaque text | P3.2 |
| ~~**M-2**~~ | ~~Whether price history for delisted names is retained~~ | Massive | **CLOSED 2026-08-26** `[V]`. Vendor KB: “our market data includes companies that have been delisted from the exchanges and is stored as it occurred on that date.” Source: `massive.com/knowledge-base/article/what-does-massive-do-with-delisted-tickers`. **No decision changes** — ADR-14’s rule that delisted names are never deleted and invariant I7 were already correct; they are now supportable by the vendor rather than at risk. An empirical spot-check at first backfill remains good practice, not a gate | — |
| **M-3** | WebSocket reconnect / replay semantics | Alpaca (Massive, Zerodha, Upstox still unretrieved) | **DOWNGRADED FROM GATING 2026-08-26** `[V]`. Two Alpaca streaming pages retrieved in full; **neither documents any replay, sequence number, resume token or gap-recovery mechanism**. A mechanism that is not documented cannot be depended on for correctness, so **rule N5 (gap-is-lost, reconcile from REST) is confirmed as the correct and sufficient design**. If vendor support later reveals an undocumented replay it can only ever be an **optimisation**, never a correctness dependency — which is why this no longer gates. Remaining `[U]`: the same semantics for Massive, Zerodha and Upstox | P2.1, P3.3 — **not gating** |
| **M-4** | **429 semantics not published**: the HTTP status on breach (Massive, FMP, Upstox, SEC), retry headers (all), and **FRED's numeric limit** | Massive, FMP, Upstox, SEC, FRED | Vendor support; for FRED, contact the St. Louis Fed as its docs invite. Until answered, **adaptive backoff, never a fixed budget** (rule N8) | P2.1 client design |
| **M-5** | **Is the news archive point-in-time?** | Benzinga via Alpaca and via Massive | **ANSWERED 2026-08-26, AND THE ANSWER IS NO** `[V]`. Both vendors expose a revision timestamp and **neither exposes any way to recover the prior text**. Massive/Benzinga: `last_updated` = “the timestamp … when the news article was **last updated in the system**” vs `published` = “when the news article was **originally published**”, and the vendor’s own sample record shows the two differing (`20:27:42Z` vs `20:27:41Z`). Alpaca: `created_at` = “Date article was created”, `updated_at` = “Date article was updated”. **`[D]` Neither API offers a version, revision, or as-of-content parameter — only time-range filtering on publication — so a historical query returns the article as currently stored, not as originally published.** Sources: `massive.com/docs/rest/partners/benzinga/news`, `docs.alpaca.markets/reference/news-3`. **Consequence: rule N4 is confirmed necessary and is now evidence-based; new rule N16 makes our own store the point-in-time record.** Residual unknown split out as **M-12** | **P5.1, P2.1** — answered; mitigation specified |
| **M-6** | **US settlement cycle** as applied; cash-account **good-faith / free-riding** treatment | Alpaca | Account agreement behind login (`AcctAppMarginAndCustAgmt.pdf` requires an account) plus a support ticket. ADR-13 Chain D specifies both counters, so either answer is implementable | P2.9 |
| **M-7** | **Data retention and training-use terms** | DeepSeek | The ToS host timed out (U13); retry, or obtain the terms from the platform console after signup. Material under `[CONST-4]` and `[DEFAULT-7]` | P4.3 / P6.2 |
| **M-8** | **EDGAR filing-availability latency** after acceptance; **Alpaca news redistribution licence** | SEC, Alpaca | SEC: dissemination cutoffs are documented, propagation latency is not — measure empirically over a week of Form 4s. Alpaca: support ticket for the Benzinga sub-licence terms | P2.1, ADR-04 |
| **M-11a** | ~~OpenAI auth mechanism~~ | OpenAI | **CLOSED 2026-08-26** `[V]` — bearer credential, exact header, org/project headers, secrecy and revocation wording now in §3.12. Source: `developers.openai.com/api/reference/overview`. **No decision changes**; consistent with the Vault line already in `[CONST]` | — |
| **M-11b** | **OpenAI Terms of Service on automated access, redistribution and storage** | OpenAI | **STILL OPEN.** The auth retrieval did not cover the ToS, and no value is assumed. Retrieve the API Terms of Service and the Usage Policies, and record the automated-access, redistribution and storage clauses. Note §3.12 already carries the **verified** data-governance facts (no training on API data absent opt-in; 30-day abuse-log retention), which is the half that AD-5 rests on | P6.2, P6.3 — **not gating** |
| **M-12** | **Materiality of Benzinga post-publication edits** — are they typo/formatting fixes, or substantive revisions and retractions that change meaning? | Benzinga via Alpaca | Vendor question to Benzinga, **plus** a measurement our own ingest can make once N16 is live: count records whose `updated_at` moves after first ingest, and diff the body. **This is the residual of M-5 and it is a materiality question, not a design question** — the design (N4 + N16) is already correct for either answer | P5.1 quality reporting — **not gating** |
| **M-9** | Broker detail gaps: **Upstox** cost, idempotency, partial-fill representation, rejection codes, tick/lot; **IBKR** `cOID` constraints, order-status enumeration, commission schedule; **Zerodha** SEBI retail-algo obligations stated only on the forum `[F]` | Upstox, IBKR, Zerodha | Vendor docs deeper in each tree, plus the NSE/SEBI circulars themselves rather than a forum paraphrase | ADR-11 activation gate; `[RS §12]` stage 6 |

**AS OF 2026-08-26 NONE OF M-2, M-3 OR M-5 STILL GATES STAGE 1.** M-2 is closed (delisted price history is retained). M-3 is answered by confirmed documentary silence, and rule N5 is the correct response either way. M-5 is answered — the archive is **not** point-in-time — and rules N4 and N16 are the mitigation. The original v0.3 reasoning is preserved below because it is why these three were prioritised for retrieval. Each concerned correctness rather than
convenience, and each is expensive to retrofit once P1.2's schema and P2.1's ingest are frozen.
v0.1 listed five such gates; **M-6 (settlement) and the former M-1 (adjustment semantics) are now
downgraded** — adjustment is fully resolved for both price vendors, and settlement has a
specified-either-way implementation in Chain D.

---

## 6. Conflicts with higher-priority material, and proposed amendments

> **DISPOSITION, 2026-08-25.** All twelve amendments below are dispositioned in
> [SPEC-P0.1-DECISIONS](SPEC-P0.1-DECISIONS.md) §0.5.2 and frozen by
> [STAGE-0-FREEZE.md](STAGE-0-FREEZE.md). **A-1, A-3, A-4, A-6, A-7, A-8, A-9, A-10, A-11 and
> A-12 are APPLIED; A-2 and A-5 needed no change.** The five requiring the Owner's authority
> — A-4, A-6, A-9, A-10 and (with P0.3's A-13) the walk-forward roll — were taken as **AD-1
> through AD-5**. Nothing in this section is still awaiting a decision.

P0.2 sits below the Constitution and below SPEC-P0.1 in precedence. Where evidence contradicts
them, this phase **reports and proposes**; it does not overturn.

| # | Conflict | Proposed resolution | Authority needed |
|---|---|---|---|
| **A-1** | `[CONST]` names **`GPT-4o-mini`** as the fallback LLM; it is absent from OpenAI's current catalogue (F-8) | Amend to **`gpt-5.6-luna`** — nearest current equivalent by role and price | ADR-09 row 12 (Owner) |
| **A-2** | `[CONST]` names **DeepSeek**; current model IDs are `deepseek-v4-flash` / `v4-pro` | **APPLIED.** Model IDs live in `config.llm.*`, never in the Constitution. Since **AD-5** DeepSeek is the **fallback**, so the key is `config.llm.fallback_model_id` | Closed |
| **A-3** | `[RS §8/§10]` and P0.1 reference **Polygon.io**; it is now **Massive** (F-1) | Rename downstream. Config records the brand host (`massive.com`) **and** the still-live API host (`api.polygon.io`) | None — cosmetic |
| **A-4** | `[CONST-10]` names **Zerodha Kite** for India. Upstox's `extended_token` (F-5) removes daily re-auth from the data and monitoring path, and it ships native Kill Switch and Static IP endpoints serving `[CONST-9]` | ~~Escalate; recommend the Owner consider Upstox as India primary~~ — **ESCALATION ANSWERED. Resolved as AD-4 (2026-08-25): Zerodha stays PRIMARY; Upstox is adopted only as the automated read-only monitoring/backup path; IBKR is manual-only emergency.** The Owner declined to promote Upstox: `extended_token` covers **read-only** endpoints while the order path still re-auths daily, and authentication convenience is not grounds for promotion | **CLOSED — Owner, AD-4** |
| **A-5** | P0.1 ADR-13 Chain A assumed a "retail data tier" without naming a vendor; F-2/F-3 show Alpaca cannot serve screening or backtest history | **No ADR amendment** — Chain A named a tier, not a vendor, and the tier is confirmed. §4 fills it with Massive + FMP | None |
| **A-6** | P0.1 **A14** put the retail data tier at **$30–200/mo**; the verified live stack is **~$228/mo** | ~~Amend A14 to **$130–230/mo, staged**~~ — **SUPERSEDED. Resolved as AD-1 (2026-08-25)**: P0.3 A-15 showed a flat band still omits the VM and off-VM backup lines, so A14 is replaced by **verified ≈$129/mo paper and ≈$228/mo live, plus two explicitly unpriced lines, with the total operating cost marked INCOMPLETE** rather than banded | **CLOSED — Owner, AD-1** |
| **A-7** | ADR-04 treated EDGAR as "minutes after filing" and did not account for dissemination cutoffs or index mutability (§3.8) | **Additive, not overturning:** adopt rules N1 and N2 as binding on P1.2, P2.1 and P5.1 | None — additive |
| **A-8** | ADR-04 selected FRED without addressing **macro data revisions** (§3.9) | **Additive:** adopt rule N3 — macro features read at decision-date vintage via ALFRED | None — additive |
| **A-9** | ADR-10 designates a US backup broker, but IBKR's session model (F-12) means the backup is unauthenticated at the moment it is needed | **Amend the runbook, not the ADR:** if IBKR is to serve as backup, the gateway login joins the **daily morning routine**; otherwise ADR-10 should state explicitly that the US backup is manual-only and not part of the RTO calculation | ADR-09 row 12 (Owner) |
| **A-10** | `[CONST]` names **DeepSeek** primary; on published data-governance terms alone, OpenAI scores higher (§4.2 Capability E) | **Escalate, do not action.** The gap is C5 only, and it closes the moment M-7 is resolved. Re-score when DeepSeek's terms are retrievable | ADR-09 row 12 (Owner) |
| **A-11** | P0.1 §6 marked **tick size** and **lot size / fractional** `[VERIFY-P0.2]` | **Resolved, and stronger than assumed:** US tick is **$0.01** today and becomes a **per-symbol, semi-annually reassigned** value from the first business day of **November 2027** (F-10). P1.1 must model tick size as a date-versioned instrument attribute, not a constant | None — additive |
| **A-12** | `[RS §12]`'s paper stage is treated as evidence about execution quality | **Correct the claim:** Alpaca paper uses IEX data, random 10% partial fills, no dividends and no fees (F-13). Paper proves plumbing; ADR-13 Chain F's ≥ 2× cost threshold must be validated on live fills (rule N11) | None — additive |

---

## 7. DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | **Massive Stocks Developer ($79/mo) is the primary source of 10-year US daily history and of point-in-time ticker reference data** | Only verified provider meeting ADR-08's ≥ 8-year and C-3's 10-year requirement at a sane price (F-3), and the only one exposing `active` + `date` + `delisted_utc` | Yes | **High** — a short or survivorship-biased history invalidates every promotion decision |
| 2 | **All Massive aggregate requests pass `adjusted=false`; all Alpaca bar requests rely on the `raw` default** | P0.1 `[DEFAULT-9]` stores raw plus a corporate-action table. Massive defaults to **adjusted**, so silence here is a bug | Yes | **High** — vendor-adjusted bars silently rewrite history on every split |
| 3 | **Alpaca's free data tier is rejected for screening** | IEX-only makes ADR-14's ADDV and close filters wrong, not noisy (F-2) | Yes | **High** if ignored — a silently wrong universe that looks correct |
| 4 | **Alpaca Algo Trader Plus ($99/mo) is the live 5-minute held-position feed, deferred to `[RS §12]` stage 5, with a one-month paid rehearsal before capital arrives** | Broker-native coherence between stop trigger and fill venue; ~$1,200 saved during validation; the rehearsal exists because paper runs on IEX and never exercises the SIP path | Yes | Medium |
| 5 | **FMP Premium ($49/mo) primary for fundamentals; SEC EDGAR XBRL is the authority on disagreement** | FMP has done the normalisation; EDGAR is authoritative, free and point-in-time | Yes | Medium |
| 6 | **No standalone news subscription. News comes from Alpaca's Benzinga feed; FMP is the fallback** | NewsAPI free is non-commercial + 24 h delayed + localhost-only; Business is $449/mo ≈ 3.5× the rest of the stack; **Massive's Benzinga is a $99/mo add-on, not an inclusion (F-6)** | Yes | Low |
| 7 | ~~DeepSeek primary; OpenAI fallback~~ — **REVERSED by AD-5 (2026-08-25): OpenAI `gpt-5.6-luna` is PRIMARY, DeepSeek `deepseek-v4-flash` is FALLBACK**, exercised on a schedule | v0.3 reasoning was that `[CONST]` names DeepSeek and P0.2 may not overturn it. The Owner then actioned escalation A-10 on published data-governance terms (§4.2 capability E). Cost remains irrelevant between them ($0.95 vs $0.73/mo); a cold fallback is still an untested fallback | **Yes — conditional on M-7** | Low |
| 8 | **Finnhub is a free supplementary source only, never a paid tier** | No middle tier: $0 → $3,500/mo (F-7) | Yes | Low |
| 9 | **IBKR is the US backup broker, scored on evidence, and is nominal unless its gateway login joins the daily routine (A-9)** | Session resets every 24 h at midnight in a named timezone and requires a same-machine browser login (F-12) | Yes | Low now; gates `[RS §12]` stage 6 |
| 10 | **EDGAR features are lagged to the dissemination date, never the filing date** | Documented 17:30 / 22:00 ET cutoffs create up to a full session of look-ahead (§3.8) | No | **High** — silent backtest inflation |
| 11 | **EDGAR index retrievals are snapshotted immutably** | Full and quarterly indexes rebuild weekly on Saturdays; history is mutable (§3.8) | No | **High** — irreproducible backtests |
| 12 | **Macro features are read at decision-date vintage via ALFRED, never at current value** | FRED series are revised; final values did not exist at the decision date (§3.9) | No | **High** — silent backtest inflation |
| 13 | **News features remain forward-validated only and may not enter walk-forward optimisation** | No vendor documents point-in-time archive integrity (M-5) | Yes | Medium |
| 14 | **WebSocket disconnect gaps are assumed lost; reconcile from REST on reconnect** | No provider documents backfill semantics (M-3); fail-closed per `[CONST-6]` | Yes | Medium |
| 15 | **Zerodha remains India primary despite Upstox's operational advantage** | `[CONST-10]` outranks P0.2. Escalated as A-4 and **confirmed by the Owner as AD-4 (2026-08-25)**: Upstox is the automated read-only monitoring backup, never primary | Partly — promoting Upstox needs a `[CONST-10]` amendment | Low today (India unfunded) |
| 16 | **US tick size is modelled as a date-versioned, per-symbol attribute — $0.01 today, reassignable from the first business day of November 2027** | SEC Rule 612 as amended, currently exempted by release 34-105656 (F-10) | Yes | Medium — a constant becomes a rounding bug on the changeover day |
| 17 | **Paper trading is accepted as evidence of plumbing only, never of fill quality or edge** | Alpaca paper: IEX data, random 10% partial fills, no dividends, no fees, no NBBO size validation (F-13) | No | **High** if ignored — a strategy promoted on paper economics is promoted on fiction |
| 18 | **The India order adapter implements client-side idempotency** | Zerodha publishes no idempotency key; `tag` is 20 alphanumeric characters and identifies without deduplicating (§3.6) | No | **High** — a retried order without dedupe is a duplicate position |
| 19 | **The client tracks a bandwidth budget alongside a rate limit for FMP** | FMP meters a trailing-30-day byte quota independently of call count (F-11) | Yes | Medium — a backfill silently exhausts the month |
| 20 | **The recommended stack is licensed on the basis that the operator is an individual non-professional subscriber trading own capital in own name** | Massive, FMP and Finnhub all restrict retail tiers this way (F-9) | Yes | **High commercially** — the data line reprices at three vendors simultaneously if this changes |

---

## 8. ASSUMPTIONS

Deliberately short. This phase's purpose was to *replace* assumptions with verified facts; what
remains unverified is in §5 as a named gap rather than an assumption carrying a guessed value.

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| B1 | `[DEFAULT-P1]` — the operator qualifies as a **non-professional subscriber** | Status is self-declared at signup and depends on facts about the person, not the API | Complete Massive's 11-question test honestly at signup; re-test on any change of circumstance | §4.3's entire price table is void; business pricing is unpublished for all three vendors |
| B2 | `[DEFAULT-P2]` — Massive Developer's 10-year history **includes delisted names' price bars** | Reference data is confirmed point-in-time; price-history retention is not stated (M-2) | Empirical probe against a known 2016 delisting | Survivorship bias re-enters at P5.1; would force Finnhub All-In-One ($3,500/mo) or a Capability-A rethink |
| B3 | `[DEFAULT-P6]` — Alpaca's Benzinga licence permits internal analytical use | The redistribution licence was not retrievable (M-8) | Support ticket to Alpaca for the Benzinga sub-licence terms | Fallback is FMP news, then no news — not NewsAPI at $449/mo |
| B4 | Token estimate of ~6,000 in / ~1,500 out per candidate thesis (inherited P0.1 A11) | No prompt exists yet | Instrument the first P4.3 call | Linear on §3.11's $0.73/mo — the conclusion survives a 10× error |
| B5 | `[DEFAULT-P9]` — 15-minute delayed data is adequate through `[RS §12]` stages 1–4 | ADR-14 computes on the prior session's completed bar and freezes the order list | Review at the stage-4 → 5 gate | Pulls $99/mo forward; does not change the design |
| B6 | IEX's share of consolidated volume is low enough to make IEX-only ADDV materially wrong | Not re-measured in this phase | Compare IEX vs consolidated ADDV on a sample | If IEX share were high, F-2 weakens — but Alpaca's own tiering implies the distinction is material |
| B7 | `[DEFAULT-P10]` — DeepSeek's terms do not claim training rights over API inputs in a way that matters, **given** that `[DEFAULT-7]` keeps portfolio state out of prompts | The ToS host timed out (M-7) | Retry `cdn.deepseek.com`, or read the terms in the platform console | What leaks is sanitised candidate reasoning — strategy style, never portfolio state. Would escalate A-10 from advisory to actionable |
| B8 | Tick size remains $0.01 through the build window | SEC exemptive relief runs to the first business day of November 2027, and the Chairman has directed a staff review "by the end of the year" that could change the increments again | Watch SEC releases; re-read Rule 612 status before any pricing-logic freeze | A constant tick becomes a rounding bug; mitigated in advance by decision 16 |

---

## 9. OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| 1 | Does Massive return **daily bars for delisted tickers** across the Developer tier's 10 years? | Empirical | `GET /v2/aggs/ticker/{delisted}/range/1/day/2015-01-01/2018-12-31?adjusted=false` for a ticker whose `delisted_utc` is known from `/v3/reference/tickers?date=2016-06-30` | **P5.1** |
| 2 | What are each stream's **reconnect and replay semantics**? | Vendor support (Alpaca, Massive, Zerodha, Upstox) | "On reconnect, does the stream replay messages missed during the disconnect, and is there a resume token or sequence number?" | P2.1, P3.3 |
| 3 | **FRED's numeric rate limit** | St. Louis Fed | Their docs invite contact: "If you have a reason that you need to exceed our limit, please contact us" — ask for the current limit and the status code returned | P2.1 |
| 4 | What **HTTP status** do Massive, FMP, Upstox and SEC return on rate-limit breach, and with which headers? | Vendor support | "Which status code and which response headers indicate throttling, and is `Retry-After` set?" | P2.1, P3.1 |
| 5 | Is the **Benzinga archive point-in-time**? | Benzinga via Alpaca | "Are articles ever edited, retracted or back-dated after publication, and does the historical archive return the original text and timestamp as published?" | **P5.1** |
| 6 | Alpaca **`client_order_id` charset**, granular **reject-reason** enumeration, and 429 retry headers | Alpaca support | "What characters are valid in `client_order_id`, is there an enumerated reject-reason list, and which headers accompany a 429?" | P3.2 |
| 7 | Alpaca **settlement and cash-account** treatment (T+1, good-faith violations, free-riding) | Account agreement + support | Read `AcctAppMarginAndCustAgmt.pdf` after account opening; ask how good-faith violations are counted on a cash account | P2.9 |
| 8 | **DeepSeek data retention and training-use terms** | DeepSeek | Retry `cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html`; otherwise the platform console | P4.3, P6.2 |
| 9 | **EDGAR propagation latency** between acceptance and index availability | Empirical | Poll `data.sec.gov` submissions for a set of Form 4 filers across one week and record acceptance→availability deltas | P2.1 |
| 10 | **Upstox** cost, idempotency, partial-fill fields, rejection codes, tick/lot; **IBKR** `cOID` constraints and order-status enumeration | Vendor docs | Deeper crawl of `upstox.com/developer/api-documentation/*` and `ibkrcampus.com/docs/web-api/trading/orders/*` | ADR-11 gate; `[RS §12]` stage 6 |
| 11 | Do the **SEBI/NSE retail-algo obligations** (exchange registration above an order-rate threshold; mandatory market protection) apply to a single-user API account as Zerodha's forum states? | NSE/SEBI circulars, not the forum | Read the NSE circular referenced by `[CONST-9]` (SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013) and the NSE operating-procedure circular directly | ADR-11 gate |
| 12 | Does the SEC's end-of-2026 review of Rules 610(c) and 612 change the increments again? | SEC | Watch for a release following the Chairman's 11 June 2026 direction to staff | P1.1 (advisory only — decision 16 already absorbs the change) |

**What blocks what:**

| Blocks | Items | Can Stage 1 proceed? |
|---|---|---|
| **P1.1 / P1.2 (domain, storage)** | Q12 (advisory) | **Yes** — adjustment semantics, tick size, lot size and reference-data fields are all now resolved |
| **P2.1 / P2.2 (ingest, scanner)** | Q2, Q3, Q4, Q9 | **Yes** — adaptive backoff replaces unknown limits; gap-is-lost replaces unknown WS semantics |
| **P2.9 (risk)** | Q7 | **Yes** — ADR-13 Chain D specifies both counters, so either answer is implementable |
| **P3.1 / P3.2 (broker, orders)** | Q6 | **Yes, with care** — the self-imposed `client_order_id` subset is safe; reject reasons are handled as opaque text with a fail-closed default |
| **P4.3 / P6.2 (LLM)** | Q8 | **Yes for prototyping, no for production** — production requires the data terms |
| **P5.1 (backtest)** | **Q1, Q5** | **No** — survivorship and news point-in-time integrity are `[RS §13]` hard requirements |
| **`[RS §12]` stage 6 (live capital)** | Q10, Q11, A-9 | **No** — backup broker and India regulatory obligations must be settled before real money scales |

**Nothing in this register blocks P0.3**, the immediate next phase: every input it needs — data
volumes (ADR-13 Chain B), throughput (ADR-14), LLM prices (§3.11–3.12) and stack cost (§4.3) — is
verified.

---

## 10. CONTRACTS EXPORTED

### 10.1 Enumerations

```python
# provider/enums.py — consumed by P2.1 (ingest), P3.1 (broker adapters), P0.3 (cost model)
from enum import StrEnum


class ProviderId(StrEnum):
    """Stable identity of an external provider. Persisted in audit rows; never renamed."""
    ALPACA_TRADING = "ALPACA_TRADING"
    ALPACA_DATA = "ALPACA_DATA"          # bars, streaming and Benzinga news share one subscription
    MASSIVE = "MASSIVE"                  # formerly POLYGON; api host remains api.polygon.io
    FMP = "FMP"
    FINNHUB = "FINNHUB"
    SEC_EDGAR = "SEC_EDGAR"
    FRED = "FRED"
    DEEPSEEK = "DEEPSEEK"
    OPENAI = "OPENAI"
    ZERODHA = "ZERODHA"
    UPSTOX = "UPSTOX"
    IBKR = "IBKR"


class DataCapability(StrEnum):
    US_EXECUTION = "US_EXECUTION"
    US_EXECUTION_BACKUP = "US_EXECUTION_BACKUP"
    US_DAILY_HISTORY = "US_DAILY_HISTORY"
    US_REALTIME_INTRADAY = "US_REALTIME_INTRADAY"
    US_REFERENCE_DATA = "US_REFERENCE_DATA"
    US_FUNDAMENTALS = "US_FUNDAMENTALS"
    NEWS = "NEWS"
    FILINGS = "FILINGS"
    MACRO = "MACRO"
    LLM = "LLM"
    IN_EXECUTION = "IN_EXECUTION"
    IN_MARKET_DATA = "IN_MARKET_DATA"


class ProviderRole(StrEnum):
    PRIMARY = "PRIMARY"
    BACKUP = "BACKUP"
    AUTHORITY = "AUTHORITY"              # wins on disagreement (EDGAR over FMP — rule N7)
    SUPPLEMENTARY = "SUPPLEMENTARY"
    NOMINAL = "NOMINAL"                  # designated but not usable without manual action (IBKR, A-9)


class TokenLifetime(StrEnum):
    """How a provider's credential expires. Drives the pre-flight check in every adapter."""
    NON_EXPIRING = "NON_EXPIRING"                    # Alpaca, Massive, FMP, Finnhub, FRED, LLMs
    DAILY_FIXED_LOCAL = "DAILY_FIXED_LOCAL"          # Zerodha 06:00 IST, Upstox 03:30 IST
    ROLLING_SESSION = "ROLLING_SESSION"              # IBKR: ~6 min idle, 24 h hard reset
    NONE_REQUIRED = "NONE_REQUIRED"                  # SEC EDGAR
```

### 10.2 Provider specification models

```python
# provider/spec.py — the registry every adapter is constructed from.
from datetime import time
from decimal import Decimal
from pydantic import BaseModel, Field, HttpUrl, model_validator

from provider.enums import DataCapability, ProviderId, ProviderRole, TokenLifetime


class RateLimit(BaseModel):
    """One rate-limit dimension. All windows are wall-clock; none is a token bucket refill rate.

    A violation means: the adapter must NOT issue the call. Exceeding a published limit is a
    defect, not a runtime condition to be discovered from a 429.
    """
    model_config = {"frozen": True}

    scope: str = Field(description="Endpoint group the limit applies to, e.g. 'orders', 'quote', 'global'.")
    per_second: int | None = Field(default=None, ge=1, description="Requests per second. None = not published.")
    per_minute: int | None = Field(default=None, ge=1, description="Requests per minute. None = not published.")
    per_day: int | None = Field(default=None, ge=1, description="Requests per calendar day, provider's timezone.")
    concurrent: int | None = Field(default=None, ge=1, description="Simultaneous in-flight requests (DeepSeek model).")
    bandwidth_bytes_30d: int | None = Field(default=None, ge=1, description="Trailing-30-day byte quota (FMP only).")
    published: bool = Field(description="False when the provider states a limit exists but gives no number (FRED).")
    breach_status: int | None = Field(default=None, ge=400, le=599,
                                      description="HTTP status on breach. None = not documented; treat any 4xx as throttling.")
    penalty_seconds: int | None = Field(default=None, ge=0,
                                        description="Enforced lockout after breach. IBKR = 900 (15-minute IP penalty box).")

    @model_validator(mode="after")
    def _at_least_one_dimension(self) -> "RateLimit":
        if self.published and not any((self.per_second, self.per_minute, self.per_day,
                                       self.concurrent, self.bandwidth_bytes_30d)):
            raise ValueError("published=True requires at least one numeric dimension")
        return self


class CredentialSpec(BaseModel):
    """How this provider's credential behaves. Checked before every session, not on 401."""
    model_config = {"frozen": True}

    lifetime: TokenLifetime
    expires_at_local: time | None = Field(default=None,
                                          description="Local wall-clock expiry for DAILY_FIXED_LOCAL. Zerodha 06:00, Upstox 03:30.")
    expiry_tz: str | None = Field(default=None, description="IANA tz for expires_at_local, e.g. 'Asia/Kolkata'.")
    idle_timeout_seconds: int | None = Field(default=None, ge=1,
                                             description="ROLLING_SESSION only. IBKR ≈ 360.")
    keepalive_seconds: int | None = Field(default=None, ge=1,
                                          description="Required keep-alive period. IBKR /tickle ≈ 60.")
    hard_reset_local: time | None = Field(default=None, description="ROLLING_SESSION hard reset. IBKR 00:00.")
    interactive_login_required: bool = Field(description="True when a human must complete a browser login. Zerodha, Upstox, IBKR-CPGW.")
    static_ip_required: bool = Field(description="True when the provider binds order placement to registered IPs. Zerodha from 2026-04-01.")
    supports_refresh: bool = Field(description="False for Zerodha (refresh_token is restricted to approved platforms).")


class IdempotencySpec(BaseModel):
    """Broker-side idempotency. Absence forces client-side dedupe (decision 18)."""
    model_config = {"frozen": True}

    supported: bool
    field_name: str | None = Field(default=None, description="'client_order_id' (Alpaca), 'tag' (Zerodha, identifies only).")
    max_length: int | None = Field(default=None, ge=1, description="Alpaca 128; Zerodha tag 20.")
    charset_regex: str = Field(default=r"^[A-Za-z0-9-]{1,64}$",
                               description="Charset WE will emit, not necessarily the vendor's full accepted set (M-1).")
    deduplicates: bool = Field(description="True only if the vendor documents that a repeat key is rejected, not merely recorded.")


class ProviderSpec(BaseModel):
    """One row of the provider registry. Immutable at runtime; changes are config commits."""
    model_config = {"frozen": True}

    provider_id: ProviderId
    capabilities: tuple[DataCapability, ...] = Field(min_length=1)
    role: dict[DataCapability, ProviderRole] = Field(description="Role per capability; a provider may be PRIMARY for one and BACKUP for another.")
    api_host: HttpUrl
    alt_host: HttpUrl | None = Field(default=None, description="Massive: api.polygon.io remains live alongside massive.com.")
    sandbox_host: HttpUrl | None = Field(default=None, description="None means no sandbox exists — testing happens in production.")
    credential: CredentialSpec
    limits: tuple[RateLimit, ...] = Field(min_length=1)
    idempotency: IdempotencySpec | None = Field(default=None, description="None for non-trading providers.")
    monthly_cost_usd: Decimal = Field(ge=0, decimal_places=2, description="Subscription only; per-transaction fees are modelled separately in P5.3.")
    licence_individual_use_only: bool = Field(description="True for Massive, FMP, Finnhub (F-9). Re-review on any change of who owns the capital.")
    stream_replays_on_reconnect: bool = Field(default=False,
                                              description="False everywhere as of 2026-08-24 (M-3). False means: reconcile from REST on reconnect (rule N5).")
```

### 10.3 SQL DDL — two tables this phase makes necessary

```sql
-- Consumed by P2.1 (ingest) and P0.3 (cost/capacity model).
-- Exists because FMP meters a trailing-30-day BYTE quota independently of call count (F-11),
-- and because several providers publish no 429 semantics (M-4), so we must never rely on
-- discovering the limit from the response.
CREATE TABLE provider_quota_usage (
    provider_id      TEXT        NOT NULL,          -- enum ProviderId
    scope            TEXT        NOT NULL,          -- matches RateLimit.scope
    window_start     TIMESTAMPTZ NOT NULL,          -- UTC, inclusive
    window_end       TIMESTAMPTZ NOT NULL,          -- UTC, exclusive
    request_count    BIGINT      NOT NULL DEFAULT 0 CHECK (request_count >= 0),
    response_bytes   BIGINT      NOT NULL DEFAULT 0 CHECK (response_bytes >= 0),
    throttled_count  BIGINT      NOT NULL DEFAULT 0 CHECK (throttled_count >= 0),  -- 429s or equivalent
    PRIMARY KEY (provider_id, scope, window_start),
    CHECK (window_end > window_start)
);
-- Violation semantics: a request that would push request_count or response_bytes past the
-- registry's published limit is REFUSED locally and logged. Fail-closed (CONST-6): we do not
-- send it and hope for a 429.

-- Consumed by P1.1 (instrument model) and P3.2 (order price rounding).
-- Exists because the US minimum pricing increment is a REGIME, not a constant (F-10):
-- $0.01 today; from the first business day of November 2027 it becomes $0.005 or $0.01 per
-- symbol, reassigned twice a year from a Time Weighted Average Quoted Spread evaluation.
CREATE TABLE tick_size_regime (
    market           TEXT        NOT NULL,          -- 'US' | 'IN'
    symbol           TEXT        NOT NULL,          -- '*' means "all symbols in this market"
    effective_from   DATE        NOT NULL,          -- exchange-local trading date, inclusive
    effective_to     DATE,                          -- exchange-local, exclusive; NULL = open-ended
    tick_size        NUMERIC(12,6) NOT NULL CHECK (tick_size > 0),   -- price units, e.g. 0.010000
    min_price        NUMERIC(12,6) NOT NULL DEFAULT 0 CHECK (min_price >= 0),  -- regime applies at or above this price
    source           TEXT        NOT NULL,          -- e.g. 'SEC Rule 612 / release 34-105656'
    PRIMARY KEY (market, symbol, effective_from),
    CHECK (effective_to IS NULL OR effective_to > effective_from)
);
-- Seed rows (verified 2026-08-24):
--   ('US', '*', <first trading_date of the ingested history window>, NULL, 0.010000, 1.000000,
--    'SEC Rule 612; $0.005 increment exempted until the first business day of November 2027 per
--     release 34-105656')
-- effective_from is seeded from the project's own history window, NOT from a historical
-- decimalisation date: this phase did not verify when the $0.01 increment first took effect, and
-- the 10-year window lies entirely inside it.
-- Violation semantics: an order whose limit_price is not an exact multiple of the tick in force
-- on its trading_date is REJECTED locally before submission, never rounded silently.
```

### 10.4 Verified limits — bind these in the client layer

| Key | Value | State |
|---|---|---|
| `provider.alpaca_trading.rate_limit_per_min` | **200**, per **account** (not per key) | `[V]` |
| `provider.alpaca_trading.breach_status` | **429** | `[V]` |
| `provider.alpaca_trading.client_order_id_max_len` | **128** (we emit ≤ 64, `[A-Za-z0-9-]`) | `[V]` / self-imposed |
| `provider.alpaca_trading.paper_base_url` | `https://paper-api.alpaca.markets` | `[V]` |
| `provider.alpaca_data.bars.adjustment_default` | **`raw`** — values `raw`,`split`,`dividend`,`spin-off`,`all` | `[V]` |
| `provider.alpaca_data.bars.limit_max` | **10,000**, counted across all symbols in the request | `[V]` |
| `provider.alpaca_data.free.exchanges` | `IEX` only — **rejected for screening** | `[V]` |
| `provider.alpaca_data.free.ws_symbol_limit` | **30** | `[V]` |
| `provider.alpaca_data.ws_connection_limit` | **1** for most subscriptions — the monitor is a singleton | `[V]` |
| `provider.alpaca_data.history_years` | **7** — **insufficient for backtest** | `[V]` |
| `provider.alpaca_data.news.limit_max` | **50** per page; source Benzinga; history from **2015** | `[V]` |
| `provider.massive.aggregates.adjusted_param` | **must be sent as `false`** (vendor default is `true`) | `[V]` |
| `provider.massive.aggregates.limit_max` | **50,000** | `[V]` |
| `provider.massive.basic.rate_limit_per_min` | **5** | `[V]` |
| `provider.massive.developer.history_years` | **10** | `[V]` |
| `provider.massive.splits.history_from` | **1978-10-25** (Starter+) | `[V]` |
| `provider.massive.dividends.history_from` | **2000-01-15** (Starter+) | `[V]` |
| `provider.massive.tickers.history_from` | **2003-09-10** (tier-dependent) | `[V]` |
| `provider.massive.api_host` / `alt_host` | `massive.com` / `api.polygon.io` | `[V]` |
| `provider.fmp.premium.rate_limit_per_min` | **750** | `[V]` |
| `provider.fmp.premium.bandwidth_bytes_30d` | **50 GB** | `[V]` |
| `provider.fmp.premium.history_years` | **30+** | `[V]` |
| `provider.finnhub.free.rate_limit_per_min` | **60**; WebSocket **50 symbols** | `[V]` |
| `provider.finnhub.global_rate_limit_per_sec` | **30** — applies on top of every plan limit | `[V]` |
| `provider.finnhub.breach_status` | **429** | `[V]` |
| `provider.sec_edgar.rate_limit_per_sec` | **10** | `[V]` |
| `provider.sec_edgar.user_agent_required` | `true` — `"<Company> <admin@domain>"` | `[V]` |
| `provider.sec_edgar.dissemination_cutoff_et` | `17:30`; `22:00` for Forms 3/4/5 | `[V]` |
| `provider.fred.rate_limit` | **UNKNOWN — adaptive backoff on `429` and `423`** | `[U]` M-4 |
| `provider.fred.attribution_required` | `true` — exact notice text in §3.9 | `[V]` |
| `provider.zerodha.rate_limit.quote_per_sec` | **1** (batch: 500 instruments/call) | `[V]` |
| `provider.zerodha.rate_limit.historical_per_sec` | **3** | `[V]` |
| `provider.zerodha.rate_limit.orders_per_sec` | **10**; **400/min**; **5,000/day** | `[V]` |
| `provider.zerodha.max_modifications_per_order` | **25** | `[V]` |
| `provider.zerodha.token_expiry_local` | **06:00 Asia/Kolkata, next day** — not refreshable | `[V]` |
| `provider.zerodha.static_ip_required_from` | **2026-04-01**, order placement only, max **2** IPs | `[V]` |
| `provider.zerodha.tag_max_len` / `charset` | **20** / alphanumeric | `[V]` |
| `provider.zerodha.ws_connections` / `instruments_per_conn` | **3** / **3,000** | `[V]` |
| `provider.zerodha.monthly_cost_inr` | **500** per API key, historical + WebSocket included | `[V]` |
| `provider.upstox.token_expiry_local` | **03:30 Asia/Kolkata, next day**; `extended_token` for read-only | `[V]` |
| `provider.upstox.rate_limit.orders` | **10/s, 500/min, 2,000/30min** (50/s for SEBI-registered algos) | `[V]` |
| `provider.upstox.rate_limit.standard` | **50/s, 500/min, 2,000/30min** | `[V]` |
| `provider.ibkr.rate_limit.global_per_sec` | **10** | `[V]` |
| `provider.ibkr.breach_status` / `penalty_seconds` | **429** / **900** (15-minute IP penalty box) | `[V]` |
| `provider.ibkr.session.idle_timeout_sec` / `keepalive_sec` | **≈360** / **≈60** (`/tickle`) | `[V]` |
| `provider.ibkr.session.hard_reset` | **24 h, at midnight NY / Zug / HK** | `[V]` |
| `provider.deepseek.fallback_model_id` | `deepseek-v4-flash` — **fallback since AD-5** (was primary) | `[V]` |
| `provider.deepseek.concurrency_limit` | **2,500** (flash) / **500** (pro); breach **429** | `[V]` |
| `provider.deepseek.offpeak_utc` | all hours except Mon–Fri `01:00–04:00` and `06:00–10:00` | `[V]` |
| `provider.deepseek.idle_close_seconds` | **600** — connection closed if inference has not started | `[V]` |
| `provider.openai.primary_model_id` | `gpt-5.6-luna` — **primary since AD-5** (was fallback); closes A-1 | `[V]` |
| `provider.openai.live_path_tier` | `STANDARD` — **never `BATCH`** until M-10 closes | AD-5 |
| `provider.openai.retry_header` | `Retry-After` + `x-ratelimit-*`; honour as a minimum | `[V]` |
| `provider.openai.abuse_log_retention_days` | **30** | `[V]` |
| `market.us.tick_size` | **0.01** for NMS stocks ≥ $1.00; regime table per §10.3 | `[V]` |
| `market.us.tick_size.next_regime_earliest` | **first business day of November 2027** | `[V]` |

### 10.5 Binding correctness rules discovered in this phase

| # | Rule | Enforced in |
|---|---|---|
| **N1** | EDGAR-derived features are lagged to the **dissemination date**, never the filing date | P2.1, P5.1 |
| **N2** | EDGAR index retrievals are **snapshotted immutably**; never re-derived after a Saturday rebuild | P1.2, P2.1 |
| **N3** | Macro features are read at **decision-date vintage** (ALFRED / `series/vintagedates`) | P2.x, P5.1 |
| **N4** | News features are **forward-validated only**; excluded from walk-forward optimisation | P5.1, P5.2 |
| **N5** | A WebSocket disconnect gap is **assumed lost**; reconcile the affected window from REST before resuming | P2.1, P3.3 |
| **N6** | Screening must never run on single-venue (IEX) prices | P2.2 |
| **N7** | Where FMP and EDGAR disagree materially, **EDGAR is authoritative** and the discrepancy is a data-quality event, never a silent tiebreak | P2.1 |
| **N8** | The FRED client uses **adaptive backoff**, never a fixed request budget | P2.1 |
| **N9** | Every Massive aggregate request sends **`adjusted=false`**; adjustment is computed on read from the splits and dividends tables | P2.1 |
| **N10** | Tick size is resolved from `tick_size_regime` **by trading date and symbol**; an order price that is not an exact multiple is rejected locally, never rounded silently | P1.1, P3.2 |
| **N11** | Paper-trading results are **plumbing evidence only**. No slippage, fill-quality, fee or edge conclusion may cite paper data | P5.3, `[RS §12]` gates |
| **N12** | Brokers without a documented idempotency key (Zerodha, and Upstox until M-9 closes) get **client-side dedupe**: a persisted intent row written before the call and reconciled against the order book after it | P3.2, P3.4 |
| **N13** | A broker-initiated cancellation of a protective stop — Alpaca cancels open GTC orders ahead of mandatory corporate actions — is a **CRITICAL event** that must re-place the stop, not a silent state change discovered at the next reconciliation | P3.3, P2.9 |
| **N14** | All vendor news, filing and social text is **untrusted DATA** through the `[CONST-4]` sanitiser before any LLM sees it. Alpaca's news `content` "might contain HTML", which is exactly the shape an injection arrives in | P4.2, P4.3 |
| **N15** | Retail data licences are **individual-use and non-professional**. Any change in who owns the capital, or any public display of vendor data, re-triggers a licensing review before the change ships | P6.3, P0.3 |
| **N16** | **The vendor news archive is not point-in-time (M-5), so our store must be.** News ingest **snapshots `headline` and `body` at first receipt**, persists the vendor revision timestamp (`updated_at` / `last_updated`), and on any later change **writes a new revision row rather than overwriting**. A backtest reads the **first-seen** revision as of the decision date, never the current one. Corollary, and it is the load-bearing half: **historical news backfill is structurally unsound for any content-derived feature** — only forward-collected news is point-in-time, which is exactly why N4 excludes news from walk-forward optimisation | **P2.1, P1.2, P5.1** |

---

## 11. Acceptance self-check

| Acceptance criterion (from the issue) | Result | Verification |
|---|---|---|
| **Every provider has a completed fact sheet** | **PASS — 12 of 12** | §3.1–§3.13 covers Alpaca (trading and data as separate sheets), IBKR, Zerodha, Upstox, Massive, Finnhub, FMP, SEC EDGAR, FRED, a news API, DeepSeek and OpenAI. **IBKR, empty in v0.1, is now fully populated** from the relocated documentation |
| **Weighted decision matrix yielding a primary and a backup per capability** | **PASS** | §4.1 defines five weighted criteria; §4.2 scores **eight** capabilities (v0.1 scored six — reference data and US backup execution are new). Every capability has a named primary and backup, except India execution, which is explicitly deferred to Owner authority (A-4) |
| **A "what breaks if this provider dies at 09:31" note per provider** | **PASS** | Present in all 13 sheets, each tracing the concrete failure path and the ADR-10 / `[CONST-6]` response. The IBKR note surfaces the finding that a backup requiring a post-failure human login is not a backup (A-9) |
| **An explicit list of every doc URL that could not be verified. No guessed rate limits** | **PASS** | §5.1 lists **16 URLs** with exact failure codes and their resolution; only **U10 and U13** remain genuinely unresolved. §5.2 lists 9 missing facts. **FRED remains the test case: the widely-circulated "120/min" figure appears nowhere in FRED's own documentation and is therefore recorded nowhere in this document** |
| **Detail level: auth/token lifetime, rate limits with 429, WS reconnect/backfill, adjusted vs unadjusted, corporate actions, survivorship, tick/lot, idempotency + charset, partial fills, rejection codes, sandbox vs prod, cost, ToS** | **PASS with 9 named gaps** | Every dimension is addressed per provider, including the ones v0.1 left blank: Alpaca's full status and event lists, `adjustment`/`asof`, paper-vs-live behaviour, the fee schedule; Massive's `adjusted` default, splits/dividends schemas and point-in-time tickers; Zerodha's `tag`, partial-fill fields and static-IP regime; Upstox's rate-limit table and token lifetimes; IBKR's pacing, sessions and order-reply loop. Where a vendor does not publish a fact, the row reads `[U]` and appears in §5.2 rather than carrying an invented value |
| **Block C: blocking questions with defaults, then proceed** | **PASS** | §0.5 lists 10 blocking questions with options, the default applied and what breaks. All are tagged `[DEFAULT-Pn]` and repeated in §8. **v0.1 omitted this section entirely** |
| **Block C: non-blocking details resolved** | **PASS** | §0.6 resolves 21 of them, including the two vendors' opposite `adjusted` defaults, split-ratio direction, which dividend date to use, fee rounding direction and bar-timestamp semantics |
| **Block B: four mandatory tables** | **PASS** | §7 DECISIONS MADE (20), §8 ASSUMPTIONS (8), §9 OPEN QUESTIONS (12), §10 CONTRACTS EXPORTED |
| **Block B: every entity gets a Pydantic v2 model or SQL DDL; no prose-only types** | **PASS** | §10.1 enums, §10.2 four Pydantic v2 models with units, ranges and violation semantics, §10.3 two SQL DDL blocks with CHECK constraints and stated violation behaviour |

---

**END OF SPEC-P0.2-PROVIDERS v0.2**
