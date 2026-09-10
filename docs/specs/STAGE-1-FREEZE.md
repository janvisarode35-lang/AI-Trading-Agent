---
id: STAGE-1-FREEZE
version: 1.0
status: ACTIVE
phase: Stage 1 — SPECIFY, closure (template X3 — MERGE)
depends_on: [SPEC-P1.1-DOMAIN v0.3, SPEC-P1.2-STORAGE v0.1, SPEC-P1.3-CONFIG v0.1, SPEC-P1.4-AUDIT v0.1, STAGE-0-FREEZE v1.1]
produces: [STAGE-1-FREEZE-RECORD, CONSOLIDATED-CONTRACTS-P1, CONSOLIDATED-ASSUMPTIONS-P1, CONSOLIDATED-OPEN-QUESTIONS-P1, RS-COVERAGE-MATRIX-P1, STAGE-2-ENTRY-GATE]
---

# STAGE 1 FREEZE RECORD

**Frozen at:** 2026-08-31 (UTC)
**Repository HEAD at freeze:** `8b24083`
**Template:** X3 — MERGE, run against the four Stage 1 specs and their code drops.

---

## 1. Merge form, and one deliberate deviation from X3

X3 step 1 says "merge into one coherent document". This record **indexes** the four specs and
consolidates their four contract tables; it does not physically concatenate 4,440 lines of spec
text into a fifth copy.

The reason is the same one STAGE-0-FREEZE gave: a concatenated copy becomes a second source of
truth that drifts from the first the moment either is edited, and this project already carries a
live instance of exactly that failure (see CONTRADICTION C-1 below). The specs remain the source
of truth; this record is the index, the consolidated cross-spec view, and the freeze authority.

**This is a deviation from the literal wording of X3 and is recorded as such.** If a single
physical document is required, it should be generated from the specs, never hand-maintained.

---

## 2. Frozen artifact list, with hashes

Hashes are SHA-256, first 16 hex characters, taken at HEAD `8b24083`.

| Artifact | Version | SHA-256 (16) | Lines |
|---|---|---|---|
| `docs/specs/SPEC-P1.1-DOMAIN.md` | 0.3 | `91cef3bff594bec4` | 1,209 |
| `docs/specs/SPEC-P1.2-STORAGE.md` | 0.1 | `b97b9b2806721000` | 2,249 |
| `docs/specs/SPEC-P1.3-CONFIG.md` | 0.1 | `33d306596a98226d` | 484 |
| `docs/specs/SPEC-P1.4-AUDIT.md` | 0.1 | `496e693620078d8a` | 498 |
| `src/domain/models.py` | P1.1 v0.3 | `f3b510059c447f85` | 2,896 |
| `migrations/0001_initial.sql` | P1.2 v0.1 | `abb2544a14694f95` | 1,464 |
| `src/config/loader.py` | P1.3 v0.1 | `83e3347f0eccc4b4` | 1,077 |
| `config/policy.yaml` | P1.3 v0.1 | `15693b3b6fbaf574` | 1,253 |
| `src/audit/events.py` | P1.4 v0.1 | `faee9fa97f76d0d5` | 719 |
| `src/audit/chain.py` | P1.4 v0.1 | `8298a736650d8971` | 481 |

**Verification state at freeze.** Five Python harnesses and two shell suites, all passing:
`verify_p11_invariants` 42, `verify_p11_p12_contract` ALIGNED (21 table/model pairs),
`verify_p11_x2_regressions` 21, `verify_p13_config` 39, `verify_p14_audit` 36,
`verify_p12_migration_rerun` 6/6, `verify_p12_cagg_immutability` 6/6.

Migration 0001 **executes** against `timescale/timescaledb:2.29.2-pg16`: exit 0, 37 tables,
8 hypertables, 3 continuous aggregates, 27 triggers, all three extensions in schema `extensions`.

---

## 3. Contradictions found by the merge

X3 step 3 requires these to be presented, not silently resolved.

### C-1 — `depends_on` version drift (2 instances) — **UNRESOLVED, recommended fix below**

| Spec | Declares | Actual current |
|---|---|---|
| SPEC-P1.2-STORAGE | `SPEC-P1.1-DOMAIN v0.1` | **v0.3** |
| SPEC-P1.3-CONFIG | `SPEC-P1.1-DOMAIN v0.2` | **v0.3** |

Three downstream specs pin three different versions of one upstream spec (P1.4 correctly pins
v0.3). Nothing in the pack verifies that a cited version is current, so this drifted silently.

`verify_p11_p12_contract` reports 21 table/model pairs ALIGNED, so the drift is **documentary,
not behavioural** — P1.2 was written against v0.1 but does not contradict v0.3.

**Recommended resolution:** bump both `depends_on` entries to `v0.3` and add a CI check asserting
every `depends_on` version equals the cited spec's current version. Not applied here, because X3
step 3 forbids silent resolution.

### C-2 — six contracts exist in code and in the CONTRACTS table but not in the `produces:` header

`SPEC-P1.4-AUDIT` header lists 22 contracts; its table plus the code carry six more:
`BreakKind`, `ChainBreak`, `IntentRecord`, `benchmark_verification()`, `promote_to_action()`,
`uuid7_timestamp_ms()`. All six verified present in `src/audit/`.

`produces:` is what a downstream phase reads to know what it may import, so an under-declared
header causes a consumer to re-implement something that already exists.

**Recommended resolution:** add the six to the header. Cosmetic notation differences elsewhere
(`fn.uuid7` in the header vs `uuid7() / uuid7_timestamp_ms()` in the table) are **not**
contradictions and are left alone.

### C-3 — no contract name is exported by two specs

Checked all 118 exported contracts for duplicate names with mismatched signatures. **None.** The
producer/consumer boundary between the four specs is clean.

---

## 4. Consolidated contracts — 118 across four specs

Signature mismatches between producer and consumer: **none found** (see C-3).

| # | Contract | Kind | Producing spec | Consumers |
|---|---|---|---|---|
| 1 | `Market` | enum | P1.1-DOMAIN | `IN` |
| 2 | `Exchange` | enum | P1.1-DOMAIN | `NASDAQ` \ |
| 3 | `Currency` | enum | P1.1-DOMAIN | `INR`, each with `minor_units = 2` |
| 4 | `Money` | type | P1.1-DOMAIN | every phase |
| 5 | `Price` | type | P1.1-DOMAIN | P2.x, P3.x, P5.x |
| 6 | `Quantity` | type | P1.1-DOMAIN | P2.8, P2.9, P3.2 |
| 7 | `InstrumentType` | enum, **deny-by-default** | P1.1-DOMAIN | P2.2, P2.9 |
| 8 | `InstrumentStatus` | enum | P1.1-DOMAIN | `HALTED` \ |
| 9 | `AccountType` | enum | P1.1-DOMAIN | `MARGIN` (future) |
| 10 | `PoolId` | enum | P1.1-DOMAIN | P1.2, P2.9 |
| 11 | `Instrument` | model | P1.1-DOMAIN | every phase |
| 12 | `SymbolMapping` | model | P1.1-DOMAIN | P1.2, P2.1, P5.1 |
| 13 | `SuccessorLink` | model | P1.1-DOMAIN | P2.1, P3.3 |
| 14 | `CorporateAction` | model | P1.1-DOMAIN | P2.1, P2.4, P5.1 |
| 15 | `ExchangeSession` | model | P1.1-DOMAIN | P1.2, P2.1, P2.9, P3.2 |
| 16 | `TradingCalendar` | type | P1.1-DOMAIN | P2.x, P3.x, P5.x |
| 17 | `Bar` | model | P1.1-DOMAIN | P2.1, P2.4, P5.1 |
| 18 | `Quote` | model | P1.1-DOMAIN | P2.2, P3.3 |
| 19 | `Trade` | model | P1.1-DOMAIN | P5.3 |
| 20 | `FundamentalsSnapshot` | model | P1.1-DOMAIN | P2.1, P2.5 |
| 21 | `NewsItem` | model | P1.1-DOMAIN | P2.1, P4.1, P4.3 |
| 22 | `StalenessPolicy` | model | P1.1-DOMAIN | P2.2, P2.9 |
| 23 | `Candidate` | model | P1.1-DOMAIN | P2.3, P2.5, P4.2 |
| 24 | `Score` | model | P1.1-DOMAIN | P2.5, P2.7 |
| 25 | `Signal` | model | P1.1-DOMAIN | P2.7, P3.4 |
| 26 | `Thesis` | model | P1.1-DOMAIN | P4.3, P4.4, P3.4 |
| 27 | `InvalidationCondition` | model | P1.1-DOMAIN | P3.3, P3.4 |
| 28 | `Decision` | model | P1.1-DOMAIN | P2.7, P3.2 |
| 29 | `PositionSizeRequest` | model | P1.1-DOMAIN | P2.8, P2.9 |
| 30 | `RiskVerdict` | model | P1.1-DOMAIN | `DENY`; `binding_constraint`; `max_permissible_quantity` informational |
| 31 | `Order` | model | P1.1-DOMAIN | P3.2 |
| 32 | `OrderState` | enum + transition table | P1.1-DOMAIN | P3.2, P3.3 |
| 33 | `Fill` | model | P1.1-DOMAIN | P3.2, P3.3 |
| 34 | `Lot` | model | P1.1-DOMAIN | P3.3, P6.3, P5.1 |
| 35 | `Position` / `PositionState` | model + transition table | P1.1-DOMAIN | P2.9, P3.3 |
| 36 | `Portfolio` | model | P1.1-DOMAIN | P2.8, P2.9 |
| 37 | `PoolNAV` / `ConsolidatedNAV` | model | P1.1-DOMAIN | P2.9, P6.1 |
| 38 | `Account` | model | P1.1-DOMAIN | P2.9, P3.2 |
| 39 | `Regime` | model | P1.1-DOMAIN | P2.6, P2.7, P2.9 |
| 40 | `KillSwitch` / `KillSwitchState` | model + transition table | P1.1-DOMAIN | P2.10, P6.1 |
| 41 | `AuditEvent` | model | P1.1-DOMAIN | P1.4, every effectful phase |
| 42 | `AuditEventClass` | enum | P1.1-DOMAIN | `EVALUATION`\ |
| 43 | `RunContext` | model | P1.1-DOMAIN | every phase |
| 44 | `DomainError` hierarchy | exceptions | P1.1-DOMAIN | every phase |
| 45 | `trading.instrument` | table (bitemporal) | P1.2-STORAGE | P2.1, P2.2, P2.3, P3.1 |
| 46 | `trading.symbol_mapping` | table (bitemporal) | P1.2-STORAGE | P2.1, P5.1 |
| 47 | `trading.successor_link` | table | P1.2-STORAGE | P2.1, P3.3 |
| 48 | `trading.exchange_session` | table | P1.2-STORAGE | P2.1, P2.9, P3.2 |
| 49 | `trading.tick_size_regime` | table | P1.2-STORAGE | P3.2 |
| 50 | `trading.corporate_action` | table (bitemporal) | P1.2-STORAGE | P2.1, P2.4, P5.1 |
| 51 | `trading.bar_daily` | hypertable | P1.2-STORAGE | P2.1, P2.4, P5.1 |
| 52 | `trading.bar_intraday_5m` | hypertable | P1.2-STORAGE | P3.3 |
| 53 | `trading.bar_intraday_5m_validation` | hypertable | P1.2-STORAGE | P5.2 |
| 54 | `trading.fundamentals_snapshot` | table (bitemporal) | P1.2-STORAGE | P2.1, P2.5, P5.1 |
| 55 | `trading.news_item` | hypertable | P1.2-STORAGE | P2.1, P4.1, P4.3 |
| 56 | `trading.universe_membership` / `universe_version` | tables | P1.2-STORAGE | P2.3, P5.1 |
| 57 | `trading.fx_rate` | table (immutable) | P1.2-STORAGE | P2.9, P6.1 |
| 58 | `trading.candidate`, `score`, `thesis`, `invalidation_condition` | tables | P1.2-STORAGE | P2.5, P2.7, P4.3, P4.4 |
| 59 | `trading.risk_evaluation` | table | P1.2-STORAGE | P2.9, P1.4 |
| 60 | `trading.decision` | table | P1.2-STORAGE | P2.7, P3.2 |
| 61 | `trading.order_intent` | table | P1.2-STORAGE | P3.2, P3.3 |
| 62 | `trading.fill` | table | P1.2-STORAGE | P3.2, P3.3 |
| 63 | `trading.lot` | table | P1.2-STORAGE | P3.3, P5.1, P6.3 |
| 64 | `trading.position_state` | table | P1.2-STORAGE | P2.9, P3.3 |
| 65 | `trading.account` | table | P1.2-STORAGE | P2.9, P3.2 |
| 66 | `trading.nav_pool` / `nav_consolidated` | tables | P1.2-STORAGE | P2.9, P6.1 |
| 67 | `trading.portfolio_snapshot` | table | P1.2-STORAGE | P2.8, P6.1 |
| 68 | `trading.kill_switch_event` | table | P1.2-STORAGE | P2.10, P6.1 |
| 69 | `trading.audit_log` | hypertable | P1.2-STORAGE | **P1.4**, every effectful phase |
| 70 | `trading.verify_audit_chain(bigint)` | function | P1.2-STORAGE | P1.4, P6.4, boot sequence |
| 71 | `trading.model_registry` | table | P1.2-STORAGE | P5.2, P6.6 |
| 72 | `trading.config_version` | table | P1.2-STORAGE | P1.3, P6.4 |
| 73 | `trading.llm_call` | hypertable | P1.2-STORAGE | P4.3, P6.1 |
| 74 | `trading.run_context` | table | P1.2-STORAGE | every phase |
| 75 | `fundamentals_asof`, `news_asof`, `universe_asof`, `instrument_asof`, `symbol_asof` | functions | P1.2-STORAGE | **P5.1, P5.2** |
| 76 | `cagg_llm_spend_daily`, `cagg_audit_events_daily`, `cagg_bar_weekly` | continuous aggregates | P1.2-STORAGE | P6.1, P2.6 |
| 77 | roles `trading_owner` / `app_rw` / `backtest_ro` / `metrics_ro` | roles | P1.2-STORAGE | P6.2, P6.4 |
| 78 | `config/policy.yaml` | file | P1.3-CONFIG | P2.9, P2.10, every phase that reads a limit |
| 79 | `PolicyLoader.load()` | method | P1.3-CONFIG | P2.9, P6.4 |
| 80 | `EffectiveConfig` | model | P1.3-CONFIG | P2.9, P1.4 |
| 81 | `EffectiveConfig.audit_payload()` | method | P1.3-CONFIG | P1.4, P6.1 |
| 82 | `PolicyDocument` | model | P1.3-CONFIG | P2.9 |
| 83 | `PolicyDocument.evaluation_order()` | method | P1.3-CONFIG | **P2.9** — the ordering contract |
| 84 | `Rule` | model | P1.3-CONFIG | P2.9 |
| 85 | `PolicyGate.evaluate()` | method | P1.3-CONFIG | **P2.9** |
| 86 | `PolicyVerdict` | model | P1.3-CONFIG | P2.9, P2.10, P1.4 |
| 87 | `RuleOutcome` | model | P1.3-CONFIG | P1.4 |
| 88 | `ACTION_PRECEDENCE` | constant | P1.3-CONFIG | P2.9 |
| 89 | `content_hash()` / `canonical_bytes()` | functions | P1.3-CONFIG | P1.4, P6.4 |
| 90 | `assert_change_authorised()` | function | P1.3-CONFIG | P6.2, P6.4 |
| 91 | `loosens_for()` | function | P1.3-CONFIG | P6.2 |
| 92 | `merge_layers()` | function | P1.3-CONFIG | P6.4 |
| 93 | `VaultRef` | model | P1.3-CONFIG | P6.2 |
| 94 | `lint_no_env_risk_reads()` / `assert_no_env_risk_reads()` | functions | P1.3-CONFIG | **CI**, P6.4 |
| 95 | `infra_env()` | function | P1.3-CONFIG | P6.2, P6.4 |
| 96 | `INFRA_ENV_ALLOWLIST` | constant | P1.3-CONFIG | P6.2 |
| 97 | Rule ids `EXP-001`…`LLM-003` | identifiers | P1.3-CONFIG | P2.9, P1.4, P6.1, P6.3 |
| 98 | `AuditEnvelope` | model | P1.4-AUDIT | **Every effectful phase** |
| 99 | `EventType` | enum | P1.4-AUDIT | every phase |
| 100 | `EVENT_REGISTRY` | mapping | P1.4-AUDIT | every producer phase |
| 101 | `EFFECTFUL_EVENT_TYPES` | frozenset | P1.4-AUDIT | P3.2, P2.10 |
| 102 | `REPRODUCIBLE_EVENT_TYPES` | frozenset | P1.4-AUDIT | P2.5, P2.9, P4.3 |
| 103 | `Producer` | enum | P1.4-AUDIT | every phase |
| 104 | `ReproducibilityBundle` | model | P1.4-AUDIT | P2.5, P2.6, P2.7, P2.9, P4.3 |
| 105 | `uuid7()` / `uuid7_timestamp_ms()` | functions | P1.4-AUDIT | P1.2 writer, every producer |
| 106 | `canonical_json()` / `canonical_bytes()` | functions | P1.4-AUDIT | **P1.2's hash trigger**, P6.3 |
| 107 | `CANONICAL_SCHEMA_VERSION` | constant | P1.4-AUDIT | P1.2, P6.3 |
| 108 | `verify_chain()` | function | P1.4-AUDIT | P6.1, P6.4, boot sequence |
| 109 | `assert_chain_intact()` | function | P1.4-AUDIT | boot sequence, P6.4 |
| 110 | `BreakKind` / `ChainBreak` | enum + record | P1.4-AUDIT | P6.1 |
| 111 | `Anchor` / `verify_against_anchor()` | model + function | P1.4-AUDIT | P6.1, P6.2 |
| 112 | `benchmark_verification()` | function | P1.4-AUDIT | P6.4 runbook |
| 113 | `write_before_act()` | function | P1.4-AUDIT | **P3.2**, P2.10 |
| 114 | `recover_incomplete_intents()` | function | P1.4-AUDIT | **P3.2**, P6.4 |
| 115 | `IntentRecord` | record | P1.4-AUDIT | P3.2 |
| 116 | `replay_run()` | function | P1.4-AUDIT | **P5.1**, P6.6 |
| 117 | `export_for_regulator()` | function | P1.4-AUDIT | **P6.3** |
| 118 | `promote_to_action()` | function | P1.4-AUDIT | P1.2 writer, P2.3 |
---

## 5. Consolidated assumptions — 32, ranked by blast radius

Ranking is by what breaks if the assumption is false, not by likelihood.

**Tier 1 — would invalidate a capacity or correctness decision**

| # | Assumption | Where it bites |
|---|---|---|
| T1-a | Mean `audit_log` row ~1,000 B (P0.3 §2.1's single most load-bearing assumption) | P0.3 §9.4 storage model. Stress-tested to 5×; breaks at ~10× (150k events/session) |
| T1-b | 15,000 audit events per session | Same model. `[DEFAULT-B4]`, inherited from ADR-13 Chain B |
| T1-c | Round-trip cost 25 bps US / 90 bps India | Every backtest edge estimate. Measured in P5.3 after ≥200 live fills |

**Tier 2 — would force a schema or policy change**

Includes the India price floor (`min_price_inr` 50.00, unverified), the PDT equity floor
(25,000, `ASSUMPTION [VERIFY-P0.2]`), and TimescaleDB compression ratios on the audit trail.

**Tier 3 — local, recoverable**

The remainder. Full per-spec detail below, unmodified from source.

| # | Source | Assumption | Impact if false |
|---|---|---|---|
| A1 | P1.1-DOMAIN | `[DEFAULT-1]` `instrument_id` is per listing venue, not per issuer | Cross-venue aggregation needs an `issuer_id` rollup — a reporting join, not a migration, since `issuer_id` already exist |
| A2 | P1.1-DOMAIN | `[DEFAULT-2]` `Price` at 6 dp is sufficient | If a vendor emits >6 dp, prices truncate silently; the check is one query and belongs in P2.2's quality gate |
| A3 | P1.1-DOMAIN | `[DEFAULT-3]` Fractional shares are unreachable in v1 | If fractional works with limit orders, `qty_increment` becomes a per-instrument value and sizing gains resolution at sma |
| A4 | P1.1-DOMAIN | `[DEFAULT-4]` Largest-remainder allocation with ascending-index tie-break | A different tie-break changes cent placement; deterministic replay would diverge between two implementations |
| A5 | P1.1-DOMAIN | `[DEFAULT-5]` Naive datetimes are rejected, not coerced | Ingest adapters for a vendor that emits naive timestamps need an explicit tz declaration — which is the correct outcome |
| A6 | P1.1-DOMAIN | `[DEFAULT-6]` India has no wash-sale rule, so the field must be `NULL` for `IN` | If India has an analogous rule, the validator inverts and the India tax export needs the field |
| A7 | P1.1-DOMAIN | `[DEFAULT-7]` `RegimeLabel` is the four `[RS §13]` labels plus `UNKNOWN` | Adding a member is additive and cheap; the closed enum is what matters, not the exact membership |
| A8 | P1.1-DOMAIN | `[DEFAULT-8]` `[CONST-2]` is enforced structurally at the `Decision` constructor | If a bypass exists, `[CONST-1]` is decorative. This is the single highest-value test in the suite |
| A9 | P1.1-DOMAIN | `[DEFAULT-9]` P1.1 owns the audit envelope, P1.4 the catalogue | If P1.4 wants the envelope too, the two must merge — a rename, not a redesign |
| A10 | P1.1-DOMAIN | `[DEFAULT-10]` `UNKNOWN` is a persisted order state | Without it, an ambiguous broker response becomes a retry and then a duplicate order |
| A11 | P1.1-DOMAIN | US and India equity settlement are both T+1 | `settlement_date` is computed by the calendar loader from a configured cycle, so a different cycle is a config change. B |
| A12 | P1.1-DOMAIN | A merger preserves the tax holding period and cost basis on a share-for-share exchange | Lot `opened_on` would reset on conversion, changing STCG/LTCG classification in India and wash-sale windows in the US |
| A13 | P1.1-DOMAIN | FIFO is the correct cost-basis method | `CostBasisMethod` is already an enum with `LIFO` and `AVERAGE`, so the change is a config value plus a re-run of the lot |
| A14 | P1.2-STORAGE | `[DEFAULT-S1]` `SECURITY DEFINER` as-of functions cover every legitimate backtest read | A missing function blocks a backtest — loud and safe, which is the intended direction of failure |
| A15 | P1.2-STORAGE | `[DEFAULT-S4]` 6 dp is enough price precision through the November 2027 regime | Truncation on a higher-precision vendor. Detected by the P2.2 quality gate |
| A16 | P1.2-STORAGE | 15× / 4× compression ratios | At 8× overall, year-10 compressed is ~19 GB and on-VM ~62 GB — still 4× headroom on 250 GB |
| A17 | P1.2-STORAGE | ~1,000 B mean `audit_log` row | P0.3 §9.4 already stress-tests to 10×: at 150,000 events/session the 250 GB volume needs resizing. Below 5× it holds |
| A18 | P1.2-STORAGE | ~8 KB mean `llm_call` row | 4× would be 300 MB compressed — still immaterial |
| A19 | P1.2-STORAGE | ~200 news items/day with revision factor `rf` unmeasured | At `rf = 3`, +250 MB compressed. P0.3 already declares this immaterial against 4.7× headroom |
| A20 | P1.2-STORAGE | `pgbackrest` is the archive tool | Any tool with WAL push and PITR substitutes; `archive_command` is one line |
| A21 | P1.2-STORAGE | An off-VM WAL receiver is reachable with low enough latency for the 5 s intraday budget | If it exceeds the budget, the intraday exit path moves to `local` durability with a stated, audited RPO > 0 for exits on |
| A22 | P1.3-CONFIG | `[DEFAULT-C4]` `cryptography` is acceptable despite `[CONST]`'s dependency rule | Fall back to HMAC and abandon per-approver attribution — i.e. abandon the two-person rule as a *provable* control |
| A23 | P1.3-CONFIG | `[DEFAULT-C7]` Two approvers is the right number | If 1 is correct, `min_approvals_to_loosen` drops to 1 and the `Governance` validator relaxes. Note the validator current |
| A24 | P1.3-CONFIG | India universe thresholds (`min_price_inr`, ranks) | India is unfunded, so nothing live depends on it. Wrong values would mis-size the India universe on the day the gate ope |
| A25 | P1.3-CONFIG | `MAX_MODIFY_PASSES = 4` is enough | If a future rule pair oscillates, the verdict is DENY — fail-closed, but a silently un-tradeable name. Instrument the pa |
| A26 | P1.3-CONFIG | Ed25519 public key is retrievable from Vault at boot | If Vault is unreachable at boot the process does not start — correct, and consistent with ADR-09 row 11's fail-closed ha |
| A27 | P1.3-CONFIG | `assumed_round_trip_bps` 25 US / 90 IN | `EDGE-001` gates on it. Too low → trades that do not clear cost; too high → no trades. Measurement-by-design **Q13** |
| A28 | P1.4-AUDIT | 18,538 events/s holds at 10M rows | The real cost adds I/O — the projection covers CPU only. If disk-bound, verification becomes a streaming job rather than |
| A29 | P1.4-AUDIT | `[DEFAULT-A8]` No natural-person data enters the log | If the ownership model changes, §8.2 is void, GDPR/DPDP erasure conflicts head-on with an immutable log, and that confli |
| A30 | P1.4-AUDIT | Off-VM anchor storage is write-once with distinct credentials | An anchor store the database's credentials can rewrite provides **no** additional guarantee — it would be security theat |
| A31 | P1.4-AUDIT | One anchor per session bounds the blast radius acceptably | A required cadence tightens the parameter; the mechanism is unchanged |
| A32 | P1.4-AUDIT | ~1 KB mean event, 15,000/session | P0.3 §9.4 stress-tests to 10×; at 150,000/session the 250 GB volume needs resizing |
---

## 6. Consolidated open questions — 29 unique

### 6.1 The four that block a Stage 2 phase

| Q | Blocks | Effect |
|---|---|---|
| **Q-P1.1-1** | **P2.9** | US settlement / good-faith rules. `settled_cash` sizing is unimplementable without it |
| **Q-P1.1-2** | **P2.9** | India settlement cycle. Not blocking while India is unfunded |
| **Q-P1.1-6** | **P2.2** | Confirms or refutes `[DEFAULT-2]` in the quality gate |
| **Q-P1.3-3** | **P2.9** | Whether the RISK stage's 60 s budget holds with 47 rules × ~20 candidates. A measurement, not a documentary gate |

**None of these blocks P2.1.** Stage 2 may begin at P2.1; P2.2 and P2.9 have named prerequisites.

### 6.2 Partially closed by the Stage 1 code drops

**Q-P1.2-6** — *"Does migration 0001 execute, and do its runtime behaviours hold?"* The first
half is **CLOSED**: the migration executes (§2 above). The second half is **OPEN** — five named
runtime assertions remain untested: `ENABLE ALWAYS` triggers under
`session_replication_role = 'replica'`; `EXCLUDE` rejecting an overlapping symbol mapping; a
`DENY` verdict rejected by `decision`; `backtest_ro` denied on a base table; the overfill
trigger firing on a deferred commit. Blocks **P6.4**, not Stage 2.

**Q-P1.2-1** — already marked CLOSED in source by SPEC-P1.4 §6.2 (`jcs-nonum-1`).

### 6.3 Full register

| Q | Source | Question | Blocks |
|---|---|---|---|
| M-1 | P1.1-DOMAIN | Alpaca idempotency-key **charset** | P3.2. Constrains a field this spec types as `str` |
| M-12 | P1.2-STORAGE | News revision factor `rf` | Not blocking. P0.3 declares it immaterial |
| M-9 | P1.1-DOMAIN | Broker detail gaps — including idempotency-key semantics for Zerodha and Upstox | P3.2. Rule N12 already prescribes client-side dedupe in the interim |
| Q-P1.1-1 | P1.1-DOMAIN | Is US equity settlement T+1, and what exactly constitutes a good-faith violation in a cash account? | **P2.9** — `settled_cash` sizing is unimplementable without it. Also P1.2's session table |
| Q-P1.1-2 | P1.1-DOMAIN | What is the NSE equity settlement cycle and its holiday-shift rule? | P2.9, and P1.2's `settlement_date` computation. Not blocking while India is unfunded |
| Q-P1.1-3 | P1.1-DOMAIN | Can a US fractional order be a **limit** order, or is it market/day only? | **P3.1/P3.2.** If market/day only, `[CONST]`'s limit-order default makes fractional unreachable and `qty_incre |
| Q-P1.1-4 | P1.1-DOMAIN | Does India have a wash-sale-equivalent (bed-and-breakfasting) restriction on listed equity? | P6.3 tax export. Folds into existing item **Q8** |
| Q-P1.1-5 | P1.1-DOMAIN | Does a share-for-share merger preserve the tax holding period in both jurisdictions? | P6.3. Not blocking Stage 1 |
| Q-P1.1-6 | P1.1-DOMAIN | What is the maximum decimal precision any selected vendor emits for a trade price? | P2.2 quality gate. Confirms or refutes `[DEFAULT-2]` |
| Q-P1.1-7 | P1.1-DOMAIN | Is `Money` at 2 dp correct for INR in all broker-reported contexts, or does any Zerodha field carry paise beyo | P3.1. If a field carries more precision, the INR minor-units constant needs a per-field exception |
| Q-P1.1-8 | P1.1-DOMAIN | An **independent** X2 review, by someone who did not author this spec | **Not blocking P1.3.** §15.1 is explicit that the 2026-08-27 X2 was author-run, and F-1 survived a suite passi |
| Q-P1.2-1 | P1.2-STORAGE | ~~What is the canonical JSON serialisation the hash chain covers?~~ | **Closed.** P1.2's §9.4 trigger comment describing `NEW.payload::text` as interim is now resolved |
| Q-P1.2-2 | P1.2-STORAGE | What is the commit latency to the off-VM WAL receiver, and does it fit P0.3 §6.2's 5 s intraday exit budget? | **P6.4/P6.5 go-live.** If it does not fit, ADR-10's RPO 0 and P0.3's exit budget are in direct tension and one |
| Q-P1.2-3 | P1.2-STORAGE | Does TimescaleDB compression on `audit_log` interact with the `ENABLE ALWAYS` deny-mutation triggers? | **P1.4 / P6.4.** A compression job blocked by our own trigger would silently stop compressing and the disk mod |
| Q-P1.2-4 | P1.2-STORAGE | What is the real mean `audit_log` row width and events/session? | Not blocking. Feeds P0.3 §9.4's sensitivity and the T4 re-open trigger |
| Q-P1.2-5 | P1.2-STORAGE | Is `pg_advisory_xact_lock` on the chain head acceptable under the P1.4 writer's concurrency? | **P1.4.** At 10× it is still far from contended, but the number should be measured rather than argued |
| Q-P1.2-6 | P1.2-STORAGE | Does migration 0001 execute, and do its runtime behaviours hold? | **P6.4.** Static checks pass (§6.11) but the DDL is unexecuted — Docker's storage layer is read-only on the bu |
| Q-P1.3-1 | P1.3-CONFIG | Who is the second approver, and how is their identity bound to a signing key? | **Any limit increase.** Not blocking P1.4 — tightening and kill both work at team size 1 |
| Q-P1.3-2 | P1.3-CONFIG | India universe price floor and hysteresis ranks | India activation. Unfunded, so not blocking |
| Q-P1.3-3 | P1.3-CONFIG | Does the `RISK` stage's 60 s budget hold with 47 rules evaluated without short-circuit, across ~20 candidates? | **P2.9.** 47 in-memory comparisons per candidate should be sub-millisecond, but P0.3 §6.1 sets the budget and  |
| Q-P1.3-4 | P1.3-CONFIG | Should `PORT-002` (15–25 position band) be `enforce` rather than `monitor`? | P6.6. Promoting it is a tightening — no approval needed (ADR-09 row 3) |
| Q-P1.4-1 | P1.4-AUDIT | Where are anchors published, and with what credentials? | **P6.2/P6.4 go-live.** Until then the chain is session-internal only |
| Q-P1.4-2 | P1.4-AUDIT | Do SEBI or SEC name a required audit retention, format or anchoring cadence? | **P6.3.** Our indefinite retention is likely to exceed any minimum; the **format** may not match. Folds into c |
| Q-P1.4-3 | P1.4-AUDIT | Does deep verification hold ~18.5k events/s when reading from TimescaleDB rather than memory? | P6.4's operational runbook. If I/O-bound, verification becomes streaming |
| Q-P1.4-4 | P1.4-AUDIT | Should P1.2's `audit_log` gain a `canonical_schema` column? | **P1.2 X2.** Additive column, cheap now (P1.2 §11.2 rule 1), expensive after the table has rows |
| Q10 | P1.4-AUDIT | Record-retention minima | P6.3 |
| Q13 | P1.3-CONFIG | Round-trip transaction cost | Feeds `EDGE-001` |
| Q15 | P1.4-AUDIT | Audit event rate and row width | Feeds P0.3 §9.4 and the T4 re-open trigger |
| Q8 | P1.1-DOMAIN | India tax schedule — STCG/LTCG rates, STT, stamp duty, set-off rules | P6.3 |
---

## 7. Coverage matrix — master-research-summary.md against Stage 0 + Stage 1

Method: every `[RS §n]` citation in a Stage 0 or Stage 1 spec, mapped back to the section it cites.

| RS § | Section | Covered by |
|---|---|---|
| 1 | Executive Summary | — narrative, no requirement to cover |
| 2 | Problem Statement | — narrative |
| 3 | Project Objectives | — narrative |
| 4 | Autonomous Trading Agent Capabilities | P0.1, P1.3 |
| 5 | Agent Architecture | P0.1, P0.2 |
| 6 | End-to-End Workflow | P0.1 |
| 7 | System Architecture | P0.1 |
| 8 | Data Requirements | P0.1, P0.2 |
| 9 | AI/ML Models | **GAP — deferred to Stage 4 (P4.1–P4.4)** |
| 10 | Technology Stack | P0.1, P0.2 |
| 11 | Risk Management | P0.1 |
| 12 | Trading Execution | P0.1, P0.2, P1.1 |
| 13 | Backtesting and Validation | P0.1, P0.2, P0.3, P1.1, P1.2 |
| 14 | Monitoring and Observability | **GAP — deferred to P6.1** |
| 15 | Security | P0.1 |
| 16 | Compliance and Safety Considerations | P0.1, P0.2, P1.1, P1.2 |
| 17 | Architecture Diagram | — diagram |
| 18 | End-to-End Flow Diagram | — diagram |
| 19 | Decisions Already Made | P0.1 |
| 20 | Open Questions / Undecided Items | P0.1 |
| 21 | Missing Research | P0.1 |
| 22 | Recommended Next Steps | — process |
| 23 | Final Project Blueprint | P0.1 |

**15 of 23 sections carry a citation.** Of the eight that do not, six are narrative, process or
diagram sections with nothing to implement. **Two are real gaps, both deliberate and both
scheduled**: §9 AI/ML Models (Stage 4) and §14 Monitoring and Observability (P6.1). Neither
belongs in Stage 1's scope, and neither blocks Stage 2.

---

## 8. Status transition

The four Stage 1 specs move `DRAFT` → `FROZEN` on this record.

| Spec | Before | After |
|---|---|---|
| SPEC-P1.1-DOMAIN v0.3 | DRAFT | **FROZEN** |
| SPEC-P1.2-STORAGE v0.1 | DRAFT | **FROZEN** |
| SPEC-P1.3-CONFIG v0.1 | DRAFT | **FROZEN** |
| SPEC-P1.4-AUDIT v0.1 | DRAFT | **FROZEN** |

Freezing means what STAGE-0-FREEZE §1 says it means: the decisions are settled and may be
re-opened only on a documented trigger. It does **not** mean the specs are proven correct, and it
does not close the open questions in §6.

---

## 9. Stage 2 entry gate

| Gate | State |
|---|---|
| Stage 1 specs FROZEN | **YES**, by this record |
| Blocking open questions for **P2.1** | **NONE** |
| Blocking open questions for P2.2 | Q-P1.1-6 |
| Blocking open questions for P2.9 | Q-P1.1-1, Q-P1.1-2, Q-P1.3-3 |
| X5 GAP AUDIT | **NOT RUN** — required by the pack before Stage 2 |

**P2.1 may proceed once X5 has run.** This record satisfies X3 only.

---

## 10. Known defects carried across the freeze

| # | Severity | State |
|---|---|---|
| **B-5** | MEDIUM | **OPEN.** Every Python harness uses bare `assert`, so a `-O` run verifies almost nothing. Only `t_m2_allocate_postcondition_survives_dash_O` uses explicit raises |
| **C-1** | LOW | **OPEN.** `depends_on` version drift, §3 above |
| **C-2** | LOW | **OPEN.** Six contracts absent from P1.4's `produces:` header, §3 above |
| — | — | Three `column "…" should be used for segmenting or ordering` warnings from `news_item` / `llm_call` compression settings. Not investigated |

B-1, B-2, B-3 and B-4 were closed before this freeze and are recorded in the git history at
`c5cb2dd`, `2cecc36` and `8b24083`.

---

## DECISIONS MADE

| # | Decision | Rationale | Reversible? | Blast radius if wrong |
|---|---|---|---|---|
| 1 | Freeze by index and consolidation, not physical concatenation | A concatenated copy becomes a second source of truth that drifts; C-1 is a live instance of that failure | Yes | Low — regenerable from the specs |
| 2 | Freeze with C-1 and C-2 unresolved | X3 step 3 forbids silent resolution; both are documentary, and `verify_p11_p12_contract` shows 21 pairs ALIGNED | Yes | Low — no behavioural effect |
| 3 | Declare P2.1 unblocked while P2.2 and P2.9 carry named prerequisites | The four Stage-2 blockers name P2.2 and P2.9 explicitly; none names P2.1 | Yes | Medium — a missed dependency would surface as rework in P2.9 |
| 4 | Freeze before X5 rather than after | X3 and X5 are separate templates; the pack orders X3 then X5. The gate in §9 records that X5 is still required | Yes | Low |

## ASSUMPTIONS

| # | Assumption | Why I had to assume it | How to verify | Impact if false |
|---|---|---|---|---|
| 1 | The four Stage 1 specs each received an X2 review | X2 findings appear in P1.1 and P1.2 artifacts; P1.3 and P1.4 have verification harnesses but no separate review record | Search session history for an X2 run against P1.3 and P1.4 | Medium — an unreviewed code drop enters Stage 2 as a dependency |
| 2 | 2026-08-31 UTC is the correct freeze date | Shell UTC clock reads 2026-08-31; the session's local clock reads 2026-09-01 | Confirm the intended convention | None — labelling only |

## OPEN QUESTIONS

| # | Question | Who/what answers it | Exact query or doc to check | Blocks which phase |
|---|---|---|---|---|
| F-1 | Should C-1 and C-2 be fixed before Stage 2, or carried? | Owner | This record §3 | None directly; carrying them risks compounding drift |
| F-2 | Did P1.3 and P1.4 receive an X2 review? | Session history | Look for an X2 run naming SPEC-P1.3 / SPEC-P1.4 | P2.x quality, indirectly |
| F-3 | Close Q-P1.2-6's five runtime assertions now or at P6.4? | Owner | This record §6.2 | P6.4 |

## CONTRACTS EXPORTED

| Name | Kind | Signature or schema | Consumers |
|---|---|---|---|
| STAGE-1-FREEZE-RECORD | document | This file | All Stage 2+ phases |
| CONSOLIDATED-CONTRACTS-P1 | table | 118 rows, §4 | X5, all Stage 2 phases |
| CONSOLIDATED-ASSUMPTIONS-P1 | table | 32 rows, §5 | X4 RED TEAM, X5 |
| CONSOLIDATED-OPEN-QUESTIONS-P1 | table | 29 rows, §6 | X5, P2.2, P2.9, P6.4 |
| RS-COVERAGE-MATRIX-P1 | table | 23 rows, §7 | X5 GAP AUDIT |
| STAGE-2-ENTRY-GATE | gate | §9 | P2.1 |

---

---

## 11. Change log against the freeze

STAGE-0-FREEZE §8: *"A re-opening that does not produce a §9 entry has not happened. That is the
whole mechanism."* This section is that record for Stage 1.

| Date | Artifact | From → To | Trigger | Authority | Summary |
|---|---|---|---|---|---|
| 2026-09-01 | SPEC-P1.2-STORAGE + `migrations/0001_initial.sql` | v0.1 → **v0.2** | **T5** — a downstream verification proved the artifact did not do what it claimed | Phase author (§8, *"an additive rule that changes no decision"*) | **Finding B**: `verify_audit_chain()` gains the CONTENT check. **Finding A**: four false claims about `ENABLE ALWAYS` corrected. **No decision, number, table, constraint or grant changed** |
| 2026-09-01 | SPEC-P1.2-STORAGE + `migrations/0001_initial.sql` | v0.2 → **v0.3** | **T5** — a downstream verification proved the hash preimage was not deterministic | Phase author (§8, *"an additive rule that changes no decision"*) | **Finding C, first half**: `audit_chain_assign()` pins `TimeZone='UTC'`. **No existing hash invalidated** — the pin reproduces the UTC rendering byte for byte. **No decision, number, table, constraint or grant changed** |
| 2026-09-05 | SPEC-P1.2-STORAGE + `migrations/0001_initial.sql` | v0.4 → **v0.5** | **X2 BLOCKER-1 (second review)** — the independent X2 re-review proved the hash preimage did not cover the P1.4 §6.1 key set | Phase author (§8, *"an additive rule that changes no decision"*) | **Preimage conformance**: `event_id`, `is_paper` and `is_backtest` added to the preimage in **both** functions. All three are `audit_log` columns that SPEC-P1.4 §6.1 pins in the key set and none was hashed; an in-place edit of the paper/real-money flag passed verification. **THIS INVALIDATES EVERY HASH COMPUTED UNDER THE OLD PREIMAGE** — permissible only because §11.4's no-history finding still holds. **No decision, number, table, constraint or grant changed** |
| 2026-09-04 | SPEC-P1.2-STORAGE + `migrations/0001_initial.sql` | v0.3 → **v0.4** | **X2 BLOCKER-1** — the independent X2 review proved v0.3 closed only half of Finding C | Phase author (§8, *"an additive rule that changes no decision"*) | **Finding C, second half**: both functions additionally pin `DateStyle='ISO, MDY'`; `occurred_at::text` depends on DateStyle as well as TimeZone. **X2 BLOCKER-2**: a stale claim that the insert trigger does not pin the setting, contradicted by v0.3 itself, removed from migration and spec. **No existing hash invalidated** — verified byte-for-byte against three reference rows. **No decision, number, table, constraint or grant changed** |

### 11.1 Why this was re-opened

**Finding B — the verifier could not detect the tamper it exists to detect.**
`trading.verify_audit_chain()` checked SEQUENCE and LINKAGE but never recomputed
`payload_hash`. Measured 2026-09-01: an `UPDATE` setting `actor='tampered'` left the function
reporting `broken_rows = 0`.

This changes **no decision**. SPEC-P1.4 §6 already mandates all three checks, and §2 row 7 already
requires a structural-only scan to be *"documented as NOT catching content mutation, so nobody
mistakes the fast path for the real one"*. P1.2 §11.2 rule 3 makes `verify_audit_chain()` the gate
a migration aborts on — so it is not a fast path, and it must do check 3. The function was simply
non-conformant with an already-frozen decision. Bringing it into conformance is additive, which is
why the authority is Phase author and not Owner.

**Finding A — the DDL asserted something untrue.** `ENABLE ALWAYS` does not survive
`session_replication_role = 'replica'` on a hypertable: DML routes to chunks, chunk triggers are
ORIGIN, and TimescaleDB refuses to promote them (`operation not supported on chunk tables`).
Correcting a comment that states a falsehood changes no decision either.

### 11.2 Scope of the change

Strictly limited to those two items.

| Changed | Not changed |
|---|---|
| `verify_audit_chain()` — added CONTENT branch, `extensions` on search_path, `TimeZone='UTC'` | Any table, column, constraint, index, grant, role, policy or hypertable setting |
| Four false `ENABLE ALWAYS` claims (DDL comment ×2, §1553, edge-case row 14, DECISIONS row 10) | Any number, threshold or decision |
| Spec version 0.1 → 0.2 | The `ALTER TABLE … ENABLE ALWAYS` statements themselves — retained, and correct for the parent |

### 11.3 Findings left open by this change

Superseded in part by §11.4 and §11.5 below (taken 2026-09-01) and by §11.7 (2026-09-04).

| # | Severity | Status now |
|---|---|---|
| **A** | HIGH | **ACCEPTED as a documented architectural limitation** — Owner decision, §11.5. Not closed, not fixable in the current architecture. Detection covers **in-place mutation of every hashed column** (all 11 P1.4 §6.1 keys that have a column, since §11.8). It does **not** cover a fabricated *append* under replica role: the chain-assign trigger is skipped there too, so an attacker can choose `seq`, `prev_hash` and `payload_hash` and produce an internally consistent row. That residual is P1.4 §6.3's, and the anchor is its answer — still gated on Q-P1.4-1 |
| **C** | MEDIUM | **FIXED at v0.4, not at v0.3** — §11.4 (TimeZone) plus §11.7 (DateStyle). v0.3 pinned `TimeZone` only and this table then claimed C was fixed; X2 proved otherwise. `occurred_at::text` renders under **both** `TimeZone` and `DateStyle`, so half the defect survived with the same signature. Both GUCs are now pinned on both functions and the property is regression-tested in four directions (§11.7) |

### 11.4 Finding C — timezone-dependent hash preimage (2026-09-01)

**Why re-opened.** `payload_hash` was not a pure function of the row's logical content. The
preimage includes `occurred_at::text`, whose rendering depends on the session TimeZone, and
`audit_chain_assign()` pinned none. Measured on the pinned environment for the single instant
`2026-08-27 12:00:00+00`:

| Session TimeZone | Digest (first 16) |
|---|---|
| UTC | `5ceae9dc855d68d9` |
| Asia/Kolkata | `db99e8d94bdb40bb` |
| America/New_York | `36eacb365c5ae4f8` |

A row written under a non-UTC session would therefore verify as **CONTENT MUTATED** against any
other session — a false tamper alarm on a legitimate row, and, with Finding B's CONTENT check now
live, a false alarm that would actually fire.

**Classification.** A reproducibility defect in the DB-side preimage. It is *not* covered by the
frozen canonicalisation rule `jcs-nonum-1` (Q-P1.2-1), which governs the **application-supplied
payload** only; `occurred_at::text` is rendered by PostgreSQL and sat outside that rule.

**Why this changes no decision.** The frozen rule already intends a deterministic preimage. The
DB side simply did not conform. Bringing it into conformance is additive — hence Phase author
authority under §8, not Owner.

**Existing hashes: none invalidated.** The fix pins the function's TimeZone rather than rewriting
the expression. `(occurred_at AT TIME ZONE 'UTC')::text` would also be deterministic but renders
differently and would invalidate every `payload_hash` already computed — precisely what §11.2
rule 1 forbids. The pinned digest **is** the current UTC digest (`5ceae9dc855d68d9` in both), so
every hash written under the existing `TZ=UTC`/`PGTZ=UTC` container config remains valid.

**Deployment state, explicitly.** `0001_initial.sql` has never been deployed. There is no
`ansible/`, `terraform/`, `deploy/` or `infra/` tree; P6.4 (Deployment, CI/CD and Disaster
Recovery) has not been run; the only workflow is `ci-migration.yml`. The local database held 100
`audit_log` rows, all ephemeral `actor='b4'` fixtures rebuilt by `scripts/apply-migration.sh`.
**There is no production audit history to invalidate.** This is why the fix is taken now: after
deployment it would become a §11.2 rule 2 event — a new table plus a chain-linking event.

**Scope.** `SET TimeZone = 'UTC'` added to `audit_chain_assign()`, in the migration and in the
spec's §9.4 DDL block. The preimage expression itself is untouched. Nothing else changed.

### 11.5 Finding A — accepted as a documented architectural limitation (2026-09-01)

Owner decision, 2026-09-01: **`audit_log` remains a hypertable.** Finding A is accepted, not fixed.

| Dimension | Position |
|---|---|
| Prevention | **Unavailable.** `ALTER TABLE … ENABLE ALWAYS TRIGGER` on a chunk returns `operation not supported on chunk tables`. No supported mechanism exists |
| Detection | **Works**, since Finding B. Verified: a replica-role UPDATE reports `content mutated` |
| Mitigation | Unchanged and already frozen — off-VM WAL archive (§10.3), `log_statement='ddl'` to an off-VM sink, anchoring (P1.4 §6.3, gated on Q-P1.4-1) |
| Frozen decision violated? | **No.** P1.4 §6.5: *"Tamper-EVIDENT. Not tamper-proof… What this design guarantees is that a mutation cannot go unnoticed."* The guarantee is detection |

Worth recording plainly: **before Finding B was fixed the system did violate that guarantee** — a
content mutation genuinely could go unnoticed. Finding A alone never did, and accepting A does not
re-open the gap.

**Corrected 2026-09-05.** This paragraph previously read *"Finding B's CONTENT check is what
brought the system into conformance"*. That was **false when written**. Finding B's check covered
8 of the 13 `audit_log` columns and missed `is_paper`, `is_backtest`, `event_id` and
`recorded_at`; `recorded_at` is correctly excluded, the other three were not. Until §11.8 an
`UPDATE` flipping `is_paper` on an `ACTION` row still left `verify_audit_chain()` reporting zero
breaks, so P1.4 §6.5's *"a mutation cannot go unnoticed"* did not hold for the flag that
separates a paper order from a real-money one. **Conformance was reached at §11.8, not here** —
Finding B built the mechanism, §11.8 gave it the key set. This is the same defect class as
Finding A, in this record rather than in the DDL, and is corrected on the same reasoning.

The Finding A regression test (`verify_p12_runtime_behaviours.sh` check 7.1b) is **retained
unweakened**. It asserts the bypass still reproduces, so if prevention is ever fixed the test
fails loudly and Finding A must be revisited deliberately rather than by accident.

### 11.6 Re-freeze status

**NOT re-frozen.** SPEC-P1.2-STORAGE v0.4 still carries `status: FROZEN` from the 2026-08-31
freeze, but this drop has not completed the review the process requires.

The governing rule (PROMPT-PACK appendix): *"Every code drop goes through X2 in a separate
conversation. The author never reviews itself. A BLOCKER finding means the drop does not land."*
Findings B and C were fixed by the same author who found them, so **X2 in a fresh context is a
precondition**, not a formality.

**Status 2026-09-04.** X2 ran and returned **BLOCKER** — two of them, plus a proof that one
regression check was vacuous. All three were resolved (§11.7) and the corrections were verified
by deliberate sabotage.

**Status 2026-09-05.** X2 ran **again**, against the v0.4 drop, and returned **BLOCKER** once
more — one this time: the CONTENT check added for Finding B covered 8 of 13 `audit_log` columns
and did not cover the P1.4 §6.1 key set, so `is_paper`, `is_backtest` and `event_id` were
mutable undetected. Resolved at v0.5 (§11.8). That review also confirmed, by deliberate
sabotage, that the v0.4 corrections themselves hold: Findings A, B and C reproduce as recorded
and CONDITION 5 is met.

That review also recorded here that *"the runtime suite is discriminating in eight directions"*.
**That claim is withdrawn as a statement about the suite.** It was true of the eight sabotages it
actually referred to — all of them against the GUC pins and the presence of the CONTENT branch —
and it did not extend to the correction v0.5 had just made. The third X2 measured exactly that
gap. See §11.9.

**Status 2026-09-06.** X2 ran a **third** time, against the v0.5 drop, and returned **BLOCKER** —
one, **BLOCKER-A**: the `event_id`, `is_paper` and `is_backtest` terms v0.5 added to the preimage
had no regression coverage, so the correction could silently revert with every suite green. That
review re-confirmed the v0.5 code fix itself as correct on every measure it took. BLOCKER-A is
resolved at §11.9, which changes **no frozen artifact** — the fix is test coverage — so there is
no version bump and no §11 change-log row.

The §11.9 coverage is **again author-written**, so step 1 applies to it exactly as it applied to
v0.3, v0.4 and v0.5 — with particular force here, because the artifact being extended is the very
test file whose blind spot BLOCKER-A was. That is the state right now — corrected, verified by
sabotage, and **awaiting a fourth X2 re-review**. Nothing below step 1 has been started.

Required sequence before re-freeze:

1. **X2 RE-REVIEW** of the corrected uncommitted drop, in a separate conversation ← **current step**
2. Resolve any BLOCKER findings
3. **Commit**
4. **X3 re-run** — the consolidated contracts, contradictions and coverage in §3–§7 were built at
   `605ff40` and SPEC-P1.2 has since moved 0.1 → 0.4
5. **X5 re-run** — `STAGE-1-GAP-AUDIT` was taken at `605ff40`; conditions 1, 2, 5, 6 and 7 have
   since changed state
6. Create `DECISIONS.md` at the repo root — required by the PROMPT-PACK appendix, currently
   absent. It must **index** the existing records (SPEC-P0.1-DECISIONS's ADRs, STAGE-0-FREEZE §6,
   this §11), not duplicate them
7. Update these freeze records, then **re-freeze**

Only after that does P2.1 become available.

### 11.7 X2 review corrections — Finding C completed, and a vacuous check replaced (2026-09-04)

The independent X2 review of the v0.3 drop returned **BLOCKER**. Three items were actioned; the
remaining X2 findings (N-2 through N-11) were deliberately **left open** and are not touched here.

**BLOCKER-1 — Finding C was half-fixed.** `occurred_at::text` renders under `DateStyle` as well
as `TimeZone`. v0.3 pinned only the latter, so the identical defect survived with a different
GUC. With `TimeZone` already pinned to UTC, the single instant `2026-08-27 12:00:00+00` still
rendered four ways:

| DateStyle | Rendering |
|---|---|
| `ISO, MDY` | `2026-08-27 12:00:00+00` — what every hash to date was built on |
| `SQL, DMY` | `27/08/2026 12:00:00 UTC` |
| `Postgres, DMY` | `Thu 27 Aug 12:00:00 2026 UTC` |
| `German, DMY` | `27.08.2026 12:00:00 UTC` |

X2 demonstrated both failure directions on an untampered chain, using only libpq's
`PGDATESTYLE` and **no SQL statement at all** — the same exposure class as `PGTZ`:

- a legitimate row *written* under `PGDATESTYLE='German, DMY'` verified as **content mutated**;
- a legitimate chain *verified from* such a session reported **every row** mutated.

Because P1.2 §11.2 rule 3 makes `verify_audit_chain()` the gate a migration aborts on, that is a
spurious tamper alarm and an aborted migration on correct data.

**Fix.** `SET DateStyle = 'ISO, MDY'` added beside the existing `SET TimeZone = 'UTC'` on **both**
`audit_chain_assign()` (§9.4) and `verify_audit_chain()` (§9.5), in the migration and in the
spec's DDL blocks. **The preimage expression is untouched.**

**Existing hashes: none invalidated.** `ISO, MDY` is the PostgreSQL default and is what every
hash to date was computed under, so the pin reproduces the existing rendering byte for byte —
the same argument §11.4 makes for `TimeZone`, and the reason the pin is on the function rather
than on the expression. Verified rather than asserted: three reference rows spanning fractional
seconds, multiple event classes and multiple payload shapes hashed **byte-for-byte identically**
before and after the change (`092f7844…`, `a7f054e2…`, `c1f34f2e…`).

**BLOCKER-2 — a stale claim contradicted by v0.3 itself.** The §9.5 comment block asserted *"The
insert trigger does NOT pin it — see Finding C"*, which v0.3 had already falsified 80 lines
earlier by adding the pin to `audit_chain_assign()`. Removed from both the migration and the
spec, and replaced with a statement of the actual invariant: the two functions carry an identical
pair of pins and must, or every row reports as mutated. This is the same defect class as
Finding A — a comment stating a falsehood — and is corrected on the same reasoning.

**N-1 — the false-positive check was vacuous.** X2 proved that check 7.1e could not fail. It
asked for `count(*) … WHERE broken_at <> SEQ`, but `BASE = max(seq)+1` and the probe insert then
takes that seq, so `BASE == SEQ`, the scan range held exactly one row, and the filter excluded
it. The query counted an empty set. Demonstrated: with the CONTENT check **entirely deleted from
the verifier**, 7.1e still reported `PASS`. That absent coverage is why BLOCKER-1 went unnoticed
by the drop's own suite.

Replaced with a precision assertion over a **populated** range — six untampered rows alongside
the one tampered row — demanding that the CONTENT check name *exactly* the tampered row. It now
fails in both directions, each proven by deliberate sabotage:

| Sabotage applied | New 7.1e result |
|---|---|
| CONTENT check deleted from the verifier | **FAIL** — reported `NONE` over a range with a known tamper |
| Verifier preimage made to drift from the writer's | **FAIL** — reported `{0,1,2,3,4,5,6}`, expected `{0}` |

**Regression coverage added.** New section 7.8 in `verify_p12_runtime_behaviours.sh`, seven
checks covering all five properties X2 required, each confirmed discriminating by removing the
pin and observing the failure:

| Check | Proves | Fails when |
|---|---|---|
| 7.8a | both functions pin `DateStyle` | either pin removed (2 checks) |
| 7.8b | control: unpinned digests **differ** across DateStyles; pinned digests **match** | the control stops discriminating |
| 7.8c | rows written under 4 DateStyles — `ISO, MDY` as the benign control plus 3 hostile — verify clean | the **writer's** pin is removed → 3 false positives, one per hostile DateStyle |
| 7.8d | untampered chain verifies clean from 2 hostile *verifier* sessions | the **verifier's** pin is removed → 4 false positives each |

7.8d deliberately closes, for `DateStyle`, the blind spot X2 recorded as N-4 against the
`TimeZone` half: 7.7c cannot detect a missing verify-side pin because the container session is
already UTC, whereas 7.8d makes the calling session hostile on purpose. **N-4 itself is left open
for the `TimeZone` half** — it is outside the scope authorised for this correction.

**Scope.** Two `SET` clauses × two functions × two files; one stale comment removed from two
files; one test check replaced; one test section added; these freeze records. The preimage
expression, and every table, column, constraint, index, grant, role, policy and hypertable
setting, are untouched.

**Not re-frozen, and not reviewed.** These corrections were written by the author of the code
they correct. §11.6 step 1 applies to them exactly as it applied to v0.3.

### 11.8 X2 BLOCKER-1, second review — the preimage key set (2026-09-05)

The independent X2 re-review of the v0.4 drop returned **BLOCKER**, one finding. Findings A, B
and C were re-measured and held; CONDITION 5, the freeze procedure and the runtime suite passed.
The blocker was that **Finding B's CONTENT check was hashing the wrong key set.**

**The defect.** `trading.audit_log` has 13 columns. The preimage covered 8:
`prev_hash, seq, event_type, event_class, occurred_at, actor, run_id, payload`. It omitted
`event_id`, `is_paper`, `is_backtest` and `recorded_at`. `recorded_at` is correctly omitted —
P1.4 §6.1 requires its absence (`[DEFAULT-A2]`). The other three are not: **SPEC-P1.4 §6.1 pins
the preimage key set explicitly and names `is_paper` and `is_backtest` in it.**

Measured on the v0.4 drop, under `session_replication_role = 'replica'`:

| Mutation | `verify_audit_chain(0)` reported |
|---|---|
| `is_paper` true→false **and** `is_backtest` false→true on an `ACTION` row | **0 breaks** |
| `recorded_at` +400 days, `event_id` → `…deadbeef` | **0 breaks** |
| `actor` → `'tampered'` (control) | 1 — `content mutated` |

`is_paper` is the flag that separates a paper order from a real-money one. P1.4 §6.5's
*"a mutation cannot go unnoticed"* did not hold for it, and §11.5 nevertheless claimed
conformance had been restored. Both the code and that claim are corrected here.

**Why this changes no decision.** P1.4 §6.1 has pinned this key set since it was written. The
database preimage simply did not implement it. Bringing it into conformance is additive — hence
Phase author authority under §8, the same basis as Findings B and C.

**Fix.** `event_id::text`, `is_paper::text` and `is_backtest::text` appended to the preimage in
**both** `audit_chain_assign()` (§9.4) and `verify_audit_chain()` (§9.5), in the migration and in
the spec's DDL blocks. Every pre-existing field keeps its exact position and rendering;
`payload::text` stays last because it is the only unbounded field and its leading `{` anchors the
final boundary. Among themselves the three follow P1.4 §6.1's order.

The preimage now covers **11 of 11** P1.4 §6.1 keys that have an `audit_log` column. The four
that do not — `canonical_schema`, `schema_version`, `causation_id`, `input_hash` — have no column
to hash and are recorded as **Q-P1.2-7** below, not silently absorbed.

**Existing hashes: EVERY ONE IS INVALIDATED.** This is the one place this record must not repeat
the argument §11.4 and §11.7 made. Those fixes pinned a GUC and reproduced the previous rendering
byte for byte. **This one does not, and cannot:** adding a field to a digest changes it. Measured
on three reference rows — old-preimage digest vs stored digest: `8b1ded46…`/`d940baf4…`,
`faf5d35f…`/`9b1a0fc4…`, `14946aad…`/`b0cd27e7…`, **none equal**.

It is permissible only because §11.4's deployment finding still holds, re-verified 2026-09-05:
no `ansible/`, `terraform/`, `deploy/` or `infra/` tree exists; the only workflow is
`ci-migration.yml`, which tears its database down; `scripts/apply-migration.sh` drops and
recreates the database on every run; and the only `audit_log` rows anywhere are ephemeral
fixtures. **There is no production audit history to invalidate.** After deployment this would be
a §11.2 rule 2 event — a new table plus a chain-linking event — and not available as an edit.
That is precisely why it is taken now.

**One regression introduced and caught during this correction.** The first draft of the §9.4
comment contained the literal words `TimeZone` and `DateStyle` inside the function body. Checks
7.7a and 7.8a guard the pins with `pg_get_functiondef(...) ~* 'TimeZone'`, which matches comment
prose as readily as a `SET` clause — so the writer-side pin guards went vacuous, and sabotage S5
dropped from 4 failures to 3, S6 from 2 to 1. Demonstrated: with the `SET DateStyle` clause
removed, `proconfig` read `search_path=… | TimeZone=UTC` while the grep guard still answered
`true`. The comment was reworded and both guards restored to 4 and 2. **The underlying fragility
is not fixed and is recorded as a finding for the harness author:** these two checks should read
`pg_proc.proconfig`, not the function text. Left open deliberately — the test file is outside the
scope authorised for this correction. **Still open after §11.9**, which does extend that file but
only for BLOCKER-A; 7.7a and 7.8a are untouched. §11.9's own new check 7.1h is written the way
this finding says these two should be — comments stripped before the text is read — but it guards
the preimage key set, not the GUC pins, so it does not close this.

**Scope.** Three fields × two functions × two files; one comment block added to each function in
each file; §11.3 and §11.5's conformance claims corrected; this section; the §11 change-log row;
the spec version bump; **Q-P1.2-7** opened. The preimage's pre-existing field order, and every
table, column, constraint, index, grant, role, policy and hypertable setting, are untouched.

**Deliberately NOT fixed here.** The second X2 raised eight non-blocking findings. None is
required for this blocker and none is touched: N-1 (the M-1 lines that entered §9.5 undeclared),
N-2 (§9.4's DDL still omits the H-1 `READ COMMITTED` guard the migration carries), N-3 (no CI runs
the regression suites), N-4 (this record's own `version:` and `depends_on:`), N-5 (the §2 hash
table), N-6, N-7, N-8. They remain open for the governed sequence.

**Not re-frozen, and not reviewed.** Written by the author of the code it corrects. §11.6 step 1
applies.

### 11.9 X2 BLOCKER-A, third review — regression coverage for the v0.5 preimage (2026-09-06)

The independent X2 re-review of the v0.5 drop returned **BLOCKER**, one finding. The v0.5 *code*
was re-measured and held on every dimension: writer and verifier preimages byte-identical, all 11
P1.4 §6.1 keys that have an `audit_log` column covered, `recorded_at` absent, digests identical
across nine `DateStyle` × `TimeZone` combinations, and each of the three added columns detected on
mutation. The blocker was that **none of it was tested.**

**The defect.** Checks 7.1c, 7.1d and 7.1e drive the CONTENT check through a single `actor`
mutation, and `actor` was already hashed before v0.5. Nothing anywhere mutated `event_id`,
`is_paper` or `is_backtest`. Measured by that review: with all three terms deleted from the
preimage in **both** `audit_chain_assign()` and `verify_audit_chain()` — in the migration, with
the database rebuilt from it — every one of the nine suites exited 0, `verify_p12_runtime_behaviours`
included at 28/28, while an `UPDATE` flipping `is_paper` on an `ACTION` row reported 0 breaks. The
correction that closed the previous BLOCKER-1 could be reverted and nothing would say so.

**Why this is a blocker rather than a finding.** §11.7 closed the previous X2 BLOCKER by adding a
new §7.8 with seven checks and recorded it here as *"Regression coverage added."* §11.8 closed a
blocker of the same class and added none, on a scope this record set for itself. That is the
standard being applied inconsistently to two consecutive corrections of the same expression, and
it is the second time a defect in that expression survived a fully green suite.

**Fix — three new check groups in `tests/verify_p12_runtime_behaviours.sh`, §7.1.** No frozen
artifact is touched.

- **7.1f — one mutation probe per hashed column.** `is_paper`, `is_backtest`, `event_id`, and
  `actor` through the identical harness as a like-for-like control. Each probe gets its **own row
  and its own scan range**: a shared row would let any one still-covered column mask the loss of
  another, because a single `UPDATE` touching all three is detected as long as one of them is
  hashed. Each also carries two untampered rows in range, so it fails in the false-positive
  direction too. Each reads the column back after the `UPDATE` and reports "the mutation did not
  land, see 7.1b" rather than "not detected" if the replica bypass ever closes — the two have
  opposite meanings.
- **7.1g — the negative probe, plus its own control.** `recorded_at` must **not** be reported.
  `[DEFAULT-A2]` keeps it out of the preimage because hashing when we wrote a row down means a
  replayed write can never reproduce the hash, which kills the replay tool (P1.4 §6.4). A
  correction that over-reaches and hashes "every column" would pass all of 7.1f. Because a
  negative assertion also passes with the CONTENT branch deleted entirely, the probe is followed
  by a mutation of `actor` **on the same row in the same range**, which must be reported. Only
  then does "recorded_at was not reported" mean it is excluded rather than that nothing was
  checked.
- **7.1h — mechanical key-set conformance from the catalogue.** The digest expression is read back
  out of `pg_get_functiondef()`, **SQL comments stripped first** so the N-9 trap cannot apply,
  split on `||` and reduced to a field list. Two assertions: writer and verifier must produce the
  same *ordered* term list, and the field *set* must be exactly the 11 P1.4 §6.1 keys that have a
  column. Set equality, so it fails on an omission and on an addition alike.

The suite goes from 28 checks to 36.

**Discrimination, measured.** Every sabotage removes the field from **both** functions, so writer
and verifier stay in agreement and nothing can fail merely because they diverged. Before this
change all four rows below were green.

| Sabotage (removed from BOTH functions) | Runtime suite | Which checks failed |
|---|---|---|
| **A1** `is_paper` | **exit 1** — 34 passed, 2 failed | 7.1f `is_paper`, 7.1h key set |
| **A2** `is_backtest` | **exit 1** — 34 passed, 2 failed | 7.1f `is_backtest`, 7.1h key set |
| **A3** `event_id` | **exit 1** — 34 passed, 2 failed | 7.1f `event_id`, 7.1h key set |
| **A4** all three | **exit 1** — 32 passed, 4 failed | 7.1f ×3, 7.1h key set |
| **A4 end-to-end** — the same three deleted from `0001_initial.sql`, database rebuilt from it | **exit 1** — 32 passed, 4 failed | 7.1f ×3, 7.1h key set |

In **all five**, 7.1e and 7.1h's writer/verifier-agreement check still passed. The failures are
attributable to the field being absent, not to the two functions disagreeing — which is the whole
point, and the reason a verifier-only sabotage would have proved nothing.

The A4 end-to-end run also re-reproduced the original defect against the sabotaged build:
`is_paper`, `is_backtest`, `event_id` and all three together each reported **0 breaks**, with
`actor` reporting 1. That is BLOCKER-1 exactly as first measured — and it is now accompanied by a
red suite instead of a green one.

**The six Python suites stay green under every sabotage above, and that is correct, not a gap.**
They exercise `src/audit/chain.py`'s own preimage, which is a different implementation over a
different key set and never reaches the database. That the two disagree is **Q-P1.2-7**, untouched
here.

**Scope.** One file — `tests/verify_p12_runtime_behaviours.sh` — plus this section and the two
corrections in §11.6 and §11.8 that describe it. **No frozen artifact changed**: not the
migration, not SPEC-P1.2, not a table, column, constraint, index, grant, role, policy or
hypertable setting, and not the preimage itself. There is therefore **no version bump and no §11
change-log row** — the change-log table records changes to frozen artifacts, and this is test
coverage for a change already recorded at §11.8.

**Two documentation corrections, both caused directly by this change and limited to it.** §11.6's
*"the runtime suite is discriminating in eight directions"* is withdrawn as a statement about the
suite — it was true of the eight sabotages it referred to and did not extend to v0.5's own fix.
§11.8's *"the test file is outside the scope authorised for this correction"* now carries a
pointer here, because that file has been extended — for BLOCKER-A only.

**Deliberately NOT fixed here.** N-1, N-2, N-3, N-4, N-5, N-6, N-7, N-8, **N-9** and **Q-P1.2-7**
are all untouched and all remain open. N-9 in particular: 7.7a and 7.8a still read the raw
function text and are still satisfiable by comment prose. The new 7.1h is written the way N-9 says
those two should be, but it guards the preimage key set, not the GUC pins, so it does not close
them.

**Not re-frozen, and not reviewed.** Written by the author of the code it covers, and the artifact
added is the very test file whose blind spot BLOCKER-A was — so §11.6 step 1 applies with more
force here, not less. Nothing has been committed, staged or pushed.
