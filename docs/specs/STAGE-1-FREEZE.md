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
test file whose blind spot BLOCKER-A was. That was the state on 2026-09-06 — corrected, verified by
sabotage, and **awaiting a fourth X2 re-review**.

**Corrected 2026-10-01.** This paragraph previously ended *"That is the state right now … Nothing
below step 1 has been started"*, and step 1 below read *"the corrected uncommitted drop"*. Both
were false from 2026-09-10. §11.10 is the full record; the entries below are pointers to it.

**Status 2026-09-10 — PROCESS DEVIATION.** The drop was committed to `main` and pushed as
`c9f30e3` before the fourth X2 had run. Step 3 happened ahead of steps 1 and 2.

**Status 2026-09-29.** X2 ran a **fourth** time and returned **BLOCKER** — one, **BLOCKER-P1**:
the deviation above, and this record stating the opposite. It ran no database test, suite or
sabotage, so it returned **no PASS** on the drop's content.

**Status 2026-09-30.** The Owner ran a dynamic regression and reported it the same day: every
suite that was run passed. It is Owner-reported evidence, not an X2 verdict, and is kept separate
from the reviewer's in §11.10.

**Status 2026-10-01 — Owner decision.** BLOCKER-P1 is resolved by keeping `c9f30e3` and recording
the deviation. That is **not** an X2 PASS and re-freezes nothing.

**Status 2026-10-02.** The fourth X2 was completed. Its reviewer ran the dynamic half that could
not run on 2026-09-29 — the full regression in both Python modes, the BLOCKER-1 reproduction and
twelve sabotages — against an isolated copy of `c9f30e3`. **It found no blocker in the technical
drop.** One sabotage went undetected, which is N-9 demonstrated. The results, and the limits of
that review's independence, are at §11.12.

**Status 2026-10-02 — Owner decision.** The Owner accepted the fourth X2's verdict as the formal
X2 PASS for the technical drop, with the independence limits and the N-9 finding as documented
at §11.12. **That acceptance does not close Stage 1 and does not re-freeze anything.**

**Status 2026-10-02 — Owner decision.** X3 and X5 are to be re-run **each in its own
conversation**, as the pack requires of its cross-cutting templates: *"Use these repeatedly, in
their own conversations."* A delta that the X2 reviewer prepared for each in the X2 session is
**not accepted** as the re-run and is not evidence in this record.

**Corrected 2026-10-05.** The paragraph above previously ended *"Neither re-run has been made."*
True when written; both have since been made, each in its own conversation: X3 on 2026-10-02 at
`b8b1340` (§12), and X5 on 2026-10-02 at `3cd91a0` (§13).

Required sequence before re-freeze:

1. **X2 RE-REVIEW** of the corrected drop — now `c9f30e3`, no longer uncommitted. The fourth X2
   returned its verdict on 2026-10-02: no blocker (§11.12). **Accepted by the Owner as the X2
   PASS on 2026-10-02**
2. Resolve any BLOCKER findings
3. **Commit** — happened out of order on 2026-09-10 (§11.10). Anything further arising from
   steps 1–2 is committed only after X2 passes
4. **X3 re-run** — **made 2026-10-02**, in its own conversation, at `b8b1340` (§12)
5. **X5 re-run** — **made 2026-10-02**, in its own conversation, at `3cd91a0` (§13). Verdict:
   **GO WITH CONDITIONS**. Recorded in `STAGE-1-GAP-AUDIT.md`, sections 6 to 10
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
force here, not less.

**Corrected 2026-10-01.** This section previously ended *"Nothing has been committed, staged or
pushed."* True when written on 2026-09-06; false from 2026-09-10. See §11.10.

### 11.10 Process deviation — the drop landed on `main` before X2 passed (recorded 2026-10-01)

**What happened.** On 2026-09-10 the whole working-tree drop was committed to `main` as one
commit and pushed to `origin/main` the same day.

| Field | Value |
|---|---|
| Commit | `c9f30e3ba9b7d89d3fdfc764e9bb6e8b2cd88d82` |
| Message | *"Backup latest local work before laptop migration"* |
| Parent | `c8225ed` (*"Close X5 conditions 1, 2 and 6"*, 2026-09-01) |
| Commit timestamp | 2026-09-10 19:18:25 +05:30 |
| Evidence of the push | `origin/main` is this commit; CI ran on it as a `push` event, 2026-09-10 13:47 UTC |
| Size | 8 files — 7 modified, 1 added — 1,738 insertions, 240 deletions |

**What it contained.** Checked against `git diff c8225ed c9f30e3`. The commit message names none
of it.

| Content | Recorded at | Files |
|---|---|---|
| SPEC-P1.2 v0.1 → v0.2 — Findings A and B | change log, §11.1, §11.2 | `migrations/0001_initial.sql`, `SPEC-P1.2-STORAGE.md` |
| v0.2 → v0.3 — Finding C, `TimeZone` pin | change log, §11.4 | same two |
| v0.3 → v0.4 — X2 BLOCKER-1 (`DateStyle` pin), BLOCKER-2 | change log, §11.7 | same two; checks 7.1e and 7.8 of the runtime suite |
| v0.4 → v0.5 — X2 BLOCKER-1, second review (preimage key set) | change log, §11.8 | same two |
| X2 BLOCKER-A — coverage for v0.5 | §11.9 | checks 7.1f–7.1h of the runtime suite |
| `tests/verify_p12_runtime_behaviours.sh` **as a new file** — 570 lines, sections 7.1–7.8 | **No entry records its creation**, nor sections 7.2–7.7. `STAGE-1-GAP-AUDIT` still lists condition 7 as OPEN | the file itself |
| Four Python harnesses moved off bare `assert` (X5 CONDITION 5) | **No entry.** §11.6 says only *"CONDITION 5 is met"*. `STAGE-1-GAP-AUDIT` still lists it as PARTIAL | `verify_p11_invariants.py`, `verify_p11_x2_regressions.py`, `verify_p13_config.py`, `verify_p14_audit.py` |
| The M-1 duplicate-`seq` lines entering SPEC §9.5 | **Undeclared** — already open as N-1 (§11.8) | `SPEC-P1.2-STORAGE.md` |
| This record's §11 | — | `STAGE-1-FREEZE.md` |

So: five changes this record governs, and three it does not record. The harness change removed
every bare `assert` statement (56, 37, 56 and 61 before; none after) and left the test-function
counts unchanged at 42, 21, 39 and 36. It was not read line by line for this entry.

**Rules broken.** PROMPT-PACK appendix — *"Every code drop goes through X2 in a separate
conversation. A BLOCKER finding means the drop does not land"* — and step 3 of §11.6. On
2026-09-10 the latest verdict was the third X2's BLOCKER, and the fourth had not run.

**Owner decision, 2026-10-01.** The commit is **kept** and the deviation **recorded**. It is not
reverted and history is not rewritten: a revert would put the v0.1 migration — Findings B and C
unfixed — back on `main` without removing `c9f30e3` from the published history.

**Evidence on the content of `c9f30e3`, by who produced it.**

| Source | Performed | Reported | What it covers | What it does not |
|---|---|---|---|---|
| **Reviewer** — fourth X2, static | 2026-09-29 | 2026-09-29, 11:38 UTC | Writer and verifier preimages extracted from the migration source are identical; they cover exactly the 11 P1.4 §6.1 keys that have an `audit_log` column; `recorded_at` is absent | No database test, no suite, no sabotage run |
| **CI** — `ci-migration.yml` on `c9f30e3` | 2026-09-10, 13:47 UTC | — | The migration applies on the pinned image | Runs no regression suite (N-3) |
| **Owner-reported** — dynamic run. **Not re-run or verified by the reviewer** | 2026-09-30 — supported by the traces described below | 2026-09-30, 15:58 UTC | See below | See below |
| **Reviewer** — fourth X2, dynamic. A separate run from the Owner's, in an isolated copy | 2026-10-01 and 2026-10-02 | 2026-10-02 | Full regression in both modes, BLOCKER-1 reproduction, twelve sabotages — §11.12 | Not the development database; not a second reviewer |

Owner-reported results, as reported:

| Suite | Normal | `python -O` |
|---|---|---|
| `verify_p11_x2_regressions.py` | 21/21 | 21/21 |
| `verify_p11_x5_conditions.py` | 12/12 | passed, no count given |
| `verify_p13_config.py` | 39/39 | not reported |
| `verify_p14_audit.py` | 36/36 | 36/36 |
| `verify_p11_invariants.py` | passed, no count given | not reported |
| `verify_p11_p12_contract.py` | passed | passed |
| `verify_p12_runtime_behaviours.sh` | 36/36 | n/a |
| `verify_p12_migration_rerun.sh` | 6/6 | n/a |
| `verify_p12_cagg_immutability.sh` | **not run** — skipped by Owner decision | n/a |

*"Not reported"* and *"no count given"* mean the Owner's report carried no figure. No log, saved
output or shell history of the run exists on the review host, so nothing was filled in.

The date the run was **performed** is supported by two traces the reviewer could observe, both
dated 2026-09-30. Bytecode caches — `.pyc`, and `.opt-1.pyc` from `-O` — for `src/domain`,
`src/audit` and `src/config` were written between 17:17 and 21:15 +05:30. The development
database's log shows deny-trigger rejections at 15:40 UTC, and that database was last recreated
at 15:51 UTC. Together they show that suites ran that day, in both Python modes and against the
database. They show no pass count, and cannot say which suite ran under `-O`, because every `-O`
cache is shared by a suite that was reported.

The same run observed Finding A still open, as check 7.1b pins it (§11.11). The Owner's run
included no sabotage. The reviewer's later run did; it is recorded separately at §11.12.

**What this entry changes, and what it does not.**

- It edits **this freeze record only**. `STAGE-1-FREEZE.md` is `status: ACTIVE` and is not one of
  the ten artifacts §2 lists as frozen. **None of those ten is changed by this entry**, so there
  is no version bump and no change-log row. (`c9f30e3` itself *did* change two of them —
  `SPEC-P1.2-STORAGE.md` and `migrations/0001_initial.sql` — which is what the change-log rows at
  the top of §11 record.) This record's own `version:` is left at 1.0; that is N-4.
- It is **not** an X2 verdict. The fourth X2's verdict is recorded separately at §11.12.
- It does **not** re-establish the freeze. SPEC-P1.2-STORAGE remains **NOT re-frozen**.

**Still open.** Rechecked against `c9f30e3` on 2026-10-01, in the numbering of the second and
third X2 (§11.8, §11.9): **N-1, N-2, N-3, N-4, N-5, N-6, N-7, N-8, N-9 and Q-P1.2-7 — all still
open, none changed.** The first X2's separate series (§11.7, *"N-2 through N-11"*) is not
itemised in this record and was **not rechecked**; it stands as §11.7 left it.

The fourth X2 returned **BLOCKER**, not PASS. Besides BLOCKER-P1 its report carried four new
non-blocking labels, N-10 to N-13, and added to existing findings in two places. All six are
listed so that this record does not understate that review. They are prefixed here because those
labels collide with the first X2's series. None is addressed by this entry.

- **X2-4/a** (its N-10) — stale text. SPEC-P1.2: the footer still reads *"v0.1"*; §6.11 and the
  Q-P1.2-6 row still say the DDL is unexecuted and that `ENABLE ALWAYS` fires; the Q-P1.2-1 row is
  contradicted by Q-P1.2-7. §11.6 of this record still says *"v0.4 still carries
  `status: FROZEN`"*.
- **X2-4/b** (its N-11) — `§11.x` references inside SPEC-P1.2 and the migration point at this
  record, not at SPEC-P1.2's own §11; the change-log rows are out of date order.
- **X2-4/c** (its N-12) — `STAGE-1-GAP-AUDIT` still lists condition 5 as PARTIAL.
- **X2-4/d** (its N-13) — a note, not a defect in an artifact: the brief given to that review
  described the v0.5 state, while the artifact was already at the post-§11.9 state.
- **X2-4/e** (added under its N-5) — the §2 hashes were taken over CRLF working-tree bytes, not
  git blobs, so they do not reproduce on another platform.
- **X2-4/f** (added under its N-4 and N-9) — the verifier's `TimeZone` pin is caught only by
  check 7.7a's text match, because the test session is already UTC.

One further item was found on 2026-10-01 while this entry was prepared, and is **not** a
fourth-X2 finding: `STAGE-1-GAP-AUDIT` still lists condition 7 as OPEN although the suite
exercising those assertions now exists. It belongs to the X5 re-run.

### 11.11 Finding A — a remediation is proposed; it is deferred, not approved, not implemented

**This section is separate from §11.10.** §11.10 corrects the record of a process deviation,
under the Owner's decision of 2026-10-01. This section records where a different matter stands.

**Finding A is OPEN.** §11.5's Owner decision — accepted as a documented limitation — is the
decision in force. **Remediation E is not approved and not implemented.** The Owner's acceptance
of the scratch-validation results below is not approval of the plan and does not close
Finding A.

**What was measured.** By the reviewer, performed 2026-10-01 between 06:49 and 06:51 UTC and
documented here the same day, in a throwaway container from the pinned image (TimescaleDB 2.29.2,
PG16) that was destroyed afterwards. Neither the repository nor the development database was
touched. The container left no artifact; the times are from the review session's transcript.

- `ALTER TABLE trading.audit_log ENABLE ALWAYS TRIGGER …`, re-issued on the hypertable **after**
  chunks exist, moved the chunk triggers from `O` to `A`. Under `session_replication_role =
  'replica'`, `UPDATE`, `DELETE` and `TRUNCATE` were then rejected and a forged insert was
  re-assigned its `seq` and hashes.
- Chunks created afterwards start at `O` again. The migration's own `ALTER` runs when no chunk
  exists, which is why it protects nothing.

So §11.3 row A (*"not fixable in the current architecture"*), §11.5 (*"Prevention: Unavailable …
No supported mechanism exists"*) and the migration comment (*"CANNOT BE MADE TO"*) overstate the
position. **They are left as written.** Correcting them belongs to whatever the Owner decides
below, not to this entry.

**What is proposed — "Remediation E".** Three statement-level `ENABLE ALWAYS` guards on the
parent table and a scheduled job that re-issues the `ALTER`. The hypertable, compression,
continuous aggregate, primary key and preimage are unchanged. A residual window remains: direct
DML on a new chunk's own table, under replica role, until the job next runs.

| | State on 2026-10-02 |
|---|---|
| Plan | Written by the reviewer and given to the Owner |
| Scratch validations | Two, performed by the reviewer on 2026-10-01 between 07:16 and 07:19 UTC in a second throwaway container: the tamper mechanism the tests would use, and concurrent inserts while the job runs. The Owner **accepted these two results as complete** on 2026-10-01, 07:27 UTC. That is acceptance of test results. It is **not** approval of the plan and **not** closure of Finding A |
| Owner decision on Remediation E | **Deferred, 2026-10-02.** The Owner directed that it may stay deferred because the Stage 2 entry gate does not require it. It is **neither approved nor rejected**. Left undecided for whenever it is taken up: the job interval; whether the residual window is acceptable; whether losing logical replication of `audit_log` is acceptable |
| Implementation | **None.** No migration, specification or test has been changed, and no object exists in any database |
| Review | None. If approved and implemented it is a new drop, and §11.6 step 1 applies to it |

### 11.12 Fourth X2, completed — dynamic results and verdict (2026-10-02)

**What this is.** The second half of the fourth X2. The first half (2026-09-29) was static only,
because the review host then had no runtime. This half ran everything that review's brief
required and the first half could not.

**Independence, stated plainly.**

- The reviewer wrote no part of `c9f30e3`: not the migration, not SPEC-P1.2, not a test.
- It is the same reviewer, in a continuation of the same conversation, as the 2026-09-29 half.
  It is not a fifth, fresh review.
- That reviewer **did** write §11.10, §11.11, this section and the notice at §12 of this record,
  and designed Remediation E. None of those is covered by the verdict below. The Owner read this
  record's text and approved it on 2026-10-02; nobody independent of its author has reviewed it.
- Whether this satisfies §11.6 step 1 was the Owner's decision, not the reviewer's. The Owner
  accepted it on 2026-10-02, with these limits stated.

**Where it ran.** A copy exported from `c9f30e3`, outside the repository: 38 of 40 tracked files
byte-identical, `docker-compose.yml` differing only in container and volume name, and one
research note differing only in line endings. Its own database container from the pinned image
(TimescaleDB 2.29.2, PG16), rebuilt from the migration before every sabotage. Python 3.11.9,
pydantic 2.13.5. The repository and the development database were not touched. The logs are in
the reviewer's session scratch folder and are **not** in this repository.

**Baseline — every suite, both modes.**

| Command | Exit | Result |
|---|---|---|
| `bash scripts/apply-migration.sh` | 0 | 37 tables, 8 hypertables, 3 continuous aggregates, 27 triggers |
| `bash tests/verify_p12_migration_rerun.sh` | 0 | 6 passed, 0 failed |
| `bash tests/verify_p12_cagg_immutability.sh` | 0 | 6 passed, 0 failed |
| `bash tests/verify_p12_runtime_behaviours.sh` | 0 | 36 passed, 0 failed |
| `python tests/verify_p11_invariants.py`, and with `-O` | 0, 0 | 42 passed; 42 passed |
| `python tests/verify_p11_p12_contract.py`, and with `-O` | 0, 0 | ALIGNED; ALIGNED |
| `python tests/verify_p11_x2_regressions.py`, and with `-O` | 0, 0 | 21 passed; 21 passed |
| `python tests/verify_p11_x5_conditions.py`, and with `-O` | 0, 0 | 12 passed; 12 passed |
| `python tests/verify_p13_config.py`, and with `-O` | 0, 0 | 39 passed; 39 passed |
| `python tests/verify_p14_audit.py`, and with `-O` | 0, 0 | 36 passed; 36 passed |

**BLOCKER-1, reproduced independently.** A fresh database from the migration; one `ACTION` row
per probe with `is_paper = true`, `is_backtest = false` and two untampered neighbours; mutated
under `session_replication_role = 'replica'`; then `verify_audit_chain()` over that range.

| Mutation | Reported |
|---|---|
| `is_paper` true → false | that row, `content mutated` |
| `is_paper` → false and `is_backtest` → true | that row, `content mutated` |
| `event_id` changed | that row, `content mutated` |
| all three together | that row, `content mutated` |
| `actor` (control) | that row, `content mutated` |
| `recorded_at` + 400 days | nothing — correct, it is outside the preimage |

In every case only the mutated row was reported. `is_backtest` was not mutated on its own.

**Conformance, read from the database.** The preimage expressions taken from
`pg_get_functiondef()` for both functions, comments stripped, are identical:
`prev_hash, seq, event_type, event_class, occurred_at, actor, run_id, event_id, is_paper,
is_backtest, payload`. `pg_proc.proconfig` carries `TimeZone=UTC` and `DateStyle=ISO, MDY` on
both.

**Sabotage.** Each was applied to the functions in the isolated database, then the 36-check
runtime suite was run.

| # | Sabotage | Suite | Detected by |
|---|---|---|---|
| S1 | CONTENT branch removed from the verifier | exit 1 — 27 passed, 9 failed | 7.1c, 7.1d, 7.1e, 7.1f ×4, 7.1g control, 7.1h |
| S2 | `actor` removed from the verifier's preimage | exit 1 — 24 passed, 12 failed | 7.1e, 7.1f ×4, 7.1g ×2, 7.1h, 7.7c, 7.8c, 7.8d ×2 |
| S3 | `is_paper` removed from the verifier only | exit 1 — 24 passed, 12 failed | the same twelve |
| S3b | `is_paper` removed from **both** functions | exit 1 — 34 passed, 2 failed | 7.1f `is_paper`, 7.1h key set |
| S4v | verifier's `DateStyle` pin removed | exit 1 — 33 passed, 3 failed | 7.8a, 7.8d ×2 |
| S4w | writer's `DateStyle` pin removed | exit 1 — 32 passed, 4 failed | 7.8a, 7.8c, 7.8d ×2 |
| S5v | verifier's `TimeZone` pin removed | exit 1 — 35 passed, 1 failed | **7.7a only** — a match on the function's text |
| S5w | writer's `TimeZone` pin removed | exit 1 — 34 passed, 2 failed | 7.7a, 7.7c |
| S6 | both writer pins removed | exit 1 — 30 passed, 6 failed | 7.7a, 7.7c, 7.8a, 7.8c, 7.8d ×2 |
| S7 | CONTENT comparison made dead code, `digest(` left in the text | exit 1 — 29 passed, 7 failed | 7.1c, 7.1e, 7.1f ×4, 7.1g control. 7.1d passed, as a text match must |
| **S8** | verifier's `TimeZone` pin removed **and** a comment containing the word `TimeZone` added to its body | **exit 0 — 36 passed, 0 failed** | **Not detected** |
| S9 | CONTENT comparison disabled in `src/audit/chain.py` | `verify_p14_audit.py` exit 1 in both modes — 34 passed, 2 failed | the two content-mutation tests, under `-O` as well |

After the last sabotage the database was rebuilt from the migration and the runtime suite re-run:
36 passed, 0 failed.

**Findings.**

- **No BLOCKER** in the technical drop. BLOCKER-1 is fixed, and the fix is covered by tests that
  fail when it is reverted (S3b).
- **N-9 is demonstrated, not merely argued (S8).** Checks 7.7a and 7.8a match the function's
  text. S5v shows the verifier's `TimeZone` pin has no other guard, and S8 shows that guard is
  satisfied by a comment. It stays non-blocking for the reason every earlier review gave: the
  result of a missing verifier pin is a false tamper alarm from a non-UTC session — loud, and
  fail-closed — not a tamper that goes unseen. It should be fixed before those two functions are
  next changed: read `pg_proc.proconfig`, and add a verifier-side check from a non-UTC session.
- N-1 to N-8 and Q-P1.2-7 are as §11.10 left them.

**Verdict on the technical content of `c9f30e3`: no blocker — in the pack's wording, SHIP.**
This is a verdict on the drop. It is not a re-freeze. Under "Independence" above it became the
X2 PASS of §11.6 step 1 only by the Owner's acceptance, given on 2026-10-02. That acceptance
does not close Stage 1.

---

## 12. X3 re-run — 2026-10-02

**Run at:** 2026-10-02 · **HEAD:** `b8b1340` · **Template:** X3 — MERGE, all seven steps, in its
own conversation, as §11.6 step 4 requires.

**This section re-freezes nothing and changes no status.** It was produced read-only: no file in
this repository was edited by the re-run. Whether it is adopted is the Owner's decision.

**Independence.** Every count and finding below was derived from the four specs, the code and the
git history at `b8b1340`. The delta that the fourth X2's reviewer prepared on 2026-10-02 was not
opened. Finding ids use the prefix `X3R-` because this record already has two colliding `N-`
series.

**Form.** A **full re-merge**, not a delta against §3 to §7. The baseline was checked first and
was wrong in places the SPEC-P1.2 change does not touch (X3R-E1, E2, E3 below), so a delta would
have carried those errors forward. The merge is again by index, not concatenation; §1's deviation
stands.

**§3 to §7 above are superseded by this section where they differ. They are left as written.**

### 12.1 What was and was not verified

| Verified by this re-run | Not verified by this re-run |
|---|---|
| The four standard tables of all four specs, re-extracted | Any database behaviour. No container was started and the development database was not touched |
| Contracts against `src/` and the migration text | Whether SPEC-P1.3 and SPEC-P1.4 ever had an X2 (question F-2) |
| SPEC-P1.2's DDL blocks against `migrations/0001_initial.sql`, section by section | N-6, N-7 and N-8 — this record does not say what they are |
| The six Python suites in both modes, in a copy outside the repository: 42, ALIGNED, 21, 12, 39, 36 — all exit 0 | Whether a Stage 0 spec decided X3R-C6 |

### 12.2 Step 1 — the artifacts

SHA-256 (16) over the **git blob** at `b8b1340`, so they reproduce on any platform.

| Artifact | Version | SHA-256 (16) | Lines | Changed since `605ff40` |
|---|---|---|---|---|
| `docs/specs/SPEC-P1.1-DOMAIN.md` | 0.3 | `c8c086c84fb19a24` | 1,210 | no |
| `docs/specs/SPEC-P1.2-STORAGE.md` | 0.5 | `e3e754eca1df1ef8` | 2,397 | **yes** |
| `docs/specs/SPEC-P1.3-CONFIG.md` | 0.1 | `5c8e9188df7e9429` | 485 | no |
| `docs/specs/SPEC-P1.4-AUDIT.md` | 0.1 | `63aec1bd1fe03a3a` | 499 | no |
| `src/domain/models.py` | P1.1 v0.3 | `f3b510059c447f85` | 2,896 | no |
| `migrations/0001_initial.sql` | P1.2 v0.5 | `42ca24cf63cc847b` | 1,599 | **yes** |
| `src/config/loader.py` | P1.3 v0.1 | `047fa57dbcdde5af` | 1,077 | no |
| `config/policy.yaml` | P1.3 v0.1 | `751385d1765bd60a` | 1,253 | no |
| `src/audit/events.py` | P1.4 v0.1 | `64313743c4480ca6` | 719 | no |
| `src/audit/chain.py` | P1.4 v0.1 | `8298a736650d8971` | 481 | no |

**The re-opened spec agrees with its code where it was changed.** SPEC-P1.2's `sql` blocks were
extracted in §6's assembly order and compared with the migration. §9.5 (`verify_audit_chain()`):
76 lines each, 0 differing. Eighteen of twenty sections are identical. The two that differ are
older than the re-open and both existed at `605ff40`: §9.4 lacks the H-1 `READ COMMITTED` guard
(N-2), and §6.10's `cagg_audit_events_daily` still uses `pg_column_size(payload)` where the
migration uses `octet_length(payload::text)` (X3R-M7).

### 12.3 Step 2 — contracts

**118 contracts** — P1.1 44, P1.2 33, P1.3 20, P1.4 21. §4's count is correct. The re-open added
and removed no row. It changed the behaviour behind rows 69 and 70: `payload_hash` now covers 11
columns, and `verify_audit_chain()` also reports `content mutated` and `duplicate seq`. Its
declared return shape is unchanged.

**§4's statement "Signature mismatches between producer and consumer: none found" is withdrawn.**

| Id | Sev | Producer → consumer | Mismatch |
|---|---|---|---|
| **X3R-M1** | HIGH | P1.4 `AuditEnvelope` ↔ P1.2 `audit_log` | Two hashes for one event: 15 keys as canonical JSON (`hash_preimage()`) against 11 columns concatenated (§9.4). The trigger overwrites the application's `payload_hash`. Five envelope fields have no column: the four in `Q-P1.2-7` **and `reproducibility`**, which `Q-P1.2-7` omits. P1.4's CONTRACTS row naming "P1.2's hash trigger" as consumer of `canonical_json()` is untrue |
| **X3R-M2** | HIGH | P1.3 `EffectiveConfig.audit_payload()` → P1.4 `AuditEnvelope` | Rejected with `NonCanonicalPayloadError`. The payload has 132 JSON-number leaves, 28 of them floats; P1.4 §6.2 rule 4 bans every JSON number. `EFFECTIVE_CONFIG_RENDERED` cannot be built from what P1.3 returns |
| **X3R-M3** | MEDIUM | P1.3 and P1.4 both export `canonical_bytes` (rows 89, 106) | P1.3's emits JSON numbers; P1.4's raises on them |
| **X3R-M4** | MEDIUM | P1.1 exports `AuditEvent` (row 41) | No such class exists. P1.1's header, §10.3 and CONTRACTS row were not updated when P1.4 §0 superseded it |
| **X3R-M5** | LOW | P1.2 as-of functions (row 75) | "Two mandatory cutoffs" is true of 2 of 6. `bars_asof` exists, is granted to `backtest_ro`, and is exported nowhere |
| **X3R-M6** | LOW | Six contract rows differ from the code | `Instrument.tick_source` does not exist; `write_before_act()` returns a tuple; `DomainError` has 29 subclasses, not 28; `Producer` has 19 members, 17 used; two more |
| **X3R-M7** | LOW | SPEC-P1.2 DDL ≠ migration | §12.2 above |

**X3R-M1 and X3R-M2 both existed at `605ff40`.** SPEC-P1.3, SPEC-P1.4, `loader.py` and
`events.py` are byte-identical to that commit. All six Python suites pass with both present: no
suite builds an envelope from P1.3's payload, and none compares the two hashes.

Checked and clean: 23 enums against their `CHECK` lists; the Block A numeric limits against the
loaded policy (13 rule thresholds); P1.3's 47-rule inventory; P1.4's 42-type registry; six
contract signatures.

### 12.4 Step 3 — contradictions

Each carries a recommended resolution. **None is resolved.**

| Id | Sev | Source A | Source B | Recommended resolution |
|---|---|---|---|---|
| **X3R-C1** | LOW | `depends_on` in P1.2, P1.3 (×2) and P1.4 | Actual versions: P1.1 v0.3, P1.2 v0.5 | **4 instances, was 2.** Bump at re-freeze. P1.4's is not only documentary: it was written against an 8-column preimage |
| **X3R-C2** | LOW | Each spec's `produces:` header | Its own CONTRACTS table and the code | **All four specs, not P1.4 alone.** P1.1's header names four things that do not exist; P1.2's omits `verify_audit_chain`. Regenerate the headers |
| **X3R-C3** | — | §3 C-3: no duplicate names | `canonical_bytes` | See X3R-M3 |
| **X3R-C5** | MEDIUM | Research summary §4: India price > **₹100** | `policy.yaml`: `min_price_inr: "50.00"`. SPEC-P1.3 says the summary "gives … not a price floor" | Use ₹100, or record an Owner decision for ₹50. P1.3's statement is false |
| **X3R-C6** | LOW | Research summary §8: reject data older than **5 s** | `DATA-001`: **600 s** | Record the authority for 600 s |
| **X3R-C7** | LOW | SPEC-P1.2 §6.11: 240 `CHECK` | SPEC-P1.2 §8: 47 `CHECK` | The migration has 240. Correct §8 |
| **X3R-C8** | LOW | SPEC-P1.1 §10.3: `prev_hash` is the SHA-256 **of** the previous hash | P1.2 §9.4, P1.4 §6.4: it **equals** the previous hash | Remove with X3R-M4 |
| **X3R-C9** | MEDIUM | SPEC-P1.1 §8.2: verdict is `ALLOW`/`DENY`; the sizer re-proposes once | SPEC-P1.3 §4: four actions; `MODIFY` re-evaluated up to 4 passes | No spec maps one to the other. P2.9 must. Also three fields named two ways: `binding_constraint`/`binding_rule_id`, `config_hash`/`content_hash`, `KillSwitchScope`/`KillScope` |
| **X3R-C10** | LOW | SPEC-P1.2 `Q-P1.2-1`: closed | SPEC-P1.2 `Q-P1.2-7`: open, same subject | Fold together |
| **X3R-C11** | LOW | SPEC-P1.1 §15.4: 43 and 20 tests | Measured: 42 and 21 | Correct the spec |
| **X3R-C12** | LOW | Footers and comments reading "v0.1"; references to `errors.py`, `env.py`, `verify_p13_no_env_risk.py`, `migrations/versions/` | P1.1 is v0.3 and P1.2 v0.5; none of those four paths exists | Correct at the next amendment |
| **X3R-C13** | LOW | SPEC-P1.4: `is_paper` and `is_backtest` exclusive; `event_id` is UUIDv7 | `audit_log`: no such `CHECK`; `event_id` defaults to a version 4 UUID | Decide with X3R-M1 |
| **X3R-C14** | MEDIUM | SPEC-P1.2 header: `status: FROZEN` | Same header: "NOT re-frozen". §8 says v0.1 is frozen; §11.6 says v0.4 | See §12.8 |

There is no X3R-C4: no Block A number is stated two ways. Thirteen rule thresholds were checked
against the loaded policy.

Not a contradiction: 28 triggers in SPEC-P1.2 §6.11 against 27 in §2. `apply-migration.sh` counts
`information_schema.triggers`, which omits the one `TRUNCATE` trigger. Reasoned from the script,
not executed.

### 12.5 Step 4 — assumptions

**32 rows, 30 distinct.** §5 did not de-duplicate. Two pairs are one assumption each: `Price` at
6 dp (P1.1 #2, P1.2 #2), and the ~1,000 B audit row at 15,000 events per session (P1.2 #4,
P1.4 #5).

Two assumptions are relied on and appear in no ASSUMPTIONS table:

- **X3R-A1 — new since the re-open.** `0001_initial.sql` has never been deployed, so there is no
  production audit history. It is the only reason §11.8 could invalidate every stored hash.
- **X3R-A2.** PDT is a margin-account rule with a $25,000 floor (SPEC-P1.1 §9.4).

Top of the ranking by impact if false: (1) `[CONST-2]` enforced at the `Decision` constructor;
(2) the off-VM anchor store is write-once — also the only answer to Finding A's residual;
(3) X3R-A1; (4) settlement is T+1 in both markets; (5) audit row width and event rate;
(6) round-trip cost.

### 12.6 Step 5 — open questions

**32 rows, 30 unique ids.** §6's 29 was correct on 2026-08-31; the difference is `Q-P1.2-7`.
`Q-P1.1-1` is still the only id restated across specs.

Raised by this re-run: **X3R-Q1** which side changes for X3R-M2; **X3R-Q2** where the
`ReproducibilityBundle` is stored; **X3R-Q3** how a `PolicyVerdict` maps to a `RiskVerdict`;
**X3R-Q4** whether earnings blackout is in scope; **X3R-Q5** the India price floor.

**What now blocks Stage 2. This replaces §6.1 and the gate table in §9.**

| Phase | Blocked by |
|---|---|
| **P2.1** | **`Q-P1.2-7` / X3R-M1.** `EVENT_REGISTRY` makes P2.1 the producer of three audit event types, and the pack's appendix says "P1.4 (audit) before anything that emits events". §6.1's "None of these blocks P2.1" does not hold for P2.1 code that writes an audit event |
| Any run | X3R-Q1. The run-start config event cannot be built |
| P2.2 | `Q-P1.1-6` |
| P2.3, P2.5, P2.6, P2.7 | `Q-P1.2-7`; X3R-Q2 for the three that produce a reproducible event |
| P2.9 | `Q-P1.1-1`, `Q-P1.1-2`, **`A-14`**, X3R-Q2, X3R-Q3, X3R-Q4. `Q-P1.3-3` is measured inside P2.9 |
| P2.10 | X3R-G2 |

`A-14` is in no Stage 1 document. STAGE-0-FREEZE §10: "A-14 must be ratified before P2.9". §6.1
and §9 omit it.

### 12.7 Step 6 — coverage

§7 marks a research-summary section covered if any spec cites it. That measures citation. The
re-run mapped 70 requirements individually; the matrix is in
`docs/specs/reviews/X3-RERUN-2026-10-02/X3-report.md` §6.2.

| State | Count |
|---|---|
| Covered by a Stage 1 spec | 37 |
| Decided in Stage 0 | 6 |
| Split between Stage 0 or 1 and a later phase | 7 |
| Owned by a later phase | 7 |
| Contradiction or difference with the research summary | 4 |
| **Gap — in no Stage 0 or Stage 1 spec, policy rule or code** | **9 rows, 8 gaps** |

Gaps, listed:

| Id | Gap | Belongs to |
|---|---|---|
| **X3R-G1** | **Earnings blackout** (research summary §4, §6 Phase 8). No rule id, no decision removing it | **Stage 1 — SPEC-P1.3** |
| X3R-G2 | Four automatic kill triggers: volatility > 3σ, API failure > 5 retries, agent loop > 10, data quality | P2.10 |
| X3R-G3 | Trailing stop. `OrderType` and `InvalidationKind` have no member for it | P3.4, with a P1.1 type |
| X3R-G4 | Origin tagging and rate limits on agent messages | P4.1 |
| X3R-G5 | Price, portfolio state, decision reason and confidence on every decision record (research summary §14). `DECISION_MADE` requires none | P1.4 or P2.7 |
| X3R-G6 | Best execution. Named in Block A item 9 | P6.3 |
| X3R-G7 | Exit-hierarchy vocabulary: emergency, high, medium, low | P3.4, with a P1.1 type |
| X3R-G8 | Monte Carlo simulation | P5.1 |

§7's two gaps — §9 AI/ML models and §14 monitoring — stand, and both are deliberate.

### 12.8 Step 7 — version and status

Nothing is changed here. This is what each should carry, for the Owner to decide.

| Artifact | Carries | Should carry | Why |
|---|---|---|---|
| SPEC-P1.1-DOMAIN v0.3 | `FROZEN` | `FROZEN` | Unchanged since the freeze. X3R-M4 is documentary |
| SPEC-P1.2-STORAGE v0.5 | `FROZEN`, and "NOT re-frozen" | **`DRAFT` until re-freeze**, then `FROZEN` at v0.5 | Block B has two statuses, and the pack's rule 3 keys on the word. On the merge evidence v0.5 is fit to re-freeze, with `Q-P1.2-7` carried as a named blocker |
| SPEC-P1.3-CONFIG v0.1 | `FROZEN` | `FROZEN`, with X3R-M2 against it | It or P1.4 must be re-opened under T5 before any run writes its config event |
| SPEC-P1.4-AUDIT v0.1 | `FROZEN` | `FROZEN`, with X3R-M1 and X3R-M2 against it | Same |
| This record | `version: 1.0`, depends on P1.2 v0.1 | `version: 1.1`, depends on P1.2 v0.5 | N-4. Not changed by this section |

Nothing found by this re-run is a defect introduced by the v0.1 → v0.5 change. X3R-M1 and X3R-M2
are older than it. Re-freezing over them is defensible only if the Stage 2 gate names them, as
§12.6 does.

### 12.9 Errors in this record found by the re-run

| Id | Where | Stated | Found |
|---|---|---|---|
| X3R-E1 | §3 C-3 | No contract name is exported by two specs | `canonical_bytes`, rows 89 and 106 |
| X3R-E2 | §4 | No producer/consumer signature mismatch | X3R-M1, X3R-M2. `verify_p11_p12_contract` checks column names in one direction only |
| X3R-E3 | §4 | The Consumers column | Wrong in rows 1, 2, 3, 8, 9, 30 and 42. The generator split on `\|` inside the Signature cell |
| X3R-E4 | §3 C-2 | Header under-declaration in P1.4 | All four specs |
| X3R-E5 | MERGE-CHANGES §2 C-4 | "20 orders/min" is in no spec prose | SPEC-P1.3 §10, line 348 |
| X3R-E6 | §5 | Assumptions consolidated | Not de-duplicated |
| X3R-E7 | §7 | 15 of 23 sections covered; two gaps | Citation counting. Eight gaps not recorded |
| X3R-E8 | §6.1, §9 | P2.9's blockers | `A-14` omitted |
| X3R-E9 | §2 | Hashes of the frozen artifacts | Taken before the merge edited the four spec headers, and over CRLF bytes for three files |

### 12.10 Next

The X5 re-run (§11.6 step 5) follows in its own conversation and is recorded in
`STAGE-1-GAP-AUDIT.md`. §12.6 and §12.7 are inputs to it.

---

## 13. X5 re-run — 2026-10-02

**Run at:** 2026-10-02 · **HEAD:** `3cd91a0` · **Template:** X5 — GAP AUDIT, all five items, in
its own conversation, as §11.6 step 5 requires. Recorded here on 2026-10-05.

**This section re-freezes nothing and changes no status.** The re-run was read-only. Its result
of record is `STAGE-1-GAP-AUDIT.md`, sections 6 to 10. The full report and its evidence are in
`docs/specs/reviews/X5-RERUN-2026-10-02/`. This section is a pointer to them and adds no finding.

**Verdict: GO WITH CONDITIONS.** No Stage 2 phase may start until its two entry conditions are
met:

| # | Entry condition |
|---|---|
| E-1 | Finish §11.6 steps 6 and 7: create `DECISIONS.md`; resolve SPEC-P1.2's status (X3R-C14); re-freeze |
| E-2 | Rewrite the Stage 2 entry gate (§9) so that it names its blockers |

**The eight conditions of the 2026-08-31 audit.** 1, 2, 5, 6 and 7 are closed, each verified by
breaking the code and observing a suite fail. 3, 4 and 8 are open. Eight further conditions, 9 to
16, are tied to the phase each gates; 9 and 10 are `Q-P1.2-7` / X3R-M1 and X3R-M2, which §12.6
names as blockers.

**Finding A is unchanged:** open and accepted (§11.5). Remediation E is deferred (§11.11). The
re-run designed and implemented nothing for either.

**Independence and limits.** Every number was measured by the re-run. §12's findings were tested
as claims; the ones reproduced are named in `STAGE-1-GAP-AUDIT.md` §9. The development database
was not touched: database results come from a throwaway container from the pinned image. All
Python results are on Python 3.11.9. What the re-run did not verify is listed in
`STAGE-1-GAP-AUDIT.md` §10.

**Next.** §11.6 steps 6 and 7. Neither has been started.
