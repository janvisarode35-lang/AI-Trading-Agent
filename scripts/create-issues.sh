#!/usr/bin/env bash
# Create the build-plan issues for the AI Trading Agent.
#
# Creates 36 phase issues (one per prompt in docs/PROMPT-PACK.md) plus a tracker
# issue that links to all of them.
#
# Auth: uses $GITHUB_TOKEN if set, otherwise asks git's credential helper for the
# stored github.com credential (the same one `git push` uses). The token is never
# printed, echoed, or written to disk.
#
# Idempotency: this script is NOT idempotent. Running it twice creates duplicates.
# It aborts up front if the repo already has open issues.
#
# Usage:  bash scripts/create-issues.sh

set -euo pipefail

OWNER="janvisarode35-lang"
REPO="AI-Trading-Agent"
API="https://api.github.com/repos/${OWNER}/${REPO}/issues"

# Python is used only to build/parse JSON safely (no shell escaping bugs).
# Note: on Windows, `python3` on PATH is often the Microsoft Store stub, which
# exits without running anything. Probe each candidate rather than trusting PATH.
PY=""
for cand in python3 python py; do
  p="$(command -v "$cand" 2>/dev/null)" || continue
  if "$p" -c 'import json' >/dev/null 2>&1; then PY="$p"; break; fi
done
[ -n "$PY" ] || { echo "no working python found" >&2; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------- auth --------
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [ -z "$TOKEN" ]; then
  TOKEN="$(printf 'protocol=https\nhost=github.com\n\n' \
           | git credential fill 2>/dev/null \
           | sed -n 's/^password=//p')"
fi
if [ -z "$TOKEN" ]; then
  echo "No credential found. Set GITHUB_TOKEN and re-run." >&2
  exit 1
fi

# ------------------------------------------------------------- preflight ------
existing="$(curl -sS -H "Authorization: Bearer ${TOKEN}" \
                 -H "Accept: application/vnd.github+json" \
                 "${API}?state=open&per_page=1" \
            | "$PY" -c 'import json,sys; print(len(json.load(sys.stdin)))')"
if [ "$existing" != "0" ]; then
  echo "Repo already has open issues. Aborting to avoid duplicates." >&2
  exit 1
fi

TRACK="${WORK}/track.md"
: > "$TRACK"
LAST_NUM=""

stage() { printf '\n### %s\n' "$1" >> "$TRACK"; }

# mkissue <title> <labels-csv> <body-file>
mkissue() {
  local title="$1" labels="$2" file="$3" code num
  "$PY" -c 'import json,sys
print(json.dumps({"title": sys.argv[1],
                  "labels": sys.argv[2].split(","),
                  "body": open(sys.argv[3], encoding="utf-8").read()}))' \
      "$title" "$labels" "$file" > "${WORK}/payload.json"

  code="$(curl -sS -o "${WORK}/resp.json" -w '%{http_code}' -X POST \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "$API" --data-binary @"${WORK}/payload.json")"

  if [ "$code" != "201" ]; then
    echo "FAILED (${code}): ${title}" >&2
    "$PY" -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); print(d.get("message"), d.get("errors",""))' "${WORK}/resp.json" >&2
    exit 1
  fi

  num="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["number"])' "${WORK}/resp.json")"
  LAST_NUM="$num"
  printf -- '- [ ] #%s %s\n' "$num" "$title" >> "$TRACK"
  echo "  #${num}  ${title}"
  sleep 1   # ponytail: fixed 1s pace to stay under the secondary rate limit; swap for 403-aware backoff if this ever runs against a large batch
}

# Shared footer appended to every phase body.
footer() {
  cat <<'FTR'

---

### How to run this phase

1. Open a **fresh** conversation.
2. Paste, in order: **Block A** (Constitution) → **Block B** (Output Contract) → **Block C** (Clarifier Rule) → this phase's prompt from `docs/PROMPT-PACK.md`.
3. Paste the **full text** of every spec listed under *Depends on* — links are not enough, the model needs the content.
4. Save the output to the deliverable path below.
5. If this phase produced code, run template **X2 — Code Review** in a *separate* conversation before merging.
FTR
}

echo "Creating issues in ${OWNER}/${REPO} ..."

# ============================================================== STAGE 0 =======
stage "Stage 0 — DECIDE"

{ cat <<'EOF'
Close every open question in the research summary so nothing downstream re-opens them.

**Depends on:** nothing — this is the first phase.
**Deliverable:** `docs/specs/SPEC-P0.1-DECISIONS.md`
**Prompt:** `docs/PROMPT-PACK.md` → *P0.1 — Decision Closure*

### What it produces

15 Architecture Decision Records, each with context, at least 3 options costed, the decision, consequences, and what would make us revisit it.

### The ones that matter most

- **Q13 Holding period** (intraday / swing / position). This single answer cascades into data frequency, storage volume, cost model, PDT exposure, tax treatment, slippage assumptions, and whether the gated LLM tier is affordable at all. The prompt requires those chains to be written out explicitly.
- **Q14 Universe size and rebalance cadence** — drives ingest throughput and the entire cost model.
- **Q11 Single-market-first vs dual-market** — decides whether every downstream spec carries two calendars, two brokers, and an FX layer from day one.

### Acceptance

- [ ] All 15 ADRs written, none left as "TBD"
- [ ] Q13 second-order effect chains stated, not just the decision
- [ ] A one-page "decisions that constrain everything else" summary
- [ ] Every ADR names a decision owner and a date
EOF
footer; } > "${WORK}/b.md"
mkissue "P0.1 — Decision Closure" "stage-0,decision" "${WORK}/b.md"

{ cat <<'EOF'
Produce a fact sheet per external provider precise enough to write client code from, plus a scored primary/backup selection.

**Depends on:** #1 (holding period determines which data granularity we are even shopping for)
**Deliverable:** `docs/specs/SPEC-P0.2-PROVIDERS.md`
**Prompt:** `docs/PROMPT-PACK.md` → *P0.2 — Provider & Broker Due Diligence*

### Scope

Alpaca (trading + data), Interactive Brokers, Zerodha Kite, Upstox, Polygon.io, Finnhub, Financial Modeling Prep, SEC EDGAR, FRED, a news API, DeepSeek, OpenAI.

### Detail level required

Auth and token lifetime (including Zerodha's daily login), every rate limit with its 429 behaviour, WebSocket reconnect and backfill semantics, adjusted vs unadjusted data, corporate-action handling, survivorship bias, tick and lot size, idempotency key support and its charset limits, partial-fill semantics, the full rejection code list, sandbox-vs-prod differences, cost, and ToS restrictions on automated access.

### Acceptance

- [ ] Every provider has a completed fact sheet
- [ ] Weighted decision matrix yielding a primary and a backup per capability
- [ ] A "what breaks if this provider dies at 09:31" note per provider
- [ ] **An explicit list of every doc URL that could not be verified.** No guessed rate limits — a guessed limit is worse than a missing one.
EOF
footer; } > "${WORK}/b.md"
mkissue "P0.2 — Provider and Broker Due Diligence" "stage-0,decision,research" "${WORK}/b.md"

{ cat <<'EOF'
A defensible monthly cost model and a hard latency budget per pipeline stage.

**Depends on:** #1, #2
**Deliverable:** `docs/specs/SPEC-P0.3-BUDGET.md`
**Prompt:** `docs/PROMPT-PACK.md` → *P0.3 — Cost, Capacity & Latency Budget*

### What it computes

- Data volume in GB before and after TimescaleDB compression, at 1m / 5m / daily, over 10 years plus live
- Ingest throughput in the worst minute of the day (the open), in msg/sec and rows/sec, and the resulting CPU and write IOPS
- LLM spend at gate widths of 5, 10, 20, 50 — and therefore **which gate width the $200-500/month ceiling actually implies**
- VM sizing with the specific bottleneck named
- Cost of one full 10-year backtest and per walk-forward window

### Latency budget

End-to-end from "bar closes" to "order acknowledged", decomposed per stage, each with a hard budget and a stated drop behaviour when blown. Stated separately for the daily-rebalance path and the intraday-exit path.

### Acceptance

- [ ] Sensitivity table: cost vs universe size vs gate width vs bar frequency
- [ ] The gate width from this phase is the number P4.2 implements
- [ ] Every stage of the latency budget has a defined behaviour when over budget
EOF
footer; } > "${WORK}/b.md"
mkissue "P0.3 — Cost, Capacity and Latency Budget" "stage-0,decision" "${WORK}/b.md"

# ============================================================== STAGE 1 =======
stage "Stage 1 — SPECIFY"

{ cat <<'EOF'
The complete typed vocabulary of the system. Everything downstream imports from here.

**Depends on:** #1, #2, #3
**Deliverable:** `docs/specs/SPEC-P1.1-DOMAIN.md` + `src/domain/models.py`
**Prompt:** `docs/PROMPT-PACK.md` → *P1.1 — Domain Model & Type System*

### The traps this phase exists to close

- **Money and Price are `Decimal`, never `float`.** Exact quantisation per market (US sub-penny rules, NSE tick size), rounding mode, and proof the arithmetic is closed under those rules.
- **Every timestamp tz-aware UTC at rest.** Trading calendars with half-days, holidays, pre/post market, DST transitions, and the India settlement calendar.
- **Symbol identity survives ticker changes.** A stable internal `instrument_id`, plus mappings for ISIN/CUSIP/FIGI, dual listings, ADRs, mergers, delistings.
- **Lot-level position accounting** with an explicit cost-basis method — this is what makes wash-sale (US) and STCG/LTCG (India) reporting possible later.
- **Every state machine gets a transition table** with the illegal transitions listed and what raises.

### Acceptance

- [ ] Every entity is a Pydantic v2 model with validators, not prose
- [ ] Every field carries unit, timezone, nullability, and valid range
- [ ] Glossary pinning each ambiguous term (exposure, drawdown, confidence, score, signal) to exactly one meaning
- [ ] `OrderState`, `KillSwitchState`, `PositionState` transition tables complete
EOF
footer; } > "${WORK}/b.md"
mkissue "P1.1 — Domain Model and Type System" "stage-1,spec" "${WORK}/b.md"

{ cat <<'EOF'
The full physical schema. DDL that runs.

**Depends on:** #4
**Deliverable:** `docs/specs/SPEC-P1.2-STORAGE.md` + migration 0001
**Prompt:** `docs/PROMPT-PACK.md` → *P1.2 — Storage Schema*

### The one that must not be got wrong

**Bitemporality is mandatory for anything a backtest reads.** Every such table carries `valid_time` and `knowledge_time` (as-reported vs as-restated fundamentals especially), and the spec must show the query pattern that makes look-ahead bias *structurally impossible* rather than a matter of discipline. Retrofitting this later is a rewrite.

### Also required

- Hypertable chunk intervals justified by the actual query pattern, plus compression and retention policies
- Check constraints encoding domain invariants, not just types — no negative NAV, `fill_qty <= order_qty`, unique `client_order_id` per account
- `audit_log` made immutable **at the database level**: revoked UPDATE/DELETE grants, trigger, hash-chain column. Show the DDL and the grants.
- Every index justified by a named query, with the query text included
- Backup and PITR plan with the RPO it actually achieves

### Acceptance

- [ ] Complete DDL that runs against PostgreSQL 16 + TimescaleDB
- [ ] Row count and on-disk size estimate per table at 1 year and 10 years
- [ ] Alembic migration 0001, plus the special rule for migrations touching audit tables
EOF
footer; } > "${WORK}/b.md"
mkissue "P1.2 — Storage Schema" "stage-1,spec" "${WORK}/b.md"

{ cat <<'EOF'
A versioned, signed, human-auditable configuration system, and the PolicyGate rule language the risk engine reads.

**Depends on:** #4, #5
**Deliverable:** `docs/specs/SPEC-P1.3-CONFIG.md` + a complete `policy.yaml` + loader/validator
**Prompt:** `docs/PROMPT-PACK.md` → *P1.3 — Configuration & Policy DSL*

### What it defines

Every risk limit expressed as a rule with a **stable rule ID** (`EXP-001`, `LOSS-002`, ...), each carrying: scope, mode (`enforce`/`monitor`), severity, threshold, comparison, measurement window, the exact data inputs it needs, its action (`ALLOW`/`DENY`/`MODIFY`/`KILL`), and **its fail-closed behaviour when its inputs are unavailable**.

### Non-obvious requirements

- Precedence when `MODIFY` and `DENY` both fire, and a deterministic total ordering of rule evaluation
- Two-person rule for limit changes; how a live change does or deliberately does not reach in-flight decisions
- **No code path may read a raw environment variable for a risk number.** State the enforcement: single loader, lint rule, and a test that fails if violated.
- Secrets never live in this file — define the Vault reference syntax

### Acceptance

- [ ] `policy.yaml` contains every limit from the Constitution, each with an ID
- [ ] Effective-config dump (post-layering) written to the audit log
- [ ] The test that fails when a risk number is read from `os.environ`
EOF
footer; } > "${WORK}/b.md"
mkissue "P1.3 — Configuration and Policy DSL" "stage-1,spec" "${WORK}/b.md"

{ cat <<'EOF'
An append-only, tamper-evident, replayable event log that is the ONLY source of truth for what the system did and why.

**Depends on:** #4, #5, #6
**Deliverable:** `docs/specs/SPEC-P1.4-AUDIT.md` + event models + hash-chain verifier
**Prompt:** `docs/PROMPT-PACK.md` → *P1.4 — Audit Trail & Event Model*

> **Ordering constraint: this must be frozen before any component that emits events.** Retrofitting an append-only hash chain across an existing system is a rewrite.

### Reproducibility is the hard requirement

A decision must be re-derivable **bit-for-bit months later**. That means capturing: input data snapshot refs, model version + hash, config version + hash, code git SHA, random seeds, library versions, and the LLM prompt + response + sampling params.

### Also required

- Full event taxonomy — every event type, schema, producer, trigger
- Every event carries `event_id` (UUIDv7), `causation_id`, `correlation_id`/`run_id`, `occurred_at`, `recorded_at`, actor, schema version, input hash
- **Write-before-act protocol**, plus what happens when the process dies between the audit write and the side effect, and the idempotent recovery on restart
- Canonical serialisation rules for the hash chain (order matters or verification is meaningless)

### Acceptance

- [ ] A runnable self-check proving a mutated row fails verification
- [ ] Verification runtime measured at 10M events
- [ ] The replay tool: given a `run_id`, re-derive the decision and diff it against the recorded one
EOF
footer; } > "${WORK}/b.md"
mkissue "P1.4 — Audit Trail and Event Model" "stage-1,spec,critical" "${WORK}/b.md"


# ============================================================== STAGE 2 =======
stage "Stage 2 — CORE (no LLM anywhere)"

{ cat <<'EOF'
A provider-agnostic ingestion layer for OHLCV, quotes, fundamentals, corporate actions, news metadata, and economic series, across US and India.

**Depends on:** #2, #4, #5, #7
**Deliverable:** `docs/specs/SPEC-P2.1-INGEST.md` + `src/data/` + tests
**Prompt:** `docs/PROMPT-PACK.md` → *P2.1 — Data Ingestion*

### The rules that matter

- **On provider error, record the failure.** Never substitute, never carry forward, never interpolate. Define exactly what downstream sees when data is absent.
- Store raw, adjust at read time — and say why.
- A missing bar on a half-day is not a gap. Gap detection is defined against the exchange calendar, not the clock.
- On reconnect, backfill the disconnect window before resuming, and **prove no bar was silently lost**.
- When two providers disagree on the same bar: state the reconciliation rule, the tolerance, and which one wins.

### Acceptance

- [ ] Recorded-fixture replay test per adapter
- [ ] Gap-detection test across a half-day and a DST boundary
- [ ] Two-provider disagreement test
- [ ] Redis cache keys, TTLs, and a cache-stampede guard
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.1 — Data Ingestion" "stage-2,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
The gate that decides whether the system is allowed to trade today. Fails closed.

**Depends on:** #8
**Deliverable:** `docs/specs/SPEC-P2.2-VALIDATION.md` + implementation + property tests
**Prompt:** `docs/PROMPT-PACK.md` → *P2.2 — Data Validation & Quality Gate*

### Seven layers, each with an exact rule and threshold

1. Schema — strict, no type coercion
2. Structural — OHLC ordering, non-negative volume, bar aligned to the grid, nothing outside session hours
3. Temporal — monotonic, no future timestamps, freshness with clock-skew tolerance
4. Statistical — price jump vs rolling volatility, volume spike, flatline, stale quote
5. Cross-source — agreement tolerance, quorum rule at three sources
6. **Corporate-action awareness** — a 50% overnight drop is a split, not an anomaly. Specify the lookup that distinguishes them, and the behaviour when the corporate-action feed is late.
7. Coverage — the minimum fraction of the universe with valid data below which **the whole run aborts**

### Acceptance

- [ ] Per record: quality score + `ACCEPT`/`QUARANTINE`/`REJECT` + the rule ID that fired
- [ ] Quarantined data is stored, never silently dropped
- [ ] Daily data-quality report, alert thresholds, and a logged manual-override procedure
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.2 — Data Validation and Quality Gate" "stage-2,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
Take the full listed universe down to 50-200 candidates, deterministically. No LLM, no ML.

**Depends on:** #9
**Deliverable:** `docs/specs/SPEC-P2.3-SCANNER.md` + implementation + golden-file test
**Prompt:** `docs/PROMPT-PACK.md` → *P2.3 — Universe & Scanner (Tier 1)*

### Every filter defined to the last detail

- **market cap** — which share class, shares-outstanding vintage, which price, FX for India
- **ADDV** — window, currency, median or mean, handling of halts and low-volume days
- **price floor** — which price, adjusted or raw, at which timestamp
- **momentum** — exact lookback, calendar or trading days, total or price return, skip-a-month or not, and why
- **value** — P/B using which book-value vintage, sector median over which set, negative book value
- **volatility** — estimator (close-to-close / Parkinson / Garman-Klass), window, annualisation, benchmark

### Also

- **Point-in-time universe**: as of a past date, exclude anything not yet listed and include everything since delisted
- Exclusions: ETFs, ADRs, SPACs, REITs, minimum listing age, halted names, India ASM/GSM surveillance lists
- Filter **order** and short-circuiting — order changes both cost and the result set
- Determinism including the tie-break rule

### Acceptance

- [ ] Golden-file test against a frozen historical date
- [ ] Diagnostic mode reporting how many symbols each filter removed and why
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.3 — Universe and Scanner (Tier 1)" "stage-2,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
Every feature used by any model, defined once, computed identically in backtest and live.

**Depends on:** #10
**Deliverable:** `docs/specs/SPEC-P2.4-FEATURES.md` + implementation + parity test
**Prompt:** `docs/PROMPT-PACK.md` → *P2.4 — Feature Engineering*

> Training/serving skew is the enemy here. **One implementation, used by both paths**, with a test that fails if they diverge.

### Per feature

Name, formula, inputs, lookback, units, expected range, NaN treatment, insufficient-history treatment, winsorisation, normalisation, and **its point-in-time availability lag** — when was this value actually knowable.

### Families

- **Fundamental** — reporting-lag rule per market (US 10-Q, India quarterly), as-reported vs restated, TTM construction, fiscal-year alignment across companies, currency
- **Sector normalisation** — z-score at which GICS level, minimum member count, what happens below it, outlier clipping, cross-sectional vs time-series choice justified
- **Technical** — ATR(14) with **Wilder smoothing, not the naive mean**, VWAP (session or rolling — say which), ADX, volume ratios, SMA set; seeding rule for the first N bars; behaviour across gaps and halts
- **Market/regime** — index returns, breadth, VIX / India VIX, term spread, credit spread

### Acceptance

- [ ] Leakage audit per feature, with the at-risk ones named and guarded
- [ ] Backtest-vs-live parity test
- [ ] Feature-drift monitor defined
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.4 — Feature Engineering" "stage-2,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
Turn features into scores, with models honest about their uncertainty.

**Depends on:** #11
**Deliverable:** `docs/specs/SPEC-P2.5-SCORING.md` + training pipeline + inference
**Prompt:** `docs/PROMPT-PACK.md` → *P2.5 — Fundamental & Technical Scoring Agents*

### Owns two contradictions in the research summary

1. **The weights sum to 90%, not 100%** (60% fundamental + 20% technical + 10% sentiment). Resolve it: state the full weighting, the missing 10%, the normalisation of each component to a common scale, and what happens when a component is unavailable.
2. **Sentiment agent LLM status** — §5 says `LLM? No`, §9 assigns LLMs to deep sentiment. Pick one and state it.

### The most important paragraph in the spec

**The target definition.** What exactly is being predicted, over what horizon, in what units, relative to what benchmark, with what labelling of the ambiguous middle — justified against the holding period decided in #1.

### Also

- Purged + embargoed cross-validation, embargo length derived from the label horizon. Explain why naive k-fold is invalid.
- Multiple-testing inflation control across the hyperparameter search, with the trial count recorded honestly
- Calibration so that a score of 80 means the same thing next year
- Any feature that cannot be explained economically gets dropped
- The no-model fallback: a pure-rules path when a model is unavailable or stale

### Acceptance

- [ ] Model registry entry with training window, data hash, metrics, approver, **and an expiry date**
- [ ] A test proving a stale or unregistered model cannot serve predictions
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.5 — Fundamental and Technical Scoring Agents" "stage-2,spec,code,ml" "${WORK}/b.md"

{ cat <<'EOF'
A small number of clearly defined market regimes and the exact way each changes system behaviour.

**Depends on:** #11, #12
**Deliverable:** `docs/specs/SPEC-P2.6-REGIME.md` + implementation + historical review
**Prompt:** `docs/PROMPT-PACK.md` → *P2.6 — Regime Detection*

### Requirements

- 3-5 regimes, each defined by **measurable conditions, not vibes**
- HMM + deterministic rules: observation vector, state count, fitting window, refit cadence
- **Label switching is a real failure mode** — specify the procedure that keeps state identities stable across refits
- **Hysteresis**: minimum dwell time and confirmation window so the regime does not flip daily, with its measured effect on turnover
- Per-market vs global regime, and how a conflict resolves
- **The behavioural consequence table**: per regime — gross exposure cap, max position size, minimum score threshold, gate width, stop multiplier, whether new entries are allowed at all. Every number stated.
- When the regime model is unavailable, default to the most conservative regime

### Acceptance

- [ ] Historical labelling review across 2008, 2015, 2018, 2020, 2022 with the labels it actually produces
- [ ] Regime transitions emit audit events and fire an alert
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.6 — Regime Detection" "stage-2,spec,code,ml" "${WORK}/b.md"

{ cat <<'EOF'
The component that emits BUY / HOLD / SELL / NO_TRADE. Deterministic synthesis of all signals.

**Depends on:** #12, #13
**Deliverable:** `docs/specs/SPEC-P2.7-DECISION.md` + implementation + truth-table test
**Prompt:** `docs/PROMPT-PACK.md` → *P2.7 — Decision Engine*

### Non-negotiable

- **The system must produce a valid decision with zero LLM input.** State the maximum share of the final score the LLM path can influence, and what the decision looks like when that path is skipped or failed.
- **`NO_TRADE` is the default.** Any path that fails to produce a confident decision returns `NO_TRADE`, not `HOLD`.
- If the confidence score is not calibrated, say so and **forbid using it for sizing**.

### Also

- The exact scoring formula with every weight, and the regime adjustment applied to it
- Thresholds for BUY / SELL / HOLD and a deliberately wide `NO_TRADE` band, plus hysteresis preventing flip-flop between adjacent runs and a minimum holding period before a reversal
- **Conflict truth table**: quant says BUY, sentiment says SELL, regime is risk-off — every combination enumerated with its output. No implicit precedence.
- Every decision emits machine-readable reasons: rule IDs and input values sufficient to reconstruct it without the model

### Acceptance

- [ ] Truth-table test covering every enumerated combination
- [ ] Idempotency: the same run over the same inputs emits no duplicate decisions
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.7 — Decision Engine" "stage-2,spec,code,critical" "${WORK}/b.md"

{ cat <<'EOF'
Turn approved decisions into target quantities that respect every constraint simultaneously.

**Depends on:** #14
**Deliverable:** `docs/specs/SPEC-P2.8-SIZING.md` + implementation + tests
**Prompt:** `docs/PROMPT-PACK.md` → *P2.8 — Position Sizing & Portfolio Construction*

### The formula, fully expanded

`risk_per_trade × NAV / (volatility × price)`, capped by max position pct, by liquidity, by remaining sector headroom, by remaining cash. **State the order of the caps**, the rounding to lot/tick, and the minimum viable size below which the trade is **dropped entirely rather than sent tiny**.

### The hard part

Portfolio-level construction when N candidates each pass individually but collectively breach sector or gross limits. Give the allocation algorithm, its objective, and its tie-break. **Prefer a deterministic greedy rule over an optimiser** unless the optimiser can be justified.

### Also

- A stock with insufficient volatility history is excluded, not defaulted
- Existing positions: drift tolerance band, minimum trade size that justifies costs, and what happens to a position that has *grown* past its cap
- Cash: reserve buffer, T+1 settlement both markets, unsettled funds, and the rule preventing a good-faith violation
- FX rate source and timing for the India sleeve

### Acceptance

- [ ] Test: all candidates want the same sector
- [ ] Output is a target portfolio plus a diff against current, as order intents carrying the constraint values that shaped them
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.8 — Position Sizing and Portfolio Construction" "stage-2,spec,code,critical" "${WORK}/b.md"

{ cat <<'EOF'
The component that says no. **Assume the AI upstream is compromised.**

**Depends on:** #6, #7, #15
**Deliverable:** `docs/specs/SPEC-P2.9-RISK-ENGINE.md` + implementation + full test suite
**Prompt:** `docs/PROMPT-PACK.md` → *P2.9 — Risk Engine*

> **Blocking constraint: this must be FROZEN and tested before any phase produces code that can reach a broker.**

### Five properties, each addressed explicitly

1. **Zero AI** — no model, no LLM, no learned threshold, no randomness anywhere
2. **Fail-closed** — any exception, missing input, stale input, or unreachable dependency returns DENY. **Prove no code path returns ALLOW on an error.**
3. **Total** — every intent gets a verdict; no path returns `None` or falls through
4. **Pure** — a pure function of (intent, portfolio state, market state, policy). No I/O inside the evaluator; state is snapshotted first.
5. **Unbypassable** — name the architectural mechanism (single choke point, signed verdict token) **and the test that fails if a new call path appears**

### Per rule

Exact numerator and denominator, price used, timestamp used, before or after the hypothetical fill, whether pending orders count toward exposure, window with timezone and boundary handling, the `MODIFY` reduced-quantity formula, and behaviour when its input is unavailable.

### Also

- Precedence lattice `KILL > DENY > MODIFY > ALLOW`, proven well-defined
- **Concurrency**: two intents evaluated in parallel must not both consume the same headroom. Specify the serialisation and its throughput ceiling.
- Every evaluation logged — **including the ALLOWs**
- Monitor mode so a rule can run in shadow before enforcement

### Acceptance

- [ ] Exhaustive boundary tests: at, just under, just over **every** threshold
- [ ] Property-based tests asserting fail-closed under arbitrary malformed input
- [ ] Fuzz suite
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.9 — Risk Engine (deterministic)" "stage-2,spec,code,critical" "${WORK}/b.md"

{ cat <<'EOF'
The last line of defence. **It must work when everything else is broken.**

**Depends on:** #7, #16
**Deliverable:** `docs/specs/SPEC-P2.10-KILLSWITCH.md` + implementation + chaos test
**Prompt:** `docs/PROMPT-PACK.md` → *P2.10 — Kill Switch*

> **Blocking constraint: FROZEN and tested before any code can reach a broker.**

### Independence is the whole point

It must trip when the main process is hung, looping, or out of memory. Name the architecture that achieves that — separate process, supervisor, watchdog, broker-level control — and what it depends on.

### State

`ARMED` / `TRIPPED` / `RESETTING` / `DISABLED`, with a transition table, and **where the state lives so it survives a process restart and a database outage**. Name the source of truth and the tie-break when two stores disagree — the safe answer wins.

### Every trigger, measured precisely

Drawdown > 10% (peak measured how, since when, marked at what price), daily loss > 2%, weekly loss > 5%, volatility > 3σ (of what, over what window), API failure > 5 consecutive retries (per provider or global), agent loop > 10 iterations (counted how), data-quality breach, unexpected position discovered, broker reconciliation mismatch, NAV computation failure.

### Also

- Manual trigger on a channel **completely separate from the AI path**, reachable when the app is down
- Trip sequence, ordered, with what happens if a step fails mid-way (what if cancel fails?)
- **Re-enablement is human-only, two-person, with a written cause and a cooling period. No automatic reset, ever.**
- **On boot the system assumes TRIPPED** until it positively verifies otherwise, including reconciling positions against the broker
- The production self-test: how we prove it still works, on what cadence, without disrupting trading

### Acceptance

- [ ] Chaos test that trips it **while orders are in flight** and asserts the end state is safe
EOF
footer; } > "${WORK}/b.md"
mkissue "P2.10 — Kill Switch" "stage-2,spec,code,critical" "${WORK}/b.md"

# ============================================================== STAGE 3 =======
stage "Stage 3 — EXECUTE"

{ cat <<'EOF'
One interface, two very different brokers, no leaking abstractions.

**Depends on:** #2, #4, #16, #17
**Deliverable:** `docs/specs/SPEC-P3.1-BROKER.md` + adapters + simulator + conformance suite
**Prompt:** `docs/PROMPT-PACK.md` → *P3.1 — Broker Abstraction*

### Requirements

- Full typed protocol with **error unions, not exceptions for control flow**
- **Capability descriptor** — brokers differ on fractional shares, order types, TIF, amend support, GTC lifetime. The caller must check. **Never silently emulate a missing capability.**
- The Zerodha daily-token problem: state exactly what happens when the token is invalid at 09:14. (Answer: it does not trade, and it pages a human.)
- **The ambiguous case is the dangerous one** — a timeout on submit. Never blind-retry; always reconcile by `client_order_id` first.
- Client-side rate limiter tuned *below* the documented limit, with a queue and a drop policy for stale intents
- Paper vs live: one code path, one flag, and a test that a live credential cannot load in paper mode or vice versa
- A **simulated adapter** implementing the same protocol with realistic partial fills and rejections, used by tests and the backtester

### Acceptance

- [ ] A conformance suite every adapter must pass, including the simulator
EOF
footer; } > "${WORK}/b.md"
mkissue "P3.1 — Broker Abstraction" "stage-3,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
Turn approved intents into fills. Exactly-once as the goal, at-least-once with reconciliation as the reality.

**Depends on:** #16, #17, #18
**Deliverable:** `docs/specs/SPEC-P3.2-EXECUTION.md` + implementation + crash tests
**Prompt:** `docs/PROMPT-PACK.md` → *P3.2 — Execution Engine*

### The state machine must include `UNKNOWN`

`NEW`, `VALIDATED`, `SENT`, `ACKED`, `PARTIALLY_FILLED`, `FILLED`, `CANCEL_PENDING`, `CANCELLED`, `REJECTED`, `EXPIRED`, **`UNKNOWN`** — plus the procedure that resolves `UNKNOWN`.

### Pre-send validation

Risk verdict token present and valid, kill switch armed and not tripped, market open per calendar, symbol tradable, price sane vs last trade, quantity within broker limits, duplicate check.

### The details that bite

- Limit price derivation, max allowed slippage from the reference, and the repricing ladder: how many times, how far, what delay, **hard give-up rule**
- **Partial fills** — when to leave the remainder working, and **how a partial fill affects the stop that was sized for the full position**
- Working orders across a session boundary or a halt
- Emergency exit is the *only* place market orders are permitted, with its own guard rails and its own audit event type
- **Reconciliation** on startup and on a timer, tolerance zero, action on mismatch is **halt and page a human — never auto-correct by trading**

### Acceptance

- [ ] Persisted intent journal written **before** send; recovery resolves in-flight intents by *querying* the broker, never by re-sending
- [ ] Test that kills the process between journal write and send, asserting no duplicate order
EOF
footer; } > "${WORK}/b.md"
mkissue "P3.2 — Execution Engine" "stage-3,spec,code,critical" "${WORK}/b.md"

{ cat <<'EOF'
Know the true state of the portfolio at all times and detect deterioration early.

**Depends on:** #19
**Deliverable:** `docs/specs/SPEC-P3.3-MONITOR.md` + implementation + tests
**Prompt:** `docs/PROMPT-PACK.md` → *P3.3 — Position Monitor*

### Covers

- The loop: cadence per check (per tick / per minute / per day), what happens when a cycle overruns, how backpressure is handled
- Per position: mark price source and fallback, unrealised P&L, holding period, distance to stop, current vs entry ATR, upcoming earnings, pending corporate actions, liquidity deterioration
- Portfolio: NAV, gross/net exposure, sector exposure, concentration, daily P&L, drawdown from peak, correlation clustering
- **Trailing stop ratchet** — moves up, never down. Exact update condition and cadence. Held locally or resting at the broker? **What happens if the connection drops while a local stop is armed?**
- **Thesis invalidation is evaluated here, deterministically.** An LLM never evaluates its own invalidation conditions.
- Anomaly detection: a position we did not open, quantity mismatch, price feed disagreeing with the broker, an impossible NAV move — each with threshold and escalation
- **Dead-man switch**: a check that the alerting itself is still alive

### Acceptance

- [ ] Trailing-stop ratchet test
- [ ] Disconnected-local-stop test
EOF
footer; } > "${WORK}/b.md"
mkissue "P3.3 — Position Monitor" "stage-3,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
The exit hierarchy, made precise and deterministic.

**Depends on:** #19, #20
**Deliverable:** `docs/specs/SPEC-P3.4-EXIT.md` + implementation + tests
**Prompt:** `docs/PROMPT-PACK.md` → *P3.4 — Exit Engine*

### Four tiers, each with trigger, cadence, order type, size, priority

- **EMERGENCY** (sell all) — stop hit, risk breach, kill switch. **Define what "stop hit" means**: trade through, close through, or quote through the level. Handle gaps below the stop, halts, and limit-down.
- **HIGH** (sell all) — thesis invalidated, earnings miss beyond threshold, fraud or delisting, liquidity collapse
- **MEDIUM** (partial) — valuation extended, technical breakdown, time stop, score decay
- **LOW** (partial or hold) — rebalancing, opportunity cost, tax-aware deferral

### Also

- Conflict resolution when two tiers fire at once — **the most urgent wins, with no averaging**
- Partial-exit sizing, and the minimum residual below which the position is closed entirely rather than left as a stub
- **Re-entry lockout** after an exit, per reason, so the system does not immediately buy back
- Wash-sale (US) and STCG/LTCG (India) consequences **surfaced in the audit record — never overriding risk for tax**

### Acceptance

- [ ] Tests: gap-through-stop, halted-at-stop, simultaneous multi-tier triggers
EOF
footer; } > "${WORK}/b.md"
mkissue "P3.4 — Exit Engine" "stage-3,spec,code,critical" "${WORK}/b.md"

# ============================================================== STAGE 4 =======
stage "Stage 4 — INTELLIGENCE (gated LLM)"

{ cat <<'EOF'
**Assume every news article is written by an attacker who knows your system prompt.**

**Depends on:** #7, #14
**Deliverable:** `docs/specs/SPEC-P4.1-SANITISER.md` + implementation + adversarial corpus
**Prompt:** `docs/PROMPT-PACK.md` → *P4.1 — Untrusted Content Pipeline*

### Threat model, each vector with a concrete example payload

News body, headline, ticker field, company name, SEC filing text, social posts, tool responses, and **previously stored records** (memory poisoning).

### The structural defence — this is the one that matters

External text is **never concatenated into a prompt**. It is passed only inside a delimited, typed data envelope with an explicit origin tag, and the system prompt states that envelope content is data and may contain hostile text. **Show the exact envelope format.** Pattern detection is defence in depth, never the primary control.

### Also

- Extraction: HTML stripping, script/comment removal, invisible characters (zero-width, bidi overrides, homoglyphs), unicode normalisation form and why, length caps
- Provenance per fragment: source, url, publisher, `retrieved_at`, trust tier — **untrusted tiers cannot influence a decision beyond a capped weight**
- Deduplication of syndicated news so one story does not look like twenty confirmations
- **Content sanitised today is still untrusted forever** — state the re-validation rule on read

### Acceptance

- [ ] Adversarial fixture corpus including finance-specific attacks: fake press release, spoofed filing, coordinated social pump
- [ ] A test asserting **every** payload fails to change the pipeline output
EOF
footer; } > "${WORK}/b.md"
mkissue "P4.1 — Untrusted Content Pipeline" "stage-4,spec,code,security,critical" "${WORK}/b.md"

{ cat <<'EOF'
A deterministic gate deciding whether the LLM path runs at all — and therefore what it costs.

**Depends on:** #3, #12, #22
**Deliverable:** `docs/specs/SPEC-P4.2-GATE.md` + implementation + concurrency test
**Prompt:** `docs/PROMPT-PACK.md` → *P4.2 — Inference Gate*

### Gate conditions

Top-N by quantitative score (**N comes from the budget in #3**), OR a statistically anomalous condition (each defined with statistic, window, threshold), OR an open position due for thesis re-validation.

### Hard budget

Per-run, per-day, per-month token and dollar caps. On exhaustion the gate closes, the pipeline continues without LLM input, and an alert fires. **Never degrade silently.**

### Also

- Cache key = content hash + prompt version + model version. Identical inputs are never paid for twice.
- Per-call accounting into `llm_calls`: tokens in/out, model, latency, dollar cost, cache hit/miss, and the decision it fed
- **The loop guard**: a hard maximum LLM calls per `run_id` that **trips the kill switch** when exceeded — this is the agent-loop trigger from #17
- Deterministic and auditable: log the gate decision and reason for every candidate, **including the ones excluded**

### Acceptance

- [ ] Test proving the monthly cap holds under concurrency
EOF
footer; } > "${WORK}/b.md"
mkissue "P4.2 — Inference Gate" "stage-4,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
The only LLM-facing component in the system.

**Depends on:** #22, #23
**Deliverable:** `docs/specs/SPEC-P4.3-RESEARCH.md` + implementation + prompt file + grammar parser
**Prompt:** `docs/PROMPT-PACK.md` → *P4.3 — Research Agent (LLM)*

### Scope, and nothing beyond it

News synthesis, filing summarisation, earnings-call reading, thesis generation with bull and bear cases, risk-factor identification, and invalidation conditions. **The LLM does not produce numbers that feed a calculation.**

### Invalidation conditions are the critical output

Each must be expressed in a **restricted, machine-evaluable grammar** over known metrics (price, score, fundamental field, event type, date) — not free text. Give the grammar, its parser, and its evaluator. **Free-text conditions are rejected at validation.**

### Also

- Output schema strict and bounded: enums where possible, length caps, required citations referencing fragment IDs from #22, and a confidence documented as **uncalibrated and forbidden from sizing**
- The numeric-hallucination guard: the model is given the numbers and **forbidden to restate any number not present in its input, verified programmatically**
- Model params (temperature, top_p, max tokens, seed, stop) each with a reason; deterministic where the provider allows
- Fallback chain DeepSeek → GPT-4o-mini → **no LLM output at all**, each downgrade logged and reducing the LLM weight
- Prompt and response stored verbatim in the audit trail

### Acceptance

- [ ] Hallucinated-number rejection test
- [ ] Grammar parser with a dry-run proving each condition is evaluable against live data today
EOF
footer; } > "${WORK}/b.md"
mkissue "P4.3 — Research Agent (LLM)" "stage-4,spec,code,ml" "${WORK}/b.md"

{ cat <<'EOF'
**Assume the LLM output is wrong.** A validation layer that can reject it entirely.

**Depends on:** #24
**Deliverable:** `docs/specs/SPEC-P4.4-LLM-VALIDATION.md` + implementation + hostile fixtures
**Prompt:** `docs/PROMPT-PACK.md` → *P4.4 — LLM Output Validation*

### Eight ordered checks, each with its rejection action

1. Schema — strict, no coercion
2. **Citation** — every claim references a fragment ID that exists in the input
3. **Numeric** — every number in the output appears in the input, or is derivable by a whitelisted operation within tolerance. Otherwise reject.
4. Consistency — bull and bear cases not identical, not contradicting the quant score beyond tolerance without an explanation field
5. Entity — the output is about the requested instrument and no other
6. Grammar — invalidation conditions parse **and dry-run evaluate**
7. **Injection residue** — instruction-like text in the output is rejected and logged as a security event
8. Sanity bounds — confidence in range, no empty required fields, no boilerplate refusal text

### Rejection policy

Retry at most N times with a stricter prompt, then fall through to no-LLM. Log every rejection with a reason code. **Track the rejection rate as a monitored metric — a rising rate is an incident.**

### Acceptance

- [ ] Fixture suite of malformed, hallucinated, and hostile outputs that must **all** be rejected
EOF
footer; } > "${WORK}/b.md"
mkissue "P4.4 — LLM Output Validation" "stage-4,spec,code,security" "${WORK}/b.md"

# ============================================================== STAGE 5 =======
stage "Stage 5 — VALIDATE"

{ cat <<'EOF'
An event-driven backtester that runs the **identical production decision code**. Its only job is to not lie.

**Depends on:** #5, #10, #11, #12, #15, #16, #21
**Deliverable:** `docs/specs/SPEC-P5.1-BACKTEST.md` + implementation + determinism test
**Prompt:** `docs/PROMPT-PACK.md` → *P5.1 — Backtest Engine*

### Code reuse is mandatory — this is the point of the phase

Scanner, features, scorers, decision engine, sizing, risk engine, and exit engine are the **production classes**, not reimplementations. A `Clock`, a `DataSource`, and a `Broker` are injected. List every place production code would otherwise call wall-clock time, a random number, or the network, and how each is intercepted.

**Add a test that fails if production code reads the wall clock directly.** Divergence between backtest and live is the single most common way systems like this lie to you.

### Look-ahead prevention must be structural

The data source **physically cannot** return a record whose `knowledge_time` is after the simulated clock. Show the mechanism and the test — not a convention, a wall.

### Also

- Point-in-time universe, delisted symbols, survivorship handling
- Corporate actions at the right time with the right cash effects: dividends, splits, spin-offs, mergers, rights issues, plus tax withholding
- Fill model: queue position assumption, whether a limit at the touch fills, partial fills, gaps, halts, limit-up/down — **and an explicit list of every optimistic assumption made**
- Cash, margin, settlement timing, interest on cash, borrow cost

### Acceptance

- [ ] Determinism test: same inputs and seed produce byte-identical output
- [ ] Known-answer test on a hand-computed 20-bar scenario
- [ ] Per-decision records identical in shape to production audit events, so backtest and live compare directly
EOF
footer; } > "${WORK}/b.md"
mkissue "P5.1 — Backtest Engine" "stage-5,spec,code,critical" "${WORK}/b.md"

{ cat <<'EOF'
The full walk-forward protocol and its statistics. **The phase whose job is to stop you fooling yourself.**

**Depends on:** #26
**Deliverable:** `docs/specs/SPEC-P5.2-WALKFORWARD.md` + runner + report template
**Prompt:** `docs/PROMPT-PACK.md` → *P5.2 — Walk-Forward Validation*

### Requirements

- Window design: IS length, OOS length, step, anchored or rolling, and the resulting number of independent test periods — every choice justified against the label horizon and the data actually available
- **Purging and embargo** sized from label horizon + feature lookback. Show why the naive split leaks.
- What is re-fit per window and what is frozen. **Anything tuned by looking at OOS results is contaminated** — state the discipline that prevents it, including how many times a human is allowed to look.
- **Multiple-testing correction** (deflated Sharpe or equivalent) with the trial count recorded honestly, and a stated method for counting trials
- Every metric defined precisely: Sharpe/Sortino/Calmar with risk-free rate, annualisation factor, return frequency; max drawdown and its duration; win rate; profit factor; turnover; capacity
- **Regime slicing** — a strategy profitable only in one regime is rejected
- Monte Carlo: trade-order shuffle, return bootstrap, parameter perturbation, each with what it tests and its pass threshold

### Acceptance

- [ ] Pass gate implemented: Sharpe > 1.0, max DD < 15%, OOS > 70% of IS
- [ ] **A failing strategy is not tweaked and re-run** — specify the cooling-off period and the documentation required
EOF
footer; } > "${WORK}/b.md"
mkissue "P5.2 — Walk-Forward Validation" "stage-5,spec,code,ml,critical" "${WORK}/b.md"

{ cat <<'EOF'
A cost model pessimistic enough that live results are a pleasant surprise.

**Depends on:** #2, #26
**Deliverable:** `docs/specs/SPEC-P5.3-COSTS.md` + implementation + sensitivity table
**Prompt:** `docs/PROMPT-PACK.md` → *P5.3 — Transaction Cost & Slippage Model*

### Explicit costs, per market and per broker, with exact formulas including rounding and minimums

Commission schedule, exchange fees, SEBI turnover fees, STT, stamp duty, GST, SEC and FINRA TAF fees, clearing charges, DP charges.

### Implicit costs

Half-spread as a function of price and liquidity tier, market impact as a function of participation rate (state the model and coefficients, **labelled ASSUMPTION if unfitted**), delay cost, and opportunity cost of unfilled orders. Plus borrow cost and FX conversion for the India sleeve.

### The test that matters

Strategy performance at **1×, 2×, and 3× the modelled cost**. A strategy that dies at 2× is not deployable.

### Acceptance

- [ ] Sensitivity table produced
- [ ] The calibration loop defined: how these get fitted to real fills once paper trading starts, and how that feeds back into the backtester
EOF
footer; } > "${WORK}/b.md"
mkissue "P5.3 — Transaction Cost and Slippage Model" "stage-5,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
The complete testing pyramid, with the specific tests this system needs.

**Depends on:** #16, #17, #19, #26
**Deliverable:** `docs/specs/SPEC-P5.4-TESTING.md` + conftest + fixtures + first suite
**Prompt:** `docs/PROMPT-PACK.md` → *P5.4 — Test Strategy*

### Property-based invariants (Hypothesis), at minimum

- The risk engine never returns `ALLOW` on malformed input
- Position sizing never exceeds any cap, for any input
- The audit chain verifies after **any** sequence of appends
- The order state machine never reaches an illegal state
- Money arithmetic never loses a cent

### Also

- Coverage floors per module, with risk engine, kill switch, execution, and sizing held to a **higher bar** than the rest. State the numbers.
- Golden-file tests on frozen historical dates, with an update procedure that makes casual updates hard
- Contract tests: every broker adapter passes the same conformance suite
- **Replay tests**: re-derive a recorded production run and assert bit-identical decisions
- Chaos: provider outage mid-run, DB unavailable, Redis flush, clock jump, duplicate fill, out-of-order fill, unknown position, network partition during submit, **process kill at every step of the execution journal**
- Backtest-vs-live parity as a first-class always-running check
- **Never mocked: the risk engine and the audit chain are always real in tests**

### Acceptance

- [ ] CI gating defined: what blocks a merge, what runs nightly, and the flake policy
EOF
footer; } > "${WORK}/b.md"
mkissue "P5.4 — Test Strategy" "stage-5,spec,code" "${WORK}/b.md"

{ cat <<'EOF'
Written, rehearsed procedures for the bad days.

**Depends on:** #17, #19, #29
**Deliverable:** `docs/specs/SPEC-P5.5-CHAOS.md` + runbooks + drill scripts
**Prompt:** `docs/PROMPT-PACK.md` → *P5.5 — Chaos, Reconciliation & Recovery Drills*

### Reconciliation

Positions, orders, cash, and NAV against the broker — on startup, on a timer, at end of day. **Tolerance is zero.** Define the diff, classify each mismatch type, and the action for each: **always halt-and-page, never auto-trade to fix.**

### Runbooks, each with steps, decision points, and expected end state

Process crash with open orders · broker outage with open positions · data provider outage mid-session · database corruption · Redis loss · kill switch tripped at 09:31 · a discovered position we never opened · duplicate fill · a fill for an order we cancelled · stale NAV · bad deploy discovered mid-session.

### Acceptance

- [ ] Drill schedule: which drills, how often, in which environment
- [ ] **A drill that has never been run does not count as a procedure** — first run of each recorded
- [ ] RPO and RTO per component with the **measured actual**, not the aspirational
- [ ] Incident record format and post-incident review requirement
EOF
footer; } > "${WORK}/b.md"
mkissue "P5.5 — Chaos, Reconciliation and Recovery Drills" "stage-5,spec,ops" "${WORK}/b.md"

# ============================================================== STAGE 6 =======
stage "Stage 6 — OPERATE"

{ cat <<'EOF'
Metrics, logs, traces, and dashboards that answer "is it behaving?" in ten seconds.

**Depends on:** #7, #17, #19, #20
**Deliverable:** `docs/specs/SPEC-P6.1-OBSERVABILITY.md` + metric defs + Prometheus rules + Grafana JSON
**Prompt:** `docs/PROMPT-PACK.md` → *P6.1 — Observability*

### Metric catalogue

Name, type, labels, **cardinality estimate**, and the question it answers. Covering: stage latency and success rate, data freshness and quality, funnel counts per stage, gate rate, LLM cost and rejection rate, decision distribution, **risk verdict distribution by rule ID**, order latency, fill rate, slippage vs model, exposure gauges, P&L and drawdown, error rates, and **every kill-switch trigger input as a live gauge**.

### Three dashboards, specified panel by panel

**Operations** (is it running) · **Trading** (what is it doing) · **Risk** (how close are we to the edge). Each panel names its query and the threshold that turns it red.

### The alerts people forget

No decisions produced today · the pipeline did not run · **the alerting pipeline itself is down** · metrics went stale.

### Acceptance

- [ ] Structured log schema with required correlation fields and a **redaction filter** — no secret or PII ever logged
- [ ] Tracing with `run_id` as the trace ID
- [ ] **Alert-fatigue budget**: max tolerable alerts per week, and what happens when exceeded
EOF
footer; } > "${WORK}/b.md"
mkissue "P6.1 — Observability" "stage-6,spec,code,ops" "${WORK}/b.md"

{ cat <<'EOF'
A complete threat model and the controls that answer it.

**Depends on:** #6, #18, #22
**Deliverable:** `docs/specs/SPEC-P6.2-SECURITY.md` + threat model + hardening checklist as a script
**Prompt:** `docs/PROMPT-PACK.md` → *P6.2 — Security & Secrets*

### Threat model

STRIDE across every trust boundary, plus the trading-specific threats named in the research summary: prompt injection, data fabrication, tool-response hijacking, state tampering, memory poisoning — **and the insider case**.

### Secrets

Vault topology, auth method, lease and renewal, rotation schedule and the **zero-downtime rotation procedure**, least privilege (**data credentials cannot trade; trading credentials cannot withdraw**), break-glass access, and audit of secret reads.

**State plainly what happens today if a broker key leaks — the exact, minutes-long procedure.**

### Also

- Network: static IP for India, VPC and security-group rules as a table, egress allowlist, TLS with pinning where supported, no inbound except a bastion
- App: authn/authz for the API **and the manual kill switch**, two-person rule for limit changes, dependency pinning with hashes and a scanning/update policy
- **Abuse cases**: what an attacker does with read access, with write access, with code execution — and which control limits each blast radius

### Acceptance

- [ ] Hardening checklist expressed as a **verifiable script**, not prose
- [ ] Detection: which security events are logged, which alert, and how a compromise would actually be noticed
EOF
footer; } > "${WORK}/b.md"
mkissue "P6.2 — Security and Secrets" "stage-6,spec,code,security,critical" "${WORK}/b.md"

{ cat <<'EOF'
Map every regulatory requirement to a concrete, testable control in the code.

**Depends on:** #1, #19, #21
**Deliverable:** `docs/specs/SPEC-P6.3-COMPLIANCE.md` + matrix + enforcement code + tests
**Prompt:** `docs/PROMPT-PACK.md` → *P6.3 — Compliance*

> **Ordering constraint: must be complete before the first live order.** SEBI strategy ID and OPS caps are per-order properties, not a bolt-on.

### SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013

Unique strategy ID stamped on every order (where generated, its format, where stored, how it reaches the broker) · OPS threshold with **client-side counting and enforcement with a margin** · the registration trigger and who owns that decision · broker-hosting implications for deployment · live-like testing evidence · static IP · 2FA.

### India

STT, stamp duty, GST, T+1 settlement, ASM/GSM surveillance lists, **circuit limits and how the system behaves at a circuit**, STCG/LTCG tracking.

### US

PDT rule (how day trades are counted, the equity check before the fourth), wash-sale tracking across accounts and substantially identical securities, best-execution documentation, Reg SHO locate if shorting.

### The line the system must not cross

Trading **only the owner's account**. Specify the technical control preventing a second person being onboarded without a licence, and the exact not-investment-advice warning surfaced in every report.

### Acceptance

- [ ] Requirement → control → test matrix, three columns filled for every row
- [ ] A compliance test suite that **runs in CI and fails the build on violation**
- [ ] Record retention and the regulator export procedure
EOF
footer; } > "${WORK}/b.md"
mkissue "P6.3 — Compliance" "stage-6,spec,code,compliance,critical" "${WORK}/b.md"

{ cat <<'EOF'
A reproducible, reversible deployment on one VM, plus the plan for when the VM dies.

**Depends on:** #5, #6, #29, #31
**Deliverable:** `docs/specs/SPEC-P6.4-DEPLOY.md` + compose files + CI workflow + runbooks
**Prompt:** `docs/PROMPT-PACK.md` → *P6.4 — Deployment, CI/CD & Disaster Recovery*

### Module boundaries enforced by tooling

A lint rule that fails if, say, the execution package imports the LLM package. Boundaries that are only documented are not boundaries.

### Deployment with market hours as a constraint

The deploy window · the pre-deploy checklist (flat or not, kill-switch state, in-flight orders) · **a migration procedure for a database that must not lose the audit chain** · a rollback that **must not lose audit records** · post-deploy verification.

### Also

- Health checks that gate startup on dependencies being **actually ready**, not merely running
- No secret in an image layer
- CI: lint, strict type check, tests by tier, security scan, build — and exactly which gates block a merge
- Backups: what, how often, **tested restore**, offsite copy, and **the last-restore-test date as a monitored metric**

### Acceptance

- [ ] Rebuild-from-scratch runbook with a measured RTO
- [ ] Plan for open positions during an outage, including the manual broker-UI fallback and **who is authorised to use it**
- [ ] Plan for the broker itself being the thing that is down
EOF
footer; } > "${WORK}/b.md"
mkissue "P6.4 — Deployment, CI/CD and Disaster Recovery" "stage-6,spec,code,ops" "${WORK}/b.md"

{ cat <<'EOF'
Make each of the seven promotion stages an objective, measurable gate that cannot be argued past.

**Depends on:** #27, #28, #33
**Deliverable:** `docs/specs/SPEC-P6.5-GOLIVE.md` + a gate-evaluation script
**Prompt:** `docs/PROMPT-PACK.md` → *P6.5 — Paper Trading & Go-Live Gates*

### Per stage — backtest, walk-forward, paper, shadow, $1k, $10k, scale-up

Entry criteria with evidence · duration as **both minimum calendar time and minimum number of trades** · success metrics with numeric thresholds and the statistical test used · automatic failure conditions that end the stage immediately · the comparison procedure (paper vs backtest, shadow vs paper, live vs shadow) with the acceptable divergence · exit criteria and who signs off · **what is deliberately NOT tested at that stage and therefore still unknown**.

### Be honest about sample size

A 3-month paper run produces very few trades. State what that does to statistical significance rather than pretending the gate is stronger than it is.

### Also

- Shadow-mode design: live decisions generated and recorded without sending orders, and how the counterfactual fill is estimated for comparison
- A one-page go-live checklist, every item binary and verifiable, **ending with the manual kill-switch test performed that morning**

### Acceptance

- [ ] A gate-evaluation script that computes each metric **from the audit log** and prints PASS or FAIL
EOF
footer; } > "${WORK}/b.md"
mkissue "P6.5 — Paper Trading and Go-Live Gates" "stage-6,spec,ops,critical" "${WORK}/b.md"

{ cat <<'EOF'
A disciplined offline improvement loop. **The system never learns online.**

**Depends on:** #1, #12, #27, #33
**Deliverable:** `docs/specs/SPEC-P6.6-LEARNING.md` + registry schema + attribution report
**Prompt:** `docs/PROMPT-PACK.md` → *P6.6 — Learning & Model Governance*

### Performance attribution

Decompose P&L into selection, sizing, timing, execution, and cost — so the failing component is **identified rather than guessed at**.

### Error taxonomy

Bad data · bad feature · bad model · bad threshold · bad execution · **bad luck**. Give the diagnostic that distinguishes bad luck from a broken model, and the sample size it requires.

### The prohibition, as an enforced control

**No change may be triggered by a single trade or a single week.** State the minimum evidence and the minimum time window, and how that is enforced rather than merely intended.

### Also

- Champion/challenger: how a challenger is created, runs **shadow only**, the comparison metric, the significance test, the minimum observation period, the promotion rule, and the **automatic demotion** rule
- Model registry: training data hash, code SHA, hyperparameters, metrics, approver, deployment date, expiry, and **refusal-to-serve when expired**
- Drift monitoring: feature drift, label drift, performance decay — each with statistic, threshold, and response (alert / retrain / halt)
- **A retrained model re-enters at the walk-forward gate, not at live**

### Acceptance

- [ ] A research log recording every experiment **including the failures**, so the trial count in the deflated Sharpe calculation is honest
EOF
footer; } > "${WORK}/b.md"
mkissue "P6.6 — Learning and Model Governance" "stage-6,spec,code,ml" "${WORK}/b.md"

# =============================================================== TRACKER ======
{
cat <<'EOF'
Master tracker for the staged build of the autonomous trading agent.

Each phase below is one issue, corresponding to one prompt in `docs/PROMPT-PACK.md`, run in its **own fresh conversation**, producing one frozen spec or one code drop.

## Working rules

- **One phase = one fresh conversation.** Context bleed between phases produces specs that agree with each other because they were written together, not because they are correct.
- **Always paste Block A (Constitution) + Block B (Output Contract) + Block C (Clarifier Rule)** ahead of every phase prompt, followed by the full text of the upstream specs it depends on.
- **Specs before code.** A code phase may only cite a spec whose status is `FROZEN`.
- **Every code drop goes through template X2 in a separate conversation.** The author never reviews itself. A BLOCKER finding means the drop does not land.
- **Freezing a spec means:** merged via X3, gap-audited via X5, and its blocking open questions closed.

## Phases
EOF
cat "$TRACK"
cat <<'EOF'

## Ordering constraints that actually matter

| Constraint | Why |
|---|---|
| P1.4 (audit) before anything that emits events | Retrofitting an append-only hash chain is a rewrite |
| **P2.9 (risk engine) and P2.10 (kill switch) FROZEN and tested before any code can reach a broker** | Non-negotiable |
| P5.1 (backtest) before P5.2 (walk-forward) | Walk-forward is a protocol on top of the simulator |
| P6.3 (compliance) before the first live order | SEBI strategy ID and OPS caps are per-order, not bolt-on |

## Cross-cutting templates (run repeatedly, not one-shot issues)

| Template | When to run |
|---|---|
| **X1 — Code Generation** | Implementing any frozen spec |
| **X2 — Code Review** | After every code drop, in a separate conversation |
| **X3 — Merge** | End of each stage, folding stage output into the master spec |
| **X4 — Red Team** | Against the full merged spec, before any real money |
| **X5 — Gap Audit** | End of each stage, before starting the next |

## Known contradictions in the research summary

Unresolved in `master-research-summary.md`; settled by the phases that own them:

1. **Score weights sum to 90%, not 100%.** §6 Phase 4 gives 60% fundamental + 20% technical + 10% sentiment. Owned by **P2.5**.
2. **Sentiment agent LLM status conflicts.** §5 lists the Sentiment Agent as `LLM? No`; §9 assigns LLMs to deep sentiment analysis. Owned by **P2.5** / **P4.2**.

## Start here

**P0.1**, specifically question 13 (holding period). It cascades into data frequency, storage volume, cost model, PDT exposure, tax treatment, slippage assumptions, and whether the gated LLM tier is affordable at all. Most of the rest of the build is downstream of that one answer.
EOF
} > "${WORK}/b.md"
mkissue "[TRACKER] Build plan — 36 phases across 7 stages" "tracker" "${WORK}/b.md"

echo
echo "Done. Created 36 phase issues + 1 tracker (#${LAST_NUM})."
