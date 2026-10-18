# CR-1: this session, the claude.ai chat and DeepSeek compared

Date: 2026-10-18. All three received the same input, `paste-ready/CR1-PDT-PASTE.txt` (SHA-256
`a34d2455…0022950`).

- This session (Claude Code): `docs/new specs/SPEC-CR1-US-DAY-TRADING.md`, its patch and test.
- claude.ai chat (Opus 5.5, Medium, web search on): `paste-ready/outputs/claude-chat/CR1/`, four
  files, each checked against the chat's stored copy by SHA-256.
  Chat: https://claude.ai/chat/0558d9e9-a17e-40ba-b167-4b7e989f4b6e
- DeepSeek: `paste-ready/outputs/CR1-DEEPSEEK-raw.txt`; see `CR1-DEEPSEEK-COMPARISON.md`.

## Agreement across all three

The USD 25,000 PDT floor is no longer FINRA's rule: replaced by intraday margin standards,
effective 2026-06-04, phase-in to 2027-10-20; PDT was a margin-account rule; cash accounts are
governed by Regulation T 12 CFR 220.8 and T+1 settlement; 25,000 must not be pinned as a live value.
The claude.ai chat and this session both cite SEC Release 34-105226, 91 FR 20731; DeepSeek had no
release number.

## The claude.ai chat compared with this session

| # | Point | claude.ai chat | This session | Disposition |
|---|-------|----------------|--------------|-------------|
| C-1 | Sources | FINRA notice PDF and weekly update, eCFR 220.8, SEC Rel. 34-42418 on sec.gov, Alpaca **forum**, T+1 from law-firm summaries | FINRA rule text and Notice 26-10, Federal Register copy of the SEC order, eCFR 220.2, 220.8 and 240.15c6-1, Alpaca's **official blog** | This session's sourcing is stronger on T+1 and Alpaca. The chat fetched sec.gov directly, which this project has paused (Owner O-16); it could not know, because O-16 was not in its input. |
| C-2 | Register diff | Pseudo-hunks (`@@ ### 6.2 …`), not a patch `git apply` accepts; no §9 change-log row | Real patch, `git apply --check` passes, adds §6.5 and a §9 row | `STAGE-0-FREEZE.md` §8: a change without a §9 entry "has not happened". Keep this session's patch. |
| C-3 | Where code goes | `src/regulatory/` and `tests/` (historical tree) | `v2/` (OWD-6) | Expected: the chat had no new-run records. |
| C-4 | Account type | Cash account (historical ADR-12) | New run: margin account with zero borrowing ([DEFAULT-16]); historical: cash | Expected from its input; this session covers both (CR1-P5). |
| C-5 | Model B | Not known; designs live order gates | v1 sends no orders; CR1-R-13 and CR1-R-14 for v1 | Expected from its input. |
| C-6 | Legacy day-trade count | Per sell **order** (telemetry only) | Per sell **fill** ([DEFAULT-57]) | Both label it an assumption, since FINRA deleted the interpretations. This session's count is the more conservative. |
| C-7 | #19 and #33 | Not identified ("not in what you pasted") | GitHub issues: #19 P3.2, #33 P6.3; neither fully unblocked | Keep this session's answer. |
| C-8 | Test | 16 checks; SHA-256 over a fact set; a lint over `src/` and `config/` for a live PDT 25,000 | 11 checks; field-by-field pins via `Literal` types; records the historical config line | Both pass and both catch a changed value. **The chat's lint, run against the real `config/policy.yaml`, fails on line 174 `pdt_equity_floor_usd: 25000`**: correct, and the same divergence this session records (section 7, OQ-CR1-4). Its `date.today()` check makes it time-dependent. |
| C-9 | Broker restriction | REGT-002: any broker restriction denies entries; re-enable needs a broker clear **and a human** | CR1-R-10: no opening buy while flagged; cleared from broker status | **Adopted**: CR1-R-10 now also needs a human acknowledgement (v0.2), as INV-7 does for the kill switch. |
| C-10 | Invariant 9 wording | Proposes amendment A-PDT-1: "US PDT" becomes Regulation T cash-account rules, plus 4210(d)(2) if margin | BA-1 already moves INV-9's execution items out of v1 | **Adopted as OQ-CR1-6**: when execution returns, INV-9 must drop "US PDT". |
| C-11 | Settlement ledger | DDL for `cash_settlement_ledger` | None (no execution in v1) | Useful input for the deferred P3.2/P3.3; not adopted now (MB-1). |

## Verdict

The claude.ai chat is strong: correct finding, honest confidence labels, and a lint that found
the real stale value in the repository. This session's spec stays the record because its sources
are primary throughout, its patch applies, it fits the new run (Model B, `v2/`, margin account),
and it answers #19 and #33. Two of the chat's ideas are adopted (C-9, C-10).
