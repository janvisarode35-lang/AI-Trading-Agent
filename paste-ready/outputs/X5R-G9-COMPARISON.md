# X5R-G9 / condition 12 — DeepSeek vs claude.ai, run 2026-10-19

Prompt: "Engineer closing a control gap in the policy layer" (policy diff function, classification
rules, SPEC-P1.3 §5.3 amendment, tests for the five X5R-G9 mutations, condition 12 closure text).

## Input

- Paste: paste-ready/X5R-G9-PASTE.txt, 174,939 characters, SHA-256
  094bf677c89172cc3b487daa55dbb82970d62bdd5331b9fa319f6474e5e220cb.
- Contents, in order: Block A, Block B and Block C, then the prompt, then the full text of
  SPEC-P1.3-CONFIG.md, config/policy.yaml, src/config/loader.py and tests/verify_p13_config.py.
  After those come STAGE-1-GAP-AUDIT.md §9 and §10, and the full text of
  tests/verify_p11_x5_conditions.py, which shows the require() pattern.
- Both chats received exactly this text. The message stored by DeepSeek and the attachment stored
  by claude.ai both hash to the value above.
- The inputs were taken from GitHub at 105f813, which matches the local files.

## Outputs saved

| Model | Files | Integrity |
|---|---|---|
| DeepSeek (Search on, DeepThink off; Continue clicked 3 times) | paste-ready/outputs/X5R-G9-DEEPSEEK-raw.txt (108,109 chars) | Equal to DeepSeek's stored message, SHA-256 c58e3e6c… |
| claude.ai (Opus 5.5, Medium, ran 31 min with its sandbox) | paste-ready/outputs/claude-chat/X5R-G9/: answer, SPEC-P1.3.1-POLICY-DIFF.md, policy_diff.py, verify_p13_policy_diff.py, mutate_x5r_g9.py | Each file equal to the claude.ai file API copy (hash checked per file) |

## Executed here (Python 3.11, pydantic 2.13.5, scratch copies of HEAD; repository untouched)

| Check | DeepSeek | claude.ai |
|---|---|---|
| Existing suites still pass (p13_config 39, p11_x5 12) | yes | yes |
| New suite on the unmutated policy | **40 pass, 2 FAIL** (t_removing_a_monitor_rule_is_neutral: removes CASH-002, which KILL-002 exempts, so the document is invalid; t_undecidable_requires_approval: DENY→MODIFY without a modify block is invalid) | **55/55 pass**, with and without -O |
| Five mutations, edited into policy.yaml text, run with and without -O | All 5 make the new suite fail. 4 are caught by a pin. EXEC-001 is caught only because t_mutation_exec001 then finds an empty diff (no allowed_values pin) | All 5 caught by the pins (t_pin_EXP_002, _LOSS_001, _LOSS_004, _EXEC_001, _STOP_001) |
| Same five against today's suites | none detected (X5R-G9 reproduced) | none detected (X5R-G9 reproduced) |
| Its own mutation harness | none supplied | mutate_x5r_g9.py --must-fail verify_p13_policy_diff.py → 5/5 KILLED, exit 0 |

## Design differences that matter

| Point | DeepSeek | claude.ai |
|---|---|---|
| Direction model | Per-field tables | One model: the rule's pass set. Comparison and threshold are judged together |
| What is diffed | Rules only | Rules plus every config key outside `rules`. Unlisted keys are UNDECIDABLE |
| Pins | 18 rules × action, mode, comparison, scope, threshold, kill_scope | 20 rules × 16 fields, and the membership of the constitutional set is pinned too |
| ALLOW rule enforce → monitor | TIGHTENS | UNDECIDABLE, because PolicyGate applies exemptions regardless of mode (F-3) |
| Shrinking KILL-002 exempts, EXEC-001 emergency set, or tightening RATE/DATA/HOLD rules | TIGHTENS, so zero approvals | UNDECIDABLE, so two approvers: these changes can block an exit |
| scope pool → instrument | LOOSENS | UNDECIDABLE |
| Governance change | diff_policies raises, so no change can be approved | Diffed. The approval count is read from the active (old) version |
| v1 assert_change_authorised | Kept. An AST lint test is added | Kept, but not to be used for approval. Removal deferred to P1.3 v0.2 (F-6) |
| Condition 12 text | Present, with the date left as "2026-XX-XX" | Present, dated 2026-10-19, with five numbered evidence items |

## Claims checked against the repository

- F-3 confirmed: src/config/loader.py:891 adds exemptions when an ALLOW rule passes, without
  checking `binds`.
- F-1 confirmed: UNIV-001 and UNIV-002 refer to `min_price` and `min_market_cap`, but the keys are
  `min_price_usd`/`_inr` and `min_market_cap_usd`/`_inr`. UNIV-003's ref is an expression.
- F-2 confirmed, at least in part: `portfolio.max_position_pct: 0.050` duplicates EXP-001.
- Claude said verify_p11_x5_conditions.py "fails with or without mutations". That was only true in
  its sandbox, which lacked src/domain/models.py. Here the suite passes 12/12.
- Not checked: F-4 (signature over the merged document), and the 264-mutation sweep (Claude ran
  it in its sandbox; not repeated here).

## Verdict

claude.ai's answer meets the acceptance criteria as delivered. The five mutations are detected,
every field is classified, and the closure text comes with evidence that has been re-run. Its
suite also passes 55/55 on Python 3.11 here.

DeepSeek's answer is usable as a second opinion but is not ready to adopt. Its suite does not pass
as delivered. EXEC-001's `allowed_values` is not pinned. Its ALLOW/monitor rule contradicts how
PolicyGate actually behaves. And the dates in its closure text are left as placeholders.

Nothing has been applied to src/, tests/, docs/specs/ or STAGE-1-GAP-AUDIT.md.
