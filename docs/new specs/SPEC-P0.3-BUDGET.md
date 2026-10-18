---
id: SPEC-P0.3-BUDGET
version: 0.1
status: DRAFT
phase: P0.3
depends_on: [SPEC-A-CONSTITUTION, SPEC-P0.1-DECISIONS, SPEC-P0.2-PROVIDERS]
produces: [F-65..F-76, DEFAULT-32..DEFAULT-41, CostBasis, PipelinePath, StageAnchor, OverrunAction, CostLine, StageBudget, LlmBudget, ContainerLimit, CapacityPlan, CL-01..CL-19, STG-A0..STG-K4, LARGEST_VM_IN_BUDGET, SENS-1]
---

> **Model B notice (2026-10-14).** The Owner chose signals only for v1 (no order routing, no broker integration, no handling of user funds). This spec's text below is unchanged. Where it concerns orders, brokers or accounts it is superseded or deferred as listed in `MODEL-B-DECISION.md` section 6, and Block A items are read with the amendments BA-1 to BA-6 there. Phases are re-run per `ROADMAP-V1.md`.

# SPEC-P0.3 — Cost, Capacity and Latency Budget (new run)

Date: 2026-10-13. Decision owner: Owner. Author: systems engineer (this run).

Inputs consumed: `CONSTITUTION.md` v0.3 (SPEC-A-CONSTITUTION), `SPEC-P0.1-DECISIONS.md` v0.1 and
`SPEC-P0.2-PROVIDERS.md` v0.1, all as supplied in full with the phase prompt. No other repository
file was read (N-3).

Run notes:
- This phase ran in a fresh conversation, as the pack requires.
- No request was made to `sec.gov`, `data.sec.gov` or `efts.sec.gov`. No account was created, no
  terms were accepted, no credential was read, no authenticated API was called, and no personal
  information was sent in any request. Every new external fact comes from a public pricing or
  documentation page and is listed in section 3 with its verification level.
- Identifier series continue from P0.2 (D-10): BQ-21, DEFAULT-32, UP-26, F-65, NB-45, D-24, A-47,
  OQ-52, E-15 onward.
- Arithmetic in this spec was checked with Python 3.11.9 `Decimal`. Every computed number shows
  its inputs so it can be redone by hand.

Status: DRAFT. It cannot be frozen while SPEC-P0.2 is DRAFT, because five India data capabilities
have no provider and therefore no price (section 9.2).

Units used throughout: 1 GB = 10^9 bytes; 1 GiB = 2^30 bytes; 1 MiB = 2^20 bytes. Money is USD
unless marked INR. A "month" for session arithmetic is 21 sessions (252 / 12, A-25).

Contents: 1 blocking questions; 2 upstream problems; 3 evidence register; 4 sizing inputs;
5 data volume; 6 ingest throughput; 7 LLM spend; 8 VM sizing; 9 monthly cost model; 10 latency
budget; 11 backtest cost; 12 sensitivity table; 13 typed form; 14 error paths; 15 non-blocking
details; then the four tables.

## 1. Blocking questions and the defaults used

| # | Question | Options | Default used | If the default is wrong |
|---|----------|---------|--------------|-------------------------|
| BQ-21 | What does the "USD 200 to 500 per month ceiling" in the phase prompt cover? No input spec defines it (UP-27). | (a) LLM spend only; (b) all recurring platform cost: VM, storage, data subscriptions, LLM; (c) everything including trading charges and taxes | [DEFAULT-32] (b). Trading charges are per trade and belong to P5.3; taxes on invoices are unpriced (CL-16). Section 7.4 answers the question under reading (a) as well. | Under (a) the ceiling is irrelevant to this design (section 7.4). Under (c) the priced total in section 9 already uses 97% of the lower bound (194.20 / 200) before a single trade. |
| BQ-22 | Which provider and region host the single VM? Upstream names none. | (a) DigitalOcean, Bangalore; (b) AWS Lightsail, Mumbai; (c) any other | [DEFAULT-33] (a): Basic Droplet, 16 GiB, 8 shared vCPU, 320 GiB SSD, USD 96 per month (F-65). Chosen over (b) because its page states an hourly rate, per-second billing with a monthly cap, and the price of a reserved address held unassigned (F-66), all of which this spec needs; Lightsail's burstable CPU baseline is not quantified on the pages read (F-69, OQ-55). | CL-01, CL-03, CL-04 change. At Lightsail prices the total falls by USD 12 (section 12.3). Nothing else in the design depends on the provider. |
| BQ-23 | Is daily history stored for the whole listed market or for the universe only? | (a) universe only, 1,000 instruments; (b) whole market, both India exchanges | [DEFAULT-34] (b). ADR-14 requires the whole market for the UNI-1 ranking. India is sized as NSE plus BSE with no overlap removed, which is an upper bound. | Under (a) storage is 21 times smaller (section 5.2) and UNI-1 cannot be computed. |
| BQ-24 | Where do backtests, retrains and hyperparameter searches run? STACK-1 allows one VM. | (a) on the live VM, unrestricted; (b) on the live VM, in a container with a memory and CPU cap that is paused while any live path runs; (c) on a second, temporary VM | [DEFAULT-35] (b). (c) is outside STACK-1 as written. | Under (a) an offline job can make the decision cycle miss its deadline, which counts toward the ADR-03 capacity trigger for a reason that is not capacity. |
| BQ-25 | Is the LLM called inside a walk-forward backtest? | (a) no; (b) yes, for every gated candidate of every out-of-sample session | [DEFAULT-36] (a). Cost under (b) is given in section 11.3 so the Owner can see it. | Under (b) one 10-year run costs USD 148 to 212 in LLM calls, and the result is contaminated by the model's knowledge of the period. |
| BQ-26 | How large may one LLM call be? P4.1 bounds the packet but gives no number yet. | planning figure only; planning figure plus hard caps | [DEFAULT-37] Planning: 8,000 input and 1,500 output tokens per call. Hard caps: 32,000 input and 4,000 output tokens per call, enforced before the call is sent. | If real packets are larger than the cap, P4.1 must truncate or the candidate gets no LLM call. If they are larger than the planning figure, section 7 scales linearly up to the cap. |
| BQ-27 | What is the hard deadline of the daily decision cycle, and when may orders be submitted? | deadline at close + 4 h, + 6 h or + 8 h; submission before the open or from the open | [DEFAULT-38] Cycle deadline: session close + 21,600 s (6 h). Order job: pre-checks from next open - 1,800 s; first submission at the open; last submission at open + 600 s; job ends at open + 900 s. | A shorter deadline cannot hold gate width 50 (section 10.2). Pre-open submission may be better for fills, but neither broker's pre-open acceptance is verified (OQ-66); P3.2 may move the window. |
| BQ-28 | Is ingest of the whole market on the decision path? | (a) yes, the cycle waits for every instrument; (b) no: universe and held instruments first and blocking, the rest in the background | [DEFAULT-39] (b). | Under (a) the India ingest alone takes 2 h 27 min at the Kite throttle (section 6.2) and the fixed part of the cycle grows from 122 to 249 minutes. |
| BQ-29 | How is the ADR-10 RPO of 60 seconds implemented, and how long is the archive kept? | (a) 16 MB WAL segments (PostgreSQL default), `archive_timeout` 60 s; (b) 1 MB segments chosen at `initdb`; retention 7 or 30 days | [DEFAULT-40] (a), with a 7-day point-in-time window and 7 daily base backups. The default segment size is kept because it cannot be changed after `initdb` (F-71) and the cost of keeping it is under USD 1 a month (section 9.3). | With 30-day retention the archive reaches 675 GiB and adds about USD 11 a month. |
| BQ-30 | Do protective stop and GTT placements count toward the RISK-10 and RISK-11 spacing of [DEFAULT-5], and in what order relative to entries? | (a) they count, stops first; (b) they count, in arrival order; (c) they do not count | [DEFAULT-41] (a). [DEFAULT-5] says new orders, modifications and exits count; a stop is all three in turn. A stop for a detected fill is queued ahead of every unsent entry. | Under (c) a burst of stops could exceed the exchange per-second threshold (F-2). Under (b) a filled position waits behind unsent entries without a stop. |

## 2. Problems in the upstream material

RULE-5 requires this section.

| # | Where | Problem | Handling in this spec |
|---|-------|---------|-----------------------|
| UP-26 | P0.3 prompt, COMPUTE and LATENCY BUDGET | The prompt assumes minute bars, a streaming ingest whose worst minute is the open, and an "intraday-exit path". ADR-13 decided otherwise: daily bars only (HP-1), no streaming data on any decision path (P0.2 section 4), and inside a session only the broker-resting stop and the kill switch can sell (HP-4). The system has no intraday exit pipeline. | Everything is sized for what was decided. The prompt's figures for 1-minute and 5-minute bars, the open-minute stream and an intraday exit are given as labelled comparisons (sections 5.3, 6.4, 7.3, 10.6). The intraday paths that do exist under the decided design are budgeted instead: placing the stop after a fill (10.4) and the kill-switch flatten (10.5). |
| UP-27 | P0.3 prompt, "the $200-500/month ceiling" | No declared input states this ceiling, what it covers, or who set it. | BQ-21, [DEFAULT-32]. OQ-52. |
| UP-28 | ADR-13, "Storage volume" row | It computes 2,520,000 daily rows for 1,000 universe instruments and states "swing needs about 1/382 of the rows". ADR-14 requires the whole listed market at daily frequency. On the counts in section 4 that is 53,708,760 rows, 21.3 times the ADR-13 figure. The honest ratio between the decided design and universe-only 1-minute bars is 1/17.9, not 1/382. The row itself flags OQ-19, so it is incomplete rather than wrong. | Section 5 sizes the whole market. |
| UP-29 | ADR-10, "RPO 60 seconds by forcing a write-ahead-log segment to the off-VM archive at least every 60 seconds" | PostgreSQL documents that a segment closed early by a forced switch is archived at full length and that a very short `archive_timeout` bloats the archive (F-70). At the default 16 MB segment that is up to 22.5 GiB of archive per day (section 9.3). ADR-10 lists the cost of option C as "one storage bucket and archive configuration". | Sized in section 9.3; fits the chosen bucket at 7-day retention. Whether the tail of a forced segment compresses is OQ-64. |
| UP-30 | P0.2 PE-14 with THR-11 and THR-12 | A 120-second deadline per call, one fallback attempt, and one concurrent request give a worst case of 240 seconds per candidate. Nobody upstream multiplied it out: 40 minutes at gate width 10, 200 minutes at 50. The LLM stage, not compute, is the longest VM-side stage of the cycle. | Section 10.2 budgets 240 s per gate unit and sets the cycle deadline so that width 50 still fits. |
| UP-31 | ADR-14 "Order rate" row; constitution Q4 | ADR-14 says "a cycle that opens 20 positions needs 20 orders: 57 seconds at the spacing in [DEFAULT-5]". That uses the 3-second global spacing only. [DEFAULT-5] also sets 6 seconds between two submissions of one strategy; with one strategy 20 entries take 19 x 6 = 114 seconds. Each fill also needs a protective stop, which [DEFAULT-5] counts ("exits count"): 20 entries plus 20 stops are 40 submissions, 39 x 6 = 234 seconds for one strategy. | Section 10.3 and 10.4 use 114 and 234 seconds. Both still fit the window. BQ-30. |
| UP-32 | P0.2 SEL-4 (India daily bars from Kite historical) with [DEFAULT-6] and THR-2 | Two consequences were not drawn. First, Kite data calls need the daily token, so on a day with no human login (HITL-7) there is no India ingest at all, not only no India orders. Second, at the client budget of 1 request per second, one request per instrument, the whole India market takes 8,803 seconds (2 h 27 min) per session. | Section 6.2. [DEFAULT-39] keeps this off the decision path. A missed day is backfilled as a data job at the next opportunity (ADR-02); the decision for that session is skipped (ADR-13 edge case). |
| UP-33 | P0.2 D-17 (recovery address registered as Zerodha's secondary static IP) | It has a recurring cost that P0.2's "known recurring cost" does not list: an address reserved and not attached is billed (F-66: USD 5.00 per month). | CL-03. |
| UP-34 | INV-8 "strategy changes are offline", ADR-07, ADR-08, STACK-1 | "Offline" work (quarterly retrain, walk-forward backtest, hyperparameter search) has no host other than the live VM. A 50-trial search is 280 hours of compute on the assumptions of section 11. STACK-1 and ADR-03 do not say how offline work is kept from starving the live path. | BQ-24, [DEFAULT-35], section 8.3. |
| UP-35 | STACK-1 "DeepSeek (primary) + GPT-4o-mini (fallback)" with F-57 and F-60 | On the recorded prices the fallback is not the more expensive model: `gpt-4o-mini` costs USD 0.15 and 0.60 per million input and output tokens; `deepseek-flash` costs USD 0.30 and 1.20 at peak and 0.15 and 0.60 off-peak. The fallback is half the primary's peak price and equal to its off-peak price. | Not a contradiction; STACK-1 stands. Recorded so that nobody justifies the ordering by cost. Section 7.1. |
| UP-36 | P0.2 F-48, [DEFAULT-25] (Massive Developer, 10 years, USD 79) | "10 years" is presumably a rolling window from today. Ten years are needed once, for the backfill; the nightly ingest needs one day. After the backfill the Starter plan (USD 29, 5 years, unlimited calls, end-of-day capable) would serve the nightly job, saving USD 50 a month, if the terms allow keeping data fetched under the higher plan. P0.2 did not consider this. | Not adopted: the terms are unread (OQ-38, OQ-56) and a re-pull of old history, needed to detect vendor restatements, would be lost. Shown in section 12.3. |
| UP-37 | P0.1 OQ-16 "blocks P0.3" (starting capital) | Still unanswered. A cost model is defensible only against the capital it serves. | Section 9.5 gives the cost as a percentage of NAV for a range of NAVs instead of assuming one ([DEFAULT-21]). |
| UP-38 | P0.3 prompt DELIVERABLE | Names `docs/specs/SPEC-P0.3-BUDGET.md`, a historical path (N-2). N-5 maps it to `docs/new specs/`. The run instruction for this conversation names a third path. | Written to `paste-ready/outputs/P0.3-CLAUDE.md` as instructed. Moving it under `docs/new specs/` is the Owner's step. |
| UP-39 | P0.2 section 5.12, "P0.3 prices at peak" | Followed. But the session clocks put almost every call off-peak (section 7.1), so the peak figure overstates expected spend by a factor of two. | Both are shown; totals use peak. |

## 3. Evidence register

Every fact was retrieved on 2026-10-13. Levels are those of P0.2 section 3 (`VerificationLevel`).
PRIMARY_FULL: the provider's own page, whole page text read in this conversation.
PRIMARY_EXTRACT: the provider's own page, read through an automated question-answering fetch.
SEARCH_EXCERPT: only a search-result excerpt of the provider's page was seen. SECONDARY: a third
party's statement.

| # | Fact | Source URL | Level | Full read owed by |
|---|------|------------|-------|-------------------|
| F-65 | DigitalOcean Droplets, Basic (shared CPU, regular): 8 GiB, 4 vCPU, 160 GiB SSD, 5,000 GiB transfer, USD 0.07143/h, USD 48.00/month. 16 GiB, 8 vCPU, 320 GiB SSD, 6,000 GiB transfer, USD 0.14286/h, USD 96.00/month. General Purpose (dedicated CPU): 16 GiB, 4 vCPU, 50 GiB, USD 126.00/month; 32 GiB, 8 vCPU, 100 GiB, USD 0.37500/h, USD 252.00/month. Billing per second with a 60-second minimum; bundled plans have a monthly cap (the page refers to 672 hours). A public IPv4 address is included in bundled plans. A Bangalore datacenter exists. Snapshots USD 0.06 per GB per month. | https://www.digitalocean.com/pricing/droplets | PRIMARY_FULL | done |
| F-66 | DigitalOcean reserved IPs: free when assigned to a Droplet; a reserved IPv4 address costs USD 5.00 per month (USD 0.01 per hour) when reserved and not assigned. | https://docs.digitalocean.com/products/networking/reserved-ips/details/pricing/ | PRIMARY_EXTRACT | P6.4 |
| F-67 | DigitalOcean Spaces object storage: USD 5 per month includes 250 GiB storage and 1 TiB outbound transfer; additional storage USD 0.02 per GiB; additional transfer USD 0.01 per GiB; cold storage USD 0.007 per GiB. | https://www.digitalocean.com/pricing/spaces-object-storage | PRIMARY_FULL | done |
| F-68 | Amazon Lightsail, Linux bundles with a public IPv4 address: 8 GB, 2 vCPU, 160 GB SSD, USD 44/month; 16 GB, 4 vCPU, 320 GB SSD, 6 TB transfer, USD 84/month; 32 GB, 8 vCPU, 640 GB SSD, USD 164/month. A static IP address is included in all plans. Mumbai plans include half the stated transfer. Block storage USD 0.10 per GB per month. Object storage bundles: USD 1 (5 GB), USD 3 (100 GB), USD 5 (250 GB). Snapshots USD 0.05 per GB per month. | https://aws.amazon.com/lightsail/pricing/ | PRIMARY_FULL | done |
| F-69 | Lightsail FAQ: instances are burstable (a CPU baseline with the ability to burst above it); a static IP not attached to an instance for more than 1 hour costs USD 0.005 per hour; 5 static IPs per account; Asia Pacific (Mumbai) is a Lightsail region. The baseline percentage per bundle is not on the page. | https://aws.amazon.com/lightsail/faq/ | PRIMARY_EXTRACT | only if (b) of BQ-22 is chosen |
| F-70 | PostgreSQL `archive_timeout`: archiving happens only for completed WAL segments. When the setting is above zero the server switches to a new segment once that time has passed since the last switch, provided there was any database activity (a single checkpoint counts; checkpoints are skipped when there is no activity). A segment closed early by a forced switch is archived at the same length as a full one, so a very short setting bloats the archive; the page calls a setting of about a minute usually reasonable and points to streaming replication for anything faster. Defaults: `checkpoint_timeout` 5 minutes, `max_wal_size` 1 GB, `wal_compression` off, `full_page_writes` on. | https://www.postgresql.org/docs/current/runtime-config-wal.html (version 18) | PRIMARY_EXTRACT | P6.4 |
| F-71 | PostgreSQL `initdb --wal-segsize`: the default segment size is 16 megabytes; the value must be a power of 2 between 1 and 1024 megabytes; it can be set only at initialisation and not changed afterwards. | https://www.postgresql.org/docs/current/app-initdb.html (version 18) | PRIMARY_EXTRACT | P6.4 |
| F-72 | PostgreSQL page layout: pages are usually 8 kB; the page header is 24 bytes; an item identifier is 4 bytes per item; the fixed heap tuple header occupies 23 bytes on most machines; user data begins at an offset that is a multiple of the platform MAXALIGN distance. | https://www.postgresql.org/docs/current/storage-page-layout.html (version 18) | PRIMARY_EXTRACT | P1.2 |
| F-73 | TimescaleDB (Tiger Data documentation), columnstore: converting a chunk can reduce its size by up to 98%; `orderby` is the time dimension; `segmentby` is the column used for access, and a lower-cardinality `segmentby` column compresses better; syntax: a `CREATE TABLE` statement ending `WITH (timescaledb.hypertable, timescaledb.segmentby='symbol', timescaledb.orderby='time DESC')`, and `CALL add_columnstore_policy('t', after => INTERVAL '7d')`; `INSERT`, `UPDATE`, `DELETE` and `UPSERT` are supported on data in the columnstore. The page does not state the rows per compressed batch, a chunk-interval rule, or the versions the syntax applies to. | https://www.tigerdata.com/docs/build/columnar-storage/setup-hypercore | PRIMARY_EXTRACT | P1.2 |
| F-74 | Massive knowledge base: a "grouped daily bars" endpoint, shown as `GET https://api.massive.com/v2/aggs/grouped/locale/us/market/stocks/{date}` with `adjusted` as a parameter, returns one bar for every US ticker that traded on the date; the example response for 2026-09-04 has `resultsCount` 12510; a sibling page speaks of over 12,000 rows. | https://massive.com/knowledge-base/article/how-can-i-get-the-daily-prices-for-all-stocks-using-massives-market-data | SEARCH_EXCERPT | P2.1 (OQ-56) |
| F-75 | DeepSeek pricing page re-read: prices identical to F-57 (`deepseek-flash`: USD 0.006 / 0.3 / 1.2 per 1M tokens for cache-hit input, cache-miss input and output at peak; half of each off-peak; peak hours 01:00 to 04:00 and 06:00 to 10:00 UTC, Monday to Friday, excluding Chinese public holidays). The page does not say whether thinking tokens are billed as output and gives no default output limit. | https://api-docs.deepseek.com/quick_start/pricing | PRIMARY_EXTRACT | P4.2 (OQ-60) |
| F-76 | A broker blog states: 2,867 companies listed on NSE in 2026, of which 94 were not traded as of 2025-12-31; 5,936 companies listed on BSE as of 2026-02-24. | https://shoonya.com/blog/how-many-companies-are-listed-in-nse-and-bse/ | SECONDARY, seen as a search excerpt | P2.1 (OQ-57) |

Count: 12 fact rows. 3 PRIMARY_FULL, 7 PRIMARY_EXTRACT, 1 SEARCH_EXCERPT, 1 SECONDARY.

F-74 and F-76 are not strong enough to be stated as facts about the market. They are used only
as inputs to assumptions A-57 and A-58. A search aimed at `nseindia.com` for a primary count
returned an oversized result that was not read; nothing from it is used.

Facts from upstream used here by number: F-7 (Kite limits), F-12 (Kite WebSocket packet sizes),
F-16 (Kite Connect INR 500), F-27 (Alpaca data plans), F-48 (Massive plans), F-57, F-58 (DeepSeek),
F-60 (OpenAI), F-61, F-62 (session times).

## 4. Sizing inputs

Every number used in sections 5 to 12 is in this table or is derived from it in view.

| Symbol | Value | Meaning | Source |
|--------|-------|---------|--------|
| S | 252 | sessions per year | A-25 |
| Y | 10 | years of history | [DEFAULT-25] |
| M | 21 | sessions per month, 252 / 12 | A-25, A-66 |
| U | 500 | universe instruments per market | ADR-14 |
| N_US | 12,510 | US tickers with a daily bar per session, all types | A-57, from F-74 |
| N_IN | 8,803 | India listings with a daily bar per session, 2,867 + 5,936 | A-58, from F-76 |
| m_US, m_IN | 390, 375 | minutes per regular session | A-26, F-61, F-62 |
| b_US, b_IN | 78, 75 | 5-minute bars per session, 390 / 5 and 375 / 5 | derived |
| B | 180 | bytes per stored bar row including indexes | A-59, section 5.1 |
| r_d, r_i | 4, 10 | planning compression ratio, daily and intraday bars | A-60; vendor ceiling 50 (F-73, "up to 98%") |
| W | 5, 10, 20, 50 | LLM gate width per market per session | [DEFAULT-17] is 10 |
| t_in, t_out | 8,000, 1,500 | planning tokens per call, input and output | [DEFAULT-37] |
| T_in, T_out | 32,000, 4,000 | hard cap per call, input and output | [DEFAULT-37] |
| p_DS | 0.30, 1.20 | `deepseek-flash` USD per 1M tokens, cache-miss input and output, peak | F-57, F-75 |
| p_DS_off | 0.15, 0.60 | the same, off-peak | F-57, F-75 |
| p_OA | 0.15, 0.60 | `gpt-4o-mini` USD per 1M tokens, input and output | F-60 |
| R | 90 | INR per USD, used only to show one combined figure | A-65; not a sourced rate |
| h | 0.14286 | USD per hour of the chosen VM | F-65 |

## 5. Data volume

### 5.1 Bytes per row

The table that will hold bars is P1.2's to define. For sizing, this layout is assumed (A-59).
It is not a contract.

| Column | Type | Bytes | Note |
|--------|------|-------|------|
| instrument_id | bigint | 8 | UNI-4 internal identifier |
| session_date | date | 4 | NB-31: a daily bar is keyed by session date |
| bar_start_utc | timestamptz | 8 | needed for intraday bars; kept for daily so one layout serves both |
| open, high, low, close | numeric | 4 x 9 = 36 | NB-3 forbids float for money; 9 bytes is an assumed average for a variable-length numeric |
| volume | bigint | 8 | |
| trade_count | bigint, nullable | 8 | Kite candles have none (F-13) |
| vwap | numeric, nullable | 9 | Kite candles have none |
| provider | smallint | 2 | `ProviderId` code |
| ingested_at | timestamptz | 8 | point-in-time |
| alignment padding | | 5 | assumed |
| Row data | | 96 | 8 + 4 + 8 + 36 + 8 + 8 + 9 + 2 + 8 + 5 |

Heap: tuple header 23 bytes, padded to 24 (F-72), plus 96 data, plus a 4-byte item identifier
(F-72) = 124 bytes. An 8,192-byte page less its 24-byte header holds floor(8,168 / 124) = 65 rows,
so the heap costs 8,192 / 65 = 126.0 bytes per row.

Indexes (assumed, A-59): primary key on (instrument_id, session_date, bar_start_utc) at about 31
bytes per row and one time index at about 22 bytes per row.

B = 126 + 31 + 22 = 179, rounded up to 180 bytes per row.

Edge cases:
- A daily bar from Kite has two null columns; nulls are not stored, so those rows are about 17
  bytes smaller. B is not reduced for this.
- If P1.1 chooses integer money (NB-13 is open) the four price columns shrink from 36 to 32
  bytes. B is not reduced for this either.
- If P1.2 adds columns, storage scales by (new row bytes + 53) / 180.

### 5.2 Decided design: daily bars, whole market, 10 years

Rows:
- US: 12,510 x 252 x 10 = 31,525,200
- India: 8,803 x 252 x 10 = 22,183,560
- Total: 53,708,760 rows

Before compression: 53,708,760 x 180 = 9,667,576,800 bytes = 9.67 GB (9.00 GiB).

After compression at r_d = 4: 9.67 / 4 = 2.42 GB. At the vendor's stated ceiling of 98% (F-73)
it would be 0.19 GB; that figure is a ceiling for other data shapes and is not used.

Why r_d is only 4 (A-60): compression works on batches of rows per `segmentby` value per chunk.
With `segmentby` = instrument and one chunk per year, a batch holds at most 252 daily rows. That
is a short batch. The ratio must be measured on real data before it is relied on (OQ-61).

Live growth: (12,510 + 8,803) x 252 = 5,370,876 rows per year = 0.97 GB per year before
compression.

For comparison, the ADR-13 figure (universe only): 1,000 x 252 x 10 = 2,520,000 rows = 0.45 GB.
Ratio 53,708,760 / 2,520,000 = 21.3 (UP-28).

Edge cases:
- N_US counts every ticker type that traded (ETFs, funds, units), not only common stock. All are
  stored: the instrument class is known only after joining to the instrument master, and an ETF
  may be read as data (ADR-05).
- N_IN adds NSE and BSE listings without removing companies listed on both. NB-31 keys a bar by
  instrument, and an NSE listing and a BSE listing are separate instruments (P0.2 5.3: no
  consolidated tape), so the sum is the correct upper bound.
- A listing that did not trade on a day has no bar and no row; the count is therefore an upper
  bound on rows per day. UNI-1 treats a no-trade day as traded value zero; that is a derived
  value in P2.3, not a stored bar (INV-6).
- Delisted instruments: the per-day count is of what traded that day, so past days include
  instruments that have since delisted, if the vendor serves them (OQ-38, OQ-39). No separate
  allowance is added.
- The counts are assumed constant over ten years (A-57, A-58). If the true ten-year average is
  half, storage halves; it cannot matter to cost (section 8.4).

### 5.3 Comparison: 5-minute and 1-minute bars (not built)

Universe only (500 per market), 10 years:

| Frequency | Rows | Arithmetic | Before, GB | After at r_i = 10, GB |
|-----------|------|------------|------------|-----------------------|
| 1d | 2,520,000 | 2 x 500 x 252 x 10 | 0.45 | 0.11 (at r_d = 4) |
| 5m | 192,780,000 | 500 x 78 x 2,520 + 500 x 75 x 2,520 = 98,280,000 + 94,500,000 | 34.70 | 3.47 |
| 1m | 963,900,000 | 500 x 390 x 2,520 + 500 x 375 x 2,520 = 491,400,000 + 472,500,000 | 173.50 | 17.35 |

Whole market, 10 years, as an upper bound (every ticker has a bar in every interval):

| Frequency | Rows | Arithmetic | Before, GB | After, GB |
|-----------|------|------------|------------|-----------|
| 1d | 53,708,760 | section 5.2 | 9.67 | 2.42 |
| 5m | 4,122,732,600 | 12,510 x 78 x 2,520 + 8,803 x 75 x 2,520 = 2,458,965,600 + 1,663,767,000 | 742.09 | 74.21 |
| 1m | 20,613,663,000 | 12,510 x 390 x 2,520 + 8,803 x 375 x 2,520 = 12,294,828,000 + 8,318,835,000 | 3,710.46 | 371.05 |

Bytes = rows x 180. The 1-minute universe row count equals the ADR-13 figure. Ten years of
minute history is not available from the selected sources in any case: Upstox serves minute
candles from January 2022 only (F-43), Alpaca from 2016 (F-27), and Kite's depth is unstated
(OQ-30).

### 5.4 Everything else on the disk

All assumed (A-61), on a five-year horizon.

| Item | GB | Arithmetic |
|------|----|------------|
| Daily bars, 10 years, uncompressed (worst case) | 9.67 | section 5.2 |
| Daily bars, live growth, 5 years | 4.83 | 0.97 x 5, rounded from 4.834 |
| Features | 6.05 | 2 markets x 1,260,000 rows x 2 (eligible set assumed twice the universe) x 150 features x 8 bytes |
| Audit trail in the database | 6.30 | 5,000 events per session x 1 kB = 5 MB; x 252 = 1.26 GB per year; x 5 |
| Local audit file sink ([DEFAULT-2]) | 6.30 | a second copy of the same records |
| News and LLM packets | 7.30 | (5 MB + 0.8 MB) per session x 252 = 1.46 GB per year; x 5 |
| Prometheus | 2.00 | assumed |
| Container images | 10.00 | assumed |
| Operating system | 10.00 | assumed |
| Backtest and model artefacts | 20.00 | assumed |
| PostgreSQL WAL and temporary space | 10.00 | `max_wal_size` default is 1 GB (F-70); the rest is backfill headroom |
| Total | 92.45 | sum of the rows |

Rule: the disk is at least twice the total, so that a restore beside the live data, a major
version upgrade or a recompression can run in place. 2 x 92.45 = 184.9 GB.

## 6. Ingest throughput

### 6.1 What the worst minute is under the decided design

There is no stream. The ingest is a batch after each close (ADR-13, P0.2 section 4). The worst
minute of the day is therefore not the open; it is the minute in which the US whole-market
response is written.

| Quantity | US | India |
|----------|----|-------|
| Messages per session | 1 response of 12,510 bars if the grouped endpoint is usable (F-74, OQ-56); otherwise 12,510 responses | 8,803 responses of 1 bar each (F-13: one instrument per request) |
| Peak messages per second | 1, or 5 at THR-7 | 1 at THR-2 |
| Peak rows per second | 12,510 in one `COPY`, or 5 | 1 |
| Rows per session | 12,510 | 8,803 |
| Bytes per session at 180 | 2.25 MB | 1.58 MB |

Total: 21,313 rows and 3.84 MB per session-pair.

CPU: parsing and validating 21,313 rows at an assumed 20,000 rows per second per core (A-63) is
1.07 core-seconds per day.

PostgreSQL writes: at an assumed 250 bytes of WAL per row (A-63) the US batch writes 12,510 x 250
= 3.13 MB of WAL in one transaction, one commit, one flush. India commits once per response: one
flush per second for 8,803 seconds. Peak sustained write rate: under 10 IOPS. Any SSD exceeds
this; the IOPS rating of the chosen disk is not on the pages read and is not needed (OQ-54).

### 6.2 Time to ingest one session

| Step | Requests | Client pace | Time |
|------|----------|-------------|------|
| US, grouped endpoint | 1 | THR-7 | seconds |
| US, per-ticker fallback | 12,510 | 5 per second (THR-7, A-41) | 12,510 / 5 = 2,502 s = 41.7 min |
| India, whole market | 8,803 | 1 per second (THR-2, half of F-7's 3 rounded down) | 8,803 s = 146.7 min |
| India, NSE only | 2,867 | 1 per second | 2,867 s = 47.8 min |
| India, universe plus held (500 + up to 20) | 520 | 1 per second | 520 s = 8.7 min |

The India whole-market ingest is bound by the Kite throttle, not by the VM. This is the named
latency bottleneck of the data path. [DEFAULT-39] splits it: the 520 instruments the decision
needs are fetched first; the remaining 8,283 follow in the background (8,283 s = 138.1 min).

Edge cases:
- No India login that day (UP-32): no token, no Kite data, no India ingest. The session's bars
  are fetched after the next login, as a data job (ADR-02). The decision for the missed session
  is skipped and is not taken later on stale intent (ADR-13).
- A background bar that is still missing at the monthly rebuild: that instrument does not have
  60 validated sessions and is not eligible (UNI-3). It is not counted as zero traded value.
- HTTP 429 inside the budget (PE-3): the pace halves for the session, so the India background
  ingest takes up to 276 minutes and may not finish before the cycle deadline; it yields and
  resumes as a data job.
- Kite `/quote` returns up to 500 instruments per call (F-14), which would cut the India ingest
  to 18 calls. Whether an after-close quote is a valid daily bar is not verified (OQ-58). It is
  not used.

### 6.3 One-off 10-year backfill

| Step | Arithmetic | Time |
|------|------------|------|
| US, grouped endpoint, one request per session | 2,520 requests / 5 per second = 504 s | 8.4 min of requests |
| US, write 31,525,200 rows | at an assumed 50,000 rows per second by `COPY` (A-63): 630 s | 10.5 min |
| India, Kite, two requests per instrument (A-68) | 17,606 requests at 1 per second | 4.9 h |
| India, write 22,183,560 rows | at 50,000 rows per second: 444 s | 7.4 min |

The India backfill from Kite covers currently listed instruments only and is BLOCKED as ADR-08
evidence ([DEFAULT-29]).

### 6.4 Comparison: a streamed open (not built)

The two opens never coincide (09:15 `Asia/Kolkata` and 09:30 `America/New_York`; A-75), so the
peak is per market.

| Case | Messages per second | Rows per second | Arithmetic |
|------|---------------------|-----------------|------------|
| 1-minute bars, universe | 8.3 | 8.3 | 500 / 60 |
| 1-minute bars, whole US market | 208.5 | 208.5 | 12,510 / 60 |
| 1-minute bars, whole India market | 146.7 | 146.7 | 8,803 / 60 |
| Kite ticks, whole India market, `full` mode | 8,803 | not stored per tick | 1 packet per instrument per second assumed (A-63); 3 connections x 3,000 instruments = 9,000 capacity (F-12) |

Kite tick bandwidth: 8,803 x 184 bytes (F-12) = 1,619,752 bytes per second = 13.0 Mbit/s.

CPU (A-63): 208.5 rows per second at 20,000 rows per second per core is 1.0% of a core. 8,803
ticks per second at an assumed 50,000 packets per second per core is 17.6% of a core.

PostgreSQL: 208.5 rows per second batched into one transaction per second is 208.5 x 250 = 52 kB
of WAL per second and about 2 flushes per second. A US tick-rate figure for the open was not
obtained from any vendor page and is not stated.

Conclusion for the comparison: even the streamed case does not load this VM. Ingest is never the
bottleneck at any frequency in this document.

## 7. LLM spend

### 7.1 Cost of one call

Cost per call = t_in x p_in / 1,000,000 + t_out x p_out / 1,000,000. Every input token is priced
as a cache miss.

| Model and tariff | Planning call (8,000 in, 1,500 out) | Capped call (32,000 in, 4,000 out) |
|------------------|-------------------------------------|------------------------------------|
| `deepseek-flash`, peak | 8,000 x 0.30 / 10^6 + 1,500 x 1.20 / 10^6 = 0.0024 + 0.0018 = USD 0.0042 | 0.0096 + 0.0048 = USD 0.0144 |
| `deepseek-flash`, off-peak | 0.0012 + 0.0009 = USD 0.0021 | 0.0048 + 0.0024 = USD 0.0072 |
| `gpt-4o-mini-2024-07-18` | 8,000 x 0.15 / 10^6 + 1,500 x 0.60 / 10^6 = 0.0012 + 0.0009 = USD 0.0021 | 0.0048 + 0.0024 = USD 0.0072 |

Which tariff applies. The LLM stage of the India cycle starts no earlier than close + 6,900 s
(section 10.2), which is 17:25 `Asia/Kolkata` = 11:55 UTC, and ends by 16:00 UTC: always off-peak.
The US cycle's LLM stage starts no earlier than 21:55 UTC in US daylight time and 22:55 UTC
otherwise, and the cycle deadline is 02:00 or 03:00 UTC. Peak begins at 01:00 UTC. A US cycle
therefore pays peak prices only if it is still calling the LLM more than 5 hours (daylight time)
or 4 hours (standard time) after the close, and never for a Friday session, whose cycle runs on
Saturday UTC. Expected spend is close to the off-peak column. Totals below use peak, as P0.2
instructs (UP-39).

Edge cases:
- Thinking mode is on by default (F-57) and the page does not say how thinking tokens are billed
  (F-75). The planning and cap figures for output are taken to include them (A-69). If they are
  billed on top, output cost rises by the thinking-token count; the hard cap in 7.5 still bounds
  the month.
- A call that times out at our 120-second deadline (PE-14) may still be billed by the provider,
  and the fallback call is billed too. The "bound" column below prices every call at the primary
  peak rate plus the fallback rate: 0.0042 + 0.0021 = USD 0.0063.
- Cache hits would cut input cost by a factor of 50 on the cached part (F-57: 0.006 against 0.3).
  None is assumed, because no prompt design exists yet (P4.3).
- A price change by either provider: the price table is configuration changed through HITL-4;
  spend is recomputed from that table, never from this document.

### 7.2 Monthly spend at the decided cadence

Calls per month = W x 2 markets x 21 sessions = 42 x W.

| W | Calls per month | `deepseek-flash` peak | `deepseek-flash` off-peak, or `gpt-4o-mini` | Bound (0.0063 per call) | Capped tokens, peak | Capped tokens, bound |
|---|-----------------|-----------------------|---------------------------------------------|-------------------------|---------------------|----------------------|
| 5 | 210 | 210 x 0.0042 = 0.88 | 0.44 | 1.32 | 3.02 | 4.54 |
| 10 | 420 | 1.76 | 0.88 | 2.65 | 6.05 | 9.07 |
| 20 | 840 | 3.53 | 1.76 | 5.29 | 12.10 | 18.14 |
| 50 | 2,100 | 8.82 | 4.41 | 13.23 | 30.24 | 45.36 |

All figures USD per month, rounded half to even. "Capped tokens, bound" prices each call at
0.0144 + 0.0072 = 0.0216.

These are upper figures for the call count. P0.2 UP-24 scopes the LLM news path to the US until
an India news source exists, which halves the calls. INV-3 also allows calls for "statistically
anomalous conditions"; U-10 leaves that undefined, so no calls are budgeted for it. P4.2 must
either fit them inside W or raise a change to this budget.

### 7.3 Comparison: the same gate at intraday cadence (not built)

Decision points per session-pair: daily 2; 5-minute 78 + 75 = 153; 1-minute 390 + 375 = 765.
Calls per month = W x points x 21.

| Cadence | Calls per month per unit of W | USD per month per unit of W, peak | W = 5 | W = 10 | W = 20 | W = 50 |
|---------|-------------------------------|-----------------------------------|-------|--------|--------|--------|
| 1d | 42 | 0.1764 | 0.88 | 1.76 | 3.53 | 8.82 |
| 5m | 3,213 | 13.4946 | 67.47 | 134.95 | 269.89 | 674.73 |
| 1m | 16,065 | 67.4730 | 337.36 | 674.73 | 1,349.46 | 3,373.65 |

Latency, not money, forbids this first: with one concurrent call and a 120-second deadline
(THR-11, PE-14) a single call can outlast a 1-minute bar.

### 7.4 Where the USD 200 to 500 ceiling lands

Reading (a), LLM spend only, planning tokens, peak price:

| Cadence | W at USD 200 | W at USD 500 | Arithmetic |
|---------|--------------|--------------|------------|
| 1d | 1,133 | 2,834 | 200 / 0.1764 = 1,133.8; 500 / 0.1764 = 2,834.5 |
| 5m | 14 | 37 | 200 / 13.4946 = 14.8; 500 / 13.4946 = 37.1 |
| 1m | 2 | 7 | 200 / 67.4730 = 2.96; 500 / 67.4730 = 7.41 |

At the decided daily cadence the universe is 500 per market, so W cannot exceed 500. Sending
every universe instrument to the LLM every session costs 42 x 500 x 0.0042 = USD 88.20 a month.
The ceiling cannot be reached. It does not imply a gate width; the gate width is set by decision
quality (P4.2) and by the latency budget (section 10.2), not by spend.

Reading (b), total platform cost ([DEFAULT-32]), using the bound of 0.0063 per call and the
fixed costs of section 9:

| Cadence | Fixed, USD | Kite at R = 90, USD | LLM per unit of W, USD | Largest W with total at most 200 | Largest W with total at most 500 |
|---------|-----------|---------------------|------------------------|----------------------------------|----------------------------------|
| 1d | 186.00 | 5.56 | 42 x 0.0063 = 0.2646 | (200 - 186 - 5.56) / 0.2646 = 31.9, so 31 | (500 - 191.56) / 0.2646 = 1,165, capped at 500 by the universe |
| 5m | 306.00 | 5.56 | 3,213 x 0.0063 = 20.2419 | none: fixed cost alone exceeds 200 | (500 - 311.56) / 20.2419 = 9.3, so 9 |
| 1m | 306.00 | 5.56 | 16,065 x 0.0063 = 101.2095 | none | (500 - 311.56) / 101.2095 = 1.86, so 1 |

The 5-minute and 1-minute rows replace Massive Developer (USD 79) with Advanced (USD 199), the
only plan listed as real time (F-48): 186 - 79 + 199 = 306.

Result. Under the decided design the ceiling is consumed by fixed cost, not by the LLM: USD 191.56
of fixed cost against USD 2.65 of LLM at W = 10. The lower bound of USD 200 is met for W up to 31
only while every unpriced line in section 9.2 stays at zero, which it will not.

### 7.5 Hard limits that make the figures enforceable

| Limit | Value | Arithmetic or reason |
|-------|-------|----------------------|
| Input tokens per call | at most 32,000 | [DEFAULT-37] |
| Output tokens per call | at most 4,000, sent as the request's output limit | [DEFAULT-37] |
| Calls per market per session | at most W first attempts, plus at most one fallback attempt each | PE-14 |
| Concurrent calls | 1 | THR-11, THR-12 |
| Monthly spend cap | USD 25.00 | Covers capped tokens with full double billing up to W = 27: 25 / (42 x 0.0216) = 27.6. At W = 10 the same worst case is USD 9.07. |

Rules:
- Spend is accumulated from the token usage each response reports, multiplied by the configured
  price table. A response with no usage figures is charged at the capped-call price for its model
  at peak.
- A call is sent only if the month's accumulated spend plus the capped-call price of that call is
  at most the cap. Equal to the cap is allowed.
- The month is the calendar month in UTC (NB-49).
- When the cap blocks a call the LLM step is unavailable for that candidate, exactly as in PE-14.
  No order depends on the LLM alone (INV-2). An alert is raised. Raising the cap is HITL-4.

Edge cases:
- The cap is reached mid-cycle: the remaining candidates of that cycle get no LLM call. The cycle
  is not aborted.
- W = 50 with capped tokens and full double billing would need USD 45.36: above the default cap.
  Choosing W = 50 therefore requires a deliberate cap change, by design.
- A fallback call is priced with the fallback's table even if the primary call's usage is
  unknown.
- The provider's own invoice differs from our accumulated figure: P6.1 compares them monthly; a
  difference above 10% [ASSUMPTION, A-70] is an alert, and the price table is re-verified.

## 8. VM sizing

### 8.1 Decision

One VM: 16 GiB RAM, 8 shared vCPU, 320 GiB SSD ([DEFAULT-33], F-65).

The bottleneck is RAM, and specifically the peak of an offline model fit or backtest running on
the same VM as the live stack. It is not CPU, not disk space and not write IOPS. The longest wait
in the system is not on the VM at all: it is the Kite historical throttle (section 6.2) and the
LLM call deadline (section 10.2).

### 8.2 Memory

All per-container figures are assumptions to be measured (A-62). They are limits enforced on the
containers, so a wrong figure causes one container to be killed, not the VM to swap.

| Container | Limit, MiB | CPU limit | Why |
|-----------|-----------|-----------|-----|
| postgres (with TimescaleDB) | 4,096 | 4 | The largest table is 9.7 GB uncompressed; decision queries touch one session and a trailing window |
| redis | 512 | 1 | Throttle counters and short-lived state only |
| vault | 256 | 1 | |
| prometheus | 1,024 | 1 | |
| grafana | 512 | 1 | |
| api (FastAPI, ADR-01) | 512 | 1 | |
| scheduler (ADR-02; runs the decision cycle and the order job) | 2,048 | 2 | Scoring 500 instruments x 150 features is megabytes |
| killswitch ([DEFAULT-4]) | 256 | 1 | Own process and container |
| offline (retrain, backtest, search) | 6,144 | 6 | Section 8.3 |
| Host reserve (kernel, Docker, page cache) | 1,024 | | |
| Total | 16,384 | | 4,096 + 512 + 256 + 1,024 + 512 + 512 + 2,048 + 256 + 6,144 + 1,024 |

The total equals the VM's 16 GiB exactly. `CapacityPlan` (section 13) rejects a plan whose limits
exceed the VM.

Offline peak. One market's training matrix is at most 500 instruments x 2,520 sessions =
1,260,000 rows. At 150 features (A-62) and 8 bytes each: 1,260,000 x 150 x 8 = 1.512 GB. Peak
during a fit is assumed to be three times the raw matrix (A-62): 4.54 GB. That fits 6,144 MiB
(6.44 GB) with 1.9 GB spare. The two markets are fitted one after the other.

Edge cases:
- Training on the eligible superset (twice the universe, as assumed for features in 5.4) doubles
  the matrix to 3.02 GB and the peak to 9.07 GB, which does not fit. The fit must then use 4-byte
  floats (peak 4.54 GB) or the VM must be the 32 GiB class. P2.5 decides; the limit holds either
  way, and a fit that exceeds it is killed inside its own container.
- The offline container is killed for exceeding its limit: the live containers are unaffected;
  the offline job fails and is reported. It is not retried automatically.
- The 8 GiB plan (USD 48): the live limits alone are 9,216 MiB, and 10,240 MiB with the host
  reserve, which already exceeds 8,192 MiB before any offline work. Rejected.

### 8.3 Keeping offline work away from the live path ([DEFAULT-35])

- The offline container is paused (frozen, not killed) from the start of any decision cycle until
  that cycle ends, and from next open - 1,800 s until open + 900 s for either market.
- It is also paused while the kill switch is tripped.
- It holds no broker credential and no route to a broker host.

Time left for offline work on a day when both markets trade:
- Worst case, both cycles run to their deadline: a cycle occupies close + 2,700 s to close +
  21,600 s = 5.25 h; two cycles 10.5 h; two order jobs 2 x 0.75 h = 1.5 h. 24 - 10.5 - 1.5 =
  12 h. The India cycle and the US order job overlap in wall-clock time (NB-52), so the true
  figure is slightly higher.
- Typical, cycles finish on their stage budgets at W = 10: (9,720 - 2,700) s = 1.95 h each.
  24 - 3.9 - 1.5 = 18.6 h.

Edge cases:
- A pause arrives during a fit: the process is frozen and resumes; its wall-clock time grows, its
  result does not change.
- A scheduled quarterly retrain (ADR-07) falls on the same night as a decision cycle: it waits.
  It has no deadline shorter than the quarter.
- Weekends and days when both markets are closed: the offline container is never paused.

### 8.4 Disk

Need: 184.9 GB (section 5.4, including the factor of two). Provided: 320 GiB = 343.6 GB. Used at
year five: 92.45 / 343.6 = 27%.

Two thresholds, measured on the filesystem that holds the PostgreSQL data directory and the local
audit file:
- above 70% used: alert;
- above 85% used: new entries are denied in both markets; exits and stops continue. A full disk
  stops the local audit sink, and if the database is also down no automated action is possible
  ([DEFAULT-2]). Entries are stopped before that state can be reached.

Edge cases:
- Exactly 70.0% or 85.0%: not a breach (NB-2). A breach is strictly greater.
- The data directory and the audit file are on different filesystems: both are measured; the
  worse one decides.
- The 160 GiB plans (171.8 GB) do not meet the 184.9 GB rule.
- Whole-market minute bars (371 GB compressed, section 5.3) do not fit. That case is not built.

### 8.5 CPU and IOPS

Peak live CPU demand is the decision cycle's feature computation over about 21,000 instruments
and one model scoring pass: seconds of one core (A-63). Eight shared vCPUs are far more than the
live path needs; six are given to the offline container. Shared vCPUs can be slowed by other
tenants (F-65: the page describes Basic Droplets as suited to bursty workloads that tolerate
variable CPU). The live path has hours of slack, so this is accepted. It makes backtest durations
variable, which is why section 11 reports cost in VM-hours, not in guaranteed minutes.

Write IOPS: under 10 sustained (section 6.1).

### 8.6 Largest VM inside the budget (for ADR-03)

ADR-03 defines its capacity trigger "on the largest VM size inside the P0.3 budget". That size is
set here: `LARGEST_VM_IN_BUDGET` = one VM of at most 32 GiB RAM and 8 vCPU costing at most USD
252.00 per month (the General Purpose 32 GiB Droplet, F-65; the Lightsail 32 GB bundle is USD
164, F-68). At USD 252 the section 9 total at W = 10 becomes 194.20 - 96 + 252 = USD 350.20,
inside the upper bound of [DEFAULT-32].

Edge case: the General Purpose 32 GiB Droplet has a 100 GiB disk, below the 184.9 GB rule. It
needs an attached volume whose price was not verified (OQ-54). The Lightsail 32 GB bundle
includes 640 GB.

## 9. Monthly cost model

### 9.1 Priced lines

W = 10. All amounts per month.

| ID | Line | Amount | Basis | Source |
|----|------|--------|-------|--------|
| CL-01 | VM, DigitalOcean Basic 16 GiB / 8 vCPU / 320 GiB | USD 96.00 | VERIFIED_PRICE | F-65 |
| CL-02 | Primary static IPv4, assigned to the VM | USD 0.00 | VERIFIED_PRICE | F-66 |
| CL-03 | Recovery static IPv4, reserved and unassigned (D-17) | USD 5.00 | VERIFIED_PRICE | F-66 |
| CL-04 | Object storage for base backups and WAL archive, 250 GiB bundle | USD 5.00 | VERIFIED_PRICE | F-67 |
| CL-05 | Object storage beyond 250 GiB | USD 1.00 | ASSUMPTION | section 9.3: 40.5 GiB x 0.02 = 0.81, rounded up |
| CL-06 | Massive, Developer plan | USD 79.00 | VERIFIED_PRICE | F-48 |
| CL-07 | Alpaca Market Data, Basic plan | USD 0.00 | VERIFIED_PRICE | F-27 |
| CL-08 | Alpaca Trading API | USD 0.00 | VERIFIED_PRICE | F-37; per-trade regulatory fees are P5.3's |
| CL-09 | FRED | USD 0.00 | VERIFIED_PRICE | P0.2 section 6.3 |
| CL-10 | Kite Connect | INR 500.00 | VERIFIED_PRICE | F-16 |
| CL-11 | `deepseek-flash`, 420 calls, planning tokens, peak | USD 1.76 | ASSUMPTION | section 7.2; price F-57, tokens [DEFAULT-37] |
| CL-12 | `gpt-4o-mini` fallback, bound: every call also billed | USD 0.88 | ASSUMPTION | 420 x 0.0021 |

Totals:
- USD lines: 96.00 + 0.00 + 5.00 + 5.00 + 1.00 + 79.00 + 0.00 + 0.00 + 0.00 + 1.76 + 0.88 =
  USD 188.64. Unrounded, 186 + 420 x 0.0063 = 188.646, shown as USD 188.65 elsewhere in this
  document.
- INR lines: INR 500.00.
- Combined, for a single headline only, at the assumed R = 90 (A-65): 500 / 90 = USD 5.56;
  188.65 + 5.56 = USD 194.20 per month, USD 2,330.42 per year, or INR 17,478 per month.

Main components of the USD 194.20: VM 96.00 (49%); Massive 79.00 (41%); storage and addresses
11.00 (6%); Kite 5.56 (3%); LLM 2.65 (1%).

"Fixed cost" in sections 7.4 and 12 means CL-01 to CL-09: USD 186.00.

### 9.2 Lines that exist and have no price

Each is a real recurring cost that cannot be stated without inventing a number (RULE-1).

| ID | Line | Why unpriced | Resolved by |
|----|------|--------------|-------------|
| CL-13 | India whole-market end-of-day history and daily files, with delisted stocks | [DEFAULT-29] requires it; product and price unknown | OQ-39 |
| CL-14 | India corporate actions, fundamentals, news, ISIN mapping | SEL-8, SEL-10, SEL-12 are UNFILLED | OQ-40 |
| CL-15 | US fundamentals backup (FMP) | Starter price ambiguous (USD 19 or 49), needed only if approved | OQ-47 |
| CL-16 | Taxes on the invoices above (for example GST on cloud and broker fees) | Not on any page read | OQ-54 |
| CL-17 | USD/INR reference-rate source | SEL-18 UNFILLED | OQ-22 |
| CL-18 | Sector taxonomy, both markets | SEL-13, SEL-14 UNFILLED | OQ-40, OQ-41 |
| CL-19 | Alert delivery channel to the operator | Not chosen; P6.1 | P6.1 |

Under [DEFAULT-32] the room left for CL-13 to CL-19 together is 200 - 194.20 = USD 5.80 a month
at the lower bound and 500 - 194.20 = USD 305.80 at the upper bound. ADR-14's "revisit when P0.3
shows the full-market daily data is unaffordable" cannot be evaluated until CL-13 has a price.
The US half is affordable: it is CL-06.

### 9.3 Backup and archive storage

`archive_timeout` = 60 s forces a segment switch every 60 seconds whenever there has been any
activity (F-70). Worst case, every minute of the day:

- Segments per day: 24 x 60 = 1,440.
- At 16 MiB each (F-71 default): 1,440 x 16 = 23,040 MiB = 22.5 GiB per day.
- 7-day window ([DEFAULT-40]): 7 x 22.5 = 157.5 GiB.
- Base backups: 7 retained x 19 GiB assumed each (A-73) = 133 GiB.
- Total: 157.5 + 133 = 290.5 GiB. Over the 250 GiB bundle by 40.5 GiB; 40.5 x 0.02 = USD 0.81.
- Upload rate: 22.5 GiB per day = 2.13 Mbit/s sustained. Monthly outbound from the VM: 30 x 22.5
  = 675 GiB, inside the plan's 6,000 GiB (F-65).

Alternatives:
- 30-day window: 30 x 22.5 = 675 GiB of WAL; (675 + 133 - 250) x 0.02 = USD 11.16.
- 1 MiB segments (F-71 minimum): 1,440 MiB = 1.41 GiB per day; 7 days = 9.8 GiB. Cheaper by
  under USD 1 a month at 7-day retention. Not chosen: irreversible after `initdb`, and unusual.

Edge cases:
- An idle minute produces no switch (F-70), so the real archive is smaller. The audit trail,
  job-run records and heartbeats make most trading-day minutes active; weekends are quieter.
  The worst case is budgeted.
- The archive is unreachable: ADR-10 already disables new entries until archiving resumes.
  Unarchived segments accumulate on the VM disk at up to 22.5 GiB per day; the 85% disk rule
  (8.4) is reached after roughly (0.85 x 343.6 - 92.45) / 24.2 = 8.2 days at year-five usage.
- The audit trail is never pruned by the retention window: the window limits how far back a
  point-in-time restore can go, and every base backup contains the full audit table.
- The bucket shares a provider with the VM. It is off the VM, which is all [DEFAULT-19] asks.
  It does not survive loss of the provider account. P6.4 owns that risk.

### 9.4 What is not in this model

Trading charges (F-19, F-37) are per trade: P5.3. Tax on gains: P6.3. The operator's time. The
cost of capital sitting in cash. Wire and remittance fees (F-37: USD 35 per outbound
international wire) are per transfer.

### 9.5 Cost against capital

OQ-16 is unanswered, so no NAV is assumed ([DEFAULT-21]). The priced total is USD 2,330.42 per
year (at R = 90). As a percentage of combined NAV per year:

| Combined NAV, USD | In INR at R = 90 | Cost per year as % of NAV | Arithmetic |
|-------------------|------------------|---------------------------|------------|
| 10,000 | 900,000 | 23.30 | 2,330.42 / 10,000 |
| 25,000 | 2,250,000 | 9.32 | |
| 50,000 | 4,500,000 | 4.66 | |
| 100,000 | 9,000,000 | 2.33 | |
| 250,000 | 22,500,000 | 0.93 | |
| 500,000 | 45,000,000 | 0.47 | |

NAV at which the priced cost is a given drag: 2% a year at USD 116,521 (INR 10,486,884); 1% at
USD 233,042; 5% at USD 46,608.

This is before CL-13 to CL-19, before trading charges and before tax. The platform's fixed cost
is the same whether the account holds USD 10,000 or USD 500,000. Below roughly USD 50,000 of
combined capital the fixed cost alone exceeds 4.66% a year, which a long-only swing strategy
must earn back before it earns anything.

## 10. Latency budget

### 10.1 Conventions

- A budget is a duration in whole seconds. A stage meets its budget if its elapsed time is at
  most the budget; equal passes.
- Durations are measured on the monotonic clock (NB-10). Anchors (close, open) are instants
  computed from the exchange calendar for that session (NB-15), so half-days and daylight saving
  need no special case.
- Every budget is per market. The two markets' paths are independent (ADR-02).
- Within every stage of the decision cycle, held instruments are processed before non-held ones,
  so that a strategy exit (HP-3) is the last thing an overrun can drop.
- "Skipped" always means: no order intents are produced for that market for the next session, an
  alert is raised, and the session counts toward the ADR-03 trigger unless P6.1 records a vendor
  cause. Resting stops and GTTs are untouched. Nothing runs late (ADR-02).

### 10.2 Daily-rebalance path, part A: decision cycle

Anchor: session close of session D. Hard deadline for the whole cycle: close + 21,600 s
([DEFAULT-38]). Stage budgets are cumulative in the order shown.

| ID | Stage | Budget, s | Derivation | When the budget is blown |
|----|-------|-----------|------------|--------------------------|
| STG-A0 | Wait for vendor data to be final | 2,700 | NSE's closing session ends 30 minutes after the close (F-62); Alpaca Basic and Massive Developer serve data 15 minutes late (F-27, F-48). 45 minutes covers both (A-67). | It is a wait, not work. If the process starts later than this, the stages below start late and the cycle deadline still applies. |
| STG-A1 | Reference ingest: instrument master, corporate actions, calendar check | 600 | assumed (A-70) | Cycle skipped. Without the session's corporate actions the share basis of tomorrow's orders cannot be confirmed (P0.2 section 7). |
| STG-A2a | Bars for universe plus held instruments | 1,200 | India: 520 requests at 1 per second = 520 s (section 6.2), with room for one halving of the pace | Instruments still missing are excluded: no decision for them (INV-6, PE-16). If the excluded share exceeds P2.2's threshold the cycle is skipped. |
| STG-A2b | Bars for the rest of the market, in the background | 17,100 | From close + 4,500 s to the cycle deadline: 21,600 - 4,500. India: 8,283 s. | Not blocking. It yields at the deadline and resumes as a data job at the next opportunity (ADR-02). |
| STG-A3 | Validation (P2.2) | 600 | assumed | Unvalidated instruments are excluded. |
| STG-A4 | Adjustment and features | 900 | assumed | Instruments without a complete feature row are excluded. |
| STG-A5 | Scoring, regime, ranking, candidate set | 300 | assumed | Cycle skipped. A partly ranked universe is not a ranking. |
| STG-A6 | News fetch and sanitising for gated candidates | 600 | assumed | Candidates without a packet get no LLM call (P0.2 section 7: an empty packet is never presented as "no news"). |
| STG-A7 | LLM gate | 240 x W | 2 attempts x 120 s (PE-14), one at a time (THR-11, THR-12) | Candidates not yet answered are treated as LLM unavailable (P4.2 decides whether they proceed). The stage is never extended. |
| STG-A8 | Sizing and risk engine | 300 | assumed | Cycle skipped. |
| STG-A9 | Audit write and persistence of order intents | 120 | assumed; two sinks ([DEFAULT-2]) | Cycle skipped. An intent without its audit record does not exist (INV-5). |

Sum of the blocking stages without the LLM: 2,700 + 600 + 1,200 + 600 + 900 + 300 + 600 + 300 +
120 = 7,320 s (122 min).

| W | LLM stage, s | Budgeted total, s | In minutes | Slack to the 21,600 s deadline, s |
|---|--------------|-------------------|------------|-----------------------------------|
| 5 | 1,200 | 8,520 | 142 | 13,080 |
| 10 | 2,400 | 9,720 | 162 | 11,880 |
| 20 | 4,800 | 12,120 | 202 | 9,480 |
| 50 | 12,000 | 19,320 | 322 | 2,280 |

The largest W that fits: (21,600 - 7,320) / 240 = 59.5, so 59. `LlmBudget` allows at most 50.

The earliest the LLM stage can start is the sum of A0 to A6 on the blocking path: 2,700 + 600 +
1,200 + 600 + 900 + 300 + 600 = 6,900 s after the close (used in section 7.1).

Wall-clock placement (from A-26; shown for orientation, never used as a rule):

| Market | Close | Cycle may start | Cycle deadline |
|--------|-------|-----------------|----------------|
| India | 15:30 `Asia/Kolkata` | 16:15 | 21:30 |
| US, daylight time | 16:00 `America/New_York` = 01:30 `Asia/Kolkata` | 02:15 `Asia/Kolkata` | 07:30 `Asia/Kolkata` |
| US, standard time | 16:00 `America/New_York` = 02:30 `Asia/Kolkata` | 03:15 `Asia/Kolkata` | 08:30 `Asia/Kolkata` |

Edge cases:
- NYSE early close at 13:00 (F-61): the anchor moves; the cycle may start at 13:45 and its
  deadline is 19:00 `America/New_York`.
- The India cycle needs the Kite token obtained that morning; it is valid until 06:00 the next
  day (NB-38), which is after the 21:30 deadline. No login that day: STG-A2a gets HTTP 403
  (PE-1), every instrument is missing, the cycle is skipped.
- The US cycle deadline in standard time (08:30 `Asia/Kolkata`) is 15 minutes before the India
  order job's pre-checks begin (08:45). They do not overlap. They also do not share a market, so
  an overlap would be allowed (ADR-02).
- The process restarts mid-cycle: per ADR-02 an incomplete order-producing run is not resumed.
  The cycle is skipped even if time remains.
- A stage finishes early: the next stage starts at once. Unused budget is not carried into a
  later stage's budget; only the cycle deadline is shared.
- A stage overruns but the cycle deadline is far away: the stage's own consequence in the table
  applies at the stage budget, not at the cycle deadline. Budgets are hard.
- The VM clock steps: stage durations use the monotonic clock; the deadline is checked against
  both the monotonic elapsed time since the cycle started and the wall clock, and the earlier
  verdict wins.
- W is changed (HITL-4) while a cycle runs: the running cycle keeps the W it started with.

### 10.3 Daily-rebalance path, part B: order job in session D+1

Anchor: open of session D+1.

| ID | Stage | Window or budget | Derivation | When it fails or overruns |
|----|-------|------------------|------------|---------------------------|
| STG-B0 | Preconditions: calendar says open; kill switch not tripped; India token valid and obtained after 06:00 (NB-38); intents exist and are exactly one session old | starts at open - 1,800 s; 60 s | [DEFAULT-38] | No orders for this market this session. |
| STG-B1 | Reconcile positions, open orders and cash over REST (D-14) | 300 s | assumed | No orders; HITL-8 if a difference remains. |
| STG-B2 | Every open position has a live stop; missing ones are placed first (PE-11, REC-4 order) | 600 s | up to 20 placements at 6 s = 114 s, plus reads | Entries disabled for the session; escalated. |
| STG-B3 | Corporate-action re-check for D+1 (ADR-13 edge case) | 120 s | assumed | Affected intents are cancelled; if the check cannot complete, all are. |
| STG-B4 | Final risk check against reconciled state and settled cash ([DEFAULT-27]) | 120 s | assumed | Intents that fail are dropped. |
| STG-B5 | Submission, one audit record before each order | from the open to open + 600 s | spacing per [DEFAULT-5] | An order not submitted by open + 600 s is never sent. |
| STG-B6 | Acknowledgement of each order | 10 s per order | assumed (A-71) | PE-8: outcome unknown; the order book is read and matched on `ClientOrderRef`; never re-sent blind. |

Pre-checks sum to 60 + 300 + 600 + 120 + 120 = 1,200 s, inside the 1,800 s before the open. The
job ends at open + 900 s with a REST read of every order it sent.

Submission arithmetic ([DEFAULT-5]; N orders need N - 1 gaps):
- 20 entries, two or more strategies alternating: 19 x 3 = 57 s.
- 20 entries, one strategy: 19 x 6 = 114 s.
- 20 entries each followed by its protective stop, one strategy ([DEFAULT-41]): 39 x 6 = 234 s.
- Most submissions that fit in 600 s for one strategy: floor(600 / 6) + 1 = 101.

End to end, "bar closes" to "order acknowledged":

| Market | Close to next open | Latest acknowledgement | End-to-end bound |
|--------|--------------------|------------------------|------------------|
| India | 17 h 45 min = 63,900 s | open + 600 s + 10 s | 64,510 s = 17 h 55 min 10 s |
| US | 17 h 30 min = 63,000 s | open + 600 s + 10 s | 63,610 s = 17 h 40 min 10 s |

Of that, the system is working for at most 21,600 s (cycle) + 2,700 s (order job, from open -
1,800 s to open + 900 s) = 24,300 s = 6 h 45 min. The rest is the market being closed. The
figures are for consecutive weekdays; over a weekend or holiday the wall-clock bound grows and
the working time does not.

Edge cases:
- Session D+1 does not open (unexpected closure): STG-B0 fails; the intents are now older than
  one session at the next open and are stale (ADR-13). The next cycle decides afresh.
- India login arrives at 09:05: STG-B0 started at 08:45 and failed. Per [DEFAULT-6] India is
  enabled from the next decision cycle; today's skipped orders are not sent late.
- Exactly open + 600.000 s: a submission at that instant is allowed (inclusive).
- An order's audit write fails on both sinks: that order is not sent (INV-5); the rest proceed.
- A broker rejects an entry (PE-6, PE-7): it still consumed its spacing slot ([DEFAULT-5]).
- Pre-open submission might improve fills, but whether a `day` limit order is accepted before
  the open, and how, is unverified for both brokers (OQ-66, NB-39). P3.2 may move the window;
  the budget shape does not change.

### 10.4 Intraday path that exists: stop placement after a fill

Anchor: the fill at the broker. This is the only price-sensitive real-time duty of the system
under HP-1 to HP-5: a filled entry has no protection until its stop (US) or GTT (India) rests at
the broker.

| ID | Stage | Budget, s | Derivation |
|----|-------|-----------|------------|
| STG-C1 | Detect the fill | 15 | The stream is not the record (D-14); a REST read of open orders every 15 s bounds detection. Cost: 4 requests per minute against Alpaca's client budget of 100 (THR-5); 1 per 15 s against Kite's 5 per second (THR-4). |
| STG-C2 | Build the stop, write its audit record | 2 | assumed (A-71) |
| STG-C3 | Wait for the rate limiter | 6 x N | N = entries of this strategy still unprotected or unsent; stops go first ([DEFAULT-41]) |
| STG-C4 | Submit and acknowledge | 10 | as STG-B6 |

Bound for the last of N simultaneous fills: 15 + 2 + 6 x N + 10 = 27 + 6 x N seconds. One fill:
33 s. Twenty at once: 147 s. Hard deadline for any fill: 180 s from the fill.

When blown: unsent entries for that market are dropped; open unfilled entry orders are cancelled
(cancels do not count toward spacing); a critical alert is raised; the stop placement is retried
once (PE-7). The system does not sell the position itself (HP-4). The kill switch remains
available.

Edge cases:
- The fill and the detection straddle a REST failure: detection time is unbounded. After 60 s
  [ASSUMPTION, A-71] without a successful read during an order job the market is treated as
  broker-down (PE-12):
  no further entries; reconcile on return, stops first.
- Partial fills: the stop must follow the filled quantity. Each change is a modification and
  counts ([DEFAULT-5]). With N positions filling in parts and one strategy, a given stop can be
  amended at most once every 6 x N seconds: every 120 s for N = 20. Between amendments part of
  the position is unprotected. The amendment policy is P3.4's (OQ-63); the arithmetic is the
  constraint it must respect.
- India: a sell GTT needs DDPI/POA or a daily TPIN authorisation (F-11). Without it the GTT is
  rejected and the 180 s deadline is certain to be blown. This is a go-live precondition, not a
  latency matter.
- A stop fires on the day of entry (HP-4): no further stage here; it is seen at the next
  reconciliation.
- The entry fills in the closing minutes: the same 180 s applies. A GTT placed after 15:30 does
  not trigger until the next session (F-11).

### 10.5 Intraday path that exists: kill-switch flatten

Anchor: the trip. The design of this path is P2.10's. The time implied by the upstream rules is
set out so that P2.10 inherits a number.

| ID | Stage | Budget, s | Derivation |
|----|-------|-----------|------------|
| STG-K1 | Cancel open entries and resting stops in the market that is in session | 30 | 40 cancels; the kill switch uses the half of each limit the trading process leaves it (THR edge case): Alpaca 100 per minute gives 24 s; Kite 5 per second gives 8 s |
| STG-K2 | Confirm the cancels by a REST read | 10 | assumed |
| STG-K3 | Submit exits | 3 x N | global spacing ([DEFAULT-5]); 20 positions: 19 gaps = 57 s, budgeted 60 |
| STG-K4 | Acknowledge and read back fills | 20 | PE-10: an India exit is not complete until the fill is read |

Bound: 60 + 3 x N seconds; 120 s for 20 positions.

When blown: the kill switch stays tripped; the manual runbook is the path (P6.4). Nothing is
retried blind (D-15).

Edge cases:
- Only one market is ever in session at a time (A-75), so N is one account's positions.
- The other market is closed: its positions cannot be flattened; the trip cancels its working
  orders and blocks it. Its resting stops are left in place.
- A stop must be cancelled before its position's exit is sent, or the two together can sell more
  than is held ([DEFAULT-4] edge case). Between the cancel and the exit the position has no
  stop: at most 30 + 10 + 3 x N seconds.
- An India exit is a market order with protection and may not fill (UP-12, PE-10): K4 reports
  it; the budget does not make it fill.
- Whether the kill switch may ignore the 3 s spacing is P2.10's decision (constitution Q4). If
  it may, K3 becomes one burst and the bound falls to about 60 s. The exchange threshold of 10
  orders per second (F-2) cannot be ignored.

### 10.6 Comparison: an intraday exit on 1-minute bars (ADR-13 option D, not built)

| Stage | Budget, s | Basis |
|-------|-----------|-------|
| Bar arrives after the minute closes | 2.0 | assumed |
| Validate the bar | 0.2 | assumed |
| Evaluate the exit rule | 0.3 | assumed |
| Risk engine | 0.1 | assumed |
| Audit write, two sinks, flushed | 0.2 | assumed |
| Rate limiter | 0 to 3.0 | [DEFAULT-5] |
| Broker round trip and acknowledgement | 2.0 | assumed; VM in India, broker in the US for one market |
| Total, single exit | 7.8, budgeted 10 | |

For k simultaneous exits the last waits 3 x (k - 1) s more: 57 s for 20, a total of 67 s. That
is longer than the bar interval. Under [DEFAULT-5] a 20-position exit on 1-minute bars cannot
finish before the next bar closes. The spacing rule, not compute, would be the binding
constraint of an intraday design.

## 11. Backtest cost

All timings are assumptions (A-64). They are to be replaced by a measured benchmark in P5.1
(OQ-62). The structure of the calculation is the deliverable; the minutes are unmeasured
assumptions and are labelled as such everywhere they appear.

### 11.1 Shape of a walk-forward run

- History: 2,520 sessions per market.
- First training window: 3 years = 756 sessions (assumed; P5.2 owns it).
- Step: one quarter = 63 sessions (ADR-07 consequence).
- Windows per market: (2,520 - 756) / 63 = 28 exactly. Both markets: 56.
- Out-of-sample sessions per market: 28 x 63 = 1,764.

### 11.2 Compute

| Item | Assumed time | Arithmetic |
|------|--------------|------------|
| One model fit | 6 min | A-64 |
| Simulating one market-session | 0.5 s | A-64 |
| Feature build, once per run | 20 min | A-64 |
| One walk-forward window (fit plus 63 sessions simulated) | 6.525 min | 6 + 63 x 0.5 / 60 |
| Full 10-year run, both markets | 398 min = 6.63 h | 56 x 6 + (2 x 2,520 x 0.5) / 60 + 20 = 336 + 42 + 20 |

Cost:
- Cash cost of a run on the live VM: USD 0.00. The VM is a flat monthly price with a cap (F-65).
- Amortised cost, at the VM's hourly rate of USD 0.14286 (F-65): full run 6.63 x 0.14286 =
  USD 0.95; one window 6.525 / 60 x 0.14286 = USD 0.016.
- A hyperparameter search of 50 trials (assumed), each a full set of fits: 50 x 56 x 6 min =
  16,800 min = 280 h. Amortised USD 40.00. In wall-clock time at 12 to 18.6 offline hours a day
  (section 8.3): 15 to 23 days.

The scarce resource is offline hours on the one VM, not money. A search that takes three weeks
does not fit comfortably inside a quarter that must also hold an ADR-08 evaluation.

### 11.3 LLM inside the backtest (not adopted, [DEFAULT-36])

- Out-of-sample sessions only: 1,764 x 2 markets x 10 candidates = 35,280 calls. At USD 0.0042:
  USD 148.18. At the off-peak rate, which a batch job can choose: USD 74.09.
- Every session: 2,520 x 2 x 10 = 50,400 calls; USD 211.68 at peak.

This is the one place in the whole design where an LLM bill reaches the USD 200 figure. It is
not adopted, for a reason that is not cost: a model with knowledge of the test period makes the
backtest look-ahead biased, and that cannot be priced away. Historical news with licence to
store and process is also unverified (OQ-37). P5.1 owns the final ruling.

Edge cases:
- A run is interrupted by a pause (8.3): no cost effect; longer wall-clock time.
- India results from Kite history are survivorship-biased ([DEFAULT-29]); the compute cost is
  the same, the result is not evidence.
- Fewer than 28 windows are possible if less than 10 years of validated history exists for a
  market: cost scales with the window count.
- Shared vCPUs make a fit's duration variable (8.5): a run is reproducible in result (fixed
  seeds, NB-24), not in duration.

## 12. Sensitivity

### 12.1 SENS-1: total monthly cost against bar frequency, universe size and gate width

USD per month, priced lines only, LLM at the bound of USD 0.0063 per call, excluding the INR 500
Kite line (add USD 5.56 at R = 90). Storage is bars only, 10 years: the whole-market daily base
of 9.67 GB (2.42 GB compressed) plus intraday bars for the universe.

| Frequency | Universe per market | Bars before, GB | Bars after, GB | Data plan | Fixed | W = 5 | W = 10 | W = 20 | W = 50 |
|-----------|---------------------|-----------------|----------------|-----------|-------|-------|--------|--------|--------|
| 1d | 100 | 9.67 | 2.42 | Massive Developer, 79 | 186.00 | 187.32 | 188.65 | 191.29 | 199.23 |
| 1d | 500 (decided) | 9.67 | 2.42 | Massive Developer, 79 | 186.00 | 187.32 | 188.65 | 191.29 | 199.23 |
| 1d | 2,000 | 9.67 | 2.42 | Massive Developer, 79 | 186.00 | 187.32 | 188.65 | 191.29 | 199.23 |
| 5m | 100 | 16.61 | 3.11 | Massive Advanced, 199 | 306.00 | 407.21 | 508.42 | 710.84 | 1,318.10 |
| 5m | 500 | 44.37 | 5.89 | Massive Advanced, 199 | 306.00 | 407.21 | 508.42 | 710.84 | 1,318.10 |
| 5m | 2,000 | 148.47 | 16.30 | Massive Advanced, 199 | 306.00 | 407.21 | 508.42 | 710.84 | 1,318.10 |
| 1m | 100 | 44.37 | 5.89 | Massive Advanced, 199 | 306.00 | 812.05 | 1,318.10 | 2,330.19 | 5,366.48 |
| 1m | 500 | 183.17 | 19.77 | Massive Advanced, 199 | 306.00 | 812.05 | 1,318.10 | 2,330.19 | 5,366.48 |
| 1m | 2,000 | 703.68 | 71.82 | Massive Advanced, 199 | 306.00 | 812.05 | 1,318.10 | 2,330.19 | 5,366.48 |

Arithmetic for one cell: 5m, W = 10: 306 + 3,213 x 10 x 0.0063 = 306 + 202.42 = 508.42.
Storage for 5m, 500: 34.70 + 9.67 = 44.37 before; 3.47 + 2.42 = 5.89 after. For a universe of u
per market, intraday rows = u x (bars_US + bars_IN) x 2,520: 5m, 100: 38,556,000 rows = 6.94 GB;
1m, 2,000: 3,855,600,000 rows = 694.01 GB.

What the table shows:
- Universe size does not move cost at any frequency. At daily frequency it does not even move
  storage, because the ranking needs the whole market regardless. At intraday frequency it moves
  storage, but every compressed figure fits the 320 GiB disk. The 1m, 2,000 case does not fit
  uncompressed (703.68 GB against 343.6 GB) and would need compression during backfill.
- Gate width moves cost by USD 0.26 per unit at daily frequency and by USD 20 and USD 101 per
  unit at 5-minute and 1-minute frequency.
- Bar frequency is the only lever that matters: it multiplies LLM calls by 76.5 (5m) or 382.5
  (1m) and forces a real-time data plan.
- VM cost is held constant across the table. That is an assumption for the intraday rows
  (section 6.4 suggests it holds; it was not measured).

### 12.2 One-at-a-time changes from the decided design (W = 10, USD 188.65 plus INR 500)

| Change | New USD total | Difference |
|--------|---------------|------------|
| VM: DigitalOcean Basic 8 GiB (rejected in 8.2) | 140.65 | -48.00 |
| VM: Lightsail 16 GB, Mumbai (F-68) | 176.65 | -12.00 |
| VM: DigitalOcean General Purpose 16 GiB, dedicated CPU, plus an unpriced volume | 218.65 | +30.00 |
| VM: `LARGEST_VM_IN_BUDGET` at USD 252 | 344.65 | +156.00 |
| Massive Starter after the backfill (UP-36) | 138.65 | -50.00 |
| Massive Advanced (20+ years, includes financials, F-48) | 308.65 | +120.00 |
| Alpaca Algo Trader Plus added (F-27) | 287.65 | +99.00 |
| WAL archive kept 30 days (9.3) | 198.81 | +10.16 (11.16 less the 1.00 already in CL-05) |
| Planning tokens replaced by capped tokens, bound | 195.07 | +6.42 (9.07 - 2.65) |
| LLM path US only (UP-24) | 187.32 | -1.32 |
| Every LLM call off-peak, no double billing | 186.88 | -1.76 |

### 12.3 Sensitivity of the unverified counts

| Input | If it is half | If it is double |
|-------|---------------|-----------------|
| N_US, N_IN (A-57, A-58) | Bars 4.83 GB; India background ingest (4,401 - 520) s = 65 min | Bars 19.34 GB; India background ingest (17,606 - 520) s = 17,086 s = 284.8 min, 14 s inside its 17,100 s window: any retry would make it yield and finish as a data job |
| B, bytes per row (A-59) | Bars 4.83 GB | Bars 19.34 GB |
| Tokens per call ([DEFAULT-37]) | LLM line 1.32 | LLM line 5.29; hard cap is 4 times planning input |
| Fit time (A-64) | Full run 3.8 h; search 140 h | Full run 12.2 h; search 560 h, which is 30 to 47 days of offline time and does not fit a quarter with an evaluation |

None of the first three changes the VM or the monthly total by more than USD 3. The fourth is
the one that can break the plan, and it is the least known.

## 13. Typed form

Entities this spec defines: a cost line, a stage budget, the LLM budget, a container limit and
the capacity plan. `Currency` is the P0.1 type; it is re-declared so the block runs alone.

### 13.1 Models

```python
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class Currency(StrEnum):
    USD = "USD"
    INR = "INR"


class CostBasis(StrEnum):
    VERIFIED_PRICE = "VERIFIED_PRICE"
    ASSUMPTION = "ASSUMPTION"
    UNPRICED = "UNPRICED"


class PipelinePath(StrEnum):
    DAILY_DECISION = "DAILY_DECISION"
    DAILY_ORDER = "DAILY_ORDER"
    POST_FILL_PROTECT = "POST_FILL_PROTECT"
    KILL_FLATTEN = "KILL_FLATTEN"


class StageAnchor(StrEnum):
    SESSION_CLOSE = "SESSION_CLOSE"
    NEXT_SESSION_OPEN = "NEXT_SESSION_OPEN"
    FILL_AT_BROKER = "FILL_AT_BROKER"
    KILL_TRIP = "KILL_TRIP"


class OverrunAction(StrEnum):
    YIELD_BACKGROUND = "YIELD_BACKGROUND"
    EXCLUDE_INSTRUMENT = "EXCLUDE_INSTRUMENT"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    SKIP_CYCLE = "SKIP_CYCLE"
    DROP_UNSENT_ORDERS = "DROP_UNSENT_ORDERS"
    RECONCILE_UNKNOWN_OUTCOME = "RECONCILE_UNKNOWN_OUTCOME"
    DISABLE_ENTRIES_AND_ESCALATE = "DISABLE_ENTRIES_AND_ESCALATE"
    ESCALATE_MANUAL_RUNBOOK = "ESCALATE_MANUAL_RUNBOOK"


_ANCHOR_OF_PATH = {
    PipelinePath.DAILY_DECISION: StageAnchor.SESSION_CLOSE,
    PipelinePath.DAILY_ORDER: StageAnchor.NEXT_SESSION_OPEN,
    PipelinePath.POST_FILL_PROTECT: StageAnchor.FILL_AT_BROKER,
    PipelinePath.KILL_FLATTEN: StageAnchor.KILL_TRIP,
}

CostLineId = Annotated[str, StringConstraints(strict=True, pattern=r"^CL-(0[1-9]|[1-9][0-9])$")]
StageId = Annotated[str, StringConstraints(strict=True, pattern=r"^[ABCK][0-9]{1,2}[a-z]?$")]
ShortText = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=200)]
ContainerName = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-z][a-z0-9_]{1,30}$")]


class CostLine(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    line_id: CostLineId
    description: ShortText
    amount_per_month: Decimal | None = Field(ge=Decimal("0"), le=Decimal("100000"))
    currency: Currency
    basis: CostBasis
    source_ref: ShortText

    @model_validator(mode="after")
    def _amount_matches_basis(self) -> "CostLine":
        if (self.basis is CostBasis.UNPRICED) != (self.amount_per_month is None):
            raise ValueError("amount_per_month is None if and only if basis is UNPRICED")
        return self


class StageBudget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    stage_id: StageId
    path: PipelinePath
    anchor: StageAnchor
    budget_s: int = Field(ge=0, le=21600)
    budget_s_per_unit: int = Field(default=0, ge=0, le=600)
    blocking: bool
    on_overrun: OverrunAction

    @model_validator(mode="after")
    def _anchor_matches_path(self) -> "StageBudget":
        if self.budget_s == 0 and self.budget_s_per_unit == 0:
            raise ValueError("a stage must have a fixed or a per-unit budget")
        if _ANCHOR_OF_PATH[self.path] is not self.anchor:
            raise ValueError("anchor does not belong to this path")
        if not self.blocking and self.on_overrun is not OverrunAction.YIELD_BACKGROUND:
            raise ValueError("a non-blocking stage can only yield")
        return self


class LlmBudget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    gate_width_per_market_per_session: int = Field(default=10, ge=1, le=50)
    planning_input_tokens_per_call: int = Field(default=8000, ge=1, le=32000)
    planning_output_tokens_per_call: int = Field(default=1500, ge=1, le=4000)
    max_input_tokens_per_call: int = Field(default=32000, ge=1, le=32000)
    max_output_tokens_per_call: int = Field(default=4000, ge=1, le=4000)
    call_deadline_s: int = Field(default=120, ge=1, le=120)
    max_attempts_per_candidate: int = Field(default=2, ge=1, le=2)
    max_concurrent_calls: int = Field(default=1, ge=1, le=1)
    monthly_spend_cap_usd: Decimal = Field(default=Decimal("25"), ge=Decimal("0"), le=Decimal("500"))

    @model_validator(mode="after")
    def _planning_within_caps(self) -> "LlmBudget":
        if self.planning_input_tokens_per_call > self.max_input_tokens_per_call:
            raise ValueError("planning input tokens exceed the hard cap")
        if self.planning_output_tokens_per_call > self.max_output_tokens_per_call:
            raise ValueError("planning output tokens exceed the hard cap")
        return self

    def stage_budget_s(self) -> int:
        return (
            self.gate_width_per_market_per_session
            * self.max_attempts_per_candidate
            * self.call_deadline_s
        )


class ContainerLimit(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    name: ContainerName
    memory_mib: int = Field(ge=64, le=65536)
    cpus: Decimal = Field(gt=Decimal("0"), le=Decimal("64"))
    pausable_offline: bool = False


class CapacityPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    vm_memory_mib: int = Field(default=16384, ge=8192, le=32768)
    vm_vcpus: int = Field(default=8, ge=4, le=8)
    vm_disk_gib: int = Field(default=320, ge=160, le=640)
    host_reserved_memory_mib: int = Field(default=1024, ge=512, le=4096)
    disk_alert_pct: int = Field(default=70, ge=1, le=99)
    disk_deny_entries_pct: int = Field(default=85, ge=1, le=99)
    containers: tuple[ContainerLimit, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _fits(self) -> "CapacityPlan":
        names = [c.name for c in self.containers]
        if len(names) != len(set(names)):
            raise ValueError("duplicate container name")
        used = sum(c.memory_mib for c in self.containers) + self.host_reserved_memory_mib
        if used > self.vm_memory_mib:
            raise ValueError("container memory limits plus host reserve exceed VM memory")
        if self.disk_alert_pct >= self.disk_deny_entries_pct:
            raise ValueError("disk alert threshold must be below the deny threshold")
        for c in self.containers:
            if c.cpus > self.vm_vcpus:
                raise ValueError("a container cpu limit exceeds the VM vCPU count")
        return self
```

Evidence: the block was executed on 2026-10-13 with Python 3.11.9 and Pydantic 2.13.5. Accepted:
a `CapacityPlan` built from the nine containers of section 8.2 (limits plus host reserve sum to
16,384); a default `LlmBudget` (`stage_budget_s()` returns 2,400; 12,000 at width 50); gate
widths 1 and 50; spend caps 0 and 500; a priced and an unpriced `CostLine`; a blocking and a
non-blocking `StageBudget`; `disk_alert_pct` 84 against 85. Rejected as expected (29 cases): a
priced line with no amount; an unpriced line with an amount; a float amount; a negative amount;
line id `CL-1`; a plain string for `currency`; an anchor that does not belong to the path; a
non-blocking stage with an action other than yield; a stage whose fixed and per-unit budgets are both 0; budgets of 21,601 and 5.0; stage id `Z1`;
gate widths 0 and 51; an input cap of 32,001; planning tokens above the cap; a deadline of 121;
concurrency 2; a float spend cap; a spend cap of 500.01; an extra field; container limits summing
to 16,385; a duplicate container; alert threshold equal to deny threshold; no containers; a 4 GiB
VM; an upper-case container name; a container CPU limit above the VM's vCPUs; assignment after
construction. Not run on Python 3.12 or later (R-4).

### 13.2 Fields

No field carries a time of day or a date, so timezone is "none" for every row. No field is
nullable except `CostLine.amount_per_month`.

| Model.field | Type | Unit | Nullable | Valid range | A violation means |
|-------------|------|------|----------|-------------|-------------------|
| CostLine.line_id | str | none | no | `CL-01` to `CL-99`, two digits | a cost with no stable identifier cannot be reconciled to an invoice; rejected (E-15) |
| CostLine.description | str | none | no | 1 to 200 characters | E-15 |
| CostLine.amount_per_month | Decimal or None | currency units per calendar month | yes | None exactly when `basis` is `UNPRICED`; otherwise 0 to 100,000 inclusive | a price that was guessed, or a known price left out; rejected (E-15). `float` is rejected (NB-3). |
| CostLine.currency | Currency | none | no | `USD` or `INR` | E-15. No conversion is implied by any field (ADR-15). |
| CostLine.basis | CostBasis | none | no | one of three values | a number of unknown standing breaks RULE-2; E-15 |
| CostLine.source_ref | str | none | no | 1 to 200 characters; an `F-n`, `A-n`, `OQ-n` or section reference | E-15 |
| StageBudget.stage_id | str | none | no | `A`, `B`, `C` or `K`, then 1 or 2 digits, then an optional lower-case letter | E-16 |
| StageBudget.path | PipelinePath | none | no | one of four values | E-16 |
| StageBudget.anchor | StageAnchor | none | no | the one anchor of that path | a budget measured from the wrong event; rejected (E-16) |
| StageBudget.budget_s | int | seconds, monotonic; the fixed part of the budget | no | 0 to 21,600 inclusive; not 0 when the per-unit part is also 0 | a stage with no bound, or one longer than the cycle; rejected (E-16) |
| StageBudget.budget_s_per_unit | int | seconds per unit of the stage's scale: gate width W for STG-A7 (240), unprotected entries N for STG-C3 (6), positions N for STG-K3 (3) | no | 0 to 600; 0 for every other stage. Stage budget = fixed part + per-unit part x scale | E-16 |
| StageBudget.blocking | bool | none | no | true or false | E-16 |
| StageBudget.on_overrun | OverrunAction | none | no | one of eight values; `YIELD_BACKGROUND` exactly for non-blocking stages | an overrun with no defined consequence; rejected (E-16) |
| LlmBudget.gate_width_per_market_per_session | int | candidates | no | 1 to 50; default 10 ([DEFAULT-17]) | above 50 the LLM stage cannot fit the cycle deadline with any margin; rejected (E-17) |
| LlmBudget.planning_input_tokens_per_call | int | tokens | no | 1 to 32,000 and at most the input cap | E-17 |
| LlmBudget.planning_output_tokens_per_call | int | tokens | no | 1 to 4,000 and at most the output cap | E-17 |
| LlmBudget.max_input_tokens_per_call | int | tokens | no | 1 to 32,000 | E-17; at run time a larger packet means the call is not sent (E-19) |
| LlmBudget.max_output_tokens_per_call | int | tokens | no | 1 to 4,000 | E-17 |
| LlmBudget.call_deadline_s | int | seconds | no | 1 to 120 (PE-14) | E-17 |
| LlmBudget.max_attempts_per_candidate | int | attempts | no | 1 or 2 (primary, then fallback once) | a retry loop; rejected (E-17) |
| LlmBudget.max_concurrent_calls | int | calls | no | exactly 1 (THR-11, THR-12) | E-17 |
| LlmBudget.monthly_spend_cap_usd | Decimal | USD per UTC calendar month | no | 0 to 500 inclusive; default 25 | E-17. A cap of 0 is valid and means the LLM is never called. |
| ContainerLimit.name | str | none | no | lower-case, 2 to 31 characters | E-18 |
| ContainerLimit.memory_mib | int | MiB | no | 64 to 65,536 | E-18 |
| ContainerLimit.cpus | Decimal | vCPUs | no | above 0, at most 64, and at most the VM's vCPUs | E-18 |
| ContainerLimit.pausable_offline | bool | none | no | true only for the offline container | a live container marked pausable would be frozen during a cycle; caught by the start-up check in E-18 |
| CapacityPlan.vm_memory_mib | int | MiB | no | 8,192 to 32,768; default 16,384 | E-18 |
| CapacityPlan.vm_vcpus | int | vCPUs | no | 4 to 8; default 8 | E-18 |
| CapacityPlan.vm_disk_gib | int | GiB | no | 160 to 640; default 320 | E-18 |
| CapacityPlan.host_reserved_memory_mib | int | MiB | no | 512 to 4,096; default 1,024 | E-18 |
| CapacityPlan.disk_alert_pct | int | percent of the filesystem used (70 means 70%, A-4) | no | 1 to 99 and strictly below the deny threshold | E-18 |
| CapacityPlan.disk_deny_entries_pct | int | percent used | no | 1 to 99; default 85 | E-18 |
| CapacityPlan.containers | tuple of ContainerLimit | none | no | at least 1; unique names; limits plus host reserve at most VM memory | the VM is over-committed; rejected (E-18) |

`LlmBudget` and `CapacityPlan` accept ranges, unlike `ScopeDecisions`, because they are budgets
that HITL-4 may move inside stated bounds. P1.3 turns them into policy keys whose defaults equal
the defaults here and tests that equality.

### 13.3 Configuration keys

| Key | Type and unit | Decided value | Valid range |
|-----|---------------|---------------|-------------|
| `budget.cycle_deadline_s` | int, seconds after session close | 21600 | 7,320 + 240 x gate width, up to 28,800 |
| `budget.cycle_settle_wait_s` | int, seconds | 2700 | 900 to 7,200 |
| `budget.order_job_lead_s` | int, seconds before the open | 1800 | 1,200 to 3,600 |
| `budget.order_submit_window_s` | int, seconds after the open | 600 | 60 to 900 |
| `budget.order_ack_timeout_s` | int, seconds | 10 | 1 to 60 |
| `budget.fill_detect_interval_s` | int, seconds | 15 | 5 to 60 |
| `budget.post_fill_stop_deadline_s` | int, seconds after the fill | 180 | 33 to 600 |
| `budget.kill_flatten_deadline_s` | int, seconds after the trip | 120 | 60 to 600 |
| `llm.monthly_spend_cap_usd` | Decimal, USD | 25 | 0 to 500 |
| `llm.max_input_tokens_per_call` | int, tokens | 32000 | 1 to 32,000 |
| `llm.max_output_tokens_per_call` | int, tokens | 4000 | 1 to 4,000 |
| `capacity.disk_alert_pct` | int, percent | 70 | 1 to 99 |
| `capacity.disk_deny_entries_pct` | int, percent | 85 | 1 to 99 |
| `backup.wal_archive_timeout_s` | int, seconds | 60 | 1 to 60 (ADR-10 RPO) |
| `backup.pitr_window_days` | int, days | 7 | 1 to 90 |
| `backup.base_backups_retained` | int, count | 7 | 2 to 30 |

Every key is changed only through HITL-4 or HITL-5. None is reachable by an LLM (INV-2).

## 14. Error paths

| # | Condition | Detected by | Fail-closed behaviour |
|---|-----------|-------------|-----------------------|
| E-15 | A `CostLine` is invalid | Pydantic `ValidationError` | The cost table does not load; the cost report is not produced. No trading effect. |
| E-16 | A `StageBudget` is invalid, or the blocking budgets of the decision path plus 240 x gate width exceed `budget.cycle_deadline_s` | Pydantic; a start-up check in the scheduler | The scheduler does not start. No decision cycle and no order job run. Resting stops are untouched. |
| E-17 | An `LlmBudget` is invalid | Pydantic | The process that calls the LLM does not start; the LLM step is unavailable; the deterministic path is unaffected (INV-2). |
| E-18 | A `CapacityPlan` is invalid, or a container other than `offline` is marked pausable | Pydantic; a start-up check | The stack is not deployed (HITL-5 fails). |
| E-19 | A packet would exceed `llm.max_input_tokens_per_call` | Token count before the call | The call is not sent. The candidate is treated as LLM unavailable. The packet is not silently truncated here; truncation rules are P4.1's. |
| E-20 | The monthly spend cap would be exceeded by the next call | The spend accumulator (7.5) | The call is not sent; LLM unavailable for that candidate; alert. |
| E-21 | A response carries no usage figures | The LLM client | The call is charged at the capped-call peak price in the accumulator. The response itself is handled by P4.2's rules. |
| E-22 | A blocking stage of the decision cycle exceeds its budget | The scheduler, monotonic clock | The stage's `on_overrun` action (10.2). Never an extension. |
| E-23 | The cycle deadline passes | The scheduler | Cycle skipped (10.1). Counts toward the ADR-03 trigger unless a vendor cause is recorded. |
| E-24 | The order job reaches open + 600 s with intents unsent | The scheduler | Unsent intents are dropped and recorded as not sent. |
| E-25 | A fill has no acknowledged stop 180 s after the fill | The order job | Entries disabled for that market for the session; open entry orders cancelled; critical alert; one retry of the stop (10.4). |
| E-26 | Disk use is above 85% | P6.1 metric, read by the risk pre-check | New entries denied in both markets; exits and stops continue. |
| E-27 | The disk-use metric is missing or stale | The risk pre-check | Treated as above 85% (INV-6): new entries denied. |
| E-28 | The offline container exceeds its memory limit | The container runtime | That container is killed. Live containers are unaffected. The job is reported failed and is not restarted automatically. |
| E-29 | The offline container is not paused when a cycle starts (the pause call failed) | The scheduler checks the container state before STG-A1 | The cycle proceeds; an alert is raised; the session is flagged so that a missed deadline is not counted as a capacity miss. |
| E-30 | A provider changes a price used in section 9 | The monthly invoice comparison (7.5) | The price table is updated through HITL-4. This spec's totals are stale until re-issued; the spend cap continues to bound the LLM line. |
| E-31 | The WAL archive grows past the bucket's bundle | Object-storage usage metric | Overage is billed (CL-05); alert above 300 GiB [ASSUMPTION, A-70]. Archiving is never stopped to save money (ADR-10). |
| E-32 | The kill-switch flatten exceeds 60 + 3 x N seconds | The kill-switch process | Stays tripped; manual runbook (10.5). |

## 15. Non-blocking details resolved in this spec

| # | Detail | Resolution |
|---|--------|------------|
| NB-45 | GB or GiB | GB is 10^9 bytes and is used for data volume; GiB is 2^30 and is used wherever a vendor sells in GiB (F-65, F-67) and for memory. 320 GiB = 343.6 GB. |
| NB-46 | "Month" | 21 sessions for call counts (252 / 12). Calendar month for invoices. The VM's monthly price is a cap, reached at 672 hours (F-65): 0.14286 x 672 = 96.00. |
| NB-47 | Money type and rounding | `Decimal` everywhere (NB-3). Displayed USD figures are rounded half to even to 2 places; sums are computed before rounding, which is why 188.646 appears as both 188.64 (sum of rounded lines) and 188.65. |
| NB-48 | Token price unit | USD per 1,000,000 tokens, as the providers state it. |
| NB-49 | Month boundary for the LLM spend cap | Calendar month in UTC. Providers' invoice months are not verified; UTC is unambiguous and has no daylight saving. |
| NB-50 | Inclusive bounds | A stage that takes exactly its budget passes. A submission at exactly open + 600 s is allowed. Spend equal to the cap is allowed. Disk use of exactly 85% is not a breach. All consistent with NB-2. |
| NB-51 | Off-by-one in spacing | N submissions need N - 1 gaps: 20 at 6 s take 114 s, not 120. The number that fit in a window of T seconds is floor(T / gap) + 1. |
| NB-52 | Overlap in wall-clock time | The India cycle (16:15 to 21:30 `Asia/Kolkata`) overlaps the US order job (18:30 to 19:15 in US daylight time, 19:30 to 20:15 otherwise). They are different markets and independent jobs (ADR-02). The global order spacing is unaffected because the India cycle sends no orders. |
| NB-53 | Daylight saving | Every budget is anchored to a session event, so US clock changes move nothing. Only the DeepSeek peak windows are fixed in UTC (NB-40); section 7.1 checks both offsets. |
| NB-54 | Half-days | The close anchor is the early close (NB-15). The order job is anchored to the open and is unaffected. |
| NB-55 | Weekends and holidays | "Next session" is by calendar (NB-14). The end-to-end wall-clock bound in 10.3 is for consecutive sessions; working time is the same on any day. |
| NB-56 | Percent units | `disk_alert_pct` 70 means 70% (A-4). Compression "ratio 4" means stored bytes are one quarter; "98%" in F-73 is a reduction, equal to ratio 50. |
| NB-57 | Seconds as integers | Budgets are whole seconds. The sub-second figures in 10.6 are a comparison only and define no contract. |
| NB-58 | Window count | (2,520 - 756) / 63 = 28 with no remainder, so there is no partial last window. With other inputs the last partial window is dropped, not padded. |
| NB-59 | Gate width is per market per session | 42 x W calls a month counts both markets. With one market disabled the count halves; the budget does not transfer to the other market. |
| NB-60 | Currency of the total | Two totals, USD and INR, are the record (ADR-15). The single USD figure uses R = 90, an assumed rate, for a headline only; no rule and no contract uses it. |
| NB-61 | Tick size, lot size, price rounding | Not relevant: no rule in this spec produces a price or a quantity. |
| NB-62 | Hours per month for amortisation | Backtest cost uses the hourly rate directly (USD 0.14286), not the monthly price divided by an assumed hour count. |

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|----------|-----------|-------------|-----------------------|
| D-24 | Size for the decided design (daily bars, whole market, no stream, no intraday exit pipeline). The prompt's minute-bar, open-minute and intraday-exit figures are labelled comparisons. | ADR-13, HP-1 to HP-5; UP-26. | Yes. | If the Owner adopts ADR-13 option D, sections 6, 7 and 10 are re-issued from the comparison figures. |
| D-25 | One VM: 16 GiB RAM, 8 shared vCPU, 320 GiB SSD; DigitalOcean Basic, Bangalore; USD 96 a month. Named bottleneck: RAM at the peak of an offline fit beside the live stack. | Section 8. [DEFAULT-33]. | Yes; a provider move also moves the static IP (UP-15). | CL-01, CL-03, CL-04; P6.4. |
| D-26 | Container memory and CPU limits as in section 8.2, summing exactly to the VM. | A limit turns a sizing error into one killed container instead of a swapping VM. | Yes. | P6.4 compose file. |
| D-27 | Offline work runs in one capped container that is paused during every decision cycle, order job and kill-switch trip, and has no broker credential. | UP-34; [DEFAULT-35]. | Yes. | P5.1, P6.6 scheduling. |
| D-28 | Decision-cycle deadline: close + 21,600 s. Stage budgets STG-A0 to STG-A9, each hard, each with a stated consequence. | Fits gate width 50 with 2,280 s spare; ends before the other market's order job. [DEFAULT-38]. | Yes, by HITL-4. | ADR-02 jobs, ADR-03 trigger. |
| D-29 | Whole-market ingest is split: universe and held instruments block the cycle; the rest runs in the background and may finish later as a data job. | The Kite throttle makes the full India ingest 147 minutes. [DEFAULT-39]. | Yes. | P2.1, P2.3. |
| D-30 | Order job: pre-checks from open - 1,800 s; submissions from the open to open + 600 s; 10 s acknowledgement timeout; job ends at open + 900 s. | Verifiable with what is known about both brokers; pre-open behaviour is not verified. | Yes; P3.2 may move it. | P3.2, P3.4. |
| D-31 | A fill must have an acknowledged stop within 180 s; bound 27 + 6 x N s; stops are queued ahead of unsent entries and count toward spacing. | HP-4 leaves the stop as the only intraday protection. [DEFAULT-41]. | Yes. | P3.4, P2.9. |
| D-32 | LLM: planning 8,000 / 1,500 tokens; hard caps 32,000 / 4,000; monthly spend cap USD 25; priced at peak; accounted from reported usage. | Makes the spend figure enforceable instead of a forecast. [DEFAULT-37]. | Yes, by HITL-4. | P4.1 packet size, P4.2. |
| D-33 | The LLM is not called inside backtests. | Look-ahead contamination; cost shown in 11.3. [DEFAULT-36]. | Yes; P5.1 rules. | P5.1, ADR-08 evidence. |
| D-34 | Backups: default 16 MB WAL segments, `archive_timeout` 60 s, 7-day point-in-time window, 7 base backups, one 250 GiB bucket. | Meets ADR-10 for under USD 7 a month; avoids an irreversible `initdb` choice. [DEFAULT-40]. | Retention: yes. Segment size: no. | P6.4. |
| D-35 | `LARGEST_VM_IN_BUDGET` for ADR-03: at most 32 GiB, 8 vCPU, USD 252 a month. | ADR-03 needs the size defined. | Yes. | ADR-03 trigger. |
| D-36 | Cost is recorded per currency. One combined USD figure is shown at an assumed rate for a headline and is used by no rule. | ADR-15. | Yes. | None. |
| D-37 | A cost with no verified price is listed as UNPRICED and is not estimated (CL-13 to CL-19). | RULE-1, D-9. | n/a | The total is a floor, not a forecast. |
| D-38 | Identifier series continue from P0.2. | D-10. | Yes. | Renumbering. |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|------------|------------------------|---------------|-----------------|
| A-47 | [DEFAULT-32] The ceiling covers all recurring platform cost and nothing per trade. | Not defined in any input (UP-27). | Owner, OQ-52. | Section 7.4 is read under the other column. |
| A-48 | [DEFAULT-33] DigitalOcean, Bangalore, Basic 16 GiB. | No provider is named upstream. | Owner, OQ-53. | CL-01, CL-03, CL-04. |
| A-49 | [DEFAULT-34] Whole-market daily history for the US and for NSE plus BSE. | ADR-14 requires it; the India scope is not stated. | P2.3 chooses the exchange for UNI-1 (P0.2 5.3). | India storage and ingest time fall by two thirds if NSE only. |
| A-50 | [DEFAULT-35] Offline work on the live VM, capped and paused. | STACK-1 names one VM. | Owner. | A second VM changes cost by one VM price. |
| A-51 | [DEFAULT-36] No LLM in backtests. | Not decided upstream. | P5.1. | USD 74 to 212 per run. |
| A-52 | [DEFAULT-37] 8,000 / 1,500 planning tokens; 32,000 / 4,000 caps. | No prompt or packet exists yet. | P4.1, P4.3 measure real packets. | LLM line scales linearly, bounded by the cap. |
| A-53 | [DEFAULT-38] Cycle deadline and order-job timings. | No timing is given upstream beyond "hours". | Paper trading, P6.5. | Budgets re-issued. |
| A-54 | [DEFAULT-39] Priority and background ingest. | Follows from the throttle arithmetic. | P2.1. | Cycle fixed time 249 minutes instead of 122. |
| A-55 | [DEFAULT-40] WAL and backup retention. | ADR-10 gives RPO and RTO only. | P6.4 restore drill. | CL-05. |
| A-56 | [DEFAULT-41] Stops count toward spacing and go first. | [DEFAULT-5] is silent on protective stops and GTTs. | Owner and P3.4, OQ-63. | Section 10.4 bound. |
| A-57 | 12,510 US tickers have a daily bar each session, constant over 10 years. | One example response for one date, seen as a search excerpt (F-74). OQ-19 is open. | OQ-56, OQ-57. | Section 12.3. |
| A-58 | 8,803 India listings (2,867 NSE + 5,936 BSE) have a daily bar each session, constant over 10 years, overlap not removed. | Secondary source (F-76). OQ-19 is open. | OQ-57. | Section 12.3. |
| A-59 | The row layout of 5.1; 9 bytes per numeric; index sizes of 31 and 22 bytes per row; 180 bytes per row in total. | P1.2 has not defined the table. | P1.2; measure `pg_total_relation_size` on a loaded sample. | Storage scales linearly; no cost effect below a factor of 10. |
| A-60 | Compression ratio 4 for daily bars and 10 for intraday bars. | The only documented figure is a ceiling of 98% (F-73). | OQ-61: measure on a year of real bars. | "After compression" figures. The disk is sized on uncompressed daily bars, so no capacity effect. |
| A-61 | The non-bar storage items of 5.4. | None exists yet. | P1.2, P1.4, P4.1, P6.1 as each is built. | Disk use; 27% at year five leaves a factor of three. |
| A-62 | Container memory limits; 150 features; fit peak three times the raw matrix. | Nothing has been built or measured. | OQ-62 benchmark. | A container is killed; limits are re-cut; at worst the 32 GiB class is needed (+USD 156). |
| A-63 | 20,000 rows per second per core for parse and validate; 50,000 rows per second for `COPY`; 50,000 tick packets per second per core; 250 bytes of WAL per row; 1 tick per instrument per second at the open. | No benchmark exists. | P2.1 benchmark. | None for the decided design, which uses 1.07 core-seconds a day. |
| A-64 | Fit 6 minutes; 0.5 s per simulated market-session; feature build 20 minutes; first window 3 years; 50 search trials. | No model, simulator or data exists. | OQ-62; P5.1, P5.2. | Section 12.3: at double, a search no longer fits a quarter. |
| A-65 | R = 90 INR per USD for the combined headline. | No rate source is selected (OQ-22) and none was looked up. | OQ-65. | The headline moves by USD 0.06 per rupee of error. Nothing else. |
| A-66 | 21 sessions a month; both markets gated to the full width every session. | A-25. | Calendars, P2.1. | Call counts within a few percent. |
| A-67 | Vendor daily data is final 45 minutes after the close. | Derived from F-27, F-48 and F-62; no vendor states a finalisation time for the daily bar. | OQ-59. | STG-A0 is lengthened; there are 11,880 s of slack at W = 10. |
| A-68 | Ten years of Kite daily candles need two requests per instrument. | Range per request is unstated (OQ-30). | OQ-30, OQ-58. | Backfill hours only. |
| A-69 | Thinking tokens are inside the output figures; a timed-out call may still be billed. | F-75: the pricing page does not say. | OQ-60. | Output cost; bounded by the cap. |
| A-70 | The stage budgets that are not derived (600, 900, 300, 120 s); the 10% invoice tolerance; the 300 GiB archive alert. | Nothing has been timed. | P6.5 paper trading. | Budgets re-cut inside 11,880 s of slack. |
| A-71 | Fill detection within 15 s; acknowledgement within 10 s; audit write within 2 s; 60 s without a successful order read means broker-down. | No broker latency is documented. | P3.1 against paper and live. | The 180 s post-fill deadline. |
| A-72 | The chosen plan, a reserved IPv4 and Spaces are available in or to the Bangalore region at the listed prices; invoice taxes are excluded. | The pricing pages are not per region. | OQ-54. | CL-01 to CL-05. |
| A-73 | A base backup is 19 GiB. | The database does not exist. | P6.4. | CL-05, cents. |
| A-74 | The extracts F-66, F-69 to F-73 and F-75 state their pages accurately. | Read by automated extraction. | Full read by the phase named in section 3. | Prices and PostgreSQL behaviour in sections 5, 8, 9. |
| A-75 | The India and US regular sessions never overlap. | Derived from A-26: India 09:15 to 15:30; US 19:00 to 01:30 or 20:00 to 02:30 in `Asia/Kolkata`. | Calendars, P2.1. | Section 10.5's N and 6.4's peak. |

Upstream assumptions this spec leans on and did not verify: A-25, A-26, A-41, A-42, A-43, A-45.

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|----------|---------------------|-----------------------------|--------------------|
| OQ-52 | What is the monthly cost ceiling, in which currency, and which costs does it cover (UP-27)? | Owner | Owner statement; `master-research-summary.md` if it holds the figure | Freeze of this spec |
| OQ-53 | Which cloud provider and region host the VM, and does any rule (SEBI or exchange static-IP rules, broker terms) require the address to be in India or tied to the client's own connection? | Owner; Zerodha; NSE | Zerodha "static-ip" support article read in full; NSE circular INVG67858; Owner decision | P6.4, India go-live |
| OQ-54 | DigitalOcean: are the Basic 16 GiB plan, reserved IPv4 addresses and Spaces offered in or to the Bangalore region at the listed prices; the price of block-storage volumes; the IOPS of the Droplet SSD; whether tax is added for a customer in India. | DigitalOcean | docs.digitalocean.com: regional availability matrix; volumes pricing; droplet limits; billing taxes page | P6.4 |
| OQ-55 | Lightsail: the CPU baseline percentage of the 16 GB bundle and how burst capacity accrues. | AWS | Lightsail documentation, "burstable performance" and instance metrics | Only if BQ-22 (b) is chosen |
| OQ-56 | Massive: primary read of the grouped daily bars endpoint (fields, `adjusted=false`, whether OTC tickers are included, whether a past date returns tickers since delisted); whether data fetched under Developer may be kept after a downgrade to Starter. | Massive | massive.com/docs/rest/stocks/aggregates (grouped daily); Massive terms | P2.1; UP-36 |
| OQ-57 | Primary counts: instruments with a daily bar per session on NYSE, NASDAQ, NSE and BSE, today and ten years ago (narrows OQ-19). | Exchanges; Massive | NSE and BSE listed-securities files (under licence, OQ-39); Massive tickers endpoint with `date` | P2.1 |
| OQ-58 | Kite: can an after-close `/quote` call serve as the session's daily bar (meaning of `ohlc.close` and `volume` after the close); maximum date range of one daily-candle request; time at which the day candle is final. | Zerodha | kite.trade/docs/connect/v3/market-quotes and /historical; Kite forum | P2.1 |
| OQ-59 | When is the daily bar for a session final and available: Massive Developer (a 15-minute-delayed plan), Alpaca Basic, Kite? | Vendors | Massive and Alpaca documentation on daily aggregates; Kite forum | P2.1; STG-A0 |
| OQ-60 | DeepSeek and OpenAI: are thinking tokens billed as output; default output limit; is a call abandoned by the client still billed; the usage fields in the response. | DeepSeek; OpenAI | api-docs.deepseek.com chat-completion reference and thinking-mode guide; developers.openai.com API reference | P4.2 |
| OQ-61 | TimescaleDB: measured compression ratio for daily bars with `segmentby` = instrument and yearly chunks; rows per compressed batch; whether the columnstore features are in the self-hosted image and under which licence. | P1.2; Tiger Data documentation | Load one year of real bars and compare `hypertable_size` before and after; Tiger Data docs on licence editions | P1.2 |
| OQ-62 | Measured on the chosen VM: model fit time, simulated session time, feature-build time, and peak memory of a fit. | P5.1 | A benchmark run in the offline container at its limits | P5.1, P5.2, P6.6 |
| OQ-63 | Do stop and GTT placements and amendments count toward RISK-10 and RISK-11; how often may a stop be amended during partial fills; may the kill switch ignore the spacing? | Owner; P2.9, P2.10, P3.4 | Ruling on BQ-30 and constitution Q4 | P2.9, P3.4 |
| OQ-64 | Does a WAL segment closed by a forced switch compress well (is the unused tail zero-filled), and which archive tool is used? | PostgreSQL documentation; P6.4 | postgresql.org continuous-archiving chapter; a measured test | P6.4 |
| OQ-65 | The USD/INR rate used for the combined cost headline (same source as OQ-22). | P0.2 follow-up | fbil.org.in reference rates | None; reporting only |
| OQ-66 | Earliest time each broker accepts a `day` limit order for the coming session, and how it is treated in the opening auction or pre-open. | Alpaca; Zerodha; NSE | docs.alpaca.markets orders page (pre-market submission); Kite orders and AMO documentation; OQ-49 | P3.2 |

Upstream questions that bear on this spec and remain open: OQ-16 (capital, section 9.5), OQ-19
(narrowed to OQ-57), OQ-21 (answered provisionally by CL-04; region open in OQ-54), OQ-22, OQ-30,
OQ-37, OQ-38, OQ-39 and OQ-40 (the unpriced lines), OQ-43, OQ-44, OQ-47.

## CONTRACTS EXPORTED

| Name | Kind (type/table/event/endpoint/config key) | Signature or schema | Consumers |
|------|---------------------------------------------|---------------------|-----------|
| F-65..F-76 | external fact identifier | Section 3 row, cited as `F-n`, with its verification level | P1.2, P4.2, P6.4 |
| DEFAULT-32..DEFAULT-41 | provisional default identifier | Section 1, cited as `[DEFAULT-n]`; not a ruling | P1.2, P2.1, P3.2, P3.4, P4.2, P5.1, P6.4 |
| CostBasis | type | `StrEnum`: `VERIFIED_PRICE`, `ASSUMPTION`, `UNPRICED` | P6.1 |
| PipelinePath | type | `StrEnum`: `DAILY_DECISION`, `DAILY_ORDER`, `POST_FILL_PROTECT`, `KILL_FLATTEN` | P1.2 (job-run records), P6.1 |
| StageAnchor | type | `StrEnum`: `SESSION_CLOSE`, `NEXT_SESSION_OPEN`, `FILL_AT_BROKER`, `KILL_TRIP` | P1.2, P6.1 |
| OverrunAction | type | `StrEnum`, 8 members, section 13.1 | P1.4 (audit event field), P2.7, P3.4, P6.1 |
| CostLine | type | frozen Pydantic v2 model, 6 fields, section 13.2 | P6.1 (cost report) |
| StageBudget | type | frozen Pydantic v2 model, 7 fields, section 13.2; budget = `budget_s` + `budget_s_per_unit` x scale | P1.3, scheduler (ADR-02), P6.1 |
| LlmBudget | type | frozen Pydantic v2 model, 9 fields; `stage_budget_s()` = width x attempts x deadline | P1.3, P4.2 |
| ContainerLimit, CapacityPlan | type | frozen Pydantic v2 models, 4 and 7 fields; limits plus reserve at most VM memory | P6.4 |
| CL-01..CL-19 | cost line identifier | Sections 9.1 and 9.2 | P6.1; any spec that adds a recurring cost |
| STG-A0..STG-A9, STG-A2a, STG-A2b | stage budget identifier | Section 10.2: seconds after session close; consequence on overrun | P2.1, P2.2, P2.4, P2.7, P4.1, P4.2, P2.8, P2.9 |
| STG-B0..STG-B6 | stage budget identifier | Section 10.3: relative to the next session open | P3.2, P3.4, P5.5 |
| STG-C1..STG-C4 | stage budget identifier | Section 10.4: bound 27 + 6 x N s, hard deadline 180 s after a fill | P3.3, P3.4 |
| STG-K1..STG-K4 | stage budget identifier | Section 10.5: bound 60 + 3 x N s after a trip | P2.10 |
| LARGEST_VM_IN_BUDGET | constant | at most 32 GiB RAM, 8 vCPU, USD 252 per month | ADR-03 trigger, P6.4 |
| SENS-1 | table | Section 12.1: USD per month by bar frequency, universe size and gate width | Owner; any ADR that revisits ADR-13 or [DEFAULT-17] |
| `budget.cycle_deadline_s`, `budget.cycle_settle_wait_s`, `budget.order_job_lead_s`, `budget.order_submit_window_s`, `budget.order_ack_timeout_s`, `budget.fill_detect_interval_s`, `budget.post_fill_stop_deadline_s`, `budget.kill_flatten_deadline_s` | config key | `int`, seconds; decided values and ranges in section 13.3 | P1.3, P3.2, P3.4, P2.10 |
| `llm.monthly_spend_cap_usd`, `llm.max_input_tokens_per_call`, `llm.max_output_tokens_per_call` | config key | `Decimal` USD; `int` tokens; section 13.3 | P1.3, P4.1, P4.2 |
| `capacity.disk_alert_pct`, `capacity.disk_deny_entries_pct` | config key | `int`, percent used; 70 and 85 | P1.3, P2.9, P6.1 |
| `backup.wal_archive_timeout_s`, `backup.pitr_window_days`, `backup.base_backups_retained` | config key | `int`; 60, 7, 7 | P1.3, P6.4 |
