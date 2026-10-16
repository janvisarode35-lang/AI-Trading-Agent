---
id: SPEC-P2N.13-FAST-FEEDS
version: 0.1
status: DRAFT
phase: P2N.13 — Licensed low-latency feeds
depends_on: [SPEC-P0.2-PROVIDERS v1.x (FROZEN), SPEC-P0.3-BUDGET (FROZEN), SPEC-P0.1-DECISIONS ADR-04/ADR-13/ADR-14 (FROZEN), SPEC-P2.1-INGEST v0.10 (DRAFT)]
produces: [LATENCY-LADDER-P2N13, FAST-FEED-REGISTRY, COVERAGE-VS-LATENCY-SPLIT, FLEET-DESCOPE-RECOMMENDATION, VENDOR-FACTS-P2N13]
---

# SPEC-P2N.13 — Licensed low-latency feeds

Evidence discipline follows `SPEC-P0.2-PROVIDERS`: every factual claim is `[V]` with a primary
source, or `[U]` with the exact page to check. No rate limit, price or latency figure is guessed.

Research performed 2026-10-16. Arithmetic in §3 and §6 is derived from the frozen ADR-13/ADR-14
parameters and is reproducible from the figures stated.

---

## 1. Blocking questions and the defaults used

| # | Question | Default used | Breaks if wrong |
|---|---|---|---|
| 1 | Is the universe for this analysis ADR-14's 1,500 US / 500 IN? | Yes `[DEFAULT-1]` | A wider universe increases the crawl's incremental coverage |
| 2 | Is the relevant latency target the exit path (P0.3 §565, ≤5 s) rather than entry? | Yes `[DEFAULT-2]` — ADR-13 permits intraday exits only | If entries become event-driven the ladder is unchanged but the budget case changes |
| 3 | Does "news" include regulatory filings? | Yes — they are the highest-value class `[DEFAULT-3]` | — |
| 4 | Is paper-trading use of a vendor feed permitted? | **Assumed NO for TrueData** — see F-3, a blocker-class finding | The validation pipeline cannot use that feed |

---

## 2. Vendor facts

### 2.1 United States

**Benzinga direct — Stock Market Newswire** `[V]` <https://www.benzinga.com/apis/cloud-product/stock-news-api/> (retrieved 2026-10-16)

| Attribute | Value | Ev |
|---|---|---|
| Volume | **130–160 full-length articles/day**, plus **600–900 real-time headlines/day** marketed for "day trading and algorithmic trading" | `[V]` |
| Delivery | **REST (pull), TCP (push), RSS** — "delivered by API (pull) or TCP (push)" | `[V]` |
| Latency | "not delayed and is offered via different delivery mechanisms to ensure minimal latency" — **no figure published** | `[V]` claim / `[U]` number |
| History | **from 2010** | `[V]` |
| Coverage | US equities and macro; "the Wilshire 5000, the TSX, and 1000 other popular tickers" | `[V]` |
| Format | XML, JSON; timezone EST | `[V]` |
| Price | **not published** | `[U]` — contact sales; a non-primary forum mention of ~$300/mo is not evidence |
| Docs | <https://docs.benzinga.io/benzinga/newsfeed-v2.html> | `[V]` |

> **F-1 — a correction to `SPEC-P0.2`.** P0.2 §355 records Alpaca's bundled Benzinga feed as
> "130+ news articles per day", back to 2015. Benzinga's own page states **from 2010** and, more
> importantly, **600–900 real-time headlines/day in addition to the 130–160 articles**. The
> headline feed is roughly **5× the article count** and is the product Benzinga markets to
> algorithmic users. Whether Alpaca's bundle includes the headline stream or only the articles is
> **not established** — `[U]`, and it materially changes the coverage case in §4.

**RTPR — real-time press releases** `[V as vendor claim]` <https://rtpr.io/rtpr-vs-benzinga-pro>

| Attribute | Value | Ev |
|---|---|---|
| Latency | **sub-500 ms** from the source wire release — vendor's own claim | `[V]` claim |
| Delivery | REST **and WebSocket**, plus keyword/ticker alerts | `[V]` |
| Price | **$139/month**, 1-week trial | `[V]` |
| Scope | source wire press releases | `[V]` |
| Licence for machine use | **not established** | `[U]` |

**SEC EDGAR** — carried forward from `SPEC-P0.2` Q5, unchanged: **10 requests/second**, declared
User-Agent required `[V]`; dissemination cutoffs 17:30 ET and 22:00 ET for Forms 3/4/5 `[V]`;
**propagation latency after acceptance is not published** `[U]`; full/quarterly indexes rebuilt
weekly early Saturday `[V]`.

### 2.2 India — the significant finding

**TrueData — Corporate Announcements API** `[V]` <https://www.truedata.in/products/marketdataapi>
(retrieved 2026-10-16)

| Attribute | Value | Ev |
|---|---|---|
| Scope | **Real-time exchange filings from NSE & BSE**, parsed and structured | `[V]` |
| **Latency** | **< 200 ms** — stated on the product page as `LATENCY < 200MS` | `[V]` **published figure** |
| Delivery | **REST polling and WebSocket** | `[V]` |
| Positioning | "corporate disclosures in real-time the instant they hit the stock exchange terminals" | `[V]` |
| Categories | Financial results (with the **original exchange-filed PDF URL**); board meetings, dividends, bonus, splits; orders, contracts, JVs, MoUs; **SAST disclosures, promoter pledge changes, insider filings** | `[V]` |
| Payload | `id`, `trade_date`, `scrip_code`, `symbol_nse`, `symbol_bse`, `company_name`, `news_headline`, `news_body`, `announcement_type`, `meeting_type`, **`critical`** flag | `[V]` |
| Price | **not published on this page** | `[U]` — <https://www.truedata.in/price> |

**TrueData — Live Market News API** (marked NEW) `[V]`: WebSockets/webhooks, "delivered in
**sub-second JSON packets for event-driven algorithmic trading**", ticker-tagged to NSE/BSE
symbols, sector classification, ML sentiment, sourced from "verified financial media sources, wire
services, and macroeconomic press releases" `[V]`. Price `[U]`.

**Bonus finding relevant to OPT.2 (#59):** the same vendor publishes a **Live Option Chain API**
and a **Realtime Option Greeks API** (IV, delta, theta, vega, gamma "+16 matrices") for NSE F&O
`[V]`. That is a direct input to #59 and should be carried there.

**Other India candidates, unverified:** MarketMaker.in (named on Zerodha's own forum as offering a
realtime NSE+BSE corporate announcement API over websocket and REST) `[U]`; stockinsights.ai
announcements tagged feed `[U]`; NSE's own paid real-time data subscription, which the page
describes as **CSV at specified intervals** — i.e. likely not a low-latency push product for
announcements `[U]`.

### 2.3 F-3 — BLOCKER-CLASS LICENCE FINDING

TrueData's published terms `[V]`, verbatim on the same page:

- "Data is licensed solely for **Personal / Proprietary Algo Trading**, Charting, and Analysis use
  of a single Subscriber." — **our use case is explicitly permitted.** Good.
- "TrueData **does not provide market data for any kind of Gaming / Virtual trading / Simulation
  usage**, as per NSE & SEBI guidelines." — **this collides with the validation pipeline.**
- Redistribution, commercial display or enterprise-wide access requires prior exchange approval.
- "The Subscriber must ensure that the information provided **terminates at his / her end**."

The simulation clause is not a detail. `master-research-summary.md` §12 and issue #35 require a
**7-stage pipeline: backtest → walk-forward → 3–6 months paper trading → shadow mode** before live
capital. Paper trading and shadow mode are, on a plain reading, "virtual trading / simulation".
If that reading is correct, this feed **cannot lawfully be used for the paper and shadow stages**,
which is where it would otherwise be proven. Escalated as OQ-3; it needs a written answer from the
vendor before any commitment, and the same question must be put to every India vendor.

---

## 3. The latency ladder

The deliverable of this phase. Ranked by time from event to our possession.

| # | Path | Mechanism | To our possession | Evidence |
|---|---|---|---|---|
| 1 | **TrueData corporate announcements (IN)** | WebSocket push | **< 200 ms** | `[V]` vendor published |
| 2 | **RTPR press releases (US)** | WebSocket push | **< 500 ms** claimed | `[V]` vendor claim |
| 3 | **TrueData news API (IN)** | WebSocket / webhook | "sub-second" claimed | `[V]` vendor claim |
| 4 | **Benzinga direct (US)** | **TCP push** | "not delayed"; no figure | `[V]` mechanism / `[U]` number |
| 5 | Alpaca bundled Benzinga (US) | REST poll, **max 50/page** | poll interval + vendor hop | `[V]` mechanism / `[U]` number |
| 6 | SEC EDGAR | REST poll ≤10 req/s | propagation unpublished | `[V]` limit / `[U]` latency |
| 7 | Publisher RSS, conditional GET | poll | poll interval, minutes | structural |
| 8 | **Open-web crawl (#46–#52)** | poll 10,000 domains | **~7 s detect, ~13 s body** | derived, §3.1 |

### 3.1 The crawl's real detection latency — computed fairly

Earlier framing on #37 implied the crawl would be "minutes to hours". **That was wrong and is
corrected here.** Done properly — half the fetch budget on listing-page discovery, half on
article bodies, politeness capped at 0.3 req/s per domain:

| Domains | req/s available per domain | Politeness-bound? | Discovery interval | Detect + fetch |
|---|---|---|---|---|
| 1,000 | 3.00 | **yes, capped to 0.3** | 6.7 s | 13.3 s |
| 10,000 | 0.30 | no — exactly at the cap | 6.7 s | 13.3 s |
| 30,000 | 0.10 | no | 20.0 s | 40.0 s |

So a well-engineered 10,000-domain fleet detects a new article in **~7 s** and holds its body in
**~13 s**. That is genuinely usable at a swing horizon. It is also:

- **66× slower** than TrueData's published 200 ms
- **27× slower** than RTPR's claimed 500 ms
- **13× slower** than TrueData's sub-second news claim

And the budget is **exclusive**: below ~10,000 domains the politeness cap means the fleet cannot
reach 3,000 req/s at all (1,000 domains × 0.3 = 300 req/s maximum). Narrow-and-fast and
broad-and-slow are the same budget spent differently.

---

## 4. Coverage versus latency

| Event class | Covered by a licensed feed? | Needs the crawl? |
|---|---|---|
| Indian exchange filings — results, board meetings, dividends, splits, orders, SAST, pledge | **Yes, authoritatively** — TrueData, direct from exchange terminals, with the filed PDF | No |
| US regulatory filings | **Yes** — EDGAR is the authority | No |
| US wire press releases | **Yes** — RTPR / Benzinga | No |
| US market-moving news on Wilshire 5000 + TSX + 1,000 tickers | **Yes** — Benzinga, in-house originated | No |
| Macro releases, both markets | **Yes** — Benzinga macro, TrueData economic calendar | No |
| Small/micro-cap local or regional-language press not carried by a wire | No | **Yes** |
| Trade and sector publications | Partial | **Yes** |
| Company IR pages not on a wire | No | **Yes** |

**Against ADR-14's actual universe — 1,500 US and 500 IN names, all of them liquid enough to pass
a $500M market-cap and $1M ADDV screen — the licensed feeds have essentially complete coverage of
every market-moving event class.** Benzinga's stated coverage (Wilshire 5000 + TSX + 1,000
tickers) is a superset of the US universe. TrueData covers NSE and BSE filings at source.

The crawl's genuine incremental coverage is the **long tail below the liquidity screen** — which
ADR-14 has already excluded from the tradeable universe. **A crawl cannot generate an actionable
signal about a name the system is not permitted to trade.**

Benzinga's own page makes the structural argument unprompted `[V]`: *"Aggregators scrape the web
for second-hand content making them slower and prone to a massive amount of repetition and
noise."* That is a vendor marketing its own product, and it is also correct about the mechanism.

---

## 5. The comparison the owner asked for

Per-month cost against seconds saved on a position-relevant event. Prices marked `[U]` are not
verified and must be confirmed before commitment.

| Option | Monthly | Latency achieved | Coverage of ADR-14 universe |
|---|---|---|---|
| **Already owned** — Alpaca bundled Benzinga | **$0 incremental** (inside the $129–228/mo ADR-13 Option B stack) | path 5 | US universe, articles; headline stream `[U]` |
| TrueData corporate announcements (IN) | `[U]` | **< 200 ms** `[V]` | India filings, authoritative |
| RTPR (US) | **$139** `[V]` | **< 500 ms** claimed | US wire press releases |
| Benzinga direct TCP push (US) | `[U]` | push, unpublished | US, + the 600–900 headline stream |
| **Crawl fleet #46–#52** | **$3,000–8,000** self-hosted; $195k+ via proxy | ~7 s detect / ~13 s body | the tail **below** the tradeable universe |

Even taking only the verified prices, a **three-figure monthly spend buys 13–66× better latency
and authoritative coverage of every event class the system can act on**, versus a four-to-five
figure monthly spend for coverage of names ADR-14 excludes.

---

## 6. Recommendation

**R-1. Buy the push tier. Descope the crawl fleet.**

1. **Wire the feed already paid for.** Alpaca's bundled Benzinga feed is inside the existing
   $129–228/mo stack. It needs no new money — only the trigger path (#55) to use it. This is the
   highest return action in the programme.
2. **Add TrueData corporate announcements for India**, subject to OQ-3 (the simulation clause) and
   its price. At a published <200 ms from the exchange terminal, with the filed PDF as a primary
   source for corroboration (#57), it is the single best latency buy identified and it fills the
   genuine India gap in `SPEC-P0.2`.
3. **Evaluate RTPR at $139/mo** for US wire press releases, pending its machine-use licence.
4. **Resolve `[U]` on whether Alpaca's bundle carries the 600–900/day headline stream** or only the
   130–160 articles. If only the articles, Benzinga direct becomes worth pricing.
5. **Descope #46–#52** from a 3,000 fetch/s fleet to a **bounded breadth tier**: the existing
   #43 RSS/conditional-GET design over a curated registry, plus #44 on-demand scraping for IR
   pages and the sub-screen tail. Keep the architecture; drop the 10,000-domain, 388 TB/month
   target until a measured coverage gap justifies it.

**R-2. The fleet's own justification must come from #53, not from this phase.** This phase
establishes that the fleet is 13–66× slower and far more expensive for the universe the system can
actually trade. Whether that remains worth building is the edge question, and #53 answers it.

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Rank paths by evidence-backed latency, not by vendor adjectives | Four of eight paths publish no figure; an unranked ladder would be fiction | Yes | Low |
| 2 | Correct the earlier "minutes to hours" crawl estimate to ~7 s / ~13 s | The fair calculation splits the budget between discovery and fetch; the earlier figure overstated the case against the crawl | Yes | Medium — it strengthens the crawl's case, and the recommendation survives anyway |
| 3 | Recommend descoping the fleet rather than cancelling it | #43/#44 breadth has real value for the sub-screen tail; the 3,000/s target does not | Yes | Medium |
| 4 | Treat TrueData's simulation clause as blocking until answered | A plain reading forbids the paper and shadow stages, which is where the feed would be proven | Yes | **High** — if correct, the India push tier cannot be validated before live |

## ASSUMPTIONS

| # | Assumption | Why | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | 0.3 req/s/domain is a defensible politeness ceiling | No universal standard exists; it is ~1 fetch per 3.3 s per host | Per-domain robots.txt `Crawl-delay` survey | Changes every figure in §3.1 proportionally |
| 2 | Half the crawl budget on discovery, half on bodies | A reasonable split; the optimum depends on articles per domain | Measure in #43 | §3.1 latencies move by ~2× either way |
| 3 | A 50 KB wire response and the §3.1 model represent real publisher pages | From the #41 sizing | Measure | §3.1 only |
| 4 | Alpaca's bundle is the same Benzinga content P0.2 recorded | P0.2 §355 states Alpaca news *is* Benzinga | Alpaca entitlement docs | If the headline stream is excluded, §4 coverage weakens |
| 5 | Vendor latency claims are honest | Unverifiable without a trial | Measure in a paid trial, both markets | The ladder's top four rows reorder |

## OPEN QUESTIONS

| # | Question | Answered by | Exact query | Blocks |
|---|---|---|---|---|
| OQ-1 | TrueData pricing for the announcements and news APIs | Vendor | <https://www.truedata.in/price>, or sales | R-1 item 2 |
| OQ-2 | Benzinga direct pricing and the published latency of the TCP push | Vendor | <https://www.benzinga.com/apis/> contact sales | R-1 item 4 |
| **OQ-3** | **Does TrueData's "no Gaming / Virtual trading / Simulation" clause forbid use in paper trading and shadow mode?** | Vendor, in writing | The terms block on <https://www.truedata.in/products/marketdataapi> | **#35 go-live pipeline; R-1 item 2** |
| OQ-4 | Does Alpaca's bundled feed include the 600–900/day headline stream? | Alpaca entitlement docs | Alpaca market-data docs | §4 coverage, R-1 item 4 |
| OQ-5 | RTPR machine-use and storage licence | Vendor | <https://rtpr.io> terms | R-1 item 3 |
| OQ-6 | EDGAR propagation latency after acceptance | Measurement | Measure in paper trading | Ladder row 6 |
| OQ-7 | MarketMaker.in and stockinsights.ai — real products, terms, prices? | Vendors | marketmaker.in; docs.stockinsights.ai | India redundancy |
| OQ-8 | Do any India vendors permit a point-in-time news archive? | Vendors | — | #26 backtest; P0.2 M-5 already flags this as the gap threatening P5.1 |

## CONTRACTS EXPORTED

| Name | Kind | Schema / signature | Consumers |
|---|---|---|---|
| `LATENCY-LADDER-P2N13` | table | §3, 8 ranked paths with evidence grade | #53, #46, #55 |
| `FAST-FEED-REGISTRY` | document | §2 vendor facts | #42 push tier |
| `COVERAGE-VS-LATENCY-SPLIT` | table | §4 by event class | #53, #45, #47 |
| `FLEET-DESCOPE-RECOMMENDATION` | decision | §6 R-1 item 5 | #46–#52 |
| `F-1` | correction | Benzinga volume and history vs `SPEC-P0.2` §355 | `SPEC-P0.2` amendment |
| `F-3` / OQ-3 | blocker | simulation-clause licence risk | #35, #33 |
| `OPTION-GREEKS-SOURCE-IN` | finding | TrueData option chain + Greeks for NSE F&O `[V]` | **#59 (OPT.2)** |

---

# AMENDMENT v0.2 — the zero-cost tier

Added 2026-10-16 on owner instruction: the descope is **accepted**, and a free alternative is
required alongside the paid tier. Research performed against primary sources with the same
`[V]` / `[U]` discipline.

## 7. Free and already-paid sources

| Source | Cost | Authoritative for | Mechanism | Latency | Ev |
|---|---|---|---|---|---|
| **SEC EDGAR** | **free** | **all US filings — it IS the event** | REST poll + Atom (`action=getcurrent`), full-index, full-text search | 10 req/s cap; propagation unpublished | `[V]` cap, `[U]` latency |
| **Alpaca bundled Benzinga** | **already paid** (inside the $129–228/mo ADR-13 Option B stack) | US market-moving news, Wilshire 5000 + TSX + 1,000 tickers | REST poll, max 50/page | poll + vendor hop | `[V]` mech, `[U]` number |
| **GDELT 2.0** | **free** | global breadth, 65 languages, archives to 1979 | DOC 2.0 API / 15-min files | **15-minute cadence** | `[V]` <https://gdeltproject.org/data.html> |
| **FRED** | **free** | US macro | REST | daily/monthly | `[V]` P0.2 |
| **Company IR RSS/Atom** | **free** | the press release at origin | conditional GET | publisher-dependent | structural |
| **NSE / BSE announcement endpoints** | **free** | **India exchange filings** | JSON endpoints behind the public announcement pages | poll | `[U]` — **undocumented, and ToS for automated access unverified** |
| **SEBI / RBI press pages** | **free** | India regulatory | poll | poll interval | `[U]` |
| Finnhub free tier | free tier | company news | REST | `[U]` | `[U]` |

## 8. The $0-incremental configuration

A viable news capability that adds **nothing** to the current monthly spend:

| Class | Source | Cost |
|---|---|---|
| US filings | EDGAR | free |
| US news | Alpaca/Benzinga | already paid |
| India filings | NSE/BSE endpoints — **subject to OQ-9** | free |
| India regulatory | SEBI, RBI | free |
| Press releases at origin | company IR RSS | free |
| Breadth / research | GDELT | free |
| Macro | FRED | free |

**This covers every authoritative event class in `SPEC-P2N.13` §4.** What the free tier does **not**
buy is latency: nothing free matches TrueData's published 200 ms or RTPR's claimed 500 ms. The free
tier polls; the paid tier is pushed to.

### 8.1 What that costs in time-to-signal

| Tier | India filings | US filings | US news |
|---|---|---|---|
| **Free** | poll interval (seconds–minutes), ToS-limited | EDGAR poll ≤10 req/s | Alpaca poll interval |
| **Paid** | **< 200 ms** | EDGAR unchanged — already the authority | Benzinga TCP push |

Against §5's valuation of a news trigger at ~52 bps of NAV/year, and the capital ladder running
from $1,000 to $10,000, **the free tier is the correct starting configuration.** It captures the
coverage, which is what makes a thesis-invalidation trigger possible at all. Latency is the
refinement to buy once NAV makes 52 bps worth more than the subscription.

## 9. Recommendation R-2 — staged, matched to the capital ladder

| Stage | NAV | Configuration | Incremental cost |
|---|---|---|---|
| Backtest → paper → shadow | — | free tier + the already-paid Alpaca feed | **$0** |
| Small capital | $1,000 | unchanged | **$0** |
| Controlled live | $10,000 | add **RTPR $139/mo** if its machine-use licence permits (OQ-5) | $139 |
| Scale-up | $100,000+ | add **TrueData announcements** for India, subject to OQ-3 and price | `[U]` |
| — | > $7 M | revisit the crawl fleet; below that it cannot break even (§5.1 of the EDGE-ADR) | — |

**The free tier is not a compromise at this capital.** It is the configuration whose cost is
proportionate to the measured value of the signal.

## 10. The risk the free tier carries, stated plainly

The India half rests on **undocumented endpoints whose terms for automated access are unverified**
(OQ-9). That is the free tier's weak point and it is a real one:

- the endpoints can change without notice — there is no contract and no deprecation policy;
- automated access may breach the site terms, with blocking as the mild outcome;
- no SLA, no support, and no entitlement to the data.

A production system should not have an authoritative class resting on an unverified endpoint
indefinitely. The free tier is right **now**; the India paid feed is the thing to buy first as
capital grows, and OQ-9 must be answered before the free path is relied on in live trading.

## OPEN QUESTIONS — amendment

| # | Question | Answered by | Exact query | Blocks |
|---|---|---|---|---|
| OQ-9 | **Do NSE and BSE permit automated access to their announcement endpoints, and at what rate?** | NSE / BSE terms of use, and their robots.txt | nseindia.com and bseindia.com terms-of-use pages | the entire free India path |
| OQ-10 | Does GDELT's licence permit use in a commercial trading decision? | GDELT terms | <https://gdeltproject.org> terms | the free breadth tier |
| OQ-11 | Is EDGAR's `action=getcurrent` Atom feed low-latency enough to be the US filing trigger? | Measurement | measure against the daily index in paper trading | #42 push tier |
| OQ-12 | Finnhub free-tier limits, coverage and licence | Vendor | finnhub.io/pricing and terms | free-tier redundancy |

## CONTRACTS EXPORTED — amendment

| Name | Kind | Schema / signature | Consumers |
|---|---|---|---|
| `FREE-TIER-CONFIG` | decision | §8 — the $0-incremental source set | #42, #43, #55 |
| `STAGED-FEED-LADDER` | decision | §9 — what to buy at which NAV | #35 go-live gates, #46 |
| `FREE-TIER-RISK` | risk | §10 — undocumented India endpoints | #33 compliance, #47 |

---

# AMENDMENT v0.3 — subscription-free architecture

Owner instruction, 2026-10-16: **no subscriptions, at all.** RSS is to be the mechanism, not a
supplement. This amendment supersedes §9's staged ladder, which assumed paid upgrades.

## 13. Correcting the v0.2 framing

v0.2 §8 built a "$0-incremental" configuration, but it rested on the **already-paid**
Alpaca/Benzinga feed and §9 presented paid tiers as the upgrade path. #43 treated RSS as the
*breadth* tier beneath a paid push tier.

That was the wrong shape. It inherited the paid data stack ADR-13 and P0.2 had already selected
instead of questioning whether it was needed at all. **RSS is the backbone.** The paid options stay
documented in §2 as declined alternatives, not as a ladder.

## 14. The distinction that governs the whole redesign

**RSS solves forward. It cannot solve backward.** A feed serves the last N items — typically 10 to
100 — and carries no archive. So:

| Need | Mechanism | Cost |
|---|---|---|
| **Going forward** — never miss news from today onward | **RSS / Atom**, conditional GET | free |
| **Backward** — the #67 event study, #62 point-in-time, #26 backtest | **SEC EDGAR structured filings** + **GDELT** | free |

These are different mechanisms and conflating them is how a plan ends up assuming a feed can be
replayed. It cannot. **Anything historical must come from an archive, and anything forward-looking
must come from a feed — and the forward capture has to start now, because a day not captured is
gone.**

## 15. SEC EDGAR 8-K item codes — the free structured event source

Verified live against the free API, 2026-10-16, no key, declared User-Agent only:

```
GET https://data.sec.gov/submissions/CIK0000320193.json

fields: acceptanceDateTime, accessionNumber, act, core_type, fileNumber, filingDate,
        filmNumber, form, isInlineXBRL, isXBRL, isXBRLNumeric, items, primaryDocDescription,
        primaryDocument, reportDate, size

8-K  filed=2026-07-30  accepted=2026-07-31T00:30:28.000Z  items=2.02,9.01
8-K  filed=2026-04-20  accepted=2026-04-21T01:29:51.000Z  items=5.02
```

1,002 recent filings per company plus older batches. `[V]` measured.

**Why this is better than classifying news text**, and not merely cheaper:

| | News keyword classifier | EDGAR 8-K item codes |
|---|---|---|
| Taxonomy | inferred, needs hand-labelling and a precision/recall estimate | **official and structured** |
| Publication time | the vendor timestamp, often `[U]` | **`acceptanceDateTime`, exact** |
| History | vendor-dependent, archive integrity `[U]` (P0.2 M-5) | **decades, public domain** |
| Licence | redistribution `[U]` (P0.2 M-8) | **US government public domain** |
| Determinism | keyword tuning is a judgement call | **a code is a code** |

### 15.1 The item codes that are thesis-breaking events

| Item | Meaning | Why it matters |
|---|---|---|
| **4.02** | Non-reliance on previously issued financials | **the strongest red flag in the taxonomy** — a restatement |
| **4.01** | Change in auditor | resignation is a major signal |
| **3.01** | Delisting notice / failure to satisfy a listing rule | |
| **2.04** | Triggering event accelerating debt | |
| **2.06** | Material impairment | |
| **2.02** | Results of operations | the earnings event |
| **1.01 / 1.02** | Material agreement entered / terminated | M&A and contract loss |
| **5.02** | Officer or director departure | |
| **8.01** | Other material events | catch-all, needs text |

This replaces the hand-labelled keyword classifier in #67 and removes the precision/recall
estimation step entirely for every class except 8.01.

## 16. The subscription-free architecture

| Layer | Source | Mechanism | Cost |
|---|---|---|---|
| **US material events, forward** | EDGAR `action=getcurrent` Atom | conditional GET | free |
| **US material events, history** | EDGAR submissions API, 8-K `items` | REST, ≤10 req/s | free |
| **US company announcements, forward** | company IR RSS/Atom | conditional GET | free |
| **India announcements** | NSE / BSE announcement endpoints — **OQ-9** | poll | free |
| **India regulatory** | SEBI, RBI | poll | free |
| **Press releases at origin** | wire-service and IR feeds | conditional GET | free |
| **Breadth / global** | GDELT 2.0, 15-min cadence `[V]` | REST | free |
| **Macro** | FRED | REST | free |

No subscription anywhere. No licence that forbids simulation use. No redistribution question on the
US side, because EDGAR is public domain.

## 17. What this costs, stated honestly

Three things the paid tier bought that this does not:

1. **Latency.** TrueData publishes <200 ms; EDGAR is a poll at ≤10 req/s and company IR feeds are
   whatever the publisher offers. Realistic detection: **seconds to a few minutes**, not
   sub-second. Against the EDGE-ADR's ~52 bps/yr trigger value on a 15-day swing horizon, that is
   very likely immaterial — and #67 is the thing that measures whether it is.
2. **Pre-digested breadth.** Benzinga writes 600–900 headlines/day across a curated universe. RSS
   plus EDGAR gives raw material and no editorial layer, so #45's symbol linkage and #57's
   corroboration carry more weight than they would have.
3. **A support contract.** A free endpoint has no SLA and can change without notice. That is the
   real operational risk and it is why **OQ-9 must be answered** before the India path is relied on
   in live trading.

## 18. The one genuinely hard free item — and a question for the Owner

**Intraday price history is the gap.** The #67 study measures Δ, the avoidable adverse move, which
wants intraday bars. Free *daily* OHLC is widely available; free *intraday history* at 200 names ×
2 years is not, from any source I can verify.

**This is less damaging than it looks**, because ADR-13 already decided the backtest simulates stops
on **daily OHLC with a conservative intrabar assumption** — fill at `min(stop, Open)` less slippage.
So a daily-resolution Δ is *consistent with the frozen backtest methodology* rather than a
compromise against it. `f_intraday` is unaffected: EDGAR's `acceptanceDateTime` measures it exactly.

**OQ-13, for the Owner:** "no subscriptions" needs one clarification. The system still needs price
data and a broker to place orders. A **brokerage account** is not a data subscription, and Alpaca
offers a free IEX-only data tier with a funded account. Three readings:

| Reading | Consequence |
|---|---|
| (a) No paid *data* subscription; a broker account with its free tier is fine | Workable. Free tier is IEX-only, thinner than the SIP consolidated tape — P0.2 already flags Alpaca data-quality concerns, and this makes them sharper |
| (b) No paid anything, including the broker | Then there is no execution venue, and the system is research-only. ADR-11 and ADR-12 both need reopening |
| (c) No subscription for **news**; price data and broker as already decided | The smallest change. This amendment stands as written and ADR-04 is amended, nothing else |

**(c) is what this amendment assumes.** If you mean (a) or (b), say so — (b) in particular changes
the programme fundamentally and is not a news question at all.

## OPEN QUESTIONS — amendment

| # | Question | Answered by | Blocks |
|---|---|---|---|
| **OQ-13** | Which reading of "no subscriptions" — (a), (b) or (c) in §18? | **Owner** | ADR-04, ADR-11, ADR-12, and #67's price source |
| OQ-14 | Free intraday price history at 200 names × 2 years — does any source permit it? | research | #67's Δ resolution; daily is the fallback and is methodologically consistent |
| OQ-15 | Does EDGAR `action=getcurrent` Atom give acceptable forward latency? | measurement | #42 |
| OQ-9 | NSE/BSE automated-access terms — still open, and now load-bearing | exchange terms | the whole free India path |

## CONTRACTS EXPORTED — amendment

| Name | Kind | Consumers |
|---|---|---|
| `SUBSCRIPTION-FREE-ARCHITECTURE` | decision | #42, #43, #44, #45 |
| `EDGAR-8K-EVENT-TAXONOMY` | classifier | **#67** — replaces the keyword classifier |
| `FORWARD-VS-BACKWARD-RULE` | principle | #62, #67, #26 — a feed cannot be replayed |
| `OQ-13` | question | ADR-04, ADR-11, ADR-12 |
