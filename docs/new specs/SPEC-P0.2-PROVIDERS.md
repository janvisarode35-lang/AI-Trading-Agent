---
id: SPEC-P0.2-PROVIDERS
version: 0.1
status: DRAFT
phase: P0.2
depends_on: [SPEC-A-CONSTITUTION, SPEC-P0.1-DECISIONS]
produces: [F-6..F-64, DEFAULT-22..DEFAULT-31, ProviderId, Capability, SelectionStatus, VerificationLevel, LimitBasis, ProviderErrorClass, ClientOrderRef, RateLimitFact, ClientThrottle, ProviderSelection, SEL-1..SEL-21, PE-1..PE-16, THR-1..THR-12]
---

> **Model B notice (2026-10-14).** The Owner chose signals only for v1 (no order routing, no broker integration, no handling of user funds). This spec's text below is unchanged. Where it concerns orders, brokers or accounts it is superseded or deferred as listed in `MODEL-B-DECISION.md` section 6, and Block A items are read with the amendments BA-1 to BA-6 there. Phases are re-run per `ROADMAP-V1.md`.

# SPEC-P0.2 — Provider and Broker Due Diligence (new run)

Date: 2026-10-13. Decision owner: Owner. Author: integration engineer (this run).

Inputs consumed: `CONSTITUTION.md` v0.3 (SPEC-A-CONSTITUTION) and `SPEC-P0.1-DECISIONS.md` v0.1, both
as supplied in full with the phase prompt. No other repository file was read (N-3).

Run notes:
- This phase ran in a fresh conversation, as the pack requires.
- The Owner has paused direct requests to SEC hosts. No request was made to `sec.gov`,
  `data.sec.gov` or `efts.sec.gov`. Everything this spec says about SEC EDGAR comes from
  third-party pages and is marked SECONDARY.
- No account was created, no terms were accepted, no credential was read, and no authenticated
  API was called. Every fact comes from a public documentation or pricing page.
- Identifier series continue from P0.1 (D-10): DEFAULT-22, A-37, OQ-27, NB-28, D-11, F-6, UP-11,
  E-9 onward.

Status of this spec: DRAFT, and it cannot be frozen as it stands. ADR-11 says a phase that cannot
be completed for one market because a vendor fact is missing stays DRAFT. Five India capabilities
have no verified provider (section 6.2).

Contents: 1 blocking questions and defaults; 2 upstream problems; 3 evidence register;
4 capabilities needed; 5 provider fact sheets; 6 decision matrix and selection; 7 what breaks at
09:31; 8 typed form; 9 error paths; 10 documentation that could not be verified;
11 non-blocking details; then the four tables.

## 1. Blocking questions and the defaults used

| # | Question | Options | Default used | If the default is wrong |
|---|----------|---------|--------------|-------------------------|
| BQ-11 | What is the "stop resting at the broker" in India? Kite stop orders (`SL`, `SL-M`) have validity `DAY`, `IOC` or `TTL` only (F-9). The only instruction that survives the session is a GTT, and the Kite API documents `LIMIT` as the only GTT order type (F-10). | (a) one single-leg sell GTT per position, with a limit price below the trigger; (b) a fresh `SL-M` order placed every morning; (c) both | [DEFAULT-22] (a). The limit price is strictly below the trigger. The size of the gap between them is P3.4's decision and is not assumed here. | Under (a) a gap through the limit price leaves the position open with no stop, and the GTT does not fire again (F-11). Under (b) a day with no human login has no stop at all. Under (c) two sell instructions exist for the same shares. |
| BQ-12 | Which US order is the resting stop? | (a) `stop`, `gtc`; (b) `stop_limit`, `gtc`; (c) bracket order at entry | [DEFAULT-23] (a). A `stop` becomes a market order when elected (F-21). It is re-placed before its 90-day expiry. | Under (b) a gap through the limit leaves the position open. Under (c) the stop cannot be re-priced independently of the entry group. |
| BQ-13 | Are fractional shares used in the US? | yes; no | [DEFAULT-24] No. Fractional orders must be `day` (F-23), so a fractional quantity cannot carry a `gtc` stop. Whole shares in both markets. | Small US accounts cannot hold high-priced names (ADR-14, small accounts). |
| BQ-14 | How many years of US daily history are bought? | 5 years (Massive Starter, USD 29); 10 years (Developer, USD 79); 20+ years (Advanced, USD 199) (F-48) | [DEFAULT-25] 10 years, Developer plan. ADR-13 sized storage for 10 years. | P0.3 budget and P5.2 walk-forward length both change. |
| BQ-15 | Are bars stored adjusted or raw? | vendor-adjusted; raw plus our own adjustment | [DEFAULT-26] Raw bars and corporate actions are stored separately. Adjustment is computed by our code. A vendor-adjusted series is used only as a cross-check. | With vendor-adjusted storage, a vendor restating history silently changes model inputs (ADR-07 T-3) and breaks point-in-time. |
| BQ-16 | What number is "settled cash" at Alpaca? No account field is described as settled cash (F-24). | (a) `cash`; (b) `non_marginable_buying_power`; (c) our own ledger of settled cash; (d) the minimum of all three | [DEFAULT-27] (d), and the account is configured with `no_shorting=true` and `max_margin_multiplier="1"` (F-25). | A buy funded by unsettled proceeds is borrowing, which ADR-12 forbids and F-4 may make unlawful. |
| BQ-17 | What happens to US fundamentals while SEC requests are paused? | (a) build the EDGAR client anyway; (b) use a paid aggregator as primary; (c) the capability stays blocked | [DEFAULT-28] (c). No EDGAR client is built or run until the Owner lifts the pause. FMP is the named backup and is used only if the Owner approves its cost and OQ-47 is answered. | P2.4 has no fundamentals features in the first model. |
| BQ-18 | Where does India full-market daily history with delisted stocks come from (ADR-14)? | (a) a paid exchange end-of-day licence; (b) broker history for currently listed stocks only; (c) no India backtest | [DEFAULT-29] (a) is required before any India backtest is accepted as ADR-08 evidence. Until then the pipeline is built on (b) and every result from it is labelled survivorship-biased. | India results look better than they are; a model is promoted on biased evidence. |
| BQ-19 | What is the internal order reference, given Kite's `tag` is at most 20 alphanumeric characters (F-9) and Alpaca's `client_order_id` at most 128 (F-22)? | a UUID (36 characters); one short format for both brokers | [DEFAULT-30] Exactly 20 characters from `A-Z0-9`, used as Kite `tag`, Alpaca `client_order_id`, and Upstox `tag`. | With two formats, the order path is broker-specific at the identifier level, which INV-10 warns against. |
| BQ-20 | How close to a documented rate limit does a client run? | at the limit; a fixed fraction | [DEFAULT-31] At most half of the documented limit, enforced client-side (section 8.3). A provider with no documented number gets an ASSUMPTION budget and an OPEN QUESTION, never a guessed limit. | Slower backfills than necessary. |

## 2. Problems in the upstream material

RULE-5 requires this section.

| # | Where | Problem | Handling in this spec |
|---|-------|---------|-----------------------|
| UP-11 | [DEFAULT-4], ADR-13 HP-4, ADR-10 REC-4: "every open position has a stop resting at the broker" | In India no stop *order* rests across sessions. A GTT is a trigger held by Zerodha, not an exchange order. Per F-10 and F-11: it places a limit order when triggered, it triggers once only, only during market hours, it is cancelled on a corporate action with more than 2% impact, it expires after 365 days, an account may hold 500, and a sell GTT on holdings needs DDPI/POA or a per-day TPIN authorisation. Execution after the trigger is not guaranteed. REC-4 treats the stop as protection; in India it is weaker than that. | BQ-11, [DEFAULT-22]. The gap is stated in section 5.3 and in PE-9. The constitution's Q3 edge case ("the broker does not support a resting stop: not eligible for entry") would, read strictly, make every Indian stock ineligible. Owner ruling needed: OQ-27. |
| UP-12 | Constitution Q1, RISK-13: "an exit sent as a market order needs no market value" | Zerodha rejects an API market order, and an `SL-M` order, whose market protection is 0 (F-16, F-18). Upstox does the same (F-41). An Indian "market" exit through the API is therefore bounded by a protection percentage and can remain unfilled. | Recorded as PE-10. P3.4 must treat an India emergency exit as possibly unfilled and must re-check it. |
| UP-13 | ADR-12, [DEFAULT-16]: "only settled cash is read" | Alpaca's documented account object has no field described as settled cash (F-24). The rule cannot be coded as written. | BQ-16, [DEFAULT-27]. OQ-33. |
| UP-14 | Constitution C-6, OQ-7 | Confirmed. A Kite access token expires at 06:00 the next day, described by Zerodha as a regulatory requirement; a refresh token is given only to approved platforms (F-6). Zerodha forum staff state a manual login at least once a day is an exchange requirement and that automating it is not recommended (F-20, search excerpt only). | [DEFAULT-6] stands. The human login window is 06:00 to 09:15 `Asia/Kolkata`, 3 hours 15 minutes. HITL-7 is real. The terms text is OQ-28. |
| UP-15 | INV-9 "static IP"; ADR-10 recovery | Zerodha requires a registered static IP for API order placement. The registration holds at most two addresses and allows one change per calendar week (F-16, F-17). A VM restored on a new address cannot place India orders for up to a week unless the address is portable or already registered as the secondary. ADR-10's RTO of 4 hours does not account for this. | D-17: the recovery address is registered as the secondary before go-live. P6.4 must reserve it. Zerodha's own pages disagree on the effective date (1 April 2026 in the article, 1 April 2025 in the FAQ): OQ-29. |
| UP-16 | INV-9 "live-like testing"; P6.5 paper trading | Zerodha has no sandbox (F-16). India cannot be paper-traded at the broker. Alpaca paper trading does not simulate queue position, market impact, dividends or regulatory fees, and fills 10% of eligible orders partially at random (F-32). | Recorded for P5.3 and P6.5: India paper trading needs our own fill simulator; US paper results overstate fill quality. |
| UP-17 | ADR-14: "P0.2 must find a data source with delisted-stock history for both markets" | US: found in principle, not confirmed (Massive ticker reference has `active`, `delisted_utc` and a point-in-time `date` parameter, F-51; whether bars are served for delisted tickers is OQ-38). India: not found. Kite's instrument master lists live instruments only (F-13). NSE's website terms prohibit automated collection (F-63, search excerpt), so the public bhavcopy files are not a lawful automated source without a licence. | BQ-18, [DEFAULT-29]. OQ-39. This is the main reason the spec stays DRAFT. |
| UP-18 | STACK-1: "DeepSeek (primary LLM) + GPT-4o-mini (fallback)" | DeepSeek's pricing page lists two models, `deepseek-flash` and `deepseek-v4-pro`, and says legacy names are still accepted but served by a newer model (F-57). A name that is silently re-pointed changes model behaviour with no change on our side. GPT-4o-mini has one snapshot, dated 2024-07-18, and no shutdown date on the page read (F-60). | D-18: the DeepSeek model identifier is `deepseek-flash`, and the served model version returned in each response is recorded with the decision. A change of served version is treated like ADR-07 T-3 for the LLM path (P4.2 owns the rule). OQ-43, OQ-44. |
| UP-19 | P0.2 prompt SCOPE (Interactive Brokers, Upstox) and OUTPUT ("a primary and a backup per capability") against ADR-10 ("no backup broker") | The prompt asks for a backup per capability; ADR-10 decides there is no backup broker. | For broker execution the "backup" column is a named cold alternate: evaluated, not integrated, not funded. Activating one is a new ADR and HITL-6. |
| UP-20 | P0.2 prompt DELIVERABLE | Names `docs/specs/SPEC-P0.2-PROVIDERS.md`, a historical path (N-2). N-5 maps it to `docs/new specs/`. The run instruction for this conversation names a third path. | Written to `paste-ready/outputs/P0.2-CLAUDE.md` as instructed. Moving it under `docs/new specs/` is the Owner's step. |
| UP-21 | F-3 (P0.1): "all accounts are set up as margin accounts" | Alpaca's own commission disclosure refers to "self-directed individual cash brokerage accounts" (F-37, search excerpt), and the account configuration accepts `max_margin_multiplier` of `"1"` (F-25). Alpaca's statements about cash accounts are not consistent across pages. | Not resolved. OQ-33. UP-4 and OQ-14 remain open. |
| UP-22 | OQ-6 (Alpaca from India) | Alpaca's "countries" support article, dated February 2026, contains no country list and refers the reader to support (F-38). Alpaca's documentation site metadata lists separate documentation sets named "Alpaca India - Domestic" and "Alpaca India - GIFT City"; their content was not read. | OQ-6 stays open and is widened: OQ-35. |
| UP-23 | A-26 (session times) | Partly confirmed. NYSE core session 09:30 to 16:00 ET, early close 13:00 (F-61). NSE normal market 09:15 to 15:30, closing session 15:40 to 16:00 (F-62, search excerpt). Two NSE pages describe the close of pre-open order collection differently. | A-26 arithmetic stands. OQ-49 for the pre-open detail and the India holiday list. A-27 (settlement) was not verified: OQ-48. |
| UP-24 | ADR-13 "LLM affordability" and ADR-04 "news" | No verified news source exists for India (section 6.2). INV-10 forbids "US-only by accident". | The LLM news path is declared US-scoped until an India source is selected (ADR-11 edge case: a market-scoped feature must be declared). OQ-40. |
| UP-25 | Constitution U-5 (sector taxonomy) | No licensed-free taxonomy was verified for either market. US SIC codes appear in EDGAR data (F-64, secondary). Alpaca's asset object has no sector and no security-type field, so it cannot tell common stock from an ETF or a depositary receipt (F-33), which ADR-05 requires. | Instrument class for the US comes from the Massive ticker `type` field (F-51; code list unverified, OQ-38). Sector taxonomy is UNFILLED for both markets: OQ-40, OQ-41. RISK-2 cannot be enforced until it is filled. |

## 3. Evidence register

Every fact was retrieved on 2026-10-13. Levels:
- PRIMARY_FULL: the provider's own page, whole page text read in this conversation.
- PRIMARY_EXTRACT: the provider's own page, read through an automated question-answering fetch.
  The page was reached; it was not read line by line. A full read is owed by the phase named.
- SEARCH_EXCERPT: only a search-result excerpt of the provider's page was seen.
- SECONDARY: a third party's statement about the provider.

| # | Fact (summary; detail in section 5) | Source URL | Level | Full read owed by |
|---|--------------------------------------|------------|-------|-------------------|
| F-6 | Kite login flow, token fields, 06:00 expiry, refresh token for approved platforms only, margin fields | https://kite.trade/docs/connect/v3/user/ | PRIMARY_EXTRACT | P3.1 |
| F-7 | Kite rate limits: quote 1/s, historical 3/s, order placement 10/s, others 10/s; 400 orders/min; 5,000 orders/day; 25 modifications per order | https://kite.trade/docs/connect/v3/exceptions/ | PRIMARY_FULL | done |
| F-8 | Kite exception names and HTTP codes | https://kite.trade/docs/connect/v3/exceptions/ | PRIMARY_FULL | done |
| F-9 | Kite orders: varieties, order types, products, validity, parameters, `tag`, statuses, response fields | https://kite.trade/docs/connect/v3/orders/ | PRIMARY_EXTRACT | P3.1 |
| F-10 | Kite GTT API: `single` and `two-leg`, order type `LIMIT`, statuses, `expires_at` | https://kite.trade/docs/connect/v3/gtt/ | PRIMARY_EXTRACT | P3.4 |
| F-11 | Zerodha GTT behaviour: 365 days, 500 active, single use, market hours only, cancelled on corporate actions, TPIN/DDPI | https://support.zerodha.com/category/trading-and-markets/charts-and-orders/gtt/articles/what-is-the-good-till-triggered-gtt-feature | PRIMARY_EXTRACT | P3.4 |
| F-12 | Kite WebSocket: URL, modes, 3,000 instruments per connection, 3 connections per key, paise encoding | https://kite.trade/docs/connect/v3/websocket/ | PRIMARY_EXTRACT | P3.1 |
| F-13 | Kite historical candles: endpoint, intervals, candle layout, `+0530` timestamps, instrument master lists live instruments only | https://kite.trade/docs/connect/v3/historical/ | PRIMARY_EXTRACT | P2.1 |
| F-14 | Kite instrument dump and quote endpoints: columns, daily generation, 500/1,000 instruments per call | https://kite.trade/docs/connect/v3/market-quotes/ | PRIMARY_EXTRACT | P2.1 |
| F-15 | Kite holdings and positions fields; sell needs POA or depository authorisation | https://kite.trade/docs/connect/v3/portfolio/ | PRIMARY_EXTRACT | P3.1 |
| F-16 | Zerodha API FAQ: static IP rules, 10 orders/s per client with HTTP 429, market protection mandatory, plans (Personal free, Connect INR 500/month), no sandbox | https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/kite-connect-api-faqs | PRIMARY_EXTRACT | P3.1, P6.3 |
| F-17 | Zerodha static-IP article: effective 1 April 2026, one primary and one optional secondary address, one change per calendar week, order placement only | https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/static-ip | PRIMARY_EXTRACT | P6.3 |
| F-18 | Zerodha staff forum post: only order endpoints are IP-checked; above 10 orders/s needs exchange registration; `SL-M` needs market protection; slicing capped at 10 | https://kite.trade/forum/discussion/15912/preparing-to-comply-with-sebis-retail-algo-rules-static-ip-ratelimits-order-types | PRIMARY_EXTRACT | P6.3 |
| F-19 | Zerodha charges for equity delivery and intraday | https://zerodha.com/charges/ | PRIMARY_EXTRACT | P5.3 |
| F-20 | Zerodha staff: a manual login at least once a day is an exchange requirement; automating login is not recommended | https://kite.trade/forum/discussion/16212/batch-automating-kite-login and https://kite.trade/forum/discussion/9770/automating-retrieval-of-request-token | SEARCH_EXCERPT | P3.1 |
| F-21 | Alpaca orders: types, time in force, 90-day GTC expiry, price increments, stop election, statuses, extended hours | https://docs.alpaca.markets/docs/orders-at-alpaca | PRIMARY_EXTRACT | P3.1, P3.4 |
| F-22 | Alpaca create-order reference: request fields, `client_order_id` max 128, responses 200/403/422, base URLs, order object | https://docs.alpaca.markets/reference/postorder | PRIMARY_EXTRACT | P3.1 |
| F-23 | Alpaca fractional trading: time in force `day` only, 9 decimal places, `fractionable` flag | https://docs.alpaca.markets/docs/fractional-trading | PRIMARY_EXTRACT | P3.1 |
| F-24 | Alpaca account object fields; none described as settled cash | https://docs.alpaca.markets/reference/getaccount-1 | PRIMARY_EXTRACT | P2.8 |
| F-25 | Alpaca account configuration: `no_shorting`, `suspend_trade`, `fractional_trading`, `max_margin_multiplier` in `"1"`, `"2"`, `"4"` | https://docs.alpaca.markets/reference/patchaccountconfig-1 | PRIMARY_EXTRACT | P2.8 |
| F-26 | Alpaca margin: under USD 2,000 equity limited to 1x; maintenance and interest rates | https://docs.alpaca.markets/docs/margin-and-short-selling | PRIMARY_EXTRACT | P2.8 |
| F-27 | Alpaca market-data plans: Basic (free) and Algo Trader Plus (USD 99/month); 200 and 10,000 historical calls/min; 30 WebSocket symbols on Basic; history since 2016 | https://docs.alpaca.markets/docs/about-market-data-api | PRIMARY_EXTRACT | P2.1 |
| F-28 | Alpaca stock bars reference: parameters, bar fields, response codes, rate-limit headers | https://docs.alpaca.markets/reference/stockbars | PRIMARY_EXTRACT | P2.1 |
| F-29 | Alpaca feeds: `iex` about 2.5% of volume; `sip` 100% | https://docs.alpaca.markets/docs/historical-stock-data-1 | PRIMARY_EXTRACT | P2.1 |
| F-30 | Alpaca trade-update stream: URLs, auth and listen messages, event list | https://docs.alpaca.markets/docs/websocket-streaming | PRIMARY_EXTRACT | P3.1 |
| F-31 | Alpaca market-data stream: URL pattern, 10-second auth window, error codes 400 to 410 and 500 | https://docs.alpaca.markets/docs/streaming-market-data | PRIMARY_EXTRACT | P3.2 |
| F-32 | Alpaca paper trading: fill rules and what is not simulated | https://docs.alpaca.markets/docs/paper-trading | PRIMARY_EXTRACT | P5.3, P6.5 |
| F-33 | Alpaca asset object: fields; no security-type or sector field | https://docs.alpaca.markets/reference/get-v2-assets-1 | PRIMARY_EXTRACT | P2.3 |
| F-34 | Alpaca corporate actions: endpoint, parameters, 16 types, split and dividend fields | https://docs.alpaca.markets/reference/corporateactions-1 | PRIMARY_EXTRACT | P2.1 |
| F-35 | Alpaca news: endpoint, parameters, article fields, page limit 50 | https://docs.alpaca.markets/reference/news-3 | PRIMARY_EXTRACT | P4.1 |
| F-36 | Alpaca Trading API throttle: 200 requests per minute per account | https://alpaca.markets/support/usage-limit-api-calls | SEARCH_EXCERPT | P3.1 |
| F-37 | Alpaca fees: no commission; SEC fee USD 0.0000206 x trade value on sells; TAF USD 0 per share; CAT USD 0.000003 per share on buys and sells; outbound international wire USD 35 | https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf and https://alpaca.markets/support/regulatory-fees | SEARCH_EXCERPT | P5.3 |
| F-38 | Alpaca countries article (February 2026): no list of countries on the page | https://alpaca.markets/support/countries-alpaca-is-available | PRIMARY_EXTRACT | Owner, OQ-35 |
| F-39 | Upstox rate limits per API group | https://upstox.com/developer/api-documentation/rate-limiting/ | PRIMARY_FULL | done |
| F-40 | Upstox authentication and token: OAuth flow, TOTP token endpoint, 03:30 expiry, `extended_token` | https://upstox.com/developer/api-documentation/authentication/ and https://upstox.com/developer/api-documentation/get-token/ | PRIMARY_EXTRACT | only if activated |
| F-41 | Upstox place order v3: fields, `tag` max 40, error codes, market protection | https://upstox.com/developer/api-documentation/v3/place-order/ | PRIMARY_EXTRACT | only if activated |
| F-42 | Upstox GTT: limit order on trigger, valid up to one year, up to three rules | https://upstox.com/developer/api-documentation/place-gtt-order/ | PRIMARY_EXTRACT | only if activated |
| F-43 | Upstox historical candles v3: availability and per-request range by unit | https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/ | PRIMARY_EXTRACT | P2.1 |
| F-44 | Upstox market feed v3: protobuf, modes, subscription and connection limits | https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ | PRIMARY_EXTRACT | only if activated |
| F-45 | Upstox: a sandbox host exists; APIs are free; INR 10 per order | https://upstox.com/developer/api-documentation/api-overview/ and https://upstox.com/trading-api/ | SEARCH_EXCERPT | only if activated |
| F-46 | IBKR Web API: 10 requests/s global, per-endpoint limits, HTTP 429 and a 10-minute penalty box, nightly reset about 01:00 regional time, order endpoint path | https://www.interactivebrokers.com/campus/ibkr-api-page/web-api-trading/ | PRIMARY_EXTRACT | only if activated |
| F-47 | IBKR India account structures and commissions (US fixed USD 0.005/share, minimum USD 1.00; NSE INR 6 to INR 20 per order) | https://www.interactivebrokers.co.in/en/accounts/individual-account-india.php and https://www.interactivebrokers.com/en/pricing/commissions-stocks.php | SEARCH_EXCERPT | only if activated |
| F-48 | Massive stock plans: Basic USD 0 (5 calls/min, 2 years, end of day); Starter USD 29; Developer USD 79; Advanced USD 199; individual use | https://massive.com/pricing | PRIMARY_EXTRACT | P0.3 |
| F-49 | Polygon.io was renamed Massive; `api.polygon.io` keeps working "for an extended period"; `api.massive.com` runs in parallel | https://massive.com/blog/polygon-is-now-massive | SEARCH_EXCERPT | P2.1 |
| F-50 | Massive aggregates: path, parameters, `adjusted` defaults to true, limit default 5,000 and maximum 50,000, bar fields | https://massive.com/docs/rest/stocks/aggregates/custom-bars | PRIMARY_EXTRACT | P2.1 |
| F-51 | Massive tickers: path, `active`, point-in-time `date`, `delisted_utc`, `type`, limit maximum 1,000 | https://massive.com/docs/rest/stocks/tickers/all-tickers | PRIMARY_EXTRACT | P2.1, P2.3 |
| F-52 | Finnhub: HTTP 429 on excess; 30 calls/s cap on top of every plan; token in query or `X-Finnhub-Token` header | https://finnhub.io/docs/api/rate-limit | PRIMARY_EXTRACT | P4.1 |
| F-53 | Finnhub plans: Free (60 calls/min, US, company news 1 year, 50 WebSocket symbols); All-In-One USD 3,500/month; both "Personal Use" | https://finnhub.io/pricing | PRIMARY_EXTRACT | P0.3 |
| F-54 | FMP plans: Basic USD 0 (250 calls/day, 500 MB); Starter (300 calls/min, 5 years, US, 20 GB); Premium USD 99 (750 calls/min, 30 years, US/UK/Canada, 50 GB); Ultimate (3,000 calls/min, global, 150 GB); display or redistribution needs a separate agreement | https://site.financialmodelingprep.com/developer/docs/pricing | PRIMARY_EXTRACT | P0.3 |
| F-55 | FRED API terms: no numeric limit; required notice; third-party copyrighted series; licence revocable | https://fred.stlouisfed.org/docs/api/terms_of_use.html | PRIMARY_EXTRACT | P2.1 |
| F-56 | FRED `series/observations`: URL, parameters, observation fields, vintage support | https://fred.stlouisfed.org/docs/api/fred/series_observations.html | PRIMARY_EXTRACT | P2.1 |
| F-57 | DeepSeek models and prices: `deepseek-flash`, `deepseek-v4-pro`; peak and off-peak prices; 1M context | https://api-docs.deepseek.com/quick_start/pricing | PRIMARY_EXTRACT | P0.3, P4.2 |
| F-58 | DeepSeek rate limiting is by account-level concurrency; HTTP 429; keep-alive lines; 10-minute server timeout | https://api-docs.deepseek.com/quick_start/rate_limit | PRIMARY_EXTRACT | P4.2 |
| F-59 | DeepSeek error codes 400, 401, 402, 422, 429, 500, 503 | https://api-docs.deepseek.com/quick_start/error_codes | PRIMARY_EXTRACT | P4.2 |
| F-60 | OpenAI `gpt-4o-mini`: USD 0.15 / 0.075 / 0.60 per 1M input / cached input / output tokens; 128,000 context; 16,384 output; snapshot `gpt-4o-mini-2024-07-18` | https://developers.openai.com/api/docs/models/gpt-4o-mini | PRIMARY_EXTRACT | P0.3, P4.2 |
| F-61 | NYSE core session 09:30 to 16:00 ET; early close 13:00 ET; 2026 and 2027 holidays | https://www.nyse.com/markets/hours-calendars | PRIMARY_EXTRACT | P2.1 |
| F-62 | NSE timings: pre-open from 09:00, normal market 09:15 to 15:30, closing session 15:40 to 16:00 | https://www.nseindia.com/static/market-data/market-timings | SEARCH_EXCERPT | P2.1 |
| F-63 | NSE website terms prohibit systematic or automated data collection; NSE sells end-of-day and historical data through NSE Data & Analytics | https://www.nseindia.com/static/nse-terms-of-use and https://www.nseindia.com/static/market-data/eod-historical-data-subscription | SEARCH_EXCERPT | P2.1 |
| F-64 | SEC EDGAR: at most 10 requests per second per user; a `User-Agent` header naming the requester and a contact address is required; JSON endpoints for submissions and company facts | https://tldrfiling.com/blog/free-sec-edgar-api-guide/ and https://sec-edgar-api.readthedocs.io/ | SECONDARY | Owner lifts pause, then P2.1 |

Count: 59 fact rows. 3 PRIMARY_FULL, 47 PRIMARY_EXTRACT, 8 SEARCH_EXCERPT, 1 SECONDARY.

## 4. Capabilities the design needs

Derived from P0.1. A capability not listed here is not needed in v1.

| Capability | Why it is needed | Market scope | Frequency |
|------------|------------------|--------------|-----------|
| broker_execution | Orders, resting stops, positions, cash, reconciliation (ADR-10, ADR-12, ADR-13) | US, IN | Order windows; reconciliation each session |
| eod_bars | Daily bars for the whole listed market including delisted stocks (ADR-13 HP-1, ADR-14) | US, IN | Once per session after the close |
| instrument_master | Symbols, instrument class, tick size, lot size, listing status (ADR-05, UNI-3) | US, IN | Once per session |
| corporate_actions | Splits, bonus issues, dividends, mergers, delistings (BQ-15, ADR-13 edge case) | US, IN | Once per session |
| fundamentals | Point-in-time financial statements (ADR-04 option A) | US, IN | On filing |
| news | Text for the gated LLM packet (ADR-04, INV-4) | US, IN | Once per decision cycle |
| sector_taxonomy | RISK-2 (U-5) | US, IN | Monthly |
| calendar | Sessions, holidays, half-days (ADR-02) | US, IN | Yearly, checked each session |
| macro | Macro series for regime features (ADR-04 option A) | none | Daily or slower |
| fx_reference | Reporting figure only (ADR-15, OQ-22) | none | Once per India day |
| llm | Gated analysis (INV-3, STACK-1) | none | At most 20 calls a day (ADR-13) |

Not needed in v1 and therefore not specified for integration: streaming market data for
decisions (HP-1 uses completed daily bars), options data, alternative data (ADR-04), a second
broker (ADR-10).

## 5. Provider fact sheets

Convention: a cell that says NOT VERIFIED names the OPEN QUESTION that resolves it. Nothing in a
NOT VERIFIED cell may be coded against.

### 5.1 Alpaca — Trading API (US broker, fixed by INV-10)

Auth. Two HTTP headers, `APCA-API-KEY-ID` and `APCA-API-SECRET-KEY` (F-22). No token lifetime
and no refresh flow are documented for Trading API keys: a key is valid until revoked. No daily
login. IP allowlisting and 2FA for API use: NOT VERIFIED (OQ-34). Paper and live use different
keys and different hosts (F-32).

Hosts (F-22, F-30): live `https://api.alpaca.markets`, paper `https://paper-api.alpaca.markets`;
streams `wss://api.alpaca.markets/stream` and `wss://paper-api.alpaca.markets/stream`.

Endpoints needed:

| Purpose | Method and path | Verified fields | Source |
|---------|-----------------|-----------------|--------|
| Place order | `POST /v2/orders` | Request: `symbol` str; `qty` str; `side` `buy`/`sell`; `type` `market`/`limit`/`stop`/`stop_limit`/`trailing_stop`; `time_in_force` `day`/`gtc`/`opg`/`cls`/`ioc`/`fok`; `limit_price` str; `stop_price` str; `extended_hours` bool, default false; `client_order_id` str, max 128; `order_class` `simple`/`bracket`/`oco`/`oto`; `position_intent`. `type` and `time_in_force` are required. `notional` is not used (BQ-13). | F-22 |
| Order object | response of the above | `id` UUID; `client_order_id` str; `symbol` str; `qty` str or null; `filled_qty` str; `filled_avg_price` str or null; `side`; `type`; `time_in_force`; `limit_price`, `stop_price` str or null; `status`; `created_at`, `updated_at`, `submitted_at` date-time; `filled_at`, `canceled_at`, `expired_at`, `failed_at`, `replaced_at` date-time or null; `expires_at`; `replaced_by`, `replaces` UUID or null | F-22 |
| Replace order | `PATCH /v2/orders/{id}` | Semantics only: `limit_price` and `stop_price` can be updated; an order in `pending_replace` rejects a cancel. Path and body fields NOT VERIFIED (OQ-34) | F-21 |
| Cancel, list, get by client id | NOT VERIFIED (OQ-34) | none | none |
| Account | `GET /v2/account` | `cash`, `buying_power`, `regt_buying_power`, `non_marginable_buying_power`, `equity`, `last_equity`, `multiplier`, `long_market_value`, `initial_margin`, `maintenance_margin`, `sma`, `accrued_fees`, `pending_transfer_in`: all str. `trading_blocked`, `account_blocked`, `trade_suspended_by_user`: bool. `status`, `currency`: str. `last_equity` is equity at 16:00:00 ET of the previous trading day. | F-24 |
| Account configuration | `PATCH /v2/account/configurations` | `no_shorting` bool; `suspend_trade` bool ("if true, new orders are blocked"); `fractional_trading` bool; `max_margin_multiplier` str in `"1"`, `"2"`, `"4"`; `trade_confirm_email` `all`/`none`; `ptp_no_exception_entry` bool. Path taken from the reference page identifier; exact path NOT VERIFIED (OQ-34) | F-25 |
| Assets | `GET /v2/assets` | Query: `status`, `asset_class` (default `us_equity`), `exchange`, `attributes`. Object: `id`, `class`, `exchange` in `AMEX`/`ARCA`/`BATS`/`NYSE`/`NASDAQ`/`NYSEARCA`/`OTC`/`CRYPTO`, `symbol`, `name`, `status` `active`/`inactive`, `tradable`, `marginable`, `shortable`, `fractionable` bool, `attributes` list, `cusip` str or null | F-33 |
| Positions, calendar, clock | NOT VERIFIED (OQ-34, OQ-36) | none | none |
| Trade updates | stream `trade_updates` | Auth message: a JSON object with `action` = `"auth"`, `key` = the key id and `secret` = the secret key; listen message `{"action":"listen","data":{"streams":["trade_updates"]}}`. Events: `new`, `fill`, `partial_fill`, `canceled`, `expired`, `done_for_day`, `replaced`, `rejected`, `pending_new`, `stopped`, `pending_cancel`, `pending_replace`, `calculated`, `suspended`, `order_replace_rejected`, `order_cancel_rejected`, `accepted`. `fill` and `partial_fill` carry `timestamp`, `price`, `qty`, `position_qty`. JSON or MessagePack; the paper stream uses binary frames. | F-30 |

Rate limits. 200 requests per minute per account, paper and live counted separately (F-36,
SEARCH_EXCERPT; documented, not empirical). Burst and per-endpoint limits: none documented in the
pages read. The 429 body for trading endpoints: NOT VERIFIED (OQ-34). The market-data reference
documents headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (F-28);
whether trading endpoints send them is NOT VERIFIED.

WebSocket. Connection limit, heartbeat and replay after reconnect are not covered on the page
read (F-30). Design rule D-14: the stream is never the record. After any disconnect, and at
least once per session, order and position state is read over REST and compared (P5.5).

Order specifics (F-21, F-22, F-23):
- Types: `market`, `limit`, `stop`, `stop_limit`, `trailing_stop`. A `stop` becomes a market
  order when elected and does not guarantee a price. A `stop_limit` that gaps through its limit
  stays open.
- Stop election: on the consolidated print; a sell stop elects on a trade at or below the stop
  price that is not outside the NBBO. Trailing stops do not trigger outside regular hours.
- Time in force: `day` (cancelled after the closing auction), `gtc`, `opg` (rejected between
  09:28 and 19:00 ET), `cls` (rejected between 15:50 and 19:00 ET), `ioc`, `fok`.
- GTC lifetime: cancelled automatically 90 days after creation; the cancel job runs at 16:15 ET
  on that date; `expires_at` gives the date.
- Price increments: at or above USD 1.00, at most 2 decimal places; below USD 1.00, at most 4.
  A violation is rejected, error code `42210000`.
- Quantity: `qty` is a string. Fractional quantities are allowed only for `day` orders; the
  reference page says "fractional only for market and day orders" while the fractional page says
  limit, stop and stop-limit are supported with `day`. The two pages disagree; BQ-13 avoids the
  question by using whole shares.
- Minimum and maximum quantity: NOT VERIFIED (OQ-34).
- Idempotency: `client_order_id`, max 128 characters, described as unique. Charset and the
  response to a duplicate: NOT VERIFIED (OQ-34).
- Amend: replace through `PATCH`; an order placed with `notional` cannot be replaced.
- Partial fills: status `partially_filled`; stream event `partial_fill` with cumulative
  `position_qty`.
- Corporate actions: non-marketable GTC limit orders are price-adjusted; "do not reduce" is not
  supported for GTC. Treatment of a GTC `stop` on a split: NOT VERIFIED (OQ-34). ADR-13 already
  cancels and re-decides orders across a corporate action; the same rule is applied to resting
  stops (PE-11).
- Statuses: `new`, `partially_filled`, `filled`, `done_for_day`, `canceled`, `expired`,
  `replaced`, `pending_cancel`, `pending_replace`, `accepted`, `pending_new`,
  `accepted_for_bidding`, `stopped`, `rejected`, `suspended`, `calculated`, `held`.
- Rejections documented: HTTP 403 "buying power or shares is not sufficient"; HTTP 422 "input
  parameters are not recognized"; `42210000` sub-penny; extended-hours order that is not a
  `day`/`gtc` limit; `opg`/`cls` outside their windows; non-limit order on an IPO symbol before
  its first trade; "requested asset is not fractionable". A complete rejection code list is not
  published on the pages read: OQ-34.

Account and margin (F-24, F-25, F-26). Equity under USD 2,000 is limited to 1x buying power.
Margin interest 6.50% a year for non-elite users, charged on the end-of-day debit balance. No
"settled cash" field (UP-13). Settlement cycle: NOT VERIFIED (OQ-48).

Failure modes. Paper differs from live (F-32): fills only when marketable against the NBBO; 10%
of eligible orders get a random partial fill; order size is not checked against quoted size;
queue position, market impact, latency slippage, dividends and regulatory fees are not
simulated. Known outages and maintenance windows: NOT VERIFIED (no status-page read; OQ-34).

Cost (F-37, SEARCH_EXCERPT). No commission on US-listed equities through the API. Pass-through:
SEC fee USD 0.0000206 x trade value on sells; FINRA TAF listed as USD 0 per share; CAT
USD 0.000003 per executed share on buys and sells; fees are rounded up to the cent. Outbound
international wire USD 35.

Legal. Eligibility of an Indian resident: NOT VERIFIED (OQ-35, OQ-14). Customer agreement terms
on automated trading: NOT VERIFIED (OQ-37).

### 5.2 Alpaca — Market Data API (US bars backup, corporate actions, news)

Auth. Same two headers as trading, or HTTP Basic (F-28). Host `https://data.alpaca.markets`;
sandbox `https://data.sandbox.alpaca.markets`.

Plans (F-27): Basic, free: real-time IEX only, 200 historical calls/min, 30 WebSocket symbols,
no historical data from the latest 15 minutes. Algo Trader Plus, USD 99/month: all US exchanges,
10,000 calls/min, unlimited symbols. History since 2016 on both.

Bars (F-28): `GET /v2/stocks/bars`.

| Parameter | Type | Default | Range and notes |
|-----------|------|---------|-----------------|
| `symbols` | str, comma-separated | required | none stated |
| `timeframe` | str | required | `1Day` for this design |
| `start`, `end` | RFC 3339 or `YYYY-MM-DD` | start of current day; now, or now minus 15 minutes without real-time access | inclusive |
| `limit` | int | 1000 | 1 to 10,000; counts data points across all symbols |
| `adjustment` | str | `raw` | `raw`, `split`, `dividend`, `spin-off`, `all`; comma-combinable |
| `asof` | `YYYY-MM-DD` | current day | maps symbol renames; `-` disables mapping |
| `feed` | str | `sip` | `sip`, `iex`, `boats`, `otc` |
| `sort` | str | `asc` | `asc`, `desc` |
| `page_token` | str | none | from `next_page_token` |

Bar fields: `t` RFC 3339 string (examples end in `Z`; the page does not state the zone), `o`,
`h`, `l`, `c` number, `v` int64, `n` int64, `vw` number. Response codes 400, 401, 403, 429, 500.

Data specifics. `sip` is the consolidated tape, 100% of volume; `iex` is one venue, about 2.5%
of volume (F-29), and must never feed a traded-value ranking (UNI-1). Adjustment defaults to
raw. Delisted symbol coverage, survivorship and the daily-bar session definition: NOT VERIFIED
(OQ-36). Latency: not relevant to an end-of-day design; the 15-minute restriction on Basic means
the daily bar is requested no earlier than 16:15 ET.

Corporate actions (F-34): `GET /v1/corporate-actions`; parameters `symbols`, `cusips`, `types`,
`start`, `end` (inclusive, default current day), `ids`, `limit` (default 100, max 1,000),
`sort` by `process_date`, `page_token`. Types: `reverse_split`, `forward_split`, `unit_split`,
`cash_dividend`, `stock_dividend`, `spin_off`, `cash_merger`, `stock_merger`,
`stock_and_cash_merger`, `redemption`, `name_change`, `worthless_removal`,
`rights_distribution`, `partial_call`, `reorganization`, `capital_gains_distribution`.
`forward_split`: `id`, `symbol`, `cusip`, `old_rate`, `new_rate` (double), `ex_date`,
`record_date`, `payable_date`, `process_date`. `cash_dividend`: `rate` (double), `special`,
`foreign` (bool), `ex_date`, `record_date`, `payable_date`, `process_date`. The page warns that
actions may arrive late. History depth: NOT VERIFIED (OQ-36).

News (F-35): `GET /v1beta1/news`; `start`, `end`, `sort` (default `desc`), `symbols`, `limit`
1 to 50 (default 10), `include_content`, `exclude_contentless`, `page_token`. Article: `id`
int64, `headline`, `author`, `created_at`, `updated_at` (RFC 3339), `summary`, `content` (may
contain HTML), `url`, `symbols` list, `source`. The example source is Benzinga. History depth
and licence to store or to pass text to a third-party LLM: NOT VERIFIED (OQ-37).

Market-data stream (F-31), not used by any decision: `wss://stream.data.alpaca.markets/{version}/{feed}`;
authenticate within 10 seconds; errors 400 invalid syntax, 401 not authenticated, 402 auth
failed, 403 already authenticated, 404 auth timeout, 405 symbol limit exceeded, 406 connection
limit exceeded, 407 slow client, 409 insufficient subscription, 410 invalid subscribe action,
500 internal error. No replay of missed data is documented.

Legal. Redistribution and storage terms: NOT VERIFIED (OQ-37).

### 5.3 Zerodha Kite Connect (India broker, fixed by INV-10)

Auth (F-6, F-16, F-17, F-20).
- Flow: browser login at `https://kite.zerodha.com/connect/login` with query parameters `v=3` and
  `api_key`; redirect with a one-time `request_token`; `POST https://api.kite.trade/session/token`
  with `api_key`, `request_token`, `checksum` = SHA-256 of `api_key + request_token + api_secret`;
  response `access_token` (str), `user_id`, `login_time`, `exchanges`, `products`, `order_types`,
  `public_token`, `refresh_token`.
- Lifetime: the access token expires at 06:00 the next day unless invalidated earlier by logout
  or by a master logout from the web terminal.
- Refresh: `refresh_token` is "only available to certain approved platforms". An individual has
  none. Refresh cannot be automated.
- Daily manual login: required (F-20, SEARCH_EXCERPT). TOTP is mandatory for the login.
- Session conflict: `TokenException` (HTTP 403) is also raised when the user logs in to another
  Kite instance (F-8). An operator opening a second API session can invalidate the system's.
- Static IP: order placement requires a registered static IP; one primary and one optional
  secondary; one change per calendar week; IPv4 and IPv6; registered per developer account;
  shareable only within immediate family; data, order book and positions endpoints work from any
  address. An order from an unregistered address is rejected; the error body is NOT VERIFIED
  (OQ-29).
- Logout: `DELETE /session/token`.

Endpoints needed (host `https://api.kite.trade`):

| Purpose | Method and path | Verified fields | Source |
|---------|-----------------|-----------------|--------|
| Place order | `POST /orders/:variety` | `tradingsymbol`, `exchange`, `transaction_type` `BUY`/`SELL`, `order_type` `MARKET`/`LIMIT`/`SL`/`SL-M`, `quantity`, `product` `CNC`/`NRML`/`MIS`/`MTF`, `price`, `trigger_price`, `disclosed_quantity`, `validity` `DAY`/`IOC`/`TTL`, `validity_ttl` (minutes), `market_protection` (greater than 0 up to 100, or -1 for automatic), `autoslice` bool (at most 10 slices), `tag` (alphanumeric, max 20). Variety: `regular`, `amo`, `co`, `iceberg`, `auction`. Path taken from the modify and cancel paths; NOT separately verified (OQ-31) | F-9 |
| Modify | `PUT /orders/:variety/:order_id` | `order_type`, `quantity`, `price`, `trigger_price`, `disclosed_quantity`, `validity`; at most 25 modifications per order | F-9, F-7 |
| Cancel | `DELETE /orders/:variety/:order_id` | none beyond the path | F-9 |
| Order object | order book and history | `order_id` str; `exchange_order_id` str or null; `status` str; `status_message`, `status_message_raw` str or null; `tradingsymbol`, `exchange`, `transaction_type`, `order_type`, `product`, `validity`, `variety` str; `price`, `trigger_price`, `average_price` float64; `quantity`, `filled_quantity`, `pending_quantity`, `cancelled_quantity`, `disclosed_quantity` int64; `order_timestamp`, `exchange_timestamp`, `exchange_update_timestamp` str; `tag` str or null; `guid` str | F-9 |
| Trades | `GET /trades`, `GET /orders/:order_id/trades` | `trade_id`, `order_id`, `exchange_order_id`, `tradingsymbol`, `exchange`, `transaction_type`, `product` str; `average_price` float64; `filled` int64; `fill_timestamp`, `order_timestamp`, `exchange_timestamp` str | F-9 |
| GTT | `POST`, `GET`, `PUT`, `DELETE` on `/gtt/triggers` and `/gtt/triggers/:id` | `type` `single`/`two-leg`; `condition` {`exchange`, `tradingsymbol`, `trigger_values` array, `last_price`}; `orders` array of {`exchange`, `tradingsymbol`, `transaction_type`, `quantity`, `order_type` `LIMIT`, `product`, `price`}. Trigger object: `id`, `type`, `created_at`, `updated_at`, `expires_at`, `status`. Statuses: `active`, `triggered`, `disabled`, `expired`, `cancelled`, `rejected`, `deleted` | F-10 |
| Holdings | `GET /portfolio/holdings` | `quantity`, `t1_quantity`, `used_quantity`, `authorised_quantity`, `collateral_quantity` int64; `average_price`, `last_price`, `close_price`, `pnl` float64; `isin` str | F-15 |
| Positions | `GET /portfolio/positions` | `net` and `day` lists; `quantity`, `overnight_quantity`, `multiplier` int64; `average_price` float64 | F-15 |
| Margins | `GET /user/margins/:segment` | `enabled` bool; `net`, `available.cash`, `available.opening_balance`, `available.live_balance`, `available.intraday_payin`, `available.collateral`, `utilised.debits`, `utilised.delivery`, `utilised.holding_sales`, `utilised.payout` float64 | F-6 |
| Instruments | `GET /instruments` | gzipped CSV, generated once a day; `instrument_token`, `exchange_token`, `tradingsymbol`, `name` str; `last_price`, `strike`, `tick_size` float64; `lot_size` int64; `expiry`, `instrument_type`, `segment`, `exchange` str | F-14 |
| Quote | `GET /quote` (500 instruments), `/quote/ohlc` (1,000), `/quote/ltp` (1,000) | `last_price` float64; `last_trade_time` str or null; `timestamp` str; `volume` int64; `ohlc.open/high/low/close` float64; `lower_circuit_limit`, `upper_circuit_limit` float64; `depth.buy[]`, `depth.sell[]` {`price`, `orders`, `quantity`} | F-14 |
| Historical | `GET /instruments/historical/:instrument_token/:interval` | `from`, `to` as `yyyy-mm-dd hh:mm:ss`; `interval` in `minute`, `day`, `3minute`, `5minute`, `10minute`, `15minute`, `30minute`, `60minute`; candles `[timestamp, open, high, low, close, volume]`; timestamp `yyyy-mm-ddThh:mm:ss+0530` | F-13 |

Rate limits (F-7, PRIMARY_FULL; documented, not empirical):

| Scope | Limit |
|-------|-------|
| Quote | 1 request per second |
| Historical candle | 3 requests per second |
| Order placement | 10 requests per second |
| All other endpoints | 10 requests per second |
| Orders | 10 per second and 400 per minute |
| Orders per user or API key per day | 5,000, across all segments and varieties |
| Modifications per order | 25, then cancel and place again |

HTTP 429 means "too many requests to the API". The 10 orders per second is per trading account,
not per app, and requests that are blocked as invalid still count (F-16). Above 10 orders per
second a strategy must be registered with the exchange (F-18). No burst allowance and no
rate-limit headers are documented.

WebSocket (F-12): `wss://ws.kite.trade` with `api_key` and `access_token`; modes `ltp` (8
bytes), `quote` (44 bytes), `full` (184 bytes, with depth); up to 3,000 instruments per
connection and 3 connections per API key; a 1-byte heartbeat every couple of seconds when idle;
market data is binary, order postbacks and errors are text (`order`, `error`, `message`).
Prices are integers in paise: divide by 100. Reconnect guidance and replay of missed ticks or
order updates are not on the page (OQ-31). Rule D-14 applies. The Personal (free) plan excludes
live and historical data (F-16).

Data specifics.
- Adjustment of historical candles for splits, bonus issues and dividends: NOT VERIFIED (OQ-30).
- History depth: "several years"; no number (OQ-30). Maximum range per request: NOT VERIFIED.
- Delisted coverage: none. The instrument master returns only live instruments (F-13).
- Instrument identity: Zerodha recommends `exchange` plus `tradingsymbol` as the key, because
  exchanges may reuse `instrument_token` (F-14). Neither survives a rename; the internal
  instrument identifier of UNI-4 must be mapped through ISIN (`isin` is on holdings, F-15; it is
  not a column of the instrument dump as listed).
- Tick size and lot size: per instrument, from the dump, refreshed daily. No constant is
  assumed.
- Timestamp zone of order and trade timestamps: not stated on the page (OQ-30). Historical
  candles carry `+0530`.
- Tape: NSE and BSE are separate venues with separate `exchange` values; there is no
  consolidated tape. Traded value for UNI-1 is per exchange; which exchange is used is P2.3's.
- Extended hours: `amo` variety exists for after-market orders (F-9); behaviour NOT VERIFIED.

Order specifics.
- Order types: `MARKET`, `LIMIT`, `SL`, `SL-M`. Market and `SL-M` need non-zero market
  protection through the API (UP-12).
- Time in force: `DAY`, `IOC`, `TTL` (minutes). There is no GTC. GTT is the multi-session
  mechanism: valid 365 days, 500 active per account, single use, triggers only in market hours
  (to 15:30 for non-F&O stocks, to 15:15 for F&O stocks), cancelled on corporate actions with
  more than 2% impact, sell GTT on holdings needs DDPI/POA or TPIN (F-11).
- Disagreement between Zerodha's own pages: the API reference lists `LIMIT` as the GTT order
  type (F-10); the support article says a "limit order or market order with market protection"
  is placed (F-11). OQ-27.
- Fractional shares: not offered; `quantity` is int64.
- Idempotency: none on the request. `tag` (alphanumeric, max 20) is echoed on the order and is
  the only caller-supplied identifier. `guid` appears on the order object; its guarantee is
  NOT VERIFIED (OQ-31). Rule D-15: after an unknown outcome the order book is read and matched on
  `tag` before anything is sent again.
- Amend: in place through `PUT`, 25 times per order.
- Partial fill: `filled_quantity`, `pending_quantity`, `cancelled_quantity` on the order;
  per-fill rows from the trades endpoint.
- Statuses: `OPEN`, `COMPLETE`, `CANCELLED`, `REJECTED`, plus interim `PUT ORDER REQ RECEIVED`,
  `VALIDATION PENDING`, `OPEN PENDING`, `MODIFY VALIDATION PENDING`, `MODIFY PENDING`,
  `TRIGGER PENDING`, `CANCEL PENDING`, `AMO REQ RECEIVED`.
- Rejection reasons: delivered as free text in `status_message`. No list is published on the
  pages read (OQ-32). The exception classes are the only stable taxonomy: `TokenException`,
  `UserException`, `OrderException`, `InputException`, `MarginException`, `HoldingException`,
  `NetworkException`, `DataException`, `GeneralException` (F-8).
- HTTP codes: 400, 403 (session expired), 404, 405, 410, 429, 500, 502 (order management system
  down), 503, 504 (F-8).

Failure modes. No sandbox (F-16). A 502 means the broker's order system is down while the API
answers. Known outage history and maintenance windows: NOT VERIFIED (OQ-32).

Cost. Connect plan INR 500 per month per API key, includes WebSocket and historical data;
Personal plan free, without data (F-16). Charges on trades (F-19): equity delivery brokerage
zero; STT 0.1% on buy and sell; exchange transaction charge NSE 0.00307%, BSE 0.00375%; SEBI
charge INR 10 per crore; stamp duty 0.015% on the buy side; GST 18% on brokerage, SEBI and
transaction charges; depository charge INR 15.34 per scrip on each sell day. Equity intraday:
brokerage 0.03% or INR 20 per executed order, whichever is lower; STT 0.025% on the sell side;
stamp duty 0.003% on the buy side. Whether a same-day buy and sell under product `CNC` is charged
as intraday is NOT VERIFIED (OQ-48; A-33 stays an assumption).

Legal. Kite Connect terms on automated login, data storage and redistribution: NOT VERIFIED
(OQ-28). Zerodha staff describe Kite Connect as "purely an execution platform" (forum excerpt),
which bears on using its data as a research store.

### 5.4 Upstox (India cold alternate; India daily-history backup)

Auth (F-40). OAuth: `https://api.upstox.com/v2/login/authorization/dialog` then
`POST https://api.upstox.com/v2/login/authorization/token` with `code`, `client_id`,
`client_secret`, `redirect_uri`, `grant_type=authorization_code`. A second endpoint,
`POST /v2/totp-login/authorization/token`, issues a token from header `x-api-key` and body
`totp` (6 digits) and `pin` (6 digits), for individual apps with TOTP enabled; issuing a new
token revokes the active one. The token "lasts until 3:30 AM the following day, regardless of
the time it was generated". `extended_token` is for prolonged, mainly read-only access. Whether
the TOTP endpoint may be called unattended under Upstox terms and exchange rules is NOT VERIFIED
(OQ-46); F-20 suggests the exchange requirement is broker-independent.

Rate limits (F-39, PRIMARY_FULL; per API, per user):

| Group | Per second | Per minute | Per 30 minutes |
|-------|-----------|------------|----------------|
| Order placement (place, modify, cancel, multi-order, GTT), regular algos | 10 | 500 | 2,000 |
| Order placement, exchange-registered algos | 50 | 500 | 2,000 |
| Other standard APIs (holdings, positions, funds, historical candles) | 50 | 500 | 2,000 |
| TOTP login | 1 | 10 | 60 |

Exceeding a limit "might result in temporary suspension of access". The response code is not
stated on the page.

Orders (F-41). `POST https://api-hft.upstox.com/v3/order/place`, `Authorization: Bearer`.
Fields: `quantity` int32, `product` `I`/`D`/`MTF`, `validity` `DAY`/`IOC`, `price` float,
`tag` str max 40, `instrument_token` str (for example `NSE_EQ|INE669E01016`), `order_type`
`MARKET`/`LIMIT`/`SL`/`SL-M`, `transaction_type` `BUY`/`SELL`, `disclosed_quantity` int32,
`trigger_price` float, `slice` bool, `market_protection` int32 (-1 automatic, 1 to 25; 0 is
rejected for market orders). Response `data.order_ids` list. No idempotency key. Selected error
codes: `UDAPI1154` static IP restriction; `UDAPI1158` market orders not allowed; `UDAPI1118`
maximum order limit exceeded; `UDAPI1119` tag too long; `UDAPI100074` order API available 05:30
to 00:00 IST. Header `X-Algo-Name` is required only for exchange-approved strategies.

GTT (F-42). `POST https://api.upstox.com/v3/order/gtt/place`; `SINGLE` or `MULTIPLE` with
rules `ENTRY`, `TARGET`, `STOPLOSS`; an `ENTRY` rule is mandatory, so a stand-alone stop for an
existing holding is not directly expressible; "always placed as a LIMIT order"; valid up to one
year; sell legs need EDIS authorisation.

Historical (F-43). `GET https://api.upstox.com/v3/historical-candle/:instrument_key/:unit/:interval/:to_date/:from_date`.
Daily data from January 2000, one decade per request; minutes and hours from January 2022.
Candle `[timestamp, open, high, low, close, volume, open_interest]`, timestamp ISO 8601 with
`+05:30`. Corporate-action adjustment and delisted coverage: NOT VERIFIED (OQ-46).

Market feed (F-44): protobuf over WebSocket; 2 connections (5 on Upstox Plus); up to 5,000
instrument keys in `ltpc` mode; standard ping frames; no replay documented.

Sandbox: a sandbox host exists (F-45, SEARCH_EXCERPT). Cost: APIs free; INR 10 per order
(F-45).

### 5.5 Interactive Brokers (US cold alternate)

Facts (F-46, F-47). Web API: 10 requests per second globally; per-endpoint limits include
`/iserver/orders` GET 1 per 5 seconds, `/iserver/trades` GET 1 per 5 seconds,
`/portfolio/accounts` GET 1 per 5 seconds, `/iserver/marketdata/snapshot` 10 per second,
`/tickle` 1 per second, `/sso/validate` 1 per minute. Exceeding a limit returns HTTP 429 and
puts the client in a penalty box for 10 minutes. Individual clients authenticate through the
Client Portal Gateway with username and password. Brokerage endpoints are briefly unavailable
each night at about 01:00 regional time. Orders: `POST /iserver/account/{accountId}/orders`,
which can answer with an "order reply" message that must be confirmed before the order is
live. A paper account needs a funded live account. Indian residents are offered account
structures for NSE only, overseas only, or both (SEARCH_EXCERPT). US commission, fixed plan:
USD 0.005 per share, minimum USD 1.00 per order, maximum 1% of trade value.

Not verified: 2FA and daily re-login for the gateway, session lifetime, customer order
identifier, full order types and time in force, stream replay (OQ-45). The page read was last
modified 2024-12-17 per its metadata.

Assessment. The nightly reset, the 10-minute penalty box and the order-reply confirmation step
are three more states than Alpaca's order path has. IBKR stays a cold alternate.

### 5.6 Massive, formerly Polygon.io (US daily bars and instrument master, primary)

Naming (F-49, SEARCH_EXCERPT): Polygon.io is now Massive. `api.polygon.io` continues to work
for an extended period; `api.massive.com` runs in parallel. Config key `massive.base_url` holds
the host so the change is one value.

Auth: API key. Header or query form NOT VERIFIED (OQ-38).

Plans (F-48): Basic USD 0, 5 calls/min, 2 years, end of day. Starter USD 29/month, unlimited
calls, 5 years, 15-minute delayed. Developer USD 79/month, unlimited calls, 10 years, 15-minute
delayed. Advanced USD 199/month, unlimited calls, 20+ years, real time, includes financials.
"Financials & Ratios" add-on USD 29/month. All plans include reference data and corporate
actions. Plans are labelled individual use; a "non-pros only" condition is linked and was not
read (OQ-38).

Bars (F-50): `GET /v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}`;
`adjusted` bool, default true; `sort` `asc`/`desc`; `limit` default 5,000, max 50,000. Result
fields: `o`, `h`, `l`, `c`, `v`, `vw` number; `t` integer, Unix milliseconds at the start of
the window; `n` integer. Split-adjusted by default; dividend adjustment is not mentioned.
[DEFAULT-26] requires `adjusted=false`.

Tickers (F-51): `GET /v3/reference/tickers`; `ticker`, `type`, `market`, `exchange`, `active`
(default true), `date` (point-in-time: "tickers available on that date"), `limit` default 100,
max 1,000. Fields: `ticker`, `name`, `market`, `locale`, `primary_exchange`, `type`, `active`,
`currency_name`, `cik`, `composite_figi`, `share_class_figi`, `delisted_utc`,
`last_updated_utc`.

Not verified (OQ-38): whether bars are returned for delisted tickers; the meaning of
`active=false`; the list of `type` codes; the split and dividend endpoints and fields; a whole
market daily endpoint; the zone that defines a daily bar; fair-use limits behind "unlimited";
429 behaviour; WebSocket details (not needed for end-of-day).

Legal: individual, non-professional use. Storage and redistribution terms NOT VERIFIED (OQ-38).

### 5.7 Finnhub (US news backup)

Facts (F-52, F-53). Base path `/api/v1`. Auth: `token` query parameter or `X-Finnhub-Token`
header. D-16 requires the header form, because a key in a URL is written to access logs. HTTP
429 when a limit is exceeded; a cap of 30 calls per second sits on top of every plan. Free plan:
60 calls/min, US coverage, company news for 1 year with real-time updates, 50 WebSocket
symbols. All-In-One: USD 3,500/month, 900 market-data and 300 fundamental calls/min. Both are
labelled "Personal Use. Terms apply". India coverage is not mentioned on the pricing page.

Not verified (OQ-50): news endpoint path and fields, terms on storage and LLM processing, India
coverage.

### 5.8 Financial Modeling Prep (US fundamentals backup)

Facts (F-54). Basic: USD 0, 250 calls per day, 500 MB bandwidth. Starter: 300 calls/min, up to
5 years, US, 20 GB; the page displays both USD 19.00 and USD 49.00 for it, so the price is
NOT VERIFIED (OQ-47). Premium: USD 99.00, 750 calls/min, up to 30 years, US, UK and Canada,
50 GB. Ultimate: 3,000 calls/min, global, full history, 150 GB; price not shown. "Displaying or
redistributing data sourced from FMP requires a specific Data Display and Licensing Agreement."

Not verified (OQ-47): every endpoint and field; whether statements carry filing and acceptance
dates (needed for point-in-time use); India coverage; 429 behaviour.

### 5.9 SEC EDGAR (US fundamentals and filings; blocked)

Everything here is SECONDARY (F-64). Third-party pages state: at most 10 requests per second
per user; every request must send a `User-Agent` naming the requester with a contact address;
requests without it are commonly answered 403; JSON endpoints exist for a company's submissions
and for XBRL company facts, keyed by a CIK zero-padded to 10 digits; submission records include
`form`, `filingDate`, `acceptanceDateTime`, `accessionNumber`, and a `sic` code.

None of this may be coded against. The capability is BLOCKED by the Owner's pause ([DEFAULT-28])
and by a second issue: the required `User-Agent` discloses a contact identity, which the Owner
must choose and approve (HITL-14 treats it like a credential). OQ-41.

### 5.10 FRED (macro, primary)

Facts (F-55, F-56). `GET https://api.stlouisfed.org/fred/series/observations`; `api_key`
(32-character lower-case alphanumeric), `series_id`, `file_type` (`json`), `observation_start`,
`observation_end`, `limit` 1 to 100,000 (default 100,000), `offset`, `sort_order`,
`realtime_start`, `realtime_end`, `vintage_dates`, `output_type` 1 to 4. Observation:
`realtime_start`, `realtime_end`, `date`, `value`, all strings. Vintage data is supported, which
is what point-in-time macro features need (ADR-04 admission rule 1). Terms: no numeric rate
limit is stated; the service "may impose limits"; the application must display "This product
uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.";
series marked as copyrighted need the owner's permission for non-personal use; the licence can
be ended at any time.

Not verified (OQ-42): the numeric rate limit and the 429 body; how a missing observation is
written in `value`; India macro series and their source.

### 5.11 News API (US)

Selected: Alpaca News (section 5.2), because it adds no account and no key. Backup: Finnhub
company news (section 5.7). Neither has verified terms for storing article text or for sending
it to DeepSeek or OpenAI (OQ-37, OQ-50); until those are answered the LLM packet may carry only
the headline, the summary and the URL is a P4.1 decision that this spec does not make. India:
no source verified (UP-24).

### 5.12 DeepSeek API (primary LLM, fixed by STACK-1)

Facts (F-57, F-58, F-59).

| Item | `deepseek-flash` | `deepseek-v4-pro` |
|------|------------------|-------------------|
| Served version on 2026-10-13 | DeepSeek-V4.1-Flash | DeepSeek-V4-Pro-0813 |
| Context | 1M tokens | 1M tokens |
| Maximum output | 384K tokens | 384K tokens |
| JSON output, tool calls | yes, yes | yes, yes |
| Input, cache hit, per 1M tokens (peak / off-peak) | 0.006 / 0.003 | 0.044 / 0.022 |
| Input, cache miss, per 1M tokens (peak / off-peak) | 0.3 / 0.15 | 1.32 / 0.66 |
| Output, per 1M tokens (peak / off-peak) | 1.2 / 0.6 | 3.96 / 1.98 |
| Concurrency limit | 2,500 | 500 |

Prices carry a `$` sign with no currency code (A-43). Peak hours are 01:00 to 04:00 and 06:00
to 10:00 UTC, Monday to Friday, excluding Chinese public holidays. Thinking mode is on by
default. Limits are by concurrency at account level, not by requests per minute; exceeding
returns HTTP 429. Under load the server holds the connection open with empty lines (or
`: keep-alive` comments when streaming) and closes it if inference has not started after 10
minutes. Errors: 400 invalid format, 401 authentication fails, 402 insufficient balance, 422
invalid parameters, 429 rate limit reached, 500 server error, 503 server overloaded.

Timing against the session clocks: the India decision cycle starts after 15:30 IST = 10:00
UTC, the end of a peak window; the US cycle starts after 16:00 ET = 20:00 or 21:00 UTC,
off-peak. No price is assumed for P0.3 from this; P0.3 prices at peak.

Not verified (OQ-43): base URL and auth header (not on the three pages read); whether
`deepseek-chat` is still accepted; whether a dated version can be pinned; default output limit;
data retention, training use and processing location.

A client that reads a body before the 10-minute server timeout would stall the decision cycle;
PE-14 sets our own deadline.

### 5.13 OpenAI API (fallback LLM, fixed by STACK-1)

Facts (F-60). `gpt-4o-mini`: USD 0.15 per 1M input tokens, USD 0.075 cached input, USD 0.60
output; context 128,000 tokens; maximum output 16,384 tokens; knowledge cutoff 2023-10-01;
structured outputs and function calling supported; single snapshot `gpt-4o-mini-2024-07-18`;
lowest listed tier 5,000 requests and 2,000,000 tokens per minute; no shutdown date on the page.

Not verified (OQ-44): base URL and auth header on a page read in this run; the account's tier;
shutdown date; data retention terms; 429 body.

D-18 pins the snapshot identifier, not the alias.

### 5.14 NSE and BSE (exchange facts)

- Sessions (F-62, SEARCH_EXCERPT): NSE pre-open from 09:00; normal market 09:15 to 15:30;
  closing session 15:40 to 16:00. BSE times were not retrieved (OQ-49).
- Holidays and special sessions for 2026 and 2027: not retrieved (OQ-49).
- Algo rules (F-2 of P0.1; F-16, F-18, F-39): the threshold of 10 orders per second is applied
  by both brokers per client; under it no strategy registration is needed (Upstox states this
  directly, citing the NSE circular of 2025-05-05); above it the strategy is registered with the
  exchange. Who generates the per-order exchange tag for an unregistered client strategy is
  still open (OQ-51, the remainder of OQ-1).
- Data (F-63, SEARCH_EXCERPT): the NSE website terms prohibit systematic or automated data
  collection. End-of-day and historical files are sold through NSE Data & Analytics. Price,
  licence terms and whether delisted securities are included: NOT VERIFIED (OQ-39).
- Tick size, lot size and price bands: read per instrument from the broker's instrument dump and
  quote (`tick_size`, `lot_size`, `lower_circuit_limit`, `upper_circuit_limit`); no exchange
  constant is assumed.

## 6. Decision matrix and selection

### 6.1 Method

Six criteria, each scored 0 to 5 from the fact sheets, weights summing to 100. Score =
sum(weight x points) / 5, so the maximum is 100. A capability's highest score is the primary and
the next is the backup. A tie is broken in favour of the provider that adds no new account
(RULE-3). A provider that INV-10 or STACK-1 fixes is primary regardless of score; its score is
still shown.

| Criterion | Weight | 5 points means | 0 points means |
|-----------|--------|----------------|----------------|
| C1 Fit to the requirement in section 4 | 30 | covers it fully | does not cover it |
| C2 Documented behaviour (limits, fields, errors) | 20 | documented and read | undocumented or unread |
| C3 Operability on one VM with one operator | 15 | key-based, no daily human step, no new account | daily human step or blocked |
| C4 Integrity (point-in-time, delisted, adjustment; for brokers, safety of the resting stop) | 15 | verified strong | verified weak or unknown |
| C5 Cost | 10 | free | above USD 500 a month or unknown |
| C6 Legal clarity for automated use and storage | 10 | terms read and permissive | terms read and prohibitive |

Points for C6 are capped at 3 wherever the terms were not read in this run.

### 6.2 Scores

| Capability | Market | Candidate | C1 | C2 | C3 | C4 | C5 | C6 | Score |
|------------|--------|-----------|----|----|----|----|----|----|-------|
| broker_execution | US | Alpaca | 5 | 4 | 5 | 4 | 5 | 2 | 87 |
| broker_execution | US | Interactive Brokers | 4 | 3 | 2 | 4 | 3 | 3 | 66 |
| broker_execution | IN | Zerodha Kite | 5 | 4 | 2 | 3 | 4 | 3 | 75 |
| broker_execution | IN | Upstox | 4 | 4 | 3 | 3 | 4 | 3 | 72 |
| eod_bars, instrument_master | US | Massive | 5 | 4 | 5 | 4 | 3 | 3 | 85 |
| eod_bars, instrument_master | US | Alpaca Market Data | 3 | 4 | 5 | 3 | 5 | 3 | 74 |
| eod_bars | US | FMP | 3 | 2 | 4 | 2 | 4 | 3 | 58 |
| eod_bars | US | Finnhub | 2 | 3 | 4 | 2 | 3 | 2 | 52 |
| eod_bars, instrument_master | IN | Zerodha Kite | 3 | 3 | 4 | 2 | 4 | 3 | 62 |
| eod_bars | IN | Upstox | 3 | 4 | 2 | 2 | 5 | 3 | 62 |
| corporate_actions | US | Alpaca Market Data | 4 | 4 | 5 | 3 | 5 | 3 | 80 |
| corporate_actions | US | Massive | 4 | 2 | 5 | 3 | 3 | 3 | 68 |
| fundamentals | US | SEC EDGAR | 5 | 1 | 2 | 5 | 5 | 3 | 71 |
| fundamentals | US | FMP | 4 | 2 | 4 | 2 | 4 | 3 | 64 |
| fundamentals | US | Finnhub (free) | 3 | 3 | 4 | 2 | 5 | 2 | 62 |
| news | US | Alpaca News | 4 | 4 | 5 | 3 | 5 | 2 | 78 |
| news | US | Finnhub | 3 | 3 | 4 | 3 | 5 | 2 | 65 |
| macro | none | FRED | 4 | 4 | 5 | 5 | 5 | 3 | 86 |
| llm | none | DeepSeek | 5 | 4 | 4 | 3 | 5 | 2 | 81 |
| llm | none | OpenAI | 5 | 4 | 4 | 4 | 4 | 3 | 84 |

Arithmetic, one row shown in full: Alpaca broker = (30x5 + 20x4 + 15x5 + 15x4 + 10x5 + 10x2) / 5
= (150 + 80 + 75 + 60 + 50 + 20) / 5 = 435 / 5 = 87.

Notes on the scores:
- India daily bars tie at 62. Zerodha wins the tie: it adds no account and no second daily
  token.
- The LLM scores differ by 3 points in OpenAI's favour (a dated snapshot against an alias that
  is re-pointed). STACK-1 fixes DeepSeek as primary; the matrix does not overrule it. The
  difference is recorded, not acted on.
- SEC EDGAR's score rests on SECONDARY evidence for C1 and C4. It is shown so that the
  comparison exists; the capability is BLOCKED either way.
- Not scored, because no fact was verified: NSE Data & Analytics (India end-of-day licence), any
  India source for corporate actions, fundamentals, news or sector taxonomy, FBIL.

### 6.3 Selection

Status values: SELECTED (ready to specify a client), PROVISIONAL (chosen; a named question must
close before code), BLOCKED (chosen; cannot be used until a named item is resolved), UNFILLED
(no provider can be named from verified facts).

| ID | Capability | Market | Primary | Backup | Status | Open items |
|----|------------|--------|---------|--------|--------|------------|
| SEL-1 | broker_execution | US | Alpaca Trading API | none integrated; cold alternate Interactive Brokers | PROVISIONAL | OQ-33, OQ-34, OQ-35 |
| SEL-2 | broker_execution | IN | Zerodha Kite Connect | none integrated; cold alternate Upstox | PROVISIONAL | OQ-27, OQ-28, OQ-29, OQ-31 |
| SEL-3 | eod_bars | US | Massive, Developer plan | Alpaca Market Data, Basic plan, `feed=sip` | PROVISIONAL | OQ-38, OQ-36 |
| SEL-4 | eod_bars | IN | Zerodha Kite Connect historical | Upstox historical | BLOCKED | OQ-39, OQ-30 |
| SEL-5 | instrument_master | US | Massive tickers (class, listing status) with Alpaca assets (tradability) | none | PROVISIONAL | OQ-38 |
| SEL-6 | instrument_master | IN | Zerodha instrument dump | none | PROVISIONAL | OQ-30, OQ-40 |
| SEL-7 | corporate_actions | US | Alpaca Market Data | Massive | PROVISIONAL | OQ-36, OQ-38 |
| SEL-8 | corporate_actions | IN | none | none | UNFILLED | OQ-40 |
| SEL-9 | fundamentals | US | SEC EDGAR | FMP | BLOCKED | OQ-41, OQ-47 |
| SEL-10 | fundamentals | IN | none | none | UNFILLED | OQ-40 |
| SEL-11 | news | US | Alpaca News | Finnhub | PROVISIONAL | OQ-37, OQ-50 |
| SEL-12 | news | IN | none | none | UNFILLED | OQ-40 |
| SEL-13 | sector_taxonomy | US | none | none | UNFILLED | OQ-41, OQ-38 |
| SEL-14 | sector_taxonomy | IN | none | none | UNFILLED | OQ-40 |
| SEL-15 | calendar | US | NYSE published calendar, entered as a reviewed file | none | PROVISIONAL | OQ-36 |
| SEL-16 | calendar | IN | none | none | UNFILLED | OQ-49 |
| SEL-17 | macro | none | FRED | none | PROVISIONAL | OQ-42 |
| SEL-18 | fx_reference | none | none | none | UNFILLED | OQ-22 |
| SEL-19 | llm | none | DeepSeek, model `deepseek-flash` | OpenAI, model `gpt-4o-mini-2024-07-18` | PROVISIONAL | OQ-43, OQ-44 |
| SEL-20 | streaming quotes at order time | US | not selected; P3.2 decides whether it is needed | none | UNFILLED | OQ-36 |
| SEL-21 | streaming quotes at order time | IN | not selected; P3.2 decides whether it is needed | none | UNFILLED | OQ-31 |

SEL-20 and SEL-21 are recorded so that P3.2 finds the question; they are not `Capability`
values in section 8 and have no client.

No row is SELECTED. Seven capability rows are UNFILLED and two are BLOCKED. Five of the seven
UNFILLED capability rows and one BLOCKED row are India rows: the India data side is the weakest
part of the design, and INV-10 forbids going forward with the US side only.

Known recurring cost of the selection, from verified prices only: Massive Developer USD 79 per
month; Kite Connect INR 500 per month; Alpaca Basic data USD 0; FRED USD 0; LLM cost is per
token and is P0.3's to compute from F-57 and F-60. Unknown and therefore not totalled: the India
end-of-day licence, FMP, any India news, fundamentals or corporate-actions source.

Edge cases of the selection rules:
- A backup is promoted: this is ADR-07 T-3 (a data vendor changes for a model input). New
  entries in that market stop until a model trained on the backup's data is promoted. A backup
  for a model input is therefore a continuity-of-history measure, not a hot failover.
- Primary and backup disagree on a value: neither is averaged. The value from the primary is
  stored; the disagreement is recorded as a data-quality event; the instrument is quarantined
  (HITL-12) if the difference exceeds a threshold that P2.2 owns.
- The primary is down and the backup is up, for a non-model input (calendar, reporting rate):
  the backup may be used the same day, and the record says which source supplied the value.
- A provider is renamed or re-hosted (F-49): the base URL is a config value changed through
  HITL-5; the provider identity in `ProviderId` does not change.

## 7. What breaks if this provider dies at 09:31

09:31 is taken as one minute after the US open (09:31 `America/New_York`) for US providers and
09:31 `Asia/Kolkata`, sixteen minutes after the India open, for India providers. Under HP-1 to
HP-4 the decision was made after the previous close and the day's orders are already working.

| Provider | State at 09:31 | What breaks | What still works | Fail-closed action |
|----------|----------------|-------------|------------------|--------------------|
| Alpaca Trading | Entry limit orders working at the broker; `gtc` stops resting | No cancel, no replace, no new order, no fill events. A fill that happens is not seen, so the new position has no stop until the API returns. If the broker itself is down, resting stops may not execute. | Orders already at the venue, if only the API is down. | No new US orders. On return: reconcile over REST before anything else (D-14), then place missing stops (REC-4 order). The kill switch cannot flatten; the manual path is the broker's own console. |
| Alpaca Market Data | Not on the 09:31 path | Nothing at 09:31. After the close: no cross-check bars, no US corporate actions, no US news. Without corporate actions, tomorrow's orders cannot be confirmed against the share basis. | Orders and stops. | If corporate actions for the session are missing at the decision cycle: no US entries for the next session (INV-6). |
| Zerodha Kite | Entry limit orders working; GTTs held by Zerodha | As Alpaca Trading, and worse: a GTT is evaluated by Zerodha, so a Zerodha outage disables every India stop. A fill that occurs has no GTT until the API returns. | Orders already at the exchange. | No new India orders. HTTP 502 or 503, or `NetworkException`: treated as broker down. On return: reconcile, then place missing GTTs. Manual path: Kite web, which needs the same broker to be up. |
| Zerodha session (token invalidated, not an outage) | Same | Every authenticated call returns 403 `TokenException`. Identical to "no login" in [DEFAULT-6] from that moment. | Orders at the exchange and existing GTTs. | India disabled; alert; HITL-7. No automated re-login. |
| Upstox | Not integrated | Nothing. | Everything. | None. |
| Interactive Brokers | Not integrated | Nothing. | Everything. | None. |
| Massive | Not on the 09:31 path | Nothing at 09:31. After the close: no US daily bars. | Orders and stops. | No US decision cycle for that session (ADR-13 edge case: no decision on D-1's bar). The backup is not switched in automatically, because that is T-3. |
| Finnhub | Not on the 09:31 path | Nothing; it is a backup. | Everything. | None. |
| FMP | Not on the 09:31 path | Nothing; it is a backup. | Everything. | None. |
| SEC EDGAR | Blocked | Nothing. | Everything. | None. |
| FRED | Not on the 09:31 path | Nothing at 09:31. A macro series not updated by the decision cycle is missing data. | Orders and stops. | Features that need the series are absent; P2.6 owns whether the regime gate denies entries. A stale value is never reused as current (INV-6). |
| News (Alpaca News) | Not on the 09:31 path | The LLM packet for tonight's US candidates has no news. | The deterministic path. | The LLM is not called with an empty packet presented as "no news"; the candidate is handled as P4.2 decides for an unavailable LLM input. |
| DeepSeek | Not on the 09:31 path | The gated LLM step in tonight's cycle. | Everything deterministic. INV-1 and INV-2 mean no order depends on the LLM alone. | One attempt within our deadline (PE-14), then the fallback once, then the candidate proceeds or is dropped as P4.2 decides. |
| OpenAI | Not on the 09:31 path | Nothing unless DeepSeek is also down. | Everything. | If both are down: the LLM step is unavailable for the cycle; never retried in a loop. |
| NSE or BSE (exchange halt) | Session interrupted | No fills; GTTs do not trigger outside market hours; resting orders may be purged by the exchange. | Nothing in that market. | India disabled until the exchange resumes and reconciliation passes. |

## 8. Typed form

Entities this spec defines: the provider and capability vocabularies, a rate-limit fact, a
client throttle, a provider selection, the internal order reference, and the provider error
classes. Provider request and response objects are the providers' own; section 5 lists their
verified fields, and the client phases (P2.1, P3.1, P4.2) define the models that wrap them.

### 8.1 Models

`Market` is the P0.1 type. It is re-declared in the block only so the block runs alone.

```python
from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class Market(StrEnum):
    US = "US"
    IN = "IN"


class ProviderId(StrEnum):
    ALPACA_TRADING = "alpaca_trading"
    ALPACA_DATA = "alpaca_data"
    IBKR = "ibkr"
    ZERODHA_KITE = "zerodha_kite"
    UPSTOX = "upstox"
    MASSIVE = "massive"
    FINNHUB = "finnhub"
    FMP = "fmp"
    SEC_EDGAR = "sec_edgar"
    FRED = "fred"
    NSE_DATA = "nse_data"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


class Capability(StrEnum):
    BROKER_EXECUTION = "broker_execution"
    EOD_BARS = "eod_bars"
    INSTRUMENT_MASTER = "instrument_master"
    CORPORATE_ACTIONS = "corporate_actions"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    SECTOR_TAXONOMY = "sector_taxonomy"
    CALENDAR = "calendar"
    MACRO = "macro"
    FX_REFERENCE = "fx_reference"
    LLM = "llm"


MARKETLESS = frozenset({Capability.MACRO, Capability.FX_REFERENCE, Capability.LLM})


class SelectionStatus(StrEnum):
    SELECTED = "SELECTED"
    PROVISIONAL = "PROVISIONAL"
    BLOCKED = "BLOCKED"
    UNFILLED = "UNFILLED"


class VerificationLevel(StrEnum):
    PRIMARY_FULL = "PRIMARY_FULL"
    PRIMARY_EXTRACT = "PRIMARY_EXTRACT"
    SEARCH_EXCERPT = "SEARCH_EXCERPT"
    SECONDARY = "SECONDARY"


class LimitBasis(StrEnum):
    DOCUMENTED = "DOCUMENTED"
    EMPIRICAL = "EMPIRICAL"


class ProviderErrorClass(StrEnum):
    AUTH_EXPIRED = "AUTH_EXPIRED"
    IP_NOT_ALLOWED = "IP_NOT_ALLOWED"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_REQUEST = "INVALID_REQUEST"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    INSUFFICIENT_HOLDINGS = "INSUFFICIENT_HOLDINGS"
    ORDER_REJECTED = "ORDER_REJECTED"
    BACKEND_DOWN = "BACKEND_DOWN"
    SERVER_ERROR = "SERVER_ERROR"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    BALANCE_EXHAUSTED = "BALANCE_EXHAUSTED"


ClientOrderRef = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z0-9]{20}$")]
OpenItemRef = Annotated[str, StringConstraints(strict=True, pattern=r"^(OQ|BQ|UP)-[1-9][0-9]*$")]
HttpsUrl = Annotated[str, StringConstraints(strict=True, pattern=r"^https://[^\s]+$")]
ScopeText = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=120)]


class RateLimitFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    provider: ProviderId
    scope: ScopeText
    max_count: int = Field(ge=1)
    window_seconds: int = Field(ge=1)
    basis: LimitBasis
    verification: VerificationLevel
    source_url: HttpsUrl
    retrieved_on: date


class ClientThrottle(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    provider: ProviderId
    scope: ScopeText
    documented_max_count: int = Field(ge=1)
    client_max_count: int = Field(ge=1)
    window_seconds: int = Field(ge=1)

    @model_validator(mode="after")
    def _headroom(self) -> "ClientThrottle":
        if self.client_max_count * 2 > self.documented_max_count:
            raise ValueError("client budget must be at most half the documented limit")
        return self


class ProviderSelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    capability: Capability
    market: Market | None
    primary: ProviderId | None
    backup: ProviderId | None
    status: SelectionStatus
    blocked_by: tuple[OpenItemRef, ...] = ()

    @model_validator(mode="after")
    def _consistent(self) -> "ProviderSelection":
        if (self.market is None) != (self.capability in MARKETLESS):
            raise ValueError("market is None if and only if the capability is market-less")
        if (self.status is SelectionStatus.UNFILLED) != (self.primary is None):
            raise ValueError("primary is None if and only if status is UNFILLED")
        if self.primary is None and self.backup is not None:
            raise ValueError("a backup without a primary is not a selection")
        if self.primary is not None and self.primary == self.backup:
            raise ValueError("primary and backup must differ")
        if (self.status is SelectionStatus.SELECTED) != (len(self.blocked_by) == 0):
            raise ValueError("blocked_by is empty if and only if status is SELECTED")
        return self
```

Evidence: the block was executed on 2026-10-13 with Python 3.11.9 and Pydantic 2.13.5. Accepted:
a market-less SELECTED row, a BLOCKED row with one open item, an UNFILLED row with one open
item, a `RateLimitFact` for the Kite order limit, a `ClientThrottle` of 100 against a documented
200, and the reference `A1B2C3D4E5F6G7H8J9K0`. Rejected as expected: a market on a market-less
capability; no market on a per-market capability; SELECTED with no primary; a backup with no
primary; primary equal to backup; SELECTED with open items; BLOCKED with none; a lower-case open
item reference; a plain string for `primary`; `max_count` of 0; an `http` URL; a float count; a
string date; a client budget of 101 against 200; a client budget of 1 against 1; order
references that are lower case, 19 or 21 characters long, contain a hyphen, or end in a newline;
assignment after construction. Not run on Python 3.12 or later (R-4).

### 8.2 Fields

No field is nullable unless the table says so. Only `retrieved_on` carries a date; none carries
a time of day.

| Model.field | Type | Unit | Timezone | Nullable | Valid range | A violation means |
|-------------|------|------|----------|----------|-------------|-------------------|
| RateLimitFact.provider | ProviderId | none | none | no | a member of `ProviderId` | a limit recorded for a provider this spec did not examine; rejected (E-9) |
| RateLimitFact.scope | str | none | none | no | 1 to 120 characters | an unscoped limit cannot be applied to an endpoint; rejected (E-9) |
| RateLimitFact.max_count | int | requests, or orders where the scope says so | none | no | at least 1 | a limit of zero would be a prohibition, which is recorded as a legal fact, not a limit; rejected (E-9) |
| RateLimitFact.window_seconds | int | seconds | none | no | at least 1; a per-day limit is 86,400 | rejected (E-9) |
| RateLimitFact.basis | LimitBasis | none | none | no | `DOCUMENTED` or `EMPIRICAL` | a limit of unknown origin is a guess; rejected (E-9) |
| RateLimitFact.verification | VerificationLevel | none | none | no | one of four levels | rejected (E-9) |
| RateLimitFact.source_url | str | none | none | no | starts with `https://`, no whitespace | a fact with no source breaks RULE-2; rejected (E-9) |
| RateLimitFact.retrieved_on | date | calendar date | `Asia/Kolkata` [DEFAULT-12] | no | a `date` object | a string or datetime was passed; rejected (E-9) |
| ClientThrottle.documented_max_count | int | requests per window | none | no | at least 1; equals a `RateLimitFact.max_count` for the same provider and scope | E-10 |
| ClientThrottle.client_max_count | int | requests per window | none | no | at least 1 and at most half of `documented_max_count`, rounded down | the client could run closer to the limit than [DEFAULT-31] allows; rejected (E-10). A documented limit of 1 per window has no valid client count in that window: the window is doubled instead (THR-3) |
| ClientThrottle.window_seconds | int | seconds | none | no | at least 1 | E-10 |
| ProviderSelection.capability | Capability | none | none | no | a member of `Capability` | E-11 |
| ProviderSelection.market | Market or None | none | none | yes | None exactly when the capability is `macro`, `fx_reference` or `llm` | a per-market capability with no market is "US-only by accident" (INV-10); rejected (E-11) |
| ProviderSelection.primary | ProviderId or None | none | none | yes | None exactly when status is `UNFILLED` | E-11 |
| ProviderSelection.backup | ProviderId or None | none | none | yes | None, or a provider different from the primary; None for `broker_execution` (ADR-10) | E-11; a broker backup is additionally rejected by the check in E-12 |
| ProviderSelection.status | SelectionStatus | none | none | no | one of four values | E-11 |
| ProviderSelection.blocked_by | tuple of str | none | none | no | empty exactly when status is `SELECTED`; each item `OQ-n`, `BQ-n` or `UP-n` | a selection that claims to be ready while a question is open, or blocked with no reason; rejected (E-11) |
| ClientOrderRef | str | none | none | no | exactly 20 characters from `A-Z0-9` | the reference would be truncated or rejected by Kite (`tag` max 20, alphanumeric); the order is not sent (E-13) |

`ClientOrderRef` edge cases: it must be unique for the life of the system, not per day, because
Alpaca treats `client_order_id` as unique and a `gtc` order lives 90 days. 36^20 values exist;
how the 20 characters are generated (random, or derived from the audit record) is P3.1's
decision. A replacement order gets a new reference. Kite GTTs carry no `tag` in the documented
GTT order fields (F-10), so a GTT is matched by its `trigger_id`, stored at creation.

### 8.3 Client throttles ([DEFAULT-31])

| ID | Provider and scope | Documented limit | Basis | Client budget |
|----|--------------------|------------------|-------|---------------|
| THR-1 | Kite, order placement | 10 per second; 400 per minute; 5,000 per day (F-7) | DOCUMENTED | Governed by [DEFAULT-5]: one order per 3 seconds, at most 20 per minute. Far inside every Kite limit. |
| THR-2 | Kite, historical candles | 3 per second (F-7) | DOCUMENTED | 1 per second |
| THR-3 | Kite, quote | 1 per second (F-7) | DOCUMENTED | 1 per 2 seconds |
| THR-4 | Kite, all other endpoints | 10 per second (F-7) | DOCUMENTED | 5 per second |
| THR-5 | Alpaca Trading, all endpoints | 200 per minute per account (F-36, SEARCH_EXCERPT) | DOCUMENTED | 100 per minute |
| THR-6 | Alpaca Market Data, Basic, historical | 200 per minute (F-27) | DOCUMENTED | 100 per minute |
| THR-7 | Massive, paid plans | "unlimited" (F-48) | none stated | 5 per second [ASSUMPTION A-41]; OQ-38 |
| THR-8 | FRED | none stated (F-55) | none stated | 1 per second [ASSUMPTION A-41]; OQ-42 |
| THR-9 | Finnhub, free | 60 per minute; 30 per second overall (F-52, F-53) | DOCUMENTED | 30 per minute |
| THR-10 | FMP, Starter | 300 per minute (F-54) | DOCUMENTED | 150 per minute |
| THR-11 | DeepSeek | concurrency 2,500 (`deepseek-flash`) (F-57, F-58) | DOCUMENTED | 1 concurrent request |
| THR-12 | OpenAI, `gpt-4o-mini` | 5,000 requests per minute at the lowest listed tier (F-60) | DOCUMENTED | 1 concurrent request |

Edge cases:
- Two processes share one account's limit (the trading process and the kill switch, both on
  Alpaca's 200 per minute or Kite's 10 per second). The kill switch has its own credentials
  ([DEFAULT-4]) but not its own limit, because limits are per account. The trading process's
  budget is half the documented limit precisely so the other half is left for the kill switch.
- A provider answers 429 although the client is inside its budget: the budget for that scope is
  halved for the rest of the session and an alert is raised; the documented fact is re-checked
  (PE-3).
- `X-RateLimit-Remaining` (Alpaca data, F-28) reports less than the client's own count: the
  header wins.
- Windows are measured on the monotonic clock (NB-10).
- THR-7 and THR-8 are our pace, not the provider's limit. They may only be loosened after the
  open question is answered with a documented number.

## 9. Error paths

Each row is a provider failure and what the client does. "Order call" means place, modify or
cancel. No row permits a default or substituted value (INV-6).

| # | Condition | Seen as | Class | Fail-closed behaviour |
|---|-----------|---------|-------|-----------------------|
| PE-1 | Kite session expired or invalidated | HTTP 403, `TokenException` (F-8) | AUTH_EXPIRED | India disabled from that moment ([DEFAULT-6]). No automatic re-login. Alert. HITL-7. Orders at the exchange and GTTs are left as they are. |
| PE-2 | Alpaca or other key rejected | HTTP 401 or 403 on a non-order call | AUTH_EXPIRED | That provider is unavailable. No retry with the same key. Alert; HITL-14. A 403 on an Alpaca order call is PE-5, not this row. |
| PE-3 | Rate limit hit | HTTP 429 (Kite, Alpaca, Finnhub, DeepSeek, IBKR) | RATE_LIMITED | Data call: wait until the window resets (the `X-RateLimit-Reset` time where given, otherwise one full window), then at most 3 retries [ASSUMPTION A-42]; after that the job fails and the data is missing. Order call: not retried inside the session's order job; the order is recorded as not sent; alert. Budget halved (section 8.3). |
| PE-4 | Order placed from an unregistered address | Kite: rejection, body not verified (OQ-29). Upstox: `UDAPI1154` | IP_NOT_ALLOWED | India order path disabled; alert. Not retried. The fix is a human change to the IP registration, limited to one per week (UP-15). |
| PE-5 | Insufficient funds or shares | Alpaca HTTP 403 on an order; Kite `MarginException`, `HoldingException` | INSUFFICIENT_FUNDS, INSUFFICIENT_HOLDINGS | The order is not sent again. It means our cash or position state disagrees with the broker's: reconciliation runs before any further order in that market (HITL-8 if a difference remains). |
| PE-6 | Request rejected as invalid | Alpaca HTTP 422 or code `42210000`; Kite `InputException`, HTTP 400; Upstox `UDAPI10xx` | INVALID_REQUEST | Not retried. Recorded with the full response. It is a defect in our code or a stale tick size: the instrument is denied new entries until the instrument master is refreshed. Counts toward RISK-10 ([DEFAULT-5]) and toward Kite's 10 per second (F-16). |
| PE-7 | Order accepted, later rejected by the exchange or risk system | Alpaca status `rejected`; Kite status `REJECTED` with `status_message` | ORDER_REJECTED | Recorded. An entry is not re-sent in that session. A stop or GTT that is rejected leaves a position unprotected: placing the stop is retried once with corrected parameters if the reason is machine-readable, otherwise the position is escalated at once. |
| PE-8 | No response, or connection dropped, after an order call was sent | timeout | UNKNOWN_OUTCOME | Never re-sent blind. The order book is read and matched on `ClientOrderRef` (Alpaca `client_order_id`, Kite `tag`). Found: adopt it. Not found after the book is read successfully: the order was not placed; whether it is sent again is P3.1's rule, with a new audit record. Book unreadable: the market is disabled until it is readable. |
| PE-9 | India GTT triggered but its limit order did not fill | GTT status `triggered`; resulting order `OPEN` or `CANCELLED` at the close | ORDER_REJECTED | The position has no stop. A new GTT cannot fire again for the old one (single use). The system does not watch prices inside the session (HP-4), so it learns this only at reconciliation. Escalated; what is done next is P3.4's rule and OQ-27. |
| PE-10 | India market or `SL-M` order with protection did not fill | order `OPEN`, then `CANCELLED` at the close | ORDER_REJECTED | An emergency exit in India is not assumed complete until the fill is read back. An unfilled exit is escalated. |
| PE-11 | A resting stop or GTT is cancelled by the broker (90-day expiry at Alpaca, 365-day expiry or corporate action at Zerodha) | Alpaca status `expired` or `canceled`; GTT status `expired`, `cancelled`, `disabled` | ORDER_REJECTED | Every session, before entries: each open position is checked for a live stop; a missing one is placed first (REC-4 order). Stops are re-placed ahead of expiry: at 60 days for Alpaca and at 300 days for a GTT [ASSUMPTION A-42]. |
| PE-12 | Broker backend down | Kite HTTP 502, `NetworkException`; any HTTP 503 or 504 | BACKEND_DOWN | That market disabled. Reads are retried with backoff; order calls are not. On recovery: reconcile first. |
| PE-13 | Response does not match the documented shape: missing field, wrong type, unknown status or enum value | validation failure in our client | MALFORMED_RESPONSE | The value is not used. For an order or account response: the market is disabled and reconciliation is required. For data: the record is rejected and the instrument has no data for that session. An unknown status string is never mapped to the nearest known one. |
| PE-14 | LLM does not answer in time | our deadline of 120 seconds per call passes [ASSUMPTION A-42]; DeepSeek may hold a connection up to 10 minutes (F-58) | SERVER_ERROR | The connection is closed. One call to the fallback under the same deadline. Then the LLM step is unavailable for that candidate. No order depends on it (INV-2). |
| PE-15 | LLM account out of credit | DeepSeek HTTP 402 | BALANCE_EXHAUSTED | No retry. Fallback used for the rest of the cycle; alert; a human tops up (HITL-14 class of action). |
| PE-16 | A data provider returns an empty result for a session that the calendar says was open | empty `bars`, empty candle list | MALFORMED_RESPONSE | Empty is not zero volume and is not "no change". The bar is missing: no decision for that instrument (ADR-13 edge case). If more than a threshold of the universe is missing, the whole cycle is skipped; the threshold is P2.2's. |

Errors of the models in section 8:

| # | Condition | Detected by | Fail-closed behaviour |
|---|-----------|-------------|-----------------------|
| E-9 | A `RateLimitFact` field is missing, of the wrong type or out of range | Pydantic `ValidationError` | The fact is not recorded. A throttle cannot be built from it. |
| E-10 | A `ClientThrottle` budget exceeds half the documented limit | the model validator | The client process does not start. |
| E-11 | A `ProviderSelection` is inconsistent | the model validator | The selection table does not load. No client is constructed for any provider. |
| E-12 | A client is constructed for a selection whose status is not `SELECTED`, or a backup is given for `broker_execution` | a start-up check in each client phase's code | The process does not start. This is why no client can go live while section 6.3 has open items. |
| E-13 | A `ClientOrderRef` fails its pattern | Pydantic `ValidationError` | The order is not sent. |
| E-14 | A served LLM model version differs from the one recorded at the last promotion | comparison of the response's model field with the stored value | The LLM output is not used for that call; alert; treated as a T-3 event for the LLM path (P4.2 owns the rule). |

## 10. Documentation that could not be verified

Pages that were needed and were not read, or were reached and did not contain the fact. Nothing
from these is stated as fact anywhere above.

| # | URL or document | What was needed | Why it is unverified |
|---|-----------------|-----------------|----------------------|
| 1 | https://www.sec.gov/os/accessing-edgar-data and https://www.sec.gov/search-filings/edgar-application-programming-interfaces | EDGAR fair-access rate, `User-Agent` rule, endpoint list | Not requested: Owner's pause on SEC hosts |
| 2 | https://data.sec.gov (submissions and company-facts endpoints) | Field names and types | Not requested: same pause |
| 3 | https://kite.trade/docs/connect/v3/gtt/ and the Zerodha GTT article | Whether a GTT can place anything but a limit order | The two Zerodha pages disagree |
| 4 | Kite Connect terms and conditions (URL not located) | Automated login, data storage, redistribution | Page not located |
| 5 | https://kite.trade/forum/discussion/16212/batch-automating-kite-login and https://kite.trade/forum/discussion/9770/automating-retrieval-of-request-token | Staff statement on daily manual login | Search excerpt only |
| 6 | https://kite.trade/docs/connect/v3/historical/ | Adjustment of candles, range per request, history depth | Reached; not stated on the page |
| 7 | https://kite.trade/docs/connect/v3/websocket/ | Reconnect and replay behaviour | Reached; not stated |
| 8 | https://kite.trade/docs/connect/v3/orders/ | Zone of order timestamps; the place-order path; `guid` semantics; rejection list | Reached; not stated |
| 9 | https://alpaca.markets/support/usage-limit-api-calls | Trading API throttle of 200 per minute | Search excerpt only |
| 10 | https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf | Fee schedule | Search excerpt only |
| 11 | https://docs.alpaca.markets/reference/getaccount-1 | A settled-cash field | Reached; no such field described |
| 12 | https://docs.alpaca.markets/reference/patchaccountconfig-1 | Meaning of `max_margin_multiplier` = `"1"` | Reached; description absent |
| 13 | https://docs.alpaca.markets/docs/websocket-streaming and https://docs.alpaca.markets/docs/streaming-market-data | Heartbeat, connection limit, replay after reconnect | Reached; not stated |
| 14 | Alpaca references for cancel, replace, list orders, get order by client order id, positions, calendar, clock | Paths and fields | Not fetched in this run |
| 15 | https://alpaca.markets/support/countries-alpaca-is-available | Whether India is supported | Reached; the page has no list |
| 16 | Alpaca documentation sets "Alpaca India - Domestic" and "Alpaca India - GIFT City" (under docs.alpaca.markets) | What they offer an Indian resident | Seen only as names in page metadata |
| 17 | Alpaca customer agreement and market-data agreement | Automated trading, storage, redistribution, news text use | Not located |
| 18 | https://massive.com/docs (splits, dividends, ticker types, grouped daily, authentication, WebSocket) | Fields and behaviour | Not fetched; two pages were read |
| 19 | Massive terms and the "non-pros only" page | Individual-use restriction, storage | Not read |
| 20 | https://finnhub.io/docs/api (company-news endpoint) and Finnhub terms | Fields, storage and commercial-use terms | Not fetched |
| 21 | https://site.financialmodelingprep.com/developer/docs (statement endpoints) | Fields, filing dates, India coverage, Starter price | Pricing page read; price ambiguous; endpoints not fetched |
| 22 | https://fred.stlouisfed.org/docs/api/fred/ (errors and limits) | Numeric rate limit | Not stated on the two pages read |
| 23 | https://api-docs.deepseek.com (first call, chat completion reference, terms) | Base URL, auth header, model aliases, data terms | Not fetched; three pages were read |
| 24 | https://developers.openai.com/api/docs (deprecations, rate limits, data controls) | Shutdown date, tier limits, retention | Not fetched; one page was read |
| 25 | https://www.interactivebrokers.com/campus/ibkr-api-page/web-api-trading/ | Authentication detail, 2FA, order types | Reached by extraction; direct fetch returned HTTP 403; page dated 2024-12-17 |
| 26 | https://upstox.com/developer/api-documentation/v3/place-gtt-order/ | GTT v3 page | HTTP 404; the non-v3 path was read instead |
| 27 | Upstox terms; sandbox documentation | Unattended TOTP login, sandbox scope | Not fetched |
| 28 | https://www.nseindia.com/static/nse-terms-of-use | Exact clause on automated collection | Fetch timed out; search excerpt only |
| 29 | https://www.nseindia.com/static/market-data/eod-historical-data-subscription and https://www.nseindia.com/static/market-data/nse-data-policy | Price, licence, delisted coverage | Search excerpt only |
| 30 | https://www.nseindia.com/static/market-data/market-timings and https://www.nseindia.com/resources/exchange-communication-holidays | Session times and holidays | Search excerpt only; holiday list not seen |
| 31 | https://www.bseindia.com (trading hours, holidays, data products) | BSE equivalents | Not fetched |
| 32 | https://nsearchives.nseindia.com/content/circulars/INVG67858.pdf | NSE circular of 2025-05-05 on retail algo trading | Not fetched; cited by Upstox |
| 33 | SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 at sebi.gov.in | Full text (OQ-1) | Not fetched |
| 34 | https://www.fbil.org.in (reference rates) | USD/INR reference rate and its publication time (OQ-22) | Not fetched |
| 35 | Broker and vendor status pages (Alpaca, Zerodha, Massive, DeepSeek, OpenAI) | Outage history and maintenance windows | Not fetched |
| 36 | Exchange and broker settlement pages | T+1 settlement in both markets (A-27) | Not fetched |

## 11. Non-blocking details resolved in this spec

| # | Detail | Resolution |
|---|--------|------------|
| NB-28 | Money and price types from providers | Kite returns prices as JSON numbers (`float64`); Alpaca returns strings. Both are parsed into `Decimal` from the response text, never through a binary float (NB-3). A JSON parser is configured to read numbers as `Decimal`. |
| NB-29 | Kite WebSocket prices | Integers in paise; divided by 100 as `Decimal`. Not used by any decision in v1. |
| NB-30 | Timestamps | Alpaca: RFC 3339; examples are UTC; a timestamp without an offset is rejected (PE-13). Kite candles: `+0530`. Kite order timestamps: zone not documented; treated as `Asia/Kolkata` [ASSUMPTION A-39]. Massive `t`: Unix milliseconds, UTC by definition of Unix time. All are stored as UTC instants plus the exchange session date (NB-4). |
| NB-31 | Daily bar identity | A daily bar is keyed by market, instrument and session date, never by the vendor's timestamp, because vendors stamp daily bars differently (start of window, midnight UTC, midnight IST). |
| NB-32 | Request date bounds | Alpaca `start` and `end` are inclusive. Upstox `to_date` is inclusive. Kite `from` and `to`: inclusiveness not stated (OQ-30); the client requests one extra day on each side and discards rows outside the range. |
| NB-33 | Pagination | Alpaca `limit` counts points across all symbols, not per symbol; the client pages until `next_page_token` is null and treats a missing token field as PE-13. |
| NB-34 | Tick size | US: 2 decimals at or above USD 1.00, 4 below (F-21); a price is rounded to the tick toward the passive side (down for a buy limit, down for a sell stop). India: `tick_size` per instrument from the dump; same rounding rule. The rounding direction for a stop is confirmed by P3.4. |
| NB-35 | Lot size | India cash equities: `lot_size` from the dump is read, not assumed to be 1. Quantity is a multiple of it, rounded down (NB-22). |
| NB-36 | Alpaca `opg` and `cls` windows | Not used. Entries are `limit`, `day` orders submitted before the open ([RISK-13], HP-2). The 09:28 ET cutoff therefore does not apply. |
| NB-37 | GTC expiry arithmetic | 90 days are calendar days from creation; the cancel runs at 16:15 ET on the expiry date. Re-placement at 60 days leaves 30 calendar days of margin. |
| NB-38 | Kite token boundary | Expiry at 06:00 `Asia/Kolkata`; India has no daylight saving. A token obtained at 05:59 lasts one minute. Login is accepted by our system only after 06:00. |
| NB-39 | India evening window | A token obtained in the morning is valid until 06:00 the next day, so after the 15:30 close there are 14 hours 30 minutes in which the same token works. Whether next-session entries are placed in that window as after-market orders is P3.2's decision; it would not remove the morning login, because stops for new fills need a valid session during the next session. |
| NB-40 | DST and the LLM price windows | DeepSeek peak windows are fixed in UTC; the US close moves between 20:00 and 21:00 UTC with daylight saving; both are off-peak. |
| NB-41 | Percent units in fees | Fees are recorded as written by the provider (0.1% is stored as 0.1 under A-4); the SEC fee is a multiplier of trade value (0.0000206), stored as a rate with its unit stated. |
| NB-42 | Fee rounding | Alpaca rounds regulatory fees up to the cent (F-37). P5.3 models that, not half-even. |
| NB-43 | API keys in URLs | Where a provider accepts a key as a query parameter or as a header (Finnhub; FRED takes it only as a parameter), the header is used when available; for FRED the URL is never logged with its query string. |
| NB-44 | 09:31 | Read as local exchange time of the provider's market (section 7). |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| D-11 | Selections SEL-1 to SEL-21 as in section 6.3; none is SELECTED; the spec stays DRAFT. | ADR-11: a phase is not frozen for one market. Facts are missing, mostly for India. | Yes. | Every client phase. |
| D-12 | US daily bars come from Massive (Developer plan, 10 years), with Alpaca Market Data as backup. | INV-10 requires a data provider separate from the broker; highest score; point-in-time ticker reference. | Yes; a switch is a T-3 event. | P2.1, P2.3, P5.x. |
| D-13 | Raw bars and corporate actions are stored separately; adjustment is ours. Requests use `adjusted=false` (Massive) and `adjustment=raw` (Alpaca). | [DEFAULT-26]; point-in-time integrity; vendor restatements must not move stored values. | Costly after data is stored. | P2.1, P2.4. |
| D-14 | No WebSocket stream is a system of record. State is read over REST after every disconnect and at least once per session. | No provider documents replay of missed events (F-12, F-30, F-31, F-44). | Yes. | P3.1, P5.5. |
| D-15 | No order call is retried blind. An unknown outcome is resolved by reading the order book and matching `ClientOrderRef`. | Kite has no idempotency key; Alpaca's duplicate behaviour is unverified. | Yes. | P3.1. |
| D-16 | Credentials are sent in headers wherever the provider accepts them. | A key in a URL reaches logs. | Yes. | P6.2. |
| D-17 | Before India goes live, the recovery host's address is registered as Zerodha's secondary static IP. | UP-15: one IP change per calendar week against an RTO of 4 hours. | Yes. | P6.4, ADR-10. |
| D-18 | LLM model identifiers are `deepseek-flash` and `gpt-4o-mini-2024-07-18`; the served model version is recorded with every call. | UP-18. | Yes. | P4.2, P0.3. |
| D-19 | The India resting stop is a single-leg sell GTT ([DEFAULT-22]); the US resting stop is a `stop`, `gtc` order ([DEFAULT-23]); whole shares only ([DEFAULT-24]). | F-9, F-10, F-21, F-23. | Yes. | P2.10, P3.4. |
| D-20 | Interactive Brokers and Upstox are cold alternates: documented here, not integrated, not funded. | ADR-10; UP-19. | Yes, by new ADR. | None while unused. |
| D-21 | SEC EDGAR is not contacted and no client for it is written until the Owner lifts the pause and names the contact identity for the `User-Agent`. | Owner's instruction; [DEFAULT-28]. | Yes. | US fundamentals features. |
| D-22 | Client request budgets are at most half of each documented limit (THR-1 to THR-12). | [DEFAULT-31]; the kill switch shares the account limit. | Yes. | Backfill duration. |
| D-23 | The decision matrix of section 6.1 (six criteria, weights 30/20/15/15/10/10) is the selection method; a constitution-fixed provider is primary regardless of score. | The prompt requires a weighted matrix; INV-10 and STACK-1 are not open to redesign. | Yes. | Selections. |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| A-37 | The PRIMARY_EXTRACT facts in section 3 state their source pages accurately. | They were read through automated extraction, not line by line. | Full read by the phase named in the register. | Any field name, limit or fee in section 5. |
| A-38 | [DEFAULT-22] to [DEFAULT-31] as given in section 1. | Each is a fork with no Owner ruling. | Owner reviews BQ-11 to BQ-20. | As stated per row in section 1. |
| A-39 | Kite order and trade timestamps without an offset are `Asia/Kolkata`. | The page does not state the zone. | OQ-30. | Fill times wrong by 5 hours 30 minutes in the audit trail. |
| A-40 | A request to `GET /v2/account/configurations` style paths and the Kite place-order path follow the patterns shown in section 5. | Derived from reference page names and sibling paths, not read. | OQ-31, OQ-34. | Client code fails at first call; no trading risk. |
| A-41 | Client pace of 5 requests per second for Massive and 1 per second for FRED. | No numeric limit is published on the pages read. These are our pace, not a claimed limit. | OQ-38, OQ-42. | A 429 or a block during backfill. |
| A-42 | Three retries on a data 429; LLM deadline 120 seconds; stops re-placed at 60 days (Alpaca) and 300 days (GTT). | No data to derive them; chosen inside the documented lifetimes (90 and 365 days, 10-minute server timeout). | P3.4, P4.2, P6.1 after paper trading. | Slow cycles, or a stop that lapses if the re-placement job fails for 30 or 65 consecutive days. |
| A-43 | DeepSeek's `$` prices are US dollars. | The page gives no currency code. | OQ-43. | LLM budget in P0.3. |
| A-44 | The 10 orders per second threshold and the static-IP rule apply to this account as an individual client running its own logic. | Read from broker pages, not from the SEBI or NSE circular. | OQ-51, OQ-1. | Registration requirements in P6.3. |
| A-45 | Alpaca's Trading API limit is 200 requests per minute per account. | Seen only as a search excerpt of Alpaca's support article. | Read the article; OQ-34. | THR-5. |
| A-46 | Zerodha's static-IP requirement took effect on 1 April 2026. | The article says 2026; the FAQ says 2025; the staff forum post is dated late March with a 1 April deadline. | OQ-29. | None for a system going live after both dates. |

A-33 and A-27 of P0.1 remain assumptions (OQ-48). A-26 is confirmed for the regular-session
times of NYSE (PRIMARY_EXTRACT) and NSE (SEARCH_EXCERPT).

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| OQ-27 | UP-11: does the Owner accept a single-use, limit-order GTT as the India "resting stop", and can a Kite API GTT place a market order with protection? | Owner; Zerodha | Ruling on UP-11. kite.trade/docs/connect/v3/gtt (order_type); Kite forum, search "GTT market order API" | P2.10, P3.4, India go-live |
| OQ-28 | Do Kite Connect's terms prohibit automated login, and what is the exchange rule requiring a daily manual login? | Zerodha | Kite Connect terms on developers.kite.trade; forum threads 16212 and 9770 read in full | P3.1 |
| OQ-29 | Zerodha static IP: effective date; response to an order from an unregistered address; whether GTT, modify and cancel calls are IP-checked. | Zerodha | support.zerodha.com article "static-ip"; kite.trade/forum/discussion/15912 | P3.1, P6.4 |
| OQ-30 | Kite historical data: are daily candles adjusted for splits, bonus issues and dividends; maximum range per request; history depth; inclusiveness of `from`/`to`; zone of order timestamps. | Zerodha | kite.trade/docs/connect/v3/historical; Kite forum FAQ thread 4732 | P2.1 |
| OQ-31 | Kite: place-order path confirmation; `guid` semantics; is a duplicate `tag` rejected; WebSocket reconnect and replay; after-market order behaviour. | Zerodha | kite.trade/docs/connect/v3/orders and /websocket; pykiteconnect source | P3.1, P3.2 |
| OQ-32 | Kite: list of order rejection reasons (`status_message`); outage history and maintenance windows. | Zerodha | Kite forum; Zerodha status and bulletin pages | P3.1, P3.4 |
| OQ-33 | Alpaca (rest of OQ-15): which field or method gives settled cash; what `max_margin_multiplier="1"` does; can an account be cash-only (UP-21); how a same-day stop exit is treated under the intraday margin framework. | Alpaca | docs.alpaca.markets: account, account configurations, margin; Alpaca support | P2.8, P2.9 |
| OQ-34 | Alpaca Trading API: paths and fields for cancel, replace, list, get-by-client-order-id, positions; response to a duplicate `client_order_id` and its charset; 429 body and headers; stream heartbeat and replay; treatment of a `gtc` stop on a split; minimum and maximum quantity; complete rejection codes; IP allowlisting. | Alpaca | docs.alpaca.markets/reference (orders, positions); alpaca.markets/support/usage-limit-api-calls | P3.1, P3.4 |
| OQ-35 | Alpaca and India (OQ-6, OQ-14 widened): is an Indian resident eligible for a US live account; what are "Alpaca India - Domestic" and "Alpaca India - GIFT City"; do they change the LRS analysis in UP-4? | Alpaca; a qualified adviser | Alpaca support; docs.alpaca.markets India documentation sets | US go-live, P6.3 |
| OQ-36 | Alpaca Market Data: are bars served for delisted symbols; corporate-actions history depth; calendar and clock endpoint fields; how the daily bar session is defined. | Alpaca | docs.alpaca.markets/reference (stock bars, corporate actions, calendar) | P2.1 |
| OQ-37 | May Alpaca bars and news be stored indefinitely, and may news text be sent to DeepSeek or OpenAI for processing? | Alpaca; Benzinga | Alpaca market data agreement; Alpaca customer agreement | P2.1, P4.1 |
| OQ-38 | Massive: bars for delisted tickers; `active=false`; ticker `type` codes for common stock, ETF and depositary receipt; split and dividend endpoints; whole-market daily endpoint; daily bar zone; fair-use behind "unlimited"; 429 behaviour; auth header; non-professional and storage terms; sector or SIC field. | Massive | massive.com/docs/rest/stocks; massive.com terms; the "non-pros only" page | P2.1, P2.3 |
| OQ-39 | India whole-market daily history including delisted stocks: product, price, licence and format from NSE Data & Analytics; the BSE equivalent (part of OQ-19). | NSE Data & Analytics; BSE | nseindia.com/static/market-data/eod-historical-data-subscription; NSE data policy; bseindia.com data products | P0.3, P2.1, P2.3, P5.x |
| OQ-40 | India sources, with licence, for corporate actions, fundamentals, news, sector classification and ISIN mapping. | NSE, BSE, data vendors | NSE and BSE corporate-filings data products; vendor coverage pages (FMP Ultimate, Finnhub) | P2.1, P2.3, P4.1 |
| OQ-41 | SEC EDGAR: will the Owner lift the pause; which contact identity goes in the `User-Agent`; then the primary facts (rate, endpoints, fields, SIC as a sector source). | Owner; SEC | Owner decision; then sec.gov "Accessing EDGAR Data" and the EDGAR API page | P2.1, P2.3 |
| OQ-42 | FRED: numeric rate limit and 429 body; representation of a missing observation; whether storing observations is permitted; a source for India macro series. | Federal Reserve Bank of St. Louis; RBI | fred.stlouisfed.org/docs/api/fred (errors); FRED terms read in full; RBI database pages | P2.1 |
| OQ-43 | DeepSeek: base URL and auth header; is `deepseek-chat` still accepted; can a dated version be pinned; default output limit; currency of prices; data retention, training use and processing location. | DeepSeek | api-docs.deepseek.com: first API call, chat completion reference, model list; DeepSeek terms and privacy policy | P0.3, P4.2 |
| OQ-44 | OpenAI: shutdown date of `gpt-4o-mini`; the account's usage tier; data retention terms; 429 body. | OpenAI | developers.openai.com/api/docs: deprecations, rate limits, data controls | P0.3, P4.2 |
| OQ-45 | Interactive Brokers: 2FA and daily login for the gateway; session lifetime; customer order id; order types and time in force; API permissions for Indian residents. | Interactive Brokers | IBKR Campus Web API pages | Only if the alternate is activated |
| OQ-46 | Upstox: may the TOTP token endpoint be called unattended; maximum GTTs; `extended_token` validity; sandbox scope; adjustment and delisted coverage of historical candles. | Upstox | upstox.com/developer/api-documentation: get-token, sandbox, expired instruments; Upstox terms | P2.1 for the history backup; otherwise only if activated |
| OQ-47 | FMP: Starter price (USD 19 or USD 49); Ultimate price; India coverage; do statements carry filing and acceptance dates; endpoint fields. | FMP | site.financialmodelingprep.com pricing and developer docs | P0.3, P2.1 |
| OQ-48 | Settlement cycle in both markets (A-27); is a same-day buy and sell under `CNC` charged and taxed as intraday (A-33). | Exchanges; Zerodha | NSE and BSE settlement pages; a US clearing or FINRA page on T+1; zerodha.com/charges; Zerodha support | P2.8, P5.3 |
| OQ-49 | NSE and BSE: exact pre-open order-collection close; holiday and special-session lists for 2026 and 2027; BSE session times (rest of OQ-26). | NSE, BSE | nseindia.com/resources/exchange-communication-holidays; bseindia.com trading holidays | P2.1 |
| OQ-50 | Finnhub: company-news endpoint fields; what "Personal Use" permits; storage; India coverage. | Finnhub | finnhub.io/docs/api/company-news; finnhub.io terms of service | P4.1 |
| OQ-51 | Rest of OQ-1: for an unregistered client strategy under 10 orders per second, who generates the exchange order tag and does the client send anything; is the threshold counted per exchange, per segment or per client. | NSE; SEBI; Zerodha | NSE circular INVG67858 (2025-05-05) and INVG69255 (2025-07-22); the NSE retail-algo FAQ of 2025-11-03; SEBI circular text | P2.9, P6.3 |

Upstream questions answered or narrowed by this spec:
- OQ-7: answered in substance (F-6; F-20 as excerpt). The terms text remains OQ-28.
- OQ-11: answered. US: `stop`, `gtc`, 90 days. India: no resting stop order; GTT, 365 days,
  with the limits in UP-11.
- OQ-15: partly answered. No borrowing-prevention setting is described beyond
  `max_margin_multiplier` and `no_shorting`; no settled-cash field; fractional orders are `day`
  only. The rest is OQ-33.
- OQ-1: partly answered (10 orders per second per client; static IP for order placement). The
  rest is OQ-51.
- OQ-19: narrowed to OQ-38 (US) and OQ-39 (India). The counts of listed and delisted stocks
  were not obtained.
- OQ-26: NYSE answered; NSE by excerpt; BSE and settlement open (OQ-48, OQ-49).
- OQ-22: not addressed; still open.
- OQ-6, OQ-14: not answered; widened by OQ-35.

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| F-6..F-64 | external fact identifier | Section 3 row, cited as `F-n`, with its verification level | every later spec that states a provider fact |
| DEFAULT-22..DEFAULT-31 | provisional default identifier | Section 1, cited as `[DEFAULT-n]`; not a ruling | P2.1, P2.8, P2.10, P3.1, P3.4, P0.3 |
| ProviderId | type | `StrEnum`, 13 members, section 8.1 | P1.1, P2.1, P3.1, P4.2, P6.1 |
| Capability | type | `StrEnum`, 11 members, section 8.1 | P2.1, P3.1, P4.1, P6.1 |
| SelectionStatus | type | `StrEnum`: `SELECTED`, `PROVISIONAL`, `BLOCKED`, `UNFILLED` | every client phase (start-up check E-12) |
| VerificationLevel | type | `StrEnum`: `PRIMARY_FULL`, `PRIMARY_EXTRACT`, `SEARCH_EXCERPT`, `SECONDARY` | X3 merge; later fact registers |
| LimitBasis | type | `StrEnum`: `DOCUMENTED`, `EMPIRICAL` | P3.1, P6.1 |
| ProviderErrorClass | type | `StrEnum`, 12 members, section 8.1; mapping in section 9 | P1.4 (audit event field), P3.1, P3.4, P6.1 |
| ClientOrderRef | type | strict `str`, pattern `^[A-Z0-9]{20}$` | P1.1, P1.4, P3.1, P5.5 |
| RateLimitFact | type | frozen Pydantic v2 model, 8 fields, section 8.2 | P3.1, P6.1 |
| ClientThrottle | type | frozen Pydantic v2 model, 5 fields; client budget at most half the documented limit | P2.1, P3.1, P4.2 |
| ProviderSelection | type | frozen Pydantic v2 model, 6 fields, validator in section 8.1 | P0.3, P2.1, P3.1, P4.1, P4.2 |
| SEL-1..SEL-21 | selection identifier | Section 6.3 row | P0.3 and every client phase |
| THR-1..THR-12 | client throttle identifier | Section 8.3 row | P2.1, P3.1, P4.2, P6.1 |
| PE-1..PE-16 | provider error path identifier | Section 9 row: condition, class, fail-closed behaviour | P3.1, P3.4, P2.10, P5.5 |
| `massive.base_url`, `alpaca.trading_base_url`, `alpaca.data_base_url`, `kite.base_url` | config key | `str`, an `https://` URL; changed only through HITL-5 | P1.3, P2.1, P3.1 |
| `llm.primary_model`, `llm.fallback_model` | config key | `str`; decided values `deepseek-flash`, `gpt-4o-mini-2024-07-18` (D-18) | P1.3, P4.2 |
| `stops.us_replace_after_days`, `stops.in_gtt_replace_after_days` | config key | `int`, days; decided values 60 and 300 [ASSUMPTION A-42]; valid range 1 to 89 and 1 to 364 | P1.3, P3.4 |
