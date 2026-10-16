---
id: SPEC-EDGE-ADR
version: 0.2
status: DRAFT
phase: EDGE-ADR — what this system competes on
depends_on: [SPEC-P0.1-DECISIONS ADR-05/ADR-13/ADR-14 (FROZEN), SPEC-P0.3-BUDGET (FROZEN), SPEC-P2N.13-FAST-FEEDS v0.1, master-research-summary.md]
produces: [EDGE-HYPOTHESIS, LATENCY-DECOMPOSITION, LATE-EXIT-COST-MODEL, CADENCE-END-STATE, EDGE-SUCCESS-CRITERIA]
---

# SPEC-EDGE-ADR — What this system actually competes on

The decision the programme never made. Every figure below is derived from the frozen ADR-13 and
ADR-14 parameters or from `SPEC-P2N.13`, and is reproducible from the stated inputs.

---

## 1. The owner target, and what in it is already built

> Every news item for a stock, covered the moment it appears anywhere on the internet, feeding a
> **live** analysis and decision platform — not a broker-style call from technical analysis alone,
> but a decision backed by live updates and current company state. India and world markets.
> Options included.

| Part of the target | Status |
|---|---|
| Multi-factor, not TA alone — 60 % fundamental / 20 % technical / 10 % sentiment + a structured thesis | **already the design** |
| Backed by current company state — fundamentals, filings, events | **already the design** |
| "The moment it appears" | conflicts with ADR-14 |
| "Live" decisioning | conflicts with ADR-14 |
| Options | conflicts with ADR-05 → #58 |

Two of five need no change. This ADR addresses the middle two.

---

## 2. Edge hypotheses, ranked

| # | Candidate edge | Real? | Defensible? | Measurement that proves or kills it |
|---|---|---|---|---|
| 1 | **Risk control and position sizing** | **Yes** | **Yes** — nobody can arbitrage your discipline away | Max drawdown vs the 15 % gate; realised vs modelled stop distances |
| 2 | **Systematic absence of emotional error** | **Yes** | **Yes** | Decision-to-execution fidelity: % of generated signals acted on without override |
| 3 | **Horizon patience** — willing to hold 15 days | **Yes** | Partly | Realised median hold inside the 8–25 day revisit band (ADR-13) |
| 4 | **Cross-source corroboration others skip** | Yes | Partly | Fabrication-attack suppression rate (#57) |
| 5 | **Breadth over under-followed names** | Yes | Partly | **But ADR-14's liquidity screen excludes the names where this bites** — see §5 |
| 6 | **Cost structure** | Partly | No | $/month vs AUM; it is a cost advantage, not an edge |
| 7 | **Latency to public news** | **No** | **No** | §3 — structurally unavailable at retail |

**The hypothesis:** this system's edge is **#1–#3 — discipline, risk control and patience — not
speed.** Everything in the architecture should be optimised for not losing money on the 5 % of
occasions that matter, and for staying out when conditions are poor. That is also precisely what
`master-research-summary.md` already concludes in "The Brutal Truth": the system's value is
capital protection, evidence-driven consistency, and knowing when to stay out.

---

## 3. The latency question, answered with numbers

From `SPEC-P2N.13` §3. Evidence grade carried through.

| Arrow | Figure | Evidence |
|---|---|---|
| Exchange terminal → TrueData WebSocket (IN) | **< 200 ms** | `[V]` vendor published |
| Source wire → RTPR WebSocket (US) | **< 500 ms** claimed | `[V]` vendor claim |
| Benzinga origination → TCP push (US) | "not delayed", no figure | `[V]` mechanism / `[U]` |
| Benzinga → Alpaca bundle → our REST poll | poll interval + vendor hop | `[U]` |
| EDGAR acceptance → dissemination | **not published** | `[U]` |
| **Web publication → our crawl detects** | **~7 s**, body at **~13 s** | derived, P2N.13 §3.1 |
| Our detection → decision | **today: up to ~17.75 h** | `[V]` P0.3 §504-505 |
| Our decision → order ack | ≤5 s budgeted on the exit path | `[V]` P0.3 §565 |

**Where a retail stack can be first: nowhere on the entry side.** A web page is a copy of
something a wire already distributed. The fastest path we can buy is ~200 ms from a vendor; firms
that trade on these events are already inside that window with direct feeds and colocation. The
crawl is 13–66× slower than the push tier and strictly downstream of it.

**But the dominant term is not any of the feed arrows — it is our own ~17.75 hours.** Every
latency decision is noise next to that, which is why §6 matters more than §3.

---

## 4. The exit-versus-entry asymmetry — and ADR-13 already resolved it

The reframe this ADR was asked to test turns out to be **already the frozen design**. ADR-13's
decision table, verbatim:

| Parameter | Value |
|---|---|
| Entry timing | Once per session, orders 09:45–10:15 ET. **"No intraday entries, ever (ADR-14)"** |
| Exit timing | **"Intraday permitted for stop-loss and exit-hierarchy triggers, on 5-minute bars for held instruments only"** |

And ADR-13's own commentary: *"The asymmetry in the last two rows is deliberate and load-bearing:
**getting out may be urgent; getting in never is.**"*

**So fast exits are not an amendment. They are already permitted, already budgeted (P0.3 §565,
≤5 s), and already have broker-side protective stops placed at entry.** What is missing is
narrower than it appeared on #37:

> The exit path is fast and price-triggered. It has **no news trigger**, because under ADR-14
> news arrives in a nightly batch.

That is the entire gap. It is a missing input to an existing fast path, not a new architecture.

---

## 5. What a news trigger is worth — the business case

Model: a thesis-breaking event (the exit hierarchy's HIGH tier — "thesis invalid, earnings miss
>10 %") arrives on a held name. Value of acting at news time rather than at the next session or
when the ATR stop fires.

Inputs, all from frozen specs: 20 slots, 16.8 round trips/slot/year → **336 position-holdings/year**
(ADR-13 Chain C/F); 80 % invested over 20 slots → **4 % average position weight** (ADR-14).

```
annual saving = E × f_intraday × f_not_already_stopped × Δ × w
```

**Base case** — E = 25 events/yr, f_intraday = 0.35, f_not_stopped = 0.50, Δ = 3 %, w = 4 %:

> **52.5 bps of NAV per year (0.53 %)**

| E/yr | Δ=2 % | Δ=3 % | Δ=5 % | Δ=8 % |
|---|---|---|---|---|
| 10 | 10.5 | 21.0 | 35.0 | 56.0 |
| **25** | 26.2 | **52.5** | 87.5 | 140.0 |
| 40 | 42.0 | 84.0 | 140.0 | 224.0 |
| 60 | 63.0 | 126.0 | 210.0 | 336.0 |

*(bps of NAV per year)*

Two structural points bound this and both reduce it:

1. **Overnight news cannot be exited at any crawl speed.** Companies publish adverse news after
   the close or before the open. At f_intraday = 0.20 the saving falls to 30 bps/yr.
2. **Broker-side ATR stops already bound the loss.** ADR-13 places protective stops at the broker
   at entry, which is why a monitor outage is survivable. The news trigger only earns in the
   subset where the thesis is broken but the stop has *not* yet fired — hence f_not_stopped = 0.5.

Also worth stating: **#39 (earnings blackout) removes the single largest class of adverse gaps by
not holding through the event at all.** That control is cheaper than any feed and does more for
this risk than a crawl does.

### 5.1 The decisive number

| Fleet cost | Break-even NAV |
|---|---|
| $3,000/mo self-hosted | **$6.9 M** |
| $8,000/mo self-hosted | **$18.3 M** |
| $195,000/mo via proxy pool | $446 M |

Against the capital ladder in `master-research-summary.md` §12:

| NAV | Saving/yr | Fleet at $36k/yr |
|---|---|---|
| $1,000 | $5 | **3,600 % of NAV** |
| $10,000 | $52 | **360 % of NAV** |
| $100,000 | $525 | 36 % of NAV |
| $1,000,000 | $5,250 | 4 % of NAV |

The programme's controlled-live stage runs at **$10,000**. At that capital the fleet costs 360 %
of NAV per year to capture 52 bps.

**And the 52 bps does not require the fleet.** Per `SPEC-P2N.13` §6, the Alpaca/Benzinga feed is
already inside the existing $129–228/mo stack. The trigger is worth ~52 bps/yr; the feed that
delivers it is **already paid for**. What the fleet adds is coverage of the tail *below* ADR-14's
liquidity screen — names the system is **not permitted to trade**. A signal about an untradeable
name has no value, which is what kills edge candidate #5 in §2.

---

## 6. Resolution

# CHOSEN END-STATE: (b) — event-driven exits, batch entries

With the correction that (b) is **substantially already ADR-13's design**, so the change is
small and local.

| | Decision |
|---|---|
| **Entries** | **Unchanged.** Once per session, 09:45–10:15 ET, from the frozen order list. ADR-14 stands. |
| **Exits** | **Unchanged in cadence** — intraday already permitted. **Add a news trigger** to the existing exit-hierarchy evaluation. |
| **ADR-13** | **No amendment required.** Its exit clause already permits this; a news-driven thesis invalidation is an exit-hierarchy trigger of HIGH urgency, which ADR-13 already allows to override the 3-session minimum hold. |
| **ADR-14** | **Minor amendment only** — state that an event may *suppress* a pending entry from the frozen order list, and may never *add* one. Suppression is free, valuable (§2 #4), and does not re-open the intraday entry path ADR-14 §70 closed. |
| **Crawl fleet #46–#52** | **Descope** per `SPEC-P2N.13` R-1 item 5. Re-justify at NAV > $7 M or on a measured coverage gap. |
| **Full event-driven entries (c)** | **Rejected.** ADR-13's four disqualifiers all still hold, §7. |

### 6.1 Why not (c)

ADR-13 rejected intraday on four independent grounds. Each is quoted and answered:

| ADR-13 argument | Still holds? |
|---|---|
| "A 60 %-fundamental score is incoherent at an intraday horizon — the dominant input would be constant across the entire holding period" | **Holds.** Unchanged by a faster feed. |
| "A 2.5×ATR distance on daily bars is a multi-day move. Intraday it would be hit rarely and meaninglessly" | **Holds.** |
| "A 6-month momentum feature has no intraday interpretation" | **Holds.** |
| "Intraday trading is legally and practically foreclosed at this capital level" (PDT, $1,000 ladder) | **Holds.** |
| Chain F: **63 %/yr cost drag at 1-day turnover** vs 4.20 % at 15 days | **Holds, and is decisive.** |

Choosing (c) would require replacing the scoring model, the stop rule, the momentum feature and
the capital plan simultaneously — to capture an entry-side latency advantage §3 shows is
structurally unavailable.

### 6.2 Amendment list for (b)

| Artifact | Change |
|---|---|
| `ADR-14` | Add: an event may suppress a pending entry; never add one. Version bump, re-freeze. |
| `ADR-13` | **None.** Record that its exit clause already authorises a news-triggered exit. |
| `SPEC-P0.3` | **None.** §565's ≤5 s exit budget already covers it. |
| #55 (P3.5) | Scope reduced to paths A, D and E. Path C (event-driven entry) is **out of scope**. |
| #54 | Reduced to the one-line ADR-14 suppression amendment. |
| #46–#52 | Descoped per P2N.13 R-1. |
| #57 | **Unchanged and now load-bearing** — a single-source exit still moves real money. |

---

## 7. Success criteria

Derived from the chosen edge (discipline and risk, not speed), reconciled with the frozen P5.2
gate (#27).

| Metric | Target | Source |
|---|---|---|
| Sharpe | > 1.0 | P5.2 gate, frozen |
| Max drawdown | < 15 % | P5.2 gate, frozen |
| OOS / IS | > 70 % | P5.2 gate, frozen |
| Realised median hold | 8–25 trading days | ADR-13 revisit band |
| Measured round-trip cost | ≤ 40 bps US | ADR-13 revisit trigger |
| Gross alpha per 15-day trade | **≥ 50 bps US, ≥ 180 bps India** | ADR-13 Chain F minimum edge |
| **Time-to-signal, exit path, p99** | **≤ 5 s** from event receipt | P0.3 §565 |
| **News-triggered exits that beat the ATR stop** | **≥ 15/yr**, measured | §5 — the falsification test |
| Fabrication-attack suppression | 100 % of the #57 corpus | #57 |

### 7.1 Falsification test

**The hypothesis dies if**, after 12 months of paper and shadow operation: fewer than 15
news-triggered exits per year beat what the ATR stop would have realised; **or** measured
round-trip cost exceeds 40 bps; **or** realised median hold falls outside 8–25 days; **or** gross
alpha per trade is below 50 bps US.

The first of those is the one that matters here: it is the direct measurement of whether the news
trigger — and therefore any of this latency work — earns its keep. It is computable from the audit
log from day one of shadow mode, and it must be reported monthly.

---

## 8. Options, in scope terms only

The edge hypothesis in §2 is discipline and risk control. **Options do not strengthen it and they
weaken #1 directly**: they add theta decay and post-event IV collapse as two new ways to lose on a
correct directional call, and ADR-05 §635 records that leverage is intrinsic, which collides with
Block A invariant 8.

They are a **separate ambition**, not a component of the edge. Full ADR is #58. This ADR's only
input to it: options should not be admitted before the §7 falsification test has run on cash
equities, because adding a leveraged instrument class to an unproven edge compounds two unknowns.

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Edge is discipline/risk/patience, not latency | §3 shows entry-side latency is structurally unavailable; §2 #1–#3 are not arbitrageable | Yes | **High** — it sets what the whole programme optimises for |
| 2 | End-state (b), and (b) is mostly already ADR-13 | ADR-13's exit clause already permits intraday exits; only the news trigger is missing | Yes | Low — smallest coherent change |
| 3 | Reject (c) | All four ADR-13 disqualifiers hold; Chain F's 63 %/yr drag is decisive | Treat as irreversible, per ADR-13 | High if overturned carelessly |
| 4 | Descope the crawl fleet | 52 bps/yr saving, break-even at $6.9 M NAV, ladder runs to $10,000; the feed that delivers the trigger is already owned | Yes | Medium — revisit above $7 M NAV |
| 5 | Events may suppress a pending entry, never add one | Suppression is valuable and does not re-open ADR-14 §70 | Yes | Low |
| 6 | Options deferred behind the falsification test | Adding leverage to an unproven edge compounds unknowns | Yes | Medium |

## ASSUMPTIONS

| # | Assumption | Why | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | E ≈ 25 thesis-breaking events/yr on a 20-slot book | No measured base rate exists | Count HIGH-tier triggers in shadow mode | §5 scales linearly; at E=60, 126 bps/yr |
| 2 | f_intraday ≈ 0.35 | Adverse corporate news skews to outside market hours | Measure publication timestamps vs session hours | At 0.20 → 30 bps/yr |
| 3 | f_not_already_stopped ≈ 0.50 | Broker-side ATR stop catches the larger moves first | Compare news timestamps to stop fills in shadow | At 0.25 → 26 bps/yr |
| 4 | Δ ≈ 3 % avoidable adverse move | Plausible for a HIGH-tier event; unmeasured | Event study on shadow-mode data | Linear; see table |
| 5 | Fleet cost $3–8k/mo self-hosted | From #41; unit prices unverified | #46 | Break-even NAV scales linearly |
| 6 | Vendor latency claims hold | `SPEC-P2N.13` §2 | Paid trial, both markets | §3 reorders; §6 unchanged |

## OPEN QUESTIONS

| # | Question | Answered by | Exact query | Blocks |
|---|---|---|---|---|
| E-1 | Measured base rate of HIGH-tier news events per holding | Shadow mode | Count exit-hierarchy HIGH triggers | §5 confidence |
| E-2 | Fraction of adverse news published inside session hours | Measurement | Publication timestamp vs exchange calendar | §5 |
| E-3 | Does the owner accept descoping #46–#52, given option (c) was chosen on #41? | **Owner** | §5.1 and P2N.13 §6 | #46–#52 |
| E-4 | Is the 15/yr falsification threshold acceptable? | Owner | §7.1 | Go-live gate #35 |
| E-5 | Does suppressing a pending entry need an ADR-14 version bump or a footnote? | #54 | ADR-14 §70 | #54 size |

## CONTRACTS EXPORTED

| Name | Kind | Schema / signature | Consumers |
|---|---|---|---|
| `EDGE-HYPOTHESIS` | decision | §2 — discipline/risk/patience, ranked, each with a measurement | #27, #35, #36, #53 descendants |
| `LATENCY-DECOMPOSITION` | table | §3, with evidence grade per arrow | #55, #56, #46 |
| `LATE-EXIT-COST-MODEL` | model | §5 formula + sensitivity + break-even NAV | #46, #54, #55 |
| `CADENCE-END-STATE` | decision | §6 — (b), with the §6.2 amendment list | #54, #55, #46–#52 |
| `EDGE-SUCCESS-CRITERIA` | table | §7 + the §7.1 falsification test | #27, #35, #36 |
| `OPTIONS-GATING` | decision | §8 — behind the falsification test | #58 |

---

# AMENDMENT v0.2 — E-4 ruled, and §7.1 corrected

Owner ruling requested 2026-10-16. Answering E-4 required correcting an error in v0.1.

## 11. The error in v0.1 §7.1

§7 set the falsification threshold at **"≥ 15 news-triggered exits per year that beat the ATR
stop"**. The base case in §5 produces:

```
qualifying events/yr = E × f_intraday × f_not_already_stopped
                     = 25 × 0.35 × 0.50
                     = 4.4
```

**The bar was 3.4× the base case.** The hypothesis would have been falsified even if the model were
exactly right. The 52.5 bps/yr figure and the 15/yr figure describe the same model and contradict
each other; 4.4 is the one consistent with §5.

**Worse than the arithmetic: a count test cannot work here at all.** Twelve months of shadow mode at
the base case yields **n ≈ 4**. Nothing is falsifiable at n = 4 — a year with 2 qualifying events and
a year with 8 are statistically indistinguishable, so the test would return noise and the programme
would act on it.

**The "≥ 15/yr" row in §7 and the first bullet of §7.1 are withdrawn.**

## 12. RULING on E-4 — test the parameters, not the count

The claim under test is narrow: *a news trigger on the exit path is worth ~52 bps of NAV/yr.* It
decomposes into four parameters, and **all four are measurable from historical data without running
the system, without shadow mode, and before #55 is built**:

| Parameter | What it is | How it is measured | Needs trading? |
|---|---|---|---|
| **E** | HIGH-tier news events/yr on a held-size book | count them on a simulated 20-slot book over history | no |
| **f_intraday** | fraction published inside session hours | publication timestamp vs exchange calendar | no |
| **f_not_stopped** | fraction where the ATR stop had not already fired | price path vs `entry − 2.5 × ATR(14)` at news time | no |
| **Δ** | avoidable adverse move | move from news time to the next session exit point, versus the stop fill | no |

So the test is an **event study**, not a 12-month wait. It can run now.

### 12.1 The kill condition, graded

Expressed as modelled annual value rather than a count, because that is the quantity the decision
actually turns on:

| Measured annual value | Ruling | What gets built |
|---|---|---|
| **< 10 bps/yr** | **Hypothesis falsified.** Noise against the 4.2 %/yr cost drag ADR-13 already budgets, and not worth the complexity or the injection surface | Abandon the intraday paths. #55 is cancelled |
| **10 – 25 bps/yr** | **Partially supported** | Build the cheap half only: #42 + #45 + #57 feeding the *existing* exit path. **Skip the #55 event loop** |
| **> 25 bps/yr** | **Supported** | Build #55 in full, scoped to paths A and E |

25 bps/yr is half of one US round trip (ADR-13 Chain F: ~25 bps) recovered every year, for a feed
already paid for. 10 bps/yr is under a quarter of a round trip — below the noise floor of the cost
model itself.

### 12.2 The carve-out that proceeds regardless

**Path D — suppressing a pending entry on adverse news — is exempt from E-4 and proceeds whatever
the event study finds.**

It needs no intraday infrastructure, no latency, and no event loop. Adverse news published overnight
is already in the nightly batch; the 09:45–10:15 placement window simply does not place that entry.
The #54 ruling already permits suppression, and the ADR-14 §70 objection does not apply —
suppressing a pending order is not re-deriving a signal.

This is worth stating plainly because it inverts the intuition the whole news programme started
from: **the single most valuable news feature in the system requires no real-time anything.** §2
rated "avoiding a bad entry" as high value, and it is reachable today at zero infrastructure cost.

### 12.3 Scope of E-4

E-4 governs **only** the news-trigger claim. The broader edge hypothesis of §2 — discipline, risk
control, patience — is already tested by the frozen P5.2 gate (Sharpe > 1.0, max DD < 15 %,
OOS > 70 % of IS) and by the ADR-13 revisit triggers (realised median hold outside 8–25 days,
measured round-trip cost > 40 bps US). Nothing here weakens those.

### 12.4 One honest caveat on the event study

It needs historical news with trustworthy timestamps. `SPEC-P0.2` M-5 records that **no vendor in
scope documents archive integrity**, which is the #62 problem.

But this study is **more robust to that problem than a backtest is**: it measures publication
timestamps and price moves, not as-reported fundamentals. A restated fundamental corrupts a
backtest; it does not change when an article was published or where price went afterwards. Dating
errors would still matter, so the study must report the fraction of items whose timestamp it could
not corroborate, and treat that fraction as its error bar.

### 12.5 Corrected §7 row and §7.1

| Metric | Target |
|---|---|
| ~~News-triggered exits that beat the ATR stop~~ | ~~≥ 15/yr~~ **— withdrawn** |
| **Modelled annual value of the news trigger, from the §12 event study** | **≥ 25 bps/yr to build #55 in full; ≥ 10 bps/yr to build the cheap half; below 10 bps/yr falsifies** |

**Corrected §7.1 falsification test.** The news-trigger hypothesis dies if the event study returns a
modelled annual value **below 10 bps of NAV**. The remaining three conditions of v0.1 §7.1 —
round-trip cost > 40 bps US, realised median hold outside 8–25 days, gross alpha per trade
< 50 bps US — stand unchanged, and are tests of the *edge*, not of the trigger.

## DECISIONS MADE — amendment

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 7 | Withdraw the 15/yr count threshold | Inconsistent with the §5 base case by 3.4×, and unfalsifiable at n ≈ 4 | Yes | Low — it was never run |
| 8 | Test the four parameters by event study instead | All four are measurable from history, so the test runs before #55 is built rather than after 12 months of shadow | Yes | Medium — a bad study kills or builds the wrong thing |
| 9 | Graded thresholds at 10 and 25 bps/yr | 25 bps is half a US round trip recovered yearly; 10 bps is below the noise floor of the cost model | Yes | Medium |
| 10 | Path D proceeds regardless of E-4 | It needs no intraday infrastructure at all — the nightly batch already holds the news | Yes | Low |

## OPEN QUESTIONS — amendment

| # | Question | Answered by | Blocks |
|---|---|---|---|
| E-5 | Who runs the §12 event study — a new issue, or part of #45? | Owner | the E-4 verdict, hence #55 |
| E-6 | What fraction of historical news timestamps can be corroborated? | the study itself | the study error bar |
